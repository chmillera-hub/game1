"""_garden.py -- THE CASTLE GARDEN: the shared location of Scenes 6, 7 and 8.

One place at three times of day (SPEC section 4):

    S6  dusk         violet sky -> peach horizon, the sun just down on the LEFT, long shadows
                     falling to the right; the lantern post not yet lit.
    S7  golden hour into blue hour; the lantern post lights up.
    S8  night: the garden dark except ONE warm lantern over the benches; far away the town's
        signs (wash-house, apothecary cross, tavern lanterns) glow small and cold.

Everything here is drawn with the shared kit (film.lib.env / props / characters), in the house
style (no outlines on set dressing, atmospheric depth, cached static layers).

WORLD COORDINATES
-----------------
World px, y down. At the default camera (core.Camera(): centre (960, 540), zoom 1) the world is
the 1920x1080 frame and you see the whole garden: the old oak on the left, bench 1 left of
centre, the gravel walk sweeping from the bottom-left past the bench up through a gap in the
back hedge toward the castle on its hill, the lantern post right of bench 1, and the spot
where the second bench ends up (S7) on the right. The action plane (parallax 1.0) holds the
whole garden; the sky, castle and hills sit on slower planes (PARALLAX), so any core.Camera
move (push-in, pan, zoom about a point) gets real multiplane depth.

    SCALE      0.78      the cast scale on the bench plane (STYLE.md: one scale per depth
                         plane -- use it for everyone on/near the benches)
    GROUND_Y   930       the ground line of bench 1 (sitters' anchors)
    BENCH1     the bench (S6-S8).        BENCH2: where the second bench ends up (S7, S8)
    BENCH2_FROM  where the dwarf drags the second bench in from (S7, off-screen right)
    LANTERN    the lantern post's foot (between the benches, its crook over bench 1's end)
    OAK, CASTLE, PATH, HEDGES, BEDS      the set (static, cached)
    SEATS      where S6 seats its two leads on bench 1 (fractions u for BenchRig.place(u));
    SEATS_S6_END  where S6 leaves them (she has shuffled closer to him): S7 picks up from here
    S6_END_PROPS  the book on the seat, the pigeon on the backrest, the sack at his feet (S7 continuity)

TIME OF DAY
-----------
`tod` is a kind name ("dusk", "golden", "blue_hour", "night") or a blend
(kind_a, kind_b, u) -- u = 0 is all kind_a. A blend paints both kinds' cached layers (build
both in Garden(kinds=...)). light_for(tod) gives the matching character light (a B.Light,
blended the same way), so the cast always agrees with the set.

QUICK START (a scene)
---------------------
    from film.scenes import _garden as G

    def setup():
        return {"g": G.Garden(kinds=("dusk",)), "light": fx.LightLayer()}

    def draw(cr, t, st):
        g, tod = st["g"], "dusk"                            # or ("golden", "blue_hour", u)
        cam = core.Camera.about(900, 760, 2.0)              # any core.Camera
        L = G.light_for(tod)
        bench = g.bench(1)                                  # sitter anchors: bench.place(u)
        gx, gy = bench.place(G.SEATS["gnome"])
        g.paint_back(cr, cam, t, tod)                       # sky, castle, hills, garden, oak
        g.shadow_pass(cr, cam, tod, [(gx, gy, 40, 150)])    # soft long shadows of the cast
        with cam.view(cr, 1.0):                             # the action plane = world coords
            post = g.draw_lantern(cr, t, L, lit=0.0)
            g.draw_bench(cr, t, L, part="back")
            ch.draw_gnome(cr, gx, gy, G.SCALE, pose, L, t)
            g.draw_bench(cr, t, L, part="front")
        g.paint_fg(cr, cam, t, tod)                         # soft foreground framing (wide shots)
        lc = st["light"].begin()
        g.light(lc, cam, t, tod)                            # horizon glow, last light, moonlight
        g.lantern_light(lc, post, t, strength=lit, cam=cam) # (S7/S8) the lantern's halo + pool
        fx.post(cr, t, light=st["light"], **G.POST["dusk"])

At night pass g.pool_light(x, y) as the light of anything you draw: warm inside the lantern's
pool, cold and dark outside it.

API (all stable; coordinates are world px unless stated)
--------------------------------------------------------
Garden(kinds=("dusk",), fg=True)        builds and caches every static layer for those kinds
  .paint_back(cr, cam, t, tod)           sky (+ twinkling stars at night), castle, hills + town,
                                         back hedges, lawn, gravel walk, beds, baked shadows, oak
  .paint_fg(cr, cam, t, tod, alpha=1)    foreground framing at parallax 1.3 (fade it in close-ups)
  .light(lc, cam, t, tod, strength=1)    soft light for a fx.LightLayer (horizon glow, last-light
                                         wash, ground haze) in full-res screen coords
  .bench(which=1, spot=None)             props.BenchRig of bench 1/2 at its spot (no drawing)
  .draw_bench(cr, t, light, which=1, part="all", spot=None, sag=0.0, sag_u=0.8, tod=None,
              shadow=None, crumbs=0, dim=0.86)
                                         draw a bench (inside cam.view(cr, 1.0)); `spot` moves it
                                         (S7 drag, see lerp_spot); sag 0..1 dips the seat under a
                                         heavy sitter at fraction sag_u (S6); part "back"/"front"
                                         around the sitters as in props.draw_garden_bench
  .seat_dip(u, sag, which=1, sag_u=0.8, height=None)  how far (px) the seat (or a point `height`
                                         up the bench) at u is pushed down by that sag
  .draw_lantern(cr, t, light, lit=0.0)   the lantern post (flame flicker -> draw every frame)
  .lantern_light(lc, rig, t, strength=1) its halo + warm pool on the ground (LightLayer)
  .shadow_pass(cr, cam, tod, casters, benches=())  soft long sun shadows for moving things (the
                                         cast, a dragged bench): call after paint_back(), before them
  .long_shadow(cr, x, y, w, h, tod, alpha=1)   one hard-ish long shadow, drawn directly
  .pool_light(x, y, lit=1, tod="night")  S8: the character/prop light at (x, y) -- warm in the
                                         lantern's pool, cold and dark outside it
  .town_glows(cr, cam, t, strength=1)    S8: the wash-house sign, the apothecary's green cross
                                         and the tavern's lantern string, tiny and cold, far away
light_for(tod) -> B.Light ;  POST[kind] -> fx.post kwargs ;  blend(tod) -> [(kind, weight)]
lerp_spot(a, b, u) -> BenchSpot (S7: the dragged bench between BENCH2_FROM and BENCH2)

Run `python3 -m film.scenes._garden` for film/build/preview/garden_<kind>.png (the four times
of day at the default camera plus a two-shot framing) -- the reference for S6-S8.
"""

