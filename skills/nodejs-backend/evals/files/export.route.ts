import { Hono } from 'hono'
import { serve } from '@hono/node-server'
import { readFile } from 'node:fs/promises'
import { db } from './db.ts'

type Env = { Variables: { requestId: string } }

const app = new Hono<Env>()

app.use('*', (c, next) => {
  c.set('requestId', crypto.randomUUID())
  console.log('incoming', c.req.method, c.req.path)
})

app.post('/exports', async (c) => {
  const body = await c.req.json()
  const rows = await db.selectAll(body.table)
  const csv = rows
    .map((row: Record<string, unknown>) => Object.values(row).join(','))
    .join('\n')
  return c.text(csv)
})

app.get('/exports/:id/download', async (c) => {
  const file = await readFile(`/var/exports/${c.req.param('id')}.csv`)
  return c.body(file)
})

app.onError((err, c) => {
  console.error(c.get('requestId'), err)
  return c.json({ error: String(err) }, 500)
})

serve({ fetch: app.fetch, port: Number(process.env.PORT ?? 3000) })
