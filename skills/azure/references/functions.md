# Azure Functions

Verified against: the Flex Consumption plan article as published in `MicrosoftDocs/azure-docs`.
Commands were not executed locally; claims are `[official]`.

Scope: choosing a hosting plan, configuring the app, and the Azure-side failure modes. Language
and framework code belongs to the language skill (`csharp-dotnet`, `python`, `typescript`,
`nodejs-backend`).

## Contents

- [Choosing a plan](#choosing-a-plan)
- [Flex Consumption specifics](#flex-consumption-specifics)
- [Runtime, worker and bundle versions](#runtime-worker-and-bundle-versions)
- [Identity-based connections](#identity-based-connections)
- [host.json settings that matter](#hostjson-settings-that-matter)
- [Cold starts](#cold-starts)
- [Deployment](#deployment)
- [Migrating Consumption to Flex Consumption](#migrating-consumption-to-flex-consumption)
- [Diagnosing a Function App](#diagnosing-a-function-app)

## Choosing a plan

| Plan | Scales to zero | VNet integration | Max instances | Notes |
|---|---|---|---|---|
| **Flex Consumption** | yes | **yes** | 1,000 | Recommended serverless plan. Linux only |
| Consumption (Y1 / Dynamic) | yes | **no** | 200 | The only serverless option on Windows |
| Premium (EP1-EP3) | no (min 1 always warm) | yes | 100 by default | Pre-warmed instances, unbounded execution duration, Windows supported |
| Dedicated (App Service plan) | no | yes | plan's instance count | Reuse an existing plan's spare capacity; needs `alwaysOn` |
| Container Apps | yes | yes | per environment | Functions in a container alongside other Container Apps workloads |

The decision usually reduces to two questions:

1. **Does it need to reach a private endpoint or a VNet-only resource?** If yes, Consumption is
   out - there is no setting that adds VNet integration to a Y1 plan. This is a plan migration,
   not a configuration change.
2. **Is a cold start acceptable?** If not, you need always-ready instances (Flex Consumption) or
   pre-warmed instances (Premium). `alwaysOn` is an App Service plan setting and has no effect on
   a Consumption plan.

## Flex Consumption specifics

- Linux only. A Windows app cannot migrate to it.
- Instance memory sizes: **512 MB (0.25 vCPU), 2048 MB (1 vCPU), 4096 MB (2 vCPU)**. 2048 MB is
  the default choice; the size can be changed later. HTTP trigger default concurrency depends on
  it.
- Maximum instance count applies to on-demand instances per *function scale group*. Always-ready
  instances are additional and do not count against the ceiling.
- Per-function scaling: HTTP and SignalR triggers scale as one group (`http`), Event Grid-based
  blob triggers as another (`blob`), Durable orchestration/activity/entity triggers as a third
  (`durable`); every other function scales on its own instances.
- Always-ready instances default to 0. With zone redundancy enabled the minimum is **2** per
  function or group, not 1.
- **Regional subscription quota: 250 cores (equivalent to 512,000 MB) per region per
  subscription**, shared by every Flex Consumption app there. Cores used = instances x cores per
  instance, so 1,000 instances of a 512 MB app and 125 instances of a 4,096 MB app both exhaust
  it. Apps that have scaled to zero do not count; always-ready instances do. A high
  `maximumInstanceCount` is not a guarantee - the quota can cap it first. It can be raised on
  request subject to capacity review.
- Azure Files shares can be mounted (SMB only, authenticated with a storage account key) for large
  binaries or shared models.
- Supported stacks: .NET 8/9/10 isolated worker (the in-process model is **not** supported), Node
  22/24, Python 3.10-3.14, Java 8/11/17/21/25, PowerShell 7.4.

## Runtime, worker and bundle versions

Three version numbers that must agree:

| Setting | Current value | Failure when wrong |
|---|---|---|
| `FUNCTIONS_EXTENSION_VERSION` | `~4` | An older host cannot load v4 extensions |
| `FUNCTIONS_WORKER_RUNTIME` | `dotnet-isolated`, `node`, `python`, `java`, `powershell` | `dotnet` (in-process) is unsupported on Flex Consumption |
| `host.json` `extensionBundle.version` | `[4.*, 5.0.0)` | A v2 or v3 bundle range on a v4 host resolves old binding extensions; bindings fail to load or behave differently |

A stale bundle range is easy to miss because the app keeps running: the host resolves the newest
bundle *within the declared range*, which may be years old. Check it whenever bindings behave
unexpectedly after a runtime upgrade.

`WEBSITE_NODE_DEFAULT_VERSION` is a Windows-only setting; on Linux the stack version comes from
`linuxFxVersion` and is ignored, so a `~18` there is misleading rather than authoritative.

## Identity-based connections

Every trigger and binding that takes a connection string also accepts an identity-based
configuration, using a setting *prefix* instead of a value:

| Connection string setting | Identity-based replacement | Role needed |
|---|---|---|
| `AzureWebJobsStorage` | `AzureWebJobsStorage__accountName` | Storage Blob Data Owner, Storage Queue Data Contributor, Storage Table Data Contributor on the host storage account |
| `ServiceBusConnection` | `ServiceBusConnection__fullyQualifiedNamespace` | Azure Service Bus Data Receiver / Sender |
| `EventHubConnection` | `EventHubConnection__fullyQualifiedNamespace` | Azure Event Hubs Data Receiver / Sender |
| `<name>` for blob triggers | `<name>__serviceUri` (plus `__queueServiceUri`, `__tableServiceUri`) | as above |

Order of operations, because getting it wrong produces a host that will not start:

1. Enable a managed identity on the app.
2. Create the role assignments and wait out the propagation window.
3. Add the `__accountName` / `__fullyQualifiedNamespace` settings.
4. Remove the connection-string settings.

`AzureWebJobsStorage` is the host's own storage - it holds timer schedules, singleton leases and
blob trigger receipts. An app whose identity lacks blob, queue *and* table data roles on it starts
and then silently fails to fire triggers.

## host.json settings that matter

- `extensionBundle.version` - see above.
- `functionTimeout` - default 5 minutes on Consumption with a **10 minute maximum**; unbounded on
  Premium and Dedicated. A timeout set above the plan's maximum is silently clamped.
- `logging.applicationInsights.samplingSettings.isEnabled` - **defaults to true** with a cap of
  20 items per second. Turning it off makes Application Insights ingestion scale linearly with
  traffic, and that bill is usually larger than the Functions bill. Tune
  `maxTelemetryItemsPerSecond` and `excludedTypes` instead of disabling.
- `extensions.serviceBus.*` - **the schema changed with the extension version, and the host
  ignores settings it does not recognise without logging anything.** Extension bundle `[4.*, 5.0.0)`
  brings Service Bus extension 5.x, which takes the flat form below. Bundle v2 and v3 bring
  extension 4.x, where the same knobs live under `messageHandlerOptions`. A `host.json` written
  for one and deployed against the other runs entirely on defaults:

  | Setting | Extension 5.x (bundle v4) | Extension 4.x (bundle v2/v3) | Default |
  |---|---|---|---|
  | Concurrency | `serviceBus.maxConcurrentCalls` | `serviceBus.messageHandlerOptions.maxConcurrentCalls` | 16 |
  | Lock renewal | `serviceBus.maxAutoLockRenewalDuration` | `serviceBus.messageHandlerOptions.maxAutoRenewDuration` | `00:05:00` |
  | Prefetch | `serviceBus.prefetchCount` | `serviceBus.prefetchCount` | 0 |

  The consequences compound. `prefetchCount: 0` disables prefetch, so every message costs a round
  trip. `maxAutoLockRenewalDuration` of five minutes under a `functionTimeout` of ten means a
  slow handler loses its lock, the message is redelivered, and the redelivery occupies a
  concurrency slot that the original invocation is still holding - which presents as a queue that
  stops draining rather than as an error. Check the dead-letter depth and the lock-lost count
  before tuning concurrency upward.
- `extensions.http.routePrefix` - defaults to `api`. Changing it breaks every published URL.

## Cold starts

A p50 in the tens of milliseconds with a p95 in seconds is the signature of cold starts on a plan
that scales to zero: the fast requests hit a warm instance, the slow ones pay for a new one.
Confirm it in Application Insights by looking at the duration distribution against instance count
rather than at the average.

Remedies in order of cost:

1. Reduce the package size and the dependency graph - the host downloads and mounts the package on
   every cold start.
2. Flex Consumption always-ready instances for the affected function group only.
3. Premium plan with pre-warmed instances, when the workload also needs unbounded duration or
   Windows.

`alwaysOn` does nothing on Consumption. A timer that pings the app every five minutes keeps at
most one instance warm and bills for the pings.

## Deployment

On Flex Consumption there is exactly one deployment path: build a zip, upload it to a blob
container, and the host runs from that package on startup. `WEBSITE_RUN_FROM_PACKAGE`,
`WEBSITE_CONTENTAZUREFILECONNECTIONSTRING` and the other settings that steered deployment on older
plans are ignored and should be deleted during migration - leaving them creates the impression of
configuration that is doing nothing.

Deployment slots exist on Premium and Dedicated plans and are the standard way to get a warm
target before a swap. Flex Consumption has no slots; it provides rolling updates as the site
update strategy instead.

## Migrating Consumption to Flex Consumption

Flex Consumption is a different resource configuration, not an in-place SKU change. Create the new
app and cut over:

- [ ] Confirm Linux and a supported stack version. Node 18 or .NET in-process means a code
      upgrade first.
- [ ] Provision the new app with the same storage account or a new one, with a managed identity
      and its role assignments in place before the first start.
- [ ] Move the extension bundle range to `[4.*, 5.0.0)` and re-test every binding.
- [ ] Drop `WEBSITE_RUN_FROM_PACKAGE`, `WEBSITE_CONTENTAZUREFILECONNECTIONSTRING`,
      `WEBSITE_CONTENTSHARE` and `alwaysOn`.
- [ ] Add VNet integration and set `publicNetworkAccess: Disabled` if the app should only be
      reachable privately.
- [ ] Configure always-ready instances for the latency-sensitive function group, and check the
      regional 250-core quota covers the intended maximum.
- [ ] Cut traffic over at the front door (Front Door, API Management or DNS), then decommission
      the old app - a shared `AzureWebJobsStorage` means both apps compete for the same singleton
      leases and blob trigger receipts while they coexist.

## Diagnosing a Function App

```bash
az functionapp show -n <app> -g <rg>
az functionapp config show -n <app> -g <rg>
# setting names only - never print values
az functionapp config appsettings list -n <app> -g <rg> --query "[].name"
az functionapp function list -n <app> -g <rg>
```

Then, in order: the app's Resource Health, the Diagnose and solve problems blade (which has a
Flex Consumption Deployment tool and a Flex Consumption Quota tool), and only then Application
Insights. Report findings before changing anything, report setting names without their values, and
get explicit approval before writing app settings, restarting or redeploying - a restart on a
queue-triggered app abandons in-flight messages.

<!-- sources: azure-functions-skills, azure-docs, microsoft-azure-skills -->
