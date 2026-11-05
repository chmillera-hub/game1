"""Synthesize all dialogue, build timeline.json + voice track (48k mono float npy)."""
import re, io, os, json, wave, hashlib
import numpy as np
from piper import PiperVoice, SynthesisConfig
from screenplay import SCENES, VOICES, CHORUS

SR = 48000
FPS = 24
VDIR = os.environ.get('PIPER_VOICES', os.path.join(os.path.dirname(__file__), '..', 'voices'))
CACHE = os.path.join(os.path.dirname(__file__), 'cache')
os.makedirs(CACHE, exist_ok=True)
_models = {}

def model(name):
    if name not in _models:
        _models[name] = PiperVoice.load(os.path.join(VDIR, name + '.onnx'))
    return _models[name]

def synth(name, sid, text, ls):
    key = hashlib.md5(f'{name}|{sid}|{text}|{ls}'.encode()).hexdigest()
    p = os.path.join(CACHE, key + '.npy')
    if os.path.exists(p):
        return np.load(p)
    v = model(name)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        v.synthesize_wav(text, wf, syn_config=SynthesisConfig(speaker_id=sid, length_scale=ls, noise_scale=0.6, noise_w_scale=0.75))
    buf.seek(0)
    wf = wave.open(buf)
    sr = wf.getframerate()
    x = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768
    # resample to SR
    n = int(len(x) * SR / sr)
    y = np.interp(np.arange(n) * sr / SR, np.arange(len(x)), x).astype(np.float32)
    np.save(p, y)
    return y

def trim(x, thr=0.012):
    a = np.abs(x)
    idx = np.where(a > thr)[0]
    if len(idx) == 0:
        return x
    s = max(0, idx[0] - int(0.02 * SR)); e = min(len(x), idx[-1] + int(0.06 * SR))
    return x[s:e]

def stretch_rate(x, rate):
    """change playback rate (pitch & speed) by rate."""
    n = int(len(x) / rate)
    return np.interp(np.arange(n) * rate, np.arange(len(x)), x).astype(np.float32)

def fit_len(x, n):
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)

def reverb(x, t60, wet, seed=1):
    rng = np.random.default_rng(seed)
    n = int(t60 * SR)
    ir = rng.standard_normal(n).astype(np.float32) * np.exp(-6.9 * np.arange(n) / n).astype(np.float32)
    # darken IR
    ir = np.convolve(ir, np.ones(8) / 8, 'same')
    ir[:int(0.012 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum()) + 1e-9
    L = len(x) + n
    nf = 1 << int(np.ceil(np.log2(L)))
    y = np.fft.irfft(np.fft.rfft(x, nf) * np.fft.rfft(ir, nf), nf)[:L].astype(np.float32)
    out = np.zeros(L, np.float32); out[:len(x)] = x
    return out + y * wet

FX = {'vo': (0.0, 0.0), 'room': (0.35, 0.10), 'hall': (1.3, 0.22), 'cave': (2.2, 0.35),
      'open': (0.6, 0.08), 'whisper': (0.9, 0.18)}

def clean(t):
    return t.replace('^', '').replace('~', '')

def sentences(t):
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z\'"])', t.strip())
    return [p for p in parts if p]

def chunk_sentence(s, maxc=44):
    words = s.split(' ')
    if len(s) <= maxc:
        return [s]
    nchunks = int(np.ceil(len(s) / maxc))
    target = len(s) / nchunks
    chunks, cur = [], ''
    for w in words:
        if cur and (len(cur) + 1 + len(w) > target * 1.15 or (len(cur) >= target * 0.6 and cur[-1] in ',;:')):
            chunks.append(cur); cur = w
        else:
            cur = (cur + ' ' + w).strip()
    if cur:
        chunks.append(cur)
    if len(chunks) >= 2 and len(chunks[-1]) < 16:
        last = chunks.pop(); chunks[-1] = chunks[-1] + ' ' + last
    return chunks

