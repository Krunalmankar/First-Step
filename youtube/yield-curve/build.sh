#!/bin/bash
# Renders the SimpleMoney yield-curve video: 4 parallel video chunks, then joins them and adds the narration.
# Usage: ./build.sh <original-video-or-audio> <out.mp4>
set -e
SRC=$1; OUT=$2; W=$(mktemp -d)
DUR=$(node -e "console.log(4.0 + 708.67 + 10.0)")
N=4; STEP=$(node -e "console.log(($DUR/$N).toFixed(3))")
for i in $(seq 0 $((N-1))); do
  A=$(node -e "console.log(($i*$STEP).toFixed(3))"); B=$(node -e "console.log(Math.min($DUR,($i+1)*$STEP).toFixed(3))")
  node render.mjs --chunk $A $B $W/part$i.mp4 > $W/log$i.txt 2>&1 &
done
wait
for i in $(seq 0 $((N-1))); do echo "file '$W/part$i.mp4'"; done > $W/list.txt
ffmpeg -loglevel error -y -f concat -safe 0 -i $W/list.txt -c copy $W/video.mp4
# narration: delayed 4 s for the disclaimer card; a quiet music tail under the 10 s end card
ffmpeg -loglevel error -y -i "$SRC" -i ../intro/music-bed.wav -filter_complex \
  "[0:a]adelay=4000|4000,apad=whole_dur=${DUR}[v];[1:a]atrim=20:30,asetpts=PTS-STARTPTS,volume=-14dB,afade=t=in:d=1.5,afade=t=out:st=7:d=3,adelay=712670|712670,apad=whole_dur=${DUR}[m];[v][m]amix=inputs=2:normalize=0:duration=first[a]" \
  -map "[a]" -c:a pcm_s16le -ar 48000 $W/audio.wav
ffmpeg -loglevel error -y -i $W/video.mp4 -i $W/audio.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart "$OUT"
cat $W/log*.txt | grep -iE "error" || true
echo "done: $OUT"
