"""Crowd extras: randomized full-body variants of the main rig with their own
procedural behaviour (gaze, blinks, reactions, talking and gestures)."""
import math

import numpy as np
import skia

import chars
import hair
from gfx import mix
from body import make_arms
from rig import Character

SKINS = [("#e8b38c", "#c88763", "#a8694c"), ("#d39a6e", "#b0744f", "#8e5a3d"), ("#c88a60", "#a26a45", "#7f5034"),
         ("#efc29e", "#d0906c", "#ad6e50"), ("#b97c55", "#925c3c", "#704329")]
CLOTH = ["#8a6744", "#6f8197", "#5d6140", "#9a4f3c", "#b59a6a", "#4f5a6e", "#7a5a6a", "#c9b48a", "#6a4a3a", "#8c8c7a"]
HAIRS = [("#2a1d15", "#150e09", "#5a4636"), ("#3d2516", "#24150c", "#7a5236"), ("#1b1512", "#0c0806", "#463a32"),
         ("#8e8880", "#5f5a54", "#d0ccc4")]


def make_extra(seed, female=None):
    rng = np.random.default_rng(seed)
    female = rng.uniform() < 0.4 if female is None else female
    base = dict(chars.MIRIAM_ST if female else chars.JESUS_ST)
    sk = SKINS[rng.integers(len(SKINS))]
    base.update(skin=sk[0], skin_sh=sk[1], skin_sh2=sk[2])
    hc = HAIRS[rng.integers(3 if female else 4)]
    base.update(hair=hc[0], hair_sh=hc[1], hair_hl=hc[2], beard=hc[0], beard_sh=hc[1], brow_col=hc[0])
    cl = CLOTH[rng.integers(len(CLOTH))]
    cl_sh = "#" + "".join(f"{int(c * 255 * 0.72):02x}" for c in mix(cl, cl, 0)[:3])
    head = CLOTH[rng.integers(len(CLOTH))]
    head_sh = "#" + "".join(f"{int(c * 255 * 0.75):02x}" for c in mix(head, head, 0)[:3])
    base.update(cloth=head, cloth_sh=head_sh)
    base["eye_h"] = base["eye_h"] * rng.uniform(0.85, 1.05)
    base["shoulder_w"] = base["shoulder_w"] * rng.uniform(0.92, 1.1)
    base["hem_y"] = 16.0 if female else rng.choice([12.4, 13.2, 15.6])
    base["mouth_w"] = base["mouth_w"] * rng.uniform(0.9, 1.1)
    kw = {}
    kind = rng.integers(3)
    if female or kind == 0:
        kw["headwear_back"] = hair.HeadCloth(layer="back", vol=0.2, flare=0.6)
        kw["headwear_front"] = hair.HeadCloth(layer="front", vol=0.2, flare=0.6, hair_fringe=female)
    elif kind == 1:
        kw["headwear_front"] = hair.ShortCurly()
        kw["ears"] = True
    else:
        kw["headwear_back"] = hair.LongHair(layer="back", tip_y=1.6, y_hang=0.3)
        kw["headwear_front"] = hair.LongHair(layer="front", tip_y=1.5, y_hang=0.3)
    if not female:
        grey = 0.6 if hc[0] == "#8e8880" else 0.0
        kw["beard"] = hair.Beard(vol=0.04, chin=rng.uniform(0.06, 0.25), grey=grey)
    neck = "round" if rng.uniform() < 0.6 else "v"
    belt = CLOTH[rng.integers(len(CLOTH))]
    kw["outfit"] = chars.tunic_outfit(cl, cl_sh, neckline=neck, belt=(belt, "#" + "".join(f"{int(c * 255 * 0.7):02x}" for c in mix(belt, belt, 0)[:3])))
    kw["arms"] = make_arms({-1: dict(sleeve=cl, sleeve_sh=cl_sh), 1: dict(sleeve=cl, sleeve_sh=cl_sh)})
    return Character(f"extra{seed}", base, **kw)


MOOD_EXPR = {
    "listen": dict(bi_l=0.15, bi_r=0.15, m_smile=0.05),
    "awe": dict(br_l=0.35, br_r=0.35, bi_l=0.2, bi_r=0.2, eo_l=1.08, eo_r=1.08, m_open=0.06),
    "worried": dict(bi_l=0.55, bi_r=0.55, eo_l=1.05, eo_r=1.05, m_press=0.25, m_smile=-0.2),
    "murmur": dict(bi_l=-0.15, bi_r=0.1, bfur=0.3, eo_l=0.95, eo_r=0.95, m_smile=-0.15),
    "agitated": dict(bi_l=-0.35, bi_r=-0.35, bfur=0.55, eo_l=1.08, eo_r=1.08, m_smile=-0.3),
    "skeptical": dict(br_l=0.4, br_r=-0.2, eo_l=0.85, eo_r=0.75, m_smirk=0.3, m_smile=-0.1),
}
EXPR_KEYS = sorted({k for e in MOOD_EXPR.values() for k in e})
DEFAULTS = dict(eo_l=1.0, eo_r=1.0)


