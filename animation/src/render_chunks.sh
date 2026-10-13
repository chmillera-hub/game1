#!/bin/bash
# Render the film shot by shot, reloading the blend for every chunk so that
# fixes published to the blend (atomic mv) reach the shots not yet rendered.
# Several runners can share one output: each claims a shot with a lock dir,
# so a forward and a reverse runner meet in the middle.
# usage: render_chunks.sh film_render.blend timeline.json out_dir [spp] [fwd|rev] [threads]
BLEND=$1; TL=$2; OUT=$3; SPP=${4:-5}; ORDER=${5:-fwd}; THREADS=${6:-0}
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT" "$OUT.locks"
python3 - "$TL" "$ORDER" <<'PY' > "$OUT.chunks.$ORDER"
import json, sys, math
d = json.load(open(sys.argv[1]))
fps = d['fps']
n = int(math.ceil(d['duration'] * fps))
rows = []
for s in d['shots']:
    f0 = int(round(s['t0'] * fps)) + 1
    f1 = min(n, int(round(s['t1'] * fps)))
    if f1 >= f0:
        rows.append('%s %d %d' % (s['name'], f0, f1))
print('\n'.join(rows[::-1] if sys.argv[2] == 'rev' else rows))
PY
complete() {
    for ((f = $2; f <= $3; f++)); do
        [ -s "$(printf '%s/f%05d.png' "$1" "$f")" ] || return 1
    done
}
while read name f0 f1; do
    complete "$OUT" "$f0" "$f1" && continue
    mkdir "$OUT.locks/$name" 2>/dev/null || continue
    echo "CHUNK $name $f0-$f1 $(date +%H:%M:%S)"
    blender -b "$BLEND" -t "$THREADS" --python "$HERE/render_film.py" -- "$OUT" "$f0" "$f1" "$SPP" > "$OUT.log.$name" 2>&1
    echo "DONE $name $(date +%H:%M:%S)"
done < "$OUT.chunks.$ORDER"
echo ALLDONE
