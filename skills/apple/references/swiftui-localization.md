# Localization

Verified against: iOS 26.6 SDK.

Most localization bugs here are silent: the string simply appears in English, or appears
correctly in the developer's locale and wrongly in every other.

## Contents

- [Literals localize themselves](#literals-localize-themselves)
- [String Catalogs](#string-catalogs)
- [Bundles in packages and frameworks](#bundles-in-packages-and-frameworks)
- [Variables and custom types](#variables-and-custom-types)
- [Interpolation and grammar](#interpolation-and-grammar)
- [Formatting values](#formatting-values)
- [Layout and RTL](#layout-and-rtl)
- [Comments for translators](#comments-for-translators)

## Literals localize themselves

Every SwiftUI initialiser that takes a `LocalizedStringKey` — `Text`, `Button`, `Label`,
`navigationTitle`, alert and dialog titles — treats a string literal as a localization key.

```swift
// Wrong: resolves eagerly and ignores a \.locale override in the environment.
Text(String(localized: "start_workout"))

// Right.
Text("start_workout")
```

Opaque keys (`"start_workout"`) and natural-language keys (`"Start Workout"`) both work;
follow whichever convention the project already uses. `Text(verbatim:)` opts a literal out
of localization — the correct choice for a debug label or an identifier, and nothing else.

Note the asymmetry that catches people: a `String` **variable** passed to `Text` selects the
`StringProtocol` overload and is **not** localized. See below.

## String Catalogs

New projects use String Catalogs (`.xcstrings`). Each build syncs keys from code into the
catalog, but Xcode does not create the catalog for you — it must already exist. A project
already on `.strings` / `.stringsdict` should get new strings added there rather than a
migration.

Route groups of strings to a specific catalog with `tableName:`:

```swift
Text("Explore", tableName: "Navigation",
     comment: "Tab bar item title for the Explore screen.")
```

When a project uses symbol keys in a catalog, set `extractionState` to `manual` and access
them through the generated symbols (`Text(.helloWorld)`). Offer to add the new key to every
language the project already supports rather than leaving it untranslated.

## Bundles in packages and frameworks

An app, app extension, or XPC service is its own main bundle, so `bundle:` can be omitted.
A framework or Swift package cannot: without an explicit bundle, SwiftUI looks the key up in
`Bundle.main`, the lookup fails **silently**, and the untranslated key text ships.

```swift
Text("Save to Favorites", bundle: #bundle,
     comment: "Button to bookmark a recipe.")
```

`#bundle` is the current form. `Bundle.module` and `Bundle(for:)` still work and are older
patterns.

## Variables and custom types

Wrapping a runtime `String` in `LocalizedStringKey(_:)` does not help — Xcode cannot extract
a literal from a runtime value, so nothing lands in the catalog and the lookup fails at
runtime.

Model a value chosen from a known set as a type that exposes `LocalizedStringResource`:

```swift
enum Category {
    case appetizers, mains, desserts

    var name: LocalizedStringResource {
        switch self {
        case .appetizers: "Appetizers"
        case .mains: "Mains"
        case .desserts: "Desserts"
        }
    }
}

Text(category.name)
```

Type user-facing properties as `LocalizedStringKey` or `LocalizedStringResource`, not
`String`. `LocalizedStringResource` defers resolution to display time, so the value honours
the locale active when it renders rather than when it was created — which matters for
notifications, tips, and anything queued. Outside a view, `String(localized:)` is the
correct API when you truly need a resolved `String` now.

## Interpolation and grammar

- Interpolate; never concatenate. `Text("Hello, \(name)")` is one translatable unit,
  `Text("Hello, ") + Text(name)` is two fragments no translator can reorder — and `Text`
  concatenation with `+` is itself deprecated.
- Use automatic grammar agreement for English, French, German, Portuguese, Spanish, and
  Italian rather than hand-written plural branches:
  `Text("^[\(people) person](inflect: true)")`.
- Plural and gender variation beyond that lives in the catalog's variations, not in Swift
  `if` statements.
- Do not apply runtime case transforms (`.uppercased()`) to user-facing text. Casing rules
  differ per language — Turkish dotted and dotless i is the classic break — and some scripts
  have no case at all. Style the text with `.textCase(.uppercase)` so the system decides.

## Formatting values

Never hand-format a value that has a `FormatStyle`.

- `Text(date, format: .dateTime.day().month().year())`
- `Text(amount, format: .currency(code: "USD"))`
- `Text(count, format: .number)`
- Lists: `ListFormatStyle` rather than `joined(separator: ", ")`, which is wrong in several
  languages.
- Names: `PersonNameComponents` with its format style, not `"\(first) \(last)"` — name order
  is not universal.
- If a manual date pattern is unavoidable for display, use `y` and never `yyyy`; `yyyy`
  produces the wrong year in some calendars. For data interchange this does not apply.
- Parse with `Date(string, strategy: .iso8601)` rather than a `DateFormatter`.

## Layout and RTL

- Use `.leading` and `.trailing`, never `.left` and `.right`. The same applies to padding
  edges, alignment guides, and text alignment.
- Test with a pseudolanguage (double-length, or right-to-left) plus the largest Dynamic
  Type size. German compound nouns and Arabic mirroring break more layouts than translation
  errors do.
- Avoid fixed widths on anything containing text.
- `\.layoutDirection` is available when a custom drawing path genuinely needs to mirror.

## Comments for translators

Every string with an interpolation needs a `comment:` explaining what the placeholder is. A
translator seeing `"%@ items"` cannot tell whether the placeholder is a count, a name, or a
category, and word order depends on the answer. Comments are the highest-leverage,
lowest-effort localization work in a codebase.

<!-- sources: avdlee-swiftui, apple-xcode27, twostraws-swiftui, apple-docs -->
