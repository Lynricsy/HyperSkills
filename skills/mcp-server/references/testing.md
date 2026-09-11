# Testing and releasing an MCP server

Verified against: `@modelcontextprotocol/inspector` 2.6.0; `mcp` 2.2.0;
`@modelcontextprotocol/sdk` 1.30.0; `@modelcontextprotocol/server` 2.0.0; Node v26.7.0.

## Contents

- Three layers of testing
- The Inspector, headless
- Driving the wire directly
- Contract tests worth keeping
- Failure paths that exist under 2026-07-28
- Pre-release inventory parity
- Verifying the install string
- Does a model actually succeed with these tools

## Three layers of testing

| Layer | Question | Tool |
|---|---|---|
| Wire | is it a conforming MCP server | Inspector CLI, raw JSON-RPC |
| Contract | does each tool honour its own schema and error contract | your test runner, in-process transport |
| Usability | can a model solve real tasks with this tool set | an eval set |

All three are necessary and they fail differently. A server can be perfectly conforming and
unusable, or produce great answers while corrupting its own protocol stream.

## The Inspector, headless

Use the `--cli` mode. A bare `npx @modelcontextprotocol/inspector` launches the UI and tries to
open a browser, which hangs in a headless environment. `[verified]`

```bash
npx @modelcontextprotocol/inspector --cli node dist/server.js --method tools/list
npx @modelcontextprotocol/inspector --cli node dist/server.js \
  --method tools/call --tool-name notes_search_notes --tool-arg query=invoice limit=5
npx @modelcontextprotocol/inspector --cli uv run server.py --method resources/list
```

It prints the raw result as JSON, which makes it the fastest way to see what the model will see —
including whether a tool has a `description` at all.

Do not use it to check the version: `--version` is not supported and falls through to the UI. Use
`npm view @modelcontextprotocol/inspector version`.

Worth knowing about its limits: the CLI is lenient about garbage on stdout and will skip an
unparseable line, so a server that logs to stdout can pass an Inspector check and still break a
stricter client. It does time out — measured, `{"error":{"code":"error","message":"Request timed
out"}}` — when a write without a trailing newline corrupts the response frame. `[verified]`

## Driving the wire directly

When you need to see exact bytes — which `_meta` keys are required, what error code comes back,
whether `server/discover` is implemented — send JSON-RPC lines to the process yourself. Under
2026-07-28 every request needs the envelope:

```bash
printf '%s\n' \
 '{"jsonrpc":"2.0","id":1,"method":"server/discover","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}}}}' \
 '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}}}}' \
 | uv run server.py
```

Read stdout and stderr separately. Anything on stdout that is not a JSON-RPC frame is a bug you
have just found; anything on stderr is fine by design.

For HTTP, remember the required headers or you get `-32020`:

```bash
curl -s -X POST http://127.0.0.1:8931/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H 'MCP-Protocol-Version: 2026-07-28' \
  -H 'Mcp-Method: tools/list' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}}}}'
```

`tools/call` also needs `Mcp-Name: <tool>`.

## Contract tests worth keeping

Test through an in-memory transport where the SDK offers one, so the test exercises real
serialisation without spawning a process. What earns a permanent test:

- **Every tool's declared schema rejects what it says it rejects.** One case per genuine boundary —
  out-of-range `limit`, unknown enum value, missing required field — not one row per parameter.
- **Each documented tool execution error is reachable and says the next action.** Assert that the
  result has `isError: true` and that the text names the recovery tool or parameter. This is the
  contract a model consumes, so it is observable behaviour, not implementation detail.
- **A tool with an `outputSchema` returns `structuredContent` that validates against it.**
- **Pagination terminates and does not skip.** Walk the cursor to exhaustion over a fixture with
  more items than one page and assert the union equals the fixture. Include the empty-string cursor
  case, because treating `""` as the end is a real bug.
