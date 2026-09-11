# The agent loop

## Contents

- [The loop is four lines; the hard part is the exits](#the-loop-is-four-lines-the-hard-part-is-the-exits)
- [Terminal states](#terminal-states)
- [The three caps](#the-three-caps)
- [Exiting on a cap](#exiting-on-a-cap)
- [Progress, not just turns](#progress-not-just-turns)
- [State that survives the process](#state-that-survives-the-process)
- [Handling a tool failure inside the loop](#handling-a-tool-failure-inside-the-loop)
- [Human interruption](#human-interruption)
- [Trajectory logging](#trajectory-logging)
- [When a loop is the wrong shape](#when-a-loop-is-the-wrong-shape)

## The loop is four lines; the hard part is the exits

```
call the model
if it produced tool calls:   run them, append results, repeat
if it produced a final answer: stop
```

Every framework implements this. What distinguishes a loop you can run in
production from one you cannot is entirely in what is missing from those
three lines: when it stops for reasons other than success, what it does with
partial work, and what it records.

## Terminal states

Enumerate them before writing the body. A loop with one exit (`the model
stopped calling tools`) has no way to end a run that is going wrong.

| State | Trigger | Result |
|---|---|---|
| `completed` | Final answer produced, and it validates against the output contract | Answer + trajectory |
| `needs_input` | The model called a tool that requires human approval, or asked a question it cannot answer itself | Paused run state, resumable |
| `turn_cap` | Turn count reached the maximum | Partial output + reason |
| `deadline` | Wall-clock budget exhausted | Partial output + reason |
| `budget` | Token or currency cap exhausted | Partial output + reason |
| `no_progress` | Repeated identical tool calls, or N turns with no state change | Partial output + reason |
| `fatal` | Premise invalid (ticket does not exist), authorisation failure, provider rejection that cannot be retried | Error, no partial claim |

Each non-`completed` state is a distinct outcome for the caller, and
collapsing them into `raise` loses the information that decides what to do
next. A `turn_cap` exit is worth resuming with a bigger cap; a `fatal` is
not.

Treat "the model produced a final answer" as a *claim*. If the run had an
output contract, validate against it; if the task had an acceptance check,
run it. A loop that believes the model's own completion report inherits the
model's optimism.

## The three caps

`while True:` with no bound is not a bug that shows up in review — it shows
up on the invoice. All three caps are needed because each catches a different
failure:

- **Turn cap.** Catches the model calling tools forever. 10–25 for a
  bounded task; higher only with the other two caps in place. Frameworks
  supply this (the OpenAI Agents SDK raises `MaxTurnsExceeded`, and
  `max_turns=None` disables it — an option that should require a comment
  explaining what bounds the run instead).
- **Wall-clock deadline.** Catches a slow tool or a provider degradation. A
  turn cap does not bound time; twelve turns with a two-minute tool is
  twenty-four minutes.
- **Token or currency budget.** Catches the expensive case a turn cap
  permits: a long context re-sent every turn. Twelve turns over a 150k
  context is not twelve cheap calls, and the cost per turn *grows* as
  history accumulates.

Each is checked **before** issuing the next request, using the accumulated
`usage` from previous responses. Checking after means the request that broke
the budget has already been paid for.

```python
for turn in range(MAX_TURNS):
    if time.monotonic() > deadline:
        return stop("deadline", partial)
    if spent_usd + estimated_next_call_usd > MAX_USD:
        return stop("budget", partial)
    ...
else:
    return stop("turn_cap", partial)
```

The `for … else` shape is worth the habit: the cap exit is written next to
the loop rather than bolted on after it.

## Exiting on a cap

An exceeded cap must produce three things:

1. The reason, as a value the caller can branch on — not a log line.
2. Whatever partial work exists: the answer so far, the facts established,
   the tool results gathered.
3. A resumable state, if resumption makes sense.

A loop that raises a bare exception on the cap throws away the work it paid
for, and the operator learns the cap exists from a stack trace. A loop that
returns nothing and logs "budget exceeded" is the same failure with better
manners.

## Progress, not just turns

Turn caps bound cost but not futility. A loop can spend all twenty turns
calling `lookup_order` with the same wrong id. Cheap detectors:

- **Identical call repeated.** Same tool, same arguments, twice in a row:
  the second result will be identical too. Return the cached result with a
  note saying it is unchanged, and if it happens a third time, stop.
- **No state change.** For tasks with observable state (files written, tests
  passing, records updated), N turns with no change is a stall.
- **Oscillation.** A → B → A → B across turns means two instructions
  conflict, and more turns will not resolve it.

On a stall, changing something is better than repeating: escalate to a human,
re-plan with the failure summarised, or exit. Retrying the same turn with a
higher temperature is a slot machine.

## State that survives the process

A run that can exceed a minute will be interrupted: deploy, OOM, timeout,
someone's laptop. Decide what is durable:

- **Externalise the facts.** Write established results to a file or store as
  they are produced. The transcript is then a cache, not the system of
  record, and a resumed run re-reads instead of re-deriving.
- **Checkpoint at turn boundaries**, including which tool calls have already
  executed. Resuming without that record re-executes side effects — the
  reason every non-idempotent tool needs a key
  (`tool-calling.md`).
- **Thread identity.** Persisted conversation state is keyed by a thread id;
  omitting it silently gives you a fresh conversation each call, which
  presents as "the agent forgot everything" rather than as an error.
- **Isolate threads.** One customer's thread id must not be derivable from
  another's, and the store must be scoped by tenant. Conversation state is
  user data.

For anything longer than a single request, a durable checkpoint beats keeping
the transcript in memory, because it also makes the run inspectable while it
is running.

## Handling a tool failure inside the loop

Three outcomes, decided per tool rather than globally
(`tool-calling.md`):

- **Return it to the model** — recoverable and actionable: bad argument,
  not-found, rate limit with a retry hint. Bound how many times the same
  tool may fail before it stops being recoverable, or a retry loop forms
  inside the model's turn budget.
- **Retry inside the tool** — transient network errors on an idempotent
  call, with a small bounded retry and jitter. Never for non-idempotent
  calls.
- **End the run** — premise invalid, authorisation denied, or the failure
  reveals something the model must not see.

The one shape to avoid is a `try/except` around the whole turn that retries
the turn. It re-executes every tool call that already succeeded
(rule 6 in `SKILL.md`).

## Human interruption

If a run can pause for approval, three things need designing, and skipping
any of them makes the feature unusable:

- **What the human sees.** The proposed call, its arguments, and enough
  context to judge it — not a raw JSON blob.
- **What they can do.** Approve, reject, or edit the arguments. Edited
  arguments must re-enter the loop as the call that was actually made, or the
  transcript and reality diverge.
- **What the model is told on rejection.** A tool result saying the call was
  declined and what to do instead. Silence reads as a failure and invites a
  retry of the same call.

Paused runs need a timeout and an owner. A run waiting forever on an approval
nobody sees is a stuck queue with no error.

## Trajectory logging

For every turn, record: the request (messages, tool schemas, model, settings),
the response, every tool call with arguments and result, retries, and the
`usage` numbers. Attach a run id and the model snapshot.

This is not observability polish; it is the difference between a debuggable
system and an anecdotal one:

- Without per-turn `usage`, cost cannot be attributed to a feature, and
  "the bill went up" has no owner.
- Without tool arguments, an incident cannot be reconstructed — you know a
  refund happened but not what the model was looking at when it decided to.
- Without the request, a behaviour change cannot be separated from a prompt
  change.
- Evals assert on trajectories, so a run that does not record one cannot be
  evaluated beyond its final string (`evaluation.md`).

Redact credentials and PII at the logging boundary rather than deciding not
to log. Log shipping, retention and alerting on those records is the
`observability` skill's territory.

## When a loop is the wrong shape

An agent loop is the right tool when the next step genuinely depends on the
previous result. It is the wrong tool, and costs 10× more, when:

- **The steps are known.** Three calls in a fixed order is a function. Giving
  the model the choice adds latency, cost, and a chance to pick wrong.
- **One call would do.** A single extraction with a schema is not an agent.
- **The task is a classification.** Route with a cheap classifier, then run
  the specific path.
- **Determinism is required.** A loop's path varies run to run; if the
  process must be auditable and identical every time, encode it.

The useful question when reviewing a loop: which decision in here actually
required the model? If the answer is "none, it just calls the same three
tools", replace it with the three calls and keep the model for the part that
needs judgement.

<!-- sources: openai-agents-python, langchain-skills, anthropics-claude-api, google-skills, murat-context-engineering, owasp-llm-top10 -->
