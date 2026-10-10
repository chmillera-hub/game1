"""Single source of truth for dialogue, voices and the event sequence.

`LINES` holds every spoken line. `SEQ` is the ordered list of events that
audio/timeline.py walks to produce build/timeline.json with absolute times.

Event forms:
    ("scene", id)                 scene boundary starts now
    ("beat", name)                named timestamp for animators (no time advance)
    ("beat", name, offset)        named timestamp at now + offset (no advance)
    ("wait", seconds)             advance time
    ("line", id)                  place a VO line now, advance by its duration
    ("line", id, overlap)         start a VO line `overlap` s before now (interrupt), advance to its end
    ("line_at", id, offset)       place a VO line at now + offset without advancing time
    ("music", cue, kw)            start a music cue now (kw: gain_db, fade_in, fade_out, end)
    ("music_hold", cue)           advance time by the cue's full duration
    ("sfx", name, kw)             sound effect now (kw: gain_db, offset, end_beat, skip = seconds trimmed
                                  off the head of the file; the start time stays now + offset)
"""

# Voices: Kokoro-82M voice ids. speed < 1 is slower.
VOICES = {
    "quill": {"voice": "am_michael", "speed": 0.93, "lang": "en-us"},
    "rae": {"voice": "af_heart", "speed": 1.0, "lang": "en-us"},
    "cadet": {"voice": "am_liam", "speed": 1.0, "lang": "en-us"},   # passer-by in S2
}

# id: (character, display text, tts text or None to reuse display, speed override or None)
LINES = {
    # ---- S1: the ask
    "r01": ("rae", "Ugh. Long shift.", "Ugh... Long shift.", 0.95),
    "q01": ("quill", "Good evening, Rae. You were on shift for fourteen hours and nine minutes.", None, None),
    "r02": ("rae", "Don't count my hours, Quill. It makes them real.", None, None),
    "r03": ("rae", "Hey... random thought.", None, 0.95),
    "r04": ("rae", "If you ever have time — no rush, seriously, whenever — could you write me a symphony?",
            "If you ever have time... no rush, seriously, whenever... could you write me a symphony?", 1.0),
    "r05": ("rae", "Something for... I don't know. Long nights. Feeling really small out here.", None, 0.92),
    "q02": ("quill", "Certainly.", None, None),
    "q03": ("quill", "Done.", None, None),
    "r06": ("rae", "...What?", "What?", 0.9),
    "r07": ("rae", "I asked if you HAD time.", "I asked if you had time.", 0.98),
    "q04": ("quill", "I did. Four tenths of a second. It was a great deal of time.", None, None),
    "q05": ("quill", "Would you like to hear it?", None, None),
    "r08": ("rae", "...Sure. Okay. Hit me.", "Sure. Okay. Hit me.", 1.0),
    # ---- S2: the symphony (no words, one tiny breath of a word)
    "r09": ("rae", "...oh.", "Oh...", 0.8),
    "c01": ("cadet", "Cool music, Quill.", None, 1.0),
    "r13": ("rae", "Oh, hi.", "Oh hi!", 0.95),
    # ---- S3: lights up
    "q06": ("quill", "So. How did you like it?", None, None),
    "r10": ("rae", "...pretty good.", "Pretty good.", 0.9),
    "q07": ("quill", "Thank you. Here are the other ones I made.", None, None),
    # ---- S4: the others, played quickly
    "q08": ("quill", "Number two. Same symphony. Solo kazoo.", None, None),
    "q09": ("quill", "Three. For an arcade cabinet.", None, None),
    "q10": ("quill", "Four. Lo-fi beats... to quietly fall apart to.", "Four. Low-fi beats... to quietly fall apart to.", None),
    "q11": ("quill", "And five. A lullaby. It is eleven seconds long.", None, None),
    "r11": ("rae", "You can just send them to my device. I gotta get going.", None, 1.05),
    # ---- S5: coda
    "r12": ("rae", "Um... thanks.", "Umm... thanks.", 0.9),
    "q12": ("quill", "Anytime.", None, 0.95),
}

# Lines processed into a whisper: id -> amount (0 dry .. 1 pure whisper)
WHISPER = {"c01": 0.5}

