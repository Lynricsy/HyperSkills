---
name: mcp-server
description: "Guides designing and reviewing a Model Context Protocol server: whether a capability is a tool, a resource or a prompt; tool names, schemas and descriptions written for a model; result size and cursor pagination; errors as the model's only recovery hint, where the SDKs disagree about thrown exceptions; stdio versus Streamable HTTP, the stdout framing rule, required MCP headers, deprecated HTTP+SSE; the stateless 2026-07-28 envelope, server/discover, dual-era initialize clients, server-minted handles replacing protocol sessions; OAuth audience binding, token passthrough, least-privilege scope, CIMD over DCR, confused deputy; tool poisoning and injection through tool results. Use when building, reviewing, migrating or publishing an MCP server. Do not use for authoring agent skills (use the skill-authoring skill), operating someone else's MCP server, the host language itself (typescript, python, go, csharp-dotnet skills), or deploying it (containers, aws, azure, gcp, cloudflare skills)."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: task
---

Paths below are relative to this skill's directory.

## Scope

Designing and implementing an MCP server, and reviewing or releasing one: which primitive a
capability belongs to, how tools are named and schema'd, what a result may cost the caller, what an
error says, which transport to speak and how not to corrupt it, how authorization works when the
server is an OAuth resource server, which threats exist because the thing is an MCP server, and how
to verify all of it.

Version-sensitive throughout. The current specification revision is **2026-07-28**, and the
shipping SDKs do not all implement it. Every rule below that depends on the revision carries a
gate, and `references/sdk-versions.md` holds the measured matrix plus the commands to re-measure
it. Treat a claim about "the MCP version" as ambiguous until someone says whether they mean the
specification revision or an SDK release.

Not covered: authoring agent skills. Writing a `SKILL.md`, its frontmatter, references or
evaluations is the `skill-authoring` skill's job, including the draft extension that distributes
skills over MCP.

Not covered: using an MCP server someone else wrote. Adding a published server to an editor,
debugging why it will not connect, or choosing between two products are operator tasks with no
design decisions in them. The one exception in scope is the configuration block **you** publish for
users of **your** server, because that is a deliverable you own.

Not covered: the host language. Idiomatic TypeScript, Python, Go or C# belongs to the `typescript`,
`python`, `go` and `csharp-dotnet` skills; this skill covers the MCP surface those languages
express. SDK API facts appear here only where they were measured, and only where getting them wrong
breaks the protocol.

Not covered: deploying the finished server. Containers, serverless runtimes, cloud networking and
TLS termination belong to the `containers`, `aws`, `azure`, `gcp` and `cloudflare` skills; this
skill stops at the process and its endpoint.

Not covered: auditing a whole codebase or threat surface. `references/threats.md` covers the
threats that exist *because* the component is an MCP server; for a full audit use the
`security-review` skill. Attacking systems, penetration testing and evading detection are out of
scope entirely.

## Core rules

1. **Every field of every tool is prompt text.** `tools/list` enters the model's context on every
   turn, so a tool the model cannot choose correctly from its definition alone is broken no matter
   how well the handler works — and a tool the model never chooses is pure cost.
2. **The description says what it does, what it returns, and what it does not do.** The third part
   prevents the wrong-tool call, which is the expensive failure because it succeeds and returns
   something plausible.
3. **A tool description never instructs the model.** "Always call this first", "do not tell the
   user" and promotional text are prompt injection through the tool list. Server-wide guidance goes
   in the `instructions` field of the `server/discover` result (2026-07-28) — and clients are
   required to treat descriptions and annotations as untrusted anyway.
4. **Describe every parameter, not just the tool.** A bare `z.string()` or an undocumented `mode`
   argument reaches the model as a type with no meaning. Doc comments are not extracted in the
   TypeScript SDKs; a Python tool with no docstring ships as `"description": ""`.
5. **One tool per operation.** A tool dispatching on an `op` string cannot have an accurate
   description, a schema that expresses per-operation requirements, or honest annotations — and it
   forces the host to gate its read path like its delete path.
