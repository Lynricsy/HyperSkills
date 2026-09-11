# Tutorials that a stranger can finish

## Contents

- [The contract](#the-contract)
- [Pick one outcome and one path](#pick-one-outcome-and-one-path)
- [Declare the starting state](#declare-the-starting-state)
- [Every step has an observable result](#every-step-has-an-observable-result)
- [Steps that are not steps](#steps-that-are-not-steps)
- [Credentials, endpoints and services](#credentials-endpoints-and-services)
- [Where the explanation goes](#where-the-explanation-goes)
- [Verifying a tutorial](#verifying-a-tutorial)
- [Diagnosing a tutorial people abandon](#diagnosing-a-tutorial-people-abandon)

## The contract

In a lesson nearly all the obligation sits with the author. The reader's only
job is to follow along; they have no obligation to understand, remember, or
work anything out. So anything on the path that can fail is the author's defect,
including the parts that are "obvious". [official]

Three properties the exercise must have:

- **Meaningful** — finishing it feels like an achievement, not a formality.
- **Completable** — a reader with the declared prerequisites and nothing else
  gets to the end.
- **Usefully complete** — the reader meets every concept, command and tool they
  will need later, once each.

## Pick one outcome and one path

State the outcome in the first two sentences, in terms the reader can check:
"by the end you will have two processes sharing one rate limit, and you will see
the second one wait." Then commit to exactly one route there.

No alternatives. Not "you can also use X", not a table of backends, not "if you
prefer Y". A first-time reader has no basis for choosing, so a choice is a place
to stop. Where a genuine fork exists, pick the one that works with the fewest
moving parts and mention the other only in a final "next steps" line pointing
at a how-to guide.

This is the property that separates a tutorial from everything else, and the
one most often lost during review: someone adds the other option "for
completeness", and the page quietly becomes a reference with numbers on it.

## Declare the starting state

Before the first code block, list everything the reader must already have. Each
item is a command they can run to check it, or a value they must obtain:

```
Before you start:
- Python 3.11 or newer: `python --version`
- The redis extra: `pip install 'corral[redis]'`
- A Redis server on localhost:6379: `redis-server --port 6379`
- An API token, exported as CORRAL_TOKEN
```

Two failure modes this prevents, both of which read as "the library is broken":

- **The install is not the install.** Step 1 installs the base package; step 3
  imports an optional backend. The reader gets `ImportError` and no reason to
  connect it with step 1. Install what the whole tutorial needs, in step 1,
  with the extras.
- **The constructor needs a secret.** Code that reads a token from the
  environment raises on the first line of the first example. A tutorial that
  never names the variable fails before the step anyone reports failing at —
  which is why reports of "it breaks at step 3" often locate the wrong step.

Name variables exactly as the code reads them. `CORRAL_API_KEY` in the docs
against `CORRAL_TOKEN` in the source is not a typo to the reader; it is an hour.

## Every step has an observable result

Each step ends with the thing the reader sees: a line of output, a file that now
exists, a status code, a row in a table, an error that proves the guard works.
Quote it.

```
$ python limits.py
waited 0.00s  status 200
waited 0.19s  status 200
```

A step with no observable result cannot be checked, so a reader who has already
gone wrong continues in the broken state and discovers it three steps later,
with no way to tell where it started.

## Steps that are not steps

Delete or rewrite these, with the reason each fails:

| Step | Why it is not one |
|---|---|
| "Watch the limiter work. Notice how the processes share the budget." | Names nothing to look at. If the output is the point, print and quote it. |
| "Once it works locally, deploy it and set the appropriate environment variables." | Names no variable, no target, no command. It is a wish with a number on it. |
| "Configure the limiter for production." | Deployment is a how-to guide for readers who already finished this. Link it. |
| "Install the dependencies." | Which ones, with which command, for which extras. |
| "Restart the server." | Which command, and how does the reader know it came back. |

## Credentials, endpoints and services

- Endpoints in examples must be either real and stable, or obviously fake with
  a stated substitute: `https://api.example.com` is fine when the page says to
  replace it, and a trap when the page tells the reader to expect output from
  it.
- Never show a credential that pattern-matches a live one. Use the provider's
  documented test prefix, or a placeholder the page explains. A sample that
  looks live gets pasted into real code and trips secret scanners on push.
- Any service the tutorial talks to (a database, a queue, a local stub) gets a
  step that starts it and a check that it is up.

## Where the explanation goes

Minimise explanation; do not eliminate it. One sentence of why, where the
reader would otherwise be typing blind, is part of the lesson. A paragraph on
the trade-offs is not: it interrupts the doing, and the reader skips it anyway
because they are mid-task. Move it to explanation and link it from the closing
section.

## Verifying a tutorial

The exit criterion is mechanical, and it is not "reads well":

- [ ] A clean environment was created and the declared prerequisites installed —
      nothing else.
- [ ] Every block was pasted in order and run. Output was captured.
- [ ] The quoted output in the page is the output that was captured, not a
      reconstruction.
- [ ] Every symbol the tutorial calls exists in the current source with that
      name and that signature.
- [ ] Every link resolves.
- [ ] The final state matches the outcome promised in the opening.

If the environment cannot be created here, say so in the delivery and name what
was not verified. An unverified tutorial that claims to be verified is worse
than one that admits it.

## Diagnosing a tutorial people abandon

Readers report where they gave up, not where it broke. Work forward from step 1
against the current source:

1. Run each block in order in a clean environment and find the **first** one
   that fails. That is usually earlier than the reported step.
2. For each failure, decide which of three it is: a missing prerequisite, a
   stale API name, or a step with no observable result that let the reader drift
   off the path.
3. Check the whole page for that class of defect, not just the instance you
   found. One stale method name usually means the page predates a rename and
   every other name on it is suspect too.
4. State the specific wrong claims before rewriting anything. A silently
   corrected page teaches its author nothing, and the next tutorial repeats it.

<!-- sources: diataxis, mblode-docs-writing, mcollina-skills, google-devdocs-style -->
