# Probing and verification

Verified against: ffmpeg/ffprobe N-126134-gc48230eb86-20260814, ImageMagick 7, libvips 8.18.6

## Contents

- [Measure before planning](#measure-before-planning)
- [The probe that answers most questions](#the-probe-that-answers-most-questions)
- [Detecting variable frame rate](#detecting-variable-frame-rate)
- [Colour tags](#colour-tags)
- [Keyframe positions](#keyframe-positions)
- [Where the `moov` atom landed](#where-the-moov-atom-landed)
- [Still images](#still-images)
- [When the documentation is silent, ask the binary](#when-the-documentation-is-silent-ask-the-binary)
- [The read-back gate](#the-read-back-gate)
- [Format checks and judgement checks](#format-checks-and-judgement-checks)
- [Quality floors and refusing an impossible target](#quality-floors-and-refusing-an-impossible-target)
- [Looking at the pixels](#looking-at-the-pixels)
- [Never overwrite the input](#never-overwrite-the-input)
- [Batch runs: isolate failures](#batch-runs-isolate-failures)

## Measure before planning

Almost every wrong command in this domain comes from a guessed property:
assuming 30 fps on VFR footage, assuming square pixels on anamorphic footage,
assuming stereo on a dual-mono file, assuming sRGB on a Display-P3 image.
Probing costs milliseconds and removes the whole class.

Probe the input, decide, act, then probe the output. The last step is the one
that gets skipped, and it is the one that catches the failures that produced a
file anyway.

## The probe that answers most questions

```bash
ffprobe -v error -of json \
  -show_entries format=format_name,duration,size,bit_rate \
  -select_streams v:0 \
  -show_entries stream=codec_name,profile,width,height,sample_aspect_ratio,\
display_aspect_ratio,pix_fmt,r_frame_rate,avg_frame_rate,nb_frames,bit_rate,\
color_range,color_space,color_transfer,color_primaries \
  in.mp4
```

Always `-v error` and `-of json`. The default human-readable banner is not a
stable interface and parsing it breaks on the next build; the JSON field names
are.

For audio, swap `-select_streams a:0` and ask for
`codec_name,sample_rate,channels,channel_layout,bit_rate`.

Duration needs care. `format.duration` is the container's claim and can be
absent or wrong for streams that were cut without a rewrite. When it matters,
decode and let ffmpeg report the truth:

```bash
ffmpeg -v error -i in.mp4 -f null - 2>&1
```

That also doubles as an integrity check: silence means every packet decoded.

## Detecting variable frame rate

`r_frame_rate` is the container's nominal rate; `avg_frame_rate` is frames
divided by duration. A meaningful gap between them means the source is
variable-rate, or has dropped frames, or both. `[community]`

Confirm by looking at the actual packet timing rather than trusting the
heuristic:

```bash
ffprobe -v error -select_streams v:0 -show_entries packet=pts_time \
  -of csv=p=0 -read_intervals '%+20' in.mp4
```

Uniform deltas mean constant rate. Anything else is VFR, and every downstream
calculation that multiplies a frame rate by a duration is then invalid.

VFR is normal for screen recordings, phone capture and browser recordings. It
is not a defect to be fixed unconditionally — but any encode that depends on a
stable frame count needs `-fps_mode cfr -r <rate>` to pin it, and that
decision should be stated rather than implied.

## Colour tags

Four fields describe how the pixels should be interpreted:
`color_primaries`, `color_transfer`, `color_space`, `color_range`. They must be
read together.

- All four present and mutually consistent: proceed.
- All four absent: the file is untagged and every player guesses, usually
  BT.709. Tag the output explicitly rather than propagating the ambiguity.
- Some present and contradictory — BT.2020 primaries with a BT.709 transfer,
  say — stop and report. A conversion computed from inconsistent tags produces
  a confidently wrong image.

`color_transfer=smpte2084` (PQ) or `arib-std-b67` (HLG) together with BT.2020
primaries is HDR. A source tagged BT.709 that merely looks flat and grey is
log footage, which is a different thing and must not be tone mapped.

Verify colour tags on the output of any conversion that touched colour. A tone
map that succeeded but left the source tags in place will be displayed wrongly
by anything that trusts metadata.

## Keyframe positions

```bash
ffprobe -v error -select_streams v:0 -skip_frame nokey \
  -show_entries frame=pts_time -of csv=p=0 in.mp4
```

Three uses:

- After a stream-copy cut, report where the cut actually landed instead of
  claiming the requested timestamp.
- Before packaging, confirm the interval is the one that was configured.
- Across ABR renditions, confirm the keyframe timestamps are identical between
  variants. Different lists mean players cannot switch cleanly, and nothing
  else in the pipeline will report it.

`-skip_frame nokey` makes this cheap by discarding non-keyframes during
decode.

## Where the `moov` atom landed

Whether an MP4 starts playing before it finishes downloading is decided by box
order, which no ffprobe field exposes. Read the top-level boxes:

```bash
python3 - "$1" <<'PY'
import struct, sys
with open(sys.argv[1], 'rb') as f:
    boxes, off = [], 0
    f.seek(0, 2); end = f.tell(); f.seek(0)
    while off < end:
        hdr = f.read(8)
        if len(hdr) < 8: break
        size, kind = struct.unpack('>I4s', hdr)
        if size == 1: size = struct.unpack('>Q', f.read(8))[0]
        boxes.append(kind.decode('latin1'))
        if size == 0: break
        off += size; f.seek(off)
print(boxes)
PY
```

`['ftyp', 'moov', 'free', 'mdat']` means the index is at the front;
`['ftyp', 'free', 'mdat', 'moov']` means it is not. `[verified]`

## Still images

```bash
magick identify -format '%f %wx%h %[colorspace] icc=%[profile:icc] orient=%[EXIF:Orientation]\n' in.jpg
vips header -a in.jpg
```

`vips header -a` dumps every field libvips parsed, including `icc-profile-data`
length and the EXIF block, which makes it the quicker way to answer "did the
metadata survive".

The properties worth asserting after an image operation: pixel dimensions,
colourspace, whether an ICC profile is present, whether EXIF orientation is
present *and* whether the pixels are already upright, and the file size. An
operation that was supposed to preserve provenance and produced
`icc=` empty has failed even though it exited 0.

## When the documentation is silent, ask the binary

Capabilities vary by build, distro packaging and version. Query the binary in
hand instead of recalling defaults:

```bash
ffmpeg -hide_banner -h filter=loudnorm        # option names, types, defaults
ffmpeg -hide_banner -h encoder=libx264        # encoder-private options
ffmpeg -hide_banner -encoders | grep -i av1
ffmpeg -hide_banner -pix_fmts | grep yuv420
ffmpeg -hide_banner -hwaccels
ffmpeg -hide_banner -muxers | grep -i hls
magick -list format | grep -i avif
vips -l | grep -i thumbnail
```

One caveat that makes this less absolute than it looks: the `(default N)`
printed by `-h encoder=` can be a wrapper sentinel meaning "unset" rather than
the value that takes effect. `[verified]` When a default matters, run a
throwaway encode and read what the encoder logs about its own configuration.

Capability probing is a prerequisite on an unfamiliar machine, not an optional
extra — but it is not free either, since `-filters` and `-encoders` enumerate
everything. Run it once per session and reuse the answer.

Report a missing capability as a missing capability. Discovering that a build
lacks `libass` or `zscale` at the point of a forty-minute render is the
avoidable outcome.

## The read-back gate

Writing a command is not doing the job. A delivery passes only when all of
these hold:

1. The process exited zero.
2. The output exists and is non-trivially sized.
3. A fresh probe of the output matches what was requested — every field that
   was supposed to change, and every field that was supposed to stay.
4. A full decode is clean: `ffmpeg -v error -i out.mp4 -f null -` prints
   nothing.
5. If the picture changed, the pixels have been looked at.

Step 3 is where most silent failures surface, because several of them produce
a plausible file: a mismatched-input concat, a filter that was dropped because
`-c copy` was also present, a loudness pass that moved the sample rate to
192 kHz, an image operation that stripped the ICC profile.

## Format checks and judgement checks

Split every discrepancy into two classes before acting on it. The split is the
difference between fixing a file and altering someone's content.

| Class | Fields | Response |
|---|---|---|
| Format | Codec, profile, pixel format, dimensions, SAR, colour tags, container flags, sample rate, channel layout, true peak, VFR | Mechanical. Fix and re-run; no consultation needed |
| Judgement | Duration, framing and aspect choice, frame rate, integrated loudness, which region was cropped, which take was used | Changing these changes the content. Report the mismatch and let a human decide |

A true peak of -0.2 dBTP is a format problem with one correct answer. An
integrated loudness of -19 LUFS against a -14 target is a judgement problem,
because the fix is audible.

## Quality floors and refusing an impossible target

| Stream | Floor | Below this |
|---|---|---|
| H.264 | CRF 28 | Blocking in gradients and motion |
| HEVC | CRF 32 | The same, at higher resolutions |
| VP9 | CRF 40 | Visible smearing |
| AAC | 128 kbit/s stereo | Audible artefacts on cymbals and sibilance |

When a requested file size can only be reached by crossing a floor, do not
cross it silently. Encode at the floor, report the size that produces, and say
plainly that the requested size is not achievable at acceptable quality. Then
name the levers that do exist: shorter duration, lower resolution, lower frame
rate, a more efficient codec.

For inputs above roughly 1 GB, confirm the plan before starting. A parameter
error discovered after a long encode costs the encode twice.

## Looking at the pixels

Any change to the picture needs a visual check, because no probe field detects
a misplaced overlay, an unreadable subtitle, a wrong crop or a tone map that
crushed the highlights.

```bash
ffmpeg -i out.mp4 -vf "fps=1/10,scale=320:-2,tile=4x4" -frames:v 1 sheet.png
```

Then read the image. If images cannot be viewed, say exactly that — for
example `Look: sheet.png (pixels not inspected)` — rather than describing a
result that was never seen.

For a human review pass, build a proxy rather than shipping the master: 720p or
smaller, 24 fps, H.264 and AAC, `-movflags +faststart`, with a `REVIEW PROXY`
label and running timecode burned into a corner. Reviewers then quote visible
timecodes, and the proxy can never be mistaken for the deliverable.

## Never overwrite the input

Derive output paths from input paths in a different directory. Write to a
temporary name, run the read-back gate against it, and only then move it into
place. A failed verification leaves the previous output intact.

When a job depends on a specific source revision, record the source SHA-256 and
re-check it before promoting. A source that changed under a long-running job
means the result describes something else; fail closed rather than publishing
it.

## Batch runs: isolate failures

One malformed asset must not end the run. Wrap each item, record the failure,
continue, and report a summary at the end:

```bash
fail=0
for f in in/*.mp4; do
  out="out/$(basename "${f%.*}").mp4"
  if ffmpeg -v error -y -i "$f" -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac "$out" \
     && ffmpeg -v error -i "$out" -f null - ; then
    echo "ok   $f"
  else
    echo "FAIL $f" >&2; rm -f "$out"; fail=1
  fi
done
exit "$fail"
```

Three properties that matter: the partial output of a failed item is removed so
nothing half-written enters the output directory, each item is verified rather
than merely attempted, and the overall exit status is non-zero when anything
failed so a caller can detect it.

Do not run more concurrent ffmpeg processes than there are cores; ffmpeg
already threads internally, and oversubscribing makes a batch slower while
making failures harder to attribute. For image batches, where each process is
single-threaded and short, parallelism up to the core count is worth it.

<!-- sources: kajisho-ffmpeg, maxazure-video, dabrlin-ffmpeg, sakydev-ffmpeg, media-os-ffmpeg, dcloud-ffmpeg, imagemagick-docs, libvips-docs, ffmpeg-filters-docs -->
