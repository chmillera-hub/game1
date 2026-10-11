# Screenplay JSON format (machine-readable; drives TTS, timing, and animation)

Write a single JSON object:

```json
{
  "title": "On-screen title for the first shot (short, evocative)",
  "logline": "one sentence",
  "voice_notes": { "NARRATOR": "...", "CONSCIOUSNESS": "...", "FEAR": "...", "JOY": "...", "...": "..." },
  "scenes": [
    {
      "id": "s01",
      "slug": "memory",
      "location": "REAL_ROOM | MIND_HQ | MIND_HQ_BACK | VOID_FACE",
      "purpose": "what the viewer must feel/understand by the end of this scene",
      "music": { "mood": "e.g. tender, curious", "instrumentation": "e.g. felt piano, soft pad", "intensity": 0.3 },
      "transition_in": "cut | dissolve | push",
      "beats": [
        {
          "id": "s01b01",
          "kind": "line",
          "speaker": "NARRATOR",
          "inner": false,
          "text": "Exact words spoken. TTS-friendly: no stage directions, no emoji, no brackets.",
          "delivery": "how it is spoken (tempo, emotion, breath), e.g. 'soft, reflective, smiling slightly'",
          "pause_after": 1.2,
          "shot": "framing + camera movement during this beat",
          "acting": {
            "FEAR": "precise face + body: eyes, eyelids, brows, mouth, head, hands, posture, timing",
            "CONSCIOUSNESS": "..."
          },
          "sfx": ["alarm_bell"]
        },
        {
          "id": "s01b02",
          "kind": "silent",
          "duration": 3.0,
          "pause_after": 0.0,
          "shot": "...",
          "acting": { "VOID": "...", "FEAR": "..." },
          "sfx": []
        }
      ]
    }
  ]
}
```

Rules
- `speaker` ∈ NARRATOR, CONSCIOUSNESS, FEAR, JOY, SADNESS, ANGER, CALM. THE VOID never speaks.
- `inner: true` = a thought heard in voice-over (no mouth movement; whisper-ish processing).
- NARRATOR lines are voice-over (the narrator is not lip-synced unless SELF is on screen speaking in REAL_ROOM — then set speaker NARRATOR and say so in acting).
- One line = one breath/thought; split long sentences into several beats so pauses can be placed.
- `pause_after` (seconds) is silence after the beat; use generous values (0.6–2.5s) around emotional moments.
- `silent` beats carry pure acting/reactions (holds, looks, gestures). Use them liberally — the creator wants faces to have time.
- `acting` must name every on-screen character who matters in that beat. Be concrete and animatable
  (e.g. "upper lids drop to half, eyes slide left to the Void, inner brows lift, lower lip trembles, shoulders hunch").
- `sfx` vocabulary (use only these): alarm_bell, alarm_pull, footsteps, door_whoosh, crowd_murmur, heartbeat,
  breath_shaky, sob, cage_close, lock_click, cage_creak, key_turn, rumble_low, shimmer, twinkle, console_beeps,
  paper_rustle, lamp_click, cloth_rustle, rust_creak.
- Total runtime target 5:00–6:30 when lines are spoken slowly (~120–135 wpm) plus pauses and silent beats.
