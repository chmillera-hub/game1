#!/opt/venv/bin/python
"""Psalm 22 - CPU frame interpolation (RIFE, IFNet v4.26) for half-rate renders.

Render a slow shot at 12 fps (odd frames only), then synthesise the even frames:

    psalm22/blender/run.sh --shot s05 --quality final --frames odd
    /opt/venv/bin/python psalm22/comp/interp.py --shot s05 --quality final

The missing frames are written next to the rendered ones as NNNN.png (same naming, same
8-bit RGB PNG), so the compositor needs no change. Generally: every missing frame f in 1..N whose
nearest rendered neighbours a < f < b are at most --max-gap apart is interpolated at t=(f-a)/(b-a)
(so 1-of-3 renders work too); a missing trailing (or leading) frame is extrapolated from the last two
rendered frames along the estimated motion (fallback: --edge hold duplicates the last frame).

Other modes:
    interp.py --shot s00 --quality draft --validate      # hide even frames of a full-rate render,
                                                         # re-create them in a scratch dir, PSNR/SSIM
    interp.py --pair a.png b.png --out mid.png [--t 0.5] # one pair
    interp.py --shot s05 --dry-run                       # print the plan only

Python API:
    from interp import Interpolator, fill_shot
    ip = Interpolator()                       # loads /opt/assets/rife/v4.26/flownet.pkl
    mid = ip.interpolate(a, b, 0.5)           # uint8 HxWx3 numpy arrays in/out
    fill_shot("s05", "final")                 # what the CLI does

Docs: psalm22/docs/interp.md. Model: RIFE / Practical-RIFE v4.26 by hzwer et al. (MIT).
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image, PngImagePlugin

# Shared 4-core box: spinning OpenMP workers collapse when Blender/ffmpeg also run (measured at load ~20:
# 20 s/frame with the default policy vs 1.3 s/frame PASSIVE). Must be set before torch is imported.
os.environ.setdefault("OMP_WAIT_POLICY", "PASSIVE")
import torch
import torch.nn as nn
import torch.nn.functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                                  # .../psalm22
WORK = os.environ.get("WORK", "/opt/work/psalm22")
RIFE_DIR = os.environ.get("RIFE_DIR", "/opt/assets/rife")
FRAME_RE = re.compile(r"^(\d{4,})\.png$")
TAG = "Interp"                                                # PNG tEXt key marking generated frames
MANIFEST = "interp.json"

MODELS = {
    "v4.26": {
        "file": "v4.26/flownet.pkl",
        "sha256": "45c7f74156704769dc9f85cfcaf8552e1e926f9399dcfa3a553dee88fac6f53f",
        "url": "https://huggingface.co/hzwer/RIFE/resolve/main/RIFEv4.26_0921.zip",
        "member": "RIFEv4.26_0921/flownet.pkl",
    },
}
DEFAULT_MODEL = "v4.26"


# ----------------------------------------------------------------------------------------------
# IFNet v4.25/v4.26 (re-implementation of Practical-RIFE train_log/IFNet_HDv3.py, MIT licence)
# ----------------------------------------------------------------------------------------------
def _conv(cin, cout, k=3, s=1, p=1):
    return nn.Sequential(nn.Conv2d(cin, cout, k, s, p, bias=True), nn.LeakyReLU(0.2, True))


class Head(nn.Module):
    def __init__(self):
        super().__init__()
        self.cnn0 = nn.Conv2d(3, 16, 3, 2, 1)
        self.cnn1 = nn.Conv2d(16, 16, 3, 1, 1)
        self.cnn2 = nn.Conv2d(16, 16, 3, 1, 1)
        self.cnn3 = nn.ConvTranspose2d(16, 4, 4, 2, 1)
        self.relu = nn.LeakyReLU(0.2, True)

    def forward(self, x):
        x = self.relu(self.cnn0(x))
        x = self.relu(self.cnn1(x))
        x = self.relu(self.cnn2(x))
        return self.cnn3(x)


class ResConv(nn.Module):
    def __init__(self, c):
        super().__init__()
        self.conv = nn.Conv2d(c, c, 3, 1, 1)
        self.beta = nn.Parameter(torch.ones((1, c, 1, 1)))
        self.relu = nn.LeakyReLU(0.2, True)

    def forward(self, x):
        return self.relu(self.conv(x) * self.beta + x)


class IFBlock(nn.Module):
    def __init__(self, cin, c):
        super().__init__()
        self.conv0 = nn.Sequential(_conv(cin, c // 2, 3, 2, 1), _conv(c // 2, c, 3, 2, 1))
        self.convblock = nn.Sequential(*[ResConv(c) for _ in range(8)])
        self.lastconv = nn.Sequential(nn.ConvTranspose2d(c, 4 * 13, 4, 2, 1), nn.PixelShuffle(2))

    def forward(self, x, flow, scale, dtype):
        """x, flow: fp32. Convs run in `dtype` (fp32 or bf16); flow/mask maths stay fp32."""
        x = F.interpolate(x, scale_factor=1. / scale, mode="bilinear", align_corners=False)
        if flow is not None:
            flow = F.interpolate(flow, scale_factor=1. / scale, mode="bilinear", align_corners=False) / scale
            x = torch.cat((x, flow), 1)
        x = x.to(dtype).contiguous(memory_format=torch.channels_last)
        tmp = self.lastconv(self.convblock(self.conv0(x))).float()
        tmp = F.interpolate(tmp, scale_factor=scale, mode="bilinear", align_corners=False)
        return tmp[:, :4] * scale, tmp[:, 4:5], tmp[:, 5:]


_GRID = {}


def warp(img, flow):
    """Backward-warp img (B,C,H,W) by flow (B,2,H,W) in pixels (Practical-RIFE model/warplayer.py)."""
    B, _, H, W = flow.shape
    k = (B, H, W)
    if k not in _GRID:
        gx = torch.linspace(-1.0, 1.0, W).view(1, 1, 1, W).expand(B, -1, H, -1)
        gy = torch.linspace(-1.0, 1.0, H).view(1, 1, H, 1).expand(B, -1, -1, W)
        _GRID[k] = torch.cat([gx, gy], 1)
    f = torch.cat([flow[:, 0:1] / ((W - 1.0) / 2.0), flow[:, 1:2] / ((H - 1.0) / 2.0)], 1)
    g = (_GRID[k] + f).permute(0, 2, 3, 1)
    return F.grid_sample(img.float(), g, mode="bilinear", padding_mode="border", align_corners=True)


class IFNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.block0 = IFBlock(7 + 8, c=192)
        self.block1 = IFBlock(8 + 4 + 8 + 8, c=128)
        self.block2 = IFBlock(8 + 4 + 8 + 8, c=96)
        self.block3 = IFBlock(8 + 4 + 8 + 8, c=64)
        self.block4 = IFBlock(8 + 4 + 8 + 8, c=32)
        self.encode = Head()
        self.dtype = torch.float32

    def forward(self, img0, img1, timestep, scale_list=(16, 8, 4, 2, 1)):
        """img0/img1: (B,3,H,W) fp32 in [0,1], H,W multiples of 64/scale. timestep: (B,1,1,1).
        Returns merged (B,3,H,W), flow (B,4,H,W) [F_t->0, F_t->1], mask (B,1,H,W), w0, w1."""
        dt = self.dtype
        t = timestep.float().expand(-1, 1, img0.shape[2], img0.shape[3])
        f0 = self.encode(img0.to(dt).contiguous(memory_format=torch.channels_last)).float()
        f1 = self.encode(img1.to(dt).contiguous(memory_format=torch.channels_last)).float()
        blocks = (self.block0, self.block1, self.block2, self.block3, self.block4)
        flow = mask = feat = None
        w0, w1 = img0, img1
        for i, blk in enumerate(blocks):
            if flow is None:
                flow, mask, feat = blk(torch.cat((img0, img1, f0, f1, t), 1), None, scale_list[i], dt)
            else:
                wf0 = warp(f0, flow[:, :2])
                wf1 = warp(f1, flow[:, 2:4])
                fd, mask, feat = blk(torch.cat((w0, w1, wf0, wf1, t, mask, feat), 1), flow, scale_list[i], dt)
                flow = flow + fd
            w0 = warp(img0, flow[:, :2])
            w1 = warp(img1, flow[:, 2:4])
        m = torch.sigmoid(mask)
        return w0 * m + w1 * (1 - m), flow, m, w0, w1


# ----------------------------------------------------------------------------------------------
# weights
# ----------------------------------------------------------------------------------------------
def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_weights(model=DEFAULT_MODEL):
    """Return the local path of the model's flownet.pkl, downloading it (from the author's
    HuggingFace repo hzwer/RIFE) into RIFE_DIR on first use."""
    spec = MODELS[model]
    dst = os.path.join(RIFE_DIR, spec["file"])
    if os.path.exists(dst):
        return dst
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    dl = os.path.join(RIFE_DIR, "dl", model)
    os.makedirs(dl, exist_ok=True)
    zpath = os.path.join(dl, os.path.basename(spec["url"]))
    if not os.path.exists(zpath):
        print("[interp] downloading", spec["url"], flush=True)
        subprocess.run(["curl", "-sSL", "--fail", "-o", zpath + ".part", spec["url"]], check=True)
        os.replace(zpath + ".part", zpath)
    with zipfile.ZipFile(zpath) as z, z.open(spec["member"]) as src, open(dst + ".part", "wb") as out:
        shutil.copyfileobj(src, out)
    got = _sha256(dst + ".part")
    if got != spec["sha256"]:
        raise RuntimeError("checksum mismatch for %s: %s" % (spec["member"], got))
    os.replace(dst + ".part", dst)
    return dst


# ----------------------------------------------------------------------------------------------
# inference wrapper
# ----------------------------------------------------------------------------------------------
def _to_tensor(a):
    return torch.from_numpy(np.ascontiguousarray(a)).permute(2, 0, 1).float().div_(255.0)


def _to_u8(x):
    return x.clamp(0, 1).mul(255.0).round().byte().permute(1, 2, 0).numpy()


class Interpolator:
    """RIFE v4.26 on CPU. All images are uint8 HxWx3 (RGB) numpy arrays."""

    def __init__(self, model=DEFAULT_MODEL, threads=None, precision="bf16", scale=1.0):
        if threads:
            torch.set_num_threads(int(threads))
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError:
            pass
        self.model_name = model
        self.scale = float(scale)
        self.precision = precision
        net = IFNet()
        sd = torch.load(ensure_weights(model), map_location="cpu", weights_only=True)
        sd = {k[7:] if k.startswith("module.") else k: v for k, v in sd.items()}
        own = net.state_dict()
        net.load_state_dict({k: v for k, v in sd.items() if k in own}, strict=True)
        net.eval()
        if precision == "bf16":
            net.to(torch.bfloat16)
            net.dtype = torch.bfloat16
        self.net = net.to(memory_format=torch.channels_last)
        self.mult = max(64, int(round(64 / self.scale)))
        self.scale_list = tuple(s / self.scale for s in (16, 8, 4, 2, 1))

    def _pad(self, x):
        h, w = x.shape[-2:]
        ph, pw = (-h) % self.mult, (-w) % self.mult
        return F.pad(x, (0, pw, 0, ph), mode="replicate") if (ph or pw) else x

    @torch.inference_mode()
    def run(self, img0, img1, ts):
        """Batched core: img0/img1 uint8 HxWx3, ts list of timesteps in (0,1).
        Returns dict(merged=[uint8...], flow=(B,4,H,W) tensor, err=[mean abs diff of the two warps])."""
        h, w = img0.shape[:2]
        a = self._pad(_to_tensor(img0)[None])
        b = self._pad(_to_tensor(img1)[None])
        B = len(ts)
        a, b = a.expand(B, -1, -1, -1), b.expand(B, -1, -1, -1)
        t = torch.tensor(ts, dtype=torch.float32).view(B, 1, 1, 1)
        merged, flow, m, w0, w1 = self.net(a, b, t, self.scale_list)
        merged, flow = merged[..., :h, :w], flow[..., :h, :w]
        d = (w0 - w1)[..., :h, :w].abs().mean(1)                     # (B,H,W) warp disagreement
        err = [{"mean": float(d[i].mean() * 255), "p99": float(torch.quantile(d[i].flatten()[::7], 0.99) * 255)}
               for i in range(B)]
        return {"merged": [_to_u8(merged[i]) for i in range(B)], "flow": flow, "err": err}

    def interpolate(self, img0, img1, t=0.5):
        return self.run(img0, img1, [t])["merged"][0]

    @torch.inference_mode()
    def extrapolate(self, other, anchor, d):
        """Predict the frame d intervals beyond `anchor`, continuing the motion other -> anchor
        (d=0.5 for one frame past the last of two frames 2 apart). Flow is estimated at the
        midpoint (best-trained timestep); anchor is backward-warped by -d * velocity."""
        r = self.run(other, anchor, [0.5])
        fl = r["flow"]
        vel = fl[:, 2:4] - fl[:, 0:2]                               # displacement other->anchor
        out = warp(_to_tensor(anchor)[None], -d * vel)
        return _to_u8(out[0]), r["err"][0]


# ----------------------------------------------------------------------------------------------
# planning / shot filling
# ----------------------------------------------------------------------------------------------
def frame_dir(shot, quality):
    return os.path.join(WORK, "frames", shot, quality)


def shot_length(shot):
    try:
        tl = json.load(open(os.path.join(ROOT, "timeline.json")))
        for s in tl["shots"]:
            if s["id"] == shot:
                return int(s["render_frames"])
    except (OSError, ValueError, KeyError):
        pass
    return None


def list_frames(d):
    out = {}
    if os.path.isdir(d):
        for name in os.listdir(d):
            m = FRAME_RE.match(name)
            if m:
                out[int(m.group(1))] = os.path.join(d, name)
    return out


def is_generated(path):
    try:
        with Image.open(path) as im:
            return TAG in im.info
    except OSError:
        return False


def make_plan(src_frames, n, max_gap=2, edge="extrapolate"):
    """src_frames: sorted list of rendered frame numbers. Returns (jobs, unfillable).
    job = ("interp", a, b, [(f, t), ...]) or ("extrap", f, anchor, other, d) or ("hold", f, anchor)."""
    have = sorted(f for f in src_frames if 1 <= f <= n)
    hs = set(have)
    jobs, bad = [], []
    if len(have) == 0:
        return jobs, list(range(1, n + 1))
    for a, b in zip(have, have[1:]):
        if b - a < 2:
            continue
        if b - a > max_gap:
            bad.extend(range(a + 1, b))
            continue
        jobs.append(("interp", a, b, [(f, (f - a) / (b - a)) for f in range(a + 1, b)]))
    lead = [f for f in range(1, have[0])]
    tail = [f for f in range(have[-1] + 1, n + 1)]
    for fs, anchor, nb in ((tail, have[-1], have[-2] if len(have) > 1 else None),
                           (lead, have[0], have[1] if len(have) > 1 else None)):
        if not fs:
            continue
        if len(fs) > max_gap - 1:
            bad.extend(fs)
            continue
        for f in fs:
            if edge == "extrapolate" and nb is not None:
                jobs.append(("extrap", f, anchor, nb, abs(f - anchor) / abs(anchor - nb)))
            else:
                jobs.append(("hold", f, anchor))
    assert not (hs & {f for j in jobs for f in _targets(j)})
    return jobs, sorted(bad)


def _targets(job):
    return [f for f, _ in job[3]] if job[0] == "interp" else [job[1]]


def _sources(job):
    return [job[1], job[2]] if job[0] == "interp" else ([job[2], job[3]] if job[0] == "extrap" else [job[2]])


def _load(path):
    with Image.open(path) as im:
        return np.array(im.convert("RGB"))


def _save(path, arr, note, level):
    info = PngImagePlugin.PngInfo()
    info.add_text(TAG, note)
    tmp = path + ".tmp.png"
    Image.fromarray(arr).save(tmp, pnginfo=info, compress_level=level)
    os.replace(tmp, path)                                       # atomic: compositor never sees half files


def psnr(a, b):
    mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    return 99.0 if mse == 0 else 10 * np.log10(255.0 ** 2 / mse)


def detail(a):
    """High-frequency energy (std of the 4-neighbour Laplacian of luma) - compares sharpness/noise."""
    y = a.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    lap = 4 * y[1:-1, 1:-1] - y[:-2, 1:-1] - y[2:, 1:-1] - y[1:-1, :-2] - y[1:-1, 2:]
    return float(lap.std())


def ssim(a, b):
    """Mean SSIM over RGB (11x11 gaussian, sigma 1.5, data range 255)."""
    x = torch.from_numpy(np.ascontiguousarray(a)).permute(2, 0, 1)[:, None].float()
    y = torch.from_numpy(np.ascontiguousarray(b)).permute(2, 0, 1)[:, None].float()
    g = torch.exp(-((torch.arange(11) - 5.0) ** 2) / (2 * 1.5 ** 2))
    g = g / g.sum()

    def f(z):                                                   # separable 11x11 gaussian, valid region
        return F.conv2d(F.conv2d(z, g.view(1, 1, 1, 11)), g.view(1, 1, 11, 1))
    mx, my = f(x), f(y)
    sxx, syy, sxy = f(x * x) - mx * mx, f(y * y) - my * my, f(x * y) - mx * my
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    s = ((2 * mx * my + c1) * (2 * sxy + c2)) / ((mx * mx + my * my + c1) * (sxx + syy + c2))
    return float(s.mean())


def fill_shot(shot=None, quality="final", src=None, out=None, n=None, max_gap=2, edge="extrapolate",
              force=False, dry_run=False, validate=False, threads=None, precision="bf16", scale=1.0,
              model=DEFAULT_MODEL, compress=3, ip=None, log=print):
    """Fill the missing frames of a half-rate render. Returns a summary dict.

    src/out default to WORK/frames/<shot>/<quality>/. Rendered frames are never overwritten; frames
    this tool generated earlier (PNG tag 'Interp') are regenerated when a source frame is newer, or
    always with force=True. validate=True: treat src as a full-rate render, use only odd frames as
    input, write the evens to `out` (default WORK/dev/interp/validate/<shot>_<quality>) and score
    them against the real ones."""
    t_start = time.time()
    src = src or frame_dir(shot, quality)
    if validate:
        out = out or os.path.join(WORK, "dev", "interp", "validate", "%s_%s" % (shot or "x", quality))
    out = out or src
    os.makedirs(out, exist_ok=True)
    found = list_frames(src)
    if not found:
        raise SystemExit("[interp] no NNNN.png frames in %s" % src)
    if validate:
        n = n or max(found)                                    # extent of the full-rate reference render
    n = n or (shot_length(shot) if shot else None) or max(found)
    truth = {}
    if validate:
        truth = {f: p for f, p in found.items() if f % 2 == 0}
        found = {f: p for f, p in found.items() if f % 2 == 1}
    # rendered frames = in src and not produced by us
    rendered, regen = {}, set()
    for f, p in found.items():
        if not validate and is_generated(p):
            regen.add(f)
        else:
            rendered[f] = p
    jobs, bad = make_plan(sorted(rendered), n, max_gap, edge)
    outs = list_frames(out)
    todo, protected = [], []
    for j in jobs:
        need = False
        for f in _targets(j):
            p = outs.get(f)
            if p is None or validate:
                need = True
            elif f in regen or is_generated(p):
                newest = max(os.path.getmtime(rendered[s]) for s in _sources(j))
                need = need or force or os.path.getmtime(p) < newest
            else:
                protected.append(f)    # a real render already sits in --out: never overwrite it
        if need:
            todo.append(j)
    if protected:
        log("[interp] keeping %d real rendered frames in %s: %s" % (len(protected), out, _ranges(sorted(protected))))
    protected = set(protected)
    nt = sum(len(_targets(j)) for j in todo)
    log("[interp] %s: %d rendered frames of %d, %d to synthesise (%d jobs), %d unfillable%s"
        % (src, len(rendered), n, nt, len(todo), len(bad), " (validate -> %s)" % out if validate else ""))
    if bad:
        log("[interp] WARNING: cannot fill frames (gap > %d or no neighbours): %s" % (max_gap, _ranges(bad)))
    summary = {"src": src, "out": out, "n": n, "rendered": len(rendered), "generated": [], "unfillable": bad,
               "model": "rife-" + model, "precision": precision}
    if dry_run:
        for j in todo:
            log("   ", j)
        return summary
    if not todo:
        return summary
    ip = ip or Interpolator(model, threads=threads, precision=precision, scale=scale)
    cache = {}
    pool = ThreadPoolExecutor(3)

    def get(f):
        if f not in cache:
            cache[f] = pool.submit(_load, rendered[f])
        return cache[f]

    records, writes, t_net = [], [], 0.0
    for idx, j in enumerate(todo):
        for f in _sources(j):
            get(f)
        if idx + 1 < len(todo):                                 # prefetch the next job's inputs
            for f in _sources(todo[idx + 1]):
                get(f)
        imgs = [get(f).result() for f in _sources(j)]
        t0 = time.time()
        if j[0] == "interp":
            _, a, b, ft = j
            r = ip.run(imgs[0], imgs[1], [t for _, t in ft])
            results = [(f, r["merged"][i], "rife-%s t=%.4f %04d %04d" % (model, t, a, b), r["err"][i])
                       for i, (f, t) in enumerate(ft)]
        elif j[0] == "extrap":
            _, f, anc, nb, d = j
            img, e = ip.extrapolate(imgs[1], imgs[0], d)
            results = [(f, img, "rife-%s extrapolate d=%.3f from %04d %04d" % (model, d, nb, anc), e)]
        else:
            _, f, anc = j
            results = [(f, imgs[0], "hold %04d" % anc, {"mean": 0.0, "p99": 0.0})]
        t_net += time.time() - t0
        for f, img, note, e in results:
            if f in protected:
                continue
            path = os.path.join(out, "%04d.png" % f)
            writes.append(pool.submit(_save, path, img, note, compress))
            rec = {"frame": f, "kind": j[0], "note": note, "warp_err": round(e["mean"], 3),
                   "warp_err_p99": round(e["p99"], 2)}
            if validate and f in truth:
                gt = _load(truth[f])
                rec["psnr"] = round(psnr(img, gt), 3)
                rec["ssim"] = round(ssim(img, gt), 5)
                rec["detail_ratio"] = round(detail(img) / max(1e-6, detail(gt)), 4)
                if j[0] == "interp":
                    blend = ((imgs[0].astype(np.uint16) + imgs[1]) // 2).astype(np.uint8)
                    rec["psnr_blend"] = round(psnr(blend, gt), 3)
                    rec["psnr_dup"] = round(psnr(imgs[0], gt), 3)
            records.append(rec)
            log("[interp] %04d %-7s warp_err %.2f%s" % (f, j[0], e["mean"],
                ("  PSNR %.2f dB  SSIM %.4f" % (rec["psnr"], rec["ssim"])) if "psnr" in rec else ""))
        live = set(f for jj in todo[idx + 1: idx + 3] for f in _sources(jj))
        for f in [k for k in cache if k not in live]:
            del cache[f]
    for w in writes:
        w.result()
    pool.shutdown()
    dt = time.time() - t_start
    summary.update(generated=[r["frame"] for r in records], seconds=round(dt, 1),
                   sec_per_frame=round(dt / max(1, len(records)), 3), net_sec_per_frame=round(t_net / max(1, len(records)), 3),
                   threads=torch.get_num_threads(), frames=records)
    if validate:
        for k in ("psnr", "ssim", "detail_ratio", "psnr_blend", "psnr_dup"):
            v = [r[k] for r in records if k in r and r["kind"] == "interp"]
            if v:
                summary[k + "_mean"] = round(float(np.mean(v)), 4)
                summary[k + "_min"] = round(float(np.min(v)), 4)
    mpath = os.path.join(out, MANIFEST)
    if not validate and os.path.exists(mpath):                  # merge with earlier runs (partial regen)
        try:
            old = {r["frame"]: r for r in json.load(open(mpath)).get("frames", [])}
        except (OSError, ValueError):
            old = {}
        new = {r["frame"] for r in records}
        keep = [r for f, r in old.items() if f not in new and is_generated(os.path.join(out, "%04d.png" % f))]
        allr = sorted(keep + records, key=lambda r: r["frame"])
        summary["frames"] = allr
        summary["generated"] = [r["frame"] for r in allr]
        summary["last_run_frames"] = sorted(new)
    errs = [r["warp_err"] for r in summary["frames"] if r["kind"] == "interp"]
    if errs:
        summary["warp_err_mean"] = round(float(np.mean(errs)), 3)
        summary["warp_err_max"] = round(float(np.max(errs)), 3)
        summary["warp_err_p90"] = round(float(np.percentile(errs, 90)), 3)
    with open(mpath + ".tmp", "w") as fh:
        json.dump(summary, fh, indent=1)
    os.replace(mpath + ".tmp", mpath)
    log("[interp] done: %d frames in %.1fs (%.2fs/frame, net %.2fs/frame, %d threads)%s"
        % (len(records), dt, summary["sec_per_frame"], summary["net_sec_per_frame"], summary["threads"],
           ("  mean PSNR %.2f dB SSIM %.4f (blend %.2f, dup %.2f)" % (summary.get("psnr_mean", 0), summary.get("ssim_mean", 0),
            summary.get("psnr_blend_mean", 0), summary.get("psnr_dup_mean", 0))) if validate else ""))
    if summary.get("warp_err_max", 0) > 6:
        log("[interp] NOTE: high warp disagreement (max %.1f/255) - inspect frames %s; consider rendering this "
            "shot at 24 fps" % (summary["warp_err_max"],
                                _ranges(sorted(r["frame"] for r in records if r["warp_err"] > 6))))
    return summary


def _ranges(fs):
    out, i = [], 0
    while i < len(fs):
        j = i
        while j + 1 < len(fs) and fs[j + 1] == fs[j] + 1:
            j += 1
        out.append(str(fs[i]) if i == j else "%d-%d" % (fs[i], fs[j]))
        i = j + 1
    return ",".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="RIFE frame interpolation for half-rate (odd-frame) renders.")
    ap.add_argument("--shot", help="shot id; frames in WORK/frames/<shot>/<quality>/")
    ap.add_argument("--quality", default="final")
    ap.add_argument("--src", help="override source frame dir")
    ap.add_argument("--out", help="write synthesised frames here instead of the source dir")
    ap.add_argument("--n", type=int, help="shot length (default: timeline render_frames, else last frame)")
    ap.add_argument("--max-gap", type=int, default=2, help="largest rendered-frame spacing to bridge (2 = odd frames)")
    ap.add_argument("--edge", choices=("extrapolate", "hold"), default="extrapolate",
                    help="trailing/leading missing frame: motion-extrapolate (default) or duplicate")
    ap.add_argument("--force", action="store_true", help="regenerate all previously generated frames")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--validate", action="store_true", help="score against a full-rate render (see docstring)")
    ap.add_argument("--threads", type=int, default=None, help="torch threads (default: all cores)")
    ap.add_argument("--precision", choices=("bf16", "fp32"), default="bf16")
    ap.add_argument("--scale", type=float, default=1.0, help="RIFE flow scale (1.0 for 540x960)")
    ap.add_argument("--model", default=DEFAULT_MODEL, choices=sorted(MODELS))
    ap.add_argument("--compress", type=int, default=3, help="PNG zlib level for written frames")
    ap.add_argument("--pair", nargs=2, metavar=("A", "B"), help="interpolate a single pair to --out")
    ap.add_argument("--t", type=float, default=0.5)
    a = ap.parse_args(argv)
    if a.pair:
        if not a.out:
            ap.error("--pair needs --out file.png")
        ip = Interpolator(a.model, threads=a.threads, precision=a.precision, scale=a.scale)
        t0 = time.time()
        r = ip.run(_load(a.pair[0]), _load(a.pair[1]), [a.t])
        _save(a.out, r["merged"][0], "rife-%s t=%.4f pair" % (a.model, a.t), a.compress)
        print("[interp] wrote %s in %.2fs (warp_err %.2f)" % (a.out, time.time() - t0, r["err"][0]["mean"]))
        return 0
    if not (a.shot or a.src):
        ap.error("need --shot (or --src)")
    s = fill_shot(a.shot, a.quality, src=a.src, out=a.out, n=a.n, max_gap=a.max_gap, edge=a.edge, force=a.force,
                  dry_run=a.dry_run, validate=a.validate, threads=a.threads, precision=a.precision,
                  scale=a.scale, model=a.model, compress=a.compress)
    return 1 if s["unfillable"] else 0


if __name__ == "__main__":
    sys.exit(main())
