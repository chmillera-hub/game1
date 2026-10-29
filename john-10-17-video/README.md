# John 10 & 17 — "I and the Father Are One"

A 3D scripture video in the style of the Psalm 22 reference: portrait 720×1280 at 24 fps,
cinematic warm-graded 3D scenes, centred serif subtitles (Cormorant Garamond), title, chapter and
end cards, a calm male narrator and an ambient score. The John 17 section takes its mood from the
candlelit "High Priestly Prayer" scene of *The Gospel of John*: night, oil lamps, prayer toward heaven.

Text: John 10:25–39 and John 17:20–26 (NIV wording as supplied, with "Pharisee opponents").

## Shots

| Narration | Scene |
|---|---|
| Title | Jerusalem and the temple on its hill in golden haze |
| 10:25 "I did tell you…" | Solomon's Colonnade: Jesus among the Pharisees |
| "The works I do…" | Stone jars at Cana, water turning to wine |
| "…you are not my sheep." | The leaders turn and walk away down the colonnade |
| "My sheep listen to my voice…" | The shepherd leads his flock across the hills |
| "I give them eternal life…" | Sheep grazing in a quiet pasture |
| "…out of my hand." | The shepherd holds a lamb at sunset |
| "My Father… is greater than all" | Looking up into clouds and sunbeams |
| "…out of my Father's hand." | The flock resting in a stone sheepfold at night |
| "I and the Father are one." | Jesus facing the light between the columns |
| 10:31–33 stones and accusation | Men raise stones in silhouette; the accusers |
| 10:34–35 "Is it not written…" | A Psalms scroll by lamplight, Psalm 82:6 in Hebrew |
| "…sent into the world?" | A light descends from heaven over Bethlehem's hills |
| "I am God's Son" / "believe the works" | Low angle against the sun; twelve baskets of bread and fish |
| "…the Father is in me" / "he escaped" | Jesus in a shaft of light; he walks away into the light |
| Chapter card | Jerusalem at night under the stars |
| 17:20–21 | The upper room in lamplight; one lamp lights another; a hillside of lamps |
| "…that the world may believe" | Earth at night from space, city lights |
| "…the glory… complete unity" | A crowd facing the sunrise; lights rising into one light |
| "Then the world will know" | Sunrise sweeping across the Earth |
| 17:24 "…before the creation of the world" | A path toward the light; flight through the cosmos |
| 17:25 "Righteous Father…" | Jesus praying under an olive tree at night |
| 17:26 | Disciples walking out at dawn; Jesus on the hill, arms open to the sunrise |
| End card | The shepherd and his flock at sunset — "I am the good shepherd." (John 10:11) |

## Pipeline

All of it runs on CPU in a headless container (no GPU).

1. **Narration** — `audio/tts.py`: Kokoro-82M (Apache-2.0), voice `am_michael`; Whisper word
   timestamps align each subtitle phrase. Writes `script/timeline.json`.
2. **Shot plan** — `script/plan_shots.py` maps 35 shots onto the narration units → `script/shots.json`.
3. **3D rendering** — `render/` is a three.js app rendered frame-by-frame in headless Chromium
   (SwiftShader WebGL) by `render/render.js`. Scene kits: `colonnade`, `hills` (terrain, grass,
   sheep, crowds, night lamps, Gethsemane, Jerusalem), `interior` (upper room, lamps, scroll, jars),
   `heaven`, `space`. Post: bloom, god rays, depth of field, ACES tone mapping and a warm film grade.
4. **Score** — `audio/music.py` synthesizes an original score (pads, strings, choir, piano, drones,
   hall reverb), timed to the narration; `audio/mix.py` ducks it under the voice (−15 LUFS master).
5. **Compositing** — `render/compose.py` dissolves the shots, sets the cards and subtitles in
   Cormorant Garamond (with ligatures and old-style figures, as in the reference), adds grain and
   encodes H.264/AAC.

`build.sh` runs everything end to end.

## Assets and licenses

- Skies (HDRIs), PBR textures and props (rocks, olive-like trees, baskets, bread, goblets,
  bowls, clay pot): [Poly Haven](https://polyhaven.com), CC0.
- Earth imagery: NASA Visible Earth (Blue Marble / Black Marble), public domain.
- Fonts: Cormorant Garamond and Frank Ruhl Libre (SIL Open Font License).
- Voice: Kokoro-82M (Apache-2.0). Music: synthesized here, original.
- Figures, sheep, architecture, lamps, scroll and jars are procedural (this repository).
