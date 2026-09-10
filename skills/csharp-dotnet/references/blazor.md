# Blazor

Verified against: ASP.NET Core 10 (.NET 10).

## Contents

- [Render modes](#render-modes)
- [Choosing a render mode](#choosing-a-render-mode)
- [Prerendering](#prerendering)
- [Component contract](#component-contract)
- [Lifecycle](#lifecycle)
- [Rendering and StateHasChanged](#rendering-and-statehaschanged)
- [Disposal](#disposal)
- [JavaScript interop](#javascript-interop)
- [Forms](#forms)
- [Dependency injection in components](#dependency-injection-in-components)

## Render modes

In a Blazor Web App, every component adopts a render mode:

| Mode | Rendered | Interactive |
|---|---|---|
| Static Server (static SSR) | Server | No |
| Interactive Server | Server, over a circuit | Yes |
| Interactive WebAssembly | Client | Yes |
| Interactive Auto | Server first, then client once the bundle is cached | Yes |

A standalone Blazor WebAssembly app has no render modes at all — everything runs on the
client, and a `@rendermode` attribute there does nothing.

Apply a mode with `@rendermode` on a component instance (`<Dialog @rendermode="InteractiveServer" />`)
or on the component definition (`@rendermode InteractiveServer`). The directive on a
definition needs a static render-mode instance; the attribute on an instance accepts any.
Setting it on `<Routes>` (and `<HeadOutlet>`) in `App.razor` makes the whole app interactive;
the router propagates its mode to the pages it renders.

The `Program` file must enable the modes the app uses:
`AddRazorComponents().AddInteractiveServerComponents()` plus
`MapRazorComponents<App>().AddInteractiveServerRenderMode()`, and the WebAssembly equivalents.
Interactive WebAssembly components must live in the client project to be included in the
downloaded bundle.

A root component (`App`) cannot be interactive. Components should not assume a mode: write
them to work under any, and degrade gracefully when rendered statically.

At runtime, `RendererInfo.Name` (`Static`, `Server`, `WebAssembly`, `WebView`),
`RendererInfo.IsInteractive` and `AssignedRenderMode` tell a component where it is executing
(.NET 9+). Use them to skip work that only makes sense once interactive, not to fork the
component's design.

## Choosing a render mode

- Content pages, forms that post back, anything that must work without a runtime download:
  static SSR.
- Low-latency internal apps, or anything needing server-only resources per keystroke:
  Interactive Server. Costs a persistent circuit per user and holds per-circuit state in
  server memory.
- Offline-capable or high-scale public apps: Interactive WebAssembly. Costs an initial
  download and means every service the component calls must be reachable from the browser.
- Auto when you want the server's first-visit latency and the client's subsequent
  independence — at the cost of writing components that must work in both, so no server-only
  service injection.

## Prerendering

Prerendering is **on by default** for every interactive render mode. The server renders static
HTML first, then the interactive runtime attaches and renders again. Consequences:

- `OnInitializedAsync` runs **twice** — once prerendering, once when interactivity attaches.
  Naively fetching there means two API/database calls and a visible flicker.
- `OnAfterRenderAsync` does **not** run during prerender.
- Internal navigation between interactive pages skips prerendering; only full page loads
  prerender.
- There is no `JSRuntime`, no browser storage and no `HttpContext`-free client state during
  prerender. Calling JS interop from `OnInitializedAsync` throws.

The fix is to persist the prerendered state instead of refetching:

```razor
@code {
    [PersistentState]
    public WeatherForecast[]? Forecasts { get; set; }

    protected override async Task OnInitializedAsync()
        => Forecasts ??= await ForecastService.GetForecastsAsync();
}
```

The `??=` is the whole mechanism: fetch only if the property was not restored. For several
instances of the same component, add `@key` so their state is distinguishable. Only drop to
the imperative `PersistentComponentState` API (`RegisterOnPersisting` +
`TryTakeFromJson`) when you need dynamic keys or custom serialisation.

Disabling prerendering (`@rendermode="new InteractiveServerRenderMode(prerender: false)"`) is
a legitimate escape hatch for a component that fundamentally cannot render without the
browser, but it costs the first-paint benefit for everyone.

## Component contract

- Data flows down through `[Parameter]`; events flow up through `EventCallback<T>`. Never use
  `Action`/`Func` for a component event — `EventCallback` marshals to the right dispatcher and
  triggers a re-render automatically.
- `[Parameter]` properties must be public with a public setter. `required` and `init` on a
  parameter cause BL0007 and fail at runtime. Use `[EditorRequired]` to get a compile-time
  warning instead.
- Never mutate a `[Parameter]` property. Copy it into a private field in `OnParametersSet` and
  work with that; the framework reassigns the parameter on every render.
- Take `IReadOnlyList<T>` rather than `IEnumerable<T>` for collection parameters, so the
  component cannot accidentally enumerate a query twice.
- Give repeated elements `@key` (a stable id, not the index). Without it, an insert or removal
  makes the diff rebuild elements and lose their state.
- Handle all four states explicitly — loading, empty, loaded, error. A component that renders
  nothing while `null` is indistinguishable from a broken one.
- Keep logic under about 50 lines in an `@code` block; beyond that use a
  `.razor.cs` partial class.

## Lifecycle

| Hook | Runs |
|---|---|
| `SetParametersAsync` | Before parameters are assigned; rarely overridden |
| `OnInitialized`/`OnInitializedAsync` | Once per component instance — twice in total when prerendering |
| `OnParametersSet`/`OnParametersSetAsync` | After every parameter change, including the first |
| `OnAfterRender`/`OnAfterRenderAsync` | After each render; never during prerender; `firstRender` distinguishes the first |
| `ShouldRender` | Before each re-render after the first |

JS interop belongs in `OnAfterRenderAsync` (guarded by `firstRender` for one-time setup),
never in `OnInitializedAsync`.

## Rendering and StateHasChanged

- Blazor re-renders automatically after a lifecycle method, after an `EventCallback`, and
  after an `await` inside an event handler completes. Explicit `StateHasChanged` is only
  needed when state changes outside those paths — a timer, a subscription, an external event.
- From a non-UI thread (a `System.Threading.Timer` callback, an event raised by a background
  service), you must marshal:
  `await InvokeAsync(() => { _value = x; StateHasChanged(); });`.
- Handle external `Action`-shaped events with an `async void` handler that awaits
  `InvokeAsync`, and route failures to `DispatchExceptionAsync` so the error boundary sees
  them. `_ = InvokeAsync(...)` swallows the exception.
- `ShouldRender` returning `false` is an optimisation for a component proven to re-render too
  often, not a default.
- Debounce with `Task.Delay` plus a `CancellationTokenSource` you cancel and replace, not with
  a timer.

## Disposal

Implement `IAsyncDisposable` (not `IDisposable`) when a component owns subscriptions, timers,
`CancellationTokenSource`s or `IJSObjectReference`s. In `DisposeAsync`: unsubscribe, cancel
and dispose the CTS, dispose JS references. Never call `StateHasChanged` from disposal.

Do not catch `ObjectDisposedException` to paper over a race — cancel the token instead, so the
work stops before the object goes away. On Interactive Server, a disconnected circuit disposes
components; JS interop after that throws, which is expected.

## JavaScript interop

- Put component JavaScript in a collocated `Component.razor.js` module and load it lazily:
  `await JS.InvokeAsync<IJSObjectReference>("import", "./Components/Thing.razor.js")` in
  `OnAfterRenderAsync(firstRender: true)`.
- Store the `IJSObjectReference` and dispose it in `DisposeAsync`; each one holds a JS-side
  object.
- Call .NET from JS with `DotNetObjectReference.Create(this)` and `[JSInvokable]`; the
  reference is disposable and leaks the component if not disposed.
- `ElementReference` is valid only after the first render; passing one earlier gives a null
  element on the JS side.
- On Interactive Server every interop call is a round trip over the circuit. Batch them, and
  never put one in a per-item render loop.

## Forms

- `EditForm` with a model plus `DataAnnotationsValidator` and `ValidationSummary` covers the
  common case. Bind with `@bind-Value` on the input components, not raw `<input>`.
- Static SSR forms post back and need an `[SupplyParameterFromForm]` model plus the
  anti-forgery token that the template already wires up.
- Validate on the server regardless of what the client did. Client validation is a UX feature.

## Dependency injection in components

- `@inject` (or `[Inject]`) resolves per component instance.
- On Interactive Server, a *scope* is the circuit, not a request — a scoped service lives as
  long as the user's connection. A scoped `DbContext` in a component is therefore long-lived
  and shared across every interaction: use `IDbContextFactory<T>` and one context per
  operation.
- On Interactive WebAssembly there is effectively one scope for the whole app, so scoped and
  singleton behave the same. A component written for Auto must not depend on either
  distinction, and must not inject a service that only exists on the server.

<!-- sources: dotnet-official, aspnetcore-docs, awesome-copilot -->
