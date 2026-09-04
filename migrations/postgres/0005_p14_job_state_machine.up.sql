BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 4 AND migration_name = 'p14.history_checkpoints_v1'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 job state-machine migration requires p14.history_checkpoints_v1';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version = 5) THEN
        RAISE EXCEPTION USING
            ERRCODE = '42710',
            MESSAGE = 'P14 job state-machine migration version 5 already exists';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256', true)
        !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            MESSAGE = 'P14 job state-machine migration requires its exact SHA-256';
    END IF;
END
$$;

-- Existing P14-01 rows stay explicitly unqualified. Only rows created by the v5 functions carry
-- state_machine_version=1 and may participate in this state machine.
ALTER TABLE hwpx_agent.jobs
    ADD COLUMN state_machine_version smallint,
    ADD COLUMN active_execution_id uuid,
    ADD COLUMN lease_issued_at timestamptz,
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
    ADD COLUMN state_machine_version smallint,
    ADD COLUMN lease_expires_at timestamptz,
    ADD COLUMN updated_at timestamptz,
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

CREATE INDEX jobs_state_machine_queue_idx
    ON hwpx_agent.jobs (tenant_id, state, created_at, job_id)
    WHERE state_machine_version = 1 AND state = 'queued';
CREATE INDEX job_attempts_state_machine_active_idx
    ON hwpx_agent.job_attempts (tenant_id, project_id, job_id, state)
    WHERE state_machine_version = 1 AND state IN ('leased', 'running');

CREATE FUNCTION hwpx_agent.guard_job_state_machine_update()
RETURNS trigger
LANGUAGE plpgsql
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

CREATE FUNCTION hwpx_agent.guard_job_attempt_state_machine_update()
RETURNS trigger
LANGUAGE plpgsql
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

CREATE FUNCTION hwpx_agent.verify_job_state_machine_consistency()
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

CREATE TRIGGER jobs_state_machine_guard
BEFORE UPDATE ON hwpx_agent.jobs
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.guard_job_state_machine_update();
CREATE TRIGGER job_attempts_state_machine_guard
BEFORE UPDATE ON hwpx_agent.job_attempts
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.guard_job_attempt_state_machine_update();
CREATE CONSTRAINT TRIGGER jobs_state_machine_consistency
AFTER INSERT OR UPDATE ON hwpx_agent.jobs
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.verify_job_state_machine_consistency();
CREATE CONSTRAINT TRIGGER job_attempts_state_machine_consistency
AFTER INSERT OR UPDATE ON hwpx_agent.job_attempts
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.verify_job_state_machine_consistency();

