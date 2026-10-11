# Scene animation guide

A scene is one file `src/scenes/<id>_<slug>.mjs`:

```js
import { W, H, clamp, lerp, ease, kf, env, noise1, fbm, autoBlink, blinkAt, applyCamera, drift, vignette } from '../engine.mjs';
import { EXPR, makeExpr, withSpeech } from '../face.mjs';
import { drawFear } from '../chars/fear.mjs';
// ... other modules (read docs/*.md for their APIs)

export const id = 's07';
// Sound effects owned by this scene (times are anchors; see src/timeline.mjs). gain in dB.
export const sfx = [
  { at: 's07b02+0.35', name: 'alarm_pull', gain: -4 },
  { at: 's07b02+0.5', name: 'alarm_bell', until: 's07b04.end', gain: -16, loop: true },
];

export function render(g, t, S) {
  // 1. camera (world coords of the chosen view), 2. set, 3. characters back-to-front, 4. foreground, 5. light overlays
}
```

`t` is ABSOLUTE film time. `S` is the scene helper (see `src/timeline.mjs`): `S.T(anchor)`, `S.k(t, keys)`,
`S.lip(speaker, t)`, `S.talking(speaker, t)`, `S.start/S.end`. ALWAYS key timing to beat anchors
(`'s07b03'`, `'s07b03.end-0.5'`, `'s07b03+1.2'`) — never hard-code absolute seconds: line lengths may change.
Scenes must render sensibly for t slightly before `S.start` and after `S.end` (dissolves overlap ~0.9 s): clamp/hold.

## Acting principles (the creator's #1 priority: faces, eyes, lids, brows, mouths, bodies — with nuance)
1. **Every character on screen is alive** every frame: breathing (built in), auto-blinks (built in), tiny
   gaze shifts (`lookX/lookY` drift with `fbm(t*0.4, seed)*0.08`), weight shifts. Never a frozen pose —
   except THE VOID, whose total stillness is its character (only its rim shimmer and the faintest hem drift).
2. **Thought precedes action**: eyes move first (≈0.15–0.3 s), then head, then body. Brows/lids change
   BEFORE the mouth speaks. Anticipate big moves with a small opposite move.
3. **Listening is acting**: when one character speaks, the listener reacts in beats: a blink at a key word,
   a brow lift, swallowing (small `headDY` dip + `pressed` lips), eyes dropping to think, then returning.
   Key a reaction 0.2–0.6 s AFTER the meaningful word lands (use `S.T('s07b03+1.4')` with the line's word
   timings in data/lines.json if you need precision).
4. **Blinks carry meaning**: add deliberate `blinkAt(t, S.T(...))` on emotional shifts (realisation, resolve,
   holding back tears = slow blink `blinkAt(t, at, 0.4)`). Fear blinks more when scared (tremble raises its rate).
5. **Eyelids & brows are the emotion**: worry = `browIn` up + slight `lidTilt`+; resolve = `browIn` slightly
   negative + `pressed`; held-back tears = `holdingBackTears` + slow `tears` welling + `tremble`; wonder =
   `lidU` negative, pupils large, `sparkle`. Use `EXPR` presets as starting points and `S.k()` to blend
   between them over 0.3–1.0 s (`S.k(t, [['s07b02', EXPR.worried], ['s07b02+0.6', EXPR.scared]])`).
6. **Mouth**: speaking characters use `withSpeech(expr, S.lip('FEAR', t))` — the emotional shape (smile,
   frown, tremble) persists under the speech. Inner-voice lines have NO mouth movement (maybe lips pressed).
7. **Tears**: well (`tears` 0→1 over ≥1 s), then a drop (`tearL` 0→1 over ~1.6 s), streams (`stream`) only
   when really crying. Wiping = arm preset `wipeEye` + `tears` reducing.
8. **Bodies**: posture tells the story (Fear hunched/crouched when afraid, slowly straightening as trust
   grows). Use `lean`, `crouch`, `headTilt`, `headDY`, `tremble` (decreasing over the film), arm presets.
9. **Timing**: hold moments. The creator wants slowness. Big emotional beats deserve 1.5–3 s of nearly still,
   readable faces. Ease everything (`sine`/`cubic`), no linear moves.

## Camera grammar (portrait 720x1280)
- Wide/establishing: whole view; Medium: characters waist-up (~zoom 1.4–2); Close-up: face fills ~40–60%
  of width; Extreme close-up: eyes. Low angle = Void looming (camera y lower, characters higher).
- Slow push-ins on emotional beats (zoom +5–12% over the beat). Gentle `drift(t)` for life (amp 2–4 px).
- Over-the-shoulder for conversation; cut on looks (eyeline match: if Fear looks up-right, next shot shows
  what it sees from its direction).
- Keep important faces in the middle 80% of the frame width and away from the bottom 15% (social UI overlays).
- Avoid fast full-frame motion (compression): pans slower than ~60 px/s at zoom 1.

## Light
- Alarm: `drawAlarmLight` (soft red). The Void's area: darker; cosmos reveal lights faces softly
  (`drawVoidGlow`, a soft violet/teal rim on Fear's face side — e.g. draw a gradient with 'screen'/'lighter'
  composite at low alpha).
- Finish with `vignette(g, 0.3–0.5)`.

## Checking your work
- `node src/render.mjs --sheet s07 --n 16 --out out/sheet_s07.png` → LOOK at it. Use `--times a,b,c` to
  inspect key moments (e.g. every 0.25 s around a reaction). Check faces read at phone size.
- Timing per frame: the sheet run prints errors for exceptions; keep frames < 40 ms.
