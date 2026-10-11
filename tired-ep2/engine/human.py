"""engine/human.py -- ONE shared, data-driven full-body rig for every person.

    draw_person(ctx, who, x, y, s, t, pose="stand", expr="neutral", ...) -> anchors

Layout of this file (read top to bottom):
  1. small math / path helpers
  2. CHARS      -- per-character design data (proportions, colours, head shape)
  3. HANDS      -- hand-shape table (finger angles), blendable
  4. FACE       -- face parameter defaults, EXPR table, per-character tuning
  5. POSES      -- static pose table + CYCLES (wave tables) for animated poses
  6. solver     -- pose resolve/blend + 2.5D FK/IK skeleton (yaw-projected)
  7. drawing    -- limbs, hands, feet, torso/outfits, head/face, accessories
  8. draw_person

Conventions
  * Local rig units are logical px at s=1. Ground contact (x, y) is the origin;
    y grows DOWN (like the canvas).
  * Body frame (3D, before projection): x = screen-right when facing camera,
    y = down, z = toward camera ("forward").  `turn` yaws the body; points are
    projected orthographically (X = x cos + z sin) so limbs foreshorten.
  * Side names "l"/"r" = the side that appears on SCREEN-LEFT / SCREEN-RIGHT
    when flip=False and turn=0 (i.e. "l" is the character's anatomical right).
  * Limb angles are ABSOLUTE (not inherited from the spine) in radians:
      pitch  p : 0 = hanging straight down, +pi/2 = pointing forward, pi = up
      abduct o : 0 = along the body, + = out to that limb's own side
"""
import math
import cairocffi as cairo
from engine.core import (PAL, hexc, mixc, clamp, lerp, smoothstep, blink_amount, noise1,
                         hash01, smooth_path, circle, ellipse, radial_glow)

TAU = 2 * math.pi
INK_W = 5.5            # outline width at s=1
TURN_RAD = 0.86        # body yaw (rad) at |turn| = 1  (~49 deg: a solid 3/4)
HEAD_TURN_RAD = 0.92   # head yaw per unit head turn


# ============================================================================
# 1. helpers
# ============================================================================
def _dk(c, k=0.25):
    """Darker shade of a colour (mixed toward ink)."""
    return mixc(c, PAL["ink"], k)


def _lt(c, k=0.25):
    return mixc(c, "#ffffff", k)


def _set(ctx, c):
    ctx.set_source_rgba(*(c if isinstance(c, tuple) else hexc(c)))


def _fill(ctx, c, preserve=False):
    _set(ctx, c)
    if preserve:
        ctx.fill_preserve()
    else:
        ctx.fill()


def _stroke(ctx, c, w, preserve=False):
    _set(ctx, c)
    ctx.set_line_width(w)
    if preserve:
        ctx.stroke_preserve()
    else:
        ctx.stroke()


def _fs(ctx, fc, w=INK_W, sc=None):
    """fill (preserve) + ink stroke current path."""
    _set(ctx, fc)
    ctx.fill_preserve()
    _set(ctx, sc or PAL["ink"])
    ctx.set_line_width(w)
    ctx.stroke()


def _rot(x, y, a):
    c, s = math.cos(a), math.sin(a)
    return (x * c - y * s, x * s + y * c)


def _norm(x, y):
    d = math.hypot(x, y)
    return (x / d, y / d) if d > 1e-9 else (0.0, 1.0)


def _capsule(ctx, ax, ay, ra, bx, by, rb):
    """Convex hull of two circles (tapered tube) as a closed, CW sub-path."""
    dx, dy = bx - ax, by - ay
    d = math.hypot(dx, dy)
    if d < 1e-6 or d <= abs(ra - rb):
        if ra >= rb:
            circle(ctx, ax, ay, ra)
        else:
            circle(ctx, bx, by, rb)
        return
    base = math.atan2(dy, dx)
    th = math.acos(clamp((ra - rb) / d, -1.0, 1.0))
    ctx.new_sub_path()
    ctx.arc(bx, by, rb, base - th, base + th)
    ctx.arc(ax, ay, ra, base + th, base + TAU - th)
    ctx.close_path()


def _quad(ctx, a, ra, b, rb):
    """Tapered tube segment with FLAT ends (hems / sleeve openings); clockwise like _capsule."""
    nx, ny = _norm(b[0] - a[0], b[1] - a[1])
    nx, ny = -ny, nx
    pts = [(a[0] + nx * ra, a[1] + ny * ra), (b[0] + nx * rb, b[1] + ny * rb),
           (b[0] - nx * rb, b[1] - ny * rb), (a[0] - nx * ra, a[1] - ny * ra)]
    area = sum(pts[i][0] * pts[(i + 1) % 4][1] - pts[(i + 1) % 4][0] * pts[i][1] for i in range(4))
    if area < 0:
        pts.reverse()
    ctx.move_to(*pts[0])
    for q in pts[1:]:
        ctx.line_to(*q)
    ctx.close_path()


def _ink_fill(ctx, build, color, inkw):
    """Outlined union without strokes: fill build(d=inkw) in ink, then build(d=0) in colour."""
    ctx.new_path()
    build(inkw)
    _set(ctx, PAL["ink"])
    ctx.fill()
    build(0.0)
    _set(ctx, color)
    ctx.fill()


def _poly(ctx, pts, close=True):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if close:
        ctx.close_path()


def _smooth(ctx, pts, closed=True, tension=0.5):
    smooth_path(ctx, pts, closed=closed, tension=tension)


def _lerp2(a, b, k):
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)


def _qcurve(ctx, p0, c, p1):
    """Quadratic bezier p0 -> p1 with control c (as a cubic)."""
    ctx.curve_to(p0[0] + (c[0] - p0[0]) * 2 / 3, p0[1] + (c[1] - p0[1]) * 2 / 3,
                 p1[0] + (c[0] - p1[0]) * 2 / 3, p1[1] + (c[1] - p1[1]) * 2 / 3, p1[0], p1[1])


def _wave(p, base, amp=0.0, ph=0.0, a2=0.0, ph2=0.0, rect=0):
    v = math.sin(TAU * (p + ph))
    if rect == 1:
        v = max(0.0, v)
    elif rect == -1:
        v = min(0.0, v)
    return base + amp * v + (a2 * math.sin(2 * TAU * (p + ph2)) if a2 else 0.0)


# ============================================================================
# 2. CHARACTERS
# ============================================================================
# Head-local frame: origin = centre of the eye line, y down, units = px at s=1.
#   levels: (y, half-width a, front depth f, back depth b) from crown to chin;
#   the 3/4 silhouette is the projection of these cross-section ellipses.
# Torso: spine node heights above the pelvis and cross-section (a, f, b).
def _C(**kw):
    return kw


CHARS = {
    # ------------------------------------------------------------- Tiredness
    "tired": _C(
        seed=11, height=960, sex="m",
        foot_h=30, foot_len=74, foot_r=25, shoe="slipper",
        thigh=187, shin=179, hip_w=42, leg_r=(42, 35, 30), pants="sweat",
        spine=dict(hem=-34, waist=92, chest=190, shoulder=262, neck=280),
        tw=dict(hem=(96, 54, 56), hip=(96, 54, 56), waist=(97, 56, 56), chest=(102, 58, 58),
                shoulder=(98, 48, 48)),
        sw=90, neck_len=46, neck_r=30, arm=(138, 128), arm_r=(31, 27, 24), hand=46,
        top="hoodie", sleeve="long",
        head=dict(levels=[(-124, 0, 0, 0), (-112, 50, 42, 58), (-84, 84, 68, 92), (-44, 99, 82, 102),
                          (0, 101, 86, 98), (34, 97, 86, 86), (62, 86, 82, 64), (86, 62, 74, 38),
                          (100, 30, 64, 14)],
                  chin=106, pivot=0.70, ex=41, ew=27, eh=21, eye="almond", brow_y=-42,
                  brow_len=1.0, brow_th=11.5, nose_y=36, nose="soft", mouth_y=68, mw=27,
                  ear_y=(-6, 40), ear_w=17, hair="mop"),
        col=dict(skin=PAL["t_skin"], skin_sh=PAL["t_skin_sh"], hair=PAL["t_hair"],
                 brow=PAL["t_hair"], iris=PAL["t_iris"], top=PAL["t_hoodie"],
                 top_dk=PAL["t_hoodie_dk"], pants=PAL["t_pants"], pants_dk=_dk(PAL["t_pants"], 0.2),
                 shoe=PAL["t_slipper"], shoe_dk=_dk(PAL["t_slipper"], 0.22), bags=PAL["t_bags"],
                 lip=None),
        posture=dict(lean=0.08, chest=0.06, hunch=0.42, neck=0.30, nod=0.05, al_o=0.02, ar_o=0.02),
        face=dict(lid=0.45, brow=-0.22, bags=1.0, lidshade=0.55),
    ),
    # --------------------------------------------------------- Embarrassment
    "embar": _C(
        seed=23, height=1060, sex="m",
        foot_h=24, foot_len=78, foot_r=19, shoe="loafer",
        thigh=228, shin=222, hip_w=34, leg_r=(27, 22, 18), pants="slacks",
        spine=dict(hem=-26, waist=92, chest=196, shoulder=268, neck=284),
        tw=dict(hem=(78, 44, 46), hip=(78, 44, 46), waist=(76, 44, 44), chest=(84, 48, 48),
                shoulder=(82, 40, 40)),
        sw=80, neck_len=58, neck_r=21, arm=(164, 152), arm_r=(23, 20, 17), hand=46,
        top="labcoat", sleeve="long",
        head=dict(levels=[(-124, 0, 0, 0), (-112, 46, 40, 54), (-84, 80, 64, 88), (-44, 92, 76, 96),
                          (0, 93, 80, 92), (36, 88, 80, 78), (68, 74, 78, 52), (94, 46, 70, 26),
                          (108, 18, 60, 8)],
                  chin=113, pivot=0.70, ex=40, ew=27, eh=27, eye="round", brow_y=-50,
                  brow_len=0.95, brow_th=9.0, nose_y=40, nose="point", mouth_y=74, mw=24,
                  ear_y=(-6, 42), ear_w=19, hair="part", glasses=True, cheek_y=50, cheek_dx=16),
        col=dict(skin=PAL["e_skin"], skin_sh=PAL["e_skin_sh"], hair=PAL["e_hair"],
                 brow=_dk(PAL["e_hair"], 0.34), iris=PAL["e_iris"], top=PAL["e_coat"],
                 top_dk=PAL["e_coat_sh"], vest=PAL["e_vest"], pants=PAL["e_pants"],
                 pants_dk=_dk(PAL["e_pants"], 0.25), shoe="#7a4a2e", shoe_dk="#4f2f1e", lip=None),
        posture=dict(lean=0.05, chest=0.07, hunch=0.22, neck=0.2, nod=0.0),
        face=dict(lid=0.02, brow=0.1),
    ),
    # --------------------------------------------------------------- the Boss
    "boss": _C(
        seed=37, height=1040, sex="f",
        foot_h=34, foot_len=66, foot_r=15, shoe="heel",
        thigh=228, shin=222, hip_w=36, leg_r=(28, 21, 15), pants="trousers",
        spine=dict(hem=-34, waist=96, chest=192, shoulder=262, neck=276),
        tw=dict(hem=(86, 46, 52), hip=(84, 46, 52), waist=(70, 40, 40), chest=(82, 48, 46),
                shoulder=(90, 40, 40)),
        sw=86, neck_len=56, neck_r=20, arm=(154, 144), arm_r=(23, 19, 15), hand=42,
        top="suit", sleeve="long",
        head=dict(levels=[(-120, 0, 0, 0), (-108, 44, 38, 52), (-80, 76, 62, 86), (-40, 88, 74, 92),
                          (0, 88, 76, 88), (34, 84, 76, 74), (66, 68, 74, 46), (92, 36, 66, 18),
                          (106, 12, 58, 6)],
                  chin=110, pivot=0.70, ex=37, ew=26, eh=17, eye="cat", brow_y=-40,
                  brow_len=1.0, brow_th=6.5, nose_y=38, nose="sharp", mouth_y=70, mw=20,
                  ear_y=(-4, 36), ear_w=15, hair="bob"),
        col=dict(skin=PAL["b_skin"], skin_sh=mixc(PAL["b_skin"], "#b98a7c", 0.5), hair=PAL["b_hair"],
                 brow="#8f94a2", iris=PAL["b_iris"], top=PAL["b_suit"], top_dk=PAL["b_suit_dk"],
                 sleeve=mixc(PAL["b_suit"], "#a3abc4", 0.14),
                 pants=PAL["b_suit"], pants_dk=PAL["b_suit_dk"], shoe="#14151b", shoe_dk="#0b0b10",
                 lip=PAL["b_lip"]),
        posture=dict(lean=-0.03, hunch=-0.25, neck=-0.04, nod=-0.06),
        face=dict(lid=0.32, brow=-0.08, lidshade=0.3),
    ),
    # -------------------------------------------------------------- the Guard
    "guard": _C(
        seed=41, height=1000, sex="m",
        foot_h=34, foot_len=78, foot_r=26, shoe="boot",
        thigh=200, shin=192, hip_w=48, leg_r=(46, 39, 33), pants="uniform",
        spine=dict(hem=-30, waist=98, chest=200, shoulder=278, neck=296),
        tw=dict(hem=(112, 64, 64), hip=(112, 64, 64), waist=(116, 70, 62), chest=(122, 70, 64),
                shoulder=(118, 56, 52)),
        sw=110, neck_len=38, neck_r=36, arm=(140, 130), arm_r=(36, 32, 27), hand=52,
        top="uniform", sleeve="long",
        head=dict(levels=[(-120, 0, 0, 0), (-108, 52, 44, 60), (-80, 88, 70, 94), (-40, 102, 84, 104),
                          (0, 104, 88, 100), (36, 104, 90, 90), (68, 98, 88, 72), (92, 78, 82, 46),
                          (106, 40, 74, 18)],
                  chin=112, pivot=0.70, ex=40, ew=21, eh=17, eye="small", brow_y=-36,
                  brow_len=1.08, brow_th=13, nose_y=38, nose="broad", mouth_y=74, mw=26,
                  ear_y=(-6, 40), ear_w=18, hair="cap", mustache=True),
        col=dict(skin=PAL["g_skin"], skin_sh=_dk(PAL["g_skin"], 0.2), hair="#231916",
                 brow="#231916", iris="#3b2618", top=PAL["g_uniform"], top_dk=_dk(PAL["g_uniform"], 0.3),
                 pants=_dk(PAL["g_uniform"], 0.12), pants_dk=_dk(PAL["g_uniform"], 0.35),
                 shoe="#1b1b22", shoe_dk="#0d0d12", lip=None),
        posture=dict(lean=-0.02, chest=-0.05, hunch=0.05, neck=0.05, al_o=0.12, ar_o=0.12),
        face=dict(lid=0.16, brow=-0.05),
    ),
    # ------------------------------------------------------- the Receptionist
    "recep": _C(
        seed=53, height=990, sex="f",
        foot_h=26, foot_len=64, foot_r=16, shoe="flat",
        thigh=200, shin=192, hip_w=38, leg_r=(31, 24, 17), pants="trousers",
        spine=dict(hem=-30, waist=90, chest=184, shoulder=252, neck=266),
        tw=dict(hem=(88, 48, 54), hip=(86, 48, 54), waist=(74, 42, 42), chest=(82, 50, 46),
                shoulder=(80, 40, 40)),
        sw=78, neck_len=50, neck_r=20, arm=(146, 136), arm_r=(24, 21, 17), hand=42,
        top="cardigan", sleeve="long",
        head=dict(levels=[(-120, 0, 0, 0), (-108, 46, 40, 54), (-80, 80, 64, 88), (-40, 92, 76, 94),
                          (0, 93, 78, 90), (34, 88, 78, 76), (64, 74, 76, 50), (90, 44, 68, 22),
                          (104, 14, 60, 6)],
                  chin=108, pivot=0.70, ex=38, ew=25, eh=19, eye="almond", brow_y=-40,
                  brow_len=0.95, brow_th=7.5, nose_y=38, nose="soft", mouth_y=70, mw=20,
                  ear_y=(-4, 38), ear_w=15, hair="bun"),
        col=dict(skin=PAL["r_skin"], skin_sh=mixc(PAL["r_skin"], "#a8704e", 0.45), hair="#4a2f25",
                 brow="#3e271f", iris="#5b3b2a", top=PAL["r_top"], top_dk=_dk(PAL["r_top"], 0.25),
                 blouse="#f4f1f6", pants="#3c3a4a", pants_dk="#2a2836", shoe="#2b2530",
                 shoe_dk="#1a161d", lip="#c4587a"),
        posture=dict(lean=0.03, hunch=0.15, neck=0.12),
        face=dict(lid=0.5, brow=-0.12, lidshade=0.35),
    ),
}

# outfit overrides (colour + garment swaps)
OUTFITS = {
    ("tired", "printer"): dict(top="polo", sleeve="short", shoe="sneaker", pants="khaki",
                               col=dict(top=PAL["polo"], top_dk=_dk(PAL["polo"], 0.2),
                                        pants=PAL["khaki"], pants_dk=_dk(PAL["khaki"], 0.22),
                                        shoe="#6b4f3a", shoe_dk="#46321f")),
    ("tired", "sewer"): dict(wet=True, col=dict(hair=_dk(PAL["t_hair"], 0.15),
                                                top=_dk(PAL["t_hoodie"], 0.1),
                                                shoe=mixc(PAL["t_slipper"], "#5b7a6a", 0.45),
                                                shoe_dk=_dk(mixc(PAL["t_slipper"], "#5b7a6a", 0.45), 0.25))),
}

# Furniture heights relative to the ground point (px at s=1), per character.
#   SEAT_H : chair seat surface (sit_chair / sit_game / sit_desk)
#   DESK_H : desk / counter top (sit_desk, type, cover_sweater, slide)
#   SILL_H : window sill line (look_window)
SEAT_H = {k: int(c["shin"] + c["foot_h"] - c["leg_r"][0] * 0.8) for k, c in CHARS.items()}
DESK_H = {k: int(c["height"] * 0.41) for k, c in CHARS.items()}
SILL_H = {k: int(c["height"] * 0.56) for k, c in CHARS.items()}


# ============================================================================
# 3. HANDS  (4-finger cartoon hands; numeric so shapes blend)
# ============================================================================
# Hand frame: origin = wrist, +x = toward the fingers, +y = thumb side.
# Units: palm length = 1 (scaled by CHARS[who]["hand"]).
# fingers (index, middle, ring, pinky): (spread angle, length, bend1, bend2)
#   bends curl toward the thumb side (+y).  thumb: (angle, length, bend).
#   hold: (x, y) grip / contact point used for the hand anchor + hold().
def _H(palm=1.0, f=None, th=(0.6, 0.72, 0.2), hold=(0.85, 0.05), cup=0.0):
    return dict(palm=palm, f=f, th=th, hold=hold, cup=cup)


_CURL = (0.0, 0.52, 1.55, 1.6)
HANDS = {
    "open":    _H(f=[(0.30, 0.86, 0.06, 0.05), (0.08, 0.95, 0.04, 0.04), (-0.13, 0.87, 0.04, 0.04),
                     (-0.36, 0.67, 0.06, 0.05)], th=(1.0, 0.78, 0.08), hold=(0.75, 0.0)),
    "relaxed": _H(f=[(0.12, 0.84, 0.34, 0.34), (0.03, 0.92, 0.38, 0.4), (-0.06, 0.85, 0.42, 0.44),
                     (-0.15, 0.66, 0.48, 0.5)], th=(0.5, 0.7, 0.28), hold=(0.8, 0.12)),
    "fist":    _H(palm=0.86, f=[(0.06,) + _CURL[1:], (0.0,) + _CURL[1:], (-0.05,) + _CURL[1:],
                                (-0.1, 0.46, 1.6, 1.6)], th=(1.3, 0.6, 1.25), hold=(0.8, 0.1)),
    "point":   _H(palm=0.9, f=[(0.0, 0.98, 0.0, 0.0), (0.0,) + _CURL[1:], (-0.05,) + _CURL[1:],
                               (-0.1, 0.46, 1.6, 1.6)], th=(0.82, 0.72, 0.05), hold=(1.6, 0.34)),
    "grip":    _H(palm=0.92, f=[(0.06, 0.86, 1.2, 1.35), (0.0, 0.92, 1.25, 1.35), (-0.05, 0.86, 1.3, 1.35),
                                (-0.1, 0.68, 1.35, 1.4)], th=(1.15, 0.68, 0.95), hold=(1.02, 0.22)),
    "splay":   _H(f=[(0.50, 0.92, 0.0, 0.0), (0.17, 1.0, 0.0, 0.0), (-0.17, 0.93, 0.0, 0.0),
                     (-0.5, 0.72, 0.0, 0.0)], th=(1.3, 0.8, 0.0), hold=(0.7, 0.0)),
    "pinch":   _H(f=[(0.3, 0.84, 0.85, 0.75), (0.0, 0.8, 1.25, 1.3), (-0.05, 0.76, 1.3, 1.35),
                     (-0.1, 0.6, 1.35, 1.4)], th=(0.62, 0.84, 0.3), hold=(1.42, 0.52)),
    "flat":    _H(f=[(0.05, 0.88, 0.0, 0.0), (0.0, 0.97, 0.0, 0.0), (-0.05, 0.89, 0.0, 0.0),
                     (-0.1, 0.69, 0.0, 0.0)], th=(0.42, 0.75, 0.04), hold=(0.85, 0.0)),
    "claw":    _H(f=[(0.52, 0.86, 0.55, 0.6), (0.18, 0.95, 0.55, 0.6), (-0.16, 0.88, 0.55, 0.6),
                     (-0.5, 0.7, 0.6, 0.65)], th=(1.15, 0.75, 0.5), hold=(0.8, 0.1)),
    "cup":     _H(f=[(0.1, 0.86, 0.22, 0.2), (0.02, 0.94, 0.22, 0.2), (-0.06, 0.87, 0.24, 0.22),
                     (-0.14, 0.67, 0.28, 0.25)], th=(0.75, 0.74, 0.12), hold=(0.7, 0.3), cup=1.0),
}


def _hand_vec(name):
    h = HANDS[name] if isinstance(name, str) else name
    v = [h["palm"], h["cup"], h["hold"][0], h["hold"][1]]
    for f in h["f"]:
        v.extend(f)
    v.extend(h["th"])
    return v


_HAND_VEC = {k: _hand_vec(k) for k in HANDS}


# ============================================================================
# 4. FACE
# ============================================================================
# Every key is ADDITIVE (expr deltas and `face=` deltas are summed onto the
# character's base).  Eye keys also accept _l / _r suffixes (per eye).
EYE_KEYS = ("brow", "brow_ang", "brow_in", "brow_out", "lid", "lid_ang", "lower",
            "pupil", "iris", "hl", "eye_size", "look_x", "look_y")
FACE_DEFAULTS = dict(
    # eyes / brows (per eye with _l/_r)
    brow=0.0, brow_ang=0.0, brow_in=0.0, brow_out=0.0, lid=0.0, lid_ang=0.0, lower=0.0,
    pupil=1.0, iris=1.0, hl=1.0, eye_size=1.0, look_x=0.0, look_y=0.0,
    # mouth
    curve=0.0, width=1.0, asym=0.0, lip_up=0.0, lip_low=0.0, open=0.0, teeth=0.0, tongue=0.0,
    frown=0.0, press=0.0, smirk=0.0, jaw=0.0, wobble=0.0,
    # misc
    cheek=0.0, flare=0.0, head_tilt=0.0, head_turn=0.0, head_nod=0.0, squash=0.0,
    bags=0.0, lidshade=0.0, blush=0.0, focus=1.0, tear=0.0,
)

# Expression deltas (relative to the character's resting face).
EXPR = {
    # --- basics
    "neutral":    {},
    "bored":      dict(lid=0.12, lid_ang=0.12, brow=-0.08, curve=-0.12, press=0.1, look_y=0.05),
    "deadpan":    dict(lid=0.08, brow=-0.04, press=0.22, width=0.9),
    "annoyed":    dict(brow=-0.2, brow_ang=-0.55, lid=0.14, lid_ang=-0.12, curve=-0.3, press=0.35,
                       asym=0.15, flare=0.3),
    "unamused":   dict(lid=0.24, brow_l=-0.1, brow_r=0.28, brow_ang_r=0.1, curve=-0.2, press=0.35,
                       smirk=-0.15, lid_ang=0.06),
    "squint":     dict(lid=0.2, lower=0.36, brow=-0.3, brow_ang=-0.35, curve=-0.12, press=0.15,
                       cheek=0.15),
    "sigh":       dict(lid=0.36, brow=0.12, brow_ang=0.32, open=0.16, width=0.78, lip_up=0.05,
                       head_nod=0.12, cheek=0.25, lid_ang=0.12),
    "content":    dict(lid=0.62, lower=0.92, curve=0.5, brow=0.12, brow_ang=0.18, cheek=0.1,
                       head_tilt=0.04),
    "soft_smile": dict(curve=0.32, lower=0.16, lid=0.05, brow=0.05, brow_ang=0.08),
    "curious":    dict(brow_l=0.42, brow_r=-0.04, brow_ang_l=0.12, lid=-0.08, lid_l=-0.08,
                       head_tilt=0.12, curve=0.04, pupil=1.1, asym=0.12),
    # --- big reactions
    "surprised":  dict(brow=0.78, lid=-0.34, pupil=0.78, open=0.36, width=0.66, eye_size=1.08,
                       squash=-0.04),
    "alarmed":    dict(brow=0.68, brow_ang=0.4, lid=-0.34, pupil=0.62, open=0.24, width=1.08,
                       curve=-0.42, teeth=0.5, eye_size=1.08),
    "scream":     dict(brow=0.92, brow_ang=0.55, lid=-0.4, pupil=0.45, open=1.0, width=1.18,
                       curve=-0.35, tongue=0.85, teeth=0.6, lip_up=0.4, squash=-0.12,
                       eye_size=1.14, flare=0.6),
    "pain":       dict(lid=0.9, lower=0.5, brow=-0.1, brow_ang=0.75, brow_in=0.3, open=0.3,
                       teeth=1.0, width=1.22, curve=-0.5, cheek=0.2, squash=0.04, flare=0.5),
    "groggy":     dict(lid=0.36, lid_l=0.12, brow=0.06, brow_ang=0.22, curve=-0.06, open=0.06,
                       head_tilt=0.08, pupil=1.12, focus=0.6, asym=0.15),
    "dazed":      dict(lid_l=0.12, lid_r=0.38, lid_ang_l=0.15, brow_l=0.25, brow_r=-0.05,
                       brow_ang=0.2, pupil=0.75, open=0.16, width=0.8, asym=0.35, wobble=0.35,
                       look_x_l=0.2, look_y_l=-0.12, look_x_r=-0.18, look_y_r=0.18, focus=0.0,
                       head_tilt=0.1),
    "determined": dict(lid=-0.28, brow=-0.2, brow_ang=-0.45, lower=0.12, press=0.42, curve=-0.06,
                       pupil=0.95, hl=1.2, head_nod=0.05),
    "awe":        dict(lid=-0.46, brow=0.52, brow_ang=0.26, pupil=1.25, hl=1.45, open=0.3,
                       width=0.82, lip_low=0.1, eye_size=1.06),
    "sad":        dict(brow=0.1, brow_ang=0.68, brow_in=0.2, lid=0.16, lid_ang=0.3, curve=-0.42,
                       frown=0.3, pupil=1.22, hl=1.35, look_y=0.18, head_nod=0.08),
    # --- Embarrassment's nervous range
    "nervous_smile": dict(curve=0.58, width=1.32, open=0.22, teeth=1.0, brow=0.25, brow_ang=0.48,
                          lid=-0.06, wobble=0.5, pupil=0.72, cheek=0.15, blush=0.35),
    "panic":      dict(brow=0.82, brow_ang=0.62, lid=-0.36, pupil=0.45, open=0.6, width=1.1,
                       curve=-0.5, teeth=0.5, wobble=0.45, eye_size=1.1, blush=0.25),
    "terrified":  dict(brow=0.92, brow_ang=0.72, lid=-0.42, pupil=0.32, iris=0.72, open=0.42,
                       width=1.2, teeth=1.0, curve=-0.62, wobble=0.6, squash=-0.06, eye_size=1.14),
    "relieved":   dict(lid=0.42, lower=0.3, brow=0.1, brow_ang=0.36, curve=0.32, open=0.12, width=0.9,
                       cheek=0.2, head_nod=-0.06),
    "pleading":   dict(brow=0.26, brow_ang=0.82, brow_in=0.25, lid=-0.1, pupil=1.38, hl=1.6,
                       curve=-0.2, wobble=0.35, lower=0.1, frown=0.2, blush=0.25),
    "guilty":     dict(brow=0.05, brow_ang=0.46, lid=0.2, lid_ang=0.1, look_x=-0.35, look_y=0.4,
                       curve=-0.16, press=0.4, asym=-0.2, blush=0.4),
    "frozen_shock": dict(eye_size=1.3, lid=-0.45, brow=1.0, pupil=0.3, iris=0.0, hl=0.4, press=0.65,
                         width=0.78, wobble=1.0, curve=-0.12, squash=-0.05, blush=0.12),
    "whisper":    dict(open=0.12, width=0.52, lip_up=0.08, brow=0.2, brow_ang=0.32, lid=-0.04,
                       curve=-0.02),
    "sheepish":   dict(curve=0.36, asym=0.25, smirk=0.2, brow=0.12, brow_ang=0.42, lid=0.16,
                       look_x=-0.3, look_y=0.25, teeth=0.7, open=0.08, width=1.12, blush=0.5),
    "fake_cool":  dict(lid=0.26, brow_l=0.3, brow_r=-0.06, curve=0.3, smirk=0.5, wobble=0.22,
                       brow_ang=-0.06, blush=0.2, head_tilt=-0.06),
    # --- others
    "cold":       dict(lid=0.1, brow=-0.05, press=0.32, curve=-0.05),
    "stern":      dict(brow=-0.26, brow_ang=-0.46, lid=0.12, press=0.5, curve=-0.26),
    "yawn":       dict(lid=1.0, lower=0.4, brow=0.42, brow_ang=0.3, open=1.0, width=0.8, tongue=0.6,
                       teeth=0.3, squash=-0.14, head_nod=-0.25, lip_up=0.2, cheek=0.3),
}

