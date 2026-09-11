// src/index.ts — api-gateway Worker
interface Env {
  SESSIONS: KVNamespace;
  DB: any;
  API_KEY: string;
  ACCOUNT_ID: string;
  CF_API_TOKEN: string;
}

let cachedUser: { id: string; plan: string } | null = null;
let hitCount = 0;

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext) {
    ctx.passThroughOnException();
    const { waitUntil } = ctx;

    hitCount++;
    const token = (request.headers.get("authorization") ?? "").replace("Bearer ", "");
    if (token !== env.API_KEY) {
      return new Response("unauthorized", { status: 401 });
    }

    if (!cachedUser) {
      cachedUser = await env.SESSIONS.get(`session:${token}`, "json");
    }

    const url = new URL(request.url);

    if (url.pathname === "/upload") {
      const body = await request.arrayBuffer();
      const key = Math.random().toString(36).slice(2);
      const res = await fetch(
        `https://api.cloudflare.com/client/v4/accounts/${env.ACCOUNT_ID}/r2/buckets/uploads/objects/${key}`,
        {
          method: "PUT",
          body,
          headers: { Authorization: `Bearer ${env.CF_API_TOKEN}` },
        },
      );
      return new Response(null, { status: res.status });
    }

    if (url.pathname === "/report") {
      const rows = await env.DB.prepare("SELECT * FROM events").all();
      const csv = rows.results
        .map((row: Record<string, unknown>) => Object.values(row).join(","))
        .join("\n");
      const share = Math.random().toString(36).slice(2);
      await env.SESSIONS.put(`report:${share}`, csv);
      waitUntil(logUsage(env, cachedUser!.id));
      return new Response(csv, { headers: { "content-type": "text/csv" } });
    }

    fetch("https://hooks.internal.example.com/ping", {
      method: "POST",
      body: JSON.stringify({ path: url.pathname }),
    });

    return Response.json({ user: cachedUser, hits: hitCount });
  },
};

async function logUsage(env: Env, userId: string) {
  await env.SESSIONS.put(`usage:${userId}:${Date.now()}`, "1");
}
