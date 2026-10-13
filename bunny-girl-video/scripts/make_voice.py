"""Read the story aloud with Kokoro TTS, then shift it to a child-like voice.

Writes build/narration.wav (48 kHz mono) and build/timeline.json with the
start/end of every page and every caption word.

Needs: kokoro (Apache-2.0 model hexgrad/Kokoro-82M), soundfile, numpy,
scipy, and the `rubberband` command line tool.
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from story import SCENES  # noqa: E402

BUILD = os.path.join(os.path.dirname(HERE), "build")
SR = 24000
VOICE = "af_heart"
SPEED = 0.86
LEAD_IN = 0.35          # title is on screen at frame 0; voice starts just after
# child-like voice: move formants up 2.8 semitones (shorter vocal tract) and
# pitch up 5 semitones in total
FORMANT_ST = 2.8
PITCH_ST = 5.0


def norm(w):
    return re.sub(r"[^a-z0-9'\-]", "", w.lower().replace("’", "'"))


def trim(audio):
    """Cut leading/trailing silence, keep a little air around the words."""
    env = np.abs(audio)
    thr = env.max() * 10 ** (-42 / 20)
    idx = np.where(env > thr)[0]
    a = max(0, idx[0] - int(0.04 * SR))
    b = min(len(audio), idx[-1] + int(0.12 * SR))
    return audio[a:b], a / SR


def main():
    from kokoro import KPipeline

    os.makedirs(BUILD, exist_ok=True)
    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")

    pieces = [np.zeros(int(LEAD_IN * SR), np.float32)]
    t = LEAD_IN
    timeline = []
    for scene in SCENES:
        sc = dict(id=scene["id"], pages=[])
        for page in scene["pages"]:
            text = page.get("say", page["show"])
            audio, tokens, off = [], [], 0.0
            for r in pipe(text, voice=VOICE, speed=SPEED):
                a = r.audio.numpy().astype(np.float32)
                for tk in r.tokens:
                    if tk.start_ts is not None and norm(tk.text):
                        tokens.append((tk.text, off + tk.start_ts, off + tk.end_ts))
                audio.append(a)
                off += len(a) / SR
            audio = np.concatenate(audio)
            audio, cut = trim(audio)
            dur = len(audio) / SR

            # match caption words to spoken tokens, in order
            words = []
            toks = [(norm(x), s - cut, e - cut) for x, s, e in tokens]
            ti = 0
            for w in page["show"].split():
                key = norm(w)
                if not key:
                    continue
                j = ti
                while j < len(toks) and toks[j][0] != key:
                    j += 1
                if j < len(toks):
                    _, s, e = toks[j]
                    ti = j + 1
                else:  # fall back to the previous word's end
                    s = e = words[-1]["end"] - t if words else 0.0
                    print("  ! no token for", w, "in", repr(text))
                words.append(dict(w=w, start=round(t + max(s, 0), 3),
                                  end=round(t + min(e, dur), 3)))
            # fill gaps so each word stays lit until the next one starts
            for k in range(len(words) - 1):
                words[k]["end"] = max(words[k]["end"], words[k + 1]["start"])

            sc["pages"].append(dict(show=page["show"], start=round(t, 3),
                                    end=round(t + dur, 3), words=words))
            pieces.append(audio)
            pause = page.get("pause", 0.45)
            pieces.append(np.zeros(int(pause * SR), np.float32))
            t += dur + pause
            print(f"{scene['id']:10s} {t:7.2f}s  {page['show'][:60]}")
        timeline.append(sc)

    raw = np.concatenate(pieces)
    raw = raw / np.abs(raw).max() * 0.9
    raw_path = os.path.join(BUILD, "narration_adult.wav")
    sf.write(raw_path, raw, SR)

    # two-step shift: (1) formants+pitch together, (2) pitch only
    step1 = os.path.join(BUILD, "narration_step1.wav")
    kid = os.path.join(BUILD, "narration_kid24k.wav")
    subprocess.run(["rubberband", "-q", "-3", "-p", str(FORMANT_ST), raw_path, step1], check=True)
    subprocess.run(["rubberband", "-q", "-3", "-F", "-p", str(PITCH_ST - FORMANT_ST), step1, kid], check=True)
    audio, _ = sf.read(kid, dtype="float32")
    audio = resample_poly(audio, 2, 1).astype(np.float32)  # 24 kHz -> 48 kHz
    audio = audio / np.abs(audio).max() * 0.9
    sf.write(os.path.join(BUILD, "narration.wav"), audio, 48000)
    os.remove(step1)

    total = len(audio) / 48000
    with open(os.path.join(BUILD, "timeline.json"), "w") as f:
        json.dump(dict(duration=round(total, 3), scenes=timeline), f, indent=1)
    print("narration length %.2fs" % total)


if __name__ == "__main__":
    main()
