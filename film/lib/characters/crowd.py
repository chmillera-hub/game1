"""crowd.py -- the extras: a parametric generator for background creatures (S4 tavern, S5
square, S8 benches), the scrying crystal everyone films with, the tavern tankard, and the
uncanny synchronized laugh.

    from film.lib import characters as ch
    spec = ch.random_creature(17)                 # deterministic: same seed -> same creature
    spec = ch.random_creature(4, "goblin")        # or pick the kind
    pose = ch.crowd_pose("film", t, spec, facing=2, thumb=feed)   # an action preset
    rig = ch.draw_crowd(cr, x, ground_y, 0.6, spec, pose, ch.LIGHTS["square"], t)

Kinds (CROWD_KINDS, heights at scale 1.0 = base.CAST_HEIGHTS): dwarf 300, goblin 260,
kobold 220, satyr 430, elf 470, harpy 400, minotaur 600 (the minotaur variant is the real
minotaur rig recoloured -- one per crowd; the others are deliberately cheap, ~3-5 ms each).

Actions (CrowdPose.action / crowd_pose): "idle", "cheer", "film" (raise_crystal_film: a glowing
scrying crystal held up, a tiny red recording rune, its cold light on the face), "lower"
(lower_crystal: held low, dimming), "turn_away", "laugh" (laugh_sync: everyone given the same t
laughs in the identical rhythm), "tankard", "sit_table", "talk" (lean in and talk).

The scrying crystal is also a standalone prop: draw_scrying_crystal(...) and crystal_hold(...)
(a hold callback for any creature's Arm(hold=...)); crystal_feed(...) renders the reflected
fight once per frame for every crystal's face.
"""

import math
import random
from dataclasses import dataclass, field

import cairocffi as cairo

from .. import core, fx
from ..core import clamp, lerp, smooth
from . import base as B
from . import _folk as F
from .base import Mat, Path, v_add, v_lerp
from .dragon import Arm

__all__ = ["CrowdSpec", "CrowdPose", "CrowdRig", "random_creature", "crowd_pose", "draw_crowd", "laugh_sync",
           "draw_scrying_crystal", "crystal_hold", "crystal_feed", "CrystalHold", "draw_tankard", "tankard_hold",
           "demo_thumb", "CROWD_KINDS", "CROWD_HEIGHTS", "CROWD_ACTIONS", "crowd_mats"]

TAU = math.tau
CROWD_KINDS = ("dwarf", "goblin", "kobold", "satyr", "elf", "harpy", "minotaur")
CROWD_HEIGHTS = {k: B.CAST_HEIGHTS[k] for k in CROWD_KINDS}
CROWD_ACTIONS = ("idle", "cheer", "film", "lower", "turn_away", "laugh", "tankard", "sit_table", "talk")
CRYSTAL_GLOW = "#5fe0ff"          # cold, arcane (STYLE: warm light is reserved for kindness)
CRYSTAL_REC = "#ff3b3b"


# ========================================================================================
# the scrying crystal
# ========================================================================================

def _crystal_outline(w, h):
    """A long hexagonal crystal slab (pointed top and bottom), centred at (0, 0)."""
    return [(0.0, -h * 0.5), (w * 0.5, -h * 0.30), (w * 0.5, h * 0.30), (0.0, h * 0.5), (-w * 0.5, h * 0.30), (-w * 0.5, -h * 0.30)]


def draw_scrying_crystal(cr, x, y, size=1.0, angle=0.0, light=None, *, face=1.0, glow=1.0, rec=True, t=0.0,
                         thumb=None, handle=True, detail=2, lw=None):
    """A hand-held scrying crystal: a long hexagonal crystal slab in a brass collar on a short
    wooden handle (like a hand-mirror). (x, y) = the grip on the handle; the crystal stands
    above it (angle tilts it, rad). size 1.0 = 62 px tall (handle included) at scale 1.

    face   +1 we see its face (the scrying side: the reflected fight, `thumb`), -1 its back
           (cold faceted glow), in between it turns edge-on (width x |face|)
    glow   0..1 brightness (lowering a crystal dims it)
    rec    the tiny red recording rune (it pulses with t)
    thumb  callback thumb(cr, w, h): draw the reflected scene in the box (0, 0, w, h) -- it is
           clipped to the crystal's face and tinted; see crystal_feed()
    Returns the crystal centre (x, y) in the caller's coordinates (for the glow / face light)."""
    L = light or B.LIGHTS["neutral"]
    lw = lw if lw is not None else B.line_for(B.LINE * 0.8, B.device_scale(cr) * size)
    w, h = 30.0, 42.0
    fw = max(0.12, abs(face))
    cr.save()
    cr.translate(x, y)
    cr.rotate(angle)
    cr.scale(size, size)
    cy = -16.0 - h * 0.5                     # the crystal's centre above the grip
    brass = B.pal(L, "#B8913F", sheen=0.8)
    wood = B.pal(L, "#6E4A2E")
    if handle:
        cr.new_path()
        core.rounded_rect(cr, -4.5 - lw, -18.0 - lw, 9.0 + 2 * lw, 22.0 + 2 * lw, 4.0)
        core.src(cr, wood.line)
        cr.fill()
        core.rounded_rect(cr, -4.5, -18.0, 9.0, 22.0, 3.5)
        core.src(cr, wood.lit)
        cr.fill()
    cr.save()
    cr.translate(0.0, cy)
    cr.scale(fw, 1.0)
    outline = _crystal_outline(w + 6.0, h + 6.0)
    body = _crystal_outline(w, h)
    # brass collar (outline ring) + the slab
    cr.new_path()
    core.polygon(cr, B.offset_closed(outline, lw / max(fw, 0.3)))
    core.src(cr, brass.line)
    cr.fill()
    core.polygon(cr, outline)
    core.src(cr, brass.lit)
    cr.fill()
    g = clamp(glow)
    gc = core.col(CRYSTAL_GLOW)
    if face > 0.05:
        # the scrying face: deep teal glass, the reflected scene, a cold sheen
        cr.new_path()
        core.polygon(cr, body)
        core.src(cr, core.mix("#0b2a33", CRYSTAL_GLOW, 0.25 + 0.35 * g))
        cr.fill_preserve()
        cr.save()
        cr.clip()
        if thumb is not None and detail >= 1:
            cr.save()
            cr.translate(-w * 0.5, -h * 0.5)
            thumb(cr, w, h)
            cr.restore()
            cr.set_source_rgba(gc[0], gc[1], gc[2], 0.22 * g)       # the cold scrying tint
            cr.paint()
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.18 + 0.12 * g)            # glare streak
        core.polygon(cr, [(-w * 0.5, -h * 0.05), (-w * 0.1, -h * 0.5), (w * 0.05, -h * 0.5), (-w * 0.5, h * 0.12)])
        cr.fill()
        cr.restore()
    else:
        # the back: cold faceted crystal
        cr.new_path()
        core.polygon(cr, body)
        core.src(cr, core.mix("#16404a", CRYSTAL_GLOW, 0.35 + 0.4 * g))
        cr.fill()
        facets = [[(0.0, -h * 0.5), (0.0, h * 0.5)], [(-w * 0.5, -h * 0.3), (0.0, -h * 0.12), (w * 0.5, -h * 0.3)],
                  [(-w * 0.5, h * 0.3), (0.0, h * 0.12), (w * 0.5, h * 0.3)]]
        if detail >= 1:
            B.detail_lines(cr, facets, 1.0, core.mix("#0b2a33", CRYSTAL_GLOW, 0.2), 0.6, taper=(1.0, 1.0, 1.0))
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.3 * g)
        core.polygon(cr, [(-w * 0.5, -h * 0.3), (0.0, -h * 0.5), (0.0, -h * 0.12), (-w * 0.5, h * 0.05)])
        cr.fill()
    cr.restore()
    if rec:
        # the tiny red recording rune: a glowing red sigil (a diamond on two legs), pulsing; it
        # shows on both sides (it glows through the crystal)
        pulse = 0.65 + 0.35 * (0.5 + 0.5 * math.sin(t * TAU * 1.2))
        rx, ry = (w * 0.22 * fw * (1 if face >= 0 else -1), cy - h * 0.27)
        rc = core.col(CRYSTAL_REC)
        cr.set_source_rgba(rc[0], rc[1], rc[2], 0.30 * pulse)
        core.circle(cr, rx, ry, 5.2)
        cr.fill()
        cr.set_source_rgba(min(1.0, rc[0] + 0.1), rc[1] + 0.25, rc[2] + 0.2, 0.95 * pulse)
        cr.set_line_width(1.3)
        cr.set_line_cap(1)
        cr.set_line_join(1)
        cr.move_to(rx, ry - 3.4)
        cr.line_to(rx + 2.2, ry - 1.0)
        cr.line_to(rx, ry + 1.4)
        cr.line_to(rx - 2.2, ry - 1.0)
        cr.close_path()
        cr.move_to(rx, ry + 1.4)
        cr.line_to(rx - 2.0, ry + 3.6)
        cr.move_to(rx, ry + 1.4)
        cr.line_to(rx + 2.0, ry + 3.6)
        cr.stroke()
    cx, cy2 = cr.user_to_device(0.0, cy)
    cr.restore()
    return cr.device_to_user(cx, cy2)


class CrystalHold:
    """A hold callback (Arm(hold=...)) that draws a scrying crystal upright in the hand and
    remembers where it went, so its cold light can be painted over the holder afterwards:

        hold = ch.crystal_hold(face=-1.0)
        rig = ch.draw_crowd(..., pose with Arm("raise_crystal_film", hold=hold) ...)
        hold.light(cr)          # draw_crowd / draw_pixie callers: crowd does this itself
    """

    def __init__(self, face=1.0, glow=1.0, rec=True, thumb=None, size=1.0, t=0.0, tilt=0.0, light=None):
        self.face, self.glow, self.rec, self.thumb, self.size, self.t, self.tilt = face, glow, rec, thumb, size, t, tilt
        self.lt = light
        self.center_dev = None
        self.scale_dev = 1.0

    def __call__(self, cr, frame):
        cr.save()
        cr.rotate(-frame.angle + self.tilt)
        sc = self.size * max(frame.scale, 1.0) / 43.0      # the crystal stands ~1.45 hand lengths tall
        c = draw_scrying_crystal(cr, 0.0, 2.0, sc, 0.0, self.lt, face=self.face, glow=self.glow, rec=self.rec,
                                 t=self.t, thumb=self.thumb)
        self.center_dev = cr.user_to_device(*c)
        self.scale_dev = B.device_scale(cr) * sc
        cr.restore()

    def light(self, cr, strength=1.0):
        """Paint the crystal's cold glow (additive) round it -- it lights the holder's face."""
        if self.center_dev is None or self.glow <= 0.01:
            return
        x, y = cr.device_to_user(*self.center_dev)
        k = self.scale_dev / max(B.device_scale(cr), 1e-6)
        g = clamp(self.glow) * strength
        fx.glow(cr, x, y, 70.0 * k, CRYSTAL_GLOW, 0.30 * g, core_r=12.0 * k, core_alpha=0.5 * g)


