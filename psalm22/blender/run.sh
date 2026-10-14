#!/bin/bash
# Render a shot headless: psalm22/blender/run.sh --shot s01a --quality preview --frames sheet6
# Waits for one of RENDER_SLOTS machine-wide Blender slots (see slot.sh).
HERE="$(cd "$(dirname "$0")" && pwd)"
BLENDER="${BLENDER:-/opt/tools/blender-4.5.14-linux-x64/blender}"
source "$HERE/slot.sh"
exec xvfb-run -a -s "-screen 0 1280x1024x24" "$BLENDER" -b -noaudio -P "$HERE/render_shot.py" -- "$@"