- **Path containment rejects an escape.** `../../etc/passwd`, an absolute path, and a symlink out of
  the root.

What does not earn a test: that a tool is registered, that a description string equals a literal,
that the SDK serialises JSON-RPC. Those pin the implementation and break on every refactor.

## Failure paths that exist under 2026-07-28

Negative-path checklists written for earlier revisions test things that no longer exist — "request
before initialization completes", "repeated initialization". The current equivalents, all measured:
`[verified]`

| Probe | Expected |
|---|---|
| request with `_meta` missing `io.modelcontextprotocol/clientCapabilities` | `-32602`, message naming the missing envelope key |
| request naming a version the server does not support | `-32022` with `data.supported` |
| HTTP POST without `Mcp-Method`, or with one that disagrees with the body | `-32020`, HTTP `400` |
| `tools/call` over HTTP without `Mcp-Name` | `-32020` |
| HTTP request with a foreign `Origin` | `403` |
| `GET` on the MCP endpoint | `405` |
| unknown method | `-32601` (HTTP `404` with a JSON-RPC body) |
| `resources/read` for a missing resource | `-32602`, never an empty `contents` array |
| call against an expired handle | `isError: true` saying so, with the tool to call instead |

Also probe the era boundary if you claim dual-era support: a legacy `initialize` followed by a
modern-envelope request on the same connection should be refused, not silently served.

## Pre-release inventory parity

The registrations in the source, the tools the running server advertises, any generated catalog or
documentation, and the README must all agree. Compare by stable identifier — tool name — not by
eyeballing counts. `[official]`

```bash
# what the running server advertises
npx @modelcontextprotocol/inspector --cli node dist/server.js --method tools/list \
  | jq -r '.tools[].name' | sort > /tmp/runtime.txt
# what the source registers
grep -oE 'registerTool\("[^"]+"' src/*.ts | sed 's/.*"\(.*\)"/\1/' | sort > /tmp/source.txt
diff /tmp/source.txt /tmp/runtime.txt
```

Regenerate any derived catalog with the repository's own build command and fail on an unexplained
working-tree diff. A tool that exists in the source but not at runtime usually means a missing
registration call or a conditional that did not fire — the kind of bug that only shows up when a
user asks for the missing feature.

Run the whole discovery pass in **one** live session. Splitting it across separate one-shot
processes tests several fresh connections, not one working server.

## Verifying the install string

An install command that has only been read is unverified. Install to a temporary directory outside
the checkout, from the published artefact, and re-run discovery there:

```bash
rm -rf /tmp/verify && mkdir /tmp/verify && cd /tmp/verify
npm pack ../path/to/server && npm i ./notes-mcp-*.tgz
npx @modelcontextprotocol/inspector --cli ./node_modules/.bin/notes-mcp --method tools/list
```

This catches missing files in the package, a wrong `bin` entry, and dependencies that were only
present in the development tree.

## Does a model actually succeed with these tools

Wire conformance does not tell you whether the tool set is usable. Build a small eval set of
realistic tasks and check whether a model completes them. What makes such a question useful:
`[official]`

- **Verifiable by string comparison.** Pin the answer format inside the question ("answer with the
  note id", "use YYYY-MM-DD") so grading is mechanical.
- **Not solvable by keyword search.** Paraphrase the target content; if the question quotes it, you
  are testing search, not the tool set.
- **Multi-step.** A question answerable by one obvious call tests nothing about tool composition.
- **Stable.** Target closed or historical data. Never counts that drift — reactions, member totals,
  "latest".
- **Read-only and independent.** Each question stands alone and mutates nothing.

Do not let the current tool set constrain the questions. A question the model cannot answer because
no tool exposes the needed data is the most valuable result the exercise produces.

<!-- sources: mcp-inspector, awesome-copilot-mcp, anthropic-mcp-builder, mcp-spec, mcp-python-sdk, mcp-typescript-sdk -->