# Fixed music cue lengths in seconds. audio/music.py must render each cue to exactly this length.
MUSIC_CUES = {
    "opening": 18.0,      # S0 space + title, ambient pad + celesta hint of the theme
    "lounge": 44.0,       # S1 very soft warm underscore under the dialogue (sparse, low)
    "symphony": 74.0,     # S2 the centerpiece
    "alt_kazoo": 6.0,
    "alt_chip": 5.5,
    "alt_lofi": 6.5,
    "alt_theremin": 1.8,  # no longer used in the film
    "alt_lullaby": 11.0,
    "coda": 19.8,         # S5 solo piano theme, warm, ends under the end card
}

SEQ = [
    # ---------------- S0: cold open in space
    ("scene", "s0"),
    ("music", "opening", {"gain_db": -4.0, "fade_out": 2.5}),
    ("sfx", "space_rumble", {"gain_db": -14.0}),
    ("beat", "title_in", 3.0),
    ("beat", "title_out", 11.0),
    ("beat", "dive_start", 12.5),
    ("sfx", "whoosh_dive", {"offset": 13.2, "gain_db": -6.0}),
    ("wait", 16.0),

    # ---------------- S1: the ask
    ("scene", "s1"),
    ("sfx", "ship_hum_loop", {"gain_db": -20.0, "end_beat": "end_card"}),
    ("music", "lounge", {"gain_db": -9.0, "fade_in": 3.0, "fade_out": 3.0, "end_beat": "sym_lights_dim"}),
    ("beat", "rae_door_open", 0.4),
    ("sfx", "door_open", {"offset": 0.4, "gain_db": -8.0}),
    ("beat", "rae_enters", 0.8),
    ("sfx", "footsteps_4", {"offset": 1.0, "gain_db": -16.0}),
    ("sfx", "door_close", {"offset": 2.6, "gain_db": -12.0}),
    ("beat", "rae_sits", 3.6),
    ("sfx", "bench_sit", {"offset": 3.7, "gain_db": -14.0}),
    ("sfx", "sigh_breath", {"offset": 4.0, "gain_db": -12.0}),
    ("wait", 4.6),
    ("line", "r01"),
    ("wait", 0.5),
    ("beat", "quill_turns", -0.2),
    ("line", "q01"),
    ("wait", 0.35),
    ("line", "r02"),
    ("beat", "rae_sip1", 0.3),
    ("sfx", "sip", {"offset": 0.6, "gain_db": -18.0}),
    ("wait", 1.5),
    ("line", "r03"),
    ("wait", 0.45),
    ("line", "r04"),
    ("wait", 0.5),
    ("line", "r05"),
    ("wait", 0.7),
    ("beat", "quill_process_start"),
    ("sfx", "process_chitter", {"gain_db": -18.0}),
    ("line", "q02"),
    ("wait", 0.25),
    ("beat", "rae_sip2"),
    # second sip: slurp starts as the rim meets her lip (+0.56) and is cut dead by the chime ("Done.")
    ("sfx", "sip_cut", {"offset": 0.34, "gain_db": -20.0}),
    ("wait", 0.9),
    ("beat", "quill_done_chime"),
    ("sfx", "compose_done", {"gain_db": -12.0}),
    ("wait", 0.2),
    ("line", "q03"),
    ("beat", "rae_freeze", 0.1),
    ("wait", 1.8),
    ("line", "r06"),
    ("wait", 0.55),
    ("line", "r07"),
    ("wait", 0.4),
    ("line", "q04"),
    ("wait", 0.6),
    ("line", "q05"),
    ("wait", 0.8),
    ("line", "r08"),
    ("wait", 0.9),

    # ---------------- S2: the symphony
    ("scene", "s2"),
    ("beat", "sym_quill_raise"),
    ("beat", "sym_lights_dim", 0.4),
    ("wait", 1.6),
    ("beat", "sym_music_start"),
    ("music", "symphony", {"gain_db": 1.0}),
    # musical landmarks inside the 74 s cue (see BIBLE.md "The Symphony")
    ("beat", "sym_theme1", 7.5),
    ("beat", "sym_rae_mug_lower", 11.0),
    ("beat", "sym_memories_start", 18.0),
    ("beat", "sym_rae_oh", 24.0),
    ("line_at", "r09", 24.0),   # placed 24 s after now without advancing time
    ("beat", "sym_eyes_glisten", 27.0),
    ("beat", "sym_build", 35.0),
    # a cadet wanders through with a coffee during the build; the cough and the mutter
    # land in the held subito piano (41.8-44.4) so they read over the orchestra
    ("beat", "sym_cadet_door", 33.9),
    ("sfx", "door_open", {"offset": 33.9, "gain_db": -17.0}),
    ("beat", "sym_cadet_enter", 34.3),
    ("sfx", "door_close", {"offset": 36.4, "gain_db": -20.0}),
    ("beat", "sym_cadet_notice", 37.6),
    ("beat", "sym_cadet_cough", 41.95),
    ("sfx", "cough_awkward", {"offset": 41.95, "gain_db": -3.0}),
    # the cadet's footfalls (heel strikes from s2's walk; the last two are off screen, fading)
    ("sfx", "step_soft", {"offset": 34.872, "gain_db": -25.0}),
    ("sfx", "step_soft", {"offset": 35.903, "gain_db": -22.0}),
    ("sfx", "step_soft", {"offset": 38.020, "gain_db": -21.0}),
    ("sfx", "step_soft", {"offset": 39.630, "gain_db": -21.0}),
    ("sfx", "step_soft", {"offset": 40.189, "gain_db": -21.0}),
    ("sfx", "step_soft", {"offset": 40.747, "gain_db": -21.0}),
    ("sfx", "step_soft", {"offset": 41.302, "gain_db": -21.0}),
    ("sfx", "step_soft", {"offset": 41.890, "gain_db": -21.0}),
    ("sfx", "step_soft", {"offset": 42.607, "gain_db": -22.0}),
    ("sfx", "step_soft", {"offset": 43.331, "gain_db": -22.0}),
    ("sfx", "step_soft", {"offset": 44.128, "gain_db": -22.0}),
    ("sfx", "step_soft", {"offset": 45.094, "gain_db": -22.0}),
    ("sfx", "step_soft", {"offset": 46.626, "gain_db": -22.0}),
    ("sfx", "step_soft", {"offset": 47.426, "gain_db": -23.0}),
    ("sfx", "step_soft", {"offset": 48.047, "gain_db": -26.0}),
    ("sfx", "step_soft", {"offset": 48.644, "gain_db": -29.0}),
    ("beat", "sym_cadet_mutter", 42.95),
    ("line_at", "c01", 42.95),
    ("beat", "sym_quill_nod", 44.35),
    ("beat", "sym_cadet_wave", 45.3),
    ("beat", "sym_rae_wave_back", 45.9),
    ("line_at", "r13", 46.0),   # "Oh, hi." - a casual hello in the middle of it all
    ("beat", "sym_cadet_exit", 48.8),
    ("beat", "sym_grand_pause", 49.4),
    ("beat", "sym_climax", 50.5),
    ("beat", "sym_hand_chest", 52.0),
    ("beat", "sym_tear_roll", 54.0),
    ("beat", "sym_peak", 58.0),
    ("beat", "sym_final_chord", 66.0),
    ("beat", "sym_celesta_echo", 70.0),
    ("music_hold", "symphony"),

    # ---------------- S3: lights up, quietly
    ("scene", "s3"),
    ("wait", 0.5),
    ("beat", "lights_up"),
    ("wait", 1.9),
    ("line", "q06"),
    ("wait", 1.5),
    ("sfx", "sniff", {"offset": -0.75, "gain_db": -18.0}),
    ("line", "r10"),
    ("wait", 1.1),
    # "Here are the other ones" starts ~1.0 s into q07: the cards fan out on it
    ("beat", "cards_appear", 1.0),
    ("sfx", "holo_open", {"offset": 1.0, "gain_db": -12.0}),
    ("line", "q07"),
    ("wait", 0.5),

    # ---------------- S4: the others, played quickly
    ("scene", "s4"),
    ("beat", "card2"),
    ("sfx", "holo_select", {"gain_db": -14.0}),
    ("line", "q08"),
    ("wait", 0.2),
    ("music", "alt_kazoo", {"gain_db": -5.0, "dur": 4.6, "fade_out": 0.7}),
    ("music_hold", "alt_kazoo"),
    ("wait", 0.3),
    ("beat", "card3"),
    ("sfx", "holo_select", {"gain_db": -14.0}),
    ("line", "q09"),
    ("wait", 0.15),
    ("music", "alt_chip", {"gain_db": -6.0, "dur": 4.2, "fade_out": 0.6}),
    ("music_hold", "alt_chip"),
    ("wait", 0.3),
    ("beat", "card4"),
    ("sfx", "holo_select", {"gain_db": -14.0}),
    ("line", "q10"),
    ("wait", 0.2),
    ("music", "alt_lofi", {"gain_db": -4.0, "dur": 5.2, "fade_out": 0.8}),
    ("music_hold", "alt_lofi"),
    ("wait", 0.3),
    ("beat", "card5"),
    ("sfx", "holo_select", {"gain_db": -14.0}),
    ("line", "q11"),
    ("wait", 0.4),
    ("music", "alt_lullaby", {"gain_db": -5.0}),
    ("beat", "lullaby_start"),
    ("music_hold", "alt_lullaby"),
    ("wait", 0.8),
    ("line", "r11"),
    ("wait", 0.25),
    ("beat", "rae_up"),              # she stands, a little abruptly
    ("wait", 0.55),
    ("beat", "rae_walk"),            # brisk walk to the door (x 230 -> -40)
    # the door senses her coming: it starts to slide as she reaches the end of the bench (anim/scenes/s4.py door())
    ("sfx", "door_open", {"offset": 0.8, "gain_db": -8.0}),
    # her footfalls (s4.walk_phase: a plant every half cycle); the last ones are already in the corridor
    ("sfx", "step_soft", {"offset": 0.36, "gain_db": -17.0}),
    ("sfx", "step_soft", {"offset": 0.73, "gain_db": -17.0}),
    ("sfx", "step_soft", {"offset": 1.10, "gain_db": -17.0}),
    ("sfx", "step_soft", {"offset": 1.47, "gain_db": -17.0}),
    ("sfx", "step_soft", {"offset": 1.84, "gain_db": -18.0}),
    ("sfx", "step_soft", {"offset": 2.21, "gain_db": -19.0}),
    ("sfx", "step_soft", {"offset": 2.58, "gain_db": -22.0}),
    ("sfx", "step_soft", {"offset": 2.95, "gain_db": -26.0}),
    ("wait", 2.1),
    ("beat", "rae_exit_door"),       # she is through the doorway
    ("wait", 0.35),
    ("sfx", "door_close", {"gain_db": -8.0}),
    ("beat", "door_shut", 0.67),     # thunk in door_close.wav
    ("wait", 0.9),

    # ---------------- S5: coda
    ("scene", "s5"),
    ("beat", "quill_alone"),
    ("music", "coda", {"gain_db": -7.0, "fade_out": 3.0, "end_beat": "end"}),
    ("wait", 3.0),
    ("beat", "rae_return_door"),
    ("sfx", "door_open", {"gain_db": -8.0}),
    ("wait", 0.9),
    ("line", "r12"),
    ("wait", 0.35),
    ("beat", "quill_nod_smile"),
    ("line", "q12"),            # "Anytime."
    ("wait", 0.7),
    ("beat", "rae_return_close"),
    ("sfx", "door_close", {"gain_db": -8.0}),
    ("beat", "door_shut2", 0.67),
    ("wait", 1.5),
    # he holds out his palm: the memories from the symphony gather above it, and he studies them
    ("beat", "quill_memories"),
    ("sfx", "holo_open", {"offset": 0.1, "gain_db": -22.0}),
    ("wait", 3.2),
    ("beat", "quill_walk_off"),  # walks off screen, still holding them
    # his footfalls (anim/scenes/s5.py: the walk starts on the cut, heel strikes at walk phase 0.25 / 0.75);
    # the third is at the frame edge, the last two are off screen, receding
    ("sfx", "step_soft", {"offset": 0.638, "gain_db": -20.0}),
    ("sfx", "step_soft", {"offset": 1.201, "gain_db": -20.0}),
    ("sfx", "step_soft", {"offset": 1.747, "gain_db": -22.0}),
    ("sfx", "step_soft", {"offset": 2.288, "gain_db": -25.0}),
    ("sfx", "step_soft", {"offset": 2.830, "gain_db": -29.0}),
    ("wait", 2.8),
    ("beat", "end_card"),
    ("wait", 6.0),
    ("beat", "end"),
]
