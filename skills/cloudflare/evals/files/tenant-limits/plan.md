# Tenant isolation plan (Workers Paid)

We are moving our B2B app to Cloudflare and want hard per-tenant isolation:

- 80,000 tenants at launch, growing to about 150,000 within a year.
- Each tenant gets its own D1 database (`tenant-<id>`).
- Each tenant gets its own R2 bucket for uploads (`uploads-<id>`).
- Each tenant gets its own KV namespace for feature flags and settings.
- Each tenant gets its own Queue for background jobs.

Our architect says Cloudflare caps all of these well below 80,000 per account, so the plan is
dead on arrival. Finance needs a yes/no per resource type, and the monthly cost of anything that
goes past what the plan includes.
