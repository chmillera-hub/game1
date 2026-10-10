"""S3 - The fall (BIBLE section 4 S3, section 9 handoffs S2->S3 and S3->S4).

render(canvas, t) is a pure function of the absolute time t. Every time comes from a named beat or from an SFX
placement in build/timeline.json (+ the hit offsets in build/sfx_timing_notes.md).

The performance is ONE continuous trajectory in the shaft's world coordinates (draw_shaft with scroll 0; the
camera simply follows him down): walk in on the slab -> freeze on the crack -> the slab drops -> his far (left)
gauntlet catches the right lip (hang) -> four slips -> he lets go -> a stoic free fall -> the two-handed thrust
into the right wall (sword_drag) grinding down with sparks -> the bottom. Anger is placed by his PELVIS through
every state change (place_by_pelvis), so blends between differently anchored states never jump.
After the impact we cut into the depths set (S4's set): he lies crumpled (head toward the right wall, facing -1)
and his sword stays stuck in that wall above him, quivering, the end of its gouge cooling.

Shot list (absolute times only for orientation; all derive from beats):
  A  s3 start -> wrong_rock-0.25    CAVERN medium: creeping on, sword raised, dim teal (S2 handoff)
  B  -> wrong_rock+0.33             SHAFT cut-away: he steps onto the slab, the foot plants ON the crack, he
                                    freezes mid-stride; the crack spreads under him
  C  -> collapse+0.14               CLOSE-UP: eyes down at his feet; the second crack: a tiny "...oh." Floor gives
  D  -> grab_ledge+0.85             WIDE cut-away: the slab drops, he drops, the far gauntlet catches the lip
                                    (armor_clank, jolt), he swings, debris rains into the dark shaft
  E  -> slipping-0.05               MEDIUM: hanging, strain, he looks up at his grip
  F  -> slipping+1.95               INSERT: the gauntlet on the dusty lip: slip / catch / slip / catch, grit
  G  -> let_go+0.12                 CLOSE-UP: strain -> the third and fourth slips -> calm acceptance; he lets go
  H  -> falling+1.3                 WIDE: the empty lip; he drops away into the dark (no scream)
  I  -> sword_thrust-0.12           CLOSE-UP falling: the wall streams past, eyes close slowly; time stops;
                                    the eyes SNAP open
  J  -> sword_thrust+1.6            MEDIUM: both hands ram the sword into the wall: sparks, soil, the gouge
  K  -> sword_thrust+3.1            CLOSE-UP: grinding strain in the spark light
  L  -> impact+0.06                 WIDE: the long glowing gouge, the bottom rushing up; IMPACT (dust, jolt)
  M  -> s3 end                      DEPTHS low wide: crumpled, armor settling (clatter bounces), dust, the sword
                                    stuck in the wall above, quivering; stillness
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import skia

from anim import char_anger as A
from anim import env, fx, light
from anim.core import (Camera, beat, clamp, ease_in, ease_in_out, ease_out, hash01, lerp, noise1, paint,
                       scene_span, smoothstep, timeline)
from anim.light import Light
from anim.rig import ArmPose, Pose
from config import H, W

AR = A.ARMS
T0, T1 = scene_span("s3")


def sfx_time(name, after=0.0):
    """First placement of SFX `name` at or after `after` (absolute s)."""
    for s in timeline()["sfx"]:
        if s["name"] == name and s["start"] >= after - 1e-6:
            return s["start"]
    raise KeyError(name)


# =========================================================================== timing (all from names)
WRONG = beat("wrong_rock")
COLLAPSE = beat("collapse")
GRAB = beat("grab_ledge")
SLIP = beat("slipping")
LETGO = beat("let_go")
FALLING = beat("falling")
THRUST = beat("sword_thrust")
IMPACT = beat("impact")
FALL_END = beat("fall_end")
CRACK = sfx_time("rock_crack", T0)
CRACK2 = CRACK + 0.45                                   # second crack (sfx notes)
_DS = sfx_time("dust_slip", T0)
SLIPS = [_DS + d for d in (0.0, 1.15, 2.2, 3.25)]     # fingers slide
CATCHES = [_DS + d for d in (0.55, 1.65, 2.85)]       # ... and hold again
STAB = sfx_time("sword_stab", T0)
SCRAPE = sfx_time("sword_scrape", T0)
JUDDER = SCRAPE + 3.4                                   # the screech starts to judder (sparks pulse)
_CL = sfx_time("armor_clatter", T0)
CLATTER = [_CL + d for d in (0.0, 0.17, 0.31, 0.42, 0.50, 0.56)]

# ---------------------------------------------------------------- cuts
CUT_B = WRONG - 0.25
CUT_C = WRONG + 0.33
CUT_D = COLLAPSE + 0.14
CUT_E = GRAB + 0.85
CUT_F = SLIP - 0.05
CUT_G = SLIP + 1.95
CUT_H = LETGO + 0.12
CUT_I = FALLING + 1.3
CUT_J = THRUST - 0.12
CUT_K = THRUST + 1.6
CUT_L = THRUST + 3.1
CUT_M = IMPACT + 0.06

# =========================================================================== shared helpers (s4 imports them)
RIM_COLD = "#A6C8E6"
FILL_COLD = "#7E9CC4"


def cam_on(pt, zoom, sx=0.5, sy=0.5):
    """Camera at `zoom` that puts stage point pt at screen fraction (sx, sy)."""
    return Camera(pt[0] + (0.5 - sx) * W / zoom, pt[1] + (0.5 - sy) * H / zoom, zoom)


def cam_on_rot(pt, zoom, sx=0.5, sy=0.5, rot=0.0):
    """Like cam_on, for a rotated camera (Camera.apply rotates about the camera centre)."""
    dx, dy = (sx - 0.5) * W / zoom, (sy - 0.5) * H / zoom
    r = math.radians(-rot)
    ox, oy = dx * math.cos(r) - dy * math.sin(r), dx * math.sin(r) + dy * math.cos(r)
    return Camera(pt[0] - ox, pt[1] - oy, zoom, rot)


_FLAT = {}


def draw_flat(c, fn, zoom, res_k=0.8):
    """Draw a static set (fn(canvas) in stage coords) under a ROLLED camera fast: env blits big pre-rasterised
    tiles, and a rotated blit of those is ~10x slower than an axis-aligned one. So render the set unrotated into
    an offscreen covering the view's bounding box and draw that one image under the rolled camera."""
    m = c.getTotalMatrix()
    if abs(m.getSkewX()) < 1e-4 and abs(m.getSkewY()) < 1e-4:
        fn(c)
        return
    vis = c.getLocalClipBounds()
    zr = zoom * res_k
    wl, hl = int(math.ceil(vis.width() * zr)), int(math.ceil(vis.height() * zr))
    if wl > 1800 or hl > 1800:
        zr *= 1800.0 / max(wl, hl)
        wl, hl = int(math.ceil(vis.width() * zr)), int(math.ceil(vis.height() * zr))
    surf = _FLAT.get("s")
    if surf is None:
        surf = _FLAT["s"] = skia.Surface(1800, 1800)
    lc = surf.getCanvas()
    lc.resetMatrix()
    lc.clipRect(skia.Rect(0, 0, wl, hl))
    lc.clear(skia.ColorBLACK)
    lc.scale(zr, zr)
    lc.translate(-vis.left(), -vis.top())
    fn(lc)
    lc.resetMatrix()
    img = surf.makeImageSnapshot(skia.IRect(0, 0, wl, hl))
    c.drawImageRect(img, skia.Rect(0, 0, wl, hl), vis, skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint(),
                    skia.Canvas.kFast_SrcRectConstraint)


