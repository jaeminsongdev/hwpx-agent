BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 7 AND migration_name = 'p14.idempotency_reconciliation_v2'
    ) OR EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions WHERE version >= 8
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 cancel cleanup migration requires exact schema version 7';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256', true) !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            MESSAGE = 'P14 cancel cleanup migration requires its exact SHA-256';
    END IF;
END
$$;

CREATE TABLE hwpx_agent.job_cancellation_requests (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    job_id uuid NOT NULL,
    idempotency_key uuid NOT NULL,
    cancellation_id uuid NOT NULL,
    subject_sha256 character(64) NOT NULL,
    state text NOT NULL,
    request_receipt_artifact_id uuid NOT NULL,
    cleanup_task_id uuid,
    requested_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    resolved_at timestamptz,
    PRIMARY KEY (tenant_id, project_id, job_id),
    UNIQUE (tenant_id, cancellation_id),
    CONSTRAINT job_cancellation_job_fk FOREIGN KEY (tenant_id, project_id, job_id)
        REFERENCES hwpx_agent.jobs (tenant_id, project_id, job_id) ON DELETE RESTRICT,
    CONSTRAINT job_cancellation_idempotency_fk FOREIGN KEY (
        tenant_id, project_id, idempotency_key
    ) REFERENCES hwpx_agent.idempotency_records (
        tenant_id, project_id, idempotency_key
    ) ON DELETE RESTRICT,
    CONSTRAINT job_cancellation_receipt_fk FOREIGN KEY (tenant_id, request_receipt_artifact_id)
        REFERENCES hwpx_agent.artifacts (tenant_id, artifact_id) ON DELETE RESTRICT,
    CONSTRAINT job_cancellation_identity CHECK (
        idempotency_key <> '00000000-0000-0000-0000-000000000000'::uuid
        AND cancellation_id <> '00000000-0000-0000-0000-000000000000'::uuid
        AND subject_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT job_cancellation_state CHECK (
        state IN ('requested', 'cancelled', 'outcome_unknown', 'too_late')
    ),
    CONSTRAINT job_cancellation_resolution CHECK (
        (state = 'requested' AND resolved_at IS NULL AND cleanup_task_id IS NULL)
        OR (state IN ('cancelled', 'outcome_unknown', 'too_late')
            AND resolved_at IS NOT NULL)
    ),
    CONSTRAINT job_cancellation_time_order CHECK (
        resolved_at IS NULL OR resolved_at >= requested_at
    )
);

CREATE TABLE hwpx_agent.job_effect_markers (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    job_id uuid NOT NULL,
    attempt_no integer NOT NULL,
    execution_id uuid NOT NULL,
    agent_instance_id uuid NOT NULL,
    fencing_token bigint NOT NULL,
    phase text NOT NULL,
    started_at timestamptz NOT NULL,
    committed_at timestamptz,
    updated_at timestamptz NOT NULL,
    PRIMARY KEY (tenant_id, project_id, job_id, attempt_no),
    UNIQUE (tenant_id, execution_id),
    CONSTRAINT job_effect_marker_attempt_fk FOREIGN KEY (
        tenant_id, project_id, job_id, attempt_no
    ) REFERENCES hwpx_agent.job_attempts (
        tenant_id, project_id, job_id, attempt_no
    ) ON DELETE RESTRICT,
    CONSTRAINT job_effect_marker_identity CHECK (
        attempt_no BETWEEN 1 AND 10
        AND fencing_token = attempt_no
        AND execution_id <> '00000000-0000-0000-0000-000000000000'::uuid
        AND agent_instance_id <> '00000000-0000-0000-0000-000000000000'::uuid
    ),
    CONSTRAINT job_effect_marker_phase CHECK (phase IN ('started', 'committed')),
    CONSTRAINT job_effect_marker_time CHECK (
        updated_at >= started_at
        AND (
            (phase = 'started' AND committed_at IS NULL)
            OR (phase = 'committed' AND committed_at IS NOT NULL
                AND committed_at >= started_at AND updated_at >= committed_at)
        )
    )
);

CREATE TABLE hwpx_agent.cleanup_tasks (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    job_id uuid NOT NULL,
    cleanup_task_id uuid NOT NULL,
    target_fingerprint character(64) NOT NULL,
    target_kind text NOT NULL,
    workspace_handle uuid,
    artifact_id uuid,
    artifact_content_sha256 character(64),
    artifact_kind text,
    source_execution_id uuid,
    source_attempt_no integer,
    source_fencing_token bigint,
    state text NOT NULL DEFAULT 'pending',
    attempt_count integer NOT NULL DEFAULT 0,
    lease_worker_id uuid,
    lease_execution_id uuid,
    lease_fencing_token bigint NOT NULL DEFAULT 0,
    lease_issued_at timestamptz,
    lease_expires_at timestamptz,
    outcome text,
    proof_sha256 character(64),
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    completed_at timestamptz,
    PRIMARY KEY (tenant_id, cleanup_task_id),
    UNIQUE (tenant_id, target_fingerprint),
    CONSTRAINT cleanup_task_job_fk FOREIGN KEY (tenant_id, project_id, job_id)
        REFERENCES hwpx_agent.jobs (tenant_id, project_id, job_id) ON DELETE RESTRICT,
    CONSTRAINT cleanup_task_artifact_fk FOREIGN KEY (tenant_id, artifact_id)
        REFERENCES hwpx_agent.artifacts (tenant_id, artifact_id) ON DELETE RESTRICT,
    CONSTRAINT cleanup_task_identity CHECK (
        cleanup_task_id <> '00000000-0000-0000-0000-000000000000'::uuid
        AND target_fingerprint ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT cleanup_task_kind CHECK (target_kind IN ('workspace', 'orphan_artifact')),
    CONSTRAINT cleanup_task_target_shape CHECK (
        (
            target_kind = 'workspace'
            AND workspace_handle IS NOT NULL
            AND artifact_id IS NULL AND artifact_content_sha256 IS NULL
            AND artifact_kind IS NULL
            AND source_execution_id IS NOT NULL
            AND source_attempt_no BETWEEN 1 AND 10
            AND source_fencing_token = source_attempt_no
        )
        OR (
            target_kind = 'orphan_artifact'
            AND workspace_handle IS NULL
            AND artifact_id IS NOT NULL
            AND artifact_content_sha256 ~ '^[0-9a-f]{64}$'
            AND artifact_kind IN ('result', 'preview', 'evidence', 'trace', 'diff', 'receipt')
            AND source_execution_id IS NULL
            AND source_attempt_no IS NULL
            AND source_fencing_token IS NULL
        )
    ),
    CONSTRAINT cleanup_task_state CHECK (
        state IN ('pending', 'leased', 'succeeded', 'failed_terminal')
    ),
    CONSTRAINT cleanup_task_attempt_range CHECK (attempt_count BETWEEN 0 AND 3),
    CONSTRAINT cleanup_task_lease_shape CHECK (
        (
            state = 'pending' AND attempt_count BETWEEN 0 AND 2
            AND lease_worker_id IS NULL AND lease_execution_id IS NULL
            AND lease_fencing_token = attempt_count
            AND lease_issued_at IS NULL AND lease_expires_at IS NULL
            AND outcome IS NULL AND proof_sha256 IS NULL AND completed_at IS NULL
        )
        OR (
            state = 'leased' AND attempt_count BETWEEN 1 AND 3
            AND lease_worker_id IS NOT NULL AND lease_execution_id IS NOT NULL
            AND lease_fencing_token = attempt_count
            AND lease_issued_at IS NOT NULL AND lease_expires_at > lease_issued_at
            AND lease_expires_at <= lease_issued_at + interval '5 minutes'
            AND outcome IS NULL AND proof_sha256 IS NULL AND completed_at IS NULL
        )
        OR (
            state = 'succeeded' AND attempt_count BETWEEN 1 AND 3
            AND lease_worker_id IS NULL AND lease_execution_id IS NULL
            AND lease_fencing_token = attempt_count
            AND lease_issued_at IS NULL AND lease_expires_at IS NULL
            AND outcome IS NOT NULL AND proof_sha256 ~ '^[0-9a-f]{64}$'
            AND completed_at IS NOT NULL
        )
        OR (
            state = 'failed_terminal' AND attempt_count = 3
            AND lease_worker_id IS NULL AND lease_execution_id IS NULL
            AND lease_fencing_token = 3
            AND lease_issued_at IS NULL AND lease_expires_at IS NULL
            AND outcome IS NULL AND proof_sha256 IS NULL AND completed_at IS NOT NULL
        )
    ),
    CONSTRAINT cleanup_task_outcome CHECK (
        outcome IS NULL
        OR (target_kind = 'workspace'
            AND outcome IN ('workspace_removed', 'workspace_already_absent'))
        OR (target_kind = 'orphan_artifact'
            AND outcome IN ('artifact_quarantined', 'artifact_already_quarantined'))
    ),
    CONSTRAINT cleanup_task_time_order CHECK (
        updated_at >= created_at
        AND (completed_at IS NULL OR completed_at >= created_at)
    )
);

ALTER TABLE hwpx_agent.job_cancellation_requests
    ADD CONSTRAINT job_cancellation_cleanup_fk FOREIGN KEY (tenant_id, cleanup_task_id)
        REFERENCES hwpx_agent.cleanup_tasks (tenant_id, cleanup_task_id) ON DELETE RESTRICT;

CREATE INDEX cleanup_tasks_ready_idx
    ON hwpx_agent.cleanup_tasks (tenant_id, state, created_at, cleanup_task_id)
    WHERE state IN ('pending', 'leased');

ALTER TABLE hwpx_agent.job_cancellation_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.job_cancellation_requests FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.job_cancellation_requests
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());
ALTER TABLE hwpx_agent.job_effect_markers ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.job_effect_markers FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.job_effect_markers
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());
ALTER TABLE hwpx_agent.cleanup_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.cleanup_tasks FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.cleanup_tasks
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());

