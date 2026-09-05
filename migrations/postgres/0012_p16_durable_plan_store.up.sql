BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 11 AND migration_name = 'p16.plan_source_v1')
        OR EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version >= 12) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'durable plan store requires exact schema version 11';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256', true) IS NULL
        OR current_setting('hwpx_agent.migration_sha256', true) !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'durable plan store requires its migration digest';
    END IF;
END
$$;

CREATE TABLE hwpx_agent.compiled_plan_records (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    plan_id varchar(124) NOT NULL,
    source_revision_id uuid NOT NULL,
    source_graph_sha256 character(64) NOT NULL,
    created_by_subject_sha256 character(64) NOT NULL,
    plan_sha256 character(64) NOT NULL,
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
    CONSTRAINT compiled_plan_records_project_fk FOREIGN KEY (tenant_id, project_id)
        REFERENCES hwpx_agent.projects (tenant_id, project_id) ON DELETE RESTRICT,
    CONSTRAINT compiled_plan_records_revision_fk FOREIGN KEY (tenant_id, project_id, source_revision_id)
        REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id) ON DELETE RESTRICT,
    CONSTRAINT compiled_plan_records_plan_id_format CHECK (
        plan_id ~ '^plan_[A-Za-z0-9_-]{8,120}$'
    ),
    CONSTRAINT compiled_plan_records_digest_format CHECK (
        source_graph_sha256 ~ '^[0-9a-f]{64}$'
        AND plan_sha256 ~ '^[0-9a-f]{64}$'
        AND aad_sha256 ~ '^[0-9a-f]{64}$'
        AND ciphertext_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT compiled_plan_records_subject_format CHECK (
        created_by_subject_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT compiled_plan_records_crypto_shape CHECK (
        encryption_algorithm = 'AES-256-GCM'
        AND encryption_key_ref ~ '^[a-z][a-z0-9]*(\.[a-z0-9][a-z0-9_-]*)+$'
        AND octet_length(nonce) = 12
        AND plaintext_bytes BETWEEN 1 AND 1048576
        AND octet_length(ciphertext) = plaintext_bytes + 16
    ),
    CONSTRAINT compiled_plan_records_lifetime CHECK (
        stored_at_unix_seconds >= 0
        AND expires_at_unix_seconds > stored_at_unix_seconds
        AND expires_at_unix_seconds <= stored_at_unix_seconds + 900
    )
);

CREATE FUNCTION hwpx_agent.validate_compiled_plan_record()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
DECLARE
    v_entries bigint;
    v_plaintext_bytes bigint;
BEGIN
    PERFORM pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtextextended(NEW.tenant_id::text, 16)
    );
    IF NOT EXISTS (
        SELECT 1
        FROM hwpx_agent.projects AS project
        JOIN hwpx_agent.tenants AS tenant
          ON tenant.tenant_id = project.tenant_id AND tenant.state = 'active'
        JOIN hwpx_agent.branches AS branch
          ON branch.tenant_id = project.tenant_id
         AND branch.project_id = project.project_id
         AND branch.is_default
         AND branch.head_revision_id = project.head_revision_id
         AND branch.head_generation = project.head_generation
        JOIN hwpx_agent.project_acl AS access
          ON access.tenant_id = project.tenant_id
         AND access.project_id = project.project_id
         AND access.subject_sha256 = NEW.created_by_subject_sha256
         AND access.role IN ('editor', 'owner')
        JOIN hwpx_agent.revisions AS revision
          ON revision.tenant_id = project.tenant_id
         AND revision.project_id = project.project_id
         AND revision.revision_id = project.head_revision_id
         AND revision.validation_state = 'verified'
        JOIN hwpx_agent.revision_graph_bindings AS binding
          ON binding.tenant_id = revision.tenant_id
         AND binding.project_id = revision.project_id
         AND binding.revision_id = revision.revision_id
         AND binding.source_artifact_id = revision.source_artifact_id
         AND binding.graph_sha256 = NEW.source_graph_sha256
        JOIN hwpx_agent.artifacts AS artifact
          ON artifact.tenant_id = revision.tenant_id
         AND artifact.artifact_id = revision.source_artifact_id
         AND artifact.artifact_kind = 'source'
         AND artifact.storage_state = 'available'
         AND artifact.validation_state = 'verified'
        WHERE project.tenant_id = NEW.tenant_id
          AND project.project_id = NEW.project_id
          AND project.head_revision_id = NEW.source_revision_id
          AND project.state = 'active'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'compiled plan requires the exact current authorized source';
    END IF;
    SELECT count(*), COALESCE(sum(plaintext_bytes), 0)
      INTO v_entries, v_plaintext_bytes
      FROM hwpx_agent.compiled_plan_records
     WHERE tenant_id = NEW.tenant_id
       AND expires_at_unix_seconds > NEW.stored_at_unix_seconds;
    IF v_entries >= 256 OR v_plaintext_bytes + NEW.plaintext_bytes > 16777216 THEN
        RAISE EXCEPTION USING ERRCODE = '54000', MESSAGE = 'compiled plan capacity exhausted';
    END IF;
    RETURN NEW;
END
$$;

CREATE TRIGGER compiled_plan_records_validate
BEFORE INSERT ON hwpx_agent.compiled_plan_records
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.validate_compiled_plan_record();

CREATE FUNCTION hwpx_agent.reject_compiled_plan_change()
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
             AND class.relname = 'compiled_plan_records'
       )) THEN
        RETURN OLD;
    END IF;
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'compiled plan records are immutable';
END
$$;

CREATE TRIGGER compiled_plan_records_immutable
BEFORE UPDATE OR DELETE ON hwpx_agent.compiled_plan_records
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_compiled_plan_change();

CREATE INDEX compiled_plan_records_expiry_idx
    ON hwpx_agent.compiled_plan_records (tenant_id, expires_at_unix_seconds, project_id, plan_id);

CREATE FUNCTION hwpx_agent.purge_expired_compiled_plan_records()
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
        pg_catalog.hashtextextended(v_tenant_id::text, 16)
    );
    WITH expired AS (
        SELECT record.ctid
        FROM hwpx_agent.compiled_plan_records AS record
        WHERE record.tenant_id = v_tenant_id
          AND record.expires_at_unix_seconds <=
              floor(extract(epoch FROM pg_catalog.statement_timestamp()))::bigint
        ORDER BY record.expires_at_unix_seconds, record.project_id, record.plan_id
        LIMIT 256
        FOR UPDATE
    )
    DELETE FROM hwpx_agent.compiled_plan_records AS record
    USING expired
    WHERE record.ctid = expired.ctid;
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END
$$;

ALTER TABLE hwpx_agent.compiled_plan_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.compiled_plan_records FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.compiled_plan_records
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());
REVOKE ALL ON TABLE hwpx_agent.compiled_plan_records FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.validate_compiled_plan_record() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.reject_compiled_plan_change() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.purge_expired_compiled_plan_records() FROM PUBLIC;

INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (12, 'p16.durable_plan_store_v1', current_setting('hwpx_agent.migration_sha256'));
COMMIT;
