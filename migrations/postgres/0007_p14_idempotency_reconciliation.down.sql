BEGIN;

DO $$
BEGIN
    IF current_setting('hwpx_agent.allow_destructive_rollback', true) IS DISTINCT FROM 'on' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 idempotency reconciliation rollback requires explicit hwpx_agent.allow_destructive_rollback=on';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 7 AND migration_name = 'p14.idempotency_reconciliation_v2'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 idempotency reconciliation migration version 7 is not installed';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version > 7) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 idempotency reconciliation rollback requires later migrations removed first';
    END IF;
    IF EXISTS (
        SELECT 1 FROM hwpx_agent.idempotency_records WHERE record_version = 2
    ) OR EXISTS (
        SELECT 1 FROM hwpx_agent.jobs WHERE state_machine_version = 2
    ) OR EXISTS (
        SELECT 1 FROM hwpx_agent.job_attempts WHERE state_machine_version = 2
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 idempotency reconciliation rollback refuses remaining version 2 data';
    END IF;
END
$$;

DROP FUNCTION hwpx_agent.get_idempotent_job_v2(uuid, uuid, character, uuid);
DROP FUNCTION hwpx_agent.commit_idempotent_revision_cas_v2(
    uuid, uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    uuid, uuid, uuid, bigint, uuid, uuid[], uuid, uuid, uuid,
    character, text, character, character, character, character
);
DROP FUNCTION hwpx_agent.reconcile_idempotent_job_v2(
    uuid, uuid, character, uuid, uuid, text, uuid, uuid, character
);
DROP FUNCTION hwpx_agent.fail_idempotent_job_terminal_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    text, text, uuid, character
);
DROP FUNCTION hwpx_agent.complete_idempotent_job_success_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    uuid, uuid, character
);
DROP FUNCTION hwpx_agent.mark_idempotent_outcome_unknown_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    uuid, character
);
DROP FUNCTION hwpx_agent.schedule_idempotent_retry_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    text, uuid, character
);
DROP FUNCTION hwpx_agent.heartbeat_idempotent_job_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    integer, character
);
DROP FUNCTION hwpx_agent.advance_idempotent_job_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    text, text, character
);
DROP FUNCTION hwpx_agent.lease_idempotent_job_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, character
);
DROP FUNCTION hwpx_agent.claim_idempotent_job_v2(
    uuid, uuid, uuid, character, uuid, uuid, uuid, uuid, uuid, bigint,
    character, character, character, character, character, character,
    text, character, integer, integer, integer, integer, character
);
DROP FUNCTION hwpx_agent.idempotency_v2_retry_at(timestamptz, integer, integer, integer);
DROP FUNCTION hwpx_agent.idempotency_v2_committed_effect_qualified(
    uuid, uuid, uuid, character, uuid, character, uuid, bigint,
    character, uuid, character, character, uuid
);
DROP FUNCTION hwpx_agent.idempotency_v2_head_matches(uuid, uuid, uuid, uuid, bigint);
DROP FUNCTION hwpx_agent.idempotency_v2_artifact_qualified(
    uuid, character, uuid, text, character
);
DROP FUNCTION hwpx_agent.require_idempotency_v2_editor(uuid, uuid, character);

DROP TRIGGER revision_commit_receipts_idempotency_v2_guard
    ON hwpx_agent.revision_commit_receipts;
DROP FUNCTION hwpx_agent.guard_idempotent_revision_commit_v2();
DROP TABLE hwpx_agent.idempotency_commit_authorizations;

DROP TRIGGER idempotency_job_consistency_from_record ON hwpx_agent.idempotency_records;
DROP TRIGGER idempotency_job_consistency_from_job ON hwpx_agent.jobs;
DROP FUNCTION hwpx_agent.verify_idempotency_job_consistency();

DROP INDEX hwpx_agent.idempotency_v2_retry_ready_idx;
DROP INDEX hwpx_agent.idempotency_v2_job_unique_idx;
DROP INDEX hwpx_agent.idempotency_v2_transaction_unique_idx;
DROP INDEX hwpx_agent.jobs_idempotency_v2_ready_idx;

