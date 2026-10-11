"""Audio-first timeline: voice lines + pauses fix every cue; shots cut on cues."""
import json
import os
import numpy as np

WORK = os.environ.get('WORK', os.path.join(os.path.dirname(__file__), 'work'))
META = json.load(open(f'{WORK}/voice/meta.json'))
FPS = 24

# Pauses (seconds) interleaved with line ids.  Long pauses are acting beats.
AUDIO = [1.6, 'N1', 1.3, 'M1', 0.5, 'M2', 1.7, 'G1', 0.6, 'J1', 1.5, 'X1', 1.1, 'X2', 2.8,
         'N2', 0.9, 'X3', 1.3, 'N3', 1.7, 'XC', 2.3, 'X4', 2.6,
         'G2', 0.8, 'Y1', 0.8, 'Y2', 0.9, 'Y3', 1.0, 'J2', 0.9, 'Y4', 1.7,
         'X5', 4.8, 'C1', 2.3,
         'N4', 0.6, 'N5', 0.9, 'N6', 1.3,
         'N7', 1.1, 'Q1', 1.3, 'R1', 1.0, 'Q2', 1.1, 'R2', 0.9, 'R3', 2.8, 'Q3', 0.9, 'R4', 1.5,
         'N8', 0.7, 'N9', 1.1, 'N10', 0.8, 'N11', 1.3, 'N12', 0.9, 'N13', 4.0]

S, E = {}, {}
_t = 0.0
for item in AUDIO:
    if isinstance(item, str):
        S[item] = _t
        _t += META[item]['dur']
        E[item] = _t
    else:
        _t += item
TOTAL = _t


def F(lid, k):
    """Global (start, end) of fragment k of a line."""
    a, b = META[lid]['frags'][k]
    return S[lid] + a, S[lid] + b


SHOTS = [
    ('open', 0.0),
    ('mockers', S['M1'] - 0.45),
    ('mary_cu:flinch', E['M2'] + 0.25),
    ('magdalene_cu:laugh', S['G1'] - 0.15),
    ('john_cu:feel', E['G1'] + 0.35),
    ('jesus_low', E['J1'] + 0.55),
    ('group3', E['X2'] + 0.45),
    ('golgotha:dark', S['N2'] - 0.25),
    ('jesus_cu:pray', E['N2'] + 0.45),
    ('golgotha:ninth', E['X3'] + 0.65),
    ('jesus_cu:cry', E['N3'] + 0.35),
    ('golgotha:cry', E['XC'] + 0.25),
    ('jesus_cu:forsaken', S['X4'] - 0.35),
    ('centurion_cu:react', E['X4'] + 0.55),
    ('magdalene_cu:mother', S['G2'] - 0.75),
    ('mary_cu:let', E['G2'] + 0.25),
    ('flashback', F('Y2', 1)[0] - 0.15),
    ('mary_cu:quiet', E['Y2'] + 0.35),
    ('john_cu:psalm', E['Y3'] + 0.45),
    ('mary_cu:praying', E['J2'] + 0.45),
    ('jesus_cu:father', E['Y4'] + 0.9),
    ('golgotha:quake', E['X5'] + 1.9),
    ('centurion_cu:truly', E['X5'] + 2.75),
    ('mary_cu:look', E['C1'] + 0.55),
    ('golgotha:dusk', S['N4'] - 0.3),
    ('centurion_cu:after', S['N5'] - 0.25),
    ('golgotha:dusk2', S['N6'] - 0.35),
    ('phone_cu', E['N6'] + 0.65),
    ('porch_two', E['N7'] + 0.55),
    ('nana_cu:every', E['Q1'] + 0.45),
    ('young_cu:what', E['R1'] + 0.5),
    ('nana_cu:heart', E['Q2'] + 0.55),
    ('young_cu:listen', F('R2', 2)[0] - 0.25),
    ('nana_cu:silence', E['R2'] + 0.45),
    ('acorn_hands', E['R3'] + 0.35),
    ('young_cu:acorn', S['Q3'] - 0.6),
    ('nana_cu:plant', E['Q3'] + 0.45),
    ('planting', E['R4'] + 0.8),
    ('golgotha:garden', E['N8'] + 0.35),
    ('golgotha:tree', E['N9'] + 0.6),
    ('porch_dawn', E['N11'] + 0.7),
    ('young_cu:dawn', S['N13'] - 0.4),
]


class Shot:
    def __init__(self, i, name, start, end):
        self.i, self.start, self.end = i, start, end
        self.setup, _, self.variant = name.partition(':')
        self.name = name

    def __repr__(self):
        return f'{self.name}[{self.start:.2f}-{self.end:.2f}]'


SHOT_LIST = [Shot(i, n, s, SHOTS[i + 1][1] if i + 1 < len(SHOTS) else TOTAL)
             for i, (n, s) in enumerate(SHOTS)]


def shot_at(t):
    for sh in SHOT_LIST:
        if sh.start <= t < sh.end:
            return sh
    return SHOT_LIST[-1]

# --------------------------------------------------------------- lip sync ---

_ENV = {}


