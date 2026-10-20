# Builds script.json: the single source of truth for lines, shots, timing hints and music hits.
# Speakers: narrator (adult Mira, VO), keeper (android), directive (Keeper's internal system voice),
#           mira (girl, 9), grandpa.
# Line fields: id, speaker, text, vo (no lip movement), gap (silence before, s), speed, emotion,
#              notes: [{word, type: high|low}] -> musical hits on that word.
import json

def L(id, speaker, text, gap=0.35, speed=None, vo=False, emotion="", notes=()):
    d = {"id": id, "speaker": speaker, "text": text, "gap": gap, "vo": vo, "emotion": emotion,
         "notes": [{"word": w, "type": t} for (w, t) in notes]}
    if speed is not None:
        d["speed"] = speed
    return d

def S(id, scene, setting, framing, desc, lines=(), pad=0.4, tail=0.8, minDur=0, beats=(), mood=""):
    return {"id": id, "scene": scene, "setting": setting, "framing": framing, "desc": desc,
            "pad": pad, "tail": tail, "minDur": minDur, "mood": mood,
            "beats": list(beats), "lines": list(lines)}

shots = [
# ---------------- SCENE 1: SHORE (dawn) ----------------
S("s01a", 1, "dawn surf, tide line", "ECU face lying sideways in wet sand",
  "FIRST FRAME = this image, fully lit, no fade. Keeper lies cheek-down in wet sand, eyes closed, foam washing "
  "over the sand near the face. Dawn gold/pink light. Eyes flutter on 'Systems online', open slowly, iris rings "
  "light up amber. On 'Sand intrusion' grains slide off the cheek like water beads.",
  [L("s01a_1", "narrator", "The charts said the island was empty.", gap=0.6, vo=True, emotion="warm, wistful"),
   L("s01a_2", "narrator", "The charts were almost right.", gap=0.5, vo=True, emotion="small knowing smile",
     notes=[("right", "high")]),
   L("s01a_3", "directive", "Systems online. Solar intake, optimal. Sand intrusion, none.", gap=0.7, vo=True),
   L("s01a_4", "directive", "Primary directive:", gap=0.4, vo=True),
   L("s01a_5", "keeper", "Help... people.", gap=0.6, speed=0.8, emotion="hoarse whisper, first words",
     notes=[("Help", "high")])],
  pad=0.0, tail=0.6, mood="awakening"),
S("s01b", 1, "dawn beach", "MS, Keeper sitting up in the shallows, looking around",
  "Keeper pushes up to sitting, water streaming off. Turns head left, then right, scanning the empty shore. "
  "On 'Scanning' a translucent cyan HUD ring expands from Keeper across the beach. On 'zero' the ring fades out.",
  [L("s01b_1", "directive", "Scanning for people.", gap=0.5, vo=True),
   L("s01b_2", "directive", "People detected... zero.", gap=0.9, vo=True, notes=[("zero", "low")])],
  pad=0.6, tail=0.5, mood="uncertain"),
S("s01c", 1, "dawn beach", "CU Keeper face",
  "Reaction: brows rise slightly, then the INNER brows lift (worry); lips part; a slow blink; gaze drops to the sand, "
  "then drifts out to the empty horizon on the question.",
  [L("s01c_1", "keeper", "Zero.", gap=0.6, speed=0.85, emotion="quiet disbelief", notes=[("Zero", "low")]),
   L("s01c_2", "keeper", "Then who am I supposed to help?", gap=0.9, speed=0.9, emotion="lost, small voice",
     notes=[("help", "low")])],
  pad=0.3, tail=1.0, mood="lonely"),
S("s01d", 1, "island wide at sunrise", "EWS, tiny Keeper on an empty beach, island, endless ocean",
  "Title card fades in over the image: FOR SOMEONE, SOMEDAY (elegant serif, letter-spaced), holds, fades out. "
  "Sun crests the horizon, light spreads over the water. Gulls drift. No dialogue.",
  [], pad=0, tail=0, minDur=5.5, mood="title theme"),

# ---------------- SCENE 2: TIME (day) ----------------
S("s02a", 2, "bright morning beach", "MS Keeper standing, wind",
  "Keeper stands, lifts face to the sun. On 'sun feeds me' the dark-blue solar cells on its shoulders catch a "
  "glint and shimmer. On 'sand can't get in' a gust throws sand at it; the sand slides right off its skin/clothes.",
  [L("s02a_1", "keeper", "Day one. I don't need to eat. I don't need to sleep.", gap=0.4, vo=True,
     emotion="log entry, calm"),
   L("s02a_2", "keeper", "The sun feeds me, and the sand can't get in.", gap=0.4, vo=True,
     notes=[("sun", "high")])],
  pad=0.3, tail=0.5, mood="calm"),
S("s02b", 2, "rock above beach", "WS time-lapse",
  "Keeper sits motionless on a rock; time-lapse: sun arcs across the sky, shadows sweep around, clouds race, "
  "day->dusk->day. Keeper never moves.",
  [L("s02b_1", "keeper", "So I have time. More time than I know what to do with.", gap=0.3, vo=True,
     emotion="hollow", notes=[("time.", "low")]),
   L("s02b_2", "directive", "Recommendation: enter standby until people are detected.", gap=0.6, vo=True)],
  pad=0.4, tail=0.4, mood="empty"),
S("s02c", 2, "day beach", "MCU Keeper looking down at its own open hands",
  "Keeper looks at its hands, slowly opening and closing them. On 'never are' gaze lifts. On 'Efficient isn't' a "
  "small sad smile, slight head shake, an exhale (shoulders drop).",
  [L("s02c_1", "keeper", "And if they never are?", gap=0.5, speed=0.9, emotion="quiet"),
   L("s02c_2", "directive", "Then standby is efficient.", gap=0.6, vo=True),
   L("s02c_3", "keeper", "Efficient isn't the same as helpful.", gap=0.9, speed=0.9,
     emotion="small sad smile, gentle defiance")],
  pad=0.3, tail=0.8, mood="resolve begins"),

# ---------------- SCENE 3: CAPTAIN ----------------
S("s03a", 3, "tide line, close to sand", "insert, low angle",
  "A small orange hermit crab (cream spiral shell) is stuck on its back at the tide line, legs wiggling helplessly. "
  "A wave froths closer. No dialogue.",
  [], pad=0, tail=0, minDur=2.6, mood="light, curious"),
S("s03b", 3, "beach", "MCU Keeper notices",
  "Keeper glances down, eyes widen, brows shoot up, mouth opens; leans forward quickly.",
  [L("s03b_1", "keeper", "Oh! Hold on, little one.", gap=0.3, speed=1.0, emotion="sudden concern, tender",
     notes=[("Oh!", "high")])],
  pad=0.4, tail=0.3, mood="light"),
S("s03c", 3, "tide line", "insert, Keeper's fingers and the crab",
  "Keeper's fingers gently flip the crab upright. It scurries a few steps, stops, eye-stalks swivel back to "
  "look at Keeper.",
  [L("s03c_1", "directive", "That is not a person.", gap=1.4, vo=True)],
  pad=0.2, tail=0.5, mood="light"),
S("s03d", 3, "beach", "CU Keeper, head tilted",
  "Half-smile, one eyebrow raised, head tilt; on 'practice' a soft laugh with eyes squinting (lower lids up). "
  "On 'Captain' it looks down warmly; the crab raises a claw (cut-in is fine).",
  [L("s03d_1", "keeper", "It was stuck. It needed help. Close enough.", gap=0.3, emotion="wry, warm",
     notes=[("help.", "high")]),
   L("s03d_2", "directive", "Logging it as... practice.", gap=0.6, vo=True),
   L("s03d_3", "keeper", "Practice. I'll take it.", gap=0.5, emotion="soft laugh, first real smile",
     notes=[("take", "high")]),
   L("s03d_4", "keeper", "I'll call you Captain.", gap=0.6, emotion="fond")],
  pad=0.2, tail=1.0, mood="light, jazzy"),

# ---------------- SCENE 4: FOR WHOEVER COMES NEXT ----------------
S("s04a", 4, "beach, wind", "MCU Keeper looking at the horizon",
  "Wind in hair. Determination grows: brows lower and straighten, chin lifts, eyes narrow slightly, small firm smile "
  "on 'whoever comes next'.",
  [L("s04a_1", "keeper", "If no one is here now...", gap=0.3, speed=0.9, emotion="thinking",
     notes=[("now...", "low")]),
   L("s04a_2", "keeper", "then I'll help whoever comes next.", gap=0.3, emotion="resolved",
     notes=[("next.", "high")])],
  pad=0.3, tail=0.6, mood="resolve"),
S("s04b", 4, "mossy rocks in jungle shade", "insert, cupped hands at a spring",
  "Fresh water pours from a lip of rock into Keeper's cupped hands, overflowing and splashing (on 'pouring').",
  [L("s04b_1", "keeper", "I found fresh water, pouring out of the rocks.", gap=0.2, vo=True,
     notes=[("water,", "high")])],
  pad=0.3, tail=0.4, mood="montage"),
S("s04c", 4, "beach path", "insert, carving",
  "Keeper carves into a flat stone with a sharp shell: an arrow and 'WATER 40 PACES' appear stroke by stroke, "
  "chips flying, timed across the line.",
  [L("s04c_1", "keeper", "I carved the way to it, in stone.", gap=0.2, vo=True)],
  pad=0.2, tail=0.6, mood="montage"),
S("s04d", 4, "jungle edge", "MS two bushes",
  "Two bushes: blue berries and red berries. Keeper sets a marked stone at each: a check mark + 'EAT' by the blue "
  "(on 'heal'), an X + 'NO' by the red (on 'hurt').",
  [L("s04d_1", "keeper", "I marked which berries heal, and which ones hurt.", gap=0.2, vo=True,
     notes=[("heal,", "high"), ("hurt.", "low")])],
  pad=0.2, tail=0.5, mood="montage"),
S("s04e", 4, "clearing above the beach", "WS time-lapse hut build",
  "Hut build time-lapse: bamboo frame rises, palm-frond thatch layers on, a rain shower passes and the inside stays "
  "dry. Keeper moves fast in time-lapse.",
  [L("s04e_1", "keeper", "I built a roof that doesn't leak.", gap=0.2, vo=True)],
  pad=0.3, tail=0.5, mood="montage"),
S("s04f", 4, "reef / flat rock", "WS then insert of map",
  "Keeper stands waist-deep looking down at jagged coral under clear water; then a flat rock with a scratched map: "
  "island outline, reef as jagged marks, a safe channel arrow.",
  [L("s04f_1", "keeper", "And I mapped the reef, so no boat would ever break on it.", gap=0.2, vo=True,
     notes=[("break", "low")])],
  pad=0.3, tail=0.5, mood="montage"),
S("s04g", 4, "beach, afternoon", "CU Keeper pausing mid-carve",
  "Keeper's hand pauses. Eyes lower, a flicker of doubt (brows pinch), then the gaze lifts to the horizon and a "
  "firm small smile forms on 'Not yet'.",
  [L("s04g_1", "directive", "None of this is being received.", gap=0.4, vo=True, notes=[("None", "low")]),
   L("s04g_2", "keeper", "Not yet.", gap=1.1, speed=0.85, emotion="quiet conviction", notes=[("yet.", "high")])],
  pad=0.3, tail=1.2, mood="hope"),

# ---------------- SCENE 5: THE LIGHT (night) ----------------
S("s05a", 5, "night, stars, black sea", "WS island silhouette at night",
  "Night. Stars, black ocean, island dark. Keeper stands on the rocky point, only its eyes glow. On 'a ship could "
  "pass' a distant ship's tiny light slides along the horizon, unaware, and vanishes.",
  [L("s05a_1", "keeper", "But at night, the island disappears.", gap=0.3, vo=True, notes=[("disappears.", "low")]),
   L("s05a_2", "keeper", "A ship could pass a mile away, and never know there was water here.", gap=0.4, vo=True),
   L("s05a_3", "keeper", "A roof. A way through.", gap=0.3, vo=True)],
  pad=0.5, tail=0.6, mood="dark"),
S("s05b", 5, "night, point", "MCU Keeper opening chest panel",
  "Keeper opens a panel on its chest: glowing gold-cyan power cells light its face from below. Brows knit, "
  "hesitation, hand trembles; it pulls one cell out (on 'shorten'). On 'stay awake forever' it looks at the cell; "
  "on 'The light does' it looks up toward the tower.",
  [L("s05b_1", "directive", "Warning. Removing a power cell will shorten your operational life by sixty-one percent.",
     gap=0.6, vo=True, notes=[("shorten", "low")]),
   L("s05b_2", "keeper", "I don't need to stay awake forever.", gap=0.8, speed=0.9, emotion="steady, quiet"),
   L("s05b_3", "keeper", "The light does.", gap=0.6, speed=0.88, emotion="certain", notes=[("light", "high")])],
  pad=0.4, tail=0.5, mood="sacrifice"),
S("s05c", 5, "night, stone tower on the point", "WS low angle tower",
  "A stacked-stone tower (cairn lighthouse) with a lantern housing on top. Keeper places the glowing cell in; light "
  "blooms, a warm beam begins to sweep across the sea. BIG music swell.",
  [L("s05c_1", "directive", "For the record... that was not efficient.", gap=2.6, vo=True)],
  pad=0.2, tail=0.4, mood="swell"),
S("s05d", 5, "night, point, beam sweeping", "CU Keeper lit by passing beam",
  "Beam sweeps across Keeper's face periodically. Soft smile, eyes half-lidded, content.",
  [L("s05d_1", "keeper", "No. It was helpful.", gap=0.4, speed=0.9, emotion="soft smile", notes=[("helpful.", "high")])],
  pad=0.3, tail=1.4, mood="warm"),

# ---------------- SCENE 6: YEARS ----------------
S("s06a", 6, "same composition: hut, tower, palm sapling", "WS time-lapse years",
  "Day/night cycling fast; storms; the sapling grows into a tall palm; Keeper repairs the tower; clothes fade. "
  "On-screen log counter (HUD style) reads DAY 400, DAY 2,000, DAY 7,300 as each is spoken.",
  [L("s06a_1", "keeper", "Day four hundred. No ships.", gap=0.3, vo=True, speed=0.92),
   L("s06a_2", "keeper", "Day two thousand. Still no ships.", gap=0.7, vo=True, speed=0.9, notes=[("Still", "low")]),
   L("s06a_3", "keeper", "Day seven thousand, three hundred.", gap=0.8, vo=True, speed=0.85)],
  pad=0.4, tail=0.6, mood="time passing"),
S("s06b", 6, "night rain, hut doorway", "MCU Keeper sitting in hut doorway, rain",
  "Rain pours. Keeper sits in the doorway, Captain the crab beside it. Raindrops run down its cheeks like tears. "
  "After 'Insufficient data' it closes its eyes, lips press together, shoulders drop.",
  [L("s06b_1", "keeper", "Directive... if no one ever comes...", gap=0.4, speed=0.85, emotion="tired, aching",
     notes=[("ever", "low")]),
   L("s06b_2", "keeper", "was any of it help?", gap=0.4, speed=0.85, emotion="breaking", notes=[("help?", "low")]),
   L("s06b_3", "directive", "Insufficient data.", gap=1.3, vo=True)],
  pad=0.5, tail=1.8, mood="grief"),
S("s06c", 6, "morning after rain", "MS Keeper looking up at a tall palm tree",
  "Morning light. Keeper stands, looks up at the tall palm it planted on day one (now towering).",
  [L("s06c_1", "keeper", "I planted that tree on my first day.", gap=0.3, speed=0.92, emotion="remembering"),
   L("s06c_2", "keeper", "It never knew who would sit in its shade. It just grew anyway.", gap=0.5, speed=0.92,
     notes=[("grew", "high")])],
  pad=0.5, tail=0.5, mood="dawning hope"),
S("s06d", 6, "morning, palm shade", "CU Keeper realization",
  "Realization: eyes lift, brows relax and rise gently, a slow small smile, eyes glisten.",
  [L("s06d_1", "keeper", "Maybe that's what help is.", gap=0.3, speed=0.9, emotion="realizing"),
   L("s06d_2", "keeper", "Not only for the people who are here...", gap=0.4, speed=0.9),
   L("s06d_3", "keeper", "but for the ones who matter, before you've even met them.", gap=0.3, speed=0.9,
     emotion="warm certainty", notes=[("matter,", "high")]),
   L("s06d_4", "directive", "Updating definition.", gap=1.0, vo=True)],
  pad=0.3, tail=0.8, mood="hope"),
S("s06e", 6, "dusk, base of the tower, facing the sea", "MS Keeper sitting down to rest",
  "Dusk. Keeper sits at the base of the tower facing the sea, Captain at its knee, beam sweeping overhead. "
  "On 'Keep the light on' it looks up at the beam; then its eye-glow dims, eyelids lower slowly, head bows. "
  "Then time-lapse: sand drifts over its shoulders, vines creep across, the beam keeps sweeping.",
  [L("s06e_1", "directive", "Power: four percent. Recommend standby.", gap=0.4, vo=True, notes=[("four", "low")]),
   L("s06e_2", "keeper", "Alright.", gap=0.8, speed=0.85, emotion="accepting, soft"),
   L("s06e_3", "keeper", "Keep the light on for me.", gap=0.9, speed=0.82, emotion="tender, fading",
     notes=[("light", "high")])],
  pad=0.4, tail=4.5, mood="power down"),

# ---------------- SCENE 7: STORM ----------------
S("s07a", 7, "night storm at sea", "MS small fishing boat in big waves",
  "Small wooden fishing boat tossed by huge waves, heavy rain, lightning flashes. Mira (girl, yellow raincoat) "
  "clings to the mast; Grandpa (white beard, navy knit cap) fights the tiller.",
  [L("s07a_1", "grandpa", "Hold on, Mira! Hold on to the mast!", gap=0.6, speed=1.05, emotion="shouting over storm"),
   L("s07a_2", "mira", "Grandpa! Look! A light!", gap=0.5, speed=1.05, emotion="shouting, hope",
     notes=[("light!", "high")]),
   L("s07a_3", "grandpa", "Out here? There's nothing out here...", gap=0.4, emotion="disbelief")],
  pad=0.3, tail=0.2, mood="storm"),
S("s07b", 7, "night storm, boat", "CU Grandpa face lit by the passing beam",
  "The warm beam sweeps across Grandpa's wet face; his eyes widen, mouth falls open, then a disbelieving smile.",
  [L("s07b_1", "grandpa", "There is now.", gap=0.9, speed=0.9, emotion="awe", notes=[("now.", "high")])],
  pad=0.3, tail=0.6, mood="storm hope"),
S("s07c", 7, "storm, reef channel", "WS boat passing between jagged rocks",
  "The boat threads between jagged rocks; white-painted marker stones and a pole mark a safe channel, lit by "
  "the sweeping beam.",
  [L("s07c_1", "mira", "Rocks! But someone marked a path, look!", gap=0.3, speed=1.05, emotion="urgent, amazed")],
  pad=0.4, tail=0.8, mood="storm"),

# ---------------- SCENE 8: ARRIVAL (dawn after storm) ----------------
S("s08a", 8, "dawn after storm, beach", "MS Mira kneeling at the carved stone",
  "Boat beached behind. Mira traces the carved letters on the stone with a finger and reads, then jumps up and "
  "runs, counting.",
  [L("s08a_1", "mira", "Water... forty paces.", gap=0.5, speed=0.9, emotion="reading slowly"),
   L("s08a_2", "mira", "One, two, three, four...", gap=0.3, speed=1.1, emotion="excited, running")],
  pad=0.3, tail=0.3, mood="wonder"),
S("s08b", 8, "jungle spring", "MCU Grandpa drinking from cupped hands",
  "Grandpa drinks from the spring from cupped hands, laughs and nearly cries with relief; looks around in wonder.",
  [L("s08b_1", "grandpa", "Fresh water.", gap=0.5, speed=0.9, emotion="relief, choked laugh"),
   L("s08b_2", "grandpa", "Someone made all this... for us?", gap=0.5, speed=0.9, emotion="wonder",
     notes=[("us?", "high")])],
  pad=0.3, tail=0.6, mood="wonder"),
S("s08c", 8, "inside the hut", "MCU Mira reading a carved stone on the wall",
  "Inside the dry hut, a carved stone hangs on the wall: IF YOU ARE READING THIS, YOU ARE NOT ALONE. Mira reads it "
  "aloud slowly; her lip trembles, eyes fill.",
  [L("s08c_1", "mira", "If you are reading this...", gap=0.5, speed=0.85, emotion="reading, soft"),
   L("s08c_2", "mira", "you are not alone.", gap=0.4, speed=0.8, emotion="voice catching",
     notes=[("alone.", "high")])],
  pad=0.4, tail=1.2, mood="tender"),

# ---------------- SCENE 9: KEEPER ----------------
S("s09a", 9, "morning, base of the tower", "WS Mira and Grandpa approach the dormant Keeper",
  "Keeper sits at the tower base, half-buried in sand, vines across it, old Captain the crab on its knee. "
  "Mira approaches carefully; Grandpa reaches out a hand to stop her.",
  [L("s09a_1", "grandpa", "Careful, Mira.", gap=0.4, speed=0.9, emotion="worried"),
   L("s09a_2", "mira", "It's okay. I think... it's been waiting.", gap=0.5, speed=0.9, emotion="gentle certainty")],
  pad=0.5, tail=0.5, mood="hush"),
S("s09b", 9, "morning", "insert, Mira's hand brushing the shoulder",
  "Mira's small hand brushes sand and leaves off the dusty solar cells on Keeper's shoulder. Sunlight hits them; "
  "they gleam; a soft chime.",
  [L("s09b_1", "directive", "Solar intake... restored.", gap=1.2, vo=True)],
  pad=0.2, tail=0.4, mood="rebirth"),
S("s09c", 9, "morning", "ECU Keeper eyes",
  "The amber iris ring flickers, relights; lids lift; pupils focus on Mira.",
  [L("s09c_1", "directive", "Scanning for people.", gap=0.3, vo=True),
   L("s09c_2", "directive", "People detected: two.", gap=0.9, vo=True, notes=[("two.", "high")])],
  pad=0.2, tail=0.6, mood="rebirth swell"),
S("s09d", 9, "morning", "CU Keeper face",
  "Brows lift, lips part, slight tremble, eyes glisten; hoarse voice.",
  [L("s09d_1", "keeper", "Hello.", gap=0.5, speed=0.8, emotion="hoarse, wonder"),
   L("s09d_2", "keeper", "Are you hurt? There's water, forty paces north...", gap=0.6, speed=1.0,
     emotion="urgent care")],
  pad=0.4, tail=0.3, mood="tender"),
S("s09e", 9, "morning", "CU Mira smiling with wet eyes",
  "Mira smiles through tears, nods.",
  [L("s09e_1", "mira", "We found it. We found everything.", gap=0.3, speed=0.95, emotion="smiling through tears"),
   L("s09e_2", "mira", "We followed your light.", gap=0.4, speed=0.9, notes=[("light.", "high")])],
  pad=0.3, tail=0.5, mood="tender"),
S("s09f", 9, "morning", "CU Keeper looks up at the tower, then back",
  "Keeper's eyes rise to the lantern above, then return to Mira; brows tilt up in the middle, lips quiver.",
  [L("s09f_1", "keeper", "It... helped?", gap=0.6, speed=0.85, emotion="fragile")],
  pad=0.6, tail=0.5, mood="tender"),
S("s09g", 9, "morning", "two-shot, Mira takes Keeper's hand",
  "Mira takes Keeper's hand in both of hers. Keeper's face: moved, a slow smile, eyelids lower, a drop slides down "
  "its cheek.",
  [L("s09g_1", "mira", "It saved us.", gap=0.3, speed=0.9, emotion="firm, loving"),
   L("s09g_2", "directive", "Directive status...", gap=1.0, vo=True),
   L("s09g_3", "directive", "complete.", gap=0.6, vo=True, notes=[("complete.", "high")])],
  pad=0.3, tail=1.4, mood="fulfillment"),
S("s09h", 9, "morning", "MCU Grandpa, cap in hand; then CU Keeper",
  "Grandpa has taken off his cap, holds it at his chest. Keeper answers, looking at Mira on 'getting ready'.",
  [L("s09h_1", "grandpa", "How long were you waiting out here?", gap=0.4, speed=0.9, emotion="gentle, humbled"),
   L("s09h_2", "keeper", "I wasn't waiting.", gap=0.6, speed=0.9, emotion="gentle"),
   L("s09h_3", "keeper", "I was getting ready.", gap=0.5, speed=0.9, emotion="warm smile",
     notes=[("ready.", "high")])],
  pad=0.3, tail=0.6, mood="warm"),
S("s09i", 9, "morning", "alternating CUs Mira / Keeper",
  "Name exchange. Mira earnest; Keeper a little shy; final smile with eyes closing briefly on 'Keeper.'",
  [L("s09i_1", "mira", "What's your name?", gap=0.3, speed=0.95),
   L("s09i_2", "keeper", "I never needed one. There was no one to call me anything.", gap=0.5, speed=0.9,
     emotion="matter-of-fact, a little sad", notes=[("no", "low")]),
   L("s09i_3", "mira", "Then you're Keeper. 'Cause you kept the light on.", gap=0.5, speed=0.92,
     emotion="decisive, beaming"),
   L("s09i_4", "keeper", "Keeper.", gap=0.8, speed=0.8, emotion="trying the name, smiling",
     notes=[("Keeper.", "high")])],
  pad=0.3, tail=1.4, mood="joy"),

# ---------------- SCENE 10: EPILOGUE ----------------
S("s10a", 10, "dusk, years later, point with tower", "WS tower, boats moored, two silhouettes",
  "Dusk years later: tower beam sweeping, a few boats moored in the cove, gardens; Keeper and Mira (older) "
  "silhouetted on the point, Captain at their feet.",
  [L("s10a_1", "narrator", "I was nine years old the night we followed that light.", gap=0.4, vo=True),
   L("s10a_2", "narrator", "The charts don't say the island is empty anymore.", gap=0.6, vo=True,
     notes=[("anymore.", "high")])],
  pad=0.4, tail=0.6, mood="reprise"),
S("s10b", 10, "dusk sea and horizon", "slow push toward the horizon, the beam passing overhead",
  "Slow push over the water toward the horizon as the beam sweeps out across the sea, a far boat light answers. "
  "Final title FOR SOMEONE, SOMEDAY appears on the last line and holds (do not fade to black).",
  [L("s10b_1", "narrator", "So if you're on an island of your own right now...", gap=0.4, vo=True,
     notes=[("island", "low")]),
   L("s10b_2", "narrator", "doing good that no one has seen yet...", gap=0.4, vo=True, notes=[("yet...", "low")]),
   L("s10b_3", "narrator", "keep the light on.", gap=0.6, vo=True, speed=0.85, notes=[("light", "high")]),
   L("s10b_4", "narrator", "Someone is on their way.", gap=0.8, vo=True, speed=0.85, notes=[("way.", "high")])],
  pad=0.3, tail=3.5, mood="finale"),
]

json.dump({"title": "For Someone, Someday", "fps": 24, "width": 720, "height": 1280, "shots": shots},
          open("script.json", "w"), indent=1)
n = sum(len(s["lines"]) for s in shots)
w = sum(len(l["text"].split()) for s in shots for l in s["lines"])
print(len(shots), "shots", n, "lines", w, "words")
