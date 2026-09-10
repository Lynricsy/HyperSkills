# Modern PHP in a Laravel application

Verified against: PHP 8.3–8.5, Laravel 13.

## Contents

- [Version floor](#version-floor)
- [Types and signatures](#types-and-signatures)
- [Enums](#enums)
- [Readonly, promotion and immutability](#readonly-promotion-and-immutability)
- [Named arguments and Laravel's backwards-compatibility promise](#named-arguments-and-laravels-backwards-compatibility-promise)
- [Attributes](#attributes)
- [Strings and arrays](#strings-and-arrays)
- [Version-gated syntax](#version-gated-syntax)
- [Style gate](#style-gate)

## Version floor

Laravel 13 requires PHP 8.3 and supports up to 8.5; Laravel 12 accepts 8.2–8.5. Read
`composer.json` before using anything newer than the floor the project declares — `"php": "^8.3"`
means 8.3 is a legal deploy target even if your machine runs 8.5, so a property hook or a pipe
operator in application code is a production fatal error, not a style choice. `composer show
--direct` lists the resolved versions of every direct dependency when the constraint is not
enough. [official]

## Types and signatures

Declare parameter, return and property types on everything you write. In a framework this dense
with magic (`__get`, facades, container resolution) the type declaration is often the only place
the shape is stated, and it is what makes static analysis worth running at all.

```php
public function isAccessible(User $user, ?string $path = null): bool
```

Use constructor property promotion, and do not leave an empty zero-argument `__construct()` behind
unless it is private to block instantiation.

```php
public function __construct(
    private readonly PaymentGateway $gateway,
    private readonly LoggerInterface $log,
) {}
```

Prefer PHPDoc blocks over inline comments, and use them where the language cannot express the type:
array shapes (`@return array{id: int, name: string}`), generic collections
(`@return Collection<int, Order>`), and closure signatures. A `@param array $data` PHPDoc that
repeats the signature is noise; an array shape is not. [official]

## Enums

Back a domain enum with a scalar and cast it on the model, so the value is an enum everywhere in
PHP and a plain column in the database:

```php
enum OrderStatus: string
{
    case Pending = 'pending';
    case Shipped = 'shipped';

    public function isTerminal(): bool
    {
        return $this === self::Shipped;
    }
}

// Model
protected function casts(): array
{
    return ['status' => OrderStatus::class];
}
```

Use TitleCase for case names unless the codebase already uses another convention. Backed enums
work directly in validation (`Rule::enum(OrderStatus::class)`), in route model binding, and as
`Feature::define` return values. A pure (unbacked) enum cannot be stored, so use one only for
in-memory states. [official]

## Readonly, promotion and immutability

`readonly` promoted properties are the right default for job payloads, DTOs, events and action
dependencies: the object is constructed once and never mutated, which is exactly what serialisation
across a queue boundary assumes. Note the interaction that bites: a queued job's `failed()` method
runs on a **new** instance rebuilt from the payload, so mutating any property during `handle()` —
readonly or not — is invisible there.

PHP 8.5 adds `clone($object, ['property' => $value])`, which is the only clean way to derive a
modified copy of a readonly object. Below 8.5, give the class an explicit `with*()` method that
constructs a new instance.

## Named arguments and Laravel's backwards-compatibility promise

Laravel explicitly excludes parameter names from its backwards-compatibility guarantees: a minor
release may rename an argument. Named arguments are fine for your own code and for a small number
of framework calls where they genuinely improve clarity
(`Queue::route(ProcessPodcast::class, connection: 'redis')` reads better than a positional list),
but do not adopt them wholesale across framework calls, and never rely on them in a package that
must survive minor upgrades. [official]

## Attributes

Laravel 13 pushes configuration onto PHP attributes across the framework: `#[Scope]`, `#[Table]`,
`#[ObservedBy]` on models; `#[Middleware]` and `#[Authorize]` on controllers; `#[Tries]`,
`#[Backoff]`, `#[Timeout]`, `#[FailOnTimeout]`, `#[UniqueFor]`, `#[DeleteWhenMissingModels]` on
jobs; `#[Config]`, `#[CurrentUser]`, `#[RouteParameter]`, `#[Give]` for contextual container
resolution.

For the queue attributes the framework reads the attribute *and* the legacy public property, and a
property whose value differs from its declared default wins over the attribute. Declaring both for
the same setting therefore produces a silent, order-dependent result — pick one form per class.
[verified: the framework's `ReadsClassAttributes` trait, `getAttributeValue()`]

## Strings and arrays

`strlen()` counts bytes and `strtolower()` ignores non-ASCII, so any user-supplied text needs the
multibyte function or the Laravel helper:

```php
mb_strlen('José');        // 4, where strlen() gives 5
Str::lower('MÜNCHEN');    // 'münchen', where strtolower() leaves Ü alone
```

Reach for `Str`, `Arr`, `Number` and `Uri` when they state the intent more directly
(`Str::slug()`, `Arr::get($array, 'user.name', 'default')`, `Number::currency(1500, 'USD')`,
`Uri::of($url)->withQuery([...])`), not as a blanket replacement for built-ins.

`Number` is for display. Never store or calculate on its output — it is locale-formatted text.

## Version-gated syntax

Use these only when the project's `php` constraint guarantees the version:

- **8.4**: `array_find()`, `array_find_key()`, `array_any()`, `array_all()` instead of hand-rolled
  loops when not already inside a Laravel collection; `new JsonResponse($data)->setStatusCode(201)`
  without wrapping parentheses.
- **8.5**: `array_first()`, `array_last()`; the pipe operator `|>` for left-to-right chains;
  `clone($object, [...])`.

One conflict to know about: Laravel 13 depends on `symfony/polyfill-php85`, which defines global
`array_first()` / `array_last()` on PHP below 8.5. Legacy helper packages such as
`laravel/helpers` define an `array_first()` with a *different* signature (it took a callback), so a
project carrying both gets whichever loaded first. Use `Arr::first($array, $callback)` and the
ambiguity disappears. [official]

## Style gate

`vendor/bin/pint --dirty` before finishing any change that touched PHP files; add
`--format agent` when the installed Pint supports it. Run the fixer, not `pint --test` — a report
you then have to apply by hand is a wasted round trip.

<!-- sources: laravel-boost, laravel-docs, laravel-framework, php-src -->