def crystal_hold(face=1.0, glow=1.0, rec=True, thumb=None, size=1.0, t=0.0, tilt=0.0, light=None):
    """A CrystalHold: a hold callback drawing the scrying crystal upright in a hand."""
    return CrystalHold(face, glow, rec, thumb, size, t, tilt, light)


def crystal_feed(draw_fn, w=96, h=72, bg="#1a2a33"):
    """Render the reflected scene ONCE (per frame) into a small surface and return a thumb
    callback that paints it into every crystal's face: draw_fn(cr, w, h) draws the scene (e.g.
    the brawl, small) into a w x h box. Cheap per crystal (one image paint)."""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(w), int(h))
    c = cairo.Context(surf)
    core.src(c, bg)
    c.paint()
    draw_fn(c, w, h)
    surf.flush()

    def thumb(cr, tw, th):
        cr.save()
        cr.scale(tw / w, th / h)
        cr.set_source_surface(surf, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_GOOD)
        cr.paint()
        cr.restore()

    thumb.surface = surf
    return thumb


def demo_thumb(cr, w, h):
    """A generic reflected-fight thumbnail for sheets: two silhouettes squaring up."""
    core.vgrad(cr, 0, 0, w, h, ["#2a3a48", "#16222c"])
    for (x, c, r) in ((w * 0.36, "#5b7a3a", 0.32), (w * 0.64, "#6a4a34", 0.4)):
        core.src(cr, c)
        core.ellipse(cr, x, h * 0.62, w * 0.1, h * r)
        cr.fill()
        core.circle(cr, x, h * (0.62 - r - 0.02), w * 0.09)
        cr.fill()


# ========================================================================================
# the tankard (tavern)
# ========================================================================================

def draw_tankard(cr, x, y, size=1.0, light=None, *, foam=1.0, lw=None, slosh=0.0):
    """A pewter tankard with a handle and a head of foam; (x, y) = its handle grip, upright.
    size 1.0 = 34 px tall."""
    L = light or B.LIGHTS["neutral"]
    lw = lw if lw is not None else B.line_for(B.LINE * 0.8, B.device_scale(cr) * size)
    pw = B.pal(L, "#9AA0A6", sheen=0.7)
    cr.save()
    cr.translate(x, y)
    cr.scale(size, size)
    body = [(4.0, -16.0), (26.0, -16.0), (27.0, 16.0), (3.0, 16.0)]
    cr.new_path()
    core.polygon(cr, B.offset_closed(body, lw))
    core.circle(cr, 2.0, 0.0, 9.0 + lw)
    core.src(cr, pw.line)
    cr.fill()
    core.src(cr, pw.shadow)
    core.circle(cr, 2.0, 0.0, 9.0)
    cr.fill()
    core.src(cr, B.pal(L, "#3a3530").lit)
    core.circle(cr, 2.0, 0.0, 5.0)
    cr.fill()
    cr.new_path()
    core.polygon(cr, body)
    B.shade(cr, Path(cr), Mat.of("#9AA0A6", sheen=0.7), L, lw, outline=False, size=24.0, rim=0.6)
    core.src(cr, pw.line, 0.8)
    for yy in (-9.0, 10.0):
        cr.rectangle(4.0, yy, 22.5, 1.6)
    cr.fill()
    if foam > 0:
        fp = B.pal(L, "#F1E8D2")
        cr.new_path()
        for i, (fx_, fy, r) in enumerate(((7.0, -17.0, 5.5), (14.0, -19.5 - slosh, 6.5), (21.5, -17.5, 5.5), (25.0, -14.0, 3.5))):
            core.circle(cr, fx_, fy, (r + lw) * foam)
        core.src(cr, pw.line)
        cr.fill()
        for i, (fx_, fy, r) in enumerate(((7.0, -17.0, 5.5), (14.0, -19.5 - slosh, 6.5), (21.5, -17.5, 5.5), (25.0, -14.0, 3.5))):
            core.circle(cr, fx_, fy, r * foam)
        core.src(cr, fp.lit)
        cr.fill()
    cr.restore()


def tankard_hold(foam=1.0, size=1.0, light=None, slosh=0.0):
    """Hold callback: a tankard upright in the hand (by its handle)."""
    def hold(cr, frame):
        cr.save()
        cr.rotate(-frame.angle)
        sc = size * max(frame.scale, 1.0) / 50.0 if frame.scale > 8 else size
        draw_tankard(cr, -6.0 * sc, 0.0, sc, light, foam=foam, slosh=slosh)
        cr.restore()
    return hold


# ========================================================================================
# the synchronized laugh
# ========================================================================================

def laugh_sync(t, bpm=280.0, t0=0.0):
    """The uncanny tavern laugh: everyone given the same t gets the IDENTICAL value -- one
    "HA" pulse per beat (default 280 per minute = 4.7 Hz), never a different phase, never a
    different volume. Returns 0..1 (mouth/head pulse); use it as pose.laugh_pulse."""
    ph = (t - t0) * bpm / 60.0
    u = ph - math.floor(ph)
    return 0.55 + 0.45 * (math.sin(math.pi * min(1.0, u / 0.55)) ** 2 if u < 0.55 else 0.0)


# ========================================================================================
# specs: deterministic random creatures
# ========================================================================================

_SKINS = {
    # SPEC §4 "no one may read as a plain human": dwarves are granite-ruddy (with stone flecks,
    # see _head_dwarf), elves moon-pale / lilac / sage -- never human peach
    "dwarf": ["#BE7E68", "#AE7464", "#B88672", "#A47A6E", "#B4806A"],
    "goblin": ["#8FAE4A", "#7FA040", "#A3B85A", "#6E9A52"],
    "kobold": ["#C8643A", "#B8562E", "#D07A3A", "#9A5A8A"],
    "satyr": ["#8E6A4A", "#A07A52", "#6E5240", "#B08A60"],
    "elf": ["#D2CAE6", "#C6BEE0", "#DCCAD8", "#C2CCE2", "#CFD0E8"],     # moon-lilac, rose-moon, periwinkle
    "harpy": ["#8A7A9A", "#9A8058", "#5E6A7E", "#A0786A"],
}
_CLOTH = ["#6E4A3A", "#4E5E3A", "#3E4A6A", "#7A3A3A", "#5A4A6E", "#8A6A3A", "#4A5A5A", "#6A5A4A", "#7A6E5A", "#3A5048"]
# hose, hoods, caps and belts: earthy wool and leather (no bright blue legs -- they read as jeans)
_HOSE = ["#5A4636", "#6A5A40", "#4E5A3C", "#5E5650", "#6E3E34", "#4A4038", "#7A6A50", "#55504A", "#3E4A44"]
_HAIR = ["#2B2624", "#5E3A24", "#8A5A2A", "#B8B0A0", "#D8C08A", "#3A2A40", "#A0522D", "#E8E0D0"]
_ACCENT = ["#B8913F", "#9AA0A6", "#C0392B", "#2E6E8A", "#7A9A3A", "#8A4A8A"]


@dataclass
class CrowdSpec:
    """One extra: its kind, a size factor, colours and features (all from the seed)."""
    kind: str
    seed: int
    size: float = 1.0
    skin: str = "#888888"
    cloth: str = "#6E4A3A"
    cloth2: str = "#4E5E3A"
    hair: str = "#2B2624"
    accent: str = "#B8913F"
    eye: str = "#C08A3A"
    hat: str = ""            # "", "hood", "cap", "hood_down"
    beard: bool = False
    ears: float = 1.0
    horns: float = 1.0
    variant: str = ""        # minotaur colour variant
    features: dict = field(default_factory=dict)


def random_creature(seed, kind=None):
    """A deterministic random extra: same seed (and kind) -> the same creature every time.
    kind: one of CROWD_KINDS or None (picked from the seed; minotaurs are rare)."""
    rng = random.Random(seed * 7919 + 13)
    if kind is None:
        kind = rng.choices(CROWD_KINDS, weights=(5, 6, 5, 3, 4, 2, 1))[0]
    sp = CrowdSpec(kind=kind, seed=seed)
    sp.size = 0.92 + 0.16 * rng.random()
    sp.skin = rng.choice(_SKINS.get(kind, ["#888888"]))
    sp.cloth = rng.choice(_CLOTH)
    sp.cloth2 = rng.choice([c for c in _HOSE if c != sp.cloth])
    sp.hair = rng.choice(_HAIR)
    sp.accent = rng.choice(_ACCENT)
    sp.eye = rng.choice(["#C08A3A", "#6E8A4A", "#5A7FA0", "#8A5A2A", "#D4A030", "#7A5AA0"])
    sp.ears = 0.8 + 0.4 * rng.random()
    sp.horns = 0.8 + 0.4 * rng.random()
    if kind == "dwarf":
        sp.hat = rng.choice(["hood", "cap", ""])
        sp.beard = True
        sp.hair = rng.choice(["#4A3020", "#5E3A24", "#8A5A2A", "#B8B0A0", "#D8C08A", "#A0522D", "#E8E0D0", "#6B4A3A"])
    elif kind == "goblin":
        sp.hat = rng.choice(["hood", "", "", "cap"])
    elif kind == "elf":
        sp.hat = rng.choice(["hood", "", ""])
        sp.hair = rng.choice(["#D8B060", "#8A4A2A", "#3A2A20", "#22202A", "#B0602A", "#E0D8C8"])
        sp.features["cloak"] = rng.random() < 0.45
    elif kind == "satyr":
        sp.beard = rng.random() < 0.7
    elif kind == "minotaur":
        from .minotaur import MINOTAUR_VARIANTS
        sp.variant = rng.choice(sorted(MINOTAUR_VARIANTS))
    return sp


# ========================================================================================
# poses
# ========================================================================================