# Per-character expression gains (applied to EXPR deltas, not to `face=`):
#   key -> multiplier;  "key-" applies to negative deltas only;  "*" = all.
EXPR_GAIN = {
    "tired": {"lid-": 0.5, "eye_size": 0.6, "brow": 0.85, "blush": 0.3},
    "boss": {"*": 0.4, "blush": 0.15},
    "recep": {"lid-": 0.7, "blush": 0.3},
    "guard": {"blush": 0.3},
}
# Per-character additive tweaks for specific expressions (after gain).
CHAR_EXPR = {
    "tired": {
        "determined": dict(lid=-0.2, brow_ang=-0.1, lower=0.05),   # lids lift: rare and important
        "awe": dict(lid=-0.26, brow=0.1),                          # fully open: the payoff
        "bored": dict(lid=0.04),
    },
    "boss": {"cold": dict(lid=0.06, press=0.15), "stern": dict(brow_ang=-0.15, lid=0.05)},
}


# ============================================================================
# 5. POSES
# ============================================================================
# A pose is a dict of joint values layered on top of POSE_DEFAULTS ("stand").
# Values may be numbers, hand names (strings), or W(...) waves (cycles; they
# are evaluated at phase = pose_t / period).  Keys:
#   global : turn dx dy rot plant hip_h lift plant_hands lean chest side twist
#            hip_roll hunch neck nod tilt head_yaw breath sway posture coat_trail
#   arm  a{l,r}_ : p o e eo w (FK, 3D)  h (hand) tf (thumb side +1/-1) hide
#            ik (0..1 weight of 2D IK) tx ty tz (ground target in units of the
#            character height: x outward, y above ground, z forward)
#            th hx hy (head-relative target, head px, x outward) grab (reach the
#            other forearm) cup (reach the headphone cup) wa wabs (absolute hand
#            angle, 0 = forward) bend (+1 elbow out/down, -1 elbow in/up)
#            layer ('back'|'mid'|'front') thumb fing (thumb / finger animation)
#   leg  l{l,r}_ : p o k ko a
def W(base, amp=0.0, ph=0.0, a2=0.0, ph2=0.0, r=0):
    """Wave value for cycle tables: base + amp*sin(2pi(p+ph)) + a2*sin(4pi(p+ph2)).
    r=1 keeps only the positive half (rectified)."""
    return ("~", base, amp, ph, a2, ph2, r)


def K(*keys):
    """Keyframed value for cycle tables: K((phase, value), ...) with phases 0..1, eased
    between keys (smoothstep), wrapping from the last key back to the first.  Use it for
    asymmetric cycles (a punch: slow wind-up, fast strike)."""
    return ("k", tuple(sorted(keys)))


def _keyval(keys, p):
    n = len(keys)
    if p < keys[0][0]:
        p += 1.0
    for i in range(n):
        p0, v0 = keys[i]
        p1, v1 = keys[(i + 1) % n]
        if i == n - 1:
            p1 += 1.0
        if p0 <= p <= p1:
            if p1 - p0 < 1e-9:
                return v1
            return v0 + (v1 - v0) * smoothstep((p - p0) / (p1 - p0))
    return keys[-1][1]


def A(side, p=None, o=None, e=None, eo=None, w=None, h=None, **kw):
    d = {}
    for k, v in (("p", p), ("o", o), ("e", e), ("eo", eo), ("w", w), ("h", h)):
        if v is not None:
            d[f"a{side}_{k}"] = v
    for k, v in kw.items():
        d[f"a{side}_{k}"] = v
    return d


def IK(side, tx, ty, tz=0.1, h=None, w=1.0, **kw):
    d = {f"a{side}_ik": w, f"a{side}_tx": tx, f"a{side}_ty": ty, f"a{side}_tz": tz}
    if h is not None:
        d[f"a{side}_h"] = h
    for k, v in kw.items():
        d[f"a{side}_{k}"] = v
    return d


def HK(side, hx, hy, h=None, w=1.0, **kw):
    """IK target relative to the head centre (head px; x outward from the face centre)."""
    d = {f"a{side}_ik": w, f"a{side}_th": 1.0, f"a{side}_hx": hx, f"a{side}_hy": hy}
    if h is not None:
        d[f"a{side}_h"] = h
    for k, v in kw.items():
        d[f"a{side}_{k}"] = v
    return d


def L(side, p=None, o=None, k=None, a=None, ko=None):
    d = {}
    for kk, v in (("p", p), ("o", o), ("k", k), ("a", a), ("ko", ko)):
        if v is not None:
            d[f"l{side}_{kk}"] = v
    return d


def P(*parts, **kw):
    d = {}
    for p in parts:
        d.update(p)
    d.update(kw)
    return d


POSE_DEFAULTS = dict(
    turn=0.0, dx=0.0, dy=0.0, rot=0.0, plant=1.0, hip_h=0.0, lift=0.0, plant_hands=0.0, plant_all=0.0, plant_butt=0.0,
    lean=0.0, chest=0.0, side=0.0, twist=0.0, hip_roll=0.0, hunch=0.0, neck=0.0, nod=0.0,
    tilt=0.0, head_yaw=0.0, breath=1.0, sway=1.0, posture=1.0, coat_trail=0.0,
    hold=0.0, hold_order=0.0, controller=0.0, counter=0.0,
    hand_top=0.0, head_face=0.0, hold_hand=1.0, pillow=0.0,
)
for _s in "lr":
    POSE_DEFAULTS.update({f"a{_s}_p": 0.05, f"a{_s}_o": 0.1, f"a{_s}_e": 0.2, f"a{_s}_eo": 0.0,
                          f"a{_s}_w": 0.0, f"a{_s}_h": "relaxed", f"a{_s}_tf": 1.0, f"a{_s}_hide": 0.0,
                          f"a{_s}_ik": 0.0, f"a{_s}_tx": 0.1, f"a{_s}_ty": 0.5, f"a{_s}_tz": 0.1,
                          f"a{_s}_th": 0.0, f"a{_s}_hx": 0.0, f"a{_s}_hy": 0.0, f"a{_s}_hz": 18.0, f"a{_s}_grab": 0.0,
                          f"a{_s}_cup": 0.0, f"a{_s}_wa": 0.0, f"a{_s}_wabs": 0.0, f"a{_s}_bend": 1.0,
                          f"a{_s}_layer": "", f"a{_s}_thumb": 0.0, f"a{_s}_fing": 0.0})
    POSE_DEFAULTS.update({f"l{_s}_p": 0.0, f"l{_s}_o": 0.05, f"l{_s}_k": 0.03, f"l{_s}_ko": 0.0,
                          f"l{_s}_a": 0.0})

_SEAT = dict(plant=1.0, **L("l", 1.45, 0.1, 1.45, 0.0), **L("r", 1.45, 0.1, 1.45, 0.0))
_HANDS_BACK = P(A("l", -0.3, 0.16, 0.5, -0.75, h="relaxed", layer="back"),
                A("r", -0.3, 0.16, 0.5, -0.75, h="relaxed", layer="back"))
_CROSSED = P(A("l", 0.3, 0.16, 1.3, -1.32, 0.1, h="relaxed", layer="front", tf=1.0),
             A("r", 0.32, 0.16, 1.22, -1.25, 0.25, h="fist", layer="mid"), hunch=0.15)

POSES = {
    # ------------------------------------------------------------ standing
    "stand": {},
    "slouch": P(A("l", -0.02, 0.06, 0.12), A("r", -0.02, 0.06, 0.12), L("l", k=0.1), L("r", k=0.08),
                lean=0.16, chest=0.12, hunch=0.75, neck=0.42, nod=0.1, hip_roll=0.05),
    "arms_crossed": P(_CROSSED, L("l", o=0.09), L("r", o=0.09)),
    "hands_pockets": P(A("l", 0.0, 0.26, 0.32, -0.42, hide=1.0), A("r", 0.0, 0.26, 0.32, -0.42, hide=1.0),
                       hunch=0.35),
    "hands_behind_back": P(_HANDS_BACK, chest=-0.04),
    "attention": P(A("l", 0.0, 0.06, 0.02, h="flat", tf=1.0), A("r", 0.0, 0.06, 0.02, h="flat"),
                   L("l", o=0.0, k=0.0), L("r", o=0.0, k=0.0), posture=0.1, lean=-0.03, chest=-0.1,
                   hunch=-0.35, neck=-0.12, nod=-0.16, breath=0.35, sway=0.0),
    "awkward": P(IK("l", 0.02, 0.43, 0.12, "relaxed", wa=1.5, wabs=0.6),
                 IK("r", 0.0, 0.42, 0.13, "relaxed", wa=1.5, wabs=0.6),
                 L("l", o=-0.02, k=0.12), L("r", o=-0.02, k=0.12), hunch=1.0, lean=0.03, neck=0.12,
                 nod=0.06),
    "sheepish": P(HK("r", 70, -40, "claw", layer="mid", bend=-1.0, wa=-1.9, wabs=0.7),
                  A("l", 0.02, 0.05, 0.15), hunch=0.6, tilt=-0.12, nod=0.08, lean=0.03),
    "plead": P(IK("l", -0.005, 0.57, 0.17, "flat", wa=-1.45, wabs=0.9, layer="front"),
               IK("r", -0.005, 0.57, 0.17, "flat", wa=-1.45, wabs=0.9, layer="front"),
               lean=0.1, hunch=0.5, nod=-0.08, neck=0.1, **L("l", k=0.12), **L("r", k=0.12)),
    "cover_eyes": P(HK("l", 16, 2, "flat", layer="front", wa=-1.7, wabs=0.85, bend=1.0),
                    HK("r", 16, 2, "flat", layer="front", wa=-1.7, wabs=0.85, bend=1.0),
                    hunch=0.7, nod=0.12, neck=0.1),
    "peek": P(HK("l", 8, -6, "splay", layer="front", wa=-1.62, wabs=0.9),
              HK("r", 8, -6, "splay", layer="front", wa=-1.62, wabs=0.9),
              hunch=0.7, nod=0.08, neck=0.1),
    "facepalm": P(HK("r", -6, -28, "flat", layer="front", wa=-1.9, wabs=0.8),
                  A("l", 0.02, 0.06, 0.15), nod=0.22, tilt=-0.1, hunch=0.4, neck=0.2),
    "shrug": P(A("l", 0.1, 0.3, 1.6, 0.8, -0.3, h="open", tf=-1.0),
               A("r", 0.1, 0.3, 1.6, 0.8, -0.3, h="open", tf=-1.0), hunch=1.5, tilt=0.13, nod=0.04,
               neck=-0.04),
    "point": P(A("r", 0.3, 1.3, 0.06, 0.0, 0.0, h="point", tf=1.0), A("l", 0.02, 0.06, 0.15),
               side=-0.03, turn=0.25),
    "hold_arm": P(A("l", 0.12, -0.1, 0.95, -1.0, 0.0, h="relaxed"),
                  P(A("r", 0.2, 0.1, 1.0), {"ar_ik": 1.0, "ar_grab": 1.0, "ar_h": "grip", "ar_layer": "front"}),
                  hunch=0.55, nod=0.08),
    "lean_in": P(_HANDS_BACK, L("l", -0.12, k=0.12), L("r", 0.12, k=0.05), lean=0.48, chest=0.12,
                 neck=0.28, nod=-0.18, hunch=0.25),
    "look_window": P(IK("l", 0.12, "sill", 0.26, "flat", wa=0.1, wabs=0.9),
                     IK("r", 0.12, "sill", 0.26, "flat", wa=0.1, wabs=0.9),
                     lean=0.32, neck=0.12, nod=-0.08, **L("l", k=0.06), **L("r", k=0.06)),
    # ------------------------------------------------------------ seated / floor
    "sit_chair": P(_SEAT, A("l", 0.32, 0.12, 0.85, -0.1, 0.3), A("r", 0.32, 0.12, 0.85, -0.1, 0.3)),
    "sit_game": P(_SEAT, IK("l", 0.075, "seat+0.12", 0.24, "grip", layer="front", wa=-1.25, wabs=0.7),
                  IK("r", 0.075, "seat+0.12", 0.24, "grip", layer="front", wa=-1.25, wabs=0.7),
                  lean=0.3, chest=0.1, hunch=0.65, neck=0.5, nod=-0.16, controller=1.0),
    "sit_desk": P(_SEAT, IK("l", 0.1, "desk", 0.3, "relaxed", wa=0.25, wabs=0.85, layer="front"),
                  IK("r", 0.1, "desk", 0.3, "relaxed", wa=0.25, wabs=0.85, layer="front"),
                  lean=0.18, hunch=0.3, neck=0.15),
    "sit_floor": P(plant=1.0, plant_butt=1.0, lean=-0.22, chest=0.14, neck=0.2, tilt=0.12, hunch=0.3,
                   **IK("l", 0.17, 0.02, -0.06, "flat", layer="back"), **IK("r", 0.17, 0.02, -0.06, "flat",
                                                                            layer="back"),
                   **L("l", 1.32, 0.42, 0.28, 0.25), **L("r", 1.3, 0.38, 0.36, 0.2), sway=0.0),
    "heap": P(plant=1.0, plant_all=1.0, rot=2.45, lean=0.45, chest=0.25, neck=0.3, tilt=-1.75, side=-0.1,
              **A("l", 0.3, 1.5, 0.5, 0.4, h="open", layer="back"), **A("r", 0.6, 1.2, 0.9, 0.3, h="relaxed"),
              **L("l", 0.9, 0.35, 1.3, 0.3), **L("r", 0.35, 0.1, 0.5, 0.2), sway=0.0, breath=0.5,
              posture=0.0),
    "lie_back": P(plant=1.0, plant_all=1.0, rot=-math.pi / 2, **A("l", 0.0, 0.38, 0.25, h="open"),
                  **A("r", 0.0, 0.42, 0.35, h="relaxed"), **L("l", 0.0, 0.12, 0.1, 0.0),
                  **L("r", 0.18, 0.06, 0.5, 0.0), sway=0.0, breath=0.6),
    "sit_up": P(plant=1.0, plant_butt=1.0, lean=-0.5, chest=0.25, neck=0.42, tilt=0.18, hunch=0.5,
                **IK("r", 0.15, 0.02, -0.2, "flat", layer="back", bend=-1.0),
                **A("l", 0.6, 0.2, 0.8, -0.2, h="relaxed"),
                **L("l", 1.42, 0.12, 0.1, 0.3), **L("r", 1.25, 0.2, 0.7, 0.2), sway=0.0),
    "crouch": P(L("l", 1.25, 0.28, 2.2, 0.2), L("r", 1.0, 0.22, 2.25, 0.25), lean=0.7, chest=0.1,
                neck=-0.25, nod=-0.18, hunch=0.3,
                **IK("r", 0.1, 0.1, 0.34, "open", wa=0.3, wabs=0.7), **A("l", 0.9, 0.2, 0.6, -0.5)),
    "cover_sweater": P(IK("l", 0.04, "desk", 0.3, "flat", wa=0.15, wabs=0.95, layer="front"),
                       IK("r", 0.04, "desk", 0.32, "flat", wa=0.15, wabs=0.95, layer="front"),
                       lean=0.78, chest=0.12, hunch=0.5, neck=-0.1, nod=-0.25,
                       **L("l", -0.15, k=0.18), **L("r", 0.1, k=0.1)),
    "back_away": P(IK("l", 0.14, 0.62, 0.12, "open", tf=-1.0, wa=-1.3, wabs=0.85),
                   IK("r", 0.14, 0.62, 0.12, "open", tf=-1.0, wa=-1.3, wabs=0.85),
                   lean=-0.2, chest=-0.05, hunch=0.65, nod=0.08, **L("l", 0.25, k=0.18),
                   **L("r", -0.22, k=0.06)),
    "arm_jerk": P(A("r", 0.55, 1.42, 0.0, 0.0, 0.25, h="splay"), A("l", 0.05, 0.08, 0.3),
                  side=-0.1, tilt=0.14, hunch=0.5, twist=0.1),
    "hands_up_small": P(A("l", 0.15, 0.5, 2.55, -0.4, 0.0, h="open", tf=-1.0),
                        A("r", 0.15, 0.5, 2.55, -0.4, 0.0, h="open", tf=-1.0), hunch=0.7, lean=-0.05),
    "catch": P(A("l", 1.32, 0.22, 0.15, 0.0, -0.1, h="claw"), A("r", 1.32, 0.22, 0.15, 0.0, -0.1, h="claw"),
               lean=0.3, chest=0.1, **L("l", 0.62, 0.1, 0.65, 0.2), **L("r", -0.38, 0.06, 0.15)),
    "cradle": P(IK("r", -0.02, 0.52, 0.16, "cup", layer="mid", tf=-1.0, wa=0.0, wabs=0.5),
                IK("l", 0.02, 0.63, 0.18, "relaxed", layer="front", wa=0.6, wabs=0.5),
                hold=2.0, lean=-0.04, hunch=0.3, nod=0.15, tilt=0.06),
    "carry_front": P(IK("l", 0.13, 0.5, 0.18, "grip", wa=1.1, wabs=0.8),
                     IK("r", 0.13, 0.5, 0.18, "grip", wa=1.1, wabs=0.8),
                     hold=2.0, lean=-0.07, hunch=0.2),
    "hold_side": P(A("r", 0.02, 0.12, 0.05, h="grip", tf=1.0), hold=1.0, side=-0.04),
    "present": P(A("r", 0.38, 0.12, 1.12, 0.0, -0.15, h="cup", tf=-1.0), hold=1.0, hold_order=1.0,
                 lean=0.06),
    "slide": P(IK("r", 0.06, "desk", 0.5, "flat", wa=0.05, wabs=1.0, layer="front"),
               IK("l", 0.14, "desk", 0.24, "relaxed", wa=0.3, wabs=0.9, layer="front"), lean=0.5,
               chest=0.1, neck=-0.15, nod=-0.1, **L("l", -0.1, k=0.1)),
    "leap_scared": P(A("l", 0.2, 1.35, 0.35, 0.95, 0.0, h="splay"), A("r", 0.2, 1.35, 0.35, 0.95, 0.0, h="splay"),
                     L("l", 0.45, 0.55, 0.85, -0.3), L("r", 0.25, 0.5, 0.6, -0.3), lift=170.0,
                     lean=-0.1, hunch=0.8, sway=0.0),
    "climb": P(plant=0.0, hip_h=-0.42, lean=0.42, chest=0.15, neck=-0.1, nod=-0.1, hunch=0.6,
               **IK("l", 0.13, 0.0, 0.16, "flat", wa=0.1, wabs=0.9, layer="front"),
               **IK("r", 0.13, 0.0, 0.16, "flat", wa=0.1, wabs=0.9, layer="front"),
               **L("l", -0.1, 0.06, 0.4, -0.5), **L("r", 0.2, 0.08, 0.6, -0.5), sway=0.0, posture=0.3),
    "pick_up": P(L("l", 1.1, 0.25, 1.9, 0.2), L("r", 0.8, 0.18, 2.0, 0.3), lean=0.95, chest=0.15,
                 neck=-0.45, nod=-0.2, **IK("r", 0.06, 0.02, 0.3, "grip", wa=1.3, wabs=0.7),
                 **A("l", 0.7, 0.3, 0.6, -0.3)),
    "throw": P(HK("r", 60, -100, "grip", hz=-90, layer="back", wa=-2.2, wabs=0.5),
               A("l", 1.25, 0.35, 0.2, h="open"), twist=-0.3, lean=-0.14, side=0.08, hold=1.0,
               **L("l", 0.45, 0.1, 0.2), **L("r", -0.2, 0.1, 0.25)),
    "headphones_on": P(IK("l", 0, 0, cup=1.0, h="grip", wa=-1.4, wabs=0.6, layer="front"),
                       IK("r", 0, 0, cup=1.0, h="grip", wa=-1.4, wabs=0.6, layer="front"), hunch=0.4),
    "yawn": P(HK("r", -8, 62, "relaxed", layer="front", wa=-2.2, wabs=0.7), A("l", 0.0, 0.1, 0.2),
              lean=-0.1, chest=-0.12, nod=-0.18, neck=-0.1),
    "fall": P(A("l", W(0.4, 0.3, 0.0), W(2.1, 0.35, 0.1, a2=0.1), W(0.8, 0.4, 0.3), 0.2, h="splay"),
              A("r", W(0.4, 0.3, 0.5), W(2.1, 0.35, 0.6, a2=0.1), W(0.8, 0.4, 0.8), 0.2, h="splay"),
              L("l", W(0.8, 0.3, 0.2), 0.35, W(1.0, 0.4, 0.4), -0.3),
              L("r", W(0.6, 0.3, 0.7), 0.3, W(0.9, 0.4, 0.9), -0.3), lean=-0.25, nod=-0.2, sway=0.0,
              period=0.5),
    "flip": P(A("l", 0.7, 0.3, 0.8, -0.3, h="grip"), A("r", 0.7, 0.3, 0.8, -0.3, h="grip"),
              L("l", 2.1, 0.12, 2.5, 0.2), L("r", 2.1, 0.12, 2.5, 0.2), lean=0.6, chest=0.3, nod=0.35,
              neck=0.3, hunch=0.6, sway=0.0),
}

# ---------------------------------------------------------------------------
# Animated cycles: name -> (period seconds, base pose, wave table)
# ---------------------------------------------------------------------------
_WALK_LEGS = P(L("l", W(0.0, 0.42, 0.0), 0.04, W(0.06, 0.78, 0.22, r=1), W(0.02, 0.26, 0.02)),
               L("r", W(0.0, 0.42, 0.5), 0.04, W(0.06, 0.78, 0.72, r=1), W(0.02, 0.26, 0.52)))
_RUN_LEGS = P(L("l", W(0.18, 0.78, 0.0), 0.05, W(0.4, 1.3, 0.16, r=1), W(-0.05, 0.35, 0.0)),
              L("r", W(0.18, 0.78, 0.5), 0.05, W(0.4, 1.3, 0.66, r=1), W(-0.05, 0.35, 0.5)))
CYCLES = {
    # ------------------------------------------------------------ locomotion
    "walk": (1.0, "stand", P(_WALK_LEGS,
                             A("l", W(0.02, 0.36, 0.5), 0.1, W(0.3, 0.14, 0.5)),
                             A("r", W(0.02, 0.36, 0.0), 0.1, W(0.3, 0.14, 0.0)),
                             twist=W(0.0, 0.07, 0.5), hip_roll=W(0.0, 0.0, 0.0, 0.035, 0.0),
                             lean=0.05, nod=W(0.0, 0.0, 0.0, 0.025, 0.1), sway=0.0, coat_trail=0.2)),
    "run": (0.56, "stand", P(_RUN_LEGS,
                             A("l", W(0.02, 0.72, 0.5), 0.14, W(1.32, 0.22, 0.75), h="fist"),
                             A("r", W(0.02, 0.72, 0.0), 0.14, W(1.32, 0.22, 0.25), h="fist"),
                             twist=W(0.0, 0.14, 0.5), lean=0.26, neck=0.1, lift=W(10, 0, 0, 12, 0.0),
                             nod=W(0.0, 0.0, 0.0, 0.04, 0.2), sway=0.0, coat_trail=0.85)),
    "run_panic": (0.44, "stand", P(_RUN_LEGS,
                                   A("l", W(0.6, 0.9, 0.3), W(0.95, 0.45, 0.05), W(1.3, 0.55, 0.7), 0.3,
                                     h="splay"),
                                   A("r", W(0.6, 0.9, 0.8), W(0.95, 0.45, 0.55), W(1.3, 0.55, 0.2), 0.3,
                                     h="splay"),
                                   lean=0.14, nod=-0.12, hunch=0.5, lift=W(10, 0, 0, 12, 0.0),
                                   tilt=W(0.0, 0.08, 0.1), sway=0.0, coat_trail=1.0)),
    "scream_run": (0.46, "stand", P(_RUN_LEGS,
                                    A("l", W(0.2, 0.2, 0.0), W(2.2, 0.3, 0.0, 0.12, 0.1), W(1.0, 0.3, 0.3),
                                      0.35, h="splay"),
                                    A("r", W(0.2, 0.2, 0.5), W(2.2, 0.3, 0.5, 0.12, 0.6), W(1.0, 0.3, 0.8),
                                      0.35, h="splay"),
                                    lean=0.02, nod=-0.18, lift=W(10, 0, 0, 12, 0.0), tilt=W(0, 0.06, 0.2),
                                    sway=0.0, coat_trail=1.0)),
    "tiptoe": (1.4, "stand", P(L("l", W(0.42, 0.62, 0.0), 0.08, W(0.45, 1.25, 0.17, r=1), -0.55),
                               L("r", W(0.42, 0.62, 0.5), 0.08, W(0.45, 1.25, 0.67, r=1), -0.55),
                               A("l", W(0.5, 0.15, 0.5), 0.35, 1.55, -0.35, -1.25, h="relaxed"),
                               A("r", W(0.5, 0.15, 0.0), 0.35, 1.55, -0.35, -1.25, h="relaxed"),
                               lean=0.24, hunch=0.7, neck=0.32, nod=-0.06, lift=W(4, 0, 0, 7, 0.1),
                               twist=W(0, 0.06, 0.5), sway=0.0)),
    "crawl": (1.2, "stand", P(L("l", W(0.05, 0.3, 0.0), 0.08, W(1.55, 0.22, 0.25), -0.6),
                              L("r", W(0.05, 0.3, 0.5), 0.08, W(1.55, 0.22, 0.75), -0.6),
                              A("l", W(0.02, 0.3, 0.5), 0.12, W(0.12, 0.25, 0.75, r=1), h="flat",
                                wa=0.1, wabs=0.5),
                              A("r", W(0.02, 0.3, 0.0), 0.12, W(0.12, 0.25, 0.25, r=1), h="flat",
                                wa=0.1, wabs=0.5),
                              lean=1.3, chest=0.12, neck=-0.85, nod=-0.25, plant_hands=1.0, sway=0.0,
                              twist=W(0, 0.05, 0.0), posture=0.0)),
    "stumble": (1.6, "stand", P(L("l", W(0.0, 0.3, 0.0, 0.08), 0.1, W(0.15, 0.5, 0.22, r=1), 0.05),
                                L("r", W(0.0, 0.26, 0.5, 0.08), 0.1, W(0.15, 0.5, 0.72, r=1), 0.05),
                                A("l", W(0.0, 0.2, 0.5), W(0.18, 0.06, 0.2), 0.15, h="relaxed"),
                                A("r", W(0.0, 0.2, 0.0), W(0.18, 0.06, 0.7), 0.15, h="relaxed"),
                                side=W(0, 0.08, 0.0), rot=W(0, 0.045, 0.1), lean=0.14, hunch=0.7,
                                nod=W(0.1, 0.06, 0.2), tilt=W(0.0, 0.12, 0.3), sway=0.0)),
    # ------------------------------------------------------------ gestures
    "bang_door": (0.5, "stand", P(A("r", W(1.55, 0.1, 0.0), 0.15, W(0.55, 0.5, 0.0), 0.0, -0.2, h="fist"),
                                  A("l", 1.3, 0.25, 0.7, -0.2, -0.6, h="flat"),
                                  lean=W(0.12, 0.05, 0.0), hunch=0.4, nod=W(0.0, 0.04, 0.05),
                                  **L("l", 0.15, k=0.1), **L("r", -0.12, k=0.05))),
    "wring_hands": (0.8, "stand", P(IK("l", W(0.0, 0.015, 0.0), W(0.53, 0.012, 0.25), 0.14, "relaxed",
                                       w=1.0, wa=-1.2, wabs=0.5),
                                    IK("r", W(0.0, 0.015, 0.5), W(0.53, 0.012, 0.75), 0.14, "relaxed",
                                       w=1.0, wa=-1.2, wabs=0.5),
                                    {"al_w": W(0, 0.5, 0.0), "ar_w": W(0, 0.5, 0.5)},
                                    hunch=0.85, nod=0.06, tilt=W(0, 0.04, 0.0))),
    "shake_arms": (0.25, "stand", P(A("l", 0.75, W(0.62, 0.18, 0.25), W(0.75, 0.35, 0.0), 0.2, h="splay"),
                                    A("r", 0.75, W(0.62, 0.18, 0.75), W(0.75, 0.35, 0.5), 0.2, h="splay"),
                                    hunch=0.8, tilt=W(0, 0.035, 0.0), nod=W(0, 0.02, 0.3), sway=0.0)),
    "tap_foot": (0.5, "arms_crossed", P(L("r", 0.18, 0.12, 0.06, W(0.22, 0.22, 0.0, r=1)),
                                        nod=W(0, 0.012, 0.0))),
    "roll_hand": (0.7, "stand", P(IK("r", W(0.17, 0.03, 0.0), W(0.56, 0.03, 0.25), 0.18, "open", tf=-1.0,
                                     wa=W(-0.4, 0.8, 0.1), wabs=0.8),
                                  A("l", 0.05, 0.1, 0.2), tilt=0.06)),
    "tug": (1.2, "stand", P(IK("l", 0.05, 0.47, W(0.36, 0.03, 0.0), "grip", wa=0.0, wabs=0.6),
                            IK("r", 0.05, 0.5, W(0.36, 0.03, 0.0), "grip", wa=0.0, wabs=0.6),
                            L("l", 0.55, 0.06, 0.12, 0.25), L("r", -0.1, 0.08, 0.62, 0.0),
                            lean=W(-0.36, 0.08, 0.0), dx=W(0, 10, 0.0), hunch=0.4, nod=0.1,
                            tilt=W(0, 0.05, 0.25), hold=2.0, sway=0.0)),
    "struggle_hold": (0.9, "stand", P(IK("l", W(0.0, 0.02, 0.0), W(0.52, 0.03, 0.25), 0.17, "claw",
                                         layer="front", wa=0.4, wabs=0.5),
                                      IK("r", W(0.0, 0.02, 0.5), W(0.58, 0.03, 0.75), 0.17, "claw",
                                         layer="mid", wa=-0.4, wabs=0.5),
                                      L("l", 0.12, 0.16, 0.25), L("r", -0.08, 0.16, 0.3),
                                      side=W(0, 0.08, 0.0), twist=W(0, 0.15, 0.25), lean=W(0.05, 0.06, 0.5),
                                      dx=W(0, 7, 0.0), tilt=W(0, 0.08, 0.1), hold=2.0, sway=0.0)),
    "game": (0.3, "sit_game", P({"al_thumb": W(0, 0.3, 0.0), "ar_thumb": W(0, 0.3, 0.37)},
                                nod=W(-0.16, 0.012, 0.0), lean=W(0.3, 0.01, 0.2))),
    "type": (0.35, "sit_desk", P({"al_fing": 1.0, "ar_fing": 1.0, "al_h": "claw", "ar_h": "claw"},
                                 nod=W(0.05, 0.01, 0.0))),
}

