# who: n narrator (first person), m the mind-alien, k the knight, r the ranger, p the parasite
SCENES = [
 {"id":"title","pre":0.8,"post":1.0,"items":[
   {"who":"n","tag":"n_title","text":"The Parasite Problem."}]},
 {"id":"couch","pre":0.5,"post":0.6,"items":[
   {"who":"n","tag":"c1","text":"So I was watching some cutscenes from Baldur's Gate 3, the video game, and an idea immediately crawled into my head."},
   {"who":"n","gap":0.5,"tag":"c2","text":"Picture some creepy alien putting a parasite into a couple of people's brains. A little tadpole, meant to slowly transform them into more copies of the alien. More mind flayers, or something like that."}]},
 {"id":"ship","pre":0.5,"post":0.6,"items":[
   {"who":"m","tag":"m1","text":"Hold still. Do not struggle. You are going to become... more."},
   {"silence":1.6,"tag":"implant"},
   {"who":"n","gap":0.3,"tag":"s1","text":"Nobody asked. Nobody consented. Their bodies, their minds, their boundaries, all violated, by something creepy as heck."}]},
 {"id":"wake","pre":0.5,"post":0.2,"items":[
   {"who":"n","tag":"w1","text":"Later, two survivors wake up in the wreckage. A knight and a ranger. Total strangers. And each one knows the other is carrying a monster in their skull."},
   {"who":"r","gap":0.6,"tag":"r1","text":"You've got one of those things in your head too. Which means you'll turn into one of them."},
   {"who":"k","gap":0.4,"tag":"k1","text":"Whoa. Hold on. Let's talk about this."},
   {"who":"r","gap":0.3,"tag":"r2","text":"Sorry. Better I end this now."},
   {"silence":0.8,"tag":"leap"}]},
 {"id":"freeze","pre":0.0,"post":0.8,"items":[
   {"silence":1.0,"tag":"stop"},
   {"who":"p","gap":0.1,"tag":"p1","text":"No. Not this one. This one is ours."},
   {"who":"n","gap":0.6,"tag":"f1","text":"And the parasite stops her. Mid swing. Her arm just won't move."},
   {"who":"n","gap":0.5,"tag":"f2","text":"So now the vibe is: this parasite prevented a death. But for a selfish-as-heck reason. It doesn't want to kill another parasite. It wants more mind flayers."}]},
 {"id":"boost","pre":0.5,"post":0.8,"items":[
   {"who":"n","tag":"b1","text":"And here's the other side effect. The parasite doesn't want to die either. It wants to incubate, to hatch, to transform its host. So it makes them stronger."},
   {"who":"p","gap":0.5,"tag":"p2","text":"Faster. Stronger. Keep the host alive. We need you ripe."},
   {"who":"n","gap":0.5,"tag":"b2","text":"Suddenly the two of them are fighting side by side. They feel stronger. And they feel less violent toward each other."}]},
 {"id":"scales","pre":0.5,"post":0.8,"items":[
   {"who":"n","tag":"q1","text":"Without the parasite, and without the creepy act of that alien, these two might have died. In combat, or by killing each other. They survived because of something disgusting."},
   {"who":"n","gap":0.7,"tag":"q2","text":"So, was the alien's act justified, in a pro-human framework?"},
   {"who":"n","gap":0.9,"tag":"q3","text":"I'd say no. Forcing a parasite into someone by violating their boundaries is still a horrible act, even if you can recognize the benefits afterward."}]},
 {"id":"camp","pre":0.5,"post":0.8,"items":[
   {"who":"n","tag":"a1","text":"So from the characters' point of view, the plan becomes: get these things out of our heads, while still benefiting from them in the meantime."},
   {"who":"k","gap":0.6,"tag":"k2","text":"We find a cure. We get these things out."},
   {"who":"r","gap":0.5,"tag":"r3","text":"Agreed. But maybe not before the next fight."}]},
 {"id":"money","pre":0.5,"post":0.8,"items":[
   {"who":"n","tag":"o1","text":"And that reminds me of the money system."},
   {"who":"n","gap":0.6,"tag":"o2","text":"You live inside money, and capitalism. So you're benefiting from the labor of other human beings, who are forced to work under penalty of starvation, or homelessness."},
   {"who":"n","gap":0.6,"tag":"o3","text":"I'm living in an apartment that was probably built on something close to slave labor. Eating food that was probably grown, or shipped, by that same forced labor."}]},
 {"id":"end","pre":0.5,"post":3.0,"items":[
   {"who":"n","tag":"e1","text":"So, like the knight and the ranger, I'm carrying a parasite I never agreed to. It keeps me fed. It keeps a roof over my head. And it is still a violation."},
   {"who":"n","gap":0.6,"tag":"e2","text":"And I'm trying to figure out a way to detach this parasite of money and coercion, before the whole world dysregulates from all of that forced labor."},
   {"who":"n","gap":0.9,"tag":"e3","text":"The parasite kept them alive. It still has to come out."}]},
]
