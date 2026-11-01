# sub-platform-prod — cost clean-up proposal (draft for Friday's change board)

Owner: platform team. Goal: cut the October run-rate by 25 %. Everything below is marked
"safe to action" by the person who wrote it.

## 1. Why did costs jump?

Daily actual cost from the portal export (EUR):

| Date | Actual cost |
|---|---|
| 2026-10-01 | 4,210 |
| 2026-10-02 | 4,190 |
| 2026-10-03 | 61,880 |
| 2026-10-04 | 4,240 |

Note from finance: "On 3 Oct we bought the 3-year reservation for the Dsv5 fleet, paid upfront."
Draft conclusion: "Something exploded on 3 Oct, probably the AKS cluster. Open an incident."

## 2. The reporting script is broken

`scripts/daily-cost.sh`, which fed the dashboard until we rebuilt the agent image last week:

```bash
az extension add --name costmanagement --upgrade
az costmanagement query \
  --type ActualCost --timeframe MonthToDate \
  --scope "/subscriptions/$SUB" \
  --dataset-aggregation '{"total":{"name":"Cost","function":"Sum"}}' \
  --dataset-grouping name="ResourceGroupName" type="Dimension"
```

Output now: `ERROR: 'query' is misspelled or not recognized by the system.`
Draft action: "Pin the costmanagement extension back to whatever version we had."

## 3. Clean-up list ("safe to action")

| # | Resource | Observation | Proposed action |
|---|---|---|---|
| a | `vm-build-02` (Standard_D8s_v5, rg-ci) | `az vm list -d` shows `VM stopped` since 2026-09-12 | none - "it's already off" |
| b | `asp-legacy-p1v3` (App Service plan, P1v3, 3 instances) | all three web apps on it are in state `Stopped` | none - "apps are stopped so the plan is free" |
| c | 6 managed disks in `rg-dr-westeurope`, names `*-ASRReplica` | `diskState: Unattached`, `managedBy` empty | delete all six |
| d | `ng-app-prod` (NAT gateway) | 2 GB processed last month, associated with `snet-app` (12 VMs, no public IPs) | delete - "basically idle" |
| e | `vm-api-01` (Standard_D8s_v5) | Advisor: resize to Standard_D8as_v5, "save EUR 61/month" | apply now |
| f | `pip-partner-sftp` (Standard public IP) | not attached to anything since the SFTP VM was rebuilt on 2026-10-20 | delete |