def cam_mix(a: Camera, b: Camera, u):
    return Camera.lerp(a, b, clamp(u))


def place_by_pelvis(p: Pose, target, t):
    """Copy of p translated so that its pelvis lands on `target` (stage) at time t (any state / blend)."""
    q = p.copy(x=0.0, y=0.0)
    px, py = A.pelvis_pos(q, t)
    return p.copy(x=target[0] - px, y=target[1] - py)


def dress(p: Pose, at, ambient, lights, rim=0.6, rim_color=RIM_COLD, gain=1.0, tint_amt=0.14, rim_dir=-115.0,
          rim_pos=None, key_dir=None):
    """Anger stays drawn 'lit' (the darkness map darkens him like the set); we only lean his colour toward the
    light he stands in (light_at), add the cold rim that keeps him readable and steer the key direction."""
    r, g, b = light.light_at(at[0], at[1], ambient, lights)
    m = max(r, g, b, 1e-3)
    tint = (int(255 * r / m), int(255 * g / m), int(255 * b / m))
    ex = dict(p.extra)
    if rim_pos is not None:
        ex["rim_pos"] = rim_pos
    else:
        ex["rim_dir"] = rim_dir
    if key_dir is not None:
        ex["key_dir"] = key_dir
    return p.copy(light=gain, tint=tint, tint_amt=tint_amt, rim=rim, rim_color=rim_color, extra=ex)


def finish(canvas, cam, t, ambient, lights, emissive=None, vig=0.45, lift=None):
    """Darkness recipe: (lit world already drawn under cam) -> darkness -> emissives under cam -> vignette."""
    canvas.resetMatrix()
    light.apply_darkness(canvas, cam, ambient=ambient, lights=[L for L in lights if L is not None], t=t,
                         lift=lift)
    if emissive is not None:
        canvas.save()
        cam.apply(canvas, t)
        emissive(canvas)
        canvas.restore()
    canvas.resetMatrix()
    light.vignette(canvas, vig)


def face_life(t, seed=0):
    """Tiny always-on facial life: (look_dx, look_dy, brow) saccade-like drifts that settle and hold."""
    k = math.floor(t / 0.9 + hash01(seed, 5))
    u = (t / 0.9 + hash01(seed, 5)) - k
    a = (hash01(k, seed + 11) - 0.5, hash01(k, seed + 12) - 0.5)
    b = (hash01(k - 1, seed + 11) - 0.5, hash01(k - 1, seed + 12) - 0.5)
    s = ease_out(clamp(u / 0.12))                         # quick move, then hold
    return (lerp(b[0], a[0], s) * 0.16, lerp(b[1], a[1], s) * 0.10, 0.04 * noise1(t * 0.4, seed + 3))


def kick_env(t, times, dur=0.35, freq=9.0):
    """Sum of decaying oscillations started at each of `times` (limb rebounds)."""
    v = 0.0
    for i, t0 in enumerate(times):
        a = t - t0
        if 0 <= a < dur:
            v += (1 - a / dur) ** 2 * math.sin(2 * math.pi * freq * a) * (1.0 / (1 + 0.6 * i))
    return v


# =========================================================================== geometry (shaft world coordinates)
SLAB_Y = env.LEDGE_Y                       # the slab surface he walks on
CRACK_X = 380.0                            # crack origin (env)
WALK_S = 0.5 * A.WALK_ADVANCE * A.WALK_STANCE  # planted foot ahead of the pelvis at the plant
X_PLANT = CRACK_X - WALK_S                 # pelvis x when his right foot comes down on the crack
LIP_X = env.HOLE_X[1]                      # the right lip corner (the slab continues to the right)
GRIP_Y = SLAB_Y - 15.0                     # top of the curled fingers: hooked over the lip, above its surface
# (x, y) of the curled fingers after each slip: they slide toward the edge and off the top
GRIP_STEPS = [(LIP_X + 30.0, SLAB_Y - 18.0), (LIP_X + 21.0, SLAB_Y - 13.0), (LIP_X + 13.0, SLAB_Y - 8.0),
              (LIP_X + 6.0, SLAB_Y - 4.0), (LIP_X - 2.0, SLAB_Y + 2.0)]
WALL_GX = LIP_X - 14.0                     # x of the gouge / blade entry on the right wall of the shaft
EMBED = 0.6
G_FALL, V_MAX = 3000.0, 2400.0             # free fall (stage units/s^2) and the 'time stops' terminal speed
V_END = 520.0                              # speed when he hits the bottom
FEET_DY = 335.0                            # pelvis -> soles in sword_drag (bent legs)


def _pose(**kw):
    ex = kw.pop("extra", {})
    p = Pose(**kw)
    p.extra = dict(ex)
    return p


# ---------------------------------------------------------------- walk (cavern + slab)
def walk_phase(t):
    """Walk phase locked so the right foot plants ON wrong_rock (phase 0), then the freeze mid-stride."""
    if t <= WRONG:
        return (t - WRONG) / A.WALK_CYCLE
    d = 0.25
    return (d / A.WALK_CYCLE) / 3.0 * ease_out((t - WRONG) / d)


def _creep_face(p, t, seed=1):
    lx, ly, br = face_life(t, seed)
    scan = 0.55 * noise1(t * 0.55, seed + 40)
    return p.copy(look_x=clamp(0.25 + scan + lx, -1, 1), look_y=0.05 + ly, brow_furrow=0.35, brow_raise=br,
                  squint=0.12, smile=-0.08)


