-- migrations/0042_add_settled_at.sql
-- Target: PostgreSQL 16, table public.payments, 210M rows, ~900 writes/s at peak.

BEGIN;

ALTER TABLE payments
  ADD COLUMN settled_at timestamptz NOT NULL DEFAULT now();

UPDATE payments
   SET settled_at = created_at
 WHERE settled_at IS NULL;

CREATE INDEX idx_payments_settled_at ON payments (settled_at DESC);

COMMIT;
