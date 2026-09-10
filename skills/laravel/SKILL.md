---
name: laravel
description: "Guides Laravel application work on Laravel 12 and 13 with modern PHP: Eloquent modelling and loading strategy (N+1, eager loading, scopes, casts, strictness), migrations and indexes, routing and controllers, form requests and validation, gates and policies, request-forgery protection and rate limiting, queues and jobs (retry_after versus timeout, attempts and backoff, idempotency versus ShouldBeUnique, dispatching inside transactions), events, notifications and mail, scheduling and Artisan, Blade and Livewire 4, Pennant feature flags, Pest tests and suite isolation, configuration, Octane caveats, and the 12 to 13 upgrade. Use when writing, reviewing, debugging or upgrading Laravel PHP code, when a page issues far too many queries, when a queued job duplicates or loses work, when a feature flag or a test behaves nondeterministically, or when Artisan, Eloquent, Blade, Livewire or Pennant appear in the task. Do not use for Laravel Cloud or Forge hosting and deployment operations, or for WordPress."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: framework
---

# laravel

Paths below are relative to this skill's directory.

## Scope

Covers building, reviewing, debugging and upgrading a Laravel application: the framework's HTTP
layer, Eloquent and the database, queues and background work, authorization, Blade and Livewire,
Pennant feature flags, the Pest test suite, Artisan and the toolchain, and the modern PHP the
framework assumes.

Written against **Laravel 13** (March 2026, PHP 8.3–8.5) with the rules that also hold on
**Laravel 12** left unmarked. Always confirm the installed versions before applying a
version-sensitive rule: `composer show --direct`.

Not covered:

- Reviewing a diff for general correctness, structure and style — use the `code-review` skill;
  come back here for the Laravel-specific rules a reviewer applies.
- Driving a reproducible local failure down to a root cause — use the `debugging` skill.
- Deciding what deserves a test and driving code with tests — use the
  `test-driven-development` skill; this skill covers how a Laravel test is written once you know
  what to test.
- Visual design, layout, CSS and design systems — use the `frontend-design` skill.
- The JavaScript side of an Inertia application — component design, client state, routing inside
  the framework — use the `vue` or `react` skill. This skill stops at the Laravel controller and
  the props it sends.
- REST contract and OpenAPI design: resource modelling, URI and versioning policy, pagination
  strategy, the error schema itself — use the `api-design` skill.
- PostgreSQL engine work: query plans, index internals, connection pooling, extensions — use the
  `postgres` skill. This skill covers what Eloquent and migrations do to a database, not how to
  tune one.
- Not covered: Laravel Cloud, Forge, Vapor and any other hosting or deployment control plane —
  provisioning, deploy pipelines, environment management and their dashboards. Report what the
  application needs from its host and stop there.
- Not covered: WordPress, Symfony and other non-Laravel PHP applications.

## Core rules

1. Read the project before writing anything. Laravel supports several valid approaches to most
   problems and the best one is the one already in the codebase — check sibling files, the
   nearest controller, model and test. A second convention beside an existing one is worse than a
   suboptimal convention, so deviate only for a correctness or security defect and say that you
   are deviating.
2. Confirm the installed version before using a version-sensitive API (`composer show --direct`,
   `package.json`). Laravel 13 moved a lot of configuration onto PHP attributes; a Laravel 12
   project has the property form and nothing else.
3. Generate files with `php artisan make:*` and pass `--no-interaction`. `php artisan list` and
   `<command> --help` cost one call and beat guessing an option name.
4. Never run a destructive Artisan command on your own initiative: `migrate:fresh`,
   `migrate:refresh`, `migrate:reset`, `migrate:rollback`, `db:wipe`, `db:seed`, or anything with
   `--seed`. Nothing at the command line distinguishes a scratch database from production, and a
   stale `.env` is the entire failure mode.
5. Eager load a relationship that will be read for many models, and count with `withCount()`
   rather than hydrating rows to call `->count()`. When you constrain an eager load's `select`,
   keep every key the relationship matches on or the relation silently comes back empty.
