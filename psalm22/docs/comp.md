# comp/ — compositor, captions, delivery encode

Owner: comp. Files: `comp/composite.py`, `comp/captions.py`, `comp/encode.py`, `comp/fonts/` (OFL fonts + licences).
Python: `/opt/venv/bin/python` (numpy, pillow, **opencv-python-headless** — installed into the venv by comp).

```
frames/<shot>/<q>/NNNN.png ─┐
post.json (grade hints) ────┤ composite.py ── 10-bit YUV pipe ──> $WORK/comp/mezz.mp4 ── encode.py ──> psalm22.mp4 (< 15 MB)
timeline.json ──────────────┤   grade → transitions → film look → 540→720 upscale → captions          (H.264 High, AAC)
audio/phrases.json ─────────┘                                               audio/mix.wav (or narration.wav) ──┘
```

## Usage

```bash
P=/opt/venv/bin/python; cd /home/user/game1/psalm22
$P comp/composite.py                          # whole film -> $WORK/comp/mezz.mp4 -> $WORK/comp/psalm22.mp4
$P comp/composite.py --no-encode              # mezzanine only
$P comp/encode.py                             # re-encode the existing mezzanine (no recompositing)
$P comp/encode.py --codec both --metrics      # H.264 + HEVC (hvc1) side by side, SSIM/PSNR vs mezzanine

# reviewing
$P comp/composite.py --stills 0,1500,6150 --stills-dir /tmp/st          # PNG stills of global frames (0-based)
$P comp/composite.py --direct /tmp/s05.mp4 --shots s05,s06a            # quick single-pass preview with audio
$P comp/composite.py --direct /tmp/x.mp4 --frames 2400-2700 --burnin  # + shot/frame/source overlay
$P comp/captions.py /tmp/caption_specimen.png                          # sheet of every caption
```

Options: `--quality auto|final|draft|preview` (default auto), `--frames A-B[,C-D]`, `--shots id,id`,
`--no-captions`, `--burnin`, `--workers N` (default 4), `--mezz PATH`, `--out PATH`, `--audio PATH`,
`--encode-args="--codec both --metrics"`. Partial ranges keep absolute caption/audio timing.

## Frame sources (what gets used)

Per shot, `$WORK/frames/<shot>/{final,draft,preview}/NNNN.png` (1-based shot frames, `render_frames` =
`nframes` + dissolve `tail`). For every frame the **best quality that has exactly that frame wins**
(final > draft > preview). Missing frames are **cross-blended between the nearest rendered frames** of the
quality with the best coverage (smallest max gap), so a `sheet6` preview already plays as an animatic.
Preview frames (270x480) are upscaled to 540x960 first. 16-bit PNGs are read at full precision (RGBA: alpha ignored).
A shot with no frames at all becomes a **labelled placeholder card** (id, title, visual description,
mood-tinted gradient, frame counter + timing bar), so the whole film always builds.

## post.json — grading hints (`ctx.post = {...}` in the shot script)

Written by `render_shot.py` next to the frames; the newest `post.json` of the shot's quality dirs is used.
All keys optional. Unknown keys are ignored. Values below are the defaults.

| key | default | meaning |
|---|---|---|
| `grade` | — | preset name or list of names applied in order (table below); explicit keys override it |
| `exposure` | 0.0 | stops (linear-light gain 2^x) |
| `temperature` | 0.0 | −1 cool … +1 warm (white balance, luminance-neutral) |
| `tint` | 0.0 | −1 green … +1 magenta |
| `contrast` | 1.0 | linear contrast around `pivot` (0.45, display space) with a soft highlight shoulder |
| `saturation` | 1.0 | 0 = B/W |
| `lift` / `gamma` / `gain` | 0 / 1 / 1 | scalar or `[r,g,b]`; lift raises blacks, gamma bends mids, gain scales |
| `shadows` / `highlights` | 0 | `[r,g,b]` split-toning offsets weighted by (1−L)² / L² (e.g. `[0,0,0.03]` = blue shadows) |
| `bloom` | 0.16 | bloom amount (only the top of the range blooms: squared knee above the threshold) |
| `bloom_threshold` | 0.70 | display luminance where bloom starts |
| `bloom_radius` | 1.0 | radius scale |
| `halation` | 0.06 | red-orange film halation around highlights |
| `vignette` | 0.16 | soft oval vignette strength |
| `sharpen` | 0.35 | unsharp amount after the 540→720 Lanczos upscale |
| `grain` | 0.0 | soft luma grain, capped at 0.03 — **leave at 0** (costs bitrate) |
| `end` | — | dict of any keys above (or `grade`), **linearly interpolated over the shot**: `{"exposure": -0.2, "end": {"exposure": -1.2}}` darkens through the shot |
| `caption` | — | `{"y": 0.68, "ink": "light", "halo": 1.0, "hide": false}` for captions that START in this shot: `y` block centre (clamped 0.60–0.74), `ink` light/dark, `halo` multiplies the dark halo (1.3 for busy bright backgrounds) |
| `title` | — | (s00 only) `{"y": 0.315, "ink": "auto"}` — `auto` picks dark umber ink if frame 1 is bright under the title, else white |
| `endcard` | — | (last shot only) `{"ink": "auto"}` |

