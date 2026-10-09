"""Global constants for the "If You Have Time" short.

Every module imports from here so paths, frame size and palette stay in one place.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
OUT = ROOT / "out"
VO_DIR = BUILD / "vo"
MUSIC_DIR = BUILD / "music"
SFX_DIR = BUILD / "sfx"
TIMELINE = BUILD / "timeline.json"
LIPSYNC = BUILD / "lipsync.json"
MUSIC_ENV = BUILD / "music" / "envelopes.json"

MODELS = Path("/home/user/models")
KOKORO_MODEL = MODELS / "kokoro-v1.0.onnx"
KOKORO_VOICES = MODELS / "voices-v1.0.bin"
SOUNDFONT = Path("/usr/share/sounds/sf3/MuseScore_General_Full.sf3")
SOUNDFONT_ALT = Path("/usr/share/sounds/sf2/FluidR3_GM.sf2")

# Video
W, H = 720, 1280          # portrait 9:16
FPS = 24
SR = 48000                # audio sample rate for the final mix

# Palette (hex strings, use anim.core.col() to convert)
PAL = {
    # ship / lounge
    "space_deep": "#05060F",
    "space_mid": "#0B1030",
    "nebula_a": "#3B2C85",
    "nebula_b": "#1E6F8C",
    "nebula_c": "#B23A7A",
    "wall_dark": "#121A2E",
    "wall_mid": "#1B2742",
    "wall_light": "#2A3A5C",
    "floor": "#0E1424",
    "trim": "#3E5683",
    "amber": "#F4A259",
    "amber_soft": "#FFD29A",
    "teal": "#2EC4B6",
    "teal_glow": "#7FFFE9",
    "console_red": "#FF5D73",
    # Quill (android)
    "q_skin": "#D7DCE3",
    "q_skin_shade": "#AEB8C6",
    "q_skin_hi": "#F3F6FA",
    "q_seam": "#93A0B3",
    "q_hair": "#1D2740",
    "q_hair_hi": "#3B4C73",
    "q_iris": "#5FE3D0",
    "q_iris_glow": "#B9FFF5",
    "q_uniform": "#262B38",
    "q_uniform_shade": "#1A1E28",
    "q_collar": "#2EC4B6",
    "q_insignia": "#DDE6F0",
    # Rae (human)
    "r_skin": "#A0673C",
    "r_skin_shade": "#7E4D2A",
    "r_skin_hi": "#C08458",
    "r_hair": "#2A1A12",
    "r_hair_hi": "#4E3122",
    "r_iris": "#3B2416",
    "r_lips": "#7A3B2E",
    "r_shirt": "#E09F3E",
    "r_jacket": "#3A3F58",
    "r_jacket_shade": "#2B2F44",
    "r_pants": "#2C3148",
    "mug": "#F1F1EE",
    "mug_text": "#D64545",
    # emotion
    "tear": "#BDE7FF",
    "blush": "#E0786B",
    "white": "#FFFFFF",
    "ink": "#141018",
}
