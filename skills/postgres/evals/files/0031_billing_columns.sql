-- migrations/0031_billing_columns.sql
-- Target: production PostgreSQL 18.6. `orders` has 180 million rows and takes
-- ~4000 writes/second around the clock. The deploy pipeline runs this file
-- inside a single transaction with a 30s statement_timeout and no lock_timeout.

BEGIN;

-- 1. every order needs a billing timestamp and a public reference
ALTER TABLE orders ADD COLUMN billed_at  timestamptz NOT NULL DEFAULT now();
ALTER TABLE orders ADD COLUMN public_ref uuid        NOT NULL DEFAULT gen_random_uuid();

-- 2. and a currency, which must never be null
ALTER TABLE orders ADD COLUMN currency text;
UPDATE orders SET currency = 'USD';
ALTER TABLE orders ALTER COLUMN currency SET NOT NULL;

-- 3. amounts overflowed integer last quarter
ALTER TABLE orders ALTER COLUMN amount_cents TYPE bigint;

-- 4. the reporting team wants this lookup to be fast
CREATE INDEX orders_customer_billed ON orders (customer_id, billed_at DESC);

-- 5. finally enforce the relationship we have always assumed
ALTER TABLE orders
    ADD CONSTRAINT orders_customer_fk
    FOREIGN KEY (customer_id) REFERENCES customers (id);

-- 6. drop the column the old billing service used
ALTER TABLE orders DROP COLUMN legacy_invoice_blob;

COMMIT;
