"""Captions for every spoken line (+ chosen vocal captions) and the on-screen titles.

    python3 tools/build_subtitles.py   -> data/subtitles.json, out/subs.ass (burned in by tools/encode.sh),
                                          The_Void_Has_a_Sense_of_Humor.srt (sidecar)

Phone-first: Nunito ExtraBold 42 px, max 2 lines (~27 chars each), centred in the subtitle band (y ≈ 880–1060),
tinted per speaker, dark outline. Timing from Whisper word times: a caption starts as its first word is voiced
and holds briefly after the last; tiny gaps are bridged so captions don't blink. Long lines split at punctuation
nearest the middle. Manual overrides: data/subtitle_overrides.json {beatId: {"text": "...", "split": [...]}}.
"""
import json, os, re, difflib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_LINE = 27
MAX_CAP = 54
LEAD, TAIL, MIN_DUR, BRIDGE = 0.05, 0.35, 0.9, 0.5
COL = {"NARRATOR": "FFFFFF", "JESUS": "FFE0A0", "USER": "A6DBFF", "FEAR": "E3D5FF", "MAGICIAN": "D0E2C2", "VOID": "C9BAFF"}
TITLE = "The Void Has a Sense of Humor"

def ass_col(hexrgb, alpha="00"):
    r, g, b = hexrgb[0:2], hexrgb[2:4], hexrgb[4:6]
    return f"&H{alpha}{b}{g}{r}".upper()

def ts_ass(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def ts_srt(t):
    t = max(0, t); ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))

def token_times(toks, words, start, dur):
    want = [norm(t) for t in toks]; got = [norm(w["w"]) for w in words]
    times = [None] * len(toks)
    for a, b, n in difflib.SequenceMatcher(None, want, got, autojunk=False).get_matching_blocks():
        for k in range(n):
            times[a + k] = (start + words[b + k]["start"], start + words[b + k]["end"])
    n = len(toks)
    for i in range(n):
        if times[i] is None:
            prev = next((j for j in range(i - 1, -1, -1) if times[j]), None)
            nxt = next((j for j in range(i + 1, n) if times[j]), None)
            t0 = times[prev][1] if prev is not None else start
            t1 = times[nxt][0] if nxt is not None else start + dur
            span = (nxt if nxt is not None else n) - (prev if prev is not None else -1)
            k = i - (prev if prev is not None else -1)
            times[i] = (t0 + (t1 - t0) * (k - 1) / span, t0 + (t1 - t0) * k / span)
    return times

def wrap(text):
    if len(text) <= MAX_LINE: return [text]
    words = text.split(); best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        score = max(len(a), len(b)) + (0 if re.search(r"[,.;:!?—]$", words[i - 1]) else 3)
        if best is None or score < best[0]: best = (score, [a, b])
    return best[1]

def chunks(toks):
    """split a token list into caption-sized chunks at good break points"""
    text = " ".join(toks)
    if len(text) <= MAX_CAP: return [toks]
    best = None
    for i in range(2, len(toks) - 1):
        a, b = " ".join(toks[:i]), " ".join(toks[i:])
        pen = 0 if re.search(r"[,.;:!?—]$", toks[i - 1]) else 12
        score = abs(len(a) - len(b)) + pen
        if best is None or score < best[0]: best = (score, i)
    i = best[1]
    return chunks(toks[:i]) + chunks(toks[i:])

