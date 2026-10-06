"""Build entry point. Reuses the magic-show pipeline and earlier projects' art.

Usage: python3 build.py c1 [--timeline | --still T ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
for d in ("magic-show", "anger-dungeon", "redditor-existentialist", "scripture-scenes"):
    sys.path.append(os.path.join(HERE, "..", d))
os.environ.setdefault("BUILD_DIR", os.path.join(HERE, "build"))

import show  # noqa: E402

show.VOICES.update({
    "me": ("en-US-AndrewNeural", "+0%", "+0Hz"),
    "doubt": ("en-US-AvaNeural", "+4%", "+10Hz"),
    "cbot": ("en-US-AndrewMultilingualNeural", "-12%", "+2Hz"),
    "phar": ("en-US-EricNeural", "-4%", "-10Hz"),
})
show.E.SPEAKER_COL.update({"me": "#FFE7A8", "doubt": "#D7C2FF", "cbot": "#FFF2B8", "phar": "#FFB89A"})

import daudio  # noqa: E402,F401
import raudio  # noqa: E402,F401
import saudio  # noqa: E402,F401

if __name__ == "__main__":
    show.main()
