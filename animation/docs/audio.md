# Audio engine — reference for scene animators and the mixer

Files: `audio/audiolib.py` (DSP + mix), `audio/music.py` (score renderer), `audio/sfx.py` (SFX synthesiser),
`audio/sfx/*.wav` (generated SFX), `data/music_cues.example.json` (a complete score, every mood, story order).
All audio is 44.1 kHz stereo float internally; files are 16-bit PCM WAV.

```bash
python3 audio/sfx.py                                   # (re)build all 20 SFX → audio/sfx/<name>.wav   (~6 s)
python3 audio/sfx.py --list                            # names + one-line descriptions
python3 audio/music.py data/music_cues.example.json out/music_example.wav    # ~60 s for 5.6 min
python3 audio/music.py cues.json out.wav --roll out/roll.png --notes out/notes.txt   # debug: piano roll + note list
python3 audio/audiolib.py mix --music out/music.wav --sfx data/sfx_events.json --out out/mix.wav
python3 audio/audiolib.py check out/mix.wav            # peak / true peak / LUFS / DC / NaN / click score
python3 audio/audiolib.py spectro in.wav out.png [--max-hz 8000] [--seconds a:b]
```

## 1. Sound effects (`audio/sfx/<name>.wav`)

Every file peaks at -3 dBFS, has no DC, natural fades (except the two seamless loops).
**Sync point** = where the audible event sits *inside* the file. To land a hit exactly on an anchor,
subtract it: `{ at: 's08b01+0.40-0.03', name: 'cage_close' }` puts the clang at `s08b01+0.40`.
**Gain** = recommended dB for a dialogue stem at -18 LUFS (also `audiolib.SFX_GAIN`). Start there, ±4 dB to taste.

| name | dur s | loop | sync point(s) in file (s) | what it is | gain dB |
|---|---|---|---|---|---|
| alarm_bell | 3.00 | **seamless** | continuous from 0 | electric fire bell: 22 Hz striker on inharmonic gong partials 1.2–5.6 kHz, "rrrring" | -18 |
| alarm_pull | 0.60 | – | scrape 0.00, **clack 0.055**, latch 0.14 | plastic/metal pull-station lever | -6 |
| footsteps | 2.50 | – | steps at 0.08, 0.64, 1.20, 1.76 (alt. L/R) | 4 soft steps, heel + scuff | -9 |
| door_whoosh | 1.30 | – | swell peak 0.43, soft thud 1.00 | swinging door, moves L→R | -13 |
| crowd_murmur | 4.00 | – | fades in 0–0.35, out 3.4–4.0 | indistinct worried walla, 8 voices, distant | -14 |
| heartbeat | 1.30 | **seamless** | lub 0.06, dub 0.34 | one cycle (46 bpm); loop it; `rate` 1.3 ≈ 60 bpm | -12 |
| breath_shaky | 2.90 | – | inhale 0.0–1.3 (catches at 0.45, 0.85), exhale 1.45–2.85 | trembling breath | -13 |
| sob | 1.90 | – | 3 hitches 0.05/0.21/0.35, whimper 0.56–1.06, exhale 1.1–1.85 | small, soft hitched sob | -12 |
| cage_close | 2.60 | – | **clang 0.03**, rattles to 0.4, latch 0.45, ring to ~2.3 | metal gate shutting | -5 |
| lock_click | 0.32 | – | clicks 0.02, 0.058 | spring latch / padlock | -10 |
| cage_creak | 2.20 | – | swell 0.15–1.9 (peak ~0.7) | slow hinge creak (stick-slip) | -12 |
| key_turn | 0.95 | – | pin ticks 0.05–0.21, grind 0.45–0.65, **bolt 0.68** | key in, turn, clunk | -9 |
| rumble_low | 5.00 | – | rises 0–2.6, peak 2.6, fades to 5.0 | sub-bass swell (41 Hz + harmonics) | -14 |
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

## 2. Music (`audio/music.py`)

Orchestra: MuseScore_General.sf2 via tinysoundfont, rendered stem by stem, sample-accurately (notes are
scheduled in blocks between events), per-stem EQ ("felt" piano = low-passed soft layer), two reverb buses
(hall 2.6 s, "vast" 5.5 s dark), gentle glue compression, loudness-normalised (default **-18 LUFS**),
true-peak limited to -1 dBTP. Deterministic (seeded humanisation).

