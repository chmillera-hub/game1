"""'Clickety-Clack!' — an original Halloween bone-dance song.

Cast: Mister Marrow (a jolly skeleton bandleader), his skeleton crew,
Alice the little ghost, and Granny Simmer the cauldron.

Melody is written in D minor around D4 and transposed per singer.
Note syntax inside a phrase:  syllable/midi/eighths   ('_/n' is a rest).
A syllable ending in '-' joins the next one into the same word.
'|' starts a new sung phrase (each phrase is voiced in one breath).
"""

BPM = 128

CHORUS = """
Click-/62/1 e-/62/1 ty/65/2 clack,/69/3 the/67/1 bones/65/2 come/64/2 back,/62/3 |
the/69/1 moon/70/2 is/69/1 up/67/3 and/65/1 the/64/1 night/65/2 is/64/2 black!/61/3 _/1 |
Shake/62/2 your/62/1 shins/65/3 and/64/1 rat-/65/1 tle/64/1 your/62/1 spine,/69/4 _/1 |
ev-/69/1 ery-/70/1 bo-/69/1 dy's/67/1 danc-/69/1 ing/67/1 and/65/1 the/64/1 dark/65/1 feels/67/2 fine!/74/5 _/1
"""

CHORUS_FINAL = """
Click-/62/1 e-/62/1 ty/65/2 clack,/69/3 the/67/1 bones/65/2 come/64/2 back,/62/3 |
the/69/1 moon/70/2 is/69/1 up/67/3 and/65/1 the/64/1 night/65/2 is/64/2 black!/61/3 _/1 |
Bones/62/2 go/62/1 clack/65/3 and/64/1 the/65/1 pot/64/1 goes/62/1 pop,/69/4 _/1 |
and/69/1 a/70/1 lit-/69/1 tle/67/1 ghost/69/1 goes/73/1 BOO/74/2 at/73/1 the/76/1 top!/74/5 _/1
"""

VERSE_1 = """
When/57/1 the/57/1 clock/62/2 strikes/62/1 twelve/64/2 and/62/1 the/60/1 owls/62/2 all/60/1 hoot,/57/3 _/1 |
we/57/1 climb/62/2 on/62/1 out/64/2 in/65/1 our/64/1 Sun-/62/2 day/60/1 suits,/57/4 _/1 |
we/57/1 dust/62/2 off/62/1 our/64/1 ribs/65/2 and/64/1 we/62/1 pol-/64/1 ish/62/1 our/60/1 toes,/62/3 _/1 |
and/57/1 we/57/1 tap,/62/1 _/1 tap,/64/1 _/1 tap/65/2 wher-/64/1 ev-/62/1 er/60/1 the/61/1 wind/62/2 blows./57/2
"""

VERSE_2 = """
There's/57/1 a/57/1 pot/62/2 by/62/1 the/62/1 door/64/2 goes/62/1 bub-/60/1 ble/62/1 pop,/57/3 _/2 |
there's/57/1 a/57/1 pump-/62/2 kin/62/1 on/64/1 drums/65/2 who/64/1 won't/62/2 stop!/57/4 _/1 |
a/57/1 cat/62/2 on/62/1 a/64/1 fid-/65/2 dle,/64/1 a/62/1 bat/64/1 on/62/1 a/60/1 horn,/62/3 _/1 |
and/57/1 we/57/1 dance,/62/1 _/1 dance,/64/1 _/1 dance/65/2 till/64/1 the/62/1 break/60/1 of/61/1 morn!/57/2 _/2
"""

TAG = """
Ev-/69/1 ery-/69/1 bo-/70/1 dy's/69/1 got/67/1 a/65/1 sound/67/2 of/65/1 their/64/1 own,/62/5 _/1 |
so/62/1 sing/65/2 it/64/1 out/65/1 loud,/69/3 you/69/1 were/70/1 nev-/69/1 er/67/1 a-/69/1 lone!/74/11
"""

