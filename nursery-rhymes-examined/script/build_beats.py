"""script.txt -> beats.json: one beat per spoken sentence, part titles and sound cues.
Spoken words and subtitles keep the script's exact text."""
import json, re, sys

SRC, OUT = sys.argv[1], sys.argv[2]
raw = open(SRC).read().replace("’", "'")

# The on-screen part titles leave out the real person's name the headings attribute the text to.
def title_of(heading):
    m = re.search(r'on "(.+?)":', heading)
    return f'On “{m.group(1)}”' if m else heading

parts = [p.strip() for p in raw.split("\n...\n") if p.strip()]
SENT_RE = re.compile(r"(?<=[.?!])\s+(?=[\"'A-Z])|(?<=[.?!]')\s+(?=[A-Z'])")
MAX = 68

def chunk(text):
    if len(text) <= MAX:
        return [text]
    words, out, cur = text.split(" "), [], []
    for w in words:
        cur.append(w)
        L = len(" ".join(cur))
        if (L >= MAX * 0.5 and re.search(r"[,;:–]$|^–$", w)) or L >= MAX:
            if L >= MAX and len(cur) > 1:
                last = cur.pop(); out.append(" ".join(cur)); cur = [last]
            else:
                out.append(" ".join(cur)); cur = []
    if cur:
        out.append(" ".join(cur))
    if len(out) > 1 and len(out[-1]) < 14:
        last = out.pop(); out[-1] += " " + last
    return out

DRAMATIC = {
    "Observe the bus.": 1.3, "The answer, I suspect, is a void, an empty driver's seat.": 1.6,
    "One day, the singing will abruptly cease.": 2.8, "The 'Itsy-Bitsy Spider.'": 1.2,
    "The 'rain,' you see, is not mere water.": 1.2, "The cycle is complete, only to begin anew.": 1.3,
}
beats = []
for pi, part in enumerate(parts):
    lines = part.split("\n")
    heading, cue = lines[0].strip(), lines[1].strip()
    body = "\n".join(lines[2:]).strip().strip('"')
    beats.append(dict(kind="title", part=pi, text=title_of(heading), heading=heading, sound=cue.strip("()")))
    paras = [p.strip().strip('"') for p in body.split("\n\n") if p.strip()]
    for qi, para in enumerate(paras):
        sents = [s.strip() for s in SENT_RE.split(para) if s.strip()]
        for si, s in enumerate(sents):
            last_in_para = si == len(sents) - 1
            pause = 1.15 if last_in_para else 0.6
            if last_in_para and qi == len(paras) - 1:
                pause = 3.2 if pi == 0 else 6.0
            pause = DRAMATIC.get(s, pause)
            beats.append(dict(kind="speech", part=pi, para=qi, voice="narrator", speaker="NARRATOR",
                              text=s, subs=chunk(s), pause_after=pause))
for i, b in enumerate(beats):
    b["id"] = i
json.dump(beats, open(OUT, "w"), indent=1, ensure_ascii=False)
sp = [b for b in beats if b["kind"] == "speech"]
print(len(beats), "beats,", len(sp), "sentences,", sum(len(b["text"].split()) for b in sp), "words")
for b in beats:
    print(b["id"], b["kind"], "|", b["text"][:90])
