#!/usr/bin/env bash
# Builds one lesson video from slides + narration.
#   lesson/slides.txt   one line per slide: <png> <wav> <seconds on screen>
#   lesson/slide_NN.wav narration from the TTS step (24 kHz mono WAV)
#   lesson/intro.mp4    5 s branded bumper, picture only
# Every slide becomes a clip; the clips are joined with 0.5 s crossfades.
set -euo pipefail

DIR="${1:-./lesson}"
OUT="${2:-lesson.mp4}"
XF=0.5
WORK="$(mktemp -d)"

# 1. one clip per slide, held on screen for the time the script writer asked for
clips=("$DIR/intro.mp4")
while read -r png wav secs; do
  [ -z "$png" ] && continue
  clip="$WORK/$(basename "$png" .png).mp4"
  ffmpeg -nostdin -y -v error -loop 1 -framerate 30 -t "$secs" -i "$DIR/$png" -i "$DIR/$wav" \
    -vf "scale=1920:1080,format=yuv420p" -c:v libx264 -crf 20 \
    -c:a aac -b:a 160k -ar 48000 -ac 2 "$clip"
  clips+=("$clip")
done < "$DIR/slides.txt"

# 2. sanity check: every clip must have a picture and a sound stream with a duration
for c in "${clips[@]:1}"; do
  ffprobe -v error -show_entries stream=codec_type,duration -of csv=p=0 "$c" | grep -q audio \
    || { echo "no audio in $c" >&2; exit 1; }
done

# 3. crossfade chain
inputs=(); vchain=""; achain=""; offset=0
for i in "${!clips[@]}"; do
  inputs+=(-i "${clips[$i]}")
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${clips[$i]}")
  vchain+="[$i:v]settb=AVTB,fps=30,format=yuv420p[s$i];"
  if [ "$i" -eq 0 ]; then
    vfade="[s0]null[v0];"
    achain="[0:a]anull[a0];"
  else
    vfade+="[v$((i-1))][s$i]xfade=transition=fade:duration=$XF:offset=$offset[v$i];"
    achain+="[a$((i-1))][$i:a]acrossfade=d=$XF[a$i];"
  fi
  offset=$(echo "$offset + $dur - $XF" | bc -l)
done
last=$(( ${#clips[@]} - 1 ))

ffmpeg -y -v error "${inputs[@]}" \
  -filter_complex "${vchain}${vfade}${achain%;}" \
  -map "[v$last]" -map "[a$last]" \
  -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart "$OUT"

rm -rf "$WORK"
echo "wrote $OUT"
