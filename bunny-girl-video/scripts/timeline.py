"""Scene boundaries and story moments, derived from build/timeline.json.

Audio and video both read this so effects land on the same frames.
"""
import json
import os

BUILD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build")
TAIL = 0.55  # let the final chord ring after the narration's last pause


def _word_times(scene, match):
    out = []
    for p in scene["pages"]:
        for w in p["words"]:
            if match(w["w"]):
                out.append(w["start"])
    return out


def load():
    with open(os.path.join(BUILD, "timeline.json")) as f:
        tl = json.load(f)
    scenes = tl["scenes"]
    by_id = {s["id"]: s for s in scenes}

    # scene i runs from its start to the next scene's start
    starts = [0.0]
    for prev, nxt in zip(scenes, scenes[1:]):
        if nxt["id"] == "poof":  # cut to POOF exactly on the word, behind a flash
            starts.append(nxt["pages"][0]["start"] - 0.08)
        else:
            starts.append((prev["pages"][-1]["end"] + nxt["pages"][0]["start"]) / 2)
    duration = round(tl["duration"] + TAIL, 3)
    for s, t0, t1 in zip(scenes, starts, starts[1:] + [duration]):
        s["t0"], s["t1"] = round(t0, 3), round(t1, 3)

    low = lambda w: w.lower().strip(".,!?“”")  # noqa: E731
    hug = by_id["hug"]
    poof_t = by_id["poof"]["t0"]
    ev = dict(
        hops=_word_times(by_id["bunny"], lambda w: low(w) == "hop"),
        bunny_name=_word_times(by_id["bunny"], lambda w: low(w) == "name")[:1],
        dog_names=_word_times(by_id["park"], lambda w: low(w) in ("cosmo", "pettie", "luna", "mooky", "buddy")),
        invisible=_word_times(by_id["invisible"], lambda w: low(w) == "invisible"),
        peekaboo=_word_times(by_id["invisible"], lambda w: low(w) == "peek-a-boo")[0],
        hugs=_word_times(hug, lambda w: low(w) == "hug"),
        love=_word_times(hug, lambda w: low(w) == "love"),
        suddenly=_word_times(hug, lambda w: low(w) == "suddenly")[0],
        music_stop=hug["pages"][-1]["start"] + 0.35,
        drumroll=(hug["pages"][-1]["end"] - 0.05, poof_t),
        poof=poof_t,
        jumps=_word_times(by_id["poof"], lambda w: low(w) in ("ran", "jumped", "played")),
        family=by_id["family"]["t0"],
        the_end=_word_times(by_id["end"], lambda w: low(w) == "end")[0],
        final_chord=by_id["end"]["pages"][-1]["end"] + 0.12,
        transitions=[s["t0"] for s in scenes[1:] if s["id"] != "poof"],
    )
    # extra moments acted out in the cartoon version
    first = lambda sid, word: _word_times(by_id[sid], lambda w: low(w) == word)[0]  # noqa: E731
    spot, laugh, shy = first("invisible", "spot"), first("invisible", "laugh"), first("invisible", "shy")
    ev.update(
        idea=first("hug", "idea"),
        tiptoe=(spot - 0.75, spot - 0.05),
        catches=[laugh - 0.35 + 0.62 * i + 0.55 for i in range(4) if laugh - 0.35 + 0.62 * i < shy - 0.4],
        rain_on=first("family", "in"),
        snow_on=first("family", "weather"),
        photo=first("family", "family") - 0.1,
        wolf_dash=2.30,
    )
    return dict(scenes=scenes, duration_video=duration, events=ev)


def scene_at(tl):
    scenes = tl["scenes"]

    def f(t):
        for s in scenes:
            if s["t0"] <= t < s["t1"]:
                return s["id"]
        return scenes[-1]["id"]
    return f


if __name__ == "__main__":
    tl = load()
    for s in tl["scenes"]:
        print(f"{s['id']:10s} {s['t0']:7.2f} -> {s['t1']:7.2f}")
    print(json.dumps(tl["events"], indent=1))
    print("video length", tl["duration_video"])
