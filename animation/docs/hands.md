# Hands (src/hand.mjs)

One articulated hand shared by Consciousness/Self (`HUMAN`: palm, four fingers, thumb) and Fear + the emotions
(`TOON3`: palm, three fingers, thumb). It is built in 3D and projected, so the thumb lands where anatomy puts it
for the hand's chirality (left/right) and how the wrist is rolled. One silhouette outline; overlaps between parts
are a soft darker skin tone (no hard interior lines, no outlined ovals).

## In character arm specs (drawFear / drawEmotion / drawSelf)

| field | meaning |
|---|---|
| `hand` | `'rest'` (hanging relaxed) · `'open'` · `'palm'` (open, spread) · `'wave'` · `'flat'` (fingers together) · `'drape'` (laid over a shoulder) · `'cup'` · `'claw'` · `'point'` · `'fist'` · `'grip'` (round handle/bar) · `'pinch'` (key, small object) · `'hold'` (flat object between fingers and opposed thumb) · `'edge'` (fingers hooked over an edge) — or a pose object, e.g. `blendHand('fist', 'point', k)` |
| `palmDir` | where the palm faces, `[x right, y down, z toward camera]` in the character's (unmirrored) frame. `[0,0,-1]` palm on the face/chest (back of the hand to camera) · `[0,0,1]` palm to the viewer · `[-side,0,0]` toward the body (hanging) · `[0,1,0]` palm down · `[0,-1,0]` palm up |
| `roll` | alternative to palmDir: 0 back of hand to camera, PI palm, PI/2 thumb side, -PI/2 pinky side |
| `handAng` / `handAngle` (Self) | absolute direction the fingers point (radians); otherwise the forearm direction + `wrist` |
| `curl` | 0..1 extra curl toward a fist; `spread` override; `holding` true when an object fills the grip |
| `whiten` (Fear pose) | 0..1 knuckles paling on a tight grip |

The arm's side gives the chirality automatically (the screen-left arm at facing 1 is the character's RIGHT hand; seen
from behind it is the LEFT). Self's older specs that only give `thumb: ±1` get the back- or palm-facing view that
puts the thumb on that side. Self props (`prop: 'clipboard' | 'notebook' | 'notebookCover'`) layer the hand around
the object: fingers behind a clipboard / closed book with the thumb over its front edge; for an open book being
read, the fingers come over the outer covers and the thumbs stay on the page side.

Drawing a hand directly: `drawHand(g, style, { ang, shape, palmDir | roll, chir, only: ['thumb'] ... })` at the wrist.

Shaking: `engine.smoothShake(t, trem, seed)` — slow, breathing/sob-paced, low amplitude (characters use it for
`tremble`; scenes that overlay things on Fear use `fearShake`, `fearBodySpace`, `fearHeadSpace`, `drawFearFrontArms`).

Tears: `face.drawTear` — one translucent, slightly blue drop with its own short trail that fades out as a whole.
`tearL`/`tearR` = progress of one tear; `stream` = a sustained cry as single alternating tears.
