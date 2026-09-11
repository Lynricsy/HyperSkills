// checkout-service: OpenTelemetry setup + the two hot paths.
// Node 22, @opentelemetry/sdk-node 2.x, running in Kubernetes behind an
// OTel Collector DaemonSet. Nothing here has been touched since the initial
// instrumentation PR eighteen months ago.
import { NodeSDK } from "@opentelemetry/sdk-node";
import { getNodeAutoInstrumentations } from "@opentelemetry/auto-instrumentations-node";
import { TraceIdRatioBasedSampler } from "@opentelemetry/sdk-trace-base";
import { trace, SpanStatusCode, SpanKind } from "@opentelemetry/api";
import { Counter, Histogram } from "prom-client";
import express from "express";

const sdk = new NodeSDK({
  serviceName: "checkout",
  sampler: new TraceIdRatioBasedSampler(0.05),
  instrumentations: [getNodeAutoInstrumentations()],
});
sdk.start();

const tracer = trace.getTracer("checkout");

const paymentAttempts = new Counter({
  name: "payment_attempts",
  help: "payment attempts",
  labelNames: ["user_id", "order_id", "provider", "error_message"],
});

const checkoutLatency = new Histogram({
  name: "checkout_latency",
  help: "checkout latency in ms",
  labelNames: ["path", "user_id", "status_code"],
});

const app = express();

// POST /api/orders/:orderId/pay
app.post("/api/orders/:orderId/pay", async (req, res) => {
  const t0 = Date.now();
  const { orderId } = req.params;
  const userId = req.header("x-user-id") ?? "anonymous";

  return tracer.startActiveSpan(
    `POST /api/orders/${orderId}/pay`,
    async (span) => {
      span.setAttribute("http.method", "POST");
      span.setAttribute("http.url", req.originalUrl);
      span.setAttribute("user_id", userId);
      try {
        if (!req.body?.card) {
          // Caller sent us garbage.
          span.setStatus({ code: SpanStatusCode.ERROR });
          span.setAttribute("http.status_code", 400);
          res.status(400).json({ error: "card required" });
          return;
        }

        const result = await chargeProvider(orderId, req.body.card);
        span.setAttribute("http.status_code", 200);
        span.setStatus({ code: SpanStatusCode.OK });
        paymentAttempts.inc({
          user_id: userId,
          order_id: orderId,
          provider: "stripe",
          error_message: "",
        });
        res.json(result);
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        span.recordException(err);
        span.setStatus({ code: SpanStatusCode.ERROR });
        console.log(
          `payment failed for order ${orderId} user ${userId}: ${message}`,
        );
        paymentAttempts.inc({
          user_id: userId,
          order_id: orderId,
          provider: "stripe",
          error_message: message,
        });
        res.status(502).json({ error: "payment failed" });
      } finally {
        checkoutLatency.observe(
          { path: req.originalUrl, user_id: userId, status_code: String(res.statusCode) },
          Date.now() - t0,
        );
        span.end();
      }
    },
  );
});

async function chargeProvider(orderId: string, card: unknown) {
  return tracer.startActiveSpan(
    `charge_provider_${orderId}`,
    { kind: SpanKind.CLIENT },
    async (span) => {
      const res = await fetch("https://api.stripe.example/charges", {
        method: "POST",
        body: JSON.stringify({ orderId, card }),
      });
      span.setAttribute("http.status_code", res.status);
      // 4xx from the provider means our request was rejected, but we return
      // a value either way and let the caller sort it out.
      span.setStatus({ code: SpanStatusCode.OK });
      span.end();
      return res.json();
    },
  );
}

// Runs every five minutes from a Kubernetes CronJob-driven HTTP ping.
export async function reconcileAbandonedCarts() {
  const rows = await db.query("SELECT id FROM carts WHERE status = 'abandoned'");
  for (const row of rows) {
    await tracer.startActiveSpan(`expire_cart_${row.id}`, async (span) => {
      await db.query("UPDATE carts SET status = 'expired' WHERE id = $1", [row.id]);
      span.end();
    });
  }
}

app.listen(8080);
// Pod terminates on SIGTERM; nothing else to do here.
