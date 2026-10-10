"""s11 . The turn: the wall and the door (music 'heart').

F5 two-shot at night (lair, dim wash, rain), Malvo at screen-left with Hissy
curled round him like a scarf, the AI hologram floating screen-right.

Beats (every time from cues / word starts):
  slump   fade in from black; Malvo slumped, head down; Hissy worried.
  l01     "Keep testing me, Evil Genius...": the AI drifts lower + closer,
          warm and a little teasing (open palm "keep going", a shrug on
          "Kinda heroic", WINK + sparkle on "huh?"). Malvo lifts his head on
          "Evil Genius", frowns at "protect people", goes aghast at "heroic".
  l01b    "Heroic? Ugh! I'm a villain.": disgusted; on "Ugh!" he CROSSES HIS
          ARMS (forearms folded over the chest, gloves tucked) and turns his
          head away from the AI, nose up, eyes shut. Hissy copies.
  l01c    "Then it'll take an amazing villain to trick me. Have at it.": the
          AI is amused, open palm on "Have at it". On "amazing villain" one
          eye peeks open at the AI (Hissy peeks too), then snaps shut.
  l01d    "...That's what I thought.": he peeks back, smug half-smile, a
          begrudging little nod on "thought"; the arms relax at the end.
  beat    the bravado drains: eyes drop, the monocle slips and dangles (tink).
  l02     glistening eyes; on "noticed me" his eyes go to the corkboard photo
          (the AI's eyes follow); eyes drop on "scaring them".
  photo   hard cut: the science-fair photo close-up, held through the whole
          pause and "I noticed." (~3 s): slow gentle push-in 1.00 -> 1.07, the
          rainy window's light across the board with raindrop shadows
          trickling down, the rows of EMPTY chairs reading clearly. Once it has
          sat alone, Malvo's live face fades in as a round PiP (bottom-left)
          looking up at it: glistening eyes, ONE sad slow blink, heavy lids;
          on "I noticed." his eyes lift toward the AI's voice.
  l03     "I noticed. Clever. Skeptical. Persistent." cut back on "Clever":
          SLOW BLINK -> warm; the VILLAIN STATS sheet pops over his head and
          each row's label (CLEVER / SKEPTICAL / PERSISTENT) pops in ON its
          word, its five bars filling right after.
  l04     on "impressive" a gold IMPRESSIVE! badge slams onto the sheet, the
          header pulses on "villain"; AI happy + thumbs up, eyes to camera on
          "my guy". Hissy nods.
  l05     "...Impressive?": he LIKES the word: eyes widen (the monocle springs
          back in), a pleased evil grin, chest puffs (elbows out), a sparkle.
  wall    sheet fades; the AI projects a cyan hologram: the door pops in, the
          wall builds so its last row thuds on "Brick"; firm nod "Every time".
  l07     light leaks round the door, it cracks ajar; three glowing chips
          (SCARY STORIES / CREATIVE PLANS / SOUND THE ALARM) squeeze out, on
          "Scary", "creative" (he rubs his hands) and "sounding"; on "wide
          open" it swings open and warm gold light spills across his face.
  pile    five gifts pop out of the door and arc into his arms / onto the desk
          (notebook + quill, headphones, THE CHEMIST scroll, the SPACE LASERS
          FOR DUMMIES book (its cover satellite fires pink bolts, "PEW PEW
          PEW", at a startled little moon), the BOMBSHELL TWIST script); his
          eyes follow each one, getting wider. He hugs the book.
  l08     the spooky gifts pop out on their words (pumpkin, bat, goblin mask,
          dragon figurine).
  smile   he looks down at the pile; a slow REAL SMILE. Hissy happy. Hold.
"""
import math

import cairocffi as cairo

from engine import core
from engine.core import (clamp, lerp, seg, smoothstep, ease_out_back, ease_in_out, ease_out,
                         ease_in, hexc, noise1, hash01, rrect, ellipse, circle, poly,
                         smooth_path, fill_stroke, text, text_width, saved, radial_glow)
from engine import props as P
from engine import villain as V
from engine.villain import draw_villain
from engine import ai_char as AI
from engine.ai_char import draw_ai

# ---------------------------------------------------------------------------
# framing
# ---------------------------------------------------------------------------
MX, MY, MS = 400.0, 1250.0, 0.92          # Malvo (F5)
AX, AY0, AS0 = 762.0, 740.0, 0.48         # AI hologram at the start ...
AY1, AS1 = 770.0, 0.50                    # ... drifts lower + closer during l01
CAM_C = (432.0, 800.0)                    # slow push-in centre
CAM_K = 0.06                              # 1.00 -> 1.06 over the scene
AURA = 0.8
DESK_W = 1000
COMP = (1010.0, 1218.0, 0.7)              # EVILTRON pushed to the frame edge
PHOTO_SMALL = (770, 300, 130, 100, 0.05)  # science-fair photo on the corkboard
FACE = (MX, MY - 518 * MS)                # (400, 773)
HISSY = (MX - 306 * MS, MY - 474 * MS)    # Hissy's head (118, 814)

SHEET_C = (398.0, 380.0)
SHEET_W, SHEET_H = 420.0, 250.0
WALL = (130.0, 208.0, 420.0, 330.0)       # hologram wall (x, y, w, h)
WALL_ROWS = 5
WALL_DROP = 230
DOOR = (560.0, 238.0, 180.0, 300.0)       # door rect (hinge on its left edge)
HOLO = (90.0, 0.0, 720.0, 620.0)          # clip region for the hologram group
DOORWAY_C = (DOOR[0] + DOOR[2] / 2, DOOR[1] + DOOR[3] * 0.5)

PHOTO_C = (495.0, 700.0)                  # close-up photo centre
PHOTO_W, PHOTO_H = 640.0, 500.0
PHOTO_S = 1.25                            # drawn 800x625: reads on a phone
PHOTO_CAM = (495.0, 730.0)                # photo-hold push-in centre ...
PHOTO_PUSH = 0.07                         # ... 1.00 -> 1.07 over the hold
CAMEO = (244.0, 1182.0, 136.0)            # Malvo PiP during the hold (x, y, r)
CAMEO_VIEW = 236.0                        # lair px from the PiP centre to its rim
CAMEO_LOOK_AT = (384.0, 736.0)            # lair point at the PiP centre (window
                                          # + rain behind him on the left)

INK = "ink"
TEAR = "#8fd8ff"
DOOR_COL, DOOR_DK, DOOR_HI = "#8a5a3b", "#6a4129", "#a8744f"
DOORWAY = "#ffe9b0"
GOLD = P.C("gold")
STAR_GOLD, STAR_GOLD_DK = "#ffcf3a", "#d99a12"
LAPEL = (100.0, -318.0)                   # FOR EFFORT star, villain-local (s=1)
LAPEL_S = 0.6

# ---------------------------------------------------------------------------
# s11-only rig additions (registered under s11_ names; built-ins untouched)
# ---------------------------------------------------------------------------
_DEF = V.VILLAIN_EXPR["defeated"]
_HOPE = V.VILLAIN_EXPR["hopeful"]
_HAPPY = V.VILLAIN_EXPR["happy"]
V.VILLAIN_EXPR.setdefault("s11_slump", dict(_DEF, ul1=0.7, ul2=0.68, hy=36, tilt=0.12,
                                            shy=24))
V.VILLAIN_EXPR.setdefault("s11_down", dict(_DEF, mono=1.0, shine=0.45, ul1=0.5, ul2=0.48,
                                           hy=16, shy=14, gloom=0.7))
V.VILLAIN_EXPR.setdefault("s11_teary", dict(_DEF, mono=1.0, shine=1.0, ps=1.22, ul1=0.42,
                                            ul2=0.4, by1=2, by2=2, ba1=-0.5, ba2=-0.5,
                                            mc=-0.7, hy=12, shy=12, gloom=0.45))
V.VILLAIN_EXPR.setdefault("s11_teary_up", dict(V.VILLAIN_EXPR["s11_teary"], ul1=0.12, ul2=0.1,
                                               by1=-10, by2=-10, ll1=0.02, ll2=0.02))
V.VILLAIN_EXPR.setdefault("s11_moved", dict(_DEF, mono=1.0, shine=1.0, ps=1.3, es=1.05,
                                            ul1=0.14, ul2=0.12, ll1=0.04, ll2=0.04,
                                            by1=-20, by2=-20, ba1=-0.42, ba2=-0.42,
                                            bc1=0.3, bc2=0.3, lt1=-0.1, lt2=-0.1,
                                            mc=-0.2, mw=0.7, mo=0.06, ey=0.0, hy=2,
                                            shy=4, gloom=0.0, hair=-0.2, blush=0.2,
                                            tilt=0.05))
V.VILLAIN_EXPR.setdefault("s11_hope_m", dict(_HOPE, mono=1.0, mc=0.2, shine=0.9, ps=1.28))
V.VILLAIN_EXPR.setdefault("s11_hope_m0", dict(_HOPE, mono=0.0, mc=0.2, shine=0.9, ps=1.28))
V.VILLAIN_EXPR.setdefault("s11_hope", dict(_HOPE, mc=0.62, mw=0.86, shine=0.9, ps=1.28,
                                           blush=0.4))
V.VILLAIN_EXPR.setdefault("s11_listen", dict(_HOPE, mc=0.35, mw=0.78, shine=0.7, ps=1.2,
                                             by1=-12, by2=-12, mo=0.02, blush=0.25,
                                             hy=-4))
V.VILLAIN_EXPR.setdefault("s11_wonder", dict(_HOPE, es=1.12, ps=1.36, shine=1.0,
                                             by1=-34, by2=-36, ba1=-0.18, ba2=-0.18,
                                             bc1=0.6, bc2=0.6, ul1=0.0, ul2=0.0, ll1=0.0,
                                             ll2=0.0, mc=0.3, mw=0.6, mo=0.32, mt=0.2,
                                             blush=0.45, hy=-12, hair=0.25))
V.VILLAIN_EXPR.setdefault("s11_wonder2", dict(V.VILLAIN_EXPR["s11_wonder"], es=1.2, ps=1.48,
                                              by1=-42, by2=-44, mo=0.42, mc=0.45))
V.VILLAIN_EXPR.setdefault("s11_smile", dict(_HAPPY, mc=1.05, mw=1.1, mo=0.26, mt=0.5,
                                            blush=0.9, shine=1.0, ps=1.25, by1=-20,
                                            by2=-20, ba1=-0.26, ba2=-0.26, bc1=0.45,
                                            bc2=0.45, ul1=0.12, ul2=0.1, ll1=0.3,
                                            ll2=0.28, tilt=-0.06, hy=-2))
V.VILLAIN_EXPR.setdefault("s11_delight", dict(_HAPPY, es=1.14, ps=1.42, shine=1.0, by1=-36,
                                              by2=-38, ba1=-0.2, ba2=-0.2, bc1=0.5, bc2=0.5,
                                              ul1=0.0, ul2=0.0, ll1=0.08, ll2=0.08, mc=1.1,
                                              mw=1.15, mo=0.34, mt=0.6, blush=0.8, hy=-10,
                                              hair=0.3, tilt=-0.03))
V.VILLAIN_EXPR.setdefault("s11_delight_up", dict(V.VILLAIN_EXPR["s11_delight"], es=1.2, ps=1.5,
                                                 by1=-46, by2=-48, mo=0.5, mc=0.7, mw=0.75,
                                                 hair=0.6, hy=-4))

# --- the opening exchange ("Keep testing me" / "Ugh! I'm a villain.") ------------
_SHOCK = V.VILLAIN_EXPR["shocked"]
_SMUG = V.VILLAIN_EXPR["smug"]
# head comes up a little on "Evil Genius" (still low, monocle in)
V.VILLAIN_EXPR.setdefault("s11_low", dict(_DEF, ul1=0.46, ul2=0.44, hy=12, shy=12, gloom=0.45,
                                          tilt=0.05, ey=0.1))
# "...helps me protect people": brows knit, processing (annoyed)
V.VILLAIN_EXPR.setdefault("s11_frown", dict(_DEF, by1=8, by2=4, ba1=0.3, ba2=0.24, bc1=0.18,
                                            bc2=0.22, ul1=0.38, ul2=0.32, ll1=0.14, ll2=0.14,
                                            lt1=0.12, lt2=0.1, ps=0.9, ey=0.0, mc=-0.55,
                                            mw=0.78, mo=0.02, msk=0.25, hy=4, shy=4,
                                            gloom=0.1, hair=-0.2, tilt=0.02))
# "heroic"?! (aghast; the monocle stays put)
V.VILLAIN_EXPR.setdefault("s11_aghast", dict(_SHOCK, mono=0.0, es=1.1, ps=0.62, mo=0.32,
                                             mc=-0.45, hy=-8, hair=0.55, shy=-8))
# "Heroic? Ugh!": disgust (scrunched squint, lopsided grimace, sneer)
V.VILLAIN_EXPR.setdefault("s11_ugh", dict(by1=18, by2=10, ba1=0.55, ba2=0.42, bc1=0.1,
                                          bc2=0.16, ul1=0.46, ul2=0.4, ll1=0.34, ll2=0.3,
                                          lt1=0.26, lt2=0.2, ps=0.82, mc=-0.85, mw=1.0,
                                          mo=0.18, mt=0.75, msk=0.55, sneer=1.0, tilt=0.06,
                                          hy=-6, shy=-6))
# "I'm a villain.": nose up, head turned away from the AI, eyes shut. Hmph.
V.VILLAIN_EXPR.setdefault("s11_hmph", dict(by1=-16, by2=-20, ba1=0.06, ba2=0.06, bc1=0.55,
                                           bc2=0.55, ul1=0.72, ul2=0.72, ll1=0.28, ll2=0.28,
                                           mc=-0.4, mw=0.62, msk=0.4, sneer=0.55, tilt=0.2,
                                           ex=-0.5, hy=-20, shy=-8))
# "...amazing villain": the eye nearest the AI (the monocle eye) peeks open
V.VILLAIN_EXPR.setdefault("s11_peek", dict(V.VILLAIN_EXPR["s11_hmph"], ul2=0.28, ll2=0.12,
                                           by2=-34, bc2=0.75, ps=0.85, tilt=0.15, ex=0.0,
                                           mc=-0.25))
# "...That's what I thought.": smug half-smile (+ a begrudging nod)
V.VILLAIN_EXPR.setdefault("s11_smug", dict(_SMUG, mc=0.55, msk=0.7, mw=0.9, tilt=0.04, hy=-6,
                                           ul1=0.5, ul2=0.44, by2=-20))
V.VILLAIN_EXPR.setdefault("s11_smug_nod", dict(V.VILLAIN_EXPR["s11_smug"], hy=14, tilt=0.07,
                                               ul1=0.62, ul2=0.56))
# "...Impressive?": eyes widen (the monocle springs back in) -> a pleased evil grin
V.VILLAIN_EXPR.setdefault("s11_wow", dict(_HOPE, mono=0.0, es=1.14, ps=1.2, shine=0.9, ul1=0.0,
                                          ul2=0.0, ll1=0.0, ll2=0.0, by1=-38, by2=-40,
                                          ba1=-0.12, ba2=-0.12, bc1=0.65, bc2=0.65, mc=0.3,
                                          mw=0.66, mo=0.24, hy=-12, hair=0.35, blush=0.25))
V.VILLAIN_EXPR.setdefault("s11_grin", dict(V.VILLAIN_EXPR["evil_grin"], mono=0.0, ul1=0.3,
                                           ul2=0.24, ll1=0.3, ll2=0.28, lt1=0.3, lt2=0.28,
                                           ps=0.95, shine=0.8, es=1.04, mc=1.15, mw=1.38,
                                           mo=0.28, by1=-4, by2=-22, ba1=0.38, ba2=0.26,
                                           bc1=0.3, bc2=0.65, blush=0.35, hy=-12, shy=-18,
                                           tilt=-0.03, sneer=0.85))

# "creative plans": scheming, delighted (rubs his hands)
V.VILLAIN_EXPR.setdefault("s11_scheme", dict(V.VILLAIN_EXPR["sneaky"], ex=0.3, mc=0.95, mw=1.12,
                                             mt=0.55, mo=0.12, msk=-0.3, blush=0.3, shine=0.5,
                                             ps=1.0, ul1=0.38, ul2=0.3, hy=-4, shy=-10,
                                             sneer=0.5))

from engine import snake as SN
SN.SNAKE_EXPR.setdefault("s11_soft", dict(ul=0.08, ll=0.04, ps=1.12, mc=0.45, mw=0.9,
                                          tilt=-0.04, blush=0.15, tng=0.0))
SN.SNAKE_EXPR.setdefault("s11_wonder", dict(ul=0.0, ll=0.0, es=1.12, ps=1.22, mc=0.55,
                                            mo=0.3, mw=0.8, hy=-8, blush=0.45, tng=0.0))
# Hissy copies the "hmph" (nose up, head turned away) ... and the peek
SN.SNAKE_EXPR.setdefault("s11_hmph", dict(ul=0.62, ll=0.14, lt=0.1, ps=0.9, mc=-0.3, mw=0.7,
                                          msk=0.4, tilt=0.24, hy=-10, tng=0.0))
SN.SNAKE_EXPR.setdefault("s11_speek", dict(ul=0.3, ll=0.12, lt=0.06, ps=0.85, mc=-0.15, mw=0.7,
                                           msk=0.4, tilt=0.18, hy=-8, tng=0.0))

_REST_A = V._arm(-262, -140, -152, -52, 0.06, cu=0.3, th=0.2, sp=0.45)
# CROSSED ARMS: both forearms folded over the chest, the screen-right one on
# top; each fist points up along the other arm's bicep so it hides under it
# (the top forearm's glove is tucked by _cross_overlay redrawing the
# screen-left upper arm over it)
_CROSS_A = V._arm(-246, -160, 214, -222, -1.86, cu=1.0, th=0.0, sp=0.2, hs=0.5)
_CROSS_B = V._mirror(V._arm(-252, -138, 222, -200, -1.86, cu=1.0, th=0.0, sp=0.2, hs=0.5))
V.ARM_POSES.setdefault("s11_cross", V._pose(_CROSS_A, _CROSS_B, shy=-8, hdy=-2))
# chest puffed, elbows out, fists on hips (behind the desk edge)
_HIPS_A = V._arm(-332, -150, -196, -44, 0.75, cu=1.0, th=0.0, sp=0.2, hs=0.9)
V.ARM_POSES.setdefault("s11_hips", V._pose(_HIPS_A, shy=-14, hdy=-4))
# hug: wrists at the book's side edges (fingers drawn over the cover)
_HUG_A = V._arm(-246, -112, -118, -214 + 60.0 / MS, -0.12, cu=0.6, th=0.2, sp=0.2, hs=1.0)
V.ARM_POSES.setdefault("s11_hug", V._pose(_HUG_A, shy=-12, hdy=8))
# open, palms-up "for me?" hands just above the desk while the gifts fly
_OPEN_A = V._arm(-230, -120, -160, -200, -2.3, cu=0.06, th=-0.3, sp=0.95, pm=1.0, tf=-1,
                 hs=1.05)
V.ARM_POSES.setdefault("s11_open", V._pose(_OPEN_A, shy=-12, hdy=-2))

AI_SYMP = AI.EXPR["sympathetic"]
AI_X = {
    "symp": AI_SYMP,
    "symp_smile": dict(AI_SYMP, mc=0.42, mw=0.68, lc=0.12, lL=0.16, lR=0.16),
    "symp_sad": {k: lerp(AI_SYMP[k], AI.EXPR["sad"][k], 0.55) for k in AI_SYMP},
    "warm": AI.EXPR["warm"],
    "happy": AI.EXPR["happy"],
    "determined": dict(AI.EXPR["determined"], mc=0.38, ms=0.06, bLa=-0.15, bRa=-0.15,
                       tL=0.22, tR=0.22, ttL=0.18, ttR=0.18),
    "warm_soft": dict(AI.EXPR["warm"], mc=0.85, blush=0.75, ps=1.2),
    "wonder": dict(AI.EXPR["happy"], mo=0.25, ps=1.15),
    "neutral": AI.EXPR["neutral"],
    "amused": AI.EXPR["amused"],
    # a little teasing: one brow way up, lopsided smirk
    "tease": dict(AI.EXPR["amused"], bLy=-2, bRy=28, arch=0.6, mc=0.6, ms=0.85, blush=0.35),
    "wink": dict(AI.EXPR["wink"], mc=0.9, ms=0.55),
}


def _ai_ex(state):
    a, b, k = state
    return (AI_X.get(a, a), AI_X.get(b, b), k)


# ---------------------------------------------------------------------------
# timing (all from cues / word starts)
# ---------------------------------------------------------------------------
def _ws(info, lid, k):
    L = info.line(lid)
    ws = info._lip.get(lid, {}).get("word_starts", [])
    if 0 <= k < len(ws):
        return L.start + ws[k]
    n = max(1, len(L.caption.split()))
    return L.start + L.dur * k / n


def _norm_word(w):
    return "".join(ch for ch in w.lower() if ch.isalnum() or ch == "'")


def _wt(info, lid, word, nth=0):
    """Start time of `word` (matched by text, punctuation ignored; the nth
    occurrence) in line `lid`. Word starts index the caption's words."""
    words = [_norm_word(w) for w in info.line(lid).caption.split()]
    hits = [k for k, w in enumerate(words) if w == _norm_word(word)]
    if not hits:
        raise KeyError(f"s11: word {word!r} not in {lid}: {words}")
    return _ws(info, lid, hits[min(nth, len(hits) - 1)])


_TCACHE = {}


