#!/bin/bash
# Render the film shot by shot, reloading the blend for every chunk so that
# fixes published to the blend (atomic mv) reach the shots not yet rendered.
# usage: render_chunks.sh film_render.blend timeline.json out_dir [spp]
BLEND=$1; TL=$2; OUT=$3; SPP=${4:-5}
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT"
python3 - "$TL" > "$OUT.chunks" <<'PY'
import json, sys, math
d = json.load(open(sys.argv[1]))
fps = d['fps']
n = int(math.ceil(d['duration'] * fps))
for s in d['shots']:
    f0 = int(round(s['t0'] * fps)) + 1
    f1 = min(n, int(round(s['t1'] * fps)))
    if f1 >= f0:
        print(s['name'], f0, f1)
PY
while read name f0 f1; do
    find "$OUT" -size 0 -delete 2>/dev/null
    echo "CHUNK $name $f0-$f1 $(date +%H:%M:%S)"
    blender -b "$BLEND" --python "$HERE/render_film.py" -- "$OUT" "$f0" "$f1" "$SPP" > "$OUT.log.$name" 2>&1
    echo "DONE $name $(ls "$OUT" | wc -l) frames $(date +%H:%M:%S)"
done < "$OUT.chunks"
echo ALLDONE
