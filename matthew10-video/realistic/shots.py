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
       "open mouth, teeth, frown lines, cross-eyed, cleavage, low neckline, revealing clothing, nsfw, "
       "two heads, duplicate face, stacked faces")

MAYA = ("a 28-year-old Black woman with warm brown skin, shoulder-length dark curly hair, soft round face, "
        "full lips, expressive dark brown eyes, natural makeup")
# Realism checkpoints default to young faces: age goes first and is spelled out.
MOM = ("a 60-year-old Black woman, mature face with visible wrinkles and smile lines, salt-and-pepper gray hair in a "
       "chin-length bob, medium brown skin, small pearl stud earrings, a pearl necklace and a dusty rose blouse")
MOM_NEG = "young, youthful, glamorous, cleavage, dangling earrings, smooth skin, headscarf, turban, hat"
DAD = ("a 62-year-old Black man with dark brown skin, short gray hair with a receding hairline, a gray mustache, "
       "rectangular glasses, navy sweater over a white collared shirt")
JORDAN = "a 22-year-old Black young man with brown skin, short messy dark hair, a dark green hoodie"
GREG = "a 45-year-old white man with neatly combed sandy blond hair, clean shaven, light blue dress shirt and navy tie"
PRIYA = "a 34-year-old South Asian woman with long dark hair in a braid over her shoulder, round glasses, an olive green sweater"
CU = "neutral relaxed expression, mouth closed, eyes open"

W, H = 768, 1344


LAYOUT = "/opt/work/real/layout"   # raw 2D frames (render/main.js --stills T --raw 1)


def shot(id, prompt, faces=(), ref=None, seed=1, w=W, h=H, ip=0.6, neg="", init=None, strength=0.75, inpaint=None,
         init_box=None):
    s = {"id": id, "prompt": f"{STYLE_HEAD}, {prompt}, {STYLE}", "negative": f"{NEG}, {neg}" if neg else NEG,
         "faces": list(faces), "ref": ref, "seed": seed, "w": w, "h": h, "ip": ip}
    if init:
        s.update(init=f"{LAYOUT}/still_{init}.png", strength=strength)
    if init_box:
        s["init_box"] = list(init_box)
    if inpaint:
        s["inpaint"] = inpaint
    return s


def region(box, prompt, seed, strength=0.9, ref=None, ip=0.6):
    r = {"box": list(box), "prompt": f"{STYLE_HEAD}, {prompt}, {STYLE}", "seed": seed, "strength": strength}
    if ref:
        r.update(ref=ref, ip=ip)
    return r


