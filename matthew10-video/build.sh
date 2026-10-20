#!/usr/bin/env bash
# End-to-end build for "Not Peace, But a Sword".
#
#   ./build.sh [stage ...]     stages: voices select pack prepare music mix frames master final
#                              (default: select prepare music mix frames master final)
#   Rebuild from the voices stored in assets/voice: ./build.sh prepare music mix frames master final
#
#   Realistic version (same soundtrack; needs the 2D build above):
#     ./build.sh real-poses real-images real-faces real-frames real-final
#   real-images generates the photographs (SDXL on CPU, ~1.5 min each), real-faces
#   animates every face with LivePortrait (the longest step), real-frames composites.
#
# Environment (defaults match the session that made it):
#   WORK=/opt/work  KVENV=/opt/vvenv (Kokoro, faster-whisper, mido)  CBVENV=/opt/cbvenv (Chatterbox)
#   JOBS=4  SF2=/usr/share/sounds/sf2/FluidR3_GM.sf2
set -euo pipefail
cd "$(dirname "$0")"
WORK=${WORK:-/opt/work}
KVENV=${KVENV:-/opt/vvenv}
CBVENV=${CBVENV:-/opt/cbvenv}
JOBS=${JOBS:-4}
SF2=${SF2:-/usr/share/sounds/sf2/FluidR3_GM.sf2}
RVENV=${RVENV:-/opt/rvenv}
BUILD=$WORK/build_final
REAL=$WORK/real
STAGES=${*:-select prepare music mix frames master final}
has() { [[ " $STAGES " == *" $1 "* ]]; }

if has voices; then
  "$KVENV/bin/python" audio/tts_kokoro.py script.json "$WORK/tts"
  HF_HOME=/opt/models/hf "$CBVENV/bin/python" audio/tts_chatterbox.py script.json "$WORK/refs" "$WORK/cb"
fi
if has select; then
  HF_HOME=/opt/models/hf "$CBVENV/bin/python" audio/score_takes.py script.json "$WORK/refs" "$WORK/cb" "$WORK/sims.json"
  "$KVENV/bin/python" audio/select_takes.py script.json "$WORK/cb" "$WORK/sims.json" "$WORK/tts" "$WORK/selection.json"
fi
if has prepare; then
  # use freshly selected takes if present, otherwise the voices stored in the repo
  SEL="$WORK/selection.json"; [[ -f "$SEL" ]] || SEL=assets/voice/selection.json
  "$KVENV/bin/python" audio/prepare.py script.json "$SEL" "$BUILD"
fi
if has music; then
  "$KVENV/bin/python" audio/music.py "$BUILD/timeline.json" "$BUILD/score.mid"
  fluidsynth -ni -q -F "$BUILD/score.wav" -r 48000 -g 0.5 -o synth.reverb.room-size=0.75 \
    -o synth.reverb.width=0.9 -o synth.reverb.level=0.7 "$SF2" "$BUILD/score.mid"
fi
if has mix; then
  "$KVENV/bin/python" audio/mix.py "$BUILD" "$BUILD/score.wav" "$BUILD/mix.wav"
fi
if has frames; then
  DUR=$(python3 -c "import json;print(json.load(open('$BUILD/timeline.json'))['duration'])")
  mkdir -p "$BUILD/seg"
  pids=()
  for i in $(seq 0 $((JOBS - 1))); do
    A=$(python3 -c "print(round($DUR * $i / $JOBS, 3))")
    B=$(python3 -c "print(round($DUR * ($i + 1) / $JOBS + (0.5 if $i == $JOBS - 1 else 0), 3))")
    # snap segment edges to whole frames so the pieces join exactly
    A=$(python3 -c "print(round($A * 24) / 24)"); B=$(python3 -c "print(round($B * 24) / 24)")
    ( set -o pipefail
      node --expose-gc render/main.js --build "$BUILD" --from "$A" --to "$B" --fps 24 2>"$BUILD/seg/log$i.txt" |
        ffmpeg -v error -y -f image2pipe -c:v mjpeg -framerate 24 -i - \
          -c:v libx264 -preset veryfast -crf 8 -pix_fmt yuv420p "$BUILD/seg/seg$i.mp4" ) &
    pids+=($!)
  done
  for p in "${pids[@]}"; do wait "$p" || { echo "render segment failed (see $BUILD/seg/log*.txt)"; exit 1; }; done
