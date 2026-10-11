"""Build phrase-sized captions for every spoken line (PLAY time).

    python3 tools/build_subtitles.py      -> data/subtitles.json, out/subtitles.srt
    node src/render.mjs --place-subs        (then choose on-screen positions that avoid faces)

Text is the screenplay's, one sentence (or short sentence pair) per caption; long sentences split at the
comma nearest the middle. Timing comes from the voice itself: word timestamps (faster-whisper) locate the
words, and the line's energy envelope locates the real pauses, so a caption starts when its first word is
voiced and ends just after its last word, not at Whisper's padded word edges. Captions snap to nearby shot
cuts (data/cuts_play.json from tools/detect_cuts.py), are held longer when reading speed would exceed ~15
characters/second, and split automatically where a pause of 0.8 s or more falls between sentences.
Manual overrides: data/subtitle_overrides.json.
"""
import difflib, json, os, re
import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_CHARS = 62        # ~2 lines at 32 px Inter in a 520 px box
MIN_DUR = 1.0
CPS = 15.0            # comfortable reading speed (characters / second)
LEAD, TAIL = 0.05, 0.3
SPLIT_GAP = 0.8       # pause between sentences that starts a new caption


def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))


def token_times(text, words, line_start, line_dur):
    toks = text.split()
    want = [norm(t) for t in toks]
    got = [norm(w["w"]) for w in words]
    times = [None] * len(toks)
    sm = difflib.SequenceMatcher(None, want, got, autojunk=False)
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            w = words[b + k]
            times[a + k] = (line_start + w["start"], line_start + w["end"])
    n = len(toks)
    for i in range(n):
        if times[i] is None:
            prev = next((j for j in range(i - 1, -1, -1) if times[j]), None)
            nxt = next((j for j in range(i + 1, n) if times[j]), None)
            t0 = times[prev][1] if prev is not None else line_start
            t1 = times[nxt][0] if nxt is not None else line_start + line_dur
            span = (nxt if nxt is not None else n) - (prev if prev is not None else -1)
            k = i - (prev if prev is not None else -1)
            times[i] = (t0 + (t1 - t0) * (k - 1) / span, t0 + (t1 - t0) * k / span)
    return toks, times


