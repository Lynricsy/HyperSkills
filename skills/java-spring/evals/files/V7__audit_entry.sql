-- Deliberately no foreign key to payment: audit rows are written in their own transaction.
CREATE TABLE audit_entry (
    id          BIGSERIAL    PRIMARY KEY,
    action      VARCHAR(40)  NOT NULL,
    payment_id  UUID         NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX audit_entry_payment_idx ON audit_entry (payment_id);