6. Make the N+1 fail loudly instead of relying on review: `Model::preventLazyLoading(!
   app()->isProduction())` in `AppServiceProvider::boot()`. Automatic eager loading
   (`Model::automaticallyEagerLoadRelationships()`) is the opposite strategy — it hides the
   access instead of surfacing it. Pick one; enabling both is contradictory.
7. Eager loading a `hasMany` does not populate the inverse on the children, so walking back up the
   relation re-queries the parent per child. Declare the relation with `chaperone()`.
8. A scope must not read ambient state. `auth()->user()` inside a scope works in a request and
   breaks in every job, command and test; take the tenant as an argument.
9. Models guard attributes by default and `$guarded = []` throws that away. Declare `$fillable`
   on anything filled from request data, and pass `validated()` or `safe()->only([...])`, never
   `$request->all()`.
10. Bindings protect values, not identifiers. A user-supplied column name or sort direction has to
    go through an allow-list; there is no binding that makes `ORDER BY {$dir}` safe.
11. Authentication is not permission and validation is not authorization. Any action whose outcome
    depends on who is asking needs a policy, a gate or a form request `authorize()`. Where the
    existence of a record is itself confidential, deny as 404 rather than 403.
12. `retry_after` on the queue connection must exceed the longest job or worker timeout, and the
    worker `--timeout` must stay below it. Otherwise a second worker reserves a job the first is
    still running. Correct timeouts reduce duplicates; only idempotent processing removes them,
    because a worker can die after the side effect and before the acknowledgement.
13. A job defaults to one attempt, and `WithoutOverlapping` or `RateLimited` failing to take a lock
    consumes one. Any job with that middleware needs a raised attempt limit or it gets a single
    shot at the lock.
14. `ShouldBeUnique` deduplicates *dispatch* through a cache lock; it is not idempotent
    processing, it needs a shared lock-capable store, and it does not apply inside a batch.
15. `failed()` runs on a freshly deserialised instance, so anything `handle()` mutated on `$this`
    is gone. Read `$this->attempts()`, the payload, or the exception.
16. A job, queued listener, mailable, notification or broadcast dispatched inside
    `DB::transaction()` can run before the commit. Fix it with `afterCommit()` at the call site or
    `'after_commit' => true` on the connection, and use `ShouldDispatchAfterCommit` for synchronous
    events. `DB::transaction()` also retries its closure on deadlock, so the closure must be safe
    to run twice.
17. `defer()` runs after the response in the same process with no retry and no durability. The
    moment losing the work would page someone, it is a queued job.
18. Call `env()` only from `config/*.php`. After `config:cache` the `.env` file is not loaded, so
    `env()` in application code returns `null` exactly where it matters — read `config()` instead,
    and check the environment with `app()->isProduction()`.
19. Pennant stores a feature's value the first time it resolves for a scope. Editing the
    definition changes nothing for anyone already resolved, so a rollout change ships with
    `pennant:purge`. The default scope is `null` in jobs, commands and unauthenticated routes,
    which reads as inactive unless the definition's parameter is nullable.
20. Keep queries out of Blade. A template loop is where relation access hides from the controller,
    from tests, and from every eager-loading decision. `{{ }}` escapes; `{!! !!}` is only for
    content sanitised for the exact context it renders into.
21. In Livewire, `wire:key` on every element in a loop, `wire:model` is deferred (`.live` for
    live updates), and a component action is a public HTTP entry point that validates and
    authorizes like a controller.
22. Tests assert observable behaviour, and a write operation's complete result is the response
    plus the database state plus the jobs, events, mail and notifications it produced. A test that
    asserts only `assertOk()` passes when nothing was saved.
23. Control time, randomness, sleep and outbound HTTP in every test that depends on them:
    `freezeTime()` / `travelTo()` (not `Carbon::setTestNow()`), `Sleep::fake()`,
    `Http::preventStrayRequests()` plus a fake for the specific endpoint, and class names passed
    to `Event::fake()` / `Queue::fake()`. Create factory records *before* faking events.
24. Every outbound `Http::` call sets `connectTimeout()` and `timeout()` and either calls
    `->throw()` or checks the status before reading the body. The client defaults to a 30-second
    response timeout that retries multiply, and it returns 4xx/5xx as ordinary responses — so a
    bare `->json()` silently parses an error page into your domain.
