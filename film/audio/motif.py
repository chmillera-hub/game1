"""THE STONE AND THE BREAD -- the film's shared musical DNA: key, tempo, meter and THE FOUR-NOTE MOTIF.

Everything musical in the film is built from what is defined here, so the bard's song, the speaking
stone's hold music and the closing score are audibly ONE idea, transformed from cold to warm.

    from film.audio import motif as M
    M.MOTIF            # (59, 57, 54, 52)  =  B3  A3  F#3  E3   (MIDI)
    M.MOTIF_RHYTHM     # (1, 1, 1, 3)       eighths: e e e  q.   -> exactly one bar of 6/8
    M.midi_to_hz(M.MOTIF)

KEY / MODE
    D major, with one modal (D mixolydian) colour: the flat-seventh chord C major (bVII), used on
    "CHARMS for the rain" / "STONE he could sell" -- the slightly-off, enchanted, storybook-medieval
    sound (Robin Hood / Shrek fairy-tale kingdom).  Tonic D3 = MIDI 50.  The song's chords are D, G, A,
    A7, Bm, Em, C (see CHORDS); its sung range is A2..D4 (MIDI 45..62).

TEMPO / METER
    6/8, felt in two: TEMPO = 74 dotted-quarter beats per minute (one eighth = 0.2703 s, one bar =
    1.622 s).  A folk-ballad lilt: walking, warm, never a jig.  The reprise and the score are slower
    (REPRISE_TEMPO = 64; the score may go as slow as ~54 with rubato).

THE FOUR-NOTE MOTIF  (scale degrees 6-5-3-2 of D major: a gentle falling pentatonic figure)
    notes   B3  A3  F#3  E3      MIDI (59, 57, 54, 52)
    rhythm  e   e   e    q.      (1, 1, 1, 3) eighths = one 6/8 bar
    It ENDS ON THE 2nd DEGREE (E): on its own it never comes home -- it hangs, waiting.  Its home is the
    tonic D one step below: RESOLUTION = 50 (D3).  The whole film is that one missing step.

  1. THE SONG HOOK  (film/audio/song.py, "A Kingdom of Stone")
     Sung at pitch (B3 A3 F#3 E3) on the title phrase "in a KING-dom of STONE" (harmony | G | A |,
     a half cadence: the kingdom is stuck), and again on "a LOCK on each HEART", "a SCARF and a SIGH",
     "WHAT he was MISS-ing".  The final line states it twice: "How a KING-dom of STONE" (| G | Em |,
     cold, minor) ... "found its WAY back to BREAD" (| G | A7 |) where, for the only time in the
     song, the E is allowed to fall to D on "bread" (a two-note melisma E3 -> D3 over A7 -> D): the
     motif comes home.  The end-card reprise does the same on "HUN-gry for BREAD ... BENCH next to YOU".

  2. THE HOLD MUSIC  (scene 3, the speaking stone -- cold, mechanical)
     The same four notes two octaves up on a tinny music box: MUSIC_BOX_MOTIF = (83, 81, 78, 76)
     (B5 A5 F#5 E5), rhythm (1, 1, 1, 3), looped with NO harmony and NO resolution, dead-even machine
     timing (no swing, no rubato) at HOLD_TEMPO = 80 (eighth = 0.25 s, loop = 1.5 s), forever.  Because
     it stops on E and jumps back up to B, the loop never arrives anywhere: "please hold".  Make it
     cold with timbre: bright inharmonic tines (partials ~1, 2.76, 5.4, 8.93 x f0), short decays
     (~0.6-0.9 s), comb teeth a few cents out of tune, a faint mechanical click per note, dry, then the
     stone-phone band-pass (~300-3400 Hz).  Optionally let the spring run down very slightly (tempo and
     pitch sag ~1-2 %) late in the hold.  hold_music_events() returns the note list.

  3. THE SCORE  (scenes 6-9 -- the motif blooms: the stone turned into bread)
     The same four notes, slow (one note per bar or per dotted-half), low-to-mid register on piano /
     harp / celesta, HARMONIZED WARMLY (WARM_HARMONY): B over Gmaj7, A over D/F#, F# over Bm7,
     E over A(sus4 -> 3) ... and then the step the hold music never takes: E falls to D over D(add9).
     Suggested arc: S6 at the laugh: the bare motif once, high and soft (harp/celesta, B4 A4 F#4 E4),
     unharmonized but slow and rubato -- recognisable, no longer mechanical.  S7: harmonized with
     WARM_HARMONY, a little fuller each statement as the bench fills.  S8: full bloom under the
     voice-over; still never resolving until the very end.  S9 (end card): the reprise carries the
     resolution (sung E -> D on "you"), and the score ends on the held D(add9) chord (FINAL_CHORD).
     score_events() returns a ready-made harmonized statement.

All functions are pure (no I/O); every value here is the single source of truth -- do not re-derive.
"""
from __future__ import annotations

