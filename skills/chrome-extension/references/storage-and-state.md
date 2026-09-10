# Storage and state

Verified against: Chrome 148 documentation on developer.chrome.com.

## Contents

- [Picking an area](#picking-an-area)
- [Exposure to content scripts](#exposure-to-content-scripts)
- [Reacting to changes](#reacting-to-changes)
- [Schema versioning](#schema-versioning)
- [Quota errors and write patterns](#quota-errors-and-write-patterns)
- [When storage is the wrong tool](#when-storage-is-the-wrong-tool)

## Picking an area

| Area | Limit | Cleared when | Use for |
|---|---|---|---|
| `session` | 10 MB | Extension disabled, reloaded, updated, or browser restart | Hot state that must survive a worker restart but not a session: capture state machines, auth nonces, in-flight cursors |
| `local` | 10 MB, more with `unlimitedStorage` | Extension removed | Everything the user would be upset to lose: history, cached data, per-device settings |
| `sync` | ~100 KB total, 8 KB per item | Extension removed | User preferences that should follow them to another machine |
| `managed` | read-only | — | Enterprise policy defaults |

`sync` is a preferences bucket, not a database. Exceeding 8 KB on one item fails that
write, and there are also per-hour write-rate limits, so do not stream state into it. If
sync is disabled by the user, it behaves like `local`.

`session` lives in memory. That is exactly what makes it right for the worker: it survives
the 30-second termination but nothing longer, so stale state cannot leak into the next
browser session.

Sensitive values (tokens, page content in flight) belong in `session` rather than `local`
for the same reason: they disappear on their own.

## Exposure to content scripts

`local`, `sync` and `managed` are readable from content scripts by default. **`session`
is not.** A content script calling `chrome.storage.session.get()` gets an error or empty
result, which reads like a bug in your code.

Two fixes, and the choice matters:

```js
// From the service worker, once, at the top level:
chrome.storage.session.setAccessLevel({ accessLevel: 'TRUSTED_AND_UNTRUSTED_CONTEXTS' });
```

That opens the area to content scripts — which run on web pages, so treat everything in it
as reachable by a compromised page. If the value is sensitive, do not open the area;
message the worker for it instead, so the worker decides what to hand over.

The same `setAccessLevel()` call exists on the other areas and can be used in the other
direction: closing `local` to content scripts when only extension pages should read it.

## Reacting to changes

`chrome.storage.onChanged` fires in every context at once, which makes it the cheapest
way to keep a popup, a side panel and a content script consistent without any messaging.

```js
chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== 'local' || !changes.settings) return;
  applySettings(changes.settings.newValue);
});
```

Always branch on the area and on the specific keys. A listener that re-renders on every
change re-renders on every unrelated write, and a listener that writes back to storage
from inside `onChanged` is an infinite loop.

## Schema versioning

Stored shapes outlive the code that wrote them: a user who skipped four releases still has
the old shape. Keep a version number alongside the data and migrate forward from
`runtime.onInstalled` when `reason === 'update'`.

```js
const CURRENT = 3;
const MIGRATIONS = {
  2: (v1) => ({ hosts: v1.hosts.map((h) => ({ host: h, mutedUntil: 0 })) }),
  3: (v2) => ({ ...v2, hosts: v2.hosts.map((h) => ({ ...h, id: crypto.randomUUID() })) }),
};

async function migrate() {
  const { schemaVersion = 1, data } = await chrome.storage.local.get(['schemaVersion', 'data']);
  let next = data;
  for (let v = schemaVersion + 1; v <= CURRENT; v++) next = MIGRATIONS[v](next);
  await chrome.storage.local.set({ data: next, schemaVersion: CURRENT });
}
```

Write one step per version and run them in order rather than one big "fix whatever shape
this is" function — a chain is testable per step and stays correct for a user who jumps
several versions. Never delete the old key before the new write succeeds.

In a WXT project, `storage.defineItem` takes `version` and `migrations` and does this for
you; see `wxt-and-tooling.md`.

## Quota errors and write patterns

Writes reject rather than truncate. Handle `QUOTA_BYTES` and `QUOTA_BYTES_PER_ITEM`
explicitly and decide what to shed — usually the oldest cache entries — instead of letting
the rejection surface as a broken feature.

Batch: one `set({ a, b, c })` is one write and one `onChanged` event; three separate calls
are three of each, and three chances for a concurrent handler to interleave. Read the keys
you need, not the whole area — `get(null)` deserialises everything.

Do not keep large binary data here. Blobs, captured media and multi-megabyte caches belong
in IndexedDB or `CacheStorage`, both of which are available in the worker.

## When storage is the wrong tool

- Frequently changing UI state that only one surface cares about: keep it local to that
  surface, it is not shared state.
- A value derived from something already stored: derive it on read. Two stored copies
  drift.
- Cross-context signalling with no persistent value: use a message or a port. Writing a
  key just to trigger `onChanged` in another context leaves dead keys behind.

<!-- sources: chrome-docs, samber-cc-skills, dot-skills, wxt-docs -->