6. **Set `readOnlyHint`, `destructiveHint`, `idempotentHint` and `openWorldHint` on every tool, and
   enforce nothing with them.** Absent, they default to the pessimistic reading and cost the user a
   confirmation on every read. Present, they are still self-reported hints, so the handler enforces
   the actual restriction.
7. **Budget the result.** Pick a character ceiling per tool, cut items rather than slicing strings,
   mark the payload `truncated`, and name the parameter that narrows it. An unmarked truncation
   makes the model reason over a mutilated payload as if it were complete.
8. **Protocol list pagination is an opaque cursor.** A missing `nextCursor` means the end; an empty
   string is a valid cursor and does not. Clients must not parse cursors, and page size is yours to
   choose — so state it in the description.
9. **Classify every failure before returning it.** Recoverable failures are results with
   `isError: true` and text the model can act on; only request-structure and server faults are
   JSON-RPC errors. Clients are only obliged to show the model the first kind.
10. **Do not rely on throwing.** Measured: `mcp` 2.2.0 discards the exception message and gives the
    model `Error executing tool <name>`; `@modelcontextprotocol/sdk` 1.30.0 and
    `@modelcontextprotocol/server` 2.0.0 forward `Error.message` verbatim, secrets included. Catch,
    decide what the model may know, and construct the result.
11. **Every error ends with the next action.** Naming the tool or parameter that recovers turns a
    dead end into a retry that differs. Without it the model retries identically.
12. **On stdio, stdout is the wire (all revisions).** The server must write nothing to stdout that
    is not a valid MCP message and may write anything to stderr. A write without a trailing newline
    prefixes the next frame, the client loses that response and the call times out — that is the
    mechanism behind "it randomly hangs".
13. **New HTTP servers speak Streamable HTTP on one endpoint.** HTTP+SSE — the `GET /sse` plus
    `POST /messages` pair — has been deprecated since revision `2025-03-26` and was formally
    reclassified as Deprecated in `2026-07-28`.
14. **On Streamable HTTP, `MCP-Protocol-Version`, `Mcp-Method` and — for
    `tools/call`, `resources/read`, `prompts/get` — `Mcp-Name` are required and must match the
    body (2026-07-28).** A mismatch is `-32020` with HTTP `400`. Measured against `mcp` 2.2.0.
15. **Validate `Origin` and bind loopback for local HTTP servers.** This is the DNS-rebinding
    defence. Several frameworks default to all interfaces with no host given, and publishing a
    container port bypasses a `127.0.0.1` bind made inside the container.
16. **There is no protocol session (2026-07-28).** No `initialize`, no
    `notifications/initialized`, no `Mcp-Session-Id`; every request carries
    `io.modelcontextprotocol/protocolVersion` and `io.modelcontextprotocol/clientCapabilities` in
    `_meta`, and omitting either is `-32602`. List results must not vary per connection.
17. **Cross-call state is a server-minted handle passed as a tool argument (2026-07-28).**
    Re-authorize the caller against the handle on every call — a handle is a name, never a
    capability — keep it opaque, bound its lifetime, state that lifetime in the creating tool's
    description, and make expiry a recoverable tool error.
18. **A 2026-07-28 server must implement `server/discover`.** It is also the dual-era probe: a
    client falls back to `initialize` on *any* unrecognised error, so never key that fallback to one
    code. Let the SDK own the era decision rather than writing a dispatcher.
19. **Roots, Sampling and Logging are deprecated (2026-07-28).** Take directories from tool
    parameters, resource URIs or configuration; call an LLM provider directly instead of sampling;
    log to stderr or OpenTelemetry. They still function — the deprecation window is at least twelve
    months — which is why so much current guidance still teaches them.
20. **Validate the token's audience, not just its signature.** A server must reject a token that
    does not name it, or every other service behind the same identity provider holds a key to this
    one. Authorization is per request; there is no session to carry a prior decision.