@dataclass
class CrowdPose(F.FolkPose):
    """FolkPose plus the crowd's action:
    action      one of CROWD_ACTIONS (see crowd_pose for what each does)
    amount      0..1 blend into the action from idle (the "one by one" lowering, turning)
    laugh_pulse the synchronized laugh pulse (laugh_sync(t)) -- identical for everyone
    crystal     a CrystalHold (film / lower / turn_away); built for you by crowd_pose
    tankard     draw a tankard in the near hand (tavern)
    table_h     sit_table: the table top above the ground
    """
    mood: object = "neutral"
    action: str = "idle"
    amount: float = 1.0
    laugh_pulse: float = 0.0
    crystal: object = None
    tankard: bool = False
    table_h: float = 150.0


CrowdRig = F.FolkRig


def crowd_pose(action, t, spec=None, **kw):
    """A ready CrowdPose for an action at time t (kw override any field, e.g. facing, yaw,
    amount, thumb= for the crystal's reflected scene, glow= for its brightness).

    idle       standing about: weight shifts, glances round (seeded)
    cheer      an arm (or both) pumping in the air, shouting, grinning
    film       raise_crystal_film: the crystal held up at eye level, its face toward the holder
               (you see the reflected fight over their shoulder when they face away; their face
               lit by its cold glow when they face you), a red recording rune
    lower      lower_crystal: the crystal comes down to the belly, dimming, the head drops
    turn_away  they turn their back (yaw swings toward 180 deg as amount -> 1), eyes on the
               lowered crystal: the circle dissolves
    laugh      the synchronized tavern laugh (laugh_sync(t): identical for everyone), tankard
               raised on the beat
    tankard    holding a tankard at the chest, a slow toast now and then
    sit_table  seated (sit=1, seat at kw.get("seat_h", 70)), forearms on the table at table_h
    talk       lean in and talk: leaning forward, mouth going, an explaining hand
    """
    seed = spec.seed if spec is not None else kw.get("seed", 0)
    thumb = kw.pop("thumb", None)
    glow = kw.pop("glow", 1.0)
    amount = kw.pop("amount", 1.0)
    base = dict(seed=seed)
    look = (0.3 * B.sway(t, 0.13, seed + 31), 0.1 * B.sway(t, 0.11, seed + 37))
    head_turn = 0.25 * B.sway(t, 0.09, seed + 41)
    face_sign = None
    if action == "idle":
        p = CrowdPose(action="idle", look=look, head_turn=head_turn, mood="neutral", **base)
    elif action == "cheer":
        pump = 0.5 + 0.5 * math.sin(t * TAU * 1.6 + seed)
        both = (seed % 3 == 0)
        p = CrowdPose(action="cheer", mood="happy", talk=0.55 + 0.4 * pump, near=Arm("cheer", amt=amount, phase=t * 1.6 + seed * 0.1),
                      far=Arm("cheer", amt=amount, phase=t * 1.6 + 0.3) if both else Arm("rest"), head_nod=0.15, **base)
    elif action in ("film", "lower", "turn_away"):
        p = CrowdPose(action=action, **base)
        face_sign = 1
    elif action == "laugh":
        pulse = laugh_sync(t)
        p = CrowdPose(action="laugh", laugh=amount, laugh_pulse=pulse, mood="happy",
                      near=Arm("tankard", amt=amount, phase=0.55 + 0.45 * pulse), tankard=True, **base)
    elif action == "tankard":
        toast = core.window((t + seed * 0.37) % 9.0, 6.0, 7.6, 0.4, 0.5)
        p = CrowdPose(action="tankard", mood="kind", look=look, near=Arm("tankard", phase=toast), tankard=True, **base)
    elif action == "sit_table":
        p = CrowdPose(action="sit_table", sit=1.0, seat_h=kw.pop("seat_h", 70.0), mood="kind", look=look,
                      near=Arm("on_table"), far=Arm("on_table"), **base)
    elif action == "talk":
        chat = 0.5 + 0.5 * math.sin(t * TAU * 2.3 + seed) * math.sin(t * TAU * 0.37 + seed)
        p = CrowdPose(action="talk", lean=0.45 * amount, talk=clamp(chat) * amount, mood="kind",
                      near=Arm("talk", amt=amount, phase=t * 0.8), head_nod=0.1 * math.sin(t * 2.0 + seed), **base)
    else:
        raise ValueError(f"unknown crowd action {action!r}")
    p = p.with_(**kw)
    if face_sign is not None:
        # the crystal's face points at its holder: we see it when the holder faces away
        yaw = F.yaw_of(p)
        if action == "turn_away":
            yaw = lerp(yaw, math.copysign(math.pi * 0.92, yaw if abs(yaw) > 1e-3 else 1.0), smooth(amount))
            p = p.with_(yaw=yaw)
        fc = clamp(-math.cos(yaw) * 1.4, -1.0, 1.0)
        if action == "film":
            hold = crystal_hold(face=fc, glow=glow * amount + 0.15 * (1 - amount), thumb=thumb, t=t)
            p = p.with_(near=Arm("raise_crystal_film", amt=amount, hold=hold), mood=p.mood if "mood" in kw else "raised",
                        look=(0.0, -0.1), crystal=hold)
        else:
            # lower: the crystal comes down as amount -> 1; turn_away: it is already down (they
            # lowered it earlier), amount only turns them
            down = amount if action == "lower" else 1.0
            dim = glow * (1.0 - 0.75 * down)
            hold = crystal_hold(face=fc, glow=dim, thumb=thumb, t=t, tilt=-0.5 * down)
            p = p.with_(near=Arm("lower_crystal", amt=down, prev="raise_crystal_film", hold=hold),
                        head_nod=-0.5 * down, look=(0.0, 0.7 * down), mood=p.mood if "mood" in kw else "bored",
                        crystal=hold)
    return p


# ========================================================================================
# kinds: builds and materials
# ========================================================================================

BUILDS = {
    "dwarf": F.Build(pelvis_h=104.0, hip_w=24.0, thigh=52.0, shin=48.0, ankle_h=14.0, sh_y=112.0, sh_w=58.0,
                     upper_arm=58.0, forearm=54.0, hand_len=46.0, neck_y=120.0, neck_len=8.0, head_up=18.0, head_fwd=8.0,
                     hunch=0.25, stride=116.0, lift=14.0, bob=3.5, breath=0.24, sit_drop=9.0, sway=1.5, fit=1.0),
    "goblin": F.Build(pelvis_h=96.0, hip_w=16.0, thigh=48.0, shin=46.0, ankle_h=10.0, sh_y=72.0, sh_w=30.0,
                      upper_arm=50.0, forearm=48.0, hand_len=34.0, neck_y=80.0, neck_len=10.0, head_up=26.0, head_fwd=10.0,
                      hunch=0.7, hunch_fwd=10.0, stride=104.0, lift=14.0, bob=3.0, breath=0.28, sit_drop=8.0, sway=1.6, fit=1.048),
    "kobold": F.Build(pelvis_h=86.0, hip_w=14.0, thigh=44.0, shin=42.0, ankle_h=10.0, sh_y=62.0, sh_w=26.0,
                      upper_arm=42.0, forearm=40.0, hand_len=28.0, neck_y=70.0, neck_len=10.0, head_up=22.0, head_fwd=10.0,
                      hunch=0.5, hunch_fwd=8.0, stride=96.0, lift=12.0, bob=3.0, breath=0.3, sit_drop=7.0, sway=1.4, fit=0.965),
    "satyr": F.Build(pelvis_h=200.0, hip_w=22.0, thigh=72.0, shin=72.0, ankle_h=14.0, cannon=58.0, cannon_tilt=0.3,
                     sh_y=124.0, sh_w=46.0, upper_arm=80.0, forearm=76.0, hand_len=54.0, neck_y=136.0, neck_len=18.0,
                     head_up=18.0, head_fwd=8.0, hunch=0.3, stride=160.0, lift=20.0, bob=4.0, breath=0.22, sit_drop=12.0, fit=1.019),
    "elf": F.Build(pelvis_h=216.0, hip_w=20.0, thigh=101.0, shin=99.0, ankle_h=16.0, sh_y=138.0, sh_w=40.0,
                   upper_arm=84.0, forearm=80.0, hand_len=52.0, neck_y=150.0, neck_len=18.0, head_up=20.0, head_fwd=4.0,
                   hunch=0.15, stride=170.0, lift=20.0, bob=3.5, breath=0.22, sit_drop=12.0, fit=1.033),
    "harpy": F.Build(pelvis_h=180.0, hip_w=18.0, thigh=60.0, shin=66.0, ankle_h=12.0, cannon=56.0, cannon_tilt=0.25,
                     sh_y=128.0, sh_w=38.0, upper_arm=80.0, forearm=78.0, hand_len=44.0, neck_y=140.0, neck_len=22.0,
                     head_up=18.0, head_fwd=10.0, hunch=0.45, stride=150.0, lift=18.0, bob=4.0, breath=0.24, sit_drop=12.0, fit=0.966),
}
HEAD_HS = {"dwarf": 1.2, "goblin": 1.25, "kobold": 1.05, "satyr": 1.2, "elf": 1.5, "harpy": 1.15}

_MAT_CACHE = {}


def crowd_mats(spec):
    """Materials for one spec (cached by its colours)."""
    key = (spec.kind, spec.skin, spec.cloth, spec.cloth2, spec.hair, spec.accent)
    m = _MAT_CACHE.get(key)
    if m is None:
        m = _MAT_CACHE[key] = {
            "skin": Mat.of(spec.skin, sss=0.35),
            "cloth": Mat.of(spec.cloth, shadow_k=1.1),
            "cloth2": Mat.of(spec.cloth2, shadow_k=1.1),
            "hair": Mat.of(spec.hair, sheen=0.25),
            "accent": Mat.of(spec.accent, sheen=0.6),
            "boots": Mat.of("#3A2C22", sheen=0.3),
            "horn": Mat.of("#D8C8A8", sheen=0.5, line_k=0.45),
            "hoof": Mat.of("#33292A", sheen=0.4),
            "beak": Mat.of("#D9A040", sheen=0.5),
            "talon": Mat.of("#2E2A26", sheen=0.5),
            "nose": Mat.of(core.mix(spec.skin, "#D9705A", 0.35), sss=0.5),
        }
    return m


# ========================================================================================
# drawing
# ========================================================================================

