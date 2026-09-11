# Diagnosing an Azure resource

Verified against: Azure Resource Health, Activity Log and Azure Monitor product documentation as
published in `MicrosoftDocs/azure-docs`. Commands were not executed locally; claims are
`[official]`.

Scope: the Azure product surface for finding out what a resource is doing - Resource Health,
Activity Log, diagnostic settings, Resource Graph, Service Health, support. Designing
instrumentation, OpenTelemetry, SLOs, alert routing and on-call practice is the `observability`
skill's job; reproducing a failure locally is the `debugging` skill's job.

## Contents

- [Order of operations](#order-of-operations)
- [Resource Health](#resource-health)
- [Activity Log](#activity-log)
- [Diagnostic settings](#diagnostic-settings)
- [Application Insights and Log Analytics as Azure resources](#application-insights-and-log-analytics-as-azure-resources)
- [Azure Resource Graph](#azure-resource-graph)
- [Service Health](#service-health)
- [Per-service first commands](#per-service-first-commands)
- [Support](#support)

## Order of operations

The ordering matters because each step rules out a class of cause, and the later steps are far
more expensive:

1. **Is Azure healthy?** Resource Health for the resource, Service Health for the region and
   service. If the platform is degraded, nothing downstream is worth reading.
2. **What changed?** Activity Log for the last 24 hours at the resource group scope. Most
   incidents are a change: a deployment, a configuration write, a scale operation, a deleted
   role assignment.
3. **What does the resource itself say?** The Diagnose and solve problems blade runs the
   service's own detectors and is the highest-yield step for App Service, Functions, Container
   Apps and AKS. It is not available from the CLI; say so rather than pretending.
4. **Logs and metrics.** Only now, and only with a hypothesis from steps 1-3.
5. **Reproduce.** If the failure can be reproduced locally, stop here and hand over to the
   `debugging` skill.

Jumping to step 4 is the common failure: an engineer reads an hour of traces to discover that
someone changed an app setting at 02:14.

## Resource Health

Resource Health reports the platform's view of one resource: `Available`, `Unavailable`,
`Degraded` or `Unknown`, with the reason classified as platform-initiated or customer-initiated.
That classification is the useful part - it tells you whether to investigate your own change or
wait for Azure.

```bash
az rest --method get \
  --url "https://management.azure.com<resourceId>/providers/Microsoft.ResourceHealth/availabilityStatuses/current?api-version=2023-07-01-preview" \
  --query "properties.{status:availabilityState, reason:reasonType, summary:summary}"
```

`Unknown` usually means the resource has not reported recently rather than that it is broken - a
stopped VM or a scaled-to-zero app reports `Unknown`, not `Unavailable`.

Resource Health is not retrospective beyond about 30 days, and it is per resource. For a regional
or service-wide event, go to Service Health.

## Activity Log

The Activity Log is the control-plane audit trail: every write, delete and action against ARM,
with the caller, the correlation ID and the outcome. It retains **90 days** and cannot be
extended in place - to keep more, add a diagnostic setting that ships it to a Log Analytics
workspace or a storage account.

```bash
# What changed here in the last day?
az monitor activity-log list -g <rg> --offset 24h \
  --query "[].{time:eventTimestamp, op:operationName.value, by:caller, status:status.value}" -o table

# Everything in one failed operation, across resources
az monitor activity-log list --correlation-id <id> --offset 7d
```

Things it does and does not contain:

- It **does** record deployments, role assignment changes, policy denials, autoscale actions,
  service health events, and every portal edit.
- It **does not** record data-plane operations. Reading a blob, executing a query, or invoking a
  function is not in the Activity Log; those need the resource's own diagnostic logs.
- The `caller` for anything done by a managed identity is an object ID, not a name. Resolve it
  with `az ad sp show --id <objectId>` before concluding "nobody changed anything".

## Diagnostic settings

Resource logs and platform metrics are **off by default** and are not retained anywhere until a
diagnostic setting routes them somewhere. When an incident starts with "check the logs" and there
are no logs, this is why, and it cannot be fixed retroactively.

```bash
az monitor diagnostic-settings create \
  --name to-law \
  --resource <resourceId> \
  --workspace <logAnalyticsWorkspaceId> \
  --logs    '[{"categoryGroup":"allLogs","enabled":true}]' \
  --metrics '[{"category":"AllMetrics","enabled":true}]'
```

- A resource can have up to five diagnostic settings.
- Platform **metrics** are collected for 93 days without any setting and are queryable with
  `az monitor metrics list`; a diagnostic setting is only needed to keep them longer or to query
  them with KQL alongside logs.
- Enforce the setting with an Azure Policy `deployIfNotExists` assignment rather than a checklist,
  and remember that such an assignment needs a managed identity with the right role or it fails
  silently at remediation.
- Log Analytics ingestion is billed per GB. Turning on `allLogs` for a chatty resource - a
  Front Door, an Application Gateway, an AKS control plane with verbose audit - is a cost
  decision. Pick categories deliberately and set the workspace's daily cap.

## Application Insights and Log Analytics as Azure resources

This skill covers the resource, not the instrumentation:

- Workspace-based Application Insights is the only supported kind; classic resources have been
  retired. The component must point at a Log Analytics workspace, and both should live in the
  region the application is in.
- `APPLICATIONINSIGHTS_CONNECTION_STRING` is the current setting.
  `APPINSIGHTS_INSTRUMENTATIONKEY` still works in some SDKs but is deprecated and does not carry
  the regional ingestion endpoint, which breaks in sovereign clouds and in some regions.
- The workspace retention default is 30 days; interactive retention up to two years and cheaper
  long-term retention are per-table settings, not workspace-wide.
- A daily cap stops ingestion when hit - alerting goes quiet for the rest of the day. Set an
  alert on the cap itself.

What to instrument, which spans and attributes to emit, how to define an SLO and how to route an
alert belong to the `observability` skill.

## Azure Resource Graph

Resource Graph queries the whole estate across subscriptions in one call, which is how you answer
inventory and governance questions without a loop over `az resource list`.

```bash
az graph query -q "
resources
| where type =~ 'microsoft.compute/disks' and managedBy == ''
| project name, resourceGroup, sku.name, properties.diskSizeGB
"
```

```bash
az graph query -q "
resources
| where isnull(tags['owner'])
| summarize count() by type, subscriptionId
"
```

Two constraints worth knowing: results are paged at 1,000 rows by default (use
`--first`/`--skip`), and the graph is eventually consistent with a lag of roughly a minute, so a
resource created seconds ago may not appear. Role assignments live in the `authorizationresources`
table, not `resources`.

## Service Health

Service Health covers the platform: active incidents, planned maintenance, health advisories and
security advisories, scoped to your subscriptions and regions. Two things to set up before you
need them:

- A Service Health alert with an action group, so a regional incident reaches on-call without
  anyone refreshing the portal.
- Resource Health alerts on the resources that matter, filtered to platform-initiated
  transitions - customer-initiated `Unavailable` is usually your own deployment.

## Per-service first commands

| Service | First command |
|---|---|
| App Service | `az webapp log tail -n <app> -g <rg>`; then the Diagnose and solve problems blade |
| Functions | `az functionapp show`, `az functionapp config appsettings list --query "[].name"`, then the Flex Consumption Deployment / Quota tools in Diagnose and solve problems |
| Container Apps | `az containerapp logs show -n <app> -g <rg> --follow`, `az containerapp revision list -o table` (a failing revision keeps the old one serving, so the app looks healthy) |
| AKS | `az aks show -g <rg> -n <c> --query "{state:provisioningState,power:powerState}"`, `az aks check-acr`, control-plane logs via diagnostic settings |
| VM | `az vm get-instance-view`, boot diagnostics, then Network Watcher `az network watcher test-ip-flow` for connectivity |
| Storage | `az storage account show --query "{net:networkRuleSet, public:allowBlobPublicAccess, shared:allowSharedKeyAccess}"` - most "403" incidents are the network rules or shared-key access being disabled |
| Deployments | `az deployment operation group list -g <rg> -n <name> --query "[?properties.provisioningState=='Failed']"` |

## Support

Before opening a ticket, collect: the resource ID, the exact time window in UTC, the correlation
ID from the failed operation, and the Resource Health status at that time. A ticket without a
correlation ID is a ticket that gets a request for a correlation ID.

Free support plans do not cover technical issues. Check the subscription's plan before promising
a response time, and note that quota increase requests are free regardless of plan.

<!-- sources: microsoft-azure-skills, awesome-copilot, azure-docs, azure-functions-skills -->
