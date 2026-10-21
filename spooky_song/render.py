"""Stage and draw 'Clickety-Clack!' frame by frame (Cairo), streamed to ffmpeg.

    python render.py                 # full render -> build/segments/
    python render.py --still 3 40.5  # PNG stills at those times (build/stills/)
"""
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import cairo
import numpy as np

import drawkit as dk
import scene as sc
import skeleton as sk
from drawkit import INK, clamp, ease_out_back, ellipse, hash01, hexc, lerp, radial, smooth, text_center, vnoise
from song import TITLE

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, 'build')
W, H, FPS = 1080, 1920, 24
TL = json.load(open(os.path.join(BUILD, 'timeline.json')))
LIPS = dict(np.load(os.path.join(BUILD, 'lipsync.npz')))
SEC = {s['name']: s for s in TL['sections']}
DURATION = TL['duration']
SUB_FONT, TITLE_FONT, HAND_FONT = dk.SUB_FONT, dk.TITLE_FONT, dk.HAND_FONT

dk.A_EMO.update({
    'nervous': dict(brow_y=7, brow_tilt=12, lid_top=.12, lid_bot=.1, smile=-.05, mouth_w=.7, blush=.6,
                    chestL=.6, chestR=.6, squash=-.03, tilt=-4),
    'scared': dict(brow_y=14, brow_tilt=8, lid_top=0, eye_scale=1.15, open=.3, smile=-.2, mouth_w=.6,
                   squash=-.04, armL=-10, armR=-10, mouthL=.5, mouthR=.5),
    'pointing_self': dict(brow_y=10, brow_tilt=6, lid_top=0, eye_scale=1.1, open=.15, smile=.1,
                          chestR=.95, blush=.4),
    'boo': dict(brow_y=18, lid_top=0, eye_scale=1.22, open=1.0, mouth_w=.85, smile=.2, squash=.14,
                armL=-70, armR=-70, bob=.3, blush=.3),
    'dancing': dict(brow_y=10, happy=.85, smile=.95, open=.2, armL=-40, armR=-40, blush=.5, bob=1.6),
    'singing_soft': dict(brow_y=9, brow_tilt=5, lid_top=.04, lid_bot=.22, smile=.6, blush=.55, glint=1.45,
                         chestL=.45, chestR=.45),
})
dk.S_EMO.update({'wink': dict(lid_top=.3, lid_bot=.3, brow_asym=12, smile=.85, glow=.8)})


def sec_beat(name):
    return 60.0 / SEC[name]['bpm']


def bar_t(name, k):
    return SEC[name]['t0'] + k * 4 * sec_beat(name)


def talk_lines(section=None):
    out = []
    for ln in TL['talk']:
        for s in TL['sections']:
            if s['t0'] <= ln['t0'] < s['t1']:
                if section is None or s['name'] == section:
                    out.append(ln)
    return out


def word_time(line, word, default=None):
    for w, s, e in line['words']:
        if ''.join(c for c in w.lower() if c.isalpha()).startswith(word.lower()):
            return s
    return default if default is not None else line['t0']


# ── the director: keyframe tracks for everyone ───────────────────────────────
EMO, GAZE, STYLE, POS, SHOTS = {}, {}, {}, {}, []
SKEL = ['M', 'K1', 'K2', 'K3', 'K4']
CAST_SKEL = {
    'M': dict(s=0.95, hat='bowler', scarf=hexc('#ff8a2a'), baton=True),
    'K1': dict(s=0.88, hat='cap'),
    'K2': dict(s=0.86, hat=None),
    'K3': dict(s=0.76, hat='flower', scarf=hexc('#e2456a')),
    'K4': dict(s=0.66, hat='beanie'),
}
HOME = dict(sc.GRAVES, A=(330, 1085), S=sc.SIMMER_AT)


def emo(t, c, name):
    EMO.setdefault(c, []).append((t, name))


def gaze(t, c, target):
    GAZE.setdefault(c, []).append((t, target))


def style(t, c, name, dur=None):
    STYLE.setdefault(c, []).append((t, name, dur))


def move(t, c, xy, dur=0.9):
    POS.setdefault(c, []).append((t, xy, dur))


def shot(t, name):
    SHOTS.append((t, name))


def everyone(t, name, who=SKEL, dur=None):
    for c in who:
        style(t, c, name, dur)


