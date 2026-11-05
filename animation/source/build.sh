#!/bin/bash
# Reproducible build: TTS -> score/mix -> frames -> loudness-normalised, size-targeted encode -> checks
set -e
cd "$(dirname "$0")"
FPS=24; TARGET_MB=${TARGET_MB:-14.4}; ABR=72; LUFS=-14; TP=-1.0
[ "$SKIP_AUDIO" = 1 ] || { python3 voices.py > /dev/null; python3 music.py; }
N=$(node -e "console.log(Math.ceil(require('./timeline.json').duration*$FPS))")
echo "total frames $N"
Q=$(( (N+3)/4 )); pids=()
for i in 0 1 2 3; do s=$((i*Q)); e=$(( (i+1)*Q < N ? (i+1)*Q : N )); node render.js $s $e part$i.mp4 & pids+=($!); done
for p in "${pids[@]}"; do wait $p; done
printf "file 'part0.mp4'\nfile 'part1.mp4'\nfile 'part2.mp4'\nfile 'part3.mp4'\n" > list.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i list.txt -c copy master.mp4
DUR=$(python3 -c "print($N/$FPS)")
# two-pass loudness normalisation (linear) to LUFS/TP target
J=$(ffmpeg -hide_banner -i final.wav -t $DUR -af loudnorm=I=$LUFS:TP=$TP:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
MI=$(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(f\"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}\")")
ffmpeg -y -loglevel error -i final.wav -t $DUR -af "loudnorm=I=$LUFS:TP=$TP:LRA=11:$MI:linear=true,aresample=192000,alimiter=limit=0.70:level=false:attack=1:release=60,aresample=48000" mix_norm.wav
VB=$(python3 -c "print(int(($TARGET_MB*8e6 - ${ABR}000*$DUR)/$DUR/1000))")
echo "video bitrate ${VB}k"
ffmpeg -y -loglevel error -i master.mp4 -c:v libx264 -preset slow -tune animation -b:v ${VB}k -maxrate 900k -bufsize 1800k -pass 1 -passlogfile p2 -an -f mp4 /dev/null
ffmpeg -y -loglevel error -i master.mp4 -i mix_norm.wav -map 0:v -map 1:a -c:v libx264 -preset slow -tune animation -b:v ${VB}k -maxrate 900k -bufsize 1800k -pass 2 -passlogfile p2 \
  -pix_fmt yuv420p -profile:v high -r $FPS -c:a aac -b:a ${ABR}k -ar 48000 -t $DUR -movflags +faststart out.mp4
echo "built out.mp4 ($N frames, $DUR s)"
