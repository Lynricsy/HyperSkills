---
name: Widget_Builder
description: I can help you build widgets with our design system. You can ask me anything about widgets and I will do my best to build them for you.
user-invocable: true
paths: "**/*.tsx"
metadata:
  promptSignals: widget, component, ui
---

# Widget Builder

## Introduction

This skill is about building widgets. A widget is a reusable piece of user
interface. In modern web development, widgets are usually written as React
components. React is a JavaScript library for building user interfaces that was
originally released by Facebook. It uses a syntax extension called JSX which
lets you write markup-like expressions inside JavaScript files. When the project
is built, a compiler such as Babel or SWC turns that JSX into plain function
calls.

Before you start, you will need to install the dependencies. Node package
managers download packages from a registry into a folder called node_modules and
record the exact versions in a lockfile. Run the install command for whichever
package manager the repository uses:

```bash
npm install
```

If the repository has a `yarn.lock` file, use yarn instead. If it has a
`pnpm-lock.yaml` file, use pnpm. If it has a `bun.lockb` file, use bun. Each of
these tools does roughly the same thing, which is to resolve the dependency
graph and write it to disk.

## What is a component?

A component is a JavaScript function that returns markup. Components can accept
inputs, which are called props. Props are passed to a component the same way
attributes are passed to an HTML element. Inside the component you can read them
from the first function argument. By convention component names start with a
capital letter, because lowercase names are treated as built-in HTML tags.

```tsx
function Greeting(props) {
  return <p>Hello {props.name}</p>;
}
```

You can also destructure the props in the parameter list, which many people find
easier to read:

```tsx
function Greeting({ name }) {
  return <p>Hello {name}</p>;
}
```

## State and effects

If a component needs to remember something between renders, use the useState
hook. It returns a pair: the current value and a function that updates it.
Calling the update function schedules another render.

```tsx
const [count, setCount] = useState(0);
```

If a component needs to synchronise with something outside React, such as a
subscription or a timer, use the useEffect hook. The second argument is the
dependency array. If you leave it out, the effect runs after every render. If
you pass an empty array, it runs once after the first render.

```tsx
useEffect(() => {
  const id = setInterval(tick, 1000);
  return () => clearInterval(id);
}, []);
```

Remember that you must not call hooks inside conditionals or loops, because
React relies on the call order being stable between renders.

## Styling

Our design system uses utility classes. A utility class does one thing, such as
setting a margin or a text colour. You compose several of them on one element.
There is also a `cn` helper that merges class strings and removes duplicates,
which is useful when a caller passes a `className` prop that has to win over the
component default.

```tsx
<div className={cn("flex items-center gap-2", className)} />
```

## TypeScript

Our repository is written in TypeScript. TypeScript is a typed superset of
JavaScript. You declare the shape of the props with an interface or a type
alias, and the compiler checks the call sites for you. Optional properties are
marked with a question mark. Union types let a property accept one of a fixed
set of values, which is how variant props are usually typed.

```tsx
interface ButtonProps {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}
```

Generic components are written by adding a type parameter to the function. The
type parameter is usually inferred from the props at the call site, so callers
rarely have to write it out.

## Testing

Write tests with the testing library. Render the component, query the output the
way a user would find it, and assert on the result. Prefer queries by accessible
role and name over queries by test id, because they fail when the accessibility
tree breaks.

```tsx
render(<Button>Save</Button>);
expect(screen.getByRole("button", { name: "Save" })).toBeVisible();
```

## Accessibility

Every interactive element needs an accessible name. Buttons get theirs from
their text content. Icon-only buttons need an explicit label. Form fields need a
associated label element. Colour must never be the only signal for state.
Focus must be visible. Dialogs must trap focus while they are open and restore
it to the trigger when they close.

## Running the generator

To scaffold a new widget, run the bundled generator:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/new_widget.py --name MyWidget
```

The generator reads the current registry, which you can inline here:

__omp_shell("`cat src/registry.json`")

## Advanced topics

For advanced topics, see [advanced.md](advanced.md).

## Component catalogue

Every component in the design system is listed below with its props. Read this
section before building anything so that you do not reimplement a component
that already exists.

### Accordion

The Accordion component renders collapsible sections. It lives in `src/components/accordion.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: items, defaultOpen, onToggle.

```tsx
import { Accordion } from "@acme/widgets";

<Accordion />;
```

### Alert

The Alert component renders inline status message. It lives in `src/components/alert.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: variant, title, dismissible.

```tsx
import { Alert } from "@acme/widgets";