def draw_crowd(cr, x, y, scale, spec, pose=None, light=None, t=0.0, detail=None, parts=None):
    """Draw one extra (anchor = ground point below the pelvis, or below the seat). The spec's
    size factor multiplies `scale`. Returns a CrowdRig (points: "crystal" when filming).
    A crystal's cold glow is painted over the creature automatically (it lights the face)."""
    pose = pose or CrowdPose()
    sc = scale * spec.size
    if spec.kind == "minotaur":
        rig = _draw_minotaur(cr, x, y, sc, spec, pose, light, t, detail, parts)
    else:
        rig = _draw_folk(cr, x, y, sc, spec, pose, light, t, detail, parts)
    hold = pose.crystal
    if isinstance(hold, CrystalHold) and hold.center_dev is not None and (parts is None or "front" in parts):
        hold.light(cr)
        rig.points["crystal"] = cr.device_to_user(*hold.center_dev)
    return rig


def _draw_minotaur(cr, x, y, sc, spec, pose, light, t, detail, parts):
    from .minotaur import MinotaurPose, draw_minotaur
    mp = MinotaurPose(**{k: getattr(pose, k) for k in ("facing", "turn", "yaw", "sit", "seat_h", "walk", "phase", "lean",
                                                        "hunch", "stance", "head_turn", "head_tilt", "head_nod", "look",
                                                        "mood", "mood2", "mood_mix", "talk", "smile", "laugh", "blink",
                                                        "near", "far", "anchor", "elev", "shadow", "seed")},
                      variant=spec.variant or "black")
    if pose.action == "laugh":
        mp = mp.with_(talk=0.5 + 0.5 * pose.laugh_pulse, head_nod=0.2 + 0.15 * pose.laugh_pulse)
    if pose.tankard:
        mp = mp.with_(near=mp.near.__class__(**{**mp.near.__dict__, "hold": tankard_hold(light=light)}))
    return draw_minotaur(cr, x, y, sc, mp, light, t, detail, parts)


def _draw_folk(cr, x, y, sc, spec, pose, light, t, detail, parts):
    kind = spec.kind
    b = BUILDS[kind]
    M = crowd_mats(spec)
    if pose.action == "laugh":
        lp = pose.laugh_pulse
        pose = pose.with_(talk=0.4 + 0.6 * lp, head_nod=0.25 + 0.2 * lp, laugh=max(pose.laugh, 0.7))
    if pose.tankard and pose.near.hold is None:
        pose = pose.with_(near=Arm(**{**pose.near.__dict__, "hold": tankard_hold(light=light, slosh=2.0 * pose.laugh_pulse)}))
    q = F.begin(cr, x, y, sc, pose, light, t, detail, b, M, parts, height=CROWD_HEIGHTS[kind])
    q.pose = pose
    A = {s: F.solve_arm(q, s, pose.near if s == q.near else pose.far) for s in (-1.0, 1.0)}
    lay = {s: F.arm_layer(q, A[s]) for s in A}
    hands = {}
    K = _KIND[kind]
    if q.want("body") and pose.shadow:
        F.contact(q, b.hip_w * 2.0 + 24.0)
    if q.want("back"):
        K["back"](q, spec)
    for s in (q.far, q.near):
        if lay[s] == "back" and q.want("back"):
            hands[s] = _arm(q, A[s], spec)
    if q.want("body"):
        K["legs"](q, spec)
        K["torso"](q, spec)
    for s in (q.far, q.near):
        if lay[s] == "mid" and q.want("mid"):
            hands[s] = _arm(q, A[s], spec)
    head = K["head"](q, spec, draw=q.want("head"))
    for s in (q.far, q.near):
        if lay[s] == "front" and q.want("front"):
            hands[s] = _arm(q, A[s], spec)
    rig = F.base_rig(q, head)
    el = {s: q.proj.xy(A[s]["wr"]) for s in A}
    rig.hand_near = hands.get(q.near) or B.HandFrame(el[q.near][0], el[q.near][1], 0.0, 1.0, [], el[q.near], False)
    rig.hand_far = hands.get(q.far) or B.HandFrame(el[q.far][0], el[q.far][1], 0.0, 1.0, [], el[q.far], False)
    return F.end(q, rig)


def _arm(q, A, spec):
    """Sleeve (cloth) over the arm, a bare hand; harpies have feathered wing-arms."""
    cr, M, proj = q.cr, q.M, q.proj
    b = q.b
    sh, el, wr = proj.xy(A["sh"]), proj.xy(A["el"]), proj.xy(A["wr"])
    r = {"dwarf": (16.0, 13.0, 11.0), "goblin": (9.0, 7.0, 6.0), "kobold": (8.0, 6.5, 5.5), "satyr": (13.0, 10.0, 8.0),
         "elf": (11.0, 9.0, 7.5), "harpy": (10.0, 8.0, 6.5)}[spec.kind]
    if spec.kind == "harpy":
        # the wing: a curtain of flight feathers hanging from the arm (one shape, scalloped
        # trailing edge; longest at the wrist), then the arm over it, then the hand
        o = proj.xy((0.0, 0.0, 0.0))
        dn = proj.xy((0.0, 1.0, -0.45))
        dx, dy = core.normalize((dn[0] - o[0], dn[1] - o[1]))
        top = [sh, core.lerp_pt(sh, el, 0.5), el, core.lerp_pt(el, wr, 0.5), wr]
        AL = b.upper_arm + b.forearm
        lens = [0.20 * AL, 0.34 * AL, 0.44 * AL, 0.52 * AL, 0.56 * AL]
        tips = [(p[0] + dx * L, p[1] + dy * L) for p, L in zip(top, lens)]
        edge = []
        for i in range(len(tips)):
            edge.append(tips[i])
            if i + 1 < len(tips):
                m_ = core.lerp_pt(tips[i], tips[i + 1], 0.5)
                edge.append((m_[0] - dx * 0.07 * AL, m_[1] - dy * 0.07 * AL))
        wr2 = (wr[0] + (wr[0] - el[0]) * 0.15, wr[1] + (wr[1] - el[1]) * 0.15)
        poly = top[:-1] + [wr2] + [(tips[-1][0] + (wr[0] - el[0]) * 0.12, tips[-1][1] + (wr[1] - el[1]) * 0.12)] + edge[::-1]
        shp, pal = F.smooth_shape(q, poly, M["cloth"], 0.4 * AL, tension=0.55, rim=0.5)
        if q.detail >= 1:
            cr.save()
            shp.add(cr)
            cr.clip()
            B.detail_lines(cr, [[core.lerp_pt(tp, t2, 0.25), t2] for tp, t2 in zip(top[1:], tips[1:])], q.lw * 0.8, pal.line, 0.5,
                           taper=(0.1, 1.0, 0.3))
            cr.restore()
        F.limb(q, [sh, el, wr], r, M["cloth"], r[0] * 1.8, rim=0.5)
        return F.hand(q, A, M["skin"], size=b.hand_len, claw=spec.features.get("claw", "#2E2A26"), finger_w=0.85, palm_w=0.8)
    long_sleeve = spec.kind in ("elf", "goblin")
    cut = core.lerp_pt(el, wr, 0.9 if long_sleeve else 0.55)
    if spec.kind == "satyr":
        F.limb(q, [sh, el, wr], r, M["skin"], r[0] * 1.8, rim=0.5)
    else:
        if not long_sleeve:                  # bare forearm below a rolled sleeve (a long sleeve hides it)
            F.limb(q, [core.lerp_pt(el, wr, 0.35), wr], (r[1] * 0.85, r[2]), M["skin"], r[0] * 1.6, rim=0.4)
        F.limb(q, [sh, el, cut], (r[0] + 2.0, r[1] + 2.0, r[1] + 1.5), M["cloth"], r[0] * 2.0, rim=0.5)
    claw = {"kobold": "#2E2A26", "goblin": "#3A3A2A"}.get(spec.kind)
    fw = {"dwarf": 1.3, "goblin": 0.95, "kobold": 0.9, "satyr": 1.0, "elf": 0.85}.get(spec.kind, 1.0)
    return F.hand(q, A, M["skin"], size=b.hand_len, claw=claw, finger_w=fw, palm_w=fw,
                  finger_len=1.15 if spec.kind in ("goblin", "elf") else 1.0)


# ---- shared garment pieces ---------------------------------------------------------------

def _tunic(q, spec, top_a=0.6, hem=40.0, flare=1.15, mat="cloth", belt=True, cloak=False):
    cr, S, proj = q.cr, q.S, q.proj
    b = q.b
    T = S["T"]
    pel = S["pelvis"]
    h = S["hunch"]
    br = S["br"]
    sit = q.sit
    walk = S["walk"]
    w = b.sh_w
    kn = v_lerp(S["knee"][0], S["knee"][1], 0.5)
    hem_c = v_lerp(v_add(pel, (0.0, hem, 0.0)), v_add(v_lerp(pel, kn, 0.6), (0.0, 10.0, 4.0)), clamp(sit / 0.7))
    sy = b.sh_y
    rings = [(T((0.0, -sy * 0.94 + 4 * h, 4.0 + 6 * h)), w * top_a, w * 0.48), (T((0.0, -sy * 0.82, 2.0)), w * 1.1 + br * 0.5, w * 0.66),
             (T((0.0, -sy * 0.55, 6.0)), w * 1.0 + br * 0.5, w * 0.7), (T((0.0, -sy * 0.25, 4.0)), w * 0.85, w * 0.64),
             (v_add(pel, (0.0, 2.0, 0.0)), w * 0.92, w * 0.66), (hem_c, w * flare + 6 * sit, w * 0.72)]
    if cloak:                                # a long cloak: wider and to the calves
        cal = v_lerp(v_add(pel, (0.0, b.pelvis_h * 0.75, -6.0)), v_add(kn, (0.0, 40.0, 0.0)), clamp(sit / 0.7))
        rings[-1] = (cal, w * 1.5 + 8 * sit, w * 0.95)
    left, right = F.ring_edges(q, rings)
    top = F.shoulder_top(q, rings[0], neck_r=w * 0.3)
    hm = F.hem_curve(q, *rings[-1], n=7, wave=1.2, phase=q.t * 1.3 + walk * S["wc"].phase * 6)
    shp, pal = F.smooth_shape(q, left + hm + right[::-1] + top, q.M[mat], w * 2.0, shadow=0.6)
    if belt:
        c3, a3, z3 = rings[3]
        c4, a4, z4 = rings[4]
        F.belt(q, v_lerp(c3, c4, 0.6), lerp(a3, a4, 0.6) + 2.0, lerp(z3, z4, 0.6) + 2.0, max(3.5, w * 0.08), q.M["cloth2"])
    if q.detail >= 1:
        cr.save()
        shp.add(cr)
        cr.clip()
        lines = []
        c4, a4, z4 = rings[4]
        c5, a5, z5 = rings[-1]
        for phi in (-0.8, 0.0, 0.8):
            if proj.depth((math.sin(phi), 0.0, math.cos(phi))) > 0.2:
                lines.append([proj.xy(v_add(c4, (math.sin(phi) * a4, 8.0, math.cos(phi) * z4))),
                              proj.xy(v_add(c5, (math.sin(phi * 1.1) * a5, -2.0, math.cos(phi) * z5)))])
        if lines:
            B.detail_lines(cr, lines, q.lw * 0.9, pal.line, 0.4, taper=(0.05, 0.9, 0.4))
        cr.restore()
    return shp, pal