import math
from dataclasses import dataclass

import cairocffi as cairo

from film.lib import core, env, fx
from film.lib import props as P
from film.lib import characters as ch

__all__ = [
    "KINDS", "SCALE", "GROUND_Y", "BenchSpot", "BENCH1", "BENCH2", "BENCH2_FROM", "lerp_spot", "SEATS",
    "SEATS_S6_END", "S6_END_PROPS", "LANTERN",
    "LANTERN_SCALE", "LANTERN_HEIGHT", "OAK", "CASTLE", "HORIZON", "PATH", "PATH_W", "HEDGES", "BEDS",
    "PARALLAX", "TOWN_SIGNS",
    "POST", "SHADOW_DIR", "GRADE", "Garden", "light_for", "blend",
]

KINDS = ("dusk", "golden", "blue_hour", "night")
_LIGHT_NAMES = {"dusk": "dusk", "golden": "golden", "blue_hour": "blue_hour", "night": "lantern_night"}

# ----------------------------------------------------------------------------------------
# the layout (world px at the action plane)
# ----------------------------------------------------------------------------------------
SCALE = 0.78                 # the cast on the bench plane (gnome seated head ~150 px, dragon ~405 standing)
GROUND_Y = 930.0             # bench 1's ground line


@dataclass(frozen=True)
class BenchSpot:
    """Where a bench stands: its ground anchor (middle, below the seat), yaw and length."""
    x: float
    y: float
    yaw: float = 0.0
    length: float = 620.0


BENCH1 = BenchSpot(860.0, GROUND_Y, -0.1, 620.0)      # the bench; its right (+X) end is a touch nearer
BENCH2 = BenchSpot(1605.0, 962.0, -0.3, 520.0)         # S7: the second bench's final spot, angled in
BENCH2_FROM = BenchSpot(2260.0, 985.0, -0.3, 520.0)    # S7: where the dwarf drags it from (off right)


def lerp_spot(a, b, u):
    """A BenchSpot between a and b (u 0..1): S7's drag, e.g. draw_bench(..., which=2,
    spot=lerp_spot(BENCH2_FROM, BENCH2, core.ramp(t, 15.5, 18.0, "inout_sine")))."""
    return BenchSpot(core.lerp(a.x, b.x, u), core.lerp(a.y, b.y, u), core.lerp(a.yaw, b.yaw, u),
                     core.lerp(a.length, b.length, u))


SEATS = {"gnome": 0.12, "dragon": 0.83}                # S6 opens with them here on bench 1 (BenchRig.place(u))
SEATS_S6_END = {"gnome": 0.3, "dragon": 0.83}          # ...and leaves them here: she shuffles closer (S7 starts so)
# the rest of S6's last frame, for S7's continuity: the coloring book lies flat on bench 1's seat
# at book_u (between them); one pigeon stands on the top of the crest board at umpire_u (it flaps
# off when S7 likes); the tied-open apothecary sack stands on the gravel at `sack` (ground point,
# drawn with props.draw_apothecary_bag at SCALE, its grip 68 px above); the other pigeons peck on
# the gravel in front of the bench (y 955-990); his wings are relaxed-up, both are smiling.
S6_END_PROPS = {"book_u": 0.55, "umpire_u": 0.5, "sack": (1042.0, 946.0)}

LANTERN = (1302.0, 912.0)       # the lantern post's foot (behind bench 1's right end, between the benches)
LANTERN_SCALE = 0.85
LANTERN_HEIGHT = 640.0          # its lamp hangs from the crook toward bench 1 (side = -1)
OAK = (300.0, 815.0, 0.62)      # the old oak: trunk base (x, y) and scale (env.OakTree)
CASTLE = (935.0, 418.0, 0.62)   # the castle's foot on its hill, far plane (parallax PARALLAX["far"])
HORIZON = 652.0
PATH = [(1158.0, 752.0), (1172.0, 818.0), (1128.0, 888.0), (985.0, 968.0), (690.0, 1068.0), (400.0, 1170.0)]
PATH_W = (58.0, 600.0)
HEDGES = [(-110.0, 802.0, 1185.0, 104.0), (1232.0, 800.0, 900.0, 98.0)]   # (x, y_bottom, w, h)
BEDS = [(40.0, 1046.0, 410.0, 70.0), (1540.0, 1056.0, 450.0, 76.0)]       # flower beds (x, y_bottom, w, h)
PARALLAX = {"sky": 0.06, "far": 0.28, "hills": 0.45, "garden": 1.0, "fg": 1.3}
# S8: where the town's three cold signs glow, in the hills plane (parallax PARALLAX["hills"])
TOWN_SIGNS = {"washhouse": (742.0, 626.0), "apothecary": (1186.0, 618.0), "tavern": (1408.0, 628.0)}

