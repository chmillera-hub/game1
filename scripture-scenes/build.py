"""Build entry point. Reuses the magic-show pipeline.

Usage: python3 build.py s1 [--timeline | --still T ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(HERE, "..", "magic-show"))
sys.path.insert(2, os.path.join(HERE, "..", "anger-dungeon"))
sys.path.insert(3, os.path.join(HERE, "..", "redditor-existentialist"))
os.environ.setdefault("BUILD_DIR", os.path.join(HERE, "build"))

import show  # noqa: E402

show.VOICES.update({
    "narr": ("en-US-ChristopherNeural", "-10%", "-2Hz"),
    "jesus": ("en-US-AndrewNeural", "-12%", "-2Hz"),
    "paul": ("en-US-SteffanNeural", "-10%", "-4Hz"),
})
show.E.SPEAKER_COL.update({"narr": "#FFFFFF", "jesus": "#FFE7A8", "paul": "#E8D2B0"})

import daudio  # noqa: E402,F401
import raudio  # noqa: E402,F401
import saudio  # noqa: E402,F401

if __name__ == "__main__":
    show.main()