def direct():
    # opening frame: Alice drifting in, skulls and hands poking up from the graves
    for c in SKEL:
        style(0, c, 'peek' if c == 'M' else 'hands')
        emo(0, c, 'sly' if c == 'M' else 'jolly')
        gaze(0, c, 'A')
    emo(0, 'A', 'curious')
    gaze(0, 'A', 'moon')
    emo(0, 'S', 'asleep')
    gaze(0, 'S', 'A')
    move(0, 'A', (300, 1100), 0.01)
    move(0.01, 'A', (390, 1085), 6.0)
    shot(0, 'establish')
    gaze(2.2, 'A', 'graves')
    psst = talk_lines('intro')[0]
    t_you = word_time(psst, 'yes')
    t_mid = word_time(psst, 'midnight')
    emo(psst['t0'], 'A', 'startled')
    gaze(psst['t0'] + 0.15, 'A', 'M')
    shot(psst['t0'], 'marrow_peek')
    emo(psst['t0'], 'M', 'sly')
    emo(t_you, 'A', 'pointing_self')
    shot(t_you, 'alice')
    emo(t_mid - 0.1, 'A', 'scared')
    gaze(t_mid, 'A', 'clock')
    shot(t_mid, 'establish')

    # verse 1 — out of the graves
    v = 'verse1'
    b = sec_beat(v)
    t0 = SEC[v]['t0']
    move(t0 + 0.1, 'A', (sc.HIDE_STONE[0], 1135), 0.6)        # dart behind the tombstone
    emo(t0, 'A', 'scared')
    gaze(t0 + 0.5, 'A', 'M')
    style(t0, 'M', 'climb', 8 * b)
    emo(t0, 'M', 'singing')
    gaze(t0, 'M', 'cam')
    shot(t0, 'marrow')
    t2 = bar_t(v, 2)
    for i, c in enumerate(['K1', 'K2', 'K3', 'K4']):
        style(t2 + i * 0.25 * b, c, 'climb', 6 * b)
        emo(t2 + i * 0.25 * b, c, 'jolly')
        gaze(t2, c, 'cam')
    style(t2, 'M', 'conduct')
    shot(t2, 'wide')
    emo(t2 + 2 * b, 'A', 'surprised')
    gaze(t2, 'A', 'crew')
    everyone(bar_t(v, 4), 'dust')
    shot(bar_t(v, 4), 'crew')
    everyone(bar_t(v, 5), 'polish')
    everyone(bar_t(v, 6), 'tap')
    shot(bar_t(v, 6), 'feet')
    everyone(bar_t(v, 7), 'sway')
    shot(bar_t(v, 7), 'alice_hide')
    emo(bar_t(v, 7), 'A', 'amazed')
    gaze(bar_t(v, 7), 'A', 'crew')

    chorus_moves = ['clap', 'groove', 'point_up', 'shimmy', 'kick', 'shimmy', 'spin', 'jazz']

    def chorus(name, shots):
        b = sec_beat(name)
        moves = chorus_moves if name != 'chorus3' else chorus_moves[:6] + ['cheer', 'jazz']
        for k, m in enumerate(moves):
            everyone(bar_t(name, k), m)
        for c in SKEL:
            emo(bar_t(name, 0), c, 'singing')
            emo(bar_t(name, 7), c, 'belting')
            gaze(bar_t(name, 0), c, 'cam')
        for k, s in shots:
            shot(bar_t(name, k), s)

    # chorus 1 — Alice watches from her hiding place and starts to smile
    chorus('chorus1', [(0, 'wide'), (4, 'crew'), (6, 'wide'), (7, 'alice_hide')])
    emo(bar_t('chorus1', 0), 'A', 'curious')
    emo(bar_t('chorus1', 3), 'A', 'happy')
    emo(bar_t('chorus1', 7), 'A', 'shy')
    gaze(bar_t('chorus1', 7), 'A', 'cam')

    # verse 2 — meet the band
    v = 'verse2'
    style(bar_t(v, 0), 'M', 'conduct')
    emo(bar_t(v, 0), 'M', 'jolly')
    for c in ['K1', 'K2', 'K3', 'K4']:
        style(bar_t(v, 0), c, 'groove')
        emo(bar_t(v, 0), c, 'jolly')
    emo(bar_t(v, 0), 'S', 'gleeful')
    gaze(bar_t(v, 0), 'S', 'cam')
    emo(bar_t(v, 1), 'S', 'wink')
    gaze(bar_t(v, 1) + 0.5 * sec_beat(v), 'S', 'A')
    shot(bar_t(v, 0), 'simmer')
    shot(bar_t(v, 2), 'pumpkin')
    shot(bar_t(v, 4), 'cat')
    shot(bar_t(v, 5), 'bat')
    shot(bar_t(v, 6), 'wide')
    move(bar_t(v, 6), 'A', (275, 1180), 1.6)
    emo(bar_t(v, 6), 'A', 'happy')
    gaze(bar_t(v, 6), 'A', 'M')
    emo(bar_t(v, 1), 'A', 'happy')

    # chorus 2 — Alice is coaxed onto the dance floor
    chorus('chorus2', [(0, 'wide'), (4, 'two'), (6, 'wide')])
    emo(bar_t('chorus2', 0), 'A', 'dancing')
    style(bar_t('chorus2', 4), 'M', 'beckon')
    gaze(bar_t('chorus2', 4), 'M', 'A')
    emo(bar_t('chorus2', 4), 'M', 'warm')
    emo(bar_t('chorus2', 4), 'A', 'shy')
    gaze(bar_t('chorus2', 4), 'A', 'M')
    # the crew shuffles aside to make room for her
    move(bar_t('chorus2', 5) + 1.0, 'M', (660, 1395), 1.2)
    move(bar_t('chorus2', 5) + 0.8, 'K1', (235, 1385), 1.2)
    move(bar_t('chorus2', 5) + 0.8, 'K3', (318, 1300), 1.2)
    move(bar_t('chorus2', 5) + 1.0, 'A', (450, 1195), 1.4)
    emo(bar_t('chorus2', 6), 'A', 'dancing')

    # the band stops: "your turn!"
    lines = talk_lines('stop')
    yt, um = lines[0], lines[1]
    everyone(SEC['stop']['t0'], 'idle')
    style(yt['t0'], 'M', 'point_A')
    emo(yt['t0'], 'M', 'gleeful')
    for c in ['K1', 'K2', 'K3', 'K4']:
        gaze(yt['t0'], c, 'A')
        emo(yt['t0'], c, 'curious')
        style(yt['t0'], c, 'listen')
    gaze(yt['t0'], 'M', 'A')
    shot(yt['t0'], 'two')
    emo(yt['t0'] + 0.4, 'A', 'surprised')
    emo(um['t0'], 'A', 'nervous')
    gaze(um['t0'], 'A', 'floor')
    shot(um['t0'], 'alice')
    pff = [a for a in TL['acts'] if a[1] == 'pff'][0]
    emo(pff[0], 'A', 'determined')
    gaze(pff[0], 'A', 'cam')
    emo(pff[0] + 1.0, 'A', 'deflated')
    gaze(pff[0] + 1.1, 'A', 'floor')
    shot(pff[0] + 1.25, 'crew')
    for c in SKEL:
        emo(pff[0] + 1.3, c, 'concerned')
    style(pff[0] + 1.3, 'M', 'idle')

    # bridge — the heart-to-heart
    L = talk_lines('bridge')
    emo(L[0]['t0'], 'A', 'sad')
    gaze(L[0]['t0'], 'A', 'floor')
    shot(L[0]['t0'], 'alice')
    gaze(word_time(L[0], 'bones'), 'A', 'self')
    gaze(L[1]['t0'], 'A', 'M')
    emo(L[1]['t0'] + 0.5, 'A', 'sad')
    shot(L[2]['t0'], 'marrow')
    emo(L[2]['t0'], 'M', 'gentle')
    style(L[2]['t0'], 'M', 'kneel')
    gaze(L[2]['t0'], 'M', 'A')
    gaze(word_time(L[2], 'look'), 'M', 'crew')
    gaze(word_time(L[2], 'nobody'), 'M', 'A')
    shot(L[3]['t0'], 'wide')
    emo(L[3]['t0'], 'M', 'warm')
    t_bones = word_time(L[3], 'bones')
    for c in ['K1', 'K2', 'K3', 'K4']:
        style(t_bones, c, 'clap', 1.2)
        emo(t_bones, c, 'gleeful')
        style(t_bones + 1.2, c, 'listen')
    t_pot = word_time(L[3], 'pot')
    emo(t_pot, 'S', 'gleeful')
    t_cat = word_time(L[3], 'cat')
    for c in SKEL + ['A']:
        gaze(t_cat, c, 'C')
    emo(t_cat, 'A', 'curious')
    shot(L[4]['t0'] - 0.2, 'cat')
    emo(L[4]['t1'] + 0.1, 'A', 'giggly')
    shot(L[5]['t0'], 'simmer')
    emo(L[5]['t0'], 'S', 'warm')
    gaze(L[5]['t0'], 'S', 'A')
    gaze(L[5]['t0'], 'A', 'S')
    shot(L[6]['t0'], 'two')
    style(L[6]['t0'], 'M', 'lean_in')
    emo(L[6]['t0'], 'M', 'curious')
    gaze(L[6]['t0'], 'M', 'A')
    gaze(L[6]['t0'], 'A', 'M')
    emo(L[6]['t0'] + 0.5, 'A', 'curious')
    shot(L[7]['t0'], 'alice')
    emo(L[7]['t0'], 'A', 'realizing')
    gaze(L[7]['t0'], 'A', 'up')
    gaze(word_time(L[7], 'boo'), 'A', 'M')
    emo(word_time(L[7], 'boo'), 'A', 'hopeful')
    shot(L[8]['t0'], 'marrow')
    emo(L[8]['t0'], 'M', 'gleeful')
    style(L[8]['t0'], 'M', 'cheer')
    for c in SKEL:
        gaze(L[8]['t0'], c, 'A')

    # BOO!
    t_boo = SEC['boo']['t0']
    b = sec_beat('boo')
    emo(t_boo - 0.1, 'A', 'boo')
    gaze(t_boo, 'A', 'cam')
    shot(t_boo, 'alice')
    shot(t_boo + 3 * b, 'wide')
    for c in SKEL:
        style(t_boo + 3 * b, c, 'blown')
        emo(t_boo + 3 * b, c, 'surprised')
        style(t_boo + 6.5 * b, c, 'cheer')
        emo(t_boo + 6.5 * b, c, 'gleeful')
    emo(t_boo + 3 * b, 'S', 'laughing')
    emo(t_boo + 6.5 * b, 'A', 'joyful')

    # final chorus — Alice in the middle of it all
    move(SEC['chorus3']['t0'], 'A', (540, 1195), 1.0)
    move(SEC['chorus3']['t0'], 'M', (770, 1395), 1.0)
    move(SEC['chorus3']['t0'], 'K1', (250, 1385), 1.0)
    move(SEC['chorus3']['t0'], 'K3', (330, 1300), 1.0)
    move(SEC['chorus3']['t0'], 'K4', (835, 1306), 1.0)
    move(SEC['chorus3']['t0'], 'K2', (925, 1390), 1.0)
    chorus('chorus3', [(0, 'wide'), (2, 'group'), (4, 'wide'), (6, 'alice'), (7, 'wide')])
    emo(SEC['chorus3']['t0'], 'A', 'dancing')
    emo(bar_t('chorus3', 6), 'A', 'boo')
    emo(bar_t('chorus3', 7), 'A', 'joyful')
    emo(SEC['chorus3']['t0'], 'S', 'gleeful')

    # tag — everyone together
    tg = 'tag'
    for c in SKEL:
        style(SEC[tg]['t0'], c, 'sway')
        emo(SEC[tg]['t0'], c, 'jolly')
        gaze(SEC[tg]['t0'], c, 'A')
    move(SEC[tg]['t0'], 'K3', (335, 1310), 2.0)
    move(SEC[tg]['t0'], 'K4', (790, 1312), 2.0)
    move(SEC[tg]['t0'], 'M', (750, 1395), 2.0)
    move(SEC[tg]['t0'], 'K1', (300, 1385), 2.0)
    move(SEC[tg]['t0'], 'K2', (885, 1390), 2.0)
    emo(SEC[tg]['t0'], 'A', 'singing_soft')
    gaze(SEC[tg]['t0'], 'A', 'cam')
    shot(SEC[tg]['t0'], 'group')
    p2 = [p for p in TL['phrases'] if p['section'] == tg][1]
    emo(p2['t0'], 'A', 'beaming')
    for c in SKEL:
        gaze(p2['t0'], c, 'cam')
        emo(p2['t0'], c, 'belting')
    shot(p2['words'][-1][1], 'wide')

    # button
    t_b = SEC['button']['t0'] + 0.5
    everyone(t_b, 'jazz')
    for c in SKEL:
        emo(t_b, c, 'gleeful')
    emo(t_b, 'A', 'joyful')
    emo(t_b, 'S', 'laughing')
    shot(SEC['end']['t0'], 'end')