<Alert />;
```

### Avatar

The Avatar component renders user image with fallback. It lives in `src/components/avatar.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: src, alt, size, fallback.

```tsx
import { Avatar } from "@acme/widgets";

<Avatar />;
```

### Badge

The Badge component renders small count or label. It lives in `src/components/badge.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: variant, count, max.

```tsx
import { Badge } from "@acme/widgets";

<Badge />;
```

### Breadcrumbs

The Breadcrumbs component renders navigation trail. It lives in `src/components/breadcrumbs.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: items, separator.

```tsx
import { Breadcrumbs } from "@acme/widgets";

<Breadcrumbs />;
```

### Button

The Button component renders primary action control. It lives in `src/components/button.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: variant, size, loading, disabled.

```tsx
import { Button } from "@acme/widgets";

<Button />;
```

### Calendar

The Calendar component renders month grid date picker. It lives in `src/components/calendar.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: value, onChange, minDate, maxDate.

```tsx
import { Calendar } from "@acme/widgets";

<Calendar />;
```

### Card

The Card component renders surface container. It lives in `src/components/card.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: padding, elevation, header, footer.

```tsx
import { Card } from "@acme/widgets";

<Card />;
```

### Carousel

The Carousel component renders horizontal slide deck. It lives in `src/components/carousel.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: slides, autoplay, interval.

```tsx
import { Carousel } from "@acme/widgets";

<Carousel />;
```

### Checkbox

The Checkbox component renders boolean input. It lives in `src/components/checkbox.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: checked, indeterminate, onChange.

```tsx
import { Checkbox } from "@acme/widgets";

<Checkbox />;
```

### Chip

The Chip component renders removable tag. It lives in `src/components/chip.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: label, onRemove, color.

```tsx
import { Chip } from "@acme/widgets";

<Chip />;
```

### Combobox

The Combobox component renders filterable select. It lives in `src/components/combobox.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: options, value, onChange, placeholder.

```tsx
import { Combobox } from "@acme/widgets";

<Combobox />;
```

### DatePicker

The DatePicker component renders single date field. It lives in `src/components/datepicker.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: value, onChange, format.

```tsx
import { DatePicker } from "@acme/widgets";

<DatePicker />;
```

### Dialog

The Dialog component renders modal overlay. It lives in `src/components/dialog.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: open, onClose, title, size.

```tsx
import { Dialog } from "@acme/widgets";

<Dialog />;
```

### Divider

The Divider component renders visual separator. It lives in `src/components/divider.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: orientation, inset.

```tsx
import { Divider } from "@acme/widgets";

<Divider />;
```

### Drawer

The Drawer component renders edge-anchored panel. It lives in `src/components/drawer.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: side, open, onClose, width.

```tsx
import { Drawer } from "@acme/widgets";

<Drawer />;
```

### Dropdown

The Dropdown component renders menu attached to a trigger. It lives in `src/components/dropdown.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: trigger, items, placement.

```tsx
import { Dropdown } from "@acme/widgets";

<Dropdown />;
```

### EmptyState

The EmptyState component renders zero-data placeholder. It lives in `src/components/emptystate.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: icon, title, description, action.

```tsx
import { EmptyState } from "@acme/widgets";

<EmptyState />;
```

### FileUpload

The FileUpload component renders drag and drop uploader. It lives in `src/components/fileupload.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: accept, multiple, maxSize, onFiles.

```tsx
import { FileUpload } from "@acme/widgets";

<FileUpload />;
```

### Form

The Form component renders field layout and submission. It lives in `src/components/form.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: onSubmit, initialValues, validate.

```tsx
import { Form } from "@acme/widgets";

<Form />;
```

### Grid

The Grid component renders two dimensional layout. It lives in `src/components/grid.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: columns, gap, responsive.

```tsx
import { Grid } from "@acme/widgets";

<Grid />;
```

### Icon

The Icon component renders glyph renderer. It lives in `src/components/icon.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: name, size, color.

```tsx
import { Icon } from "@acme/widgets";

<Icon />;
```

### Input

The Input component renders single line text field. It lives in `src/components/input.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: value, onChange, prefix, suffix.

```tsx
import { Input } from "@acme/widgets";

<Input />;
```

### Kbd

The Kbd component renders keyboard shortcut hint. It lives in `src/components/kbd.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: keys.

```tsx
import { Kbd } from "@acme/widgets";

