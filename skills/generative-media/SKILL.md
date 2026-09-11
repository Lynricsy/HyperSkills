---
name: generative-media
description: "Engineers code that calls a media model: image generation and mask-guided editing where the mask is a hint and never a crop, video generation constrained to fixed short clips behind an asynchronous job, text to speech returning raw PCM rather than a playable file, speech to text whose fixed decode window drives timestamp drift and silence hallucination, local diffusion whose reproducibility rests on generator state, device RNG and pinned versions rather than a seed, job lifecycle with polling, webhooks, retries that cost money, quotas and billing, and provenance duties (SynthID, C2PA, disclosure) that a later resize destroys. Use when adding or fixing generated or transcribed images, video, speech or music, when a render cannot be reproduced across machines, when a generation times out in a handler, or when compliance asks how a viewer can tell an asset is AI-made. Do not use for text-model applications, retrieval or agent loops, for training weights, or for deterministic transcoding, muxing and resizing."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: task
---

# generative-media

Paths below are relative to this skill's directory.

## Scope

Calling a model that emits or reads pixels, video frames or audio samples:
image generation and editing, video generation, speech synthesis, speech
recognition, music, and local diffusion pipelines. Everything around that
call — how the request is shaped, how the job is run, what the output costs,
what must be stored, and what must be disclosed.

The same input must produce the same bytes. That is the line: work whose
output varies with a model, a seed or a server-side version belongs here;
work that is a pure function of its input belongs to the `media-processing`
skill.

Not covered — do not answer from this skill:

- Muxing, containerising, resampling, concatenating, cutting and resizing
  what a model returned, and the ffmpeg or image-tool commands to do it: the
  `media-processing` skill. The constraints those steps must satisfy —
  sample rate, clip duration, metadata that must survive — are stated here.
- Models that emit text or structured data, retrieval, evals and agent
  loops: the `ai-engineering` skill.
- Changing weights: fine-tuning, LoRA training, distillation, quantisation:
  the `ml-training` skill. Loading someone else's weights to generate
  belongs here.
- Vector search over embeddings of media: the skill for the store in use.
- Art direction. This skill makes a generation pipeline correct, affordable
  and accountable; it does not decide whether the image is good.

## Read first

`references/provenance-and-policy.md` before shipping any generated asset to
users. Provenance and disclosure are obligations attached to the asset, and
the failure mode is discovering them after publication.

## Core rules

Each rule is an invariant. The clause after the dash is what breaks when it
is violated.

1. Resolve the model from the provider at run time — a model id written into
   code is a fact with a half-life of months, and the call keeps working
   against a superseded generation long after a better or cheaper one
   exists.
2. Read the model's own schema before constructing a request — capability
   varies per model within one provider, and an unsupported parameter is
   commonly accepted and ignored rather than rejected.
3. Treat an edit mask as a prompt-level hint, never as a crop — the model may
   change pixels inside the region you meant to protect, so "only the
   background changes" is not something the endpoint can promise. `[official]`
4. Recover pixel-exact regions by compositing deterministically after
   generation — refining the prompt or the mask edge does not convert a
   probabilistic edit into an exact one.
5. Restate the invariants on every edit turn — each turn is a fresh
   generation, and a constraint honoured in turn two is not inherited by
   turn three.
6. Do not promise byte-level reproducibility from a hosted endpoint — where a
   seed exists at all it improves similarity, and providers say so
   explicitly. `[official]`
7. Make the archived output the artefact of record — the bytes you stored,
   addressed by their hash, are the only thing that reproduces exactly.
8. Create or reseed the generator per image in a local pipeline — a generator
   reused across a loop advances its state, so image N depends on every call
   before it and cannot be re-rendered alone. `[official]`
9. Generate latents on CPU when a result must cross devices — the CPU and
   CUDA RNGs produce different noise from the same seed. `[official]`
10. Pin the weights revision, the library version and the scheduler
    alongside the seed — any of them moving changes the output while the
    seed stays reassuringly identical.
11. Reach for the full-determinism switch only when determinism is worth its
    throughput cost, and state that even then the library does not promise
    bit-identical results. `[official]`
12. Design video, music and long audio as asynchronous jobs — these run for
    minutes, and a request handler that awaits them is a timeout with extra
    steps. `[official]`
13. Persist the provider's request or operation id before the first poll —
    without it a crash orphans a job you have already paid for.
14. Never retry a generation call blindly — a retry is a second charge and a
    different result, so reconcile against the original job's state first.
15. Download the output into your own storage as part of the job, not as a
    later optimisation — provider URLs expire on schedules that differ per
    provider and none of them is a storage layer. `[official]`
16. Treat a safety or content-policy refusal as a first-class outcome with
    its own path — it is not a network error, it usually is not billed, and
    it needs a clinical rewrite rather than a synonym shuffle.
17. Ask the model for clips of the length it actually produces and assemble
    longer pieces yourself — prompting for a duration the model cannot emit
    yields a short clip, not an error. `[official]`
