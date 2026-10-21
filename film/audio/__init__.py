"""Audio for THE STONE AND THE BREAD.

  tts.py    casts the voices, synthesizes every dialogue line (film/assets/dialogue/*.wav) and writes the
            film's single source of timing truth, film/timeline.json.
  sfx.py / music.py / mix.py   ambience, foley, score and the final mix (see SPEC.md section 5).

Nothing is imported here on purpose: `python3 film/audio/tts.py` must stay importable without side effects.
"""
