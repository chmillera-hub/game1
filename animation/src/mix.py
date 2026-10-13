"""Brindle Cross -- the film's audio mixer.

    python3 mix.py TIMELINE_JSON VOICES_DIR OUT_WAV

Reads the audio, music and sfx entries of timeline.json and writes a 48 kHz stereo float32
WAV of exactly round(duration * 48000) samples:

* voice lines  24 kHz mono clips (VOICES_DIR/<id>.wav, lines.json for the hushed flag),
               resampled to 48 kHz, entry gain, centred. The on-screen characters (O, E, T,
               K) get a faint street ambience -- early reflections and a small slap off the
               bakery's brick wall, about -20 dB wet. The narrator (N) stays dry, close and
               warm (90 Hz high-pass, a little low shelf); hushed lines are dry as well
               ("mix close and dry" in the screenplay).
* music        music_lib.render_cue per entry, entry gain. params.cut stops the cue dead at
               t+dur with a 12 ms anti-click fade. Other cues ring out naturally, unless more
               than 0.3 s of them would run under the next cue's start -- then they fade over
               0.4 s there. Only a quiet ring-out (no notes after the next cue starts and
               already 12 dB under the cue's level) counts as an intended overlap and is kept.
* sfx          sfx_lib.sfx per entry, placed so the transient (`sync`) lands on t, entry
               gain. The timeline gains are trims on the library's normalised files (they
               already land near the library's targets), so mix_gain_db is only logged, never
               added on top. Repeated effects get different seeds. Laughs are panned slightly
               (seeded); everything else stays where the library put it, near centre.
               Unknown effect names and rejected params take a logged fallback.
* ducking      music and the wind bed duck 7 dB under every voice line (80 ms attack ahead
               of the line, 350 ms release), computed from the line spans. Other sfx are not
               ducked.
* balance      every line must sit >= 10 dB above everything else (RMS over its span). A line
               that does not gets a deeper duck, then a local dip of the sfx under it; the
               voice itself is never raised.
* master       -16 LUFS integrated, true peak <= -1.5 dBTP: linear gain plus a 4x-oversampled
               look-ahead limiter for the peaks that need it, measured with ffmpeg's loudnorm
               analysis before and after.

Renders are cached in <dir of OUT_WAV>/cache; a JSON report is written next to OUT_WAV.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import zlib

import numpy as np
import soundfile as sf
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import music_lib  # noqa: E402
import sfx_lib  # noqa: E402

SR = 48000

NARRATOR_EQ = [('hp', 90), ('ls', 220, 1.5), ('hs', 8500, -1.0)]
CHARACTER_EQ = [('hp', 70)]
STREET_WET_DB = -20.0
# (delay s, gain, pan): pavement, the bakery's brick wall right behind them, shop fronts,
# then the small slap off the facades across the square
STREET_ER = [(0.007, 0.50, -0.4), (0.012, 0.42, 0.45), (0.019, 0.33, -0.2), (0.027, 0.26, 0.6),
             (0.041, 0.18, -0.55), (0.071, 0.30, 0.15), (0.117, 0.12, -0.3)]

CUT_FADE = 0.012          # anti-click fade of a dead music stop
LIB_CUT_FADE = 0.030      # music_lib's own fade at a cut
OVERLAP_OK = 0.3          # a cue may run this far under the next one
XFADE = 0.4               # ... beyond that it fades out over this long
RING_SLACK = 0.25         # after the last musical event, only the ring-out is left
QUIET_TAIL = 12.0         # a ring-out this far under the cue's RMS may overlap the next cue
END_FADE = 0.3            # anything still sounding at the film's last sample

DUCK_DB = 7.0
DUCK_ATTACK = 0.08
DUCK_RELEASE = 0.35
DUCKED_SFX = ('wind',)
MIN_SPEECH_TO_BED = 10.0
FIX_MARGIN = 0.5
MAX_EXTRA_DUCK = 12.0
MAX_SFX_DIP = 18.0

# max |pan| per laugh; the crowd is spread wider than Edith's and Teddy's own laughs
LAUGH_PAN = {'crowd_laugh': 0.35, 'child_giggle': 0.2, 'laugh_old_woman': 0.1,
             'huff_laugh': 0.1, 'nasal_laugh': 0.1}
# stand-ins for effect names the library does not have: name -> (stand-in, param renames)
SFX_FALLBACKS = {
    'footsteps': ('footsteps_cobble', {}),
    'cane_tap': ('cane_click', {}),
    'bell': ('shop_bell', {}),
    'tick': ('tower_tick', {}),
    'laugh': ('crowd_laugh', {}),
}

TARGET_LUFS = -16.0
TP_CEIL_DB = -1.5
TP_MARGIN_DB = 0.3        # our oversampled peak reading vs ffmpeg's
LIMIT_LOOK = 0.005
LIMIT_HOLD = 0.061

WARNINGS = []


def db(x):
    return 10.0 ** (x / 20.0)


def to_db(p):
    """Power -> dB."""
    return 10.0 * np.log10(max(float(p), 1e-20))


def log(msg):
    print(msg, flush=True)


def warn(msg):
    WARNINGS.append(msg)
    print('WARNING: ' + msg, flush=True)


def fade_curve(n, out=True):
    """Raised-cosine fade of n samples (1 -> 0 when out)."""
    u = (np.arange(n) + 1.0) / max(n, 1)
    w = 0.5 + 0.5 * np.cos(np.pi * u)
    return w if out else w[::-1]


def place(dst, src, i0, gain=1.0):
    """Add src (stereo) into dst at sample i0, clipped to dst. A source that would run past
    the end gets an END_FADE fade ending on the last sample. Returns (a, b, faded)."""
    if i0 < 0:
        src = src[-i0:]
        i0 = 0
    n = min(len(src), len(dst) - i0)
    if n <= 0:
        return i0, i0, False
    s = src[:n] * gain
    faded = len(src) > n and np.max(np.abs(src[n:])) > 1e-5
    if faded:
        k = min(n, int(END_FADE * SR))
        s[n - k:] *= fade_curve(k)[:, None]
    dst[i0:i0 + n] += s
    return i0, i0 + n, faded


def stereo(x):
    return np.stack([x, x], axis=1) if x.ndim == 1 else x


def balance_pan(x, p):
    """Constant-power balance of a stereo signal, p in [-1, 1] (0 = unchanged)."""
    a = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return x * (np.array([np.cos(a), np.sin(a)]) * np.sqrt(2.0))[None, :]


def lib_crc(module):
    with open(module.__file__, 'rb') as fh:
        return '%08x' % zlib.crc32(fh.read())


def cache_key(*parts):
    return hashlib.sha1(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:12]


def read_wav(path):
    y, sr = sf.read(path, dtype='float64', always_2d=True)
    assert sr == SR, (path, sr)
    return stereo(y[:, 0]) if y.shape[1] == 1 else y


# ----------------------------------------------------------------------------- voices


def street_ir():
    """Stereo IR of the faint street ambience: early reflections, the slap and a short dark
    tail. The caller scales the wet signal against the dry line (STREET_WET_DB)."""
    rng = np.random.default_rng(11)
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    ir = np.zeros((n, 2))
    for d, g, p in STREET_ER:
        a = (p + 1) * np.pi / 4
        i = int(round(d * SR))
        ir[i] += g * np.array([np.cos(a), np.sin(a)]) * np.sqrt(2.0)
    tail = rng.standard_normal((n, 2)) * (np.exp(-6.91 * t / 0.45) * (1 - np.exp(-t / 0.02)))[:, None]
    tail[:int(0.015 * SR)] = 0.0
    ir += 0.35 * tail / np.sqrt(np.sum(tail ** 2, axis=0))
    return signal.sosfilt(signal.butter(2, [180, 4500], 'bandpass', fs=SR, output='sos'), ir, axis=0)


def load_line(voices_dir, lid):
    y, sr = sf.read(os.path.join(voices_dir, lid + '.wav'), dtype='float64', always_2d=True)
    y = y.mean(axis=1)
    if sr != SR:
        g = np.gcd(SR, sr)
        y = signal.resample_poly(y, SR // g, sr // g)
    return y


def build_voices(tl, voices_dir, N):
    meta_path = os.path.join(voices_dir, 'lines.json')
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    ir = street_ir()
    V = np.zeros((N, 2))
    lines = []
    for e in sorted((e for e in tl['audio'] if e.get('kind', 'line') == 'line'), key=lambda e: e['t']):
        lid, spk = e['id'], e.get('speaker') or meta.get(e['id'], {}).get('speaker', 'N')
        hushed = bool(meta.get(lid, {}).get('hushed', False))
        x = load_line(voices_dir, lid)
        if spk == 'N':
            y, how = stereo(music_lib.apply_eq(x, NARRATOR_EQ)), 'narrator: dry, hp90 + warmth'
        elif hushed:
            y, how = stereo(music_lib.apply_eq(x, CHARACTER_EQ)), 'hushed: close and dry'
        else:
            x = music_lib.apply_eq(x, CHARACTER_EQ)
            wet = np.stack([signal.fftconvolve(x, ir[:, c]) for c in range(2)], axis=1)
            y = wet * (db(STREET_WET_DB) * np.sqrt(np.mean(x ** 2) / np.mean(wet ** 2)))
            y[:len(x)] += x[:, None]
            how = 'street ambience %+.0f dB wet' % STREET_WET_DB
        i0 = int(round(e['t'] * SR))
        a, b, _ = place(V, y, i0, db(e.get('gain', 0.0)))
        dur = float(e.get('dur', len(x) / SR))
        lines.append(dict(id=lid, speaker=spk, t=e['t'], dur=dur, gain=e.get('gain', 0.0), hushed=hushed,
                          a=i0, b=min(N, i0 + int(round(dur * SR)))))
        log('  voice %-4s %s t=%7.3f dur=%5.2f gain %+5.1f dB  %s' % (lid, spk, e['t'], dur, e.get('gain', 0.0), how))
    return V, lines


# ----------------------------------------------------------------------------- music


def render_music(e, cache):
    """Render (or reuse) one music entry. Returns (audio, info, n_keep, cut)."""
    p = dict(e.get('params') or {})
    dur = float(e['dur'])
    cut = bool(p.get('cut', False))
    # music_lib stops a cut cue with a 30 ms fade ending at `duration`; render it 18 ms
    # long so our own 12 ms fade at t+dur is what actually stops it
    rdur = dur + (LIB_CUT_FADE - CUT_FADE if cut else 0.0)
    key = cache_key(e['name'], round(rdur, 6), p, lib_crc(music_lib))
    wav = os.path.join(cache, 'music_%s_%s.wav' % (e['name'], key))
    meta = wav[:-4] + '.json'
    if os.path.exists(wav) and os.path.exists(meta):
        info = json.load(open(meta))
    else:
        info = music_lib.render_cue(e['name'], wav, rdur, **p)
        json.dump(info, open(meta, 'w'))
    return read_wav(wav), info, int(round(dur * SR)), cut


def musical_end(info):
    """Time (s, in the cue) of its last beat / marker: after it only the ring-out is left."""
    ts = list(info.get('events', [])) + list(info.get('downbeats', []))
    for k, v in (info.get('markers') or {}).items():
        if k == 'stop':
            continue
        ts += [x for x in (v if isinstance(v, list) else [v]) if isinstance(x, (int, float))]
    return max(ts) if ts else info['duration']


def build_music(tl, N, cache):
    M = np.zeros((N, 2))
    entries = sorted(tl['music'], key=lambda e: e['t'])
    report = []
    for k, e in enumerate(entries):
        y, info, n_keep, cut = render_music(e, cache)
        t0, dur = float(e['t']), float(e['dur'])
        nxt = next((m for m in entries[k + 1:] if m['t'] > t0 + 1e-6), None)
        note = ''
        if cut:
            y = y[:n_keep].copy()
            nf = int(CUT_FADE * SR)
            y[-nf:] *= fade_curve(nf)[:, None]
            note = 'cut dead at %.3f s (%.0f ms fade)' % (t0 + dur, CUT_FADE * 1000)
        elif nxt is not None and t0 + dur - nxt['t'] > OVERLAP_OK:
            over = t0 + dur - nxt['t']
            m_end = t0 + musical_end(info)
            i_next = int(round((nxt['t'] - t0) * SR))
            tail_db = to_db(np.mean(y[i_next:i_next + int(0.25 * SR)] ** 2)) - info['rms_db']
            what = 'last note at %.2f s, overlap starts %.1f dB under the cue' % (m_end, tail_db)
            if nxt['t'] >= m_end + RING_SLACK and tail_db < -QUIET_TAIL:
                note = 'rings %.2f s under %s (%s): quiet ring-out, kept' % (over, nxt['name'], what)
            else:
                f1 = nxt['t'] + OVERLAP_OK - t0
                n1, nf = int(round(f1 * SR)), int(round(XFADE * SR))
                y = y[:n1].copy()
                y[n1 - nf:] *= fade_curve(nf)[:, None]
                note = 'would run %.2f s under %s (%s): %.1f s fade %.2f-%.2f s' % (
                    over, nxt['name'], what, XFADE, t0 + f1 - XFADE, t0 + f1)
        a, b, faded = place(M, y, int(round(t0 * SR)), db(e.get('gain', 0.0)))
        if faded:
            note += ('; ' if note else '') + 'runs past the film end: %.1f s end fade' % END_FADE
        log('  music %-11s t=%7.3f dur=%6.2f gain %+5.1f dB  %.2f-%.2f s  %s' % (
            e['name'], t0, dur, e.get('gain', 0.0), a / SR, b / SR, note or 'plays out naturally'))
        report.append(dict(name=e['name'], t=t0, dur=dur, gain=e.get('gain', 0.0), start=a / SR, end=b / SR,
                           note=note, peak_db=info.get('peak_db'), rms_db=info.get('rms_db')))
    return M, report


# ----------------------------------------------------------------------------- sfx


def render_sfx(name, duration, seed, params, cache):
    key = cache_key(name, duration, seed, params, lib_crc(sfx_lib))
    wav = os.path.join(cache, 'sfx_%s_%s.wav' % (name, key))
    meta = wav[:-4] + '.json'
    if os.path.exists(wav) and os.path.exists(meta):
        info = json.load(open(meta))
    else:
        info = sfx_lib.sfx(name, wav, duration=duration, seed=seed, **params)
        json.dump(info, open(meta, 'w'))
    return read_wav(wav), info


def render_sfx_entry(e, seed, cache):
    """Render one sfx entry, taking (and logging) a fallback when the library lacks the name
    or rejects a param. Returns (audio, info, name used, fallback note)."""
    name = e['name']
    params = dict(e.get('params') or {})
    duration = params.pop('duration', None)
    known = sfx_lib.effects()
    note = ''
    if name not in known:
        alt, pmap = SFX_FALLBACKS.get(name, (None, {}))
        if alt not in known:
            warn('sfx %s at %.3f: DROPPED -- not in sfx_lib and no fallback' % (name, e['t']))
            return None, None, name, 'dropped'
        note = 'FALLBACK %s -> %s' % (name, alt)
        name, params = alt, {pmap.get(k, k): v for k, v in params.items()}
    try:
        y, info = render_sfx(name, duration, seed, params, cache)
    except TypeError as err:
        bad = re.findall(r"'(\w+)'", str(err))
        kept = {k: v for k, v in params.items() if k not in bad}
        note += (' ' if note else '') + 'FALLBACK dropped params %s (%s)' % (sorted(set(params) - set(kept)), err)
        y, info = render_sfx(name, duration, seed, kept, cache)
    if note:
        warn('sfx %s at %.3f: %s' % (e['name'], e['t'], note))
    return y, info, name, note


def build_sfx(tl, N, cache):
    D = np.zeros((N, 2))      # ducked with the music (the wind bed)
    S = np.zeros((N, 2))      # not ducked
    seen = {}
    rng = np.random.default_rng(zlib.crc32(b'laugh pans'))
    report = []
    for e in sorted(tl['sfx'], key=lambda e: e['t']):
        seed = seen.get(e['name'], 0)
        seen[e['name']] = seed + 1
        y, info, used, note = render_sfx_entry(e, seed, cache)
        if y is None:
            report.append(dict(name=e['name'], t=e['t'], note=note))
            continue
        pan = 0.0
        if used in LAUGH_PAN:
            pan = float(rng.choice([-1.0, 1.0]) * rng.uniform(0.4, 1.0) * LAUGH_PAN[used])
            y = balance_pan(y, pan)
        dst = D if used in DUCKED_SFX else S
        g = float(e.get('gain', 0.0))
        a, b, faded = place(dst, y, int(round((e['t'] - info['sync']) * SR)), db(g))
        lvl = (info['lufs_i'] if info['kind'] == 'bed' else info['lufs_m']) + g
        lib_target = lvl - g + info['mix_gain_db']
        extra = []
        if pan:
            extra.append('pan %+.2f' % pan)
        if used in DUCKED_SFX:
            extra.append('ducked')
        if faded:
            extra.append('end fade %.1f s' % END_FADE)
        if note:
            extra.append(note)
        log('  sfx   %-18s t=%7.3f seed %d sync %.3f %-7s %5.2f s gain %+5.1f -> %s %6.1f LUFS (lib target %6.1f)  %s' % (
            used, e['t'], seed, info['sync'], info['kind'], info['duration'], g,
            'I' if info['kind'] == 'bed' else 'M', lvl, lib_target, ', '.join(extra)))
        report.append(dict(name=e['name'], used=used, t=e['t'], seed=seed, gain=g, sync=info['sync'], kind=info['kind'],
                           start=a / SR, end=b / SR, level_lufs=round(lvl, 1), lib_target=round(lib_target, 1),
                           pan=round(pan, 3), note=note))
    return D, S, report


# ----------------------------------------------------------------------------- ducking + balance


def span_envelope(lines, depths, N):
    """Depth (dB) envelope: raised-cosine attack ending at each line's start, hold, release.
    Overlapping lines take the deeper of their depths."""
    env = np.zeros(N)
    na, nr = int(DUCK_ATTACK * SR), int(DUCK_RELEASE * SR)
    att, rel = fade_curve(na, out=False), fade_curve(nr)
    for ln, d in zip(lines, depths):
        if d <= 0:
            continue
        a, b = ln['a'], ln['b']
        shape = np.concatenate([att, np.ones(b - a), rel]) * d
        i0 = a - na
        lo, hi = max(0, i0), min(N, i0 + len(shape))
        env[lo:hi] = np.maximum(env[lo:hi], shape[lo - i0:hi - i0])
    return env


def line_powers(ln, V, D, S, gd, gs):
    """Mean power over the line's span: voice, whole bed, ducked part, sfx part."""
    a, b = ln['a'], ln['b']
    d, s = D[a:b] * gd[a:b, None], S[a:b] * gs[a:b, None]
    return np.mean(V[a:b] ** 2), np.mean((d + s) ** 2), np.mean(d ** 2), np.mean(s ** 2)


