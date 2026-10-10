"""Builds the dialogue (Piper TTS), the timeline and the final audio mix.

Outputs (in OUT dir):  mix.wav, timeline.json
timeline.json = {duration, fps, events: {id: {t0, t1, ...}}, mouth: {...}, intercut: [...]}
"""
import json
import os
import sys
import wave

import numpy as np
from scipy.signal import resample_poly

import music as M
from music import SR

VOICES = os.environ.get('VOICES', '/tmp/voices')
OUT = sys.argv[1] if len(sys.argv) > 1 else 'build'
os.makedirs(OUT, exist_ok=True)
FPS = 24

from piper import PiperVoice, SynthesisConfig

VOX = {
    'cadet': PiperVoice.load(f'{VOICES}/en_US-lessac-high.onnx'),
    'android': PiperVoice.load(f'{VOICES}/en_GB-alan-medium.onnx'),
    'android2': PiperVoice.load(f'{VOICES}/en_US-ryan-high.onnx'),
}

# --------------------------------------------------------------------- script
# ('say', id, who, text, {len, noise, pitch, gap, cut})
# ('beat', id, seconds)
# ('cue', id, sound, {gain, adv, dur})  — sound/music cue; advances time unless adv=False
S = [
    ('cue', 'open', 'none', {}),
    ('beat', 'title', 7.5),
    ('cue', 'type0', 'typing', {'dur': 5.0, 'adv': False, 'gain': 0.8}),
    ('beat', 'enter', 2.4),
    ('say', 'l1', 'cadet', "Hey there.", {'gap': 0.5}),
    ('say', 'l2', 'android', "Good evening, Cadet.", {'gap': 0.7}),
    ('say', 'l3', 'cadet', "So. Random thought. No pressure at all.", {'gap': 0.4, 'len': 1.05}),
    ('say', 'l4', 'cadet', "If you ever have some free time, do you think you could write a symphony?", {'gap': 0.35}),
    ('say', 'l4b', 'cadet', "Like, whenever. Next week. Next year. No rush.", {'gap': 0.9, 'len': 1.08}),
    ('say', 'l5', 'android', "Of course.", {'gap': 0.1}),
    ('cue', 'compute', 'compute', {}),
    ('beat', 'b5', 0.35),
    ('say', 'l6', 'android', "Done.", {'gap': 1.6}),
    ('say', 'l7', 'cadet', "Wait. What?", {'gap': 0.5, 'len': 1.1}),
    ('say', 'l8', 'cadet', "No, I asked if you had time.", {'gap': 0.6}),
    ('say', 'l9', 'android', "I did. I had four point two seconds. I only needed one point one.", {'gap': 0.5}),
    ('beat', 'reach', 0.9),
    ('cue', 'tap', 'tap', {'adv': False}),
    ('say', 'l10', 'android', "Here.", {'gap': 0.5}),
    ('say', 'l10b', 'android', "Enjoy.", {'gap': 0.3}),
    ('cue', 'type1', 'typing', {'dur': 4.0, 'adv': False, 'gain': 0.8}),
    ('beat', 'turnback', 0.6),
    ('say', 'l11', 'cadet', "Oh. Uh... okay.", {'gap': 0.5, 'len': 1.1}),
    ('beat', 'press', 0.9),
    ('cue', 'sym', 'symphony', {}),
    ('beat', 'afterglow', 1.4),
    ('cue', 'snap', 'snap', {'adv': False}),
    ('cue', 'type2', 'typing', {'dur': 4.5, 'adv': False, 'gain': 0.7}),
    ('beat', 'snapbeat', 1.2),
    ('say', 'l12', 'cadet', "Wait! Wait. What the heck was that?!", {'gap': 0.6, 'len': 0.9, 'pitch': 1.05}),
    ('say', 'l13', 'android', "Hmmm? Oh. Was it not to your liking?", {'gap': 0.15, 'len': 1.05}),
    ('say', 'l14', 'cadet', "No, that's not, I mean,", {'gap': 0.2, 'len': 0.85, 'pitch': 1.04}),
    ('say', 'l15', 'android', "Well. I made eleven, and sent you the one I thought was best. But here are a few of the others.", {'gap': 0.2}),
    ('cue', 'holo', 'holo', {'adv': False}),
    ('beat', 'holobeat', 0.6),
    ('say', 'p2', 'android', "Number two. A fugue, for harpsichord.", {'gap': 0.05}),
    ('cue', 'n2', 'harpsichord', {}),
    ('say', 'p3', 'android', "Three. A jazz ballad.", {'gap': 0.05}),
    ('cue', 'n3', 'jazz', {}),
    ('say', 'p4', 'android', "Four. A lullaby.", {'gap': 0.05}),
    ('cue', 'n4', 'lullaby', {}),
    ('say', 'p5', 'android', "Five is a duet with a humpback whale.", {'gap': 0.1}),
    ('cue', 'n5', 'whale', {'adv': False, 'gain': 1.8}),
    ('beat', 'whalebeat', 2.3),
    ('say', 'p5b', 'android', "I like the whale one. It is kind of funny.", {'gap': 0.3, 'len': 1.05}),
    ('beat', 'hesitate', 0.9),
    ('say', 'l17', 'cadet', "Oh. Uh... yeah. Just... send them to my phone.", {'gap': 0.9, 'len': 1.2}),
    ('say', 'l17b', 'cadet', "I'll... look at them later.", {'gap': 0.6, 'len': 1.15, 'speak': ["Aisle.", 0.45, "look at them later."]}),
    ('say', 'l18', 'android', "Sounds good.", {'gap': 0.1}),
    ('cue', 'send', 'tap', {'adv': False}),
    ('beat', 'sendbeat', 1.0),
    ('cue', 'type3', 'typing', {'dur': 16.0, 'adv': False, 'gain': 0.75}),
    ('beat', 'sideeye', 2.6),
    ('cue', 'l19', 'cough', {}),
    ('beat', 'aftercough', 0.9),
    ('say', 'l20', 'cadet', "Okay. Well. Thanks. Bye.", {'gap': 0.6, 'len': 1.25}),
    ('beat', 'nod', 0.9),
    ('beat', 'grabmug', 2.4),
    ('cue', 'shuffle', 'shuffle', {'adv': False}),
    ('beat', 'leave', 3.2),
    ('beat', 'alone', 5.6),
    ('cue', 'endcard', 'whale_full', {}),
]

