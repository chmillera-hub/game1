# who: n narrator, j Jesus, jq Jesus (quiet), s lead soldier, t townsperson
SCENES = [
 {"id":"title","pre":0.8,"post":1.0,"items":[
   {"who":"n","tag":"n_title","text":"Jesus, and the Gauntlet That Everyone Wanted to Use Wrong."}]},
 {"id":"square","pre":0.5,"post":0.8,"items":[
   {"who":"n","tag":"sq1","text":"The square is packed so tight, the air feels electric. Soldiers, zealots, townspeople, revolutionaries, all staring at Jesus, who stands in the center, unarmed and radically nonviolent, with the Infinity Gauntlet glowing on his hand like a small sun."},
   {"who":"n","gap":0.5,"tag":"sq2","text":"Everyone expects carnage. Everyone expects judgment. Everyone expects the snap."}]},
 {"id":"demand","pre":0.3,"post":0.6,"items":[
   {"who":"s","tag":"dem","text":"Finally! Justice! End the wicked! End the traitors! End the sinners! End the ones who oppose us!"},
   {"silence":2.0,"tag":"roar"},
   {"who":"n","gap":0.1,"tag":"hum","text":"The gauntlet hums. Jesus lifts his hand. People brace for annihilation."}]},
 {"id":"snap","pre":0.3,"post":0.8,"items":[
   {"who":"n","tag":"n_snap","text":"He snaps."},
   {"silence":1.6,"tag":"pop"},
   {"who":"n","gap":0.1,"tag":"feast","text":"And then... a mountain of warm bread. Pitchers of wine. Baskets of figs and dates. A platter of roasted fish. And somewhere in the distance, the mosquito population drops by forty percent."},
   {"who":"j","gap":0.6,"tag":"dinner","text":"Dinner is served."}]},
 {"id":"stunned","pre":0.3,"post":0.6,"items":[
   {"who":"n","tag":"frozen","text":"The crowd freezes."},
   {"who":"t","gap":0.6,"tag":"what","text":"Wait... what?"},
   {"who":"j","gap":0.6,"tag":"worms","text":"I also reduced parasitic worms. Thought that might help. Anyway, grab a plate."},
   {"who":"n","gap":0.6,"tag":"story","text":"He sits down at the table he conjured, pours wine, breaks bread, and starts telling a story about a fishing trip with the disciples. Laughing, gesturing, ignoring the stunned silence around him."}]},
 {"id":"rage","pre":0.2,"post":0.5,"items":[
   {"who":"n","tag":"purple","text":"The lead soldier's face turns purple."},
   {"who":"s","gap":0.5,"tag":"abom","text":"This is an abomination! You wasted the gauntlet! You were supposed to destroy our enemies!"},
   {"who":"j","gap":0.6,"tag":"myguy","text":"My guy... I'm literally trying to feed you."},
   {"who":"s","gap":0.5,"tag":"taking","text":"We're taking the gauntlet. You're too weak to use it properly."}]},
 {"id":"flip","pre":0.2,"post":0.6,"items":[
   {"who":"n","tag":"flipn","text":"The soldiers stomp to the table, flip it over, kick loaves of bread across the dirt, and scream in his face."},
   {"who":"j","gap":0.7,"tag":"bro","text":"Bro. I have the Infinity Gauntlet. You don't think I already thought of this?"},
   {"who":"s","gap":0.5,"tag":"appr","text":"Apprehend him!"},
   {"who":"n","gap":0.3,"tag":"phase","text":"Guards grab Jesus by the arms. He phases straight through them, like mist. He resets the table with a relaxing energy, sits back down, and keeps telling the fish story."}]},
 {"id":"violence","pre":0.2,"post":0.6,"items":[
   {"who":"n","tag":"punch","text":"One soldier throws a punch. His fist goes straight through Jesus, and he tumbles into a pile of bread. Another lunges for a disciple, and his hand passes through like smoke."},
   {"who":"j","gap":0.7,"tag":"rule","text":"Are you done? I made it so you cannot make physical contact with anyone, unless you're acting in a pro-human, non-violent way. You can yell. You can complain. You can express your feelings. But you cannot touch anyone without consent."},
   {"who":"s","gap":0.5,"tag":"demonic","text":"This is demonic! This is dark magic! You're making us intangible!"},
   {"who":"j","gap":0.5,"tag":"harmless","text":"No. I'm making you harmless."}]},
 {"id":"leave","pre":0.2,"post":0.8,"items":[
   {"who":"n","tag":"storm","text":"The soldiers insist the gauntlet is cursed, and that preventing violence is somehow evil, and they storm out of the city. A few people panic, and follow them. Most stay."},
   {"who":"jq","gap":0.7,"tag":"someday","text":"Maybe someday they'll understand that violence isn't how you get what you want, in this kingdom."},
   {"who":"n","gap":0.6,"tag":"snap2","text":"He snaps again. The tablecloth straightens. The bread reassembles. The wine refills. The disciples laugh. The feast continues."},
   {"who":"j","gap":0.5,"tag":"anyway","text":"So anyway, I was telling you about that fish..."}]},
 {"id":"metaphor","pre":0.4,"post":0.8,"items":[
   {"who":"n","tag":"m1","text":"So, what's the metaphor? The gauntlet is technology: a tool that prevents non-consensual harm, without inflicting harm."},
   {"who":"n","gap":0.5,"tag":"m2","text":"Jesus is the pro-human, non-violent framework: a presence that dissolves violence, instead of countering it."},
   {"who":"n","gap":0.5,"tag":"m3","text":"The soldiers believe power only matters when it can hurt someone, and they panic when they meet a power that refuses to."},
   {"who":"n","gap":0.5,"tag":"m4","text":"The phasing is consent-based interaction. You can talk, express, and disagree, but you cannot touch without consent."},
   {"who":"n","gap":0.5,"tag":"m5","text":"And the feast is the kingdom of heaven as abundance, not domination. A world where power nourishes, instead of destroys."}]},
 {"id":"end","pre":0.4,"post":1.0,"items":[
   {"who":"n","tag":"e1","text":"A Jesus who makes violence impossible, and uses infinite power to create infinite safety."},
   {"who":"n","gap":0.5,"tag":"e2","text":"A Jesus who refuses to disappear anyone, even the violent, because the point is transformation, not erasure."},
   {"silence":2.0,"tag":"fin"}]},
]
