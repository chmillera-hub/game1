#!/usr/bin/env python3
"""make.py -- rebuild THE STONE AND THE BREAD from source, end to end.

    python3 film/make.py [--jobs 4] [--skip-audio] [--skip-render]

Steps: dialogue + timeline (film/audio/tts.py, reuses committed wavs), the bard's song
(film/audio/song.py), the soundtrack mix (film/audio/mix.py), every scene (film/render.py --all),
and the final encode with captions (film/assemble.py).
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(*args):
    print("\n==>", " ".join(args), flush=True)
    subprocess.run([sys.executable, *args], check=True, cwd=ROOT.parent)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--skip-audio", action="store_true")
    ap.add_argument("--skip-render", action="store_true")
    a = ap.parse_args()
    if not a.skip_audio:
        run("film/audio/song.py")
        run("film/audio/tts.py")
        run("film/audio/mix.py")
    if not a.skip_render:
        run("film/render.py", "--all", "--jobs", str(a.jobs))
    run("film/assemble.py")


if __name__ == "__main__":
    main()
