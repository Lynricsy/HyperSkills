# Team members screen: redesign brief

## Our product

Fieldnote is a shared lab-notebook tool for small research groups (3 to 40 people).
The web app already has a design system:

- Surfaces `--surface` #FBFAF7 and `--surface-raised` #FFFFFF, text `--text` #1C1E1D, muted `--text-muted` #5F6461
- One accent `--accent` #2F6B4F (a dark lab green), used for primary actions only
- Type: "Source Serif 4" for page titles, "IBM Plex Sans" for UI, "IBM Plex Mono" for IDs
- Radius scale 4 / 8 px, hairline borders, no shadows except on menus
- Components: Table, Menu, Dialog, Toast, Badge, Select, TextField, Button (primary / secondary / danger)

## The screen

Settings → Members. Lists everyone in the workspace with name, email, role (Owner, Admin, Member,
Guest), last active date, and pending invitations. Admins and Owners can invite people, change roles,
resend or revoke invitations, and remove members. A workspace must always keep at least one Owner.
Members and Guests can open this page too.

Today it is a plain HTML table with a "+ Invite" link above it. Support tickets say people cannot
tell pending invites from members, role changes happen with no confirmation, and removing someone
has no undo.

## References the team likes

### Linear, Settings → Members

- Dense single-column list, 44 px rows, avatar + name + email stacked on the left, role as an inline
  select on the right, overflow menu at the far right.
- Search field and an "Invite" primary button in the header row, purple (#5E6AD2) button.
- Pending invites are a separate section below members, with "Resend" and "Revoke" in the overflow
  menu. Copy: "Invite your teammates to collaborate in Linear."
- Keyboard: Cmd+K opens a command menu that can invite people.

### Vercel, Team Settings → Members

- Tabs: "Team Members" / "Pending Invitations".
- Black-and-white UI, Geist type, every row has a role select and a "…" menu.
- Invite is a panel at the top with an email field that accepts several addresses and a role select,
  then "Invite".
- Removing a member opens a confirmation dialog that asks you to type the member's email.
