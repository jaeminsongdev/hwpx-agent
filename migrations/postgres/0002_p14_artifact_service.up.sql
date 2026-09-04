BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM hwpx_agent.schema_versions
        WHERE version = 1 AND migration_name = 'p14.metadata_v1'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 artifact service migration requires p14.metadata_v1';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version = 2) THEN
        RAISE EXCEPTION USING
            ERRCODE = '42710',
            MESSAGE = 'P14 artifact service migration version 2 already exists';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256', true)
        !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            MESSAGE = 'P14 artifact service migration requires its exact SHA-256';
    END IF;
END
$$;

ALTER TABLE hwpx_agent.artifacts
    ADD COLUMN service_metadata_version smallint,
    ADD COLUMN filename text,
    ADD COLUMN object_key text,
    ADD COLUMN encryption_algorithm text,
    ADD COLUMN encryption_nonce bytea,
    ADD COLUMN aad_sha256 character(64),
    ADD COLUMN ciphertext_sha256 character(64),
    ADD COLUMN validation_state text,
    ADD COLUMN scanner_engine_ref text,
    ADD COLUMN scanner_signature_version text,
    ADD COLUMN authorization_generation bigint,
    ADD COLUMN legacy_storage_state text,
    ADD COLUMN legacy_quarantine_reason_code text,
    ADD COLUMN legacy_verified_at timestamptz;

-- Version 1 rows have no ciphertext identity. Preserve their metadata and references, but never
-- expose them as downloadable content until a reviewed service ingestion creates a version 1
-- service record.
UPDATE hwpx_agent.artifacts
SET legacy_storage_state = storage_state,
    legacy_quarantine_reason_code = quarantine_reason_code,
    legacy_verified_at = verified_at,
    storage_state = 'orphaned',
    quarantine_reason_code = NULL,
    verified_at = NULL
WHERE storage_state IN ('available', 'quarantined');

ALTER TABLE hwpx_agent.artifacts
    ADD CONSTRAINT artifacts_service_metadata_version CHECK (
        service_metadata_version IS NULL OR service_metadata_version = 1
    ),
    ADD CONSTRAINT artifacts_filename_format CHECK (
        filename IS NULL
        OR (
            length(filename) BETWEEN 1 AND 255
            AND filename NOT IN ('.', '..')
            AND filename !~ '[\\/[:cntrl:]]'
            AND filename !~ '^[[:space:]]|[[:space:]]$'
        )
    ),
    ADD CONSTRAINT artifacts_encryption_algorithm CHECK (
        encryption_algorithm IS NULL OR encryption_algorithm = 'AES-256-GCM'
    ),
    ADD CONSTRAINT artifacts_encryption_nonce_size CHECK (
        encryption_nonce IS NULL OR octet_length(encryption_nonce) = 12
    ),
    ADD CONSTRAINT artifacts_aad_digest_format CHECK (
        aad_sha256 IS NULL OR aad_sha256 ~ '^[0-9a-f]{64}$'
    ),
    ADD CONSTRAINT artifacts_ciphertext_digest_format CHECK (
        ciphertext_sha256 IS NULL OR ciphertext_sha256 ~ '^[0-9a-f]{64}$'
    ),
    ADD CONSTRAINT artifacts_validation_state_value CHECK (
        validation_state IS NULL
        OR validation_state IN ('unverified', 'verified', 'failed', 'quarantined')
    ),
    ADD CONSTRAINT artifacts_scanner_engine_format CHECK (
        scanner_engine_ref IS NULL
        OR scanner_engine_ref ~ '^[a-z][a-z0-9]*(\.[a-z0-9_-]+)+$'
    ),
    ADD CONSTRAINT artifacts_scanner_signature_format CHECK (
        scanner_signature_version IS NULL
        OR scanner_signature_version ~ '^[A-Za-z0-9._-]{1,128}$'
    ),
    ADD CONSTRAINT artifacts_authorization_generation_range CHECK (
        authorization_generation IS NULL OR authorization_generation >= 1
    ),
    ADD CONSTRAINT artifacts_legacy_storage_state_value CHECK (
        legacy_storage_state IS NULL OR legacy_storage_state IN ('available', 'quarantined')
    ),
    ADD CONSTRAINT artifacts_legacy_quarantine_code_format CHECK (
        legacy_quarantine_reason_code IS NULL
        OR legacy_quarantine_reason_code ~ '^[A-Z][A-Z0-9_]{2,63}$'
    ),
    ADD CONSTRAINT artifacts_legacy_verified_time_order CHECK (
        legacy_verified_at IS NULL OR legacy_verified_at >= created_at
    ),
    ADD CONSTRAINT artifacts_legacy_recovery_complete CHECK (
        (
            legacy_storage_state IS NULL
            AND legacy_quarantine_reason_code IS NULL
            AND legacy_verified_at IS NULL
        )
        OR (
            service_metadata_version IS NULL
            AND storage_state = 'orphaned'
            AND legacy_storage_state IN ('available', 'quarantined')
            AND (
                (
                    legacy_storage_state = 'quarantined'
                    AND legacy_quarantine_reason_code IS NOT NULL
                )
                OR (
                    legacy_storage_state = 'available'
                    AND legacy_quarantine_reason_code IS NULL
                )
            )
        )
    ),
    ADD CONSTRAINT artifacts_service_metadata_complete CHECK (
        (
            service_metadata_version IS NULL
            AND filename IS NULL
            AND object_key IS NULL
            AND encryption_algorithm IS NULL
            AND encryption_nonce IS NULL
            AND aad_sha256 IS NULL
            AND ciphertext_sha256 IS NULL
            AND validation_state IS NULL
            AND scanner_engine_ref IS NULL
            AND scanner_signature_version IS NULL
            AND authorization_generation IS NULL
            AND storage_state IN ('staged', 'orphaned', 'purging')
        )
        OR (
            service_metadata_version = 1
            AND filename IS NOT NULL
            AND object_key IS NOT NULL
            AND encryption_algorithm = 'AES-256-GCM'
            AND encryption_nonce IS NOT NULL
            AND aad_sha256 IS NOT NULL
            AND ciphertext_sha256 IS NOT NULL
            AND validation_state IS NOT NULL
            AND scanner_engine_ref IS NOT NULL
            AND scanner_signature_version IS NOT NULL
            AND authorization_generation IS NOT NULL
            AND storage_state IN ('available', 'quarantined')
            AND (
                (storage_state = 'available' AND validation_state = 'verified')
                OR (
                    storage_state = 'quarantined'
                    AND validation_state IN ('unverified', 'failed', 'quarantined')
                )
            )
        )
    ),
    ADD CONSTRAINT artifacts_object_key_binding CHECK (
        object_key IS NULL
        OR object_key = concat(
            'artifacts/v1/', replace(tenant_id::text, '-', ''), '/', artifact_kind, '/',
            storage_state, '/', content_sha256, '.aes256gcm'
        )
    ),
    ADD CONSTRAINT artifacts_object_key_unique UNIQUE (object_key);