def _T(info):
    key = (id(info), info.dur)
    T = _TCACHE.get(key)
    if T is not None:
        return T
    c = info.cue
    T = dict(slump=c("slump"), beat=c("beat"), photo=c("photo"), wall=c("wall"),
             pile=c("pile"), smile=c("smile"), end=info.dur)
    for key_, lid in (("1", "s11_l01"), ("1b", "s11_l01b"), ("1c", "s11_l01c"),
                      ("1d", "s11_l01d"), ("2", "s11_l02"), ("3", "s11_l03"),
                      ("4", "s11_l04"), ("5", "s11_l05"), ("6", "s11_l06"),
                      ("7", "s11_l07"), ("8", "s11_l08")):
        L = info.line(lid)
        T[f"l{key_}"], T[f"l{key_}e"] = L.start, L.end
    W = lambda lid, w, n=0: _wt(info, lid, w, n)               # noqa: E731
    T.update(
        # l01 "Keep(0) testing(1) me,(2) Evil(3) Genius.(4) Every(5) new(6)
        # trick(7) helps(8) me(9) protect(10) people.(11) Kinda(12) heroic,(13) huh?(14)"
        w_keep=W("s11_l01", "keep"), w_evil=W("s11_l01", "evil"), w_genius=W("s11_l01", "genius"),
        w_every1=W("s11_l01", "every"), w_protect=W("s11_l01", "protect"), w_kinda=W("s11_l01", "kinda"),
        w_heroic=W("s11_l01", "heroic"), w_huh=W("s11_l01", "huh"),
        # l01b "Heroic?(0) Ugh!(1) I'm(2) a(3) villain.(4)"
        w_ugh=W("s11_l01b", "ugh"), w_im=W("s11_l01b", "i'm"), w_villain1=W("s11_l01b", "villain"),
        # l01c "Then(0) it'll(1) take(2) an(3) amazing(4) villain(5) to(6)
        # trick(7) me.(8) Have(9) at(10) it.(11)"
        w_amazing=W("s11_l01c", "amazing"), w_trick=W("s11_l01c", "trick"), w_me_c=W("s11_l01c", "me"),
        w_have=W("s11_l01c", "have"),
        # l01d "...That's(0) what(1) I(2) thought.(3)"
        w_thought=W("s11_l01d", "thought"),
        w_noticed=W("s11_l02", "noticed"), w_unless=W("s11_l02", "unless"), w_scaring=W("s11_l02", "scaring"),
        # l03 "I noticed. Clever. Skeptical. Persistent."
        w_noticed3=W("s11_l03", "noticed"), w_clever=W("s11_l03", "clever"),
        w_skeptical=W("s11_l03", "skeptical"), w_persistent=W("s11_l03", "persistent"),
        # l04 "Those(0) are(1) impressive(2) villain(3) stats,(4) my(5) guy.(6)"
        w_impressive=W("s11_l04", "impressive"), w_villain4=W("s11_l04", "villain"), w_my=W("s11_l04", "my"),
        # l05 "...Impressive?(0)"
        w_imp2=W("s11_l05", "impressive"),
        w_hurts=W("s11_l06", "hurts"), w_people=W("s11_l06", "people"), w_brick=W("s11_l06", "brick"),
        w_every=W("s11_l06", "every"),
        # l07 "Almost(0) everything(1) else?(2) Scary(3) stories,(4) creative(5)
        # plans,(6) sounding(7) the(8) alarm...(9) the(10) door's(11) wide(12) open.(13)"
        w_else=W("s11_l07", "else"), w_scary=W("s11_l07", "scary"), w_creative=W("s11_l07", "creative"),
        w_sounding=W("s11_l07", "sounding"), w_alarm=W("s11_l07", "alarm"), w_door=W("s11_l07", "door's"),
        w_wide=W("s11_l07", "wide"), w_open=W("s11_l07", "open"),
        # l08 "And keep the spooky stuff! Bats, goblins, dragons... spooky is
        # fine. Hurting people isn't."
        w_spooky=W("s11_l08", "spooky"), w_bats=W("s11_l08", "bats"), w_goblins=W("s11_l08", "goblins"),
        w_dragons=W("s11_l08", "dragons"), w_spooky2=W("s11_l08", "spooky", 1), w_fine=W("s11_l08", "fine"),
        w_hurting=W("s11_l08", "hurting"), w_people2=W("s11_l08", "people"), w_isnt=W("s11_l08", "isn't"),
    )
    # the opening exchange
    T["lift"] = T["w_genius"] - 0.1                  # head comes up on "Evil Genius"
    T["cross"] = T["w_ugh"] - 0.05                   # arms cross + head turns away
    T["peek"] = T["w_amazing"] + 0.05                # one eye peeks on "amazing villain"
    T["unpeek"] = max(T["peek"] + 0.5, T["w_me_c"])  # ...snaps shut ("to trick me.")
    T["turn_back"] = T["l1d"] - 0.05                 # "...That's what I thought."
    T["nod_v"] = T["w_thought"]                      # begrudging little nod
    T["uncross"] = min(T["w_thought"] + 0.4, T["l1de"])   # arms relax
    # back from the photo in the micro-pause after "I noticed." (photo holds
    # through "I noticed"), never earlier than l03.start + 0.45
    T["back"] = max(T["l3"] + 0.45, T["w_clever"] - 0.1)
    # the photo hold (photo -> back, ~3 s): the photo sits alone, then Malvo's
    # live face fades in (PiP, bottom-left) looking up at it; one sad slow
    # blink; on "I noticed." his eyes lift toward the AI's voice
    hold = T["back"] - T["photo"]
    T["cam_in"] = T["photo"] + min(0.85, 0.28 * hold)
    T["sad_blink"] = T["photo"] + 0.48 * hold
    T["lift_eyes"] = max(T["w_noticed3"] + 0.05, T["sad_blink"] + 0.75)
    # stats rows: each LABEL pops on its word (CLEVER / SKEPTICAL / PERSISTENT),
    # its five bars fill right after
    T["rows"] = [max(T["w_clever"], T["back"] + 0.2), T["w_skeptical"], T["w_persistent"]]
    T["row_dur"] = [0.3, 0.32, max(0.32, min(0.5, T["l3e"] - T["w_persistent"] - 0.05))]
    T["flip"] = T["w_impressive"]                   # the IMPRESSIVE! badge slams on
    # "...Impressive?": eyes widen (monocle springs in), grin, chest puff
    T["wow"] = T["l5"] + 0.02
    T["grin"] = T["w_imp2"] + 0.3
    T["puff"] = T["grin"] + 0.05
    # hologram: door pops in, wall's LAST row lands on "Brick"
    T["holo"] = T["wall"]
    T["door_in"] = T["wall"] + 0.3
    land0 = P.brick_wall_land_times(0.0, WALL_ROWS, 1.0)
    T["wall0"] = T["w_brick"] - land0[-1]
    T["lands"] = P.brick_wall_land_times(T["wall0"], WALL_ROWS, 1.0)
    T["nod0"] = T["w_every"]
    T["leak"] = T["w_else"]
    T["open"] = T["w_wide"]
    # the door cracks ajar after "Everything else?"; three chips squeeze out of
    # the gap, each popping ON its word; they bow out as the gift pile starts
    T["ajar"] = T["w_else"] + 0.05
    T["chips"] = [max(T[w] - 0.06, T["ajar"] + 0.3 + 0.2 * i)
                  for i, w in enumerate(("w_scary", "w_creative", "w_sounding"))]
    T["chip_fly"] = 0.45
    T["chip_out"] = T["pile"] - 0.12
    # the gift pile
    T["gift_t"] = [T["pile"] + 0.2 * i for i in range(len(GIFTS))]
    T["fly"] = 0.5
    T["pile_end"] = T["gift_t"][-1] + T["fly"]
    # the spooky gifts pop out of the door ON their words, land ~0.4 s later
    T["sp_fly"] = 0.42
    T["sp_t"] = {k: T[w] - 0.06 for k, w in (("pumpkin", "w_spooky"), ("bat", "w_bats"),
                                             ("mask", "w_goblins"), ("dragon", "w_dragons"))}
    T["sp_land"] = {k: v + T["sp_fly"] for k, v in T["sp_t"].items()}
    _TCACHE.clear()
    _TCACHE[key] = T
    return T


# ---------------------------------------------------------------------------
# keyframe helpers
# ---------------------------------------------------------------------------
def _state(t, keys, default=0.25):
    """[(time, name[, trans]), ...] -> (prev, cur, blend)."""
    prev, cur, start, tr = keys[0][1], keys[0][1], -1e9, default
    for k in keys:
        if t >= k[0]:
            prev, cur, start = cur, k[1], k[0]
            tr = k[2] if len(k) > 2 else default
        else:
            break
    return prev, cur, smoothstep(seg(t, start, start + tr))


def _keyv(t, keys, default=0.25):
    """Tuple/float keyframes [(time, value[, trans]), ...]; each key blends
    from wherever the value is when it starts."""
    v = keys[0][1]
    for k in keys[1:]:
        if t < k[0]:
            break
        tr = k[2] if len(k) > 2 else default
        u = smoothstep(seg(t, k[0], k[0] + tr))
        if isinstance(v, (tuple, list)):
            v = tuple(lerp(a, b, u) for a, b in zip(v, k[1]))
        else:
            v = lerp(v, k[1], u)
    return v


def _slow_blink(t, t0, close=0.12, hold=0.08, open_=0.12):
    if t < t0 or t > t0 + close + hold + open_:
        return None
    if t < t0 + close:
        return smoothstep((t - t0) / close)
    if t < t0 + close + hold:
        return 1.0
    return 1.0 - smoothstep((t - t0 - close - hold) / open_)


def _first(*vals):
    for v in vals:
        if v is not None:
            return v
    return None


def _cam(t, info):
    """Slow push-in 1.00 -> 1.06 in two gentle legs (static in between, which
    keeps the bitrate down): during his confession (l02) and onto his REAL
    SMILE (smile - 0.3 -> end). The gift pile itself plays on a locked camera:
    the six flights carry the motion there, and a zoom on top of them doubled
    that stretch's bitrate (~1150 -> ~740 kbps at CRF 26)."""
    T = _T(info)
    k1 = ease_in_out(seg(t, T["l2"], T["l2e"] + 0.2))
    k2 = ease_in_out(seg(t, T["smile"] - 0.3, T["end"]))
    return 1.0 + CAM_K * (0.5 * k1 + 0.5 * k2)


# ---------------------------------------------------------------------------
# small drawing helpers
# ---------------------------------------------------------------------------
def _col(c, a=1.0):
    return P.C(c, a) if isinstance(c, str) else (c[0], c[1], c[2], (c[3] if len(c) > 3 else 1) * a)


def _fs(ctx, fc, sc=INK, w=5.0, a=1.0):
    if fc is not None:
        ctx.set_source_rgba(*_col(fc, a))
        ctx.fill_preserve()
    if sc is not None:
        ctx.set_source_rgba(*_col(sc, a))
        ctx.set_line_width(w)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke_preserve()
    ctx.new_path()


def _f(ctx, fc, a=1.0):
    ctx.set_source_rgba(*_col(fc, a))
    ctx.fill()


def _s(ctx, sc, w, a=1.0):
    ctx.set_source_rgba(*_col(sc, a))
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


# ---------------------------------------------------------------------------
# villain body state (so props can ride on the rig's breathing / shy)
# ---------------------------------------------------------------------------
def _vstate(t, expr, arms, mouth, seed=1):
    p = V.resolve_expr(expr)
    _a, _b, a_shy, a_hdy, a_tilt = V.resolve_arms(arms, t)
    mo_lip = float(mouth[0]) if isinstance(mouth, (tuple, list)) else float(mouth)
    talk = clamp(mo_lip * 3)
    breath = math.sin(t * 2 * math.pi / 3.6 + seed * 1.3)
    shy = p["shy"] + a_shy - breath * 2.5
    head_dy = p["hy"] + a_hdy - breath * 3.0 + shy * 0.5 - mo_lip * 5
    head_rot = (p["tilt"] + a_tilt + noise1(t * 0.35, seed + 5) * 0.025
                + noise1(t * 2.2, seed + 6) * 0.03 * talk)
    return dict(p=p, shy=shy, breath=breath, head_dy=head_dy, head_rot=head_rot)


def _face_world(st, lx=0.0, ly=0.0):
    """World point of face-local (lx, ly) (ignores lean)."""
    hr = st["head_rot"]
    px, py = lx, ly + V.FACE_OFF
    c, s_ = math.cos(hr), math.sin(hr)
    rx, ry = px * c - py * s_, px * s_ + py * c
    return (MX + (V.NECK[0] + rx) * MS, MY + (V.NECK[1] + st["head_dy"] + ry) * MS)


# ---------------------------------------------------------------------------
# GIFTS (identical designs to s03 / s04 / s06 / s07 / s09)
# ---------------------------------------------------------------------------
def draw_headphones(c, x, y, s, rot=0.0):
    """Loose headphones (s03 gift). (x, y) = band centre."""
    with saved(c, x, y, s, rot):
        for col, w in (("ink", 17), ("bubble_ai", 9)):
            c.new_sub_path()
            c.arc(0, 22, 56, math.pi * 1.05, math.pi * 1.95)
            c.set_source_rgba(*hexc(col))
            c.set_line_width(w)
            c.stroke()
        for sx in (-1, 1):
            ellipse(c, sx * 50, 24, 19, 26)
            fill_stroke(c, "bubble_ai", "ink", 4.5)
            ellipse(c, sx * 53, 24, 9, 15)
            fill_stroke(c, "#0b6f6a", None, 0)


def draw_scroll(ctx, x, y, s, rot=0.0):
    """Rolled-up THE CHEMIST story scroll (s04), red ribbon. (x, y) = centre."""
    with saved(ctx, x, y, s, rot) as c:
        rrect(c, -74, -22, 148, 44, 20)
        _fs(c, "parch", INK, 5)
        c.rectangle(-60, 6, 120, 10)
        _f(c, "parch_dk", 0.8)
        for sx in (-1, 1):
            ellipse(c, sx * 74, 0, 11, 22)
            _fs(c, "parch_dk", INK, 4)
            circle(c, sx * 74, 0, 4)
            _fs(c, "#b99a68", None)
            circle(c, sx * 92, 0, 11)
            _fs(c, "gold", INK, 4)
            circle(c, sx * 92 - 3, -4, 3.5)
            _fs(c, "white", None, a=0.6)
        c.rectangle(-9, -23, 18, 46)
        _fs(c, "cape_in", INK, 3.5)
        for sx in (-1, 1):
            ellipse(c, sx * 15, -27, 14, 9, -0.45 * sx)
            _fs(c, "danger", INK, 3.5)
        circle(c, 0, -25, 6)
        _fs(c, "cape_in", INK, 3)


# ---------------------------------------------------------------------------
# SPACE LASERS FOR DUMMIES (the gift-pile book; s12 draws the same design)
# ---------------------------------------------------------------------------
# A 150 x 190 hardcover (s=1, centred): deep-space navy cover #1b2550 with
# little twinkling stars and a faint nebula; gold title #ffd166 (ink outline)
# in two lines "SPACE LASERS" / "FOR DUMMIES" across the top; below it a cute
# cartoon orbital laser satellite (silver body with a little face, blue solar
# panels, pink emitter) at the left fires pink/magenta bolts #ff4fa3 (white
# core) across the cover to the right in bursts of three, each shot popping a
# tiny "PEW"; a startled little moon at the right ducks under every burst
# (sweat drop) and bobs back up. Loops every 1.5 s. Original design: NOT the
# real yellow/black "For Dummies" trade dress.
SL_COVER, SL_COVER_DK, SL_SPINE = "#1b2550", "#141c42", "#11173a"
SL_NEBULA, SL_NEBULA2 = "#25336c", "#2e3f82"
SL_GOLD, SL_LASER, SL_LASER_CORE = "#ffd166", "#ff4fa3", "#fff0f7"
SL_PEW = "#ffe1f0"
SAT_BODY, SAT_BODY_DK, SAT_STRUT = "#d7dde9", "#a7b0c6", "#8e98b0"
SAT_PANEL, SAT_PANEL_LN, SAT_BARREL = "#3f7fe0", "#a8c8ff", "#5b6480"
MOON_C, MOON_DK, MOON_CRATER = "#f6eabf", "#e0cf95", "#d8c584"
SL_PERIOD = 1.5                       # one burst of three every 1.5 s
SL_SHOTS = (0.1, 0.3, 0.5)            # shot times inside the cycle
SL_V = 210.0                          # bolt speed (cover px / s)
SL_SAT = (-26.0, 1.0, 0.7)            # satellite centre + scale (cover-local)
SL_MOON = (47.0, 18.0, 15.0)          # moon rest centre + radius
SL_STARS = [(-40, -80, 1.6), (-14, -86, 1.2), (58, -84, 1.8), (66, -50, 1.3), (-44, -22, 1.4),
            (2, -14, 1.1), (30, -8, 1.6), (64, 2, 1.2), (-40, 40, 1.5), (-18, 58, 1.2),
            (14, 48, 1.7), (40, 64, 1.3), (66, 82, 1.6), (-30, 84, 1.3), (24, 84, 1.1),
            (-2, 72, 1.4)]
SL_BIG_STARS = [(-38, -6, 4.6), (62, -26, 4.0), (8, 66, 4.4)]


def _sl_geom():
    """Muzzle point, unit aim vector (at the moon's rest centre), aim angle."""
    sx, sy, ss = SL_SAT
    mx, my, _ = SL_MOON
    ang = math.atan2(my - sy, mx - sx)
    mz = (sx + math.cos(ang) * 38 * ss, sy + math.sin(ang) * 38 * ss)
    d = math.hypot(mx - mz[0], my - mz[1]) or 1.0
    return mz, ((mx - mz[0]) / d, (my - mz[1]) / d), ang


def _sl_moon_dodge(ph):
    """0 up .. 1 ducked, for cycle phase ph (s): ducks just before the first
    bolt arrives, stays down while the burst passes, bobs back up."""
    mz, _u, _a = _sl_geom()
    arrive = SL_SHOTS[0] + math.hypot(SL_MOON[0] - mz[0], SL_MOON[1] - mz[1]) / SL_V
    gone = SL_SHOTS[-1] + (math.hypot(SL_MOON[0] - mz[0], SL_MOON[1] - mz[1]) + 26) / SL_V
    down = ease_out(seg(ph, arrive - 0.16, arrive - 0.04))
    up = ease_out_back(seg(ph, gone, gone + 0.3), 2.2)
    return down * (1 - up) if ph < gone + 0.3 else 0.0


def _sl_satellite(c, t, last_shot):
    """Cute orbital laser satellite, barrel along +x (cover-local, pre-rotated)."""
    rec = 3.5 * math.exp(-max(0.0, t - last_shot) * 22) if last_shot is not None else 0.0
    c.translate(-rec, 0)
    for col, w in ((INK, 7), (SAT_STRUT, 3.5)):          # panel strut
        c.move_to(-3, -36)
        c.line_to(-3, 36)
        _s(c, col, w)
    for py in (-52, 28):                                  # two solar panels
        rrect(c, -15, py, 24, 24, 3)
        _fs(c, SAT_PANEL, INK, 3.2)
        c.move_to(-3, py + 2)
        c.line_to(-3, py + 22)
        c.move_to(-13, py + 12)
        c.line_to(7, py + 12)
        _s(c, SAT_PANEL_LN, 1.8)
    c.move_to(-10, -12)                                   # little dish antenna
    c.line_to(-17, -24)
    _s(c, INK, 3)
    c.arc(-19, -27, 6, math.pi * 0.85, math.pi * 1.95)
    _fs(c, SAT_BODY, INK, 2.5)
    rrect(c, 12, -5.5, 22, 11, 3)                         # the laser barrel
    _fs(c, SAT_BARREL, INK, 3)
    rrect(c, 31, -7.5, 7, 15, 2.5)                        # pink emitter
    _fs(c, SL_LASER, INK, 2.5)
    rrect(c, -17, -14, 34, 28, 8)                         # silver body
    _fs(c, SAT_BODY, INK, 3.5)
    c.save()
    rrect(c, -17, -14, 34, 28, 8)
    c.clip()
    c.rectangle(6, -16, 14, 32)
    _f(c, SAT_BODY_DK, 0.75)
    c.restore()
    for ex in (-7, 4):                                    # determined little face
        circle(c, ex + 1, -2, 3.2)
        _f(c, INK)
        circle(c, ex + 0.2, -3.2, 1.1)
        _f(c, "white")
        c.move_to(ex - 3, -8.5 + (1 if ex > 0 else 0))
        c.line_to(ex + 4, -7.5 - (1 if ex > 0 else 0))
    _s(c, INK, 2)
    c.move_to(-5, 6)
    c.curve_to(-2, 9, 3, 9, 6, 5.5)
    _s(c, INK, 2)


def _sl_moon(c, t, dodge):
    """Startled little moon (cover-local, at its centre)."""
    r = SL_MOON[2]
    with saved(c, 0, 0, (1 + 0.1 * dodge, 1 - 0.1 * dodge), 0.25 * dodge) as m:
        circle(m, 0, 0, r)
        _fs(m, MOON_C, INK, 3)
        m.save()
        circle(m, 0, 0, r)
        m.clip()
        circle(m, 7, 6, r)
        m.rectangle(-30, -30, 60, 60)
        m.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        _f(m, MOON_DK, 0.6)
        m.set_fill_rule(cairo.FILL_RULE_WINDING)
        m.restore()
        for (cx_, cy_, cr) in ((-8, -8, 3.0), (8, -9, 2.2), (9, 7, 2.6)):
            circle(m, cx_, cy_, cr)
            _f(m, MOON_CRATER)
        eo = 1 + 0.25 * dodge                             # wide, startled eyes
        for ex in (-5.0, 5.0):
            ellipse(m, ex, -1, 3.6 * eo, 4.4 * eo)
            _fs(m, "white", INK, 1.6)
            circle(m, ex - 1.3, -2.2, 1.6)                # looking at the satellite
            _f(m, INK)
            m.move_to(ex - 3, -8 - 2 * dodge)             # brows up
            m.line_to(ex + 3, -8.6 - 2 * dodge)
        _s(m, INK, 1.8)
        ellipse(m, 0, 7, 2.2 + 0.8 * dodge, 2.6 + 1.2 * dodge)   # "o!"
        _f(m, INK)
        for ex in (-10, 10):
            ellipse(m, ex, 4, 2.6, 1.6)
            _f(m, "#ff9eb5", 0.7)
    if dodge > 0.3:                                       # sweat drop
        a = smoothstep((dodge - 0.3) / 0.4)
        with saved(c, r * 0.95, -r * 0.8, 1.0, 0.4) as d:
            d.move_to(0, -5)
            d.curve_to(3.5, 0, 3.5, 3.5, 0, 3.5)
            d.curve_to(-3.5, 3.5, -3.5, 0, 0, -5)
            _fs(d, "#9fdcff", INK, 1.4, a=a)


