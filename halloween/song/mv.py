"""CLICKETY-CLACK music video: choreography, shots and frame rendering.

  python3 mv.py --stills 0 30 60      # PNG stills
  python3 mv.py --workers 4           # all frames -> build/mv_chunks/*.mkv
"""
import argparse
import bisect
import json
import math
import os
import subprocess
import sys
import time

import numpy as np
import skia
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import garden as G  # noqa: E402
import score as SC  # noqa: E402
from anim import q  # noqa: E402
from cat import draw_cat, pose as cpose  # noqa: E402
from gfx import H, W, Camera, Xf, clamp, ease_in_out, ease_out, fill, font, lerp, lin_grad, poly, rad_grad, \
    smooth_path, stroke, text_center  # noqa: E402
from mice import draw_mouse, pose as mpose  # noqa: E402
from skeleton import bone, draw_skeleton, pose as spose, reach, rib_point  # noqa: E402
from subs import Subs  # noqa: E402

BUILD = os.path.join(HERE, "build")
FPS = 24
BEAT, BAR = SC.BEAT, SC.BAR
DUR = SC.TOTAL_BARS * BAR + 2.0
NAMES = ["rattles", "femurella", "clatter", "tibbs"]


def bt(bar, beat=0.0):
    return bar * BAR + beat * BEAT


def sec_of(t):
    cur = SC.SECTIONS[0][0]
    for name, b0, nb, _ in SC.SECTIONS:
        if t >= b0 * BAR:
            cur = name
    return cur


def sec_start(name):
    for n, b0, nb, _ in SC.SECTIONS:
        if n == name:
            return b0 * BAR
    raise KeyError(name)


