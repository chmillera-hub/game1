# Psalm 22 — a 3D-animated portrait film

**Deliverable:** `Psalm22_portrait.mp4` — 720×1280 (9:16 portrait), 24 fps, 4 min 19 s, H.264 + AAC, 14.3 MB.
The first frame is the bright golden title shot of Golgotha (no dark preview square).

Psalm 22:1–31 (NIV) narrated (AI voice, Kokoro `am_michael`) with on-screen captions, an original score and
sound design, over CG scenes rendered in Blender 4.5 (EEVEE) that visualise each block of the text:
Golgotha and the darkened sun, Gethsemane, the Holy of Holies, the Red Sea, the nativity, Mary at the cross,
the bulls and lions of Bashan, water poured out, a melting candle, the potsherd, dogs and soldiers, the casting
of lots, the light breaking through, the beasts turning to dust, the empty tomb, the scarred hand, the risen
face, the Earth at sunrise, the story passed to the next generation, and the empty cross at sunrise.

## Required notice when posting
Scripture quotations taken from The Holy Bible, New International Version® NIV®. Copyright © 1973, 1978,
1984, 2011 by Biblica, Inc.™ Used by permission. All rights reserved worldwide.

Some animal models are CC BY 4.0 — see `CREDITS.md` (credit them in the post description).

## Rebuild
See `DEV.md` (pipeline), `docs/*.md` (module APIs). Order: `audio/tts.py` → `timeline.py` →
`render_queue.py` (Blender renders, hours on CPU) → `audio/music.py`, `sfx.py`, `mix.py` →
`comp/composite.py` (grading, captions, encode < 15 MB).