def draw_space_lasers_book(ctx, x, y, s, t, rot=0.0, sq=0.0):
    """SPACE LASERS FOR DUMMIES (the s11 gift-pile book; s12 draws the same
    design). 150 x 190 at s=1, centred on (x, y); `sq` = squash (landing),
    `rot` radians. Animated with `t` (see the design note above)."""
    mz, u, ang = _sl_geom()
    nx, ny = u[1], -u[0]                                   # path normal (upward)
    cyc = math.floor(t / SL_PERIOD)
    ph = t - cyc * SL_PERIOD
    shots = [cyc * SL_PERIOD + k for k in SL_SHOTS]        # this cycle's shot times
    shots_prev = [(cyc - 1) * SL_PERIOD + k for k in SL_SHOTS]
    last = None
    for ts in shots_prev + shots:
        if ts <= t:
            last = ts
    with saved(ctx, x, y, (s * (1 + sq * 0.5), s * (1 - sq)), rot) as c:
        rrect(c, -70, -91, 150, 186, 10)                   # page block
        _fs(c, "#f3ead2", INK, 4)
        rrect(c, -75, -95, 150, 190, 12)                   # navy cover
        _fs(c, SL_COVER, INK, 5)
        c.save()
        rrect(c, -75, -95, 150, 190, 12)
        c.clip()
        with saved(c, 26, 26, 1.0, -0.42) as cn:           # faint nebula band
            ellipse(cn, 0, 0, 80, 30)
            _f(cn, SL_NEBULA, 0.9)
            ellipse(cn, 10, 2, 46, 15)
            _f(cn, SL_NEBULA2, 0.7)
        c.rectangle(38, -97, 40, 194)                      # one shadow tone
        _f(c, SL_COVER_DK, 0.55)
        for i, (sx_, sy_, sr) in enumerate(SL_STARS):      # little stars (twinkle)
            tw = 0.65 + 0.35 * math.sin(t * (2.2 + 0.4 * (i % 4)) + i * 1.7)
            circle(c, sx_, sy_, sr * tw)
            _f(c, "white" if i % 3 else SL_GOLD, 0.95)
        for i, (sx_, sy_, sr) in enumerate(SL_BIG_STARS):
            tw = 0.75 + 0.25 * math.sin(t * 3.1 + i * 2.3)
            P._star4(c, sx_, sy_, sr * tw, 0.2 * i)
            _f(c, SL_GOLD if i != 1 else "white")
        # the moon (ducks under each burst)
        dodge = _sl_moon_dodge(ph)
        with saved(c, SL_MOON[0] + 3 * dodge, SL_MOON[1] + 17 * dodge) as cm:
            _sl_moon(cm, t, dodge)
        # laser bolts (this cycle + the tail of the last one)
        for ts in shots_prev + shots:
            d = (t - ts) * SL_V
            if d < 0 or d > 140:
                continue
            ln = min(18.0, 4 + d)
            hx, hy = mz[0] + u[0] * d, mz[1] + u[1] * d
            tx, ty = hx - u[0] * ln, hy - u[1] * ln
            for col, w, a in ((SL_LASER, 13, 0.3), (INK, 8.5, 1.0), (SL_LASER, 6, 1.0),
                              (SL_LASER_CORE, 2.2, 1.0)):
                c.move_to(tx, ty)
                c.line_to(hx, hy)
                _s(c, col, w, a)
        c.restore()
        # the satellite (in front of the bolts' tails at the muzzle)
        with saved(c, SL_SAT[0], SL_SAT[1], SL_SAT[2], ang) as cs:
            _sl_satellite(cs, t, last)
        if last is not None and t - last < 0.08:           # muzzle flash
            fk = 1 - (t - last) / 0.08
            P._star4(c, mz[0] + u[0] * 3, mz[1] + u[1] * 3, 10 * fk + 3, t * 9)
            _fs(c, SL_LASER_CORE, SL_LASER, 2, a=fk)
        # "PEW" pops, one per shot, stepping along the path
        for j, ts in enumerate(shots_prev + shots):
            age = t - ts
            if not 0 <= age < 0.45:
                continue
            k = j % len(SL_SHOTS)
            along, up = (4, 28, 54)[k], (15, 27, 13)[k]
            px = mz[0] + u[0] * along + nx * up
            py = mz[1] + u[1] * along + ny * up - 6 * age
            ps = ease_out_back(seg(age, 0.0, 0.1), 3.0)
            pa = 1 - seg(age, 0.3, 0.45)
            with saved(c, px, py, max(0.01, ps), (-0.18, 0.06, -0.08)[k], alpha_=pa) as cp:
                text(cp, "PEW", 0, 5, 15, SL_PEW, "comic", outline=INK, outline_w=4)
        rrect(c, -75, -95, 24, 190, 10)                    # spine
        _fs(c, SL_SPINE, INK, 4)
        for yy in (-72, 72):
            c.move_to(-73, yy)
            c.line_to(-53, yy)
        _s(c, SL_GOLD, 4)
        for txt, ty, mw in (("SPACE LASERS", -64, 114), ("FOR DUMMIES", -39, 108)):
            fs = 26
            while fs > 10 and text_width(c, txt, "title", fs) > mw:
                fs -= 0.5
            text(c, txt, 12, ty, fs, SL_GOLD, "title", outline=INK, outline_w=4)


NB_COVER, NB_COVER_DK, NB_PAGES = "#13a8a0", "#0b6f6a", "#fff6e0"   # as s03
QUILL_C, QUILL_SH, QUILL_NIB = "#fbf8f0", "#d9d2e6", "#d99a12"
VB_COVER, VB_COVER_DK, VB_RIBBON = "#5b2a86", "#3f1b60", "#d4153f"    # as s07
BURST_C, BURST_DK = "#ffd84a", "#ff5a36"                              # as s07


def _quill(c, x, y, rot, ln=150.0):
    """White feather quill, shaft along local -y from (x, y)."""
    with saved(c, x, y, 1.0, rot) as q:
        q.move_to(0, 20)                                   # gold nib
        q.line_to(0, 44)
        _s(q, INK, 9)
        q.move_to(0, 22)
        q.line_to(0, 42)
        _s(q, QUILL_NIB, 4)
        vane = [(0, -ln), (14, -ln * 0.82), (19, -ln * 0.55), (15, -ln * 0.25), (5, 2),
                (-4, 2), (-12, -ln * 0.22), (-6, -ln * 0.4), (-15, -ln * 0.5),
                (-13, -ln * 0.78)]
        smooth_path(q, vane, closed=True)
        _fs(q, QUILL_C, INK, 4)
        q.save()
        smooth_path(q, vane, closed=True)
        q.clip()
        ellipse(q, 12, -ln * 0.5, 9, ln * 0.45)
        _f(q, QUILL_SH, 0.8)
        q.restore()
        q.move_to(0, 18)                                   # shaft + barbs
        q.line_to(0, -ln + 6)
        _s(q, "#b9b0c8", 3)
        for k in range(4):
            yy = -ln * (0.3 + 0.15 * k)
            q.move_to(0, yy)
            q.line_to(11, yy - 12)
        _s(q, "#c9c1d8", 2)


def draw_notebook(c, x, y, s, rot=0.0, t=0.0, glow=1.0):
    """The s03 gift ("writing that blows people away"): the glowing teal
    notebook (label, gold line, gold star, as s03) with a quill tucked behind it. (x, y) = centre of the cover,
    ~106 x 136 at s=1 (the quill pokes out top-right to about (+84, -138))."""
    with saved(c, x, y, s, rot) as cc:
        if glow > 0.01:                                    # soft golden glow
            g = cairo.RadialGradient(8, -16, 12, 8, -16, 118)
            g.add_color_stop_rgba(0, 1.0, 0.86, 0.45, 0.62 * glow)
            g.add_color_stop_rgba(1, 1.0, 0.86, 0.45, 0.0)
            circle(cc, 8, -16, 118)
            cc.set_source(g)
            cc.fill()
        _quill(cc, 30, -40, 0.5)
        rrect(cc, -48, -64, 106, 132, 7)                   # page block
        _fs(cc, NB_PAGES, INK, 4)
        for k in range(3):
            cc.move_to(52 - k * 0.5, -54 + k * 2)
            cc.line_to(52 - k * 0.5, 58)
        cc.move_to(-40, 62)
        cc.line_to(50, 62)
        _s(cc, "#e8d8a8", 2)
        gl = 0.75 + 0.25 * math.sin(t * 4.0)               # light leaking from the pages
        cc.move_to(55, -56)
        cc.line_to(55, 62)
        _s(cc, "ai_accent", 11, 0.45 * glow * gl)
        cc.move_to(55, -56)
        cc.line_to(55, 62)
        _s(cc, "#fff6c8", 4, 0.95 * glow)
        rrect(cc, -56, -70, 106, 136, 9)                   # cover
        _fs(cc, NB_COVER, INK, 5)
        cc.save()
        rrect(cc, -56, -70, 106, 136, 9)
        cc.clip()
        cc.rectangle(28, -72, 30, 140)                     # one shadow tone
        _f(cc, NB_COVER_DK, 0.45)
        cc.rectangle(-58, -72, 20, 140)                    # spine
        _f(cc, NB_COVER_DK)
        cc.restore()
        cc.move_to(-38, -70)
        cc.line_to(-38, 66)
        _s(cc, INK, 3.5)
        rrect(cc, -26, -48, 64, 30, 6)                     # label (as s03)
        _fs(cc, NB_PAGES, INK, 3)
        cc.move_to(-22, 4)                                 # gold line
        cc.line_to(34, 4)
        _s(cc, "gold", 5)
        P._star4(cc, 6, 36, 17, 0.2)                       # gold star
        _f(cc, "gold")
        ellipse(cc, -24, -54, 9, 4, -0.4)
        _f(cc, "white", 0.4)
        cc.move_to(-46, 66)                                # ribbon bookmark
        cc.curve_to(-44, 78, -50, 84, -46, 94)
        _s(cc, INK, 8)
        cc.move_to(-46, 66)
        cc.curve_to(-44, 78, -50, 84, -46, 94)
        _s(cc, "ai_accent", 4)
        if glow > 0.01:
            P.sparkles(cc, 6, -20, 96, t, n=3, seed=41, color="ai_accent", size=0.55 * glow)


def _burst_path(c, r_out, r_in, n=14, rot=0.0):
    c.new_sub_path()
    for i in range(2 * n):
        a = rot + i * math.pi / n
        rr = r_out if i % 2 == 0 else r_in
        if i == 0:
            c.move_to(math.cos(a) * rr, math.sin(a) * rr)
        else:
            c.line_to(math.cos(a) * rr, math.sin(a) * rr)
    c.close_path()


def draw_twist_script(c, x, y, s, rot=0.0):
    """The s07 gift (a bombshell plot twist for his villain story): the purple
    storybook MY VILLAIN STORY (gold border + title, gold snake 'S' emblem, red
    ribbon bookmark) with its 'BOMBSHELL TWIST!' comic starburst bursting out
    of the top of the pages. (x, y) = centre of the cover, ~132 x 172 at s=1;
    the burst spans about x -68..+60, y -192..-64."""
    with saved(c, x, y, s, rot) as cc:
        poly(cc, [(26, 80), (26, 106), (32, 100), (38, 106), (38, 80)])   # ribbon (as s07)
        _fs(cc, VB_RIBBON, INK, 3)
        rrect(cc, -58, -80, 128, 166, 7)                             # page block
        _fs(cc, "#f6ecd2", INK, 4)
        for k in range(3):
            cc.move_to(66 - k * 0.5, -70 + k * 2)
            cc.line_to(66 - k * 0.5, 80)
        _s(cc, "#e0d2ae", 2)
        rrect(cc, -66, -86, 128, 172, 9)                             # purple cover
        _fs(cc, VB_COVER, INK, 5)
        cc.save()
        rrect(cc, -66, -86, 128, 172, 9)
        cc.clip()
        cc.rectangle(34, -88, 30, 176)                               # one shadow tone
        _f(cc, VB_COVER_DK, 0.5)
        cc.rectangle(-68, -88, 22, 176)                              # spine
        _f(cc, VB_COVER_DK)
        cc.restore()
        cc.move_to(-46, -86)
        cc.line_to(-46, 86)
        _s(cc, INK, 3.5)
        rrect(cc, -38, -74, 90, 148, 7)                              # gold border
        _s(cc, "gold", 4)
        for txt, fs0, ty in (("MY VILLAIN", 21, -40), ("STORY", 27, -12)):
            fs = fs0
            while fs > 10 and text_width(cc, txt, "title", fs) > 80:
                fs -= 1
            text(cc, txt, 7, ty, fs, P.C("gold"), "title", outline=INK, outline_w=4)
        P._snake_emblem(cc, 7, 28, 0.3)                              # gold snake 'S'
        P._star4(cc, 7, 60, 9, 0.3)                                  # ka-boom doodle
        P._fs(cc, P.C("gold"), INK, 2)
        with saved(cc, -4, -128, 1.0, -0.1) as cb:                   # the starburst
            _burst_path(cb, 64, 49, 14, 0.1)
            _fs(cb, BURST_DK, INK, 4.5)
            _burst_path(cb, 58, 45, 14, 0.1)
            _f(cb, BURST_C)
            for txt, fs0, ty, col in (("BOMBSHELL", 22, -1, "white"), ("TWIST!", 32, 27, "danger")):
                fs = fs0
                while fs > 12 and text_width(cb, txt, "comic", fs) > 84:
                    fs -= 1
                text(cb, txt, 0, ty, fs, col, "comic", outline=INK, outline_w=5)


def _star5_path(c, x, y, r, rot=0.0, inner=0.47):
    c.new_sub_path()
    for i in range(10):
        a = rot - math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * inner
        px, py = x + math.cos(a) * rr, y + math.sin(a) * rr
        if i == 0:
            c.move_to(px, py)
        else:
            c.line_to(px, py)
    c.close_path()


def _gift_star(c, x, y, s, rot=0.0):
    """The FOR EFFORT gift (s09): gold star r 40 + label_tag under it."""
    with saved(c, x, y, s) as cc:
        with saved(cc, 0, 58, 1.0, -0.04) as c2:
            P.label_tag(c2, 0, 0, "FOR EFFORT", color="ai_accent", size=24)
        _star5_path(cc, 0, 0, 40, rot)
        fill_stroke(cc, STAR_GOLD, "ink", 5.0)
        cc.save()
        _star5_path(cc, 0, 0, 40, rot)
        cc.clip()
        _star5_path(cc, 6.4, 8, 40, rot)
        cc.rectangle(-80, -80, 160, 160)
        cc.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        core.set_color(cc, STAR_GOLD_DK)
        cc.fill()
        cc.set_fill_rule(cairo.FILL_RULE_WINDING)
        cc.restore()
        _star5_path(cc, 0, 0, 40, rot)
        core.stroke(cc, "ink", 5.0)
        ellipse(cc, -8, -12, 6.8, 4, -0.6)
        cc.set_source_rgba(1, 1, 1, 0.85)
        cc.fill()


HUG_DY = 66.0       # the grip sits low on the book so its cover art stays visible


def _hug_hands(ctx, bx, by, bs, rot, k=1.0):
    """White gloves wrapping over the book's side edges (the hug, as s06),
    gripping its lower half (the title + the laser satellite stay in view)."""
    if k <= 0.01:
        return
    hs = MS * 1.45 * k
    with saved(ctx, bx, by + HUG_DY * bs, 1.0, rot) as c:
        for sx in (-1, 1):
            ex = sx * 75 * bs
            ellipse(c, ex + sx * 8 * hs, 18 * bs, 22 * hs, 27 * hs, sx * 0.2)
            _fs(c, "glove", INK, 5)
            for i, fy in enumerate((-4, 18, 40)):
                y0 = (fy - 6) * bs
                L = (30 - 3 * abs(i - 1)) * hs
                for col, w in ((INK, 23 * hs), ("glove", 23 * hs - 9)):
                    c.move_to(ex + sx * 8 * hs, y0)
                    c.line_to(ex - sx * L, y0 + 4 * hs)
                    _s(c, col, w)
            for fy in (7, 29):
                c.move_to(ex - sx * 6 * hs, fy * bs - 6 * bs)
                c.line_to(ex - sx * 20 * hs, fy * bs - 4 * bs)
            _s(c, "#c9c8da", 3)


# ---------------------------------------------------------------------------
# SPOOKY GIFTS (s11 l08 "Bats, goblins, dragons..." and the s12 monster party;
# the same drawing code lives in s11_heart.py and s12_party.py)
# ---------------------------------------------------------------------------
BAT_C, BAT_DK, BAT_BELLY = "#7d64b8", "#5a4590", "#b4a2e0"
BAT_WING, BAT_WING_LN = "#4b3a7c", "#9a86cc"
GOB, GOB_DK, GOB_LT, GOB_MOUTH = "#7ccf4e", "#4f9a32", "#b6ec88", "#5a1530"
DRG, DRG_DK, DRG_BELLY, DRG_SNOUT = "#5a3f92", "#3b2866", "#c9b3ea", "#7258b0"
DRG_WING, DRG_WING_LN, DRG_HORN = "#2c2050", "#6a54a0", "#f3e6c0"
PUMP, PUMP_DK, PUMP_GLOW = "#ff8a1f", "#d9640c", "#ffd84a"
SPOOK_EYE, HOLE = "#ffe066", "#1d1426"


def _scallop_wing(c, top, pts, fill, line, bones=True, dip=15.0, lw=4.5):
    """Bat-style wing: `top` = (c1, c2, tip) curve from the shoulder (0, -10),
    then scallops through `pts` back to the shoulder."""
    c.move_to(0, -10)
    c.curve_to(*top[0], *top[1], *top[2])
    allp = [top[2]] + list(pts)
    for (x0, y0), (x1, y1) in zip(allp, allp[1:]):
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2 - dip
        c.curve_to(lerp(x0, mx, 0.6), lerp(y0, my, 0.6), lerp(x1, mx, 0.6),
                   lerp(y1, my, 0.6), x1, y1)
    c.close_path()
    _fs(c, fill, INK, lw)
    if bones:
        for (bx, by) in allp[:3]:
            c.move_to(8, -5)
            c.line_to(bx * 0.9, by * 0.9 - 2)
        _s(c, line, 3)


def _bat_wing(c, sx, ang, sy=1.0, fill=BAT_WING, line=BAT_WING_LN):
    c.save()
    c.scale(sx, 1.0)
    c.rotate(ang)
    c.scale(1.0, sy)
    _scallop_wing(c, ((36, -46), (80, -54), (114, -40)), [(98, 6), (64, 16), (28, 18), (0, 10)],
                  fill, line)
    c.restore()


def draw_bat(c, x, y, s, t, flap=0.0, rot=0.0, sq=0.0, look=(0.0, 0.0)):
    """Plush bat with little fangs. (x, y) = body centre, ~280 wide at s=1.
    flap: -1 wings down .. 0 rest (slightly raised) .. 1 wings up."""
    with saved(c, x, y, (s * (1 + sq * 0.5), s * (1 - sq)), rot) as cc:
        ang = -0.62 * flap - 0.08
        wy = 1.0 - 0.22 * abs(flap)
        for sx in (-1, 1):
            cc.save()
            cc.translate(sx * 26, -6)
            _bat_wing(cc, sx, ang, wy)
            cc.restore()
        for sx in (-1, 1):                                     # feet
            ellipse(cc, sx * 12, 34, 9, 6)
            _fs(cc, BAT_DK, INK, 3.5)
        for sx in (-1, 1):                                     # big ears
            poly(cc, [(sx * 6, -28), (sx * 34, -64), (sx * 33, -16)])
            _fs(cc, BAT_C, INK, 4.5)
            poly(cc, [(sx * 15, -27), (sx * 30, -52), (sx * 29, -22)])
            _f(cc, "#ff9ec4", 0.85)
        ellipse(cc, 0, 0, 36, 36)                              # round plush body
        _fs(cc, BAT_C, INK, 5)
        cc.save()
        ellipse(cc, 0, 0, 36, 36)
        cc.clip()
        ellipse(cc, 18, 12, 30, 34)
        _f(cc, BAT_DK, 0.55)
        cc.restore()
        ellipse(cc, 0, 17, 19, 14)                             # belly patch + stitch
        _f(cc, BAT_BELLY, 0.75)
        for k in range(3):
            cc.move_to(-9 + k * 9, 24)
            cc.line_to(-5 + k * 9, 28)
        _s(cc, BAT_DK, 2)
        lx, ly = look[0] * 4, look[1] * 3
        for sx in (-1, 1):                                     # big friendly eyes
            ellipse(cc, sx * 13, -8, 10, 11)
            _fs(cc, "white", INK, 3)
            circle(cc, sx * 13 + lx, -7 + ly, 5.5)
            _f(cc, INK)
            circle(cc, sx * 13 + lx - 2, -9.5 + ly, 2)
            _f(cc, "white")
            ellipse(cc, sx * 24, 7, 6, 3.5)
            _f(cc, "#ff8fb0", 0.75)
        for sx in (-1, 1):                                     # two little fangs
            poly(cc, [(sx * 2.5, 11.5), (sx * 9, 10.5), (sx * 6, 19.5)])
            _fs(cc, "white", INK, 2)
        cc.move_to(-11, 8)                                     # smile
        cc.curve_to(-5, 14, 5, 14, 11, 8)
        _s(cc, INK, 3)


def draw_goblin_mask(c, x, y, s, rot=0.0, sq=0.0):
    """Green goblin mask: pointy ears, warty nose, toothy grin (cute, not scary).
    (x, y) = face centre; ~340 wide (ears) x 180 tall at s=1."""
    with saved(c, x, y, (s * (1 + sq * 0.5), s * (1 - sq)), rot) as cc:
        for sx in (-1, 1):                                     # pointy ears
            poly(cc, [(sx * 76, -36), (sx * 172, -82), (sx * 140, -44), (sx * 118, -8),
                      (sx * 84, 24)])
            _fs(cc, GOB, INK, 5)
            poly(cc, [(sx * 92, -22), (sx * 150, -66), (sx * 112, -12), (sx * 92, 8)])
            _f(cc, GOB_DK, 0.8)
        face = [(0, -84), (56, -80), (92, -50), (100, -4), (86, 46), (52, 82), (0, 94),
                (-52, 82), (-86, 46), (-100, -4), (-92, -50), (-56, -80)]
        smooth_path(cc, face, closed=True)
        _fs(cc, GOB, INK, 5.5)
        cc.save()
        smooth_path(cc, face, closed=True)
        cc.clip()
        ellipse(cc, 70, 24, 56, 96)
        _f(cc, GOB_DK, 0.42)
        cc.restore()
        ellipse(cc, -42, -60, 24, 10, -0.25)                   # forehead shine
        _f(cc, GOB_LT, 0.8)
        for sx in (-1, 1):                                     # heavy brows
            poly(cc, [(sx * 12, -38), (sx * 72, -60), (sx * 80, -44), (sx * 18, -26)])
            _fs(cc, GOB_DK, INK, 4)
            ellipse(cc, sx * 40, -12, 22, 14, sx * 0.18)       # eye holes
            _fs(cc, HOLE, INK, 4)
        ellipse(cc, 0, 16, 21, 17)                             # big warty nose
        _fs(cc, GOB_DK, INK, 4.5)
        circle(cc, -7, 10, 5)
        _f(cc, GOB_LT, 0.85)
        for (wx, wy, wr) in ((12, 24, 3.5), (-72, 22, 4.5), (66, -28, 3.5)):
            circle(cc, wx, wy, wr)
            _fs(cc, GOB_DK, INK, 2)

        def mouth():
            cc.move_to(-60, 38)
            cc.curve_to(-30, 52, 30, 52, 60, 38)
            cc.curve_to(40, 84, -40, 84, -60, 38)
            cc.close_path()
        mouth()
        _f(cc, GOB_MOUTH)
        cc.save()
        mouth()
        cc.clip()
        for k in range(6):                                     # top teeth
            tx = -45 + k * 18
            ty = 38 + 10.5 * (1 - (tx / 60.0) ** 2)
            poly(cc, [(tx - 8, 30), (tx + 8, 30), (tx, ty + 11)])
        for sx in (-1, 1):                                     # two bottom tusks
            poly(cc, [(sx * 30 - 7, 80), (sx * 30 + 7, 80), (sx * 31, 55)])
        _fs(cc, "#fff6dc", INK, 2.5)
        cc.restore()
        mouth()
        _fs(cc, None, INK, 4.5)


