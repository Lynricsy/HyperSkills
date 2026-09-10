# Supabase Storage

Verified against: Supabase Storage (platform), `@supabase/supabase-js` 2.x.

## Contents

- [Buckets](#buckets)
- [Policies per operation](#policies-per-operation)
- [Serving files](#serving-files)
- [Image transformations](#image-transformations)
- [Uploading](#uploading)
- [Debugging checklist](#debugging-checklist)

## Buckets

A bucket is public or private, and the choice is not cosmetic:

- **Public** — every object is readable by anyone with the URL, and it caches well on the CDN. Use
  it for assets that are genuinely public: logos, avatars if you accept that, marketing images.
- **Private** (the default) — objects are reachable only through a signed URL or an authenticated
  `GET` with the user's `Authorization` header.

Storage authorizes through RLS policies on `storage.objects`. With no policies, uploads are
refused outright. Bucket membership is just a column: `bucket_id = 'receipts'` inside the policy.

Path is also just a column. `storage.foldername(name)` splits the object path, so the standard
per-user layout is `<uid>/<file>` with `(storage.foldername(name))[1]` compared to the caller.

## Policies per operation

Each SDK call needs the privileges it actually performs, and the mismatch fails **silently**:

| Call | Needs |
|---|---|
| `upload` | `INSERT` |
| `upload` with `{ upsert: true }` | `INSERT` + `SELECT` + `UPDATE` |
| `download`, `createSignedUrl` | `SELECT` |
| `list` | `SELECT` |
| `remove` | `DELETE` |
| `move`, `copy` | `SELECT` + `INSERT` (+ `DELETE` for `move`) |

`upsert` with only `INSERT` granted is the classic one: the first upload works, replacing a file
does nothing, and no error is raised. An empty `list()` is the same story from the `SELECT` side —
a missing policy, not a client bug.

```sql
create policy "own receipts insert"
  on storage.objects for insert to authenticated
  with check (
    bucket_id = 'receipts'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );

create policy "own receipts read"
  on storage.objects for select to authenticated
  using (
    bucket_id = 'receipts'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );

create policy "own receipts replace"
  on storage.objects for update to authenticated
  using (
    bucket_id = 'receipts'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  )
  with check (
    bucket_id = 'receipts'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );
```

Keep the `bucket_id` predicate in every policy. A policy written without it applies to every
bucket in the project, so a permissive rule intended for avatars also opens the invoices bucket.

For a bucket that should be readable by anyone but not *listable*, the operation-aware helpers
`storage.allow_only_operation()` / `storage.allow_any_operation()` distinguish "read this object"
from "enumerate the bucket" within a single `SELECT` policy. Without that distinction, a
read-everything policy also hands over the file listing.

A trusted server may bypass policies with a secret key in the `Authorization` header. That is for
your own backend only, and it is never the fix for a policy that does not work.

## Serving files

```ts
// Public bucket only
const { data } = supabase.storage.from('assets').getPublicUrl('logo.svg')

// Private bucket: sign server-side, with an expiry in seconds
const { data, error } = await supabase.storage
  .from('receipts')
  .createSignedUrl(`${userId}/2026-08.pdf`, 3600)
```

`getPublicUrl` does no I/O and returns no error — it just formats
`/storage/v1/object/public/<bucket>/<path>`. Called on a private bucket it happily returns a URL
that 400s. If a "broken image" URL contains `/object/public/` for a bucket you know is private,
that is the bug.

Two facts about signed URLs worth internalising:

- They are signed with a **dedicated internal key per project**, separate from the Auth JWT
  signing key. Rotating or revoking Auth keys, disabling legacy keys, or switching from HS256 to
  asymmetric signing does **not** invalidate outstanding signed URLs. They stay valid until they
  expire, and revoking them early requires Supabase support. Choose expiries accordingly.
- Force a download rather than inline rendering with `?download` or `?download=name.pdf`, or the
  `download` option on the SDK call.

## Image transformations

`getPublicUrl`, `createSignedUrl` and `download` all take a `transform` option
(`width`, `height`, `resize`, `quality`, `format`), served from `/storage/v1/render/image/…`. For
a signed URL the transform is baked into the token, so the parameters cannot be edited afterwards —
which is the point, but it means one signed URL per variant.

Transformations are billable and can be disabled project-wide; if a transform URL suddenly 4xxs
across the board, check whether the feature is switched off before debugging the parameters.

## Uploading

- Default upload is a single request; for large files use resumable (TUS) uploads so a dropped
  connection resumes instead of restarting.
- The S3-compatible endpoint exists for tools that only speak S3; it authenticates with its own
  credentials and bypasses RLS, so treat it as server-side only.
- Set `contentType` on upload when the file name has no useful extension, otherwise the object is
  served as `application/octet-stream` and browsers download instead of rendering it.

## Debugging checklist

1. Which bucket, and is it public or private? Read it from the migration or the dashboard, not
   from the variable name.
2. Which SDK call, and does the caller hold **every** privilege that call needs (the table above)?
3. Is the failure a silent no-op (`upsert` without `UPDATE`, empty `list()`) or an HTTP error? A
   silent no-op is nearly always a missing policy for one of the operations.
4. Is `getPublicUrl` being used on a private bucket?
5. Does the policy include the `bucket_id` predicate and a path check that cannot be satisfied by
   another user's folder?
6. Verify by request, as the actual role — upload, replace, list, sign and fetch as a signed-in
   user, then repeat as a *different* user and confirm each step is refused.

<!-- sources: supabase-docs, supabase-official-skill, magnus-agent-skills -->
