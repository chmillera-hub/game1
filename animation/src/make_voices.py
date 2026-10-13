"""Generate every voiced line (wav + phoneme timings + visemes).

Usage: python3 make_voices.py lines.txt out_dir
lines.txt rows: ID|SPEAKER[speed]|text      e.g.  L035|E0.83|That was Walter's.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import tts  # noqa: E402

VOICES = {
    # narrator: flat, unhurried municipal information-film voice
    'N': dict(mix={'bm_lewis': 0.6, 'bm_george': 0.4}, speed=0.92, pitch=-1.0, formant=True),
    # Oswald: warm, smaller than his body
    'O': dict(mix={'am_michael': 0.8, 'am_puck': 0.2}, speed=0.92, pitch=-0.5, formant=True),
    # Edith: warm, plain, pauses do the acting; age from speed and breath, not pitch
    'E': dict(mix={'af_heart': 1.0}, speed=0.88, pitch=-1.0, formant=True),
    # Tomas: deeper, gruff
    'T': dict(mix={'am_fenrir': 0.85, 'am_onyx': 0.15}, speed=0.95, pitch=-1.0, formant=True),
    # Teddy: a child (formants move on the first pass, preserved on the second)
    'K': dict(mix={'am_puck': 0.5, 'af_heart': 0.5}, speed=1.05, pitch=2.0, formant=False, pitch2=1.0),
}


def parse(path):
    rows = []
    for ln in open(path):
        ln = ln.rstrip('\n')
        if not ln.strip() or ln.startswith('#'):
            continue
        lid, sp, txt, sub, trim, flags = (ln.split('|') + ['', '', ''])[:6]
        speed = float(sp[1:]) if len(sp) > 1 else None
        rows.append(dict(id=lid, spk=sp[0], speed=speed, tts=txt, sub=sub or txt, trim=trim, flags=flags))
    return rows


def main(path, out):
    os.makedirs(out, exist_ok=True)
    meta = {}
    for row in parse(path):
        v = dict(VOICES[row['spk']])
        if row['speed']:
            v['speed'] = row['speed']
        hushed = 'hushed' in row['flags']
        r = tts.make_line(row['tts'], v, os.path.join(out, row['id'] + '.wav'), trim_spec=row['trim'] or None, hushed=hushed)
        r.update(speaker=row['spk'], id=row['id'], subtitle=row['sub'], hushed=hushed)
        meta[row['id']] = r
        print('%s %s %.2fs  %s' % (row['id'], row['spk'], r['dur'], row['sub']))
    json.dump(meta, open(os.path.join(out, 'lines.json'), 'w'))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