def slab_walk_pose(t):
    ph = walk_phase(t)
    x = X_PLANT + A.WALK_ADVANCE * ph
    p = _pose(x=x, y=SLAB_Y, facing=1.0, turn=0.5, lean=4.0, arm_r=AR["sword_guard"],
              arm_l=ArmPose(shoulder=24.0, elbow=30.0, wrist=0.0, hand="relaxed"),
              extra=dict(state="walk", phase=ph, sword="hand", shield="back"))
    p = _creep_face(p, t)
    # freeze: eyes snap down to his feet a beat after the crack, head follows a little
    dn = smoothstep((t - (CRACK + 0.22)) / 0.18)
    oh = smoothstep((t - (CRACK2 + 0.12)) / 0.3)
    p = p.copy(look_x=lerp(p.look_x, 0.15, dn), look_y=lerp(p.look_y, 1.0, dn), head_nod=-0.7 * dn,
               brow_furrow=lerp(0.35, 0.12, oh), brow_raise=0.18 * oh,
               lid_l=lerp(1.0, 0.8, dn) * lerp(1.0, 0.86, oh) * A.blink(t + 3),
               lid_r=lerp(1.0, 0.78, dn) * lerp(1.0, 0.86, oh) * A.blink(t + 3), mouth_open=0.05 * oh, squint=lerp(0.12, 0.0, dn),
               breath=0.0 if t > CRACK + 0.2 else None)          # he stops breathing
    return p


# ---------------------------------------------------------------- hang
def grip_at(t):
    """(x, y) of the curled fingers on the lip."""
    g = GRIP_STEPS[0]
    for i, ts in enumerate(SLIPS):
        end = CATCHES[i] if i < len(CATCHES) else LETGO
        if t >= ts:
            u = clamp((t - ts) / max(0.05, end - ts))
            k = ease_out(u) if i < 3 else ease_in_out(u)
            a, b = GRIP_STEPS[i], GRIP_STEPS[i + 1]
            g = (lerp(a[0], b[0], k), lerp(a[1], b[1], k))
    return g


def grip_x(t):
    return grip_at(t)[0]


def slip_jolt(t):
    """Small downward jolt (stage units) of the hand / body at each slip, settling at the catch."""
    v = 0.0
    for i, ts in enumerate(SLIPS):
        a = t - ts
        if 0 <= a < 0.45:
            v += 9.0 * math.sin(math.pi * clamp(a / 0.45)) * (1.0 + 0.3 * i)
    return v


def hang_pose(t):
    a = t - GRAB
    sw = 3.0 + 13.0 * math.exp(-a / 1.4)
    kick = 0.15 + 0.6 * math.exp(-a / 0.9) + 0.25 * sum(math.exp(-max(0.0, t - s) / 0.4) * (t >= s) for s in SLIPS)
    slip = 0.55 * smoothstep((t - SLIPS[3]) / (LETGO - SLIPS[3])) + 0.45 * smoothstep((t - LETGO) / 0.08)
    gx, gy = grip_at(t)
    p = _pose(x=gx, y=gy + slip_jolt(t), facing=1.0, turn=0.66, arm_r=AR["sword_low"], arm_l=AR["rest"],
              extra=dict(state="hang", hang_hand="l", swing=sw, kick=clamp(kick), slip=clamp(slip), sword="hand",
                         shield="back"))
    # face: strain, eyes up at the grip; slips spike it; then the acceptance
    lx, ly, br = face_life(t, 7)
    calm = smoothstep((t - (SLIPS[3] + 0.25)) / 0.7)
    spike = sum(math.exp(-max(0.0, t - s) / 0.5) * (t >= s) for s in SLIPS)
    strain = clamp((0.75 + 0.25 * spike) * (1 - 0.85 * calm))
    look_down = smoothstep((t - (CATCHES[2] + 0.2)) / 0.25) * (1 - smoothstep((t - (SLIPS[3] + 0.55)) / 0.5))
    p = A.expr(p, "strain", strain, t)
    p.extra["grimace"] = clamp(0.35 + 0.5 * spike) * (1 - calm)
    lid = lerp(1.0, 0.72, calm)
    bl = A.blink(t)
    if calm > 0:   # one slow, heavy acceptance blink
        bl = min(bl, 1.0 - 0.95 * math.sin(math.pi * clamp((t - (SLIPS[3] + 0.62)) / 0.5)))
    p = p.copy(look_x=clamp(0.35 + lx - 0.3 * look_down - 0.2 * calm, -1, 1),
               look_y=clamp(lerp(-0.85, 0.9, look_down) * (1 - calm) + 0.15 * calm + ly, -1, 1),
               lid_l=clamp(lid * bl * (1 - 0.15 * look_down)), lid_r=clamp(lid * bl * (1 - 0.15 * look_down)),
               brow_raise=br + 0.05 * calm - 0.1 * (1 - calm), brow_worry=0.1 * calm, smile=lerp(-0.25, -0.05, calm),
               head_nod=lerp(0.25, -0.05, calm) - 0.35 * look_down, mouth_open=0.03 * calm,
               shoulders_up=0.3 * (1 - calm))
    return p


@lru_cache(maxsize=1)
def _hang_start():
    p = hang_pose(GRAB)
    return A.pelvis_pos(p, GRAB), A.hand_pos(p, "l", GRAB)


@lru_cache(maxsize=1)
def _hang_end():
    p = hang_pose(LETGO)
    return A.pelvis_pos(p, LETGO)


# ---------------------------------------------------------------- the drop after the collapse
@lru_cache(maxsize=1)
def _freeze_pelvis():
    return A.pelvis_pos(slab_walk_pose(COLLAPSE), COLLAPSE)


def drop_pose(t):
    """collapse -> grab_ledge: the floor goes, he drops, the far hand finds the lip."""
    u = clamp((t - COLLAPSE) / (GRAB - COLLAPSE))
    (p0x, p0y), ((p1x, p1y), palm) = _freeze_pelvis(), _hang_start()
    tgt = (lerp(p0x, p1x, ease_in_out(u)), p0y + (p1y - p0y) * (0.25 * u + 0.75 * u * u))
    mix = smoothstep(u / 0.3)
    reach = smoothstep((u - 0.6) / 0.38)
    base = slab_walk_pose(min(t, COLLAPSE + 0.02))
    ex = dict(base.extra)
    ex.update(state="walk", state_b="fall", mix=mix, tumble=-6.0 * u, fall_speed=1960.0 * u, arms_w=0.0,
              reach_l=palm, reach_l_w=reach)
    arm_l = ArmPose.blend(ArmPose(24.0, 30.0, 0.0, "relaxed"), AR["hang_reach"], smoothstep(u / 0.45))
    arm_r = ArmPose.blend(AR["sword_guard"], ArmPose(shoulder=96.0, elbow=34.0, wrist=-30.0, hand="hold"),
                          smoothstep(u / 0.4))
    p = base.copy(arm_l=arm_l, arm_r=arm_r, extra=ex, breath=None, head_nod=lerp(-0.35, 0.3, smoothstep(u / 0.5)),
                  look_x=0.3, look_y=lerp(0.9, -0.9, smoothstep((u - 0.1) / 0.3)), eye_wide=0.4 * (1 - u * 0.5),
                  brow_raise=0.3 * (1 - u), brow_furrow=0.25 + 0.3 * u, lid_l=1.0, lid_r=1.0, mouth_open=0.0,
                  smile=-0.2)
    # the last moment: blend into the hang (placed by the pelvis it converges exactly onto the catch)
    hm = smoothstep((t - (GRAB - 0.16)) / 0.16)
    if hm > 0:
        hp = hang_pose(GRAB)
        hx = dict(hp.extra)
        hx.update(state="fall", state_b="hang", mix=hm, tumble=-6.0 * u, fall_speed=1960.0 * u, arms_w=1.0,
                  reach_l=palm, reach_l_w=reach * (1 - hm))
        p = p.copy(arm_l=ArmPose.blend(arm_l, hp.arm_l, hm), arm_r=ArmPose.blend(arm_r, hp.arm_r, hm), extra=hx)
    return place_by_pelvis(p, tgt, t)


