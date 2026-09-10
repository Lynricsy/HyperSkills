// lib/supabase/server.ts — used by every Server Component and Route Handler.
// There is no proxy.ts / middleware.ts anywhere in the repo.
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export function createClient() {
  const cookieStore = cookies()

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value
        },
        set(name: string, value: string, options: Record<string, unknown>) {
          cookieStore.set({ name, value, ...options })
        },
        remove(name: string, options: Record<string, unknown>) {
          cookieStore.set({ name, value: '', ...options })
        },
      },
    }
  )
}

// app/api/projects/route.ts
export async function GET() {
  const supabase = createClient()

  const { data: session } = await supabase.auth.getSession()
  if (!session) {
    return Response.json({ error: 'not signed in' }, { status: 401 })
  }

  // Returns [] in the deployed app. The same SELECT in the Supabase SQL
  // editor returns every row.
  const { data, error } = await supabase.from('projects').select('*')
  return Response.json({ data, error })
}
