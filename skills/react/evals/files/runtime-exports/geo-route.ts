// app/api/geo/route.ts
// Edge so the country lookup runs close to the visitor.
export const runtime = 'edge'

export async function GET(request: Request) {
  const country = request.headers.get('x-vercel-ip-country') ?? 'unknown'
  return Response.json({ country })
}
