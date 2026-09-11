# Unity scripting: lifecycle, callbacks and asynchrony

Verified against: Unity 6.3 LTS (6000.3).

## Contents

- [What belongs in which callback](#what-belongs-in-which-callback)
- [Event execution order](#event-execution-order)
- [Order across objects](#order-across-objects)
- [Component access](#component-access)
- [Coroutines](#coroutines)
- [Awaitable](#awaitable)
- [Cancellation](#cancellation)
- [Choosing between coroutines, Awaitable and Task](#choosing-between-coroutines-awaitable-and-task)
- [Communication between components](#communication-between-components)
- [Object lifetime and the fake null](#object-lifetime-and-the-fake-null)
- [Time](#time)

## What belongs in which callback

| Callback | Runs | Put here |
|---|---|---|
| `Awake` | once per instance, on load, even if the component is disabled | self-setup, caching own components, reading own serialized fields |
| `OnEnable` | every time the component is enabled | event subscriptions, re-arming coroutines |
| `Start` | before the first `Update`, after every `Awake` | wiring that depends on *other* objects existing |
| `FixedUpdate` | fixed timestep (0.02 s by default), possibly 0 or several times per frame | Rigidbody forces and velocity writes |
| `Update` | once per frame | input polling, timers, non-physics logic |
| `LateUpdate` | after every `Update` | camera follow, IK cleanup, anything that must see this frame's final transforms |
| `OnDisable` | on disable, and before `OnDestroy` | unsubscribe, stop coroutines, release handles |
| `OnDestroy` | before destruction | final release of native or unmanaged resources |

`Awake` runs on a disabled component; `Start` does not run until the component is first
enabled. A component that is disabled in the scene and enabled later therefore has already
run `Awake` — initialization that assumes "Awake means we are about to run" is wrong.

## Event execution order

```
load
 └─ Awake            (all objects, then)
 └─ OnEnable         (all objects)
 └─ SceneManager.sceneLoaded
 └─ Start            (all objects)

frame
 ├─ FixedUpdate  ─┐
 │  internal physics step, OnTrigger*/OnCollision*
 │  WaitForFixedUpdate resumes
 │  (repeats until physics time catches up with frame time)
 ├─ Update       ─┘
 │  yield null / WaitForSeconds resume
 ├─ internal animation update, OnAnimatorMove, OnAnimatorIK
 ├─ LateUpdate
 ├─ rendering: OnWillRenderObject, OnPreCull, OnPreRender,
 │             OnRenderObject, OnPostRender, OnRenderImage
 ├─ OnGUI (IMGUI, possibly several times per frame)
 └─ WaitForEndOfFrame resumes

teardown
 └─ OnDisable → OnDestroy → OnApplicationQuit
```

Two practical readings of this diagram:

- `FixedUpdate` can run zero times in a fast frame and many times in a slow one. Anything
  that must happen exactly once per frame does not go there; anything that must be
  timestep-stable does not go anywhere else.
- Collision and trigger callbacks are raised inside the physics step, so they are
  interleaved with `FixedUpdate`, not with `Update`.

## Order across objects

Order *within* one object follows the diagram. Order *between* objects is undefined for
every callback. Two ways to fix it, in preference order:

1. Remove the dependency: self-setup in `Awake`, cross-object wiring in `Start`.
2. If a genuine ordering requirement remains, make it explicit with
   `[DefaultExecutionOrder(-100)]` on the class, or the project's Script Execution Order
   list. An undeclared ordering assumption fails intermittently and only on some machines.

## Component access

```csharp
private Rigidbody _rb;

private void Awake() => _rb = GetComponent<Rigidbody>();
```

- Cache in `Awake`. `GetComponent` walks the GameObject's component list on every call.
- `TryGetComponent<T>(out var c)` for the "might not be there" case: it avoids the
  managed allocation that a failed `GetComponent` used to produce and reads better than a
  null check.
- `GetComponents<T>()` allocates an array; `GetComponents<T>(List<T>)` fills a buffer you
  own. Same for `GetComponentsInChildren`.
- `[RequireComponent(typeof(Rigidbody))]` makes the dependency structural: Unity adds the
  component when the script is attached and refuses to remove it. Cheaper than defensive
  null checks.
- `Camera.main` is a tag lookup, not a field. Cache it, and re-acquire only when cameras
  actually change.

## Coroutines

```csharp
private Coroutine _blink;

private void OnEnable() => _blink ??= StartCoroutine(Blink());
private void OnDisable()
{
    if (_blink != null) { StopCoroutine(_blink); _blink = null; }
}

private IEnumerator Blink()
{
    var wait = new WaitForSeconds(0.1f);      // allocate once, reuse every iteration
    while (true) { _label.enabled = !_label.enabled; yield return wait; }
}
```

Facts that decide designs:

- Coroutines run on the main thread. They are cooperative scheduling, not concurrency.
- `enabled = false` does **not** stop a coroutine. Deactivating the GameObject or
  destroying the MonoBehaviour does. `[verified]` So `OnDisable` must stop them explicitly
  if stopping is what you mean.
- `StartCoroutine` inside `Update` starts a new coroutine every frame. Guard it, or hold
  the handle as above.
- Each `yield return new WaitForSeconds(t)` allocates. Hoist the instruction out of the
  loop; `yield return null` allocates nothing.
- `StopCoroutine(string)` and `StopAllCoroutines` are blunt; keep the `Coroutine` handle.
- A coroutine cannot return a value and cannot `try`/`catch` across a `yield`.

Yield instructions: `null` (next frame, after `Update`), `WaitForSeconds`,
`WaitForSecondsRealtime`, `WaitForFixedUpdate`, `WaitForEndOfFrame`, `WaitUntil`,
`WaitWhile`, another `Coroutine`, or an `AsyncOperation`.

## Awaitable

`Awaitable` is Unity's own await-compatible type, designed for Unity's loop rather than the
thread pool. Statics, all with an optional `CancellationToken` `[verified]`:
`Awaitable.NextFrameAsync`, `FixedUpdateAsync`, `EndOfFrameAsync`, `WaitForSecondsAsync`,
`FromAsyncOperation`; plus `Awaitable.MainThreadAsync()` and
`Awaitable.BackgroundThreadAsync()` for thread hops, and `GetAwaiter()` extensions on
`AsyncOperation` and `UnityEvent`.

The constraints are non-obvious and come from the engine's own source `[verified]`:

- **An `Awaitable` may be awaited once.** They are pooled; awaiting the same instance twice
  is undefined behaviour. Never store one in a field and await it from two places.
- It captures neither `ExecutionContext` nor `SynchronizationContext`. Continuations run
  **synchronously** on whichever thread raised completion — so after an `await` of
  something that completes on a background thread you are on that thread, and touching the
  Unity API there throws. `Awaitable.MainThreadAsync()` is the way back.
- `Awaiter.GetResult()` does not block; calling it before completion is undefined
  behaviour. Do not hand-roll awaiter plumbing.

```csharp
private async Awaitable LoadThenShowAsync()
{
    await Awaitable.NextFrameAsync(destroyCancellationToken);
    var data = await ParseOnWorkerAsync();          // may complete off the main thread
    await Awaitable.MainThreadAsync();              // required before touching the API
    _label.text = data.title;
}
```

## Cancellation

`MonoBehaviour.destroyCancellationToken` is cancelled when the component is destroyed —
the right token for almost every async method on a component. One trap: the getter throws
`MissingReferenceException` when it is read for the first time *after* the object has been
destroyed. `[verified]` Touch it once while alive:

```csharp
private CancellationToken _ct;
private void Awake() => _ct = destroyCancellationToken;   // create the source early
```

## Choosing between coroutines, Awaitable and Task

Default to `Awaitable` for new asynchronous code: it returns values, supports
`try`/`catch`/`finally`, takes a `CancellationToken`, and allocates less than an iterator.
Use a coroutine when the logic is a frame-sequenced script (a cutscene, a tween, a
state-machine step) and reads better as one, or when the surrounding code is already
coroutine-based. Reach for `Task`/`ValueTask` only at a boundary that genuinely needs the
TPL — a library API, `HttpClient`, `Task.WhenAll` — and marshal back with
`Awaitable.MainThreadAsync()`. Mixing all three in one system is how projects end up with
two cancellation models and no way to stop anything.

## Communication between components

- **Direct reference** (`[SerializeField] private Health _health;`) — the default. Cheapest
  and traceable in the Inspector.
- **C# `event Action<T>`** — for one-to-many within a scene. Subscribe in `OnEnable`,
  unsubscribe in `OnDisable`. An unsubscribed handler keeps the subscriber alive and fires
  on a destroyed object.
- **`UnityEvent`** — when designers must wire the callback in the Inspector. Slower than a
  C# event and harder to find in code; use it at designer-facing seams only.
- **ScriptableObject event channel** — an asset both sides reference, for cross-scene or
  cross-prefab signals without a singleton. The cost is indirection: nothing in the
  Inspector shows who listens.
- Avoid `SendMessage`/`BroadcastMessage` entirely: string-based, reflective, silent when
  the name is wrong.

## Object lifetime and the fake null

`Destroy(obj)` defers actual destruction to the end of the frame, and a destroyed
`UnityEngine.Object` compares equal to `null` through an overloaded `==` while the managed
wrapper still exists. Two consequences:

- `obj != null` is a *managed-and-native* check on Unity objects and is what you want;
- `obj is not null`, `obj?.Method()` and `ReferenceEquals` bypass the overload and will
  happily call into a destroyed object. Use `!= null` on Unity types, and never the
  null-conditional operator on them.

`DestroyImmediate` exists for Editor code only; calling it at runtime corrupts state.

## Time

- `Time.deltaTime` scales per-frame motion in `Update`; `Time.fixedDeltaTime` is the
  physics step (0.02 s by default).
- `Time.timeScale = 0` freezes `Time.deltaTime`, `FixedUpdate` and `WaitForSeconds`, but
  not `Time.unscaledDeltaTime` or `WaitForSecondsRealtime`. A pause menu animated with
  scaled time never animates.
- `Time.time` is not valid before the first frame and not valid from a constructor.

<!-- sources: gamedev-unity, nicewolf-unity, unity-docs, unity-cs-reference -->
