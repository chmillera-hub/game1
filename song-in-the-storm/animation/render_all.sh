#!/bin/bash
# usage: render_all.sh part totalFrames workers
part=$1; N=$2; K=$3
step=$(( (N + K - 1) / K ))
pids=()
for i in $(seq 0 $((K-1))); do
  a=$((i*step)); b=$(( (i+1)*step )); [ $b -gt $N ] && b=$N
  node render.js $part $a $b segs/${part}_$i.mp4 > segs/${part}_$i.log 2>&1 &
  pids+=($!)
done
wait "${pids[@]}"
(cd segs && ls ${part}_*.mp4) | sort -V | sed "s/^/file '/; s/$/'/" > segs/${part}_list.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i segs/${part}_list.txt -i ../${part}.wav -c:v copy -c:a aac -b:a 192k -shortest ../${part}_final.mp4
echo FINISHED $part
