import json, subprocess, wave, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from narration import SCENES
VOICE = os.environ["VOICE"]
os.makedirs("audio", exist_ok=True)
GAP = 0.45      # pause between sentences
PAD_START = 0.6 # lead-in per scene
PAD_END = 1.0   # tail per scene
def dur(p):
    with wave.open(p) as w: return w.getnframes()/w.getframerate(), w.getframerate()
t = 0.0; out = []; sr=None; chunks=[]
for si,(sid,sents) in enumerate(SCENES):
    start = t; t += PAD_START
    sd = []
    for k,s in enumerate(sents):
        p = f"audio/{si:02d}_{k}.wav"
        subprocess.run(["python3","-m","piper","-m",VOICE,"--length-scale","1.0","-f",p],input=s.encode(),check=True,capture_output=True)
        d,sr = dur(p)
        sd.append({"text":s,"start":t,"end":t+d,"file":p}); t += d + GAP
    t += PAD_END - GAP
    out.append({"id":sid,"start":start,"end":t,"sents":sd})
json.dump({"scenes":out,"total":t,"sr":sr}, open("timeline.json","w"), indent=1)
print("total", t)
