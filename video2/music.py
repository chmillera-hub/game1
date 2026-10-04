import json, wave, numpy as np
tl = json.load(open("timeline.json")); sr = tl["sr"]; N = int(tl["total"]*sr)+sr
voice = np.zeros(N, np.float32)
for sc in tl["scenes"]:
    for s in sc["sents"]:
        with wave.open(s["file"]) as w:
            a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)/32768
        i = int(s["start"]*sr); voice[i:i+len(a)] += a
# ambient pad: per-scene chord, dark (minor) -> hopeful (major)
F = lambda m: 440*2**((m-69)/12)
chords = {"title":[43,50,55],"launch":[48,55,60,64],"crowd":[45,52,57,60],"dream":[48,55,59,64],"leap":[53,60,64,69],
 "fall":[41,48,53,56],"impact":[38,45,50,53],"lying":[40,47,52,55],"comfort":[43,50,55,58],"repost":[48,55,60,64],
 "rope":[50,57,62,66],"arms":[48,55,60,64,67],"end":[48,55,60,64,67,72]}
t = np.arange(N)/sr; pad = np.zeros(N, np.float32)
for sc in tl["scenes"]:
    a,b = int((sc["start"]-1.0)*sr), int((sc["end"]+1.0)*sr); a=max(a,0); b=min(b,N)
    seg = np.zeros(b-a, np.float32); tt = t[a:b]
    for m in chords[sc["id"]]:
        f=F(m)
        seg += np.sin(2*np.pi*f*tt)+0.4*np.sin(2*np.pi*f*2*tt+1)+0.15*np.sin(2*np.pi*f*3*tt)
        seg += 0.6*np.sin(2*np.pi*(f*1.003)*tt)   # slight detune for warmth
    seg *= (0.75+0.25*np.sin(2*np.pi*0.12*tt))
    env = np.minimum(1, np.minimum(np.arange(len(seg)), len(seg)-np.arange(len(seg)))/(1.2*sr))
    pad[a:b] += seg*env/len(chords[sc["id"]])
pad /= np.abs(pad).max(); voice /= max(np.abs(voice).max(),1e-6)
# duck pad under voice
duck = np.convolve(np.abs(voice), np.ones(int(sr*0.3))/(sr*0.3), "same"); duck = np.clip(duck*8,0,1)
mix = 0.9*voice + 0.16*pad*(1-0.55*duck)
mix = np.clip(mix,-1,1)
with wave.open("mix.wav","wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((mix*32767).astype(np.int16).tobytes())
