# Retrieval for generation

## Contents

- [What retrieval is actually for](#what-retrieval-is-actually-for)
- [The retrieval unit is not the storage unit](#the-retrieval-unit-is-not-the-storage-unit)
- [Chunking decisions that change answers](#chunking-decisions-that-change-answers)
- [Embedding symmetry](#embedding-symmetry)
- [Ranking: k, a floor, and a reranker](#ranking-k-a-floor-and-a-reranker)
- [Hybrid retrieval](#hybrid-retrieval)
- [Metadata filters before vectors](#metadata-filters-before-vectors)
- [Citations and traceability](#citations-and-traceability)
- [The corpus is untrusted input](#the-corpus-is-untrusted-input)
- [Measuring retrieval separately from generation](#measuring-retrieval-separately-from-generation)
- [When not to retrieve](#when-not-to-retrieve)

## What retrieval is actually for

Retrieval exists to put the smallest sufficient set of true statements in
front of the model. Every failure mode below is a way of violating one of
those three words: *smallest* (budget blown, relevant chunk buried),
*sufficient* (the answer's other half was in the next chunk), or *true* (the
corpus is stale, or someone wrote into it).

Index internals — HNSW parameters, IVF lists, recall against exact search,
build memory — are the database's problem: the `postgres`, `redis`,
`mongodb` or `elasticsearch` skill. This file covers what you put in it and
what you do with what comes out.

## The retrieval unit is not the storage unit

Embedding a whole document as one vector is the single most common structural
defect, and it is not a tuning problem:

- One vector is one direction. A 91 KB returns policy covering EU rights,
  damaged goods, and gift receipts produces a vector that is the average of
  all three, close to nothing in particular. A two-paragraph file that is
  entirely about gift receipts outranks it on a gift-receipt question, even
  when the policy is the authoritative source.
- Retrieval then returns the whole document, so one hit costs the entire
  budget and the model must locate the relevant paragraph itself — inside a
  context that also has to hold seven other documents.

Separate the two units:

- **Retrieval unit** — small enough that its embedding is about one thing.
  Sections under a heading, or token-bounded windows of a few hundred tokens
  with overlap.
- **Context unit** — what actually goes into the prompt once a chunk wins.
  Often the chunk plus its heading path, its neighbours, or its parent
  section. Store the parent id on every chunk so this is a lookup, not a
  re-search.

## Chunking decisions that change answers

- **Split on structure first.** Markdown headings, function boundaries, list
  items, table rows. A chunk that starts mid-sentence embeds partly as
  gibberish. A chunk that splits a table from its header loses the meaning of
  every column.
- **Carry the path.** Prefix each chunk with its document title and heading
  trail (`returns.md › Damaged goods › EU customers`). Retrieval then works
  for questions phrased in the document's vocabulary rather than the chunk's,
  and the model can tell two similarly worded chunks apart.
- **Overlap only to repair boundaries.** 10–20% is enough to keep a sentence
  from being cut. More overlap multiplies storage and returns near-duplicate
  neighbours that each consume budget and say the same thing. If duplicates
  keep appearing in the top-k, dedupe by document and offset before building
  the prompt.
- **Size by tokens, not characters.** A 1000-character chunk is ~165 tokens
  of prose but ~425 tokens of JSON (`context-budget.md`), so a
  character-sized chunk store has wildly variable cost per hit.
- **Keep tables and code whole or split them deliberately.** Half a code
  block retrieved without its imports is an answer that will not run.
- **Re-chunking is a re-index.** Changing the rule invalidates every stored
  vector; version the chunking rule alongside the embedding model so you can
  tell which documents were indexed under which.

## Embedding symmetry

Index-time and query-time embeddings must come from the same model, the same
dimension, and the same normalisation. Mismatches do not raise: the numbers
are still valid vectors, so the search returns the nearest of the wrong
thing, and every answer is subtly off with no error anywhere.

Store the model name and dimension as columns next to the vector, and assert
at startup that the query embedder matches. When you change models, reindex
to a new table and switch atomically — an index containing two models'
vectors is permanently wrong for both.

Asymmetric-by-design models (a query encoder plus a document encoder, or
instruction-prefixed models needing `query:` / `passage:` prefixes) are the
exception, and they fail the same way if you swap the prefixes: no error,
worse results. Write the prefix into the same helper both paths call.

## Ranking: k, a floor, and a reranker

`LIMIT 8` with no threshold means eight chunks come back for every question,
including questions the corpus does not answer. The model then has eight
irrelevant passages and an instruction to answer from them, which is the
cheapest possible way to manufacture a confident wrong answer.

The shape that works:

1. Retrieve a wide candidate set — 30 to 100 — by vector similarity. Recall
   matters here, precision does not.
2. Apply a floor. Either an absolute similarity threshold, calibrated once
   against a labelled set, or a relative one (drop candidates below a
   fraction of the top score, which travels better across query types).
3. Rerank the survivors with a cross-encoder or a rerank endpoint. A
   cross-encoder reads the query and the passage together, so it can tell
   "how do I refund a gift" from "how do I gift a refund", which cosine
   similarity on independent embeddings cannot.
4. Take as many as the context budget allows, in rank order, and stop.
5. If nothing survives the floor, return nothing, and let the generation step
   say it cannot answer. "I don't have that in the handbook" is a correct
   answer and a much cheaper support ticket than a wrong one.

Reranking is the highest-value addition to a naive pipeline, because step 1
can then be tuned for recall instead of being both the recall and the
precision stage.

## Hybrid retrieval

Vector search is weak exactly where support and engineering corpora are
strongest: exact identifiers, error codes, SKU numbers, flag names, rare
proper nouns. `ERR_TLS_CERT_ALTNAME_INVALID` is one token soup in embedding
space and an exact match in a lexical index.

Run both, then combine by rank rather than by score — reciprocal rank fusion
or a simple interleave. Scores from a BM25 index and a cosine index are not
on a comparable scale, and normalising them per query is a tuning problem
with no stable answer.

Cheap heuristic for whether you need it: if user queries contain tokens that
appear verbatim in the documents and nowhere else, you need lexical
retrieval.

## Metadata filters before vectors

Tenant, language, product version, effective date, visibility. These are
`WHERE` clauses, not similarity concerns, and applying them after retrieval
means the top-k is spent on rows the user may not see — sometimes leaving
zero results after filtering, which reads as "no answer exists".

Version and date filters are the ones teams forget. A corpus containing both
the v2 and v3 policy will return whichever embeds closer, and the model has
no way to know v3 supersedes v2. Either filter to the current version or put
the version in the chunk text so the model can prefer it.

## Citations and traceability

Each chunk enters the prompt with a stable id — path plus line range, or a
document id plus chunk index — and the instruction requires the answer to
cite the ids it used:

```
<chunk id="handbook/returns.md#L120-L164" title="Returns › Damaged goods">
…
</chunk>
```

This is not a UI nicety. Without it:

- a wrong answer cannot be attributed to a document, so you cannot tell a
  retrieval failure from a generation failure, and you fix the wrong layer;
- you cannot check whether the answer is grounded in what was retrieved, so
  your eval cannot assert grounding (`evaluation.md`);
- a stale document keeps producing wrong answers indefinitely, because
  nothing points at it.

Validate the citations in code: every cited id must be one of the ids you
actually supplied. A fabricated citation is the clearest possible signal that
the answer was not grounded, and it is a one-line check.

## The corpus is untrusted input

Retrieved text is third-party text. Anyone who can write into the corpus —
a public wiki, a shared drive, a ticket the customer typed, a crawled page —
can write instructions into it, and those instructions arrive inside your
prompt. Treat the corpus as a write surface with an access model:

- Retrieved chunks go in a labelled data region, never in an instruction turn
  (`prompt-structure.md`, `prompt-injection.md`).
- Ingestion sanitises the delimiter sequence you use for that region.
- Embeddings are recoverable text, not hashes: an embedding store holding
  customer PII is a store holding customer PII, and access to it must match.
  The same applies to what you log — a vector plus its source text in a debug
  log is the document, copied.
- Deletion must propagate to the index. A document removed from the source of
  truth but still embedded keeps answering questions.

## Measuring retrieval separately from generation

An end-to-end quality score cannot tell you which half is broken. Two cheap
measurements pay for themselves:

- **Retrieval**: for a set of questions with known answer locations, does the
  correct chunk appear in the top-k, and at what rank? Recall@k and MRR need
  no judge and no model call.
- **Grounding**: does every claim in the answer trace to a retrieved chunk?
  Checkable by citation validation for the mechanical part, and by a judge
  for the semantic part.

When end-to-end quality drops, check retrieval first. It is the half that
changes silently when the corpus, the chunker, or the embedding model moves.

## When not to retrieve

- The corpus is small enough to fit in the window, is stable, and is the same
  for every request. Put it in the cached prefix and skip the machinery — a
  retrieval pipeline over 30 KB of policy is infrastructure with negative
  value.
- The question is about the conversation or the user's own data. That is
  state to pass, not a corpus to search.
- The answer requires aggregation over the whole corpus ("how many policies
  mention EU rights"). Top-k retrieval structurally cannot answer counting
  questions; query the data instead.

<!-- sources: langchain-skills, google-skills, owasp-llm-top10, vercel-ai-sdk, murat-context-engineering, promptfoo -->
