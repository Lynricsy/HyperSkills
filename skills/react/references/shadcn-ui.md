# shadcn/ui

Applies to any project with a `components.json`. These class conventions are
also this repository's only source of Tailwind guidance — in a shadcn project,
they win over any general Tailwind habit.

Verified against: shadcn CLI 3.x (`npx shadcn@latest`).

## Contents

- Project context comes from the CLI, not from memory
- Component docs come from the CLI too
- CLI commands
- Styling and Tailwind conventions
- Forms and inputs
- Component composition
- Icons
- `base` vs `radix`
- Registries
- Theming
- Chat and messaging

---

## Project context comes from the CLI, not from memory

First command in any shadcn task:

```bash
npx shadcn@latest info --json
```

Use the project's own package runner (`pnpm dlx shadcn@latest`,
`bunx --bun shadcn@latest`) as reported by `packageManager`. Read these fields
before writing a line of code:

| Field | Why it changes what you write |
|---|---|
| `aliases` | the real import prefix (`@/`, `~/`, `@workspace/ui/components`). Never hardcode `@/components/ui`. |
| `resolvedPaths` | exact filesystem destinations for components, utils, hooks |
| `isRSC` | when true, any component using state, effects, handlers or browser APIs needs `'use client'` |
| `tailwindVersion` | `v4` uses `@theme inline` blocks; `v3` uses `tailwind.config.js` |
| `tailwindCssFile` | the global CSS file where custom variables live — edit that file, never create a new one |
| `base` | `radix` or `base`; changes component APIs and available props |
| `iconLibrary` | `lucide` → `lucide-react`, `tabler` → `@tabler/icons-react`, and so on. Never assume Lucide. |
| `style`, `preset` | visual treatment; needed before applying or switching a preset |
| `framework` | routing and file conventions (App Router vs a Vite SPA) |
| `packageManager` | the runner for every non-shadcn install too |
| installed components | what already exists |

The upstream skill injects this JSON automatically at load time. That mechanism
is harness-specific and fails silently where it is unsupported — which leaves
the agent guessing. Run the command explicitly instead.

---

## Component docs come from the CLI too

```bash
npx shadcn@latest docs button dialog select
```

This returns documentation, example and API-reference URLs for each component.
Fetch them and read them before creating, fixing or debugging a component.
Component APIs change between releases, so a recalled API is the top source of
broken shadcn code. `npx shadcn@latest view @shadcn/button` inspects a registry
item that is not installed yet.

---

## CLI commands

```bash
# Create a project
npx shadcn@latest init --name my-app --preset base-nova
npx shadcn@latest init --defaults              # next template, nova preset

# Initialize an existing project
npx shadcn@latest init --preset base-nova

# Add components (registry must be explicit)
npx shadcn@latest add button card dialog
npx shadcn@latest add @magicui/shimmer-button
npx shadcn@latest add owner/repo/item

# Preview before writing
npx shadcn@latest add button --dry-run
npx shadcn@latest add button --diff button.tsx

# Search
npx shadcn@latest search @shadcn -q "sidebar"
npx shadcn@latest search                        # every configured registry

# Presets
npx shadcn@latest preset resolve --json         # current project's preset
npx shadcn@latest preset decode <code>
npx shadcn@latest apply <code>                  # existing project
npx shadcn@latest apply <code> --only theme,font
```

Rules for these commands:

- **Never decode a preset code or build a preset URL by hand.** Use
  `preset decode`, `preset url`, `preset open`, `preset resolve`.
- **Updating an installed component:** `--dry-run` to list affected files, then
  `--diff <file>` per file. No local changes → overwrite is safe. Local changes
  → read the file, read the diff, apply the upstream change while preserving
  the local edits. `--overwrite` needs explicit approval.
- **Never fetch component source from GitHub by hand.** The CLI rewrites
  imports for the project; a raw file does not.
- **Switching presets is a four-way choice** — overwrite, partial
  (`--only theme,font`), merge, or config-only. Ask which; do not pick.
- **Run preset commands inside the project.** `apply` needs an existing
  `components.json`, and preset codes do not encode `base`, so a scratch
  directory needs `--base <current-base>` passed explicitly.