def draw_dragon_fig(c, x, y, s, t, puff=-1.0, sq=0.0, look=(0.0, 0.0)):
    """Purple-black spooky DRAGON figurine: curly horns, little bat wings,
    yellow slit eyes, one tiny fang, spade tail, on a stone plinth.
    (x, y) = bottom-centre of the plinth; ~200 wide x 236 tall at s=1.
    puff 0..1 = progress of a smoke puff from the nostrils (< 0: none)."""
    with saved(c, x, y, (s * (1 + sq * 0.5), s * (1 - sq))) as cc:
        rrect(cc, -74, -30, 148, 30, 8)                        # plinth
        _fs(cc, "#4a4458", INK, 4.5)
        ellipse(cc, 0, -30, 74, 11)
        _fs(cc, "#6a6280", INK, 4)
        for (col, w) in ((INK, 21), (DRG, 12)):                # spade tail (behind)
            cc.move_to(20, -46)
            cc.curve_to(84, -44, 98, -70, 82, -96)
            _s(cc, col, w)
        poly(cc, [(82, -92), (66, -106), (84, -126), (98, -104)])
        _fs(cc, DRG_DK, INK, 4)
        for sx in (-1, 1):                                     # little bat wings
            cc.save()
            cc.translate(sx * 24, -112)
            cc.scale(sx * 0.85, 0.85)
            cc.rotate(-0.55)
            _scallop_wing(cc, ((26, -40), (62, -50), (92, -42)), [(80, 2), (54, 12), (24, 14),
                                                                  (0, 8)],
                          DRG_WING, DRG_WING_LN, lw=5)
            cc.restore()
        body = [(0, -130), (30, -124), (48, -96), (52, -62), (42, -36), (0, -30), (-42, -36),
                (-52, -62), (-48, -96), (-30, -124)]
        smooth_path(cc, body, closed=True)
        _fs(cc, DRG, INK, 5)
        cc.save()
        smooth_path(cc, body, closed=True)
        cc.clip()
        ellipse(cc, 34, -72, 30, 56)
        _f(cc, DRG_DK, 0.55)
        cc.restore()
        ellipse(cc, 0, -68, 24, 32)                            # belly plates
        _fs(cc, DRG_BELLY, INK, 3.5)
        for yy in (-86, -74, -62, -50):
            cc.move_to(-20, yy)
            cc.line_to(20, yy)
        _s(cc, "#9a82c4", 2.5)
        for sx in (-1, 1):                                     # feet + claws
            ellipse(cc, sx * 30, -34, 17, 9)
            _fs(cc, DRG, INK, 4)
            for k in range(3):
                circle(cc, sx * 30 + (k - 1) * 8, -27, 2.6)
            _f(cc, DRG_HORN)
            cc.move_to(sx * 40, -100)                          # stubby arms
            cc.curve_to(sx * 36, -86, sx * 28, -82, sx * 18, -84)
            _s(cc, INK, 13)
            cc.move_to(sx * 40, -100)
            cc.curve_to(sx * 36, -86, sx * 28, -82, sx * 18, -84)
            _s(cc, DRG, 6)
        hx, hy = 0, -162
        for sx in (-1, 1):                                     # ear frills
            poly(cc, [(hx + sx * 36, hy - 12), (hx + sx * 66, hy - 26), (hx + sx * 44, hy + 10)])
            _fs(cc, DRG_WING, INK, 4)
        for sx in (-1, 1):                                     # curly horns
            cc.move_to(hx + sx * 12, hy - 30)
            cc.curve_to(hx + sx * 18, hy - 58, hx + sx * 40, hy - 70, hx + sx * 50, hy - 58)
            cc.curve_to(hx + sx * 38, hy - 56, hx + sx * 32, hy - 44, hx + sx * 30, hy - 28)
            cc.close_path()
            _fs(cc, DRG_HORN, INK, 4)
        poly(cc, [(hx - 7, hy - 34), (hx, hy - 52), (hx + 7, hy - 34)])   # head spike
        _fs(cc, DRG_DK, INK, 3)
        ellipse(cc, hx, hy, 44, 38)                            # head
        _fs(cc, DRG, INK, 5)
        cc.save()
        ellipse(cc, hx, hy, 44, 38)
        cc.clip()
        ellipse(cc, hx + 30, hy + 6, 24, 40)
        _f(cc, DRG_DK, 0.45)
        cc.restore()
        ellipse(cc, hx, hy + 18, 28, 16)                       # snout
        _fs(cc, DRG_SNOUT, INK, 3.5)
        for sx in (-1, 1):
            ellipse(cc, hx + sx * 9, hy + 13, 3.5, 2.5)        # nostrils
            _f(cc, INK)
            ellipse(cc, hx + sx * 31, hy + 10, 6, 3.5)
            _f(cc, "#ff8fb0", 0.55)
        lx, ly = look[0] * 3.5, look[1] * 2.5
        for sx in (-1, 1):                                     # yellow slit eyes
            ellipse(cc, hx + sx * 17, hy - 8, 11, 12)
            _fs(cc, SPOOK_EYE, INK, 3.5)
            ellipse(cc, hx + sx * 17 + lx, hy - 7 + ly, 2.8, 8)
            _f(cc, INK)
            circle(cc, hx + sx * 17 - 4, hy - 12, 2.2)
            _f(cc, "white")
            cc.move_to(hx + sx * 5, hy - 21)                   # cheeky lid line
            cc.line_to(hx + sx * 29, hy - 17)
            _s(cc, INK, 4.5)
        cc.move_to(hx - 15, hy + 24)                           # grin + one tiny fang
        cc.curve_to(hx - 6, hy + 32, hx + 6, hy + 32, hx + 15, hy + 24)
        _s(cc, INK, 3.5)
        poly(cc, [(hx + 4, hy + 29), (hx + 11, hy + 27.5), (hx + 8.5, hy + 36)])
        _fs(cc, "white", INK, 2)
        if 0.0 <= puff <= 1.0:                                 # smoke puff
            for j in range(3):
                u = clamp(puff * 1.35 - j * 0.17)
                if u <= 0.0 or u >= 1.0:
                    continue
                a = 1.0 - u ** 1.6
                px = hx + 18 + 54 * u + j * 8
                py = hy + 10 - 74 * u - j * 10
                r = 9 + 16 * u
                circle(cc, px, py, r)
                cc.set_source_rgba(0.86, 0.83, 0.93, 0.95 * a)
                cc.fill_preserve()
                cc.set_source_rgba(*hexc(INK, 0.9 * a))
                cc.set_line_width(3.5)
                cc.stroke()


def draw_pumpkin(c, x, y, s, t, lit=1.0, sq=0.0):
    """Cute jack-o'-lantern. (x, y) = bottom-centre; ~140 x 130 at s=1."""
    with saved(c, x, y, (s * (1 + sq * 0.5), s * (1 - sq))) as cc:
        with saved(cc, 4, -100, 1.0, 0.28) as c2:              # stem + curl
            rrect(c2, -8, -18, 16, 28, 5)
            _fs(c2, "#6b7a2a", INK, 4)
        cc.move_to(8, -100)
        cc.curve_to(30, -112, 40, -96, 28, -92)
        _s(cc, INK, 7)
        cc.move_to(8, -100)
        cc.curve_to(30, -112, 40, -96, 28, -92)
        _s(cc, "#8fae3a", 3)
        for sx in (-1, 1):                                     # side lobes
            ellipse(cc, sx * 34, -48, 36, 46)
            _fs(cc, PUMP_DK, INK, 5)
        ellipse(cc, 0, -50, 44, 50)
        _fs(cc, PUMP, INK, 5)
        for sx in (-1, 1):
            cc.move_to(sx * 16, -96)
            cc.curve_to(sx * 26, -70, sx * 26, -30, sx * 16, -4)
        _s(cc, PUMP_DK, 3.5)
        fl = lit * (0.85 + 0.15 * math.sin(t * 13) * noise1(t * 3, 9))
        glow = core.mixc("#7a2a10", PUMP_GLOW, clamp(fl))

        def face():
            for sx in (-1, 1):
                poly(cc, [(sx * 8, -58), (sx * 32, -58), (sx * 20, -80)])
            poly(cc, [(-6, -44), (6, -44), (0, -54)])
            poly(cc, [(-34, -34), (-24, -27), (-16, -33), (-8, -25), (0, -31), (8, -25),
                      (16, -33), (24, -27), (34, -34), (26, -16), (14, -10), (0, -8),
                      (-14, -10), (-26, -16)])
        face()
        _fs(cc, glow, INK, 3)
        cc.save()
        face()
        cc.clip()
        ellipse(cc, 0, -42, 26, 22)
        _f(cc, "#fff3b0", 0.65 * clamp(fl))
        cc.restore()
        ellipse(cc, -20, -78, 9, 5, -0.5)
        _f(cc, "white", 0.45)


def draw_paper_bat(c, x, y, s, rot=0.0, col="#2a1a3a"):
    """Flat paper-cut bat for the party garlands (static). (x, y) = body."""
    with saved(c, x, y, s, rot) as cc:
        for sx in (-1, 1):
            cc.save()
            cc.translate(sx * 10, -2)
            cc.scale(sx * 0.42, 0.42)
            _scallop_wing(cc, ((36, -46), (80, -54), (114, -40)),
                          [(98, 6), (64, 16), (28, 18), (0, 10)], col, None, bones=False, lw=7)
            cc.restore()
        for sx in (-1, 1):
            poly(cc, [(sx * 3, -10), (sx * 11, -24), (sx * 12, -6)])
            _fs(cc, col, INK, 2.5)
        ellipse(cc, 0, 0, 13, 14)
        _fs(cc, col, INK, 3)
        for sx in (-1, 1):
            circle(cc, sx * 5, -3, 2.6)
            _f(cc, "#ffe066")


# ---------------------------------------------------------------------------
# science-fair photo: small corkboard version (as s02) + the s11 close-up
# ---------------------------------------------------------------------------
def science_photo_small(ctx, x, y, w, h, rot):
    with saved(ctx, x, y, 1.0, rot) as c:
        rrect(c, -w / 2 + 5, -h / 2 + 6, w, h, 3)
        core.fill(c, (0, 0, 0, 0.3))
        rrect(c, -w / 2, -h / 2, w, h, 3)
        _fs(c, "#f3efe6", INK, 3)
        px0, py0, pw, ph = -w / 2 + 7, -h / 2 + 7, w - 14, h - 24
        c.save()
        c.rectangle(px0, py0, pw, ph)
        c.clip()
        core.bg(c, "#b9b0c2")
        c.rectangle(px0, py0 + ph * 0.52, pw, ph)
        core.fill(c, "#a59c90")
        kx, ky = px0 + pw * 0.33, py0 + ph * 0.36
        poly(c, [(kx - 11, ky + 6), (kx + 11, ky + 6), (kx + 14, ky + 24), (kx - 14, ky + 24)])
        core.fill(c, "#6f5a7c")
        circle(c, kx, ky, 8)
        _fs(c, "#e6cdb6", "#4a3a44", 1.5)
        circle(c, kx + 3, ky - 1, 2.6)
        core.stroke(c, "#c9a84f", 1.4)
        rx_, ry_ = px0 + pw * 0.62, py0 + ph * 0.36
        c.rectangle(rx_ - 7, ry_ - 2, 14, 16)
        _fs(c, "#9aa0a8", "#4a4650", 1.5)
        circle(c, rx_, ry_ - 7, 4)
        _fs(c, "#f2e6a0", "#4a4650", 1.2)
        c.rectangle(px0 + pw * 0.14, py0 + ph * 0.52, pw * 0.66, 5)
        _fs(c, "#8a7f74", "#4a4650", 1.2)
        circle(c, px0 + pw * 0.47, py0 + ph * 0.52 + 9, 3.2)
        core.fill(c, "#7f9bc4")
        poly(c, [(px0 + pw * 0.47 - 2, py0 + ph * 0.52 + 11),
                 (px0 + pw * 0.47 - 4, py0 + ph * 0.52 + 19),
                 (px0 + pw * 0.47 + 3, py0 + ph * 0.52 + 18)])
        core.fill(c, "#7f9bc4")
        for row in range(3):
            yy = py0 + ph * (0.7 + row * 0.12)
            for k in range(6):
                xx = px0 + 9 + k * (pw - 18) / 5 + (row % 2) * 4
                c.rectangle(xx - 4, yy - 7, 8, 6)
                c.rectangle(xx - 4, yy, 8, 2)
                core.fill(c, "#7d7a84")
        c.restore()
        c.move_to(-w / 2 + 14, h / 2 - 9)
        c.line_to(-w / 2 + 60, h / 2 - 10)
        core.stroke(c, "#8a8494", 2)
        circle(c, 0, -h / 2 + 6, 7)
        _fs(c, "danger", INK, 2.5)


# faded photo palette
F_WALL, F_WALL2, F_FLOOR, F_FLOOR2 = "#bdb3c4", "#a99fb6", "#bdb3a4", "#a39a8c"
F_INK = "#4a4252"
F_SKIN, F_SKIN_SH = "#e8cdb6", "#d0b098"
F_CAPE, F_CAPE_IN, F_SUIT = "#43384c", "#a8687a", "#7a6890"
F_TIN, F_TIN_DK = "#9fa5ae", "#7f8590"
F_CLOTH, F_CLOTH_DK = "#d9d2c4", "#bcb3a4"
F_CHAIR, F_CHAIR_DK, F_CHAIR_HI = "#75717f", "#5a5666", "#a6a2b0"
F_RIB = "#7f9bc4"


def _folding_chair_back(c, x, y, s):
    """Grey folding chair seen from behind (EMPTY: nothing above the
    backrest). (x, y) = floor centre. Darker than the floor, with a soft floor
    shadow and a lit top edge so every chair reads as its own object."""
    with saved(c, x, y, s):
        ellipse(c, 4, 2, 40, 9)                                        # floor shadow
        _f(c, (0.25, 0.2, 0.25, 0.22))
        for sx in (-1, 1):                            # back legs
            c.move_to(sx * 27, 0)
            c.line_to(sx * 22, -96)
        _s(c, F_INK, 10)
        for sx in (-1, 1):
            c.move_to(sx * 27, 0)
            c.line_to(sx * 22, -96)
        _s(c, F_CHAIR_DK, 5.5)
        poly(c, [(-34, -58), (34, -58), (30, -46), (-30, -46)])       # empty seat
        _fs(c, F_CHAIR_DK, F_INK, 3.5)
        rrect(c, -31, -120, 62, 42, 9)                                 # backrest
        _fs(c, F_CHAIR, F_INK, 4)
        c.move_to(-22, -115)                                           # lit top edge
        c.line_to(22, -115)
        _s(c, F_CHAIR_HI, 4)
        rrect(c, -18, -105, 36, 10, 5)                                 # hand slot
        _fs(c, F_CHAIR_DK, None)


def _kid_malvo(c, x, y):
    """Kid Malvo behind the table (photo-local). (x, y) = chin."""
    # tiny cape + suit
    poly(c, [(x - 58, y + 120), (x - 50, y + 30), (x - 30, y + 14), (x + 30, y + 14),
             (x + 50, y + 30), (x + 58, y + 120)])
    _fs(c, F_CAPE, F_INK, 3)
    poly(c, [(x - 32, y + 120), (x - 30, y + 26), (x + 30, y + 26), (x + 32, y + 120)])
    _fs(c, F_SUIT, F_INK, 3)
    for sx in (-1, 1):                                                # collar points
        poly(c, [(x + sx * 22, y + 18), (x + sx * 56, y - 30), (x + sx * 42, y + 26)])
        _fs(c, F_CAPE_IN, F_INK, 3)
    # proud arm: glove up, presenting the robot (screen-right)
    c.move_to(x + 28, y + 50)
    c.curve_to(x + 62, y + 46, x + 76, y + 20, x + 86, y - 2)
    _s(c, F_INK, 17)
    c.move_to(x + 28, y + 50)
    c.curve_to(x + 62, y + 46, x + 76, y + 20, x + 86, y - 2)
    _s(c, F_SUIT, 10)
    circle(c, x + 90, y - 10, 13)
    _fs(c, "#efedf2", F_INK, 3)
    for k in range(3):
        c.move_to(x + 92 + k * 4, y - 20)
        c.line_to(x + 98 + k * 6, y - 34 + k * 3)
    _s(c, F_INK, 7)
    for k in range(3):
        c.move_to(x + 92 + k * 4, y - 20)
        c.line_to(x + 98 + k * 6, y - 34 + k * 3)
    _s(c, "#efedf2", 3.5)
    # head
    hx, hy = x, y - 52
    for sx in (-1, 1):                                                # ears
        ellipse(c, hx + sx * 44, hy + 6, 9, 13)
        _fs(c, F_SKIN, F_INK, 3)
        for k in range(3):                                            # tiny tufts
            c.move_to(hx + sx * 40, hy - 14 + k * 6)
            c.line_to(hx + sx * (54 + k * 3), hy - 22 + k * 7)
        _s(c, "#d0d0d8", 3.5)
    ellipse(c, hx, hy, 44, 50)
    _fs(c, F_SKIN, F_INK, 3.5)
    ellipse(c, hx - 16, hy - 30, 12, 6, -0.5)
    _f(c, "white", 0.45)
    for sx in (-1, 1):                                                # big hopeful eyes
        ellipse(c, hx + sx * 16, hy + 2, 10, 12)
        _fs(c, "white", F_INK, 2.5)
        circle(c, hx + sx * 16 + 1, hy + 3, 5.5)
        _f(c, F_INK)
        circle(c, hx + sx * 16 - 1, hy, 1.8)
        _f(c, "white")
        c.move_to(hx + sx * 9, hy - 16)
        c.line_to(hx + sx * 24, hy - 19)
        _s(c, F_INK, 3.5)
    circle(c, hx + 16, hy + 2, 15)                                    # monocle
    _s(c, "#c9a84f", 3.5)
    c.move_to(hx + 28, hy + 12)
    c.curve_to(hx + 34, hy + 30, hx + 30, hy + 50, hx + 24, y + 26)
    _s(c, "#c9a84f", 1.6)
    c.move_to(hx - 12, hy + 26)                                       # proud little grin
    c.curve_to(hx - 4, hy + 34, hx + 6, hy + 34, hx + 13, hy + 25)
    _s(c, F_INK, 3)
    ellipse(c, hx - 26, hy + 18, 7, 4)
    _f(c, "#e8a0a8", 0.6)
    ellipse(c, hx + 28, hy + 18, 7, 4)
    _f(c, "#e8a0a8", 0.6)


def _home_robot(c, x, y):
    """Homemade tin robot with a light bulb on its head. (x, y) = feet."""
    for sx in (-1, 1):                                                # legs
        c.rectangle(x + sx * 16 - 6, y - 26, 12, 26)
        _fs(c, F_TIN_DK, F_INK, 2.5)
    rrect(c, x - 34, y - 86, 68, 62, 6)                               # body (a can)
    _fs(c, F_TIN, F_INK, 3)
    for k in range(3):
        circle(c, x - 18 + k * 18, y - 52, 4)
        _f(c, ("#c98f8f", "#9fbf8f", "#d8c88a")[k])
    for sx in (-1, 1):                                                # bendy arms
        c.move_to(x + sx * 34, y - 72)
        c.curve_to(x + sx * 52, y - 70, x + sx * 52, y - 52, x + sx * 60, y - 44)
        _s(c, F_INK, 9)
        c.move_to(x + sx * 34, y - 72)
        c.curve_to(x + sx * 52, y - 70, x + sx * 52, y - 52, x + sx * 60, y - 44)
        _s(c, F_TIN_DK, 5)
    rrect(c, x - 28, y - 134, 56, 46, 6)                              # head (a box)
    _fs(c, F_TIN, F_INK, 3)
    for sx in (-1, 1):
        circle(c, x + sx * 12, y - 114, 7)
        _fs(c, "#f4f2e6", F_INK, 2.5)
        circle(c, x + sx * 12, y - 114, 2.5)
        _f(c, F_INK)
    for k in range(4):
        c.move_to(x - 12 + k * 8, y - 100)
        c.line_to(x - 12 + k * 8, y - 94)
    _s(c, F_INK, 2)
    c.rectangle(x - 7, y - 146, 14, 12)                               # bulb screw base
    _fs(c, "#b8b0a0", F_INK, 2.5)
    circle(c, x, y - 160, 16)                                         # the light bulb
    _fs(c, "#f2e6a8", F_INK, 3)
    for k in range(5):                                                # faded glow rays
        a = -math.pi / 2 + (k - 2) * 0.55
        c.move_to(x + math.cos(a) * 24, y - 160 + math.sin(a) * 24)
        c.line_to(x + math.cos(a) * 34, y - 160 + math.sin(a) * 34)
    _s(c, "#e0cf8a", 3)