Presets (`grade`): `neutral`, `warm`, `gold`, `cool`, `night`, `eclipse` (desaturated, red-brown, heavy
vignette — the darkened sun), `flashback` (lifted blacks, soft, warm, glowy), `glory` (bright, gold, big bloom),
`bleak`, `dawn`, `dusk`, `candle`, `space`. Values: see `PRESETS` in `comp/composite.py`.

Example (s00 prototype): `{"grade": "warm", "bloom": 0.35}`. Night flashback: `{"grade": ["night", "flashback"], "vignette": 0.3}`.

Order of operations: grade (540x960, per source shot) → dissolve blend → Lanczos 720x1280 + unsharp →
bloom/halation (screen) → vignette → flash → captions → fade-to-black → BT.709 YUV.

## Transitions (`transition_in` in timeline.json)

* `cut` — nothing.
* `dissolve` — the previous shot's 14-frame `tail` (frames nframes+1 … nframes+14) is blended with the next
  shot's first 14 frames (smoothstep). Each side keeps its own grade; look params are interpolated.
* `flash` — white bloom peak exactly on the cut: 3 frames ramp up, peak on the first frame of the new shot,
  ~10 frame decay; bloom threshold drops and amount rises with it.
* `fade_black` — short dip: 6 frames down, 9 frames up. Never applied at frame 0.
* End of film: the last 1.1 s fade to black (end card included). Frame 0 is never faded.

## Captions, title, end card (`comp/captions.py`)

* Text: exact NIV phrases from `$WORK/audio/phrases.json` (curly quotes, apostrophes, em dashes preserved).
* Font: **Cormorant Garamond SemiBold** 46 px (auto-shrinks to ≥ 36 px for long phrases), warm white
  `#FFFBF3`, soft drop shadow + wide dark halo whose strength adapts to the background luminance under the
  text (legible over bright skies and night scenes alike).
* Layout: max 2 **balanced** lines (prefers breaking after punctuation, never ends line 1 on a weak word
  like “the/of/your”, mildly bottom-heavy, no one-word lines),
  max width 540 px, centred at x = 0.48 W, block centre y = 0.68 H. Safe zone: never below 82 % of the height
  or in the right 12 %.
* Timing: fade/rise in 0.28 s starting 0.12 s before the voice; lingers 0.55 s after the phrase when there
  is room; with tight gaps the old line is gone exactly when the next one starts rising (no overlap).
* Title over s00: “PSALM 22” (Cinzel SemiBold, tracked) + hairline + “A Psalm of David” (Cormorant Italic),
  centre y = 0.315 H (inside the centre-square thumbnail crop, above the crosses). **Fully opaque on frame 1**
  (no fade-in, no darkening); slow 2 % push; fades out 2.9–4.0 s. Ink is chosen once from frame 1.
* Effects (meaning-driven, readability first — table `EFFECTS` in captions.py):

| phrase | effect |
|---|---|
| “…why have you forsaken me?” | `drift` — words drift apart as the line fades (loneliness) |
| “Yet you are enthroned as the Holy One;” | `holy` — gold-white ink, softly breathing gold glow on “Holy One” |
| “I am poured out like water,” | `ripple` — “like water” gently undulates; the line ripples away |
| “it has melted within me.” | `melt` — “melted” softens while spoken; then the line sags, blurs, drips away |
| “you lay me in the dust of death.” | `crumble` — letters crumble left→right into sand grains that fall and blow away |
| “He has done it!” | `triumph` — larger Cinzel, gold glow, slow scale-in, one light sweep; holds into the outro |

* End card (outro, 2.6 s after the last phrase): “PSALM 22 · NIV” / hairline / *It is finished.* / “— John 19:30”,
  centred at y = 0.44 H, ink chosen once from a reference frame (dark umber over bright sunrise, else white).

## Encode (`comp/encode.py`)

* Mezzanine (composite.py): x264 **10-bit** 4:2:0, CRF 8, veryfast, BT.709 tags, MP4 container (exact timestamps).
  The compositor streams raw `yuv420p10le` into ffmpeg — no PNG/intermediate sequences.
* Delivery: **H.264 High@4.0, yuv420p, 720x1280, 24 fps, two-pass ABR**, `-movflags +faststart`, BT.709 tags,
  x264 `preset slow` + `aq-mode=3:aq-strength=0.9` (dark-scene bias against banding), keyint 240, bframes 4, ref 4,
  `-maxrate 3x -bufsize 6x`.
* Bitrate: `video_kbps = (15e6·(1−margin) − audio_bytes − container_overhead)·8 / duration`; the audio is
  encoded first so its exact size is known; if the file still lands within 0.5 % of 15 MB, pass 2 reruns lower.
  Default margin 4.5 % → ≈14.3 MB target.
