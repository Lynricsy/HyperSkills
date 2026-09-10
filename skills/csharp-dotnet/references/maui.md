# .NET MAUI

Verified against: .NET MAUI 10 (.NET 10).

## Contents

- [App lifecycle](#app-lifecycle)
- [Dependency injection](#dependency-injection)
- [Compiled bindings](#compiled-bindings)
- [MVVM plumbing](#mvvm-plumbing)
- [Shell navigation](#shell-navigation)
- [CollectionView](#collectionview)
- [Platform-specific code](#platform-specific-code)
- [Performance](#performance)

## App lifecycle

Four states: Not Running, Running, Deactivated (visible but unfocused — a dialog, split
screen, the notification shade), Stopped (backgrounded, not visible).

`Microsoft.Maui.Controls.Window` raises six cross-platform events: `Created`, `Activated`,
`Deactivated`, `Stopped`, `Resumed`, `Destroying`. Subscribe by overriding `CreateWindow` in
`App`.

Placement rules that matter:

- Persist anything the user would hate to lose on `Stopped`, not on `Destroying` — a
  backgrounded app can be killed without further notice.
- Refresh volatile data on `Resumed`, not on `Activated`: `Activated` fires for a transient
  focus change and refreshing there hammers the network.
- `Deactivated` means "lost focus", not "backgrounded". Pausing playback there is usually
  wrong.
- Platform-native hooks (`OnCreate`, `WillEnterForeground`, …) go through
  `ConfigureLifecycleEvents` in `MauiProgram`; use them only for something the cross-platform
  events do not surface.
- Multi-window (iPad, Mac Catalyst, Windows) means these events fire per window. State keyed
  to "the app" is wrong there.

## Dependency injection

Same `Microsoft.Extensions.DependencyInjection` container as ASP.NET Core, configured in
`MauiProgram.CreateMauiApp()` and immutable afterwards.

- Pages and ViewModels: `AddTransient`. A fresh instance per navigation avoids stale state,
  and a singleton page cannot be re-added to the visual tree once removed.
- Shared, expensive or genuinely app-wide state: `AddSingleton`.
- `AddScoped` rarely means what you want. MAUI has no request scope; it creates one scope per
  window, and resolving from the root provider makes a scoped service behave like a singleton.
  For unit-of-work semantics create the scope explicitly with `IServiceScopeFactory`, or use
  `AddDbContextFactory`.
- Register the page *and* its ViewModel, then `Routing.RegisterRoute`, so
  `Shell.Current.GoToAsync` resolves the page through DI and injects its dependencies.
- Platform-specific implementations registered under `#if` must cover **every** target
  platform or have a fallback; a missing branch is an unregistered service that throws only on
  that platform, at resolution time.

## Compiled bindings

Reflection-based bindings are slow and are not trim/AOT-safe. `x:DataType` turns a binding
into generated code.

- Put `x:DataType` where a binding scope starts: the page or view root where `BindingContext`
  is assigned, and **each** `DataTemplate`. Do not scatter it on arbitrary children.
- A `DataTemplate` needs its own `x:DataType`; inheriting one from an outer scope resolves
  against the wrong type (XC0024).
- `x:DataType="x:Object"` to silence a warning is an anti-pattern — it disables the
  compile-time check and restores reflection.
- To enforce it, set `MauiEnableXamlCBindingWithSourceCompilation` to `true` first, then
  `<WarningsAsErrors>XC0022;XC0025</WarningsAsErrors>`. Promoting XC0025 without that switch
  breaks projects using `Source=`/`RelativeSource` bindings.
- For code-behind bindings on .NET 9+, the `SetBinding` lambda overload is the AOT-safe form.

## MVVM plumbing

- The ViewModel must raise change notification or nothing updates. Use the
  CommunityToolkit.Mvvm source generators (`ObservableObject` with `[ObservableProperty]` and
  `[RelayCommand]`) rather than hand-written `INotifyPropertyChanged` boilerplate — the
  generator also produces AOT-safe code.
- A binding that renders blank is far more often an unset or wrong `BindingContext` than a
  wrong path. Check the context first.
- Value converters are for presentation only; anything with a decision in it belongs in the
  ViewModel as a property.
- `BindingMode`: `OneWay` is the default for most properties and `TwoWay` for input controls.
  Setting `TwoWay` on a display-only binding costs a change handler for nothing.

## Shell navigation

- `AppShell` defines the visual hierarchy — `FlyoutItem`, `TabBar`, `Tab`, `ShellContent`.
  Pages reachable only by navigation are registered with `Routing.RegisterRoute`.
- Navigate with URI-shaped routes: `GoToAsync("orders/detail?id=42")`. `//` resets to an
  absolute route, `..` goes back, and `../..` goes back twice — mixing these up is the usual
  cause of a broken back stack.
- Receive parameters with `[QueryProperty]` or `IQueryAttributable`. Pass an id, not an
  object graph; a complex object in a query string does not survive a process restart.
- Guard navigation in `OnNavigating` (`ShellNavigatingEventArgs.Cancel()`); an `async`
  confirmation needs `GetDeferral()`/`Complete()`, otherwise navigation continues while the
  dialog is still open.

## CollectionView

`CollectionView` replaces `ListView`; do not carry `ListView` habits into it.

- Never use `ViewCell` as a `DataTemplate` root — that is a `ListView` construct and it
  breaks virtualisation here.
- Bind to `ObservableCollection<T>` whenever the list changes after first render; a plain
  `List<T>` never notifies.
- Mutate the bound collection on the UI thread only. Background mutation produces an
  intermittent crash in the layout pass, not an exception you can catch at the call site.
- Give the `DataTemplate` its own `x:DataType`.
- `EmptyView` for the no-data state, `RemainingItemsThreshold` plus
  `RemainingItemsThresholdReachedCommand` for incremental loading, `SwipeView` for row
  actions.
- Keep item templates shallow. Nested layouts multiply per item, and the deepest measurable
  cost in a MAUI list is item template complexity.

## Platform-specific code

- Prefer the cross-platform API (`Microsoft.Maui.Devices`, `Microsoft.Maui.Storage`,
  `Microsoft.Maui.ApplicationModel`) before writing anything platform-specific.
- Beyond that, use partial classes under `Platforms/<Platform>/` — the SDK includes them per
  target automatically. `#if ANDROID` inside a shared file is for a few lines, not for a
  whole implementation.
- Customise controls with handler mappers
  (`Microsoft.Maui.Handlers.EntryHandler.Mapper.AppendToMapping(...)`), not by replacing the
  handler.

## Performance

- Judge on a Release build on a real device. Debug builds on Android carry an interpreter and
  produce numbers that mean nothing.
- Android release builds should have AOT and the linker configured; check `PublishTrimmed`
  and `RunAOTCompilation` before investigating anything else about startup.
- The recurring costs are: deep visual trees, reflection bindings, images decoded at full
  resolution, and work in a page constructor or `OnAppearing` that should be async and
  deferred.
- Compiled bindings and trimming go together: an app that is not trim-clean will fail at
  runtime with missing members only in the release configuration.

<!-- sources: dotnet-official, awesome-copilot -->