def ramp(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else float(t >= b)


def hit(t, t0, decay=12.0):
    """1 at t0, decaying afterwards; 0 before."""
    return math.exp(-(t - t0) * decay) if t >= t0 else 0.0


def during(t, t0, t1):
    return t0 is not None and t0 <= t < t1


# ------------------------------------------------------------------ lyrics & lip-sync
def _key(s):
    return "".join(ch for ch in s.lower() if ch.isalnum())


class SongTimeline:
    def __init__(self):
        with open(os.path.join(BUILD, "lyrics.json")) as f:
            raw = json.load(f)
        self.lines = []
        for d in raw:
            info = SC.SINGERS[d["who"]]
            self.lines.append(dict(d, color=info["color"], label=info["label"]))
        self.items = {}
        self.duration = DUR
        self.env = {}
        for k in ("lead", "gang", "kids", "spoken"):
            y, sr = sf.read(os.path.join(BUILD, f"vox_{k}.wav"), dtype="float32")
            m = np.abs(y).max(axis=1)
            hop = sr // 100
            n = len(m) // hop
            e = np.sqrt((m[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
            ref = np.percentile(e[e > 1e-4], 90) if np.any(e > 1e-4) else 1.0
            self.env[k] = np.clip(e / ref, 0, 1.3)
        self.words = sorted((w["start"], _key(w["text"])) for d in self.lines for w in d["words"])
        self._cache = {}

    def stem_for(self, d):
        if not d["sung"]:
            return "spoken"
        return {"ALL": "gang", "TIBBS": "kids", "MICE": "kids"}.get(d["who"], "lead")

    def jaw(self, who_set, t):
        v = 0.0
        for d in self.lines:
            if d["who"] in who_set and d["start"] - 0.08 <= t <= d["end"] + 0.08:
                e = self.env[self.stem_for(d)]
                i = int(t * 100)
                if 0 <= i < len(e):
                    v = max(v, float(e[i]))
        return min(1.0, v ** 0.8)

    def singing(self, who, t, pad=0.15):
        return any(d["who"] == who and d["start"] - pad <= t <= d["end"] + pad for d in self.lines)

    def word_at(self, word, t0=0.0):
        """Absolute start time of the first word matching `word` at/after t0."""
        k = (_key(word), t0)
        if k not in self._cache:
            self._cache[k] = next((s for s, w in self.words if w == k[0] and s >= t0), None)
        return self._cache[k]


ST = None


def W_(word, after=0.0):
    return ST.word_at(word, after)


SKEL_WHO = {"rattles": {"RATTLES", "ALL"}, "femurella": {"FEMURELLA", "ALL"}, "clatter": {"CLATTER", "ALL"},
            "tibbs": {"TIBBS", "ALL"}}

# ------------------------------------------------------------------ staging
HOME = {"rattles": (420, 1615, 0.95), "femurella": (690, 1615, 0.92), "clatter": (880, 1530, 0.92),
        "tibbs": (200, 1690, 1.0)}
BRIDGE_POS = {"rattles": (290, 1600, 0.95), "femurella": (830, 1600, 0.92), "clatter": (560, 1700, 0.95),
              "tibbs": (180, 1700, 1.0)}
XYLO_POS = {"rattles": (480, 1665, 0.95), "clatter": (735, 1650, 0.92), "femurella": (285, 1590, 0.9),
            "tibbs": (140, 1725, 1.0)}
EMERGE = {"rattles": (bt(4), bt(6)), "femurella": (bt(13, 2), bt(14, 2)), "clatter": (bt(14), bt(15)),
          "tibbs": (bt(15), bt(15, 3))}
XYLO_T = (bt(52), bt(56))
COLLAPSE_T = bt(74, 0.5)
ROOSTER_T = bt(72, 1.6)
STOP_T = (bt(34), bt(36))          # stop-time under the cat's line
FREEZE_T = None                    # set from the lyrics ("FREEZE!" .. "Unfreeze!")
KNOCKS = [bt(2, 0.5), bt(2, 1.0), bt(2, 1.5), bt(3, 0.0), bt(3, 0.5), bt(3, 1.0)]


def hidden_height(name):
    """Local units a skeleton must sink to be fully below the mound lip (hat included)."""
    return 900.0 if name == "clatter" else 790.0


def depth_of(name, t):
    """0 = standing on the mound, 1 = fully underground."""
    e0, e1 = EMERGE[name]
    if t >= e0:
        return 1.0 - ease_out(ramp(t, e0, e1))
    # intro: the skulls are already peeking out on the very first frame, then duck on "Listen..."
    i = NAMES.index(name)
    peek = 0.64 if name != "clatter" else 0.67
    bob = 0.015 * math.sin(t * 5 + i * 1.7)
    duck_at = 2.02 + i * 0.07
    return lerp(peek + bob, 1.0, ease_in_out(ramp(t, duck_at, duck_at + 0.3)))


def mound_shake(name, t):
    if name == "rattles":
        v = max([hit(t, k, 14) for k in KNOCKS] + [0.0])
        if bt(3, 2) <= t < bt(4):
            v = max(v, 0.45 + 0.4 * abs(math.sin(t * 38)))
        return v
    pre = {"femurella": W_("pops", bt(12)), "clatter": EMERGE["clatter"][0], "tibbs": EMERGE["tibbs"][0]}[name]
    if pre is None:
        return 0.0
    return 0.6 * abs(math.sin(t * 40)) if pre - 0.4 <= t < pre else 0.0


def groove(b, amp=1.0, phase=0.0):
    """Basic swing groove: dip on the beat, sway, stepping feet, swinging arms."""
    bb = b + phase
    s = math.sin(math.pi * bb)
    dip = math.cos(math.pi * bb) ** 2
    return dict(bounce=16 * dip * amp, sway=14 * math.sin(math.pi * (bb - 0.5)) * amp,
                sh_l=(28 + 30 * s * amp, 18 + 10 * amp), sh_r=(28 - 30 * s * amp, 18 + 10 * amp),
                foot_l=(-44.0, -22 * max(0.0, s) * amp), foot_r=(44.0, -22 * max(0.0, -s) * amp),
                tilt=5 * math.sin(math.pi * bb) * amp, head_dy=4 * dip * amp, lean=3 * math.sin(math.pi * bb) * amp)


def jazz(t, at_times, dur=0.45):
    """Jazz-hands burst near any of the given times."""
    for tt in at_times:
        u = (t - tt) / dur
        if 0 <= u <= 1:
            return math.sin(math.pi * min(1.0, u * 1.3))
    return 0.0


def chorus_moves(t, cs, P):
    """Chorus choreography (everybody in unison)."""
    b = t / BEAT
    rel = (t - cs) / BEAT          # beats into the chorus
    P.update(groove(b, 1.15))
    P["grin"] = 1.0
    k = jazz(t, [cs + BEAT * x for x in (1.5, 5.5, 17.5)], 0.5)
    if k > 0:  # "clack!": jazz hands and a high kick
        P.update(sh_l=(150 * k + 28 * (1 - k), -10.0), sh_r=(150 * k + 28 * (1 - k), -10.0), hand_l=t * 6,
                 hand_r=t * 6, foot_r=(70.0, -80 * k), brow=0.8 * k)
    if 8 <= rel < 16:  # the skeletons are back: march with a rattle and a snap
        s = math.sin(math.pi * b)
        P.update(sh_l=(60 + 50 * s, 40.0), sh_r=(60 - 50 * s, 40.0), twist=18 * math.sin(math.pi * b * 2))
        if rel >= 15:
            P.update(sh_r=(165.0, -20.0), hand_r=t * 4)
    if 18 <= rel < 24:  # don't you be scared: spooky claws
        u = ramp(rel, 18, 19)
        P.update(sh_l=(120 * u + 30, -50 * u), sh_r=(120 * u + 30, -50 * u), lean=8 * u, brow=-0.7 * u,
                 hand_l=t * 3, hand_r=t * 3, look=(0.0, 0.0))
    if 24 <= rel < 27:  # grab a bony hand: reach out to the viewer
        P.update(sh_r=(85.0, -5.0), sh_l=(30.0, 20.0), lean=-4, brow=0.3)
    if 27 <= rel < 30:  # if you dare!
        u = ramp(rel, 27, 27.4)
        P.update(sh_l=(40 + 120 * u, -20.0), sh_r=(40 + 120 * u, -20.0), brow=0.9 * u, lean=-6 * u)


def look_at(P, tx, ty):
    """Point the pupils toward a world position."""
    dx, dy = tx - P["x"], ty - (P["y"] - 520 * P["scale"])
    d = math.hypot(dx, dy) + 1e-6
    P["look"] = (clamp(dx / d * 1.1, -1, 1), clamp(dy / d * 1.1, -1, 1))


def positions(name, t):
    if FREEZE_T and bt(44) <= t < bt(52):
        return BRIDGE_POS[name]
    if XYLO_T[0] <= t < XYLO_T[1]:
        return XYLO_POS[name]
    return HOME[name]


def skel_pose(name, t):
    x, y, s = positions(name, t)
    P = spose(x=x, y=y, scale=s, seed={"rattles": 1, "femurella": 2, "clatter": 3, "tibbs": 4}[name])
    P.update({"rattles": dict(hat="bowler"), "femurella": dict(flower=True),
              "clatter": dict(big=True, scarf=True), "tibbs": dict(tiny=True, bucket=True)}[name])
    t_real = t
    frozen = FREEZE_T[0] <= t < FREEZE_T[1]
    if frozen:  # hold the pose of the freeze moment
        t = FREEZE_T[0] - 0.01
    sec = sec_of(t)
    b = t / BEAT
    phase = {"rattles": 0.0, "femurella": 0.12, "clatter": -0.1, "tibbs": 0.2}[name]
    P.update(groove(b, 0.6, phase))
    P["look"] = (0.0, 0.1)
    if sec.startswith("chorus"):
        chorus_moves(t, sec_start(sec), P)
    elif sec in ("verse1", "pre1", "verse2", "pre2"):
        P.update(groove(b, 0.75, phase))
    elif sec == "bridge":
        P.update(groove(b, 0.55, phase))
        P["twist"] = 10 * math.sin(math.pi * b)
        tw, tk = W_("wiggle", bt(44)), W_("wobble", bt(44))
        if during(t, tw - 0.1 if tw else None, tk or 0):
            P.update(sh_l=(150.0, -10.0), sh_r=(150.0, -10.0), hand_l=t * 7, hand_r=t * 7, brow=0.7, grin=1.0)
        if during(t, tk - 0.1 if tk else None, FREEZE_T[0]):
            wob = math.sin(t * 22)
            P.update(knee_out=1.0 + 0.9 * wob, bounce=24, foot_l=(-56.0, 0.0), foot_r=(56.0, 0.0), sh_l=(70.0, 30.0),
                     sh_r=(70.0, 30.0), hand_l=t * 7, hand_r=t * 7)
        if t >= FREEZE_T[0] - 0.05:  # silly frozen poses
            P.update({"rattles": dict(sh_l=(160.0, -30.0), sh_r=(70.0, 60.0), foot_r=(60.0, -70.0), lean=-8, brow=1.0,
                                      jaw=0.5),
                      "femurella": dict(sh_l=(100.0, 80.0), sh_r=(100.0, 80.0), foot_l=(-70.0, -60.0), lean=10,
                                        look=(-0.8, -0.4)),
                      "clatter": dict(sh_l=(120.0, -60.0), sh_r=(40.0, 30.0), lean=6, brow=-0.5),
                      "tibbs": dict(sh_l=(170.0, 0.0), sh_r=(170.0, 0.0), foot_r=(50.0, -50.0), brow=1.0)}[name])
    elif sec == "xylo":
        P.update(groove(b, 0.7, phase))
    elif sec == "intro":
        P.update(groove(b, 0.0))
        P["look"] = (math.sin(t * 2.2 + NAMES.index(name)), -0.1)   # peeking around
        P["brow"] = 0.5
        if t > 1.9:
            P["look"] = (0.0, 0.0)
            P["brow"] = 1.0
    # ---- climbing out of the mounds
    depth = depth_of(name, t)
    P["_depth"] = depth
    if depth > 0 and t >= EMERGE[name][0]:
        P.update(sh_l=(170.0, 0.0), sh_r=(150.0, 10.0), hand_l=t * 5, hand_r=t * 5, brow=0.6)
    elif depth > 0:
        P.update(sh_l=(10.0, 5.0), sh_r=(10.0, 5.0))
    # ---- per-character acting
    if name == "rattles":
        rattles_acting(P, t, sec, b)
    elif name == "femurella":
        if sec == "verse2":
            if ST.singing("RATTLES", t):
                look_at(P, 420, 1100)
            tt = W_("trick", bt(24))
            if during(t, tt - 0.6 if tt else None, (tt or 0) + 1.2):
                P.update(sh_r=(150.0, 10.0), hand_r=t * 4)
            tn = W_("comb", bt(24))
            if during(t, tn - 0.3 if tn else None, (tn or 0) + 0.7):  # combing her (non-existent) hair
                P.update(sh_l=(160.0, 70 + 30 * math.sin(t * 16)), tilt=-8)
    elif name == "tibbs":
        tt = W_("trick", bt(24))
        if during(t, tt - 0.6 if tt else None, (tt or 0) + 1.4):
            P.update(sh_r=(150.0, -10.0), bounce=30 * abs(math.sin(t * 8)), brow=0.9, grin=1.0)
        for who_line in ("TIBBS",):
            if ST.singing(who_line, t, 0.1):  # "If you dare!" with a little jump
                P.update(sh_l=(160.0, -20.0), sh_r=(160.0, -20.0), hand_l=t * 6, hand_r=t * 6, bounce=-30, brow=1.0)
    elif name == "clatter":
        clatter_acting(P, t, sec, b)
        tg = W_("grinning", bt(14))
        if sec == "pre1" and tg and t >= tg - 0.3:  # "...and it's grinning at me!"
            P.update(look=(0.0, 0.0), grin=1.0, brow=0.6, tilt=8 * math.sin(t * 3))
    # ---- the band stops: everybody looks up at the cat on the fence
    if STOP_T[0] <= t < STOP_T[1] and depth == 0:
        u = ramp(t, STOP_T[0], STOP_T[0] + 0.25)
        P.update(bounce=0.0, sway=0.0, sh_l=(20.0, 10.0), sh_r=(20.0, 10.0), foot_l=(-44.0, 0.0),
                 foot_r=(44.0, 0.0), tilt=6 * u * (1 if x < G.FENCE_POST_CAT[0] else -1), lean=0.0)
        look_at(P, G.FENCE_POST_CAT[0], G.FENCE_POST_CAT[1] - 120)
        P["brow"] = 0.7 * u
        P["sad"] = 0.25 * u
        if t >= bt(35, 2.5):  # sheepish grin... then straight back into the chorus
            P.update(grin=1.0, sh_l=(40.0, 60.0), sh_r=(40.0, 60.0), look=(0.0, 0.0))
    # ---- outro: the rooster crows
    if sec == "outro" and t < COLLAPSE_T:
        if t >= ROOSTER_T:
            u = ramp(t, ROOSTER_T, ROOSTER_T + 0.15)
            P.update(bounce=0.0, sway=0.0, sh_l=(40 + 120 * u, -10.0), sh_r=(40 + 120 * u, -10.0),
                     brow=1.0, sad=0.5, look=(0.4, -0.7), jaw=0.3, foot_l=(-44.0, 0.0), foot_r=(44.0, 0.0))
        if name == "rattles":
            tu = W_("Uh-oh", bt(72))
            if tu and t >= tu - 0.1:
                P.update(sh_l=(20.0, 150.0), sh_r=(20.0, 150.0), look=(0.0, -0.9), brow=1.0, sad=0.8, tilt=-6)
            ts = W_("sunrise", bt(72))
            if ts and t >= ts - 0.05:
                P.update(look=(0.0, 0.0), sad=1.0, brow=0.6)
    # ---- jaw from the singing
    jaw = ST.jaw(SKEL_WHO[name], t_real)
    if frozen and name != "clatter":
        jaw = P.get("jaw", 0.0)
    P["jaw"] = max(P.get("jaw", 0.0), jaw)
    # ---- collapse at sunrise
    if t >= COLLAPSE_T:
        i = NAMES.index(name)
        P["collapse"] = ease_out(ramp(t, COLLAPSE_T + i * 0.12, COLLAPSE_T + i * 0.12 + 0.6))
        P["blink"] = 1.0 if P["collapse"] > 0.9 else 0.0
        P["sad"] = 0.0
        P["brow"] = 0.0
        if name == "rattles":
            ts = W_("Same", bt(72))
            if ts and t >= ts - 0.4:
                P.update(blink=0.0, look=(0.0, 0.1), brow=0.6, grin=1.0)
                if t > ts + 1.3:
                    P["blink"] = 1.0 if t < ts + 1.55 else 0.0
    # blinks (between beats, every few bars; never while peeking out in the intro)
    if P.get("collapse", 0) == 0 and not frozen and t >= bt(2):
        bb = (b + 0.6 + {"rattles": 0, "femurella": 3, "clatter": 5, "tibbs": 7}[name]) % 11
        if bb < 0.22:
            P["blink"] = 1.0
    return P


def rattles_acting(P, t, sec, b):
    if sec == "verse1":
        tg = W_("garden", bt(4))
        if during(t, tg - 0.2 if tg else None, (tg or 0) + 1.2):  # presenting the garden
            P.update(sh_l=(95.0, 10.0), hand_l=t * 2)
        tk = W_("Knock", bt(4))
        if during(t, tk - 0.1 if tk else None, (tk or 0) + 1.0):
            kk = abs(math.sin((t - tk) * math.pi / BEAT))
            P.update(sh_r=(80.0, -40 - 40 * kk), brow=0.5)
        tw = W_("Who's", bt(4))
        if during(t, tw if tw else None, (tw or 0) + 1.8):  # hand to ear, peering
            P.update(sh_l=(150.0, 120.0), tilt=-10, look=(-0.6, 0.0), brow=0.8)
        tv = W_("waving", bt(4))
        if during(t, tv - 0.3 if tv else None, (tv or 0) + 1.6):
            P.update(sh_r=(160.0, -20 + 40 * math.sin(t * 14)), hand_r=t * 3, grin=1.0, look=(0.0, 0.0))
    if sec == "pre1":
        tf = W_("foot", bt(12))
        if during(t, tf - 0.2 if tf else None, (tf or 0) + 3.0):  # watching the other mounds
            look_at(P, 690, 1500)
            P["brow"] = 0.9
    if sec == "verse2":
        if ST.singing("FEMURELLA", t):
            look_at(P, 690, 1100)
        tt = W_("tummy", bt(24))
        if during(t, tt - 0.3 if tt else None, (tt or 0) + 0.9):  # pats the empty ribcage
            P.update(sh_l=(-20.0, -95.0), sh_r=(-20.0, -95.0), sad=0.5, brow=0.6)
        tn = W_("nose", bt(24))
        if during(t, tn - 0.3 if tn else None, (tn or 0) + 0.9):
            P.update(sh_r=(-10.0, -150.0), look=(0.0, -0.3))
        ts = W_("sniff", bt(24))
        if during(t, ts - 0.2 if ts else None, (ts or 0) + 0.8):
            P.update(tilt=-12, head_dy=-10, look=(0.2, -0.8), blink=0.6)
        th = W_("hair", bt(24))
        if during(t, th - 0.5 if th else None, (th or 0) + 1.6):  # tips the hat: bald as an egg
            u = ramp(t, th - 0.5, th - 0.1)
            P.update(sh_r=(165.0 * u + 28 * (1 - u), -10.0 * u), brow=0.9 * u, grin=1.0, look=(0.0, 0.0))
            if u < 0.5:
                P["hat_lift"] = 50 * u
            else:
                P["hat_hand"] = True
    if sec == "pre2" and t < STOP_T[0]:
        P.update(knee_out=1.0 + 1.6 * math.sin(math.pi * b * 2), bounce=20, sad=0.4, brow=0.7)
    if sec == "xylo":
        xylo_player(P, t)


def clatter_acting(P, t, sec, b):
    if sec == "pre2" and t < STOP_T[0]:
        P.update(knee_out=1.0 + 1.6 * math.sin(math.pi * b * 2 + 1), bounce=20)
    if sec == "bridge" and t < FREEZE_T[0]:
        P["look"] = (0.0, 0.0)
        ts = W_("scream", bt(44))
        if during(t, ts - 0.2 if ts else None, (ts or 0) + 0.5):  # a mock scream
            P.update(sh_l=(150.0, 125.0), sh_r=(150.0, 125.0), brow=1.0, jaw=0.9, lean=-6)
        tr = W_("run", bt(44))
        if during(t, tr - 0.15 if tr else None, (tr or 0) + 1.6):  # running on the spot
            r = math.sin(t * 18)
            P.update(foot_l=(-40.0, -50 * max(0.0, r)), foot_r=(40.0, -50 * max(0.0, -r)), sh_l=(40 + 40 * r, 90.0),
                     sh_r=(40 - 40 * r, 90.0), brow=0.6, lean=-4)
        tk = W_("skeleton", bt(44))
        if during(t, tk - 0.1 if tk else None, (tk or 0) + 0.9):  # a shrug
            P.update(sh_l=(60.0, -60.0), sh_r=(60.0, -60.0), head_dy=8, brow=0.4, sad=0.3)
        tf = W_("fun", bt(44))
        if during(t, tf - 0.15 if tf else None, (tf or 0) + 1.2):
            P.update(sh_l=(165.0, -10.0), sh_r=(165.0, -10.0), hand_l=t * 6, hand_r=t * 6, grin=1.0, brow=0.9)
    if sec == "xylo":
        # proud and still, arms up out of the way, watching the mallet
        P.update(bounce=4 * math.cos(math.pi * b) ** 2, sway=0.0, twist=0.0, lean=-3.0, sh_l=(100.0, -40.0),
                 sh_r=(110.0, -30.0), hand_l=t * 2, hand_r=t * 2, grin=1.0, look=(-0.7, 0.6), tilt=-6,
                 foot_l=(-44.0, 0.0), foot_r=(44.0, 0.0))
        P["rib_glow"] = xylo_rib(t)
        P["scarf_swing"] = 95.0   # tails flung aside so the ribs can be played


XYLO_SOLO = [("E5", .5), ("G5", .5), ("B5", .5), ("G5", .5), ("E5", .5), ("D#5", .5), ("E5", 1),
             ("C6", .5), ("B5", .5), ("A5", .5), ("G5", .5), ("E5", 1), ("_", 1),
             ("A5", .5), ("C6", .5), ("E6", .5), ("C6", .5), ("A5", .5), ("G5", .5), ("F#5", 1),
             ("B5", .25), ("A5", .25), ("G5", .25), ("F#5", .25), ("E5", .25), ("D#5", .25), ("C5", .25), ("B4", .25),
             ("B4", .5), ("D#5", .5), ("F#5", .5), ("B5", .5)]


def _solo_notes():
    from synth import midi
    out, tt = [], bt(52)
    for nt, bb in XYLO_SOLO:
        rib = None if nt == "_" else int(clamp((95 - midi(nt)) / 4.0, 0, 4))
        out.append((tt, bb * BEAT, rib))
        tt += bb * BEAT
    return out


SOLO = None


def xylo_rib(t):
    for t0, d, rib in SOLO:
        if t0 <= t < t0 + min(d, 0.22) and rib is not None:
            return rib
    return -1


def xylo_player(P, t):
    """Rattles plays Big Clatter's ribs with a bone mallet: IK onto the rib that sounds."""
    Pc = skel_pose("clatter", t)
    idx = max(0, bisect.bisect_right([n[0] for n in SOLO], t) - 1)
    t0, d, rib = SOLO[idx]
    nxt = SOLO[idx + 1] if idx + 1 < len(SOLO) else None
    lift = (-40.0, -55.0)
    a = rib_point(Pc, rib if rib is not None else 2)
    if rib is None:
        a = (a[0] + lift[0], a[1] + lift[1])
    if t < SOLO[0][0] or nxt is None:
        tx, ty = a[0] + lift[0] * 0.6, a[1] + lift[1] * 0.6
    else:
        bpt = rib_point(Pc, nxt[2] if nxt[2] is not None else 2)
        if nxt[2] is None:
            bpt = (bpt[0] + lift[0], bpt[1] + lift[1])
        u = clamp((t - t0) / (nxt[0] - t0))
        # rebound a little after the hit, wind up, strike the next rib exactly on its note
        arc = math.sin(math.pi * u ** 1.6) * min(1.0, (nxt[0] - t0) / 0.3)
        v = ease_in_out(clamp((u - 0.2) / 0.6))
        tx = lerp(a[0], bpt[0], v) + lift[0] * arc
        ty = lerp(a[1], bpt[1], v) + lift[1] * arc
    P.update(sway=0.0, lean=4.0, twist=6.0, mallet=True, look=(0.7, 0.3), grin=1.0, brow=0.4)
    P["sh_r"] = reach(P, 1, tx, ty, extra=64.0)
    P["sh_l"] = (120 + 25 * math.sin(t * 4), -40.0)   # showman flourish
    P["hand_l"] = t * 4


# ------------------------------------------------------------------ cat & mice
def cat_pose_fence(t):
    x, y = G.FENCE_POST_CAT
    P = cpose(x=x, y=y + 4, scale=0.3, facing=-1, lid=0.35, lid_tilt=0.2, pupil=0.4, light_dir=-1.0,
              look=(0.0, 0.6))
    P["tail_t"] = t
    P["breathe"] = t * 2
    sec = sec_of(t)
    if sec == "intro":
        P.update(look=(0.0, 0.0), lid=0.3, lid_tilt=0.4, smile=0.3)
    if STOP_T[0] <= t < STOP_T[1]:
        tu, tw = W_("Ugh", bt(33)), W_("What's", bt(33))
        P.update(lid=0.5, lid_tilt=0.5, ear_back=0.3, look=(0.0, 0.7))
        if tu and tw and tu - 0.1 <= t < tw:   # eye roll
            k = ramp(t, tu - 0.1, tw - 0.1)
            P.update(look=(0.8 * math.cos(math.pi * k), -0.8 * math.sin(math.pi * k)), lid=0.55, ear_back=0.6)
        if t >= bt(35, 2.2):  # long-suffering slow blink
            P["lid"] = 0.5 + 0.45 * math.sin(math.pi * ramp(t, bt(35, 2.2), bt(35, 3.6)))
    if sec == "chorus4":
        P["tail_amp"] = 1.0 + 1.5 * abs(math.sin(math.pi * t / BEAT))
        P.update(lid=0.2, smile=0.4, look=(0.0, 0.3))
        P["tilt"] = 8 * math.sin(math.pi * t / BEAT)
    if sec == "outro":
        P.update(look=(0.0, 0.1), lid=0.45, smile=0.5)
    P["mouth"] = ST.jaw({"CAT"}, t) * 0.8
    return P


MICE_LINE = [("wedge", 245, 1835, 0.82), ("pip", 410, 1772, 0.72), ("biscuit", 570, 1850, 0.8),
             ("crumb", 745, 1782, 0.86), ("tilt", 905, 1852, 0.72)]


def mouse_pose_garden(i, name, x, y, s, t):
    t_in = bt(56) + i * 0.18
    u = ease_in_out(ramp(t, t_in, t_in + 2.0))
    P = mpose(x=lerp(-200 - i * 140, x, u), y=y, scale=s, facing=1, light=(-0.4, 0), seed=60 + i)
    if name == "biscuit":
        P["prop"] = "pumpkin"
        P["arm_l"] = (-40.0, -60.0)
        P["arm_r"] = (-40.0, -60.0)
    b = t / BEAT
    if u < 1:
        P["walking"] = 1.0
        P["walk"] = t * 3.2
        P.update(pupil=0.8, brow=0.9, mouth=0.5, mround=0.8)
    else:
        P["lift"] = 22 * abs(math.sin(math.pi * b + i * 0.3))
        P["squash"] = 1 + 0.08 * math.cos(2 * math.pi * b)
        P["tilt"] = 6 * math.sin(math.pi * b + i)
        if name != "biscuit":
            up = abs(math.sin(math.pi * b / 2))
            P["arm_l"] = (60 + 90 * up, -10.0)
            P["arm_r"] = (60 + 90 * up, -10.0)
        P.update(smile=0.8, pupil=1.2, ear_perk=0.6, lid_low=0.3)
    m = ST.jaw({"MICE"}, t)
    P["mouth"] = max(P["mouth"], m)
    if m > 0.1:
        P["brow"] = 0.8
        P["lift"] = 40 * abs(math.sin(math.pi * b))
        if name != "biscuit":
            P["arm_l"] = (160.0, -10.0)
            P["arm_r"] = (160.0, -10.0)
    ty = W_("Yeah", bt(72))
    if ty and t >= ty - 0.1:
        P["lift"] = 60 * abs(math.sin(min(1.0, (t - ty + 0.1) / 0.5) * math.pi))
        P.update(smile=1.0, brow=1.0, mouth=max(P["mouth"], 0.6))
        if name != "biscuit":
            P["arm_l"] = (160.0, -10.0)
            P["arm_r"] = (160.0, -10.0)
    elif t >= COLLAPSE_T and t < (ty or 1e9) - 0.1:  # the skeletons fell apart!
        P.update(lift=0.0, brow=1.0, pupil=0.7, mouth=0.6, mround=1.0, smile=0.0, ear_perk=1.0)
    return P


# ------------------------------------------------------------------ drawing
TITLE_F = None


def draw_title(c, a, y=620):
    global TITLE_F
    if TITLE_F is None:
        TITLE_F = (font("Griffy-Regular.ttf", 132), font("Griffy-Regular.ttf", 56))
    big, small = TITLE_F
    text_center(c, "Clickety-Clack!", 540, y, big, (244, 238, 220), a=a, outline=(16, 10, 24), outline_w=14)
    text_center(c, "(the skeletons are back)", 540, y + 78, small, (255, 196, 110), a=a, outline=(16, 10, 24),
                outline_w=8)


def draw_foot_gag(c, t):
    """Pre-chorus: a bony foot pops out of Femurella's mound and wiggles its toes, then a knee."""
    tf, tk = W_("pops", bt(12)), W_("knee", bt(12))
    if tf is None or not (tf - 0.1 <= t < EMERGE["femurella"][0]):
        return
    mx, my = G.MOUNDS["femurella"]
    with Xf(c, mx + 6, my - 8, sx=1.35):
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(-300, -500, 300, 0), skia.ClipOp.kIntersect, True)
        if t < tk - 0.15:
            up = ease_out(ramp(t, tf - 0.1, tf + 0.15))
            top = 70 - 160 * up
            bone(c, 0, 80, 0, top, 16, 7)
            with Xf(c, 0, top, rot=-8 * math.sin(t * 9)):
                ft = smooth_path([(-14, 10), (-18, -10), (10, -16), (44, -12), (50, 2), (30, 12)], tension=0.6)
                c.drawPath(ft, fill((238, 232, 212)))
                c.drawPath(ft, stroke((60, 58, 72), 2.4))
                for k in range(4):  # wiggly toes
                    a = math.radians(-30 + k * 16 + 14 * math.sin(t * 16 + k * 1.3))
                    x0, y0 = 42 + k * 2, -12 + k * 6
                    bone(c, x0, y0, x0 + math.cos(a) * 24, y0 + math.sin(a) * 24, 9, 20 + k)
        else:
            k = ease_out(ramp(t, tk - 0.15, tk + 0.1))
            bob = 6 * math.sin(t * 10)
            kx, ky = 0, -110 * k + bob
            bone(c, -26, 60, kx, ky, 16, 8)
            bone(c, kx, ky, 28, 60, 15, 9)
            c.drawCircle(kx, ky, 15, fill((238, 232, 212)))
            c.drawCircle(kx, ky, 15, stroke((60, 58, 72), 2.4))
        c.restore()


def skeleton_in_mound(c, name, P, t):
    depth = P.pop("_depth", 0.0)
    if depth >= 0.999:
        return
    if depth <= 0:
        draw_skeleton(c, P)
        return
    mx, my = G.MOUNDS[name]
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(-2000, -3000, 4000, my - 6), skia.ClipOp.kIntersect, True)
    s = P["scale"] * (0.62 if P["tiny"] else 1.0)
    P["y"] = P["y"] + depth * hidden_height(name) * s
    draw_skeleton(c, P)
    c.restore()
    if t >= EMERGE[name][0] and depth < 0.95:  # dirt spray while climbing out
        for k in range(6):
            a = k * 1.05 + t * 3
            r = 60 + 50 * ((t * 4 + k) % 1.0)
            c.drawCircle(mx + math.cos(a) * r, my - 20 - abs(math.sin(a)) * r * 0.8, 6, fill((80, 62, 50)))


def draw_garden_frame(c, t, cam, mice_out=False):
    tq = q(t)
    frozen = FREEZE_T[0] <= t < FREEZE_T[1]
    tb = FREEZE_T[0] if frozen else tq       # the world holds its breath on FREEZE
    dawn = ease_in_out(ramp(t, bt(72, 1.7), bt(74, 2)))
    c.save()
    cam.apply(c, 0.5)
    G.backdrop_far(c, tb, dawn)
    c.restore()
    c.save()
    cam.apply(c, 1.0)
    G.backdrop_near(c, tb, dawn, 1.0, cat_on_fence=lambda cc: draw_cat(cc, cat_pose_fence(tq)))
    G.ground(c, tq)
    for name, (mx, my) in G.MOUNDS.items():
        G.mound(c, mx, my, 1.0, open_=1.0, shake=mound_shake(name, tq), seed=NAMES.index(name))
    G.pumpkins(c, tb, frozen, hop=(t / BEAT) if sec_of(t) == "chorus4" else 0.0)
    draw_foot_gag(c, tq)
    actors = []
    for name in NAMES:
        P = skel_pose(name, tq)
        actors.append((P["y"], "skel", name, P))
    if mice_out:
        for i, (name, x, y, s) in enumerate(MICE_LINE):
            P = mouse_pose_garden(i, name, x, y, s, tb)
            actors.append((P["y"], "mouse", name, P))
    actors.sort(key=lambda a: a[0])
    for _, kind, name, P in actors:
        if kind == "skel":
            skeleton_in_mound(c, name, P, tq)
        else:
            draw_mouse(c, name, P)
    G.fog(c, tb)
    c.restore()
    c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), fill((0, 0, 0), 1.0, rad_grad((W / 2, H * 0.48), H * 0.7,
                                                                             [(0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0.5)],
                                                                             [0, 0.55, 1])))


