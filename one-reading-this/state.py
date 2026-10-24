"""Pre-pass: turn the screenplay + timeline into one plain dict of numbers per
frame (camera, faces, hands, props, cards, subtitles). Smoothing needs history,
so it happens here once; the renderer can then draw frames in parallel."""
import json, math, pickle
import numpy as np
from script import BEATS
from timeline import sub_chunks, word_time

FPS = 24
DT = 1 / FPS

EMO = {
    "neutral": dict(),
    "tired": dict(brow=-0.1, btilt=0.25, lid=0.45, smile=-0.15, tilt=-0.05),
    "sad": dict(brow=0.05, btilt=0.75, lid=0.35, lidb=0.1, smile=-0.45, tilt=-0.07, wet=0.6),
    "hurt": dict(brow=0.15, btilt=0.95, lid=0.4, lidb=0.15, smile=-0.6, tilt=-0.04, wet=0.9),
    "worried": dict(brow=0.35, btilt=0.6, lid=0.02, lidb=0.0, smile=-0.3, tilt=0.03),
    "warm": dict(brow=0.1, btilt=0.1, lid=0.18, lidb=0.25, smile=0.45, tilt=0.05, blush=0.2),
    "smile": dict(brow=0.2, lid=0.15, lidb=0.35, smile=0.8, mw=1.1, tilt=0.04, blush=0.35),
    "smirk": dict(brow=0.3, basym=0.35, lid=0.25, lidb=0.2, smile=0.55, tilt=0.08),
    "laugh": dict(brow=0.35, lid=0.45, lidb=0.5, smile=1.0, mw=1.15, jawbase=0.35, tilt=0.1, blush=0.5, shake=1.0),
    "laughcry": dict(brow=0.3, btilt=0.6, lid=0.4, lidb=0.45, smile=0.75, jawbase=0.2, tilt=0.06, wet=1.0, blush=0.5, shake=0.6),
    "shy": dict(brow=0.1, btilt=0.3, lid=0.38, lidb=0.3, smile=0.4, tilt=0.1, blush=0.6, gaze=(0.25, 0.65)),
    "earnest": dict(brow=0.3, btilt=0.35, lid=0.05, lidb=0.05, smile=0.1, lean=1.0),
    "tender": dict(brow=0.15, btilt=0.4, lid=0.28, lidb=0.3, smile=0.4, tilt=0.06, wet=0.3),
    "thinking": dict(brow=0.15, btilt=-0.35, basym=0.4, lid=0.3, smile=-0.05, gaze=(-0.5, -0.6)),
    "realize": dict(brow=0.7, btilt=0.1, lid=-0.05, smile=0.3, jawbase=0.1, pupil=1.0),
    "surprised": dict(brow=1.0, btilt=0.15, lid=-0.12, lidb=0.0, smile=0.0, jawbase=0.3, pupil=1.0),
    "listen": dict(brow=0.15, btilt=0.15, lid=0.15, lidb=0.1, smile=0.2, tilt=0.06, lean=0.6),
    "curious": dict(brow=0.45, basym=0.3, lid=0.1, smile=0.15, tilt=0.1),
    "serious": dict(brow=-0.1, btilt=-0.25, lid=0.22, lidb=0.05, smile=-0.1),
    "sadsmile": dict(brow=0.1, btilt=0.7, lid=0.35, lidb=0.25, smile=0.3, tilt=-0.04, wet=0.4),
    "determined": dict(brow=0.0, btilt=-0.35, lid=0.18, lidb=0.1, smile=0.25),
    "uneasy": dict(brow=0.3, btilt=0.5, lid=0.2, smile=-0.15, mw=0.9, gaze=(-0.5, 0.3)),
    "joy": dict(brow=0.5, btilt=0.1, lid=0.1, lidb=0.4, smile=1.0, jawbase=0.15, blush=0.5, pupil=0.6),
    "proud": dict(brow=0.25, btilt=0.3, lid=0.3, lidb=0.4, smile=0.7, tilt=0.08, wet=0.3, blush=0.2),
}
BASE = dict(brow=0.0, btilt=0.0, basym=0.0, lid=0.12, lidb=0.05, smile=0.1, mw=1.0, tilt=0.0,
            blush=0.0, wet=0.0, jawbase=0.0, pupil=0.0, lean=0.0, shake=0.0)
TAU = dict(lid=0.12, lidb=0.15, jawbase=0.12)

