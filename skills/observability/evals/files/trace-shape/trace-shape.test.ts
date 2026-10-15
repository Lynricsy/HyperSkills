// Trace-shape tests for the checkout handler. Written against @opentelemetry 1.x;
// package.json now pins the 2.x SDK packages.
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import { context, propagation, SpanKind, SpanStatusCode, trace } from "@opentelemetry/api";
import { W3CTraceContextPropagator } from "@opentelemetry/core";
import { NodeTracerProvider } from "@opentelemetry/sdk-trace-node";
import { InMemorySpanExporter, SimpleSpanProcessor } from "@opentelemetry/sdk-trace-base";

const exporter = new InMemorySpanExporter();

beforeAll(() => {
  const provider = new NodeTracerProvider();
  provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
  provider.register({ propagator: new W3CTraceContextPropagator() });
});

afterEach(() => exporter.reset());

const tracer = trace.getTracer("checkout");

// Minimal stand-in for the real handler: SERVER span from the incoming headers,
// one CLIENT span to the payment provider underneath it.
async function handleCheckout(headers: Record<string, string>) {
  const parent = propagation.extract(context.active(), headers);
  await tracer.startActiveSpan("POST /api/checkout", { kind: SpanKind.SERVER }, parent, async (server) => {
    await tracer.startActiveSpan("POST", { kind: SpanKind.CLIENT }, async (client) => {
      client.setStatus({ code: SpanStatusCode.OK });
      client.end();
    });
    server.end();
  });
}

describe("checkout trace shape", () => {
  it("has no orphan CLIENT spans", async () => {
    await handleCheckout({});
    const spans = exporter.getFinishedSpans();
    const orphans = spans.filter((s) => s.kind === SpanKind.CLIENT && !s.parentSpanId);
    expect(orphans).toHaveLength(0);
  });

  it("records the request when the edge proxy forwards an unsampled traceparent", async () => {
    // Our edge proxy samples 1% and forwards flags=00 for the rest; this service
    // must still record every request it handles.
    await handleCheckout({
      traceparent: "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-00",
    });
    const names = exporter.getFinishedSpans().map((s) => s.name);
    expect(names).toContain("POST /api/checkout");
  });
});
