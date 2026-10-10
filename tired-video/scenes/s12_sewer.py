"""s12 — the sewer: waking up, the watcher, the catch, the bond.

Shot list (all times derived from cues / lines; see shots() below):
  A  POV        eyesOpen .. sit+0.2       eyelid wipe out of black, the hole above, a drip falls at us
  B  crater     .. l01.end+0.15           the drip lands on his face (flinch), he sits up, "...Where am I?"
  C  sleeve     .. stumble                lifts a dripping sleeve, "Why am I wet?", brow, lid drop + press
  D  stumble    .. watched                gets up, turns, stumbles screen-left (squish steps); pan
  E1 slits      .. watched+0.62           insert: two teal slits open and blink in the black side tunnel
  E2 freeze     .. sense                  he stops; shoulders rise; eyes slide back, head still
  F  sense/leap .. writhe                 sonar rings + teal irises outline the shadow behind him;
                                          head turns slowly; it lunges, he spins and catches it
  H  writhe     .. form                   it thrashes, he holds firm (feet slide), strain, teal eyes
  I  form       .. eyesWide               the wisps pull in: the sleek creature appears in his arms
  J  eyesWide   .. calm                   tight two-shot: its eyes go wide, his lids lift, glows in sync
  K  calm       .. l03                    limp, nuzzles his chest, purr, heartbeats fall into sync, smile
  L  l03        .. bond                   close: "...Okay. Hi." -- it opens its eyes at "Hi." and chirps
  M  bond       .. end                    slow pull-back in the warm daylight shaft, glows pulsing together
"""
import math

from engine import core, human, creatures, sets, fx
from engine.core import (tween, seg, clamp, lerp, smoothstep, ease_out_back, ease_in_out, ease_out,
                         ease_in, state_at, hash01)
from audio import sfx

M = sets.SEWER_MARKS
S = 0.75                    # Tiredness scale in the sewer world (the set's char_scale)
SC = 0.70                   # creature scale (dog-sized next to him)
FY = M["walk_feet_y"]       # 1282 feet line
HOLE_X = M["hole"][0]       # 1300
TUN = M["side_tunnel"][0]   # (2150, 690, 300, 560)
SLIT = (TUN[0] + TUN[2] * 0.5, 1000)   # the watcher's eyes inside the black side tunnel
CRE_X = 1600                # where the shadow crouches behind him (just outside the light shaft)
X_SIT = 1300                # crater
X_STAND = 1420              # feet after getting up (legs were stretched out to the right)
TK = dict(outfit="sewer", bandage=True, headphones=None)
POWER = "#3ff2e0"
# side-on floor poses (the stock sit_up props the butt ~150 px above the floor in a flat side view)
LIE = {"base": "lie_back", "ar_o": 0.08, "ar_e": 0.3}
SITP = {"base": "sit_up", "ll_p": 1.8, "lr_p": 1.7, "ll_k": 0.1, "lr_k": 0.5}
# writhe strain: clenched teeth, brows pulled in, steady eyes
STRAIN = {"brow": -0.25, "brow_ang": -0.5, "open": 0.3, "teeth": 1.0, "width": 1.1, "curve": -0.3,
          "flare": 0.5, "cheek": 0.15}

# --------------------------------------------------------------------------- timing


def K(info):
    """All key times of the scene, derived from cues and line timings."""
    c = info.cue
    l1, l2, l3 = info.line("s12_l01"), info.line("s12_l02"), info.line("s12_l03")
    k = dict(dur=info.dur, sit=c("sit"), l1=l1.start, l1e=l1.end, l2=l2.start, l2e=l2.end,
             l3=l3.start, l3e=l3.end, stumble=c("stumble"), watched=c("watched"), sense=c("sense"),
             leap=c("leap"), grab=c("grab"), writhe=c("writhe"), form=c("form"), wide=c("eyesWide"),
             calm=c("calm"), bond=c("bond"))
    k["cutB"] = k["sit"] + 0.2
    k["drip_hit"] = k["cutB"] + 0.16
    k["sit0"] = k["drip_hit"] + 0.32           # groggy beat after the flinch, then up
    k["sit1"] = k["sit0"] + 0.85
    k["cutC"] = k["l1e"] + 0.15
    k["lift0"] = k["cutC"] + 0.08
    k["lift1"] = k["lift0"] + 0.42
    k["lower0"] = k["l2e"] + 0.02
    k["rise0"] = k["stumble"] - 0.05
    k["rise1"] = k["rise0"] + 0.6
    k["walk0"] = k["rise1"]
    k["cutE2"] = k["watched"] + 0.62
    nh = max(1, int(round((k["cutE2"] + 0.02 - k["walk0"]) / 0.8)))
    k["walk1"] = k["walk0"] + 0.8 * nh          # stops on a contact pose
    k["hunch0"] = max(k["walk1"] + 0.1, k["cutE2"] + 0.1)
    k["slide0"] = k["hunch0"] + 0.2             # pupils slide back toward the dark
    k["ping"] = k["sense"] + 0.1
    k["turn0"] = k["sense"] + 0.55              # pupils lead, the head follows 0.15 s later
    k["spring"] = k["leap"] + 0.26              # creature leaves the ground
    k["spin0"] = k["leap"] + 0.12
    k["catch"] = k["grab"]
    k["nuzzle"] = k["calm"] + 0.6
    # the "Hi." word (lip-sync word index; fallback 60 % through the line)
    k["hi"] = l3.start + 0.62 * l3.dur
    n = int(l3.dur / 0.02)
    for i in range(n):
        tt = l3.start + i * 0.02
        if info.word_at(tt, "s12_l03") >= 1:     # "...Okay." (0) "Hi." (1)
            k["hi"] = tt
            break
    return k


def warm_k(t, k):
    """0..1 warming of the image (in step with the music's warm turn, ~66 %)."""
    return smoothstep(seg(t, k["form"] + 0.5, k["calm"] + 1.2))


