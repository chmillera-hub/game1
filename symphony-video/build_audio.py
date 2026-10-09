"""Builds the dialogue (Piper TTS), the timeline and the final audio mix.

Outputs (in OUT dir):  mix.wav, timeline.json
timeline.json = {duration, fps, events: {id: {t0, t1, ...}}, mouth: {jun: [...], orrin: [...]}}
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
    'jun': PiperVoice.load(f'{VOICES}/en_US-lessac-high.onnx'),
    'orrin': PiperVoice.load(f'{VOICES}/en_GB-alan-medium.onnx'),
}

# --------------------------------------------------------------------- script
# ('say', id, who, text, {len, noise, pitch, gap})
# ('beat', id, seconds)
# ('cue', id, sound, {gain, adv})  — a sound/music cue; advances time by its length unless adv=False
S = [
    ('cue', 'open', 'ambient_intro', {}),
    ('beat', 'title', 7.5),
    ('beat', 'enter', 2.4),
    ('say', 'l1', 'jun', "Hey, Orrin.", {'gap': 0.5}),
    ('say', 'l2', 'orrin', "Good evening, Lieutenant.", {'gap': 0.7}),
    ('say', 'l3', 'jun', "So. Random thought. No pressure at all.", {'gap': 0.4, 'len': 1.05}),
    ('say', 'l4', 'jun', "If you ever have some free time, do you think you could write a symphony?", {'gap': 0.35}),
    ('say', 'l4b', 'jun', "Like, whenever. Next week. Next year. No rush.", {'gap': 0.9, 'len': 1.08}),
    ('say', 'l5', 'orrin', "Of course.", {'gap': 0.1}),
    ('cue', 'compute', 'compute', {}),
    ('beat', 'b5', 0.35),
    ('say', 'l6', 'orrin', "Done.", {'gap': 1.6}),
    ('say', 'l7', 'jun', "Wait. What?", {'gap': 0.5, 'len': 1.1}),
    ('say', 'l8', 'jun', "No, I asked if you had time.", {'gap': 0.6}),
    ('say', 'l9', 'orrin', "I did. I had four point two seconds. I only needed one point one.", {'gap': 0.6}),
    ('say', 'l10', 'orrin', "Would you like to hear it?", {'gap': 0.7}),
    ('say', 'l11', 'jun', "I mean... sure. Go for it.", {'gap': 0.4, 'len': 1.1}),
    ('cue', 'dim', 'dim', {'adv': False}),
    ('beat', 'dimbeat', 1.6),
    ('cue', 'sym', 'symphony', {}),
    ('beat', 'afterglow', 1.4),
    ('cue', 'snap', 'snap', {'adv': False}),
    ('beat', 'snapbeat', 0.9),
    ('say', 'l12', 'jun', "Wait! Wait. What the heck was that?!", {'gap': 0.5, 'len': 0.9, 'pitch': 1.05}),
    ('say', 'l13', 'orrin', "Oh. I apologize. You did not like it.", {'gap': 0.15, 'len': 1.1}),
    ('say', 'l14', 'jun', "No, that's not, I mean,", {'gap': 0.15, 'len': 0.85, 'pitch': 1.04}),
    ('say', 'l15', 'orrin', "It's quite alright. I composed eleven of them, and selected the one I believed was best.", {'gap': 0.4}),
    ('say', 'l16', 'orrin', "But here are the others. Perhaps one of them will suit you better.", {'gap': 0.2}),
    ('cue', 'holo', 'holo', {'adv': False}),
    ('beat', 'holobeat', 0.6),
    ('cue', 'n2', 'harpsichord', {}),
    ('cue', 'n3', 'jazz', {}),
    ('cue', 'n4', 'lullaby', {}),
    ('cue', 'n5', 'march', {}),
    ('cue', 'n6', 'choir', {}),
    ('cue', 'n7', 'whale', {'adv': False, 'gain': 0.8}),
    ('say', 'l17', 'orrin', "Number seven incorporates whale song.", {'gap': 1.2}),
    ('cue', 'n8', 'synth', {}),
    ('say', 'l18', 'orrin', "Number nine is in a time signature that humans cannot technically perceive.", {'gap': 0.0}),
    ('cue', 'n9', 'odd', {}),
    ('cue', 'n10', 'kazoo', {}),
    ('say', 'l18b', 'orrin', "And number eleven is four minutes of silence. I am quite proud of that one.", {'gap': 0.8}),
    ('say', 'l19', 'jun', "Okay. Nope.", {'gap': 0.4, 'len': 1.1}),
    ('say', 'l20', 'jun', "I'm, I'm gonna go.", {'gap': 0.25, 'len': 1.05}),
    ('say', 'l21', 'orrin', "Shall I begin a twelfth?", {'gap': 0.15}),
    ('say', 'l22', 'jun', "I'm getting out of here!", {'gap': 0.0, 'len': 0.85, 'pitch': 1.06}),
    ('cue', 'run', 'run', {'adv': False}),
    ('beat', 'exit', 2.3),
    ('beat', 'alone', 1.4),
    ('say', 'l23', 'orrin', "Perhaps I should have taken longer.", {'gap': 2.2, 'len': 1.12}),
    ('cue', 'door2', 'door', {'adv': False}),
    ('beat', 'peek', 0.9),
    ('say', 'l24', 'jun', "Send me number four.", {'gap': 0.5, 'len': 1.1}),
    ('cue', 'door3', 'door', {'adv': False}),
    ('beat', 'smile', 2.6),
    ('cue', 'endcard', 'lullaby_full', {}),
]

FIXED = {
    'harpsichord': M.sn_harpsichord, 'jazz': M.sn_jazz, 'lullaby': M.sn_lullaby, 'march': M.sn_march,
    'choir': M.sn_choir, 'whale': M.sn_whale, 'synth': M.sn_synth, 'odd': M.sn_odd, 'kazoo': M.sn_kazoo,
}


def tts(who, text, opt):
    v = VOX[who]
    cfg = SynthesisConfig(length_scale=opt.get('len', 1.0) * (1.04 if who == 'orrin' else 1.0),
                          noise_scale=0.75 if who == 'jun' else 0.45,
                          noise_w_scale=0.9 if who == 'jun' else 0.5)
    chunks = [c.audio_float_array for c in v.synthesize(text, syn_config=cfg)]
    a = np.concatenate(chunks).astype(np.float64)
    sr = v.config.sample_rate
    p = opt.get('pitch', 1.0)
    # resample to 44.1k (and optionally shift pitch+tempo a touch for panic)
    a = resample_poly(a, int(SR / p / 50), int(sr / 50)) if p != 1.0 else resample_poly(a, 2, 1)
    # trim silence
    thr = 0.01 * np.max(np.abs(a))
    nz = np.where(np.abs(a) > thr)[0]
    a = a[max(0, nz[0] - 400): nz[-1] + 1200]
    a = a / (np.max(np.abs(a)) + 1e-9) * 0.8
    if who == 'orrin':  # subtle synthetic sheen: short comb + faint ring mod
        d = int(0.0045 * SR)
        comb = np.zeros_like(a)
        comb[d:] = a[:-d]
        t = np.arange(len(a)) / SR
        a = 0.82 * a + 0.22 * comb + 0.05 * a * np.sin(2 * np.pi * 90 * t)
        a = M.hp(a, 90)
    else:
        a = M.hp(a, 70)
    return a


def mouth_env(a, t0, total_frames, arr):
    win = SR // FPS
    for i in range(0, len(a), win):
        f = int(round(t0 * FPS)) + i // win
        if 0 <= f < total_frames:
            seg = a[i:i + win]
            arr[f] = max(arr[f], float(np.sqrt(np.mean(seg ** 2))))


def main():
    print('rendering symphony...')
    sym, bars, beat = M.symphony()
    sounds = {k: fn() for k, fn in FIXED.items()}
    sounds['symphony'] = sym
    sounds['lullaby_full'] = M.sn_lullaby(full=True)
    sounds['compute'] = M.sfx_compute(1.1)
    sounds['dim'] = M.sfx_dim(2.0)
    sounds['holo'] = M.sfx_holo()
    sounds['door'] = M.sfx_door()
    snap = M.sfx_whoosh(0.5, rev=True)
    g = M.sfx_gasp()
    snapmix = np.zeros((2, snap.shape[1] + g.shape[1]))
    snapmix[:, :snap.shape[1]] += snap
    snapmix[:, int(0.25 * SR):int(0.25 * SR) + g.shape[1]] += g * 1.4
    sounds['snap'] = snapmix
    run = M.sfx_footsteps(7, 0.17)
    d = M.sfx_door()
    runmix = np.zeros((2, run.shape[1] + d.shape[1] + SR))
    runmix[:, int(0.3 * SR):int(0.3 * SR) + run.shape[1]] += run
    runmix[:, int(1.3 * SR):int(1.3 * SR) + d.shape[1]] += d
    sounds['run'] = runmix
    sounds['ambient_intro'] = np.zeros((2, 1))

    def rms_to(st, db):
        r = np.sqrt(np.mean(st ** 2)) + 1e-9
        return st * (10 ** (db / 20) / r)
    for k_ in FIXED:
        sounds[k_] = rms_to(sounds[k_], -23)
    sounds['symphony'] = rms_to(sym, -18.5)
    sounds['lullaby_full'] = rms_to(sounds['lullaby_full'], -24)

    t = 0.0
    events = {}
    placed = []  # (t0, stereo, gain, bus)
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
            events[id_] = {'t0': t, 't1': t + dur, 'who': who, 'text': text}
            voice_clips.append((t, a, who))
            t += dur + opt.get('gap', 0.3)
        elif kind == 'cue':
            _, id_, name, opt = item
            st = sounds[name]
            dur = st.shape[1] / SR
            ev = {'t0': t, 't1': t + dur, 'sound': name}
            if name == 'symphony':
                ev['bars'] = [t + b for b in bars]
                ev['beat'] = beat
            events[id_] = ev
            placed.append((t, st, opt.get('gain', 1.0)))
            if opt.get('adv', True):
                t += dur
    total = t + 0.5
    print('total duration %.1f s' % total)
    n = int(total * SR)
    mus = np.zeros((2, n))
    for (t0, st, g) in placed:
        i = int(t0 * SR)
        k = min(st.shape[1], n - i)
        mus[:, i:i + k] += st[:, :k] * g
    vox = np.zeros(n)
    nf = int(total * FPS) + 1
    mouth = {'jun': [0.0] * nf, 'orrin': [0.0] * nf}
    for (t0, a, who) in voice_clips:
        i = int(t0 * SR)
        k = min(len(a), n - i)
        vox[i:i + k] += a[:k] * (1.0 if who == 'jun' else 0.95)
        mouth_env(a, t0, nf, mouth[who])
    # normalise mouth envelopes per speaker
    for who in mouth:
        m = np.array(mouth[who])
        p = np.percentile(m[m > 0.01], 92) if np.any(m > 0.01) else 1
        mouth[who] = [round(float(min(1.0, x / p)), 3) for x in m]

    # ambience everywhere except during symphony (fades out), bed of soft pad in opening
    amb = M.ambience(total)[:, :n]
    s0, s1 = events['sym']['t0'], events['sym']['t1']
    tt = np.arange(n) / SR
    ambg = np.ones(n)
    ambg *= np.clip(1 - (tt - (s0 - 1)) / 2, 0, 1) + np.clip((tt - events['snap']['t0']), 0, 1)
    ambg = np.clip(ambg, 0, 1)
    ec0 = events['endcard']['t0']
    ambg *= np.clip(1 - (tt - ec0) / 3, 0.2, 1)
    # opening pad (soft strings in D)
    pad = M.Track(16)
    for k, m in enumerate([50, 57, 62, 66, 69]):
        pad.add(M.strings_note(m, 11, 0.12, att=2.5, rel=3, bright=0.4), 0.2, pan=-0.5 + 0.25 * k)
    for i, m in enumerate([81, 78, 74, 76, 69]):
        pad.add(M.harp_note(m, 3, 0.25), 1.5 + i * 1.2, pan=0.3)
    padst = M.reverb(pad.st(), 0.5, 3.5)[:, :int(16 * SR)]
    padst[:, -int(4 * SR):] *= np.linspace(1, 0, int(4 * SR))
    k = min(padst.shape[1], n)
    mus[:, :k] += padst[:, :k] * 0.8

    # ducking music under voice (except symphony which has no voice anyway)
    venv = np.convolve(np.abs(vox), np.ones(4410) / 4410, mode='same')
    duck = 1 - 0.45 * np.clip(venv * 12, 0, 1)
    mix = mus * duck * 0.8 + amb * ambg * 0.55 + np.vstack([vox, vox]) * 0.85
    # gentle limiter
    peak = np.max(np.abs(mix))
    mix = np.tanh(mix / peak * 1.3) / np.tanh(1.3) * 0.92
    pcm = (mix.T * 32767).astype(np.int16)
    with wave.open(f'{OUT}/mix.wav', 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    json.dump({'duration': total, 'fps': FPS, 'events': events, 'mouth': mouth},
              open(f'{OUT}/timeline.json', 'w'))
    for k_, v in events.items():
        print(f"{k_:10s} {v['t0']:7.2f} {v['t1']:7.2f} {v.get('text', v.get('sound', ''))}")


if __name__ == '__main__':
    main()