REVOKE ALL ON TABLE hwpx_agent.job_cancellation_requests FROM PUBLIC;
REVOKE ALL ON TABLE hwpx_agent.job_effect_markers FROM PUBLIC;
REVOKE ALL ON TABLE hwpx_agent.cleanup_tasks FROM PUBLIC;

CREATE TABLE hwpx_agent.cancel_cleanup_v1_rollback_functions (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    job_guard text NOT NULL,
    attempt_guard text NOT NULL,
    job_consistency text NOT NULL,
    idempotency_consistency text NOT NULL
);
INSERT INTO hwpx_agent.cancel_cleanup_v1_rollback_functions (
    singleton, job_guard, attempt_guard, job_consistency, idempotency_consistency
)
SELECT true,
    pg_get_functiondef('hwpx_agent.guard_job_state_machine_update()'::regprocedure),
    pg_get_functiondef('hwpx_agent.guard_job_attempt_state_machine_update()'::regprocedure),
    pg_get_functiondef('hwpx_agent.verify_job_state_machine_consistency()'::regprocedure),
    pg_get_functiondef('hwpx_agent.verify_idempotency_job_consistency()'::regprocedure);
REVOKE ALL ON TABLE hwpx_agent.cancel_cleanup_v1_rollback_functions FROM PUBLIC;

-- Cancellation is an extension of the version-2 job/idempotency state machine. Legacy rows stay
-- untouched. A claimed job may become a receipt-backed terminal cancellation before attempt one.
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
                    state = 'terminal_failure'
                    AND (
                        attempt_count > 0
                        OR (attempt_count = 0 AND terminal_error_code = 'JOB_CANCELLED')
                    )
                    AND result_revision_id IS NULL AND receipt_artifact_id IS NOT NULL
                    AND terminal_error_code IS NOT NULL AND retry_not_before IS NULL
                )
            )
        )
    );

ALTER TABLE hwpx_agent.jobs
    DROP CONSTRAINT jobs_state_machine_complete_v7,
    ADD CONSTRAINT jobs_state_machine_complete_v8 CHECK (
        (
            state_machine_version IS NULL
            AND active_execution_id IS NULL AND lease_issued_at IS NULL
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
                    AND result_revision_id IS NULL AND terminal_error_code = 'OUTCOME_UNKNOWN'
                    AND completed_at IS NULL
                )
                OR (
                    state = 'succeeded' AND attempt_count > 0
                    AND lease_owner_agent_id IS NULL AND active_execution_id IS NULL
                    AND lease_issued_at IS NULL AND lease_expires_at IS NULL
                    AND result_revision_id IS NOT NULL AND terminal_error_code IS NULL
                    AND completed_at IS NOT NULL
                )
                OR (
                    state = 'failed' AND attempt_count > 0
                    AND lease_owner_agent_id IS NULL AND active_execution_id IS NULL
                    AND lease_issued_at IS NULL AND lease_expires_at IS NULL
                    AND result_revision_id IS NULL AND terminal_error_code IS NOT NULL
                    AND completed_at IS NOT NULL
                )
                OR (
                    state = 'cancelled'
                    AND lease_owner_agent_id IS NULL AND active_execution_id IS NULL
                    AND lease_issued_at IS NULL AND lease_expires_at IS NULL
                    AND result_revision_id IS NULL AND terminal_error_code = 'JOB_CANCELLED'
                    AND completed_at IS NOT NULL AND cancellation_requested_at IS NOT NULL
                )
            )
        )
    );

ALTER TABLE hwpx_agent.job_attempts
    DROP CONSTRAINT job_attempts_state_machine_complete_v7,
    ADD CONSTRAINT job_attempts_state_machine_complete_v8 CHECK (
        (
            state_machine_version IS NULL AND lease_expires_at IS NULL AND updated_at IS NULL
        )
        OR (
            state_machine_version = 1 AND attempt_no = 1 AND fencing_token = 1
            AND state IN ('leased', 'running', 'succeeded', 'failed')
            AND lease_expires_at > started_at
            AND lease_expires_at <= started_at + interval '1 hour'
            AND updated_at >= started_at
            AND (completed_at IS NULL OR updated_at >= completed_at)
        )
        OR (
            state_machine_version = 2 AND attempt_no BETWEEN 1 AND 10
            AND fencing_token = attempt_no
            AND state IN ('leased', 'running', 'succeeded', 'failed', 'cancelled', 'unknown_outcome')
            AND lease_expires_at > started_at
            AND lease_expires_at <= started_at + interval '1 hour'
            AND updated_at >= started_at
            AND (completed_at IS NULL OR updated_at >= completed_at)
        )
    );

ALTER TABLE hwpx_agent.artifacts
    DROP CONSTRAINT artifacts_service_metadata_complete,
    DROP CONSTRAINT artifacts_object_key_binding,
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
            AND encryption_algorithm = 'AES-256-GCM' AND encryption_nonce IS NOT NULL
            AND aad_sha256 IS NOT NULL AND ciphertext_sha256 IS NOT NULL
            AND validation_state IS NOT NULL AND scanner_engine_ref IS NOT NULL
            AND scanner_signature_version IS NOT NULL AND authorization_generation IS NOT NULL
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

CREATE OR REPLACE FUNCTION hwpx_agent.guard_job_state_machine_update()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_stage_lease_unchanged boolean;
    v_worker_qualified boolean;
    v_now timestamptz := clock_timestamp();
    v_heartbeat_allowed boolean :=
        current_setting('hwpx_agent.allow_job_lease_heartbeat', true) IS NOT DISTINCT FROM 'on';
    v_expiry_allowed boolean :=
        current_setting('hwpx_agent.allow_job_lease_expiry_finalize', true) IS NOT DISTINCT FROM 'on';
    v_v2_allowed boolean :=
        current_setting('hwpx_agent.allow_idempotency_v2_transition', true) IS NOT DISTINCT FROM 'on';
    v_cancel_allowed boolean :=
        current_setting('hwpx_agent.allow_cancel_cleanup_v1_transition', true) IS NOT DISTINCT FROM 'on';