_SAG_SQUASH = 0.05              # draw_bench(sag=1): the seat drops 5 % of its height ...
_SAG_TILT = 9.0                 # ... plus ~9 px (x SCALE) more at the heavy end

# the sun is just down beyond the left edge: shadows fall to the right and a little toward us
SHADOW_DIR = {"dusk": (1.0, 0.17), "golden": (1.0, 0.12)}
_SHADOW_LEN = {"dusk": 2.6, "golden": 1.7}        # shadow length / caster height
_SHADOW_COL = {"dusk": "#2a1f3e", "golden": "#3b2a2a"}
_SHADOW_A = {"dusk": 0.42, "golden": 0.36}
_GROUND_K = 0.34                # how flat the ground looks from the camera (shadow thickness / caster width)

# post-processing that suits each time of day (fx.post kwargs)
POST = {
    "dusk": dict(bloom_strength=0.38, threshold=0.68, bloom_radius=2.4, wide=0.35, grain=0.035, vignette=0.42,
                 vignette_color=(0.06, 0.02, 0.08)),
    "golden": dict(bloom_strength=0.45, threshold=0.66, bloom_radius=2.4, wide=0.45, grain=0.035, vignette=0.38,
                   vignette_color=(0.08, 0.04, 0.02)),
    "blue_hour": dict(bloom_strength=0.5, threshold=0.62, bloom_radius=2.2, wide=0.3, grain=0.04, vignette=0.48,
                      vignette_color=(0.02, 0.02, 0.07)),
    "night": dict(bloom_strength=0.6, threshold=0.58, bloom_radius=2.2, wide=0.4, grain=0.042, vignette=0.58,
                  vignette_color=(0.01, 0.01, 0.04)),
}


def blend(tod):
    """[(kind, weight)] for a time of day: "dusk" -> [("dusk", 1.0)];
    ("golden", "blue_hour", 0.3) -> [("golden", 0.7), ("blue_hour", 0.3)] (zero weights dropped)."""
    if isinstance(tod, str):
        return [(tod, 1.0)]
    a, b, u = tod
    u = core.clamp(u)
    out = [(a, 1.0 - u), (b, u)]
    return [(k, w) for k, w in out if w > 1e-4] or [(a, 1.0)]


def light_for(tod):
    """The character light (characters.base.Light) matching a time of day or blend."""
    ws = blend(tod)
    L = ch.LIGHTS[_LIGHT_NAMES[ws[0][0]]]
    if len(ws) == 2:
        L = ch.Light.lerp(L, ch.LIGHTS[_LIGHT_NAMES[ws[1][0]]], ws[1][1])
    return L


def _sun_shadow(kind):
    return kind in SHADOW_DIR


# ----------------------------------------------------------------------------------------
# static art, per kind
# ----------------------------------------------------------------------------------------

def _sky(cr, kind):
    pal = env.palette(kind)
    if kind in ("dusk", "golden"):
        # the sun is just down (dusk) / low (golden) beyond the left edge: glow + cloud light from there
        sun = (40.0, 700.0, 0.1) if kind == "dusk" else (60.0, 610.0, 0.1)
        env.draw_sky(cr, kind=kind, horizon=HORIZON, seed=11, sun=sun)
        hc = pal["sky"][-1]
        fx.glow(cr, -40.0, HORIZON - 30.0, 760.0, core.tint(hc, 0.25), 0.55 if kind == "dusk" else 0.6, additive=False)
        fx.glow(cr, -60.0, HORIZON + 10.0, 300.0, core.tint(hc, 0.55), 0.5, additive=False)
    elif kind == "blue_hour":
        env.draw_sky(cr, kind=kind, horizon=HORIZON, seed=11, sun=(60.0, 760.0, 0.1))
        fx.glow(cr, -60.0, HORIZON, 640.0, "#d0a8c0", 0.32, additive=False)
    else:  # night: stars and the moon high on the right
        env.draw_sky(cr, kind=kind, horizon=HORIZON, seed=11, moon=(1560.0, 170.0, 30.0))


def _far(cr, kind):
    wa = {"dusk": 0.0, "golden": 0.0, "blue_hour": 0.18, "night": 0.32}[kind]
    env.draw_castle_hill(cr, CASTLE[0], CASTLE[1], CASTLE[2], kind=kind, seed=1, hill_w=880.0, hill_h=150.0,
                         window_alpha=wa, light_dx=-0.6)


def _hills(cr, kind):
    pal = env.palette(kind)
    env.draw_hills(cr, -90.0, 2100.0, 668.0, kind=kind, layers=3, seed=2, height=(26.0, 104.0), light_dx=-0.6)
    # the town at the foot of the castle hill: a low roofline, small and far away
    lit = {"dusk": 0.0, "golden": 0.0, "blue_hour": 0.15, "night": 0.28}[kind]
    env.draw_roofline(cr, 560.0, 1500.0, 646.0, 0.034, kind=kind, seed=4, lit=lit, haze=0.18 if kind != "night" else 0.05)
    env.draw_haze(cr, -90.0, 520.0, 2100.0, 180.0, pal["haze"], 0.0, 0.28 if kind != "night" else 0.18)


