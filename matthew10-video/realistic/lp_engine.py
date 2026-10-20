"""LivePortrait as a parametric face rig for photographs.

A face in a photo is prepared once (implicit keypoints + appearance features);
each frame then sets head rotation, gaze, lids, brows, mouth shapes and a blend
of emotion deltas, and LivePortrait re-renders the face, which is pasted back
into the photo with its feathered mask.
"""
import sys

import cv2
import numpy as np
import torch

sys.path.insert(0, "/opt/real/LivePortrait")
from src.config.crop_config import CropConfig  # noqa: E402
from src.config.inference_config import InferenceConfig  # noqa: E402
from src.live_portrait_wrapper import LivePortraitWrapper  # noqa: E402
from src.utils.camera import get_rotation_matrix  # noqa: E402
from src.utils.crop import crop_image, paste_back, prepare_paste_back  # noqa: E402
from src.utils.cropper import Cropper  # noqa: E402
from src.utils.retargeting_utils import calc_eye_close_ratio  # noqa: E402

torch.set_num_threads(4)

# On CPU the warp and decoder are ~90% convolutions; in bfloat16 they run on the
# AMX units at about twice the speed. Sampling stays in float32 so the warp's
# sub-pixel positions (hair edges) do not shimmer from frame to frame, and 3D
# average pooling has no bfloat16 kernel.
_grid_sample = torch.nn.functional.grid_sample


def _grid_sample_f32(inp, grid, *a, **k):
    if inp.dtype == torch.bfloat16 or grid.dtype == torch.bfloat16:
        return _grid_sample(inp.float(), grid.float(), *a, **k).to(inp.dtype)
    return _grid_sample(inp, grid, *a, **k)


torch.nn.functional.grid_sample = _grid_sample_f32


class _Pool32(torch.nn.Module):
    def __init__(self, pool):
        super().__init__()
        self.pool = pool

    def forward(self, x):
        return self.pool(x.float()).to(x.dtype)


def _bf16(module):
    for name, child in module.named_children():
        if isinstance(child, torch.nn.AvgPool3d):
            setattr(module, name, _Pool32(child))
        else:
            _bf16(child)
    return module.to(torch.bfloat16)


