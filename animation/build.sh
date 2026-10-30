#!/usr/bin/env bash
# Full build: voices -> cues -> score -> mix -> frames -> compressed portrait MP4s.
# Output: build/the_family_inside.mp4 (HEVC, < 15 MB) and build/the_family_inside_h264.mp4 (H.264, max compatibility).
set -euo pipefail
cd "$(dirname "$0")"
JOBS=${JOBS:-4}
export TARGET_MB=${TARGET_MB:-14.6}     # total file size target (MB)
export ABR=${ABR:-64}                   # AAC audio bitrate (kbps)

python3 audio/gen_voices.py | tail -1
node src/render.js cues
python3 audio/music.py build/cues.json
python3 audio/mix.py build/cues.json
node src/render.js parallel --jobs "$JOBS" --w 1080

./encode.sh
