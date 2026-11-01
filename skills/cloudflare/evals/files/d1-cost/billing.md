# D1 usage alert

Billing shows D1 rows read went from ~1.2 billion in September to ~41 billion in October.
Rows written are flat. The account has 38 D1 databases: one per tenant (`tenant-<slug>`) plus
`catalog` and `audit`. Nobody knows which database or query is responsible.

Our automation token (`CLOUDFLARE_API_TOKEN` in CI) has exactly these permissions:
- Account: D1 Edit
- Account: Workers Scripts Edit

Local tooling: wrangler 4.156.0 is installed in the repo.