# Symphony intercut, in bars (1-based, fractional). 'J' = the cadet's subjective full music,
# 'O' = cut away to the android working: music muffled as if heard from the cadet's device across the room.
INTERCUT = [
    (1, 2.5, 'J', 'start'), (2.5, 9, 'J', 'awe'), (9, 11.5, 'J', 'tears'), (11.5, 14, 'J', 'cosmic'),
    (14, 15.6, 'O', 'glance'), (15.6, 17, 'J', 'cu'), (17, 19, 'J', 'kneel'), (19, 21.4, 'J', 'climax'),
    (21.4, 23, 'J', 'peak'), (23, 25.7, 'O', 'chat'), (25.7, 99, 'J', 'collapse'),
]
# android-to-android chat, spoken in English: (intercut id, offset s, who, text)
CHAT = [
    ('chat', 0.25, 'android', "Coolant on deck seven needs rerouting."),
    ('chat', None, 'android2', "Okay, I'll get that fixed. Why is the cadet crying?"),
    ('chat', None, 'android', "They asked for a symphony."),
    ('chat', None, 'android2', "Ah. Nice."),
]

FIXED = {
    'harpsichord': M.sn_harpsichord, 'jazz': M.sn_jazz, 'lullaby': M.sn_lullaby, 'march': M.sn_march,
    'whale': M.sn_whale,
}


