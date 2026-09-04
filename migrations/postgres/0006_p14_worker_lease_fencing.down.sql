BEGIN;

DO $$
BEGIN
    IF current_setting('hwpx_agent.allow_destructive_rollback', true) IS DISTINCT FROM 'on' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 worker lease rollback requires explicit hwpx_agent.allow_destructive_rollback=on';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 6 AND migration_name = 'p14.worker_lease_fencing_v1'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 worker lease migration version 6 is not installed';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version > 6) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 worker lease rollback requires later migrations removed first';
    END IF;
END
$$;

DROP FUNCTION hwpx_agent.expire_job_lease(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, uuid, character
);
DROP FUNCTION hwpx_agent.heartbeat_job_lease(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, integer, character
);
DROP FUNCTION hwpx_agent.heartbeat_scheduler_worker(
    uuid, character, uuid, text, character, text, integer, character
);
DROP FUNCTION hwpx_agent.register_scheduler_worker(
    uuid, character, uuid, text, character, text, integer, character
);

CREATE OR REPLACE FUNCTION hwpx_agent.guard_job_state_machine_update()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog
AS $$
DECLARE
    v_stage_lease_unchanged boolean;
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
           OR NEW.cancellation_requested_at IS NOT NULL THEN
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
SECURITY INVOKER
SET search_path = pg_catalog
AS $$
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
    IF OLD.state_machine_version IS DISTINCT FROM NEW.state_machine_version
       OR OLD.lease_expires_at IS DISTINCT FROM NEW.lease_expires_at THEN
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

DROP TRIGGER worker_registrations_guard ON hwpx_agent.worker_registrations;
DROP FUNCTION hwpx_agent.guard_worker_registration_update();
DROP INDEX hwpx_agent.worker_registrations_eligibility_idx;
DROP TABLE hwpx_agent.worker_registrations;

ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions WHERE version = 6;
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;

COMMIT;
