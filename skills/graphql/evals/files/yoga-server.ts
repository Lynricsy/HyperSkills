// GraphQL Yoga 6 server for the storefront API (Node 22).
// Deployed behind the CDN; NODE_ENV is set by the container image.
import { createServer } from 'node:http';
import { createSchema, createYoga } from 'graphql-yoga';
import { db } from './db';

const typeDefs = /* GraphQL */ `
  type Query {
    order(id: ID!): Order
  }

  type Mutation {
    applyCoupon(orderId: ID!, code: String!): Order
  }

  type Order {
    id: ID!
    total: Int!
    couponCode: String
  }
`;

const resolvers = {
  Query: {
    order: (_: unknown, { id }: { id: string }) => db.orders.findById(id),
  },
  Mutation: {
    applyCoupon: async (_: unknown, { orderId, code }: { orderId: string; code: string }) => {
      const coupon = await db.coupons.findByCode(code);
      if (!coupon || coupon.expired) {
        // Support wants shoppers to see this text in the app.
        throw new Error(`Coupon ${code} is expired or does not exist`);
      }
      // A failed write here surfaces the driver message, e.g.
      // "duplicate key value violates unique constraint orders_coupon_uniq on host pg-primary-2".
      return db.orders.applyCoupon(orderId, coupon.id);
    },
  },
};

const yoga = createYoga({
  schema: createSchema({ typeDefs, resolvers }),
  // The shoppers never saw the coupon message, so masking was switched off.
  maskedErrors: false,
  // Mobile clients send several operations per HTTP request.
  batching: true,
});

createServer(yoga).listen(4000);