BEGIN
    IF OLD.state_machine_version IS DISTINCT FROM NEW.state_machine_version THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_STATE_MACHINE_VERSION_IMMUTABLE';
    END IF;
    IF OLD.state_machine_version IS NULL THEN
        RETURN NEW;
    END IF;
    IF ROW(
        OLD.tenant_id, OLD.project_id, OLD.job_id, OLD.request_id,
        OLD.input_artifact_id, OLD.expected_revision_id,
        OLD.operation_plan_sha256, OLD.required_target_profile_id,
        OLD.required_capability_set_sha256, OLD.created_at
    ) IS DISTINCT FROM ROW(
        NEW.tenant_id, NEW.project_id, NEW.job_id, NEW.request_id,
        NEW.input_artifact_id, NEW.expected_revision_id,
        NEW.operation_plan_sha256, NEW.required_target_profile_id,
        NEW.required_capability_set_sha256, NEW.created_at
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_SPEC_IMMUTABLE';
    END IF;
    IF NEW.updated_at < OLD.updated_at THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_UPDATED_AT_REGRESSION';
    END IF;

    IF OLD.state_machine_version = 2 AND v_cancel_allowed THEN
        IF OLD.state IN ('succeeded', 'failed', 'cancelled') THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_TERMINAL_IMMUTABLE';
        END IF;
        IF OLD.state IN ('leased', 'staged', 'executing', 'validating')
           AND NEW.state = OLD.state
           AND OLD.cancellation_requested_at IS NULL
           AND NEW.cancellation_requested_at IS NOT NULL
           AND ROW(
                NEW.attempt_count, NEW.lease_owner_agent_id, NEW.active_execution_id,
                NEW.fencing_token, NEW.lease_issued_at, NEW.lease_expires_at,
                NEW.result_revision_id, NEW.terminal_error_code, NEW.completed_at
           ) IS NOT DISTINCT FROM ROW(
                OLD.attempt_count, OLD.lease_owner_agent_id, OLD.active_execution_id,
                OLD.fencing_token, OLD.lease_issued_at, OLD.lease_expires_at,
                OLD.result_revision_id, OLD.terminal_error_code, OLD.completed_at
           ) THEN
            RETURN NEW;
        END IF;
        IF OLD.state IN ('queued', 'retry_pending') AND NEW.state = 'cancelled'
           AND NEW.cancellation_requested_at IS NOT NULL
           AND NEW.attempt_count = OLD.attempt_count AND NEW.fencing_token = OLD.fencing_token
           AND NEW.lease_owner_agent_id IS NULL AND NEW.active_execution_id IS NULL
           AND NEW.lease_issued_at IS NULL AND NEW.lease_expires_at IS NULL
           AND NEW.result_revision_id IS NULL AND NEW.terminal_error_code = 'JOB_CANCELLED'
           AND NEW.completed_at IS NOT NULL THEN
            RETURN NEW;
        END IF;
        IF OLD.state IN ('leased', 'staged', 'executing', 'validating')
           AND NEW.state IN ('cancelled', 'unknown_outcome')
           AND OLD.cancellation_requested_at IS NOT NULL
           AND NEW.cancellation_requested_at IS NOT NULL
           AND NEW.attempt_count = OLD.attempt_count AND NEW.fencing_token = OLD.fencing_token
           AND NEW.lease_owner_agent_id IS NULL AND NEW.active_execution_id IS NULL
           AND NEW.lease_issued_at IS NULL AND NEW.lease_expires_at IS NULL
           AND NEW.result_revision_id IS NULL
           AND (
                (NEW.state = 'cancelled' AND NEW.terminal_error_code = 'JOB_CANCELLED'
                 AND NEW.completed_at IS NOT NULL)
                OR (NEW.state = 'unknown_outcome'
                    AND NEW.terminal_error_code = 'OUTCOME_UNKNOWN'
                    AND NEW.completed_at IS NULL)
           ) THEN
            RETURN NEW;
        END IF;
        IF NEW.state = OLD.state AND OLD.cancellation_requested_at IS NOT NULL
           AND NEW.cancellation_requested_at IS NULL
           AND ROW(
                NEW.attempt_count, NEW.lease_owner_agent_id, NEW.active_execution_id,
                NEW.fencing_token, NEW.lease_issued_at, NEW.lease_expires_at,
                NEW.result_revision_id, NEW.terminal_error_code, NEW.completed_at
           ) IS NOT DISTINCT FROM ROW(
                OLD.attempt_count, OLD.lease_owner_agent_id, OLD.active_execution_id,
                OLD.fencing_token, OLD.lease_issued_at, OLD.lease_expires_at,
                OLD.result_revision_id, OLD.terminal_error_code, OLD.completed_at
           ) THEN
            RETURN NEW;
        END IF;
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_CANCEL_TRANSITION_INVALID';
    END IF;

    IF OLD.state_machine_version = 2 THEN
        IF NOT v_v2_allowed THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_V2_TRANSITION_REQUIRED';
        END IF;
        IF OLD.cancellation_requested_at IS NOT NULL THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_CANCELLATION_PENDING';
        END IF;
        IF OLD.state IN ('succeeded', 'failed', 'cancelled') THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_TERMINAL_IMMUTABLE';
        END IF;
        IF ROW(OLD.state, NEW.state) NOT IN (
            ROW('queued', 'leased'), ROW('retry_pending', 'leased'),
            ROW('leased', 'leased'), ROW('staged', 'staged'),
            ROW('executing', 'executing'), ROW('validating', 'validating'),
            ROW('leased', 'staged'), ROW('staged', 'executing'),
            ROW('executing', 'validating'),
            ROW('leased', 'retry_pending'), ROW('staged', 'retry_pending'),
            ROW('executing', 'retry_pending'), ROW('validating', 'retry_pending'),
            ROW('leased', 'unknown_outcome'), ROW('staged', 'unknown_outcome'),
            ROW('executing', 'unknown_outcome'), ROW('validating', 'unknown_outcome'),
            ROW('validating', 'succeeded'),
            ROW('leased', 'failed'), ROW('staged', 'failed'),
            ROW('executing', 'failed'), ROW('validating', 'failed'),
            ROW('unknown_outcome', 'retry_pending'),
            ROW('unknown_outcome', 'succeeded'), ROW('unknown_outcome', 'failed')
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_TRANSITION_INVALID';
        END IF;
        RETURN NEW;
    END IF;

    IF OLD.state IN ('succeeded', 'failed', 'cancelled', 'unknown_outcome') THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_TERMINAL_IMMUTABLE';
    END IF;
    IF OLD.state IN ('leased', 'staged', 'executing', 'validating')
       AND NEW.state IS DISTINCT FROM OLD.state AND OLD.lease_expires_at <= v_now
       AND NOT (v_expiry_allowed AND NEW.state = 'failed'
                AND NEW.terminal_error_code = 'LEASE_EXPIRED') THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'JOB_LEASE_EXPIRED';
    END IF;
    IF OLD.state IN ('leased', 'staged', 'executing', 'validating')
       AND NEW.state = OLD.state THEN
        IF NOT v_heartbeat_allowed
           OR ROW(
                NEW.attempt_count, NEW.lease_owner_agent_id, NEW.active_execution_id,
                NEW.fencing_token, NEW.lease_issued_at, NEW.result_revision_id,
                NEW.terminal_error_code, NEW.completed_at, NEW.cancellation_requested_at
           ) IS DISTINCT FROM ROW(
                OLD.attempt_count, OLD.lease_owner_agent_id, OLD.active_execution_id,
                OLD.fencing_token, OLD.lease_issued_at, OLD.result_revision_id,
                OLD.terminal_error_code, OLD.completed_at, OLD.cancellation_requested_at
           )
           OR OLD.lease_expires_at <= v_now OR NEW.lease_expires_at <= OLD.lease_expires_at
           OR NEW.lease_expires_at > OLD.lease_issued_at + interval '1 hour' THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_HEARTBEAT_INVALID';
        END IF;
        RETURN NEW;
    END IF;
    v_stage_lease_unchanged := ROW(
        NEW.attempt_count, NEW.lease_owner_agent_id, NEW.active_execution_id,
        NEW.fencing_token, NEW.lease_issued_at, NEW.lease_expires_at,
        NEW.result_revision_id, NEW.terminal_error_code, NEW.completed_at,
        NEW.cancellation_requested_at
    ) IS NOT DISTINCT FROM ROW(
        OLD.attempt_count, OLD.lease_owner_agent_id, OLD.active_execution_id,
        OLD.fencing_token, OLD.lease_issued_at, OLD.lease_expires_at,
        OLD.result_revision_id, OLD.terminal_error_code, OLD.completed_at,
        OLD.cancellation_requested_at
    );
    IF OLD.state = 'queued' AND NEW.state = 'leased' THEN
        SELECT EXISTS (
            SELECT 1 FROM hwpx_agent.worker_registrations AS worker
            WHERE worker.tenant_id = NEW.tenant_id
              AND worker.agent_instance_id = NEW.lease_owner_agent_id
              AND worker.subject_sha256 = hwpx_agent.current_subject_sha256()
              AND worker.target_profile_id = NEW.required_target_profile_id
              AND worker.capability_set_sha256 = NEW.required_capability_set_sha256
              AND worker.state = 'ready'
              AND worker.last_heartbeat_at <= v_now AND worker.expires_at > v_now
              AND NEW.lease_expires_at > v_now AND NEW.lease_expires_at <= worker.expires_at
        ) INTO v_worker_qualified;
        IF NOT v_worker_qualified THEN
            RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'JOB_WORKER_NOT_QUALIFIED';
        END IF;
        IF NEW.attempt_count <> 1 OR NEW.lease_owner_agent_id IS NULL
           OR NEW.active_execution_id IS NULL OR NEW.fencing_token <> 1
           OR NEW.lease_issued_at IS NULL OR NEW.lease_expires_at IS NULL
           OR NEW.result_revision_id IS NOT NULL OR NEW.terminal_error_code IS NOT NULL
           OR NEW.completed_at IS NOT NULL THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_LEASE_TRANSITION_INVALID';
        END IF;
    ELSIF ROW(OLD.state, NEW.state) IN (
        ROW('leased', 'staged'), ROW('staged', 'executing'), ROW('executing', 'validating')
    ) THEN
        IF NOT v_stage_lease_unchanged THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_STAGE_LEASE_DRIFT';
        END IF;
    ELSIF OLD.state = 'validating' AND NEW.state = 'succeeded' THEN
        IF NEW.attempt_count <> OLD.attempt_count OR NEW.fencing_token <> OLD.fencing_token
           OR NEW.lease_owner_agent_id IS NOT NULL OR NEW.active_execution_id IS NOT NULL
           OR NEW.lease_issued_at IS NOT NULL OR NEW.lease_expires_at IS NOT NULL
           OR NEW.result_revision_id IS NULL OR NEW.terminal_error_code IS NOT NULL
           OR NEW.completed_at IS NULL OR NEW.cancellation_requested_at IS NOT NULL THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_SUCCESS_TRANSITION_INVALID';
        END IF;
    ELSIF OLD.state IN ('leased', 'staged', 'executing', 'validating')
          AND NEW.state = 'failed' THEN
        IF NEW.attempt_count <> OLD.attempt_count OR NEW.fencing_token <> OLD.fencing_token
           OR NEW.lease_owner_agent_id IS NOT NULL OR NEW.active_execution_id IS NOT NULL
           OR NEW.lease_issued_at IS NOT NULL OR NEW.lease_expires_at IS NOT NULL
           OR NEW.result_revision_id IS NOT NULL OR NEW.terminal_error_code IS NULL
           OR NEW.completed_at IS NULL OR NEW.cancellation_requested_at IS NOT NULL
           OR (v_expiry_allowed AND NEW.terminal_error_code <> 'LEASE_EXPIRED') THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_FAILURE_TRANSITION_INVALID';
        END IF;
    ELSE
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_TRANSITION_INVALID';
    END IF;
    RETURN NEW;
END
$$;

CREATE OR REPLACE FUNCTION hwpx_agent.guard_job_attempt_state_machine_update()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
DECLARE
    v_heartbeat_allowed boolean :=
        current_setting('hwpx_agent.allow_job_lease_heartbeat', true) IS NOT DISTINCT FROM 'on';
    v_v2_allowed boolean :=
        current_setting('hwpx_agent.allow_idempotency_v2_transition', true) IS NOT DISTINCT FROM 'on';
    v_cancel_allowed boolean :=
        current_setting('hwpx_agent.allow_cancel_cleanup_v1_transition', true) IS NOT DISTINCT FROM 'on';
BEGIN
    IF ROW(
        OLD.tenant_id, OLD.project_id, OLD.job_id, OLD.attempt_no,
        OLD.execution_id, OLD.agent_instance_id, OLD.fencing_token, OLD.started_at
    ) IS DISTINCT FROM ROW(
        NEW.tenant_id, NEW.project_id, NEW.job_id, NEW.attempt_no,
        NEW.execution_id, NEW.agent_instance_id, NEW.fencing_token, NEW.started_at
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_ATTEMPT_IDENTITY_IMMUTABLE';
    END IF;
    IF OLD.state_machine_version IS DISTINCT FROM NEW.state_machine_version THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_ATTEMPT_LEASE_IMMUTABLE';
    END IF;
    IF OLD.state_machine_version IS NULL THEN
        RETURN NEW;
    END IF;
    IF NEW.updated_at < OLD.updated_at THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_ATTEMPT_UPDATED_AT_REGRESSION';
    END IF;
    IF OLD.state IN ('succeeded', 'failed', 'cancelled', 'unknown_outcome') THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_ATTEMPT_TERMINAL_IMMUTABLE';
    END IF;

    IF OLD.state_machine_version = 2 AND v_cancel_allowed THEN
        IF OLD.state NOT IN ('leased', 'running')
           OR NEW.state NOT IN ('cancelled', 'unknown_outcome')
           OR NEW.lease_expires_at IS DISTINCT FROM OLD.lease_expires_at
           OR NEW.receipt_artifact_id IS NULL OR NEW.completed_at IS NULL THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_ATTEMPT_CANCEL_INVALID';
        END IF;
        RETURN NEW;
    END IF;

    IF OLD.state_machine_version = 2 THEN
        IF NOT v_v2_allowed THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_V2_TRANSITION_REQUIRED';
        END IF;
        IF NEW.state = OLD.state AND NEW.lease_expires_at IS DISTINCT FROM OLD.lease_expires_at THEN
            IF NOT v_heartbeat_allowed OR OLD.state NOT IN ('leased', 'running')
               OR NEW.lease_expires_at <= OLD.lease_expires_at
               OR NEW.lease_expires_at > OLD.started_at + interval '1 hour'
               OR NEW.receipt_artifact_id IS DISTINCT FROM OLD.receipt_artifact_id
               OR NEW.completed_at IS DISTINCT FROM OLD.completed_at THEN
                RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_ATTEMPT_HEARTBEAT_INVALID';
            END IF;
            RETURN NEW;
        END IF;
        IF OLD.lease_expires_at IS DISTINCT FROM NEW.lease_expires_at THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_ATTEMPT_LEASE_IMMUTABLE';
        END IF;
        IF OLD.state = 'leased' AND NEW.state = 'running' THEN
            IF NEW.receipt_artifact_id IS NOT NULL OR NEW.completed_at IS NOT NULL THEN
                RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_ATTEMPT_RUNNING_INVALID';
            END IF;
        ELSIF OLD.state IN ('leased', 'running')
              AND NEW.state IN ('succeeded', 'failed', 'unknown_outcome') THEN
            IF NEW.receipt_artifact_id IS NULL OR NEW.completed_at IS NULL THEN
                RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_ATTEMPT_TERMINAL_INVALID';
            END IF;
        ELSE
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_ATTEMPT_TRANSITION_INVALID';
        END IF;
        RETURN NEW;
    END IF;

    IF NEW.state = OLD.state AND NEW.lease_expires_at IS DISTINCT FROM OLD.lease_expires_at THEN
        IF NOT v_heartbeat_allowed OR OLD.state NOT IN ('leased', 'running')
           OR NEW.lease_expires_at <= OLD.lease_expires_at
           OR NEW.lease_expires_at > OLD.started_at + interval '1 hour'
           OR NEW.receipt_artifact_id IS DISTINCT FROM OLD.receipt_artifact_id
           OR NEW.completed_at IS DISTINCT FROM OLD.completed_at THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_ATTEMPT_HEARTBEAT_INVALID';
        END IF;
        RETURN NEW;
    END IF;
    IF OLD.lease_expires_at IS DISTINCT FROM NEW.lease_expires_at THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_ATTEMPT_LEASE_IMMUTABLE';
    END IF;
    IF OLD.state = 'leased' AND NEW.state = 'running' THEN
        IF NEW.receipt_artifact_id IS NOT NULL OR NEW.completed_at IS NOT NULL THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_ATTEMPT_RUNNING_INVALID';
        END IF;
    ELSIF OLD.state IN ('leased', 'running') AND NEW.state IN ('succeeded', 'failed') THEN
        IF NEW.receipt_artifact_id IS NULL OR NEW.completed_at IS NULL THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_ATTEMPT_TERMINAL_INVALID';
        END IF;
    ELSE
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_ATTEMPT_TRANSITION_INVALID';
    END IF;
    RETURN NEW;
END
$$;

CREATE OR REPLACE FUNCTION hwpx_agent.verify_job_state_machine_consistency()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_tenant_id uuid := COALESCE(NEW.tenant_id, OLD.tenant_id);
    v_project_id uuid := COALESCE(NEW.project_id, OLD.project_id);
    v_job_id uuid := COALESCE(NEW.job_id, OLD.job_id);
    v_job hwpx_agent.jobs%ROWTYPE;
    v_attempt hwpx_agent.job_attempts%ROWTYPE;
    v_attempt_count bigint;
    v_dense boolean;
BEGIN
    SELECT * INTO v_job FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = v_tenant_id AND job.project_id = v_project_id
      AND job.job_id = v_job_id;
    IF NOT FOUND OR v_job.state_machine_version IS NULL THEN
        RETURN NULL;
    END IF;
    SELECT count(*) INTO v_attempt_count FROM hwpx_agent.job_attempts AS attempt
    WHERE attempt.tenant_id = v_tenant_id AND attempt.project_id = v_project_id
      AND attempt.job_id = v_job_id
      AND attempt.state_machine_version = v_job.state_machine_version;
    IF v_job.state = 'queued'
       OR (v_job.state_machine_version = 2 AND v_job.state = 'cancelled'
           AND v_job.attempt_count = 0) THEN
        IF v_attempt_count <> 0 THEN
            RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'JOB_ATTEMPT_CONSISTENCY_INVALID';
        END IF;
        RETURN NULL;
    END IF;
    IF v_job.state_machine_version = 1 AND v_attempt_count <> 1 THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'JOB_ATTEMPT_CONSISTENCY_INVALID';
    END IF;
    IF v_job.state_machine_version = 2 THEN
        SELECT count(*) = v_job.attempt_count
           AND min(attempt_no) = 1 AND max(attempt_no) = v_job.attempt_count
           AND bool_and(fencing_token = attempt_no)
        INTO v_dense
        FROM hwpx_agent.job_attempts AS attempt
        WHERE attempt.tenant_id = v_tenant_id AND attempt.project_id = v_project_id
          AND attempt.job_id = v_job_id AND attempt.state_machine_version = 2;
        IF v_attempt_count <> v_job.attempt_count OR NOT COALESCE(v_dense, false) THEN
            RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'JOB_ATTEMPT_SEQUENCE_INVALID';
        END IF;
    END IF;
    SELECT * INTO STRICT v_attempt FROM hwpx_agent.job_attempts AS attempt
    WHERE attempt.tenant_id = v_tenant_id AND attempt.project_id = v_project_id
      AND attempt.job_id = v_job_id AND attempt.attempt_no = v_job.attempt_count
      AND attempt.state_machine_version = v_job.state_machine_version;
    IF v_job.state IN ('leased', 'staged', 'executing', 'validating')
       AND ROW(v_attempt.agent_instance_id, v_attempt.execution_id,
               v_attempt.started_at, v_attempt.lease_expires_at)
           IS DISTINCT FROM ROW(v_job.lease_owner_agent_id, v_job.active_execution_id,
                                v_job.lease_issued_at, v_job.lease_expires_at) THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'JOB_ATTEMPT_BINDING_INVALID';
    END IF;
    IF v_attempt.fencing_token <> v_job.fencing_token
       OR (v_job.state IN ('leased', 'staged') AND v_attempt.state <> 'leased')
       OR (v_job.state IN ('executing', 'validating') AND v_attempt.state <> 'running')
       OR (v_job.state = 'retry_pending' AND v_attempt.state NOT IN ('failed', 'unknown_outcome'))
       OR (v_job.state = 'unknown_outcome' AND v_attempt.state <> 'unknown_outcome')
       OR (v_job.state = 'succeeded' AND v_attempt.state NOT IN ('succeeded', 'unknown_outcome'))
       OR (v_job.state = 'failed' AND v_attempt.state NOT IN ('failed', 'unknown_outcome'))
       OR (v_job.state = 'cancelled'
           AND v_attempt.state NOT IN ('cancelled', 'failed', 'unknown_outcome'))
       OR (
            v_job.state_machine_version = 1 AND v_job.state IN ('succeeded', 'failed')
            AND v_attempt.completed_at IS DISTINCT FROM v_job.completed_at
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'JOB_ATTEMPT_CONSISTENCY_INVALID';
    END IF;
    RETURN NULL;
END
$$;

CREATE OR REPLACE FUNCTION hwpx_agent.verify_idempotency_job_consistency()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_tenant_id uuid := COALESCE(NEW.tenant_id, OLD.tenant_id);
    v_project_id uuid := COALESCE(NEW.project_id, OLD.project_id);
    v_job_id uuid := COALESCE(NEW.job_id, OLD.job_id);
    v_record hwpx_agent.idempotency_records%ROWTYPE;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_record_found boolean;
    v_job_found boolean;
BEGIN
    IF v_job_id IS NULL THEN
        RETURN NULL;
    END IF;
    SELECT * INTO v_record FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = v_tenant_id AND record.project_id = v_project_id
      AND record.job_id = v_job_id AND record.record_version = 2;
    v_record_found := FOUND;
    SELECT * INTO v_job FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = v_tenant_id AND job.project_id = v_project_id
      AND job.job_id = v_job_id;
    v_job_found := FOUND;
    IF NOT v_record_found
       AND (NOT v_job_found OR v_job.state_machine_version IS DISTINCT FROM 2) THEN
        RETURN NULL;
    END IF;
    IF NOT v_record_found OR NOT v_job_found
       OR v_job.state_machine_version IS DISTINCT FROM 2
       OR ROW(v_record.request_id, v_record.source_artifact_id,
              v_record.expected_revision_id, v_record.attempt_count,
              v_record.last_fencing_token, v_record.result_revision_id)
          IS DISTINCT FROM ROW(v_job.request_id, v_job.input_artifact_id,
                               v_job.expected_revision_id, v_job.attempt_count,
                               v_job.fencing_token, v_job.result_revision_id)
       OR (v_record.state = 'claimed' AND v_job.state <> 'queued')
       OR (v_record.state = 'in_progress'
           AND v_job.state NOT IN ('leased', 'staged', 'executing', 'validating'))
       OR (v_record.state = 'retry_pending' AND v_job.state <> 'retry_pending')
       OR (v_record.state = 'outcome_unknown' AND v_job.state <> 'unknown_outcome')
       OR (v_record.state = 'terminal_success' AND v_job.state <> 'succeeded')
       OR (v_record.state = 'terminal_failure'
           AND v_job.state NOT IN ('failed', 'cancelled')) THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'IDEMPOTENCY_JOB_CONSISTENCY_INVALID';
    END IF;
    RETURN NULL;
END
$$;

CREATE FUNCTION hwpx_agent.protect_cancel_cleanup_identity()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    IF TG_TABLE_NAME = 'job_cancellation_requests' THEN
        IF (to_jsonb(NEW) - 'state' - 'cleanup_task_id' - 'resolved_at')
           IS DISTINCT FROM
           (to_jsonb(OLD) - 'state' - 'cleanup_task_id' - 'resolved_at') THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'CANCELLATION_IDENTITY_IMMUTABLE';
        END IF;
    ELSIF TG_TABLE_NAME = 'job_effect_markers' THEN
        IF (to_jsonb(NEW) - 'phase' - 'committed_at' - 'updated_at')
           IS DISTINCT FROM
           (to_jsonb(OLD) - 'phase' - 'committed_at' - 'updated_at') THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'EFFECT_MARKER_IDENTITY_IMMUTABLE';
        END IF;
    ELSIF TG_TABLE_NAME = 'cleanup_tasks' THEN
        IF (to_jsonb(NEW) - ARRAY[
                'state', 'attempt_count', 'lease_worker_id', 'lease_execution_id',
                'lease_fencing_token', 'lease_issued_at', 'lease_expires_at',
                'outcome', 'proof_sha256', 'updated_at', 'completed_at'
            ]) IS DISTINCT FROM
           (to_jsonb(OLD) - ARRAY[
                'state', 'attempt_count', 'lease_worker_id', 'lease_execution_id',
                'lease_fencing_token', 'lease_issued_at', 'lease_expires_at',
                'outcome', 'proof_sha256', 'updated_at', 'completed_at'
            ]) THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'CLEANUP_TASK_IDENTITY_IMMUTABLE';
        END IF;
    ELSE
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'CANCEL_CLEANUP_GUARD_SCOPE_INVALID';
    END IF;
    RETURN NEW;
END
$$;

CREATE TRIGGER job_cancellation_identity_guard
BEFORE UPDATE ON hwpx_agent.job_cancellation_requests
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.protect_cancel_cleanup_identity();
CREATE TRIGGER job_effect_marker_identity_guard
BEFORE UPDATE ON hwpx_agent.job_effect_markers
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.protect_cancel_cleanup_identity();
CREATE TRIGGER cleanup_task_identity_guard
BEFORE UPDATE ON hwpx_agent.cleanup_tasks
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.protect_cancel_cleanup_identity();
CREATE TRIGGER job_cancellation_reject_delete
BEFORE DELETE ON hwpx_agent.job_cancellation_requests
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();
CREATE TRIGGER job_effect_marker_reject_delete
BEFORE DELETE ON hwpx_agent.job_effect_markers
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();
CREATE TRIGGER cleanup_task_reject_delete
BEFORE DELETE ON hwpx_agent.cleanup_tasks
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();

CREATE FUNCTION hwpx_agent.cleanup_artifact_is_referenced_v1(
    p_tenant_id uuid,
    p_artifact_id uuid
)
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = pg_catalog, hwpx_agent
AS $$
    SELECT EXISTS (
        SELECT 1 FROM hwpx_agent.revisions AS revision
        WHERE revision.tenant_id = p_tenant_id
          AND p_artifact_id IN (
              revision.source_artifact_id,
              revision.result_artifact_id,
              revision.semantic_diff_artifact_id
          )
        UNION ALL
        SELECT 1 FROM hwpx_agent.jobs AS job
        WHERE job.tenant_id = p_tenant_id AND job.input_artifact_id = p_artifact_id
        UNION ALL
        SELECT 1 FROM hwpx_agent.job_attempts AS attempt
        WHERE attempt.tenant_id = p_tenant_id
          AND attempt.receipt_artifact_id = p_artifact_id
        UNION ALL
        SELECT 1 FROM hwpx_agent.idempotency_records AS record
        WHERE record.tenant_id = p_tenant_id
          AND p_artifact_id IN (record.source_artifact_id, record.receipt_artifact_id)
        UNION ALL
        SELECT 1 FROM hwpx_agent.job_cancellation_requests AS cancellation
        WHERE cancellation.tenant_id = p_tenant_id
          AND cancellation.request_receipt_artifact_id = p_artifact_id
    )
$$;

CREATE FUNCTION hwpx_agent.cleanup_artifact_qualified_v1(
    p_tenant_id uuid,
    p_subject_sha256 character(64),
    p_artifact_id uuid
)
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = pg_catalog, hwpx_agent
AS $$
    SELECT EXISTS (
        SELECT 1 FROM hwpx_agent.artifacts AS artifact
        JOIN hwpx_agent.artifact_acl AS acl
          ON acl.tenant_id = artifact.tenant_id AND acl.artifact_id = artifact.artifact_id
        WHERE artifact.tenant_id = p_tenant_id AND artifact.artifact_id = p_artifact_id
          AND artifact.service_metadata_version = 1
          AND artifact.storage_state = 'available'
          AND artifact.validation_state = 'verified'
          AND artifact.artifact_kind <> 'source'
          AND acl.subject_sha256 = p_subject_sha256 AND acl.can_manage
          AND NOT hwpx_agent.cleanup_artifact_is_referenced_v1(p_tenant_id, p_artifact_id)
    )
$$;

CREATE FUNCTION hwpx_agent.request_job_cancellation_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_idempotency_key uuid,
    p_job_id uuid,
    p_cancellation_id uuid,
    p_request_receipt_artifact_id uuid,
    p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_state text,
    returned_job_state text,
    returned_cleanup_task_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_existing hwpx_agent.job_cancellation_requests%ROWTYPE;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_record hwpx_agent.idempotency_records%ROWTYPE;
    v_state text;
    v_now timestamptz := clock_timestamp();
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(
        p_tenant_id, p_project_id, p_subject_sha256
    );
    IF p_job_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_cancellation_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_request_receipt_artifact_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'CANCELLATION_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_existing FROM hwpx_agent.job_cancellation_requests AS cancellation
    WHERE cancellation.tenant_id = p_tenant_id
      AND cancellation.project_id = p_project_id
      AND cancellation.job_id = p_job_id FOR UPDATE;
    IF FOUND THEN
        IF ROW(v_existing.idempotency_key, v_existing.cancellation_id, v_existing.subject_sha256,
               v_existing.request_receipt_artifact_id)
           IS DISTINCT FROM ROW(p_idempotency_key, p_cancellation_id, p_subject_sha256,
                                p_request_receipt_artifact_id) THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'CANCELLATION_IDENTITY_CONFLICT';
        END IF;
        RETURN QUERY SELECT v_existing.state, job.state, v_existing.cleanup_task_id
        FROM hwpx_agent.jobs AS job
        WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
          AND job.job_id = p_job_id;
        RETURN;
    END IF;
    SELECT * INTO v_job FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
      AND job.job_id = p_job_id FOR UPDATE;
    SELECT * INTO v_record FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = p_tenant_id AND record.project_id = p_project_id
      AND record.idempotency_key = p_idempotency_key FOR UPDATE;
    IF NOT FOUND OR v_job.state_machine_version IS DISTINCT FROM 2
       OR v_record.record_version IS DISTINCT FROM 2
       OR v_record.job_id IS DISTINCT FROM p_job_id
       OR v_record.subject_sha256 IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'CANCELLATION_JOB_NOT_FOUND';
    END IF;
    IF NOT hwpx_agent.idempotency_v2_artifact_qualified(
        p_tenant_id, p_subject_sha256, p_request_receipt_artifact_id, 'receipt',
        (SELECT content_sha256 FROM hwpx_agent.artifacts
         WHERE tenant_id = p_tenant_id AND artifact_id = p_request_receipt_artifact_id)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'CANCELLATION_RECEIPT_NOT_QUALIFIED';
    END IF;
    v_state := CASE
        WHEN v_job.state IN ('queued', 'retry_pending') THEN 'cancelled'
        WHEN v_job.state IN ('leased', 'staged', 'executing', 'validating') THEN 'requested'
        WHEN v_job.state = 'unknown_outcome' THEN 'outcome_unknown'
        ELSE 'too_late'
    END;
    INSERT INTO hwpx_agent.job_cancellation_requests (
        tenant_id, project_id, job_id, idempotency_key, cancellation_id, subject_sha256,
        state, request_receipt_artifact_id, requested_at, resolved_at
    ) VALUES (
        p_tenant_id, p_project_id, p_job_id, p_idempotency_key,
        p_cancellation_id, p_subject_sha256,
        v_state, p_request_receipt_artifact_id, v_now,
        CASE WHEN v_state = 'requested' THEN NULL ELSE v_now END
    );
    IF v_state = 'requested' THEN
        PERFORM set_config('hwpx_agent.allow_cancel_cleanup_v1_transition', 'on', true);
        UPDATE hwpx_agent.jobs SET cancellation_requested_at = v_now, updated_at = v_now
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
        PERFORM set_config('hwpx_agent.allow_cancel_cleanup_v1_transition', 'off', true);
    ELSIF v_state = 'cancelled' THEN
        DELETE FROM hwpx_agent.idempotency_commit_authorizations
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id
          AND idempotency_key = p_idempotency_key AND job_id = p_job_id;
        PERFORM set_config('hwpx_agent.allow_cancel_cleanup_v1_transition', 'on', true);
        UPDATE hwpx_agent.jobs SET
            state = 'cancelled', cancellation_requested_at = v_now,
            lease_owner_agent_id = NULL, active_execution_id = NULL,
            lease_issued_at = NULL, lease_expires_at = NULL,
            terminal_error_code = 'JOB_CANCELLED', completed_at = v_now, updated_at = v_now
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
        UPDATE hwpx_agent.idempotency_records SET
            state = 'terminal_failure', receipt_artifact_id = p_request_receipt_artifact_id,
            terminal_error_code = 'JOB_CANCELLED', retry_not_before = NULL, updated_at = v_now
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id
          AND idempotency_key = p_idempotency_key;
        PERFORM set_config('hwpx_agent.allow_cancel_cleanup_v1_transition', 'off', true);
    END IF;
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, concat('job.cancel_', v_state),
        p_subject_sha256, p_job_id, p_event_sha256
    );
    RETURN QUERY SELECT v_state, (SELECT state FROM hwpx_agent.jobs AS job
        WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
          AND job.job_id = p_job_id), NULL::uuid;
END
$$;

CREATE FUNCTION hwpx_agent.mark_job_effect_phase_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_job_id uuid,
    p_agent_instance_id uuid,
    p_execution_id uuid,
    p_attempt_no integer,
    p_fencing_token bigint,
    p_phase text,
    p_event_sha256 character(64)
)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_job hwpx_agent.jobs%ROWTYPE;
    v_marker hwpx_agent.job_effect_markers%ROWTYPE;
    v_now timestamptz := clock_timestamp();
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(
        p_tenant_id, p_project_id, p_subject_sha256
    );
    IF p_phase NOT IN ('started', 'committed')
       OR p_attempt_no NOT BETWEEN 1 AND 10 OR p_fencing_token <> p_attempt_no
       OR p_agent_instance_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_execution_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'EFFECT_MARKER_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_job FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
      AND job.job_id = p_job_id FOR UPDATE;
    IF NOT FOUND OR v_job.state_machine_version IS DISTINCT FROM 2
       OR v_job.state NOT IN ('leased', 'staged', 'executing', 'validating')
       OR ROW(v_job.lease_owner_agent_id, v_job.active_execution_id,
              v_job.attempt_count, v_job.fencing_token)
          IS DISTINCT FROM ROW(p_agent_instance_id, p_execution_id,
                               p_attempt_no, p_fencing_token)
       OR v_job.lease_expires_at <= v_now THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'EFFECT_MARKER_LEASE_MISMATCH';
    END IF;
    SELECT * INTO v_marker FROM hwpx_agent.job_effect_markers AS marker
    WHERE marker.tenant_id = p_tenant_id AND marker.project_id = p_project_id
      AND marker.job_id = p_job_id AND marker.attempt_no = p_attempt_no FOR UPDATE;
    IF p_phase = 'started' THEN
        IF v_job.cancellation_requested_at IS NOT NULL THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'SAFE_POINT_CANCELLATION_PENDING';
        END IF;
        IF FOUND THEN
            IF ROW(v_marker.execution_id, v_marker.agent_instance_id,
                   v_marker.fencing_token, v_marker.phase)
               IS DISTINCT FROM ROW(p_execution_id, p_agent_instance_id,
                                    p_fencing_token, 'started'::text) THEN
                RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'EFFECT_MARKER_CONFLICT';
            END IF;
            RETURN 'started';
        END IF;
        INSERT INTO hwpx_agent.job_effect_markers (
            tenant_id, project_id, job_id, attempt_no, execution_id,
            agent_instance_id, fencing_token, phase, started_at, updated_at
        ) VALUES (
            p_tenant_id, p_project_id, p_job_id, p_attempt_no, p_execution_id,
            p_agent_instance_id, p_fencing_token, 'started', v_now, v_now
        );
    ELSE
        IF NOT FOUND OR v_marker.phase <> 'started'
           OR ROW(v_marker.execution_id, v_marker.agent_instance_id, v_marker.fencing_token)
              IS DISTINCT FROM ROW(p_execution_id, p_agent_instance_id, p_fencing_token) THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'EFFECT_MARKER_START_REQUIRED';
        END IF;
        UPDATE hwpx_agent.job_effect_markers SET
            phase = 'committed', committed_at = v_now, updated_at = v_now
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id
          AND job_id = p_job_id AND attempt_no = p_attempt_no;
    END IF;
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, concat('job.effect_', p_phase),
        p_subject_sha256, p_job_id, p_event_sha256
    );
    RETURN p_phase;
END
$$;

CREATE FUNCTION hwpx_agent.finalize_job_cancellation_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_idempotency_key uuid,
    p_job_id uuid,
    p_agent_instance_id uuid,
    p_execution_id uuid,
    p_attempt_no integer,
    p_fencing_token bigint,
    p_cleanup_task_id uuid,
    p_workspace_handle uuid,
    p_event_sha256 character(64)
)
RETURNS TABLE (returned_state text, returned_cleanup_task_id uuid)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_cancellation hwpx_agent.job_cancellation_requests%ROWTYPE;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_record hwpx_agent.idempotency_records%ROWTYPE;
    v_marker hwpx_agent.job_effect_markers%ROWTYPE;
    v_outcome text;
    v_attempt_state text;
    v_fingerprint character(64);
    v_now timestamptz := clock_timestamp();
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(
        p_tenant_id, p_project_id, p_subject_sha256
    );
    IF p_cleanup_task_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_workspace_handle = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_attempt_no NOT BETWEEN 1 AND 10 OR p_fencing_token <> p_attempt_no
       OR p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'CANCELLATION_FINALIZE_INVALID';
    END IF;
    SELECT * INTO v_cancellation FROM hwpx_agent.job_cancellation_requests AS cancellation
    WHERE cancellation.tenant_id = p_tenant_id
      AND cancellation.project_id = p_project_id
      AND cancellation.job_id = p_job_id FOR UPDATE;
    IF NOT FOUND OR v_cancellation.subject_sha256 <> p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'CANCELLATION_NOT_FOUND';
    END IF;
    IF v_cancellation.state <> 'requested' THEN
        IF v_cancellation.cleanup_task_id IS NOT NULL
           AND v_cancellation.cleanup_task_id <> p_cleanup_task_id THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'CANCELLATION_CLEANUP_CONFLICT';
        END IF;
        RETURN QUERY SELECT v_cancellation.state, v_cancellation.cleanup_task_id;
        RETURN;
    END IF;
    SELECT * INTO v_job FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
      AND job.job_id = p_job_id FOR UPDATE;
    SELECT * INTO v_record FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = p_tenant_id AND record.project_id = p_project_id
      AND record.idempotency_key = p_idempotency_key FOR UPDATE;
    IF v_job.state_machine_version IS DISTINCT FROM 2
       OR v_job.state NOT IN ('leased', 'staged', 'executing', 'validating')
       OR v_job.cancellation_requested_at IS NULL
       OR ROW(v_job.lease_owner_agent_id, v_job.active_execution_id,
              v_job.attempt_count, v_job.fencing_token)
          IS DISTINCT FROM ROW(p_agent_instance_id, p_execution_id,
                               p_attempt_no, p_fencing_token)
       OR v_job.lease_expires_at <= v_now
       OR v_record.record_version IS DISTINCT FROM 2
       OR v_record.state <> 'in_progress' OR v_record.job_id <> p_job_id
       OR v_record.subject_sha256 <> p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'CANCELLATION_LEASE_MISMATCH';
    END IF;
    SELECT * INTO v_marker FROM hwpx_agent.job_effect_markers AS marker
    WHERE marker.tenant_id = p_tenant_id AND marker.project_id = p_project_id
      AND marker.job_id = p_job_id AND marker.attempt_no = p_attempt_no;
    IF NOT FOUND THEN
        v_outcome := 'cancelled';
    ELSIF v_marker.phase = 'started' THEN
        v_outcome := 'outcome_unknown';
    ELSE
        v_outcome := 'too_late';
    END IF;
    IF v_outcome = 'too_late' THEN
        PERFORM set_config('hwpx_agent.allow_cancel_cleanup_v1_transition', 'on', true);
        UPDATE hwpx_agent.jobs SET cancellation_requested_at = NULL, updated_at = v_now
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
        PERFORM set_config('hwpx_agent.allow_cancel_cleanup_v1_transition', 'off', true);
        UPDATE hwpx_agent.job_cancellation_requests SET
            state = 'too_late', resolved_at = v_now
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
        INSERT INTO hwpx_agent.audit_events (
            tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
        ) VALUES (
            p_tenant_id, p_project_id, 'job.cancel_too_late',
            p_subject_sha256, p_job_id, p_event_sha256
        );
        RETURN QUERY SELECT 'too_late'::text, NULL::uuid;
        RETURN;
    END IF;
    v_fingerprint := encode(sha256(convert_to(concat_ws('|',
        'workspace', p_tenant_id::text, p_project_id::text, p_job_id::text,
        p_workspace_handle::text, p_execution_id::text,
        p_attempt_no::text, p_fencing_token::text
    ), 'UTF8')), 'hex');
    INSERT INTO hwpx_agent.cleanup_tasks (
        tenant_id, project_id, job_id, cleanup_task_id, target_fingerprint,
        target_kind, workspace_handle, source_execution_id,
        source_attempt_no, source_fencing_token, created_at, updated_at
    ) VALUES (
        p_tenant_id, p_project_id, p_job_id, p_cleanup_task_id, v_fingerprint,
        'workspace', p_workspace_handle, p_execution_id,
        p_attempt_no, p_fencing_token, v_now, v_now
    );
    DELETE FROM hwpx_agent.idempotency_commit_authorizations
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND idempotency_key = p_idempotency_key AND job_id = p_job_id
      AND attempt_no = p_attempt_no AND fencing_token = p_fencing_token;
    v_attempt_state := CASE
        WHEN v_job.state IN ('leased', 'staged') THEN 'leased' ELSE 'running'
    END;
    PERFORM set_config('hwpx_agent.allow_cancel_cleanup_v1_transition', 'on', true);
    UPDATE hwpx_agent.job_attempts SET
        state = CASE WHEN v_outcome = 'cancelled' THEN 'cancelled' ELSE 'unknown_outcome' END,
        receipt_artifact_id = v_cancellation.request_receipt_artifact_id,
        completed_at = v_now, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id
      AND attempt_no = p_attempt_no AND execution_id = p_execution_id
      AND agent_instance_id = p_agent_instance_id AND fencing_token = p_fencing_token
      AND state_machine_version = 2 AND state = v_attempt_state;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'CANCELLATION_ATTEMPT_MISMATCH';
    END IF;
    UPDATE hwpx_agent.jobs SET
        state = CASE WHEN v_outcome = 'cancelled' THEN 'cancelled' ELSE 'unknown_outcome' END,
        lease_owner_agent_id = NULL, active_execution_id = NULL,
        lease_issued_at = NULL, lease_expires_at = NULL,
        terminal_error_code = CASE
            WHEN v_outcome = 'cancelled' THEN 'JOB_CANCELLED' ELSE 'OUTCOME_UNKNOWN'
        END,
        completed_at = CASE WHEN v_outcome = 'cancelled' THEN v_now ELSE NULL END,
        updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    UPDATE hwpx_agent.idempotency_records SET
        state = CASE
            WHEN v_outcome = 'cancelled' THEN 'terminal_failure' ELSE 'outcome_unknown'
        END,
        receipt_artifact_id = v_cancellation.request_receipt_artifact_id,
        terminal_error_code = CASE
            WHEN v_outcome = 'cancelled' THEN 'JOB_CANCELLED' ELSE 'OUTCOME_UNKNOWN'
        END,
        retry_not_before = NULL,
        last_retry_class = CASE
            WHEN v_outcome = 'outcome_unknown' THEN 'automation_unknown' ELSE last_retry_class
        END,
        updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND idempotency_key = p_idempotency_key;
    PERFORM set_config('hwpx_agent.allow_cancel_cleanup_v1_transition', 'off', true);
    UPDATE hwpx_agent.job_cancellation_requests SET
        state = v_outcome, cleanup_task_id = p_cleanup_task_id, resolved_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, concat('job.cancel_', v_outcome),
        p_subject_sha256, p_job_id, p_event_sha256
    );
    RETURN QUERY SELECT v_outcome, p_cleanup_task_id;