# ---------------------------------------------------------------- free fall + drag: pelvis trajectory
def _speed(t):
    if t < LETGO:
        return 0.0
    if t < STAB:
        return V_MAX * math.tanh(G_FALL * (t - LETGO) / V_MAX)
    v0 = V_MAX * math.tanh(G_FALL * (STAB - LETGO) / V_MAX)
    a = t - STAB
    v = V_END + (v0 - V_END) * (0.7 * math.exp(-0.85 * a) + 0.3 * math.exp(-12.0 * a))
    if t > JUDDER:
        v *= 1.0 + 0.2 * math.sin(2 * math.pi * 10.5 * (t - JUDDER)) * smoothstep((t - JUDDER) / 0.25)
    return v


_DT = 1.0 / 480.0


@lru_cache(maxsize=1)
def _ytab():
    n = int((IMPACT + 0.2 - LETGO) / _DT) + 2
    ys = np.zeros(n)
    for i in range(1, n):
        ta = LETGO + (i - 0.5) * _DT
        ys[i] = ys[i - 1] + _speed(ta) * _DT
    return ys


def fall_dist(t):
    """Distance fallen since let_go (stage units)."""
    if t <= LETGO:
        return 0.0
    ys = _ytab()
    f = (min(t, IMPACT) - LETGO) / _DT
    i = int(f)
    if i >= len(ys) - 1:
        return float(ys[-1])
    return float(ys[i] + (ys[i + 1] - ys[i]) * (f - i))


@lru_cache(maxsize=1)
def _drag_offset():
    """pelvis - blade entry for the drag pose (no shake)."""
    p = _pose(x=0.0, y=0.0, facing=1.0, turn=0.66, extra=dict(state="sword_drag", shake=0.0, embed=EMBED))
    return A.pelvis_pos(p, THRUST)


def pelvis_world(t):
    """Pelvis trajectory from let_go to the impact (shaft world coords)."""
    hx, hy = _hang_end()
    od = _drag_offset()
    xd = WALL_GX + od[0]
    u = ease_in_out(clamp((t - (LETGO + 0.2)) / (CUT_J - (LETGO + 0.2))))
    return lerp(hx, xd, u), hy + fall_dist(t)


def entry_y(t):
    """World y of the blade entry (the bottom of the gouge) during the drag."""
    return pelvis_world(t)[1] - _drag_offset()[1]


def _fall_arms(t, k_up=1.0):
    w = noise1(t * 1.7, 61)
    arm_r = ArmPose(shoulder=118.0 + 8 * w, elbow=40.0, wrist=-26.0, hand="hold")
    arm_l = ArmPose(shoulder=132.0 + 10 * noise1(t * 1.5, 62), elbow=36.0, wrist=6.0, hand="relaxed")
    return arm_l, arm_r


def fall_pose(t):
    """let_go -> sword_thrust (and the thrust blend into sword_drag)."""
    v = _speed(t)
    a = t - LETGO
    tum = -4.0 - 7.0 * smoothstep(a / 2.5) + 3.0 * math.sin(a * 0.8)
    arm_l, arm_r = _fall_arms(t)
    ex = dict(state="fall", tumble=tum, fall_speed=max(300.0, v), arms_w=0.0, sword="hand", shield="back")
    p = _pose(facing=1.0, turn=0.42, arm_l=arm_l, arm_r=arm_r, extra=ex)
    # leaving the hang: blend hang -> fall
    hm = smoothstep((t - LETGO) / 0.3)
    if hm < 1.0:
        hp = hang_pose(t)
        hx = dict(hp.extra)
        hx.update(state="hang", state_b="fall", mix=hm, tumble=tum, fall_speed=max(300.0, v), arms_w=1.0 - hm)
        p = hp.copy(arm_l=ArmPose.blend(hp.arm_l, arm_l, hm), arm_r=ArmPose.blend(hp.arm_r, arm_r, hm), extra=hx)
    # face: calm acceptance -> eyes close slowly -> SNAP open
    lx, ly, br = face_life(t, 13)
    close = ease_in_out(clamp((t - (FALLING + 1.45)) / 1.35))
    snap = clamp((t - (THRUST - 0.24)) / 0.07)
    lid = lerp(0.72, 0.0, close)
    lid = lerp(lid, 1.0, snap)
    p = p.copy(look_x=0.1 + lx * (1 - close), look_y=0.1 + ly, lid_l=lid, lid_r=lid, eye_wide=0.35 * snap,
               brow_raise=lerp(0.05 + br, -0.35, snap), brow_furrow=lerp(0.0, 0.75, snap), brow_worry=0.08 * (1 - snap),
               head_nod=lerp(0.1 + 0.12 * close, -0.1, snap), smile=lerp(-0.05, -0.3, snap), mouth_open=0.0)
    if snap > 0:
        p.extra["grimace"] = 0.4 * snap
    # the thrust: twist into sword_drag
    dm = ease_in(clamp((t - CUT_J) / (STAB - CUT_J)))
    if dm > 0:
        ex2 = dict(p.extra)
        ex2.update(state="fall", state_b="sword_drag", mix=dm, embed=EMBED, shake=0.0, arms_w=1.0)
        p = p.copy(extra=ex2)
    return place_by_pelvis(p, pelvis_world(t), t)


def drag_pose(t):
    """sword_thrust -> impact: anchored at the blade entry on the wall."""
    a = t - STAB
    sh = smoothstep(a / 0.12) * (1.0 + 0.7 * smoothstep((t - JUDDER) / 0.2))
    p = _pose(x=WALL_GX, y=entry_y(t), facing=1.0, turn=0.66,
              extra=dict(state="sword_drag", embed=EMBED, shake=sh, sword="hand", shield="back"))
    p = A.expr(p, "strain", 1.0, t)
    p.extra["grimace"] = 0.75 + 0.2 * noise1(t * 3.0, 71)
    lx, ly, br = face_life(t, 17)
    p = p.copy(look_x=0.5 + lx, look_y=-0.55 + ly, lid_l=0.62 * A.blink(t), lid_r=0.6 * A.blink(t),
               squint=0.55, brow_furrow=0.8, head_nod=-0.15)
    return p


