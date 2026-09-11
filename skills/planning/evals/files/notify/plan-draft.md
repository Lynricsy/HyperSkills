# Notifications Implementation Plan

**Goal:** Notify users when something important happens.

All tasks below are independent and can be worked in parallel.

## Tasks

- [ ] **Task 1: Add notification service.** Extend `services/notifier/` with a
      `notify()` entry point. Add appropriate error handling.
- [ ] **Task 2: Wire up the frontend.** Add a notification bell and a dropdown
      list to `web/`, calling `GET /notifications`.
- [ ] **Task 3: Add the API.** Add `GET /notifications` and
      `POST /notifications/:id/read`.
- [ ] **Task 4: Hook into events.** Subscribe to the events the product cares
      about and call `notify()`.
- [ ] **Task 5: Add push notifications for mobile.**
- [ ] **Task 6: While we're in there, refactor `services/mailer` to go through
      the new service, and migrate the four billing receipt templates over to
      it.** Similar to Task 1.
- [ ] **Task 7: Run tests.**

## Testing

Write tests for the above.

## Definition of done

The feature works end to end and the team is happy with it.