CH = {
    "M": dict(hx=205.0, hy=640.0, R=80.0, dir=1, turn=0.32, gaze=(0.65, -0.05)),
    "A": dict(hx=520.0, hy=615.0, R=84.0, dir=-1, turn=-0.32, gaze=(-0.65, -0.05)),
}
TABLE_Y = 905.0
MUG_SPOT = {"M": (300.0, 902.0), "A": (606.0, 900.0)}
BOOK = (160.0, 918.0)
CANDLE0, CANDLE1 = (455.0, 890.0), (372.0, 893.0)


def split(v, default=None):
    """'a|b@0.6|c@0.8' -> [(0, a), (0.6, b), (0.8, c)]"""
    if v is None:
        return [(0.0, default)]
    if not isinstance(v, str):
        return [(0.0, v)]
    out = []
    for k, part in enumerate(v.split("|")):
        if "@" in part:
            name, f = part.split("@"); out.append((float(f), name))
        else:
            out.append((0.0, part))
    return out


def pick(spec, frac):
    cur = spec[0][1]
    for f, v in spec:
        if frac >= f:
            cur = v
    return cur


def pose_targets(c, pose, t, frac, st):
    """Hand world positions + hand shapes for a pose."""
    hx, hy, R, d = c["hx"], c["hy"], c["R"], c["dir"]
    near, far = ("R", "L") if d == 1 else ("L", "R")
    tab = {near: (hx + d * 0.8 * R, TABLE_Y + 8), far: (hx - d * 0.75 * R, TABLE_Y + 12)}
    shapes = {near: "rest", far: "rest"}
    if pose == "book":
        tab = {"L": (BOOK[0] - 55, BOOK[1] + 8), "R": (BOOK[0] + 60, BOOK[1] + 4)}
    elif pose in ("mug", "slide_mug"):
        tab["R"] = (MUG_SPOT[c["name"]][0] - 6, MUG_SPOT[c["name"]][1] - 6)
        shapes["R"] = "fist"
    elif pose == "sip":
        tab["R"] = (hx + 0.42 * R, hy + 0.95 * R)
        shapes["R"] = "fist"
    elif pose == "heart":
        tab[near] = (hx + d * 0.1 * R, hy + 2.0 * R)
    elif pose == "gesture":
        tab[near] = (hx + d * 0.95 * R, hy + 1.4 * R + 6 * math.sin(t * 3.1))
        shapes[near] = "open"
    elif pose == "open":
        tab[near] = (hx + d * 1.0 * R, TABLE_Y - 25)
        tab[far] = (hx + d * 0.2 * R, TABLE_Y - 18)
        shapes = {near: "open", far: "open"}
    elif pose == "chin":
        tab[near] = (hx + d * 0.12 * R, hy + 1.12 * R)
        shapes[near] = "fist"
    elif pose == "rub":
        tab[far] = (hx - d * 0.25 * R + 4 * math.sin(t * 9), hy + 0.12 * R + 3 * math.cos(t * 9))
        shapes[far] = "fist"
    elif pose == "fist":
        shapes = {near: "fist", far: "fist"}
        tab[near] = (hx + d * 0.7 * R, TABLE_Y + 4)
    elif pose == "point":
        tab[near] = (hx + d * 1.45 * R, hy + 1.45 * R + 4 * math.sin(t * 5))
        shapes[near] = "point"
    elif pose == "carry":
        tab = {"L": (hx - 0.55 * R, hy + 1.95 * R), "R": (hx + 0.45 * R, hy + 1.95 * R)}
        shapes = {"L": "fist", "R": "fist"}
    elif pose == "slide":
        cx, cy = st["candle"]
        tab[near] = (cx + 26, cy - 4)
    return tab, shapes


class Smooth:
    def __init__(self):
        self.v = {}

    def __call__(self, key, target, tau=0.2, snap=False):
        if key not in self.v or snap:
            self.v[key] = target
        else:
            a = 1 - math.exp(-DT / tau)
            self.v[key] += (target - self.v[key]) * a
        return self.v[key]


