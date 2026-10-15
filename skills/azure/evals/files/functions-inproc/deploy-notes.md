# order-sync deployment notes

- Function App: `func-ordersync-prod` (resource group `rg-orders-prod`)
- Plan: Consumption (Y1), **Linux**
- App settings (from Bicep `functions.bicep`): `FUNCTIONS_EXTENSION_VERSION=~4`,
  `FUNCTIONS_WORKER_RUNTIME=dotnet`, `ServiceBus__fullyQualifiedNamespace=sb-orders-prod.servicebus.windows.net`
- Deployment slot: `staging` (one staging slot beside production)
- CI: `dotnet restore OrderSync.sln && dotnet build OrderSync.sln -c Release && func azure functionapp publish ...`
- The solution also contains `OrderSync.Tests` (xUnit), which deserializes `samples/order.json` into `OrderMessage`.
- Local runs: developers export `FUNCTIONS_WORKER_RUNTIME` in their shell; `local.settings.json` is git-ignored.
