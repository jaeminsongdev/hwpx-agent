BEGIN;

DO $$
BEGIN
    IF current_setting('hwpx_agent.allow_destructive_rollback', true) IS DISTINCT FROM 'on' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 cancel cleanup rollback requires explicit hwpx_agent.allow_destructive_rollback=on';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 8 AND migration_name = 'p14.cancel_cleanup_v1'
    ) OR EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions WHERE version > 8
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 cancel cleanup rollback requires exact latest schema version 8';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.job_cancellation_requests)
       OR EXISTS (SELECT 1 FROM hwpx_agent.job_effect_markers)
       OR EXISTS (SELECT 1 FROM hwpx_agent.cleanup_tasks)
       OR EXISTS (
            SELECT 1 FROM hwpx_agent.jobs
            WHERE state_machine_version = 2
              AND (cancellation_requested_at IS NOT NULL OR state = 'cancelled')
       )
       OR EXISTS (
            SELECT 1 FROM hwpx_agent.job_attempts
            WHERE state_machine_version = 2 AND state = 'cancelled'
       )
       OR EXISTS (
            SELECT 1 FROM hwpx_agent.idempotency_records
            WHERE record_version = 2 AND state = 'terminal_failure'
              AND attempt_count = 0 AND terminal_error_code = 'JOB_CANCELLED'
       )
       OR EXISTS (
            SELECT 1 FROM hwpx_agent.artifacts
            WHERE service_metadata_version = 1 AND storage_state = 'purging'
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 cancel cleanup rollback refuses remaining version 8 data';
    END IF;
END
$$;

DROP FUNCTION hwpx_agent.complete_cleanup_task_v1(
    uuid, character, uuid, uuid, uuid, integer, bigint, text, character, character
);
DROP FUNCTION hwpx_agent.claim_cleanup_task_v1(
    uuid, character, uuid, uuid, integer, character
);
DROP FUNCTION hwpx_agent.queue_orphan_cleanup_v1(
    uuid, uuid, character, uuid, uuid, uuid, character
);
DROP FUNCTION hwpx_agent.finalize_job_cancellation_v1(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    uuid, uuid, character
);
DROP FUNCTION hwpx_agent.mark_job_effect_phase_v1(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, text, character
);
DROP FUNCTION hwpx_agent.request_job_cancellation_v1(
    uuid, uuid, character, uuid, uuid, uuid, uuid, character
);
DROP FUNCTION hwpx_agent.cleanup_artifact_qualified_v1(uuid, character, uuid);
DROP FUNCTION hwpx_agent.cleanup_artifact_is_referenced_v1(uuid, uuid);

DROP TRIGGER cleanup_task_reject_delete ON hwpx_agent.cleanup_tasks;
DROP TRIGGER job_effect_marker_reject_delete ON hwpx_agent.job_effect_markers;
DROP TRIGGER job_cancellation_reject_delete ON hwpx_agent.job_cancellation_requests;
DROP TRIGGER cleanup_task_identity_guard ON hwpx_agent.cleanup_tasks;
DROP TRIGGER job_effect_marker_identity_guard ON hwpx_agent.job_effect_markers;
DROP TRIGGER job_cancellation_identity_guard ON hwpx_agent.job_cancellation_requests;
DROP FUNCTION hwpx_agent.protect_cancel_cleanup_identity();

DROP TABLE hwpx_agent.job_cancellation_requests;
DROP TABLE hwpx_agent.job_effect_markers;
DROP TABLE hwpx_agent.cleanup_tasks;

ALTER TABLE hwpx_agent.artifacts
    DROP CONSTRAINT artifacts_service_metadata_complete_v8,
    DROP CONSTRAINT artifacts_object_key_binding_v8,
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
    );