WINDOW_MICE = [("biscuit", 385, 1442, 1.1, 1), ("tilt", 700, 1446, 1.05, -1),
               ("wedge", 235, 1562, 1.5, 1), ("crumb", 545, 1566, 1.6, -1), ("pip", 855, 1562, 1.45, -1)]


def paper_bat(c, x, y, s, rot):
    with Xf(c, x, y, rot=rot, sx=s):
        c.drawPath(poly([(0, -6), (14, -14), (30, -10), (24, 0), (34, 6), (14, 4), (0, 10), (-14, 4), (-34, 6),
                         (-24, 0), (-30, -10), (-14, -14)]), fill((30, 20, 34)))


def draw_window_frame(c, t, cam):
    """Cutaway: the pencil mice watching from the kitchen window."""
    tq = q(t)
    c.save()
    cam.apply(c, 1.0)
    c.drawRect(skia.Rect.MakeLTRB(-400, -400, W + 400, H + 400), fill((18, 14, 26)))
    for i in range(-6, 20):  # clapboards
        c.drawLine(-400, i * 120, W + 400, i * 120 + 14, stroke((30, 24, 40), 6))
    x0, y0, x1, y1 = 110, 700, 970, 1562
    arch = skia.Path()
    arch.moveTo(x0, y1)
    arch.lineTo(x0, y0 + 260)
    arch.quadTo(x0, y0, 540, y0 - 60)
    arch.quadTo(x1, y0, x1, y0 + 260)
    arch.lineTo(x1, y1)
    arch.close()
    c.drawPath(arch, fill((255, 196, 120), 1.0, lin_grad((0, y0), (0, y1), [(255, 214, 150), (226, 150, 80)])))
    c.save()
    c.clipPath(arch, skia.ClipOp.kIntersect, True)
    # the kitchen inside: a hanging lamp, a paper-bat garland and a shelf for the back row
    c.drawLine(540, y0 - 80, 540, 790, stroke((60, 36, 30), 4))
    c.drawCircle(540, 812, 120, fill((255, 236, 180), 1.0, rad_grad((540, 812), 120, [(255, 246, 210, 0.9),
                                                                                   (255, 220, 150, 0.0)])))
    c.drawPath(poly([(512, 790), (568, 790), (588, 836), (492, 836)]), fill((70, 40, 34)))
    sw = math.sin(tq * 2.0) * 6
    garland = [(x0, 905), (330, 975 + sw), (540, 1000), (750, 975 - sw), (x1, 905)]
    c.drawPath(open_path_pts(garland), stroke((90, 50, 40), 3))
    for k in range(9):
        u = (k + 0.5) / 9
        bx = lerp(x0, x1, u)
        by = 905 + 95 * math.sin(math.pi * u) + 10
        paper_bat(c, bx, by, 0.9, 10 * math.sin(tq * 3 + k))
    c.drawRect(skia.Rect.MakeLTRB(x0, 1440, x1, 1466), fill((150, 90, 50)))
    start = bt(38)
    b = tq / BEAT
    for i, (name, mx, my, s, f) in enumerate(WINDOW_MICE):
        P = mpose(x=mx, y=my, scale=s, facing=f, seed=80 + i, light=(0.4, 0))
        if tq < start + 1.2:  # gasp at the dancing skeletons
            P.update(pupil=0.7, brow=1.0, mouth=0.9, mround=0.9, ear_perk=1.0, look=(-0.3 * f, 0.2))
        else:
            P.update(lift=18 * abs(math.sin(math.pi * b + i * 0.4)), smile=0.9, pupil=1.25, brow=0.5, lid_low=0.35,
                     tilt=8 * math.sin(math.pi * b + i), mouth=0.35 * abs(math.sin(math.pi * b)))
            if name not in ("biscuit",):
                up = abs(math.sin(math.pi * b / 2 + i))
                P["arm_l"] = (60 + 100 * up, -10.0)
                P["arm_r"] = (60 + 100 * up, -10.0)
        if name == "biscuit":
            P.update(prop="pumpkin", arm_l=(-40.0, -60.0), arm_r=(-40.0, -60.0))
        if name == "tilt":
            P["sleep"] = tq < start + 2.0
            if P["sleep"]:
                P.update(lift=0.0, mouth=0.0, brow=0.0, smile=0.0, tilt=10)
        draw_mouse(c, name, P)
    for k in range(3):  # glass reflections
        c.drawPath(poly([(x0 + 100 + k * 260, y0 - 100), (x0 + 160 + k * 260, y0 - 100), (x0 - 140 + k * 260, y1),
                         (x0 - 200 + k * 260, y1)]), fill((255, 255, 255), 0.06))
    c.restore()
    c.drawPath(arch, stroke((10, 8, 16), 40))
    c.drawLine(540, y0 - 50, 540, y1, stroke((10, 8, 16), 18))
    c.drawLine(x0, 1135, x1, 1122, stroke((10, 8, 16), 16))
    c.drawRect(skia.Rect.MakeLTRB(x0 - 60, y1 - 6, x1 + 60, y1 + 40), fill((40, 28, 36)))
    c.restore()


