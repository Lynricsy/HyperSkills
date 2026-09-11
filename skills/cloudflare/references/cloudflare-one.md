# Cloudflare One: Access, Gateway, the device client and Tunnel

Verified against: official documentation and the official `cloudflare-one` skill, re-read
2026-09. **Nothing in this file was reproduced locally** — every claim needs an account, a
domain or the `cloudflared` binary, so treat all of it as `[official]` and retrieve current
limits, category IDs and API bodies before acting. Never guess an application ID, a category
ID, a wirefilter field or a request body.

## Contents

- [Access versus Gateway](#access-versus-gateway)
- [Access applications and policies](#access-applications-and-policies)
- [Service tokens and non-human clients](#service-tokens-and-non-human-clients)
- [Gateway policy types and order](#gateway-policy-types-and-order)
- [TLS inspection and DLP](#tls-inspection-and-dlp)
- [The device client, enrollment and profiles](#the-device-client-enrollment-and-profiles)
- [Split tunnel](#split-tunnel)
- [Cloudflare Tunnel](#cloudflare-tunnel)
- [Log surfaces](#log-surfaces)
- [Rollout discipline](#rollout-discipline)

## Access versus Gateway

Access controls **application authorization** — who may reach this application. Gateway
controls **traffic inspection and filtering** — what this device may do on the network. A
requirement that spans identity-aware application access and web security needs both, and
mixing them up produces a policy that appears to do nothing.

Two more distinctions that get conflated:

- **Access Groups** are Cloudflare objects. **IdP/SCIM groups** are identity claims. Gateway
  group selectors use synced IdP groups, not Access Groups.
- **Browser Rendering** (clientless SSH/RDP/VNC through the browser) is an Access capability.
  **Browser Isolation** renders general web content remotely. They are different products.

## Access applications and policies

- Access is **default-deny**. A private application with routes and DNS but no Allow policy
  still blocks everyone — "the tunnel is healthy" is not the same as "the app is reachable".
- Create policies through the reusable policy collection (`/access/policies`) and attach them
  to applications. Do not send inline `policies` in an application create/update request
  unless the current API documentation requires an app-scoped policy for that type.
- A policy returned as `reusable: false` is legacy. Migrate it with the documented
  `make_reusable` endpoint or replace it; do not create new ones. This is a different thing
  from the deprecated legacy private-network application type.
- Public hostname applications can be clientless. Private destinations require the device
  client or another on-ramp, **plus** routes and DNS resolution — creating the Access app alone
  is not enough. Private hostnames need explicit resolver policies.
- Group names and SAML/OIDC attribute names and values are **case-sensitive**. Verify the exact
  claim before writing a group rule, and do not invent group selectors when group sync is not
  configured.
- SCIM changes and group membership can be stale until sync and re-authentication complete.
  Troubleshoot against the user's **last authenticated identity**, not the IdP's current state.
- SaaS federation handles authentication into the SaaS app. Authorization and tenant
  restrictions usually need SaaS-side roles plus Gateway tenant controls.
- For SSH with the device client deployed, Zero Trust Infrastructure Access is the purpose-built
  option: keystroke logging, control over target authentication, and short-lived certificates
  that replace static keys. Short-lived certificates require the target's `sshd` to trust the
  Cloudflare CA public key.

## Service tokens and non-human clients

Headless devices and machine clients authenticate with a service token, and the identity that
results has no group membership: it is
`non_identity@<team-domain>.cloudflareaccess.com`. Consequences:

- A device profile or policy that targets IdP groups **never matches** a service-token client.
  Target them explicitly by that identity, by OS or device attributes, or let them fall to the
  default profile.
- Generated secrets — IPsec PSKs, some OAuth/client secrets — are returned **once**. Store them
  at creation time.

## Gateway policy types and order

DNS, Network, HTTP and Egress policies have different evaluation semantics; they are not one
ordered list. Retrieve the current order-of-enforcement page before explaining precedence. What
is stable enough to rely on:

- `dns.domains` matches a domain **and its subdomains**; `dns.fqdn` is exact-match only. Using
  `fqdn` where `domains` was meant is the usual cause of "the block rule does nothing".
- HTTP **Do Not Inspect** rules run before Allow/Block/Isolate. A later block rule cannot
  override an earlier inspection bypass.
- Network policies are strict L4 controls; identity-aware L4 matching needs authenticated
  device context.
- Access policy selectors can use IP lists but not Gateway domain or URL lists.
- Audit SSH is a Gateway Network policy action that logs commands without blocking, and requires
  the session to be proxied through Cloudflare.

## TLS inspection and DLP

- Deploy the Cloudflare root CA to managed devices **before** enabling TLS inspection, and
  enumerate certificate-pinned applications as Do Not Inspect exceptions first. Enabling
  inspection without both is a self-inflicted outage.
- HTTP inspection and DLP for encrypted traffic are impossible without TLS inspection. If
  inspection is off, DLP on HTTPS does nothing.
- DLP profiles are **detection definitions only**. They have no effect until referenced by a
  Gateway HTTP policy or CASB scan settings.
- Sequence DLP as log → tune → block. Start with payload logging where policy allows it, drive
  the false-positive rate down, then enforce.
- API CASB is out-of-band and periodic, not inline enforcement. Large SaaS integrations can
  take 24–48 hours for an initial scan, and reauthorizing can restart scan state. For inline
  control of specific SaaS actions, use Gateway granular application controls.

## The device client, enrollment and profiles

Two separate things control the client:

1. **Enrollment rules** — who may connect. The enrollment rule is an **Access application of
   type `warp`**, and it accepts reusable Access policies. Debug enrollment in Access, not in
   Devices. This is the single most misdirected troubleshooting path in Cloudflare One.
2. **Device profiles** — how the client behaves afterwards: connection mode, split tunnel,
   user permissions, auto-reconnect, captive portal handling. Profiles match by user group or
   device attributes in precedence order, first match wins, default profile catches the rest.

MDM parameters (`mdm.xml`, managed preferences) **override** dashboard-configured profile
settings for any setting present in the file. When dashboard changes appear to have no effect
on managed devices, read the MDM config. If another VPN or agent controls DNS, use traffic-only
mode to avoid routing-table and DNS conflicts. Captive portal detection temporarily
disconnects the client, and is a common source of user-visible friction.

## Split tunnel

Include/exclude is **per profile, not per entry** — you cannot mix modes in one profile, and
switching modes means re-evaluating every entry.

| Goal | Mode | Why |
|---|---|---|
| VPN replacement only (private apps) | Include | only the listed private CIDRs and hostnames go through the client; minimal blast radius |
| Secure web gateway only | Exclude | all traffic through the client; exclude only what breaks (local printers, pinned apps) |
| VPN replacement plus SWG | Exclude | the common enterprise configuration |
| Coexistence with another VPN | Include | avoids fighting the other tunnel interface and its DNS control |
| DNS filtering only | DNS-only | queries go to Gateway, no traffic proxying |

Split tunnel entries and tunnel routes must align **bidirectionally**. A CIDR in the include
list with no matching tunnel route is a black hole; a tunnel route with no matching profile
entry means traffic never enters the tunnel.

## Cloudflare Tunnel

Tunnel is an off-ramp from a private network to Cloudflare; Cloudflare WAN and Mesh are
off-ramps that can also be on-ramps. `cloudflared` is a separate binary from wrangler — check
`cloudflared --version` before writing instructions.

**Quick tunnel** — temporary `https://*.trycloudflare.com`, no account, for demos and previews:

```sh
cloudflared tunnel --no-autoupdate --url http://localhost:3000
```

**Named tunnel** — a stable hostname on a Cloudflare-managed domain:

```sh
cloudflared tunnel login
cloudflared tunnel create <name>
cloudflared tunnel route dns <name> app.example.com
cloudflared tunnel run <name>
```

Choose quick mode when the URL may change, no domain is involved and no login is wanted;
choose named mode for a fixed hostname, a webhook endpoint or anything that must survive a
restart. Prefer remotely managed, token-based tunnels for new deployments unless there is a
concrete reason for local config.

Verification discipline, because the common failure is declaring success too early:

- Check the local service is reachable first. Treat `200`, `301`, `302`, `304`, `401` and `403`
  as evidence it is up — an auth challenge means the server is answering.
- A printed `trycloudflare.com` URL is **not** a working tunnel. Wait for at least one
  `Registered tunnel connection` line as well.
- DNS for a fresh `trycloudflare.com` hostname can take a minute or two to propagate, and a
  fake-IP proxy resolver may never resolve it; retry, and fall back to DNS-over-HTTPS to check.
- Run **multiple connectors on separate hosts** for production HA. A healthy tunnel only proves
  `cloudflared` can reach Cloudflare — it still needs published application routes, network
  routes or hostname routes for anything to be reachable.
- Virtual networks are for genuinely overlapping IP space. Do not reach for them as a general
  segmentation tool; use policy.
- Never print, paste, commit or relocate tunnel tokens or the local Cloudflare credentials
  file.

Before exposing a local service publicly, check what is behind it: an admin panel, an
unauthenticated write API, internal tooling or anything holding real data should get an Access
policy in front of it rather than a public URL.

## Log surfaces

| Question | Log |
|---|---|
| Why was this request blocked or allowed | Gateway activity logs (DNS, HTTP, Network decisions), filterable by rule, identity, destination, action |
| Who authenticated to this app and which policy matched | Access audit logs |
| Which unmanaged SaaS apps are in use | Shadow IT discovery (needs TLS inspection for HTTPS visibility) |
| Is this device healthy, can it reach that origin | DEX, including HTTP and traceroute tests and fleet status |
| Long retention, SIEM | Logpush for Gateway, Access, Network and DEX — configure before go-live if compliance requires it |

Troubleshoot from the log toward the configuration: find the entry showing the failure (a
Gateway block, an Access deny, a tunnel error, a DNS miss), then trace back to the rule, route
or policy that produced it. The reverse direction — reading policies and reasoning about what
should have happened — is how hours disappear.

## Rollout discipline

Stage broad block, allow, DLP and TLS-inspection policies **disabled or scoped to a pilot
group or site** unless a wider rollout is explicitly approved. For every change, state the
prerequisites, the resources to inspect or create, the test cases, and the rollback. Validate
Access changes by testing the authorized, unauthorized, posture-failing, service-token and
multi-IdP flows that apply, then read the logs to confirm which policy matched.

<!-- sources: cloudflare-skills, cloudflare-docs, xiaoyuboi-tunnel -->
