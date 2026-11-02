"""Pick, shape, level and package the narration.

usage: python process_voice.py <takes dir> <out dir> <voice.js out> [--pre SECONDS] [--gain G]

For every line: transcribe each take with Whisper, keep the take that says the words
exactly (then the one that fits its window), trim it, open its pauses to the scripted
lengths, fit it to its caption window, match loudness, find when each caption word is
spoken, and lay all lines end to end into one MP3 embedded as 01b-voice.js.
"""
import sys, os, re, json, glob, base64, subprocess, difflib, warnings, argparse
import numpy as np, soundfile as sf, librosa, pyloudnorm as pyln
warnings.filterwarnings('ignore')
from faster_whisper import WhisperModel

ap = argparse.ArgumentParser()
ap.add_argument('takes'); ap.add_argument('out'); ap.add_argument('js')
ap.add_argument('--pre', type=float, default=0.0)
ap.add_argument('--gain', type=float, default=1.0)
ap.add_argument('--lead', type=float, default=0.18)
ap.add_argument('--gap', type=float, default=0.7)
args = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(args.out, exist_ok=True)
SR = 24000
TARGET_LUFS = -17.0
lines = json.load(open(f'{HERE}/lines.json'))
script = json.load(open(f'{HERE}/script.json'))
wm = WhisperModel('small.en', device='cpu', compute_type='int8')
meter = pyln.Meter(SR)

FILLERS = {'ah', 'oh', 'uh', 'um', 'hmm', 'mm', 'ha', 'haha', 'heh', 'huh', 'hm'}
NUM = {'99': 'ninetynine', 'ninety-nine': 'ninetynine'}

def norm(w):
    w = w.lower().replace('’', "'")
    w = NUM.get(w.strip('.,!?;:'), w)
    return re.sub(r"[^a-z0-9]", '', w)

def words_of(say):
    return [w for w in re.sub(r'\s*\{[0-9.]+\}\s*', ' ', say).split()]

def transcribe(y):
    y16 = librosa.resample(y, orig_sr=SR, target_sr=16000)
    segs, _ = wm.transcribe(y16, beam_size=5, word_timestamps=True, language='en',
                            initial_prompt='ninety-nine, pro-human, grim reaper')
    out = []
    for s in segs:
        for w in s.words:
            t = w.word.strip()
            if out and t.startswith('-'):            # Whisper splits hyphenated words: "ninety" "-nine"
                p = out[-1]; out[-1] = (p[0] + t, p[1], w.end); continue
            for x in {'wanna': ['want', 'to'], 'gonna': ['going', 'to'], 'gotta': ['got', 'to']}.get(norm(t), [t]):
                out.append((x, w.start, w.end))
    return out

def errors(expected, hyp):
    e = [norm(w) for w in expected]; h = [norm(w[0]) for w in hyp if norm(w[0]) not in FILLERS]
    e = [x for x in e if x]; h = [x for x in h if x]
    sm = difflib.SequenceMatcher(a=e, b=h, autojunk=False)
    return sum(max(i2 - i1, j2 - j1) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != 'equal')

def trim(y, head=0.12, tail=0.16):
    fr = librosa.feature.rms(y=y, frame_length=480, hop_length=120)[0]
    thr = max(fr.max() * 10 ** (-46 / 20), 1e-4)
    on = np.where(fr > thr)[0]
    if not len(on):
        return y
    s = max(0, on[0] * 120 - int(head * SR)); e = min(len(y), on[-1] * 120 + 480 + int(tail * SR))
    out = y[s:e].copy()
    f = int(0.006 * SR); out[:f] *= np.linspace(0, 1, f); out[-f:] *= np.linspace(1, 0, f)
    return out

def longest_internal_gap(y):
    fr = librosa.feature.rms(y=y, frame_length=480, hop_length=120)[0]
    quiet = fr < fr.max() * 10 ** (-38 / 20)
    best = run = 0
    for q in quiet:
        run = run + 1 if q else 0; best = max(best, run)
    return best * 120 / SR

def pause_slots(say):
    """[(word index after which to pause, seconds)] from the {x} markers."""
    out, n = [], 0
    for part in re.split(r'(\{[0-9.]+\})', say):
        m = re.fullmatch(r'\{([0-9.]+)\}', part)
        if m:
            out.append((n, float(m.group(1))))
        else:
            n += len(part.split())
    return out

