"""Resolve time anchors ("start of line L04", "the word 'squeeze' in L09")."""
import timeline

_TL = None


def tl():
    global _TL
    if _TL is None:
        _TL = timeline.load()
        _TL["by_id"] = {ln["id"]: ln for ln in _TL["lines"]}
    return _TL


def line(lid):
    return tl()["by_id"][lid]


def L(lid, which="start", off=0.0):
    """Anchor to a line start/end."""
    return ("L", lid, which, off)


def Wd(lid, word, which="start", off=0.0, nth=0):
    """Anchor to the nth occurrence of a word in a line."""
    return ("W", lid, word, which, off, nth)


def At(t):
    return ("T", t)


def resolve(a):
    if isinstance(a, (int, float)):
        return float(a)
    kind = a[0]
    if kind == "T":
        return float(a[1])
    if kind == "L":
        _, lid, which, off = a
        ln = line(lid)
        return ln[which] + off
    if kind == "W":
        _, lid, word, which, off, nth = a
        ln = line(lid)
        hits = [w for w in ln["words"] if w["text"].strip(".,!?;:'\"").lower() == word.lower()]
        if len(hits) <= nth:
            raise KeyError(f"word {word!r} #{nth} not in {lid}: {[w['text'] for w in ln['words']]}")
        return hits[nth][which] + off
    raise ValueError(a)


def total():
    return tl()["total"]
