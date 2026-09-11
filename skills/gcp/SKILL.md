---
name: gcp
description: "Guides Google Cloud control-plane and architecture work: gcloud CLI discipline and its silent defaults, the organization/folder/project hierarchy and organization policy, IAM allow and deny policies, service accounts and Workload Identity Federation, Cloud Run revisions, concurrency, traffic splitting and cold starts, the GKE cluster control plane, Cloud SQL and managed data service selection, Cloud Storage classes and lifecycle, Cloud Logging and Cloud Monitoring as products, cost attribution, budgets and quotas, and Architecture Framework reviews. Use when writing or reviewing gcloud commands, auditing a project IAM policy, deploying or debugging Cloud Run, sizing a GKE cluster, or explaining a Google Cloud bill. Do not use for Kubernetes manifests or container images (use the `containers` skill), Terraform HCL (use the `terraform` skill), OpenTelemetry instrumentation or alert pipelines (use the `observability` skill), AWS, Azure, Firebase, or Gemini API application development."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: platform
---

# gcp

## Scope

Covers the Google Cloud control plane and the architecture decisions that sit on top of it:
the `gcloud` CLI and its defaults, the resource hierarchy and organization policy, IAM
(predefined and custom roles, conditions, deny policies, service accounts, Workload Identity
Federation), Cloud Run, the GKE cluster and node-pool control plane, Cloud SQL and the choice
between managed data services, Cloud Storage, Cloud Logging and Cloud Monitoring as products,
cost and quota management, and Well-Architected reviews against Google's Architecture
Framework.

Verified against **Google Cloud SDK 584.0.0**. Every rule below that depends on a CLI default
carries a `[verified]` marker and was read from that release's `--help` output; rules marked
`[official]` come from cloud.google.com and were not reproduced locally because doing so would
create billable resources.

Not covered:

- Kubernetes manifests, Helm, Kustomize, probes, resource limits, Pod security, Dockerfiles
  and image builds — including for GKE workloads. Use the `containers` skill. This skill stops
  at the cluster boundary: creating the cluster and its node pools, its network mode, its
  identity integration and its upgrade channel.
- Terraform and OpenTofu: HCL, modules, state, `terraform test`, provider development. Use the
  `terraform` skill. Where this skill shows infrastructure as code it uses Google's own tools.
- OpenTelemetry instrumentation, Collector configuration, semantic conventions, RED/USE metric
  design, SLO definition and alert routing. Those belong to the `observability` skill; what
  belongs here is the Cloud Logging and Cloud Monitoring **product surface** — query language,
  buckets, sinks, retention, quotas and billing.
- Index and mapping design or query DSL for search backends. Use the `elasticsearch` skill.
  SQL schema, indexing and `EXPLAIN` for Postgres. Use the `postgres` skill.
- AWS and Azure. This skill writes only Google Cloud; cross-cloud comparison stays to a
  sentence where a decision genuinely depends on it.
- Firebase, and Gemini / Vertex AI application development. No skill in this library covers
  either yet; say so rather than improvising.

Paths below are relative to this skill's directory.

## Core rules

1. Run `gcloud help <leaf command>` before writing any command, and treat memory of flag names
   and defaults as stale. Validation is not transitive from the parent group, and defaults
   differ between sibling leaves (gcloud 584.0.0) `[verified]`.
2. Pass `--project=PROJECT_ID` explicitly on every command that touches a resource. Relying on
   the active configuration makes the target depend on invisible local state, and the classic
   production accident is a correct command aimed at the wrong project.
3. Pass `--quiet` on every command an agent executes. Without a TTY, any prompt — a delete
   confirmation, an unspecified region, a component install — blocks until the harness kills
   it (gcloud 584.0.0) `[verified]`.
4. Never run a `list` without `--limit`, `--filter` or `--format`. Discover the schema first
   with `... list --limit=1 --format=json`, then project only the fields you need.