def _back(cr, kind):
    """The garden's far strip: lawn up to the back hedge, the hedges (soft focus)."""
    pal = env.palette(kind)
    env.draw_grass(cr, -90.0, 690.0, 2100.0, 160.0, kind, seed=3, density=0.8, flowers=False)
    for i, (x, y, w, h) in enumerate(HEDGES):
        env.draw_hedge(cr, x, y, w, h, kind, seed=4 + i, light_dx=-0.6)
    if _sun_shadow(kind):
        # the hedges' long shadows reach toward us across the lawn
        dx, dy = SHADOW_DIR[kind]
        for (x, y, w, h) in HEDGES:
            L = h * _SHADOW_LEN[kind] * 0.35
            core.polygon(cr, [(x, y - 2), (x + w, y - 2), (x + w + dx * L, y + dy * L + 26), (x + dx * L, y + dy * L + 26)])
            cr.set_source(core.linear(0, y, 0, y + dy * L + 26, [core.alpha(_SHADOW_COL[kind], _SHADOW_A[kind] * 0.9),
                                                                  core.alpha(_SHADOW_COL[kind], 0.0)]))
            cr.fill()
    if kind == "night":
        env.draw_haze(cr, -90.0, 680.0, 2100.0, 200.0, pal["haze"], 0.0, 0.12)


def _baked_shadow(cr, x, y, w, h, kind, alpha=1.0, k=1.0, taper=0.5):
    """A long sun shadow on the ground from the foot point (x, y) of a caster w px wide and
    h px tall: a tapered band (foreshortened on the ground) that fades toward its tip."""
    if not _sun_shadow(kind) or alpha <= 0.0:
        return
    dx, dy = SHADOW_DIR[kind]
    n = math.hypot(dx, dy)
    dx, dy = dx / n, dy / n
    L = h * _SHADOW_LEN[kind] * k
    w0 = max(2.0, w * _GROUND_K)
    tip = (x + dx * L, y + dy * L)
    a = _SHADOW_A[kind] * alpha
    col = _SHADOW_COL[kind]
    cr.new_path()
    core.tapered(cr, [(x, y), ((x + tip[0]) * 0.5, (y + tip[1]) * 0.5), tip], w0, w0 * taper, cap=True)
    cr.set_source(core.linear(x, y, tip[0], tip[1], [(0.0, core.alpha(col, a)), (0.55, core.alpha(col, a * 0.75)),
                                                     (1.0, core.alpha(col, 0.0))]))
    cr.fill()


def _bench_shadow(cr, sp, kind, alpha=1.0):
    """A bench's long shadow: the seat and back smeared to the right along the ground, plus
    thin streaks from its iron ends."""
    if not _sun_shadow(kind) or alpha <= 0.0:
        return
    dx, dy = SHADOW_DIR[kind]
    n = math.hypot(dx, dy)
    dx, dy = dx / n, dy / n
    half = (sp.length * 0.5 - 16.0) * SCALE * math.cos(sp.yaw)
    L = P.BENCH_SEAT_H * SCALE * _SHADOW_LEN[kind] * 1.25
    a = _SHADOW_A[kind] * alpha
    col = _SHADOW_COL[kind]
    x0, x1, y = sp.x - half - 10.0, sp.x + half + 10.0, sp.y + 3.0
    th = 30.0 * SCALE
    cr.new_path()
    core.polygon(cr, [(x0, y - th * 0.3), (x1, y - th * 0.3), (x1 + dx * L, y + dy * L + th * 0.2),
                      (x0 + dx * L * 0.85, y + dy * L * 0.85 + th * 1.1), (x0, y + th * 0.6)])
    cr.set_source(core.linear(x0, y, x1 + dx * L, y + dy * L, [(0.0, core.alpha(col, a * 0.85)), (0.6, core.alpha(col, a * 0.6)),
                                                              (1.0, core.alpha(col, 0.0))]))
    cr.fill()
    for xx in (x0 + 12.0, x1 - 12.0):
        _baked_shadow(cr, xx, y, 12.0, 245.0 * SCALE, kind, 0.55 * alpha, 1.0, 0.6)


def _ground(cr, kind):
    """The near garden: lawn, the gravel walk, flower beds and the static long shadows."""
    pal = env.palette(kind)
    env.draw_grass(cr, -90.0, 792.0, 2100.0, 450.0, kind, seed=5)
    env.draw_gravel_path(cr, PATH, PATH_W, kind, seed=6)
    if _sun_shadow(kind):
        ox, oy, osc = OAK
        # the oak: the trunk's long shadow, then the crown's dappled shade far across the lawn
        _baked_shadow(cr, ox + 8, oy + 4, 120.0 * osc, 300.0, kind, 1.0, 1.0, 0.7)
        for j in range(7):
            u = (j + 0.5) / 7
            bx = ox + 330 + 760 * u + 40 * math.sin(j * 2.3)
            by = oy + 42 + 120 * u + 14 * math.cos(j * 1.9)
            _baked_shadow(cr, bx, by, 170.0 + 70 * math.sin(j * 1.7), 40.0, kind, 0.55, 1.0, 0.8)
        # the lantern post: a long thin line of shadow
        _baked_shadow(cr, LANTERN[0], LANTERN[1] + 2, 16.0, LANTERN_HEIGHT * LANTERN_SCALE * 0.8, kind, 0.9, 1.0, 0.6)
        _bench_shadow(cr, BENCH1, kind, 1.0)          # bench 1 never moves: bake it
    for i, (x, y, w, h) in enumerate(BEDS):
        env.draw_flower_bed(cr, x, y, w, h, kind, seed=7 + i)
        _baked_shadow(cr, x + w * 0.5, y + 4, h * 0.5, h * 0.8, kind, 0.5, 1.0)
    if kind == "night":
        # the garden falls into the dark beyond the lantern's reach
        cr.rectangle(-90.0, 690.0, 2100.0, 560.0)
        core.src(cr, "#03050d", 0.32)
        cr.fill()