def main():
    tl = json.load(open(os.path.join(ROOT, "data/timeline.json")))
    lines = json.load(open(os.path.join(ROOT, "data/lines.json")))
    ovp = os.path.join(ROOT, "data/subtitle_overrides.json")
    over = json.load(open(ovp)) if os.path.exists(ovp) else {}
    caps = []
    for bid in tl["order"]:
        b = tl["beats"][bid]
        if b["kind"] == "line" and bid in lines:
            L = lines[bid]
            text = over.get(bid, {}).get("text", b["text"])
            toks = text.split()
            tt = token_times(toks, L.get("words", []), b["start"], b["end"] - b["start"])
            if L.get("bleep"):   # the bleeped word appears with the bleep
                bi = next((i for i, tk in enumerate(toks) if "f***" in tk), None)
                if bi is not None:
                    tt[bi] = (b["end"] - 0.45, b["end"])
            pos = 0
            for ch in chunks(toks):
                i0, i1 = pos, pos + len(ch) - 1; pos += len(ch)
                caps.append({"beat": bid, "speaker": b["speaker"], "text": " ".join(ch), "start": tt[i0][0] - LEAD, "end": tt[i1][1] + TAIL, "kind": "line"})
        elif b["kind"] == "vocal" and b.get("caption"):
            caps.append({"beat": bid, "speaker": b["speaker"], "text": b["caption"], "start": b["start"], "end": max(b["end"], b["start"] + 1.2), "kind": "vocal"})
    caps.sort(key=lambda c: c["start"])
    # tidy timing: min duration, bridge small gaps, never overlap
    for i, c in enumerate(caps):
        c["end"] = max(c["end"], c["start"] + MIN_DUR)
        if i + 1 < len(caps):
            nxt = caps[i + 1]
            if nxt["start"] - c["end"] < BRIDGE: c["end"] = nxt["start"] - 0.04
            c["end"] = min(c["end"], nxt["start"] - 0.04)
            if c["end"] - c["start"] < 0.5: c["end"] = c["start"] + 0.5
    # titles
    titles = [{"text": TITLE, "start": 0.0, "end": 3.6, "style": "Title"}]
    bonus = next((s for s in tl["scenes"] if s["location"] == "MIND_BACKROOM"), None)
    if bonus:
        titles.append({"text": "Bonus scene", "start": bonus["start"] + 0.2, "end": bonus["start"] + 3.2, "style": "Card"})
    json.dump({"captions": caps, "titles": titles}, open(os.path.join(ROOT, "data/subtitles.json"), "w"), indent=1)
    # ---- ASS
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Nunito ExtraBold,42,&H00FFFFFF,&H00FFFFFF,&H00180F14,&H96000000,0,0,0,0,100,100,0.5,0,1,3.4,1.6,5,40,40,0,1
Style: Vocal,Nunito,34,&H00FFFFFF,&H00FFFFFF,&H00180F14,&H96000000,0,1,0,0,100,100,0.5,0,1,3,1.2,5,40,40,0,1
Style: Title,Fredoka SemiBold,60,&H00FFFFFF,&H00FFFFFF,&H00301A3A,&H64000000,0,0,0,0,100,100,1,0,1,4,3,8,50,50,150,1
Style: Card,Fredoka SemiBold,44,&H00FFE6B4,&H00FFFFFF,&H00301A3A,&H64000000,0,0,0,0,100,100,2,0,1,3.5,2,8,50,50,170,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for tt in titles:
        txt = tt["text"] if tt["style"] != "Title" else "The Void Has\\Na Sense of Humor"
        fad = "{\\fad(0,700)}" if tt["start"] == 0 else "{\\fad(350,600)}"
        ev.append(f"Dialogue: 1,{ts_ass(tt['start'])},{ts_ass(tt['end'])},{tt['style']},,0,0,0,,{fad}{txt}")
    for c in caps:
        col = ass_col(COL.get(c["speaker"], "FFFFFF"))
        txt = "\\N".join(wrap(c["text"]))
        style = "Vocal" if c["kind"] == "vocal" else "Cap"
        ev.append(f"Dialogue: 0,{ts_ass(c['start'])},{ts_ass(c['end'])},{style},{c['speaker']},0,0,0,,{{\\pos(360,968)\\c{col}}}{txt}")
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    open(os.path.join(ROOT, "out/subs.ass"), "w").write(hdr + "\n".join(ev) + "\n")
    # ---- SRT
    srt = []
    for i, c in enumerate(caps, 1):
        srt.append(f"{i}\n{ts_srt(c['start'])} --> {ts_srt(c['end'])}\n" + "\n".join(wrap(c["text"])) + "\n")
    open(os.path.join(ROOT, "The_Void_Has_a_Sense_of_Humor.srt"), "w").write("\n".join(srt))
    print(f"captions: {len(caps)}  titles: {len(titles)}")

if __name__ == "__main__":
    main()
