// Support tooling. Mounted by app.js; see there for how requests reach this router.
const express = require("express");
const { pool } = require("./db");

const router = express.Router();

router.get("/members/:id", async (req, res) => {
  const { rows } = await pool.query("SELECT id, email, points, created_at FROM members WHERE id = $1", [
    req.params.id,
  ]);
  if (rows.length === 0) return res.sendStatus(404);
  res.json(rows[0]);
});

router.post("/members/:id/adjust", async (req, res) => {
  const delta = Number(req.body.delta);
  if (!Number.isInteger(delta) || Math.abs(delta) > 10_000) return res.status(400).end();
  await pool.query("UPDATE members SET points = points + $1 WHERE id = $2", [delta, req.params.id]);
  await pool.query("INSERT INTO audit_log (actor_id, action, target_id, detail) VALUES ($1, 'adjust', $2, $3)", [
    req.session.user.id,
    req.params.id,
    JSON.stringify({ delta }),
  ]);
  res.sendStatus(204);
});

module.exports = router;
