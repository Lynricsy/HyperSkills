#!/usr/bin/env bash
# scripts/provision-aks.sh — draft from the platform team.
# Target: 6 internal HTTP services + 2 queue workers, ~40 pods, business hours traffic,
# must reach an Azure SQL private endpoint in the same VNet, EU data residency.
set -euo pipefail

RG=rg-orders-prod
CLUSTER=aks-orders-prod
LOCATION=westeurope
NODE_COUNT=2
NODE_SIZE=Standard_B2s

az group create -n "$RG" -l "$LOCATION"

az aks create \
  --resource-group "$RG" \
  --name "$CLUSTER" \
  --location "$LOCATION" \
  --tier free \
  --node-count "$NODE_COUNT" \
  --node-vm-size "$NODE_SIZE" \
  --network-plugin kubenet \
  --service-principal "$AKS_SP_APPID" \
  --client-secret "$AKS_SP_SECRET" \
  --kubernetes-version 1.29.4 \
  --generate-ssh-keys \
  --attach-acr crordersprod001

az aks get-credentials -g "$RG" -n "$CLUSTER" --admin

# CI pulls images with the ACR admin user
az acr update -n crordersprod001 --admin-enabled true
ACR_PASSWORD=$(az acr credential show -n crordersprod001 --query "passwords[0].value" -o tsv)
kubectl create secret docker-registry acr-creds \
  --docker-server=crordersprod001.azurecr.io \
  --docker-username=crordersprod001 \
  --docker-password="$ACR_PASSWORD"
