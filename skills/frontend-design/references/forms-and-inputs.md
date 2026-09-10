# Forms and inputs

Forms are where interfaces fail most reliably, and almost every failure is on this list.

## Contents

- [Labels and structure](#labels-and-structure)
- [Input types and autofill](#input-types-and-autofill)
- [Never fight the user](#never-fight-the-user)
- [Validation and errors](#validation-and-errors)
- [Submission](#submission)
- [Destructive and irreversible actions](#destructive-and-irreversible-actions)
- [Multi-step and long forms](#multi-step-and-long-forms)
- [States](#states)
- [Checkable rules](#checkable-rules)

## Labels and structure

- Every input has a visible label. A placeholder is not a label: it disappears on input, fails
  contrast more often than not, and leaves screen-reader users with nothing.
- Labels are clickable: `for`/`htmlFor` pointing at the input's id, or the label wrapping the
  control.
- Checkbox and radio: the label and the control share one hit target with no dead zone between them.
- Group related fields with `<fieldset>` and `<legend>`, or a clear visual grouping with a heading.
- Complex inputs get persistent helper text below the field, not a placeholder that vanishes.
- Placeholders, where used, show an example of the expected pattern and end with `…`.
- Required fields are marked visibly and programmatically (`required`), never by color alone.

## Input types and autofill

- Use the semantic `type`: `email`, `tel`, `url`, `number`, `search`, `date`. It brings validation,
  the right mobile keyboard, and browser affordances.
- Add `inputmode` where the type is too broad (`inputmode="numeric"` for a one-time code that must
  keep leading zeros, so `type="number"` is wrong).
- Every input carries a meaningful `name` and an `autocomplete` token (`email`, `given-name`,
  `postal-code`, `current-password`, `one-time-code`). Autofill is an accessibility feature, not a
  convenience.
- Set `autocomplete="off"` only on fields where a password manager would be actively wrong, and never
  on authentication fields; suppressing managers there is an SC 3.3.8 failure.
- Disable spellcheck on emails, usernames, codes and identifiers (`spellcheck="false"`). Leave it on
  for prose.
- Do not re-ask for information already supplied earlier in the same process; auto-populate it or
  let it be selected (SC 3.3.7).

## Never fight the user

- Never block paste. `onPaste` with `preventDefault` breaks password managers, breaks long codes and
  is an SC 3.3.8 failure. There is no legitimate reason for it.
- Never disable zoom.
- Never mask a field so aggressively that the person cannot verify what they typed; offer a show/hide
  toggle on passwords.
- Never truncate or reformat as the person types in a way that fights the caret.
- Use `autoFocus` sparingly: desktop only, one primary input, never on small screens where it raises
  the keyboard over the content.

## Validation and errors

- Validate on blur, not on every keystroke. Validating mid-typing shows errors for input that is
  merely incomplete.
- Show the error inline, below or beside its field, and connect it with `aria-describedby`. Set
  `aria-invalid` on the control.
- The error state is visible without color: an icon, a border weight change, and text.
- The message states the cause and the fix. "Invalid input" is not a message; "Enter an expiry date
  in MM/YY" is.
- After a failed submit with several errors, render a focusable error summary at the top, link each
  item to its field, keep the inline errors, and move focus to the summary. With no summary, move
  focus to the first invalid field.
- Errors are announced: a live region or `role="alert"` on the summary.
- Error and success colors still meet 4.5:1.
- Errors in the interface's voice: no apologies, never vague about what happened, always a next step.

## Submission

- The submit button stays enabled until the request actually starts. Disabling it while the form is
  merely incomplete hides why it is unavailable.
- Once the request starts, disable it and show progress in place, so a double submit is impossible.
- Confirm completion visibly: an inline success state or a toast, announced politely.
- A request timeout shows a clear message and a retry.
- Warn before navigating away with unsaved changes, via a router guard or `beforeunload`.
- An action keeps the same verb through the whole flow: a "Publish" button produces a "Published"
  confirmation.

## Destructive and irreversible actions

- Confirm, or offer an undo window. Never act immediately with no recourse.
- The destructive action uses the semantic danger color and is spatially separated from the primary
  action, so muscle memory does not delete things.
- Undo is better than confirmation for frequent operations; confirmation is better for rare and
  unrecoverable ones.
- Confirm before dismissing a sheet or modal with unsaved input.

## Multi-step and long forms

- Show a step indicator, and allow going back without losing input.
- Auto-save drafts on long forms so an accidental dismissal is not a data loss event.
- Preserve state on back navigation: scroll position, filter values, entered text.
- Put stateful UI in the URL (filters, tabs, pagination, expanded panels) so a form or list view can
  be shared and restored.

## States

| State | Presentation |
|---|---|
| Rest | Base tokens |
| Hover | More contrast than rest, pointer devices only |
| Focus | Visible `:focus-visible` indicator, 3:1 against both focused and unfocused states |
| Active | Slight scale (0.97) or a darker surface, 100-160ms |
| Loading | In-place progress on the control that was activated |
| Disabled | Reduced opacity plus the semantic attribute plus a cursor change; label stays legible |
| Read-only | Visually and semantically distinct from disabled; the value is selectable |
| Invalid | `aria-invalid`, icon, border, message |

Disabled and read-only are different things. A read-only field holds a real value the person may
need to copy; a disabled field is not currently applicable.

## Checkable rules

- Input with no label, or with a placeholder used as the label.
- Missing `autocomplete` or a meaningless `name`.
- Wrong `type` for the data.
- `onPaste` with `preventDefault`.
- `spellcheck` left on for an email, code or username field.
- Submit button disabled before the request starts.
- Error not associated with its field (`aria-describedby` missing), or not announced.
- Error state conveyed by color alone.
- No focus move after a failed submit.
- Destructive action with no confirmation and no undo.
- `autoFocus` with no justification, or on a small-screen layout.
- No unsaved-changes warning on a long form.
- Placeholder not ending in `…`, or not showing the expected pattern.

<!-- sources: vercel-wig, addy-frontend-ui, uiux-pro-max, anthropic-frontend-design, w3c-wcag22 -->