CREATE FUNCTION hwpx_agent.enqueue_job_state_machine(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_job_id uuid,
    p_request_id uuid,
    p_input_artifact_id uuid,
    p_expected_revision_id uuid,
    p_operation_plan_sha256 character(64),
    p_required_target_profile_id text,
    p_required_capability_set_sha256 character(64)
)
RETURNS TABLE (
    returned_job_id uuid,
    returned_state text,
    returned_attempt_count integer,
    returned_fencing_token bigint,
    returned_result_revision_id uuid,
    returned_terminal_error_code text,
    returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'JOB_CONTEXT_MISMATCH';
    END IF;
    IF p_tenant_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_project_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_job_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_request_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_input_artifact_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_expected_revision_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$'
       OR p_operation_plan_sha256 !~ '^[0-9a-f]{64}$'
       OR p_required_capability_set_sha256 !~ '^[0-9a-f]{64}$'
       OR p_required_target_profile_id !~ '^[A-Za-z0-9][A-Za-z0-9._-]{1,126}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'JOB_REQUEST_INVALID';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.projects AS project
        WHERE project.tenant_id = p_tenant_id
          AND project.project_id = p_project_id
          AND project.state = 'active'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'JOB_PROJECT_NOT_FOUND';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.project_acl AS acl
        WHERE acl.tenant_id = p_tenant_id
          AND acl.project_id = p_project_id
          AND acl.subject_sha256 = p_subject_sha256
          AND acl.role IN ('editor', 'owner')
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'JOB_MUTATION_DENIED';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM hwpx_agent.artifacts AS artifact
        JOIN hwpx_agent.artifact_acl AS acl
          ON acl.tenant_id = artifact.tenant_id
         AND acl.artifact_id = artifact.artifact_id
        WHERE artifact.tenant_id = p_tenant_id
          AND artifact.artifact_id = p_input_artifact_id
          AND artifact.service_metadata_version = 1
          AND artifact.storage_state = 'available'
          AND artifact.validation_state = 'verified'
          AND artifact.artifact_kind IN ('source', 'result')
          AND acl.subject_sha256 = p_subject_sha256
          AND (acl.can_read OR acl.can_manage)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'JOB_INPUT_ARTIFACT_NOT_QUALIFIED';
    END IF;
    IF p_expected_revision_id IS NOT NULL AND NOT EXISTS (
        SELECT 1
        FROM hwpx_agent.revisions AS revision
        JOIN hwpx_agent.revision_graph_seals AS seal
          ON seal.tenant_id = revision.tenant_id
         AND seal.project_id = revision.project_id
         AND seal.revision_id = revision.revision_id
        WHERE revision.tenant_id = p_tenant_id
          AND revision.project_id = p_project_id
          AND revision.revision_id = p_expected_revision_id
          AND seal.seal_kind = 'service_v1'
          AND seal.committed_generation > 0
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'JOB_EXPECTED_REVISION_NOT_QUALIFIED';
    END IF;
    IF EXISTS (
        SELECT 1 FROM hwpx_agent.jobs AS job
        WHERE job.tenant_id = p_tenant_id
          AND job.project_id = p_project_id
          AND (job.job_id = p_job_id OR job.request_id = p_request_id)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23505', MESSAGE = 'JOB_IDENTITY_ALREADY_EXISTS';
    END IF;

    INSERT INTO hwpx_agent.jobs (
        tenant_id, project_id, job_id, request_id, input_artifact_id,
        expected_revision_id, operation_plan_sha256, required_target_profile_id,
        required_capability_set_sha256, state, attempt_count, fencing_token,
        state_machine_version
    ) VALUES (
        p_tenant_id, p_project_id, p_job_id, p_request_id, p_input_artifact_id,
        p_expected_revision_id, p_operation_plan_sha256, p_required_target_profile_id,
        p_required_capability_set_sha256, 'queued', 0, 0, 1
    );
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'job.enqueued', p_subject_sha256,
        p_job_id, p_operation_plan_sha256
    );

    RETURN QUERY SELECT
        p_job_id, 'queued'::text, 0, 0::bigint, NULL::uuid, NULL::text, NULL::uuid;
END
$$;

CREATE FUNCTION hwpx_agent.lease_job_state_machine(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_job_id uuid,
    p_agent_instance_id uuid,
    p_execution_id uuid,
    p_lease_seconds integer,
    p_transition_sha256 character(64)
)
RETURNS TABLE (
    returned_job_id uuid,
    returned_state text,
    returned_attempt_count integer,
    returned_fencing_token bigint,
    returned_result_revision_id uuid,
    returned_terminal_error_code text,
    returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_job hwpx_agent.jobs%ROWTYPE;
    v_now timestamptz := transaction_timestamp();
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'JOB_CONTEXT_MISMATCH';
    END IF;
    IF p_tenant_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_project_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$'
       OR p_job_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_agent_instance_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_execution_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_lease_seconds NOT BETWEEN 1 AND 3600
       OR p_transition_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'JOB_LEASE_REQUEST_INVALID';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.project_acl AS acl
        JOIN hwpx_agent.projects AS project
          ON project.tenant_id = acl.tenant_id AND project.project_id = acl.project_id
        WHERE acl.tenant_id = p_tenant_id
          AND acl.project_id = p_project_id
          AND acl.subject_sha256 = p_subject_sha256
          AND acl.role IN ('editor', 'owner')
          AND project.state = 'active'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'JOB_MUTATION_DENIED';
    END IF;
    SELECT * INTO v_job
    FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id
      AND job.project_id = p_project_id
      AND job.job_id = p_job_id
    FOR UPDATE;
    IF NOT FOUND OR v_job.state_machine_version IS DISTINCT FROM 1 THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'JOB_NOT_FOUND';
    END IF;
    IF v_job.state <> 'queued' THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_TRANSITION_INVALID';
    END IF;

    UPDATE hwpx_agent.jobs
    SET state = 'leased',
        attempt_count = 1,
        lease_owner_agent_id = p_agent_instance_id,
        active_execution_id = p_execution_id,
        fencing_token = 1,
        lease_issued_at = v_now,
        lease_expires_at = v_now + make_interval(secs => p_lease_seconds),
        updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    INSERT INTO hwpx_agent.job_attempts (
        tenant_id, project_id, job_id, attempt_no, execution_id,
        agent_instance_id, fencing_token, state, started_at,
        state_machine_version, lease_expires_at, updated_at
    ) VALUES (
        p_tenant_id, p_project_id, p_job_id, 1, p_execution_id,
        p_agent_instance_id, 1, 'leased', v_now, 1,
        v_now + make_interval(secs => p_lease_seconds), v_now
    );
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'job.leased', p_subject_sha256,
        p_job_id, p_transition_sha256
    );
    RETURN QUERY SELECT
        p_job_id, 'leased'::text, 1, 1::bigint, NULL::uuid, NULL::text, NULL::uuid;
END
$$;

CREATE FUNCTION hwpx_agent.advance_job_state_machine(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_job_id uuid,
    p_agent_instance_id uuid,
    p_execution_id uuid,
    p_attempt_no integer,
    p_fencing_token bigint,
    p_expected_state text,
    p_next_state text,
    p_transition_sha256 character(64)
)
RETURNS TABLE (
    returned_job_id uuid,
    returned_state text,
    returned_attempt_count integer,
    returned_fencing_token bigint,
    returned_result_revision_id uuid,
    returned_terminal_error_code text,
    returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_job hwpx_agent.jobs%ROWTYPE;
    v_now timestamptz := transaction_timestamp();
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'JOB_CONTEXT_MISMATCH';
    END IF;
    IF p_tenant_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_project_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$'
       OR p_job_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_agent_instance_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_execution_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_attempt_no <> 1 OR p_fencing_token <> 1
       OR ROW(p_expected_state, p_next_state) NOT IN (
            ROW('leased', 'staged'),
            ROW('staged', 'executing'),
            ROW('executing', 'validating')
       )
       OR p_transition_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'JOB_STAGE_REQUEST_INVALID';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.project_acl AS acl
        JOIN hwpx_agent.projects AS project
          ON project.tenant_id = acl.tenant_id AND project.project_id = acl.project_id
        WHERE acl.tenant_id = p_tenant_id
          AND acl.project_id = p_project_id
          AND acl.subject_sha256 = p_subject_sha256
          AND acl.role IN ('editor', 'owner')
          AND project.state = 'active'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'JOB_MUTATION_DENIED';
    END IF;
    SELECT * INTO v_job
    FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id
      AND job.project_id = p_project_id
      AND job.job_id = p_job_id
    FOR UPDATE;
    IF NOT FOUND OR v_job.state_machine_version IS DISTINCT FROM 1 THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'JOB_NOT_FOUND';
    END IF;
    IF v_job.state IS DISTINCT FROM p_expected_state THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_TRANSITION_INVALID';
    END IF;
    IF ROW(
        v_job.lease_owner_agent_id, v_job.active_execution_id,
        v_job.attempt_count, v_job.fencing_token
    ) IS DISTINCT FROM ROW(
        p_agent_instance_id, p_execution_id, p_attempt_no, p_fencing_token
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'JOB_LEASE_MISMATCH';
    END IF;

    UPDATE hwpx_agent.jobs SET state = p_next_state, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    IF p_next_state = 'executing' THEN
        UPDATE hwpx_agent.job_attempts
        SET state = 'running', updated_at = v_now
        WHERE tenant_id = p_tenant_id
          AND project_id = p_project_id
          AND job_id = p_job_id
          AND attempt_no = p_attempt_no
          AND execution_id = p_execution_id
          AND agent_instance_id = p_agent_instance_id
          AND fencing_token = p_fencing_token
          AND state_machine_version = 1
          AND state = 'leased';
        IF NOT FOUND THEN
            RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'JOB_ATTEMPT_LEASE_MISMATCH';
        END IF;
    END IF;
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, concat('job.', p_next_state),
        p_subject_sha256, p_job_id, p_transition_sha256
    );
    RETURN QUERY SELECT
        p_job_id, p_next_state, p_attempt_no, p_fencing_token,
        NULL::uuid, NULL::text, NULL::uuid;
END
$$;

CREATE FUNCTION hwpx_agent.commit_job_success(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_job_id uuid,
    p_agent_instance_id uuid,
    p_execution_id uuid,
    p_attempt_no integer,
    p_fencing_token bigint,
    p_result_revision_id uuid,
    p_receipt_artifact_id uuid,
    p_transition_sha256 character(64)
)
RETURNS TABLE (
    returned_job_id uuid,
    returned_state text,
    returned_attempt_count integer,
    returned_fencing_token bigint,
    returned_result_revision_id uuid,
    returned_terminal_error_code text,
    returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_job hwpx_agent.jobs%ROWTYPE;
    v_now timestamptz := transaction_timestamp();
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'JOB_CONTEXT_MISMATCH';
    END IF;
    IF p_tenant_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_project_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$'
       OR p_job_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_agent_instance_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_execution_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_attempt_no <> 1 OR p_fencing_token <> 1
       OR p_result_revision_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_receipt_artifact_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_transition_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'JOB_SUCCESS_REQUEST_INVALID';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.project_acl AS acl
        JOIN hwpx_agent.projects AS project
          ON project.tenant_id = acl.tenant_id AND project.project_id = acl.project_id
        WHERE acl.tenant_id = p_tenant_id
          AND acl.project_id = p_project_id
          AND acl.subject_sha256 = p_subject_sha256
          AND acl.role IN ('editor', 'owner')
          AND project.state = 'active'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'JOB_MUTATION_DENIED';
    END IF;
    SELECT * INTO v_job
    FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id
      AND job.project_id = p_project_id
      AND job.job_id = p_job_id
    FOR UPDATE;
    IF NOT FOUND OR v_job.state_machine_version IS DISTINCT FROM 1 THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'JOB_NOT_FOUND';
    END IF;
    IF v_job.state <> 'validating' THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_TRANSITION_INVALID';
    END IF;
    IF ROW(
        v_job.lease_owner_agent_id, v_job.active_execution_id,
        v_job.attempt_count, v_job.fencing_token
    ) IS DISTINCT FROM ROW(
        p_agent_instance_id, p_execution_id, p_attempt_no, p_fencing_token
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'JOB_LEASE_MISMATCH';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM hwpx_agent.revisions AS revision
        JOIN hwpx_agent.revision_graph_seals AS seal
          ON seal.tenant_id = revision.tenant_id
         AND seal.project_id = revision.project_id
         AND seal.revision_id = revision.revision_id
        WHERE revision.tenant_id = p_tenant_id
          AND revision.project_id = p_project_id
          AND revision.revision_id = p_result_revision_id
          AND seal.seal_kind = 'service_v1'
          AND seal.committed_generation > 0
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'JOB_RESULT_REVISION_NOT_QUALIFIED';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM hwpx_agent.artifacts AS artifact
        JOIN hwpx_agent.artifact_acl AS acl
          ON acl.tenant_id = artifact.tenant_id AND acl.artifact_id = artifact.artifact_id
        WHERE artifact.tenant_id = p_tenant_id
          AND artifact.artifact_id = p_receipt_artifact_id
          AND artifact.service_metadata_version = 1
          AND artifact.storage_state = 'available'
          AND artifact.validation_state = 'verified'
          AND artifact.artifact_kind = 'receipt'
          AND acl.subject_sha256 = p_subject_sha256
          AND (acl.can_read OR acl.can_manage)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'JOB_RECEIPT_ARTIFACT_NOT_QUALIFIED';
    END IF;

    UPDATE hwpx_agent.jobs
    SET state = 'succeeded',
        lease_owner_agent_id = NULL,
        active_execution_id = NULL,
        lease_issued_at = NULL,
        lease_expires_at = NULL,
        result_revision_id = p_result_revision_id,
        updated_at = v_now,
        completed_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    UPDATE hwpx_agent.job_attempts
    SET state = 'succeeded', receipt_artifact_id = p_receipt_artifact_id,
        completed_at = v_now, updated_at = v_now
    WHERE tenant_id = p_tenant_id
      AND project_id = p_project_id
      AND job_id = p_job_id
      AND attempt_no = p_attempt_no
      AND execution_id = p_execution_id
      AND agent_instance_id = p_agent_instance_id
      AND fencing_token = p_fencing_token
      AND state_machine_version = 1
      AND state = 'running';
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'JOB_ATTEMPT_LEASE_MISMATCH';
    END IF;
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id,
        revision_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'job.succeeded', p_subject_sha256,
        p_job_id, p_result_revision_id, p_transition_sha256
    );
    RETURN QUERY SELECT
        p_job_id, 'succeeded'::text, p_attempt_no, p_fencing_token,
        p_result_revision_id, NULL::text, p_receipt_artifact_id;
END
$$;

CREATE FUNCTION hwpx_agent.fail_job_state_machine(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_job_id uuid,
    p_agent_instance_id uuid,
    p_execution_id uuid,
    p_attempt_no integer,
    p_fencing_token bigint,
    p_error_code text,
    p_receipt_artifact_id uuid,
    p_transition_sha256 character(64)
)
RETURNS TABLE (
    returned_job_id uuid,
    returned_state text,
    returned_attempt_count integer,
    returned_fencing_token bigint,
    returned_result_revision_id uuid,
    returned_terminal_error_code text,
    returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_job hwpx_agent.jobs%ROWTYPE;
    v_attempt_state text;
    v_now timestamptz := transaction_timestamp();
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'JOB_CONTEXT_MISMATCH';
    END IF;
    IF p_tenant_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_project_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$'
       OR p_job_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_agent_instance_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_execution_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_attempt_no <> 1 OR p_fencing_token <> 1
       OR p_error_code !~ '^[A-Z][A-Z0-9_]{2,63}$'
       OR p_receipt_artifact_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_transition_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'JOB_FAILURE_REQUEST_INVALID';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.project_acl AS acl
        JOIN hwpx_agent.projects AS project
          ON project.tenant_id = acl.tenant_id AND project.project_id = acl.project_id
        WHERE acl.tenant_id = p_tenant_id
          AND acl.project_id = p_project_id
          AND acl.subject_sha256 = p_subject_sha256
          AND acl.role IN ('editor', 'owner')
          AND project.state = 'active'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'JOB_MUTATION_DENIED';
    END IF;
    SELECT * INTO v_job
    FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id
      AND job.project_id = p_project_id
      AND job.job_id = p_job_id
    FOR UPDATE;
    IF NOT FOUND OR v_job.state_machine_version IS DISTINCT FROM 1 THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'JOB_NOT_FOUND';
    END IF;
    IF v_job.state NOT IN ('leased', 'staged', 'executing', 'validating') THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_TRANSITION_INVALID';
    END IF;
    IF ROW(
        v_job.lease_owner_agent_id, v_job.active_execution_id,
        v_job.attempt_count, v_job.fencing_token
    ) IS DISTINCT FROM ROW(
        p_agent_instance_id, p_execution_id, p_attempt_no, p_fencing_token
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'JOB_LEASE_MISMATCH';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM hwpx_agent.artifacts AS artifact
        JOIN hwpx_agent.artifact_acl AS acl
          ON acl.tenant_id = artifact.tenant_id AND acl.artifact_id = artifact.artifact_id
        WHERE artifact.tenant_id = p_tenant_id
          AND artifact.artifact_id = p_receipt_artifact_id
          AND artifact.service_metadata_version = 1
          AND artifact.storage_state = 'available'
          AND artifact.validation_state = 'verified'
          AND artifact.artifact_kind = 'receipt'
          AND acl.subject_sha256 = p_subject_sha256
          AND (acl.can_read OR acl.can_manage)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'JOB_RECEIPT_ARTIFACT_NOT_QUALIFIED';
    END IF;
    v_attempt_state := CASE
        WHEN v_job.state IN ('leased', 'staged') THEN 'leased'
        ELSE 'running'
    END;

    UPDATE hwpx_agent.jobs
    SET state = 'failed',
        lease_owner_agent_id = NULL,
        active_execution_id = NULL,
        lease_issued_at = NULL,
        lease_expires_at = NULL,
        terminal_error_code = p_error_code,
        updated_at = v_now,
        completed_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    UPDATE hwpx_agent.job_attempts
    SET state = 'failed', receipt_artifact_id = p_receipt_artifact_id,
        completed_at = v_now, updated_at = v_now
    WHERE tenant_id = p_tenant_id
      AND project_id = p_project_id
      AND job_id = p_job_id
      AND attempt_no = p_attempt_no
      AND execution_id = p_execution_id
      AND agent_instance_id = p_agent_instance_id
      AND fencing_token = p_fencing_token
      AND state_machine_version = 1
      AND state = v_attempt_state;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'JOB_ATTEMPT_LEASE_MISMATCH';
    END IF;
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'job.failed', p_subject_sha256,
        p_job_id, p_transition_sha256
    );
    RETURN QUERY SELECT
        p_job_id, 'failed'::text, p_attempt_no, p_fencing_token,
        NULL::uuid, p_error_code, p_receipt_artifact_id;
END
$$;

CREATE FUNCTION hwpx_agent.get_job_state_machine(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_job_id uuid
)
RETURNS TABLE (
    returned_job_id uuid,
    returned_state text,
    returned_attempt_count integer,
    returned_fencing_token bigint,
    returned_result_revision_id uuid,
    returned_terminal_error_code text,
    returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
STABLE
SET search_path = pg_catalog, hwpx_agent
AS $$
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'JOB_CONTEXT_MISMATCH';
    END IF;
    IF p_tenant_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_project_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$'
       OR p_job_id = '00000000-0000-0000-0000-000000000000'::uuid THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'JOB_GET_REQUEST_INVALID';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.project_acl AS acl
        WHERE acl.tenant_id = p_tenant_id
          AND acl.project_id = p_project_id
          AND acl.subject_sha256 = p_subject_sha256
    ) THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'JOB_NOT_FOUND';
    END IF;
    RETURN QUERY
    SELECT
        job.job_id,
        job.state,
        job.attempt_count,
        job.fencing_token,
        job.result_revision_id,
        job.terminal_error_code,
        attempt.receipt_artifact_id
    FROM hwpx_agent.jobs AS job
    LEFT JOIN hwpx_agent.job_attempts AS attempt
      ON attempt.tenant_id = job.tenant_id
     AND attempt.project_id = job.project_id
     AND attempt.job_id = job.job_id
     AND attempt.attempt_no = job.attempt_count
     AND attempt.state_machine_version = 1
    WHERE job.tenant_id = p_tenant_id
      AND job.project_id = p_project_id
      AND job.job_id = p_job_id
      AND job.state_machine_version = 1;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'JOB_NOT_FOUND';
    END IF;
END
$$;

REVOKE ALL ON FUNCTION hwpx_agent.guard_job_state_machine_update() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.guard_job_attempt_state_machine_update() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.verify_job_state_machine_consistency() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.enqueue_job_state_machine(
    uuid, uuid, character, uuid, uuid, uuid, uuid, character, text, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.lease_job_state_machine(
    uuid, uuid, character, uuid, uuid, uuid, integer, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.advance_job_state_machine(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, text, text, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.commit_job_success(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, uuid, uuid, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.fail_job_state_machine(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, text, uuid, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.get_job_state_machine(
    uuid, uuid, character, uuid
) FROM PUBLIC;

INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (5, 'p14.job_state_machine_v1', current_setting('hwpx_agent.migration_sha256'));

COMMIT;