direct()
for d in (EMO, GAZE, STYLE, POS):
    for k in d:
        d[k].sort(key=lambda e: e[0])
SHOTS.sort(key=lambda e: e[0])


# ── evaluating tracks ────────────────────────────────────────────────────────
def last(events, t):
    cur = None
    for e in events:
        if e[0] > t:
            break
        cur = e
    return cur


def emo_blend(c, t, base, table, default, blend=0.35):
    cur = dict(base, **table.get(default, {}))
    for et, name in EMO.get(c, []):
        if et > t:
            break
        tgt = dict(base, **table.get(name, {}))
        w = smooth((t - et) / blend)
        cur = {k: lerp(cur[k], tgt[k], w) for k in base}
    return cur


def pos_of(c, t):
    p = HOME[c]
    for et, xy, d in POS.get(c, []):
        if et > t:
            break
        w = smooth((t - et) / d)
        p = (lerp(p[0], xy[0], w), lerp(p[1], xy[1], w))
    return p


def section_at(t):
    for s in TL['sections']:
        if s['t0'] <= t < s['t1']:
            return s
    return TL['sections'][-1]


def beats_at(t):
    s = section_at(t)
    return (t - s['t0']) / (60.0 / s['bpm']), s


def lip(c, t):
    arr = LIPS[c]
    i = t * int(LIPS['rate'])
    i0 = int(i)
    if i0 < 0 or i0 + 1 >= len(arr):
        return 0.0
    return lerp(arr[i0], arr[i0 + 1], i - i0)