# ---------------------------------------------------------------------------
# Episode 2 poses
# ---------------------------------------------------------------------------
# punches use the l arm: the NEAR arm when turn > 0 (use flip=True to face left)
_PUNCH_WIND = P(A("l", -0.8, 0.18, 2.15, -0.1, 0.2, h="fist", tf=1.0),
                A("r", 0.75, 0.3, 1.5, -0.6, -0.1, h="fist", tf=1.0),
                L("r", 0.34, 0.1, 0.32, -0.02), L("l", -0.26, 0.1, 0.5, 0.3),
                twist=-0.5, lean=-0.12, side=0.05, hunch=0.6, nod=0.12, neck=0.05, sway=0.2)
_PUNCH = P(A("l", 1.52, 0.04, 0.03, -0.04, 0.0, h="fist", tf=1.0),
           A("r", 0.45, 0.3, 1.75, -0.6, -0.2, h="fist", tf=1.0),
           L("r", 0.44, 0.1, 0.42, -0.02), L("l", -0.32, 0.1, 0.12, 0.3),
           twist=0.42, lean=0.26, chest=0.06, side=-0.04, hunch=0.35, nod=0.06, neck=0.1, sway=0.2)
_GUARD = P(A("l", 0.4, 0.22, 1.8, -0.5, -0.2, h="fist", tf=1.0),
           A("r", 0.5, 0.22, 1.7, -0.5, -0.2, h="fist", tf=1.0),
           L("r", 0.3, 0.1, 0.3, -0.02), L("l", -0.26, 0.1, 0.32, 0.3),
           lean=0.06, hunch=0.5, nod=0.06, sway=0.4)
_CRATE_LEGS = P(L("l", 1.78, 0.2, 1.3, -0.46), L("r", 1.72, 0.14, 1.24, -0.46))
_LIE_F = dict(plant=1.0, plant_all=1.0, turn=1.45, rot=math.pi / 2, head_face=1.0, tilt=0.0, nod=0.0,
              neck=-0.6, lean=0.0, chest=-0.12, hunch=0.15, sway=0.0, breath=0.55, posture=0.0, pillow=48.0)
POSES.update({
    "sit_crate": P(_CRATE_LEGS,
                   A("l", 0.3, 0.16, 1.05, -0.5, -0.75, h="relaxed"),
                   A("r", 0.28, 0.16, 1.1, -0.5, -0.8, h="relaxed"), plant=1.0,
                   lean=0.5, chest=0.16, hunch=0.65, neck=0.32, nod=0.34, tilt=0.04, sway=0.4, breath=0.8,
                   ),
    "punch_wind": _PUNCH_WIND,
    "punch": _PUNCH,
    "guard_fists": _GUARD,
    "haul": P(IK("l", 0.035, 0.94, 0.47, "grip", wa=-1.0, wabs=0.45, bend=1.0),
              IK("r", 0.035, 0.96, 0.48, "grip", wa=-1.0, wabs=0.45, bend=1.0),
              L("l", 0.62, 0.16, 0.2, -0.3), L("r", -0.38, 0.12, 0.7, 0.35),
              lean=-0.55, chest=-0.05, hunch=0.9, neck=0.18, nod=0.2, tilt=0.05, side=0.02,
              sway=0.0, posture=0.3),
    "lie_front": P(_LIE_F,
                   A("l", 2.8, 0.3, 0.95, -0.25, 0.3, h="relaxed", layer="mid"),
                   A("r", 2.9, 0.3, 0.75, -0.2, 0.2, h="relaxed", layer="back"),
                   L("l", 0.02, 0.06, 0.1, -1.25), L("r", -0.06, 0.09, 0.22, -1.25)),
    "flop": P(plant=1.0, turn=1.45, rot=0.78, head_face=0.55, lean=0.04, chest=-0.04, hunch=0.3,
              neck=-0.25, nod=-0.1, tilt=0.0, sway=0.0, posture=0.1, pillow=24.0,
              **A("l", 2.0, 0.3, 0.3, -0.1, 0.0, h="open", layer="mid"),
              **A("r", 2.15, 0.3, 0.35, -0.1, 0.0, h="open", layer="back"),
              **L("l", 0.05, 0.06, 0.1, -0.35), **L("r", -0.4, 0.08, 0.35, -0.6)),
    "hand_out": P(A("r", 0.92, 0.16, 0.42, -0.12, -0.12, h="cup", tf=-1.0),
                  A("l", 0.02, 0.06, 0.18), hold=1.0, hold_order=1.0, lean=0.1, nod=0.04, tilt=0.03,
                  hunch=0.3, **L("r", 0.12, k=0.08)),
})


def _keyed_cycle(period, base, keyposes, const=None):
    """Cycle table from static pose tables keyed at phases: [(phase, table), ...]."""
    tabs = [(ph, dict(POSE_DEFAULTS, **tb)) for ph, tb in keyposes]
    out = {}
    for k in tabs[0][1]:
        vals = [(ph, tb[k]) for ph, tb in tabs]
        if isinstance(vals[0][1], str):
            out[k] = vals[0][1]
        elif any(abs(v - vals[0][1]) > 1e-9 for _, v in vals):
            out[k] = K(*vals)
        else:
            out[k] = vals[0][1]
    out.update(const or {})
    return (period, base, out)


CYCLES.update({
    # upright crouch sneak: knees bent, torso upright, arms close (NOT butt-up)
    "sneak": (1.3, "stand", P(L("l", W(0.34, 0.3, 0.0), 0.1, W(0.74, 0.55, 0.22, r=1), W(0.4, 0.3, 0.5)),
                              L("r", W(0.34, 0.3, 0.5), 0.1, W(0.74, 0.55, 0.72, r=1), W(0.4, 0.3, 0.0)),
                              A("l", W(0.12, 0.07, 0.5), 0.08, 1.35, -0.45, -0.55, h="relaxed"),
                              A("r", W(0.12, 0.07, 0.0), 0.08, 1.35, -0.45, -0.55, h="relaxed"),
                              lean=0.1, chest=0.0, hunch=0.6, neck=0.12, nod=-0.04, lift=W(0, 0, 0, 4, 0.1),
                              twist=W(0, 0.05, 0.5), sway=0.0)),
    # one-shot style punch: guard -> wind-up (0.40) -> strike lands at phase 0.52 -> recover
    "punch_cycle": _keyed_cycle(1.2, "stand", [(0.0, _GUARD), (0.4, _PUNCH_WIND), (0.52, _PUNCH),
                                               (0.75, _PUNCH)], {"sway": 0.0}),
    # straining on the lever: small trembles on top of "haul"
    "haul_strain": (0.36, "haul", P(lean=W(-0.3, 0.02, 0.0), tilt=W(0.05, 0.025, 0.25), dx=W(0, 2.0, 0.5),
                                    hunch=W(0.85, 0.05, 0.1), nod=W(0.12, 0.02, 0.4))),
    # small bent-elbow wave at chest height (palm out)
    "wave_small": (0.7, "stand", P(A("r", 0.3, 0.52, 1.55, W(-0.5, 0.28, 0.0), W(0.0, 0.25, 0.1),
                                     h="open", tf=-1.0),
                                   A("l", 0.02, 0.06, 0.18), tilt=W(0.05, 0.02, 0.0), hunch=0.3,
                                   side=-0.02)),
    # thumbing a phone held in both hands, seated (chair / bed edge height SEAT_H)
    "phone_thumb": (0.42, "sit_chair", P(IK("l", 0.06, "seat+0.2", 0.22, "grip", layer="front", wa=-1.3,
                                            wabs=0.7),
                                         IK("r", 0.06, "seat+0.2", 0.22, "grip", layer="front", wa=-1.3,
                                            wabs=0.7),
                                         {"al_thumb": W(0, 0.25, 0.0), "ar_thumb": W(0, 0.25, 0.43)},
                                         lean=0.28, chest=0.08, hunch=0.6, neck=0.42, nod=0.18, hold=2.0)),
    # lying face-down, near hand out by the face thumbing a phone (hold "l" = near hand)
    "phone_thumb_lie": (0.42, "lie_front", P(A("l", 2.85, 0.35, 1.25, -0.3, 0.0, h="grip", layer="mid"),
                                             {"al_thumb": W(0, 0.3, 0.0)}, hold=1.0, hold_hand=-1.0)),
    # confident stride (hood over the eyes): chin up, chest out, loose bigger arm swing
    "walk_eyes_closed": (1.05, "stand", P(L("l", W(0.0, 0.47, 0.0), 0.04, W(0.06, 0.82, 0.22, r=1),
                                            W(0.02, 0.28, 0.02)),
                                          L("r", W(0.0, 0.47, 0.5), 0.04, W(0.06, 0.82, 0.72, r=1),
                                            W(0.02, 0.28, 0.52)),
                                          A("l", W(0.04, 0.44, 0.5), 0.12, W(0.32, 0.16, 0.5)),
                                          A("r", W(0.04, 0.44, 0.0), 0.12, W(0.32, 0.16, 0.0)),
                                          twist=W(0.0, 0.1, 0.5), hip_roll=W(0.0, 0.0, 0.0, 0.04, 0.0),
                                          lean=0.0, chest=-0.07, nod=W(-0.14, 0.0, 0.0, 0.03, 0.1),
                                          neck=-0.05, posture=0.35, sway=0.0, coat_trail=0.2)),
})

# Per-character pose tweaks: (who, pose) -> overrides merged on top.
POSE_WHO = {
    ("tired", "hands_pockets"): P(A("l", 0.32, 0.2, 0.95, -1.05, hide=1.0),
                                  A("r", 0.32, 0.2, 0.95, -1.05, hide=1.0), hunch=0.6),
    ("boss", "stand"): P(_HANDS_BACK),
    # Episode 2: the Boss walks with her hands still clasped behind her back (no arm swing);
    # in other cycles the clasp no longer leaks in (it made hands flip behind her back)
    **{("boss", c): P(_HANDS_BACK) for c in ("walk", "walk_eyes_closed", "sneak", "tiptoe")},
    **{("boss", c): {"al_eo": 0.0, "ar_eo": 0.0, "al_layer": "", "ar_layer": ""}
       for c in ("run", "run_panic", "scream_run", "crawl", "stumble", "shake_arms")},
    ("guard", "stand"): P(A("l", 0.05, 0.16, 0.25), A("r", 0.05, 0.16, 0.25)),
}

# Static poses that are secretly animated (waves) use this period (s).
STATIC_PERIOD = 0.5

# Poses whose hands hold a prop: "hold" 1 = right hand, 2 = both hands (the
# callback gets side "both" and the midpoint between the hands).


# ============================================================================
# 6. SOLVER
# ============================================================================
_HAND_KEYS = ("al_h", "ar_h")
_STR_KEYS = ("al_layer", "ar_layer")


def _eval(v, phase):
    if isinstance(v, tuple) and v:
        if v[0] == "~":
            return _wave(phase, *v[1:])
        if v[0] == "k":
            return _keyval(v[1], phase)
    return v


def _overlay(d, table, phase):
    for k, v in table.items():
        if k in ("base", "period"):
            continue
        d[k] = _eval(v, phase)


def _ik_layer_reset(d, table):
    """An arm the table drives by IK forgets a layer inherited from its base (e.g. the
    Boss's hands-behind-back stand leaking 'back' into wring_hands); Episode 2 fix."""
    for s_ in "lr":
        if f"a{s_}_ik" in table and f"a{s_}_layer" not in table:
            d[f"a{s_}_layer"] = ""


def _pose_raw(spec, who, pt):
    """Resolve one pose spec (name / dict) into a flat dict (hand names kept)."""
    if isinstance(spec, dict):
        d = _pose_raw(spec.get("base", "stand"), who, pt)
        _ik_layer_reset(d, spec)
        # waves in a dict use its own "period", else the base cycle's period (Episode 2),
        # else STATIC_PERIOD
        per = spec.get("period", d.get("_cycle", STATIC_PERIOD))
        _overlay(d, spec, (pt / per) % 1.0)
        if "period" in spec and "_cycle" not in d:
            d["_cycle"] = spec["period"]
        return d
    name = spec
    if name in CYCLES:
        period, base, table = CYCLES[name]
        d = _pose_raw(base, who, pt)
        _ik_layer_reset(d, table)
        _overlay(d, table, (pt / period) % 1.0)
        d["_cycle"] = period
    else:
        if name not in POSES:
            raise KeyError(f"human: unknown pose {name!r}")
        d = dict(POSE_DEFAULTS)
        tab = POSES[name]
        _overlay(d, tab, (pt / tab.get("period", STATIC_PERIOD)) % 1.0)
    tw = POSE_WHO.get((who, name))
    if tw:
        _overlay(d, tw, 0.0)
    return d


def _numeric(d, C, who):
    """Hand names -> vectors, named heights -> numbers."""
    out = dict(d)
    for k in _HAND_KEYS:
        v = out[k]
        out[k] = list(_HAND_VEC[v]) if isinstance(v, str) else list(v)
    H = C["height"]
    leglen = C["thigh"] + C["shin"] + C["foot_h"]
    for k in ("hip_h", "al_ty", "ar_ty"):
        v = out[k]
        if isinstance(v, str):
            base, _, add = v.partition("+")
            if base == "seat":
                val = SEAT_H[who] + C["leg_r"][0] * 0.8
            elif base == "desk":
                val = DESK_H[who]
            elif base == "sill":
                val = SILL_H[who]
            else:
                val = 0.0
            if k == "hip_h":
                out[k] = val / leglen + (float(add) if add else 0.0)
            else:
                out[k] = val / H + (float(add) if add else 0.0)
    return out


def resolve_pose(pose, who, pt):
    """pose (name | dict | (a, b, k)) -> numeric joint dict."""
    C = CHARS[who]
    if isinstance(pose, (tuple, list)) and len(pose) == 3 and not isinstance(pose[0], (int, float)):
        a = resolve_pose(pose[0], who, pt)
        b = resolve_pose(pose[1], who, pt)
        k = clamp(float(pose[2]))
        out = {}
        for key, va in a.items():
            vb = b.get(key, va)
            if isinstance(va, list):
                out[key] = [x + (y - x) * k for x, y in zip(va, vb)]
            elif isinstance(va, str) or isinstance(vb, str):
                out[key] = vb if k >= 0.5 else va
            else:
                out[key] = va + (vb - va) * k
        for key, vb in b.items():
            if key not in out:
                out[key] = vb
        return out
    return _numeric(_pose_raw(pose, who, pt), C, who)


def _up(p, r):
    return (math.sin(r), -math.cos(r) * math.cos(p), math.cos(r) * math.sin(p))


def _dir(p, o, sgn):
    co = math.cos(o)
    return (sgn * math.sin(o), co * math.cos(p), co * math.sin(p))


def _add(a, b, k=1.0):
    return (a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k)


class _Proj:
    """Yaw projection + whole-body screen roll + translation (rig-local 2D)."""
    __slots__ = ("c", "s", "rc", "rs", "tx", "ty")

    def __init__(self, yaw, rot, tx=0.0, ty=0.0):
        self.c, self.s = math.cos(yaw), math.sin(yaw)
        self.rc, self.rs = math.cos(rot), math.sin(rot)
        self.tx, self.ty = tx, ty

    def __call__(self, p):
        X = p[0] * self.c + p[2] * self.s
        Z = -p[0] * self.s + p[2] * self.c
        Y = p[1]
        return (X * self.rc - Y * self.rs + self.tx, X * self.rs + Y * self.rc + self.ty, Z)


def _lerp3(a, b, k):
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k)


def _ik3(S, T, L1, L2, pole):
    dx, dy, dz = T[0] - S[0], T[1] - S[1], T[2] - S[2]
    d0 = math.sqrt(dx * dx + dy * dy + dz * dz)
    if d0 < 1e-6:
        dx, dy, dz, d0 = 0.0, 1.0, 0.0, 1.0
    u = (dx / d0, dy / d0, dz / d0)
    d = clamp(d0, abs(L1 - L2) + 1.0, L1 + L2 - 0.5)
    ca = clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1.0, 1.0)
    sa = math.sqrt(max(0.0, 1 - ca * ca))
    pd = pole[0] * u[0] + pole[1] * u[1] + pole[2] * u[2]
    q = (pole[0] - u[0] * pd, pole[1] - u[1] * pd, pole[2] - u[2] * pd)
    ql = math.sqrt(q[0] ** 2 + q[1] ** 2 + q[2] ** 2)
    if ql < 1e-6:
        q, ql = (1.0, 0.0, 0.0), 1.0
    q = (q[0] / ql, q[1] / ql, q[2] / ql)
    E = (S[0] + L1 * (u[0] * ca + q[0] * sa), S[1] + L1 * (u[1] * ca + q[1] * sa),
         S[2] + L1 * (u[2] * ca + q[2] * sa))
    W = (S[0] + u[0] * d, S[1] + u[1] * d, S[2] + u[2] * d)
    return E, W


def _ang_lerp(a, b, k):
    d = (b - a + math.pi) % TAU - math.pi
    return a + d * k


def _leg_low(C, Q, s_, sgn, p):
    """Lowest foot/knee point (body y, down) of one leg for thigh pitch p, hip at the pelvis."""
    k, o = Q[f"l{s_}_k"], Q[f"l{s_}_o"]
    kn = _dir(p, o, sgn)
    kn_y = kn[1] * C["thigh"]
    q = p - k
    an_y = kn_y + _dir(q, o + Q[f"l{s_}_ko"], sgn)[1] * C["shin"]
    fp = q + Q[f"l{s_}_a"]
    so_y = an_y + math.cos(fp) * C["foot_h"]
    toe_y = so_y - math.sin(fp) * C["foot_len"] * 0.72
    heel_y = so_y + math.sin(fp) * C["foot_len"] * 0.28
    return max(so_y, toe_y, heel_y, kn_y + C["leg_r"][1])


def _floor_legs(C, Q, phi):
    """Side-on floor sits (plant_butt): raise the legs so heels and butt share the floor line.

    In front views the feet stay lower than the butt (the floor recedes toward camera, the
    Episode 1 look); from |turn| ~0.3 up to ~0.8 the legs are progressively laid on the floor."""
    pb = Q["plant_butt"]
    if pb <= 0.01:
        return
    fl = pb * smoothstep((abs(math.sin(phi)) - 0.2) / 0.42)
    if fl <= 0.01:
        return
    target = C["leg_r"][0] * 0.95
    for s_, sgn in (("l", -1), ("r", 1)):
        p0 = Q[f"l{s_}_p"]
        if _leg_low(C, Q, s_, sgn, p0) <= target:
            continue
        lo, hi = p0, p0 + 1.3
        if _leg_low(C, Q, s_, sgn, hi) > target:
            p1 = hi
        else:
            for _ in range(14):
                mid = (lo + hi) * 0.5
                if _leg_low(C, Q, s_, sgn, mid) > target:
                    lo = mid
                else:
                    hi = mid
            p1 = hi
        Q[f"l{s_}_p"] = lerp(p0, p1, fl)


def _solve(C, Q, who, turn, t, fx, headphones, lag_Q=None, reach=None):
    """Skeleton in rig-local 2D (ground origin, y down). Returns dict J.

    reach: {side: (x, y, w, ang|None)} rig-local world-space hand targets (Episode 2)."""
    H = C["height"]
    sp = C["spine"]
    leglen = C["thigh"] + C["shin"] + C["foot_h"]
    tq = clamp(turn + Q["turn"], -1.6, 1.6)
    phi = tq * TURN_RAD
    tw = Q["twist"]
    rot = Q["rot"]
    seed = C["seed"]
    br = Q["breath"] * math.sin(TAU * t / 3.7 + seed)
    lean, chest, side, hunch = Q["lean"], Q["chest"], Q["side"], Q["hunch"]
    _floor_legs(C, Q, phi)

    # ---- spine (body frame, pelvis at origin)
    P0 = (0.0, 0.0, 0.0)
    hem = _add(P0, _up(lean * 0.3, side * 0.3), sp["hem"])
    wst = _add(P0, _up(lean * 0.5, side * 0.5), sp["waist"])
    chs = _add(wst, _up(lean, side), sp["chest"] - sp["waist"])
    shl = _add(chs, _up(lean + chest * 0.6, side), sp["shoulder"] - sp["chest"])
    shl = (shl[0], shl[1] - br * 1.6 - hunch * 8, shl[2] + hunch * 6)
    nck = _add(shl, _up(lean + chest + Q["neck"] * 0.3, side), sp["neck"] - sp["shoulder"] + hunch * 4)
    hpv = _add(nck, _up(lean + chest + Q["neck"], side * 1.2), C["neck_len"] - hunch * 10)
    hpv = (hpv[0], hpv[1], hpv[2] + hunch * 10)

    pr = _Proj(phi, rot)
    pr_w = _Proj(phi + tw * 0.3, rot)
    pr_c = _Proj(phi + tw * 0.65, rot)
    pr_s = _Proj(phi + tw, rot)

    J = {"phi": phi, "turn": tq, "rot": rot}
    # ---- legs
    lowest = -1e9
    legs = {}
    for s_, sgn in (("l", -1), ("r", 1)):
        hip = (sgn * C["hip_w"] * math.cos(Q["hip_roll"]), sgn * C["hip_w"] * math.sin(Q["hip_roll"]) * -1, 0.0)
        p, o, k = Q[f"l{s_}_p"], Q[f"l{s_}_o"], Q[f"l{s_}_k"]
        kn = _add(hip, _dir(p, o, sgn), C["thigh"])
        q = p - k
        an = _add(kn, _dir(q, o + Q[f"l{s_}_ko"], sgn), C["shin"])
        fp = q + Q[f"l{s_}_a"]
        fdir = (sgn * 0.1, -math.sin(fp), math.cos(fp))
        dn = (0.0, math.cos(fp), math.sin(fp))
        sole = _add(an, dn, C["foot_h"])
        toe = _add(sole, fdir, C["foot_len"] * 0.72)
        heel = _add(sole, fdir, -C["foot_len"] * 0.28)
        g = dict(hip=pr(hip), knee=pr(kn), ankle=pr(an), sole=pr(sole), toe=pr(toe), heel=pr(heel),
                 fp=fp)
        legs[s_] = g
        lowest = max(lowest, g["sole"][1], g["toe"][1], g["heel"][1], g["knee"][1] + C["leg_r"][1])
    # seat / rear volume reduction for bent, crouched and seated poses (no butt emphasis)
    pmax = max(Q["ll_p"], Q["lr_p"])
    J["seat_flat"] = max(smoothstep((lean - 0.12) / 0.5), 0.75 * smoothstep((pmax - 0.6) / 0.6))
    for g in legs.values():
        g["sf"] = J["seat_flat"]
    # ---- torso nodes
    nodes = dict(hem=pr(hem), pel=pr(P0), wst=pr_w(wst), chs=pr_c(chs), shl=pr_s(shl), nck=pr_s(nck),
                 hpv=pr_s(hpv))
    sw = C["sw"] * (1 - 0.05 * hunch)
    shj = {}
    for s_, sgn in (("l", -1), ("r", 1)):
        off = _rot(sgn * sw, 0.0, side)
        shj[s_] = pr_s((shl[0] + off[0], shl[1] + off[1] + hunch * 4, shl[2] - hunch * 4))
    # ---- arms (FK)
    arms = {}
    for s_, sgn in (("l", -1), ("r", 1)):
        off = _rot(sgn * sw, 0.0, side)
        S3 = (shl[0] + off[0], shl[1] + off[1] + hunch * 4, shl[2] - hunch * 4)
        p, o, e, eo = Q[f"a{s_}_p"], Q[f"a{s_}_o"], Q[f"a{s_}_e"], Q[f"a{s_}_eo"]
        E3 = _add(S3, _dir(p, o, sgn), C["arm"][0])
        W3 = _add(E3, _dir(p + e, o + eo, sgn), C["arm"][1])
        T3 = _add(W3, _dir(p + e + Q[f"a{s_}_w"], o + eo, sgn), 30.0)
        arms[s_] = dict(S=pr_s(S3), E=pr_s(E3), W=pr_s(W3), T=pr_s(T3), S3=S3, E3=E3, W3=W3)
        if Q["plant_hands"] > 0:
            lowest = max(lowest, arms[s_]["W"][1] + C["hand"] * 0.35)
        if Q["plant_all"] > 0:
            for q in ("S", "E", "W"):
                lowest = max(lowest, arms[s_][q][1] + C["arm_r"][1])
    if Q["plant_butt"] > 0:
        lowest = max(lowest, nodes["pel"][1] + C["leg_r"][0] * 0.95)
    if Q["plant_all"] > 0:
        hc = _rot(0.0, -C["head"]["chin"] * C["head"]["pivot"], rot)
        hp2 = nodes["hpv"]
        cph, sph = abs(math.cos(phi)), abs(math.sin(phi))

        def thick(k):    # projected half-thickness of the torso (profile-aware)
            a_, f_, b_ = C["tw"][k]
            return math.hypot(a_ * 0.9 * cph, max(f_, b_) * 0.95 * sph)
        lowest = max(lowest, hp2[1] + hc[1] + 105 - Q["pillow"], nodes["pel"][1] + thick("hip"),
                     nodes["shl"][1] + thick("shoulder"))

    # ---- ground lock
    lock_dy = -lowest
    pel_dy = -Q["hip_h"] * leglen
    gy = lerp(pel_dy, lock_dy, Q["plant"]) - Q["lift"] + Q["dy"]
    gx = Q["dx"] + Q["sway"] * 2.5 * noise1(t * 0.33, seed)

    def mv(p):
        return (p[0] + gx, p[1] + gy, p[2])

    for g in legs.values():
        for k in ("hip", "knee", "ankle", "sole", "toe", "heel"):
            g[k] = mv(g[k])
    for k in list(nodes):
        nodes[k] = mv(nodes[k])
    for s_ in "lr":
        shj[s_] = mv(shj[s_])
        for k in ("S", "E", "W", "T"):
            arms[s_][k] = mv(arms[s_][k])
    J["legs"], J["nodes"], J["shj"], J["arms"] = legs, nodes, shj, arms
    J["pel_y"] = gy

    # ---- head transform (needed for head-relative IK targets)
    fdir = 1.0 if tq >= -0.001 else -1.0
    J["fdir"] = fdir
    hd = C["head"]
    psi = clamp(tq + tw / TURN_RAD + Q["head_yaw"] + fx["head_turn"], -1.6, 1.6)
    if Q["head_face"] > 0:      # face the camera regardless of the body turn (lie_front, flop)
        psi = lerp(psi, clamp(fx["head_turn"], -1.6, 1.6), clamp(Q["head_face"]))
    psi *= HEAD_TURN_RAD
    tilt = (Q["tilt"] + fx["head_tilt"] + rot + side * 0.5
            + (lean + chest + Q["neck"]) * math.sin(phi) * 0.35
            + Q["sway"] * 0.022 * noise1(t * 0.27, seed + 3))
    nod = Q["nod"] + fx["head_nod"] + (lean + chest + Q["neck"]) * 0.1
    piv = nodes["hpv"]
    up_off = hd["chin"] * hd["pivot"]
    hcx, hcy = _rot(0.0, -up_off, tilt)
    J["head"] = dict(pivot=(piv[0], piv[1]), cx=piv[0] + hcx, cy=piv[1] + hcy, tilt=tilt, psi=psi,
                     nod=nod, z=piv[2])

    # ---- arm IK (3D: 2D targets are lifted into body space at a chosen depth)
    phs = phi + tw
    cps, sps = math.cos(phs), math.sin(phs)
    rc, rs = math.cos(rot), math.sin(rot)

    def lift(X, Y, Z):
        x0, y0 = X - gx, Y - gy
        X0, Y0 = x0 * rc + y0 * rs, -x0 * rs + y0 * rc
        return (X0 * cps - Z * sps, Y0, X0 * sps + Z * cps)

    def proj(p3):
        return mv(pr_s(p3))

    order = ("l", "r") if Q["ar_grab"] >= Q["al_grab"] else ("r", "l")
    f0 = hd["levels"][4][2]
    for s_ in order:
        sgn = -1 if s_ == "l" else 1
        a = arms[s_]
        S3, E3, W3 = a["S3"], a["E3"], a["W3"]
        Wr, T = a["W"], a["T"]
        fk_ang = math.atan2(T[1] - Wr[1], T[0] - Wr[0]) if math.hypot(T[0] - Wr[0], T[1] - Wr[1]) > 4 \
            else math.pi / 2
        ik = Q[f"a{s_}_ik"]
        ang = fk_ang
        if ik > 0.001:
            x3, z3 = sgn * Q[f"a{s_}_tx"] * H, Q[f"a{s_}_tz"] * H
            X = nodes["pel"][0] + x3 * cps + z3 * sps
            Y = -Q[f"a{s_}_ty"] * H
            Z = -x3 * sps + z3 * cps
            th = Q[f"a{s_}_th"]
            if th > 0:
                hh = J["head"]
                ox = sgn * Q[f"a{s_}_hx"] * math.cos(psi) + f0 * math.sin(psi) * 0.6
                rx, ry = _rot(ox, Q[f"a{s_}_hy"], hh["tilt"])
                X, Y = lerp(X, hh["cx"] + rx, th), lerp(Y, hh["cy"] + ry, th)
                Z = lerp(Z, hh["z"] + f0 * math.cos(psi) + Q[f"a{s_}_hz"], th)
            if Q[f"a{s_}_cup"] > 0:
                cups = _cup_positions(C, J, headphones)
                k = Q[f"a{s_}_cup"]
                X, Y = lerp(X, cups[s_][0], k), lerp(Y, cups[s_][1], k)
                Z = lerp(Z, J["head"]["z"] + 10, k)
            T3 = lift(X, Y, Z)
            if Q[f"a{s_}_grab"] > 0:
                o_ = arms["r" if s_ == "l" else "l"]
                m = _lerp3(o_["E3f"], o_["W3f"], 0.6)
                T3 = _lerp3(T3, (m[0], m[1], m[2] + 16), Q[f"a{s_}_grab"])
            bend = Q[f"a{s_}_bend"]
            pole = (sgn * 0.6 * bend, 0.75, -0.5 + 0.4 * max(0.0, -bend))
            Ei, Wi = _ik3(S3, T3, C["arm"][0], C["arm"][1], pole)
            E3 = _lerp3(E3, Ei, ik)
            W3 = _lerp3(W3, Wi, ik)
        rc_ = reach.get(s_) if reach else None
        if rc_ is not None and rc_[2] > 0.001:
            E3, W3 = _reach_ik(C, Q, s_, sgn, S3, E3, W3, rc_, proj, lift)
        Ep, Wp = proj(E3), proj(W3)
        if ik > 0.001:
            dxp, dyp = Wp[0] - Ep[0], Wp[1] - Ep[1]
            if math.hypot(dxp, dyp) > C["arm"][1] * 0.25:
                ik_ang = math.atan2(dyp, dxp) + Q[f"a{s_}_w"]
                ang = _ang_lerp(ang, ik_ang, ik)
        wabs = Q[f"a{s_}_wabs"]
        if wabs > 0:
            wa = Q[f"a{s_}_wa"]
            abs_ang = wa if fdir > 0 else math.pi - wa
            ang = _ang_lerp(ang, abs_ang, wabs)
        if rc_ is not None and rc_[2] > 0.001:
            if rc_[3] is not None:
                r_ang = rc_[3]
            else:
                r_ang = math.atan2(Wp[1] - Ep[1], Wp[0] - Ep[0])
            ang = _ang_lerp(ang, r_ang, rc_[2])
        a["E3f"], a["W3f"] = E3, W3
        a["E2"], a["W2"], a["ang"], a["zE"], a["zW"] = (Ep[0], Ep[1]), (Wp[0], Wp[1]), ang, Ep[2], Wp[2]
    J["Q"] = Q
    J["lag"] = lag_Q
    return J


