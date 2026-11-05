# Export metadata and render settings

All values below were measured on `a-table-instead-of-a-palace.mp4` with ffprobe and ffmpeg. The raw output is in `checks_output.txt`, produced by `source/checks.sh`.

| Item | Requested | Measured |
|---|---|---|
| Container | MP4 for phones and social apps | MP4, with faststart enabled so it starts playing before fully downloading |
| Video | Portrait, 9:16 | H.264 High profile, 720 × 1280, yuv420p color format, 24/1 fps |
| Frames | All frames of the timeline | 9,581 (decoded count = container count = shot-log count) |
| Duration | Set by the dialogue (no limit) | 399.208 s for video, 399.201 s for audio (a 7 ms difference, under one AAC audio frame) |
| Audio | Stereo | AAC-LC, 48 kHz, 2 channels, 73.9 kbps |
| Loudness | −14 LUFS integrated, −1.0 dBTP true peak | **−14.3 LUFS**, true peak **−1.0 dBFS**, loudness range 3.5 LU |
| File size | Under 15 MB | **14,730,872 bytes (14.73 MB)**. Overall bitrate 295 kbps, video 216 kbps. |
| Compression loss | At least 90% of master quality | SSIM **0.9948** against the near-lossless render master (CRF 10) |
| First frame | Not dark | Mean brightness 140 out of 255: the fully drawn golden hillside |

The loudness lands 0.3 LU under the −14 target because the peak limiter takes priority over loudness.

## Render pipeline (`source/build.sh`)

1. `voices.py` runs Piper TTS for every line and writes `timeline.json`, with every line, subtitle chunk, word accent and frame-by-frame mouth data.
2. `music.py` generates the score, accents and sound effects, then ducks the music and mixes it into `final.wav` (48 kHz).
3. `render.js` draws each frame with @napi-rs/canvas, as raw RGBA piped to ffmpeg. It runs four processes in parallel, each on a quarter of the frame range, and joins them without re-encoding.
   - The intermediate master is `libx264 -preset veryfast -crf 10`.
   - Every frame is a pure function of its frame number. All procedural motion is seeded hash noise, and there is no state carried between frames, so any frame range can be rendered on its own.
4. Audio: two-pass `loudnorm` (I = −14, TP = −1, LRA = 11, linear mode), resampled to 192 kHz for the `alimiter` peak limiter (limit 0.70), then back to 48 kHz.
5. Video: two-pass `libx264 -preset slow -tune animation -b:v 216k -maxrate 900k -bufsize 1800k`. The bitrate is computed from a 14.4 MB target. Audio is `aac 72k` with `-movflags +faststart`.

On 4 CPU cores, the full rebuild takes about 6 minutes: about 1.5 minutes to render the frames, about 3 minutes for the two-pass encode, and the rest for audio. TTS is cached after the first run.

## Dependency versions

- Python 3.13.18, with numpy 2.5.3, scipy 1.18.1, piper-tts 1.8.0 and onnxruntime 1.29.0.
- Node.js v22.23.4, with @napi-rs/canvas 1.1.0.
- FFmpeg 6.1.1 (Ubuntu build), using libx264 and the native AAC encoder.
- Fonts: Inter (SemiBold, SemiBold Italic, Bold) and DejaVu Serif Bold / DejaVu Sans, the latter for the Hebrew הֶבֶל. These are SIL OFL and Bitstream Vera licenses.