CREATE OR REPLACE FUNCTION hwpx_agent.protect_idempotency_identity()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    IF ROW(
        NEW.tenant_id,
        NEW.project_id,
        NEW.idempotency_key,
        NEW.request_sha256,
        NEW.created_at
    ) IS DISTINCT FROM ROW(
        OLD.tenant_id,
        OLD.project_id,
        OLD.idempotency_key,
        OLD.request_sha256,
        OLD.created_at
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'idempotency identity is immutable';
    END IF;
    RETURN NEW;
END
$$;

ALTER TABLE hwpx_agent.idempotency_records
    DROP CONSTRAINT idempotency_v2_branch_fk,
    DROP CONSTRAINT idempotency_v2_source_artifact_fk,
    DROP CONSTRAINT idempotency_v2_expected_revision_fk,
    DROP CONSTRAINT idempotency_record_version_value,
    DROP CONSTRAINT idempotency_state_value,
    DROP CONSTRAINT idempotency_v2_digest_format,
    DROP CONSTRAINT idempotency_v2_retry_class,
    DROP CONSTRAINT idempotency_v2_metadata_complete,
    DROP CONSTRAINT idempotency_terminal_consistency,
    DROP CONSTRAINT idempotency_time_order,
    DROP COLUMN record_version,
    DROP COLUMN subject_sha256,
    DROP COLUMN branch_id,
    DROP COLUMN request_id,
    DROP COLUMN source_artifact_id,
    DROP COLUMN expected_revision_id,
    DROP COLUMN expected_revision_generation,
    DROP COLUMN execution_manifest_sha256,
    DROP COLUMN source_artifact_sha256,
    DROP COLUMN expected_effect_sha256,
    DROP COLUMN transaction_receipt_sha256,
    DROP COLUMN max_attempts,
    DROP COLUMN base_delay_seconds,
    DROP COLUMN max_delay_seconds,
    DROP COLUMN attempt_count,
    DROP COLUMN last_fencing_token,
    DROP COLUMN retry_not_before,
    DROP COLUMN last_retry_class,
    ADD CONSTRAINT idempotency_state_value CHECK (
        state IN ('claimed', 'terminal_success', 'terminal_failure', 'unknown_outcome')
    ),
    ADD CONSTRAINT idempotency_terminal_consistency CHECK (
        (state = 'claimed' AND result_revision_id IS NULL AND receipt_artifact_id IS NULL)
        OR (
            state = 'terminal_success'
            AND result_revision_id IS NOT NULL
            AND receipt_artifact_id IS NOT NULL
            AND terminal_error_code IS NULL
        )
        OR (
            state IN ('terminal_failure', 'unknown_outcome')
            AND result_revision_id IS NULL
            AND receipt_artifact_id IS NOT NULL
            AND terminal_error_code IS NOT NULL
        )
    ),
    ADD CONSTRAINT idempotency_time_order CHECK (
        updated_at >= created_at AND expires_at > created_at
    );

ALTER TABLE hwpx_agent.jobs
    DROP CONSTRAINT jobs_state_value,
    DROP CONSTRAINT jobs_terminal_time_consistency,
    DROP CONSTRAINT jobs_state_machine_version,
    DROP CONSTRAINT jobs_state_machine_complete_v7,
    ADD CONSTRAINT jobs_state_value CHECK (
        state IN (
            'queued', 'leased', 'staged', 'executing', 'validating',
            'succeeded', 'failed', 'cancelled', 'unknown_outcome'
        )
    ),
    ADD CONSTRAINT jobs_terminal_time_consistency CHECK (
        (state IN ('succeeded', 'failed', 'cancelled', 'unknown_outcome')) =
        (completed_at IS NOT NULL)
    ),
    ADD CONSTRAINT jobs_state_machine_version CHECK (
        state_machine_version IS NULL OR state_machine_version = 1
    ),
    ADD CONSTRAINT jobs_state_machine_v1_complete CHECK (
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
                    state = 'queued'
                    AND attempt_count = 0
                    AND lease_owner_agent_id IS NULL
                    AND active_execution_id IS NULL
                    AND fencing_token = 0
                    AND lease_issued_at IS NULL
                    AND lease_expires_at IS NULL
                    AND result_revision_id IS NULL
                    AND terminal_error_code IS NULL
                    AND completed_at IS NULL
                )
                OR (
                    state IN ('leased', 'staged', 'executing', 'validating')
                    AND attempt_count = 1
                    AND lease_owner_agent_id IS NOT NULL
                    AND active_execution_id IS NOT NULL
                    AND fencing_token = 1
                    AND lease_issued_at IS NOT NULL
                    AND lease_expires_at > lease_issued_at
                    AND lease_expires_at <= lease_issued_at + interval '1 hour'
                    AND result_revision_id IS NULL
                    AND terminal_error_code IS NULL
                    AND completed_at IS NULL
                )
                OR (
                    state IN ('succeeded', 'failed')
                    AND attempt_count = 1
                    AND lease_owner_agent_id IS NULL
                    AND active_execution_id IS NULL
                    AND fencing_token = 1
                    AND lease_issued_at IS NULL
                    AND lease_expires_at IS NULL
                    AND completed_at IS NOT NULL
                )
            )
        )
    );

