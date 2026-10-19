"""The Ones Who Watch: script + acting direction."""

# ---- world layout (wide shot == world coords, 1080x1920) ----
POS = {
    'IRIS': (560, 1080),
    'CLAWD': (255, 430),
    'CLAWDIA': (830, 330),
    'GOSTE': (235, 1335),
    'BEE': (1250, 820),
    'WINDOW': (930, 965),
    'MOON': (560, 255),
}

SHOTS = {
    'wide': (540, 960, 1.0),
    'wide_hi': (540, 900, 1.08),
    'sky': (540, 420, 1.45),
    'clawd': (265, 470, 2.1),
    'clawdia': (815, 375, 2.25),
    'iris': (560, 1110, 1.65),
    'iris_cu': (560, 1085, 2.5),
    'iris_ecu': (560, 1080, 3.6),
    'goste': (250, 1330, 2.35),
    'goste_cu': (240, 1300, 3.1),
    'pump': (230, 1450, 2.2),
    'iris_goste': (410, 1220, 1.38),
    'garden': (500, 1150, 1.15),
    'window': (930, 960, 2.6),
    'window_wide': (760, 1080, 1.35),
    'bee_goste': (190, 1260, 2.0),
}

EXPR = {
    'neutral':   dict(lid=.12, blid=0, brow=0, arch=.1, smile=.1, pupil=1.0, tiltb=0, mopen=0),
    'happy':     dict(lid=.05, blid=.38, brow=.25, arch=.2, smile=.75, pupil=1.15, tiltb=0, mopen=0),
    'sad':       dict(lid=.38, blid=0, brow=-.05, arch=.85, smile=-.55, pupil=1.25, tiltb=0, mopen=0),
    'worried':   dict(lid=0, blid=0, brow=.3, arch=.75, smile=-.35, pupil=.9, tiltb=0, mopen=0),
    'scared':    dict(lid=0, blid=0, brow=.65, arch=.6, smile=-.45, pupil=.6, tiltb=0, mopen=.05),
    'angry':     dict(lid=.32, blid=.1, brow=-.4, arch=-.85, smile=-.5, pupil=.85, tiltb=0, mopen=0),
    'grumpy':    dict(lid=.42, blid=0, brow=-.2, arch=-.5, smile=-.35, pupil=.95, tiltb=0, mopen=0),
    'surprised': dict(lid=0, blid=0, brow=.85, arch=.3, smile=0, pupil=.75, tiltb=0, mopen=.35),
    'skeptic':   dict(lid=.36, blid=.05, brow=.15, arch=-.1, smile=-.12, pupil=.95, tiltb=.7, mopen=0),
    'tender':    dict(lid=.22, blid=.2, brow=.1, arch=.5, smile=.35, pupil=1.25, tiltb=0, mopen=0),
    'amused':    dict(lid=.26, blid=.3, brow=.1, arch=0, smile=.5, pupil=1.05, tiltb=.45, mopen=0),
    'determined': dict(lid=.18, blid=.05, brow=-.25, arch=-.45, smile=.25, pupil=1.0, tiltb=0, mopen=0),
    'awe':       dict(lid=0, blid=0, brow=.6, arch=.4, smile=.2, pupil=1.4, tiltb=0, mopen=.18),
    'sleepy':    dict(lid=.7, blid=.1, brow=-.05, arch=.1, smile=0, pupil=1.0, tiltb=0, mopen=0),
    'hurt':      dict(lid=.25, blid=.05, brow=.2, arch=1.0, smile=-.65, pupil=1.3, tiltb=0, mopen=0),
    'soft_smile': dict(lid=.18, blid=.25, brow=.15, arch=.35, smile=.5, pupil=1.25, tiltb=0, mopen=0),
}


def ex(tl, ch, name, dt=0.0, dur=0.3, t=None, **over):
    p = dict(EXPR[name])
    p.update(over)
    tl.set(ch, dt=dt, dur=dur, t=t, **p)


