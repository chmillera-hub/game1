"""Synthesize every spoken beat with Kokoro, then give each character
their own colour of voice (pitch / formant / vibrato) with ffmpeg.

Writes build/voice/NNN.wav (48 kHz mono) and build/voice/NNN.json holding
word timings, so the timeline can sync subtitles, stingers and reactions.
"""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

from story import BEATS, VOICES

OUT = os.path.join(os.path.dirname(__file__), 'build', 'voice')


def synth(pipes, spk, text, speed):
    v = VOICES[spk]
    pipe = pipes[v['lang']]
    audio, words, offset = [], [], 0.0
    for r in pipe(text, voice=v['voice'], speed=v['speed'] * speed):
        a = r.audio.numpy().astype(np.float32)
        for t in r.tokens or []:
            if t.start_ts is None or not any(c.isalnum() for c in t.text):
                continue
            words.append((t.text, offset + t.start_ts, offset + (t.end_ts or t.start_ts)))
        audio.append(a)
        offset += len(a) / 24000
    return np.concatenate(audio), words


def colour(src, dst, spk, pitch):
    v = VOICES[spk]
    ratio = 2 ** ((v['semitones'] + pitch) / 12)
    chain = [f"rubberband=pitch={ratio:.5f}:formant={v['formants']}:transients=smooth"]
    chain += ['aresample=48000', 'highpass=f=70']
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-af', ','.join(chain),
                    '-ac', '1', '-c:a', 'pcm_f32le', dst], check=True)


def vibrato(x, depth, rate=5.2, sr=48000):
    """Warble the pitch by about +/-depth/4 (ffmpeg's vibrato filter emits NaNs here)."""
    t = np.arange(len(x)) / sr
    wobble = 1 + 0.35 * np.sin(2 * np.pi * 0.37 * t)          # uneven, like an old voice
    delay = (depth / 4) / (2 * np.pi * rate) * (1 + np.sin(2 * np.pi * rate * t)) * wobble
    pos = np.clip(np.arange(len(x)) - delay * sr, 0, len(x) - 1)
    return np.interp(pos, np.arange(len(x)), x).astype(np.float32)


def main():
    from kokoro import KPipeline
    os.makedirs(OUT, exist_ok=True)
    pipes = {'a': KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M'),
             'b': KPipeline(lang_code='b', repo_id='hexgrad/Kokoro-82M')}
    for i, b in enumerate(BEATS):
        if 'say' not in b:
            continue
        spk, text = b['say']
        key = json.dumps([spk, text, b.get('speed', 1), b.get('pitch', 0), VOICES[spk]])
        meta_path = os.path.join(OUT, f'{i:03d}.json')
        wav_path = os.path.join(OUT, f'{i:03d}.wav')
        if os.path.exists(meta_path) and json.load(open(meta_path)).get('key') == key:
            continue
        audio, words = synth(pipes, spk, text, b.get('speed', 1.0))
        raw = os.path.join(OUT, f'{i:03d}_raw.wav')
        sf.write(raw, audio, 24000)
        colour(raw, wav_path, spk, b.get('pitch', 0.0))
        os.remove(raw)
        a48, _ = sf.read(wav_path, dtype='float32')
        if VOICES[spk]['vibrato']:
            a48 = vibrato(a48, VOICES[spk]['vibrato'])
        # trim Kokoro's leading/trailing silence so beats butt together tightly
        env = np.abs(a48)
        loud = np.nonzero(env > 0.01)[0]
        lead = max(0, loud[0] - int(0.03 * 48000)) if len(loud) else 0
        tail = min(len(a48), loud[-1] + int(0.12 * 48000)) if len(loud) else len(a48)
        a48 = a48[lead:tail]
        sf.write(wav_path, a48, 48000, subtype='FLOAT')
        shift = lead / 48000
        words = [(w, max(0.0, s - shift), max(0.0, e - shift)) for w, s, e in words]
        json.dump({'key': key, 'dur': len(a48) / 48000, 'words': words},
                  open(meta_path, 'w'), indent=0)
        print(f'{i:03d} {spk} {len(a48)/48000:5.2f}s  {text[:60]}', file=sys.stderr)


if __name__ == '__main__':
    main()
