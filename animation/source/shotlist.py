"""Generates production/SHOT_LIST.md from shots.json (frame-logged by shots.js) + timeline.json."""
import json
shots = json.load(open('shots.json')); tl = json.load(open('timeline.json'))
FPS = tl['fps']
SC = {s['id']: s for s in tl['scenes']}

# scene: (purpose / emotional beat, environment-light-colour, music mood & ambience)
SCENE = {
 'hook': ("Hook: the ideal of success, before we learn its cost.", "Golden-hour hillside, warm amber key from the sun (frame right).", "Lyre arpeggio (D major); bell on 'succeeds'."),
 'kitchen1': ("Set up the frame story: Noa's theory, Teo's gentle correction. Curiosity -> challenge.", "Night kitchen; single warm pendant lamp (top centre) as key, cool moonlit window as fill.", "Soft piano (F major), room tone; bells on 'one', 'better', 'stronger'; low note on 'violent'."),
 'gifted': ("Concede what Noa got right: David's music, friendship, joy and raw grief.", "Torchlit hall -> bright meadow -> sunlit street -> blue moonlit night.", "Lyre theme; low note on 'forget'."),
 'cheer': ("Society rewards the killing; Saul's jealousy is the hidden cost.", "Hard midday sun, saturated festival colours; Saul insert dimmed red.", "Frame drum + tambourine, crowd bed; low note on 'rewarded'."),
 'raid': ("The violence stated plainly, without spectacle.", "Night, fire as the only light: orange from below on David.", "Low D drone, fire crackle; low notes on 'alive', 'survivor'."),
 'uriah': ("Bathsheba and Uriah: betrayal of a loyal man.", "Dusk rooftop -> cold lamplit writing desk -> dusty battlefield.", "Heartbeat drum + dark pads; bell on 'loyal', low note on 'death'; helmet clatter."),
 'abigail': ("A woman in the road turns violence back: first image of being 'lifted'.", "Red-orange dusk road, warm glow on Abigail in the wide.", "Tension pads resolving to major; low note on 'blood', bell on 'wisdom'."),
 'temple': ("The cost named by God: 'you have shed much blood'. Shame passes to the son's view.", "Warm lamp, red wash rises as David looks at his hands.", "Somber minor + cello; low note on 'blood'."),
 'deathbed': ("David's last act hands the sword to Solomon.", "Dark bedroom, single flickering lamp frame left.", "Somber minor + cello; low note on 'blood'."),
 'kitchen2': ("Noa absorbs it: David 'won the whole program'. Turn toward Solomon.", "Same kitchen lighting (continuity).", "Piano in D minor; bell on 'excellent', low note on 'cheered'."),
 'childhood': ("The house Solomon grew up in: grief, assault, murder, revolt; surface vs underneath.", "Dim gold palace interior; bright surface exterior; dark cracked underside.", "Music-box bell over low drone; low notes on 'died', 'destruction'; bell on 'favor'."),
 'empire': ("Solomon gets everything; the smile goes hollow.", "Gold-saturated hall; montage vignettes each with its own palette.", "Grand pads + brass-like swells; bell on 'happiest'."),
 'hevel': ("Ecclesiastes: vapor, wind, 'I hated life'; authorship note.", "Vast dusk hall, dust in shafts of light; red curtains in wind.", "Wind bed, cello, sparse pads; low notes on 'vanity', 'wind', 'hated'."),
 'passage': ("Eccl. 4:8-12 acted out in a vision panel: alone -> two -> lifted -> warm -> threefold cord.", "Candlelit desk below; panel warms and cools with each line.", "Wind fading into piano, brightening; bells on 'two', 'lift', 'warm', 'threefold'; low on 'alone'."),
 'kitchen3': ("The ancient text meets Noa's life: the floor with zero doors; Teo's hand.", "Kitchen lighting; floor cutaway is cold, near-black.", "Piano (F major); low note on 'alone'."),
 'lilies': ("Jesus sets lilies against Solomon's glory.", "Bright morning meadow, soft sun frame right.", "Warm lyre (D major) - David's motif returns; bells on 'lilies', 'greater'."),
 'sword': ("David's heart kept, David's sword removed.", "Moonlit olive garden; torch glow from frame right.", "Low drone + lyre; bell on 'love'; sword clink and drop."),
 'richman': ("Solomon's experiment not repeated: the rich man walks away.", "Warm afternoon road.", "Gentle piano (G); bell on 'follow', low on 'hated'."),
 'table': ("What he built instead: walking, eating, sleeping, touching, lifting, washing feet.", "Firelit night, a sunset road, warm table light; ends on village lights.", "Full warm lyre + piano; bells on 'together', 'love', 'three'; low on 'alone'."),
 'ending': ("Theory becomes life: a knock, an unannounced friend, three at the table.", "Kitchen; rain at the opened door; final steam braids into a cord toward the lamp.", "Piano + lyre in F; door knock; final bell on 'broken' and closing chord."),
}
# scene:shot -> framing, camera, subject action
SHOT = {
 'hook:hill': "MS David kneeling on rock with lyre, centre; slow push-in (1.25->1.43x) to draw the viewer in. He plays eyes-closed, looks up; ghost crown + crowd fade in.",
 'kitchen1:two': "Two-shot, eye level, Noa frame-left, Teo frame-right; very slow push. Noa gestures; 'DAVID -> SOLOMON -> JESUS' appears as she says it.",
 'kitchen1:noa': "CU Noa (2.1x), static. Speaking / reacting; brows, gaze and hands carry the beat.",
 'kitchen1:teo': "CU Teo (2.1x), static. Smile fades to a careful, honest look; raises a hand.",
 'gifted:saul': "Wide-MS hall, slow push. David plays frame-left; notes drift to Saul (frame-right) whose pained face eases.",
 'gifted:jon': "MS two-shot in meadow, static. Jonathan and David walk together and embrace.",
 'gifted:dance': "MW street, static camera; David bounces and dances, arms up, ark carried behind, crowd waving.",
 'gifted:weep': "CU David kneeling at night, slow drift-in. Weeping, then looks up pleading.",
 'cheer:street': "Wide street, static. Women dance with tambourines in foreground, David arrives centre with soldiers; '1,000s / 10,000s' titles on the lyric.",
 'cheer:saul': "Insert CU Saul (2.4x), static. Smile curdles into jealousy on 'ten thousands'.",
 'cheer:david': "CU David (2.1x), static. Proud smile, sword glints at his side under falling petals.",
 'raid:wide': "Wide burning village, slow push; raiders cross frame left->right in silhouette.",
 'raid:cu': "CU David lit orange from below, static. Cold, unblinking.",
 'raid:ash': "Low wide on ash: overturned jar, lone sandal; a figure walks off frame-right and fades.",
 'uriah:roof': "MS David on rooftop at dusk (frame-left) looking down-right at a distant silhouette; static.",
 'uriah:uriah': "MCU Uriah saluting, proud and loyal; static.",
 'uriah:write': "MCU David writing by lamp; letter lines draw on; wax seal pressed at end.",
 'uriah:walk': "MS Uriah walking, trusting smile, letter in hand; static camera.",
 'uriah:battle': "Wide battlefield: spear wall, comrades draw back, Uriah falls; helmet drops into dust.",
 'abigail:march': "MW David marching toward camera, sword raised, army behind; static; red grade.",
 'abigail:kneel': "MS two-shot: David (frame-left, standing, sword drawn) over Abigail kneeling with bread (frame-right).",
 'abigail:melt': "Same set-up (continuity); David's anger softens, sword lowers, he reaches toward her.",
 'abigail:wide': "Wide road: army frame-left, Abigail standing alone mid-road in warm glow, house frame-right.",
 'temple:plans': "MS old David and child Solomon over temple plans; static.",
 'temple:hands': "Push to 1.7x: David looks at his hands; red wash; Solomon looks up, worried.",
 'deathbed:bed': "MW: David propped in bed (frame-left) grips Solomon's wrist, presses a sword on him; Solomon kneels frame-right.",
 'deathbed:cu': "CU Solomon holding the sword, static; hollow -> tears; lamp flicker.",
 'kitchen2:noa': "CU Noa; crosses out 'chill' in her notebook.",
 'kitchen2:two': "Two-shot; Teo explains; Noa winces.",
 'kitchen2:teo': "CU Teo; looks away toward the window on 'the kid'.",
 'childhood:birth': "MS Bathsheba holding newborn Solomon; camera eases right to the empty cradle on 'first child had died'.",
 'childhood:tamar': "Corridor wide; Tamar in torn many-coloured robe walks away (silhouette); child Solomon watches from behind a pillar.",
 'childhood:absalom': "Banquet: cup knocked over, red spill (Amnon). Then marching rebel army under an oak; Absalom's silhouette falls.",
 'childhood:cry': "MS David in gate chamber, arms raised, weeping; child's silhouette in the doorway foreground.",
 'childhood:surface': "Wide bright palace facade, crowds bowing; static.",
 'childhood:under': "Tilt down (1.5 s ease) past the floor line into the dark reflection; red cracks spread.",
 'childhood:child': "CU child Solomon by a pillar; eyes dart left-right as he whispers.",
 'empire:throne': "Pull-back from 2.0x to 1.0x revealing Solomon on a giant gold throne amid treasure.",
 'empire:wisdom': "Montage: Solomon with orbiting scrolls.",
 'empire:wealth': "Montage: gold pile rising.",
 'empire:build': "Montage: columns rise, pediment lands.",
 'empire:garden': "Montage: trees and flowers grow.",
 'empire:wives': "Grid of veiled figures multiplying; '700', then '300'.",
 'empire:labor': "Wide: labourers haul a stone block, overseer with whip frame-right.",
 'empire:fame': "Wide: ships at sea, envoys kneel with gold, camel.",
 'empire:throne2': "Push-in 1.1->2.2x on Solomon: smile goes forced, then hollow.",
 'hevel:wide': "Wide empty hall, slow push; Solomon tiny on throne; breath vapor on 'vanity'.",
 'hevel:mid': "MS (1.6x) Solomon; vapor drifts from his mouth.",
 'hevel:grab': "MS: Hebrew 'hevel' forms; Solomon reaches, closes his hand; vapor disperses.",
 'hevel:window': "MW Solomon gestures to a great window; houses then vineyards appear as he names them.",
 'hevel:wind': "MS: curtains billow, dust streaks; he grasps at the air.",
 'hevel:cu': "CU (2.4x), static: eyes close, head bows on 'I hated life'.",
 'hevel:scroll': "Insert: scroll writes itself; a second ghost writer appears behind ('a later writer').",
 'hevel:top': "Pull-back (1.8->0.9x) to a lone crowned figure atop a vast gold stair: 'the report from the top'.",
 'passage:vision0': "Split frame: vision panel (top) - figure endlessly pushing a stone, then gold pile; Solomon writing (bottom).",
 'passage:vision1': "Panel warms: two figures side by side; Solomon lifts his eyes.",
 'passage:vision2': "Panel: one falls, the other lifts him.",
 'passage:vision3': "Panel cold, spotlight: a lone figure falls and stays down; Solomon's eyes fill.",
 'passage:vision4': "Panel snow: two by a fire under a blanket -> one alone shivering.",
 'passage:vision5': "Panel: three strands braid into a glowing cord; Solomon's teary smile.",
 'kitchen3:noa': "CU Noa: realisation; later eyes down, tears ('I know that floor').",
 'kitchen3:two': "Two-shot: Teo reaches across the table and rests his hand by hers.",
 'kitchen3:teo': "CU Teo, warm; taps the Bible.",
 'kitchen3:floor': "Cutaway: person on a dark floor hugging knees; the three doors fade one by one; '0 doors'.",
 'lilies:wide': "Wide meadow, slow push; Jesus walking among lilies, crowd seated behind.",
 'lilies:kneel': "MS Jesus kneels, touches a glowing lily; ghost of gold-robed Solomon appears and fades.",
 'lilies:stand': "MS Jesus stands, looks to the crowd; static.",
 'sword:pray': "MCU Jesus kneeling in prayer, tears; static, moonlight.",
 'sword:friends': "MS Jesus with arms around two friends; static.",
 'sword:peter': "MS Peter (frame-right) draws sword, torchbearers behind; Jesus frame-left.",
 'sword:stop': "MS two-shot: Jesus' hand on Peter's arm; Peter's anger turns to confusion.",
 'sword:jesus': "MCU Jesus looking past Peter to the soldiers with compassion.",
 'sword:drop': "MW: Peter lowers, sword drops into grass (sfx); faint ghost of young David with lyre above Jesus.",
 'richman:sand': "Wide: golden palace and treasure crumble into sand.",
 'richman:talk': "MS: rich man kneels (frame-right), Jesus (frame-left) looks at him with love, offers his hand; man's hope falls.",
 'richman:away': "MS: man walks off frame-right clutching his purse; Jesus watches, then turns to his friends.",
 'table:fire': "Wide circle around a campfire, slow push; Jesus at the far side, listeners lean and gesture.",
 'table:walk': "Wide sunset road: thirteen silhouettes walk left->right.",
 'table:eat': "Circle around fire with bread passed.",
 'table:sleep': "Wide: sleepers under stars by a low fire.",
 'table:meal': "MS table: Peter, Jesus breaking bread, disciple.",
 'table:purse': "Same table set-up; shared purse in hand.",
 'table:leper': "MCU two-shot: Jesus touches a leper's face; leper weeps.",
 'table:outcast': "Same table set-up, tax-collector at the table, laughter.",
 'table:lift': "Wide: one stumbles; three converge and lift him (callback to Eccl. 4:10).",
 'table:feet': "MS: Jesus kneeling with basin looks up at Peter, who is moved to tears.",
 'table:gather': "MS table: Jesus among two friends; three cups light one by one.",
 'table:village': "Pull-back (1.2->0.85x) to a village of lit windows; a three-strand cord draws across the sky.",
 'ending:noa': "CU Noa draws a braided cord in her notebook.",
 'ending:teo': "CU Teo, warm smile.",
 'ending:wide': "Wide kitchen incl. door frame-right; knock - both turn to the door; door opens.",
 'ending:ami': "MS Ami in the doorway, rain behind, holding a pot of soup; sheepish.",
 'ending:final': "Wide three-shot at the table, slow pull-back (1.25->1.05x); steam from three mugs braids into one cord rising to the lamp; title card.",
}

