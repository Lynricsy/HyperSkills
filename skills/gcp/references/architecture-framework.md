# Architecture Framework review

Google Cloud's Well-Architected Framework has six pillars. This reference turns each into
checks that can be answered from a project's configuration rather than from a conversation,
plus the two architecture decisions that dominate everything else: which compute product, and
which regions.

Verified against: cloud.google.com/architecture/framework (pillar structure) and the product
behaviour verified elsewhere in this skill.

## Contents

- [Choosing compute](#choosing-compute)
- [Choosing regions](#choosing-regions)
- [Operational excellence](#operational-excellence)
- [Security, privacy and compliance](#security-privacy-and-compliance)
- [Reliability](#reliability)
- [Cost optimization](#cost-optimization)
- [Performance optimization](#performance-optimization)
- [Sustainability](#sustainability)
- [Running the review](#running-the-review)

## Choosing compute

| Product | Fits | Ruled out by |
|---|---|---|
| **Cloud Run** service | HTTP/gRPC request-response, event consumers, anything that can scale to zero | needs a persistent local disk, a fixed IP per instance, or a process that must run between requests without instance-based billing |
| **Cloud Run** job / worker pool | batch to completion; always-on pull consumers | needs request routing |
| **Cloud Run functions** | one small handler per event | a codebase big enough to have modules |
| **GKE** | many services sharing a cluster, custom scheduling, operators, service mesh, GPU/TPU fleets | one service and a team that does not want to own Kubernetes — the $0.10/cluster/hour plus the operational surface is not free |
| **Compute Engine** | licensed software, kernel-level requirements, lift-and-shift, sustained predictable load with CUDs | anything that could be a container and does not need the host |
| **App Engine standard** | existing App Engine estates | new work — Cloud Run is the current answer |

The default for new work is Cloud Run. Move to GKE when the *number of services and their
interdependence* justifies a shared scheduler, not when one service becomes important. The
migration Cloud Run → GKE is a Dockerfile you already have plus manifests; the reverse is
harder because you will have adopted cluster-level machinery.

Container images, manifests and cluster-internal design are the `containers` skill's subject;
this table is about which Google Cloud product to stand up.

## Choosing regions

Four inputs, in this order:

1. **Data residency and compliance.** Enforce with the `gcp.resourceLocations` org policy, not
   with a wiki page. This constraint eliminates most of the map before the others matter.
2. **Latency to users.** Pick the region nearest the traffic, then check that every dependency
   (Cloud SQL, buckets, Memorystore) is in the *same* region. Cross-region calls add both
   latency and egress cost on every request.
3. **Product availability.** Not every product, machine type, GPU or Cloud SQL edition exists
   in every region. Check before designing around one.
4. **Price.** Regions differ materially — `us-central1` is typically among the cheapest, and
   some regions are 20–30% more for identical resources.

Zonal versus regional is a separate axis: a zonal resource (a zonal GKE cluster, a
`ZONAL` Cloud SQL instance, a single VM) is unavailable for the duration of a zone incident.
Anything with an SLO is regional. Multi-region is for the small set of systems whose RTO
cannot tolerate a regional outage, and it multiplies both cost and complexity — it is a
deliberate decision, not a default.

## Operational excellence

- Every deployment can be rolled back without a rebuild. On Cloud Run that is
  `update-traffic --to-revisions=<previous>=100`; if the service is on
  `latestRevision: true` at 100% there is no such path.
- Infrastructure is described in code and applied by a pipeline, not by console clicks. Use
  the `terraform` skill for the HCL side; Google's own options are Infrastructure Manager and
  the Config Connector.
- Deployments are traceable to a commit — image digests, not `:latest`, and
  `--revision-suffix=GIT_SHA`.
- There is a maintenance window on every managed resource that has one (Cloud SQL, GKE), so
  the vendor's restart happens when someone is awake.
- Essential Contacts are set on the organization, so security and outage notices reach a team
  rather than the person who created the project.

## Security, privacy and compliance

- No downloaded service account keys; `iam.disableServiceAccountKeyCreation` enforced.
- No workload running as a default service account; every workload has its own identity with
  scoped roles.
- No basic roles (`roles/owner`, `roles/editor`, `roles/viewer`) in a production project's
  policy except for a named break-glass group.
- No `allUsers` or `allAuthenticatedUsers` on buckets or services that are not deliberately
  public; `storage.publicAccessPrevention` enforced.
- Databases have no public IP, or at minimum no `0.0.0.0/0` authorized network and SSL
  required.
- Secrets in Secret Manager with a rotation schedule, not in environment variables committed
  to a repository.
- Data Access audit logs enabled where "who read this" is a question you will need answered —
  before the incident, since they are not retroactive.
- Deny policies for the invariants that must survive a well-meaning grant.

## Reliability

- Define the SLO before the architecture. "99.9% of checkout requests under 800 ms" decides
  regional versus zonal, HA versus single instance, and how much redundancy is justified.
- Every stateful managed service is regional: Cloud SQL `--availability-type=regional`,
  regional GKE control plane, multi-zone node pools.
- Backups exist **and a restore has been performed**. Point-in-time recovery is on where the
  RPO is shorter than the backup interval, with the Enterprise edition's 7-day PITR ceiling
  checked against the requirement.
- Deletion protection and liens on the resources whose loss is unrecoverable.
- Graceful degradation is designed: what the service returns when the database is down is a
  decision, not an exception trace.
- Quotas have headroom for the peak you plan, requested in advance.
- Retry with exponential backoff and jitter on every cross-service call, because rate quotas
  and transient 503s are normal operation in a distributed system.

## Cost optimization

- Costs are attributable: one project per application per environment, labels enforced at
  creation, BigQuery billing export enabled (it is not retroactive).
- Budgets exist with forecast-based thresholds, and everyone involved knows a budget does not
  cap spend.
- Idle resources are swept regularly — unattached disks, reserved-but-unused IPs, stopped VMs
  still paying for disks, old snapshots, orphaned load balancers.
- Storage classes and lifecycle rules match object lifetimes, with the minimum-duration
  charges accounted for.
- Right-sizing precedes commitments; a three-year CUD on an over-provisioned fleet locks in
  the waste.
- Non-production scales to zero or shuts down outside working hours.

## Performance optimization

- Compute, data and users are co-located in one region. Most "slow in Europe" reports are a
  US-region database.
- Autoscaling bounds are set deliberately, and the downstream (database connections,
  third-party rate limits) can absorb the maximum.
- Caching exists where the read pattern justifies it — Cloud CDN in front of static content,
  Memorystore in front of expensive queries — before the database is scaled up.
- Load testing has established where the system actually saturates. Concurrency and instance
  settings derived from a measurement, not from a default.
- The observability signals needed to answer "where did the time go" exist before the
  performance question arrives.

## Sustainability

Google publishes per-region carbon characteristics; where latency and residency allow a
choice, the lower-carbon region is free to pick. Beyond that, the sustainability actions and
the cost actions are the same list: delete idle resources, right-size, move cold data to
colder classes, and scale non-production to zero.

## Running the review

A useful review is evidence-first and per-finding:

1. Establish scope and inventory before opinions: which projects, which services. Cloud Asset
   Inventory (`gcloud asset search-all-resources`) beats asking.
2. Go pillar by pillar, and for each check record the **observed configuration** — the policy
   binding, the flag value, the missing setting — not an impression.
3. Rank by consequence, not by pillar order. A publicly reachable production database
   outranks a missing label convention, always.
4. For each finding give the exact change: the `gcloud` command or the setting and its target
   value, plus what it costs or breaks.
5. Name what you could not check. "Data Access audit logs are off, so I cannot tell whether
   this bucket has been read externally" is a finding in itself.

<!-- sources: gcp-docs, google-skills, optimnow-finops -->