def build(tl):
    S = tl.set
    # ---------------- defaults ----------------
    for ch in ('IRIS', 'BEE', 'CLAWD', 'CLAWDIA', 'GOSTE'):
        ex(tl, ch, 'neutral', dur=0)
    S('IRIS', dur=0, x=560, y=1080, lean=0, droop=.1, spread=0, leafL=0, leafR=0, look='auto')
    ex(tl, 'IRIS', 'sleepy', dur=0, lid=.92)
    S('CLAWD', dur=0, x=255, y=430, rain=0, dark=.25, look='auto')
    ex(tl, 'CLAWD', 'grumpy', dur=0)
    S('CLAWDIA', dur=0, x=830, y=330, rain=0, dark=0, look='auto')
    ex(tl, 'CLAWDIA', 'tender', dur=0)
    S('GOSTE', dur=0, x=235, y=1640, alpha=.82, oness=1, tremble=.6, armL=0, armR=0,
      wave=0, tear=0, blush=0, look='auto')
    ex(tl, 'GOSTE', 'scared', dur=0)
    S('BEE', dur=0, x=1300, y=760, face=-1, look='auto', antenna=.5)
    S('WORLD', dur=0, dawn=0, window=.85, child=0, childwave=0, title=0, endtitle=0, fogamt=1, mooneye=0)
    S('PHOTO', dur=0, alpha=1, cx=751, cy=1000, zoom=1.0, flook=(0, 0), flid=0,
      ghostsmile=0, wink=0, ghostlook=(0, 0))
    tl.cam('wide', dur=0)
    tl.scene('photo')
    tl.mood('mystery')

    # ================= OPENING: the real drawing =================
    # first frame = the drawing itself; the flower's eye wakes up immediately
    S('PHOTO', t=0.15, dur=0.2, flid=.0)
    tl.sfx('creak', t=0.3)
    S('PHOTO', t=0.5, dur=0.25, flook=(-.8, -.1))
    S('PHOTO', t=1.15, dur=0.25, flook=(.8, -.2))
    S('PHOTO', t=1.0, dur=6.0, zoom=1.12, cx=745, cy=960)
    tl.wait(0.6)
    st, d = tl.line('N', "Somebody drew this... with one black marker, and a very big imagination.",
                    hi=['imagination'], gap=0.5)
    S('PHOTO', t=st + 1.8, dur=0.3, flook=(0, .1))
    S('PHOTO', t=st + d - 0.6, dur=0.25, flook=(0, 0))
    st, d = tl.line('N', "But on Halloween night... drawings like this one start to look back.",
                    lo=['look back'], gap=0.2)
    S('PHOTO', t=st + d - 1.2, dur=0.35, flook=(0, 0), flid=0)
    tl.sting('lo', t=st + d - 0.9, strength=0.6)
    # push into the pupil
    S('PHOTO', t=st + d - 0.2, dur=1.7, zoom=34, cx=742, cy=1032)
    tl.sfx('whoosh', t=st + d - 0.1)
    tl.t = st + d + 1.5
    cut = tl.t
    S('PHOTO', t=cut, dur=0, alpha=0)
    tl.scene('garden', t=cut)
    tl.cam(('iris_pupil', 40), t=cut, dur=0)
    tl.cam('wide', t=cut + 0.05, dur=3.4)
    S('WORLD', t=cut + 0.8, dur=0.6, title=1)
    S('WORLD', t=cut + 4.6, dur=0.7, title=0)
    S('IRIS', t=cut, dur=0, lid=.0)
    ex(tl, 'IRIS', 'sleepy', t=cut + 1.2, dur=1.2, lid=.88)
    tl.sfx('owl', t=cut + 2.2)
    tl.wait(1.6)

    # ================= THE GARDEN =================
    st, d = tl.line('N', "Behind the last house on Hollow Lane, there is a garden where everyone has exactly one eye.",
                    gap=0.3)
    tl.cam('garden', t=st + 2.2, dur=d - 2.2)
    S('CLAWD', t=st + d - 1.6, look=(-.2, .7))
    S('CLAWDIA', t=st + d - 1.3, look=(.3, .6))
    st, d = tl.line('N', "They call themselves the Watchers. And tonight... something new has arrived.",
                    hi=['new'], gap=0.1)
    tl.cam('sky', t=st, dur=0)
    S('CLAWD', t=st + 0.3, dur=1.0, x=262)
    ex(tl, 'CLAWDIA', 'worried', t=st + d - 1.6, dur=0.5)
    S('CLAWDIA', t=st + d - 1.6, look=(-.4, 1))
    S('CLAWD', t=st + d - 1.4, look=(-.1, 1))

    # ---- Bee bursts in
    tl.mood('comic', dt=0.2)
    tl.cam('wide_hi', dt=0, dur=0)
    S('BEE', dt=0.0, dur=1.0, x=700, y=900, face=-1)
    ex(tl, 'BEE', 'scared', dt=0, dur=0.2, mopen=.2)
    S('BEE', dt=0, dur=0.2, antenna=1)
    tl.sfx('buzzin', dt=0)
    tl.wait(0.8)
    st, d = tl.line('BEE', "Iris! Iris! Wake up! There's a thing by the pumpkins, and it has TWO eyes! Two! Who needs TWO?!",
                    hi=['TWO eyes'], gap=0.25)
    tl.cam('iris', t=st + 0.2, dur=0.8)
    S('BEE', t=st + 0.0, dur=0.5, x=735, y=880, look='IRIS')
    S('BEE', t=st + 1.6, dur=0.45, x=690, y=930)
    S('BEE', t=st + 2.4, dur=0.5, x=760, y=860, look=(-1, .6))
    ex(tl, 'BEE', 'surprised', t=st + 3.0, dur=0.15)
    S('BEE', t=st + 3.4, dur=0.3, x=720, y=905, look='IRIS')
    ex(tl, 'BEE', 'angry', t=st + d - 1.3, dur=0.2, brow=.5, arch=.6, mopen=.2)
    S('IRIS', t=st + 0.6, dur=0.12, lid=.97)
    S('IRIS', t=st + 1.5, dur=1.4, lid=.55)
    S('IRIS', t=st + 1.8, look='BEE')
    st, d = tl.line('IRIS', "Bee. Breathe.", speed=1.15, gap=0.15)
    ex(tl, 'IRIS', 'sleepy', t=st, dur=0.6, lid=.5, smile=.05)
    S('IRIS', t=st, dur=0.8, droop=.18)
    S('BEE', t=st + 0.2, dur=0.4, y=920)
    st, d = tl.line('BEE', "Do bees even BREATHE?!", hi=['BREATHE'], pitch=1.04, gap=0.25)
    ex(tl, 'BEE', 'worried', t=st, dur=0.2, brow=.7, mopen=.1)
    S('BEE', t=st, dur=0.25, y=870, antenna=1)
    ex(tl, 'IRIS', 'amused', t=st + d * 0.7, dur=0.6, lid=.4)
    st, d = tl.line('IRIS', "You're doing it right now. ...Badly.", speed=1.08, gap=0.45)
    S('IRIS', t=st, dur=0.5, droop=.0, spread=.1)
    S('IRIS', t=st + d * 0.5, dur=0.2, look=(-.25, .2))
    S('IRIS', t=st + d - 0.3, dur=0.2, look='BEE')
    ex(tl, 'BEE', 'skeptic', t=st + d - 0.3, dur=0.3)
    S('BEE', t=st + d - 0.3, dur=0.4, antenna=.2)

    # ---- The clouds
    tl.cam('clawd', dt=-0.1, dur=0)
    ex(tl, 'CLAWD', 'grumpy', dt=0, dur=0.4, lid=.3)
    S('CLAWD', dt=0, look=(.2, .8))
    st, d = tl.line('CLAWD', "Two eyes. That means it can look at two things at once.", gap=0.15, speed=1.05)
    S('CLAWD', t=st + 1.4, dur=0.3, look=(-.7, .3))
    S('CLAWD', t=st + 2.2, dur=0.3, look=(.7, .3))
    S('CLAWD', t=st + 3.0, look='cam')
    st, d = tl.line('CLAWD', "Never trust something that can't make up its mind.", lo=['Never trust'], gap=0.3, speed=1.05)
    ex(tl, 'CLAWD', 'angry', t=st, dur=0.35, lid=.35)
    S('CLAWD', t=st, dur=0.6, dark=.45)
    tl.cam('clawdia', dt=-0.05, dur=0)
    ex(tl, 'CLAWDIA', 'amused', dt=0, dur=0.3, smile=.25)
    S('CLAWDIA', dt=0, look='CLAWD')
    st, d = tl.line('CLAWDIA', "Oh, hush, Clawd.", gap=0.1)
    S('CLAWDIA', t=st + d, dur=0.4, look=(-.5, 1))
    ex(tl, 'CLAWDIA', 'worried', t=st + d, dur=0.5, pupil=1.25)
    st, d = tl.line('CLAWDIA', "Look at it. It's shaking.", lo=['shaking'], gap=0.4, speed=1.1)
    tl.mood('mystery', t=st)

    # ================= GOSTE =================
    tl.cam('pump', dt=-0.2, dur=0)
    S('GOSTE', dt=0, dur=1.6, y=1500)
    S('GOSTE', dt=0.2, look=(.8, -.4))
    tl.sfx('shimmer', dt=0)
    S('GOSTE', dt=1.2, dur=0.3, look=(.4, -.9))
    tl.wait(1.5)
    S('GOSTE', dt=0, dur=1.4, y=1335)
    tl.cam('goste', dt=0, dur=1.4)
    tl.wait(0.4)
    st, d = tl.line('GOSTE', "Please... don't be scared of me.", speed=1.15, gap=0.35, whisper=True)
    S('GOSTE', t=st, look='cam')
    S('GOSTE', t=st + 0.5, dur=0.6, armL=.5, armR=.5)
    tl.cam('clawd', dt=-0.05, dur=0)
    ex(tl, 'CLAWD', 'skeptic', dt=0, dur=0.3)
    S('CLAWD', dt=0, look='GOSTE')
    st, d = tl.line('CLAWD', "Scared? Of you? You're the size of a pillowcase.", hi=['pillowcase'], gap=0.3)
    ex(tl, 'CLAWD', 'amused', t=st + d - 1.0, dur=0.3, smile=.2)
    tl.cam('goste_cu', dt=0, dur=0)
    S('GOSTE', dt=0, dur=0.5, armL=0, armR=0, look=(-.3, .7))
    ex(tl, 'GOSTE', 'hurt', dt=0, dur=0.5, pupil=1.2)
    st, d = tl.line('GOSTE', "I don't know how I got here.", speed=1.08, gap=0.25)
    S('GOSTE', t=st + d * 0.6, dur=0.6, look=(.6, -.5))
    st, d = tl.line('GOSTE', "I was somewhere warm... and then I wasn't.", lo=["wasn't"], speed=1.12, gap=0.5)
    ex(tl, 'GOSTE', 'awe', t=st, dur=0.8, mopen=0, smile=.1)
    ex(tl, 'GOSTE', 'sad', t=st + d * 0.55, dur=0.6)
    S('GOSTE', t=st + d * 0.55, dur=0.7, look=(0, .9))

    tl.mood('tender', dt=-0.2)
    tl.cam('goste', dt=-0.1, dur=3.5)
    st, d = tl.line('N', "The little ghost's mouth was stuck in a perfect O... as if a surprise had happened long ago, and never finished.",
                    lo=['never finished'], gap=0.4)
    S('GOSTE', t=st + 2, dur=0.6, look=(-.5, .6))
    S('GOSTE', t=st + d - 1.5, look=(.9, -.2))

    tl.cam('iris_goste', dt=-0.1, dur=0)
    S('IRIS', dt=-0.3, dur=1.6, lean=-1, leafL=.6)
    ex(tl, 'IRIS', 'tender', dt=-0.3, dur=0.8)
    S('IRIS', dt=-0.3, look='GOSTE')
    S('GOSTE', dt=0, look='IRIS')
    ex(tl, 'GOSTE', 'scared', dt=0, dur=0.3, pupil=1.0)
    st, d = tl.line('IRIS', "What's your name, little one?", speed=1.12, gap=0.5)
    ex(tl, 'GOSTE', 'worried', t=st + d, dur=0.6, pupil=1.25)
    S('GOSTE', t=st + d * 0.8, dur=0.6, tremble=.25)

    tl.cam('goste_cu', dt=-0.1, dur=4.5)
    S('GOSTE', dt=0, dur=0.5, look=(-.2, .9))
    st, d = tl.line('GOSTE', "I don't remember. Everything feels... blurry.", speed=1.12, gap=0.3)
    ex(tl, 'GOSTE', 'sad', t=st + 0.5, dur=0.6)
    S('GOSTE', t=st + d * 0.6, dur=0.4, look=(.3, -.3))
    st, d = tl.line('GOSTE', "Like I was drawn in pencil... and someone is erasing me.", lo=['erasing'], speed=1.15, gap=0.6)
    S('GOSTE', t=st + d * 0.45, dur=1.6, alpha=.42, tremble=.4)
    S('GOSTE', t=st + d * 0.45, look='cam')
    ex(tl, 'GOSTE', 'hurt', t=st + d * 0.45, dur=0.7, tear=.7)
    tl.sfx('erase', t=st + d * 0.5)

    tl.cam('clawdia', dt=-0.2, dur=0)
    ex(tl, 'CLAWDIA', 'hurt', dt=-0.2, dur=0.4, tear=1)
    S('CLAWDIA', dt=0, dur=1.5, rain=1, dark=.5)
    S('CLAWDIA', dt=0, look=(-.5, 1))
    st, d = tl.line('CLAWDIA', "Oh... that is the saddest thing I have ever heard.", lo=['saddest'], speed=1.12, gap=0.3)
    tl.cam('sky', dt=-0.1, dur=0)
    S('CLAWD', dt=-0.2, look='CLAWDIA')
    ex(tl, 'CLAWD', 'skeptic', dt=-0.2, dur=0.3, lid=.5)
    S('BEE', t=st, dur=0.1, x=1250, y=700)
    S('BEE', t=st + d - 0.8, dur=0.9, x=830, y=470, face=-1, look='CLAWDIA')
    ex(tl, 'BEE', 'neutral', t=st + d - 0.5, dur=0.3)
    st, d = tl.line('CLAWD', "You're raining on the bee.", gap=0.3)
    S('CLAWD', t=st + d * 0.4, look='BEE')
    tl.cam(('@BEE', 2.6, 0, 60), dt=-0.1, dur=0)
    ex(tl, 'BEE', 'grumpy', dt=-0.1, dur=0.3, lid=.55, smile=-.4)
    S('BEE', dt=-0.1, dur=0.4, antenna=0, look='cam')
    st, d = tl.line('BEE', "I'm fine. I'm totally fine. I'm just... moist.", hi=['moist'], gap=0.35, speed=1.05, pitch=.97)
    S('BEE', t=st + d * 0.65, dur=0.2, look=(.3, -.8))
    S('BEE', t=st + d - 0.4, look='cam')
    tl.sting('hi', t=st + d + 0.1, strength=0.5)
    S('CLAWDIA', t=st + d * 0.7, dur=1.0, rain=0.15, dark=.25)
    ex(tl, 'CLAWDIA', 'amused', t=st + d * 0.7, dur=0.4, tear=.3)
    S('BEE', t=st + d + 0.3, dur=1.4, x=600, y=750, face=-1, look='GOSTE')
    ex(tl, 'BEE', 'neutral', t=st + d + 0.4, dur=0.3)

    # ================= THE HEART OF IT =================
    tl.mood('sad', dt=0.4)
    tl.cam('iris_goste', dt=0.3, dur=0)
    S('GOSTE', dt=0.3, dur=1.0, alpha=.5, tremble=.15)
    ex(tl, 'GOSTE', 'worried', dt=0.3, dur=0.5, tear=.3)
    tl.wait(0.4)
    S('GOSTE', dt=0, look='IRIS')
    st, d = tl.line('GOSTE', "Why do you all have only one eye?", speed=1.1, gap=0.6)
    S('IRIS', t=st + d, look='WINDOW')
    tl.cam('window_wide', t=st + d, dur=3.0)
    ex(tl, 'IRIS', 'tender', t=st + d, dur=1.0, lid=.25)
    S('IRIS', t=st + d, dur=1.5, lean=0.3, leafL=0, leafR=.25)
    S('GOSTE', t=st + d + 0.6, look='WINDOW')
    st, d = tl.line('IRIS', "Two eyes are for looking around.", speed=1.12, gap=0.3)
    st, d = tl.line('IRIS', "One eye... is for keeping watch over something you love.", hi=['love'], speed=1.14, gap=0.5)
    tl.cam('window', t=st + d * 0.5, dur=2.5)
    S('WORLD', t=st + d * 0.5, dur=1.0, window=1)
    st, d = tl.line('IRIS', "A child lives in that window. Every night, until the light goes out, I watch...",
                    speed=1.12, gap=0.15)
    tl.cam('iris_cu', t=st + d - 0.2, dur=0)
    S('IRIS', t=st + d - 0.3, look='cam')
    st, d = tl.line('IRIS', "...so they never feel alone in the dark.", hi=['never feel alone'], lo=['dark'], speed=1.14, gap=0.7)
    ex(tl, 'IRIS', 'soft_smile', t=st, dur=0.8)
    S('IRIS', t=st + d * 0.6, look='GOSTE')

    tl.cam('goste_cu', dt=-0.1, dur=0)
    ex(tl, 'GOSTE', 'worried', dt=-0.1, dur=0.5, tear=.4)
    S('GOSTE', dt=0, look='IRIS')
    st, d = tl.line('GOSTE', "And the things that nobody watches...", lo=['nobody'], speed=1.18, gap=0.25)
    S('GOSTE', t=st + d * 0.5, dur=0.5, look=(-.2, .9))
    st, d = tl.line('GOSTE', "What happens to them?", speed=1.15, gap=1.3)
    S('GOSTE', t=st, look='IRIS')
    tl.cam('iris_ecu', t=st + d + 0.1, dur=1.3)
    # Iris doesn't want to answer
    S('IRIS', t=st + d + 0.2, dur=0.5, look=(-.6, .6))
    ex(tl, 'IRIS', 'sad', t=st + d + 0.2, dur=1.2, lid=.5)
    S('IRIS', t=st + d + 0.2, dur=2.0, droop=.8, leafR=0, lean=-.3)
    tl.sfx('heartbeat', t=st + d + 0.5)
    st, d = tl.line('IRIS', "...They fade.", lo=['fade'], speed=1.3, gap=1.2)
    S('IRIS', t=st + d * 0.5, dur=0.4, look='GOSTE')

    tl.cam('goste_cu', dt=-1.0, dur=0)
    S('GOSTE', dt=-1.0, dur=0.6, look=(0, 1), armL=.55, armR=.55)
    S('GOSTE', dt=-0.6, dur=1.6, alpha=.3)
    ex(tl, 'GOSTE', 'hurt', dt=-1.0, dur=0.8, tear=1, lid=.3)
    st, d = tl.line('GOSTE', "Then I'm already... almost gone.", lo=['almost gone'], speed=1.2, gap=1.2, whisper=True)
    S('GOSTE', t=st + d, dur=0.6, look='cam', armL=0, armR=0)
    tl.sfx('wind_gust', t=st + d)
    tl.cam('garden', t=st + d + 0.1, dur=1.2)

    # ================= THE TURN =================
    tl.mood('comic', dt=0.0)
    S('BEE', dt=-0.5, dur=0.55, x=105, y=1215, face=1, look='GOSTE')
    ex(tl, 'BEE', 'determined', dt=-0.4, dur=0.2)
    S('BEE', dt=-0.4, dur=0.2, antenna=1)
    tl.sfx('buzzin', dt=-0.4)
    tl.cam('bee_goste', dt=0.05, dur=0)
    st, d = tl.line('BEE', "Nope! No! Absolutely not! New rule: I watch you.", hi=['New rule'], gap=0.2, speed=1.0)
    ex(tl, 'GOSTE', 'surprised', t=st + 0.2, dur=0.2, mopen=0)
    S('GOSTE', t=st + 0.2, look='BEE')
    S('BEE', t=st + d * 0.5, dur=0.25, y=1195)
    S('BEE', t=st + d * 0.75, dur=0.25, y=1225)
    st, d = tl.line('BEE', "I've only got one eye, but it is a VERY good eye.", hi=['VERY good'], gap=0.3)
    ex(tl, 'BEE', 'happy', t=st + d * 0.5, dur=0.3)
    st, d = tl.line('BEE', "...It's mostly for flowers. But I'll make an exception.", gap=0.45, speed=1.05)
    ex(tl, 'BEE', 'amused', t=st, dur=0.3, lid=.3, tiltb=.6)
    S('BEE', t=st + 0.2, dur=0.3, look=(-1, -.3))
    S('BEE', t=st + d * 0.6, dur=0.3, look='GOSTE')
    ex(tl, 'GOSTE', 'awe', t=st + d * 0.7, dur=0.6, mopen=0, smile=0, tear=.6)
    S('GOSTE', t=st + d * 0.7, dur=1.0, alpha=.5)

    tl.cam('clawd', dt=-0.1, dur=0)
    S('CLAWD', dt=-0.1, look=(-.6, 1))
    ex(tl, 'CLAWD', 'grumpy', dt=-0.1, dur=0.3, lid=.6)
    tl.sfx('sigh', dt=0.1)
    S('CLAWD', dt=0.1, dur=0.8, y=445)
    S('CLAWD', dt=0.9, dur=0.8, y=430)
    tl.wait(0.9)
    st, d = tl.line('CLAWD', "...Fine. I'll keep an eye on the kid too.", gap=0.25, speed=1.08)
    S('CLAWD', t=st + 0.5, dur=0.4, look=(.6, -.6))
    S('CLAWD', t=st + d * 0.6, dur=0.4, look='GOSTE')
    st, d = tl.line('CLAWD', "Just the one.", gap=0.3, speed=1.05)
    ex(tl, 'CLAWD', 'amused', t=st, dur=0.4, smile=.3, lid=.35)
    S('CLAWD', t=st, dur=1.0, dark=.1)
    tl.cam('clawdia', dt=-0.1, dur=0)
    ex(tl, 'CLAWDIA', 'happy', dt=-0.1, dur=0.6, tear=.4)
    S('CLAWDIA', dt=-0.1, dur=1.2, rain=0, dark=0, look=(-.5, 1))
    st, d = tl.line('CLAWDIA', "We all will.", hi=['all'], gap=0.4)

    tl.mood('tender', dt=-0.3)
    tl.cam('goste_cu', dt=-0.1, dur=0)
    ex(tl, 'GOSTE', 'hurt', dt=-0.1, dur=0.6, tear=.9, lid=.15)
    S('GOSTE', dt=-0.1, look=(.4, -.6), alpha=.6, dur=0.8)
    st, d = tl.line('GOSTE', "But you don't even know who I am.", speed=1.12, gap=0.5)
    tl.cam('iris_goste', dt=-0.1, dur=3.0)
    S('IRIS', dt=-0.3, dur=1.4, lean=-1, droop=0, spread=.3, leafL=.9)
    ex(tl, 'IRIS', 'tender', dt=-0.3, dur=0.8)
    S('IRIS', dt=-0.3, look='GOSTE')
    S('GOSTE', dt=0, look='IRIS')
    st, d = tl.line('IRIS', "We don't need to know who you were.", speed=1.12, gap=0.2)
    st, d = tl.line('IRIS', "Only who you are tonight.", hi=['tonight'], speed=1.14, gap=0.7)
    ex(tl, 'IRIS', 'soft_smile', t=st + d * 0.6, dur=0.6)
    S('GOSTE', t=st + d * 0.5, dur=2.0, alpha=.8, tremble=0)
    ex(tl, 'GOSTE', 'awe', t=st + d * 0.5, dur=0.8, mopen=0, tear=.6, smile=.05)
    tl.sfx('shimmer', t=st + d * 0.5)

    # ================= THE WINDOW LOOKS BACK =================
    tl.mood('wonder', dt=-0.2)
    tl.cam('window_wide', dt=-0.1, dur=4)
    st, d = tl.line('N', "And then, something happened that had never happened before... on any Halloween.", gap=0.5)
    S('WORLD', t=st + d * 0.5, dur=0.3, window=.6)
    S('WORLD', t=st + d * 0.5 + 0.3, dur=0.3, window=1.1)
    tl.sfx('chime', t=st + d * 0.6)
    tl.cam('window', t=st + d, dur=1.6)
    S('WORLD', t=st + d - 0.3, dur=1.5, child=1)
    st, d = tl.line('N', "The window... looked back.", hi=['looked back'], gap=0.6, speed=1.1)
    S('WORLD', t=st + d + 0.1, dur=0.4, childwave=1)
    for ch in ('IRIS', 'CLAWD', 'CLAWDIA', 'BEE', 'GOSTE'):
        S(ch, t=st + 0.8, look='WINDOW')
    ex(tl, 'CLAWD', 'surprised', t=st + 0.8, dur=0.3, mopen=.2)
    ex(tl, 'CLAWDIA', 'surprised', t=st + 0.8, dur=0.3, mopen=.2)
    ex(tl, 'BEE', 'surprised', t=st + 0.8, dur=0.3)
    ex(tl, 'IRIS', 'surprised', t=st + 0.8, dur=0.3, mopen=.1)
    ex(tl, 'GOSTE', 'surprised', t=st + 0.8, dur=0.3, mopen=0, tear=.4)
    tl.cam('sky', dt=0.1, dur=0)
    st, d = tl.line('CLAWD', "We're not supposed to be seen...", whisper=True, gap=0.3, speed=1.05)
    tl.cam('iris_cu', dt=-0.1, dur=0)
    ex(tl, 'IRIS', 'soft_smile', dt=-0.1, dur=0.6)
    S('IRIS', dt=0.4, dur=0.4, look='GOSTE')
    st, d = tl.line('IRIS', "Not us, Clawd. Look who they're waving at.", speed=1.1, gap=0.5)
    S('IRIS', t=st + d * 0.4, look='CLAWD')
    S('IRIS', t=st + d * 0.75, look='GOSTE')
    tl.cam('goste_cu', dt=0, dur=5.0)
    S('GOSTE', dt=0, look='WINDOW')
    S('GOSTE', dt=0.6, dur=0.8, armR=.9, alpha=.95)
    S('GOSTE', dt=1.2, wave=1)
    tl.sting('hi', dt=1.6, strength=1.0)
    # the O finally finishes
    S('GOSTE', dt=1.8, dur=1.6, oness=0)
    ex(tl, 'GOSTE', 'happy', dt=1.8, dur=1.4, tear=.8, blush=1)
    tl.sfx('shimmer', dt=1.8)
    tl.wait(3.2)
    st, d = tl.line('GOSTE', "They see me. ...I'm here.", speed=1.1, gap=0.2)
    st, d = tl.line('GOSTE', "I'm really here.", hi=['really here'], speed=1.08, gap=0.4)
    S('GOSTE', t=st + d, wave=0, dur=0.5, armR=0)
    S('GOSTE', t=st + d, look='IRIS')
    tl.cam('iris_goste', dt=-0.1, dur=3.5)
    S('IRIS', dt=-0.1, look='GOSTE', dur=1.0, spread=.6, droop=0, lean=-.7)
    ex(tl, 'IRIS', 'happy', dt=-0.1, dur=0.6, tear=.4)
    st, d = tl.line('IRIS', "That's how it works, little one.", speed=1.12, gap=0.2)
    st, d = tl.line('IRIS', "When someone sees you... you become real.", hi=['real'], speed=1.15, gap=0.6)
    tl.mood('hope', t=st + d * 0.7)
    tl.cam('wide', t=st + d, dur=3)
    for ch in ('CLAWD', 'CLAWDIA', 'BEE'):
        S(ch, t=st + d * 0.5, look='GOSTE')
        ex(tl, ch, 'happy', t=st + d * 0.6, dur=0.6)
    S('CLAWD', t=st + d, dur=1, dark=0)
    S('BEE', t=st + d, dur=2.0, x=100, y=1160)
    S('WORLD', t=st + d * 0.6, dur=1.2, mooneye=1)
    S('WORLD', t=st + d + 0.5, dur=6.0, dawn=1)

    # ================= MORNING: back to the page =================
    st, d = tl.line('N', "The next morning, a child sat at the kitchen table with one black marker.", gap=0.3)
    S('WORLD', t=st, dur=0.8, childwave=0)
    xf = st + d - 1.0
    S('PHOTO', t=xf, dur=0, cx=751, cy=1000, zoom=1.18)
    S('PHOTO', t=xf, dur=1.6, alpha=1)
    tl.scene('photo', t=xf + 1.6)
    tl.sfx('paper', t=xf + 0.6)
    S('PHOTO', t=xf, dur=14, zoom=1.0)
    st, d = tl.line('N', "They drew two clouds, with one eye each. A brave little bee. A flower who watches over everything.",
                    gap=0.3)
    S('PHOTO', t=st + 0.9, dur=0.3, flook=(-.7, -.6))
    S('PHOTO', t=st + d - 1.0, dur=0.3, flook=(0, 0))
    st, d = tl.line('N', "And one small ghost... so it would never, ever be erased.", hi=['never, ever'], gap=0.4)
    S('PHOTO', t=st + 1.0, dur=0.3, flook=(-.9, -.5))
    S('PHOTO', t=st + d * 0.6, dur=1.4, ghostsmile=1)
    tl.sfx('shimmer', t=st + d * 0.6)
    S('PHOTO', t=st + d * 0.6, dur=0.3, ghostlook=(.6, .2))
    S('PHOTO', t=st + d + 0.2, dur=0.3, flook=(0, .1))
    S('WORLD', t=st + d, dur=0.8, endtitle=1)
    st, d = tl.line('N', "Happy Halloween. Keep watching the ones you love.", hi=['love'], gap=0.4)
    S('PHOTO', t=st + d * 0.8, dur=0.15, wink=1)
    S('PHOTO', t=st + d * 0.8 + 0.5, dur=0.2, wink=0)
    tl.wait(1.8)
    tl.end = tl.t
