"""DO NOT DISTURB: a three-part animated story (Tiredness, Embarrassment, Impulsivity and the creature)."""

SPEAKERS = {
    "tired": ("TIREDNESS", "#7d6fb0"),
    "emb": ("EMBARRASSMENT", "#d91c3c"),
    "boss": ("DR. CONTEMPT", "#5d6b8a"),
    "aide": ("ASSISTANT", "#a0805a"),
    "guard": ("SECURITY", "#2e3a66"),
    "recept": ("RECEPTIONIST", "#1fa59a"),
    "sci": ("SCIENTIST", "#5d6b8a"),
    "narr2": ("NARRATOR", "#26244a"),
}


def install():
    from toon.draw import set_ink
    from toon import characters, sets, engine, audio
    from .style import INK
    from . import cast, places, sound
    set_ink(INK)
    characters.DRAWERS.update(cast.DRAW)
    sets.SETS.update(places.SETS)
    engine.HEAD_TOP.update(cast.HEADS)
    engine.SPEAKERS.update(SPEAKERS)
    audio.VOICES.update(sound.VOICES)
    audio.SFX.update(sound.SFX)
    audio.MUSIC.update(sound.MUSIC)
