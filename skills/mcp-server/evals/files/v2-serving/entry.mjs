// Entry points for the notes MCP server.
// Dependencies: @modelcontextprotocol/server 2.4.0, @modelcontextprotocol/core 2.4.0, zod 4.
//   node entry.mjs stdio   -> launched by editors and by the platform team's agent host
//   node entry.mjs http    -> loopback-only endpoint for the local dashboard
import { createServer } from "node:http";
import { McpServer, createMcpHandler } from "@modelcontextprotocol/server";
import { StdioServerTransport } from "@modelcontextprotocol/server/stdio";
import * as z from "zod";
import { searchNotes } from "./store.mjs";

function buildServer() {
  const server = new McpServer({ name: "notes", version: "3.2.0" }, { capabilities: { tools: {} } });
  server.registerTool(
    "notes_search",
    {
      description: "Full-text search over the caller's notes. Returns at most 20 {id, title} matches; use a narrower query for more.",
      inputSchema: z.object({ query: z.string().min(2).describe("Words to match in note titles and bodies") }),
      annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
    },
    async ({ query }) => ({ content: [{ type: "text", text: JSON.stringify(await searchNotes(query)) }] }),
  );
  return server;
}

if (process.argv[2] === "http") {
  // DNS-rebinding protection: the v2 SDK validates Origin for us, so binding loopback is enough.
  const handler = createMcpHandler(() => buildServer(), { onerror: (err) => console.error(err) });
  createServer(async (req, res) => {
    const request = new Request(`http://127.0.0.1:8932${req.url}`, {
      method: req.method,
      headers: req.headers,
      body: req.method === "POST" ? req : undefined,
      duplex: "half",
    });
    const response = await handler.fetch(request);
    res.writeHead(response.status, Object.fromEntries(response.headers));
    res.end(Buffer.from(await response.arrayBuffer()));
  }).listen(8932, "127.0.0.1");
} else {
  await buildServer().connect(new StdioServerTransport());
}