class Engine:
    def __init__(self, crop_scale=2.1):
        self.inf = InferenceConfig(flag_force_cpu=True, flag_use_half_precision=False, flag_do_torch_compile=False)
        self.crop_cfg = CropConfig(flag_force_cpu=True, scale=crop_scale)
        self.w = LivePortraitWrapper(self.inf)
        self.cropper = Cropper(crop_cfg=self.crop_cfg, flag_force_cpu=True, image_type="human_face")
        self.warp = _bf16(self.w.warping_module)
        self.decode = _bf16(self.w.spade_generator)

    def faces(self, img_rgb, min_size=48):
        bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        fs = self.cropper.face_analysis_wrapper.get(bgr, flag_do_landmark_2d_106=True, direction="left-right")
        return [f for f in fs if (f.bbox[2] - f.bbox[0]) >= min_size]

    def prepare(self, img_rgb, face):
        crop = crop_image(img_rgb, face.landmark_2d_106, dsize=512, scale=self.crop_cfg.scale,
                          vy_ratio=self.crop_cfg.vy_ratio, flag_do_rot=True)
        img256 = cv2.resize(crop["img_crop"], (256, 256), interpolation=cv2.INTER_AREA)
        I_s = self.w.prepare_source(img256)
        with torch.no_grad():
            info = self.w.get_kp_info(I_s)
            f_s = self.w.extract_feature_3d(I_s)
            x_s = self.w.transform_keypoint(info)
        mask = prepare_paste_back(self.inf.mask_crop, crop["M_c2o"], dsize=(img_rgb.shape[1], img_rgb.shape[0]))
        # how open each eye is in the photo (203-point landmarks), for the eye retargeting
        lmk = self.cropper.human_landmark_runner.run(img_rgb, face.landmark_2d_106)
        eye_ratio = torch.from_numpy(calc_eye_close_ratio(lmk[None])).float()
        return {"info": info, "f_s": f_s.to(torch.bfloat16), "x_s": x_s, "M_c2o": crop["M_c2o"], "mask": mask,
                "bbox": face.bbox.copy(), "eye_ratio": eye_ratio}

    def exp_of(self, img_rgb):
        fs = self.faces(img_rgb)
        f = max(fs, key=lambda f: f.bbox[2] - f.bbox[0])
        return self.prepare(img_rgb, f)["info"]["exp"].clone()

    @torch.no_grad()
    def eye_delta(self, src, close):
        """Keypoint offset that sets both eyes to the same openness: close 0 = as open as
        the photo's eyes on average, 1 = shut. LivePortrait's eye retargeting measures
        each eye, so lids close alike even on a turned head (offsets on the eye
        keypoints close one eye before the other)."""
        r = src["eye_ratio"]
        target = (r.mean() * (1.0 - close)).reshape(1, 1)
        return self.w.retarget_eye(src["x_s"], torch.cat([r, target], dim=1))

    @torch.no_grad()
    def render(self, src, delta, rot, close=None):
        """delta: 1x21x3 expression offset; rot: (pitch, yaw, roll) degrees added to the source pose;
        close: lids (see eye_delta), None = as photographed."""
        info = src["info"]
        R = get_rotation_matrix(info["pitch"] + rot[0], info["yaw"] + rot[1], info["roll"] + rot[2])
        x_d = info["scale"][..., None] * (info["kp"] @ R + info["exp"] + delta)
        x_d[:, :, :2] += info["t"][:, None, :2]
        if close is not None:
            x_d = x_d + self.eye_delta(src, close)
        x_d = self.w.stitching(src["x_s"], x_d)
        o = self.warp(src["f_s"], kp_source=src["x_s"].to(torch.bfloat16), kp_driving=x_d.to(torch.bfloat16))
        return self.w.parse_output(self.decode(feature=o["out"]).float())[0]

    def paste(self, frame, src, crop_img):
        return paste_back(crop_img, src["M_c2o"], frame, src["mask"])


# ------------------------------------------------------------------ controls
def fe_delta(eyes=0.0, eyebrow=0.0, pupil_x=0.0, pupil_y=0.0, mouth=0.0, eee=0.0, woo=0.0, smile=0.0):
    """Keypoint offsets for slider-style controls (after ComfyUI-AdvancedLivePortrait's
    expression editor). Returns (delta 1x21x3, extra pitch in degrees)."""
    d = torch.zeros(1, 21, 3)
    d[0, 20, 1] += smile * -0.01
    d[0, 14, 1] += smile * -0.02
    d[0, 17, 1] += smile * 0.0065
    d[0, 17, 2] += smile * 0.003
    d[0, 13, 1] += smile * -0.00275
    d[0, 16, 1] += smile * -0.00275
    d[0, 3, 1] += smile * -0.0035
    d[0, 7, 1] += smile * -0.0035

    d[0, 19, 1] += mouth * 0.001
    d[0, 19, 2] += mouth * 0.0001
    d[0, 17, 1] += mouth * -0.0001
    pitch = -mouth * 0.05

    d[0, 20, 2] += eee * -0.001
    d[0, 20, 1] += eee * -0.001
    d[0, 14, 1] += eee * -0.001

    d[0, 14, 1] += woo * 0.001
    d[0, 3, 1] += woo * -0.0005
    d[0, 7, 1] += woo * -0.0005
    d[0, 17, 2] += woo * -0.0005

    if pupil_x > 0:
        d[0, 11, 0] += pupil_x * 0.0007
        d[0, 15, 0] += pupil_x * 0.001
    else:
        d[0, 11, 0] += pupil_x * 0.001
        d[0, 15, 0] += pupil_x * 0.0007
    d[0, 11, 1] += pupil_y * -0.001
    d[0, 15, 1] += pupil_y * -0.001
    eyes -= pupil_y / 2.0

    d[0, 11, 1] += eyes * -0.001
    d[0, 13, 1] += eyes * 0.0003
    d[0, 15, 1] += eyes * -0.001
    d[0, 16, 1] += eyes * 0.0003
    d[0, 1, 1] += eyes * -0.00025
    d[0, 2, 1] += eyes * 0.00025

    if eyebrow > 0:
        d[0, 1, 1] += eyebrow * 0.001
        d[0, 2, 1] += eyebrow * -0.001
    else:
        d[0, 1, 0] += eyebrow * -0.001
        d[0, 2, 0] += eyebrow * 0.001
        d[0, 1, 1] += eyebrow * 0.0003
        d[0, 2, 1] += eyebrow * -0.0003
    return d, pitch