def dim_k(t, k):
    """0..1 ominous darkening while he is being watched."""
    return smoothstep(seg(t, k["watched"], k["watched"] + 0.6)) * (1 - warm_k(t, k))


def pulse(t, k):
    """Shared glow pulse for the two of them (eyesWide onward), 0..1."""
    a = smoothstep(seg(t, k["wide"] + 0.1, k["wide"] + 0.6))
    return a * (0.5 + 0.5 * math.sin(math.tau * (t - k["wide"]) / 1.25 - math.pi / 2))


# --------------------------------------------------------------------------- Tiredness acting


def _fkeys(t, table):
    """{face_key: [(t, v), ...]} -> {face_key: value} (eased)."""
    return {key: tween(t, ks) for key, ks in table.items()}


def _xstop(k):
    v = human.cycle_speed("tired", "stumble", -0.95, "sewer") * S
    return X_STAND + v * (k["walk1"] - k["walk0"]), v


def tired_state(t, k):
    st = dict(x=X_SIT, y=FY, turn=0.0, pose=LIE, pose_t=None, expr="groggy", look=(0, 0),
              blink=None, power=0.0, face={})
    face = {}
    if t < k["rise0"]:
        # ------------------------------------------------------------ crater: lying -> sitting up
        sit_k = ease_in_out(seg(t, k["sit0"], k["sit1"]))
        if sit_k <= 0:
            st["pose"] = LIE
        elif sit_k >= 1:
            st["pose"] = SITP
        else:
            st["pose"] = (LIE, SITP, sit_k)
        st["turn"] = lerp(0.0, 0.9, ease_in_out(seg(t, k["sit0"] + 0.1, k["sit1"])))
        st["expr"] = state_at(t, [(0, "groggy"), (k["l1"] + 0.1, "dazed"), (k["l1e"] + 0.1, "groggy")], 0.3)
        # flinch at the drip: eyes squeeze, then groggy lids
        td = k["drip_hit"]
        if td <= t < td + 0.5:
            st["blink"] = tween(t, [(td, 0.6), (td + 0.04, 1.0), (td + 0.22, 1.0), (td + 0.5, 0.0)])
        elif t < td:
            st["blink"] = 0.6             # still out cold, lids barely parted
        face.update(_fkeys(t, {
            "lower": [(td, 0), (td + 0.05, 0.7), (td + 0.3, 0.6), (td + 0.5, 0.0)],
            "press": [(td, 0), (td + 0.05, 0.6), (td + 0.4, 0.0)],
            "frown": [(td, 0), (td + 0.05, 0.4), (td + 0.4, 0.0)],
            "head_tilt": [(k["sit0"], 0.0), (k["sit1"], 0.07), (k["sit1"] + 0.4, -0.04), (k["l1e"], 0.05)],
            # look up at the hole on "Where", the head follows 0.15 s later
            "head_nod": [(k["l1"] + 0.1, 0.0), (k["l1"] + 0.45, -0.18), (k["l1"] + 0.9, -0.1),
                         (k["l1e"], 0.02)],
            "head_turn": [(k["l1"] + 0.8, 0.0), (k["l1"] + 1.0, -0.22), (k["l1e"] + 0.1, 0.1)],
            "lid": [(k["l1"], 0.08), (k["l1"] + 0.35, -0.06), (k["l1e"], 0.06)],
        }))
        st["look"] = tween(t, [(k["sit1"] - 0.3, (0.3, 0.1)), (k["l1"] + 0.25, (0.05, -1.05)),
                               (k["l1"] + 0.6, (0.0, -1.1)), (k["l1"] + 0.82, (-0.85, -0.3)),
                               (k["l1e"] - 0.05, (0.6, -0.15)), (k["cutC"], (0.4, 0.05))])
        # ------------------------------------------------------------ the sleeve
        if t >= k["cutC"] - 0.1:
            lift = ease_out_back(seg(t, k["lift0"], k["lift1"]), 1.3)
            low = ease_in_out(seg(t, k["lower0"], k["lower0"] + 0.35))
            lk = clamp(lift * (1 - low), 0.0, 1.1)
            # a little limp shake of the wrist (drips fly) after the lift
            wob = math.sin((t - k["lift1"]) * 16.0) * (1 - seg(t, k["lift1"], k["lift1"] + 0.45)) \
                * seg(t, k["lift1"] - 0.05, k["lift1"])
            # forearm held out, limp wrist hanging (the soggy sleeve dripping)
            sleeve = dict(SITP, al_ik=1.0, al_th=1.0, al_hx=-200.0, al_hy=40.0 - 14 * wob, al_hz=170.0,
                          al_h="relaxed", al_w=1.2 + 0.35 * wob, al_layer="front", neck=0.32, nod=0.06,
                          lean=-0.42)
            if lk > 0.001:
                st["pose"] = (SITP, sleeve, lk)
            st["expr"] = state_at(t, [(0, "groggy"), (k["lift0"], "bored"),
                                      (k["l2e"] + 0.05, "unamused")], 0.3)
            face = _fkeys(t, {
                # one brow creeps up on "wet", then the deadpan lid drop + lip press
                "brow_r": [(k["l2"] + 0.55, 0.0), (k["l2"] + 0.9, 0.3), (k["l2e"] + 0.4, 0.26),
                           (k["rise0"], 0.1)],
                "lid": [(k["l2"], 0.02), (k["l2e"] - 0.05, 0.02), (k["l2e"] + 0.2, 0.13)],
                "press": [(k["l2e"], 0.0), (k["l2e"] + 0.2, 0.45), (k["rise0"], 0.35)],
                "head_tilt": [(k["lift0"], 0.03), (k["lift1"], 0.09), (k["l2e"] + 0.2, 0.04)],
                "head_nod": [(k["lift0"], 0.0), (k["lift1"], 0.08)],
            })
            # eyes go to the sleeve first (the head follows), then a flat look away on the lid drop
            st["look"] = tween(t, [(k["cutC"], (0.4, 0.05)), (k["lift0"] + 0.12, (0.85, 0.15)),
                                   (k["l2e"] - 0.15, (0.85, 0.2)), (k["l2e"] + 0.1, (0.25, 0.0)),
                                   (k["rise0"], (0.1, 0.1))])
        st["turn"] = 0.9 if t >= k["sit1"] else st["turn"]
    elif t < k["catch"]:
        # ------------------------------------------------------------ up, turn, stumble, freeze, sense
        xs, v = _xstop(k)
        rk = seg(t, k["rise0"], k["rise1"])
        st["turn"] = -0.95
        if rk < 1:
            a = ease_in_out(seg(rk, 0.0, 0.5))
            b = ease_in_out(seg(rk, 0.45, 1.0))
            st["pose"] = (SITP, "crouch", a) if rk < 0.5 else ("crouch", "stand", b)
            st["x"] = lerp(X_SIT, X_STAND, ease_in_out(seg(rk, 0.15, 0.6)))
            st["turn"] = tween(t, [(k["rise0"] + 0.3, 0.9), (k["rise1"], -0.95)])
            st["expr"] = "groggy"
            st["look"] = tween(t, [(k["rise0"], (0.3, 0.5)), (k["rise1"], (-0.6, 0.2))])
        elif t < k["walk1"]:
            st["x"] = X_STAND + v * max(0.0, t - k["walk0"])
            bk = smoothstep(seg(t, k["walk0"], k["walk0"] + 0.15))
            st["pose"] = ("stand", "stumble", bk) if bk < 1 else "stumble"
            st["pose_t"] = max(0.0, t - k["walk0"])
        else:
            st["x"] = xs
            hk = ease_out_back(seg(t, k["hunch0"], k["hunch0"] + 0.3), 1.6)
            freeze = {"base": "stand", "hunch": 0.15 + 0.5 * hk, "breath": 1 - 0.9 * clamp(hk),
                      "sway": 1 - clamp(hk), "nod": -0.03 * hk, "lean": -0.03 * hk}
            sk = smoothstep(seg(t, k["walk1"], k["walk1"] + 0.22))
            st["pose"] = ("stumble", freeze, sk) if sk < 1 else freeze
            st["pose_t"] = k["walk1"] - k["walk0"]
            st["turn"] = tween(t, [(k["walk1"], -0.95), (k["walk1"] + 0.3, -0.72)])
        if rk >= 1:
            st["expr"] = state_at(t, [(0, "groggy"), (k["walk0"] + 0.5, "bored"),
                                      (k["hunch0"], "neutral")], 0.3)
            st["look"] = tween(t, [(k["walk0"], (-0.6, 0.2)), (k["walk0"] + 0.5, (-0.7, 0.05)),
                                   (k["slide0"], (-0.5, 0.0)), (k["slide0"] + 0.22, (0.95, 0.02)),
                                   (k["sense"] + 0.2, (0.95, 0.05))])
            face = _fkeys(t, {
                "lid": [(k["hunch0"], 0.03), (k["hunch0"] + 0.15, -0.1), (k["sense"], -0.08),
                        (k["ping"], -0.08), (k["ping"] + 0.1, -0.22), (k["ping"] + 0.6, -0.14)],
                "pupil": [(k["hunch0"], 0.0), (k["hunch0"] + 0.2, -0.28), (k["sense"], -0.25),
                          (k["ping"] + 0.3, -0.1)],
                "press": [(k["hunch0"], 0.0), (k["hunch0"] + 0.2, 0.35), (k["sense"] + 0.6, 0.2)],
                "head_turn": [(k["turn0"], 0.0), (k["turn0"] + 1.0, 0.75)],
                "head_tilt": [(k["turn0"], 0.0), (k["turn0"] + 1.0, -0.05)],
            })
            if t >= k["sense"]:
                st["look"] = tween(t, [(k["sense"], (0.95, 0.05)), (k["turn0"] - 0.15, (1.0, 0.1)),
                                       (k["turn0"] + 1.0, (0.55, 0.12))])
        # the spin round to face it, then the catch
        if t >= k["spin0"]:
            sp = ease_out_back(seg(t, k["spin0"], k["spin0"] + 0.3), 1.1)
            st["turn"] = lerp(-0.72, 0.55, sp)
            face["head_turn"] = lerp(0.75, 0.0, clamp(sp))
            anticip = {"base": "stand", "hunch": 0.55, "lean": -0.1, "nod": 0.05}
            catch = {"base": "catch", "hold": 2, "lean": 0.18}
            ck = ease_out(seg(t, k["spin0"] + 0.12, k["catch"]))
            pk = smoothstep(seg(t, k["spin0"], k["spin0"] + 0.12))
            st["pose"] = (anticip, catch, ck) if ck > 0 else ("stand", anticip, pk)
            st["expr"] = "alarmed"
            face["lid"] = -0.2
            face["pupil"] = -0.35
            st["look"] = tween(t, [(k["spin0"], (0.9, 0.0)), (k["catch"], (0.6, 0.2))])
        st["power"] = tween(t, [(k["ping"], 0.0), (k["ping"] + 0.1, 1.0), (k["ping"] + 0.5, 0.8)])
    else:
        # ------------------------------------------------------------ holding it
        xs, v = _xstop(k)
        slide = ease_out(seg(t, k["catch"], k["catch"] + 0.55)) * 70 \
            + ease_out(seg(t, k["writhe"] + 0.45, k["writhe"] + 0.8)) * 22 \
            + ease_out(seg(t, k["writhe"] + 1.35, k["writhe"] + 1.65)) * 14
        st["x"] = xs - slide
        st["turn"] = tween(t, [(k["catch"], 0.55), (k["writhe"], 0.45), (k["calm"] + 0.2, 0.45),
                               (k["calm"] + 0.9, 0.35)])
        imp = 1 - ease_out(seg(t, k["catch"], k["catch"] + 0.3))
        strug = {"base": "struggle_hold", "lean": -0.06 - 0.16 * imp, "hunch": 0.2 + 0.3 * imp}
        catch = {"base": "catch", "hold": 2, "lean": 0.05}
        ck = smoothstep(seg(t, k["catch"], k["catch"] + 0.3))
        calm_k = ease_in_out(seg(t, k["calm"] + 0.1, k["calm"] + 0.9))
        cradle = {"base": "cradle", "nod": 0.2, "tilt": 0.06}
        if calm_k > 0:
            st["pose"] = (strug, cradle, calm_k)
        elif ck < 1:
            st["pose"] = (catch, strug, ck)
        else:
            st["pose"] = strug
        st["pose_t"] = t
        st["expr"] = state_at(t, [(0, "alarmed"), (k["catch"] + 0.12, STRAIN), (k["form"] + 0.7, "neutral"),
                                  (k["calm"] + 0.4, "soft_smile")], 0.3)
        p = pulse(t, k)
        face = _fkeys(t, {
            "brow": [(k["form"] + 0.6, 0.0), (k["wide"], 0.12), (k["wide"] + 0.35, 0.24),
                     (k["calm"] + 0.3, 0.06)],
            "brow_ang": [(k["form"] + 0.7, 0.0), (k["calm"], 0.05), (k["calm"] + 0.7, 0.22)],
            # lids: steady in the fight; lift with it in the mirror moment; soften after
            "lid": [(k["catch"], -0.16), (k["form"] + 0.7, -0.14), (k["wide"], -0.14),
                    (k["wide"] + 0.25, -0.3), (k["calm"] + 0.1, -0.26), (k["calm"] + 0.9, -0.17),
                    (k["l3"], -0.16), (k["bond"] + 0.6, -0.13)],
            "pupil": [(k["form"] + 0.6, -0.1), (k["wide"] + 0.25, 0.25), (k["calm"] + 0.5, 0.15)],
            "open": [(k["wide"] + 0.1, 0.0), (k["wide"] + 0.35, 0.07), (k["calm"] + 0.2, 0.07),
                     (k["calm"] + 0.5, 0.0)],
            "head_tilt": [(k["catch"], 0.0), (k["catch"] + 0.2, -0.1), (k["form"], -0.08),
                          (k["form"] + 1.0, 0.0), (k["calm"] + 0.9, 0.07)],
            "head_nod": [(k["catch"], 0.0), (k["catch"] + 0.2, -0.12), (k["form"] + 0.8, -0.04),
                         (k["wide"], 0.04), (k["calm"] + 0.8, 0.1)],
            # the rare, faint smile
            "curve": [(k["calm"] + 0.6, 0.0), (k["calm"] + 1.3, 0.22), (k["l3"], 0.24), (k["bond"], 0.32)],
            "lower": [(k["calm"] + 0.6, 0.0), (k["calm"] + 1.3, 0.15)],
            "smirk": [(k["calm"] + 0.9, 0.0), (k["calm"] + 1.4, 0.12)],
        })
        # the head jerks away from the snapping maw now and then
        if t < k["form"] + 0.6:
            jerk = math.sin(t * 6.3) * 0.035 * (1 - seg(t, k["form"], k["form"] + 0.6))
            face["head_tilt"] = face.get("head_tilt", 0) + jerk
        st["look"] = tween(t, [(k["catch"], (-0.2, 0.4)), (k["catch"] + 0.3, (-0.5, 0.5)),
                               (k["form"] + 0.5, (-0.55, 0.6)), (k["wide"], (-0.55, 0.72)),
                               (k["calm"] + 0.4, (-0.45, 0.7))])
        # no blink may steal the mirror moment (its eyes go wide, his lids lift)
        if k["wide"] - 0.1 <= t < k["calm"] - 0.1:
            st["blink"] = 0.0
        # a slow, fond blink just before he speaks
        t0 = k["l3"] - 1.05
        if t0 <= t < t0 + 0.95:
            st["blink"] = tween(t, [(t0, 0.0), (t0 + 0.3, 1.0), (t0 + 0.5, 1.0), (t0 + 0.95, 0.0)])
        st["power"] = 0.78 + 0.17 * p - 0.06 * smoothstep(seg(t, k["calm"], k["calm"] + 1.5))
    st["face"] = face
    return st


