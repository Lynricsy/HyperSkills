# Speech synthesis and recognition

## Contents

- [Synthesis: the response is not a playable file](#synthesis-the-response-is-not-a-playable-file)
- [Synthesis: input limits and where to split](#synthesis-input-limits-and-where-to-split)
- [Synthesis: keeping voice and pacing stable across segments](#synthesis-keeping-voice-and-pacing-stable-across-segments)
- [Synthesis: joining segments](#synthesis-joining-segments)
- [Synthesis: markup is read aloud](#synthesis-markup-is-read-aloud)
- [Synthesis: directing a performance](#synthesis-directing-a-performance)
- [Synthesis: disclosure is mandatory](#synthesis-disclosure-is-mandatory)
- [Recognition: request limits](#recognition-request-limits)
- [Recognition: the 30-second window and its three consequences](#recognition-the-30-second-window-and-its-three-consequences)
- [Recognition: split on silence, then re-add the offset](#recognition-split-on-silence-then-re-add-the-offset)
- [Recognition: the prompt field is hallucination fuel](#recognition-the-prompt-field-is-hallucination-fuel)
- [Recognition: diarisation is a different model](#recognition-diarisation-is-a-different-model)
- [Recognition: repetition and low-resource languages](#recognition-repetition-and-low-resource-languages)
- [Recognition: input conversion is not your job](#recognition-input-conversion-is-not-your-job)

## Synthesis: the response is not a playable file

Hosted speech endpoints commonly return raw PCM — 24 kHz, 16-bit, mono, with
no container and no header [official]. The same is true of realtime audio
sockets, which is what makes it a general trap rather than one vendor's quirk.

Naming those bytes `.wav` does not make them a WAV. A browser player, an
`<audio>` element, a media library and a mobile player all reject the file,
and the error they report ("unsupported format", "cannot decode") points at
the player rather than at the missing 44-byte RIFF header.

Writing that header, remuxing into another container, resampling to a target
rate, and normalising loudness are deterministic operations: same input, same
bytes. They belong in the deterministic toolchain, and it needs three facts
from you — sample rate, bit depth, channel count — because raw PCM carries
none of them. Getting the rate wrong does not error; it changes the pitch.

Where the endpoint offers an encoded output format instead, taking it removes
this whole class of problem. Raw PCM is worth the extra step only when you are
streaming or concatenating before encoding.

## Synthesis: input limits and where to split

Every synthesis endpoint caps a single request, but the cap is per provider
and per model, and the providers do not even agree on the unit: one counts
characters of input, another counts tokens of a session context window.
Read the limit off the model you resolved, the same way you resolved the
model — a number carried over from another vendor's endpoint is a bug that
only shows up on long input.

Two failure shapes follow from the cap, and they need different handling:

- The request is rejected. Benign: you find out immediately.
- The request succeeds and the audio is truncated, with the truncation
  reported only in the response's finish or stop reason. Check that field on
  every response; a job that writes whatever came back ships half a chapter
  and reports success.

A per-minute request quota is the second constraint, and it is the one that
decides wall-clock time for long-form work: a chapter split into dozens of
segments spends minutes queueing even when every call is fast. Look the quota
up for the account and model in use, build it into the client as an enforced
limit rather than a comment, and derive the job's concurrency from it.

Where you split matters more than that you split. Split on sentence or
paragraph boundaries; never on a fixed character count. A fixed-length cut
lands mid-clause, and the model gives each segment the falling intonation of a
completed sentence, so the listener hears the text break even though the audio
is continuous. Pack whole sentences up to the cap, and prefer a paragraph
boundary when one is available within the last quarter of the budget.

## Synthesis: keeping voice and pacing stable across segments

Each request is independent. Two segments of the same chapter are two
unrelated performances unless you make them identical inputs:

- Same voice, same model version, same output format on every segment of one
  deliverable. A mid-job model change is audible.
- Same style instructions string, byte for byte. Paraphrasing the direction
  between segments changes the delivery.
- Instruction following is model-dependent: on models that predate
  instruction-following synthesis, a style instruction is accepted and ignored
  [official]. Silent ignoring is the failure — you will hear no change and
  conclude the wording was too weak. Check the model's schema for the field
  before spending iterations on the prose.
- Some drift in energy and speaking rate survives all of this. Audition the
  segment boundaries rather than only the first segment.

## Synthesis: joining segments

Concatenating segments back to back produces speech that sounds hurried and
unnatural, because each segment starts at its first phoneme. Insert deliberate
silence at joins — short between sentences, longer between paragraphs and
sections — and keep the values consistent across the deliverable.

Insertion and concatenation are deterministic work — same input, same bytes —
and belong to the deterministic toolchain. Two constraints travel with the
hand-off: every segment must share one sample rate and channel count before
joining, and joining encoded segments by byte concatenation corrupts the
result for most formats. Join in the PCM domain, then encode once.

## Synthesis: markup is read aloud

Markdown, HTML and templating syntax reach the model as text and are performed
as text: asterisks become spoken emphasis artefacts or literal readings, list
bullets become audible, link syntax becomes a recitation of the URL, and code
fences get read character by character.

Flatten to plain prose before synthesis — strip markup, expand abbreviations
that should be spoken in full, and decide explicitly what happens to code
blocks, tables and footnotes, which usually means omitting them rather than
narrating them.

## Synthesis: directing a performance

For anything beyond neutral narration, the prompt is a direction sheet, not a
sentence. Four blocks, in order [official]:

1. **Audio profile** — who the voice belongs to: age, register, texture.
2. **The scene** — where they are, who they are addressing, emotional state.
3. **Director's notes** — style, accent, pacing. Accents work better when
   specified to a locality rather than a country.
4. **Transcript** — the words, with inline audio tags.

Per-dimension labels that models respond to: voice affect, tone, pacing,
emotion, pronunciation, pauses, emphasis, delivery [official]. The two
framings are the same instrument at different granularity — the four-block
form is the skeleton, the label list is the field set.

Inline tags carry rough durations: a short pause is on the order of 250 ms, a
medium pause 500 ms, a long pause 1000 ms or more [official]. Tags must be
written in English even when the spoken line is not — `[anger] Je ne sais pas`
works, a translated tag does not.

When you want variation in delivery, ask for several takes inside one request
rather than issuing several requests. One request costs one call and the takes
share a voice state; three requests cost three calls and drift apart
[official].

## Synthesis: disclosure is mandatory

Provider usage policies require a clear disclosure to end users that the voice
is AI-generated [official]. This is a policy obligation, not a courtesy, and
it applies wherever the audio is published — not only where a user might be
deceived.

Two design implications: the disclosure has to reach a person (a visible
label, a spoken preamble, a marked entry in a playlist), and it has to survive
the delivery pipeline, which metadata alone usually does not. Synthetic
narration sitting in the same list as human-recorded narration is the case
that most obviously needs it.

## Recognition: request limits

Hosted transcription endpoints cap a single request at about 25 MB and accept
a fixed format whitelist — commonly mp3, mp4, mpeg, mpga, m4a, wav and webm
[official]. Both produce clean request failures, which makes them the easy
half of the problem.

## Recognition: the 30-second window and its three consequences

The open-weights recognition architecture that nearly every hosted
transcription service is built on consumes audio in a sliding 30-second
window and decodes each window autoregressively; the low-level path pads or
truncates the input to exactly 30 seconds before computing features
[official]. Hosted services inherit the window, which is why "audio longer
than 30 seconds needs an explicit chunking strategy" appears in vendor docs —
and why omitting it returns a truncated transcript rather than an error
[official].

Three consequences that get misdiagnosed as model quality:

1. **Timestamp drift.** Segment timestamps accumulate error across windows, so
   subtitle timing that is right at the start is late by the end. Do not
   derive precise cue times from a single long-file transcription; re-anchor
   per chunk.
2. **Words cut at boundaries.** A word straddling a window edge is split
   across two decodes and often comes back twice, or garbled, or not at all.
3. **Hallucinated speech in silence.** A window containing only silence, music
   or noise still gets decoded, and the model is trained to emit text. It
   invents a plausible sentence — commonly a stock phrase from the training
   data. The transcript looks fluent and is fiction.

The underlying causes are documented by the model authors: large-scale weakly
supervised training produces text that was never spoken, because the model
mixes predicting the next word with transcribing the audio [official].

## Recognition: split on silence, then re-add the offset

The standard mitigation for all three consequences is to segment before
transcribing, using voice activity detection or silence detection, and to
transcribe each speech region separately [official]. Local recognition
tooling ships VAD for exactly this reason.

Two rules make the result usable:

- Cut in silence, not on a clock. A boundary inside speech reintroduces
  boundary-cut words.
- Each chunk's timestamps are relative to the chunk. Add the chunk's start
  offset to every timestamp before merging, and keep the offsets in the
  record — this is the step that is silently forgotten, producing a transcript
  where every cue after the first chunk is early by a growing amount.

Dropping non-speech regions entirely is also what suppresses the silence
hallucinations: text can only be invented for audio that was submitted.

## Recognition: the prompt field is hallucination fuel

The prompt or keyword field exists to bias decoding towards domain vocabulary —
product names, jargon, proper nouns — and it works. It also raises the
probability of those exact strings appearing where they were not said, because
biasing decoding is the whole mechanism.

Keep the list short and specific to the audio in hand, never a generic
glossary, and treat an unexpectedly perfect appearance of a prompted term as
suspect. Where a literal keyword list parameter is offered separately from a
free-text prompt, prefer it: it states intent without supplying a sentence for
the model to complete.

## Recognition: diarisation is a different model

Speaker diarisation is served by a separate model, not a flag on the ordinary
transcription model, and the diarising model may reject the prompt parameter
entirely [official]. That is a real capability loss, not an inconvenience: the
vocabulary-biasing technique used to rescue recognition accuracy is
unavailable exactly when you also want speakers labelled.

Known-speaker references are also capped — around four [official]. Beyond
that, speakers come back as anonymous labels that are consistent within one
request and meaningless across requests, so cross-file speaker identity has to
be resolved by your own code.

Decide up front which you need. Running both models over the same audio and
merging transcripts on timestamps is possible, but the two segmentations will
not align exactly, and reconciling them is more work than it looks.

## Recognition: repetition and low-resource languages

The sequence-to-sequence architecture is prone to emitting repeated text, and
beam search and temperature scheduling only partly mitigate it [official].
Repetition is machine-detectable: a repeated n-gram loop within a segment is
almost always a decode failure rather than a speaker repeating themselves.
Flag it, re-decode the affected chunk, and do not ship it silently.

Both this and hallucination are markedly worse for low-resource languages
[official]. Where accuracy matters in one of those, budget for sampled human
review rather than for a better prompt.

## Recognition: input conversion is not your job

Local recognition binaries typically accept only 16-bit WAV and need audio at
16 kHz mono. Converting to it is a deterministic transcode — same input, same
bytes — and belongs to the deterministic toolchain. This reference constrains only
what recognition needs from the result: 16 kHz, mono, 16-bit PCM in a WAV
container, under the endpoint's size cap, with any leading silence preserved
rather than trimmed, since trimming shifts every timestamp downstream.

The split matters because the two halves fail differently. A wrong sample rate
is a parameter bug with a deterministic fix. A transcript containing a
sentence nobody said is an inherent property of probabilistic recognition, and
the fix is segmentation, detection and review — not a better command line.

<!-- sources: openai-skills-speech, openai-skills-transcribe, google-genmedia-skills, google-gemini-docs, openai-whisper, whisper-cpp, openai-docs -->
