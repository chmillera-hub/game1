# The Void Has a Sense of Humor — 3D animated short

A portrait (9:16, **720×1280, 24 fps**) **3D** animated short, about **5:16**, with voice acting, narration, an
original orchestral score, sound effects and burned-in subtitles. It is in a luminous "inside the mind" style
with all-original characters, and was generated entirely in code from the creator's story. It is a companion
piece to *The Void and My Fear*: the bonus scene takes place during that film's cage scene.

**Deliverables**
- `The_Void_Has_a_Sense_of_Humor.mp4`: H.264 High + AAC 64 kbps, BT.709, faststart, captions burned in. It is
  **14.54 MB** and runs **5:16** (video at 297 kbps). This is the one to post anywhere.
- `The_Void_Has_a_Sense_of_Humor_hevc.mp4`: the same film as HEVC (hvc1), **14.58 MB**. It has noticeably
  cleaner gradients and dark scenes, and plays on iPhone, recent Android and most browsers.
- `The_Void_Has_a_Sense_of_Humor.srt`: captions as a sidecar file.
- `thumbnail.jpg`: frame 0 with the title. The film starts on a finished image, so social previews aren't black.

## The film

**Part One (golden dusk at the Edge of the Mind).**
1. A crying Twitter user runs from the Void.
2. Jesus appears "now", walks up, puts his arm around the Void and whispers a joke. We never hear it.
3. The Void laughs maniacally and coughs up stars and little galaxies.
4. Jesus delivers the line "The void's got a pretty good sense of humor. Tee-hee."
5. The user answers "What the actual [bleep]?!"
6. The Void whispers back while side-eyeing the user, crosses its arms and scowls. "Do you have a moment?"
7. The user says "Hell no", and the Void rolls its eyes, huffs, turns its back and sulks.
8. Jesus makes the awkward clenched-teeth face, puts his hand on the Void's shoulder and gets a gentle smile back.
9. Jesus kneels and invites the user to talk about their emotions. For a second the user feels seen, then the
   walls go back up and they storm off and block him.
10. Jesus shrugs, the Void pats his shoulder with a sad smile, and the two walk into the sunset telling dumb
    jokes. On a far hill, the user's thumb hovers over "Unblock".

**Bonus (the back of my mind).**
1. The Void opens Fear's time-out cage.
2. The Depression Magician lurks behind it, licking its lips.
3. The Void spots the Magician in the corner of its eye and, without making a fuss, donkey-kicks it into the
   buckets with its fat leg.
4. Fear asks "What's that noise?" and the Void shrugs innocently.
5. The universe fills the room: galaxies and nebulae, just so the Void can have a moment with my fear.

## How it was made