def draw_tired(ctx, t, info, k, st=None, hold=None):
    st = st or tired_state(t, k)
    return human.draw_person(ctx, "tired", st["x"], st["y"], S, t, pose=st["pose"], expr=st["expr"],
                             look=st["look"], mouth=info.mouth("tired", t), face=st["face"],
                             turn=st["turn"], blink=st["blink"], power=st["power"], pose_t=st["pose_t"],
                             hold=hold, **TK)


# --------------------------------------------------------------------------- the creature

# silhouette of the form-0 crouch (facing right, ground point 0,0, s=1) for the sonar outline
SIL = [(-290, -300), (-255, -305), (-238, -240), (-205, -200), (-165, -248), (-130, -215), (-92, -268),
       (-52, -226), (-12, -265), (22, -216), (62, -238), (108, -248), (148, -286), (176, -236),
       (222, -214), (252, -160), (252, -96), (216, -55), (162, -46), (152, 0), (92, 5), (72, -50),
       (-58, -55), (-80, 2), (-152, 6), (-202, -58), (-236, -120), (-266, -190), (-302, -262)]


def shadow_path(ctx, x, y, s, flip=True):
    pts = [(x + (-px if flip else px) * s, y + py * s) for px, py in SIL]
    core.smooth_path(ctx, pts, closed=True, tension=0.6)