25. Finish with the project's own gate: `vendor/bin/pint --dirty`, the narrowest test selection
    that covers the change (`php artisan test --compact --filter=...`), then the wider suite, plus
    whatever static analysis the project runs. Report the commands and their output; when a
    command named here does not exist in the project, say so and name the one that does.

## Workflows

### build-or-change-a-feature

- [ ] Establish the ground truth first: Laravel and PHP versions from `composer.json`, whether the
      skeleton is Laravel 11+ (`bootstrap/app.php`) or an upgraded Laravel 10 layout
      (`app/Http/Kernel.php`), and which test framework is installed.
- [ ] Read the nearest existing example of what you are about to write — controller, model,
      action, test — and follow its structure and naming.
- [ ] Generate the files with `php artisan make:*` rather than hand-writing boilerplate, and make
      a factory for any new model.
- [ ] Put validation and authorization at the boundary: a form request or an inline
      `$request->validate()`, plus a policy check (`references/http-and-validation.md`).
- [ ] Decide the data access deliberately — relationships and casts on the model, eager loads at
      the query, no query in the view (`references/eloquent-and-data-access.md`).
- [ ] Decide where side effects run: inline, `defer()`, a queued job, or an event with a queued
      listener — and whether it is dispatched inside a transaction
      (`references/queues-events-and-scheduling.md`).
- [ ] Write the tests in the same change: the valid path asserting response *and* persisted state,
      one failed-authorization case, one validation failure asserting the message
      (`references/testing-with-pest.md`).
- [ ] **Gate — the change is proven, not just written:** the new tests pass,
      `vendor/bin/pint --dirty` is clean, and you have exercised the changed path once for real
      (a request, an Artisan call, or `queue:work --once`) rather than only running unit tests.

### fix-a-query-or-performance-problem

- [ ] Get the number first. Query count and timing from Telescope, Debugbar, Pulse, or a
      temporary `DB::listen()` — a fix chosen without a measurement is a guess.
- [ ] Classify the shape: query count scaling with row count is an N+1; one slow query is an index
      or plan problem; memory growth is a full-result hydration; latency under concurrency with
      no slow query is lock contention or an external call.
- [ ] For an N+1, find where the relation is accessed — usually a Blade loop, an API resource, or
      a job — then eager load at the query, `withCount()` for counts, `chaperone()` for inverse
      access.
- [ ] Turn on `Model::preventLazyLoading(! app()->isProduction())` so the next one fails in
      development instead of shipping.
- [ ] For a single slow query, read the plan and design the index for the real filter and sort
      order. Do not add an index because a column appears in a `WHERE`
      (`references/eloquent-and-data-access.md`).
- [ ] For memory, replace `all()` with keyed chunking (`chunkById` / `lazyById` when the loop
      writes to columns the query filters on) or one bulk statement.
- [ ] Cache only after the query work is done, and pick the right primitive:
      `remember`, `flexible`, `once`, `memo`, or a lock (`references/runtime-config-and-upgrades.md`).
- [ ] **Gate — the number moved:** report the before and after query count or timing for the same
      request, and name the mechanism that changed it.

### review-or-repair-a-test-suite

- [ ] Read the suite's conventions before judging any single test; a repeated pattern is a
      convention that outranks a default.
- [ ] For each test in scope, name the defect it would catch. A test that catches nothing gets
      reported, not silently rewritten.
- [ ] Fix nondeterminism first: records created in `beforeEach()`, bare `Http::fake()`,
      `Carbon::setTestNow()`, nameless `Event::fake()` before factories, real sleeps
      (`references/testing-with-pest.md`).
- [ ] Check assertion strength: named response assertions, a known expected value rather than one
      the implementation computed, and the full result of every write.
- [ ] Check the coverage split: the permission matrix belongs to policy tests, the validation
      matrix to the rule test, with one case at the endpoint proving the wiring.
- [ ] For a slow suite, profile before configuring: `pest --profile`, then `BCRYPT_ROUNDS=4`,
      `LazilyRefreshDatabase`, disabled per-request packages, and `--parallel`.
