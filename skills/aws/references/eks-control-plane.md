# EKS and ECS control planes

Verified against: the Amazon EKS and Amazon ECS user guides on docs.aws.amazon.com.

This file covers the AWS side of a managed cluster: creating it, paying for it, granting it
identity, connecting it, and upgrading it. Everything that goes through `kubectl apply` —
manifests, Helm charts, probes, resource limits, Pod security, Dockerfiles — belongs to the
`containers` skill.

## Contents

- [Version support is a billing and upgrade deadline](#version-support-is-a-billing-and-upgrade-deadline)
- [Cluster creation decisions you cannot easily reverse](#cluster-creation-decisions-you-cannot-easily-reverse)
- [Compute: managed node groups, Karpenter, Fargate, Auto Mode](#compute-managed-node-groups-karpenter-fargate-auto-mode)
- [Identity: EKS Pod Identity versus IRSA](#identity-eks-pod-identity-versus-irsa)
- [Cluster access: the access entry API](#cluster-access-the-access-entry-api)
- [Networking and IP exhaustion](#networking-and-ip-exhaustion)
- [Add-ons](#add-ons)
- [Upgrading](#upgrading)
- [What EKS costs](#what-eks-costs)
- [ECS and Fargate](#ecs-and-fargate)
- [ECR](#ecr)

## Version support is a billing and upgrade deadline

A Kubernetes minor version gets **14 months of standard support** on EKS from its EKS release
date, then **12 months of extended support** at an additional charge per cluster-hour.
Extended support is **enabled by default**, and a cluster still running when extended support
ends is **automatically upgraded** to the oldest version still supported. `[official]`

Three consequences:

- An unattended cluster has both a surprise bill (the day standard support ends, in UTC) and
  a surprise upgrade (the day extended support ends) already scheduled.
- Disabling extended support does not buy you time; it means the auto-upgrade happens at the
  end of *standard* support instead.
- `aws eks describe-cluster-versions` returns `endOfStandardSupportDate` and
  `endOfExtendedSupportDate`. Put them in a calendar, and alarm on approaching them, rather
  than finding out from the bill.

An in-place upgrade can be rolled back to the previous minor version within **7 days** of
completion, but not if the cluster was auto-upgraded at the end of extended support. That
7-day window is the real reason to upgrade deliberately rather than letting it happen.

## Cluster creation decisions you cannot easily reverse

| Decision | Why it is hard to change |
|---|---|
| VPC and subnets | Fixed for the life of the cluster; a too-small CIDR means rebuilding |
| Service IPv4 CIDR | Immutable after creation |
| IP family (IPv4 vs IPv6) | Immutable after creation |
| Cluster name | Appears in every IAM policy, add-on config and tag |
| Endpoint access (public / private / both) | Changeable, but flipping to private-only without a bastion or VPN locks everyone out, including the CI runner |

Create with at least two subnets in different AZs, in subnets large enough for the pod IP
model you have chosen, and decide the endpoint-access model before the first workload
depends on it.

## Compute: managed node groups, Karpenter, Fargate, Auto Mode

| Option | Fits | Operational cost |
|---|---|---|
| Managed node groups | predictable workloads, specific instance types, GPU or licensed software | you choose types and sizes, and own the scaling policy |
| Karpenter | mixed and bursty workloads | it provisions right-sized nodes from pod requirements and consolidates them; you own its configuration and its upgrades |
| Fargate profiles | isolation per pod, no node management | per-pod pricing, no DaemonSets, no privileged containers, limited storage |
| EKS Auto Mode | teams that do not want to operate the data plane at all | AWS manages nodes, scaling and core add-ons; a premium on top of EC2 pricing and less control |

Karpenter's consolidation is the largest single cost lever on a bin-packed cluster, and also
the most common cause of "why did my pod move at 3am" — the answer is usually consolidation
doing its job, and the fix is a pod disruption budget, which is a `containers` topic.

Fargate's no-DaemonSet restriction breaks the usual log and metric collection pattern; plan
the sidecar approach before committing a workload to it.

## Identity: EKS Pod Identity versus IRSA

Both give a pod an IAM role. Prefer **EKS Pod Identity** for new clusters.

| | IRSA | EKS Pod Identity |
|---|---|---|
| Mechanism | OIDC provider per cluster, role trust policy references it | association between a role and a service account, configured in EKS |
| Trust policy | one entry per cluster | a single `pods.eks.amazonaws.com` principal, reusable across clusters |
| Who configures it | whoever can create OIDC providers in IAM | cluster admin in EKS, IAM admin in IAM — clean separation |
| Same role across many clusters | edit the trust policy for each | one association per cluster, no trust-policy change |

`[official]` Pod Identity requires the `eks-pod-identity-agent` add-on. IRSA remains
necessary where a workload runs outside EKS but needs the same role shape, or where a tool
only understands the OIDC form.

Two traps that apply to both: if IMDS is not restricted on the nodes, a pod can still reach
the **node** role's credentials and bypass the whole mechanism, so block IMDS from pods
(hop limit 1) as part of cluster setup; and containers are not a security boundary, so two
pods on one node share a kernel regardless of which roles they hold.

## Cluster access: the access entry API

Granting a human or a CI role access to the Kubernetes API is an EKS-side operation
(`aws eks create-access-entry` plus an access policy association), not a `ConfigMap` edit.
The legacy `aws-auth` ConfigMap still works on older clusters, but it is a single mutable
object with no audit trail and a syntax error in it locks the entire cluster out.

The cluster creator gets implicit admin on older authentication modes; on the access-entry
model that is explicit and can be removed, which is what you want — but it also means a
cluster created by a pipeline may have no human administrator until one is granted.

## Networking and IP exhaustion

The default VPC CNI gives every pod a routable VPC IP from the subnet. That is excellent for
observability and security-group integration, and it is the number one capacity surprise:
pods per node are bounded by the instance type's ENI and IP limits, and a `/24` subnet runs
out of addresses long before the nodes run out of CPU.

The levers, in order of how disruptive they are:

- Prefix delegation (`ENABLE_PREFIX_DELEGATION`) assigns `/28` prefixes instead of individual
  IPs and multiplies the pods-per-node ceiling. Cheapest fix, no rebuild.
- Secondary CIDR ranges on the VPC with custom networking, so pods draw from a separate,
  larger range than the nodes.
- A different CNI, or IPv6 — both are effectively rebuild decisions.

Security groups for pods lets a pod carry its own security group, which is how you give one
workload database access without opening the node's group to everything on it.

## Add-ons

Prefer EKS **managed add-ons** (VPC CNI, CoreDNS, kube-proxy, EBS CSI driver, Pod Identity
agent) over self-managed manifests: they are versioned against the cluster version, upgraded
through the EKS API, and their compatibility is checked during an upgrade.

Each add-on has a version compatible with each Kubernetes version, and an upgrade that skips
the add-on step leaves a CNI or kube-proxy older than the control plane — which is the
supported configuration only for a narrow skew.

## Upgrading

1. Read the version's release notes for removed APIs. The cluster insights API
   (`aws eks list-insights`) reports deprecated API usage the cluster has actually seen,
   which beats grepping manifests.
2. Upgrade the control plane one minor version at a time. Skipping is not supported.
3. Upgrade the add-ons to versions compatible with the new control plane.
4. Upgrade the nodes. Managed node groups do a rolling replacement that respects pod
   disruption budgets — a PDB that can never be satisfied stalls the upgrade rather than
   breaking the workload, which looks like a hang.
5. Verify, and remember the 7-day rollback window exists only for in-place upgrades that you
   initiated.

## What EKS costs

- The control plane bills **per cluster-hour** whether or not a single pod runs. Four idle
  clusters cost the same as four busy ones at that layer, which makes per-team and
  per-environment cluster sprawl expensive.
- Extended support adds a surcharge per cluster-hour for the whole 12 months.
- The data plane is normal EC2 or Fargate pricing; Karpenter consolidation and Spot capacity
  are the main levers there.
- Cross-AZ traffic between pods is charged like any other cross-AZ traffic, and a service
  mesh that ignores topology can generate a lot of it.

## ECS and Fargate

ECS has no control-plane charge — you pay only for the compute. It is the cheaper and simpler
answer whenever Kubernetes portability is not a requirement.

- **Task definitions are immutable and versioned.** "Updating" one creates a new revision;
  services reference a revision, so a deploy is a service update to a new revision.
- The **deployment circuit breaker** rolls a failing deployment back automatically. Without
  it, a service can sit in a create-fail-retry loop indefinitely while the old tasks drain.
- **ECS Exec** (`aws ecs execute-command`) replaces SSH into the host and works on Fargate.
  It needs the SSM agent permissions on the task role and `enableExecuteCommand` on the
  service — enable it before you need it, because turning it on requires a new deployment.
- **Action Logs** report control-plane failures — rollbacks, circuit-breaker trips, task
  placement failures — that do not appear in application logs. When a deployment fails for
  no visible reason, that is where the reason is.
- Task placement failures are usually capacity or configuration, not the image: no subnet
  capacity, no ENI available, a task size Fargate does not offer, or a missing platform
  version.
- **AWS App Runner is sunset as of 2026-04-30** — no new customers and no new features.
  Existing users migrate to ECS Express Mode. Do not propose App Runner for anything new.
  `[official]`

## ECR

- Set a lifecycle policy on every repository at creation. Image layers accumulate silently
  and an untended repository is a steady, growing cost.
- Enable scan-on-push (basic or enhanced via Inspector) — it is the cheapest place in the
  pipeline to find a known CVE.
- Enable tag immutability for production repositories. A mutable `latest` means the image
  that passed CI and the image that ran in production are not provably the same artefact.
- Pull-through cache repositories remove the Docker Hub rate limit from your build path,
  which is a reliability fix rather than a cost one.
- Cross-region replication is configured on the registry, not the repository, and it is the
  supported way to avoid cross-region pulls at scale.

<!-- sources: aws-agent-toolkit, aws-docs, itsmostafa-aws -->
