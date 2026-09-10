# Eloquent, queries and schema

Verified against: Laravel 13 (rules that also hold on 12 are unmarked; 13-only APIs are labelled).

## Contents

- [Loading strategy](#loading-strategy)
- [The inverse-relationship N+1](#the-inverse-relationship-n1)
- [Scopes](#scopes)
- [Casts and attributes](#casts-and-attributes)
- [Subqueries and aggregates](#subqueries-and-aggregates)
- [Iterating large result sets](#iterating-large-result-sets)
- [Transactions and locks](#transactions-and-locks)
- [Mass assignment](#mass-assignment)
- [Raw SQL and identifiers](#raw-sql-and-identifiers)
- [Migrations](#migrations)
- [Indexes](#indexes)

## Loading strategy

Eager load a relationship that will be touched for many models; leave it lazy when it may not be
needed or when there is exactly one model.

```php
$posts = Post::with('author')->get();
```

Constrain the eager load when the relation carries large columns, and keep every key Eloquent
needs to match rows — the parent's local key, the child's foreign key, and the related primary key:

```php
User::with(['posts' => fn ($q) => $q->select('id', 'user_id', 'title')->latest()->limit(10)])->get();
```

Dropping `posts.user_id` from that select silently produces empty relations, not an error.

Counting is a different operation from loading. `withCount('comments')` returns
`$post->comments_count` from one query; `$post->comments->count()` hydrates every comment row to
throw them away. Conditional counts get an alias:

```php
Post::withCount(['comments', 'comments as approved_count' => fn ($q) => $q->where('approved', true)])->get();
```

**Pick one strictness strategy for the whole application, and do it in `AppServiceProvider::boot()`:**

```php
Model::preventLazyLoading(! app()->isProduction());   // fail loudly outside production
```

The alternative is `Model::automaticallyEagerLoadRelationships()` (or
`$collection->withRelationshipAutoloading()` for one collection), which makes Laravel lazy-eager-load
the whole collection's relation on first access. It removes the query storm but also removes the
signal, so an unintentional access is no longer visible in review. Prefer `preventLazyLoading`
outside production and enable autoloading only where the access pattern is genuinely dynamic.
Enabling both is contradictory: the violation exception fires before the autoloader can help.
[official]

## The inverse-relationship N+1

Eager loading `comments` does **not** hydrate `$comment->post` on the children, so a loop that
walks back up the relation re-queries the parent once per child. Declare the relation with
`chaperone()` and Eloquent sets the parent on each child:

```php
public function comments(): HasMany
{
    return $this->hasMany(Comment::class)->chaperone();
}
```

For an already-loaded pair, `$feature->comments->each->setRelation('feature', $feature)` does the
same thing at the call site.

## Scopes

Extract a repeated constraint into a local scope so the same predicate cannot drift between call
sites. Laravel 12+ marks scopes with the `#[Scope]` attribute on a `protected` method rather than
the `scopeName()` prefix:

```php
// #[Scope] comes from the Eloquent Attributes namespace.
#[Scope]
protected function active(Builder $query): void
{
    $query->where('verified', true)->whereNotNull('activated_at');
}

User::active()->get();
Article::whereHas('user', fn ($q) => $q->active())->get();
```

A scope must not read ambient request state. `where('team_id', auth()->user()->team_id)` inside a
scope throws or silently returns the wrong rows in a queue job, an Artisan command and a test,
because there is no authenticated user there. Take the tenant as an argument:
`#[Scope] protected function forTeam(Builder $q, Team $team): void`.

Global scopes apply to every query on the model including admin screens, exports, reports and
jobs, and they do not appear at the call site. Reserve them for constraints that are genuinely
universal — soft deletes, hard multi-tenancy — and use an explicit local scope for anything a
reader might need to opt out of.

An alternative to a growing pile of scopes is a dedicated builder class registered with
`#[UseEloquentBuilder(OrderBuilder::class)]`, which gives the query methods a type and a home.
Treat it as the escape hatch for a model with many query methods, not the default. [community]

## Casts and attributes

Declare casts in a `casts()` method (the `$casts` property still works; follow the project):

```php
protected function casts(): array
{
    return [
        'status' => OrderStatus::class,
        'is_active' => 'boolean',
        'metadata' => 'array',
        'ordered_at' => 'datetime',
        'total' => 'decimal:2',
        'api_key' => 'encrypted',
    ];
}
```

Cast every date column the application treats as a date — Eloquent only does `created_at` and
`updated_at` for you, so an uncast `ordered_at` reaches Blade as a string and invites
`Carbon::parse()` in the template.

`encrypted` values cannot be queried and produce variable-length ciphertext, so the column needs to
be `TEXT` or larger; pair it with `$hidden` so it stays out of JSON. Encryption is not access
control.

Non-conventional table and key names belong on the `#[Table('my_flights', key: 'flight_id')]`
attribute rather than `$table` / `$primaryKey` properties in Laravel 13. Observers attach with
`#[ObservedBy([OrderObserver::class])]`.

Database defaults apply on insert, not on instantiation. If code reads `$model->status` before
saving, mirror the default in `$attributes` and keep the two in sync.

## Subqueries and aggregates

When one value from a has-many relation is needed, select it as a correlated subquery instead of
loading the collection:

```php
#[Scope]
protected function withLastLoginAt(Builder $query): void
{
    $query->addSelect([
        'last_login_at' => Login::select('created_at')
            ->whereColumn('user_id', 'users.id')
            ->latest()
            ->take(1),
    ])->withCasts(['last_login_at' => 'datetime']);
}
```

Several counts over the same filtered set collapse into one query with conditional aggregates plus
`toBase()` when models add nothing:

```php
Feature::toBase()
    ->selectRaw("count(case when status = 'Requested' then 1 end) as requested")
    ->selectRaw("count(case when status = 'Completed' then 1 end) as completed")
    ->first();
```

`whereHas()` compiles to `EXISTS` and `whereIn(..., $subquery)` to `IN`. Neither loads rows into
PHP and either can win depending on engine, indexes and cardinality — measure with the real query
plan rather than asserting one is faster.

## Iterating large result sets

| Need | Use | Why not the others |
|---|---|---|
| Attribute-only pass, no relations | `cursor()` | one query, hydrates one model at a time; cannot eager load, and some drivers still buffer the raw result |
| Relations needed per chunk | `lazy()` / `chunk()` | chunked queries, eager loading works per chunk |
| The loop updates columns the query filters on | `lazyById()` / `chunkById()` | offset pagination shifts rows as they stop matching, so plain `chunk()` skips records |

Never do `Model::all()` followed by a per-row `update()`. That is one hydration of the whole table
plus one write query per row; use a keyed chunk, or a single `$collection->toQuery()->update([...])`
when per-model events are not required (bulk updates do not fire them).

## Transactions and locks

`DB::transaction()` retries the closure on deadlock, so the closure must be safe to run twice: no
HTTP calls, no queue dispatches that are not `afterCommit`, no file writes.

Serialise concurrent work with the mechanism that matches the resource:

```php
Cache::lock('order-processing-'.$order->id, 10)->block(5, fn () => $order->process());

DB::transaction(function () use ($id) {
    $product = Product::where('id', $id)->lockForUpdate()->first();
    // row is locked until this transaction ends
});
```

`lockForUpdate()` is meaningless outside a transaction. `Cache::lock()` requires a store with
atomic locks (`redis`, `memcached`, `database`, `dynamodb`, `file`, `array`).

Validating against mutable state does not prevent a race between the check and the write. Stock
levels, uniqueness and quota limits need a database constraint, an atomic update or a lock.

## Mass assignment

Models guard everything by default; `$guarded = []` opts the model out entirely, which turns every
`create($request->all())` into a full-column write including `user_id`, `team_id`, `is_admin`.
Declare `$fillable` on any model populated from request data, and pass `validated()` or
`safe()->only([...])` rather than `all()`. Mass-assignment protection is not validation and not
authorization — never widen validation rules just to make a mass assignment succeed.

## Raw SQL and identifiers

Bindings protect *values*. They cannot protect an identifier, so a user-selected column or sort
direction must be mapped through an allow-list:

```php
$direction = $request->string('dir')->toString() === 'desc' ? 'desc' : 'asc';   // allow-list
$posts = Post::where('title', 'like', "%{$term}%")->orderBy('created_at', $direction)->get();
```

Prefer models over `DB::table()` in application code so casts, scopes and the model's configured
table stay in effect. Query builder and raw SQL are legitimate where their lower-level behaviour is
the point (reporting joins, bulk statements); keep those covered by tests, because a schema rename
will not touch them.

Migrations are the exception in the other direction: write literal table names there. A migration
is a historical snapshot, and a model renamed two years later must not change what an old migration
did.

## Migrations

- Generate with `php artisan make:migration create_posts_table` so the timestamp and structure are
  right.
- A migration that has run anywhere shared is immutable. Editing it makes fresh installs diverge
  from upgraded ones; write a new migration instead.
- When modifying a column, restate every attribute it had. Anything omitted is dropped.
- `down()` should be honest: implement it when the change is safely reversible and say so when it
  is not, rather than shipping a `down()` that destroys data.
- Adding a required or unique column to a populated table is a multi-step deploy: nullable column →
  code that tolerates both states → chunked backfill → constraint. Large backfills belong in a
  restartable command or job, not inside the schema migration.

## Indexes

An index follows a measured query pattern, not the presence of a column in `WHERE`. Selectivity,
write cost and the existing index set all matter, and foreign keys often already have one — check
before adding a duplicate. Composite index column order must match how the query filters and sorts,
and matching the `ORDER BY` list is not a guarantee the planner will use it. Confirm with the
database's own query plan against production-like data.

```php
$table->index(['status', 'created_at']);   // supports WHERE status = ? ORDER BY created_at
```

Pagination without an explicit, unique tie-breaker returns undefined row order and can repeat or
skip rows across pages: `->orderByDesc('created_at')->orderByDesc('id')->paginate()`.

<!-- sources: laravel-boost, laravel-docs, leeovery-agentic-skills -->