def anger_shaft(t):
    """Anger in the shaft world at time t (any time from CUT_B to the impact)."""
    if t < COLLAPSE:
        return slab_walk_pose(t)
    if t < GRAB:
        return drop_pose(t)
    if t < LETGO:
        return hang_pose(t)
    if t < STAB:
        return fall_pose(t)
    return drag_pose(t)


def _floor_w():
    return pelvis_world(IMPACT)[1] + FEET_DY


# =========================================================================== shaft drawing
SHAFT_AMB = 0.12


def shaft_ambient(cam_y):
    """Darker the deeper we are (the cavern light is above)."""
    return lerp(0.12, 0.085, smoothstep((cam_y - 900.0) / 2500.0))


def _sparks_on(t):
    return STAB - 0.01 <= t <= IMPACT + 0.02


def _spark_amount(t):
    if not _sparks_on(t):
        return 0.0
    a = t - STAB
    burst = 1.6 * math.exp(-a / 0.18)
    base = 0.85 + 0.15 * noise1(t * 7.0, 81)
    jud = 1.0 + 0.45 * max(0.0, math.sin(2 * math.pi * 10.5 * (t - JUDDER))) * smoothstep((t - JUDDER) / 0.2)
    fade = 1.0 - smoothstep((t - (IMPACT - 0.05)) / 0.07)
    return (base * jud + burst) * fade


def _shaft_lights(t, p_anger):
    L = list(env.shaft_lights(t))
    if t >= CUT_L:
        fy = _floor_w()
        k = smoothstep((t - CUT_L) / 0.8)
        L.append(Light(360.0, fy + 20.0, 760.0, 0.3 * k, "fungus", "fungus"))
        L.append(Light(430.0, fy + 30.0, 520.0, 1.2 * clamp(1 - (t - IMPACT) / 0.4) * (t >= IMPACT), "#FFE2B0", "flash"))
    if _sparks_on(t):
        ex, ey = WALL_GX, entry_y(t)
        sa = _spark_amount(t)
        L.append(light.spark_light(ex - 10, ey - 20, t, amount=min(1.0, 0.5 * sa), radius=520))
        L.append(Light(ex - 30, ey - 10, 560.0, 0.55 * min(1.0, sa), "#FFC98A", "point"))   # steadier warm key
        L.append(light.flash_light(ex, ey, t - STAB, strength=0.9, radius=900, dur=0.35))
    return L


def _draw_shaft_world(c, t, cam, p, crack=0.0, collapse_t=None, show_floor=False):
    v = _speed(t) if t >= LETGO else 0.0
    blur = 0.0
    follow = cam_follows(t)
    if follow and v > 200:
        blur = min(70.0, 0.55 * v / 24.0)
    gouge = None
    if t >= STAB:
        gouge = (WALL_GX, entry_y(STAB) - 6.0, entry_y(t))
    kw = dict(scroll=0.0, gouge=gouge, crack=crack, collapse_t=collapse_t, blur=blur,
              bottom=(_floor_w() - 30.0) if show_floor else None, dust=0.0)
    if cam.zoom <= 1.25:
        env.draw_shaft(c, t, **kw)
    else:
        draw_shaft_hz(c, t, cam, kw)
    if _sparks_on(t) and t >= STAB:          # soil spat out of the groove (lit), bursts every 0.2 s
        k1 = int((t - STAB) / 0.2)
        for k in range(max(0, k1 - 4), k1 + 1):
            te = STAB + k * 0.2
            fx.debris(c, t, t - te, (WALL_GX - 6, entry_y(te)), seed=400 + k, kind="stone", n=4, speed=520,
                      direction=-150, spread=50, size=0.45, gravity=2200, life=0.8)


def _draw_grit(c, t):
    """Grit trickling from his fingers off the right lip (drawn in front of him: it falls past his arm)."""
    if not (GRAB - 0.05 <= t <= LETGO + 1.5):
        return
    amt = 0.3 + 0.7 * sum(math.exp(-max(0.0, t - s) / 0.6) * (t >= s) for s in SLIPS)
    amt *= 1.0 - smoothstep((t - LETGO - 0.4) / 1.0)
    gx = grip_x(min(t, LETGO))
    fx.dust_fall(c, t, LIP_X - 34, LIP_X - 4, SLAB_Y + 2, amount=clamp(amt), seed=301, length=420, size=1.3)
    for i, ts in enumerate(SLIPS):       # a spill of grit at each slip
        fx.debris(c, t, t - ts, (gx - 14, SLAB_Y - 4), seed=310 + i, kind="stone", n=7, speed=180,
                  direction=120, spread=60, size=0.4, gravity=1800, life=1.0)


_LR_SURF = {}
HZ_WALL = 0.7          # close framings rasterise the periodic shaft wall at this zoom's bucket (= the wides')
HZ_TOP = 1.6           # cap for the slab / cavern-backdrop tiles in close framings (1.15 below zoom 2)
_LIN = skia.SamplingOptions(skia.FilterMode.kLinear)


def _draw_lowres(c, cam, zt, draw_fn, opaque):
    """Run draw_fn(stage canvas) into an offscreen that sees the same view at zoom zt, upscale it onto c."""
    k = zt / cam.zoom
    wl, hl = max(8, int(round(W * k))), max(8, int(round(H * k)))
    surf = _LR_SURF.get((wl, hl, opaque))
    if surf is None:
        surf = _LR_SURF[(wl, hl, opaque)] = skia.Surface(wl, hl)
    lc = surf.getCanvas()
    lc.resetMatrix()
    lc.clear(skia.ColorBLACK if opaque else skia.ColorTRANSPARENT)
    lc.translate(wl / 2.0, hl / 2.0)
    lc.scale(zt, zt)
    if cam.rot:
        lc.rotate(cam.rot)
    lc.translate(-cam.cx, -cam.cy)
    draw_fn(lc)
    img = surf.makeImageSnapshot()
    c.save()
    c.resetMatrix()
    c.drawImageRect(img, skia.Rect(0, 0, wl, hl), skia.Rect(0, 0, W, H), _LIN, skia.Paint(),
                    skia.Canvas.kFast_SrcRectConstraint)
    c.restore()