def line_audio(spk, text):
    name, sid, ls, pitch, fx = VOICES[spk]
    sents = sentences(text)
    pieces, sinfo = [], []
    t = 0.0
    for i, s in enumerate(sents):
        c = clean(s)
        if name == 'CHORUS':
            # rhythmic chorus: split at '...' into phrases, align all voices
            phrases = [p.strip() for p in c.split('...') if p.strip()]
            seg = []
            for ph in phrases:
                vs = [trim(synth(n, i_d, ph, ls)) for n, i_d in CHORUS]
                L = int(np.median([len(v) for v in vs]) * 1.05)
                mix = np.zeros(L + 2000, np.float32)
                for k, v in enumerate(vs):
                    off = (k * 137) % 900
                    mix[off:off + L] += fit_len(v, L) * (0.42 if k < 2 else 0.33)
                seg.append(mix); seg.append(np.zeros(int(0.28 * SR), np.float32))
            a = np.concatenate(seg[:-1])
        else:
            a = trim(synth(name, sid, c, ls * pitch))
            if pitch != 1.0:
                a = stretch_rate(a, pitch)
        dur = len(a) / SR
        sinfo.append((s, t, t + dur))
        pieces.append(a)
        gap = 0.42 if s.rstrip().endswith('...') else 0.26
        if i < len(sents) - 1:
            pieces.append(np.zeros(int(gap * SR), np.float32))
            t += dur + gap
        else:
            t += dur
    dry = np.concatenate(pieces)
    peak = np.percentile(np.abs(dry), 99.5) + 1e-6
    dry = dry * (0.55 / peak)
    if spk == 'SOLOMON_CHILD':
        dry *= 0.75
    return dry, sinfo, fx

def envelopes(x, start_t):
    """per-frame mouth openness & brightness, frames aligned to global timeline."""
    hop = SR // FPS
    f0 = int(round(start_t * FPS))
    off = int(round((f0 / FPS - start_t) * SR))
    env, bright = [], []
    nfr = int(np.ceil((len(x) / SR) * FPS)) + 2
    for k in range(nfr):
        s = off + k * hop
        w = x[max(0, s - hop // 2):max(0, s + hop // 2 + hop // 2)]
        if len(w) < 64:
            env.append(0); bright.append(0); continue
        r = float(np.sqrt((w ** 2).mean()))
        sp = np.abs(np.fft.rfft(w * np.hanning(len(w))))
        fr = np.fft.rfftfreq(len(w), 1 / SR)
        c = float((sp * fr).sum() / (sp.sum() + 1e-9))
        env.append(r); bright.append(c)
    env = np.array(env); bright = np.array(bright)
    env = np.clip(env / (np.percentile(env, 95) + 1e-6), 0, 1.2)
    env = np.where(env < 0.12, 0, env)
    b = np.clip((bright - 900) / 2200, 0, 1)
    return f0, [round(float(v), 3) for v in env], [round(float(v), 3) for v in b]

def main():
    tl = {'fps': FPS, 'scenes': [], 'accents': [], 'sfx': []}
    t = 0.0
    track = np.zeros(int(SR * 900), np.float32)
    for sc in SCENES:
        scene = {'id': sc['id'], 'mood': sc['mood'], 'start': round(t, 3), 'lines': []}
        cur = t + sc['lead']
        for li, (spk, text, gap) in enumerate(sc['lines']):
            if li > 0:
                cur += gap
            dry, sinfo, fx = line_audio(spk, text)
            t60, wet = FX[fx]
            wetx = reverb(dry, t60, wet, seed=li + 7) if wet > 0 else dry
            s0 = int(cur * SR)
            track[s0:s0 + len(wetx)] += wetx
            dur = len(dry) / SR
            f0, env, br = envelopes(dry, cur)
            chunks = []
            for (s, a, b) in sinfo:
                cs = chunk_sentence(clean(s))
                tot = sum(len(c) for c in cs)
                acc = a
                for c in cs:
                    d = (b - a) * len(c) / tot
                    chunks.append({'text': c, 'start': round(cur + acc, 3), 'end': round(cur + acc + d, 3)})
                    acc += d
                # accents
                raw = s
                for m in re.finditer(r'([\^~])(\w+)', raw):
                    pos = len(clean(raw[:m.start()]))
                    frac = (pos + len(m.group(2)) * 0.3) / max(1, len(clean(raw)))
                    tl['accents'].append({'t': round(cur + a + (b - a) * frac, 3),
                                          'kind': 'hi' if m.group(1) == '^' else 'lo', 'word': m.group(2)})
            scene['lines'].append({'spk': spk, 'text': clean(text), 'start': round(cur, 3), 'end': round(cur + dur, 3),
                                   'f0': f0, 'env': env, 'br': br, 'chunks': chunks})
            cur += dur
        cur += sc['tail']
        scene['end'] = round(cur, 3)
        tl['scenes'].append(scene)
        t = cur
    tl['duration'] = round(t, 3)
    track = track[:int((t + 0.5) * SR)]
    np.save(os.path.join(os.path.dirname(__file__), 'voice.npy'), track)
    with open(os.path.join(os.path.dirname(__file__), 'timeline.json'), 'w') as f:
        json.dump(tl, f)
    print('duration', t)
    for s in tl['scenes']:
        print(s['id'], s['start'], s['end'], round(s['end'] - s['start'], 1))

if __name__ == '__main__':
    main()
