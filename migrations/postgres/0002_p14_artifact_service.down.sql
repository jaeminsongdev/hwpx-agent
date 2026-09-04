BEGIN;

DO $$
BEGIN
    IF current_setting('hwpx_agent.allow_destructive_rollback', true) IS DISTINCT FROM 'on' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 artifact service rollback requires explicit hwpx_agent.allow_destructive_rollback=on';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 2 AND migration_name = 'p14.artifact_service_v1'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 artifact service migration version 2 is not installed';
    END IF;
END
$$;

DROP TABLE hwpx_agent.artifact_acl;

DROP TRIGGER artifact_service_manager_required ON hwpx_agent.artifacts;
DROP TRIGGER artifacts_protect_service_identity ON hwpx_agent.artifacts;
DROP FUNCTION hwpx_agent.require_artifact_manager();
DROP FUNCTION hwpx_agent.bump_artifact_acl_generation();
DROP FUNCTION hwpx_agent.protect_artifact_acl_identity();
DROP FUNCTION hwpx_agent.protect_artifact_service_identity();

ALTER TABLE hwpx_agent.artifacts
    DROP CONSTRAINT artifacts_object_key_unique,
    DROP CONSTRAINT artifacts_object_key_binding,
    DROP CONSTRAINT artifacts_service_metadata_complete,
    DROP CONSTRAINT artifacts_legacy_recovery_complete,
    DROP CONSTRAINT artifacts_legacy_verified_time_order,
    DROP CONSTRAINT artifacts_legacy_quarantine_code_format,
    DROP CONSTRAINT artifacts_legacy_storage_state_value,
    DROP CONSTRAINT artifacts_authorization_generation_range,
    DROP CONSTRAINT artifacts_scanner_signature_format,
    DROP CONSTRAINT artifacts_scanner_engine_format,
    DROP CONSTRAINT artifacts_validation_state_value,
    DROP CONSTRAINT artifacts_ciphertext_digest_format,
    DROP CONSTRAINT artifacts_aad_digest_format,
    DROP CONSTRAINT artifacts_encryption_nonce_size,
    DROP CONSTRAINT artifacts_encryption_algorithm,
    DROP CONSTRAINT artifacts_filename_format,
    DROP CONSTRAINT artifacts_service_metadata_version;

UPDATE hwpx_agent.artifacts
SET storage_state = legacy_storage_state,
    quarantine_reason_code = legacy_quarantine_reason_code,
    verified_at = legacy_verified_at
WHERE legacy_storage_state IS NOT NULL;

ALTER TABLE hwpx_agent.artifacts
    DROP COLUMN legacy_verified_at,
    DROP COLUMN legacy_quarantine_reason_code,
    DROP COLUMN legacy_storage_state,
    DROP COLUMN authorization_generation,
    DROP COLUMN scanner_signature_version,
    DROP COLUMN scanner_engine_ref,
    DROP COLUMN validation_state,
    DROP COLUMN ciphertext_sha256,
    DROP COLUMN aad_sha256,
    DROP COLUMN encryption_nonce,
    DROP COLUMN encryption_algorithm,
    DROP COLUMN object_key,
    DROP COLUMN filename,
    DROP COLUMN service_metadata_version;

ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions WHERE version = 2;
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;

COMMIT;
