"""Write ../SCRIPT.md (every line with its timestamp in the video)."""
from screenplay import build

NAMES = {'narr': 'NARRATOR (you)', 'me': 'YOU', 'anger': 'ANGER', 'doubt': 'DOUBT', 'boredom': 'BOREDOM',
         'stranger': 'AUDIENCE MEMBER', 'gemini': 'GEMINI BOT'}
SCENES = [(0, 'Intro: the theater inside your head'), (27, 'The first joke'), (59, 'The spiral'),
          (86.5, 'Anger loses it'), (117, 'The random audience member'), (136, 'Grabbing Anger by the shoulders'),
          (157, 'The sniper jokes'), (183, 'The thousand-yard stare'), (206, 'Laughing'),
          (221, 'The reveal: "the boss of comedy"'), (250, 'The heart of it'), (280, 'The button')]


def ts(t):
    return '%d:%04.1f' % (int(t // 60), t % 60)


if __name__ == '__main__':
    tl = build()
    out = ['# Anger Goes to a Comedy Show: script with timestamps', '',
           f'Runtime {ts(tl.end)}. Times are where each line starts in the video.', '']
    si = 0
    for ln in tl.lines:
        while si < len(SCENES) and ln['t0'] >= SCENES[si][0]:
            out += ['', f'## {SCENES[si][1]}', '']
            si += 1
        out.append(f'- `{ts(ln["t0"])}` **{NAMES[ln["speaker"]]}:** {ln["caption"] or "*(laughing)*"}')
    open('../SCRIPT.md', 'w').write('\n'.join(out) + '\n')
    print('wrote SCRIPT.md', ts(tl.end))
