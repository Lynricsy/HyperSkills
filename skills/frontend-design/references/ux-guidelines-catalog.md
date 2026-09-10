# UX judgement calls

The review checklist covers what is decidable from a single line of code. This file covers the
judgement calls one level up: cases where the code is syntactically fine and the experience is still
wrong. Everything here is web-only; native platform idioms are out of scope for this skill.

## Contents

- [Overflow and compact labels](#overflow-and-compact-labels)
- [State legibility](#state-legibility)
- [Waiting and feedback](#waiting-and-feedback)
- [Error recovery](#error-recovery)
- [Hierarchy and emphasis](#hierarchy-and-emphasis)
- [Progressive disclosure](#progressive-disclosure)
- [Charts and data](#charts-and-data)
- [Tables and lists](#tables-and-lists)
- [Trust and honesty](#trust-and-honesty)

## Overflow and compact labels

- Pick the component from the semantics, not the shape. A badge is a count or a status; a status tag
  is a state; a filter chip is a removable query term. They look alike and behave differently.
- Wrap a chip collection before shrinking its labels. Shrinking text to fit is how a filter bar
  becomes unreadable.
- A `+n` overflow summary is an operable disclosure, not a decoration. It reveals the hidden values
  by pointer and by keyboard; hiding values behind an inert `+3` loses information.
- Any unavoidable truncation is disclosed to pointer and keyboard users alike, and the full value
  stays reachable.
- Essential labels stay visible. Dropping to icon-only to save space costs discoverability, and an
  icon-only navigation is worse than a scrolling one.

## State legibility

- Disabled and read-only are different states with different meanings. Read-only holds a real value
  the person may need to read or copy; disabled means not currently applicable. Rendering them
  identically makes both confusing.
- A disabled control should communicate why, or be replaced by an enabled control that explains the
  blocker when used. A dead button with no explanation is a dead end.
- The current location, the current filter, and the current sort are all visible without opening
  anything.
- Loading, empty, error and populated are four states. Every data-backed view needs all four
  designed, not just the populated one.
- Optimistic updates need a visible rollback path when the request fails, otherwise the interface has
  lied.

## Waiting and feedback

- Match the feedback to the expected wait. Near-instant work gets no indicator, because a flashing
  spinner is worse than none. Work over about a second gets a skeleton or an in-place progress state.
  Work over about ten seconds gets progress with an explanation.
- Skeletons match the shape and size of what replaces them. A skeleton of the wrong size causes the
  layout shift it was meant to prevent.
- Visible response to a press within about 100ms, independently of when the operation completes.
- Toasts auto-dismiss in roughly 3 to 5 seconds, never steal focus, and are announced politely.
  Anything the person must act on is not a toast.
- Confirm completion. An action that silently succeeds reads as an action that failed.

## Error recovery

- Every error message contains a recovery path: retry, edit, go back, or contact.
- A failed submit keeps the entered data. Losing a filled form is the least forgivable defect on this
  page.
- Errors above the fold, or focus moved to them. An error the person cannot find is not reported.
- Distinguish "you need to change something" from "the system failed"; the recovery differs.
- A network timeout is a distinct case from a validation failure, and says so.

## Hierarchy and emphasis

- One primary action per view. Secondary actions are visually subordinate; two equally weighted
  primaries means the design has not decided.
- Establish hierarchy with size, spacing and contrast rather than color alone.
- Use whitespace to group related items and separate unrelated ones. Uniform spacing means grouping
  carries no information.
- Destructive actions are separated spatially from constructive ones, so muscle memory is not a
  hazard.
- Elevation follows a single scale. Random shadow values read as accidental.

## Progressive disclosure

- Reveal complexity in stages rather than presenting every option at once.
- Defaults should be right for the common case, so most people never open the advanced section.
- A disclosure that hides something required is a trap; required fields are never behind a toggle.
- Keep the disclosure state in the URL when it changes what the person is looking at.

## Charts and data

- Match the chart to the question: trend to a line, comparison to bars, composition to a stacked bar
  rather than a pie beyond about five categories.
- Provide a text alternative: a summary describing the key insight, or an accessible table. A chart
  alone is unreadable to assistive technology.
- Distinguish series by more than hue: direct labels, patterns, or shapes. Never a red and green
  pair as the only distinction.
- Data marks meet 3:1 contrast against the background; data labels meet 4.5:1. Gridlines stay low
  contrast so they do not compete with the data.
- Label axes with units, and label the time granularity on a time series.
- Interactive marks are keyboard reachable, and tooltip content is not hover-only.
- Aggregate or sample beyond about a thousand points, and offer drill-down instead of rendering
  everything.
- Charts reflow on small screens: fewer ticks, horizontal bars, or a table.
- Entrance animation respects reduced motion, and the data is readable before it finishes.

## Tables and lists

- Sortable columns expose `aria-sort` with the current state.
- Row actions that only appear on hover are unreachable by keyboard and invisible on touch. Make them
  persistent, or reveal them on focus as well.
- Bulk and destructive operations get an undo, because a mis-click is worse at scale.
- A dense table drops card containers entirely: hairlines, tight padding, tabular figures.
- Selection state survives pagination, or the interface says clearly that it does not.

## Trust and honesty

- Never present an empty result as though it were data. Say that nothing matched, and say what was
  searched.
- Never fabricate content to fill a layout. If real content is unavailable, label it as sample data
  in the interface, not only in the code.
- Mock and sample data still respects the copy rules: plausible names, organic numbers, real-looking
  brands. A layout that only works with `John Doe` and `99.99%` has not been tested.
- When a value is estimated, rounded or delayed, the interface says so. Fake precision erodes trust
  faster than an honest approximation.

<!-- sources: uiux-pro-max, vercel-wig, addy-frontend-ui, antfu-design, anthropic-frontend-design -->
