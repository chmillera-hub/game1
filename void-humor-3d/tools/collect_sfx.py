#!/usr/bin/env python3
"""Collect every sound-effect event of the film -> data/sfx_events.json (what audio/mix.py plays).

    python3 tools/collect_sfx.py [--timeline data/timeline.json] [--out data/sfx_events.json] [-v]

Sources, in order:
 (a) each beat's `sfx` list in the timeline (copied from the screenplay), placed automatically:
     * footsteps_* loop through the beat (consecutive beats with the same footsteps join into one walk),
       starting at a matching verb if the line has one ("storms off" -> the stomps start on "storms");
     * wind_soft becomes a soft bed over the beat (fades in before, out after);
     * one-shots land on a matching word of the line when there is one (kick_thump on "kicks", block_thunk on
       "blocks", pat_pat on "pats", dagger_shing on "dagger"...; Whisper word times when TTS exists, else an
       estimate), otherwise near the beat start, several one-shots of a beat staggered;
     * bleep is dropped when the line audio already carries tts.py's bleep.
 (b) precise cues written by the scene animators, which OVERRIDE (a): every entry of
     data/cues/<sceneId>.json  {"sfx": [{"t": "s13b08+0.42" | 123.4, "name": "kick_thump", "gain_db": 0, "pan": 0.2}],
                                "hits": [...music hits, read by audio/music.py...]}
     and of the older data/sfx_cues.json (a list of the same sfx entries, or {"sfx": [...]}).
     A cue removes the beat-level entries of the SAME name in the SAME beat (the beat named by its ref, or the
     beat containing its time). Optional cue fields: "until" (ref/seconds: loops loopable sounds until then,
     cuts others with a fade), "fade" (s, default 0.15), "variant" (1..n), "rate" (varispeed, default 1).

Times: `t` = the moment the sound LANDS (the impact / first footfall) — the mixer subtracts each file's sync
point (audio/sfx/meta.json). Refs: 's13b08', 's13b08+0.42', 's05b02.end-0.3', 's08.start+1', 's08.end', 'film.end'.
gain_db 0 = the file's designed level (sensible against dialogue); pan -1..+1.

Output events: {t, name, file, sync, gain_db, pan, beat, src[, until, fade, rate]} sorted by t.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "audio"))
from audiolib import TimeRefs  # noqa: E402

FOOT = ("footsteps_soft", "footsteps_run", "footsteps_stomp")
BEDS = ("wind_soft",)
ALIAS = {"star_cough": "star_pop", "footsteps": "footsteps_soft", "sparkle": "sparkle_appear", "thud": "thud_sit",
         "ding": "notification_ding", "crash": "crash_buckets", "birdies": "cartoon_birdies", "kick": "kick_thump"}
# word prefixes that anchor a one-shot to the spoken word (first match in the line)
KEYWORDS = {
    "kick_thump": ["kick"], "block_thunk": ["block"], "phone_tap": ["block", "phone", "tap"], "pat_pat": ["pat"],
    "crash_buckets": ["bucket", "knock", "crash", "into"], "mop_clatter": ["supplies", "cleaning", "mop"],
    "bucket_bonk": ["bucket", "cartoon"], "cartoon_birdies": ["cartoon", "birdie"],
    "whoosh_fly": ["flying", "fly", "flies", "flew"], "dagger_shing": ["dagger"], "dust_sparkle": ["dust"],
    "lock_click": ["opened", "open", "unlock"], "cage_creak": ["opened", "open", "cage"],
    "star_pop": ["star", "cough"], "galaxy_whirl": ["galax"], "nebula_swell": ["nebula"],
    "thud_sit": ["ass", "sit", "fall", "fell", "plop"], "sparkle_appear": ["now", "appear"],
    "twinkle": ["smile", "giggl", "twinkl", "star"], "shimmer": ["shimmer", "appear", "bonus"],
    "cloth_rustle": ["arm", "hand", "shoulder", "cross", "lean", "gets", "puts", "pulls"],
    "whoosh": ["turn", "huff", "roll", "spin", "whip"], "gulp": ["gulp", "swallow"],
    "rumble_low": ["void", "rumbl", "deep"], "notification_ding": ["block", "notif"],
}
FOOT_KEYWORDS = {"footsteps_stomp": ["storm", "stomp", "march"], "footsteps_run": ["run", "flee", "dash"],
                 "footsteps_soft": ["walk", "step", "stroll"]}
KEY_OFFSET = {"phone_tap": -0.35, "cage_creak": 0.25, "block_thunk": 0.05, "kick_thump": 0.08, "pat_pat": 0.05,
              "notification_ding": 0.6, "mop_clatter": 0.35, "bucket_bonk": 0.1, "cartoon_birdies": 0.3,
              "whoosh_fly": 0.0, "crash_buckets": 0.05}
DEFAULT_OFFSET = {"sparkle_appear": 0.25, "notification_ding": 0.35, "rumble_low": -0.6, "nebula_swell": -0.3,
                  "galaxy_whirl": -0.1, "shimmer": -0.15}
PAN_CYCLE = {"star_pop": [-0.3, 0.3, -0.1, 0.2], "twinkle": [0.15, -0.15, 0.25], "cartoon_birdies": [0.0]}
STAGGER = 0.4


def rp(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def load_json(p, default):
    p = rp(p)
    return json.load(open(p)) if os.path.exists(p) else default


def load_meta():
    meta = load_json("audio/sfx/meta.json", {})
    if not meta:
        print("[collect_sfx] audio/sfx/meta.json missing: run python3 audio/sfx.py (using default durations)", file=sys.stderr)
    return meta


def load_cue_files(verbose=False):
    """All precise cue files: data/cues/*.json + data/sfx_cues.json (+ data/music_hits.json for hits).
    Returns (sfx_entries, hit_entries); each entry gets '_src'."""
    sfx, hits = [], []
    cdir = os.environ.get("CUES_DIR") or os.path.join(ROOT, "data", "cues")
    for p in sorted(glob.glob(os.path.join(cdir, "*.json"))):
        try:
            d = json.load(open(p))
        except Exception as e:  # a half-written file from a parallel writer: skip, say so
            print(f"[cues] skipping unreadable {p}: {e}", file=sys.stderr)
            continue
        src = os.path.relpath(p, ROOT) if p.startswith(ROOT) else p
        if isinstance(d, list):
            d = {"sfx": d}
        sfx += [dict(e, _src=src) for e in d.get("sfx", []) or []]
        hits += [dict(h, _src=src) for h in d.get("hits", []) or []]
    d = load_json("data/sfx_cues.json", [])
    if isinstance(d, dict):
        hits += [dict(h, _src="data/sfx_cues.json") for h in d.get("hits", []) or []]
        d = d.get("sfx", [])
    sfx += [dict(e, _src="data/sfx_cues.json") for e in d or []]
    d = load_json("data/music_hits.json", [])
    if isinstance(d, dict):
        d = d.get("hits", [])
    hits += [dict(h, _src="data/music_hits.json") for h in d or []]
    if verbose:
        print(f"[cues] {len(sfx)} sfx cue(s), {len(hits)} music hit(s) from cue files", file=sys.stderr)
    return sfx, hits


def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))


def word_times(bid, b, lines):
    """[(word, abs_start)] for a line beat: Whisper times if the beat's audio exists, else an estimate."""
    toks = (b.get("text") or "").split()
    if not toks:
        return []
    L = lines.get(bid)
    if L and b.get("audio") and L.get("words"):
        import difflib
        want = [norm(t) for t in toks]
        got = [norm(w["w"]) for w in L["words"]]
        out = {}
        for a, c, n in difflib.SequenceMatcher(None, want, got, autojunk=False).get_matching_blocks():
            for k in range(n):
                out[a + k] = b["start"] + L["words"][c + k]["start"]
        res = []
        for i, t in enumerate(toks):
            if i in out:
                res.append((norm(t), out[i]))
            else:
                res.append((norm(t), b["start"] + (b["end"] - b["start"]) * i / len(toks)))
        return res
    dur = max(0.2, b["end"] - b["start"] - 0.3)
    total = sum(len(t) + 1 for t in toks)
    acc, res = 0, []
    for t in toks:
        res.append((norm(t), b["start"] + dur * acc / total))
        acc += len(t) + 1
    return res


def find_word(words, prefixes, after=None):
    for w, t in words:
        if after is not None and t < after - 1e-6:
            continue
        for p in prefixes:
            if w.startswith(p):
                return t
    return None


class Variants:
    def __init__(self, meta):
        self.meta, self.count = meta, {}

    def file(self, name, variant=None):
        files = self.meta.get(name, {}).get("files") or [f"{name}.wav"]
        if variant is None:
            i = self.count.get(name, 0)
            self.count[name] = i + 1
        else:
            i = int(variant) - 1
        return "audio/sfx/" + files[i % len(files)]


def beat_events(tl, lines, meta, verbose=False):
    beats, order = tl["beats"], tl["order"]
    R = TimeRefs(tl)
    V = Variants(meta)
    ev = []
    pan_i = {}

    def info(n):
        m = meta.get(n, {})
        return m.get("dur", 1.0), m.get("sync", 0.0)

    # --- footsteps & beds: merge consecutive beats carrying the same name
    runs = {}
    for bid in order:
        b = beats[bid]
        for n0 in b.get("sfx", []) or []:
            n = ALIAS.get(n0, n0)
            if n in FOOT or n in BEDS:
                lst = runs.setdefault(n, [])
                if lst and b["start"] - lst[-1][2] < 0.8 and b["scene"] == beats[lst[-1][0]]["scene"]:
                    lst[-1][2] = max(lst[-1][2], b["end"])
                else:
                    lst.append([bid, b["start"], b["end"]])
    for n, lst in runs.items():
        dur, sync = info(n)
        for bid, s, e in lst:
            b = beats[bid]
            if n in FOOT:
                t0 = s + 0.05
                if b["kind"] == "line":
                    kw = find_word(word_times(bid, b, lines), FOOT_KEYWORDS.get(n, []))
                    if kw is not None and kw < e - 0.3:
                        t0 = kw + 0.05
                end = e + 0.15
                t = t0
                while t < end - 0.05:
                    f = V.file(n)
                    rec = {"t": round(t, 3), "name": n, "file": f, "sync": sync, "gain_db": 0.0, "pan": 0.0,
                           "beat": R.beat_at(t) or bid, "src": "beat"}
                    if t + dur - sync > end:
                        rec.update(until=round(end, 3), fade=0.12)
                    ev.append(rec)
                    t += dur
            else:  # bed
                ev.append({"t": round(s - 0.8, 3), "name": n, "file": V.file(n, 1), "sync": 0.0, "gain_db": 0.0, "pan": 0.0,
                           "beat": bid, "src": "beat", "until": round(e + 1.5, 3), "fade": 1.2, "fade_in": 0.8, "loop": True})
    # --- one-shots
    for bid in order:
        b = beats[bid]
        names = [ALIAS.get(n, n) for n in b.get("sfx", []) or []]
        shots = [n for n in names if n not in FOOT and n not in BEDS]
        if not shots:
            continue
        words = word_times(bid, b, lines) if b["kind"] == "line" else []
        k = 0
        for n in shots:
            if n not in meta and meta:
                print(f"[collect_sfx] {bid}: unknown sfx '{n}' — skipped", file=sys.stderr)
                continue
            if n == "bleep":
                L = lines.get(bid, {})
                if b.get("audio") and L.get("bleep"):
                    continue  # tts.py already put the bleep into the line audio
                toks = (b.get("text") or "").split()
                i = next((i for i, x in enumerate(toks) if "f***" in x), None)
                t = words[i][1] if (i is not None and i < len(words)) else b["start"] + 0.1
            else:
                t = find_word(words, KEYWORDS.get(n, [])) if words else None
                if t is not None:
                    t += KEY_OFFSET.get(n, 0.0)
                else:
                    t = b["start"] + 0.12 + DEFAULT_OFFSET.get(n, 0.0) + STAGGER * k
                    k += 1
                    t = min(t, max(b["start"] + 0.05, b["end"] - 0.1)) if b["end"] - b["start"] > 0.3 else t
            pc = PAN_CYCLE.get(n)
            pan = 0.0
            if pc:
                pan = pc[pan_i.get(n, 0) % len(pc)]
                pan_i[n] = pan_i.get(n, 0) + 1
            dur, sync = info(n)
            ev.append({"t": round(t, 3), "name": n, "file": V.file(n), "sync": sync, "gain_db": 0.0, "pan": pan,
                       "beat": bid, "src": "beat"})
    return ev, V


def cue_events(tl, meta, V, entries):
    R = TimeRefs(tl)
    out, overrides = [], set()
    for e in entries:
        try:
            n = ALIAS.get(e["name"], e["name"])
            t, bid, sid = R.parse(e["t"] if "t" in e else e["at"])
        except KeyError as err:
            print(f"[collect_sfx] {e.get('_src')}: {err} — cue skipped", file=sys.stderr)
            continue
        if meta and n not in meta:
            print(f"[collect_sfx] {e.get('_src')}: unknown sfx '{n}' — cue skipped", file=sys.stderr)
            continue
        bid = bid or R.beat_at(t)
        m = meta.get(n, {})
        rec = {"t": round(t, 3), "name": n, "file": V.file(n, e.get("variant")), "sync": m.get("sync", 0.0),
               "gain_db": float(e.get("gain_db", e.get("gain", 0.0)) or 0.0), "pan": float(e.get("pan", 0.0) or 0.0),
               "beat": bid, "src": e.get("_src", "cue")}
        if e.get("until") is not None:
            try:
                rec["until"] = round(R(e["until"]), 3)
                rec["fade"] = float(e.get("fade", 0.15))
                if m.get("loop") or e.get("loop"):
                    rec["loop"] = True
            except KeyError as err:
                print(f"[collect_sfx] {e.get('_src')}: {err} (until ignored)", file=sys.stderr)
        if e.get("rate"):
            rec["rate"] = float(e["rate"])
        out.append(rec)
        overrides.add((bid, n))
    return out, overrides


def collect(timeline="data/timeline.json", verbose=False):
    tl = timeline if isinstance(timeline, dict) else json.load(open(rp(timeline)))
    lines = {} if tl.get("estimated") else load_json(os.environ.get("LINES_JSON", "data/lines.json"), {})
    meta = load_meta()
    ev, V = beat_events(tl, lines, meta, verbose)
    sfx_cues, _ = load_cue_files(verbose)
    cev, overrides = cue_events(tl, meta, V, sfx_cues)
    kept = []
    for e in ev:
        if (e["beat"], e["name"]) in overrides:
            continue
        kept.append(e)
    dropped = len(ev) - len(kept)
    allev = sorted(kept + cev, key=lambda e: (e["t"], e["name"]))
    if verbose:
        print(f"[collect_sfx] {len(kept)} beat-level events ({dropped} overridden), {len(cev)} cue events", file=sys.stderr)
    return allev


def main():
    a = sys.argv[1:]
    tlp = a[a.index("--timeline") + 1] if "--timeline" in a else "data/timeline.json"
    out = a[a.index("--out") + 1] if "--out" in a else "data/sfx_events.json"
    ev = collect(tlp, verbose=True)
    json.dump(ev, open(rp(out), "w"), indent=1)
    if "-v" in a:
        for e in ev:
            extra = f" until {e['until']:.2f}" if e.get("until") is not None else ""
            print(f"  {e['t']:8.2f}  {e['beat'] or '-':8s} {e['name']:18s} {os.path.basename(e['file']):22s} "
                  f"{e['gain_db']:+5.1f} dB pan {e['pan']:+.2f}{extra}  [{e['src']}]")
    print(f"sfx events: {len(ev)} -> {out}")


if __name__ == "__main__":
    main()
