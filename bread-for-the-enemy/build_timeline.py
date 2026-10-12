"""
Resolve the screenplay into an absolute timeline:
  - synthesises every line (cached), measures it, lays it on the clock
  - resolves acting keyframes, sfx and music cues to absolute times
  - writes <work>/timeline.json (read by the renderer, music and sfx builders)
  - writes <work>/voice.wav (48 kHz stereo dialogue stem with room treatment)
"""
import json
import os
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import audiofx  # noqa: E402
import screenplay  # noqa: E402
import tts  # noqa: E402

OUT_SR = 48000
FPS = 24


def shot_env(shot):
    if shot.startswith(("upper", "church")):
        return "room_warm"
    if shot.startswith("street"):
        return "street"
    if shot.startswith("cell"):
        return "cell"
    if shot.startswith("jer"):
        return "memory"
    if shot.startswith("dam"):
        return "desert"
    if shot.startswith("dawn"):
        return "outdoor"
    return "dry"


def build():
    cur = 0.0
    shots, lines, texts, sfx, music = [], [], [], [], []
    acts = {}
    last_line = None
    cur_shot = None

    def resolve(ev):
        if "ls" in ev and last_line:
            return last_line["start"] + ev["ls"]
        if "lf" in ev and last_line:
            return last_line["start"] + ev["lf"] * (last_line["end"] - last_line["start"])
        return cur + ev.get("at", 0.0)

    for ev in screenplay.EVENTS:
        k = ev["kind"]
        if k == "shot":
            if cur_shot:
                cur_shot["end"] = cur
            params = {kk: vv for kk, vv in ev.items() if kk not in ("kind", "shot")}
            cur_shot = dict(id=ev["shot"], start=cur, params=params, env=shot_env(ev["shot"]))
            shots.append(cur_shot)
        elif k == "line":
            who = ev["who"]
            text_tts = ev.get("tts", ev["text"])
            speed = ev.get("speed", 0.9)
            fx = ev.get("fx")
            start = cur + ev.get("pre", 0.0)
            if who == "both":
                xa, ta = tts.synth("paul", text_tts, speed, None)
                xb, tb = tts.synth("asher", text_tts, speed * 1.02, None)
                clips = {"paul": (xa, ta, 0.0), "asher": (xb, tb, 0.05)}
            else:
                x, tm = tts.synth(who, text_tts, speed, fx)
                clips = {who: (x, tm, 0.0)}
            dur = max(len(c[0]) / tts.SR + c[2] for c in clips.values())
            mouth = {}
            for w, (x, tm, off) in clips.items():
                mc = tts.mouth_curves(x, tm)
                mouth[w] = dict(offset=off, **mc)
            line = dict(who=who, start=round(start, 4), end=round(start + dur, 4), text=ev.get("sub", ev["text"]),
                        vo=bool(ev.get("vo", False)), fx=fx, vol=ev.get("vol", 1.0), mouth=mouth,
                        env=cur_shot["env"] if cur_shot else "dry", shot=cur_shot["id"] if cur_shot else None,
                        clips={w: dict(off=c[2]) for w, c in clips.items()},
                        _audio={w: c for w, c in clips.items()})
            lines.append(line)
            last_line = line
            cur = start + dur + ev.get("gap", 0.35)
        elif k == "pause":
            cur += ev["sec"]
        elif k == "act":
            t = resolve(ev)
            state = {kk: vv for kk, vv in ev.items() if kk not in ("kind", "who", "at", "ls", "lf", "dur")}
            acts.setdefault(ev["who"], []).append(dict(t=round(t, 4), dur=ev.get("dur", 0.45), state=state))
        elif k == "sfx":
            t = resolve(ev)
            sfx.append(dict(t=round(t, 4), name=ev["sfx"], **{kk: vv for kk, vv in ev.items()
                                                              if kk not in ("kind", "sfx", "at", "ls", "lf")}))
        elif k == "music":
            music.append(dict(t=round(cur, 4), cue=ev["cue"]))
        elif k == "text":
            t = resolve(ev)
            texts.append(dict(t=round(t, 4), dur=ev.get("dur", 3.0), style=ev["style"], text=ev["text"],
                              sub=ev.get("sub")))
    if cur_shot:
        cur_shot["end"] = cur
    total = cur
    for who in acts:
        acts[who].sort(key=lambda a: a["t"])
    return dict(fps=FPS, duration=round(total, 3), shots=shots, lines=lines, acts=acts, sfx=sfx,
                music=music, texts=texts)


def mix_voice(tl, path):
    n = int((tl["duration"] + 4) * OUT_SR)
    buf = np.zeros((n, 2), dtype=np.float64)
    for ln in tl["lines"]:
        for w, (x, tm, off) in ln["_audio"].items():
            env = "narr" if ln["who"] == "narrator" else ln["env"]
            if ln["vo"] and ln["who"] == "paul" and ln["env"] in ("desert", "memory"):
                env = "narr"  # old Paul narrating over his memory
            y = audiofx.resample(x.astype(np.float64), tts.SR, OUT_SR)
            fx = ln["fx"] if ln["fx"] in ("memory", "divine", "soft_divine") else None
            st = audiofx.place_voice(y, OUT_SR, env, fx)
            gain = ln["vol"] * (0.62 if (ln["who"] == "both" and w == "asher") else 1.0)
            i0 = int((ln["start"] + off) * OUT_SR)
            i1 = min(n, i0 + len(st))
            buf[i0:i1] += st[: i1 - i0] * gain
    pk = np.max(np.abs(buf))
    if pk > 0.98:
        buf *= 0.98 / pk
    sf.write(path, buf.astype(np.float32), OUT_SR)


def main():
    work = tts.WORK
    os.makedirs(work, exist_ok=True)
    tl = build()
    mix_voice(tl, os.path.join(work, "voice.wav"))
    for ln in tl["lines"]:
        ln.pop("_audio", None)
    with open(os.path.join(work, "timeline.json"), "w") as f:
        json.dump(tl, f)
    # SRT sidecar
    def ts(t):
        h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
        return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"
    names = dict(narrator="Narrator", jesus="Jesus", paul="Paul", saul="Saul", asher="Asher", yosef="Yosef",
                 elder="Elder", guard="Guard", child="Young Asher", both="Paul & Asher")
    with open(os.path.join(work, "subtitles.srt"), "w") as f:
        lines = tl["lines"]
        for i, ln in enumerate(lines, 1):
            end = ln["end"] + 0.25
            if i < len(lines):
                end = min(end, lines[i]["start"] - 0.02)
            f.write(f"{i}\n{ts(ln['start'])} --> {ts(end)}\n")
            prefix = "" if ln["who"] == "narrator" else f"{names[ln['who']].upper()}: "
            f.write(f"{prefix}{ln['text']}\n\n")
    print(f"duration {tl['duration']:.1f}s  shots {len(tl['shots'])}  lines {len(tl['lines'])}")


if __name__ == "__main__":
    main()
