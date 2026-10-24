#!/usr/bin/env bash
# Final encode: H.264 + AAC in MP4 (plays everywhere, uploads to every social app),
# two-pass to a fixed size budget, loudness-normalised audio, soft subtitle track too.
set -euo pipefail
cd "$(dirname "$0")"
TARGET_MB=${TARGET_MB:-14.2}
ABR=${ABR:-64}
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 build/video_raw.mkv)
VKBPS=$(python3 -c "print(int(($TARGET_MB*8*1024*1024/1000/$DUR - $ABR) * 0.97))")
echo "duration ${DUR}s -> video ${VKBPS} kbps, audio ${ABR} kbps"

ffmpeg -y -loglevel error -i build/mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=9 -ar 44100 build/mix_norm.wav

X264="preset=veryslow:tune=animation:keyint=240:min-keyint=24:bframes=6:ref=6:aq-mode=3:deblock=1,1"
vopts=(-c:v libx264 -b:v ${VKBPS}k -maxrate $((VKBPS*3))k -bufsize $((VKBPS*6))k
       -x264-params "$X264" -pix_fmt yuv420p -profile:v high -level 4.0)
mkdir -p output
ffmpeg -y -loglevel error -i build/video_raw.mkv "${vopts[@]}" -pass 1 -passlogfile build/x264 -an -f mp4 /dev/null
ffmpeg -y -loglevel error -i build/video_raw.mkv -i build/mix_norm.wav -i build/subtitles.srt \
  -map 0:v -map 1:a -map 2:s "${vopts[@]}" -pass 2 -passlogfile build/x264 \
  -c:a aac -b:a ${ABR}k -ac 2 -c:s mov_text -metadata:s:s:0 language=eng \
  -movflags +faststart -t "$DUR" output/the-one-reading-this.mp4
cp build/subtitles.srt output/the-one-reading-this.srt
ls -la output/
