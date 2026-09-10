# Form actions, progressive enhancement, and remote functions

Verified against: SvelteKit 2.70.

## Contents

- [Anatomy of a form action](#anatomy-of-a-form-action)
- [`fail` versus `error` versus `redirect`](#fail-versus-error-versus-redirect)
- [Cookies in an action](#cookies-in-an-action)
- [Progressive enhancement with `use:enhance`](#progressive-enhancement-with-useenhance)
- [Customising the submit callback](#customising-the-submit-callback)
- [Hand-rolled submission](#hand-rolled-submission)
- [Remote functions (experimental)](#remote-functions-experimental)
- [Choosing between actions and remote functions](#choosing-between-actions-and-remote-functions)

## Anatomy of a form action

Actions live only in `+page.server.js`. A single `default` action, or named
actions addressed as `?/name`:

```js
// +page.server.js
import { fail, redirect } from '@sveltejs/kit';

/** @satisfies {import('./$types').Actions} */
export const actions = {
  login: async ({ request, cookies, url }) => {
    const data = await request.formData();
    const email = String(data.get('email') ?? '');

    if (!email) return fail(400, { email, missing: true });

    cookies.set('session', await issueSession(email), { path: '/', httpOnly: true });
    redirect(303, url.searchParams.get('next') ?? '/dashboard');
  },

  logout: async ({ cookies }) => {
    cookies.delete('session', { path: '/' });
    redirect(303, '/');
  }
};
```

```svelte
<script lang="ts">
  import { enhance } from '$app/forms';
  import type { PageProps } from './$types';
  let { data, form }: PageProps = $props();
</script>

<form method="POST" action="?/login" use:enhance>
  <input name="email" type="email" value={form?.email ?? ''} />
  {#if form?.missing}<p class="error">Email is required</p>{/if}
  <button>Sign in</button>
</form>
```

A default action cannot coexist with named actions in the same file. A named
action is invoked with `action="?/login"` on the form or `formaction="?/login"`
on a button, which is how one form drives several actions.

Constraints that produce silent failures:

- The form must be `method="POST"`. A `GET` form navigates and runs `load`; it
  never reaches an action.
- The action must live in `+page.server.js`. Pointing a form at a `+server.js`
  endpoint and adding `use:enhance` is an error, not a fallback.
- `enhance` is an import from `$app/forms`, not a global. A missing import
  leaves `use:enhance` as a no-op directive.
- After an action, the page's `load` functions re-run and the return value
  arrives as the `form` prop. `form` is `undefined` on a fresh page load.

## `fail` versus `error` versus `redirect`

| Situation | Call | Result |
|---|---|---|
| Invalid user input | `return fail(400, { ...submitted, reason })` | page re-renders, data on the `form` prop |
| Genuinely cannot serve the page | `error(500, 'message')` | nearest `+error.svelte` renders |
| Done, move on | `redirect(303, '/next')` | browser follows with `GET` |

Sending validation failures through `error()` is the most common form bug: the
user loses everything they typed and gets an error page instead of a message
next to the field. `fail`'s payload must be devalue-serializable and should echo
back the submitted values (never the password) so the inputs can be repopulated.

In SvelteKit 2, `error()` and `redirect()` throw by themselves — writing
`throw redirect(...)` is SvelteKit 1 syntax. It still happens to work, but it
misleads the next reader about the control flow and `svelte-migrate` removes it.
Never call either inside a `try` block; if unavoidable, distinguish them from
real errors with `isHttpError` / `isRedirect`.

Use `303` after a `POST` so the browser follows with `GET`. `302` re-issues the
`POST` in some clients and will double-submit.

## Cookies in an action

`cookies.set`, `cookies.delete` and `cookies.serialize` require an explicit
`path` in SvelteKit 2 — usually `path: '/'`. Without it SvelteKit throws, and
the reason the option is mandatory is that the browser default (the parent of
the current path) is almost never what was intended. `httpOnly` and `sameSite`
default to safe values; `secure` defaults to true except on `localhost`, so
hard-coding `secure: true` breaks local development over plain HTTP.

Set the cookie *before* redirecting; the redirect response carries it.

## Progressive enhancement with `use:enhance`

Bare `use:enhance` reproduces what the browser would do, minus the full reload:
it updates `form`, `page.form` and `page.status`, resets the `<form>` element,
calls `invalidateAll()` on a successful response, follows a `redirect` result
with `goto`, and renders the nearest `+error` boundary on an `error` result.
Focus is reset in every case. The one asymmetry: `form` and `page.form` are only
updated when the action lives on the page being submitted from — for
`<form action="/somewhere/else">` use `applyAction` instead.

That default is what you want most of the time. Reach for a callback only when
one of those behaviours is wrong for the page.

## Customising the submit callback

`use:enhance={fn}` where `fn` runs before submission and may return a second
callback that receives the `ActionResult`:

```svelte
<script>
  import { enhance } from '$app/forms';
  let saving = $state(false);
</script>

<form
  method="POST"
  use:enhance={() => {
    saving = true;
    return async ({ update }) => {
      await update({ reset: false });   // keep what the user typed
      saving = false;
    };
  }}
>
```

The pre-submit callback receives `{ formElement, formData, action, cancel,
submitter }`; calling `cancel()` aborts the submission. Returning a
callback replaces the default handling entirely, so it must call `update()` or
`applyAction(result)` — otherwise nothing on the page changes and the form looks
dead.

`applyAction(result)` differs from `update()`: it applies `success`/`failure`
data regardless of which page the action lived on, follows a `redirect` with
`goto(location, { invalidateAll: true })`, and renders `+error` for an `error`
result.

## Hand-rolled submission

Sometimes wanted (a non-`<form>` trigger, a custom optimistic flow). Then the
response must be read with `deserialize` from `$app/forms`, not `JSON.parse` —
action results, like `load` results, may contain `Date` and `BigInt`:

```js
import { applyAction, deserialize } from '$app/forms';
import { invalidateAll } from '$app/navigation';

const response = await fetch(form.action, { method: 'POST', body: new FormData(form) });
const result = deserialize(await response.text());
if (result.type === 'success') await invalidateAll();
applyAction(result);
```

A `fetch('?/login')` with a hand-built body and an `res.ok` check is the version
to reject: the action response is a typed envelope, `res.ok` cannot tell
`success` from `failure` from `redirect`, the server's messages are discarded,
and the route stops working without JavaScript.

## Remote functions (experimental)

Available since SvelteKit 2.27 and still experimental: the API may change
without a major release. Opt in through `svelte.config.js`:

```js
export default {
  compilerOptions: { experimental: { async: true } },
  kit: { experimental: { remoteFunctions: true } }
};
```

Functions are exported from a module whose name contains a `remote` segment
(`data.remote.ts`), always run on the server, and are transformed on the client
into typed `fetch` wrappers. Four flavours:

- `query(schema?, fn)` — read dynamic data; deduplicated per argument set;
  `.refresh()` re-fetches. Cannot be used on a fully prerendered page.
- `form(schema, fn)` — a mutation; the returned object spreads onto `<form>`
  and supplies `method`, `action` and a progressive-enhancement attachment, so
  it works without JavaScript. `.as(type)` on a field yields the input
  attributes and wires validation.
- `command(schema?, fn)` — a mutation not tied to a form; callable from an
  event handler. Cannot be called during render.
- `prerender(schema?, fn)` — like `query` but evaluated at build time.

Arguments must be validated with a [Standard Schema](https://standardschema.dev)
(valibot, zod, arktype) whenever the callback reads them; the schema is the
security boundary, because these are public HTTP endpoints.

Single-flight mutations are the reason to use them: a `form` or `command`
handler can call `query.refresh()` on the queries it invalidated and the fresh
data rides back on the mutation's response. Without that, a `form` invalidates
everything and a `command` invalidates nothing.

`getRequestEvent()` from `$app/server` is how a remote function reaches
`cookies`, `locals` and `request` — there is no event parameter.

## Choosing between actions and remote functions

The official position: form actions are feature-complete and will keep working;
new development is focused on remote functions, which are intended to become
the recommended way to talk to the server.

Default to form actions for existing projects and anything that must be stable.
Consider remote functions for a new project that can absorb API churn, and say
so explicitly when recommending them — enabling `experimental.async` changes
effect ordering across the whole app, so it is not a per-route decision.

<!-- sources: sveltekit-core, spences10-svelte, awesome-copilot, svelte-dev-docs -->
