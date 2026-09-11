# gcloud CLI

Verified against: Google Cloud SDK 584.0.0 (core 2026.09.04). Flag text quoted below was read
from `--help` output of that release.

## Contents

- [The one rule that prevents most failures](#the-one-rule-that-prevents-most-failures)
- [Non-interactive execution](#non-interactive-execution)
- [Scoping every command](#scoping-every-command)
- [Cutting output down](#cutting-output-down)
- [Filters](#filters)
- [Authentication: which credential is actually in use](#authentication-which-credential-is-actually-in-use)
- [Impersonation instead of keys](#impersonation-instead-of-keys)
- [Configurations](#configurations)
- [Long-running operations](#long-running-operations)
- [Operations that need a human](#operations-that-need-a-human)
- [Alpha, beta and components](#alpha-beta-and-components)

## The one rule that prevents most failures

Run `gcloud help <leaf command>` before writing the command, every time. Not `gcloud help
compute` — `gcloud help compute instances create`. Validation is not transitive: a flag that
exists on one leaf under a group frequently does not exist on its sibling, and flag *defaults*
differ between leaves that look identical. Two examples from the same release:

- `gcloud sql instances create` defaults `--region` to `us-central` — the legacy region name,
  not `us-central1`. Nothing else in the CLI defaults to that value.
- `gcloud run deploy` has both `--min-instances` and `--min`. They are different features —
  one is revision-scoped and immutable, the other service-scoped and mutable — and no amount
  of reading the `gcloud run` group help reveals that.

Flag surfaces also move between releases. `--tier` on `gcloud container clusters create-auto`
is marked DEPRECATED in 584.0.0; `gcloud run` has grown `multi-region-services` and
`compose up` subgroups. Memory of the CLI is stale by construction; the local help output is
not.

## Non-interactive execution

Pass `--quiet` (`-q`) on every command an agent runs. Without a TTY, a command that wants
confirmation — deletes, unspecified regions, component installs — blocks until the harness
times it out, and the transcript shows nothing useful. `--quiet` forces the default answer or
an immediate explicit error instead.

The same applies to location flags. Most regional and zonal resources prompt for a location
when `--region`/`--zone`/`--location` is omitted. Discover locations first rather than
guessing:

```bash
gcloud compute regions list --project=PROJECT_ID --format="value(name)" --limit=50
gcloud artifacts locations list --project=PROJECT_ID --format="value(name)" --limit=50
```

`gcloud <group> locations list` works for most modern services; Compute Engine is the
exception with its own `regions list` / `zones list`.

## Scoping every command

Always pass `--project=PROJECT_ID` explicitly on anything that touches a resource. Relying on
`gcloud config get-value project` means the command's target depends on invisible local state,
and the most common production accident is a correct command aimed at the wrong project.

Project **ID** (`acme-prod`, immutable, globally unique) and project **number**
(`482910337712`) both work in `--project`, but service agents and generated resource names use
the number, so both appear in real output. They are not interchangeable in strings you build
by hand — a Cloud Run `namespace:` field holds the number, an IAM binding holds the ID.

## Cutting output down

Never run a `list` without at least one of `--limit`, `--filter`, `--format`. An unscoped list
of instances, buckets or log entries can be tens of thousands of rows.

Discover the schema before projecting fields:

```bash
gcloud run services list --project=PROJECT_ID --limit=1 --format=json
```

Then project only what is needed:

```bash
gcloud run services list --project=PROJECT_ID --region=us-central1 \
  --format="json(metadata.name, status.url, status.latestReadyRevisionName)"
```

`--format` is a projection language of its own (`value()`, `table()`, `json()`, `csv()`, plus
transforms like `.date()`, `.list()`, `.segment()`). `gcloud topic formats` and
`gcloud topic projections` document it; read those rather than post-processing with `jq`,
because the projection runs before the data leaves the client and keeps the context small.

`--format="value(...)"` emits bare values with no quoting or header — the right choice when
feeding another command.

## Filters

`--filter` runs server-side where the API supports it, so it is cheaper than filtering
locally. Syntax notes that catch people out:

- `:` is "contains / matches", `=` is equality. `--filter="name:web"` matches `web-1` and
  `myweb`; `--filter="name=web"` matches only `web`.
- Do not quote the right side of `:`. Quote the whole flag value instead.
- `labels.env=prod` reaches into map fields; `NOT`, `AND`, `OR` are uppercase.
- Timestamps compare against a duration expression:
  `--filter="creationTimestamp<-P7D"` is "older than seven days".

`gcloud topic filters` is the reference.

## Authentication: which credential is actually in use

Three distinct credential stores exist, and confusing them produces "works in my shell, fails
in the code" reports:

| Store | Set by | Used by |
|---|---|---|
| gcloud's own account | `gcloud auth login` | the `gcloud` command itself |
| Application Default Credentials (ADC) | `gcloud auth application-default login` | client libraries, Terraform, anything using ADC |
| Attached identity | the runtime (Cloud Run, GKE, GCE) | everything on that instance, via the metadata server |

`gcloud auth login` does **not** set ADC, and `gcloud auth application-default login` does not
change gcloud's own account. Check both: `gcloud auth list` and
`gcloud auth application-default print-access-token`.

ADC resolution order is: `GOOGLE_APPLICATION_CREDENTIALS` → the user ADC file written by
`gcloud auth application-default login` → the attached service account from the metadata
server. On a Google Cloud runtime the third entry is what you want; a stale ADC file on a
developer laptop silently shadows it.

`gcloud auth application-default login` also writes a **quota project** into the ADC file
(from `billing/quota_project` or `core/project`). That project — not the project the resource
lives in — is billed for API quota when a client library calls Google APIs. If a library
reports `SERVICE_DISABLED` or quota errors for a project you never touched, the quota project
is the cause; `--disable-quota-project` or `gcloud auth application-default set-quota-project`
fixes it.

## Impersonation instead of keys

`--impersonate-service-account=SA_EMAIL` makes a single invocation act as a service account
without any key material. The caller needs `roles/iam.serviceAccountTokenCreator` on the
target. Delegation chains work too —
`--impersonate-service-account=SA_1,SA_2` requires the active account to hold token-creator on
`SA_1` and `SA_1` to hold it on `SA_2`; `SA_1` is the impersonated account and `SA_2` the
delegate. Use this instead of `gcloud auth activate-service-account --key-file=` for anything
that would otherwise need a downloaded key.

## Long-running operations

Cluster creation, Cloud SQL instance creation, and most `update` calls on big resources are
long-running operations. `--async` returns the operation name immediately where it is
supported (not every command has it). Poll with the service's own operations group —
`gcloud container operations describe`, `gcloud sql operations wait`, and so on; there is no
single global `gcloud operations describe` that covers every service.

Without `--async`, the command blocks and a harness timeout can kill the client while the
server-side operation continues — leaving a half-created resource and no operation id in the
transcript. For anything that takes minutes, prefer `--async` plus explicit polling.

## Operations that need a human

Ask before running, regardless of how confident the plan is:

- any IAM allow/deny policy, role, or binding mutation — privilege escalation and lockout are
  both one command away, and the blast radius is invisible in the command text
- `gcloud * delete` on anything stateful
- `gcloud billing *` — changes what is charged and can detach a billing account, stopping
  every service in the project
- `gcloud organizations *` and `gcloud resource-manager org-policies *` — org-level scope
- `gcloud kms *` — destroying or disabling a key version makes the data it wraps unreadable
- `gcloud services enable` — enabling an API can start provisioning and billing. Assume the
  APIs you need are enabled; when a call fails with `SERVICE_DISABLED`, the error names the
  exact API, and *that* is the moment to ask.

When a command supports `--dry-run` or `--validate-only`, run that form first and show its
output. `gcloud org-policies set-policy`, `gcloud dns record-sets transaction execute` and
several others support it; the help output for the leaf command is the only reliable way to
know.

## Alpha, beta and components

`gcloud alpha`/`gcloud beta` surfaces need their component installed and will prompt to
install it — another reason `--quiet` matters in automation, and a reason to install
components explicitly in CI rather than at first use. Commands move from `beta` to GA without
notice in the release notes you read; if `gcloud beta run deploy --no-build` fails as unknown,
check whether the flag graduated to `gcloud run deploy` in the installed version before
concluding it was removed.

<!-- sources: google-skills, gcp-docs, cloud-run-mcp -->
