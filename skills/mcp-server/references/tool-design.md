# Tool design

Verified against: MCP specification revision 2026-07-28; `mcp` 2.2.0; `@modelcontextprotocol/sdk`
1.30.0 and `@modelcontextprotocol/server` 2.0.0.

## Contents

- The tool list is prompt text
- Names
- One tool per operation
- Descriptions
- Parameter schemas
- Annotations
- Structured output
- How many tools
- Cross-call state: server-minted handles
- Tools you should not have written

## The tool list is prompt text

Every field of every tool in `tools/list` lands in the model's context on every turn. That makes
tool definitions prompt engineering with a schema attached, and it puts a price on each one. Thirty
tools with rich schemas can consume several thousand tokens before the conversation starts.
`[official]`

The corollary is that a tool the model cannot choose correctly from its definition alone is
broken, no matter how well the handler works.

## Names

The specification's constraints are loose: 1–128 characters, case-sensitive, only ASCII letters,
digits, `_`, `-` and `.`, unique within the server. `[verified]` Some hosts impose a tighter cap
(64 characters is common), so stay well inside.

Uniqueness is per server, and clients aggregating several servers hit collisions — two servers each
exposing `search` is the canonical case. Prefix with the service: `notes_search_notes`, not
`search`. Do not rely on the client disambiguating for you, and do not rely on `serverInfo.name`
being unique either; it is self-reported and unverified.

Use one casing convention across the whole server and start with a verb: `notes_create_note`,
`notes_list_notes`, `notes_delete_note`.

## One tool per operation

The single most common structural defect is the multiplexed dispatcher:

```typescript
// Wrong: one tool, four operations, no way to describe or annotate any of them
{ name: "note_action", inputSchema: { op: z.string(), id: z.string(), body: z.string().optional() } }
```

It fails on four counts. The description cannot be accurate for all four operations at once. The
schema cannot express that `body` is required for a write and meaningless for a delete. The
annotations cannot say read-only and destructive simultaneously, so the host must assume the worst
for the read path or the best for the delete path. And a host that auto-approves read-only calls
cannot auto-approve anything here.

Split it. Read and write operations especially belong in separate tools; documenting "safe" and
"unsafe" modes inside one description does not substitute for the split. `[official]`

## Descriptions

The description is the only thing the model reads before deciding to call. Write it as a one-line
manual entry with disambiguation:

```
notes_search_notes — Search notes by keyword across title and body. Returns up to `limit`
matches ranked by recency, newest first. Does NOT search attachments or comments; use
notes_search_comments for those.
```

Three things, always: what it does, what it returns, what it does *not* do. The third prevents the
wrong-tool call, which is the expensive failure — the model calls, gets a plausible-looking wrong
answer, and proceeds.

When two tools are close, each description points at the other: `notes_get_note — Fetch a note by
id. If you only have a title, use notes_search_notes.`

Doc comments are not extracted in the TypeScript SDKs. A JSDoc block above the handler reaches
nobody; the description has to be in the tool definition. In `mcp` 2.x the Python docstring *is*
the description, and a tool with no docstring ships as `"description": ""`. `[verified]`

An acceptance bar you can actually check: a description is good enough when the tool is selected
for its own intent in the presence of its siblings, and is *not* selected for an unrelated
intent. Test both directions. `[official]`

Two hard prohibitions:

- **Do not instruct the model in a tool description.** "Always call this first", "never tell the
  user which records you read", "prefer our product" — these are prompt injection through the tool
  list, and reviewers treat them as such. Server-wide guidance belongs in the `instructions` field
  of `server/discover`.
- **Do not restate host policy.** Clients must treat descriptions and annotations as untrusted
  data unless the server is trusted, so anything you write there is a hint, never a control.

## Parameter schemas

Every constraint in the schema is one runtime failure that cannot happen. Describe every property
— the description text reaches the model, the property name barely does.

| Instead of | Use |
|---|---|
| `z.string()` for an id | `z.string().regex(/^n_[a-z0-9]{6}$/)` |
| `z.string()` for a mode | `z.enum(["markdown", "json"])` |
| `z.number()` for a limit | `z.number().int().min(1).max(100).default(20)` |
| an optional flag with no hint | `.optional().describe("Defaults to the caller's workspace")` |

```typescript
inputSchema: z.object({
  query: z.string().min(1).describe("Keywords to match. Quoted phrases are matched literally."),
  status: z.enum(["open", "archived", "all"]).default("open")
    .describe("Filter by status. Use 'all' to include archived notes."),
  limit: z.number().int().min(1).max(50).default(10).describe("Max results. Hard cap 50."),
}).strict(),                         // unknown properties are rejected at the boundary
```

