#!/usr/bin/env python3
"""Build the animated story.

    python3 build.py 1 2 3            # render all three parts to out/
    python3 build.py 1 --stills 5,12  # just render still frames (seconds) for a quick look
    python3 build.py 1 --info         # print the timeline (shot starts, total length)
"""
import argparse
import importlib
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from toon.engine import render_video, render_still, SPEAKERS  # noqa: E402

OUT = os.path.join(HERE, "out")
BUILD = os.path.join(HERE, "build")


def load(n):
    mod = importlib.import_module(f"story.part{n}")
    return mod.build()


def screenplay(parts, path):
    lines = ["# Emotional Education — screenplay", "",
             "Generated from the scripts in `story/`. Timestamps are from the rendered videos.", ""]
    for p in parts:
        lines += [f"## Part {p.num}: {p.subtitle}", ""]
        for s in p.shots:
            for ln in s.lines:
                t = s.t0 + ln.t0
                stamp = f"`{int(t // 60)}:{t % 60:04.1f}`"
                if ln.style == "cc":
                    lines.append(f"{stamp} *{ln.text}*  ")
                    continue
                name = SPEAKERS.get(ln.vkey, (ln.vkey, ""))[0]
                tag = {"think": " (thinking)", "whisper": " (whispering)", "shout": " (yelling)"}.get(ln.style, "")
                lines.append(f"{stamp} **{name}{tag}:** {ln.text}  ")
        lines.append("")
    with open(path, "w") as f:
        f.write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("parts", nargs="*", type=int, default=[1, 2, 3])
    ap.add_argument("--stills", default="")
    ap.add_argument("--info", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--crf", type=int, default=20)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    built = []
    for n in args.parts:
        t0 = time.time()
        part = load(n)
        built.append(part)
        print(f"part {n}: {part.total:.1f}s, {len(part.shots)} shots (script built in {time.time() - t0:.1f}s)")
        if args.info:
            for i, s in enumerate(part.shots):
                first = s.lines[0].text[:60] if s.lines else ""
                print(f"  [{i:02d}] {s.t0:6.1f}s +{s.dur:5.1f}  {s.set:8s} {first}")
            continue
        if args.stills:
            d = os.path.join(BUILD, f"stills{n}")
            os.makedirs(d, exist_ok=True)
            for ts in args.stills.split(","):
                t = float(ts)
                render_still(part, t, os.path.join(d, f"t{t:06.1f}.png"))
            print("stills ->", d)
            continue
        base = f"part{n}-{part.slug.split('-', 1)[1]}"
        mp4 = os.path.join(OUT, f"{base}.mp4")
        render_video(part, mp4, os.path.join(BUILD, f"part{n}"), workers=args.workers, crf=args.crf)
        part.write_srt(os.path.join(OUT, f"{base}.srt"))
        print(f"  -> {mp4} ({time.time() - t0:.0f}s)")
    if not args.info and not args.stills and len(built) == 3:
        screenplay(built, os.path.join(HERE, "SCREENPLAY.md"))


if __name__ == "__main__":
    main()
