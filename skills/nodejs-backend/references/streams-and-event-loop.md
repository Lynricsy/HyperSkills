# Streams, backpressure and the event loop

Verified against: Node.js 24 LTS

## Contents

- [The rule and the reason](#the-rule-and-the-reason)
- [pipeline, always](#pipeline-always)
- [Async-generator transforms](#async-generator-transforms)
- [Streaming a query result out of a handler](#streaming-a-query-result-out-of-a-handler)
- [Manual backpressure](#manual-backpressure)
- [Web streams and the two worlds](#web-streams-and-the-two-worlds)
- [What blocks the event loop](#what-blocks-the-event-loop)
- [Measuring: which of the three is it](#measuring-which-of-the-three-is-it)
- [Caching and request coalescing](#caching-and-request-coalescing)

## The rule and the reason

Node's concurrency comes from one thread doing something else while I/O is in
flight. Two things break it, and they have opposite symptoms:

- **Buffering** a whole payload. Memory scales with payload size times
  concurrency; the process dies at some traffic level nobody predicted, and the
  crash is a container OOM kill with no stack.
- **Blocking** the thread. Latency on every other in-flight request rises, so
  the alert fires on an endpoint that has nothing to do with the change.

Both are invisible in development, where payloads are small and concurrency is
one.

## pipeline, always

```ts
import { pipeline } from 'node:stream/promises'
import { createReadStream, createWriteStream } from 'node:fs'
import { createGzip } from 'node:zlib'

await pipeline(createReadStream(input), createGzip(), createWriteStream(output))
```

`pipeline` is not a nicer `.pipe()`. It is the only form that propagates an
error to the caller and destroys every stream in the chain. With `.pipe()`, a
failure in the middle leaves the source open and the error goes to an `error`
listener you probably did not attach — which is an unhandled `error` event, and
therefore fatal.

The promise version from `node:stream/promises` also gives the awaited
completion point that lets a handler return only after the transfer finished.

## Async-generator transforms

A generator is a valid pipeline stage, and it is far easier to get right than a
`Transform` subclass — no `_transform`, no callback, no manual `destroy`:

```ts
async function* parseLines(source: AsyncIterable<Buffer>): AsyncGenerator<string> {
  let tail = ''
  for await (const chunk of source) {
    tail += chunk.toString('utf8')
    const lines = tail.split('\n')
    tail = lines.pop() ?? ''      // the last piece may be a partial line
    for (const line of lines) yield line
  }
  if (tail.length > 0) yield tail
}

await pipeline(createReadStream('orders.csv'), parseLines, insertBatch)
```

The partial-line carry is the detail that gets skipped. A chunk boundary lands
mid-line whenever the file is bigger than the highWaterMark, so a transform that
splits each chunk independently corrupts one record per chunk — and the tests
pass because the fixture fits in one chunk.

For line-oriented reading where no transform is needed, `readline`'s async
iterator is simpler:

```ts
for await (const line of createInterface({ input: createReadStream(path), crlfDelay: Infinity })) {
  await handle(line)
}
```

## Streaming a query result out of a handler

Buffering a result set is the version of this problem that reaches production
most often, because it starts as a table with 200 rows.

```ts
// Buffers everything twice: all rows, then the whole serialised body.
const rows = await db.selectAll(table)
return c.text(rows.map((r) => Object.values(r).join(',')).join('\n'))
```

The fix has three parts, all required:

1. Ask the driver for a **cursor or async iterator** instead of an array. A
   driver that only returns arrays needs keyset pagination in a loop.
2. Serialise **per row**, not per result set.
3. Hand the stream to the framework so it can apply backpressure from the
   socket. Each branch reference shows the exact call: Fastify accepts a
   `Readable` from the handler, Hono has the streaming helpers, NestJS has
   `StreamableFile`.

Also set the response headers before the first byte — once the stream starts,
the status and headers are already sent and no error handler can change them
(see `validation-and-errors.md`).

## Manual backpressure

When there is no pipeline — writing to a socket or a third-party sink in a loop
— honour the return value of `write()`:

```ts
import { once } from 'node:events'

for (const chunk of chunks) {
  if (!writable.write(chunk)) {
    await once(writable, 'drain')   // the sink's buffer is full: wait
  }
}
```

Ignoring the `false` means every unwritten chunk queues inside your process.
That is the same OOM as buffering, arriving more slowly and therefore harder to
attribute.

## Web streams and the two worlds

Node has two stream families. `node:stream` (`Readable`, `Writable`) is what
`fs`, `http` and most drivers speak. Web streams (`ReadableStream`,
`WritableStream`) are what `fetch` bodies and the Web-standard frameworks speak.

Convert rather than reimplement:

```ts
import { Readable, Writable } from 'node:stream'

const nodeStream = Readable.fromWeb(webReadable)
const webStream = Readable.toWeb(nodeStream)
```

This matters most in Hono on Node, where the app is written against
`Response`/`ReadableStream` but the data source is a Node driver or `fs`. Wrap
at the boundary, once, and keep the rest of the code in one family.

Backpressure still applies in the web family — `ReadableStream`'s `pull` is only
called when the consumer asks — but a source that pushes with
`controller.enqueue()` in a tight loop ignores it exactly like a `write()`
whose return value is discarded.

## What blocks the event loop

Three categories, in the order they appear in real code:

- **Synchronous filesystem and crypto.** `readFileSync`, `writeFileSync`,
  `existsSync` in a request path, `execSync`, synchronous hashing or key
  derivation. Boot-time use is fine — nothing is waiting yet.
- **Large parse/serialise.** `JSON.parse` and `JSON.stringify` are synchronous
  and O(size). A 20 MB body is tens of milliseconds of dead time on every
  request. Body size limits are the real fix; a response schema-driven
  serialiser helps because it does not walk unknown structure.
- **Unbounded loops over data.** A `for` loop over a full result set, a regex
  with catastrophic backtracking on user input, sorting a large array. Adding
  `await` inside does not help unless the awaited thing actually yields.

The escape hatch for genuinely CPU-bound work is a worker thread or a queue —
see the last section of `lifecycle-and-shutdown.md` for which to pick.

One more not-obvious blocker: `UV_THREADPOOL_SIZE` (default 4) bounds the pool
used by `fs`, DNS lookups and `zlib`. Heavy concurrent file or compression work
saturates it and looks exactly like a blocked event loop, except loop delay
stays low. Raising it trades memory for parallelism and is a last resort, after
confirming the queue is the bottleneck.

## Measuring: which of the three is it

"The endpoint is slow" has three shapes and they need different fixes. Measure
first (rule 22), quote the number, and re-measure after.

| Observation | Meaning | Next step |
|---|---|---|
| High event-loop delay | something is blocking the thread | `--cpu-prof`, find the synchronous frame |
| Low delay, slow requests | the wait is downstream | count and time the queries or upstream calls |
| Memory grows with traffic and never returns | buffering or an unbounded cache | two heap snapshots, compare retained size |
| Process never exits after work finishes | open handles, not slowness | enumerate handles (`lifecycle-and-shutdown.md`) |

Commands:

```bash
node --cpu-prof --cpu-prof-dir=./prof src/main.ts   # .cpuprofile, load in DevTools
node --heap-prof src/main.ts                        # sampling allocation profile
node --inspect src/main.ts                          # attach for heap snapshots
```

Event-loop delay comes from `monitorEventLoopDelay` in `node:perf_hooks`:

```ts
import { monitorEventLoopDelay } from 'node:perf_hooks'

const h = monitorEventLoopDelay({ resolution: 20 })   // 20 ms sampling
h.enable()
setInterval(() => log.info({ p99Ms: h.percentile(99) / 1e6 }, 'loop delay'), 10_000).unref()
```

Percentiles are in nanoseconds, hence the division. Export this: it is the one
number that distinguishes "we are blocking" from "we are waiting", and it is
cheap enough to leave on permanently.

## Caching and request coalescing

Two distinct problems, two distinct tools:

- **Repeated identical work in one process** — a bounded in-memory cache with an
  eviction policy. Unbounded is a memory leak with a friendly name; a `Map` used
  as a cache with no eviction is the most common one in this ecosystem.
- **Concurrent identical work** — coalescing, so ten simultaneous requests for
  the same key make one upstream call and share the promise. Without it, a cold
  cache under load stampedes the thing it was protecting.

Both are process-local, so they multiply by replica count and vanish on deploy.
Anything that must be shared or must survive a restart belongs in a real store,
which is out of scope here.

<!-- sources: mcollina-skills, nodejs-docs, fastify-docs, hono-docs, nestjs-docs -->
