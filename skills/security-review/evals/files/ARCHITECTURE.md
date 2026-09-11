# Acme Reports — architecture notes

## Services

| Service | Runtime | Network | Notes |
|---|---|---|---|
| `web` | Next.js on Cloudflare Workers | Public | Session cookie issued by `api` |
| `api` | Node 20 / Express, ECS | Public via ALB | Owns the `orders` and `customers` tables |
| `reporting` | Python / Flask, ECS | Private subnet | Reachable from `api` only, in theory |
| `warehouse` | ClickHouse | Private subnet | No authentication; network-restricted |
| `worker` | Node 20, ECS | Private subnet | Consumes SQS, has the same DB role as `api` |

## Request flow for "download my invoice"

1. Browser sends `GET /api/orders/<id>/invoice.pdf` with the session cookie.
2. ALB terminates TLS and forwards to `api`.
3. `api` validates the session, loads the order, renders the PDF.
4. `api` calls `reporting` at `POST /internal/reports` for the monthly statement variant.
5. `reporting` queries `warehouse` and POSTs the finished report to a callback URL
   supplied in the request body.

## Trust and identity

- Browser to `api`: session cookie, signed, 90-day lifetime.
- `api` to `reporting`: plain HTTP inside the VPC. There is no service-to-service
  authentication; `reporting` trusts anything that can reach it.
- `reporting` to `warehouse`: plain HTTP, no credentials.
- The ALB routes `/internal/*` to `api` only. A separate ALB rule added last quarter
  routes `/reports/*` to `reporting` so the mobile team could poll report status.
- `reporting` runs with the `reporting-service` IAM role and instance metadata is
  reachable at the usual link-local address (IMDSv1 is still enabled on this cluster).

## Data

- `orders`, `customers`: multi-tenant, `customer_id` column, no row-level security.
- Invoices and finished reports land in the `acme-reports` S3 bucket, one prefix per
  tenant, no bucket policy separating prefixes.
- Sessions live in Redis, keyed by `sid`, no per-tenant namespace.

## Known gaps the team already tracks

- No WAF in front of the public ALB.
- Audit logging exists for logins only, not for data reads or admin actions.
