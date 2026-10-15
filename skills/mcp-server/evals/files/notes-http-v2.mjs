// notes-mcp HTTP entry point (Streamable HTTP, 2026-07-28 era).
// Deployed behind our ingress at https://notes.example.com/mcp.
// Dependencies: @modelcontextprotocol/server 2.3.1, @modelcontextprotocol/core 2.3.1, zod 4, jose 6.
import { createServer } from "node:http";
import { McpServer, createMcpHandler, requireBearerAuth } from "@modelcontextprotocol/server";
import { createRemoteJWKSet, jwtVerify } from "jose";
import * as z from "zod";
import { searchNotes, readNote } from "./store.mjs";

const ISSUER = "https://login.example.com/";
const jwks = createRemoteJWKSet(new URL(`${ISSUER}.well-known/jwks.json`));

// Built once at startup so tool registration is not repeated on every request.
const server = new McpServer(
  { name: "notes-mcp", version: "3.4.0" },
  { capabilities: { tools: {} } },
);

server.registerTool(
  "notes_search",
  {
    description: "Search notes by keyword. Returns at most `limit` note ids with titles.",
    inputSchema: z.object({
      query: z.string().describe("Keywords to match against note titles and bodies"),
      limit: z.number().int().min(1).max(50).default(10).describe("Maximum results, 1-50"),
    }),
  },
  async ({ query, limit }) => ({
    content: [{ type: "text", text: JSON.stringify(await searchNotes(query, limit)) }],
  }),
);

server.registerTool(
  "notes_read",
  {
    description: "Return one note's body as markdown.",
    inputSchema: z.object({ note_id: z.string().describe("Note id, e.g. 'n_8f21c3'") }),
  },
  async ({ note_id }) => ({ content: [{ type: "text", text: await readNote(note_id) }] }),
);

const handler = createMcpHandler(() => server);

const auth = requireBearerAuth({
  verifier: {
    async verifyAccessToken(token) {
      // Signature, issuer and expiry are checked by jose.
      const { payload } = await jwtVerify(token, jwks, { issuer: ISSUER });
      return {
        token,
        clientId: String(payload.azp ?? payload.client_id ?? "unknown"),
        scopes: String(payload.scope ?? "").split(" ").filter(Boolean),
        expiresAt: payload.exp,
      };
    },
  },
  requiredScopes: ["notes.read"],
  resourceMetadataUrl: "https://notes.example.com/.well-known/oauth-protected-resource/mcp",
});

createServer(async (req, res) => {
  const request = new Request(`https://notes.example.com${req.url}`, {
    method: req.method,
    headers: req.headers,
    body: req.method === "POST" ? req : undefined,
    duplex: "half",
  });
  const authResult = await auth(request);
  const response = authResult instanceof Response ? authResult : await handler.fetch(request);
  res.writeHead(response.status, Object.fromEntries(response.headers));
  res.end(Buffer.from(await response.arrayBuffer()));
}).listen(8931, "127.0.0.1");
