import os

HERE = os.path.dirname(os.path.abspath(__file__))
# Large downloads (TTS model, voices) and intermediate renders live outside the repo.
WORK = os.environ.get("BOL_WORK", os.path.join(HERE, "_work"))
MODELS = os.environ.get("BOL_MODELS", os.path.join(WORK, "models"))

W, H = 720, 1280
FPS = 24
SR = 48000  # final audio sample rate
TTS_SR = 24000

os.makedirs(WORK, exist_ok=True)