import math
from typing import Iterable, Sequence

# ------------------------------------------------------------------------------------------------
# key / tempo / meter
# ------------------------------------------------------------------------------------------------
KEY = "D major (with a D-mixolydian bVII colour chord, C major)"
TONIC = 50                                   # D3
TONIC_PC = 2                                 # pitch class of D
SCALE = (0, 2, 4, 5, 7, 9, 11)               # major scale steps
METER = (6, 8)                               # 6/8, felt in two dotted-quarter beats per bar
TEMPO = 74.0                                 # dotted-quarter beats per minute (the prologue song)
REPRISE_TEMPO = 64.0                         # the end-card reprise (softer, slower)
HOLD_TEMPO = 80.0                            # music-box hold loop (dotted-quarter bpm)
EIGHTHS_PER_BEAT = 3
BEATS_PER_BAR = 2

# ------------------------------------------------------------------------------------------------
# THE FOUR-NOTE MOTIF
# ------------------------------------------------------------------------------------------------
MOTIF = (59, 57, 54, 52)                     # B3 A3 F#3 E3  (scale degrees 6 5 3 2)
MOTIF_NAMES = ("B3", "A3", "F#3", "E3")
MOTIF_DEGREES = (6, 5, 3, 2)
MOTIF_RHYTHM = (1, 1, 1, 3)                  # eighth notes: e e e q.  = one 6/8 bar
RESOLUTION = 50                              # D3: where the motif finally comes home ("bread")
MUSIC_BOX_MOTIF = tuple(m + 24 for m in MOTIF)   # B5 A5 F#5 E5 (hold music)
SCORE_MOTIF = tuple(m + 12 for m in MOTIF)       # B4 A4 F#4 E4 (score melody register)

# ------------------------------------------------------------------------------------------------
# chords (root-position chord tones as MIDI around octave 3) and the harmonizations of the motif
# ------------------------------------------------------------------------------------------------
CHORDS = {
    "D": (50, 54, 57), "Dadd9": (50, 54, 57, 64), "D/F#": (42, 50, 57), "Dmaj7": (50, 54, 57, 61),
    "G": (43, 47, 50), "Gmaj7": (43, 47, 50, 54), "Gadd9": (43, 47, 50, 57),
    "A": (45, 49, 52), "A7": (45, 49, 52, 55), "Asus4": (45, 50, 52), "Asus2": (45, 47, 52),
    "Bm": (47, 50, 54), "Bm7": (47, 50, 54, 57),
    "Em": (52, 55, 59), "Em7": (52, 55, 59, 62),
    "C": (48, 52, 55), "F#m": (42, 45, 49),
}

# The song's hook harmonies (cold) and the score's (warm). One chord per motif note.
SONG_HARMONY = ("G", "G", "G", "A")          # "KING-dom of STONE": | G . . | A . . |   (half cadence)
COLD_HARMONY = ("G", "G", "Em", "Em")        # "KING-dom of STONE" in the last line: stays minor
WARM_HARMONY = ("Gmaj7", "D/F#", "Bm7", "Asus4")   # score: IV - I6 - vi7 - Vsus4 (-> V) ...
WARM_RESOLVE = ("A", "Dadd9")                # ... sus4 opens to A, then E falls to D over D(add9)
FINAL_CHORD = "Dadd9"

