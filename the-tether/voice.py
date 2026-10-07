"""Synthesize every spoken line with Piper TTS and lay out the film's timeline.

Each script entry waits `gap` seconds after the previous entry *ends*, so the
picture (film.html) can key its animation off named markers instead of
hard-coded times. Output: build/voice/*.wav and build/timeline.json (+ .js).
"""
import json, os, subprocess, sys, wave

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build")
VOICE_DIR = os.path.join(OUT, "voice")
os.makedirs(VOICE_DIR, exist_ok=True)

VOICES = {
    # who: (model, length_scale, noise_scale, noise_w)
    "N": ("en_GB-alan-medium", 1.22, 0.55, 0.7),   # narrator
    "J": ("en_US-ryan-high", 1.32, 0.75, 0.9),     # Jesus, whispered aloud
    "I": ("en_US-ryan-high", 1.25, 0.6, 0.8),      # Jesus, inner voice
    "G1": ("en_US-lessac-high", 1.1, 0.6, 0.8),    # ghost phrase, layered
    "G2": ("en_GB-alan-medium", 1.15, 0.6, 0.8),
    "G3": ("en_US-ryan-high", 1.05, 0.6, 0.8),
}

# (kind, who/name, text, gap-before)
SCRIPT = [
    ("mark", "open", None, 0.0),
    ("say", "N", "There is a place inside him... where he thinks without words.", 5.0),
    ("say", "N", "No walls. No temple. Only atmosphere. Dark, and glowing, all at once.", 1.6),
    ("say", "N", "A stillness that breathes... like a storm cloud, holding its lightning.", 1.4),
    ("mark", "jesus", None, 1.0),
    ("say", "N", "He is not on a throne. He is not robed in light.", 3.0),
    ("say", "N", "Just plain clothes, worn by the earth. And a halo that flickers. Not broken... just tired.", 1.4),
    ("say", "N", "He is not standing. He is crawling.", 1.6),
    ("mark", "father", None, 5.0),
    ("say", "N", "And ahead of him... stands the Father.", 2.4),
    ("say", "N", "Older than time. Vast as a thunderhead, split open by the sun.", 1.4),
    ("say", "N", "Arms crossed. Silent. He does not look down.", 1.4),
    ("say", "N", "His gaze is locked on the far edge of the void... on things that live beyond the present moment.", 1.4),
    ("mark", "plea", None, 2.5),
    ("say", "J", "This hurts.", 2.6),
    ("say", "J", "This loneliness... hurts.", 1.8),
    ("say", "J", "The world is so empty sometimes. I feel like the last heartbeat... echoing across a dying field.", 1.8),
    ("say", "J", "What am I supposed to do?", 1.8),
    ("say", "J", "How do I help anyone... when I feel like this?", 1.6),
    ("mark", "ghost", None, 2.0),
    ("ghost", "G", "Give it to God.", 0.0),
    ("say", "N", "A whisper so familiar, it almost feels automatic.", 4.6),
    ("say", "N", "The Father is right there. He could let it go... like a dropped stone.", 1.4),
    ("mark", "hover", None, 0.0),
    ("mark", "withdraw", None, 4.2),
    ("say", "N", "But he doesn't.", 0.4),
    ("mark", "curl", None, 1.0),
    ("say", "N", "Not in defeat. In containment. Like he is holding something sacred.", 4.8),
    ("mark", "inner", None, 1.0),
    ("say", "I", "If I give this away... I'll lose the thread.", 1.0),
    ("say", "I", "I'll forget what I'm fighting for. I'll slip back into the haze. Scrolling. Smiling. Numb.", 1.4),
    ("mark", "thread", None, 0.6),
    ("say", "I", "But if I stay with it... if I hold it long enough...", 1.0),
    ("say", "I", "maybe I'll see what this pain is trying to teach me. Not just for me. For them.", 1.0),
    ("mark", "tether", None, 1.6),
    ("say", "N", "He doesn't want to keep it. But the pain is the tether. The ache is the compass.", 0.4),
    ("say", "N", "And something in him believes the Father knows that too.", 1.4),
    ("mark", "grief", None, 0.6),
    ("say", "N", "That the silence isn't neglect. It's space. Trust.", 1.0),
    ("say", "N", "Maybe... even grief.", 1.8),
    ("mark", "pullback", None, 3.2),
    ("say", "N", "And the frame widens...", 3.0),
    ("say", "N", "until there is only a titan of light, staring into cosmic silence...", 3.0),
    ("say", "N", "and a single son, curled on the floor beneath him... groaning a prayer without words.", 2.0),
    ("mark", "fade", None, 4.0),
    ("mark", "title", None, 3.0),
    ("mark", "end", None, 8.0),
]


