# "One": John 10:25–39 and John 17:20–26 (portrait animated short)

A realistic-3D, 9:16 animated short with voice acting, an original score, sound design and
burned-in subtitles. It was made entirely with open-source tools on a CPU-only machine.

| File | What it is |
|---|---|
| `one_john10_john17.mp4` | Main delivery: H.264 + AAC, 540×960, 24 fps, under 15 MB. Plays everywhere. |
| `one_john10_john17_hevc.mp4` | Smaller HEVC version (needs a player that supports H.265). |
| `one_john10_john17.srt` | Subtitles as a separate file (they are also burned into the videos). |
| `pipeline/` | Every script used to make the film. |

## Story

1. **Solomon's Colonnade, winter.** The religious leaders press Jesus. He answers with the shepherd
   image ("no one will snatch them out of my hand") and "I and the Father are one". Stones come up.
   He reasons with them from Psalm 82. A young Pharisee's stone slips from his hand, and they try to
   seize Jesus but he escapes. Afterward the young Pharisee asks the elder: "Have you ever seen a
   man born blind... open his eyes?"
2. **The street.** Peter and John catch up, frightened. "Do not be afraid, John."
3. **The upper room, the last night.** Jesus prays the John 17 prayer while his friends listen.
4. **Two thousand years later.** A woman reads that prayer alone at night ("He prayed... for me?").
   She calls the sister she hurt at their father's funeral. Their reconciliation plays against the
   prayer for unity, and the film ends on a hug at an open door and the line "...that I myself may
   be in them."

Scripture lines follow the NIV text you supplied. Narration and the modern scenes are dramatization.

## Changing things

Everything is driven by small data files. Edit one, then re-run the steps after it.

- **Dialogue, emotions, pauses:** `pipeline/screenplay.py`. Each line has a speaker, text, emotion
  and voice intensity (`ex`).
- **Voices:** `pipeline/tts_generate.py`. Kokoro reference voices are cloned by Chatterbox for an
  expressive delivery, and every take is checked with Whisper. Run `timeline.py` afterwards.
- **Shots, camera, acting:** `pipeline/shots.py`. Each shot lists its set, cast, camera and timed
  actions (`emo`, `look`, `nod`, `gest` such as `chest`, `palms_open`, `point`, `grab`,
  `phone_ear`, `knuckles_mouth`, and others), anchored to lines or words.
- **Character looks:** `pipeline/blender/charspecs.py` controls body shape, skin, eyes, hair,
  beards and clothing. `charbuild.py` builds them.
- **Music:** `pipeline/score.py` composes the score against the dialogue. `HIGH`/`LOW` set which
  words get the high (hopeful) or low (heavy) accents.
- **Mix and sound design:** `pipeline/mix.py`.
- **Final assembly, grading, subtitles, compression:** `pipeline/compose.py`.

Order: `tts_generate.py` → `timeline.py` → `score.py` → `mix.py` → `render_all.py` (Blender)
→ `compose.py`.

## How it was made

- **Characters:** Blender 4.5 with the MPFB (MakeHuman) add-on. Every character has 52 ARKit
  facial shape keys and 22 visemes. Strand beards, procedural robes, shawls and head coverings come
  from `charbuild.py`.
- **Performance:** `blender/perform.py` layers emotion blends, phoneme lip sync (from Whisper word
  timings and espeak phonemes), random blinks, saccades, eyelid-follow, speech-driven brow raises
  and idle micro-motion. `gestures.py` handles IK hand gestures, breathing, leaning and walking.
- **Sets:** procedural Blender sets in `pipeline/sets/` for the colonnade, upper room, apartment,
  kitchen, hallway, hillside with sheep, cosmos, night city and scroll.
- **Rendering:** Cycles on CPU at 432×768, upscaled and graded to 540×960.
- **Audio:** Chatterbox TTS (MIT), with Kokoro-82M (Apache-2.0) for the reference voices and the
  very short lines. The score is a MIDI file rendered with FluidSynth and the FluidR3 GM soundfont
  (MIT). Ambience and effects are synthesized. The mix is loudness-normalized to −14 LUFS.

## Licenses of third-party assets

The MakeHuman/MPFB system assets, skins, poses and face-unit packs are CC0. Blender and MPFB are
GPL tools (their output is yours). The FluidR3 GM soundfont is MIT. Kokoro voices are Apache-2.0,
and Chatterbox is MIT (its audio carries Resemble's inaudible watermark). No copyrighted
characters or logos appear.