def blink(c, t, dur=0.16):
    seed = sum(map(ord, c)) * 7
    k = int(t / 3.1)
    best = 0.0
    for kk in (k - 1, k, k + 1):
        bt = kk * 3.1 + hash01(kk, seed) * 2.4
        u = (t - bt) / dur
        if 0 <= u <= 1:
            best = max(best, math.sin(math.pi * u) ** 0.7)
    for et, _ in EMO.get(c, []):
        u = (t - et - 0.04) / dur
        if 0 <= u <= 1 and hash01(int(et * 10), seed) < 0.6:
            best = max(best, math.sin(math.pi * u) ** 0.7)
    return best


def skeleton_pose(c, t):
    b, s = beats_at(t)
    seed = SKEL.index(c)
    events = STYLE.get(c, [])
    cur = last(events, t)
    prev = None
    for e in events:
        if e is cur:
            break
        prev = e

    def eval_style(e):
        if e is None:
            return sk.dance('idle', b, seed)
        t0, name, dur = e
        u = clamp((t - t0) / dur) if dur else 0.0
        if name == 'peek':
            return sk.pose(rise=0.17, head=4 * math.sin(t * 1.3), armL=-170, armR=170, elbL=-20, elbR=20)
        if name == 'hands':
            w = math.sin(t * 6 + seed)
            return sk.pose(rise=0.06, armL=-172 + 8 * w, armR=172 - 8 * w, spread=0.8 + 0.2 * w)
        if name == 'climb':
            start = 0.17 if c == 'M' else 0.06
            p = sk.dance('climb', b, seed, u)
            p['rise'] = lerp(start, 1.0, smooth(u * 1.15))
            if u >= 0.85:
                g = sk.dance('conduct' if c == 'M' else 'groove', b, seed)
                return sk.blend_pose(p, g, smooth((u - 0.85) / 0.15))
            return p
        if name == 'point_A':
            return sk.pose(armR=-100 if pos_of(c, t)[0] > pos_of('A', t)[0] else 100, elbR=0, armL=-20, lean=-5,
                           head=-6, dy=-2)
        if name == 'kneel':
            return sk.pose(crouch=0.9, lean=-10, head=-14, armR=-60 + 30 * math.sin(t * 1.5), elbR=-40,
                           armL=-30, elbL=-50)
        if name == 'lean_in':
            return sk.pose(crouch=0.55, lean=-16, head=-16, armL=-40, elbL=-90, armR=40, elbR=90)
        if name == 'blown':
            k = math.sin(min(u * 6, 1) * math.pi / 2) if dur else 1.0
            return sk.pose(lean=18, head=14, armL=-120, armR=120, elbL=-40, elbR=40, crouch=0.3,
                           shake=0.6, dy=-2)
        return sk.dance(name, b, seed, u)

    p = eval_style(cur)
    if cur is not None and prev is not None:
        w = smooth((t - cur[0]) / 0.22)
        if w < 1:
            p = sk.blend_pose(eval_style(prev), p, w)
    return p


def skeleton_face(c, t):
    f = emo_blend(c, t, sk.FACE_DEF, sk.FACE_EMO, 'neutral')
    src = 'M' if c == 'M' else 'K'
    singing = lip(src, t)
    if c != 'M' and not any(c in ph['singers'] and ph['t0'] - 0.2 <= t <= ph['t1'] + 0.2 for ph in TL['phrases']):
        singing = 0.0                         # this crew member isn't singing right now
    f['jaw'] = clamp(f['jaw'] + singing * 0.85)
    f['brow_y'] += 4 * singing
    return f


def gaze_target(name, me, t, at):
    fixed = {'cam': (0, 0.05), 'up': (0.05, -1), 'floor': (0.15, 1), 'self': (0.35, 0.85)}
    if name in fixed:
        return fixed[name]
    p = at.get(name)
    if p is None:
        return (0, 0.05)
    dx, dy = p[0] - me[0], p[1] - me[1]
    d = math.hypot(dx, dy) + 1e-6
    k = min(1.0, d / 150)
    return (dx / d * k, dy / d * k)


def gaze_of(c, t, me, at):
    cur = (0, 0.05)
    for et, name in GAZE.get(c, []):
        if et > t:
            break
        tg = gaze_target(name, me, t, at)
        w = smooth((t - et) / 0.16)
        cur = (lerp(cur[0], tg[0], w), lerp(cur[1], tg[1], w))
    k = math.floor(t / 1.4 + hash01(int(t / 1.4), sum(map(ord, c))) * 0.5)
    return (cur[0] + 0.06 * (hash01(k, 3) - 0.5), cur[1] + 0.05 * (hash01(k, 5) - 0.5))


