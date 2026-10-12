"""Build the explainer: voices -> timeline -> audio mix -> frames -> final MP4.

    python3 build.py            # full build
    python3 build.py --audio    # stop after the audio mix
"""
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

import audio
import render
import timeline

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
OUT = os.path.join(HERE, "output", "hit-and-hide-explainer.mp4")


def main():
    os.makedirs(BUILD, exist_ok=True)
    print("1/4 voices + timeline")
    tl, track, mouth, rnd, qa = timeline.build()
    timeline.save(tl, mouth, rnd, render.TL_PATH)
    print(f"    {len(tl['beats'])} beats, {tl['total']:.1f}s")
    print("2/4 music, sound effects, mix")
    mix = audio.mix(track, tl["scenes"], tl["sfx"], tl["total"])
    wav = os.path.join(BUILD, "mix.wav")
    sf.write(wav, mix, audio.SR)
    if "--audio" in sys.argv:
        return
    print("3/4 rendering frames")
    vid = os.path.join(BUILD, "video_only.mp4")
    render.render_video(vid, workers=int(os.environ.get("WORKERS", "4")))
    print("4/4 mux + loudness normalize")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vid, "-i", wav,
                    "-af", "loudnorm=I=-15:TP=-1.5:LRA=11", "-ar", "48000",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", OUT], check=True)
    print("done:", OUT)


if __name__ == "__main__":
    main()
