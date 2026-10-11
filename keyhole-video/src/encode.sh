#!/bin/bash
# usage: encode.sh <dir> <outname>   (two-pass H.264 ~400 kbps + AAC 96 kbps, ~13.5 MB for 3:44)
set -e
cd $1
ffmpeg -y -hide_banner -loglevel error -i video_hq.mp4 -c:v libx264 -preset veryslow -tune animation -b:v 400k -pass 1 -passlogfile p2 -an -f mp4 /dev/null
ffmpeg -y -hide_banner -loglevel error -i video_hq.mp4 -i ../build/mix_norm.wav -map 0:v -map 1:a -c:v libx264 -preset veryslow -tune animation \
  -b:v 400k -maxrate 1200k -bufsize 2400k -pass 2 -passlogfile p2 -pix_fmt yuv420p -c:a aac -b:a 96k -ac 2 -movflags +faststart -shortest $2
