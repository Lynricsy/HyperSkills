# Cloud Storage

Verified against: Google Cloud SDK 584.0.0 (`gcloud storage` help text quoted below is from
that release); pricing and consistency semantics cross-read against
cloud.google.com/storage.

## Contents

- [Decisions fixed at creation](#decisions-fixed-at-creation)
- [Storage classes and minimum durations](#storage-classes-and-minimum-durations)
- [Lifecycle rules](#lifecycle-rules)
- [Autoclass](#autoclass)
- [Soft delete and versioning](#soft-delete-and-versioning)
- [Access control](#access-control)
- [Consistency](#consistency)
- [Where the bill comes from](#where-the-bill-comes-from)
- [gcloud storage, not gsutil](#gcloud-storage-not-gsutil)
- [Diagnosing 403 and 404](#diagnosing-403-and-404)

## Decisions fixed at creation

```bash
gcloud storage buckets create gs://BUCKET_NAME \
  --project=PROJECT_ID \
  --location=us-central1 \
  --default-storage-class=STANDARD \
  --uniform-bucket-level-access \
  --public-access-prevention \
  --soft-delete-duration=0 \
  --quiet
```

Three defaults are wrong for almost every production bucket and two of them are permanent:

| Setting | CLI default | Why it matters |
|---|---|---|
| `--location` | `us` (multi-region) | **cannot be changed after creation** without a bucket relocation operation or a copy. A multi-region bucket costs more per GiB than a region and puts data outside a single-region residency requirement |
| `--uniform-bucket-level-access` | `False` | leaves per-object ACLs enabled, so an object can be public while the bucket policy says otherwise. Enabling it later is possible but is a 90-day-reversible switch, and only after you have proven nothing depends on ACLs |
| `--soft-delete-duration` | 7 days | soft-deleted bytes are **billed as storage**; on a high-churn bucket this is a large invisible line item |

Note the console's bucket-creation wizard turns uniform bucket-level access on by default
while the API and CLI do not — which is why "our buckets have UBLA" and "the one Terraform
created does not" are both true.

Bucket names are globally unique across all of Google Cloud and cannot be reused immediately
after deletion. Do not put project or environment secrets in the name; do put something
unique in it (`acme-prod-events-a91f`), because `events` is taken.

## Storage classes and minimum durations

| Class | Minimum storage duration | Retrieval fee |
|---|---|---|
| `RAPID` (Rapid Bucket only, zonal) | none | none |
| `STANDARD` | none | none |
| `NEARLINE` | 30 days | yes |
| `COLDLINE` | 90 days | yes |
| `ARCHIVE` | 365 days | yes |

**The minimum duration is billed whether the object survives or not.** Deleting, overwriting
or re-classing an object before its minimum is up incurs an early-deletion charge for the
remaining days. An object moved to `ARCHIVE` on day 7 and deleted on day 30 is billed for 365
days of Archive storage — which is why a lifecycle policy that transitions early and deletes
soon after is the classic way to *raise* a storage bill while believing you lowered it.

Rule of thumb driven by lifetime, not by access frequency alone: total object lifetime under
30 days → stay in Standard. 30–90 days → Nearline. 90–365 days → Coldline. Over a year and
read a handful of times → Archive.

Retrieval fees apply per byte read from the colder classes, so a "cold" dataset that a monthly
job scans in full is not cheap in Coldline.

## Lifecycle rules

```json
{
  "rule": [
    { "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
      "condition": {"age": 30, "matchesStorageClass": ["STANDARD"]} },
    { "action": {"type": "Delete"}, "condition": {"age": 400} },
    { "action": {"type": "Delete"},
      "condition": {"numNewerVersions": 3, "isLive": false} },
    { "action": {"type": "AbortIncompleteMultipartUpload"},
      "condition": {"age": 7} }
  ]
}
```

Behaviour that surprises people:

- Rules are evaluated **asynchronously**. A configuration change can take up to 24 hours to
  take effect, and during that window Cloud Storage may still act on the previous
  configuration — including deleting objects under a rule you just relaxed. Lifecycle is not a
  mechanism for prompt or precise deletion.
- Conditions within one rule are ANDed. Separate conditions need separate rules.
- `age` counts from object creation, not from last access. There is no "delete if not read
  for N days" condition; that is what Autoclass or Storage Insights are for.
- Always include `matchesStorageClass` on a `SetStorageClass` rule, otherwise the rule
  re-evaluates objects that are already in the target class and generates needless
  operations.
- `AbortIncompleteMultipartUpload` is the rule almost nobody sets. Failed multipart uploads
  leave parts that are billed as storage and are invisible in a normal object listing.

## Autoclass

Autoclass moves each object between classes based on its own access pattern and removes the
whole class of mistakes above: no early-deletion fees, no retrieval fees, no Class A charge
for its own transitions. It costs a per-object management fee and an enablement charge.

Use it when access patterns are unknown or genuinely per-object. Use explicit lifecycle rules
when the pattern is known and uniform — for a bucket of 500 million small objects the
per-object management fee dominates.

## Soft delete and versioning

They are different mechanisms and they stack:

- **Soft delete** is on by default with a 7-day retention. Deleted (and overwritten) objects
  are retained and billed for that window, and can be restored. Set
  `--soft-delete-duration=0` to disable it on buckets of temporary or regenerable data.
- **Object versioning** is off by default. When on, every overwrite creates a noncurrent
  version that lives until a lifecycle rule removes it. A bucket with versioning on and no
  `numNewerVersions` or `daysSinceNoncurrentTime` rule grows without bound.

A bucket with versioning on, soft delete at 7 days, and a write-heavy workload stores several
copies of everything. When a storage bill does not match the object listing, this is almost
always why — `gcloud storage ls -a gs://BUCKET` shows noncurrent versions, and the soft-delete
bytes show up as the `Soft-deleted` metric in Monitoring rather than in any listing.

## Access control

- **Uniform bucket-level access** turns off per-object ACLs and makes IAM the only mechanism.
  Turn it on. Per-object ACLs mean auditing access requires reading every object.
- **Public access prevention** (`--public-access-prevention`) blocks `allUsers` and
  `allAuthenticatedUsers` grants regardless of what anyone tries to set. Enforce the
  `storage.publicAccessPrevention` org policy to make it organization-wide.
- Grant `roles/storage.objectViewer` / `objectCreator` / `objectAdmin` **on the bucket**, not
  the project. `roles/storage.admin` at project level is administration of every bucket
  including deletion.
- **Signed URLs** give time-limited access without an identity — the right answer for browser
  uploads and downloads. They are signed by a service account, so
  `roles/iam.serviceAccountTokenCreator` is the permission the signer needs, not a storage
  role.
- **Requester Pays** shifts egress and operation charges to the caller's project. Callers must
  then pass a billing project on every request, which breaks naive clients — enable it
  deliberately, not as a cost measure on an internal bucket.

## Consistency

Cloud Storage is **strongly globally consistent** for object read-after-write, read-after-
metadata-update, read-after-delete, and for bucket and object listing. There is no window in
which a freshly written object is missing from a list. Code that retries a read in a loop
"until the object appears" is working around a problem that no longer exists.

The exception is deliberate caching: publicly readable objects served with a `Cache-Control`
max-age are served from caches for that duration, so an overwrite is not immediately visible
to downstream readers. Set `Cache-Control: no-store` on mutable public objects, or version the
object name.

## Where the bill comes from

Four independent lines, and storage is often not the largest:

1. **Storage** — per GiB-month at the class rate, plus soft-deleted and noncurrent bytes.
2. **Network egress** — leaving Google Cloud, or crossing regions. Reading a US multi-region
   bucket from a `europe-west1` workload pays cross-continent egress on every read.
3. **Operations** — Class A (writes, lists) are roughly ten times Class B (reads) per 10,000.
   A job that lists a million-object bucket every five minutes generates a real bill from
   listing alone.
4. **Retrieval and early deletion** — the colder-class charges described above.

Co-locating the bucket with the compute that reads it removes line 2 entirely and is usually
the biggest single win.

## gcloud storage, not gsutil

`gcloud storage` is the current CLI: it parallelises by default, is substantially faster on
large transfers, and receives new features. `gsutil` still ships and still works but is in
maintenance. New scripts use `gcloud storage`; the flag names differ (`gcloud storage cp`
vs `gsutil cp` is close, but `gcloud storage rsync` and the `--recursive` semantics are not
identical), so translate rather than assuming.

```bash
gcloud storage ls --long gs://BUCKET/prefix/ --limit=20
gcloud storage cp --recursive ./dist gs://BUCKET/releases/GIT_SHA/
gcloud storage rsync --recursive --delete-unmatched-destination-objects ./site gs://BUCKET
gcloud storage du --summarize --readable-sizes gs://BUCKET
```

`--delete-unmatched-destination-objects` is the destructive one. Run without it first and read
the output.

## Diagnosing 403 and 404

Cloud Storage returns **404 for objects you are not allowed to see**, so that listing
permissions cannot be used to probe for object existence. A 404 on an object you are sure
exists is usually a permission problem, not a missing object.

Work through it in this order:

1. Which identity is calling — `gcloud auth list`, or the attached service account for a
   workload. The ADC quota project can also be the culprit for a `SERVICE_DISABLED` error
   masquerading as an access failure.
2. Bucket-level IAM: `gcloud storage buckets get-iam-policy gs://BUCKET`. Remember project
   and folder-level grants are inherited and do not appear here.
3. A deny policy or VPC Service Controls perimeter — both produce 403 with a distinguishing
   `reason` in the error body, and neither shows up in the bucket policy.
4. If UBLA is off, an object ACL can differ from the bucket policy:
   `gcloud storage objects describe gs://BUCKET/OBJECT --format="json(acl)"`.
5. Public access prevention or the `storage.publicAccessPrevention` org policy, if the failure
   is specifically a public read.

<!-- sources: gcp-docs, google-skills, gcs-extension -->