def balance(lines, V, D, S, N):
    """Duck depths per line (music + wind) and sfx dips that keep every line >= 10 dB over
    the bed. Returns gain curves (gd, gs) and per-line results."""
    duck = np.full(len(lines), DUCK_DB)
    dip = np.zeros(len(lines))
    for it in range(8):
        gd = db(-span_envelope(lines, duck, N))
        gs = db(-span_envelope(lines, dip, N))
        short = []
        for i, ln in enumerate(lines):
            pv, pb, pd, ps = line_powers(ln, V, D, S, gd, gs)
            r = to_db(pv) - to_db(pb)
            if r < MIN_SPEECH_TO_BED:
                short.append((i, r, pd, ps))
        if not short:
            break
        for i, r, pd, ps in short:
            need = MIN_SPEECH_TO_BED + FIX_MARGIN - r
            if pd >= ps and duck[i] < DUCK_DB + MAX_EXTRA_DUCK:
                duck[i] = min(DUCK_DB + MAX_EXTRA_DUCK, duck[i] + need)
            elif dip[i] < MAX_SFX_DIP:
                dip[i] = min(MAX_SFX_DIP, dip[i] + need)
            else:
                duck[i] = min(DUCK_DB + MAX_EXTRA_DUCK, duck[i] + need)
    gd = db(-span_envelope(lines, duck, N))
    gs = db(-span_envelope(lines, dip, N))
    for i, ln in enumerate(lines):
        if duck[i] > DUCK_DB or dip[i] > 0:
            log('  balance %s: duck %.1f dB, sfx dip %.1f dB' % (ln['id'], duck[i], dip[i]))
    return gd, gs, duck, dip


