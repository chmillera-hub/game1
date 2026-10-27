import os

SRC = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(SRC)
OUTPUT = os.path.join(PROJECT, "output")
# Large intermediate files (voice takes, frames, mezzanine video) stay out of git.
BUILD = os.environ.get(
    "WHATIF_BUILD",
    "/tmp/claude-0/-home-user-game1/a9b092f6-4ce6-50bc-aaf9-83aebfe2e2ab/scratchpad/build_noforce",
)
VOICE = os.path.join(BUILD, "voice")
AUDIO = os.path.join(BUILD, "audio")
VIDEO = os.path.join(BUILD, "video")
CACHE = os.path.join(BUILD, "cache")

for d in (OUTPUT, BUILD, VOICE, AUDIO, VIDEO, CACHE):
    os.makedirs(d, exist_ok=True)

W, H = 1080, 1920
FPS = 24
SR = 48000