END
$$;

CREATE FUNCTION hwpx_agent.queue_orphan_cleanup_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_job_id uuid,
    p_cleanup_task_id uuid,
    p_artifact_id uuid,
    p_event_sha256 character(64)
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_existing hwpx_agent.cleanup_tasks%ROWTYPE;
    v_artifact hwpx_agent.artifacts%ROWTYPE;
    v_fingerprint character(64);
    v_now timestamptz := clock_timestamp();
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(
        p_tenant_id, p_project_id, p_subject_sha256
    );
    IF p_cleanup_task_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_artifact_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_event_sha256 !~ '^[0-9a-f]{64}$'
       OR NOT EXISTS (
            SELECT 1 FROM hwpx_agent.jobs AS job
            WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
              AND job.job_id = p_job_id
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'ORPHAN_CLEANUP_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_existing FROM hwpx_agent.cleanup_tasks AS task
    WHERE task.tenant_id = p_tenant_id AND task.cleanup_task_id = p_cleanup_task_id;
    IF FOUND THEN
        IF v_existing.project_id <> p_project_id OR v_existing.job_id <> p_job_id
           OR v_existing.target_kind <> 'orphan_artifact'
           OR v_existing.artifact_id <> p_artifact_id THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'CLEANUP_TASK_IDENTITY_CONFLICT';
        END IF;
        RETURN p_cleanup_task_id;
    END IF;
    SELECT * INTO v_artifact FROM hwpx_agent.artifacts AS artifact
    WHERE artifact.tenant_id = p_tenant_id AND artifact.artifact_id = p_artifact_id
    FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'CLEANUP_ARTIFACT_NOT_FOUND';
    END IF;
    IF v_artifact.artifact_kind = 'source' THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'CLEANUP_SOURCE_PROTECTED';
    END IF;
    IF NOT hwpx_agent.cleanup_artifact_qualified_v1(
        p_tenant_id, p_subject_sha256, p_artifact_id
    ) THEN
        IF hwpx_agent.cleanup_artifact_is_referenced_v1(p_tenant_id, p_artifact_id) THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'CLEANUP_TARGET_REFERENCED';
        END IF;
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'CLEANUP_ARTIFACT_NOT_QUALIFIED';
    END IF;
    v_fingerprint := encode(sha256(convert_to(concat_ws('|',
        'orphan_artifact', p_tenant_id::text, p_artifact_id::text,
        v_artifact.content_sha256, v_artifact.artifact_kind
    ), 'UTF8')), 'hex');
    INSERT INTO hwpx_agent.cleanup_tasks (
        tenant_id, project_id, job_id, cleanup_task_id, target_fingerprint,
        target_kind, artifact_id, artifact_content_sha256, artifact_kind,
        created_at, updated_at
    ) VALUES (
        p_tenant_id, p_project_id, p_job_id, p_cleanup_task_id, v_fingerprint,
        'orphan_artifact', p_artifact_id, v_artifact.content_sha256,
        v_artifact.artifact_kind, v_now, v_now
    );
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'cleanup.orphan_queued', p_subject_sha256,
        p_job_id, p_event_sha256
    );
    RETURN p_cleanup_task_id;