18. Split long speech input on sentence or paragraph boundaries, under the
    endpoint's input limit — a cut at a fixed character count lands
    mid-clause and the prosody audibly breaks.
19. Hold voice and style configuration identical across the chunks of one
    narration, and join them with controlled silence — drift between chunks
    is what makes stitched narration sound synthetic.
20. Treat a speech response as raw samples until proven otherwise — renaming
    raw PCM to `.wav` does not give it a header, and the player simply
    refuses the file. `[official]`
21. Chunk long transcription on silence and add each chunk's offset back —
    the model decodes in a fixed window, so timestamp error accumulates
    across an uninterrupted long file. `[official]`
22. Gate non-speech audio out before transcription rather than filtering the
    text after — the model invents plausible sentences over music and
    silence, and a fabricated sentence is indistinguishable from a real one
    downstream. `[official]`
23. Keep provider provenance — SynthID signals, C2PA manifests — intact
    through every downstream step, and never strip or forge it; a routine
    resize destroys it by default. `[official]`
24. Disclose synthetic media where a person can actually see or hear it, not
    only in metadata — the obligation is that the audience can tell.
25. Persist the generation record — prompt, parameters, resolved model
    version, request id and the hash of the delivered bytes — so a published
    asset can be traced to the call that produced it.

## Workflows

### Add a generation path

- [ ] State what the output is for, which decides resolution, duration and
      therefore cost before any code exists.
- [ ] Resolve the model and read its schema; record the resolved version
      string.
- [ ] Decide synchronous, polling or webhook from the modality, not from
      convenience, and persist the job id at submission.
- [ ] Write the download-and-store step in the same change as the call.
- [ ] Record the generation record and, for user-facing assets, the
      disclosure surface.
- [ ] **Gate:** run one real generation end to end and show the stored
      artefact, its hash, and the record that points at it. A mocked call
      proves nothing about quotas, latency or refusals.

### Make renders reproducible

- [ ] Establish what "reproducible" has to mean here: identical bytes, or an
      approved artefact that can be retrieved.
- [ ] For a hosted endpoint, say plainly that only retrieval is achievable,
      and build the archive.
- [ ] For a local pipeline, fix generator construction, device placement of
      the noise, and the pinned versions; measure before claiming.
- [ ] **Gate:** render the same item twice in separate processes and compare
      hashes; then render it on the second machine and report whether the
      hashes match. Report the measured answer, including when it is "no".

### Integrate speech in or out

- [ ] Establish the endpoint's input limits and the exact format of its
      output, including whether that output is a container or raw samples.
- [ ] Place the boundary: transcoding, containerising and joining are
      deterministic work handed to the media tooling with explicit
      parameters (sample rate, channels, bit depth).
- [ ] Chunk on linguistic or silence boundaries and keep offsets.
- [ ] Add the disclosure for synthesised voice.
- [ ] **Gate:** play back or probe one produced file end to end and confirm
      duration, sample rate and that it opens in the target player. For
      transcription, check a timestamp near the end of a long file against
      the audio.

### Review a generation job

- [ ] Identify the modality and check the lifecycle first: synchronous or
      not, job id persisted, retries, refusal path.
- [ ] Check the cost model: what is billed, per what unit, and what bounds
      a runaway batch.
- [ ] Check what happens to the output: stored where, addressed how, with
      what record.
- [ ] Check provenance and disclosure end to end, including every
      downstream transform of the asset.
- [ ] **Gate:** name, for each finding, the user-visible failure it causes.
      A finding with no consequence is noise.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Generate versus edit, masks, reference images, prompt structure, size and cost | Producing or editing images | `references/image-generation.md` |
| Clip length, storyboarding, async submission, retention, safety filters | Producing video or music | `references/video-generation.md` |
| TTS chunking, voice consistency, raw PCM output; ASR limits, drift, hallucination, diarization | Producing or reading speech | `references/speech.md` |
| Generator state, device RNG, determinism switches, version pinning, VRAM | Running diffusion locally or chasing a non-reproducible render | `references/local-diffusion.md` |
| Sync/poll/webhook, job state, idempotent retries, quotas, billing units, storage | Wiring a generation call into a service, or a batch overspends | `references/job-lifecycle.md` |
| SynthID, C2PA, disclosure obligations, records, policy refusals | Before publishing any generated asset | `references/provenance-and-policy.md` |

## Output format

For a review, group findings by file and cite `path:line - finding`. Each
finding names the user-visible consequence, and separates what is broken
from what is a cost or policy decision the owner must make.

For an implemented change, report:

```
Generated: <what was produced, and where it is stored>
Record:    <model version, parameters, request id, output hash>
Cost:      <billing unit and what bounds it>
Exposure:  <provenance carried, and where the disclosure is visible>
Notes:     <what is not reproducible, and anything left to the owner>
```

## Environment

Provider SDKs as the repository already has them. Local pipelines need a
GPU-capable torch build plus diffusers; state the VRAM requirement before
suggesting a model. Verifying C2PA manifests needs the c2pa tooling. Any
containerisation, resampling or concatenation of generated media is done
with `ffmpeg`.
