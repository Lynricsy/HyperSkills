# Writing and validating an OpenAPI 3.1 document

## Contents

- [Which version to write](#which-version-to-write)
- [What 3.1 changed](#what-31-changed)
- [Design-first, code-first, hybrid](#design-first-code-first-hybrid)
- [Document skeleton](#document-skeleton)
- [Authoring discipline](#authoring-discipline)
- [Gate 1: lint](#gate-1-lint)
- [Gate 2: mock](#gate-2-mock)
- [Mistakes that lint will not catch](#mistakes-that-lint-will-not-catch)

## Which version to write

Write `openapi: 3.1.0` unless the project already standardised elsewhere. 3.1 is what the
current tool ecosystem and the widely used public guidelines target.

3.2 exists (its first patch release followed a year after 3.2.0) and the tooling is starting
to follow — Redocly CLI 2.52 validates a 3.2 document as readily as a 3.1 one `[verified]`.
Move when the generators, mock servers and documentation renderers a project actually depends
on all accept it; until then a 3.2 document buys nothing and costs compatibility.

Do not write 3.0 for a new API: its Schema Object is a JSON Schema dialect of its own, so
every schema written there has to be revisited later.

## What 3.1 changed

The Schema Object is now plain JSON Schema 2020-12. Three consequences that break documents
carried over from 3.0: `[official]`

| 3.0 | 3.1 |
|---|---|
| `nullable: true` | `type: [string, "null"]` |
| `example: 5` inside a schema | `examples: [5]` (an array) |
| `$ref` had to stand alone | sibling keywords next to `$ref` are allowed |

`nullable` is the trap: it is not an error in 3.1, it is an unknown keyword, so tools ignore
it silently and the schema now accepts `null` nowhere. Grep for it whenever a document was
migrated.

Also new in 3.1: `webhooks` as a top-level entry point for callbacks your API sends, and
`info.summary`. `paths` is no longer required, so a document can describe webhooks only.

## Design-first, code-first, hybrid

| Approach | Right when |
|---|---|
| Design-first — the document is the source, code is generated or hand-written against it | A new API, or any contract with consumers outside your team. The contract can be reviewed before anything is built |
| Code-first — the document is generated from annotations | An existing API whose behaviour is the truth and whose document is currently a lie |
| Hybrid — annotate code, generate, then diff against a reviewed document in CI | A living API where the document must stay honest without freezing development |

Design-first is the default for anything this skill is used for: the point of contract design
is to make the decisions before they are expensive. Where a framework generates the document,
the contract still has to be reviewed as a document — a generated document reflects the
implementation, including its accidents.

## Document skeleton

```yaml
openapi: 3.1.0
info:
  title: Shipments API
  version: 1.4.0            # document version, not the API's major version
  license: { name: Apache-2.0, identifier: Apache-2.0 }
servers:
  - url: https://api.example.com/v1
security:
  - bearerAuth: []          # default for every operation; override per operation
paths:
  /shipments:
    get:
      operationId: listShipments      # unique; SDK method names come from this
      summary: List shipments
      parameters:
        - { $ref: "#/components/parameters/PageAfter" }
        - { $ref: "#/components/parameters/PageSize" }
      responses:
        "200":
          description: A page of shipments.
          headers:
            ETag: { schema: { type: string } }
          content:
            application/json:
              schema: { $ref: "#/components/schemas/ShipmentPage" }
        "400": { $ref: "#/components/responses/Problem" }
        "401": { $ref: "#/components/responses/Problem" }
        "429": { $ref: "#/components/responses/Problem" }
components:
  securitySchemes:
    bearerAuth: { type: http, scheme: bearer }
  parameters:
    PageAfter:
      name: page[after]
      in: query
      description: Opaque cursor from a previous response's `links.next`.
      schema: { type: string }
    PageSize:
      name: page[size]
      in: query
      schema: { type: integer, default: 25, maximum: 100 }
  responses:
    Problem:
      description: RFC 9457 problem details.
      content:
        application/problem+json:
          schema: { $ref: "#/components/schemas/Problem" }
  schemas:
    Problem:
      type: object
      required: [type, title, status]
      properties:
        type: { type: string, format: uri }
        title: { type: string }
        status: { type: integer }
        detail: { type: string }
        instance: { type: string }
      examples:
        - type: https://api.example.com/problems/validation-error
          title: Request body failed validation
          status: 422
```

## Authoring discipline

- **One self-contained document per API.** Split source files if the team prefers, but publish
  a bundled single file: consumers, linters and mock servers all handle one file reliably and
  remote `$ref` chains poorly.
- **`$ref` everything reusable** — problem responses, pagination parameters, the error schema,
  every entity. A copied schema drifts, and the drift shows up as an inconsistent API.
- **Distinct read and write schemas** (`Shipment` and `ShipmentCreate`) where server-owned
  fields exist. Mark server-owned properties `readOnly: true` so a generator does not put
  them in the create model.
- **Every operation declares every response it can return**, including 401, 403 and 429.
  Undeclared error responses are the most common gap, and the one that makes generated
  clients throw on paths you knew about.
- **Examples on every schema and every non-trivial response.** They are the part humans read,
  and they are what a mock server serves — a document without examples produces mocks full of
  `"string"`.
- **`operationId` on every operation**, stable forever: SDK method names derive from it, so
  changing one is a breaking change for generated clients.
- **Descriptions state the contract, not the obvious.** `description: The shipment id` earns
  nothing; `Opaque cursor from a previous response's links.next; do not construct` earns its
  bytes.
- **Constraints belong in the schema** (`maximum`, `minLength`, `pattern`, `enum`, `format`).
  A bound that lives only in prose cannot be validated or mocked — and once documented, a
  bound is contract.
- **`security` at the top level with per-operation overrides.** Declaring it per operation
  means the one you forget is public.

## Gate 1: lint

```
npx @redocly/cli@latest lint openapi.yaml
```

- Exit 0 means no errors; **warnings do not affect the exit code** `[verified]`. Read them
  anyway: either fix them or turn them off explicitly in `redocly.yaml`, so the next person
  does not have to re-triage the same list.
- Structural mistakes it does catch: a `$ref` to a schema that does not exist, an undefined
  security scheme, a response with no description, duplicate `operationId`s. A dangling
  `$ref` is one error and exit 1 `[verified]`.
- Run it in CI on the published document. A contract nobody validates drifts back into
  hand-maintained prose.

## Gate 2: mock

```
npx @stoplight/prism-cli@latest mock openapi.yaml --port 4010
```

Then exercise the paths that matter — the happy path, the paginated listing, one validation
failure, one auth failure:

```
curl -i -H 'Authorization: Bearer t' 'http://127.0.0.1:4010/shipments?page[size]=2'
curl -i -X POST http://127.0.0.1:4010/shipments -H 'Authorization: Bearer t' \
     -H 'Content-Type: application/json' -d '{"weight_grams":0}'
```

What the mock tells you that the linter cannot `[verified]`:

- **Missing error responses.** Prism enforces the document's `security`, and when the
  document declares no 401 it synthesises one of its own with a `detail` saying so. Any
  synthesised response is a hole in the contract.
- **Whether declared constraints are real.** A body violating `minimum: 1` is rejected and
  answered with the documented error response that matches; if nothing matches, clients would
  have received a body you never designed.
- **Whether required headers are actually required.** Omit `Idempotency-Key` and see whether
  the request is rejected.
- **How thin the examples are.** A response of `{"total": "string"}` is the document telling
  you that field has no example.

Keep the mock running while writing the client-side integration: a contract that a real HTTP
client can drive is a contract that survives review.

## Mistakes that lint will not catch

- A collection endpoint with no pagination parameters, or pagination parameters with no
  documented maximum.
- A bare array as a top-level response schema.
- `nullable: true` left over from 3.0.
- Error responses typed as `application/json` rather than `application/problem+json`.
- `example`/`examples` values that contradict the schema's own constraints.
- A `PATCH` body declared as `application/json` with no merge-patch or JSON-Patch semantics
  stated.
- Server-owned fields present in the create schema without `readOnly`.
- `servers` still pointing at `example.com` or `localhost` — this one is a warning, so it
  ships unless someone reads warnings.
- A version bump in `info.version` mistaken for an API version bump.

<!-- sources: openapi-spec, jeffallan-api-designer, wshobson-openapi-spec-generation, zalando-guidelines, rfc9457, redocly-cli, prism-cli -->
