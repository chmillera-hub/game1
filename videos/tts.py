import wave, json
from piper import PiperVoice, SynthesisConfig
v = PiperVoice.load("en_US-ryan-high.onnx")
segs = json.load(open("segs.json"))
cfg = SynthesisConfig(length_scale=1.2, noise_scale=0.5, noise_w_scale=0.6)
for i, s in enumerate(segs):
    with wave.open(f"seg{i}.wav", "wb") as w:
        v.synthesize_wav(s["text"], w, syn_config=cfg)
    with wave.open(f"seg{i}.wav") as w:
        print(i, round(w.getnframes()/w.getframerate(), 2), w.getframerate())
