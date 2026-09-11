# Data persistence

Verified against: OpenHarmony application-dev docs, `database/data-persistence-by-preferences`, `data-persistence-by-rdb-store`, `preferences-guidelines`, `ui/state-management/arkts-new-persistencev2`, `arkts-appstorage`.

## Contents

- [Choosing a store](#choosing-a-store)
- [Preferences](#preferences)
- [RelationalStore](#relationalstore)
- [PersistenceV2](#persistencev2)
- [Files](#files)
- [Encryption and secrets](#encryption-and-secrets)
- [Migration and schema change](#migration-and-schema-change)
- [Failure table](#failure-table)

## Choosing a store

| Need | Use |
|---|---|
| A handful of settings and flags | `Preferences` |
| UI state that must survive a restart | `PersistenceV2` (V2) / `PersistStorage` (V1) |
| Structured, queryable records | `RelationalStore` (RDB) |
| Large blobs, media, exports | the file system via `Context` directories |
| Key-value data that must sync across devices | distributed KV store |
| Secrets | the key store / universal keystore, never any of the above |

The line between `Preferences` and RDB is not data size alone: `Preferences` keeps the whole
store in memory and has no query language, so a hundred settings is fine and a thousand
records with filtering is not.

## Preferences

Key-value, file-backed plus an in-memory cache.

Hard limits:

- Key: a non-empty string, **at most 1024 bytes**.
- String value: UTF-8, may be empty, **at most 16 MB**.
- **No encryption.** If the data is sensitive you must encrypt it yourself and store the
  ciphertext as a `Uint8Array`. A session token in plain `Preferences` is readable by
  anything with access to the sandbox — and caching an authorization decision there is
  wrong for a second reason (see `references/stage-model.md`).

Two storage formats, and the boundary is version-gated:

| Format | Availability | Notes |
|---|---|---|
| XML | the original ArkTS format | single-process |
| GSKV | **API version 18+** | binary, multi-process concurrent read/write, writes flushed to storage immediately |

Before API 18, ArkTS APIs supported only XML and C APIs only GSKV, so the two languages
**could not operate the same instance**. From API 18 both support both formats, and they
can share an instance only if they use the same format. A native module and an ArkTS module
that disagree on format silently read different data.

Behavioural traps:

- After `removePreferencesFromCache()` or `deletePreferences()`, data-change subscriptions
  are **cancelled automatically**. Calling `getPreferences()` again gives you an instance
  with no observers; you must re-subscribe. An "observer stopped firing after we cleared the
  cache" bug is always this.
- Do not call `deletePreferences()` concurrently with any other Preferences API across
  threads or processes — the documented result is undefined behaviour.
- `flush()` is asynchronous for XML. A write followed immediately by a process kill can be
  lost; GSKV flushes in real time.

## RelationalStore

SQLite underneath, with a documented connection model that matters:

- **Four read connections and one write connection.** Read connections expand dynamically;
  the write connection does not. When the write connection is busy, writes queue.
- Only one write operation at a time, by design.
- Default journal mode is WAL; default flush mode is FULL.
- ArkTS column types: `number`, `string`, binary, `boolean`.
- **A record larger than 2 MB inserts successfully and cannot be read back.** There is no
  error at write time. Store large payloads as files and keep the path in the row.
- Database files are deleted automatically when the app is uninstalled.

Resource ownership is the main source of production bugs here. Every `ResultSet` must be
closed on **every** path — success, early return, and exception. A leaked `ResultSet` holds
a read connection; five of them and every subsequent query blocks. Wrap iteration so that
`close()` is unconditional.

Transactions: wrap a batch in one transaction rather than issuing N autocommitted
statements — both for atomicity and because each commit is a flush. For a bulk import, run
it off the UI thread as a single TaskPool task (see `references/concurrency.md`).

Predicates are built with `RdbPredicates`; prefer them over hand-built SQL strings, and
never interpolate user input into `executeSql`.

## PersistenceV2

The V2 counterpart to `AppStorage`/`PersistStorage`: it connects an `@ObservedV2` class to
disk.

```ts
@ObservedV2
class Settings {
  @Trace theme: string = 'system';
  @Type(Array) @Trace recents: string[] = [];
}

const settings = PersistenceV2.connect(Settings, () => new Settings())!;
```

- Only `@Trace`-marked properties are persisted; anything else is dropped on reload.
- `@Type` pins the declared type of a property so deserialization can reconstruct it.
  Without it, a class-typed or array-typed property can come back wrong.
- The persisted value is written when a traced property changes; a manual `PersistenceV2.save(key)`
  exists for cases where you need a checkpoint.
- Register an error callback (`PersistenceV2.notifyOnError`) — a serialization failure is
  otherwise silent, and the symptom is settings that reset at random.
- Treat it as UI state, not as a database. It is neither queryable nor encrypted.

For V1 code the equivalents are `AppStorage` + `PersistentStorage` with `@StorageLink` /
`@StorageProp` — and see `references/arkui-state-v1-interop.md` for why binding those
decorators to a V2 model object does not work.

## Files

Get every path from a `Context`: `filesDir`, `cacheDir`, `preferencesDir`, `databaseDir`,
`tempDir`, `distributedFilesDir`. Never hardcode a sandbox path — it differs by context, by
module, and by encryption area (`EL1`–`EL5`), and a path captured from one context and used
from another points somewhere else.

`cacheDir` can be cleared by the system at any time. Anything the app cannot regenerate
belongs in `filesDir`.

File I/O is `@ohos.file.fs` (`fileIo`). Every `open` needs a matching `close` on all paths;
prefer the stream APIs for large files so you are not holding the whole payload in memory.
For user-visible media, go through the picker and `photoAccessHelper` rather than reaching
into shared storage directly — the permission model expects it.

## Encryption and secrets

Nothing in this reference encrypts anything. Keys, tokens and credentials belong in the
platform key store; if a design puts a long-lived token in `Preferences` or a row in RDB,
that is a finding, not a trade-off. When ciphertext must live in one of these stores,
encrypt with a key held by the key store and persist only the ciphertext.

## Migration and schema change

- RDB migration goes through the store's version: compare `store.version`, run the upgrade
  statements, set the new version, all inside one transaction. A partially applied upgrade
  leaves a database that no code path expects.
- Test the upgrade from the **oldest version still installed on devices**, not from the
  previous one. `compatibleSdkVersion` tells you how far back that is.
- Downgrades do not happen in the store but do happen in the field, because a user can
  install an older build from a shared package. Decide explicitly whether to detect and
  reset, or to keep the schema additive.
- For `Preferences` and `PersistenceV2` there is no migration mechanism: renaming a key or
  changing a property type loses the old value. Read the old key, write the new one, and
  delete the old one in one release; drop the compatibility code a release later.

## Failure table

| Pattern | Consequence |
|---|---|
| `ResultSet` not closed on an error path | a read connection leaks; queries eventually block |
| RDB record > 2 MB | inserts fine, cannot be read back, no error |
| N autocommitted inserts instead of one transaction | N flushes; slow and non-atomic |
| Token or credential in `Preferences` | plaintext in the sandbox |
| Preferences key > 1024 bytes or value > 16 MB | rejected |
| ArkTS and C APIs on one Preferences instance with different formats | each side reads different data |
| Re-`getPreferences()` after `deletePreferences()` without re-subscribing | observers never fire again |
| `deletePreferences()` concurrent with another Preferences call | undefined behaviour |
| Property without `@Trace` in a `PersistenceV2` class | not persisted, resets on reload |
| Class/array property without `@Type` | deserialized incorrectly |
| No `PersistenceV2.notifyOnError` handler | silent loss of persisted state |
| Hardcoded sandbox path | reads/writes the wrong location under another context |
| Irreplaceable data in `cacheDir` | cleared by the system |
| Schema upgrade tested only from the previous version | crash on devices upgrading from older builds |

<!-- sources: openharmony-docs, corey-harmonyos, dengshiying-harmonyos, huawei-docs -->
