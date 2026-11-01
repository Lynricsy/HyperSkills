# orders database

- Engine: PostgreSQL 16 on Amazon RDS, single primary, no read replicas.
- Region: us-east-1 (N. Virginia). Not replicated to any other region.
- Fronted by Hyperdrive config `orders-pg` (caching enabled, default max_age).

# Latency report (last 7 days, from Workers metrics)

| Client location | p50 /orders/:id | p95 /orders/:id |
|---|---|---|
| Ashburn | 38 ms | 70 ms |
| Frankfurt | 520 ms | 760 ms |
| Singapore | 980 ms | 1,310 ms |

admin-dashboard (service binding -> OrdersService.getOrder) shows the same pattern.

# Deploy

CI runs `npm ci && npx wrangler deploy --secrets-file production.env` with wrangler pinned in package.json.
Last week we bumped wrangler from 4.150.0 to 4.156.0. Since that deploy, every /webhooks/payments call
returns 401 "bad signature". The payment provider says nothing changed on their side, and nobody edited
production.env.
