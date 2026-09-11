# Durable Object class lifecycle

Verified against: wrangler 4.131.0. Every operation here is destructive or irreversible in some
direction, so the order of deploys matters more than the syntax.

## Contents

- [Two flows, one at a time](#two-flows-one-at-a-time)
- [How exports reconciliation works](#how-exports-reconciliation-works)
- [Create](#create)
- [Delete](#delete)
- [Rename safely](#rename-safely)
- [Transfer between Workers](#transfer-between-workers)
- [Storage backends](#storage-backends)
- [Constraints that break deploy pipelines](#constraints-that-break-deploy-pipelines)
- [Converting off the legacy migrations array](#converting-off-the-legacy-migrations-array)

## Two flows, one at a time

A Worker declares Durable Object class lifecycle either with the declarative `exports` map
(Wrangler 4.107+) or with the legacy imperative `migrations` array. They are **mutually
exclusive at config validation** — a configuration containing both is rejected before anything
is uploaded: `[verified]`

```
✘ [ERROR] Processing wrangler.jsonc configuration:
  - `migrations` and `exports` are mutually exclusive. Choose one or the other to declare
    your Durable Object lifecycle, but not both.
```

`exports` is the current mechanism and the one to write for anything new. Converting an
existing Worker needs no data migration, but it is **one-way**: once a Worker has deployed with
`exports`, later deploys cannot return to `migrations`. Decide the route explicitly rather than
drifting into it by adding one `exports` entry to a `migrations` config.

## How exports reconciliation works

On deploy, Cloudflare compares three things: the classes the code actually exports, what
`exports` declares, and the namespaces already provisioned for this Worker. The current state
of the map is the source of truth — there is no `tag` and no history to keep.

The rule that surprises people: **a class present only in the code is ignored.** No namespace
is provisioned implicitly. A class you exported but never declared simply does not exist as a
Durable Object, and `env.X` for it is undefined rather than an error at deploy time.

`wrangler deploy` prints a `Durable Object exports reconciliation` block whenever a lifecycle
change applies or produces notices, and lists stale tombstones under `removable_entries` so you
know which entries can be dropped from the config.

| Operation | `state` | Required fields |
|---|---|---|
| Create (default) | `"created"` or omitted | `storage` |
| Delete | `"deleted"` | — |
| Rename | `"renamed"` | `renamed_to` |
| Transfer out | `"transferred"` | `transferred_to` |
| Receive a transfer | `"expecting-transfer"` | `storage`, `transfer_from` |

## Create

```jsonc
{
  "durable_objects": {
    "bindings": [{ "name": "ROOM", "class_name": "Room" }]
  },
  "exports": {
    "Room": { "type": "durable-object", "storage": "sqlite" }
  }
}
```

`storage` is required on live entries. The namespace is provisioned on the first deploy that
declares it; later deploys with the same entry change nothing and simply confirm the class is
still live. A class needs a `durable_objects.bindings` entry as well if the Worker reaches it
through `env`.

## Delete

Deleting removes the namespace and **all stored data, permanently**. There is no trash and no
soft delete. Copy anything you need out first.

```jsonc
{ "exports": { "OldRoom": { "type": "durable-object", "state": "deleted" } } }
```

Two preconditions are enforced at deploy time: the class must be **absent from the code** (a
live binding cannot resolve to a deleted namespace), and no other Worker in the account may
bind it — otherwise the deploy is rejected with
`tombstone_delete_blocked_by_external_bindings` and the list of referencing scripts. Redeploy
those Workers without the binding first.

## Rename safely

A rename moves stored data from one class name to another inside the same Worker. Expressing it
as delete-plus-create is **data loss that deploys cleanly** — the old namespace and every
object in it is destroyed, and the new name starts empty.

The rename needs a tombstone keyed by the old name and a live entry for the new one in the same
map:

```jsonc
{
  "exports": {
    "OldName": { "type": "durable-object", "state": "renamed", "renamed_to": "NewName" },
    "NewName": { "type": "durable-object", "storage": "sqlite" }
  }
}
```

`renamed_to` must be a valid identifier, differ from the source, appear as a live entry in the
same map, and not collide with an existing namespace on this Worker.

**Use three deploys.** The namespace's class pointer and the deployed code do not flip
atomically; for a few seconds during rollout one may be visible without the other.

1. **Alias.** Make the new name canonical in code and re-export it under the old name. Leave
   `exports` unchanged. Deploy.
   ```ts
   export class NewName extends DurableObject { /* … */ }
   export { NewName as OldName };
   ```
2. **Rename while the alias is live.** Add the `renamed` tombstone and the new live entry.
   Deploy. A `tombstone_class_still_in_code` info notice is expected here and confirms the safe
   pattern.
3. **Drop the alias.** Remove `export { NewName as OldName }`. Deploy. The tombstone is now
   stale and appears in `removable_entries`; delete it from the config at your leisure.

## Transfer between Workers

Transfer moves a provisioned namespace from a source Worker to a target Worker in the same
account, and needs four coordinated deploys because two Workers must agree. The target declares
`expecting-transfer` with `transfer_from: "<source-worker>"`; the source declares
`transferred` with `transferred_to: "<target-worker>"`. **The handoff commits when the source
Worker's deploy lands.**

Do not add a `durable_objects.bindings` entry for the class on the target while it is still in
the `expecting-transfer` phase — self-referencing bindings are not routed through the source's
namespace during that window. A pending transfer can be cancelled by removing the
`expecting-transfer` entry before the source deploys.

## Storage backends

```
"storage": "sqlite"      // the only option for new namespaces
"storage": "legacy-kv"   // accepted only for already-provisioned key-value namespaces
```

- SQLite-backed is the recommended and only path for new namespaces: SQL, Point-in-Time
  Recovery over 30 days, and a higher per-object storage limit.
- New key-value-backed namespaces cannot be created at all through `exports`, and accounts
  without an existing key-value namespace cannot create one by any route. Workers Free has only
  SQLite.
- **Storage type is immutable once provisioned.** Switching a live entry between `sqlite` and
  `legacy-kv` is rejected with `storage_type_mismatch`. Genuinely changing backends means
  deleting the namespace and re-provisioning, with full data loss in between.
- To work out an existing class's backend, trace it to the migration that created it: classes
  introduced with `new_sqlite_classes` are `sqlite`; classes introduced with `new_classes` are
  `legacy-kv`.

## Constraints that break deploy pipelines

- `exports` and `migrations` are mutually exclusive, and `exports` is one-way.
- **`wrangler versions upload` does not apply lifecycle changes** and fails fast when the
  config contains `exports` entries. Lifecycle changes go through `wrangler deploy`.
- **Gradual deployments do not support lifecycle changes** — they are atomic at the control
  plane and cannot be split across versions.
- **A rollback cannot cross a lifecycle change.** You cannot roll back to a version deployed
  before an `exports`-driven lifecycle change.
- Ship one lifecycle change per deploy, separate from feature changes, so that the deploy you
  cannot roll back is as small as possible.

## Converting off the legacy migrations array

No data moves; only the configuration shape changes. Work out each live class's backend from
the migration that created it, then replace the whole array:

```jsonc
// before
{ "migrations": [{ "tag": "v1", "new_sqlite_classes": ["ChatRoom"] }] }

// after
{ "exports": { "ChatRoom": { "type": "durable-object", "storage": "sqlite" } } }
```

Then deploy. Future deletes, renames and transfers happen entirely through `exports`.

<details>
<summary>The legacy `migrations` array, for Workers that stay on it</summary>

Each entry needs a **unique** `tag`; entries are applied in order and the history is kept
forever. Duplicated tags are invalid. The operations are `new_sqlite_classes`,
`new_classes` (key-value backend, no longer available for new namespaces),
`renamed_classes: [{ "from": "A", "to": "B" }]` and `deleted_classes`. The same rules about
data loss, one-lifecycle-change-per-deploy and `versions upload` apply. Historical entries must
not be edited or reordered — they describe what was already applied, including which backend
each class got.

</details>

<!-- sources: cloudflare-docs, workers-sdk, cloudflare-skills -->