def voiced_segments(wav, offset):
    """[(start, end)] of speech in absolute play time, gaps under 0.12 s merged"""
    a, sr = sf.read(wav, dtype="float32")
    if a.ndim > 1:
        a = a.mean(1)
    hop = int(sr * 0.01)
    n = len(a) // hop
    rms = np.sqrt(np.mean(a[: n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    thr = max(np.percentile(db, 95) - 32, -50)
    on = db > thr
    segs, i = [], 0
    while i < n:
        if on[i]:
            j = i
            while j < n and on[j]:
                j += 1
            segs.append([i * 0.01, j * 0.01])
            i = j
        else:
            i += 1
    merged = []
    for s in segs:
        if merged and s[0] - merged[-1][1] < 0.12:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    return [(offset + s, offset + e) for s, e in merged if e - s > 0.03]


def gaps_between(segs, t0, t1):
    """silences fully or partly inside [t0, t1]: [(gap_start, gap_end)]"""
    out = []
    for (s0, e0), (s1, e1) in zip(segs, segs[1:]):
        if e0 < t1 and s1 > t0:
            out.append((e0, s1))
    return out


def chunk_tokens(toks, split_after=()):
    """one sentence per caption; short sentences merged; long ones split near the middle (comma preferred)"""
    def length(ix):
        return len(" ".join(toks[i] for i in ix))
    sents, cur = [], []
    for i, t in enumerate(toks):
        cur.append(i)
        if re.search(r"[.?!]$", t) or t in split_after:
            sents.append(cur); cur = []
    if cur:
        sents.append(cur)
    forced = {i for i, t in enumerate(toks) if t in split_after}
    merged = []
    for st in sents:
        if merged and merged[-1][-1] not in forced and (length(merged[-1]) < 16 or length(st) < 10) \
                and length(merged[-1] + st) <= MAX_CHARS:
            merged[-1] = merged[-1] + st
        else:
            merged.append(st)
    out = []
    for st in merged:
        if length(st) <= MAX_CHARS:
            out.append(st); continue
        k = -(-length(st) // MAX_CHARS)
        total = length(st)
        cuts, start = [], 0
        for j in range(1, k):
            ideal = total * j / k
            best, best_cost = None, 1e9
            for m in range(start + 1, len(st)):
                pos = length(st[:m])
                cost = abs(pos - ideal) - (14 if toks[st[m - 1]].endswith(",") else 0)
                if length(st[start:m]) <= MAX_CHARS and cost < best_cost:
                    best, best_cost = m, cost
            cuts.append(best); start = best
        bounds = [0] + cuts + [len(st)]
        out += [st[bounds[i]:bounds[i + 1]] for i in range(len(bounds) - 1)]
    return out


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    tl_path = os.path.join(ROOT, "data/timeline_play.json")
    lines_path = os.path.join(ROOT, "data/lines_play.json")
    if not os.path.exists(tl_path):
        tl_path, lines_path = os.path.join(ROOT, "data/timeline.json"), os.path.join(ROOT, "data/lines.json")
    tl = json.load(open(tl_path))
    lines = json.load(open(lines_path))
    ov_path = os.path.join(ROOT, "data/subtitle_overrides.json")
    ov = json.load(open(ov_path)) if os.path.exists(ov_path) else {}
    cuts_path = os.path.join(ROOT, "data/cuts_play.json")
    cuts = json.load(open(cuts_path))["cuts"] if os.path.exists(cuts_path) else []

    caps = []
    for bid in tl["order"]:
        b = tl["beats"][bid]
        if b["kind"] != "line":
            continue
        L = lines[bid]
        toks, times = token_times(b["text"], L["words"], b["start"], b["end"] - b["start"])
        segs = voiced_segments(os.path.join(ROOT, L["file"]), b["start"])
        chunks = chunk_tokens(toks, set(ov.get("split_after", {}).get(bid, [])))
        # automatic split at a long pause after a sentence end inside a chunk
        refined = []
        for ix in chunks:
            cur = [ix[0]]
            for p, q in zip(ix, ix[1:]):
                gap = [g for g in gaps_between(segs, times[p][1] - 0.4, times[q][0] + 0.8) if g[1] - g[0] >= SPLIT_GAP]
                if re.search(r"[.?!]$", toks[p]) and gap:
                    refined.append(cur); cur = []
                cur.append(q)
            refined.append(cur)
        chunks = refined
        # boundaries from real pauses
        starts, ends = [], []
        first_on = segs[0][0] if segs else times[chunks[0][0]][0]
        last_off = segs[-1][1] if segs else times[chunks[-1][-1]][1]
        for ci, ix in enumerate(chunks):
            if ci == 0:
                starts.append(max(b["start"], first_on - LEAD))
            if ci == len(chunks) - 1:
                ends.append(last_off + TAIL)
            else:
                p, q = ix[-1], chunks[ci + 1][0]
                gs = gaps_between(segs, times[p][1] - 0.5, times[q][0] + 0.8)
                if gs:
                    g0, g1 = max(gs, key=lambda g: g[1] - g[0])
                    ends.append(min(g0 + TAIL, g1 - 0.04))
                    starts.append(g1 - LEAD)
                else:
                    ends.append(times[p][1] + 0.1)
                    starts.append(times[q][0] - LEAD)
        for ci, ix in enumerate(chunks):
            caps.append({"beat": bid, "idx": ci, "scene": b["scene"], "speaker": b["speaker"], "inner": bool(b.get("inner")),
                         "text": " ".join(toks[i] for i in ix), "start": starts[ci], "end": ends[ci], "voice_end": ends[ci] - TAIL})

    # snap to shot cuts, reading speed, flicker, overlaps
    for i, c in enumerate(caps):
        nxt = caps[i + 1]["start"] if i + 1 < len(caps) else c["end"] + 5
        # a cut just after the caption starts: start on the cut (no flash of the caption over the old shot)
        near = [x for x in cuts if c["start"] < x <= c["start"] + 0.3]
        if near:
            c["start"] = near[0]
        # reading speed: hold longer when there is room (stop at the next cut if it is close)
        need = len(c["text"]) / CPS
        if c["end"] - c["start"] < max(MIN_DUR, need):
            target = c["start"] + max(MIN_DUR, need)
            target = min(target, c["end"] + 1.0, nxt - 0.1)
            later = [x for x in cuts if c["end"] < x < target]
            if later and later[0] - c["end"] >= 0.2:
                target = later[0]
            c["end"] = max(c["end"], target)
        # a cut just before the caption ends, after the voice has finished: end on the cut
        near_end = [x for x in cuts if c["end"] - 0.35 <= x < c["end"] and x >= c["voice_end"] + 0.05]
        if near_end:
            c["end"] = near_end[-1]
        # bridge short gaps to the next caption (no blink between them)
        if 0 < nxt - c["end"] < 0.35:
            c["end"] = nxt
        c["end"] = min(c["end"], nxt)
        key = f"{c['beat']}:{c['idx']}"
        if key in ov.get("end_max", {}):
            c["end"] = min(c["end"], ov["end_max"][key])
        if key in ov.get("pos", {}):
            c["pos_override"] = ov["pos"][key]
        c["start"], c["end"] = round(max(0.0, c["start"]), 3), round(c["end"], 3)
        c.pop("voice_end", None)
    # the film's last line: hold it into the silence that follows
    if caps:
        last = caps[-1]
        last["end"] = round(max(last["end"], min(last["end"] + 1.2, tl["duration"] - 2.0)), 3)

    json.dump({"captions": caps}, open(os.path.join(ROOT, "data/subtitles.json"), "w"), indent=1)
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    with open(os.path.join(ROOT, "out/subtitles.srt"), "w") as f:
        for i, c in enumerate(caps, 1):
            f.write(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}\n\n")
    fast = [c for c in caps if len(c["text"]) / max(0.01, c["end"] - c["start"]) > CPS + 0.5]
    print(f"{len(caps)} captions; {len(fast)} still faster than {CPS:.0f} cps (no room to extend)")


if __name__ == "__main__":
    main()