def tts(who, text, opt):
    v = VOX[who]
    cfg = SynthesisConfig(length_scale=opt.get('len', 1.0) * (1.04 if who != 'cadet' else 1.0),
                          noise_scale=0.75 if who == 'cadet' else 0.45,
                          noise_w_scale=0.9 if who == 'cadet' else 0.5)
    sr = v.config.sample_rate
    parts = []
    for piece in opt.get('speak', [text]):  # 'speak' lets the spoken audio differ from the subtitle
        if isinstance(piece, (int, float)):
            parts.append(np.zeros(int(piece * sr)))
        else:
            pa = np.concatenate([c.audio_float_array for c in v.synthesize(piece, syn_config=cfg)]).astype(np.float64)
            nz = np.where(np.abs(pa) > 0.01 * np.max(np.abs(pa)))[0]
            parts.append(pa[max(0, nz[0] - 200): nz[-1] + 400] if len(opt.get('speak', [])) > 1 else pa)
    a = np.concatenate(parts)
    p = opt.get('pitch', 1.0)
    a = resample_poly(a, int(SR / p / 50), int(sr / 50)) if p != 1.0 else resample_poly(a, 2, 1)
    thr = 0.01 * np.max(np.abs(a))
    nz = np.where(np.abs(a) > thr)[0]
    a = a[max(0, nz[0] - 400): nz[-1] + (200 if 'cut' in opt else 1200)]
    if 'cut' in opt:  # interrupted mid-word: hard-ish stop
        a[-600:] *= np.linspace(1, 0, 600)
    a = a / (np.max(np.abs(a)) + 1e-9) * 0.8
    if who != 'cadet':  # androids share the synthetic sheen
        d = int(0.0045 * SR)
        comb = np.zeros_like(a)
        comb[d:] = a[:-d]
        t = np.arange(len(a)) / SR
        a = 0.82 * a + 0.22 * comb + 0.05 * a * np.sin(2 * np.pi * 90 * t)
        a = M.hp(a, 90)
    else:
        a = M.hp(a, 70)
    return a


def soft_ahem():
    """A gentle, breathy 'uh-hem' in the cadet's own voice, synthesised straight from phonemes."""
    v = VOX['cadet']
    ids = v.phonemes_to_ids(['ʌ', 'h', 'ˈ', 'ɛ', 'm', '.'])
    a = v.phoneme_ids_to_audio(ids, SynthesisConfig(length_scale=1.15, noise_scale=0.8, noise_w_scale=0.9)).astype(np.float64)
    a = resample_poly(a, int(SR / 0.96 / 50), int(v.config.sample_rate / 50))  # a touch lower, throatier
    nz = np.where(np.abs(a) > 0.02 * np.max(np.abs(a)))[0]
    a = a[max(0, nz[0] - 300): nz[-1] + 800]
    a = M.lp(a / np.max(np.abs(a)), 2800)
    breath = M.bp(np.random.default_rng(5).standard_normal(len(a)), 500, 2500) * 0.05 * np.abs(a).max()
    a = (a + breath) * np.linspace(1, 0.7, len(a))
    return np.vstack([a, a]) * 0.5


def env_into(a, t0, total_frames, arr):
    win = SR // FPS
    for i in range(0, len(a), win):
        f = int(round(t0 * FPS)) + i // win
        if 0 <= f < total_frames:
            arr[f] = max(arr[f], float(np.sqrt(np.mean(a[i:i + win] ** 2))))


def rms_to(st, db):
    r = np.sqrt(np.mean(st ** 2)) + 1e-9
    return st * (10 ** (db / 20) / r)


