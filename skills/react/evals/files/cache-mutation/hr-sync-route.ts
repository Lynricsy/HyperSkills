// app/api/hr-sync/route.ts
// Called by the HR system whenever job titles change (several times a day).
import { updateTag } from 'next/cache'
import { db } from '@/lib/db'
import { verifyHrSignature } from '@/lib/hr'

export async function POST(request: Request) {
  const body = await request.text()
  if (!verifyHrSignature(request.headers.get('x-hr-signature'), body)) {
    return new Response('Invalid signature', { status: 401 })
  }

  const changes: { userId: string; title: string }[] = JSON.parse(body)
  for (const change of changes) {
    await db.profile.update({ where: { id: change.userId }, data: { title: change.title } })
  }

  updateTag('team-directory')
  return Response.json({ updated: changes.length })
}
