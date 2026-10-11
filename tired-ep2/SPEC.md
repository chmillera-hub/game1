# Production Bible — "TIREDNESS — Episode 2: Lights Out"

A portrait (9:16) 2D cartoon, **~4:30, HARD MAX 4:50**. It picks up exactly where
Episode 1 ended.

**Where Episode 1 ended.** Tiredness, bitten by a HushCorp "carrier" critter, now
has strength and a strange new sense. He followed the escaped creature through
the sewers into an enormous secret shaft, full of glowing containment pods
holding sleeping creatures like it. "...Is this your family?" It nodded.

**Episode 2 in one breath:**
1. On the catwalk Tiredness finds the creature's empty pod. Its nameplate
   reads **CURIOSITY**, and the other plates read JOY, COURAGE, CALM, WONDER…:
   HushCorp locks up feelings.
2. The Boss, watching on a monitor, says "Right on time" and cuts the lights.
3. In total darkness Curiosity pulls Tiredness's hood over his eyes. He
   discovers his new sense works when his eyes are CLOSED: "Finally. A
   superpower I'm actually good at."
4. Guards with flashlights search. Curiosity trolls one of them, waving at the
   back of his head with an evil little grin, then melts into a shadow to hide.
5. In a quiet corridor Tiredness gives up ("they're not my problem").
   Curiosity, hurt, walks away alone. Tiredness sits with that, sighs, and
   follows.
