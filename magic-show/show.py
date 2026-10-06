"""Build pipeline: voices -> timeline -> audio mix -> frames -> mp4.

Usage:  python3 show.py part1|part2 [--still T ...] [--from T --to T]
"""
import asyncio
import hashlib
import importlib
import math
import os
import ssl
import subprocess
import sys
import wave
from multiprocessing import Pool

import cairo
import numpy as np

import audio
import engine as E

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.environ.get("BUILD_DIR", os.path.join(HERE, "build"))
VOICE_DIR = os.path.join(BUILD, "voices")
SR = audio.SR

VOICES = {
    "narr": ("en-US-AndrewNeural", "+0%", "+0Hz"),
    "me": ("en-US-AndrewNeural", "+0%", "+0Hz"),
    "anger": ("en-US-GuyNeural", "+6%", "-4Hz"),
    "doubt": ("en-US-AvaNeural", "+6%", "+10Hz"),
    "boredom": ("en-US-BrianNeural", "-16%", "-10Hz"),
}


class Beat:
    def __init__(self, act=None, who=None, line=None, tts=None, sub=None, pre=0.25, post=0.4,
                 min=0.0, id=None, rate=None, pitch=None, gain=1.0):
        self.act, self.who, self.line = act, who, line
        self.tts = tts or line
        self.sub = sub if sub is not None else line
        self.pre, self.post, self.min = pre, post, min
        self.id, self.rate, self.pitch, self.gain = id, rate, pitch, gain
        self.start = self.d = self.vs = self.vd = 0.0
        self.wav = None
        self.env = None


# ------------------------------------------------------------- voices
def voice_key(b):
    v, r, p = VOICES[b.who]
    r = b.rate or r
    p = b.pitch or p
    return v, r, p, hashlib.sha1(f"{v}|{r}|{p}|{b.tts}".encode()).hexdigest()[:16]


async def _tts(sem, v, r, p, txt, mp3):
    import certifi
    certifi.where = lambda: "/root/.ccr/ca-bundle.crt"
    import edge_tts
    import edge_tts.communicate as c
    c._SSL_CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
    async with sem:
        for attempt in range(4):
            try:
                await edge_tts.Communicate(txt, v, rate=r, pitch=p).save(mp3)
                return
            except Exception as e:  # network hiccup
                print("tts retry", attempt, e)
                await asyncio.sleep(2 ** attempt)
        raise RuntimeError("tts failed: " + txt)


def make_voices(beats):
    os.makedirs(VOICE_DIR, exist_ok=True)
    jobs = []
    for b in beats:
        if not b.who or not b.tts:
            continue
        v, r, p, key = voice_key(b)
        wav = os.path.join(VOICE_DIR, key + ".wav")
        b.wav = wav
        if not os.path.exists(wav):
            jobs.append((v, r, p, b.tts, wav))

    async def run():
        sem = asyncio.Semaphore(4)
        await asyncio.gather(*[_tts(sem, v, r, p, txt, w[:-4] + ".mp3") for v, r, p, txt, w in jobs])

    if jobs:
        asyncio.run(run())
        for v, r, p, txt, w in jobs:
            mp3 = w[:-4] + ".mp3"
            trim = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-af", trim,
                            "-ar", str(SR), "-ac", "1", w], check=True)
            os.remove(mp3)


def read_wav(path):
    with wave.open(path) as f:
        x = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return x


# ------------------------------------------------------------- timeline
def layout(beats):
    t = 0.0
    for b in beats:
        b.start = t
        b.vs = b.pre
        if b.wav:
            x = read_wav(b.wav)
            b.vd = len(x) / SR
            # mouth envelope per video frame
            hop = SR // E.FPS
            n = int(math.ceil(len(x) / hop))
            rms = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
            ref = np.percentile(rms, 90) + 1e-6
            e = np.clip(rms / ref, 0, 1.2)
            e = np.convolve(e, [0.3, 0.4, 0.3], mode="same")
            b.env = e
        else:
            b.vd = 0.0
        b.d = max(b.min, b.pre + b.vd + b.post)
        t += b.d
    return t


def run_state(part, t, collect=False):
    S = part.init_state()
    S["t"] = t
    for b in part.BEATS:
        if collect or t >= b.start:
            lt = b.d if collect else min(t - b.start, b.d)
            if b.act:
                b.act(S, lt, b)
    if not collect:
        # lip sync + subtitles
        for b in part.BEATS:
            if b.env is not None and b.start + b.vs <= t < b.start + b.vs + b.vd:
                i = int((t - b.start - b.vs) * E.FPS)
                if b.who in S and isinstance(S[b.who], dict):
                    S[b.who]["talk"] = float(b.env[min(i, len(b.env) - 1)])
            if b.sub and b.who and b.start + b.vs - 0.1 <= t < b.start + b.vs + b.vd + 0.35:
                S["subtitle"] = (b.sub, b.who)
    return S