ALTER TABLE hwpx_agent.job_attempts
    DROP CONSTRAINT job_attempts_state_machine_version,
    DROP CONSTRAINT job_attempts_state_machine_complete_v7,
    ADD CONSTRAINT job_attempts_state_machine_version CHECK (
        state_machine_version IS NULL OR state_machine_version = 1
    ),
    ADD CONSTRAINT job_attempts_state_machine_v1_complete CHECK (
        (
            state_machine_version IS NULL
            AND lease_expires_at IS NULL
            AND updated_at IS NULL
        )
        OR (
            state_machine_version = 1
            AND attempt_no = 1
            AND fencing_token = 1
            AND state IN ('leased', 'running', 'succeeded', 'failed')
            AND lease_expires_at > started_at
            AND lease_expires_at <= started_at + interval '1 hour'
            AND updated_at >= started_at
            AND (completed_at IS NULL OR updated_at >= completed_at)
        )
    );

-- Restore the exact version-6 worker qualification, heartbeat and expiry behavior.
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
    IF OLD.state IN ('succeeded', 'failed', 'cancelled', 'unknown_outcome') THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_TERMINAL_IMMUTABLE';
    END IF;
    IF OLD.state IN ('leased', 'staged', 'executing', 'validating')
       AND NEW.state IS DISTINCT FROM OLD.state
       AND OLD.lease_expires_at <= v_now
       AND NOT (
            v_expiry_allowed
            AND NEW.state = 'failed'
            AND NEW.terminal_error_code = 'LEASE_EXPIRED'
       ) THEN
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
           OR OLD.lease_expires_at <= v_now
           OR NEW.lease_expires_at <= OLD.lease_expires_at
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
            SELECT 1
            FROM hwpx_agent.worker_registrations AS worker
            WHERE worker.tenant_id = NEW.tenant_id
              AND worker.agent_instance_id = NEW.lease_owner_agent_id
              AND worker.subject_sha256 = hwpx_agent.current_subject_sha256()
              AND worker.target_profile_id = NEW.required_target_profile_id
              AND worker.capability_set_sha256 = NEW.required_capability_set_sha256
              AND worker.state = 'ready'
              AND worker.last_heartbeat_at <= v_now
              AND worker.expires_at > v_now
              AND NEW.lease_expires_at > v_now
              AND NEW.lease_expires_at <= worker.expires_at
        ) INTO v_worker_qualified;
        IF NOT v_worker_qualified THEN
            RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'JOB_WORKER_NOT_QUALIFIED';
        END IF;
        IF NEW.attempt_count <> 1
           OR NEW.lease_owner_agent_id IS NULL
           OR NEW.active_execution_id IS NULL
           OR NEW.fencing_token <> 1
           OR NEW.lease_issued_at IS NULL
           OR NEW.lease_expires_at IS NULL
           OR NEW.result_revision_id IS NOT NULL
           OR NEW.terminal_error_code IS NOT NULL
           OR NEW.completed_at IS NOT NULL THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_LEASE_TRANSITION_INVALID';
        END IF;
    ELSIF ROW(OLD.state, NEW.state) IN (
        ROW('leased', 'staged'),
        ROW('staged', 'executing'),
        ROW('executing', 'validating')
    ) THEN
        IF NOT v_stage_lease_unchanged THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_STAGE_LEASE_DRIFT';
        END IF;
    ELSIF OLD.state = 'validating' AND NEW.state = 'succeeded' THEN
        IF NEW.attempt_count <> OLD.attempt_count
           OR NEW.fencing_token <> OLD.fencing_token
           OR NEW.lease_owner_agent_id IS NOT NULL
           OR NEW.active_execution_id IS NOT NULL
           OR NEW.lease_issued_at IS NOT NULL
           OR NEW.lease_expires_at IS NOT NULL
           OR NEW.result_revision_id IS NULL
           OR NEW.terminal_error_code IS NOT NULL
           OR NEW.completed_at IS NULL
           OR NEW.cancellation_requested_at IS NOT NULL THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_SUCCESS_TRANSITION_INVALID';
        END IF;
    ELSIF OLD.state IN ('leased', 'staged', 'executing', 'validating')
          AND NEW.state = 'failed' THEN
        IF NEW.attempt_count <> OLD.attempt_count
           OR NEW.fencing_token <> OLD.fencing_token
           OR NEW.lease_owner_agent_id IS NOT NULL
           OR NEW.active_execution_id IS NOT NULL
           OR NEW.lease_issued_at IS NOT NULL
           OR NEW.lease_expires_at IS NOT NULL
           OR NEW.result_revision_id IS NOT NULL
           OR NEW.terminal_error_code IS NULL
           OR NEW.completed_at IS NULL
           OR NEW.cancellation_requested_at IS NOT NULL
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
    IF NEW.state = OLD.state
       AND NEW.lease_expires_at IS DISTINCT FROM OLD.lease_expires_at THEN
        IF NOT v_heartbeat_allowed
           OR OLD.state NOT IN ('leased', 'running')
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
    v_tenant_id uuid;
    v_project_id uuid;
    v_job_id uuid;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_attempt hwpx_agent.job_attempts%ROWTYPE;
    v_attempt_count bigint;
