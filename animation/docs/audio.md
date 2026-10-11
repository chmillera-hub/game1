# Audio engine — reference for scene animators and the mixer

Files: `audio/audiolib.py` (DSP + mix), `audio/music.py` (score renderer), `audio/sfx.py` (SFX synthesiser),
`audio/sfx/*.wav` (generated SFX), `data/music_cues.example.json` (a complete score, every mood, story order).
All audio is 44.1 kHz stereo float internally; files are 16-bit PCM WAV.

```bash
python3 audio/sfx.py                                   # (re)build all 20 SFX → audio/sfx/<name>.wav   (~5 s)
python3 audio/sfx.py --list                            # names + one-line descriptions
python3 audio/sfx.py heartbeat sob --spectro out       # rebuild some + write out/spectro_sfx_<name>.png
python3 audio/music.py data/music_cues.example.json out/music_example.wav    # ~45 s for the 5.65-min score
python3 audio/music.py data/music_plan.json out/music.wav   # the production plan renders directly (from/to/at)
python3 audio/music.py cues.json out.wav --roll out/roll.png --notes out/notes.txt   # debug: piano roll + note list
python3 audio/music.py cues.json out.wav --lufs -18 --seed 0 --cue-dir out/cues --quiet  # target / humanisation / per-cue stems
python3 audio/audiolib.py mix --music out/music.wav --sfx data/sfx_events.json --out out/mix.wav
python3 audio/audiolib.py check out/mix.wav            # peak / true peak / LUFS / DC / NaN / click score
python3 audio/audiolib.py spectro in.wav out.png [--max-hz 8000] [--seconds a:b]
```
Render speed: the score takes ≈ 7–8 s per minute of film (4 cores) — well inside "< 2 min for a 6-min score".

