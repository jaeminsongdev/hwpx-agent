BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 12 AND migration_name = 'p16.durable_plan_store_v1')
        OR EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version >= 13) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'plan review evidence requires exact schema version 12';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256', true) IS NULL
        OR current_setting('hwpx_agent.migration_sha256', true) !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'plan review evidence requires its migration digest';
    END IF;
END
$$;

CREATE TABLE hwpx_agent.plan_review_evidence_records (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    plan_id varchar(124) NOT NULL,
    created_by_subject_sha256 character(64) NOT NULL,
    compiled_plan_sha256 character(64) NOT NULL,
    route_set_sha256 character(64) NOT NULL,
    semantic_diff_sha256 character(64) NOT NULL,
    result_graph_sha256 character(64) NOT NULL,
    evidence_sha256 character(64) NOT NULL,
    plaintext_bytes bigint NOT NULL,
    encryption_algorithm varchar(32) NOT NULL,
    encryption_key_ref varchar(128) NOT NULL,
    nonce bytea NOT NULL,
    aad_sha256 character(64) NOT NULL,
    ciphertext_sha256 character(64) NOT NULL,
    ciphertext bytea NOT NULL,
    stored_at_unix_seconds bigint NOT NULL,
    expires_at_unix_seconds bigint NOT NULL,
    PRIMARY KEY (tenant_id, project_id, plan_id),
    CONSTRAINT plan_review_evidence_plan_fk FOREIGN KEY (tenant_id, project_id, plan_id)
        REFERENCES hwpx_agent.compiled_plan_records (tenant_id, project_id, plan_id) ON DELETE RESTRICT,
    CONSTRAINT plan_review_evidence_plan_id_format CHECK (
        plan_id ~ '^plan_[A-Za-z0-9_-]{8,120}$'
    ),
    CONSTRAINT plan_review_evidence_digest_format CHECK (
        created_by_subject_sha256 ~ '^[0-9a-f]{64}$'
        AND compiled_plan_sha256 ~ '^[0-9a-f]{64}$'
        AND route_set_sha256 ~ '^[0-9a-f]{64}$'
        AND semantic_diff_sha256 ~ '^[0-9a-f]{64}$'
        AND result_graph_sha256 ~ '^[0-9a-f]{64}$'
        AND evidence_sha256 ~ '^[0-9a-f]{64}$'
        AND aad_sha256 ~ '^[0-9a-f]{64}$'
        AND ciphertext_sha256 ~ '^[0-9a-f]{64}$'
        AND compiled_plan_sha256 <> repeat('0', 64)
        AND route_set_sha256 <> repeat('0', 64)
        AND semantic_diff_sha256 <> repeat('0', 64)
        AND result_graph_sha256 <> repeat('0', 64)
        AND evidence_sha256 <> repeat('0', 64)
        AND aad_sha256 <> repeat('0', 64)
        AND ciphertext_sha256 <> repeat('0', 64)
    ),
    CONSTRAINT plan_review_evidence_crypto_shape CHECK (
        encryption_algorithm = 'AES-256-GCM'
        AND encryption_key_ref ~ '^[a-z][a-z0-9]*(\.[a-z0-9][a-z0-9_-]*)+$'
        AND octet_length(nonce) = 12
        AND plaintext_bytes BETWEEN 1 AND 1048576
        AND octet_length(ciphertext) = plaintext_bytes + 16
    ),
    CONSTRAINT plan_review_evidence_lifetime CHECK (
        stored_at_unix_seconds >= 0
        AND expires_at_unix_seconds > stored_at_unix_seconds
        AND expires_at_unix_seconds <= stored_at_unix_seconds + 900
    )
);

CREATE FUNCTION hwpx_agent.validate_plan_review_evidence_record()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
DECLARE
    v_entries bigint;
    v_plaintext_bytes bigint;