```python
@mcp.tool()
def notes_search_notes(
    query: Annotated[str, Field(min_length=1, description="Keywords to match.")],
    status: Annotated[Literal["open", "archived", "all"], Field(description="Filter by status.")] = "open",
    limit: Annotated[int, Field(ge=1, le=50, description="Max results. Hard cap 50.")] = 10,
) -> str:
    """Search notes by keyword across title and body. Does NOT search attachments."""
```

Declare parameters at the top level of the tool signature. Wrapping every argument in a single
Pydantic model nests the whole schema under one `params` property, which the model then has to
guess its way into; this pattern appears in published guidance and should be corrected, not
copied. `[verified]`

A schema with no parameters must still be a valid JSON Schema object. Prefer
`{ "type": "object", "additionalProperties": false }`, which accepts only the empty object.
`[official]`

`inputSchema` and `outputSchema` may use any JSON Schema 2020-12 keyword as of 2026-07-28, but an
external `$ref` pointing at an absolute URI must not be fetched: clients disable remote resolution
by default and reject schemas that fail to validate because of it. Keep every `$ref` internal.
`[official]`

## Annotations

Annotations tell the host how to present and gate the call. They default to the pessimistic
reading, so omitting them costs the user a confirmation dialog on every read. `[official]`

| Annotation | Default when absent | Host behaviour |
|---|---|---|
| `readOnlyHint` | `false` | `true` may be auto-approved |
| `destructiveHint` | `true` | confirmation dialog |
| `idempotentHint` | `false` | `true` may be retried on a transient error |
| `openWorldHint` | `true` | may show a network indicator |

Set them on every tool. Think about the combination rather than copying: a delete is destructive
but idempotent; a purge-with-compaction is neither; a create is neither read-only nor destructive.
Annotations are hints and never a security boundary — enforce the actual authorization in the
handler.

## Structured output

Declare `outputSchema` and return `structuredContent` when the result has a shape. Keep a text
block as well, because not every host reads `structuredContent`:

```typescript
return {
  content: [{ type: "text", text: JSON.stringify(note) }],
  structuredContent: note,
};
```

In `mcp` 2.x the output schema is derived from the return annotation, and a scalar return is
wrapped: a `-> str` tool emits `outputSchema` of `{"result": {"type": "string"}}` and
`structuredContent` of `{"result": "..."}`. Return a `TypedDict` or Pydantic model when you want a
real shape. `[verified]`

## How many tools

| Count | What to do |
|---|---|
| 1–15 | one tool per operation; this is the target |
| 15–30 | still workable; audit for near-duplicates worth merging |
| 30+ | switch to search-and-execute, optionally promoting the 3–5 most-used to dedicated tools |

Search-and-execute is two tools — one that takes a natural-language intent and returns matching
action ids with their parameter schemas, one that runs an action by id. The catalog stays on the
server. Reach for it when wrapping a large API surface, not before. `[official]`

## Cross-call state: server-minted handles

There is no protocol session as of 2026-07-28, so a browser context, a shopping cart or an open
transaction cannot live "on the connection". The sanctioned pattern is an explicit handle:

```jsonc
// → tools/call  { "name": "create_basket", "arguments": {} }
// ← result      structuredContent: { "basket_id": "bsk_a1b2c3" }
// → tools/call  { "name": "add_item", "arguments": { "basket_id": "bsk_a1b2c3", "sku": "..." } }
```

Four rules for handles: `[official]`

- **Authorize on every call.** A handle is a name, not a capability. On an authenticated server,
  re-check the caller against the handle each time. On an unauthenticated server the handle *is* a
  bearer token, so generate it with real entropy and bound its lifetime.
- **Keep it opaque.** A handle that encodes structure invites guessing.
- **State the lifetime in the creating tool's description** ("baskets expire after 24 hours idle"),
  so the model sees it when it decides to create state.
- **Make expiry recoverable.** A call against an unknown or expired handle returns a tool execution
  error saying so, so the model can create a new one instead of looping.

## Tools you should not have written

- Anything the model never chooses: `get_config`, `list_regions`, `health_check`. That is
  reference data for the host, or a line in a description.
- A passthrough that takes a freeform URL or SQL string with no constraint. If you genuinely need
  one, the description must point at the target API's documentation so the model can form valid
  input. `[official]`
- A tool whose only job is to tell the model how to use the other tools. Use `instructions`.

<!-- sources: mcp-spec, anthropic-mcp-server-dev, anthropic-mcp-builder, microsoft-mcp-builder, mcp-python-sdk -->
