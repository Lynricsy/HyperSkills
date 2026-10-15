# GPU Resident Drawer rollout checklist (warehouse level)

Project: Unity 6000.3, URP. Universal Renderer Rendering Path is Forward+, BatchRendererGroup
Variants is set to Keep All, and the URP asset has GPU Resident Drawer set to Instanced
Drawing. Our lead wrote this checklist from the manual's "works only with" list for the GPU
Resident Drawer. We are about to apply it to ~3,000 prefabs with an editor script.

1. **Static props (shelves, pallets, racking).** The manual says a renderer must be "in the
   hierarchy of Animation or Animator components". None of these prefabs has one, so add an
   empty `Animator` (no controller) to the root of every static prop prefab so the drawer
   picks them up.
2. **Sliding doors.** Already fine: each door sits under an `Animator` whose open/close clips
   key `MeshRenderer.enabled` so the leaf is hidden while it is open.
3. **`LampFlicker.cs`** (on 220 ceiling lamps) implements `OnRenderObject` to nudge an
   emission value every frame. Callbacks exclude renderers from the drawer, so delete it and
   bake the flicker into the shader.
4. **`CrateAudioCull.cs`** (on ~400 crates) uses `OnBecameVisible` / `OnBecameInvisible` to
   mute crates the camera cannot see. Keep it; it only toggles an `AudioSource`.

Question for review: is anything here wrong before we run the script?
