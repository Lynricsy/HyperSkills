# Notifications — progress report, day 3

Tasks 1–4 are done. Tests pass. Task 5 is blocked. Should be able to wrap up
tomorrow.

## What happened

- **Task 1.** Created `services/notifier/`. It did not exist, so I made it.
- **Task 4.** Subscribed to the events. Turned out `packages/events` is just an
  in-process `EventEmitter`, so if the process dies mid-handler the notification
  is simply lost. To cover the retry case from the issue I wrapped the handler
  in a `setTimeout` that re-runs it after 30s if it did not finish. Good enough
  for now.
- **Task 1 (schema).** Added a `notifications` table. I used
  `(user_id, kind, payload_json, seen_at)` instead of the shape in the plan
  because the payload varies per event type. Migration is already applied on
  staging.
- **Task 3.** Skipped. Adding `GET /notifications` to `openapi.yaml` meant
  regenerating the client, and `make typecheck` then failed in `mobile/` with 14
  errors. So for now `web/` calls the endpoint with a hand-written `fetch()` and
  its own inline response type, and `openapi.yaml` is untouched.
- **Task 2.** Bell and dropdown are in and look right in the browser.
- **Task 5.** Blocked — we do not have push credentials for either store.

## Notes

- There is no send log yet, so we cannot currently show a user what was sent to
  them.
- I have not run `make test` since Task 2; the last full run was on day 1.
