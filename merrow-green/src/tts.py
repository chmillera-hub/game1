import wave, json
from piper import PiperVoice, SynthesisConfig
from script import LINES
v = PiperVoice.load("../voices/en_US-ryan-medium.onnx")
cfg = SynthesisConfig(length_scale=1.1, noise_scale=0.6, noise_w_scale=0.7)
durs=[]
for i,t in enumerate(LINES):
    with wave.open(f"line{i}.wav","wb") as w:
        v.synthesize_wav(t,w,syn_config=cfg)
    with wave.open(f"line{i}.wav") as w:
        durs.append(w.getnframes()/w.getframerate())
json.dump(durs,open("durs.json","w"))
print(durs, sum(durs))