5. Ask for human approval before any IAM mutation, any `delete`, any `gcloud billing`,
   `gcloud organizations` or `gcloud kms` call, and before `gcloud services enable` — enabling
   an API can begin provisioning and billing. Assume required APIs are enabled; when a call
   fails, the `SERVICE_DISABLED` error names the exact API to ask about.
6. Deny policies are evaluated before allow policies, so a deny is the only way to make a
   permission stay unavailable no matter who grants it later (IAM v2) `[official]`. Removing a
   binding is a state any project owner can undo.
7. You cannot revoke an inherited role at a lower level. Allow policies are the additive union
   of every ancestor; a narrower policy on the project changes nothing about a folder grant.
8. Never create downloaded service account keys. Use an attached identity on Google Cloud,
   Workload Identity Federation off it, or `--impersonate-service-account` for one-off human
   access, and enforce `iam.disableServiceAccountKeyCreation`.
9. On a Workload Identity Federation provider, always set an attribute condition, and condition
   on the IdP's numeric IDs (`repository_id`, `repository_owner_id`) rather than names. Without
   the condition any token the IdP issues is accepted; with name-based conditions, a deleted
   repository or org name can be re-registered by someone else `[official]`.
10. The Compute Engine default service account holds `roles/editor` unless the
    `iam.automaticIamGrantsForDefaultServiceAccounts` constraint is enforced, and that
    constraint is enforced by default **only for organizations created after 2024-05-03**
    `[official]`. Older organizations must set it and strip the existing grants.
11. IAM changes take about 2 minutes and can take 7 minutes or longer to propagate `[official]`.
    Verification immediately after a change can report a false result, and a revocation is not
    incident containment — disable the account or rotate the credential as well.
12. `gcloud logging read` defaults to `--freshness=1d` (gcloud 584.0.0) `[verified]`. A query
    for anything older returns empty and exits zero; a `timestamp>=` clause in the filter does
    not override it. Set `--freshness` explicitly on every incident query.
13. Logging Query Language takes double-quoted string literals and uppercase `AND`/`OR`/`NOT`
    only. Match audit `protoPayload.methodName` with `SEARCH(...)`, not `=` (version prefixes
    vary) and not `:` (substring false positives) `[official]`.
14. Cloud Run maximum concurrency defaults to **80 × vCPU** when the service is created via the
    CLI or Terraform and to a flat **80** via the console, with a ceiling of 1000; the default
    is applied only at service creation `[official]`. Quoting a flat 80 for a multi-vCPU
    service is wrong.
15. `--min-instances`/`--max-instances` are set immutably on each Cloud Run revision, so
    changing them deploys a new revision; `--min`/`--max` are service-level and change without
    a deploy (gcloud 584.0.0) `[verified]`. Use the service-level pair for capacity changes.
16. Cloud Run's request timeout defaults to 300 s and maxes at 3600 s `[official]`. A request
    cut off at exactly five minutes with no application log is this default.
17. Startup CPU boost is enabled by default on new Cloud Run services (gcloud 584.0.0)
    `[verified]`. An explicit `startup-cpu-boost: "false"` in a service is an opt-out to
    remove, not a feature to discover.
18. Ship a Cloud Run change as `deploy --no-traffic --tag=<tag>`, verify on the tag URL, then
    `services update-traffic --to-tags=<tag>=10`. A service whose traffic block is
    `latestRevision: true` at 100% sends every deploy straight to production.
19. `gcloud sql instances create` defaults `--region` to `us-central` (the legacy region name,
    not `us-central1`), `--database-version` to `MYSQL_8_0`, and `--availability-type` to
    `zonal` (gcloud 584.0.0) `[verified]`. Region and engine are immutable; production needs
    `--availability-type=regional`.
20. On Cloud SQL Enterprise, point-in-time recovery retains at most **7 days** of transaction
    logs; Enterprise Plus allows up to 35 (gcloud 584.0.0) `[verified]`. A 30-day recovery
    requirement is an edition decision made before the instance exists.