def spec_kw(t, k):
    """Creature controls while it is in his arms."""
    form = ease_in_out(seg(t, k["form"], k["form"] + 1.4))
    wr = 1.0 - 0.85 * ease_in_out(seg(t, k["form"] + 0.2, k["form"] + 1.3))
    wr *= 1.0 - seg(t, k["wide"], k["wide"] + 0.3)
    p = pulse(t, k)
    expr, look, tilt, blink = "snarl", (0.4, -0.5), 0.0, None
    if t >= k["wide"]:
        expr, look = "wide", (0.55, -0.85)        # it sees his teal eyes: the same glow
    if t >= k["calm"]:
        expr, look = "calm", (0.5, -0.8)
        tilt = 0.12 * ease_in_out(seg(t, k["calm"], k["calm"] + 0.45))   # goes limp, head sinks
    if t >= k["nuzzle"]:
        expr = "content"
        tilt = 0.12 + 0.09 * math.sin(math.tau * (t - k["nuzzle"]) / 1.2)   # rubbing into his chest
    if t >= k["hi"] - 0.05:
        expr, look = "calm", (0.55, -0.85)
        tilt = 0.08 * (1 - ease_out(seg(t, k["hi"], k["hi"] + 0.3))) - 0.04 * ease_out(seg(t, k["hi"], k["hi"] + 0.3))
        bt = t - (k["hi"] - 0.05)
        blink = clamp(1.0 - bt / 0.25) if bt < 1.3 else None   # eyes ease open, look up at him, no blink
    if t >= k["bond"] + 0.45:
        expr = "content"
        tilt = 0.06 + 0.05 * math.sin(math.tau * (t - k["bond"]) / 1.6)
        blink = None
    glow = 1.0 + 0.55 * p + 0.2 * warm_k(t, k)
    return dict(form=form, writhe=wr, expr=expr, look=look, glow=glow, tilt=tilt, blink=blink)


