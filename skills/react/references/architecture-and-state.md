# Architecture and state

Where files go, where state lives, and how a feature is split. Read this when
starting a component or a feature, or when deciding where a piece of state
belongs.

Verified against: React 19.3.

## Contents

- File layout
- Composition over configuration
- Container and presentation
- Choosing where state lives
- Prop drilling limit
- Loading, empty and error states
- Optimistic updates
- Form state with Actions (React 19+)

---

## File layout

Colocate everything a component owns; a reader should not have to search three
trees to change one component.

```
src/components/TaskList/
  TaskList.tsx          # implementation
  TaskList.test.tsx     # tests
  use-task-list.ts      # hook, when the state is non-trivial
  types.ts              # component-specific types
```

Follow the project's existing convention when it has one — a consistent wrong
layout costs less than two competing right ones. In an App Router project,
route-private components go in `app/<segment>/_components/`, where the leading
underscore keeps the folder out of routing.

---

## Composition over configuration

```tsx
// Good — the caller composes what it needs
<Card>
  <CardHeader><CardTitle>Tasks</CardTitle></CardHeader>
  <CardContent><TaskList tasks={tasks} /></CardContent>
</Card>

// Avoid — every new need adds a prop
<Card title="Tasks" headerVariant="large" bodyPadding="md" content={<TaskList tasks={tasks} />} />
```

When a component starts collecting `show*` and `is*` props, stop adding props
and split it. The full refactor chain is in `composition-patterns.md`.

A component past roughly 200 lines is usually two components; check whether the
top half only prepares data for the bottom half.

---

## Container and presentation

Separate the component that gets data from the component that renders it. The
presentation half then renders from props alone, which makes it trivially
testable and reusable.

```tsx
// Container — owns data and the three non-happy states
export function TaskListContainer() {
  const { tasks, isLoading, error, refetch } = useTasks()

  if (isLoading) return <TaskListSkeleton />
  if (error) return <ErrorState message="Failed to load tasks" retry={refetch} />
  if (tasks.length === 0) return <EmptyState message="No tasks yet" />

  return <TaskList tasks={tasks} />
}

// Presentation — props in, markup out
export function TaskList({ tasks }: { tasks: Task[] }) {
  return (
    <ul role="list">
      {tasks.map((task) => <TaskItem key={task.id} task={task} />)}
    </ul>
  )
}
```

In an App Router project the container is usually a Server Component that awaits
the data, and the presentation component is the one that may carry
`'use client'`.

---

## Choosing where state lives

Take the first row that works. Every row down adds either a subscription or a
place for the value to go stale.

| Location | Use for |
|---|---|
| Local `useState` | state one component owns |
| Lifted to the closest common parent | two or three siblings share it |
| URL search params | filters, pagination, tabs — anything a user should be able to share or reload into |
| Server cache (SWR / React Query) | remote data, with caching and revalidation |
| Context | theme, auth, locale — read often, written rarely |
| Global store (Zustand, Redux) | complex client state genuinely needed app-wide |

Two rules that follow from the table:

- Remote data is not client state. Storing a fetch result in `useState` gives
  up deduplication, revalidation and request cancellation.
- Anything a user would expect to survive a reload or a shared link belongs in
  the URL, not in a store.

Context has one trap worth knowing: every consumer re-renders when the value
changes, so a context holding a frequently-changing value behaves like a global
re-render trigger. Split it — one context per change frequency — or move the
volatile part into a store with selectors.

---

## Prop drilling limit

Do not pass a prop through more than about three components that do not use it.
Past that, either restructure the tree (pass the rendered element as `children`
instead of the data it needs) or introduce a context. Restructuring is usually
the better fix, because it removes the intermediate knowledge entirely.

---

## Loading, empty and error states

A component that handles only the success path is unfinished. Requirements:

- Loading: a skeleton that matches the real layout, not a centred spinner —
  a spinner throws away the layout information you already have and causes a
  jump when content arrives. Mark it with `aria-busy`.
- Empty: say what is missing and offer the action that fixes it.
- Error: say what failed, in the user's terms, and offer a retry.

```tsx
function TaskListSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading tasks">
      {Array.from({ length: 3 }, (_, i) => (
        <div key={i} className="h-12 animate-pulse rounded bg-muted" />
      ))}
    </div>
  )
}
```

---

## Optimistic updates

For an action whose outcome is near-certain, render the result immediately and
roll back on failure. In React 19 `useOptimistic(value, reducer?)` does this
inside a transition, with the rollback handled for you:

```tsx
'use client'

function TaskItem({ task, toggleTask }: { task: Task; toggleTask: (id: string) => Promise<void> }) {
  const [optimisticTask, setOptimisticTask] = useOptimistic(task)

  return (
    <button
      onClick={async () => {
        setOptimisticTask({ ...task, done: !task.done })
        await toggleTask(task.id)
      }}
    >
      {optimisticTask.done ? 'Done' : 'Open'}
    </button>
  )
}
```

The optimistic value reverts automatically when the surrounding action settles
or throws — you do not write the rollback. With a server-cache library, use its
own optimistic API (cancel in-flight queries, snapshot, write, restore on
error) rather than combining the two.

---

## Form state with Actions (React 19+)

A form that submits to a Server Action needs no `isLoading` state and no
`onSubmit` handler.

`useActionState` holds the action's return value and its pending flag:

```tsx
'use client'

import { useActionState } from 'react'
import { createTask } from './actions'

const [state, formAction, isPending] = useActionState(createTask, { error: null })

return (
  <form action={formAction}>
    <input name="title" required />
    <button disabled={isPending}>Create</button>
    {state.error ? <p role="alert">{state.error}</p> : null}
  </form>
)
```

The action receives the previous state as its first argument and the form data
as its second: `async function createTask(prev, formData)`. Return the next
state; do not throw for expected validation failures, because a thrown error
reaches the error boundary instead of the form.

`useFormStatus` reads the enclosing form's submission status **from a child
component** — calling it in the component that renders the `<form>` returns
`pending: false` forever, which is the single most common mistake with it:

```tsx
function SubmitButton() {
  const { pending } = useFormStatus()
  return <button disabled={pending}>Save</button>
}

// <form action={save}><SubmitButton /></form>
```

Use `useActionState` when you need the action's result, `useFormStatus` when a
nested control only needs the pending flag, and `useOptimistic` when the UI
should show the result before the action returns.

<!-- sources: addy-frontend-ui, react-docs, vercel-react-bp -->
