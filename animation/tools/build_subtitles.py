"""Build phrase-sized captions for every spoken line, timed from word timestamps (play time).

    python3 tools/build_subtitles.py      -> data/subtitles.json, out/subtitles.srt

Caption text is the screenplay text (not the speech recogniser's), split at sentence ends and, for long
sentences, at commas, so each caption is at most ~2 short lines. Placement on screen is decided later by
`node src/render.mjs --place-subs`, which renders each caption's frames and avoids covering faces.
"""
import difflib, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_CHARS = 62        # ~2 lines at 32 px Inter in a 520 px box
MIN_DUR = 1.0
LEAD, TAIL = 0.08, 0.3


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
    # fill gaps by interpolating between known neighbours (or proportionally across the line)
    n = len(toks)
    for i in range(n):
        if times[i] is None:
            prev = next((j for j in range(i - 1, -1, -1) if times[j]), None)
            nxt = next((j for j in range(i + 1, n) if times[j]), None)
            t0 = times[prev][1] if prev is not None else line_start
            t1 = times[nxt][0] if nxt is not None else line_start + line_dur
            span = (nxt if nxt is not None else n) - (prev if prev is not None else -1)
            k = i - (prev if prev is not None else -1)
            a = t0 + (t1 - t0) * (k - 1) / span
            times[i] = (a, t0 + (t1 - t0) * k / span)
    return toks, times


def chunk_tokens(toks):
    """split token list into caption chunks (lists of indices): one sentence per caption, short sentences
    merged ("Huge. Unmoving."), long ones split at the comma (else the word gap) nearest the balance point"""
    def length(ix):
        return len(" ".join(toks[i] for i in ix))
    sents, cur = [], []
    for i, t in enumerate(toks):
        cur.append(i)
        if re.search(r"[.?!]$", t):
            sents.append(cur); cur = []
    if cur:
        sents.append(cur)
    merged = []
    for st in sents:
        if merged and (length(merged[-1]) < 16 or length(st) < 10) and length(merged[-1] + st) <= MAX_CHARS:
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
    old = {}
    p_old = os.path.join(ROOT, "data/subtitles.json")
    if os.path.exists(p_old):  # keep manual placement overrides across rebuilds
        for c in json.load(open(p_old)).get("captions", []):
            if c.get("pos_override"):
                old[(c["beat"], c["idx"])] = c["pos_override"]
    caps = []
    for bid in tl["order"]:
        b = tl["beats"][bid]
        if b["kind"] != "line":
            continue
        L = lines[bid]
        toks, times = token_times(b["text"], L["words"], b["start"], b["end"] - b["start"])
        for ci, ix in enumerate(chunk_tokens(toks)):
            caps.append({
                "beat": bid, "idx": ci, "scene": b["scene"], "speaker": b["speaker"], "inner": bool(b.get("inner")),
                "text": " ".join(toks[i] for i in ix),
                "start": round(times[ix[0]][0] - LEAD, 3), "end": round(times[ix[-1]][1] + TAIL, 3),
                "line_end": b["end"],
            })
    # timing polish: minimum duration, no flicker gaps, no overlaps
    for i, c in enumerate(caps):
        nxt = caps[i + 1]["start"] if i + 1 < len(caps) else c["end"] + 5
        if c["end"] - c["start"] < MIN_DUR:
            c["end"] = min(c["start"] + MIN_DUR, nxt - 0.04)
        if 0 < nxt - c["end"] < 0.35:
            c["end"] = nxt - 0.04
        c["end"] = round(min(c["end"], nxt - 0.04), 3)
        c["start"] = round(max(0.0, c["start"]), 3)
        if (c["beat"], c["idx"]) in old:
            c["pos_override"] = old[(c["beat"], c["idx"])]
    json.dump({"captions": caps}, open(os.path.join(ROOT, "data/subtitles.json"), "w"), indent=1)
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    with open(os.path.join(ROOT, "out/subtitles.srt"), "w") as f:
        for i, c in enumerate(caps, 1):
            f.write(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}\n\n")
    print(f"{len(caps)} captions from {sum(1 for b in tl['beats'].values() if b['kind'] == 'line')} lines")


if __name__ == "__main__":
    main()
