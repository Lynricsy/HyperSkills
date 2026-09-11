# Docker Compose for development

Verified against: Compose Specification as implemented by Compose v5 (`docker compose`).

## Contents

- [The shape of a current file](#the-shape-of-a-current-file)
- [`version:` is obsolete](#version-is-obsolete)
- [Dependency ordering that actually waits](#dependency-ordering-that-actually-waits)
- [Healthchecks worth having](#healthchecks-worth-having)
- [One-shot services and profiles](#one-shot-services-and-profiles)
- [Source code in the container](#source-code-in-the-container)
- [Volumes and state](#volumes-and-state)
- [Networks, ports and service discovery](#networks-ports-and-service-discovery)
- [Configuration and secrets](#configuration-and-secrets)
- [Composing files: `include`, `extends`, overrides](#composing-files-include-extends-overrides)
- [Validation gate](#validation-gate)

## The shape of a current file

```yaml
name: acme-dev

services:
  api:
    build:
      context: .
      target: dev
    environment:
      DATABASE_URL: postgres://app:app@db:5432/app
    depends_on:
      db: { condition: service_healthy }
      cache: { condition: service_healthy }
      migrate: { condition: service_completed_successfully }
    ports: ["127.0.0.1:3000:3000"]
    develop:
      watch:
        - { path: ./src, action: sync, target: /app/src }
        - { path: ./package-lock.json, action: rebuild }

  migrate:
    build: { context: ., target: dev }
    profiles: ["tools"]
    restart: "no"
    command: npm run migrate
    depends_on:
      db: { condition: service_healthy }

  db:
    image: postgres:17.2-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: app
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d app"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 10s

  cache:
    image: redis:7.4-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      retries: 10

volumes:
  pgdata:
```

## `version:` is obsolete

The top-level `version` property exists only for backward compatibility, is purely
informative, and produces a warning when present. Compose always validates against the
current schema regardless of what it says. Delete it. [official]

Set `name:` instead — it fixes the project name (and therefore container, network and
volume names) rather than deriving it from the directory, which is what makes two
checkouts of the same repository collide.

## Dependency ordering that actually waits

The short form is the single most common source of "it works on the second try":

```yaml
depends_on: [db]          # waits for the container to be created and started
```

That is all it guarantees. Postgres has not finished initialising, the JVM has not
bound its port. Use the long form:

| Condition | Means |
|---|---|
| `service_started` | The default; container started. Almost never what you want for a dependency you talk to. |
| `service_healthy` | The dependency's own `healthcheck` is passing. Requires the dependency to define one. |
| `service_completed_successfully` | The dependency container exited with code 0. This is how a migration or seed job is ordered. |

`restart: true` inside the long form additionally restarts the dependent service when
Compose updates the dependency — useful for a service that caches a connection at
start-up.

A migration service needs **both** treatments: `service_completed_successfully` so the
API waits for it, and a `profiles:` entry (below) so it is not in everybody's default
`up`. Profiles alone turn "runs every time" into "never runs", which is a different
bug.

## Healthchecks worth having

A healthcheck that passes before the service is usable is worse than none, because
`service_healthy` then gates on nothing.

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U app -d app"]
  start_period: 10s     # failures during this window do not count
  interval: 5s
  timeout: 3s
  retries: 10
```

`pg_isready` without `-U`/`-d` passes against the temporary server the official
Postgres image runs during first-time initialisation — the check succeeds, the API
connects, and the real server restarts underneath it. Name the user and the database.

Use `start_period` rather than a long `interval` for slow starters: failures inside the
start period do not count toward `retries`, so the service is not marked unhealthy
while it is legitimately booting.

`CMD` is exec form and needs the binary to exist in the image; `CMD-SHELL` runs through
`/bin/sh` and needs a shell. Distroless images have neither, so their healthcheck has
to be a compiled probe or has to move to the platform.

## One-shot services and profiles

```yaml
migrate:
  profiles: ["tools"]
  restart: "no"
```

Services with a `profiles:` key are excluded from `docker compose up` unless the
profile is activated with `--profile tools` or `COMPOSE_PROFILES`. `docker compose run
--rm migrate` activates the service's own profiles implicitly, so the everyday command
does not need the flag.

`restart: "no"` matters for one-shot containers: with a restart policy inherited from a
template or set globally, a job that exits 0 is started again.

## Source code in the container

Two workable models. Pick one; mixing them is where the confusion comes from.

**`develop.watch` (preferred).** Compose watches host paths and applies an action:

| Action | Effect |
|---|---|
| `sync` | Copies changed files into the running container at `target`. No restart. |
| `restart` | Restarts the container. |
| `sync+restart` | Copy, then restart — for a process that reads config at start-up. |
| `sync+exec` | Copy, then run a command inside the container. |
| `rebuild` | Rebuild the image from `build:` and recreate the service. |

Source paths get `sync`; the dependency manifest and lockfile get `rebuild`, because a
new dependency has to be installed in the image, not copied in. Run it with
`docker compose watch` (or `docker compose up --watch`).

The reason to prefer this over a bind mount is not correctness, it is I/O: a
whole-tree bind mount on macOS or Windows pays a filesystem round trip on every read
the container makes, including every dependency file at start-up. `sync` pushes only
what changed and leaves the container's filesystem native.

**Bind mount plus a shadowing volume.** If you keep `- .:/app`, the host's dependency
directory replaces the image's, which breaks immediately when the host is a different
platform (native modules, compiled wheels). Shadow it:

```yaml
volumes:
  - .:/app
  - /app/node_modules      # anonymous volume, wins over the bind mount at this path
```

The anonymous volume is populated from the image the first time and then persists, so
after changing dependencies you need `docker compose down -v` or a named volume you can
remove — a real cost, and the reason `watch` is the better default.

Use `ignore:` on a `sync` rule for anything generated inside the container that the
host should not overwrite.

## Volumes and state

- Named volumes for anything that must survive `docker compose down` (database data
  directories). An anonymous volume is deleted by `down -v` along with everything else,
  and is hard to identify.
- Bind mounts for source and for files you want to edit; they inherit host ownership,
  which is why a container running as a non-root user cannot write to them unless the
  uid matches. Fix by running the dev container with the host uid
  (`user: "${UID}:${GID}"`) rather than by `chmod 777`.
- `tmpfs:` for scratch that should never touch disk.

## Networks, ports and service discovery

Services on the same Compose network reach each other by **service name** on the
container port: `postgres://app:app@db:5432/app` works with no `ports:` entry at all.
`ports:` exists only to expose something to the host.

Therefore publishing `5432:5432` is not how the API reaches the database — it is how
everyone on the local network reaches your development database. Publish only what a
host tool needs, and bind it: `"127.0.0.1:5432:5432"`.

`expose:` is documentation; it does not publish anything and is not required for
inter-service traffic.

## Configuration and secrets

- `env_file:` for the bulk, `environment:` for the few values that vary per developer.
  Values in `environment:` override `env_file:`.
- `${VAR:-default}` interpolation is resolved from the shell and the `.env` file next to
  the Compose file — note that `.env` configures *Compose*, while `env_file:` configures
  *the container*. They are frequently confused.
- For anything genuinely secret even locally, use the `secrets:` top-level section with
  `file:`; it mounts at `/run/secrets/<name>` and stays out of `docker inspect`.
- A plaintext password for a throwaway local database is acceptable — say so explicitly
  when reviewing rather than ignoring it, so the reader knows it was considered and
  that the same file must not be reused for anything shared.

## Composing files: `include`, `extends`, overrides

- `compose.yaml` plus `compose.override.yaml` is applied automatically; this is the
  clean place for developer-only settings so the base file stays deployable.
- `include:` pulls in another complete Compose file, keeping its own relative paths
  correct — the right tool for a sub-project's stack.
- `extends:` reuses a single service definition across files. It does not merge
  `depends_on`, `volumes_from` or `links`, which surprises people.
- Merge semantics differ per field: sequences are appended, mappings are merged, scalars
  are replaced. When in doubt, run `docker compose config` and read the result rather
  than predicting it.

## Validation gate

```bash
docker compose config --quiet            # schema + interpolation; silent means valid
docker compose config                     # the fully merged file, with defaults resolved
docker compose down -v && docker compose up --wait
```

`--wait` blocks until every service with a healthcheck is healthy and fails if one is
not, which turns "it eventually came up" into a pass/fail. A cold start from `down -v`
with no manual step in between is the real test of the dependency wiring.

<!-- sources: compose-spec, docker-docs, netresearch-docker, impertio-docker -->
