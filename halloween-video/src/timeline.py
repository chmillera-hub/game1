"""Timeline: lines, keyframed character params, camera, sfx, music moods."""
from collections import defaultdict

FPS = 24
W, H = 1080, 1920


class TL:
    def __init__(self, durs=None, onsets=None):
        self.t = 0.0
        self.durs = durs or {}
        self.onsets = onsets or {}
        self.lines = []
        self.keys = defaultdict(list)   # (ch, param) -> [(t, value, dur)]
        self.cams = []                  # (t, shot, dur)
        self.events = []                # (t, kind, kwargs)
        self.moods = []                 # (t, mood)
        self.stings = []                # (t, 'hi'|'lo', strength)
        self.scenes = []                # (t, scene)

    @staticmethod
    def vkey(sp, text, speed, pitch):
        return f"{sp}|{speed:.3f}|{pitch:.3f}|{text}"

    def line(self, sp, text, gap=0.35, hi=(), lo=(), speed=1.0, pitch=1.0,
             vol=1.0, whisper=False, sub=None):
        key = self.vkey(sp, text, speed, pitch)
        d = self.durs.get(key, 0.075 * len(text) + 0.4)
        st = self.t
        self.lines.append(dict(sp=sp, text=text, start=st, dur=d, key=key,
                               speed=speed, pitch=pitch, vol=vol, whisper=whisper,
                               hi=list(hi), lo=list(lo), sub=sub or text))
        for kind, words in (('hi', hi), ('lo', lo)):
            for w in words:
                on = self.onsets.get((key, w), 0.0)
                self.stings.append((st + on, kind, 1.0))
        self.t = st + d + gap
        return st, d

    def wait(self, s):
        self.t += s

    def at(self, t=None, dt=0.0):
        return (self.t if t is None else t) + dt

    def set(self, ch, dt=0.0, dur=0.35, t=None, **p):
        tt = self.at(t, dt)
        for k, v in p.items():
            self.keys[(ch, k)].append((tt, v, dur))

    def cam(self, shot, dt=0.0, dur=0.0, t=None):
        self.cams.append((self.at(t, dt), shot, dur))

    def sfx(self, name, dt=0.0, t=None, **kw):
        self.events.append((self.at(t, dt), name, kw))

    def mood(self, name, dt=0.0, t=None):
        self.moods.append((self.at(t, dt), name))

    def sting(self, kind, dt=0.0, t=None, strength=1.0):
        self.stings.append((self.at(t, dt), kind, strength))

    def scene(self, name, dt=0.0, t=None):
        self.scenes.append((self.at(t, dt), name))