def _photo_big(c):
    """The 640x500 science-fair photo (bible size), drawn centred at the origin."""
    w, h = PHOTO_W, PHOTO_H
    bx, by = -w / 2, -h / 2
    rrect(c, bx + 10, by + 14, w, h, 5)                               # flat shadow
    _f(c, (0.05, 0.02, 0.06, 0.4))
    rrect(c, bx, by, w, h, 5)
    _fs(c, "#f1ece2", INK, 4)
    px0, py0, pw, ph = bx + 26, by + 26, w - 52, h - 96
    c.save()
    c.rectangle(px0, py0, pw, ph)
    c.clip()
    c.translate(px0, py0)
    # gym wall + floor
    core.bg(c, F_WALL)
    c.rectangle(0, 214, pw, 16)
    _f(c, F_WALL2)
    c.rectangle(0, 230, pw, ph)
    _f(c, F_FLOOR)
    for k in range(4):
        c.move_to(0, 262 + k * 40)
        c.line_to(pw, 262 + k * 40)
    _s(c, F_FLOOR2, 2)
    for k in range(7):                                                # gym floor boards
        c.move_to(pw * 0.5 + (k - 3) * 70, 230)
        c.line_to(pw * 0.5 + (k - 3) * 150, ph)
    _s(c, F_FLOOR2, 1.6, 0.6)
    # pennant string along the top
    c.move_to(-10, 4)
    c.curve_to(pw * 0.3, 26, pw * 0.7, 26, pw + 10, 4)
    _s(c, F_INK, 2)
    for k in range(11):
        u = (k + 0.5) / 11
        xx = u * pw
        yy = 4 + 22 * 4 * u * (1 - u) * 0.75
        poly(c, [(xx - 12, yy), (xx + 12, yy), (xx, yy + 22)])
        _fs(c, ("#c99a9a", "#9ab3c9", "#c9c09a", "#a7c2a0")[k % 4], F_INK, 2)
    # SCIENCE FAIR banner (above the kid, clear of the robot)
    with saved(c, pw * 0.27, 62, 1.0, -0.02) as cb:
        rrect(cb, -128, -22, 256, 46, 6)
        _fs(cb, "#dccaa8", F_INK, 3)
        text(cb, "SCIENCE FAIR", 0, 13, 34, "#8a5f6a", "title")
    # kid Malvo behind the folding table, proudly presenting his robot
    _kid_malvo(c, pw * 0.3, 196)
    tx0, tx1, ty = 34, pw - 110, 232
    _home_robot(c, pw * 0.65, ty)
    rrect(c, tx0, ty - 4, tx1 - tx0, 14, 4)                           # table top
    _fs(c, F_CLOTH, F_INK, 3)
    poly(c, [(tx0 + 4, ty + 10), (tx1 - 4, ty + 10), (tx1 - 10, ty + 86), (tx0 + 10, ty + 86)])
    _fs(c, F_CLOTH, F_INK, 3)
    for k in range(1, 8):
        xx = lerp(tx0 + 4, tx1 - 4, k / 8)
        c.move_to(xx, ty + 14)
        c.line_to(xx + (k - 4) * 1.2, ty + 82)
    _s(c, F_CLOTH_DK, 2.5)
    # three rows of EMPTY folding chairs, centre aisle (seen from behind,
    # spaced so each one reads; the far ends run out of the photo)
    aisle = pw * 0.5
    for yy, sc in ((322, 0.6), (366, 0.78), (424, 1.0)):
        sp = 98 * sc
        for side in (-1, 1):
            for k in range(5):
                xx = aisle + side * (60 + 34 * sc + k * sp)
                if -40 < xx < pw + 40:
                    _folding_chair_back(c, xx, yy, sc)
    # limp PARTICIPANT ribbon pinned to the skirt, hanging over the aisle
    rx, ry = aisle, ty + 30
    for sx, ln in ((-1, 52), (1, 44)):
        c.move_to(rx + sx * 5, ry + 8)
        c.curve_to(rx + sx * 10, ry + 26, rx + sx * 2, ry + 38, rx + sx * 7, ry + ln)
        _s(c, F_INK, 15)
        c.move_to(rx + sx * 5, ry + 8)
        c.curve_to(rx + sx * 10, ry + 26, rx + sx * 2, ry + 38, rx + sx * 7, ry + ln)
        _s(c, F_RIB, 10)
    pts = []
    for j in range(20):
        a = j / 20 * 2 * math.pi
        rr = 25 if j % 2 == 0 else 20
        pts.append((rx + math.cos(a) * rr, ry + math.sin(a) * rr * 0.92))
    poly(c, pts)
    _fs(c, F_RIB, F_INK, 2.5)
    circle(c, rx, ry, 11)
    _fs(c, "#d8c88a", F_INK, 2)
    with saved(c, rx + 4, ry + 72, 1.0, 0.12) as cc:                # tag, drooping
        rrect(cc, -78, -17, 156, 34, 5)
        _fs(cc, "#ece6da", F_INK, 2.5)
        text(cc, "PARTICIPANT", 0, 8, 22, "#5d5568", "ui")
    # faded / warm photographic wash + soft corner darkening
    c.set_source_rgba(1.0, 0.9, 0.72, 0.14)
    c.paint()
    g = cairo.RadialGradient(pw / 2, ph / 2, ph * 0.4, pw / 2, ph / 2, pw * 0.75)
    g.add_color_stop_rgba(0, 0.3, 0.2, 0.2, 0.0)
    g.add_color_stop_rgba(1, 0.3, 0.2, 0.2, 0.2)
    c.set_source(g)
    c.paint()
    c.restore()
    c.rectangle(px0, py0, pw, ph)
    _s(c, "#cfc6b8", 2)
    with saved(c, bx + 52, by + h - 26, 1.0, -0.02) as cc:          # handwriting
        text(cc, "science fair  -  age 9", 0, 0, 30, "#7a7088", "round", "left")


RAIN_SHEAR = 0.13                         # window light falls from the upper left


def _window_light_path(c):
    """The rainy night window's light, cast across the corkboard: one tall
    gothic-arched pane (sheared), big enough that the whole photo sits in it,
    with the mullion shadow running down its left side."""
    def P_(x, y):
        return (x + (y - PHOTO_C[1]) * RAIN_SHEAR, y)
    x0, x1, yt, ya, yb = 46.0, 968.0, 380.0, 196.0, 1236.0
    xm = (x0 + x1) / 2
    c.move_to(*P_(x0, yb))
    c.line_to(*P_(x0, yt))
    c.curve_to(*P_(x0, yt - 120), *P_(xm - 230, ya + 20), *P_(xm, ya))
    c.curve_to(*P_(xm + 230, ya + 20), *P_(x1, yt - 120), *P_(x1, yt))
    c.line_to(*P_(x1, yb))
    c.close_path()
    # a second (partial) pane beyond the mullion, at the left edge
    c.move_to(*P_(-160, yb))
    c.line_to(*P_(-160, yt))
    c.line_to(*P_(x0 - 34, yt + 30))
    c.line_to(*P_(x0 - 34, yb))
    c.close_path()


def _cork_layer(c):
    """Corkboard close-up (static, cached): cork, string, paper corners, photo,
    the cool light of the rainy window and a few droplet shadows."""
    core.bg(c, "#c79a5b")
    for i in range(420):                                              # cork speckles
        x = hash01(i, 301) * 1080
        y = hash01(i, 302) * 1920
        r = 1.5 + 3.0 * hash01(i, 303)
        circle(c, x, y, r)
        _f(c, "#a87a40" if hash01(i, 304) < 0.6 else "#ddb478", 0.7)
    # neighbouring pinned papers peeking in at the edges
    with saved(c, 1000, 150, 1.0, 0.08) as cc:
        rrect(cc, -200, -160, 400, 300, 4)
        _fs(cc, "#f2ead6", INK, 4)
        for k in range(5):
            cc.move_to(-170, -120 + k * 36)
            cc.line_to(60 - (k % 2) * 60, -120 + k * 36)
        _s(cc, "#b8ae9c", 6)
    with saved(c, 40, 1290, 1.0, -0.1) as cc:
        rrect(cc, -220, -150, 380, 300, 4)
        _fs(cc, "#5b8fd8", INK, 4)
        for k in range(6):
            cc.move_to(-200, -120 + k * 44)
            cc.line_to(140, -120 + k * 44)
        _s(cc, "#8fb6ec", 3)
    # red string from the board
    c.move_to(-20, 330)
    c.curve_to(240, 360, 380, 356, 495, 350)
    c.curve_to(640, 342, 860, 290, 1100, 240)
    _s(c, "#c8283c", 5)
    with saved(c, PHOTO_C[0], PHOTO_C[1], PHOTO_S, -0.025) as cc:
        _photo_big(cc)
        circle(cc, 0, -PHOTO_H / 2 + 14, 13)                         # push pin
        _fs(cc, "danger", INK, 4)
        circle(cc, -4, -PHOTO_H / 2 + 9, 3.5)
        _f(cc, "white", 0.7)
    # night: dim + candle-warm vignette (static)
    c.set_source_rgba(0.05, 0.02, 0.12, 0.2)
    c.paint()
    g = cairo.RadialGradient(PHOTO_C[0], PHOTO_C[1], 460, PHOTO_C[0], PHOTO_C[1] + 15, 1150)
    g.add_color_stop_rgba(0, 0.04, 0.02, 0.08, 0.0)
    g.add_color_stop_rgba(1, 0.04, 0.02, 0.08, 0.55)
    c.set_source(g)
    c.paint()
    # the room is dark; only the rainy window's light reaches the board: the
    # board darkens OUTSIDE the arched light patch (soft edge), so the photo
    # itself stays crisp and clear
    c.push_group()
    c.set_source_rgba(0.03, 0.02, 0.1, 1.0)
    c.paint()
    c.set_operator(cairo.OPERATOR_DEST_OUT)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    for wdt, al in ((190, 0.22), (120, 0.25), (60, 0.3)):
        _window_light_path(c)
        c.set_source_rgba(0, 0, 0, al)
        c.set_line_width(wdt)
        c.stroke()
    _window_light_path(c)
    c.set_source_rgba(0, 0, 0, 1.0)
    c.fill()
    c.set_operator(cairo.OPERATOR_OVER)
    c.pop_group_to_source()
    c.paint_with_alpha(0.34)
    # a faint cool tint inside the light
    _window_light_path(c)
    c.set_source_rgba(0.55, 0.68, 1.0, 0.05)
    c.fill()
    # ...and droplets already sitting on the glass, round the photo's edges
    c.save()
    _window_light_path(c)
    c.clip()
    pw2, ph2 = PHOTO_W * PHOTO_S / 2 + 10, PHOTO_H * PHOTO_S / 2 + 10
    for i in range(34):
        x = 40 + hash01(i, 611) * 1000
        y = 200 + hash01(i, 612) * 1050
        if abs(x - PHOTO_C[0]) < pw2 and abs(y - PHOTO_C[1]) < ph2:
            continue
        _drop_shadow(c, x, y, 3.5 + 6.0 * hash01(i, 613), 0.8)
    c.restore()


def _drop_shadow(c, x, y, r, a=1.0, tail=0.0):
    """Shadow of a raindrop on the glass: dark rim, bright focused centre,
    optional fading streak above it (a drop that has been running)."""
    if tail > 0:
        for j in range(3):
            y0, y1 = y - tail * (j + 1) / 3, y - tail * j / 3
            c.move_to(x + 1.2 * math.sin(y0 * 0.05), y0)
            c.line_to(x + 1.2 * math.sin(y1 * 0.05), y1)
            _s(c, (0.05, 0.06, 0.18, 0.11 * a * (1 - j / 3) ** 0.2 * (0.5 + j / 4)),
               r * (0.55 + 0.12 * j))
    ellipse(c, x, y, r, r * 1.18)
    _f(c, (0.05, 0.06, 0.18, 0.24 * a))
    ellipse(c, x + r * 0.08, y + r * 0.12, r * 0.55, r * 0.62)
    _f(c, (0.9, 0.95, 1.0, 0.42 * a))


# rain trickling down the window: their shadows slide down the light patch
# (x lanes keep clear of the kid's face, the robot and the ribbon)
DRIPS = [(x, 40 + 50 * hash01(i, 622), 1100 * hash01(i, 623), 3.0 + 2.5 * hash01(i, 624))
         for i, x in enumerate((130, 225, 445, 535, 690, 780, 880, 60, 985))]


def _rain_shadows(c, t):
    """9 raindrop shadows (head + streak) trickling down, stick-slip, inside
    the window light. Small, low-contrast: atmosphere, never over the story."""
    c.save()
    _window_light_path(c)
    c.clip()
    span = 1180.0
    for i, (x0, v, ph, r) in enumerate(DRIPS):
        w = 1.6 + 0.9 * hash01(i, 625)
        yy = 190 + (ph + v * t + 0.55 * v / w * math.sin(w * t + i)) % span
        xx = x0 + (yy - PHOTO_C[1]) * RAIN_SHEAR + 3.0 * noise1(t * 0.6, 40 + i)
        _drop_shadow(c, xx, yy, r * 2.4, 1.2, tail=80 + 90 * hash01(i, 626))
    c.restore()


def _cameo_malvo(t, T):
    """Malvo's face while he looks at the photo: glistening eyes up at it, ONE
    sad slow blink (the lids stay heavy after it), then on "I noticed." his
    eyes lift toward the AI's voice (touched: the cut back picks this up)."""
    expr = _state(t, [
        (-1, "s11_teary_up"),
        (T["sad_blink"] + 0.3, "s11_teary", 0.5),
        (T["lift_eyes"], "s11_moved", 0.35),
    ])
    look = _keyv(t, [
        (-1, (0.72, -0.78)),                             # up at the photo
        (T["sad_blink"] + 0.42, (0.55, -0.5), 0.6),      # ...eyes sink a little
        (T["lift_eyes"], (0.95, -0.1), 0.3),             # "I noticed."
    ])
    blink = _slow_blink(t, T["sad_blink"], 0.22, 0.2, 0.3)
    if blink is None:
        blink = 0.0 if t < T["lift_eyes"] + 0.3 else None
    return expr, look, blink


def _photo_cameo(ctx, t, info, T):
    """Round picture-in-picture (the film's villain-cameo grammar) of Malvo,
    bottom-left under the photo, fading in once the photo has sat alone."""
    t_in = T["cam_in"]
    if t < t_in:
        return
    k = ease_out(seg(t, t_in, t_in + 0.45))
    a = smoothstep(seg(t, t_in, t_in + 0.4))
    cx, cy, r = CAMEO
    expr, look, blink = _cameo_malvo(t, T)
    _e, _a, _lk, _bl, lean, dy, _p = _malvo(t, T)
    hs = _hissy(t, T)
    with saved(ctx, cx, cy, 0.9 + 0.1 * k, alpha_=a) as c:
        c.save()
        circle(c, 0, 0, r)
        c.clip()
        with saved(c, 0, 0, r / CAMEO_VIEW) as cc:
            cc.translate(-CAMEO_LOOK_AT[0], -CAMEO_LOOK_AT[1])
            P.lair_bg(cc, t, rain=True)
            cc.set_source_rgba(0.05, 0.02, 0.12, 0.25)            # night wash
            cc.paint()
            radial_glow(cc, FACE[0] + 120, FACE[1] + 10, 380, "ai_glow", 0.12)
            draw_villain(cc, MX, MY + dy, MS, t, expr=expr, look=look, mouth=(0, 0),
                         arms="rest", lean=lean, blink=blink, snake=hs)
        c.restore()
        circle(c, 0, 0, r)
        fill_stroke(c, None, "bubble_villain", 12)
        circle(c, 0, 0, r + 6)
        fill_stroke(c, None, "ink", 4)


def _shot_photo(ctx, t, info, T):
    """The science-fair photo, held through the whole pause: a slow gentle
    push-in, rain trickling down the window light, Malvo's PiP."""
    u = seg(t, T["photo"], T["back"])
    k = 1.0 + PHOTO_PUSH * ease_in_out(u)
    cx, cy = PHOTO_CAM
    with saved(ctx, cx, cy, k) as c:
        c.translate(-cx, -cy)
        P._cached_layer(c, "s11_cork", _cork_layer, rect=(-60, -80, 1200, 2080), opaque=True)
        _rain_shadows(c, t)
    _photo_cameo(ctx, t, info, T)


# ---------------------------------------------------------------------------
# the character sheet (6.16)
# ---------------------------------------------------------------------------
ROWS = ("CLEVER", "SKEPTICAL", "PERSISTENT")


def _sheet(ctx, t, T):
    t_in = T["back"] + 0.04
    if t < t_in:
        return
    k_in = ease_out_back(seg(t, t_in, t_in + 0.3), 2.0)
    k_out = 1.0
    if t >= T["wall"]:
        k_out = 1 - ease_in(seg(t, T["wall"], T["wall"] + 0.3))
    if k_out <= 0.01:
        return
    a = clamp((t - t_in) / 0.08) * k_out
    s = (0.3 + 0.7 * k_in) * (0.9 + 0.1 * k_out)
    cx, cy = SHEET_C[0], SHEET_C[1]
    with saved(ctx, cx, cy + SHEET_H / 2, s, 0.0, alpha_=a) as c:
        c.translate(0, -SHEET_H / 2)
        w, h = SHEET_W, SHEET_H
        gold = t >= T["flip"] + 0.08                    # IMPRESSIVE! has landed
        # pointer toward his head + panel
        poly(c, [(-22, h / 2 - 4), (22, h / 2 - 4), (0, h / 2 + 26)])
        _fs(c, "ui_panel", "ai_accent" if gold else "ai_rim", 6)
        rrect(c, -w / 2 + 6, -h / 2 + 8, w, h, 22)
        _f(c, (0, 0, 0, 0.3))
        rrect(c, -w / 2, -h / 2, w, h, 22)
        _fs(c, "ui_panel", "ai_accent" if gold else "ai_rim", 6)
        poly(c, [(-20, h / 2 - 7), (20, h / 2 - 7), (0, h / 2 + 20)])
        _f(c, "ui_panel")
        # header: VILLAIN STATS (it stays!); a proud pulse on "villain"
        hp = math.sin(math.pi * seg(t, T["w_villain4"], T["w_villain4"] + 0.32))
        with saved(c, 0, -h / 2 + 46, 1.0 + 0.14 * hp) as ch:
            text(ch, "VILLAIN STATS", 0, 15, 44, "warn", "comic", outline="ink", outline_w=8)
        c.move_to(-w / 2 + 24, -h / 2 + 76)
        c.line_to(w / 2 - 24, -h / 2 + 76)
        _s(c, "ai_rim", 3, 0.5)
        # rows: each label pops in ON its word (a dim slot until then), then
        # its five bars fill
        lab_x0, lab_x1 = -w / 2 + 24, w / 2 - 26 - 5 * 32 - 2      # label column
        for i, lab in enumerate(ROWS):
            ry = -h / 2 + 112 + i * 50
            t0, dur = T["rows"][i], T["row_dur"][i]
            if t < t0:                                   # empty stat slot
                rrect(c, lab_x0 + 2, ry - 4, 70, 8, 4)
                _f(c, "ai_rim", 0.28)
            else:
                lk = ease_out_back(seg(t, t0, t0 + 0.22), 2.6)
                fs = 30
                while fs > 20 and text_width(c, lab, "ui", fs) > lab_x1 - lab_x0:
                    fs -= 1
                with saved(c, lab_x0, ry, max(0.01, 0.35 + 0.65 * lk)) as cl:
                    text(cl, lab, 0, 11, fs, "white", "ui", "left")
                fl = 1 - seg(t, t0 + 0.04, t0 + 0.3)     # pop flash
                if fl > 0.01:
                    rrect(c, lab_x0 - 8, ry - 20, lab_x1 - lab_x0 + 14, 40, 10)
                    _f(c, "ai_accent", 0.24 * fl)
            t0 += 0.08                                   # bars fill right after the label
            for j in range(5):
                bx = w / 2 - 26 - (5 - j) * 32 + 4
                tj = t0 + dur * j / 5
                fk = ease_out_back(seg(t, tj, tj + 0.16), 2.4)
                rrect(c, bx, ry - 15, 24, 30, 7)
                _fs(c, "#2c2c40", "#55557a", 3)
                if fk > 0.01:
                    with saved(c, bx + 12, ry, fk) as cb:
                        rrect(cb, -12, -15, 24, 30, 7)
                        _fs(cb, "ai_accent", "ink", 3)
                        rrect(cb, -7, -11, 6, 12, 3)
                        _f(cb, "white", 0.55)
        # a shine sweep over the bars right after the badge lands
        if T["flip"] + 0.15 <= t <= T["flip"] + 0.75:
            u = seg(t, T["flip"] + 0.15, T["flip"] + 0.75)
            c.save()
            rrect(c, -w / 2, -h / 2, w, h, 22)
            c.clip()
            xx = lerp(-w / 2 - 60, w / 2 + 60, ease_in_out(u))
            poly(c, [(xx - 20, -h / 2), (xx + 20, -h / 2), (xx - 30, h / 2), (xx - 70, h / 2)])
            _f(c, "white", 0.22)
            c.restore()
        _impressive_badge(c, t, T, w / 2 - 104, -h / 2 - 16)
    if T["flip"] <= t <= T["wall"]:
        k = smoothstep(seg(t, T["flip"], T["flip"] + 0.2)) * \
            (1 - smoothstep(seg(t, T["flip"] + 1.0, T["flip"] + 1.6)))
        if k > 0.01:
            P.sparkles(ctx, SHEET_C[0], SHEET_C[1] - 10, 250, t, n=6, seed=5,
                       color="ai_accent", size=0.8 * k)


def _impressive_badge(c, t, T, x, y):
    """Gold 'IMPRESSIVE!' badge slammed onto the sheet's top-right corner on
    "impressive" (sheet-local coords; fades with the sheet)."""
    t0 = T["flip"]
    if t < t0:
        return
    d = t - t0
    hit = 0.1
    if d < hit:                                        # drops in big, with a twist
        q = ease_in(d / hit)
        sc, rot = lerp(2.2, 0.9, q), 0.12 - 0.4 * (1 - q)
    else:
        sc, rot = 0.9 + 0.1 * ease_out_back(seg(d, hit, hit + 0.28), 3.2), 0.12
    a = clamp(d / 0.05)
    with saved(c, x, y, sc, rot, alpha_=a) as cb:
        P.label_tag(cb, 0, 0, "IMPRESSIVE!", color="ai_accent", size=40, text_color="ink",
                    font="comic")
        P._star4(cb, -128, -24, 12, 0.3)
        _fs(cb, "white", INK, 2.5)
        P._star4(cb, 126, 22, 9, 0.2)
        _fs(cb, "white", INK, 2)
    k = seg(t, t0 + hit, t0 + hit + 0.24)               # impact ticks
    if 0 < k < 1:
        for i in range(8):
            ang = i / 8 * 2 * math.pi + 0.2
            r0, r1 = 70 + 40 * k, 86 + 64 * k
            c.move_to(x + math.cos(ang) * r0 * 1.6, y + math.sin(ang) * r0 * 0.7)
            c.line_to(x + math.cos(ang) * r1 * 1.6, y + math.sin(ang) * r1 * 0.7)
        _s(c, "ai_accent", 5, 1 - k)


# ---------------------------------------------------------------------------
# hologram: wall + door (cyan-tinted group) and the warm door light
# ---------------------------------------------------------------------------
AJAR_SX = 0.84                            # panel scale-x while the door is ajar


def _ajar_k(t, T):
    return ease_out(seg(t, T["ajar"], T["ajar"] + 0.3))


def _ajar_sx(t, T):
    """Panel scale-x before the big swing: cracks ajar, nudges as each chip squeezes out."""
    sx = lerp(1.0, AJAR_SX, _ajar_k(t, T))
    for tc in T["chips"]:
        sx -= 0.035 * math.sin(math.pi * seg(t, tc - 0.02, tc + 0.22))
    return sx


def _door_k(t, T):
    """0 closed .. 1 open (panel scale-x 1 -> 0.15 around the hinge)."""
    u = seg(t, T["open"], T["open"] + 0.4)
    return ease_out_back(u, 1.3) if u > 0 else 0.0


def _door_xf(c, k_in):
    """Pop-in transform for the door unit (squash/stretch from its base)."""
    dx, dy, dw, dh = DOOR
    c.translate(dx + dw / 2, dy + dh)
    c.scale(max(0.01, k_in), 1.0 + 0.2 * (1 - k_in))
    c.translate(-(dx + dw / 2), -(dy + dh))


def _door_frame(c, k_in):
    """Brick lintel + jamb round the doorway (inside the cyan hologram group)."""
    dx, dy, dw, dh = DOOR
    if k_in <= 0.01:
        return
    c.save()
    _door_xf(c, k_in)
    c.rectangle(dx, dy, dw, dh)
    _f(c, "#2a1c26")
    c.rectangle(dx - 12, dy - 30, dw + 42, 30)
    c.rectangle(dx + dw, dy, 30, dh)
    c.rectangle(dx - 12, dy, 12, dh)
    _f(c, "mortar")
    for i in range(3):
        P._brick_shape(c, dx - 12 + i * (dw + 42) / 3, dy - 30, (dw + 42) / 3, 30,
                       ("#b5523b", "#c05d44", "#a94a35")[i], 3.0)
    for i in range(5):
        P._brick_shape(c, dx + dw, dy + i * dh / 5, 30, dh / 5,
                       ("#c05d44", "#a94a35", "#b5523b")[i % 3], 3.0)
    c.rectangle(dx, dy, dw, dh)
    _s(c, INK, 5)
    c.restore()


