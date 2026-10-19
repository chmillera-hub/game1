"""Animate the faces in the generated photographs with LivePortrait.

Every photograph on screen is re-rendered frame by frame with its people's
performance from the 2D direction (poses.jsonl, exported by render/main.js):
head turns relative to the photo's own pose, gaze, blinks and lids, brows,
lip sync and a blend of emotion deltas taken from generated expression photos.
Only the face region changes, so each frame is stored as a patch:
  OUT/base/NAME.jpg + NAME.json        the photograph and its faces
  OUT/plates/NAME/box.json             patch rectangle in photo pixels
  OUT/plates/NAME/00123.jpg            the patch for film frame 123

Usage:
  python render_faces.py base   IMG_DIR OUT shots.json            (photos, face boxes, emotion basis)
  python render_faces.py calib  IMG_DIR OUT NAME                  (contact sheet of the controls)
  python render_faces.py plates IMG_DIR OUT shots.json poses.jsonl [NAME ...]
"""
import json
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent))
import lp_engine as lp  # noqa: E402

torch.set_num_threads(int(os.environ.get("THREADS", "4")))

EMOTIONS = ["sad", "cry", "joy", "surprise", "anger", "worry", "tender"]
# Expression keypoints by region (LivePortrait's own retargeting groups).
EYES = [1, 2, 11, 13, 15, 16, 18]
LIPS = [6, 12, 14, 17, 19, 20]

# Photos whose hands or props sit on the face: hold back the controls that
# would drag them along.
LIMITS = {
    "call_maya_mouth": {"mouth": 0.0, "smile": 0.0, "rot": 0.3},
    "office_overwhelm": {"mouth": 0.3, "eyes": 0.0, "rot": 0.3},
    "office_temple": {"rot": 0.4, "eyes": 0.5},
    "call_maya": {"rot": 0.5},
    "mirror_reflection": {"rot": 0.8},
}


def read_rgb(p):
    return cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB)


def write_jpg(p, rgb, q=94):
    cv2.imwrite(str(p), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, q])


def pick_faces(eng, img, n):
    """The n largest faces, left to right."""
    fs = eng.faces(img)
    fs = sorted(fs, key=lambda f: -(f.bbox[2] - f.bbox[0]))[:n]
    return sorted(fs, key=lambda f: f.bbox[0])


# ------------------------------------------------------------------ base
def cmd_base(img_dir, out, shots_path):
    shots = json.loads(Path(shots_path).read_text())
    eng = lp.Engine()
    (out / "base").mkdir(parents=True, exist_ok=True)
    for s in shots:
        if s["id"].startswith(("expr_", "ref_")):
            continue
        img = read_rgb(img_dir / f"{s['id']}.png")
        faces = pick_faces(eng, img, len(s["faces"])) if s["faces"] else []
        if len(faces) < len(s["faces"]):
            print(f"!! {s['id']}: found {len(faces)} of {len(s['faces'])} faces")
        write_jpg(out / "base" / f"{s['id']}.jpg", img, 95)
        meta = {"w": img.shape[1], "h": img.shape[0],
                "faces": [{"bbox": [round(float(v), 1) for v in f.bbox], "who": s["faces"][i]} for i, f in enumerate(faces)]}
        (out / "base" / f"{s['id']}.json").write_text(json.dumps(meta))
        print(f"{s['id']:20s} {len(faces)} face(s)", flush=True)
    # emotion basis: (emotion - neutral) in LivePortrait's expression space
    neutral = eng.exp_of(read_rgb(img_dir / "expr_neutral.png"))
    basis = {}
    for k in EMOTIONS:
        p = img_dir / f"expr_{k}.png"
        if p.exists():
            basis[k] = (eng.exp_of(read_rgb(p)) - neutral)[0].numpy().tolist()
    (out / "basis.json").write_text(json.dumps(basis))
    print("basis:", {k: round(float(np.abs(np.array(v)).sum()), 3) for k, v in basis.items()})


def load_basis(out):
    raw = json.loads((out / "basis.json").read_text())
    w = torch.full((21, 1), 0.6)
    w[EYES] = 1.0
    w[LIPS] = 0.45
    return {k: (torch.tensor(v) * w)[None] for k, v in raw.items()}


