"""Voice acting: turns script.json into one WAV per line plus build/timeline.json.

The timeline holds every scene's and line's start/end time and a per-frame
mouth envelope (openness + width) for lip sync. Everything else (animation,
music, captions, sound effects) is timed from this file, so editing a line in
script.json and re-running the pipeline re-syncs the whole video.
"""
import json, os, sys
import numpy as np
import soundfile as sf
from scipy.signal import resample, butter, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, 'build')
VOICE_DIR = os.path.join(BUILD, 'voice')
MODELS = os.path.join(HERE, '.cache', 'models')
DEFAULT_GAP = 0.35  # pause between consecutive lines when "pre" is not given


def trim(sig, sr, thresh=0.012, pad=0.04):
    env = np.abs(sig)
    idx = np.where(env > thresh)[0]
    if len(idx) == 0:
        return sig
    a = max(0, idx[0] - int(pad * sr))
    b = min(len(sig), idx[-1] + int(pad * 1.5 * sr))
    out = sig[a:b].copy()
    f = int(0.01 * sr)
    out[:f] *= np.linspace(0, 1, f)
    out[-f:] *= np.linspace(1, 0, f)
    return out


def mouth_envelope(sig, sr, fps):
    """Per-frame mouth openness (loudness) and width (brightness of the sound)."""
    hop = sr / fps
    n = int(np.ceil(len(sig) / hop))
    hp = sosfilt(butter(4, 2200, 'hp', fs=sr, output='sos'), sig)
    rms, hi = np.zeros(n), np.zeros(n)
    for i in range(n):
        a, b = int(i * hop), int(min(len(sig), (i + 1) * hop + hop * 0.5))
        seg = sig[a:b]
        if len(seg) == 0:
            continue
        rms[i] = np.sqrt(np.mean(seg ** 2))
        hi[i] = np.sqrt(np.mean(hp[a:b] ** 2))
    ref = np.percentile(rms, 92) + 1e-6
    op = np.clip(rms / ref, 0, 1.15) ** 0.8
    # light smoothing so the mouth doesn't flicker frame to frame
    op = np.convolve(op, [0.25, 0.5, 0.25], mode='same')
    op[op < 0.08] = 0
    width = np.clip(hi / (rms + 1e-6) * 2.2, 0, 1)
    return [round(float(x), 2) for x in op], [round(float(x), 2) for x in width]


def main():
    script = json.load(open(os.path.join(HERE, 'script.json')))
    fps = script['fps']
    os.makedirs(VOICE_DIR, exist_ok=True)
    only = set(sys.argv[1:])  # optionally re-voice just some line ids

    from kokoro_onnx import Kokoro
    kokoro = Kokoro(os.path.join(MODELS, 'kokoro-v1.0.onnx'), os.path.join(MODELS, 'voices-v1.0.bin'))

    t = 0.0
    timeline = {'fps': fps, 'scenes': [], 'lines': {}}
    for scene in script['scenes']:
        sc = {'id': scene['id'], 'start': round(t, 3), 'lines': []}
        t += scene.get('lead', 0.5)
        for i, line in enumerate(scene['lines']):
            cast = script['voices'][line['spk']]
            path = os.path.join(VOICE_DIR, line['id'] + '.wav')
            text = line.get('tts', line['text'])
            speed = line.get('speed', cast['speed'])
            rate = cast.get('rate', 1.0)
            # cache key: only re-voice a line when its words or voice settings change
            key = json.dumps([text, cast['voice'], speed, rate])
            key_path = path + '.key'
            cached = os.path.exists(path) and os.path.exists(key_path) and open(key_path).read() == key
            if not cached or line['id'] in only:
                samples, sr = kokoro.create(text, voice=cast['voice'], speed=speed, lang='en-us')
                samples = trim(np.asarray(samples, dtype=np.float32), sr)
                if rate != 1.0:  # "tape slow-down": a little lower and slower
                    samples = resample(samples, int(len(samples) / rate)).astype(np.float32)
                sf.write(path, samples, sr)
                open(key_path, 'w').write(key)
                print(f"voiced {line['id']:10s} {len(samples)/sr:5.2f}s  {text[:60]}")
            samples, sr = sf.read(path, dtype='float32')
            if i > 0 or 'pre' in line:
                t += line.get('pre', DEFAULT_GAP if i > 0 else 0)
            dur = len(samples) / sr
            op, wd = mouth_envelope(samples, sr, fps)
            timeline['lines'][line['id']] = {
                'id': line['id'], 'spk': line['spk'], 'scene': scene['id'],
                'text': line['text'], 'start': round(t, 3), 'end': round(t + dur, 3),
                'dur': round(dur, 3), 'open': op, 'width': wd,
            }
            sc['lines'].append(line['id'])
            t += dur
        t += scene.get('tail', 0.5)
        sc['end'] = round(t, 3)
        timeline['scenes'].append(sc)
    timeline['duration'] = round(t, 3)
    json.dump(timeline, open(os.path.join(BUILD, 'timeline.json'), 'w'))
    for sc in timeline['scenes']:
        print(f"{sc['id']:8s} {sc['start']:7.2f} -> {sc['end']:7.2f}  ({sc['end']-sc['start']:.1f}s)")
    print(f"TOTAL {t:.2f}s = {int(t//60)}:{t%60:04.1f}")


if __name__ == '__main__':
    main()
