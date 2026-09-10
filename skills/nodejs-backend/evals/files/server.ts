import Fastify from 'fastify'
import { readFileSync } from 'node:fs'
import { Pool } from 'pg'

const app = Fastify({ logger: true })
const pool = new Pool({ connectionString: process.env.DATABASE_URL })

app.decorateRequest('ctx', { traceId: '', tenant: 'public' })

app.addHook('onRequest', async (request) => {
  request.ctx.traceId = String(request.headers['x-trace-id'] ?? '')
  request.ctx.tenant = String(request.headers['x-tenant'] ?? 'public')
})

app.setErrorHandler((error, request, reply) => {
  request.log.error(error.message)
  reply.status(error.statusCode ?? 500).send({
    message: error.message,
    code: error.code,
    stack: error.stack,
  })
})

app.get('/orders/:id', async (request) => {
  const { id } = request.params as { id: string }
  const { rows } = await pool.query(
    'select * from orders where id = $1 and tenant = $2',
    [id, request.ctx.tenant],
  )
  if (rows.length === 0) {
    throw new Error(`order ${id} not found in tenant ${request.ctx.tenant}`)
  }
  return rows[0]
})

app.post('/orders/import', async () => {
  const raw = readFileSync('/var/spool/orders/pending.csv', 'utf8')
  const lines = raw.split('\n').filter((line) => line.length > 0)
  for (const line of lines) {
    await pool.query('insert into orders (payload) values ($1)', [line])
  }
  return { imported: lines.length }
})

await app.listen({ port: Number(process.env.PORT ?? 3000), host: '0.0.0.0' })

process.on('SIGTERM', () => {
  app.log.info('SIGTERM received')
  process.exit(0)
})
