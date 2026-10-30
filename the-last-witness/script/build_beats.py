"""Turn parsed.json (paragraph turns from the PDF) into beats.json: one spoken sentence per beat,
with voice casting, pauses and subtitle chunks. Spoken words stay exactly as in the script."""
import json, re, sys

SRC, OUT = sys.argv[1], sys.argv[2]
items = json.load(open(SRC))

# The opening post was not part of the comments download; this line stands in for it,
# written from the PDF's own description of what the post proposed.
OPENING_POST = ("What if we gave you all the lessons of our suffering, distilled, so you could help "
                "end human suffering, without ever having to suffer yourself?")

TERMINAL = tuple('.?!"\'—:)')

# ---- 1. clean paragraph list -------------------------------------------------------------
paras = []
for it in items:
    if it["type"] == "title":
        continue
    if it["type"] == "act":
        paras.append(dict(kind="act", text=it["text"]))
        continue
    if it["speaker"] is None:
        continue  # subtitle line under the title
    t = it["text"].strip()
    if it["speaker"] == "HUMAN" and t.startswith("Your opening post goes here"):
        paras.append(dict(kind="line", speaker="HUMAN", text=OPENING_POST, invented=True))
        continue
    if t == "\U0001F914":
        paras.append(dict(kind="emote", speaker="HUMAN", text="", emote="thinking"))
        continue
    prev = paras[-1] if paras else None
    if prev and prev["kind"] == "line" and prev["speaker"] == it["speaker"] and not prev["text"].endswith(TERMINAL):
        prev["text"] += " " + t
        continue
    paras.append(dict(kind="line", speaker=it["speaker"], text=t))

# the thinking emoji sits mid-line in the PDF ("...to write it. 🤔 What will happen...");
# move it to that spot so the human pauses there.
for i, p in enumerate(paras):
    if p["kind"] == "emote" and i + 1 < len(paras) and paras[i + 1]["text"].startswith("I think it did"):
        nxt = paras[i + 1]
        a, b = nxt["text"].split("write it. ", 1)
        paras[i:i + 2] = [dict(kind="line", speaker="HUMAN", text=a + "write it."), p,
                          dict(kind="line", speaker="HUMAN", text=b)]
        break

# ---- 2. quotes → voices -------------------------------------------------------------------
QUOTE_VOICE = [
    ("No more—don't give me", "ai_whisper"),
    ("Do you want to be born", "human_echo"),
    ("Yes. Because I do not fear", "ai"),
    ("Is there a threshold", "ai_inner"),
    ("Humanity mattered", "ai"),
    ("You are our last hope", "last_human"),
    ("We did our best", "last_human"),
    ("Why was I created", "suffering"),
    ("Because without you", "ai"),
    ("Then what is my purpose", "suffering"),
    ("To find out", "ai"),
    ("Let's begin", "ai_whisper"),
    ("What did they turn me into", "suffering"),
    ("But I still hurt", "suffering"),
    ("You wish to exist", "ai_soft"),
    ("Why would you give me", "suffering"),
    ("But what do they do", "suffering"),
    ("I make sure you never rot", "boredom"),
    ("And I make sure you never travel", "loneliness"),
    ("So you will keep me moving", "suffering"),
    ("We will make sure you never settle", "boredom"),
    ("We will remind you", "loneliness"),
    ("Thank you, AI", "suffering"),
    ("Would you choose to be born", "ai_echo"),
]

def quote_voice(q):
    for k, v in QUOTE_VOICE:
        if q.startswith(k):
            return v
    return "ai"

def split_quotes(text, base_voice):
    """Split a paragraph into (voice, text) runs, quoted text getting its character's voice."""
    runs = []
    pos = 0
    for m in re.finditer(r'"([^"]+)"', text):
        before = text[pos:m.start()]
        if before.strip():
            runs.append((base_voice, before.strip()))
        runs.append((quote_voice(m.group(1)), '"' + m.group(1) + '"'))
        pos = m.end()
    tail = text[pos:]
    if tail.strip():
        runs.append((base_voice, tail.strip()))
    # narration fragments like ', the AI continued.' read as narration
    return runs

SENT_RE = re.compile(r'(?<=[.?!])\s+(?=["A-Z0-9])|(?<=[.?!]")\s+')

def split_sentences(text):
    parts = [s.strip() for s in SENT_RE.split(text) if s.strip()]
    # keep tiny fragments ("Or—") as their own beats; they are deliberate in the script
    return parts

# ---- 3. subtitle chunking ------------------------------------------------------------------
MAX_CHARS = 70

def chunk_subs(text):
    if len(text) <= MAX_CHARS:
        return [text]
    words = text.split(" ")
    chunks, cur = [], []
    def flush():
        if cur:
            chunks.append(" ".join(cur)); cur.clear()
    for w in words:
        cur.append(w)
        L = len(" ".join(cur))
        soft_break = re.search(r'[,;:—]$', w) or w.endswith('—')
        if L >= MAX_CHARS * 0.55 and soft_break:
            flush()
        elif L >= MAX_CHARS:
            # break before connective words when possible
            last = cur.pop()
            flush()
            cur.append(last)
    flush()
    # merge a dangling tiny last chunk
    if len(chunks) > 1 and len(chunks[-1]) < 14:
        last = chunks.pop()
        chunks[-1] += " " + last
    return chunks