def synth(who, text, path):
    model, ls, ns, nw = VOICES[who]
    if not os.path.exists(path):
        subprocess.run(
            [sys.executable, "-m", "piper", "-m", os.path.join(HERE, "voices", model + ".onnx"),
             "-f", path, "--length-scale", str(ls), "--noise-scale", str(ns),
             "--noise-w-scale", str(nw), "--sentence-silence", "0.35"],
            input=text.encode(), check=True, capture_output=True)
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def envelope(path, fps=30):
    import numpy as np
    with wave.open(path) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    hop = sr // fps
    n = len(x) // hop
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    rms = np.clip(rms / (rms.max() + 1e-9), 0, 1) ** 0.6
    return [round(float(v), 2) for v in rms]


def main():
    t = 0.0
    cues, marks = [], {}
    for i, (kind, who, text, gap) in enumerate(SCRIPT):
        t += gap
        if kind == "mark":
            marks[who] = round(t, 3)
            continue
        if kind == "ghost":
            # Three voices saying the same phrase, staggered; the cue spans all of them.
            parts, end = [], t
            for j, (g, off) in enumerate([("G1", 0.0), ("G2", 0.9), ("G3", 1.9), ("G1", 3.0)]):
                path = os.path.join(VOICE_DIR, f"{i:02d}_{g}_{j}.wav")
                d = synth(g, text, path)
                parts.append({"file": os.path.relpath(path, OUT), "start": round(t + off, 3), "dur": round(d, 3), "who": g})
                end = max(end, t + off + d)
            cues.append({"who": "G", "text": text, "start": round(t, 3), "dur": round(end - t, 3), "parts": parts})
            t = end
            continue
        path = os.path.join(VOICE_DIR, f"{i:02d}_{who}.wav")
        d = synth(who, text, path)
        cues.append({"who": who, "text": text, "start": round(t, 3), "dur": round(d, 3),
                     "file": os.path.relpath(path, OUT)})
        t += d
    # Mouth envelope (30 fps RMS, 0..1) for the lines Jesus speaks aloud.
    for c in cues:
        if c["who"] == "J":
            c["env"] = envelope(os.path.join(OUT, c["file"]))

    m = marks
    # Lightning: (time, strength 0..1, where). "far" = distant storm cloud,
    # "father" = inside the Father's body. Thunder in audio.py follows these.
    flashes = [
        (3.2, 0.35, "far"), (9.9, 0.5, "far"), (16.6, 0.3, "far"), (23.4, 0.6, "far"),
        (m["jesus"] + 9.5, 0.3, "far"), (m["jesus"] + 21.0, 0.35, "far"),
        (m["father"] + 1.3, 1.0, "father"), (m["father"] + 9.0, 0.55, "father"),
        (m["father"] + 17.5, 0.7, "father"), (m["father"] + 24.8, 0.45, "father"),
        (m["ghost"] + 0.4, 0.5, "father"), (m["ghost"] + 11.0, 0.35, "far"),
        (m["withdraw"] + 0.5, 0.45, "father"), (m["inner"] + 4.0, 0.3, "far"),
        (m["tether"] + 3.0, 0.55, "father"), (m["pullback"] + 6.0, 0.4, "father"),
        (m["pullback"] + 16.5, 0.3, "far"),
    ]
    timeline = {"duration": marks["end"], "marks": marks, "cues": cues,
                "flashes": [{"t": round(t, 3), "s": s, "where": w} for t, s, w in flashes]}
    with open(os.path.join(OUT, "timeline.json"), "w") as f:
        json.dump(timeline, f, indent=1)
    with open(os.path.join(OUT, "timeline.js"), "w") as f:
        f.write("window.TIMELINE = " + json.dumps(timeline) + ";\n")
    print(f"duration {marks['end']:.1f}s")
    for k, v in marks.items():
        print(f"  {k:9s} {v:7.2f}")


if __name__ == "__main__":
    main()
