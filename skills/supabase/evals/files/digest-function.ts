// supabase/functions/send-digest/index.ts
// Called nightly by pg_cron (digest-cron.sql) and on demand from the app by signed-in users.
import { withSupabase } from 'npm:@supabase/server@1'

export default {
  fetch: withSupabase({ auth: ['user', 'secret'] }, async (req, ctx) => {
    const onlyMine = ctx.authMode === 'user'

    let query = ctx.supabaseAdmin
      .from('digests')
      .select('id, user_id')
      .lte('send_at', new Date().toISOString())
      .is('sent_at', null)

    if (onlyMine) {
      query = query.eq('user_id', ctx.userClaims!.id)
    }

    const { data: due, error } = await query
    if (error) {
      return Response.json({ error: error.message }, { status: 500 })
    }

    for (const digest of due ?? []) {
      await ctx.supabaseAdmin.from('digest_queue').insert({ digest_id: digest.id })
    }

    return Response.json({ queued: due?.length ?? 0 })
  }),
}
