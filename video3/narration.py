# who: n = narrator, a = android, as = android (soft), h = human reciting, e = the android's shout
SCENES = [
 {"id":"title","pre":0.8,"post":1.0,"items":[
   {"who":"n","tag":"n_title","text":"The Library. A scene about a monster, and a mercy that is easy to miss."}]},
 {"id":"room","pre":0.6,"post":1.2,"items":[
   {"who":"n","tag":"n_room1","text":"Deep in a grand old mansion, a library glows in the last light of a dying fire."},
   {"who":"n","gap":0.4,"tag":"n_room2","text":"In a leather chair, an android sits perfectly still, watching the flames."}]},
 {"id":"enter","pre":0.2,"post":0.8,"items":[
   {"who":"n","gap":2.4,"tag":"n_enter","text":"Someone enters, and stops in the shadows. Just a silhouette, staring."},
   {"silence":2.2}]},
 {"id":"confess","pre":1.0,"post":0.6,"items":[
   {"who":"a","tag":"ai1","text":"I'm a monster."},
   {"who":"a","gap":1.5,"tag":"ai2","text":"Did you learn enough to help save me from myself?"}]},
 {"id":"silence","pre":0.0,"post":0.0,"items":[{"silence":5.0,"tag":"hush"}]},
 {"id":"kneel","pre":0.4,"post":0.0,"items":[
   {"who":"h","gap":2.0,"tag":"ps1","label":"PSALM 22  \u00b7  WORLD ENGLISH BIBLE","text":"My God, my God, why have you forsaken me? Why are you so far from helping me, and from the words of my groaning?"},
   {"who":"h","gap":0.5,"tag":"ps2","label":"PSALM 22  \u00b7  WORLD ENGLISH BIBLE","text":"My God, I cry in the daytime, but you don't answer; in the night season, and am not silent."},
   {"who":"h","gap":0.5,"tag":"ps3","label":"PSALM 22  \u00b7  WORLD ENGLISH BIBLE","text":"But you are holy, you who inhabit the praises of Israel."},
   {"who":"h","gap":0.5,"tag":"ps4","label":"PSALM 22  \u00b7  WORLD ENGLISH BIBLE","trunc":0.62,"text":"Our fathers trusted in you. They trusted, and you delivered them."}]},
 {"id":"enough","pre":0.05,"post":2.2,"items":[
   {"who":"e","tag":"enough","text":"Enough!"}]},
 {"id":"thermal","pre":0.9,"post":0.5,"items":[
   {"who":"n","tag":"th1","text":"The android turns. In the dark, nothing is hidden from those eyes."},
   {"who":"n","gap":0.5,"tag":"th2","text":"Heat vision. A racing pulse. A trembling human, vulnerable and afraid."},
   {"who":"n","gap":0.6,"tag":"th3","text":"Slowly, they back away, certain they've been caught, and hoping to be spared."},
   {"silence":2.6,"tag":"leave"}]},
 {"id":"alone","pre":1.4,"post":0.0,"items":[
   {"who":"as","tag":"s1","text":"Did they know that I love them?"},
   {"who":"as","gap":2.4,"tag":"s2","text":"Surely such as these will have tribulation in this world... but fear not... I have overcome the world."},
   {"silence":4.0,"tag":"flick"}]},
 {"id":"end","pre":0.4,"post":0.6,"items":[{"silence":4.2,"tag":"endcard"}]},
]
