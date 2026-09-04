BEGIN;

DO $$
BEGIN
    IF current_setting('hwpx_agent.allow_p14_retention_mirror_rollback', true)
        IS DISTINCT FROM 'yes' THEN
        RAISE EXCEPTION USING ERRCODE = '55000',
            MESSAGE = 'P14 retention mirror rollback requires explicit gate';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 9 AND migration_name = 'p14.retention_local_mirror_v1'
    ) OR EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version > 9) THEN
        RAISE EXCEPTION USING ERRCODE = '55000',
            MESSAGE = 'P14 retention mirror rollback requires exact schema version 9';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.retention_policies)
       OR EXISTS (SELECT 1 FROM hwpx_agent.legal_holds)
       OR EXISTS (SELECT 1 FROM hwpx_agent.artifact_deletion_requests)
       OR EXISTS (SELECT 1 FROM hwpx_agent.artifact_purge_receipts)
       OR EXISTS (SELECT 1 FROM hwpx_agent.project_local_mirrors)
       OR EXISTS (SELECT 1 FROM hwpx_agent.local_mirror_conflicts)
       OR EXISTS (
            SELECT 1 FROM hwpx_agent.artifacts
            WHERE storage_state IN ('tombstoned', 'purged')
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000',
            MESSAGE = 'P14 retention mirror rollback refuses version 9 data';
    END IF;
END
$$;

DROP FUNCTION hwpx_agent.resolve_local_mirror_conflict_v1(uuid, uuid, character, uuid, text, uuid);
DROP FUNCTION hwpx_agent.complete_local_mirror_push_v1(uuid, uuid, character, uuid, uuid, uuid);
DROP FUNCTION hwpx_agent.begin_local_mirror_push_v1(uuid, uuid, character, uuid, uuid, uuid, integer);
DROP FUNCTION hwpx_agent.queue_local_mirror_plan_v1(uuid, uuid, character, uuid, character, character);
DROP FUNCTION hwpx_agent.register_local_mirror_v1(uuid, uuid, character, uuid, character, uuid, uuid, bigint, character);
DROP FUNCTION hwpx_agent.complete_artifact_purge_v1(uuid, uuid, character, uuid, uuid, bigint, uuid, text, character);
DROP FUNCTION hwpx_agent.record_artifact_purge_failure_v1(uuid, uuid, character, uuid, uuid, bigint, character);
DROP FUNCTION hwpx_agent.claim_artifact_purge_v1(uuid, uuid, character, uuid, uuid, uuid, integer);
DROP FUNCTION hwpx_agent.request_artifact_deletion_v1(uuid, uuid, character, uuid, uuid, text);
DROP FUNCTION hwpx_agent.release_legal_hold_v1(uuid, uuid, character, uuid);
DROP FUNCTION hwpx_agent.create_legal_hold_v1(uuid, uuid, character, uuid, uuid, text);
DROP FUNCTION hwpx_agent.create_retention_policy_v1(uuid, text, character, integer, bigint, bigint, bigint, bigint, bigint, bigint, bigint);
DROP FUNCTION hwpx_agent.has_active_legal_hold_v1(uuid, uuid, uuid);
DROP FUNCTION hwpx_agent.artifact_referenced_outside_project_v1(uuid, uuid, uuid);
DROP FUNCTION hwpx_agent.artifact_referenced_by_project_v1(uuid, uuid, uuid);
DROP FUNCTION hwpx_agent.require_retention_role_v1(uuid, uuid, character, boolean);

DROP TRIGGER cleanup_tasks_retention_reference_guard ON hwpx_agent.cleanup_tasks;
DROP TRIGGER cancellations_retention_reference_guard ON hwpx_agent.job_cancellation_requests;
DROP TRIGGER idempotency_retention_reference_guard ON hwpx_agent.idempotency_records;
DROP TRIGGER job_attempts_retention_reference_guard ON hwpx_agent.job_attempts;
DROP TRIGGER jobs_retention_reference_guard ON hwpx_agent.jobs;
DROP TRIGGER revisions_retention_reference_guard ON hwpx_agent.revisions;
DROP FUNCTION hwpx_agent.guard_new_artifact_reference_v1();

DROP TABLE hwpx_agent.local_mirror_conflicts;
DROP TABLE hwpx_agent.project_local_mirrors;
DROP TABLE hwpx_agent.artifact_purge_receipts;
DROP TABLE hwpx_agent.artifact_deletion_requests;
DROP TABLE hwpx_agent.legal_holds;
DROP TABLE hwpx_agent.retention_policy_rules;
DROP TABLE hwpx_agent.retention_policies;
DROP FUNCTION hwpx_agent.protect_p14_09_identity();

ALTER TABLE hwpx_agent.artifacts
    DROP CONSTRAINT artifacts_storage_state_value,
    DROP CONSTRAINT artifacts_quarantine_consistency,
    DROP CONSTRAINT artifacts_service_metadata_complete_v9,
    DROP CONSTRAINT artifacts_object_key_binding_v9;

ALTER TABLE hwpx_agent.artifacts
    ADD CONSTRAINT artifacts_storage_state_value CHECK (
        storage_state IN ('staged', 'available', 'quarantined', 'orphaned', 'purging')
    ),
    ADD CONSTRAINT artifacts_quarantine_consistency CHECK (
        (storage_state = 'quarantined' AND quarantine_reason_code IS NOT NULL)
        OR (storage_state <> 'quarantined' AND quarantine_reason_code IS NULL)
    ),
    ADD CONSTRAINT artifacts_service_metadata_complete_v8 CHECK (
        (
            service_metadata_version IS NULL
            AND filename IS NULL AND object_key IS NULL
            AND encryption_algorithm IS NULL AND encryption_nonce IS NULL
            AND aad_sha256 IS NULL AND ciphertext_sha256 IS NULL
            AND validation_state IS NULL AND scanner_engine_ref IS NULL
            AND scanner_signature_version IS NULL AND authorization_generation IS NULL
            AND storage_state IN ('staged', 'orphaned', 'purging')
        )
        OR (
            service_metadata_version = 1
            AND filename IS NOT NULL AND object_key IS NOT NULL
            AND encryption_algorithm = 'AES-256-GCM'
            AND encryption_nonce IS NOT NULL
            AND aad_sha256 IS NOT NULL AND ciphertext_sha256 IS NOT NULL
            AND validation_state IS NOT NULL
            AND scanner_engine_ref IS NOT NULL
            AND scanner_signature_version IS NOT NULL
            AND authorization_generation IS NOT NULL
            AND storage_state IN ('available', 'quarantined', 'purging')
            AND (
                (storage_state IN ('available', 'purging') AND validation_state = 'verified')
                OR (storage_state = 'quarantined'
                    AND validation_state IN ('unverified', 'failed', 'quarantined'))
            )
        )
    ),
    ADD CONSTRAINT artifacts_object_key_binding_v8 CHECK (
        object_key IS NULL
        OR object_key = concat(
            'artifacts/v1/', replace(tenant_id::text, '-', ''), '/', artifact_kind, '/',
            CASE WHEN storage_state = 'purging' THEN 'available' ELSE storage_state END,
            '/', content_sha256, '.aes256gcm'
        )
    );

ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions
WHERE version = 9 AND migration_name = 'p14.retention_local_mirror_v1';
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;

COMMIT;
