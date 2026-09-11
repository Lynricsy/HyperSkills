---
name: media-processing
description: "Engineers deterministic media work with ffmpeg and the image tools: container and codec selection, remux versus transcode, rate control that silently degrades (VP9 constant quality without -b:v 0, SVT-AV1's sentinel CRF default), filter-graph traps (scale=W:-1 producing odd heights libx264 rejects, setsar=1 corrupting display aspect ratio), frame-accurate seeking, concat, subtitles, two-pass loudnorm and the 192 kHz resample it hides, HLS and DASH packaging with keyframe-aligned GOPs, and still-image batches in libvips, sharp, ImageMagick or Pillow where EXIF orientation and ICC profiles decide whether the result is right. Use when transcoding, cutting, packaging for streaming, normalising loudness, extracting frames, generating thumbnails, or reviewing an ffmpeg command that produced an unplayable file. Do not use for framework-owned image pipelines such as the Astro image service or next/image, for image format choices made for page speed, for Office and PDF documents, or for media a model generates."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: task
---

# media-processing

Paths below are relative to this skill's directory.

## Scope

Media whose output is a function of its input: transcoding, cutting,
concatenating, filtering, packaging, loudness work, frame extraction, and
still-image batches. The tools are ffmpeg/ffprobe for anything with a
timeline, and libvips/sharp/ImageMagick/Pillow for anything that is a picture
in and a picture out.

The same input must produce the same bytes. That is the line: work whose
output varies with a model, a seed or a server-side version belongs to the
`generative-media` skill.

Not covered — do not answer from this skill:

- Framework-owned image pipelines: the Astro image service, `next/image`,
  `opengraph-image`, and any build-time asset transform the framework runs.
  Those belong to the `astro` or `react` skill.
- Which format or size a page should serve, and what that does to LCP: the
  `frontend-design` skill.
- `.docx`, `.pptx`, `.xlsx` and `.pdf`, including PDF page rasterisation and
  OCR: the `office` skill.
- Generating, editing or transcribing media with a model, and the provenance
  metadata such a model attaches: the `generative-media` skill. Muxing,
  resampling and concatenating what it returns belongs here.
- Video editing as an authoring or creative decision. This skill executes a
  specification; it does not decide pacing, framing or which take is better.

## Core rules

Each rule is an invariant. The clause after the dash is what breaks when it
is violated.

1. Probe every input with `ffprobe` before planning anything — resolution,
   SAR/DAR, frame rate, VFR suspicion, colour tags and codecs decide the
   command, and none of them are visible in the script you were handed.
2. Prefer remux or stream copy over re-encoding whenever the requested change
   does not touch pixels or samples — every re-encode is a generation loss
   that no later step can recover.
3. Never write the output over the input, and never in place — a failed run
   otherwise destroys the only copy of the source.
4. Scale with `scale=W:-2` or `scale=-2:H`, never `-1` and never `-s` —
   `-1` can compute an odd dimension, which libx264 with `yuv420p` rejects
   outright, leaving a file with no `moov` atom. `[verified]`
5. Do not append `setsar=1` to a `scale` as a reflex — `scale` preserves the
   source SAR, so forcing 1:1 on an anamorphic source changes a correct
   16:9 display into a squashed 4:3. `[verified]`
6. Put `-ss` before `-i` when re-encoding — input seeking has been
   frame-accurate since FFmpeg 2.1, and output seeking decodes and discards
   everything up to the cut point instead. `[official]`
7. Treat a `-c copy` cut as landing on the nearest keyframe, not the
   requested timestamp — report the real cut point or switch to a re-encode;
   silently delivering a clip that starts seconds early is worse.
8. Write libvpx-vp9 constant quality as `-crf N -b:v 0` — omitting `-b:v 0`
   invokes Constrained Quality instead, which looks identical on easy
   material and collapses the moment the constraint binds. `[official]`
9. Do not copy that habit to libsvtav1 — CRF is already its default rate
   control, the effective default is 35, and the `default 0` that
   `ffmpeg -h` prints is a wrapper sentinel, not a value. `[official]`
10. Pick the preset from the job, not from a habit: a fast preset for
    intermediates, the default for delivery, a slow one for archive — the
    slowest preset costs roughly 2.8x the encode time of the default for a
    few percent of quality. `[official]`
11. Add `-movflags +faststart` to MP4 and MOV meant for progressive download
    — without it the index sits at the end of the file and playback cannot
    start until the download does. Segmented delivery does not need it.
12. Normalise loudness in two passes, and follow `loudnorm` with an explicit
    `aresample` — one pass runs the dynamic path and rewrites the loudness
    range, and the filter silently resamples its output to 192 kHz. `[verified]`
13. Resample every track to a common rate before `amix` or `concat` — mixing
    mismatched rates shifts pitch, and nothing in the output warns you.
14. Fix the GOP and align it across every rendition of an ABR ladder
    (`-g` and `-keyint_min` at framerate times segment duration, plus
    `-sc_threshold 0`) — without a shared splice point the player stalls or
    glitches on every quality switch.
15. Pin the frame rate before computing a GOP from it — on a VFR phone
    recording "framerate times segment duration" is arithmetic on a number
    that does not exist, and segment durations drift.
16. Do still-image work in an image tool, never in ffmpeg — ffmpeg discards
    the EXIF block, so whether it applied the orientation first is a
    build-level default that the output no longer records either way, and
    `-q:v` is not the same scale as any image tool's quality option.
    `[verified]`
17. Assume sharp has already stripped every metadata block and converted to
    sRGB — the call you have to write is the one that *keeps* metadata, not
    the one that removes it. `[official]`