# The song's verse progression, one chord per dotted-quarter beat (2 per bar), bars 1-8.
VERSE_PROGRESSION = (("D", "D"), ("G", "A"), ("D", "D"), ("A", "Bm"),
                     ("D", "G"), ("C", "Em"), ("G", "A"), ("A7", "D"))


# ------------------------------------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------------------------------------
def midi_to_hz(m):
    """MIDI note number(s) -> Hz (A4 = 69 = 440 Hz). Accepts a number or a sequence."""
    if isinstance(m, (int, float)):
        return 440.0 * 2.0 ** ((m - 69.0) / 12.0)
    return [440.0 * 2.0 ** ((x - 69.0) / 12.0) for x in m]


def hz_to_midi(f: float) -> float:
    return 69.0 + 12.0 * math.log2(max(f, 1e-9) / 440.0)


_NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note(name: str) -> int:
    """'F#3' -> 54, 'Bb2' -> 46 (scientific pitch, C4 = 60)."""
    s = name.strip()
    pc = _NAMES[s[0].upper()]
    k = 1
    while k < len(s) and s[k] in "#b":
        pc += 1 if s[k] == "#" else -1
        k += 1
    return 12 * (int(s[k:]) + 1) + pc


def note_name(m: int) -> str:
    n = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")[int(m) % 12]
    return f"{n}{int(m) // 12 - 1}"


def eighth_seconds(tempo: float = TEMPO) -> float:
    """Length of one eighth note at `tempo` dotted-quarter bpm (6/8)."""
    return 60.0 / tempo / EIGHTHS_PER_BEAT


def bar_seconds(tempo: float = TEMPO) -> float:
    return 6.0 * eighth_seconds(tempo)


