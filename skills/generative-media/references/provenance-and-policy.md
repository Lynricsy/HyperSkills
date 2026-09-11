# Provenance, disclosure and content policy

## Contents

- [Three layers, all of them required](#three-layers-all-of-them-required)
- [Layer 1: platform-enforced marking](#layer-1-platform-enforced-marking)
- [C2PA vocabulary worth using precisely](#c2pa-vocabulary-worth-using-precisely)
- [Layer 2: disclosure a person can perceive](#layer-2-disclosure-a-person-can-perceive)
- [Layer 3: the generation record](#layer-3-the-generation-record)
- [Downstream processing strips metadata by default](#downstream-processing-strips-metadata-by-default)
- [Content policy refusals](#content-policy-refusals)

## Three layers, all of them required

Provenance for generated media is three independent obligations that are
routinely collapsed into one and then all missed:

```
Platform layer   provider-embedded marking (invisible watermark, signed manifest)
                 -> cannot be disabled; you can read and verify it
Compliance layer explicit disclosure that a human perceives
                 -> a metadata field does not satisfy it
Engineering layer prompt, model version, request id, parameters, output hash
                 -> your own record, the only one that answers "which call made this"
```

Satisfying any one of them leaves the other two unsatisfied. An asset with an
intact provider manifest and no visible label fails compliance; a labelled
asset with no generation record cannot be defended when someone disputes what
it depicts.

## Layer 1: platform-enforced marking

Major providers mark every generated asset by default and offer no switch:
generated images carry an invisible pixel watermark (SynthID on one major
platform), and generated images and video carry C2PA content-credential
metadata [official]. This is a property of the output, not a feature you opt
into.

What that means in practice:

- Your job is to preserve and verify, not to produce or suppress. Read the
  manifest after download, verify it validates, and record the result
  alongside the artefact hash.
- Absence of marking is a signal. If an asset that should carry provider
  marking does not, something in the pipeline removed it — that is a bug to
  find, not a state to accept.
- Invisible watermarking and embedded manifests are different mechanisms with
  different survival characteristics. A manifest lives in file metadata and
  dies with it; the watermark is in the pixels and survives some, though not
  all, transformation. Do not treat either as sufficient alone.
- Never remove, alter or forge these markings. Doing so to quiet a compliance
  complaint converts a policy problem into misrepresentation.

## C2PA vocabulary worth using precisely

Content Credentials have a small, exact vocabulary, and using it loosely makes
provenance discussions unresolvable [official]:

| Term | Meaning |
|---|---|
| Manifest | The provenance container bound to an asset; an asset may carry several, forming a chain |
| Assertion | One statement inside a manifest — how the asset was created, what actions were applied, which ingredients were used |
| Claim | The set of assertions gathered for signing, with the hashes binding them to the asset bytes |
| Claim signature | The cryptographic signature over the claim, made by the actor asserting it |
| Ingredient | A prior asset consumed to produce this one, referenced with its own manifest |
| Validation | Checking signature, certificate chain and the hash bindings to the bytes actually present |
| Trust list | The set of signing certificates a verifier accepts; a valid signature from an untrusted signer is a different outcome from an invalid signature |

Two distinctions that matter when reporting a result. A manifest that fails
validation is not the same as an absent manifest — the first means the bytes
changed after signing, the second means nothing was ever asserted. And a
validated manifest attests to who asserted what, not to whether the assertion
is true; it makes provenance attributable, not correct.

## Layer 2: disclosure a person can perceive

Provider usage policies require a clear disclosure to end users that a
synthetic voice is AI-generated [official], and comparable expectations apply
to generated imagery. The operative requirement is that a person can tell.

Consequences for implementation:

- Metadata alone does not satisfy it. Nobody inspects file metadata, and the
  most common delivery pipelines discard it.
- The disclosure must live where the asset is consumed: a visible caption or
  badge next to an image, a spoken or written statement accompanying
  narration, a marked entry in a list where synthetic and human-recorded items
  sit side by side.
- It must survive the channel. A label applied in a CMS field that the
  published template ignores has not been applied.
- Disclosure is a product requirement with a deadline of first publication,
  not a task to schedule later. Retrofitting it across already-published
  assets requires the engineering-layer record to identify which assets are
  affected — another reason that record has to exist.

Disclosure does not substitute for the platform layer, and the platform layer
does not substitute for disclosure.

## Layer 3: the generation record

For every artefact you publish, persist, in one row and durably:

- The prompt as actually sent, including any provider-side rewriting — the
  rewritten text is what produced the output.
- The model version string, exactly as the provider reported it, not the
  friendly name.
- All parameters, including seed, aspect ratio or duration, quality tier,
  reference image hashes and, locally, library and weights revisions.
- The request or job id.
- The hash of the bytes you delivered, and the hash of the bytes the provider
  returned if post-processing changed them.
- Timestamps, and the human who approved it.

This record answers questions no other system can: which call produced this
published image, whether a given asset is synthetic at all, which assets used
a model version that has since been withdrawn, and which assets need
re-disclosure when policy changes. Filename conventions do not answer any of
them — filenames get renamed, and processing pipelines rewrite them.

The record is also the reproducibility artefact of last resort. Hosted
generation cannot be replayed; the approved bytes plus this record are what
"we can account for this image" means.

## Downstream processing strips metadata by default

This is the most common way a provenance chain dies, and it is silent. Image
and video processing tools discard metadata unless told to keep it: a resize,
a format conversion, a thumbnail step, a CDN transformation or a social
platform's own re-encode can all drop an embedded manifest while producing a
visually identical file. Nothing errors. The asset simply stops being
attributable.

The processing itself is deterministic work — same input, same bytes — and
belongs to the deterministic toolchain. What this side owes that hand-off is
the constraint, stated explicitly rather than assumed:

- Metadata preservation is a requirement of every step between generation and
  publication, including steps run by a CDN or a third-party platform.
- Where a step cannot preserve the manifest, the output must be re-signed, or
  the chain must record the break deliberately, with the processed asset
  referencing the original as an ingredient.
- Verification belongs at the end of the pipeline, on the bytes that are
  actually published, not on the bytes the provider returned. A check that
  runs before the resize proves nothing about what shipped.
- The invisible watermark may survive a transformation that destroys the
  manifest, so a stripped manifest does not mean the asset is unmarked — and
  a surviving watermark does not excuse the stripped manifest.

## Content policy refusals

A refusal or safety block is a legitimate outcome and the only correct
responses are to change the request or to stop:

- Rewrite clinically where the block came from wording rather than intent:
  remove emotive and ambiguous language, keep the physical description.
- Report the block to the requester with the attempted rewrite attached, so a
  person decides what happens next.
- Do not split a blocked request into pieces designed to pass individually,
  do not obfuscate the prompt, and do not route to a provider chosen for a
  weaker filter. Those are circumvention, they are usually terms violations,
  and they convert a provider's decision into your liability.
- Region-dependent restrictions — notably on generating people — are
  configuration, not obstacles. Resolve them per deployment region and fail at
  configuration time rather than working around them at request time
  [official].

Persistent blocks on a legitimate use case are an escalation to the provider,
not an engineering problem to solve in code.

<!-- sources: c2pa-spec, google-gemini-docs, openai-skills-speech, openai-skills-imagegen, google-genmedia-skills -->