def main():
    tl = json.load(open("build/timeline.json"))
    beats = tl["beats"]; total = tl["total"]
    env = np.load("build/env.npz")
    nf = int(total * FPS) + 1
    rng = np.random.default_rng(11)

    # blink schedules
    blinks = {}
    for k in "MA":
        ts, t = [], 1.2 + rng.uniform(0, 1)
        while t < total + 5:
            ts.append(t)
            if rng.uniform() < 0.15:
                ts.append(t + 0.32)
            t += rng.uniform(2.2, 5.0)
        blinks[k] = np.array(ts)

    # subtitles
    subs = []
    for b in beats:
        for text, t0, t1 in sub_chunks(b):
            subs.append((t0, t1, b["s"], text))

    # cards: group consecutive beats with the same ref
    card_spans = []
    for i, (b, sb) in enumerate(zip(beats, BEATS)):
        cd = sb.get("card")
        if not cd:
            continue
        ref = cd[0]
        if card_spans and card_spans[-1]["ref"] == ref and card_spans[-1]["last"] == i - 1:
            span = card_spans[-1]; span["last"] = i; span["t1"] = b["next"] - 0.15
        else:
            span = dict(ref=ref, card=cd, first=i, last=i, t0=b["start"] - 0.25, t1=b["next"] - 0.15, sub=None)
            card_spans.append(span)
        if cd[4] == "sub" and span["sub"] is None:
            wt = word_time(b["segs"], "the one reading")
            if wt is None:
                wt = word_time(b["segs"], "reading")
            span["sub"] = (wt - 0.55) if wt else b["start"] + 0.8
            span["sub"] = max(span["sub"], span["t0"] + 0.9) if i == span["first"] else span["sub"]

    sm = Smooth()
    states = []
    prev_shot = None; shot_t0 = 0
    prev_emo = {"M": None, "A": None}
    extra_blink = {"M": [], "A": []}
    tear_t0 = None
    glance = {"M": (0, 0, 0), "A": (0, 0, 0)}

    for f in range(nf):
        t = f * DT
        k = 0
        for j, b in enumerate(beats):
            if t >= b["start"] - 0.12:
                k = j
        b = beats[k]; sb = BEATS[k]
        vdur = max(0.3, b["end"] - b["start"])
        frac = (t - b["start"]) / vdur
        fx = sb.get("fx", {})
        S = dict(t=t, f=f, beat=k)

        # ---- camera
        shot = pick(split(sb.get("shot", "two")), frac)
        if t < b["start"] and k > 0:
            shot = pick(split(sb.get("shot", "two")), 0)
        if shot != prev_shot:
            shot_t0 = t; prev_shot = shot
        S["shot"] = shot; S["shot_t"] = t - shot_t0
        S["shot_dur"] = max(1.0, b["next"] - shot_t0)
        S["beat_segs"] = b["segs"]; S["beat_start"] = b["start"]; S["beat_end"] = b["end"]

        speaking = b["s"] if b["start"] <= t <= b["end"] + 0.05 else None
        # ---- props
        abe_enter_beat = 2
        ab = beats[abe_enter_beat]
        rel = t - ab["start"]
        S["mugs_on"] = k > abe_enter_beat or (k == abe_enter_beat and rel > 0.0) or t > ab["start"]
        place_t = 4.9
        S["mug_placed"] = (t - ab["start"]) > place_t
        cold = 0.0
        for j in range(len(beats)):
            if BEATS[j].get("fx", {}).get("cold") and t > beats[j]["start"]:
                cold = min(1, (t - beats[j]["start"] - 1.5) / 3)
        S["steam"] = 1 - max(0, cold)
        rain = 1.0
        for j in range(len(beats)):
            if BEATS[j].get("fx", {}).get("rain_ease") and t > beats[j]["start"]:
                rain = 1 - 0.75 * min(1, (t - beats[j]["start"]) / 3)
        S["rain"] = rain
        # candle
        cs = None
        for j, sbb in enumerate(BEATS):
            if sbb.get("fx", {}).get("candle_slide"):
                cs = j
        cb = beats[cs]
        cf = (t - cb["start"]) / (cb["end"] - cb["start"])
        u = min(1, max(0, (cf - 0.35) / 0.5))
        u = u * u * (3 - 2 * u)
        S["candle"] = (CANDLE0[0] + (CANDLE1[0] - CANDLE0[0]) * u, CANDLE0[1] + (CANDLE1[1] - CANDLE0[1]) * u)
        # mirror
        S["mirror"] = 0.0
        if fx.get("mirror") and shot == "window":
            S["mirror"] = min(1, S["shot_t"] / 0.9)
        S["title"] = 1.0 if t < 4.0 else max(0, 1 - (t - 4.0) / 0.8)
        S["end"] = 0.0
        if fx.get("end"):
            S["end"] = min(1, max(0, (t - b["end"] - 0.3) / 1.2))

        # ---- card
        S["card"] = None
        for sp in card_spans:
            if sp["t0"] <= t <= sp["t1"] + 0.35:
                a_in = min(1, (t - sp["t0"]) / 0.35)
                a_out = min(1, max(0, (sp["t1"] + 0.35 - t) / 0.35))
                subp = 0.0 if sp["sub"] is None else max(0, t - sp["sub"])
                S["card"] = dict(c=sp["card"], a=min(a_in, a_out), sub=subp, has_sub=sp["sub"] is not None, age=t - sp["t0"])
        # ---- subtitle
        S["sub"] = None
        for (t0, t1, spk, text) in subs:
            if t0 <= t < t1:
                S["sub"] = (spk, text, t - t0)

        # ---- characters
        for name in "MA":
            c = dict(CH[name]); c["name"] = name
            d = c["dir"]
            emo_spec = split(sb.get(name.lower()), "neutral")
            emo = pick(emo_spec, frac)
            if emo != prev_emo[name] and prev_emo[name] is not None and rng.uniform() < 0.7:
                extra_blink[name].append(t + 0.04)
            prev_emo[name] = emo
            P = dict(BASE); P.update(EMO.get(emo, {}))
            out = {}
            for key in BASE:
                out[key] = sm(name + key, P[key], TAU.get(key, 0.22))
            # pose
            pose = pick(split(sb.get(name.lower() + "p"), "table"), frac)
            if name == "A" and k == abe_enter_beat:
                pose = "carry" if rel < place_t else "mug"

            # base position (Abe walks in during beat 2)
            bx, by = c["hx"], c["hy"]
            walk = 0.0
            present = True
            if name == "A":
                if k < abe_enter_beat:
                    present = False
                elif k == abe_enter_beat:
                    wu = min(1, max(0, (rel - 0.2) / 4.0))
                    bx = 900 + (c["hx"] - 900) * (1 - (1 - wu) ** 2)
                    walk = 1.0 if 0 < wu < 1 else 0.0
                    stand = 1.0 if rel < 4.6 else max(0, 1 - (rel - 4.6) / 1.0)
                    stand = stand * stand * (3 - 2 * stand)
                    by = c["hy"] - 105 * stand
                    if walk:
                        by += -abs(math.sin(rel * 5.2)) * 9
            lean = out["lean"] * 7 * d
            if pose == "sip":
                out["tilt"] += -d * 0.07
                out["lid"] = max(out["lid"], 0.45)
            # laughter bounce
            shake = out["shake"] * math.sin(t * 2 * math.pi * 6.5) * 3.0 * (0.6 + 0.4 * math.sin(t * 1.7))
            breath = math.sin(t * 2 * math.pi * 0.24 + (0 if name == "M" else 1.7))
            S_body_x = bx + lean
            S_body_y = by + breath * 1.2 + shake
            # speech motion
            if speaking == name:
                e = float(env[name][min(f, len(env[name]) - 1)])
                z = float(env[name + "z"][min(f, len(env[name + "z"]) - 1)])
            else:
                e, z = 0.0, 0.0
            jaw_t = max(out["jawbase"], min(1.0, e * 0.9))
            jaw = sm(name + "jaw", jaw_t, 0.045)
            es = sm(name + "es", e, 0.25)
            mw = out["mw"] * (0.86 + 0.32 * min(1, z * 4)) if e > 0.08 else out["mw"]
            mw = sm(name + "mwv", mw, 0.06)
            # turn & head
            turn = c["turn"]
            if shot == "cam" and name == "M":
                turn = 0.0
            if fx.get("headshake") and name == b["s"]:
                ts = t - (b["start"] + vdur * fx["headshake"])
                if 0 < ts < 1.3:
                    turn += 0.16 * math.sin(ts * 2 * math.pi * 2.0) * (1 - ts / 1.3)
            turn = sm(name + "turn", turn, 0.15, snap=(shot == "cam" and S["shot_t"] < DT * 1.5))
            nod = 0.0
            if fx.get("nod") and name == b["s"]:
                ts = t - b["start"]
                if 0 < ts < 1.6:
                    nod = math.sin(ts * 2 * math.pi * 1.25) * 0.05 * c["R"] * (1 - ts / 1.6)
            tilt = out["tilt"] * d * -1 + (0.025 * math.sin(t * 1.3 + (0 if name == "M" else 2)) * es)
            if shot == "cam" and name == "M":
                tilt = out["tilt"] * 0.6
            hx = S_body_x + 0.0
            hy = S_body_y - es * 0.035 * c["R"] + nod + jaw * 1.5
            # gaze
            g = sb.get(name.lower() + "g")
            if g == "cam":
                gt = (0.0, 0.0)
            elif g is not None:
                gt = tuple(g)
            elif "gaze" in P:
                gt = (P["gaze"][0] * d, P["gaze"][1])
            else:
                gt = c["gaze"]
                if speaking is None and b["s"] == "N":
                    gt = (c["gaze"][0] * 0.6, 0.15)
            if name == "M" and k < abe_enter_beat:
                gt = (0.2, 0.8)
            if name == "M" and k == abe_enter_beat:
                gt = (0.2, 0.8) if rel < 2.6 else (0.85, -0.25)
            # speaker glances away now and then
            gl = glance[name]
            if speaking == name and t > gl[0] + gl[1] + 2.4 and rng.uniform() < 0.02:
                glance[name] = (t, rng.uniform(0.35, 0.8), rng.choice([0, 1]))
            gl = glance[name]
            if gl[0] <= t <= gl[0] + gl[1] and g is None:
                gt = ((0.15 * d, 0.45) if gl[2] == 0 else (-0.3 * d, -0.35))
            jit = (0.04 * math.sin(math.floor(t * 2.3) * 12.9898 + (0 if name == "M" else 3)),
                   0.03 * math.sin(math.floor(t * 2.3) * 78.233))
            gx = sm(name + "gx", gt[0] + jit[0], 0.06)
            gy = sm(name + "gy", gt[1] + jit[1], 0.06)
            # blink
            bl = 0.0
            for bt in list(blinks[name]) + extra_blink[name]:
                dtb = t - bt
                if 0 <= dtb < 0.17:
                    bl = max(bl, dtb / 0.06 if dtb < 0.06 else 1 - (dtb - 0.06) / 0.11)
            wink = 0.0
            if fx.get("wink") and name == "A":
                wt = b["start"] + vdur * 0.85
                dtw = t - wt
                if 0 <= dtw < 0.55:
                    wink = min(1, dtw / 0.08) if dtw < 0.35 else max(0, 1 - (dtw - 0.35) / 0.2)
            # tear
            tear = 0.0
            if name == "M":
                if fx.get("tear"):
                    if tear_t0 is None or tear_t0 < b["start"] - 0.5:
                        tear_t0 = b["start"] + vdur * 0.55
                    tear = max(0, (t - tear_t0) / 2.4)
                elif tear_t0 is not None and t - tear_t0 < 14 and k in (15, 16, 17, 64):
                    tear = 1.0 + (t - tear_t0) / 30
            # hands
            hs = dict(hx=c["hx"], hy=c["hy"], R=c["R"], dir=d, name=name)
            if name == "A" and k == abe_enter_beat:
                hs["hx"], hs["hy"] = bx, by
            tgt, shapes = pose_targets(hs, pose, t, frac, S)
            hand = {}
            for side in "LR":
                snap = name == "A" and k == abe_enter_beat and rel < place_t
                hand[side + "x"] = sm(name + side + "x", tgt[side][0], 0.16, snap=snap)
                hand[side + "y"] = sm(name + side + "y", tgt[side][1], 0.16, snap=snap)
                hand[side + "h"] = shapes[side]
            hold = sm(name + "hold", 1.0 if pose in ("mug", "sip") else 0.0, 0.12)
            S[name] = dict(present=present, bx=S_body_x, by=S_body_y, hx=hx, hy=hy, turn=turn, tilt=tilt,
                           gx=gx, gy=gy, blink=bl, wink=wink, lid=out["lid"], lidb=out["lidb"],
                           brow=out["brow"], btilt=out["btilt"], basym=out["basym"], smile=out["smile"],
                           mw=mw, jaw=jaw, blush=out["blush"], wet=out["wet"], pupil=out["pupil"],
                           tear=tear, breath=breath, sway=0.02 * math.sin(t * 1.1) + shake * 0.004,
                           hold=hold, pose=pose, carry=(pose == "carry"), **hand)
        states.append(S)
    pickle.dump(dict(states=states, total=total), open("build/states.pkl", "wb"))
    print("frames", nf)


if __name__ == "__main__":
    main()
