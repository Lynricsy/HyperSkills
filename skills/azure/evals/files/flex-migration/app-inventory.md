# func-doc-intake-prod — inventory for the Flex Consumption move

Current hosting: Consumption plan (`Y1`), **Windows**, PowerShell 7.4, Functions host v4.
Storage account `stdocintakeprod` (also the `AzureWebJobsStorage` account).

## host.json

```json
{
  "version": "2.0",
  "managedDependency": { "enabled": true },
  "extensionBundle": { "id": "Microsoft.Azure.Functions.ExtensionBundle", "version": "[4.*, 5.0.0)" }
}
```

## requirements.psd1

```powershell
@{
    'Az.Accounts' = '3.*'
    'Az.Storage'  = '7.*'
}
```

## Functions

| Function | Trigger | Notes |
|---|---|---|
| `IngestScan` | Blob trigger on `incoming/{name}` in `stdocintakeprod` (default polling, no `source` set) | Calls `Invoke-OcrClient`, writes JSON to `processed/` |
| `NightlyPurge` | Timer `0 0 2 * * *` | Deletes `processed/` blobs older than 30 days |
| `Status` | HTTP GET | Returns queue depth for the ops dashboard |

## Invoke-OcrClient (shared module, `Modules/OcrClient/OcrClient.psm1`)

```powershell
function Invoke-OcrClient([string]$Path) {
    # mTLS to the OCR vendor; cert uploaded to the app and loaded via WEBSITE_LOAD_CERTIFICATES
    $cert = Get-Item "Cert:\CurrentUser\My\$env:OCR_CERT_THUMBPRINT"
    $tmp  = "D:\local\Temp\$([IO.Path]::GetFileName($Path))"
    Invoke-RestMethod -Uri $env:OCR_ENDPOINT -Method Post -InFile $tmp -Certificate $cert
}
```

## Target state agreed with security

- New Flex Consumption app with VNet integration into `vnet-docs-prod/snet-functions`.
- `stdocintakeprod` and the new function app reachable only through private endpoints;
  `publicNetworkAccess: Disabled` on both.
- Cut over in one change window next Thursday.
