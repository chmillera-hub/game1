"""Burned-in subtitles, name supers and the end card for "Brindle Cross" (ASS).

Usage: python3 subs.py timeline.json out.ass

Reads timeline['subs'] ({t0, t1, text, style 'narr'|'dlg'}), timeline['labels']
({t0, t1, title, desc, correct}) and timeline['shots'] and writes one ASS script for
the 540x960 frame. Layout is phone first (app UI covers the bottom ~20 %):

  subtitles  centred, side margins 36 px, Inter 31, bottom of the last line at
             y=712 (74 %), so one line sits at 71-74 % and two at 68-74 % (below the
             mouths in the low close-ups of Edith).
             'narr' is cream italic, 'dlg' white regular; soft 2 px outline plus a
             faint shadow, no box. Lines are broken here, at the most natural
             balanced point that fits (sentence ends and commas first).
  supers     left at x=36: letter-spaced Inter SemiBold title (box 504-530), a brass
             rule that draws in from the left, italic description (540-560), i.e.
             52-58 %, clear of the subtitles. Fade 250 ms in, 300 ms out.
             'correct' {t, text} retypes the description from t, one character
             every 45 ms, the original characters staying put; the super is held
             1.2 s past the last keystroke (within its shot) so the change reads.
  end card   the last label, centred on the black tail as a title card.

Timing: every event is snapped to the frame grid (fps from the timeline) and starts
at frame 1 or later, so frame 0 is always the clean picture. Subtitles linger 0.3 s
(never across a cut), get at least 1 s or 15 chars/s, close tiny gaps, and never
overlap: the earlier one ends 2 frames before the next (or butts against it, minimum
0.6 s); if even that is impossible both stay up, the earlier one raised.
"""
import json
import math
import re
import sys

from PIL import ImageFont

W, H = 540, 960
FONT_DIR = '/usr/share/fonts/opentype/inter/'
SIDE = 36

SUB_SIZE = 31
SUB_BOTTOM = 712
NARR_COLOUR = '&H00D8E8F2'      # warm cream (ASS colours are &HAABBGGRR)
DLG_COLOUR = '&H00FFFFFF'
OUTLINE = '&H30000000'
SHADOW = '&HA0000000'
SUB_TAGS = r'{\blur0.8}'

LINGER, MIN_READ, CPS = 0.3, 1.0, 15.0
MIN_SHOW, CHAIN = 0.6, 0.35
GAP_FRAMES = 2

TITLE_SIZE, TITLE_SPACING = 26, 3
DESC_SIZE = 20
TITLE_TOP, RULE_Y, DESC_TOP = 504, 535, 540
RULE_COLOUR = '&H0058B4E0'      # brass, like the clock bezel
FADE_IN, FADE_OUT = 250, 300
TYPE_STEP = 0.045
CORRECT_HOLD = 1.2              # the retyped description stays fully up this long before its fade

CARD_SIZE, CARD_SPACING, CARD_DESC_SIZE = 44, 8, 24
CARD_FADE_IN = 400

FACES = {
    'Inter': 'Inter-Regular.otf',
    'Inter Italic': 'Inter-Italic.otf',
    'Inter SemiBold': 'Inter-SemiBold.otf',
    'Inter Display SemiBold': 'InterDisplay-SemiBold.otf',
}

HEADER = """[Script Info]
Title: Brindle Cross - A Sunday in November
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
"""
STYLE = ('Style: {name},{font},{size},{colour},&H000000FF,{outline},{shadow},0,{italic},0,0,'
         '100,100,{spacing},0,1,{bord},{shad},{align},{side},{side},{mv},1')
