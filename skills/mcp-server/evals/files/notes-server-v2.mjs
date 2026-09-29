// notes-mcp, migrated from @modelcontextprotocol/sdk 1.x to the v2 packages.
// package.json: "@modelcontextprotocol/server": "^2.2.0", "ajv": "^8.17.1"
import { McpServer } from "@modelcontextprotocol/server";
import { serveStdio } from "@modelcontextprotocol/server/stdio";
import { AjvJsonSchemaValidator } from "@modelcontextprotocol/server/validators/ajv";

import { listNotes, readNote } from "./store.js";

serveStdio(
  () => {
    const server = new McpServer(
      { name: "notes-mcp", version: "0.4.0" },
      {
        capabilities: { tools: {} },
        // added after the first round of -32603s; did not help
        jsonSchemaValidator: new AjvJsonSchemaValidator(),
      },
    );

    server.registerTool(
      "list_notes",
      {
        description: "List note ids and titles, newest first.",
        inputSchema: {
          type: "object",
          properties: {
            limit: { type: "integer", minimum: 1, maximum: 50, description: "Max notes to return" },
          },
        },
      },
      async ({ limit = 20 }) => ({
        content: [{ type: "text", text: JSON.stringify(await listNotes(limit)) }],
      }),
    );

    server.registerTool(
      "get_note",
      {
        description: "Return one note's body as markdown.",
        inputSchema: {
          type: "object",
          properties: { note_id: { type: "string", description: "Note id, e.g. 'n_8f21c3'" } },
          required: ["note_id"],
        },
      },
      async ({ note_id }) => ({ content: [{ type: "text", text: await readNote(note_id) }] }),
    );

    return server;
  },
  { onerror: (e) => process.stderr.write(`mcp: ${e.message}\n`) },
);
