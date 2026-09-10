# Navigation: go_router, deep links, auto_route

Verified against: go_router 14.x–16.x.

## Contents

- [Router setup](#router-setup)
- [Typed routes](#typed-routes)
- [Passing data](#passing-data)
- [Tabs and shells](#tabs-and-shells)
- [Auth redirects](#auth-redirects)
- [Platform deep links: Android](#platform-deep-links-android)
- [Platform deep links: iOS](#platform-deep-links-ios)
- [Verifying a deep link](#verifying-a-deep-link)
- [auto_route](#auto_route)
- [Testing routes](#testing-routes)
- [Failure catalogue](#failure-catalogue)

## Router setup

```dart
import 'package:flutter_web_plugins/url_strategy.dart';

void main() {
  usePathUrlStrategy();          // web only: drops the '#' from URLs
  runApp(const MyApp());
}

final router = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomeScreen(),
      routes: [
        GoRoute(                                   // nested: no leading slash
          path: 'order/:id',
          name: 'order',
          builder: (context, state) => OrderScreen(id: state.pathParameters['id']!),
        ),
      ],
    ),
  ],
  errorBuilder: (context, state) => NotFoundScreen(uri: state.uri),
);

MaterialApp.router(routerConfig: router);
```

- Build the router **once** — a top-level `final`, or a `late final` in a
  `State`. Constructing it inside `build` resets the navigation stack on every
  rebuild.
- Nest the detail route under its parent so a cold-start deep link produces a
  back stack (Home → Order) instead of an app that exits on the first back press.
- Always supply `errorBuilder`: external links arrive with paths you never
  defined.

## Typed routes

With `go_router_builder` (`dev_dependencies: go_router_builder, build_runner`):

```dart
part 'routes.g.dart';

@TypedGoRoute<HomeRoute>(path: '/', routes: [TypedGoRoute<OrderRoute>(path: 'order/:id')])
class HomeRoute extends GoRouteData with $HomeRoute {
  const HomeRoute();
  @override
  Widget build(BuildContext context, GoRouterState state) => const HomeScreen();
}

class OrderRoute extends GoRouteData with $OrderRoute {
  const OrderRoute({required this.id});
  final String id;
  @override
  Widget build(BuildContext context, GoRouterState state) => OrderScreen(id: id);
}
```

Navigate with `const OrderRoute(id: '42').go(context)` / `.push(context)`.
Regenerate with `dart run build_runner build --delete-conflicting-outputs`.
Prefer typed routes: a string path typed by hand in feature code is a runtime
404 waiting to happen.

## Passing data

| Need | Do |
|---|---|
| Identifier | path parameter `:id` |
| Optional filter, pagination | query parameter, read from `state.uri.queryParameters` |
| A whole entity | pass the id and load it in the notifier/bloc |
| Result from a pushed page | `final ok = await const EditRoute().push<bool>(context);` |

`extra` is not serialisable: it survives neither a cold-start deep link nor state
restoration, so anything reachable by URL must be reconstructible from the path
and query alone.

## Tabs and shells

```dart
StatefulShellRoute.indexedStack(
  builder: (context, state, shell) => ScaffoldWithNavBar(shell: shell),
  branches: [
    StatefulShellBranch(routes: [GoRoute(path: '/home', builder: ...)]),
    StatefulShellBranch(routes: [GoRoute(path: '/settings', builder: ...)]),
  ],
)
```

Each branch keeps its own navigation stack and state. Switch with
`shell.goBranch(index, initialLocation: index == shell.currentIndex)` so tapping
the active tab pops back to its root. `ShellRoute` (without `Stateful`) shares one
stack — use it only for a chrome that does not need per-tab history.

## Auth redirects

```dart
GoRouter(
  refreshListenable: sessionListenable,   // notify on sign-in/sign-out
  redirect: (context, state) {
    final signedIn = session.isSignedIn;
    final atLogin = state.matchedLocation == '/login';
    if (!signedIn && !atLogin) {
      return '/login?from=${Uri.encodeComponent(state.uri.toString())}';
    }
    if (signedIn && atLogin) {
      return state.uri.queryParameters['from'] ?? '/';
    }
    return null;
  },
);
```

- Without `refreshListenable` the redirect never re-runs after login and the user
  stays on `/login`.
- Carry the original location in `from`, or every deep link that hits the auth
  wall lands on the home screen.
- `redirect` reads only session state — never awaits, never touches a repository;
  it runs on every navigation.

## Platform deep links: Android

`android/app/src/main/AndroidManifest.xml`, inside the existing `<activity>` (add
a new filter; do not modify the MAIN/LAUNCHER one):

```xml
<meta-data android:name="flutter_deeplinking_enabled" android:value="true" />

<intent-filter android:autoVerify="true">
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="https" android:host="shop.example.com" android:pathPrefix="/order" />
</intent-filter>
```

Host `https://shop.example.com/.well-known/assetlinks.json`:

```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.example.shop",
    "sha256_cert_fingerprints": ["<upload key>", "<Play App Signing key>"]
  }
}]
```

- Serve it over HTTPS with `Content-Type: application/json` and **no redirect** —
  a 301 from `http` or from the apex domain fails verification silently.
- Include both fingerprints: local `./gradlew signingReport` and the Play App
  Signing SHA-256. Missing the second one is the classic "works in debug, opens
  the browser in production".
- Attributes inside one `<data>` element combine as written; splitting scheme and
  host into separate `<data>` elements widens the match to every combination.

## Platform deep links: iOS

1. Xcode → Runner target → Signing & Capabilities → Associated Domains →
   `applinks:shop.example.com`, which writes `ios/Runner/Runner.entitlements`:

   ```xml
   <key>com.apple.developer.associated-domains</key>
   <array><string>applinks:shop.example.com</string></array>
   ```

   Check that both Debug and Release configurations point `CODE_SIGN_ENTITLEMENTS`
   at that file.
2. `ios/Runner/Info.plist`: `<key>FlutterDeepLinkingEnabled</key><true/>`. Set it
   to `false` only when a plugin such as `app_links` owns link handling instead.
3. Host `https://shop.example.com/.well-known/apple-app-site-association`
   (no file extension, `application/json`, no redirect):

   ```json
   {"applinks": {"details": [{
     "appIDs": ["TEAMID.com.example.shop"],
     "components": [{"/": "/order/*"}]
   }]}}
   ```

Apple caches the file through its CDN, so changes can take up to a day; during
development append `?mode=developer` to the entitlement and enable Associated
Domains Development in the device's developer settings.

## Verifying a deep link

```bash
# server side first — cheapest failure to find
curl -sIL https://shop.example.com/.well-known/assetlinks.json
curl -sIL https://shop.example.com/.well-known/apple-app-site-association

# Android: verification state, then a real click
adb shell pm get-app-links com.example.shop
adb shell am start -a android.intent.action.VIEW -d "https://shop.example.com/order/42"

# iOS simulator
xcrun simctl openurl booted "https://shop.example.com/order/42"
```

On Android 12+ an unverified App Link opens the browser with no disambiguation
dialog. On iOS, typing the URL in Safari or tapping a link on the same domain
does not open the app — test from Notes or Messages.

## auto_route

Only when the project already depends on it — do not mix routers.

```dart
@AutoRouterConfig()
class AppRouter extends RootStackRouter {
  @override
  List<AutoRoute> get routes => [
        AutoRoute(page: HomeRoute.page, initial: true),
        AutoRoute(page: OrderRoute.page, path: '/order/:id'),
      ];
}
```

Pages are annotated `@RoutePage()`; navigation is `context.router.push(OrderRoute(id: '42'))`.
Deep-link platform configuration is identical to go_router's — it is native, not
package, configuration.

## Testing routes

```dart
testWidgets('signed-out user is redirected to /login', (tester) async {
  final router = createRouter(FakeSession(signedIn: false));
  await tester.pumpWidget(MaterialApp.router(routerConfig: router));
  await tester.pumpAndSettle();
  expect(router.routerDelegate.currentConfiguration.uri.path, '/login');
});
```

Drive deep links in tests with `router.go('/order/42')` and assert the rendered
screen; that covers the Dart half. The native half needs a device.

## Failure catalogue

| Symptom | Cause |
|---|---|
| Navigation resets on every rebuild | router constructed inside `build` |
| Redirect loop | redirect returns a location that itself redirects; always allow the target route |
| Stuck on `/login` after signing in | missing `refreshListenable` |
| Link opens the browser on Android | `assetlinks.json` redirected, wrong host, or missing Play signing fingerprint |
| Link opens the app on the home screen | deep-link path not nested/matched, or `from` not carried through login |
| Cold-start deep link loses state | data passed via `extra` |
| Back button exits immediately | detail route declared top-level instead of nested |

<!-- sources: flutter-official, sgruhier-flutter -->