# ----------------------------------------------------------------------------- mastering


def ffmpeg_loudness(x):
    """ffmpeg loudnorm analysis pass over stereo float samples (piped as f32le)
    -> dict (input_i, input_tp, input_lra, input_thresh)."""
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-f', 'f32le', '-ar', str(SR), '-ac', '2',
                        '-i', 'pipe:0', '-af',
                        'loudnorm=I=%g:TP=%g:LRA=11:print_format=json' % (TARGET_LUFS, TP_CEIL_DB),
                        '-f', 'null', '-'], input=np.ascontiguousarray(x, dtype='<f4').tobytes(),
                       capture_output=True, check=True)
    err = r.stderr.decode(errors='replace')
    js = json.loads(err[err.rindex('{'):err.rindex('}') + 1])
    return {k: float(v) for k, v in js.items() if k.startswith('input_')}


def peak_env(x, os_=4, block=1 << 20):
    """Per-sample true-peak envelope (max |x| of the 4x-oversampled signal over both channels)."""
    pad = 64
    out = np.empty(len(x))
    for s in range(0, len(x), block):
        lo, hi = max(0, s - pad), min(len(x), s + block + pad)
        up = np.abs(signal.resample_poly(x[lo:hi], os_, 1, axis=0)).max(axis=1)
        e = up.reshape(-1, os_).max(axis=1)
        e = np.maximum(e, np.concatenate([[0.0], e[:-1]]))
        out[s:min(len(x), s + block)] = e[s - lo:s - lo + min(block, len(x) - s)]
    return out


