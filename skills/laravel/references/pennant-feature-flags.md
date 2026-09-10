# Feature flags with Laravel Pennant

Verified against: Laravel Pennant 1.x on Laravel 13.

## Contents

- [The one thing to understand first](#the-one-thing-to-understand-first)
- [Defining a feature](#defining-a-feature)
- [Checking a feature](#checking-a-feature)
- [Scope](#scope)
- [Rollouts and purging](#rollouts-and-purging)
- [Loops and eager loading](#loops-and-eager-loading)
- [Testing](#testing)
- [Retiring a flag](#retiring-a-flag)

## The one thing to understand first

**The first check for a given scope resolves the closure and stores the result.** Every later
check for that scope reads storage; the closure never runs again. This is what makes a
`Lottery`-based rollout stable per user — and it is also why editing the definition changes
nothing for anyone who has already been resolved, and why a lottery makes tests
non-deterministic until you take control of the value.

## Defining a feature

```php
// Feature is the Pennant facade; Lottery is a Laravel support helper.
Feature::define('new-api', fn (User $user) => match (true) {
    $user->isInternalTeamMember() => true,
    $user->isHighTrafficCustomer() => false,
    default => Lottery::odds(1 / 100),
});
```

A definition that is only a lottery can skip the closure: `Feature::define('site-redesign',
Lottery::odds(1, 1000))`. Class-based features in `app/Features` are the better home once a flag
has real logic, dependencies, or its own default scope.

A feature is not restricted to booleans. Returning a string gives an A/B/C variant read with
`Feature::value('purchase-button')` and matched in Blade with `@feature('purchase-button',
'blue-sapphire') ... @elsefeature(...)`. With rich values, "active" means *any value other than
`false`* — so `active()` is true for the string `'off'`.

## Checking a feature

```php
if (Feature::active('new-api')) { /* ... */ }
if (Feature::for($team)->active('billing-v2')) { /* ... */ }

Feature::when('purchase-button', fn ($colour) => /* ... */, fn () => /* ... */);
```

```blade
@feature('new-dashboard')
    <x-new-dashboard />
@else
    <x-old-dashboard />
@endfeature
```

Pennant caches resolved values in memory for the request, so repeated checks of the same feature
cost nothing extra and stay consistent within one request. `Feature::flushCache()` clears it when
a long-running process needs to re-read.

## Scope

The default scope is the authenticated user, which means the scope is `null` in an Artisan
command, a queued job and any unauthenticated route. If the definition's parameter is not
nullable, Pennant returns `false` without invoking the closure — the flag silently reads as off in
exactly the contexts nobody tests.

```php
Feature::define('new-api', fn (User|null $user) => match (true) {
    $user === null => true,           // decide explicitly what "no scope" means
    $user->isInternalTeamMember() => true,
    default => Lottery::odds(1 / 100),
});
```

Either handle `null` in the definition or always pass the scope explicitly with `for()`. Scoping
to a team, an organisation or an account is as valid as scoping to a user; type-hint whichever
model the rollout is actually per.

## Rollouts and purging

Widening a rollout by editing the odds only affects scopes that have never been resolved. To
re-roll everyone, purge the stored values:

```shell
php artisan pennant:purge new-api
php artisan pennant:purge --except-registered      # drop flags no longer defined anywhere
```

`Feature::activate($name)` / `deactivate()` (optionally `for($scope)`) override a single stored
value — the right tool for enabling a flag for one customer, the wrong tool for a rollout change.

Purging is a deployment step. A rollout change that ships without one is a change that appears to
do nothing.

## Loops and eager loading

With the `database` driver, checking a feature per item in a loop is one query per item. Load the
values first:

```php
Feature::for($users)->load(['notifications-beta']);      // or loadMissing([...]) / loadAll()

foreach ($users as $user) {
    if (Feature::for($user)->active('notifications-beta')) { /* ... */ }
}
```

## Testing

Re-define the feature at the top of the test. The definition in the service provider — lottery,
randomness and all — is then irrelevant:

```php
test('shows the new checkout', function () {
    Feature::define('express-checkout', true);
    // ...
});
```

The same works for class-based features (`Feature::define(NewApi::class, true)`). A test that
instead relies on the real definition is asserting a coin flip. If the flag genuinely must resolve
through a `Lottery`, use the lottery test helpers rather than repeating the run.

Cover both branches. A flag that is only ever tested in its "on" state means the fallback path
ships untested and stays that way until the rollback that needs it.

## Retiring a flag

Removing the `Feature::define` call does not remove the stored values, and an undefined feature
that is still checked resolves as inactive while emitting an `UnknownFeatureResolved` event. Delete
the checks, delete the definition, then purge the name — in that order, so no request lands
between the definition disappearing and the branch being removed.

<!-- sources: laravel-boost, laravel-docs -->
