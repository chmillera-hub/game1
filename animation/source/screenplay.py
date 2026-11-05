# Screenplay: "A Table Instead of a Palace"
# ^word = high/hopeful musical accent, ~word = low/existential accent
# Each scene: id, mood (music), lead (s before first line), tail (s after last line)
# Each line: (speaker, text, gap_before_seconds)

SCENES = [
 dict(id='hook', mood='hill', lead=0.6, tail=0.5, lines=[
  ('TEO_VO', "What does a man look like... when he ^succeeds completely at everything his world asks of him?", 0),
 ]),
 dict(id='kitchen1', mood='kitchen', lead=0.5, tail=0.6, lines=[
  ('NOA', "Okay. Hear me out. David, then Solomon, then Jesus. It's ^one arc.", 0),
  ('NOA', "David's the emotional, musical one. Chill... unless he's defending somebody.", 0.3),
  ('TEO', "Your arc holds together. Honestly, ^better than you think.", 0.6),
  ('TEO', "But one piece needs an honest correction first.", 0.5),
  ('NOA', "Which piece?", 0.4),
  ('TEO', "Chill unless defending. The record is much more ~violent than that.", 0.4),
  ('TEO', "And including the violence makes your arc ^stronger. Not weaker.", 0.5),
  ('NOA', "Show me.", 0.7),
 ]),
 dict(id='gifted', mood='lyre', lead=0.6, tail=0.4, lines=[
  ('TEO_VO', "You're right that he was gifted. He played music for a troubled king.", 0),
  ('TEO_VO', "He loved his friend Jonathan with a ^bond deeper than brothers.", 0.4),
  ('DAVID', "I will dance before the Lord! I will become even more ^undignified than this!", 0.4),
  ('TEO_VO', "He danced with everything he had. And he wept. Openly. Without shame.", 0.4),
  ('DAVID', "How long, O Lord? Will you ~forget me forever?", 0.5),
 ]),
 dict(id='cheer', mood='drums', lead=0.4, tail=0.3, lines=[
  ('WOMEN', "Saul has struck down his thousands... and David, his ten thousands!", 0),
  ('TEO_VO', "His society ~rewarded him for killing. And they sang about it in the streets.", 0.5),
 ]),
 dict(id='raid', mood='dark', lead=0.6, tail=0.6, lines=[
  ('TEO_VO', "Living among the Philistines, he raided towns... and left no man or woman ~alive.", 0),
  ('TEO_VO', "So that no ~survivor could report what he had done.", 0.6),
 ]),
 dict(id='uriah', mood='dread', lead=0.5, tail=0.9, lines=[
  ('TEO_VO', "He took Bathsheba, the wife of Uriah, one of his own ^loyal soldiers.", 0),
  ('DAVID', "Set Uriah in the front of the hardest fighting. Then draw back from him, so that he is struck down.", 0.5),
  ('TEO_VO', "Uriah carried the letter himself. His own ~death, sealed, in his hand.", 0.5),
 ]),
 dict(id='abigail', mood='tension', lead=0.4, tail=0.5, lines=[
  ('TEO_VO', "Over an insult, he set out to kill Nabal, and every male in his house.", 0),
  ('ABIGAIL', "My lord, please. Do not carry the guilt of shedding ~blood without cause.", 0.4),
  ('DAVID', "Blessed be your ^wisdom. You kept me this day from bloodguilt.", 0.7),
  ('TEO_VO', "He stopped only because a woman stood in the road.", 0.4),
 ]),
 dict(id='temple', mood='somber', lead=0.5, tail=0.6, lines=[
  ('DAVID_OLD', "My son. I wanted to build a house for God.", 0),
  ('DAVID_OLD', "But God said to me: you shall not build it... because you have shed much ~blood.", 0.4),
 ]),
 dict(id='deathbed', mood='somber', lead=0.5, tail=0.7, lines=[
  ('DAVID_OLD', "Joab. Do not let his gray head go down to the grave in peace.", 0),
  ('DAVID_OLD', "And Shimei... bring his gray head down with ~blood.", 0.5),
  ('TEO_VO', "Even dying, the sword was the last thing he handed his son.", 0.6),
 ]),
 dict(id='kitchen2', mood='kitchen_sad', lead=0.6, tail=0.6, lines=[
  ('NOA', "So... he wasn't chill.", 0),
  ('TEO', "He did exactly what his society told him. And he was ^excellent at it.", 0.5),
  ('TEO', "What it told him included killing. And people ~cheered.", 0.4),
  ('NOA', "So David is what it looks like... when someone wins the whole program.", 0.8),
  ('TEO', "Completely. And then... there's the kid who grew up inside that win.", 0.5),
 ]),
 dict(id='childhood', mood='musicbox', lead=0.5, tail=0.5, lines=[
  ('TEO_VO', "Solomon was born to Bathsheba after Uriah was killed. Their first child had ~died.", 0),
  ('TEO_VO', "He grew up in a house where his brother Amnon raped his sister Tamar.", 0.5),
  ('TEO_VO', "Where Absalom killed Amnon for it. Then rebelled against their father... and died in the revolt.", 0.5),
  ('DAVID_CRY', "O my son Absalom! My son, my son! If only I had died instead of you!", 0.4),
  ('TEO_VO', "On the surface: a palace. A beloved king. Wealth. God's ^favor.", 0.6),
  ('TEO_VO', "Underneath: a father brilliant in public... who could not stop the ~destruction inside his own home.", 0.3),
  ('SOLOMON_CHILD', "Something's wrong here. And nobody will say what it is.", 0.6),
 ]),
 dict(id='empire', mood='grand', lead=0.4, tail=0.4, lines=[
  ('TEO_VO', "Then Solomon got everything. At a scale nobody else ever got.", 0),
  ('TEO_VO', "Wisdom. Wealth. Buildings. Gardens.", 0.3),
  ('TEO_VO', "Seven hundred wives. Three hundred concubines.", 0.2),
  ('TEO_VO', "Forced labor. International fame.", 0.2),
  ('TEO_VO', "If more were the answer, he would have been the ^happiest man in history.", 0.4),
 ]),
 dict(id='hevel', mood='empty', lead=0.8, tail=0.6, lines=[
  ('SOLOMON', "~Vanity of vanities. All is ~vanity.", 0),
  ('TEO_VO', "The Hebrew word is hevel. Vapor. Breath. Something you can't grab.", 0.6),
  ('SOLOMON', "I made great works. I built houses. I planted vineyards for myself...", 0.4),
  ('SOLOMON', "and behold, all was vanity, and a striving after ~wind.", 0.2),
  ('SOLOMON', "So I ~hated life.", 0.8),
  ('TEO_VO', "Tradition says Solomon wrote it. Many scholars think a later writer took on his voice. Either way... it's the report from the top.", 0.6),
 ]),
 dict(id='passage', mood='passage', lead=0.6, tail=0.8, lines=[
  ('SOLOMON', "There is one who has no other. No son. No brother. Yet there is no end to all his toil... and his eyes are never satisfied with riches.", 0),
  ('SOLOMON', "^Two are better than one.", 0.8),
  ('SOLOMON', "For if they fall, one will ^lift up his fellow.", 0.4),
  ('SOLOMON', "But woe to him who is ~alone when he falls, and has not another to lift him up.", 0.5),
  ('SOLOMON', "If two lie together, they keep ^warm. But how can one keep warm alone?", 0.5),
  ('SOLOMON', "A ^threefold cord is not quickly broken.", 0.7),
 ]),
 dict(id='kitchen3', mood='kitchen_hope', lead=0.5, tail=0.6, lines=[
  ('NOA', "That's... the door test.", 0),
  ('TEO', "The man with everything says the emptiness is endless toil, with nobody beside you.", 0.4),
  ('TEO', "Woe to him who is alone when he falls. That's the person on the floor... with zero doors to knock on.", 0.4),
  ('NOA', "Yeah. I know that floor.", 0.9),
  ('TEO', "I know you do.", 0.7),
  ('TEO', "Now watch what the Son of David does with all this.", 0.7),
 ]),
 dict(id='lilies', mood='warm', lead=0.5, tail=0.5, lines=[
  ('TEO_VO', "They called Jesus the Son of David. And he talked about Solomon directly.", 0),
  ('JESUS', "Consider the ^lilies of the field. Even Solomon in all his glory was not dressed like one of these.", 0.4),
  ('JESUS', "Something ^greater than Solomon is here.", 0.5),
 ]),
 dict(id='sword', mood='garden', lead=0.4, tail=0.6, lines=[
  ('TEO_VO', "From David, he kept the heart. The music. The raw prayer. The loyalty of a friend.", 0),
  ('PETER', "Lord, should we strike with the sword?", 0.4),
  ('JESUS', "Put your sword back in its place.", 0.5),
  ('JESUS', "^Love your enemies. Pray for those who persecute you.", 0.5),
  ('TEO_VO', "David's heart... with David's sword removed.", 0.5),
 ]),
 dict(id='richman', mood='warm_sad', lead=0.4, tail=0.6, lines=[
  ('TEO_VO', "From Solomon, he took the proof. That experiment had already been run to the maximum.", 0),
  ('JESUS', "Do not store up treasures on earth. Go, sell what you have, and come... ^follow me.", 0.4),
  ('TEO_VO', "More wealth. More buildings. More achievement. It ended in 'I ~hated life.' He didn't repeat it.", 0.8),
 ]),
 dict(id='table', mood='warm_full', lead=0.5, tail=0.6, lines=[
  ('TEO_VO', "Instead of a palace, he built this. Twelve people walking together. Eating ^together. Sleeping outside together.", 0),
  ('TEO_VO', "Shared meals. A shared purse. Touching lepers. Eating with outcasts.", 0.4),
  ('TEO_VO', "A group where nobody was ~alone when they fell.", 0.3),
  ('JESUS', "^Love one another, as I have loved you.", 0.6),
  ('JESUS', "Where two or three are gathered in my name, there I am among them.", 0.6),
  ('TEO_VO', "Two. ^Three. A threefold cord. A village... embodied.", 0.5),
 ]),
 dict(id='ending', mood='ending', lead=0.5, tail=3.2, lines=[
  ('NOA', "A cord of three... instead of a crown.", 0),
  ('TEO', "A ^table instead of a palace.", 0.5),
  ('AMI', "Hey. I didn't call first. Is that okay?", 2.6),
  ('NOA', "It's ^more than okay. Come in.", 0.7),
  ('TEO_VO', "Two are better than one. And a threefold cord... is not quickly ^broken.", 1.4),
 ]),
]

