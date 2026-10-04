# who: n narrator, d Death, f the Father, j Jesus
SCENES = [
 {"id":"title","pre":0.8,"post":1.0,"items":[
   {"who":"n","tag":"n_title","text":"Death Takes a Service Call."}]},
 {"id":"ticket","pre":0.5,"post":0.6,"items":[
   {"who":"n","tag":"n1","text":"Imagine Death getting a service ticket for his next pickup."},
   {"who":"d","gap":0.6,"tag":"tk","text":"Oh, I got a service ticket for the next one. Let's see... thirty-something-year-old dude, named Jesus. Former carpenter. Should be located between two thieves. Alright, I'll go pick him up and bring him to the afterlife. Let's go."}]},
 {"id":"walk","pre":0.4,"post":0.7,"items":[
   {"who":"n","tag":"w1","text":"Death walks along the path to the cross, whistling, looking side to side, bored out of his skull. He checks his watch."},
   {"silence":2.0,"tag":"whistle"},
   {"who":"d","gap":0.3,"tag":"dogw","text":"Alright. I've got time to take the skull dog for a walk after this."},
   {"who":"n","gap":0.6,"tag":"kick","text":"He kicks a stone along in front of him, staring at his feet."},
   {"silence":1.2,"tag":"kicked"}]},
 {"id":"cross","pre":0.4,"post":0.8,"items":[
   {"who":"n","tag":"c1","text":"At the foot of the cross, Death stretches nice and wide, eyes closed. A little cough. Then he looks up at Jesus."},
   {"silence":0.7,"tag":"beat"},
   {"who":"n","gap":0.2,"tag":"c2","text":"And his jaw drops straight to the floor. A blinding, divine light fills his face."},
   {"who":"d","gap":0.8,"tag":"wtf","text":"What the actual... is going on? Hey, God! What are you doing?"},
   {"who":"f","gap":0.7,"tag":"thanks","text":"Thank you for picking up my Son."},
   {"who":"d","gap":0.6,"tag":"why","text":"What are you talking about? This is just some guy. Anybody could say he's the Son of God. Why this man? Can you please turn down the light?"},
   {"who":"f","gap":0.7,"tag":"see","text":"Ha, ha. Well... you'll see when you bring him up here. We can have a conversation."},
   {"who":"d","gap":0.9,"tag":"delay","text":"...It looks like I'm going to have to delay walking my skull dog."},
   {"who":"f","gap":0.7,"tag":"bring","text":"Oh, don't worry. You can walk your dog with him now. Bring him up."}]},
 {"id":"carry","pre":0.4,"post":0.8,"items":[
   {"who":"n","tag":"c3","text":"Death takes the Son of Man down from the cross. He weighs about a hundred times more than Death is used to."},
   {"who":"d","gap":0.6,"tag":"heck","text":"What the actual heck is going on?"},
   {"who":"n","gap":0.6,"tag":"thieves","text":"Death touches the feet of the thieves, and they vanish."},
   {"who":"d","gap":0.7,"tag":"hell","text":"Okay. Well, those guys went to hell, so at least they're out of the way."},
   {"who":"f","gap":0.7,"tag":"para","text":"No. Send them up to me. The Son of Man said they will be in Paradise as well."},
   {"who":"d","gap":0.8,"tag":"devil","text":"Gosh dang it. Now I have to go talk to the devil, and tell him to send those two back up to You."}]},
 {"id":"whisper","pre":0.4,"post":0.6,"items":[
   {"who":"n","tag":"nwh","text":"From his perch on Death's shoulder, Jesus whispers into his ear."},
   {"who":"j","gap":0.6,"tag":"will","text":"Thy will has been done."},
   {"who":"d","gap":1.0,"tag":"rules","text":"Oh, what the heck is going on now? This dude is breaking all the rules. I have no idea what's going on anymore. Alright. Here you go, Father."}]},
 {"id":"arrive","pre":0.4,"post":0.8,"items":[
   {"who":"n","tag":"thud","text":"Death vanishes in a cloud of smoke. And Jesus lands on the ground with a very loud thud."},
   {"who":"f","gap":0.9,"tag":"arise","text":"Arise, Son of Man! The one sent from heaven to save the world!"},
   {"who":"n","gap":0.7,"tag":"stand","text":"Jesus casually stands up, brushing the dust off his feet."},
   {"who":"j","gap":0.5,"tag":"ready","text":"Okay. You ready to take a walk, Death?"},
   {"who":"d","gap":0.6,"tag":"getdog","text":"Sure. Let me get my dog."}]},
 {"id":"dog","pre":0.4,"post":1.5,"items":[
   {"who":"n","tag":"rush","text":"The skull dog comes rushing in from the side, tongue hanging out, barking."},
   {"silence":1.0,"tag":"bark"},
   {"who":"d","gap":0.2,"tag":"precious","text":"Oh, come here, you precious thing."},
   {"who":"n","gap":0.7,"tag":"jump","text":"The dog runs right past Death, without even looking at him, and jumps into the arms of Jesus."},
   {"silence":1.2,"tag":"cuddle"},
   {"who":"d","gap":0.3,"tag":"walkdone","text":"Okay. Can we just get this walk done?"},
   {"who":"j","gap":0.7,"tag":"sure","text":"Sure, buddy."}]},
]