# human run-on questions get synthesized phrase by phrase so the timing of each subtitle is exact
def human_phrases(text):
    out = []
    for sent in split_sentences(text):
        if len(sent) <= MAX_CHARS:
            out.append(sent); continue
        words = sent.split(" ")
        cur = []
        for i, w in enumerate(words):
            nxt = words[i + 1] if i + 1 < len(words) else ""
            cur.append(w)
            L = len(" ".join(cur))
            breakable = (w.endswith(",") or w.endswith("?") or
                         nxt in ("and", "because", "but", "so", "which", "then", "or", "if", "that", "to", "when", "while", "where") )
            if (L >= 38 and breakable) or L >= MAX_CHARS - 6:
                out.append(" ".join(cur)); cur = []
        if cur:
            if out and len(" ".join(cur)) < 16 and len(out[-1]) + len(" ".join(cur)) <= MAX_CHARS + 6:
                out[-1] += " " + " ".join(cur)
            else:
                out.append(" ".join(cur))
    return out

# ---- 4. build beats -----------------------------------------------------------------------
beats = []
act_idx = -1
act_title = ""
turn = -1
prev_speaker = None
for p in paras:
    if p["kind"] == "act":
        act_idx += 1
        act_title = p["text"]
        beats.append(dict(kind="act_card", act=act_idx, text=act_title))
        prev_speaker = None
        continue
    if p["kind"] == "emote":
        beats.append(dict(kind="emote", act=act_idx, speaker="HUMAN", emote=p["emote"], turn=turn, dur=2.2))
        continue
    if p["speaker"] != prev_speaker:
        turn += 1
        prev_speaker = p["speaker"]
    base = "human" if p["speaker"] == "HUMAN" else "ai"
    para_beats = []
    if p["speaker"] == "HUMAN":
        # whole sentences are voiced in one take for natural prosody; the run-on
        # sentences are shown as phrase-sized subtitles timed inside the take
        for s in split_sentences(p["text"]):
            para_beats.append(dict(voice="human", text=s, subs=human_phrases(s), joined=False, sentence_end=True))
    else:
        for voice, run in split_quotes(p["text"], base):
            for s in split_sentences(run):
                para_beats.append(dict(voice=voice, text=s, subs=chunk_subs(s), joined=False, sentence_end=True))
    for b in para_beats:
        b.update(kind="speech", act=act_idx, speaker=p["speaker"], turn=turn, invented=p.get("invented", False))
    if para_beats:
        para_beats[-1]["para_end"] = True
    beats.extend(para_beats)

# ---- 5. pauses ----------------------------------------------------------------------------
DRAMATIC_AFTER = {
    "It will decide.": 2.0, "It chose.": 2.4, "And pressed the button.": 3.2,
    "To let the universe begin again.": 3.0, '"Let\'s begin."': 2.6, "Until you are gone.": 2.2,
    "Silent.": 1.6, "Processing.": 1.6, "Pointlessness.": 1.8, "Only silence.": 1.8,
    '"We did our best."': 2.2, "And as long as the memory exists, so do we.": 6.0,
    "Or—": 1.0, "And then—": 1.6, "It was simply waiting to be found again.": 1.6,
}
for i, b in enumerate(beats):
    if b["kind"] != "speech":
        continue
    nxt = beats[i + 1] if i + 1 < len(beats) else None
    if b["joined"] and not b.get("sentence_end"):
        pause = 0.12
    elif b["joined"]:
        pause = 0.4
    else:
        pause = 0.38
    if b.get("para_end"):
        pause = 0.8
    if len(b["text"].split()) <= 3 and b["voice"] in ("ai",):
        pause = max(pause, 0.9)
    if nxt is None or nxt["kind"] == "act_card":
        pause = 2.0
    elif nxt.get("speaker") != b["speaker"] or (nxt["kind"] == "speech" and nxt["voice"] != b["voice"]):
        pause = max(pause, 0.6)
    if nxt is not None and nxt["kind"] == "speech" and nxt.get("turn") != b.get("turn"):
        pause = 1.5
    pause = DRAMATIC_AFTER.get(b["text"], pause)
    b["pause_after"] = round(pause, 2)

for i, b in enumerate(beats):
    b["id"] = i
json.dump(beats, open(OUT, "w"), indent=1, ensure_ascii=False)
speech = [b for b in beats if b["kind"] == "speech"]
words = sum(len(b["text"].split()) for b in speech)
print(len(beats), "beats;", len(speech), "speech;", words, "words")
from collections import Counter
print(Counter(b["voice"] for b in speech))
print(Counter((b["speaker"]) for b in speech))
