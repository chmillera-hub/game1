#!/usr/bin/env python3
"""THE STONE AND THE BREAD -- dialogue casting, synthesis, placement and the film's timing truth.

    python3 film/audio/tts.py                  # synthesize MISSING line wavs, then (re)write film/timeline.json
    python3 film/audio/tts.py --force          # re-synthesize every line (deterministic: fixed per-part seeds)
    python3 film/audio/tts.py --force --only s4_l1 s6_laugh
    python3 film/audio/tts.py --check          # validate film/timeline.json + the wavs (assertions only)

Outputs
  film/assets/dialogue/<line_id>.wav   DRY voice (no fx), 48 kHz mono 16-bit, leading/trailing silence trimmed
                                       to 20 ms, 6 ms / 10 ms raised-cosine edge fades, every line normalised to
                                       -20 LUFS integrated (BS.1770 K-weighting), true sample peak <= -1 dBFS.
                                       The committed wavs are the source of truth: they are only re-made with
                                       --force (manifest.json beside them records exactly how each was made and
                                       this script warns when a wav is stale against its spec).
  film/timeline.json                   fps/size/total, cast, scenes, lines (+24 fps speech envelopes), beats.
                                       Written ONLY by this script.

Timing model
  line.start / line.end are LOCAL scene seconds of the wav's first / last sample (the voice onset is 20 ms
  after start, the offset 20 ms before end).  Place the wav at global_start in the mix.
  env[k] is the speech level at local time start + k/24 (Hann-weighted RMS over +-1/24 s, compressed,
  normalised per line to 0..1, gated to 0 below -30 dB re the line's p95 so mouths close in pauses).
  Each line's start is solved per scene (dynamic programming, 10 ms grid) to stay within +-1.0 s of the
  SPEC section 6 target, never overlap (>= 0.3 s apart), end >= 0.6 s before the scene ends, and keep
  conversational replies 0.4-0.9 s after the previous speaker.  Beats that depend on lines move with them.

Determinism
  Every synthesized part uses its own fresh ONNX session seeded with onnxruntime.set_seed(part.seed)
  (Piper's VITS noise is drawn from the session RNG), single-threaded for bit-stable numerics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import wave
import zlib
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from multiprocessing import get_context
from typing import Optional

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
ROOT = os.path.dirname(FILM)
VOICE_DIR = os.path.join(FILM, "build", "voices")
DIALOGUE_DIR = os.path.join(FILM, "assets", "dialogue")
MANIFEST = os.path.join(DIALOGUE_DIR, "manifest.json")
TIMELINE = os.path.join(FILM, "timeline.json")
SCRIPT_MD = os.path.join(FILM, "SCRIPT.md")
LOG_PATH = os.path.join(FILM, "build", "tts_log.json")

FPS, WIDTH, HEIGHT = 24, 1920, 1080
SR = 48000
EDGE = 0.020                 # silence kept before the voice onset / after the offset
FADE_IN, FADE_OUT = 0.006, 0.010
PART_EDGE = 0.010            # margin kept around each part before joining parts
TARGET_LUFS = -20.0
PEAK_CEIL_DB = -1.0
MIN_GAP = 0.30               # hard minimum silence between two lines of a scene
END_GUARD = 0.60             # lines end at least this long before the scene ends
NUDGE = 1.00                 # max |start - target|

SCENES = [  # id, name, global start, duration  (SPEC section 6; fixed)
    (1, "washhouse", 0.0, 25.0),
    (2, "apothecary", 25.0, 25.0),
    (3, "stone", 50.0, 20.0),
    (4, "tavern", 70.0, 25.0),
    (5, "crowd", 95.0, 25.0),
    (6, "bench", 120.0, 30.0),
    (7, "bread", 150.0, 30.0),
    (8, "close", 180.0, 20.0),
    (9, "endcard", 200.0, 10.0),
]
TOTAL = 210.0

# ================================================================================================
# CAST -- chosen by objective analysis (film/build/cast_scan.py + cast_deep.py; see notes)
# ================================================================================================
#   Measures: median F0 / F0 SD in semitones (YIN), speaking rate (syllables/s), HNR / H1-H2 / CPP
#   (breathiness), spectral centroid + LTAS tilt (warmth), Whisper small.en word errors + log-prob
#   (intelligibility), DNSMOS P.835 OVRL (quality), audeering wav2vec2 perceived age / gender.
#   Pool: all 14 single-speaker voices, all 904 LibriTTS-R and all 109 VCTK speakers (broad scan),
#   then role shortlists rendered on the role's own lines with several seeds.
CAST = {
    "MAN": dict(
        character="the dragon", model="en_US-hfc_male-medium", speaker_id=None,
        length_scale=1.05, noise_scale=0.667, noise_w=0.8,
        notes="US male (HiFi-Captain). Best of 26 male candidates rendered on 11 of his lines: median F0 "
              "~118 Hz (target 95-125), the most expressive of the field (F0 SD 4.1 st, not monotone), "
              "clearest diction (Whisper: 0 word errors, best mean log-prob -0.07) and best DNSMOS OVRL 3.43; "
              "perceived age ~34. Dialogue length_scale 1.05; the scene-8 voice-over uses 1.12 (vo=true, "
              "fx='vo': intimate, a touch of room reverb). Bright-ish timbre: a gentle -2 dB shelf above ~5 kHz "
              "warms the dragon in the mix. s4_l1 (fx='drowned') is cut off on purpose mid-breath "
              "('Lately I f-'); the tavern music swells from beat s4_swell to bury it. s6_laugh is five "
              "'hah' pulses of this same voice assembled into a real laugh bout (~1.2 s, pitch stepping down "
              "from ~196 to ~146 Hz, decrescendo): keep it MODERATE in the mix, about -3 to -4 dB under his "
              "dialogue level, never louder than the lines around it."),
    "PHARMACIST": dict(
        character="the lioness", model="en_US-libritts_r-medium", speaker_id=515,
        length_scale=1.06, noise_scale=0.5, noise_w=0.6,
        notes="LibriTTS-R reader 5139. Soft and warm: dark timbre (spectral centroid ~300 Hz, LTAS tilt "
              "-10.8 dB/oct) with soft, breathy phonation (H1-H2 +7.4 dB), median F0 ~196 Hz, perceived age "
              "~30, kind contour (F0 SD ~2.9 st). The only soft LibriTTS voice that never turned 'Try these' "
              "into 'Fry these' (6/6 Whisper-perfect renditions vs 3-4/6). Distinct from the gnome (30 Hz "
              "higher, ~25 years younger-sounding, darker, smoother) and from the stone (far less pitch "
              "movement, darker). length_scale 1.06, noise 0.5/0.6."),
    "PHONE": dict(
        character="the speaking stone", model="en_US-lessac-high", speaker_id=None,
        length_scale=1.0, noise_scale=0.5, noise_w=0.5,
        notes="US announcer-style female (high quality): crisp, very articulate menu voice (Whisper 0 errors, "
              "log-prob -0.08, DNSMOS 3.47), bright sing-song IVR contour (F0 SD ~5.8 st), median F0 ~185 Hz. "
              "noise 0.5/0.5 for a controlled, regular read. Captions off (scene 3 shows its words as glowing "
              "rune-text). Mix fx='phone': stone-phone band-pass (~300-3400 Hz) plus a faint magical shimmer; "
              "that, its pitch movement and brightness keep it well apart from the pharmacist."),
    "BOUNCER": dict(
        character="the stone troll", model="en_GB-vctk-medium", speaker_id=102,
        length_scale=1.18, noise_scale=0.5, noise_w=0.6,
        notes="VCTK speaker p237 (Scottish male). The deepest + flattest + slowest combination of 26 male "
              "candidates: median F0 ~77-81 Hz, F0 SD ~0.75 st (a flat, bored monotone), ~3.3 syl/s at "
              "length_scale 1.18; 'Keep it light, buddy.' recognised perfectly in 6/6 renditions. Dark "
              "timbre (centroid ~210 Hz). noise 0.5/0.6."),
    "CROWD": dict(
        character="the pixie", model="en_US-libritts_r-medium", speaker_id=448,
        length_scale=0.92, noise_scale=0.5, noise_w=0.6,
        notes="LibriTTS-R reader 4807: young (perceived ~27), high (median F0 ~244 Hz -- a tiny pixie), quick "
              "(fastest finalist, ~5.8 syl/s) and expressive (F0 SD ~3.9 st) for the sneer. 'Ew.' is fed as "
              "'Eew.' (/iːw/): espeak reads 'Ew.' as /juː/ = 'you' (Whisper heard 'You, what is he doing?' in "
              "0/4 'Ew.' renditions vs 'Ew' in 4/4 with 'Eew.'). length_scale 0.92, noise 0.5/0.6."),
    "OLD_WOMAN": dict(
        character="the gnome grandmother", model="en_US-libritts_r-medium", speaker_id=510,
        length_scale=1.15, noise_scale=0.5, noise_w=0.6,
        notes="LibriTTS-R reader 4800: the oldest-sounding clean female voice found (perceived age ~54 after "
              "an age scan of all ~600 female-pitched LibriTTS-R/VCTK speakers; several 'older' candidates "
              "were high-pitched men and were rejected). Warm and twinkly (F0 SD ~3.9 st), the roughest/"
              "breathiest phonation of the finalists (HNR ~10 dB, the most F0 micro-perturbation -- an older "
              "voice quality), Whisper-perfect on 15/15 renditions. length_scale 1.15 (slow, dry), noise "
              "0.5/0.6."),
}


# ================================================================================================
# LINES -- text is the script's words verbatim; `say` is what Piper is fed (respelled where espeak
# misreads), split into parts joined by deliberate pauses.
# ================================================================================================
@dataclass
class Part:
    say: str                          # Piper input (may be respelled; phonemes are logged)
    pause: float = 0.0                # silence AFTER this part (voice offset -> next voice onset), s
    seed: Optional[int] = None        # RNG seed for this part's session (None -> stable hash)
    ls: Optional[float] = None        # length_scale override
    ns: Optional[float] = None        # noise_scale override
    nw: Optional[float] = None        # noise_w override
    cut: Optional[dict] = None        # interruption: {"run": -2, "keep": 0.035, "fade": 0.012}
    widen: Optional[float] = None     # widen the longest internal pause of this part to this many s
    gain_db: float = 0.0              # relative gain of this part inside its line
    pulse: Optional[dict] = None      # laugh pulse: {"vowel": s, "ioi": s to next pulse's vowel onset}


@dataclass
class Line:
    id: str
    scene: int
    speaker: str
    text: str
    target: float
    parts: list
    caption: bool = True
    vo: bool = False
    fx: Optional[str] = None
    reply: Optional[tuple] = None     # preferred gap window after the previous line (exchange), s
    min_gap: float = MIN_GAP
    lo: float = 0.0                   # extra hard bounds on start (story constraints)
    hi: float = 1e9


LINES = [
    # ---- S1 the wash-house
    Line("s1_l1", 1, "MAN", "Self-service.", 11.8, [Part("Self-service.", seed=12676)], lo=11.3),
    Line("s1_l2", 1, "MAN", "That's the whole city, isn't it.", 18.5,
         [Part("That's the whole city, isn't it.", seed=4687)]),
    # ---- S2 the apothecary
    Line("s2_l1", 2, "PHARMACIST", "Try these. Lots of people swear by them.", 17.0,
         [Part("Try these.", seed=11687, pause=0.42), Part("Lots of people swear by them.", seed=12724)]),
    Line("s2_l2", 2, "MAN", "Do any of them talk back?", 20.3, [Part("Do any of them talk back?", seed=10698)],
         reply=(0.45, 0.9)),
    # ---- S3 the speaking stone
    Line("s3_l1", 3, "PHONE", "For billing, press one.", 1.0, [Part("For billing, press one.", seed=8698)],
         caption=False, fx="phone"),
    Line("s3_l2", 3, "PHONE", "For a new account, press two.", 3.6, [Part("For a new account, press two.", seed=13709)],
         caption=False, fx="phone"),
    Line("s3_l3", 3, "PHONE", "For loneliness… please hold.", 6.6,
         [Part("For loneliness,", seed=13720, pause=0.62), Part("please hold.", seed=9757)], caption=False, fx="phone"),
    Line("s3_l4", 3, "MAN", "I've been on hold my whole life.", 14.3, [Part("I've been on hold my whole life.", seed=11731)]),
    # ---- S4 the tavern door
    Line("s4_l1", 4, "MAN", "Can I tell you something? Lately I—", 10.0,
         [Part("Can I tell you something?", seed=5709, pause=0.38),
          Part("Lately I feel", seed=9746, cut={"gap": "longest", "keep": 0.030, "fade": 0.010})],
         fx="drowned"),
    Line("s4_l2", 4, "BOUNCER", "Keep it light, buddy.", 15.5, [Part("Keep it light, buddy.", seed=7720)]),
    # ---- S5 the crowd
    Line("s5_l1", 5, "CROWD", "Ew. What is he doing?", 13.4,
         [Part("Eew.", seed=4720, pause=0.35), Part("What is he doing?", seed=11757)]),
    Line("s5_l2", 5, "MAN", "We'll film a fight.", 16.3, [Part("We'll film a fight.", seed=11731)], reply=(0.5, 1.4)),
    Line("s5_l3", 5, "MAN", "But someone gets gentle, and everybody looks away.", 18.8,
         [Part("But someone gets gentle, and everybody looks away.", seed=12742)], min_gap=0.6),
    # ---- S6 the bench
    Line("s6_l1", 6, "OLD_WOMAN", "They tell you to try that too?", 13.2, [Part("They tell you to try that too?", seed=7731)]),
    Line("s6_l2", 6, "MAN", "Candles. Vitamins. Yoga.", 16.0,
         [Part("Candles.", seed=11742, pause=0.45), Part("Vitamins.", seed=10779, pause=0.45), Part("Yoga.", seed=6816)], reply=(0.5, 1.0)),
    Line("s6_l3", 6, "OLD_WOMAN", "They told me to get a cat. I got the cat.", 19.0,
         [Part("They told me to get a cat.", seed=9753, pause=0.72), Part("I got the cat.", seed=6790)], reply=(0.45, 0.9)),
    Line("s6_l4", 6, "OLD_WOMAN", "The cat sleeps through every story about my day.", 23.4,
         [Part("The cat sleeps through every story about my day.", seed=10764)], reply=(0.8, 1.3), min_gap=0.7),
    # The laugh: five 'hah' pulses synthesized in the dragon's own voice, assembled like a real laugh bout
    # (film/build/laugh_pulses.py + laugh_pick.py): ~4.4 pulses/s, each an F0 arch, starting ~+9 st above
    # his speaking pitch and stepping down (196 -> 181 -> 168 -> 155 -> 146 Hz), decrescendo, breathy /h/
    # between pulses, ending on a longer relaxed 'ha'.  Whisper hears 'Ha ha ha ha ha'.
    Line("s6_laugh", 6, "MAN", "(laughs)", 26.8,
         [Part("[[hˈʌ!]]", seed=96104, ls=0.7, ns=0.667, nw=0.8, gain_db=0.0, pulse={"vowel": 0.14, "ioi": 0.235}),
          Part("[[hˈʌ.]]", seed=100202, ls=0.8, ns=0.667, nw=0.8, gain_db=-1.2, pulse={"vowel": 0.12, "ioi": 0.22}),
          Part("[[hˈɑ!]]", seed=95000, ls=0.6, ns=0.667, nw=0.8, gain_db=-2.6, pulse={"vowel": 0.11, "ioi": 0.215}),
          Part("Ha.", seed=93105, ls=0.7, ns=0.667, nw=0.8, gain_db=-4.0, pulse={"vowel": 0.11, "ioi": 0.235}),
          Part("Ha.", seed=93204, ls=0.8, ns=0.667, nw=0.8, gain_db=-6.0, pulse={"vowel": 0.19, "ioi": 0.0})],
         caption=False, reply=(0.3, 0.7), min_gap=0.25),
    # ---- S7 the bread
    Line("s7_l1", 7, "MAN", "You know what's funny?", 18.6, [Part("You know what's funny?", seed=12742)]),
    Line("s7_l2", 7, "MAN", "All that stuff they gave me was for being alone.", 20.6,
         [Part("All that stuff they gave me was for being alone.", seed=13753)], min_gap=0.5),
    Line("s7_l3", 7, "OLD_WOMAN", "And all this costs is a loaf of bread.", 24.6,
         [Part("And all this costs is a loaf of bread.", seed=7764)], reply=(0.6, 1.4)),
    # ---- S8 close (voice-over)
    Line("s8_l1", 8, "MAN", "They kept handing me stones.", 2.5, [Part("They kept handing me stones.", seed=13753, ls=1.12)],
         vo=True, fx="vo"),
    Line("s8_l2", 8, "MAN", "We were hungry for bread the whole time.", 7.0,
         [Part("We were hungry for bread the whole time.", seed=10764, ls=1.12)], vo=True, fx="vo", min_gap=0.8),
    Line("s8_l3", 8, "MAN", "All it took was somebody to break it.", 11.8,
         [Part("All it took was somebody to break it.", seed=12775, ls=1.12)], vo=True, fx="vo", min_gap=0.8),
]

REQUIRED_LINES = ["s1_l1", "s1_l2", "s2_l1", "s2_l2", "s3_l1", "s3_l2", "s3_l3", "s3_l4", "s4_l1", "s4_l2",
                  "s5_l1", "s5_l2", "s5_l3", "s6_l1", "s6_l2", "s6_l3", "s6_l4", "s6_laugh", "s7_l1", "s7_l2",
                  "s7_l3", "s8_l1", "s8_l2", "s8_l3"]
REQUIRED_BEATS = ["s1_fadein", "s1_glance", "s1_lean", "s1_tap", "s1_lookaround",
                  "s2_slide", "s2_note", "s2_nod", "s2_items", "s2_item1", "s2_item2", "s2_item3", "s2_item4",
                  "s2_stare", "s2_pause", "s2_ring",
                  "s3_hold",
                  "s4_stamp", "s4_smile", "s4_inside", "s4_swell", "s4_turn", "s4_lookbouncer", "s4_lookhand",
                  "s4_exit",
                  "s5_stop", "s5_hug", "s5_silence", "s5_lower",
                  "s6_sit", "s6_pause", "s6_book", "s6_glance", "s6_laugh",
                  "s7_tear", "s7_hand", "s7_teen", "s7_offer", "s7_teensit", "s7_driver", "s7_worker",
                  "s7_full", "s7_drag",
                  "s8_fade"]


def derive_beats(L: dict) -> list:
    """Every SPEC section 6 beat (+ a few explicitly-timed unnamed ranges), moved with the lines they
    depend on.  L[id] = (start, end) local seconds."""
    B = []

    def b(bid, t, end=None):
        B.append({"id": bid, "scene": int(bid[1]), "t": round(float(t), 3),
                  "end": None if end is None else round(float(end), 3)})

    s, e = (lambda k: L[k][0]), (lambda k: L[k][1])
    # S1
    b("s1_fadein", 0.0, 1.0)
    b("s1_glance", 5.5)
    b("s1_lean", 7.0)
    b("s1_tap", 8.3, min(11.0, s("s1_l1") - 0.3))
    la = max(13.5, e("s1_l1") + 0.6)
    b("s1_lookaround", la, max(min(18.0, s("s1_l2") - 0.4), la + 2.0))
    b("s1_hold", max(21.0, e("s1_l2") + 0.6), 25.0)
    # S2
    b("s2_slide", 1.5)
    b("s2_note", 3.0, 6.0)
    b("s2_nod", 6.5)
    stare = min(16.5, s("s2_l1") - 0.5)
    b("s2_items", 8.0, stare)
    b("s2_item1", 9.0)
    b("s2_item2", 11.0)
    b("s2_item3", 13.0)
    b("s2_item4", 15.0)
    b("s2_stare", stare)
    pause = e("s2_l2") + 0.6
    b("s2_pause", pause)
    b("s2_ring", min(pause + 1.0, 24.0))
    # S3
    b("s3_hold", max(10.0, e("s3_l3") + 0.6), 20.0)
    b("s3_lantern", max(17.0, e("s3_l4") + 0.6), 20.0)
    # S4
    b("s4_stamp", 3.0)
    b("s4_smile", 3.6, 6.0)
    b("s4_inside", 6.3)
    b("s4_swell", s("s4_l1") + 0.8)
    turn = max(12.8, e("s4_l1") + 0.3)
    b("s4_turn", turn)
    b("s4_lookbouncer", min(max(14.0, turn + 0.8), s("s4_l2") - 0.8))
    lookhand = max(18.0, e("s4_l2") + 0.6)
    b("s4_lookhand", lookhand)
    b("s4_exit", max(20.0, lookhand + 1.6), 25.0)
    # S5
    b("s5_stop", 8.5)
    b("s5_hug", 9.6)
    b("s5_silence", 10.0)
    b("s5_lower", 10.8, min(13.0, s("s5_l1") - 0.3))
    b("s5_alone", max(22.0, e("s5_l3") + 0.4), 25.0)
    # S6
    b("s6_sit", 1.5, 4.0)
    b("s6_pause", 4.0, 9.0)
    b("s6_book", 9.0, 12.0)
    b("s6_glance", min(12.6, s("s6_l1") - 0.5))
    b("s6_laugh", s("s6_laugh"), e("s6_laugh"))
    # S7
    b("s7_tear", 0.8)
    b("s7_hand", 1.8)
    b("s7_feed", 2.5, 6.5)
    b("s7_teen", 6.5)
    b("s7_offer", 8.0)
    b("s7_teensit", 9.8)
    b("s7_driver", 11.5)
    b("s7_worker", 13.5)
    b("s7_full", 15.0)
    b("s7_drag", 15.5, min(18.0, s("s7_l1") - 0.4))
    # S8
    b("s8_fade", max(17.5, e("s8_l3") + 1.5), 20.0)
    # S9 (end card; explicit SPEC timings)
    b("s9_fadein", 0.0, 1.5)
    b("s9_quote", 2.5, 4.0)
    b("s9_fadeout", 8.5, 10.0)
    B.sort(key=lambda d: (d["scene"], d["t"]))
    return B


# ================================================================================================
# synthesis
# ================================================================================================
def part_seed(line_id: str, k: int, part: Part) -> int:
    if part.seed is not None:
        return int(part.seed)
    return zlib.crc32(f"{line_id}:{k}:{part.say}".encode()) & 0x7FFFFFFF


def part_settings(line: Line, k: int) -> dict:
    part = line.parts[k]
    c = CAST[line.speaker]
    return dict(model=c["model"], speaker_id=c["speaker_id"], say=part.say,
                ls=part.ls if part.ls is not None else c["length_scale"],
                ns=part.ns if part.ns is not None else c["noise_scale"],
                nw=part.nw if part.nw is not None else c["noise_w"],
                seed=part_seed(line.id, k, part))


def synth_job(job: dict):
    """Worker: one part -> (float32 audio at the voice's native rate, sample rate, phonemes)."""
    import onnxruntime as ort
    from piper import PiperVoice
    from piper.config import PiperConfig, SynthesisConfig

    path = os.path.join(VOICE_DIR, job["model"] + ".onnx")
    with open(path + ".json", "r", encoding="utf-8") as fh:
        cfg = json.load(fh)
    ort.set_seed(int(job["seed"]))
    so = ort.SessionOptions()
    so.intra_op_num_threads = 1
    so.inter_op_num_threads = 1
    sess = ort.InferenceSession(path, sess_options=so, providers=["CPUExecutionProvider"])
    voice = PiperVoice(config=PiperConfig.from_dict(cfg), session=sess)
    syn = SynthesisConfig(speaker_id=job["speaker_id"], length_scale=job["ls"], noise_scale=job["ns"],
                          noise_w_scale=job["nw"], normalize_audio=False)
    chunks, phon = [], []
    # == PiperVoice.synthesize() sentence by sentence, minus its hard clip to [-1, 1] (we normalise later)
    for phonemes in voice.phonemize(job["say"]):
        if not phonemes:
            continue
        audio = voice.phoneme_ids_to_audio(voice.phonemes_to_ids(phonemes), syn)
        chunks.append(np.asarray(audio, np.float32).reshape(-1))
        phon.append("".join(phonemes))
    audio = np.concatenate(chunks) if chunks else np.zeros(1, np.float32)
    return audio, int(cfg["audio"]["sample_rate"]), phon


# ================================================================================================
# DSP helpers
# ================================================================================================
def _frames(x: np.ndarray, n: int, hop: int) -> np.ndarray:
    if len(x) < n:
        x = np.pad(x, (0, n - len(x)))
    nfr = 1 + (len(x) - n) // hop
    st = x.strides[0]
    return np.lib.stride_tricks.as_strided(x, shape=(nfr, n), strides=(st * hop, st)).copy()


def frame_db(x: np.ndarray, sr: int, win: float = 0.010, hop: float = 0.005):
    """Short-time level in dBFS, frames centred at k*hop."""
    W, H = max(1, int(win * sr)), max(1, int(hop * sr))
    xp = np.pad(np.asarray(x, np.float64), (W // 2, W))
    F = _frames(xp, W, H)
    rms = np.sqrt(np.mean(F * F, axis=1) + 1e-20)
    return 20 * np.log10(rms + 1e-12), H


def speech_bounds(x: np.ndarray, sr: int, rel_db: float = 48.0, abs_db: float = -62.0):
    """(onset, offset) sample indices of the voice: first/last 10 ms frame above max(peak-48 dB, -62 dBFS)."""
    db, H = frame_db(x, sr)
    if len(db) == 0:
        return 0, len(x)
    thr = max(db.max() - rel_db, abs_db)
    idx = np.where(db > thr)[0]
    if len(idx) == 0:
        return 0, len(x)
    W = int(0.010 * sr)
    on = max(0, idx[0] * H - W // 2)
    off = min(len(x), idx[-1] * H + W // 2)
    return int(on), int(off)


def raised_cos(n: int) -> np.ndarray:
    if n <= 0:
        return np.ones(0)
    return 0.5 - 0.5 * np.cos(np.pi * (np.arange(n) + 0.5) / n)


def trim(x: np.ndarray, sr: int, margin: float, fade_in: float = 0.0, fade_out: float = 0.0) -> np.ndarray:
    on, off = speech_bounds(x, sr)
    m = int(round(margin * sr))
    a, b = max(0, on - m), min(len(x), off + m)
    y = np.asarray(x[a:b], np.float64).copy()
    # if the source had less silence than the margin, pad so the margin is exact
    if on - m < 0:
        y = np.concatenate([np.zeros(m - on), y])
    if off + m > len(x):
        y = np.concatenate([y, np.zeros(off + m - len(x))])
    fi, fo = int(round(fade_in * sr)), int(round(fade_out * sr))
    if fi:
        y[:fi] *= raised_cos(fi)
    if fo:
        y[-fo:] *= raised_cos(fo)[::-1]
    return y


def voiced_runs(x: np.ndarray, sr: int, fmin=60.0, fmax=500.0, vthresh=0.3):
    """Voiced segments [(start_s, end_s)] from the YIN track."""
    t, f0, v = yin(x, sr, fmin, fmax, vthresh=vthresh)
    runs, i, n = [], 0, len(v)
    while i < n:
        if v[i]:
            j = i
            while j < n and v[j]:
                j += 1
            runs.append((t[i], t[j - 1]))
            i = j
        else:
            i += 1
    return runs


def vowel_runs(x: np.ndarray, sr: int, rel_db: float = 22.0, min_gap: float = 0.035, min_len: float = 0.03):
    """Vocalic segments [(start_s, end_s)]: frames whose 80-900 Hz energy is within rel_db of the loudest
    frame AND that are periodic (YIN aperiodicity < 0.5); gaps < min_gap merged, blips < min_len dropped.
    Robust for breathy voices where strict YIN voicing fragments."""
    x = np.asarray(x, np.float64)
    W, H = int(0.020 * sr), int(0.005 * sr)
    F = _frames(np.pad(x, (W // 2, W)), W, H) * np.hanning(W)[None, :]
    nfft = 1 << int(math.ceil(math.log2(W)))
    P = np.abs(np.fft.rfft(F, nfft)) ** 2
    fr = np.fft.rfftfreq(nfft, 1.0 / sr)
    lb = 10 * np.log10(P[:, (fr >= 80) & (fr <= 900)].sum(axis=1) + 1e-20)
    t = np.arange(len(lb)) * H / sr
    ty, _, vy = yin(x, sr, 60.0, 500.0, vthresh=0.5)
    per = np.interp(t, ty, vy.astype(float)) > 0.5
    act = (lb > lb.max() - rel_db) & per
    runs, i, n = [], 0, len(act)
    while i < n:
        if act[i]:
            j = i
            while j < n and act[j]:
                j += 1
            runs.append([t[i], t[j - 1]])
            i = j
        else:
            i += 1
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] < min_gap:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return [(a, b) for a, b in merged if b - a >= min_len]


def apply_cut(x: np.ndarray, sr: int, cut: dict) -> np.ndarray:
    """Interrupt a part abruptly, mid-word, with a short `fade`.
    {"gap": "longest"}: stop `keep` s into the longest unvoiced gap between vocalic runs -- in
    'Lately I feel' that is the /f/, so the line stops on the first breath of 'f-' right after 'Lately I'.
    {"run": k}: stop `keep` s after the end of vocalic run k."""
    runs = vowel_runs(x, sr)
    if len(runs) < 2:
        raise RuntimeError(f"cut: need >= 2 vocalic runs, found {len(runs)}")
    if cut.get("gap") == "longest":
        k = int(np.argmax([runs[i + 1][0] - runs[i][1] for i in range(len(runs) - 1)]))
        t_cut = runs[k][1] + cut.get("keep", 0.03)
    else:
        t_cut = runs[cut.get("run", -2)][1] + cut.get("keep", 0.03)
    n = min(len(x), int(round(t_cut * sr)))
    fo = int(round(cut.get("fade", 0.01) * sr))
    y = np.asarray(x[:n], np.float64).copy()
    y[-fo:] *= raised_cos(fo)[::-1]
    return y


def make_pulse(x: np.ndarray, sr: int, vowel: float, asp_max: float = 0.07, tau: float = 0.028):
    """One laugh pulse from a synthesized 'hah': keep <= asp_max s of the /h/ breath before the vowel,
    hold the vowel for `vowel` s, then let it die away exponentially (tau) -- a short, bouncy 'ha'.
    Returns (pulse, vowel_onset_index); the pulse is peak-normalised to 1."""
    x = np.asarray(x, np.float64)
    on, off = speech_bounds(x, sr)
    t, f0, v = yin(x, sr, 70.0, 420.0, vthresh=0.5)
    vi = [i for i in np.where(v)[0] if t[i] * sr >= on]
    vo = int(round(t[vi[0]] * sr)) if vi else on + int(0.05 * sr)
    start = max(on, vo - int(round(asp_max * sr)))
    seg = x[start:off].copy()
    n_hold = (vo - start) + int(round(vowel * sr))
    n_tail = int(round(4 * tau * sr))
    env = np.ones(len(seg))
    if n_hold < len(seg):
        k = np.arange(len(seg) - n_hold)
        env[n_hold:] = np.exp(-k / (tau * sr))
        env[n_hold + n_tail:] = 0.0
        nf = min(n_tail, len(seg) - n_hold) // 3          # last third of the tail: smooth to exactly 0
        if nf > 0:
            e0 = n_hold + min(n_tail, len(seg) - n_hold)
            env[e0 - nf: e0] *= raised_cos(nf)[::-1]
    fi = int(0.006 * sr)
    env[:fi] *= raised_cos(fi)
    seg = (seg * env)[: n_hold + n_tail]
    seg /= np.max(np.abs(seg)) + 1e-12
    return seg, vo - start


def assemble_laugh(line: "Line", results: list, sr: int) -> np.ndarray:
    """Overlap-add the pulses of a laugh so each pulse's vowel onset lands on its beat (Part.pulse.ioi)."""
    pulses, onsets, t = [], [], 0.0
    for part, (audio, _, _) in zip(line.parts, results):
        p, vo = make_pulse(audio, sr, part.pulse["vowel"], part.pulse.get("asp", 0.07))
        p = p * 10 ** (part.gain_db / 20)
        pulses.append((p, vo))
        onsets.append(t)
        t += part.pulse.get("ioi", 0.2)
    lead = max(vo for _, vo in pulses)
    n = int(round(onsets[-1] * sr)) + lead + max(len(p) for p, _ in pulses) + 1
    y = np.zeros(n)
    for (p, vo), o in zip(pulses, onsets):
        a = lead + int(round(o * sr)) - vo
        y[a: a + len(p)] += p
    return y


def widen_pause(x: np.ndarray, sr: int, length: float) -> np.ndarray:
    """Set the longest internal pause (level < peak-40 dB) of a part to `length` seconds."""
    db, H = frame_db(x, sr)
    on, off = speech_bounds(x, sr)
    quiet = db < db.max() - 40
    best, i, n = None, int(on / H) + 1, int(off / H) - 1
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if best is None or (j - i) > (best[1] - best[0]):
                best = (i, j)
            i = j
        else:
            i += 1
    if best is None:
        return x
    a, b = best[0] * H, best[1] * H
    mid = (a + b) // 2
    cur = b - a
    need = int(round(length * sr))
    if need >= cur:
        return np.concatenate([x[:mid], np.zeros(need - cur), x[mid:]])
    cut = cur - need
    return np.concatenate([x[:mid - cut // 2], x[mid - cut // 2 + cut:]])


def resample(x: np.ndarray, sr_in: int, sr_out: int = SR) -> np.ndarray:
    """High-quality resampling: ffmpeg soxr (precision 28), else ffmpeg swr, else numpy FFT."""
    x = np.asarray(x, np.float32)
    if sr_in == sr_out:
        return x.astype(np.float64)
    n_out = int(round(len(x) * sr_out / sr_in))
    pad = int(0.05 * sr_in)
    xin = np.concatenate([np.zeros(pad, np.float32), x, np.zeros(pad, np.float32)])
    p_out = int(round(pad * sr_out / sr_in))
    if shutil.which("ffmpeg"):
        for flt in (f"aresample={sr_out}:resampler=soxr:precision=28:cheby=1", f"aresample={sr_out}"):
            cmd = ["ffmpeg", "-nostdin", "-v", "error", "-f", "f32le", "-ar", str(sr_in), "-ac", "1",
                   "-i", "pipe:0", "-af", flt, "-f", "f32le", "-ac", "1", "pipe:1"]
            r = subprocess.run(cmd, input=xin.tobytes(), capture_output=True)
            if r.returncode == 0:
                y = np.frombuffer(r.stdout, np.float32).astype(np.float64)
                y = y[p_out: p_out + n_out]
                if len(y) < n_out:
                    y = np.pad(y, (0, n_out - len(y)))
                return y
    # numpy fallback: band-limited FFT resampling of the zero-padded signal
    n_in = len(xin)
    m_out = int(round(n_in * sr_out / sr_in))
    X = np.fft.rfft(xin.astype(np.float64))
    Y = np.zeros(m_out // 2 + 1, complex)
    k = min(len(X), len(Y))
    Y[:k] = X[:k]
    y = np.fft.irfft(Y, m_out) * (m_out / n_in)
    return y[p_out: p_out + n_out]


def _biquad_response(b, a, w):
    z = np.exp(-1j * w)
    return (b[0] + b[1] * z + b[2] * z * z) / (a[0] + a[1] * z + a[2] * z * z)


def lufs(x: np.ndarray, sr: int = SR) -> float:
    """BS.1770-4 integrated loudness (K-weighting applied in the frequency domain; 48 kHz coefficients)."""
    x = np.asarray(x, np.float64)
    pad = int(0.25 * sr)
    n = len(x) + 2 * pad
    nfft = 1 << int(math.ceil(math.log2(n)))
    w = 2 * np.pi * np.arange(nfft // 2 + 1) / nfft
    h1 = _biquad_response([1.53512485958697, -2.69169618940638, 1.19839281085285],
                          [1.0, -1.69065929318241, 0.73248077421585], w)
    h2 = _biquad_response([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621], w)
    X = np.fft.rfft(np.concatenate([np.zeros(pad), x, np.zeros(pad)]), nfft)
    y = np.fft.irfft(X * h1 * h2, nfft)[pad: pad + len(x)]
    blk, hop = int(0.4 * sr), int(0.1 * sr)
    if len(y) < blk:
        z = np.array([np.mean(y * y)])
    else:
        F = _frames(y, blk, hop)
        z = np.mean(F * F, axis=1)
    lj = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lj > -70]
    if len(z1) == 0:
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(z1)) - 10
    z2 = z[lj > max(rel, -70)]
    return float(-0.691 + 10 * np.log10(np.mean(z2) + 1e-20))


def yin(x: np.ndarray, sr: int, fmin=55.0, fmax=520.0, win=0.035, hop=0.005, thresh=0.12, vthresh=0.3):
    """Vectorised YIN pitch tracker -> (times, f0 Hz (0 = unvoiced), voiced mask)."""
    x = np.asarray(x, np.float64)
    W = int(round(win * sr))
    tmax = int(math.ceil(sr / fmin))
    tmin = max(2, int(math.floor(sr / fmax)))
    H = max(1, int(round(hop * sr)))
    N = W + tmax + 2
    F = _frames(np.pad(x, (W // 2, N)), N, H)
    nfr = F.shape[0]
    nfft = 1 << int(math.ceil(math.log2(N + W)))
    c = np.fft.irfft(np.conj(np.fft.rfft(F[:, :W], nfft)) * np.fft.rfft(F, nfft), nfft)[:, : tmax + 2]
    cs = np.concatenate([np.zeros((nfr, 1)), np.cumsum(F * F, axis=1)], axis=1)
    taus = np.arange(tmax + 2)
    e = cs[:, W + taus] - cs[:, taus]
    d = np.maximum(e[:, :1] + e - 2 * c, 0.0)
    d[:, 0] = 0
    dn = np.ones_like(d)
    dn[:, 1:] = d[:, 1:] * taus[1:] / np.maximum(np.cumsum(d[:, 1:], axis=1), 1e-12)
    reg = dn[:, tmin: tmax + 1]
    below = reg < np.maximum(thresh, reg.min(axis=1, keepdims=True) + 0.08)
    has = below.any(axis=1)
    first = np.where(has, below.argmax(axis=1), 0)
    idx = np.arange(reg.shape[1])[None, :]
    after = (idx >= first[:, None]) & (~below)
    endd = np.where(after.any(axis=1), after.argmax(axis=1), reg.shape[1])
    masked = np.where((idx >= first[:, None]) & (idx < endd[:, None]), reg, np.inf)
    k = np.clip(np.where(has, masked.argmin(axis=1), reg.argmin(axis=1)) + tmin, 2, tmax)
    rows = np.arange(nfr)
    y0, y1, y2 = dn[rows, k - 1], dn[rows, k], dn[rows, k + 1]
    den = y0 - 2 * y1 + y2
    off = np.clip(np.where(np.abs(den) > 1e-12, 0.5 * (y0 - y2) / np.where(np.abs(den) > 1e-12, den, 1), 0), -1, 1)
    f0 = sr / (k + off)
    rms_db = 10 * np.log10(e[:, 0] / W + 1e-20)
    v = (y1 < vthresh) & (rms_db > np.percentile(rms_db, 99) - 38) & (f0 >= fmin) & (f0 <= fmax)
    # drop voiced blips shorter than 20 ms
    out, i = v.copy(), 0
    while i < nfr:
        if v[i]:
            j = i
            while j < nfr and v[j]:
                j += 1
            if j - i < 4:
                out[i:j] = False
            i = j
        else:
            i += 1
    t = np.arange(nfr) * H / sr
    return t, np.where(out, f0, 0.0), out


def speech_env(y: np.ndarray, sr: int = SR, fps: int = FPS) -> list:
    """24 fps mouth-driving envelope: env[k] = level at k/fps from the wav start."""
    y = np.asarray(y, np.float64)
    n = int(round(len(y) / sr * fps))
    half = int(round(sr / fps))                      # +-1 frame Hann window (light smoothing)
    win = np.hanning(2 * half + 1)
    yp = np.pad(y * y, (half, half + 1))
    cen = np.round(np.arange(n) * sr / fps).astype(int)
    ms = np.array([np.dot(yp[c: c + 2 * half + 1], win) / win.sum() for c in cen])
    rms = np.sqrt(ms + 1e-20)
    act = rms[rms > rms.max() * 1e-3]
    ref = np.percentile(act, 95) if len(act) else rms.max()
    rel = 20 * np.log10(rms / (ref + 1e-12) + 1e-12)
    level = np.clip(rms / (ref + 1e-12), 0, 1) ** 0.6           # gentle compression
    knee = np.clip((rel + 30.0) / 8.0, 0, 1)                     # -30 dB -> 0 ... -22 dB -> 1
    knee = knee * knee * (3 - 2 * knee)
    env = np.clip(level * knee, 0, 1)
    env[rel < -30.0] = 0.0
    return [round(float(v), 3) for v in env]


def read_wav(path: str):
    with wave.open(path, "rb") as w:
        sr, ch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(n)
    a = np.frombuffer(raw, np.int16).astype(np.float64) / 32768.0
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    return a, sr, ch, sw


def write_wav(path: str, y: np.ndarray, sr: int = SR):
    q = np.clip(np.round(np.asarray(y) * 32767.0), -32768, 32767).astype("<i2")
    tmp = path + ".tmp"
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(q.tobytes())
    os.replace(tmp, path)


# ================================================================================================
# line assembly
# ================================================================================================
def spec_hash(line: Line) -> str:
    d = {"text": line.text, "speaker": line.speaker,
         "parts": [dict(part_settings(line, k), pause=p.pause, cut=p.cut, widen=p.widen, gain_db=p.gain_db,
                        pulse=p.pulse) for k, p in enumerate(line.parts)],
         "v": 3}
    return hashlib.sha1(json.dumps(d, sort_keys=True).encode()).hexdigest()[:16]


def assemble(line: Line, results: list) -> np.ndarray:
    """Join the synthesized parts of a line -> final 48 kHz float audio (trimmed, faded, normalised)."""
    srs = {r[1] for r in results}
    if len(srs) != 1:
        raise RuntimeError(f"{line.id}: parts at different rates {srs}")
    sr = srs.pop()
    if any(p.pulse for p in line.parts):
        return finish(assemble_laugh(line, results, sr), sr)
    segs = []
    for k, (part, (audio, _, _)) in enumerate(zip(line.parts, results)):
        x = np.asarray(audio, np.float64)
        if part.widen:
            x = widen_pause(x, sr, part.widen)
        if part.cut:
            x = apply_cut(x, sr, part.cut)
        x = trim(x, sr, PART_EDGE)
        if part.gain_db:
            x = x * 10 ** (part.gain_db / 20)
        segs.append(x)
        if k < len(line.parts) - 1:
            segs.append(np.zeros(max(0, int(round((part.pause - 2 * PART_EDGE) * sr)))))
    return finish(np.concatenate(segs), sr)


def finish(x: np.ndarray, sr: int) -> np.ndarray:
    """Native-rate line audio -> 48 kHz, edges trimmed to EDGE with fades, -20 LUFS, peak <= -1 dBFS."""
    y = resample(x, sr, SR)
    y = trim(y, SR, EDGE, FADE_IN, FADE_OUT)
    g = 10 ** ((TARGET_LUFS - lufs(y)) / 20)
    peak = np.max(np.abs(y)) * g
    ceil = 10 ** (PEAK_CEIL_DB / 20)
    if peak > ceil:
        g *= ceil / peak
    return y * g


# ================================================================================================
# placement
# ================================================================================================
def place_scene(lines: list, durs: dict, scene_dur: float, step: float = 0.01) -> dict:
    """Exact DP over a 10 ms grid: minimise sum (start-target)^2 + soft reply-gap penalties subject to
    +-NUDGE, no overlap (min_gap), scene-end guard and per-line bounds."""
    grids, unary = [], []
    for ln in lines:
        lo = max(ln.target - NUDGE, ln.lo, 0.0)
        hi = min(ln.target + NUDGE, ln.hi, scene_dur - END_GUARD - durs[ln.id])
        if hi < lo - 1e-9:
            raise RuntimeError(f"{ln.id}: no room (dur {durs[ln.id]:.2f}s, window {lo:.2f}..{hi:.2f})")
        g = np.arange(int(math.ceil(lo / step - 1e-6)), int(math.floor(hi / step + 1e-6)) + 1) * step
        grids.append(g)
        unary.append((g - ln.target) ** 2)
    acc, backs = unary[0], []
    for i in range(1, len(lines)):
        prev, cur = lines[i - 1], lines[i]
        gap = grids[i][None, :] - (grids[i - 1][:, None] + durs[prev.id])
        pair = np.where(gap >= cur.min_gap - 1e-9, 0.0, np.inf)
        if cur.reply:
            lo_p, hi_p = cur.reply
            pair = pair + 40.0 * (np.maximum(0, lo_p - gap) ** 2 + np.maximum(0, gap - hi_p) ** 2)
        tot = acc[:, None] + pair
        bk = np.argmin(tot, axis=0)
        acc = tot[bk, np.arange(len(grids[i]))] + unary[i]
        backs.append(bk)
    j = int(np.argmin(acc))
    if not np.isfinite(acc[j]):
        raise RuntimeError("placement infeasible in scene %d" % lines[0].scene)
    starts = [0.0] * len(lines)
    starts[-1] = grids[-1][j]
    for i in range(len(lines) - 1, 0, -1):
        j = int(backs[i - 1][j])
        starts[i - 1] = grids[i - 1][j]
    return {ln.id: round(float(s), 3) for ln, s in zip(lines, starts)}


# ================================================================================================
# timeline
# ================================================================================================
def median_f0(speaker: str, wavs: dict) -> float:
    vals = []
    for ln in LINES:
        if ln.speaker != speaker or ln.id == "s6_laugh":
            continue
        y = wavs[ln.id]
        lo, hi = (50.0, 300.0) if speaker in ("MAN", "BOUNCER") else (90.0, 520.0)
        _, f0, v = yin(resample(y, SR, 16000), 16000, lo, hi)      # 16 kHz is plenty for F0
        vals.append(f0[v])
    allv = np.concatenate(vals) if vals else np.zeros(1)
    return round(float(np.median(allv)), 1) if len(allv) else 0.0


def dump_timeline(tl: dict) -> str:
    """Readable, diff-friendly JSON: one object per line, env arrays inline."""
    J = lambda o: json.dumps(o, ensure_ascii=False)  # noqa: E731
    out = ["{"]
    out.append(f'  "fps": {tl["fps"]}, "width": {tl["width"]}, "height": {tl["height"]}, "total": {tl["total"]},')
    out.append('  "cast": {')
    items = list(tl["cast"].items())
    for i, (k, v) in enumerate(items):
        out.append(f"    {J(k)}: {J(v)}" + ("," if i < len(items) - 1 else ""))
    out.append("  },")
    for key in ("scenes", "lines", "beats"):
        out.append(f'  "{key}": [')
        arr = tl[key]
        for i, v in enumerate(arr):
            out.append("    " + J(v) + ("," if i < len(arr) - 1 else ""))
        out.append("  ]" + ("," if key != "beats" else ""))
    out.append("}")
    return "\n".join(out) + "\n"


def build(force: bool, only: Optional[list], jobs: int):
    os.makedirs(DIALOGUE_DIR, exist_ok=True)
    manifest = {}
    if os.path.exists(MANIFEST):
        with open(MANIFEST) as fh:
            manifest = json.load(fh)
    todo = []
    for ln in LINES:
        path = os.path.join(DIALOGUE_DIR, ln.id + ".wav")
        want = force and (not only or ln.id in only)
        if want or not os.path.exists(path):
            todo.append(ln)
        elif manifest.get(ln.id, {}).get("hash") != spec_hash(ln):
            print(f"  ! {ln.id}.wav is stale against its spec (kept; re-make with --force --only {ln.id})")
    log = {}
    if os.path.exists(LOG_PATH):
        try:
            with open(LOG_PATH) as fh:
                log = json.load(fh)
        except Exception:
            log = {}
    if todo:
        jobs_list = [(ln, k, part_settings(ln, k)) for ln in todo for k in range(len(ln.parts))]
        print(f"synthesizing {len(todo)} line(s), {len(jobs_list)} part(s) with {jobs} worker(s) ...", flush=True)
        with ProcessPoolExecutor(max_workers=jobs, mp_context=get_context("spawn")) as ex:
            res = list(ex.map(synth_job, [j[2] for j in jobs_list]))
        by_line = {}
        for (ln, k, js), r in zip(jobs_list, res):
            by_line.setdefault(ln.id, [None] * len(ln.parts))[k] = r
        for ln in todo:
            y = assemble(ln, by_line[ln.id])
            write_wav(os.path.join(DIALOGUE_DIR, ln.id + ".wav"), y)
            manifest[ln.id] = {"hash": spec_hash(ln), "speaker": ln.speaker, "text": ln.text,
                               "parts": [dict(part_settings(ln, k), pause=p.pause, cut=p.cut, widen=p.widen,
                                              gain_db=p.gain_db, pulse=p.pulse) for k, p in enumerate(ln.parts)]}
            log[ln.id] = {"phonemes": [r[2] for r in by_line[ln.id]], "says": [p.say for p in ln.parts]}
            print(f"  {ln.id:9s} {len(y)/SR:5.2f}s  {' | '.join(' '.join(r[2]) for r in by_line[ln.id])}")
        with open(MANIFEST, "w") as fh:
            json.dump(manifest, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "w") as fh:
            json.dump(log, fh, indent=1, ensure_ascii=False)

    # ---- read back every wav (the committed files are the truth)
    wavs, durs = {}, {}
    for ln in LINES:
        a, sr, ch, sw = read_wav(os.path.join(DIALOGUE_DIR, ln.id + ".wav"))
        assert sr == SR and ch == 1 and sw == 2, f"{ln.id}: wav must be 48 kHz mono 16-bit"
        wavs[ln.id] = a
        durs[ln.id] = len(a) / SR

    # ---- placement per scene
    starts = {}
    for sid, _, _, sdur in SCENES:
        sl = [ln for ln in LINES if ln.scene == sid]
        if sl:
            starts.update(place_scene(sl, durs, sdur))
    scene_start = {s[0]: s[2] for s in SCENES}
    lines_out, L = [], {}
    for ln in LINES:
        st = starts[ln.id]
        en = round(st + durs[ln.id], 4)
        L[ln.id] = (st, en)
        lines_out.append({
            "id": ln.id, "scene": ln.scene, "speaker": ln.speaker, "text": ln.text,
            "start": st, "end": en,
            "global_start": round(scene_start[ln.scene] + st, 4), "global_end": round(scene_start[ln.scene] + en, 4),
            "wav": f"film/assets/dialogue/{ln.id}.wav",
            "caption": ln.caption, "vo": ln.vo, "fx": ln.fx,
            "env": speech_env(wavs[ln.id]),
        })
    cast_out = {}
    for spk, c in CAST.items():
        cast_out[spk] = {"character": c["character"], "model": c["model"], "speaker_id": c["speaker_id"],
                         "length_scale": c["length_scale"], "noise_scale": c["noise_scale"], "noise_w": c["noise_w"],
                         "median_f0": median_f0(spk, wavs), "notes": c["notes"]}
    tl = {"fps": FPS, "width": WIDTH, "height": HEIGHT, "total": TOTAL, "cast": cast_out,
          "scenes": [{"id": s[0], "name": s[1], "start": s[2], "duration": s[3]} for s in SCENES],
          "lines": lines_out, "beats": derive_beats(L)}
    tmp = TIMELINE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(dump_timeline(tl))
    os.replace(tmp, TIMELINE)
    print(f"wrote {os.path.relpath(TIMELINE, ROOT)}")
    report(tl)
    return tl


def report(tl: dict):
    tg = {ln.id: ln.target for ln in LINES}
    print(f"\n{'line':9s} {'spk':10s} {'target':>6s} {'start':>7s} {'end':>7s} {'dur':>5s} {'gap':>5s}  text")
    prev = {}
    for d in tl["lines"]:
        g = d["start"] - prev[d["scene"]] if d["scene"] in prev else float("nan")
        prev[d["scene"]] = d["end"]
        print(f"{d['id']:9s} {d['speaker']:10s} {tg[d['id']]:6.2f} {d['start']:7.2f} {d['end']:7.2f} "
              f"{d['end']-d['start']:5.2f} {g:5.2f}  {d['text']}")
    print("\ncast:")
    for k, c in tl["cast"].items():
        print(f"  {k:10s} {c['character']:22s} {c['model']}#{c['speaker_id']}  ls {c['length_scale']}  "
              f"ns {c['noise_scale']} nw {c['noise_w']}  median F0 {c['median_f0']} Hz")


# ================================================================================================
# validation
# ================================================================================================
def check(path: str = TIMELINE) -> bool:
    with open(path, encoding="utf-8") as fh:
        tl = json.load(fh)
    errs = []

    def need(cond, msg):
        if not cond:
            errs.append(msg)

    need(set(tl) == {"fps", "width", "height", "total", "cast", "scenes", "lines", "beats"}, f"top keys {set(tl)}")
    need(tl["fps"] == 24 and tl["width"] == 1920 and tl["height"] == 1080 and tl["total"] == 210.0, "header")
    # scenes
    need([(s["id"], s["name"], s["start"], s["duration"]) for s in tl["scenes"]] == [s for s in SCENES], "scenes")
    for s in tl["scenes"]:
        need(set(s) == {"id", "name", "start", "duration"}, f"scene keys {s}")
    need(abs(sum(s["duration"] for s in tl["scenes"]) - tl["total"]) < 1e-9, "durations sum")
    sdur = {s["id"]: s["duration"] for s in tl["scenes"]}
    sstart = {s["id"]: s["start"] for s in tl["scenes"]}
    # cast
    need(set(tl["cast"]) == {"MAN", "PHARMACIST", "PHONE", "BOUNCER", "CROWD", "OLD_WOMAN"}, "cast speakers")
    for k, c in tl["cast"].items():
        need(set(c) == {"character", "model", "speaker_id", "length_scale", "noise_scale", "noise_w", "median_f0",
                        "notes"}, f"cast keys {k}")
        need(os.path.exists(os.path.join(VOICE_DIR, c["model"] + ".onnx")) or not os.path.isdir(VOICE_DIR),
             f"voice model missing {c['model']}")
        need(isinstance(c["notes"], str) and len(c["notes"]) > 20, f"cast notes {k}")
        need(c["median_f0"] > 50, f"median_f0 {k}")
    # lines
    spec = {ln.id: ln for ln in LINES}
    ids = [d["id"] for d in tl["lines"]]
    need(sorted(ids) == sorted(REQUIRED_LINES) and len(set(ids)) == len(ids), f"line ids {ids}")
    with open(SCRIPT_MD, encoding="utf-8") as fh:
        script = fh.read()
    with open(os.path.join(FILM, "SPEC.md"), encoding="utf-8") as fh:
        script += fh.read()          # s4_l1's drowned words are written in SPEC section 6
    by_scene = {}
    for d in tl["lines"]:
        need(set(d) == {"id", "scene", "speaker", "text", "start", "end", "global_start", "global_end", "wav",
                        "caption", "vo", "fx", "env"}, f"line keys {d['id']}")
        ln = spec.get(d["id"])
        if ln is None:
            continue
        need(d["scene"] == ln.scene and d["speaker"] == ln.speaker and d["text"] == ln.text, f"{d['id']} identity")
        need(d["speaker"] in tl["cast"], f"{d['id']} speaker")
        if d["id"] != "s6_laugh":
            need(d["text"] in script, f"{d['id']} text not verbatim in SCRIPT.md / SPEC.md: {d['text']!r}")
        need(0.0 <= d["start"] < d["end"], f"{d['id']} start/end")
        need(d["end"] <= sdur[d["scene"]] - END_GUARD + 1e-6, f"{d['id']} ends too late ({d['end']})")
        need(abs(d["start"] - ln.target) <= NUDGE + 1e-6, f"{d['id']} moved > {NUDGE}s from target")
        need(abs(d["global_start"] - (sstart[d["scene"]] + d["start"])) < 1e-3, f"{d['id']} global_start")
        need(abs(d["global_end"] - (sstart[d["scene"]] + d["end"])) < 1e-3, f"{d['id']} global_end")
        need(d["caption"] is ln.caption and d["vo"] is ln.vo and d["fx"] == ln.fx, f"{d['id']} flags")
        need(d["fx"] in (None, "phone", "vo", "drowned"), f"{d['id']} fx")
        n_env = round((d["end"] - d["start"]) * FPS)
        env = d["env"]
        need(abs(len(env) - n_env) <= 1, f"{d['id']} env len {len(env)} vs {n_env}")
        need(all(0.0 <= v <= 1.0 for v in env), f"{d['id']} env range")
        need(max(env) >= 0.9, f"{d['id']} env not normalised (max {max(env)})")
        need(env[0] <= 0.35, f"{d['id']} env starts open ({env[0]})")
        need(d["wav"] == f"film/assets/dialogue/{d['id']}.wav", f"{d['id']} wav path")
        wp = os.path.join(ROOT, d["wav"])
        if not os.path.exists(wp):
            errs.append(f"{d['id']} wav missing")
            continue
        a, sr, ch, sw = read_wav(wp)
        need(sr == SR and ch == 1 and sw == 2, f"{d['id']} wav format {sr}/{ch}/{sw}")
        need(abs(len(a) / sr - (d["end"] - d["start"])) <= 1e-3, f"{d['id']} wav duration mismatch")
        pk = 20 * np.log10(np.max(np.abs(a)) + 1e-12)
        need(pk <= PEAK_CEIL_DB + 0.05, f"{d['id']} peak {pk:.2f} dBFS")
        lo = lufs(a)
        need(abs(lo - TARGET_LUFS) <= 0.6 or pk >= PEAK_CEIL_DB - 0.1, f"{d['id']} loudness {lo:.2f} LUFS")
        # trimmed edges: voice within ~20 ms of both ends
        on, off = speech_bounds(a, sr)
        need(on / sr <= EDGE + 0.012 and (len(a) - off) / sr <= EDGE + 0.012, f"{d['id']} edges not trimmed")
        # multi-part lines: the mouth closes in the deliberate pauses
        if len(ln.parts) > 1 and d["id"] != "s4_l1":
            need(min(env[2:-2]) == 0.0, f"{d['id']} mouth never closes in its pauses")
        by_scene.setdefault(d["scene"], []).append(d)
    for sc, arr in by_scene.items():
        story = [ln.id for ln in LINES if ln.scene == sc]
        need([d["id"] for d in arr] == story, f"scene {sc} story order")
        srt = sorted(arr, key=lambda d: d["start"])
        need([d["id"] for d in srt] == story, f"scene {sc} start order")
        for p, q in zip(srt, srt[1:]):
            need(q["start"] >= p["end"] + 0.25 - 1e-6, f"overlap/too tight {p['id']} -> {q['id']}")
    # beats
    bids = [b["id"] for b in tl["beats"]]
    need(len(set(bids)) == len(bids), "duplicate beats")
    need(set(REQUIRED_BEATS) <= set(bids), f"missing beats {set(REQUIRED_BEATS) - set(bids)}")
    B = {b["id"]: b for b in tl["beats"]}
    for b in tl["beats"]:
        need(set(b) == {"id", "scene", "t", "end"}, f"beat keys {b}")
        need(0.0 <= b["t"] <= sdur[b["scene"]], f"beat {b['id']} t out of scene")
        need(b["end"] is None or b["t"] <= b["end"] <= sdur[b["scene"]] + 1e-9, f"beat {b['id']} end")
        need(b["id"].startswith(f"s{b['scene']}_"), f"beat {b['id']} scene")
    Ld = {d["id"]: d for d in tl["lines"]}
    if not errs:
        need(B["s1_tap"]["end"] <= Ld["s1_l1"]["start"], "s1_tap before s1_l1")
        need(Ld["s1_l1"]["end"] <= B["s1_lookaround"]["t"] and B["s1_lookaround"]["end"] <= Ld["s1_l2"]["start"],
             "s1_lookaround between the lines")
        need(B["s2_stare"]["t"] < Ld["s2_l1"]["start"], "s2_stare before s2_l1")
        need(Ld["s2_l2"]["end"] < B["s2_pause"]["t"] < B["s2_ring"]["t"] < sdur[2], "s2_pause/s2_ring after s2_l2")
        need(B["s3_hold"]["t"] >= Ld["s3_l3"]["end"], "s3_hold after 'please hold'")
        need(abs(B["s4_swell"]["t"] - (Ld["s4_l1"]["start"] + 0.8)) < 0.01, "s4_swell = s4_l1 + 0.8")
        need(B["s4_lookbouncer"]["t"] < Ld["s4_l2"]["start"], "s4_lookbouncer before s4_l2")
        need(B["s4_lookhand"]["t"] > Ld["s4_l2"]["end"] and B["s4_exit"]["t"] > B["s4_lookhand"]["t"],
             "s4_lookhand after s4_l2")
        need(B["s5_lower"]["end"] <= Ld["s5_l1"]["start"], "s5_lower before s5_l1")
        need(B["s6_glance"]["t"] < Ld["s6_l1"]["start"], "s6_glance before s6_l1")
        need(abs(B["s6_laugh"]["t"] - Ld["s6_laugh"]["start"]) < 1e-6 and Ld["s6_laugh"]["start"] > Ld["s6_l4"]["end"],
             "s6_laugh after s6_l4")
        need(B["s7_drag"]["end"] <= Ld["s7_l1"]["start"], "s7_drag before s7_l1")
        need(B["s8_fade"]["t"] >= Ld["s8_l3"]["end"], "s8_fade after the last VO line")
        # story order of the SPEC beats inside each scene
        for sc in range(1, 10):
            seq = [bid for bid in REQUIRED_BEATS if B.get(bid, {}).get("scene") == sc]
            ts = [B[bid]["t"] for bid in seq]
            need(ts == sorted(ts), f"scene {sc} beat order {seq}")
    for e in errs:
        print("  FAIL:", e)
    print(f"check: {'OK' if not errs else str(len(errs)) + ' problem(s)'} "
          f"({len(tl['lines'])} lines, {len(tl['beats'])} beats, {len(tl['cast'])} voices)")
    return not errs


def phoneme_report():
    """Print the espeak phonemes Piper will speak for every part (catches misreadings, spelled letters)."""
    from piper.phonemize_espeak import ESPEAK_DATA_DIR, EspeakPhonemizer
    ph = EspeakPhonemizer(ESPEAK_DATA_DIR)
    for ln in LINES:
        with open(os.path.join(VOICE_DIR, CAST[ln.speaker]["model"] + ".onnx.json")) as fh:
            ev = json.load(fh)["espeak"]["voice"]
        for k, p in enumerate(ln.parts):
            if p.say.startswith("[["):
                out = p.say[2:-2]
            else:
                out = " | ".join("".join(s) for s in ph.phonemize(ev, p.say))
            print(f"{ln.id:9s} {ln.speaker:10s} {ev:10s} {p.say!r:52s} {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="re-synthesize wavs even if they exist")
    ap.add_argument("--only", nargs="*", default=None, help="with --force: only these line ids")
    ap.add_argument("--check", action="store_true", help="validate film/timeline.json and the wavs, then exit")
    ap.add_argument("--phonemes", action="store_true", help="print the phonemes of every part, then exit")
    ap.add_argument("--jobs", type=int, default=min(4, os.cpu_count() or 1))
    args = ap.parse_args()
    if args.phonemes:
        phoneme_report()
        return
    if args.check:
        sys.exit(0 if check() else 1)
    build(args.force, args.only, args.jobs)
    sys.exit(0 if check() else 1)


if __name__ == "__main__":
    main()
