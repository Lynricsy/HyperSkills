# Navigation

Verified against: Navigation 2.8+ (type-safe routes) and Navigation 3 (`NavDisplay`,
`NavKey`).

## Contents

- [Which library](#which-library)
- [Type-safe Navigation 2](#type-safe-navigation-2)
- [Navigation 3](#navigation-3)
- [Passing data and returning results](#passing-data-and-returning-results)
- [Conditional navigation](#conditional-navigation)
- [Deep links](#deep-links)
- [Back handling](#back-handling)
- [Migrating 2 → 3](#migrating-2--3)

## Which library

Follow whichever library the project already uses; running both is a guaranteed
double-back-stack bug. For a new Compose-only app, Navigation 3 gives you the back stack
as a plain list you own. For a project with Fragments, a large existing graph, or a
`NavHost` per feature module, staying on Navigation 2 with type-safe routes is the
cheaper correct answer.

## Type-safe Navigation 2

String routes are a runtime crash waiting for a typo. From Navigation 2.8, destinations
are `@Serializable` types (needs the `org.jetbrains.kotlin.plugin.serialization` plugin):

```kotlin
@Serializable object Home
@Serializable data class Profile(val userId: String)

NavHost(navController, startDestination = Home) {
    composable<Home> { HomeScreen(onOpenProfile = { navController.navigate(Profile(it)) }) }
    composable<Profile> { backStackEntry ->
        val route: Profile = backStackEntry.toRoute()
        ProfileScreen(route.userId)
    }
}
```

In a ViewModel, read the same route from `SavedStateHandle.toRoute<Profile>()` instead of
pulling string arguments out by key.

## Navigation 3

Navigation 3 removes the graph: the back stack is a list you own, and a `NavDisplay`
renders it.

```kotlin
@Serializable data object Home : NavKey
@Serializable data class Profile(val userId: String) : NavKey

val backStack = rememberNavBackStack(Home)

NavDisplay(
    backStack = backStack,
    onBack = { backStack.removeLastOrNull() },
    entryProvider = entryProvider {
        entry<Home> { HomeScreen(onOpen = { backStack.add(Profile(it)) }) }
        entry<Profile> { key -> ProfileScreen(key.userId) }
    },
)
```

Consequences of "the back stack is just a list":

- Navigating is `backStack.add(key)`; popping is `removeLastOrNull()`; a multi-step
  synthetic stack is `backStack.addAll(...)`. There is no `popUpTo` DSL to learn — and no
  DSL to protect you either, so guard against double navigation from a fast double-tap
  with `dropUnlessResumed { }`.
- Use `rememberNavBackStack` (not a bare `mutableStateListOf`) so the stack is saved and
  restored across configuration change and process death; keys must be `@Serializable`
  and implement `NavKey`.
- Each entry gets its own scope, so a `ViewModel` scoped to an entry is retained while the
  entry stays on the stack.
- Multiple back stacks (bottom-bar tabs) are multiple lists plus a selector, not a
  framework feature.
- Adaptive layouts are **scene strategies**: a scene can read more than one entry from the
  back stack and render them side by side (list-detail, supporting pane, two-pane),
  collapsing back to one on a compact window.
- Dialogs and bottom sheets are entry metadata, not separate destination kinds.

## Passing data and returning results

Pass identifiers, not objects. A route is serialized into saved state, so it must stay
small and stable; the screen loads the entity from its repository using the id.

Return a result by lifting the shared state above both screens — a repository, a shared
`ViewModel`, or (Navigation 3) state held next to the back stack. Writing into the
previous entry's saved state handle works but couples the two screens and breaks when the
caller is not where you expected.

## Conditional navigation

Model auth and onboarding as *state that selects the back stack*, not as a redirect
sprinkled through destinations:

```kotlin
val backStack = if (isLoggedIn) mainBackStack else authBackStack
```

Redirect-on-entry logic (checking a flag inside every destination) produces flicker, a
polluted back stack and race conditions when the flag flips mid-navigation.

## Deep links

Declare the filter in the manifest and verify the domain:

```xml
<intent-filter android:autoVerify="true">
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="https" android:host="shop.example.com" />
</intent-filter>
```

App Links additionally need `/.well-known/assetlinks.json` on the domain, carrying the
SHA-256 fingerprint of every signing key you ship with — including the Play App Signing
key, which is the fingerprint people forget.

On the Compose side, Navigation 2 attaches `deepLinks = listOf(navDeepLink<Profile>(...))`
to the destination; Navigation 3 matches the incoming `Uri` yourself and pushes the
resulting keys, which is also how you build a synthetic back stack so the user can go
"up" into a screen they never visited.

Test with an explicit intent rather than by tapping a link:

```bash
adb shell am start -a android.intent.action.VIEW -d "https://shop.example.com/order/42"
```

Deep link data is attacker-controlled: validate the host, path and every parameter before
acting on it, and never forward it into another component unchecked.

## Back handling

- Predictive back is on by default from Android 16 for apps targeting SDK 36; opt in
  earlier with `android:enableOnBackInvokedCallback="true"`.
- Intercept with `BackHandler`/`PredictiveBackHandler` in Compose and disable the handler
  when it should not apply, rather than conditionally ignoring the callback — a
  permanently enabled handler that does nothing breaks the predictive-back animation.
- Never call `finish()` to go back; let the navigation system pop.

## Migrating 2 → 3

Migrate per module and keep both running side by side through the transition:

1. Convert string routes to `@Serializable` types under Navigation 2 first. This is
   valuable on its own and is the bulk of the work.
2. Make each route implement `NavKey`.
3. Replace the `NavHost` graph with a back stack list plus an `entryProvider`.
4. Move `popUpTo`/`launchSingleTop` behaviour into explicit list manipulation and write a
   test for each, because the framework no longer enforces them.
5. Re-implement adaptive destinations as scenes.
6. Re-test back handling, deep links and multi-backstack behaviour; these are where the
   semantics actually differ.

<!-- sources: android-official, aldefy-compose, silvermoon-android, android-docs -->
