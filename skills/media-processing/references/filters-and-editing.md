# Filters and editing

Verified against: ffmpeg N-126134-gc48230eb86-20260814

## Contents

- [Filter graph syntax, and where it bites](#filter-graph-syntax-and-where-it-bites)
- [Scaling: `-2`, never `-1`, never `-s`](#scaling--2-never--1-never--s)
- [SAR, DAR, and why `setsar=1` is usually the bug](#sar-dar-and-why-setsar1-is-usually-the-bug)
- [Seeking and cutting](#seeking-and-cutting)
- [Concatenation: demuxer or filter](#concatenation-demuxer-or-filter)
- [Trimming inside a graph needs `setpts`](#trimming-inside-a-graph-needs-setpts)
- [Overlays: measure first, then compute coordinates](#overlays-measure-first-then-compute-coordinates)
- [Subtitles: burned or soft](#subtitles-burned-or-soft)
- [GIF in two passes](#gif-in-two-passes)
- [Filter ordering in a full edit](#filter-ordering-in-a-full-edit)

## Filter graph syntax, and where it bites

`-vf`/`-af` is shorthand for a single-input single-output `-filter_complex`.
The moment there is more than one input or more than one output, only
`-filter_complex` works, and mixing the two forms in one command is rejected.

Mistakes that produce confusing errors rather than obvious ones:

- Commas separate filters in a chain; semicolons separate chains. A semicolon
  where a comma belongs leaves a dangling unlabelled output and the parse error
  points at the wrong place.
- Inside filter arguments, `:` separates options and `=` assigns them. A colon
  in a value (a Windows-style path, a timestamp in `drawtext`) must be escaped,
  and the escaping is evaluated twice when the graph is inside shell quotes.
  Prefer passing paths through a variable-free relative form and avoid colons
  in filenames entirely. `[community]`
- Stream labels are consumed exactly once. Feeding `[0:v]` into two filters
  requires `split` (or `asplit`), otherwise the graph fails with an unconnected
  input.
- When any filter is present, `-c:v copy` cannot apply. The two are mutually
  exclusive by construction, not merely inadvisable. `[official]`

When a filter's options are uncertain, read them from the running binary
instead of recalling them: `ffmpeg -h filter=scale` lists the exact option
names, types and defaults for the build in hand.

## Scaling: `-2`, never `-1`, never `-s`

```bash
ffmpeg -i in.mp4 -vf "scale=1280:-2" -c:v libx264 -crf 20 -pix_fmt yuv420p out.mp4
```

`-1` preserves aspect ratio exactly and therefore produces odd dimensions on
many sources. `yuv420p` requires even width and height, so the encoder aborts:
`[libx264] width not divisible by 2 (321x241)` followed by
`Error while opening encoder`, leaving a file that later reads as
`moov atom not found`. `[verified]` The failure is input-dependent, so in batch
work it detonates on an unpredictable subset.

`-2` computes the same aspect-preserving value and rounds to an even number,
which removes the entire failure class. Use `scale=W:-2` or `scale=-2:H`.

`-s WxH` is the legacy option. It cannot express `-1`/`-2`, cannot participate
in a filter chain, and is silently ignored in some filter-graph combinations.
It is otherwise equivalent to a bare `scale`: on a 640x480 source with SAR 4:3,
`-s 320x240` and `-vf scale=320:240` both yield `320,240,SAR 4:3,DAR 16:9`.
`[verified]` There is no reason to reach for it.

To fit inside a box without cropping, combine scale and pad:

```bash
-vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:color=black,setsar=1"
```

`force_original_aspect_ratio=decrease` guarantees the result fits; `pad` with
`-1:-1` centres it. The `setsar=1` here is load-bearing, for the reason in the
next section.

## SAR, DAR, and why `setsar=1` is usually the bug

Three quantities, easy to conflate: storage dimensions (pixel counts), sample
aspect ratio (SAR, the shape of one pixel), and display aspect ratio
(DAR = width/height x SAR). A 640x480 frame with SAR 4:3 displays as 16:9.

`scale` preserves the source SAR. It does not distort the picture and it does
not need correcting. On the 640x480 SAR 4:3 source above,
`scale=320:240` yields `320,240,SAR 4:3,DAR 16:9` — still correct. `[verified]`

Appending `setsar=1` to that same command yields `320,240,SAR 1:1,DAR 4:3`.
`[verified]` The picture is now displayed at the wrong shape. The habit of
"always add `setsar=1` after `scale`" manufactures this defect on every
non-square-pixel source, which is most DVD, broadcast and anamorphic footage.

Write `setsar=1` in exactly three situations:

1. Converting a non-square-pixel source to square pixels on purpose. Then the
   storage dimensions must be recomputed to the display dimensions first
   (`scale=852:480` for the example above), and `setsar=1` records the fact.
2. After `pad` or `crop`, which change the frame geometry without touching SAR
   and can therefore leave an inconsistent DAR.
3. Before `concat`, `hstack` or `vstack`, which require every input to agree on
   SAR and will otherwise refuse or misalign.

Outside those, leave SAR alone and verify DAR on the output instead of
asserting it in the graph.

## Seeking and cutting

For any cut that re-encodes, put `-ss` (and `-to`/`-t`) before `-i`:

```bash
ffmpeg -ss 00:01:30 -i in.mp4 -to 00:02:00 -c:v libx264 -crf 20 -c:a aac out.mp4
```

Input-side seeking is both fast and frame-accurate when transcoding, from
FFmpeg 2.1 onward. `[official]` It jumps near the target and decodes forward,
so cost does not grow with the offset.

`-to` is an absolute timestamp on the same timeline as `-ss`; `-t` is a
duration. Giving both makes `-t` win. `[official]`

With `-c copy` the story changes, because no decoder runs: the cut lands on the
nearest keyframe at or before the requested time, so it can be early by up to
one GOP, commonly 1-10 seconds.

```bash
ffmpeg -ss 00:01:30 -i in.mp4 -to 00:02:00 -c copy -avoid_negative_ts make_zero cut.mp4
```

`-avoid_negative_ts make_zero` rebases timestamps so the fragment does not
carry negative PTS into a later `concat`. `[official]`

Pick one of two behaviours and be explicit about which: accept the GOP-level
offset and report where the cut actually landed (read the first keyframe time
from the output), or re-encode when the offset exceeds what the task tolerates.
A useful threshold is half a second. `[community]`

<details>
<summary>Old pattern: output-side seeking for frame accuracy</summary>

Guidance predating FFmpeg 2.1 recommended `-ss` after `-i` for accurate cuts,
on the grounds that input-side seeking only reached a keyframe and could
produce black frames. That behaviour was superseded; the old semantics are
still reachable with `-noaccurate_seek`. `[official]` Output-side seeking now
only means "decode and discard everything before the cut point", which is
slower with no accuracy benefit.
</details>

## Concatenation: demuxer or filter

The demuxer joins files without decoding and is the right tool when the inputs
already match in codec, profile, resolution, SAR, frame rate, pixel format,
sample rate and channel layout:

```bash
# list.txt: one `file 'clip1.mp4'` line per input, quotes included
ffmpeg -f concat -safe 0 -i list.txt -c copy joined.mp4
```

`-safe 0` permits absolute paths and `..` in the list. `[official]`

The trap is that the demuxer does not verify the match. Given mismatched
inputs it still writes a file; playback then breaks after the first join —
frozen video, drifting audio, or a stream a player abandons — with no error
from the muxing step. `[community]` Check the parameters with a probe before
choosing this path rather than discovering it in the player.

For heterogeneous inputs, normalise and use the `concat` filter, which decodes
and re-encodes:

```bash
ffmpeg -i a.mov -i b.mp4 -filter_complex \
"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1,setsar=1,fps=30[v0];\
 [1:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1,setsar=1,fps=30[v1];\
 [0:a]aresample=48000[a0];[1:a]aresample=48000[a1];\
 [v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]" \
 -map "[v]" -map "[a]" -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac out.mp4
```

Every input must be brought to the same resolution, SAR, frame rate and sample
rate before `concat`; the filter requires it. When a normalising re-encode is
unavoidable, say so before running it — a caller who asked for a join does not
expect a full transcode of both sources.

## Trimming inside a graph needs `setpts`

`trim` and `atrim` select a time range but leave the original timestamps.
Downstream filters then see a stream that starts at, say, 90 seconds, and
`concat` produces a long gap or drops the segment entirely.

```bash
-filter_complex "[0:v]trim=start=10:end=20,setpts=PTS-STARTPTS[v];\
                 [0:a]atrim=start=10:end=20,asetpts=PTS-STARTPTS[a]"
```

`setpts=PTS-STARTPTS` and `asetpts=PTS-STARTPTS` rebase to zero and are not
optional. The failure is silent: the graph runs, the file exists, the timing is
wrong.

## Overlays: measure first, then compute coordinates

Probe the base video's dimensions before writing overlay coordinates rather
than assuming them. `[official]` The origin `0:0` is top-left; the bottom-right
anchor is `main_w-overlay_w : main_h-overlay_h`.

```bash
ffmpeg -i base.mp4 -i logo.png -filter_complex \
  "[1:v]scale=160:-2[wm];[0:v][wm]overlay=W-w-24:H-h-24" \
  -c:a copy out.mp4
```

`W`/`H` are the base frame, `w`/`h` the overlay, which is why the expression
survives a resolution change while hard-coded pixels do not. Scale the overlay
relative to the measured base dimensions; a logo sized for 1080p is a
postage stamp on 4K and a banner on 480p.

Because frame size changes invalidate every coordinate, do all reframing before
any overlay or subtitle work.

## Subtitles: burned or soft

Soft subtitles keep the text selectable and switchable and cost no quality:

```bash
ffmpeg -i in.mp4 -i subs.srt -c copy -c:s mov_text -metadata:s:s:0 language=eng out.mp4
```

MP4 carries `mov_text`; MKV carries SRT and ASS directly. Prefer soft
subtitles whenever the player will honour them.

Burning is required for platforms that ignore subtitle tracks, and it forces a
re-encode:

```bash
ffmpeg -i in.mp4 -vf "subtitles=subs.srt:force_style='FontName=Noto Sans CJK JP,FontSize=28,Outline=2'" \
  -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a copy out.mp4
```

Two failure modes specific to burning:

- **Missing glyphs are silent.** libass and `drawtext` render tofu boxes for
  characters the font lacks and exit 0. For CJK or any non-Latin script, verify
  a font exists first (`fc-list :lang=ja file`) and pass a concrete font file
  where the renderer supports it, rather than a family name. `[community]`
- **Style is only judged visually.** Render two or three single-frame previews
  over real footage at different style settings and have a human pick one
  before committing to a full burn. `[community]` A contrast problem found
  after a forty-minute encode costs the encode twice.

Escaping inside `subtitles=` is severe: the filename passes through both shell
and filter parsing. Keep subtitle files in the working directory with plain
ASCII names.

## GIF in two passes

A single-pass GIF uses a fixed 216-colour palette and bands badly. Generate a
palette from the content first:

```bash
ffmpeg -i in.mp4 -vf "fps=15,scale=iw*0.33:-2:flags=lanczos,palettegen" -y palette.png
ffmpeg -i in.mp4 -i palette.png -filter_complex \
  "fps=15,scale=iw*0.33:-2:flags=lanczos[x];[x][1:v]paletteuse" -y out.gif
```

`fps=15` and a 0.33 scale factor are the defaults to start from; raise them
only on explicit request. `[official]` GIF size grows with frame count and
dimensions multiplicatively, and a few seconds of 30 fps full-resolution
footage produces tens of megabytes. For anything longer than a few seconds,
offer a short MP4 or WebM instead.

## Filter ordering in a full edit

When several operations combine, the order changes the result, not just the
speed:

```
colour (tone map / LUT)
  -> cut
  -> concatenate
  -> reframe (scale / crop / pad)
  -> overlay and subtitles
  -> audio (mix, levels, loudness)
  -> encode and mux
```

Colour first, because tone mapping on already-compressed intermediate output
amplifies artefacts. Reframing strictly before overlays and subtitles, because
text and logo sizes are computed against frame dimensions; doing it the other
way scales the text along with the picture and lands it at the wrong size.
Audio last, so loudness is measured on the final edit rather than on material
that later gets cut.

<!-- sources: media-os-ffmpeg, n0an-ffmpeg, kajisho-ffmpeg, vertex-genmedia-av, terminalskills-ffmpeg, cutcraft, ffmpeg-filters-docs, ffmpeg-seeking-docs -->
