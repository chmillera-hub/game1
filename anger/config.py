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
    # cave
    "rock_dark": "#14121A", "rock_mid": "#2A2733", "rock_light": "#4A4552", "rock_warm": "#5A4636",
    "soil": "#3B2C22", "moss": "#2F4A2E", "vine": "#3E5B2E", "vine_light": "#6E8F3E", "web": "#D9D6CF",
    "water": "#1C3A4A", "water_hi": "#5FA8C0", "fungus": "#7FE0C8", "fungus_glow": "#B8FFF0",
    "wood": "#5A3B22", "wood_dark": "#3A2414", "iron": "#4B4F57",
    "torch_core": "#FFF2C0", "torch_flame": "#FFB347", "torch_ember": "#FF6A2B", "torch_light": "#FFC977",
    "dark_ambient": "#0A0D18", "night_blue": "#1A2440",
    # Anger
    "a_skin": "#C98A62", "a_skin_shade": "#9E6646", "a_skin_hi": "#E2A97E", "a_beard": "#3A2418",
    "a_hair": "#2E1C12", "a_scar": "#B0705A", "a_eye": "#5A3A22",
    "a_steel": "#8E96A3", "a_steel_shade": "#5E6672", "a_steel_hi": "#D7DEE8", "a_leather": "#5C3A24",
    "a_cloth": "#6E2A22", "a_gold": "#C9A24A",
    # cave crawler monster
    "m_skin": "#2B2A33", "m_skin_hi": "#4A4856", "m_eye": "#E8FF6A", "m_eye_glow": "#C8FF3A",
    "m_gum": "#7A2E3A", "m_tooth": "#EDE6D3", "m_drool": "#CFE8E4",
    # the big round friend
    "b_fur": "#8A6A4E", "b_fur_shade": "#6A4E38", "b_fur_hi": "#B08E6A", "b_belly": "#D8C29A",
    "b_eye": "#121014", "b_tongue": "#D9637A",
    # the voice in the dark
    "glove": "#6B4A2E", "glove_hi": "#94693F",
    "white": "#FFFFFF", "ink": "#100C12", "blood": "#7A1E1E", "tear": "#BDE7FF",
}
