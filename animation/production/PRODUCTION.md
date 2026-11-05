# Production notes: *A Table Instead of a Palace*

## Brief as recorded

The production template's brief fields were left blank, so the values below come from your earlier written request or are choices I made. Each one is marked with its source.

| Field | Value | Source |
|---|---|---|
| Title | A Table Instead of a Palace | Chosen. It comes from the script's closing line. |
| Story | A friend answers Noa's theory that David, Solomon and Jesus form one arc. David succeeded at his society's program, violence included. Solomon inherited the rewards and found them empty and lonely (Ecclesiastes 4). Jesus answers with nonviolent love and shared life. | Your script |
| Main characters | Noa (the theorist), Teo (the friend who answers), Ami (the third friend at the end), plus the biblical cast | Chosen to give the script a conversation and narrator, which you asked for |
| Setting | A night kitchen in the present day, with flashbacks to ancient Israel and Judea | Chosen |
| Visual style | Flat 2D vector style with big-headed characters, so faces carry the emotion | Chosen, because you asked for the effort to go into faces, body language and dialogue |
| Emotional arc | Curiosity, then a correction, then a heavy middle (violence and inherited damage), then emptiness (Ecclesiastes), then recognition ("I know that floor"), then warmth and belonging (a knock at the door, three at the table) | Chosen |
| Duration | 399.21 s (9,581 frames). The length comes from the dialogue, since you said there was no limit. | Your request |
| Output | Portrait 9:16, 720 × 1280, 24 fps, H.264 + AAC, under 15 MB | Your request (portrait, mobile, under 15 MB). This replaces the template's 16:9 default. |
| Production mode | Code-only visuals: every image is drawn by the project code, with no image or video generation, stock imagery or tracing | Chosen |
| Audio | Synthesized voices (TTS), a procedurally generated score and procedural sound effects, with burned-in subtitles | Your request |
| Budget | No explicit limit. A full render plus encode takes about 6 minutes on 4 CPU cores. | — |

## Visual rules

- **Shapes and rendering:** characters and sets are built from flat fills, simple gradients and soft radial glows. There are no textures and no film grain, which also keeps compression efficient.
- **Character proportions:** heads are large, about 2.8–3.1 heads tall overall (head radius `u`, feet at about 4.9u below the head centre). Faces are the main acting surface: independent brows, upper and lower lids, gaze, a mouth shape driven by the voice audio, and tears.
- **Light is motivated per location:**
  - Kitchen: warm pendant lamp as the key light from top centre, cool moonlit window as fill.
  - Fire scenes: orange light from below.
  - Night exteriors: blue soft-light grade.
  - Light is applied as a full-frame grade over both characters and background, so subject and environment always share the same light.
- **Palette per act:**
  - David: ochre, crimson and gold, shifting to fire orange and red for the violence.
  - Solomon: royal blue and gold, desaturating to dusk grey.
  - Jesus: warm daylight greens, moonlit blue, and firelight.
  - The kitchen always returns to the same warm/cool balance so the frame story feels like home.
- **Screen direction in the kitchen:** Noa is always frame-left and Teo frame-right. The door is frame-right, so Ami enters from the right. The final three-shot keeps that order, with Ami in the middle.
- **Subtitles:** sit in a lower safe band (y ≈ 980–1120) above where phone apps put their buttons. Speaker tags are color-coded, and narration is in italics.

## Locked character designs

The designs are defined once, in `source/core.js` (the `CH` table), and every shot uses that same definition. For each character it fixes the skin and shadow tones, hair style and color, iris color, costume and accent colors, beard, glasses, headwear and accessories.

The two-pass reference images are in `cast_lineup.jpg` (all 19 characters) and `expression_sheet.jpg` (14 expressions on 5 principals).

Each character's identifying features:
- **Noa:** curly dark hair, mustard sweater, gold earrings.
- **Teo:** gray hair and trimmed beard, glasses, green cardigan.
- **Ami:** red beanie, teal jacket.
- **David:** red-auburn curly hair and ruddy cheeks. He wears a tan tunic when young, a crimson robe and gold crown as king, and has a white beard and purple robe when old.
- **Solomon:** royal-blue robe with gold trim and a crown. He has a black beard as king and a long gray beard when old.
- **Jesus:** long brown hair and beard, off-white robe, blue sash and mantle.
- **Peter:** gray curly hair and beard, brown robe.

## Animation approximations

These are approximations, not simulations:

- **Lip sync:** from the loudness of each voice line, measured every frame, which sets how far the mouth opens. The brightness of the sound (spectral centroid) sets mouth width (wide "ee" versus round "oo"). This isn't phoneme-accurate.
- **Blinks and life:** blinks, small eye movements, head sway and breathing are seeded, deterministic noise. Every render is identical.
- **Expressions:** keyframed per dialogue line, and blended with 0.45 s smoothstep transitions.
- **Arms:** a two-bone pose system with posed shoulder and elbow angles, not a physics simulation. Held props are drawn at the computed hand position, so hands stay attached to what they hold.
- **Effects:** fire, smoke, vapor, wind streaks, rain, petals and snow are procedural particles driven only by time, so there is no simulation state that depends on earlier frames. Particles fade in and out at their life-cycle ends rather than popping.
- **Camera moves:** pushes and pulls are linear or eased zooms around a fixed point, and each is listed in the shot list with its purpose. Most dialogue shots hold a static camera.
- **Light response:** done as a per-shot color grade (multiply or soft-light) plus additive glows. There are no cast shadows apart from simple contact ellipses.

## Quality criteria and how each was checked

- **Story clarity.** Every spoken claim has a matching on-screen action or image, as listed per shot in `SHOT_LIST.md`. This was checked by reviewing a frame from every shot (`contact_sheet_*.jpg`).
- **Character consistency.** One shared definition is used throughout, with no per-shot redrawing. This was checked on the reference sheets and contact sheets.
- **Composition.** The subject's face must not sit under the subtitle band. This was checked on the contact sheets; one failure, the campfire shot, was found and fixed.
- **Motion.**
  - There must be no flash cuts. Shot lengths were checked against the frame-by-frame shot log: two flash cuts (2 and 12 frames) were found and removed. The shortest remaining shots are the intended one-word montage cuts (17–25 frames).
  - Looping effects must not pop. Four defects were found and fixed: petals, smoke, the walking procession and the stone-pushing loop.
  - Props must not teleport. The sword popping out of David's hand in the Abigail scene was fixed.
  - Frame strips of lip-sync, the dance peak and a crossfade were inspected.
- **Continuity.** The kitchen screen direction and lighting stay fixed, and the costume for each age of each character comes from a single definition.
- **Sound.**
  - Sound effects must land on the visible action. Three were misaligned and are now tied to the frame of the action.
  - Loudness and true peak must hit the target (see `EXPORT.md`).
  - Voice licenses must allow redistribution (see `AUDIO.md`). The cast was changed for this reason.
- **Delivery.** Exact frame count, resolution and frame rate, no black or frozen segments, no decode errors, file size under 15 MB, and a bright first frame. These are checked automatically by `source/checks.sh`.
