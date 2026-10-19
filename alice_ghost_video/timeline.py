"""Lay the beats out on a clock.

Reads the story plus the synthesized voice timings and writes
build/timeline.json: when every scene, shot, emotion, gaze, action,
stinger, spoken line and subtitle happens.
"""
import json
import os
import re

from story import BEATS

HERE = os.path.dirname(__file__)
VOICE = os.path.join(HERE, 'build', 'voice')

MAX_SUB_CHARS = 58        # two comfortable lines on a phone


def norm(w):
    return re.sub(r'[^a-z0-9]', '', w.lower())


def align(text, tokens):
    """Give every space-separated word of `text` (punctuation kept) a time span."""
    words = text.split()
    out, k = [], 0
    for w in words:
        target, got, start, end = norm(w), '', None, None
        while k < len(tokens) and len(got) < len(target):
            t, s, e = tokens[k]
            if start is None:
                start = s
            got += norm(t)
            end = e
            k += 1
        if start is None:                      # ran out of tokens: reuse the last end
            start = end = out[-1][2] if out else 0.0
        out.append((w, start, end))
    return out


def chunk_subs(timed):
    """Split one line into subtitle chunks, preferring breaks after punctuation."""
    chunks, cur = [], []
    for i, item in enumerate(timed):
        cur.append(item)
        length = len(' '.join(w for w, _, _ in cur))
        last = i == len(timed) - 1
        nxt = '' if last else ' '.join(w for w, _, _ in cur + [timed[i + 1]])
        brk = item[0][-1] in '.?!,…' or item[0].endswith('...')
        if last or len(nxt) > MAX_SUB_CHARS or (brk and length > 26 and item[0][-1] in '.?!'):
            chunks.append(cur)
            cur = []
    # avoid a lonely one-word orphan chunk
    if len(chunks) > 1 and len(chunks[-1]) == 1 and len(
            ' '.join(w for w, _, _ in chunks[-2] + chunks[-1])) <= MAX_SUB_CHARS + 8:
        tail = chunks.pop()
        chunks[-1] += tail
    return chunks


def main():
    tl = dict(fps=24, scenes=[], shots=[], emo={'A': [], 'S': []}, gaze={'A': [], 'S': []},
              pos={'A': [], 'S': []}, acts=[], stingers=[], speech=[], subs=[], beats=[], words=[])

    def apply(t, d):
        for key, val in d.items():
            if key in ('A', 'S'):
                tl['emo'][key].append((t, val))
            elif key.endswith('.gaze'):
                tl['gaze'][key[0]].append((t, val))
            elif key.endswith('.pos'):
                tl['pos'][key[0]].append((t, val))
            elif key in ('hi', 'lo'):
                tl['stingers'].append((t, key, val))
            elif key == 'act':
                tl['acts'].append((t, val, 0.0))

    t = 0.0
    for i, b in enumerate(BEATS):
        t += b.get('pre', 0.0)
        start = t
        if 'scene' in b:
            tl['scenes'].append((start, b['scene']))
        if 'shot' in b:
            tl['shots'].append((start, b['shot']))
        apply(start, b.get('emo', {}))
        if 'say' in b:
            spk, text = b['say']
            meta = json.load(open(os.path.join(VOICE, f'{i:03d}.json')))
            dur = meta['dur']
            timed = align(text, meta['words'])
            tl['speech'].append((start, spk, i, dur, b.get('gain', 1.0)))
            for w, s, e in timed:
                tl['words'].append((start + s, start + e, spk, w))
            chunks = chunk_subs(timed)
            for ci, ch in enumerate(chunks):
                s0 = start + ch[0][1] - 0.08
                s1 = start + ch[-1][2] + 0.35
                if ci + 1 < len(chunks):
                    s1 = min(s1, start + chunks[ci + 1][0][1] - 0.08)
                tl['subs'].append([s0, s1, spk, ' '.join(w for w, _, _ in ch)])
            k = 0
            for word, d in b.get('cues', []):
                target = norm(word)
                while k < len(timed) and not norm(timed[k][0]).startswith(target):
                    k += 1
                if k == len(timed):
                    raise SystemExit(f'beat {i}: cue word {word!r} not found in {text!r}')
                apply(start + timed[k][1], d)
                k += 1
        else:
            dur = b['dur']
        if 'act' in b:
            tl['acts'].append((start, b['act'], dur))
        tl['beats'].append((start, start + dur, i))
        t = start + dur + b.get('post', 0.0)

    # subtitles of consecutive lines must not overlap, and keep a minimum on-screen time
    subs = sorted(tl['subs'])
    for a, b in zip(subs, subs[1:]):
        a[1] = min(max(a[1], a[0] + 1.0), b[0] - 0.02)
    tl['subs'] = subs
    tl['duration'] = t
    for k in ('emo', 'gaze', 'pos'):
        for c in tl[k]:
            tl[k][c].sort(key=lambda e: e[0])
    tl['acts'].sort(key=lambda e: e[0])
    json.dump(tl, open(os.path.join(HERE, 'build', 'timeline.json'), 'w'), indent=1)
    print(f'duration {t:.1f}s, {len(tl["subs"])} subtitles, {len(tl["stingers"])} stingers')


if __name__ == '__main__':
    main()
