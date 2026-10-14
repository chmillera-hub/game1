#!/bin/bash
# Run any Blender python script headless (EEVEE-capable) inside the shared render semaphore:
#   psalm22/blender/bl.sh my_test.py [script args...]
HERE="$(cd "$(dirname "$0")" && pwd)"
BLENDER="${BLENDER:-/opt/tools/blender-4.5.14-linux-x64/blender}"
SCRIPT="$1"; shift
source "$HERE/slot.sh"
exec xvfb-run -a -s "-screen 0 1280x1024x24" "$BLENDER" -b -noaudio -P "$SCRIPT" -- "$@"
