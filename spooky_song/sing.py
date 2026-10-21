"""Turn speech into singing.

Every sung phrase is first spoken by Kokoro TTS, then split into syllables
(word timestamps + phoneme vowel nuclei), and resynthesized with the WORLD
vocoder: each syllable is time-warped onto its note (consonants kept crisp,
vowels stretched), and its pitch is replaced by the written melody with
glides and vibrato. Spoken lines go through the same vocoder so every
character keeps one consistent voice.

Writes build/stems/<singer>.wav, build/timeline.json and build/lipsync.npz.
"""
import hashlib
import json
import os
import re
import sys

import numpy as np
import pyworld as pw
import soundfile as sf
from scipy.signal import resample_poly

from song import BPM, CREW, FORM, SINGERS

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, 'build')
CACHE = os.path.join(BUILD, 'tts')
SR = 24000
OUT_SR = 48000
FP = 5.0                                   # WORLD frame period, ms
FPS_ = 1000.0 / FP
VOWELS = set('AIOWYQæɑɒɔəɚɛɜɪʊʌiuᵊɐaeoɘɵ')

_pipes = {}


def pipe(lang):
    if lang not in _pipes:
        from kokoro import KPipeline
        _pipes[lang] = KPipeline(lang_code=lang, repo_id='hexgrad/Kokoro-82M')
    return _pipes[lang]


def tts(voice, lang, text, speed):
    """Kokoro speech + per-token (text, phonemes, start, end); cached on disk."""
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.md5(json.dumps([voice, lang, text, round(speed, 3)]).encode()).hexdigest()[:16]
    path = os.path.join(CACHE, key)
    if os.path.exists(path + '.json'):
        audio, _ = sf.read(path + '.wav', dtype='float64')
        return audio, json.load(open(path + '.json'))
    chunks, toks, off = [], [], 0.0
    for r in pipe(lang)(text, voice=voice, speed=speed):
        a = r.audio.numpy().astype(np.float64)
        for t in r.tokens or []:
            if t.start_ts is None:
                continue
            toks.append([t.text, t.phonemes or '', off + t.start_ts, off + (t.end_ts or t.start_ts)])
        chunks.append(a)
        off += len(a) / SR
    audio = np.concatenate(chunks)
    sf.write(path + '.wav', audio, SR, subtype='FLOAT')
    json.dump(toks, open(path + '.json', 'w'))
    return audio, toks


def norm(w):
    return re.sub(r'[^a-z0-9]', '', w.lower())


def map_words(words, toks):
    """Give every word a (start, end, phonemes) from Kokoro's tokens."""
    toks = [t for t in toks if norm(t[0])]
    out, k = [], 0
    for w in words:
        target, got, s, e, ph = norm(w), '', None, None, ''
        while k < len(toks) and len(got) < len(target):
            if s is None:
                s = toks[k][2]
            got += norm(toks[k][0])
            e = toks[k][3]
            ph += toks[k][1]
            k += 1
        if s is None:
            s = e = out[-1][1] if out else 0.0
        out.append((s, e, ph))
    return out


def split_syllables(span, n):
    """Split a word's time span into n syllables using its vowel nuclei."""
    s, e, ph = span
    if n == 1 or e - s < 1e-3:
        return [(s, e)] if n == 1 else [(s + (e - s) * i / n, s + (e - s) * (i + 1) / n) for i in range(n)]
    chars = [c for c in ph if c not in 'ˈˌː']
    groups, i = [], 0
    while i < len(chars):
        if chars[i] in VOWELS:
            j = i
            while j + 1 < len(chars) and chars[j + 1] in VOWELS:
                j += 1
            groups.append((i, j))
            i = j + 1
        else:
            i += 1
    if len(groups) != n:
        return [(s + (e - s) * i / n, s + (e - s) * (i + 1) / n) for i in range(n)]
    cuts = []
    for a, b in zip(groups, groups[1:]):
        gap = b[0] - a[1] - 1                  # consonants between nuclei
        cuts.append(b[0] - (1 if gap >= 1 else 0) + (0.5 if gap == 0 else 0))
    L = len(chars)
    bounds = [s] + [s + (e - s) * c / L for c in cuts] + [e]
    return list(zip(bounds[:-1], bounds[1:]))