def degree(d: int, octave: int = 3) -> int:
    """Scale degree (1..7, may exceed 7) of D major -> MIDI.  degree(1) = D3 = 50."""
    d0 = d - 1
    return TONIC + 12 * (octave - 3) + 12 * (d0 // 7) + SCALE[d0 % 7]


def chord_tones(name: str) -> tuple:
    return CHORDS[name]


def voicing(name: str, low: int = 40, high: int = 72, top: int | None = None, n: int = 4,
            bass: bool = True) -> list:
    """A spread, warm voicing of chord `name` between MIDI `low`..`high`.
    bass=True puts the chord's lowest listed tone (root, or the slash bass) in the bottom octave >= low.
    top: optional melody note that must be the highest note (other tones are placed below it).
    Returns ascending MIDI notes (n tones, or fewer if the range is tight)."""
    pcs = []
    for t in CHORDS[name]:
        if t % 12 not in pcs:
            pcs.append(t % 12)
    bass_pc = pcs[0]
    ceiling = (top - 1) if top is not None else high
    out, start = [], low
    if bass:
        b = low + ((bass_pc - low) % 12)            # lowest note >= low with the bass pitch class
        out.append(b)
        start = b + 7                                # open fifth (or more) above the bass
    # every chord tone appears once in the upper structure (the bass pc is only re-used for triads)
    upper = [p for p in pcs if not (bass and p == bass_pc and len(pcs) > 3)]
    want = n - len(out) - (1 if top is not None else 0)
    best = None
    for shift in (0, -12, -24):                      # drop the stack an octave if it overshoots the ceiling
        for r in range(len(upper)):                  # most compact close-position rotation
            order = upper[r:] + upper[:r]
            seq, cur = [], max(start + shift, (out[0] + 3) if out else low)
            for p in order:
                c = cur + ((p - cur) % 12)
                seq.append(c)
                cur = c + 1
            k = 0
            while len(seq) < want:                   # doublings: repeat the stack an octave up
                seq.append(seq[k] + 12)
                k += 1
            seq = seq[:max(want, 0)]
            if seq and seq[-1] <= ceiling and (best is None or seq[-1] < best[-1]):
                best = seq
        if best is not None:
            break
    out += best or []
    if top is not None:
        out.append(top)
    return sorted(out)


def motif(transpose: int = 0) -> list:
    """The four motif notes (MIDI), optionally transposed by semitones (use +-12 multiples to keep
    the identity; the hold music uses +24, the score +12 or 0)."""
    return [m + transpose for m in MOTIF]


def motif_events(t0: float, eighth: float, transpose: int = 0, loops: int = 1, gap_eighths: float = 0.0,
                 resolve: bool = False) -> list:
    """[(start_s, dur_s, midi)] for `loops` back-to-back statements of the motif with rhythm MOTIF_RHYTHM.
    resolve=True appends the resolution note (motif E falls to D) as one extra bar after the last loop."""
    ev, t = [], t0
    for _ in range(loops):
        for m, r in zip(MOTIF, MOTIF_RHYTHM):
            ev.append((t, r * eighth, m + transpose))
            t += r * eighth
        t += gap_eighths * eighth
    if resolve:
        ev.append((t, 6 * eighth, RESOLUTION + transpose))
    return ev


def hold_music_events(duration: float, t0: float = 0.0, tempo: float = HOLD_TEMPO) -> list:
    """Scene-3 music box: MUSIC_BOX_MOTIF looped, dead-even, no harmony, never resolving, filling
    `duration` seconds from t0. [(start_s, dur_s, midi)]"""
    e = eighth_seconds(tempo)
    loop = sum(MOTIF_RHYTHM) * e
    n = int(math.ceil(duration / loop)) + 1
    ev = [x for x in motif_events(t0, e, transpose=24, loops=n) if x[0] < t0 + duration]
    return ev


def score_events(t0: float, note_seconds: float = 2.4, register: int = 12, resolve: bool = True,
                 harmony: Sequence[str] = WARM_HARMONY, chord_low: int = 38, chord_high: int = 69) -> list:
    """A slow, warmly harmonized statement of the motif for the score (scenes 6-9).
    Each motif note lasts `note_seconds`; under it the chord from `harmony` (bass + inner voices).
    Returns [(start_s, dur_s, midi, role)] with role 'melody' | 'chord' | 'bass'.
    resolve=True adds the sus4 -> 3 opening and the final E -> D resolution over D(add9)."""
    ev = []
    t = t0
    mel = motif(register)
    for i, (m, ch) in enumerate(zip(mel, harmony)):
        v = voicing(ch, low=chord_low, high=chord_high, top=None, n=4)
        ev.append((t, note_seconds, v[0], "bass"))
        for x in v[1:]:
            if x < m:
                ev.append((t + 0.03 * (1 + v.index(x)), note_seconds, x, "chord"))
        ev.append((t, note_seconds, m, "melody"))
        t += note_seconds
    if resolve:
        # sus4 opens to the major third, then the melody steps down E -> D over D(add9)
        a = voicing(WARM_RESOLVE[0], low=chord_low, high=chord_high, n=4)
        for x in a:
            ev.append((t - 0.5 * note_seconds, 0.5 * note_seconds, x, "chord" if x != a[0] else "bass"))
        d = voicing(WARM_RESOLVE[1], low=chord_low, high=chord_high, n=5)
        for x in d:
            ev.append((t, 2.0 * note_seconds, x, "chord" if x != d[0] else "bass"))
        ev.append((t, 2.0 * note_seconds, RESOLUTION + register, "melody"))
    return ev


if __name__ == "__main__":
    print("KEY", KEY, "| TEMPO", TEMPO, "| METER", METER)
    print("MOTIF", [note_name(m) for m in MOTIF], MOTIF_RHYTHM, ["%.1f Hz" % f for f in midi_to_hz(MOTIF)])
    print("hold music (first loop):", [(round(a, 3), round(b, 3), note_name(c)) for a, b, c in hold_music_events(1.6)])
    for name in WARM_HARMONY + WARM_RESOLVE:
        print(f"  {name:6s}", [note_name(x) for x in voicing(name)])
