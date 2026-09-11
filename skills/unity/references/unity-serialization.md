# Unity serialization and the data model

Verified against: Unity 6.3 LTS (6000.3); differences on 6.6 (6000.6) are marked.

## Contents

- [Why this is its own reference](#why-this-is-its-own-reference)
- [Field serialization conditions](#field-serialization-conditions)
- [Type support, and the Dictionary version boundary](#type-support-and-the-dictionary-version-boundary)
- [Custom classes: inline versus SerializeReference](#custom-classes-inline-versus-serializereference)
- [Properties](#properties)
- [Construction order and where initialization belongs](#construction-order-and-where-initialization-belongs)
- [Renaming and refactoring serialized data](#renaming-and-refactoring-serialized-data)
- [Inspector visibility versus serialization](#inspector-visibility-versus-serialization)
- [ScriptableObject as data](#scriptableobject-as-data)
- [Prefabs, variants and overrides](#prefabs-variants-and-overrides)
- [Hot reload and why private fields sometimes survive](#hot-reload-and-why-private-fields-sometimes-survive)
- [Diagnosing a serialization bug](#diagnosing-a-serialization-bug)

## Why this is its own reference

Unity does not use .NET serialization. It has its own field-based serializer that also
drives the Inspector, prefab overrides, scene files, undo, hot reload and `.asset` files.
The failure mode is silence: a field that does not meet the conditions is not stored and
not reported. Every "the Inspector is empty", "my defaults came back", "the list reset on
reload" and "the derived type became the base type" report is one of the rules below.

## Field serialization conditions

Unity serializes **fields**, not properties. A field is serialized when all of these hold
`[official]`:

- it is `public`, or carries `[SerializeField]`;
- it is not `static`;
- it is not `const`;
- it is not `readonly`;
- its type is serializable (next section).

Consequences worth internalising:

- `[SerializeField] private static int seed;` stores nothing. The attribute is accepted,
  no warning is produced, and the value resets to the field initializer every domain
  reload.
- `[SerializeField] private readonly float cooldown = 2.5f;` stores nothing and cannot be
  edited in the Inspector. `readonly` and "designer-tunable" are mutually exclusive.
- `[SerializeField] public int Ammo { get; set; }` does not compile at all — see
  [Properties](#properties).
- Prefer `[SerializeField] private` over `public` for tunables: the Inspector still edits
  them, but no other script can write them.

## Type support, and the Dictionary version boundary

Serializable field types `[official]`:

- primitives (`int`, `float`, `double`, `bool`, `string`, …) and enums up to 32 bits;
- fixed-size buffers;
- Unity built-ins (`Vector2`/`Vector3`, `Rect`, `Matrix4x4`, `Color`, `AnimationCurve`, …);
- structs and classes carrying `[System.Serializable]`;
- references to types deriving from `UnityEngine.Object`;
- a single-level `T[]` or `List<T>` of any of the above.

Never serialized, on every Unity 6 version:

- jagged arrays (`int[][]`) and multidimensional arrays (`int[,]`);
- containers nested directly in containers (`List<Dictionary<string,int>>`,
  `Dictionary<string,int>[]`).

`Dictionary<TKey, TValue>` is the one that moved. On **Unity 6.3 LTS** the manual lists
dictionaries among the unsupported "multilevel types", so `[SerializeField]
Dictionary<string,int>` is dropped. From **Unity 6.6** `Dictionary<TKey, TValue>` behind
`[SerializeField]` is a supported field type. `[verified]` (compared the 6000.3 and 6000.6
serialization-rules pages) Do not repeat the folklore "Unity can never serialize a
Dictionary"; state the version.

The portable workaround, and the only option on 6.3 LTS, is to wrap the nested type:

```csharp
[System.Serializable]
public struct DropRate          // one level of nesting, inside a [Serializable] type
{
    public string itemId;
    public int weight;
}

[SerializeField] private List<DropRate> dropRates = new();
```

For a runtime dictionary, build it in `Awake` from the serialized list, or implement
`ISerializationCallbackReceiver` and convert in `OnAfterDeserialize`.

`[System.Serializable]` is **not inherited**. Apply it to every class in the hierarchy. For
a base class you cannot edit (a third-party type), `[MakeSerializable]` pulls it into the
hierarchy. `[official]`

## Custom classes: inline versus SerializeReference

By default a non-`UnityEngine.Object` class is serialized **inline, by value**, inside the
host MonoBehaviour or ScriptableObject. That has four consequences that surprise people
`[official]`:

- inline serialization cannot represent `null` — Unity substitutes an inline object with
  unassigned fields;
- two fields pointing at the same instance become two separate objects after a reload;
- a cycle in the data leads to strange Inspector behaviour, console errors or an infinite
  loop;
- **polymorphism is lost**: assign a `FireDamage` to a `DamageEffect`-typed field and only
  the `DamageEffect` fields are stored; on load Unity instantiates `DamageEffect`.

`[SerializeReference]` fixes all four by storing the object in a managed-reference registry
instead of inline. Use it exactly when you need one of those four things — it is less
efficient, so inline remains the default. An interface-typed field is the common case:

```csharp
public interface IDropSource { string Describe(); }

[SerializeReference] private IDropSource source;   // without the attribute: never stored
```

With `[SerializeReference]` Unity does not strictly require `[Serializable]` on the class
but logs a console warning; `[MakeSerializable]` suppresses it. `[official]`

## Properties

Unity does not serialize properties. `SerializeField` is declared
`[AttributeUsage(AttributeTargets.Field)]` `[verified]`, so putting it on a property is
**CS0592** (`Attribute 'SerializeField' is not valid on this declaration type`) and the
whole file fails to compile — this is a red Console, not a silent no-op. Give the property
an explicit backing field and serialize that:

```csharp
[SerializeField] private int ammo;
public int Ammo { get => ammo; set => ammo = value; }
```

## Construction order and where initialization belongs

The order for a component loaded from a scene or prefab is: construct → **overwrite every
serialized field with the deserialized value** → `Awake` → `OnEnable` → `Start`. So:

- a constructor body and field initializers cannot establish runtime state that survives
  loading; they only matter for an instance created with `new` in the Editor (`Reset`
  territory) or for non-serialized fields;
- engine APIs are not valid from a constructor — `Time.time`, `GetComponent`, anything
  touching the native object, are all out;
- `Awake`/`OnEnable` are where derived state, caches, `System.Random` instances and event
  subscriptions belong;
- `Reset` supplies authoring-time defaults when the component is first added or reset in
  the Inspector; `OnValidate` reacts to Inspector edits.

The practical rule: if a field is `[SerializeField]`, its value comes from the asset, and
code that assigns it at construction is either dead or actively fighting the designer.

## Renaming and refactoring serialized data

Serialized data is keyed by field name. Renaming a field orphans every stored value in
every scene, prefab, variant and `.asset` — quietly, because the new name simply has no
stored value and falls back to the field initializer. `[FormerlySerializedAs]` from
`UnityEngine.Serialization` is the migration path, and it has to ship in the same change as
the rename `[verified]`:

```csharp
using UnityEngine.Serialization;

[FormerlySerializedAs("chance")]
[SerializeField] private float dropChance = 0.1f;
```

Keep the attribute until every asset has been re-saved, then remove it. Changing a field's
*type* is not covered by the attribute; that needs `ISerializationCallbackReceiver` or an
Editor migration script.

## Inspector visibility versus serialization

Four attributes are routinely confused:

| Attribute | Serialized | Shown in Inspector |
|---|---|---|
| `[SerializeField]` | yes | yes |
| `[HideInInspector]` (with `public`/`[SerializeField]`) | yes | no |
| `[System.NonSerialized]` | no | no |
| none, on a `private` field | no | no |

`[HideInInspector]` is the right tool for state you want persisted but not edited;
`[NonSerialized]` is the right tool for a cache you want rebuilt every load. Reaching for
`[HideInInspector]` to "clean up" a field that should not persist at all is a common
mistake — the value keeps coming back from the asset.

## ScriptableObject as data

A ScriptableObject is a `UnityEngine.Object` that lives as a project asset rather than on a
GameObject. It follows the same field rules, plus `[official]`:

- `[CreateAssetMenu]` is what makes it creatable from the Assets menu;
- in the Editor, Inspector edits persist automatically; edits made from script need
  `EditorUtility.SetDirty` plus a save;
- **at runtime in a player, changes are not written back to disk.** Treat a
  ScriptableObject as read-only configuration at runtime and keep mutable state elsewhere,
  or the Editor will appear to persist data that the shipped game loses;
- in the Editor, runtime mutation of a ScriptableObject *does* persist across Play-mode
  exits, which is why "it worked in the Editor" is such a common report for save systems
  built on ScriptableObjects.

Reference the same asset from many components instead of copying data: one instance, one
memory footprint, one place to edit.

## Prefabs, variants and overrides

- A prefab instance in a scene stores only its **overrides** — the fields that differ from
  the asset. Changing the asset propagates to every instance except where an override
  exists, which is why "my prefab change did not apply" is usually a stale override, not a
  broken prefab.
- A prefab variant is a prefab whose base is another prefab; its overrides stack. Adding a
  field to the base is safe; renaming one breaks overrides in every variant (see
  `[FormerlySerializedAs]` above).
- Nested prefabs keep their own override layer. Applying an override has to name the target
  (instance, variant, or base) — "Apply All" on a variant silently rewrites the base.

## Hot reload and why private fields sometimes survive

After a script recompile the Editor serializes live objects, reloads the domain and
restores them. That pass uses a broader rule than asset serialization: some private fields
survive a hot reload even without `[SerializeField]`. Do not infer from "it kept its value
after I saved the script" that a field is serialized — check it by entering and leaving
Play mode, or by reopening the scene.

## Diagnosing a serialization bug

1. Is the field `public` or `[SerializeField]`, and not `static`/`const`/`readonly`?
2. Is the field's type in the supported list, at one level of nesting only? Check the
   project's Unity version for the `Dictionary` case.
3. Does every custom class in the chain carry `[System.Serializable]`?
4. Is the field interface-typed or polymorphic? Then it needs `[SerializeReference]`.
5. Was the field recently renamed? Check git history and add `[FormerlySerializedAs]`.
6. Is code assigning the field in a constructor or field initializer and expecting it to
   win? It cannot.
7. Only after all six: suspect the Inspector, the prefab override layer, or a custom
   `PropertyDrawer`.

<!-- sources: gamedev-unity, nicewolf-unity, unity-docs, unity-cs-reference -->
