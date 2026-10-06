"""Build entry point. Reuses the magic-show pipeline and scripture-scenes art.

Usage: python3 build.py v1 [--timeline | --still T ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
for d in ("magic-show", "anger-dungeon", "redditor-existentialist", "scripture-scenes"):
    sys.path.append(os.path.join(HERE, "..", d))
os.environ.setdefault("BUILD_DIR", os.path.join(HERE, "build"))

import show  # noqa: E402

V = {
    "narr": ("en-US-ChristopherNeural", "-8%", "-2Hz"),
    "maya": ("en-US-AnaNeural", "+0%", "+0Hz"),
    "lily": ("en-US-AnaNeural", "+6%", "+4Hz"),
    "otis": ("en-US-RogerNeural", "-12%", "-8Hz"),
    "coach": ("en-US-GuyNeural", "-2%", "-4Hz"),
    "rosa": ("en-US-JennyNeural", "-4%", "+0Hz"),
    "dad": ("en-US-BrianNeural", "-6%", "-2Hz"),
    "marcus": ("en-US-SteffanNeural", "-8%", "-6Hz"),
    "grace": ("en-US-MichelleNeural", "-8%", "+0Hz"),
    "leader": ("en-US-AndrewNeural", "-10%", "-2Hz"),
}
show.VOICES.update(V)
show.E.SPEAKER_COL.update({k: "#FFE7A8" for k in V})
show.E.SPEAKER_COL["narr"] = "#FFFFFF"

import daudio  # noqa: E402,F401
import raudio  # noqa: E402,F401
import saudio  # noqa: E402,F401

if __name__ == "__main__":
    show.main()
