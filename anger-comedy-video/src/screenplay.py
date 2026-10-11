"""The screenplay + choreography: 'Anger Goes to a Comedy Show'.

Adapted from the user's 'Gemini bot stand-up / Anger meltdown' story.  Every
spoken line is synthesized first so its real duration drives the timing; the
acting (faces, eyes, lids, brows, posture, hands) is keyed around each line.
"""
from timeline import Timeline, ik, arm_anchor
from tts import synth, caption_text
from sets import ROW_X
from common import FPS

A, M, DB, B, S, G = 'anger', 'me', 'doubt', 'boredom', 'stranger', 'gemini'
AISLE = 110

SHOTS = {
    'title':    dict(world='aud', cx=150, cy=-372, z=0.9),
    'row':      dict(world='aud', cx=0, cy=-250, z=0.5),
    'two_ma':   dict(world='aud', cx=150, cy=-300, z=0.95),
    'doubt':    dict(world='aud', cx=-600, cy=-350, z=1.5),
    'boredom':  dict(world='aud', cx=-300, cy=-350, z=1.5),
    'anger':    dict(world='aud', cx=300, cy=-350, z=1.5),
    'anger_cu': dict(world='aud', cx=300, cy=-366, z=2.5),
    'me':       dict(world='aud', cx=0, cy=-360, z=1.5),
    'me_cu':    dict(world='aud', cx=0, cy=-382, z=2.5),
    'db_two':   dict(world='aud', cx=-450, cy=-330, z=1.0),
    'mb_two':   dict(world='aud', cx=-150, cy=-330, z=1.0),
    'stage_wide': dict(world='stage', cx=0, cy=-420, z=0.8),
    'stage_med':  dict(world='stage', cx=0, cy=-330, z=1.3),
    'stage_cu':   dict(world='stage', cx=0, cy=-410, z=2.2),
}

SPEAKER_COLORS = {
    'me': (120, 230, 215), 'anger': (255, 120, 95), 'doubt': (200, 180, 255),
    'boredom': (180, 200, 220), 'stranger': (140, 220, 120), 'gemini': (120, 235, 255),
    'narr': (255, 244, 220),
}


class Director:
    def __init__(self, tl):
        self.tl = tl
        self.t = 0.0

    def wait(self, d):
        self.t += d
        return self.t

    def say(self, who, text, fx=(), speed=None, pitch=None, gain=1.0, vo=False, post=0.55,
            at=None, bob=1.0, brow=1.0, cap=True):
        r = synth(who, text, tuple(fx), speed, pitch, gain)
        t0 = self.t if at is None else at
        line = dict(actor=who, speaker='narr' if vo else who, t0=t0, t1=t0 + r['dur'],
                    env=r['env'], round=r['round'], fps=FPS, voiceover=vo, wav=r['wav'],
                    caption=caption_text(text) if cap else '', fx=tuple(fx), bob=bob, brow=brow,
                    frags=r['frags'] if cap else [])
        self.tl.say_line(line)
        if at is None:
            self.t = line['t1'] + post
        return line['t0'], line['t1']

    def shot(self, name, t=None, dur=0.0, kind='io', **over):
        t = self.t if t is None else t
        sh = dict(SHOTS[name])
        sh.update(over)
        w = sh.pop('world')
        fol = sh.pop('follow', '')
        self.tl.set('cam', t, world=w, follow=fol)
        sh.setdefault('fw', 1.0 if fol else 0.0)
        sh.setdefault('fdx', 0.0)
        sh.setdefault('fdy', 0.0)
        self.tl.key('cam', t, dur, kind, **sh)

    def drift(self, t0, t1, **kw):
        """slow camera move between t0 and t1"""
        self.tl.key('cam', t0, t1 - t0, 'io', **kw)

    def sfx(self, name, t=None, gain=1.0, **kw):
        self.tl.add_sfx(name, self.t if t is None else t, gain, **kw)

    def burst(self, *a, **k):
        self.tl.burst(*a, **k)

    def music(self, name, t0, t1, gain=1.0, fade_in=0.5, fade_out=1.0):
        self.tl.music.append(dict(name=name, t0=t0, t1=t1, gain=gain, fade_in=fade_in, fade_out=fade_out))