def parse(lyric):
    """-> list of phrases; each phrase is a list of notes (syl, midi, start_eighth, eighths)."""
    phrases, cur, pos = [], [], 0
    for tok in lyric.split():
        if tok == '|':
            phrases.append(cur)
            cur = []
            continue
        parts = tok.split('/')
        if parts[0] == '_':
            pos += int(parts[1])
            continue
        syl, midi, dur = parts[0], int(parts[1]), int(parts[2])
        cur.append(dict(syl=syl, midi=midi, e0=pos, de=dur))
        pos += dur
    if cur:
        phrases.append(cur)
    return phrases


def phrase_words(notes):
    """Group the syllables (not melisma notes) into words, keeping punctuation for display."""
    words, cur = [], []
    for i, n in enumerate(notes):
        if n['syl'] == '~':
            continue
        cur.append(i)
        if not n['syl'].endswith('-'):
            words.append(cur)
            cur = []
    if cur:
        words.append(cur)
    return words


def word_text(notes, idxs):
    return ''.join(notes[i]['syl'].rstrip('-') for i in idxs)


def tts_text(w):
    return w.lower() if w.isupper() else w


# ── WORLD helpers ────────────────────────────────────────────────────────────
def analyze(x):
    f0, t = pw.harvest(x, SR, f0_floor=60.0, f0_ceil=800.0, frame_period=FP)
    sp = pw.cheaptrick(x, f0, t, SR)
    ap = pw.d4c(x, f0, t, SR)
    return f0, sp, ap


def formant_shift(sp, ratio):
    if abs(ratio - 1) < 1e-3:
        return sp
    bins = np.arange(sp.shape[1])
    src = np.clip(bins / ratio, 0, sp.shape[1] - 1)
    i0 = np.floor(src).astype(int)
    i1 = np.minimum(i0 + 1, sp.shape[1] - 1)
    w = src - i0
    lsp = np.log(sp + 1e-20)
    return np.exp(lsp[:, i0] * (1 - w) + lsp[:, i1] * w)


