"""Validate a screenplay JSON against data/SCREENPLAY_FORMAT.md and estimate runtime.

    python3 tools/check_screenplay.py data/screenplay.json
"""
import json, re, sys

SPEAKERS = {"NARRATOR", "JESUS", "USER", "FEAR", "MAGICIAN"}
VOCAL_SPEAKERS = SPEAKERS | {"VOID"}
VOCALS = {"laugh_maniacal", "laugh_soft", "giggle", "snort", "whisper", "huff", "sigh", "hum", "cough", "gasp",
          "scream_short", "mmhm", "whimper", "gulp"}
SFX = set("""footsteps_soft footsteps_run footsteps_stomp sparkle_appear thud_sit cloth_rustle whoosh star_pop
galaxy_whirl bleep phone_tap notification_ding block_thunk wind_soft shimmer twinkle nebula_swell rumble_low
cage_creak lock_click kick_thump whoosh_fly crash_buckets mop_clatter bucket_bonk cartoon_birdies dust_sparkle
dagger_shing gulp pat_pat""".split())
LOCS = {"THE_EDGE", "MIND_BACKROOM"}
WPM = {"NARRATOR": 150, "JESUS": 145, "USER": 165, "FEAR": 150, "MAGICIAN": 140}


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/screenplay.json"
    sp = json.load(open(path))
    errs, warns = [], []
    ids = set()
    total = 0.0
    marks = 0
    lines = 0
    for k in ("title", "logline", "voice_notes", "scenes"):
        if k not in sp:
            errs.append(f"missing top-level key {k}")
    for sc in sp.get("scenes", []):
        sid = sc.get("id", "?")
        if sc.get("location") not in LOCS:
            errs.append(f"{sid}: bad location {sc.get('location')}")
        if sc.get("transition_in", "cut") not in ("cut", "dissolve"):
            errs.append(f"{sid}: bad transition_in")
        for b in sc.get("beats", []):
            bid = b.get("id", "?")
            if bid in ids:
                errs.append(f"duplicate beat id {bid}")
            ids.add(bid)
            if not bid.startswith(sid + "b"):
                errs.append(f"{bid}: id must start with {sid}b")
            kind = b.get("kind")
            for k in ("shot", "action", "acting"):
                if not b.get(k):
                    warns.append(f"{bid}: missing {k}")
            for s in b.get("sfx", []):
                if s not in SFX:
                    errs.append(f"{bid}: unknown sfx {s}")
            if kind == "line":
                if b.get("speaker") not in SPEAKERS:
                    errs.append(f"{bid}: bad speaker {b.get('speaker')}")
                t = b.get("text", "")
                if re.search(r"[\[\]{}<>*_#]", t.replace("f***", "")):
                    errs.append(f"{bid}: text has brackets/markup other than ^/~ : {t}")
                m = len(re.findall(r"[\^~]\w", t))
                marks += m
                lines += 1
                if m > 2:
                    warns.append(f"{bid}: {m} stinger marks (max 2)")
                words = len(re.findall(r"[A-Za-z']+", t))
                dur = words / WPM.get(b.get("speaker"), 150) * 60 + 0.25
                total += dur + float(b.get("pause_after", 0))
            elif kind == "vocal":
                if b.get("speaker") not in VOCAL_SPEAKERS:
                    errs.append(f"{bid}: bad vocal speaker")
                if b.get("vocal") not in VOCALS:
                    errs.append(f"{bid}: bad vocal {b.get('vocal')}")
                if "duration" not in b:
                    errs.append(f"{bid}: vocal needs duration")
                if not b.get("overlap"):
                    total += float(b.get("duration", 0)) + float(b.get("pause_after", 0))
            elif kind == "silent":
                if "duration" not in b:
                    errs.append(f"{bid}: silent needs duration")
                total += float(b.get("duration", 0)) + float(b.get("pause_after", 0))
            else:
                errs.append(f"{bid}: bad kind {kind}")
    print(f"scenes={len(sp.get('scenes', []))} beats={len(ids)} lines={lines} stinger_marks={marks} "
          f"est_runtime={total:.0f}s ({total/60:.2f} min)")
    for w in warns:
        print("WARN", w)
    for e in errs:
        print("ERROR", e)
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