def _reach_ik(C, Q, s_, sgn, S3, E3, W3, rc, proj, lift):
    """World-space reach: put the hand's GRIP point on the rig-local 2D target (x, y).

    The depth is kept near the pose's own hand depth (clamped so the arm can reach), the
    target is clamped to the arm length, elbows bend naturally via the pose's `bend` pole."""
    tx, ty, w, rang = rc
    L1, L2 = C["arm"]
    Lmax = (L1 + L2) * 0.985
    Sp = proj(S3)
    Wp0 = proj(W3)
    hv = Q[f"a{s_}_h"]
    hs = C["hand"]
    ys = (-1.0 if s_ == "l" else 1.0) * (1.0 if Q[f"a{s_}_tf"] >= 0 else -1.0)
    gx_, gy_ = hv[2] * hv[0] * hs, ys * hv[3] * hs      # grip offset in the hand frame
    bend = Q[f"a{s_}_bend"]
    pole = (sgn * 0.6 * bend, 0.75, -0.5 + 0.4 * max(0.0, -bend))
    dx, dy = tx - Sp[0], ty - Sp[1]
    a0 = rang if rang is not None else math.atan2(dy, dx)
    wx = tx - (math.cos(a0) * gx_ - math.sin(a0) * gy_)
    wy = ty - (math.sin(a0) * gx_ + math.cos(a0) * gy_)
    Ei = Wi = None
    for _ in range(2):
        ddx, ddy = wx - Sp[0], wy - Sp[1]
        dd = math.hypot(ddx, ddy)
        if dd > Lmax:
            wx, wy = Sp[0] + ddx * Lmax / dd, Sp[1] + ddy * Lmax / dd
            zt = Sp[2]
        else:
            rem = math.sqrt(Lmax * Lmax - dd * dd)
            zt = Sp[2] + clamp(Wp0[2] - Sp[2], -0.7 * rem, 0.7 * rem)
        Ei, Wi = _ik3(S3, lift(wx, wy, zt), L1, L2, pole)
        if rang is not None:
            break
        Ep_, Wp_ = proj(Ei), proj(Wi)
        a1 = math.atan2(Wp_[1] - Ep_[1], Wp_[0] - Ep_[0])
        wx = tx - (math.cos(a1) * gx_ - math.sin(a1) * gy_)
        wy = ty - (math.sin(a1) * gx_ + math.cos(a1) * gy_)
    return _lerp3(E3, Ei, w), _lerp3(W3, Wi, w)


def _cup_positions(C, J, hp):
    """Screen positions of the headphone cups for state hp (0 neck .. 1 on)."""
    hh = J["head"]
    hd = C["head"]
    a = hd["levels"][4][1]
    k = smoothstep(hp)
    psi = hh["psi"]
    out = {}
    nk = J["nodes"]["nck"]
    for s_, sgn in (("l", -1), ("r", 1)):
        ex, ey = _rot(sgn * (a + 6) * math.cos(psi) - math.sin(psi) * 10, (hd["ear_y"][0] + hd["ear_y"][1]) / 2,
                      hh["tilt"])
        on = (hh["cx"] + ex, hh["cy"] + ey)
        neck = (nk[0] + sgn * (C["neck_r"] + 30) * math.cos(J["phi"]), nk[1] + 16)
        mid = _lerp2(neck, on, k)
        # arc outward while lifting
        bulge = math.sin(k * math.pi) * 34
        out[s_] = (mid[0] + sgn * bulge, mid[1])
    return out


# ============================================================================
# 7a. DRAWING: hands, feet, legs, arms
# ============================================================================
_FBASE = ((0.93, 0.31, 0.31), (1.0, 0.1, 0.32), (0.97, -0.11, 0.3), (0.88, -0.3, 0.27))
_PALM = ((0.0, -0.27), (0.38, -0.42), (0.84, -0.44), (1.0, -0.26), (1.03, 0.1), (0.92, 0.4),
         (0.5, 0.45), (0.04, 0.3))
_TW = 0.34


def _finger_pts(hv, i, palm, phase, fing):
    sp, ln, b1, b2 = hv[4 + i * 4: 8 + i * 4]
    if fing:
        w = math.sin(TAU * (phase * 2.0 + i * 0.27))
        b1 += fing * 0.32 * max(0.0, w)
        b2 += fing * 0.2 * max(0.0, w)
    bx, by, fw = _FBASE[i]
    bx *= palm
    j0 = (bx - 0.16, by * 0.96)
    j1 = (bx + math.cos(sp) * ln * 0.5, by + math.sin(sp) * ln * 0.5)
    a2 = sp + b1
    j2 = (j1[0] + math.cos(a2) * ln * 0.3, j1[1] + math.sin(a2) * ln * 0.3)
    a3 = a2 + b2
    tip = (j2[0] + math.cos(a3) * ln * 0.2, j2[1] + math.sin(a3) * ln * 0.2)
    return [j0, j1, j2, tip], fw


def _thumb_pts(hv, palm, thumb):
    ta, tl, tb = hv[20] + thumb, hv[21], hv[22]
    b0 = (0.16 * palm, 0.28)
    t1 = (b0[0] + math.cos(ta) * tl * 0.52, b0[1] + math.sin(ta) * tl * 0.52)
    tb_a = ta - tb if ta > 0.9 else ta + tb * 0.6
    t2 = (t1[0] + math.cos(tb_a) * tl * 0.48, t1[1] + math.sin(tb_a) * tl * 0.48)
    return [b0, t1, t2]


