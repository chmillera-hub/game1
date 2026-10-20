"""score.py - compose the film score as MIDI and render it with fluidsynth.
Usage: python3 audio/score.py   (run from film root)
Inputs : build/timeline.json (shot moods, word-hit notes)
Outputs: build/midi/score.mid, build/music.wav (48 kHz stereo, length = timeline duration)
Grid: constant 80 bpm (bar = 3.0 s, 1 s = 480 ticks @60bpm MIDI clock); each bar takes the mood of
the shot at its midpoint. Key D major / B minor; 4-bar motif returns (solo piano -> full theme).
"""
import json, subprocess, numpy as np, soundfile as sf, mido, os
T = json.load(open('build/timeline.json')); DUR = T['duration']
TPS = 480  # ticks per second (tempo 60 bpm, tpb 480)
BEAT = 0.75; BAR = 4 * BEAT
ev = []  # (time_s, msg)
def note(ch, p, t0, d, v):
    v = int(max(1, min(127, v)))
    ev.append((t0, mido.Message('note_on', channel=ch, note=int(p), velocity=v)))
    ev.append((min(t0 + d, DUR), mido.Message('note_off', channel=ch, note=int(p), velocity=0)))
def cc(ch, c, val, t): ev.append((t, mido.Message('control_change', channel=ch, control=c, value=int(val))))
PROG = {0: 0, 1: 48, 2: 89, 3: 32, 4: 44, 5: 47, 6: 8, 7: 42, 8: 46, 10: 43, 11: 49}
# chords (root midi, quality)
CH = {'D': (50, [0, 4, 7]), 'G': (43, [0, 4, 7]), 'Bm': (47, [0, 3, 7]), 'A': (45, [0, 4, 7]),
      'Em': (52, [0, 3, 7]), 'F#': (42, [0, 4, 7]), 'Gmaj7': (43, [0, 4, 7, 11]), 'Dsus': (50, [0, 5, 7])}
MAJ = ['D', 'Bm', 'G', 'A']; MIN = ['Bm', 'G', 'D', 'A']; STORM = ['Bm', 'Bm', 'G', 'F#']
JAZZ = ['D', 'Bm', 'Em', 'A']
# motif: (beat offset, semitone above D5=74, beats)
MOTIF = [[(0, 4, 1), (1, 7, 1), (2, 9, 2)], [(0, 7, 1), (1, 4, 1), (2, 2, 2)],
         [(0, 4, 1), (1, 7, 1), (2, 11, 1), (3, 9, 1)], [(0, 7, 2), (2, 4, 1), (3, 2, 1)]]
def cue(m):
    m = m.lower()
    if 'storm' in m: return 'storm'
    if 'jazzy' in m or m.startswith('light'): return 'jazz'
    if m in ('awakening', 'uncertain', 'lonely', 'calm', 'empty', 'resolve begins'): return 'solo'
    if m in ('dark', 'sacrifice', 'grief', 'time passing', 'power down'): return 'low'
    if m in ('swell', 'warm', 'rebirth swell', 'fulfillment', 'joy', 'reprise', 'finale', 'title theme'): return 'full'
    return 'mid'  # resolve, montage, hope, wonder, tender, hush, rebirth, dawning hope
def mood_at(t):
    for s in T['shots']:
        if s['start'] <= t < s['end']: return s['mood']
    return T['shots'][-1]['mood']