# ------------------------------------------------------------------ patches
class Photo:
    """One photograph with its faces prepared for re-rendering."""

    def __init__(self, eng, img, faces):
        self.eng, self.img = eng, img
        self.srcs = [eng.prepare(img, f) for f in faces]
        H, W = img.shape[:2]
        x0, y0, x1, y1 = W, H, 0, 0
        for s in self.srcs:
            ys, xs = np.nonzero(s["mask"][..., 0] > 1 / 255)
            if len(xs):
                x0, y0, x1, y1 = min(x0, xs.min()), min(y0, ys.min()), max(x1, xs.max() + 1), max(y1, ys.max() + 1)
        # even-sized box on a 2-pixel grid
        self.box = [int(x0) // 2 * 2, int(y0) // 2 * 2, min(W, (int(x1) + 1) // 2 * 2), min(H, (int(y1) + 1) // 2 * 2)]
        bx0, by0, bx1, by1 = self.box
        self.base_patch = img[by0:by1, bx0:bx1].astype(np.float32)
        for s in self.srcs:
            s["mask_box"] = s["mask"][by0:by1, bx0:bx1]
            M = s["M_c2o"].copy().astype(np.float64)
            M[0, 2] -= bx0
            M[1, 2] -= by0
            s["M_box"] = M[:2]

    def patch(self, deltas):
        """deltas: per face (delta, rot) or None to keep it as photographed."""
        bx0, by0, bx1, by1 = self.box
        out = self.base_patch.copy()
        for s, d in zip(self.srcs, deltas):
            if d is None:
                continue
            crop = self.eng.render(s, d[0], d[1])
            crop = sharpen(crop)
            warped = cv2.warpAffine(crop, s["M_box"], (bx1 - bx0, by1 - by0), flags=cv2.INTER_CUBIC,
                                    borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
            m = s["mask_box"]
            out = m * warped + (1 - m) * out
        return np.clip(out, 0, 255).astype(np.uint8)


def sharpen(img, amount=0.35):
    """LivePortrait renders at 512 px; restore some of the photo's crispness."""
    blur = cv2.GaussianBlur(img, (0, 0), 1.2)
    return cv2.addWeighted(img, 1 + amount, blur, -amount, 0)


def controls(P, mean, lim):
    """2D pose -> LivePortrait controls. Head turns and gaze are relative to this
    photo's average, so the photograph's own composition is the rest pose."""
    Q = dict(P)
    for k in ("yaw", "pitch", "roll", "gazeX", "gazeY"):
        Q[k] = P[k] - mean.get(k, 0.0)
    c = lp.pose_to_controls(Q)
    r = lim.get("rot", 1.0)
    c["rot"] = tuple(v * r for v in c["rot"])
    for k in ("mouth", "eee", "woo"):
        c[k] *= lim.get("mouth", 1.0)
    c["smile"] *= lim.get("smile", 1.0)
    c["eyes"] *= lim.get("eyes", 1.0)
    c["pupil_x"] *= lim.get("eyes", 1.0)
    c["pupil_y"] *= lim.get("eyes", 1.0)
    return c


def cmd_plates(img_dir, out, shots_path, poses_path, only):
    shots = {s["id"]: s for s in json.loads(Path(shots_path).read_text())}
    # frames per photograph, with the poses of the people in it
    jobs = {}
    last_mask = {}
    with open(poses_path) as fh:
        for line in fh:
            r = json.loads(line)
            for L in r["real"]:
                name = L.get("img")
                if not name or name not in shots or not shots[name]["faces"]:
                    continue
                if only and name not in only:
                    continue
                if L.get("mask"):
                    # the reflection reused as the porcelain mask: a held pose, so a
                    # patch every two seconds is enough (the compositor holds the last one)
                    if r["f"] - last_mask.get(name, -999) < 48:
                        continue
                    last_mask[name] = r["f"]
                    poses = [r["actors"].get("maskA")]
                else:
                    poses = [r["actors"].get(who) if scene == r["scene"] else None for scene, who in shots[name]["faces"]]
                if all(p is None for p in poses):
                    continue
                jobs.setdefault(name, []).append((r["f"], poses))
    basis = load_basis(out)
    eng = lp.Engine()
    total = sum(len(v) for v in jobs.values())
    done, t_start = 0, time.time()
    for name, frames in sorted(jobs.items(), key=lambda kv: -len(kv[1])):
        meta = json.loads((out / "base" / f"{name}.json").read_text())
        img = read_rgb(out / "base" / f"{name}.jpg")
        faces = pick_faces(eng, img, len(shots[name]["faces"]))
        if not faces:
            print(f"!! {name}: no faces, skipped")
            continue
        photo = Photo(eng, img, faces)
        pdir = out / "plates" / name
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "box.json").write_text(json.dumps({"box": photo.box, "w": meta["w"], "h": meta["h"]}))
        nf = len(faces)
        # average pose of each person while this photo is on screen
        means = []
        for i in range(nf):
            ps = [p[i] for _, p in frames if p[i] is not None]
            means.append({k: float(np.mean([p[k] for p in ps])) for k in ("yaw", "pitch", "roll", "gazeX", "gazeY")} if ps else {})
        lim = LIMITS.get(name, {})
        for f, poses in frames:
            dst = pdir / f"{f:05d}.jpg"
            if dst.exists():
                continue
            deltas = []
            for i in range(nf):
                P = poses[i] if i < len(poses) else None
                if P is None:
                    deltas.append(None)
                    continue
                c = controls(P, means[i], lim)
                deltas.append(lp.controls_to_delta(c, basis))
            write_jpg(dst, photo.patch(deltas), 93)
            done += 1
            if done % 50 == 0:
                el = time.time() - t_start
                print(f"{name:20s} f{f:5d}  {done}/{total}  {el / done:.2f}s/patch  "
                      f"eta {el / done * (total - done) / 60:.0f} min", flush=True)


# ------------------------------------------------------------------ calibration
def cmd_calib(img_dir, out, name):
    """Contact sheet: each control pushed both ways, for checking signs by eye."""
    eng = lp.Engine()
    img = read_rgb(out / "base" / f"{name}.jpg") if (out / "base" / f"{name}.jpg").exists() else read_rgb(img_dir / f"{name}.png")
    face = pick_faces(eng, img, 1)[0]
    src = eng.prepare(img, face)
    x0, y0, x1, y1 = face.bbox
    s = (x1 - x0) * 1.6
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    box = [int(max(0, cx - s / 2)), int(max(0, cy - s / 2)), int(cx + s / 2), int(cy + s / 2)]
    tests = [("rest", {}), ("yaw+15", {"rot": (0, 15, 0)}), ("yaw-15", {"rot": (0, -15, 0)}),
             ("pitch+12", {"rot": (12, 0, 0)}), ("roll+15", {"rot": (0, 0, 15)}),
             ("pupil_x+12", {"pupil_x": 12}), ("pupil_y+10", {"pupil_y": 10}), ("eyes-15", {"eyes": -15}),
             ("eyes+5", {"eyes": 5}), ("brow+10", {"eyebrow": 10}), ("brow-10", {"eyebrow": -10}),
             ("mouth+50", {"mouth": 50}), ("eee+12", {"eee": 12}), ("woo+12", {"woo": 12}), ("smile+1", {"smile": 1.0})]
    basis = load_basis(out) if (out / "basis.json").exists() else {}
    tests += [(f"emo:{k}", {"emo": k}) for k in basis]
    tiles = []
    for label, kw in tests:
        d, extra = lp.fe_delta(kw.get("eyes", 0), kw.get("eyebrow", 0), kw.get("pupil_x", 0), kw.get("pupil_y", 0),
                               kw.get("mouth", 0), kw.get("eee", 0), kw.get("woo", 0), kw.get("smile", 0))
        if "emo" in kw:
            d = d + basis[kw["emo"]]
        rot = kw.get("rot", (0, 0, 0))
        crop = eng.render(src, d, (rot[0] + extra, rot[1], rot[2]))
        full = eng.paste(img.copy(), src, crop)
        t = cv2.resize(full[box[1]:box[3], box[0]:box[2]], (320, 320), interpolation=cv2.INTER_AREA)
        cv2.putText(t, label, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        tiles.append(t)
    while len(tiles) % 5:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.concatenate(tiles[i:i + 5], 1) for i in range(0, len(tiles), 5)]
    sheet = np.concatenate(rows, 0)
    p = out / f"calib_{name}.jpg"
    write_jpg(p, sheet, 90)
    print("wrote", p)


if __name__ == "__main__":
    cmd, img_dir, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    if cmd == "base":
        cmd_base(img_dir, out, sys.argv[4])
    elif cmd == "calib":
        cmd_calib(img_dir, out, sys.argv[4])
    elif cmd == "plates":
        cmd_plates(img_dir, out, sys.argv[4], sys.argv[5], set(sys.argv[6:]))