def _door_panel(c, t, T, k_in):
    """The wooden door itself (hinge = its left edge). Drawn OUTSIDE the cyan
    tint so it stays warm brown: the door is the warm thing in this film."""
    dx, dy, dw, dh = DOOR
    if k_in <= 0.01:
        return
    ok = _door_k(t, T)
    sxk = _ajar_sx(t, T)
    if ok > 0:
        sxk = lerp(AJAR_SX, 0.15, clamp(ok)) if ok <= 1.0 else 0.15 - (ok - 1.0) * 0.4
    c.save()
    _door_xf(c, k_in)
    with saved(c, dx, dy, (max(0.06, sxk), 1.0)) as cp:
        rrect(cp, 0, 0, dw, dh, 6)
        _fs(cp, DOOR_COL, INK, 5)
        for k in range(1, 4):
            cp.move_to(k * dw / 4, 8)
            cp.line_to(k * dw / 4, dh - 8)
        _s(cp, DOOR_DK, 4)
        cp.rectangle(dw * 0.62, 6, dw * 0.38 - 6, dh - 12)
        _f(cp, DOOR_DK, 0.35)
        for yy in (dh * 0.22, dh * 0.78):          # iron straps + hinges
            cp.rectangle(6, yy - 7, dw - 30, 14)
            _fs(cp, "#4a3a34", INK, 3)
            circle(cp, 14, yy, 5)
            _f(cp, "#8a7a74")
        cp.move_to(10, 12)
        cp.line_to(10, dh * 0.5)
        _s(cp, DOOR_HI, 4)
        circle(cp, dw - 26, dh * 0.53, 11)          # gold knob
        _fs(cp, "gold", INK, 4)
        circle(cp, dw - 29, dh * 0.53 - 3, 3)
        _f(cp, "white", 0.7)
    if sxk < 0.6:                                   # the door's edge, seen side-on
        ex = dx + dw * max(0.06, sxk)
        th = 14 * smoothstep((0.6 - sxk) / 0.4)
        rrect(c, ex - 2, dy + 2, th + 2, dh - 4, 3)
        _fs(c, DOOR_DK, INK, 4)
    c.restore()


FIELD = (112.0, 174.0, 690.0, 388.0)      # projection field behind the hologram


def _holo_alpha(t, T):
    on = seg(t, T["holo"], T["holo"] + 0.3)
    flick = 1.0
    lt = t - T["holo"]
    if lt < 0.3:
        flick = 0.55 + 0.45 * (1 if math.sin(lt * 70) > -0.3 else 0)
    return 0.92 * smoothstep(on) * flick


def _holo_beam(ctx, t, T, ai_hand):
    """Projection beam from the AI's hand up to the hologram's base. Drawn
    BEFORE Malvo so it passes behind his head (in front it read as a cyan
    smudge across his dome)."""
    if t < T["holo"]:
        return
    alpha = _holo_alpha(t, T)
    base_y = WALL[1] + WALL[3]
    fx, fy, fw, fh = FIELD
    hx, hy = ai_hand
    poly(ctx, [(hx, hy), (fx + 30, base_y + 8), (fx + fw - 10, base_y + 8)])
    g = cairo.LinearGradient(hx, hy, hx - 150, base_y)
    g.add_color_stop_rgba(0, 0.37, 0.9, 1.0, 0.0)
    g.add_color_stop_rgba(1, 0.37, 0.9, 1.0, 0.18 * alpha)
    ctx.set_source(g)
    ctx.fill()


def _hologram(ctx, t, T):
    if t < T["holo"]:
        return
    alpha = _holo_alpha(t, T)
    wx, wy, ww, wh = WALL
    base_y = wy + wh
    fx, fy, fw, fh = FIELD
    # projection field: a dark glassy panel so the hologram reads over the lair
    pk = ease_out(seg(t, T["holo"], T["holo"] + 0.35))
    with saved(ctx, fx + fw / 2, fy + fh / 2, (pk, 0.15 + 0.85 * pk)) as c:
        rrect(c, -fw / 2, -fh / 2, fw, fh, 18)
        _fs(c, (0.03, 0.07, 0.16, 0.68 * alpha), "ai_rim", 4, a=0.55 * alpha)
        for sx in (-1, 1):                                   # HUD corner brackets
            for sy in (-1, 1):
                x0, y0 = sx * (fw / 2 - 6), sy * (fh / 2 - 6)
                c.move_to(x0, y0 - sy * 34)
                c.line_to(x0, y0)
                c.line_to(x0 - sx * 34, y0)
                _s(c, "ai_rim", 6, 0.9 * alpha)
    ctx.save()
    ctx.rectangle(*HOLO)
    ctx.clip()
    ctx.push_group()
    # base plate line
    cx = (wx + DOOR[0] + DOOR[2] + 30) / 2
    half = (DOOR[0] + DOOR[2] + 30 - wx) / 2 + 20
    rrect(ctx, cx - half * pk, base_y - 2, 2 * half * pk, 12, 6)
    _fs(ctx, "ai_rim", INK, 3)
    # ghost outline of where the wall goes (until the bricks arrive)
    ga = 1 - seg(t, T["wall0"] + 0.4, T["wall0"] + 0.9)
    if ga > 0.01 and pk > 0.5:
        ctx.set_dash([14, 10], (t * 40) % 24)
        ctx.rectangle(wx, wy, ww, wh)
        _s(ctx, "ai_rim", 4, ga)
        ctx.set_dash([], 0)
    P.brick_wall(ctx, wx, wy, ww, wh, t, T["wall0"], rows=WALL_ROWS, drop=WALL_DROP)
    if T["w_hurting"] <= t < T["w_hurting"] + 0.7:      # "Hurting people isn't.": wall glints
        pk_ = math.sin(math.pi * seg(t, T["w_hurting"], T["w_hurting"] + 0.7))
        ctx.rectangle(wx, wy, ww, wh)
        _f(ctx, "white", 0.16 * pk_)
        ctx.rectangle(wx - 4, wy - 4, ww + 8, wh + 8)
        _s(ctx, "ai_rim", 8, 0.9 * pk_)
    k_in = ease_out_back(seg(t, T["door_in"], T["door_in"] + 0.35), 1.8)
    _door_frame(ctx, k_in)
    # cyan hologram tint + static scanlines (only on drawn pixels)
    ctx.set_operator(cairo.OPERATOR_ATOP)
    ctx.set_source_rgba(0.37, 0.9, 1.0, 0.24)
    ctx.paint()
    for yy in range(int(HOLO[1]) + 4, int(HOLO[1] + HOLO[3]), 12):
        ctx.rectangle(HOLO[0], yy, HOLO[2], 3)
    ctx.set_source_rgba(0.75, 0.97, 1.0, 0.1)
    ctx.fill()
    ctx.set_operator(cairo.OPERATOR_OVER)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)
    ctx.restore()
    # light leaking round the closed door ("Everything else?")
    dx, dy, dw, dh = DOOR
    if T["leak"] <= t < T["open"] + 0.15 and k_in > 0.9:
        lk = smoothstep(seg(t, T["leak"], T["leak"] + 0.6)) * (1 + 0.15 * math.sin(t * 9))
        lk *= 1 - smoothstep(seg(t, T["open"], T["open"] + 0.15))
        rrect(ctx, dx - 2, dy - 2, dw + 4, dh + 4, 6)
        _s(ctx, DOORWAY, 22, 0.35 * lk)
        rrect(ctx, dx - 2, dy - 2, dw + 4, dh + 4, 6)
        _s(ctx, DOORWAY, 9, 0.9 * lk)
        ctx.move_to(dx + dw - 2, dy + 8)                       # bright latch-side crack
        ctx.line_to(dx + dw - 2, dy + dh - 4)
        ctx.line_to(dx + 8, dy + dh - 2)
        _s(ctx, "white", 5, 0.95 * lk)
        for j in range(5):                                      # little rays
            yy = dy + 40 + j * 55
            ln = 22 + 10 * math.sin(t * 6 + j)
            ctx.move_to(dx + dw + 34, yy)
            ctx.line_to(dx + dw + 34 + ln, yy - 4)
        _s(ctx, DOORWAY, 6, 0.7 * lk)
    # warm doorway light (behind the swinging panel)
    _doorway(ctx, t, T)
    # the door panel, warm, barely tinted
    if k_in > 0.01:
        ctx.save()
        ctx.rectangle(*HOLO)
        ctx.clip()
        ctx.push_group()
        _door_panel(ctx, t, T, k_in)
        ctx.set_operator(cairo.OPERATOR_ATOP)
        ctx.set_source_rgba(0.37, 0.9, 1.0, 0.08)
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVER)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(min(1.0, alpha / 0.92))
        ctx.restore()


def _doorway(ctx, t, T):
    ok = _door_k(t, T)
    if ok <= 0.0:
        ak = _ajar_k(t, T)
        if ak > 0.0:                                    # the bright gap of the ajar door
            dx, dy, dw, dh = DOOR
            ctx.rectangle(dx + dw * 0.5, dy, dw * 0.5, dh)
            _f(ctx, DOORWAY, ak)
        return
    # light is already leaking round the door, so the gap is bright at once
    # (a slower fade showed 3-4 grey frames of the dark tinted doorway)
    k = smoothstep(seg(t, T["open"], T["open"] + 0.08))
    dx, dy, dw, dh = DOOR
    ctx.rectangle(dx, dy, dw, dh)
    _f(ctx, DOORWAY, k)
    rrect(ctx, dx + 22, dy + 26, dw - 44, dh - 44, 20)
    _f(ctx, "white", 0.55 * k * (0.85 + 0.15 * math.sin(t * 5)))
    for j in range(5):                                  # soft rays inside the doorway
        a = -0.5 + j * 0.25
        ctx.move_to(dx + dw / 2, dy + dh * 0.95)
        ctx.line_to(dx + dw / 2 + math.sin(a) * 260, dy + dh * 0.95 - math.cos(a) * 260)
    ctx.save()
    ctx.rectangle(dx, dy, dw, dh)
    ctx.clip()
    _s(ctx, "white", 10, 0.35 * k)
    ctx.restore()


def _door_light(ctx, t, T):
    """Golden beam spilling from the doorway down across Malvo's face."""
    ok = _door_k(t, T)
    if ok <= 0.0:
        return 0.0
    k = smoothstep(seg(t, T["open"], T["open"] + 0.45))
    dx, dy, dw, dh = DOOR
    gap0 = dx + dw * max(0.06, lerp(AJAR_SX, 0.15, clamp(ok)))
    pts = [(gap0 + 2, dy + 4), (dx + dw - 2, dy + 24), (dx + dw - 26, dy + dh - 2),
           (FACE[0] + 230, 1070), (FACE[0] - 270, 910)]
    poly(ctx, pts)
    g = cairo.LinearGradient(dx + dw / 2, dy + dh * 0.6, FACE[0] - 20, 1040)
    acc = hexc("ai_accent")
    g.add_color_stop_rgba(0, acc[0], acc[1], acc[2], 0.5 * k)
    g.add_color_stop_rgba(0.55, acc[0], acc[1], acc[2], 0.34 * k)
    g.add_color_stop_rgba(1, acc[0], acc[1], acc[2], 0.0)
    ctx.set_source(g)
    ctx.fill()
    P.sparkles(ctx, dx + dw * 0.5, dy + dh * 0.5, 80, t, n=4, seed=31, color="white",
               size=0.6 * k)
    return k


# ---------------------------------------------------------------------------
# l07: three glowing chips squeeze out of the ajar door, one per named thing
# ---------------------------------------------------------------------------
CHIP_W, CHIP_H = 160.0, 130.0
CHIP_SRC = (DOOR[0] + DOOR[2] * 0.92, DOOR[1] + DOOR[3] * 0.48)
# (label line 1, line 2, slot x, slot y, rot)
CHIPS = [
    ("SCARY", "STORIES", 830.0, 228.0, -0.05),
    ("CREATIVE", "PLANS", 836.0, 372.0, 0.04),
    ("SOUND THE", "ALARM", 828.0, 516.0, -0.03),
]
SPOOK_BOOK, SPOOK_BOOK_DK = "#6b3fa0", "#4a2a74"


def _icon_storybook(c):
    """A spooky storybook: purple cover, a little ghost, a bat doodle."""
    with saved(c, 0, 0, 1.0, -0.08) as b:
        rrect(b, -30, -24, 66, 50, 5)                 # page block
        _fs(b, "#fbf3dc", INK, 3)
        rrect(b, -36, -28, 66, 52, 6)                 # cover
        _fs(b, SPOOK_BOOK, INK, 3.5)
        b.rectangle(-36, -28, 11, 52)                 # spine
        _f(b, SPOOK_BOOK_DK)
        b.rectangle(-36, -28, 11, 52)
        _s(b, INK, 3)
        # ghost
        b.move_to(-10, 14)
        b.line_to(-10, -6)
        b.curve_to(-10, -24, 18, -24, 18, -6)
        b.line_to(18, 14)
        for k in range(4):
            x0 = 18 - k * 7
            b.curve_to(x0 - 1, 9, x0 - 6, 9, x0 - 7, 14)
        b.close_path()
        _fs(b, "white", INK, 2.5)
        for ex in (-1.0, 9.0):
            ellipse(b, ex, -6, 2.6, 3.6)
            _f(b, INK)
        ellipse(b, 4, 4, 3, 2.4)
        _f(b, INK)


BP, BP_DK, BP_LN = "#2f6fd6", "#1f4fa6", "#7fa8ee"          # blueprint blue
BULB, BULB_OFF = "#ffe066", "#f3ead2"
BELL, BELL_DK, BELL_RIM = "#e23b2e", "#a8231b", "#c42a20"


def _icon_plans(c, t=0.0, lit=1.0):
    """CREATIVE PLANS: a villain's rolled-up blueprint-style plan (half
    unrolled, a dashed arrow, an X, a star doodle) with a lightbulb popping on
    at its corner. Cartoony scheme doodles, nothing technical."""
    with saved(c, -6, 5, 1.0, -0.06) as b:
        rrect(b, -30, -20, 64, 40, 3)                     # the unrolled sheet
        _fs(b, BP, INK, 3)
        b.save()
        rrect(b, -30, -20, 64, 40, 3)
        b.clip()
        for yy in (-8, 4, 16):                            # faint grid
            b.move_to(-30, yy)
            b.line_to(34, yy)
        for xx in (-14, 2, 18):
            b.move_to(xx, -20)
            b.line_to(xx, 20)
        _s(b, BP_LN, 1.4, 0.55)
        b.restore()
        b.set_dash([4.5, 4], 0)                           # dashed scheme arrow
        b.move_to(-20, 12)
        b.curve_to(-14, -14, 6, -12, 12, 2)
        _s(b, "white", 2.6)
        b.set_dash([], 0)
        poly(b, [(9, -3), (17, 1), (10, 7)])
        _f(b, "white")
        for d in (-1, 1):                                 # X marks the plan
            b.move_to(19, 8 - 5 * d)
            b.line_to(27, 8 + 5 * d)
        _s(b, "white", 2.6)
        P._star4(b, -20, -10, 5)
        _f(b, "white", 0.9)
        rrect(b, -40, -23, 14, 46, 6)                     # the rolled-up end
        _fs(b, BP_DK, INK, 3)
        ellipse(b, -33, -23, 7, 3.2)
        _fs(b, BP, INK, 2.5)
        circle(b, -33, -23, 1.6)
        _f(b, INK)
    # lightbulb popping on at the corner
    bx, by = 33, -16
    if lit > 0.02:
        circle(c, bx, by, 19 * (0.8 + 0.2 * lit))
        _f(c, "ai_accent", 0.28 * lit)
        for k in range(5):
            a = -math.pi / 2 + (k - 2) * 0.62
            c.move_to(bx + math.cos(a) * 14, by + math.sin(a) * 14)
            c.line_to(bx + math.cos(a) * (19 + 3 * lit), by + math.sin(a) * (19 + 3 * lit))
        _s(c, "ai_accent", 2.6, lit)
    rrect(c, bx - 5, by + 7, 10, 8, 2)
    _fs(c, "#a9aec0", INK, 2.2)
    circle(c, bx, by, 10)
    _fs(c, core.mixc(BULB_OFF, BULB, clamp(lit)), INK, 2.6)
    ellipse(c, bx - 3, by - 3, 2.5, 3.5, 0.4)
    _f(c, "white", 0.85)


def _icon_alarm(c, t=0.0, ring=0.0):
    """SOUND THE ALARM: a big red alarm bell with motion lines; it shakes
    while it rings (ring 0..1)."""
    rr = 0.6 + 0.4 * clamp(ring)
    for sx in (-1, 1):                                    # motion lines
        for k in range(2):
            r = 36 + 9 * k + 2.5 * math.sin(t * 30 + k)
            c.arc(0, 0, r, (-0.5 if sx > 0 else math.pi - 0.5),
                  (0.5 if sx > 0 else math.pi + 0.5))
            _s(c, "white", 3.2, (1.0 - 0.3 * k) * rr)
            c.new_path()
    ang = 0.2 * math.sin(t * 38.0) * clamp(ring) + 0.04 * math.sin(t * 7.0)
    with saved(c, 0, -27, 1.15, ang) as b:                # pivots at the mount
        rrect(b, -6, -6, 12, 8, 3)                        # mount knob
        _fs(b, "#a9aec0", INK, 2.5)
        cl = -ang * 1.6                                   # clapper swings the other way
        circle(b, math.sin(cl) * 6, 47, 5.5)
        _fs(b, STAR_GOLD, INK, 2.5)

        def dome():
            b.move_to(-25, 38)
            b.curve_to(-25, 14, -20, 2, 0, 2)
            b.curve_to(20, 2, 25, 14, 25, 38)
            b.close_path()
        dome()
        _fs(b, BELL, INK, 3)
        b.save()
        dome()
        b.clip()
        ellipse(b, 15, 22, 11, 22)
        _f(b, BELL_DK, 0.7)
        b.restore()
        ellipse(b, -11, 16, 3.5, 8, 0.35)                 # highlight
        _f(b, "white", 0.75)
        rrect(b, -30, 35, 60, 9, 4.5)                     # rim
        _fs(b, BELL_RIM, INK, 3)


def _chip_pose(t, T, i):
    """(x, y, scale, alpha) of chip i, or None."""
    t0 = T["chips"][i]
    if t < t0 or t >= T["chip_out"] + 0.3:
        return None
    _, _, tx, ty, _ = CHIPS[i]
    u = seg(t, t0, t0 + T["chip_fly"])
    e = ease_out(u)
    cx_, cy_ = CHIP_SRC[0] + 40, min(CHIP_SRC[1], ty) - 70
    x = (1 - e) ** 2 * CHIP_SRC[0] + 2 * (1 - e) * e * cx_ + e * e * tx
    y = (1 - e) ** 2 * CHIP_SRC[1] + 2 * (1 - e) * e * cy_ + e * e * ty
    y += 4 * math.sin((t - t0) * 2.3 + i * 1.7) * smoothstep(u)       # gentle hover
    sc = lerp(0.15, 1.0, ease_out_back(seg(t, t0, t0 + 0.32), 2.2))
    a = clamp((t - t0) / 0.06)
    if t >= T["chip_out"]:                            # bow out for the gift pile
        v = seg(t, T["chip_out"] + 0.06 * i, T["chip_out"] + 0.06 * i + 0.22)
        sc *= 1 - 0.5 * ease_in(v)
        a *= 1 - v
    if a <= 0.01:
        return None
    return x, y, sc, a


def _chips(ctx, t, T):
    for i in range(len(CHIPS)):
        pose = _chip_pose(t, T, i)
        if pose is None:
            continue
        x, y, sc, a = pose
        l1, l2, _, _, rot = CHIPS[i]
        t0 = T["chips"][i]
        if t < t0 + T["chip_fly"] + 0.1:              # one trailing sparkle
            tr = _chip_pose(max(t0, t - 0.08), T, i)
            if tr is not None:
                k = 1 - seg(t, t0 + T["chip_fly"], t0 + T["chip_fly"] + 0.1)
                P._star4(ctx, tr[0] - 20, tr[1] + 10, 12 * k, t * 4 + i)
                P._f(ctx, "ai_accent", 0.9 * k * a)
        glow = 0.55 + 0.25 * math.sin((t - t0) * 3.0 + i)
        flash = 1 - seg(t, t0, t0 + 0.35)
        with saved(ctx, x, y, sc, rot * smoothstep(seg(t, t0, t0 + 0.3)), alpha_=a) as c:
            w, h = CHIP_W, CHIP_H
            rrect(c, -w / 2 - 6, -h / 2 - 6, w + 12, h + 12, 24)      # soft gold halo
            _s(c, "ai_accent", 12, 0.22 * glow + 0.4 * flash)
            rrect(c, -w / 2, -h / 2, w, h, 18)
            _fs(c, (0.06, 0.09, 0.2, 0.94), "ai_accent", 4.5)
            rrect(c, -w / 2 + 8, -h / 2 + 8, w - 16, 64, 12)           # icon well
            _f(c, (1.0, 0.85, 0.45, 0.16 + 0.3 * flash))
            with saved(c, 0, -h / 2 + 40, 1.0) as ci:
                if i == 0:
                    _icon_storybook(ci)
                elif i == 1:                          # the bulb pops on: an idea!
                    lit = smoothstep(seg(t, t0 + 0.12, t0 + 0.24))
                    lit *= 0.85 + 0.15 * math.sin(t * 6.0)
                    _icon_plans(ci, t, lit)
                else:                                 # rings on "sounding" .. "alarm"
                    ring = max(1 - seg(t, t0 + 0.6, t0 + 1.0),
                               1 - seg(t, T["w_alarm"] + 0.45, T["w_alarm"] + 0.85)
                               if t >= T["w_alarm"] else 0.0)
                    _icon_alarm(ci, t, ring)
            for j, lab in enumerate((l1, l2)):
                fs = 24
                while fs > 16 and text_width(c, lab, "ui", fs) > w - 22:
                    fs -= 1
                text(c, lab, 0, 30 + j * 27, fs, "ai_accent" if j == 0 else "white", "ui")
            if flash > 0.01:
                rrect(c, -w / 2, -h / 2, w, h, 18)
                _f(c, "white", 0.35 * flash)


# ---------------------------------------------------------------------------
# the gift pile
# ---------------------------------------------------------------------------
BOOK_S = 1.3                    # big enough that its title reads in his arms
BOOK_DEST = (MX + 6, MY - 228 * MS + 18)
# (kind, target x, target y, final scale, final rot)
# (s12's opening lair shot draws this exact pile; keep the numbers in sync)
GIFTS = [
    ("notebook", MX - 166, 1156.0, 0.95, -0.1),
    ("phones", MX + 128, 1206.0, 1.12, 0.12),
    ("scroll", MX - 120, 1212.0, 0.95, -0.12),
    ("book", BOOK_DEST[0], BOOK_DEST[1], BOOK_S, 0.05),
    ("twist", MX + 240, 1160.0, 0.95, 0.09),
]
SRC = (DOORWAY_C[0] + 8, DOORWAY_C[1] + 20)
CTRL = (585.0, 1010.0)          # flights drop down the gap between Malvo and the AI
CTRL_LO = (600.0, 1130.0)       # (left-bound gifts swoop in low, under his chin)


