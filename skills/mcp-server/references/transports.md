# Transports: stdio and Streamable HTTP

Verified against: MCP specification revision 2026-07-28; `mcp` 2.2.0;
`@modelcontextprotocol/sdk` 1.30.0; `@modelcontextprotocol/server` 2.0.0; Node v26.7.0.

## Contents

- Choosing
- stdio: the framing rule
- What actually happens when you log to stdout
- stdio: shutdown and restart
- Streamable HTTP: one endpoint
- Streamable HTTP: required request metadata headers
- Streamable HTTP: Origin, binding and the removed GET endpoint
- Server-to-client notifications
- The deprecated HTTP+SSE transport
- Old patterns

## Choosing

| | stdio | Streamable HTTP |
|---|---|---|
| Who runs it | the client, as a subprocess | you, as a service |
| Reach | the user's machine only | anyone with the URL |
| Auth | environment variables, OS keychain | OAuth 2.1 resource server |
| Updates | the user reinstalls | you deploy |

Default to Streamable HTTP for anything wrapping a network API: one deployment serves everyone,
you control upgrades, and OAuth works properly because there is a real endpoint to redirect back
to. Choose stdio when the server must touch the user's machine — local files, a desktop
application, a localhost service — or for a prototype. `[official]`

A stdio server that needs OAuth is a warning sign: the browser-redirect-to-localhost dance breaks
in headless environments, every user repeats it, and there is no central revocation.

## stdio: the framing rule

One newline-delimited JSON-RPC message per line, no embedded newlines. Then the rule that breaks
more servers than anything else in MCP: `[verified]`

- The server **must not write anything to stdout that is not a valid MCP message.**
- The server **may** write arbitrary UTF-8 to stderr for any logging purpose, and the client must
  not treat stderr output as an error signal.
- The server must not write JSON-RPC *requests* to stdout; server-to-client asks travel as
  `InputRequiredResult` replies.

stdout is the wire. Every `print`, `console.log`, progress bar, dependency warning and banner from
a library you imported is a frame on that wire.

## What actually happens when you log to stdout

Three measured outcomes, because the answer is not "it always breaks": `[verified]`

1. **`mcp` 2.2.0 protects you.** Its stdio transport claims file descriptor 1 and points it at
   stderr (`os.dup(2)`), serving the real wire from a private duplicate. A `print()` inside a tool
   comes out on stderr and the frames stay clean. The source describes this as best-effort: when
   descriptors cannot be duplicated it serves `sys.stdout`'s buffer in place "exactly as v1 did",
   and corruption is possible again.
2. **The TypeScript SDKs do not.** In both 1.30.0 and 2.0.0, `console.log("DEBUG: ...")` inside a
   handler appears as a bare line in the protocol stream. A lenient client skips it — Inspector
   2.6.0 still returned the right result — so this can sit in production looking harmless.
3. **A write without a trailing newline is fatal.** `process.stdout.write("working... ")` before
   returning produces this on the wire:

```
{"result":{"protocolVersion":"2025-11-25",...},"jsonrpc":"2.0","id":1}
working... {"result":{"content":[{"type":"text","text":"done"}]},"jsonrpc":"2.0","id":2}
```

The second line is no longer valid JSON, so the client never sees that response:

```
$ npx @modelcontextprotocol/inspector --cli node server.mjs --method tools/call --tool-name partial_write
{"error":{"code":"error","message":"Request timed out"}}
```

That is the mechanism behind "the server randomly hangs": one un-newlined write, one lost
response, one client-side timeout. Do not rely on the Python guard and do not rely on client
leniency. Route logging to stderr explicitly, and in .NET set the log threshold to stderr before
anything else runs. `[official]`

## stdio: shutdown and restart

The portable graceful-shutdown signal is end-of-file on stdin: the client closes the input stream
and waits, escalating to `SIGTERM` and then `SIGKILL` if the process does not exit. A server should
exit promptly on stdin EOF — honouring it is what keeps clients from having to kill you.
`[official]`

Because the protocol is stateless, an unexpected exit costs only the in-flight requests; the client
restarts the process and retries. Any `subscriptions/listen` stream must be re-established after
restart.

## Streamable HTTP: one endpoint

A single HTTP endpoint path (conventionally `/mcp`) handles everything. Every client message is a
new HTTP POST whose body is exactly one JSON-RPC request or notification; clients must send an
`Accept` header listing both `application/json` and `text/event-stream`, and the server must
support replying either way. `[official]`

As of 2026-07-28 there is no `Mcp-Session-Id` header and no protocol-level session. Also removed:
SSE stream resumability — there are no event ids and no `Last-Event-ID`, so a broken stream loses
the in-flight request and the client must re-issue it as a *new* request with a new id.