EVENTS = """
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def styles():
    s = dict(outline=OUTLINE, shadow=SHADOW, side=SIDE, spacing=0, italic=0, bord=2, shad=1.2)
    rows = [
        dict(s, name='Narr', font='Inter', size=SUB_SIZE, colour=NARR_COLOUR, italic=-1,
             align=2, mv=H - SUB_BOTTOM),
        dict(s, name='Dlg', font='Inter', size=SUB_SIZE, colour=DLG_COLOUR, align=2, mv=H - SUB_BOTTOM),
        dict(s, name='Title', font='Inter SemiBold', size=TITLE_SIZE, colour='&H00F8F8F8',
             spacing=TITLE_SPACING, bord=1.6, shad=1, align=7, mv=0),
        dict(s, name='Desc', font='Inter', size=DESC_SIZE, colour=NARR_COLOUR, italic=-1,
             bord=1.4, shad=1, align=7, mv=0),
        dict(s, name='Rule', font='Inter', size=20, colour=RULE_COLOUR, bord=0.8, shad=0.8, align=7, mv=0),
        dict(s, name='Card', font='Inter Display SemiBold', size=CARD_SIZE, colour='&H00F8F8F8',
             spacing=CARD_SPACING, bord=1.5, shad=1, align=2, mv=0),
        dict(s, name='CardDesc', font='Inter', size=CARD_DESC_SIZE, colour=NARR_COLOUR, italic=-1,
             bord=1.2, shad=1, align=8, mv=0),
    ]
    return '\n'.join(STYLE.format(**r) for r in rows)


# ---------------------------------------------------------------- text

def typeset(text):
    """Typographic punctuation; the words themselves are untouched."""
    s = text.replace('\\N', '\n')
    s = '\n'.join(' '.join(p.split()) for p in s.split('\n'))
    s = re.sub(r'\.\s?\.\s?\.', '\u2026', s)
    s = s.replace('--', '\u2014')
    s = re.sub(r"'(em|cause|tis|twas|til|bout|round|n)\b", '\u2019\\1', s)
    s = re.sub(r"(^|[\s(\[\u2014\u2026\"])'", '\\1\u2018', s)
    s = s.replace("'", '\u2019')
    s = re.sub(r'(^|[\s(\[\u2014\u2026])"', '\\1\u201c', s)
    s = s.replace('"', '\u201d')
    # ASS override and escape characters cannot appear in dialogue text
    return s.replace('{', '(').replace('}', ')').replace('\\', '\u2216').strip()


_fonts = {}


def text_width(text, face, size, spacing=0.0):
    """Advance width in script pixels as libass lays it out (size = win ascent+descent)."""
    key = (face, size)
    if key not in _fonts:
        probe = ImageFont.truetype(FONT_DIR + FACES[face], 1000)
        em = size * 1000.0 / sum(probe.getmetrics())
        _fonts[key] = ImageFont.truetype(FONT_DIR + FACES[face], max(1, round(em * 4)))
    return _fonts[key].getlength(text) / 4.0 + spacing * len(text)


WEAK_END = {'a', 'an', 'the', 'to', 'of', 'and', 'or', 'i', 'my', 'his', 'her', 'your', 'at',
            'in', 'on', 'for', 'is', 'was', 'mr.', 'mrs.', 'it\u2019s', 'he\u2019d', 'that'}
GOOD_START = {'before', 'and', 'but', 'when', 'because', 'so', 'from', 'with', 'who', 'which'}


def break_score(top, bottom, wt, wb, maxw):
    last = top.split(' ')[-1].lower()
    first = bottom.split(' ')[0].lower()
    score = 0.6 * abs(wt - wb) / maxw
    if wt > wb:
        score += 0.05
    if top[-1] in '.?!\u2026':
        score -= 0.35
    elif top[-1] in ',;:\u2014':
        score -= 0.2
    if last in WEAK_END:
        score += 0.25
    if first in GOOD_START:
        score -= 0.1
    if first[:1] in '\u2014\u2013-':
        score += 1.0
    return score


def wrap(text, face, size, maxw=W - 2 * SIDE):
    """Split one paragraph into lines that fit maxw; two lines prefer a natural, balanced break."""
    if text_width(text, face, size) <= maxw:
        return [text]
    words = text.split(' ')
    best = None
    for i in range(1, len(words)):
        top, bottom = ' '.join(words[:i]), ' '.join(words[i:])
        wt, wb = text_width(top, face, size), text_width(bottom, face, size)
        over = max(wt, wb) - maxw
        score = break_score(top, bottom, wt, wb, maxw) + (10 + over / maxw if over > 0 else 0)
        if best is None or score < best[0]:
            best = (score, top, bottom, wt, wb)
    if best is None:
        return [text]
    _, top, bottom, wt, wb = best
    if wt > maxw and ' ' in top:
        return wrap(top, face, size, maxw) + [bottom]
    if wb > maxw and ' ' in bottom:
        return [top] + wrap(bottom, face, size, maxw)
    return [top, bottom]


def layout(text, face, size):
    return [ln for para in text.split('\n') for ln in wrap(para, face, size)]


# ---------------------------------------------------------------- timing

class Clock:
    """Snaps seconds to frames and frames to ASS centiseconds that libass shows on that frame."""

    def __init__(self, fps):
        self.fps = fps

    def frame(self, t):
        """First frame at or after t; times within float noise of a frame land on it."""
        x = t * self.fps
        n = round(x)
        return max(1, n if abs(x - n) < 1e-3 else math.ceil(x))

    def stamp(self, f):
        cs = int(math.floor(f * 100.0 / self.fps + 1e-9))
        return '%d:%02d:%02d.%02d' % (cs // 360000, cs // 6000 % 60, cs // 100 % 60, cs % 100)

    def event(self, layer, f0, f1, style, text, margin_v=0):
        """One Dialogue line shown on frames f0 .. f1-1 (None if empty)."""
        if f1 <= f0:
            return None
        return 'Dialogue: %d,%s,%s,%s,,0,0,%d,,%s' % (layer, self.stamp(f0), self.stamp(f1), style,
                                                      margin_v, text)


def time_subs(subs, cuts, gap):
    """Display interval for every subtitle: [(sub, t_start, t_end, stacked_under)]."""
    subs = sorted(subs, key=lambda s: s['t0'])
    out = []
    for i, s in enumerate(subs):
        t0, t1 = s['t0'], s['t1']
        nxt = subs[i + 1]['t0'] if i + 1 < len(subs) else None
        want = max(t1 + LINGER, t0 + max(MIN_READ, len(s['text']) / CPS))
        cut = next((c for c in cuts if t1 < c < want), None)
        if cut is not None:
            want = max(cut, t0 + MIN_SHOW)
        end, stacked = want, None
        if nxt is not None:
            limit = nxt - gap
            # closing the gap must not carry the line over a cut after its voice ended
            no_cut = not any(t1 < c <= limit + 1e-6 for c in cuts)
            if want > limit or (limit - want < CHAIN and no_cut):
                end = limit
            if end < t0 + MIN_SHOW:
                end = min(nxt, want)
            if end < t0 + MIN_SHOW:
                end, stacked = want, subs[i + 1]
        out.append((s, t0, end, stacked))
    return out


# ---------------------------------------------------------------- events

def sub_lines(sub):
    style = 'Narr' if sub.get('style') == 'narr' else 'Dlg'
    return style, layout(typeset(sub['text']), 'Inter Italic' if style == 'Narr' else 'Inter', SUB_SIZE)


def subtitle_events(clock, subs, cuts):
    events = []
    for s, t0, t1, stacked in time_subs(subs, cuts, GAP_FRAMES / clock.fps):
        style, lines = sub_lines(s)
        mv = H - SUB_BOTTOM
        if stacked is not None:
            mv += len(sub_lines(stacked)[1]) * SUB_SIZE + 6
        events.append(clock.event(0, clock.frame(t0), clock.frame(t1), style,
                                  SUB_TAGS + r'\N'.join(lines), margin_v=mv))
    return events


def rule(width, x, y, fad, centred=False):
    """A 2 px bar drawn with an ASS vector shape; it grows out from its anchor."""
    return (r'{\an%d\pos(%d,%d)\p1\fscx0\t(0,450,0.6,\fscx100)%s}m 0 0 l %d 0 %d 2 0 2{\p0}'
            % (5 if centred else 7, x, y, fad, width, width))


def typing_steps(old, new):
    """Strings shown while 'old' is retyped as 'new': backspace to the common prefix, then type."""
    n = 0
    while n < min(len(old), len(new)) and old[n] == new[n]:
        n += 1
    return [old[:k] for k in range(len(old) - 1, n - 1, -1)] + [new[:k] for k in range(n + 1, len(new) + 1)]


def super_events(clock, lab):
    """Lower-third name super: title, drawn-in rule, description (optionally retyped)."""
    title = typeset(lab['title']).upper()
    desc = typeset(lab.get('desc') or '')
    fad = r'\fad(%d,%d)' % (FADE_IN, FADE_OUT)
    f0, f1 = clock.frame(lab['t0']), clock.frame(lab['t1'])
    tw = text_width(title, 'Inter SemiBold', TITLE_SIZE, TITLE_SPACING) - TITLE_SPACING
    events = [
        clock.event(2, f0, f1, 'Title', r'{\pos(%d,%d)%s\blur0.6}%s' % (SIDE, TITLE_TOP, fad, title)),
        clock.event(1, f0, f1, 'Rule', rule(round(tw), SIDE, RULE_Y, fad)),
    ]
    if not desc:
        return events
    pos = r'\pos(%d,%d)\blur0.6' % (SIDE, DESC_TOP)
    corr = lab.get('correct')
    if not corr or not (lab['t0'] < corr['t'] < lab['t1']):
        events.append(clock.event(2, f0, f1, 'Desc', '{%s%s}%s' % (pos, fad, desc)))
        return events
    # the correction: one event per typed character, contiguous on the frame grid
    steps = typing_steps(desc, typeset(corr['text']))
    shown = [(f0, desc)]
    for k, txt in enumerate(steps):
        f = min(clock.frame(corr['t'] + k * TYPE_STEP), f1 - 1)
        if f == shown[-1][0]:
            shown[-1] = (f, txt)
        else:
            shown.append((f, txt))
    for k, (fa, txt) in enumerate(shown):
        fb = shown[k + 1][0] if k + 1 < len(shown) else f1
        fade = r'\fad(%d,0)' % FADE_IN if k == 0 else ''
        if k == len(shown) - 1:
            fade = r'\fad(0,%d)' % FADE_OUT if k else fad
        events.append(clock.event(2, fa, fb, 'Desc', '{%s%s}%s' % (pos, fade, txt)))
    return events


def card_events(clock, lab):
    """The end card: title, short rule and description centred on the frame."""
    title = typeset(lab['title']).upper()
    desc = typeset(lab.get('desc') or '')
    size = CARD_SIZE
    while text_width(title, 'Inter Display SemiBold', size, CARD_SPACING) > W - 2 * SIDE:
        size -= 1
    fad = r'\fad(%d,%d)' % (CARD_FADE_IN, FADE_OUT)
    f0, f1 = clock.frame(lab['t0']), clock.frame(lab['t1'])
    cx = W // 2
    # \fsp also pads after the last letter, so nudge the title right by half of it
    events = [
        clock.event(2, f0, f1, 'Card', r'{\pos(%g,%d)\fs%d%s\blur0.8}%s' % (
            cx + CARD_SPACING / 2.0, 478, size, fad, title)),
        clock.event(1, f0, f1, 'Rule', rule(40, cx, 491, fad, centred=True)),
    ]
    if desc:
        events.append(clock.event(2, f0, f1, 'CardDesc', r'{\pos(%d,%d)%s\blur0.8}%s' % (cx, 502, fad, desc)))
    return events


def hold_correction(lab, cuts, next_t0):
    """Stretch a super whose description is retyped, so the new text can be read before the fade.

    It stays at least CORRECT_HOLD after the last keystroke, but never past the next cut or the
    next super."""
    corr = lab.get('correct')
    if not corr or not (lab['t0'] < corr['t'] < lab['t1']):
        return
    n = len(typing_steps(typeset(lab.get('desc') or ''), typeset(corr['text'])))
    need = corr['t'] + n * TYPE_STEP + CORRECT_HOLD + FADE_OUT / 1000.0
    stops = [c for c in cuts if c > corr['t']][:1] + ([next_t0] if next_t0 is not None else [])
    lab['t1'] = max(lab['t1'], min([need] + stops))


def tidy_labels(labels, cuts):
    """Sort; a super that runs into the next one ends at its start, or at a cut just before it."""
    labels = [dict(lab) for lab in sorted(labels, key=lambda lab: lab['t0'])]
    for a, b in zip(labels, labels[1:]):
        if a['t1'] > b['t0']:
            a['t1'] = b['t0']
            near = [c for c in cuts if b['t0'] - 0.5 <= c <= b['t0'] and c > a['t0'] + 1.0]
            if near:
                a['t1'] = near[0]
    for i, lab in enumerate(labels):
        hold_correction(lab, cuts, labels[i + 1]['t0'] if i + 1 < len(labels) else None)
    return labels


def build(tl):
    clock = Clock(tl.get('fps', 24))
    cuts = sorted({round(s['t0'], 6) for s in tl.get('shots', []) if s['t0'] > 0})
    events = subtitle_events(clock, tl.get('subs', []), cuts)
    labels = tidy_labels(tl.get('labels', []), cuts)
    for i, lab in enumerate(labels):
        if i == len(labels) - 1:
            events += card_events(clock, lab)
        else:
            events += super_events(clock, lab)
    events = [e for e in events if e]
    return HEADER.format(w=W, h=H) + styles() + '\n' + EVENTS + '\n'.join(events) + '\n'


def main(timeline_path, out_path):
    tl = json.load(open(timeline_path))
    ass = build(tl)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(ass)
    n = ass.count('\nDialogue:')
    print('wrote %s (%d events)' % (out_path, n))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