def draw_shaft_hz(c, t, cam, kw):
    """draw_shaft for close framings. env rasterises the periodic shaft wall as a full-period strip per zoom
    bucket (10k+ px tall at zoom 3) and the slab / cavern backdrop tiles at zoom 3 cost >1 s per miss, so the
    wall is drawn into a low-res offscreen (HZ_WALL) and the slab / lip into one capped at HZ_TOP, both upscaled
    (it is dark, vignetted and mostly motion-blurred); the fresh end of the gouge is redrawn sharp on top."""
    top = env.LEDGE_Y + 200.0
    vis = c.getLocalClipBounds()

    def wall(lc):
        v = lc.getLocalClipBounds()
        lc.clipRect(skia.Rect(v.left() - 10, top, v.right() + 10, v.bottom() + 10))
        env.draw_shaft(lc, t, **dict(kw, gouge=None))
    if vis.bottom() > top:
        _draw_lowres(c, cam, HZ_WALL, wall, True)
    if vis.top() < top + 160.0:
        def slab(lc):
            v = lc.getLocalClipBounds()
            lc.clipRect(skia.Rect(v.left() - 10, v.top() - 10, v.right() + 10, top))
            env.draw_shaft(lc, t, **dict(kw, gouge=None, bottom=None, blur=0.0))
        zt = min(cam.zoom, HZ_TOP if cam.zoom >= 2.0 else 1.15)
        if zt >= cam.zoom - 1e-6:
            c.save()
            c.clipRect(skia.Rect(vis.left() - 10, vis.top() - 10, vis.right() + 10, top))
            env.draw_shaft(c, t, **dict(kw, gouge=None, bottom=None, blur=0.0))
            c.restore()
        else:
            _draw_lowres(c, cam, zt, slab, False)
    if kw.get("gouge") is not None and hasattr(env, "_draw_gouge"):
        gx, y0, y1 = kw["gouge"]
        env._draw_gouge(c, t, (gx, max(y0, y1 - 900.0), y1), 0.0)


def cam_follows(t):
    return (CUT_I <= t < CUT_L) or (CUT_H + 0.6 <= t < CUT_I)


def _draw_sparks(c, t):
    if not _sparks_on(t):
        return
    amt = _spark_amount(t)
    ex, ey = WALL_GX, entry_y(t)
    v = _speed(t)
    fx.sparks(c, t, ex - 4, ey, rate=150 * clamp(amt, 0.3, 2.0), direction=-118, spread=46, speed=900, life=0.45,
              gravity=900, size=1.15, seed=91, alpha=clamp(amt, 0, 1), drift=(0.0, -v), t0=STAB)
    fx.sparks(c, t, ex - 4, ey, rate=60 * clamp(amt, 0.3, 2.0), direction=-160, spread=40, speed=600, life=0.3,
              gravity=900, size=0.8, seed=92, alpha=clamp(amt, 0, 1), drift=(0.0, -v), t0=STAB, glow=False)
    fx.ember_burst(c, t, ex - 6, ey, t - STAB, n=22, seed=93, size=1.3, speed=520, life=0.9)


def _anger_lit(p, t, ambient, L, rim=0.6):
    hc = A.head_center(p, t)
    if _sparks_on(t):
        sp = (WALL_GX - 10, entry_y(t) - 20)
        return dress(p, hc, ambient, L, rim=0.85, rim_color="#FFC27A", rim_pos=sp, key_dir=sp, tint_amt=0.18)
    return dress(p, hc, ambient, L, rim=rim)


def _render_shaft(c, t, cam, *, crack=0.0, collapse_t=None, show_floor=False, vig=0.45, extra_draw=None):
    p = anger_shaft(t)
    amb = shaft_ambient(cam.cy)
    L = _shaft_lights(t, p)
    hc = A.head_center(p, t)
    L.append(Light(hc[0], hc[1] + 120, 520.0, 0.16, FILL_COLD, "point"))     # soft cold fill so he reads
    c.save()
    cam.apply(c, t)
    _draw_shaft_world(c, t, cam, p, crack=crack, collapse_t=collapse_t, show_floor=show_floor)
    A.draw(c, _anger_lit(p, t, amb, L), t)
    _draw_grit(c, t)
    if extra_draw is not None:
        extra_draw(c)
    c.restore()

    def emit(cc):
        _draw_sparks(cc, t)
    finish(c, cam, t, amb, L, emissive=emit, vig=vig)


# =========================================================================== cameras
def _shake(cam, t):
    ev = [(COLLAPSE, 16.0, 0.9), (GRAB, 12.0, 0.45), (STAB, 18.0, 0.5), (IMPACT, 30.0, 0.7)]
    ev += [(s, 2.5, 0.25) for s in SLIPS]
    if t >= JUDDER and t < IMPACT:
        ev.append((JUDDER, 5.0, IMPACT - JUDDER + 0.01))
    if STAB <= t < IMPACT:
        ev.append((STAB, 3.0, IMPACT - STAB))
    return fx.camera_shake(cam, t, ev, freq=14.0, seed=3, rot=False)


def cam_B(t):
    u = clamp((t - CUT_B) / (CUT_C - CUT_B))
    a = Camera(345.0, 300.0, 0.8)
    b = Camera(350.0, 290.0, 0.84)
    return cam_mix(a, b, ease_in_out(u))


def cam_C(t):
    hc = A.head_center(slab_walk_pose(min(t, COLLAPSE)), min(t, COLLAPSE))
    return cam_on((hc[0] + 10, hc[1] + 6), 2.75, 0.5, 0.44)


def cam_D(t):
    u = ease_in_out(clamp((t - CUT_D) / (CUT_E - CUT_D)))
    return cam_mix(Camera(420.0, 700.0, 0.66), Camera(460.0, 760.0, 0.72), u)


def cam_E(t):
    u = ease_in_out(clamp((t - CUT_E) / (CUT_F - CUT_E)))
    hc = A.head_center(hang_pose(CUT_E), CUT_E)          # a steady frame: the body swings inside it
    return cam_on((lerp(hc[0], LIP_X, 0.4), hc[1] - 10), lerp(1.45, 1.55, u), 0.5, 0.56)


def cam_F(t):
    u = ease_in_out(clamp((t - CUT_F) / (CUT_G - CUT_F)))
    return Camera(LIP_X - 30 - 4 * u, SLAB_Y + 120, 2.9 + 0.2 * u)


def cam_G(t):
    p = hang_pose(min(t, LETGO))
    hc = A.head_center(p, min(t, LETGO))
    u = ease_in_out(clamp((t - CUT_G) / (LETGO - CUT_G)))
    return cam_on((hc[0] + 6, hc[1] - 4), lerp(2.55, 2.85, u), 0.5, 0.45)


def cam_H(t):
    hx, hy = _hang_end()
    base = Camera(470.0, 1020.0, 0.62)
    a = clamp((t - (CUT_H + 0.5)) / (CUT_I - CUT_H - 0.5))
    dy = fall_dist(t) * 0.55 * smoothstep(a)
    return Camera(base.cx, base.cy + dy, base.zoom)


def cam_I(t):
    p = fall_pose(t)
    hc = A.head_center(p, t)
    u = clamp((t - CUT_I) / (CUT_J - CUT_I))
    return cam_on((hc[0] + 8, hc[1] + 10), lerp(2.0, 2.4, ease_in_out(u)), 0.5, 0.44)