def sample_frames(arr, pos, log=False):
    pos = np.clip(pos, 0, len(arr) - 1)
    i0 = np.floor(pos).astype(int)
    i1 = np.minimum(i0 + 1, len(arr) - 1)
    w = (pos - i0)[:, None]
    if log:
        la = np.log(arr + 1e-20)
        return np.exp(la[i0] * (1 - w) + la[i1] * w)
    return arr[i0] * (1 - w) + arr[i1] * w


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def sing_phrase(singer, notes, t_phrase, eighth, transpose, alpha, rng):
    """Render one phrase. Returns (audio at OUT_SR starting at t_phrase - lead, lead seconds)."""
    cfg = SINGERS[singer]
    words = phrase_words(notes)
    text = ' '.join(tts_text(word_text(notes, w)) for w in words)
    span = (notes[-1]['e0'] + notes[-1]['de'] - notes[0]['e0']) * eighth
    x, toks = tts(cfg['voice'], cfg['lang'], text, 1.0)
    nat = (toks[-1][3] - toks[0][2]) if toks else len(x) / SR
    speed = float(np.clip(nat / max(span * 0.92, 0.3), 0.62, 1.12))
    x, toks = tts(cfg['voice'], cfg['lang'], text, speed)
    f0s, sp, ap = analyze(x)
    sp = formant_shift(sp, cfg['formant'])
    voiced = f0s > 0
    med = np.median(f0s[voiced]) if voiced.any() else 150.0

    spans = map_words([word_text(notes, w) for w in words], toks)
    # source span for every syllable note
    src = {}
    for w, sp_w in zip(words, spans):
        for i, seg in zip(w, split_syllables(sp_w, len(w))):
            src[i] = seg
    # syllables with their melisma continuation notes
    sylls = []
    for i, n in enumerate(notes):
        if n['syl'] == '~':
            sylls[-1]['subs'].append(n)
        else:
            sylls.append(dict(idx=i, subs=[n], src=src[i]))

    def frame_of(t):
        return t * FPS_

    lead = 0.15
    total = span + lead + 0.6
    nfr = int(total * FPS_) + 1
    out_pos = np.full(nfr, -1.0)                 # source frame index for each output frame
    out_f0 = np.zeros(nfr)
    t0_ph = notes[0]['e0'] * eighth
    # onset/coda lengths from the voicing track
    for k, s in enumerate(sylls):
        S0, S1 = s['src']
        f_a, f_b = int(frame_of(S0)), max(int(frame_of(S1)), int(frame_of(S0)) + 1)
        v = voiced[f_a:f_b] if f_b <= len(voiced) else voiced[f_a:]
        if v.any():
            on = np.argmax(v) / FPS_
            co = (len(v) - 1 - np.argmax(v[::-1])) / FPS_
            s['onset'], s['coda'] = on, (S1 - S0) - co
        else:
            s['onset'], s['coda'] = (S1 - S0) * 0.5, 0.0
        s['T0'] = s['subs'][0]['e0'] * eighth - t0_ph + lead
        s['T1'] = (s['subs'][-1]['e0'] + s['subs'][-1]['de']) * eighth - t0_ph + lead
        s['pre'] = min(0.6 * s['onset'], 0.07)
    for k, s in enumerate(sylls):
        A = s['T0'] - s['pre']
        nxt = sylls[k + 1] if k + 1 < len(sylls) else None
        legato = nxt is not None and abs(nxt['T0'] - s['T1']) < 1e-6
        B = (nxt['T0'] - nxt['pre']) if legato else s['T1'] - 0.03
        S0, S1 = s['src']
        Ls, L = max(S1 - S0, 0.02), max(B - A, 0.02)
        o = min(s['onset'], 0.45 * Ls)
        c = min(s['coda'], 0.4 * Ls)
        fa, fb = int(np.ceil(A * FPS_)), int(np.floor(B * FPS_))
        for f in range(max(fa, 0), min(fb, nfr)):
            tau = f / FPS_ - A
            if L >= Ls:
                if tau < o:
                    ss = S0 + tau
                elif L - tau < c:
                    ss = S1 - (L - tau)
                else:
                    ss = S0 + o + (tau - o) * (Ls - o - c) / max(L - o - c, 1e-3)
            else:
                ss = S0 + tau * Ls / L
            out_pos[f] = ss * FPS_
            # melody pitch (with glide into the note and vibrato on long notes)
            tt = f / FPS_
            sub = s['subs'][0]
            for sb in s['subs']:
                if sb['e0'] * eighth - t0_ph + lead <= tt:
                    sub = sb
            ns = sub['e0'] * eighth - t0_ph + lead
            nd = sub['de'] * eighth
            m = sub['midi'] + transpose + cfg['octave']
            prev = None
            si = s['subs'].index(sub)
            if si > 0:
                prev = s['subs'][si - 1]['midi'] + transpose + cfg['octave']
            elif k > 0 and abs(sylls[k - 1]['T1'] - s['T0']) < 1e-6:
                prev = sylls[k - 1]['subs'][-1]['midi'] + transpose + cfg['octave']
            u = tt - ns
            if prev is not None and u < 0.06:
                w = max(0.0, u) / 0.06
                m = prev + (m - prev) * (w * w * (3 - 2 * w))
            if nd > 0.36 and u > 0.18:
                depth = min(1.0, (u - 0.18) / 0.25) * 0.32
                m += depth * np.sin(2 * np.pi * 5.6 * u + s['idx'])
            out_f0[f] = mtof(m)
    valid = out_pos >= 0
    pos = np.where(valid, out_pos, 0)
    f0_src = f0s[np.clip(np.round(pos).astype(int), 0, len(f0s) - 1)]
    vmask = valid & (f0_src > 0)
    # keep a little of the natural speech melody (more for half-spoken verses)
    nat = np.where(f0_src > 0, f0_src / med, 1.0)
    f0_out = np.where(vmask, out_f0 * nat ** (1 - alpha), 0.0)
    f0_out *= 2 ** (rng.normal(0, 0.004))           # each singer slightly off-centre, like a real choir
    sp_out = sample_frames(sp, pos, log=True)
    ap_out = sample_frames(ap, pos)
    sp_out[~valid] = 1e-16
    ap_out[~valid] = 1.0
    # soften entries/exits next to silence
    edges = np.convolve(valid.astype(float), np.ones(5) / 5, 'same')
    sp_out *= (edges ** 2)[:, None] + 1e-12
    y = pw.synthesize(np.ascontiguousarray(f0_out), np.ascontiguousarray(sp_out),
                      np.ascontiguousarray(ap_out), SR, FP)
    y = resample_poly(y, OUT_SR // SR, 1)
    return y, lead


def speak(singer, text, speed):
    """A spoken line in the character's voice; returns (audio, word spans)."""
    cfg = SINGERS[singer]
    x, toks = tts(cfg['voice'], cfg['lang'], text, speed)
    f0, sp, ap = analyze(x)
    sp = formant_shift(sp, cfg['formant'])
    f0 = f0 * cfg['speak_pitch']
    y = pw.synthesize(f0, np.ascontiguousarray(sp), ap, SR, FP)
    y = resample_poly(y, OUT_SR // SR, 1)
    words = text.split()
    spans = map_words(words, toks)
    # trim leading silence
    loud = np.nonzero(np.abs(y) > 0.01 * np.abs(y).max())[0]
    lead = max(0, loud[0] - int(0.03 * OUT_SR)) if len(loud) else 0
    tail = min(len(y), loud[-1] + int(0.15 * OUT_SR)) if len(loud) else len(y)
    y = y[lead:tail]
    sh = lead / OUT_SR
    return y, [(w, max(0, s - sh), max(0, e - sh)) for w, (s, e, _) in zip(words, spans)]


# ── assemble the whole song ──────────────────────────────────────────────────
def main():
    os.makedirs(os.path.join(BUILD, 'stems'), exist_ok=True)
    rng = np.random.default_rng(5)
    tl = dict(sections=[], phrases=[], talk=[], stingers=[], acts=[])
    pending = []                                   # (singer, start_time, audio, gain)
    t = 0.0
    for sec in FORM:
        bpm = sec.get('bpm', BPM)
        eighth = 60.0 / bpm / 2
        start = t
        if 'dialogue' in sec:
            t += 0.6 if sec['name'] == 'bridge' else 0.25
            for item in sec['dialogue']:
                if item[0] == 'ACT':
                    tl['acts'].append((t, item[1], item[2]))
                    t += item[2]
                    continue
                spk, text, opts = item
                y, words = speak(spk, text, opts.get('speed', 1.0))
                pending.append((spk, t, y, opts.get('gain', 1.0)))
                dur = len(y) / OUT_SR
                tl['talk'].append(dict(t0=t, t1=t + dur, spk=spk, text=text, emo=opts.get('emo'),
                                       words=[(w, t + s, t + e) for w, s, e in words]))
                for word, kind in opts.get('cues', []):
                    for w, s, e in words:
                        if norm(w).startswith(norm(word)):
                            tl['stingers'].append((t + s, kind))
                            break
                t += dur + opts.get('post', 0.4)
            t += 0.2
        elif 'seconds' in sec:
            t += sec['seconds']
        else:
            t += sec['bars'] * 8 * eighth
        tl['sections'].append(dict(name=sec['name'], t0=start, t1=t, bpm=bpm, key=sec['key'],
                                   bars=sec.get('bars')))
        for off, spk, text, opts in sec.get('talk', []):
            who = list(SINGERS) if spk == 'ALL' else [spk]
            for s in who:
                if s == 'C':
                    continue
                y, words = speak(s, text, opts.get('speed', 1.0))
                pending.append((s, start + off, y, opts.get('gain', 1.0) * (0.6 if spk == 'ALL' else 1.0)))
            tl['talk'].append(dict(t0=start + off, t1=start + off + len(y) / OUT_SR, spk=spk, text=text,
                                   words=[(w, start + off + s, start + off + e) for w, s, e in words]))
        if 'lyric' in sec:
            phrases = parse(sec['lyric'])
            for pi, notes in enumerate(phrases):
                singers = dict(sec['singers'])
                if 'join' in sec and pi >= sec.get('join_phrase', 0):
                    singers.update(sec['join'])
                p0 = start + notes[0]['e0'] * eighth
                for s, alpha in singers.items():
                    y, lead = sing_phrase(s, notes, p0, eighth, sec['key'], alpha, rng)
                    pending.append((s, p0 - lead, y, 1.0))
                words = phrase_words(notes)
                tl['phrases'].append(dict(
                    section=sec['name'], singers=sorted(singers), t0=p0,
                    t1=start + (notes[-1]['e0'] + notes[-1]['de']) * eighth,
                    words=[(word_text(notes, w), start + notes[w[0]]['e0'] * eighth,
                            start + (notes[w[-1]]['e0'] + notes[w[-1]]['de']) * eighth) for w in words],
                    notes=[(n['syl'], start + n['e0'] * eighth, start + (n['e0'] + n['de']) * eighth,
                            n['midi'] + sec['key']) for n in notes]))
                print(f"  {sec['name']} phrase {pi + 1}: {', '.join(sorted(singers))}", file=sys.stderr)
    tl['duration'] = t
    L = int((t + 1.0) * OUT_SR)
    stems = {}
    for s, t0, y, g in pending:
        st = stems.setdefault(s, np.zeros(L))
        y = y / (np.sqrt(np.mean(y[np.abs(y) > 0.02 * np.abs(y).max()] ** 2)) + 1e-9) * 0.1 * g
        i0 = int(t0 * OUT_SR)
        n = min(len(y), L - i0)
        st[i0:i0 + n] += y[:n]
    for s, st in stems.items():
        sf.write(os.path.join(BUILD, 'stems', f'{s}.wav'), st.astype(np.float32), OUT_SR, subtype='FLOAT')
    # lip / jaw movement per character (the crew share one jaw track)
    rate = 100
    hop = OUT_SR // rate
    lips = {}
    groups = {'M': ['M'], 'A': ['A'], 'S': ['S'], 'C': ['C'], 'K': CREW}
    for g, members in groups.items():
        sig = sum((stems[m] for m in members if m in stems), np.zeros(L))
        frames = len(sig) // hop
        rms = np.sqrt((sig[:frames * hop].reshape(frames, hop) ** 2).mean(axis=1))
        ref = np.percentile(rms[rms > 0.004], 90) if (rms > 0.004).any() else 1.0
        o = np.clip(rms / ref, 0, 1.2)
        lips[g] = np.where(o < 0.08, 0, o) ** 0.7
    np.savez(os.path.join(BUILD, 'lipsync.npz'), rate=rate, **lips)
    json.dump(tl, open(os.path.join(BUILD, 'timeline.json'), 'w'), indent=1)
    print(f'song {t:.1f}s, {len(tl["phrases"])} phrases, {len(tl["talk"])} spoken lines')


if __name__ == '__main__':
    main()