## Streamable HTTP: required request metadata headers

The transport mirrors selected body fields into headers so intermediaries can route without
parsing the body. All three are required for compliance: `[verified]`

| Header | Source | Required on |
|---|---|---|
| `MCP-Protocol-Version` | `_meta` `io.modelcontextprotocol/protocolVersion` | every POST |
| `Mcp-Method` | `method` | every request |
| `Mcp-Name` | `params.name` or `params.uri` | `tools/call`, `resources/read`, `prompts/get` |

A mismatch between header and body is `-32020` with HTTP `400`. Measured against `mcp` 2.2.0:

```
# no Mcp-Method
{"jsonrpc":"2.0","id":1,"error":{"code":-32020,"message":"mcp-method header does not match the request body's method"}}
# tools/call with Mcp-Method but no Mcp-Name
{"jsonrpc":"2.0","id":2,"error":{"code":-32020,"message":"mcp-name header does not match the request body's 'name' parameter"}}
```

Other status mappings a server must honour: an unsupported protocol version is `400` with
`UnsupportedProtocolVersionError`; an unimplemented method is `404` with `-32601`, whose JSON-RPC
body is what distinguishes it from a plain `404` from a legacy server that does not host the modern
endpoint. `[official]`

The `MCP-Protocol-Version` header is also what selects the era in practice. Measured against `mcp`
2.2.0: without it, the same `mcp.run("streamable-http")` deployment serves the legacy session-based
implementation, replies `Bad Request: Missing session ID`, and issues `mcp-session-id` after an
`initialize`. With `MCP-Protocol-Version: 2026-07-28` it serves the modern stateless path and emits
no session header at all. `[verified]`

## Streamable HTTP: Origin, binding and the removed GET endpoint

- The server must validate `Origin` on every incoming connection and reject an invalid one.
  `mcp` 2.2.0 does this by default — a request with `Origin: https://evil.example` returns `403`
  with no configuration. This is the DNS-rebinding defence; do not disable it to make a browser
  demo work. `[verified]`
- When running locally, bind loopback, not `0.0.0.0`. Several web frameworks default to all
  interfaces when no host is given, and publishing a container port bypasses a `127.0.0.1` bind
  made *inside* the container. Check both. `[official]`
- `GET` on the MCP endpoint returns `405` — the GET/SSE listening endpoint no longer exists in the
  modern era. Measured against `mcp` 2.2.0. `[verified]`

## Server-to-client notifications

`resources/subscribe` / `resources/unsubscribe` and the GET SSE stream are replaced by
`subscriptions/listen`: one long-lived POST-response stream the client opts into by naming the
notification types it wants (`toolsListChanged`, `promptsListChanged`, `resourcesListChanged`,
`resourceSubscriptions`). The server acknowledges and tags each notification with
`io.modelcontextprotocol/subscriptionId` in `_meta`. `[official]`

Request-scoped notifications are different and do not use that stream: `notifications/progress` and
`notifications/message` flow on the response stream of the request they belong to.

## The deprecated HTTP+SSE transport

The two-endpoint design — a `GET /sse` stream plus a separate `POST /messages` — has been
deprecated since revision `2025-03-26` and was formally reclassified as Deprecated under the
feature-lifecycle policy in `2026-07-28`, with Streamable HTTP as the migration path. `[verified]`

Recognise it in a config or a code base by the endpoint pair, by `type: "sse"` in a client config,
or by `SSEServerTransport` in the source. The TypeScript v2 SDK removed the SSE and WebSocket
transports outright, so migrating off it is also a prerequisite for that upgrade. `[official]`

New servers: single Streamable HTTP endpoint, no exceptions.

## Old patterns

<details>
<summary>Session-based Streamable HTTP (2025-11-25 and earlier)</summary>

Before 2026-07-28, a Streamable HTTP server minted an `Mcp-Session-Id` on `initialize`, clients
echoed it on every later request, list results could vary per session, and browser clients had to
have that header exposed through CORS. Stream resumability existed via SSE event ids and
`Last-Event-ID`.

All of it is gone in the modern era. If you still need to serve handshake-era clients, keep the
legacy path behind an SDK option (TypeScript v2 `serveStdio`'s `legacy` setting; the Python
`streamable-http` app selecting on `MCP-Protocol-Version`) rather than writing session code of your
own, and treat the session id as a correlation token only — never as an authorization decision.

</details>

<!-- sources: mcp-spec, mcp-python-sdk, mcp-typescript-sdk, awesome-copilot-mcp, anthropic-mcp-server-dev, cloudflare-agents-mcp, mcp-inspector -->
