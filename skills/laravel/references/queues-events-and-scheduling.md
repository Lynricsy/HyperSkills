# Queues, jobs, events and scheduling

Verified against: Laravel 13 (13-only APIs are labelled).

## Contents

- [The reservation race](#the-reservation-race)
- [Attempts, backoff and timeouts](#attempts-backoff-and-timeouts)
- [Idempotency and uniqueness](#idempotency-and-uniqueness)
- [Failure handling](#failure-handling)
- [Jobs and database transactions](#jobs-and-database-transactions)
- [Payloads](#payloads)
- [Batches and chains](#batches-and-chains)
- [Queue routing](#queue-routing)
- [Events and listeners](#events-and-listeners)
- [Notifications and mail](#notifications-and-mail)
- [Work that is not a queue job](#work-that-is-not-a-queue-job)
- [Scheduling](#scheduling)
- [Artisan commands](#artisan-commands)

## The reservation race

For drivers that use Laravel's `retry_after` (database, Redis, Beanstalkd), the connection's
`retry_after` must be **longer** than the longest job or worker timeout, and the worker's
`--timeout` must be shorter than `retry_after`. When a reservation expires while the first worker
is still running, a second worker picks the same job up and both execute it.

```php
// config/queue.php — connection
'retry_after' => 150,
```

```php
#[Timeout(120)]      // job, Laravel 13; below that, public $timeout = 120;
```

SQS ignores `retry_after` and uses its own visibility timeout, configured on the queue itself.

Correct timeouts reduce duplicates; they do not eliminate them. A worker can be killed after the
side effect and before the acknowledgement, so anything whose repetition is visible to a user or a
third party has to be idempotent anyway.

## Attempts, backoff and timeouts

A job defaults to **one** attempt. An attempt is consumed by an unhandled exception, an explicit
`release()`, a `WithoutOverlapping` or `RateLimited` middleware failing to take its lock, a
timeout, and a clean run — so any job using that middleware needs a raised attempt limit or it
gets one shot at the lock and then fails.

Laravel 13 declares these as class attributes:

```php
// Tries, Backoff, Timeout and FailOnTimeout live in the queue Attributes namespace.
#[Tries(4)]
#[Backoff(1, 5, 10)]     // progressive delays between attempts
#[Timeout(120)]
#[FailOnTimeout]         // otherwise a timeout consumes an attempt and releases
class SyncWithStripe implements ShouldQueue {}
```

The old public properties (`$tries`, `$backoff`, `$timeout`, `$maxExceptions`, `$uniqueFor`,
`$deleteWhenMissingModels`) still work, and a property set to something other than its declared
default takes precedence over the attribute. Never declare both for one setting — the winner is
not obvious from reading the class.
[verified: the framework's `ReadsClassAttributes` trait, `getAttributeValue()`]

`retryUntil()` is the time-based alternative and takes precedence over attempt counts, so
`$tries = 0` alongside it is redundant.

Back off transient failures only. A validation error or a rejected business rule will fail
identically on every attempt; fail it immediately instead of burning the retry budget.

## Idempotency and uniqueness

They solve different problems and you usually need both:

- `ShouldBeUnique` + `uniqueId()` + `#[UniqueFor(3600)]` stops a **second dispatch** while one is
  pending. It is a cache lock, needs a shared lock-capable store across every dispatching process,
  and does not apply to jobs inside a batch. Use `ShouldBeUniqueUntilProcessing` when the lock
  should drop as processing starts.
- Idempotent processing stops a **second execution** from having a second effect: an idempotency
  key on the outbound request, a uniqueness constraint, or a guard that checks whether the work is
  already recorded before doing it again.

## Failure handling

`failed(?Throwable $e)` runs on a **freshly deserialised instance**. Anything `handle()` mutated on
`$this` is gone; read `$this->attempts()`, the payload, or the exception. Implement it when the
application must record state or alert someone — the queue's own failure reporting already logs the
exception, so a `Log::error` in every job just duplicates it.

`ThrottlesExceptions` middleware and `maxExceptions` bound a job that keeps failing against a
degraded dependency without exhausting attempts on every one of its siblings.

## Jobs and database transactions

A job dispatched inside `DB::transaction()` can be reserved by a worker before the transaction
commits, so it sees rows that do not exist yet. Fix it at the dispatch site with `->afterCommit()`,
or once for the connection with `'after_commit' => true`. When the transaction rolls back, the
dispatch is discarded.

The same hazard covers queued **listeners, mailables, notifications and broadcast events**;
`after_commit` on the connection covers all of them, and per-object escapes exist:

```php
ProcessPodcast::dispatch($podcast)->afterCommit();
$user->notify((new InvoicePaid($invoice))->afterCommit());
Mail::to($user)->send((new OrderShipped($order))->afterCommit());
```

For a synchronous event dispatched inside a transaction, `ShouldDispatchAfterCommit` on the event
class delays dispatch until every open transaction commits and discards it on rollback.

`beforeCommit()` is the escape hatch when `after_commit` is on globally and one job must go now.

## Payloads

Serialising an Eloquent model into a job stores the key and re-fetches the record when the job
runs; if the record is gone the job throws `ModelNotFoundException`. `#[DeleteWhenMissingModels]`
discards it quietly instead — Laravel 13 also honours that attribute for queued notifications.

Laravel 13 restores eager-loaded relations when a model **collection** is serialised and
deserialised. That changes payload size and post-deserialisation state for jobs that used to
receive bare models; check jobs that relied on relations being absent.

## Batches and chains

`Bus::batch()` coordinates a group and gives you `then()` / `catch()` / `finally()`. A batch is not
a transaction: work already completed is not rolled back when a sibling fails. One failure cancels
the remaining jobs unless `allowFailures()` says partial completion is acceptable. Unique-job
constraints do not apply inside a batch.

## Queue routing

Laravel 13 centralises connection/queue assignment instead of scattering `onQueue()` across
dispatch sites:

```php
Queue::route(ProcessPodcast::class, connection: 'redis', queue: 'podcasts');
Queue::route(RequiresVideo::class, queue: 'video');       // interface, trait or parent class
Queue::forward('reports', 'reports.fifo', 'sqs');         // move a queue without touching jobs
```

A job's own explicit connection still wins.

## Events and listeners

Listeners are discovered from the configured directories by the type hint on `handle()` /
`__invoke()`; register manually only when discovery is off or the listener lives elsewhere. Cache
the discovery in deployment (`php artisan optimize` or `event:cache`) and rebuild it whenever
listener definitions change — a stale cache means a listener silently stops firing.

## Notifications and mail

Queue anything that calls an external service, unless the caller needs immediate delivery
feedback. `ShouldQueue` on a mailable makes `Mail::send()` queue it, which changes the assertion:
`Mail::assertQueued()` for queued mailables, `Mail::assertSent()` only for synchronous ones — the
wrong one fails a correct implementation.

`Notification::route('mail', 'ops@example.com')->notify(...)` sends to an address with no model.
Implement `HasLocalePreference` on the notifiable so queued delivery keeps the recipient's locale.

## Work that is not a queue job

`defer(fn () => ...)` runs after the response in the **same process**: no retry, no durability, and
it dies with the worker. Use it for logging a page view; use a queued job the moment losing the
work matters.

`Concurrency::run([...])` executes closures in child processes that each boot the application, so
it pays off for genuinely independent IO-bound work and loses on cheap queries.

`Context::add()` carries request-scoped data through the call stack and into queued jobs, and
visible context is added to log records. `Context::addHidden()` propagates to jobs without
appearing in logs — that propagation is exactly why secrets do not belong there.

## Scheduling

- `withoutOverlapping($minutes)` — the argument is the **lock expiry**, not a task timeout. The
  default is 24 hours; too short an expiry lets a second run start while the first is still
  working. `php artisan schedule:clear-cache` releases a stale lock.
- `onOneServer()` — every scheduler node must share one lock-capable cache store. Name scheduled
  closures before applying it, or two closures collide on one lock identity.
- `runInBackground()` — for `command()` and `exec()` tasks only, and only where the task is
  independent; same-minute tasks otherwise run sequentially.
- `environments(['production'])` is an operational guard, not authorization.
- There is no scheduler-level deadline. Bound long work inside the command itself — finite chunks,
  an explicit deadline check, or dispatched jobs with their own timeouts.

## Artisan commands

Generate files with `php artisan make:*` and pass `--no-interaction` so a prompt cannot hang;
`php artisan make:class` covers a plain PHP class. `php artisan list` and `<command> --help` are
cheaper than guessing an option.

Destructive commands need explicit human confirmation, never an autonomous run: `migrate:fresh`,
`migrate:refresh`, `migrate:reset`, `migrate:rollback`, `db:wipe`, `db:seed`, and any command
carrying `--seed`. Nothing distinguishes a development database from production at the command
line, and a wrong `.env` is the whole failure mode. Mark commands that must not run concurrently
with the `Isolatable` interface. [community]

<!-- sources: laravel-boost, laravel-docs, laravel-framework, johnlui-laravel-skills -->
