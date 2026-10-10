# Ace and Blueberry: animated video

An animated video of Mom's picture book *Ace and Blueberry*, made for phones.

**Video file:** [`Ace_and_Blueberry.mp4`](Ace_and_Blueberry.mp4)

| | |
|---|---|
| Length | 3:14 |
| Format | Portrait 9:16, 720×1280, 24 fps |
| Codecs | H.264 (High) video and AAC stereo audio in MP4. Plays on any phone or platform |
| File size | 8.8 MB |
| Audio | Voice acting, original background music and sound effects. Loudness is normalized to −15 LUFS |
| Captions | Built into the picture, colour-coded by speaker |

`thumbnail.jpg` is a cover frame you can use as the upload thumbnail.

## How the story is told

Every page of the book is in the video, in the book's order:

1. **Title.** Polka dots, the wavy yellow and pink ribbons and the blue title, as on the book's cover.
2. **"Hi, Blueberry!" / "Hi, Ace!"** Blueberry rolls in on his purple ball. The wall has stars, as in the drawing.
3. **Roll fast, roll slow.** Blueberry zooms past with whooshes, rolls slowly, then visits Ace.
4. **"Ooch!"** Ace taps the ball, flinches and shakes her hand. Then a close-up of her sore, bitten nails.
5. **The baby brother.** A dream bubble shows him nibbling Ace's nails while she sleeps. Blueberry giggles, says "Hmmm…", thinks it over, a lightbulb goes on, and he says "Wear gloves to bed!"
6. **Gloves night.** The baby brother finds gloves and gives up ("Huh?"). In the morning her nails are fine, but her hands are too hot.
7. **Favorite color: blue.** Blueberry holds up the nail polish and paints each nail with a little "ding". The old gloves now hang on the wall.
8. **Blue nails night.** The baby brother takes a nibble and says "Yuck! Yucky!" The nails grow back over the days ("Look! No more ooches!").
9. **Every Tuesday after dinner.** A calendar page, then pink, green and rainbow nails.
10. **The End.** A stage with curtains, a tree and a red bow, as in the last drawing. Ace and Blueberry wave goodbye.

The characters are redrawn as smooth cartoons based on Mom's drawings. Ace has curly orange hair, blue-outlined eyes with big lashes and hoop earrings. Blueberry is a grey-and-cream hamster in a purple ball. The baby brother has spiky teal hair and a toothy grin. The characters blink, move their eyes and change expression. Their mouths move with their recorded lines.

**Small additions to the text.** These are short lines that suit a video: "Zoom, zoom!", "Nice and easy…", "Yahoo!", "Gloves? Okay, I'll try it!", "All done!", "Ooh! So pretty!", "Hooray! It worked!", "Look! No more ooches!", "Pink, please!", "Green, please!", "Ooh! All the colors!", "Thank you for your help, Blueberry!" and "Any time, Ace! That's what best friends are for." The baby brother also says three lines: "Nom nom…", "Huh?" and "Yuck! Yucky!". The narration otherwise follows the book closely.

## Changing things

Everything is generated from code, so changes are cheap:

| What | Where |
|---|---|
| Words, who says them, voices, pauses and timing | `story.py` |
| Pictures, animation and expressions for each scene | `render/scenes.js` |
| How the characters are drawn | `render/chars.js` |
| Rooms and backgrounds | `render/bg.js` |
| Props such as the lightbulb, nail polish, calendar and bow | `render/props.js` |
| Music and sound effects | `audio.py` |
| Captions, transitions and video output | `render/main.js` |

## Rebuilding

```bash
./build.sh            # full rebuild (first run downloads the voice model + fonts, ~350 MB)
SKIP_TTS=1 ./build.sh # reuse already-generated voices
```

`verify.py` uses speech recognition (faster-whisper) to check that each voice line is understandable. It needs `pip install faster-whisper`.

`node render/main.js sheet out.png 4 10 20 30` renders preview frames at the given times, in seconds.

## Credits

- **Story and original illustrations:** Mom
- **Voices:** [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) text-to-speech (Apache-2.0). The narrator voice is `af_heart`. Ace uses `af_bella`, Blueberry uses `am_michael` and the baby brother uses `am_puck`, each pitched up.
- **Music and sound effects:** original. They are synthesized in `audio.py`, with no samples.
- **Fonts:** Fredoka (SIL OFL 1.1) and Luckiest Guy (Apache-2.0), from Google Fonts.