21. `gcloud storage buckets create` defaults to the `us` multi-region and to uniform
    bucket-level access **off** (gcloud 584.0.0) `[verified]`; the console wizard defaults it
    on. Location cannot be changed after creation.
22. Cloud Storage minimum storage durations are Nearline 30 days, Coldline 90, Archive 365, and
    the remainder is billed on early deletion or re-class `[official]`. Transitioning to a cold
    class shortly before deleting raises the bill.
23. Soft delete is enabled by default with 7-day retention and soft-deleted bytes are billed
    `[official]`. On a high-churn bucket it is a large line item that no object listing shows.
24. Lifecycle configuration changes take up to 24 hours to take effect and Cloud Storage may
    act on the previous configuration during that window `[official]`. Lifecycle is not a
    mechanism for prompt or precise deletion.
25. Default to GKE Autopilot; choose Standard only for a requirement Autopilot cannot express.
    Clusters with an SLO are regional, and a cluster created with neither a channel nor a
    version enrols in the REGULAR channel with node auto-upgrade on (gcloud 584.0.0)
    `[verified]`.

## Workflows

### Deploy or change a Cloud Run service

- [ ] Read the current service: `gcloud run services describe NAME --region=R --format=yaml`.
- [ ] Confirm the runtime identity is a dedicated service account, not the Compute Engine
      default.
- [ ] Decide concurrency, CPU, memory and timeout against the measured request profile; check
      `max instances × per-instance pool size` against the database's `max_connections`.
- [ ] Deploy with `--no-traffic --tag=`, pinned by image digest and `--revision-suffix=GIT_SHA`.
- [ ] Exercise the tag URL directly.
- [ ] Shift 10% with `update-traffic --to-tags=`, watch latency, error rate, instance count and
      database connections, then promote with `--to-revisions=<rev>=100`.
- [ ] **Gate:** `gcloud run services describe NAME --region=R --format="value(status.traffic)"`
      shows the intended split, and a rollback command to the previous revision is written down
      before promotion.

### Audit a project's IAM

- [ ] `gcloud projects get-iam-policy PROJECT_ID --format=yaml` — read with policy version 3 so
      conditional bindings are not silently dropped.
- [ ] Flag every basic role, every `allUsers`/`allAuthenticatedUsers`, and every workload
      running as a default service account.
- [ ] List service account keys: `gcloud iam service-accounts keys list --iam-account=... --managed-by=user`.
      Any user-managed key is a finding.
- [ ] List deny policies and organization policies at project, folder and organization; an
      absent guardrail is as much a finding as a bad binding.
- [ ] Propose the narrowest predefined role per principal; use the IAM recommender's 90-day
      analysis as a candidate list, not a patch.
- [ ] **Gate:** for each change, a verification command *and* an acknowledgement that IAM takes
      2–7 minutes to propagate, so the verification is run after that window.

### Investigate a production failure from signals

