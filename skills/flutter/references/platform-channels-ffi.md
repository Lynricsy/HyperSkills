# Platform channels, Pigeon and FFI

## Contents

- [Which mechanism](#which-mechanism)
- [MethodChannel](#methodchannel)
- [EventChannel](#eventchannel)
- [Codec and type mapping](#codec-and-type-mapping)
- [Threading](#threading)
- [Pigeon](#pigeon)
- [FFI with ffigen](#ffi-with-ffigen)
- [Testing the Dart side](#testing-the-dart-side)
- [Failure catalogue](#failure-catalogue)

## Which mechanism

| Need | Use |
|---|---|
| A few calls into platform SDK code (Kotlin/Swift/C++) | `MethodChannel` |
| A continuous stream from the platform (sensors, connectivity) | `EventChannel` |
| More than a handful of calls, or structured payloads | `pigeon` (generates typed channel code both sides) |
| A C / Objective-C / Swift **library**, no platform SDK involved | `dart:ffi` with `ffigen` |
| Existing pub package covers it | the package — do not re-implement a plugin |

Platform channels are asynchronous by construction; every call crosses an
isolate-safe message boundary, so a chatty per-frame API will cost more than the
work it does.

## MethodChannel

Dart side:

```dart
import 'package:flutter/services.dart';

class Battery {
  // Prefix with a domain you own so the name cannot collide with a plugin.
  static const _channel = MethodChannel('samples.example.com/battery');

  Future<int> level() async {
    try {
      return await _channel.invokeMethod<int>('getBatteryLevel') ?? -1;
    } on PlatformException catch (e) {
      throw BatteryException(e.code, e.message);
    } on MissingPluginException {
      throw BatteryException('unimplemented', 'No handler on this platform');
    }
  }
}
```

Android (`MainActivity.kt`), inside `configureFlutterEngine`:

```kotlin
MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL)
    .setMethodCallHandler { call, result ->
        when (call.method) {
            "getBatteryLevel" -> {
                val level = getBatteryLevel()
                if (level != -1) result.success(level)
                else result.error("UNAVAILABLE", "Battery level not available", null)
            }
            else -> result.notImplemented()
        }
    }
```

iOS (`AppDelegate.swift`):

```swift
let channel = FlutterMethodChannel(name: "samples.example.com/battery",
                                   binaryMessenger: controller.binaryMessenger)
channel.setMethodCallHandler { call, result in
  guard call.method == "getBatteryLevel" else { return result(FlutterMethodNotImplemented) }
  result(self.batteryLevel())          // or FlutterError(code:message:details:)
}
```

Rules:

- The channel name is a contract between two languages: define it once per side
  as a constant, and keep the method names in one place.
- Call `result.success` / `result.error` / `result.notImplemented` **exactly
  once** per invocation; a missing reply leaves the Dart future pending forever.
- `notImplemented()` on the platform surfaces as `MissingPluginException` in
  Dart — handle it, because a platform you did not implement (web, desktop) hits
  it at runtime.
- Errors cross as `PlatformException(code, message, details)`; use stable codes,
  not localised prose.
- A `MissingPluginException` right after a hot restart usually means the plugin
  registered before the restart; do a full stop/run before debugging further.

## EventChannel

```dart
static const _events = EventChannel('samples.example.com/charging');
Stream<ChargingStatus> get charging =>
    _events.receiveBroadcastStream().map(ChargingStatus.parse);
```

The platform side registers a `StreamHandler`: `onListen` starts the source and
pushes with the event sink, `onCancel` tears it down. Every listener starts a new
subscription — share the stream with `broadcast` semantics and cancel it in
`dispose`/`onDispose`, or the native receiver leaks.

## Codec and type mapping

`StandardMessageCodec` carries `null`, `bool`, `int`, `double`, `String`,
`Uint8List`, `Int32List`, `Int64List`, `Float32List`, `Float64List`, `List`, `Map`.
Anything else must be flattened by hand.

| Dart | Kotlin | Swift |
|---|---|---|
| `int` (≤32 bits) | `Int` | `NSNumber(value: Int32)` |
| `int` (>32 bits) | `Long` | `NSNumber(value: Int)` |
| `double` | `Double` | `NSNumber(value: Double)` |
| `Uint8List` | `ByteArray` | `FlutterStandardTypedData(bytes:)` |
| `List` | `List` | `Array` |
| `Map` | `HashMap` | `Dictionary` |

Send bulk binary as a typed list (`Uint8List`), not as a `List<int>`: the typed
list is copied as a block, the generic list element by element.

## Threading

- Platform handlers run on the platform main thread (Android UI thread, iOS main
  thread) unless the channel was created with a background `TaskQueue`
  (`messenger.makeBackgroundTaskQueue()`), so long work in a handler freezes the
  UI — hop to a background executor and post the result back.
- Calls **into** Flutter must be made on the platform main thread
  (`runOnUiThread` / `DispatchQueue.main.async`).
- From a Dart background isolate, initialise the messenger first:

```dart
final token = RootIsolateToken.instance!;
await Isolate.run(() {
  BackgroundIsolateBinaryMessenger.ensureInitialized(token);
  // plugin calls are legal from here on
});
```

## Pigeon

Define the protocol in a Dart file (not shipped in the app), generate both sides:

```dart
// pigeons/messages.dart
import 'package:pigeon/pigeon.dart';

class SearchRequest {
  SearchRequest({required this.query});
  final String query;
}

@HostApi()
abstract class SearchApi {
  @async
  SearchReply search(SearchRequest request);
}
```

```bash
dart run pigeon --input pigeons/messages.dart
```

Generated Dart calls a generated Kotlin/Swift interface you implement. This
removes the two things that break hand-written channels: stringly-typed method
names and hand-rolled map serialisation. `@FlutterApi()` generates the reverse
direction (platform calling Dart).

## FFI with ffigen

For linking a C-style library directly, do not hand-write bindings — generate
them.

```bash
dart pub add dev:ffigen
dart run tool/ffigen.dart          # a script that configures FfiGenerator
dart analyze
```

- Headers live in `third_party/` (vendored) or `src/`; generated bindings in
  `lib/src/third_party/<lib>.g.dart`.
- Filter aggressively (include only the functions/structs you call) — generating
  a whole system header produces thousands of lines nobody reads.
- Put the upstream copyright plus a "generated, do not edit" note in the
  generator's `preamble`, and add analyzer ignores there rather than to the
  project's `analysis_options.yaml`.
- Never edit a generated binding by hand; regenerate and re-run `dart analyze`
  before committing.
- FFI calls are synchronous and run on the calling isolate: anything slow blocks
  that isolate, so call heavy natives from `Isolate.run`. Memory allocated with
  `calloc` must be freed; wrap it in `using((arena) { ... })` from
  `package:ffi`.
- Native assets / build hooks (`hook/build.dart`) are how a package ships the
  compiled library with the app instead of requiring a manual install step.

## Testing the Dart side

```dart
TestWidgetsFlutterBinding.ensureInitialized();

TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
    .setMockMethodCallHandler(
  const MethodChannel('samples.example.com/battery'),
  (call) async => call.method == 'getBatteryLevel' ? 42 : null,
);
```

This covers everything on the Dart side of the boundary: argument encoding,
error mapping, stream transformation. The native half needs an integration test
on a device.

## Failure catalogue

| Symptom | Cause |
|---|---|
| Future never completes | handler returned without calling `result` |
| `MissingPluginException` | no handler for this platform, or stale registration after hot restart |
| Works on Android, crashes on iOS | int width mismatch (32 vs 64 bit) or a type outside the standard codec |
| UI freezes during a channel call | heavy work on the platform main thread |
| `Unhandled Exception: PlatformException(error, null, null)` | platform threw without a code/message; always fill both |
| Plugin call throws in an isolate | missing `BackgroundIsolateBinaryMessenger.ensureInitialized` |
| Generated FFI bindings do not compile | stale generation, or headers moved; re-run the generator |

<!-- sources: flutter-docs, dart-official -->
