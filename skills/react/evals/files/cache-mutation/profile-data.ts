// lib/profile.ts
// Next.js 16.3, cacheComponents: true.
// 'use cache' was added to both reads so /people/[id] and the header avatar
// land in the static shell. Before this change both reads were uncached.
import { cacheLife } from 'next/cache'
import { db } from '@/lib/db'

export type Profile = {
  id: string
  displayName: string
  title: string
  avatarUrl: string
  bio: string
}

// Read by app/people/[id]/page.tsx and by <HeaderAvatar userId=...> in the root layout.
export async function getProfile(userId: string): Promise<Profile | null> {
  'use cache'
  cacheLife('hours')
  return db.profile.findUnique({ where: { id: userId } })
}

// Read by app/people/page.tsx (the company directory).
export async function getTeamDirectory(): Promise<Profile[]> {
  'use cache'
  cacheLife('max')
  return db.profile.findMany({ orderBy: { displayName: 'asc' } })
}

// Read by app/settings/profile/page.tsx to prefill the edit form.
// Deliberately uncached: the form must show what is in the database.
export async function getProfileForEdit(userId: string): Promise<Profile | null> {
  return db.profile.findUnique({ where: { id: userId } })
}
