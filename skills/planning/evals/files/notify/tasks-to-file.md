# Agreed tasks for the notifications work

The plan is signed off. These six items need to exist as issues in `acme/notify`
under the `notifications-v1` milestone.

1. Add a durable outbox table and writer — labels: `area/db`, `size/M`
2. Add the notifier service with an idempotency key — labels: `area/backend`, `size/M`
3. Add `GET /notifications` to `openapi.yaml` and regenerate the client — labels: `area/api`, `size/S`
4. Update `mobile/` call sites for the regenerated client — labels: `area/mobile`, `size/S`
5. Add the notification bell and list to `web/` — labels: `area/web`, `size/M`
6. Add a send log with 7-year retention for enterprise accounts — labels: `area/backend`, `compliance`, `size/L`

Item 4 is blocked by item 3. Items 5 and 6 are blocked by item 2.