def _fg(cr, kind):
    """Soft foreground framing at parallax 1.3: tall grass and wild flowers in the bottom corners."""
    pal = env.palette(kind)
    fd, fm, fl = pal["foliage"]
    dark = core.shade(fd, 0.25)
    for side, x0 in ((-1, -120.0), (1, 1660.0)):
        cr.new_path()
        for i in range(70):
            h = core.hash01(i, 300 + side)
            bx = x0 + 380.0 * core.hash01(i, 310 + side)
            L = 70.0 + 150.0 * h
            lean = (core.hash01(i, 320 + side) - 0.5) * 0.9 + side * 0.15
            by = 1175.0 + 30.0 * core.hash01(i, 330 + side)
            core.tapered(cr, [(bx, by), (bx + math.sin(lean) * L * 0.5, by - L * 0.5),
                              (bx + math.sin(lean) * L, by - L)], 7.0 + 6.0 * h, 0.0)
        core.src(cr, dark, 0.95)
        cr.fill()
        for i in range(9):
            px = x0 + 40 + 300.0 * core.hash01(i, 340 + side)
            py = 1070.0 + 70.0 * core.hash01(i, 350 + side)
            c = ("#e7a6c0", "#f1e6ee", "#b9a4e2")[i % 3]
            core.src(cr, env.haze_toward(c, pal["haze"], 0.35 if kind != "night" else 0.75), 0.9)
            for k in range(5):
                a = k * math.tau / 5 + i
                core.circle(cr, px + math.cos(a) * 6.0, py + math.sin(a) * 6.0, 5.0)
            cr.fill()


# one-time colour grades of the cached layers, per time of day: washes painted ATOP each layer
# (only where it has paint) -- the garden takes the sky's colour; plus a vertical darkening of
# the near ground so the eye rests on the bench, not the foreground.
GRADE = {
    "dusk": {"back": [("#6d5d96", 0.30)], "oak": [("#5c4c86", 0.24)], "ground": [("#4a3c6c", 0.20)],
             "ground_v": ("#1b1530", 0.0, 0.52), "fg": [("#1f1a34", 0.45)], "hills": [("#8a74a8", 0.10)]},
    "golden": {"back": [("#b88a5a", 0.16)], "oak": [("#a07040", 0.12)], "ground": [("#6a4e2c", 0.12)],
               "ground_v": ("#2a1d12", 0.0, 0.42), "fg": [("#2a2014", 0.4)], "hills": []},
    "blue_hour": {"back": [("#3a4476", 0.30)], "oak": [("#323c6a", 0.28)], "ground": [("#262c50", 0.24)],
                  "ground_v": ("#0c1024", 0.0, 0.5), "fg": [("#0e1226", 0.5)], "hills": []},
    "night": {"back": [("#0b1022", 0.30)], "oak": [("#0a0f22", 0.30)], "ground": [("#090d1c", 0.22)],
              "ground_v": ("#03050d", 0.0, 0.5), "fg": [("#05070f", 0.6)], "hills": []},
}


def _grade_layer(layer, washes, vgrad=None):
    """Paint colour washes ATOP a cached fx.Layer (only where it has paint), once."""
    if not washes and vgrad is None:
        return
    surf = layer.surface
    c = cairo.Context(surf)
    c.scale(layer.res, layer.res)
    c.translate(-layer.x, -layer.y)              # world coordinates
    c.set_operator(cairo.OPERATOR_ATOP)
    for col, a in washes:
        core.src(c, col, a)
        c.paint()
    if vgrad is not None:
        col, a0, a1 = vgrad
        c.set_source(core.linear(0.0, 800.0, 0.0, 1180.0, [core.alpha(col, a0), core.alpha(col, a1)]))
        c.paint()
    surf.flush()


# ----------------------------------------------------------------------------------------
# the garden
# ----------------------------------------------------------------------------------------