- **After adding from a community registry**, check the added non-UI files for
  hardcoded `@/components/ui/...` paths and rewrite them to the project's real
  alias.

---

## Styling and Tailwind conventions

- **Semantic tokens, never raw palette colors.** `bg-primary`,
  `text-primary-foreground`, `text-muted-foreground` — not `bg-blue-500`,
  `text-gray-600`. Raw colors break theming and dark mode.
- **No manual `dark:` color overrides.** The tokens already resolve per theme.
  `bg-background text-foreground`, not `bg-white dark:bg-gray-950`.
- **Status colors go through `Badge` variants or a semantic token**
  (`text-destructive`). If a needed success color has no token, ask about adding
  one to the theme rather than reaching for `text-emerald-600`.
- **Built-in variants before custom classes.** `variant="outline"`, `size="sm"`.
- **`className` is for layout only** — `max-w-md`, `mx-auto`, `mt-4`. Never
  component colors or typography. To change appearance, in order: built-in
  variant → semantic token → a CSS variable in the project's global CSS file.
- **`gap-*`, never `space-x-*` or `space-y-*`.** `space-y-4` becomes
  `flex flex-col gap-4`; `space-x-2` becomes `flex gap-2`.
- **`size-*` when width and height are equal.** `size-10`, not `w-10 h-10`.
- **`truncate`**, not `overflow-hidden text-ellipsis whitespace-nowrap`.
- **`cn()` for conditional classes**, not a template-literal ternary inside
  `className`.
- **No manual `z-index` on overlay components.** `Dialog`, `Sheet`, `Drawer`,
  `AlertDialog`, `DropdownMenu`, `Popover`, `Tooltip` and `HoverCard` manage
  their own stacking; a hand-written `z-50` fights it.
- **Use the provided utilities for shimmer and scroll-edge fading** rather than
  hand-rolled keyframes or mask gradients.

---

## Forms and inputs

Form layout is `FieldGroup` + `Field` + `FieldLabel`. A raw `div` with
`space-y-*` or `grid gap-*` is wrong even when it looks right.

```tsx
<FieldGroup>
  <Field>
    <FieldLabel htmlFor="email">Email</FieldLabel>
    <Input id="email" type="email" />
  </Field>
</FieldGroup>
```

- Validation state is `data-invalid` on the `Field` plus `aria-invalid` on the
  control. Disabled state is `data-disabled` on the `Field` plus `disabled` on
  the control. Hand-written `border-red-500` is both a duplicate and invisible
  to a screen reader.
- `Field orientation="horizontal"` for settings rows.
  `FieldLabel className="sr-only"` for a visually hidden label.
- `FieldSet` + `FieldLegend` groups related checkboxes or radios — not a `div`
  with a heading.
- `InputGroup` takes `InputGroupInput` / `InputGroupTextarea`, never a raw
  `Input` or `Textarea`.
- A button inside an input is `InputGroup` + `InputGroupAddon`, never an
  absolutely positioned `Button` over a padded `Input`.
- An option set of 2–7 choices is `ToggleGroup` + `ToggleGroupItem`, not a
  `Button` loop with hand-managed active state.

Control selection: text → `Input`; fixed options → `Select`; searchable →
`Combobox`; no-JS native → `native-select`; boolean → `Switch` for settings,
`Checkbox` in forms; single choice from few → `RadioGroup`; 2–5 toggle →
`ToggleGroup`; verification code → `InputOTP`; multi-line → `Textarea`.

---

## Component composition

- **Items live inside their group.** `SelectItem` → `SelectGroup`;
  `DropdownMenuItem` → `DropdownMenuGroup`; `CommandItem` → `CommandGroup`;
  `MenubarItem` → `MenubarGroup`; `ContextMenuItem` → `ContextMenuGroup`.
- **`Dialog`, `Sheet` and `Drawer` always need a title** (`DialogTitle`,
  `SheetTitle`, `DrawerTitle`) for accessibility. `className="sr-only"` when it
  should not be visible.
- **`TabsTrigger` goes inside `TabsList`**, never directly in `Tabs`.
- **`Avatar` always needs `AvatarFallback`**, for when the image fails.
- **Use the full `Card` composition** — `CardHeader` / `CardTitle` /
  `CardDescription` / `CardContent` / `CardFooter` — not everything dumped into
  `CardContent`.
