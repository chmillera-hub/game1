"""Export subtitles as SRT from the voice timeline."""
import sys
from common import TL, LINES

NAMES = {"N": "", "Z": "ZOMBIE: ", "HA": "PILOT: ", "HB": "CREW: "}


def ts(x):
    h, x = divmod(x, 3600)
    m, s = divmod(x, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s - int(s)) * 1000):03d}"


out, k = [], 1
for lid in TL["order"]:
    d = LINES[lid]
    for i, sb in enumerate(d["subs"]):
        end = sb["t1"] + (0.5 if i == len(d["subs"]) - 1 else 0.0)
        out.append(f"{k}\n{ts(sb['t0'])} --> {ts(end)}\n{NAMES[d['spk']]}{sb['text']}\n")
        k += 1
open(sys.argv[1], "w").write("\n".join(out))
print(k - 1, "cues")
