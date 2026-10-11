"""Shared constants and paths for the 'Anger Goes to a Comedy Show' video build."""
import os

W, H = 720, 1280          # portrait output
FPS = 24
SR = 48000                # final audio sample rate

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUILD = os.environ.get("ANGER_BUILD", os.path.join(ROOT, "build"))
MODELS = os.environ.get("KOKORO_MODELS", os.path.join(ROOT, "models"))
FONT_DIR = "/usr/share/fonts/opentype/inter"

os.makedirs(BUILD, exist_ok=True)