def _legs_plain(q, spec, r=(14.0, 10.0, 8.0), mat="cloth2", boot_len=30.0, boot_w=10.0, boots="boots"):
    F.legs(q, list(r), q.M[mat], r[0] * 1.8)
    F.feet(q, q.M[boots], size=r[2] * 2.0, length=boot_len, width=boot_w, height=boot_w * 1.1, shaft=r[2] * 2.0,
           shaft_r=r[2] + 1.5)


def _legs_goat(q, spec, r=(22.0, 15.0, 7.0, 6.0), mat="skin"):
    F.digi_legs(q, r, q.M[mat], r[0] * 1.5)
    groups = []
    for f in q.S["feet"]:
        g = f["ground"]
        groups.append(F.blob_pts(q.proj, (g[0], g[1] - 6.0, g[2] + 4.0), 7.5, 6.5, 10.0, 10))
    F.hull_union(q, groups, q.M["hoof"], 14.0, rim=0.4)


def _legs_bird(q, spec):
    """Harpy: feathered thighs (plumage 'breeches'), scaly yellow shanks, dark talons."""
    cr = q.cr
    F.digi_legs(q, (16.0, 10.0, 5.5, 5.0), q.M["beak"], 18.0, contour=False)
    groups = []
    for f in q.S["feet"]:
        hip, kn = f["hip"], f["knee"]
        groups.append(F.blob_pts(q.proj, hip, 17.0, 14.0, 17.0, 10) + F.blob_pts(q.proj, v_lerp(hip, kn, 0.8), 14.0, 12.0, 14.0, 10)
                      + [q.proj.xy(v_add(kn, (0.0, 14.0, -4.0)))])
    F.hull_union(q, groups, q.M["cloth"], 26.0, tension=0.7, rim=0.5)
    lines = []
    for f in q.S["feet"]:
        g = f["ground"]
        for (dx, dz) in ((-7.0, 14.0), (0.0, 17.0), (7.0, 14.0), (0.0, -9.0)):
            lines.append([q.proj.xy((g[0], g[1] - 5.0, g[2])), q.proj.xy((g[0] + dx, g[1] - 1.0, g[2] + dz))])
    B.detail_lines(cr, lines, q.lw * 2.0, q.P(q.M["talon"]).lit, 1.0, taper=(1.0, 0.9, 0.3))


def _no_back(q, spec):
    pass


# ---- heads -------------------------------------------------------------------------------

def _hx(q, spec):
    HS = HEAD_HS[spec.kind] * (0.95 + 0.1 * spec.ears * 0)
    P, nz, D, W = F.head_xf(q, HS)
    e = F.expr_of(q.pose)
    hyaw = q.S["head_yaw"]
    near = -1.0 if math.sin(hyaw) >= 0 else 1.0
    return HS, P, nz, D, W, e, near


def _eyes(q, spec, P, nz, e, near, pos, rx, ry, HS, **kw):
    out = []
    pal = q.P(q.M["skin"])
    for s in (-near, near):
        ec = F.eye_at(q, P, nz, s, e, (s * pos[0], pos[1], pos[2]), rx * HS, ry * HS, iris=spec.eye, skin=spec.skin,
                      line=pal.line, crease=0.0, bags=0.0, **kw)
        out.append(ec or P((s * pos[0], pos[1], pos[2])))
    return out


def _brows(q, spec, P, nz, e, near, x0, x1, y, z0, z1, w=7.0, mat="hair"):
    cr = q.cr
    outs, shapes = [], []
    for s in (-near, near):
        if nz((s * 0.4, -0.5, 0.75)) < -0.1:
            continue
        sh, so = B.taper_paths(cr, F.brow_pts(P, s, e, near, x0, x1, y, z0, z1, 12.0, 10.0), w, w * 0.45, q.lw * 0.8)
        shapes.append(sh)
        outs.append(so)
    if shapes:
        B.fill_outlines(cr, outs, q.P(q.M[mat]).line)
        for sh in shapes:
            sh.add(cr)
        core.src(cr, q.P(q.M[mat]).lit)
        cr.fill()


def _pts(P, spec, q, eyes, mouth, top):
    return {"center": P((0.0, 0.0, 0.0)), "mouth": mouth, "nose": mouth, "eyes": eyes, "top": top}


def _ear_pair(q, P, sides, root, tip, w0, mat="skin", droop=0.0, inner=None):
    """Two ears as one union (sides: which to draw now)."""
    if not sides:
        return
    cr = q.cr
    lw = q.lw * 0.9
    outs, shapes, inn = [], [], []
    for s in sides:
        tw = 0.05 * math.sin(q.t * 1.6 + s * 2.0 + q.pose.seed)
        r = (s * root[0], root[1], root[2])
        tp = (s * tip[0], tip[1] + droop + tw * 20.0, tip[2])
        mid_hi = v_lerp(r, tp, 0.5)
        pts = [P((r[0], r[1] - w0, r[2])), P((mid_hi[0], mid_hi[1] - w0 * 0.7, mid_hi[2])), P(tp),
               P((mid_hi[0], mid_hi[1] + w0 * 0.5, mid_hi[2])), P((r[0], r[1] + w0, r[2]))]
        sh, so = B.smooth_paths(cr, pts, lw, 0.75)
        shapes.append(sh)
        outs.append(so)
        if inner and q.detail >= 1:
            inn.append([P(v_lerp(r, tp, 0.1)), P((mid_hi[0], mid_hi[1] - w0 * 0.35, mid_hi[2])), P(v_lerp(r, tp, 0.85)),
                        P((mid_hi[0], mid_hi[1] + w0 * 0.2, mid_hi[2]))])
    pal = q.P(q.M[mat])
    B.fill_outlines(cr, outs, pal.line)
    for sh in shapes:
        sh.add(cr)
    q.shade(Path(cr), q.M[mat], lw=lw, outline=False, size=w0 * 1.6, rim=0.6)
    if inn:
        cr.new_path()
        for p in inn:
            core.smooth_closed(cr, p, 0.8)
        core.src(cr, inner, 0.55)
        cr.fill()


def _hood(q, P, nz, facing_away, mat, r=38.0, hole=(29.0, 32.0), hole_z=22.0):
    """A hood up over the head with the face showing through its opening (see faun._hood)."""
    cr, lw = q.cr, q.lw
    outer = core.convex_hull(F.ellipsoid2d(P, (0.0, -10.0, -6.0), r, r, r, 16) + F.ellipsoid2d(P, (0.0, 14.0, -12.0), r * 0.8, r * 0.5, r * 0.7, 10)
                             + [P((0.0, -r * 0.7, -r * 1.35))])
    hl = None
    if not facing_away and nz((0.0, 0.0, 1.0)) > 0.05:
        hl = F.clamp_into(outer, F.ellipsoid2d(P, (0.0, 0.0, hole_z), hole[0], hole[1], 12.0, 14), 0.94)
        if F.area2(hl) * F.area2(outer) > 0:
            hl = hl[::-1]
    pal = q.P(q.M[mat])
    cr.new_path()
    core.smooth_closed(cr, B.offset_closed(outer, lw), 0.85)
    if hl:
        core.smooth_closed(cr, B.offset_closed(hl, -lw), 0.9)
    core.src(cr, pal.line)
    cr.fill()
    core.smooth_closed(cr, outer, 0.85)
    if hl:
        core.smooth_closed(cr, hl, 0.9)
    q.shade(Path(cr), q.M[mat], outline=False, size=r * 1.4, shadow=0.75)
    return hl


def _cap_round(q, P, D, mat, y=-26.0, r=31.0, ry=13.0):
    """A soft medieval felt cap: a brimless dome rising to a floppy peak that leans back (a
    round cap with a brim read as a modern flat cap -- SPEC §0.1). F.dome_cap keeps its back
    from ever covering the face. P / D: the head's transforms from _hx / head_xf."""
    c = (0.0, y + ry * 0.55, -4.0)
    peak = (0.0, y - ry * 1.9, -r * 0.62)
    F.dome_cap(q, P, D, c, r, ry * 1.3, q.M[mat], r, brim=0.6, rim=0.7, extra=[peak])


def _mouth(q, P, nz, e, pos, w, spec, HS):
    pal = q.P(q.M["skin"])
    F.mouth_at(q, P, nz, pos, w * HS, e, clamp(q.pose.talk), skin=spec.skin, line=pal.line)


# goblin: big head, huge sideways ears, long pointed nose, sly grin
def _head_goblin(q, spec, draw=True):
    HS, P, nz, D, W, e, near = _hx(q, spec)
    pts = _pts(P, spec, q, [P((s * 15.0, -6.0, 26.0)) for s in (-near, near)], P((0.0, 18.0, 28.0)), P((0.0, -36.0, 0.0)))
    if not draw:
        return pts
    away = nz((0.0, 0.0, 1.0)) < -0.25
    behind = {s: D((s * 30.0, -4.0, -2.0)) < D((0.0, -4.0, -2.0)) - 2.0 for s in (-1.0, 1.0)}
    ear = ((28.0, -6.0, -2.0), (74.0 * spec.ears, -16.0, -10.0), 12.0)
    _ear_pair(q, P, [s for s in (-1.0, 1.0) if behind[s]], *ear, inner="#C77A6A", droop=6.0 * (1 - spec.ears))
    hood_up = spec.hat == "hood"
    F.hull_union(q, [F.ellipsoid2d(P, (0.0, -6.0, 0.0), 32.0, 30.0, 30.0, 16), F.ellipsoid2d(P, (0.0, 12.0, 10.0), 26.0, 16.0, 22.0, 12),
                     F.blob_pts(q.proj, q.S["neck_top"], 9.0, 8.0, 8.0, 10)], q.M["skin"], 60.0)
    hl = None
    if hood_up:
        hl = _hood(q, P, nz, away, "cloth2", r=36.0, hole=(30.0, 31.0))
    if not away:
        if hl is not None:
            q.cr.save()
            q.cr.new_path()
            core.smooth_closed(q.cr, hl, 0.9)
            q.cr.clip()
        pts["eyes"] = _eyes(q, spec, P, nz, e, near, (15.0, -6.0, 26.0), 10.0, 11.0, HS, lid_add=0.05)
        _brows(q, spec, P, nz, e, near, 4.0, 26.0, -18.0, 30.0, 22.0, 6.0, "skin")
        if hl is not None:
            q.cr.restore()
        # long pointy nose
        if nz((0.0, 0.0, 1.0)) > -0.4:
            nose = [P((0.0, -4.0, 28.0)), P((0.0, 4.0, 40.0)), P((0.0, 8.0, 50.0))]
            sh, so = B.taper_paths(q.cr, nose, 13.0, 3.0, q.lw * 0.9)
            q.shade(sh, q.M["skin"], lw=q.lw * 0.9, outline=so, size=10.0, rim=0.0)
        _mouth(q, P, nz, e.with_(smile=e.smile + 0.35), (0.0, 18.0, 27.0), 22.0, spec, HS)
    _ear_pair(q, P, [s for s in (-1.0, 1.0) if not behind[s]], *ear, inner="#C77A6A", droop=6.0 * (1 - spec.ears))
    if spec.hat == "cap":
        _cap_round(q, P, D, "cloth2", y=-30.0, r=29.0, ry=12.0)
    return pts


