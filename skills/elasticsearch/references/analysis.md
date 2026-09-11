# Text analysis

Verified against: Elasticsearch 9.5.3 (Lucene 10.5.1).

## Contents

- [The chain, and where it runs](#the-chain-and-where-it-runs)
- [Index analyzer versus search analyzer](#index-analyzer-versus-search-analyzer)
- [Autocomplete without breaking search](#autocomplete-without-breaking-search)
- [Synonyms](#synonyms)
- [Language handling](#language-handling)
- [Normalizers for keyword fields](#normalizers-for-keyword-fields)
- [Debugging analysis](#debugging-analysis)

## The chain, and where it runs

A `text` field is turned into terms by three stages, in order:

1. **Character filters** — rewrite the raw string (`html_strip`, `mapping`, `pattern_replace`).
2. **Tokenizer** — split into tokens. Exactly one (`standard`, `whitespace`, `keyword`, `pattern`,
   `edge_ngram`, `ngram`, `path_hierarchy`, plus the language-specific ones).
3. **Token filters** — rewrite or drop tokens (`lowercase`, `asciifolding`, `stop`, `stemmer`,
   `synonym_graph`, `shingle`, `edge_ngram`).

The output of the chain is what is in the index. Nothing else is. A query term that the chain would
have transformed differently will not match, and the failure mode is zero hits with no error.

Analysis settings live under `settings.analysis` and, like the rest of the mapping, are fixed once
the index has documents. Adding an analyzer requires closing the index (`POST /{index}/_close`,
update, `POST /{index}/_open`) and only affects documents indexed afterwards — which means it is a
reindex in practice.

## Index analyzer versus search analyzer

By default the same analyzer runs at index time and at search time, which is what you want for
`standard` and for stemming: query and document go through the same transformation, so they meet in
the middle.

It is exactly wrong for anything that expands one token into many at index time. Measured on
9.5.3 with an `edge_ngram` analyzer (min 2, max 10) mapped as the field analyzer,
`POST /{index}/_analyze` on the query text `elastic` returns:

```
[el, ela, elas, elast, elasti, elastic]
```

so the query for `elastic` matches every document containing any word starting with `el`. The fix
is one line in the mapping:

```json
{ "name": { "type": "text", "analyzer": "autocomplete", "search_analyzer": "standard" } }
```

Rule of thumb: an analyzer that *adds* tokens (ngrams, index-time synonyms, shingles) belongs at
index time only. An analyzer that *normalises* tokens (lowercase, asciifolding, stemming) belongs
on both sides.

Two more asymmetries worth knowing:

- `multi_match` with `type: cross_fields` requires every listed field to use the same analyzer; it
  blends term statistics across fields and cannot do that when the term streams differ. Mixing
  `english` on one field and `standard` on another silently degrades it to per-field behaviour.
- Stop-word removal at index time makes phrase queries containing those words unmatchable, because
  positions shift. Prefer keeping stop words and letting BM25 discount them.

## Autocomplete without breaking search

Three mechanisms, in order of preference:

1. **`search_as_you_type` field type.** Generates the sub-fields (`._2gram`, `._3gram`,
   `._index_prefix`) and the right search analyzer for you. Query it with
   `multi_match` / `bool_prefix`. Start here.
2. **`edge_ngram` at index time with `search_analyzer: standard`.** More control over gram sizes;
   needs `index.max_ngram_diff` raised when `max_gram - min_gram > 1`. Storage grows with the gram
   range, so cap `max_gram` at the length where a prefix stops being ambiguous (10–15 characters).
3. **`match_bool_prefix` on an ordinary `text` field.** No extra storage; the last term becomes a
   prefix query, which is a term-dictionary scan. Fine for small indices, not for large ones.

`completion` (the suggester) is a fourth mechanism with different semantics: it is an in-memory FST
of curated suggestions, not a search over documents. Use it for a fixed suggestion list, not for
"search my catalogue as I type".

Never solve autocomplete with `wildcard: "*term*"`. A leading `*` cannot use the term dictionary
and forces a scan of every term in the field.

## Synonyms

Prefer search-time synonyms. They can be changed without reindexing and they keep the index
statistics honest; index-time synonyms bake the expansion into the postings, inflate term
frequencies and require a reindex for every edit.

Use `synonym_graph` rather than `synonym`: it handles multi-word synonyms correctly by emitting a
graph rather than overlapping tokens. Place it after `lowercase` in the filter chain and make sure
the synonym file's terms are written in the form the earlier filters produce (a stemmer before the
synonym filter will have already changed the token).

The synonyms API (`PUT /_synonyms/{set}`) stores sets in a system index and reloads analyzers on
change, which is the manageable option for a set that product owners edit. A file under `config/`
requires a rolling restart or a reload call on every node.

Equivalent (`a, b, c`) versus explicit (`a, b => c`) matters: explicit rules are directional and are
the right form when the target term is the canonical one and the sources should not match each
other.

## Language handling

- One analyzer per language, one field per language (`title.en`, `title.de`), and query the field
  matching the user's language. A single `standard` analyzer across mixed-language content stems
  nothing and matches badly in every language.
- The built-in language analyzers (`english`, `german`, ...) bundle a stemmer, a stop-word list and
  a possessive filter. `english` stems aggressively; for a product catalogue `light_english` (or a
  `minimal_english` stemmer) usually ranks better because it does not conflate distinct words.
- CJK needs a real tokenizer. `standard` splits Chinese into single characters, which produces high
  recall and terrible precision. Use the ICU or SmartCN plugin, or the `cjk` bigram analyzer.
- `asciifolding` makes `café` match `cafe`. Add `preserve_original: true` if the exact-accent form
  should still rank higher.

## Normalizers for keyword fields

A `keyword` field cannot have an analyzer, but it can have a `normalizer` — a chain restricted to
character filters and a few token filters (`lowercase`, `asciifolding`, `trim`) that produces
exactly one token.

```json
{ "settings": { "analysis": { "normalizer": { "lc": { "filter": ["lowercase", "asciifolding"] } } } },
  "mappings": { "properties": { "brand": { "type": "keyword", "normalizer": "lc" } } } }
```

This is the correct fix for "the filter works for `Nike` but not `nike`". Lower-casing in the
application does not work, because the query term is not normalised on the way in unless the field
has a normalizer.

## Debugging analysis

`POST /{index}/_analyze` is the first call in any "why does this not match" investigation, and it
takes three useful shapes:

```json
{ "field": "title", "text": "Quick Brown Fox" }                       // what the mapping does
{ "analyzer": "english", "text": "running shoes" }                    // try an analyzer
{ "tokenizer": "standard", "filter": ["lowercase", "my_syn"], "text": "..." }  // try a chain
```

Add `"explain": true` to see the token stream after each stage, which is how you find out that the
stemmer ran before the synonym filter.

`GET /{index}/_termvectors/{id}?fields=title` shows the terms actually stored for one document,
which settles arguments about whether the problem is at index time or query time.

<!-- sources: elastic-agent-skills, clawic-elasticsearch, elastic-docs -->
