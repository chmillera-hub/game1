# Screenplay JSON format (machine-readable; drives TTS, timing, music, SFX and animation)

Write a single JSON object to `data/screenplay.json`:

```json
{
  "title": "The Void Has a Sense of Humor",
  "logline": "one sentence",
  "voice_notes": { "NARRATOR": "...", "JESUS": "...", "USER": "...", "FEAR": "...", "MAGICIAN": "...", "VOID": "..." },
  "scenes": [
    {
      "id": "s01",
      "slug": "running_from_the_void",
      "location": "THE_EDGE | MIND_BACKROOM",
      "time_of_day": "golden dusk | late dusk | sunset | backroom",
      "purpose": "what the viewer must feel/understand by the end of this scene",
      "music": { "mood": "e.g. tense-comic chase", "instrumentation": "e.g. pizzicato strings, low brass", "intensity": 0.5 },
      "transition_in": "cut | dissolve",
      "beats": [
        {
          "id": "s01b01",
          "kind": "line",
          "speaker": "NARRATOR",
          "text": "So let's say a Twitter user is ~running from the ~void.",
          "delivery": "how it is spoken (tempo, emotion, breath, emphasis)",
          "pause_after": 0.6,
          "shot": "framing + camera movement during this beat (3D: lens feel, angle, height, move)",
          "action": "what physically happens on screen during this beat (blocking, props, FX) — say-it-show-it",
          "acting": {
            "USER": "precise face + body: eyes, eyelids, brows, mouth, head, hands, posture, timing",
            "VOID": "..."
          },
          "sfx": ["footsteps_run"]
        },
        {
          "id": "s02b05",
          "kind": "vocal",
          "speaker": "VOID",
          "vocal": "laugh_maniacal",
          "duration": 4.5,
          "caption": "(maniacal cosmic laughter)",
          "pause_after": 0.2,
          "shot": "...", "action": "...", "acting": { "VOID": "...", "JESUS": "..." },
          "sfx": ["star_cough"]
        },
        {
          "id": "s02b06",
          "kind": "silent",
          "duration": 2.0,
          "pause_after": 0.0,
          "shot": "...", "action": "...", "acting": { "...": "..." },
          "sfx": []
        }
      ]
    }
  ]
}
```

## Rules

- `speaker` for `line` beats ∈ NARRATOR, JESUS, USER, FEAR, MAGICIAN. NARRATOR is voice-over (no lip-sync).
- `kind: "vocal"` = non-verbal vocalization; `vocal` ∈ `laugh_maniacal, laugh_soft, giggle, snort, whisper,
  huff, sigh, hum, cough, gasp, scream_short, mmhm, whimper, gulp`. Any speaker (mostly VOID). `duration` is
  required. Optional `caption` (shown in subtitles in parentheses; keep few and short). Two characters can
  overlap: add `"overlap": true` to start this beat at the same time as the previous beat (e.g. Jesus's
  "mm-hm" nods during the Void's whisper).
- One `line` = one breath/thought; split long sentences into several beats so pauses can be placed.
- `pause_after` (seconds) is silence after the beat; generous (0.4–2.0 s) around emotional/comic moments.
  Comedy needs timing: a held beat before and after a punchline.
- `silent` beats carry pure acting/reactions (holds, looks, gestures). Use them liberally — the creator
  wants faces and bodies to have time to act and react.
- **Text markup for musical word-painting**: prefix a single word with `^` for a high, hopeful/light/funny
  note (e.g. `^humor`, `^meaningful`, `^smile`) and `~` for a low, heavy/existential/sad note (e.g. `~void`,
  `~terror`, `~alone`). Use on roughly 1 of every 3–4 lines, max 2 marks per line. The markup is stripped for
  TTS and subtitles.
- Profanity: write `f***` for the bleeped word in USER's line (the audio pipeline speaks up to "actual" and
  inserts a comedic bleep), e.g. `"What the actual f***?!"`.
- `acting` must name every on-screen character who matters in that beat. Be concrete and animatable:
  e.g. "upper lids drop to half, eyes slide left to the Void, inner brows lift, lower lip trembles,
  shoulders hunch, left hand grips the phone to the chest".
- `action` must make the say-it-show-it rule explicit for that beat (what the viewer SEES that matches what
  is said).
- `sfx` vocabulary (use only these): footsteps_soft, footsteps_run, footsteps_stomp, sparkle_appear,
  thud_sit, cloth_rustle, whoosh, star_pop, galaxy_whirl, bleep, phone_tap, notification_ding, block_thunk,
  wind_soft, shimmer, twinkle, nebula_swell, rumble_low, cage_creak, lock_click, kick_thump, whoosh_fly,
  crash_buckets, mop_clatter, bucket_bonk, cartoon_birdies, dust_sparkle, dagger_shing, gulp, pat_pat.
- Shots must respect the frame layout: subtitles occupy y≈880–1060 of 1280; faces and key action in
  y≈110–850.
- Total runtime target 4:30–6:30 at natural pacing with pauses and silent beats.
- Frame 0 (first beat of s01) must be a striking, bright-enough, finished image — no fade from black.
