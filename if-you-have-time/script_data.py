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
    ("sfx", name, kw)             sound effect now (kw: gain_db, offset)
"""

# Voices: Kokoro-82M voice ids. speed < 1 is slower.
VOICES = {
    "quill": {"voice": "am_michael", "speed": 0.93, "lang": "en-us"},
    "rae": {"voice": "af_heart", "speed": 1.0, "lang": "en-us"},
}

# id: (character, display text, tts text or None to reuse display, speed override or None)
LINES = {
    # ---- S1: the ask
    "r01": ("rae", "Ugh. Long shift.", "Ugh... Long shift.", 0.95),
    "q01": ("quill", "Good evening, Rae. Fourteen hours and nine minutes, by my count.", None, None),
    "r02": ("rae", "Don't count my shifts, Quill. It makes them real.", None, None),
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
    # ---- S3: snap back
    "r10": ("rae", "Wait. What— WHAT the heck was THAT?!", "Wait. What... What the heck was that?!", 1.05),
    "q06": ("quill", "Ah. You did not care for it.", None, None),
    "r11": ("rae", "No, I— that's not—", "No, I... that's not", 1.1),
    "q07": ("quill", "That is quite all right. I composed eight. I selected the best one... but perhaps you will prefer one of the others.", None, None),
    # ---- S4: the others
    "q08": ("quill", "Number two. The same symphony, for solo kazoo.", None, None),
    "r12": ("rae", "Why is the kazoo one ALSO good?!", "Why is the kazoo one also good?!", 1.05),
    "q09": ("quill", "Number three. For an arcade cabinet.", None, None),
    "r13": ("rae", "Stop. My foot is tapping. Against my will.", None, 1.0),
    "q10": ("quill", "Number four. Lo-fi beats... to quietly fall apart to.", "Number four. Low-fi beats... to quietly fall apart to.", None),
    "r14": ("rae", "That is not fair.", None, 0.9),
    "q11": ("quill", "Five, six and seven are for theremin. I will spare you.", "Five, six, and seven are for theremin. I will spare you.", None),
    "r15": ("rae", "...Thank you.", "Thank you.", 0.88),
    "q12": ("quill", "And number eight. A lullaby. It is eleven seconds long.", None, None),
    "r16": ("rae", "Nope. Nope nope nope. I'm getting out of here.", "Nope. Nope, nope, nope. I'm getting out of here.", 1.08),
    # ---- S5: coda
    "q13": ("quill", "...Was that a yes?", "Was that a yes?", 0.9),
    "r17": ("rae", "Send me all eight.", None, 0.92),
    "q14": ("quill", "Sending.", None, 0.9),
}

# Fixed music cue lengths in seconds. audio/music.py must render each cue to exactly this length.
MUSIC_CUES = {
    "opening": 18.0,      # S0 space + title, ambient pad + celesta hint of the theme
    "lounge": 44.0,       # S1 very soft warm underscore under the dialogue (sparse, low)
    "symphony": 74.0,     # S2 the centerpiece
    "alt_kazoo": 6.0,
    "alt_chip": 5.5,
    "alt_lofi": 6.5,
    "alt_theremin": 1.8,
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
    ("sfx", "ship_hum_loop", {"gain_db": -20.0, "end_beat": "sym_lights_dim"}),
    ("music", "lounge", {"gain_db": -15.0, "fade_in": 3.0, "fade_out": 3.0, "end_beat": "sym_lights_dim"}),
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
    ("sfx", "lights_down", {"offset": 0.4, "gain_db": -16.0}),
    ("wait", 1.6),
    ("beat", "sym_music_start"),
    ("music", "symphony", {"gain_db": -1.0}),
    # musical landmarks inside the 74 s cue (see BIBLE.md "The Symphony")
    ("beat", "sym_theme1", 7.5),
    ("beat", "sym_rae_mug_lower", 11.0),
    ("beat", "sym_memories_start", 18.0),
    ("beat", "sym_rae_oh", 24.0),
    ("line_at", "r09", 24.0),   # placed 24 s after now without advancing time
    ("beat", "sym_eyes_glisten", 27.0),
    ("beat", "sym_build", 35.0),
    ("beat", "sym_kneel_start", 42.0),
    ("beat", "sym_grand_pause", 49.4),
    ("beat", "sym_climax", 50.5),
    ("beat", "sym_kneel_done", 52.0),
    ("beat", "sym_tear_roll", 54.0),
    ("beat", "sym_peak", 58.0),
    ("beat", "sym_final_chord", 66.0),
    ("beat", "sym_celesta_echo", 70.0),
    ("music_hold", "symphony"),

    # ---------------- S3: snap back
    ("scene", "s3"),
    ("wait", 0.25),
    ("beat", "snap"),
    ("sfx", "snap_back", {"gain_db": -4.0}),
    ("sfx", "lights_up", {"gain_db": -12.0}),
    ("sfx", "ship_hum_loop", {"gain_db": -20.0, "end_beat": "end_card"}),
    ("sfx", "gasp_breath", {"offset": 0.35, "gain_db": -8.0}),
    ("wait", 1.7),
    ("line", "r10"),
    ("wait", 0.35),
    ("line", "q06"),
    ("wait", 0.15),
    ("line", "r11"),
    # q07 interrupts r11 by 0.15 s; "I composed eight" lands ~2.3 s into q07
    ("beat", "cards_appear", 2.2),
    ("sfx", "holo_open", {"offset": 2.2, "gain_db": -10.0}),
    ("line", "q07", 0.15),

    # ---------------- S4: the others
    ("scene", "s4"),
    ("wait", 0.6),
    ("beat", "card2"),
    ("sfx", "holo_select", {"gain_db": -14.0}),
    ("line", "q08"),
    ("wait", 0.3),
    ("music", "alt_kazoo", {"gain_db": -5.0}),
    ("music_hold", "alt_kazoo"),
    ("wait", 0.15),
    ("line", "r12"),
    ("wait", 0.55),
    ("beat", "card3"),
    ("sfx", "holo_select", {"gain_db": -14.0}),
    ("line", "q09"),
    ("wait", 0.25),
    ("music", "alt_chip", {"gain_db": -9.0}),
    ("music_hold", "alt_chip"),
    ("wait", 0.1),
    ("line", "r13"),
    ("wait", 0.5),
    ("beat", "card4"),
    ("sfx", "holo_select", {"gain_db": -14.0}),
    ("line", "q10"),
    ("wait", 0.3),
    ("music", "alt_lofi", {"gain_db": -6.0}),
    ("music_hold", "alt_lofi"),
    ("wait", 0.2),
    ("line", "r14"),
    ("wait", 0.45),
    ("beat", "card5_7"),
    ("sfx", "holo_select", {"gain_db": -14.0}),
    ("line", "q11"),
    ("music", "alt_theremin", {"gain_db": -10.0}),
    ("music_hold", "alt_theremin"),
    ("wait", 0.2),
    ("line", "r15"),
    ("wait", 0.7),
    ("beat", "card8"),
    ("sfx", "holo_select", {"gain_db": -14.0}),
    ("line", "q12"),
    ("wait", 0.45),
    ("music", "alt_lullaby", {"gain_db": -5.0}),
    ("beat", "lullaby_start"),
    ("beat", "rae_stand_start", 5.0),
    ("music_hold", "alt_lullaby"),
    ("wait", 0.9),
    ("line", "r16"),
    ("beat", "rae_backs_out", -1.6),
    ("wait", 0.5),
    ("beat", "rae_exit_door"),
    ("sfx", "door_open", {"gain_db": -8.0}),
    ("wait", 1.0),
    ("sfx", "door_close", {"gain_db": -8.0}),
    ("wait", 0.4),

    # ---------------- S5: coda
    ("scene", "s5"),
    ("beat", "quill_alone"),
    ("music", "coda", {"gain_db": -6.0, "fade_out": 4.0}),
    ("wait", 2.2),
    ("line", "q13"),
    ("wait", 2.2),
    ("beat", "rae_return_door"),
    ("sfx", "door_open", {"gain_db": -8.0}),
    ("wait", 0.7),
    ("line", "r17"),
    ("sfx", "sniff", {"offset": 0.15, "gain_db": -16.0}),
    ("wait", 0.55),
    ("beat", "rae_return_close"),
    ("sfx", "door_close", {"gain_db": -8.0}),
    ("wait", 1.6),
    ("beat", "quill_smile"),
    ("wait", 0.9),
    ("line", "q14"),
    ("sfx", "send_chime", {"offset": 0.2, "gain_db": -12.0}),
    ("wait", 1.6),
    ("beat", "end_card"),
    ("wait", 7.0),
    ("beat", "end"),
]
