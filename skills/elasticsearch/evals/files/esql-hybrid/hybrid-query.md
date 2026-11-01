# Article search: ES|QL hybrid query

Cluster: Elasticsearch 9.5.5 (self-managed, upgraded from 9.3.2 last week), Enterprise licence.
`articles` has `content` (text) and `semantic_content` (semantic_text on the default ELSER
endpoint). About 4 million documents.

This is the query the search API sends. It was written and load-tested on the 9.3 staging cluster,
where it returned results in ~180 ms:

```esql
FROM articles METADATA _score, _id, _index
| FORK ( WHERE MATCH(content, ?q) | SORT _score DESC )
       ( WHERE semantic_content : ?q | SORT _score DESC )
| FUSE
| KEEP _id, title, _score
| LIMIT 10
```

Since the upgrade every call fails with a 400 `verification_exception`. Nothing in the query
changed.

Two more things came up in the review meeting:

1. Platform ops want the query removed from production anyway because "FORK and FUSE are tech
   preview and not covered by support".
2. The EU team wants the same query to also search their remote cluster, i.e.
   `FROM articles, eu:articles METADATA _score, _id, _index`. Someone said FORK cannot be used
   with remote clusters at all.

The ask: why does the query fail on 9.5, is ops right, can the EU change work, and what should
the query look like on 9.5?