def tp_limit(x, ceil_db):
    """Linked look-ahead limiter on the true-peak envelope: the gain reaches its floor
    LIMIT_LOOK before an over, holds LIMIT_HOLD after it, raised-cosine-ish ramps."""
    ceil = db(ceil_db)
    g = np.minimum(1.0, ceil / np.maximum(peak_env(x), 1e-12))
    if g.min() >= 1.0:
        return x, np.ones(len(x)), 0.0, 0
    A, H = int(LIMIT_LOOK * SR), int(LIMIT_HOLD * SR)
    H += (H - A) % 2
    m = minimum_filter1d(g, size=A + H + 1, origin=(H - A) // 2, mode='nearest')
    w = A // 2 + 1
    m = uniform_filter1d(uniform_filter1d(m, w, mode='nearest'), w, mode='nearest')
    return x * m[:, None], m, float(-20 * np.log10(m.min())), int(np.sum(g < 1.0))


def master(mix):
    before = ffmpeg_loudness(mix)
    log('  before: I %.2f LUFS, TP %.2f dBTP, LRA %.1f LU, threshold %.2f LUFS' % (
        before['input_i'], before['input_tp'], before['input_lra'], before['input_thresh']))
    next_gain = TARGET_LUFS - before['input_i']
    for it in range(5):
        gain = next_gain
        y, curve, gr, novers = tp_limit(mix * db(gain), TP_CEIL_DB - TP_MARGIN_DB)
        after = ffmpeg_loudness(y)
        log('  pass %d: gain %+.2f dB, limiter max %.2f dB on %d samples -> I %.2f LUFS, TP %.2f dBTP' % (
            it + 1, gain, gr, novers, after['input_i'], after['input_tp']))
        if abs(after['input_i'] - TARGET_LUFS) <= 0.1 and after['input_tp'] <= TP_CEIL_DB:
            break
        next_gain = gain + TARGET_LUFS - after['input_i']
    else:
        warn('mastering did not converge: I %.2f, TP %.2f' % (after['input_i'], after['input_tp']))
    return y, curve * db(gain), gain, gr, before, after


# ----------------------------------------------------------------------------- main


def report_lines(lines, V, D, S, gd, gs, duck, dip, mg):
    """Per-line speech-to-bed table, through the mastering gain curve mg."""
    rows = []
    log('  %-4s %s %8s %5s %6s %8s %8s %7s %6s %6s %s' % ('line', 'S', 't', 'dur', 'gain', 'voice', 'bed', 'S/B', 'duck', 'dip', ''))
    for i, ln in enumerate(lines):
        a, b = ln['a'], ln['b']
        g = mg[a:b, None]
        v = V[a:b] * g
        bed = (D[a:b] * gd[a:b, None] + S[a:b] * gs[a:b, None]) * g
        pv, pb = np.mean(v ** 2), np.mean(bed ** 2)
        r = to_db(pv) - to_db(pb)
        flag = ('hushed ' if ln['hushed'] else '') + ('' if r >= MIN_SPEECH_TO_BED else 'SHORT')
        log('  %-4s %s %8.3f %5.2f %+6.1f %8.1f %8.1f %+7.1f %6.1f %6.1f %s' % (
            ln['id'], ln['speaker'], ln['t'], ln['dur'], ln['gain'], to_db(pv), to_db(pb), r, duck[i], dip[i], flag))
        rows.append(dict(id=ln['id'], speaker=ln['speaker'], t=ln['t'], dur=ln['dur'], hushed=ln['hushed'],
                         voice_rms_db=round(to_db(pv), 2), bed_rms_db=round(to_db(pb), 2),
                         speech_to_bed_db=round(r, 2), duck_db=round(float(duck[i]), 2), sfx_dip_db=round(float(dip[i]), 2)))
    return rows


def main(timeline_path, voices_dir, out_wav):
    tl = json.load(open(timeline_path))
    N = int(round(float(tl['duration']) * SR))
    out_dir = os.path.dirname(os.path.abspath(out_wav))
    cache = os.path.join(out_dir, 'cache')
    os.makedirs(cache, exist_ok=True)
    log('film %.4f s = %d samples @ %d Hz' % (tl['duration'], N, SR))

    log('voices (%d lines)' % len(tl['audio']))
    V, lines = build_voices(tl, voices_dir, N)
    log('music (%d cues)' % len(tl['music']))
    M, music_rep = build_music(tl, N, cache)
    log('sfx (%d effects)' % len(tl['sfx']))
    W, S, sfx_rep = build_sfx(tl, N, cache)
    D = M + W
    del M, W

    log('ducking + balance (%.0f dB, attack %.0f ms, release %.0f ms)' % (DUCK_DB, DUCK_ATTACK * 1e3, DUCK_RELEASE * 1e3))
    gd, gs, duck, dip = balance(lines, V, D, S, N)
    mix = V + D * gd[:, None] + S * gs[:, None]

    log('master (target %.1f LUFS, TP <= %.1f dBTP)' % (TARGET_LUFS, TP_CEIL_DB))
    y, mg, gain, gr, before, after = master(mix)
    del mix
    assert len(y) == N and np.all(np.isfinite(y))
    sf.write(out_wav, y.astype(np.float32), SR, subtype='FLOAT')
    final = ffmpeg_loudness(sf.read(out_wav, dtype='float64', always_2d=True)[0])
    log('  after (file): I %.2f LUFS, TP %.2f dBTP, LRA %.1f LU; sample peak %.2f dBFS; %d samples' % (
        final['input_i'], final['input_tp'], final['input_lra'], 20 * np.log10(np.abs(y).max()), len(y)))

    log('speech-to-bed per line (RMS over the line span, after mastering)')
    rows = report_lines(lines, V, D, S, gd, gs, duck, dip, mg)
    worst = min(rows, key=lambda r: r['speech_to_bed_db'])
    log('min speech-to-bed: %+.1f dB (%s)' % (worst['speech_to_bed_db'], worst['id']))
    if worst['speech_to_bed_db'] < MIN_SPEECH_TO_BED:
        warn('%d line(s) below +%.0f dB' % (sum(r['speech_to_bed_db'] < MIN_SPEECH_TO_BED for r in rows), MIN_SPEECH_TO_BED))
    rep = dict(out=out_wav, samples=N, sr=SR, loudness_before=before, loudness_after=final, master_gain_db=gain,
               limiter_max_db=gr, lines=rows, music=music_rep, sfx=sfx_rep, warnings=WARNINGS)
    json.dump(rep, open(os.path.splitext(out_wav)[0] + '_report.json', 'w'), indent=1)
    log('wrote %s (%d warnings)' % (out_wav, len(WARNINGS)))
    for w in WARNINGS:
        log('  ! ' + w)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__.split('\n\n')[1])
    main(*sys.argv[1:])
