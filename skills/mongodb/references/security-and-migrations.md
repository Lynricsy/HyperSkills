# Security and online change

Verified against: MongoDB 8.0/8.3 documentation; behaviour checks on 8.3.9.

## Contents

- [Authentication](#authentication)
- [Role design](#role-design)
- [Network and TLS](#network-and-tls)
- [Encryption at rest, in transit, in use](#encryption-at-rest-in-transit-in-use)
- [Injection](#injection)
- [Auditing and what leaks into logs](#auditing-and-what-leaks-into-logs)
- [Online collection change](#online-collection-change)
- [Backfilling safely](#backfilling-safely)
- [Adding, changing and removing an index in production](#adding-changing-and-removing-an-index-in-production)

## Authentication

Access control is **off** by default on a `mongod` started without `--auth` or
`security.authorization: enabled`, and the localhost exception then grants full access from
the same machine. A development container with no auth is fine; the same configuration
reachable from a network is an open database.

- `SCRAM-SHA-256` is the default mechanism and the right one for password auth.
- X.509 certificates for service-to-service, and for replica-set member authentication
  (`clusterAuthMode`), which is separate from client auth. Internal member auth must be
  enabled, or any host that can reach the port can join the set.
- Kerberos and LDAP are Enterprise features; OIDC is available for workforce/workload
  identity on current versions.
- Credentials belong in the connection string's source, not in the code. A URI with the
  password in it ends up in logs, in `ps`, and in the error messages the driver prints.

## Role design

Built-in roles are per database: `read`, `readWrite`, `dbAdmin`, `userAdmin`, and the
cluster-wide `readWriteAnyDatabase`, `clusterMonitor`, `root`. Two rules:

- One role per application, scoped to the one database and, where it matters, to the
  collections it uses. A user-defined role with explicit `actions` on named resources is
  cheap to write and is the difference between a bug and a dropped collection.
- A separate read-only user for analytics, dashboards and anything a human pastes into a
  shell. Most incidents are an application credential used interactively.

```javascript
db.createRole({
  role: "orders_app",
  privileges: [
    { resource: { db: "shop", collection: "orders" },
      actions: ["find", "insert", "update", "remove"] },
    { resource: { db: "shop", collection: "order_events" },
      actions: ["find", "insert"] }
  ],
  roles: []
})
```

Audit with `db.getUsers()` and `db.getRoles({showPrivileges: true})`, and check for users
holding `root` or `readWriteAnyDatabase` that should not.

## Network and TLS

Bind to the interfaces that need it (`net.bindIp`), never `0.0.0.0` on a public network,
and put the deployment behind a firewall or private network regardless. `tls.mode:
requireTLS` with `tlsCAFile` for client verification; the driver's
`tlsAllowInvalidCertificates` exists for debugging and turns TLS into theatre in
production.

## Encryption at rest, in transit, in use

- **At rest** — WiredTiger encryption (Enterprise/Atlas) or full-disk encryption. Either
  protects a stolen disk, neither protects a compromised application.
- **In transit** — TLS, above.
- **In use** — Client-Side Field Level Encryption encrypts fields in the driver with keys
  the server never sees; deterministic encryption allows equality queries on the encrypted
  field, randomised does not allow any.
- **Queryable Encryption** is the current form: equality and range queries over encrypted
  fields are supported in production; prefix, suffix and substring queries are public
  preview in 8.2 and explicitly not for production (the GA form will be incompatible with
  the preview). The encrypted fields must be declared in the collection's `encryptedFields`
  at creation time, and cannot be changed afterwards without re-creating the collection.

Both CSFLE and Queryable Encryption require a key-management provider and change the query
surface — decide them at modelling time, not as a hardening pass.

## Injection

The `$`-prefixed keys in a query document are operators, so a filter built from
unvalidated JSON lets a caller send `{"password": {"$ne": null}}` and match every
document. The defences, in order:

- Never build a filter by spreading request bodies into it. Pick the fields explicitly and
  coerce the types.
- Reject `$`-prefixed and dotted keys at the API boundary.
- `$where` and `$function` execute JavaScript on the server: disable server-side scripting
  (`security.javascriptEnabled: false`) unless something needs it, and rewrite `$where` as
  `$expr`.
- `$expr` with a user-supplied expression is the same hazard in a newer wrapper.

## Auditing and what leaks into logs

Enterprise auditing (`auditLog`) records authentication, authorisation failures and DDL.
Without it, the `mongod` log plus the profiler are what you have — and both contain query
predicates, which means they contain user data. Slow-query logging on a collection holding
personal data is a data-protection decision, not just an operational one.

## Online collection change

Classify the change first:

| Change | Safe alone? | Procedure |
|---|---|---|
| Add an optional field | yes | write it; readers default it |
| Add a required field | no | version, backfill, then tighten the validator |
| Change a field's type or shape | no | dual-write both, backfill, switch reads, drop the old |
| Rename a field | no | as above; `$rename` in one `updateMany` over a large collection is a full rewrite |
| Remove a field | no | stop reading, deploy, then `$unset` in batches |
| Split or merge collections | no | dual-write, backfill, switch reads, then stop writing the old |

The invariant behind all of them: a MongoDB collection has no schema, so **the application
is the migration**. A field the readers cannot identify cannot be migrated online, which is
why `schemaVersion` goes in before the first change.

Deploy order is always: readers tolerant → writers new → backfill → readers strict →
cleanup. Each step is its own deploy, and each one is independently revertible.

## Backfilling safely

```javascript
let last = MinKey;
while (true) {
  const batch = db.users.find({ _id: { $gt: last }, schemaVersion: { $lt: 2 } })
                        .sort({ _id: 1 }).limit(1000).toArray();
  if (!batch.length) break;
  db.users.updateMany(
    { _id: { $in: batch.map(d => d._id) } },
    [{ $set: { fullName: { $concat: ["$first", " ", "$last"] }, schemaVersion: 2 } }],
    { writeConcern: { w: "majority" } }
  );
  last = batch[batch.length - 1]._id;
  sleep(100);
}
```

Why each part: bounded by `_id` so it is resumable after any interruption; an
aggregation-pipeline update so the server computes the value without a round trip;
`w: "majority"` so the loop advances only as fast as replication does; a pause so the
secondaries and the balancer get air. Watch `rs.printSecondaryReplicationInfo()` while it
runs and stop if lag climbs.

An unbounded `updateMany` over a large collection is the failure mode: it cannot be
interrupted cleanly, it writes one oplog entry per document as fast as the primary can, and
it is how a backfill becomes a replication incident.

Keep the validator at `validationAction: "warn"` while both shapes exist, and tighten to
`"error"` only after a count of documents not matching the new version returns zero.

## Adding, changing and removing an index in production

- An index build on a replica set runs on every member and takes an exclusive lock only at
  the start and the end. It does not block writes throughout, but it competes for cache and
  I/O for the whole build — start it in a quiet window and watch replication lag.
- `createIndexes` against an existing equivalent index with different options fails rather
  than replacing it. To change options, build under a new name, hide the old, then drop.
- Removing: `hideIndex` → one full business cycle → `dropIndex`. Verified that a hidden
  index is ignored by the planner immediately and restored instantly by `unhideIndex`,
  which is the whole reason to take the detour.
- Do not drop a `unique` or TTL index on usage statistics alone; it is enforcing something,
  not serving queries.
- A TTL index deletes in a background pass roughly once a minute, so "expired" and "gone"
  are different states. Anything that must not be readable after expiry needs the filter in
  the query too.

<!-- sources: mongodb-docs, mongodb-agent-skills, azure-documentdb-kit -->