fi
if has master; then
  : > "$BUILD/seg/list.txt"
  for i in $(seq 0 $((JOBS - 1))); do echo "file 'seg$i.mp4'" >> "$BUILD/seg/list.txt"; done
  ffmpeg -v error -y -f concat -safe 0 -i "$BUILD/seg/list.txt" -c copy "$BUILD/master_video.mp4"
fi
if has pack; then
  "$KVENV/bin/python" tools/pack_voices.py "$WORK/selection.json" assets/voice
fi
if has final; then
  "$KVENV/bin/python" tools/encode.py "$BUILD" "$(pwd)/NotPeaceButASword.mp4"
fi

# ---------------------------------------------------------------- realistic version
SHOTS=$WORK/real_shots.json
if has real-poses; then
  node render/main.js --build "$BUILD" --export-poses "$WORK/poses.jsonl"
fi
if has real-images; then
  "$RVENV/bin/python" realistic/shots.py "$SHOTS"
  # raw 2D frames that the group shots are photo-realized from
  T=$(python3 -c "import json;print(','.join(sorted({s['init'].rsplit('still_',1)[1][:-4] for s in json.load(open('$SHOTS')) if s.get('init')})))")
  node render/main.js --build "$BUILD" --stills "$T" --outdir "$REAL/layout" --raw 1
  "$RVENV/bin/python" realistic/gen_images.py "$SHOTS" "$REAL/img"
fi
if has real-faces; then
  "$RVENV/bin/python" realistic/render_faces.py base "$REAL/img" "$REAL" "$SHOTS"
  "$RVENV/bin/python" realistic/render_faces.py plates "$REAL/img" "$REAL" "$SHOTS" "$WORK/poses.jsonl"
fi
if has real-frames; then
  DUR=$(python3 -c "import json;print(json.load(open('$BUILD/timeline.json'))['duration'])")
  mkdir -p "$REAL/seg"
  pids=()
  for i in $(seq 0 $((JOBS - 1))); do
    A=$(python3 -c "print(round(round($DUR * $i / $JOBS, 3) * 24) / 24)")
    B=$(python3 -c "print(round(round($DUR * ($i + 1) / $JOBS + (0.5 if $i == $JOBS - 1 else 0), 3) * 24) / 24)")
    ( set -o pipefail
      node --expose-gc render/main_real.js --build "$BUILD" --real "$REAL" --from "$A" --to "$B" 2>"$REAL/seg/log$i.txt" |
        ffmpeg -v error -y -f image2pipe -c:v mjpeg -framerate 24 -i - \
          -c:v libx264 -preset veryfast -crf 10 -pix_fmt yuv420p "$REAL/seg/seg$i.mp4" ) &
    pids+=($!)
  done
  for p in "${pids[@]}"; do wait "$p" || { echo "render segment failed (see $REAL/seg/log*.txt)"; exit 1; }; done
  : > "$REAL/seg/list.txt"
  for i in $(seq 0 $((JOBS - 1))); do echo "file 'seg$i.mp4'" >> "$REAL/seg/list.txt"; done
  ffmpeg -v error -y -f concat -safe 0 -i "$REAL/seg/list.txt" -c copy "$REAL/master_video.mp4"
fi
if has real-final; then
  "$KVENV/bin/python" tools/encode.py "$BUILD" "$(pwd)/NotPeaceButASword_realistic.mp4" \
    --master "$REAL/master_video.mp4" --work "$REAL/enc" --tune film --sizes 720:1280   # 720p measured better at this bitrate
fi