def open_path_pts(pts):
    p = skia.Path()
    p.moveTo(*pts[0])
    for i in range(1, len(pts) - 1):
        mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2
        p.quadTo(pts[i][0], pts[i][1], mx, my)
    p.lineTo(*pts[-1])
    return p


# ------------------------------------------------------------------ shots
WIDE = (540, 1010, 1.0)
GROUP = (560, 1280, 1.3)
TIBBS_CU = (300, 1350, 1.3)
FEM_CU = (690, 1235, 1.45)
MICE_CU = (560, 1250, 1.5)
SHOTS = None


def build_shots():
    return [
        (0.0, "garden", WIDE),                          # skulls peeking out at midnight (title)
        (bt(2), "garden", (425, 1580, 2.3)),            # something's knocking in Rattles' mound
        (bt(4), "garden", (430, 1300, 1.55)),           # he bursts out and sings
        (bt(8), "garden", (430, 1270, 1.7)),            # knock, knock!
        (bt(12), "garden", (760, 1450, 1.8)),           # up pops a foot... a bony knee
        (bt(14), "garden", (860, 1180, 1.4)),           # a grinning skull
        (bt(15, 2), "garden", WIDE),
        (bt(20), "garden", GROUP),
        (bt(22), "garden", WIDE),
        (bt(23, 2), "garden", TIBBS_CU),                # if you dare!
        (bt(24), "garden", (560, 1250, 1.35)),          # verse 2 duet
        (bt(26), "garden", FEM_CU),                     # Femurella
        (bt(27, 1), "garden", TIBBS_CU),                # trick or treat!
        (bt(28), "garden", (430, 1310, 1.5)),           # no nose
        (bt(30), "garden", FEM_CU),                     # never need a comb
        (bt(31, 1), "garden", (430, 1330, 1.45)),       # ...'cause no hair: Rattles tips his hat
        (bt(32), "garden", (560, 1300, 1.25)),          # knockity-knock knees
        (bt(34), "garden", (532, 970, 3.4)),            # the cat: what's all the clatter?
        (bt(35, 2), "garden", GROUP),                   # sheepish grins
        (bt(36), "garden", WIDE),
        (bt(38), "window", (540, 960, 1.0)),            # the pencil mice are watching
        (bt(40), "garden", GROUP),
        (bt(42), "garden", WIDE),
        (bt(43, 2), "garden", TIBBS_CU),
        (bt(44), "garden", (560, 1300, 1.45)),          # Big Clatter's bridge
        (bt(48), "garden", WIDE),
        (bt(52), "garden", (600, 1330, 1.45)),          # rib xylophone
        (bt(56), "garden_mice", WIDE),
        (bt(60), "garden_mice", (560, 1310, 1.18)),
        (bt(62), "garden_mice", WIDE),
        (bt(63, 2), "garden_mice", MICE_CU),            # the mice: if you dare!
        (bt(64), "garden_mice", WIDE),
        (bt(68), "garden_mice", GROUP),
        (bt(70), "garden_mice", WIDE),
        (bt(71, 2), "garden_mice", MICE_CU),
        (bt(72), "garden_mice", WIDE),                  # a rooster?!
        (bt(72, 2), "garden_mice", (420, 1280, 1.6)),   # uh-oh... sunrise
        (bt(74, 0.25), "garden_mice", WIDE),            # collapse
        (bt(75, 3.7), "garden_mice", (430, 1520, 1.9)),  # same time next year?
        (bt(76, 3.6), "garden_mice", WIDE),
    ]


