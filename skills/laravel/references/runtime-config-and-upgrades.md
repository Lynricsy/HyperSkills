# Configuration, caching, runtime and upgrading

Verified against: Laravel 13 (upgrade section covers 12 → 13).

## Contents

- [Application skeleton](#application-skeleton)
- [Configuration and environment](#configuration-and-environment)
- [Caching](#caching)
- [Application structure](#application-structure)
- [Octane and long-lived workers](#octane-and-long-lived-workers)
- [Upgrading 12 to 13](#upgrading-12-to-13)
- [Applying an upgrade safely](#applying-an-upgrade-safely)

## Application skeleton

Since Laravel 11 the skeleton is `bootstrap/app.php`-centred: middleware, exception handling and
routing are configured there with `Application::configure()->withMiddleware(...)
->withExceptions(...)`, service providers are listed in `bootstrap/providers.php`, console
commands in `app/Console/Commands` are auto-registered, and there is no `Http/Kernel.php` or
`Console/Kernel.php`.

An application upgraded from Laravel 10 that still has `app/Http/Kernel.php` is supported and
should stay that way: middleware registration lives in the kernel, exception handling in
`app/Exceptions/Handler.php`, scheduling in `app/Console/Kernel.php`. Restructuring it is a
separate, explicitly requested project — check which layout the project has before writing
registration code.

## Configuration and environment

`env()` is legal in `config/*.php` and nowhere else. Once `php artisan config:cache` runs, the
`.env` file is not loaded, so `env('API_KEY')` in application code returns `null` in exactly the
environment where it matters.

```php
// config/services.php
return ['stripe' => ['key' => env('STRIPE_KEY')]];

// anywhere else
config('services.stripe.key');
```

Environment checks use `app()->isProduction()` / `App::environment('production')`, not
`env('APP_ENV')`.

Never commit a populated `.env`. Laravel can encrypt one (`php artisan env:encrypt
--env=production`), and a hosting platform's own secret store injected at runtime is the other
acceptable option.

Give a repeated domain value a name — an enum case or a class constant — rather than repeating a
string literal. In a localised application, user-facing strings live in language files behind
`__()`.

Run `composer audit` in CI and act on findings.

## Caching

- `Cache::remember($key, $ttl, $callback)` for cache-aside reads. The hand-written
  `if (! Cache::get(...))` version treats a valid `false` or `0` as a miss and recomputes forever.
  `remember()` does not deduplicate concurrent misses; add `Cache::lock()` when duplicate
  computation is expensive.
- `Cache::add($key, $value, $ttl)` is the atomic conditional write; `has()` + `put()` is a race.
- `Cache::flexible($key, [$fresh, $stale], $callback)` serves stale data during the stale window
  and refreshes after the response — same process, not a durable job. Past the stale window the
  request recomputes synchronously.
- `Cache::memo()` decorates a store so repeated reads of one key inside a request hit memory;
  `once()` memoises a callback's result for the current request or job without touching any store.
- `Cache::touch($key, $ttl)` extends an item's TTL without a read-modify-write (Laravel 13).
- Tags let you invalidate a group without tracking keys, and are **not** supported by the `file`,
  `database` or `dynamodb` drivers.
- The `failover` driver moves to the next store when one throws — not on a plain cache miss, and
  it does not replicate.

Cache and session both deserialise whatever they stored. Laravel 13's skeleton sets the cache's
`serializable_classes` to `false` and the session's `serialization` to `json` to blunt PHP
deserialisation gadget chains if `APP_KEY` leaks. An application that intentionally caches PHP
objects must list those classes explicitly.

## Application structure

Extract a business operation into an action or service class when it becomes reusable or
independently testable — not to satisfy a line limit, and not speculatively. Laravel gives action
classes no special meaning; follow whatever naming and invocation convention the project already
has.

Depend on a contract at a real boundary (payment gateway, notification channel, external service)
where an alternative implementation or a test double is genuinely useful, and bind it in a service
provider. Everywhere else, depend on the concrete class.

Inject dependencies through the constructor, or through the signature of a container-invoked
method for a single-action need. Laravel 13's contextual attributes cover the cases that used to
force a manual `app()` call: `#[Config('app.timezone')]`, `#[CurrentUser]`, `#[RouteParameter]`,
`#[Give(DatabaseRepository::class)]`, `#[Cache('redis')]`, `#[DB('mysql')]`, `#[Log('daily')]`.

Add a package or change a dependency only with the user's agreement, and stay inside the existing
directory structure.

## Octane and long-lived workers

Octane boots the application once and reuses it across requests, so `register()` and `boot()` run
once per worker and anything captured in a singleton outlives the request that created it.

- Do not inject the container or the `Request` into a singleton's constructor. Inject a resolver
  closure (`fn () => Container::getInstance()`) or, better, pass the specific values a method
  needs at call time.
- Static arrays that accumulate entries are a memory leak that only shows up under Octane; a
  process that grows across requests is the symptom.
- Octane resets first-party framework state between requests. It cannot reset global state your
  own code created.

Choose Octane for a measured request-throughput problem, after the query and cache work is done —
it multiplies existing state bugs rather than creating new performance headroom for free.

## Upgrading 12 to 13

Laravel 13 (March 2026) requires PHP 8.3–8.5. Laravel 12 accepts PHP 8.2–8.5 and receives bug
fixes until August 2026 and security fixes until February 2027. The upgrade is deliberately small;
`laravel/boost` ^2 exposes an `/upgrade-laravel-v13` prompt that automates most of it.

Dependency floors: `laravel/framework ^13.0`, `laravel/tinker ^3.0`, `phpunit/phpunit ^12.0`,
`pestphp/pest ^4.0`, `laravel/boost ^2.0`.

The changes that actually break applications:

| Change | What to do |
|---|---|
| CSRF middleware renamed to `PreventRequestForgery` (with `Sec-Fetch-Site` origin checking) | Update every `withoutMiddleware([VerifyCsrfToken::class])` in routes and tests; the old names survive as deprecated aliases |
| Cache `serializable_classes` defaults to `false` | List the classes the application intentionally caches, or move to array payloads |
| Session `serialization` defaults to `json` | Adopting it logs every active session out; keep `php` to upgrade seamlessly and switch deliberately |
| MySQL/MariaDB `upsert` validates `uniqueBy` | An empty `uniqueBy` now throws `InvalidArgumentException` instead of producing invalid SQL |
| MySQL `DELETE ... JOIN` now compiles `ORDER BY` / `LIMIT` | Previously ignored clauses can now make the engine throw `QueryException` |
| `JobAttempted::$exceptionOccurred` → `$exception` | Update queue event listeners |
| `QueueBusy::$connection` → `$connectionName` | Update listeners |
| `Container::call` honours nullable class defaults | Method injection that relied on receiving an instance now receives `null` |
| Instantiating a model while it is booting throws `LogicException` | Move the work out of `boot()` / `boot*()` trait hooks |
| Model collections restore eager-loaded relations on deserialisation | Check queued jobs whose payload size or post-deserialisation state assumed otherwise |
| Custom `Str` factories reset between tests | Set them per test or in a setup hook |
| Domain routes now match before non-domain routes | Review overlap between catch-all subdomain routes and normal routes |
| `symfony/polyfill-php85` defines global `array_first()` / `array_last()` | Prefer `Arr::first()` / `Arr::last()`, which no legacy helper package shadows |
| `Js::from` emits unescaped Unicode | Update snapshots that pinned `\u00e8`-style escapes |
| Bootstrap pagination views renamed to `pagination::bootstrap-3` | Update direct references |
| Default password-reset subject is now "Reset your password" | Update assertions and translation overrides |

## Applying an upgrade safely

Whether it is a framework major, a starter-kit sync or a dependency bump, the same guardrails
apply and they are worth stating to the user before touching anything:

- Refuse to start with a dirty working tree. Do not stash on the user's behalf.
- Work on a dedicated branch; never modify the branch the user was on.
- One coherent change per commit, so a single step can be reverted.
- Never auto-resolve a conflict in customised code, and never silently overwrite `composer.json`,
  `package.json` or a lock file — show the diff and let the user decide.
- Behaviour preservation is the contract: the checks that passed before must pass after. A
  previously-passing test that now fails is a regression to surface, not to fix by editing the
  test.

<!-- sources: laravel-boost, laravel-docs, laravel-agent-skills -->
