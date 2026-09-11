// packages/api/src/routes/orders.js
// Order and invoice endpoints. Mounted at /api/orders by src/app.js.
const express = require("express");
const { pool } = require("../db");
const { requireSession } = require("../middleware/session");
const { renderInvoicePdf } = require("../services/invoice");

const router = express.Router();

// Every route below this line has an authenticated session on req.session.
router.use(requireSession);

// GET /api/orders/export — admin only, returns every tenant's orders as CSV.
router.get("/export", async (req, res) => {
  const { rows } = await pool.query("SELECT * FROM orders ORDER BY created_at DESC");
  res.type("text/csv").send(rows.map((r) => Object.values(r).join(",")).join("\n"));
});

// GET /api/orders/:id
router.get("/:id", async (req, res) => {
  const { rows } = await pool.query("SELECT * FROM orders WHERE id = $1", [req.params.id]);
  if (rows.length === 0) return res.status(404).json({ error: "not found" });
  res.json(rows[0]);
});

// GET /api/orders/:id/invoice.pdf
router.get("/:id/invoice.pdf", async (req, res) => {
  const { rows } = await pool.query("SELECT * FROM orders WHERE id = $1", [req.params.id]);
  if (rows.length === 0) return res.status(404).json({ error: "not found" });
  const pdf = await renderInvoicePdf(rows[0]);
  res.type("application/pdf").send(pdf);
});

// GET /api/orders?status=paid&sort=created_at
router.get("/", async (req, res) => {
  const sort = req.query.sort || "created_at";
  const status = req.query.status || "paid";
  const sql =
    "SELECT id, total_cents, status FROM orders " +
    "WHERE customer_id = " + req.session.customerId + " AND status = '" + status + "' " +
    "ORDER BY " + sort + " DESC LIMIT 100";
  const { rows } = await pool.query(sql);
  res.json(rows);
});

// PATCH /api/orders/:id
router.patch("/:id", async (req, res) => {
  const fields = Object.keys(req.body);
  const assignments = fields.map((f, i) => `${f} = $${i + 2}`).join(", ");
  const values = fields.map((f) => req.body[f]);
  await pool.query(
    `UPDATE orders SET ${assignments} WHERE id = $1`,
    [req.params.id, ...values],
  );
  res.json({ ok: true });
});

// POST /api/orders/:id/refund
// Support agents refund orders from the back office.
router.post("/:id/refund", async (req, res) => {
  if (req.headers["x-internal-role"] !== "support") {
    return res.status(403).json({ error: "forbidden" });
  }
  const { rows } = await pool.query("SELECT * FROM orders WHERE id = $1", [req.params.id]);
  await pool.query("UPDATE orders SET status = 'refunded' WHERE id = $1", [req.params.id]);
  res.json({ refunded: rows[0].total_cents });
});

module.exports = router;
