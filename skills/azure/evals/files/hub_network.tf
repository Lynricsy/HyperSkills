terraform {
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "subnets" {
  default = ["app", "data", "mgmt", "bastion"]
}

resource "azurerm_resource_group" "hub" {
  name     = "rg-hub-prod"
  location = "westeurope"
}

resource "azurerm_virtual_network" "hub" {
  name                = "vnet-hub-prod"
  location            = azurerm_resource_group.hub.location
  resource_group_name = azurerm_resource_group.hub.name
  address_space       = ["10.10.0.0/16"]
}

resource "azurerm_subnet" "this" {
  count                = length(var.subnets)
  name                 = "snet-${var.subnets[count.index]}"
  resource_group_name  = azurerm_resource_group.hub.name
  virtual_network_name = azurerm_virtual_network.hub.name
  address_prefixes     = [cidrsubnet(azurerm_virtual_network.hub.address_space[0], 8, count.index)]
}

resource "azurerm_network_security_group" "app" {
  name                = "nsg-app-prod"
  location            = azurerm_resource_group.hub.location
  resource_group_name = azurerm_resource_group.hub.name
}

resource "azurerm_subnet_network_security_group_association" "app" {
  subnet_id                 = azurerm_subnet.this[0].id
  network_security_group_id = azurerm_network_security_group.app.id
}