# voice casting: model, speaker id, length_scale, pitch factor, fx
# All voices are redistributable (see production/AUDIO.md):
#   joe-medium CC0 | john-medium public domain (LibriVox) | libritts_r CC BY 4.0 | northern_english_male CC BY-SA 4.0
VOICES = {
 'TEO':        ('en_US-john-medium', None, 1.02, 1.0, 'room'),
 'TEO_VO':     ('en_US-john-medium', None, 1.04, 1.0, 'vo'),
 'NOA':        ('en_US-libritts_r-medium', 20, 1.04, 1.0, 'room'),
 'DAVID':      ('en_US-joe-medium', None, 1.02, 1.0, 'hall'),
 'DAVID_OLD':  ('en_US-libritts_r-medium', 50, 1.25, 0.95, 'hall'),
 'DAVID_CRY':  ('en_US-joe-medium', None, 1.12, 1.0, 'cave'),
 'ABIGAIL':    ('en_US-libritts_r-medium', 40, 1.15, 1.0, 'open'),
 'WOMEN':      ('CHORUS', None, 1.15, 1.0, 'open'),
 'SOLOMON':    ('en_US-libritts_r-medium', 43, 1.32, 0.97, 'hall'),
 'SOLOMON_CHILD': ('en_US-libritts_r-medium', 57, 1.15, 1.12, 'whisper'),
 'JESUS':      ('en_GB-northern_english_male-medium', None, 1.25, 1.0, 'open'),
 'PETER':      ('en_US-libritts_r-medium', 31, 1.15, 1.0, 'open'),
 'AMI':        ('en_US-libritts_r-medium', 22, 1.02, 1.0, 'room'),
}
CHORUS = [('en_US-libritts_r-medium', 4), ('en_US-libritts_r-medium', 9), ('en_US-libritts_r-medium', 12),
          ('en_US-libritts_r-medium', 18), ('en_US-libritts_r-medium', 29), ('en_US-libritts_r-medium', 54)]
