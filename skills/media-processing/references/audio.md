# Audio

Verified against: ffmpeg N-126134-gc48230eb86-20260814

## Contents

- [Loudness normalisation takes two passes](#loudness-normalisation-takes-two-passes)
- [`loudnorm` silently changes the sample rate](#loudnorm-silently-changes-the-sample-rate)
- [Loudness targets are per destination](#loudness-targets-are-per-destination)
- [Mixing: sample rates first, then levels](#mixing-sample-rates-first-then-levels)
- [`-shortest` and `duration=shortest` are different switches](#-shortest-and-durationshortest-are-different-switches)
- [Wrapping raw PCM](#wrapping-raw-pcm)
- [Codec and bitrate selection](#codec-and-bitrate-selection)
- [Channel layout and downmixing](#channel-layout-and-downmixing)
- [Processing order in an audio chain](#processing-order-in-an-audio-chain)

## Loudness normalisation takes two passes

`loudnorm` implements EBU R 128: integrated loudness in LUFS, loudness range
(LRA) in LU, and true peak in dBTP. `[official]`

Single-pass `loudnorm` is not normalisation. Its `linear` option defaults to
true but is documented as "normalize linearly *if possible*", and linear
operation is only possible when all four `measured_*` values are supplied.
`[verified]` Without them the filter runs its dynamic path, which applies
gain that varies over time and rewrites LRA — so the output does not have the
dynamics of the input, and the LRA it reports is not the LRA it produced.

Measure, then apply:

```bash
# pass 1 - measure, discard output
ffmpeg -i in.wav -af loudnorm=I=-16:LRA=11:TP=-1.5:print_format=json -f null - 2>&1 | tail -20

# pass 2 - feed the measured values back, and pin the sample rate
ffmpeg -i in.wav -af "loudnorm=I=-16:LRA=11:TP=-1.5:\
measured_I=-21.34:measured_LRA=8.70:measured_TP=-3.10:measured_thresh=-31.86:\
offset=0.42:linear=true,aresample=48000" -ar 48000 -c:a aac -b:a 192k out.m4a
```

Copy all five printed values, including `offset`. Dropping one puts the filter
back on the dynamic path with no warning.

Single-pass is acceptable only for a rough preview that nobody delivers.

## `loudnorm` silently changes the sample rate

`loudnorm` runs internally at 192 kHz and does not resample back. Nothing in
the log mentions it.

Measured on a 44,100 Hz source: `-af loudnorm=I=-16 -vn out.wav` produced
`pcm_s16le, 192000 Hz`; `-af loudnorm=I=-16:TP=-1.5 -c:v copy out.mp4`
produced `aac, 96000 Hz`, the AAC encoder's ceiling. Neither emitted a warning.
`[verified]`

The consequences are quiet and downstream: a 192 kHz WAV is four times the
expected size, a 96 kHz AAC track breaks HLS variant alignment, and a mux
against 48 kHz material drifts.

End every `loudnorm` chain with `aresample=<rate>` and set `-ar <rate>` on the
output as well. Both, because the filter fixes the graph and the output option
fixes the encoder.

## Loudness targets are per destination

`loudnorm`'s own defaults are `I=-24`, `LRA=7`, `TP=-2`. `[verified]` Those
are broadcast values, not streaming values, and leaving them implicit delivers
material about ten LU quieter than a streaming platform expects.

Always state all three explicitly. Starting points:

| Destination | I (LUFS) | TP (dBTP) | LRA (LU) |
|---|---|---|---|
| Web video and music streaming | -14 | -1.0 | 11 |
| Podcasts and spoken word | -16 | -1.0 | 7-9 |
| Short-form mobile video | -14 | -1.0 | 7 |
| Broadcast (EBU R 128) | -23 | -1.0 | 15 |

`[community]` — these are delivery conventions, not standard text. Confirm
against the destination's own published specification when one exists.

True peak below 0 dBFS matters because lossy encoders overshoot on decode;
-1.0 dBTP leaves headroom for that. A file that measures 0.0 dBTP before
encoding will clip after it. `[official]`

## Mixing: sample rates first, then levels

Mixing streams at different sample rates without resampling changes pitch and
speed of the mismatched input, and the result sounds broken rather than
erroring. `[official]` Resample every input to a common rate as the first step
of the mix graph.

```bash
ffmpeg -i voice.wav -i music.mp3 -filter_complex \
"[0:a]aresample=48000,volume=0dB[v];\
 [1:a]aresample=48000,volume=-14dB,afade=t=out:st=115:d=5[m];\
 [v][m]amix=inputs=2:duration=first:normalize=0[a]" \
 -map "[a]" -c:a aac -b:a 192k out.m4a
```

Two things in that graph are easy to get wrong:

- **`normalize`.** `amix` defaults to `normalize=1`, which divides every input
  by the input count: two sources each arrive 6 dB down, four arrive 12 dB
  down, and the mix sounds thin for no visible reason. `[official]` Set
  `normalize=0` and control levels with an explicit `volume` per input.
- **Relative levels.** Music under speech sits roughly 12-18 dB below the
  voice. Set that with `volume` before the mix, not by normalising afterwards,
  which cannot separate the two again. `[community]`

Finish music beds with `afade=t=out` rather than letting them stop dead at the
end of the programme; `st` is the start time of the fade in seconds, so it is
computed from the measured duration of the other stream, not guessed.

## `-shortest` and `duration=shortest` are different switches

`-shortest` is an output option: muxing stops when the shortest *input stream*
ends, which can truncate video that was meant to be complete.

`amix=duration=shortest` is a filter option: the *mix* ends when its shortest
input ends, leaving other output streams untouched.

Use `duration=first` when the first input defines the programme length (voice
over a music bed), `duration=longest` with `apad` when a short audio track must
cover a long video, and `-shortest` only when truncating the whole output is
genuinely intended.

## Wrapping raw PCM

Headerless PCM has no way to declare its own format, so every parameter must be
supplied on the input side. Guessing produces noise or half-speed playback
rather than an error.

```bash
# 24 kHz, 16-bit little-endian, mono -> WAV
ffmpeg -f s16le -ar 24000 -ac 1 -i raw.pcm out.wav

# same, resampled to 48 kHz for muxing with video
ffmpeg -f s16le -ar 24000 -ac 1 -i raw.pcm -af "aresample=48000:resampler=soxr" -ar 48000 out.wav
```

`-f`, `-ar` and `-ac` must appear before `-i`; after it they describe the
output and the input is then misinterpreted. `s16le` matches 16-bit signed
little-endian, the common case; `f32le` for 32-bit float.

This is the receiving end of the handoff from speech synthesis: the generation
side chooses the voice and the model and returns bytes plus a declared format,
and wrapping and resampling those bytes is deterministic work — identical
input yields identical output, which is what makes it belong here. Take the
sample rate, bit depth and channel count from the producer's declared contract
rather than inferring them, and resample to the project rate in the same
command so no 24 kHz file escapes into a 48 kHz timeline.

The reverse handoff has the same shape: speech recognition generally expects
16 kHz mono PCM, and producing that is one deterministic transcode
(`-ar 16000 -ac 1 -c:a pcm_s16le`) performed before the recogniser is called.

## Codec and bitrate selection

| Use | Codec | Bitrate |
|---|---|---|
| Video soundtrack, general delivery | `aac` | 128k mono, 192k stereo, 384k 5.1 |
| WebM, Opus-capable pipelines | `libopus` | 96k stereo is transparent for speech and music |
| Lossless delivery | `flac` | - |
| Intermediate between processing steps | `pcm_s16le` or `pcm_s24le` | - |

Use AAC as the default for MP4 delivery. Below 128 kbit/s stereo AAC becomes
audibly lossy; treat that as a floor and report it rather than crossing it to
hit a size target.

Never re-encode audio that does not need to change. When only the video is
being touched, `-c:a copy` avoids a generation of loss. Extracting a track is
the same idea: `-vn -c:a copy` when the target container accepts the codec, and
only then a transcode.

Changing a file extension does not change the codec. Renaming `.wav` to `.mp3`
produces a file that fails in exactly the players that matter.

## Channel layout and downmixing

`-ac 2` applies a default downmix matrix, which is fine for stereo from mono
and usually acceptable from 5.1. When dialogue intelligibility matters, set the
matrix explicitly with `pan` rather than accepting the default centre level:

```bash
-af "pan=stereo|FL=0.5*FC+0.707*FL+0.707*BL|FR=0.5*FC+0.707*FR+0.707*BR"
```

Check the source layout before assuming: a "stereo" file with identical
channels is dual mono, and `-ac 1` on it is free, while `-ac 1` on true stereo
discards content.

## Processing order in an audio chain

```
highpass (remove rumble)
  -> denoise (afftdn)
  -> time changes (atempo)
  -> dynamics (dynaudnorm / acompressor)
  -> loudness (two-pass loudnorm)
  -> aresample to the delivery rate
```

Loudness last, because every earlier stage changes the measurement. Denoise
before dynamics, because a compressor otherwise pulls the noise floor up
between phrases. Time changes before dynamics, because `atempo` alters the
envelope the compressor reacts to.

<!-- sources: media-os-ffmpeg, vertex-genmedia-av, n0an-ffmpeg, terminalskills-ffmpeg, maxazure-video, ffmpeg-filters-docs, ebu-r128 -->
