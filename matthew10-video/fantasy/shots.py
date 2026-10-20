"""Shot list for the fantasy version: one generated still per image on screen.

Same format as realistic/shots.py (read by realistic/gen_images.py). The people
keep their faces from the realistic version through IP-Adapter references
(ref_*.png in the image folder). `faces` lists the people animated in each
still, left to right, as (scene, actor) from fantasy/direction.js.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "realistic"))
from shots import MAYA, MOM, NEG  # noqa: E402

STYLE_HEAD = "epic fantasy film still, photorealistic, cinematic, 35mm photograph"
STYLE = ("dramatic volumetric lighting, atmospheric, highly detailed, rich color grading, shallow depth of field")
NEG_F = NEG + ", modern clothing, phone, car, glasses on a young woman"
CU = "neutral relaxed expression, mouth closed, eyes open"
DAD = ("a 62-year-old Black man with dark brown skin, short gray hair, a gray mustache and round wire spectacles, "
       "a navy wool coat with silver buttons over a white high-collared shirt")
GREG = ("a 45-year-old white man with neatly combed sandy blond hair, clean shaven, a fine linen shirt, a dark leather "
        "vest and a brass chain of office")
PRIYA = ("a 34-year-old South Asian woman with a long dark braid over her shoulder and round wire spectacles, an olive "
         "green linen robe")
W, H = 768, 1344


def shot(id, prompt, faces=(), ref=None, seed=1, w=W, h=H, ip=0.6, neg="", init=None, strength=0.75):
    s = {"id": id, "prompt": f"{STYLE_HEAD}, {prompt}, {STYLE}", "negative": f"{NEG_F}, {neg}" if neg else NEG_F,
         "faces": list(faces), "ref": ref, "seed": seed, "w": w, "h": h, "ip": ip}
    if init:
        s.update(init=init, strength=strength)
    return s


M = MAYA   # her face; costumes are given per shot
SHOTS = [
    # ---------------------------------------------------------------- the city of glass
    shot("city_wide", "a city of glass towers rising from a vast frozen sea at dusk, warm golden light glowing inside the "
         "glass, a green aurora in a deep blue sky, snow mist drifting over the ice, epic wide shot", seed=201),
    shot("law_door", "a towering arched doorway of frosted glass and silver in a fantasy city, an arch of glowing runes "
         "carved above it, falling snow, warm lantern light, low angle", seed=202),
    shot("smiling_crowd", "elegant people in winter fantasy cloaks walking across a plaza of clear glass at dusk, every "
         "face wearing the same calm polite smile, lanterns, slightly uncanny, medium wide shot", seed=203),
    shot("maya_smile", f"close-up portrait of {M}, wearing a deep blue wool cloak over a cream linen dress with a high "
         "neckline, standing in a city of glass at dusk, warm lights in soft bokeh behind her, a polite tight-lipped "
         "smile, tired eyes", faces=[("glass", "maya")], ref="ref_maya", seed=204),

    # ---------------------------------------------------------------- the feast
    # the realistic dinner photo turned into an ice hall keeps the family in their seats
    shot("feast_hall", "a feast hall carved from ice and glass lit by hundreds of candles, a Black family at a long "
         "table: on the left a 60-year-old mother with a gray bob in a rose velvet gown and pearls, in the middle a father "
         "with gray hair, round spectacles and a gray mustache in a navy coat, on the right a young man in a dark green "
         "tunic, the back of a young woman's dark curly hair in the foreground",
         faces=[("feast", "mom"), ("feast", "dad"), ("feast", "jordan")], seed=205,
         init="/opt/work/real/img/table_wide.png", strength=0.6),
    shot("mom_feast", f"close-up portrait of {MOM}, wearing a rose velvet gown with a high collar and a pearl circlet in "
         "her hair, seated at a feast in a hall of ice and candles, warm candlelight, pleasant expression, lips closed",
         faces=[("feast", "mom")], ref="ref_mom", seed=206, neg="young, smile with teeth"),
    shot("maya_ember", f"close-up of {M}, wearing a dark green velvet gown with a high neckline, seated at a candlelit "
         "feast in a hall of ice, holding a small glowing ember of golden light cupped in her hands below her chin, the "
         "glow lighting her face, troubled expression, mouth closed", faces=[("feast", "maya")], ref="ref_maya", seed=207),
    shot("dad_feast", f"close-up portrait of {DAD}, seated at a feast in a hall of ice and candles, warm candlelight, "
         "stern expression, mouth closed", faces=[("feast", "dad")], ref="ref_dad", seed=208),
    shot("crack_floor", "close-up of a floor of clear glass beneath a candlelit feast table, reflections of candle "
         "flames in the glass, a jagged crack beginning to split the glass", seed=209),

    # ---------------------------------------------------------------- the sword
    shot("sword_sky", "a colossal sword of blazing white light descending point-first out of a storm of dark clouds "
         "toward a city of glass on a frozen sea, lightning, epic scale, night", seed=210),
    shot("sword_impact", "a giant glowing sword of light plunged into a frozen sea at night, a vast crack of light "
         "racing across the ice toward a city of glass, a shockwave of snow and light", seed=211),
    shot("shadows_wall", "enormous looming shadows of a family cast by candlelight onto a wall of ice, a lone young woman "
         "with dark curly hair standing small before them, seen from behind, dramatic", seed=212),
    shot("frozen_faces", "serene faces of people frozen just beneath clear ice, eyes closed, faint polite smiles, pale "
         "blue light, eerie, close-up", seed=213),
    shot("ice_floe", "a lone young woman in a deep blue cloak standing on a small ice floe drifting on a black sea at "
         "night, a green aurora overhead, a glowing sword of light standing upright in the ice beside her, a distant "
         "glass city", seed=214),

    # ---------------------------------------------------------------- the hall of mirrors
    shot("mirror_hall", "an endless hall of ornate gilded mirrors lit by candles, a young Black woman with dark curly "
         "hair in a deep blue cloak walking alone down the middle, reflections repeating into the distance", seed=215),
    shot("mirror_refl", f"close-up of {M}, wearing a cream linen dress with a high neckline, framed in an ornate gilded "
         "mirror, candlelight, a perfect polite smile, lips closed", faces=[("mirrors", "refl")], ref="ref_maya",
         seed=216),
    shot("maya_mirror", f"close-up of {M}, wearing a cream linen dress with a high neckline, in a dark candlelit hall of "
         "mirrors, sad expression, eyes glistening, mouth closed", faces=[("mirrors", "maya")], ref="ref_maya",
         seed=217),
    shot("maya_light", f"close-up of {M}, wearing a cream linen dress with a high neckline, in a dark hall, her face "
         "softly lit by cool blue-white light from a small glowing orb floating in front of her, mouth closed",
         faces=[("mirrors", "maya")], ref="ref_maya", seed=218),

    # ---------------------------------------------------------------- the cross
    shot("figure_cross", "a tall robed figure made of radiant white light, face hidden in glowing light, walking up a "
         "misty mountain path at dawn carrying a heavy wooden cross on his shoulder, a young woman in a deep blue cloak "
         "following behind him lifting a wooden cross onto her own shoulder", seed=219),
    shot("mask_shatter", "a white porcelain mask with a painted smile shattering into pieces in mid-air, glowing "
         "shards, dark background, dramatic light", seed=220),
    shot("true_face", f"close-up of {M}, tears on her cheeks, warm golden light pouring over her face, looking upward, "
         "eyes open, dark background with floating golden motes, mouth closed", faces=[("cross", "maya")],
         ref="ref_maya", seed=221),

    # ---------------------------------------------------------------- the guildhall
    shot("guildhall", "a vast fantasy workshop hall with hundreds of glaring brass lanterns hanging from iron chains, "
         "long workbenches, steam, harsh flickering light, crowded, oppressive", seed=222),
    shot("maya_guild", f"close-up of {M}, wearing a brown leather work apron over a cream linen dress with a high "
         "neckline, at a workbench in a harsh lantern-lit workshop, squinting, pained expression, mouth closed",
         faces=[("guild", "maya")], ref="ref_maya", seed=223),
    shot("guildmaster", f"low angle close-up of {GREG}, in a lantern-lit workshop, a condescending smile, mouth closed",
         faces=[("guild", "greg")], ref="ref_greg", seed=224),
    shot("overwhelm", f"close-up of {M}, wearing a brown leather work apron, pressing both hands over her ears, eyes "
         "squeezed shut, distressed, harsh glaring lantern light", faces=[("guild", "maya")], ref="ref_maya", seed=225),

    # ---------------------------------------------------------------- the sparrows
    shot("market", "a fantasy market square at golden hour, wooden carts with small wicker cages of sparrows, "
         "merchants, cobblestones, warm sunlight and dust in the air", seed=226),
    shot("two_sparrows", "close-up of two small brown sparrows in a tiny wicker cage on a wooden market cart beside a "
         "single copper coin, warm golden light", seed=227),
    shot("sparrow_fall", "a small brown sparrow falling through a shaft of golden light toward old cobblestones, wings "
         "loose, dust in the air, slow motion, close-up", seed=228),
    shot("hand_catch", "a gentle hand made of radiant golden light catching a small brown sparrow in mid-air, rays of "
         "light, floating dust, dark background", seed=229),
    shot("hair_stars", f"close-up of {M}, wearing a deep blue cloak, under a starry night sky, tiny golden lights like "
         "stars caught in her dark curly hair, looking up in wonder, mouth closed", faces=[("sparrows", "maya")],
         ref="ref_maya", seed=230),
    shot("flock_rise", "a young woman in a deep blue cloak standing in a cobblestone square at sunset as a great flock "
         "of sparrows rises into the golden sky all around her, seen from behind", seed=231),

    # ---------------------------------------------------------------- the scrying pool
    shot("pool", "a round stone basin of still water glowing with soft blue light in a dark stone chamber, candles, "
         "mist", seed=232),
    shot("mom_pool", f"close-up of {MOM}, wearing a rose velvet gown and a pearl circlet, in a dim castle chamber, lit "
         "by cool blue light from below as if from water, tense expression, lips closed", faces=[("pool", "mom")],
         ref="ref_mom", seed=233, neg="young, smile with teeth"),
    shot("maya_pool", f"close-up of {M}, wearing a deep blue cloak, leaning over a basin of glowing water at night, cool "
         "blue light from below on her face, sad, mouth closed", faces=[("pool", "maya")], ref="ref_maya", seed=234),

    # ---------------------------------------------------------------- the road
    shot("gate_night", "a young woman in a deep blue cloak carrying a lantern walking out through the great gate of a "
         "glass city at night, snow falling, cold blue light, seen from behind", seed=235),
    shot("bridge", "a long narrow stone bridge over a deep misty chasm, a lone cloaked woman crossing it, a small glowing "
         "orb of light floating ahead of her, golden sunrise ahead, storm clouds behind, epic wide shot", seed=236),
    shot("figure_dawn", "a tall robed figure made of radiant white light, face hidden in glowing light, standing at the "
         "far end of a stone bridge at sunrise with arms open in welcome, golden light, mist, seen from a distance",
         seed=237),
    shot("maya_road", f"close-up of {M}, wearing a deep blue cloak, on a mountain road at dawn, warm sunrise light, a "
         "small glowing orb of light near her shoulder lighting her face, hopeful, mouth closed",
         faces=[("flight", "maya")], ref="ref_maya", seed=238),

    # ---------------------------------------------------------------- the next town
    shot("haven", "a cozy fantasy village in a green mountain valley at sunrise, soft warm lanterns, flower gardens, "
         "sparrows on the rooftops, peaceful", seed=239),
    shot("priya", f"close-up portrait of {PRIYA}, in a cozy library with soft dim lanterns, warm smile, mouth closed",
         faces=[("haven", "priya")], ref="ref_priya", seed=240),
    shot("maya_haven", f"close-up of {M}, wearing a rust orange wool dress with a high neckline, in a cozy room with "
         "soft lantern light, gentle smile, eyes glistening, mouth closed", faces=[("haven", "maya")], ref="ref_maya",
         seed=241),
    shot("sparrow_letter", "a small brown sparrow perched on a wooden windowsill with a tiny rolled parchment letter "
         "tied to its leg with red thread, sunrise light, close-up", seed=242),
    shot("maya_window", f"close-up of {M}, wearing a rust orange wool dress with a high neckline, standing by a window "
         "at sunrise, warm golden light on her face, a small sparrow on the windowsill, peaceful, mouth closed",
         faces=[("haven", "maya")], ref="ref_maya", seed=243),
]

if __name__ == "__main__":
    json.dump(SHOTS, open(sys.argv[1], "w"), indent=1)
    print(len(SHOTS), "shots")
