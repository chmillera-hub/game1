# Soundtrack

All score and sound design is procedural, written for this film. It uses no samples and copies no existing music.

```
python3 -I audio/score.py     # ~25 s  -> build/audio/work/{bed,song,cues,amb,events}.npy
python3 -I audio/mix.py       # ~45 s  -> build/audio/{voice,music,sfx,mix}.wav + work/mix_report.json
python3 -I audio/analyze.py   # PNG spectrogram/level plots -> build/audio/plots/ (optional: start end)
```

Outputs are 48 kHz mono 16-bit, exactly `timeline.duration` long. The stems hold the ducked, gain-matched layers as they sit in the mix, so voice + music + sfx = mix. `music` = bed + song + cues, and `sfx` = amb + events.

## score.py
- **Moods**: each mood renders into its own bus and is normalised to a target loudness (`MOOD_LEVEL`). The buses are then summed with 2.5 s raised-cosine crossfades.
  - bleak: low D drones, a wind-like breath, and a discordant 146.8/148.1 Hz beating hum.
  - irony: a faint, hollow open C major chord.
  - dread: low cluster swells over a D1 pedal.
  - song: a soft C pedal plus a sour high sine.
  - drone: a numb G drone.
  - urgent: an accelerating pulse climbing chromatically, with a rising filtered minor-2nd line.
  - drip: water-like plucks.
  - fragile: an original A minor music-box motif that winds down slightly with each phrase.
  - storm: a wide dark A drone with low swells.
  - false_hope: a saccharine F add9 pad, plus bells with a detuned partial and a flat A5.
  - clinical: thin cool sines.
  - cycle: an Am-F-Dm-E ostinato.
  - resigned: a slow descending low line, then a long fade.
- **Song**: the timeline notes are sung by a unison choir of 6 detuned humming voices. Each voice is a harmonic source with scoops, delayed vibrato and an "mmm" to "ooo" (to "oh" when loud) formant morph, with child-raised formants.
  - The loud passage gets more level and openness.
  - The drone passage is lower, flatter, closed and low-passed.
  - At `songEnd` there is a 12 ms hard cut, and the room tail dies within 0.35 s. Bed, song, cues, events, engine and hum are all zeroed until the urgent cue, so only the thinned wind and the soft "cease" hit (placed exactly on `songEnd`) remain.
- **Cues**: high = bell (sour on ironic/false-hope words), low = deep note with sub, swell = 2.6 s filtered rise ending on the word, light = pluck/tine, hit = felt impact.
- **SFX**:
  - Part I: wind (0 s to Part II), discordant hum (0 s to the cut), engine and road (engine cue to the cut), wheel ticks, seat creak, gears, screech, cable snap, whoosh, rumble.
  - Part II: continuous drips, skitters (plus 6 faint extra ones in pauses), a squeak, and rain (steady, then a heavy torrent roar, then a splash, dissolving as the sun appears). The rain returns briefly in the cycle and quietly at the end.
  - Also in Part II: a shimmer cascade and a pill pop.

## mix.py
- **Narrator**:
  - Rubberband −1 semitone with formants preserved, then high-pass, low shelf +1.8 dB at 170 Hz, a slight cut at 330 Hz, +1 dB presence and a sibilance shelf.
  - Gentle 2:1 compression, then partial per-beat level normalisation and a 7.5% small dark room.
  - Peak control sits 13 dB above the voice's integrated level.
- **Bus levels**: each bus is set relative to the voice (`REL`) and ducked while the narrator speaks (`DUCK`). A smoothed speech-first safety stage then keeps the background at least 11 LU under every active 400 ms speech block.
- **Final level**: gain to −16 LUFS, then a 4x-oversampled lookahead limiter at −2 dBTP. The report is written to `build/audio/work/mix_report.json`.
