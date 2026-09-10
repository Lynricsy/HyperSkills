# Architecture and the native boundary

Verified against: React Native 0.87, Expo SDK 54–57.

## Contents

- [What the New Architecture actually changed](#what-the-new-architecture-actually-changed)
- [Version floors for architecture facts](#version-floors-for-architecture-facts)
- [The interop layer and its two holes](#the-interop-layer-and-its-two-holes)
- [Turbo Native Module: the spec is the contract](#turbo-native-module-the-spec-is-the-contract)
- [Wiring codegen](#wiring-codegen)
- [Registry lookup: getEnforcing vs get](#registry-lookup-getenforcing-vs-get)
- [Threads and what may be synchronous](#threads-and-what-may-be-synchronous)
- [Fabric native components](#fabric-native-components)
- [Expo modules: when to prefer them](#expo-modules-when-to-prefer-them)
- [Old patterns](#old-patterns)

## What the New Architecture actually changed

Three pieces, and they explain most of the constraints elsewhere in this skill:

- **JSI** replaces the asynchronous, JSON-serializing bridge. JavaScript holds a
  reference to a C++ object and calls it directly, so a large payload (camera
  frame, database handle, audio buffer) crosses without serialization. This is
  why a synchronous native call is now *possible* — and why it is dangerous
  (it runs on the caller's thread).
- **Fabric** is the renderer: the shadow tree lives in C++, layout comes from
  Yoga, and mounting is scheduled against React's concurrent renderer. Layout
  information can be read and acted on inside a single commit, so a synchronous
  layout effect no longer shows an intermediate frame the way an `onLayout` →
  `setState` round trip does.
- **Turbo Native Modules** are lazily initialized and typed from a generated
  interface, so a module that is never called is never constructed. [official]

Enabling it does not by itself make an app faster. It removes a class of
serialization cost and unlocks concurrent React and synchronous measurement; the
wins come from code that uses them.

## Version floors for architecture facts

| Fact | Floor |
|---|---|
| New Architecture enabled by default | React Native 0.76 |
| New Architecture is the only runtime (no opt-out) | React Native 0.82 |
| Legacy Architecture code compiled out of iOS builds by default | React Native 0.84 |
| Hermes V1 is the default engine | React Native 0.84 |
| Precompiled React Native iOS binaries by default | React Native 0.84 |
| Strict TypeScript API is the default | React Native 0.87 |
| New Architecture default in Expo | SDK 53 |

Anything written for the opt-in era ("flip `newArchEnabled`", "check whether the
app is on the New Architecture before recommending X") is describing a decision
that no longer exists on a supported release.

## The interop layer and its two holes

Legacy native modules and legacy view managers keep working on the New
Architecture through the interop layer, which survives even on releases that
compile the legacy runtime out. Migration is therefore a quality move — codegen
type safety, lazy init, no reflection — not a rescue.

The two things interop does not give a legacy component:

- access to a custom Shadow Node, so anything that needs custom C++ layout must
  become a real Fabric component;
- concurrent-safe behaviour, so a legacy view under a `startTransition` or
  Suspense boundary is not guaranteed to behave.

A legacy module that only exposes methods and events has no such hole; the
pressure to migrate it is smaller than the ecosystem's tone suggests. Judge by
what the module does, not by its age.

## Turbo Native Module: the spec is the contract

```ts
// specs/NativeDeviceInfo.ts
import type {TurboModule} from 'react-native';
import {TurboModuleRegistry} from 'react-native';

export interface Spec extends TurboModule {
  // Synchronous: returns a value on the caller's thread. Keep it this cheap.
  isLowPowerMode(): boolean;
  // Everything that touches disk, network or real computation is a Promise.
  getBatteryLevel(): Promise<number>;
  readDeviceReport(): Promise<string>;
}

export default TurboModuleRegistry.getEnforcing<Spec>('NativeDeviceInfo');
```

Rules the file has to satisfy, each because codegen or runtime lookup fails
otherwise:

- **Name prefix `Native`.** Codegen keys the generated interface off the spec
  file name; the convention is enforced by tooling and by every generated
  template.
- **The string passed to the registry is the registered native name.** It is
  matched at runtime, not compile time — a mismatch is a runtime throw (with
  `getEnforcing`) or a silent `null` (with `get`).
- **Only codegen-supported types.** Primitives, `string`, `boolean`, object
  literals, arrays, `Promise<T>`, void, nullable variants, and enums via the
  codegen type helpers. A class instance, a `Map`, a `Date` or a function type
  other than a callback has no native representation.
- **Nullability is part of the contract.** `string | null` generates a nullable
  native return; `string` does not, and returning nil there is undefined
  behaviour rather than a JavaScript `null`.
- **Codegen type helpers come from the root export.** Under the Strict
  TypeScript API they live behind the `CodegenTypes` namespace
  (`CodegenTypes.Int32`, `CodegenTypes.WithDefault<...>`), not a deep import.

## Wiring codegen

```json
{
  "codegenConfig": {
    "name": "AppSpecs",
    "type": "modules",
    "jsSrcsDir": "specs",
    "android": {"javaPackageName": "com.acme.specs"}
  }
}
```

- `type` is `modules`, `components`, or `all` when the package ships both.
- `jsSrcsDir` is the directory codegen scans. A spec outside it is invisible,
  which looks exactly like a codegen bug.
- iOS runs codegen from the CocoaPods script phase, so `pod install` is what
  regenerates it. Android runs it as part of the build, or directly:
  `./gradlew generateCodegenArtifactsFromSchema`.
- Read the generated interface before writing native code, and after every spec
  change. It is the only authoritative statement of the method signatures the
  native class must conform to.

For a library rather than an app, `codegenConfig` goes in the library's own
`package.json`; consuming apps pick it up when autolinking scans dependencies.

## Registry lookup: getEnforcing vs get

| Call | Missing module | Use when |
|---|---|---|
| `getEnforcing<Spec>(name)` | throws immediately | the module ships inside the app and its absence is a build error |
| `get<Spec>(name)` | returns `null` | the module is optional — a platform-conditional capability, or a dependency that may not be installed |

`get` obliges the call site to handle `null` once, in a wrapper, rather than
letting `?.` spread through the codebase. Choosing `getEnforcing` and then
writing `Module?.method()` everywhere is the worst of both: the optional syntax
implies a fallback that can never run.

## Threads and what may be synchronous

| Work | Where it runs | Constraint |
|---|---|---|
| Host view creation and mutation | main/UI thread | never touch views from a background queue |
| Synchronous spec method | the calling JavaScript thread | must be trivial: no I/O, no locks, no large allocation |
| Promise-returning spec method | a shared native executor | fine for moderate work; it is shared, so do not camp on it |
| Heavy CPU or I/O | a module-owned queue or coroutine scope | cancel it when the module is torn down, or it leaks |

Thread names and exact scheduling vary between releases and host setups, so
confirm with a profiler when the precise thread matters instead of asserting it.
The stable part is the rule: a synchronous method holds up whatever called it,
and in practice that is the thread rendering the UI. [community]

The module-owned queue also matters for teardown: a background scope that
outlives its module keeps its captured objects alive and delivers results to a
dead consumer. The platform skill (`apple` / `android`) owns the idiom;
this skill owns the requirement that one exists.

## Fabric native components

A native view follows the same shape — spec first, then codegen, then the native
implementation:

```ts
// specs/AcmeMapViewNativeComponent.ts
import type {ViewProps, HostComponent} from 'react-native';
import {codegenNativeComponent} from 'react-native';
import type {CodegenTypes} from 'react-native';

interface NativeProps extends ViewProps {
  latitude: CodegenTypes.Double;
  longitude: CodegenTypes.Double;
  showsTraffic?: CodegenTypes.WithDefault<boolean, false>;
  onRegionChange?: CodegenTypes.DirectEventHandler<{zoom: CodegenTypes.Double}>;
}

export default codegenNativeComponent<NativeProps>(
  'AcmeMapView',
) as HostComponent<NativeProps>;
```

- The file name must end in `NativeComponent`; codegen selects component specs
  by that suffix.
- `type: "components"` (or `"all"`) in `codegenConfig`, or nothing is generated.
  On iOS the same block needs
  `"ios": {"componentProvider": {"<JS name>": "<Objective-C class>"}}` —
  the JS name from `codegenNativeComponent` mapped to the class that implements
  it. Without that entry the component resolves to nothing at runtime.
- Imperative operations go through `codegenNativeCommands` rather than a prop
  that encodes an action — a command is dispatched once, a prop change is
  reconciled and can be re-applied.
- Events are declared in the spec: `DirectEventHandler` for an event on the
  view, `BubblingEventHandler` when it should propagate.

## Expo modules: when to prefer them

In an Expo project, an Expo module is usually the better shape for new native
code: it ships with a lifecycle (`OnCreate`, `OnDestroy`, view lifecycle), a
declarative definition DSL on each platform, and — decisively — a config plugin
slot, so the native configuration the module needs survives `expo prebuild`.
Scaffold with `npx create-expo-module`, or `--local` for a module that lives
inside the app and needs no publishing.

Choose a plain Turbo Native Module when the package must work in bare React
Native projects without the Expo modules runtime.

## Old patterns

<details>
<summary>Legacy bridge modules (<code>NativeModules</code>, <code>RCT_EXPORT_MODULE</code>, <code>ReactContextBaseJavaModule</code>)</summary>

Reading a module off `NativeModules` still works through the interop layer, and
plenty of dependencies do it. Do not write new code this way: there is no
generated interface, so a signature mismatch surfaces as `undefined is not a
function` at the call site, and the module is constructed eagerly at startup.
When migrating, keep the native name identical so both access paths resolve
during the transition.

</details>

<details>
<summary><code>newArchEnabled</code> / <code>RCT_NEW_ARCH_ENABLED</code> toggles</summary>

On 0.76–0.81 these flags switched the runtime, and much community material still
treats the choice as live. From 0.82 the New Architecture is the only runtime;
the flags no longer select anything, and re-enabling legacy code on iOS requires
building React Native from source. Treat any advice that hinges on flipping them
as written for an unsupported release.

</details>

<!-- sources: rn-docs, callstack-rn, expo-official, expo-docs -->