def shape_pauses(y, hyp, say, scale=1.0):
    """Open each scripted pause to its length, splicing silence in at the quietest point of the gap."""
    content = [w for w in hyp if norm(w[0]) not in FILLERS and norm(w[0])]
    inserts = []
    for k, secs in pause_slots(say):
        if k <= 0 or k >= len(content):
            continue
        end_prev, start_next = content[k - 1][2], content[k][1]
        gap = max(0.0, start_next - end_prev)
        add = secs * scale - gap
        if add <= 0.03:
            continue
        a, b = int(max(0, end_prev - 0.04) * SR), int(min(len(y) / SR, start_next + 0.04) * SR)
        if b - a < 64:
            at = int((end_prev + start_next) / 2 * SR)
        else:
            seg = y[a:b] ** 2
            win = np.convolve(seg, np.ones(240) / 240, mode='same')
            at = a + int(np.argmin(win))
        inserts.append((at, add))
    if not inserts:
        return y
    parts, last = [], 0
    for at, add in sorted(inserts):
        f = 120
        pre = y[last:at].copy(); n = min(f, len(pre))
        if n:
            pre[-n:] *= np.linspace(1, 0, n)
        parts += [pre, np.zeros(int(add * SR), np.float32)]
        last = at
    post = y[last:].copy(); n = min(120, len(post)); post[:n] *= np.linspace(0, 1, n)
    parts.append(post)
    return np.concatenate(parts)

def atempo(y, factor):
    tmp_in, tmp_out = f'{args.out}/_in.wav', f'{args.out}/_out.wav'
    sf.write(tmp_in, y, SR)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp_in, '-af', f'atempo={factor:.4f}', tmp_out], check=True)
    out, _ = sf.read(tmp_out, dtype='float32')
    return out

def polish(y):
    """Voice-over treatment: rumble cut, a little less boom, a little more presence, gentle compression."""
    tmp_in, tmp_out = f'{args.out}/_pin.wav', f'{args.out}/_pout.wav'
    sf.write(tmp_in, y, SR)
    chain = ('highpass=f=70,equalizer=f=220:t=q:w=1.2:g=-1.5,equalizer=f=3200:t=q:w=1.4:g=1.5,'
             'acompressor=threshold=0.08:ratio=2.5:attack=12:release=150:knee=6:makeup=1.6')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp_in, '-af', chain, '-ar', str(SR), tmp_out], check=True)
    out, _ = sf.read(tmp_out, dtype='float32')
    return out