CREATE TABLE hwpx_agent.artifact_acl (
    tenant_id uuid NOT NULL,
    artifact_id uuid NOT NULL,
    subject_sha256 character(64) NOT NULL,
    can_read boolean NOT NULL DEFAULT false,
    can_manage boolean NOT NULL DEFAULT false,
    can_read_quarantine boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, artifact_id, subject_sha256),
    CONSTRAINT artifact_acl_artifact_fk FOREIGN KEY (tenant_id, artifact_id)
        REFERENCES hwpx_agent.artifacts (tenant_id, artifact_id) ON DELETE CASCADE,
    CONSTRAINT artifact_acl_subject_format CHECK (subject_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT artifact_acl_permission_nonempty CHECK (
        can_read OR can_manage OR can_read_quarantine
    )
);

CREATE FUNCTION hwpx_agent.protect_artifact_service_identity()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    IF ROW(
        NEW.service_metadata_version,
        NEW.filename,
        NEW.encryption_algorithm,
        NEW.encryption_nonce,
        NEW.aad_sha256,
        NEW.ciphertext_sha256,
        NEW.scanner_engine_ref,
        NEW.scanner_signature_version,
        NEW.legacy_storage_state,
        NEW.legacy_quarantine_reason_code,
        NEW.legacy_verified_at
    ) IS DISTINCT FROM ROW(
        OLD.service_metadata_version,
        OLD.filename,
        OLD.encryption_algorithm,
        OLD.encryption_nonce,
        OLD.aad_sha256,
        OLD.ciphertext_sha256,
        OLD.scanner_engine_ref,
        OLD.scanner_signature_version,
        OLD.legacy_storage_state,
        OLD.legacy_quarantine_reason_code,
        OLD.legacy_verified_at
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'artifact encryption and scanner identity is immutable';
    END IF;
    IF NEW.authorization_generation < OLD.authorization_generation THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'artifact authorization generation cannot decrease';
    END IF;
    IF ROW(NEW.storage_state, NEW.object_key, NEW.validation_state, NEW.quarantine_reason_code)
        IS DISTINCT FROM ROW(
            OLD.storage_state, OLD.object_key, OLD.validation_state, OLD.quarantine_reason_code
        ) AND NEW.authorization_generation IS DISTINCT FROM OLD.authorization_generation + 1 THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'artifact security state change requires one authorization generation increment';
    END IF;
    RETURN NEW;
END
$$;

CREATE FUNCTION hwpx_agent.protect_artifact_acl_identity()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    IF ROW(NEW.tenant_id, NEW.artifact_id, NEW.subject_sha256)
        IS DISTINCT FROM ROW(OLD.tenant_id, OLD.artifact_id, OLD.subject_sha256) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'artifact ACL identity is immutable';
    END IF;
    RETURN NEW;
END
$$;

CREATE FUNCTION hwpx_agent.bump_artifact_acl_generation()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
DECLARE
    target_tenant uuid;
    target_artifact uuid;
    acl_count bigint;
BEGIN
    target_tenant := COALESCE(NEW.tenant_id, OLD.tenant_id);
    target_artifact := COALESCE(NEW.artifact_id, OLD.artifact_id);

    IF NOT EXISTS (
        SELECT 1
        FROM hwpx_agent.artifacts
        WHERE tenant_id = target_tenant
          AND artifact_id = target_artifact
          AND service_metadata_version = 1
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'artifact ACL requires service metadata version 1';
    END IF;

    SELECT count(*) INTO acl_count
    FROM hwpx_agent.artifact_acl
    WHERE tenant_id = target_tenant AND artifact_id = target_artifact;

    IF TG_OP <> 'INSERT' OR acl_count > 1 THEN
        UPDATE hwpx_agent.artifacts
        SET authorization_generation = authorization_generation + 1
        WHERE tenant_id = target_tenant AND artifact_id = target_artifact;
    END IF;
    RETURN NULL;
END
$$;

CREATE FUNCTION hwpx_agent.require_artifact_manager()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
DECLARE
    target_tenant uuid;
    target_artifact uuid;
BEGIN
    target_tenant := COALESCE(NEW.tenant_id, OLD.tenant_id);
    target_artifact := COALESCE(NEW.artifact_id, OLD.artifact_id);
    IF EXISTS (
        SELECT 1
        FROM hwpx_agent.artifacts
        WHERE tenant_id = target_tenant
          AND artifact_id = target_artifact
          AND service_metadata_version = 1
    ) AND NOT EXISTS (
        SELECT 1
        FROM hwpx_agent.artifact_acl
        WHERE tenant_id = target_tenant
          AND artifact_id = target_artifact
          AND can_manage
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'artifact ACL must retain at least one manager';
    END IF;
    RETURN NULL;
END
$$;

CREATE TRIGGER artifacts_protect_service_identity
BEFORE UPDATE ON hwpx_agent.artifacts
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.protect_artifact_service_identity();

CREATE TRIGGER artifact_acl_protect_identity
BEFORE UPDATE ON hwpx_agent.artifact_acl
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.protect_artifact_acl_identity();

CREATE TRIGGER artifact_acl_touch_updated_at
BEFORE UPDATE ON hwpx_agent.artifact_acl
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.touch_updated_at();

CREATE TRIGGER artifact_acl_bump_generation
AFTER INSERT OR UPDATE OR DELETE ON hwpx_agent.artifact_acl
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.bump_artifact_acl_generation();

CREATE CONSTRAINT TRIGGER artifact_acl_manager_required
AFTER INSERT OR UPDATE OR DELETE ON hwpx_agent.artifact_acl
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.require_artifact_manager();

CREATE CONSTRAINT TRIGGER artifact_service_manager_required
AFTER INSERT OR UPDATE ON hwpx_agent.artifacts
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
WHEN (NEW.service_metadata_version = 1)
EXECUTE FUNCTION hwpx_agent.require_artifact_manager();

CREATE INDEX artifact_acl_subject_idx
    ON hwpx_agent.artifact_acl (tenant_id, subject_sha256, artifact_id);

ALTER TABLE hwpx_agent.artifact_acl ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.artifact_acl FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.artifact_acl
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());

REVOKE ALL ON TABLE hwpx_agent.artifact_acl FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.protect_artifact_service_identity() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.protect_artifact_acl_identity() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.bump_artifact_acl_generation() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.require_artifact_manager() FROM PUBLIC;

INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (
    2,
    'p14.artifact_service_v1',
    current_setting('hwpx_agent.migration_sha256')
);

COMMIT;
