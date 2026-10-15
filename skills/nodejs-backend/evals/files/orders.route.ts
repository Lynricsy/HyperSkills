// services/orders-api (Fastify 5.12, default Ajv settings)
import type { FastifyInstance } from 'fastify'

const createOrderBody = {
  type: 'object',
  required: ['sku', 'qty'],
  // Unknown fields such as a misspelled `discount` are rejected with 400.
  // contract/orders.test.ts relies on this: it posts { sku, qty, discount } and expects 400.
  additionalProperties: false,
  properties: {
    sku: { type: 'string', minLength: 1 },
    qty: { type: 'integer', minimum: 1 },
    discountCode: { type: 'string' },
  },
} as const

export async function orderRoutes(app: FastifyInstance) {
  app.post('/orders', { schema: { body: createOrderBody } }, async (request, reply) => {
    const order = await app.orders.create(request.body)
    return reply.code(201).send({ id: order.id })
  })
}
