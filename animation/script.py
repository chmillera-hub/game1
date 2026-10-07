"""The screenplay: every timed event in both parts lives here.

audio.py reads this to place voices, music and sound effects; it then writes
build/timeline_partN.json, which the renderer (scene.html) reads so the
pictures, subtitles and lip-sync line up with the sound.
"""

FPS = 24
W, H = 1280, 720

# Speakers -> how they are voiced.
VOICES = {
    # Inner voice of the listener: close, intimate, a little slow.
    "listener": dict(model="en_US-ryan-high", length=1.12, noise=0.70, noise_w=0.85, fx="inner"),
    # The singer when speaking: soft and worn out.
    "singer": dict(model="en_GB-cori-high", length=1.22, noise=0.75, noise_w=0.9, fx="room"),
    # The listener after the change: slower, warmer.
    "jesus": dict(model="en_US-ryan-high", length=1.28, noise=0.55, noise_w=0.7, fx="warm"),
    # Society: a crowd of different voices, turned into whispers.
    "whisper": dict(model="en_US-libritts_r-medium", length=1.0, noise=0.6, noise_w=0.8, fx="whisper"),
}

WHISPER_SPEAKERS = [12, 87, 140, 233, 391, 455, 610, 702, 815, 870]

# Song tempo (bars of 4 beats). One full melody "loop" is 8 bars.
BPM = 70
BEAT = 60.0 / BPM
BAR = 4 * BEAT
LOOP = 8 * BAR

PARTS = {
    1: dict(
        title="The Song",
        duration=192.0,
        shots=[
            # name, start, end
            ("street", 0, 16),
            ("street_listener", 16, 32),
            ("room_wide", 32, 50),
            ("singer_close", 50, 72),
            ("memories", 72, 96),
            ("listener_close", 96, 118),
            ("storm", 118, 162),
            ("horns", 162, 178.5),
            ("black", 178.5, 182),
            ("card", 182, 192),
        ],
        lines=[
            # speaker, start, text, (optional speaker id for whispers)
            ("listener", 23.5, "Someone's singing."),
            ("listener", 55.0, "Something that beautiful..."),
            ("listener", 59.6, "coming out of someone the world keeps throwing away."),
            ("listener", 74.5, "Someone who doesn't fit."),
            ("listener", 78.6, "And because they don't fit... the world abandons them."),
            ("listener", 86.6, "Makes their life a living hell."),
            ("listener", 99.0, "And still... they can see something this beautiful."),
            ("whisper", 119.5, "Not my problem.", 0),
            ("listener", 123.0, "The abandonment."),
            ("listener", 126.2, "The ostracization."),
            ("whisper", 129.3, "Keep walking.", 1),
            ("whisper", 131.6, "There isn't enough.", 2),
            ("listener", 134.6, "Watching people suffer... and not lifting a finger to help them."),
            ("whisper", 140.6, "Help them and you'll be next.", 3),
            ("listener", 144.2, "And keeping everything so scarce that if you help someone else..."),
            ("listener", 150.0, "you could wind up starved. Or homeless yourself."),
            ("whisper", 155.4, "You don't belong here.", 4),
            ("whisper", 157.4, "Not my problem.", 5),
            ("whisper", 158.6, "There isn't enough.", 6),
            ("whisper", 159.5, "Keep walking.", 7),
        ],
        thunder=[122.0, 131.0, 139.0, 147.0, 153.6, 158.4, 164.5, 169.5, 175.0],
        song=dict(
            vocal_start=7.0, vocal_stop=178.5,
            muffle_until=32.0,      # heard through the wall until the door opens
            warp_from=112.0,        # the song starts to bend as the storm rises
            loops=7,
        ),
        subtitles=True,
    ),
    2: dict(
        title="The Spark",
        duration=210.0,
        shots=[
            ("storm_peak", 0, 24),
            ("spark_appear", 24, 40),
            ("spark_close", 40, 62),
            ("transform", 62, 100),
            ("kneel", 100, 121),
            ("jesus_close", 121, 128),
            ("singer_reply", 128, 145),
            ("leave_room", 145, 158),
            ("night_walk", 158, 190),
            ("finale", 190, 210),
        ],
        lines=[
            ("whisper", 1.5, "Keep walking.", 1),
            ("listener", 5.0, "It doesn't stop."),
            ("whisper", 8.6, "There isn't enough.", 2),
            ("listener", 12.0, "Is this all there is?"),
            ("whisper", 14.8, "You don't belong here.", 4),
            ("listener", 17.4, "Suffering... without end?"),
            ("whisper", 20.6, "Not my problem.", 0),
            ("listener", 42.4, "It's so small."),
            ("listener", 46.6, "But it's brighter than all of it."),
            ("listener", 52.4, "Something sacred is still here..."),
            ("listener", 57.0, "and it can't be put out. Not anymore."),
            ("singer", 114.2, "...You stayed."),
            ("singer", 117.6, "Nobody ever stays."),
            ("jesus", 121.6, "I heard you."),
            ("jesus", 124.8, "Keep singing."),
            ("jesus", 175.0, "Maybe that's what it's for."),
            ("jesus", 179.4, "Carry it out into the night..."),
            ("jesus", 183.4, "until someone else remembers they can do the same."),
        ],
        thunder=[3.0, 9.2, 15.2, 19.6],
        song=dict(
            # music box version when the spark appears, choir during the change,
            # the singer comes back in, stops when they look up, then sings again.
            musicbox_start=26.0,
            choir_start=62.0,
            vocal_a=(100.0, 110.2),
            vocal_b_start=132.0,
        ),
        subtitles=True,
    ),
}
