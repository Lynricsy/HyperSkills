# Managed data services: choosing one, and running Cloud SQL

SQL schema design, indexing, `EXPLAIN` and query tuning are the `postgres` skill's subject.
This reference covers the Google Cloud control plane: which managed service fits, and the
instance-level settings on Cloud SQL that decide whether it survives production.

Verified against: Google Cloud SDK 584.0.0 (`gcloud sql` help text quoted below is from that
release).

## Contents

- [Picking the service](#picking-the-service)
- [Cloud SQL editions](#cloud-sql-editions)
- [Create-time settings you cannot change later](#create-time-settings-you-cannot-change-later)
- [Availability](#availability)
- [Backups and point-in-time recovery](#backups-and-point-in-time-recovery)
- [Connectivity](#connectivity)
- [Replicas and read pools](#replicas-and-read-pools)
- [Maintenance](#maintenance)
- [A production instance](#a-production-instance)
- [Diagnosing a slow or refusing instance](#diagnosing-a-slow-or-refusing-instance)

## Picking the service

| Need | Service | Why not the neighbour |
|---|---|---|
| Relational, single region, standard Postgres/MySQL/SQL Server | **Cloud SQL** | the default; you get the real engine, extensions and wire protocol |
| Relational Postgres, higher throughput, HTAP, sub-second failover | **AlloyDB** | Postgres-compatible but not Postgres: no arbitrary extensions, higher floor cost |
| Relational, horizontal scale, multi-region strong consistency | **Spanner** | pays for global consistency with a different SQL dialect, no extensions, and a high entry price |
| Document, mobile/web clients, offline sync | **Firestore** | no joins, no aggregations beyond count/sum/avg, query shape must be known at index time |
| Wide-column, very high write rate, time series | **Bigtable** | single-row transactions only, no secondary indexes; the row key *is* the design |
| Analytics over large tables | **BigQuery** | not an OLTP store: no single-row updates at transactional latency |
| Cache, session store, queues | **Memorystore** (Redis/Valkey/Memcached) | in-memory, durability is opt-in and partial |

The common mistake is reaching for Spanner because a service is "important". Spanner earns its
cost when a single region's write throughput or its failure domain is genuinely the limit; a
regional Cloud SQL instance with a read replica handles far more traffic than most teams
think, and the migration path from Cloud SQL to AlloyDB or Spanner later is real work either
way.

## Cloud SQL editions

| | Enterprise | Enterprise Plus |
|---|---|---|
| Machine sizing | `--cpu` + `--memory` custom, or `--tier` for shared-core | `--tier` only, from a fixed list (`--cpu`/`--memory` are rejected) |
| Retained automated backups (default) | 7 | 15 |
| Transaction log retention for PITR | default 7 days, **maximum 7** | default 14 days, maximum 35 |
| Data cache | no | yes |
| Maintenance downtime | seconds-scale restart | near-zero downtime |

The PITR ceiling is the one that forces the choice: on Enterprise you cannot recover to a
point more than seven days back, whatever the backup retention says. If the compliance
requirement is 30 days of point-in-time recovery, that is an Enterprise Plus instance, decided
before creation.

## Create-time settings you cannot change later

- **Region.** `gcloud sql instances create` defaults `--region` to **`us-central`** — the
  legacy region name, not `us-central1`. An instance created with the default sits in a region
  the rest of your infrastructure is not in, and the only fix is a new instance plus a
  migration.
- **Database version.** Defaults to `MYSQL_8_0` when `--database-version` is omitted, which
  quietly produces a MySQL instance for a team that assumed Postgres. Current major versions
  accepted by this release include `POSTGRES_18`, `MYSQL_9_7` and `SQLSERVER_2025_ENTERPRISE`;
  minor versions are also accepted. Major-version upgrades in place are supported but are a
  planned operation, not a flag change.
- **Instance name.** Cannot be reused for about a week after deletion.
- **Edition.** Enterprise ↔ Enterprise Plus is an in-place upgrade for some paths and a
  migration for others; treat it as a create-time decision.

`--availability-type` and private IP *can* be changed later, but both restart the instance.

## Availability

`--availability-type` defaults to **`zonal`**: a single zone, no failover, and a zone incident
is an outage of unknown length. Production wants `regional`, which keeps a synchronous standby
in a second zone and fails over automatically.

Switching an existing instance to regional is an in-place update that restarts it — plan the
window rather than discovering the restart. High availability roughly doubles the instance
cost, because you are paying for the standby.

HA is not a backup: a bad migration replicates to the standby instantly. Backups and PITR
cover that; failover does not.

## Backups and point-in-time recovery

Automated backups are **on by default** (`--no-backup` disables them). Point-in-time recovery
is **not** — `--enable-point-in-time-recovery` must be passed explicitly, requires automated
backups, and needs enough storage for the write-ahead logs.

- `--retained-backups-count` defaults to 7 (Enterprise) / 15 (Enterprise Plus), range 1–365.
- `--retained-transaction-log-days` defaults to 7 (Enterprise, max 7) / 14 (Enterprise Plus,
  max 35).
- `--retain-backups-on-delete` keeps backups after the instance is deleted. Without it,
  deleting the instance deletes its backups.
- `--deletion-protection` blocks `gcloud sql instances delete`. Off by default. Turn it on for
  every instance that matters; it costs nothing.

Restoring a backup into the *same* instance overwrites it. Restore into a new instance first,
verify, then cut over.

## Connectivity

Ordered by preference:

1. **Cloud SQL Auth Proxy / language connectors.** The client authenticates with IAM, the
   connection is encrypted by the proxy, and nothing needs an IP allow-list. On Cloud Run,
   `--add-cloudsql-instances=PROJECT:REGION:INSTANCE` provides this as a Unix socket at
   `/cloudsql/PROJECT:REGION:INSTANCE`; the runtime service account needs
   `roles/cloudsql.client`.
2. **Private IP** via Private Service Connect or VPC peering. No public surface at all.
3. **Public IP with authorized networks.** Last resort, and `0.0.0.0/0` in the authorized
   network list is a publicly reachable database regardless of the password.

`--ssl-mode` controls whether unencrypted connections are accepted; `ENCRYPTED_ONLY` or
`TRUSTED_CLIENT_CERTIFICATE_REQUIRED` rather than the permissive default. The org policy
`sql.restrictPublicIp` closes the public path for the whole hierarchy and is the durable fix.

IAM database authentication (`--database-flags=cloudsql.iam_authentication=on` for Postgres)
lets users and service accounts connect with short-lived IAM credentials instead of a stored
password — the same argument as everywhere else in this skill.

`max_connections` is a database flag, and Cloud SQL's default for a small instance is low
enough that a Cloud Run service scaling to 50 instances with a pool of 10 exhausts it. Size
the application pool against `max_connections`, and reach for a pooler (PgBouncer, or the
managed connection pooling where available) before raising the flag.

## Replicas and read pools

- **Read replicas** are individually addressed instances with their own connection strings.
  Asynchronous: replica lag is real and a read-after-write against a replica returns stale
  data.
- **Read pools** (Enterprise Plus) put several read replicas behind one endpoint so the client
  does not load-balance by hand.
- A read replica can be promoted to a standalone primary. That is a one-way operation and it
  is the disaster-recovery path for a lost region — not the same thing as HA failover.
- Cross-region replicas add egress cost and lag; they exist for DR and for reads local to
  another region, not for extra capacity in the primary region.

## Maintenance

Set a maintenance window (`--maintenance-window-day`, `--maintenance-window-hour`) and a
`--maintenance-release-channel`. Without a window, Google picks the time. Enterprise instances
restart during maintenance; Enterprise Plus has near-zero downtime maintenance. Deny
maintenance periods exist for freeze windows.

## A production instance

```bash
gcloud sql instances create checkout-db \
  --project=PROJECT_ID \
  --database-version=POSTGRES_17 \
  --region=us-central1 \
  --edition=ENTERPRISE_PLUS \
  --tier=db-perf-optimized-N-4 \
  --availability-type=regional \
  --enable-point-in-time-recovery \
  --retained-transaction-log-days=14 \
  --deletion-protection \
  --no-assign-ip \
  --network=projects/PROJECT_ID/global/networks/prod-vpc \
  --maintenance-window-day=SUN --maintenance-window-hour=4 \
  --quiet
```

Every one of `--region`, `--database-version`, `--availability-type`, `--deletion-protection`
and `--no-assign-ip` is there because the default is wrong for production.

## Diagnosing a slow or refusing instance

1. **Connection refusals** are usually `max_connections`, not the network. Check
   `cloudsql.googleapis.com/database/postgresql/num_backends` in Cloud Monitoring against the
   flag value before touching connectivity.
2. **Sudden latency after a deploy** with unchanged queries is normally connection churn: a
   new revision opening a fresh pool per instance.
3. **Query Insights** (`--insights-config-query-insights-enabled`) is off by default and is
   the fastest way to find the expensive statement. Turn it on before the next incident, not
   during it.
4. **Storage auto-increase** (`--storage-auto-increase`) grows the disk automatically and
   never shrinks it. An instance that once filled with WAL keeps paying for the larger disk
   forever.
5. Instance-level metrics and logs live in Cloud Monitoring and Cloud Logging; query
   construction for those is in this skill's logging and monitoring reference. Statement-level
   tuning is the `postgres` skill's subject.

<!-- sources: gcp-docs, google-skills, bagelhole-devops -->