SHOTS = [
    # identity anchors (generated first; their faces become the references)
    shot("ref_maya", f"close-up studio portrait of {MAYA}, wearing a cream top, soft window light, plain warm gray background, "
         f"looking at the camera, {CU}", seed=11, w=896, h=1152),

    # neutral on purpose: the reference's expression carries into every shot it anchors
    shot("ref_mom", f"close-up portrait of {MOM}, soft window light, plain warm gray background, looking at the camera, "
         "calm neutral expression, lips closed, no smile", seed=12, w=896, h=1152, neg=f"{MOM_NEG}, smile, smiling, teeth"),

    # 1. the table
    # Group shots are photo-realized from the 2D frames (img2img): SDXL cannot place
    # three described people from text alone (it merges them).
    shot("table_wide", "a Black family at a dinner table at night in a cozy dining room with warm wood paneled walls, "
         "on the left a mother in her late fifties with a graying bob in a dusty rose blouse, in the middle an older "
         "father with gray hair, glasses and a gray mustache in a navy sweater, on the right a young adult son in a dark "
         "green hoodie, all three facing the camera, plates of roast dinner, a warm pendant lamp above the table, a window "
         "with blue dusk light and red curtains, a wall clock and a framed family photo, the back of a young woman's "
         "dark curly hair in the blurred foreground", faces=[("table", "mom"), ("table", "dad"), ("table", "jordan")],
         seed=21, neg=MOM_NEG, init="0.10",
         inpaint=[region((0, 650, 215, 915), "an elegant 60-year-old Black woman with a short salt-and-pepper gray bob "
                         "haircut, a pearl necklace and a dusty rose blouse, sitting at the end of a dinner table at night, "
                         "a gentle closed-mouth smile, facing the camera, warm lamp light", 15, 1.0),
                  region((250, 680, 515, 910), f"{DAD}, sitting at a dinner table at night, facing the camera, warm lamp light", 6),
                  region((540, 670, 760, 910), f"{JORDAN}, sitting at a dinner table at night, facing the camera, warm lamp "
                         "light", 7)]),
    shot("table_maya", f"close-up portrait of {MAYA}, wearing a mustard yellow cardigan over a cream top, sitting at a dinner "
         f"table at night, warm lamp light from above, blurred dining room with warm bokeh lights behind her, {CU}, "
         "looking slightly to the left of the camera", faces=[("table", "maya")], ref="ref_maya", seed=22),
    shot("table_mom", f"close-up portrait of {MOM}, sitting at a dinner table at night, warm lamp light, blurred window with "
         f"blue dusk and red curtains behind her, pleasant {CU}, looking slightly to the right of the camera",
         faces=[("table", "mom")], ref="ref_mom", seed=23, neg=MOM_NEG),
    shot("table_dad", f"close-up portrait of {DAD}, sitting at a dinner table at night, warm lamp light, blurred wall with a "
         f"framed photo behind him, stern {CU}, looking slightly down", faces=[("table", "dad")], seed=24),
    shot("table_jordan", f"close-up portrait of {JORDAN}, sitting at a dinner table at night, warm lamp light, blurred dining "
         f"room behind him, {CU}, looking slightly to the left of the camera", faces=[("table", "jordan")], seed=25),

    # interlude: the sword
    shot("sword_table", "dramatic dark scene, silhouettes of a family seated together at the left end of a long dinner table, "
         "a lone young woman silhouette seated at the far right end, a dark room glowing with firelight from below, "
         "floating embers and smoke, deep red and orange tones, a single candle on the table, epic cinematic composition",
         seed=31),
    shot("sword_maya", f"close-up portrait of {MAYA}, wearing a cream cardigan over a mustard yellow top, in a dark room lit "
         "by warm orange firelight from the left side, glowing "
         f"embers floating in the dark background, solemn {CU}, looking slightly down",
         faces=[("sword", "maya")], ref="ref_maya", seed=32),

    # 2. the mask
    # the compositor adds the glass (asking for a mirror duplicates the person)
    shot("mirror_reflection", f"close-up of {MAYA}, wearing a cozy lavender gray knit turtleneck sweater, standing in a "
         f"bathroom at night facing the camera as if looking into a mirror, cool white vanity light "
         f"from above, teal tiles behind her, {CU}, looking straight ahead", faces=[("mask", "refl")], ref="ref_maya", seed=41),
    shot("mirror_real", f"close-up of {MAYA}, wearing a cozy lavender gray knit turtleneck sweater, standing in a dim bathroom at night, cool light "
         f"from a vanity lamp on one side of her face, teal tiles blurred behind, {CU}, looking slightly to the left",
         faces=[("mask", "real")], ref="ref_maya", seed=42),
    shot("bed_wide", "a young Black woman with curly hair in a lavender sweater sitting on her bed at night in a dark bedroom, "
         "her face lit by a laptop screen, warm string fairy lights on the wall, city lights through the window, "
         "cozy blue and warm tones, wide shot", faces=[("mask", "bed")], seed=43),
    shot("bed_cu", f"close-up of {MAYA}, wearing a cozy lavender gray knit turtleneck sweater, sitting on her bed at night with her knees pulled up, "
         f"her face lit by cool blue laptop screen light from below, warm fairy lights bokeh behind her, {CU}, "
         "looking down slightly", faces=[("mask", "bed")], ref="ref_maya", seed=44),

    # interlude: the cross
    shot("cross_true", f"head and shoulders portrait of {MAYA}, wearing a cozy lavender gray knit turtleneck sweater, glowing warm golden light on her face, "
         f"dark background with floating golden embers, {CU}, looking at the camera",
         faces=[("cross", "trueA")], ref="ref_maya", seed=53),
    shot("cross_moon", f"close-up of {MAYA}, wearing a cozy lavender gray knit turtleneck sweater, in a dark bedroom at night, cool blue moonlight "
         "through a window casting the shadow of the window frame, a cross shaped shadow across her face and chest, "
         f"{CU}, serene", faces=[("cross", "moon")], ref="ref_maya", seed=52),

    # 3. the office
    shot("office_two", "an open-plan office under harsh fluorescent lights, a white man in his forties with sandy blond "
         "hair, a light blue shirt and a navy tie standing behind a gray cubicle wall and leaning over it, looking down at "
         "a young Black woman with dark curly hair in a teal sweater with a red lanyard and headphones around her neck, "
         "seated at her desk in the foreground, computer monitor, cool greenish fluorescent tones",
         faces=[("office", "greg"), ("office", "maya")], seed=61, init="158.60",
         # his whole upper body: repainting only the head left two collars and ties
         inpaint=[region([(40, 170, 480, 570), (40, 565, 372, 835)], "a 45-year-old white man with short neatly combed "
                         "sandy blond hair, clean shaven, square jaw, light blue dress shirt and navy tie, standing behind "
                         "a cubicle wall in an open-plan office under fluorescent lights, looking down", 18, 1.0)],
         neg="woman, long hair, curly hair, two ties, extra arms"),
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
    # Close-ups from 2D frames keep cartoon proportions below ~0.9 strength; at 0.9 only the
    # pose survives (here the phones at their ears, from the two halves of the split screen).
    shot("sparrows_shoulder", f"close-up of {MAYA}, wearing a teal sweater with a red lanyard, at golden hour in a park, a "
         f"small brown sparrow perched on her shoulder, warm sunset light, soft bokeh, serene {CU}, looking slightly to the "
         "right", faces=[("sparrows", "maya")], ref="ref_maya", seed=82),

    # 4. the call
    shot("call_maya", f"close-up of {MAYA}, wearing a cozy lavender gray knit sweater, holding a smartphone to her ear, on a "
         "phone call, sitting on a sofa in her living room at night, warm table lamp light, bookshelf blurred behind her, "
         f"anxious {CU}", faces=[("call", "maya")], ref="ref_maya", seed=91, init="236.00", init_box=(0, 960, 1080, 1920),
         strength=0.9),
    shot("call_mom", f"close-up of {MOM}, holding a phone to her ear, on a phone call in her kitchen in the evening, warm "
         f"kitchen light, cabinets blurred behind her, tight {CU}", faces=[("call", "mom")], ref="ref_mom", seed=92,
         neg=MOM_NEG, init="236.00", init_box=(0, 0, 1080, 960), strength=0.9),
    shot("call_maya_after", f"close-up of {MAYA}, wearing a cozy lavender gray knit turtleneck sweater, sitting on a sofa at night holding a phone "
         f"in her lap, its screen softly lighting her face, warm lamp light, bookshelf blurred behind her, {CU}, "
         "looking down", faces=[("call", "maya")], ref="ref_maya", seed=94),

    # interlude: the road
    shot("road_night", "a lone young woman in a hoodie walking away from the camera down the middle of an empty country road "
         "at night, a small town glowing with warm lights on the horizon, starry deep blue sky, wide cinematic shot", seed=101),
    shot("road_dawn", "a lone young woman in a hoodie walking away from the camera down the middle of an empty country road "
         "at dawn, sunrise glowing golden on the horizon behind a small town, soft pink and gold sky, wide cinematic shot",
         seed=101),

    # epilogue
    shot("epi_two", "a bright modern office with large windows and green plants in morning sunlight, two coworkers side "
         "by side: on the left a South Asian woman in her thirties with a long dark braid over her shoulder, round glasses "
         "and an olive green sweater, on the right a young Black woman with dark curly hair in a rust orange sweater, "
         "warm natural light", faces=[("epilogue", "priya"), ("epilogue", "maya")], seed=111, init="291.60",
         inpaint=[region((365, 520, 745, 905), f"{MAYA}, no glasses, a rust orange sweater, in a bright office in morning "
                         "light, gentle expression, mouth closed", 17, 0.9, ref="ref_maya")], neg="glasses"),
    shot("epi_maya", f"close-up of {MAYA}, wearing a rust orange sweater, in a bright office with plants and windows, soft "
         f"morning light, gentle {CU}, looking slightly to the left", faces=[("epilogue", "maya")], ref="ref_maya", seed=112),
    shot("epi_window", f"close-up of {MAYA}, wearing a rust orange crew-neck sweater, standing by a window at sunrise, warm "
         "golden light on her face, a small brown sparrow perched on the windowsill beside her, city rooftops outside, "
         f"peaceful {CU}, looking slightly to the right", faces=[("epilogue", "maya")], ref="ref_maya", seed=113,
         init="307.00", strength=0.9),
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
