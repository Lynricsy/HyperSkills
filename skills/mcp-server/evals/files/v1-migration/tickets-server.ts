import express from "express";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { ListResourcesRequestSchema, ReadResourceRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { registerAuditResources } from "./plugins/audit.js";
import { findTickets } from "./store.js";

export function buildServer() {
  const server = new McpServer(
    { name: "tickets", version: "0.9.0" },
    { capabilities: { tools: {}, resources: {}, prompts: {} } },
  );

  server.tool(
    "search_tickets",
    "Search open tickets by text. Returns at most 20 tickets as JSON.",
    { query: z.string().describe("Free text, e.g. 'login timeout'") },
    async ({ query }, extra) => {
      const tenant = extra.requestInfo?.headers["x-tenant-id"];
      const rows = await findTickets(String(tenant ?? "default"), query);
      return { content: [{ type: "text", text: JSON.stringify(rows.slice(0, 20)) }] };
    },
  );

  // The audit plugin is shared with the admin console, so it receives the SDK surface
  // instead of importing it.
  registerAuditResources(server.server, { ListResourcesRequestSchema, ReadResourceRequestSchema });

  return server;
}

const app = express();
app.use(express.json());
app.post("/mcp", async (req, res) => {
  const server = buildServer();
  const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
  res.on("close", () => transport.close());
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
});
app.listen(8931, "127.0.0.1");