def _draw_hand(ctx, skin, ink, W, ang, hv, ysign, hs, inkw, phase=0.0, fing=0.0, thumb=0.0,
               palm_view=False):
    """Draw one cartoon hand. W = wrist (2D), ang = pointing angle. Returns hold point."""
    ca, sa = math.cos(ang), math.sin(ang)
    px, py = -sa * ysign, ca * ysign            # +y (thumb side) in screen

    def M(x, y):
        return (W[0] + (ca * x + px * y) * hs, W[1] + (sa * x + py * y) * hs)

    palm = hv[0]
    cup = hv[1]
    ctx.set_line_cap(1)
    ctx.set_line_join(1)
    pal = [M(x * palm, y * (1 - 0.12 * cup)) for x, y in _PALM]
    fingers = [_finger_pts(hv, i, palm, phase, fing) for i in range(4)]
    fsc = [[M(*q) for q in pts] for pts, fw in fingers]
    th = [M(*q) for q in _thumb_pts(hv, palm, thumb)]
    ink2 = inkw * 2

    def poly_(pts):
        ctx.move_to(*pts[0])
        for q in pts[1:]:
            ctx.line_to(*q)
    # pass 1: silhouette in ink
    _set(ctx, ink)
    _smooth(ctx, pal, True, 0.6)
    ctx.set_line_width(ink2)
    ctx.stroke_preserve()
    ctx.fill()
    for (pts, fw), sc in zip(fingers, fsc):
        poly_(sc)
        ctx.set_line_width(fw * hs + ink2)
        ctx.stroke()
    poly_(th)
    ctx.set_line_width(_TW * hs + ink2)
    ctx.stroke()
    # pass 2: skin
    _set(ctx, skin)
    _smooth(ctx, pal, True, 0.6)
    ctx.fill()
    for (pts, fw), sc in zip(fingers, fsc):
        poly_(sc)
        ctx.set_line_width(fw * hs)
        ctx.stroke()
    # pass 3: separation lines where neighbouring fingers touch
    _set(ctx, ink)
    ctx.set_line_width(max(1.0, inkw * 0.5))
    for i in range(3):
        a, b = fingers[i][0], fingers[i + 1][0]
        lim = (fingers[i][1] + fingers[i + 1][1]) * 0.5 * 1.02
        mids = []
        ba = (hv[6 + i * 4] + hv[10 + i * 4]) * 0.5
        bb = ba + (hv[7 + i * 4] + hv[11 + i * 4]) * 0.5
        for k in (0.12, 0.35, 0.6, 0.82, 1.0):
            if (k > 0.4 and ba > 0.9) or (k > 0.7 and bb > 1.1):
                break
            pa, pb = _along(a, k), _along(b, k)
            if math.hypot(pa[0] - pb[0], pa[1] - pb[1]) > lim:
                break
            mids.append(M((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2))
        if len(mids) >= 2:
            poly_(mids)
            ctx.stroke()
    if palm_view:
        ctx.move_to(*M(0.25 * palm, 0.26))
        _qcurve(ctx, M(0.25 * palm, 0.26), M(0.5 * palm, 0.02), M(0.8 * palm, -0.14))
        _set(ctx, alpha_ink(ink, 0.5))
        ctx.set_line_width(inkw * 0.5)
        ctx.stroke()
    # pass 4: thumb over the palm with a lighter inner outline (root blended into the palm)
    t0 = _lerp2(th[0], th[1], 0.4)
    tp = [t0, th[1], th[2]]
    poly_(tp)
    _set(ctx, ink)
    ctx.set_line_width(_TW * hs + inkw * 1.1)
    ctx.stroke()
    poly_(tp)
    _set(ctx, skin)
    ctx.set_line_width(_TW * hs)
    ctx.stroke()
    circle(ctx, t0[0], t0[1], _TW * hs * 0.5 + inkw * 0.6 + 0.6)
    ctx.fill()
    return M(hv[2] * palm, hv[3])


def _along(pts, k):
    """Point at fraction k (by segment count) along a polyline."""
    n = len(pts) - 1
    f = k * n
    i = min(int(f), n - 1)
    u = f - i
    return (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * u, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * u)


def alpha_ink(c, a):
    c = hexc(c)
    return (c[0], c[1], c[2], c[3] * a)


def _draw_shoe(ctx, C, col, g, inkw):
    style = C["_shoe"]
    r = C["foot_r"]
    an, so, toe, heel = g["ankle"], g["sole"], g["toe"], g["heel"]
    ux, uy = _norm(an[0] - so[0], an[1] - so[1])
    hc = (heel[0] + ux * r * 0.95, heel[1] + uy * r * 0.95)
    tc = (toe[0] + ux * r * 0.8, toe[1] + uy * r * 0.8)
    ln = math.hypot(tc[0] - hc[0], tc[1] - hc[1])
    front = 1.0 - min(1.0, ln / (C["foot_len"] * 0.75))
    rt = r * (0.62 if style == "heel" else 0.9)
    fw = {"slipper": 0.62, "boot": 0.42, "heel": 0.12}.get(style, 0.3)

    def build(d):
        _capsule(ctx, hc[0], hc[1], r + d, tc[0], tc[1], rt + d)
        if front > 0.05:
            ellipse(ctx, tc[0], tc[1] + r * 0.05, r * (1.0 + fw * front) + d, r * 0.94 + d)
        if style == "slipper":
            for i in range(5):
                q = _lerp2(hc, tc, i / 4.0)
                circle(ctx, q[0] - ux * r * 0.55, q[1] - uy * r * 0.55, r * 0.5 + d)
        if style == "boot":
            _capsule(ctx, an[0], an[1] - 4, r * 0.95 + d, hc[0], hc[1], r + d)
    _ink_fill(ctx, build, col["shoe"], inkw)
    # sole strip / details
    sole_c = {"sneaker": "#f2efe8", "flat": col["shoe_dk"], "slipper": _lt(col["shoe"], 0.35)}.get(
        style, col["shoe_dk"])
    a0 = (heel[0] + ux * 3, heel[1] + uy * 3)
    a1 = (toe[0] + ux * 3, toe[1] + uy * 3)
    ctx.move_to(*a0)
    ctx.line_to(*a1)
    _set(ctx, sole_c)
    ctx.set_line_width(r * (0.42 if style in ("boot", "sneaker") else 0.3))
    ctx.stroke()
    if style == "heel":
        # little heel block under the heel
        hb = (heel[0] + ux * 2, heel[1])
        ctx.move_to(hb[0] - 4, hb[1] - r * 0.6)
        ctx.line_to(hb[0] - 3, hb[1] + 2)
        ctx.line_to(hb[0] + 5, hb[1] + 2)
        ctx.line_to(hb[0] + 6, hb[1] - r * 0.6)
        _fs(ctx, col["shoe_dk"], inkw * 0.8)


def _leg_end(g, rr):
    kn, an = g["knee"], g["ankle"]
    dx, dy = _norm(an[0] - kn[0], an[1] - kn[1])
    return (an[0] + dx * rr[2] * 0.1, an[1] + dy * rr[2] * 0.1), (dx, dy)


def _leg_path(ctx, C, g, rr, k0=0.0, d=0.0):
    e, (dx, dy) = _leg_end(g, rr)
    e = (e[0] + dx * d, e[1] + dy * d)
    h = _lerp2(g["hip"], g["knee"], k0)
    _capsule(ctx, h[0], h[1], rr[0] + d, g["knee"][0], g["knee"][1], rr[1] + d)
    _quad(ctx, g["knee"], rr[1] + d, e, rr[2] + d)


def _draw_leg(ctx, C, col, g, inkw, other=None, k0=0.0):
    _draw_shoe(ctx, C, col, g, inkw)
    rr = C["leg_r"]
    pk = clamp(1.0 + g["knee"][2] * 0.0012, 0.9, 1.25)
    sf = g.get("sf", 0.0)
    rr = (rr[0] * (1.0 - 0.16 * sf), rr[1] * pk, rr[2] * clamp(1.0 + g["ankle"][2] * 0.0012, 0.9, 1.2))
    rp = rr[0] * (1.05 - 0.12 * sf)

    def build(d):
        _leg_path(ctx, C, g, rr, k0, d)
        if other is not None:    # pelvis piece joins this (near) leg with the hips
            h0, h1 = g["hip"], other["hip"]
            _capsule(ctx, h0[0], h0[1] - 6, rp + d, h1[0], h1[1] - 6, rp + d)
    _ink_fill(ctx, build, col["pants"], inkw)
    # cuff band at the ankle (sweatpants elastic / trousers hem)
    kn, an = g["knee"], g["ankle"]
    dx, dy = _norm(an[0] - kn[0], an[1] - kn[1])
    st = C["_pants"]
    if st in ("sweat",):
        e, _ = _leg_end(g, rr)
        c0 = (e[0] - dx * 17, e[1] - dy * 17)
        ctx.new_path()
        _quad(ctx, c0, rr[2] * 0.98, e, rr[2] * 0.86)
        _fs(ctx, col["pants_dk"], inkw * 0.8)
    # knee fold line on bent knees
    bend = abs(math.atan2(an[1] - kn[1], an[0] - kn[0]) - math.atan2(kn[1] - g["hip"][1], kn[0] - g["hip"][0]))
    bend = min(bend, TAU - bend)
    if bend > 0.35:
        nx, ny = -dy, dx
        ctx.move_to(kn[0] + nx * rr[1] * 0.2 - dx * 6, kn[1] + ny * rr[1] * 0.2 - dy * 6)
        ctx.line_to(kn[0] - nx * rr[1] * 0.5 + dx * 4, kn[1] - ny * rr[1] * 0.5 + dy * 4)
        _set(ctx, alpha_ink(PAL["ink"], 0.5))
        ctx.set_line_width(inkw * 0.6)
        ctx.stroke()


def _draw_arm(ctx, C, col, a, side, J, inkw, t, phase):
    Q = J["Q"]
    S, E, Wr, ang = a["S"], a["E2"], a["W2"], a["ang"]
    rr = C["arm_r"]
    hide = Q[f"a{side}_hide"] > 0.5
    hand_pt = Wr
    ysign = (-1.0 if side == "l" else 1.0) * (1.0 if Q[f"a{side}_tf"] >= 0 else -1.0)
    tfk = abs(Q[f"a{side}_tf"])
    persp = clamp(1.0 + a["zW"] * 0.0011, 0.88, 1.22)
    hs = C["hand"] * persp
    skin = col["skin"]
    sleeve = C["_sleeve"]
    if not hide:
        hy = ysign * max(0.35, tfk)
        hand_pt = _draw_hand(ctx, skin, PAL["ink"], Wr, ang, Q[f"a{side}_h"], hy, hs, inkw, phase,
                             Q[f"a{side}_fing"], Q[f"a{side}_thumb"], palm_view=Q[f"a{side}_tf"] < 0)
    a["hold_pt"] = hand_pt
    if sleeve == "short":
        def b1(d):
            _capsule(ctx, S[0], S[1], rr[0] * 0.8 + d, E[0], E[1], rr[1] * 0.78 + d)
            _capsule(ctx, E[0], E[1], rr[1] * 0.78 + d, Wr[0], Wr[1], rr[2] * 0.75 + d)
        _ink_fill(ctx, b1, skin, inkw)
        m = _lerp2(S, E, 0.62)

        def b2(d):
            circle(ctx, S[0], S[1], rr[0] * 1.08 + d)
            _quad(ctx, S, rr[0] * 1.08 + d, m, rr[0] * 0.98 + d)
        _ink_fill(ctx, b2, col["top"], inkw)
        return
    dx, dy = _norm(Wr[0] - E[0], Wr[1] - E[1])
    We = (Wr[0] + dx * rr[2] * 0.15, Wr[1] + dy * rr[2] * 0.15)
    pushed = J.get("_bandage") == side
    if pushed:   # sleeve shoved up to the elbow: bare forearm (for the bandage)
        def b3(d):
            circle(ctx, S[0], S[1], rr[0] * 1.04 + d)
            _capsule(ctx, S[0], S[1], rr[0] + d, E[0], E[1], rr[1] + d)
        _ink_fill(ctx, b3, col["top"], inkw)
        _ink_fill(ctx, lambda d: _capsule(ctx, E[0], E[1], rr[1] * 0.72 + d, We[0], We[1], rr[2] * 0.72 + d),
                  skin, inkw)
        ctx.new_path()
        _capsule(ctx, E[0] - dx * 6, E[1] - dy * 6, rr[1] * 1.08, E[0] + dx * 10, E[1] + dy * 10, rr[1] * 1.0)
        _fs(ctx, col["top_dk"], inkw * 0.85)
        return
    def b4(d):
        circle(ctx, S[0], S[1], rr[0] * 1.04 + d)
        _capsule(ctx, S[0], S[1], rr[0] + d, E[0], E[1], rr[1] + d)
        circle(ctx, E[0], E[1], rr[1] + d)
        _quad(ctx, E, rr[1] + d, (We[0] + dx * d, We[1] + dy * d), rr[2] * 1.04 + d)
    _ink_fill(ctx, b4, col.get("sleeve", col["top"]), inkw)
    # cuff
    cuff = {"hoodie": col["top_dk"], "labcoat": col["top_dk"], "suit": "#e9ecf2",
            "uniform": col["top_dk"], "cardigan": col["top_dk"]}.get(C["_top"], col["top_dk"])
    clen = 20 if C["_top"] in ("hoodie", "cardigan") else 12
    ctx.new_path()
    _quad(ctx, (We[0] - dx * clen, We[1] - dy * clen), rr[2] * 1.06, We, rr[2] * 1.04)
    _fs(ctx, cuff, inkw * 0.85)
    # elbow fold
    ex, ey = _norm(E[0] - S[0], E[1] - S[1])
    cr = ex * dy - ey * dx
    if abs(cr) > 0.3:
        nx, ny = -ey * (1 if cr > 0 else -1), ex * (1 if cr > 0 else -1)
        ctx.move_to(E[0] + nx * rr[1] * 0.75 - ex * 8, E[1] + ny * rr[1] * 0.75 - ey * 8)
        ctx.line_to(E[0] + nx * rr[1] * 0.1 + dx * 3, E[1] + ny * rr[1] * 0.1 + dy * 3)
        _set(ctx, alpha_ink(PAL["ink"], 0.45))
        ctx.set_line_width(inkw * 0.55)
        ctx.stroke()


# ============================================================================
# 7b. DRAWING: torso + outfits
# ============================================================================
def _torso_geom(C, J):
    """Torso outline points + per-level frames (centre, normal, wL, wR, front offset)."""
    nd = J["nodes"]
    phi = J["phi"]
    c, s = math.cos(phi), math.sin(phi)
    tw = C["tw"]
    keys = (("hem", "hem"), ("pel", "hip"), ("wst", "waist"), ("chs", "chest"), ("shl", "shoulder"))
    lv = {}
    for i, (nk, wk) in enumerate(keys):
        p = nd[nk]
        up_from = nd[keys[max(0, i - 1)][0]] if i > 0 else nd["hem"]
        up_to = nd[keys[min(len(keys) - 1, i + 1)][0]]
        if i == 0:
            up_from, up_to = nd["hem"], nd["pel"]
        tx, ty = _norm(up_to[0] - up_from[0], up_to[1] - up_from[1])
        nx, ny = -ty, tx
        if abs(nx) < 1e-6 and abs(ny) < 1e-6:     # (Ep2 fix: a horizontal spine is valid)
            nx, ny = 1.0, 0.0
        a, f, b = tw[wk]
        sf = J.get("seat_flat", 0.0)
        if sf > 0 and wk in ("hem", "hip", "waist"):
            b *= 1.0 - {"hem": 0.4, "hip": 0.36, "waist": 0.15}[wk] * sf
        if wk == "chest":
            a += J["Q"]["breath"] * 1.2 * math.sin(TAU * J["t"] / 3.7 + C["seed"])
        fr = f if s >= 0 else b
        bk = b if s >= 0 else f
        wR = math.sqrt((a * c) ** 2 + (fr * s) ** 2)
        wL = math.sqrt((a * c) ** 2 + (bk * s) ** 2)
        lv[wk] = dict(p=p, n=(nx, ny), t=(tx, ty), wL=wL, wR=wR, front=f * s, a=a)
    return lv


def _pt(lv, key, u, du=0.0):
    """Point on level `key` at u (-1 = left edge, 0 = centre, +1 = right edge), du along spine."""
    L = lv[key]
    w = L["wR"] if u >= 0 else L["wL"]
    p, n, t = L["p"], L["n"], L["t"]
    return (p[0] + n[0] * w * u + t[0] * du, p[1] + n[1] * w * u + t[1] * du)


def _front(lv, key, off=0.0, du=0.0):
    """Point on the front centre line of level `key` (off = sideways px, du along spine)."""
    L = lv[key]
    p, n, t = L["p"], L["n"], L["t"]
    k = math.cos(abs(math.asin(clamp(L["front"] / max(1.0, L["a"] + 30), -1, 1))))
    x = L["front"] + off * k
    return (p[0] + n[0] * x + t[0] * du, p[1] + n[1] * x + t[1] * du)


def _torso_pts(C, J, lv):
    sh = J["shj"]
    nk = J["nodes"]["nck"]
    Ls, Lc = lv["shoulder"], lv["chest"]
    t = Ls["t"]
    n = Ls["n"]
    ar = C["arm_r"][0]
    pts = [_pt(lv, "hem", -1.0), _pt(lv, "hip", -1.0), _pt(lv, "waist", -1.0), _pt(lv, "chest", -1.0)]
    sl, sr = sh["l"], sh["r"]
    # outer shoulder tops: whichever is further out than the chest edge
    pts.append((sl[0] - n[0] * ar * 0.25 + t[0] * ar * 0.8, sl[1] - n[1] * ar * 0.25 + t[1] * ar * 0.8))
    nr = C["neck_r"] * 1.35
    pts.append((nk[0] - n[0] * nr + t[0] * 4, nk[1] - n[1] * nr + t[1] * 4))
    pts.append((nk[0] + n[0] * nr + t[0] * 4, nk[1] + n[1] * nr + t[1] * 4))
    pts.append((sr[0] + n[0] * ar * 0.25 + t[0] * ar * 0.8, sr[1] + n[1] * ar * 0.25 + t[1] * ar * 0.8))
    pts += [_pt(lv, "chest", 1.0), _pt(lv, "waist", 1.0), _pt(lv, "hip", 1.0), _pt(lv, "hem", 1.0)]
    hc = lv["hem"]["p"]
    ht = lv["hem"]["t"]
    pts.append((hc[0] - ht[0] * 5, hc[1] - ht[1] * 5))
    return pts


def _draw_hood(ctx, C, col, J, inkw):
    """Tiredness's hood lump behind the neck (drawn before the torso)."""
    nk = J["nodes"]["nck"]
    lv = J["_lv"]
    n, t = lv["shoulder"]["n"], lv["shoulder"]["t"]
    s = math.sin(J["phi"])
    cx = nk[0] - n[0] * s * 22
    cy = nk[1] - n[1] * s * 22
    w = C["neck_r"] * 2.5
    pts = [(cx - n[0] * w + t[0] * -14, cy - n[1] * w - t[1] * 14),
           (cx - n[0] * w * 0.8 + t[0] * 26, cy - n[1] * w * 0.8 + t[1] * 26),
           (cx + t[0] * 36, cy + t[1] * 36),
           (cx + n[0] * w * 0.8 + t[0] * 26, cy + n[1] * w * 0.8 + t[1] * 26),
           (cx + n[0] * w + t[0] * -14, cy + n[1] * w - t[1] * 14),
           (cx, cy - t[1] * 10)]
    _smooth(ctx, pts, True, 0.55)
    _fs(ctx, col["top_dk"], inkw * 2 * 0.5 * 2)


def _draw_neck(ctx, C, col, J, inkw, blush_k=0.0):
    a, b = J["nodes"]["nck"], J["head"]["pivot"]
    r = C["neck_r"]
    ctx.new_path()
    _capsule(ctx, a[0], a[1] + 8, r * 1.05, b[0], b[1], r)
    _set(ctx, PAL["ink"])
    ctx.set_line_width(inkw * 2)
    ctx.stroke_preserve()
    skin = col["skin"]
    if blush_k > 0:
        skin = mixc(skin, PAL["blush"], 0.35 * blush_k)
    _set(ctx, skin)
    ctx.fill()
    # chin shadow
    ctx.save()
    ctx.new_path()
    _capsule(ctx, a[0], a[1] + 8, r * 1.05, b[0], b[1], r)
    ctx.clip()
    ellipse(ctx, b[0], b[1] + 6, r * 1.3, r * 0.8, J["head"]["tilt"])
    _set(ctx, col["skin_sh"])
    ctx.fill()
    ctx.restore()


def _coat_tails(ctx, C, col, J, inkw, part):
    """Lab-coat skirt below the torso hem. part = 'back' (between legs) or 'front'."""
    lv = J["_lv"]
    Q = J["Q"]
    lagQ = J["lag"] or Q
    fd = J["fdir"]
    trail = Q["coat_trail"]
    ln = C["thigh"] * 0.5
    out = {}
    for s_, sgn, u in (("l", -1, -1.0), ("r", 1, 1.0)):
        lp = lagQ[f"l{s_}_p"]
        lo = lagQ[f"l{s_}_o"]
        d3 = _dir(lp * 0.65, lo, sgn)
        dx = d3[0] * math.cos(J["phi"]) + d3[2] * math.sin(J["phi"])
        dy = d3[1]
        dx = dx * 0.8 - fd * trail * 0.55
        dx, dy = _norm(dx, max(0.35, dy))
        if J["rot"]:                # tails follow the body roll (lying / tipping poses)
            dx, dy = _rot(dx, dy, J["rot"])
        top_o = _pt(lv, "hem", u, 2)
        top_i = _front(lv, "hem", sgn * C["tw"]["hem"][0] * 0.16, 2)
        out[s_] = (top_o, top_i, (dx, dy))
    if part == "back":
        (lo_, li_, dl), (ro_, ri_, dr) = out["l"], out["r"]
        lb = ln * 0.8
        lo_, ro_ = _lerp2(lo_, li_, 0.25), _lerp2(ro_, ri_, 0.25)
        pts = [lo_, ro_, (ro_[0] + dr[0] * lb, ro_[1] + dr[1] * lb),
               (lo_[0] + dl[0] * lb, lo_[1] + dl[1] * lb)]
        _poly(ctx, pts)
        _fs(ctx, col["top_dk"], inkw)
        return
    for s_, sgn in (("l", -1), ("r", 1)):
        top_o, top_i, (dx, dy) = out[s_]
        flare = sgn * 10 + (-J["fdir"]) * trail * 22
        bo = (top_o[0] + dx * ln * 1.02 + flare, top_o[1] + dy * ln * 1.02)
        bi = (top_i[0] + dx * ln * 0.96, top_i[1] + dy * ln * 0.96)
        pts = [top_o, bo, bi, top_i]
        _poly(ctx, pts)
        _fs(ctx, col["top"], inkw)
        # hem shading line
        ctx.move_to(*_lerp2(bo, bi, 0.0))
        ctx.line_to(*bi)
        _set(ctx, alpha_ink(col["top_dk"], 1.0))
        ctx.set_line_width(5)
        ctx.stroke()


def _draw_torso(ctx, C, col, J, inkw, t):
    lv = J["_lv"]
    pts = _torso_pts(C, J, lv)
    top = C["_top"]
    base = col["top"]
    ctx.save()
    _smooth(ctx, pts, True, 0.5)
    ctx.clip_preserve()
    _set(ctx, col["top_dk"])
    ctx.fill()
    ctx.translate(-13, -6)
    _smooth(ctx, pts, True, 0.5)
    _set(ctx, base)
    ctx.fill()
    ctx.translate(13, 6)
    anchors = _torso_details(ctx, C, col, J, lv, top, inkw, t)
    ctx.restore()
    _smooth(ctx, pts, True, 0.5)
    _stroke(ctx, PAL["ink"], inkw)
    _torso_overlay(ctx, C, col, J, lv, top, inkw, t)
    return anchors


def _shape(ctx, pts, fc, inkw, tension=0.0):
    if tension:
        _smooth(ctx, pts, True, tension)
    else:
        _poly(ctx, pts)
    _fs(ctx, fc, inkw)


def _torso_details(ctx, C, col, J, lv, top, inkw, t):
    """Garment details inside the torso clip. Returns {'pocket': (x, y)}."""
    ink = PAL["ink"]
    thin = inkw * 0.7
    aw = C["tw"]["waist"][0]
    ps = J.get("_pocket_sgn", 1.0)      # chest pocket side: +1 screen-right (default), -1 left
    pocket = _front(lv, "chest", ps * C["tw"]["chest"][0] * 0.5, 22)
    if top == "hoodie":
        # hem band
        _shape(ctx, [_pt(lv, "hem", -1.2, -4), _pt(lv, "hem", 1.2, -4), _pt(lv, "hem", 1.2, 20),
                     _pt(lv, "hem", -1.2, 20)], col["top_dk"], thin)
        # kangaroo pocket
        y0, y1 = 20, 62
        p = [_front(lv, "hem", -aw * 0.62, y0), _front(lv, "hem", aw * 0.62, y0),
             _front(lv, "hem", aw * 0.44, y1 + 26), _front(lv, "hem", -aw * 0.44, y1 + 26)]
        _shape(ctx, p, _dk(col["top"], 0.08), thin, 0.0)
        for sgn in (-1, 1):
            a0 = _front(lv, "hem", sgn * aw * 0.44, y1 + 24)
            a1 = _front(lv, "hem", sgn * aw * 0.6, y0 + 2)
            c0 = _front(lv, "hem", sgn * aw * 0.66, y1 + 16)
            ctx.move_to(*a0)
            _qcurve(ctx, a0, c0, a1)
            _stroke(ctx, ink, thin)
        pocket = _front(lv, "chest", ps * C["tw"]["chest"][0] * 0.45, 26)
    elif top == "polo":
        # placket + buttons
        a0, a1 = _front(lv, "shoulder", -9, 8), _front(lv, "chest", -9, -8)
        b0, b1 = _front(lv, "shoulder", 9, 8), _front(lv, "chest", 9, -8)
        _shape(ctx, [a0, b0, b1, a1], _dk(col["top"], 0.06), thin)
        for k in (0.35, 0.75):
            q = _lerp2(_front(lv, "shoulder", 0, 8), _front(lv, "chest", 0, -8), k)
            circle(ctx, q[0], q[1], 3.2)
            _fs(ctx, "#f4efe2", 2)
        _shape(ctx, [_pt(lv, "hem", -1.2, -4), _pt(lv, "hem", 1.2, -4), _pt(lv, "hem", 1.2, 10),
                     _pt(lv, "hem", -1.2, 10)], col["top_dk"], thin)
    elif top == "labcoat":
        # open front: vest + shirt + slacks visible
        g_top = C["neck_r"] * 1.1
        g_bot = aw * 0.36
        L0, R0 = _front(lv, "shoulder", -g_top, 16), _front(lv, "shoulder", g_top, 16)
        L1, R1 = _front(lv, "hem", -g_bot, -4), _front(lv, "hem", g_bot, -4)
        _shape(ctx, [L0, R0, R1, L1], col["vest"], thin)
        # slacks showing below the vest
        W0, W1 = _front(lv, "waist", -g_bot * 0.9, -8), _front(lv, "waist", g_bot * 0.9, -8)
        _shape(ctx, [W0, W1, R1, L1], col["pants"], thin)
        # shirt collar V
        n0 = _front(lv, "shoulder", 0, -10)
        v = _front(lv, "chest", 0, 10)
        _shape(ctx, [_front(lv, "shoulder", -g_top * 0.9, 18), _front(lv, "shoulder", g_top * 0.9, 18), v],
               "#ffffff", thin)
        _shape(ctx, [_front(lv, "shoulder", -g_top * 0.95, 22), n0, _front(lv, "shoulder", -2, 0),
                     _front(lv, "shoulder", -g_top * 0.2, -8)], "#ffffff", thin)
        # lapels
        for sgn in (-1, 1):
            a = _front(lv, "shoulder", sgn * g_top * 1.0, 18)
            b = _front(lv, "chest", sgn * (g_top * 1.0 + 26), 10)
            c = _front(lv, "chest", sgn * g_top * 0.95, -16)
            _shape(ctx, [a, b, c], col["top_dk"] if sgn > 0 else col["top"], thin)
        # breast pocket (wearer's left = screen right) with pens
        pc = _front(lv, "chest", ps * aw * 0.66, 4)
        pw, ph = 22, 24
        n, tt = lv["chest"]["n"], lv["chest"]["t"]

        def Pp(x, y):
            return (pc[0] + n[0] * x - tt[0] * y, pc[1] + n[1] * x - tt[1] * y)
        for i, pcol in enumerate(("#2b6cd8", "#e2463f")):
            x = -8 + i * 11
            _shape(ctx, [Pp(x - 3, -10), Pp(x + 3, -10), Pp(x + 3, 12), Pp(x - 3, 12)], pcol, 2.5)
        _shape(ctx, [Pp(-pw, 0), Pp(pw, 0), Pp(pw * 0.9, ph), Pp(-pw * 0.9, ph)], col["top"], thin)
        pocket = Pp(0, 6)
        # hip pockets
        for sgn in (-1, 1):
            q = _front(lv, "hem", sgn * aw * 0.85, 30)
            ctx.move_to(q[0] - 18, q[1])
            ctx.line_to(q[0] + 18, q[1])
            _stroke(ctx, ink, thin)
    elif top == "suit":
        g = C["neck_r"] * 1.0
        v = _front(lv, "waist", 0, 20)
        _shape(ctx, [_front(lv, "shoulder", -g, 20), _front(lv, "shoulder", g, 20), v],
               col["top_dk"], thin)
        for sgn in (-1, 1):
            a = _front(lv, "shoulder", sgn * g * 1.05, 18)
            b = _front(lv, "chest", sgn * (g + 30), 16)
            c = _front(lv, "chest", sgn * (g + 14), -6)
            _shape(ctx, [a, b, c, v], _dk(col["top"], 0.18), thin)
        btn = _front(lv, "waist", 0, 14)
        circle(ctx, btn[0], btn[1], 4.5)
        _fs(ctx, "#111218", 2)
        # jacket front parting below the button
        h0 = _front(lv, "hem", 0, 0)
        ctx.move_to(*btn)
        ctx.line_to(h0[0] - 6, h0[1] + 6)
        _stroke(ctx, ink, thin)
        pocket = _front(lv, "chest", ps * C["tw"]["chest"][0] * 0.5, 14)
    elif top == "uniform":
        # placket
        a0, a1 = _front(lv, "shoulder", 0, 10), _front(lv, "hem", 0, 0)
        ctx.move_to(*a0)
        ctx.line_to(*a1)
        _stroke(ctx, ink, thin)
        for k in (0.2, 0.42, 0.64):
            q = _lerp2(a0, a1, k)
            circle(ctx, q[0] + 6, q[1], 3.5)
            _fs(ctx, "#c9ced8", 2)
        # chest pocket flaps
        for sgn in (-1, 1):
            c0 = _front(lv, "chest", sgn * 46, 14)
            _shape(ctx, [(c0[0] - 22, c0[1] - 8), (c0[0] + 22, c0[1] - 8), (c0[0] + 20, c0[1] + 6),
                         (c0[0], c0[1] + 12), (c0[0] - 20, c0[1] + 6)], col["top_dk"], thin)
        # belt
        _shape(ctx, [_pt(lv, "hem", -1.2, 14), _pt(lv, "hem", 1.2, 14), _pt(lv, "hem", 1.2, 34),
                     _pt(lv, "hem", -1.2, 34)], "#1a1b22", thin)
        bk = _front(lv, "hem", 0, 24)
        ctx.rectangle(bk[0] - 11, bk[1] - 8, 22, 16)
        _fs(ctx, "#c9ced8", 2.5)
        pocket = _front(lv, "chest", ps * 46, 22)
    elif top == "cardigan":
        g_top = C["neck_r"] * 1.0
        L0, R0 = _front(lv, "shoulder", -g_top, 14), _front(lv, "shoulder", g_top, 14)
        v = _front(lv, "waist", 0, 6)
        _shape(ctx, [L0, R0, (v[0] + 4, v[1]), (v[0] - 4, v[1])], col["blouse"], thin)
        for k in (0.25, 0.55, 0.85):
            q = _lerp2(L0, _front(lv, "hem", -6, 0), 0.25 + k * 0.7)
            circle(ctx, q[0] - 8, q[1], 3.5)
            _fs(ctx, "#f2e9f7", 2)
        _shape(ctx, [_pt(lv, "hem", -1.2, -4), _pt(lv, "hem", 1.2, -4), _pt(lv, "hem", 1.2, 16),
                     _pt(lv, "hem", -1.2, 16)], col["top_dk"], thin)
        # name badge
        bc = _front(lv, "chest", 44, 18)
        ctx.rectangle(bc[0] - 15, bc[1] - 7, 30, 14)
        _fs(ctx, "#ffffff", 2.5)
        pocket = bc if ps > 0 else _front(lv, "chest", -44, 18)
    return {"pocket": pocket}


def _torso_overlay(ctx, C, col, J, lv, top, inkw, t):
    """Details that sit on top of the torso outline (collars, strings, badges)."""
    thin = inkw * 0.7
    nk = J["nodes"]["nck"]
    n, tt = lv["shoulder"]["n"], lv["shoulder"]["t"]
    if top == "hoodie":
        # collar ribbing around the neck front
        fx = lv["shoulder"]["front"] * 0.35
        cx, cy = nk[0] + n[0] * fx, nk[1] + n[1] * fx
        r = C["neck_r"] * 1.4
        ctx.move_to(cx - n[0] * r, cy - n[1] * r)
        _qcurve(ctx, (cx - n[0] * r, cy - n[1] * r), (cx - tt[0] * 30, cy - tt[1] * 30 + 0),
                (cx + n[0] * r, cy + n[1] * r))
        _stroke(ctx, PAL["ink"], inkw * 0.9)
        # drawstrings
        sw_ = math.sin(t * 1.3 + C["seed"]) * 2
        for sgn in (-1, 1):
            a = (cx + n[0] * sgn * 13 - tt[0] * 20, cy + n[1] * sgn * 13 - tt[1] * 20)
            ln = 70 + sgn * 8
            b = (a[0] - tt[0] * ln + sw_ + sgn * 3, a[1] - tt[1] * ln)
            ctx.move_to(*a)
            _qcurve(ctx, a, ((a[0] + b[0]) / 2 + sgn * 4, (a[1] + b[1]) / 2), b)
            _stroke(ctx, PAL["ink"], 7.5)
            ctx.move_to(*a)
            _qcurve(ctx, a, ((a[0] + b[0]) / 2 + sgn * 4, (a[1] + b[1]) / 2), b)
            _stroke(ctx, "#e9e6f2", 3.2)
            ctx.new_path()
            _capsule(ctx, b[0], b[1] - 2, 3.6, b[0], b[1] + 9, 3.6)
            _fs(ctx, "#d8d4e2", 2.5)
    elif top == "polo":
        fx = lv["shoulder"]["front"] * 0.35
        cx, cy = nk[0] + n[0] * fx, nk[1] + n[1] * fx
        r = C["neck_r"] * 1.35
        for sgn in (-1, 1):
            p = [(cx + n[0] * sgn * r * 0.15 + tt[0] * 2, cy + tt[1] * 2),
                 (cx + n[0] * sgn * r * 1.15, cy + n[1] * sgn * r * 1.15 - tt[1] * 6),
                 (cx + n[0] * sgn * r * 0.75 - tt[0] * 28, cy - tt[1] * 28)]
            _shape(ctx, p, _lt(col["top"], 0.25), thin)
        # lanyard + badge
        b = _front(lv, "chest", -6, -6)
        for sgn in (-1, 1):
            ctx.move_to(cx + n[0] * sgn * r, cy + n[1] * sgn * r)
            ctx.line_to(b[0] + sgn * 5, b[1] - 18)
            _stroke(ctx, PAL["ink"], 8)
            ctx.move_to(cx + n[0] * sgn * r, cy + n[1] * sgn * r)
            ctx.line_to(b[0] + sgn * 5, b[1] - 18)
            _stroke(ctx, PAL["hush"], 4)
        ctx.new_path()
        ctx.rectangle(b[0] - 18, b[1] - 16, 36, 46)
        _fs(ctx, "#ffffff", 3)
        ctx.rectangle(b[0] - 18, b[1] - 16, 36, 9)
        _fs(ctx, PAL["hush"], 2)
        ctx.rectangle(b[0] - 10, b[1] - 2, 20, 18)
        _fs(ctx, "#c9d2da", 2)
    elif top == "suit":
        pin = _front(lv, "chest", 34, 26)
        circle(ctx, pin[0], pin[1], 5.5)
        _fs(ctx, PAL["hush"], 2.5)
    elif top == "uniform":
        # badge (wearer's left) + shoulder radio
        bd = _front(lv, "chest", 48, 34)
        p = [(bd[0], bd[1] - 14), (bd[0] + 12, bd[1] - 8), (bd[0] + 10, bd[1] + 8), (bd[0], bd[1] + 14),
             (bd[0] - 10, bd[1] + 8), (bd[0] - 12, bd[1] - 8)]
        _shape(ctx, p, "#e8c25a", 3)
        sl = J["shj"]["l"]
        rx, ry = sl[0] + n[0] * 26 - tt[0] * 0, sl[1] + 24
        ctx.new_path()
        ctx.rectangle(rx - 12, ry - 16, 24, 32)
        _fs(ctx, "#1a1b22", 3)
        ctx.move_to(rx - 6, ry - 16)
        ctx.line_to(rx - 6, ry - 38)
        _stroke(ctx, PAL["ink"], 5)
        circle(ctx, rx + 3, ry - 6, 3)
        _fs(ctx, PAL["danger"], 1.5)


# ============================================================================
# 7c. HEAD: geometry + hair
# ============================================================================
# Hair shapes in the head-local FRONT view (origin = eye-line centre, y down).
HAIR = {
    "mop": dict(
        back=[(-100, 34), (-112, 6), (-110, -14), (-122, -40), (-113, -62), (-121, -88), (-101, -114),
              (-82, -136), (-48, -154), (-10, -160), (30, -158), (66, -146), (96, -124), (117, -98),
              (112, -74), (124, -50), (111, -26), (115, 4), (100, 34), (84, -10), (40, -40), (-40, -40),
              (-84, -10)],
        front=[(-100, -12), (-107, -50), (-101, -86), (-80, -117), (-44, -140), (0, -148), (44, -142),
               (80, -121), (102, -89), (109, -52), (103, -16), (95, -30), (90, -54), (79, -42), (70, -68),
               (54, -40), (44, -66), (24, -34), (14, -64), (-2, -46), (-16, -72), (-40, -34), (-50, -62),
               (-66, -46), (-78, -68), (-92, -36)],
        tuft=[(-16, -144), (-15, -162), (-3, -176), (14, -179), (8, -169), (2, -158), (6, -144)],
        strands=[[(-60, -112), (-46, -92), (-38, -80)], [(20, -128), (30, -104), (32, -86)],
                 [(60, -112), (72, -92), (74, -76)], [(-20, -126), (-14, -100)]],
        tension=0.55),
    "part": dict(
        back=[(-96, 22), (-104, -20), (-104, -60), (-94, -96), (-70, -126), (-34, -144), (6, -150),
              (46, -142), (80, -120), (100, -86), (106, -46), (102, -6), (96, 22), (70, -30), (0, -50),
              (-70, -30)],
        front=[(-96, -10), (-102, -50), (-96, -86), (-77, -116), (-46, -136), (-28, -141), (6, -153),
               (48, -147), (84, -123), (104, -88), (109, -50), (101, -12), (93, -40), (79, -70),
               (52, -91), (16, -101), (-14, -101), (-30, -105), (-50, -93), (-72, -77), (-88, -50)],
        tuft=[(4, -150), (0, -166), (12, -180), (27, -182), (20, -172), (18, -162), (20, -150)],
        strands=[[(-30, -106), (-36, -138)], [(0, -136), (40, -128), (74, -104)], [(20, -116), (56, -106)]],
        tension=0.5),
    "bob": dict(
        back=[(-104, 70), (-114, 20), (-114, -36), (-104, -80), (-80, -118), (-44, -140), (0, -146),
              (44, -140), (80, -118), (104, -80), (114, -36), (114, 20), (104, 70), (84, 74), (64, 26),
              (0, -40), (-64, 26), (-84, 74)],
        front=[(-104, -10), (-109, -56), (-95, -100), (-62, -131), (-14, -147), (36, -143), (76, -123),
               (100, -91), (108, -50), (104, -14), (95, -40), (80, -72), (56, -98), (42, -103), (16, -88),
               (-18, -70), (-54, -54), (-84, -38), (-100, -16)],
        sides=[[(-100, -40), (-112, 0), (-112, 46), (-104, 84), (-72, 101), (-80, 60), (-86, 16), (-90, -24)],
               [(100, -50), (112, -6), (112, 42), (102, 80), (68, 99), (78, 58), (84, 14), (88, -30)]],
        strands=[[(-16, -128), (-50, -102), (-80, -64)], [(30, -132), (2, -112), (-30, -88)],
                 [(-104, -6), (-104, 40), (-94, 78)], [(104, -10), (104, 38), (94, 76)], [(62, -126), (82, -98)]],
        tension=0.36),
    "cap": dict(
        back=[(-102, -60), (-104, -20), (-100, 6), (-92, 10), (-90, -40), (90, -40), (92, 10), (100, 6),
              (104, -20), (102, -60), (90, -96), (-90, -96)],
        front=[(-100, -40), (-104, -6), (-94, 6), (-90, -30)],
        front2=[(100, -40), (104, -6), (94, 6), (90, -30)],
        strands=[], tension=0.5),
    "bun": dict(
        back=[(-98, 30), (-106, -20), (-102, -70), (-84, -108), (-50, -134), (0, -142), (50, -134),
              (84, -108), (102, -70), (106, -20), (98, 30), (70, -20), (0, -40), (-70, -20)],
        bun=(10, -150, 33),
        front=[(-98, -10), (-104, -56), (-90, -96), (-60, -124), (-16, -138), (30, -134), (70, -116),
               (96, -84), (104, -44), (98, -8), (86, -36), (66, -64), (34, -80), (0, -84), (-34, -76),
               (-62, -60), (-84, -38)],
        strands=[[(-30, -128), (-56, -98), (-72, -66)], [(20, -128), (52, -108)]],
        tension=0.5),
}


class _HG:
    """Head geometry for the current yaw / cheek puff / jaw drop."""

    def __init__(self, C, J, F, opn):
        hd = C["head"]
        self.hd = hd
        psi = J["head"]["psi"]
        self.c, self.s = math.cos(psi), math.sin(psi)
        self.nod = J["head"]["nod"]
        self.cheek = F["cheek"]
        self.drop = opn * 16.0 + F["squash"] * 0.0
        my, ch = hd["mouth_y"], hd["chin"]
        self.my, self.ch = my, ch
        lv = []
        for (y, a, f, b) in hd["levels"]:
            if y > my - 10:
                y = y + self.drop * (y - (my - 10)) / max(1.0, ch - (my - 10))
            if 20 < y < 90:
                a += self.cheek * 9 * math.sin((y - 20) / 70 * math.pi)
            lv.append((y, a, f, b))
        self.lv = lv
        self.chin = ch + self.drop

    def abf(self, y):
        lv = self.lv
        if y <= lv[0][0]:
            return lv[1][1:] if y < lv[0][0] - 1 else lv[0][1:]
        for i in range(1, len(lv)):
            if y <= lv[i][0]:
                y0, a0, f0, b0 = lv[i - 1]
                y1, a1, f1, b1 = lv[i]
                k = (y - y0) / (y1 - y0)
                return (a0 + (a1 - a0) * k, f0 + (f1 - f0) * k, b0 + (b1 - b0) * k)
        return lv[-1][1:]

    def ext(self, a, f, b):
        c, s = self.c, self.s
        fr, bk = (f, b) if s >= 0 else (b, f)
        return (-math.sqrt((a * c) ** 2 + (bk * s) ** 2), math.sqrt((a * c) ** 2 + (fr * s) ** 2))

    def proj(self, xf, y, dz=0.0):
        a, f, b = self.abf(y)
        a = max(a, 1.0)
        u = clamp(xf / a, -0.999, 0.999)
        th = math.asin(u)
        ct = math.cos(th)
        c, s = self.c, self.s
        X = a * u * c + (f * ct + dz) * s
        Z = -a * u * s + (f * ct + dz) * c
        k = ct * c - (f / a) * u * s
        return X, Z, max(0.04, k)

    def outline(self):
        lv = self.lv
        right, left = [], []
        for (y, a, f, b) in lv[1:]:
            el, er = self.ext(a, f, b)
            right.append((er, y))
            left.append((el, y))
        y0 = lv[0][0]
        fch = lv[-1][2]
        pts = [(0.0 + self.s * 6, y0)] + right + [(fch * self.s * 0.9, self.chin)] + left[::-1]
        return pts

    def warp(self, x, y, mode="front", dz=0.0):
        """Map a front-view hair/accessory point onto the turned head."""
        a, f, b = self.abf(clamp(min(y, 0.0), self.lv[0][0] + 2, self.lv[-1][0]))
        a = max(a, 40.0)
        el, er = self.ext(a, f, b)
        u = x / a
        side = er if u >= 0 else -el
        if mode == "back":
            return (u * side, y)
        if abs(u) >= 1.0:
            X = u * side
        else:
            Xi = a * u * self.c + (f * math.sqrt(1 - u * u) + dz) * self.s
            w = smoothstep((abs(u) - 0.55) / 0.45)
            X = Xi + (u * side - Xi) * w
        return (X, y)


def _hair_path(ctx, hg, pts, mode, tension, dy=0.0):
    wp = [hg.warp(x, y + (dy if y > -110 else dy * 0.5), mode) for x, y in pts]
    _smooth(ctx, wp, True, tension)
    return wp


def _draw_back_hair(ctx, C, col, hg, F, inkw, wet):
    st = HAIR[C["head"]["hair"]]
    hcol = col["hair"]
    if "bun" in st:
        bx, by, br = st["bun"]
        X, _ = hg.warp(bx, by, "back")
        circle(ctx, X, by, br)
        _fs(ctx, hcol, inkw)
        ctx.move_to(X - br * 0.5, by - br * 0.3)
        _qcurve(ctx, (X - br * 0.5, by - br * 0.3), (X, by - br * 0.8), (X + br * 0.55, by - br * 0.1))
        _stroke(ctx, _dk(hcol, 0.4), inkw * 0.5)
    _hair_path(ctx, hg, st["back"], "back", st["tension"])
    _fs(ctx, _dk(hcol, 0.12), inkw)


def _draw_front_hair(ctx, C, col, hg, F, inkw, t, wet):
    st = HAIR[C["head"]["hair"]]
    hcol = col["hair"]
    dy = hg.nod * 6
    if "sides" in st:
        for sd in st["sides"]:
            _hair_path(ctx, hg, sd, "front", st["tension"], dy)
            _fs(ctx, hcol, inkw)
    if "tuft" in st:
        tp = st["tuft"]
        if wet:   # damp hair: the cowlick droops
            tp = [(x + (y + 144) * -0.6, -144 + (y + 144) * 0.25) for x, y in tp]
        _hair_path(ctx, hg, tp, "front", 0.5, dy)
        _fs(ctx, hcol, inkw)
    _hair_path(ctx, hg, st["front"], "front", st["tension"], dy)
    _fs(ctx, hcol, inkw)
    if "front2" in st:
        _hair_path(ctx, hg, st["front2"], "front", st["tension"], dy)
        _fs(ctx, hcol, inkw)
    # strands / sheen
    hl = _lt(hcol, 0.28) if C["head"]["hair"] != "bob" else "#aeb4c3"
    for sline in st["strands"]:
        wp = [hg.warp(x, y + dy, "front") for x, y in sline]
        ctx.move_to(*wp[0])
        for q in wp[1:]:
            ctx.line_to(*q)
        _stroke(ctx, _dk(hcol, 0.45) if C["head"]["hair"] in ("mop", "bun") else hl, inkw * 0.55)
    if wet:
        # drips hanging from the fringe
        for i, (x, y) in enumerate(((-40, -70), (30, -66), (78, -52))):
            ph = (t * 0.7 + i * 0.37) % 1.0
            X, Y = hg.warp(x, y + dy + 10 + ph * 24, "front")
            ctx.new_path()
            _drop(ctx, X, Y, 4.0 * (1 - ph * 0.3), "#a9dff0", inkw * 0.8)


NAPE_Y = {"mop": 48, "part": 30, "cap": 22, "bun": 34, "bob": 74}


def _draw_nape(ctx, C, col, hg, inkw):
    """Hair over the back of the skull in 3/4 views (the back hair sits under the head fill)."""
    ny = NAPE_Y.get(C["head"]["hair"])
    if ny is None or abs(hg.s) < 0.06:
        return
    sb = -1.0 if hg.s > 0 else 1.0
    c, s = hg.c, hg.s
    cd, sd = math.cos(0.16), math.sin(0.16)
    outer, inner = [], []
    ys = (-96, -70, -40, -10, 18, ny)
    for y in ys:
        a, f, b = hg.abf(min(y, 60))
        el, er = hg.ext(a, f, b)
        ext = el if sb < 0 else er
        outer.append((ext + sb * 3, y))
        # just behind the ear line, on the back half of the skull
        inner.append((a * sb * cd * c - b * sd * s, y))
    mess = C["head"]["hair"] == "mop"
    bot = [(lerp(outer[-1][0], inner[-1][0], 0.5) + sb * (4 if mess else 0), ny + (12 if mess else 6))]
    pts = outer + bot + inner[::-1]
    _smooth(ctx, pts, True, 0.45)
    _fs(ctx, _dk(col["hair"], 0.05), inkw)


def _draw_ear(ctx, C, col, hg, sgn, inkw, blush_ear):
    hd = C["head"]
    y0, y1 = hd["ear_y"]
    ym = (y0 + y1) / 2 + hg.nod * 4
    a, f, b = hg.abf(ym)
    X = sgn * a * hg.c - 0.12 * a * hg.s
    Z = -sgn * a * hg.s
    face_k = abs(hg.s) if Z > 0 else 0.0
    rx = hd["ear_w"] * (0.62 + 0.45 * face_k)
    ry = (y1 - y0) * 0.55
    cx = X + sgn * rx * (0.55 - 0.6 * face_k)
    skin = col["skin"] if not blush_ear else mixc(col["skin"], PAL["blush"], blush_ear)
    ellipse(ctx, cx, ym, rx, ry, sgn * 0.12)
    _fs(ctx, skin, inkw)
    ctx.move_to(cx - sgn * rx * 0.1, ym - ry * 0.5)
    _qcurve(ctx, (cx - sgn * rx * 0.1, ym - ry * 0.5), (cx + sgn * rx * 0.55, ym - ry * 0.1),
            (cx, ym + ry * 0.45))
    _stroke(ctx, col["skin_sh"], inkw * 0.8)
    return Z


# ============================================================================
# 7d. FACE: eyes, brows, nose, mouth
# ============================================================================
# eye shape: (inner corner y, outer corner y, top power, bottom power, top k, bottom k)
EYE_SHAPES = {
    "almond": (0.14, -0.06, 0.62, 0.9, 1.05, 0.86),
    "round": (0.04, -0.02, 0.5, 0.55, 1.0, 0.98),
    "cat": (0.24, -0.3, 0.62, 1.0, 1.0, 0.7),
    "small": (0.1, -0.04, 0.6, 0.8, 1.0, 0.9),
}
_EU = (-1.0, -0.93, -0.72, -0.4, 0.0, 0.4, 0.72, 0.93, 1.0)
SCLERA = "#fbfaf7"
MOUTH_IN = "#4a1a2e"
TONGUE = "#e8667e"


def _eye_curves(shape, eh):
    iy, oy, tp, bp, tk, bk = EYE_SHAPES[shape]
    tops, bots = [], []
    for u in _EU:
        yc = lerp(iy, oy, (u + 1) * 0.5) * eh
        w = max(0.0, 1 - u * u)
        tops.append(yc - eh * tk * w ** tp)
        bots.append(yc + eh * bk * w ** bp)
    return tops, bots


def _draw_eye(ctx, C, col, cx, cy, ew, eh, ew0, sgn, E, inkw, power, hs, lashes):
    """One eye. E: lid, lid_ang, lower, pupil, iris, hl, lx, ly, focus, lidshade, bags."""
    shape = C["head"]["eye"]
    tops, bots = _eye_curves(shape, eh)
    L = E["lid"]
    la, lo = E["lid_ang"], E["lower"]
    xs = [cx + sgn * u * ew for u in _EU]
    up, low = [], []
    gap = 0.0
    for i, u in enumerate(_EU):
        t_, b_ = tops[i], bots[i]
        Lu = clamp(L + la * 0.35 * u)
        Lo = clamp(lo * (1 - 0.2 * u * u))
        yu = t_ + (b_ - t_) * Lu
        yl = b_ - (b_ - t_) * Lo * 0.75
        if yu > yl:
            yu = yl
        up.append(yu)
        low.append(yl)
        gap = max(gap, yl - yu)
    ink = PAL["ink"]
    # under-eye bags (Tiredness)
    if E["bags"] > 0.01:
        pts = []
        rng = range(1, 8)
        for i in rng:
            pts.append((xs[i], cy + bots[i] + 3.0))
        for i in reversed(rng):
            w = max(0.0, 1 - _EU[i] ** 2)
            pts.append((xs[i], cy + bots[i] + 3.0 + 8.5 * w ** 0.8 * (eh / 21)))
        _poly(ctx, pts)
        _set(ctx, alpha_ink(col.get("bags", col["skin_sh"]), 0.36 * E["bags"]))
        ctx.fill()
        ctx.move_to(*pts[len(rng)])
        for q in pts[len(rng) + 1:]:
            ctx.line_to(*q)
        _set(ctx, alpha_ink(col.get("bags", col["skin_sh"]), 0.62 * E["bags"]))
        ctx.set_line_width(inkw * 0.5)
        ctx.stroke()
    # heavy lid skin (between the eye contour and the lid edge)
    if L > 0.05 and gap > 1.0 and E["lidshade"] > 0:
        ctx.move_to(xs[0], cy + tops[0])
        for i in range(1, 9):
            ctx.line_to(xs[i], cy + tops[i] - 1.5)
        for i in range(8, -1, -1):
            ctx.line_to(xs[i], cy + up[i])
        ctx.close_path()
        _set(ctx, alpha_ink(col["skin_sh"], E["lidshade"] * clamp(L * 2.5)))
        ctx.fill()
    if gap < 1.2:
        # closed: one lash line along the lid
        if power > 0.02:     # sensing with the eyes closed: teal light along the lash line
            ctx.move_to(xs[1], cy + low[1] + inkw * 0.75)
            for i in range(2, 8):
                ctx.line_to(xs[i], cy + low[i] + inkw * 0.75)
            _set(ctx, alpha_ink(mixc(PAL["power"], "#ffffff", 0.3), 0.9 * clamp(power * 1.4)))
            ctx.set_line_width(inkw * 0.75)
            ctx.stroke()
        ctx.move_to(xs[0], cy + low[0])
        for i in range(1, 9):
            ctx.line_to(xs[i], cy + low[i])
        _set(ctx, ink)
        ctx.set_line_width(inkw * 1.15)
        ctx.stroke()
        if lashes:
            ctx.move_to(xs[8], cy + low[8])
            ctx.line_to(xs[8] + sgn * ew * 0.28, cy + low[8] - eh * 0.22)
            ctx.stroke()
        return
    # aperture
    def ap():
        ctx.move_to(xs[0], cy + up[0])
        for i in range(1, 9):
            ctx.line_to(xs[i], cy + up[i])
        for i in range(8, -1, -1):
            ctx.line_to(xs[i], cy + low[i])
        ctx.close_path()
    ctx.save()
    ap()
    _set(ctx, SCLERA)
    ctx.fill_preserve()
    ctx.clip()
    # iris + pupil
    r0 = min(ew0, eh) * 0.78
    ri = r0 * E["iris"]
    kx = clamp(ew / max(1.0, ew0), 0.3, 1.0)
    ix = cx + E["lx"] * ew * 0.52 + E["yaw"] * ew0 * 0.12
    # Heavy lids (Episode 2): the iris settles toward the middle of the VISIBLE aperture so a
    # level gaze reads as looking straight ahead (not down), and a down gaze keeps the pupil.
    lo_ = E.get("lid_open", L)
    heavy = smoothstep((lo_ - 0.22) / 0.4)
    ly_ = E["ly"]
    if heavy > 0.001:
        edge = tops[4] + (bots[4] - tops[4]) * clamp(lo_)
        lowc = bots[4] - (bots[4] - tops[4]) * clamp(lo) * 0.75
        vis_mid = (edge + lowc) * 0.5
        iy = cy + vis_mid * 0.42 * heavy
        iy += ly_ * eh * ((0.58 * (1 - 0.45 * heavy)) if ly_ > 0 else 0.42)
    else:
        iy = cy + ly_ * eh * (0.58 if ly_ > 0 else 0.42)
    icol = col["iris"]
    if power > 0:
        icol = mixc(icol, PAL["power"], clamp(power * 1.3))
    pr = r0 * 0.5 * E["pupil"] * (1 - 0.3 * power) * (1 + 0.15 * (1 - E["focus"]))
    if ri > 0.5:
        ellipse(ctx, ix, iy, ri * kx, ri)
        _set(ctx, icol)
        ctx.fill_preserve()
        _set(ctx, _dk(icol, 0.45))
        ctx.set_line_width(max(1.5, inkw * 0.42))
        ctx.stroke()
        if power > 0.05:
            ellipse(ctx, ix, iy, ri * kx * 0.72, ri * 0.72)
            _set(ctx, alpha_ink(mixc(PAL["power"], "#ffffff", 0.6), power))
            ctx.set_line_width(max(1.2, ri * 0.16))
            ctx.stroke()
    ellipse(ctx, ix, iy, pr * kx, pr)
    _set(ctx, "#120d18" if power < 0.5 else mixc("#120d18", PAL["hush_dk"], power - 0.5))
    ctx.fill()
    # lid shadow on the eyeball
    ctx.move_to(xs[0], cy + up[0])
    for i in range(1, 9):
        ctx.line_to(xs[i], cy + up[i])
    _set(ctx, (0.55, 0.5, 0.62, 0.17))
    ctx.set_line_width(max(3.0, eh * 0.3))
    ctx.stroke()
    # highlights
    hl = E["hl"]
    if hl > 0.02:
        hr = max(1.6, r0 * 0.3 * hl)
        circle(ctx, ix - r0 * 0.34 * kx, iy - r0 * 0.36, hr)
        _set(ctx, "#ffffff")
        ctx.fill()
        circle(ctx, ix + r0 * 0.3 * kx, iy + r0 * 0.3, max(1.0, hr * 0.42))
        ctx.fill()
    tr = E.get("tears", 0.0)
    if tr > 0.01:            # wet glisten pooling on the lower lid
        ctx.move_to(xs[1], cy + low[1] - 1.5)
        for i in range(2, 8):
            ctx.line_to(xs[i], cy + low[i] - eh * 0.1 - 1.0)
        _set(ctx, (0.86, 0.97, 1.0, 0.85 * clamp(tr * 1.5)))
        ctx.set_line_width(max(2.0, eh * 0.2))
        ctx.stroke()
        circle(ctx, xs[5], cy + low[5] - eh * 0.16, max(1.4, eh * 0.09))
        _set(ctx, (1, 1, 1, clamp(tr * 2)))
        ctx.fill()
    ctx.restore()
    # lash line + lower line
    ctx.move_to(xs[0], cy + up[0])
    for i in range(1, 9):
        ctx.line_to(xs[i], cy + up[i])
    _set(ctx, ink)
    ctx.set_line_width(inkw * 1.2)
    ctx.stroke()
    ctx.move_to(xs[1], cy + low[1])
    for i in range(2, 8):
        ctx.line_to(xs[i], cy + low[i])
    ctx.set_line_width(inkw * 0.55)
    ctx.stroke()
    if lashes:
        ctx.move_to(xs[8], cy + up[8])
        ctx.line_to(xs[8] + sgn * ew * 0.3, cy + up[8] - eh * 0.3)
        ctx.set_line_width(inkw * 0.9)
        ctx.stroke()
    # crease above a heavy lid
    if L > 0.12:
        ctx.move_to(xs[1], cy + tops[1] - 2)
        for i in range(2, 8):
            ctx.line_to(xs[i], cy + tops[i] - 2.5)
        _set(ctx, alpha_ink(ink, 0.75))
        ctx.set_line_width(inkw * 0.55)
        ctx.stroke()


def _draw_tear(ctx, Ev, sgn, k, inkw):
    """A single tear: wells at the outer lower lid, then rolls down the cheek (k 0..1)."""
    X, Y, ew, eh, kk, E = Ev
    k = clamp(k)
    x0 = X + sgn * ew * 0.55
    y0 = Y + eh * 0.85
    yy = y0 + smoothstep(clamp((k - 0.25) / 0.75)) * eh * 2.6
    xx = x0 + sgn * (yy - y0) * 0.08
    r = eh * (0.16 + 0.12 * smoothstep(k / 0.4))
    if yy - y0 > 2:           # wet trail
        ctx.move_to(x0, y0)
        _qcurve(ctx, (x0, y0), (x0 + sgn * 1.5, (y0 + yy) / 2), (xx, yy - r))
        _stroke(ctx, (0.86, 0.96, 1.0, 0.75), max(1.6, r * 0.6))
    _drop(ctx, xx, yy, r, "#cdeeff", inkw * 0.8)


def _draw_brow(ctx, cx, ytop, ew, sgn, B, color, th, blen, outline, inkw):
    """Tapered brow. B: brow, brow_ang, brow_in, brow_out."""
    br, ba, bi, bo = B
    y_in = -br * 20 - ba * 16 - bi * 4
    y_out = -br * 20 + ba * 9 - bo * 9
    arch = 5.5
    top, bot = [], []
    n = 7
    for j in range(n):
        v = j / (n - 1)
        x = cx + sgn * (-0.95 + 2.05 * v) * ew * blen
        y = ytop + lerp(y_in, y_out, v) - arch * 4 * v * (1 - v)
        y -= bi * 9 * max(0.0, 1 - v / 0.45) ** 2
        y -= bo * 7 * max(0.0, (v - 0.55) / 0.45) ** 2
        w = th * (1.0 - 0.5 * v ** 1.6) * (0.82 + 0.18 * math.sin(math.pi * min(1.0, v * 1.4)))
        top.append((x, y - w / 2))
        bot.append((x, y + w / 2))
    pts = top + bot[::-1]
    _smooth(ctx, pts, True, 0.4)
    if outline:
        _fs(ctx, color, inkw * 0.45)
    else:
        _fill(ctx, color)


def _draw_nose(ctx, C, col, hg, F, inkw):
    hd = C["head"]
    st = hd["nose"]
    ny = hd["nose_y"] + hg.nod * 9
    s = hg.s
    nl = {"soft": 20, "point": 26, "sharp": 24, "broad": 18}[st]
    nw = {"soft": 15, "point": 11, "sharp": 9, "broad": 19}[st] * (1 + F["flare"] * 0.22)
    tipX, _, _ = hg.proj(0, ny, nl)
    brX, _, _ = hg.proj(0, ny - 30, 2)
    wl, _, kl = hg.proj(-nw, ny + 3, nl * 0.25)
    wr, _, kr = hg.proj(nw, ny + 3, nl * 0.25)
    ink = PAL["ink"]
    ty = ny + (4 if st == "sharp" else 0)
    sd = 1 if s >= 0 else -1
    # side silhouette (shows more as the head turns)
    if abs(s) > 0.12:
        near_w = wl if sd > 0 else wr
        pts = [(brX, ny - 30), (tipX + sd * 3, ty - 2), (tipX, ty + 6), (near_w, ny + 7)]
        _poly(ctx, pts)
        _set(ctx, col["skin"])
        ctx.fill()
        ctx.move_to(brX, ny - 30)
        ctx.curve_to(brX + sd * 2, ny - 14, tipX + sd * 4, ty - 8, tipX + sd * 2, ty + 1)
        ctx.curve_to(tipX, ty + 7, tipX - sd * 6, ty + 8, tipX - sd * 10, ty + 6)
        _stroke(ctx, ink, inkw * 0.9)
    else:
        # front: short shadow-side stroke + bottom curve
        if st == "sharp":
            ctx.move_to(tipX + 3, ny - 28)
            ctx.curve_to(tipX + 5, ny - 14, tipX + 6, ty - 4, tipX + 1, ty + 2)
            _stroke(ctx, alpha_ink(ink, 0.8), inkw * 0.6)
        else:
            ctx.move_to(tipX + nw * 0.55, ny - 12)
            ctx.curve_to(tipX + nw * 0.8, ny - 4, tipX + nw * 0.85, ny + 2, tipX + nw * 0.5, ny + 6)
            _stroke(ctx, alpha_ink(col["skin_sh"], 1.0), inkw * 0.8)
    # bottom curve with nostril wings
    ctx.move_to(wl, ny + 2)
    ctx.curve_to(wl + (tipX - wl) * 0.3, ny + 10, tipX - 4, ty + 9, tipX, ty + 8)
    ctx.curve_to(tipX + 4, ty + 9, wr - (wr - tipX) * 0.3, ny + 10, wr, ny + 2)
    _stroke(ctx, ink, inkw * (0.85 if st != "sharp" else 0.6))
    if st in ("broad", "soft") or F["flare"] > 0.1:
        fr = 1.8 + F["flare"] * 2.2
        for xw, kk in ((wl, kl), (wr, kr)):
            if kk > 0.3:
                ellipse(ctx, xw + (tipX - xw) * 0.35, ny + 6, fr * 1.4 * kk, fr)
                _fill(ctx, alpha_ink(ink, 0.7))
    return (tipX, ty)


def _draw_mouth(ctx, C, col, hg, F, inkw, t, opn, wide):
    hd = C["head"]
    my = hd["mouth_y"] + hg.nod * 10
    jaw = F["jaw"] * 9
    curve, asym, smirk, press = F["curve"], F["asym"], F["smirk"], F["press"]
    frown, wob = F["frown"], F["wobble"]
    mw = hd["mw"] * F["width"] * (1 + 0.24 * wide) * (1 - 0.18 * press) * (1 - 0.25 * max(0.0, -wide) * opn)
    mw = max(4.0, mw)
    lift = {}
    for sgn in (-1, 1):
        lf = curve * 11 + asym * sgn * 6 - frown * 8
        if smirk * sgn > 0:
            lf += abs(smirk) * 12
        else:
            lf -= abs(smirk) * 2
        lift[sgn] = lf
    Lx, _, _ = hg.proj(-mw + jaw, my)
    Rx, _, _ = hg.proj(mw + jaw, my)
    Mx, _, _ = hg.proj(jaw, my)
    Ly, Ry = my - lift[-1], my - lift[1]
    ink = PAL["ink"]
    teeth = F["teeth"]
    grin = teeth > 0.5 and opn < 0.32
    o = max(opn, 0.16 * teeth if grin else 0.0)
    lipc = col.get("lip")
    if o < 0.045:
        # ---------------- closed mouth
        mid_y = (Ly + Ry) / 2 + curve * 4.5 - press * 1.0 + frown * 1.5
        n = 9
        pts = []
        for j in range(n):
            v = j / (n - 1)
            x = Lx + (Rx - Lx) * v
            if v <= 0.5:
                y = _bez1(Ly, mid_y, v * 2)
            else:
                y = _bez1(mid_y, Ry, v * 2 - 1, rev=True)
            if wob > 0:
                y += wob * 2.6 * math.sin(v * math.pi * 4 + t * 9) * math.sin(v * math.pi)
            pts.append((x, y))
        if lipc:
            th = 4.5 * (1 - press * 0.6)
            up = [(x, y - th * math.sin(math.pi * (j / (n - 1))) ** 0.6) for j, (x, y) in enumerate(pts)]
            dn = [(x, y + th * 1.25 * math.sin(math.pi * (j / (n - 1))) ** 0.6) for j, (x, y) in enumerate(pts)]
            _poly(ctx, up + dn[::-1])
            _fill(ctx, lipc)
        ctx.move_to(*pts[0])
        for q in pts[1:]:
            ctx.line_to(*q)
        _set(ctx, ink)
        ctx.set_line_width(inkw * (1.0 + 0.1 * press))
        ctx.stroke()
        # corner ticks: smile dimples / press tension
        for sgn, (cx_, cy_) in ((-1, pts[0]), (1, pts[-1])):
            lf = lift[sgn]
            if lf > 5:          # smile dimple curling up
                ctx.move_to(cx_ - sgn * 1.5, cy_ + 1.5)
                _qcurve(ctx, (cx_ - sgn * 1.5, cy_ + 1.5), (cx_ + sgn * 5, cy_), (cx_ + sgn * 4, cy_ - 6))
                ctx.set_line_width(inkw * 0.6)
                ctx.stroke()
            elif press > 0.3:   # pressed-lip tension marks
                ctx.move_to(cx_ + sgn * 1.5, cy_ - 3.5)
                _qcurve(ctx, (cx_ + sgn * 1.5, cy_ - 3.5), (cx_ + sgn * 4.5, cy_), (cx_ + sgn * 2.5, cy_ + 3.5))
                _set(ctx, alpha_ink(ink, 0.8))
                ctx.set_line_width(inkw * 0.55)
                ctx.stroke()
                _set(ctx, ink)
        if press > 0.25 or frown > 0.2:
            ctx.move_to(Mx - mw * 0.32, my + 10 + frown * 3)
            _qcurve(ctx, (Mx - mw * 0.32, my + 10 + frown * 3), (Mx, my + 14 + frown * 4),
                    (Mx + mw * 0.32, my + 10 + frown * 3))
            _set(ctx, alpha_ink(ink, 0.55))
            ctx.set_line_width(inkw * 0.55)
            ctx.stroke()
        return (Mx, my)
    # ---------------- open mouth
    H = 44 * o
    up_mid = (Ly + Ry) / 2 + curve * 3 - F["lip_up"] * 9 - o * 5
    lo_mid = up_mid + max(3.0, H) + max(0.0, curve) * 10 + F["lip_low"] * 6
    rnd = clamp(-wide) * 0.5 + (0.25 if F["width"] < 0.85 else 0.0)
    q = 0.55 + rnd * 0.25
    def path():
        ctx.move_to(Lx, Ly)
        ctx.curve_to(Lx + (Mx - Lx) * q * 0.8, up_mid - (Ly - up_mid) * 0.15 - rnd * 4,
                     Mx - (Mx - Lx) * 0.35, up_mid, Mx, up_mid)
        ctx.curve_to(Mx + (Rx - Mx) * 0.35, up_mid, Rx - (Rx - Mx) * q * 0.8,
                     up_mid - (Ry - up_mid) * 0.15 - rnd * 4, Rx, Ry)
        ctx.curve_to(Rx - (Rx - Mx) * 0.05, Ry + (lo_mid - Ry) * (0.75 + rnd * 0.2),
                     Mx + (Rx - Mx) * 0.55, lo_mid, Mx, lo_mid)
        ctx.curve_to(Mx - (Mx - Lx) * 0.55, lo_mid, Lx + (Mx - Lx) * 0.05,
                     Ly + (lo_mid - Ly) * (0.75 + rnd * 0.2), Lx, Ly)
        ctx.close_path()
    if wob > 0:
        dyw = wob * 1.8 * math.sin(t * 11)
        up_mid += dyw
    ctx.save()
    path()
    _set(ctx, MOUTH_IN)
    ctx.fill_preserve()
    ctx.clip()
    if F["tongue"] > 0.02 and not grin:
        ellipse(ctx, Mx + jaw * 0.4, lo_mid - 2, (Rx - Lx) * 0.3, max(4.0, (lo_mid - up_mid) * 0.38 * F["tongue"]))
        _fill(ctx, TONGUE)
    if teeth > 0.02:
        if grin:
            _set(ctx, "#ffffff")
            ctx.paint()
            midy = (up_mid + lo_mid) / 2 + 1
            ctx.move_to(Lx, (Ly + midy) / 2)
            ctx.curve_to(Lx + (Mx - Lx) * 0.5, midy, Mx - 8, midy, Mx, midy)
            ctx.curve_to(Mx + 8, midy, Rx - (Rx - Mx) * 0.5, midy, Rx, (Ry + midy) / 2)
            _stroke(ctx, alpha_ink(ink, 0.7), inkw * 0.5)
            for v in (-0.5, -0.17, 0.17, 0.5):
                xx = Mx + v * (Rx - Lx)
                ctx.move_to(xx, up_mid - 6)
                ctx.line_to(xx, lo_mid + 6)
            _stroke(ctx, alpha_ink(ink, 0.35), inkw * 0.4)
        else:
            th_ = min(10.0, (lo_mid - up_mid) * 0.32) * clamp(teeth * 1.5)
            ctx.rectangle(Lx - 5, up_mid - 30, Rx - Lx + 10, 30 + th_)
            _fill(ctx, "#ffffff")
            if teeth > 0.75 and o > 0.3:
                ctx.rectangle(Lx - 5, lo_mid - th_ * 0.9, Rx - Lx + 10, 40)
                _fill(ctx, "#ffffff")
    ctx.restore()
    path()
    if lipc:
        _stroke(ctx, lipc, inkw * 1.6)
        path()
    _stroke(ctx, ink, inkw * 0.95)
    return (Mx, (up_mid + lo_mid) / 2)


def _bez1(a, b, v, rev=False):
    """Ease between corner height a and mid height b (smile-shaped)."""
    if rev:
        k = 1 - (1 - v) ** 2
        k = v * v
        return a + (b - a) * k
    k = 1 - (1 - v) ** 2
    return a + (b - a) * k


# ============================================================================
# 7e. FACE resolve + head orchestration + accessories
# ============================================================================
_MULT_KEYS = ("pupil", "iris", "hl", "eye_size", "width", "focus")


def _key0(k):
    return k[:-2] if k.endswith("_l") or k.endswith("_r") else k


def _expr_dict(expr, who):
    """Expression (name | dict | (a, b, k)) -> dict of deltas (gain + char tweaks applied)."""
    if isinstance(expr, (tuple, list)) and len(expr) == 3:
        a, b = _expr_dict(expr[0], who), _expr_dict(expr[1], who)
        k = clamp(float(expr[2]))
        out = {}
        for key in set(a) | set(b):
            va, vb = a.get(key, 0.0), b.get(key, 0.0)
            if isinstance(va, tuple) or isinstance(vb, tuple):
                va = va if isinstance(va, tuple) else (0.0, 0.0)
                vb = vb if isinstance(vb, tuple) else (0.0, 0.0)
                out[key] = (va[0] + (vb[0] - va[0]) * k, va[1] + (vb[1] - va[1]) * k)
            else:
                out[key] = va + (vb - va) * k
        return out
    if isinstance(expr, dict):
        src, name = expr, None
    else:
        if expr not in EXPR:
            raise KeyError(f"human: unknown expression {expr!r}")
        src, name = EXPR[expr], expr
    gain = EXPR_GAIN.get(who, {})
    out = {}
    for k, v in src.items():
        if isinstance(v, (tuple, list)):
            out[k] = tuple(v)
            continue
        k0 = _key0(k)
        d = v - 1.0 if k0 in _MULT_KEYS and k == k0 else v
        g = gain.get(k0 + "-", None) if d < 0 else None
        if g is None:
            g = gain.get(k0, gain.get("*", 1.0))
        out[k] = d * g
    if name:
        for k, v in CHAR_EXPR.get(who, {}).get(name, {}).items():
            out[k] = out.get(k, 0.0) + v
    return out


def resolve_face(who, expr="neutral", face=None):
    """Final additive face params (before blink/look/lip-sync)."""
    C = CHARS[who]
    F = dict(FACE_DEFAULTS)
    for src in (C["face"], _expr_dict(expr, who), face or {}):
        for k, v in src.items():
            if isinstance(v, (tuple, list)):
                old = F.get(k)
                F[k] = (old[0] + v[0], old[1] + v[1]) if isinstance(old, tuple) else (float(v[0]), float(v[1]))
            else:
                F[k] = F.get(k, 0.0) + v
    return F


# Gaze-driven lid follow (Episode 2 fix): looking down drops the upper lids, but the
# droop is capped so heavy-lidded characters keep their irises visible.
#   who -> (down gain, up gain, closure cap for the down droop)
GAZE_LID = {"tired": (0.22, 0.22, 0.6), "boss": (0.2, 0.26, 0.64)}
GAZE_LID_DEFAULT = (0.22, 0.3, 0.66)


def _eye_params(F, side, blink, look, drift, who=None):
    g = lambda k: F.get(k, 0.0) + F.get(k + "_" + side, 0.0)
    lx = look[0] + g("look_x") + drift[0]
    ly = look[1] + g("look_y") + drift[1]
    lk = F.get("look_" + side)
    if isinstance(lk, tuple):
        lx += lk[0]
        ly += lk[1]
    lx, ly = clamp(lx, -1.25, 1.25), clamp(ly, -1.25, 1.25)
    dn_gain, up_gain, cap = GAZE_LID.get(who, GAZE_LID_DEFAULT)
    lid0 = g("lid")
    droop = dn_gain * max(0.0, ly)
    room = max(0.0, cap - max(0.0, lid0))
    if room > 1e-4:        # soft cap: approaches `cap`, never passes it
        droop = room * math.tanh(droop / room)
    else:
        droop = 0.0
    lid = lid0 + droop - up_gain * max(0.0, -ly)
    wide = max(0.0, -lid)
    lid = clamp(lid)
    lid_open = lid                      # lid without the blink (for iris placement)
    lid = lid + (1 - lid) * blink
    return dict(lid=lid, lid_open=lid_open, wide=wide * (1 - blink), lid_ang=g("lid_ang"),
                lower=clamp(g("lower")),
                pupil=max(0.15, g("pupil")), iris=max(0.0, g("iris")), hl=max(0.0, g("hl")),
                eye_size=max(0.5, g("eye_size")), lx=lx, ly=ly, focus=clamp(F["focus"]),
                brow=(g("brow"), g("brow_ang"), g("brow_in"), g("brow_out")),
                lidshade=F["lidshade"], bags=F["bags"], blink=blink)


def _head_xf(J, C, F):
    """(cx, cy, tilt, sx, sy, yc) head-local -> rig-local transform parameters."""
    h = J["head"]
    sq = F["squash"]
    return h["cx"], h["cy"], h["tilt"], 1 + sq * 0.6, 1 - sq, C["head"]["chin"] * 0.55


def _hmap(xf, x, y):
    cx, cy, tl, sx, sy, yc = xf
    px, py = x * sx, yc + (y - yc) * sy
    rx, ry = _rot(px, py, tl)
    return (cx + rx, cy + ry)


def _enter_head(ctx, xf):
    cx, cy, tl, sx, sy, yc = xf
    ctx.save()
    ctx.translate(cx, cy)
    if tl:
        ctx.rotate(tl)
    if sx != 1 or sy != 1:
        ctx.translate(0, yc)
        ctx.scale(sx, sy)
        ctx.translate(0, -yc)


def _draw_head(ctx, C, col, J, F, inkw, t, st):
    """Face + hair + head accessories. st: dict of runtime state. Returns head-local anchors."""
    hd = C["head"]
    opn = st["open"]
    hg = _HG(C, J, F, opn)
    st["hg"] = hg
    blush = st["blush"]
    out = {}
    xf = st["xf"]
    _enter_head(ctx, xf)
    # ---- ears behind / head shape
    ear_bl = clamp((blush - 0.65) / 0.3) * 0.6
    zs = {}
    for sgn in (-1, 1):
        Z = -sgn * 100 * hg.s
        if Z < 30:
            _draw_ear(ctx, C, col, hg, sgn, inkw, ear_bl)
        zs[sgn] = Z
    outl = hg.outline()
    skin = col["skin"]
    ctx.save()
    _smooth(ctx, outl, True, 0.55)
    ctx.clip_preserve()
    _set(ctx, col["skin_sh"])
    ctx.fill()
    ctx.translate(-9, -7)
    _smooth(ctx, outl, True, 0.55)
    _set(ctx, skin)
    ctx.fill()
    ctx.translate(9, 7)
    # blush layers
    if blush > 0.01:
        a_face = smoothstep((blush - 0.3) / 0.4) * 0.38 + smoothstep((blush - 0.7) / 0.3) * 0.26
        if a_face > 0.005:
            _smooth(ctx, outl, True, 0.55)
            _set(ctx, alpha_ink(PAL["blush"], a_face))
            ctx.fill()
        a_ch = clamp(blush / 0.3) * 0.5 + clamp((blush - 0.3) / 0.7) * 0.25
        for sgn in (-1, 1):
            cyb = hd.get("cheek_y", 30) + hg.nod * 8
            X, Z, k = hg.proj(sgn * (hd["ex"] + hd.get("cheek_dx", 8)), cyb)
            if k > 0.2:
                ellipse(ctx, X, cyb, 24 * k, 13)
                _set(ctx, alpha_ink(PAL["blush"], a_ch * min(1.0, k * 1.4)))
                ctx.fill()
    ctx.restore()
    _smooth(ctx, outl, True, 0.55)
    _stroke(ctx, PAL["ink"], inkw)
    _draw_nape(ctx, C, col, hg, inkw)
    for sgn in (-1, 1):
        if zs[sgn] >= 30:
            _draw_ear(ctx, C, col, hg, sgn, inkw, ear_bl)
    # ---- skin marks
    if hd.get("glasses"):     # freckles
        for sgn in (-1, 1):
            for j, (fx_, fy_) in enumerate(((30, 24), (40, 30), (50, 23), (38, 18))):
                X, Z, k = hg.proj(sgn * fx_, fy_ + hg.nod * 8)
                if k > 0.3:
                    circle(ctx, X, fy_ + hg.nod * 8, 2.0)
                    _fill(ctx, alpha_ink(_dk(col["skin_sh"], 0.15), 0.8))
    # ---- eyes
    ey = hg.nod * 8
    look, drift, blink = st["look"], st["drift"], st["blink"]
    for side, sgn in (("l", -1), ("r", 1)):
        E = _eye_params(F, side, blink, look, drift, C.get("_who"))
        X, Z, k = hg.proj(sgn * hd["ex"], ey)
        ew0 = hd["ew"] * E["eye_size"]
        eh = hd["eh"] * E["eye_size"] * (1 + 0.42 * E["wide"])
        ew = ew0 * k * (1 + 0.12 * E["wide"])
        E["yaw"] = hg.s
        E["tears"] = st.get("tears", 0.0)
        if E["tears"] > 0:
            E["hl"] += 0.45 * E["tears"]
        out["eye_" + side] = (X, ey)
        if k > 0.1:
            _draw_eye(ctx, C, col, X, ey, ew, eh, ew0, sgn, E, inkw, st["power"], 1.0,
                      C.get("sex") == "f")
        st["E_" + side] = (X, ey, ew, eh, k, E)
    st["brow_lift"] = (max(0.0, st["E_l"][5]["brow"][0]), max(0.0, st["E_r"][5]["brow"][0]))
    if st.get("tears", 0.0) > 0.7:
        side = "l" if st["E_l"][4] > st["E_r"][4] else "r"
        _draw_tear(ctx, st["E_" + side], -1 if side == "l" else 1, (st["tears"] - 0.7) / 0.3, inkw)
    # ---- nose, mouth, mustache
    out["nose"] = _draw_nose(ctx, C, col, hg, F, inkw)
    out["mouth"] = _draw_mouth(ctx, C, col, hg, F, inkw, t, opn, st["wide"])
    if hd.get("mustache"):
        my = hd["mouth_y"] + hg.nod * 10 - 11
        pts = []
        for xf_, yy in ((-34, 6), (-28, -4), (-12, -8), (0, -5), (12, -8), (28, -4), (34, 6), (16, 2),
                        (0, 4), (-16, 2)):
            X, _, _ = hg.proj(xf_, my + yy)
            pts.append((X, my + yy))
        _smooth(ctx, pts, True, 0.5)
        _fs(ctx, col["hair"], inkw * 0.7)
    if hd["nose"] == "sharp":      # cheekbone shading lines
        for sgn in (-1, 1):
            X0, _, k0 = hg.proj(sgn * 62, 30 + hg.nod * 8)
            X1, _, k1 = hg.proj(sgn * 76, 46 + hg.nod * 8)
            if min(k0, k1) > 0.3:
                ctx.move_to(X0, 30 + hg.nod * 8)
                ctx.line_to(X1, 46 + hg.nod * 8)
                _stroke(ctx, alpha_ink(col["skin_sh"], 0.9), inkw * 0.55)
    # ---- outfit marks (sewer)
    if st.get("wet"):
        for (xf_, yy, ang) in ((-50, 44, 0.5), ):
            X, _, k = hg.proj(xf_, yy + hg.nod * 8)
            if k > 0.25:
                _bandaid(ctx, X, yy + hg.nod * 8, ang, 1.0, inkw)
        for (xf_, yy, r) in ((55, 50, 9), (-28, -62, 7)):
            X, _, k = hg.proj(xf_, yy)
            if k > 0.25:
                ellipse(ctx, X, yy, r * 1.4 * k, r)
                _fill(ctx, (0.25, 0.32, 0.22, 0.35))
    # ---- hair
    _draw_front_hair(ctx, C, col, hg, F, inkw, t, st.get("wet"))
    if st.get("wet"):
        X, _, k = hg.proj(-58, -88)
        _bandaid(ctx, X, -88, -0.35, 0.85, inkw)
    # ---- brows (over the fringe)
    for side, sgn in (("l", -1), ("r", 1)):
        X, Y, ew, eh, k, E = st["E_" + side]
        if k > 0.12:
            ytop = hd["brow_y"] + hg.nod * 7 - (eh - hd["eh"]) * 0.6
            _draw_brow(ctx, X, ytop, hd["ew"] * k, sgn, E["brow"], col["brow"], hd["brow_th"],
                       hd["brow_len"], C["head"]["hair"] in ("bob", "part"), inkw)
    # ---- glasses
    if hd.get("glasses"):
        _draw_glasses(ctx, C, hg, st, inkw, t)
    if hd["hair"] == "cap":
        _draw_cap(ctx, C, col, hg, inkw)
    if hd["hair"] == "bun":
        _draw_headset(ctx, C, hg, inkw, out)
    if st.get("hood", 0.0) > 0.0:
        _hood_front(ctx, C, col, hg, st, inkw)
    # ---- sweat / heat
    if st["sweat"] > 0.01:
        _draw_sweat(ctx, C, hg, st["sweat"], t, inkw)
    if blush > 0.85:
        _draw_heat(ctx, hg, clamp((blush - 0.85) / 0.15), t, inkw)
    top_y = min(y for _, y in HAIR[hd["hair"]]["back"] + HAIR[hd["hair"]]["front"]
                + HAIR[hd["hair"]].get("tuft", []))
    if hd["hair"] == "cap":
        top_y = -160
    if hd["hair"] == "bun":
        top_y = -184
    out["top"] = (hg.warp(0, top_y)[0], top_y)
    out["face"] = (hg.proj(0, 20)[0], 20)
    ctx.restore()
    return out


def _bandaid(ctx, x, y, ang, k, inkw):
    with _Saved(ctx, x, y, ang, k):
        ctx.new_path()
        _capsule(ctx, -20, 0, 7.5, 20, 0, 7.5)
        _fs(ctx, "#f0c49a", inkw * 0.55)
        ctx.rectangle(-6, -6, 12, 12)
        _fill(ctx, "#f8e2c8")
        for dx in (-3, 3):
            for dy in (-3, 3):
                circle(ctx, dx, dy, 0.9)
                _fill(ctx, "#c99a74")


class _Saved:
    def __init__(self, ctx, x, y, rot=0.0, sc=1.0):
        self.c, self.a = ctx, (x, y, rot, sc)

    def __enter__(self):
        x, y, r, s = self.a
        self.c.save()
        self.c.translate(x, y)
        if r:
            self.c.rotate(r)
        if s != 1:
            self.c.scale(s, s)

    def __exit__(self, *a):
        self.c.restore()


def _draw_glasses(ctx, C, hg, st, inkw, t):
    hd = C["head"]
    gcol = PAL["glasses"]
    R = hd["eh"] * 1.55
    lens = {}
    for side, sgn in (("l", -1), ("r", 1)):
        X, Y, ew, eh, k, E = st["E_" + side]
        rx = R * clamp(k * 1.05, 0.12, 1.0)
        lens[side] = (X, Y, rx, R, k)
    # askew glasses (Episode 2): rotate the frame about the bridge, sag a little, offset.
    gt = st.get("gtilt", 0.0)
    gdx, gdy = st.get("gdx", 0.0), st.get("gdy", 0.0) + 12.0 * abs(gt)
    (Xl0, Yl0, _, _, _), (Xr0, Yr0, _, _, _) = lens["l"], lens["r"]
    pvx, pvy = (Xl0 + Xr0) / 2, (Yl0 + Yr0) / 2
    cg, sg = math.cos(gt), math.sin(gt)

    def G(x, y):
        dx_, dy_ = x - pvx, y - pvy
        return (pvx + dx_ * cg - dy_ * sg + gdx, pvy + dx_ * sg + dy_ * cg + gdy)
    if gt or gdx or gdy:
        for side in ("l", "r"):
            X, Y, rx, R_, k = lens[side]
            X, Y = G(X, Y)
            lens[side] = (X, Y, rx, R_, k)
    # temples to the ears (only the visible near/side pieces); the ear end stays put
    for side, sgn in (("l", -1), ("r", 1)):
        X, Y, rx, R_, k = lens[side]
        a, f, b = hg.abf(0)
        ex = sgn * a * hg.c - 0.12 * a * hg.s
        Z = -sgn * a * hg.s
        if Z > -60:
            ctx.move_to(X + sgn * rx * 0.95 * cg + R_ * 0.25 * sg, Y - R_ * 0.25 * cg + sgn * rx * 0.95 * sg)
            ctx.line_to(ex, -4)
            _stroke(ctx, gcol, inkw * 0.9)
    # bridge
    (Xl, Yl, rxl, _, _), (Xr, Yr, rxr, _, _) = lens["l"], lens["r"]
    bx = (Xl + rxl + Xr - rxr) / 2
    by_ = (Yl + Yr) / 2
    p0 = (Xl + rxl * 0.96 * cg + R * 0.2 * sg, Yl - R * 0.2 * cg + rxl * 0.96 * sg)
    p1 = (Xr - rxr * 0.96 * cg + R * 0.2 * sg, Yr - R * 0.2 * cg - rxr * 0.96 * sg)
    ctx.move_to(*p0)
    _qcurve(ctx, p0, (bx + R * 0.5 * sg, by_ - R * 0.5 * cg), p1)
    _stroke(ctx, gcol, inkw * 1.05)
    glint = st.get("glint", 0.0)
    for side in ("l", "r"):
        X, Y, rx, R_, k = lens[side]
        if k < 0.1:
            continue
        if gt:
            ctx.save()
            ctx.translate(X, Y)
            ctx.rotate(gt)
            ctx.translate(-X, -Y)
        ellipse(ctx, X, Y, rx, R_)
        _set(ctx, (0.82, 0.92, 1.0, 0.16))
        ctx.fill_preserve()
        _set(ctx, gcol)
        ctx.set_line_width(inkw * 1.25)
        ctx.stroke()
        # glints
        for (x0, y0, x1, y1, w) in ((-0.62, -0.12, -0.28, -0.58, 0.15), (-0.72, 0.22, -0.62, 0.08, 0.08)):
            ctx.move_to(X + rx * x0, Y + R_ * y0)
            ctx.line_to(X + rx * x1, Y + R_ * y1)
            _stroke(ctx, (1, 1, 1, 0.78), max(2.0, R_ * w))
        if glint > 0:
            ellipse(ctx, X, Y, rx, R_)
            _set(ctx, (1, 1, 1, 0.6 * glint))
            ctx.fill()
        if gt:
            ctx.restore()


# ---------------------------------------------------------------------------
# Tiredness's hood (Episode 2): hood 0 = down behind the neck, 1 = up and low over the eyes
# ---------------------------------------------------------------------------
# Front-view outline of the raised hood (head-local, right half, bottom -> crown).
_HOOD_OUT = ((84, 118), (101, 84), (117, 44), (128, 0), (134, -46), (132, -92), (118, -134), (90, -168),
             (48, -191), (0, -200))
# Back shell (behind the head) in the lump's point order, see _hood_back.
_HOOD_BACK = ((-100, 86), (-133, 0), (-134, -92), (-94, -170), (0, -205), (94, -170), (134, -92),
              (133, 0), (100, 86), (62, 130), (0, 142), (-62, 130))


def _hood_map(hg, x, y, dz=0.0, hang=False):
    """Front-view hood point -> turned head-local point (like hg.warp, true widths below the
    eye line unless hang=True: the hood's sides hang straight from the cheeks)."""
    yy = min(y, 0.0) if hang else y
    a, f, b = hg.abf(clamp(yy, hg.lv[0][0] + 2, hg.lv[-1][0]))
    a = max(a, 40.0)
    el, er = hg.ext(a, f, b)
    u = x / a
    side = er if u >= 0 else -el
    if abs(u) >= 1.0:
        return (u * side, y)
    Xi = a * u * hg.c + (f * math.sqrt(1 - u * u) + dz) * hg.s
    w = smoothstep((abs(u) - 0.55) / 0.45)
    return (Xi + (u * side - Xi) * w, y)


def _hood_scale(C):
    return C["head"]["levels"][4][1] / 101.0


def _hood_rim(C, u, nod):
    """Rim centre y (head-local) and the eye-cover amount for hood state u."""
    v = clamp((u - 0.4) / 0.6)
    hd = C["head"]
    end = hd["eh"] * 0.86 + 9 + nod * 8
    yr = lerp(-152.0 * _hood_scale(C), end, smoothstep(v))
    eye_top = nod * 8 - hd["eh"] * 1.1
    cover = clamp((yr - eye_top) / (end - eye_top)) if v > 0 else 0.0
    return yr, v, cover


def _cr_mid(p0, p1, p2, p3, tension=0.55):
    """Point halfway along the smooth_path bezier segment p1 -> p2."""
    c1 = (p1[0] + (p2[0] - p0[0]) * tension / 3, p1[1] + (p2[1] - p0[1]) * tension / 3)
    c2 = (p2[0] - (p3[0] - p1[0]) * tension / 3, p2[1] - (p3[1] - p1[1]) * tension / 3)
    return ((p1[0] + 3 * c1[0] + 3 * c2[0] + p2[0]) / 8, (p1[1] + 3 * c1[1] + 3 * c2[1] + p2[1]) / 8)


def _hinv(xf, X, Y):
    """Rig-local point -> head-local (inverse of _hmap)."""
    cx, cy, tl, sx, sy, yc = xf
    rx, ry = _rot(X - cx, Y - cy, -tl)
    return (rx / sx, yc + (ry - yc) / sy)


def _lump_pts(C, J):
    nk = J["nodes"]["nck"]
    lv = J["_lv"]
    n, t = lv["shoulder"]["n"], lv["shoulder"]["t"]
    s = math.sin(J["phi"])
    cx = nk[0] - n[0] * s * 22
    cy = nk[1] - n[1] * s * 22
    w = C["neck_r"] * 2.5
    return [(cx - n[0] * w + t[0] * -14, cy - n[1] * w - t[1] * 14),
            (cx - n[0] * w * 0.8 + t[0] * 26, cy - n[1] * w * 0.8 + t[1] * 26),
            (cx + t[0] * 36, cy + t[1] * 36),
            (cx + n[0] * w * 0.8 + t[0] * 26, cy + n[1] * w * 0.8 + t[1] * 26),
            (cx + n[0] * w + t[0] * -14, cy + n[1] * w - t[1] * 14),
            (cx, cy - t[1] * 10)]


def _hood_back(ctx, C, col, J, xf, hg, u, inkw):
    """Hood behind the head: grows from the neck lump (u=0) to a shell around the skull."""
    lp = _lump_pts(C, J)
    n = len(lp)
    lump12 = []
    for i in range(n):
        lump12.append(lp[i])
        lump12.append(_cr_mid(lp[i - 1], lp[i], lp[(i + 1) % n], lp[(i + 2) % n]))
    lump12 = [_hinv(xf, *p) for p in lump12]
    e = smoothstep(u / 0.5)
    sc = _hood_scale(C)
    bulk = -hg.s * 26.0
    pts = []
    for (lx, ly), (bx, by) in zip(lump12, _HOOD_BACK):
        X, Y = _hood_map(hg, bx * sc, by * sc, hang=True)
        back = (bx * hg.s < 0)
        if back:
            X += bulk * smoothstep((90 - by) / 120.0)
        pts.append((lx + (X - lx) * e, ly + (Y - ly) * e))
    _enter_head(ctx, xf)
    _smooth(ctx, pts, True, 0.55)
    _fs(ctx, col["top_dk"], lerp(inkw * 2, inkw, e))
    ctx.restore()


def _hood_front(ctx, C, col, hg, st, inkw):
    """Raised hood over the head (head-local ctx). Hides hair/brows/eyes under the rim."""
    u = st["hood"]
    yr, v, cover = _hood_rim(C, u, hg.nod)
    st["hood_rim"] = yr
    st["hood_cover"] = cover
    if v <= 0.0:
        return
    sc = _hood_scale(C)
    side_k = smoothstep((v - 0.08) / 0.55)
    bulk = -hg.s * 26.0
    outer_r = [(x * sc, y * sc) for x, y in _HOOD_OUT]

    def outer_w(y):
        pts = outer_r
        if y >= pts[0][1]:
            return pts[0][0]
        for i in range(1, len(pts)):
            if y >= pts[i][1]:
                y0, y1 = pts[i - 1][1], pts[i][1]
                k = (y - y0) / (y1 - y0)
                return pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * k
        return 0.0

    def inner_w(y):
        a, f, b = hg.abf(clamp(y, hg.lv[0][0] + 2, hg.lv[-1][0]))
        if y > 100 * sc:
            return 70 * sc
        return max(a - 15 * sc, 54 * sc)

    def ow(y):
        return lerp(outer_w(y) - 1.5, min(inner_w(y), outer_w(y) - 1.5), side_k)

    def MO(x, y):
        X, Y = _hood_map(hg, x, y, hang=True)
        if x * hg.s < 0:
            X += bulk * smoothstep((90 - y) / 120.0)
        return (X, Y)

    def MI(x, y):
        return _hood_map(hg, x, y, dz=6.0)
    # ---- outer contour: right bottom -> crown -> left bottom
    outer = [MO(x, y) for x, y in outer_r] + [MO(-x, y) for x, y in reversed(outer_r[:-1])]
    # ---- opening: left bottom -> up -> rim -> right -> down
    ycorner = yr + 12 * sc
    ys = [y * sc for y in (118, 92, 66, 40, 14, -12, -40, -70, -100)]
    ys = [y for y in ys if y > ycorner + 6]
    droop = 5 * sc * smoothstep((v - 0.5) / 0.5)
    brl = st.get("brow_lift", (0.0, 0.0))
    rim = []
    wc = ow(ycorner)
    hd = C["head"]
    for j in range(9):
        q = -1 + 2 * j / 8.0
        xx = q * wc * 0.96
        yy = yr + droop * (1 - q * q) + (ycorner - yr) * q ** 4
        # the rim lifts a hair over a raised brow (reads through the fabric)
        for sgn, bl in ((-1, brl[0]), (1, brl[1])):
            if bl > 0:
                yy -= bl * 7 * sc * math.exp(-((xx - sgn * hd["ex"]) / (hd["ew"] * 1.2)) ** 2) * cover
        rim.append((xx, yy))
    inner = [MI(-ow(y), y) for y in ys] + [MI(x, y) for x, y in rim] + [MI(ow(y), y) for y in reversed(ys)]
    shell = outer + inner
    # ---- shadow over the upper face (inside the opening, under the rim)
    if v > 0.25:
        ctx.save()
        _smooth(ctx, hg.outline(), True, 0.55)
        ctx.clip()
        k = smoothstep((v - 0.25) / 0.5)
        g = cairo.LinearGradient(0, yr - 4, 0, yr + 70 * sc)
        g.add_color_stop_rgba(0, 0.07, 0.06, 0.13, 0.62 * k)
        g.add_color_stop_rgba(0.45, 0.07, 0.06, 0.13, 0.2 * k)
        g.add_color_stop_rgba(1, 0.07, 0.06, 0.13, 0.0)
        ctx.set_source(g)
        ctx.paint()
        ctx.set_source_rgba(0.07, 0.06, 0.13, 0.1 * k)
        ctx.paint()
        ctx.restore()
    # ---- the shell
    ctx.save()
    _smooth(ctx, shell, True, 0.45)
    ctx.clip_preserve()
    _set(ctx, col["top"])
    ctx.fill()
    # soft fabric shading: darker toward the opening / far side, lighter crown
    ctx.translate(10, 10)
    _smooth(ctx, [MO(x * 0.9, y * 0.97 - 4) for x, y in outer_r[3:]] +
            [MO(-x * 0.9, y * 0.97 - 4) for x, y in reversed(outer_r[3:-1])], True, 0.5)
    _set(ctx, _lt(col["top"], 0.07))
    ctx.fill()
    ctx.translate(-10, -10)
    # rolled hem along the opening
    _smooth(ctx, inner, False, 0.45)
    _set(ctx, col["top_dk"])
    ctx.set_line_width(22 * sc)
    ctx.stroke()
    # centre seam from the crown to the rim
    sp = [MI(0, y) for y in (-198 * sc, lerp(-198 * sc, yr, 0.5), yr - 10 * sc)] if yr > -150 * sc else []
    if sp:
        ctx.move_to(*sp[0])
        _qcurve(ctx, sp[0], sp[1], sp[2])
        _stroke(ctx, alpha_ink(PAL["ink"], 0.32), inkw * 0.55)
    ctx.restore()
    _smooth(ctx, shell, True, 0.45)
    _stroke(ctx, PAL["ink"], inkw)
    # inner hem line
    _smooth(ctx, inner, False, 0.45)
    _stroke(ctx, alpha_ink(PAL["ink"], 0.55), inkw * 0.5)
    # sense glow leaking under the rim (power with the eyes covered)
    pw = st["power"]
    if pw > 0.01 and cover > 0.05:
        for side, sgn in (("l", -1), ("r", 1)):
            X, Y, ew, eh, kk, E = st["E_" + side]
            if kk < 0.15:
                continue
            seg = []
            for j in range(7):
                xx = X + (j / 6.0 - 0.5) * ew * 2.1
                ux = xx  # rim y at this screen x (rim is defined in front-view x; approximate)
                q = clamp(ux / max(1.0, wc), -1, 1)
                seg.append((xx, yr + droop * (1 - q * q) + 4.5 * sc))
            ctx.move_to(*seg[0])
            for q in seg[1:]:
                ctx.line_to(*q)
            _stroke(ctx, alpha_ink(mixc(PAL["power"], "#ffffff", 0.35), 0.85 * pw * cover), 3.2 * sc)


def _draw_cap(ctx, C, col, hg, inkw):
    cap = C["col"]["top"]
    crown = [(-104, -66), (-104, -100), (-84, -136), (-40, -158), (0, -162), (40, -158), (84, -136),
             (104, -100), (104, -66), (0, -60)]
    wp = [hg.warp(x, y) for x, y in crown]
    _smooth(ctx, wp, True, 0.45)
    _fs(ctx, cap, inkw)
    band = [(-104, -80), (104, -80), (104, -64), (-104, -64)]
    wp = [hg.warp(x, y) for x, y in band]
    _poly(ctx, wp)
    _fs(ctx, _dk(cap, 0.35), inkw * 0.7)
    # brim protrudes toward the camera / facing side
    s = hg.s
    brim = []
    for x, y, dz in ((-94, -66, 0), (-60, -54, 30), (0, -48, 46), (60, -54, 30), (94, -66, 0), (0, -70, 6)):
        X, _ = hg.warp(x, y, dz=dz)
        brim.append((X + dz * s * 0.6, y + dz * 0.06))
    _smooth(ctx, brim, True, 0.5)
    _fs(ctx, _dk(cap, 0.5), inkw)
    X, _ = hg.warp(0, -112)
    pts = [(X, -128), (X + 13, -120), (X + 11, -102), (X, -94), (X - 11, -102), (X - 13, -120)]
    _poly(ctx, pts)
    _fs(ctx, "#e8c25a", inkw * 0.6)


def _draw_headset(ctx, C, hg, inkw, out):
    a, f, b = hg.abf(10)
    band = [hg.warp(x, y, "front") for x, y in ((-98, 4), (-108, -60), (-80, -128), (0, -150), (80, -128),
                                                (108, -60), (98, 4))]
    _smooth(ctx, band, False, 0.5)
    _stroke(ctx, PAL["ink"], 11)
    _smooth(ctx, band, False, 0.5)
    _stroke(ctx, "#5b5f6e", 5)
    ex = -a * hg.c - 0.12 * a * hg.s
    Z = a * hg.s
    if Z > -50:
        ctx.new_path()
        ellipse(ctx, ex - 4, 14, 15, 22)
        _fs(ctx, "#3a3d4a", inkw)
        mx, my = out["mouth"]
        tip = (mx - C["head"]["mw"] - 14, my + 14)
        ctx.move_to(ex + 4, 26)
        _qcurve(ctx, (ex + 4, 26), (ex + 8, tip[1] + 6), tip)
        _stroke(ctx, PAL["ink"], 7)
        ctx.move_to(ex + 4, 26)
        _qcurve(ctx, (ex + 4, 26), (ex + 8, tip[1] + 6), tip)
        _stroke(ctx, "#5b5f6e", 3)
        ctx.new_path()
        _capsule(ctx, tip[0] - 4, tip[1], 5, tip[0] + 8, tip[1] - 1, 5)
        _fs(ctx, "#2b2d36", inkw * 0.6)


def _draw_sweat(ctx, C, hg, sw, t, inkw):
    side = 1 if hg.s <= 0.25 else -1
    hd = C["head"]
    a, f, b = hg.abf(-50)
    xt = side * a * 0.86
    X, Z, k = hg.proj(xt, -54)
    drop_c = "#bfe9ff"
    n = 1 + int(sw * 2.99)
    for i in range(n):
        yy = -64 + i * 15
        xx = X + side * (i * 5 - 2)
        _drop(ctx, xx, yy, 6.5 - i * 0.8, drop_c, inkw)
    # sliding drop
    ph = (t * 0.55 + C["seed"] * 0.13) % 1.0
    yy = -40 + ph * 95
    X2, _, k2 = hg.proj(side * a * 0.84, yy)
    al = 1.0 if ph < 0.8 else (1 - ph) / 0.2
    if sw > 0.3 and k2 > 0.15:
        ctx.push_group()
        _drop(ctx, X2 - side * 2, yy, 6.0 * (0.6 + 0.4 * sw), drop_c, inkw)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(al)


def _drop(ctx, x, y, r, c, inkw):
    ctx.move_to(x, y - r * 2.1)
    ctx.curve_to(x + r * 0.4, y - r * 1.2, x + r, y - r * 0.4, x + r, y + r * 0.1)
    ctx.arc(x, y + r * 0.1, r, 0, math.pi)
    ctx.curve_to(x - r, y - r * 0.4, x - r * 0.4, y - r * 1.2, x, y - r * 2.1)
    ctx.close_path()
    _fs(ctx, c, inkw * 0.5)
    circle(ctx, x - r * 0.35, y - r * 0.1, r * 0.25)
    _fill(ctx, "#ffffff")


def _draw_heat(ctx, hg, k, t, inkw):
    for i, xo in enumerate((-50, 0, 50)):
        ph = t * 3 + i * 1.3
        y0 = -182 - (i % 2) * 10
        ctx.move_to(xo - 4, y0)
        for j in range(1, 9):
            yy = y0 - j * 5
            ctx.line_to(xo + math.sin(ph + j * 0.9) * 6, yy)
        _stroke(ctx, alpha_ink(PAL["blush"], 0.85 * k), inkw * 0.75)


# ============================================================================
# 7f. body-space accessories
# ============================================================================
def _hp_state(headphones):
    if headphones is None or headphones is False:
        return None
    if headphones == "neck":
        return 0.0
    if headphones == "on" or headphones is True:
        return 1.0
    return clamp(float(headphones))


def _draw_hp_band(ctx, C, J, xf, hg, hp, inkw):
    cups = _cup_positions(C, J, hp)
    k = smoothstep(clamp(hp * 1.5))
    top = _hmap(xf, *hg.warp(0, -166 if C["head"]["hair"] == "mop" else -150))
    nk = J["nodes"]["nck"]
    back = (nk[0], nk[1] - 8)
    apex = _lerp2(back, top, k)
    a, b = cups["l"], cups["r"]
    c1 = (a[0] + (apex[0] - a[0]) * 0.1, apex[1] - (a[1] - apex[1]) * 0.25 * k + 10 * (1 - k))
    c2 = (b[0] + (apex[0] - b[0]) * 0.1, apex[1] - (b[1] - apex[1]) * 0.25 * k + 10 * (1 - k))
    for w, c in ((18, PAL["ink"]), (8, PAL["headphones"])):
        ctx.move_to(a[0], a[1] - 18 * k)
        ctx.curve_to(c1[0], c1[1], c1[0], apex[1], apex[0], apex[1])
        ctx.curve_to(c2[0], apex[1], c2[0], c2[1], b[0], b[1] - 18 * k)
        _stroke(ctx, c, w)


def _draw_hp_cups(ctx, C, J, hp, inkw):
    cups = _cup_positions(C, J, hp)
    k = smoothstep(hp)
    tilt = J["head"]["tilt"] * k
    for s_, sgn in (("l", -1), ("r", 1)):
        x, y = cups[s_]
        rx = lerp(36, 24, k)
        ry = lerp(24, 40, k)
        ang = tilt + sgn * 0.25 * (1 - k)
        ellipse(ctx, x, y, rx, ry, ang)
        _fs(ctx, PAL["headphones"], inkw)
        ellipse(ctx, x + sgn * rx * 0.18 * k, y, rx * 0.55, ry * 0.62, ang)
        _fs(ctx, PAL["headphones_dk"], inkw * 0.6)


def _draw_bandage(ctx, C, a, inkw):
    E, Wr = a["E2"], a["W2"]
    r = C["arm_r"][2] * 1.12
    p0, p1 = _lerp2(E, Wr, 0.3), _lerp2(E, Wr, 0.78)
    ctx.new_path()
    _capsule(ctx, p0[0], p0[1], r * 1.05, p1[0], p1[1], r)
    _fs(ctx, "#f6f3ee", inkw * 0.8)
    dx, dy = _norm(p1[0] - p0[0], p1[1] - p0[1])
    nx, ny = -dy, dx
    for k in (0.25, 0.5, 0.75):
        q = _lerp2(p0, p1, k)
        ctx.move_to(q[0] - nx * r * 0.9 - dx * 4, q[1] - ny * r * 0.9 - dy * 4)
        ctx.line_to(q[0] + nx * r * 0.9 + dx * 4, q[1] + ny * r * 0.9 + dy * 4)
    _stroke(ctx, "#cfc8bf", inkw * 0.5)


def _draw_controller(ctx, hl, hr, inkw, thumbs=(0.0, 0.0), skin=None):
    """Game pad held in both hands (drawn over the palms, thumbs on top)."""
    cx, cy = (hl[0] + hr[0]) / 2, (hl[1] + hr[1]) / 2 - 6
    ang = math.atan2(hr[1] - hl[1], hr[0] - hl[0])
    if abs(ang) > math.pi / 2:
        ang -= math.copysign(math.pi, ang)
    ang *= 0.5
    w = max(118.0, min(150.0, math.hypot(hr[0] - hl[0], hr[1] - hl[1]) + 50))
    with _Saved(ctx, cx, cy, ang):
        def body(d):
            _capsule(ctx, -w * 0.5, 4, 22 + d, -w * 0.25, -2, 20 + d)
            _capsule(ctx, w * 0.25, -2, 20 + d, w * 0.5, 4, 22 + d)
            rrect_(ctx, -w * 0.3 - d, -20 - d, w * 0.6 + 2 * d, 34 + 2 * d)
        _ink_fill(ctx, body, "#3a3d4c", inkw)
        for (bx, by, c) in ((w * 0.3, -6, "#ff5a6e"), (w * 0.38, 2, "#3ddc84"), (w * 0.22, 2, "#4fa3ff"),
                            (w * 0.3, 10, "#ffcc33")):
            circle(ctx, bx, by, 4.2)
            _fill(ctx, c)
        ctx.rectangle(-w * 0.36, -2, 18, 6)
        ctx.rectangle(-w * 0.36 + 6, -8, 6, 18)
        _fill(ctx, "#1d1f28")
        if skin is not None:      # thumbs on the sticks / buttons
            def thb(d):
                for sgn, th in ((-1, thumbs[0]), (1, thumbs[1])):
                    bx = sgn * w * 0.3 + th * 10 * sgn
                    by = -2 + th * 6
                    _capsule(ctx, sgn * w * 0.52, 14, 9.5 + d, bx, by, 9.0 + d)
            _ink_fill(ctx, thb, skin, inkw)


def rrect_(ctx, x, y, w, h):
    """Axis-aligned rectangle sub-path, clockwise (matches _capsule winding)."""
    ctx.move_to(x, y)
    ctx.line_to(x + w, y)
    ctx.line_to(x + w, y + h)
    ctx.line_to(x, y + h)
    ctx.close_path()


def _draw_counter(ctx, who, inkw):
    top = -DESK_H[who] + 4
    ctx.rectangle(-300, top, 600, -top + 4)
    _fs(ctx, PAL["corp_wall"], inkw)
    ctx.rectangle(-300, top - 16, 600, 18)
    _fs(ctx, "#f5f8fb", inkw)
    ctx.rectangle(-300, top + 60, 600, 14)
    _fill(ctx, PAL["hush"])


# ============================================================================
# 8. draw_person
# ============================================================================
_CHAR_CACHE = {}
BLINK = {"tired": (0.22, 0.24), "embar": (0.42, 0.14), "boss": (0.14, 0.16), "guard": (0.25, 0.18),
         "recep": (0.2, 0.2)}


def _char(who, outfit):
    key = (who, outfit)
    c = _CHAR_CACHE.get(key)
    if c is None:
        base = CHARS[who]
        c = dict(base)
        c["col"] = dict(base["col"])
        ov = OUTFITS.get(key, {})
        for k, v in ov.items():
            if k == "col":
                c["col"].update(v)
            else:
                c[k] = v
        c["_top"] = ov.get("top", base["top"])
        c["_sleeve"] = ov.get("sleeve", base["sleeve"])
        c["_shoe"] = ov.get("shoe", base["shoe"])
        c["_pants"] = ov.get("pants", base["pants"])
        c["_who"] = who
        _CHAR_CACHE[key] = c
    return c


def _arm_layer(Q, a, J, side):
    lay = Q[f"a{side}_layer"]
    if lay:
        return lay
    zc = J["nodes"]["chs"][2]
    if a["S"][2] < zc - 25 and a["zW"] < zc + 50:
        return "back"
    if a["zW"] > J["head"]["z"] + 30 and a["W2"][1] < J["head"]["pivot"][1] + 20:
        return "front"
    return "mid"


# ---------------------------------------------------------------------------
# Draw-order signatures (Episode 2: no hand z-order flicker)
# ---------------------------------------------------------------------------
# A signature is (layer_l, layer_r, top): the layer of each arm and which arm is drawn
# last when both share a layer.  Within a layer, depth decides only when the hands are
# clearly at different depths (ZTIE); near-equal depths use the pose's preference
# (`hand_top`, default "r"), so tiny depth changes (breathing, IK rounding) never flip it.
# In a blend (a, b, k) the order is pose a's until a switch point k* and pose b's after
# it; k* is picked once per blend (cached) where the elements whose order changes are
# farthest apart, so the order changes at most once and never while they overlap.
_LAYER_IX = {"back": 0, "mid": 1, "front": 2}
ZTIE = 24.0
_SWITCH_CACHE = {}
_SWITCH_KS = tuple(0.05 * i for i in range(1, 20))


def _arm_sig(Q, J):
    arms = J["arms"]
    ll = _arm_layer(Q, arms["l"], J, "l")
    lr = _arm_layer(Q, arms["r"], J, "r")
    dz = arms["r"]["zW"] - arms["l"]["zW"]
    if abs(dz) < ZTIE:      # near-equal depths: the pose's preference (default l on top,
        top = "r" if Q.get("hand_top", 0.0) > 0.5 else "l"     # like arms_crossed / cradle)
    else:
        top = "r" if dz > 0 else "l"
    return (ll, lr, top)


def _sig_ranks(sig):
    ll, lr, top = sig
    rl, rr = _LAYER_IX[ll] * 2, _LAYER_IX[lr] * 2
    if ll == lr:
        if top == "l":
            rl += 1
        else:
            rr += 1
    return rl, rr


def _seg_dist(a, b, c, d):
    """Distance between 2D segments ab and cd."""
    def pd(p, q0, q1):
        vx, vy = q1[0] - q0[0], q1[1] - q0[1]
        L2 = vx * vx + vy * vy
        u = 0.0 if L2 < 1e-9 else clamp(((p[0] - q0[0]) * vx + (p[1] - q0[1]) * vy) / L2)
        return math.hypot(p[0] - q0[0] - vx * u, p[1] - q0[1] - vy * u)
    return min(pd(a, c, d), pd(b, c, d), pd(c, a, b), pd(d, a, b))


def _hand_tip(C, a):
    ca, sa = math.cos(a["ang"]), math.sin(a["ang"])
    W = a["W2"]
    return (W[0] + ca * C["hand"] * 1.15, W[1] + sa * C["hand"] * 1.15)


def _sig_separation(C, J, sa, sb):
    """Smallest clearance (px) among the element pairs whose order differs between sa, sb."""
    arms = J["arms"]
    ra, rb = _sig_ranks(sa), _sig_ranks(sb)
    rad = C["arm_r"][2] + C["hand"] * 0.38
    seps = []
    if (ra[0] < ra[1]) != (rb[0] < rb[1]):
        al, ar = arms["l"], arms["r"]
        d = _seg_dist(al["E2"], _hand_tip(C, al), ar["E2"], _hand_tip(C, ar))
        seps.append(d - 2 * rad)
    hh = J["head"]
    hr = C["head"]["levels"][4][1]
    poly = None
    for i, s_ in enumerate("lr"):
        a = arms[s_]
        pts = (a["E2"], _lerp2(a["E2"], a["W2"], 0.5), a["W2"], _lerp2(a["W2"], _hand_tip(C, a), 0.6))
        if (sa[i] == "back") != (sb[i] == "back"):      # arm vs torso silhouette / thighs
            if poly is None:
                J.setdefault("t", 0.0)
                poly = _torso_pts(C, J, _torso_geom(C, J))
            best = 1e9
            for p in pts[1:]:
                dt = _poly_sdist(p, poly)
                for g in J["legs"].values():
                    dt = min(dt, _seg_dist(p, p, g["hip"][:2], g["knee"][:2]) - C["leg_r"][0])
                best = min(best, dt)
            seps.append(best - rad)
        if (sa[i] == "front") != (sb[i] == "front"):    # arm vs head
            best = min(math.hypot(p[0] - hh["cx"], p[1] - hh["cy"]) for p in pts[2:]) - hr
            seps.append(best - rad)
    return min(seps) if seps else 1e9


def _poly_sdist(p, poly):
    """Signed distance from p to a closed polygon (negative inside)."""
    inside = False
    best = 1e18
    n = len(poly)
    x, y = p
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a[1] > y) != (b[1] > y):
            xc = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if xc > x:
                inside = not inside
        best = min(best, _seg_dist(p, p, a, b))
    return -best if inside else best


