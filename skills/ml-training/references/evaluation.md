# Evaluating a fine-tune

## Contents

- [Decide what would count as failure first](#decide-what-would-count-as-failure-first)
- [The four measurements](#the-four-measurements)
- [Loss is not quality](#loss-is-not-quality)
- [When a benchmark and a human disagree](#when-a-benchmark-and-a-human-disagree)
- [Regression: the part everyone skips](#regression-the-part-everyone-skips)
- [Making runs comparable](#making-runs-comparable)
- [LLM-as-judge, carefully](#llm-as-judge-carefully)

## Decide what would count as failure first

Write the acceptance criterion before the run, in a form that can come out
false: "escalation tickets routed to the right queue in >= 85% of a 200-item
held-out set, with no regression beyond 2 points on the general instruction
eval." A criterion written after the numbers arrive describes the numbers.

The corollary: pick the eval set before training, freeze it, and never train
on anything derived from it — including data you filtered using it.

## The four measurements

A fine-tune needs all four; three of them are routinely skipped.

| Measurement | Answers | Skipping it means |
|---|---|---|
| Task metric on a held-out set | did it learn the thing | no evidence at all |
| Regression on general capability | what did it forget | shipping a model that is better at one task and worse at everything |
| Base-model baseline on the same set | was training necessary | crediting the fine-tune for what the base model already did |
| Human or behavioural check on real inputs | does it work in the product | a benchmark number nobody in the product recognises |

The base-model baseline is the cheapest and the most often missing. Run the
eval against the untouched base model first. If the delta is small, you have
learned something valuable for the cost of an inference pass.

## Loss is not quality

Eval loss measures likelihood of a reference answer under the model. It falls
when the model memorises the reference style and it rises when the model
produces a *better* answer worded differently. Use it to detect divergence
and overfitting, not to decide whether the model is good.

What the curves actually tell you:

| Pattern | Reading |
|---|---|
| Train down, eval down | learning; keep going |
| Train down, eval flat then up | overfitting; stop at the eval minimum |
| Both flat from step 0 | learning rate too low, or the loss is masked out entirely |
| Loss to NaN mid-run | fp16 overflow, a bad batch, or LR too high — check in that order |
| Loss drops vertically at an epoch boundary | the model is memorising, not generalising |
| Eval loss great, humans unimpressed | contamination, or the metric is not the goal |

## When a benchmark and a human disagree

The human is the measurement and the benchmark is the proxy. A large gap in
the benchmark's favour has a short list of causes, in order of likelihood:

1. **Contamination** — the benchmark, or something near-duplicate to it, is
   in the training data. Check before anything else, by indexing the training
   corpus's n-grams and streaming the benchmark through that index.
2. **Non-independent sets** — the reported subset was carved out of the eval
   split, so two numbers are one number.
3. **The metric is not the behaviour** — exact match rewards reproducing the
   reference string, which a memorising model does perfectly.
4. **Distribution mismatch** — the eval set is the easy part of the traffic.

None of these is fixed by training longer, and all of them are cheaper to
diagnose than to re-run.

## Regression: the part everyone skips

Every fine-tune trades something. Keep a fixed regression suite and run it
for every candidate:

- a general instruction-following set (a few hundred items is enough to see a
  multi-point drop)
- the format and safety behaviours you rely on — does it still produce valid
  JSON, still refuse what it used to refuse
- the previous release's task set, so quality is monotone across releases

Run it against base, previous release, and candidate in the same pass, with
the same decoding parameters. A regression suite that is only run when
someone is suspicious is not a regression suite.

## Making runs comparable

Two runs are comparable only if the decoding and prompting are identical.
Pin, and record with the result:

- decoding parameters (temperature, top-p, max tokens, seed, stop strings)
- the exact prompt and chat template, rendered
- the harness and its version, and the task version within it
- the eval set's content hash

Greedy decoding (temperature 0) removes one variance source and makes small
deltas readable; report sampled numbers when sampling is what you ship, but
do not compare a greedy run against a sampled one.

`lm-evaluation-harness` is the default for standard academic tasks because it
pins prompt formats per task — which is also why its numbers can differ from
a paper's: the paper used a different prompt. The version and task name
belong in the report.

## LLM-as-judge, carefully

A judge model is the only affordable option for open-ended quality, and it
has known biases: position (prefers the first answer), length (prefers the
longer one), and self-preference (prefers text from its own family).

Minimum discipline:

- Randomise or swap the presentation order and average over both.
- Pin the judge model and its version; a judge upgrade invalidates the whole
  history of scores.
- Never judge with the model you are training, or with its teacher.
- Calibrate once against human labels on 50-100 items and report the
  agreement rate. A judge you have not calibrated produces a number with
  unknown units.

<!-- sources: lm-eval-harness, hf-skills -->