# ── per-frame character states ───────────────────────────────────────────────
def alice_state(t, at):
    p = emo_blend('A', t, dk.A_DEF, dk.A_EMO, 'curious')
    x, y = pos_of('A', t)
    s = 0.5
    g = dict(p)
    b, sec = beats_at(t)
    op = lip('A', t)
    metered = sec.get('bars') and sec['name'] not in ('boo',)
    dancing = metered and sec['name'] in ('chorus2', 'chorus3', 'tag', 'button') and not (
        sec['name'] == 'chorus2' and t < bar_t('chorus2', 0) + 0.3)
    if dancing:
        y += -10 * abs(math.sin(math.pi * b))                     # bob on the beat with everyone
        g['tilt'] = p['tilt'] + 7 * math.sin(math.pi * b)
        g['armL'] = p['armL'] + 18 * math.sin(math.pi * b)
        g['armR'] = p['armR'] - 18 * math.sin(math.pi * b)
    else:
        y += p['bob'] * 10 * math.sin(t * 2 * math.pi * 0.42)
        g['tilt'] = p['tilt'] + 2 * math.sin(t * 0.9)
    if sec['name'] == 'verse2' and t > bar_t('verse2', 6):           # tapping along
        g['armR'] = lerp(g['armR'], 30 + 30 * abs(math.sin(math.pi * b)), smooth((t - bar_t('verse2', 6)) / 0.5))
    if sec['name'] == 'verse1' or (sec['name'] == 'chorus1'):        # peeking over the stone
        y += 14 * math.sin(t * 1.1)
    g['squash'] = p['squash'] + 0.02 * op
    g['open'] = clamp(p['open'] * (1 - 0.5 * op) + 0.85 * op)
    g['smile'] = p['smile'] * (1 - 0.35 * op)
    g['blink'] = blink('A', t)
    g['flip'] = 1.0
    # spin on the spin bars when she's dancing
    if dancing and sec['name'] == 'chorus2':
        k6 = bar_t(sec['name'], 6)
        u = ((t - k6) / (60 / sec['bpm']) - 0.9) / 1.1
        if 0 <= u < 1:
            g['flip'] = math.cos(2 * math.pi * smooth(u))
            if abs(g['flip']) < 0.08:
                g['flip'] = 0.08 if g['flip'] >= 0 else -0.08
    # the failed clack: scrunch up... puff
    for t0, name, d in TL['acts']:
        if name == 'pff' and t0 <= t <= t0 + d:
            u = t - t0
            g['squash'] += -0.08 * smooth(u / 0.6) + 0.12 * math.sin(math.pi * clamp((u - 0.6) / 0.25))
            g['tilt'] += 3 * math.sin(u * 30) * (u < 0.6)
    # BOO: swell up, then a gust
    tb = SEC['boo']['t0']
    if tb - 0.2 <= t <= SEC['boo']['t1']:
        u = t - tb
        g['squash'] += 0.06 * smooth(u / 0.3)
        g['s_boost'] = 1 + 0.18 * smooth(u / 0.4) * (1 - smooth((u - 2.6) / 0.8))
    g['glow'] = 1.0
    g['heart'] = 0
    if SEC['tag']['t0'] <= t:
        g['inner'] = 0.6 * smooth((t - SEC['tag']['t0']) / 2)
    g['gaze'] = gaze_of('A', t, (x, y - 100 * s), at)
    g['tilt'] += 3 * g['gaze'][0]
    g.update(x=x, y=y, s=s * g.get('s_boost', 1.0))
    return g


def simmer_state(t, at):
    p = emo_blend('S', t, dk.S_DEF, dk.S_EMO, 'asleep')
    c = dict(p)
    x, y = HOME['S']
    op = lip('S', t)
    b, sec = beats_at(t)
    c['squash'] = p['squash'] + 0.015 * math.sin(t * 2 * math.pi * 0.3) + 0.03 * op
    if sec['name'] in ('verse2', 'chorus1', 'chorus2', 'chorus3', 'tag') and p['lid_top'] < 0.9:
        c['squash'] += 0.025 * abs(math.sin(math.pi * b))
    c['tilt'] = 1.5 * math.sin(t * 0.5)
    if p['happy'] > 0.9 and p['open'] > 0.5:
        c['squash'] += 0.03 * math.sin(t * 2 * math.pi * 7)
    c['open'] = clamp(p['open'] * (1 - 0.5 * op) + 0.8 * op)
    c['blink'] = blink('S', t, 0.24)
    v2 = SEC['verse2']['t0']
    br = talk_lines('bridge')[5]
    c['blorps'] = [v2 + 0.3 + k * 0.9 for k in range(4)] + [br['t0'] + 0.4, br['t1'] - 0.3]
    c['glow'] = p['glow'] + 0.3 * (t > SEC['chorus3']['t0'])
    c['gcol'] = (0.85, 0.75, 1.0) if t > SEC['boo']['t0'] else (0.55, 1.0, 0.78)
    c['fire'] = 0.0
    c['gaze'] = gaze_of('S', t, (x, y), at)
    c.update(x=x, y=y, s=0.5)
    return c


def hat_flight(c, t, skull):
    """Hats blow off at the BOO and drop back on at the final chorus."""
    tb = SEC['boo']['t0'] + 3 * sec_beat('boo')
    t_back = SEC['chorus3']['t0'] + 1.2
    if not (tb <= t <= t_back):
        return None
    u = t - tb
    up = min(u, 1.4)
    x = skull[0] + 160 * up + 40 * math.sin(u * 3)
    y = skull[1] - 120 - 260 * up + 80 * up * up
    rot = u * 5
    land = smooth((t - (t_back - 0.8)) / 0.8)
    return (lerp(x, skull[0], land), lerp(y, skull[1] - 0, land), lerp(rot, 0, land))


# ── cameras ──────────────────────────────────────────────────────────────────
def camera(t, at):
    st = last(SHOTS, t)
    name = st[1] if st else 'wide'
    m = at['M_body']
    a = at['A']
    fixed = {
        'establish': (540, 960, 1.0), 'wide': (540, 1125, 1.2), 'crew': (560, 1175, 1.45), 'feet': (560, 1280, 1.75),
        'group': (560, 1160, 1.4),
        'simmer': (sc.SIMMER_AT[0] + 40, sc.SIMMER_AT[1] - 60, 2.4), 'pumpkin': (sc.PUMPKIN_AT[0], sc.PUMPKIN_AT[1] - 40, 2.7),
        'cat': (sc.CAT_AT[0], sc.CAT_AT[1] - 10, 2.7), 'bat': (880, 860, 2.4), 'end': (540, 960, 1.0),
        'alice_hide': (300, 1100, 1.9),
    }
    if name in fixed:
        cx, cy, z = fixed[name]
    elif name == 'alice':
        cx, cy, z = a[0], a[1] + 60, 2.1
    elif name == 'marrow':
        cx, cy, z = m[0], m[1] + 70, 1.7
    elif name == 'marrow_peek':
        cx, cy, z = 560, 1290, 2.1
    elif name == 'two':
        cx, cy, z = (a[0] + m[0]) / 2, (a[1] + m[1]) / 2 + 60, 1.45
    else:
        cx, cy, z = 540, 960, 1.0
    hw, hh = W / 2 / z, H / 2 / z
    return round(clamp(cx, hw, W - hw), 0), round(clamp(cy, hh, H - hh), 0), round(z, 3)