def _detour(Q, sa, sb, k):
    """Blend path tweak: an arm that goes between behind-the-body and in-front swings out
    around the hips/torso instead of passing through them (bell-shaped in k)."""
    w = 4.0 * k * (1.0 - k)
    if w <= 0.0:
        return
    for i, s_ in enumerate("lr"):
        if (sa[i] == "back") != (sb[i] == "back"):
            Q[f"a{s_}_o"] += 0.45 * w
            Q[f"a{s_}_eo"] += 0.25 * w
            Q[f"a{s_}_tx"] += 0.08 * w


_CYCLE_ORDER = {}
_CYC_N = 48


def _cycle_sig(pose, who, C, pt, turn, hp, period):
    """Draw-order signature of a cycle at phase pt, from a cached per-cycle table:
    layers are a majority vote over the cycle (no mid-cycle layer pops), and the
    hand-over-hand order only changes at phases where the hands are clearly apart."""
    tb = round(turn * 20) / 20
    key = (C["_who"], id(C), _pose_key(pose), tb, round(hp, 2))
    tab = _CYCLE_ORDER.get(key)
    if tab is None:
        fx0 = {"head_turn": 0.0, "head_tilt": 0.0, "head_nod": 0.0}
        rad = C["arm_r"][2] + C["hand"] * 0.38
        votes = {"l": {}, "r": {}}
        raw = []
        for i in range(_CYC_N):
            Q = resolve_pose(pose, who, period * i / _CYC_N)
            for kk, v in C["posture"].items():
                Q[kk] = Q[kk] + v * Q["posture"]
            Q["sway"] = 0.0
            Q["breath"] = 0.0
            J = _solve(C, Q, who, tb, 0.0, fx0, hp)
            sg = _arm_sig(Q, J)
            al, ar = J["arms"]["l"], J["arms"]["r"]
            sep = _seg_dist(al["E2"], _hand_tip(C, al), ar["E2"], _hand_tip(C, ar)) - 2 * rad
            for j, s_ in enumerate("lr"):
                votes[s_][sg[j]] = votes[s_].get(sg[j], 0) + 1
            raw.append((sg[2], sep))
        lay = tuple(max(votes[s_].items(), key=lambda kv: (kv[1], _LAYER_IX[kv[0]]))[0] for s_ in "lr")
        clear = [i for i in range(_CYC_N) if raw[i][1] > 6.0]
        tops = [raw[i][0] for i in range(_CYC_N)]
        if clear:
            start = clear[0]
            cur = raw[start][0]
            for j in range(_CYC_N):
                i = (start + j) % _CYC_N
                if raw[i][1] > 6.0:
                    cur = raw[i][0]
                tops[i] = cur
        else:       # hands always together: one fixed order for the whole cycle
            cnt = {}
            for t_, _ in raw:
                cnt[t_] = cnt.get(t_, 0) + 1
            only = max(cnt.items(), key=lambda kv: kv[1])[0]
            tops = [only] * _CYC_N
        tab = [(lay[0], lay[1], tp) for tp in tops]
        if len(_CYCLE_ORDER) > 2000:
            _CYCLE_ORDER.clear()
        _CYCLE_ORDER[key] = tab
    i = int(round((pt / period) % 1.0 * _CYC_N)) % _CYC_N
    return tab[i]


