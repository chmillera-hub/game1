"""Build QA contact sheets.
    python3 tools/qa_sheets.py            -> out/qa/scene_<id>.png, out/qa/cuts.png, out/qa/enc_<id>.png
scene_* come from the renderer (master quality); enc_* are frames from out/final.mp4 (compressed).
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QA = os.path.join(ROOT, "out/qa")
os.makedirs(QA, exist_ok=True)
_tp = os.path.join(ROOT, "data/timeline_play.json")
tl = json.load(open(_tp if os.path.exists(_tp) else os.path.join(ROOT, "data/timeline.json")))
only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
try:
    FONT = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Medium.otf", 15)
except Exception:
    FONT = ImageFont.load_default()

def beat_at(t, sid):
    cur = None
    for b in tl["order"]:
        B = tl["beats"][b]
        if B["scene"] == sid and t >= B["start"]:
            cur = b
    return cur or ""

def montage(frames, labels, out, cols=4, tw=270, th=480):
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + 24)), (17, 17, 17))
    d = ImageDraw.Draw(sheet)
    for i, (f, lab) in enumerate(zip(frames, labels)):
        x, y = (i % cols) * tw, (i // cols) * (th + 24)
        sheet.paste(Image.open(f).convert("RGB").resize((tw, th)), (x, y + 24))
        d.text((x + 4, y + 4), lab, fill=(255, 255, 255), font=FONT)
    sheet.save(out)

for sc in tl["scenes"]:
    sid = sc["id"]
    if only and sid not in only:
        continue
    dur = sc["end"] - sc["start"]
    n = max(8, min(24, int(dur / 1.2)))
    times = [round(sc["start"] + dur * (i + 0.5) / n, 3) for i in range(n)]
    subprocess.run(["node", "src/render.mjs", "--sheet", sid, "--times", ",".join(map(str, times)),
                    "--out", os.path.join(QA, f"scene_{sid}.png")], cwd=ROOT, check=True)
    final = os.path.join(ROOT, "out/final.mp4")
    if os.path.exists(final):
        sub = times[:: max(1, len(times) // 8)][:8]
        files = []
        for i, t in enumerate(sub):
            f = os.path.join(QA, f"_enc_{sid}_{i}.png")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", final, "-frames:v", "1", f], check=True)
            files.append(f)
        montage(files, [f"{t:.1f}s {beat_at(t, sid)} (compressed)" for t in sub], os.path.join(QA, f"enc_{sid}.png"))
        for f in files:
            os.remove(f)
    print("sheet", sid, flush=True)

if not only:
    # every cut: last frame before | first settled frame after
    pairs = []
    sc = tl["scenes"]
    for a, b in zip(sc[:-1], sc[1:]):
        t0 = round(b["start"] - 0.05, 2)
        t1 = round(b["start"] + (0.95 if b["transition_in"] == "dissolve" else 0.05), 2)
        pairs.append((a["id"], b["id"], t0, t1, b["transition_in"]))
    ts = sorted({t for p in pairs for t in p[2:4]})
    sd = os.path.join(QA, "_cuts")
    os.makedirs(sd, exist_ok=True)
    subprocess.run(["node", "src/render.mjs", "--stills", ",".join(map(str, ts)), "--outdir", sd], cwd=ROOT, check=True)
    frames, labels = [], []
    for a, b, t0, t1, tr in pairs:
        frames += [os.path.join(sd, f"still_{t0:.2f}.png"), os.path.join(sd, f"still_{t1:.2f}.png")]
        labels += [f"{a} end {t0:.2f}", f"-> {b} {tr} {t1:.2f}"]
    montage(frames, labels, os.path.join(QA, "cuts.png"), cols=6, tw=216, th=384)
    # the very first frame, full size
    subprocess.run(["node", "src/render.mjs", "--stills", "0", "--outdir", QA], cwd=ROOT, check=True)
    print("cuts + first frame done")
