import json, subprocess, wave, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from narration import SCENES
S = os.environ["VOICES"]   # dir with alan.onnx, v.onnx (ryan), lessac.onnx
SR = 22050
VOICE = {"n": (S+"/en_US-hfc_male-medium.onnx", 1.05, "", 1.0),
         "d": (S+"/alan.onnx", 1.05, "aecho=0.6:0.4:40:0.12", 0.9),
         "f": (S+"/v.onnx", 1.12, "aecho=0.8:0.7:110|230:0.5|0.35,volume=1.5,alimiter=limit=0.95", 0.82),
         "j": (S+"/en_US-joe-medium.onnx", 1.1, "", 1.0)}
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