def build():
    tl = Timeline()
    for n, x in ROW_X.items():
        tl.actor(n, 'char', x=float(x), y=0.0)
    tl.actor(G, 'bot', x=-640.0, y=0.0)
    tl.actor('cam', 'cam', world='aud', follow='', fw=0.0, fdx=0.0, fdy=0.0, cx=150.0, cy=-372.0, z=0.9,
             shake=0.0, desat=0.0, dark=0.0, flash=0.0, sepia=0.0, muffle=0.0)
    tl.actor('ov', 'fx')
    d = Director(tl)
    E, K, P, R = tl.expr, tl.key, tl.pose, tl.reach

    # ---------------------------------------------------------------- initial state
    K(A, 0, 0, prop_r='popcorn', ra1=10, ra2=72, rh='grip', eat=1.0, smile=0.75, lid_b=0.3, lid_t=0.2)
    E(A, 0, 'happy', 0)
    K(S, 0, 0, prop_l='soda', la1=8, la2=98)
    P(DB, 0, 'lap', 0)
    P(M, 0, 'lap', 0)
    E(M, 0, 'soft', 0)
    K(M, 0, 0, look_y=-0.15)
    K(DB, 0, 0, look_y=-0.1)
    K(G, 0, 0, x=-640.0)

    # ================================================================ SCENE 0 — intro
    d.music('lounge', 0.0, 33.0, gain=0.9, fade_in=0.0, fade_out=1.5)
    d.shot('title')
    tl.overlay('title', 0.0, 4.6, fade_out=0.7)
    d.drift(0.0, 6.0, z=0.98, cy=-360)
    d.t = 1.0
    t0, t1 = d.say(M, "There's a little theater... [0.35] inside my head.", vo=True, post=0.45)
    E(M, t0 + 0.4, 'warm', 0.6)
    K(M, t0 + 0.6, 0.5, look_x=0.55, head_turn=0.25)
    K(M, t1 - 0.2, 0.5, look_x=0.0, head_turn=0.0)

    d.shot('row')
    d.drift(d.t, d.t + 4.0, z=0.53)
    t0, t1 = d.say(M, "And tonight... [0.4] my emotions bought tickets.", vo=True, post=0.6)
    for n in (DB, B, S):
        tl.blink(n, t0 + 0.6 + 0.3 * len(n) % 1)

    # Doubt
    d.shot('doubt', dur=0.0)
    d.drift(d.t, d.t + 4.5, z=1.6, cy=-368)
    tl.overlay('tag', d.t + 0.2, d.t + 3.3, text='DOUBT', who=DB)
    t0, t1 = d.say(M, "Doubt came... [0.4] because Doubt always comes.", vo=True, post=0.6)
    R(DB, t0 + 0.2, -1, 'face', 0.4, dx=-6, dy=-18, hand='point')     # push glasses up
    K(DB, t0 + 0.6, 0.15, head_nod=-4)
    P(DB, t0 + 1.3, 'lap', 0.5)
    K(DB, t0 + 0.6, 0.2, head_nod=0)
    E(DB, t0 + 1.0, 'skeptical', 0.4)
    K(DB, t0 + 1.0, 0.4, look_x=0.05, look_y=0.05, head_tilt=-4)
    E(DB, t1 + 0.4, 'neutral', 0.6)
    K(DB, t1 + 0.4, 0.5, head_tilt=0)

    # Boredom
    d.shot('boredom')
    d.drift(d.t, d.t + 4.5, z=1.6, cy=-368)
    tl.overlay('tag', d.t + 0.2, d.t + 3.3, text='BOREDOM', who=B)
    t0, t1 = d.say(M, "Boredom came... [0.5] mostly to nap.", vo=True, post=0.8)
    # big slow yawn
    K(B, t0 + 0.4, 0.8, open=0.9, mw=0.75, lid_t=0.85, brow_y=0.5, head_tilt=-6, smile=-0.2)
    R(B, t0 + 0.5, 1, 'mouth', 0.6, dx=10, dy=10, hand='open')
    K(B, t0 + 2.0, 0.7, open=0.0, mw=1.0, lid_t=0.62, brow_y=-0.2, head_tilt=4, smile=-0.08)
    P(B, t0 + 2.2, 'lap', 0.6, la2=40, ra2=40)
    K(B, t0 + 2.4, 1.2, sink=26)
    tl.blink(B, t1 + 0.1, 0.6)

    # Anger
    d.shot('anger')
    d.drift(d.t, d.t + 5, z=1.62, cy=-372)
    tl.overlay('tag', d.t + 0.2, d.t + 3.4, text='ANGER', who=A)
    t0, t1 = d.say(M, "And Anger? [0.6] Anger brought popcorn.", vo=True, post=0.5)
    K(A, t0 + 0.9, 0.3, eat=0.0)
    E(A, t0 + 1.0, 'grin', 0.3)
    R(A, t0 + 1.05, -1, 'chest', 0.35, dx=-70, dy=-30, hand='thumb')
    K(A, t0 + 1.1, 0.3, look_x=0.0, look_y=0.0, head_tilt=-5)
    tl.blink(A, t0 + 1.6, 0.18)
    K(A, t1 + 0.1, 0.3, eat=1.0, head_tilt=0)
    E(A, t1 + 0.1, 'happy', 0.4)

    d.shot('two_ma')
    d.drift(d.t, d.t + 8, z=1.02, cy=-320)
    t0, t1 = d.say(M, "Anger is my protector. [0.5] When something is truly wrong... [0.4] "
                      "he's the first one on his feet.", vo=True, post=0.6)
    K(A, t0 + 0.3, 0.3, eat=0.0)
    E(A, t0 + 0.5, 'proud', 0.5)
    K(A, t0 + 0.5, 0.6, lean=-3, head_tilt=-6, bob=-6)
    R(A, t0 + 0.6, -1, 'chest', 0.4, dx=-20, dy=10, hand='fist')
    tl.nod(A, t0 + 1.6, 2, 6)
    E(M, t0 + 0.8, 'warm', 0.6)
    K(M, t0 + 0.8, 0.5, look_x=0.85, head_turn=0.35)
    t0, t1 = d.say(M, "But tonight? [0.6] He was off duty.", vo=True, post=0.8)
    K(A, t0 + 0.4, 0.8, lean=-6, sink=12, bob=0, head_tilt=4)
    E(A, t0 + 0.6, 'happy', 0.7, lid_t=0.42, lid_b=0.3)
    K(A, t0 + 1.2, 0.4, eat=1.0)
    K(M, t0 + 1.0, 0.6, look_x=0.0, head_turn=0.0, look_y=-0.15)
    E(M, t1, 'soft', 0.5)

    # ================================================================ SCENE 1 — the first joke
    d.shot('stage_wide')
    T = d.t
    d.sfx('servo', T + 0.1, 0.5)
    K(G, T, 1.8, 'out', x=0.0)
    for i in range(5):
        K(G, T + i * 0.36, 0.18, hop=14)
        K(G, T + i * 0.36 + 0.18, 0.18, hop=0)
    K(G, T, 0, face='star', ra1=20, ra2=100)
    d.sfx('feedback', T + 2.0, 0.35)
    K(G, T + 2.0, 0.1, screen_flash=1.0)
    K(G, T + 2.1, 0.4, screen_flash=0.0)
    d.t = T + 2.0
    d.drift(T, T + 8, z=0.86, cy=-400)
    t0, t1 = d.say(G, "Ladies and gentlemen! [0.5] Prepare to have your minds... [0.7] BLOWN!",
                   fx=('robot',), post=0.3)
    K(G, t0, 0.4, face='normal', smile=0.8, la1=40, la2=10)
    K(G, t1 - 0.7, 0.25, 'back', la1=150, la2=-10, face='star', hop=10)
    K(G, t1 - 0.3, 0.2, hop=0)
    K(G, t1 + 0.1, 0.12, screen_flash=1.0)
    K(G, t1 + 0.25, 0.5, screen_flash=0.0)
    d.sfx('claps_few', t1 + 0.2, 0.5)
    d.t = t1 + 1.2

    d.shot('anger')
    d.drift(d.t, d.t + 4, z=1.6)
    E(A, d.t, 'smug', 0.3)
    t0, t1 = d.say(A, "Alright, robot. [0.4] Let's see what you got.", post=0.4, bob=1.3)
    K(A, t0, 0.3, eat=0.0, look_x=0.0, look_y=-0.05)
    K(A, t1 - 0.2, 0.4, eat=1.0)
    E(A, t1, 'happy', 0.4)
    K(G, d.t, 0.4, la1=10, la2=30, face='normal')

    d.shot('stage_med')
    d.drift(d.t, d.t + 10, z=1.42, cy=-345)
    t0, t1 = d.say(G, "So. [0.7] Why did the perfectionist... [0.3] refuse to fall into a black hole?",
                   fx=('robot',), post=1.1)
    K(G, t0 + 1.0, 0.6, lean=-8, face='smug', la1=55, la2=60, lh='point')
    K(G, t1, 0.4, lean=0, face='expect', la1=10, la2=30, lh='open')
    t0, t1 = d.say(G, "Because it would collapse... [0.6] all their expectations!", fx=('robot',), post=0.2)
    K(G, t0, 0.3, face='normal', look_x=0.0)
    K(G, t1 - 0.6, 0.3, face='happy', la1=25, la2=145)   # press the rimshot button
    d.sfx('rimshot', t1 + 0.05, 0.75)
    K(G, t1 + 0.45, 0.3, la1=10, la2=30)
    d.t = t1 + 0.6
    d.sfx('crickets', d.t, 0.55, dur=4.2)
    K(G, d.t, 0, face='expect')

    # the silent row
    d.shot('row', z=0.56, cy=-300)
    T = d.t
    d.drift(T, T + 3.0, z=0.6)
    K(A, T, 0, eat=0.0)
    m = arm_anchor(A, 'mouth')
    a1, a2 = ik(A, -1, m[0] - 40, m[1] + 40)
    K(A, T - 0.3, 0.25, la1=a1, la2=a2, lh='fist', prop_l='kernel')
    E(A, T, 'neutral', 0.8)
    for n in (DB, B, M, S):
        tl.blink(n, T + 0.4 + 0.37 * (len(n) % 3))
    E(M, T + 0.2, 'stunned', 0.8, open=0.0, pupil=0.85)
    E(DB, T + 0.8, 'skeptical', 1.4)
    E(S, T + 0.5, 'confused', 1.0)
    d.t = T + 1.7

    d.shot('anger_cu', follow=A, fdy=34)
    T = d.t
    d.drift(T, T + 12, z=2.8, fdy=30)
    K(A, T, 0, saccade=0.0, chew=0.6)
    K(A, T + 0.2, 1.2, chew=0.0)
    d.burst(T + 0.5, 300 - 8, -248, n=1, spread=40, up=60, floor=0, seed=3, size=0.8)
    d.sfx('tick', T + 1.1, 0.4)
    K(A, T + 0.8, 0.6, look_x=-0.85, head_turn=-0.08)
    K(A, T + 1.6, 0.8, look_x=0.85, head_turn=0.08)
    K(A, T + 2.6, 0.4, look_x=0.0, head_turn=0.0)
    E(A, T + 0.8, 'suspicious', 1.4)
    d.t = T + 2.9
    t0, t1 = d.say(A, "Wait a minute...", fx=('whisper',), post=0.7, bob=0.4)
    K(A, t1, 1.0, sweat=0.45)
    t0, t1 = d.say(A, "Something's wrong here.", fx=('whisper',), post=0.6, bob=0.4)
    K(A, t0, 0.5, brow_y=-0.5, lid_t=0.5)
    t0, t1 = d.say(M, "That's the thing about Anger. [0.5] He doesn't explode right away. [0.6] "
                      "First... [0.5] he listens.", vo=True, post=0.6)
    K(A, t0 + 1.5, 0.5, look_x=-0.3, look_y=-0.1)
    K(A, t0 + 3.6, 0.6, look_x=0.0, look_y=-0.05, head_tilt=-7)
    E(A, t0 + 3.6, 'suspicious', 0.6, lid_t=0.5, brow_y=-0.55)

    # ================================================================ SCENE 2 — the spiral
    d.music('tension', d.t, d.t + 34, gain=0.55, fade_in=2.0, fade_out=0.05)
    d.shot('stage_med', cx=-20)
    d.drift(d.t, d.t + 9, z=1.5, cx=0)
    t0, t1 = d.say(G, "But seriously, folks. [0.5] Feelings are just... [0.5] gravitational waves... [0.6] of JOY!",
                   fx=('robot',), post=0.15)
    K(G, t0 + 0.2, 0.5, la1=60, la2=20, face='normal', lean=4)
    K(G, t1 - 0.6, 0.3, 'back', la1=120, la2=-20, face='star', lean=-3)
    t0, t1 = d.say(G, "Ha. [0.3] Ha. [0.3] Ha.", fx=('robot',), post=0.5, speed=0.9)
    K(G, t0, 0, text='HA HA HA')
    for i in range(3):
        K(G, t0 + i * 0.6, 0.12, bob=-8)
        K(G, t0 + i * 0.6 + 0.15, 0.2, bob=0)
    K(G, t1 + 0.3, 0, text='', face='expect')
    K(G, t1 + 0.3, 0.4, la1=10, la2=30)

    d.shot('anger_cu', follow=A, fdy=34)
    T = d.t
    d.drift(T, T + 6, z=2.7, fdy=32)
    E(A, T, 'worried', 0.35, pupil=0.75, lid_t=0.05)
    K(A, T, 0.5, sweat=0.75, head_tilt=0, saccade=0.4)
    d.t = T + 0.8
    t0, t1 = d.say(A, "No, no, no. [0.3] It's fine. [0.35] It's just warming up. [0.7] Right?",
                   fx=('whisper',), speed=1.0, post=0.3, bob=0.6)
    tl.headshake(A, t0, 3, 0.18, 0.22)
    K(A, t1 - 0.8, 0.4, look_x=-0.9, head_turn=-0.35)
    E(A, t1 - 0.8, 'uneasy', 0.4, brow_y=0.7, smile=0.2)

    d.shot('two_ma')
    T = d.t
    K(M, T, 0.4, look_x=0.85, head_turn=0.4)
    E(M, T + 0.3, 'awkward', 0.4)
    K(M, T + 0.4, 0.3, la1=25, la2=-40, ra1=25, ra2=-40)      # small shrug
    K(M, T + 0.4, 0.3, bob=-8)
    K(M, T + 1.1, 0.4, la1=4, la2=48, ra1=4, ra2=48, bob=0)
    K(M, T + 0.5, 0.4, head_tilt=8)
    E(A, T + 1.2, 'worried', 0.5, smile=-0.5)
    K(A, T + 1.3, 0.5, look_x=0.0, head_turn=0.0, look_y=-0.1)
    tl.blink(A, T + 1.25, 0.2)
    K(M, T + 1.6, 0.5, look_x=0.0, head_turn=0.0, head_tilt=0)
    E(M, T + 1.8, 'uneasy', 0.5)
    d.t = T + 2.4

    d.shot('db_two')
    d.drift(d.t, d.t + 9, z=1.08)
    P(DB, d.t - 0.3, 'cross', 0.01)
    E(B, d.t, 'deadpan', 0.1)
    t0, t1 = d.say(DB, "Oh, I knew this was going to be a train wreck.", post=0.7, bob=0.7)
    E(DB, t0, 'smug', 0.3, brow_l=0.8)
    K(DB, t0, 0.3, look_x=0.4, head_turn=0.15)
    K(DB, t1, 0.4, look_x=0.0, head_turn=0.0)
    tl.nod(DB, t1 - 0.4, 1, 6)
    # boredom slowly wakes up
    K(B, t1 - 0.4, 1.4, lid_t=0.05, brow_y=0.55, sink=8)
    K(B, d.t - 0.3, 0.6, lid_t=-0.08, pupil=0.85)
    K(DB, d.t - 0.2, 0.4, look_x=0.85, head_turn=0.3)
    E(DB, d.t - 0.2, 'confused', 0.4)
    tl.blink(B, d.t + 0.4, 0.15)
    tl.blink(B, d.t + 0.75, 0.15)
    K(DB, d.t + 1.2, 0.4, look_x=0.0, head_turn=0.0)
    d.t += 1.5
    d.shot('stage_med')
    d.drift(d.t, d.t + 9, z=1.5, cy=-360)
    K(G, d.t, 0, face='expect', la1=10, la2=30, lean=0)
    K(G, d.t + 0.2, 0.6, la1=40, la2=60, lean=-6)
    d.t += 0.9
    d.sfx('cough', d.t, 0.6)
    d.t += 0.8

    d.shot('anger_cu', z=2.6, follow=A, fdy=34)
    T = d.t
    d.drift(T, T + 7, z=3.0, fdy=28)
    E(A, T, 'terrified', 0.6)
    K(A, T, 0.6, sweat=1.0, pale=0.7, gloom=1.0, saccade=0.0, shake=0.25)
    K(A, T + 0.3, 0.4, tub_crush=1.0)
    d.sfx('crunch', T + 0.35, 0.8)
    d.burst(T + 0.35, 360, -230, n=7, spread=140, up=180, floor=0, seed=7)
    d.t = T + 1.0
    t0, t1 = d.say(A, "Oh no... [0.6] please, God... [0.7] no.", fx=('whisper',), post=0.3, bob=0.3)
    K(A, t0, 0.4, shake=0.45)

    # ================================================================ SCENE 3 — meltdown
    T = d.t
    d.shot('two_ma', z=0.8, cy=-330, cx=200)
    d.sfx('scratch', T, 0.8)
    d.sfx('whoosh', T + 0.05, 0.6)
    d.music('doom', T + 0.35, T + 21.0, gain=0.5, fade_in=0.05, fade_out=2.5)
    K(A, T, 0.28, 'back', stand=1.0, shake=0.0, pale=0.2, gloom=0.0, sink=0)
    K(A, T, 0, prop_r='', eat=0.0, prop_l='', lean=0)
    P(A, T, 'hands_up', 0.25, kind='back')
    E(A, T, 'panic', 0.2)
    d.burst(T + 0.05, 360, -260, n=26, spread=520, up=900, floor=0, seed=11, size=1.1)
    d.sfx('popcorn', T + 0.05, 0.6)
    E(M, T + 0.1, 'alarmed', 0.2)
    K(M, T + 0.1, 0.25, look_x=0.9, head_turn=0.4, lean=-4)
    for n in (DB, B, S):
        E(n, T + 0.2, 'alarmed', 0.3)
    d.t = T + 0.35
    t0, t1 = d.say(A, "NOPE! [0.15] NOPE! [0.35] We have to leave! [0.25] Right NOW!", fx=('shout',),
                   speed=1.0, post=0.15, bob=1.6)
    E(A, t0, 'shout', 0.2)
    K(A, t0, 0.5, y=float(AISLE), x=280.0)
    t0, t1 = d.say(A, "This is NOT a drill! [0.3] Get out of here, kid! [0.25] It's not SAFE!",
                   fx=('shout',), speed=1.04, post=0.2, bob=1.6)
    K(A, t0 + 1.0, 0.3, head_turn=-0.5, look_x=-0.9)
    R(A, t0 + 1.0, -1, 'chest', 0.3, dx=-170, dy=-10, hand='grip')
    K(A, t0 + 1.0, 0.3, x=200.0)
    K(M, t0 + 1.2, 0.2, la1=50, la2=0, bob=-6)   # yanked a little
    K(M, t0 + 1.6, 0.4, bob=0)
    P(A, t1 - 0.1, 'hands_up', 0.3)
    K(A, t1 - 0.1, 0.3, head_turn=0.0, look_x=0.0)
    P(M, t1, 'lap', 0.5)

    # running in circles with arms up while narration plays
    d.shot('row', z=0.62, cx=150, cy=-260)
    T = d.t
    d.drift(T, T + 12, z=0.66)
    xs = [520, 60, 520, 60, 420, 150, 480]
    for i, xx in enumerate(xs):
        K(A, T + i * 1.35, 1.25, x=float(xx), head_turn=0.5 if (xs[i] > (xs[i - 1] if i else 200)) else -0.5)
    K(A, T, 0, sweat=1.0, steam=0.0)
    for i in range(10):
        K(A, T + i * 0.8, 0.35, la1=165, ra1=140, la2=-25, ra2=-5)
        K(A, T + i * 0.8 + 0.4, 0.35, la1=140, ra1=165, la2=-5, ra2=-25)
    for n in (M, DB, B, S):
        K(n, T, 0.3, saccade=0.2)
    # their heads follow him
    for i, xx in enumerate(xs):
        for n in (M, DB, B, S):
            rel = (xx - ROW_X[n]) / 500.0
            K(n, T + i * 1.35 + 0.2, 0.6, look_x=max(-1, min(1, rel)), head_turn=max(-0.4, min(0.4, rel * 0.4)),
              look_y=0.2)
    E(DB, T + 1.0, 'skeptical', 0.6)
    E(B, T + 1.0, 'stunned', 0.6, lid_t=0.0)
    E(S, T + 1.0, 'confused', 0.6)
    E(M, T + 1.0, 'stunned', 0.6)
    t0, t1 = d.say(M, "Anger was built for danger. [0.6] Fires. [0.45] Bullies. "
                      "[0.45] Betrayal. [0.8] He was not built... [0.6] for this.", vo=True, post=0.4)
    E(M, t1 - 2.0, 'hold_laugh', 0.6)

    # pacing and muttering in front of the stranger
    d.shot('row', cx=560, cy=-300, z=1.0)
    T = d.t
    d.drift(T, T + 12, z=1.08, cy=-310)
    K(A, T, 0, x=420.0)
    P(A, T, 'rest', 0.3)
    R(A, T, 1, 'head_side', 0.35, dx=-30, dy=0, hand='open')
    E(A, T, 'angry', 0.4, open=0.0)
    K(A, T, 0.4, vein=1.0, steam=0.8, sweat=0.8)
    pace = [760, 440, 760, 470, 700]
    for i, xx in enumerate(pace):
        K(A, T + 0.2 + i * 2.1, 1.8, x=float(xx), head_turn=0.35 if i % 2 == 0 else -0.35)
    K(S, T, 0.4, saccade=0.3)
    for i, xx in enumerate(pace):
        rel = (xx - 600) / 200.0
        K(S, T + 0.3 + i * 2.1, 1.6, look_x=max(-1, min(1, rel)), look_y=0.25,
          head_turn=max(-0.3, min(0.3, rel * 0.3)))
    E(S, T, 'uneasy', 0.5)
    t0, t1 = d.say(A, "They're not even jokes. [0.5] They're emotional landmines. [0.6] "
                      "Who let this thing on stage? [0.6] Heads will roll for this...",
                   speed=0.98, post=0.4, bob=1.2)
    R(A, t0 + 2.3, -1, 'chest', 0.3, dx=-90, dy=-60, hand='fist')
    R(A, t0 + 4.4, -1, 'chest', 0.3, dx=-60, dy=40, hand='point')
    P(A, t1 - 0.3, 'fists', 0.4)
    E(A, t1 - 0.6, 'furious', 0.4)

    d.shot('mb_two')
    T = d.t
    d.drift(T, T + 6, z=1.12)
    K(B, T, 0.6, lean=7, head_turn=0.4, look_x=0.9, head_tilt=6)
    E(B, T, 'deadpan', 0.5, lid_t=0.4)
    K(M, T, 0.3, look_x=-0.3, look_y=0.1)
    d.t = T + 0.5
    t0, t1 = d.say(B, "He's having the time of his life. [0.6] And he doesn't even know it.", post=0.5, bob=0.4)
    K(M, t0 + 0.5, 0.4, look_x=-0.8, head_turn=-0.35)
    E(M, t0 + 1.0, 'hold_laugh', 0.6)
    tl.pulse(M, t1 - 0.2, 'laugh', 0.5, 0.1, 0.5, 0.3)
    K(B, t1 + 0.2, 0.6, lean=0, head_turn=0, look_x=0, head_tilt=0)

    # ================================================================ SCENE 4 — the stranger
    d.shot('row', cx=540, cy=-330, z=1.15)
    T = d.t
    d.drift(T, T + 16, z=1.25, cy=-345)
    K(A, T, 0, x=400.0, y=float(AISLE), head_turn=-0.3, lean=0)
    K(A, T, 0.6, x=420.0)
    E(A, T, 'angry', 0.3, open=0.0)
    K(S, T, 0.4, look_x=-0.95, head_turn=0.0, saccade=0.0)
    E(S, T, 'skeptical', 0.4)
    R(S, T, -1, 'mouth', 0.5, dx=-6, dy=26)
    d.sfx('slurp', T + 0.5, 0.6, dur=1.3)
    K(S, T + 0.6, 0.0, lid_t=0.4)
    K(S, T + 1.9, 0.5, la1=8, la2=98)
    d.t = T + 2.2
    t0, t1 = d.say(S, "Dude. [0.6] What is your problem?", fx=('whisper',), post=0.15, bob=0.6)
    K(S, t0, 0.4, lean=-5, head_turn=-0.3)
    E(S, t0, 'confused', 0.4)
    # Anger whirls around
    T = d.t
    K(A, T, 0.15, 'snap', head_turn=0.45, look_x=0.9, x=425.0)
    E(A, T, 'furious', 0.15)
    d.sfx('whip', T, 0.35)
    d.t = T + 0.25
    t0, t1 = d.say(A, "MY problem?! [0.45] Do you not HEAR what is happening up there?!", fx=('shout',),
                   speed=0.98, post=0.6, bob=1.5)
    E(A, t0, 'shout', 0.15, brow_tilt=-0.8)
    R(A, t0 + 1.2, -1, 'head_top', 0.3, dx=-120, dy=-60, hand='point')
    K(S, t0, 0.3, lean=6, head_turn=0.0, look_x=-0.9)
    E(S, t0, 'alarmed', 0.3)
    tl.blink(S, t1 + 0.1, 0.2)
    E(S, t1 + 0.2, 'deadpan', 0.6, lid_t=0.45)
    P(A, t1, 'fists', 0.4)
    t0, t1 = d.say(S, "...It's a robot. [0.6] Telling bad jokes.", speed=0.9, post=0.5, bob=0.3)
    tl.blink(S, t0 + 1.0, 0.35)
    # Anger leans in close
    d.shot('row', cx=515, cy=-370, z=1.75)
    T = d.t
    d.drift(T, T + 7, z=1.9, cy=-378)
    K(A, T, 0.6, x=440.0, lean=7, head_turn=0.55, look_x=1.0, s=1.04)
    E(A, T, 'angry', 0.4, lid_t=0.38, open=0.0)
    K(A, T, 0.5, sweat=0.9, vein=1.0, twitch=0.0)
    K(S, T, 0.5, lean=9, head_turn=-0.15)
    d.t = T + 0.6
    t0, t1 = d.say(A, "Those aren't jokes. [0.6] Every word... [0.5] is a direct assault... [0.5] on my dignity.",
                   fx=('whisper',), speed=0.9, post=0.5, bob=0.5)
    K(A, t0 + 2.0, 0.3, twitch=1.0)
    K(A, t1, 0.3, twitch=0.0)
    E(S, t0 + 1.0, 'uneasy', 0.5)
    K(S, t0 + 1.4, 0.5, look_x=-0.3, look_y=0.25)
    K(S, t0 + 2.6, 0.4, look_x=-0.9, look_y=0.0)
    K(A, d.t - 0.2, 0.5, lean=0, s=1.0)
    E(S, d.t - 0.2, 'deadpan', 0.6)
    K(S, d.t, 0.8, lean=0, look_x=-0.6)
    d.t += 0.4

    # ================================================================ SCENE 5 — shoulders
    T = d.t
    d.music('pad', T, T + 30, gain=0.5, fade_in=2.5, fade_out=1.5)
    d.shot('two_ma', cx=200, cy=-330, z=0.95)
    K(M, T, 0.5, stand=1.0, look_x=0.6, head_turn=0.3)
    K(M, T + 0.4, 0.7, x=120.0, y=float(AISLE))
    E(M, T, 'determined', 0.5)
    K(A, T, 0.8, x=320.0, head_turn=0.0, lean=0)
    P(A, T, 'rest', 0.6, la1=16, la2=108, ra1=16, ra2=108, lh='open', rh='open')
    E(A, T + 0.6, 'panic', 0.4)
    K(A, T + 0.6, 0.4, breath=2.6, saccade=1.8, shake=0.25)
    d.t = T + 1.4
    d.shot('two_ma', cx=220, cy=-420, z=1.6)
    T = d.t
    d.drift(T, T + 15, z=1.85, cy=-430)
    R(M, T - 0.2, 1, 'chest', 0.4, dx=190, dy=-80, hand='grip')
    K(M, T - 0.2, 0.4, head_turn=0.55, look_x=0.9, lean=3)
    K(A, T - 0.2, 0.4, head_turn=-0.45)
    t0, t1 = d.say(M, "Anger. [0.7] Hey. [0.6] Look at me.", post=0.6)
    E(M, t0, 'tender', 0.5)
    K(A, t1 - 0.4, 0.4, saccade=0.0, look_x=-0.95)
    E(A, t1 - 0.4, 'scared', 0.4)
    K(A, t1, 0.8, breath=1.8, shake=0.1)
    tl.blink(A, t1 + 0.3, 0.2)
    t0, t1 = d.say(M, "It's just a comedy routine. [0.6] It can't hurt us.", post=0.5)
    tl.nod(M, t0 + 1.8, 1, 6)
    E(M, t0 + 0.5, 'soft', 0.5)
    t0, t1 = d.say(A, "Can't hurt us? [0.5] Have you HEARD it?", fx=('shout',), speed=0.92, post=0.6,
                   gain=0.85, bob=1.2)
    E(A, t0, 'panic', 0.3, open=0.2)
    K(A, t0, 0.3, look_x=-0.95)
    t0, t1 = d.say(M, "Just look. [0.5] One joke. [0.6] I'm right here.", post=0.4)
    R(M, t0 + 0.1, -1, 'head_top', 0.5, dx=-120, dy=-40, hand='point')
    E(M, t0 + 0.1, 'warm', 0.5)
    P(M, t0 + 2.3, 'rest', 0.6, ra1=60, ra2=50)
    R(M, t0 + 2.3, 1, 'chest', 0.5, dx=190, dy=-80, hand='grip')
    K(A, t0 + 0.8, 0.6, look_x=-0.2, look_y=-0.2, head_turn=-0.1)
    E(A, t0 + 0.8, 'worried', 0.5)
    K(A, t1 - 0.3, 0.4, look_x=-0.95, head_turn=-0.4)
    d.sfx('gulp', d.t + 0.2, 0.7)
    tl.pulse(A, d.t + 0.2, 'head_nod', 7, 0.12, 0.05, 0.2)
    d.t += 0.8
    t0, t1 = d.say(A, "...Fine. [0.6] But if this kills me... [0.6] I'm haunting you.", speed=0.9, post=0.6,
                   bob=0.6)
    E(A, t0, 'suspicious', 0.5, lid_t=0.45)
    K(A, t0, 0.5, breath=1.4, shake=0.0)
    E(M, t1 - 0.6, 'happy', 0.5)
    tl.nod(M, t1 - 0.3, 1, 5)
    K(A, t1 + 0.1, 0.8, look_x=0.0, head_turn=0.0, look_y=-0.15)
    E(A, t1 + 0.2, 'worried', 0.6)
    P(M, t1 + 0.2, 'rest', 0.6)
    K(M, t1 + 0.2, 0.6, head_turn=0.0, look_x=0.0, look_y=-0.15, lean=0)

    # ================================================================ SCENE 6 — the sniper
    d.shot('stage_med')
    d.drift(d.t, d.t + 7, z=1.45)
    t0, t1 = d.say(G, "Why did the emotion go to therapy? [0.9] It had unresolved... [0.5] quantum entanglement!",
                   fx=('robot',), post=0.1)
    K(G, t0, 0.4, face='normal', lean=-5)
    K(G, t1 - 0.5, 0.25, la1=70, la2=40, lh='point', face='wink', lean=4)
    d.sfx('rimshot', t1 + 0.1, 0.7)
    d.t = t1 + 0.5

    d.shot('two_ma', cx=275, cy=-410, z=1.35)
    T = d.t
    K(A, T, 0, saccade=0.0, look_x=0.0, look_y=-0.15)
    E(A, T, 'stunned', 0.2)
    K(A, T + 0.3, 0.2, twitch=1.0)
    K(M, T, 0.3, look_x=0.85, head_turn=0.35)
    E(M, T + 0.3, 'uneasy', 0.4)
    T = T + 1.3
    d.sfx('impact', T, 0.85)
    tl.pulse('cam', T, 'shake', 1.0, 0.02, 0.1, 0.4)
    K(A, T, 0.12, 'snap', lean=-10, x=360.0, twitch=0.0)
    R(A, T, -1, 'chest', 0.12, dx=-10, dy=0, hand='grip', kind='snap')
    R(A, T, 1, 'chest', 0.12, dx=20, dy=10, hand='grip', kind='snap')
    E(A, T, 'terrified', 0.1, open=0.5)
    K(A, T + 0.3, 0.6, lean=-5)
    d.t = T + 0.35
    t0, t1 = d.say(A, "AGH! [0.35] They got me! [0.35] THEY GOT ME!", fx=('shout',), speed=1.04, post=0.3, bob=1.5)
    K(A, t0, 1.2, x=385.0)
    E(M, t0 + 0.6, 'stunned', 0.3)
    E(M, t1 - 0.3, 'hold_laugh', 0.5)

    d.shot('row', cx=560, cy=-330, z=1.4)
    T = d.t
    E(S, T, 'shocked_o', 0.3)
    K(S, T, 0.3, look_x=-0.9, look_y=0.1, la1=35, la2=60)
    d.t = T + 1.0

    d.shot('stage_cu')
    d.drift(d.t, d.t + 6, z=2.4)
    t0, t1 = d.say(G, "And THAT is why emotional singularities... [0.5] are the black holes... [0.5] of laughter!",
                   fx=('robot',), post=0.1)
    K(G, t1 - 0.8, 0, text='HA HA HA')
    K(G, t1 + 0.4, 0, text='', face='happy')

    d.shot('row', cx=470, cy=-310, z=1.1)
    T = d.t + 0.15
    d.sfx('impact', T, 0.9)
    tl.pulse('cam', T, 'shake', 1.2, 0.02, 0.12, 0.5)
    K(A, T, 0.25, 'snap', kneel=1.0, stand=0.0, lean=6, x=420.0)
    R(A, T, -1, 'chest', 0.2, dx=-150, dy=-120, hand='splay')
    E(A, T, 'terrified', 0.15, open=0.6)
    d.t = T + 0.4
    t0, t1 = d.say(A, "I'm hit again! [0.3] OH GOD, [0.25] I'M HIT!", fx=('shout',), speed=1.04, post=0.3, bob=1.4)
    K(S, t0 + 0.6, 0.4, stand=0.55, lean=-4)
    E(S, t0 + 0.6, 'alarmed', 0.3)
    t0, t1 = d.say(S, "Okay, what the actual [BLEEP:0.65] is going on?! [0.5] Is this guy DYING?!", fx=('shout',), speed=1.04, post=0.5, bob=1.4)
    E(S, t0, 'panic', 0.3)
    K(S, t0, 0.3, la1=70, la2=-20, ra1=40, ra2=60, prop_l='', lh='splay', head_turn=-0.3)
    K(S, t0 + 1.0, 0, prop_r='soda')
    tl.headshake(S, t0 + 2.6, 3, 0.4, 0.35)

    # ================================================================ SCENE 7 — thousand-yard stare
    T = d.t
    d.music('taps', T + 0.3, T + 20, gain=0.55, fade_in=1.5, fade_out=1.5)
    d.sfx('tinnitus', T, 0.35, dur=13.0)
    K('cam', T, 1.2, desat=0.8, dark=0.55, muffle=1.0)
    d.shot('row', cx=440, cy=-330, z=1.9, follow=A, fdx=40, fdy=40)
    d.drift(T, T + 14, z=2.7, fdx=10, fdy=30)
    K(A, T, 0.8, saccade=0.0, autoblink=0.0, bags=1.0, shake=0.06, lean=2)
    E(A, T, 'stare', 1.2)
    P(A, T, 'rest', 1.0, la1=5, ra1=5, la2=10, ra2=10)
    d.t = T + 2.0
    t0, t1 = d.say(A, "The wave functions... [0.6] they're collapsing. [0.9] We've lost... [0.6] the front line...",
                   fx=('whisper',), speed=0.88, post=0.4, bob=0.2, brow=0.0)
    # stranger waves a hand in front of his face
    K(S, d.t - 2.5, 0.8, stand=1.0, x=600.0, lean=-6, prop_r='')
    tt = d.t - 1.5
    for i in range(4):
        K(S, tt + i * 0.4, 0.2, la1=85, la2=10, lh='open')
        K(S, tt + i * 0.4 + 0.2, 0.2, la1=70, la2=-10)
    t0, t1 = d.say(S, "Uh... [0.5] bro? [0.7] You okay?", speed=0.9, post=0.4, bob=0.4)
    E(S, t0, 'worried', 0.4)
    t0, t1 = d.say(G, "...emotional time dilation makes the punchline stretch... [0.5] infinitely!",
                   fx=('robot',), post=0.5, gain=0.85, cap=True)
    P(S, t1 - 0.5, 'rest', 0.5)
    # he tips over
    T = d.t
    K(A, T, 0.55, 'in', lean=-75)
    K(A, T + 0.55, 0, lying=1.0, lean=0, kneel=0.0, x=470.0, y=float(AISLE + 30), head_lift=0.0)
    d.sfx('thud', T + 0.55, 1.0)
    tl.pulse('cam', T + 0.55, 'shake', 1.6, 0.02, 0.1, 0.5)
    d.burst(T + 0.56, 360, AISLE + 20, n=6, spread=200, up=260, floor=AISLE + 40, seed=21, size=0.9)
    d.shot('row', T + 0.5, cx=430, cy=-150, z=1.2)
    K('cam', T + 0.5, 0.5, desat=0.0, dark=0.0, muffle=0.0)
    E(S, T + 0.55, 'shocked_o', 0.15)
    K(S, T + 0.6, 0.4, lean=0, look_x=-0.6, look_y=0.6)
    d.t = T + 2.6
    d.shot('row', cx=470, cy=-190, z=1.2)
    t0, t1 = d.say(S, "Did he just... [0.6] die? [0.9] From bad comedy?", fx=('whisper',), speed=0.9,
                   post=0.4, bob=0.4)
    E(S, t0, 'stunned', 0.5)
    K(S, t0 + 1.5, 0.6, look_x=-0.95, look_y=0.0, head_turn=-0.3)
    K(S, t1 - 0.5, 0.5, look_x=0.0, look_y=-0.05, head_turn=0.0)

    # ================================================================ SCENE 8 — laughing
    d.shot('me')
    T = d.t
    d.drift(T, T + 9, z=1.65, cy=-372)
    K(M, T, 0, x=150.0, y=float(AISLE), stand=1.0)
    E(M, T, 'hold_laugh', 0.2, open=0.0)
    K(M, T, 0.3, look_x=0.6, look_y=0.5, head_turn=0.3)
    tl.pulse(M, T + 0.5, 'blush', 0.6, 0.3, 0.6, 0.3)
    T = T + 1.2
    E(M, T, 'laugh', 0.3)
    K(M, T, 0.4, laugh=1.0, tears=1.0, hunch=0.6, look_y=0.0, head_turn=0.0)
    R(M, T, -1, 'belly', 0.4, dx=-30, dy=0, hand='fist')
    R(M, T, 1, 'belly', 0.4, dx=30, dy=0, hand='fist')
    d.t = T + 0.1
    t0, t1 = d.say(M, "Ha! [0.15] Ha ha ha! [0.2] Haha!", speed=1.05, post=0.0, gain=0.7, bob=1.6, cap=False)
    t0, t1 = d.say(M, "And me? [0.5] I was laughing so hard I couldn't breathe. [0.7] Not at the robot. [0.7] At him.",
                   vo=True, post=0.4, at=d.t - 0.3)
    d.t = t1 + 0.4
    d.shot('db_two')
    d.drift(d.t, d.t + 6, z=1.1)
    P(DB, d.t - 0.1, 'lap', 0.01)
    E(DB, d.t, 'sad', 0.5)
    E(B, d.t, 'deadpan', 0.5, lid_t=0.45)
    K(B, d.t, 0, look_x=0.6, look_y=0.4, saccade=0.0)
    t0, t1 = d.say(B, "If he's dead... [0.6] at least he died fighting for a noble cause.", post=0.4, bob=0.2)
    R(DB, t0 + 0.8, 1, 'chest', 0.5, dx=-10, dy=-10, hand='open')
    tl.nod(DB, t1 - 0.6, 2, 6, 0.45)
    K(M, d.t, 0, laugh=0.4, hunch=0.2)

    # ================================================================ SCENE 9 — the reveal
    d.shot('row', cx=430, cy=-60, z=1.6)
    T = d.t
    K(A, T, 0, lying=1.0, popcorn_stuck=1.0, bags=0.0, iris_dim=0.0, pupil=1.0, autoblink=1.0)
    E(A, T, 'determined', 0.0, lid_t=0.48)
    K(A, T + 0.9, 0.08, head_lift=0.2)
    K(A, T + 1.0, 0.08, head_lift=0.0)
    d.music('heroic', T + 1.4, T + 16, gain=0.6, fade_in=1.0, fade_out=2.0)
    K(A, T + 1.4, 1.0, head_lift=1.0)
    K(A, T + 1.4, 0, look_x=-0.6, look_y=-0.3, saccade=0.0)
    d.t = T + 2.6
    d.shot('row', d.t - 1.2, 1.2, follow=A, fdx=40, fdy=60, z=2.0)
    d.drift(d.t, d.t + 7, z=2.25, fdy=50)
    t0, t1 = d.say(A, "You see now? [0.9] I'm like Doubt... [0.7] but for comedy.", speed=0.88, post=0.5, bob=0.5)
    K(A, t0 + 1.4, 0.5, look_x=-0.4, lid_t=0.4)
    tl.blink(A, t0 + 1.2, 0.3)

    d.shot('doubt')
    T = d.t
    d.drift(T, T + 6, z=1.62)
    E(DB, T, 'grin', 0.2, brow_y=0.9)
    K(DB, T, 0, look_x=0.9, head_turn=0.35)
    R(DB, T + 0.1, 1, 'chest', 0.3, dx=60, dy=-70, hand='thumb')
    tl.nod(DB, T + 0.1, 6, 11, 0.24)
    d.t = T + 0.9
    t0, t1 = d.say(DB, "Oh, yeah. [0.4] He's the boss of comedy. [0.4] It's all him.",
                   speed=1.0, post=0.5, bob=1.4, brow=1.6)
    tl.nod(DB, t1 - 0.6, 3, 8, 0.22)

    d.shot('row', cx=400, cy=-330, z=1.3)
    T = d.t
    K(A, T, 0, lying=0.0, kneel=1.0, stand=0.0, x=420.0, y=float(AISLE), popcorn_stuck=0.8, lean=0)
    E(A, T, 'proud', 0.0, lid_t=0.4)
    R(A, T, -1, 'chest', 0.3, dx=-40, dy=-20, hand='open')
    K(A, T + 0.3, 0.3, la1=10, la2=80)
    K(A, T + 0.3, 0.6, popcorn_stuck=0.35)
    d.burst(T + 0.4, 420, -170, n=4, spread=120, up=100, floor=AISLE + 10, seed=31, size=0.8)
    d.t = T + 0.8
    K(A, d.t, 0.8, stand=1.0, kneel=0.0)
    K(A, d.t, 0.5, look_x=-0.6, head_turn=-0.3)
    E(A, d.t + 0.4, 'determined', 0.4)
    d.t += 1.1
    d.shot('row', cx=380, cy=-380, z=1.6)
    t0, t1 = d.say(A, "If I didn't exist... [0.6] you'd be laughing at THAT.", speed=0.9, post=0.9)
    R(A, t0 + 1.0, 1, 'head_top', 0.4, dx=110, dy=-60, hand='point')
    K(A, t0 + 1.0, 0.4, look_x=0.1, look_y=-0.3, head_turn=0.1)
    E(A, t0 + 1.0, 'angry', 0.4, open=0.0)
    P(A, t1 + 0.3, 'rest', 0.6)
    K(A, t1 + 0.3, 0.6, look_x=-0.7, look_y=0.0, head_turn=-0.3)
    E(A, t1 + 0.4, 'soft', 0.6)
    t0, t1 = d.say(A, "And that... [0.6] would be the real crime.", speed=0.88, post=0.4)

    d.shot('me')
    T = d.t
    d.drift(T, T + 8, z=1.6)
    K(M, T, 0, laugh=0.6, hunch=0.0, tears=0.8)
    E(M, T, 'laugh', 0.0)
    R(M, T + 0.2, 1, 'face', 0.4, dx=34, dy=-6, hand='open')
    K(M, T + 1.0, 0.5, laugh=0.0, tears=0.4)
    P(M, T + 1.3, 'rest', 0.5)
    E(M, T + 1.0, 'grin', 0.5)
    K(M, T + 1.0, 0.4, look_x=0.7, head_turn=0.3)
    d.t = T + 1.0
    t0, t1 = d.say(M, "Okay, okay. [0.4] I didn't know it was that serious.", post=0.5)
    E(M, t0 + 2.0, 'warm', 0.5)
    d.shot('anger')
    K(A, d.t, 0, x=300.0, y=float(AISLE), stand=1.0, popcorn_stuck=0.35)
    P(A, d.t, 'cross', 0.5)
    E(A, d.t, 'smug', 0.5)
    K(A, d.t, 0.5, look_x=-0.7, head_turn=-0.25, head_tilt=-5)
    d.t += 0.6
    t0, t1 = d.say(A, "Damn right, it's serious.", speed=0.9, post=0.9)
    tl.nod(A, t1 - 0.2, 1, 6)

    # ================================================================ SCENE 10 — the heart
    T = d.t
    d.music('warm', T, T + 46, gain=0.6, fade_in=2.0, fade_out=2.0)
    d.shot('two_ma', cy=-330, z=1.15)
    d.drift(T, T + 30, z=1.32, cy=-350)
    # back in their seats
    K(A, T, 0, x=300.0, y=0.0, stand=0.0, kneel=0.0, lying=0.0, popcorn_stuck=0.2, sweat=0.0, vein=0.0,
      steam=0.0, pale=0.0, lean=0.0, head_tilt=0.0, breath=1.0, shake=0.0, saccade=1.0, autoblink=1.0,
      tub_crush=0.0, iris_dim=0.0, bags=0.0)
    P(A, T, 'cross', 0)
    E(A, T, 'neutral', 0, smile=-0.05)
    K(A, T, 0, look_x=0.0, look_y=-0.1, head_turn=0.0)
    K(M, T, 0, x=0.0, y=0.0, stand=0.0, laugh=0.0, tears=0.0, hunch=0.0, head_turn=0.0)
    P(M, T, 'lap', 0)
    E(M, T, 'soft', 0)
    K(M, T, 0, look_x=0.0, look_y=-0.1)
    for n in (DB, B, S):
        E(n, T, 'neutral', 0)
        K(n, T, 0, look_x=0.0, look_y=-0.1, head_turn=0.0, lean=0.0, stand=0.0, saccade=1.0)
    K(S, T, 0, x=600.0, prop_l='soda', la1=8, la2=98, prop_r='', lh='open')
    d.t = T + 1.5
    K(M, d.t - 0.6, 0.6, look_x=0.85, head_turn=0.4)
    E(M, d.t - 0.6, 'tender', 0.6)
    t0, t1 = d.say(M, "Hey... [0.7] I'm sorry I laughed.", speed=0.88, post=1.0)
    K(A, t0 + 0.5, 0.6, look_x=0.6, head_turn=0.25)
    E(A, t0 + 0.6, 'sad', 0.6, smile=-0.1)
    tl.blink(A, t1 + 0.2, 0.25)
    t0, t1 = d.say(A, "...Don't be. [0.7] You're supposed to laugh. [0.7] Just... [0.5] at the right things.",
                   speed=0.88, post=0.9, bob=0.6)
    K(A, t0 + 1.5, 0.7, look_x=-0.8, head_turn=-0.35)
    E(A, t0 + 1.5, 'soft', 0.7)
    E(M, t1 - 0.5, 'smug', 0.6, smile=0.7)
    t0, t1 = d.say(M, "Like you... [0.5] face down... [0.5] in popcorn?", speed=0.9, post=0.8)
    E(A, t0 + 1.2, 'suspicious', 0.8, smile=-0.1)
    K(A, t1 - 0.2, 0, saccade=0.0)
    E(A, t1 + 0.5, 'proud', 1.4, smile=0.6, lid_t=0.35)
    K(A, t1 + 0.6, 1.0, blush=0.6)
    tl.pulse(A, t1 + 1.4, 'head_nod', 5, 0.12, 0.05, 0.25)
    d.t = t1 + 1.6
    t0, t1 = d.say(A, "...Yeah. [0.7] That one... [0.6] I'll allow.", speed=0.88, post=0.5, bob=0.6)
    K(A, t1, 0.5, saccade=1.0)
    E(A, t1, 'happy', 0.4)
    E(M, t1, 'laugh', 0.4)
    K(M, t1, 0.4, laugh=0.6)
    K(A, t1, 0.4, laugh=0.5)
    K(A, t1 + 0.2, 0.3, lean=-8, x=270.0)
    K(A, t1 + 0.6, 0.4, lean=0, x=300.0)
    K(M, t1 + 0.35, 0.2, lean=-5)
    K(M, t1 + 0.7, 0.4, lean=0)
    K(M, t1 + 1.8, 0.5, laugh=0.0)
    K(A, t1 + 1.8, 0.5, laugh=0.0)
    E(M, t1 + 1.8, 'warm', 0.5)
    E(A, t1 + 1.8, 'soft', 0.5)
    d.t = t1 + 2.2
    d.shot('row', z=0.55, cy=-280)
    d.drift(d.t, d.t + 14, z=0.5, cy=-260)
    for n in (DB, B, S):
        E(n, d.t + 0.5, 'soft', 1.0)
    E(B, d.t + 0.5, 'soft', 1.0, lid_t=0.4)
    t0, t1 = d.say(M, "Anger doesn't hate laughter. [0.7] He guards it. [1.0] Because the things we laugh at... "
                      "[0.6] are the things we let close.", vo=True, speed=0.88, post=1.0)
    K(M, t0 + 3.0, 0.8, look_x=0.0, head_turn=0.0, look_y=-0.1)
    K(A, t0 + 3.0, 0.8, look_x=0.0, head_turn=0.0, look_y=-0.1)
    E(A, t0 + 3.0, 'warm', 0.8)

    # ================================================================ SCENE 11 — the button
    d.shot('stage_wide')
    T = d.t
    d.drift(T, T + 6, z=0.9, cy=-420)
    K(G, T, 0, face='happy', la1=10, la2=30)
    t0, t1 = d.say(G, "Thank you! [0.4] You've been a wonderful audience! [0.6] I'll be here all week!",
                   fx=('robot',), post=0.4)
    for i in range(4):
        K(G, t0 + 1.0 + i * 0.4, 0.2, la1=150, la2=20)
        K(G, t0 + 1.2 + i * 0.4, 0.2, la1=130, la2=-20)
    K(G, t1 - 0.8, 0, face='star')
    d.sfx('rimshot', t1 - 0.1, 0.6)

    d.shot('anger_cu', z=2.4, follow=A, fdy=36)
    T = d.t
    d.drift(T, T + 5, z=2.8, fdy=30)
    K(A, T, 0, saccade=0.0)
    E(A, T, 'stunned', 0.3, smile=0.3)
    K(A, T + 0.4, 0.2, twitch=1.0)
    K(A, T + 1.5, 0.2, twitch=0.0)
    d.t = T + 1.4
    t0, t1 = d.say(A, "All week?", fx=('whisper',), speed=0.85, post=0.5, gain=1.6)
    E(A, t0, 'terrified', 0.5, smile=-0.4)
    d.shot('row', z=0.6, cx=150, cy=-290)
    T = d.t
    for n in (M, DB, B, S):
        rel = (300 - ROW_X[n]) / 400.0
        K(n, T - 0.2, 0.5, look_x=max(-1, min(1, rel)), head_turn=max(-0.45, min(0.45, rel * 0.4)), saccade=0.0)
    t0, t1 = d.say(A, "ALL WEEK?!", fx=('shout',), speed=0.9, post=0.2, bob=2.0)
    K(A, t0, 0.2, 'back', stand=1.0)
    P(A, t0, 'hands_up', 0.2)
    E(A, t0, 'shout', 0.1, open=0.6)
    d.burst(t0 + 0.05, 300, -300, n=10, spread=380, up=700, floor=0, seed=41, size=1.0)
    T = t1 + 0.2
    for n, lv in ((M, 1.0), (DB, 0.8), (S, 0.6)):
        E(n, T + 0.1 * len(n) % 0.5, 'laugh', 0.3)
        K(n, T, 0.3, laugh=lv)
    E(B, T + 0.3, 'smug', 0.5)
    tl.headshake(S, T + 0.4, 4, 0.3, 0.32)
    d.t = T
    t0, t1 = d.say(M, "Ha ha ha ha!", speed=1.05, post=0.0, gain=0.55, cap=False)
    t0b, t1b = d.say(DB, "Ha ha ha!", speed=1.05, post=0.0, gain=0.45, cap=False, at=t0 + 0.2)
    d.t = max(t1, t1b) + 0.3
    E(A, d.t - 0.6, 'grimace', 0.4)
    P(A, d.t - 0.4, 'rest', 0.5)
    K(A, d.t - 0.4, 0.8, stand=0.0, sink=30, lean=4)
    tl.overlay('end', d.t + 0.3, d.t + 4.0)
    d.music('outro', T - 0.2, d.t + 4.2, gain=0.85, fade_in=0.2, fade_out=1.0)
    d.t += 4.2
    tl.end = d.t
    tl.finalize()
    return tl


if __name__ == '__main__':
    tl = build()
    print('duration %.1fs  lines %d' % (tl.end, len(tl.lines)))
    for ln in tl.lines:
        print('%6.1f %6.1f %-9s %s' % (ln['t0'], ln['t1'], ln['speaker'], ln['caption'][:70]))
