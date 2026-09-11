# MCP protocol model

Verified against: MCP specification revision 2026-07-28 (`schema/2026-07-28/schema.ts`,
`LATEST_PROTOCOL_VERSION = "2026-07-28"`).

## Contents

- Revisions and what a version gate means
- The three server primitives
- Statelessness and the request envelope
- `resultType` and the two result shapes
- `server/discover`
- Version negotiation and the two eras
- Error codes
- Cancellation and progress
- Multi round-trip requests
- Caching hints
- Deprecated features registry

## Revisions and what a version gate means

MCP revisions are dates, not semver. Released revisions, oldest first:
`2024-11-05`, `2025-03-26`, `2025-06-18`, `2025-11-25`, `2026-07-28`. A `draft` directory also
exists in the specification repository; it is not a released revision and nothing should target
it. `[verified]`

Two independent numbers matter and are constantly confused:

- the **specification revision** a server claims to speak, and
- the **SDK release** that implements it.

They diverge today. See `references/sdk-versions.md` for the measured matrix. When you write a
version gate in code or in a design doc, say which of the two you mean.

## The three server primitives

| Primitive | Who invokes it | Use it for |
|---|---|---|
| Tool | the model, during a turn | anything the model should be able to *do* |
| Resource | the host application | browsable context the host attaches — files, records, docs |
| Prompt | the user, usually as a slash command | a canned workflow with arguments |

Almost every server needs only tools. The common failure is the opposite one: shipping as a tool
something the model never decides to call, such as `get_server_config` or `list_supported_regions`.
That is reference data the host or the tool description should carry, and every such tool costs
context on every turn. `[official]`

Tools are still the right home for anything that needs the model to choose arguments, even if it
is read-only.

## Statelessness and the request envelope

As of 2026-07-28 there is no `initialize` handshake, no `notifications/initialized`, and no
protocol-level session. Every request is self-contained and carries its own metadata in
`params._meta`: `[verified]`

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {},
      "io.modelcontextprotocol/clientInfo": { "name": "ExampleClient", "version": "1.0.0" }
    }
  }
}
```

`protocolVersion` and `clientCapabilities` are required on every request; omitting either is a
malformed request. Observed against `mcp` 2.2.0 over stdio: `[verified]`

```
{"jsonrpc":"2.0","id":1,"error":{"code":-32602,
 "message":"params._meta is missing the required envelope key(s): io.modelcontextprotocol/clientCapabilities"}}
```

Consequences for server code:

- A server must not rely on anything a previous request over the same connection did.
- List results (`tools/list`, `resources/list`, `prompts/list`) must not vary per connection.
- Anything that needs to survive across calls becomes an explicit server-minted handle passed as
  an ordinary tool argument. See the cross-call state section of `references/tool-design.md`.
- `serverInfo` and `clientInfo` are self-reported and unverified. They are for display, logging
  and debugging; never branch security decisions on them.

## `resultType` and the two result shapes

Every result carries a required `resultType`: `"complete"` for an ordinary result, or
`"input_required"` for the interim result of a multi round-trip request. A client reading a result
from an earlier-revision server that omits the field treats it as `"complete"`. `[verified]`

## `server/discover`

A 2026-07-28 server must implement `server/discover`. It takes no parameters beyond `_meta` and
returns supported versions, capabilities and identity in one round trip: `[verified]`

```json
{"jsonrpc":"2.0","id":1,"result":{
  "resultType":"complete",
  "supportedVersions":["2026-07-28"],
  "capabilities":{"tools":{"listChanged":true},"resources":{"listChanged":true,"subscribe":true}},
  "ttlMs":0,"cacheScope":"private",
  "_meta":{"io.modelcontextprotocol/serverInfo":{"name":"lab","version":"0.1.0"}}}}
```

`instructions` is an optional natural-language field in the same result — the one sanctioned place
to put server-wide guidance for the model, rather than smuggling it into tool descriptions.

## Version negotiation and the two eras

There is no negotiation handshake. A request either names a version the server supports or it is
rejected with `UnsupportedProtocolVersionError` (`-32022`), whose `data.supported` lists what the
server does speak; the client retries with one of those. `[verified]`

The specification calls revisions `2026-07-28` and later **modern** (per-request metadata) and
`2025-11-25` and earlier **legacy** (`initialize` handshake). An implementation that speaks both is
**dual-era**.

A dual-era client probes with `server/discover` first, then:

| Probe outcome | Meaning | Action |
|---|---|---|
| `DiscoverResult` | modern server | pick from `supportedVersions` |
| `UnsupportedProtocolVersionError` | modern, different version | use a version from `data.supported`; do **not** fall back to `initialize` |
| any other error, or no reply | legacy server | fall back to `initialize` |

The fallback must not be keyed to one specific error code: legacy servers answer an unknown
pre-`initialize` method with whatever their implementation happens to return. Measured against the
TypeScript SDK v1 1.30.0 that is `-32601 Method not found`, which is exactly the "any other error"
branch. `[verified]`

The era is decided by the connection's opening message and then pinned. Observed against `mcp`
2.2.0: after a legacy `initialize`, a modern-envelope request on the same connection is refused.
`[verified]`

```
{"jsonrpc":"2.0","id":2,"error":{"code":-32600,
 "message":"this connection serves the handshake protocol era; requests carrying the 2026-07-28 envelope are not accepted on it"}}