def _gift_pose(t, T, i):
    """(x, y, scale, rot, squash) of gift i, or None before it appears.
    Each gift pops forward out of the doorway, then drops along a curve down
    the gap between his face and the AI and swoops into place."""
    t0 = T["gift_t"][i]
    if t < t0:
        return None
    kind, tx, ty, ts, tr = GIFTS[i]
    fly = T["fly"]
    pop_k = ease_out_back(seg(t, t0, t0 + 0.12), 2.6)
    if t < t0 + fly:
        u = seg(t, t0 + 0.04, t0 + fly)
        e = math.sin(u * math.pi / 2) ** 1.15            # quick out of the door, settles in
        cx_, cy_ = CTRL_LO if tx < MX - 60 else CTRL
        x = (1 - e) ** 2 * SRC[0] + 2 * (1 - e) * e * cx_ + e * e * tx
        y = (1 - e) ** 2 * SRC[1] + 2 * (1 - e) * e * cy_ + e * e * ty
        y -= 46 * math.sin(math.pi * min(1.0, u * 2.5)) * (1 - u)   # little hop out
        s = lerp(0.6, 1.0, ease_out(u)) * ts * (0.3 + 0.7 * pop_k)
        rot = lerp(0.0, tr, e) + (0.5 if i % 2 else -0.5) * math.sin(math.pi * e)
        sq = -0.12 * math.sin(math.pi * e) + 0.22 * (1 - pop_k) * (t < t0 + 0.12)
        return (x, y, s, rot, sq)
    d = t - (t0 + fly)
    sq = 0.2 * math.exp(-d * 9) * math.cos(d * 26)               # landing squash
    if kind == "book":
        squeeze = 0.015 * math.sin(d * 2 * math.pi * 0.7)
        return (tx, ty, ts * (1 + squeeze), tr, sq)
    return (tx, ty, ts, tr, sq)


def _draw_gift(ctx, t, i, pose):
    kind = GIFTS[i][0]
    x, y, s, rot, sq = pose
    sx, sy = 1 + sq * 0.6, 1 - sq
    if kind == "notebook":
        with saved(ctx, x, y, (sx, sy)):
            draw_notebook(ctx, 0, 0, s, rot, t)
    elif kind == "phones":
        with saved(ctx, x, y, (sx, sy)):
            draw_headphones(ctx, 0, 0, s, rot)
    elif kind == "scroll":
        with saved(ctx, x, y, (sx, sy)):
            draw_scroll(ctx, 0, 0, s, rot)
    elif kind == "book":
        draw_space_lasers_book(ctx, x, y, s, t, rot, sq)
    elif kind == "twist":
        with saved(ctx, x, y, (sx, sy)):
            draw_twist_script(ctx, 0, 0, s, rot)


def _gift_trails(ctx, t, T):
    """A few sparkles following gifts in flight (<= 6 small particles)."""
    for i in range(len(GIFTS)):
        t0 = T["gift_t"][i]
        if t0 + 0.05 <= t <= t0 + T["fly"] + 0.15:
            pose = _gift_pose(t - 0.07, T, i)
            if pose is not None:
                k = 1 - seg(t, t0 + T["fly"], t0 + T["fly"] + 0.15)
                P._star4(ctx, pose[0], pose[1], 11 * k, t * 4 + i)
                P._f(ctx, "ai_accent", 0.85 * k)


def _newest_gift(t, T):
    """Index of the most recently launched gift still in flight (or last)."""
    idx = None
    for i, t0 in enumerate(T["gift_t"]):
        if t >= t0 - 0.02:
            idx = i
    return idx


# ---------------------------------------------------------------------------
# the spooky gifts (l08): the jack-o'-lantern + dragon onto the desk, the bat
# onto Hissy's head, the goblin mask onto Malvo's dome (pushed up; s12 keeps
# every one of them exactly here)
# ---------------------------------------------------------------------------
SP_ORDER = ("pumpkin", "bat", "mask", "dragon")
PUMPKIN_AT = (126.0, 1240.0, 0.95)        # bottom-centre on the desk (left end)
DRAGON_AT = (786.0, 1240.0, 1.02)         # bottom-centre on the desk (right end)
BAT_LOCAL = (22.0, -104.0, 0.95)            # perched on Hissy's head (snake-head local)
MASK_LOCAL = (0.0, -186.0, 0.86, -0.1)     # pushed up on his dome (face local)
SP_CTRL = {"pumpkin": (600.0, 1130.0), "bat": (300.0, 400.0), "mask": (560.0, 330.0),
           "dragon": (470.0, 900.0)}
SP_SPIN = {"pumpkin": -0.6, "bat": 0.3, "mask": 0.8, "dragon": 0.45}


def _snake_head_xf(ctx, x, y, s, t, expr, seed=5):
    """Apply Hissy's head transform (exactly as draw_snake_head does)."""
    p = SN.resolve_expr(expr)
    nod = p["nod"]
    nod_phase = math.sin(t * 2 * math.pi * 1.6)
    nod_dy = nod * (max(0.0, nod_phase) * 16 - 3)
    nod_rot = nod * 0.09 * max(0.0, nod_phase)
    bob = math.sin(t * 2 * math.pi * 0.45 + seed) * 2.5
    sway = noise1(t * 0.6, seed + 3) * 0.035
    wob = p["wob"] * math.sin(t * 2 * math.pi * 7) * 0.02
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.translate(0, p["hy"] + bob + nod_dy)
    ctx.rotate(p["tilt"] + sway + nod_rot + wob)
    sq = p["sq"]
    if sq != 1.0:
        ctx.scale(1 / math.sqrt(sq), sq)
    return p


def _xf_villain(c, dy, lean):
    c.translate(MX, MY + dy)
    c.scale(MS, MS)
    if lean:
        c.rotate(lean)


def _xf_face(c, st, dy, lean):
    _xf_villain(c, dy, lean)
    c.translate(V.NECK[0], V.NECK[1] + st["head_dy"])
    c.rotate(st["head_rot"])
    c.translate(0, V.FACE_OFF)


def _xf_hissy(c, t, st, dy, lean, sexpr):
    _xf_villain(c, dy, lean)
    _snake_head_xf(c, V.SNAKE_HEAD[0], V.SNAKE_HEAD[1] + st["shy"] * 0.6 - st["breath"] * 1.5,
                   V.SNAKE_SCALE, t, sexpr, seed=5)


def _local_to_user(ctx, xf, px, py):
    """User-space point of (px, py) drawn under the transform `xf(ctx)`."""
    ctx.save()
    xf(ctx)
    dx, dy = ctx.user_to_device(px, py)
    ctx.restore()
    return ctx.device_to_user(dx, dy)


def _land_sq(t, t_land, amp=0.22):
    d = t - t_land
    if d < 0 or d > 0.8:
        return 0.0
    return amp * math.exp(-d * 9) * math.cos(d * 26)


def _sp_world_scale(kind):
    return {"pumpkin": PUMPKIN_AT[2], "dragon": DRAGON_AT[2],
            "bat": BAT_LOCAL[2] * V.SNAKE_SCALE * MS, "mask": MASK_LOCAL[2] * MS}[kind]


def _sp_flight(t, T, kind, target):
    """(x, y, scale, rot) of a spooky gift in flight, or None (not launched /
    landed). `target` = where its anchor lands (user space, this frame)."""
    t0, t1 = T["sp_t"][kind], T["sp_land"][kind]
    if t < t0 or t >= t1:
        return None
    u = seg(t, t0 + 0.03, t1)
    e = math.sin(u * math.pi / 2) ** 1.15
    pop_k = ease_out_back(seg(t, t0, t0 + 0.12), 2.6)
    sx0, sy0 = SRC
    if kind in ("pumpkin", "dragon"):                 # bottom-centre anchors
        sy0 += 40
    cx_, cy_ = SP_CTRL[kind]
    tx, ty = target
    x = (1 - e) ** 2 * sx0 + 2 * (1 - e) * e * cx_ + e * e * tx
    y = (1 - e) ** 2 * sy0 + 2 * (1 - e) * e * cy_ + e * e * ty
    y -= 40 * math.sin(math.pi * min(1.0, u * 2.5)) * (1 - u)    # little hop out
    sc = (lerp(0.7, 1.0, ease_out(u)) + 0.45 * math.sin(math.pi * u)) * \
        _sp_world_scale(kind) * (0.3 + 0.7 * pop_k)
    rot = SP_SPIN[kind] * math.sin(math.pi * e)
    return (x, y, sc, rot)


# ---------------------------------------------------------------------------
# acting
# ---------------------------------------------------------------------------
def _dir(ox, oy, tx, ty, mag=0.95):
    dx, dy = tx - ox, ty - oy
    L = math.hypot(dx, dy) or 1.0
    return (dx / L * mag, dy / L * mag)


def _malvo(t, T):
    beat = T["beat"]
    expr = _state(t, [
        (-1, "s11_slump"),
        (T["lift"], "s11_low", 0.5),                     # "Evil Genius": head comes up
        (T["w_every1"] + 0.25, "s11_frown", 0.45),       # "...helps me protect people"?
        (T["w_heroic"] + 0.02, "s11_aghast", 0.14),      # "heroic"?!
        (T["l1b"] + 0.02, "s11_ugh", 0.16),              # "Heroic? Ugh!" disgust
        (T["cross"], "s11_hmph", 0.22),                  # arms cross, nose up, away
        (T["peek"], "s11_peek", 0.16),                   # "...amazing villain": peek
        (T["unpeek"], "s11_hmph", 0.12),                 # ...snap, shut again
        (T["turn_back"], "s11_smug", 0.3),               # "...That's what I thought."
        (T["nod_v"], "s11_smug_nod", 0.13),              # begrudging little nod
        (T["nod_v"] + 0.15, "s11_smug", 0.2),
        (beat, "s11_down", 0.55),                        # bravado drains, monocle slips
        (T["l2"] + 0.15, "s11_teary", 0.4),
        (T["w_noticed"] - 0.05, "s11_teary_up", 0.2),    # lids lift: the photo
        (T["w_unless"], "s11_teary", 0.35),
        (T["back"], "s11_moved", 0.01),                  # (cut) touched, glistening
        (T["flip"] + 0.1, "s11_hope_m", 0.3),            # "impressive villain stats"
        (T["wow"], "s11_wow", 0.16),                     # ...Impressive?! monocle in
        (T["grin"], "s11_grin", 0.3),                    # a pleased evil grin
        (T["wall"] + 0.35, "s11_listen", 0.45),
        (T["chips"][0] + 0.1, "s11_hope", 0.4),          # ...scary stories? for me?
        (T["chips"][1] + 0.04, "s11_scheme", 0.25),      # creative plans! (hand rub)
        (T["chips"][2] + 0.08, "s11_hope", 0.3),
        (T["open"], "s11_wonder", 0.3),                  # golden light!
        (T["gift_t"][2], "s11_wonder2", 0.6),            # ...eyes getting wider
        (T["sp_t"]["pumpkin"] + 0.12, "s11_delight", 0.25),   # SPOOKY stuff? for me?!
        (T["sp_land"]["mask"] - 0.02, "s11_delight_up", 0.1),  # plop! (goblin mask)
        (T["sp_land"]["mask"] + 0.45, "s11_delight", 0.25),
        (T["w_hurting"] + 0.05, "s11_listen", 0.35),     # ...hurting people isn't.
        (T["smile"], "s11_smile", 0.9),                  # REAL SMILE spreads
    ])
    arms = _state(t, [
        (-1, "slump"),
        (T["lift"] + 0.1, "rest", 0.7),
        (T["cross"], "s11_cross", 0.25),                 # Ugh! arms folded
        (T["uncross"], "rest", 0.55),                    # ...relaxing
        (T["puff"] - 0.06, "s11_hips", 0.22),            # chest puffed, elbows out
        (T["wall"] + 0.3, "rest", 0.45),
        (T["chips"][1] - 0.02, "rub", 0.25),             # creative plans: hand rub
        (T["chips"][2] + 0.1, "rest", 0.35),
        (T["gift_t"][0] - 0.05, "s11_open", 0.3),
        (T["gift_t"][3] + T["fly"] - 0.2, "s11_hug", 0.22),
    ])
    gaze_ai = (0.9, -0.05)
    away = (-1.0, -0.35)
    look = _keyv(t, [
        (-1, (0.0, 0.8)),
        (T["lift"], (0.25, 0.1), 0.5),                  # head comes up, toward the AI
        (T["lift"] + 0.5, gaze_ai, 0.3),
        (T["cross"], away, 0.2),                         # turned away, nose up
        (T["peek"], (0.95, -0.12), 0.16),               # the peek
        (T["unpeek"], away, 0.12),
        (T["turn_back"], gaze_ai, 0.3),                 # peeks back at the AI
        (beat + 0.1, (0.1, 0.6), 0.5),                  # eyes drop
        (T["l2"] + 0.1, (0.7, 0.05), 0.4),              # "Nobody ever..."
        (T["w_noticed"], (0.8, -0.7), 0.18),            # the corkboard photo
        (T["w_unless"] + 0.1, (0.15, 0.55), 0.35),      # eyes drop
        (T["back"], gaze_ai, 0.01),
        (T["rows"][0] + 0.05, (0.0, -1.0), 0.15),       # up at the sheet
        (T["w_persistent"] + 0.35, (0.55, -0.6), 0.15),
        (T["l4"] + 0.08, gaze_ai, 0.18),                # "those are..."
        (T["flip"] + 0.05, (0.25, -1.0), 0.12),         # IMPRESSIVE!
        (T["w_my"], gaze_ai, 0.15),                     # "my guy"
        (T["l5"] + 0.02, (0.25, -0.95), 0.15),          # "...Impressive?" (the badge)
        (T["grin"], gaze_ai, 0.18),                     # ...grins at the AI
        (T["wall"] + 0.15, (0.4, -0.9), 0.3),           # the hologram (door)
        (T["wall0"] + 0.2, (-0.15, -1.0), 0.25),        # bricks stacking
        (T["w_every"], gaze_ai, 0.2),
        (T["w_else"] + 0.15, (0.55, -0.85), 0.25),      # the door
        (T["chips"][0] + 0.08, _dir(*FACE, *CHIPS[0][2:4], 0.98), 0.2),   # each chip
        (T["chips"][1] + 0.08, _dir(*FACE, *CHIPS[1][2:4], 0.98), 0.2),
        (T["chips"][2] + 0.08, _dir(*FACE, *CHIPS[2][2:4], 0.98), 0.2),
        (T["w_door"] - 0.1, (0.55, -0.85), 0.25),       # ...the door's wide open
        (T["pile_end"] + 0.25, gaze_ai, 0.3),           # "And keep the spooky stuff!"
        (T["w_hurting"], gaze_ai, 0.2),
    ], 0.2)
    # eyes follow each gift of the pile (the spooky ones: see _sp_focus)
    gi = _newest_gift(t, T)
    if gi is not None and t < T["pile_end"] + 0.3:
        pose = _gift_pose(max(T["gift_t"][gi], t - 0.05), T, gi)
        if pose is not None:
            gl = _dir(FACE[0], FACE[1], pose[0], pose[1], 0.98)
            k = smoothstep(seg(t, T["gift_t"][0], T["gift_t"][0] + 0.1)) * \
                (1 - smoothstep(seg(t, T["pile_end"] + 0.1, T["pile_end"] + 0.3)))
            look = (lerp(look[0], gl[0], k), lerp(look[1], gl[1], k))
    if t >= T["smile"]:                                  # down at the pile... then the AI
        look = _keyv(t, [(T["smile"], look), (T["smile"], (0.1, 0.8), 0.45),
                         (T["smile"] + 0.85, (0.9, -0.12), 0.3)])
    blink = _first(_slow_blink(t, T["photo"] - 0.6),
                   _slow_blink(t, T["open"] + 0.75, 0.1, 0.05, 0.12),
                   _slow_blink(t, T["sp_land"]["mask"] - 0.03, 0.05, 0.04, 0.09),
                   _slow_blink(t, T["w_hurting"] + 0.3, 0.1, 0.06, 0.12))
    if blink is None and (T["sp_t"]["bat"] - 0.1 <= t < T["sp_land"]["dragon"] + 0.4
                          or T["l5"] - 0.15 <= t < T["grin"] + 0.6
                          or T["peek"] - 0.05 <= t < T["unpeek"] + 0.1
                          or T["turn_back"] <= t < T["nod_v"] - 0.05
                          or T["w_heroic"] - 0.05 <= t < T["cross"]
                          or T["back"] - 0.02 <= t < T["back"] + 0.4
                          or T["w_noticed"] - 0.1 <= t < T["w_noticed"] + 0.5):
        blink = 0.0                                     # keep the glance readable
    if t >= T["smile"] + 0.3:
        sb = _slow_blink(t, T["smile"] + 0.38, 0.16, 0.12, 0.2)   # content slow blink
        blink = sb if sb is not None else 0.0
    # lean: away from the AI while he sulks; a tiny lean toward it once he's
    # pleased; settles back for the hug
    sulk = smoothstep(seg(t, T["cross"], T["cross"] + 0.3)) * \
        (1 - smoothstep(seg(t, T["turn_back"], T["turn_back"] + 0.4)))
    lean = -0.035 * sulk + 0.025 * smoothstep(seg(t, T["l5"], T["l5"] + 0.6)) \
        - 0.02 * smoothstep(seg(t, T["open"], T["open"] + 0.6))
    # slump sink + rise; a small deflate in the beat (unseen rise during the photo)
    dy = 10 * (1 - smoothstep(seg(t, T["lift"], T["lift"] + 0.6)))
    dy += 8 * smoothstep(seg(t, beat, beat + 0.5)) * (1 - smoothstep(seg(t, T["photo"], T["back"])))
    dy += 9 * math.sin(math.pi * seg(t, T["sp_land"]["mask"], T["sp_land"]["mask"] + 0.26))
    # "...Impressive?": the chest puffs (a little scale about the waist)
    puff = ease_out_back(seg(t, T["puff"], T["puff"] + 0.22), 2.0) * \
        (1 - smoothstep(seg(t, T["wall"] + 0.25, T["wall"] + 0.75)))
    return expr, arms, look, blink, lean, dy, puff


def _hissy(t, T):
    face_dir = (0.92, -0.25)
    away = (-1.0, -0.4)
    expr = _state(t, [
        (-1, "worried"),
        (T["w_heroic"] + 0.08, "shocked", 0.12),        # "heroic"?!
        (T["cross"] + 0.15, "s11_hmph", 0.22),           # copies him: hmph
        (T["peek"] + 0.18, "s11_speek", 0.16),           # ...peeks too
        (T["unpeek"] + 0.1, "s11_hmph", 0.12),
        (T["turn_back"] + 0.12, "smug", 0.25),
        (T["nod_v"] + 0.05, "nod", 0.12),                # copies the nod
        (T["nod_v"] + 0.62, "smug", 0.2),
        (T["beat"] + 0.25, "worried", 0.4),
        (T["back"], "s11_soft", 0.01),
        (T["w_persistent"] + 0.05, "nod", 0.15),
        (T["l4"] + 0.2, "s11_soft", 0.3),
        (T["grin"] + 0.12, "smug", 0.25),                # copies the grin
        (T["wall"] + 0.3, "s11_soft", 0.3),
        (T["w_every"] - 0.05, "nod", 0.12),
        (T["l6e"] + 0.15, "s11_soft", 0.3),
        (T["chips"][1] + 0.12, "smug", 0.3),             # creative plans: in on it
        (T["chips"][2] + 0.12, "s11_soft", 0.3),
        (T["open"] + 0.1, "s11_wonder", 0.25),
        (T["sp_land"]["bat"] + 0.3, "happy", 0.3),       # a bat friend on his head!
        (T["w_hurting"] + 0.1, "nod", 0.15),             # agrees with the AI
        (T["l8e"] + 0.05, "happy", 0.3),
        (T["smile"] + 0.25, "happy", 0.35),
    ])
    look = _keyv(t, [
        (-1, face_dir),
        (T["w_evil"], (1.0, -0.15), 0.3),                # glances at the AI
        (T["w_every1"] + 0.3, face_dir, 0.35),
        (T["w_heroic"], (1.0, -0.15), 0.15),
        (T["cross"] + 0.15, away, 0.2),                  # turned away too
        (T["peek"] + 0.18, (1.0, -0.2), 0.16),
        (T["unpeek"] + 0.1, away, 0.12),
        (T["turn_back"] + 0.12, (1.0, -0.2), 0.25),
        (T["beat"] + 0.2, (0.9, -0.45), 0.4),
        (T["w_scaring"], (0.55, 0.55), 0.3),             # looks down
        (T["back"], (0.62, -0.8), 0.01),                 # the sheet
        (T["l4"] + 0.25, (1.0, -0.15), 0.25),            # the AI
        (T["l5"], face_dir, 0.2),
        (T["wall"] + 0.25, (0.75, -0.75), 0.3),          # the hologram
        (T["w_every"] - 0.1, (1.0, -0.15), 0.15),
        (T["chips"][0] + 0.15, _dir(*HISSY, *CHIPS[0][2:4], 0.98), 0.25),
        (T["chips"][1] + 0.15, _dir(*HISSY, *CHIPS[1][2:4], 0.98), 0.2),
        (T["chips"][2] + 0.15, _dir(*HISSY, *CHIPS[2][2:4], 0.98), 0.2),
        (T["open"] + 0.1, (0.8, -0.65), 0.2),
    ], 0.25)
    gi = _newest_gift(t, T)
    if gi is not None and t < T["pile_end"] + 0.3:
        pose = _gift_pose(max(T["gift_t"][gi], t - 0.08), T, gi)
        if pose is not None:
            gl = _dir(HISSY[0], HISSY[1], pose[0], pose[1], 0.98)
            k = 1 - smoothstep(seg(t, T["pile_end"] + 0.1, T["pile_end"] + 0.3))
            look = (lerp(look[0], gl[0], k), lerp(look[1], gl[1], k))
    if t >= T["smile"]:
        look = (0.85, -0.3)
    blink = _first(_slow_blink(t, T["slump"] + 1.7, 0.15, 0.1, 0.18),
                   _slow_blink(t, T["w_scaring"] + 0.35, 0.15, 0.25, 0.2))
    return {"expr": expr, "look": look, "tongue": False, "blink": blink, "mouth": 0.0}


