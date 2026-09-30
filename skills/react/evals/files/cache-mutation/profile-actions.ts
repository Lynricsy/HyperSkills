// app/settings/profile/actions.ts
'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { db } from '@/lib/db'
import { verifySession } from '@/lib/auth'

export async function updateProfile(formData: FormData) {
  const session = await verifySession()
  if (!session) throw new Error('Unauthorized')

  const displayName = String(formData.get('displayName') ?? '').trim()
  const title = String(formData.get('title') ?? '').trim()
  const bio = String(formData.get('bio') ?? '').trim()
  if (!displayName) throw new Error('Display name is required')

  await db.profile.update({
    where: { id: session.user.id },
    data: { displayName, title, bio },
  })

  // Written before cacheComponents was enabled; unchanged since.
  revalidatePath('/settings/profile')
  redirect(`/people/${session.user.id}`)
}
