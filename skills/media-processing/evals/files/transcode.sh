#!/usr/bin/env bash
# Nightly batch: turn the day's camera uploads into web deliverables.
# Sources are mixed: 1080p phone clips, a 640x480 SD camera (anamorphic),
# and occasional 4K drone footage.
set -euo pipefail

IN_DIR="${1:-./incoming}"
OUT_DIR="${2:-./web}"
mkdir -p "$OUT_DIR"

for f in "$IN_DIR"/*.mp4; do
  base="$(basename "$f" .mp4)"

  # 1. WebM for the players that still ask for it
  ffmpeg -y -i "$f" \
    -c:v libvpx-vp9 -crf 32 \
    -c:a libopus -b:a 128k \
    "$OUT_DIR/$base.webm"

  # 2. MP4 at 1280 wide, keep aspect ratio
  ffmpeg -y -i "$f" \
    -vf "scale=1280:-1,setsar=1" \
    -c:v libx264 -preset veryslow -crf 23 \
    -c:a aac -b:a 128k \
    "$OUT_DIR/$base-720.mp4"

  # 3. 10 second preview starting at 00:01:30
  ffmpeg -y -i "$f" -ss 00:01:30 -t 10 \
    -c:v libx264 -crf 28 -an \
    "$OUT_DIR/$base-preview.mp4"
done

echo "done: $OUT_DIR"
