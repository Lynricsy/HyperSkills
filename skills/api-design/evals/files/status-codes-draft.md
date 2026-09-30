# Subscriptions API — status codes (draft for partners)

| Code | Meaning | Client action |
|------|---------|---------------|
| 200 | Subscription returned | — |
| 401 | Missing or expired token | Refresh the token and retry |
| 403 | Token lacks the `subscriptions:read` scope | Do not retry |
| 404 | Subscription does not exist | Remove it from your records |
| 410 | Subscription was deleted | Remove it from your records |
| 429 | Rate limited | Retry after `Retry-After` |
| 5xx | Our side failed | Retry with backoff |

Errors use `application/problem+json`.
