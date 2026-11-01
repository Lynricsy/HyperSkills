// Draft: run on Gateway HTTP traffic to our file-sharing SaaS.
// Goals: tag uploads with the tenant, retry once on upstream 5xx, fall back to the backup
// endpoint if the primary keeps failing, and log who uploaded what.

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const user = request.headers.get("x-user-email") ?? "unknown";
    const headers = new Headers(request.headers);
    headers.set("X-Tenant", "acme");
    const upstream = new Request(request, { headers });

    let response = await fetch(upstream);
    if (response.status >= 500) {
      response = await fetch(upstream); // retry once
    }
    if (response.status >= 500) {
      const backup = new URL(request.url);
      backup.hostname = "backup.files-saas.example";
      response = await fetch(new Request(backup, upstream));
    }

    const body = await response.text();
    console.log(JSON.stringify({ user, url: request.url, status: response.status, bytes: body.length }));
    return new Response(body, response);
  },
};
