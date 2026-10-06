# Lab Partners

An animated series in four parts (2 to 4 minutes each) with voiceovers, sound effects, music and
subtitles. Boredom is a mad scientist, Doubt is a librarian, and Lord Vex is a villain with a heart that
keeps getting in the way.

| Part | File | Length |
|------|------|--------|
| 1: The Heist | `videos/part1-the-heist.mp4` | 2:19 |
| 2: Villain School | `videos/part2-villain-school.mp4` | 2:52 |
| 3: Vacation | `videos/part3-vacation.mp4` | 3:34 |
| 4: The Comedy Show | `videos/part4-the-comedy-show.mp4` | 4:00 |

**Part 1:** Vex tries to rob the lab. The music cuts the moment Boredom and Doubt look at him. Lifting the
vial brings on boss music. He fumbles it, makes a slow-motion dive and earns a golf clap. Then he finds out
they read his post on the evil lair forums.

**Part 2:** Vex asks the duo to support his identity as a villain. They become his secret mentors, approve
buildings for his robot rampage, and take his breakdown seriously. They write a master plan, and his heart
grows.

**Part 3:** His villain friends plan to wreck the lab. Boredom and Doubt leave for the Bahamas ("LOL"),
watch the news name Vex Master Villain, and clink glasses. Back at the office, Vex whines to them on a
video call, until his minion says "Uhh... sir?" and forgets to close the door.

**Part 4:** The council assigns Vex an heir. He swears off Boredom and Doubt and chases the car, the
money, the sitcom and the medals, while his smile shrinks. One phone call later, he finds that humor is
the answer. At the Villain Comedy Night, the stone-faced council doesn't laugh until a banana peel
changes everything.

Part 1 is family friendly: the villain says "Oh, fudge!" and "I'm toast!" instead of swearing. Part 4 still bleeps a few words, with `[BLEEP]` in the subtitles.

## Rebuilding

Reuses the pipelines in `../magic-show`, `../anger-dungeon`, `../redditor-existentialist` and
`../scripture-scenes`. `mgfx.py` holds the characters, props and sets; `maudio.py` adds sounds and
music; `mcommon.py` has shared helpers; `m1.py` to `m4.py` hold each part's script and choreography.

```bash
python3 build.py m1               # -> build/m1.mp4
python3 build.py m2 --timeline    # print beat timings
python3 build.py m3 --still 120   # render one frame
```