def caption_word_times(caption, hyp):
    cw = caption.replace(' / ', ' ').split()
    c = [norm(w) for w in cw]
    h = [(norm(w[0]), w[1], w[2]) for w in hyp]
    h = [x for x in h if x[0] and x[0] not in FILLERS]
    times = [None] * len(cw)
    sm = difflib.SequenceMatcher(a=c, b=[x[0] for x in h], autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal' or (op == 'replace' and i2 - i1 == j2 - j1):
            for k in range(i2 - i1):
                times[i1 + k] = h[j1 + k][1]
        elif op == 'replace':
            for k in range(i2 - i1):
                times[i1 + k] = h[j1 + min(j2 - j1 - 1, int(k * (j2 - j1) / (i2 - i1)))][1]
    end = h[-1][2] if h else 0
    # fill gaps (emoji, words Whisper merged) by interpolating between known neighbours
    for i in range(len(times)):
        if times[i] is None:
            prev = next((times[j] for j in range(i - 1, -1, -1) if times[j] is not None), 0.0)
            nxt = next((times[j] for j in range(i + 1, len(times)) if times[j] is not None), None)
            times[i] = (prev + nxt) / 2 if nxt is not None else max(prev + 0.25, end - 0.1)
    for i in range(1, len(times)):
        times[i] = max(times[i], times[i - 1] + 0.04)
    return [round(float(t), 3) for t in times]

report, clips, audio = [], [], []
cursor = 0.25
for i, (L, S) in enumerate(zip(lines, script)):
    expected = words_of(S['say'])
    budget = (L['win'] - args.lead - args.gap) if i < len(lines) - 1 else 4.5
    cands = []
    for f in sorted(glob.glob(f'{args.takes}/line_{i:02d}*.wav')):
        y, sr = sf.read(f, dtype='float32')
        if y.ndim > 1:
            y = y.mean(1)
        if sr != SR:
            y = librosa.resample(y, orig_sr=sr, target_sr=SR)
        y = trim(y)
        hyp = transcribe(y)
        err = errors(expected, hyp)
        gapmax = longest_internal_gap(y)
        dur = len(y) / SR
        # exact words first; then no long dead air; then a take that fits without squeezing
        score = err * 10 + max(0, gapmax - 1.0) * 6 + max(0, dur - budget) * 2 + (0.15 if 'take0' not in f else 0)
        cands.append((score, f, y, hyp, err, gapmax))
    if not cands:
        sys.exit(f'no takes for line {i}')
    cands.sort(key=lambda c: c[0])

    def finish(y, hyp):
        # pauses: full length if there is room, less if the window is tight
        for scale in (1.0, 0.75, 0.5, 0.0):
            shaped = shape_pauses(y, hyp, S['say'], scale)
            if len(shaped) / SR <= budget:
                break
        y, factor = shaped, 1.0
        if len(y) / SR > budget:
            factor = min(1.15, (len(y) / SR) / budget + 0.005)
            y = atempo(y, factor)
        y = polish(y)
        # loudness: every line at the same integrated level
        lufs = meter.integrated_loudness(np.pad(y, (0, max(0, int(0.5 * SR) - len(y)))))
        y = y * 10 ** ((TARGET_LUFS - lufs) / 20)
        pk = np.abs(y).max()
        if pk > 0.8:                                  # soft-clip the rare peak rather than turn the line down
            y = np.tanh(y / 0.8) * 0.8 if pk < 1.1 else y * 0.8 / pk
        return y, factor, transcribe(y)

    # the best raw take that is still word-perfect after processing
    chosen = None
    for c in cands:
        y2, factor, hyp2 = finish(c[2], c[3])
        if chosen is None or (errors(expected, hyp2) == 0 and errors(expected, chosen[1][2]) > 0):
            chosen = (c, (y2, factor, hyp2))
        if errors(expected, hyp2) == 0:
            break
    (score, f, _, hyp, err, gapmax), (y, factor, hyp2) = chosen
    raw = len(chosen[0][2]) / SR
    sf.write(f'{args.out}/line_{i:02d}.wav', y, SR)
    wt = caption_word_times(L['text'], hyp2)
    d = len(y) / SR
    clips.append({'o': round(cursor, 4), 'd': round(d, 4), 'w': wt})
    audio += [y, np.zeros(int(0.3 * SR), np.float32)]
    cursor += d + 0.3
    heard = ' '.join(w[0] for w in hyp2)
    err2 = errors(expected, hyp2)
    flag = ('ERR%d ' % err if err else '') + ('POSTERR%d ' % err2 if err2 else '') + ('OVER ' if d > budget + 0.01 else '') + ('GAP%.1f ' % gapmax if gapmax > 1.0 else '')
    report.append({'i': i, 'take': os.path.basename(f), 'err': err, 'err_processed': err2, 'dur': round(d, 2), 'budget': round(budget, 2), 'tempo': factor, 'heard': heard})
    print(f'{i:2d} {os.path.basename(f):<20} err {err} raw {raw:4.2f} -> {d:4.2f}/{budget:4.2f} x{factor:.2f} {flag}| {heard}', flush=True)

sprite = np.concatenate([np.zeros(int(0.25 * SR), np.float32)] + audio)
sf.write(f'{args.out}/narration.wav', sprite, SR)
mp3 = f'{args.out}/narration.mp3'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{args.out}/narration.wav', '-ar', '24000', '-ac', '1', '-c:a', 'libmp3lame', '-q:a', '2', mp3], check=True)
b64 = base64.b64encode(open(mp3, 'rb').read()).decode()
voice = {'lead': args.lead, 'pre': args.pre, 'gain': args.gain, 'clips': clips}
with open(args.js, 'w') as fh:
    fh.write('// ============================================================================\n')
    fh.write('//  VOICE — the narration: every line, spoken, laid end to end in one MP3.\n')
    fh.write('//  Generated by film-src/voice/process_voice.py; clips[i] = { o: offset, d: duration,\n')
    fh.write('//  w: when each caption word is spoken }, all in seconds.\n')
    fh.write('// ============================================================================\n')
    meta = json.dumps(voice, separators=(',', ':'))
    fh.write(f'const VOICE = Object.assign({meta}, {{ mp3: "{b64}" }});\n')
json.dump(report, open(f'{args.out}/report.json', 'w'), indent=1)
print('mp3', os.path.getsize(mp3), 'bytes; sprite', round(len(sprite) / SR, 1), 's; js', os.path.getsize(args.js))
