Two problems with the local stack (distroless-stack.yaml, api.Dockerfile excerpt below).

1. `docker compose up` never starts `worker`: `api` stays "unhealthy" although
   `curl localhost:8080/healthz` from the host returns 200. Plan: switch the final stage from
   distroless to `alpine:3.24` so the healthcheck has `wget`, or drop the healthcheck and the
   `depends_on` condition.

2. The build step for private modules:

       # syntax=docker/dockerfile:1
       FROM golang:1.27 AS build
       RUN --mount=type=ssh \
           mkdir -p -m 0700 /root/.ssh && \
           echo "StrictHostKeyChecking no" >> /root/.ssh/config && \
           GOPRIVATE=github.com/acme/* go mod download

   Developers run `docker compose build` from their normal shell. On my machine `ssh-add -l`
   lists four keys (personal GitHub, the prod bastion, the release-signing deploy key, a customer
   VPN key). Is this setup fine security-wise?