- [ ] Fix the time window first, and set `--freshness` wider than it.
- [ ] Request layer: `resource.type="cloud_run_revision"` (or the correct type from the topic
      router's logging reference) filtered on `httpRequest.status>=500`, `--order=asc`.
- [ ] Application layer: same resource, `severity>=ERROR`, correlate by `trace`.
- [ ] Dependency layer: the database's own logs and its connection metrics.
- [ ] Control plane: `gcloud <service> operations list` for a maintenance event or an upgrade
      that coincides.
- [ ] **Gate:** a named root cause with a quoted log line or metric series behind it, or an
      explicit statement of which signal is missing and what must be enabled to get it.

Where a local failure can be reproduced, use the `debugging` skill; instrumentation, trace
propagation and alert design are the `observability` skill's subject.

### Review an architecture or a bill

- [ ] Inventory first: `gcloud asset search-all-resources --scope=projects/PROJECT_ID`.
- [ ] Walk the six Architecture Framework pillars, recording the observed configuration for
      each check rather than an impression.
- [ ] For cost, query the BigQuery billing export grouped by service and SKU and rank by
      **delta** against the previous period, not by absolute size.
- [ ] Attribute the top delta down to a project, then a label, then a resource.
- [ ] Order findings by consequence, not by pillar.
- [ ] **Gate:** every finding carries the exact `gcloud` command or setting that fixes it, what
      it costs or breaks, and — for cost work — the expected monthly delta.

## Topic router

| Topic | Read when | File |
|---|---|---|
| gcloud CLI, auth, ADC, impersonation, filters and formats | writing or debugging any command; "which credential is this using" | `references/gcloud-cli.md` |
| Organization, folders, projects, org policy, labels vs tags, Shared VPC | designing a landing zone; enforcing a guardrail; a project-level accident | `references/resource-hierarchy.md` |
| Roles, conditions, deny policies, service accounts, Workload Identity Federation | auditing or changing access; diagnosing a 403 | `references/iam.md` |
| Cloud Run revisions, concurrency, scaling, timeouts, traffic, jobs, VPC egress | deploying, tuning or rolling back a service; cold starts | `references/cloud-run.md` |
| GKE clusters, node pools, channels, upgrades, VPC-native, Workload Identity for GKE | creating or operating a cluster; an upgrade or IP-exhaustion question | `references/gke-control-plane.md` |
| Cloud SQL settings, editions, HA, backups, connectivity; choosing between managed data services | standing up or reviewing a database; picking Spanner vs Cloud SQL vs Firestore | `references/data-services.md` |
| Buckets, storage classes, lifecycle, soft delete, access, 403/404 triage | a storage bill, a lifecycle policy, or an access failure | `references/cloud-storage.md` |
| Logging query language, buckets, sinks, retention, pricing; Monitoring metric kinds and quotas | pulling logs, routing them, or explaining an observability bill | `references/logging-monitoring.md` |
| Quota types and increases, budgets, billing export, commitments, discounts | a cost investigation; a `RESOURCE_EXHAUSTED`; capacity planning | `references/cost-and-quotas.md` |
| Compute and region selection, the six Well-Architected pillars as checks | a design review or a production-readiness review | `references/architecture-framework.md` |

## Output format

For a review (IAM, architecture, cost), group findings by severity and give each one evidence
and a fix:

```
## Blocking

- iam-policy.yaml:12 - serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com holds roles/editor
  Why: the default Compute Engine identity; any workload without an explicit --service-account runs with
       project-wide write access. This organization predates 2024-05-03, so the automatic grant applied.
  Fix: gcloud resource-manager org-policies enable-enforce iam.automaticIamGrantsForDefaultServiceAccounts --organization=ORG_ID
       gcloud projects remove-iam-policy-binding PROJECT_ID --member=serviceAccount:... --role=roles/editor
  Verify (after 7 minutes): gcloud projects get-iam-policy PROJECT_ID --flatten=bindings --filter="bindings.members:...-compute@"

## High
...

## Not checkable here
- Data Access audit logs are disabled, so object-read history for gs://... cannot be established.
```

For a change, give the commands in execution order, mark which need human approval, and end
with the rollback command.

## Environment

`gcloud` is required. Install the CLI, then:

```bash
gcloud version                       # confirm the release before quoting any default
gcloud auth login                    # the CLI's own credential
gcloud auth application-default login  # separate: what client libraries and Terraform use
gcloud components install gke-gcloud-auth-plugin   # required for kubectl against GKE
```

`gcloud help <leaf command>` works fully offline and is the authority for flags and defaults in
the installed release.

<!-- sources: gcp-docs, google-skills, gcs-extension, optimnow-finops, bagelhole-devops, cloud-run-mcp, google-agents-cli -->