def make_hold(t, k, store):
    """Hold callback: the creature sits between his arms (his front arm wraps over it)."""
    kw = spec_kw(t, k)
    calm_k = ease_in_out(seg(t, k["calm"] + 0.1, k["calm"] + 0.9))
    sag = 6 * ease_in_out(seg(t, k["calm"], k["calm"] + 0.5))

    def hold(ctx, side, hx, hy, ang):
        store["hold"] = (hx, hy)
        if t < k["catch"]:
            return
        ik = 1 - ease_out(seg(t, k["catch"], k["catch"] + 0.25))
        dx = (-60 - 30 * calm_k) * S + ik * 20
        dy = (48 + 10 * calm_k + sag) * S
        a = creatures.draw_specimen(ctx, hx + dx, hy + dy, SC, t, pose="held", flip=True, face=1.0, **kw)
        store["spec"] = a
    return hold


def draw_shadow_creature(ctx, t, alpha, sq=1.0):
    """The shadow form crouched on the walkway behind him (form 0), drawn at `alpha`."""
    if alpha <= 0.01:
        return

    def fn(c):
        with core.saved(c, CRE_X, FY, (1.0 + (1 - sq) * 0.6, sq)):
            creatures.draw_specimen(c, 0, 0, SC, t, form=0.0, pose="crouch", expr="snarl", flip=True)
    core.fade_group(ctx, alpha, fn)


def draw_slits(ctx, x, y, s, t, open_k):
    """Two bare glowing teal slits in the dark (the watcher)."""
    if open_k <= 0.01:
        return
    core.radial_glow(ctx, x, y, 170 * s, POWER, 0.2 * open_k)
    for side in (-1, 1):
        ex = x + side * 52 * s
        ey = y + 2 * s * math.sin(t * 1.3)
        w, h = 38 * s, 12 * s * open_k
        with core.saved(ctx, ex, ey, 1.0, side * 0.22):
            ctx.move_to(-w, 0)
            ctx.curve_to(-w * 0.4, -h * 1.5, w * 0.4, -h * 1.2, w, h * 0.2)
            ctx.curve_to(w * 0.3, h * 1.1, -w * 0.4, h * 1.0, -w, 0)
            ctx.close_path()
            core.fill(ctx, POWER, preserve=True)
            core.stroke(ctx, core.alpha("#c9fff8", 0.7), 3 * s)
            core.circle(ctx, side * 7 * s, 0, 5 * s * open_k)
            core.fill(ctx, "#062a28")


# --------------------------------------------------------------------------- set + overlays


def sewer_bg(ctx, t, k):
    light = 1.0 - 0.26 * dim_k(t, k)
    sets.sewer(ctx, t, layer="bg", light=light)


def warm_beam(ctx, t, k):
    """Warm the daylight shaft (static shape, the alpha ramps slowly)."""
    w = warm_k(t, k)
    if w <= 0.01:
        return
    hx = HOLE_X
    ctx.move_to(hx - 105, 110)
    ctx.line_to(hx + 105, 110)
    ctx.line_to(hx + 260, 1300)
    ctx.line_to(hx - 260, 1300)
    ctx.close_path()
    core.fill(ctx, (1.0, 0.80, 0.48, 0.17 * w))
    core.ellipse(ctx, hx, 1272, 300, 40)
    core.fill(ctx, (1.0, 0.85, 0.55, 0.16 * w))


def warm_screen(ctx, t, k):
    w = warm_k(t, k)
    if w > 0.01:
        ctx.rectangle(0, 0, core.W, core.H)
        core.fill(ctx, (1.0, 0.72, 0.42, 0.07 * w))


def drip_drop(ctx, x, y, s, stretch=1.0):
    core.ellipse(ctx, x, y, 10 * s, 14 * s * stretch)
    core.fill(ctx, "#cdf2e8", preserve=True)
    core.stroke(ctx, "#1d1626", 3 * s)
    core.circle(ctx, x - 3 * s, y - 4 * s, 3 * s)
    core.fill(ctx, "#ffffff")


