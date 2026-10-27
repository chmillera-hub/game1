"""Lay the voice lines out on one absolute timeline."""
import json
import os

import paths
from script import ACCENTS, DEFAULT_GAP, GAP_BEFORE, LINES, TAIL

LEAD_IN = 0.0  # frame 0 is already the opening shot (no fade from black)


def build():
    meta = json.load(open(os.path.join(paths.VOICE, "lines.json")))
    t = LEAD_IN
    lines = []
    for lid, speaker, chunks, spd, gain in LINES:
        t += GAP_BEFORE.get(lid, DEFAULT_GAP)
        m = meta[lid]
        words = [dict(w, start=w["start"] + t, end=w["end"] + t) for w in m["words"]]
        lines.append(dict(id=lid, speaker=speaker, start=t, end=t + m["dur"], text=m["text"],
                          words=words, chunks=[[a + t, b + t] for a, b in m["chunks"]]))
        t += m["dur"]
    total = t + TAIL
    accents = []
    by_id = {ln["id"]: ln for ln in lines}
    for lid, word, kind in ACCENTS:
        ln = by_id[lid]
        hit = [w for w in ln["words"] if w["text"].strip(".,!?").lower() == word.lower()]
        if not hit:
            raise ValueError(f"accent word {word!r} not found in {lid}: {[w['text'] for w in ln['words']]}")
        w = hit[0] if kind != "hi" or len(hit) == 1 else hit[-1]
        accents.append(dict(line=lid, word=word, kind=kind, t=w["start"], end=w["end"]))
    tl = dict(total=total, lines=lines, accents=accents)
    json.dump(tl, open(os.path.join(paths.BUILD, "timeline.json"), "w"), indent=1)
    return tl


def load():
    return json.load(open(os.path.join(paths.BUILD, "timeline.json")))


if __name__ == "__main__":
    tl = build()
    print("total %.1f s (%d:%04.1f)" % (tl["total"], tl["total"] // 60, tl["total"] % 60))
    for ln in tl["lines"]:
        print(f"{ln['id']} {ln['start']:7.2f}-{ln['end']:7.2f} {ln['speaker']:8s} {ln['text'][:70]}")
