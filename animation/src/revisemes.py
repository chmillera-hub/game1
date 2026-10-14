"""Recompute the visemes in lines.json from the stored audio and phoneme timings.

Usage: python3 revisemes.py voices_dir
(no re-synthesis: use after changing tts.visemes or its phoneme table)
"""
import json
import os
import sys

import soundfile as sf

sys.path.insert(0, os.path.dirname(__file__))
import tts  # noqa: E402


def main(vdir):
    path = os.path.join(vdir, 'lines.json')
    meta = json.load(open(path))
    for lid, r in meta.items():
        wav, sr = sf.read(os.path.join(vdir, lid + '.wav'), dtype='float32')
        assert sr == tts.SR
        tim = [tuple(x) for x in r['timings']]
        r['visemes'] = tts.visemes(tim, wav, fps=24)
    json.dump(meta, open(path, 'w'))
    print('recomputed', len(meta), 'lines')


if __name__ == '__main__':
    main(sys.argv[1])