class Behavior:
    """Procedural performance for one crowd member: gaze shifts between the
    speaker and neighbours, blinks, breathing, small reactions, whispering to a
    neighbour (murmur) and, when agitated, talking and gesturing.

    moods: a mood name, or a list of (time, mood) changes."""

    def __init__(self, seed, moods="listen", focus=-1.0, t0=0.0):
        self.rng = np.random.default_rng(seed * 7 + 3)
        self.seed = seed
        self.moods = [(t0 - 10.0, moods)] if isinstance(moods, str) else sorted(moods)
        self.focus = focus  # screen direction of the speaker (-1 left, +1 right)
        r = self.rng
        # gaze plan: (start, gx, gy, yaw, talking)
        plan = []
        t = self.moods[0][0] + 10.0 - r.uniform(0, 2.0) if isinstance(moods, str) else self.moods[0][0] - r.uniform(0, 2.0)
        while t < self.moods[-1][0] + 140:
            mood = self.mood_at(t)
            u = r.uniform()
            if mood == "agitated":
                choice = "neighbor" if u < 0.55 else ("focus" if u < 0.85 else "down")
                dur = r.uniform(0.6, 1.6)
            elif mood == "murmur":
                choice = "neighbor" if u < 0.45 else ("focus" if u < 0.85 else "down")
                dur = r.uniform(0.8, 2.2)
            elif mood == "worried":
                choice = "focus" if u < 0.55 else ("neighbor" if u < 0.85 else "down")
                dur = r.uniform(1.0, 3.0)
            else:
                choice = "focus" if u < 0.7 else ("neighbor" if u < 0.9 else "down")
                dur = r.uniform(1.4, 4.2)
            talk = False
            if choice == "focus":
                gx, gy, yaw = max(-0.6, min(0.6, 0.42 * focus)), r.uniform(-0.12, 0.05), 20 * focus + r.uniform(-5, 5)
            elif choice == "neighbor":
                d = -1 if r.uniform() < 0.5 else 1
                gx, gy, yaw = 0.45 * d, r.uniform(-0.05, 0.1), 24 * d
                talk = mood == "murmur" and r.uniform() < 0.6
            else:
                gx, gy, yaw = r.uniform(-0.2, 0.2), 0.45, 8 * focus
            plan.append((t, gx, gy, yaw, talk))
            t += dur
        self.plan = plan
        self.blinks = list(np.cumsum(r.uniform(1.8, 4.8, 120)) + plan[0][0])
        self.talk_phase = r.uniform(0, 10)
        tg = self.moods[0][0] + r.uniform(0.2, 2.5)
        self.gesture_t = []
        while tg < self.moods[-1][0] + 60:
            if self.mood_at(tg) == "agitated":
                self.gesture_t.append(tg)
            tg += r.uniform(1.8, 3.5)

    def mood_at(self, t):
        m = self.moods[0][1]
        for (mt, mood) in self.moods:
            if mt <= t:
                m = mood
        return m

    def expr_at(self, t):
        """Expression for the current mood, eased over 1 s after each change."""
        cur = {}
        for i, (mt, mood) in enumerate(self.moods):
            if mt > t:
                break
            tgt = MOOD_EXPR.get(mood, {})
            x = 1.0 if i == 0 else min(1.0, max(0.0, (t - mt) / 1.0))
            x = x * x * (3 - 2 * x)
            cur = {k: cur.get(k, DEFAULTS.get(k, 0.0)) + (tgt.get(k, DEFAULTS.get(k, 0.0)) - cur.get(k, DEFAULTS.get(k, 0.0))) * x
                   for k in EXPR_KEYS}
        return cur

    def params(self, t):
        # gaze with smooth transitions (eyes fast, head slower)
        cur = self.plan[0]
        prev = cur
        for p in self.plan:
            if p[0] <= t:
                prev, cur = cur, p
            else:
                break
        u_eye = min(1.0, max(0.0, (t - cur[0]) / 0.18))
        u_head = min(1.0, max(0.0, (t - cur[0]) / 0.7))
        u_head = u_head * u_head * (3 - 2 * u_head)
        gx = prev[1] + (cur[1] - prev[1]) * u_eye
        gy = prev[2] + (cur[2] - prev[2]) * u_eye
        yaw = prev[3] + (cur[3] - prev[3]) * u_head
        P = self.expr_at(t)
        P.update(gx=gx, gy=gy, yaw=yaw, t=t, pitch=2.0 * math.sin(t * 0.37 + self.seed), roll=1.5 * math.sin(t * 0.29 + self.seed * 2),
                 breath=0.5 + 0.5 * math.sin(t * 1.5 + self.seed), wind=0.3)
        # blink
        mult = 1.0
        for b in self.blinks:
            if b <= t < b + 0.22:
                x = t - b
                mult = 1 - x / 0.065 if x < 0.065 else (0.0 if x < 0.1 else min(1.0, (x - 0.1) / 0.12))
                break
        P["eo_l"] = P.get("eo_l", 1.0) * mult
        P["eo_r"] = P.get("eo_r", 1.0) * mult
        mood = self.mood_at(t)
        if mood == "agitated":
            s = math.sin(t * 9.0 + self.talk_phase) * math.sin(t * 2.3 + self.talk_phase * 0.5)
            P["m_open"] = max(0.0, s) * 0.55
            P["pitch"] += 3.0 * math.sin(t * 4.0 + self.seed)
            for g in self.gesture_t:
                if g <= t < g + 1.6:
                    x = (t - g) / 1.6
                    amt = math.sin(math.pi * x)
                    side = 1 if (self.seed % 2) else -1
                    P["arm_r" if side > 0 else "arm_l"] = dict(target=(side * 3.4, 2.4, 1.4), hand="open", palm=(0.2, -1.0, 0.4),
                                                               rest_blend=1 - amt, beat=0.8)
                    break
        elif cur[4]:
            # whispering to a neighbour: small, quick mouth movements and a lean in
            s = math.sin((t - cur[0]) * 11.0 + self.talk_phase) * math.sin((t - cur[0]) * 3.1)
            fade = min(1.0, (t - cur[0]) / 0.3)
            P["m_open"] = P.get("m_open", 0.0) + max(0.0, s) * 0.3 * fade
            P["roll"] += 3.0 * (1 if cur[1] > 0 else -1) * fade
        elif mood in ("worried", "awe"):
            P["m_open"] = P.get("m_open", 0.0) + 0.04 * max(0.0, math.sin(t * 0.7 + self.seed))
        return P


