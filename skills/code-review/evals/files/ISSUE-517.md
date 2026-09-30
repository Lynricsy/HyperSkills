# Issue #517 — Export a customer's orders as CSV

## Problem

Customers regularly ask support for a copy of their order history. Today support copies rows
out of the admin screen by hand.

## Requirement

Add an endpoint that downloads one customer's orders as a CSV file.

- `GET /orders/export?customerId=<id>` responds with `text/csv`.
- First line is the header `id,sku,quantity,note,created_at`, then one line per order.
- `note` is the free-text note the customer typed at checkout.

## Out of scope

- No schema changes.
- No auth changes; the existing session middleware already guards `/orders/*`.
- No UI; support pastes the URL into the browser.

## Acceptance

- Support can open the downloaded file in a spreadsheet and send it to the customer.
- Existing order tests still pass.
