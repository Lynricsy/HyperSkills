# VPC, endpoints and the network's effect on cost and reachability

Verified against: the Amazon VPC and PrivateLink user guides, the Elastic Load Balancing user
guide and the Route 53 developer guide on docs.aws.amazon.com.

## Contents

- [VPC and subnet layout](#vpc-and-subnet-layout)
- [Getting out: NAT, and the endpoints that avoid it](#getting-out-nat-and-the-endpoints-that-avoid-it)
- [Interface endpoints (PrivateLink)](#interface-endpoints-privatelink)
- [Cross-AZ traffic](#cross-az-traffic)
- [Security groups versus NACLs](#security-groups-versus-nacls)
- [Load balancer selection](#load-balancer-selection)
- [DNS, certificates and their placement](#dns-certificates-and-their-placement)
- [Lambda in a VPC](#lambda-in-a-vpc)
- [Connecting VPCs and on-premises](#connecting-vpcs-and-on-premises)
- [Tracing an unreachable endpoint](#tracing-an-unreachable-endpoint)

## VPC and subnet layout

- Size the VPC CIDR for the lifetime of the account, not for today. You can add secondary
  CIDRs later, but you cannot shrink or renumber one, and an overlap with a peer or an
  on-premises range is unfixable without a migration. `/16` for a production VPC with
  `/20`-ish subnets is a defensible default.
- "Public" and "private" are properties of the route table, not of the subnet: a subnet is
  public exactly when its route table has a default route to an internet gateway.
- Three AZs is the usual minimum for production; two survives one failure but leaves no
  capacity headroom during it. Some services (EKS control plane, RDS Multi-AZ) require
  subnets in at least two.
- AWS reserves five IP addresses in every subnet, so a `/28` gives eleven usable addresses,
  not sixteen. Container and Lambda workloads consume addresses far faster than instance
  counts suggest.

## Getting out: NAT, and the endpoints that avoid it

A NAT gateway bills an hourly charge per gateway plus a per-GB data-processing charge on
everything through it — and one per AZ is the usual highly-available layout, so the hourly
cost triples before any traffic flows.

The largest reduction is usually not a cheaper NAT; it is removing AWS-service traffic from
the NAT path entirely:

- **Gateway VPC endpoints** exist for **Amazon S3 and DynamoDB only**. They work by adding a
  prefix-list route to the subnet's route table, they do not use PrivateLink, and
  **there is no additional charge for using them**. `[official]` For a workload that reads
  from S3 through a NAT gateway, this is free money.
- Gateway endpoints are regional and route-table scoped: an instance in a subnet whose route
  table lacks the endpoint route still goes out through NAT, which is how half a fleet ends
  up on the expensive path.
- A NAT instance is cheaper than a NAT gateway at low volume but is a single point of failure
  you now operate. Reach for it only in non-production.
- If the only reason a subnet has a NAT gateway is package installation at boot, bake the
  packages into the image instead.

## Interface endpoints (PrivateLink)

For every other AWS service, and for third-party or your own services, an interface endpoint
creates an ENI in your subnets with a private IP.

- Billing is per endpoint **per AZ per hour** plus per GB processed. Three AZs times twenty
  services is a real number before any traffic. Enable them per service, per environment,
  where the traffic or the isolation requirement justifies it — not by policy across the
  board.
- Private DNS is what makes the endpoint transparent: the service's public hostname resolves
  to the endpoint's private IP inside the VPC. That is also its sharpest edge — enabling
  private DNS on an API Gateway VPC endpoint makes *all* `execute-api` calls from that VPC
  resolve to the endpoint, including calls to public APIs, which then fail with 403. Use
  custom domain names for the public ones.
- An endpoint has its own resource policy. The default allows everything; narrowing it to your
  organisation is the control that stops an endpoint being used to exfiltrate to a foreign
  bucket.
- Endpoints are the mechanism behind "private-only" architectures; they are not a substitute
  for IAM. A private endpoint to S3 still authorises by policy.

## Cross-AZ traffic

Data transferred between availability zones within a region is charged in **both**
directions. It is invisible in most architecture diagrams and shows up as a "Data Transfer"
line that nobody can attribute.

The usual sources, in order of size: chatty service-to-service calls behind a load balancer
that does not preserve zone affinity; a cache or database accessed from every zone; and
replication that was configured for durability but is crossing zones more than it needs to.
The levers are zone-aware routing where the framework supports it, co-locating tightly
coupled tiers, and accepting the cost where the availability requirement genuinely needs it.

Traffic within one AZ, and traffic to and from S3 and DynamoDB in the same region, is not
charged this way.

## Security groups versus NACLs

| | Security group | Network ACL |
|---|---|---|
| Attaches to | ENI | subnet |
| State | stateful — return traffic is implicit | stateless — you must allow both directions |
| Rules | allow only | allow and deny, evaluated in numbered order |
| Default | deny all inbound, allow all outbound | allow all both ways |

Use security groups as the primary control, and reference other security groups rather than
CIDRs — `allow 5432 from sg-app` keeps working when the application's addresses change, and
it documents the intent. Keep NACLs for coarse subnet-level blocks; a NACL that needs
per-service rules is a sign the design belongs in security groups.

The stateless nature of NACLs is the recurring outage: an inbound allow with no matching
outbound ephemeral-port range silently breaks responses.

A shared security group is a blast radius. Before widening one, enumerate everything attached
to it, and never widen ingress to `0.0.0.0/0` to make a test pass.

## Load balancer selection

- **ALB** for HTTP/HTTPS: path and host routing, WebSockets, OIDC authentication, target
  groups of instances, IPs or Lambda functions.
- **NLB** for TCP/UDP, static IPs, extreme throughput, or when the client must see a
  preserved source IP without proxy protocol parsing.
- **Gateway Load Balancer** only for inserting third-party inline appliances.
- Both ALB and NLB bill an hourly charge plus capacity units; an idle load balancer per
  environment is a recurring cost that dev accounts forget.
- ALB has an idle timeout (60 seconds by default) that must be *longer* than the backend's
  keep-alive, or the load balancer reuses a connection the backend has already closed and the
  client sees a 502. This is the most common "intermittent 502" cause.
- Cross-zone load balancing is on by default for ALB and off by default for NLB; turning it on
  for NLB evens out the load and adds cross-AZ data transfer charges.

## DNS, certificates and their placement

- ACM certificates are regional. A certificate for CloudFront must be issued in
  **us-east-1**, regardless of where everything else lives. So must an edge-optimized API
  Gateway custom domain's certificate.
- ACM certificates validated by DNS renew automatically as long as the validation CNAME
  stays in place. Deleting it after issuance is a time bomb that fires at renewal.
- Route 53 alias records to AWS targets are free to query and can point at the zone apex;
  a CNAME cannot. Use alias for anything AWS-hosted.
- Health-check-based failover needs the health check to test something meaningful. A check
  against `/` that returns 200 from a load balancer with zero healthy targets fails over
  nothing.
- A private hosted zone must be associated with every VPC that should resolve it, including
  VPCs in other accounts (a two-step authorisation).

## Lambda in a VPC

- Attach a function to a VPC only when it needs to reach something private. In a VPC it has
  **no** internet access unless the subnet routes to a NAT gateway, which means every call to
  a public AWS API now costs NAT data processing.
- The remedy is endpoints: a gateway endpoint for S3 and DynamoDB, interface endpoints for
  the handful of services the function actually calls.
- Hyperplane ENIs are shared across invocations, so VPC attachment no longer imposes the old
  per-cold-start ENI penalty — but ENIs per VPC are a quota shared with other services.
- A function in a private subnet that "hangs" for its whole timeout is almost always a
  missing route or a missing endpoint, not a slow dependency: there is no route, so the
  connection never gets an answer at all.

## Connecting VPCs and on-premises

- **Peering** is simple, non-transitive, and requires non-overlapping CIDRs. Fine for two
  VPCs; unmanageable at ten.
- **Transit Gateway** is the hub for many VPCs and hybrid connectivity. It bills per
  attachment-hour plus per GB, so it is the right answer at scale and an expensive one for
  three VPCs.
- **PrivateLink** exposes one service rather than a network, which is the correct choice when
  the requirement is "consume their API", not "join their network" — and it sidesteps CIDR
  overlap entirely.
- **Site-to-Site VPN** is quick and runs over the internet; **Direct Connect** is a
  provisioned circuit with a lead time measured in weeks. A VPN over Direct Connect is the
  usual way to get both encryption and predictable latency.

## Tracing an unreachable endpoint

Work outward in this order; each step is cheap and eliminates a layer:

1. `aws ec2 describe-security-groups` — is the port open *from* the right source?
2. Route table — is there a route to the destination at all?
3. NACL — are both directions allowed, including ephemeral ports?
4. DNS — does the name resolve, and to a private or public address?
5. VPC Reachability Analyzer — it answers the whole question in one call and names the
   blocking component, which beats reasoning about it.
6. VPC Flow Logs — `REJECT` entries prove where the packet died; an absence of entries proves
   it never arrived.

The distinction that saves the most time: a connection refused quickly is a listener or
security-group problem; a connection that hangs until timeout is a routing or NACL problem.

<!-- sources: aws-agent-toolkit, aws-docs, awesome-copilot-aws -->
