// Registered by buildServer() in server.mjs; the CLI runs the same server over stdio
// (serveStdio from @modelcontextprotocol/server/stdio).
import * as z from "zod";
import { loadAuditEvents } from "./store.mjs";

export function registerExportTool(server) {
  server.registerTool(
    "export_audit_log",
    {
      description: "Export the full audit log for a tenant and month as JSON.",
      inputSchema: z.object({
        tenant: z.string().describe("Tenant id, e.g. 'acme'"),
        month: z.string().describe("Month as YYYY-MM, e.g. '2026-09'"),
      }),
      annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
    },
    async ({ tenant, month }) => {
      const events = await loadAuditEvents(tenant, month); // largest tenant: ~60k events, ~14 MB as JSON
      return { content: [{ type: "text", text: JSON.stringify(events) }] };
    },
  );
}