# kobold: small reptile, a blunt snout, little horns, big yellow eyes
def _head_kobold(q, spec, draw=True):
    HS, P, nz, D, W, e, near = _hx(q, spec)
    pts = _pts(P, spec, q, [P((s * 14.0, -8.0, 22.0)) for s in (-near, near)], P((0.0, 14.0, 44.0)), P((0.0, -30.0, 0.0)))
    if not draw:
        return pts
    away = nz((0.0, 0.0, 1.0)) < -0.25
    cr = q.cr
    horns = []
    for s in (-1.0, 1.0):
        sp_ = [P((s * 12.0, -24.0, -4.0)), P((s * 18.0 * spec.horns, -36.0 * spec.horns, -16.0)), P((s * 18.0 * spec.horns, -40.0 * spec.horns, -28.0))]
        horns.append(B.taper_paths(cr, sp_, 9.0, 2.0, q.lw * 0.8))
    B.fill_outlines(cr, [o for _, o in horns], q.P(q.M["horn"]).line)
    for sh, _o in horns:
        sh.add(cr)
    q.shade(Path(cr), q.M["horn"], lw=q.lw * 0.8, outline=False, size=7.0, rim=0.7)
    F.hull_union(q, [F.ellipsoid2d(P, (0.0, -6.0, -2.0), 26.0, 26.0, 28.0, 16), F.ellipsoid2d(P, (0.0, 8.0, 30.0), 18.0, 13.0, 20.0, 12),
                     F.blob_pts(q.proj, q.S["neck_top"], 8.0, 8.0, 8.0, 10)], q.M["skin"], 50.0)
    if not away:
        pts["eyes"] = _eyes(q, spec, P, nz, e, near, (14.0, -8.0, 22.0), 11.0, 12.5, HS, pupil_aspect=0.55)
        pal = q.P(q.M["skin"])
        sm = e.smile
        op = clamp(max(q.pose.talk, e.open))
        lines = []
        for s in (-1.0, 1.0):
            if nz((s * 0.5, 0.2, 0.8)) > -0.1:
                lines.append([P((s * 16.0, 10.0 - sm * 4.0, 18.0)), P((s * 10.0, 13.0 + op * 3, 34.0)), P((0.0, 14.0 + op * 5, 47.0))])
                lines.append([P((s * 5.0, 2.0, 48.0)), P((s * 6.0, 3.0, 47.0))])
        B.detail_lines(cr, lines, q.lw * 1.1, pal.line, 0.95, taper=(0.5, 1.0, 0.6))
        if op > 0.1:
            m = P((0.0, 16.0, 40.0))
            cr.new_path()
            core.ellipse(cr, m[0], m[1] + op * 2.0, 6.0 * HS, 3.0 * op * HS)
            core.src(cr, "#4A1E22")
            cr.fill()
        _brows(q, spec, P, nz, e, near, 5.0, 22.0, -20.0, 26.0, 20.0, 5.0, "skin")
    return pts


# satyr: ram horns, pointed ears, beard, goat muzzle (adult cousin of the faun)
def _head_satyr(q, spec, draw=True):
    HS, P, nz, D, W, e, near = _hx(q, spec)
    pts = _pts(P, spec, q, [P((s * 14.0, -8.0, 24.0)) for s in (-near, near)], P((0.0, 20.0, 32.0)), P((0.0, -40.0, -2.0)))
    if not draw:
        return pts
    away = nz((0.0, 0.0, 1.0)) < -0.25
    cr = q.cr
    behind = {s: D((s * 28.0, -6.0, -4.0)) < D((0.0, -6.0, -4.0)) - 2.0 for s in (-1.0, 1.0)}
    ear = ((27.0, -6.0, -4.0), (50.0 * spec.ears, -12.0, -10.0), 7.0)
    _ear_pair(q, P, [s for s in (-1.0, 1.0) if behind[s]], *ear)
    F.hull_union(q, [F.ellipsoid2d(P, (0.0, -10.0, -4.0), 28.0, 28.0, 30.0, 16), F.ellipsoid2d(P, (0.0, 10.0, 22.0), 15.0, 13.0, 16.0, 12),
                     F.blob_pts(q.proj, q.S["neck_top"], 12.0, 8.0, 11.0, 10)], q.M["skin"], 60.0)
    if not away:
        pts["eyes"] = _eyes(q, spec, P, nz, e, near, (14.0, -8.0, 24.0), 9.5, 11.0, HS, lid_add=0.08)
        _brows(q, spec, P, nz, e, near, 4.0, 24.0, -20.0, 28.0, 20.0, 7.0)
        n0 = P((0.0, 6.0, 38.0))
        cr.new_path()
        core.ellipse(cr, n0[0], n0[1], 5.0 * HS, 3.5 * HS)
        core.src(cr, "#3A2A26")
        cr.fill()
        if spec.beard:
            sw = 1.5 * math.sin(q.t * 1.4 + spec.seed)
            bd = [P((s * 14.0, 12.0, 18.0)) for s in (-1.0, 1.0)] + [P((0.0, 18.0, 30.0)), P((sw, 40.0, 22.0)), P((sw * 1.3, 46.0, 16.0))]
            shp, so, _ = B.hull_paths(cr, bd, q.lw * 0.9)
            q.shade(shp, q.M["hair"], lw=q.lw * 0.9, outline=so, size=14.0, rim=0.5)
        _mouth(q, P, nz, e, (0.0, 18.0, 31.0), 18.0, spec, HS)
    _ear_pair(q, P, [s for s in (-1.0, 1.0) if not behind[s]], *ear)
    # curled ram horns (one union)
    horns = []
    for s in (-1.0, 1.0):
        k = spec.horns
        sp_ = [P((s * 14.0, -30.0, 2.0)), P((s * 28.0 * k, -40.0, -10.0)), P((s * 40.0 * k, -26.0, -18.0)), P((s * 36.0 * k, -10.0, -10.0)),
               P((s * 28.0 * k, -12.0, 2.0))]
        horns.append(B.taper_paths(cr, sp_, 15.0, 4.0, q.lw * 0.9))
    B.fill_outlines(cr, [o for _, o in horns], q.P(q.M["horn"]).line)
    for sh, _o in horns:
        sh.add(cr)
    q.shade(Path(cr), q.M["horn"], lw=q.lw * 0.9, outline=False, size=12.0, rim=0.7)
    return pts


# elf: long swept ears, almond eyes, long hair, a travelling hood
def _head_elf(q, spec, draw=True):
    HS, P, nz, D, W, e, near = _hx(q, spec)
    pts = _pts(P, spec, q, [P((s * 13.0, -6.0, 24.0)) for s in (-near, near)], P((0.0, 16.0, 26.0)), P((0.0, -36.0, 0.0)))
    if not draw:
        return pts
    away = nz((0.0, 0.0, 1.0)) < -0.25
    cr = q.cr
    behind = {s: D((s * 26.0, -4.0, -2.0)) < D((0.0, -4.0, -2.0)) - 2.0 for s in (-1.0, 1.0)}
    hood_up = spec.hat == "hood"
    # long swept ears; with the hood up they come out THROUGH it (slits in the hood, like the
    # hero elf) -- an elf without visible ears reads as a person in a hood (SPEC §4)
    ear = (((31.0, -6.0, -4.0), (60.0 * spec.ears, -33.0, -16.0), 7.5) if hood_up else
           ((24.0, -4.0, -2.0), (54.0 * spec.ears, -30.0, -14.0), 7.0))
    # long hair: two locks falling behind the ears to the shoulders (behind the head), and
    # from behind a curtain of hair down the nape
    if not hood_up:
        locks = []
        sw = 1.5 * math.sin(q.t * 1.1 + spec.seed)
        for s in (-1.0, 1.0):
            top_ = W((s * 20.0, -12.0, -10.0))
            locks.append(B.taper_paths(cr, [q.proj.xy(top_), q.proj.xy(v_add(top_, (s * 4.0 + sw, 34.0, -4.0))),
                                            q.proj.xy(v_add(top_, (s * 3.0 + sw, 62.0, -8.0)))], 22.0, 8.0, q.lw))
        B.fill_outlines(cr, [o for _, o in locks], q.P(q.M["hair"]).line)
        for sh_, _o in locks:
            sh_.add(cr)
        q.shade(Path(cr), q.M["hair"], outline=False, size=16.0, rim=0.6)
    _ear_pair(q, P, [s for s in (-1.0, 1.0) if behind[s]], *ear)
    F.hull_union(q, [F.ellipsoid2d(P, (0.0, -6.0, 0.0), 25.0, 28.0, 27.0, 16), F.ellipsoid2d(P, (0.0, 14.0, 12.0), 16.0, 12.0, 16.0, 12),
                     F.blob_pts(q.proj, q.S["neck_top"], 8.0, 8.0, 8.0, 10)], q.M["skin"], 50.0)
    if not hood_up:
        if away:
            F.hull_union(q, [F.ellipsoid2d(P, (0.0, -4.0, -10.0), 26.0, 30.0, 20.0, 14) + [P((s * 18.0, 40.0, -16.0)) for s in (-1.0, 1.0)]],
                         q.M["hair"], 40.0, rim=0.6)
        F.dome_cap(q, P, D, (0.0, -14.0, -2.0), 26.5, 22.0, q.M["hair"], 30.0, brim=0.5, rim=0.7)
    hl = None
    if hood_up:
        hl = _hood(q, P, nz, away, "cloth", r=34.0, hole=(26.0, 30.0), hole_z=20.0)
    if not away:
        if hl is not None:
            cr.save()
            cr.new_path()
            core.smooth_closed(cr, hl, 0.9)
            cr.clip()
        pts["eyes"] = _eyes(q, spec, P, nz, e, near, (13.0, -5.0, 24.0), 11.5, 8.5, HS, lid_add=0.1, lash_flick=0.9)
        _brows(q, spec, P, nz, e, near, 4.0, 24.0, -17.0, 27.0, 20.0, 4.5)
        if hl is not None:
            cr.restore()
        pal = q.P(q.M["skin"])
        B.detail_lines(cr, [[P((0.0, -2.0, 29.0)), P((0.0, 6.0, 31.0)), P((near * 2.0, 8.0, 30.0))]], q.lw * 0.9, pal.line, 0.6)
        _mouth(q, P, nz, e, (0.0, 15.0, 26.0), 14.0, spec, HS)
        if not hood_up and q.detail >= 1:
            fr = [P((-22.0, -24.0, 18.0)), P((0.0, -30.0, 24.0)), P((20.0, -22.0, 18.0))]
            sh, so = B.taper_paths(cr, fr, 12.0, 4.0, q.lw * 0.8)
            q.shade(sh, q.M["hair"], lw=q.lw * 0.8, outline=so, size=10.0, rim=0.6)
    _ear_pair(q, P, [s for s in (-1.0, 1.0) if not behind[s]], *ear)
    return pts