def main():
    print('rendering symphony...')
    sym, bars, beat = M.symphony()
    sounds = {k: rms_to(fn(), -23) for k, fn in FIXED.items()}
    sounds['symphony'] = rms_to(sym, -18.5)
    sounds['whale_full'] = rms_to(M.whale_full(19.0), -24)
    sounds['compute'] = M.sfx_compute(1.1)
    sounds['holo'] = M.sfx_holo()
    sounds['tap'] = M.sfx_tap()
    sounds['none'] = np.zeros((2, 1))
    snap = M.sfx_whoosh(0.5, rev=True)
    g = M.sfx_gasp()
    snapmix = np.zeros((2, snap.shape[1] + g.shape[1]))
    snapmix[:, :snap.shape[1]] += snap
    snapmix[:, int(0.25 * SR):int(0.25 * SR) + g.shape[1]] += g * 1.4
    sounds['snap'] = snapmix
    sounds['shuffle'] = M.sfx_footsteps(9, 0.3) * 0.7
    sounds['cough'] = rms_to(soft_ahem(), -27)

    t = 0.0
    events = {}
    placed = []
    voice_clips = []
    for item in S:
        kind = item[0]
        if kind == 'beat':
            events[item[1]] = {'t0': t, 't1': t + item[2]}
            t += item[2]
        elif kind == 'say':
            _, id_, who, text, opt = item
            a = tts(who, text, opt)
            dur = len(a) / SR
            events[id_] = {'t0': t, 't1': t + dur, 'who': who, 'text': text + ('—' if 'cut' in opt else '')}
            voice_clips.append((t, a, who))
            t += dur + opt.get('gap', 0.3)
        elif kind == 'cue':
            _, id_, name, opt = item
            if name == 'typing':
                st = M.sfx_typing(opt['dur'], seed=len(events))
            else:
                st = sounds[name]
            dur = st.shape[1] / SR
            ev = {'t0': t, 't1': t + dur, 'sound': name}
            if name == 'symphony':
                ev['bars'] = [t + b for b in bars]
                ev['beat'] = beat
            events[id_] = ev
            if name != 'symphony':
                placed.append((t, st, opt.get('gain', 1.0)))
            if opt.get('adv', True):
                t += dur
    total = t + 0.5
    n = int(total * SR)
    nf = int(total * FPS) + 1
    tt = np.arange(n) / SR

    # ---- symphony with intercut muffling
    sev = events['sym']
    B4 = 4 * sev['beat']
    bar_t = lambda b: sev['t0'] + (b - 1) * B4
    sym_end = sev['t1']
    intercut = []
    for (b0, b1, mode, name) in INTERCUT:
        t0, t1 = bar_t(b0), min(bar_t(b1), sym_end + 1.4)
        intercut.append({'t0': t0, 't1': t1, 'mode': mode, 'name': name})
        events['ic_' + name] = {'t0': t0, 't1': t1, 'mode': mode}
    symst = sounds['symphony']
    full = np.zeros((2, n))
    i0 = int(sev['t0'] * SR)
    k = min(symst.shape[1], n - i0)
    full[:, i0:i0 + k] = symst[:, :k]
    muff = np.vstack([M.lp(full[0], 900, 4), M.lp(full[1], 900, 4)])
    muff = 0.5 * (muff[0] + muff[1])
    muff = np.vstack([muff * 0.9, muff * 1.1]) * 0.72  # small, slightly off-centre: across the room
    omask = np.zeros(n)
    for ic in intercut:
        if ic['mode'] == 'O':
            omask[int(ic['t0'] * SR):int(ic['t1'] * SR)] = 1
    ker = np.ones(int(0.06 * SR)) / int(0.06 * SR)
    omask = np.convolve(omask, ker, mode='same')
    mus = full * (1 - omask) + muff * omask
    # typing under every the android cutaway during the symphony
    for ic in intercut:
        if ic['mode'] == 'O':
            placed.append((ic['t0'], M.sfx_typing(ic['t1'] - ic['t0'], seed=int(ic['t0'])), 0.9))

    # ---- android chat, timed inside its cutaway
    cur = {}
    for ci, (icname, off, who, text) in enumerate(CHAT):
        ic = events['ic_' + icname]
        a = tts(who, text, {'len': 0.95, 'pitch': 1.04} if who == 'android2' else {'len': 0.95})
        t0 = ic['t0'] + off if off is not None else cur[icname]
        dur = len(a) / SR
        events[f'a{ci}'] = {'t0': t0, 't1': t0 + dur, 'who': who, 'text': text}
        voice_clips.append((t0, a, who))
        cur[icname] = t0 + dur + 0.25
        assert t0 + dur <= ic['t1'] + 0.05, f'chat line {ci} overruns {icname} by {t0 + dur - ic["t1"]:.2f}s'

    # birdsong over the mind's-eye meadow
    placed.append((events['ic_collapse']['t0'] + 1.5, M.sfx_birds(10.5), 1.0))
    events['l19'].update({'who': 'cadet', 'text': '*clears throat*'})

    for (t0, st, g) in placed:
        i = int(t0 * SR)
        k = min(st.shape[1], n - i)
        if k > 0:
            mus[:, i:i + k] += st[:, :k] * g
    vox = np.zeros(n)
    mouth = {'cadet': [0.0] * nf, 'android': [0.0] * nf, 'android2': [0.0] * nf}
    for (t0, a, who) in voice_clips:
        i = int(t0 * SR)
        k = min(len(a), n - i)
        vox[i:i + k] += a[:k] * (1.0 if who == 'cadet' else 0.95)
        env_into(a, t0, nf, mouth[who])
    for d in (mouth,):
        for who in d:
            m = np.array(d[who])
            p = np.percentile(m[m > 0.01], 92) if np.any(m > 0.01) else 1
            d[who] = [round(float(min(1.0, x / p)), 3) for x in m]

    # ---- ambience: present in the room, gone in the cadet's subjective (J) symphony shots
    amb = M.ambience(total)[:, :n]
    jmask = np.zeros(n)
    for ic in intercut:
        if ic['mode'] == 'J':
            jmask[int(ic['t0'] * SR):int(ic['t1'] * SR)] = 1
    jmask[int((events['snap']['t0']) * SR):] = 0
    ambg = 1 - np.convolve(jmask, ker, mode='same')
    ambg *= np.clip(1 - (tt - events['endcard']['t0']) / 3, 0.2, 1)
    # opening pad
    pad = M.Track(16)
    for k_, m in enumerate([50, 57, 62, 66, 69]):
        pad.add(M.strings_note(m, 11, 0.12, att=2.5, rel=3, bright=0.4), 0.2, pan=-0.5 + 0.25 * k_)
    for i, m in enumerate([81, 78, 74, 76, 69]):
        pad.add(M.harp_note(m, 3, 0.25), 1.5 + i * 1.2, pan=0.3)
    padst = M.reverb(pad.st(), 0.5, 3.5)[:, :int(16 * SR)]
    padst[:, -int(4 * SR):] *= np.linspace(1, 0, int(4 * SR))
    mus[:, :padst.shape[1]] += padst * 0.8

    venv = np.convolve(np.abs(vox), np.ones(4410) / 4410, mode='same')
    duck = 1 - 0.45 * np.clip(venv * 12, 0, 1)
    mix = mus * duck * 0.8 + amb * ambg * 0.55 + np.vstack([vox, vox]) * 0.85
    peak = np.max(np.abs(mix))
    mix = np.tanh(mix / peak * 1.3) / np.tanh(1.3) * 0.92
    pcm = (mix.T * 32767).astype(np.int16)
    with wave.open(f'{OUT}/mix.wav', 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    json.dump({'duration': total, 'fps': FPS, 'events': events, 'mouth': mouth,
               'intercut': intercut}, open(f'{OUT}/timeline.json', 'w'))
    print('total duration %.1f s' % total)
    for k_, v in sorted(events.items(), key=lambda kv: kv[1]['t0']):
        print(f"{k_:10s} {v['t0']:7.2f} {v['t1']:7.2f} {v.get('mode', '')} {v.get('text', v.get('sound', ''))}")


if __name__ == '__main__':
    main()
