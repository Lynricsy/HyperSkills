# Dataset hygiene

## Contents

- [The order of operations](#the-order-of-operations)
- [Deduplication](#deduplication)
- [Splitting](#splitting)
- [Contamination against public benchmarks](#contamination-against-public-benchmarks)
- [Look at the tokens, not the rows](#look-at-the-tokens-not-the-rows)
- [Labels and loss masking](#labels-and-loss-masking)
- [Quantity, quality, and what a small set can do](#quantity-quality-and-what-a-small-set-can-do)

## The order of operations

This sequence is not a style preference; each step out of order produces a
specific, silent defect:

```
1. pool every source
2. normalise            (whitespace, casing for comparison only, unicode)
3. deduplicate          (exact, then near)
4. decontaminate        against every benchmark you will report
5. split                (group by document / thread / user, not by row)
6. inspect              length distribution, label balance, rendered template
```

Deduplicating *after* splitting is the canonical mistake: it removes
duplicates inside each split and leaves every cross-split pair intact, which
is exactly the pair that inflates your eval number. Splitting before
decontaminating means the benchmark rows are already in `train`.

`scripts/dataset_overlap.py` runs steps 3-4 as a check and exits non-zero on
leakage, so it can gate a pipeline.

## Deduplication

Three levels, increasing cost:

| Level | Method | Catches |
|---|---|---|
| Exact | hash of the normalised string | re-exports, repeated scrapes |
| Near | n-gram Jaccard or MinHash/LSH over shingles | re-posts, templated rows, minor edits |
| Semantic | embedding similarity | paraphrase, translation |

Exact dedup alone is close to useless on real corpora. Support tickets get
re-opened with `RE:` prefixes, documentation gets copied between pages, and
scraped web text arrives with different boilerplate around identical bodies.
A corpus that looks 2% duplicated by hash is routinely 20-30% duplicated by
n-gram overlap.

Thresholds worth defending: Jaccard >= 0.8 over word n-grams marks
near-identical rows; 0.6 is appropriate when heavy shared boilerplate
dominates the token count. Pick one, write it down next to the dataset
version, and keep it stable across runs — changing the threshold changes the
dataset, which changes every number measured on it.

Do not compare every pair. Build an inverted index from n-gram to row id and
only compare rows that share a gram; pairwise comparison is quadratic and
does not finish on a corpus of any interesting size.

## Splitting

Split by the unit of *independence*, which is almost never the row:

- Conversations: split by thread id, so no turn of a conversation appears on
  both sides.
- Documents chunked into passages: split by document id.
- Per-customer or per-author data: split by that identity, or the model
  learns the author and the eval measures how well it memorised them.
- Time series and anything with a temporal drift: split by time, with eval
  strictly after train. A random split on time-ordered data reports a number
  you will never see in production.

A held-out set carved out of an already-derived set is not independent. If
your reported benchmark subset is sampled from the eval split, the two
numbers move together and neither is a check on the other.

## Contamination against public benchmarks

Any public benchmark you intend to report has to be checked against the
training corpus, not assumed clean. Mixing a benchmark into training "for
domain coverage" makes the score meaningless rather than better.

The standard definition, from the GPT-3 paper's Appendix C and used by
`lm-evaluation-harness`'s decontamination pass: an eval document is
contaminated if it shares **any n-gram** with any training document, with n
in the 8-13 range; 13 is the usual single value. [official]

Two practical notes:

- Run it in the direction that scales: index the training n-grams once, then
  stream the eval set through the index. The reverse is what makes people
  abandon decontamination as "too slow".
- Report the contaminated fraction alongside the score. A benchmark with 4%
  contamination is usable with a caveat; one with 40% is not a measurement.

When contamination is discovered after training, the honest options are to
re-measure on a clean subset and say so, or to retrain. Adjusting the
threshold until the number looks acceptable is the one option that is not
available.

## Look at the tokens, not the rows

"240k examples" says nothing about cost or about truncation. Before any
launch, compute the tokenised length distribution with the **exact tokenizer
and chat template** you will train with:

- median and p99 length — `max_length` is chosen against these, not guessed
- fraction of rows that would be truncated at the chosen `max_length`
- total token count — this, times epochs, is what you are paying for

A p99 of 9.6k against `max_length=1024` means 1% of your rows enter training
as a truncated prompt with the answer cut off. They are not slightly worse
examples; they are noise with a loss attached.

Padding waste is the other half. If the median is 1.4k and `max_length` is
8192, most of every batch is padding. Fix it with packing (concatenate short
examples), padding-free batching, or length-grouped sampling — in that order
of preference.

## Labels and loss masking

For instruction data the loss belongs on the assistant turns. Verify it
rather than trusting the default: take one batch, find the positions where
`labels != -100`, and decode them. What comes out should be exactly the text
you want the model to produce. This five-line check catches prompt-masking
bugs, template mismatches and off-by-one shifts in one go, and it is the
single highest-value inspection in the whole pipeline.

Check the rendered template the same way: decode one full training example to
a string, and compare it byte-for-byte with what the serving stack sends. A
missing BOS token or a different system-prompt wrapper degrades every
downstream number without ever failing.

## Quantity, quality, and what a small set can do

A thousand carefully curated examples routinely beat fifty thousand scraped
ones for style, format and tone. They do not beat them for coverage: a
behaviour the training set never demonstrates will not appear.

The useful distinction is what you are teaching:

| Goal | Data that works | Rough volume |
|---|---|---|
| Output format, tone, refusal style | curated, consistent, hand-checked | 500-5,000 |
| A task the base model can nearly do | demonstrations of the task | 1,000-20,000 |
| A domain's vocabulary and idiom | raw domain text (continued pretraining) | 10^8 tokens and up |
| Facts that change | not a training set — use retrieval | — |

<!-- sources: lm-eval-harness, hf-skills, trl-docs -->
