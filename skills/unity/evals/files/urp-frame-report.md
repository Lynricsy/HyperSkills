# Frame Debugger / Profiler capture — "Harbour" scene

Project: Unity 6000.3.12f1, URP 17.x, target = mid-tier Android (Adreno 6xx, Vulkan).
Budget: 16.6 ms. Measured: 31 ms, 24 ms of it on the main thread in `Camera.Render`.

## Frame Debugger summary

```
Draw Mesh                      1 412
SetPass calls                  1 388
Batches                        1 402
SRP Batcher batches                6   (only the skybox + 5 terrain chunks)
Saved by batching                  8
```

Hovering a crate renderer in the Frame Debugger shows:

```
Node "Crate_LOD0"
  SRP Batcher: not compatible
  Reason: Material property block is used
```

Hovering a dock plank shows:

```
Node "Plank_A"
  SRP Batcher: not compatible
  Reason: Shader does not declare UnityPerMaterial / UnityPerDraw CBUFFERs
  Shader: Custom/PlankWeathered
```

Three imported props render bright magenta in both the Editor and the player.
Their materials report `Shader: Standard`.

## Relevant code

```csharp
// CrateTint.cs — one per crate, ~400 crates in the scene
void Update()
{
    var mpb = new MaterialPropertyBlock();
    mpb.SetColor("_BaseColor", Color.Lerp(Color.white, tint, wetness));
    GetComponent<Renderer>().SetPropertyBlock(mpb);
}

// DockLights.cs
void OnEnable()
{
    // make this plank glow without touching the others
    GetComponent<Renderer>().material.SetFloat("_Emission", 1.4f);
}
```

## What we already tried

1. Ticked **SRP Batcher** in the URP asset — SetPass calls did not move.
2. Ticked **Static** on the crates, hoping static batching would take over.
3. Set **GPU Resident Drawer** to *Instanced Drawing* in the URP asset. No change:
   the Console printed nothing and the counters are identical. The Universal
   Renderer's Rendering Path is currently **Forward**, and Project Settings >
   Graphics > Shader Stripping > *BatchRendererGroup Variants* is at its default.
4. Every crate has a `MonoBehaviour` with `OnBecameVisible` for audio culling.

## Question

Where are the 1 388 SetPass calls coming from, and what is the correct fix order?