END
$$;

CREATE FUNCTION hwpx_agent.claim_cleanup_task_v1(
    p_tenant_id uuid,
    p_subject_sha256 character(64),
    p_worker_id uuid,
    p_cleanup_execution_id uuid,
    p_lease_seconds integer,
    p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_cleanup_task_id uuid,
    returned_project_id uuid,
    returned_job_id uuid,
    returned_target_kind text,
    returned_workspace_handle uuid,
    returned_artifact_id uuid,
    returned_artifact_content_sha256 character(64),
    returned_artifact_kind text,
    returned_source_execution_id uuid,
    returned_source_attempt_no integer,
    returned_source_fencing_token bigint,
    returned_attempt_count integer,
    returned_fencing_token bigint,
    returned_lease_expires_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_task hwpx_agent.cleanup_tasks%ROWTYPE;
    v_now timestamptz := clock_timestamp();
    v_expires timestamptz;
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256
       OR p_worker_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_cleanup_execution_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_lease_seconds NOT BETWEEN 1 AND 300
       OR p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'CLEANUP_CLAIM_REQUEST_INVALID';
    END IF;
    v_expires := v_now + make_interval(secs => p_lease_seconds);
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.worker_registrations AS worker
        WHERE worker.tenant_id = p_tenant_id AND worker.agent_instance_id = p_worker_id
          AND worker.subject_sha256 = p_subject_sha256 AND worker.state = 'ready'
          AND worker.last_heartbeat_at <= v_now AND worker.expires_at >= v_expires
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'CLEANUP_WORKER_NOT_QUALIFIED';
    END IF;
    UPDATE hwpx_agent.cleanup_tasks SET
        state = 'failed_terminal', lease_worker_id = NULL, lease_execution_id = NULL,
        lease_issued_at = NULL, lease_expires_at = NULL,
        completed_at = v_now, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND state = 'leased'
      AND lease_expires_at <= v_now AND attempt_count = 3;
    SELECT task.* INTO v_task FROM hwpx_agent.cleanup_tasks AS task
    JOIN hwpx_agent.project_acl AS acl
      ON acl.tenant_id = task.tenant_id AND acl.project_id = task.project_id
     AND acl.subject_sha256 = p_subject_sha256 AND acl.role IN ('editor', 'owner')
    WHERE task.tenant_id = p_tenant_id
      AND (
          task.state = 'pending'
          OR (task.state = 'leased' AND task.lease_expires_at <= v_now)
      )
      AND task.attempt_count < 3
      AND (
          task.target_kind = 'workspace'
          OR NOT hwpx_agent.cleanup_artifact_is_referenced_v1(
              p_tenant_id, task.artifact_id
          )
      )
    ORDER BY task.created_at, task.cleanup_task_id
    FOR UPDATE OF task SKIP LOCKED
    LIMIT 1;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'CLEANUP_TASK_NOT_FOUND';
    END IF;
    IF v_task.target_kind = 'orphan_artifact' THEN
        IF hwpx_agent.cleanup_artifact_is_referenced_v1(p_tenant_id, v_task.artifact_id) THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'CLEANUP_TARGET_REFERENCED';
        END IF;
        IF NOT EXISTS (
            SELECT 1 FROM hwpx_agent.artifacts AS artifact
            JOIN hwpx_agent.artifact_acl AS acl
              ON acl.tenant_id = artifact.tenant_id AND acl.artifact_id = artifact.artifact_id
            WHERE artifact.tenant_id = p_tenant_id
              AND artifact.artifact_id = v_task.artifact_id
              AND artifact.content_sha256 = v_task.artifact_content_sha256
              AND artifact.artifact_kind = v_task.artifact_kind
              AND artifact.service_metadata_version = 1
              AND artifact.storage_state IN ('available', 'purging')
              AND artifact.validation_state = 'verified'
              AND acl.subject_sha256 = p_subject_sha256 AND acl.can_manage
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'CLEANUP_TARGET_DRIFT';
        END IF;
        IF EXISTS (
            SELECT 1 FROM hwpx_agent.artifacts AS artifact
            WHERE artifact.tenant_id = p_tenant_id AND artifact.artifact_id = v_task.artifact_id
              AND artifact.storage_state = 'available'
        ) THEN
            UPDATE hwpx_agent.artifacts SET
                storage_state = 'purging', authorization_generation = authorization_generation + 1,
                updated_at = v_now
            WHERE tenant_id = p_tenant_id AND artifact_id = v_task.artifact_id;
        END IF;
    END IF;
    UPDATE hwpx_agent.cleanup_tasks SET
        state = 'leased', attempt_count = attempt_count + 1,
        lease_worker_id = p_worker_id, lease_execution_id = p_cleanup_execution_id,
        lease_fencing_token = attempt_count + 1,
        lease_issued_at = v_now, lease_expires_at = v_expires, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND cleanup_task_id = v_task.cleanup_task_id
    RETURNING * INTO v_task;
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, v_task.project_id, 'cleanup.task_leased', p_subject_sha256,
        v_task.job_id, p_event_sha256
    );
    RETURN QUERY SELECT
        v_task.cleanup_task_id, v_task.project_id, v_task.job_id, v_task.target_kind,
        v_task.workspace_handle, v_task.artifact_id, v_task.artifact_content_sha256,
        v_task.artifact_kind, v_task.source_execution_id, v_task.source_attempt_no,
        v_task.source_fencing_token, v_task.attempt_count, v_task.lease_fencing_token,
        v_task.lease_expires_at;
END
$$;

CREATE FUNCTION hwpx_agent.complete_cleanup_task_v1(
    p_tenant_id uuid,
    p_subject_sha256 character(64),
    p_cleanup_task_id uuid,
    p_worker_id uuid,
    p_cleanup_execution_id uuid,
    p_attempt_no integer,
    p_fencing_token bigint,
    p_outcome text,
    p_proof_sha256 character(64),
    p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_state text,
    returned_outcome text,
    returned_proof_sha256 character(64),
    returned_completed_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_task hwpx_agent.cleanup_tasks%ROWTYPE;
    v_now timestamptz := clock_timestamp();
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256
       OR p_attempt_no NOT BETWEEN 1 AND 3 OR p_fencing_token <> p_attempt_no
       OR p_proof_sha256 !~ '^[0-9a-f]{64}$'
       OR p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'CLEANUP_COMPLETE_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_task FROM hwpx_agent.cleanup_tasks AS task
    WHERE task.tenant_id = p_tenant_id AND task.cleanup_task_id = p_cleanup_task_id
    FOR UPDATE;
    IF NOT FOUND OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.project_acl AS acl
        WHERE acl.tenant_id = p_tenant_id AND acl.project_id = v_task.project_id
          AND acl.subject_sha256 = p_subject_sha256 AND acl.role IN ('editor', 'owner')
    ) THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'CLEANUP_TASK_NOT_FOUND';
    END IF;
    IF v_task.state = 'succeeded' THEN
        IF v_task.outcome <> p_outcome OR v_task.proof_sha256 <> p_proof_sha256 THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'CLEANUP_RECEIPT_CONFLICT';
        END IF;
        RETURN QUERY SELECT v_task.state, v_task.outcome,
            v_task.proof_sha256, v_task.completed_at;
        RETURN;
    END IF;
    IF v_task.state <> 'leased'
       OR ROW(v_task.lease_worker_id, v_task.lease_execution_id,
              v_task.attempt_count, v_task.lease_fencing_token)
          IS DISTINCT FROM ROW(p_worker_id, p_cleanup_execution_id,
                               p_attempt_no, p_fencing_token)
       OR v_task.lease_issued_at > v_now OR v_task.lease_expires_at <= v_now THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'CLEANUP_LEASE_MISMATCH';
    END IF;
    IF (v_task.target_kind = 'workspace'
        AND p_outcome NOT IN ('workspace_removed', 'workspace_already_absent'))
       OR (v_task.target_kind = 'orphan_artifact'
           AND p_outcome NOT IN ('artifact_quarantined', 'artifact_already_quarantined')) THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'CLEANUP_OUTCOME_INVALID';
    END IF;
    IF v_task.target_kind = 'orphan_artifact' THEN
        IF hwpx_agent.cleanup_artifact_is_referenced_v1(p_tenant_id, v_task.artifact_id) THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'CLEANUP_TARGET_REFERENCED';
        END IF;
        IF NOT EXISTS (
            SELECT 1 FROM hwpx_agent.artifacts AS artifact
            WHERE artifact.tenant_id = p_tenant_id
              AND artifact.artifact_id = v_task.artifact_id
              AND artifact.content_sha256 = v_task.artifact_content_sha256
              AND artifact.artifact_kind = v_task.artifact_kind
              AND artifact.service_metadata_version = 1
              AND artifact.storage_state = 'purging'
              AND artifact.validation_state = 'verified'
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'CLEANUP_TARGET_DRIFT';
        END IF;
        UPDATE hwpx_agent.artifacts SET
            storage_state = 'quarantined', validation_state = 'quarantined',
            quarantine_reason_code = 'ORPHAN_CLEANUP',
            object_key = concat(
                'artifacts/v1/', replace(tenant_id::text, '-', ''), '/', artifact_kind,
                '/quarantined/', content_sha256, '.aes256gcm'
            ),
            authorization_generation = authorization_generation + 1,
            updated_at = v_now
        WHERE tenant_id = p_tenant_id AND artifact_id = v_task.artifact_id;
    END IF;
    UPDATE hwpx_agent.cleanup_tasks SET
        state = 'succeeded', lease_worker_id = NULL, lease_execution_id = NULL,
        lease_issued_at = NULL, lease_expires_at = NULL,
        outcome = p_outcome, proof_sha256 = p_proof_sha256,
        completed_at = v_now, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND cleanup_task_id = p_cleanup_task_id
    RETURNING * INTO v_task;
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, v_task.project_id, 'cleanup.task_succeeded', p_subject_sha256,
        v_task.job_id, p_event_sha256
    );
    RETURN QUERY SELECT v_task.state, v_task.outcome,
        v_task.proof_sha256, v_task.completed_at;
END
$$;

REVOKE ALL ON FUNCTION hwpx_agent.protect_cancel_cleanup_identity() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.cleanup_artifact_is_referenced_v1(uuid, uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.cleanup_artifact_qualified_v1(uuid, character, uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.request_job_cancellation_v1(
    uuid, uuid, character, uuid, uuid, uuid, uuid, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.mark_job_effect_phase_v1(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, text, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.finalize_job_cancellation_v1(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    uuid, uuid, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.queue_orphan_cleanup_v1(
    uuid, uuid, character, uuid, uuid, uuid, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.claim_cleanup_task_v1(
    uuid, character, uuid, uuid, integer, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.complete_cleanup_task_v1(
    uuid, character, uuid, uuid, uuid, integer, bigint, text, character, character
) FROM PUBLIC;

INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (8, 'p14.cancel_cleanup_v1', current_setting('hwpx_agent.migration_sha256'));

COMMIT;
