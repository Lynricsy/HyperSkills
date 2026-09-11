# Data updates

Verified against: base library 3.x, `glass-easel` 1.2.0, `miniprogram-api-typings` 5.2.3.

## Contents

- [The cost model, in the platform's order](#the-cost-model-in-the-platforms-order)
- [The two update algorithms](#the-two-update-algorithms)
- [What this means for batching](#what-this-means-for-batching)
- [setData semantics and hard limits](#setdata-semantics-and-hard-limits)
- [Advanced update APIs (glass-easel)](#advanced-update-apis-glass-easel)
- [groupSetData: hiding an intermediate frame](#groupsetdata-hiding-an-intermediate-frame)
- [What belongs in data, and what does not](#what-belongs-in-data-and-what-does-not)
- [Observers](#observers)
- [Deep-copy options](#deep-copy-options)
- [Recursive updates](#recursive-updates)
- [Measuring instead of guessing](#measuring-instead-of-guessing)
- [Checklist for a stuttering page](#checklist-for-a-stuttering-page)

## The cost model, in the platform's order

The platform documents two factors and their order:

1. the total node count of the Shadow tree belonging to **the component that calls the
   update**;
2. the amount of data changed.

and states that the first matters more than the second. Almost all folklore about
`setData` inverts this, because the bridge-serialisation story is easy to tell. The
practical difference is large: on a page holding one 7000-node tree, hand-writing a
payload diff changes the second-order term while every update still walks 7000 nodes.
Moving the rows into a `<feed-row>` component that calls `setData` on itself cuts the
walked tree to one row.

So the fix order for a slow page is:

1. **Split components** so that the tree an update walks is small.
2. **Remove render-irrelevant fields** from `data` so no update happens at all.
3. **Send less** per update, and prefer path updates over whole-object rewrites.

Step 3 first is the common mistake.

## The two update algorithms

| Algorithm | How it works | When chosen |
|---|---|---|
| Virtual-tree update | Depth-first traversal of the whole Shadow tree to find bindings to refresh | Default; always under exparser |
| Binding-map update | Uses compile-time information to jump straight to the affected binding expressions; no traversal | glass-easel only, and only when the conditions below hold |

The binding-map path is selected only when **both** hold:

- exactly **one** data field is updated in this call; and
- that field is **not** used by a `wx:if`, `wx:for` or `let:` node, nor by any
  descendant of one.

Otherwise the framework falls back to the virtual-tree walk.

Two direct consequences:

- Anything driving a `wx:for` list can never take the fast path. Long-list cost is a
  structural problem, not a payload problem.
- Updating a child component's property recursively triggers that child's own update,
  and the framework re-picks an algorithm for the child's tree. Small, shallow component
  trees therefore compose well; one enormous page tree does not.

For `Object` and `Array` properties the framework cannot reliably tell whether the value
changed. Declare a property `comparer` so an unchanged object does not start a subtree
update:

```javascript
Component({
  properties: {
    config: {
      type: Object,
      // return true == changed == update; false == no update
      comparer(newVal, oldVal) { return newVal.revision !== oldVal.revision },
    },
  },
})
```

## What this means for batching

"Merge your `setData` calls" is only half a rule. Merging N field updates into one call
replaces N targeted binding-map updates with one virtual-tree walk.

Decide by what the fields drive:

- Fields that feed `wx:if` / `wx:for` / `let:`, or more than one field changing anyway —
  batch them. There is no fast path to lose, and batching saves render passes.
- Two independent plain interpolation bindings (`{{ title }}`, `{{ count }}`) — leaving
  them as two single-field calls keeps both on the fast path.
- An intermediate visual state must not be shown — use `groupSetData`, which is about
  frames, not about algorithms.

## setData semantics and hard limits

```javascript
this.setData(
  { 'list[2].liked': true, 'obj.a.b': 1 },   // data paths need no pre-declaration
  () => { /* runs after the data is fully applied to the renderer */ },
)
```

- The value must be JSON-serialisable.
- **One call carries at most 1024 kB.**
- A key whose value is `undefined` is skipped. `cursor: res.cursor ?? undefined` is a
  silent no-op that leaves the previous cursor in place — use `null` for "cleared".
- Mutating `this.data` directly does not update the view and desynchronises the two
  copies; always go through an update API.
- The callback fires late, after the data has reached the renderer. It is the right tool
  for "measure the node after it exists" and the wrong tool for sequencing business
  logic.
- Under glass-easel, the template update itself is **synchronous**: once `setData`
  returns you may query the component tree and node geometry. Inside a data observer it
  behaves like `updateData` and is applied after the observer finishes.

## Advanced update APIs (glass-easel)

```javascript
// address a field by array path; nothing is applied yet
this.replaceDataOnPath(['obj', 'foo', 0], 3)

// splice an array in place: at index 1, delete 2, insert 3
this.spliceArrayDataOnPath(['obj', 'foo'], 1, 2, [5, 6, 7])

// flush everything accumulated so far
this.applyDataUpdates()
```

`groupUpdates` removes the chance of forgetting the flush, and merges the calls into a
single render:

```javascript
this.groupUpdates(() => {
  this.updateData({ a: 3 })
  this.updateData({ b: 4 })
})
```

`updateData` has `setData`'s shape but does not apply; it must be flushed by
`applyDataUpdates` or by returning from `groupUpdates`. Inside observers, prefer
`updateData` — `setData` there already behaves that way, and the explicit name says so.

List mutations map onto `spliceArrayDataOnPath` far better than onto array rebuilds:

```javascript
// append a page of results (index undefined == append)
this.spliceArrayDataOnPath(['list'], undefined, 0, newItems)
this.applyDataUpdates()

// drop the head and append the tail, as one render
this.groupUpdates(() => {
  this.spliceArrayDataOnPath(['comments'], 0, 1, [])
  this.spliceArrayDataOnPath(['comments'], undefined, 0, [newComment])
})
```

`this.setData({ list })` after `list.push(...)` rewrites the whole array, and the
framework then re-diffs every row.

## groupSetData: hiding an intermediate frame

Some pairs of updates genuinely cannot be merged — updating a `<scroll-view>`'s item
list and then its scroll position must be two separate `setData` calls, because the
second depends on the nodes the first created. `groupSetData` keeps the state between
them off screen:

```javascript
this.groupSetData(() => {
  this.setData({ list })
  this.setData({ scrollPosition })
})
```

## What belongs in data, and what does not

| Kind of state | Home |
|---|---|
| Read by a WXML binding | `data` |
| Render-indirect, watched by `observers` | pure data field (`options.pureDataPattern`, 2.8.2+) |
| Never rendered: caches, ids, buffers, timers | plain instance field, `this.userData = …` |
| Shared across pages | `App({ globalData })`, or a module |

```javascript
Component({
  options: { pureDataPattern: /^_/ },   // any data key starting with _ never renders
  data: { _rawRows: [], visibleRows: [] },
  observers: { '_rawRows': function (rows) { this.setData({ visibleRows: project(rows) }) } },
})
```

Two traps around instance fields:

- Non-function fields declared in the `Page`/`Component` constructor object are
  **deep-copied once per instance**. A 400 KB table declared there is copied at page
  creation. Assign it inside `onLoad`/`created` instead, where you control whether it is
  copied at all.
- Do not use `data` as a message bus between methods. Every write is a render trigger.

## Observers

- `observers` fire when a field is **set**, whether or not the value changed. Property
  `observer` functions fire only after the comparer decides the value changed.
- Watch source fields and write derived fields; writing the watched field from inside its
  own observer loops.
- Path and wildcard forms: `'obj.a, arr[2]'`, `'obj.**'`, `'**'`.
- Data written inside an observer is merged into the same render pass, which is why
  observers are a cheaper place to derive state than a second `setData` from the caller.

## Deep-copy options

glass-easel copies data before applying it so that mutating `this.data` cannot corrupt
the template, and copies properties when a parent passes them down. Both are tunable:

| Option | Values | Cost of the fast setting |
|---|---|---|
| `dataDeepCopy` | `Simple` (default), `SimpleWithRecursion`, `None` | With `None` you must never write `this.data.x = …` |
| `propertyPassingDeepCopy` | same | With `None` the child must not mutate objects it receives |
| `propertyEarlyInit` | `true`/`false` | `true` saves one initial render but can run observers before `created` |

These are the right lever for a component that updates many times per second and owns
large objects; they are the wrong lever for a page that is slow once.

## Recursive updates

Applying data to the template is synchronous and descends into child components
mid-flight. If a child, during that descent, causes the parent to update again, the
parent is running two updates at once and the template can end up inconsistent. The
common shape is: parent sets a child property → child's observer fires → observer
triggers an event → parent calls `setData` synchronously in the handler.

Break the cycle by deferring the event out of the update: `wx.nextTick(() =>
this.triggerEvent('change', detail))`.

## Measuring instead of guessing

```javascript
this.setUpdatePerformanceListener({ withDataPaths: true }, (res) => {
  console.log(res)   // per-update statistics for this component
})
```

Attach it to the component you suspect, reproduce the interaction, and compare before
and after a change. "Split the component and it should be faster" is not a result.

## Checklist for a stuttering page

- [ ] Which component calls the update, and how many nodes does its tree hold?
- [ ] How many fields does each call touch, and do any of them feed `wx:if`/`wx:for`?
- [ ] Does every field in `data` have a binding that reads it?
- [ ] Is anything large declared in the constructor object rather than assigned in
      `onLoad`?
- [ ] Is `onPageScroll` declared at all? Is any update running from a scroll callback?
- [ ] Does a hidden page keep updating after `onHide`?
- [ ] Are `Object`/`Array` properties passed to children guarded by a `comparer`?
- [ ] Are list mutations expressed as splices rather than array rebuilds?

<!-- sources: wx-official-docs, wx-glass-easel, wx-api-typings -->
