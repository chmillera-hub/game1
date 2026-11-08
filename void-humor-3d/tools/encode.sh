#!/usr/bin/env bash
# Size-targeted final encode: frames + mix + burned-in subtitles -> MP4 (BT.709, faststart).
#   tools/encode.sh 14.6            -> The_Void_Has_a_Sense_of_Humor.mp4   (H.264 High, 2-pass, AAC 64k)
#   tools/encode.sh 14.6 hevc       -> The_Void_Has_a_Sense_of_Humor_hevc.mp4 (x265 2-pass, hvc1 tag)
# Inputs: out/frames/%05d.jpg (24 fps), out/mix.wav, out/subs.ass, assets/fonts/
set -euo pipefail
cd "$(dirname "$0")/.."
MB=${1:-14.6}
CODEC=${2:-h264}
AK=${AK:-64}
N=$(ls out/frames/*.jpg | wc -l)
DUR=$(python3 -c "print($N/24)")
VK=$(python3 -c "print(int(($MB*8*1000*0.985/$DUR) - $AK - 2))")
echo "frames=$N dur=${DUR}s target=${MB}MB -> video ${VK} kbps + audio ${AK} kbps ($CODEC)"
VF="subtitles=out/subs.ass:fontsdir=assets/fonts,format=yuv420p"
COL="-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv"
mkdir -p out/enc
if [ "$CODEC" = "hevc" ]; then
  OUT=The_Void_Has_a_Sense_of_Humor_hevc.mp4
  P="aq-mode=3:psy-rd=1.0:psy-rdoq=1.0:deblock=-1,-1:bframes=8:rc-lookahead=60:colorprim=bt709:transfer=bt709:colormatrix=bt709"
  ffmpeg -y -loglevel warning -framerate 24 -i out/frames/%05d.jpg -vf "$VF" -c:v libx265 -preset slow -b:v ${VK}k \
    -x265-params "pass=1:stats=out/enc/x265.log:$P" $COL -an -f null /dev/null
  ffmpeg -y -loglevel warning -framerate 24 -i out/frames/%05d.jpg -i out/mix.wav -vf "$VF" -c:v libx265 -preset slow -b:v ${VK}k \
    -x265-params "pass=2:stats=out/enc/x265.log:$P" -tag:v hvc1 $COL -c:a aac -b:a ${AK}k -ac 2 -ar 44100 \
    -shortest -movflags +faststart "$OUT"
else
  OUT=The_Void_Has_a_Sense_of_Humor.mp4
  X="aq-mode=3:aq-strength=0.8:deblock=1,1:psy-rd=0.6,0.0:bframes=6:b-adapt=2:ref=6:me=umh:subme=9:rc-lookahead=60"
  ffmpeg -y -loglevel warning -framerate 24 -i out/frames/%05d.jpg -vf "$VF" -c:v libx264 -preset veryslow -profile:v high \
    -b:v ${VK}k -pass 1 -passlogfile out/enc/x264 -x264-params "$X" $COL -an -f null /dev/null
  ffmpeg -y -loglevel warning -framerate 24 -i out/frames/%05d.jpg -i out/mix.wav -vf "$VF" -c:v libx264 -preset veryslow -profile:v high \
    -b:v ${VK}k -pass 2 -passlogfile out/enc/x264 -x264-params "$X" $COL -c:a aac -b:a ${AK}k -ac 2 -ar 44100 \
    -shortest -movflags +faststart "$OUT"
fi
ls -l "$OUT" | awk '{printf "%s  %.2f MB\n", $9, $5/1e6}'
