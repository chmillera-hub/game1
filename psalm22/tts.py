"""Voice every line of the screenplay with Kokoro and store audio + lip-sync data."""
import os, sys, json, subprocess, tempfile
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
from kokoro_onnx import Kokoro
sys.path.insert(0, os.path.dirname(__file__))
from script import CAST, LINES, CRY_PHONEMES

MODELS = os.environ['KOKORO_DIR']
OUT = os.environ['WORK'] + '/voice'
os.makedirs(OUT, exist_ok=True)
SR = 48000
PAUSE = {'|': 0.45, '||': 0.95}
SLOW = 0.95   # everyone a touch slower, for processing time

k = Kokoro(f'{MODELS}/kokoro-v1.0.onnx', f'{MODELS}/voices-v1.0.bin')

def synth(text, voice, speed, lang, phon=False):
    a, sr = k.create(text, voice=voice, speed=speed * (1 if phon else SLOW), lang=lang, is_phonemes=phon)
    a = resample_poly(a.astype(np.float64), 2, 1)  # 24k -> 48k
    # trim residual silence
    thr = 0.01 * np.max(np.abs(a))
    idx = np.where(np.abs(a) > thr)[0]
    a = a[max(0, idx[0] - 480): idx[-1] + 1440]
    return a

def shift(a, semis):
    if abs(semis) < 1e-3:
        return a
    with tempfile.TemporaryDirectory() as d:
        sf.write(f'{d}/i.wav', a, SR)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{d}/i.wav', '-af',
                        f'rubberband=pitch={2 ** (semis / 12):.5f}:formant=preserved:pitchq=quality',
                        f'{d}/o.wav'], check=True)
        b, _ = sf.read(f'{d}/o.wav')
    return b

def split(text):
    parts, cur, i = [], '', 0
    while i < len(text):
        if text.startswith('||', i):
            parts.append((cur.strip(), PAUSE['||'])); cur = ''; i += 2
        elif text[i] == '|':
            parts.append((cur.strip(), PAUSE['|'])); cur = ''; i += 1
        else:
            cur += text[i]; i += 1
    parts.append((cur.strip(), 0.0))
    return [(p, g) for p, g in parts if p]

def envelope(a):
    """100 Hz loudness + brightness tracks for lip sync."""
    hop = SR // 100
    n = len(a) // hop + 1
    pad = np.pad(a, (0, n * hop + 2048 - len(a)))
    loud = np.zeros(n); bright = np.zeros(n)
    win = np.hanning(1024)
    freqs = np.fft.rfftfreq(1024, 1 / SR)
    lo = (freqs > 250) & (freqs < 1100); hi = (freqs > 2200) & (freqs < 6000)
    for i in range(n):
        seg = pad[i * hop: i * hop + 1024]
        loud[i] = np.sqrt(np.mean(seg ** 2))
        sp = np.abs(np.fft.rfft(seg * win)) ** 2
        bright[i] = sp[hi].sum() / (sp[lo].sum() + sp[hi].sum() + 1e-9)
    ref = np.percentile(loud[loud > 1e-4], 92) if np.any(loud > 1e-4) else 1
    loud = np.clip(loud / (ref + 1e-9), 0, 1.4)
    return loud.astype(np.float32), bright.astype(np.float32)

def find_gaps(a, thr=0.036, minlen=0.06):
    """Silent stretches inside an utterance (at 48 kHz)."""
    hop = 480
    e = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a) - hop, hop)])
    q = e < thr * e.max()
    out, i = [], 0
    while i < len(q):
        if q[i]:
            j = i
            while j < len(q) and q[j]:
                j += 1
            if (j - i) * hop / SR >= minlen and i > 0 and j < len(q):
                out.append((i * hop / SR, j * hop / SR))
            i = j
        else:
            i += 1
    return out