# harpy: a bird face -- small hooked beak, round eyes, a feather crest
def _head_harpy(q, spec, draw=True):
    HS, P, nz, D, W, e, near = _hx(q, spec)
    pts = _pts(P, spec, q, [P((s * 14.0, -8.0, 22.0)) for s in (-near, near)], P((0.0, 12.0, 38.0)), P((0.0, -46.0, -8.0)))
    if not draw:
        return pts
    away = nz((0.0, 0.0, 1.0)) < -0.25
    cr = q.cr
    # crest: three long feathers swept back (behind the head)
    crest = []
    sw = 0.08 * math.sin(q.t * 1.7 + spec.seed)
    for k, (x, l) in enumerate(((-6.0, 40.0), (0.0, 48.0), (6.0, 40.0))):
        sp_ = [P((x, -24.0, -4.0)), P((x * 1.5, -40.0, -18.0 - sw * 20)), P((x * 2.0, -44.0 - l * 0.2, -26.0 - l * 0.4 - sw * 30))]
        crest.append(B.taper_paths(cr, sp_, 10.0, 2.0, q.lw * 0.8))
    B.fill_outlines(cr, [o for _, o in crest], q.P(q.M["cloth"]).line)
    for sh, _o in crest:
        sh.add(cr)
    q.shade(Path(cr), q.M["cloth"], lw=q.lw * 0.8, outline=False, size=8.0, rim=0.7)
    F.hull_union(q, [F.ellipsoid2d(P, (0.0, -4.0, 0.0), 27.0, 28.0, 28.0, 16), F.ellipsoid2d(P, (0.0, 10.0, 12.0), 20.0, 14.0, 18.0, 12),
                     F.blob_pts(q.proj, q.S["neck_top"], 10.0, 9.0, 10.0, 10)], q.M["cloth"], 50.0)
    if not away:
        # pale face disc, round eyes, small hooked beak
        fm = F.ellipsoid2d(P, (0.0, -2.0, 16.0), 20.0, 19.0, 12.0, 14)
        cr.new_path()
        core.smooth_closed(cr, fm, 0.9)
        core.src(cr, q.P(q.M["skin"]).lit)
        cr.fill()
        pts["eyes"] = _eyes(q, spec, P, nz, e, near, (12.0, -6.0, 22.0), 10.5, 11.0, HS, iris_size=0.75)
        beak = [P((-6.0, 2.0, 24.0)), P((6.0, 2.0, 24.0)), P((-5.0, 12.0, 26.0)), P((5.0, 12.0, 26.0)), P((0.0, 6.0, 38.0)), P((0.0, 16.0, 38.0))]
        shp, so, _ = B.hull_paths(cr, beak, q.lw * 0.85)
        q.shade(shp, q.M["beak"], lw=q.lw * 0.85, outline=so, size=8.0, rim=0.0)
        op = clamp(max(q.pose.talk, e.open))
        if op > 0.08:
            m = P((0.0, 13.0 + 3 * op, 30.0))
            cr.new_path()
            core.ellipse(cr, m[0], m[1], 4.0 * HS, 2.5 * op * HS)
            core.src(cr, "#4A1E22")
            cr.fill()
        _brows(q, spec, P, nz, e, near, 4.0, 22.0, -18.0, 24.0, 18.0, 5.0, "cloth")
    return pts


# dwarf (cheap): beard, nose, hood or cap
def _head_dwarf(q, spec, draw=True):
    HS, P, nz, D, W, e, near = _hx(q, spec)
    pts = _pts(P, spec, q, [P((s * 14.0, -6.0, 26.0)) for s in (-near, near)], P((0.0, 20.0, 30.0)), P((0.0, -42.0, 0.0)))
    if not draw:
        return pts
    away = nz((0.0, 0.0, 1.0)) < -0.25
    cr = q.cr
    hood_up = spec.hat == "hood"
    F.hull_union(q, [F.ellipsoid2d(P, (0.0, -12.0, -4.0), 30.0, 30.0, 30.0, 16), F.ellipsoid2d(P, (0.0, 6.0, 8.0), 30.0, 18.0, 24.0, 12),
                     F.blob_pts(q.proj, q.S["neck_top"], 18.0, 6.0, 16.0, 10)], q.M["skin"], 60.0)
    hl = None
    if hood_up:
        hl = _hood(q, P, nz, away, "cloth2", r=38.0, hole=(31.0, 33.0), hole_z=22.0)
    if not away:
        # beard first (sideburns -> a point on the chest), the face features go on top of it
        sw = 1.2 * math.sin(q.t * 1.3 + spec.seed)
        # a big beard down the chest (SPEC: "enormous braided beard hiding the mouth")
        bd = [P((s * x, y, z)) for s in (-1.0, 1.0) for (x, y, z) in ((28.0, 4.0, 0.0), (26.0, 13.0, 9.0), (22.0, 24.0, 18.0),
                                                                       (17.0, 36.0, 21.0))]
        tip = q.proj.xy(v_add(W((0.0, 26.0, 24.0)), (sw, 44.0, 8.0)))
        bd += [P((0.0, 21.0, 31.0)), tip, (tip[0] - 11, tip[1] - 9), (tip[0] + 11, tip[1] - 9)]
        bpal = F.hull_union(q, [bd], q.M["hair"], 34.0, rim=0.6, shadow=0.7)[1]
        if q.detail >= 1:
            # two braids down the middle, bound by a brass ring above the tip
            top = P((0.0, 24.0, 30.0))
            braids = [[(top[0] + d, top[1]), ((top[0] + tip[0]) / 2 + d * 1.3, (top[1] + tip[1]) / 2),
                       (tip[0] + d * 0.6, tip[1] - 12.0)] for d in (-5.0, 5.0)]
            B.detail_lines(cr, braids, q.lw * 0.8, bpal.line, 0.55)
            ring = (tip[0] * 0.8 + top[0] * 0.2, tip[1] * 0.8 + top[1] * 0.2)
            rp, ro = B.ellipse_paths(cr, ring[0], ring[1], 7.5, 3.6, q.lw * 0.8)
            q.shade(rp, q.M["accent"], lw=q.lw * 0.8, outline=ro, size=6.0, rim=0.5)
        if hl is not None:
            cr.save()
            cr.new_path()
            core.smooth_closed(cr, hl, 0.9)
            cr.clip()
        pts["eyes"] = _eyes(q, spec, P, nz, e, near, (14.0, -7.0, 27.0), 9.5, 10.5, HS, lid_add=0.08)
        if hl is not None:
            cr.restore()
        nose = F.ellipsoid2d(P, (0.0, 4.0, 33.0), 10.5, 9.0, 9.0, 12)
        shp, so, _ = B.hull_paths(cr, nose, q.lw * 0.9)
        q.shade(shp, q.M["nose"], lw=q.lw * 0.9, outline=so, size=16.0, rim=0.0)
        op = clamp(max(q.pose.talk, e.open))
        if op > 0.06:                        # the mouth: a dark gap under the moustache
            m = P((0.0, 19.0, 31.0))
            cr.new_path()
            core.ellipse(cr, m[0], m[1] + 2.0 * op, 6.5 * HS, (2.0 + 5.0 * op) * HS)
            core.src(cr, "#4A1E22")
            cr.fill()
        mo = []
        for s in (-1.0, 1.0):
            if nz((s * 0.5, 0.2, 0.8)) > -0.2:
                mo.append(B.taper_paths(cr, [P((s * 2.0, 12.0, 34.0)), P((s * 11.0, 14.0 - e.smile * 3, 31.0)), P((s * 20.0, 20.0 - e.smile * 7, 23.0))],
                                        10.0, 3.5, q.lw * 0.8))
        if mo:
            hp = q.P(q.M["hair"])
            B.fill_outlines(cr, [o for _, o in mo], hp.line)
            for sh, _o in mo:
                sh.add(cr)
            core.src(cr, core.mix(hp.lit, "#F4E6D0", 0.18))
            cr.fill()
        _brows(q, spec, P, nz, e, near, 3.0, 25.0, -19.0, 31.0, 22.0, 7.5)
        if q.detail >= 1:
            # faint granite flecks (SPEC: craggy granite-ruddy skin, a creature not a ruddy old man)
            cr.new_path()
            for k, v in enumerate(((-10.0, -33.0, 20.0), (8.0, -36.0, 19.0), (17.0, -29.0, 21.0), (-23.0, 4.0, 19.0),
                                   (22.0, 7.0, 19.0), (-27.0, -9.0, 15.0))):
                if nz((v[0] / 30.0, v[1] / 30.0, v[2] / 30.0)) < 0.15:
                    continue
                p = P(v)
                cr.new_sub_path()
                cr.arc(p[0], p[1], 1.3 + 0.9 * core.hash01(k, spec.seed), 0.0, TAU)
            core.src(cr, q.P(q.M["skin"]).shadow, 0.6)
            cr.fill()
    if not hood_up and away:                # the back of his head: hair to the nape
        F.hull_union(q, [F.ellipsoid2d(P, (0.0, -8.0, -12.0), 30.0, 24.0, 20.0, 14)], q.M["hair"], 30.0, rim=0.6)
    if spec.hat == "cap":
        _cap_round(q, P, D, "cloth2", y=-35.0, r=31.5, ry=13.0)
    elif not hood_up:
        F.dome_cap(q, P, D, (0.0, -20.0, -5.0), 31.5, 25.0, q.M["hair"], 30.0, brim=0.5, rim=0.7)
    return pts


