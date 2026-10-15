#!/usr/bin/env bash
# Two-pass loudness normalisation for podcast masters (-16 LUFS integrated, -1.5 dBTP).
# Pass 1 measures, pass 2 feeds every measured value back with linear=true, so pass 2
# should be nothing more than a fixed gain change.
set -euo pipefail

in="$1"
out="${in%.*}.norm.wav"

stats=$(ffmpeg -hide_banner -nostats -i "$in" \
  -af loudnorm=I=-16:LRA=7:TP=-1.5:print_format=json -f null - 2>&1 \
  | sed -n '/^{/,/^}/p')
echo "$stats" > "${in%.*}.pass1.json"

mi=$(jq -r .input_i <<<"$stats")
mlra=$(jq -r .input_lra <<<"$stats")
mtp=$(jq -r .input_tp <<<"$stats")
mth=$(jq -r .input_thresh <<<"$stats")
off=$(jq -r .target_offset <<<"$stats")

ffmpeg -y -hide_banner -i "$in" \
  -af "loudnorm=I=-16:LRA=7:TP=-1.5:measured_I=$mi:measured_LRA=$mlra:measured_TP=$mtp:measured_thresh=$mth:offset=$off:linear=true" \
  -c:a pcm_s24le "$out"