def cam_J(t):
    py = pelvis_world(t)[1]
    u = ease_in_out(clamp((t - CUT_J) / (CUT_K - CUT_J)))
    return Camera(lerp(420.0, 440.0, u), py - 230.0, lerp(1.1, 1.2, u))


def cam_K(t):
    p = drag_pose(t)
    hc = A.head_center(p, t)
    return cam_on((hc[0] + 40, hc[1] - 20), 2.4, 0.5, 0.45)


def cam_L(t):
    py = pelvis_world(t)[1]
    z = 0.68
    stop = _floor_w() + 60.0 - 0.36 * H / z          # the floor ends up at ~86% of the frame height
    want = py - 40.0
    # follow him, then ease into the stop (smooth min) so the camera does not hit it hard
    k = 140.0
    lo, hi = min(want, stop), max(want, stop)
    cy = lo - k * math.log1p(math.exp(-(hi - lo) / k))
    u = ease_in_out(clamp((t - CUT_L) / (CUT_M - CUT_L)))
    return Camera(lerp(400.0, 420.0, u), cy, z)


# =========================================================================== shot A: the cavern (S2 handoff)
A_U0 = 0.43                                  # where he is on the cavern path at the scene start


def cam_A(t):
    p = _cavern_walk(t)
    u = clamp((t - T0) / (CUT_B - T0))
    return Camera(p.x + lerp(40.0, 70.0, u), 1176.0 - 380.0, 0.98)


def _cavern_walk(t):
    ph = walk_phase(t)
    ph0 = walk_phase(T0)
    sc = 1.04
    x = env.path_point(A_U0)[0] + A.WALK_ADVANCE * sc * (ph - ph0)
    y = 1176.0
    p = _pose(x=x, y=y, scale=sc, facing=1.0, turn=0.5, lean=4.0, arm_r=AR["sword_guard"],
              arm_l=ArmPose(shoulder=24.0, elbow=30.0, wrist=0.0, hand="relaxed"),
              extra=dict(state="walk", phase=ph, sword="hand", shield="back"))
    return _creep_face(p, t)


def shot_A(c, t):
    p = _cavern_walk(t)
    hc = A.head_center(p, t)
    cam = cam_A(t)
    amb = 0.12
    L = list(env.cavern_lights(t))
    L.append(Light(hc[0], hc[1] + 150, 560.0, 0.14, FILL_COLD, "point"))
    c.save()
    cam.apply(c, t)
    env.draw_cavern(c, t, pool_splash_t=t - beat("torch_splash"), torch_float=True)
    A.draw(c, dress(p, hc, amb, L, rim=0.6), t)
    c.restore()

    def emit(cc):
        env.draw_fungi_glow(cc, t, "cavern", exclude=[(p.x - 260, 300, p.x + 330, 1260)])
    finish(c, cam, t, amb, L, emissive=emit, vig=0.45)


# =========================================================================== shot M: the depths (S3 -> S4)
LIE_X = 150.0                                # pelvis x of the lying Anger (depths), head toward the right wall
LIE_Y = env.FLOOR_Y
SWORD_Y = 420.0                              # where the blade is stuck in the right wall (depths coords)
SWORD_ANG = 98.0                             # point direction (deg from up): into the wall, tip a hair down
GOUGE_LEN = 360.0
LIE_EXCLUDE = [(LIE_X - 600, 880, LIE_X + 560, 1240)]     # fungi glow must not draw over him


def wall_x(y):
    """x of the depths' right wall face at height y (as env draws it)."""
    return env._wall_face_x(y) + 140.0 * smoothstep((-200.0 - y) / 700.0)


def sword_entry():
    return wall_x(SWORD_Y) - 4.0, SWORD_Y


def sword_grip(t):
    """Grip of the stuck sword (the blade pivots at its entry and quivers after he is torn off it)."""
    ex, ey = sword_entry()
    a = t - IMPACT
    ang = SWORD_ANG + (7.0 * math.exp(-a / 0.45) * math.sin(2 * math.pi * 8.5 * a) if a > 0 else 0.0)
    d = (A.SWORD_GRIP * 0.5 + 10.0 + A.SWORD_BLADE * (1.0 - EMBED))
    r = math.radians(ang)
    return ex - math.sin(r) * d, ey + math.cos(r) * d, ang


def draw_stuck_sword(c, t, light_k=1.0):
    gx, gy, ang = sword_grip(t)
    ex, ey = sword_entry()
    # the end of the gouge it carved down the wall
    pts = []
    for i in range(13):
        yy = ey - GOUGE_LEN * (1 - i / 12.0)
        pts.append((wall_x(yy) - 6.0 + 3.0 * noise1(yy / 40.0, 501), yy))
    path = skia.Path()
    path.moveTo(*pts[0])
    for q in pts[1:]:
        path.lineTo(*q)
    c.drawPath(path, paint("#2A1E18", 0.7, stroke=16.0))
    c.drawPath(path, paint("#060506", 0.95, stroke=8.0))
    c.drawPath(path, paint("#B8A898", 0.45, stroke=2.0))
    A.draw_sword(c, gx, gy, ang, 1.0, light=light_k, embed=EMBED)


def gouge_heat(t):
    return clamp(1.0 - (t - IMPACT) / 3.2) ** 1.5 if t >= IMPACT else 1.0


def draw_gouge_glow(c, t):
    """EMISSIVE: the cooling hot end of the gouge at the blade."""
    k = gouge_heat(t)
    if k <= 0.01:
        return
    ex, ey = sword_entry()
    path = skia.Path()
    path.moveTo(wall_x(ey - 120) - 6, ey - 120)
    path.lineTo(ex - 2, ey)
    c.drawPath(path, paint("#FF7A2A", 0.55 * k, stroke=5.0, blend="add"))
    fx.ember_burst(c, t, ex - 6, ey, t - IMPACT, n=10, seed=511, size=0.8, speed=160, life=1.2)
    from anim.core import glow
    glow(c, ex - 4, ey, 36.0, "#FF8A3A", 0.5 * k)


def bottom_lights(t, strength=1.0):
    L = list(env.depths_lights(t, strength))
    ex, ey = sword_entry()
    k = gouge_heat(t)
    if k > 0.01:
        L.append(Light(ex - 30, ey + 10, 360.0, 0.55 * k, "#FF9A50", "point"))
    return L