def apply_cam(ctx, cam):
    cx, cy, z = cam
    ctx.translate(W / 2, H / 2)
    ctx.scale(z, z)
    ctx.translate(-cx, -cy)


BG = {}


def background(cam):
    if cam not in BG:
        if len(BG) > 30:
            BG.clear()
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
        ctx = cairo.Context(surf)
        apply_cam(ctx, cam)
        sc.bg_dance(ctx)
        BG[cam] = surf
    return BG[cam]


# ── overlays ─────────────────────────────────────────────────────────────────
SING_COL = {'M': hexc('#f1e6c8'), 'crew': hexc('#f1e6c8'), 'A': hexc('#f4f0ff'), 'S': hexc('#ffc27a'),
            'ALL': hexc('#ffd36b'), 'C': hexc('#ffe27a')}


def phrase_color(ph):
    s = set(ph['singers'])
    if s == {'A'}:
        return SING_COL['A']
    if 'A' in s:
        return SING_COL['ALL']
    return SING_COL['crew']


def layout_words(ctx, words, size, maxw=900):
    ctx.select_font_face(SUB_FONT)
    ctx.set_font_size(size)
    space = ctx.text_extents(' ').x_advance + 4
    widths = [ctx.text_extents(w).x_advance for w in words]
    lines, cur, cw = [], [], 0
    for i, w in enumerate(widths):
        if cur and cw + space + w > maxw:
            lines.append(cur)
            cur, cw = [], 0
        cw += (space if cur else 0) + w
        cur.append(i)
    lines.append(cur)
    if len(lines) == 2:                                     # balance the two lines
        best = None
        for k in range(1, len(words)):
            a = sum(widths[:k]) + space * (k - 1)
            b = sum(widths[k:]) + space * (len(words) - k - 1)
            if max(a, b) <= maxw and (best is None or max(a, b) < best[0]):
                best = (max(a, b), [list(range(k)), list(range(k, len(words)))])
        if best:
            lines = best[1]
    return lines, widths, space


def draw_box(ctx, x0, y0, x1, y1, a):
    r = 26
    ctx.new_path()
    ctx.arc(x0 + r, y0 + r, r, math.pi, 1.5 * math.pi)
    ctx.arc(x1 - r, y0 + r, r, 1.5 * math.pi, 2 * math.pi)
    ctx.arc(x1 - r, y1 - r, r, 0, 0.5 * math.pi)
    ctx.arc(x0 + r, y1 - r, r, 0.5 * math.pi, math.pi)
    ctx.close_path()
    ctx.set_source_rgba(0.03, 0.02, 0.06, 0.55 * a)
    ctx.fill()


def draw_lyrics(ctx, t):
    """Karaoke lyrics for the song, plain subtitles for spoken lines."""
    item = None
    phs = TL['phrases']
    for i, ph in enumerate(phs):
        nxt = phs[i + 1]['t0'] - 0.35 if i + 1 < len(phs) else ph['t1'] + 1.0
        end = min(ph['t1'] + 0.8, nxt)
        if ph['t0'] - 0.35 <= t < end:
            item = ('sing', ph, ph['t0'] - 0.35, end)
    for ln in TL['talk']:
        if ln['t0'] - 0.05 <= t <= ln['t1'] + 0.35:
            item = ('talk', ln, ln['t0'] - 0.05, ln['t1'] + 0.35)
    if not item:
        return
    kind, data, s0, s1 = item
    a = clamp((t - s0) / 0.1) * clamp((s1 - t) / 0.1)
    size = 60
    if kind == 'sing':
        words = [w for w, _, _ in data['words']]
        times = [(ws, we) for _, ws, we in data['words']]
        col = phrase_color(data)
    else:
        spk = data['spk']
        words = data['text'].split()
        if spk == 'ALL':
            words = ['BOO!']
        times = [(ws, we) for _, ws, we in data['words']] if spk != 'ALL' else [(data['t0'], data['t1'])]
        col = SING_COL['ALL'] if spk == 'ALL' else SING_COL.get(spk, SING_COL['M'])
    lines, widths, space = layout_words(ctx, words, size)
    lh = size * 1.12
    bottom = 1545
    top = bottom - lh * len(lines)
    widest = max(sum(widths[i] for i in ln) + space * (len(ln) - 1) for ln in lines)
    note_w = 46 if kind == 'sing' else 0
    pad = 26
    x0 = W / 2 - (widest + note_w) / 2 - pad
    draw_box(ctx, x0, top - 14, W / 2 + (widest + note_w) / 2 + pad, bottom + 22, a)
    if kind == 'sing':
        ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(40)
        ctx.move_to(x0 + pad - 4, top + lh - 16)
        ctx.set_source_rgba(*hexc('#ff9a3c'), a)
        ctx.show_text('♪')
    for li, ln in enumerate(lines):
        lw = sum(widths[i] for i in ln) + space * (len(ln) - 1)
        x = W / 2 - lw / 2 + note_w / 2
        y = top + lh * (li + 1) - 12
        for i in ln:
            ws, we = times[i] if i < len(times) else (s0, s1)
            if kind == 'sing':
                if ws <= t < we:
                    c, alpha = hexc('#ff9a3c'), 1.0
                elif t >= we:
                    c, alpha = col, 1.0
                else:
                    c, alpha = col, 0.5
            else:
                c, alpha = col, 1.0
            ctx.select_font_face(SUB_FONT)
            ctx.set_font_size(size)
            ctx.move_to(x, y)
            ctx.text_path(words[i])
            ctx.set_source_rgba(0.02, 0.01, 0.04, a)
            ctx.set_line_width(7)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.stroke_preserve()
            ctx.set_source_rgba(*c, a * alpha)
            ctx.fill()
            x += widths[i] + space


def draw_title(ctx, t):
    a = 1 - smooth((t - 5.0) / 0.9)
    if a <= 0:
        return
    y = 200 + 5 * math.sin(t * 1.6)
    text_center(ctx, TITLE, W / 2 + 4, y + 8, TITLE_FONT, 150, (0, 0, 0, 0.45 * a), bold=True)
    text_center(ctx, TITLE, W / 2, y, TITLE_FONT, 150, hexc('#f4e6c4', a), outline=hexc('#120c18', a), ow=12, bold=True)
    text_center(ctx, 'a moonlight bone dance', W / 2, y + 74, SUB_FONT, 48, hexc('#ffb54d', a),
                outline=hexc('#120c18', a), ow=6)


