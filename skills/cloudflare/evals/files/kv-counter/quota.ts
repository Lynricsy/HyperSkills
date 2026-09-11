// src/quota.ts — per-team API quota, currently backed by Workers KV
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const team = new URL(request.url).searchParams.get("team");
    if (!team) return new Response("missing team", { status: 400 });

    const key = `quota:${team}`;
    const used = Number((await env.QUOTA.get(key)) ?? "0");

    if (used >= 1000) {
      return new Response("quota exceeded", { status: 429 });
    }

    await env.QUOTA.put(key, String(used + 1), { expirationTtl: 60 });

    const plan = await env.QUOTA.get(`plan:${team}`, "json");
    return Response.json({ used: used + 1, plan });
  },
} satisfies ExportedHandler<Env>;
