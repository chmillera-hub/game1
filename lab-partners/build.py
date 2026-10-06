"""Build entry point for Lab Partners. Reuses the earlier projects' pipeline and art.

Usage: python3 build.py m1|m2|m3|m4 [--timeline | --still T ...]
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
    "narr": ("en-US-AndrewNeural", "+0%", "+0Hz"),
    "boredom": ("en-US-BrianNeural", "-10%", "-8Hz"),
    "doubt": ("en-US-AvaNeural", "+4%", "+10Hz"),
    "vex": ("en-US-RogerNeural", "+2%", "-6Hz"),
    "minion": ("en-US-EricNeural", "+6%", "+14Hz"),
    "heir": ("en-US-SteffanNeural", "+4%", "+6Hz"),
    "anchor": ("en-US-ChristopherNeural", "+4%", "+0Hz"),
    "goon": ("en-US-GuyNeural", "+8%", "+2Hz"),
    "council": ("en-US-ChristopherNeural", "-12%", "-16Hz"),
}
show.VOICES.update(V)
show.E.SPEAKER_COL.update({"narr": "#FFFFFF", "boredom": "#C3D7E3", "doubt": "#D7C2FF", "vex": "#B8F2A8",
                           "minion": "#FFE36A", "heir": "#FFB89A", "anchor": "#FFFFFF",
                           "goon": "#FF9C8F", "council": "#C8C8D8"})

import daudio  # noqa: E402,F401
import raudio  # noqa: E402,F401
import saudio  # noqa: E402,F401
import maudio  # noqa: E402,F401

if __name__ == "__main__":
    show.main()