**Production path** (what `tools/render_all.sh` ends up muxing): `tools/resolve_music.py` turns
`data/music_plan.json` into `data/music_cues.json` → `python3 audio/music.py data/music_cues.json out/music.wav`
→ `python3 audio/mix.py` (the pipeline's mixer: reads `out/music.wav` + `data/sfx_events.json`, writes `out/mix.wav`).
`audiolib.mix_film` / `audiolib.py mix` (§4) is an alternative mixer that writes the same file.
Re-render the score whenever the timeline changes (anchors and dialogue gaps move with it).

## 1. Sound effects (`audio/sfx/<name>.wav`)

Every file peaks at -3 dBFS, has no DC, natural fades (except the two seamless loops).
**Sync point** = where the audible event sits *inside* the file. To land a hit exactly on an anchor,
subtract it: `{ at: 's08b01+0.40-0.03', name: 'cage_close' }` puts the clang at `s08b01+0.40`.
**Gain** = recommended dB for a dialogue stem at -18 LUFS (also `audiolib.SFX_GAIN`). Start there, ±4 dB to taste.

| name | dur s | loop | sync point(s) in file (s) | what it is | gain dB |
|---|---|---|---|---|---|
| alarm_bell | 3.00 | **seamless** | continuous from 0 | electric fire bell: 22 Hz striker on inharmonic gong partials 1.2–5.6 kHz, "rrrring" | -18 |
| alarm_pull | 0.60 | – | scrape 0.00, **clack 0.055**, latch 0.14 | plastic/metal pull-station lever | -6 |
| footsteps | 2.50 | – | steps at 0.08, 0.64, 1.20, 1.76 (alt. L/R) | 4 soft steps: 95 Hz heel thump (+ its saturated harmonics), 200–800 Hz floor knock, soft contact tick, scuff. ~42 % of the energy above 200 Hz (reads on phones) | -9 |
| door_whoosh | 1.30 | – | swell peak 0.43, soft thud 1.00 | swinging door, moves L→R | -13 |
| crowd_murmur | 4.00 | – | fades in 0–0.35, out 3.4–4.0 | indistinct worried walla, 8 voices, distant | -14 |
| heartbeat | 1.30 | **seamless** | lub 0.06, dub 0.34 | one cycle (46 bpm); loop it; `rate` 1.3 ≈ 60 bpm. Sub thump + 130–500 Hz body knock + the thump's saturated harmonics (180–700 Hz) + valve tick + a soft 1–3.5 kHz onset click. ~29 % of the energy above 200 Hz (reads on phone speakers); ~2 dB louder (LUFS) than the old sub-only version | -12 |
| breath_shaky | 2.90 | – | inhale 0.0–1.3 (catches at 0.45, 0.85), exhale 1.45–2.85 | trembling breath | -13 |
| sob | 1.90 | – | 3 hitches 0.05/0.21/0.35, two breathy whimper catches 0.56 / 0.83 (to ~1.15), exhale 1.1–1.85 | small, soft hitched sob | -12 |
| cage_close | 2.60 | – | **clang 0.03**, rattles to 0.4, latch 0.45, ring to ~2.3 | metal gate shutting | -5 |
| lock_click | 0.32 | – | clicks 0.02, 0.058 | spring latch / padlock | -10 |
| cage_creak | 2.20 | – | swell 0.15–1.9 (peak ~0.7) | slow hinge creak (stick-slip) | -12 |
| key_turn | 0.95 | – | pin ticks 0.05–0.21, grind 0.45–0.65, **bolt 0.68** | key in, turn, clunk | -9 |
| rumble_low | 5.00 | – | rises 0–2.6, peak 2.6, fades to 5.0 | sub-bass swell (41 Hz) + a 70–350 Hz churn/harmonic layer + the tone's 5th–12th harmonics (soft clipper) and a dark 180–700 Hz grit band. ~25 % of the energy above 200 Hz, so it reads on phones | -14 |
| shimmer | 3.00 | – | swells in 0–1.0, sparkles 0.1–2.6 | bowed-glass + celesta wash, D lydian (matches the score) | -15 |
| twinkle | 1.90 | – | notes 0.02 (A6), 0.20 (E7), 0.42 (F#6) | three celesta notes, D major | -18 |
| console_beeps | 1.00 | – | blips 0.02, 0.13, 0.24, 0.48 | soft friendly UI blips (E6 A6 C#7, F#6) | -24 |
| paper_rustle | 1.10 | – | swish peak 0.5, crinkles throughout | notebook page handling/turn | -12 |
| lamp_click | 0.30 | – | press 0.02, release 0.11 | desk-lamp switch | -8 |
| cloth_rustle | 1.00 | – | swishes 0.0 / 0.28 / 0.5 | soft fabric movement | -15 |
| rust_creak | 1.70 | – | swell 0.1–1.5 (peak ~0.65) | rusty, grainy gate squeak | -17 |

### Scene SFX entries (`export const sfx = [...]` → `tools/collect_sfx.mjs` → `data/sfx_events.json`)
| field | default | meaning |
|---|---|---|
| `at` | – | anchor/seconds where the **file** starts (subtract the sync point, see above) |
| `name` | – | one of the 20 names |
| `gain` | 0 | dB on the -3 dBFS file (use the table) |
| `until` | null | anchor where it stops: loops repeat until then; one-shots are cut there |
| `loop` | false | repeat the file until `until` (needs `until`). alarm_bell/heartbeat butt-join seamlessly; others get a 40 ms crossfade |
| `pan` | 0 | -1 left … +1 right (mono → equal-power, unity at centre; stereo files → balance) |
| `fade` | 0.3 | fade-out (s) applied at `until` |
| `rate` | 1 | varispeed (pitch + speed): 1.2 = 20 % faster/higher. Heartbeat 1.0 = 46 bpm, 1.4 ≈ 65 bpm |

Gotchas: SFX are mono-compatible but mostly stereo (short room ambience baked in, wet 8–35 %); don't add more
reverb in the scene. The bell is meant to sit *under* the narration (-16…-20 dB) — it is unsettling, not loud.
Only `alarm_bell` and `heartbeat` are made to loop: `audio/mix.py` butt-joins repeats with no crossfade, so a
looped one-shot (e.g. `crowd_murmur`) would pulse with its own fades — place several overlapping copies instead
(`audiolib.render_sfx_events` crossfades 40 ms, which is smoother but still not seamless).
Phone speakers reproduce little below ~150–200 Hz: `heartbeat`, `rumble_low` and `footsteps` therefore carry a
harmonic/body layer above 200 Hz (energy share above 200 Hz: heartbeat 1.5 → 29 %, rumble_low 1.6 → 25 %,
footsteps 4.4 → 42 %; level through a 250 Hz high-pass +8…+12 dB vs. the old files). Their weight on
headphones is still sub-bass — on phones they read as soft knocks/rumbles, not as big hits.

## 2. Music (`audio/music.py`)

Orchestra: MuseScore_General.sf2 via tinysoundfont, rendered stem by stem, sample-accurately (notes are
scheduled in blocks between events), per-stem EQ ("felt" piano = low-passed soft layer), two reverb buses
(hall 2.6 s, "vast" 5.5 s dark), gentle glue compression, loudness-normalised (default **-18 LUFS**, re-trimmed
after limiting so it lands on target), true-peak limited to -1 dBTP. Deterministic (seeded humanisation).

### Cue sheet
```json
{ "timeline": "data/timeline.json",        // anchors + dialogue (default data/timeline.json)
  "speech_from": "data/timeline.json",     // dialogue = beats with kind "line". DEFAULT = the timeline above, so it
                                           //   may be omitted; false = no dialogue awareness
  "speech": [[12.0, 14.5]],                // extra dialogue intervals, absolute s (optional)
  "duration": "film.end",                  // number or anchor; default = timeline duration
  "cues": [ { "start": "s13b06-0.3", "end": "s14b06.end+1.5", "mood": "reveal_wonder", "intensity": 0.5,
              "fade_in": 2.5, "fade_out": 2.5, "open_at": "s14b01+0.3",
              "hits": [{ "t": "s14b01+0.3", "type": "swell", "len": 5 }] } ] }
```
Every time (`start`, `end`, `duration`, `open_at`, `hits[].t`) is **seconds or an anchor** with the `src/timeline.mjs`
syntax: `'s05b03'`, `'s05b03.end'`, `'s05b03.mid'`, `'s05b03+1.2'`, `'s05b03.end-0.4'`, `'s07'` (scene start), `'s07.end'`,
`'film.end'`. Unknown ids abort with a clear message. The plan spelling of `data/music_plan.json` is accepted too
(`from`/`to` for `start`/`end`, `at` for `t`), so the plan renders without `tools/resolve_music.py`.
The renderer prints `[music] dialogue: N lines from …` — if it says no timeline was found, melodies are **not**
kept out of the dialogue.

| cue field | default | meaning |
|---|---|---|
| `start`, `end` | – | cue span; cues may overlap — overlapping fades are equal-power crossfades |
| `mood` | – | one of the 12 moods below |
| `intensity` | 0.4 | 0..1: level (−7 dB at 0), velocities, number of layers (strings/choir/celesta/cello join at ~0.3–0.55) |
| `key` | "D" | tonic (C, C#, Db … B; a trailing `m` is ignored — the mood sets the mode). Folded into −6…+5 semitones of D |
| `bpm` | mood | tempo override (moods are 60–72) |
| `fade_in` / `fade_out` | 1.5 / 2.0 | sine fades inside [start, end] (min 0.02 / 0.05). No melodic phrase starts inside them |
| `hits` | [] | `{t, type, len?}` — see below |
| `phrases` | mood | ordered list of phrase names to try in each dialogue gap (longest that fits wins) |
| `phrase_seq` | – | names used in order, one per placed phrase (`X_short` variants are tried automatically) |
| `phrase_stem` / `phrase_oct` | mood | instrument for the melody (piano, musicbox, celesta, cello, strings, viola, harp…) / octave shift in semitones |
| `tone` | "high" | stillness only: held `high` A5 harmonic, `low` D2 note, or `both` |
| `open_at` | – | reveal_wonder only: the **void sonority** holds until here, then opens (see moods) |

**Hits** (all five work in every mood):
- `swell` — gentle crescendo over `len` s (default 4.5): adds a strings (+choir/horns/glass per mood) layer that
  grows from silence, +3 dB and intensity +0.25 for the rest of the cue.
- `sting` — soft-but-sudden accent, music continues. Dark moods (curious_unease, alarm_chaos, void_presence,
  confrontation, sorrow, stillness, dread): timpani + low strings on a b9 cluster over the tonic pedal + low piano.
  Bright moods: the chord sounding at `t`, voiced warm (timpani on its root, low strings, piano octave, one celesta glint).
- `drop` — falls to −26 dB in 0.35 s, no new notes until the next hit.
- `silence` — fades to 0 in 0.2 s, nothing until the next hit (the reverb tail rings out).
- `resolve` — cadence on the tonic exactly at `t` (dominant/plagal before it; if the dialogue leaves room a motif
  phrase is placed so that its last note **lands on t**), rolled tonic chord, tonic held afterwards. After a
  drop/silence it brings the level back over 0.3 s (never lowers it after a swell).

**Dialogue awareness**: melodic phrases are placed only in dialogue gaps (line edges padded 0.3 s before /
0.2 s after), outside the cue's own fade-in/fade-out, never over a phrase of an overlapping cue (earlier cues in
the sheet win), and never squeezed more than ~12 % faster than the cue tempo — a gap that is too short simply
gets no melody. Phrases snap to the bar grid's half-beats. Under speech the moods keep to pads, low strings and
very soft high piano "pings". The bar grid is stretched ≤ ±12 % so hits land on downbeats.

### Moods (default key D)
| mood | tempo | harmony / texture | melody in gaps |
|---|---|---|---|
| tender_memory | 66 | D major ↔ Bm: felt piano broken chords, warm pad, celesta glints (I≥0.2), strings (I≥0.55) | memory theme |
| curious_unease | 62 | D minor/dorian, #11 colours: pizzicato tiptoe, pad, eerie glass 9th | fear motif (fragile) on music box |
| alarm_chaos | 72 | D pedal, b6 → Neapolitan → V: strings 8th ostinato (3+3+2), tremolo, timpani — **no melody**; a `resolve` lands on a plain tonic chord | none |
| void_presence | 60 | the VOID sonority: low open fifths D–A(–E/F), dark pad, bowed-glass fifth breathing, distant timpani roll | none |
| confrontation | 66 | D minor, gentle but firm: strings, composed viola line, one sustained piano note per bar | fear motif, questioning |
| sorrow | 60 | D minor lament: low strings, solo cello long tones (A-G-F-E…), sparse piano | lament / fragile motif on cello |
| stillness | 60 | almost nothing: one held tone (`tone`); resolve = a single warm low piano chord + pad | via `phrases` only |
| dread | 60 | held minor-9th / tritone over D, timpani heartbeat slowing ~66→42 bpm, low horn semitone (I≥0.4) | via `phrases` only |
| reveal_wonder | 64 | Dmaj9 ↔ E/D (lydian), strings, choir aahs, celesta cascades, harp arpeggios. With `open_at`: before it the void sonority (dark pad + low strings D–A, bowed-glass A–E); at it a harp glissando rises into the downbeat, the fifths become the root of the lydian cluster, strings/choir bloom in over 3–5 s and the void drone recedes | wonder (lydian motif) on celesta + harp, only after the opening |
| belonging | 66 | D major descending bass, warm strings, piano, cello counter-line (I≥0.42) | fear motif, hopeful |
| resolution | 63 | tonic-pedal plagal D – G/D, warm pad, half-note piano | fear motif, resolved |
| outro | 60 | **solo piano** (a soft pad joins only at I≥0.4); after `resolve`: final chord + celesta twinkles | fear motif, resolved (ends on the tonic at the resolve hit) |

**Leitmotifs** (`PHRASES` in music.py; each has a `_short` variant): `memory` (5-3-2-3…), `fear_minor`
(b3-2-b3 · 5, hesitant), `fear_question` (…5-6, hangs on IV), `fear_hope` (major, ends on 5), `fear_resolved`
(3-2-3-5 | 4-3-2-1 over a cadential 6/4), `wonder` (3-2-3-5-#4-5, lydian), `lament` (5-4-3-2-1).
In the example score the Fear motif travels: fragile music box (s02) → fragile minor piano (s04) → questioning
(s06) → fragile on cello + the lament (s07–s08) → questioning music box (s11) → questioning/fragile fragments in
the pauses of s12 → wonder (s14: at the void's opening and in its pauses) → hopeful (s15–s16) → resolved
(s17 after "Can I help?", s20 ending on the final tonic).

Console report (stdout): per cue RMS / peak / LUFS / phrase count + whole-file health. `--cue-dir DIR` writes each cue dry.
The example sheet's loudness arc (file normalised to -18 LUFS integrated): tender ≈ -19, curious/alarm -19…-23,
void -17…-22, dread -18…-20, stillness -26 / -22, reveal -14.4 (peak), hush -21, belonging -15, resolution -17,
outro (solo piano) -19.

## 3. audiolib API (`import sys; sys.path.insert(0, 'audio'); import audiolib as A`)
Arrays are float32 `(n, 2)` at `A.SR = 44100`; mono `(n,)` accepted almost everywhere. Times in s, gains in dB, pan -1…+1.

| function | notes |
|---|---|
| `load(path, sr=SR, stereo=True)` / `save(path, x, sr=SR, subtype='PCM_16', dither=True)` | any format in; save clamps to ±1 with TPDF dither |
| `to_stereo(x)`, `to_mono(x)`, `silence(sec)`, `resample(x, sr_from, sr_to)`, `change_rate(x, rate)` | |
| `db2lin`, `lin2db`, `gain_db(x, db)`, `peak_normalize(x, peak_db=-3)`, `remove_dc(x, hz=12)` | |
| `fade_in(x, sec, shape='sine')`, `fade_out(...)`, `fades(x, fin, fout)` | shapes: sine (equal power), linear, exp, log |
| `pan(x, p)`, `pan_gains(p)` | mono: equal-power, unity at centre (hard pan = +3 dB one side); stereo: balance |
| `highpass/lowpass(x, hz, order=2)`, `bandpass(x, lo, hi)`, `peaking_eq(x, hz, gain, q=1)`, `low_shelf/high_shelf(x, hz, gain)`, `eq_chain(x, [('hp',80),('peak',3000,-2,1)…])` | Butterworth / RBJ biquads |
| `make_reverb_ir(decay=2.4, predelay=0.02, damping=0.5, size=0.6, cross=0.3, seed=7)` | true-stereo synthetic IR `(n,2,2)`: decorrelated noise tails, band-dependent RT60 (darker tail), early reflections, unit energy |
| `reverb(x, wet=0.25, dry=1.0, keep_tail=True, **ir_params, width=1.0)`, `reverb_wet(x, …)` | FFT convolution (float32); `keep_tail` extends the output. Measured RT60 of the music's "hall": 2.9 s lows → 1.7 s highs; "vast": 5.8 → 3.1 s; L/R correlation ≈ 0 |
| `compress(x, threshold_db=-18, ratio=3, attack=0.01, release=0.15, knee_db=6, makeup_db=0, sidechain=None)` | soft-knee RMS, stereo-linked |
| `duck(music, voice, depth_db=-9, attack=0.08, release=0.5, threshold_db=-45, hold=0.25, lookahead=None, return_gain=False)` | sidechain ducking; lookahead defaults to `attack` so the music is down at the first syllable; `hold` bridges word gaps |
| `place(track, clip, at_seconds, gain_db=0, pan=0)` → track | adds in place, **grows the track; always use the return value**; negative `at` trims the head |
| `render_sfx_events(events, duration, sfx_dir=None)` | renders `data/sfx_events.json`-style events (loop/until/fade/rate/pan/gain) |
| `loudness(x)` → LUFS | ITU-R BS.1770-4 (K-weighting, 400 ms/75 %, abs -70 + rel -10 gates); matches ffmpeg ebur128 |
| `normalize_loudness(x, target_lufs=-16)`, `true_peak(x)` → dBTP, `limit(x, ceiling_db=-1, lookahead=0.005, release=0.08)`, `master(x, target_lufs=-16, ceiling_db=-1)` | look-ahead limiter with 4× oversampled (true-)peak detection, smooth attack + exponential release, verified ≤ ceiling. Only blocks whose sample peak is within 6 dB of the ceiling are oversampled (fast). `master` = normalise → limit → re-trim (≤ 2 passes) so the limited result lands within 0.05 LU of the target |
| `analyze(x)` → dict | peak, true peak, RMS, LUFS, DC, NaN count, max sample jump, click score (>~8 on music = suspicious) |
| `spectrogram_png(x, path, max_hz=8000, width=1400, height=420, marks=[(sec,label)])` | log-frequency spectrogram + RMS/peak strip |
| `mix_film(timeline, music, sfx_events, out, voice_lufs=-18, music_lufs=-25, duck_db=-8, sfx_db=0, master_lufs=-16, ceiling_db=-1)` | full mix (below) |

## 4. Mixing the film
`mix_film` / `python3 audio/audiolib.py mix …`: places every `kind:"line"` beat's `audio` at its `start`, normalises
dialogue to -18 LUFS, music to -25 LUFS then ducks it -8 dB under speech (≈ 14 dB under the voice while talking,
≈ 7 dB under it in gaps), renders the SFX events (`--sfx none` to skip; no `--sfx` → events derived from the
screenplay's per-beat `sfx` lists at beat start +0.15 s with the table gains — a rough preview only), sums,
masters to **-16 LUFS / -1 dBTP**, writes `out/mix.wav` (what `tools/render_all.sh` muxes). The pipeline's own mixer
`audio/mix.py` (not part of this module) writes the same file with per-speaker room reverb and ffmpeg loudnorm;
use one or the other. A full 5.65-min mix takes ~1 min.

## 5. Limitations / gotchas
- The score is generated from rules + composed progressions/motifs, verified by analysis (spectrograms, piano roll,
  levels), never by ear. Use `--roll` to see exactly what plays where; tweak `intensity`, `hits`, `phrases`.
- GM samples: the piano velocity layer ~73–105 in this SF2 is broken (≈ 20 dB quieter than vel 70, re-measured) — the
  engine caps piano velocity at 70 and gets loudness from gain instead. TinySoundFont ignores CC91 reverb (we use our
  own), and CC7/CC11 are not used.
- Melody needs gaps: a scene with wall-to-wall dialogue gets pads and pings only. A 3-note `_short` motif needs a
  silence of ≈ 1.5 s, a full motif ≈ 4–7 s; and none starts inside a cue's fades. In the example,
  s18–s19 (continuous narration) therefore has no melody — the resolved motif comes back in s20.
- Under narration the reveal (s14) is the busiest texture (celesta 3-note figures, harp, choir at low velocity): keep
  the music ducked there; lower the cue's `intensity` if the narration needs more room.
- The score is only as aligned as the timeline it was rendered with: re-render after any re-timing.
- The crowd walla and sob are synthetic voices (formant filtered): keep them low in the mix (they are designed to be).
- `place()` returns a new array when it grows the track. `load()` always returns stereo unless `stereo=False`.
