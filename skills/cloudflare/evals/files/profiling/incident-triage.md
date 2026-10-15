# checkout-api performance incident

Owner: payments platform team

## Symptoms (production only)

- `checkout-api` intermittently ends invocations with outcome `exceededCpu` on `POST /checkout/quote`.
  It started after last week's release that added promo-code evaluation. Roughly 2% of quote
  requests, clustered at peak hours.
- Cart memory keeps climbing: some carts in the `CartDO` Durable Object namespace hit
  `exceededMemory` after a few hundred line-item updates. The worst instance so far is
  `9f2c4a1b7d3e5f60812a9b0c4d6e8f1023456789abcdef0123456789abcdef01`
  (namespace id `4b1e0c9d2a7f4e3c8b6a5d1f0e2c3b4a`).
- Neither reproduces in `wrangler dev`; local runs finish quote requests in ~3 ms CPU.

## What we tried

- `wrangler tail --status error` shows the `exceededCpu` outcomes but nothing about which code burns the CPU.
- We filtered Workers Logs to yesterday 18:00-19:00 (the worst hour).

## Deploy state

See `versions.txt` (pasted from `wrangler versions list` and `wrangler deployments list`
for both Workers). This morning Dana uploaded a version of checkout-api with extra logging
but did not deploy it yet.