_crowd_chars = {}


def crowd_char(seed, female=None):
    key = (seed, female)
    if key not in _crowd_chars:
        _crowd_chars[key] = make_extra(seed, female)
    return _crowd_chars[key]


_behaviors = {}


def behavior(seed, mood, focus, t0):
    key = (seed, mood if isinstance(mood, str) else tuple(mood), focus, round(t0, 2))
    if key not in _behaviors:
        _behaviors[key] = Behavior(seed, mood, focus, t0)
    return _behaviors[key]


def draw_crowd(cv, t, members, mood="listen", focus=-1.0, t0=0.0, light=None, blur=0.0):
    """members: list of (seed, x, feet_y, S, yaw_bias). Drawn back to front (by feet_y).
    mood: a mood name or a list of (time, mood) changes."""
    if blur > 0:
        p = skia.Paint()
        p.setImageFilter(skia.ImageFilters.Blur(blur, blur, skia.TileMode.kDecal))
        cv.saveLayer(None, p)
    for (seed, x, fy, S, yb) in sorted(members, key=lambda m: m[2]):
        ch = crowd_char(seed)
        P = behavior(seed, mood, focus, t0).params(t)
        P["yaw"] = max(-44.0, min(44.0, P["yaw"] * 0.8 + yb))
        P["byaw"] = max(-36.0, min(36.0, 0.6 * (20 * focus + yb)))  # the body stays turned toward the speaker
        if abs(P["byaw"]) > 18.0:
            # turned well round: the far arm hangs behind the body, as it does seen three-quarters on
            far_key = "arm_r" if P["byaw"] < 0 else "arm_l"
            if P.get(far_key) is None:
                P[far_key] = dict(target=(0.0, 0.0, 0.0), rest_blend=1.0, layer="behind", hand="relaxed")
        if light:
            P.update(light)
        y = fy - 16.95 * S * ch.st.get("body_scale", 1.0)
        ch.draw(cv, P, x, y, S)
    if blur > 0:
        cv.restore()
