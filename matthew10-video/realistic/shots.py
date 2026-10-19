"""Shot list for the realistic version.

Every shot is one generated photograph. `faces` lists the people whose faces
are animated (left to right as they appear), each driven by an actor exported
from the 2D direction (scene, actor name). `ref` anchors identity with an
IP-Adapter face reference.
"""
import json
import sys

# Leading style words carry the most weight; the rest goes at the end.
STYLE_HEAD = "cinematic film still, photorealistic, 35mm photograph"
STYLE = "natural skin texture, soft cinematic lighting, shallow depth of field, high detail, color graded"
NEG = ("cartoon, anime, illustration, painting, drawing, 3d render, cgi, plastic skin, deformed, disfigured, "
       "extra fingers, bad hands, extra limbs, text, watermark, logo, lowres, blurry face, oversaturated, "
       "open mouth, teeth, frown lines, cross-eyed")

MAYA = ("a 28-year-old Black woman with warm brown skin, shoulder-length dark curly hair, soft round face, "
        "full lips, expressive dark brown eyes, natural makeup")
MOM = ("a Black woman in her late fifties with medium brown skin, a graying chin-length bob, soft smile lines around "
       "her eyes, small pearl stud earrings, a pearl necklace and a high-necked dusty rose blouse")
MOM_NEG = "young, youthful, glamorous, cleavage, dangling earrings"
DAD = ("a 62-year-old Black man with dark brown skin, short gray hair with a receding hairline, a gray mustache, "
       "rectangular glasses, navy sweater over a white collared shirt")
JORDAN = "a 22-year-old Black young man with brown skin, short messy dark hair, a dark green hoodie"
GREG = "a 45-year-old white man with neatly combed sandy blond hair, clean shaven, light blue dress shirt and navy tie"
PRIYA = "a 34-year-old South Asian woman with long dark hair in a braid over her shoulder, round glasses, an olive green sweater"
CU = "neutral relaxed expression, mouth closed, eyes open"

W, H = 768, 1344


def shot(id, prompt, faces=(), ref=None, seed=1, w=W, h=H, ip=0.6, neg=""):
    return {"id": id, "prompt": f"{STYLE_HEAD}, {prompt}, {STYLE}", "negative": f"{NEG}, {neg}" if neg else NEG,
            "faces": list(faces), "ref": ref, "seed": seed, "w": w, "h": h, "ip": ip}