def splash(ctx, x, y, s, t, t0, n=6, seed=0, dur=0.45, spread=1.0, color="#cdf2e8", up=1.0):
    """Tiny crown of droplets flicked up from (x, y)."""
    p = seg(t, t0, t0 + dur)
    if t < t0 or p >= 1:
        return
    for i in range(n):
        a = -math.pi / 2 + (hash01(i, seed) - 0.5) * 2.2 * spread
        v = (90 + 90 * hash01(i, seed + 3)) * s * up
        px = x + math.cos(a) * v * p * 1.4
        py = y + math.sin(a) * v * p * 1.4 + 260 * s * p * p
        r = (6 + 3 * hash01(i, seed + 5)) * s * (1 - 0.5 * p)
        core.circle(ctx, px, py, r)
        core.fill(ctx, core.alpha(color, 1 - p * p), preserve=True)
        core.stroke(ctx, core.alpha("#1d1626", 0.6 * (1 - p * p)), 2 * s)


def sleeve_drips(ctx, t, k, a):
    """Drops falling from the lifted cuff (wrist anchor)."""
    if not (k["lift1"] - 0.1 <= t < k["lower0"] + 0.5):
        return
    wx, wy = a["wrist_l"]
    for i, t0 in enumerate((k["lift1"] - 0.05, k["lift1"] + 0.12, k["lift1"] + 0.5, k["l2"] + 0.8,
                            k["l2e"] - 0.15)):
        dt = t - t0
        if 0 <= dt < 0.55:
            yy = wy + 12 * S + 0.5 * 2600 * S * dt * dt
            drip_drop(ctx, wx + (8 - 5 * i) * S, yy, S * 0.95, 1.0 + min(0.4, dt * 1.5))


def hair_drip(ctx, t, k, a):
    """A drop rolling off the damp fringe now and then (tiny life)."""
    hx, hy = a["face"]
    for t0 in (k["l1"] + 0.5, k["cutC"] + 1.3):
        dt = t - t0
        if 0 <= dt < 0.45:
            drip_drop(ctx, hx - 45 * S, hy + 25 * S + 0.5 * 2400 * S * dt * dt, S * 0.7)


# --------------------------------------------------------------------------- shots


def shot_A(ctx, t, info, k):
    """POV: lying in the crater, looking straight up at the hole (groggy head drift)."""
    rot = 0.035 * math.sin(t * 0.9 + 0.3)
    z = 1.0 + 0.06 * ease_out(seg(t, 0, k["cutB"]))
    with core.camera(ctx, 540, 960, z, rot):
        sets.sewer_hole_pov(ctx, t, drip_t0=k["cutB"] - 0.95 * 1.32)
    fx.eyelid_wipe(ctx, t, 0.0, k["sit"])


def shot_B(ctx, t, info, k):
    st = tired_state(t, k)
    up = ease_in_out(seg(t, k["sit0"] + 0.1, k["sit1"] + 0.25))
    cx = lerp(1060, 1290, up)
    cy = lerp(1080, 1040, up)
    z = lerp(2.15, 2.05, up) + 0.12 * ease_in_out(seg(t, k["sit1"], k["cutC"]))
    with core.camera(ctx, cx, cy, z):
        sewer_bg(ctx, t, k)
        a = draw_tired(ctx, t, info, k, st)
        # the drip that wakes him: falls onto his cheek, tiny splash
        fxp, fyp = a["face"]
        td = k["drip_hit"]
        if td - 0.24 <= t < td:
            p = seg(t, td - 0.24, td)
            drip_drop(ctx, fxp + 6 * S, fyp - 560 * S * (1 - p * p), S * 1.3, 1.3)
        splash(ctx, fxp + 6 * S, fyp - 14 * S, S * 1.2, t, td, n=7, seed=4, dur=0.42)
        # water sheds as he sits up out of the puddle
        sx = st["x"]
        splash(ctx, sx - 80 * S, FY - 14, S, t, k["sit0"] + 0.2, n=7, seed=9, dur=0.55)
        splash(ctx, sx + 120 * S, FY - 14, S, t, k["sit0"] + 0.35, n=5, seed=12, dur=0.5)
        hair_drip(ctx, t, k, a)


def shot_C(ctx, t, info, k):
    st = tired_state(t, k)
    z = 2.35 + 0.15 * ease_in_out(seg(t, k["cutC"], k["stumble"]))
    with core.camera(ctx, 1345, 1030, z):
        sewer_bg(ctx, t, k)
        a = draw_tired(ctx, t, info, k, st)
        sleeve_drips(ctx, t, k, a)
        hair_drip(ctx, t, k, a)


def shot_D(ctx, t, info, k):
    st = tired_state(t, k)
    # pan with him as he stumbles off to the left (lead room ahead of him)
    xs, v = _xstop(k)
    cx = lerp(1380, xs - 40, ease_in_out(seg(t, k["rise0"] + 0.3, k["watched"] + 0.3)))
    with core.camera(ctx, cx, 960, 1.4):
        sewer_bg(ctx, t, k)
        draw_tired(ctx, t, info, k, st)


def shot_E1(ctx, t, info, k):
    """Insert: in the black side-tunnel mouth, two teal slits open and blink."""
    z = 1.6 + 0.14 * ease_in_out(seg(t, k["watched"], k["cutE2"]))
    with core.camera(ctx, SLIT[0] - 10, SLIT[1] + 40, z):
        sewer_bg(ctx, t, k)
        t0 = k["watched"] + 0.12
        o = ease_out(seg(t, t0, t0 + 0.2))
        tb = k["watched"] + 0.42
        if tb <= t < tb + 0.16:
            o *= 1 - math.sin(math.pi * seg(t, tb, tb + 0.16))
        draw_slits(ctx, SLIT[0] + 6 * math.sin(t * 0.7), SLIT[1], 1.15, t, o)


def shot_E2(ctx, t, info, k):
    st = tired_state(t, k)
    xs, v = _xstop(k)
    with core.camera(ctx, xs + 30, 800, 2.3):
        sewer_bg(ctx, t, k)
        draw_tired(ctx, t, info, k, st)


