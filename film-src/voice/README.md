# The narrator's voice

The film is narrated line by line in the author's own words. The voice is generated with free, open-weight text-to-speech models that run locally. No paid service or API key is needed.

| Step | Tool | License |
| --- | --- | --- |
| Narration (performance) | [Chatterbox-Turbo](https://huggingface.co/ResembleAI/chatterbox-turbo) by Resemble AI | MIT |
| Narrator's timbre (reference voice) | [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M), voice `am_michael` | Apache-2.0 |
| Take checking and caption timing | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) `small.en` | MIT |

`reference-voice.wav` is about 17 seconds of Kokoro's `am_michael` voice, made from lines 7, 13 and 15 of `gen_kokoro.py`. Chatterbox-Turbo takes its timbre from that clip, so the narrator is a synthetic voice and not a copy of any real person. Chatterbox-Turbo also performs a few cues: a sigh before "Now I'm on my deathbed", and a chuckle after "I'm not going to go easy".

Chatterbox embeds an inaudible Perth watermark in everything it generates.

## Files

| File | What it does |
| --- | --- |
| `script.json` | The performance script: one entry per caption line. `{0.3}` marks a pause in seconds, and `mood` sets the delivery for the Kokoro fallback. |
| `dumplines.mjs` | Reads each line's start time and window from `../src/08-film.js` and writes `lines.json`. |
| `gen_turbo.py` | Records three takes of every line with Chatterbox-Turbo. |
| `gen_kokoro.py` | Records one take of every line with Kokoro alone. It's faster and has fewer dependencies, but the delivery is flatter. |
| `process_voice.py` | Checks every take, processes the best one, and writes `../src/01b-voice.js`. Details below. |

`process_voice.py` does these steps:

1. Transcribes every take with Whisper.
2. Keeps the take that says the words exactly and fits its caption window.
3. Trims the take and opens its pauses to the scripted lengths.
4. Gives every line a voice-over treatment (EQ and gentle compression) and matches it to −17 LUFS.
5. Records when each caption word is spoken.
6. Lays all the lines end to end in one MP3, embedded as `../src/01b-voice.js`.

In the film, each line starts 0.18 s after its caption appears. The captions' words surface as they are spoken. With narration the score sits 2 dB lower and dips a further 7.5 dB under each line, so the voice sits about 10 dB over the music. The narrator is heard even through the film's silent beats.

## Re-record

```sh
# Python 3.11 with chatterbox-tts; Python 3.12 with faster-whisper, librosa, soundfile, pyloudnorm
node dumplines.mjs ../src/08-film.js lines.json
python gen_turbo.py reference-voice.wav takes/            # about 1 hour on 4 CPU cores
python process_voice.py takes/ processed/ ../src/01b-voice.js
node ../build.mjs
```

To use a different voice, replace `reference-voice.wav` with about 10 to 20 seconds of clean speech, recorded by someone who has agreed to it. You can also run `gen_kokoro.py <voice> takes/` with any Kokoro voice instead of `gen_turbo.py`.
