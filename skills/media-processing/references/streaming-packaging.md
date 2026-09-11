# Streaming packaging

Verified against: ffmpeg N-126134-gc48230eb86-20260814

## Contents

- [Keyframes decide whether packaging works](#keyframes-decide-whether-packaging-works)
- [Variable frame rate breaks the `-g` arithmetic](#variable-frame-rate-breaks-the--g-arithmetic)
- [`hls_time` is a lower bound](#hls_time-is-a-lower-bound)
- [VOD playlists and live windows are mutually exclusive modes](#vod-playlists-and-live-windows-are-mutually-exclusive-modes)
- [fMP4 and CMAF](#fmp4-and-cmaf)
- [Building an ABR ladder](#building-an-abr-ladder)
- [BANDWIDTH must be measured, not copied from `-b:v`](#bandwidth-must-be-measured-not-copied-from--bv)
- [DASH](#dash)
- [Multiple destinations with `tee`](#multiple-destinations-with-tee)
- [RTMP and SRT](#rtmp-and-srt)
- [What segmented delivery does not need](#what-segmented-delivery-does-not-need)

## Keyframes decide whether packaging works

A segment can only begin at a keyframe. If keyframes fall wherever the encoder
feels like putting them, segments end up at irregular lengths, and — the part
that actually breaks playback — different ABR renditions get their keyframes in
different places, so there is no common splice point and a player switching
bitrate either stalls or shows a glitch.

Pin the GOP on every rendition, with the same numbers:

```bash
# 30 fps source, 4-second segments -> GOP of 120 frames
-g 120 -keyint_min 120 -sc_threshold 0
```

`-g` is the maximum GOP length in frames, `-keyint_min` the minimum, and
`-sc_threshold 0` disables the extra keyframes x264 would insert at scene
changes. `[official]` All three are needed: without `-keyint_min` the encoder
may still shorten a GOP, and without `-sc_threshold 0` a scene cut inserts an
unplanned keyframe that shifts nothing in this rendition but does not exist in
the others.

For x265 the scene-cut control lives in the encoder's own parameter string:
`-x265-params "keyint=120:min-keyint=120:scenecut=0"`. `[community]`

The frame-count form is arithmetic on the frame rate, so it is only correct
when the frame rate is known and constant. The time-based form is not:

```bash
-force_key_frames "expr:gte(t,n_forced*4)"
```

This requests a keyframe every four seconds of presentation time regardless of
frame rate. `[official]` Use it when the frame rate is variable or unknown, and
use `-g`/`-keyint_min` when it is pinned. Do not use both; they express the
same intent through different mechanisms and the result is harder to predict
than either alone.

Segmenting with `-f segment` obeys the same rule — segments land on keyframes,
so `-segment_time 60` without forced keyframes gives approximately 60 seconds:

```bash
ffmpeg -i in.mp4 -c:v libx264 -crf 20 -force_key_frames "expr:gte(t,n_forced*60)" \
  -c:a aac -f segment -segment_time 60 -reset_timestamps 1 part_%03d.mp4
```

`-reset_timestamps 1` restarts each segment's timeline at zero, which is what
downstream tools expect from an independent file. `[official]`

## Variable frame rate breaks the `-g` arithmetic

Screen recordings, phone footage and anything that came out of a browser
capture are frequently VFR. "GOP = fps x segment duration" has no meaning for
them: the nominal frame rate is an average, so a 120-frame GOP is four seconds
in one stretch and nine in another.

Detect it before packaging by comparing the container's nominal rate with the
average actually achieved, and by looking at the spread of frame durations. A
noticeable gap between `r_frame_rate` and `avg_frame_rate` means treat the
source as VFR. `[community]`

Two ways out, both acceptable, one to be chosen deliberately:

- Pin the frame rate during the packaging encode with `-fps_mode cfr -r 30`,
  then the frame-count GOP arithmetic holds again.
- Keep the source timing and switch to `-force_key_frames` with a time
  expression.

Doing neither produces a ladder whose renditions cannot be switched between,
and the symptom shows up only on a real player under bandwidth change.

## `hls_time` is a lower bound

`-hls_time 4` asks the muxer to close a segment once four seconds have
elapsed *and* a keyframe is available. `[official]` With a 10-second GOP,
every segment is 10 seconds. Aligning `hls_time` with the GOP duration is what
makes the requested length the actual length; the option on its own cannot
force anything.

Segment length is a latency/overhead trade: 2 seconds for lower latency and
more requests, 6 seconds for fewer requests and more buffering. Four is a
reasonable default for VOD.

```bash
ffmpeg -i in.mp4 \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p \
  -g 120 -keyint_min 120 -sc_threshold 0 \
  -c:a aac -b:a 128k -ar 48000 \
  -f hls -hls_time 4 -hls_playlist_type vod \
  -hls_segment_filename 'seg_%04d.ts' out.m3u8
```

## VOD playlists and live windows are mutually exclusive modes

`-hls_playlist_type vod` (and `event`) promises the playlist only grows and
nothing is ever removed. `-hls_flags delete_segments` removes segments that
have scrolled out of the window. The two contradict each other and cannot be
combined. `[official]`

| Mode | Options | Resulting playlist |
|---|---|---|
| VOD | `-hls_playlist_type vod` | Complete, ends with `#EXT-X-ENDLIST`, all segments retained |
| Live sliding window | `-hls_list_size 6 -hls_flags delete_segments+append_list` | Last six segments on disk, older ones deleted |
| Live, full archive | `-hls_playlist_type event -hls_list_size 0` | Grows without bound; keep the disk in mind |

`-hls_list_size 0` means unlimited and is the right pairing for VOD.

## fMP4 and CMAF

```bash
-f hls -hls_segment_type fmp4 -hls_fmp4_init_filename init.mp4 -hls_time 4
```

Fragmented MP4 segments are the same media that DASH uses, so one set of
segments can serve both manifests. `[official]` They also allow HEVC and AV1,
which MPEG-TS segments do not carry cleanly. Choose fMP4 unless a specific
legacy player requires `.ts`.

The init segment is not optional and not implied — publish `init.mp4`
alongside the media segments. A ladder that works locally and 404s in
production is usually a missing init segment.

## Building an ABR ladder

Every rendition must share: codec, profile constraints where players are
fussy, GOP structure and duration, audio codec, sample rate and channel
layout. Only resolution and bitrate vary.

```bash
ffmpeg -i in.mp4 \
 -filter_complex "[0:v]split=3[v1][v2][v3];\
  [v1]scale=1920:-2[v1out];[v2]scale=1280:-2[v2out];[v3]scale=854:-2[v3out]" \
 -map "[v1out]" -c:v:0 libx264 -b:v:0 5000k -maxrate:v:0 5350k -bufsize:v:0 7500k \
 -map "[v2out]" -c:v:1 libx264 -b:v:1 2800k -maxrate:v:1 2996k -bufsize:v:1 4200k \
 -map "[v3out]" -c:v:2 libx264 -b:v:2 1400k -maxrate:v:2 1498k -bufsize:v:2 2100k \
 -map a:0 -map a:0 -map a:0 -c:a aac -b:a 128k -ar 48000 -ac 2 \
 -preset medium -pix_fmt yuv420p -g 120 -keyint_min 120 -sc_threshold 0 \
 -f hls -hls_time 4 -hls_playlist_type vod -hls_segment_type fmp4 \
 -master_pl_name master.m3u8 \
 -var_stream_map "v:0,a:0 v:1,a:1 v:2,a:2" \
 stream_%v/playlist.m3u8
```

ABR uses bitrate targets rather than CRF, because a player needs to know in
advance what a rendition costs. `-maxrate` with `-bufsize` caps the peak so a
rendition cannot exceed the bandwidth its manifest advertises.

Rungs roughly 1.5x-2x apart give a player useful choices; closer spacing wastes
encoding time on renditions it will skip. Cap the ladder at the source
resolution — upscaling spends bitrate to reproduce nothing.

## BANDWIDTH must be measured, not copied from `-b:v`

`BANDWIDTH` in the master playlist is the *peak* segment bitrate, not the
average target. Copying `-b:v` into it under-declares the rendition, and a
player that sizes its buffer from that number stalls on the densest segment.

Compute it from the segments that were actually produced: for each segment,
bytes x 8 / segment duration; `BANDWIDTH` is the maximum of those, and
`AVERAGE-BANDWIDTH` is total bytes x 8 / total duration. Round up. `[community]`

`ffmpeg`'s own master playlist is a starting point, not a finished artefact.
Verify the declared values against the files on disk before publishing.

## DASH

```bash
ffmpeg -i in.mp4 -map 0 -c:v libx264 -crf 20 -g 120 -keyint_min 120 -sc_threshold 0 \
  -c:a aac -b:a 128k -f dash -seg_duration 4 -use_template 1 -use_timeline 1 \
  out.mpd
```

`-use_template 1 -use_timeline 1` produces a segment template with an explicit
timeline, which tolerates segments whose durations are not perfectly uniform —
and after the keyframe discussion above, they will not be. `[official]`

The same fMP4 segments can back both an MPD and an HLS master playlist; that is
the practical reason to prefer CMAF packaging over generating two sets.

## Multiple destinations with `tee`

Encode once, write several outputs, instead of running one encode per
destination:

```bash
ffmpeg -i in.mp4 -c:v libx264 -crf 20 -g 120 -keyint_min 120 -sc_threshold 0 -c:a aac \
  -f tee -map 0:v -map 0:a \
  "[f=hls:hls_time=4:hls_playlist_type=vod]out.m3u8|\
   [f=mp4:movflags=+faststart]out.mp4"
```

Options inside each bracket apply to that output only, and `|` separates
outputs. A failure on one branch takes the whole command down by default;
`onfail=ignore` on a branch keeps the others alive when one destination is
expendable. `[official]`

## RTMP and SRT

RTMP carries H.264 plus AAC only, needs `-f flv`, and wants a 2-second
keyframe interval because that is what ingest services segment on.

```bash
ffmpeg -re -i in.mp4 -c:v libx264 -preset veryfast -b:v 4500k -maxrate 4500k -bufsize 9000k \
  -g 60 -keyint_min 60 -sc_threshold 0 -pix_fmt yuv420p \
  -c:a aac -b:a 160k -ar 44100 -f flv rtmp://host/app/key
```

`-re` reads the input at its native rate and is required when streaming a file;
without it ffmpeg pushes as fast as it can and the server drops the connection.

SRT tolerates packet loss over the open internet where RTMP does not, carries
MPEG-TS, and is configured through the URL query
(`srt://host:9000?mode=caller&latency=200000`, latency in microseconds).
`[community]` Use RTMP for services that only accept it, SRT for contribution
links over unreliable networks.

Treat the stream key as a secret: it appears in the process list and in shell
history when written inline. Pass it through an environment variable.

## What segmented delivery does not need

`-movflags +faststart` is a progressive-download fix: it relocates the index of
a single MP4 so playback can start before the download completes. Segments are
already small and already indexed by the playlist, so the flag buys nothing and
costs a full rewrite per segment. Leave it off for HLS and DASH outputs, and
keep it for the standalone MP4 that often ships alongside them.

<!-- sources: media-os-ffmpeg, kajisho-ffmpeg, terminalskills-ffmpeg, ffmpeg-formats-docs, ffmpeg-h264-docs -->
