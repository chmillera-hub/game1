#!/usr/bin/env bash
# Re-encode a rendered part to fit under a size cap (default 28.5 MiB) with a two-pass x264 encode.
# Usage: ./fit_size.sh in.mp4 out.mp4 [max_mib]
set -euo pipefail
in=$1; out=$2; cap=${3:-28.5}
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
abr=160
vbr=$(python3 -c "print(int($cap*8*1048.576/$dur - $abr - 40))")
tmp=$(mktemp -d)
ffmpeg -v error -y -i "$in" -c:v libx264 -preset slow -b:v ${vbr}k -pass 1 -passlogfile "$tmp/p" -an -f mp4 /dev/null
ffmpeg -v error -y -i "$in" -c:v libx264 -preset slow -b:v ${vbr}k -pass 2 -passlogfile "$tmp/p" \
  -pix_fmt yuv420p -c:a aac -b:a ${abr}k -movflags +faststart "$out"
rm -rf "$tmp"
echo "$out: $(du -m "$out" | cut -f1) MB (video ${vbr}k)"
