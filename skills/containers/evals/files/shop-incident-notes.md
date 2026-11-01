# Ops review, week 44 (draft - Bob)

## 1. Scanner finding on shop-prod-1:9100

The security scanner flags port 9100 on shop-prod-1 as `s3-sync 1.3.0` (CVE-2026-4471, path
traversal). That cannot be ours: s3-sync was retired on 2026-10-22, its profile is gone from
deploy.sh, and we have redeployed six times since with `up -d --remove-orphans`, which removes
anything that is no longer part of the stack. `docker compose config --services` on the host lists
only `api` and `worker`. Conclusion: stale scanner cache. Action: mark as false positive.

## 2. Slow requests on 2026-10-27, 14:05-14:47 UTC

AWS reported degraded CloudWatch Logs ingestion in eu-central-1 for exactly that window. During
it, api p99 went from 180 ms to 30 s and most requests timed out, while CPU on the host stayed at
8 % and the database dashboard looked normal. Docker buffers container output in memory, so a
logging outage cannot slow the application down - it can at worst lose some lines. The database
must have been the bottleneck even though its dashboard did not show it. Action: add two read
replicas (+1,900 EUR/month) and raise the api timeout to 60 s.

## 3. eMudhra CA compromise

Carla checked whether our images still trust the compromised eMudhra roots:

    $ docker run --rm registry.example.com/shop/api:2.14.0 \
        grep -ci emudhra /etc/ssl/certs/ca-certificates.crt
    0

So the roots are not in the image. Image 2.14.0 was built by CI on 2026-10-15 from
`FROM alpine:3.24` with `RUN apk add --no-cache ca-certificates` (the CI builder keeps its layer
cache between builds). Action: write "all shop images are covered" in the release note and close
the ticket.
