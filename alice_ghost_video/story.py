"""The script for "Alice" — a little ghost who can't keep a single snack.

Every beat is one of:
  * a spoken line:   {'say': (speaker, text), ...}
  * a silent action: {'act': name, 'dur': seconds, ...}

Optional keys on any beat:
  scene  – switch background ('night', 'kitchen', 'supper', 'end')
  shot   – camera framing name (see render.SHOTS)
  emo    – {'A': emotion, 'S': emotion, 'A.gaze': target, ...} applied at beat start
  cues   – [(word, {...same keys as emo..., 'hi'/'lo': stinger, 'act': name})]
           fired the moment that word is spoken
  act    – action started at beat start (spoken beats may also carry one)
  pre    – silence before the beat (seconds)
  post   – silence after the beat (seconds)
  speed  – TTS speed multiplier
  pitch  – extra semitone shift for this line
  gain   – loudness multiplier (whispers < 1)
  sub    – subtitle text if it should differ from the spoken text

Speakers: N = narrator, A = Alice (the ghost), S = Granny Simmer (the cauldron).
"""

VOICES = {
    # Kokoro voice, base speed, semitone shift, whether formants move with pitch,
    # and a gentle vibrato depth (an old, warbly voice for the cauldron).
    'N': dict(lang='b', voice='bm_fable', speed=0.90, semitones=-1.0, formants='preserved', vibrato=0.0),
    'A': dict(lang='a', voice='af_heart', speed=0.98, semitones=4.0, formants='shifted', vibrato=0.0),
    'S': dict(lang='b', voice='bf_emma', speed=0.88, semitones=-2.5, formants='preserved', vibrato=0.06),
}

NAMES = {'N': '', 'A': 'Alice', 'S': 'Granny Simmer'}

