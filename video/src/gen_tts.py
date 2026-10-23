import asyncio, ssl, os, json, subprocess, sys, numpy as np
import edge_tts, edge_tts.communicate as c
c._SSL_CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
sys.path.insert(0, os.path.dirname(__file__))
from script import S, VOICES
FPS = 24; SR = 44100
async def tts(e):
    v, rate, pitch = VOICES[e["sp"]]
    mp3 = f"tts/{e['id']}.mp3"; js = f"tts/{e['id']}.json"
    if os.path.exists(mp3) and os.path.exists(js) and json.load(open(js)).get("text")==e["text"]:
        return
    for attempt in range(4):
        try:
            com = edge_tts.Communicate(e["text"], v, rate=rate, pitch=pitch, proxy=os.environ["HTTPS_PROXY"], boundary="WordBoundary")
            words=[]; data=b""
            async for ch in com.stream():
                if ch["type"]=="audio": data+=ch["data"]
                elif ch["type"]=="WordBoundary": words.append(dict(w=ch["text"], t=ch["offset"]/1e7, d=ch["duration"]/1e7))
            open(mp3,"wb").write(data); json.dump(dict(text=e["text"], words=words), open(js,"w")); return
        except Exception as ex:
            print("retry", e["id"], ex); await asyncio.sleep(2**attempt)
async def main():
    await asyncio.gather(*[tts(e) for e in S if e["sp"]])
asyncio.run(main())
# decode, build timeline
t = 0.0; tl = []
for e in S:
    if not e["sp"]:
        tl.append(dict(id=e["id"], sp=None, scene=e["scene"], start=t, end=t+e["dur"])); t += e["dur"]; continue
    t += e.get("gap", 0.3)
    wav = subprocess.run(["ffmpeg","-v","quiet","-i",f"tts/{e['id']}.mp3","-f","s16le","-ac","1","-ar",str(SR),"-"],capture_output=True).stdout
    a = np.frombuffer(wav, np.int16).astype(np.float32)/32768
    # trim leading/trailing silence
    nz = np.where(np.abs(a)>0.01)[0]; s0 = max(0,nz[0]-int(0.03*SR)); s1 = min(len(a), nz[-1]+int(0.08*SR))
    a = a[s0:s1]; np.save(f"tts/{e['id']}.npy", a)
    dur = len(a)/SR
    hop = SR//FPS; env = [float(np.sqrt(np.mean(a[i:i+hop]**2))) for i in range(0,len(a),hop)]
    mx = max(env) or 1; env = [round(min(1, x/mx*1.3),3) for x in env]
    words = json.load(open(f"tts/{e['id']}.json"))["words"]
    off = s0/SR
    words = [dict(w=w["w"], t=round(t+w["t"]-off,3), d=round(w["d"],3)) for w in words]
    tl.append(dict(id=e["id"], sp=e["sp"], scene=e["scene"], text=e["text"], start=round(t,3), end=round(t+dur,3), words=words, env=env, hi=e.get("hi",[]), lo=e.get("lo",[])))
    t += dur + e.get("hold", 0.5)
json.dump(dict(fps=FPS, total=round(t,3), lines=tl), open("timeline.json","w"))
print("total", t)
