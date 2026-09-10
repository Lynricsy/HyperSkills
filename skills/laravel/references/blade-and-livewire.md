# Blade views and Livewire components

Verified against: Laravel 13, Livewire 4, Volt 1.

## Contents

- [Blade components](#blade-components)
- [Data reaches the view already loaded](#data-reaches-the-view-already-loaded)
- [Escaping](#escaping)
- [Fragments](#fragments)
- [Livewire 4 component formats](#livewire-4-component-formats)
- [Livewire correctness rules](#livewire-correctness-rules)
- [What changed in Livewire 4](#what-changed-in-livewire-4)
- [Volt](#volt)
- [Testing components](#testing-components)
- [Choosing a stack](#choosing-a-stack)

## Blade components

Use a component when a reusable piece of UI benefits from explicit props, slots or an attribute
bag; an include is fine for a small partial that intentionally shares the current view's data —
pass it an explicit array when the implicit sharing would obscure its inputs.

Merge caller attributes so a component stays composable, and note that `class` merges rather than
replaces:

```blade
<div {{ $attributes->merge(['class' => 'alert alert-'.$type]) }}>{{ $message }}</div>
```

`@pushOnce` for a component's own script block — plain `@push` adds it once per render, so a
component in a loop emits the script N times.

`@aware` reads a prop that was explicitly passed to an ancestor component. It does **not** see an
ancestor's default value, which is the usual reason it appears to do nothing.

A view composer centralises data for named views. Keep it compatible with every view it targets
and avoid broad wildcards; it runs only for view rendering, so JSON and streamed responses get
nothing from it.

## Data reaches the view already loaded

No queries in templates. `@foreach (User::all() as $user)` hides the query from the controller,
from tests, and from any eager-loading decision — build the data in the controller, an action or a
view composer, and pass it in. This is the most common source of production N+1s because a
template loop is where the relation access lives.

## Escaping

`{{ }}` escapes for HTML. `{!! !!}` is only for content already sanitised **for the exact context
it renders into** — HTML, URL, JavaScript and CSS each escape differently, so "we sanitised it"
is not an answer by itself. User-supplied text goes through `{{ }}`.

Server data destined for JavaScript goes through `{{ Js::from($data) }}`, which encodes for a
script context; in Laravel 13 it leaves Unicode unescaped by default. A large model serialised
into a `data-` attribute leaks fields and complicates escaping — pass identifiers, not records.

## Fragments

A route can return a named fragment of a view for htmx or Turbo clients rather than a second
endpoint:

```php
return view('dashboard', compact('users'))->fragmentIf($request->hasHeader('HX-Request'), 'user-list');
```

## Livewire 4 component formats

Check the project before generating anything. Existing components define the convention, and
`config/livewire.php` (`make_command.type`, `make_command.emoji`, `component_locations`,
`component_namespaces`) can change both the default format and where files land — including
whether the ⚡ filename prefix is used at all.

| Format | Command | Where it lands |
|---|---|---|
| Single-file (v4 default) | `make:livewire create-post` | `resources/views/components/⚡create-post.blade.php` |
| Full-page | `make:livewire pages::create-post` | `resources/views/pages/⚡create-post.blade.php` |
| Multi-file | `make:livewire create-post --mfc` | a `⚡create-post/` directory with `.php` + `.blade.php` |
| Class-based (v3 style) | `make:livewire create-post --class` | `app/Livewire/CreatePost.php` + `resources/views/livewire/create-post.blade.php` |

`php artisan livewire:convert <name>` moves an existing component between formats.

## Livewire correctness rules

- `wire:key` on every element rendered in a loop. Without it Livewire re-uses DOM nodes across
  re-renders and state lands on the wrong row.
- `wire:model` is deferred. Live updates need `wire:model.live`; expecting the deferred form to
  round-trip on keystroke is the most common "it doesn't update" report.
- A Livewire action is a public HTTP entry point. Validate and authorize inside it exactly as you
  would in a controller — the component's properties come from the browser.
- `wire:loading` for the pending state, so a slow action does not look broken.
- Alpine ships inside Livewire; including it separately breaks both.

## What changed in Livewire 4

Applies when upgrading, or when reading a v3 codebase:

- Full-page components register with `Route::livewire('/posts/create', CreatePost::class)`.
- Config keys renamed: `layout` → `component_layout`, `lazy_placeholder` → `component_placeholder`.
- `wire:model` now ignores child events; `wire:model.deep` restores the old behaviour.
- `wire:scroll` → `wire:navigate:scroll`; `wire:transition` uses the View Transitions API and its
  modifiers are gone.
- Component tags must be explicitly closed.
- JavaScript: `$wire.$js('name', fn)` → `$wire.$js.name = fn`; the `commit` / `request` hooks
  became `interceptMessage()` / `interceptRequest()`.
- New capability worth knowing before hand-rolling equivalents: `@island` for isolated update
  regions, `wire:click.async` / `#[Async]` for non-blocking actions, `defer` and `lazy.bundle`
  loading, and the `wire:sort`, `wire:intersect`, `wire:ref`, `.renderless`, `.preserve-scroll`
  directives.

## Volt

Volt is the functional single-file API for Livewire. Read the existing components first: a project
uses either the functional style (`state()`, `computed()`, `mount()`) or the class-based style
(`new class extends Component`), and mixing them in one codebase is the failure. Generate with
`php artisan make:volt [name] [--test|--pest]` and remember the `@volt` wrapper in a Blade file.

## Testing components

```php
Livewire::test(Counter::class)->assertSet('count', 0)->call('increment')->assertSet('count', 1);
Volt::test('counter')->assertSee('Count: 0')->call('increment')->assertSee('Count: 1');
```

These are feature tests: they exercise the real component through the real request path. Reach for
a browser test only for behaviour that lives in JavaScript and cannot be reached this way, and
only if the project already installs a browser driver.

## Choosing a stack

Livewire and Volt keep state on the server; Inertia keeps it in a JavaScript component. Do not
introduce a second stack into an application that already picked one — the duplicated
authorization, validation and state handling costs far more than the ergonomics gained.

<!-- sources: laravel-boost, laravel-docs -->