| Stage | Files |
|---|---|
| Brief, story, cast, locations, look | `BIBLE.md` |
| Screenplay (22 scenes, 160 beats). Three director drafts were judged by a three-judge panel, synthesized, critiqued and fixed | `data/screenplay.json`, `data/drafts/`, `data/SCREENPLAY_FORMAT.md` |
| Staging: world map, marks, per-beat cameras, continuity table | `docs/STAGING.md`, `web/src/scenes/marks.js` |
| Voices: Kokoro TTS, with a 50/50 narrator blend matching the earlier film. The Void's whispers are "whisperized" so they can't be understood | `audio/tts.py`, `audio/vocals.py` |
| Timeline (every beat's absolute time) and lip-sync (Whisper word timing → phonemes → mouth shapes) | `tools/build_timeline.py`, `audio/lipsync.py` |
| Score with leitmotifs, word painting (high notes on `^hopeful` words, low notes on `~heavy` ones) and comic hits; SFX; mix at -14 LUFS | `audio/music.py`, `audio/sfx.py`, `audio/mix.py`, `docs/AUDIO.md` |
| 3D engine: three.js r170 rendered headless (SwiftShader); face rig with 3D eyes, real eyelids, swept brows and painted mouths; IK limbs and hands; glow materials; particles; post | `web/src/core/`, `docs/ENGINE.md` |
| Characters (each built, reviewed by an art director, then fixed) | `web/src/chars/`, `docs/chars/` |
| Sets: the Edge dreamscape, the back room with its cage and janitor corner, the cosmos | `web/src/sets/`, `docs/sets/` |
| One module per scene, timed to beats (each animated, director-reviewed and fixed), plus a whole-film review covering continuity, acting and technical lenses | `web/src/scenes/sNN.js`, `data/cues/sNN.json` |
| Captions and titles (Nunito / Fredoka, tinted per speaker, kept out of the phone-UI zones) | `tools/build_subtitles.py` |
| Rendering and encoding | `tools/render.js`, `tools/render_all.sh`, `tools/encode.sh` |

Everything is anchored to beat references (for example `T('s13b08.end-0.3')`). Changing a line or a pause and
rebuilding re-times the picture, lip-sync, music and captions automatically.

## Rebuild

Requirements:
- Node 22 with Playwright's Chromium (`npm install`)
- Python 3 with `kokoro-onnx soundfile scipy faster-whisper pyloudnorm` and `tinysoundfont` (install it with
  `--no-deps`)
- ffmpeg with libass
- In `models/`:
  - `kokoro-v1.0.onnx` and `voices-v1.0.bin` (kokoro-onnx release `model-files-v1.0`)
  - `whisper-base.en/` (Systran/faster-whisper-base.en)
  - `FluidR3_GM.sf2` (the `fluid-soundfont-gm` package)

```bash
python3 audio/tts.py && python3 audio/vocals.py        # voices
python3 tools/build_timeline.py && python3 audio/lipsync.py
tools/build_audio.sh                                    # SFX events, score, mix -> out/mix.wav
python3 tools/build_subtitles.py                        # out/subs.ass + .srt
tools/render_all.sh 3                                   # out/frames/*.jpg (about 1 s/frame per worker on 4 cores)
tools/encode.sh 14.6 && tools/encode.sh 14.6 hevc       # size-targeted 2-pass encodes
```

You can preview without a full render:
- `node tools/render.js sheet --from 60 --to 90 --n 16` builds a contact sheet.
- `node tools/render.js stills --t 12.5,40` renders single frames.
- `python3 tools/review_sheets.py` builds review sheets per scene and across every cut.
- `node tools/render.js sheet --lab void` shows a character lab.

## Common changes

- **A line or a pause:** edit `data/screenplay.json` and re-run TTS for those beats
  (`python3 audio/tts.py data/screenplay.json s13b08`). Then rebuild the timeline, lip-sync, audio, subtitles
  and the render.
- **High and low word notes:** add `^word` or `~word` in the line text.
- **Voices:** edit the `VOICES` table in `audio/tts.py` (Kokoro voice blends, speed and pitch).
- **Music mood per cue:** edit `data/music_plan.json` or `data/music_overrides.json`.
- **A facial expression or gesture:** edit the scene's module in `web/src/scenes/sNN.js`. Face parameters are
  documented in `docs/ENGINE.md` (presets such as `X('awkward')`, `X('sadSmile', {mOpen: 0.1})`).
- **File size:** run `tools/encode.sh <MB>`.

## Notes and choices worth knowing

- **The Void has eyes now.** In *The Void and My Fear* its face was pure darkness. This story needs side-eye,
  eye-rolls, scowls and smiles, so it now has two soft starlight eyes, nebula brows and a crescent mouth that
  opens onto deeper cosmos. It still never speaks words.
- **Fear** keeps the earlier film's design: a small lavender bean with a mustard scarf.
- **Original designs:** all characters are original. No logos appear; the phone app is a generic feed with a
  plain "Block" dialog.
- **The bleep:** "What the actual f***" is bleeped in the audio and written `f***` in the captions.
- **"...How rude."** The script had the Magician's last word as "...Rude.", but as a single word the voice read
  as "Road", so it was changed to "...How rude.".
- **Untested by ear.** The audio could not be listened to during production; it was checked with ASR and level
  meters. "Tee-hee" is generated from explicit phonemes, because the ASR can't transcribe it.

## Credits and licenses

- **Voices:** Kokoro-82M (Apache-2.0) via kokoro-onnx.
- **Lip-sync alignment:** faster-whisper base.en (MIT).
- **Music:** original, rendered with the FluidR3 GM soundfont (MIT).
- **Sound effects:** synthesized in code.
- **Fonts:** Nunito and Fredoka (SIL Open Font License).
- **Engine:** three.js (MIT).
- **Story:** the creator.
