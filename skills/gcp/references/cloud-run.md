# Cloud Run: revisions, scaling, and shipping a change

Verified against: Google Cloud SDK 584.0.0 (`gcloud run` help text quoted below is from that
release); behaviour cross-read against cloud.google.com/run.

## Contents

- [Three resource types](#three-resource-types)
- [Revisions are immutable](#revisions-are-immutable)
- [Concurrency](#concurrency)
- [Two pairs of scaling flags](#two-pairs-of-scaling-flags)
- [Request timeout](#request-timeout)
- [CPU allocation and billing mode](#cpu-allocation-and-billing-mode)
- [Cold starts](#cold-starts)
- [Execution environment](#execution-environment)
- [Shipping a change safely](#shipping-a-change-safely)
- [Identity and access](#identity-and-access)
- [Reaching a VPC and a database](#reaching-a-vpc-and-a-database)
- [Building and image sources](#building-and-image-sources)
- [Jobs](#jobs)
- [What breaks on first deploy](#what-breaks-on-first-deploy)

## Three resource types

| Type | Trigger | Shape |
|---|---|---|
| **Service** | HTTP request, Eventarc event, Pub/Sub push | stateless instances behind a stable URL, autoscaled per request |
| **Job** | manual, schedule, or API | runs to completion across N tasks, no URL, no request handling |
| **Worker pool** | nothing external | always-on instances for pull workloads (Pub/Sub pull, Kafka, RabbitMQ) |

A process that polls a queue in a background thread of a *service* is a common mistake: the
service scales on request volume, so with no requests it scales to zero and the poller stops.
That workload is a worker pool or a job.

## Revisions are immutable

Every `gcloud run deploy` creates a new revision. The revision's container image,
environment variables, resource limits, concurrency and revision-level scaling bounds cannot
be edited afterwards — changing any of them produces another revision. Traffic assignment,
by contrast, lives on the *service* and can be moved between existing revisions with no
deploy at all. That split is what makes rollback instant: the previous revision still exists
and still works.

## Concurrency

One instance handles many requests at once. The default is not what most sources say:

- Created via **gcloud CLI or Terraform**: maximum concurrency defaults to **80 × the number
  of vCPUs** (so a 4-vCPU service starts at 320).
- Created via the **Google Cloud console**: a flat **80**.
- The ceiling in every case is **1000**.
- The default applies **only when the service is first created**. Later deploys of new
  revisions do not re-derive it, so changing `--cpu` on an existing service does not change
  its concurrency.

Lower it when the container cannot serve requests in parallel (single-threaded runtimes,
a per-request in-memory model, a fixed-size database connection pool). Setting
`--concurrency=1` turns Cloud Run into one-request-per-instance and multiplies instance count
and cost accordingly. Raise it when handlers are I/O-bound and cheap.

Concurrency, CPU and the connection pool are one budget: with concurrency 80 and a pool of
100 per instance, 50 instances open 5000 connections and a `db-custom-2-7680` Cloud SQL
instance with `max_connections=100` refuses almost all of them. Size the pool as
`max_connections / expected instances`, not per request.

## Two pairs of scaling flags

This is the distinction that the CLI help makes and almost every other source misses:

| Flag | Scope | Mutability |
|---|---|---|
| `--min-instances`, `--max-instances` | the **revision** | "immutably set on each new Revision" — changing the value deploys another revision |
| `--min`, `--max` | the **service** | divided among all revisions receiving traffic; "can be modified without deploying a new Revision" |

Use `--min`/`--max` for operational capacity changes (scaling up for a launch, dropping
warm instances overnight) — they do not roll your image. Use `--min-instances`/
`--max-instances` when the bound is a property of that particular revision.

`--max-instances` is also a cost fuse and a downstream protection: without it, a traffic spike
can open more database connections than the database will accept and turn a slow service into
a hard outage.

## Request timeout

Default **300 seconds (5 minutes)**, maximum **3600 seconds (60 minutes)** for services. A
request killed at exactly five minutes with no application log line is this default, not a
load balancer or a client. Raising it is legitimate for long uploads and streaming responses;
it is not a fix for a request that hangs, because the instance stays occupied for the whole
window and concurrency is consumed the entire time.

Above roughly 15 minutes, design for retries: clients disconnect, and Cloud Run does not
resume a request across instances.

For event-driven invocations the *trigger's* timeout applies as well — an Eventarc, Pub/Sub
push or Cloud Scheduler ack deadline shorter than the Cloud Run timeout produces a redelivery
while the first attempt is still running.

## CPU allocation and billing mode

Two billing behaviours, controlled by `--cpu-throttling` / `--no-cpu-throttling`:

- **Request-based billing (default)** — the instance is charged while starting, handling a
  request, and shutting down. Outside a request the CPU is throttled to near zero.
- **Instance-based billing** (`--no-cpu-throttling`, "CPU always allocated") — charged for the
  whole instance lifetime, and background work between requests actually runs.

Any code that continues after the response is written — flushing a metrics buffer, finishing
an async write, a background timer — silently does not run under the default. The symptom is
"the last few log lines never appear" or "some writes are missing under low traffic". Either
finish the work before responding, or switch to instance-based billing and accept the cost.

## Cold starts

`--cpu-boost` (startup CPU boost) is **enabled by default on new services**. Finding
`run.googleapis.com/startup-cpu-boost: "false"` in a service YAML means someone opted out;
that is a bug to remove, not a feature to discover.

The levers that actually move cold start, in order of effect:

1. `--min-instances`/`--min` above zero — keeps warm instances, billed at a reduced idle rate
   but not free.
2. Shrink the image and defer work out of module import. Most of a "slow cold start" is
   application initialisation, not Cloud Run.
3. Second-generation execution environment costs more startup latency than first generation;
   if cold start dominates and you do not need full Linux compatibility, gen1 starts faster.
4. Lazily open connections rather than opening a full pool at import time.

## Execution environment

| | gen1 | gen2 |
|---|---|---|
| Sandbox | gVisor, syscall emulation | microVM, full Linux |
| Cold start | faster | slower |
| CPU / network throughput | lower | higher, better under packet loss |
| Needs it | most HTTP services | anything using unsupported syscalls, network filesystems, high throughput |

`--execution-environment=gen2` is required for some features (network file system mounts, for
example) and is selected automatically when you request one of them.

## Shipping a change safely

Deploy without traffic, tag it, verify against the tag URL, then shift:

```bash
gcloud run deploy checkout-api --project=PROJECT_ID --region=us-central1 \
  --image=us-central1-docker.pkg.dev/PROJECT_ID/api/checkout:GIT_SHA \
  --no-traffic --tag=canary --quiet

# tagged URL: https://canary---checkout-api-<hash>-uc.a.run.app
gcloud run services update-traffic checkout-api --project=PROJECT_ID --region=us-central1 \
  --to-tags=canary=10 --quiet

# promote
gcloud run services update-traffic checkout-api --project=PROJECT_ID --region=us-central1 \
  --to-revisions=checkout-api-00042-abc=100 --quiet
```

- `--tag` gives the revision its own permanent URL, reachable even at 0% traffic. That is how
  you smoke-test the exact artefact before users see it.
- Rollback is `--to-revisions=<previous>=100`. It takes seconds and does not rebuild anything.
- `--to-latest` pins traffic to whatever the newest ready revision is, which re-enables
  deploy-straight-to-production. A service whose `traffic` block says
  `latestRevision: true` at 100% has no canary step available without changing that first.

Use `--revision-suffix=GIT_SHA` so revision names are traceable to a commit instead of
`-00042-abc`.

## Identity and access

- `--service-account=` sets the **runtime** identity. Omitting it falls back to the Compute
  Engine default service account, which in older organizations holds `roles/editor` — a web
  service with project-wide write access. Always set it.
- `--allow-unauthenticated` adds `allUsers` as `roles/run.invoker`. For a private service,
  grant `roles/run.invoker` to the specific caller's service account instead and have it send
  an ID token.
- `--no-invoker-iam-check` disables the IAM check entirely so another layer (an external
  load balancer with IAP, for example) can own authorization. Turning it on without that layer
  publishes the service.
- The deployer needs `roles/iam.serviceAccountUser` on the runtime service account, not just
  `roles/run.admin` — the "act as" permission is a separate grant and is the most common
  first-deploy 403.

## Reaching a VPC and a database

Two mechanisms:

- **Direct VPC egress** — assigns the instance an address in your subnet. Lower latency, no
  extra instances to pay for, needs enough free IPs in the subnet for the peak instance count.
- **Serverless VPC Access connector** — a managed pool of VMs that proxies the traffic. Costs
  for the connector instances whether or not traffic flows.

Prefer Direct VPC egress for new services; keep connectors where subnet address space is
tight. `--vpc-egress=private-ranges-only` (default) sends only RFC 1918 traffic through the
VPC; `all-traffic` routes public egress through it too, which is what you want when a static
egress IP via Cloud NAT is required for a third-party allow-list.

For Cloud SQL, `--add-cloudsql-instances=PROJECT:REGION:INSTANCE` mounts a Unix socket at
`/cloudsql/PROJECT:REGION:INSTANCE`, authenticated by the runtime service account holding
`roles/cloudsql.client`. No password on the wire, no IP allow-list, nothing to rotate.

## Building and image sources

- `gcloud run deploy --source .` builds with Cloud Build: buildpacks if there is no
  Dockerfile, the Dockerfile if there is one. The Cloud Build service account needs
  `roles/run.builder`.
- `--base-image` plus `--automatic-updates` lets Google rebase the application layer onto a
  patched base image without a rebuild by you — only with Google Cloud buildpacks base images.
- `gcloud beta run deploy --source . --no-build --base-image=... --command=...` skips Cloud
  Build entirely and uploads the artefact, which is much faster for iteration.
- Prefer Artifact Registry over Docker Hub: Docker Hub images are cached for up to an hour,
  so a pushed fix can deploy stale. Cloud Run copies the image at deploy time and does not
  re-pull on instance start, so a mutable tag like `:latest` pins to whatever the tag meant at
  deploy — deploy by digest or by an immutable tag if you need to know what is running.

Dockerfile authoring, multi-stage builds and image hardening are not this skill's subject —
use the `containers` skill.

## Jobs

```bash
gcloud run jobs create import-orders --project=PROJECT_ID --region=us-central1 \
  --image=IMAGE --tasks=50 --parallelism=10 --max-retries=3 --task-timeout=30m --quiet
gcloud run jobs execute import-orders --region=us-central1 --wait --quiet
```

- `--tasks` up to 10,000. Each task gets `CLOUD_RUN_TASK_INDEX` (0-based) and
  `CLOUD_RUN_TASK_COUNT`; partition work from those, not from a queue.
- `--max-retries` defaults to 3, range 0–10. When one task exceeds it the whole execution is
  marked failed — the other tasks still run to completion.
- `--task-timeout` defaults to 10 minutes, maximum 168 hours (7 days); 1 hour for tasks using
  GPUs.
- `--parallelism` caps concurrent tasks. Unset means as many as possible at once, which is how
  a job exhausts a database's connection limit on its first run.
- Without `--wait`, `execute` returns as soon as the execution is created, so a pipeline step
  that does not wait reports success for a job that later fails.

## What breaks on first deploy

- **Listening on `127.0.0.1`.** The container must listen on `0.0.0.0` and on the port in
  `$PORT` (8080 unless `--port` says otherwise). Binding localhost produces a container that
  starts fine and fails the health check.
- **Writing to the local filesystem.** The root filesystem is in-memory: writes count against
  the memory limit, and an instance that fills it is killed with an OOM, not a disk error.
- **Assuming the instance survives between requests.** In-process caches, sessions and
  scheduled timers do not survive scale-in.
- **`namespace` in the service YAML.** It holds the project *number*, not the project ID;
  hand-written YAML with the ID in that field fails to apply.

<!-- sources: gcp-docs, google-skills, cloud-run-mcp, google-agents-cli -->