# ---- torsos / legs per kind --------------------------------------------------------------

def _torso_dwarf(q, spec):
    _tunic(q, spec, top_a=0.7, hem=20.0, flare=1.05)


def _torso_goblin(q, spec):
    _tunic(q, spec, top_a=0.55, hem=26.0, flare=1.25, belt=True)


def _torso_kobold(q, spec):
    _tunic(q, spec, top_a=0.55, hem=22.0, flare=1.1, belt=True)


def _torso_satyr(q, spec):
    """Bare furry chest under an open vest."""
    _tunic(q, spec, top_a=0.6, hem=10.0, flare=1.0, mat="skin", belt=False)
    shp, pal = _tunic(q, spec, top_a=0.62, hem=6.0, flare=1.0, mat="cloth", belt=True)


def _torso_elf(q, spec):
    """A travelling cloak to the calves (some), else a belted knee tunic over hose."""
    if spec.features.get("cloak", True):
        _tunic(q, spec, top_a=0.55, hem=30.0, flare=1.1, mat="cloth2", belt=False)
        _tunic(q, spec, top_a=0.6, hem=0.0, flare=1.0, mat="cloth", belt=False, cloak=True)
    else:
        _tunic(q, spec, top_a=0.58, hem=58.0, flare=1.2, mat="cloth", belt=True)


def _torso_harpy(q, spec):
    """A feathered body (cloth = plumage) with a scalloped breast."""
    shp, pal = _tunic(q, spec, top_a=0.6, hem=18.0, flare=1.05, mat="cloth", belt=False)
    if q.detail >= 1:
        cr = q.cr
        S = q.S
        cr.save()
        shp.add(cr)
        cr.clip()
        T = S["T"]
        lines = []
        for row in range(3):
            y = -q.b.sh_y * (0.65 - 0.18 * row)
            arc = F.front_arc(q, T((0.0, y, 6.0)), q.b.sh_w * 0.9, q.b.sh_w * 0.62, 7)
            lines.append(arc)
        B.detail_lines(cr, lines, q.lw * 0.8, pal.line, 0.4, taper=(0.2, 1.0, 0.2))
        cr.restore()


def _back_kobold(q, spec):
    """A tail (behind the body unless seen from behind)."""
    cr, proj, S = q.cr, q.proj, q.S
    pel = S["pelvis"]
    wav = B.chain(q.t, 4, freq=0.4, delay=0.18, amp=0.5, seed=spec.seed)
    pts = []
    acc = 0.0
    for i in range(5):
        u = i / 4.0
        if i:
            acc += wav[i - 1]
        pts.append(proj.xy(v_add(pel, (acc * 40.0 * u, 10.0 + 60.0 * u * (1 - 0.5 * q.sit), -10.0 - 60.0 * u))))
    shp, so = B.tube_paths(cr, pts, [9.0, 7.5, 6.0, 4.0, 1.5], q.lw, samples=3)
    q.shade(shp, q.M["skin"], outline=so, size=12.0, rim=0.5)


_KIND = {
    "dwarf": {"head": _head_dwarf, "torso": _torso_dwarf, "back": _no_back,
              "legs": lambda q, s: _legs_plain(q, s, (20.0, 15.0, 12.0), "cloth2", 38.0, 13.0)},
    "goblin": {"head": _head_goblin, "torso": _torso_goblin, "back": _no_back,
               "legs": lambda q, s: _legs_plain(q, s, (10.0, 7.5, 6.0), "cloth2", 34.0, 9.0)},
    "kobold": {"head": _head_kobold, "torso": _torso_kobold, "back": _back_kobold,
               "legs": lambda q, s: _legs_plain(q, s, (10.0, 7.0, 5.5), "skin", 26.0, 8.0, boots="skin")},
    "satyr": {"head": _head_satyr, "torso": _torso_satyr, "back": _no_back, "legs": lambda q, s: _legs_goat(q, s)},
    "elf": {"head": _head_elf, "torso": _torso_elf, "back": _no_back,
            "legs": lambda q, s: _legs_plain(q, s, (13.0, 9.5, 7.5), "cloth2", 34.0, 9.0)},
    "harpy": {"head": _head_harpy, "torso": _torso_harpy, "back": _no_back, "legs": _legs_bird},
}


# ========================================================================================
# character sheet + line-up
# ========================================================================================

def lineup():
    out = []
    for kind, seed, w in (("satyr", 3, 160.0), ("harpy", 5, 160.0), ("goblin", 2, 130.0), ("kobold", 7, 120.0)):
        spec = random_creature(seed, kind)
        spec.size = 1.0
        out.append(B.LineupItem(kind, lambda cr, x, y, sc, spec=spec: draw_crowd(cr, x, y, sc, spec, CrowdPose(facing=1), t=0.4), w))
    return out


def sheet_items():
    items = []
    L = B.LIGHTS
    neutral = L["neutral"]

    def add(label, w, h, fn, group):
        items.append(B.SheetItem(label, w, h, fn, group))

    # ---- a gallery: every kind, several seeds
    for kind in CROWD_KINDS:
        n = 1 if kind == "minotaur" else 3
        for k in range(n):
            spec = random_creature(10 + k * 7, kind)

            def fn(cr, spec=spec, k=k):
                F.sheet_bg(cr, 200, 400, floor=372)
                sc = min(0.6, 340.0 / CROWD_HEIGHTS[spec.kind] / spec.size)
                draw_crowd(cr, 100, 384, sc, spec, crowd_pose("idle", 0.4, spec, facing=(1, -1, 0)[k % 3]), neutral, t=0.4)
            add(f"{kind} #{10 + k * 7}", 200, 400, fn, "gallery")
    # ---- random_creature(seed): the mix a scene gets
    for seed in range(100, 108):
        spec = random_creature(seed)

        def fn(cr, spec=spec):
            F.sheet_bg(cr, 200, 300, "square", floor=272)
            draw_crowd(cr, 100, 284, 0.42, spec, crowd_pose("cheer", 1.0, spec, facing=-1), L["square"], t=1.0)
        add(f"random_creature({seed}) cheer", 200, 300, fn, "gallery")

    # ---- actions
    acts = [("idle", dict()), ("cheer", dict()), ("film (facing us: back of crystal, lit face)", dict(facing=0, turn=0.3)),
            ("film (from behind: the fight in it)", dict(facing=2, turn=0.4, thumb=demo_thumb)), ("lower", dict(facing=0, turn=0.3)),
            ("turn_away 0.5", dict(amount=0.5, facing=1)), ("turn_away 1.0", dict(amount=1.0, facing=1)),
            ("laugh (sync)", dict(facing=0, turn=0.2)), ("tankard", dict(facing=1)), ("sit_table", dict(facing=1, turn=-0.3)),
            ("talk (lean in)", dict(facing=1))]
    kinds = ("goblin", "elf", "satyr", "goblin", "dwarf", "kobold", "elf", "dwarf", "satyr", "harpy", "goblin")
    for (label, kw), kind in zip(acts, kinds):
        act = label.split(" ")[0]
        spec = random_creature(40 + len(label), kind)

        def fn(cr, spec=spec, act=act, kw=kw):
            F.sheet_bg(cr, 230, 400, "square", floor=372)
            sc = min(0.62, 330.0 / CROWD_HEIGHTS[spec.kind] / spec.size)
            if act == "sit_table":
                core.src(cr, "#6b4a2e")
                cr.rectangle(120, 384 - 150 * sc * spec.size, 120, 12)
                cr.fill()
            pose = crowd_pose(act, 2.0, spec, **kw)
            draw_crowd(cr, 100, 384, sc, spec, pose, L["square"], t=2.0)
        add(label, 230, 400, fn, "actions")

    # ---- the synchronized laugh: 5 different creatures, same t -> identical rhythm
    for i, tt in enumerate((0.00, 0.05, 0.10, 0.15)):
        def fn(cr, tt=tt):
            F.sheet_bg(cr, 440, 260, "tavern", floor=232)
            for j, kind in enumerate(("dwarf", "goblin", "satyr", "elf", "kobold")):
                spec = random_creature(60 + j, kind)
                sc = 160.0 / CROWD_HEIGHTS[kind] / spec.size
                draw_crowd(cr, 46 + j * 86, 244, sc, spec, crowd_pose("laugh", tt, spec, facing=0, turn=0.3 - 0.15 * j),
                           L["tavern"], t=tt)
        add(f"laugh_sync t={tt:.2f} (identical pulse {laugh_sync(tt):.2f})", 440, 260, fn, "crystal, laugh & lights")
    # ---- the crystal itself
    for label, kw in (("crystal: face + feed", dict(face=1.0, thumb=demo_thumb)), ("crystal: back", dict(face=-1.0)),
                      ("crystal: edge-on", dict(face=0.15)), ("crystal: lowered, dim", dict(face=1.0, glow=0.2, thumb=demo_thumb))):
        def fn(cr, kw=kw):
            F.sheet_bg(cr, 160, 260, "square")
            c = draw_scrying_crystal(cr, 80, 200, 2.6, 0.0, L["square"], t=0.3, **kw)
            fx.glow(cr, c[0], c[1], 90.0, CRYSTAL_GLOW, 0.25 * kw.get("glow", 1.0))
        add(label, 160, 260, fn, "crystal, laugh & lights")
    for name in ("square", "tavern", "lantern_night", "golden"):
        def fn(cr, name=name):
            F.sheet_bg(cr, 300, 260, name, floor=232)
            for j, kind in enumerate(("goblin", "dwarf", "elf")):
                spec = random_creature(80 + j, kind)
                sc = 200.0 / CROWD_HEIGHTS[kind] / spec.size
                draw_crowd(cr, 60 + j * 90, 244, sc, spec, crowd_pose("idle", 0.4, spec, facing=0, turn=0.3), L[name], t=0.4)
        add(name, 300, 260, fn, "crystal, laugh & lights")
    return items