BEGIN
    v_tenant_id := COALESCE(NEW.tenant_id, OLD.tenant_id);
    v_project_id := COALESCE(NEW.project_id, OLD.project_id);
    v_job_id := COALESCE(NEW.job_id, OLD.job_id);
    SELECT * INTO v_job
    FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = v_tenant_id
      AND job.project_id = v_project_id
      AND job.job_id = v_job_id;
    IF NOT FOUND OR v_job.state_machine_version IS NULL THEN
        RETURN NULL;
    END IF;
    SELECT count(*) INTO v_attempt_count
    FROM hwpx_agent.job_attempts AS attempt
    WHERE attempt.tenant_id = v_tenant_id
      AND attempt.project_id = v_project_id
      AND attempt.job_id = v_job_id
      AND attempt.state_machine_version = 1;
    IF v_job.state = 'queued' THEN
        IF v_attempt_count <> 0 THEN
            RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'JOB_ATTEMPT_CONSISTENCY_INVALID';
        END IF;
        RETURN NULL;
    END IF;
    IF v_attempt_count <> 1 THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'JOB_ATTEMPT_CONSISTENCY_INVALID';
    END IF;
    SELECT * INTO STRICT v_attempt
    FROM hwpx_agent.job_attempts AS attempt
    WHERE attempt.tenant_id = v_tenant_id
      AND attempt.project_id = v_project_id
      AND attempt.job_id = v_job_id
      AND attempt.attempt_no = v_job.attempt_count
      AND attempt.state_machine_version = 1;
    IF v_job.state IN ('leased', 'staged', 'executing', 'validating')
       AND ROW(
            v_attempt.agent_instance_id, v_attempt.execution_id,
            v_attempt.started_at, v_attempt.lease_expires_at
       ) IS DISTINCT FROM ROW(
            v_job.lease_owner_agent_id, v_job.active_execution_id,
            v_job.lease_issued_at, v_job.lease_expires_at
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'JOB_ATTEMPT_BINDING_INVALID';
    END IF;
    IF v_attempt.fencing_token <> v_job.fencing_token
       OR (v_job.state IN ('leased', 'staged') AND v_attempt.state <> 'leased')
       OR (v_job.state IN ('executing', 'validating') AND v_attempt.state <> 'running')
       OR (v_job.state = 'succeeded' AND v_attempt.state <> 'succeeded')
       OR (v_job.state = 'failed' AND v_attempt.state <> 'failed')
       OR (
            v_job.state IN ('succeeded', 'failed')
            AND v_attempt.completed_at IS DISTINCT FROM v_job.completed_at
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'JOB_ATTEMPT_CONSISTENCY_INVALID';
    END IF;
    RETURN NULL;
END
$$;

ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions WHERE version = 7;
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;

COMMIT;
