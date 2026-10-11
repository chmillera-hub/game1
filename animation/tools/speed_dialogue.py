"""Speed up all dialogue uniformly (no re-synthesis) and build the playback timeline + time warp.

    python3 tools/speed_dialogue.py [factor=1.15]

The animation stays authored against data/timeline.json ("story time"). This step produces:
  audio/wav_play/<id>.wav     each line time-compressed by `factor` (WSOLA atempo: pitch and timbre unchanged)
  data/lines_play.json        durations and word timestamps in the faster audio
  data/timeline_play.json     the timeline as played: line beats shortened, pauses and silent beats unchanged
  data/timewarp.json          piecewise-linear map between story time and play time

The renderer draws frame `t_play` by evaluating every scene at story time W(t_play), so during speech all motion
(lips, reactions, gestures) compresses in exact sync with the voice, while silent acting holds keep their length.
"""
import json, os, subprocess, sys
import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 44100


def main():
    factor = float(sys.argv[1]) if len(sys.argv) > 1 else 1.15
    tl = json.load(open(os.path.join(ROOT, "data/timeline.json")))
    lines = json.load(open(os.path.join(ROOT, "data/lines.json")))
    os.makedirs(os.path.join(ROOT, "audio/wav_play"), exist_ok=True)

    lines_play = {}
    for bid, L in lines.items():
        src = os.path.join(ROOT, L["file"])
        dst_rel = os.path.join("audio/wav_play", os.path.basename(L["file"]))
        dst = os.path.join(ROOT, dst_rel)
        if factor != 1.0:
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", f"atempo={factor:.4f}",
                            "-ar", str(SR), "-c:a", "pcm_s16le", dst], check=True)
        else:
            subprocess.run(["cp", src, dst], check=True)
        a, sr = sf.read(dst, dtype="float32")
        dur = len(a) / sr
        k = dur / L["dur"]
        lines_play[bid] = dict(L, file=dst_rel, dur=round(dur, 3), authored_dur=L["dur"],
                               words=[dict(w, start=round(w["start"] * k, 3), end=round(w["end"] * k, 3)) for w in L["words"]])
    json.dump(lines_play, open(os.path.join(ROOT, "data/lines_play.json"), "w"), indent=1)

    # knots (story, play): every line beat compresses; everything else keeps slope 1
    knots = [(0.0, 0.0)]
    shift = 0.0
    for bid in tl["order"]:
        b = tl["beats"][bid]
        if b["kind"] != "line":
            continue
        s, e = b["start"], b["end"]
        new_len = lines_play[bid]["dur"] * (e - s) / lines[bid]["dur"]  # timeline beat length == audio length
        knots.append((s, s - shift))
        shift += (e - s) - new_len
        knots.append((e, e - shift))
    S = np.array([k[0] for k in knots])
    P = np.array([k[1] for k in knots])

    def to_play(t):
        if t >= S[-1]:
            return float(P[-1] + (t - S[-1]))
        return float(np.interp(t, S, P))

    play = json.loads(json.dumps(tl))
    for sc in play["scenes"]:
        sc["start"], sc["end"] = round(to_play(sc["start"]), 3), round(to_play(sc["end"]), 3)
    for bid, b in play["beats"].items():
        b["start"], b["end"] = round(to_play(b["start"]), 3), round(to_play(b["end"]), 3)
        if b["kind"] == "line":
            b["audio"] = lines_play[bid]["file"]
    play["duration"] = round(to_play(tl["duration"]), 3)
    play["story_duration"] = tl["duration"]
    json.dump(play, open(os.path.join(ROOT, "data/timeline_play.json"), "w"), indent=1)
    json.dump({"factor": factor, "knots": [[round(s, 4), round(p, 4)] for s, p in knots]},
              open(os.path.join(ROOT, "data/timewarp.json"), "w"))
    with open(os.path.join(ROOT, "data/timeline_play.txt"), "w") as f:
        for sc in play["scenes"]:
            f.write(f"\n=== {sc['id']} {sc['slug']} [{sc['start']:.2f} - {sc['end']:.2f}] (play time)\n")
            for bid in play["order"]:
                b = play["beats"][bid]
                if b["scene"] == sc["id"]:
                    f.write(f"  {b['start']:7.2f}-{b['end']:7.2f} {bid:8s} {b.get('speaker', '--silent--'):15s} {b.get('text', '')}\n")
    print(f"dialogue x{factor}: story {tl['duration']:.1f}s -> play {play['duration']:.1f}s "
          f"(saved {tl['duration'] - play['duration']:.1f}s)")


if __name__ == "__main__":
    main()
