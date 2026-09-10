# Inventory service — current endpoint list

Pulled from the router file. Everything is under `https://inv.internal/`.

| Endpoint | Method | Notes |
|---|---|---|
| `/getWarehouseList` | GET | returns every warehouse, no limit |
| `/getWarehouse?id=12` | GET | 200 with `{"error":"not found"}` when the id is unknown |
| `/createWarehouse` | POST | 200 on success, body is the new warehouse |
| `/updateWarehouseName` | POST | 200; also silently creates the warehouse if missing |
| `/deleteWarehouse` | POST | 200 with `{"ok":true}`, 200 with `{"ok":false}` if it did not exist |
| `/warehouse/12/getItems` | GET | returns all stock items for the warehouse |
| `/addItemToWarehouse` | POST | 200; duplicate SKU in the same warehouse overwrites the old row |
| `/setItemQuantity` | POST | 200; negative quantities accepted |
| `/reserveStock` | POST | 200 or 500 with an HTML error page from the proxy |
| `/releaseReservation` | POST | 200 always, even when the reservation id is bogus |
| `/searchItems?q=bolt&page=3` | GET | page size fixed at 20, no total |
| `/exportInventoryCsv` | POST | takes 4-6 minutes, holds the connection open, times out at the LB |
| `/api/v2/warehouses` | GET | someone started a v2 here; v1 has no prefix at all |

Clients: one iOS app (cannot be force-updated), one internal admin SPA, two
partner integrations that we cannot change on our schedule.
