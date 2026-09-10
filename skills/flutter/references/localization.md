# Localization with ARB files

Verified against: Flutter's `gen_l10n` tool as documented for current stable
(`flutter gen-l10n`).

## Contents

- [Setup](#setup)
- [Where the generated file lives](#where-the-generated-file-lives)
- [ARB syntax](#arb-syntax)
- [Using strings](#using-strings)
- [Locale resolution](#locale-resolution)
- [Package boundaries](#package-boundaries)
- [Failure catalogue](#failure-catalogue)

## Setup

```bash
flutter pub add flutter_localizations:"{sdk: flutter}" intl:any
```

`pubspec.yaml`:

```yaml
flutter:
  generate: true
```

`l10n.yaml` at the project root:

```yaml
arb-dir: lib/l10n
template-arb-file: app_en.arb
output-localization-file: app_localizations.dart
```

App wiring:

```dart
import 'package:flutter_localizations/flutter_localizations.dart';
import 'l10n/app_localizations.dart';

MaterialApp(
  localizationsDelegates: const [
    AppLocalizations.delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
  ],
  supportedLocales: AppLocalizations.supportedLocales,
);
```

Generation runs on `flutter pub get` and `flutter run`; force it with
`flutter gen-l10n`.

## Where the generated file lives

The generated `app_localizations.dart` is written next to the ARB files
(`lib/l10n/` for the config above) and imported by **relative path**, as in the
snippet above.

<details>
<summary>Old pattern: synthetic package (pre-deprecation)</summary>

Older projects set `synthetic-package: true` in `l10n.yaml` and imported
`package:flutter_gen/gen_l10n/app_localizations.dart`. That option is deprecated;
current tooling generates into `arb-dir` (or `output-dir`). If you inherit such a
project, drop the option and change the import to the relative path — an import
of `package:flutter_gen/...` that "cannot be resolved" is this, not a broken
install.
</details>

## ARB syntax

`lib/l10n/app_en.arb` (template — the only file that carries `@`-metadata):

```json
{
  "helloWorld": "Hello World!",
  "@helloWorld": {
    "description": "Greeting on the home screen"
  },
  "greeting": "Hello {userName}",
  "@greeting": {
    "placeholders": { "userName": { "type": "String", "example": "Ada" } }
  },
  "unreadCount": "{count, plural, =0{No messages} =1{1 message} other{{count} messages}}",
  "@unreadCount": {
    "placeholders": { "count": { "type": "num", "format": "compact" } }
  },
  "pronoun": "{gender, select, male{he} female{she} other{they}}",
  "@pronoun": {
    "placeholders": { "gender": { "type": "String" } }
  },
  "dueDate": "Due {date}",
  "@dueDate": {
    "placeholders": { "date": { "type": "DateTime", "format": "yMMMd" } }
  }
}
```

`lib/l10n/app_es.arb` carries only the translations, no metadata:

```json
{ "helloWorld": "¡Hola Mundo!" }
```

Rules:

- The `other` case is mandatory in `plural` and `select`.
- Placeholder names and types must match between template and translations; a
  mismatch fails generation with a message naming the key.
- Never build a sentence by concatenating fragments — word order differs by
  language. One key per full sentence, with placeholders.
- Escape a literal brace by enabling `use-escaping: true` and writing `'{'`.
- Keys are identifiers in the generated API: `camelCase`, no leading digits.

## Using strings

```dart
final l10n = AppLocalizations.of(context)!;
Text(l10n.greeting(user.name));
```

- The lookup needs a `BuildContext` below `MaterialApp`; a string needed in a
  notifier or repository means the layer is wrong — pass a key or format at the
  widget.
- For numbers, dates and currency outside ARB, use `intl` directly
  (`NumberFormat.currency(locale: ...)`, `DateFormat.yMMMd(locale)`), always with
  an explicit locale rather than the process default.
- Right-to-left comes free through `Directionality`, but only if layouts use
  `EdgeInsetsDirectional`/`start`/`end` instead of `left`/`right`.

## Locale resolution

- `supportedLocales` drives matching; the device locale that has no match falls
  back to the first entry, so put the real default first.
- Override the whole app with `MaterialApp(locale: ...)` (a user-chosen language),
  and one subtree with `Localizations.override(context: ..., locale: ...)`.
- Test a locale without changing the device:
  `MaterialApp(locale: const Locale('es'), ...)` in a widget test, then assert on
  translated text.

## Package boundaries

In a multi-package app, each package that owns UI owns its own ARB files and
generates its own `AppLocalizations`-style class; the app must not reach into a
package's l10n or vice versa. Shared strings live in the shared UI package, and a
package never assumes the app's locale list.

## Failure catalogue

| Symptom | Cause |
|---|---|
| `Target of URI hasn't been generated` | `generate: true` missing, or `flutter pub get` not run after adding `l10n.yaml` |
| `package:flutter_gen/...` unresolved | project still uses the removed synthetic package; import the relative path |
| `AppLocalizations.of(context)` is null | the delegate is not in `localizationsDelegates`, or the context is above `MaterialApp` |
| Generation fails after adding a translation | placeholder set differs from the template |
| Plural renders the ICU source text | missing `other` case, or `count` not declared as a placeholder |
| Strings not translated in Material widgets | `GlobalMaterialLocalizations.delegate` missing |
| Layout breaks in Arabic/Hebrew | hard-coded `left`/`right` padding and alignment |

<!-- sources: flutter-official, flutter-docs, evanca-rules -->