ALTER TABLE hwpx_agent.idempotency_records
    DROP CONSTRAINT idempotency_terminal_consistency,
    ADD CONSTRAINT idempotency_terminal_consistency CHECK (
        (
            record_version = 1
            AND (
                (state = 'claimed' AND result_revision_id IS NULL AND receipt_artifact_id IS NULL)
                OR (
                    state = 'terminal_success' AND result_revision_id IS NOT NULL
                    AND receipt_artifact_id IS NOT NULL AND terminal_error_code IS NULL
                )
                OR (
                    state IN ('terminal_failure', 'outcome_unknown')
                    AND result_revision_id IS NULL AND receipt_artifact_id IS NOT NULL
                    AND terminal_error_code IS NOT NULL
                )
            )
        )
        OR (
            record_version = 2
            AND (
                (
                    state = 'claimed' AND attempt_count = 0
                    AND result_revision_id IS NULL AND receipt_artifact_id IS NULL
                    AND terminal_error_code IS NULL AND retry_not_before IS NULL
                    AND last_retry_class IS NULL
                )
                OR (
                    state = 'in_progress' AND attempt_count > 0
                    AND result_revision_id IS NULL AND receipt_artifact_id IS NULL
                    AND terminal_error_code IS NULL AND retry_not_before IS NULL
                )
                OR (
                    state = 'retry_pending' AND attempt_count > 0
                    AND result_revision_id IS NULL AND receipt_artifact_id IS NOT NULL
                    AND terminal_error_code IS NULL AND retry_not_before IS NOT NULL
                    AND last_retry_class IN (
                        'transient_storage', 'transient_network', 'automation_no_effect'
                    )
                )
                OR (
                    state = 'outcome_unknown' AND attempt_count > 0
                    AND result_revision_id IS NULL AND receipt_artifact_id IS NOT NULL
                    AND terminal_error_code = 'OUTCOME_UNKNOWN'
                    AND retry_not_before IS NULL AND last_retry_class = 'automation_unknown'
                )
                OR (
                    state = 'terminal_success' AND attempt_count > 0
                    AND result_revision_id IS NOT NULL AND receipt_artifact_id IS NOT NULL
                    AND terminal_error_code IS NULL AND retry_not_before IS NULL
                )
                OR (
                    state = 'terminal_failure' AND attempt_count > 0
                    AND result_revision_id IS NULL AND receipt_artifact_id IS NOT NULL
                    AND terminal_error_code IS NOT NULL AND retry_not_before IS NULL
                )
            )
        )
    );

