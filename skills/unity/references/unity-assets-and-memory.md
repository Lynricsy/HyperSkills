# Unity assets and memory

Verified against: Unity 6.3 LTS (6000.3).

## Contents

- [Where runtime memory actually goes](#where-runtime-memory-actually-goes)
- [Texture import settings](#texture-import-settings)
- [Sprite atlases](#sprite-atlases)
- [Meshes and audio](#meshes-and-audio)
- [Loading strategies, in order of preference](#loading-strategies-in-order-of-preference)
- [Addressables](#addressables)
- [Instantiated objects that outlive the scene](#instantiated-objects-that-outlive-the-scene)
- [Measuring](#measuring)

## Where runtime memory actually goes

On a shipped game the ranking is almost always: **textures ≫ meshes > audio > shader
variants > managed heap**. Script allocation shows up in frame-time (see
`unity-performance.md`), not usually in the footprint. Optimizing C# to fix an out-of-memory
crash on mobile is the classic wrong turn — check the texture budget first.

## Texture import settings

Import settings, not authoring resolution, determine what the player loads.

- **Max Size** is per-platform. The platform override is what ships; the default tab is
  ignored once an override exists. A 4096 source with a 1024 Android override costs 1024.
- **Compression format** decides size and quality:
  - Android: ASTC (pick a block size; 6×6 is a common default), ETC2 as the fallback;
  - iOS: ASTC;
  - desktop: BC7 for quality, BC1/BC3 (DXT) for size;
  - `RGBA 32 bit` / `Uncompressed` is 4 bytes a pixel and is almost never right.
- **Generate Mip Maps** on for anything seen at varying distance in 3D — without them,
  minified textures both alias and thrash texture cache. Off for UI and sprites, where they
  waste 33% and are never sampled.
- **Read/Write Enabled** keeps a second CPU-side copy: it doubles the cost and is only
  needed for `GetPixels`/`SetPixels`. It defaults off; someone turns it on to debug and
  leaves it.
- **Crunch compression** shrinks the *download*, not the runtime footprint, and costs
  decompression time at load.
- A non-power-of-two texture cannot use most block formats and falls back to a larger
  format silently.

## Sprite atlases

`com.unity.2d.sprite` Sprite Atlas packs many sprites into one texture so 2D and UI
rendering can batch.

- One atlas per screen or per logical group. An atlas spanning several screens loads all of
  it for one screen.
- Enable **Include in Build** (or it is packed but never shipped) and check **Allow
  Rotation**/**Tight Packing** against the sprite content — tight packing on UI sprites
  used with 9-slicing breaks them.
- Atlas variants provide a lower-resolution set for weaker devices, driven by a scale
  factor.
- Editing atlas assets from script needs an explicit save; do not script atlas packing in a
  runtime build.
- Two sprites in different atlases cannot batch together. A HUD built from sprites spread
  across four atlases costs four state changes per frame.

## Meshes and audio

- Mesh Compression trades precision for size; Optimize Mesh reorders for GPU cache. Both
  are import settings and cost nothing at runtime.
- Disable **Read/Write Enabled** on meshes not modified at runtime — same doubling as
  textures.
- Audio: **Decompress On Load** for short, frequent SFX; **Compressed In Memory** for
  medium clips; **Streaming** for music and long ambience. A music track left on Decompress
  On Load is tens of megabytes of PCM resident for the whole session.
- Force To Mono on anything without meaningful stereo content halves the data.

## Loading strategies, in order of preference

1. **Direct reference from a scene or prefab** — Unity loads it with the scene, unloads it
   with the scene. Correct default; no code.
2. **Addressables** — for content that must load and unload on demand, ship separately,
   or come from a CDN.
3. **`Resources/`** — everything under a `Resources` folder is included in the build
   regardless of references, is never stripped, and inflates the startup load. Unity
   discourages it; treat existing usage as debt and new usage as a mistake.
4. **`StreamingAssets/`** — raw files copied verbatim, read with platform file APIs. For
   data you want outside the asset pipeline entirely (a video, a config blob).

`Resources.UnloadUnusedAssets` is a scan of the whole heap and takes tens to hundreds of
milliseconds; it is a scene-transition tool, not something to call on a timer.

## Addressables

- Content is built **separately** from the player. A player build does not rebuild
  Addressables groups, and a stale catalog fails at load with a missing-key error rather
  than a build error.
- Every load returns an `AsyncOperationHandle` and **every load must be released**:
  `Addressables.Release(handle)` or `Addressables.ReleaseInstance(go)` for
  `InstantiateAsync`. Reference counting is per handle; a forgotten release keeps the whole
  bundle resident, which looks like a slow leak across level loads.
- Group layout is the whole game: *Pack Together* makes one bundle per group (fewer
  requests, more loaded than needed), *Pack Separately* makes one per entry (many requests,
  precise). Split by lifetime — content used together should live together.
- An asset referenced from two groups is **duplicated into both bundles**. The Analyze tool
  ("Check Duplicate Bundle Dependencies") is how you find it; this is the usual cause of a
  build that is twice the expected size.
- Labels are for filtering and preloading, not for grouping; grouping is the group.
- The Play-mode script matters: *Use Asset Database* ignores built content entirely, *Use
  Existing Build* reads the last content build. "It works in the Editor but not in the
  build" after an asset change is usually the first; "my asset change had no effect" is
  usually the second.
- `Addressables.LoadSceneAsync` replaces `SceneManager.LoadSceneAsync` for Addressable
  scenes; mixing the two APIs on the same scene gives a missing-scene error.

## Instantiated objects that outlive the scene

Several Unity types are created implicitly at runtime and are owned by nobody:

- `renderer.material` and `renderer.materials` instantiate copies (see
  `unity-rendering.md`). `Destroy` them in `OnDestroy` or accept the leak.
- `Instantiate`d `Mesh`, `Texture2D`, `RenderTexture` and `ComputeBuffer` are not
  garbage-collected: they are native objects. `Destroy`/`Release` them explicitly.
- A `RenderTexture` left allocated holds GPU memory for the process lifetime.
- Objects moved to a persistent scene with `DontDestroyOnLoad` survive every scene load,
  including a reload of the scene that created them — the standard cause of "two
  GameManagers after returning to the menu".

## Measuring

- **Memory Profiler package** (`com.unity.memoryprofiler`) takes a snapshot from a device
  and attributes native and managed memory per object. This is the only reliable way to
  answer "what is resident".
- The built-in Profiler's Memory module gives totals and the `GC.Alloc` call sites; it does
  not attribute native asset memory well.
- The **build report** in the Editor log lists the largest assets in the build — a build-size
  answer, not a runtime-footprint answer. The two differ: compressed on disk, decompressed
  in memory.
- Always measure on the target device in a development build. The Editor holds
  uncompressed copies of nearly everything and its numbers mean nothing for a shipped app.

<!-- sources: gamedev-unity, nicewolf-unity, unity-official-skills, unity-docs -->