def shot_F(ctx, t, info, k):
    """Sense -> leap -> catch, one continuous two-shot."""
    st = tired_state(t, k)
    z = 1.16 + 0.06 * ease_in_out(seg(t, k["sense"], k["leap"])) + 0.1 * ease_out(seg(t, k["catch"], k["writhe"]))
    cx = 1435 - 90 * ease_in_out(seg(t, k["spring"], k["writhe"]))
    dx, dy = core.shake(t, k["catch"], 0.35, 16)
    store = {}
    with core.camera(ctx, cx + dx, 990 + dy, z):
        sewer_bg(ctx, t, k)
        # --- the shadow behind him (shown by the rings, then it lunges)
        rev = smoothstep(seg(t, k["ping"] + 0.5, k["ping"] + 1.1))
        if t < k["spring"]:
            al = 0.4 * rev + 0.6 * smoothstep(seg(t, k["leap"], k["leap"] + 0.12))
            sq = 1.0 - 0.14 * math.sin(math.pi * seg(t, k["leap"], k["spring"]))   # squash before the spring
            draw_shadow_creature(ctx, t, al, sq)
        a = draw_tired(ctx, t, info, k, st, hold=make_hold(t, k, store))
        # --- the lunge: it flies at his hands (in front of him)
        if k["spring"] <= t < k["catch"]:
            p = seg(t, k["spring"], k["catch"])
            hl, hr = a["hand_l"], a["hand_r"]
            tx, ty = (hl[0] + hr[0]) / 2 - 20 * S, (hl[1] + hr[1]) / 2 + 30 * S
            x0, y0 = CRE_X + 60 * SC, FY - 140 * SC
            e = ease_in(p) * 0.3 + p * 0.7
            px = lerp(x0, tx, e)
            py = lerp(y0, ty, e) - math.sin(math.pi * p) * 110
            fx.motion_lines(ctx, px + 170 * SC, py, 0.0, 240, t, 1.0, color="#0b1110", seed=3)
            creatures.draw_specimen(ctx, px, py, SC * (1.0 + 0.1 * math.sin(math.pi * p)), t, form=0.0,
                                    pose="leap", expr="snarl", flip=True)
        # --- impact: skid + water flick at the feet
        if t >= k["catch"]:
            fx.dust_puff(ctx, st["x"], FY, S, t, k["catch"], seed=2, dur=0.7, color="#9fc9bd", spread=0.8)
            splash(ctx, st["x"] - 70 * S, FY - 8, S, t, k["catch"] + 0.02, n=7, seed=21, dur=0.5)
        # --- the sense: rings from his head light up the shadow's silhouette
        hx, hy = a["head"]
        out = (lambda c: shadow_path(c, CRE_X, FY, SC)) if t < k["leap"] + 0.1 else None
        fx.ripple_rings(ctx, hx, hy, 1.0, t, k["ping"], n=3, interval=0.42, ring_dur=1.5, max_r=820,
                        width=9, outline_fn=out)
        if k["ping"] <= t < k["ping"] + 0.5:
            ex, ey = a["eye_r"]
            fx.eye_glint(ctx, ex, ey, 0.8, t, k["ping"] + 0.05, dur=0.4)


def _two_shot(ctx, t, info, k, cam, hearts=False, glow_pool=0.0):
    st = tired_state(t, k)
    store = {}
    cx, cy, z = cam
    with core.camera(ctx, cx, cy, z):
        sewer_bg(ctx, t, k)
        warm_beam(ctx, t, k)
        if glow_pool > 0.01:
            core.radial_glow(ctx, st["x"] - 60, 960, 520, "#ffcf8a", 0.2 * glow_pool)
        a = draw_tired(ctx, t, info, k, st, hold=make_hold(t, k, store))
        sp = store.get("spec")
        if hearts and sp is not None:
            t0 = k["calm"] + 0.35
            sync = smoothstep(seg(t, t0 + 0.3, k["l3"] + 0.2))
            # his heart: upper chest (clear of his hands); its heart: on its chest
            (l1x, l1y), (r1x, r1y) = a["shoulder_l"][:2], a["shoulder_r"][:2]
            hx1, hy1 = (l1x + r1x) / 2 + 22 * S, (l1y + r1y) / 2 + 62 * S
            hx2, hy2 = sp["hold_points"]["chest"]
            fx.heartbeat_sync(ctx, hx1, hy1, hx2 - 10 * S, hy2 + 12 * S, t, t0, sync, s=0.8, period=0.9)
    return st, a


def shot_H(ctx, t, info, k):
    xs, v = _xstop(k)
    z = 1.95 + 0.12 * ease_in_out(seg(t, k["writhe"], k["form"]))
    dx, dy = core.shake(t, k["writhe"] + 0.95, 0.3, 7)
    cam = (xs - 105 + dx, 905 + dy, z)
    _two_shot(ctx, t, info, k, cam)
    # the feet skid back under the thrashing (wet walkway): small puffs + flicks
    st = tired_state(t, k)
    with core.camera(ctx, *cam):
        for i, ts in enumerate((k["writhe"] + 0.45, k["writhe"] + 1.35)):
            fx.dust_puff(ctx, st["x"] + 20 * S, FY, S * 0.8, t, ts, seed=5 + i, dur=0.6, color="#9fc9bd",
                         spread=0.6)
            splash(ctx, st["x"] - 40 * S, FY - 8, S * 0.8, t, ts + 0.02, n=5, seed=31 + i, dur=0.45)


def shot_I(ctx, t, info, k):
    xs, v = _xstop(k)
    z = 2.35 + 0.15 * ease_in_out(seg(t, k["form"], k["wide"]))
    _two_shot(ctx, t, info, k, (xs - 140, 860, z))


def shot_J(ctx, t, info, k):
    xs, v = _xstop(k)
    z = 2.9 + 0.12 * ease_in_out(seg(t, k["wide"], k["calm"]))
    _two_shot(ctx, t, info, k, (xs - 80, 790, z))


def shot_K(ctx, t, info, k):
    xs, v = _xstop(k)
    z = 2.05 + 0.1 * ease_in_out(seg(t, k["calm"], k["l3"]))
    _two_shot(ctx, t, info, k, (xs - 135, 880, z), hearts=True, glow_pool=warm_k(t, k))