# ------------------------------------------------------------- audio
def build_audio(part, total, out_wav):
    n = int((total + 0.5) * SR)
    voice = np.zeros(n, np.float32)
    fx = np.zeros(n, np.float32)
    for b in part.BEATS:
        if b.wav:
            x = read_wav(b.wav)
            x = x / (np.max(np.abs(x)) + 1e-9) * 0.85 * b.gain
            i = int((b.start + b.vs) * SR)
            voice[i:i + len(x)] += x[:max(0, n - i)]
    S = run_state(part, total, collect=True)
    for (ts, name, g) in S["sfx"]:
        x = audio.get_sfx(name) * g
        i = int(ts * SR)
        if i >= n:
            continue
        fx[i:i + len(x)] += x[:n - i]
    # music: piecewise mood / volume schedule
    sched = sorted(S["music"], key=lambda m: m[0])
    mus = np.zeros(n, np.float32)
    tracks = {}
    for k, entry in enumerate(sched):
        ts, mood, vol = entry[:3]
        fin, fout = entry[3] if len(entry) > 3 else (0.6, 0.6)
        te = sched[k + 1][0] if k + 1 < len(sched) else total + 0.5
        if mood is None or vol <= 0:
            continue
        if mood not in tracks:
            tracks[mood] = audio.MOODS[mood](total + 1)
        i0, i1 = int(ts * SR), min(n, int(te * SR))
        seg = tracks[mood][i0:i1].copy() * vol
        f1 = min(len(seg), max(1, int(fin * SR)))
        f2 = min(len(seg), max(1, int(fout * SR)))
        if len(seg) > 0:
            seg[:f1] *= np.linspace(0, 1, f1)
            seg[-f2:] *= np.linspace(1, 0, f2)
        mus[i0:i0 + len(seg)] += seg
    # duck music under speech
    ve = np.abs(voice)
    k = int(0.25 * SR)
    sm = np.convolve(ve, np.ones(k) / k, mode="same")
    duck = 1 - 0.55 * np.clip(sm * 12, 0, 1)
    mix = voice + fx * 0.8 + mus * 0.22 * duck
    mix = np.tanh(mix * 1.1) * 0.92
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(out_wav, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(pcm.tobytes())


# ------------------------------------------------------------- video
def prepare(name):
    part = importlib.import_module(name)
    make_voices(part.BEATS)
    total = layout(part.BEATS)
    part.TOTAL = total
    part.index()
    return part, total


def render_frame(part, t):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, E.W, E.H)
    ctx = cairo.Context(surf)
    S = run_state(part, t)
    part.draw(ctx, S, t)
    ctx.identity_matrix()
    ctx.reset_clip()
    if S.get("subtitle") and S.get("subs", True):
        E.draw_subtitle(ctx, *S["subtitle"])
    return surf


def _render_chunk(args):
    name, f0, f1, path = args
    part, total = prepare(name)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
           "-s", f"{E.W}x{E.H}", "-r", str(E.FPS), "-i", "-", "-c:v", "libx264",
           "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        surf = render_frame(part, f / E.FPS)
        p.stdin.write(bytes(surf.get_data()))
    p.stdin.close()
    p.wait()
    return path


def main():
    name = sys.argv[1]
    args = sys.argv[2:]
    part, total = prepare(name)
    os.makedirs(BUILD, exist_ok=True)
    print(f"{name}: {total:.1f}s, {len(part.BEATS)} beats")
    if args and args[0] == "--still":
        for ts in args[1:]:
            surf = render_frame(part, float(ts))
            surf.write_to_png(os.path.join(BUILD, f"{name}_{float(ts):06.2f}.png"))
        return
    if args and args[0] == "--timeline":
        for b in part.BEATS:
            print(f"{b.start:7.2f} {b.d:5.2f} {b.who or '-':8s} {b.id or '':10s} {(b.line or '')[:70]}")
        return
    wav = os.path.join(BUILD, f"{name}.wav")
    build_audio(part, total, wav)
    nf = int(total * E.FPS)
    workers = int(os.environ.get("WORKERS", os.cpu_count() or 4))
    step = math.ceil(nf / workers)
    chunks = [(name, i, min(nf, i + step), os.path.join(BUILD, f"{name}_chunk{k}.mp4"))
              for k, i in enumerate(range(0, nf, step))]
    with Pool(len(chunks)) as pool:
        paths = pool.map(_render_chunk, chunks)
    lst = os.path.join(BUILD, f"{name}_list.txt")
    with open(lst, "w") as f:
        for pth in paths:
            f.write(f"file '{pth}'\n")
    out = os.path.join(BUILD, f"{name}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-i", wav, "-c:v", "copy", "-af", "loudnorm=I=-15:TP=-1.5:LRA=11", "-ar", "48000",
                    "-c:a", "aac", "-b:a", "160k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    for pth in paths:
        os.remove(pth)
    print("wrote", out)


if __name__ == "__main__":
    main()