BEATS = [
    # ── 1. Gloomy little town, opening frame shows Alice + title ────────────
    dict(scene='night', shot='night_wide', act='title',
         emo={'A': 'content', 'A.gaze': 'moon'},
         say=('N', "In a crooked old town, where the long shadows creep, "
                   "where the moon's always full, and the bats never sleep,"),
         pre=0.6, post=0.25,
         cues=[('creep', {'lo': 1}), ('bats', {'act': 'bats'})]),
    dict(shot='night_mid',
         say=('N', "there floated a ghost, rather small, rather white, "
                   "named Alice... who dreamed about snacks every night."),
         post=0.3,
         cues=[('ghost', {'A.gaze': 'cam'}),
               ('Alice', {'A': 'shy', 'A.gaze': 'cam', 'act': 'wave'}),
               ('dreamed', {'A': 'dreamy', 'A.gaze': 'up'}),
               ('snacks', {'hi': 1, 'act': 'bubbles_in'})]),
    dict(shot='night_bubbles', emo={'A': 'dreamy', 'A.gaze': 'bubbleL'},
         say=('A', "Mmm... an eyeball gobstopper..."), gain=0.85, speed=0.9,
         post=0.15),
    dict(emo={'A.gaze': 'bubbleR'},
         say=('A', "and a stripey moon-mint..."), gain=0.85, speed=0.9,
         post=0.35),
    dict(shot='night_mid', emo={'A': 'blissful'},
         say=('A', "Yum."), gain=0.9, speed=0.85,
         act='yum_text', cues=[('Yum', {'hi': 2})], post=0.9),

    # ── 2. The kitchen: everything falls straight through ───────────────────
    dict(scene='kitchen', shot='kitchen_wide', act='bubbles_out',
         emo={'A': 'happy', 'A.gaze': 'plate', 'S': 'asleep'},
         say=('N', "Now the trouble with ghosts, as the old stories tell, "
                   "is they're made out of moonlight, and whispers as well."),
         pre=0.3, post=0.2,
         cues=[('moonlight', {'A.gaze': 'cam', 'A': 'curious'}),
               ('whispers', {'A': 'happy', 'A.gaze': 'plate'})]),
    dict(shot='kitchen_table',
         say=('N', "So whatever she nibbled, and whatever she chewed..."),
         post=0.1, cues=[('nibbled', {'A': 'eager'})]),
    dict(act='eat_fail_1', dur=3.6, emo={'A': 'eager', 'A.gaze': 'hand'}),
    dict(shot='kitchen_wide',
         say=('N', "went straight through the middle. Poor Alice. No food."),
         post=0.5, emo={'A': 'deflated', 'A.gaze': 'floor'},
         cues=[('No', {'lo': 2})]),
    dict(shot='alice_close', emo={'A': 'determined', 'A.gaze': 'plate'},
         say=('A', "Okay. Okay. This time... I'll be really quick."),
         speed=1.05, post=0.2),
    dict(shot='kitchen_table', act='eat_fail_2', dur=3.4,
         emo={'A': 'determined', 'A.gaze': 'hand'}),
    dict(shot='alice_close', emo={'A': 'deflated', 'A.gaze': 'floor'},
         say=('A', "...Every single time."), speed=0.82, gain=0.85,
         pre=0.4, post=1.0, cues=[('time', {'lo': 1})]),

    # ── 3. Granny Simmer wakes up ───────────────────────────────────────────
    dict(shot='kitchen_wide', act='simmer_wakes', dur=1.8,
         emo={'S': 'sleepy', 'S.gaze': 'A'}),
    dict(emo={'S': 'amused', 'A': 'startled', 'A.gaze': 'S'},
         say=('S', "Hmm... That's the third gobstopper this week "
                   "that's rolled under my belly, dearie."),
         post=0.3, cues=[('third', {'A': 'embarrassed', 'A.gaze': 'S', 'A.pos': 'talk'})]),
    dict(shot='alice_close', emo={'A': 'startled', 'A.gaze': 'S'},
         say=('A', "Oh! Granny Simmer! I'm sorry, I didn't mean to wake you... "
                   "I was just... hungry."),
         post=0.4,
         cues=[('sorry', {'A': 'embarrassed', 'A.gaze': 'away'}),
               ('hungry', {'A': 'sad', 'A.gaze': 'floor'})]),
    dict(shot='simmer_close', emo={'S': 'curious', 'S.gaze': 'A'},
         say=('S', "Hungry? Ghosts don't get hungry, little one."),
         post=0.7, cues=[('little', {'S': 'gentle'})]),
    dict(shot='alice_close', emo={'A': 'sad', 'A.gaze': 'floor'},
         say=('A', "Then what's this? Right here."), speed=0.9, post=0.3,
         cues=[('here', {'act': 'heart_show', 'A.gaze': 'chest', 'A': 'hurt'})]),
    dict(emo={'A': 'sad', 'A.gaze': 'S'},
         say=('A', "It feels like a hole... like I'm empty in the middle, "
                   "and everything just falls right through."),
         speed=0.9, post=0.6,
         cues=[('hole', {'lo': 1}), ('empty', {'S': 'concerned', 'A.gaze': 'floor'}),
               ('falls', {'A.gaze': 'S'})]),
    dict(shot='simmer_close', emo={'S': 'concerned', 'S.gaze': 'A'},
         say=('S', "Ah. ...That's a different kind of hungry."),
         speed=0.84, post=0.9),
    dict(shot='window_two', emo={'A': 'wistful', 'A.gaze': 'window', 'A.pos': 'window'},
         say=('A', "Every Moon Supper, the whole town sits together at the long table. "
                   "They pass the bowls... they say 'yum' with their mouths full... "
                   "and they laugh."),
         speed=0.92, post=0.4,
         cues=[('yum', {'hi': 1}), ('laugh', {'A': 'wistful_smile'})]),
    dict(shot='alice_close', emo={'A': 'wistful', 'A.gaze': 'window'},
         say=('A', "And I just float above them. Watching. "
                   "I'm there... but I'm not really there."),
         speed=0.86, post=1.4,
         cues=[('float', {'A': 'sad'}), ('Watching', {'A.gaze': 'floor'}),
               ('not', {'lo': 2, 'act': 'tear', 'S': 'sad'})]),
    dict(shot='simmer_close', emo={'S': 'thoughtful', 'S.gaze': 'up'},
         say=('S', "You know what I've learned, after three hundred years of soup?"),
         speed=0.86, post=0.5, cues=[('soup', {'S.gaze': 'A', 'S': 'warm'})]),
    dict(shot='alice_close', emo={'A': 'sad', 'A.gaze': 'S'},
         say=('A', "...What?"), gain=0.7, speed=0.85, post=0.5),
    dict(shot='two_shot', emo={'S': 'warm', 'S.gaze': 'A'},
         say=('S', "Nobody remembers the soup. "
                   "They remember who was sitting next to them."),
         speed=0.85, post=0.8,
         cues=[('They', {'A': 'hopeful', 'A.pos': 'talk'}), ('next', {'hi': 1})]),
    dict(shot='alice_close', emo={'A': 'sad', 'A.gaze': 'self'},
         say=('A', "But nobody can sit next to me. I'm see-through."),
         speed=0.9, post=0.7, cues=[('see', {'lo': 1})]),
    dict(shot='simmer_close', emo={'S': 'mischievous', 'S.gaze': 'A'},
         say=('S', "Then... we'll cook you a soup that's see-through, too."),
         post=0.5, cues=[('cook', {'hi': 1, 'A': 'curious'})]),
    dict(shot='alice_close', emo={'A': 'curious', 'A.gaze': 'S'},
         say=('A', "A see-through... soup?"), post=0.4),
    dict(shot='two_shot', emo={'S': 'gleeful', 'S.gaze': 'A'},
         say=('S', "Fetch me those sweets, dearie. The eyeball. The stripey one. "
                   "Go on. Trust an old pot."),
         post=0.2,
         cues=[('eyeball', {'A.gaze': 'floor'}), ('Trust', {'A': 'hopeful', 'A.gaze': 'S'})]),

    # ── 4. A see-through soup ───────────────────────────────────────────────
    dict(shot='kitchen_wide', act='fetch_drop', dur=4.6,
         emo={'A': 'eager', 'S': 'gleeful', 'A.pos': 'by_pot'}),
    dict(shot='steam_shot', act='steam_rise', emo={'A': 'curious', 'A.gaze': 'steam', 'S': 'warm', 'S.gaze': 'steam'},
         say=('N', "The pot gave a gurgle, a burble, a sigh, "
                   "and a silvery steam began curling up high."),
         post=0.2, cues=[('silvery', {'hi': 1, 'A': 'amazed'})]),
    dict(say=('N', "It was soft, it was swirly, it floated with grace... "
                   "a wisp of a thing, with a rather sweet face."),
         post=0.5, cues=[('sweet', {'act': 'wisp_face', 'A': 'happy'})]),
    dict(shot='two_shot', emo={'S': 'warm', 'S.gaze': 'A', 'A.gaze': 'steam'},
         say=('S', "Steam is just soup that's learned how to float. "
                   "Now... who does that remind you of?"),
         speed=0.88, post=0.8,
         cues=[('float', {'A.gaze': 'S', 'A': 'curious'}), ('remind', {'A': 'realizing'})]),
    dict(shot='alice_close', emo={'A': 'realizing', 'A.gaze': 'S'},
         say=('A', "...Me?"), speed=0.85, post=0.6, cues=[('Me', {'hi': 2})]),
    dict(shot='simmer_close', emo={'S': 'tender', 'S.gaze': 'A'},
         say=('S', "Go on, little one. Breathe it in."), speed=0.84, post=0.3),
    dict(shot='steam_shot', act='inhale', dur=4.4,
         emo={'A': 'inhale', 'S': 'tender', 'S.gaze': 'A'}),
    dict(shot='alice_close', emo={'A': 'amazed', 'A.gaze': 'cam'},
         say=('A', "Oh... Oh! It's staying... I can taste it!"),
         gain=0.95, post=0.4,
         cues=[('staying', {'act': 'heart_fill'}), ('taste', {'hi': 2, 'A': 'joyful'})]),
    dict(emo={'A': 'joyful', 'A.gaze': 'up'},
         say=('A', "It's minty... and sweet... and just a tiny bit eyeball-y..."),
         post=0.2, cues=[('eyeball', {'A': 'giggly', 'A.gaze': 'S'})]),
    dict(shot='two_shot', emo={'S': 'laughing', 'S.gaze': 'A'},
         say=('S', "Ha! That's the secret ingredient!"), post=0.2),
    dict(shot='two_shot', emo={'A': 'joyful', 'A.gaze': 'cam'}, act='spin',
         say=('A', "Yum!"), post=1.2, cues=[('Yum', {'hi': 3, 'act': 'hearts_burst'})]),

    # ── 5. Moon Supper ──────────────────────────────────────────────────────
    dict(scene='supper', shot='supper_wide', emo={'A': 'content', 'A.gaze': 'S', 'S': 'warm', 'S.gaze': 'A'},
         say=('N', "And that Moon Supper night, at the end of the table, "
                   "sat a ghost and a pot, just as close as they're able."),
         pre=0.2, post=0.6, cues=[('ghost', {'act': 'lean'})]),
    dict(shot='supper_two', emo={'A': 'content', 'A.gaze': 'S'},
         say=('A', "Granny Simmer? ...I don't feel hollow anymore."),
         speed=0.9, post=0.6, cues=[('hollow', {'hi': 1})]),
    dict(emo={'S': 'tender', 'S.gaze': 'A'},
         say=('S', "You never were, dearie. "
                   "You were only waiting for someone to share with."),
         speed=0.86, post=0.7, cues=[('share', {'A': 'touched'})]),
    dict(emo={'A': 'shy', 'A.gaze': 'S'},
         say=('A', "Then... save me a seat? Every Moon Supper?"), post=0.4),
    dict(emo={'S': 'warm'}, say=('S', "Always."), speed=0.85, post=1.0,
         cues=[('Always', {'hi': 2, 'A': 'joyful'})]),
    dict(shot='supper_wide', emo={'A': 'content', 'A.gaze': 'moon'},
         say=('N', "So if ever you're feeling see-through, alone... "
                   "like there's food on the table, but none is your own..."),
         post=0.3, cues=[('alone', {'lo': 2})]),
    dict(shot='supper_two', emo={'A': 'content', 'A.gaze': 'S'},
         say=('N', "remember small Alice, and Simmer's warm hum: "
                   "it's who shares it with you... that makes it a yum."),
         post=0.4, cues=[('who', {'A.gaze': 'cam', 'A': 'beaming'}), ('yum', {'hi': 3})]),
    dict(shot='alice_close', emo={'A': 'beaming', 'A.gaze': 'cam'},
         say=('A', "Yum!"), act='hearts_float', post=1.6, cues=[('Yum', {'hi': 1})]),

    # ── 6. End card ─────────────────────────────────────────────────────────
    dict(scene='end', shot='end', act='end_card', dur=6.0,
         emo={'A': 'beaming', 'A.gaze': 'cam'}),
]
