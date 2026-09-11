# Video encoding

Verified against: ffmpeg N-126134-gc48230eb86-20260814 (libx264, libx265, libsvtav1, libvpx-vp9)

## Contents

- [Decide remux before you decide an encoder](#decide-remux-before-you-decide-an-encoder)
- [Container and codec selection](#container-and-codec-selection)
- [CRF is per-encoder, and the numbers do not transfer](#crf-is-per-encoder-and-the-numbers-do-not-transfer)
- [libsvtav1: the defaults ffmpeg prints are not the defaults it uses](#libsvtav1-the-defaults-ffmpeg-prints-are-not-the-defaults-it-uses)
- [libvpx-vp9: constant quality needs `-b:v 0` spelled out](#libvpx-vp9-constant-quality-needs--bv-0-spelled-out)
- [Presets: three rows, not one magic default](#presets-three-rows-not-one-magic-default)
- [CRF cannot hit a file size; two-pass ABR can](#crf-cannot-hit-a-file-size-two-pass-abr-can)
- [Playback compatibility: the four things that break players](#playback-compatibility-the-four-things-that-break-players)
- [HDR to SDR, fail closed](#hdr-to-sdr-fail-closed)
- [Hardware encoders are a property of the machine, not of the codec](#hardware-encoders-are-a-property-of-the-machine-not-of-the-codec)

## Decide remux before you decide an encoder

Transcoding is lossy, slow, and irreversible. Remuxing is none of those. Ask
whether the existing bytes already satisfy the target before picking an encoder.

Remux (`-c copy`) covers: changing container, dropping or reordering streams,
editing metadata, relocating the `moov` atom, and cutting on keyframe
boundaries when a GOP-sized offset is acceptable.

Re-encoding is forced by any of these, with no exceptions: a video filter
(`scale`, `crop`, `overlay`, `subtitles`, `fade`, `trim`), any audio
modification (`amix`, `atempo`, `volume`, `loudnorm`), burned-in subtitles, a
codec, profile, pixel-format or frame-rate change, or a bitrate target.
`[official]` A command that mixes `-vf` with `-c:v copy` is not a fast path; it
is a contradiction ffmpeg resolves by ignoring one of them.

A failing remux usually reports the real cause: `Could not find tag for codec
<x> in stream #0` means the target container cannot carry that codec, so the
decision was container selection, not encoding. `[community]`

## Container and codec selection

| Target | Container | Video | Audio | Why not something else |
|---|---|---|---|---|
| General delivery, browsers, mobile | MP4 | H.264 (`libx264`) | AAC (`aac`) | Widest decoder base; no licensing decision to make at the file level |
| Same reach, smaller files, Apple ecosystem | MP4 | HEVC (`libx265`) | AAC | Needs `-vtag hvc1`; older browsers will not decode it |
| Open-codec delivery, bandwidth-sensitive libraries | MP4 or WebM | AV1 (`libsvtav1`) | Opus | Encoding is slow and decode support is younger than H.264 |
| WebM-only pipelines | WebM | VP9 (`libvpx-vp9`) | Opus | Constant quality needs an explicit flag; see below |
| Intermediate between processing steps | MKV or MOV | `ffv1` or ProRes | `pcm_s16le`/`pcm_s24le` | Lossy intermediates stack generation loss across every pass |
| Archival master | MKV | `ffv1` | FLAC or PCM | MP4 is a delivery container, not a preservation one |

Use MP4 with H.264 and AAC as the default. For an intermediate that will be
re-encoded later, use a lossless or intra-only codec instead, so the final
encode is the only lossy step.

## CRF is per-encoder, and the numbers do not transfer

CRF numbers are encoder-private. Copying a value from an x264 recipe into an
AV1 command produces a wildly different file, and nothing warns about it.

| Encoder | Range | Effective default | Working band | Confidence |
|---|---|---|---|---|
| `libx264` | 0-51 | 23 | 17-28; 18 is visually lossless | `[official]` |
| `libx265` | 0-51 | 28 | 22-32 | `[official]` |
| `libsvtav1` | 0-63 | **35** | 25-45 | `[official]` `[verified]` |
| `libvpx-vp9` | 0-63 | none; must be given | 15-35, always with `-b:v 0` | `[official]` |

Roughly, ±6 CRF halves or doubles the bitrate on the same encoder.
`[community]` That heuristic is for estimating, never for promising a size.

True lossless is a separate mode, not the bottom of the CRF scale: `-qp 0` on
x264, `-x265-params lossless=1` on x265. Lossless H.264 needs a High 4:4:4
Predictive profile, which most hardware decoders reject. `[official]`

## libsvtav1: the defaults ffmpeg prints are not the defaults it uses

`ffmpeg -h encoder=libsvtav1` reports `-crf … (default 0)` and
`-preset … (default -2)`. Both are wrapper sentinels meaning "not set", not
values that take effect. Encoding with neither flag logs what actually ran:

```
Svt[info]: SVT [config]: preset / tune / pred struct : 8 / PSNR / random access
Svt[info]: SVT [config]: BRC mode / rate factor       : CRF / 35.00
```

`[verified]` So the real defaults are preset 8 and CRF 35, and `-h` output is
not documentation for this encoder. When a default matters, read the encoder's
own startup log instead.

Two consequences:

- CRF is already the default rate-control mode for `libsvtav1`. Do not add
  `-b:v 0`; it contributes nothing here. `[official]`
- SVT-AV1 picks a short default keyframe interval, around two to three seconds.
  Set `-g` explicitly for anything that will be segmented or seeked.
  `[official]`

`-b:v 0` belongs to exactly one place: `libaom-av1` on FFmpeg before 4.3, where
CRF mode had to be armed by zeroing the bitrate. `[official]` Carrying that
flag into any other AV1 encoder is cargo cult.

<details>
<summary>Claims to distrust if they resurface</summary>

Secondary sources still state that `libsvtav1` defaults to CRF 0, that `-b:v 0`
enables CRF mode for it, and that its default preset is around 10. All three
disagree with the encoder's own configuration log shown above. `[verified]`
</details>

## libvpx-vp9: constant quality needs `-b:v 0` spelled out

For VP9 constant quality, write both flags every time:

```bash
ffmpeg -i in.mp4 -c:v libvpx-vp9 -crf 30 -b:v 0 -row-mt 1 -c:a libopus out.webm
```

Omitting `-b:v 0`, or leaving a non-zero `-b:v` in place, silently switches the
encoder into Constrained Quality mode. `[official]` The command still looks
correct and still succeeds.

Measured on one easy-to-encode source: `-crf 30` and `-crf 30 -b:v 0` produced
byte-identical output (1,221,946 B), while `-crf 30 -b:v 256k` produced
239,192 B. `[verified]` So the flag is invisible until the constraint binds,
which is precisely why it must be written: the day a template that carries a
`-b:v` is reused, quality collapses with no diagnostic.

A non-zero `-b:v` alongside `-crf` is legitimate only when a bitrate ceiling is
actually wanted. Say so in that case, and call it Constrained Quality rather
than letting a reader assume constant quality.

## Presets: three rows, not one magic default

Preset trades encoding time for compression efficiency at the same quality. It
is a scheduling decision, and the right answer depends on what the file is for.

| Role | Preset | Reasoning |
|---|---|---|
| Intermediate, proxies, anything re-encoded later | `veryfast` | Quality loss is spent again downstream; throughput is the only thing that matters |
| Delivery | `medium` | x264's own default, and the balance point for a single output |
| Archive or a file encoded once and served many times | `slow` | Roughly 5-10% better than `medium` for a bounded time increase |

Do not default to `veryslow`. Against `medium` it costs about 280% of the
encoding time for about 3% over `slower`. `[official]` An agent asked to
process a folder will multiply that by the file count.

## CRF cannot hit a file size; two-pass ABR can

CRF targets quality, so the output size is whatever the content needs. When the
requirement is "under N megabytes", switch rate-control modes:

```bash
# bitrate = target_bytes * 8 / duration_seconds, minus the audio bitrate
ffmpeg -y -i in.mp4 -c:v libx264 -b:v 2400k -pass 1 -an -f mp4 /dev/null
ffmpeg -i in.mp4 -c:v libx264 -b:v 2400k -pass 2 -c:a aac -b:a 128k out.mp4
```

Pass 1 writes `ffmpeg2pass-0.log` in the working directory; run the two passes
in the same directory and clean the log afterwards. `[official]`

Reaching for `-maxrate`/`-bufsize` on top of CRF caps the peak, not the total,
and does not answer a size question.

Neither mode can produce quality that the bitrate cannot carry. When a size
target is only reachable by dropping below the point where artefacts become
visible, encode at that limit, report the size it produces, and say the
requested size is not achievable — then offer shorter duration, lower
resolution, lower frame rate or a more efficient codec.

## Playback compatibility: the four things that break players

When a file plays black, desyncs, or is rejected as "not supported", check
these before suspecting the encoder:

1. **Pixel format.** `-pix_fmt yuv420p` is a hard requirement for QuickTime and
   most consumer players. Encoders will happily emit `yuv444p` or 10-bit from a
   10-bit source and produce a file only ffmpeg can open. `[official]`
2. **Profile.** `-profile:v high -level 4.0` keeps H.264 inside what older
   hardware decoders accept. High 4:4:4 and 10-bit H.264 are software-only in
   practice. `[community]`
3. **HEVC tag.** Apple players and AirDrop need `-vtag hvc1`; without it the
   default `hev1` tagging is not recognised. `[community]`
4. **`moov` position.** For progressive download and browser playback, add
   `-movflags +faststart`.

On `+faststart`: it is a container-layer concern, not an encoding parameter.
Reading the top-level boxes of two otherwise identical `-c copy` outputs shows
`['ftyp','free','mdat','moov']` without it and `['ftyp','moov','free','mdat']`
with it. `[verified]` The index moves to the front so a player can start before
the download finishes. The cost is one extra full-file rewrite, which is real
I/O on large files. Add it to MP4 and MOV meant for progressive download; skip
it for purely local files, for intermediates that will be processed again, and
for segmented delivery, where the packager owns the layout.

## HDR to SDR, fail closed

Tone mapping is the one conversion where guessing produces a plausible-looking
but wrong result, so the rule is to refuse rather than approximate.

Convert only when the metadata is unambiguous: transfer is `smpte2084` (PQ) or
`arib-std-b67` (HLG) **and** primaries and matrix are BT.2020. Unknown,
missing, or mutually inconsistent colour tags mean stop and report, not
proceed. `[community]`

```bash
ffmpeg -i hdr.mov -vf "zscale=t=linear:npl=100,format=gbrpf32le,\
zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p" \
  -c:v libx264 -crf 18 -preset medium \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  out.mp4
```

Two degradations to reject outright: a bare `tonemap` without converting to
linear light first, and "just force `-pix_fmt yuv420p`" as a fallback when tone
mapping fails. Both yield washed-out or clipped images that pass a file-exists
check. `[community]`

After conversion, read back all four colour tags on the output and confirm
BT.709. A tone map that succeeded but left BT.2020 tags will be displayed
wrongly by anything that trusts metadata.

Dolby Vision and HDR10+ dynamic metadata do not survive this path. Say so, and
have a human review skin tones, highlights, shadows, gradients and saturated
colours on a trusted SDR display before the result is treated as final.

An HDR source that is merely being cut or remuxed should stay HDR: keep HEVC
Main 10 and carry the source colour tags through. Silently flattening to SDR is
a content change nobody asked for.

Log footage (S-Log, V-Log, C-Log) is tagged SDR and looks flat and grey. It is
not HDR and must not be tone mapped; it needs its LUT. Detect it by inspection,
not by assuming from the camera model.

## Hardware encoders are a property of the machine, not of the codec

Never select `h264_nvenc`, `hevc_qsv`, `h264_vaapi` or `hevc_videotoolbox`
because a previous machine had them. Capabilities vary by OS, build and distro
packaging. Probe on every unfamiliar machine and choose from what the probe
reports:

```bash
ffmpeg -version
ffmpeg -hide_banner -encoders | grep -iE 'nvenc|qsv|vaapi|videotoolbox|amf'
ffmpeg -hide_banner -hwaccels
```

Fallback order, stopping at the first one the probe confirms: platform
accelerator (`*_videotoolbox` on macOS, `*_nvenc` with NVIDIA, `*_qsv` with
Intel, `*_vaapi` on Linux with Mesa) then software (`libx264`, `libx265`,
`libsvtav1`, `libvpx-vp9`).

An encoder listed in `-encoders` can still fail at runtime when no device is
present, so treat the first successful encode as the real test. Hardware
encoders also do not accept CRF: they use `-cq`/`-qp`/`-global_quality` with
their own scales, and at equal bitrate they are consistently worse than
software. Use them for throughput, not for quality.

<!-- sources: terminalskills-ffmpeg, n0an-ffmpeg, kajisho-ffmpeg, maxazure-video, dabrlin-ffmpeg, sakydev-ffmpeg, dcloud-ffmpeg, ffmpeg-h264-docs, ffmpeg-av1-docs, ffmpeg-vp9-docs -->
