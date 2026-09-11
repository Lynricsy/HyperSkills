# Issue #412 — Notify users when something important happens

**Reporter:** @dana (Support lead) · **Labels:** enhancement, needs-triage

## Body

Support keeps getting tickets from customers who say they had no idea their
thing had changed until they logged in days later. We should notify users when
something important happens on their account, the way Slack does it. Nothing
fancy — just make sure people find out.

It should feel instant but not spammy.

We already have the email templates from the billing work, so this should mostly
be plumbing.

Obviously it must not double-send when the worker retries.

No rush, but it should be in before the SOC 2 audit window opens.

---

### Comment — @raj (Mobile)

+1. This should work for the mobile app too, not just web. Push would be ideal
but in-app is fine for v1.

### Comment — @dana

One more thing: enterprise accounts have a compliance requirement that anything
we send to a user is retrievable later, so whatever we build needs to keep a
record.

### Comment — @sam (Eng manager)

Let's keep this small. Ship something this cycle.
