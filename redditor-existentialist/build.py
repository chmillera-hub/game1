"""Build entry point. Reuses the magic-show pipeline and the dungeon sound library.

Usage: python3 build.py r1|r2|r3 [--timeline | --still T ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(HERE, "..", "magic-show"))
sys.path.insert(2, os.path.join(HERE, "..", "anger-dungeon"))
os.environ.setdefault("BUILD_DIR", os.path.join(HERE, "build"))

import show  # noqa: E402

show.VOICES.update({
    "narr": ("en-US-AndrewNeural", "+0%", "+0Hz"),
    "me": ("en-US-AndrewNeural", "+0%", "+0Hz"),
    "redditor": ("en-US-EricNeural", "-4%", "-2Hz"),
    "doubt": ("en-US-AvaNeural", "+4%", "+10Hz"),
    "anger": ("en-US-GuyNeural", "-2%", "-12Hz"),
    "boredom": ("en-US-BrianNeural", "-16%", "-10Hz"),
})
show.E.SPEAKER_COL.update({"redditor": "#B8C4D8", "doubt": "#D7C2FF", "anger": "#FF9C8F",
                           "narr": "#FFFFFF", "me": "#FFE7A8", "boredom": "#C3D7E3"})

import daudio  # noqa: E402,F401  (dungeon sounds and moods)
import raudio  # noqa: E402,F401  (extra sounds and moods)

if __name__ == "__main__":
    show.main()