# Singers: Kokoro voice, octave offset from the written melody, how much the
# natural speech melody is replaced by the written tune (1 = fully sung),
# pitch factor and formant factor for spoken lines, pan.
SINGERS = {
    'M':  dict(voice='am_michael', lang='a', octave=-12, formant=0.90, speak_pitch=0.78, pan=0.0, gain=1.0),
    'A':  dict(voice='af_heart', lang='a', octave=0, formant=1.08, speak_pitch=1.26, pan=0.1, gain=1.0),
    'S':  dict(voice='bf_emma', lang='b', octave=0, formant=0.96, speak_pitch=0.86, pan=-0.3, gain=0.8),
    'K1': dict(voice='am_puck', lang='a', octave=-12, formant=0.95, speak_pitch=0.9, pan=-0.45, gain=0.55),
    'K2': dict(voice='am_fenrir', lang='a', octave=-12, formant=0.92, speak_pitch=0.9, pan=0.45, gain=0.55),
    'K3': dict(voice='af_bella', lang='a', octave=0, formant=0.97, speak_pitch=1.0, pan=-0.25, gain=0.45),
    'K4': dict(voice='af_nicole', lang='a', octave=0, formant=1.0, speak_pitch=1.0, pan=0.3, gain=0.4),
    'C':  dict(voice='am_echo', lang='a', octave=0, formant=1.15, speak_pitch=1.5, pan=0.4, gain=0.7),
}
CREW = ['K1', 'K2', 'K3', 'K4']

# Song form.
#   metered sections: 'bars' (+ 'lyric', 'singers' = {singer: how sung, 1.0 fully}),
#                     optional 'talk' = [(seconds into section, speaker, text, opts)]
#   free-time sections: 'dialogue' = [(speaker, text, opts) | ('ACT', name, seconds)]
FORM = [
    dict(name='intro', bars=4, key=0,
         talk=[(2.5, 'M', "Psst. Hey... you. Yes, you. It's midnight.", dict(speed=0.9))]),
    dict(name='verse1', bars=8, key=0, lyric=VERSE_1, singers={'M': 0.9}),
    dict(name='chorus1', bars=8, key=0, lyric=CHORUS,
         singers={'M': 1.0, 'K1': 1.0, 'K2': 1.0, 'K3': 1.0, 'K4': 1.0}),
    dict(name='verse2', bars=8, key=0, lyric=VERSE_2, singers={'M': 0.9}),
    dict(name='chorus2', bars=8, key=0, lyric=CHORUS,
         singers={'M': 1.0, 'K1': 1.0, 'K2': 1.0, 'K3': 1.0, 'K4': 1.0}),
    # the band stops dead: Alice's turn
    dict(name='stop', key=0, dialogue=[
        ('M', "Your turn, little ghost! Give us a clack!", dict(speed=1.0, emo='gleeful', post=0.5)),
        ('A', "Um... okay...", dict(speed=0.9, gain=0.75, emo='nervous', post=0.3)),
        ('ACT', 'pff', 2.0),
    ]),
    # free-time heart-to-heart over a quiet vamp
    dict(name='bridge', key=0, dialogue=[
        ('A', "I... I can't. I don't have any bones.", dict(speed=0.88, cues=[('bones', 'lo')], emo='sad', post=0.5)),
        ('A', "I can't clickety... and I can't clack.", dict(speed=0.86, cues=[('clack', 'lo')], emo='sad', post=1.0)),
        ('M', "Hmm. Little one... look around. Nobody here sounds the same.", dict(speed=0.86, emo='gentle', post=0.5)),
        ('M', "The bones go clack. The pot goes bubble. And the cat goes...", dict(speed=0.9, emo='warm', post=0.25)),
        ('C', "Mrrrow.", dict(speed=0.8, emo='smug', post=0.5)),
        ('S', "And I go bubble, dearie. Very loudly.", dict(speed=0.88, emo='warm', post=0.6)),
        ('M', "So tell me... what does a ghost go?", dict(speed=0.85, emo='curious', post=1.0)),
        ('A', "A ghost goes... boo?", dict(speed=0.85, cues=[('boo', 'hi')], emo='hopeful', gain=0.8, post=0.5)),
        ('M', "Louder!", dict(speed=1.0, cues=[('Louder', 'hi')], emo='gleeful', post=0.3)),
    ]),
    dict(name='boo', bars=2, key=0, lyric="Boo!/69/3 ~/74/11 _/2", singers={'A': 1.0}),
    dict(name='chorus3', bars=8, key=2, lyric=CHORUS_FINAL,
         singers={'M': 1.0, 'A': 1.0, 'S': 1.0, 'K1': 1.0, 'K2': 1.0, 'K3': 1.0, 'K4': 1.0}),
    dict(name='tag', bars=5, key=2, bpm=96, lyric=TAG, singers={'A': 1.0},
         join={'M': 1.0, 'S': 1.0, 'K1': 1.0, 'K2': 1.0, 'K3': 1.0}, join_phrase=1),
    dict(name='button', bars=1, key=2, bpm=96, talk=[(0.55, 'ALL', "Boo!", dict(speed=1.0))]),
    dict(name='end', seconds=5.5, key=2),
]

TITLE = 'Clickety-Clack!'
