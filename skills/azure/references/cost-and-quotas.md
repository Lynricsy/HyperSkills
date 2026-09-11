# Cost and quotas

Verified against: the Azure subscription and service limits article and the `az quota` command
surface as documented in `MicrosoftDocs/azure-docs` and `microsoft/azure-skills`. Commands were
not executed locally; claims are `[official]`.

This file contains no prices. Prices change and a table of them is a liability; what follows is
how to obtain the current number and which shapes are wasteful regardless of the number.

## Contents

- [Quotas are capacity](#quotas-are-capacity)
- [Finding the right quota name](#finding-the-right-quota-name)
- [Requesting an increase](#requesting-an-increase)
- [Comparing regions](#comparing-regions)
- [Getting a real price](#getting-a-real-price)
- [Where the money actually goes](#where-the-money-actually-goes)
- [Waste shapes](#waste-shapes)
- [Commitment discounts](#commitment-discounts)
- [Attributing cost](#attributing-cost)

## Quotas are capacity

An Azure quota is not a billing limit. It is the amount of a resource type your subscription may
hold **in one region**, and if you do not have it, the deployment fails. Requesting an increase
is free; you pay only for what you actually deploy. Checking quota before a capacity change is
therefore free insurance, and skipping it is how a migration fails halfway through.

Quotas are per subscription per region. "We are out of vCPU" is solved by another region, another
subscription, or an increase - never by a bigger resource group.

Adjustable quotas (VM vCPUs by family, public IPs, storage accounts) can be raised, usually with
automatic approval. Non-adjustable ones are architectural facts; the 4000 role assignments per
subscription is the one most likely to surprise a platform team.

## Finding the right quota name

**There is no 1:1 mapping between an ARM resource type and its quota name.** Guessing the quota
name from the resource type is the single most common reason `az quota show` returns
`BadRequest`.

| ARM type | Quota resource name |
|---|---|
| `Microsoft.Compute/virtualMachines` | `cores`, `virtualMachines`, and a per-family name such as `standardDSv5Family` |
| `Microsoft.App/managedEnvironments` | `ManagedEnvironmentCount` |
| `Microsoft.Network/publicIPAddresses` | `PublicIPAddresses`, `IPv4StandardSkuPublicIpAddresses` |

Discover it instead of guessing:

```bash
az extension add --name quota   # required once; without it the commands do not exist

SCOPE="/subscriptions/$SUB/providers/Microsoft.Compute/locations/westeurope"

# 1. List everything, match on the human-readable localizedValue
az quota list --scope "$SCOPE" -o table

# 2. Use the `name` field from that output, never the ARM type
az quota show       --resource-name standardDSv5Family --scope "$SCOPE"
az quota usage show --resource-name standardDSv5Family --scope "$SCOPE"
```

Two failure modes to recognise:

- The REST API and the portal can display **"No Limit"**. That does not mean unlimited; it means
  the quota API does not model that resource type. Fall back to the published service limits.
- Some providers are not supported by the quota API at all - `Microsoft.DocumentDB` (Cosmos DB)
  among them. `BadRequest` from `az quota` is the symptom; the service's own limits documentation
  is the answer.

Confirmed working: `Microsoft.Compute`, `Microsoft.Network`, `Microsoft.App`,
`Microsoft.Storage`, `Microsoft.MachineLearningServices`.

Some services keep their quota outside this API entirely - Azure Functions Flex Consumption has a
regional 250-core memory quota surfaced through a dedicated portal tool, not `az quota`.

## Requesting an increase

```bash
az quota update \
  --resource-name standardDSv5Family \
  --scope "$SCOPE" \
  --limit-object value=500 \
  --resource-type dedicated

az quota request status list --scope "$SCOPE" -o table
```

Most adjustable quotas are approved within minutes; some go to manual review. Ask for headroom
above the immediate need - roughly 20% - because the next request has the same latency and the
quota costs nothing to hold.

## Comparing regions

Capacity differs sharply between regions and between VM families within a region, and a
deployment plan that assumes the first-choice region has capacity is a plan with a single point
of failure.

```bash
for region in westeurope northeurope swedencentral; do
  SCOPE="/subscriptions/$SUB/providers/Microsoft.Compute/locations/$region"
  LIMIT=$(az quota show --resource-name standardDSv5Family --scope "$SCOPE" --query "properties.limit.value" -o tsv)
  USED=$(az quota usage show --resource-name standardDSv5Family --scope "$SCOPE" --query "properties.usages.value" -o tsv)
  echo "$region limit=$LIMIT used=$USED available=$((LIMIT - USED))"
done
```

Also check that the SKU exists in the region at all, and whether it is zone-capable:

```bash
az vm list-skus -l westeurope --size Standard_D4s_v5 \
  --query "[].{name:name, zones:locationInfo[0].zones, restrictions:restrictions[].reasonCode}"
```

A non-empty `restrictions` array with `NotAvailableForSubscription` means the SKU is not offered
to this subscription in that region - a quota increase will not fix it.

## Getting a real price

Use the Retail Prices API, which is unauthenticated and always current:

```bash
curl -s "https://prices.azure.com/api/retail/prices?\$filter=serviceName eq 'Virtual Machines' and armRegionName eq 'westeurope' and armSkuName eq 'Standard_D4s_v5' and priceType eq 'Consumption'" \
  | jq '.Items[] | {sku: armSkuName, meter: meterName, price: retailPrice, unit: unitOfMeasure}'
```

Points that change the answer by more than the rate does:

- Retail prices ignore your enterprise agreement discount, reservations and Azure Hybrid Benefit.
  Quote them as an upper bound, and get the real figure from Cost Management.
- Filter on `priceType eq 'Consumption'` or you will mix in reservation prices and get a number
  that is neither.
- Windows and Linux are different meters for the same VM size.
- Egress, storage transactions and private endpoint hours are separate meters that rarely appear
  in a napkin estimate and frequently dominate it.

Never quote a price from memory. State the assumptions - region, SKU, hours per month, storage
and egress volume - and show the arithmetic, because the assumptions are where the estimate is
wrong.

## Where the money actually goes

In most subscriptions, in rough order: compute that is always on, premium managed disks,
cross-region and internet egress, Log Analytics ingestion, and per-hour platform resources
(Application Gateway, Firewall, NAT Gateway, private endpoints, API Management) that nobody
attributes to a workload because they are shared.

Application Gateway, Azure Firewall and API Management bill per hour whether or not traffic flows.
In a dev subscription, those three can exceed the cost of everything they front.

## Waste shapes

Findable with Resource Graph and worth a scheduled query rather than an annual review:

| Shape | How to find it |
|---|---|
| Unattached managed disks | `resources \| where type =~ 'microsoft.compute/disks' and managedBy == ''` |
| Unassociated public IPs | `resources \| where type =~ 'microsoft.network/publicipaddresses' and isnull(properties.ipConfiguration)` |
| Stopped but not deallocated VMs | `az vm list -d --query "[?powerState=='VM stopped']"` - still billing for compute |
| Empty App Service plans | a plan with zero apps still bills for its instances |
| Orphaned NICs, disk snapshots, old Recovery Services restore points | Resource Graph by type with no parent reference |
| Oversized SKUs | Azure Advisor cost recommendations, which are based on observed utilisation |
| Non-production running at night | `az aks stop`, VM auto-shutdown schedules, scale-to-zero plans |
| Log Analytics ingestion from `allLogs` on a chatty resource | `Usage \| summarize sum(Quantity) by DataType` in the workspace |

`az advisor recommendation list --category Cost` is the cheapest first pass; it sees utilisation
data you do not.

## Commitment discounts

- **Reservations** commit to a specific resource shape (VM family and region, or a managed
  instance) for one or three years. Best for a steady baseline you are confident about.
- **Savings plans** commit to an hourly spend across compute types and regions. Less discount,
  more flexibility - correct when the shape of the fleet is still moving.
- **Azure Hybrid Benefit** applies existing Windows Server and SQL Server licences with Software
  Assurance and is frequently forgotten on new deployments.
- **Dev/Test subscriptions** carry lower rates for non-production, with the restriction that they
  are not for production workloads.

Buy the baseline, not the peak: an over-bought reservation is a sunk cost, while an under-bought
one still saves on what it covers.

## Attributing cost

Cost is attributed by subscription, resource group, resource and **tags**. Since tags do not
inherit, a cost report grouped by `cost-center` is only as good as the policy that enforces the
tag.

```bash
az costmanagement query \
  --type ActualCost --timeframe MonthToDate \
  --scope "/subscriptions/$SUB" \
  --dataset-aggregation '{"total":{"name":"Cost","function":"Sum"}}' \
  --dataset-grouping name="ResourceGroupName" type="Dimension"
```

For anything recurring, configure a Cost Management export to storage and query that; the API is
throttled and paginated, and the export is the supported path for reporting. Budgets with action
groups give an alert at a threshold - they do not stop spending, and nothing in Azure does.

<!-- sources: microsoft-azure-skills, sre-agent-skills, azure-docs, awesome-copilot -->
