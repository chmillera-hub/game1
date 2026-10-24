"""Lay the voice lines end to end and derive everything time-based:
beat start/end, absolute sentence segments, music cue times, subtitles (SRT),
and per-frame mouth envelopes for lip sync."""
import json, re, wave
import numpy as np
from script import BEATS

FPS = 24
LEAD = 0.7          # music + picture run this long before the first line
SR = 44100


def load_wav(p):
    with wave.open(p) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


def word_time(segs, word, after=0.0):
    """Estimate when `word` is spoken: proportional position within its sentence."""
    wl = word.lower()
    for text, t0, t1 in segs:
        if t1 < after:
            continue
        k = text.lower().find(wl)
        if k >= 0 and len(text) > 0:
            # bias toward the middle of the word, voice runs slightly ahead of characters
            frac = (k + len(word) * 0.5) / len(text)
            return t0 + (t1 - t0) * frac
    return None


def build():
    meta = json.load(open("build/voice.json"))
    t = LEAD
    out = []
    for b, m in zip(BEATS, meta):
        start = t
        segs = [[s, start + a, start + c] for s, a, c in m["segs"]]
        end = start + m["dur"]
        cues = []
        for kind, word in b.get("cues", []):
            wt = word_time(segs, word)
            if wt is None:
                print("cue word not found:", word, "in", b["t"])
                continue
            cues.append((kind, wt))
        out.append(dict(i=m["i"], s=b["s"], start=start, end=end, segs=segs, cues=cues))
        t = end + b.get("pause", 0.45)
    total = t + 0.3
    for k, o in enumerate(out):
        o["next"] = out[k + 1]["start"] if k + 1 < len(out) else total
    json.dump(dict(beats=out, total=total, fps=FPS), open("build/timeline.json", "w"), indent=1)

    # voice stem + envelopes
    n = int(total * SR) + SR
    stems = {s: np.zeros(n, np.float32) for s in "NMA"}
    for o in out:
        a = load_wav(f"build/voice/{o['i']:03d}.wav")
        k = int(o["start"] * SR)
        stems[o["s"]][k:k + len(a)] += a
    voice = stems["N"] + stems["M"] + stems["A"]
    np.save("build/voice_mix.npy", voice)

    nf = int(total * FPS) + 1
    env = {}
    hop = SR // FPS
    for s in "MA":
        x = stems[s]
        e = np.zeros(nf, np.float32)
        z = np.zeros(nf, np.float32)
        for f in range(nf):
            seg = x[f * hop:(f + 1) * hop + hop // 2]
            if len(seg) == 0:
                continue
            e[f] = np.sqrt(np.mean(seg ** 2))
            z[f] = np.mean(np.abs(np.diff(np.sign(seg)))) * 0.5 if len(seg) > 1 else 0
        e = e / (np.percentile(e[e > 0.01], 92) + 1e-6) if np.any(e > 0.01) else e
        env[s] = np.clip(e, 0, 1.3)
        env[s + "z"] = z
    np.savez("build/env.npz", **env)

    write_srt(out)
    print(f"total {total:.2f}s  frames {nf}")


def fmt(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


NAMES = {"N": "", "M": "MAYA: ", "A": "ABE: "}


def sub_chunks(o):
    """Split a beat's sentences into readable subtitle chunks (<= ~70 chars)."""
    chunks = []
    for text, t0, t1 in o["segs"]:
        text = text.strip()
        if len(text) <= 72:
            chunks.append([text, t0, t1])
            continue
        parts = re.split(r"(?<=,)\s+", text)
        groups, cur = [], ""
        for p in parts:
            if cur and len(cur) + len(p) + 1 > 60:
                groups.append(cur); cur = p
            else:
                cur = (cur + " " + p).strip()
        if cur:
            groups.append(cur)
        total = sum(len(g) for g in groups)
        tt = t0
        for g in groups:
            d = (t1 - t0) * len(g) / total
            chunks.append([g, tt, tt + d]); tt += d
    # each chunk stays up until the next one (or a short tail)
    for k, c in enumerate(chunks):
        nxt = chunks[k + 1][1] if k + 1 < len(chunks) else min(o["next"] - 0.05, c[2] + 0.9)
        c[2] = max(c[2], nxt - 0.02) if k + 1 < len(chunks) else nxt
    return chunks


def write_srt(out):
    lines, n = [], 1
    for o in out:
        for text, t0, t1 in sub_chunks(o):
            lines.append(f"{n}\n{fmt(t0)} --> {fmt(t1)}\n{NAMES[o['s']]}{text}\n")
            n += 1
    open("build/subtitles.srt", "w").write("\n".join(lines))


if __name__ == "__main__":
    build()
