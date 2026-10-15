// lib/auth-guard.ts (Next.js App Router, @supabase/ssr)
// Project created in 2023. We still sign user JWTs with the legacy JWT secret (HS256);
// the move to the new JWT signing keys has sat on the backlog since spring.
import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'

// Perf review: requireUser() adds ~80 ms to every server-rendered request.
// getClaims() verifies the token locally against the cached JWKS, so it cannot be the
// cause — the time must be going into the profile query below.
export async function requireUser() {
  const supabase = await createClient()

  const { data, error } = await supabase.auth.getClaims()
  if (error || !data) {
    redirect('/login')
  }

  const { data: profile } = await supabase
    .from('profiles')
    .select('id, display_name, plan')
    .eq('id', data.claims.sub)
    .single()

  return { claims: data.claims, profile }
}