### Cue sheet
```json
{ "timeline": "data/timeline.json",        // for anchors (default data/timeline.json)
  "speech_from": "data/timeline.json",     // dialogue intervals = beats with kind "line" (optional, recommended)
  "speech": [[12.0, 14.5]],                // extra dialogue intervals, absolute s (optional)
  "duration": "film.end",                  // number or anchor; default = timeline duration
  "cues": [ { "start": "s14-0.6", "end": "s14b06.end+1.5", "mood": "reveal_wonder", "intensity": 0.5,
              "fade_in": 2.5, "fade_out": 2.5, "hits": [{ "t": "s14b01+0.3", "type": "swell", "len": 5 }] } ] }
```
Every time (`start`, `end`, `duration`, `hits[].t`) is **seconds or an anchor** with the `src/timeline.mjs` syntax:
`'s05b03'`, `'s05b03.end'`, `'s05b03.mid'`, `'s05b03+1.2'`, `'s05b03.end-0.4'`, `'s07'` (scene start), `'s07.end'`,
`'film.end'`. Unknown ids abort with a clear message. Re-render the score whenever the timeline changes.

| cue field | default | meaning |
|---|---|---|
| `start`, `end` | – | cue span; cues may overlap — overlapping fades are equal-power crossfades |
| `mood` | – | one of the 12 moods below |
| `intensity` | 0.4 | 0..1: level (−7 dB at 0), velocities, number of layers (strings/choir/celesta/cello join at ~0.3–0.55) |
| `key` | "D" | tonic (C, C#, Db … B; a trailing `m` is ignored — the mood sets the mode). Folded into −6…+5 semitones of D |
| `bpm` | mood | tempo override (moods are 60–72) |
| `fade_in` / `fade_out` | 1.5 / 2.0 | sine fades inside [start, end] (min 0.02 / 0.05) |
| `hits` | [] | `{t, type, len?}` — see below |
| `phrases` | mood | ordered list of phrase names to try in each dialogue gap (longest that fits wins) |
| `phrase_seq` | – | names used in order, one per placed phrase (`X_short` variants are tried automatically) |
| `phrase_stem` / `phrase_oct` | mood | instrument for the melody (piano, musicbox, celesta, cello, strings, viola, harp…) / octave shift in semitones |
| `tone` | "high" | stillness only: held `high` A5 harmonic, `low` D2 note, or `both` |

**Hits**: `swell` gentle crescendo over `len` s (default 4.5; adds a strings layer, +3 dB, intensity +0.25 for the rest of
the cue) · `sting` soft-but-sudden accent (timpani + low strings + low piano; music continues) · `drop` falls to −26 dB
in 0.35 s, no new notes until the next hit · `silence` fades to 0 in 0.2 s, nothing until the next hit (reverb rings
out) · `resolve` cadence on the tonic exactly at `t` (dominant/plagal before it; if the dialogue leaves room a motif
phrase is placed so that its last note **lands on t**), rolled tonic chord, tonic held afterwards.

**Dialogue awareness**: melodic phrases are placed only in gaps (≥ ~1.2–4.5 s, line edges padded 0.3 s before /
0.2 s after), snapped to the bar grid; under speech the moods keep to pads, low strings and very soft high piano
"pings". The bar grid is stretched ≤ ±12 % so hits land on downbeats.

### Moods (default key D)
| mood | tempo | harmony / texture | melody in gaps |
|---|---|---|---|
| tender_memory | 66 | D major ↔ Bm: felt piano broken chords, warm pad, celesta glints (I≥0.2), strings (I≥0.55) | memory theme |
| curious_unease | 62 | D minor/dorian, #11 colours: pizzicato tiptoe, pad, eerie glass 9th | fear motif (fragile) on music box |
| alarm_chaos | 72 | D pedal, b6 → Neapolitan → V: strings 8th ostinato (3+3+2), tremolo, timpani — **no melody** | none |
| void_presence | 60 | the VOID sonority: low open fifths D–A(–E/F), dark pad, bowed-glass fifth breathing, distant timpani roll | none |
| confrontation | 66 | D minor, gentle but firm: strings, composed viola line, one sustained piano note per bar | fear motif, questioning |
| sorrow | 60 | D minor lament: low strings, solo cello long tones (A-G-F-E…), sparse piano | lament / fragile motif on cello |
| stillness | 60 | almost nothing: one held tone (`tone`); resolve = a single warm low piano chord + pad | via `phrases` only |
| dread | 60 | held minor-9th / tritone over D, timpani heartbeat slowing ~66→42 bpm, low horn semitone (I≥0.4) | via `phrases` only |
| reveal_wonder | 64 | the void opens: Dmaj9 ↔ E/D (lydian), strings, choir aahs, celesta cascades, harp arpeggios | wonder (lydian motif) on celesta + harp |
| belonging | 66 | D major descending bass, warm strings, piano, cello counter-line (I≥0.42) | fear motif, hopeful |
| resolution | 63 | tonic-pedal plagal D – G/D, warm pad, half-note piano | fear motif, resolved |
| outro | 60 | solo piano, pad; after `resolve`: final chord + celesta twinkles | fear motif, resolved (ends on the tonic at the resolve hit) |

**Leitmotifs** (`PHRASES` in music.py; each has a `_short` variant): `memory` (5-3-2-3…), `fear_minor`
(b3-2-b3 · 5, hesitant), `fear_question` (…5-6, hangs on IV), `fear_hope` (major, ends on 5), `fear_resolved`
(3-2-3-5 | 4-3-2-1 over a cadential 6/4), `wonder` (lydian #4→5), `lament` (5-4-3-2-1).

Console report (stdout): per cue RMS / peak / LUFS / phrase count + whole-file health. `--cue-dir DIR` writes each cue dry.
The example sheet's loudness arc: tender ≈ -19 LUFS, alarm/curious -20…-23, void -17…-21, stillness -26,
reveal -14 (peak), belonging -15, outro -18.5 (file normalised to -18 LUFS integrated).

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
| `reverb(x, wet=0.25, dry=1.0, keep_tail=True, **ir_params, width=1.0)`, `reverb_wet(x, …)` | FFT convolution; `keep_tail` extends the output |
| `compress(x, threshold_db=-18, ratio=3, attack=0.01, release=0.15, knee_db=6, makeup_db=0, sidechain=None)` | soft-knee RMS, stereo-linked |
| `duck(music, voice, depth_db=-9, attack=0.08, release=0.5, threshold_db=-45, hold=0.25, lookahead=None, return_gain=False)` | sidechain ducking; lookahead defaults to `attack` so the music is down at the first syllable; `hold` bridges word gaps |
| `place(track, clip, at_seconds, gain_db=0, pan=0)` → track | adds in place, **grows the track; always use the return value**; negative `at` trims the head |
| `render_sfx_events(events, duration, sfx_dir=None)` | renders `data/sfx_events.json`-style events (loop/until/fade/rate/pan/gain) |
| `loudness(x)` → LUFS | ITU-R BS.1770-4 (K-weighting, 400 ms/75 %, abs -70 + rel -10 gates); matches ffmpeg ebur128 |
| `normalize_loudness(x, target_lufs=-16)`, `true_peak(x)` → dBTP, `limit(x, ceiling_db=-1, lookahead=0.005, release=0.08)`, `master(x, target_lufs=-16, ceiling_db=-1)` | look-ahead limiter with 4× oversampled peak detection (verified ≤ ceiling) |
| `analyze(x)` → dict | peak, true peak, RMS, LUFS, DC, NaN count, max sample jump, click score (>~8 on music = suspicious) |
| `spectrogram_png(x, path, max_hz=8000, width=1400, height=420, marks=[(sec,label)])` | log-frequency spectrogram + RMS/peak strip |
| `mix_film(timeline, music, sfx_events, out, voice_lufs=-18, music_lufs=-25, duck_db=-8, sfx_db=0, master_lufs=-16, ceiling_db=-1)` | full mix (below) |

## 4. Mixing the film
`mix_film` / `python3 audio/audiolib.py mix …`: places every `kind:"line"` beat's `audio` at its `start`, normalises
dialogue to -18 LUFS, music to -25 LUFS then ducks it -8 dB under speech (≈ 14 dB under the voice while talking,
≈ 7 dB under it in gaps), renders the SFX events (`--sfx none` to skip; no `--sfx` → events derived from the
screenplay's per-beat `sfx` lists at beat start +0.15 s with the table gains — a rough preview only), sums,
masters to **-16 LUFS / -1 dBTP**, writes `out/mix.wav` (what `tools/render_all.sh` muxes).

## 5. Limitations / gotchas
- The score is generated from rules + composed progressions/motifs, verified by analysis (spectrograms, piano roll,
  levels), never by ear. Use `--roll` to see exactly what plays where; tweak `intensity`, `hits`, `phrases`.
- GM samples: the piano velocity layer 73–105 in this SF2 is broken (near-silent) — the engine caps piano velocity at 70
  and gets loudness from gain instead. TinySoundFont ignores CC91 reverb (we use our own), and CC7/CC11 are not used.
- Melody needs gaps: a scene with wall-to-wall dialogue gets pads and pings only. Silent beats ≥ 2 s are where motifs appear.
- The crowd walla and sob are synthetic voices (formant filtered): keep them low in the mix (they are designed to be).
- `place()` returns a new array when it grows the track. `load()` always returns stereo unless `stereo=False`.
