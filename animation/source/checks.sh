#!/bin/bash
cd "$(dirname "$0")"; F=${1:-out.mp4}
echo "== metadata"; ffprobe -v error -show_entries format=duration,size,bit_rate:stream=codec_name,profile,width,height,r_frame_rate,pix_fmt,sample_rate,channels,duration,bit_rate,nb_frames -of compact $F
echo "== decoded video frames"; ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 $F
echo "== loudness (EBU R128)"; ffmpeg -hide_banner -nostats -i $F -map 0:a -af ebur128=peak=true -f null - 2>&1 | grep -A20 "Summary" | grep -E "I:|LRA:|Peak:"
echo "== black segments (>=0.5s)"; ffmpeg -hide_banner -nostats -i $F -vf blackdetect=d=0.5:pix_th=0.08 -an -f null - 2>&1 | grep -o "black_start.*" || echo none
echo "== frozen segments (>=2s)"; ffmpeg -hide_banner -nostats -i $F -vf freezedetect=n=0.001:d=2 -an -f null - 2>&1 | grep -oE "freeze_(start|duration|end): [0-9.]+" | paste - - - || echo none
echo "== decode errors"; ffmpeg -v error -i $F -f null - 2>&1 | head -3; echo "(end)"
echo "== silence in audio (>=3s below -50dB)"; ffmpeg -hide_banner -nostats -i $F -af silencedetect=n=-50dB:d=3 -vn -f null - 2>&1 | grep -oE "silence_(start|end): [0-9.]+" || echo none
echo "== SSIM vs master"; ffmpeg -hide_banner -nostats -i $F -i master.mp4 -lavfi "[0:v][1:v]ssim" -f null - 2>&1 | grep -oE "All:[0-9.]+"
echo "== first frame mean luma"; ffmpeg -v error -i $F -vframes 1 -vf format=gray -f rawvideo - | python3 -c "import sys,numpy as np;print(np.frombuffer(sys.stdin.buffer.read(),np.uint8).mean())"