18. Apply EXIF orientation explicitly in whichever tool you chose — relying
    on an implicit autorotate ties the result to one build of one tool.
19. Convert or attach a colour profile deliberately for wide-gamut sources —
    a discarded ICC profile makes Display-P3 pixels get read as sRGB, which
    is exactly the washed-out look people report. `[verified]`
20. Preserve provenance metadata (C2PA manifests, SynthID-bearing chunks)
    through any resize or format change, or state that you are dropping it —
    the default strip in every image tool destroys it silently.
21. Re-probe the produced file and compare it against the request before
    reporting success — a zero exit status, a written file and a correct
    command are all compatible with a wrong result.
22. Look at the pixels whenever the picture changed, and say so honestly when
    you cannot — writing `pixels not inspected` is acceptable, claiming a
    visual check you did not perform is not.
23. Isolate failures in a batch: one malformed input must not abort the run,
    and the run must exit non-zero if anything failed — an overnight job that
    dies on file three silently delivers nothing.
24. Verify encoder and hardware-acceleration availability on the machine
    rather than assuming a name exists — builds differ, and a missing
    encoder surfaces as a late runtime error mid-batch.
25. Verify the font actually contains the glyphs before burning subtitles —
    libass and `drawtext` render missing glyphs as blank boxes without
    raising an error.

## Workflows

### Transcode, cut or filter

- [ ] `ffprobe` every input: duration, resolution, SAR/DAR, frame rate and
      whether it is variable, pixel format, colour tags, audio layout.
- [ ] Decide remux versus re-encode from that probe, not from the request's
      wording.
- [ ] Order the filter chain: colour → cut → concat → reframe → overlay and
      subtitles → audio → loudness → export. Reframing after overlay sizes
      the text against the wrong canvas.
- [ ] Write the command with the rate control the chosen encoder actually
      uses, and an explicit `-pix_fmt` for delivery.
- [ ] Run on one representative input first, not the whole directory.
- [ ] **Gate:** `ffprobe` the output and assert duration, dimensions, DAR,
      frame rate, pixel format and audio rate against what was asked. Any
      mismatch is a failure, not a note.

### Package an ABR ladder

- [ ] Establish the source frame rate and pin it if the source is VFR.
- [ ] Choose the segment duration, then derive one GOP length and apply the
      identical keyframe settings to every rendition.
- [ ] Encode each rendition with one rate-control strategy — capped CRF or
      two-pass ABR, not `-crf` and `-b:v` together.
- [ ] Build the master playlist from measured peak bitrates and the
      dimensions actually produced.
- [ ] **Gate:** probe the segment durations and keyframe timestamps of every
      rendition and show that the splice points coincide. Playlist metadata
      that disagrees with the segments is a failure.

### Batch still images

- [ ] Read one source file's metadata: dimensions, EXIF orientation, ICC
      profile, colour space, subsampling.
- [ ] Choose the image tool and stay in it; do not mix ffmpeg into an
      image-to-image pipeline.
- [ ] Decide explicitly, per output, whether metadata is kept or dropped.
- [ ] Apply orientation and colour conversion as explicit steps.
- [ ] **Gate:** re-read a converted file and report dimensions, orientation
      and colour profile; open at least one output and confirm it is upright
      and correctly coloured, or state that pixels were not inspected.

### Review an existing command or script

- [ ] Probe a representative input so the review is grounded in the real
      material rather than the script text.
- [ ] Separate findings into what is mechanically wrong (rate control,
      dimensions, pixel format, metadata, ordering) and what is a delivery
      decision (target resolution, quality level, preset, loudness target).
- [ ] Fix the first category; surface the second with its cost and let the
      owner decide.
- [ ] **Gate:** run the corrected command on one input and probe the result.
      A review that never executed anything reports as unverified.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Codec and container choice, CRF, presets, two-pass, HDR to SDR, hardware acceleration | Re-encoding anything, or the output looks or weighs wrong | `references/video-encoding.md` |
| Filter graphs, scaling, SAR/DAR, seeking, cutting, concat, overlay, subtitles, GIF | Building or debugging a `-vf`/`-filter_complex` chain, or a cut lands in the wrong place | `references/filters-and-editing.md` |
| Loudness, mixing, sample rates, PCM containerisation, audio codecs | Any audio-only change, or levels are inconsistent between deliverables | `references/audio.md` |
| HLS, DASH, GOP alignment, ABR ladders, live outputs | Packaging for a player, or switching quality misbehaves | `references/streaming-packaging.md` |
| Tool choice for stills, EXIF, ICC, resize semantics, thumbnails, sprite sheets | Anything that is a picture in and a picture out | `references/images.md` |
| ffprobe fields, capability discovery, delivery checks, batch failure handling | Before planning and again before declaring a job done | `references/probing-and-verification.md` |

## Output format

Report a finished job in five labelled lines. Keep the field names in
English; write the sentences in the user's language.

```
Done:   <what now exists, with the output path>
Steps:  <the operations applied, in order>
Check:  <the probed facts, each against what was requested>
Look:   <path to the frame or contact sheet you viewed, or
         "PATH (pixels not inspected; no image view available)">
Notes:  <delivery decisions left to the owner, and anything not done>
```

For a review, group findings by file and cite `path:line - finding`, keeping
mechanical defects and delivery decisions in separate lists.

## Environment

`ffmpeg` and `ffprobe` from the same build. For stills, one of `vips`
(preferred for batches), `sharp`, `magick` or Pillow. Capabilities vary per
build: check `ffmpeg -encoders`, `-filters` and `-pix_fmts` on an unfamiliar
machine before relying on `libass`, `zscale`, `libsvtav1` or any hardware
encoder.
