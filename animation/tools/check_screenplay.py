"""Validate a screenplay JSON and estimate runtime. Usage: python3 check_screenplay.py file.json"""
import json, sys, re
SPEAKERS = {"NARRATOR","CONSCIOUSNESS","FEAR","JOY","SADNESS","ANGER","CALM"}
SFX = set("alarm_bell alarm_pull footsteps door_whoosh crowd_murmur heartbeat breath_shaky sob cage_close lock_click cage_creak key_turn rumble_low shimmer twinkle console_beeps paper_rustle lamp_click cloth_rustle rust_creak".split())
WPS = 2.05  # slow delivery words/sec (Kokoro speed ~0.85)
d = json.load(open(sys.argv[1]))
errs = []; total = 0.0; ids = set(); nlines = 0; words = 0
for s in d["scenes"]:
    st = 0.0
    for b in s["beats"]:
        if b["id"] in ids: errs.append(f"dup id {b['id']}")
        ids.add(b["id"])
        if b["kind"] == "line":
            if b.get("speaker") not in SPEAKERS: errs.append(f"{b['id']} bad speaker {b.get('speaker')}")
            t = b.get("text","")
            if re.search(r"[\[\]\(\)\*]|[^\x00-\x7F’‘“”—–…]", t): errs.append(f"{b['id']} text has brackets/emoji/non-ascii: {t!r}")
            n = len(t.split()); words += n; nlines += 1
            st += n / WPS + 0.35 * t.count(",") + 0.5 * len(re.findall(r"[.?!…]", t))
        elif b["kind"] == "silent":
            st += float(b["duration"])
        else: errs.append(f"{b['id']} bad kind")
        st += float(b.get("pause_after", 0))
        for x in b.get("sfx", []) or []:
            if x not in SFX: errs.append(f"{b['id']} unknown sfx {x}")
        if not b.get("acting"): errs.append(f"{b['id']} missing acting")
    total += st
    print(f"{s['id']:>5} {s.get('slug',''):<22} {st:6.1f}s  beats={len(s['beats'])}")
print(f"TOTAL ~{total:.0f}s ({total/60:.1f} min), lines={nlines}, words={words}")
print("ERRORS:" if errs else "OK: no format errors")
for e in errs: print("  -", e)