6. Embarrassment, down here on HushCorp business, runs into them. He looks at
   his red-blinking recorder, switches it off ("My pocket calculator just
   stopped working"), and gives them his keycard.
7. In the control room the Boss is already waiting. She knew the moment the
   bite happened. She offers him the one thing he wants: go home, sleep, never
   be bothered again. He is tempted, then: "But for once... I'm not tired."
   His eyes open fully.
8. He smashes the case and hauls the MASTER RELEASE lever with his new
   strength. The Boss triggers lockdown and every pod re-seals except one tiny
   pod: JOY, a baby creature. Embarrassment holds a hatch open and they escape.
   The Boss watches and says "Let them run."
9. Dawn, his bedroom. He flops face-down: "Worst. Day. Ever." Curiosity and
   baby Joy curl up on his back. A tiny smile. He sleeps. End card.

Tone: deadpan comedy, wonder, a real emotional turn in the middle, and a warm
ending. HushCorp stays mysterious: it knows things it shouldn't, and the Boss
lets them go on purpose.

## 0. LESSONS FROM EPISODE 1 — these are hard rules now
1. **Never rushed.** One idea at a time. Hold reactions; give every line air
   before and after. A muted viewer must always know what is happening and
   why. If a beat needs more time, take it (within your allowance). Never
   cram two actions into one beat.
2. **Physical cause and effect must be visible.** Characters never just
   appear in odd places. Show the hit, then the fall, then the result.
3. **Clear, unambiguous gestures.** A big shrug, a nod, pointing (index
   finger with thumb visible, aimed sideways or down), a small bent-elbow
   wave. Avoid vague hand rolling.
   * Never a raised straight arm with a flat palm (salute-like).
   * Never a lone raised middle finger.
4. **No butt emphasis, ever.**
   * No butt-up crawling, no climbing seen from behind, no bent-over rear
     views, no tight pants on the seat.
   * Sneaking is an upright crouch.
   * Stage people from the front or in 3/4.
5. **No hand/arm z-order flicker.**
   * Check consecutive frames wherever hands cross the body or each other.
   * A hand must never pop in front of / behind the other hand or the body
     from one frame to the next.
6. **Mysterious things stay mysterious.**
   * Shadows of creatures are amorphous, not cute silhouettes.
   * HushCorp's knowledge is unexplained.
7. **Audible means audible.** Shouts and important off-screen lines are
   clear and loud enough; muffled only when the joke needs it.
8. **Shakes and impacts are long enough to register**: ≥ 0.6 s with a clear
   build and settle, plus things in the room reacting.
9. Characters don't say each other's names unless a real person would.

## 1. Hard rules (carried over)
* Everything procedural (Python + cairocffi).
* Deliverable < 15 MB at 720x1280, 24 fps, H.264 + AAC. Flat colours,
  mostly static backgrounds, ≤ ~20 small moving particles, no full-screen
  noise, no constant shake, flashes ≤ 3 frames, no strobing.
* **Frame 0 of s01 is bright and readable**: the social preview. No black
  first frame.
* No gore. Cartoon violence only (a fist through a glass case, a bonk on a
  pipe).
* Deterministic (no unseeded randomness).

## 2. Tech contract
Same engine as Episode 1 (read engine/core.py, engine/timeline.py).
* Logical canvas 1080x1920; safe zones x 60..930, y 120..1330. Captions are
  drawn by the engine at baseline y≈1450 (band ≈1330–1560).
* Scene modules: `scenes/<module>.py` with `render(ctx, t, info)`, optional
  `SFX(info)`, `CAPTION_Y`, `caption_y(t, info)`.
* Timing always comes from `info.cue(...)` / `info.line(id)`. Never hard-code
  dialogue times.
* Speakers: `tired`, `embar`, `boss`, `guard`, `guard2`.
* Helpers: `core.camera`, `core.cached`, `core.cache_steps`, `state_at`,
  `tween`, `seg`, easing; previews via `build.py sheet/still/scene`.

## 3. Cast (rigs from Episode 1, extended for Episode 2)
* **Tiredness** (`human.draw_person(..., "tired")`): heavy lids (~45% closed), eye bags, navy
  hoodie (now with a `hood` that can be pulled up over his eyes), bandaged
  right forearm, two band-aids and smudges (outfit "sewer") for s01–s07, and
  `power` teal irises.
  * With eyes CLOSED and sensing, a faint teal glow shows along his lash line.
  * His lids open fully ONLY at "I'm not tired" in s06. That is the payoff of
    the episode; protect it.
* **Curiosity** (`creatures.draw_specimen`, form=1): the sleek indigo creature with
  fin ears, a long tail, a teal rim and HUGE teal eyes.
  * Personality: loyal, curious, a little sassy (eye-rolls), and a troll (an
    evil little grin and a wave behind a guard's back). It can melt into a
    flat shadow puddle to hide (`pose="puddle"`).
  * Name tag CURIOSITY when it is named in s01.
* **Baby Joy** (`creatures.draw_specimen(..., baby=True)`): a chubby, big-headed,
  tiny-eared baby of the same species. Giggly, wobbly. It appears in s07–s08.
* **Embarrassment**: lanky, glasses, lab coat, blush/sweat system, carrying a
  flashlight, his keycard and the recorder (red LED) in his chest pocket.
  * This episode he is calmer and braver at the key moment. His voice slows
    when he is sincere.
* **The Boss**: still, cold, all-knowing. She sits in a tall chair in the dark
  control room, lit by monitors. Her smallest moves are her biggest
  reactions.
* **Guards** (guard rig): two of them in s03 with flashlights. One is gruff;
  the other is scared of the dark.

## 4. Places (sets from Episode 1, extended)
* **shaft / catwalk:** pods with nameplates; `power` 0..1 for lights dying in
  a cascade.
* **shaft_lower:** pipes, crates, stairs; dark when power=0.
* **service_tunnel:** a dim concrete HushCorp corridor with emergency lamps
  and a keycard door.
* **control_room:** a dark room with a wall of monitors, the Boss's tall chair,
  the glass-cased MASTER RELEASE lever, a LOCKDOWN button and a side hatch.
* **bedroom at dawn.**

Darkness is drawn as "almost black but readable". The **sense** reveals
the world as teal-tinted bands inside expanding ripple rings (fx).

## 5. Audio
Voices are slower than Episode 1: tired 0.9×, embar 1.0×, boss 0.9×.
Music per scene:

| Scene | Cue |
|---|---|
| s01 | bond |
| s02 | ominous with a warm turn |
| s03 | sneaky |
| s04 | lonely (new) |
| s05 | awkward |
| s06 | lullaby (new: an eerie music-box temptation) |
| s07 | chaos |
| s08 | chill (the lo-fi callback to Episode 1's opening) |

## 6. Files
* People: `engine/human.py` (API_human.md).
* Creatures: `engine/creatures.py` (API_creatures.md).
* Sets and props: `engine/sets.py`, `engine/props.py` (API_sets.md).
* Effects: `engine/fx.py` (API_fx.md).
* Audio: `audio/*` (API_audio.md).
* DIRECTION.md: shot-by-shot direction.
