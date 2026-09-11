# Choosing and sizing managed data services

Verified against: the DynamoDB, RDS/Aurora, Aurora DSQL, ElastiCache, S3 and Kinesis
developer guides on docs.aws.amazon.com. Quotas are per account and per region and most are
adjustable defaults — confirm with `aws service-quotas get-service-quota` before a number
drives a design.

## Contents

- [Start from the access pattern](#start-from-the-access-pattern)
- [DynamoDB](#dynamodb)
- [RDS and Aurora](#rds-and-aurora)
- [Aurora DSQL](#aurora-dsql)
- [ElastiCache and MemoryDB](#elasticache-and-memorydb)
- [S3](#s3)
- [Streaming: Kinesis, MSK, and when a queue is enough](#streaming-kinesis-msk-and-when-a-queue-is-enough)
- [OpenSearch Service](#opensearch-service)
- [The costs that arrive later](#the-costs-that-arrive-later)

## Start from the access pattern

The decision is rarely "which database is best". It is which constraints eliminate options:

| Constraint | What it rules out |
|---|---|
| Ad-hoc queries the team cannot enumerate in advance | DynamoDB as the primary store |
| Single-digit-millisecond reads at very high, spiky volume | A single relational writer |
| Strong cross-row transactions across many entities | Most key-value designs |
| Multi-region active-active writes | Single-writer Aurora, single-region DynamoDB tables |
| Scale to zero between bursts | Provisioned RDS, provisioned DynamoDB, ElastiCache node clusters |
| An existing PostgreSQL application with extensions | DynamoDB, DSQL (extension support is limited) |

Write the pattern down before comparing features, and price the **idle** case as well as the
peak: provisioned capacity, per-cluster-hour control planes and per-AZ endpoints charge
whether or not traffic arrives.

## DynamoDB

- Model for the access pattern, not the entities. Design work belongs before the table exists;
  changing the partition key later requires a new table and a migration, because the key is
  immutable and a change to it forces replacement in CloudFormation.
- An item is capped at 400 KB. Larger payloads go to S3 with the key stored in the item.
  `[official]`
- Default throughput quotas are 40,000 read and 40,000 write units per table (on-demand or
  provisioned), and 80,000 each per account for provisioned mode; on-demand tables have no
  account-level throughput quota. All adjustable. `[official]`
- Throughput is spread across partitions, so a hot partition key throttles while the table
  reports spare capacity. The fix is key design (add a suffix, shard the key), not more
  capacity.
- On-demand is the correct default: it removes a whole class of capacity incidents and is
  cheaper than over-provisioning. Switch to provisioned with auto-scaling only when the
  traffic is steady and measured, and note the switch is rate-limited.
- A GSI has its own capacity. Under-provisioning a GSI throttles **writes to the base table**,
  which is the least intuitive failure mode in the service.
- Enable point-in-time recovery on anything that matters and deletion protection on anything
  in production. Both are single properties and both prevent a category of incident.
- Streams are the integration point: they deliver in order per shard, at least once, with a
  24-hour retention. A consumer down for a day loses data.

## RDS and Aurora

- **Aurora over RDS** when you want storage that grows automatically, faster failover and up
  to fifteen low-lag readers; **RDS** when you need an engine or version Aurora does not offer,
  or when the workload is small enough that Aurora's minimum cost is the larger number.
- **Aurora Serverless v2** scales capacity in ACUs and can scale to zero after an idle period,
  which makes it the right shape for development and spiky internal tools. Cold resume adds
  latency — do not put a user-facing synchronous path behind a scale-to-zero cluster.
- Multi-AZ is availability, not backup, and not read scaling. An RDS Multi-AZ standby serves
  no traffic; Aurora replicas do. A failover is measured in tens of seconds and drops every
  open connection, so the application needs reconnect logic regardless.
- Storage autoscaling has a ceiling you set. Hitting it is an outage; alarm on free storage,
  not just on CPU.
- The most common RDS surprise is connection exhaustion: `max_connections` scales with
  instance class, and serverless-style compute multiplies connection count by concurrency.
  Put RDS Proxy in front of anything Lambda-backed, or pool in the application.
- Backups and snapshots are encrypted only if the instance is; you cannot encrypt an existing
  unencrypted instance in place — you restore a snapshot into a new encrypted instance.
- Major version upgrades are one-way. Test against a restored snapshot, and read the engine's
  deprecation schedule: AWS force-upgrades at end of standard support.

## Aurora DSQL

A serverless, PostgreSQL-compatible distributed SQL database with active-active multi-region
writes. Its constraints are unusual enough that "PostgreSQL-compatible" misleads people:

| Limit | Default |
|---|---|
| Rows per transaction | 3,000 |
| Data per transaction | 10 MiB |
| Transaction duration | 5 minutes |
| Connections per cluster | 10,000 |
| Connection duration | 60 minutes |
| Auth token expiry | 15 minutes |
| Indexes per table | 24 |

`[official]` — these are the values AWS publishes as defaults; verify before sizing a batch
job against them.

Concurrency control is optimistic, so a committing transaction can fail with `40001` and
**must** be retried by the application. That is not an error condition to log; it is the
normal control flow, and code written against single-writer PostgreSQL will not have it.
Foreign-key violations (`23503`) are not retryable and must be handled differently.

The 3,000-row transaction limit means bulk loading is a batching problem, and the 60-minute
connection cap means long-lived pools need rotation. DDL runs one statement per transaction,
and indexes are built with `CREATE INDEX ASYNC`.

Choose DSQL for multi-region active-active relational workloads with short transactions.
Do not choose it as a drop-in for an existing Aurora PostgreSQL application.

## ElastiCache and MemoryDB

- **ElastiCache** is a cache: data loss on failover is acceptable by design.
  **MemoryDB** is a durable primary store with a multi-AZ transaction log, priced accordingly.
  Picking MemoryDB for caching is expensive; picking ElastiCache as a system of record loses
  data.
- ElastiCache Serverless removes node sizing and scales automatically; node-based clusters are
  cheaper at steady, known load.
- Cluster mode changes the client contract — cross-slot operations fail — so it is a design
  decision, not a scaling knob to turn later.
- Redis-compatible data structure and key design questions belong to the `redis` skill; what
  belongs here is the service, instance and networking choice.

## S3

- Storage class is where the money is. Standard-IA and One Zone-IA bill a 30-day minimum
  duration; Glacier Instant Retrieval bills 90 days; Glacier Flexible and Deep Archive bill
  90 and 180 days. Moving objects that are deleted a week later to IA costs *more* than
  leaving them. `[official]`
- **Intelligent-Tiering** is the right default for data whose access pattern is unknown: a
  small per-object monitoring charge in exchange for automatic movement and no retrieval fee
  between the frequent and infrequent tiers.
- Lifecycle rules are the mechanism; a bucket without them keeps everything in Standard
  forever, which is the single most common line in an oversized S3 bill.
- Versioning plus no lifecycle rule on noncurrent versions means the bucket grows without
  bound and "deleted" objects still bill. Delete markers on a versioned bucket also make an
  apparently empty bucket refuse to delete.
- Block Public Access at the account level, encryption by default, and a bucket policy denying
  non-TLS requests (`aws:SecureTransport: false`) are the baseline; the last one is not
  implied by the first two.
- Request-rate scaling is per prefix (thousands of requests per second per prefix), so a
  workload that hammers one prefix throttles while the bucket is idle.

## Streaming: Kinesis, MSK, and when a queue is enough

- Most "we need streaming" requirements are satisfied by SQS plus EventBridge, which have no
  shards to size and no consumer-group semantics to operate. Reach for a log only when you
  need ordered replay or multiple independent consumers of the same records.
- **Kinesis Data Streams** on-demand removes shard management; provisioned mode is cheaper at
  known steady throughput but makes every scaling event a resharding operation.
- **MSK** exists for Kafka API compatibility and an existing Kafka ecosystem. MSK Serverless
  removes broker sizing; MSK Provisioned does not, and broker storage fills quietly.
- Ordering is per shard or per partition in every one of these. "Globally ordered" is not on
  offer, and designing for it produces a single-partition bottleneck.
- Consumer lag is the health metric — `IteratorAge` for Kinesis, consumer-group lag for
  Kafka. CPU on the consumer tells you nothing about whether it is keeping up.

## OpenSearch Service

Use it for full-text relevance, aggregations over semi-structured data and log search at a
scale where a relational `LIKE` has stopped working. Service-level decisions — managed
domains versus OpenSearch Serverless, instance and storage sizing, UltraWarm and cold tiers,
dedicated master nodes, the VPC versus public endpoint choice — belong here. Index and
mapping design, query DSL, analyzers and relevance tuning belong to the `elasticsearch` skill;
log and metric collection pipelines belong to the `observability` skill.

The recurring operational failure is a domain with no dedicated master nodes and an even
number of data nodes: a network partition produces split brain, and the cluster goes red.

## The costs that arrive later

- Every cross-AZ byte between an application and its database is charged in both directions.
  A three-AZ deployment that ignores zone affinity pays for it continuously.
- Snapshots and automated backups keep billing after the instance is deleted. Manual snapshots
  in particular are retained until someone deletes them.
- A provisioned resource with zero traffic costs the same as one with traffic. Idle
  non-production databases are usually the largest single line in a development account.
- Data transfer *out* to the internet is the most expensive direction; putting CloudFront in
  front of an origin usually reduces it, because CloudFront's egress pricing is lower and
  cache hits never reach the origin.

<!-- sources: awslabs-agent-plugins, aws-agent-toolkit, aws-docs, itsmostafa-aws -->
