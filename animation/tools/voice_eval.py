import numpy as np, soundfile as sf, sys
from kokoro_onnx import Kokoro
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
k = Kokoro("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin")
asr = WhisperModel("models/whisper-base.en", device="cpu", compute_type="int8")
TEXT = "And then, one day, I put my hand on Fear's shoulder. It was shaking. And I said, you need to stop pulling the fire alarm."
def f0(a, sr):
    fr = int(sr*0.04); hop = int(sr*0.01); out=[]
    for i in range(0, len(a)-fr, hop):
        x = a[i:i+fr]; 
        if np.sqrt((x**2).mean()) < 0.02: continue
        x = x - x.mean(); ac = np.correlate(x, x, 'full')[fr-1:]
        lo, hi = int(sr/400), int(sr/70)
        j = lo + np.argmax(ac[lo:hi])
        if ac[j] > 0.3*ac[0]: out.append(sr/j)
    return np.median(out) if out else 0, np.percentile(out,90)-np.percentile(out,10) if out else 0
def blend(spec):
    st = None
    for name, w in spec:
        v = k.get_voice_style(name) * w
        st = v if st is None else st + v
    return st
cands = {
 'af_heart': [('af_heart',1)], 'af_bella': [('af_bella',1)], 'af_nicole':[('af_nicole',1)], 'bf_emma':[('bf_emma',1)],
 'am_michael':[('am_michael',1)], 'am_fenrir':[('am_fenrir',1)], 'am_puck':[('am_puck',1)], 'af_sky':[('af_sky',1)],
 'heart50_michael50':[('af_heart',.5),('am_michael',.5)], 'heart60_fenrir40':[('af_heart',.6),('am_fenrir',.4)],
 'heart40_michael60':[('af_heart',.4),('am_michael',.6)],
}
for name, spec in cands.items():
    style = blend(spec)
    s, sr = k.create(TEXT, voice=style, speed=0.85, lang='en-us')
    sf.write(f'out/voice_{name}.wav', s, sr)
    med, rng = f0(s, sr)
    segs,_ = asr.transcribe(resample_poly(s,2,3).astype(np.float32), word_timestamps=True, language='en')
    ws = [w for sg in segs for w in sg.words]
    txt = ''.join(w.word for w in ws).strip()
    conf = np.mean([w.probability for w in ws])
    print(f"{name:20s} dur={len(s)/sr:5.2f}s f0={med:6.1f}Hz range={rng:5.1f} conf={conf:.3f} | {txt}")
