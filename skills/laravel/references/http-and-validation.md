# Routing, controllers, validation and authorization

Verified against: Laravel 13 (13-only APIs are labelled).

## Contents

- [Routes and binding](#routes-and-binding)
- [Controllers](#controllers)
- [Validation](#validation)
- [Authorization](#authorization)
- [Request forgery protection](#request-forgery-protection)
- [Rate limiting](#rate-limiting)
- [Responses and API resources](#responses-and-api-resources)
- [Error handling](#error-handling)
- [Uploads](#uploads)
- [Outbound HTTP](#outbound-http)

## Routes and binding

Let implicit model binding resolve route parameters; `findOrFail($id)` in the action is the same
behaviour written by hand. When a nested resource must belong to its parent, add `scopeBindings()`
so `/users/{user}/posts/{post}` cannot resolve another user's post — this constrains resolution,
it does not authorize the request.

`Route::resource()` / `Route::apiResource()` when the endpoint fits the seven resource actions;
explicit routes when it does not. `apiResource()` omits `create` and `edit` and does **not** add an
`/api` prefix by itself — that comes from the application's API route file registration.

Generate links with named routes and `route()`, never string-concatenated paths.

In Laravel 13, routes carrying an explicit domain are matched before non-domain routes regardless
of registration order.

## Controllers

One resource per controller, using the standard action names. A custom verb (`publish`, `approve`,
`archive`) is a signal that a second resource is hiding: `PublishedPodcastController@store` /
`@destroy` gives the operation its own authorization, validation and middleware boundary. Treat it
as a signal, not a law — an explicit action route is fine when modelling it as a resource would
obscure the domain.

A controller coordinates: authorize, validate, call one application operation, return a response.
Extract substantial or reused logic into an action or service class; do not extract to satisfy a
line count.

Laravel 13 allows middleware and policy checks as attributes, which keeps them next to the action
they guard:

```php
#[Middleware('auth')]
class CommentController
{
    #[Middleware('subscribed')]
    #[Authorize('create', [Comment::class, 'post'])]
    public function store(Post $post) { /* ... */ }
}
```

Inject dependencies through the constructor (lifetime of the object) or the action signature (one
action). `app()` / `resolve()` inside a method hides the dependency from both the reader and the
test.

## Validation

A form request when the rule set is substantial, reused, or clearer outside the controller;
`$request->validate([...])` inline when it is small and local. Array rule syntax composes with rule
objects and avoids delimiter escapes: `'email' => ['required', 'email', Rule::unique('users')]`.

Pass forward only what was validated:

```php
$post = Post::create($request->safe()->only(['title', 'body']));
```

`validated()` still contains every validated key, including control fields the model should never
receive — hence `only()`. Typed accessors (`$request->string()`, `->integer()`, `->boolean()`,
`->date()`, `->enum()`) are for reading individual inputs with the right coercion.

Cross-field and stateful checks go in `after()`, guarded so they do not run expensive queries on
input that already failed:

```php
public function after(): array
{
    return [function (Validator $validator) {
        if ($validator->errors()->hasAny(['product_id', 'quantity'])) {
            return;
        }
        // ...compare against stock, add errors
    }];
}
```

Validation against mutable state is advisory: it cannot stop a race between the check and the
write. Back it with a database constraint or an atomic update.

## Authorization

Authentication is not permission and validation is not authorization. Every action whose result
depends on who is asking gets a policy, a gate, or a form request `authorize()`:

```php
Gate::authorize('update', $post);          // throws 403 (or the policy's own response)
```

```php
public function authorize(): bool
{
    return $this->user()?->can('update', $this->route('post')) ?? false;
}
```

Return a `Response` from a gate or policy when the status matters. For a resource whose existence
is itself confidential, `Response::denyAsNotFound()` answers 404 instead of confirming the record
exists with a 403.

`Gate::before()` short-circuits every check for a super-admin, which also means a bug there grants
everything; keep it to one narrow predicate and cover it in the policy tests.

## Request forgery protection

Laravel 13 renamed the CSRF middleware to `PreventRequestForgery` (`VerifyCsrfToken` and
`ValidateCsrfToken` remain as deprecated aliases). It now checks the browser's `Sec-Fetch-Site`
header first and falls back to token verification, and the builder method is
`preventRequestForgery(...)`. Route and test exclusions must reference the new class — an exclusion
list still naming `VerifyCsrfToken` keeps working through the alias but will not survive its
removal.

`@csrf` in every state-changing Blade form on the `web` middleware group. A route deliberately
excluded from the middleware — a third-party webhook — needs its own authenticity check
(signature verification), not nothing. Axios sends the encrypted `XSRF-TOKEN` cookie back as the
`X-XSRF-TOKEN` header; another client needs equivalent wiring. A token mismatch is never fixed by
disabling the middleware.

## Rate limiting

Limit login, password reset, verification resend, and any expensive or abusable API route. The
limiter key is the design decision: an IP alone punishes everyone behind one NAT, an account
identifier alone lets an attacker lock out a specific user.

```php
RateLimiter::for('login', fn (Request $request) => Limit::perMinute(5)->by(
    Str::transliterate(Str::lower($request->string('email')).'|'.$request->ip())
));
```

## Responses and API resources

Default to Eloquent API Resources for JSON endpoints, plus whatever versioning the application
already uses. Laravel 13 also ships first-party JSON:API resources when that is the contract you
have to satisfy.

Deciding the resource shape, URI structure, status-code policy, pagination style and error schema
is contract design, not framework work.

Serialize models for JavaScript with `{{ Js::from($article) }}`; in Laravel 13 it emits unescaped
Unicode by default, which changes snapshot expectations that pinned `\u00e8`-style escapes.

## Error handling

Pick one place per exception type and stay consistent with the project: `report()` / `render()`
methods on the exception class, or `report()` / `render()` callbacks in `bootstrap/app.php`'s
`withExceptions()`. The semantics differ and this trips people:

- An exception's `report()` method **suppresses** the default reporting unless it returns `false`.
- A `report()` callback **allows** default reporting unless it returns `false` or is chained with
  `stop()`.
- Returning `false` from a `render()` method or callback defers to Laravel's default rendering.

Mark exceptions the handler should never report with the `ShouldntReport` interface (or
`dontReport()`), throttle a noisy integration with `throttle()` and a `Limit`/`Lottery`, and attach
structured data with a `context()` method so it lands in the log record.

If the API contract requires JSON regardless of the `Accept` header, say so explicitly rather than
relying on content negotiation:

```php
$exceptions->shouldRenderJsonWhen(fn (Request $request, Throwable $e) => $request->is('api/*') || $request->expectsJson());
```

## Uploads

`mimes:jpg,png` inspects file contents and guesses a type; `extensions` checks the client-supplied
extension and is worthless alone. Validate content type, size and dimensions, let Laravel generate
the stored filename (`$request->file('avatar')->store('avatars')`), and keep untrusted files out of
any directory the web server will execute. Publicly served uploads usually also want re-encoding
and a content-disposition header.

## Outbound HTTP

Set both timeouts — the client defaults to a 30-second response timeout and no meaningful ceiling
once retries multiply it:

```php
Http::connectTimeout(3)->timeout(5)->get($url)->throw()->json();
```

The client returns 4xx/5xx responses rather than throwing, so a bare `->json()` silently parses an
error body. Call `->throw()` or check the status.

Retry only what is safe to repeat: idempotent verbs, or a state-changing request the remote API
protects with an idempotency key you send identically on every attempt. Share configuration with
`Http::macro()`, and run independent calls through `Http::pool()`.

<!-- sources: laravel-boost, laravel-docs -->