BEGIN
    PERFORM pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtextextended(NEW.tenant_id::text, 17)
    );
    IF NOT EXISTS (
        SELECT 1
        FROM hwpx_agent.compiled_plan_records AS plan
        WHERE plan.tenant_id = NEW.tenant_id
          AND plan.project_id = NEW.project_id
          AND plan.plan_id = NEW.plan_id
          AND plan.created_by_subject_sha256 = NEW.created_by_subject_sha256
          AND plan.plan_sha256 = NEW.compiled_plan_sha256
          AND plan.stored_at_unix_seconds <= NEW.stored_at_unix_seconds
          AND plan.expires_at_unix_seconds >= NEW.expires_at_unix_seconds
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'plan review evidence requires its exact live compiled plan';
    END IF;
    SELECT count(*), COALESCE(sum(plaintext_bytes), 0)
      INTO v_entries, v_plaintext_bytes
      FROM hwpx_agent.plan_review_evidence_records
     WHERE tenant_id = NEW.tenant_id
       AND expires_at_unix_seconds > NEW.stored_at_unix_seconds;
    IF v_entries >= 256 OR v_plaintext_bytes + NEW.plaintext_bytes > 16777216 THEN
        RAISE EXCEPTION USING ERRCODE = '54000', MESSAGE = 'plan review evidence capacity exhausted';
    END IF;
    RETURN NEW;
END
$$;

CREATE TRIGGER plan_review_evidence_records_validate
BEFORE INSERT ON hwpx_agent.plan_review_evidence_records
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.validate_plan_review_evidence_record();

CREATE FUNCTION hwpx_agent.reject_plan_review_evidence_change()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    IF TG_OP = 'DELETE'
       AND OLD.expires_at_unix_seconds <=
           floor(extract(epoch FROM pg_catalog.statement_timestamp()))::bigint
       AND current_user = pg_catalog.pg_get_userbyid((
           SELECT class.relowner
           FROM pg_catalog.pg_class AS class
           JOIN pg_catalog.pg_namespace AS namespace ON namespace.oid = class.relnamespace
           WHERE namespace.nspname = 'hwpx_agent'
             AND class.relname = 'plan_review_evidence_records'
       )) THEN
        RETURN OLD;
    END IF;
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'plan review evidence records are immutable';
END
$$;

CREATE TRIGGER plan_review_evidence_records_immutable
BEFORE UPDATE OR DELETE ON hwpx_agent.plan_review_evidence_records
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_plan_review_evidence_change();

CREATE INDEX plan_review_evidence_expiry_idx
    ON hwpx_agent.plan_review_evidence_records
       (tenant_id, expires_at_unix_seconds, project_id, plan_id);

CREATE FUNCTION hwpx_agent.purge_expired_plan_review_evidence_records()
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
SET row_security = off
AS $$
DECLARE
    v_tenant_id uuid;
    v_deleted bigint;
BEGIN
    v_tenant_id := hwpx_agent.current_tenant_id();
    PERFORM pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtextextended(v_tenant_id::text, 17)
    );
    WITH expired AS (
        SELECT record.ctid
        FROM hwpx_agent.plan_review_evidence_records AS record
        WHERE record.tenant_id = v_tenant_id
          AND record.expires_at_unix_seconds <=
              floor(extract(epoch FROM pg_catalog.statement_timestamp()))::bigint
        ORDER BY record.expires_at_unix_seconds, record.project_id, record.plan_id
        LIMIT 256
        FOR UPDATE
    )
    DELETE FROM hwpx_agent.plan_review_evidence_records AS record
    USING expired
    WHERE record.ctid = expired.ctid;
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END
$$;

ALTER TABLE hwpx_agent.plan_review_evidence_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.plan_review_evidence_records FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.plan_review_evidence_records
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());
REVOKE ALL ON TABLE hwpx_agent.plan_review_evidence_records FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.validate_plan_review_evidence_record() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.reject_plan_review_evidence_change() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.purge_expired_plan_review_evidence_records() FROM PUBLIC;

INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (13, 'p16.plan_review_evidence_v1', current_setting('hwpx_agent.migration_sha256'));
COMMIT;
