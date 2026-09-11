# Semantic conventions: stability and migration

Verified against: open-telemetry/semantic-conventions v1.44.0 (latest release), otelcol-contrib
0.160.0.

## Contents

- [Why this is a versioning problem](#why-this-is-a-versioning-problem)
- [Stability levels](#stability-levels)
- [The domains](#the-domains)
- [`OTEL_SEMCONV_STABILITY_OPT_IN`](#otel_semconv_stability_opt_in)
- [Declarative version selection](#declarative-version-selection)
- [The renames that matter](#the-renames-that-matter)
- [`schema_url` and translation](#schema_url-and-translation)
- [Where `gen_ai.*` went](#where-gen_ai-went)
- [Inventing an attribute](#inventing-an-attribute)
- [Reviewing a convention change](#reviewing-a-convention-change)

## Why this is a versioning problem

Semantic conventions look like a naming guide and behave like a dependency. Three things move
independently:

1. The convention document — what the attribute is called and what it means.
2. The instrumentation library — which version of the convention it emits.
3. The consumer — dashboards, alerts, recording rules and the backend's own normalisation.

A fleet can therefore be emitting three convention versions at once, with dashboards written
against a fourth. The symptom is never an error: it is a panel that goes empty for some services,
or an alert that stops matching after a dependency bump.

The practical consequence: do not reason about attribute names from memory. Check the released
convention for the version in play, and check what the instrumentation is actually emitting.

## Stability levels

| Level | Meaning | How to treat it |
|---|---|---|
| Stable | Will not change in a breaking way | Depend on it freely |
| Development / Experimental | May change or be removed | Use only when no stable alternative exists, and leave a comment saying so |
| Deprecated | Superseded by a newer key | Migrate; the old key keeps working for a while and then stops |

Stability is per convention area, and within an area it can be mixed — the HTTP document is marked
**Mixed**, not uniformly stable. "Is OTel semconv stable?" has no single answer; the answerable
question is "is *this* group, at *this* version, stable?"

Prefer the stable set. Where you must use a development-stage attribute, write a code comment
naming it as experimental so it surfaces the next time the dependency is bumped, rather than
being discovered when a dashboard empties.

## The domains

The conventions are organised by area, and this list is what to check against before inventing a
key: general, CI/CD, cloud providers, CloudEvents, database, DNS, exceptions, FaaS, feature flags,
GraphQL, hardware, HTTP, messaging, mobile, NFS, object stores, RPC, runtime, system, URL, plus
per-signal documents for events, logs, metrics, profiles, resource and trace, and the
`registry/attributes/` index of every individual attribute.

Two of these are worth knowing about specifically: `registry/attributes/` is the fast way to check
whether a key already exists, and `non-normative/` holds the migration guides — including per-area
documents for HTTP, database, RPC, code attributes and Kubernetes attributes, which are the ones
with real churn.

## `OTEL_SEMCONV_STABILITY_OPT_IN`

This is the mechanism by which an instrumentation library moves from its old experimental
attribute names to the stable ones without breaking its consumers. It is the single most useful
fact in this reference, because the rename tables are easy to look up and this is not.

The environment variable takes a comma-separated list of category-specific values:

| Value | Behaviour |
|---|---|
| `<category>` (e.g. `http`, `database`, `messaging`, `rpc`) | Emit the stable conventions for that category and stop emitting the old experimental ones |
| `<category>/dup` | Emit **both** the old and the stable conventions, so a consumer can migrate in stages |
| absent | Keep emitting whatever the instrumentation emitted before — the default is no change |

When both `<category>` and `<category>/dup` are present, **`/dup` wins.** That precedence is the
detail that decides whether a phased migration works or silently skips its dual-emit phase.

The intended sequence for a migration:

1. Set `<category>/dup` in production. Both name sets flow; nothing breaks.
2. Migrate dashboards, alerts and recording rules to the stable names while both exist.
3. Switch to `<category>` alone. Old names stop.
4. Remove the variable at the next major version of the instrumentation.

Libraries that are already stable do not read this variable — they emit stable conventions
unconditionally. The variable exists for instrumentation that shipped before its area stabilised,
which is why a library upgrade can change attribute names all by itself if the library crossed
that boundary in the meantime. [official]

## Declarative version selection

Newer SDKs also expose convention version selection through declarative configuration, under
`.instrumentation/development.general.<domain>.semconv`, where `<domain>` is one of `code`, `db`,
`gen_ai`, `http`, `k8s`, `messaging` or `rpc`. The properties are `version` (required, an
integer), `experimental` (include development-stage conventions, default false) and `dual_emit`
(also emit the previous major version, default false).

The path itself contains `development`, and the document's status is Development: treat this as a
preview, not as a stable interface, and keep `OTEL_SEMCONV_STABILITY_OPT_IN` as the mechanism to
reach for in production until the path loses that segment. Note also that `version` here is a
convention *major* version (`1`, `2`), not a semconv release like `1.44.0` — mixing the two up
produces a configuration error at best and a silently ignored setting at worst. [official]

## The renames that matter

Current name on the right. If the left appears in code, a dashboard, or an alert expression, it is
a migration item, not a style preference:

| Deprecated | Current |
|---|---|
| `http.method` | `http.request.method` |
| `http.status_code` | `http.response.status_code` |
| `http.url` | `url.full` |
| `http.target` | `url.path` + `url.query` |
| `http.scheme` | `url.scheme` |
| `http.flavor` | `network.protocol.version` |
| `http.user_agent` | `user_agent.original` |
| `http.client_ip` | `client.address` |
| `net.peer.name` / `net.host.name` | `server.address` |
| `net.peer.port` / `net.host.port` | `server.port` |
| `db.system` | `db.system.name` |
| `db.name` | `db.namespace` |
| `db.statement` | `db.query.text` |
| `db.operation` | `db.operation.name` |
| `deployment.environment` | `deployment.environment.name` (deprecated since v1.27.0) |
| `http.server.duration` | `http.server.request.duration` — **and the unit changed from ms to s** |
| `http.client.duration` | `http.client.request.duration` — **and the unit changed from ms to s** |

The last two are the dangerous rows, and the HTTP migration guide is explicit about them: the name
changed, the unit changed from `ms` to `s`, **and the default histogram bucket boundaries were
re-derived for seconds with the zero boundary removed**. A threshold carried over from the old
metric is therefore wrong by a factor of 1000 — `> 800` against the seconds-unit metric means 800
seconds, so the alert can never fire — and pre-existing custom bucket boundaries are wrong too.
Any migration touching a duration metric re-derives its thresholds and its buckets rather than
porting them. The stable HTTP conventions these rows migrate to were published in v1.23.1.

## `schema_url` and translation

Each resource and instrumentation scope may carry a `schema_url` naming the convention version it
was written against — for example `https://opentelemetry.io/schemas/1.40.0`. It is visible in
Collector output with a `debug` exporter at `verbosity: detailed`:

```
ResourceSpans #0
Resource SchemaURL: https://opentelemetry.io/schemas/1.40.0
```

Two uses:

- **Diagnosis.** When two services disagree about an attribute name, compare their `schema_url`
  values first. It is faster and more reliable than reading either dependency tree. [verified]
- **Translation.** A schema file describes the transformations between versions, which lets a
  pipeline normalise mixed-version telemetry to a single version at ingest. Several backends do
  this for you; where they do, know which version they normalise to, because that is the version
  your dashboards must be written against.

Translation at ingest is a convenience, not a licence to leave instrumentation stale: it cannot
invent an attribute the old version never emitted, and it cannot fix a unit change in a metric
that was recorded in the wrong unit.

## Where `gen_ai.*` went

The GenAI conventions — `gen_ai.*`, and the OpenAI and MCP-specific documents — moved out of the
core `semantic-conventions` repository in **v1.42.0** to a dedicated
`open-telemetry/semantic-conventions-genai` repository. The core repository keeps only deprecated
stubs from before that release.

Practical consequence: an answer about `gen_ai.*` attributes sourced from the core repository is
reading a stub. Go to the GenAI repository instead. Instrumenting LLM calls itself is not covered
by any skill in this library yet; say so rather than improvising conventions. [official]

## Inventing an attribute

Only after checking the registry, and then with three constraints:

1. **Namespace it with something you own.** `com.acme.order.priority`, not `priority`. An
   unnamespaced custom key will eventually collide with a convention key that means something
   else.
2. **Bound the values.** Custom or not, an unbounded value on a metric is still a cardinality bug,
   and an unbounded value in a span name is still one operation per entity.
3. **Do not shadow a convention key with different semantics.** Reusing `http.route` for something
   that is not a route silently corrupts every consumer that trusts the convention — including the
   backend's own normalisation.

When a stable key exists for the concept, use it even if a custom name reads better locally. The
value of a convention is that a consumer who has never seen your service can query it.

## Reviewing a convention change

- Are any deprecated keys being introduced, including in dashboards and alert expressions?
- Does any key carry a value the convention does not define — free text where an enum is
  specified, a raw path where a template is specified?
- Are there two names for one concept across services (`status`, `status_code`, `http_status`)?
  That is three label families, and joins between them fail.
- Does a duration metric rename also change the unit? Then every threshold on it is wrong.
- Is a development-stage attribute being used where a stable one exists?
- Are custom keys namespaced, and bounded where the signal requires it?
- Does the change affect a stream whose `schema_url` claims an older version? Then either
  `schema_url` is stale or the attribute is not what it claims.

<!-- sources: otel-semconv, ollygarden-otel-skills, dash0-agent-skills, otel-docs, otel-collector-contrib, getsentry-sdk-skills -->