def frame(c, t, subs):
    i = max(0, bisect.bisect_right([s[0] for s in SHOTS], t) - 1)
    _, kind, (cx, cy, z) = SHOTS[i]
    cm = Camera(cx, cy, z)
    if FREEZE_T[0] <= t < FREEZE_T[1]:  # a little punch-in on FREEZE
        cm = Camera(cx, cy - 20, z * 1.06)
    if kind == "window":
        draw_window_frame(c, t, cm)
    else:
        draw_garden_frame(c, t, cm, mice_out=(kind == "garden_mice"))
    # title on the first shot, end card at the end
    if t < bt(2):
        draw_title(c, 1.0 - ramp(t, bt(1, 2), bt(2)))
    if t >= bt(77, 0.5):
        draw_title(c, ramp(t, bt(77, 0.5), bt(77, 1.5)))
        f = font("Griffy-Regular.ttf", 66)
        text_center(c, "Happy Halloween!", 540, 790, f, (255, 210, 130), a=ramp(t, bt(77, 1.0), bt(77, 2.0)),
                    outline=(16, 10, 24), outline_w=9)
    subs.draw(c, t)


class Film:
    def __init__(self):
        global ST, FREEZE_T, SOLO, SHOTS
        ST = SongTimeline()
        FREEZE_T = (W_("FREEZE", bt(49)), W_("Unfreeze", bt(49)) + 0.12)
        SOLO = _solo_notes()
        SHOTS = build_shots()
        self.subs = Subs(ST, base_y=300, captions={}, prefer_latest=True)
        self.surface = skia.Surface(W, H)
        self.n_frames = int(math.ceil(DUR * FPS))

    def render(self, t):
        c = self.surface.getCanvas()
        c.clear(skia.Color(0, 0, 0))
        frame(c, t, self.subs)
        return self.surface


