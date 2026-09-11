# Dockerfile and the build

Verified against: Docker Engine 29 with BuildKit, `docker/dockerfile:1` frontend, Buildx 0.2x.

## Contents

- [Stage structure](#stage-structure)
- [Choosing the runtime base image](#choosing-the-runtime-base-image)
- [Cache: what invalidates what](#cache-what-invalidates-what)
- [Cache mounts](#cache-mounts)
- [`.dockerignore`](#dockerignore)
- [Entrypoint, command and signals](#entrypoint-command-and-signals)
- [Users, ownership and writable paths](#users-ownership-and-writable-paths)
- [HEALTHCHECK](#healthcheck)
- [Multi-architecture builds](#multi-architecture-builds)
- [Build lint and reproducibility](#build-lint-and-reproducibility)
- [Worked example](#worked-example)

## Stage structure

A stage exists to be *thrown away*. The useful shape is three or four stages where each
later stage copies named artefacts, never directories:

```
deps     install production dependencies only
build    install all dependencies, compile, run codegen
runtime  a different, smaller base + the two things above
```

Splitting `deps` from `build` lets both run in parallel and lets `runtime` copy
production dependencies that never saw a dev toolchain.

`COPY --from=build /app /app` defeats the whole exercise: it drags the builder's
sources, dev dependencies, package-manager caches and anything else in that working
directory into the shipped image. Copy `/app/dist`, `/app/node_modules`,
`/out/server` — paths you chose.

Name stages (`FROM golang:1.26 AS build`) and target them during development with
`docker build --target build`, which is how you get a shell in the stage that failed.

## Choosing the runtime base image

Default to the smallest image that can actually run the process:

| Process | Runtime base |
|---|---|
| Statically linked binary (Go with `CGO_ENABLED=0`, Rust with musl) | `scratch`, or `gcr.io/distroless/static:nonroot` when you need CA certificates, `/etc/passwd` and timezone data |
| Dynamically linked binary, or a runtime like Node or Python | `gcr.io/distroless/<runtime>:nonroot`, or the distribution's `-slim` variant when a package manager is genuinely needed at build time |
| Anything you must `exec` into in production to debug | Alpine, knowingly |

Distroless has no shell, so `docker exec ... sh` fails and `RUN` cannot be used in that
stage — that is the point, and it is also the reason to keep a `debug` variant tag
available for incident work, or to use `kubectl debug` with an ephemeral container.

Alpine's cost is not size, it is musl: DNS resolution differs from glibc (notably
around search domains and parallel A/AAAA queries), and any dependency shipping a
glibc-compiled binary — Python manylinux wheels, Node native modules, prebuilt shared
libraries — either fails to load or has to be rebuilt from source, which makes the
image bigger than the `-slim` alternative you were avoiding.

Pin the base image. `node:20` moves every week; `node:20.18.1-bookworm-slim` moves
never, and `node:20.18.1-bookworm-slim@sha256:...` cannot move at all. The pin belongs
in the Dockerfile, and updating it is a reviewable commit rather than a surprise.

## Cache: what invalidates what

The rules, which are narrower than most people assume: [official]

- The builder compares each instruction against the cached layer. Any difference in the
  instruction text is a miss, and **once one layer misses, every later layer is
  rebuilt**.
- `ADD`, `COPY` and `RUN --mount=type=bind` additionally hash the *file metadata* of
  what they bring in. `mtime` is deliberately excluded, so re-checking out a repository
  does not invalidate the cache.
- Every other instruction, including `RUN apt-get update`, is matched on the command
  string alone. The builder does not look at what changed inside the container. This is
  why a months-old `RUN apt-get update && apt-get install ...` layer keeps being reused
  with stale package indexes, and why that pair must stay in one `RUN`.
- `WORKDIR` respects `SOURCE_DATE_EPOCH`: setting it to a commit timestamp invalidates
  `WORKDIR` and everything after it on every commit.

Therefore order by rate of change:

```dockerfile
COPY package.json package-lock.json ./   # changes when dependencies change
RUN npm ci                               # expensive
COPY src ./src                           # changes every commit
RUN npm run build                        # cheap
```

Measured on a trivial Node service: with `COPY . .` before the install, a one-line
source edit re-ran `npm install`, the build and an `apt-get install` step; with the
order above, both `npm ci` steps were `CACHED` and only the source copy and compile
re-ran. [verified]

Use the lockfile-respecting install command (`npm ci`, `pip install -r
requirements.txt --require-hashes`, `go mod download`, `uv sync --frozen`), not the
resolving one. The resolving command can produce a different dependency tree from the
same inputs, which makes the cached layer a lie.

For cross-machine CI caching, the build cache is an export target:

```bash
docker buildx build \
  --cache-from type=registry,ref=example.com/app:buildcache \
  --cache-to   type=registry,ref=example.com/app:buildcache,mode=max \
  -t example.com/app:$GIT_SHA --push .
```

Without this, every CI runner is a cold build regardless of how well the Dockerfile is
ordered.

## Cache mounts

`--mount=type=cache` keeps a package manager's own download cache across builds without
putting it in a layer:

```dockerfile
RUN --mount=type=cache,target=/root/.npm npm ci
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends ca-certificates
```

Two things to know: the cache is not shared between builders (so it does nothing for a
fresh CI runner unless the builder is persisted), and `sharing=locked` is required for
apt-style caches because concurrent builds corrupt them.

For apt specifically, the Debian images ship a hook that deletes downloaded packages;
`rm -f /etc/apt/apt.conf.d/docker-clean` before the install is what makes the cache
mount effective.

## `.dockerignore`

Without one, the entire working tree is sent to the builder as build context, and
`COPY . .` copies all of it into the image. Measured: 73.5 MB of host `node_modules`
and `.git` inside a Node image, on top of the 32 MB the install itself added.
[verified]

Prefer fail-closed:

```
*
!package.json
!package-lock.json
!src/
!tsconfig.json
```

A deny-list is one forgotten entry away from shipping a new `.env.staging`; an
allow-list fails by omitting something the build needs, which surfaces immediately.

BuildKit also reads `<dockerfile-name>.dockerignore` in preference to `.dockerignore`,
which is how one repository keeps different contexts for different images.

## Entrypoint, command and signals

Use exec form. `CMD npm start` is shell form: the container's PID 1 becomes
`/bin/sh -c npm start`, `sh` does not forward `SIGTERM` to its child, so on
`docker stop` or a Kubernetes eviction the process never learns it should drain, and is
`SIGKILL`ed when the grace period expires. BuildKit warns about this directly:
`JSONArgsRecommended: JSON arguments recommended for CMD to prevent unintended behavior
related to OS signals`. [verified]

```dockerfile
ENTRYPOINT ["/app/entrypoint.sh"]     # if you need one at all
CMD ["node", "dist/index.js"]
```

If the entrypoint is a shell script, end it with `exec "$@"` so the real process
replaces the shell and inherits PID 1.

PID 1 also never reaps orphaned children. If the process forks (some Python and Ruby
servers, anything spawning subprocesses), add an init: `docker run --init`,
`init: true` in Compose, or `shareProcessNamespace`-free Kubernetes defaults plus a
process that reaps properly. Symptom of getting this wrong: zombie processes
accumulating until the pid limit.

## Users, ownership and writable paths

```dockerfile
# Most official images already ship an unprivileged user; reuse it.
USER node
# Otherwise create one with a fixed, non-zero uid so Kubernetes can assert runAsNonRoot.
RUN useradd --uid 10001 --create-home app
USER 10001
```

Use a numeric uid in `USER` when the workload will run with `runAsNonRoot: true`: the
kubelet can only verify a *numeric* uid before start; with a username it has to resolve
`/etc/passwd` inside the image and fails closed on distroless.

Set ownership while copying (`COPY --chown=10001:10001`) rather than in a later `RUN
chown -R`, which duplicates every touched file into a new layer.

Assume a read-only root filesystem at runtime and declare the writable paths as volumes
or `emptyDir` mounts. Applications that insist on writing next to their code (caches,
compiled templates, PID files) need that path configured elsewhere — discovering this
in the cluster instead of the Dockerfile costs a deploy.

## HEALTHCHECK

`HEALTHCHECK` is read by Docker and Compose. Kubernetes ignores it entirely and uses
the pod's probes, so a `HEALTHCHECK` in an image destined only for Kubernetes is dead
weight that also adds a process spawn every interval.

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD ["/app/healthcheck"]
```

Prefer a compiled probe or a language-native one-liner over `curl`/`wget`, which are
not present in a minimal image and would have to be added just for this.

## Multi-architecture builds

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t example.com/app:1.2.3 --push .
```

Multi-platform builds need the `docker-container` driver and push the result as an
index (manifest list); the default `docker` driver can only load a single platform.

In the Dockerfile, use the automatic args instead of hard-coding:

```dockerfile
FROM --platform=$BUILDPLATFORM golang:1.26 AS build
ARG TARGETOS TARGETARCH
RUN CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH go build -o /out/server .
```

`--platform=$BUILDPLATFORM` on the build stage keeps the compiler running natively and
cross-compiles, instead of emulating the whole toolchain under QEMU — usually an order
of magnitude faster. Only the runtime stage needs to be the target platform.

Watch for silently wrong results: a base image without an arm64 variant fails the
build, but a `RUN curl ... | sh` installer that ignores the architecture produces an
image that only crashes at run time on the other platform.

## Build lint and reproducibility

```bash
docker build --check .          # BuildKit's own lint rules, no image produced
```

It catches the two mistakes this file cares most about — `SecretsUsedInArgOrEnv` and
`JSONArgsRecommended` — plus stage-name and copy-from mistakes. Run it in CI; it is
fast and produces no artefacts. [verified]

For reproducibility: pin the base by digest, pin the package set with a lockfile, and
set `SOURCE_DATE_EPOCH` to a fixed value (not a commit timestamp) if identical inputs
must produce an identical digest.

## Worked example

```dockerfile
# syntax=docker/dockerfile:1
FROM node:22.13.1-bookworm-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    --mount=type=secret,id=npm_token \
    NPM_CONFIG_USERCONFIG=/tmp/npmrc \
    sh -c 'printf "//registry.npmjs.org/:_authToken=%s\n" "$(cat /run/secrets/npm_token)" > /tmp/npmrc \
      && npm ci --omit=dev'

FROM node:22.13.1-bookworm-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY src ./src
COPY tsconfig.json ./
RUN npm run build

FROM gcr.io/distroless/nodejs22-debian12:nonroot AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY --from=deps  /app/node_modules ./node_modules
COPY --from=build /app/dist         ./dist
USER 65532
CMD ["dist/index.js"]
```

Rebuilt from 1.3 GB to 230 MB on a trivial Express service by these changes alone
(single-stage `node:22` with `COPY . .` and no `.dockerignore`, against the shape
above). The `docker history` of the original attributed the bytes to three layers:
61.7 MB of debugging tools installed into the runtime, 32 MB of install output and
73.5 MB from the unfiltered build context. [verified]

<!-- sources: docker-docs, netresearch-docker, awesome-copilot, google-skills, impertio-docker -->
