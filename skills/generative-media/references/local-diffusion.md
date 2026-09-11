# Local diffusion and reproducibility

## Contents

- [What a seed buys you locally, and what it does not](#what-a-seed-buys-you-locally-and-what-it-does-not)
- [The generator's state is consumed](#the-generators-state-is-consumed)
- [`torch.manual_seed` is not what seeds the pipeline](#torchmanual_seed-is-not-what-seeds-the-pipeline)
- [CPU and GPU are different random number generators](#cpu-and-gpu-are-different-random-number-generators)
- [The full-determinism switch and its price](#the-full-determinism-switch-and-its-price)
- [Five conditions, and no guarantee even then](#five-conditions-and-no-guarantee-even-then)
- [Pin the things that silently change output](#pin-the-things-that-silently-change-output)
- [Schedulers and step counts](#schedulers-and-step-counts)
- [Memory: what fits, and what it costs](#memory-what-fits-and-what-it-costs)
- [Using someone else's LoRA](#using-someone-elses-lora)
- [Node-graph workflows](#node-graph-workflows)

## What a seed buys you locally, and what it does not

On a local open-weights stack the seed is a real control: it selects the
initial noise, and with everything else held fixed the same seed gives the
same image. On a hosted API the same parameter is a similarity hint — one
vendor states outright that the seed does not guarantee determinism, it only
slightly improves it.

Those are different contracts and they need different engineering. Locally you
can build a reproduction procedure. On a hosted endpoint you archive the
approved bytes and treat the call as unrepeatable.

Everything below is the local half.

## The generator's state is consumed

A torch generator carries random state that advances every time it is drawn
from [official]. Reusing one generator object across a loop therefore makes
image N depend on the N−1 draws that preceded it:

```python
# Wrong: one generator, state advances with every call.
generator = torch.Generator("cpu").manual_seed(0)
for prompt in prompts:
    pipe(prompt, generator=generator)
```

Nothing errors, and the batch is internally consistent — rerun the whole
script and you get the same set back. The failure appears the moment someone
reruns a single prompt on its own: it draws from a fresh state and produces a
different image from the one approved in the batch, with the same seed in the
log.

Create or reseed a generator per image, and record which seed went with which
output:

```python
# Right: a fresh generator per image, seed recorded alongside the artefact.
for prompt, seed in zip(prompts, seeds):
    pipe(prompt, generator=torch.Generator("cpu").manual_seed(seed))
```

This is the most common true answer to "I fixed the seed, why is it still
different".

## `torch.manual_seed` is not what seeds the pipeline

A global seed call at the top of a script seeds the default global generator.
A pipeline invoked with an explicit generator argument does not use it, so the
global call changes nothing about the image and supplies false confidence
[official].

It is not harmless: it makes unrelated randomness — data shuffling, dropout in
any auxiliary model, augmentation — look pinned too, so a script can appear
deterministic while the only thing actually pinned is the part you passed
explicitly. Seed explicitly at the call, or accept that nothing is seeded.

## CPU and GPU are different random number generators

The same seed produces different noise on a CPU generator and on a CUDA
generator; they are separate implementations, not one algorithm running in two
places [official]. Diffusion libraries therefore create the initial noise
tensor on the CPU and move it to the accelerator, precisely so a result can
survive a change of device.

If cross-machine reproduction matters, use a CPU generator and accept the
negligible cost of generating a latent there [official]. If you let the device
generate its own noise, the approved image from a laptop cannot be reproduced
on a server, and no amount of seed discipline will recover it.

Two further limits worth stating to whoever is asking for parity:

- Different accelerator backends — CUDA, Metal, ROCm, CPU — run different
  kernels. Matching noise is necessary for parity but not sufficient; the
  denoising arithmetic still differs.
- Bit-identical parity between two different GPUs, or between a laptop
  accelerator and a datacentre card, is not something to promise. The
  deliverable is the approved image bytes, archived; the pipeline is how they
  were made, not a way to make them again.

## The full-determinism switch and its price

The library's full-determinism helper does three specific things [official]:

1. Sets the cuBLAS workspace configuration environment variable to a fixed
   value, which makes certain GEMM routines deterministic.
2. Disables the cuDNN benchmark autotuner, so convolution algorithm selection
   stops depending on measured timings — the autotuner is why a warm process
   can pick a different algorithm from a cold one.
3. Disables TF32 on matmul and cuDNN paths, so reduced-precision fast paths
   stop introducing run-to-run variation.

Each of the three costs throughput, which is why this is a test and
verification switch rather than a production default. It must also be set
before the pipeline runs; flipping it after models are loaded does not undo
choices already made.

## Five conditions, and no guarantee even then

Local reproduction is reliable only when all five hold simultaneously
[official]:

1. Same weights, down to the exact revision of the checkpoint.
2. Same library and framework versions.
3. Same device and backend.
4. Same pipeline configuration — scheduler, step count, guidance, resolution,
   precision, and any memory optimisation that changes the computation.
5. A freshly seeded generator per image, on the CPU.

Change any one and the contract is void. And even with all five, the upstream
position is explicit: you can limit randomness, but identical output is not
guaranteed even with an identical seed, and reproducibility across releases
and platforms holds only within a tolerance range [official].

So the artefact of record is the image file plus its generation record —
prompt, seed, every parameter, weights revision, library versions, device, and
the hash of the bytes. Approval attaches to bytes, never to a recipe.

## Pin the things that silently change output

| Pin | Why it moves the image |
|---|---|
| Library version | Scheduler implementations, default timestep spacing and numerical details change between releases |
| Weights revision | Repository revisions are mutable by default; a re-uploaded checkpoint under the same name is a different model |
| Weight precision and variant | fp16 and fp32 variants of the same checkpoint do not produce the same pixels |
| Scheduler class and its config | Two schedulers at the same step count follow different trajectories |
| Memory optimisations | Attention slicing, sequential offload and similar features alter the order and precision of the arithmetic |

A lockfile pinning the library is half the job; the weights revision belongs in
the same lock, quoted explicitly at load time rather than resolved to whatever
the remote branch currently points at.

## Schedulers and step counts

Schedulers trade steps against quality, and the trade is not linear: some
converge to an acceptable image in a small number of steps, others need
several times as many for the same subjective result. Step count is not a
quality dial you can raise indefinitely — past a scheduler's useful range the
image stops improving and starts costing.

Two practical rules. Choose a scheduler once per project and record it in the
generation record, because swapping it invalidates every previously approved
seed. And when comparing schedulers, compare at matched wall-clock or matched
cost, not at matched step count, since a step means a different amount of work
in each.

## Memory: what fits, and what it costs

Peak memory is driven by weight precision, resolution and batch size, in that
order, and the resolution term grows with the number of latent pixels rather
than linearly with the long edge. The usual escape hatches — half precision,
attention slicing, model or sequential CPU offload, tiled decoding — each buy
memory with throughput, and several of them change the arithmetic, which puts
them in the pinning table above.

Order of preference when a pipeline will not fit: lower precision first (it is
the cheapest in quality terms and the most predictable), then offloading,
then tiling, and only then resolution. Reducing resolution changes the image
itself, so it is a creative change wearing an engineering costume.

## Using someone else's LoRA

Adapters published for a base model carry two things worth reading before use:
a trigger phrase that must appear in the prompt, without which the adapter
contributes little, and a recommended weight [community]. When combining
several adapters, keep the total influence near unity — weights around
0.9–1.1 in aggregate — because stacking them at full strength produces
saturated, incoherent output [community].

Adapter identity and weight belong in the generation record alongside the
seed; an image reproduced with the right seed and the wrong adapter weight is
a different image.

## Node-graph workflows

Node-graph runtimes package the same pipeline concepts as a visual graph:
sampler and scheduler selection, guidance scale, latent creation and
resizing, adapter loading, masking and inpainting, and nodes that call hosted
generation APIs from inside a local graph. Everything in this reference
applies unchanged to them, because underneath they run the same libraries.

The one workflow-specific trap: a saved graph pins the topology and the
parameters, not the environment. Node package versions, custom node updates,
model file contents behind a filename, and the runtime's own version all sit
outside the saved file. A graph that produced an approved image last month can
produce a different one today with every visible field identical. Archive the
output bytes and the environment versions next to the graph, or the graph is
documentation rather than a reproduction.

<!-- sources: diffusers-docs, google-gemini-docs, replicate-skills, comfyui -->
