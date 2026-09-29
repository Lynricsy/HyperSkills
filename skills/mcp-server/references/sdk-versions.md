# SDK versions versus the specification revision

Verified against: `mcp` (PyPI) 2.2.0, `@modelcontextprotocol/sdk` 1.31.0 (and 1.30.0),
`@modelcontextprotocol/server` and `@modelcontextprotocol/core` 2.2.0 (and 2.0.0),
`@modelcontextprotocol/inspector` 2.8.0, Node v26.7.0 and v26.9.0.

## Contents

- The divergence, measured
- How to re-measure it
- Python: `mcp` 2.x renamed the entry point
- Python: `fastmcp` is a different package
- TypeScript: v1 is a single package, v2 is scoped packages
- TypeScript: two v2 traps that both surface as `-32603`
- .NET and the other SDKs
- What to write in a design document

## The divergence, measured

The current specification revision is `2026-07-28`. The SDKs do not all implement it.

| Runtime | Package | Version | `LATEST_PROTOCOL_VERSION` | `server/discover` |
|---|---|---|---|---|
| Python | `mcp` | 2.2.0 | `2026-07-28` | answers `supportedVersions: ["2026-07-28"]` |
| Node | `@modelcontextprotocol/sdk` (v1) | 1.31.0 | `2025-11-25` | `-32601 Method not found` |
| Node | `@modelcontextprotocol/server` (v2) | 2.2.0 | `2025-11-25` | answers `supportedVersions: ["2026-07-28"]` |

Two things follow, and both are easy to get wrong:

1. **A spec revision is not an SDK capability.** "We are on 2026-07-28" is a claim about wire
   format that a TypeScript v1 server cannot make. Ask for the constant, not the marketing.
2. **In the v2 TypeScript SDK, `LATEST_PROTOCOL_VERSION` describes the legacy era only.** It reads
   `2025-11-25` while the same build answers `server/discover` with `2026-07-28`. Reading that
   export as the implementation ceiling is wrong. `[verified]`

The v1 server also silently downgrades: a client asking for `2026-07-28` in `initialize` gets
`{"protocolVersion":"2025-11-25"}` back with no error. A server that must fail loudly on an
unsupported version has to check the negotiated value itself. `[verified]`

## How to re-measure it

Do not take this table on faith — it dates the moment it is written. Re-run:

```bash
# specification: the only authoritative revision list
gh api repos/modelcontextprotocol/modelcontextprotocol/git/trees/main?recursive=1 \
  --jq '.tree[].path' | grep '^schema/' | grep -v examples
gh api repos/modelcontextprotocol/modelcontextprotocol/contents/schema/<rev>/schema.ts \
  --jq .content | base64 -d | grep LATEST_PROTOCOL_VERSION

# published SDK versions
npm view @modelcontextprotocol/sdk version
npm view @modelcontextprotocol/server version
python -c "import importlib.metadata as m; print(m.version('mcp'))"

# what the installed SDK actually thinks
python -c "import mcp.types as t; print(t.LATEST_PROTOCOL_VERSION)"
node -e "import('@modelcontextprotocol/server').then(m=>console.log(m.LATEST_PROTOCOL_VERSION))"
```

## Python: `mcp` 2.x renamed the entry point

`from mcp.server.fastmcp import FastMCP` is the line in nearly every published example, including
official skills. Under `mcp` 2.x it does not exist: `[verified]`

```
ModuleNotFoundError: No module named 'mcp.server.fastmcp'. This is mcp 2.x, where FastMCP was
renamed to MCPServer (from mcp.server.mcpserver import MCPServer) and other APIs changed
```

Current shape:

```python
from typing import Annotated
from pydantic import Field
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("notes", version="1.0.0")

@mcp.tool()
def get_note(note_id: Annotated[str, Field(description="Note id, e.g. 'n_8f21c3'")]) -> str:
    """Return one note's body as markdown."""
    ...

if __name__ == "__main__":
    mcp.run()                      # stdio; mcp.run("streamable-http", port=8931) for HTTP
```

The transport literal is `"streamable-http"` with a hyphen. `"streamable_http"` with an underscore
appears in published guidance and is not a valid value.

Schema generation comes from type hints plus `pydantic.Field`, and the tool description comes from
the docstring. A tool with no docstring is emitted with `"description": ""` — see
`references/tool-design.md`.

## Python: `fastmcp` is a different package

PyPI has both `mcp` (2.2.0, the official SDK) and `fastmcp` (4.0.3, a separate third-party
package). They are not the same project and their APIs differ. Pick one deliberately and say which
in the project's dependency file; the default for a new server is `mcp`. `[verified]`