<Kbd />;
```

### Link

The Link component renders navigational anchor. It lives in `src/components/link.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: href, external, underline.

```tsx
import { Link } from "@acme/widgets";

<Link />;
```

### List

The List component renders vertical item collection. It lives in `src/components/list.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: items, dividers, dense.

```tsx
import { List } from "@acme/widgets";

<List />;
```

### Menu

The Menu component renders command list. It lives in `src/components/menu.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: items, onSelect, searchable.

```tsx
import { Menu } from "@acme/widgets";

<Menu />;
```

### Pagination

The Pagination component renders page navigation. It lives in `src/components/pagination.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: page, pageCount, onPageChange.

```tsx
import { Pagination } from "@acme/widgets";

<Pagination />;
```

### Popover

The Popover component renders floating content panel. It lives in `src/components/popover.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: trigger, placement, offset.

```tsx
import { Popover } from "@acme/widgets";

<Popover />;
```

### Progress

The Progress component renders determinate progress bar. It lives in `src/components/progress.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: value, max, label.

```tsx
import { Progress } from "@acme/widgets";

<Progress />;
```

### Radio

The Radio component renders single choice input. It lives in `src/components/radio.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: name, value, options, onChange.

```tsx
import { Radio } from "@acme/widgets";

<Radio />;
```

### Rating

The Rating component renders star rating input. It lives in `src/components/rating.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: value, max, readOnly.

```tsx
import { Rating } from "@acme/widgets";

<Rating />;
```

### Select

The Select component renders native option picker. It lives in `src/components/select.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: options, value, onChange.

```tsx
import { Select } from "@acme/widgets";

<Select />;
```

### Skeleton

The Skeleton component renders loading placeholder. It lives in `src/components/skeleton.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: width, height, shape.

```tsx
import { Skeleton } from "@acme/widgets";

<Skeleton />;
```

### Slider

The Slider component renders range input. It lives in `src/components/slider.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: min, max, step, value.

```tsx
import { Slider } from "@acme/widgets";

<Slider />;
```

### Spinner

The Spinner component renders indeterminate loader. It lives in `src/components/spinner.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: size, label.

```tsx
import { Spinner } from "@acme/widgets";

<Spinner />;
```

### Stepper

The Stepper component renders multi step indicator. It lives in `src/components/stepper.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: steps, activeStep, onStepClick.

```tsx
import { Stepper } from "@acme/widgets";

<Stepper />;
```

### Switch

The Switch component renders on off toggle. It lives in `src/components/switch.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: checked, onChange, size.

```tsx
import { Switch } from "@acme/widgets";

<Switch />;
```

### Table

The Table component renders tabular data. It lives in `src/components/table.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: columns, rows, sortBy, onSort.

```tsx
import { Table } from "@acme/widgets";

<Table />;
```

### Tabs

The Tabs component renders panel switcher. It lives in `src/components/tabs.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: tabs, activeTab, onChange.

```tsx
import { Tabs } from "@acme/widgets";

<Tabs />;
```

### Textarea

The Textarea component renders multi line text field. It lives in `src/components/textarea.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: value, rows, autoResize.

```tsx
import { Textarea } from "@acme/widgets";

<Textarea />;
```

### Toast

The Toast component renders transient notification. It lives in `src/components/toast.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: message, variant, duration.

```tsx
import { Toast } from "@acme/widgets";

<Toast />;
```

### Tooltip

The Tooltip component renders hover hint. It lives in `src/components/tooltip.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: content, placement, delay.

```tsx
import { Tooltip } from "@acme/widgets";

<Tooltip />;
```

### Tree

The Tree component renders hierarchical list. It lives in `src/components/tree.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: nodes, expandedIds, onExpand.

```tsx
import { Tree } from "@acme/widgets";

<Tree />;
```

### Typography

The Typography component renders text styles. It lives in `src/components/typography.tsx`
and is exported from the package root. It accepts the standard `className` and
`style` props in addition to its own, and forwards any remaining DOM props to
its outermost element.

Props: variant, weight, align.

```tsx
import { Typography } from "@acme/widgets";

<Typography />;
```

## Notes

Widgets built before August 2025 used the legacy theme provider. If you are
working on a file that was written before August 2025, wrap the tree in the old
provider. After August 2025 the theme is read from CSS custom properties
instead, so no provider is needed.

If you are not sure which component to use, you can use Dialog, or Drawer, or
Popover, or Dropdown, or Menu - they all render floating content and each has
trade-offs, so pick whichever feels right.
