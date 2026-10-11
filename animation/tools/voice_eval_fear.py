import numpy as np, soundfile as sf, subprocess, os
from kokoro_onnx import Kokoro
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
exec(open('tools/voice_eval.py').read().split("cands = {")[0].split("TEXT =")[0])
k = Kokoro("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin")
asr = WhisperModel("models/whisper-base.en", device="cpu", compute_type="int8")
TEXT = "Why are you doing this? You're going to hurt me. This is a trick."
import importlib.util
src = open('tools/voice_eval.py').read()
ns = {}; exec(src[src.index('def f0'):src.index('cands = {')], {'np':np, 'k':k}, ns)
f0, blend = ns['f0'], ns['blend']
cands = {
 'nicole': ([('af_nicole',1)], 1.0, 1.0), 'nicole_up3': ([('af_nicole',1)], 1.0, 1.19),
 'nicole60_sky40_up2': ([('af_nicole',.6),('af_sky',.4)], 1.0, 1.12),
 'sky_up3': ([('af_sky',1)], 0.95, 1.19), 'bella_up2': ([('af_bella',1)], 0.95, 1.12),
 'nicole50_bella50_up2': ([('af_nicole',.5),('af_bella',.5)], 1.0, 1.12),
 'puck_up5': ([('am_puck',1)], 0.95, 1.33),
}
for name,(spec, speed, pitch) in cands.items():
    s, sr = k.create(TEXT, voice=blend(spec), speed=speed, lang='en-us')
    sf.write('out/_tmp.wav', s, sr)
    if pitch != 1.0:
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i','out/_tmp.wav','-af',f'rubberband=pitch={pitch}:formant=shifted','out/_tmp2.wav'])
        s, sr = sf.read('out/_tmp2.wav', dtype='float32')
    sf.write(f'out/fear_{name}.wav', s, sr)
    med, rng = f0(s, sr)
    segs,_ = asr.transcribe(resample_poly(s,2,3).astype(np.float32) if sr==24000 else s, word_timestamps=True, language='en')
    ws = [w for sg in segs for w in sg.words]
    print(f"{name:22s} dur={len(s)/sr:5.2f}s f0={med:6.1f} range={rng:5.1f} conf={np.mean([w.probability for w in ws]):.3f} | {''.join(w.word for w in ws).strip()}")
