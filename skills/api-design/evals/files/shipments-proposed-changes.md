# Proposed changes for the next Shipments API release

Product wants all of this shipped as `1.5.0` on the existing `/v1` base path.
Two partner integrations and a warehouse scanner firmware (updated twice a year)
consume this API today.

1. `GET /shipments` starts returning `{ "items": [...], "next": "<cursor>" }`
   with a default page size of 100 instead of the bare array.
2. `ShipmentCreate` gains a required `carrier_code` field so we stop guessing
   the carrier.
3. `Shipment.notes` is renamed to `internal_notes` because that is what it
   actually holds.
4. `Shipment.status` gains a `returned` value.
5. `Shipment.id` changes from `integer` to a ULID string; the old numeric ids
   keep working as an alias for six months.
6. `Shipment.weight_kg` is documented as "grams" instead, since the warehouse
   has been sending grams all along and nobody noticed.
7. `carrier_ref` `maxLength` goes from 20 to 64 to fit the new carrier's refs.
8. `POST /shipments` starts returning `201` instead of `200`.
9. A new optional `insured_value` field is added to `ShipmentCreate`.
10. `GET /shipments?status=` gains `cancelled` as an accepted value.
11. The old `/shipments/{id}` numeric-id route will be removed "eventually" —
    the plan is to just announce it in the changelog.
