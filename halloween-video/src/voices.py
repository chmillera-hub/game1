"""Synthesize every line with Piper, post-process per character, cache to disk."""
import hashlib, io, json, os, subprocess, sys, wave
import numpy as np
from piper import PiperVoice, SynthesisConfig

HERE = os.path.dirname(os.path.abspath(__file__))
VDIR = os.path.join(HERE, '..', 'voices')
CACHE = os.path.join(HERE, 'cache_voice')
SR = 44100

# model, speaker, length_scale, pitch factor, keep-chipmunk (0..1), gain, noise, noise_w
CAST = {
    'N':       ('en_GB-alan-medium', None, 1.10, 0.97, 0.0, 1.0, 0.62, 0.75),
    'IRIS':    ('en_US-libritts_r-medium', 345, 1.10, 0.95, 0.0, 1.05, 0.70, 0.85),
    'BEE':     ('en_US-lessac-medium', None, 0.95, 1.38, 0.55, 0.95, 0.75, 0.9),
    'CLAWD':   ('en_US-libritts_r-medium', 805, 1.05, 0.90, 0.0, 1.1, 0.66, 0.8),
    'CLAWDIA': ('en_US-libritts_r-medium', 23, 1.06, 1.02, 0.0, 1.0, 0.72, 0.85),
    'GOSTE':   ('en_US-amy-medium', None, 1.02, 1.17, 0.25, 1.0, 0.72, 0.9),
}

_models = {}


def model(name):
    if name not in _models:
        _models[name] = PiperVoice.load(os.path.join(VDIR, name + '.onnx'))
    return _models[name]


def raw_synth(sp, text, speed):
    mname, sid, ls, *_ , ns, nw = CAST[sp]
    v = model(mname)
    cfg = SynthesisConfig(speaker_id=sid, length_scale=ls * speed, noise_scale=ns, noise_w_scale=nw)
    b = io.BytesIO()
    with wave.open(b, 'wb') as w:
        v.synthesize_wav(text, w, syn_config=cfg)
    return b.getvalue()


def process(sp, wavbytes, pitch, whisper):
    _, _, _, p0, chip, gain, *_ = CAST[sp]
    p = p0 * pitch
    # pitch shift: asetrate by p, then restore part of the duration
    tempo = 1.0 / (p ** (1 - chip))
    tempo = min(max(tempo, 0.5), 2.0)
    filt = [f'asetrate=22050*{p:.4f}', f'aresample={SR}', f'atempo={tempo:.4f}',
            'highpass=f=70', 'equalizer=f=3000:t=q:w=1:g=2']
    if whisper:
        filt += ['highpass=f=180', 'volume=0.8']
    if sp == 'N':
        filt += ['bass=g=3:f=120', 'equalizer=f=250:t=q:w=1:g=1.5']
    if sp == 'CLAWD':
        filt += ['bass=g=4:f=110']
    out = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'wav', '-i', 'pipe:0', '-af', ','.join(filt),
                          '-ac', '1', '-f', 'f32le', 'pipe:1'], input=wavbytes, capture_output=True, check=True).stdout
    a = np.frombuffer(out, np.float32).copy()
    # trim silence
    env = np.abs(a)
    thr = 0.02 * env.max()
    idx = np.where(env > thr)[0]
    if len(idx):
        a = a[max(0, idx[0] - int(0.03 * SR)): idx[-1] + int(0.08 * SR)]
    a = a / (np.abs(a).max() + 1e-9) * 0.8 * gain
    return a


def speakable(text):
    import re
    return re.sub(r"\b([A-Z]{2,})\b", lambda m: m.group(1).lower(), text)


def render_line(sp, text, speed, pitch, whisper):
    # "..." becomes a real, held pause between separately spoken chunks
    parts = [p.strip() for p in speakable(text).split('...')]
    out = []
    for i, p in enumerate(parts):
        if not p or not any(c.isalnum() for c in p):
            continue
        if out:
            out.append(np.zeros(int(SR * (0.42 if sp != 'BEE' else 0.3)), np.float32))
        out.append(process(sp, raw_synth(sp, p, speed), pitch, whisper))
    a = np.concatenate(out)
    return a / (np.abs(a).max() + 1e-9) * 0.8 * CAST[sp][5]


def h(s):
    return hashlib.md5(s.encode()).hexdigest()[:16]


def main():
    sys.path.insert(0, HERE)
    from timeline import TL
    from story import build
    os.makedirs(CACHE, exist_ok=True)
    tl = TL()
    build(tl)
    durs, onsets = {}, {}
    for ln in tl.lines:
        key = ln['key']
        fn = os.path.join(CACHE, h(key + str(ln['whisper'])) + '.npy')
        if not os.path.exists(fn):
            a = render_line(ln['sp'], ln['text'], ln['speed'], ln['pitch'], ln['whisper'])
            np.save(fn, a)
        a = np.load(fn)
        durs[key] = len(a) / SR
        for w in ln['hi'] + ln['lo']:
            i = ln['text'].lower().find(w.lower())
            pre = ln['text'][:i].strip()
            if i <= 0 or len(pre) < 2:
                onsets[key + '§' + w] = 0.05
                continue
            fn2 = os.path.join(CACHE, h('PRE' + key + w) + '.npy')
            if not os.path.exists(fn2):
                np.save(fn2, render_line(ln['sp'], pre, ln['speed'], ln['pitch'], ln['whisper']))
            b = np.load(fn2)
            onsets[key + '§' + w] = len(b) / SR - 0.02
        print(f"{ln['sp']:8s} {durs[key]:5.2f}s  {ln['text'][:60]}")
    json.dump(dict(durs=durs, onsets=onsets), open(os.path.join(HERE, 'voice_meta.json'), 'w'))
    print('total speech', sum(durs.values()))


if __name__ == '__main__':
    main()
