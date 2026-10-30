"""Parse the screenplay PDF into ordered paragraphs: headings, speaker labels, human (italic) and AI (regular) text."""
import json, sys
import pdfplumber

PDF = sys.argv[1]
OUT = sys.argv[2]

def classify(font):
    if "Bold" in font: return "bold"
    if "Italic" in font: return "italic"
    return "regular"

rows = []  # (page, top, x0, x1, style, size, text)
with pdfplumber.open(PDF) as pdf:
    for pi, page in enumerate(pdf.pages):
        words = page.extract_words(extra_attrs=["fontname", "size"], keep_blank_chars=False, use_text_flow=True)
        lines = {}
        for w in words:
            key = round(w["top"])
            lines.setdefault(key, []).append(w)
        for top in sorted(lines):
            ws = sorted(lines[top], key=lambda w: w["x0"])
            styles = [classify(w["fontname"]) for w in ws]
            style = max(set(styles), key=styles.count)
            rows.append(dict(page=pi, top=top, x0=ws[0]["x0"], x1=ws[-1]["x1"], style=style,
                             size=round(ws[0]["size"], 1), text=" ".join(w["text"] for w in ws),
                             first_w=ws[0]["x1"] - ws[0]["x0"]))

paras = []
cur = None
RIGHT_MARGIN = 542  # a line was wrapped if the next line's first word would not have fit after it
for i, r in enumerate(rows):
    nxt = rows[i + 1] if i + 1 < len(rows) else None
    if r["style"] == "bold":
        if cur: paras.append(cur); cur = None
        t = r["text"]
        if r["size"] >= 15:
            kind = "title" if r["size"] > 20 else "act"
        elif t.startswith("THE HUMAN"):
            kind = "label_human"
        elif t.startswith("THE AI"):
            kind = "label_ai"
        else:
            kind = "other"
        paras.append(dict(kind=kind, text=t))
        continue
    if cur and cur["style"] == r["style"] and cur["wrap"]:
        cur["text"] += " " + r["text"]
    else:
        if cur: paras.append(cur)
        cur = dict(kind="text", style=r["style"], text=r["text"])
    cur["wrap"] = bool(nxt) and (r["x1"] + 3.5 + nxt["first_w"] > RIGHT_MARGIN)
if cur: paras.append(cur)

# assemble into speaker turns
out = []
act = None
speaker = None
for p in paras:
    if p["kind"] == "act":
        act = p["text"]; out.append(dict(type="act", text=act)); continue
    if p["kind"] == "title":
        out.append(dict(type="title", text=p["text"])); continue
    if p["kind"] == "label_human": speaker = "HUMAN"; continue
    if p["kind"] == "label_ai": speaker = "AI"; continue
    if p["kind"] == "text":
        t = p["text"].replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
        t = t.replace("- ", "-") if False else t
        out.append(dict(type="line", act=act, speaker=speaker, style=p["style"], text=t))
json.dump(out, open(OUT, "w"), indent=1, ensure_ascii=False)
print(len(out), "items")