def crumpled_pose(t, seed=21):
    """Crumpled on his back (facing -1: head toward the right wall); out cold. Armor settles on the clatter."""
    a = t - IMPACT
    bump = sum(kick_env(t, [ct], dur=0.22, freq=6.0) * (6.0 - 0.8 * i) for i, ct in enumerate(CLATTER))
    flop = kick_env(t, CLATTER, dur=0.3, freq=5.0)
    arm_r = ArmPose(shoulder=4.0 + 8.0 * flop, elbow=18.0 - 6.0 * flop, wrist=10.0, hand="relaxed")
    arm_l = ArmPose(shoulder=-6.0 + 6.0 * flop, elbow=22.0 + 6.0 * flop, wrist=0.0, hand="relaxed")
    p = _pose(x=LIE_X, y=LIE_Y, facing=-1.0, turn=0.32, arm_r=arm_r, arm_l=arm_l, bounce=-abs(bump),
              head_tilt=4.0 * flop, lid_l=0.0, lid_r=0.0, mouth_open=0.08, brow_worry=0.2,
              breath=0.25 * math.sin(2 * math.pi * 0.22 * t) * smoothstep((a - 0.8) / 1.0),
              extra=dict(state="crumpled", arms_w=0.0, sword=None, shield="back", bruised=1.0,
                         dazed=0.5, grimace=0.15))
    return p


def shot_M(c, t):
    p = crumpled_pose(t)
    hc = A.head_center(p, t)
    u = ease_in_out(clamp((t - (IMPACT + 0.7)) / (T1 - IMPACT - 0.7)))
    cam = cam_mix(Camera(345.0, 800.0, 1.02), Camera(352.0, 830.0, 1.09), u)
    cam = fx.camera_shake(cam, t, [(IMPACT, 22.0, 0.6)] + [(ct, 3.0, 0.15) for ct in CLATTER], freq=14, seed=7)
    amb = 0.105
    L = bottom_lights(t)
    L.append(Light(hc[0] - 120, hc[1] + 40, 600.0, 0.2, FILL_COLD, "point"))
    c.save()
    cam.apply(c, t)
    dust = lerp(1.0, 0.75, clamp((t - IMPACT) / 2.6))
    env.draw_depths(c, t, dust=dust, shake=0.6 * clamp(1 - (t - IMPACT) / 2.0))
    draw_stuck_sword(c, t, light_k=1.0)
    A.draw(c, dress(p, hc, amb, L, rim=0.55, rim_dir=-100.0), t)
    impact_dust(c, t)
    c.restore()

    def emit(cc):
        env.draw_fungi_glow(cc, t, "depths", exclude=LIE_EXCLUDE)
        draw_gouge_glow(cc, t)
    finish(c, cam, t, amb, L, emissive=emit, vig=0.5)


def impact_dust(c, t):
    """The impact dust cloud (shared with s4 so it keeps settling across the cut)."""
    a = t - IMPACT
    if 0 <= a <= 4.6:
        fx.dust_cloud(c, t, LIE_X + 120, LIE_Y + 10, a, size=2.0, seed=531, n=18, life=4.6, alpha=0.7)
        fx.debris(c, t, a, (LIE_X + 120, LIE_Y - 30), seed=532, kind="stone", n=10, speed=520, direction=-90,
                  spread=150, floor_y=LIE_Y + 20, size=0.7, life=3.0)


# =========================================================================== the shaft shots
def shot_B(c, t):
    cam = _shake(cam_B(t), t)
    cr = 0.55 * smoothstep((t - CRACK) / 0.18) + 0.45 * smoothstep((t - CRACK2) / 0.15)
    _render_shaft(c, t, cam, crack=cr)


def shot_C(c, t):
    cam = cam_C(t)
    if t > COLLAPSE:   # the floor goes: the face drops out of the frame, the camera jolts after it
        a = t - COLLAPSE
        cam = Camera(cam.cx, cam.cy + 90.0 * ease_in(clamp(a / 0.14)), cam.zoom)
    cam = _shake(cam, t)
    cr = 0.55 * smoothstep((t - CRACK) / 0.18) + 0.45 * smoothstep((t - CRACK2) / 0.15)
    _render_shaft(c, t, cam, crack=cr, collapse_t=(t - COLLAPSE) if t >= COLLAPSE else None, vig=0.55)


def shot_D(c, t):
    cam = _shake(cam_D(t), t)
    _render_shaft(c, t, cam, crack=1.0, collapse_t=t - COLLAPSE)


def shot_E(c, t):
    cam = _shake(cam_E(t), t)
    _render_shaft(c, t, cam, collapse_t=t - COLLAPSE, vig=0.5)


def shot_F(c, t):
    cam = _shake(cam_F(t), t)
    _render_shaft(c, t, cam, collapse_t=t - COLLAPSE, vig=0.55)


def shot_G(c, t):
    cam = _shake(cam_G(t), t)
    _render_shaft(c, t, cam, collapse_t=t - COLLAPSE, vig=0.55)


def shot_H(c, t):
    cam = cam_H(t)
    _render_shaft(c, t, cam, collapse_t=t - COLLAPSE, vig=0.5)


def shot_I(c, t):
    cam = cam_I(t)
    _render_shaft(c, t, cam, collapse_t=t - COLLAPSE, vig=0.6)


def shot_J(c, t):
    cam = _shake(cam_J(t), t)
    _render_shaft(c, t, cam, collapse_t=t - COLLAPSE, vig=0.5)


def shot_K(c, t):
    cam = _shake(cam_K(t), t)
    _render_shaft(c, t, cam, collapse_t=t - COLLAPSE, vig=0.55)


def shot_L(c, t):
    cam = _shake(cam_L(t), t)

    def floor_dust(cc):
        a = t - IMPACT
        if a >= 0:
            fx.dust_cloud(cc, t, pelvis_world(IMPACT)[0], _floor_w(), a, size=2.2, seed=541, n=16, life=3.0)
    _render_shaft(c, t, cam, collapse_t=t - COLLAPSE, show_floor=True, extra_draw=floor_dust)


SHOTS = [(T0, shot_A), (CUT_B, shot_B), (CUT_C, shot_C), (CUT_D, shot_D), (CUT_E, shot_E), (CUT_F, shot_F),
         (CUT_G, shot_G), (CUT_H, shot_H), (CUT_I, shot_I), (CUT_J, shot_J), (CUT_K, shot_K), (CUT_L, shot_L),
         (CUT_M, shot_M)]


def shot_at(t):
    fn = SHOTS[0][1]
    for t0, f in SHOTS:
        if t >= t0:
            fn = f
    return fn


def render(canvas, t):
    shot_at(t)(canvas, t)


# =========================================================================== motion-locked SFX
def sfx_events():
    ev = []
    for tk in A.step_times("walk", T0, WRONG + 1e-3, walk_phase(T0)):
        ev.append({"name": ("armor_step", "armor_step_2", "armor_step_3")[len(ev) % 3], "start": round(tk, 3),
                   "gain_db": -13.0})
    ev.append({"name": "armor_shift", "start": round(CRACK + 0.24, 3), "gain_db": -20.0})   # the freeze
    ev.append({"name": "armor_shift", "start": round(CATCHES[0] + 0.05, 3), "gain_db": -18.0})
    ev.append({"name": "armor_shift", "start": round(CUT_J + 0.02, 3), "gain_db": -12.0})  # the twist / thrust
    return ev