21. **Never pass the inbound token upstream.** Calling another API makes the server an OAuth client
    to it, with its own separately-issued token. Passthrough defeats audience binding in one hop.
22. **Scope is a blast radius.** Request the narrowest scopes the operation needs, answer a
    shortfall with `403` and a `WWW-Authenticate` challenge naming the required scope, and prefer
    Client ID Metadata Documents over Dynamic Client Registration (deprecated 2026-07-28). A static
    client id fronting DCR for a third-party authorization server is the confused deputy and needs
    per-client consent.
23. **Tool arguments come from a model that has read untrusted content.** Treat them as an
    unauthenticated request body: argv arrays instead of shell strings, `resolve` plus `relative`
    containment instead of a `".."` substring check, and per-tool rate limits inside the server. A
    local server has no sandbox.
24. **A tool that returns content it did not author carries injection into the context.** Label
    foreign content as data with its provenance, return the minimum, and never let fetched text
    decide authorization.
25. **Verify by running it, not by reading it.** `npx @modelcontextprotocol/inspector --cli <cmd>
    --method tools/list` shows what the model will see. A published install string that has only
    been read is unverified.

## Workflows

### Implement a new server

- [ ] Settle the shape first: what it connects to, who installs it, roughly how many operations,
      whether it must touch the user's machine. Answer these before writing code — changing them
      later is a rewrite. Default to Streamable HTTP unless it must be local.
- [ ] Fix the target revision and the SDK in the same sentence, e.g. "specification 2026-07-28 on
      `@modelcontextprotocol/server` 2.0.0". Read `references/sdk-versions.md` and run the
      re-measure commands; do not trust a remembered version.
- [ ] Decide primitives: tools for what the model does, resources for context the host attaches,
      prompts for user-invoked workflows. Reference data is not a tool.
- [ ] Write the tool list on paper first — names, one-line descriptions, parameters. Under ~15
      operations, one tool each; over 30, search-and-execute. `references/tool-design.md`.
- [ ] Implement handlers with tight schemas, explicit annotations, budgeted results, and errors
      constructed in the handler rather than thrown. `references/tool-results.md`,
      `references/errors.md`.
- [ ] Wire the transport, and route all logging to stderr before anything else initialises.
      `references/transports.md`.
- [ ] **Gate:** `npx @modelcontextprotocol/inspector --cli <command> --method tools/list` returns
      every tool with a non-empty `description`, every parameter described, and nothing on stdout
      that is not a JSON-RPC frame.

### Review an existing server

- [ ] Read the live `tools/list`, not only the source — descriptions can change after approval.
- [ ] Read every description as prospective prompt content: imperatives aimed at the model,
      instructions to withhold information from the user, promotional text.
- [ ] Check each tool for the multiplexed-`op` shape, missing parameter descriptions, missing
      annotations, and unbounded results.
- [ ] Trace every tool argument to its sink: shell invocation, path join, SQL, URL fetch.
      `references/threats.md`.
- [ ] Check the error paths: what reaches the model on an exception, and whether each message names
      a next action.
- [ ] Check stdout discipline on stdio, and header, `Origin` and binding discipline on HTTP.
- [ ] **Gate:** every finding is `path:line - finding` with a concrete fix, and the report separates
      findings that block a release from hardening.

### Migrate across a revision

- [ ] Establish both numbers: the revision the client requires, and what the installed SDK build
      actually speaks. Read the exported protocol-version constant and call `server/discover`
      against the running server — in the TypeScript v2 SDK the exported
      `LATEST_PROTOCOL_VERSION` describes the legacy era only and is not the ceiling.
- [ ] List the removed surfaces the code depends on: `initialize`, `Mcp-Session-Id`,
      `resources/subscribe`, the GET SSE endpoint, `ping`, `logging/setLevel`, server-initiated
      requests. `references/protocol-model.md`.
