# Serverless: Lambda, API Gateway, Step Functions, SQS and EventBridge

Verified against: AWS Lambda quotas page, API Gateway REST and HTTP quota tables, and the
Step Functions developer guide on docs.aws.amazon.com. Numbers below are **default** quotas
for a mature account; new accounts start lower and AWS raises them with usage.

## Contents

- [Lambda quotas that decide designs](#lambda-quotas-that-decide-designs)
- [Concurrency, scaling and throttling](#concurrency-scaling-and-throttling)
- [Cold starts and what actually helps](#cold-starts-and-what-actually-helps)
- [Event source mappings and at-least-once delivery](#event-source-mappings-and-at-least-once-delivery)
- [Idempotency](#idempotency)
- [API Gateway: choosing the type](#api-gateway-choosing-the-type)
- [Timeouts, and why 504 is usually a design bug](#timeouts-and-why-504-is-usually-a-design-bug)
- [Authorizers](#authorizers)
- [The recurring API Gateway failures](#the-recurring-api-gateway-failures)
- [Step Functions: Standard versus Express](#step-functions-standard-versus-express)
- [SQS and EventBridge wiring](#sqs-and-eventbridge-wiring)

## Lambda quotas that decide designs

| Resource | Default | Adjustable |
|---|---|---|
| Function timeout | 900 s (15 min). Lambda Managed Instances functions invoked asynchronously or via an event source mapping — except Amazon MQ and DocumentDB — reach 5,400 s (90 min) | no |
| Memory | 128 MB – 10,240 MB, 1 MB steps; **1,769 MB is exactly one vCPU** | no |
| Invocation payload | 6 MB request and 6 MB response (synchronous); 1 MB (asynchronous); 200 MB for a streamed response | no |
| Deployment package | 50 MB zipped via the API, 250 MB unzipped including layers; 10 GB as a container image | no |
| Layers | 5 per function | no |
| Environment variables | 4 KB aggregate | no |
| `/tmp` | 512 MB – 10,240 MB | no |
| Concurrent executions | 1,000 per account per region | yes |
| Concurrency scaling | 1,000 new execution environments every 10 s, per function | no |
| Control-plane API calls | 15 rps **across all control-plane APIs combined**, not per API | no |

The last row is the one that breaks automation: a deployment loop that calls
`UpdateFunctionConfiguration` for forty functions will throttle. `[official]`

Two consequences people miss. First, memory is the only CPU dial — dropping a function from
1,769 MB to 1,024 MB does not save 42%, it halves the CPU and often increases duration enough
to cost more. Second, the 6 MB response ceiling is why "return the report" becomes "return a
presigned S3 URL" at some size, and response streaming (200 MB) changes that ceiling only for
Function URLs and compatible integrations.

## Concurrency, scaling and throttling

- **Reserved concurrency** is both a floor and a ceiling: it guarantees that much capacity to
  the function and forbids it more. Setting it to 0 is the documented way to stop a function
  without deleting it.
- **Provisioned concurrency** keeps initialised environments warm. It costs money whether or
  not traffic arrives, so it belongs on the latency-critical synchronous path and nowhere
  else.
- The account concurrency limit is shared. One function looping at 1,000 concurrent
  invocations throttles every other function in the account and region — reserved concurrency
  on the noisy function is the containment.
- A throttled **synchronous** invocation returns 429 to the caller immediately. A throttled
  **asynchronous** invocation is retried by Lambda for up to six hours with backoff, which
  looks like "nothing happened" rather than an error.

## Cold starts and what actually helps

In rough order of effect: reduce the deployment package and the number of modules imported at
init; move client construction and configuration reads to module scope so they happen once
per environment rather than once per invocation; use arm64 (usually the same or better
latency and cheaper per GB-second); raise memory, because init also gets more CPU. SnapStart
helps JVM-style runtimes with expensive initialisation. VPC attachment no longer adds the
old multi-second penalty — ENI setup is shared — but a VPC without the right endpoints still
adds latency and NAT cost to every AWS API call the function makes.

Anything that stores per-caller state in a module-level variable is a correctness bug, not an
optimisation: execution environments are reused across different callers.

## Event source mappings and at-least-once delivery

Every event source mapping delivers **at least once**. The questions that matter are ordering,
batching and what happens to a failure.

| Source | Ordering | Failure handling to configure |
|---|---|---|
| SQS standard | none | `VisibilityTimeout` ≥ function timeout, redrive policy with DLQ, `FunctionResponseTypes: [ReportBatchItemFailures]` |
| SQS FIFO | per message group | same, plus awareness that a stuck group blocks itself |
| DynamoDB Streams / Kinesis | per shard | `BisectBatchOnFunctionError`, `MaximumRetryAttempts`, `MaximumRecordAgeInSeconds`, on-failure destination |
| Kafka / MSK | per partition | `ReportBatchItemFailures`, consumer-group lag alarm |

The visibility timeout rule is the most frequently violated: if it is shorter than the
function timeout, SQS makes the message visible again while the first invocation is still
running and a second consumer picks it up. AWS's guidance is a visibility timeout of about six
times the function timeout. The symptom is duplicated side effects with no error anywhere.

Without `ReportBatchItemFailures`, one poison record in a batch of ten causes all ten to be
redelivered, forever, until the message ages out — and the nine good records are processed
again each time.

For streams, a rising `IteratorAge` means the consumer is falling behind; the levers are
`BatchSize`, `ParallelizationFactor` and the shard count, in that order of cheapness.

## Idempotency

Because delivery is at-least-once and clients retry, a handler with side effects needs an
idempotency key. Three workable implementations:

- **AWS Lambda Powertools Idempotency** (Python, TypeScript, Java, .NET), backed by a DynamoDB
  table with TTL. It stores the in-progress marker as well as the result, so a concurrent
  duplicate waits rather than double-executing.
- **A conditional write** — `PutItem` with `attribute_not_exists(pk)` — where the business
  operation is itself a single DynamoDB write.
- **The downstream system's own idempotency key** (payment providers all have one). Pass the
  order id, not a generated UUID, or the retry generates a new key and charges twice.

The key must come from the *request*, not from the invocation: a Lambda request id is
different on every retry.

## API Gateway: choosing the type

| | REST API (v1) | HTTP API (v2) | WebSocket |
|---|---|---|---|
| Positioning | full API management | low-cost proxy | bidirectional |
| Relative cost | higher | ~70% cheaper | per message |
| Max integration timeout | 29 s default, raisable on Regional and private only | **30 s, not raisable** | 29 s |
| Payload | 10 MB | 10 MB | 128 KB message / 32 KB frame |
| Usage plans and API keys | yes | no | no |
| Request validation | yes (JSON Schema draft 4) | no | no |
| Caching | yes (0.5–237 GB) | no | no |
| WAF | yes | no (put CloudFront in front) | no |
| Resource policies / private endpoints | yes | no | no |
| JWT authorizer | no (use Cognito authorizer) | yes, native | no |
| Canary deployments | yes | no | no |

Decide this first. The feature set is the API type, and moving between them means rebuilding
routes, authorizers, stages and the deployment pipeline.

Edge-optimized endpoints do **not** cache at the edge; they only shorten the TCP path via
CloudFront POPs. For real edge caching or edge compute, use a Regional endpoint with your own
CloudFront distribution in front.

## Timeouts, and why 504 is usually a design bug

The documented quota for a REST API is an integration timeout of 50 ms to 29 s for all
integration types. It is adjustable for **Regional** and **private** APIs and not adjustable
for edge-optimized ones; AWS notes that raising it above 29 s may require a reduction in the
account's Region-level throttle quota. The HTTP API quota table lists a 30 s maximum marked
not increasable. `[official]`

So a backend that takes 95 seconds cannot sit behind any API Gateway integration. The fix is
to take the work off the request path:

- accept, enqueue to SQS or EventBridge, return `202` with a status URL;
- or start a Step Functions execution and poll or push the result;
- or, for a long *response* rather than long processing, stream it (Lambda Function URL or a
  streaming-capable integration).

Raising the Lambda timeout does the opposite of helping: the client still gets a 504 at the
gateway's limit while the function keeps running and keeps billing.

## Authorizers

- A REST **TOKEN** authorizer caches by the identity source value; an HTTP API or REST
  **REQUEST** authorizer caches by the combination of all declared identity sources. If the
  cached policy is broader than the requested resource, the cache becomes an authorisation
  bypass — return a policy scoped to the specific method ARN, or set the cache TTL to 0 when
  the policy varies per resource.
- Missing identity sources produce 401 before the authorizer is ever invoked, which looks like
  an authorizer bug and is not.
- An HTTP API JWT authorizer caches the issuer's public keys for about two hours; plan key
  rotation with overlap.
- Passing an ID token where the API validates scopes on an access token is the single most
  common 401.

## Step Functions: Standard versus Express

| | Standard | Express |
|---|---|---|
| Max duration | 1 year | 5 minutes |
| Semantics | exactly-once | at-least-once (async) / at-most-once (sync) |
| History | 90 days, queryable via API | CloudWatch Logs only |
| Throughput | ~2,000 executions/s | ~100,000 executions/s |
| Pricing | per state transition | per execution and duration |
| `.sync` / `.waitForTaskToken` | yes | no |

Choose Standard for anything non-idempotent or auditable (payments, fulfilment); Express for
high-volume idempotent processing. The absence of `.waitForTaskToken` on Express is what
usually forces the decision.

For new state machines set `"QueryLanguage": "JSONata"` at the top level: it replaces the five
JSONPath fields (`InputPath`, `Parameters`, `ResultSelector`, `ResultPath`, `OutputPath`) with
`Arguments` and `Output`. Two traps: `Assign` and `Output` are evaluated in parallel, so a
variable assigned in a state is not visible in that same state's `Output`; and a JSONata
expression that resolves to nothing raises `States.QueryEvaluationError` rather than passing
null through.

Every `Task` needs an explicit `Retry` — at minimum `Lambda.ServiceException`,
`Lambda.AWSLambdaException`, `Lambda.SdkClientException` and `States.TaskFailed` — and a
`Catch` that routes to a compensating or failure state. A Task with neither fails the whole
execution on a transient error.

## SQS and EventBridge wiring

- An EventBridge rule target with no `RetryPolicy` and no `DeadLetterConfig` drops events once
  retries are exhausted, silently. Both belong on every rule target.
- EventBridge event patterns match on structure, not on a query language; a pattern that never
  matches produces no error and no metric other than a flat `TriggeredRules`. Test patterns
  with `aws events test-event-pattern` before deploying.
- SQS `DelaySeconds` is capped at 15 minutes, so "retry in an hour" needs Step Functions or a
  scheduler, not a delay queue.
- An SQS queue used as a DLQ needs a retention period at least as long as the source's, or the
  failed messages expire before anyone looks at them.
- SNS fan-out to SQS requires the queue policy to allow `sns.amazonaws.com` with an
  `aws:SourceArn` condition; without the condition it is a confused-deputy hole, and without
  the policy the subscription silently delivers nothing.

<!-- sources: awslabs-agent-plugins, aws-agent-toolkit, aws-builder-samples, aws-docs -->
