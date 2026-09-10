-- Self-hosted PostgreSQL 18.6. Multi-tenant SaaS, no Supabase, no cloud
-- platform. The API connects as the role `app_user` and sets the tenant per
-- request. `documents` has ~2 million rows across ~4000 tenants.

CREATE TABLE documents (
    id         bigserial PRIMARY KEY,
    tenant_id  bigint NOT NULL,
    author_id  bigint NOT NULL,
    title      text   NOT NULL,
    body       text
);

CREATE TABLE tenant_members (
    user_id   bigint NOT NULL,
    tenant_id bigint NOT NULL,
    role      text   NOT NULL,
    PRIMARY KEY (user_id, tenant_id)
);

-- Per-request the API runs:  SET app.tenant_id = '<id>';  SET app.user_id = '<id>';

CREATE FUNCTION current_tenant() RETURNS bigint
LANGUAGE plpgsql STABLE AS $$
BEGIN
    RETURN current_setting('app.tenant_id')::bigint;
END $$;

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy A: everything a tenant can touch
CREATE POLICY documents_tenant ON documents
    FOR ALL
    USING (tenant_id = current_tenant());

-- Policy B: editors may also reach documents in tenants they belong to
CREATE POLICY documents_editor ON documents
    FOR ALL
    USING (EXISTS (
        SELECT 1 FROM tenant_members m
        WHERE m.user_id = current_setting('app.user_id')::bigint
          AND m.tenant_id = documents.tenant_id
          AND m.role = 'editor'
    ));

-- Reporting jobs connect as `reporting`, which owns the table.
-- Nightly batch jobs connect as `etl`, which has BYPASSRLS.

-- Observed problems:
--   * A dashboard query that used to take 30ms now takes about 4 seconds.
--   * A support engineer managed to move a document into another tenant with
--     UPDATE documents SET tenant_id = 12345 WHERE id = 987;
--   * The reporting role sees every tenant's rows.