def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


# Calibration. Signs measured with face landmarks on rendered test frames
# (LivePortrait: +yaw turns the face to screen left, +pitch nods down, +roll
# tilts clockwise, +pupil_x looks to screen right, +pupil_y looks up; the 2D
# rig turns to screen right, nods down, tilts clockwise, looks right / down).
# Gains are below the 2D rig's, which exaggerates for legibility.
CAL = {"yaw": -18.0, "pitch": 13.0, "roll": 50.0, "pupil_x": 11.0, "pupil_y": -9.0, "mouth": 62.0,
       "eee": 9.0, "woo": 9.0, "close": 15.0, "brow": 9.0, "emo": 1.4}


def pose_to_controls(P):
    """Map an exported 2D-rig pose to LivePortrait controls + emotion weights."""
    close = clamp(P["blink"] + P["lid"] + 0.5 * (P["lidL"] + P["lidR"]) + 0.35 * P["squint"] - 0.8 * P["wide"], -0.6, 1.0)
    eyes = -close * CAL["close"] if close > 0 else -close * 6.0
    brow = (0.45 * P["browIn"] + 0.55 * P["browOut"] + 0.8 * P["browTalk"]) * CAL["brow"]
    mouth = (P["open"] + 0.8 * P["jawOpen"]) * CAL["mouth"] - P["press"] * 8.0
    smile = clamp(P["smile"], -0.3, 1.0) * 0.9
    w = {
        "sad": clamp(0.9 * max(0, P["browIn"]) + 0.7 * max(0, -P["smile"]) - 0.9 * max(0, P["browOut"]) - 0.6 * max(0, P["smile"])),
        "cry": clamp((P["wet"] - 0.45) * 1.8) * clamp(P["browIn"] * 1.4),
        "joy": clamp((P["smile"] - 0.35) * 1.4) * (1 - clamp(P["wide"] * 2)),
        "surprise": clamp(1.3 * P["wide"] + 0.4 * max(0, P["browOut"]) - 0.25),
        "anger": clamp(1.1 * max(0, -P["browIn"]) + 0.3 * P["browKnit"] * (1 if P["browIn"] < 0 else 0)),
        "worry": clamp(0.7 * P["browKnit"] + 0.35 * P["press"] - 0.3 * max(0, -P["browIn"])),
        "tender": clamp(1.5 * P["wet"] * max(0, P["smile"]) * 2),
    }
    return {
        "rot": (P["pitch"] * CAL["pitch"], P["yaw"] * CAL["yaw"], P["roll"] * CAL["roll"]),
        "eyes": eyes, "eyebrow": brow, "pupil_x": P["gazeX"] * CAL["pupil_x"], "pupil_y": P["gazeY"] * CAL["pupil_y"],
        "mouth": mouth, "eee": P["mouthWide"] * CAL["eee"], "woo": P["round"] * CAL["woo"], "smile": smile,
        "weights": w,
    }


def controls_to_delta(c, basis):
    """-> (keypoint offset, rotation, lids): closing lids go to the eye retargeting,
    widening stays a keypoint offset."""
    eyes = c["eyes"]
    close = min(1.0, max(0.0, -eyes / CAL["close"]))
    d, extra_pitch = fe_delta(max(eyes, 0.0), c["eyebrow"], c["pupil_x"], c["pupil_y"], c["mouth"], c["eee"], c["woo"], c["smile"])
    for k, wk in c["weights"].items():
        if wk > 0 and k in basis:
            d = d + basis[k] * (wk * CAL["emo"])
    p, y, r = c["rot"]
    return d, (p + extra_pitch, y, r), close
