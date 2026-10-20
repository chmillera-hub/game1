#!/usr/bin/env bash
# Build the fantasy version of "Not Peace, But a Sword".
#
#   fantasy/build.sh [stage ...]
#   stages: voices select prepare music mix images faces depth frames final
#   (default: all of them, in that order)
#
# voices and images are the slow ones (CPU Chatterbox and SDXL); both resume
# where they stopped. Uses the tools and environments of ../build.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
WORK=${WORK:-/opt/work}
KVENV=${KVENV:-/opt/vvenv}
CBVENV=${CBVENV:-/opt/cbvenv}
RVENV=${RVENV:-/opt/rvenv}
JOBS=${JOBS:-4}
SF2=${SF2:-/usr/share/sounds/sf2/FluidR3_GM.sf2}
F=$WORK/fantasy
FB=$F/build
SCRIPT=fantasy/script.json
SHOTS=$F/shots.json
STAGES=${*:-voices select prepare music mix images faces depth frames final}
has() { [[ " $STAGES " == *" $1 "* ]]; }

if has voices; then
  "$KVENV/bin/python" audio/tts_kokoro.py "$SCRIPT" "$F/tts"
  HF_HOME=/opt/models/hf "$CBVENV/bin/python" audio/tts_chatterbox.py "$SCRIPT" "$WORK/refs" "$F/cb"
fi
if has select; then
  HF_HOME=/opt/models/hf "$CBVENV/bin/python" audio/score_takes.py "$SCRIPT" "$WORK/refs" "$F/cb" "$F/sims.json"
  "$KVENV/bin/python" audio/select_takes.py "$SCRIPT" "$F/cb" "$F/sims.json" "$F/tts" "$F/selection.json"
fi
if has prepare; then
  "$KVENV/bin/python" audio/prepare.py "$SCRIPT" "$F/selection.json" "$FB" "$F/tts"
fi
if has music; then
  "$KVENV/bin/python" fantasy/music.py "$FB/timeline.json" "$FB/score.mid"
  fluidsynth -ni -q -F "$FB/score.wav" -r 48000 -g 0.5 -o synth.reverb.room-size=0.8 \
    -o synth.reverb.width=0.9 -o synth.reverb.level=0.75 "$SF2" "$FB/score.mid"
fi
if has mix; then
  "$KVENV/bin/python" fantasy/mix.py "$FB" "$FB/score.wav" "$FB/mix.wav"
fi
if has images; then
  "$RVENV/bin/python" fantasy/shots.py "$SHOTS"
  # face references from the realistic version (identity for IP-Adapter)
  mkdir -p "$F/img"
  for r in ref_maya ref_mom; do [[ -f "$F/img/$r.png" ]] || cp "$WORK/real/img/$r.png" "$F/img/"; done
  [[ -f "$F/img/ref_dad.png" ]] || cp "$WORK/real/img/table_dad.png" "$F/img/ref_dad.png"
  [[ -f "$F/img/ref_greg.png" ]] || cp "$WORK/real/img/office_greg.png" "$F/img/ref_greg.png"
  [[ -f "$F/img/ref_priya.png" ]] || "$RVENV/bin/python" -c "
from PIL import Image; im = Image.open('$WORK/real/img/epi_two.png'); im.crop((0, 0, im.width // 2, im.height)).save('$F/img/ref_priya.png')"
  "$RVENV/bin/python" realistic/gen_images.py "$SHOTS" "$F/img"
fi
if has faces; then
  # emotion deltas measured on the realistic version's expression photos
  [[ -f "$F/basis.json" ]] || cp "$WORK/real/basis.json" "$F/basis.json"
  "$RVENV/bin/python" realistic/render_faces.py base "$F/img" "$F" "$SHOTS"
  node fantasy/render.js --build "$FB" --real "$F" --shots "$SHOTS" --export-poses "$F/poses.jsonl"
  "$RVENV/bin/python" realistic/render_faces.py plates "$F/img" "$F" "$SHOTS" "$F/poses.jsonl"
fi
if has depth; then
  "$RVENV/bin/python" fantasy/depth.py "$F/base" "$F/depth"
fi
if has frames; then
  DUR=$(python3 -c "import json;print(json.load(open('$FB/timeline.json'))['duration'])")
  mkdir -p "$F/seg"
  pids=()
  for i in $(seq 0 $((JOBS - 1))); do
    A=$(python3 -c "print(round(round($DUR * $i / $JOBS, 3) * 24) / 24)")
    B=$(python3 -c "print(round(round($DUR * ($i + 1) / $JOBS + (0.5 if $i == $JOBS - 1 else 0), 3) * 24) / 24)")
    ( set -o pipefail
      node --expose-gc fantasy/render.js --build "$FB" --real "$F" --from "$A" --to "$B" 2>"$F/seg/log$i.txt" |
        ffmpeg -v error -y -f image2pipe -c:v mjpeg -framerate 24 -i - \
          -c:v libx264 -preset veryfast -crf 10 -pix_fmt yuv420p "$F/seg/seg$i.mp4" ) &
    pids+=($!)
  done
  for p in "${pids[@]}"; do wait "$p" || { echo "render segment failed (see $F/seg/log*.txt)"; exit 1; }; done
  : > "$F/seg/list.txt"
  for i in $(seq 0 $((JOBS - 1))); do echo "file 'seg$i.mp4'" >> "$F/seg/list.txt"; done
  ffmpeg -v error -y -f concat -safe 0 -i "$F/seg/list.txt" -c copy "$F/master_video.mp4"
fi
if has final; then
  "$KVENV/bin/python" tools/encode.py "$FB" "$(pwd)/NotPeaceButASword_fantasy.mp4" \
    --master "$F/master_video.mp4" --work "$F/enc" --tune film --sizes 720:1280
fi