def voice_line(text, voice, speed, lang, semis):
    """Synthesize the whole line for natural prosody, then lengthen the pauses at the markers."""
    frags = split(text)
    plain = ' '.join(f for f, _ in frags)
    a = synth(plain, voice, speed, lang)
    a = shift(a, semis)
    dur = len(a) / SR
    gaps = find_gaps(a)
    # expected position of each marker by character share
    total_chars = sum(len(f) for f, _ in frags)
    cuts, used, acc = [], set(), 0
    for f, pause in frags[:-1]:
        acc += len(f)
        guess = dur * acc / total_chars
        best, bscore = None, 1e9
        for gi, (g0, g1) in enumerate(gaps):
            if gi in used:
                continue
            c = (g0 + g1) / 2
            score = abs(c - guess) - 1.5 * min(g1 - g0, 0.4)
            if score < bscore:
                best, bscore = gi, score
        if best is None or abs((gaps[best][0] + gaps[best][1]) / 2 - guess) > 0.25 * dur + 0.3:
            cuts.append((guess, guess, pause))
        else:
            used.add(best)
            cuts.append((gaps[best][0], gaps[best][1], pause))
    cuts.sort()
    out, frag_t, pos, tcur = [], [], 0, 0.0
    for g0, g1, pause in cuts:
        mid = int((g0 + g1) / 2 * SR)
        seg = a[pos:mid]
        out.append(seg)
        start = tcur
        tcur += len(seg) / SR
        frag_t.append((start, start + (g0 - pos / SR)))
        extra = max(0.0, pause - (g1 - g0))
        out.append(np.zeros(int(extra * SR)))
        tcur += extra
        pos = mid
    seg = a[pos:]
    out.append(seg)
    lead = (cuts[-1][1] - cuts[-1][0]) / 2 if cuts else 0.0
    frag_t.append((tcur + lead, tcur + len(seg) / SR))
    # first fragment starts at 0, later fragments start after their gap
    fixed = []
    for i, (s0, s1) in enumerate(frag_t):
        if i > 0:
            g0, g1, _ = cuts[i - 1]
            s0 = s0 + (g1 - g0) / 2 if i < len(frag_t) - 1 else s0
        fixed.append((s0, s1))
    return np.concatenate(out), fixed


def clean_edges(a, lid):
    """Soften a breathy onset / stray tail that the TTS sometimes leaves on a line."""
    hop = 480
    e = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a) - hop, hop)])
    m = e.max()
    first = int(np.argmax(e > 0.3 * m))
    s0 = max(0, (first - 4) * hop)
    if s0 > 0:
        a = a.copy()
        a[:s0] *= 0.15
    if lid in ('Y1',):
        last = len(e) - 1 - int(np.argmax(e[::-1] > 0.3 * m))
        end = min(len(a), (last + 14) * hop)
        a = a[:end].copy()
        a[-1440:] *= np.linspace(1, 0, 1440)
    return a


meta = {}
only = set(sys.argv[1:])
old_meta = {}
if only and os.path.exists(f'{OUT}/meta.json'):
    old_meta = json.load(open(f'{OUT}/meta.json'))
for lid, char, text in LINES:
    if only and lid not in only:
        meta[lid] = old_meta[lid]
        continue
    voice, speed, lang, semis = CAST[char]
    chunks = []
    frags = []
    if text == '@CRY':
        gaps = [1.05, 1.15, 0.0]
        for ph, g in zip(CRY_PHONEMES, gaps):
            a = synth(ph, voice, 0.66, lang, phon=True)
            a = shift(a, 1.2)                       # vocal strain
            a = a / (np.max(np.abs(a)) + 1e-9)
            a = np.tanh(2.2 * a) / np.tanh(2.2)     # raw, pushed voice
            t0 = sum(len(c) for c in chunks) / SR
            frags.append((t0, t0 + len(a) / SR))
            chunks += [a, np.zeros(int(g * SR))]
        a = np.concatenate(chunks)
    else:
        a, frags = voice_line(text, voice, speed, lang, semis)
    a = clean_edges(a, lid)
    a = a / (np.max(np.abs(a)) + 1e-9) * 0.9
    sf.write(f'{OUT}/{lid}.wav', a.astype(np.float32), SR)
    loud, bright = envelope(a)
    np.savez(f'{OUT}/{lid}_env.npz', loud=loud, bright=bright)
    meta[lid] = {'char': char, 'dur': len(a) / SR, 'frags': frags}
    print(f'{lid:4s} {char:10s} {len(a)/SR:5.2f}s  frags={len(frags)}', flush=True)

# Crowd murmur material
if only:
    json.dump(meta, open(f'{OUT}/meta.json', 'w'), indent=1)
    sys.exit(0)
crowd = ["What did he say?", "Look at the sky.", "Come away from here.", "Is he still alive?",
         "They say he healed people.", "Hush, the soldiers are watching.", "Where are his friends now?",
         "It's so dark.", "I can't look.", "Let's go home."]
voices = ['am_eric', 'bm_daniel', 'af_river', 'am_liam', 'bf_lily', 'am_echo', 'bf_alice', 'am_adam', 'af_jessica', 'am_onyx']
for i, (t, v) in enumerate(zip(crowd, voices)):
    a = synth(t, v, 0.95, 'en-gb' if v[0] == 'b' else 'en-us')
    sf.write(f'{OUT}/crowd{i}.wav', (a / (np.max(np.abs(a)) + 1e-9) * 0.9).astype(np.float32), SR)
json.dump(meta, open(f'{OUT}/meta.json', 'w'), indent=1)
print('total speech', sum(m['dur'] for m in meta.values()))
