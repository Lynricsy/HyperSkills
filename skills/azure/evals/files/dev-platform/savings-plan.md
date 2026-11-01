# Dev platform savings plan - Q4

Prepared by the platform team for the dev/test subscription. Please sanity-check before we
start on Monday.

## aks-dev (AKS, Base SKU, Standard tier)

Current state (`az aks show` trimmed):

```json
{
  "sku": { "name": "Base", "tier": "Standard" },
  "identity": { "type": "SystemAssigned" },
  "networkProfile": {
    "networkPlugin": "kubenet",
    "networkPolicy": "calico",
    "loadBalancerSku": "standard",
    "outboundType": "loadBalancer"
  },
  "nodeProvisioningProfile": { "mode": "Manual" },
  "agentPoolProfiles": [
    { "name": "npsystem", "osType": "Linux",   "mode": "System", "enableAutoScaling": false, "count": 2 },
    { "name": "npapps",   "osType": "Linux",   "mode": "User",   "enableAutoScaling": true,  "minCount": 3, "maxCount": 12 },
    { "name": "npwin",    "osType": "Windows", "mode": "User",   "enableAutoScaling": false, "count": 2 }
  ]
}
```

Plan:

1. Enable Node Auto Provisioning: `az aks update -g rg-dev -n aks-dev --node-provisioning-mode Auto`.
   "NAP always beats the cluster autoscaler on cost, so this is pure savings."
2. Keep the nightly pipeline that runs `az aks stop -g rg-dev -n aks-dev` at 20:00 and
   `az aks start` at 07:00.
3. Later in the quarter: switch the outbound type to `userAssignedNATGateway`.

## hooks-relay (Go webhook relay, currently a VM)

The relay is a small Go 1.25 HTTP service on a B2s VM that is idle most of the day. Plan: move it
to Azure Functions as a **custom handler on an Elastic Premium EP1 plan**, because "native Go on
Functions is still a preview that needs HTTP/2 switched off, and Flex Consumption does not take
Go".
