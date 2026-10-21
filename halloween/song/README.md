# CLICKETY-CLACK (The Skeletons Are Back)

An original spooky Halloween sing-along music video (portrait 1080×1920, 2:28)
set in the same moonlit garden as *TOO MOM*. At midnight four skeletons climb
out of their graves to dance and sing. The black cat on the fence is not
impressed, and the pencil mice from the drawing watch from the kitchen window
before running out to join the last choruses. Then a rooster crows, and the
sunrise turns the whole band back into a pile of bones... until next year.

The finished video is `out/clickety_clack.mp4` (H.264 + AAC, under 15 MB). The
first frame is the title shot, with four glowing skulls peeking out of their
graves (no fade from black).

## The cast

| Character | Look | Voice |
| --- | --- | --- |
| **Rattles** (lead) | bowler hat | sung lead |
| **Femurella** | pink flower | duet in verse 2 |
| **Big Clatter** | biggest, striped knitted scarf | spoken bridge, his ribs are the xylophone |
| **Tibbs** | tiny, pumpkin treat bucket | "If you dare!" |
| The Cat | skinny black cat on a fence post | "Ugh. What's all the clatter?" |
| The Pencil Mice | from the drawing | "If you dare!", "Yeah!" |

## Lyrics (words and melody written for this project)

> *Cat:* Psst. It's midnight. ...Listen...
>
> **Verse 1** (Rattles)
> Down in the garden where the pumpkins grow,
> something's knocking on the dirt below...
> Knock, knock! Who's there? Can you guess who?
> A bony little hand, and it's waving at you!
>
> **Pre-chorus**
> Up pops a foot, then a bony knee,
> then a grinning skull, and it's grinning at me!
>
> **Chorus** (everybody)
> Clickety-clack! Clickety-clack!
> The skeletons are back with a rattle and a snap!
> Clickety-clack! Don't you be scared,
> grab a bony hand, if you dare! — *If you dare!*
>
> **Verse 2** (Rattles & Femurella)
> They haven't got a tummy, so they can't eat sweets,
> they just rattle at the doors when you shout trick or treat!
> They haven't got a nose, but they love to sniff the air,
> and they never need a comb, 'cause they haven't any hair!
>
> Their bony knees go knockity-knock!
> *Cat:* Ugh. What's all the clatter?
>
> **Chorus**
>
> **Bridge** (Big Clatter, spoken)
> Now some folks scream, and some folks run,
> but a skeleton just wants to have some fun!
> So wiggle your fingers, and wobble your knees,
> and... FREEZE! ... Unfreeze!
>
> *(xylophone solo, played on Big Clatter's ribs)*
>
> **Chorus** ×2 (up a half step, the mice join in)
>
> *Rooster.* Rattles: Uh-oh... sunrise. *(clatter)* ... Same time next year?
> Mice: Yeah!

## How it is made

Everything is generated from code, with no stock art, samples or recordings.
The puppets, fonts and helpers from *TOO MOM* (`../gfx.py`, `../mice.py`,
`../cat.py`, `../sets.py`, `../subs.py`, `../synth.py`) are reused.

| Step | File | What it does |
| --- | --- | --- |
| Song | `score.py` | Tempo, form, chords, melody tokens (`SYL\|NOTE\|BEATS`), spoken lines |
| Singing | `sing.py` | Kokoro TTS speech → syllables → WORLD vocoder re-pitched onto the melody (vibrato, scoops, consonants kept crisp) |
| Vocals | `vocals.py` | Lead, gang (4–5 voices, octaves), kids and spoken stems + `lyrics.json` word timings |
| Band | `band.py` | Swing oom-pah band: drums, tuba, organ, brass, theremin, bone xylophone, SFX; vocal-aware ducking and mix |
| Puppets | `skeleton.py` | Bone rig with IK legs and arms, skull with jaw, brows, blinks and glowing pupils; hat, flower, scarf, bucket, mallet |
| Set | `garden.py` | Moonlit garden, mounds, fence, crooked house; dawn |
| Video | `mv.py` | Choreography, lyric-cued gags, lip-sync from the vocal stems, shot list, karaoke lyrics, render |

Rebuild (from this folder; Python 3.12+, ffmpeg with libx264 + librubberband):

```bash
pip install kokoro misaki[en] soundfile scipy skia-python numpy pyworld
python3 vocals.py                 # sings every line (cached in build/cache)
python3 band.py                   # band + mix -> build/song_mix.wav
PYTHONHASHSEED=0 python3 mv.py --workers 4
cd .. && python3 encode.py --build song/build --chunks mv_chunks --mix song_mix.wav \
    --outdir song/out --audio-kbps 128 --limit 0.66 --static-gain --name clickety_clack.mp4 --title "Clickety-Clack"
```

## Notes

- The singing is synthesized: speech from a TTS model, re-pitched note by
  note. It is in tune and on the beat, but some sung words are less clear
  than real singing, so the karaoke lyrics are always on screen.
- Inspired by the *feel* of classic Halloween skeleton songs, but the title,
  words, melody, chords and arrangement are all original. No characters,
  lyrics or music from any existing song or film are used.

## Credits & licences

- Voices: [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (Apache-2.0)
- Fonts: Fredoka and Griffy (SIL Open Font License, see `../assets/fonts/OFL_*.txt`)
- Song, art, animation, music and sound design: generated for this project
