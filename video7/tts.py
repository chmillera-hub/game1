import json, subprocess, wave, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from narration import SCENES
S = os.environ["VOICES"]   # dir with alan.onnx, v.onnx (ryan), lessac.onnx
SR = 22050
VOICE = {"n": (S+"/en_US-hfc_male-medium.onnx", 1.05, "", 1.0),
         "b": (S+"/alan.onnx", 1.28, "", 0.86),
         "l": (S+"/en_US-joe-medium.onnx", 1.35, "tremolo=f=6:d=0.3,aecho=0.6:0.4:60:0.15,volume=0.8", 1.22),
         "f": (S+"/en_US-hfc_male-medium.onnx", 0.78, "", 1.3),
         "a": (S+"/v.onnx", 0.95, "volume=1.3,alimiter=limit=0.95", 0.86),
         "s": (S+"/lessac.onnx", 1.1, "aecho=0.6:0.4:50:0.12", 1.0)}
os.makedirs("audio", exist_ok=True)
def dur(p):
    with wave.open(p) as w: return w.getnframes()/w.getframerate()
t = 0.0; out = []; k = 0
for sc in SCENES:
    start = t; t += sc["pre"]; sents = []
    for it in sc["items"]:
        if "silence" in it:
            sents.append({"who":"silence","text":"","tag":it.get("tag"),"start":t,"end":t+it["silence"],"file":None}); t += it["silence"]; continue
        t += it.get("gap", 0.45)
        who = it["who"]; model, ls, fx, pitch = VOICE[who]
        raw = f"audio/r{k}.wav"; fin = f"audio/{k:02d}_{sc['id']}.wav"; k += 1
        subprocess.run(["python3","-m","piper","-m",model,"--length-scale",str(ls),"-f",raw], input=it["text"].encode(), check=True, capture_output=True)
        d = dur(raw)
        chain = []
        if it.get("trunc"):
            d = d * it["trunc"]; chain.append(f"atrunc")  # placeholder replaced below
        cmd = ["ffmpeg","-y","-loglevel","error","-i",raw]
        filt = []
        if it.get("trunc"): filt.append(f"atrim=0:{d:.3f},afade=t=out:st={d-0.12:.3f}:d=0.12")
        if pitch != 1.0: filt.insert(0, "asetrate=%d,aresample=%d" % (int(SR * pitch), SR))
        if fx: filt.append(fx)
        if filt: cmd += ["-af", ",".join(filt)]
        cmd += ["-ar", str(SR), "-ac", "1", fin]
        subprocess.run(cmd, check=True)
        if who == "e": d = min(dur(fin), d / 0.76 + 0.4)
        sents.append({"who":who,"text":it["text"],"label":it.get("label"),"tag":it.get("tag"),"start":t,"end":t+d,"file":fin})
        t += d
    t += sc["post"]
    out.append({"id":sc["id"],"start":start,"end":t,"sents":sents})
json.dump({"scenes":out,"total":t,"sr":SR}, open("timeline.json","w"), indent=1)
print("total", t)
