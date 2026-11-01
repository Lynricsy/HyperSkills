import { WorkerEntrypoint } from "cloudflare:workers";
import { Client } from "pg";

async function loadOrder(env: Env, orderId: string) {
  const client = new Client({ connectionString: env.HYPERDRIVE.connectionString });
  await client.connect();
  try {
    // Five sequential round trips per request; each depends on the previous result.
    const order = await client.query("SELECT * FROM orders WHERE id = $1", [orderId]);
    const customer = await client.query("SELECT * FROM customers WHERE id = $1", [order.rows[0].customer_id]);
    const lines = await client.query("SELECT * FROM order_lines WHERE order_id = $1", [orderId]);
    const stock = await client.query("SELECT * FROM stock WHERE sku = ANY($1)", [lines.rows.map((l) => l.sku)]);
    const shipping = await client.query("SELECT * FROM shipments WHERE order_id = $1", [orderId]);
    return { order: order.rows[0], customer: customer.rows[0], lines: lines.rows, stock: stock.rows, shipping: shipping.rows };
  } finally {
    await client.end();
  }
}

// Called over a service binding (RPC) by admin-dashboard, which runs the same five queries per order.
export class OrdersService extends WorkerEntrypoint<Env> {
  async getOrder(orderId: string) {
    return loadOrder(this.env, orderId);
  }
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/orders/")) {
      return Response.json(await loadOrder(env, url.pathname.split("/")[2]));
    }
    if (url.pathname === "/webhooks/payments") {
      const body = await request.text();
      const ok = await verifySignature(body, request.headers.get("x-signature") ?? "", env.WEBHOOK_SECRET);
      return ok ? new Response("ok") : new Response("bad signature", { status: 401 });
    }
    return new Response("not found", { status: 404 });
  },
};

async function verifySignature(body: string, signature: string, secret: string): Promise<boolean> {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["verify"]);
  const sig = Uint8Array.from(signature.match(/../g) ?? [], (h) => parseInt(h, 16));
  return crypto.subtle.verify("HMAC", key, sig, new TextEncoder().encode(body));
}
