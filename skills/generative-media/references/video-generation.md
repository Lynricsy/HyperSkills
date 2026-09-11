# Video generation

## Contents

- [Duration and frame rate are fixed, not requested](#duration-and-frame-rate-are-fixed-not-requested)
- [Anything longer is a shot list](#anything-longer-is-a-shot-list)
- [Holding consistency across shots](#holding-consistency-across-shots)
- [Writing a shot prompt](#writing-a-shot-prompt)
- [Seeds barely move a video model](#seeds-barely-move-a-video-model)
- [Subtitle contamination](#subtitle-contamination)
- [Video is an asynchronous job, always](#video-is-an-asynchronous-job-always)
- [Server-side retention is not storage](#server-side-retention-is-not-storage)
- [Safety rejection is a first-class outcome](#safety-rejection-is-a-first-class-outcome)
- [Region and person-generation restrictions](#region-and-person-generation-restrictions)

## Duration and frame rate are fixed, not requested

Hosted video models emit short clips at a frame rate they choose. One current
flagship accepts only 4, 6 or 8 seconds, runs at a fixed 24 fps, forces the
duration to 8 seconds whenever 1080p, 4K, reference images or clip extension
are in play, and returns exactly one video per request [official].

The design consequences arrive before the first call:

- Duration is an enum, not a number. Code that computes a length and passes it
  will fail validation on some values and silently round on others.
- Frame rate is not yours to pick at generation time. Conforming a clip to a
  project's frame rate is a deterministic retime, done afterwards.
- One video per request means N variants cost N jobs, and each has its own
  latency and its own failure mode.
- Enabling a quality tier can change the accepted duration set. Read the
  current model version's input schema before assuming last month's
  combination still validates.

## Anything longer is a shot list

For anything past the single-clip ceiling, write a storyboard first and
generate 5–8 second shots against it [official]. Not "generate a 30 second
advert" — five shots, each with its own prompt, each independently
regenerable.

Joining them is a deterministic operation and does not belong here: same input,
same bytes belongs to the deterministic toolchain; output that varies with
model, seed or server-side version belongs here. Hand off the clips with the
constraints the join needs made explicit, because the join will fail or
silently re-encode otherwise:

- Every clip at the same frame rate, resolution and pixel format.
- Every clip's audio at the same sample rate and channel count, or with audio
  absent everywhere rather than on some clips only.
- Clip boundaries placed on cuts you intend, not wherever the model stopped —
  write the last beat of each shot so it can be cut cleanly.

Concatenation, transitions, colour matching, loudness alignment and muxing are
all deterministic work. Do not attempt them by re-prompting.

## Holding consistency across shots

Nothing carries between two generation requests. Every shot prompt restates
the whole world [official]:

- A fixed character block, byte-identical across shots: age, build, hair,
  clothing down to colour and material, distinguishing features.
- A fixed environment block: location, time of day, weather, light direction
  and quality.
- A fixed style block: film stock or rendering style, colour grade, lens.
- Only then the per-shot content: subject action, camera move, framing.

Where the model accepts reference images, feeding the same reference into every
shot holds identity far better than prose does. Where it does not, expect drift
and plan the edit to cut around it — a shot change is a natural place for a
face to change slightly; a continuous pan is not.

Shot progression that reads as intentional: wide establishing, then medium,
then close, across roughly 8–15 seconds of screen time [community]. Sequences
that hold one framing for the whole duration read as a single generated clip,
which is what they are.

## Writing a shot prompt

Seven elements, each one sentence or less [community]:

| Element | Example content |
|---|---|
| Subject | who or what, with the fixed character block |
| Environment | where, when, weather, light |
| Action | one action, with a clear beginning and end inside the clip length |
| Style | film stock, animation style, grade |
| Camera | lens and movement: static, slow push in, handheld follow |
| Composition | framing and subject placement |
| Mood | the atmosphere the grade and pacing should carry |

Visual facts outperform flattering adjectives: "overcast daylight, wet asphalt,
35 mm handheld" produces a specific image; "stunning cinematic masterpiece"
produces the model's average [community]. Change one element per iteration —
with a model this large, changing three and liking the result teaches you
nothing about which change did it.

## Seeds barely move a video model

Contrary to the intuition built on image models, several video models return
highly similar output across different seeds [community]. Re-rolling the seed
is not a variation strategy; it is a way to spend money on the same clip
twice. To get a different take, change the prompt.

Even where a seed parameter exists, hosted video generation does not promise
determinism from it. The vendor statement to internalise is that the seed does
not guarantee determinism, it only slightly improves it [official]. Plan
reproducibility around archiving the approved bytes, never around replaying
the call.

## Subtitle contamination

Video training corpora contain large quantities of burnt-in subtitles, so
prompts that look like dialogue produce clips with text burnt across the
bottom of the frame [community]. Two mitigations, used together:

- Write dialogue with a colon, not quotation marks: `Woman: we should go.`
  Quoted strings read as on-screen text.
- Say `(no subtitles)` explicitly, and repeat it if a clip comes back with
  text anyway.

Text that does appear is baked into pixels. Removing it is an inpainting or
cropping job, not a re-prompt, and both degrade the frame.

## Video is an asynchronous job, always

Design video, music and long-form audio generation as asynchronous jobs from
the first line of code — submit, persist the request id, poll or receive a
webhook [official]. This is not a scalability preference; it is what the
latency distribution forces. One vendor documents a range from 11 seconds to
6 minutes at peak for a single clip [official].

Synchronous blocking is available only where a provider offers it, is capped
in the tens of seconds, and is explicitly recommended only for very fast
models [official]. Restrict it to calls whose p99 you have actually measured
below 60 seconds — in practice, images and short speech — and give every
synchronous path a fallback that converts to polling on timeout rather than
failing the user's request.

A generation call that times out on the client is not a call that did not
happen. The job is still running and will still be billed.

## Server-side retention is not storage

Providers delete generated media on their own schedule and the schedules do not
agree: output URLs that expire one hour after the job finishes, and generated
videos held server-side for two days before deletion, are both current vendor
behaviour [official]. Extended clips count as newly generated, with their own
fresh retention clock.

So downloading the bytes and writing them to your own storage is a mandatory
step of the generation flow, not an optimisation. Do it in the same run that
created them, before reporting success, and record the artefact hash against
the request id. The failure this prevents is mundane and unrecoverable: three
days later the client asks for the original and the link is a 404.

## Safety rejection is a first-class outcome

A safety filter block is a normal branch of the job state machine, not an
exception to log and retry. Handle it explicitly:

- Rewrite clinically. Strip emotionally coloured, ambiguous or suggestive
  wording and keep the physical description of what should be on screen
  [official]. "A terrified child fleeing" becomes "a child running along a
  corridor, looking back over one shoulder".
- Do not retry the identical prompt, and do not shop for a model with a looser
  filter. Both are ways of spending money to arrive at the same block, and the
  second is circumvention.
- Expect billing asymmetry: at least one vendor does not charge when audio is
  blocked by safety filters and no video is produced [official]. Others do
  charge for a rejected job. Read the current policy rather than assuming
  either way, because a retry loop over a billed rejection is expensive.
- Surface the block to the caller with the rewritten prompt attached, so a
  human can see what was changed on their behalf.

## Region and person-generation restrictions

Controls on generating people are region-dependent, and the same code can
succeed in one deployment region and fail in another. One vendor permits only
the adults-allowed setting in the EU, UK, Switzerland and the MENA region
[official], meaning a default that works in development fails in production
after a region change nobody associated with generation.

Treat the person-generation setting as deployment configuration, not a
constant: resolve it per region, validate it at startup, and fail loudly at
configuration time rather than on the first user-facing request.

<!-- sources: google-gemini-docs, google-genmedia-skills, replicate-skills, google-skills-gemini-api -->