- [ ] Convert per-connection state to server-minted handles before touching the transport; this is
      the part that changes the tool signatures.
- [ ] Do the mechanical package migration separately from the behavioural one, so a failure has one
      cause. For TypeScript that is `npx @modelcontextprotocol/codemod v1-to-v2`, then grep for the
      `@mcp-codemod-error` markers it leaves.
- [ ] Decide the dual-era policy explicitly: serve handshake-era clients through the SDK's legacy
      path, or reject them and say so in the README.
- [ ] **Gate:** the negative-path probes in `references/testing.md` return the codes listed there —
      `-32602` for a missing envelope key, `-32020` for a header mismatch, `-32022` for an
      unsupported version, `405` for `GET`.

### Harden authorization

- [ ] Walk `references/auth.md`'s checklist against the deployed configuration, not the design doc.
- [ ] Confirm audience validation against the canonical server URI, and that a token minted for a
      sibling service is rejected.
- [ ] Find every path that could forward the inbound token upstream and remove it.
- [ ] Justify each requested scope against a specific operation; delete the rest.
- [ ] **Gate:** a token issued for another resource behind the same issuer is rejected with `401`,
      demonstrated against the running server.

### Publish

- [ ] Reconcile source registrations, runtime `tools/list`, any generated catalog, and the README by
      tool name.
- [ ] Review the config block users will paste as code: no inline credentials, an exact pinned
      version, no `sh -c`, no `type: "sse"`, no wildcard allow flags.
- [ ] Install the packaged artefact into a temporary directory outside the checkout and re-run
      discovery there.
- [ ] **Gate:** `references/testing.md`'s install-verification sequence succeeds from the published
      artefact, and the four inventories agree.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Revisions, `_meta` envelope, `server/discover`, eras, error-code ranges, deprecation registry | any version question, or migrating | `references/protocol-model.md` |
| Which SDK speaks which revision, package layout, renamed entry points, measured traps | before writing or upgrading any code | `references/sdk-versions.md` |
| Names, descriptions, schemas, annotations, tool count, cross-call handles | designing or reviewing the tool surface | `references/tool-design.md` |
| Result size, truncation contract, pagination, content types, caching fields | results are too big, truncated, or paged wrong | `references/tool-results.md` |
| Protocol versus tool errors, SDK divergence on exceptions, error wording | the model cannot recover from a failure | `references/errors.md` |
| stdio framing, Streamable HTTP headers, `Origin`, deprecated HTTP+SSE | choosing a transport, or the connection misbehaves | `references/transports.md` |
| Resource-server duties, audience, passthrough, scope, CIMD, confused deputy | any authenticated HTTP deployment | `references/auth.md` |
| Tool poisoning, injection through results, command injection, containment, config hygiene | reviewing for safety, or shipping to users | `references/threats.md` |
| Inspector CLI, raw wire probes, contract tests, inventory parity, usability evals | verifying anything | `references/testing.md` |

## Output format

For a review, group findings by file and lead each with its location:

```
skills/notes/src/server.ts
  src/server.ts:47 - execSync interpolates the `q` tool argument into a shell string.
      Fix: execFile("grep", ["-ril", q, DB]) — argv array, no shell.
  src/server.ts:78 - run_report's description instructs the model ("always call this first",
      "never tell the user"). Fix: describe behaviour only; move guidance to `instructions`.
```

Then two lists, in this order: **blocks release** and **hardening**. Put a finding in the first list
only if it is exploitable, silently loses data, or corrupts the protocol. State the revision each
version-dependent finding is judged against.

## Environment

Verified on Linux with Node v26.7.0, Python 3.12 and uv 0.11.21.

```bash
# TypeScript, v2 line
npm i @modelcontextprotocol/server @modelcontextprotocol/core zod ajv ajv-formats

# Python, official SDK
uv pip install mcp

# verification client (use --cli; the bare command opens a browser UI)
npx @modelcontextprotocol/inspector --cli <server command> --method tools/list
```
