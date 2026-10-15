// Loyalty-points service at https://points.example.com. Browser clients only; no third-party embeds.
const express = require("express");
const session = require("express-session");
const multer = require("multer");
const { pool } = require("./db"); // node-postgres Pool
const { requireAuth, requireRole } = require("./auth"); // 401 / 403 unless req.session.user satisfies them
const adminRouter = require("./admin");
const storage = require("./storage"); // uploads to the bucket behind https://files.points-usercontent.net

const app = express();
app.use(
  session({
    secret: process.env.SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
    cookie: { httpOnly: true, secure: true, sameSite: "lax" },
  }),
);
app.use(express.json()); // only parses Content-Type: application/json

app.use("/admin", requireAuth, requireRole("support"), adminRouter);

// Members transfer points to each other. Called by the SPA with fetch() and a JSON body.
app.post("/api/transfers", requireAuth, async (req, res) => {
  const { toMemberId, points } = req.body;
  if (!Number.isInteger(points) || points <= 0) return res.status(400).end();
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const { rows } = await client.query(
      "UPDATE members SET points = points - $1 WHERE id = $2 AND points >= $1 RETURNING points",
      [points, req.session.user.id],
    );
    if (rows.length === 0) {
      await client.query("ROLLBACK");
      return res.status(409).json({ error: "insufficient points" });
    }
    await client.query("UPDATE members SET points = points + $1 WHERE id = $2", [points, toMemberId]);
    await client.query("COMMIT");
    res.json({ balance: rows[0].points });
  } catch (err) {
    await client.query("ROLLBACK");
    throw err;
  } finally {
    client.release();
  }
});

// Members attach receipts (PDF, images, or the HTML e-mail receipt saved from their mail client).
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 5 * 1024 * 1024 } });
app.post("/api/receipts", requireAuth, upload.single("receipt"), async (req, res) => {
  const key = `receipts/${req.session.user.id}/${crypto.randomUUID()}`;
  await storage.put(key, req.file.buffer, {
    contentType: "application/octet-stream",
    contentDisposition: "attachment",
  });
  await pool.query("INSERT INTO receipts (member_id, object_key, original_name) VALUES ($1, $2, $3)", [
    req.session.user.id,
    key,
    req.file.originalname,
  ]);
  res.status(201).json({ url: `https://files.points-usercontent.net/${key}` });
});

// Claim the one-time welcome bonus.
app.post("/api/welcome-bonus", requireAuth, async (req, res) => {
  const memberId = req.session.user.id;
  const existing = await pool.query("SELECT 1 FROM bonus_claims WHERE member_id = $1 AND kind = 'welcome'", [
    memberId,
  ]);
  if (existing.rowCount > 0) return res.status(409).json({ error: "already claimed" });
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    await client.query("INSERT INTO bonus_claims (member_id, kind) VALUES ($1, 'welcome')", [memberId]);
    await client.query("UPDATE members SET points = points + 500 WHERE id = $1", [memberId]);
    await client.query("COMMIT");
  } catch (err) {
    await client.query("ROLLBACK");
    if (err.code === "23505") return res.status(409).json({ error: "already claimed" });
    throw err;
  } finally {
    client.release();
  }
  res.json({ ok: true });
});

app.listen(3000);
