# Image generation and editing

## Contents

- [Pick a capability, then look up a model](#pick-a-capability-then-look-up-a-model)
- [Generate or edit: decide by what must survive](#generate-or-edit-decide-by-what-must-survive)
- [A mask is a prompt, not a crop](#a-mask-is-a-prompt-not-a-crop)
- [Automatic prompt rewriting changes what a mask means](#automatic-prompt-rewriting-changes-what-a-mask-means)
- [Editing is iterative and invariants decay](#editing-is-iterative-and-invariants-decay)
- [Reference images and multi-image composition](#reference-images-and-multi-image-composition)
- [`background` is not the backdrop](#background-is-not-the-backdrop)
- [What the prompt may invent, and what it may not](#what-the-prompt-may-invent-and-what-it-may-not)
- [Aspect ratio drives resolution drives cost](#aspect-ratio-drives-resolution-drives-cost)
- [Prompt failures that get misread as model quality](#prompt-failures-that-get-misread-as-model-quality)
- [Writing the artefact](#writing-the-artefact)

## Pick a capability, then look up a model

Model identifiers in this domain turn over within a release cycle, and three
upstream skills surveyed at the same moment named three mutually contradictory
sets while the vendors' own docs named a fourth. Treat every model id you
remember — from a previous conversation, from a README, from training data — as
already wrong.

The sequence that survives:

1. Enumerate the provider's current models from its models endpoint or model
   index page, at the time you write the call.
2. Read that model version's own input schema. Hosted catalogues publish one
   per version; it is the only authority on which parameters exist.
3. Then write the call, against that schema.

Choose by capability, not by name [official]:

| Capability needed | What to look for in the schema | What happens if you assume it |
|---|---|---|
| Text to image | Prompt only | — |
| Image to image | An image input plus a strength or fidelity control | An image passed to a text-only endpoint is ignored; you get a plausible unrelated picture, not an error |
| Masked edit | A separate mask input alongside the image | The mask is dropped and the whole frame is regenerated |
| Style or subject reference | Multiple image inputs with per-image roles | References get treated as edit sources; the output tries to preserve them instead of borrowing from them |
| Multi-image composition | A declared maximum input count | Inputs past the cap are silently dropped by some providers, rejected by others |
| Transparent output | An explicit alpha or background control | You get an opaque approximation of transparency — a checkerboard, or flat white |

## Generate or edit: decide by what must survive

A user attaching an image does not mean the task is an edit. Decide on one
question: must some region of the supplied image survive as itself?

- Any pixel region has to remain recognisably the original — a face, a product,
  a logo, a screenshot's text — use the edit path with the original as input
  [official].
- The supplied image only supplies style, palette, layout or subject identity,
  and a fresh composition is acceptable — use generation with the image as a
  reference [official].

Getting this backwards fails silently in the expensive direction: generation
with a reference returns a competent new image, the user reads it as a botched
edit, and the next iteration tries to fix a prompt that was never the problem.

## A mask is a prompt, not a crop

Masking is prompt-guided; exact shapes are not guaranteed [official]. The mask
biases where the model concentrates change. It does not constrain it. Pixels
inside the region you meant to protect can move, edges do not necessarily land
on the mask boundary, and fine structure near the seam is regenerated rather
than preserved.

Consequences to design around:

- Never promise that "only the background changed". The edit endpoint cannot
  make that promise, so neither can you.
- When the requirement is pixel-exact — the delivered product must be the
  photographed product, the logo must be the logo — do not tighten the prompt
  and do not refine the mask. Generate the new region, then composite the
  original over it through an alpha matte in the deterministic toolchain. Same
  input, same bytes belongs there; output that varies with model, seed or
  server-side version belongs here.
- Feathering, alpha channels, edge refinement and colour matching are
  compositing operations with exact results. Asking a generative edit to
  perform them converts a solvable problem into a probabilistic one.

## Automatic prompt rewriting changes what a mask means

Several hosted image models rewrite the submitted prompt before conditioning on
it. That switch changes the semantics of an identical mask and an identical
sentence [community]:

- Rewriting on: describe only what belongs inside the masked region. The
  rewriter supplies the surrounding scene from the input image.
- Rewriting off: the prompt must describe the whole scene, including the parts
  you are not changing, or the unmasked context gets re-invented from nothing.

Check the schema for the rewrite toggle before writing the prompt, and record
which state produced an approved image. A prompt copied between two projects
with different toggle settings is not the same prompt.

## Editing is iterative and invariants decay

Each edit request is independent conditioning. Nothing carries over implicitly
from the previous round, so every invariant has to be restated every round
[official]:

```
Round 1: ... change the sky to overcast.
Round 2: same person, same navy jacket, same three-quarter angle,
         same overcast sky — change only the shoes to brown leather.
```

Dropping the restatement is how a five-round edit ends with a different person
wearing the right shoes.

Verb choice decides whether identity survives [community]. Wholesale verbs —
`transform`, `restyle`, `reimagine`, `turn into` — license the model to replace
the subject. Small changes need the explicit two-part form: change X, keep Y
unchanged.

## Reference images and multi-image composition

Hosted image editing endpoints currently accept up to 16 input images
[official]. The cap is not the limit that matters in practice:

- Each additional reference adds conditioning that can conflict with the
  others. Beyond a handful, consistency degrades — the model averages the
  references rather than honouring each.
- A high input-fidelity setting substantially increases input token count, so
  the same call gets materially more expensive when you ask it to respect the
  inputs harder [official].
- References carrying the same subject from several angles work better than
  references carrying several subjects. If you need several subjects composed
  exactly, place them deterministically and generate only the parts that may
  vary.

## `background` is not the backdrop

A `background` parameter controlling output transparency (transparent, opaque,
auto) is a different thing from the words "background", "scene" or "backdrop"
in the prompt [official]. The parameter decides whether the emitted file has an
alpha channel; the prompt decides what is depicted behind the subject.

Two failures follow from conflating them: asking the prompt for "no background"
and getting a plain white wall rendered as pixels, and setting transparency
while the prompt describes a rich scene, which yields a transparent file with
the scene baked into the subject's edges. Transparency also constrains output
format — a format without an alpha channel cannot carry it.

## What the prompt may invent, and what it may not

When expanding a terse user request into a full prompt, the boundary between
helpful specification and unrequested authorship is the thing to police
[official].

May be added:

- Lighting, time of day and weather consistent with the request.
- Lens and camera language, depth of field, framing and composition.
- Material, surface and texture detail on objects the user named.
- Rendering style, when the user gave none and the use case implies one.

May not be added:

- Characters, animals or objects the user did not imply.
- Brand names, logos, trademarks or product likenesses.
- Text, slogans or captions that were not requested.
- A colour palette that overrides one the user supplied.
- Narrative — a story, a mood arc, an implied event.

These are the additions the user cannot see you made until the asset is already
published. Report the final prompt actually sent, including anything the
provider's rewriter added, next to the delivered file.

## Aspect ratio drives resolution drives cost

The billing chain for hosted image generation is aspect ratio → resolution tier
→ emitted token count, and it is stepped rather than continuous [official]. A
given quality tier maps each aspect ratio onto a fixed pixel geometry, and that
geometry maps onto a fixed number of billed output tokens. Two consequences:

- Asking for a slightly taller frame can cross into the next tier and change
  the price with no visible change in detail.
- The cost of a batch is knowable before you run it, because the token count
  per image is fixed by the tier and not by the prompt.

Read the provider's current ratio-to-resolution-to-token table when you need
the numbers; do not carry them in code or in your head, because a model
generation change replaces the whole table.

Independently of price, most models were trained near one megapixel and behave
best there [community]. Far above it you get edge artefacts and duplicated
subjects; far below it you get hard crops and lost detail. Generate near the
trained resolution and resize deterministically afterwards.

## Prompt failures that get misread as model quality

| Symptom | Cause | Fix |
|---|---|---|
| Adding a negative prompt makes output worse | The model was not trained with negative conditioning; the text is injected as noise, not as removal [community] | Check the schema. If there is no negative-prompt field, describe what you want present instead |
| Over-saturated, high-contrast, "burnt" output | Guidance scale set too high [community] | Lower it; guidance trades prompt adherence against image plausibility |
| Identity replaced after a small requested change | A wholesale verb in the prompt [community] | Change X, keep Y unchanged |
| Output reads as generic stock imagery | Prompt made of flattering adjectives — stunning, cinematic, masterpiece [community] | Replace with visual facts: overcast daylight, brushed aluminium, 50 mm perspective |
| Iteration is not converging | Several variables changed per round | Change exactly one variable per iteration, and keep the rest of the prompt byte-identical |
| Request rejected by the safety filter | Emotive or ambiguous wording, not the subject itself | Rewrite clinically: strip the emotionally coloured language, keep the physical description. Do not retry unchanged and do not shop for a laxer model |

## Writing the artefact

- Never overwrite the source asset. Write a sibling with an explicit version
  suffix — `hero-v2.png` next to `hero.png` — so the approved bytes stay
  recoverable [official].
- Decide placement by use, not by convenience: an asset the project will ship
  belongs in the workspace with every referrer updated in the same change; a
  throwaway preview belongs in a temporary directory and should not acquire
  referrers.
- Report the final on-disk path and the final prompt actually sent. When the
  provider rewrote the prompt, the rewritten text is what produced the pixels;
  the original is not a reproduction recipe.
- Persist the generation record — prompt, model version string, request id,
  parameters, and the hash of the bytes you delivered — alongside the file.
  Without it, an image that later needs defending cannot be traced to the call
  that made it.

<!-- sources: openai-skills-imagegen, replicate-skills, google-gemini-docs, google-genmedia-skills, openai-docs -->
