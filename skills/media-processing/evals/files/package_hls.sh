#!/usr/bin/env bash
# Package a lecture recording into an ABR HLS ladder for the web player.
# Sources are screen recordings and phone-shot talking heads.
set -euo pipefail

IN="${1:?input file}"
OUT="${2:-hls}"
mkdir -p "$OUT"

package() {
  local name="$1" height="$2" vbitrate="$3" abitrate="$4"
  ffmpeg -y -i "$IN" \
    -vf "scale=-2:$height" \
    -c:v libx264 -b:v "$vbitrate" -crf 23 \
    -c:a aac -b:a "$abitrate" \
    -f hls \
    -hls_time 6 \
    -hls_playlist_type vod \
    -hls_segment_filename "$OUT/${name}_%03d.ts" \
    "$OUT/$name.m3u8"
}

package 1080p 1080 5000k 192k
package 720p   720 2800k 128k
package 480p   480 1400k 128k

cat > "$OUT/master.m3u8" <<'EOF'
#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080
1080p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720
720p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=854x480
480p.m3u8
EOF

echo "packaged into $OUT"