ALTER TABLE hwpx_agent.jobs
    DROP CONSTRAINT jobs_state_machine_complete_v8,
    ADD CONSTRAINT jobs_state_machine_complete_v7 CHECK (
        (
            state_machine_version IS NULL
            AND active_execution_id IS NULL
            AND lease_issued_at IS NULL
        )
        OR (
            state_machine_version = 1
            AND cancellation_requested_at IS NULL
            AND (
                (
                    state = 'queued' AND attempt_count = 0
                    AND lease_owner_agent_id IS NULL AND active_execution_id IS NULL
                    AND fencing_token = 0 AND lease_issued_at IS NULL
                    AND lease_expires_at IS NULL AND result_revision_id IS NULL
                    AND terminal_error_code IS NULL AND completed_at IS NULL
                )
                OR (
                    state IN ('leased', 'staged', 'executing', 'validating')
                    AND attempt_count = 1 AND lease_owner_agent_id IS NOT NULL
                    AND active_execution_id IS NOT NULL AND fencing_token = 1
                    AND lease_issued_at IS NOT NULL AND lease_expires_at > lease_issued_at
                    AND lease_expires_at <= lease_issued_at + interval '1 hour'
                    AND result_revision_id IS NULL AND terminal_error_code IS NULL
                    AND completed_at IS NULL
                )
                OR (
                    state IN ('succeeded', 'failed') AND attempt_count = 1
                    AND lease_owner_agent_id IS NULL AND active_execution_id IS NULL
                    AND fencing_token = 1 AND lease_issued_at IS NULL
                    AND lease_expires_at IS NULL AND completed_at IS NOT NULL
                )
            )
        )
        OR (
            state_machine_version = 2
            AND cancellation_requested_at IS NULL
            AND attempt_count BETWEEN 0 AND 10
            AND fencing_token = attempt_count
            AND (
                (
                    state = 'queued' AND attempt_count = 0
                    AND lease_owner_agent_id IS NULL AND active_execution_id IS NULL
                    AND lease_issued_at IS NULL AND lease_expires_at IS NULL
                    AND result_revision_id IS NULL AND terminal_error_code IS NULL
                    AND completed_at IS NULL
                )
                OR (
                    state = 'retry_pending' AND attempt_count > 0
                    AND lease_owner_agent_id IS NULL AND active_execution_id IS NULL
                    AND lease_issued_at IS NULL AND lease_expires_at IS NULL
                    AND result_revision_id IS NULL AND terminal_error_code IS NULL
                    AND completed_at IS NULL
                )
                OR (
                    state IN ('leased', 'staged', 'executing', 'validating')
                    AND attempt_count > 0 AND lease_owner_agent_id IS NOT NULL
                    AND active_execution_id IS NOT NULL AND lease_issued_at IS NOT NULL
                    AND lease_expires_at > lease_issued_at
                    AND lease_expires_at <= lease_issued_at + interval '1 hour'
                    AND result_revision_id IS NULL AND terminal_error_code IS NULL
                    AND completed_at IS NULL
                )
                OR (
                    state = 'unknown_outcome' AND attempt_count > 0
                    AND lease_owner_agent_id IS NULL AND active_execution_id IS NULL
                    AND lease_issued_at IS NULL AND lease_expires_at IS NULL
                    AND result_revision_id IS NULL
                    AND terminal_error_code = 'OUTCOME_UNKNOWN'
                    AND completed_at IS NULL
                )
                OR (
                    state = 'succeeded' AND attempt_count > 0
                    AND lease_owner_agent_id IS NULL AND active_execution_id IS NULL
                    AND lease_issued_at IS NULL AND lease_expires_at IS NULL
                    AND result_revision_id IS NOT NULL
                    AND terminal_error_code IS NULL AND completed_at IS NOT NULL
                )
                OR (
                    state = 'failed' AND attempt_count > 0
                    AND lease_owner_agent_id IS NULL AND active_execution_id IS NULL
                    AND lease_issued_at IS NULL AND lease_expires_at IS NULL
                    AND result_revision_id IS NULL
                    AND terminal_error_code IS NOT NULL AND completed_at IS NOT NULL
                )
            )
        )
    );

ALTER TABLE hwpx_agent.job_attempts
    DROP CONSTRAINT job_attempts_state_machine_complete_v8,
    ADD CONSTRAINT job_attempts_state_machine_complete_v7 CHECK (
        (
            state_machine_version IS NULL
            AND lease_expires_at IS NULL AND updated_at IS NULL
        )
        OR (
            state_machine_version = 1
            AND attempt_no = 1 AND fencing_token = 1
            AND state IN ('leased', 'running', 'succeeded', 'failed')
            AND lease_expires_at > started_at
            AND lease_expires_at <= started_at + interval '1 hour'
            AND updated_at >= started_at
            AND (completed_at IS NULL OR updated_at >= completed_at)
        )
        OR (
            state_machine_version = 2
            AND attempt_no BETWEEN 1 AND 10
            AND fencing_token = attempt_no
            AND state IN ('leased', 'running', 'succeeded', 'failed', 'unknown_outcome')
            AND lease_expires_at > started_at
            AND lease_expires_at <= started_at + interval '1 hour'
            AND updated_at >= started_at
            AND (completed_at IS NULL OR updated_at >= completed_at)
        )
    );

DO $$
DECLARE
    v_job_guard text;
    v_attempt_guard text;
    v_job_consistency text;
    v_idempotency_consistency text;
BEGIN
    SELECT job_guard, attempt_guard, job_consistency, idempotency_consistency
    INTO STRICT v_job_guard, v_attempt_guard, v_job_consistency, v_idempotency_consistency
    FROM hwpx_agent.cancel_cleanup_v1_rollback_functions WHERE singleton;
    EXECUTE v_job_guard;
    EXECUTE v_attempt_guard;
    EXECUTE v_job_consistency;
    EXECUTE v_idempotency_consistency;
END
$$;

DROP TABLE hwpx_agent.cancel_cleanup_v1_rollback_functions;

ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions WHERE version = 8;
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;

COMMIT;