def _pose_key(p):
    return p if isinstance(p, str) else repr(p)


def _is_blend(pose):
    return isinstance(pose, (tuple, list)) and len(pose) == 3 and not isinstance(pose[0], (int, float))


def _sig_detail(pose, who, C, pt, turn, fx, hp):
    """Blend pose -> (signature, (sa, sb, k) for the detour or None)."""
    a, b, k = pose
    k = clamp(float(k))
    sa = _sig_for(a, who, C, pt, turn, fx, hp)
    if k <= 0.0:
        return sa, None
    sb = _sig_for(b, who, C, pt, turn, fx, hp)
    if k >= 1.0:
        return sb, None
    if sa == sb:
        return sa, None
    return (sa if k < _switch_k(who, C, a, b, turn, hp, sa, sb) else sb), (sa, sb, k)


def _sig_for(pose, who, C, pt, turn, fx, hp, reach=None):
    """Draw-order signature of a pose (name | dict | blend) at this moment."""
    if _is_blend(pose):
        return _sig_detail(pose, who, C, pt, turn, fx, hp)[0]
    per = _pose_period(pose)
    if per:
        return _cycle_sig(pose, who, C, pt, turn, hp, per)
    Q = resolve_pose(pose, who, pt)
    for kk, v in C["posture"].items():
        Q[kk] = Q[kk] + v * Q["posture"]
    J = _solve(C, Q, who, turn, 0.0, fx, hp, None, reach)
    return _arm_sig(Q, J)