def draw_pop_text(ctx, t, t0, text, x, y, size=150, life=2.2, col='#f4e6c4'):
    u = t - t0
    if not (0 <= u <= life):
        return
    sc_ = ease_out_back(u / 0.3) * (1 + 0.03 * math.sin(u * 20))
    a = 1 - smooth((u - life + 0.4) / 0.4)
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(-0.1 + 0.03 * math.sin(u * 8))
    ctx.scale(sc_, sc_)
    text_center(ctx, text, 0, 0, HAND_FONT, size, hexc(col, a), outline=hexc('#120c18', a), ow=12)
    ctx.restore()


def draw_wind(ctx, t):
    tb = SEC['boo']['t0'] + 3 * sec_beat('boo')
    u = t - tb
    if not (-0.2 <= u <= 2.0):
        return
    for k in range(14):
        f = (u * 1.4 + k / 14) % 1.0
        x = lerp(380, 1150, f)
        y = 700 + 60 * k + 30 * math.sin(f * 6 + k)
        a = 0.35 * math.sin(math.pi * f) * (1 - smooth((u - 1.5) / 0.5))
        ctx.new_path()
        ctx.move_to(x - 120, y)
        ctx.curve_to(x - 60, y - 20, x, y + 20, x + 60, y - 10)
        ctx.set_source_rgba(0.85, 0.9, 1.0, a)
        ctx.set_line_width(5)
        ctx.stroke()


def draw_end(ctx, t, frame):
    u = t - SEC['end']['t0']
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(dk.linear(0, 0, 0, H, [(0, hexc('#1e1527', 1)), (1, hexc('#0b0910', 1))]))
    ctx.fill()
    dk.stars(ctx, 90, H, 21)
    text_center(ctx, TITLE, 540, 260, TITLE_FONT, 140, hexc('#f4e6c4'), outline=hexc('#120c18'), ow=12, bold=True)
    a = smooth((u - 0.4) / 0.6)
    for i, line in enumerate(['starring', 'Alice  ·  Mister Marrow  ·  Granny Simmer', 'and the Moonlight Bone Crew']):
        text_center(ctx, line, 540, 380 + i * 62, SUB_FONT, 44 if i != 1 else 50, hexc('#e9dcae' if i != 1 else '#ffd36b', a))
    b = smooth((u - 1.0) / 0.6)
    text_center(ctx, 'original song & story, grown from a drawing by Alice', 540, 1700, SUB_FONT, 40, hexc('#cdbfa0', b))
    # the gang takes a bow
    beat = u * 1.6
    f = sk.face_params('gleeful')
    f['jaw'] = 0.2
    sk.draw_skeleton(ctx, 290, 1600, 1.05, sk.dance('cheer', beat, 0), f, (0.2, 0.0), blink('M', t), t, frame,
                     hat='bowler', scarf=hexc('#ff8a2a'))
    g = dict(dk.A_DEF, **dk.A_EMO['joyful'])
    g.update(x=760, y=1230 + 10 * math.sin(t * 2.4), s=0.58, tilt=5 * math.sin(t * 1.2), flip=1.0, glow=1.0, heart=0,
             squash=0.03 * math.sin(t * 3), gaze=(-0.2, 0.0), blink=blink('A', t))
    g['armR'] = -60 + 28 * math.sin(u * 2 * math.pi * 1.4)
    dk.draw_ghost(ctx, g, t, frame)
    cc = dict(dk.S_DEF, **dk.S_EMO['laughing'])
    cc.update(x=560, y=1560, s=0.5, tilt=2 * math.sin(t), squash=0.03 * math.sin(t * 9), blink=0, gaze=(-0.3, 0),
              glow=0.9, gcol=(0.85, 0.75, 1.0), fire=0.0, blorps=[])
    dk.draw_cauldron(ctx, cc, t, frame)
    dk.draw_hearts(ctx, 760, 900 - 6 * math.sin(t * 1.3), 1.0, t, b)


