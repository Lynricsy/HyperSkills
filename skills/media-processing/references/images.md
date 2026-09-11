# Images

Verified against: ffmpeg N-126134-gc48230eb86-20260814, libvips 8.18.6, Pillow 12.3.0

## Contents

- [ffmpeg is not an image processor](#ffmpeg-is-not-an-image-processor)
- [What ffmpeg is for: frames in and out of video](#what-ffmpeg-is-for-frames-in-and-out-of-video)
- [Choosing the image tool](#choosing-the-image-tool)
- [sharp strips metadata by default; preserving is the explicit act](#sharp-strips-metadata-by-default-preserving-is-the-explicit-act)
- [Metadata loss is a provenance problem, not only a colour one](#metadata-loss-is-a-provenance-problem-not-only-a-colour-one)
- [ImageMagick geometry has four modes and one trap](#imagemagick-geometry-has-four-modes-and-one-trap)
- [`mogrify` rewrites in place](#mogrify-rewrites-in-place)
- [Bulk thumbnails: shrink on load](#bulk-thumbnails-shrink-on-load)
- [Pillow](#pillow)
- [Quality scales do not transfer between formats](#quality-scales-do-not-transfer-between-formats)
- [Sprite sheets](#sprite-sheets)

## ffmpeg is not an image processor

Any job whose input is an image and whose output is an image goes to an
imaging library. Not ffmpeg. This holds for format conversion, compression,
resizing and batch processing alike.

Reproduced on a 640x480 JPEG carrying EXIF `Orientation=6` and `Make=ACME`:

| Command | Output size | EXIF Orientation | EXIF Make |
|---|---|---|---|
| source | 640x480 | 6 | ACME |
| `ffmpeg -i src.jpg -q:v 2 out.jpg` | **480x640** | **absent** | **absent** |
| `ffmpeg -noautorotate -i src.jpg -q:v 2 out.jpg` | 640x480 | **absent** | **absent** |
| `vips copy src.jpg out.jpg[Q=90]` | 640x480 | 6 | ACME |

`[verified]` Two separate things happen, and only one of them is stable.
ffmpeg dropped the entire EXIF block in every case. Whether it *applied* the
orientation before dropping it is a build-level default: this build rotated
by default and stopped the instant `-noautorotate` was passed. An embedded
ICC profile, by contrast, is passed through.

That combination is the trap, and it is worse than a plain rotation bug. The
tag is gone from the output, so the rotation is either baked in or
permanently lost with nothing left to record which. A batch that produces
upright thumbnails on the machine it was written on produces sideways ones on
a build whose default differs, and no downstream consumer can repair them
because the evidence was discarded. Do not reason about which way a given
build behaves; take the work out of ffmpeg and apply orientation explicitly.

The second reason is the quality scale. `-q:v` on the mjpeg encoder is a
quantiser from 2 to 31 where lower is better; `magick -quality 85` and
`sharp.jpeg({quality: 85})` are a 0-100 perceptual scale where higher is
better. They are not convertible, so a `-q:v` value cannot be derived from a
requested "quality 85" and any mapping written down is a guess.

## What ffmpeg is for: frames in and out of video

```bash
# one frame at a timestamp; PNG so the still is not re-compressed
ffmpeg -ss 00:00:05 -i in.mp4 -frames:v 1 frame.png

# one frame every 10 s, tiled into a contact sheet
ffmpeg -i in.mp4 -vf "fps=1/10,scale=320:-2,tile=4x4" -frames:v 1 sheet.png

# image sequence back to video
ffmpeg -framerate 30 -i frame_%04d.png -c:v libx264 -crf 18 -pix_fmt yuv420p out.mp4
```

`-framerate` must precede `-i` when reading a sequence; after `-i` it sets the
output rate and ffmpeg duplicates or drops frames to reach it. The
`%04d` pattern requires contiguous zero-padded numbering starting at the value
given by `-start_number`, defaulting to 0; a gap ends the read silently at the
gap.

Handing those extracted stills to an imaging library for cropping, compression
or annotation is the correct next step, not a detour.

## Choosing the image tool

Use libvips — the `vips`/`vipsthumbnail` CLI, or the `sharp` binding in a Node
project. It streams rather than loading whole images into memory, which is
what makes large batches finish. For compositing, text annotation, PDF or SVG
rasterisation and the long tail of format oddities, use ImageMagick instead.

Pillow belongs in the same conversation only when Python is already the
project's imaging layer; its pitfalls are below.

ImageMagick v7's single entry point is `magick`. `convert` is the legacy v6
name and on v7 it is a compatibility shim, so write `magick` and
`magick identify` rather than `convert` and `identify`. `[official]`

## sharp strips metadata by default; preserving is the explicit act

sharp removes all metadata — EXIF, ICC, XMP, IPTC — on output, and converts to
sRGB when no ICC profile is kept. `[official]` Privacy stripping therefore
requires no call at all. The operation that needs writing down is the opposite
one.

```js
// default: everything removed, output is sRGB
await sharp(src).resize(1600).jpeg({ quality: 82 }).toFile(out);

// keep colour management and authorship
await sharp(src).autoOrient().resize(1600).keepMetadata().jpeg({ quality: 82 }).toFile(out);
```

- `keepMetadata()` keeps EXIF, ICC, XMP and IPTC.
- `withMetadata()` keeps EXIF, XMP and IPTC and lets specific fields be set.
- `autoOrient()` applies the EXIF orientation. Parameterless `rotate()` is a
  backwards-compatible alias for it; `autoOrient()` says what it means.
  `[official]`

The consequence that produces bug reports: a Display-P3 or Adobe RGB source
loses its ICC profile and its pixel values are then interpreted as sRGB, so
saturated colours shift visibly. Nothing errors. For wide-gamut input either
keep the profile or convert deliberately with `.toColorspace()` before writing,
and decide which — the default is a silent third option.

Two smaller sharp behaviours worth knowing: `fit: 'inside'` with
`withoutEnlargement: true` is the "fit within a box, never upscale" combination
(`inside` alone still enlarges small images), and SVG input is rasterised at
its declared size unless `density` is raised, so an SVG watermark composited at
its natural size comes out soft.

## Metadata loss is a provenance problem, not only a colour one

Stripping metadata also removes content credentials and provenance manifests
that a downstream consumer may be required to verify. An image that arrives
with a signed provenance record and leaves a resize step without one cannot be
re-attested; the chain is broken, not merely thinned.

So make it a decision with a stated answer, in both directions:

- Publishing to the open web, no provenance requirement: strip. Location data
  in EXIF is the usual reason.
- Anything that carries content credentials, or any archival or editorial
  pipeline: preserve explicitly, and verify after the operation that the record
  is still present rather than assuming the flag worked.

Orientation is the special case: it must be *applied* to the pixels rather than
merely carried, because consumers that ignore EXIF will otherwise show the
image sideways. Apply it, then let the surviving metadata describe an image
that is already upright.

## ImageMagick geometry has four modes and one trap

| Written as | Meaning |
|---|---|
| `800x600` | Fit inside the box, aspect preserved; result may be smaller in one dimension |
| `800x600^` | Fill the box — scale so the *smaller* dimension reaches the target; result overflows the other dimension |
| <code>800x600!</code> | Force exactly, ignoring aspect ratio; distorts |
| `50%` | Scale by percentage |
| `800x600>` / `800x600<` | Only shrink / only enlarge |

`^` does not crop. `[official]` A command that stops at `-resize 800x600^`
produces an oversized image, and calling that mode "fill with crop" is the
error to watch for. Cropping needs `-extent` with a gravity:

```bash
magick in.jpg -auto-orient -resize 800x600^ -gravity center -extent 800x600 -strip out.jpg
```

`-auto-orient` first, because rotation after cropping crops the wrong region.
`-strip` last, because it removes the orientation tag the earlier step consumed.

Rasterising vector input needs `-density` *before* the input, since it controls
how the input is read:

```bash
magick -density 300 in.pdf[0] -background white -alpha remove page1.png
```

`[0]` selects the first page; without it a multi-page PDF produces one output
file per page.

## `mogrify` rewrites in place

`mogrify` overwrites its inputs. A wrong parameter destroys the originals, and
a partially completed run leaves a directory in which some files have been
processed and some have not, with no way to tell which.

Write to a separate directory, always:

```bash
mkdir -p out && magick mogrify -path out -resize 1600x1600\> -quality 82 -format webp *.jpg
```

`-path out` redirects output; `-format webp` changes the extension alongside
the encoder. Run it against two files first and inspect the results before
pointing it at the batch.

The same rule applies to every tool here: never write an output over its own
input. Derive output names from input names in a different directory.

## Bulk thumbnails: shrink on load

`vips thumbnail` uses the shrink-on-load support in the JPEG, WebP and
associated-thumbnail paths, decoding at a reduced size rather than decoding the
full image and then resampling. `[official]` On large batches that is a
different order of magnitude of work, and it also keeps memory flat.

```bash
vipsthumbnail in/*.jpg --size 400x400 --smartcrop attention \
  -o "out/%s.webp[Q=80,strip]"
```

`--smartcrop attention` picks the crop window from image content rather than
the geometric centre, which matters for faces and off-centre subjects.
`[official]` The `%s` in the output pattern is the input basename; `strip`
removes metadata, so drop it when provenance must survive.

For anything above a few hundred files, process in parallel at the shell level
(`xargs -P`) rather than inside one process, and keep a per-file failure from
ending the run.

## Pillow

Two Pillow-specific behaviours account for most of its surprises:

```python
from PIL import Image, ImageOps

with Image.open(src) as im:
    im.draft("RGB", (800, 800))        # JPEG only: decode at a reduced scale
    im = ImageOps.exif_transpose(im)   # apply EXIF orientation to the pixels
    im.thumbnail((800, 800))
    im.save(dst, quality=82, progressive=True, subsampling="4:2:0",
            icc_profile=im.info.get("icc_profile"))
```

- Pillow does **not** apply EXIF orientation on open. Without
  `ImageOps.exif_transpose` every image from a phone held sideways is saved
  sideways. `[official]`
- `save()` does not carry metadata across by default either; `icc_profile` and
  `exif` must be passed explicitly.
- `draft()` is a JPEG-only fast path that asks the decoder for a smaller image.
  It changes the image in place and only ever reduces, so call it before any
  measurement that depends on size. `[official]`
- `thumbnail()` modifies in place and never enlarges; `resize()` returns a new
  image and will enlarge.

## Quality scales do not transfer between formats

A number that means one thing in JPEG means something else in WebP and
something else again in AVIF. AVIF around 50 is roughly comparable to JPEG 80,
and copying 80 into an AVIF encoder produces a file far larger than intended
for no visible benefit. `[community]`

Sensible starting points, to be checked against the actual images rather than
trusted: JPEG 80-85, WebP 80, AVIF 50. Encode a representative sample at two or
three settings and compare at full size before applying a value to a batch.

## Sprite sheets

For a grid assembled from separate image files, use `vips arrayjoin` (fast, low
memory) or `magick montage` when labels or per-tile framing are wanted:

```bash
vips arrayjoin "$(ls tiles/*.png | tr '\n' ' ')" sprite.png --across 10
magick montage tiles/*.png -tile 10x -geometry +0+0 -background none sprite.png
```

Every tile must already be the same size; `arrayjoin` pads to the largest tile
rather than scaling, which silently misaligns the CSS offsets that consume the
sheet. Normalise the tiles in a prior step and verify the final dimensions are
exactly `tile_w x columns` by `tile_h x rows`.

For a sprite sheet of video thumbnails, the frames come from ffmpeg's `tile`
filter in one pass, as shown earlier, rather than from extracting hundreds of
individual files and joining them.

<!-- sources: terminalskills-imagemagick, terminalskills-sharp, einverne-imagemagick, sharp-docs, imagemagick-docs, libvips-docs, pillow-docs -->