def _switch_k(who, C, a, b, turn, hp, sa, sb):
    key = (C["_who"], id(C), _pose_key(a), _pose_key(b), round(turn * 20) / 20, sa, sb)
    ks = _SWITCH_CACHE.get(key)
    if ks is not None:
        return ks
    fx0 = {"head_turn": 0.0, "head_tilt": 0.0, "head_nod": 0.0}
    tq = round(turn * 20) / 20
    best, ks = -1e18, 0.5
    for k in _SWITCH_KS:
        Q = resolve_pose((a, b, k), who, 0.0)
        for kk, v in C["posture"].items():
            Q[kk] = Q[kk] + v * Q["posture"]
        Q["breath"] = 0.0
        Q["sway"] = 0.0
        _detour(Q, sa, sb, k)
        J = _solve(C, Q, who, tq, 0.0, fx0, hp)
        score = min(_sig_separation(C, J, sa, sb), 60.0) - 40.0 * abs(k - 0.5)
        if score > best + 1e-6:
            best, ks = score, k
    if len(_SWITCH_CACHE) > 2000:
        _SWITCH_CACHE.clear()
    _SWITCH_CACHE[key] = ks
    return ks


def _drift(t, seed):
    """Tiny idle saccades: quick hops between nearby gaze points."""
    u = t * 0.75 + hash01(seed, 5)
    i = math.floor(u)
    f = u - i
    k = smoothstep(f / 0.07)
    x0, x1 = hash01(i - 1, seed) - 0.5, hash01(i, seed) - 0.5
    y0, y1 = hash01(i - 1, seed + 9) - 0.5, hash01(i, seed + 9) - 0.5
    return ((x0 + (x1 - x0) * k) * 0.14, (y0 + (y1 - y0) * k) * 0.08)


_SPEED_CACHE = {}


def cycle_speed(who, pose, turn=1.0, outfit="default"):
    """Ground speed (px/s at s=1, screen x) that keeps the planted foot from sliding.

    Move the character by  speed * s * dt  per frame toward its facing side
    (+x for turn > 0, flip=False).  0.0 for non-locomotion poses."""
    key = (who, pose if isinstance(pose, str) else repr(pose), outfit)
    tq = clamp(turn, -1.6, 1.6) * TURN_RAD
    if key in _SPEED_CACHE:
        return _SPEED_CACHE[key] * math.sin(tq)
    C = _char(who, outfit)
    period = _pose_period(pose)
    if period is None:
        _SPEED_CACHE[key] = 0.0
        return 0.0
    n = 48
    fx = {"head_turn": 0.0, "head_tilt": 0.0, "head_nod": 0.0}
    samples = []
    for i in range(n + 1):
        pt = period * i / n
        Q = resolve_pose(pose, who, pt)
        for k, v in C["posture"].items():
            Q[k] = Q[k] + v * Q["posture"]
        Q["sway"] = 0.0
        Q["dx"] = 0.0
        J = _solve(C, Q, who, 1.0, 0.0, fx, 0.0)
        samples.append({q: (J["legs"][q]["sole"][0], J["legs"][q]["sole"][1]) for q in "lr"})
    vs = []
    dt = period / n
    for i in range(n):
        a, b = samples[i], samples[i + 1]
        low = max("lr", key=lambda q: a[q][1])
        if abs(a[low][1] - b[low][1]) < 1.5:
            vs.append(-(b[low][0] - a[low][0]) / dt)
    vs.sort()
    v = vs[len(vs) // 2] if vs else 0.0
    v /= math.sin(TURN_RAD)          # forward speed (sampled at turn = 1)
    _SPEED_CACHE[key] = v
    return v * math.sin(tq)


def _pose_period(pose):
    """Cycle period of a pose name or dict pose (dicts inherit their base cycle's period)."""
    if isinstance(pose, str):
        return CYCLES[pose][0] if pose in CYCLES else None
    if isinstance(pose, dict):
        bp = _pose_period(pose.get("base", "stand"))
        if bp is not None:
            return pose.get("period", bp)
        return pose.get("period")
    return None


_LEG_KEYS = ("ll_", "lr_", "hip_roll", "plant", "hip_h", "turn")


def _pose_speed(who, pose, turn, outfit):
    if isinstance(pose, dict):     # dicts based on a cycle get a real speed (Episode 2 fix)
        if _pose_period(pose) is None:
            return 0.0
        if "period" not in pose and not any(k.startswith(_LEG_KEYS) for k in pose):
            return _pose_speed(who, pose.get("base", "stand"), turn, outfit)   # legs untouched
        if len(_SPEED_CACHE) > 4000:
            _SPEED_CACHE.clear()
        return cycle_speed(who, pose, turn, outfit)
    if isinstance(pose, str):
        return cycle_speed(who, pose, turn, outfit)
    if isinstance(pose, (tuple, list)) and len(pose) == 3:
        k = clamp(float(pose[2]))
        return lerp(_pose_speed(who, pose[0], turn, outfit), _pose_speed(who, pose[1], turn, outfit), k)
    return 0.0


def _hold_sides(hold_sides, hold_mode, hand1="r"):
    """Normalise hold_sides -> list of 'l' / 'r' / 'both' entries."""
    if hold_sides is None:          # Episode 1 behaviour: the pose decides
        return {1: [hand1], 2: ["both"]}.get(hold_mode, [])
    if isinstance(hold_sides, str):
        if hold_sides == "both":
            return ["both"]
        return [c for c in ("l", "r") if c in hold_sides]
    out = []
    for q in hold_sides:
        if q in ("l", "r", "both") and q not in out:
            out.append(q)
    return out


def draw_person(ctx, who, x, y, s, t, pose="stand", expr="neutral", look=(0, 0), mouth=(0, 0),
                face=None, turn=0.0, flip=False, blink=None, blush=None, sweat=0.0, power=0.0,
                outfit="default", headphones=None, bandage=False, hold=None, pose_t=None, seed=0,
                counter=None, glint=0.0, shadow=True, drift=True, hood=0.0, tears=0.0,
                glasses_tilt=0.0, glasses_dx=0.0, glasses_dy=0.0, hold_sides=None, hold_layer=None,
                reach=None, pocket_side=None):
    """Draw a person. Returns anchors in the CALLER's ctx coordinates (see API_human.md)."""
    C = _char(who, outfit)
    col = C["col"]
    pt = t if pose_t is None else pose_t
    Q = resolve_pose(pose, who, pt)
    pw = Q["posture"]
    for k, v in C["posture"].items():
        Q[k] = Q[k] + v * pw
    F = resolve_face(who, expr, face)
    fx = {"head_turn": F["head_turn"], "head_tilt": F["head_tilt"], "head_nod": F["head_nod"]}
    hp = _hp_state(headphones)
    hp0 = hp if hp is not None else 0.0
    sgnf = -1.0 if flip else 1.0
    # world-space reach targets -> rig-local (x, y, weight, hand angle)
    reach_l = None
    if reach:
        reach_l = {}
        for side_, v in reach.items():
            if v is None or side_ not in ("l", "r"):
                continue
            w_ = clamp(float(v[2])) if len(v) > 2 and v[2] is not None else 1.0
            ang_ = v[3] if len(v) > 3 else None
            if ang_ is not None and flip:
                ang_ = math.pi - ang_
            reach_l[side_] = ((v[0] - x) / (s * sgnf), (v[1] - y) / s, w_, ang_)
    lagQ = resolve_pose(pose, who, pt - 0.09) if C["_top"] == "labcoat" else None
    sig = None
    if _is_blend(pose):     # draw order through blends: see _sig_for / _switch_k
        sig, det = _sig_detail(pose, who, C, pt, turn, fx, hp0)
        if det is not None:
            _detour(Q, *det)
    J = _solve(C, Q, who, turn, t, fx, hp0, lagQ, reach_l)
    J["t"] = t
    J["_lv"] = _torso_geom(C, J)
    J["_bandage"] = None if not bandage else ("r" if bandage is True else bandage)
    if pocket_side in (None, "r", "right"):
        J["_pocket_sgn"] = 1.0
    elif pocket_side in ("l", "left"):
        J["_pocket_sgn"] = -1.0
    else:   # "near": the side toward the camera for this facing
        J["_pocket_sgn"] = -1.0 if J["turn"] > 0.02 else 1.0
    inkw = INK_W
    # ---- runtime face state
    lip_o, lip_w = (mouth or (0.0, 0.0))
    opn = clamp(F["open"] + lip_o * 0.62)
    if lip_o > 0:
        F["press"] = F["press"] * (1 - clamp(lip_o * 2))
    rate, dur = BLINK.get(who, (0.25, 0.16))
    bl = blink_amount(t, C["seed"] + seed * 31, rate, dur) if blink is None else clamp(blink)
    bval = F["blush"] if blush is None else blush
    hood_u = clamp(hood) if C["_top"] == "hoodie" else 0.0
    st = dict(open=opn, wide=clamp(lip_w, -1, 1), blush=clamp(bval), look=look,
              drift=_drift(t, C["seed"] + seed) if drift else (0.0, 0.0), blink=bl,
              power=clamp(power), sweat=clamp(sweat), wet=C.get("wet", False), glint=glint,
              hood=hood_u, tears=clamp(tears + F.get("tear", 0.0)), gtilt=glasses_tilt,
              gdx=glasses_dx, gdy=glasses_dy)
    xf = _head_xf(J, C, F)
    st["xf"] = xf
    hg = _HG(C, J, F, opn)
    bside = None if not bandage else ("r" if bandage is True else bandage)
    phase = (pt / Q.get("_cycle", 1.0)) % 1.0

    ctx.save()
    M0 = ctx.get_matrix()
    ctx.translate(x, y)
    ctx.scale(s * sgnf, s)
    ctx.set_line_cap(1)   # round
    ctx.set_line_join(1)
    ctx.set_tolerance(0.3)
    # ---- ground shadow
    if shadow:
        lift_h = max(0.0, -(J["pel_y"] + (C["thigh"] + C["shin"] + C["foot_h"]))) if Q["plant"] > 0.5 else 0
        sk = 1.0 / (1.0 + lift_h / 300.0)
        ellipse(ctx, J["nodes"]["pel"][0], 0, (C["tw"]["hip"][0] * 1.5 + 30) * sk, 16 * sk)
        _set(ctx, (0.11, 0.08, 0.15, 0.16 * sk))
        ctx.fill()
    arms = J["arms"]
    # ---- draw order (continuous through blends and cycles: see _sig_for / _cycle_sig)
    if sig is None:
        per = _pose_period(pose) if not reach_l else None
        sig = _cycle_sig(pose, who, C, pt, turn, hp0, per) if per else _arm_sig(Q, J)
    layers = {"l": sig[0], "r": sig[1]}
    top_arm = sig[2]
    ranks = _sig_ranks(sig)
    arm_seq = ["l", "r"] if ranks[0] < ranks[1] else ["r", "l"]
    # ---- held props
    hold_mode = int(round(Q["hold"]))
    entries = []
    if hold:
        if hold_layer in (None, "auto"):
            slot = "after" if Q["hold_order"] > 0.5 else "before"
        else:
            slot = {"front": "after", "back": "before", "top": "top"}.get(hold_layer, "before")
        for sd in _hold_sides(hold_sides, hold_mode, "l" if Q["hold_hand"] < 0 else "r"):
            entries.append((sd, slot))
    both_last = arm_seq[-1]
    anchors_local = {}

    def do_hold(side):
        if side == "both":
            a, b = arms["l"]["hold_pt"], arms["r"]["hold_pt"]
            hx, hy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            ang = math.atan2(b[1] - a[1], b[0] - a[0])
        else:
            hx, hy = arms[side]["hold_pt"]
            ang = arms[side]["ang"]
        sx_, sy_ = x + s * sgnf * hx, y + s * hy
        ang_s = ang if not flip else math.pi - ang
        ctx.save()
        ctx.set_matrix(M0)
        hold(ctx, side, sx_, sy_, ang_s)
        ctx.restore()

    def draw_arm(s_):
        a = arms[s_]
        _draw_arm(ctx, C, col, a, s_, J, inkw, t, phase)
        if bside == s_:
            _draw_bandage(ctx, C, a, inkw)

    # provisional hold points (hand anchor before drawing) = wrist + along hand
    for s_ in "lr":
        a = arms[s_]
        hv = Q[f"a{s_}_h"]
        hs = C["hand"]
        ca, sa = math.cos(a["ang"]), math.sin(a["ang"])
        ys = (-1.0 if s_ == "l" else 1.0) * (1.0 if Q[f"a{s_}_tf"] >= 0 else -1.0)
        a["hold_pt"] = (a["W2"][0] + (ca * hv[2] * hv[0] - sa * ys * hv[3]) * hs,
                        a["W2"][1] + (sa * hv[2] * hv[0] + ca * ys * hv[3]) * hs)

    def layer_pass(lname):
        here = [q for q in arm_seq if layers[q] == lname]
        if layers[both_last] == lname:
            for sd, sl in entries:
                if sd == "both" and sl == "before":
                    do_hold("both")
        for s_ in here:
            for sd, sl in entries:
                if sd == s_ and sl == "before":
                    do_hold(s_)
            draw_arm(s_)
            for sd, sl in entries:
                if sd == s_ and sl == "after":
                    do_hold(s_)
            if s_ == both_last:
                for sd, sl in entries:
                    if sd == "both" and sl == "after":
                        do_hold("both")

    # ---- back hair + headphone band behind
    _enter_head(ctx, xf)
    _draw_back_hair(ctx, C, col, hg, F, inkw, st["wet"])
    ctx.restore()
    if hp is not None and hp < 0.62:
        _draw_hp_band(ctx, C, J, xf, hg, hp, inkw)
    if C["_top"] == "hoodie":
        if hood_u > 0.0:
            _hood_back(ctx, C, col, J, xf, hg, hood_u, inkw)
        else:
            _draw_hood(ctx, C, col, J, inkw)
    if C["_top"] == "labcoat":
        _coat_tails(ctx, C, col, J, inkw, "back")
    layer_pass("back")
    # ---- legs (far first)
    legs = J["legs"]
    far, near = sorted("lr", key=lambda q: legs[q]["knee"][2])
    lap = max(legs["l"]["knee"][2], legs["r"]["knee"][2]) - J["nodes"]["pel"][2] > C["tw"]["hip"][1] * 1.6
    if not lap:
        _draw_leg(ctx, C, col, legs[far], inkw)
        _draw_leg(ctx, C, col, legs[near], inkw, other=legs[far])
    if C["_top"] == "labcoat":
        _coat_tails(ctx, C, col, J, inkw, "front")
    # ---- neck + torso
    _draw_neck(ctx, C, col, J, inkw, clamp((st["blush"] - 0.7) / 0.3))
    tor = _draw_torso(ctx, C, col, J, inkw, t)
    if lap:   # thighs come toward camera (seated, front view): legs over the torso hem
        _draw_leg(ctx, C, col, legs[far], inkw, k0=0.3)
        _draw_leg(ctx, C, col, legs[near], inkw, k0=0.3)
    anchors_local["pocket"] = tor["pocket"]
    if hp is not None and hp < 0.3:
        _draw_hp_cups(ctx, C, J, hp, inkw)
    layer_pass("mid")
    # ---- head
    st["hg"] = hg
    ha = _draw_head(ctx, C, col, J, F, inkw, t, st)
    if hp is not None and hp >= 0.62:
        _draw_hp_band(ctx, C, J, xf, hg, hp, inkw)
    if hp is not None and hp >= 0.3:
        _draw_hp_cups(ctx, C, J, hp, inkw)
    if st["power"] > 0.01:
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_SCREEN)
        cover = st.get("hood_cover", 0.0)
        pwr = st["power"]
        for side in ("l", "r"):
            X, Y, ew, eh, k, E = st["E_" + side]
            if k <= 0.12:
                continue
            if E["lid"] < 0.97 and cover < 0.99:
                px_, py_ = _hmap(xf, X, Y)
                op = (1 - E["lid"] * 0.6) * (1 - cover)
                radial_glow(ctx, px_, py_, C["head"]["ew"] * 2.4, PAL["power"], 0.62 * pwr * op)
                radial_glow(ctx, px_, py_, C["head"]["ew"] * 1.05, "#d9fffb", 0.35 * pwr * op)
            closed = smoothstep((E["lid"] - 0.82) / 0.15) * (1 - cover)
            if closed > 0.01:       # eyes closed: a faint glow along the lash line
                px_, py_ = _hmap(xf, X, Y + eh * 0.62)
                radial_glow(ctx, px_, py_, C["head"]["ew"] * 1.55, PAL["power"], 0.34 * pwr * closed)
            if cover > 0.01:        # hood over the eyes: light leaking under the rim
                px_, py_ = _hmap(xf, X, st.get("hood_rim", Y) + 9)
                radial_glow(ctx, px_, py_, C["head"]["ew"] * 1.7, PAL["power"], 0.4 * pwr * cover)
        ctx.restore()
    layer_pass("front")
    if Q["controller"] > 0.5:
        _draw_controller(ctx, arms["l"]["hold_pt"], arms["r"]["hold_pt"], inkw,
                         (Q["al_thumb"], Q["ar_thumb"]), col["skin"])
    for sd, sl in entries:
        if sl == "top":
            do_hold(sd)
    if counter is None:
        counter = (who == "recep")
    if counter:
        _draw_counter(ctx, who, inkw)
    ctx.restore()

    # ---- anchors -> caller coords
    def S(p):
        return (x + s * sgnf * p[0], y + s * p[1])

    def SA(p, ang):
        q = S(p)
        return (q[0], q[1], ang if not flip else math.pi - ang)

    hd = {k: _hmap(xf, *v) for k, v in ha.items()}
    out = {
        "head": S((xf[0], xf[1])), "face": S(hd["face"]), "eye_l": S(hd["eye_l"]), "eye_r": S(hd["eye_r"]),
        "mouth": S(hd["mouth"]), "nose": S(hd["nose"]), "top": S(hd["top"]),
        "hand_l": SA(arms["l"]["hold_pt"], arms["l"]["ang"]), "hand_r": SA(arms["r"]["hold_pt"], arms["r"]["ang"]),
        "wrist_l": S(arms["l"]["W2"]), "wrist_r": S(arms["r"]["W2"]),
        "elbow_l": S(arms["l"]["E2"]), "elbow_r": S(arms["r"]["E2"]),
        "pocket": S(anchors_local["pocket"]), "shoulder_l": S(J["shj"]["l"]), "shoulder_r": S(J["shj"]["r"]),
        "hip": S(J["nodes"]["pel"]), "neck": S(J["nodes"]["nck"]),
        "foot_l": S(J["legs"]["l"]["sole"]), "foot_r": S(J["legs"]["r"]["sole"]),
        "knee_l": S(J["legs"]["l"]["knee"]), "knee_r": S(J["legs"]["r"]["knee"]),
        "ground": (x, y), "seat": (x, y - s * SEAT_H[who]), "desk": (x, y - s * DESK_H[who]),
        "sill": (x, y - s * SILL_H[who]), "crate": (x, y - s * CRATE_H[who]), "blink": bl,
        "cycle": Q.get("_cycle"), "speed": _pose_speed(who, pose, turn, outfit) * s * sgnf,
        "order": tuple(arm_seq), "layers": (layers["l"], layers["r"]),
        "hood_rim": S(_hmap(xf, 0.0, st["hood_rim"])) if "hood_rim" in st else None,
    }
    return out


# ----------------------------------------------------------------------------
# convenience
# ----------------------------------------------------------------------------
def ground_from_seat(who, seat_y, s):
    """Seated poses anchor on the floor: convert a set's seat-surface y to the ground y."""
    return seat_y + SEAT_H[who] * s


def metrics(who):
    """Reference sizes at s=1: height, seat/desk/sill heights, head size."""
    C = CHARS[who]
    return dict(height=C["height"], seat=SEAT_H[who], desk=DESK_H[who], sill=SILL_H[who],
                head=C["head"]["chin"] + 150, leg=C["thigh"] + C["shin"] + C["foot_h"])


def _alias(who):
    def f(ctx, x, y, s=1.0, t=0.0, **kw):
        return draw_person(ctx, who, x, y, s, t, **kw)
    f.__name__ = f"draw_{who}"
    f.__doc__ = f"draw_person(ctx, {who!r}, x, y, s, t, **kw)"
    return f


draw_tired, draw_embar, draw_boss, draw_guard, draw_recep = (_alias(w) for w in
                                                             ("tired", "embar", "boss", "guard", "recep"))
POSE_NAMES = tuple(POSES) + tuple(CYCLES)
EXPR_NAMES = tuple(EXPR)


def _crate_heights():
    """Low-box seat height (sit_crate) per character, measured from the pose's own legs."""
    out = {}
    fx = {"head_turn": 0.0, "head_tilt": 0.0, "head_nod": 0.0}
    for who in CHARS:
        C = _char(who, "default")
        Q = resolve_pose("sit_crate", who, 0.0)
        Q["sway"] = 0.0
        J = _solve(C, Q, who, 0.0, 0.0, fx, 0.0)
        out[who] = int(-J["nodes"]["pel"][1] - C["leg_r"][0] * 0.8)
    return out


# CRATE_H : top of the low box Tiredness sits on in `sit_crate` (px above the ground at s=1)
CRATE_H = _crate_heights()
