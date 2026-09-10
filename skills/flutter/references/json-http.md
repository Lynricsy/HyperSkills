# JSON and HTTP

## Contents

- [Models: hand-written or generated](#models-hand-written-or-generated)
- [Parsing defensively](#parsing-defensively)
- [The http client](#the-http-client)
- [Errors are exceptions, never null](#errors-are-exceptions-never-null)
- [Large payloads](#large-payloads)
- [Platform configuration](#platform-configuration)
- [Testing network code](#testing-network-code)
- [Failure catalogue](#failure-catalogue)

## Models: hand-written or generated

Hand-written is fine for a handful of models; generate once the app has more than
a few, or once nullability rules get subtle.

```dart
class User {
  const User({required this.id, required this.name, this.email});

  final int id;
  final String name;
  final String? email;

  factory User.fromJson(Map<String, dynamic> json) => switch (json) {
        {'id': final int id, 'name': final String name} => User(
            id: id,
            name: name,
            email: json['email'] as String?,
          ),
        _ => throw FormatException('Unexpected user payload: $json'),
      };

  Map<String, dynamic> toJson() => {'id': id, 'name': name, 'email': email};
}
```

With `json_serializable`: annotate `@JsonSerializable()`, add
`part 'user.g.dart';`, and run
`dart run build_runner build --delete-conflicting-outputs`. Use
`@JsonKey(name: 'user_name')` for snake_case APIs rather than renaming Dart
fields, or set `fieldRename: FieldRename.snake` once at the class level.
`freezed` adds immutability, `copyWith` and unions on top.

## Parsing defensively

- Cast the result of `jsonDecode` explicitly: `as Map<String, dynamic>` /
  `as List<dynamic>`. It returns `dynamic`, and `strict-casts` will not let the
  implicit version through.
- Map patterns validate shape and bind in one step (the `switch` above), which
  turns a wrong payload into a `FormatException` at the boundary instead of a
  `type 'Null' is not a subtype of 'String'` three layers up.
- Numbers arrive as `int` or `double` depending on the encoder: read them as
  `num` and call `.toDouble()`.
- Dates arrive as strings: `DateTime.parse(...)`, and store UTC.
- An empty body with status 204 is not JSON — check before decoding.

## The http client

```dart
class WeatherApi {
  WeatherApi({http.Client? client}) : _client = client ?? http.Client();
  final http.Client _client;

  Future<Weather> fetch(String city) async {
    final response = await _client
        .get(Uri.https('api.example.com', '/weather', {'city': city}),
             headers: {'Accept': 'application/json'})
        .timeout(const Duration(seconds: 10));

    if (response.statusCode != 200) {
      throw WeatherException(response.statusCode, response.body);
    }
    return Weather.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  void close() => _client.close();
}
```

- Build URLs with `Uri.https`/`Uri.parse`, never string concatenation — query
  values must be encoded.
- Inject the `http.Client` so tests can supply a fake; keep one client for the
  app rather than creating one per request (connection reuse), and close it on
  shutdown.
- Always set a timeout. Without one, a hung socket becomes a spinner that never
  stops.
- Use `response.bodyBytes` with an explicit `utf8.decode` when the server does
  not declare a charset; `response.body` assumes latin-1 in that case.
- `dio` is the usual alternative when interceptors, retries and cancellation are
  needed; do not add both.

## Errors are exceptions, never null

Returning `null` on failure makes `FutureBuilder` and `AsyncNotifier` treat the
failure as "no data yet" — an infinite spinner. Throw a typed exception at the
boundary and translate it into state in the notifier/bloc:

```dart
sealed class ApiFailure implements Exception {}
final class NetworkFailure extends ApiFailure {}      // SocketException, timeout
final class ServerFailure extends ApiFailure {        // 5xx
  ServerFailure(this.statusCode);
  final int statusCode;
}
final class ClientFailure extends ApiFailure {        // 4xx, includes auth
  ClientFailure(this.statusCode, this.message);
  final int statusCode;
  final String message;
}
```

Catch `SocketException`, `TimeoutException` and `FormatException` in the
repository and map them; let everything else escape — a bug should not be
disguised as a network error.

## Large payloads

```dart
List<Photo> parsePhotos(String body) => (jsonDecode(body) as List<dynamic>)
    .cast<Map<String, dynamic>>()
    .map(Photo.fromJson)
    .toList();

final photos = await compute(parsePhotos, response.body);
```

Anything above roughly a few hundred kilobytes, or any parse over ~8 ms, belongs
in an isolate. The function must be top-level or static; closures cannot cross
the isolate boundary.

## Platform configuration

- Android: `<uses-permission android:name="android.permission.INTERNET" />` in
  `android/app/src/main/AndroidManifest.xml` (present in the template).
- macOS: `com.apple.security.network.client` in **both**
  `macos/Runner/DebugProfile.entitlements` and `Release.entitlements`. Missing
  the release one is the classic "works in debug only".
- Cleartext HTTP is blocked by default on both platforms; use HTTPS rather than
  opting out.

## Testing network code

```dart
import 'package:http/testing.dart';

final client = MockClient((request) async {
  expect(request.url.queryParameters['city'], 'Berlin');
  return http.Response('{"city":"Berlin","celsius":21}', 200);
});
```

`MockClient` from `package:http/testing.dart` needs no mocking library and keeps
the assertion about the request in one place. Use a `mocktail` mock instead when
the test must `verify` call counts or stub several methods of a wider API.
Test the failure paths explicitly: non-200, malformed body, timeout.

## Failure catalogue

| Symptom | Cause |
|---|---|
| Infinite spinner | error path returns `null` instead of throwing |
| `type 'Null' is not a subtype of type 'String'` | missing field; validate in `fromJson` |
| Garbled non-ASCII text | `response.body` used without utf8 decoding |
| Frame drop while loading a list | parsing on the UI isolate; use `compute` |
| Works on Android, fails on macOS release | missing network entitlement in `Release.entitlements` |
| Requests hang forever | no `.timeout(...)` on the call |
| Generated model missing new field | `build_runner` not re-run |

<!-- sources: flutter-official, evanca-rules, dart-official -->