- **`Button` has no `isPending` or `isLoading` prop.** Compose `Spinner` +
  `data-icon` + `disabled`.
- **Reach for an existing component before writing markup:** `Alert` for
  callouts, `Empty` for empty states, `Separator` instead of `<hr>` or a
  border div, `Skeleton` instead of a custom pulsing div, `Badge` instead of a
  styled `span`.
- **Toast follows the project's base:** `toast` from the `toast` component on
  Base UI, `toast()` from `sonner` on Radix and React Aria.

Overlay choice: `Dialog` (modal), `Sheet` (side panel), `Drawer` (bottom
sheet), `AlertDialog` (confirmation).

---

## Icons

- Import from the configured `iconLibrary`. Never assume `lucide-react`.
- Icons inside `Button` carry `data-icon="inline-start"` or
  `data-icon="inline-end"`.
- **No sizing classes on icons inside components.** Components size their own
  icons via CSS — no `size-4`, no `w-4 h-4`, no `mr-2` — unless the user asks
  for a custom size.
- Pass icons as component references (`icon={CheckIcon}`), not string keys into
  a lookup map.

---

## `base` vs `radix`

Check the `base` field first; these APIs are not interchangeable.

| Need | `radix` | `base` |
|---|---|---|
| Replace a trigger's element | `asChild` + child element | `render={<Button />}` |
| Trigger renders a non-button (`<a>`, `<span>`) | `asChild` alone | `render` **plus** `nativeButton={false}` |
| `Select` options | inline JSX only | an `items` prop on the root |
| `ToggleGroup` multi-select | `type="multiple"` | `multiple` |
| `Slider` value | scalar | array |

`asChild` / `render` applies to every trigger and close component:
`DialogTrigger`, `SheetTrigger`, `AlertDialogTrigger`, `DropdownMenuTrigger`,
`PopoverTrigger`, `TooltipTrigger`, `CollapsibleTrigger`, `DialogClose`,
`SheetClose`, `NavigationMenuLink`, `BreadcrumbLink`, `SidebarMenuButton`,
`Badge`, `Item`. Never wrap a trigger in an extra element to work around it.

---

## Registries

Never choose a registry on the user's behalf. "Add a login block" without a
registry (`@shadcn`, `@tailark`, `owner/repo`) is a question, not a default —
different registries ship different source under the same name.

Every added file gets re-read after the fact: missing sub-components, missing
imports, wrong composition, and icon imports from the wrong library are all
common in third-party registry items. Fix them before moving on.

Authoring a registry is a separate task: a source `registry.json` (with `name`,
`homepage`, and `items` or `include`) built into served JSON with
`npx shadcn@latest build`. Include paths are relative to the declaring
`registry.json`, must point at a `registry.json` file, and cannot use remote
URLs, absolute paths or parent traversal.

---

## Theming

Components read semantic CSS variables, so changing a variable changes every
component that references it. Colors follow a `name` / `name-foreground` pair —
the base for backgrounds, `-foreground` for text and icons on top — and are
written in OKLCH (`oklch(lightness chroma hue)`).

The core set: `--background`, `--foreground`, `--card`, `--primary`,
`--secondary`, `--muted`, `--accent`, `--destructive`, `--border`, `--input`,
`--ring`, `--chart-1` … `--chart-5`, `--sidebar-*`, `--surface`.

Dark mode is a `.dark` class on the root element; in Next.js drive it with
`next-themes`. Edit the project's existing `tailwindCssFile`; never introduce a
second global stylesheet.

---

## Chat and messaging

Conversation UI composes the chat primitives rather than hand-rolled markup:
`MessageScroller` for the conversation, `Message` for a row, `Bubble` for the
surface, `Attachment` for files, `Marker` for system notes and dividers. The
nesting order is fixed (`MessageScrollerProvider` → `MessageScroller` →
`MessageScrollerViewport` → `MessageScrollerContent` → `MessageScrollerItem`).

`MessageScroller` owns scroll behaviour — streaming follow, anchoring and
jump-to-latest are built in. Writing a stick-to-bottom hook or a resize observer
for it is re-implementing what is already there.

<!-- sources: shadcn-official -->
