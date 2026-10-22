#!/usr/bin/env python3
"""THE STONE AND THE BREAD -- the bard's song "A Kingdom of Stone" (prologue) and its end-card reprise.

    python3 film/audio/song.py              # compose + synthesize everything -> film/assets/song/
    python3 film/audio/song.py --verify     # ... then measure it (pitch, Whisper WER, timing, levels, PNGs)
    python3 film/audio/song.py --only prologue|reprise

Outputs (film/assets/song/, 48 kHz, 24-bit PCM)
  prologue_vocal.wav   mono    the sung lead + its -10 dB double, EQ'd, de-essed, compressed, DRY (no hall)
  prologue_accomp.wav  stereo  lute + recorder + frame drum/tambourine, with their own hall reverb
  prologue_mix.wav     stereo  vocal + the vocal's hall reverb + accompaniment, bus-limited (the finished song)
  reprise_*.wav        same for the end-card reprise (voice + lute only)
  song_timing.json     bpm, meter, and per piece: duration, intro_end, lines (start/end, words, syllables with
                       notes, 24 fps vocal envelope), beats, downbeats, strums (every right-hand stroke),
                       chords, sections, marks.  All times are seconds from the start of THAT piece.
  The stems are at mix level: mix_L/R = vocal (the mono stem added to BOTH channels at unity gain) +
  accomp_L/R + the vocal's hall reverb (not delivered separately), before the bus limiter.

How the singing is made (speech-to-singing, all deterministic)
  1. Score: every syllable of the SPEC 0.2 lyrics (verbatim) has a note (pitch, bar, eighth position, length)
     in 6/8 at motif.TEMPO; motif.py's four-note motif is the hook ("KING-dom of STONE" ... "WAY back to
     BREAD").  Chords one per dotted-quarter beat.  Written 16th-note pickups are sung as two 0.75-eighth
     notes (a singer's rubato that keeps 'and he', 'they had' intelligible); the lute stays strict.
  2. Piper (VITS, en_GB-northern_english_male) is patched in memory (onnx): the per-phoneme durations become
     an input, and both Gaussian noise sources become inputs fed from a seeded numpy RNG (onnxruntime's
     RandomNormalLike is not reproducible).  Each line is one natural utterance whose vowels are already
     stretched to the note lengths: the vowel attack (espeak's stress-mark token) lands exactly on the beat,
     onset consonants sit just before it, codas and word-boundary tokens keep their natural length (x1.1:
     crisp sung consonants), the vowel absorbs the rest.  SAY holds the few respellings that Whisper proved
     necessary; TAKE_SEEDS the best of 8 noise seeds per line (sung-ASR take selection).
  3. WORLD (pyworld harvest / CheapTrick / D4C): the speech F0 is replaced by the melody -- note pitches,
     ~45 ms portamento, a scoop into each phrase, small overshoots on upward leaps, delayed vibrato
     (~5.5 Hz, +-28-35 cents) on notes > 0.38 s, a relaxed fall at line ends, slow random drift of a few
     cents; unvoiced consonant frames stay unvoiced.  VITS sometimes renders a long-held token as near
     silence (a held schwa, the length mark of /uː/): repair_nuclei() refills such frames from the same
     vowel's good frames and lifts nuclei that come out far too quiet; steady_nuclei() re-voices vowels that
     VITS rendered as breath noise (a stretched 'a', 'back', 'lock': mean formant envelope + voiced tilt, else
     they come out whispered); enhance_formants() sharpens the envelope's formant structure above ~500-900 Hz
     (re-pitching and stretching blur it: 'scarf' -> 'scuff'; F1 is left alone, or one harmonic dominates the sung
     vowel).  Resynthesized at 22.05 kHz and upsampled to 48 kHz.
  4. Every sung line is ridden to the same loudness (VOICE line_lufs: raw VITS takes differ by up to 11 dB, and a
     line sung 5-8 dB under its neighbours loses its words to the lute).  A second take (the runner-up seed, +-10 ms
     timing jitter, +5 cents, 0.9x vibrato) doubles the lead at
     -10 dB on the held vowels only (vowel_gate: no doubled, flammed consonants); then high-pass, gentle
     presence EQ, split-band de-esser, compressor (fed at a fixed loudness, so changing one line's take cannot
     change how every other line is compressed); in the mix a synthetic hall IR (band-wise exponentially
     decaying noise, RT60 ~1.45 s, early reflections) fed with 45 ms pre-delay, high-passed at 200 Hz and ducked
     6 dB while he sings, so the words stay dry and close and the room blooms in the gaps.  The lute is EQ'd for
     the voice (-4 dB below ~250 Hz, +6 dB shelf above ~1.5 kHz: less low-mid mud under the words, more pluck) and the
     accompaniment dips 3 dB while he sings: the vocal sits ~8 dB above it in 1-4 kHz, ~6 LU above it overall.
     MIX / ARR hold the mix and arrangement settings; BREATH a catch-breath at the commas where the next pickup
     follows at once.
  Accompaniment: Karplus-Strong lute (exactly tuned loop with fractional delay, double courses, octave strings
  on the basses, fingertip excitation, pluck-position comb, lute-body resonance IR), arpeggios / strums /
  rolls from the chord chart, strings damped when the chord moves on; a recorder (additive + breath noise +
  chiff + delayed vibrato) playing the motif as a counter-melody from the interlude on and resolving
  G4 -> F#4 under the last chord; a light frame drum + tambourine in verse 2; the intro is the bard
  tuning up (a flat A string, the peg turned while it rings, a fifth, two harmonics), a playful run and a
  rolled chord (the book opens on it), then the vamp.  The arrangement builds: verse 1 fingerpicked lute; the
  interlude gives the motif to the recorder (lute steps back); verse 2 strums a little fuller (+1.5 dB) with
  the drum (~6 dB under the lute) and tambourine (~20 dB under) and the recorder doubling the hook 8va (~9 dB
  under); the coda thins to rolls; the final chord rings on (2x decay) under the outro.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from dataclasses import dataclass, field

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter, resample_poly, sosfilt, sosfiltfilt

HERE = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(HERE)
ROOT = os.path.dirname(FILM)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from film.audio import motif as M  # noqa: E402

OUT_DIR = os.path.join(FILM, "assets", "song")
BUILD_DIR = os.path.join(FILM, "build", "song")
VOICE_DIR = os.path.join(FILM, "build", "voices")
SR = 48000
FPS = 24

# ================================================================================================
# THE BARD'S VOICE (cast by sung-output tests: Whisper WER + DNSMOS over several voices/seeds)
# ================================================================================================
VOICE = dict(model="en_GB-northern_english_male-medium", speaker_id=None,
             nat_ls=1.0,        # length_scale used to read the natural (consonant) durations
             cons=1.1,          # consonant length factor (x natural): crisp sung consonants
             article_schwa=False,  # (tested: /ə/ for the article 'a' did not help)
             syllabic_n="keep",   # 'wasn't' keeps its hummed syllabic n
             strip_commas=True,   # Piper sees no commas inside a sung line (they act as phrase breaks)
             ap_pct=30,           # held vowels: aperiodicity capped at the line's 30th-percentile profile
             bound="natural",   # word-boundary tokens: "zero" | "natural" | factor
             pad_mode="natural",  # stretched vowels keep their trailing transition pad natural
             min_frac=0.45,     # the vowel keeps at least this fraction of every note
             noise=0.5, noise_w=0.6,
             seed=7,
             steady=True,       # steady_nuclei(): re-voice breath-noise VITS vowels (see there)
             steady_breathy=0.6,  # ... a monophthong core with less than this raw voiced fraction is re-voiced
             steady_smooth=0,     # ... optional temporal smoothing (frames) of the other held-vowel envelopes
             formant_enh=0.6,   # WORLD envelope formant sharpening on voiced frames (cepstral postfilter); 0 = off
             formant_band=(500, 900),  # ... only above ~500-900 Hz (F2/F3: vowel identity).  Full band also sharpened
                                       # F1, which at sung pitches sits on 2-4 harmonics: one harmonic then dominated
                                       # the vowel (hollow, weak fundamental; 7.9% of frames pitch-ambiguous vs 0.9%)
             cons_db=None,      # articulation: dB boost per consonant class {"plos","fric","sib","nasal","liquid"}
             breath=0.03,       # a line's last note stops this long before the next line's first consonant (s)
             line_lufs=-30.0)   # vocal riding: each sung line (dry) normalized to this K-weighted loudness before the
                                # vocal chain.  VITS takes differ by up to 11 dB (line 2 sat 5-8 dB under line 1 in the
                                # delivered vocal, and lost its words in the mix).  None = off; shaping: LINE_GAIN_DB

# Deliberate per-line level offsets (dB) on top of the riding (musical dynamics); empty = every line equally present.
LINE_GAIN_DB = {}

# Mix settings (one place; make_piece/mixdown read them).  Per-piece values are dicts {piece: value}.
MIX = dict(double_db=-10.0,      # the double take under the lead
           vocal_comp_in_lufs=-28.0,   # the vocal chain's compressor sees the (ridden) vocal at this loudness
           double_gate=True,     # the double sounds only on held vowels (consonants single-tracked, no flams)
           double_floor_db=-30.0,
           hall_send_db=-16.0, hall_predelay=0.045,          # the words stay dry and close, the room is behind them
           hall_rt60={"prologue": 1.45, "reprise": 1.6},
           hall_duck_db=6.0,     # the vocal hall return dips this much while he sings (blooms in the gaps)
           hall_hp=200.0,        # high-pass on the hall send (Hz, 0 = off): no low-mid mud under the words
           acc_gap_lu={"prologue": 6.0, "reprise": 5.0},   # vocal stem loudness above the accompaniment
           acc_duck_db=3.0,      # the accompaniment dips this much (smoothly) while he sings
           acc_dip_db=0.0,       # (optional presence dip at 2.6 kHz on the accompaniment bus; off -- see lute_eq)
           # the lute's tone in the mix [(kind "low"|"high"|"peak", Hz, dB, slope/Q)]: the Karplus-Strong gut strings
           # put nearly all their energy below 500 Hz (masking the voice's low end, nothing in the presence band: the
           # vocal sat 14-17 dB above the accompaniment in 1-4 kHz).  Less mud, more pluck: ~8 dB in 1-4 kHz.
           lute_eq=(("low", 250.0, -4.0, 0.8), ("high", 1500.0, 6.0, 0.8)),
           acc_eq=(),            # extra accompaniment-bus EQ, same format
           rec_gain=0.42, drum_gain=1.0, tamb_gain=0.8,
           target_lufs={"prologue": -17.0, "reprise": -19.0})

# ================================================================================================
# THE SCORE
#   (syllable, pitch, bar, eighth position in bar (0..5, may be fractional), length in eighths)
#   A trailing '-' joins a syllable to the next one (same word).  'E3>D3' = two-note melisma on one vowel.
#   Bar 1 beat 1 is the first downbeat of verse 1; pickups sit in the bar before.
# ================================================================================================
PROLOGUE_LINES = [
    ("s0_l1", "Once upon a time, in a kingdom of stone,", [
        ("Once", "A2", 0, 4, 1), ("u-", "D3", 0, 5, 1), ("pon", "F#3", 1, 0, 2), ("a", "E3", 1, 2, 1),
        ("time,", "F#3", 1, 3, 2), ("in", "G3", 1, 5, .5), ("a", "A3", 1, 5.5, .5),
        ("king-", "B3", 2, 0, 1), ("dom", "A3", 2, 1, 1), ("of", "F#3", 2, 2, 1), ("stone,", "E3", 2, 3, 2)]),
    ("s0_l2", "Lived a town full of folk who were living alone.", [
        ("Lived", "C#3", 2, 5, .5), ("a", "C#3", 2, 5.5, .5),
        ("town", "D3", 3, 0, 1), ("full", "E3", 3, 1, 1), ("of", "F#3", 3, 2, 1),
        ("folk", "A3", 3, 3, 1), ("who", "G3", 3, 4, 1), ("were", "F#3", 3, 5, 1),
        ("liv-", "E3", 4, 0, 1), ("ing", "D3", 4, 1, 1), ("a-", "C#3", 4, 2, 1), ("lone.", "B2", 4, 3, 2)]),
    ("s0_l3", "They had potions for sleeping and charms for the rain,", [
        ("They", "D3", 4, 5, .5), ("had", "E3", 4, 5.5, .5),
        ("po-", "F#3", 5, 0, 1), ("tions", "G3", 5, 1, 1), ("for", "A3", 5, 2, 1),
        ("sleep-", "B3", 5, 3, 1), ("ing", "A3", 5, 4, 1), ("and", "B3", 5, 5, 1),
        ("charms", "C4", 6, 0, 1), ("for", "B3", 6, 1, 1), ("the", "A3", 6, 2, 1), ("rain,", "G3", 6, 3, 2)]),
    ("s0_l4", "And a lock on each heart, and a latch on each pane.", [
        ("And", "G3", 6, 5, .5), ("a", "A3", 6, 5.5, .5),
        ("lock", "B3", 7, 0, 1), ("on", "A3", 7, 1, 1), ("each", "F#3", 7, 2, 1),
        ("heart,", "E3", 7, 3, 2), ("and", "F#3", 7, 5, .5), ("a", "G3", 7, 5.5, .5),
        ("latch", "A3", 8, 0, 1), ("on", "G3", 8, 1, 1), ("each", "E3", 8, 2, 1), ("pane.", "D3", 8, 3, 4)]),
    # -- bar 9: interlude (page turn, the recorder enters with the motif) --
    ("s0_l5", "Now a dragon lived there with a scarf and a sigh,", [
        ("Now", "A2", 9, 4, 1), ("a", "D3", 9, 5, 1),
        ("dra-", "F#3", 10, 0, 1), ("gon", "F#3", 10, 1, 1), ("lived", "E3", 10, 2, 1),
        ("there", "F#3", 10, 3, 1), ("with", "G3", 10, 4, 1), ("a", "A3", 10, 5, 1),
        ("scarf", "B3", 11, 0, 1), ("and", "A3", 11, 1, 1), ("a", "F#3", 11, 2, 1), ("sigh,", "E3", 11, 3, 2)]),
    ("s0_l6", "And he waved at his neighbours, who hurried on by.", [
        ("And", "C#3", 11, 5, .5), ("he", "C#3", 11, 5.5, .5),
        ("waved", "D3", 12, 0, 1), ("at", "E3", 12, 1, 1), ("his", "F#3", 12, 2, 1),
        ("neigh-", "A3", 12, 3, 1), ("bours,", "G3", 12, 4, 1), ("who", "F#3", 12, 5, 1),
        ("hur-", "E3", 13, 0, 1), ("ried", "D3", 13, 1, 1), ("on", "C#3", 13, 2, 1), ("by.", "B2", 13, 3, 2)]),
    ("s0_l7", "Every merchant in town had a stone he could sell —", [
        ("Ev-", "D3", 13, 5, .5), ("ery", "E3", 13, 5.5, .5),
        ("mer-", "F#3", 14, 0, 1), ("chant", "G3", 14, 1, 1), ("in", "A3", 14, 2, 1),
        ("town", "B3", 14, 3, 1), ("had", "A3", 14, 4, 1), ("a", "B3", 14, 5, 1),
        ("stone", "C4", 15, 0, 1), ("he", "B3", 15, 1, 1), ("could", "A3", 15, 2, 1), ("sell", "G3", 15, 3, 2)]),
    ("s0_l8", "But for what he was missing, there wasn't a spell.", [
        ("But", "G3", 15, 5, .5), ("for", "A3", 15, 5.5, .5),
        ("what", "B3", 16, 0, 1), ("he", "A3", 16, 1, 1), ("was", "F#3", 16, 2, 1),
        ("miss-", "E3", 16, 3, 1), ("ing,", "F#3", 16, 4, 1), ("there", "G3", 16, 5, 1),
        ("was-", "A3", 17, 0, 1), ("n't", "G3", 17, 1, 1), ("a", "E3", 17, 2, 1), ("spell.", "D3", 17, 3, 4)]),
    # -- bar 18 (a 3/8 bar): the storyteller's breath; the bard looks up at us --
    ("s0_l9", "So pull up a stool, friend, and hear how it's said:", [
        ("So", "D3", 18, 2, 1),
        ("pull", "F#3", 19, 0, 1), ("up", "E3", 19, 1, 1), ("a", "F#3", 19, 2, 1),
        ("stool,", "A3", 19, 3, 1), ("friend,", "B3", 19, 4, 1), ("and", "C#4", 19, 5, 1),
        ("hear", "D4", 20, 0, 1), ("how", "C#4", 20, 1, 1), ("it's", "B3", 20, 2, 1), ("said:", "A3", 20, 3, 2)]),
    ("s0_l10", "How a kingdom of stone found its way back to bread.", [
        ("How", "G3", 20, 5, .5), ("a", "A3", 20, 5.5, .5),
        ("king-", "B3", 21, 0, 1), ("dom", "A3", 21, 1, 1), ("of", "F#3", 21, 2, 1),
        ("stone", "E3", 21, 3, 2), ("found", "F#3", 21, 5, .5), ("its", "A3", 21, 5.5, .5),
        ("way", "B3", 22, 0, 1), ("back", "A3", 22, 1, 1), ("to", "F#3", 22, 2, 1),
        ("bread.", "E3>D3", 22, 3, "BREAD")]),
]

REPRISE_LINES = [
    ("s9_l1", "So if you've a loaf, friend, you know what to do:", [
        ("So", "A2", 0, 4, 1), ("if", "D3", 0, 5, 1),
        ("you've", "F#3", 1, 0, 2), ("a", "E3", 1, 2, 1),
        ("loaf,", "A3", 1, 3, 1), ("friend,", "B3", 1, 4, 1), ("you", "C#4", 1, 5, 1),
        ("know", "D4", 2, 0, 1), ("what", "C#4", 2, 1, 1), ("to", "B3", 2, 2, 1), ("do:", "A3", 2, 3, 2)]),
    ("s9_l2", "Someone's hungry for bread on the bench next to you.", [
        ("Some-", "G3", 2, 5, .5), ("one's", "A3", 2, 5.5, .5),
        ("hun-", "B3", 3, 0, 1), ("gry", "A3", 3, 1, 1), ("for", "F#3", 3, 2, 1),
        ("bread", "E3", 3, 3, 2), ("on", "F#3", 3, 5, .5), ("the", "A3", 3, 5.5, .5),
        ("bench", "B3", 4, 0, 1), ("next", "A3", 4, 1, 1), ("to", "F#3", 4, 2, 1),
        ("you.", "E3>D3", 4, 3, "YOU")]),
]

# What Piper is fed when it differs from the lyric (same syllables; [[...]] = raw phonemes).  Each respelling
# was chosen because Whisper misheard the plain spelling when sung.  [[hˈɛd]] / [[dɹˈɛɡən]]: espeak's TRAP vowel /æ/,
# stretched and re-pitched, is heard as /ʌ/ or /ɒ/ ('had' -> 'have', 'hot', 'harder'; 'dragon' -> 'drug and'); a singer's
# brighter /ɛ/ (the older-RP 'had') keeps the word.
SAY = {
    "s0_l1": "Once [[ʌpˈɒn]] a time, in a kingdom of stone,",               # a held schwa renders silent
    "s0_l2": "Lived [[eɪ]] town full of folk who were living alone.",      # /ɐ/ heard as 'the'
    "s0_l3": "They [[hˈɛd]] potions for sleeping and charms for the rain,",  # 'They have/hot potions'
    "s0_l4": "And [[ə]] lock on each heart, and [[ə]] latch on each pane.",  # /ɐ/ heard as "I'll"
    "s0_l5": "Now [[ə]] [[dɹˈɛɡən]] lived there with [[ə]] scarf and [[ə]] sigh,",  # 'Now I drag and'; strong
                                                                    # 'ay' + 'dre-' was heard as 'Now Adrian can'
    "s0_l7": "Every merchant in town [[hˈɛd]] a stone he could sell —",     # 'had a' heard as 'harder'
    "s0_l9": "So pull up [[ə]] stool, friend, and hear how it's said:",     # /ɐ/: 'So Paul, there's a still friend'
}

# A catch-breath (s) before the next line where the lyric has a comma/colon and the pickup follows at once
# (the last note stops this long before the next line's first consonant; default VOICE["breath"]).
BREATH = {"s0_l5": 0.10, "s0_l9": 0.10,
          "s9_l1": 0.10}      # reprise: "...what to do: / Someone's hungry" ran on with ~20 ms between the lines

# Best takes: Piper noise seed per line for (lead, double), picked by sung-ASR take selection -- every line
# rendered with 8 seeds, scored by Whisper small.en + base.en WER (+ log-prob); the respelled lines were
# chosen jointly with their spelling.  Lines not listed fall back to default seeds.
# s0_l3/l4/l5/l7/l9 were re-chosen in the final mix context (lute EQ, vocal riding, band-limited formant
# sharpening): spelling x 4-8 seeds per line, each take scored over 10 views (vocal stem; the mix with the
# accompaniment at +0 and +3 dB, two cut points; base.en + small.en, homophones allowed), ranked by mean + worst
# view, vowels required voiced.  A single-view pick is noise: the same take scores 10-45% across these views.
TAKE_SEEDS = {
    "s0_l1": (7017, 6017), "s0_l2": (8048, 3048), "s0_l3": (3079, 5079), "s0_l4": (8110, 7110),
    "s0_l5": (7141, 1141), "s0_l6": (5172, 8172), "s0_l7": (1203, 2203), "s0_l8": (8234, 6234),
    "s0_l9": (3265, 6265), "s0_l10": (8296, 3296), "s9_l1": (2017, 4017), "s9_l2": (3048, 2048),
}


def take_seed(li: int, lid: str, take: int) -> int:
    if lid in TAKE_SEEDS:
        return int(TAKE_SEEDS[lid][take])
    return VOICE["seed"] + 31 * li + 7 * take


# one chord per dotted-quarter beat: {bar: (beat1, beat2)}
PROLOGUE_CHORDS = {0: ("D", "D")}
for _b, _c in enumerate(M.VERSE_PROGRESSION, start=1):
    PROLOGUE_CHORDS[_b] = _c                       # verse 1, bars 1-8
PROLOGUE_CHORDS[9] = ("G", "A")                    # interlude: the motif's own harmony
for _b, _c in enumerate(M.VERSE_PROGRESSION, start=10):
    PROLOGUE_CHORDS[_b] = _c                       # verse 2, bars 10-17
PROLOGUE_CHORDS[17] = ("A7", "Bm")                 # "there wasn't a spell" -- deceptive, sad
PROLOGUE_CHORDS.update({18: ("G", "G"), 19: ("D", "A"), 20: ("G", "A"), 21: ("G", "Em"), 22: ("G", "A7")})
REPRISE_CHORDS = {0: ("D", "D"), 1: ("D", "A"), 2: ("G", "A"), 3: ("G", "A"), 4: ("G", "A7")}

# fermata notes: (first-note seconds, second-note seconds) of the final melisma
FERMATA = {"BREAD": (0.75, 1.40), "YOU": (0.75, 1.35)}


# ================================================================================================
# tempo grid
# ================================================================================================
class Grid:
    """Eighth-note grid -> seconds.  Bar 0 starts at t_bar0.  bar_len = {bar: eighths} for odd-length bars
    (a 3/8 storyteller's breath); rit = [(bar_from, bar_to, f_from, f_to)] stretches eighth lengths smoothly
    (ritardando; bar positions may be fractional)."""

    def __init__(self, t_bar0: float, tempo: float, n_bars: int, rit=(), bar_len=None):
        self.eighth = M.eighth_seconds(tempo)
        self.bar_len = {b: 6 for b in range(n_bars + 3)}
        self.bar_len.update(bar_len or {})
        self.bar0 = np.concatenate([[0], np.cumsum([self.bar_len[b] for b in range(n_bars + 3)])])
        n = int(self.bar0[-1])
        f = np.ones(n)
        for b0, b1, f0, f1 in rit:
            i0, i1 = int(round(self._idx(b0))), int(round(self._idx(b1)))
            x = np.linspace(0, 1, i1 - i0, endpoint=False) + 0.5 / max(i1 - i0, 1)
            f[i0:i1] = f0 + (f1 - f0) * (x * x * (3 - 2 * x))
            f[i1:] = f1
        self.e = self.eighth * f
        self.cum = np.concatenate([[t_bar0], t_bar0 + np.cumsum(self.e)])
        self.t_bar0 = t_bar0

    def _idx(self, barf):
        b = int(math.floor(barf + 1e-9))
        return self.bar0[b] + (barf - b) * self.bar_len[b]

    def t(self, bar, pos=0.0) -> float:
        x = self.bar0[bar] + pos
        i = int(math.floor(x + 1e-9))
        return float(self.cum[i] + (x - i) * self.e[i])

    def dur(self, bar, pos, length) -> float:
        return self.t(bar, pos + length) - self.t(bar, pos)


PROLOGUE_T_BAR0 = 3.00          # the vamp bar (bar 0) starts here; before it the bard tunes up
PROLOGUE_GRID = Grid(PROLOGUE_T_BAR0, M.TEMPO, 23, bar_len={18: 3},
                     rit=[(21, 22, 1.0, 1.14), (22, 22.5, 1.14, 1.42)])
REPRISE_T_BAR0 = 0.0            # the lute's soft rolled chord comes in at bar 0, eighth 1 = t 0 (timeline.json and S9
                                # are built on this timing: reprise 11.947 s); mixdown() fades every stem in over 3 ms,
                                # so the file never starts on a step
REPRISE_GRID = Grid(REPRISE_T_BAR0 - M.eighth_seconds(M.REPRISE_TEMPO), M.REPRISE_TEMPO, 5,
                    rit=[(3.5, 4.0, 1.0, 1.10), (4.0, 4.5, 1.10, 1.38)])


def nm(name: str) -> int:
    return M.note(name)


# ================================================================================================
# phonemes -> syllables
# ================================================================================================
VOWELS = set("aeiouæɐɑɒɔəɚɛɜɪʊʌᵻɘɵʉɨyøœɤɯ")
LENGTH, SYLLABIC = "ː", "̩"
STRESS = set("ˈˌ")
PUNCT = set(",.;:!?—-")
SONORANT = set("mnŋlɹrwjɾɫ")
VOICED_OBS = set("bdɡvðzʒ")
UNVOICED = set("ptkfθsʃhxç")
CONS_FACTOR = {"h": 1.5}       # extra length for weak consonants that vanish when sung (who, had, hurried)
ONSETS = {"pl", "pɹ", "bl", "bɹ", "tɹ", "dɹ", "kl", "kɹ", "kw", "ɡl", "ɡɹ", "ɡw", "fl", "fɹ", "θɹ", "ʃɹ",
          "sl", "sw", "sm", "sn", "sp", "st", "sk", "pj", "bj", "tj", "dj", "kj", "mj", "nj", "fj", "vj", "hj",
          "lj", "tʃ", "dʒ", "θw", "tw", "dw", "sj", "spl", "spɹ", "stɹ", "skɹ", "skw", "skj", "spj", "stj"}


@dataclass
class Syl:
    word: int
    onset: list = field(default_factory=list)      # phoneme indices (consonants before the vowel)
    nucleus: list = field(default_factory=list)    # stress mark(s) + vowel(s) (+ length mark)
    coda: list = field(default_factory=list)


def _is_vowel(p):
    return p in VOWELS or p == LENGTH


def syllabify(ph):
    """Flat Piper phoneme list of one line -> syllables (maximal-onset split inside words; stress marks
    belong to the nucleus because acoustically they are the vowel's attack)."""
    words, cur = [], []
    for i, p in enumerate(ph):
        if p == " " or p in PUNCT:
            if cur:
                words.append(cur)
                cur = []
        else:
            cur.append(i)
    if cur:
        words.append(cur)
    syls = []
    for wi, idx in enumerate(words):
        toks = [ph[i] for i in idx]
        nuc, k = [], 0
        while k < len(toks):
            if _is_vowel(toks[k]):
                j = k
                while j < len(toks) and _is_vowel(toks[j]):
                    j += 1
                a = k
                while a > 0 and toks[a - 1] in STRESS:
                    a -= 1
                nuc.append((a, j))
                k = j
            elif k + 1 < len(toks) and toks[k + 1] == SYLLABIC:
                nuc.append((k, k + 2))
                k += 2
            else:
                k += 1
        if not nuc:
            continue
        ws = [Syl(word=wi, nucleus=[idx[q] for q in range(a, b)]) for a, b in nuc]
        ws[0].onset = [idx[q] for q in range(0, nuc[0][0])]
        ws[-1].coda = [idx[q] for q in range(nuc[-1][1], len(toks))]
        for n in range(len(nuc) - 1):
            mid = list(range(nuc[n][1], nuc[n + 1][0]))
            split = len(mid)
            for s in range(len(mid) + 1):
                cl = "".join(toks[q] for q in mid[s:])
                if len(mid) - s <= 1 and not (len(mid) - s == 1 and toks[mid[s]] == "ŋ") or cl in ONSETS:
                    split = s
                    break
            ws[n].coda = [idx[q] for q in mid[:split]]
            ws[n + 1].onset = [idx[q] for q in mid[split:]]
        syls.extend(ws)
    return syls


def sing_phonemes(ph):
    """Singing respellings (VOICE options): the article 'a' /ɐ/ -> /ə/ (espeak-rp's /ɐ/ is heard as 'I' /
    'the' when sung); syllabic n either kept (sung 'wasn't' = /wɒzn̩t/, the n hummed) or /ən/."""
    out = []
    for i, p in enumerate(ph):
        if p == SYLLABIC and out and VOICE.get("syllabic_n", "keep") != "keep":
            out[-1:] = ["ə", out[-1]]
            continue
        if (p == "ɐ" and VOICE.get("article_schwa", True) and (i == 0 or ph[i - 1] == " ")
                and (i + 1 == len(ph) or ph[i + 1] in " ,.")):
            out.append("ə")
            continue
        out.append(p)
    return out


# ================================================================================================
# timed Piper: VITS with the per-phoneme durations as an input
# ================================================================================================
def _patched_model(path):
    """Load a Piper VITS model and patch it (in memory) so that
       * the per-phoneme-id durations are an input ("dur_override") and the predicted ones an output, and
       * both Gaussian noise sources (duration predictor + latent prior) are inputs ("noise_dp", "noise_z"):
         onnxruntime's RandomNormalLike is not reproducible across runs, ours is (seeded numpy)."""
    import onnx
    m = onnx.load(path)
    g = m.graph
    ceil = [n for n in g.node if n.op_type == "Ceil"]
    rnd = [n for n in g.node if n.op_type == "RandomNormalLike"]
    if len(ceil) != 1 or len(rnd) != 2:
        raise RuntimeError("unexpected VITS graph in " + path)
    cname = ceil[0].output[0]
    vi = onnx.helper.ValueInfoProto()
    vi.name = cname
    g.output.append(vi)                       # expose the predicted durations ...
    g.input.append(onnx.helper.make_tensor_value_info("dur_override", onnx.TensorProto.FLOAT, [1, 1, None]))
    for n in g.node:                          # ... and let ours drive the length regulator
        if n is not ceil[0]:
            for i, name in enumerate(n.input):
                if name == cname:
                    n.input[i] = "dur_override"
    names = {}
    for n in rnd:
        key = "noise_dp" if n.name.startswith("/dp/") else "noise_z"
        names[key] = n.output[0]
        g.node.remove(n)
        g.input.append(onnx.helper.make_tensor_value_info(n.output[0], onnx.TensorProto.FLOAT, [1, None, None]))
    return m.SerializeToString(), names


class TimedPiper:
    def __init__(self, model, speaker_id=None):
        import onnxruntime as ort
        from piper import PiperVoice
        from piper.config import PiperConfig
        path = os.path.join(VOICE_DIR, model + ".onnx")
        with open(path + ".json", encoding="utf-8") as fh:
            cfg = json.load(fh)
        self.sr = int(cfg["audio"]["sample_rate"])
        self.hop = 256
        self.sid = speaker_id
        so = ort.SessionOptions()
        so.intra_op_num_threads = 1
        so.inter_op_num_threads = 1
        blob, self.noise_names = _patched_model(path)
        self.sess = ort.InferenceSession(blob, sess_options=so, providers=["CPUExecutionProvider"])
        self.voice = PiperVoice(config=PiperConfig.from_dict(cfg), session=self.sess)
        self.multi = cfg["num_speakers"] > 1
        self.channels = 192
        for c in (192, 256, 128, 384):          # latent width of this model (probe once)
            try:
                self.channels = c
                self.run([1, 0, 2], np.ones(3), 0.5, 1.0, 0.6, 0)
                break
            except Exception:
                continue

    def phonemize(self, text):
        out = []
        for s in self.voice.phonemize(text):
            out.extend(s)
        return out

    def run(self, ids, dur, ns, ls, nw, seed):
        """-> (audio float64 at self.sr, predicted frames per id).  Deterministic for a given seed."""
        rng = np.random.default_rng(int(seed))
        dur = np.asarray(dur, np.float32)
        args = {"input": np.array([ids], np.int64), "input_lengths": np.array([len(ids)], np.int64),
                "scales": np.array([ns, ls, nw], np.float32), "dur_override": dur.reshape(1, 1, -1),
                self.noise_names["noise_dp"]: rng.standard_normal((1, 2, len(ids))).astype(np.float32),
                self.noise_names["noise_z"]: rng.standard_normal((1, self.channels, max(1, int(dur.sum()))))
                .astype(np.float32)}
        if self.multi:
            args["sid"] = np.array([0 if self.sid is None else self.sid], np.int64)
        out = self.sess.run(None, args)
        return out[0].reshape(-1).astype(np.float64), out[1].reshape(-1).astype(np.float64)


# ================================================================================================
# notes
# ================================================================================================
@dataclass
class Note:
    syl: str            # syllable as written in the score ("king-", "stone,")
    start: float        # vowel onset (s, piece time)
    end: float          # end of the note's sound (s)
    pitches: list       # MIDI (two for a melisma)
    split: float = 0.5  # melisma: fraction of the note on the first pitch
    word: int = 0
    bar: int = 0
    pos: float = 0.0


PICKUP_SWING = 0.75     # a written pair of 16ths (at eighths 5 and 5.5) is sung as two 0.75-eighth notes
                        # starting at 4.5: the singer's rubato gives short pickups ('and he', 'they had')
                        # room to be understood, taking it from the dotted note before; the lute stays strict


def swing_pickups(spec):
    out = list(spec)
    for k in range(len(out) - 1):
        s0, p0, b0, x0, l0 = out[k]
        s1, p1, b1, x1, l1 = out[k + 1]
        if b0 == b1 and x0 == 5 and x1 == 5.5 and l0 == 0.5 and l1 == 0.5:
            out[k] = (s0, p0, b0, 6 - 2 * PICKUP_SWING, PICKUP_SWING)
            out[k + 1] = (s1, p1, b1, 6 - PICKUP_SWING, PICKUP_SWING)
    return out


def score_notes(lines, grid):
    """lines -> list of (line_id, text, [Note])"""
    out = []
    for lid, text, spec in lines:
        notes, w = [], 0
        for k, (syl, pitch, bar, pos, length) in enumerate(swing_pickups(spec)):
            st = grid.t(bar, pos)
            ps = [nm(p) for p in pitch.split(">")]
            split = 0.5
            if isinstance(length, str):
                a, b = FERMATA[length]
                en = st + a + b
                split = a / (a + b)
            else:
                en = grid.t(bar, pos + length)
            notes.append(Note(syl=syl, start=st, end=en, pitches=ps, split=split, word=w, bar=bar, pos=pos))
            if not syl.endswith("-"):
                w += 1
        for k in range(len(notes) - 1):
            notes[k].end = notes[k + 1].start          # legato inside a line
        out.append((lid, text, notes))
    return out


def words_of(text):
    import re
    t = text.replace("—", " ")
    return [w for w in (re.sub(r"[^A-Za-z']", "", x) for x in t.split()) if w]


# ================================================================================================
# the vocal: allocate durations, synthesize, re-pitch with WORLD
# ================================================================================================
def _unit_ids(n_ph):
    """Piper id layout ^ _ p1 _ p2 _ ... pN _ $  ->  (token id index, pad id index) per phoneme."""
    return [(2 + 2 * k, 3 + 2 * k) for k in range(n_ph)]


def plan_line(tp, text, notes, next_onset_start=None, seed=7, nat_ls=None, cons=None, bound=None,
              pad_mode=None, min_frac=None, say=None, breath=None):
    """Phonemize + syllabify + allocate phoneme durations so each nucleus starts at its note start.
    Consonants (and the word-boundary tokens between words) keep ~natural length; the vowel absorbs the rest
    of the note.  Returns ids, frame durations, utterance start time, phoneme spans and roles."""
    nat_ls = VOICE["nat_ls"] if nat_ls is None else nat_ls
    cons = VOICE["cons"] if cons is None else cons
    bound = VOICE["bound"] if bound is None else bound
    pad_mode = VOICE["pad_mode"] if pad_mode is None else pad_mode
    min_frac = VOICE["min_frac"] if min_frac is None else min_frac
    say = (say or text).replace("\u2014", ",").replace(":", ",").replace(";", ",")
    if VOICE.get("strip_commas", True):      # legato: no phrase breaks inside a sung line
        say = say.rstrip(" ,.")
        say = say.replace(",", "") + "."
    ph = sing_phonemes(tp.phonemize(say))
    syls = syllabify(ph)
    if len(syls) != len(notes):
        raise RuntimeError(f"{text!r}: {len(syls)} sung syllables from espeak vs {len(notes)} notes: "
                           + " ".join("".join(ph[i] for i in s.onset + s.nucleus + s.coda) for s in syls))
    ids = tp.voice.phonemes_to_ids(ph)
    _, nat = tp.run(ids, np.ones(len(ids)), VOICE["noise"], nat_ls, VOICE["noise_w"], seed)
    fr = tp.hop / tp.sr
    units = _unit_ids(len(ph))
    u = np.array([(nat[a] + nat[b]) * fr for a, b in units])
    role = ["bound"] * len(ph)
    syl_of = [-1] * len(ph)
    for si, s in enumerate(syls):
        for i in s.onset:
            role[i], syl_of[i] = "on", si
        for i in s.nucleus:
            role[i], syl_of[i] = ("stress" if ph[i] in STRESS else "nuc"), si
        for i in s.coda:
            role[i], syl_of[i] = "coda", si
    n = len(notes)
    # boundary tokens (spaces / punctuation) belong to the gap after the syllable before them
    bnd = [[] for _ in range(n)]
    last = -1
    for i in range(len(ph)):
        if role[i] == "bound":
            if 0 <= last < n - 1:
                bnd[last].append(i)
        else:
            last = syl_of[i]
    bscale = 0.0 if bound == "zero" else (cons if bound == "natural" else float(bound))
    cf = np.array([cons * CONS_FACTOR.get(p, 1.0) for p in ph])      # per-phoneme consonant factor
    on_d = np.array([sum(u[i] * cf[i] for i in s.onset) for s in syls])
    co_d = np.array([sum(u[i] * cf[i] for i in s.coda) for s in syls])
    bd_d = np.array([sum(u[i] for i in bnd[k]) for k in range(n)]) * bscale
    st_d = np.array([sum(u[i] for i in s.nucleus if ph[i] in STRESS) for s in syls])
    starts = np.array([nt.start for nt in notes])
    ends = np.array([nt.end for nt in notes])
    if next_onset_start is not None:
        ends[-1] = min(ends[-1], next_onset_start - (VOICE.get("breath", 0.03) if breath is None else breath))
    # consonants squeezed (jointly per syllable boundary) only when the vowel would get < min_frac of the note
    sc = np.ones(n)          # scale of [coda k + boundary k + onset k+1]
    for k in range(n):
        ioi = (starts[k + 1] if k + 1 < n else ends[k]) - starts[k]
        need = co_d[k] + bd_d[k] + (on_d[k + 1] if k + 1 < n else 0.0)
        min_v = max(0.06, min_frac * ioi)
        if ioi - st_d[k] - need < min_v:
            sc[k] = float(np.clip((ioi - st_d[k] - min_v) / max(need, 1e-6), 0.35, 1.0))
    tok = np.zeros(len(ph))
    for k, s in enumerate(syls):
        for i in s.onset:
            tok[i] = u[i] * cf[i] * (sc[k - 1] if k > 0 else 1.0)
        for i in s.coda:
            tok[i] = u[i] * cf[i] * sc[k]
        for i in bnd[k]:
            tok[i] = u[i] * bscale * sc[k]
    for k, s in enumerate(syls):
        ioi = (starts[k + 1] if k + 1 < n else ends[k]) - starts[k]
        gap = sum(tok[i] for i in s.coda) + sum(tok[i] for i in bnd[k])
        nxt_on = sum(tok[i] for i in syls[k + 1].onset) if k + 1 < n else 0.0
        nuc_total = ioi - gap - nxt_on
        strs = [i for i in s.nucleus if ph[i] in STRESS]
        vows = [i for i in s.nucleus if ph[i] not in STRESS]
        for i in strs:
            tok[i] = min(u[i], 0.35 * nuc_total)
        rest = max(nuc_total - sum(tok[i] for i in strs), 0.03)
        natv = np.array([u[i] for i in vows]) + 1e-4
        chars = "".join(ph[i] for i in vows)
        if len(vows) == 1:
            tok[vows[0]] = rest
        elif LENGTH in chars or SYLLABIC in chars:
            for i, w in zip(vows, natv / natv.sum()):
                tok[i] = rest * w
        else:   # diphthong: hold the first element, glide at the end (GOAT /əʊ/ keeps more of its glide)
            share = 0.42 if chars.startswith("əʊ") else 0.30
            tail = min(natv[1:].sum() * 1.6, share * rest)
            tok[vows[0]] = rest - tail
            for i, w in zip(vows[1:], natv[1:] / natv[1:].sum()):
                tok[i] = tail * w
    BOS, EOS = 0.07, 0.06
    t_first = starts[0] - sum(tok[i] for i in syls[0].onset)
    t0 = t_first - BOS
    seq = [(0, BOS * 0.7), (1, BOS * 0.3)]
    for k, (a, b) in enumerate(units):
        d = tok[k]
        na, nb = nat[a], nat[b]
        if role[k] == "nuc" and pad_mode == "natural" and d > (na + nb) * fr:
            pad = min(nb * fr, 0.5 * d)          # stretched vowel: keep the pad (transition) natural
            seq += [(a, d - pad), (b, pad)]
        elif na + nb > 0:
            seq += [(a, d * na / (na + nb)), (b, d * nb / (na + nb))]
        else:
            seq += [(a, d), (b, 0.0)]
    seq.append((len(ids) - 1, EOS))
    dur = np.zeros(len(ids))
    t_acc, f_acc = 0.0, 0
    start_frame = {}
    for idx, sec in seq:
        t_acc += sec
        f1 = int(round(t_acc / fr))
        dur[idx] = max(0, f1 - f_acc)
        start_frame[idx] = f_acc
        f_acc = f1
    spans = []
    for k, (a, b) in enumerate(units):
        spans.append((start_frame[a] * fr, (start_frame[a] + dur[a] + dur[b]) * fr))
    return dict(ph=ph, syls=syls, ids=ids, dur=dur, t0=t0, spans=spans, role=role, syl_of=syl_of,
                ends=ends, fr=fr)


def smooth_noise(n, rate, cutoff, rng):
    w = rng.standard_normal(n + 400)
    b, a = butter(2, min(0.99, cutoff / (rate / 2)))
    y = lfilter(b, a, w)[400:400 + n]
    return y / (np.std(y) + 1e-9)


def f0_track(t_abs, notes, plan, rng, vib_scale=1.0, cents=0.0, vib_rate=5.5):
    """Target melody (MIDI float) on absolute frame times."""
    ph, syls, spans, t0 = plan["ph"], plan["syls"], plan["spans"], plan["t0"]
    n = len(notes)
    seg = []
    for k, s in enumerate(syls):
        idx = s.onset + s.nucleus
        seg.append(t0 + min(spans[i][0] for i in idx))
    seg.append(np.inf)
    m = np.zeros_like(t_abs)
    for k, nt in enumerate(notes):
        a = seg[k] if k > 0 else -np.inf
        sel = (t_abs >= a) & (t_abs < seg[k + 1])
        if len(nt.pitches) == 1:
            m[sel] = nt.pitches[0]
        else:
            tsplit = nt.start + nt.split * (nt.end - nt.start)
            m[sel & (t_abs < tsplit)] = nt.pitches[0]
            m[sel & (t_abs >= tsplit)] = nt.pitches[1]
    dt = t_abs[1] - t_abs[0]
    L = max(3, int(round(0.045 / dt)) | 1)
    ker = np.hanning(L + 2)[1:-1]
    ker /= ker.sum()
    out = np.convolve(np.pad(m, (L // 2, L // 2), mode="edge"), ker, mode="valid")
    for k, nt in enumerate(notes):
        dur = nt.end - nt.start
        sel = (t_abs >= nt.start - 0.06) & (t_abs < nt.end)
        tt = t_abs[sel] - nt.start
        if k == 0:                                         # scoop into the phrase
            out[sel] += -0.65 * np.exp(-np.maximum(tt + 0.06, 0) / 0.055)
        elif nt.pitches[0] - notes[k - 1].pitches[-1] >= 4:   # small overshoot on an upward leap
            out[sel] += 0.18 * np.maximum(tt, 0) / 0.04 * np.exp(1 - np.maximum(tt, 0) / 0.04) * (tt > 0)
        if dur > 0.38:
            onset = min(0.20, 0.35 * dur)
            ramp = np.clip((tt - onset) / 0.18, 0, 1)
            depth = (0.28 + 0.07 * np.clip((dur - 0.8) / 0.8, 0, 1)) * vib_scale
            rate = vib_rate + 0.15 * rng.standard_normal()
            fade = np.clip((dur - tt) / 0.07, 0, 1)
            out[sel] += depth * ramp * fade * np.sin(2 * np.pi * rate * np.maximum(tt - onset, 0))
        if k == n - 1:                                     # relaxed fall at the very end of the line
            tail = np.clip((tt - (dur - 0.09)) / 0.09, 0, 1)
            out[sel] -= 0.35 * tail * tail
    out += 0.055 * smooth_noise(len(t_abs), 1 / dt, 1.3, rng) + 0.012 * smooth_noise(len(t_abs), 1 / dt, 9, rng)
    return out + cents / 100.0


def world_sing(x, fs, plan, notes, rng, f0_floor=60.0, f0_ceil=420.0, warp=1.0, **kw):
    import pyworld as pw
    f0, t = pw.harvest(x, fs, f0_floor=f0_floor, f0_ceil=f0_ceil, frame_period=5.0)
    ph, role, spans = plan["ph"], plan["role"], plan["spans"]
    tok = np.full(len(t), -1)
    for i, (a, b) in enumerate(spans):
        tok[(t >= a) & (t < b)] = i
    voiced_cls = np.array([i >= 0 and (role[i] in ("nuc", "stress") or ph[i] in SONORANT or ph[i] in VOICED_OBS)
                           for i in tok])
    unv_cls = np.array([i >= 0 and ph[i] in UNVOICED for i in tok])
    f0r = f0.copy()
    v = f0r > 0
    if v.sum() > 2:
        lf = np.interp(np.arange(len(f0r)), np.where(v)[0], np.log(f0r[v]))
        fill = (~v) & voiced_cls
        f0r[fill] = np.exp(lf[fill])
    sp = pw.cheaptrick(x, f0r, t, fs)
    ap = pw.d4c(x, f0r, t, fs)
    sp, ap, f0r, repaired = repair_nuclei(sp, ap, f0r, t, plan, fs, f0_raw=f0)
    if VOICE.get("steady", True):
        sp, ap, nb = steady_nuclei(sp, ap, t, plan, f0, fs, breathy=VOICE.get("steady_breathy", 0.6),
                                   smooth_frames=VOICE.get("steady_smooth", 0))
        repaired += nb
    ap = clean_phonation(ap, t, plan, pct=VOICE.get("ap_pct", 30))
    if warp != 1.0:          # formant warp (<1 lowers formants: a touch darker / warmer)
        nb = sp.shape[1]
        src = np.clip(np.arange(nb) * warp, 0, nb - 1)
        sp = np.array([np.interp(src, np.arange(nb), row) for row in sp])
    target = f0_track(t + plan["t0"], notes, plan, rng, **kw)
    voiced = (f0r > 0) & ~unv_cls
    f0o = np.where(voiced, 440.0 * 2.0 ** ((target - 69.0) / 12.0), 0.0)
    if VOICE.get("formant_enh", 0.0) > 0:
        sp = enhance_formants(sp, np.where(voiced)[0], VOICE["formant_enh"], fs, band=VOICE.get("formant_band"))
    y = pw.synthesize(f0o, sp, ap, fs, frame_period=5.0)
    return y, dict(t=t, f0_in=f0, f0_out=f0o, target=target, voiced=voiced, repaired=repaired)


def enhance_formants(sp, frames, beta, fs, q_lo=0.0004, q_hi=0.0045, band=None):
    """Formant sharpening of WORLD envelopes (the cepstral 'postfilter' of vocoded TTS).  Re-pitching a speech
    envelope to sung notes and stretching its vowels blurs the formants (vowels drift toward a neutral 'uh': scarf
    -> 'scuff', heart -> 'horse'); in the given frames the log envelope's cepstrum between quefrencies q_lo..q_hi
    (the formant structure, above the spectral tilt and below the F0 scale) is scaled by up to (1 + beta) with a
    raised-cosine taper, i.e. formant peaks up and valleys down in dB.  Each frame keeps its energy.
    band=(f_lo, f_hi): sharpen only above f_lo (smooth crossfade to full effect at f_hi), energy kept in that band.
    At sung pitches F1 is sampled by only 2-4 harmonics: sharpening it makes ONE harmonic dominate the vowel (a hollow,
    whistly tone with a weak fundamental) while vowel identity for the ear lives mostly in F2/F3."""
    if beta <= 0 or len(frames) == 0:
        return sp
    sp = sp.copy()
    L = np.log(sp[frames] + 1e-20)
    c = np.fft.irfft(L, axis=1)
    n = c.shape[1]
    q = np.minimum(np.arange(n), n - np.arange(n)) / fs
    lift = np.zeros(n)
    rise = (q >= q_lo) & (q < 2 * q_lo)
    lift[rise] = 0.5 - 0.5 * np.cos(np.pi * (q[rise] - q_lo) / q_lo)
    lift[(q >= 2 * q_lo) & (q <= 0.75 * q_hi)] = 1.0
    fall = (q > 0.75 * q_hi) & (q <= q_hi)
    lift[fall] = 0.5 + 0.5 * np.cos(np.pi * (q[fall] - 0.75 * q_hi) / (0.25 * q_hi))
    L2 = np.fft.rfft(c * (1.0 + beta * lift)[None, :], axis=1).real
    if band is None:
        S2 = np.exp(L2)
        S2 *= (sp[frames].sum(axis=1) / (S2.sum(axis=1) + 1e-30))[:, None]
    else:
        f = np.arange(L.shape[1]) * fs / 2.0 / (L.shape[1] - 1)
        w = np.clip((f - band[0]) / float(band[1] - band[0]), 0.0, 1.0)
        w = w * w * (3 - 2 * w)
        S2 = np.exp(L + w[None, :] * (L2 - L))
        hb = f >= band[0]
        g = sp[frames][:, hb].sum(axis=1) / (S2[:, hb].sum(axis=1) + 1e-30)
        S2 *= 1.0 + w[None, :] * (g[:, None] - 1.0)
    sp[frames] = S2
    return sp


CONS_CLASS = {**{p: "plos" for p in "ptkbdɡ"}, **{p: "fric" for p in "fvθðhx"}, **{p: "sib" for p in "szʃʒ"},
              **{p: "nasal" for p in "mnŋ"}, **{p: "liquid" for p in "lɹwj"}}


def articulate(y, sr, plan, cons_db, ramp=0.008):
    """Sung diction: consonants (onsets/codas) lifted by class (dB), smooth ramps; vowels untouched.  Stretched
    vowels dominate a sung line's energy and the hall/lute mask the short consonants that carry the words."""
    if not cons_db:
        return y
    g = np.zeros(len(y))
    for i, (a, b) in enumerate(plan["spans"]):
        if plan["role"][i] not in ("on", "coda"):
            continue
        db = cons_db.get(CONS_CLASS.get(plan["ph"][i], ""), 0.0)
        if db:
            s, e = int(a * sr), int(b * sr)
            g[max(0, s):max(0, e)] = np.maximum(g[max(0, s):max(0, e)], db)
    L = int(ramp * sr) | 1
    k = np.hanning(L + 2)[1:-1]
    g = np.convolve(g, k / k.sum(), mode="same")
    return y * 10 ** (g / 20)


def steady_nuclei(sp, ap, t, plan, f0_raw, fs, breathy=0.6, smooth_frames=0, margin=0.025):
    """Sung vowels hold a steady vocal-tract shape.  VITS sometimes renders a stretched vowel (an unstressed 'a', or a
    short vowel before a voiceless coda: 'back', 'lock') as breath noise: harvest finds little periodicity there, and
    CheapTrick's envelope of noise jitters at random from one 5 ms frame to the next, so even re-voiced it comes out
    rough/whispered (a sung 'a' that is heard as nothing).  Per sung nucleus core (margins kept for the formant
    transitions):
      * a breathy monophthong (raw voiced fraction < `breathy`): the log envelope becomes the core's mean (its formant
        average) with the line's voiced-vowel spectral tilt, frame energy kept smooth, and the aperiodicity capped at
        the line's typical sung-vowel profile (diphthongs keep their glide and are left alone);
      * smooth_frames > 0: light temporal smoothing of every other nucleus's log envelope (smooth_frames x 5 ms).
    Returns (sp, ap, notes)."""
    sp, ap = sp.copy(), ap.copy()
    spans, syls, ph = plan["spans"], plan["syls"], plan["ph"]
    cores, mono = [], []
    for sy in syls:
        a, b = spans[sy.nucleus[0]][0] + margin, spans[sy.nucleus[-1]][1] - margin
        cores.append(np.where((t >= a) & (t < b))[0])
        vows = "".join(ph[i] for i in sy.nucleus if ph[i] not in STRESS and ph[i] != LENGTH)
        mono.append(len(vows) == 1)
    vfr = [float(np.mean(f0_raw[ix] > 0)) if len(ix) else 1.0 for ix in cores]
    good = [ix for ix, v in zip(cores, vfr) if len(ix) and v >= breathy]
    ap_ref = np.median(ap[np.concatenate(good)], axis=0) if good else None
    # the line's voiced-vowel spectral tilt (low quefrencies of the mean log envelope of its well-voiced vowels)
    tilt_ref = None
    if good:
        c_ref = np.fft.irfft(np.log(sp[np.concatenate(good)] + 1e-20).mean(axis=0))
        nq = len(c_ref)
        qq = np.minimum(np.arange(nq), nq - np.arange(nq))
        tilt_ref = (c_ref, qq <= int(round(0.0004 * fs)))     # quefrency < 0.4 ms: tilt / overall shape
    notes = []
    k = np.hanning(max(smooth_frames, 1) + 2)[1:-1]
    k /= k.sum()
    for si, (ix, v) in enumerate(zip(cores, vfr)):
        if len(ix) < 3:
            continue
        L = np.log(sp[ix] + 1e-20)
        if v < breathy and mono[si]:
            e = L.mean(axis=1)                                 # per-frame log energy (smoothed)
            es = np.convolve(np.pad(e, (2, 2), mode="edge"), np.ones(5) / 5, mode="valid")
            M_ = L.mean(axis=0)
            if tilt_ref is not None:                           # breath is far brighter than voice: voiced tilt,
                c = np.fft.irfft(M_)                           # own formant detail
                c[tilt_ref[1]] = tilt_ref[0][tilt_ref[1]]
                M_ = np.fft.rfft(c).real
            sp[ix] = np.exp(M_[None, :] - M_.mean() + es[:, None])
            if ap_ref is not None:
                ap[ix] = np.minimum(ap[ix], ap_ref[None, :])
            notes.append((si, f"breathy nucleus re-voiced (raw voiced {v:.2f})"))
        elif smooth_frames > 1 and len(ix) > smooth_frames:
            Lp = np.pad(L, ((smooth_frames // 2, smooth_frames // 2), (0, 0)), mode="edge")
            sp[ix] = np.exp(np.apply_along_axis(lambda c: np.convolve(c, k, mode="valid"), 0, Lp))
    return sp, ap, notes


def clean_phonation(ap, t, plan, pct=30):
    """Sung vowels are phonated more cleanly than breathy read speech: inside each held vowel (stress mark +
    vowel tokens, transitions excluded) cap D4C's aperiodicity at the line's own clean profile (per-bin
    `pct` percentile over all its held-vowel frames).  Consonants keep their noise."""
    if pct is None or pct >= 100:
        return ap
    spans, syls, ph = plan["spans"], plan["syls"], plan["ph"]
    held = []
    for sy in syls:
        a, b = spans[sy.nucleus[0]][0], spans[sy.nucleus[-1]][1]
        ix = np.where((t >= a + 0.02) & (t < b - 0.03))[0]
        if len(ix):
            held.append(ix)
    if not held:
        return ap
    allix = np.concatenate(held)
    prof = np.percentile(ap[allix], pct, axis=0)
    ap = ap.copy()
    ap[allix] = np.minimum(ap[allix], prof[None, :])
    return ap


def repair_nuclei(sp, ap, f0r, t, plan, fs, drop_db=10.0, floor_db=-40.0, boost_to=-4.0, max_boost=12.0,
                  f0_raw=None):
    """VITS sometimes renders a stretched vowel token (a long schwa, the length mark of /uː/, a vowel
    before a comma) as near-silence part-way through the note.  Per sung nucleus:
      1. collapse repair: frames that fall > drop_db below the nucleus's sustain level, or whose source F0 is
         missing / > 4 semitones off the vowel's own (creaky VITS phonation, mis-analysed envelope), are refilled
         from its good frames, walking back and forth through them (ping-pong) so the timbre keeps moving;
      2. level repair: a whole nucleus far below the line's median vowel level is boosted (<= max_boost dB)
         toward median + boost_to dB, and its aperiodicity capped at the line's typical vowel profile
         (a quiet VITS vowel is breathy; lifted as-is it would come out as pitchless noise).
    Returns (sp, ap, f0r, notes) -- notes lists what was repaired."""
    sp, ap, f0r = sp.copy(), ap.copy(), f0r.copy()
    nb = sp.shape[1]
    fr = np.arange(nb) * fs / 2 / (nb - 1)
    band = (fr >= 90) & (fr <= 5000)
    edb = 10 * np.log10(sp[:, band].sum(axis=1) + 1e-20)
    spans, syls, ph = plan["spans"], plan["syls"], plan["ph"]
    rng_idx = []
    for sy in syls:
        # the held part: stress mark + first vowel (a diphthong's quieter off-glide is left untouched,
        # it carries the word: 'sigh' must not become 'sah'); long vowels (V + length mark) as a whole
        vows = [i for i in sy.nucleus if ph[i] not in STRESS]
        chars = "".join(ph[i] for i in vows)
        last = sy.nucleus[-1] if (len(vows) == 1 or LENGTH in chars or SYLLABIC in chars) else vows[0]
        a, b = spans[sy.nucleus[0]][0], spans[last][1]
        rng_idx.append(np.where((t >= a) & (t < b))[0])
    med = np.median([np.median(edb[ix]) for ix in rng_idx if len(ix)])
    allv = np.concatenate([ix for ix in rng_idx if len(ix)])
    loud = allv[edb[allv] >= med - 6.0]
    ap_ref = np.median(ap[loud], axis=0) if len(loud) else None     # a typical sung vowel's aperiodicity
    notes = []
    for k, ix in enumerate(rng_idx):
        if len(ix) < 6:
            continue
        e = np.convolve(edb[ix], np.ones(3) / 3, mode="same")
        core = ix[2:-8] if len(ix) > 14 else ix[1:-2]           # leave onset / coda transitions alone
        ec = e[2:-8] if len(ix) > 14 else e[1:-2]
        if len(ec) < 3:
            continue
        ref = np.percentile(ec[: max(3, len(ec) // 2)], 90)    # the vowel's sustain level
        if ref < med + floor_db:
            notes.append((k, "silent nucleus (needs a respelling)"))
            continue
        ok_lvl = ec >= ref - drop_db
        if f0_raw is not None:        # creaky / irregular VITS phonation: the analysis F0 is missing or far
            fr0 = f0_raw[core]        # from the vowel's own pitch, so its envelope keeps a wrong harmonic ripple
            v = fr0 > 0
            if v.sum() >= 3:
                medf = np.median(fr0[v])
                ok_f0 = v & (np.abs(np.log2(np.maximum(fr0, 1e-3) / medf)) < 0.34)
                ok_lvl = ok_lvl & ok_f0
        good = core[ok_lvl]
        bad = core[~ok_lvl]
        if len(bad) and len(good) >= 3:
            src = np.concatenate([good, good[::-1]])
            for j, i in enumerate(bad):
                g = src[j % len(src)]
                sp[i], ap[i] = sp[g], ap[g]
                if f0r[g] > 0:
                    f0r[i] = f0r[g]
            notes.append((k, f"refilled {len(bad)} frames"))
        lvl = np.median(10 * np.log10(sp[ix][:, band].sum(axis=1) + 1e-20))
        if lvl < med + boost_to - 1.0:
            gdb = min(max_boost, med + boost_to - lvl)
            ramp = np.ones(len(ix))
            m = min(4, len(ix) // 3)
            if m:
                ramp[:m] = np.linspace(0.3, 1, m)
                ramp[-m:] = np.linspace(1, 0.3, m)
            sp[ix] *= (10 ** (gdb * ramp / 10))[:, None]
            if ap_ref is not None and gdb >= 4.0:   # quiet = breathy: give the lifted vowel a sung voice
                ap[ix] = np.minimum(ap[ix], ap_ref[None, :])
            notes.append((k, f"boost {gdb:.1f} dB"))
    return sp, ap, f0r, notes


def render_vocal(lines_notes, tp, total, take=0, jitter=0.0, cents=0.0, vib_scale=1.0, warp=1.0, log=None):
    """Sing every line; returns (mono 48 kHz track of length `total` s, per-line info)."""
    sr_in = tp.sr
    y48 = np.zeros(int(total * SR) + SR)
    info = []
    rng_j = np.random.default_rng(1000 + take)
    # natural first-onset durations of every line (to end each line just before the next one's consonant)
    plans = []
    for li, (lid, text, notes) in enumerate(lines_notes):
        ns = [Note(**{**nt.__dict__}) for nt in notes]
        if jitter > 0:
            for k, nt in enumerate(ns):
                d = float(np.clip(rng_j.normal(0, jitter), -2 * jitter, 2 * jitter))
                nt.start += d
            for k in range(len(ns) - 1):
                ns[k].end = ns[k + 1].start
        plans.append(ns)
    first_on = []
    for li, (lid, text, notes) in enumerate(lines_notes):
        p = plan_line(tp, text, plans[li], seed=take_seed(li, lid, take), say=SAY.get(lid))
        first_on.append(plans[li][0].start - sum(p["dur"][2 + 2 * i] + p["dur"][3 + 2 * i]
                                                 for i in p["syls"][0].onset) * p["fr"])
    for li, (lid, text, notes) in enumerate(lines_notes):
        ns = plans[li]
        nxt = first_on[li + 1] if li + 1 < len(lines_notes) else None
        if nxt is not None and nxt > ns[-1].end + 0.25:
            nxt = None                                        # a rest follows: keep the written length
        seed = take_seed(li, lid, take)
        p = plan_line(tp, text, ns, next_onset_start=nxt, seed=seed, say=SAY.get(lid), breath=BREATH.get(lid))
        ns[-1].end = float(p["ends"][-1])
        x, _ = tp.run(p["ids"], p["dur"], VOICE["noise"], 1.0, VOICE["noise_w"], seed)
        rng = np.random.default_rng(seed + 99)
        y, w = world_sing(x, sr_in, p, ns, rng, warp=warp, vib_scale=vib_scale, cents=cents)
        y = articulate(y, sr_in, p, VOICE.get("cons_db"))
        # edge fades, upsample to 48 kHz, place
        fi = int(0.004 * sr_in)
        y[:fi] *= np.linspace(0, 1, fi)
        y[-fi:] *= np.linspace(1, 0, fi)
        z = resample_poly(y, 320, 147)
        if VOICE.get("line_lufs") is not None:   # ride the vocal: every sung line at the same loudness (+ LINE_GAIN_DB)
            lv = kweight_lufs(z)
            if lv > -70.0:
                z = z * 10 ** ((VOICE["line_lufs"] + LINE_GAIN_DB.get(lid, 0.0) - lv) / 20)
        a = int(round(p["t0"] * SR))
        if a < 0:
            z, a = z[-a:], 0
        y48[a:a + len(z)] += z[: len(y48) - a]
        info.append(dict(id=lid, text=text, notes=ns, plan=p, world=w, t0=p["t0"], x=x, y=y, sr=sr_in))
        if log is not None:
            log(f"    {lid} take{take}: {len(p['syls'])} syl, utt {p['t0']:.2f}s +{len(x) / sr_in:.2f}s")
    return y48[: int(total * SR)], info


# ================================================================================================
# generic DSP
# ================================================================================================
def biquad_peak(f0, gain_db, q, sr=SR):
    A = 10 ** (gain_db / 40)
    w = 2 * np.pi * f0 / sr
    al = np.sin(w) / (2 * q)
    b = np.array([1 + al * A, -2 * np.cos(w), 1 - al * A])
    a = np.array([1 + al / A, -2 * np.cos(w), 1 - al / A])
    return b / a[0], a / a[0]


def biquad_shelf(f0, gain_db, high=True, sr=SR, s=0.8):
    A = 10 ** (gain_db / 40)
    w = 2 * np.pi * f0 / sr
    al = np.sin(w) / 2 * np.sqrt((A + 1 / A) * (1 / s - 1) + 2)
    c = np.cos(w)
    if high:
        b = [A * ((A + 1) + (A - 1) * c + 2 * np.sqrt(A) * al), -2 * A * ((A - 1) + (A + 1) * c),
             A * ((A + 1) + (A - 1) * c - 2 * np.sqrt(A) * al)]
        a = [(A + 1) - (A - 1) * c + 2 * np.sqrt(A) * al, 2 * ((A - 1) - (A + 1) * c),
             (A + 1) - (A - 1) * c - 2 * np.sqrt(A) * al]
    else:
        b = [A * ((A + 1) - (A - 1) * c + 2 * np.sqrt(A) * al), 2 * A * ((A - 1) - (A + 1) * c),
             A * ((A + 1) - (A - 1) * c - 2 * np.sqrt(A) * al)]
        a = [(A + 1) + (A - 1) * c + 2 * np.sqrt(A) * al, -2 * ((A - 1) + (A + 1) * c),
             (A + 1) + (A - 1) * c - 2 * np.sqrt(A) * al]
    b, a = np.array(b), np.array(a)
    return b / a[0], a / a[0]


def compress(x, sr, thresh_db=-20.0, ratio=2.6, attack=0.006, release=0.12, knee=6.0):
    rms = np.sqrt(lfilter([1 - math.exp(-1 / (0.008 * sr))], [1, -math.exp(-1 / (0.008 * sr))], x * x) + 1e-12)
    lvl = 20 * np.log10(rms + 1e-9)
    over = lvl - thresh_db
    gr = np.where(over <= -knee / 2, 0.0,
                  np.where(over >= knee / 2, over * (1 - 1 / ratio),
                           (1 - 1 / ratio) * (over + knee / 2) ** 2 / (2 * knee)))
    g = 10 ** (-gr / 20)
    # smooth gain: fast attack, slow release
    ga, grl = math.exp(-1 / (attack * sr)), math.exp(-1 / (release * sr))
    inv = 1 - g
    sm = np.maximum(lfilter([1 - ga], [1, -ga], inv), lfilter([1 - grl], [1, -grl], inv))
    return x * (1 - np.clip(sm, 0, 1))


def deess(x, sr, lo=4800.0, hi=10500.0, thresh_db=-6.0, max_cut_db=8.0):
    """Split-band de-esser: when the sibilant band dominates, pull that band down."""
    sos = butter(2, [lo / (sr / 2), min(hi / (sr / 2), 0.99)], btype="band", output="sos")
    band = sosfiltfilt(sos, x)
    a = math.exp(-1 / (0.005 * sr))
    eb = np.sqrt(lfilter([1 - a], [1, -a], band * band) + 1e-12)
    ef = np.sqrt(lfilter([1 - a], [1, -a], x * x) + 1e-12)
    rel = 20 * np.log10(eb / ef)
    cut = np.clip((rel - thresh_db) * 1.5, 0, max_cut_db)
    g = 10 ** (-cut / 20)
    return x - band * (1 - g)


def kweight_lufs(x, sr=SR):
    """BS.1770-4 integrated loudness (mono or stereo (n,2)), 48 kHz coefficients."""
    x = np.asarray(x, np.float64)
    if x.ndim == 1:
        x = x[:, None]
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    y = lfilter(b2, a2, lfilter(b1, a1, x, axis=0), axis=0)
    blk, hop = int(0.4 * sr), int(0.1 * sr)
    if len(y) < blk:
        return -70.0
    nfr = 1 + (len(y) - blk) // hop
    cs = np.concatenate([np.zeros((1, y.shape[1])), np.cumsum(y * y, axis=0)])
    z = np.array([(cs[i * hop + blk] - cs[i * hop]) / blk for i in range(nfr)]).sum(axis=1)
    lj = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[lj > -70]
    if len(z1) == 0:
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(z1)) - 10
    z2 = z[lj > max(rel, -70)]
    return float(-0.691 + 10 * np.log10(np.mean(z2) + 1e-20))


def true_peak_db(x):
    """4x oversampled peak (dBFS)."""
    x = np.asarray(x, np.float64)
    if x.ndim == 1:
        x = x[:, None]
    pk = 0.0
    for c in range(x.shape[1]):
        pk = max(pk, np.abs(resample_poly(x[:, c], 4, 1)).max())
    return 20 * np.log10(pk + 1e-12)


def limiter(x, sr, ceiling_db=-1.3, lookahead=0.004, release=0.08):
    """Look-ahead peak limiter on a stereo (n,2) or mono signal (gain computed on the 4x-oversampled max)."""
    st = x if x.ndim == 2 else x[:, None]
    ceil = 10 ** (ceiling_db / 20)
    pk = np.max(np.abs(st), axis=1)
    # oversampled peak estimate
    os4 = np.max(np.abs(np.stack([resample_poly(st[:, c], 4, 1) for c in range(st.shape[1])], 1)), axis=1)
    pk = np.maximum(pk, os4.reshape(-1, 4).max(axis=1)[: len(pk)] if len(os4) >= 4 * len(pk) else pk)
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-9))
    from scipy.ndimage import minimum_filter1d
    la = int(lookahead * sr)
    g = minimum_filter1d(need, size=2 * la + 1)
    gr = math.exp(-1 / (release * sr))
    gs = 1 - np.maximum(lfilter([1 - gr], [1, -gr], 1 - g), 1 - g)
    out = st * gs[:, None]
    return out if x.ndim == 2 else out[:, 0]


def duck_gain(voice, sr, depth_db=3.0, attack=0.03, release=0.25):
    """Smooth gain curve (1 .. 10^(-depth/20)) that follows the voice's activity (sidechain ducking)."""
    a = math.exp(-1 / (0.02 * sr))
    env = np.sqrt(lfilter([1 - a], [1, -a], voice * voice) + 1e-12)
    edb = 20 * np.log10(env)
    act = np.clip((edb - (edb.max() - 40.0)) / 12.0, 0, 1)        # 0 = silent .. 1 = singing
    ga, gr = math.exp(-1 / (attack * sr)), math.exp(-1 / (release * sr))
    sm = np.maximum(lfilter([1 - ga], [1, -ga], act), lfilter([1 - gr], [1, -gr], act))
    return 10 ** (-depth_db * np.clip(sm, 0, 1) / 20)


def pan(x, p):
    """Equal-power pan of mono x to stereo, p in -1..1."""
    th = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(th), x * np.sin(th)], 1)


def hall_ir(rt60=1.4, predelay=0.02, seed=11, sr=SR):
    """Synthetic stereo hall: band-split exponentially decaying noise (highs die faster), soft build-up,
    a few early reflections, 20 ms pre-delay. Unit energy per channel."""
    rng = np.random.default_rng(seed)
    n = int((rt60 * 1.25 + predelay) * sr)
    t = np.arange(n) / sr
    N = 1 << int(np.ceil(np.log2(n)))
    fr = np.fft.rfftfreq(N, 1 / sr)
    chans = []
    for ch in range(2):
        X = np.fft.rfft(rng.standard_normal(n), N)
        y = np.zeros(n)
        for lo, hi, k in [(0, 200, 1.12), (200, 800, 1.0), (800, 2500, 0.85), (2500, 6000, 0.62),
                          (6000, 24001, 0.42)]:
            m = ((fr >= lo) & (fr < hi)).astype(float)
            y += np.fft.irfft(X * m, N)[:n] * np.exp(-6.91 * t / (rt60 * k))
        y *= np.clip(t / 0.035, 0, 1) ** 1.5
        pd = int(predelay * sr)
        y = np.concatenate([np.zeros(pd), y[: n - pd]])
        for d, g in [(0.009, 0.45), (0.014, 0.38), (0.019, 0.33), (0.027, 0.27), (0.036, 0.22), (0.048, 0.16)]:
            k = int((d + 0.002 * rng.uniform(-1, 1)) * sr)
            y[k] += g * (1 if rng.uniform() > 0.5 else -1) * 0.25
        chans.append(y / np.sqrt(np.sum(y * y)))
    return np.stack(chans, 1)


def reverb(x, ir):
    if x.ndim == 1:
        return np.stack([fftconvolve(x, ir[:, 0]), fftconvolve(x, ir[:, 1])], 1)
    return np.stack([fftconvolve(x[:, 0], ir[:, 0]), fftconvolve(x[:, 1], ir[:, 1])], 1)


def fit(x, n):
    """Trim/zero-pad (along axis 0) to n samples."""
    if len(x) >= n:
        return x[:n]
    pad = [(0, n - len(x))] + [(0, 0)] * (x.ndim - 1)
    return np.pad(x, pad)


# ================================================================================================
# instruments
# ================================================================================================
def midi_hz(m):
    return 440.0 * 2.0 ** ((np.asarray(m, float) - 69.0) / 12.0)


def ks_string(f0, dur, t60=2.5, damp=0.18, pick=0.17, vel=0.8, soft=0.5, rng=None, bend=None, sr=SR):
    """Extended Karplus-Strong gut string: loop = 3-tap lowpass (damp) x linear fractional delay (exact
    tuning), loop gain from t60; excitation = one period of smoothed noise (fingertip), pick-position comb."""
    rng = rng or np.random.default_rng(0)
    n = int(round(dur * sr))
    period = sr / f0
    a = float(np.clip(damp, 0.0, 0.25))
    N = int(np.floor(period - 1.0))
    frac = period - 1.0 - N
    taps = np.convolve([a, 1 - 2 * a, a], [1 - frac, frac])
    g = 10.0 ** (-3.0 / (t60 * f0))
    L = N + 1
    e = rng.uniform(-1, 1, L)
    c = float(np.clip(0.35 + 0.6 * soft - 0.35 * vel, 0.05, 0.95))
    e = lfilter([1 - c], [1, -c], e)
    e = lfilter([1 - c], [1, -c], e[::-1])[::-1]
    P = max(1, int(round(pick * N)))
    e = e - np.concatenate([np.zeros(P), e[:-P]])
    e -= e.mean()
    e *= vel / (np.abs(e).max() + 1e-9)
    x = np.zeros(n)
    x[:min(L, n)] = e[:min(L, n)]
    if N < 260:
        den = np.zeros(N + len(taps))
        den[0] = 1.0
        den[N:N + len(taps)] -= g * taps
        out = lfilter([1.0], den, x)
    else:
        off = N + len(taps) + 1
        y = np.zeros(off + n)
        gt = g * taps
        k = 0
        while k < n:
            m = min(N, n - k)
            i0 = off + k
            acc = x[k:k + m].copy()
            for j, tj in enumerate(gt):
                acc += tj * y[i0 - N - j: i0 - N - j + m]
            y[i0:i0 + m] = acc
            k += m
        out = y[off:]
    if bend is not None:
        tt = np.arange(n) / sr
        pos = np.cumsum(2.0 ** (bend(tt) / 1200.0))
        out = np.interp(pos - pos[0], np.arange(n), out, right=0.0)
    return out


def lute_body_ir(seed=3, sr=SR):
    rng = np.random.default_rng(seed)
    n = int(0.16 * sr)
    t = np.arange(n) / sr
    modes = [(104, 0.045, 1.0), (198, 0.034, 0.85), (287, 0.028, 0.7), (410, 0.022, 0.45), (565, 0.018, 0.35),
             (770, 0.014, 0.25), (1150, 0.010, 0.22), (1630, 0.008, 0.17), (2380, 0.006, 0.11), (3150, 0.004, 0.07)]
    ir = np.zeros(n)
    for f, tau, amp in modes:
        ir += amp * np.exp(-t / tau) * np.sin(2 * np.pi * f * (1 + 0.01 * rng.standard_normal()) * t
                                               + rng.uniform(0, np.pi))
    ir /= np.sqrt(np.sum(ir ** 2))
    d = np.zeros(n)
    d[0] = 1.0
    return 0.6 * d + 1.2 * ir


@dataclass
class Pluck:
    t: float
    midi: int
    vel: float
    end: float = None      # damped at (s); None = ring
    bend: object = None    # optional cents(t) for the tuning-peg gag
    harmonic: bool = False
    ring: float = 1.0      # decay-time (t60) multiplier


def render_lute(plucks, total, seed=21):
    """Render a list of Pluck -> mono lute (with double courses + octave strings), body resonance applied."""
    rng = np.random.default_rng(seed)
    n = int(total * SR)
    y = np.zeros(n + SR)
    for p in plucks:
        f = float(midi_hz(p.midi))
        ring = (p.end - p.t) if p.end is not None else 4.0
        ring = float(np.clip(ring, 0.05, 4.0))
        dur = ring + 0.06
        a = int(round(p.t * SR))
        if a >= n:
            continue
        if p.harmonic:     # natural harmonic: near-sine, bell-like
            tt = np.arange(int(min(dur, 2.0) * SR)) / SR
            s = p.vel * 0.55 * (np.sin(2 * np.pi * f * tt) + 0.08 * np.sin(4 * np.pi * f * tt)) * \
                np.exp(-tt / 0.7) * np.clip(tt / 0.002, 0, 1) * np.clip((tt[-1] - tt) / 0.08, 0, 1)  # no cut-off tail
        else:
            low = p.midi < 52
            t60 = (3.2 if low else (2.4 if p.midi < 64 else 1.6)) * p.ring
            damp = 0.22 if low else (0.18 if p.midi < 64 else 0.155)     # gut strings: warm, not zingy
            s = ks_string(f, dur, t60=t60, damp=damp, pick=0.19 if low else 0.15, vel=p.vel, soft=0.66,
                          rng=rng, bend=p.bend)
            # second string of the course: unison (or octave on the basses), a hair later and detuned
            f2 = f * (2.0 if low else 1.0) * 2 ** (rng.uniform(1.5, 3.0) * rng.choice([-1, 1]) / 1200)
            s2 = ks_string(f2, dur, t60=t60 * (0.8 if low else 1.0), damp=damp * (0.8 if low else 1.0),
                           pick=0.14, vel=p.vel * (0.45 if low else 0.8), soft=0.5, rng=rng, bend=p.bend)
            d2 = int(rng.uniform(0.0008, 0.0022) * SR)
            s = s + np.concatenate([np.zeros(d2), s2[: len(s2) - d2]])
            # damping at the end (left hand lifts / string re-plucked)
            fo = int(0.05 * SR)
            k = int(ring * SR)
            if k < len(s):
                s[k:k + fo] *= np.linspace(1, 0, len(s[k:k + fo]))
                s[k + fo:] = 0
        y[a:a + len(s)] += s[: len(y) - a]
    y = fftconvolve(y, lute_body_ir())[: n + SR]
    sos = butter(2, [70 / (SR / 2), 7500 / (SR / 2)], btype="band", output="sos")
    return sosfilt(sos, y)[:n]


def recorder_line(phrases, total, seed=31):
    """phrases: list of phrases, each a list of (t, dur, midi, vel); notes inside a phrase are slurred."""
    rng = np.random.default_rng(seed)
    n = int(total * SR)
    out = np.zeros(n + SR)
    for notes in phrases:
        # 40 ms of pre-roll: the zero-phase (forward-backward) envelope smoothing below needs room before the first
        # note, else the phrase starts at ~half amplitude on its first sample (a click at every recorder entry)
        t0 = notes[0][0] - 0.04
        T = notes[-1][0] + notes[-1][1] - t0 + 0.15
        L = int(T * SR)
        t = np.arange(L) / SR
        m = np.zeros(L)
        envt = np.zeros(L)
        for i, (ts, d, mm, v) in enumerate(notes):
            a, b = int((ts - t0) * SR), int((ts - t0 + d) * SR)
            m[a:] = mm
            envt[a:b] = v
        gl = int(0.03 * SR)
        ker = np.hanning(gl)
        ker /= ker.sum()
        m = np.convolve(np.pad(m, (gl // 2, gl - gl // 2 - 1), mode="edge"), ker, mode="valid")
        vib = np.zeros(L)
        for ts, d, mm, v in notes:
            a, b = int((ts - t0) * SR), min(L, int((ts - t0 + d) * SR))
            tt = np.arange(b - a) / SR
            vib[a:b] = 11.0 * np.clip((tt - 0.25) / 0.3, 0, 1) * np.sin(2 * np.pi * 5.1 * tt)
        f = midi_hz(m) * 2 ** (vib / 1200)
        for ts, d, mm, v in notes:
            a = int((ts - t0) * SR)
            k = min(int(0.05 * SR), L - a)
            f[a:a + k] *= 2 ** (-16 * np.exp(-np.arange(k) / (0.014 * SR)) / 1200)
        # breath envelope: attack ~40 ms, release ~80 ms, smooth
        att = math.exp(-1 / (0.018 * SR))
        env = lfilter([1 - att], [1, -att], envt)
        env = lfilter([1 - att], [1, -att], env[::-1])[::-1]
        ph = 2 * np.pi * np.cumsum(f) / SR
        y = np.zeros(L)
        for k, h in enumerate([1.0, 0.20, 0.09, 0.04, 0.022, 0.01]):
            y += h * np.sin((k + 1) * ph + rng.uniform(0, 6.28)) * ((k + 1) * f < SR / 2 - 1000)
        y *= env * (1 + 0.035 * vib / 11.0)
        sos = butter(2, [1000 / (SR / 2), 7000 / (SR / 2)], btype="band", output="sos")
        breath = sosfilt(sos, rng.standard_normal(L)) * env * 0.03
        for ts, d, mm, v in notes:     # chiff (tongued attack)
            a = int((ts - t0) * SR)
            k = min(int(0.03 * SR), L - a)
            fc = float(midi_hz(mm))
            sos2 = butter(2, [min(0.9, 2.2 * fc / (SR / 2)), min(0.95, 5.5 * fc / (SR / 2))], btype="band",
                          output="sos")
            rise = 0.5 - 0.5 * np.cos(np.pi * np.clip(np.arange(k) / (0.002 * SR), 0, 1))     # 2 ms tongue attack
            breath[a:a + k] += sosfilt(sos2, rng.standard_normal(k)) * np.exp(-np.arange(k) / (0.007 * SR)) * rise \
                * 0.2 * v
        a0 = int(t0 * SR)
        out[a0:a0 + L] += (y + breath)[: len(out) - a0]
    return out[:n]


def drum_hit(kind, vel, rng):
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    if kind == "doum":
        y = np.zeros(n)
        for r, dcy, am in zip([1.0, 1.59, 2.14, 2.30, 2.65, 2.92], [0.28, 0.15, 0.10, 0.08, 0.07, 0.06],
                              [1.0, 0.45, 0.32, 0.22, 0.16, 0.1]):
            fr = 66.0 * r * (1 + 0.09 * np.exp(-t / 0.03))
            y += am * np.exp(-t / dcy) * np.sin(2 * np.pi * np.cumsum(fr) / SR)
        y += 0.45 * sosfilt(butter(2, 900 / (SR / 2), output="sos"), rng.standard_normal(n) * np.exp(-t / 0.004))
    elif kind == "tek":
        y = np.zeros(n)
        for r, dcy, am in zip([1.0, 1.59, 2.14, 2.65, 3.5], [0.05, 0.04, 0.03, 0.025, 0.02], [1, .6, .5, .3, .2]):
            y += am * np.exp(-t / dcy) * np.sin(2 * np.pi * 235.0 * r * t + rng.uniform(0, 6))
        nz = sosfilt(butter(2, [1200 / (SR / 2), 5000 / (SR / 2)], btype="band", output="sos"),
                     rng.standard_normal(n) * np.exp(-t / 0.012))
        y = 0.5 * y + 1.2 * nz
    else:  # jingle (tambourine)
        y = np.zeros(n)
        for j in range(7):
            a = int(rng.uniform(0, 0.012) * SR)
            tt = t[: n - a]
            part = np.zeros(n - a)
            for _ in range(5):
                part += rng.uniform(0.3, 1.0) * np.exp(-tt / (0.11 * rng.uniform(0.5, 1.2))) * \
                    np.sin(2 * np.pi * rng.uniform(4200, 11500) * tt + rng.uniform(0, 6))
            y[a:] += part
        y += 0.8 * sosfilt(butter(2, 6000 / (SR / 2), btype="high", output="sos"),
                           rng.standard_normal(n) * np.exp(-t / 0.02))
    # the buffer is 0.5 s: fade its last 120 ms (a hand damping the skin) -- cutting the doum's low mode off while it
    # still rings at ~-15 dB was a click 0.5 s after every downbeat
    nf = int(0.12 * SR)
    y[-nf:] *= 0.5 + 0.5 * np.cos(np.linspace(0.0, np.pi, nf))
    return vel * y / (np.abs(y).max() + 1e-9)


def render_hits(hits, total, seed=41):
    """hits: [(t, kind, vel)] -> (drum mono, tambourine mono)"""
    rng = np.random.default_rng(seed)
    n = int(total * SR)
    dr, tb = np.zeros(n + SR), np.zeros(n + SR)
    for t, kind, vel in hits:
        h = drum_hit(kind, vel, rng)
        a = int(round(t * SR))
        tgt = tb if kind == "jingle" else dr
        tgt[a:a + len(h)] += h[: len(tgt) - a]
    return dr[:n], tb[:n]


# ================================================================================================
# arrangement
# ================================================================================================
ARR = dict(v1_vel=0.55,            # lute velocity, verse 1 (fingerpicked arpeggios)
           v2_vel=0.55,            # lute velocity, verse 2 (strummed: should sit a little fuller than verse 1)
           interlude_style="arp_soft",  # lute under the recorder's motif in the interlude (bar 9): it steps back
           interlude_vel=0.45,
           rec_interlude_vel=1.6,   # recorder: the motif at the page turn (its one featured statement, ~lute level)
           rec_double_vel=0.76,     # recorder: soft 8va doubling of the hook in verse 2 (~9 dB under the lute)
           rec_final_vel=0.65,      # recorder: G4 -> F#4 under the last chord
           v2_gain_db=1.5,          # lute fader in verse 2 (bars 10-17): the strummed verse sits fuller
           final_ring=2.0)          # decay-time multiplier for the final chord (lets it ring out under the outro)

LUTE_UPPER = {"D": (57, 62, 66), "G": (59, 62, 67), "A": (57, 61, 64), "A7": (55, 61, 64), "Bm": (59, 62, 66),
              "Em": (55, 59, 64), "C": (55, 60, 64), "F#m": (57, 61, 66)}
LUTE_BASS = {"D": (38, 45), "G": (43, 50), "A": (45, 52), "A7": (45, 52), "Bm": (47, 54), "Em": (40, 47),
             "C": (48, 43), "F#m": (42, 49)}


def chord_at(chords, bar, half):
    return chords.get(bar, ("D", "D"))[half]


def halves_of(grid, bar):
    """Dotted-quarter beats present in a bar: (0, 1) in 6/8, (0,) in a 3/8 bar."""
    return (0, 1) if grid.bar_len[bar] >= 6 else (0,)


class Strokes:
    """Collects lute plucks + the right-hand stroke log (for the bard's strumming animation)."""

    def __init__(self):
        self.plucks, self.log = [], []
        self.auto = []          # lute fader moves [(t_from, t_to, dB)]

    def pluck(self, t, midi, vel, kind="pluck"):
        self.plucks.append(Pluck(t, midi, vel))
        self.log.append(dict(t=round(t, 4), kind=kind, n=1, vel=round(vel, 2)))

    def strum(self, t, notes, vel, up=False, spread=0.018, kind=None, rng=None, ring=1.0):
        order = sorted(notes, reverse=up)
        for i, m in enumerate(order):
            jit = (rng.uniform(-0.003, 0.003) if rng is not None else 0.0)
            self.plucks.append(Pluck(t + i * spread + jit, m, vel * (0.92 ** i if not up else 0.8 * 0.95 ** i),
                                     ring=ring))
        self.log.append(dict(t=round(t, 4), kind=kind or ("up" if up else "down"), n=len(notes),
                             vel=round(vel, 2)))

    def damp_all(self, total):
        """End each pluck when the same pitch is re-struck or when a later chord no longer contains it
        (the left hand moves): computed from the onset list."""
        ps = sorted(self.plucks, key=lambda p: p.t)
        for i, p in enumerate(ps):
            if p.end is not None:
                continue
            nxt = [q.t for q in ps[i + 1:] if q.midi == p.midi and q.t > p.t + 0.01]
            p.end = min(nxt[0] if nxt else total, p.t + 3.6)
        self.plucks = ps


def lute_bar(S, grid, chords, bar, style, vel=0.55, rng=None, halves=(0, 1)):
    """One bar of lute accompaniment in 6/8."""
    for h in halves:
        ch = chord_at(chords, bar, h)
        up = LUTE_UPPER[ch]
        b_root, b_fifth = LUTE_BASS[ch]
        p0 = 3 * h
        t = [grid.t(bar, p0 + i) for i in range(3)]
        if style == "arp":           # bass - middle - top  (fingerpicked)
            S.pluck(t[0], b_root if h == 0 or chord_at(chords, bar, 0) != ch else b_fifth, vel * 1.05, "bass")
            S.pluck(t[1], up[1], vel * 0.72)
            S.pluck(t[2], up[2] if h == 0 else up[0], vel * 0.66)
        elif style == "arp_soft":
            S.pluck(t[0], b_root if h == 0 or chord_at(chords, bar, 0) != ch else b_fifth, vel * 0.9, "bass")
            S.pluck(t[1], up[0], vel * 0.55)
            S.pluck(t[2], up[1] if h == 0 else up[2], vel * 0.5)
        elif style == "strum":       # bass + brushed chord on the beat, light up-stroke on the third eighth
            S.pluck(t[0], b_root if h == 0 or chord_at(chords, bar, 0) != ch else b_fifth, vel * 1.05, "bass")
            S.strum(t[0] + 0.012, list(up), vel * 0.62, spread=0.014, rng=rng)
            S.strum(t[2], list(up[1:]), vel * 0.42, up=True, spread=0.011, rng=rng)
        elif style == "roll":        # one slow rolled chord per beat
            S.strum(t[0], [b_root] + list(up), vel, spread=0.035, kind="roll", rng=rng)


def recorder_motif(grid, bar, transpose=12, vel=0.8, pos=0.0):
    ev = []
    p = pos
    for m, r in zip(M.MOTIF, M.MOTIF_RHYTHM):
        ev.append((grid.t(bar, p), grid.dur(bar, p, r) * (0.92 if r == 1 else 0.97), m + transpose, vel))
        p += r
    return ev


def arrange_prologue(notes_by_line):
    g = PROLOGUE_GRID
    rng = np.random.default_rng(5)
    S = Strokes()
    marks = {}
    # --- intro: the bard tunes up ------------------------------------------------------------------
    S.pluck(0.10, 57, 0.5, "tune")                               # A string, flat (see bend below)
    S.plucks[-1].bend = lambda tt: -38.0 + 0 * tt
    S.pluck(0.52, 57, 0.55, "tune")                              # ... plucked again while the peg turns
    S.plucks[-1].bend = lambda tt: -38.0 + 38.0 * np.clip((tt - 0.10) / 0.40, 0, 1) ** 0.8
    S.strum(1.06, [50, 57], 0.55, spread=0.012, kind="tune")     # open fifth D3+A3: in tune now
    S.plucks.append(Pluck(1.48, 74, 0.45, harmonic=True))        # harmonic "ting" D5
    S.log.append(dict(t=1.48, kind="harmonic", n=1, vel=0.45))
    S.plucks.append(Pluck(1.68, 69, 0.4, harmonic=True))         # harmonic A4
    S.log.append(dict(t=1.68, kind="harmonic", n=1, vel=0.4))
    # playful run up the D scale, accelerating, into a rolled D chord (the book opens on it)
    run = [50, 52, 54, 55, 57, 59, 61, 62, 64, 66]
    tr = 1.95
    for i, m in enumerate(run):
        S.pluck(tr, m, 0.42 + 0.03 * i, "run")
        tr += 0.064 - 0.0033 * i
    S.strum(2.56, [38, 45, 50, 57, 62, 66], 0.85, spread=0.03, kind="flourish", rng=rng)
    marks["flourish"] = 2.56
    marks["vamp"] = g.t(0)
    # --- in tempo ---------------------------------------------------------------------------------
    styles = {0: "arp_soft"}
    styles.update({b: "arp" for b in range(1, 9)})
    styles[9] = ARR["interlude_style"]
    styles.update({b: "strum" for b in range(10, 18)})
    styles.update({18: "roll", 19: "arp_soft", 20: "arp_soft", 21: "roll"})
    for bar in range(0, 22):
        st = styles[bar]
        vel = {0: 0.5, 9: ARR["interlude_vel"], 18: 0.6, 19: 0.48, 20: 0.5, 21: 0.5}.get(
            bar, ARR["v2_vel"] if 10 <= bar <= 17 else ARR["v1_vel"])
        lute_bar(S, g, PROLOGUE_CHORDS, bar, st, vel=vel, rng=rng, halves=halves_of(g, bar))
    # bar 22: "way back to" (G) ... A7 under "bread" ... final D when the melisma resolves
    S.strum(g.t(22, 0), [43] + list(LUTE_UPPER["G"]), 0.5, spread=0.04, kind="roll", rng=rng)
    bread = notes_by_line["s0_l10"][-1]
    S.strum(bread.start, [45] + list(LUTE_UPPER["A7"]), 0.5, spread=0.045, kind="roll", rng=rng)
    t_res = bread.start + bread.split * (bread.end - bread.start)
    S.strum(t_res, [38, 45, 50, 57, 62, 66], 0.72, spread=0.055, kind="final", rng=rng, ring=ARR["final_ring"])
    marks["final_chord"] = t_res
    total = t_res + 3.4                    # the voice holds D3 ~1.4 s, then ~2 s of lute ring-out
    if ARR.get("v2_gain_db"):              # verse 2 strums a little fuller (fader up through bars 10-17)
        S.auto.append((g.t(10, 0) - 0.15, g.t(18, 0), ARR["v2_gain_db"]))
    S.damp_all(total)
    # chord changes damp the strings the next chord does not contain
    changes = []
    for bar in sorted(PROLOGUE_CHORDS):
        for h in halves_of(g, bar):
            changes.append((g.t(bar, 3 * h), chord_at(PROLOGUE_CHORDS, bar, h)))
    _damp_on_changes(S, changes, [(bread.start, "A7"), (t_res, "D")])
    # --- recorder (from the interlude): the motif as a counter-melody ------------------------------
    interlude = recorder_motif(g, 9, vel=ARR["rec_interlude_vel"])      # interlude (page turn) ...
    t_pick = notes_by_line["s0_l5"][0].start - 0.12                      # ... its last note ends before
    interlude[-1] = (interlude[-1][0], t_pick - interlude[-1][0], interlude[-1][2], interlude[-1][3])  # 'Now a'
    dv = ARR["rec_double_vel"]
    phrases = [interlude,
               recorder_motif(g, 11, vel=dv),                            # doubles "SCARF and a SIGH" 8va, softly
               recorder_motif(g, 16, vel=dv * 0.92)[:3]]                 # "WHAT he was MISS-" ...
    fv = ARR["rec_final_vel"]
    phrases.append([(bread.start, t_res - bread.start, 67, fv), (t_res, 2.3, 66, fv * 1.09)])   # G4 -> F#4 (7 -> 3)
    rec = recorder_line(phrases, total)
    # --- frame drum + tambourine (verse 2, lightly) ------------------------------------------------
    hits = []
    for bar in range(10, 18):
        hits += [(g.t(bar, 0), "doum", 0.55), (g.t(bar, 3), "tek", 0.22), (g.t(bar, 5), "tek", 0.08),
                 (g.t(bar, 3), "jingle", 0.22), (g.t(bar, 5), "jingle", 0.08)]
    hits += [(g.t(18, 0), "doum", 0.5), (g.t(18, 0) + 0.02, "jingle", 0.12)]
    for bar in (19, 20):
        hits += [(g.t(bar, 0), "doum", 0.32), (g.t(bar, 3), "jingle", 0.1)]
    hits += [(t_res, "jingle", 0.12)]
    return S, rec, hits, total, marks


def _damp_on_changes(S, changes, extra=()):
    ch = sorted(list(changes) + list(extra))
    times = np.array([c[0] for c in ch])
    for p in S.plucks:
        if p.harmonic or p.bend is not None:
            continue
        k = np.searchsorted(times, p.t + 0.05)
        while k < len(ch):
            tc, name = ch[k]
            pcs = {x % 12 for x in M.CHORDS[name]}
            if p.midi % 12 not in pcs:
                p.end = min(p.end if p.end is not None else 1e9, tc + 0.03)
                break
            k += 1


def arrange_reprise(notes_by_line):
    g = REPRISE_GRID
    rng = np.random.default_rng(6)
    S = Strokes()
    marks = {}
    S.strum(g.t(0, 1), [38, 45, 50, 57, 62, 66], 0.5, spread=0.06, kind="roll", rng=rng)
    S.pluck(g.t(0, 3), 45, 0.32, "bass")
    S.pluck(g.t(0, 4), 62, 0.25)
    S.pluck(g.t(0, 5), 66, 0.22)
    for bar in range(1, 4):
        lute_bar(S, g, REPRISE_CHORDS, bar, "arp_soft", vel=0.42, rng=rng)
    S.strum(g.t(4, 0), [43] + list(LUTE_UPPER["G"]), 0.42, spread=0.045, kind="roll", rng=rng)
    you = notes_by_line["s9_l2"][-1]
    S.strum(you.start, [45] + list(LUTE_UPPER["A7"]), 0.42, spread=0.05, kind="roll", rng=rng)
    t_res = you.start + you.split * (you.end - you.start)
    S.strum(t_res, [38, 45, 50, 57, 62, 66], 0.55, spread=0.065, kind="final", rng=rng)
    marks["final_chord"] = t_res
    total = t_res + 2.8
    S.damp_all(total)
    changes = [(g.t(b, 3 * h), chord_at(REPRISE_CHORDS, b, h)) for b in sorted(REPRISE_CHORDS) for h in (0, 1)]
    _damp_on_changes(S, changes, [(you.start, "A7"), (t_res, "D")])
    return S, None, [], total, marks


# ================================================================================================
# vocal processing, mix, timing json
# ================================================================================================
def process_vocal(lead, double, double_db=-10.0):
    v = lead + 10 ** (double_db / 20) * double
    v = sosfilt(butter(2, 75 / (SR / 2), btype="high", output="sos"), v)
    b, a = biquad_peak(330, -1.5, 1.0)
    v = lfilter(b, a, v)
    b, a = biquad_peak(3100, 2.5, 0.9)
    v = lfilter(b, a, v)
    b, a = biquad_shelf(140, 1.0, high=False)
    v = lfilter(b, a, v)
    v = deess(v, SR)
    # into the compressor at a fixed loudness (was: the whole track's peak -> 0.5, so swapping ONE line's take moved
    # every line's compression -- and flipped other lines' intelligibility)
    lv = kweight_lufs(v)
    if lv > -70.0:
        v = v * 10 ** ((MIX.get("vocal_comp_in_lufs", -28.0) - lv) / 20)
    else:
        v = v / (np.abs(v).max() + 1e-9) * 0.5
    v = compress(v, SR, thresh_db=-22.0, ratio=2.6)
    return v


def speech_env(y, start, end, sr=SR, fps=FPS):
    """24 fps mouth envelope of the dry vocal between start..end (same recipe as tts.py)."""
    seg = y[int(round(start * sr)): int(round(end * sr))]
    n = int(round((end - start) * fps))
    half = int(round(sr / fps))
    win = np.hanning(2 * half + 1)
    yp = np.pad(seg * seg, (half, half + 1 + max(0, int(n * sr / fps) - len(seg))))
    cen = np.round(np.arange(n) * sr / fps).astype(int)
    ms = np.array([np.dot(yp[c: c + 2 * half + 1], win) / win.sum() for c in cen])
    rms = np.sqrt(ms + 1e-20)
    act = rms[rms > rms.max() * 1e-3]
    ref = np.percentile(act, 95) if len(act) else rms.max()
    rel = 20 * np.log10(rms / (ref + 1e-12) + 1e-12)
    level = np.clip(rms / (ref + 1e-12), 0, 1) ** 0.6
    knee = np.clip((rel + 30.0) / 8.0, 0, 1)
    knee = knee * knee * (3 - 2 * knee)
    env = np.clip(level * knee, 0, 1)
    env[rel < -30.0] = 0.0
    return [round(float(v), 3) for v in env]


def line_timing(info, vocal_dry):
    """Per line: voice onset/offset, words, syllables (+ note), 24 fps envelope."""
    out = []
    for li in info:
        p, ns = li["plan"], li["notes"]
        ph, syls, spans, t0 = p["ph"], p["syls"], p["spans"], p["t0"]
        syl_rows = []
        for k, (s, nt) in enumerate(zip(syls, ns)):
            idx = s.onset + s.nucleus + s.coda
            a = t0 + min(spans[i][0] for i in idx)
            b = t0 + max(spans[i][1] for i in idx)
            syl_rows.append(dict(s=nt.syl.rstrip("-").strip(",.:;—"), start=round(a, 3), end=round(b, 3),
                                 note=round(nt.start, 3), note_end=round(nt.end, 3),
                                 midi=nt.pitches if len(nt.pitches) > 1 else nt.pitches[0],
                                 pitch=">".join(M.note_name(x) for x in nt.pitches), word=nt.word))
        wl = words_of(li["text"])
        words = []
        for w_i, w in enumerate(wl):
            rows = [r for r in syl_rows if r["word"] == w_i]
            words.append(dict(w=w, start=rows[0]["start"], end=rows[-1]["end"], note=rows[0]["note"]))
        start = syl_rows[0]["start"]
        # the end: last voiced sound of the line (the final syllable's sounding end)
        end = max(syl_rows[-1]["end"], ns[-1].end)
        end = min(end, ns[-1].end + 0.08)
        start = max(0.0, start - 0.02)
        out.append(dict(id=li["id"], text=li["text"], start=round(start, 3), end=round(end, 3),
                        sung=True, words=words, syllables=syl_rows,
                        env=speech_env(vocal_dry, start, end)))
    return out


def beat_grid(grid, bar_from, bar_to, extra_downbeats=()):
    beats, downs = [], []
    for b in range(bar_from, bar_to + 1):
        downs.append(round(grid.t(b, 0), 3))
        beats += [round(grid.t(b, 3 * h), 3) for h in halves_of(grid, b)]
    for t in extra_downbeats:
        downs.append(round(t, 3))
        beats.append(round(t, 3))
    return sorted({b for b in beats if b >= 0}), sorted({d for d in downs if d >= 0})


def synth_vocal(lines_notes, total, log=None):
    """The sung lead (take 0) and its double (take 1: runner-up seed, +-10 ms, +5 cents, 0.9x vibrato)."""
    tp = TimedPiper(VOICE["model"], VOICE["speaker_id"])
    lead, info = render_vocal(lines_notes, tp, total, take=0, log=log)
    double, _ = render_vocal(lines_notes, tp, total, take=1, jitter=0.010, cents=5.0, vib_scale=0.9)
    return lead, double, info


def fader(n, moves, ramp=0.3, sr=SR):
    """Fader automation: [(t_from, t_to, dB)] segments with smooth ramps -> linear gain curve of n samples."""
    g = np.zeros(n)
    for a, b, db in moves:
        g[max(0, int(a * sr)):max(0, int(b * sr))] += db
    L = int(ramp * sr) | 1
    k = np.hanning(L + 2)[1:-1]
    g = np.convolve(np.pad(g, (L // 2, L // 2), mode="edge"), k / k.sum(), mode="valid")
    return 10 ** (g / 20)


def render_accomp(S, rec, hits, total):
    """Raw instrument tracks (mono, piece length): lute, recorder, frame drum, tambourine."""
    n = int(round(total * SR))
    parts = dict(lute=fit(render_lute(S.plucks, total), n))
    if getattr(S, "auto", None):
        parts["lute"] = parts["lute"] * fader(n, S.auto)
    if rec is not None:
        parts["rec"] = fit(rec, n)
    if hits:
        dr, tb = render_hits(hits, total)
        parts["drum"], parts["tamb"] = fit(dr, n), fit(tb, n)
    return parts


def vowel_gate(info, n, pre=0.02, post=0.012, floor_db=-30.0, ramp=0.012, sr=SR):
    """1 over every sung vowel nucleus (shrunk by pre/post), floor elsewhere, smooth: keeps the double off the
    consonants, where two takes' slightly different timing smears the words."""
    g = np.zeros(n)
    for li in info:
        p = li["plan"]
        for sy in p["syls"]:
            a = int((li["t0"] + p["spans"][sy.nucleus[0]][0] + pre) * sr)
            b = int((li["t0"] + p["spans"][sy.nucleus[-1]][1] - post) * sr)
            if b > a:
                g[max(0, a):max(0, min(n, b))] = 1.0
    L = int(ramp * sr) | 1
    k = np.hanning(L + 2)[1:-1]
    g = np.convolve(g, k / k.sum(), mode="same")
    fl = 10 ** (floor_db / 20)
    return fl + (1 - fl) * g


def eq_chain(x, bands):
    """Apply [(kind "low"|"high" shelf | "peak", Hz, dB, shelf slope | Q)] biquads in order (mono or (n, 2))."""
    for kind, f_, db_, q_ in bands:
        if not db_:
            continue
        if kind == "peak":
            b_, a_ = biquad_peak(f_, db_, q_)
        else:
            b_, a_ = biquad_shelf(f_, db_, high=(kind == "high"), s=q_)
        x = lfilter(b_, a_, x, axis=0)
    return x


def mixdown(name, total, lead, double, info, parts):
    """Vocal processing + accompaniment balance + halls + loudness -> stems dict (see the module docstring)."""
    n = int(round(total * SR))
    dbl = fit(double, n)
    if MIX["double_gate"]:
        dbl = dbl * vowel_gate(info, n, floor_db=MIX["double_floor_db"])
    vocal = fit(process_vocal(fit(lead, n), dbl, MIX["double_db"]), n)
    acc = pan(eq_chain(parts["lute"], MIX.get("lute_eq", ())), -0.22) * 1.0
    if "rec" in parts:
        acc += pan(parts["rec"], 0.32) * MIX["rec_gain"]
    if "drum" in parts:
        acc += pan(parts["drum"], 0.08) * MIX["drum_gain"] + pan(parts["tamb"], 0.38) * MIX["tamb_gain"]
    # make room for the words: a gentle dip in the accompaniment's presence band, and the accompaniment
    # ducked (smooth) whenever the bard sings
    if MIX["acc_dip_db"]:
        b_, a_ = biquad_peak(2600, MIX["acc_dip_db"], 0.8)
        acc = lfilter(b_, a_, acc, axis=0)
    acc = eq_chain(acc, MIX.get("acc_eq", ()))
    acc = acc * duck_gain(vocal, SR, depth_db=MIX["acc_duck_db"])[:, None]
    # levels: vocal on top (acc_gap_lu above the accompaniment), then a shared hall
    lv, la = kweight_lufs(vocal), kweight_lufs(acc)
    acc *= 10 ** ((lv - MIX["acc_gap_lu"][name] - la) / 20)
    ir_a = hall_ir(MIX["hall_rt60"][name])
    ir_v = hall_ir(MIX["hall_rt60"][name], predelay=MIX["hall_predelay"])
    send = vocal
    if MIX["hall_hp"]:
        send = sosfilt(butter(2, MIX["hall_hp"] / (SR / 2), btype="high", output="sos"), send)
    v_wet = fit(reverb(send, ir_v), n) * 10 ** (MIX["hall_send_db"] / 20)
    if MIX["hall_duck_db"]:
        v_wet = v_wet * duck_gain(vocal, SR, depth_db=MIX["hall_duck_db"], attack=0.01, release=0.35)[:, None]
    a_wet = fit(reverb(acc, ir_a), n) * 10 ** (-13.0 / 20)
    acc_stem = fit(acc, n) + a_wet
    voc_stem = fit(vocal, n)
    mix = np.stack([voc_stem, voc_stem], 1) * 0.7071 + v_wet + acc_stem
    # fades: tail ring-out
    fo = int(0.9 * SR)
    ramp = np.linspace(1, 0, fo) ** 2
    fi = int(0.003 * SR)                       # ... and a 3 ms head fade-in (the reprise's first pluck is at t = 0)
    ramp_in = 0.5 - 0.5 * np.cos(np.linspace(0.0, np.pi, fi))
    for arr in (mix, acc_stem, v_wet):
        arr[-fo:] *= ramp[:, None]
        arr[:fi] *= ramp_in[:, None]
    voc_stem[-fo:] *= ramp
    voc_stem[:fi] *= ramp_in
    # loudness: mix to the target LUFS; every stem limited to <= -1.5 dBTP *before* the stems are summed,
    # so vocal(both channels) + vocal hall + accomp == mix before the final bus limiter (-1.3 dBTP)
    g = 10 ** ((MIX["target_lufs"][name] - kweight_lufs(mix)) / 20)
    voc_stem = limiter(voc_stem * g * 0.7071, SR, ceiling_db=-1.5)
    acc_stem = limiter(acc_stem * g, SR, ceiling_db=-1.5)
    v_wet *= g
    mix = np.stack([voc_stem, voc_stem], 1) + v_wet + acc_stem
    mix_l = limiter(mix, SR, ceiling_db=-1.3)
    return dict(vocal=voc_stem, accomp=acc_stem, mix=mix_l, vocal_wet=v_wet, lead=lead, double=double,
                lute=parts["lute"])


def make_piece(name, lines, grid, chords, arrange, log):
    t_start = time.time()
    lines_notes = score_notes(lines, grid)
    notes_by_line = {lid: ns for lid, _, ns in lines_notes}
    S, rec, hits, total, marks = arrange(notes_by_line)
    total = round(total, 3)
    log(f"[{name}] {total:.2f} s; singing ...")
    lead, double, info = synth_vocal(lines_notes, total, log)
    log(f"[{name}] vocal done ({time.time() - t_start:.1f}s); instruments ...")
    parts = render_accomp(S, rec, hits, total)
    stems = mixdown(name, total, lead, double, info, parts)
    n = int(round(total * SR))
    timing = dict(duration=total, lines=line_timing(info, fit(lead, n)), info=info, strokes=S.log,
                  marks=marks, grid=grid, chords=chords, notes=lines_notes)
    log(f"[{name}] done in {time.time() - t_start:.1f}s")
    return stems, timing


def piece_json(name, timing, grid, chords, bars):
    lines = timing["lines"]
    first_on = lines[0]["start"]
    marks = {k: round(v, 3) for k, v in timing["marks"].items()}
    final = marks.get("final_chord")
    beats, downs = beat_grid(grid, bars[0], bars[1], extra_downbeats=[final] if final else [])
    strums = sorted(round(s["t"], 3) for s in timing["strokes"])
    chord_list = []
    for bar in sorted(chords):
        if bar < bars[0] or bar > bars[1]:
            continue
        for h in halves_of(grid, bar):
            nm_ = chord_at(chords, bar, h)
            if not chord_list or chord_list[-1]["chord"] != nm_:
                chord_list.append(dict(t=round(grid.t(bar, 3 * h), 3), chord=nm_, bar=bar))
    if final:
        chord_list.append(dict(t=final, chord="D", bar=bars[1] + 1))
    vocal_end = lines[-1]["end"]
    if name == "prologue":
        v2_start = next(l["start"] for l in lines if l["id"] == "s0_l5")
        coda_start = next(l["start"] for l in lines if l["id"] == "s0_l9")
        sections = {"intro": [0.0, first_on], "v1": [first_on, v2_start], "v2": [v2_start, coda_start],
                    "coda": [coda_start, vocal_end], "outro": [vocal_end, timing["duration"]]}
        marks.update(interlude=round(grid.t(9, 0), 3), page_turn_v2=round(grid.t(9, 0), 3),
                     break_=round(grid.t(18, 0), 3), coda_look_up=round(grid.t(17, 3), 3),
                     book_opens=round(marks.get("flourish", 2.56) + 0.3, 3))
        marks["break"] = marks.pop("break_")
    else:
        l2 = lines[1]
        last_note = timing["notes"][-1][2][-1].start
        sections = {"intro": [0.0, first_on], "v1": [first_on, l2["start"]], "v2": [l2["start"], last_note],
                    "coda": [last_note, vocal_end], "outro": [vocal_end, timing["duration"]]}
    sections = {k: [round(a, 3), round(b, 3)] for k, (a, b) in sections.items()}
    clean_lines = []
    for l in lines:
        clean_lines.append({k: l[k] for k in ("id", "text", "start", "end", "sung", "words", "syllables", "env")})
    return {"duration": timing["duration"], "intro_end": round(first_on, 3),
            "tempo": round(60.0 / (grid.eighth * 3), 3), "lines": clean_lines, "beats": beats, "downbeats": downs,
            "strums": strums, "strokes": timing["strokes"], "chords": chord_list, "sections": sections,
            "marks": marks}


def write_wav(path, x, bits=24):
    import soundfile as sf
    sf.write(path, np.clip(x, -1, 1), SR, subtype="PCM_24" if bits == 24 else "PCM_16")


def dump_json(path, d):
    """Compact-but-readable JSON (arrays of numbers inline)."""
    s = json.dumps(d, indent=1, ensure_ascii=False)
    import re
    s = re.sub(r"\[\s+([-0-9.,\s]+?)\s+\]", lambda m: "[" + ",".join(x.strip() for x in m.group(1).split(",")) + "]", s)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(s + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--verify", action="store_true", help="measure pitch / WER / timing / levels, write PNGs")
    ap.add_argument("--only", choices=["prologue", "reprise"], default=None)
    args = ap.parse_args(argv)
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(BUILD_DIR, exist_ok=True)

    def log(s):
        print(s, flush=True)

    result = {}
    jpath = os.path.join(OUT_DIR, "song_timing.json")
    old = {}
    if os.path.exists(jpath):
        with open(jpath, encoding="utf-8") as fh:
            old = json.load(fh)
    pieces = [("prologue", PROLOGUE_LINES, PROLOGUE_GRID, PROLOGUE_CHORDS, arrange_prologue, (0, 22)),
              ("reprise", REPRISE_LINES, REPRISE_GRID, REPRISE_CHORDS, arrange_reprise, (0, 4))]
    for name, lines, grid, chords, arr, bars in pieces:
        if args.only and args.only != name:
            if name in old:
                result[name] = old[name]
            continue
        stems, timing = make_piece(name, lines, grid, chords, arr, log)
        write_wav(os.path.join(OUT_DIR, f"{name}_vocal.wav"), stems["vocal"])
        write_wav(os.path.join(OUT_DIR, f"{name}_accomp.wav"), stems["accomp"])
        write_wav(os.path.join(OUT_DIR, f"{name}_mix.wav"), stems["mix"])
        # scratch: the dry lead (ASR / pitch checks)
        write_wav(os.path.join(BUILD_DIR, f"{name}_lead_dry.wav"), stems["lead"] / (np.abs(stems["lead"]).max() + 1e-9) * 0.7)
        result[name] = piece_json(name, timing, grid, chords, bars)
        if args.verify:
            verify_piece(name, stems, timing, result[name], log)
    doc = {"bpm": M.TEMPO, "meter": "6/8", "beat": "dotted quarter (2 per bar)", "key": M.KEY,
           "motif": {"midi": list(M.MOTIF), "names": list(M.MOTIF_NAMES), "rhythm_eighths": list(M.MOTIF_RHYTHM)},
           "sr": SR, "voice": {k: VOICE[k] for k in ("model", "speaker_id")},
           "stems": {"vocal": "mono, dry processed lead + double (no hall); add to both channels at unity gain",
                     "accomp": "stereo, instruments + their hall, at mix level",
                     "mix": "stereo, vocal + vocal hall + accomp, bus-limited (-1.3 dBTP)"},
           "notes": "times in seconds from the start of each piece; line start/end = first/last sound of the "
                    "sung line; env = 24 fps mouth envelope from line start; strums = every right-hand lute "
                    "stroke (strokes has kind/vel); beats = dotted-quarter beats; sections are contiguous.",
           "reprise_bpm": M.REPRISE_TEMPO}
    doc.update(result)
    dump_json(jpath, doc)
    log(f"wrote {jpath}")


def verify_piece(name, stems, timing, pj, log):
    """Objective checks -> film/build/song/<name>_verify.json + spectrogram PNGs; returns the report.
    (a) pitch: harvest F0 of the dry lead, per note (median of the note's middle), cents vs the score
    (b) intelligibility: faster-whisper (small.en + base.en) on every line rendered in isolation -> WER
    (c) timing: acoustic vowel onsets (voicing + energy rise) vs the notes' beat positions
    (d) levels: peak / true peak / BS.1770 loudness of the stems and the mix
    (e) spectrograms of the vocal and the mix (numpy + Pillow)."""
    import pyworld as pw
    rep = {}
    lead = stems["lead"]
    # (a) pitch: F0 re-measured (harvest) on each sung line, over each note's vowel nucleus
    errs, rows, vib = [], [], []
    for li in timing["info"]:
        p_, ns, y, srl = li["plan"], li["notes"], li["y"], li["sr"]
        f0, t = pw.harvest(y, srl, f0_floor=70, f0_ceil=500, frame_period=5.0)
        li["f0_out_measured"] = (t, f0)
        for sy, nt in zip(p_["syls"], ns):
            na = p_["t0"] + p_["spans"][sy.nucleus[0]][0]
            nb = p_["t0"] + p_["spans"][sy.nucleus[-1]][1]
            segs = []
            if len(nt.pitches) == 1:
                segs.append((na, nb, nt.pitches[0]))
            else:
                ts = nt.start + nt.split * (nt.end - nt.start)
                segs += [(na, ts, nt.pitches[0]), (ts, nb, nt.pitches[1])]
            for a_, b_, m in segs:
                d = b_ - a_
                lo, hi = a_ + min(0.05, 0.25 * d), b_ - min(0.05, 0.25 * d)
                sel = (t + p_["t0"] >= lo) & (t + p_["t0"] < hi) & (f0 > 0)
                if sel.sum() < 3:
                    continue
                cents = 1200 * np.log2(f0[sel] / M.midi_to_hz(m))
                c = float(np.median(cents))
                errs.append(c)
                rows.append(dict(line=li["id"], syl=nt.syl, note=M.note_name(m), cents=round(c, 1),
                                 dur=round(b_ - a_, 3)))
                if b_ - a_ > 0.55:   # vibrato on the sustained part: extent + dominant rate (3-9 Hz)
                    sv = (t + p_["t0"] >= a_ + 0.3) & (t + p_["t0"] < b_ - 0.08) & (f0 > 0)
                    if sv.sum() >= 24:
                        cc = 1200 * np.log2(f0[sv] / M.midi_to_hz(m))
                        cc = cc - np.polyval(np.polyfit(np.arange(len(cc)), cc, 1), np.arange(len(cc)))
                        spec = np.abs(np.fft.rfft(cc * np.hanning(len(cc)), 1024))
                        fr = np.fft.rfftfreq(1024, 0.005)
                        band = (fr >= 3) & (fr <= 9)
                        vib.append((float(np.percentile(np.abs(cc), 90)), float(fr[band][np.argmax(spec[band])])))
    errs = np.array(errs)
    rep.update(pitch_notes=int(len(errs)), pitch_median_abs_cents=float(np.median(np.abs(errs))),
               pitch_mean_abs_cents=float(np.mean(np.abs(errs))), pitch_p90_abs_cents=float(np.percentile(np.abs(errs), 90)),
               pitch_within_25c=float(np.mean(np.abs(errs) < 25)))
    if vib:
        v = np.array(vib)
        rep.update(vibrato_notes=len(v), vibrato_extent_cents=float(np.median(v[:, 0])), vibrato_rate_hz=float(np.median(v[:, 1])))
    worst = sorted(rows, key=lambda r: -abs(r["cents"]))[:5]
    log(f"  (a) pitch: {len(errs)} notes, median |err| {rep['pitch_median_abs_cents']:.1f} c, p90 "
        f"{rep['pitch_p90_abs_cents']:.1f} c, {100 * rep['pitch_within_25c']:.0f}% within 25 c; vibrato "
        f"{rep.get('vibrato_extent_cents', 0):.0f} c @ {rep.get('vibrato_rate_hz', 0):.1f} Hz; worst "
        + ", ".join(f"{w['syl']}({w['note']}) {w['cents']:+.0f}" for w in worst))
    # (b) intelligibility
    try:
        os.environ.setdefault("HF_HOME", os.path.join(BUILD_DIR, "hf"))
        from faster_whisper import WhisperModel
        import re as _re

        def norm(s_):
            s_ = s_.lower().replace("\u2019", "'").replace("neighbors", "neighbours")
            return _re.sub(r"[^a-z0-9' ]+", " ", s_).split()

        def wer(ref, hyp):
            r, h = norm(ref), norm(hyp)
            d = np.zeros((len(r) + 1, len(h) + 1), int)
            d[:, 0] = np.arange(len(r) + 1)
            d[0, :] = np.arange(len(h) + 1)
            for i in range(1, len(r) + 1):
                for j in range(1, len(h) + 1):
                    d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (r[i - 1] != h[j - 1]))
            return int(d[len(r), len(h)]), len(r)

        rep["asr"] = {}
        for mname in ("small.en", "base.en"):
            asr = WhisperModel(mname, device="cpu", compute_type="int8", cpu_threads=2)
            tot_e = tot_n = 0
            per = []
            for li in timing["info"]:
                y = resample_poly(li["y"], 320, 441)        # 22.05 kHz -> 16 kHz
                y = (y / (np.abs(y).max() + 1e-9) * 0.5).astype(np.float32)
                y = np.concatenate([np.zeros(4800, np.float32), y, np.zeros(4800, np.float32)])
                segs, _ = asr.transcribe(y, language="en", beam_size=5, condition_on_previous_text=False,
                                         without_timestamps=True, temperature=0.0)   # no sampling: repeatable
                hyp = " ".join(sg.text.strip() for sg in segs)
                e, n_ = wer(li["text"], hyp)
                tot_e += e
                tot_n += n_
                per.append(dict(line=li["id"], wer=round(e / n_, 3), hyp=hyp))
            whole = lead[int(max(0, pj["lines"][0]["start"] - 0.3) * SR): int((pj["lines"][-1]["end"] + 0.3) * SR)]
            w16 = resample_poly(whole, 1, 3)
            w16 = (w16 / (np.abs(w16).max() + 1e-9) * 0.5).astype(np.float32)
            segs, _ = asr.transcribe(w16, language="en", beam_size=5, condition_on_previous_text=False,
                                     without_timestamps=True, temperature=0.0)
            hyp_w = " ".join(sg.text.strip() for sg in segs)
            ew, nw = wer(" ".join(l["text"] for l in pj["lines"]), hyp_w)
            rep["asr"][mname] = dict(per_line_wer=round(tot_e / tot_n, 3), whole_wer=round(ew / nw, 3),
                                     lines=per, whole_hyp=hyp_w)
            log(f"  (b) WER {mname}: per-line {tot_e}/{tot_n} = {100 * tot_e / tot_n:.1f}%, whole piece "
                f"{100 * ew / nw:.1f}%")
            for r_ in per:
                if r_["wer"] > 0:
                    log(f"        {r_['line']}: {100 * r_['wer']:.0f}%  {r_['hyp']!r}")
    except ImportError:
        log("  (b) faster-whisper not installed: WER skipped (pip install faster-whisper)")
    # (c) timing: acoustic vowel onsets (end of the unvoiced consonant gap -> first sustained voiced, loud
    #     frame; harvest on the output) vs the notes' beat positions, for syllables whose onset ends unvoiced
    on_err, on_rows = [], []
    for li in timing["info"]:
        p_, ns, y, srl = li["plan"], li["notes"], li["y"], li["sr"]
        ph, syls, spans = p_["ph"], p_["syls"], p_["spans"]
        f0o, t = pw.harvest(y, srl, f0_floor=70, f0_ceil=500, frame_period=2.5)
        hop = int(0.0025 * srl)
        e = np.sqrt(np.convolve(y * y, np.ones(hop * 4) / (hop * 4), mode="same")[::hop] + 1e-12)
        edb = 20 * np.log10(e)
        n_ = min(len(edb), len(f0o))
        edb, f0o, t = edb[:n_], f0o[:n_], t[:n_]
        for sy, nt in zip(syls, ns):
            if not sy.onset or ph[sy.onset[-1]] not in UNVOICED:
                continue
            a_, b_ = spans[sy.nucleus[0]][0], spans[sy.nucleus[-1]][1]
            peak = edb[(t >= a_) & (t < b_)].max()
            ts = nt.start - p_["t0"]
            w_ = np.where((t >= ts - 0.12) & (t <= ts + 0.10))[0]
            unv = [i for i in w_ if f0o[i] == 0 and t[i] <= ts + 0.06]
            if not unv:
                continue
            for i in range(max(unv), min(n_ - 4, max(unv) + 80)):
                if np.all(f0o[i:i + 4] > 0) and edb[i] > peak - 10:     # voiced AND at vowel level
                    on_err.append(t[i] - ts)
                    on_rows.append((li["id"], nt.syl, round(1000 * (t[i] - ts))))
                    break
    on_err = np.array(on_err)
    rep.update(onset_notes=int(len(on_err)), onset_median_abs_ms=float(1000 * np.median(np.abs(on_err))),
               onset_p90_abs_ms=float(1000 * np.percentile(np.abs(on_err), 90)),
               onset_mean_ms=float(1000 * np.mean(on_err)), onset_within_40ms=float(np.mean(np.abs(on_err) <= 0.04)))
    log(f"  (c) timing: {len(on_err)} measurable vowel onsets: median |err| {rep['onset_median_abs_ms']:.0f} ms, "
        f"p90 {rep['onset_p90_abs_ms']:.0f} ms, mean {rep['onset_mean_ms']:+.0f} ms, "
        f"{100 * rep['onset_within_40ms']:.0f}% within 40 ms; largest "
        + ", ".join(f"{a_}:{b_} {c_:+d}ms" for a_, b_, c_ in sorted(on_rows, key=lambda r: -abs(r[2]))[:5]))
    rep["onsets"] = on_rows
    # (d) levels
    for k in ("vocal", "accomp", "mix"):
        x = stems[k]
        rep[f"{k}_peak_dbfs"] = float(20 * np.log10(np.abs(x).max() + 1e-12))
        rep[f"{k}_lufs"] = kweight_lufs(x)
    rep["mix_true_peak_dbtp"] = true_peak_db(stems["mix"])
    try:
        import subprocess
        tmp = os.path.join(OUT_DIR, f"{name}_mix.wav")
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", tmp, "-af", "ebur128=peak=true", "-f",
                            "null", "-"], capture_output=True, text=True, timeout=120)
        import re as _re
        mI = _re.findall(r"I:\s+(-?[0-9.]+) LUFS", r.stderr)
        mP = _re.findall(r"Peak:\s+(-?[0-9.]+) dBFS", r.stderr)
        if mI:
            rep["mix_ffmpeg_lufs"] = float(mI[-1])
        if mP:
            rep["mix_ffmpeg_true_peak"] = float(mP[-1])
    except Exception as ex:          # ffmpeg missing: keep the numpy measurement
        rep["ffmpeg_error"] = str(ex)
    log(f"  (d) levels: mix {rep['mix_lufs']:.1f} LUFS (ffmpeg {rep.get('mix_ffmpeg_lufs', float('nan')):.1f}), "
        f"peak {rep['mix_peak_dbfs']:.2f} dBFS, true peak {rep['mix_true_peak_dbtp']:.2f} dBTP; vocal stem "
        f"{rep['vocal_lufs']:.1f} LUFS, accomp stem {rep['accomp_lufs']:.1f} LUFS")
    # (e) spectrograms
    try:
        spectro_png(stems["lead"], SR, os.path.join(BUILD_DIR, f"{name}_vocal_spec.png"), fmax=6000,
                    f0=f0, f0_t=t, marks=[(l["start"], l["id"]) for l in pj["lines"]])
        spectro_png(stems["mix"].mean(axis=1), SR, os.path.join(BUILD_DIR, f"{name}_mix_spec.png"), fmax=8000,
                    marks=[(l["start"], l["id"]) for l in pj["lines"]])
    except Exception as ex:
        log(f"  (e) spectrogram failed: {ex}")
    with open(os.path.join(BUILD_DIR, f"{name}_verify.json"), "w") as fh:
        json.dump(dict(report=rep, notes=rows), fh, indent=1)
    return rep


def spectro_png(x, sr, path, fmax=6000, win=0.046, hop=0.005, height=420, dyn=72, marks=None, f0=None, f0_t=None,
                px_per_s=100):
    """Log-magnitude spectrogram (linear frequency 0..fmax) with optional F0 overlay and line marks."""
    from PIL import Image, ImageDraw
    x = np.asarray(x, np.float64)
    W, H = int(win * sr), int(hop * sr)
    nfft = 1 << int(np.ceil(np.log2(W)))
    pad = np.pad(x, (W // 2, W // 2))
    nfr = 1 + (len(pad) - W) // H
    win_ = np.hanning(W)
    fy = np.linspace(0, fmax, height)
    freqs = np.fft.rfftfreq(nfft, 1 / sr)
    cols = np.empty((height, nfr), np.float32)
    for k0 in range(0, nfr, 2048):
        k1 = min(nfr, k0 + 2048)
        idx = np.arange(W)[None, :] + H * np.arange(k0, k1)[:, None]
        S_ = np.abs(np.fft.rfft(pad[idx] * win_[None, :], nfft, axis=1)) ** 2
        db = 10 * np.log10(S_ + 1e-12)
        for j in range(k1 - k0):
            cols[:, k0 + j] = np.interp(fy, freqs, db[j])
    cols -= cols.max()
    v = np.clip((cols + dyn) / dyn, 0, 1)[::-1]
    r = np.clip(1.5 * v, 0, 1)
    g = np.clip(1.5 * v - 0.5, 0, 1)
    b = np.clip(3 * v, 0, 1) * (v < 0.33) + np.clip(1 - 3 * (v - 0.33), 0, 1) * (v >= 0.33) * (v < 0.66) + \
        np.clip(3 * (v - 0.66), 0, 1) * (v >= 0.66)
    img = Image.fromarray((np.stack([r, g, b], -1) * 255).astype(np.uint8))
    img = img.resize((max(1, int(len(x) / sr * px_per_s)), height), Image.BILINEAR)
    d = ImageDraw.Draw(img)
    sx = img.size[0] / (len(x) / sr)
    if f0 is not None:
        for tt, ff in zip(f0_t, f0):
            if 0 < ff < fmax:
                d.point((tt * sx, height - 1 - ff / fmax * (height - 1)), fill=(0, 255, 120))
    for tt, lab in (marks or []):
        d.line([(tt * sx, 0), (tt * sx, 10)], fill=(255, 255, 255))
        d.text((tt * sx + 2, 0), lab, fill=(255, 255, 255))
    img.save(path)
    return path


if __name__ == "__main__":
    main()