def shot_L(ctx, t, info, k):
    xs, v = _xstop(k)
    z = 2.95 + 0.1 * ease_in_out(seg(t, k["l3"], k["bond"]))
    _two_shot(ctx, t, info, k, (xs - 100, 835, z), hearts=True, glow_pool=warm_k(t, k))


def shot_M(ctx, t, info, k):
    xs, v = _xstop(k)
    p = ease_in_out(seg(t, k["bond"], k["dur"]))
    z = lerp(2.4, 1.55, p)
    _two_shot(ctx, t, info, k, (xs - 120 + 70 * p, lerp(820, 880, p), z), hearts=True,
              glow_pool=warm_k(t, k))


def shots(k):
    return [(0.0, shot_A), (k["cutB"], shot_B), (k["cutC"], shot_C), (k["stumble"], shot_D),
            (k["watched"], shot_E1), (k["cutE2"], shot_E2), (k["sense"], shot_F), (k["writhe"], shot_H),
            (k["form"], shot_I), (k["wide"], shot_J), (k["calm"], shot_K), (k["l3"], shot_L),
            (k["bond"], shot_M)]


_K = {}


def _keys(info):
    key = (info.id, info.dur, tuple(sorted(info.cues.items())))
    if key not in _K:
        _K.clear()
        _K[key] = K(info)
    return _K[key]


def render(ctx, t, info):
    k = _keys(info)
    ctx.rectangle(0, 0, core.W, core.H)
    core.fill(ctx, "#0b1f1d")
    fn = shot_A
    for t0, f in shots(k):
        if t >= t0:
            fn = f
    fn(ctx, t, info, k)
    warm_screen(ctx, t, k)


# --------------------------------------------------------------------------- sound


def SFX(info):
    k = K(info)
    ev = []
    ev += sfx.loop_events("sewer_ambience", 0.0, info.dur, -6)
    ev.append((0.0, "eye_open", -1))
    ev.append((0.3, "drip", -13, -0.3))
    ev.append((k["drip_hit"] - 0.02, "drip", -3, 0.0))
    ev.append((k["sit0"] + 0.15, "water_splash", -10, 0.0))
    ev.append((k["sit0"] + 0.3, "cloth_rustle", -4, 0.0))
    # the sleeve: rustle + drips hitting the puddle
    ev.append((k["lift0"], "cloth_rustle", -5, 0.1))
    for t0 in (k["lift1"] - 0.05, k["lift1"] + 0.5, k["l2"] + 0.8):
        ev.append((t0 + 0.3, "drip", -14, 0.15))
    # getting up + squishy stumble steps (one per contact)
    ev.append((k["rise0"] + 0.15, "water_splash", -13, 0.0))
    ev.append((k["rise0"] + 0.45, "squish", -4, 0.0))
    # stumble foot contacts land at ~0.47 s and ~1.15 s of each 1.6 s cycle; the stop plants at walk1
    i = 0
    for c0 in range(4):
        for ph in (0.47, 1.15):
            tc = k["walk0"] + 1.6 * c0 + ph
            if tc < k["walk1"] - 0.05:
                ev.append((tc, "squish", -2 - (i % 2), -0.1 * i))
                i += 1
    ev.append((k["walk1"] + 0.05, "squish", -6, -0.2))
    # watched: a low growl from the dark (behind him, screen-right), his heart thumps
    ev.append((k["watched"] + 0.1, "creature_snarl", -13, 0.6))
    ev.append((k["hunch0"], "heartbeat", -5, 0.0))
    ev.append((k["hunch0"] + 0.62, "heartbeat", -7, 0.0))
    # the sense
    ev.append((k["ping"], "sonar_ping", 0, 0.0))
    # the lunge and the catch
    ev.append((k["leap"], "creature_hiss", 0, 0.35))
    ev.append((k["spring"], "whoosh", -6, 0.2))
    ev.append((k["catch"], "body_thud", -3, 0.0))
    ev.append((k["catch"] + 0.02, "water_splash", -6, -0.1))
    # writhe
    ev.append((k["writhe"] + 0.05, "creature_snarl", -1, 0.0))
    ev.append((k["writhe"] + 0.25, "cloth_rustle", -2, 0.0))
    ev.append((k["writhe"] + 0.45, "squish", -6, -0.1))
    ev.append((k["writhe"] + 1.35, "squish", -7, -0.1))
    ev.append((k["writhe"] + 1.25, "creature_hiss", -5, 0.0))
    ev.append((k["form"] - 0.25, "cloth_rustle", -6, 0.0))
    # the change
    ev.append((k["form"] + 0.05, "swoosh_up", -9, 0.0))
    ev.append((k["form"] + 1.15, "sparkle", -12, 0.0))
    # calm: purr + two heartbeats falling into sync (heart 2 lags less and less, as drawn)
    ev.append((k["nuzzle"] - 0.1, "creature_purr", 2, 0.0))
    ev.append((k["l3"] + 0.3, "creature_purr", -4, 0.0))
    ev.append((k["hi"] + 0.35, "creature_chitter", -7, 0.0))
    ev.append((k["bond"] + 0.4, "creature_purr", 0, 0.0))
    t0 = k["calm"] + 0.35
    j = 1
    while t0 + j * 0.9 < k["bond"] + 0.8:
        tb = t0 + j * 0.9
        sync = smoothstep(seg(tb, t0 + 0.3, k["l3"] + 0.2))
        lag = (1 - sync) * (0.5 + 0.22 * math.sin(math.tau * (tb - t0) / 3.1)) * 0.9
        g = -10 if k["l3"] - 0.1 < tb < k["l3e"] else -7
        ev.append((tb, "heartbeat", g, -0.15))
        if lag > 0.06:
            ev.append((tb + 0.9 - lag, "heartbeat", g - 3, 0.15))
        j += 1
    return ev
