# Issue #482 — List a customer's orders

## Problem

Support has no way to see what a customer has ordered without querying the database by hand.

## Requirement

Add a read endpoint that returns the orders belonging to one customer.

- `GET /orders?customerId=<id>` returns `id`, `sku`, `quantity` and `status` for that customer.
- Optional `status` query parameter filters to a single status.
- Response is JSON, newest first.

## Out of scope

- No changes to order creation or cancellation.
- No schema changes.
- No auth changes; the existing session middleware already guards `/orders/*`.

## Acceptance

- New endpoint returns only the requested customer's rows.
- Existing order tests still pass.