SHOTS = [
    # identity anchors (generated first; their faces become the references)
    shot("ref_maya", f"close-up studio portrait of {MAYA}, wearing a cream top, soft window light, plain warm gray background, "
         f"looking at the camera, {CU}", seed=11, w=896, h=1152),

    # 1. the table
    # (SDXL loses track of three described people in one long sentence; short, ordered descriptions work better)
    shot("table_wide", "wide shot of a Black family of three at a dinner table in a cozy dining room at night, seen from "
         "across the table, all three seated side by side facing the camera: on the left a mother in her late fifties "
         "with a graying bob and a dusty rose blouse, in the middle an older father with gray hair, glasses and a gray "
         "mustache in a navy sweater, on the right a young adult son with short hair in a dark green hoodie, plates of "
         "roast dinner, candles, wine glasses, warm pendant lamp above the table, a window with blue dusk light behind them",
         faces=[("table", "mom"), ("table", "dad"), ("table", "jordan")], seed=21, neg=MOM_NEG),
    shot("table_maya", f"close-up portrait of {MAYA}, wearing a mustard yellow cardigan over a cream top, sitting at a dinner "
         f"table at night, warm lamp light from above, blurred dining room with warm bokeh lights behind her, {CU}, "
         "looking slightly to the left of the camera", faces=[("table", "maya")], ref="ref_maya", seed=22),
    shot("table_mom", f"close-up portrait of {MOM}, sitting at a dinner table at night, warm lamp light, blurred window with "
         f"blue dusk and red curtains behind her, pleasant {CU}, looking slightly to the right of the camera",
         faces=[("table", "mom")], seed=23, neg=MOM_NEG),
    shot("table_dad", f"close-up portrait of {DAD}, sitting at a dinner table at night, warm lamp light, blurred wall with a "
         f"framed photo behind him, stern {CU}, looking slightly down", faces=[("table", "dad")], seed=24),
    shot("table_jordan", f"close-up portrait of {JORDAN}, sitting at a dinner table at night, warm lamp light, blurred dining "
         f"room behind him, {CU}, looking slightly to the left of the camera", faces=[("table", "jordan")], seed=25),

    # interlude: the sword
    shot("sword_table", "dramatic dark scene, silhouettes of a family seated together at the left end of a long dinner table, "
         "a lone young woman silhouette seated at the far right end, a dark room glowing with firelight from below, "
         "floating embers and smoke, deep red and orange tones, a single candle on the table, epic cinematic composition",
         seed=31),
    shot("sword_maya", f"close-up portrait of {MAYA}, in a dark room lit by warm orange firelight from the left side, glowing "
         f"embers floating in the dark background, solemn {CU}, looking slightly down",
         faces=[("sword", "maya")], ref="ref_maya", seed=32),

    # 2. the mask
    shot("mirror_reflection", f"close-up of a bathroom mirror showing the reflection of {MAYA}, wearing a lavender gray hoodie, "
         f"cool white vanity light, teal tiles, she faces the mirror, {CU}, looking straight ahead",
         faces=[("mask", "refl")], ref="ref_maya", seed=41),
    shot("mirror_real", f"close-up of {MAYA}, wearing a lavender gray hoodie, standing in a dim bathroom at night, cool light "
         f"from a vanity lamp on one side of her face, teal tiles blurred behind, {CU}, looking slightly to the left",
         faces=[("mask", "real")], ref="ref_maya", seed=42),
    shot("bed_wide", "a young Black woman with curly hair in a lavender hoodie sitting on her bed at night in a dark bedroom, "
         "her face lit by a laptop screen, warm string fairy lights on the wall, city lights through the window, "
         "cozy blue and warm tones, wide shot", faces=[("mask", "bed")], seed=43),
    shot("bed_cu", f"close-up of {MAYA}, wearing a lavender gray hoodie, sitting on her bed at night with her knees pulled up, "
         f"her face lit by cool blue laptop screen light from below, warm fairy lights bokeh behind her, {CU}, "
         "looking down slightly", faces=[("mask", "bed")], ref="ref_maya", seed=44),

    # interlude: the cross
    shot("cross_true", f"close-up portrait of {MAYA}, wearing a lavender gray hoodie, glowing warm golden light on her face, "
         f"dark background with floating golden embers, {CU}, looking at the camera",
         faces=[("cross", "trueA")], ref="ref_maya", seed=51),
    shot("cross_moon", f"close-up of {MAYA}, wearing a lavender gray hoodie, in a dark bedroom at night, cool blue moonlight "
         "through a window casting the shadow of the window frame, a cross shaped shadow across her face and chest, "
         f"{CU}, serene", faces=[("cross", "moon")], ref="ref_maya", seed=52),

    # 3. the office
    shot("office_two", "an open-plan office under harsh fluorescent lights, two coworkers: on the left a white man in his "
         "forties with sandy blond hair, a light blue shirt and a navy tie, standing and leaning on a gray cubicle wall, "
         "looking down at her; on the right a young Black woman with dark curly hair in a teal sweater with a red lanyard, "
         "seated at her desk and looking up at him, computer monitor, cool greenish fluorescent tones",
         faces=[("office", "greg"), ("office", "maya")], seed=61),
    shot("office_maya", f"close-up of {MAYA}, wearing a teal sweater with a red lanyard and headphones around her neck, "
         f"sitting at an office desk under harsh fluorescent lights, blurred open office behind her, tired {CU}, "
         "looking slightly up", faces=[("office", "maya")], ref="ref_maya", seed=62),
    shot("office_temple", f"close-up of {MAYA}, wearing a teal sweater with a red lanyard and headphones around her neck, "
         "rubbing her temple with her fingertips, squinting under harsh fluorescent office lights, blurred open office "
         "behind her, mouth closed", faces=[("office", "maya")], ref="ref_maya", seed=63),
    shot("office_greg", f"low angle close-up of {GREG}, standing in an open-plan office under fluorescent lights, friendly "
         f"{CU}, looking down toward the camera", faces=[("office", "greg")], seed=64),
    shot("office_overwhelm", f"close-up of {MAYA}, wearing a teal sweater, pressing both hands over her ears, eyes shut tight, "
         "distressed, harsh flickering fluorescent office light, blurred office behind her, mouth closed",
         faces=[("office", "maya")], ref="ref_maya", seed=65),

    # 3b. the park
    shot("park_wide", "a young Black woman with curly hair in a teal sweater sitting alone on a wooden park bench at golden "
         "hour, a few sparrows on the path near her feet, low sun glowing behind trees, warm peaceful light, wide shot",
         faces=[("park", "maya")], seed=71),
    shot("park_cu", f"close-up of {MAYA}, wearing a teal sweater, sitting on a park bench at golden hour, warm backlight "
         f"from the setting sun, a small brown sparrow on the bench beside her, soft bokeh, tired {CU}, "
         "looking down to the right", faces=[("park", "maya")], ref="ref_maya", seed=72),

    # interlude: the sparrows
    shot("sparrows_flock", "a flock of small brown sparrows flying across a golden sunset sky, glowing clouds, warm light, "
         "wide cinematic composition", seed=81),
    shot("sparrows_shoulder", f"close-up of {MAYA}, wearing a teal sweater, at golden hour with a small brown sparrow perched "
         f"on her shoulder, warm sunlight, soft bokeh, serene {CU}, looking slightly to the right",
         faces=[("sparrows", "maya")], ref="ref_maya", seed=82),

    # 4. the call
    shot("call_maya", f"close-up of {MAYA}, wearing a lavender gray hoodie, holding a smartphone to her right ear, sitting on a "
         f"sofa in her living room at night, warm table lamp light, bookshelf blurred behind her, anxious {CU}",
         faces=[("call", "maya")], ref="ref_maya", seed=91),
    shot("call_mom", f"close-up of {MOM}, holding a phone to her ear in her kitchen in the evening, warm kitchen light, "
         f"cabinets blurred behind her, tight {CU}", faces=[("call", "mom")], seed=92, neg=MOM_NEG),
    shot("call_maya_mouth", f"close-up of {MAYA}, wearing a lavender gray hoodie, sitting on a sofa at night with one hand "
         "pressed over her mouth, eyes glistening with tears, warm lamp light, bookshelf blurred behind her",
         faces=[("call", "maya")], ref="ref_maya", seed=93),
    shot("call_maya_after", f"close-up of {MAYA}, wearing a lavender gray hoodie, sitting on a sofa at night holding a phone "
         f"in her lap, its screen softly lighting her face, warm lamp light, bookshelf blurred behind her, {CU}, "
         "looking down", faces=[("call", "maya")], ref="ref_maya", seed=94),

    # interlude: the road
    shot("road_night", "a lone young woman in a hoodie walking away from the camera down the middle of an empty country road "
         "at night, a small town glowing with warm lights on the horizon, starry deep blue sky, wide cinematic shot", seed=101),
    shot("road_dawn", "a lone young woman in a hoodie walking away from the camera down the middle of an empty country road "
         "at dawn, sunrise glowing golden on the horizon behind a small town, soft pink and gold sky, wide cinematic shot",
         seed=101),

    # epilogue
    shot("epi_two", "a bright modern office with large windows and green plants in morning sunlight, two coworkers at "
         "neighboring desks: on the left a South Asian woman in her thirties with a long dark braid, round glasses and an "
         "olive green sweater, smiling warmly; on the right a young Black woman with dark curly hair in a rust orange "
         "sweater, warm natural light", faces=[("epilogue", "priya"), ("epilogue", "maya")], seed=111),
    shot("epi_maya", f"close-up of {MAYA}, wearing a rust orange sweater, in a bright office with plants and windows, soft "
         f"morning light, gentle {CU}, looking slightly to the left", faces=[("epilogue", "maya")], ref="ref_maya", seed=112),
    shot("epi_window", f"close-up of {MAYA}, wearing a rust orange sweater, standing by a window at sunrise, warm golden light "
         f"on her face, a small brown sparrow perched on the windowsill beside her, rooftops outside, peaceful {CU}, "
         "looking slightly to the right", faces=[("epilogue", "maya")], ref="ref_maya", seed=113),
]