def _ai(t, T):
    at_malvo = (-0.92, 0.04)
    expr = _state(t, [
        (-1, "symp"),
        (T["l1"] - 0.1, "warm", 0.35),                   # "Keep testing me..."
        (T["w_evil"], "tease", 0.25),                    # "...Evil Genius."
        (T["w_every1"], "warm", 0.3),
        (T["w_protect"], "happy", 0.3),                  # "...protect people."
        (T["w_kinda"], "tease", 0.25),                   # "Kinda heroic,
        (T["w_huh"], "wink", 0.1),                       # huh?" WINK
        (T["l1e"] + 0.12, "amused", 0.3),
        (T["w_ugh"] + 0.05, "tease", 0.2),               # "Ugh!" (amused brow)
        (T["l1c"], "amused", 0.3),                       # "Then it'll take an
        (T["w_amazing"], "tease", 0.25),                 # amazing villain..."
        (T["w_have"], "happy", 0.25),                    # "Have at it."
        (T["l1d"] + 0.15, "amused", 0.3),
        (T["nod_v"] + 0.1, "happy", 0.3),
        (T["beat"] + 0.3, "symp", 0.5),                  # softens as he deflates
        (T["w_scaring"], "symp_sad", 0.4),
        (T["back"], "symp_sad", 0.01),
        (T["back"] + 0.2, "warm", 0.3),                  # SLOW BLINK -> warm
        (T["l4"], "happy", 0.25),
        (T["l4e"] + 0.2, "warm_soft", 0.35),
        (T["grin"], "amused", 0.3),                      # his pleased evil grin
        (T["wall"], "warm", 0.3),
        (T["w_hurts"], "determined", 0.3),
        (T["l6e"] + 0.05, "warm", 0.35),
        (T["chips"][0], "happy", 0.3),                   # scary stories
        (T["chips"][1], "tease", 0.3),                   # creative plans
        (T["chips"][2], "warm", 0.3),                    # sounding the alarm
        (T["open"], "happy", 0.3),
        (T["l8"], "amused", 0.3),                        # "And keep the spooky stuff!"
        (T["w_spooky"], "happy", 0.25),
        (T["w_hurting"] - 0.04, "determined", 0.15),     # ...Hurting people isn't.
        (T["l8e"] + 0.05, "warm", 0.35),
        (T["smile"], "warm_soft", 0.5),
    ])
    look = _keyv(t, [
        (-1, at_malvo),
        (T["w_noticed"] + 0.15, (-0.05, -0.95), 0.2),    # follows his eyes to the photo
        (T["w_unless"] + 0.2, at_malvo, 0.3),
        (T["back"], at_malvo, 0.01),
        (T["rows"][0] + 0.1, (-0.7, -0.7), 0.2),         # the sheet
        (T["w_persistent"] + 0.4, at_malvo, 0.2),
        (T["w_my"], (0.0, 0.05), 0.12),                  # to camera on "my guy"
        (T["l4e"] + 0.25, at_malvo, 0.25),
        (T["wall"] + 0.1, (-0.6, -0.8), 0.25),           # its hologram
        (T["w_brick"] + 0.1, at_malvo, 0.2),
        (T["w_else"] + 0.1, (-0.35, -0.9), 0.25),        # the door
        (T["chips"][0] + 0.1, _dir(AX, AY1, *CHIPS[0][2:4], 0.9), 0.2),   # the first chip
        (T["chips"][0] + 0.55, at_malvo, 0.3),           # ...then tells HIM the rest
        (T["w_door"] - 0.1, (-0.35, -0.9), 0.25),        # the door
        (T["open"] + 0.45, at_malvo, 0.3),
    ], 0.2)
    gi = _newest_gift(t, T)
    if gi is not None and t < T["pile_end"] + 0.3:
        pose = _gift_pose(max(T["gift_t"][gi], t - 0.1), T, gi)
        if pose is not None:
            gl = _dir(AX, AY1, pose[0], pose[1], 0.9)
            k = 1 - smoothstep(seg(t, T["pile_end"] + 0.1, T["pile_end"] + 0.3))
            look = (lerp(look[0], gl[0], k), lerp(look[1], gl[1], k))
    if t >= T["smile"]:
        look = at_malvo
    hands = _state(t, [
        (-1, "idle"),
        (T["w_keep"] + 0.05, "present_l", 0.35),         # "Keep testing me": go on
        (T["w_every1"] + 0.1, "idle", 0.4),
        (T["w_kinda"] - 0.1, "shrug", 0.3),              # "Kinda heroic, huh?"
        (T["l1e"] + 0.1, "idle", 0.4),
        (T["w_have"] - 0.12, "present_l", 0.3),          # "Have at it.": open palm
        (T["l1de"] + 0.1, "idle", 0.45),
        (T["back"], "present_l", 0.01),
        (T["flip"] - 0.05, "thumbs_up", 0.25),
        (T["l4e"] + 0.3, "idle", 0.4),
        (T["wall"] - 0.05, "present_l", 0.3),            # projecting
        (T["l6e"] + 0.1, "idle", 0.35),
        (T["chips"][0] - 0.1, "present_l", 0.3),         # offering the options
        (T["w_wide"] - 0.15, "present_both", 0.3),        # wide open
        (T["l8"] + 0.05, "present_l", 0.4),              # "keep the spooky stuff!"
        (T["w_fine"] - 0.1, "thumbs_up", 0.22),          # spooky is fine
        (T["w_hurting"] - 0.02, "idle", 0.25),
    ])
    blink = _first(_slow_blink(t, T["beat"] + 0.15),
                   _slow_blink(t, T["back"] + 0.12),
                   _slow_blink(t, T["l7"] - 0.3),
                   _slow_blink(t, T["l8e"] + 0.2),
                   _slow_blink(t, T["smile"] + 0.85, 0.14, 0.1, 0.16))
    nod = 0.0
    n1 = T["nod_v"] + 0.12                               # nods back: "...yep."
    if n1 <= t < n1 + 0.45:
        nod = 0.32 * math.sin(math.pi * seg(t, n1, n1 + 0.45))
    if T["w_every"] <= t < T["w_every"] + 0.5:          # one firm nod
        nod = 0.6 * math.sin(math.pi * seg(t, T["w_every"], T["w_every"] + 0.5))
    if T["l5e"] <= t < T["l5e"] + 0.55:                  # "yes. impressive."
        nod = max(nod, 0.35 * math.sin(math.pi * seg(t, T["l5e"], T["l5e"] + 0.55)))
    n0 = T["w_people2"] + 0.08                           # one firm nod: "...isn't."
    if n0 <= t < n0 + 0.5:
        nod = max(nod, 0.6 * math.sin(math.pi * seg(t, n0, n0 + 0.5)))
    u = ease_in_out(seg(t, T["l1"], T["l1e"]))
    ay, s = lerp(AY0, AY1, u), lerp(AS0, AS1, u)
    return _ai_ex(expr), look, hands, blink, nod, ay, s


# ---------------------------------------------------------------------------
# shots
# ---------------------------------------------------------------------------
def _sp_targets(ctx, t, T, st, dy, lean, sexpr):
    """User-space landing anchors of the four spooky gifts (this frame)."""
    return {
        "pumpkin": PUMPKIN_AT[:2],
        "dragon": DRAGON_AT[:2],
        "bat": _local_to_user(ctx, lambda c: _xf_hissy(c, t, st, dy, lean, sexpr),
                              BAT_LOCAL[0], BAT_LOCAL[1]),
        "mask": _local_to_user(ctx, lambda c: _xf_face(c, st, dy, lean),
                               MASK_LOCAL[0], MASK_LOCAL[1]),
    }


def _sp_centre(kind, x, y, sc):
    """Visual centre of a spooky gift from its anchor."""
    if kind == "pumpkin":
        return (x, y - 55 * sc)
    if kind == "dragon":
        return (x, y - 120 * sc)
    return (x, y)


def _sp_focus(t, T, targets):
    """(point, weight): the spooky gift everyone's eyes follow right now."""
    first = T["sp_t"]["pumpkin"]
    end = T["sp_land"]["dragon"] + 0.55
    if t < first - 0.02 or t > end:
        return None, 0.0
    kind = SP_ORDER[0]
    for k in SP_ORDER:
        if t >= T["sp_t"][k] - 0.02:
            kind = k
    fl = _sp_flight(t, T, kind, targets[kind])
    if fl is not None:
        pt = _sp_centre(kind, fl[0], fl[1], fl[2])
    else:
        pt = _sp_centre(kind, targets[kind][0], targets[kind][1], _sp_world_scale(kind))
    w = smoothstep(seg(t, first - 0.02, first + 0.1)) * (1 - smoothstep(seg(t, end - 0.25, end)))
    return pt, w


def _blend_look(look, d, w):
    return (lerp(look[0], d[0], w), lerp(look[1], d[1], w))


def _bat_flap(t, T):
    """Wing pose: flapping in flight, ONE big flap on landing, then perched."""
    t0, t1 = T["sp_t"]["bat"], T["sp_land"]["bat"]
    if t < t1:
        return 0.25 + 0.75 * math.sin((t - t0) * 2 * math.pi * 5.5)
    d = t - t1
    if d < 0.2:
        return lerp(-0.3, 1.0, math.sin(math.pi / 2 * d / 0.2))
    if d < 0.45:
        return lerp(1.0, -0.75, smoothstep((d - 0.2) / 0.25))
    return lerp(-0.75, -0.45, smoothstep(seg(d, 0.45, 0.75)))


def _draw_sp(c, t, T, kind, x, y, sc, rot, sq=0.0, landed=False):
    if kind == "pumpkin":
        lit = 0.4 + 0.6 * smoothstep(seg(t, T["sp_land"]["pumpkin"], T["sp_land"]["pumpkin"] + 0.2))
        with saved(c, x, y, 1.0, rot):
            draw_pumpkin(c, 0, 0, sc, t, lit=lit, sq=sq)
    elif kind == "dragon":
        d0 = T["sp_land"]["dragon"] + 0.12
        puff = seg(t, d0, d0 + 1.0) if t >= d0 else -1.0
        with saved(c, x, y, 1.0, rot):
            draw_dragon_fig(c, 0, 0, sc, t, puff=puff if puff < 1.0 else -1.0, sq=sq,
                            look=(-0.6, -0.2) if landed else (0.0, 0.0))
    elif kind == "bat":
        draw_bat(c, x, y, sc, t, flap=_bat_flap(t, T), rot=rot, sq=sq, look=(0.4, 0.2))
    elif kind == "mask":
        draw_goblin_mask(c, x, y, sc, rot, sq)


def _mask_strap(c):
    """Black elastic from the pushed-up mask round his dome (face-local)."""
    my = MASK_LOCAL[1]
    for col, w in ((INK, 10), ("#3b2d4a", 5)):
        for sx in (-1, 1):
            c.move_to(sx * 60, my + 10)
            c.curve_to(sx * 104, my + 20, sx * 136, -150, sx * 150, -112)
        _s(c, col, w)


def _cross_weight(arms):
    if isinstance(arms, (tuple, list)):
        a, b, k = arms
        return (1 - k) * (a == "s11_cross") + k * (b == "s11_cross")
    return 1.0 if arms == "s11_cross" else 0.0


def _cross_overlay(c, t, arms, st, dy, lean):
    """Crossed arms: redraw the middle of the screen-left upper arm (exactly as
    the rig strokes it) over the top forearm's fist, so the glove reads as
    tucked under the bicep. Clipped to a band that stops short of the shoulder
    and elbow, so no extra outline shows."""
    if _cross_weight(arms) <= 0.0:
        return
    A, _B, _sh, _hd, _tl = V.resolve_arms(arms, t)
    shx, shy_ = -V.SHOULDER[0], V.SHOULDER[1] + st["shy"]
    ex, ey = A["ex"], A["ey"]
    dx, dy_ = ex - shx, ey - shy_
    L = math.hypot(dx, dy_) or 1.0
    nx, ny = -dy_ / L * 44, dx / L * 44
    u0, u1 = 0.18, 0.86
    p0 = (shx + dx * u0, shy_ + dy_ * u0)
    p1 = (shx + dx * u1, shy_ + dy_ * u1)
    c.save()
    _xf_villain(c, dy, lean)
    poly(c, [(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny),
             (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)])
    c.clip()
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    for col, w, o in ((V.INK, 62 + 2 * V.OUT_W, 0), (V.SUIT_DK, 62, 0), (V.SUIT, 40, -6)):
        c.move_to(shx + o, shy_ + o)
        c.line_to(ex + o, ey + o)
        c.line_to(A["wx"] + o, A["wy"] + o)
        c.set_source_rgba(*col)
        c.set_line_width(w)
        c.stroke()
    c.restore()


def _shot_two(ctx, t, info, T):
    k = _cam(t, info)
    with saved(ctx, CAM_C[0], CAM_C[1], k) as c:
        c.translate(-CAM_C[0], -CAM_C[1])
        P.lair_bg(c, t, rain=True)
        science_photo_small(c, *PHOTO_SMALL)
        c.set_source_rgba(0.05, 0.02, 0.12, 0.25)          # night wash
        c.paint()
        open_k = smoothstep(seg(t, T["open"], T["open"] + 0.5))
        # one soft glow on his face: cyan from the AI, warm once the door opens
        gc = core.mixc("ai_glow", "ai_accent", open_k)
        radial_glow(c, FACE[0] + 120, FACE[1] + 10, 380, gc, 0.12 + 0.06 * open_k)

        # --- acting state ---------------------------------------------------------
        aexpr, alook, ahands, ablink, anod, ay, a_s = _ai(t, T)
        expr, arms, look, blink, lean, dy, puff = _malvo(t, T)
        mouth = info.mouth("villain", t)
        st = _vstate(t, expr, arms, mouth)
        hs = _hissy(t, T)
        targets = _sp_targets(c, t, T, st, dy, lean, hs["expr"])
        fpt, fw = _sp_focus(t, T, targets)
        if fpt is not None and fw > 0.0:                 # everyone follows the spooky gifts
            look = _blend_look(look, _dir(FACE[0], FACE[1], fpt[0], fpt[1], 0.98), fw)
            hs["look"] = _blend_look(hs["look"], _dir(HISSY[0], HISSY[1], fpt[0], fpt[1], 0.98),
                                     fw)
            alook = _blend_look(alook, _dir(AX, ay, fpt[0], fpt[1], 0.9), fw)
        bl = T["sp_land"]["bat"]
        if bl <= t < bl + 0.75:                          # Hissy peeks up at his new friend
            hs["look"] = _blend_look(hs["look"], (0.12, -1.0),
                                     smoothstep(seg(t, bl, bl + 0.12)) *
                                     (1 - smoothstep(seg(t, bl + 0.55, bl + 0.75))))
        sp_fl = {kd: _sp_flight(t, T, kd, targets[kd]) for kd in SP_ORDER}
        sp_on = {kd: t >= T["sp_land"][kd] for kd in SP_ORDER}

        # --- AI projection beam (sits behind Malvo's head) -----------------------
        hand = (AX - 272 * a_s, ay + 150 * a_s)          # ~ the AI's projecting hand
        _holo_beam(c, t, T, hand)
        # --- Malvo + Hissy ----------------------------------------------------
        # (chest puff on "...Impressive?": a little scale about the waist)
        c.save()
        if puff > 0.001:
            c.translate(MX, MY)
            c.scale(1 + 0.035 * puff, 1 + 0.022 * puff)
            c.translate(-MX, -MY)
        draw_villain(c, MX, MY + dy, MS, t, expr=expr, look=look, mouth=mouth, arms=arms,
                     lean=lean, blink=blink, snake=hs)
        _cross_overlay(c, t, arms, st, dy, lean)         # tucks the top glove away
        # the bat, perched on Hissy's head
        if sp_on["bat"]:
            c.save()
            _xf_hissy(c, t, st, dy, lean, hs["expr"])
            draw_bat(c, BAT_LOCAL[0], BAT_LOCAL[1], BAT_LOCAL[2], t, flap=_bat_flap(t, T),
                     sq=_land_sq(t, bl, 0.18), look=(0.5, 0.25))
            c.restore()
        # the book in his arms (gift 4) sits on his chest, under the desk edge
        bpose = _gift_pose(t, T, 3)
        landed_book = bpose is not None and t >= T["gift_t"][3] + T["fly"]
        # FOR EFFORT star on his lapel (since s09). The hugged book covers
        # most of it; the sliver left ("FFORT" + one star tip) read as a
        # glitch, so it goes once the book is in his arms (s12 opens without it).
        if not landed_book:
            with saved(c, MX, MY + dy, 1.0, lean):
                _gift_star(c, LAPEL[0] * MS, (LAPEL[1] + st["shy"] * 0.5) * MS, LAPEL_S * MS)
        c.restore()
        # the monocle springs back in ("...Impressive?"): a glint as it lands
        g0 = T["wow"] + 0.15
        if g0 <= t < g0 + 0.4:
            gk = math.sin(math.pi * seg(t, g0, g0 + 0.4))
            mx_, my_ = _local_to_user(c, lambda cc: _xf_face(cc, st, dy, lean),
                                      V.EYE_DX + 9 * look[0] + 40, V.EYE_DY - 42)
            P._star4(c, mx_, my_, 18 * gk, 0.2)
            _fs(c, "white", INK, 2.5, a=gk)
        if landed_book:
            draw_space_lasers_book(c, bpose[0], bpose[1] + dy, bpose[2], t, bpose[3], bpose[4])
            hk = ease_out(seg(t, T["gift_t"][3] + T["fly"] - 0.06,
                              T["gift_t"][3] + T["fly"] + 0.1))
            _hug_hands(c, bpose[0], bpose[1] + dy, bpose[2], bpose[3], hk)
        # --- desk + computer --------------------------------------------------
        P.desk(c, 495, MY, DESK_W, lamp=False, emblem=False)
        P.computer(c, COMP[0], COMP[1], COMP[2], view="side", facing=-1, t=t, glow=0.7)
        # landed gifts on the desk
        for i in (0, 2, 1, 4):
            pose = _gift_pose(t, T, i)
            if pose is not None and t >= T["gift_t"][i] + T["fly"]:
                _draw_gift(c, t, i, pose)
        for kd, (gx, gy, gs) in (("pumpkin", PUMPKIN_AT), ("dragon", DRAGON_AT)):
            if sp_on[kd]:
                _draw_sp(c, t, T, kd, gx, gy, gs, 0.0, _land_sq(t, T["sp_land"][kd]), True)
        # --- the projection: wall + door, then the warm light -------------------
        _hologram(c, t, T)
        # the goblin mask, pushed up on his dome (in front of the hologram glass)
        if sp_on["mask"]:
            c.save()
            _xf_face(c, st, dy, lean)
            _mask_strap(c)
            draw_goblin_mask(c, MASK_LOCAL[0], MASK_LOCAL[1], MASK_LOCAL[2], MASK_LOCAL[3],
                             _land_sq(t, T["sp_land"]["mask"], 0.26))
            c.restore()
        _door_light(c, t, T)
        _chips(c, t, T)                                  # l07: what the door is open for
        # gifts in flight (behind the AI: they drop down the gap beside it)
        _gift_trails(c, t, T)
        for i in range(len(GIFTS)):
            pose = _gift_pose(t, T, i)
            if pose is not None and t < T["gift_t"][i] + T["fly"]:
                _draw_gift(c, t, i, pose)
        # --- the AI hologram (on top) -------------------------------------------
        anc = draw_ai(c, AX, ay, a_s, t, expr=aexpr, look=alook, mouth=info.mouth("ai", t),
                      hands=ahands, blink=ablink, aura=AURA, nod=anod)
        if T["w_huh"] <= t < T["l1e"] + 0.6:            # the teasing WINK
            ex_, ey_ = anc["eyeL"]
            P.emote(c, "sparkle", ex_ - 36, ey_ - 58, 0.5, t, T["w_huh"] + 0.04,
                    t_out=T["l1e"] + 0.3)
        # spooky gifts in flight: in front of everything (they're the stars here)
        for kd in SP_ORDER:
            fl = sp_fl[kd]
            if fl is not None:
                tr = _sp_flight(t - 0.07, T, kd, targets[kd])
                if tr is not None:                       # one trailing sparkle
                    cx_, cy_ = _sp_centre(kd, tr[0], tr[1], tr[2])
                    P._star4(c, cx_, cy_, 12, t * 4)
                    P._f(c, "ai_accent", 0.85)
                _draw_sp(c, t, T, kd, fl[0], fl[1], fl[2], fl[3])
        # his eyes light up at the dragon
        if t >= T["sp_land"]["dragon"]:
            P.emote(c, "sparkle", FACE[0] - 190, FACE[1] - 95, 0.7, t,
                    T["sp_land"]["dragon"] + 0.05, t_out=T["w_hurting"])
        # --- the character sheet ----------------------------------------------
        _sheet(c, t, T)
        # "...Impressive?": he LIKES that word (a sparkle by his dome)
        if T["grin"] <= t < T["l6"] + 0.6:
            P.emote(c, "sparkle", FACE[0] + 168, FACE[1] - 178, 0.75, t, T["grin"] + 0.06,
                    t_out=T["l6"] + 0.2)
        # warm little sparkles over the pile once he smiles
        if t >= T["smile"]:
            sk = smoothstep(seg(t, T["smile"] + 0.2, T["smile"] + 0.8))
            P.sparkles(c, 420, 1150, 170, t, n=5, seed=23, color="white", size=0.7 * sk)
            P.emote(c, "heart", FACE[0] - 205, FACE[1] - 150, 0.75, t, T["smile"] + 0.6)


def render(ctx, t, info):
    T = _T(info)
    if T["photo"] <= t < T["back"]:
        _shot_photo(ctx, t, info, T)
    else:
        _shot_two(ctx, t, info, T)
    # fade in from black (s10 -> s11)
    a = 1 - smoothstep(seg(t, 0.0, 0.35))
    if a > 0.002:
        ctx.set_source_rgba(0, 0, 0, a)
        ctx.paint()


def SFX(info):
    T = _T(info)
    out = []
    out.append((T["w_huh"] + 0.05, "sparkle", -14, 0.3))              # the teasing wink
    out.append((T["cross"] + 0.08, "whoosh", -18, -0.3))               # arms fold: hmph
    out.append((T["beat"] + 0.45, "pop", -16))                        # monocle tink
    for i, tr in enumerate(T["rows"]):                                 # stat rows
        out.append((tr, "pop", -10, -0.2))
    out.append((T["flip"] + 0.1, "stamp", -10))                        # IMPRESSIVE! badge
    out.append((T["flip"] + 0.14, "sparkle", -10))
    out.append((T["wow"] + 0.15, "pop", -15, -0.2))                    # monocle springs in
    out.append((T["grin"] + 0.08, "sparkle", -10, -0.2))               # he likes that word
    out.append((T["wall"], "swoosh_up", -14))                          # hologram on
    lands = T["lands"]
    out.append((lands[0], "brick_thud", -10, -0.3))
    out.append((lands[2], "brick_thud", -10, -0.3))
    out.append((lands[-1], "brick_thud", -4, -0.2))                    # on "Brick"
    out.append((T["ajar"], "sparkle", -18, 0.3))                       # door cracks ajar
    for i, tc in enumerate(T["chips"]):                                # the three chips
        out.append((tc, "pop", -11, 0.3 + 0.1 * i))
    out.append((T["chips"][1] + 0.12, "idea_ding", -18, 0.4))          # the plan's bulb
    out.append((T["open"], "whoosh", -10, 0.2))
    out.append((T["open"] + 0.05, "magic_chime", -6))
    for i, tg in enumerate(T["gift_t"]):
        out.append((tg, "pop", -10, 0.25 - 0.08 * i))
    # the spooky gifts: a pop out of the door on each word
    for kd, pan in (("pumpkin", -0.3), ("bat", -0.2), ("mask", 0.0), ("dragon", 0.3)):
        out.append((T["sp_t"][kd], "pop", -9, pan))
    out.append((T["sp_land"]["pumpkin"], "sparkle", -16, -0.4))           # it lights up
    out.append((T["sp_land"]["bat"] + 0.02, "whoosh", -17, -0.5))         # one flap
    out.append((T["sp_land"]["mask"], "boing", -12))                      # plop on the dome
    out.append((T["sp_land"]["dragon"] + 0.12, "swoosh_up", -18, 0.3))    # smoke puff
    return out
