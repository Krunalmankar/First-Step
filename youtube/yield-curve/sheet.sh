#!/bin/bash
# sheet.sh <dir> <out.png> t1 t2 t3 t4 [t5 t6]: tiles stills in a 2-column grid at half size
d=$1; out=$2; shift 2; ins=""; n=0
for t in "$@"; do ins="$ins -i $d/t$t.png"; n=$((n+1)); done
lay=""; for ((i=0;i<n;i++)); do c=$((i%2)); r=$((i/2)); x=$([ $c -eq 0 ] && echo 0 || echo w0); y=""; for ((k=0;k<r;k++)); do y="${y:+$y+}h0"; done; lay="$lay${lay:+|}${x}_${y:-0}"; done
ffmpeg -loglevel error -y $ins -filter_complex "xstack=inputs=$n:layout=$lay,scale=1920:-1" $out