```

Do not try to serve both eras from one hand-rolled dispatcher. Let the SDK own the era decision
(the TypeScript v2 `serveStdio` has a `legacy: 'serve' | 'reject'` option for exactly this) and
keep one set of tool registrations behind it.

## Error codes

2026-07-28 partitions the JSON-RPC server-error range: `[verified]`

| Range | Owner |
|---|---|
| `-32000` … `-32019` | implementation-defined; existing SDK usage grandfathered, no new allocations |
| `-32020` … `-32099` | reserved for the MCP specification |

Specification codes in current use: `-32020` `HeaderMismatch`, `-32021`
`MissingRequiredClientCapability`, `-32022` `UnsupportedProtocolVersion`. Renumbered in this
revision — a server must not emit the old `-32001` / `-32003` / `-32004` values for them.

A resource that does not exist is `-32602` (Invalid params), not `-32002`; `-32002` is accepted by
clients only for backward compatibility. A server must never answer `resources/read` for a missing
resource with an empty `contents` array, because an empty array is ambiguous between "exists and is
empty" and "does not exist".

## Cancellation and progress

Cancellation is a `notifications/cancelled` notification naming the request id. The server should
stop as soon as practical and must send nothing further for that request. On Streamable HTTP,
closing the response stream is itself an unambiguous cancellation. `[official]`

`notifications/progress` and `notifications/message` are request-scoped: they travel on the
response stream of the request they relate to, not on any shared channel. A server must not emit
`notifications/message` for a request that did not ask for logging via
`_meta` `io.modelcontextprotocol/logLevel` — and that field is itself deprecated along with the
Logging feature.

## Multi round-trip requests

Server-initiated requests are gone. When a server needs more information mid-request it returns an
`InputRequiredResult` (`resultType: "input_required"`) whose `inputRequests` field carries what it
needs; the client retries the *original* request with `inputResponses`. This replaces
`roots/list`, `sampling/createMessage` and `elicitation/create` as server-to-client calls.
`[official]`

Practical consequence: a server that needs user input cannot block inside a handler. It must be
able to reconstruct its position from the retried request — encode whatever it needs in
`requestState` rather than parking state in memory keyed by connection.

## Caching hints

Results of `tools/list`, `prompts/list`, `resources/list`, `resources/read`,
`resources/templates/list` and `server/discover` carry two required fields: `[verified]`

- `ttlMs` — freshness hint in milliseconds, must be `>= 0`. `0` means immediately stale. Absent is
  treated as `0`.
- `cacheScope` — `"public"` if shared intermediaries may cache the response, `"private"` if the
  payload is caller-specific. A private response must never be reused across authorization
  contexts.

If a list varies with the caller's token, it is `"private"`. Getting this wrong is a cross-tenant
data leak through an intermediary cache, not a performance bug. Servers should also return
`tools/list` in a deterministic order so clients and prompt caches can actually hit.

## Deprecated features registry

`docs/specification/2026-07-28/deprecated.mdx` is the authoritative list. Currently deprecated,
with a minimum twelve-month window before removal becomes possible: `[verified]`

| Feature | Deprecated in | Migrate to |
|---|---|---|
| HTTP+SSE transport | `2025-03-26` | Streamable HTTP |
| Roots | `2026-07-28` | directories or files as tool parameters, resource URIs, or server configuration |
| Sampling | `2026-07-28` | call an LLM provider API directly from the server |
| Logging (`logging/setLevel`, `notifications/message`) | `2026-07-28` | stderr on stdio; OpenTelemetry for observability |
| OAuth Dynamic Client Registration | `2026-07-28` | Client ID Metadata Documents |
| `includeContext: "thisServer"` / `"allServers"` | `2025-11-25` | omit, or `"none"` |

Nothing has been removed under the policy yet, so the deprecated surfaces still work. That is why
so much published guidance still teaches them — being functional is not the same as being the
right thing to build now.

<!-- sources: mcp-spec, mcp-python-sdk, mcp-typescript-sdk, anthropic-mcp-server-dev -->
