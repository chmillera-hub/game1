"""Subtitles from build/timeline.json.
Usage: python3 audio/subs.py  -> writes build/subs.ass (720x1280, burn with ffmpeg -vf ass=) and build/subs.srt.
Chunks lines by word timing (<=30 chars, break at punctuation, wrap to 2 lines >22 chars).
Chunk shows [first word start-0.05, last word end+0.25], clipped to never overlap the next chunk.
Styles per speaker: keeper, directive ('▸ ' mono cyan), narrator (italic), mira, grandpa. Centered at y=925."""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TL = json.load(open(os.path.join(ROOT, 'build/timeline.json')))
MAXC, WRAP = 30, 22

def chunks(words):
    out, cur = [], []
    for i, w in enumerate(words):
        txt = ' '.join(x['w'] for x in cur + [w])
        if cur and len(txt) > MAXC:
            out.append(cur); cur = []
        cur.append(w)
        t = ' '.join(x['w'] for x in cur)
        if re.search(r'[.!?;:,—…]["\')]*$', w['w']) and (len(t) >= 12 or re.search(r'[.!?]', w['w'][-1:])):
            out.append(cur); cur = []
    if cur:
        if out and len(' '.join(x['w'] for x in out[-1] + cur)) <= MAXC and len(cur) == 1:
            out[-1] += cur
        else: out.append(cur)
    # avoid orphan single word after an overflow split: borrow the previous chunk's last word
    for i in range(1, len(out)):
        if len(out[i]) == 1 and len(out[i-1]) >= 3 and not re.search(r'[.!?,;:\u2014\u2026]$', out[i-1][-1]['w']):
            out[i].insert(0, out[i-1].pop())
    return out

def wrap(t):
    if len(t) <= WRAP: return [t]
    ws = t.split(' '); best = None
    for k in range(1, len(ws)):
        a, b = ' '.join(ws[:k]), ' '.join(ws[k:]); s = max(len(a), len(b))
        if best is None or s < best[0]: best = (s, [a, b])
    return best[1] if best else [t]

items = []
for sh in TL['shots']:
    for ln in sh.get('lines', []):
        ws = ln.get('words') or [{'w': ln['text'], 'start': ln['start'], 'end': ln['end']}]
        for c in chunks(ws):
            items.append({'sp': ln['speaker'], 'text': ' '.join(x['w'] for x in c),
                          'a': max(0, c[0]['start'] - 0.05), 'b': c[-1]['end'] + 0.25})
items.sort(key=lambda x: x['a'])
for i in range(len(items) - 1):
    items[i]['b'] = min(items[i]['b'], items[i + 1]['a'] - 0.01)

def ts_ass(t):
    cs = int(round(t * 100)); return f"{cs//360000}:{cs//6000%60:02d}:{cs//100%60:02d}.{cs%100:02d}"
def ts_srt(t):
    ms = int(round(t * 1000)); return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"
def col(h): return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}".upper()

# Name, font, size, colour, bold, italic
ST = {'keeper': ('Inter SemiBold', 40, 'ffffff', 0, 0), 'directive': ('JetBrains Mono', 34, '7fe7ff', 1, 0),
      'narrator': ('Inter SemiBold', 40, 'fff3e0', 0, 1), 'mira': ('Inter SemiBold', 40, 'ffe9a8', 0, 0),
      'grandpa': ('Inter SemiBold', 40, 'f3d9c0', 0, 0)}
hdr = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 720", "PlayResY: 1280", "WrapStyle: 2",
       "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
       "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"]
for n, (f, s, c, b, it) in ST.items():
    hdr.append(f"Style: {n},{f},{s},{col(c)},&H000000FF,&H00140A0A,&H80000000,{-1 if b else 0},{-1 if it else 0},"
               f"0,0,100,100,0,0,1,3,2,5,30,30,0,1")
hdr += ["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
srt = []
for i, it in enumerate(items):
    sp = it['sp'] if it['sp'] in ST else 'keeper'
    txt = ('▸ ' if sp == 'directive' else '') + it['text']
    lines = wrap(txt)
    hdr.append(f"Dialogue: 0,{ts_ass(it['a'])},{ts_ass(it['b'])},{sp},,0,0,0,,{{\\an5\\pos(360,925)\\blur0.6}}" + r'\N'.join(lines))
    srt.append(f"{i+1}\n{ts_srt(it['a'])} --> {ts_srt(it['b'])}\n" + '\n'.join(lines) + "\n")
open(os.path.join(ROOT, 'build/subs.ass'), 'w').write('\n'.join(hdr) + '\n')
open(os.path.join(ROOT, 'build/subs.srt'), 'w').write('\n'.join(srt))
print(f"subs: {len(items)} chunks")
