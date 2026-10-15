// Shared with the admin console: callers inject the server and the request schemas,
// so this module has no SDK import of its own.
import { listAuditDays, readAuditDay } from "../store.js";

type Extra = { requestInfo?: { headers: Record<string, string | string[] | undefined> } };
type Registrar = {
  setRequestHandler(
    schema: unknown,
    handler: (req: { params: { uri: string } }, extra: Extra) => Promise<unknown>,
  ): void;
};

export function registerAuditResources(
  server: Registrar,
  schemas: { ListResourcesRequestSchema: unknown; ReadResourceRequestSchema: unknown },
) {
  server.setRequestHandler(schemas.ListResourcesRequestSchema, async (_req, extra) => {
    const tenant = String(extra.requestInfo?.headers["x-tenant-id"] ?? "default");
    const days = await listAuditDays(tenant);
    return {
      resources: days.map((d) => ({ uri: `audit://${tenant}/${d}`, name: `Audit log ${d}` })),
    };
  });

  server.setRequestHandler(schemas.ReadResourceRequestSchema, async (req, extra) => {
    const tenant = String(extra.requestInfo?.headers["x-tenant-id"] ?? "default");
    const day = req.params.uri.split("/").pop() ?? "";
    return { contents: [{ uri: req.params.uri, text: await readAuditDay(tenant, day) }] };
  });
}
