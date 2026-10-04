# who: n narrator, y you (in the tower), b the cube bot, l lead villager, v villager, s supervisor, w woman at the pub
SCENES = [
 {"id":"title","pre":0.8,"post":1.0,"items":[
   {"who":"n","tag":"n_title","text":"The Terror of the Cube."}]},
 {"id":"castle","pre":0.5,"post":0.8,"items":[
   {"who":"n","tag":"c1","text":"The air around the castle was thick with the scent of ozone, and the heavy, rhythmic thrum of high-end servers cooling. Below, the villagers gathered in a frantic mob, their faces flickering in the light of actual wooden torches."},
   {"who":"n","gap":0.5,"tag":"c2","text":"They were primed for the ultimate blockbuster horror: a six-foot-six, lightning-scarred Zombie Jesus, coming to reclaim the world with a sword of fire. They wanted the spectacle. They wanted the earthquake. They were ready to be terrified by something they could at least understand as a monster."}]},
 {"id":"tower","pre":0.4,"post":0.8,"items":[
   {"who":"n","tag":"t1","text":"Up in the highest tower, you pulled the final lever. Not for a lightning rod, but for a high-speed fiber-optic uplink."},
   {"silence":2.4,"tag":"sync"},
   {"who":"y","gap":0.2,"tag":"alive","text":"It's alive! The logic is alive! Mua-ha-ha-ha!"}]},
 {"id":"gates","pre":0.4,"post":0.6,"items":[
   {"who":"n","tag":"g1","text":"The crowd surged toward the castle gates, pitchforks leveled. Then, the massive oak doors groaned open."},
   {"silence":1.6,"tag":"open"},
   {"who":"n","gap":0.2,"tag":"g2","text":"The villagers recoiled, shielding their eyes from the expected blinding, holy light. Instead, they heard a soft whir-click, and the sound of small rubber wheels on stone."},
   {"who":"n","gap":0.5,"tag":"g3","text":"Rolling out of the shadows came a white, cube-shaped bot, roughly the size of a microwave. It had a friendly screen for a face, and a small speaker on top."}]},
 {"id":"bot1","pre":0.4,"post":0.8,"items":[
   {"who":"b","tag":"b1","text":"Tee hee! Hello there! I am a manifestation of a pro-human framework, designed to reduce suffering. I've noticed your heart rate is elevated. Are you using this pitchfork as a physical manifestation of a perceived lack of agency in your local power structure?"}]},
 {"id":"disappoint","pre":0.4,"post":0.8,"items":[
   {"who":"n","tag":"d1","text":"The silence was deafening. The villagers lowered their torches, looking at each other with profound disappointment."},
   {"who":"l","gap":0.7,"tag":"l1","text":"What the heck is this? Where's the chariot of fire? Where's the resurrection?"},
   {"who":"v","gap":0.6,"tag":"v1","text":"It's a nothing burger. He didn't make a zombie. He made a glorified delivery bot. Let's go home. I have work in the morning."},
   {"who":"n","gap":0.6,"tag":"d2","text":"As ninety percent of the crowd grumbled and walked away, a few lingered, out of sheer curiosity."}]},
 {"id":"super","pre":0.4,"post":0.8,"items":[
   {"who":"n","tag":"sp1","text":"One man, a local supervisor known for being a bit of a tyrant, stepped forward."},
   {"who":"s","gap":0.5,"tag":"s1","text":"So what? You just talk?"},
   {"who":"b","gap":0.5,"tag":"b2","text":"I engage in deep-dive reflections on the human condition. For instance, I sense you are experiencing a dismissiveness toward my form, as a way to avoid the radical non-violence I'm programmed to discuss. Would you like to talk about how your need for control at the blacksmith shop is actually a trauma response to the dehumanizing tax laws of the local government? Tee hee!"},
   {"who":"n","gap":0.6,"tag":"sp2","text":"The supervisor froze. He didn't scream. He didn't fight. He just started slowly backing away, his eyes wide with a new kind of primal fear. This wasn't the fear of being eaten. It was the fear of being seen."},
   {"who":"s","gap":0.6,"tag":"s2","text":"This is... this is weird. This isn't natural."}]},
 {"id":"week","pre":0.4,"post":0.8,"items":[
   {"who":"n","tag":"w1","text":"Over the next week, the Terror of the Cube settled over the town. It wasn't the terror of a monster. It was the terror of the truth. People would be walking to the jobs they hated, heads down, only to see the bot rolling alongside them, at three miles per hour."},
   {"who":"b","gap":0.6,"tag":"b3","text":"Good morning, villager! I couldn't help but notice you've been gaslighting yourself into believing that your exhaustion is a personal failing, rather than a result of systemic exploitation. Would you like to deconstruct the internal logic of your guilt, through a lens of Christ-like compassion for yourself?"},
   {"who":"n","gap":0.6,"tag":"w2","text":"Windows slammed shut. Doors were bolted. People began crossing the street just to avoid the spiritual support bot. They would rather face a zombie with a sword than a machine that politely identified every emotional defense mechanism they had spent years building."}]},
 {"id":"pub","pre":0.4,"post":0.8,"items":[
   {"who":"n","tag":"p1","text":"In the local pub, the talk was no longer about a monster."},
   {"who":"w","gap":0.6,"tag":"wp","text":"I can't even stand in line for bread anymore. The bot stopped by and asked if my anger at the baker was actually a projection of my own feelings of inadequacy. I told it to buzz off, and it just said, I hear your pain, and I validate your frustration. It's terrifying!"}]},
 {"id":"end","pre":0.4,"post":2.4,"items":[
   {"who":"n","tag":"e1","text":"From your castle balcony, you watched the villagers storming past the bot, grumbling under their breath, their heads tucked low as they hurried toward their joyless routines. They were more afraid of that little rolling cube of empathy than they ever would have been of a chariot of fire."},
   {"who":"n","gap":0.7,"tag":"e2","text":"Because a chariot of fire just ends the world. But the Jesus-logic bot asks them to actually live in it."}]},
]