nbar = int(np.ceil(DUR / BAR)); chord_at = {}
prev = None; k = 0
for b in range(nbar):
    t0 = b * BAR; c = cue(mood_at(t0 + BAR / 2))
    if c != prev: k = 0
    prog = {'storm': STORM, 'low': MIN, 'jazz': JAZZ}.get(c, MAJ)
    name = prog[k % 4]; last = t0 + BAR >= DUR - 0.01
    if last: name = 'D'
    root, iv = CH[name]; chord_at[b] = (root, iv)
    d = DUR - t0 if last else BAR
    tones = [root + i for i in iv]
    if c == 'solo':
        for j, p in enumerate([root - 12, tones[1] + 12, tones[2] + 12, tones[0] + 24]):
            note(0, p, t0 + j * BEAT, BAR - j * BEAT if not last else d, 48 - 6 * (j == 0))
        note(2, root, t0, d, 30); [note(2, p + 12, t0, d, 26) for p in tones[1:]]
        if k % 8 < 4: [note(0, 74 + s, t0 + o * BEAT, l * BEAT, 52) for o, s, l in MOTIF[k % 4]]
    elif c == 'jazz':
        walk = [root - 12, root - 12 + iv[1], root - 12 + 7, root - 12 + 9]
        for j, p in enumerate(walk): note(3, p, t0 + j * BEAT, BEAT * .9, 70)
        for j in range(4):  # brushed feel: ride + soft snare swish
            note(9, 51, t0 + j * BEAT, .2, 34); note(9, 40, t0 + j * BEAT + BEAT * .66, .1, 22)
        for j in (1, 3): [note(0, p + 12, t0 + j * BEAT + .1, .4, 44) for p in tones]
        if k % 4 == 0: [note(0, 74 + s, t0 + o * BEAT, l * BEAT, 50) for o, s, l in MOTIF[k // 4 % 4]]
    elif c == 'low':
        note(1, root - 12, t0, d, 44); note(1, tones[2] - 12 if root > 47 else tones[2], t0, d, 38)
        note(2, root, t0, d, 32); [note(2, p + 12, t0, d, 26) for p in tones[1:]]
        note(0, root - 24, t0, 2.5, 36)
        if k % 2 == 1: note(0, tones[1] + 24, t0 + 2 * BEAT, 2, 34)
    elif c == 'storm':
        note(4, root - 12, t0, d, 70); note(4, root, t0, d, 62); note(4, tones[2], t0, d, 56)
        note(10, root - 24, t0, d, 60)
        for r in range(12): note(5, 38 if name != 'G' else 43, t0 + 2.0 + r * .08, .08, 40 + r * 4)
        note(5, 38 if name != 'G' else 43, t0, .5, 80)
    else:  # mid / full
        full = c == 'full'
        note(1, root - 12, t0, d, 50 + 10 * full); [note(1, p + 12, t0, d, 44 + 10 * full) for p in tones[1:]]
        note(2, root, t0, d, 34)
        if full: note(11, tones[0] + 24, t0, d, 46); note(10, root - 24, t0, d, 50)
        for j, p in enumerate([root - 12, tones[2], tones[1] + 12, tones[2] + 12, tones[0] + 24, tones[2] + 12, tones[1] + 12, tones[2]]):
            note(0, p, t0 + j * BEAT / 2, BEAT if not last else d, 42 + 8 * full)
        if full or k % 8 < 4:
            [note(0, 74 + s, t0 + o * BEAT, l * BEAT, 60 + 6 * full) for o, s, l in MOTIF[k % 4]]
            if full: [note(1, 62 + s, t0 + o * BEAT, l * BEAT, 52) for o, s, l in MOTIF[k % 4]]
    prev = c; k += 1
# word hits
for n in T['notes']:
    t = n['t']; root, iv = chord_at[min(int(t // BAR), nbar - 1)]
    pcs = [(root + i) % 12 for i in iv]
    if n['type'] == 'high':
        cand = sorted(p for p in range(79, 100) if p % 12 in pcs)[:4]
        for j, p in enumerate(cand):
            note(6, p, t + j * .09, 1.4, 50 - 3 * j); note(8, p - 12, t + j * .09, 1.6, 40)
    else:
        r = root % 12 + 26
        note(7, r + 12, t, 2.6, 58); note(10, r, t, 2.8, 52); note(0, r + 12, t, 2.0, 46)
mid = mido.MidiFile(ticks_per_beat=480); tr = mido.MidiTrack(); mid.tracks.append(tr)
tr.append(mido.MetaMessage('set_tempo', tempo=1000000))
for ch, p in PROG.items():
    tr.append(mido.Message('program_change', channel=ch, program=p))
    tr.append(mido.Message('control_change', channel=ch, control=91, value=60))
tr.append(mido.Message('control_change', channel=7, control=7, value=110))
ev.sort(key=lambda e: (e[0], e[1].type == 'note_on'))
last = 0
for t, m in ev:
    tk = int(round(t * TPS)); tr.append(m.copy(time=tk - last)); last = tk
os.makedirs('build/midi', exist_ok=True); mid.save('build/midi/score.mid')
subprocess.run(['fluidsynth', '-ni', '-g', '0.6', '-r', '48000', '-F', 'build/music_raw.wav',
                '/usr/share/sounds/sf2/FluidR3_GM.sf2', 'build/midi/score.mid'], check=True, capture_output=True)
a, sr = sf.read('build/music_raw.wav'); N = int(round(DUR * 48000))
a = a[:N] if len(a) >= N else np.vstack([a, np.zeros((N - len(a), 2))])
f = int(.15 * sr); a[-f:] *= np.linspace(1, 0, f)[:, None] ** .5  # ring to the end, tiny click guard
sf.write('build/music.wav', a.astype(np.float32), 48000, subtype='FLOAT'); os.remove('build/music_raw.wav')
print('music', a.shape, 'peak', np.abs(a).max())
