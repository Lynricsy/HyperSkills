# Deferred work has several owners

Verified against: C++20 coroutine mechanisms, working-draft
[dcl.fct.def.coroutine]. Coroutine semantic claims are [official]; callback
boundary design is an independent rewrite of selected [community] guidance.

## Separate the four lifetimes

| Object | What preserving it does not preserve |
|---|---|
| Queue entry or callback wrapper | Pointees of raw pointers, reference captures, `this`, or views |
| Lambda closure | Referents of its borrowed captures |
| Coroutine frame | The closure of an implicit-object coroutine lambda, or objects passed by reference |
| `coroutine_handle` value | Ownership: copying a handle neither retains nor duplicates the frame |

Before submitting work, decide if the operation owns a snapshot or holds a live
owner. Capture an owning value for a snapshot. For a live object, retain ownership
under the existing concurrency model, or use a weak reference when “owner gone,
skip work” is the specified cancellation behavior. Do not silently change a
must-deliver callback into a weak-reference no-op.

A callback capturing a `shared_ptr` may keep its object alive yet create a cycle
when the object owns the queue or callback. Locate the edge broken on unsubscribe,
completion, or shutdown. A token's destruction is not proof of cancellation unless
the API guarantees queued and already-running callbacks can no longer access state.

## Move ownership into coroutine parameters before initial suspension

A C++20 coroutine copies its parameters into coroutine state before constructing
the promise and reaching `initial_suspend`. A by-reference parameter still refers
to the caller's object; copying that reference is not ownership transfer.

A capturing coroutine lambda commonly accesses captures through its closure's
implicit object parameter. Invoking a temporary closure and retaining only the
returned task leaves the frame referring to a destroyed closure. A captured
`shared_ptr` does not help once the closure holding that pointer is destroyed.
Moving a capture into a local at the top of the body can also be too late: lazy
`initial_suspend` occurs before the body executes.

Use a named coroutine with owning by-value parameters. This is a C++20 integration
excerpt using the project's existing `Task` and `Report`, not a standalone task
implementation:

```cpp
Task render_report(std::shared_ptr<Report> report) {
    co_await report->wait_until_ready();
    report->render();
}

// The owning parameter enters coroutine state before lazy initial suspension.
auto task = render_report(std::move(report));
queue.submit(std::move(task));
```

The project must guarantee that the awaitable, task, and executor support the
cancellation protocol below. A by-value `string_view` parameter would still be a
borrow; changing the parameter syntax alone cannot repair that contract.
A captureless ordinary lambda may call this named coroutine when an adapter is
needed. Avoid keeping a capturing coroutine closure alive by accident in a caller.

## Assign frame destruction, not just frame storage

Use the project's established task abstraction. When inspecting its owning handle
wrapper, verify that copying is forbidden or backed by a real ownership protocol,
moving empties the source, move assignment disposes of the prior destination safely,
and destruction occurs exactly once. Do not publish a handwritten generator whose
implicit copy constructor causes two destructors to destroy one frame.

Separate these transitions:

- **Queued, never resumed:** discarding the task destroys the suspended frame and
  its parameter owners even though body-local cleanup never ran.
- **Suspended on an external operation:** detach or cancel that operation so it
  cannot resume a destroyed frame; destroying the handle first is unsafe.
- **Running:** synchronize with the executor; `destroy()` is not a cross-thread
  cancellation interrupt and requires a suspended coroutine.
- **Completed:** if `final_suspend` suspends, the frame still needs its owner's
  destruction. If the coroutine self-destroys, retained handles must not be used.
- **Transferred:** only the new owner may destroy; stale handles cannot resume,
  query `done()`, or destroy after the frame has gone away.

Do not resume a completed coroutine, or concurrently resume and destroy it.
A stop token is cooperative notification; it does not revoke callbacks already
scheduled by an awaiter. Also check exceptions: promise `unhandled_exception`
and result retrieval must follow the task's error contract rather than dropping
an exception in an unobserved detached operation.

## Exercise the boundary without erasing it

Queue the work, release the submitting scope, mutate the original input when a
snapshot is promised, then drain. Observe the promised value and exactly-once
completion. Separately cancel before first resume and while suspended, using the
executor's cancellation contract. Observe resource release and no later callback.
Use weak observers or counted resource lifetimes for semantic checks; ASan adds
coverage but cannot replace the ownership assertions. Do not “fix” a lazy task by
running it immediately or remove cancellation assertions to obtain a green run.

<!-- sources: margelo-cpp, cpp-draft, ecc-cpp-testing -->
