// infra/main.bicep — platform team, "orders" workload
targetScope = 'resourceGroup'

@description('Environment name')
@allowed([
  'dev'
  'test'
  'prod'
])
param env string = 'dev'

@description('Workload name')
param workload string = 'orders-api'

@secure()
@description('SQL administrator password')
param sqlAdminPassword string = 'Contoso!Passw0rd2024'

param location string = 'eastus'

var storageName = 'st-${workload}-${env}-${uniqueString(resourceGroup().id)}'
var planName = 'plan-${workload}-${env}'
var siteName = 'app-${workload}-${env}'

resource storage 'Microsoft.Storage/storageAccounts@2021-04-01' = {
  name: storageName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: true
  }
}

resource plan 'Microsoft.Web/serverfarms@2021-02-01' = {
  name: planName
  location: location
  sku: {
    name: 'S1'
    tier: 'Standard'
  }
}

resource site 'Microsoft.Web/sites@2021-02-01' = {
  name: siteName
  location: location
  properties: {
    serverFarmId: resourceId('Microsoft.Web/serverfarms', planName)
    siteConfig: {
      appSettings: [
        {
          name: 'STORAGE_CONNECTION_STRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageName};AccountKey=${listKeys(resourceId('Microsoft.Storage/storageAccounts', storageName), '2021-04-01').keys[0].value}'
        }
        {
          name: 'SQL_PASSWORD'
          value: sqlAdminPassword
        }
        {
          name: 'APPINSIGHTS_ENDPOINT'
          value: 'https://dc.applicationinsights.azure.com/v2/track'
        }
      ]
    }
  }
  dependsOn: [
    plan
    storage
  ]
}

resource ownerAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: '${workload}-owner-assignment'
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8e3af657-a8ff-443c-a75c-2fe8c4bcb635')
    principalId: reference(resourceId('Microsoft.Web/sites', siteName), '2021-02-01', 'Full').identity.principalId
  }
}

output storageAccountKey string = listKeys(resourceId('Microsoft.Storage/storageAccounts', storageName), '2021-04-01').keys[0].value
output siteUrl string = 'https://${siteName}.azurewebsites.net'