# Expression references: one woman, one seed, different emotions. LivePortrait
# extracts the expression of each; (emotion - neutral) becomes a blendable delta.
EXPRESSIONS = {
    "neutral": "neutral relaxed expression, mouth closed",
    "sad": "deeply sad expression, inner eyebrows raised, downturned mouth, mouth closed",
    "cry": "crying, tears on her cheeks, eyebrows pulled up and together, lips trembling, mouth closed",
    "joy": "joyful genuine smile with crinkled eyes, mouth closed",
    "surprise": "surprised expression, eyebrows raised high, eyes wide open, mouth slightly open",
    "anger": "angry expression, eyebrows lowered and drawn together, lips pressed tightly",
    "worry": "worried anxious expression, eyebrows drawn together and raised, lips pressed",
    "tender": "tender emotional expression, soft sad smile, eyes glistening",
}
for k, v in EXPRESSIONS.items():
    SHOTS.append(shot(f"expr_{k}", f"close-up studio headshot of a 30-year-old woman with brown skin and dark hair pulled back, "
                      f"{v}, plain gray background, looking at the camera", seed=777, w=832, h=1024))

if __name__ == "__main__":
    json.dump(SHOTS, open(sys.argv[1], "w"), indent=1)
    print(len(SHOTS), "shots")
