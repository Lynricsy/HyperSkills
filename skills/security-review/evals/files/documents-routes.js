// packages/api/src/routes/documents.js — mounted at /api/documents by src/app.js.
// requireSession verifies the session JWT and sets req.user = { id, tenantId, role }.
const router = require("express").Router();
const { db } = require("../db");
const { requireSession } = require("../middleware/session");
const shares = require("../services/shares");
const storage = require("../services/storage");

router.use(requireSession);

function sameTenant(user, doc) {
  return doc.tenant_id === user.tenantId;
}

// GET /api/documents/search?q=invoice
router.get("/search", async (req, res) => {
  const tenantId = req.headers["x-tenant-id"];
  const rows = await db.any(
    "SELECT id, title FROM documents WHERE tenant_id = $1 AND title ILIKE $2 LIMIT 50",
    [tenantId, `%${req.query.q}%`],
  );
  res.json(rows);
});

// GET /api/documents/:id — metadata
router.get("/:id", async (req, res) => {
  const doc = await db.oneOrNone("SELECT * FROM documents WHERE id = $1", [req.params.id]);
  if (!doc || !sameTenant(req.user, doc)) return res.status(404).end();
  res.json(doc);
});

// GET /api/documents/:id/download?tenantId=<tenant>
router.get("/:id/download", async (req, res) => {
  const doc = await db.oneOrNone("SELECT * FROM documents WHERE id = $1", [req.params.id]);
  if (!doc || doc.tenant_id !== req.query.tenantId) return res.status(404).end();
  storage.stream(doc.blob_key).pipe(res);
});

// POST /api/documents/:id/share  { tenantId, expiresInDays }
// Returns a public, unauthenticated link to the file.
router.post("/:id/share", async (req, res) => {
  const doc = await db.oneOrNone("SELECT * FROM documents WHERE id = $1", [req.params.id]);
  if (!doc || doc.tenant_id !== req.body.tenantId) return res.status(404).end();
  const link = await shares.create(doc.id, req.body.expiresInDays || 7);
  res.status(201).json({ url: link.url });
});

// DELETE /api/documents/:id — tenant admins clean up their workspace
router.delete("/:id", async (req, res) => {
  if (req.user.role !== "admin") return res.status(403).end();
  await db.none("DELETE FROM documents WHERE id = $1", [req.params.id]);
  res.status(204).end();
});

module.exports = router;
