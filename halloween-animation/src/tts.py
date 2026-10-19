"""Synthesize every line with Kokoro, pitch-shift per character, and measure
sentence timings, marked-word cue times and lip-sync envelopes."""
import json, os, re, subprocess, sys
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, 'work')
VOX = os.path.join(WORK, 'vox')
os.makedirs(VOX, exist_ok=True)

SR = 24000
ENV_HZ = 48

k = Kokoro(os.path.join(HERE, 'models/kokoro-v1.0.onnx'), os.path.join(HERE, 'models/voices-v1.0.bin'))

MARK = re.compile(r'(^|(?<=[\s"(]))([\^_~])(?=\w)')


def parse(text):
    """Return clean text and list of (word, kind, char_index_in_clean)."""
    cues, out, i = [], [], 0
    kinds = {'^': 'hi', '_': 'lo', '~': 'mark'}
    while i < len(text):
        ch = text[i]
        if ch in kinds and (i == 0 or not text[i - 1].isalnum()) and i + 1 < len(text) and text[i + 1].isalnum():
            m = re.match(r"[\w']+", text[i + 1:])
            cues.append((m.group(0).strip("'"), kinds[ch], len(''.join(out))))
            i += 1
            continue
        out.append(ch)
        i += 1
    return ''.join(out), cues


def speakable(s):
    # all-caps emphasis words are read as words, not spelled out
    return re.sub(r"\b([A-Z]{2,})\b", lambda m: m.group(1).capitalize(), s)


def split_sentences(s):
    parts = re.split(r'(?<=[.?!])\s+(?=[A-Z"\'])', s.strip())
    spans, pos = [], 0
    for p in parts:
        st = s.index(p, pos)
        spans.append((st, st + len(p)))
        pos = st + len(p)
    return spans


def synth(text, voice, speed):
    a, sr = k.create(speakable(text), voice=voice, speed=speed, lang='en-us')
    assert sr == SR
    return a.astype(np.float32)


def pause_after(sent):
    s = sent.rstrip()
    if s.endswith('...'):
        return 0.5
    if s.endswith('?'):
        return 0.38
    if s.endswith('!'):
        return 0.28
    return 0.34


def trailing_pause(prefix):
    p = prefix.rstrip()
    if p.endswith('...'):
        return 0.42
    if p.endswith((',', ';', ':', '—')):
        return 0.12
    if p.endswith(('.', '?', '!')):
        return 0.3
    return 0.03


def pitch_shift(a, semis):
    if abs(semis) < 0.05:
        return a
    src = os.path.join(VOX, '_tmp_in.wav')
    dst = os.path.join(VOX, '_tmp_out.wav')
    sf.write(src, a, SR)
    ratio = 2 ** (semis / 12)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-af',
                    f'rubberband=pitch={ratio:.5f}:formant=shifted:pitchq=quality:transients=smooth:window=long',
                    dst], check=True)
    b, _ = sf.read(dst, dtype='float32')
    return b[:len(a)] if len(b) >= len(a) else np.pad(b, (0, len(a) - len(b)))


def envelopes(a):
    hop = SR // ENV_HZ
    win = SR // 24
    n = int(np.ceil(len(a) / hop)) + 1
    rms, cent = [], []
    pad = np.pad(a, (win, win))
    freqs = np.fft.rfftfreq(win, 1 / SR)
    w = np.hanning(win)
    for i in range(n):
        c = i * hop + win
        seg = pad[c - win // 2: c + win // 2]
        if len(seg) < win:
            seg = np.pad(seg, (0, win - len(seg)))
        r = float(np.sqrt(np.mean(seg ** 2)) + 1e-9)
        rms.append(r)
        spec = np.abs(np.fft.rfft(seg * w))
        band = (freqs > 200) & (freqs < 5000)
        cs = float((spec[band] * freqs[band]).sum() / (spec[band].sum() + 1e-9))
        cent.append(cs)
    rms = np.array(rms)
    db = 20 * np.log10(rms + 1e-9)
    ref = np.percentile(db[db > -60], 95) if np.any(db > -60) else -20
    openv = np.clip((db - (ref - 30)) / 28, 0, 1)
    cent = np.array(cent)
    cn = np.clip((cent - 900) / 1800, 0, 1)
    return [round(float(x), 3) for x in openv], [round(float(x), 3) for x in cn]


def main():
    lines = json.load(open(os.path.join(WORK, 'lines_in.json')))
    only = set(int(x) for x in sys.argv[1:]) if len(sys.argv) > 1 else None
    out_path = os.path.join(WORK, 'lines_out.json')
    prev = {d['idx']: d for d in json.load(open(out_path))} if os.path.exists(out_path) else {}
    results = []
    for ln in lines:
        if only is not None and ln['idx'] not in only and ln['idx'] in prev:
            results.append(prev[ln['idx']])
            continue
        clean, cues = parse(ln['text'])
        spans = split_sentences(clean)
        chunks, sents, t = [], [], 0.0
        for si, (a0, a1) in enumerate(spans):
            stext = clean[a0:a1]
            audio = synth(stext, ln['voice'], ln['speed'])
            dur = len(audio) / SR
            sents.append({'text': stext, 'start': round(t, 3), 'end': round(t + dur, 3), 'a0': a0, 'a1': a1})
            chunks.append(audio)
            t += dur
            if si < len(spans) - 1:
                p = pause_after(stext)
                chunks.append(np.zeros(int(p * SR), np.float32))
                t += p
        audio = np.concatenate(chunks)
        cue_out = []
        for word, kind, ci in cues:
            s = next(s for s in sents if s['a0'] <= ci < s['a1'] + 1)
            prefix = clean[s['a0']:ci]
            if prefix.strip():
                d = len(synth(prefix.strip(), ln['voice'], ln['speed'])) / SR + trailing_pause(prefix)
                m = re.match(r"[\w']+[.,!?]*", clean[ci:])
                d_end = len(synth((prefix + m.group(0)).strip(), ln['voice'], ln['speed'])) / SR
                if d > d_end - 0.12:
                    d = max(0.0, d_end - 0.22)
            else:
                d = 0.0
            cue_out.append({'word': word, 'kind': kind, 't': round(s['start'] + d, 3)})
        audio = pitch_shift(audio, ln['pitch'])
        peak = np.max(np.abs(audio)) + 1e-9
        audio = audio / peak * 0.9
        wav = os.path.join(VOX, f"line_{ln['idx']:03d}.wav")
        sf.write(wav, audio, SR)
        env, cent = envelopes(audio)
        for s in sents:
            s.pop('a0'); s.pop('a1')
        res = {'idx': ln['idx'], 'who': ln['who'], 'wav': wav, 'dur': round(len(audio) / SR, 3),
               'sentences': sents, 'cues': cue_out, 'env': env, 'cent': cent}
        results.append(res)
        print(f"[{ln['idx']:2d}] {ln['who']:7s} {res['dur']:5.2f}s  cues={[(c['word'], c['t']) for c in cue_out]}", flush=True)
    json.dump(results, open(out_path, 'w'))
    print('total speech', round(sum(r['dur'] for r in results), 1), 's')


if __name__ == '__main__':
    main()
