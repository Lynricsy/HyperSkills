# Cluster context

## aks-shop-prod (rg-shop-prod, westeurope)
- Public API server with authorized IP ranges, Azure CNI Overlay.
- Pool `npapps`: Standard_D16ds_v5, zones 1 2 3, 12 nodes, upgrade from 1.33.5 to 1.34.2 in progress.
  Regional vCPU quota for DDSv5 family: 512, used 192.
- Pool `npcache` is new; Alice copied the flags from our "production cluster" runbook
  (`--node-vm-size Standard_D4s_v5 --node-osdisk-type Ephemeral`).

## aks-pay-prod (rg-payments-prod, westeurope)
- Private cluster (`--enable-private-cluster`), private DNS zone `privatelink.westeurope.azmk8s.io`
  created by AKS in the node resource group.
- Spoke VNet `vnet-pay-spoke` uses custom DNS servers 10.10.0.4 and 10.10.0.5 (domain controllers in the hub).
- The hub DNS servers forward everything they are not authoritative for to the on-premises resolvers
  (192.168.50.10). Existing nodes were created before the spoke switched to custom DNS last week.