def env(lid):
    if lid not in _ENV:
        z = np.load(f'{WORK}/voice/{lid}_env.npz')
        k = np.hanning(7); k /= k.sum()
        loud = np.convolve(z['loud'], k, mode='same')
        bright = np.convolve(z['bright'], k, mode='same')
        _ENV[lid] = (loud, bright)
    return _ENV[lid]


LINES_BY_CHAR = {}
for lid, m in META.items():
    LINES_BY_CHAR.setdefault(m['char'], []).append(lid)


def speech(char, t, lead=0.04):
    """Return (loudness 0..1.4, brightness) of `char` speaking at time t."""
    for lid in LINES_BY_CHAR.get(char, []):
        if S[lid] - 0.05 <= t <= E[lid] + 0.05:
            loud, bright = env(lid)
            i = (t - S[lid] + lead) * 100
            if i < 0 or i >= len(loud) - 1:
                return 0.0, 0.3
            j = int(i); fr = i - j
            return float(loud[j] * (1 - fr) + loud[j + 1] * fr), float(bright[j] * (1 - fr) + bright[j + 1] * fr)
    return 0.0, 0.3


CAPTIONS = {
    'N1': "It was noon… and darkness came over the whole land.",
    'M1': "He trusted in the Lord.",
    'M2': "Then let the Lord rescue him… since he delights in him!",
    'G1': "How can they look at him… and laugh?",
    'J1': "Because if they laugh… they don't have to feel it.",
    'X1': "Woman… here is your son.",
    'X2': "Son… here is your mother.",
    'N2': "For three hours, the sky held its breath.",
    'X3': "You are my strength… do not be far from me.",
    'N3': "Then, at the ninth hour…",
    'XC': "Eloi! Eloi! Lema sabachthani?",
    'X4': "My God… my God… why have you forsaken me?",
    'G2': "Mother… he's crying out. Everyone can hear him.",
    'Y1': "Let them hear.",
    'Y2': "The night he was born, he cried just like that. I didn't hush him. I held him.",
    'Y3': "I won't ask him to be quiet now.",
    'J2': "It's the psalm. “From my mother's womb… you have been my God.”",
    'Y4': "He's still praying, John. Out loud.",
    'X5': "Father… into your hands… I commit my spirit.",
    'C1': "Truly… this man was the Son of God.",
    'N4': "He didn't whisper it. He cried it out, in front of everyone.",
    'N5': "And the soldier sent to silence him… was the one who heard him.",
    'N6': "It was the sacred scream of a soul refusing to suffer in silence. Emotional truth, made public.",
    'N7': "Two thousand years later, the world is numb. Half asleep. But underneath it all, the pain is volcanic.",
    'Q1': "Nana? Do you ever feel like you're screaming… and everyone just nods politely, and scrolls past?",
    'R1': "Every day of my life, baby.",
    'Q2': "Then what do we do? Without turning cruel… and without letting them convince us we're crazy?",
    'R2': "We speak close to the heart. We feel it, all the way through. And we listen to what the night is trying to teach us.",
    'R3': "Silence isn't strength, baby. God didn't stay silent while He suffered. So why should you?",
    'Q3': "An acorn?",
    'R4': "Plant it. Tend what grows from the hard places.",
    'N8': "When the noise gets too loud, a parable can hold what plain words can't.",
    'N9': "In the place where he was crucified, there was a garden.",
    'N10': "Suffering, tended with care, can grow into a tree. And its fruit is connection.",
    'N11': "The kind that still cries out in grief, because it remembers what came before… and will not let the machine of suppression tear the garden down.",
    'N12': "So here we are. Still breathing. Still feeling. Still tending the garden. That's sacred.",
    'N13': "Keep the fire lit. Others are watching. And maybe the garden in them is waiting for the Lord of their emotions to wake them up too.",
}


def caption_at(t):
    """Split long captions across the line's fragments so each card stays short."""
    for lid, text in CAPTIONS.items():
        if S[lid] - 0.1 <= t <= E[lid] + 0.35:
            frags = META[lid]['frags']
            words = text.split()
            if len(words) <= 9:
                return text, lid
            # group fragments into chunks of <= ~9 words
            ftxt = _frag_text(lid)
            chunks, cur, cur_s = [], [], None
            for k, ft in enumerate(ftxt):
                if cur and len(' '.join(cur + [ft]).split()) > 10:
                    chunks.append((cur_s, ' '.join(cur)))
                    cur, cur_s = [], None
                if cur_s is None:
                    cur_s = S[lid] + frags[k][0]
                cur.append(ft)
            chunks.append((cur_s, ' '.join(cur)))
            cur_txt = chunks[0][1]
            for cs, ct in chunks:
                if t >= cs - 0.1:
                    cur_txt = ct
            return cur_txt, lid
    return None, None


def _frag_text(lid):
    import script
    raw = dict((l, tx) for l, c, tx in script.LINES)[lid]
    if raw == '@CRY':
        return ['Eloi!', 'Eloi!', 'Lema sabachthani?']
    parts = [p.strip() for p in raw.replace('||', '|').split('|') if p.strip()]
    return [p.replace('...', '…') for p in parts]