def render_frame(frame):
    t = frame / FPS
    sec = section_at(t)
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    if sec['name'] == 'end':
        draw_end(ctx, t, frame)
        return surf
    b, _ = beats_at(t)
    # skeleton poses and where their skulls are (for gazes and cameras)
    poses, faces, skulls = {}, {}, {}
    for c in SKEL:
        poses[c] = skeleton_pose(c, t)
        x, ground = pos_of(c, t)
        skulls[c] = sk.skull_world(x, ground, CAST_SKEL[c]['s'], poses[c])
    apos = pos_of('A', t)
    at = {'M': skulls['M'], 'A': (apos[0], apos[1] - 65), 'S': (sc.SIMMER_AT[0], sc.SIMMER_AT[1] - 20),
          'C': (sc.CAT_AT[0], sc.CAT_AT[1] - 40), 'moon': sc.MOON_XY, 'clock': (790, 880), 'graves': (560, 1380),
          'crew': (560, 1150), 'M_body': (pos_of('M', t)[0], skulls['M'][1] + 160)}
    g = alice_state(t, at)
    at['A'] = (g['x'], g['y'] - 65)
    cam = camera(t, at)

    ctx.set_source_surface(background(cam), 0, 0)
    ctx.paint()
    ctx.save()
    apply_cam(ctx, cam)

    # owl, bats, band in the back
    v1 = SEC['verse1']['t0']
    owl_awake = smooth((t - (v1 + 4 * sec_beat('verse1') * 1.0)) / 0.3) * (1 - smooth((t - v1 - 8) / 0.5))
    sc.draw_owl(ctx, 118, 905, 0.9, t, max(owl_awake, 0.15))
    s_name = sec['name']
    playing = s_name in ('verse2', 'chorus1', 'chorus2', 'chorus3', 'tag', 'intro', 'verse1', 'button', 'boo')
    cat_mouth = lip('C', t)
    cat_lids = 0.55 if cat_mouth < 0.1 else 0.3
    sc.draw_cat(ctx, sc.CAT_AT[0], sc.CAT_AT[1], 0.75, t, playing and s_name != 'intro', b, cat_lids, cat_mouth)
    bat_t = t * 0.35
    bx = 880 + 110 * math.cos(bat_t * 2 * math.pi)
    by = 840 + 50 * math.sin(bat_t * 4 * math.pi)
    if s_name == 'verse2' and bar_t('verse2', 5) <= t < bar_t('verse2', 6):
        bx, by = 880, 860
    toot = 0.0
    if s_name in ('verse2', 'chorus2', 'chorus3'):
        ph = (b % 4) / 4
        toot = max(0.0, math.sin(2 * math.pi * ph)) if s_name == 'verse2' and bar_t('verse2', 5) <= t < bar_t('verse2', 6) else 0.0
    sc.draw_bat(ctx, bx, by, 0.85, t, toot)

    # depth-sorted characters
    items = []
    for c in SKEL:
        x, ground = pos_of(c, t)
        items.append((ground, 'skel', c, x, ground))
    items.append((HOME['S'][1] + 60, 'simmer', 'S', 0, 0))
    items.append((sc.PUMPKIN_AT[1] + 80, 'pumpkin', 'P', 0, 0))
    hiding = t < bar_t('verse2', 6) + 0.8
    items.append((1300 if hiding else 1420, 'alice', 'A', 0, 0))
    items.append((1330, 'hidestone', None, 0, 0))
    for depth, kind, c, x, ground in sorted(items, key=lambda e: e[0]):
        if kind == 'skel':
            p = poses[c]
            f = skeleton_face(c, t)
            cfg = CAST_SKEL[c]
            gz = gaze_of(c, t, skulls[c], at)
            rise = p['rise']
            clip = None
            if rise < 0.999:
                clip = ground - 2
                p = dict(p)
                p['dy'] = p['dy'] + (1 - rise) * 470
            hat_off = hat_flight(c, t, skulls[c]) if cfg.get('hat') else None
            sk.draw_skeleton(ctx, x, ground, cfg['s'], p, f, gz, blink(c, t), t, frame, hat=cfg.get('hat'),
                             scarf=cfg.get('scarf'), baton=cfg.get('baton') and rise > 0.9 and s_name in ('verse1', 'verse2'),
                             hat_off=hat_off, clip_ground=clip)
            if rise < 0.999:
                sc.grave_mound(ctx, x, ground, 0.82 if c in ('K3', 'K4') else 1.0)
        elif kind == 'simmer':
            cs = simmer_state(t, at)
            dk.draw_cauldron(ctx, cs, t, frame)
            dk.draw_steam_squiggles(ctx, cs['x'], cs['y'], cs['s'], t, 0.5)
        elif kind == 'pumpkin':
            ph = b % 1.0
            hit = max(0.0, 1 - ph * 4) if playing and s_name not in ('intro',) else 0.0
            sc.draw_pumpkin_drummer(ctx, sc.PUMPKIN_AT[0], sc.PUMPKIN_AT[1], 0.55, t, ph, hit)
        elif kind == 'alice':
            dk.draw_ghost(ctx, g, t, frame)
        elif kind == 'hidestone':
            if hiding:
                dk.tombstone(ctx, sc.HIDE_STONE[0], sc.HIDE_STONE[1] + 85, 130, 185, -0.05)
    for x, y, r, seed in ((80, 1690, 60, 1), (1000, 1660, 52, 2)):
        dk.pumpkin(ctx, x, y, r, t, 0.5 + 0.5 * vnoise(t * 6, seed))
    draw_wind(ctx, t)
    # hearts at the very end of the tag
    tg = SEC['tag']
    if t > tg['t1'] - 4.0:
        f = smooth((t - (tg['t1'] - 4.0)) / 0.8)
        dk.draw_hearts(ctx, g['x'], g['y'] - 250 - 18 * (t - tg['t1'] + 4), 0.85 * f, t, f)
    ctx.restore()

    dk.vignette(ctx, 0.5)
    if t < 6:
        draw_title(ctx, t)
    # word pops
    draw_pop_text(ctx, t, SEC['boo']['t0'] + 0.05, 'BOO!', 540, 520, 230, 3.0)
    for ph in TL['phrases']:
        if ph['section'] == 'chorus3':
            for w, ws, we in ph['words']:
                if w.startswith('BOO'):
                    draw_pop_text(ctx, t, ws, 'BOO!', 300, 450, 150, 1.6)
    draw_pop_text(ctx, t, SEC['button']['t0'] + 0.55, 'BOO!', 540, 480, 200, 1.9, '#ffd36b')
    for t0, name, d in TL['acts']:
        if name == 'pff':
            draw_pop_text(ctx, t, t0 + 0.7, 'pff.', 760, 650, 90, 1.4, '#cdbfa0')
    draw_lyrics(ctx, t)
    return surf


def render_range(args):
    start, end, path = args
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr0', '-s', f'{W}x{H}',
           '-r', str(FPS), '-i', '-', '-c:v', 'libx264rgb', '-qp', '0', '-preset', 'ultrafast', path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(start, end):
        surf = render_frame(f)
        surf.flush()
        proc.stdin.write(bytes(surf.get_data()))
    proc.stdin.close()
    proc.wait()
    return path


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--still':
        os.makedirs(os.path.join(BUILD, 'stills'), exist_ok=True)
        for ts in sys.argv[2:]:
            render_frame(int(float(ts) * FPS)).write_to_png(os.path.join(BUILD, 'stills', f'still_{float(ts):07.2f}.png'))
        return
    total = int(math.ceil(DURATION * FPS))
    workers = int(os.environ.get('WORKERS', os.cpu_count() or 4))
    nseg = workers * 3
    bounds = [round(total * i / nseg) for i in range(nseg + 1)]
    seg_dir = os.path.join(BUILD, 'segments')
    os.makedirs(seg_dir, exist_ok=True)
    jobs = [(bounds[i], bounds[i + 1], os.path.join(seg_dir, f'seg{i:02d}.mkv')) for i in range(nseg)]
    with Pool(workers) as pool:
        paths = pool.map(render_range, jobs, chunksize=1)
    with open(os.path.join(seg_dir, 'list.txt'), 'w') as fh:
        for p in paths:
            fh.write(f"file '{p}'\n")
    print(f'rendered {total} frames')


if __name__ == '__main__':
    main()
