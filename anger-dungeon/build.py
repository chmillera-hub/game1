"""Build entry point. Reuses the magic-show pipeline (voices, timeline, audio, render).

Usage: python3 build.py d1|d2|d3 [--timeline | --still T ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(HERE, "..", "magic-show"))
os.environ.setdefault("BUILD_DIR", os.path.join(HERE, "build"))

import show  # noqa: E402

show.VOICES.update({
    "narr": ("en-US-ChristopherNeural", "-6%", "-4Hz"),
    "anger": ("en-US-GuyNeural", "-8%", "-14Hz"),
    "stranger": ("en-US-RogerNeural", "+2%", "-6Hz"),
})
show.E.SPEAKER_COL.update({"anger": "#FF9C8F", "stranger": "#E8C77A", "narr": "#FFFFFF"})

import daudio  # noqa: E402,F401  (registers sounds and music)

if __name__ == "__main__":
    show.main()