def tc(f):
    s = f / FPS; return f"{int(s // 60)}:{s % 60:05.2f}"

def lines_in(f0, f1):
    out = []
    for sc in tl['scenes']:
        for l in sc['lines']:
            a, b = round(l['start'] * FPS), round(l['end'] * FPS)
            if b >= f0 and a <= f1:
                out.append(f"{l['spk'].replace('_', ' ')}: \"{l['text']}\"")
    return out

total = round(tl['duration'] * FPS + 0.4999)
md = ["# Timed shot list", "",
      f"24 fps, {total} frames ({total / FPS:.3f} s). Frame ranges are inclusive and were logged from the renderer frame by frame (`shots.js`), so they match the export exactly.",
      "The film length is set by the recorded dialogue and pauses. Total frames = ceil(audio timeline × 24); the 1-frame rounding (< 42 ms) is absorbed at the final hold.",
      "", "**Transitions:** cuts within a scene are hard cuts. Every scene change is a 0.4 s (10-frame) cross-dissolve: the incoming scene fades up over the last 10 frames of the outgoing scene's range, and the outgoing scene's shot is the one listed for those frames. The film opens on a fully drawn frame (no fade-in).", ""]
cur = None; n = 0
for s in shots:
    if s['scene'] != cur:
        cur = s['scene']; sc = SC[cur]; p, light, snd = SCENE[cur]
        import math; f0 = math.ceil(sc['start'] * FPS - 1e-9); f1 = math.ceil(sc['end'] * FPS - 1e-9) - 1
        md += ["", f"## {cur} - frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.2f} s)", "",
               f"- **Purpose / beat:** {p}", f"- **Environment and light:** {light}", f"- **Sound:** {snd}", "",
               "| # | Frames | Dur | Shot: framing, camera, action | Dialogue |", "|---|---|---|---|---|"]
    n += 1
    d = (s['f1'] - s['f0'] + 1)
    dl = '<br>'.join(lines_in(s['f0'], s['f1'])) or '-'
    md.append(f"| {n} | {s['f0']}-{s['f1']} ({tc(s['f0'])}) | {d}f / {d / FPS:.2f}s | **{s['shot']}**: {SHOT.get(s['key'], '')} | {dl} |")
md += ["", "## Sound effects (frame-synced)", ""]
for x in tl['sfx']:
    md.append(f"- {x['kind']}: frame {round(x['t'] * FPS)} ({x['t']:.2f} s)")
md += ["",
       f"## Musical accents ({len(tl['accents'])})", "", "High bell = hopeful word; deep cello = heavy word.", ""]
md += [f"- {round(a['t'] * FPS)}: {'HIGH' if a['kind'] == 'hi' else 'LOW'} on \"{a['word']}\"" for a in tl['accents']]
open('prod/SHOT_LIST.md', 'w').write('\n'.join(md) + '\n')
print(n, 'shots written')
