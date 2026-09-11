# Tool results: size, shape and paging

Verified against: MCP specification revision 2026-07-28; `mcp` 2.2.0; `@modelcontextprotocol/sdk`
1.30.0.

## Contents

- Result size is the server's problem
- A truncation contract
- Pagination is an opaque cursor
- Content block types
- `resource_link` versus embedding
- Response format switches
- Caching fields on list results
- A review checklist for results

## Result size is the server's problem

A tool result is consumed by a model with a finite context window, and the client has no way to ask
for less after the fact. A server that returns the upstream API's full response has moved its
performance problem into the caller's context and made every subsequent turn worse.

Two separate mistakes hide behind "the answers get truncated":

- The tool returns everything and *something downstream* truncates — silently, mid-JSON, with no
  marker. The model then reasons over a mutilated payload as if it were complete.
- The tool returns a single 40k-item array because the handler read an index file and stringified
  it. The call succeeds and the turn is unusable.

Both are fixed on the server, by budgeting the response.

## A truncation contract

Pick an explicit character budget per tool and hold to it. Around 25,000 characters is a workable
default for a text result. When a result exceeds it: `[official]`

1. Cut the data, not the structure — halve the number of items rather than slicing the string.
2. Set an explicit marker in the payload (`"truncated": true`) *and* say so in the text.
3. Say what to do about it, naming the parameter that narrows the result.

```
Showing 10 of 847 notes (truncated). Narrow with query= or raise limit= up to 50.
```

The last line matters more than it looks: it converts a dead end into the model's next action. A
bare truncated blob makes the model guess.

## Pagination is an opaque cursor

At protocol level, `tools/list`, `resources/list`, `resources/templates/list` and `prompts/list`
page with an opaque `nextCursor` string. The rules: `[verified]`

- Page size is the server's choice; a client must not assume a fixed size.
- A missing `nextCursor` means the end. An **empty string is a valid cursor** and must not be read
  as the end.
- Clients must treat cursors as opaque — no parsing, no arithmetic, no inference from the value.
- Cursors should be stable, and an invalid cursor is `-32602`.

For your own tools' domain paging, the same cursor discipline is the safer default. A
`total`/`offset`/`has_more` envelope appears in a lot of published guidance and is fine as
*additional* information inside `structuredContent`, but it must not replace the opaque cursor on
the protocol list methods, and offsets over a mutating collection give the model duplicated and
skipped rows.

Whatever you choose, state the page size in the tool description so the model can plan.

## Content block types

| Type | Shape | Use for |
|---|---|---|
| `text` | `{ type: "text", text }` | the default |
| `image` | `{ type: "image", data: <base64>, mimeType }` | screenshots, charts |
| `audio` | `{ type: "audio", data: <base64>, mimeType }` | recordings, speech |
| `resource_link` | `{ type: "resource_link", uri, name?, description? }` | a pointer the client may fetch later |
| `resource` | `{ type: "resource", resource: { uri, text \| blob, mimeType } }` | inline the full content |

A result may carry several blocks of different types. Binary payloads must be base64 with a correct
MIME type. `[official]`

## `resource_link` versus embedding

Return a `resource_link` when the payload is large or when the client may not need it — the client
decides whether to spend the context. Embed when it is small and always needed.

A `resource_link` is only useful if the URI is actually readable through `resources/read` on this
server. Handing back a link to a URI the server does not serve is worse than returning nothing,
because the model will try.

## Response format switches

A per-tool `response_format` enum (`"markdown"` default, `"json"` for machine consumption) lets the
caller control verbosity without a second tool. Markdown for reading: headers, lists, human dates,
display names with ids in parentheses, no verbose metadata. JSON for processing: every field,
stable names. `[official]`

This is worth the parameter only when both audiences are real. A single-format tool with a tight
schema beats two formats nobody switches.

## Caching fields on list results

`tools/list`, `prompts/list`, `resources/list`, `resources/read`, `resources/templates/list` and
`server/discover` results must carry `ttlMs` (`>= 0`, milliseconds, `0` = immediately stale) and
`cacheScope` (`"public"` or `"private"`). `[verified]`

The SDKs fill these in with conservative defaults — `mcp` 2.2.0 emits `"ttlMs":0` and
`"cacheScope":"private"` unless told otherwise, which is correct but gives up all caching. Set
them deliberately:

- If the list is identical for every caller, `"public"` with a real TTL.
- If the list depends on the caller's token, `"private"`. A private response must never be reused
  across authorization contexts; marking a per-tenant list `"public"` is a cross-tenant leak
  through a shared intermediary cache.
- The same `cacheScope` must apply to every page of one list.

Also return `tools/list` in a deterministic order. A list that reshuffles defeats both the client's
cache and the model's prompt cache, for no benefit.

A cache key is the method plus its parameters — including the pagination `cursor`. Results of a
request carrying `inputResponses` or `requestState` must never be cached at all, because those are
by definition one specific round trip. When a client needs a consistent snapshot of a whole list it
re-fetches from the first page; if a cursor stops working mid-walk it discards every cached page
and starts over. `[official]`

`ttlMs` is a freshness hint, not a polling interval. A client is expected to check freshness when
it next needs the data, not to wake up and re-fetch on a timer. Setting a small non-zero TTL to
"keep clients current" produces load without producing currency.

## A review checklist for results

- [ ] Every tool that can return a collection has a `limit` with a stated maximum, and a cursor.
- [ ] No handler stringifies an entire upstream response or index file.
- [ ] Truncation is marked in the payload *and* stated in the text, with the narrowing parameter
      named.
- [ ] The page size appears in the tool description.
- [ ] An empty-string cursor is handled as a valid cursor, not as the end of results.
- [ ] `resource_link` URIs are actually readable through `resources/read` on this server.
- [ ] `cacheScope` is `"private"` for anything that varies by caller, and the same value is used
      for every page of a list.
- [ ] `tools/list` order is deterministic.

<!-- sources: mcp-spec, anthropic-mcp-builder, anthropic-mcp-server-dev, microsoft-mcp-builder, mcp-python-sdk -->