* Audio: AAC-LC 48 kHz, **64 kbps mono / 80 kbps stereo**, padded/trimmed to the video length.
  Source `$WORK/audio/mix.wav`, fallback `narration.wav`, else silence.
* 10→8 bit: zimg `zscale` with **ordered dither** (`--dither none|ordered|random|error_diffusion|sws`).
* First frame: IDR, checked with ffprobe and reported (`first_frame_idr`).
* HEVC comparison: `--codec hevc` (x265 medium two-pass, `-tag:v hvc1`, Main) → `psalm22_hevc.mp4`.

## Measurements (2026-10-14, test film = s00 renders + 39 placeholder shots)

Machine was heavily shared during all tests (7 Blender renders, load average 17-27 on 4 cores), so wall
times below are pessimistic; CPU-seconds are the contention-independent number.

| stage | CPU cost | wall, shared box | wall, est. 4 free cores |
|---|---|---|---|
| compositing (4 workers) | ~0.09 CPU-s/frame (real frames 0.10-0.13, placeholders ~0.07) | 764 / 836 s | ~2.5 min |
| 10-bit mezzanine x264 (concurrent) | ~0.015 CPU-s/frame | (overlapped) | (overlapped) |
| H.264 pass 1 / pass 2 (preset slow) | — | 95-102 s / 224-254 s | ~1 / ~2.5 min |
| **whole film** | **15-16 CPU-min total** (run 2: user 14m27 + sys 1m28) | **18m09 / 20m09** (two runs) | **≈ 6 min** (< 15 min target, not verified on an idle box) |

Real CG frames will cost more in x264 than placeholders (more detail/motion); budget ~2x for the encode.

Draft film `$WORK/dev/comp/draft.mp4`: **14.315 MB**, 258.875 s, 6213 frames, H.264 High@4.0 yuv420p
720x1280 24 fps, video 355 kbps + AAC-LC stereo 80 kbps (`mix.wav`), atoms ftyp-moov-free-mdat (+faststart),
first frame I/IDR, first-frame mean luma 0.68. With mono narration only, the formula gives 387 kbps video.

Banding / dither (synthetic moonlit-sky gradient, luma 0.02-0.22, slow light move + fog, 6 s):

| 10→8 bit dither | bitrate at CRF 20 | look at 375 kbps ABR (5x contrast) |
|---|---|---|
| none | 227 kbps (ref) | hard contour bands |
| **ordered (default)** | 240 kbps (**+6 %**) | bands broken up, slight texture |
| error_diffusion | 321 kbps (+41 %) | similar to ordered, much more expensive |

H.264 vs HEVC at the film's rate (proxy clip: 10 s push-in on the real s00 render + caption, 6 s dark gradient; SSIM/PSNR vs
the 10-bit mezzanine):

| codec | rate | size | SSIM | PSNR-Y | enc. speed (shared box) |
|---|---|---|---|---|---|
| H.264 slow | 387 kbps | 779 kB | 0.9954 | 50.0 dB | 11.4 fps |
| HEVC medium (hvc1) | 387 kbps | 774 kB | 0.9950 | 50.9 dB | 8.3 fps |
| HEVC medium (hvc1) | 270 kbps | 543 kB | 0.9946 | 50.2 dB | 8.9 fps |

HEVC matches H.264 quality at ~70 % of the bitrate (≈ +0.9 dB at equal rate; detail crops visually near
identical on this easy proxy). Recommendation: deliver **H.264** (universal playback, social platforms re-encode
anyway); keep `--codec hevc` as an alternate if a platform accepts HEVC and the real renders look starved.

## Notes for shot authors

* Keep faces/subjects out of y = 0.60–0.80 H if a shot has long two-line captions, or set
  `ctx.post["caption"] = {"y": 0.62}` (block moves up) / `{"halo": 1.3}` for busy bright backgrounds.
* s00: leave the upper-middle sky calm (title sits at 0.25–0.37 H); frame 1 must be bright —
  the title ink auto-switches to dark umber when the sky behind it is brighter than 0.66 luma.
* Render 8-bit PNG is fine; 16-bit PNG is read losslessly if you want less banding at the source.
* `grain` stays 0 — at ~390 kbps noise eats the whole budget.

## Fonts & credits

All fonts are SIL Open Font License 1.1, from github.com/google/fonts (`ofl/…`), stored with their licence
texts in `comp/fonts/` (re-downloaded by `captions.ensure_fonts()` if missing):

* Cormorant Garamond (variable, roman + italic) — © 2015 The Cormorant Project Authors — `OFL-CormorantGaramond.txt`
* Cinzel (variable) — © 2020 The Cinzel Project Authors — `OFL-Cinzel.txt`
* EB Garamond (variable, roman + italic; placeholder cards / fallback) — © 2017 The EB Garamond Project Authors — `OFL-EBGaramond.txt`

Scripture: Psalm 22 and John 19:30 quotations are from the Holy Bible, New International Version (NIV)
— if the film is published, add the standard NIV copyright notice in the post description.
