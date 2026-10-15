// services/edge (Hono on Node via @hono/node-server)
import { Hono } from 'hono'
import { serve } from '@hono/node-server'
import { authHandler } from './auth' // fetch-style: (request: Request) => Promise<Response>

const app = new Hono()

app.get('/healthz', (c) => c.text('ok'))

// Hand everything under /auth to the auth library.
app.mount('/auth', authHandler)

serve({ fetch: app.fetch, port: Number(process.env.PORT ?? 8080) })