## TypeScript: v1 is a single package, v2 is scoped packages

`@modelcontextprotocol/sdk` is the v1 line; it still receives releases (1.31.0 at the time of
measurement) but keeps the `2025-11-25` ceiling above. The v2 line ships as separate packages that
are versioned independently — `server`, `core`, `client` and `codemod` at 2.2.0, `node` at 2.1.0,
the framework adapters at 2.0.x when measured: `[verified]`

| Package | Contents |
|---|---|
| `@modelcontextprotocol/core` | schemas, constants, protocol types |
| `@modelcontextprotocol/server` | `McpServer`; `/stdio` and `/validators/ajv` subpaths |
| `@modelcontextprotocol/client` | client side |
| `@modelcontextprotocol/node` | Node-specific bindings |
| `@modelcontextprotocol/express`, `/fastify`, `/hono` | HTTP framework adapters |
| `@modelcontextprotocol/codemod` | `npx @modelcontextprotocol/codemod v1-to-v2` |

Migrating is a dependency change, not a version bump. Run the codemod, then grep the tree for
`@mcp-codemod-error` markers it leaves where it could not decide. Other v2 differences worth
knowing before you start: `zod` moves to `^4.2`, the SSE and WebSocket transports are gone, the
handler's second argument is a structured `ctx` instead of v1's `extra`, and HTTP status lives on
`error.status` rather than `error.code`. `[official]`

One measurable difference in emitted schemas: v1 stamps
`"$schema":"http://json-schema.org/draft-07/schema#"` on `inputSchema`, v2 stamps
`"https://json-schema.org/draft/2020-12/schema"`. The specification's default dialect when
`$schema` is absent is 2020-12, so v1's tools declare a dialect that is not the default. `[verified]`

## TypeScript: two v2 traps that both surface as `-32603`

Both of these make *every* request fail — `server/discover` and `tools/list` included — with an
opaque `{"code":-32603,"message":"Internal server error"}`. Without an `onerror` option nothing
reaches stderr; with the handler below the cause is printed (`factory is not a function`, or
`inputSchema/outputSchema/argsSchema must be a Standard Schema …`), so always pass one. Measured on
2.0.0 and 2.2.0. `[verified]`

```javascript
import { McpServer } from "@modelcontextprotocol/server";
import { serveStdio } from "@modelcontextprotocol/server/stdio";
import * as z from "zod";

serveStdio(
  () => {                                           // trap 1: a FACTORY, not a server instance
    const server = new McpServer({ name: "notes", version: "1.0.0" }, { capabilities: { tools: {} } });
    server.registerTool(
      "get_note",
      {
        description: "Return one note's body as markdown.",
        inputSchema: z.object({ note_id: z.string() }),  // trap 2: a schema object, not bare JSON Schema
      },
      async ({ note_id }) => ({ content: [{ type: "text", text: await readNote(note_id) }] }),
    );
    // register tools here — the same factory serves both protocol eras
    return server;
  },
  { onerror: (e) => process.stderr.write(`mcp: ${e.message}\n`) },
);
```

Trap 2 is the v1 habit of passing a plain JSON Schema literal as `inputSchema`. v2 expects a
Standard Schema object — a `zod` v4 schema, or a JSON Schema literal wrapped in `fromJsonSchema(…)`
from `@modelcontextprotocol/server`. The bare literal fails every request even when a
`jsonSchemaValidator` is passed. The validator itself is optional: when omitted the server uses a
runtime-selected default (AJV on Node, `@cfworker/json-schema` on workerd), and requests succeed
without it. `[verified]`

`serveStdio` owns the era decision for the connection and pins one instance from the factory for
its lifetime. Pass `legacy: 'reject'` to refuse handshake-era clients outright instead of serving
them.

## .NET and the other SDKs

The .NET packages are `ModelContextProtocol` and `ModelContextProtocol.AspNetCore`. Published
guidance naming `Microsoft.Mcp.Core` is wrong. On the 2.x line HTTP hosting defaults to
`Stateless = true`; setting `Stateless = false` pushes clients onto the legacy `initialize`
fallback, which is usually the opposite of what the person flipping that flag intended. Deprecated
roots/sampling/logging surfaces raise build warning `MCP9005` — suppress it only as a documented
transition, never as a default. `[official]`

Go and C# SDK APIs are not covered here beyond the above: they were not exercised on the machine
this skill was written on, so their details would be unverified. For the language itself use the
`go`, `csharp-dotnet`, `typescript` or `python` skill.

<!-- sources: mcp-typescript-sdk, mcp-python-sdk, mcp-spec, awesome-copilot-mcp -->
