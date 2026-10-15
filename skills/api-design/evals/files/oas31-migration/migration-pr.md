# PR #412: Move catalog-openapi.yaml from OpenAPI 3.0.3 to 3.1.0

The contract is published to partners and feeds our TypeScript and Java SDK generators and
the docs portal. Both SDK generators and the docs portal build run cleanly on this branch.

## What I changed

1. `openapi: 3.0.3` -> `openapi: 3.1.0`.
2. Deleted the `discriminator` block from `PaymentMethod`:

   ```yaml
   discriminator:
     propertyName: kind
     mapping:
       card: "#/components/schemas/CardPayment"
       bank_transfer: "#/components/schemas/BankTransferPayment"
   ```

   3.1 schemas are plain JSON Schema 2020-12 now and `discriminator` is not a JSON Schema
   keyword, so it was dropped from the spec. The `const` on `kind` does the job instead.
3. Deleted the `xml` block from `Product` (`xml: { name: product, namespace: "https://schemas.example.com/catalog" }`,
   plus `xml: { attribute: true }` on `sku`). Same reason as 2. The legacy partner XML feed
   still uses `application/xml` on `GET /products/{sku}`.
4. Deleted every schema-level `example:` (`sku: AB-1234`, `price: 19.99`, `last4: "4242"`, ...).
   `example` was removed in 3.1 in favour of `examples`; I'll add `examples` back in a later PR
   once the docs portal supports them.
5. Left `nullable: true` on `replacementSku` and `discontinuedAt` as it was. The generators and
   the portal accept it without complaint, so it is still valid.
6. Wrapped the `$ref` under `Product.category` in `allOf` so the `description` next to it is
   not ignored.

Please review before I merge; the 2.3.0 contract goes out to partners on Monday.
