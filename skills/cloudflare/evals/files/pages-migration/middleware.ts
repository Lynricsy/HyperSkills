// functions/_middleware.ts — Pages Functions middleware
export const onRequest: PagesFunction<{ SESSIONS: KVNamespace }> = async (context) => {
  const url = new URL(context.request.url);

  if (url.pathname.startsWith("/account")) {
    const cookie = context.request.headers.get("cookie") ?? "";
    const sid = /sid=([^;]+)/.exec(cookie)?.[1];
    const session = sid ? await context.env.SESSIONS.get(`sess:${sid}`) : null;
    if (!session) {
      return Response.redirect(`${url.origin}/login`, 302);
    }
  }

  console.log(`${context.request.method} ${url.pathname}`);
  return context.next();
};
