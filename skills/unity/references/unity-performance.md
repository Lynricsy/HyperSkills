# Unity performance: allocation, per-frame cost and the Profiler

Verified against: Unity 6.3 LTS (6000.3); 6.4 (6000.4) differences are marked.

## Contents

- [Measure first](#measure-first)
- [The GC sawtooth](#the-gc-sawtooth)
- [What allocates in a frame](#what-allocates-in-a-frame)
- [Scene lookups and the Find family](#scene-lookups-and-the-find-family)
- [Object pooling](#object-pooling)
- [Logging](#logging)
- [Transforms and vectors](#transforms-and-vectors)
- [Editor numbers are not device numbers](#editor-numbers-are-not-device-numbers)
- [Common false leads](#common-false-leads)

## Measure first

Name the bottleneck before changing code. Three captures answer almost everything:

| Symptom | Capture | What proves the cause |
|---|---|---|
| periodic 1–2 s freezes, sawtooth memory graph | Profiler, CPU module, `GC.Alloc` sorted by call site | a call site allocating on every frame |
| steady high main-thread time, low GPU time | Profiler, CPU module, Hierarchy view by self-time | a script marker dominating, or `Camera.Render` |
| high `Camera.Render`, many SetPass calls | Frame Debugger | per-object state changes — see `unity-rendering.md` |

Deep Profile gives per-method attribution but distorts absolute times; use it to find the
call site, not to quote a number. `ProfilerMarker` / `Profiler.BeginSample` around a
suspect block is cheaper and keeps the numbers honest.

## The GC sawtooth

Unity's default collector (Boehm) is non-generational and non-compacting. Every managed
allocation that survives a frame grows the heap; a collection walks the whole heap and
stalls the main thread. The heap also never shrinks back to the OS in the incremental
configuration, so a spike becomes a permanent footprint. The fix is not "collect more
often" — it is not allocating in a per-frame path.

Incremental GC (Player Settings) spreads a collection over frames and turns one long stall
into many small ones. It reduces the visible hitch; it does not reduce allocation, and it
adds a small constant overhead. Turn it on after removing the allocations, not instead.

## What allocates in a frame

Each of these is a managed allocation **per call** `[official]`:

- string concatenation and `$"..."` interpolation, `ToString()` on a number,
  `string.Format`, `+=` on a string;
- `gameObject.tag` (returns a managed string) — use `CompareTag(...)`, which compares
  natively;
- `Physics.RaycastAll`, `OverlapSphere`, `OverlapBox` and friends (they return a fresh
  array) — use the `NonAlloc` overloads with a preallocated `RaycastHit[]`/`Collider[]`,
  or a single `Physics.Raycast(out RaycastHit)` when you only need the nearest hit;
- `GetComponents<T>()`, `GetComponentsInChildren<T>()` — use the `List<T>` overloads;
- `Object.FindObjectsByType<T>()` (a fresh array) plus the scan itself;
- LINQ (`Where`, `Select`, `OrderBy`, `ToList`) — every operator allocates an enumerator;
- `foreach` over an interface-typed collection (`IList<T>`, `IEnumerable<T>`) boxes the
  enumerator; `foreach` over a concrete `List<T>` or array does not;
- boxing a struct into `object`, or passing one to a `params object[]`;
- `new WaitForSeconds(t)` on each loop iteration — hoist it;
- closures and lambdas that capture locals, when created per frame;
- `Mesh.vertices`, `Mesh.triangles`, `Texture2D.GetPixels` — these copy into a new array
  on every read. Read once, or use the `NativeArray` / `SetVertexBufferData` paths.

The rule of thumb that actually matters: an allocation inside `Update` on a prefab with 400
live instances is 400 allocations per frame, and it is almost always one of the items above
rather than anything exotic.

## Scene lookups and the Find family

`GameObject.Find`, `GameObject.FindWithTag`, `Camera.main` (a tag lookup) and the
`FindObjectsByType` family all traverse structures proportional to the scene. None of them
belong in `Update`. Cache in `Awake`, and let creation push a reference in rather than
polling for it.

The API names have moved twice, and getting the version right matters `[verified]`:

- `Object.FindObjectsOfType` and `Object.FindObjectOfType` are `[Obsolete]` on every
  Unity 6 version. Replacements: `FindObjectsByType<T>()` and `FindAnyObjectByType<T>()`.
- On **Unity 6.3 LTS** the fast form is `FindObjectsByType<T>(FindObjectsSortMode.None)` —
  the sortless overload skips an instance-ID sort.
- From **Unity 6.4** that advice inverts. The `FindObjectsSortMode` enum, *every* overload
  that takes it, and `FindFirstObjectByType` are all `[Obsolete]`, because instance-ID
  ordering is being replaced by `EntityId`. The current form is
  `FindObjectsByType<T>()` / `FindObjectsByType<T>(FindObjectsInactive.Include)` and
  `FindAnyObjectByType<T>()`.

So a file written against the 6.3 guidance grows one warning per call site on a 6.4+
upgrade. When migrating, do not simply delete the sort argument on 6.3 — the sortless
overload there *is* the `FindObjectsSortMode.None` one.

## Object pooling

`UnityEngine.Pool.ObjectPool<T>` and `ListPool<T>`/`DictionaryPool<T>` ship with the
engine; do not hand-roll a pool.

```csharp
private ObjectPool<Projectile> _pool;

private void Awake() => _pool = new ObjectPool<Projectile>(
    createFunc: () => Instantiate(_prefab),
    actionOnGet: p => p.gameObject.SetActive(true),
    actionOnRelease: p => p.gameObject.SetActive(false),
    actionOnDestroy: p => Destroy(p.gameObject),
    collectionCheck: true,          // catches a double Release in development
    defaultCapacity: 32);
```

Pooling rules that are easy to get wrong:

- reset **all** state on `Get`, not on `Release`. A pooled object that kept a stale target
  reference is the classic "enemy attacks nothing" bug.
- a pooled object's `Awake` runs once, at creation. Per-use initialization must be an
  explicit method or `OnEnable`.
- `collectionCheck: true` costs a little and catches double-release; keep it on in
  development builds.
- pooling is for objects created and destroyed many times per second. Pooling a UI panel
  that opens twice a session buys nothing and adds a lifecycle to maintain.

## Logging

`Debug.Log` arguments are evaluated before the call, so `Debug.Log($"hp={hp}")` builds the
string every frame even when logging is filtered out. Development-only logging needs the
call itself removed:

```csharp
[System.Diagnostics.Conditional("UNITY_EDITOR"), System.Diagnostics.Conditional("DEVELOPMENT_BUILD")]
private static void LogVerbose(string message) => Debug.Log(message);
```

`Debug.Log` also captures a stack trace by default; a per-frame log costs far more than the
string. Stack-trace capture per log type is configurable in Player Settings.

## Transforms and vectors

- `transform` is a property that resolves through the native object; cache it in a field
  for hot paths.
- Reading `transform.position` composes the world matrix; reading and writing it several
  times in one method is several conversions. Read once into a local, modify, write once.
- `transform.position += v` is read-modify-write; in a loop over children this is the usual
  source of "why is my `Update` 4 ms".
- Prefer `sqrMagnitude` over `magnitude` and `Vector3.SqrMagnitude` comparisons over
  `Vector3.Distance` when you only compare against a threshold — no square root.
- `Vector3`/`Quaternion` are structs and do not allocate; `new Vector3(...)` in a loop is
  free. Do not "optimize" those away.

## Editor numbers are not device numbers

The Editor runs un-stripped, with the Editor's own loop, extra allocation tracking and the
Scene view rendering. Editor profiling is for *finding* the call site. Any number you quote
must come from a development build attached to the Profiler on the target device. Mobile in
particular changes the answer: thermal throttling, a tile-based GPU where overdraw
dominates, and much smaller memory budgets.

## Common false leads

- **"Reduce draw calls."** In URP the meaningful counter is SetPass calls; see
  `unity-rendering.md`. Merging meshes to cut draw calls can make things worse by defeating
  culling.
- **"Use structs everywhere."** A large struct copied through several calls costs more than
  a reference. The allocation problem is per-frame *garbage*, not reference types.
- **"Cache everything."** Caching a `Transform` in a hot loop is worth it; caching an
  `int` is noise, and a cache that can go stale is a correctness bug traded for nothing.
- **"Turn on Incremental GC / IL2CPP and re-measure."** Both help, neither removes an
  allocation in an `Update`. Fix the call site first so the improvement is attributable.

<!-- sources: gamedev-unity, nicewolf-unity, unity-docs, unity-cs-reference -->