class Garden:
    """The cached castle garden for the given kinds (times of day). Build it once in setup()."""

    def __init__(self, kinds=("dusk",), fg=True):
        self.kinds = tuple(kinds)
        self.L = {}
        for k in self.kinds:
            if k not in KINDS:
                raise ValueError(f"unknown time of day {k!r} (choose from {KINDS})")
            L = {
                "sky": env.layer(lambda cr, k=k: _sky(cr, k), blur=2.5, opaque=True),
                "far": env.layer(lambda cr, k=k: _far(cr, k), blur=1.8),
                "hills": env.layer(lambda cr, k=k: _hills(cr, k), blur=1.3),
                "back": env.layer(lambda cr, k=k: _back(cr, k), blur=1.1),
                "ground": env.layer(lambda cr, k=k: _ground(cr, k), blur=0.45),
                "oak": env.OakTree(OAK[0], OAK[1], OAK[2], kind=k, seed=2, light_dx=-0.6, blur=0.7),
            }
            if fg:
                L["fg"] = env.layer(lambda cr, k=k: _fg(cr, k), blur=6.0, x=-400, y=-300, w=2720, h=1700)
            if env.palette(k).get("star"):
                L["stars"] = env.StarField((-90.0, -80.0, 2100.0, 560.0), n=90, seed=5)
            gr = GRADE[k]
            _grade_layer(L["hills"], gr["hills"])
            _grade_layer(L["back"], gr["back"])
            _grade_layer(L["ground"], gr["ground"], gr["ground_v"])
            for lay in [L["oak"].trunk] + [c[0] for c in L["oak"].clumps]:
                _grade_layer(lay, gr["oak"])
            if fg:
                _grade_layer(L["fg"], gr["fg"])
            self.L[k] = L
        self._bench_rigs = {}
        self._shadow_buf = None

    # -- painting the set ------------------------------------------------------------
    def _paint(self, cr, cam, name, tod, parallax, t=0.0):
        for i, (k, w) in enumerate(blend(tod)):
            lay = self.L[k].get(name)
            if lay is None:
                continue
            with cam.view(cr, parallax):
                a = 1.0 if i == 0 else w
                if name == "oak":
                    lay.draw(cr, t, alpha=a)
                elif name == "stars":
                    lay.draw(cr, t, alpha=w)
                else:
                    lay.paint(cr, alpha=a)

    def paint_back(self, cr, cam, t, tod="dusk"):
        """Everything behind the action: sky, castle, hills + town, back hedges, lawn, walk, beds, oak."""
        self._paint(cr, cam, "sky", tod, PARALLAX["sky"])
        self._paint(cr, cam, "stars", tod, PARALLAX["sky"], t)
        self._paint(cr, cam, "far", tod, PARALLAX["far"])
        self._paint(cr, cam, "hills", tod, PARALLAX["hills"])
        self._paint(cr, cam, "back", tod, PARALLAX["garden"])
        self._paint(cr, cam, "ground", tod, PARALLAX["garden"])
        self._paint(cr, cam, "oak", tod, PARALLAX["garden"], t)

    def paint_fg(self, cr, cam, t, tod="dusk", alpha=1.0):
        """Soft foreground grass and flowers in the bottom corners (parallax 1.3)."""
        if alpha <= 0.0:
            return
        for i, (k, w) in enumerate(blend(tod)):
            lay = self.L[k].get("fg")
            if lay is not None:
                with cam.view(cr, PARALLAX["fg"]):
                    lay.paint(cr, alpha=alpha * (1.0 if i == 0 else w))

    def light(self, lc, cam, t, tod="dusk", strength=1.0):
        """Soft light into a fx.LightLayer context (full-res screen coords), per time of day:
        dusk/golden -- the horizon glow on the sun's side (left) and the last light on the lawn;
        blue hour -- the afterglow low on the left; night -- the moon's halo. (The lantern's light
        is separate: lantern_light().)"""
        for k, w in blend(tod):
            s = strength * w
            if s <= 0:
                continue
            if k in ("dusk", "golden"):
                warm = "#ffb889" if k == "dusk" else "#ffc87a"
                with cam.view(lc, PARALLAX["hills"]):
                    fx.glow(lc, -80.0, HORIZON - 40.0, 900.0, warm, 0.26 * s)
                with cam.view(lc, PARALLAX["garden"]):
                    fx.light_pool(lc, 640.0, 975.0, 1100.0, 170.0, "#ffc9a0" if k == "dusk" else "#ffd28a", 0.07 * s)
            elif k == "blue_hour":
                with cam.view(lc, PARALLAX["hills"]):
                    fx.glow(lc, -60.0, HORIZON, 700.0, "#b48cc0", 0.16 * s)
            else:
                with cam.view(lc, PARALLAX["sky"]):
                    fx.glow(lc, 1560.0, 170.0, 260.0, "#9fb4e8", 0.16 * s)

    # -- benches ------------------------------------------------------------------------
    def bench(self, which=1, spot=None):
        """props.BenchRig of bench `which` (1 or 2) at its spot (or `spot`), without drawing."""
        sp = spot or (BENCH1 if which == 1 else BENCH2)
        key = (sp.x, sp.y, sp.yaw, sp.length)
        if key not in self._bench_rigs:
            self._bench_rigs[key] = P.draw_garden_bench(core.frame(4, 4)[1], sp.x, sp.y, SCALE, ch.LIGHTS["dusk"],
                                                        0.0, yaw=sp.yaw, length=sp.length, part="back")
        return self._bench_rigs[key]

    def seat_dip(self, u, sag, which=1, sag_u=0.8, spot=None, height=None):
        """World px a point on the bench at fraction u sinks under draw_bench(..., sag, sag_u):
        add it to a sitter's anchor y so they ride the bench (e.g. the gnome when the dragon
        lands). height = that point's height above the ground in bench units at scale 1.0
        (default: the seat top; e.g. ~242 for the top of the crest board)."""
        if sag == 0.0:
            return 0.0
        sp = spot or (BENCH1 if which == 1 else BENCH2)
        span = (sp.length - 60.0) * SCALE
        x_far = sp.x + (0.5 - sag_u) * span * 1.25
        x_s = sp.x + (sag_u - 0.5) * span
        x_u = sp.x + (u - 0.5) * span
        tilt = sag * _SAG_TILT * SCALE / max(1.0, x_s - x_far) if x_s != x_far else 0.0
        h = P.BENCH_SEAT_H if height is None else height
        return sag * _SAG_SQUASH * h * SCALE + tilt * (x_u - x_far)

    def draw_bench(self, cr, t, light, which=1, part="all", spot=None, sag=0.0, sag_u=0.8, tod=None, shadow=None,
                   crumbs=0, dim=0.86):
        """Draw bench 1 or 2 (inside cam.view(cr, 1.0)) and return its BenchRig. `spot` moves it
        (S7's drag); `sag` (0..1, may overshoot negative in a wobble) bows the seat under a heavy
        sitter at fraction sag_u -- the bench creaks (S6). shadow: draw its long sun shadow for
        `tod` (default: the first kind built; dusk/golden only) -- None = only for bench 2 or a
        moved bench (bench 1's is baked into the ground layer). If you give a bench's shadow to
        shadow_pass(benches=[...]) instead (softer), pass shadow=False here. dim < 1 keeps the
        wood a step darker than the cast (STYLE.md: characters out-contrast the set)."""
        sp = spot or (BENCH1 if which == 1 else BENCH2)
        if shadow is None:
            shadow = which == 2 or spot is not None            # bench 1 at its spot: baked in the ground
        if shadow and part in ("all", "back"):
            for k, w in blend(tod or self.kinds[0]):
                _bench_shadow(cr, sp, k, w)
        light = light.with_(exposure=light.exposure * dim)
        if sag != 0.0:
            # the seat gives under the weight: a squash about the ground line (the feet stay
            # planted) plus a slight tilt toward the heavy end (sag_u) -- see seat_dip()
            cr.save()
            span = (sp.length - 60.0) * SCALE
            x_far = sp.x + (0.5 - sag_u) * span * 1.25          # the light end barely moves
            x_s = sp.x + (sag_u - 0.5) * span
            tilt = sag * _SAG_TILT * SCALE / max(1.0, x_s - x_far) if x_s != x_far else 0.0
            cr.translate(x_far, sp.y)
            cr.transform(cairo.Matrix(1.0, tilt, 0.0, 1.0 - sag * _SAG_SQUASH, 0.0, 0.0))
            cr.translate(-x_far, -sp.y)
            P.draw_garden_bench(cr, sp.x, sp.y, SCALE, light, t, yaw=sp.yaw, length=sp.length, part=part,
                                crumbs=crumbs)
            cr.restore()
            return self.bench(which, spot)
        return P.draw_garden_bench(cr, sp.x, sp.y, SCALE, light, t, yaw=sp.yaw, length=sp.length, part=part,
                                   crumbs=crumbs)

    # -- the lantern post ---------------------------------------------------------------
    def draw_lantern(self, cr, t, light, lit=0.0):
        """The iron lantern post (inside cam.view(cr, 1.0)): its candle lantern hangs from a
        crook toward bench 1. lit 0..1 (S7 lights it, S8 lit). Returns its PropRig."""
        return P.draw_lantern_post(cr, LANTERN[0], LANTERN[1], LANTERN_SCALE, light, t, lit=lit, kind="warm",
                                   style="crook", side=-1, height=LANTERN_HEIGHT, seed=3)

    def lantern_light(self, lc, rig, t, strength=1.0, cam=None):
        """The lantern's warm halo and its pool on the ground, into a LightLayer (pass the camera
        so it lands in the right place; strength follows lit)."""
        if strength <= 0:
            return
        cam = cam or core.Camera()
        with cam.view(lc, 1.0):
            P.lantern_light(lc, rig, LANTERN_SCALE, t, strength=strength, ground_y=GROUND_Y + 10.0)

    # -- shadows ------------------------------------------------------------------------
    def long_shadow(self, cr, x, y, w, h, tod="dusk", alpha=1.0):
        """A long soft sun shadow (dusk / golden) cast from the ground point (x, y) by something
        h px tall and w px wide at its foot. Draw it before the caster, inside cam.view(cr, 1.0)."""
        for k, wt in blend(tod):
            if _sun_shadow(k):
                _baked_shadow(cr, x, y, w, h, k, alpha * wt, 1.0)

    def shadow_pass(self, cr, cam, tod, casters=(), benches=(), alpha=1.0):
        """Soft long sun shadows for things that move (dusk / golden): drawn at quarter
        resolution and composited in one upscale, so their edges are soft like the baked ones.
        Call it after paint_back() and before drawing the casters. casters = [(x, y, w, h) or
        (x, y, w, h, alpha)] ground points in world px (w = width at the foot, h = height);
        benches = [BenchSpot] (e.g. bench 2 while it is dragged)."""
        ws = [(k, w) for k, w in blend(tod) if _sun_shadow(k)]
        if not ws or alpha <= 0.0 or (not casters and not benches):
            return
        buf = self._shadow_buf
        if buf is None:
            buf = self._shadow_buf = core.new_surface(core.W // 4, core.H // 4)
        c = cairo.Context(buf)
        c.set_operator(cairo.OPERATOR_CLEAR)
        c.paint()
        c.set_operator(cairo.OPERATOR_OVER)
        c.scale(0.25, 0.25)
        c.transform(cam.matrix(PARALLAX["garden"]))
        for k, w in ws:
            for cs in casters:
                a = cs[4] if len(cs) > 4 else 1.0
                _baked_shadow(c, cs[0], cs[1], cs[2], cs[3], k, a * w)
            for sp in benches:
                _bench_shadow(c, sp, k, w)
        buf.flush()
        cr.save()
        cr.identity_matrix()
        cr.scale(4.0, 4.0)
        cr.set_source_surface(buf, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_BILINEAR)
        cr.paint_with_alpha(core.clamp(alpha))
        cr.restore()

    def pool_light(self, x, y, lit=1.0, tod="night", reach=520.0):
        """S8: the light on something at world (x, y) by the lantern: its warm key inside the
        pool, falling off with distance into the cold night (pass it to draw_* for anything at
        night -- a bench or a character outside the pool reads dark). reach = the pool's radius."""
        lx, ly = LANTERN[0] - 52.0, LANTERN[1] - 0.5 * LANTERN_HEIGHT * LANTERN_SCALE
        d = math.hypot(x - lx, (y - ly) * 0.8)
        k = core.clamp(lit) * (1.0 - core.smoothstep(reach * 0.25, reach, d))
        dark = ch.LIGHTS["blue_hour"].with_(exposure=0.55, rim_strength=0.25, name="night_dark")
        base = light_for(tod) if tod != "night" else dark
        return ch.Light.lerp(base, ch.LIGHTS["lantern_night"], k)

    # -- S8: the town far away ------------------------------------------------------------
    def town_glows(self, cr, cam, t, strength=1.0):
        """S8: the three cold glows of the town under the castle -- the wash-house sign (teal),
        the apothecary's green cross, the tavern's string of lanterns (magenta/amber) -- tiny,
        far away, at the hills plane. Draw after paint_back()."""
        if strength <= 0:
            return
        with cam.view(cr, PARALLAX["hills"]):
            x, y = TOWN_SIGNS["washhouse"]
            fx.glow(cr, x, y, 34.0, "#5fe0d0", 0.5 * strength)
            core.src(cr, "#bff8ee", 0.85 * strength)
            core.rounded_rect(cr, x - 6.0, y - 2.5, 12.0, 5.0, 1.2)
            cr.fill()
            x, y = TOWN_SIGNS["apothecary"]
            fl = 0.85 + 0.15 * math.sin(t * 1.3)
            fx.glow(cr, x, y, 30.0, "#5fe08a", 0.5 * strength * fl)
            core.src(cr, "#c8ffd6", 0.95 * strength)
            cr.rectangle(x - 1.2, y - 4.0, 2.4, 8.0)
            cr.rectangle(x - 4.0, y - 1.2, 8.0, 2.4)
            cr.fill()
            x, y = TOWN_SIGNS["tavern"]
            for i in range(7):
                px = x - 24.0 + 8.0 * i
                py = y + 3.0 * math.sin(math.pi * i / 6.0)
                c = ("#ff6fa8", "#ffb84a", "#e0508a")[i % 3]
                tw = 0.75 + 0.25 * math.sin(t * 3.1 + i * 1.7)
                fx.glow(cr, px, py, 7.0, c, 0.55 * strength * tw)
                core.src(cr, c, 0.9 * strength)
                core.circle(cr, px, py, 1.1)
                cr.fill()


# ----------------------------------------------------------------------------------------
# preview: python3 -m film.scenes._garden
# ----------------------------------------------------------------------------------------

def _preview():
    import time
    from pathlib import Path
    out = Path(__file__).resolve().parents[1] / "build" / "preview"
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    g = Garden(kinds=KINDS)
    print(f"[garden] built {len(KINDS)} times of day in {time.perf_counter() - t0:.1f}s")
    lay = fx.LightLayer()
    for k in KINDS:
        for name, cam in (("wide", core.Camera(960.0, 590.0, 1.0)), ("twoshot", core.Camera(855.0, 790.0, 2.1))):
            s, cr = core.frame()
            L = light_for(k)
            a = time.perf_counter()
            g.paint_back(cr, cam, 1.0, k)
            bench = g.bench(1)
            gx, gy = bench.place(SEATS["gnome"])
            dx, dy = bench.place(SEATS["dragon"])
            g.shadow_pass(cr, cam, k, [(gx, gy, 40.0, 150.0), (dx, dy, 90.0, 330.0)])
            Lg = g.pool_light(gx, gy - 120, 1.0) if k == "night" else L
            Ld = g.pool_light(dx, dy - 250, 1.0) if k == "night" else L
            with cam.view(cr, 1.0):
                post = g.draw_lantern(cr, 1.0, L, lit=1.0 if k == "night" else 0.0)
                g.draw_bench(cr, 1.0, Ld, part="back")
                ch.draw_gnome(cr, gx, gy, SCALE, ch.GnomePose(facing=1, sit=1.0, turn=-0.5), Lg, 1.0)
                ch.draw_dragon(cr, dx, dy, SCALE, ch.DragonPose(facing=-1, sit=1.0, turn=1.1), Ld, 1.0)
                g.draw_bench(cr, 1.0, Ld, part="front")
                if k in ("golden", "blue_hour", "night"):
                    L2 = g.pool_light(BENCH2.x, BENCH2.y - 100, 1.0) if k == "night" else L
                    g.draw_bench(cr, 1.0, L2, which=2, tod=k)
            if k == "night":
                g.town_glows(cr, cam, 1.0)
            g.paint_fg(cr, cam, 1.0, k, alpha=1.0 if name == "wide" else 0.0)
            lc = lay.begin()
            g.light(lc, cam, 1.0, k)
            if k == "night":
                g.lantern_light(lc, post, 1.0, cam=cam)
            fx.post(cr, 1.0, light=lay, **POST[k])
            ms = (time.perf_counter() - a) * 1000
            p = out / f"garden_{k}_{name}.png"
            s.write_to_png(str(p))
            print(f"[garden] {p.name}  {ms:.0f} ms")


if __name__ == "__main__":
    _preview()
