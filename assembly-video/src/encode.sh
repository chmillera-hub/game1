#!/bin/bash
# usage: encode.sh <video_kbps> <out.mp4>
set -e
VK=${1:-440}
OUT=${2:-final.mp4}
DUR=$(python3 -c "import json;print(json.load(open('timeline.json'))['duration'])")
printf "file '%s'\n" seg_00.mkv seg_01.mkv seg_02.mkv seg_03.mkv > segs/list.txt
[ -f segs/full.mkv ] || ffmpeg -y -loglevel error -f concat -safe 0 -i segs/list.txt -c copy segs/full.mkv
# loudness normalisation (two-pass, linear)
J=$(ffmpeg -hide_banner -i audio/mix.wav -t $DUR -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
MI=$(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_i'],d['input_tp'],d['input_lra'],d['input_thresh'],d['target_offset'])")
read II ITP ILRA ITH OFF <<< "$MI"
ffmpeg -y -loglevel error -i audio/mix.wav -t $DUR -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$II:measured_TP=$ITP:measured_LRA=$ILRA:measured_thresh=$ITH:offset=$OFF:linear=true,aresample=48000" -ac 1 -c:a aac -b:a 64k audio/final_audio.m4a
X264="-c:v libx264 -preset veryslow -tune animation -profile:v high -level 4.0 -pix_fmt yuv420p -g 240 -keyint_min 24 -bf 3 -b:v ${VK}k -maxrate $((VK*3))k -bufsize $((VK*4))k"
cd segs
ffmpeg -y -loglevel error -i full.mkv $X264 -pass 1 -passlogfile x264log -an -f mp4 /dev/null
cd ..
ffmpeg -y -loglevel error -i segs/full.mkv -i audio/final_audio.m4a -map 0:v -map 1:a $X264 -pass 2 -passlogfile segs/x264log -c:a copy -movflags +faststart -t $DUR "$OUT"
ls -l "$OUT"
