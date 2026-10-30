"""Check a direction file against SPEC.md enums and the act's beat ids.
Usage: python3 direction/validate.py <act_index> direction/actN.json [first_id last_id]"""
import json, re, sys

act = int(sys.argv[1])
path = sys.argv[2]
spec = open(__file__.replace("validate.py", "SPEC.md")).read()
beats = json.load(open(__file__.replace("direction/validate.py", "script/beats.json")))

def enum_after(label):
    m = re.search(label + r"(.*?)`\n", spec, re.S)
    return set(re.findall(r"([a-z_]+)", m.group(1))) if m else set()

shots = set(re.findall(r"`((?:room|ship|void|memory|nv|vision)_[a-z_]+)`", spec))
vigs = set(re.findall(r"^\| `([a-z_]+)` \|", spec, re.M)) | {"custom"}
exprs = set(re.search(r"- `expr`: one of `([^`]+)`", spec, re.S).group(1).replace("\n", " ").replace(" ", "").split(","))
gestures = set(re.search(r"- `gesture`: `([^`]+)`", spec, re.S).group(1).replace("\n", " ").replace(" ", "").split(","))
gazes = {"other", "camera", "down", "up", "away", "window", "vision", "hands", "far"}
moods = {"intimate", "curious", "wonder", "melancholy", "grief", "dread", "tension", "resolve", "hope",
         "tender", "playful", "awe", "triumph", "silence"}
kinds = {"high", "low", "swell", "light", "hit"}
charkeys = {"human", "ai", "last_human", "suffering", "boredom", "loneliness"}

lo, hi = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 10**9)
want = {b["id"]: b for b in beats if b.get("act") == act and b["kind"] != "act_card" and lo <= b["id"] <= hi}
data = json.load(open(path))
errs = []
seen = set()
for d in data:
    i = d.get("id")
    if i not in want:
        errs.append(f"id {i} not a beat of act {act}"); continue
    seen.add(i)
    if d.get("shot") not in shots: errs.append(f"{i}: bad shot {d.get('shot')}")
    v = d.get("vignette")
    if v is not None and v not in vigs: errs.append(f"{i}: bad vignette {v}")
    for k, c in (d.get("chars") or {}).items():
        if k not in charkeys: errs.append(f"{i}: bad char {k}"); continue
        if c.get("expr") not in exprs: errs.append(f"{i}: {k} bad expr {c.get('expr')}")
        if c.get("gaze", "other") not in gazes: errs.append(f"{i}: {k} bad gaze {c.get('gaze')}")
        if c.get("gesture", "idle") not in gestures: errs.append(f"{i}: {k} bad gesture {c.get('gesture')}")
        g = c.get("glance")
        if g and g.get("to") not in ("down", "up", "away", "vision"): errs.append(f"{i}: {k} bad glance {g}")
    m = d.get("music") or {}
    if m.get("mood") and m["mood"] not in moods: errs.append(f"{i}: bad mood {m['mood']}")
    cue = m.get("cue")
    if cue:
        if cue.get("kind") not in kinds: errs.append(f"{i}: bad cue kind {cue}")
        b = want[i]
        if b["kind"] == "speech" and cue.get("word", "").lower().strip(".,?!\"") not in b["text"].lower():
            errs.append(f"{i}: cue word {cue.get('word')!r} not in line")
missing = sorted(set(want) - seen)
if missing: errs.append(f"missing ids: {missing}")
print("\n".join(errs) if errs else f"OK: {len(data)} beats")
sys.exit(1 if errs else 0)