def render_chunk(args):
    idx, f0, f1, out = args
    film = Film()
    buf = np.empty((H, W, 4), np.uint8)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "ultrafast", "-qp", "0",
                          "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(f0, f1):
        film.render(f / FPS).readPixels(skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType),
                                        buf, W * 4)
        p.stdin.write(buf.tobytes())
        if (f - f0) % 240 == 0:
            print(f"[chunk {idx}] {f - f0}/{f1 - f0} {time.time() - t0:.0f}s", flush=True)
    p.stdin.close()
    p.wait()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", nargs="*", type=float)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    if args.stills:
        film = Film()
        os.makedirs(os.path.join(BUILD, "stills"), exist_ok=True)
        for t in args.stills:
            path = os.path.join(BUILD, "stills", f"s{t:07.2f}.png")
            film.render(t).makeImageSnapshot().save(path, skia.kPNG)
            print(path)
        return
    n = int(math.ceil(DUR * FPS))
    cd = os.path.join(BUILD, "mv_chunks")
    os.makedirs(cd, exist_ok=True)
    k = args.workers
    bounds = [n * i // k for i in range(k + 1)]
    jobs = [(i, bounds[i], bounds[i + 1], os.path.join(cd, f"c{i:02d}.mkv")) for i in range(k)]
    from multiprocessing import Pool
    t0 = time.time()
    with Pool(k) as pool:
        outs = pool.map(render_chunk, jobs)
    with open(os.path.join(cd, "list.txt"), "w") as f:
        for o in outs:
            f.write(f"file '{o}'\n")
    print(f"rendered {n} frames in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