- [ ] **Gate — the suite is honest and stable:** the previously failing or flaky test now passes
      repeatedly, the whole file passes in isolation *and* inside the full suite, and removing
      the behaviour under test makes it fail.

### upgrade-a-laravel-application

- [ ] Refuse to begin with a dirty working tree, and work on a dedicated branch.
- [ ] Establish the starting point: current framework, PHP and first-party package versions, and
      whether the checks that must still pass afterwards pass right now.
- [ ] Bump the dependency floors together (`laravel/framework`, `laravel/tinker`, PHPUnit, Pest,
      Boost) rather than one at a time.
- [ ] Work the breaking-change table in `references/runtime-config-and-upgrades.md`, starting with
      the ones that fail silently: the CSRF middleware rename, cache `serializable_classes`, and
      session `serialization`.
- [ ] Grep for the renamed symbols the compiler will not catch — `VerifyCsrfToken` in route and
      test exclusions, `JobAttempted::$exceptionOccurred`, `QueueBusy::$connection`.
- [ ] Commit one coherent change at a time so a single step can be reverted, and never silently
      overwrite `composer.json`, `package.json` or a lock file.
- [ ] **Gate — same behaviour, new version:** every check that passed before the upgrade passes
      after it, and any test you had to change is explained by a documented breaking change rather
      than edited to fit.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Relationships, loading strategy and strictness, `#[Scope]`, casts, subqueries, chunking, transactions and locks, mass assignment, migrations, indexes | Touching a model, a query, or the schema | `references/eloquent-and-data-access.md` |
| Route binding, resource controllers, controller attributes, form requests, validation, gates and policies, `PreventRequestForgery`, rate limits, API resources, exception handling, uploads, the HTTP client | Building or reviewing anything that answers a request or calls out over HTTP | `references/http-and-validation.md` |
| `retry_after`, attempts and backoff attributes, uniqueness versus idempotency, `failed()`, transactions, payload serialisation, batches, queue routing, events, notifications, mail, `defer()`, `Context`, scheduling, Artisan | Work that happens outside the request, or a job that duplicates, loses or reorders work | `references/queues-events-and-scheduling.md` |
| What earns a test, naming, factories and datasets, fakes and determinism, assertion choice, endpoint coverage, layer ownership, suite speed, review checklist | Writing, fixing or reviewing tests | `references/testing-with-pest.md` |
| Blade components and escaping, fragments, Livewire 4 component formats and directives, the v3→v4 changes, Volt, component testing | Anything under `resources/views`, or a Livewire component | `references/blade-and-livewire.md` |
| Feature definition and storage semantics, scope and the `null` scope, rich values, purging a rollout, eager loading flags, testing and retiring a flag | Pennant appears, or a flag behaves differently in a job, a test or after a rollout change | `references/pennant-feature-flags.md` |
| Skeleton layout, `env()` versus `config()`, cache primitives, action and contract boundaries, contextual container attributes, Octane state hazards, the 12→13 breaking-change table, upgrade guardrails | Configuration, caching, container wiring, Octane, or any upgrade | `references/runtime-config-and-upgrades.md` |
| Version floor, types and PHPDoc shapes, enums, readonly, named arguments, framework attributes and the attribute-versus-property precedence, `mb_*`, PHP 8.4/8.5-gated syntax, Pint | Writing PHP that must run on the project's declared floor, or reviewing style | `references/modern-php.md` |

## Environment

- Verify installed versions rather than assuming them: `composer show --direct` for PHP packages,
  `package.json` for JavaScript ones. `php artisan about` summarises the application's drivers and
  cache state in one call.
- Formatting is `vendor/bin/pint --dirty` (add `--format agent` when supported). Run the fixer,
  not `--test`.
- Tests are `php artisan test --compact`, narrowed with a path or `--filter=name`; call
  `vendor/bin/pest` or `vendor/bin/phpunit` directly for runner-specific flags.
- `laravel/boost` is the first-party MCP server for Laravel projects. When it is installed, its
  `search-docs` tool returns documentation for the versions this application actually has, which
  beats recalling an API. When it is not installed, inspect the framework in `vendor/` rather than
  guessing a signature.
