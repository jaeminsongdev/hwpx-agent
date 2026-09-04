BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 5 AND migration_name = 'p14.job_state_machine_v1'
    ) OR EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions WHERE version >= 6
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 worker lease migration requires exact schema version 5';
    END IF;
END
$$;

CREATE TABLE hwpx_agent.worker_registrations (
    tenant_id uuid NOT NULL,
    agent_instance_id uuid NOT NULL,
    subject_sha256 character(64) NOT NULL,
    target_profile_id text NOT NULL,
    capability_set_sha256 character(64) NOT NULL,
    state text NOT NULL,
    registered_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    last_heartbeat_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    expires_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, agent_instance_id),
    CONSTRAINT worker_registrations_tenant_fk FOREIGN KEY (tenant_id)
        REFERENCES hwpx_agent.tenants (tenant_id) ON DELETE RESTRICT,
    CONSTRAINT worker_registrations_agent_nonzero CHECK (
        agent_instance_id <> '00000000-0000-0000-0000-000000000000'::uuid
    ),
    CONSTRAINT worker_registrations_subject_format CHECK (
        subject_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT worker_registrations_profile_format CHECK (
        target_profile_id ~ '^[A-Za-z0-9][A-Za-z0-9._-]{1,126}$'
    ),
    CONSTRAINT worker_registrations_capability_format CHECK (
        capability_set_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT worker_registrations_state CHECK (state IN ('ready', 'draining')),
    CONSTRAINT worker_registrations_time_order CHECK (
        last_heartbeat_at >= registered_at
        AND updated_at >= registered_at
        AND expires_at > last_heartbeat_at
        AND expires_at <= last_heartbeat_at + interval '5 minutes'
    )
);

CREATE INDEX worker_registrations_eligibility_idx
    ON hwpx_agent.worker_registrations (
        tenant_id, target_profile_id, capability_set_sha256, expires_at, agent_instance_id
    )
    WHERE state = 'ready';

ALTER TABLE hwpx_agent.worker_registrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.worker_registrations FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.worker_registrations
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());

CREATE FUNCTION hwpx_agent.guard_worker_registration_update()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    IF ROW(
        OLD.tenant_id, OLD.agent_instance_id, OLD.subject_sha256,
        OLD.target_profile_id, OLD.capability_set_sha256, OLD.registered_at
    ) IS DISTINCT FROM ROW(
        NEW.tenant_id, NEW.agent_instance_id, NEW.subject_sha256,
        NEW.target_profile_id, NEW.capability_set_sha256, NEW.registered_at
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'WORKER_IDENTITY_IMMUTABLE';
    END IF;
    IF NEW.last_heartbeat_at < OLD.last_heartbeat_at
       OR NEW.updated_at < OLD.updated_at
       OR NEW.expires_at <= OLD.expires_at THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'WORKER_HEARTBEAT_REGRESSION';
    END IF;
    IF OLD.state = 'draining' AND NEW.state = 'ready' THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'WORKER_DRAINING_TERMINAL';
    END IF;
    RETURN NEW;
END
$$;

CREATE TRIGGER worker_registrations_guard
BEFORE UPDATE ON hwpx_agent.worker_registrations
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.guard_worker_registration_update();

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

CREATE FUNCTION hwpx_agent.register_scheduler_worker(
    p_tenant_id uuid,
    p_subject_sha256 character(64),
    p_agent_instance_id uuid,
    p_target_profile_id text,
    p_capability_set_sha256 character(64),
    p_state text,
    p_heartbeat_seconds integer,
    p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_agent_instance_id uuid,
    returned_state text,
    returned_expires_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_now timestamptz := clock_timestamp();
    v_expires_at timestamptz;
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'WORKER_CONTEXT_MISMATCH';
    END IF;
    IF p_tenant_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_agent_instance_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$'
       OR p_target_profile_id !~ '^[A-Za-z0-9][A-Za-z0-9._-]{1,126}$'
       OR p_capability_set_sha256 !~ '^[0-9a-f]{64}$'
       OR p_state NOT IN ('ready', 'draining')
       OR p_heartbeat_seconds NOT BETWEEN 1 AND 300
       OR p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'WORKER_REGISTER_REQUEST_INVALID';
    END IF;
    v_expires_at := v_now + make_interval(secs => p_heartbeat_seconds);
    INSERT INTO hwpx_agent.worker_registrations (
        tenant_id, agent_instance_id, subject_sha256, target_profile_id,
        capability_set_sha256, state, registered_at, last_heartbeat_at,
        expires_at, updated_at
    ) VALUES (
        p_tenant_id, p_agent_instance_id, p_subject_sha256, p_target_profile_id,
        p_capability_set_sha256, p_state, v_now, v_now, v_expires_at, v_now
    );
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, event_type, subject_sha256, payload_sha256
    ) VALUES (
        p_tenant_id, 'worker.registered', p_subject_sha256, p_event_sha256
    );
    RETURN QUERY SELECT p_agent_instance_id, p_state, v_expires_at;
EXCEPTION
    WHEN unique_violation THEN
        RAISE EXCEPTION USING ERRCODE = '23505', MESSAGE = 'WORKER_ALREADY_REGISTERED';
END
$$;

CREATE FUNCTION hwpx_agent.heartbeat_scheduler_worker(
    p_tenant_id uuid,
    p_subject_sha256 character(64),
    p_agent_instance_id uuid,
    p_target_profile_id text,
    p_capability_set_sha256 character(64),
    p_state text,
    p_heartbeat_seconds integer,
    p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_agent_instance_id uuid,
    returned_state text,
    returned_expires_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_worker hwpx_agent.worker_registrations%ROWTYPE;
    v_now timestamptz := clock_timestamp();
    v_expires_at timestamptz;
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'WORKER_CONTEXT_MISMATCH';
    END IF;
    IF p_tenant_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_agent_instance_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$'
       OR p_target_profile_id !~ '^[A-Za-z0-9][A-Za-z0-9._-]{1,126}$'
       OR p_capability_set_sha256 !~ '^[0-9a-f]{64}$'
       OR p_state NOT IN ('ready', 'draining')
       OR p_heartbeat_seconds NOT BETWEEN 1 AND 300
       OR p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'WORKER_HEARTBEAT_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_worker
    FROM hwpx_agent.worker_registrations AS worker
    WHERE worker.tenant_id = p_tenant_id
      AND worker.agent_instance_id = p_agent_instance_id
    FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'WORKER_NOT_FOUND';
    END IF;
    IF v_worker.subject_sha256 <> p_subject_sha256
       OR v_worker.target_profile_id <> p_target_profile_id
       OR v_worker.capability_set_sha256 <> p_capability_set_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'WORKER_IDENTITY_MISMATCH';
    END IF;
    IF v_worker.expires_at <= v_now
       OR (v_worker.state = 'draining' AND p_state = 'ready') THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'WORKER_UNAVAILABLE';
    END IF;
    v_expires_at := v_now + make_interval(secs => p_heartbeat_seconds);
    IF v_expires_at <= v_worker.expires_at THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'WORKER_HEARTBEAT_NOT_EXTENDED';
    END IF;
    UPDATE hwpx_agent.worker_registrations
    SET state = p_state,
        last_heartbeat_at = v_now,
        expires_at = v_expires_at,
        updated_at = v_now
    WHERE tenant_id = p_tenant_id AND agent_instance_id = p_agent_instance_id;
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, event_type, subject_sha256, payload_sha256
    ) VALUES (
        p_tenant_id, 'worker.heartbeat', p_subject_sha256, p_event_sha256
    );
    RETURN QUERY SELECT p_agent_instance_id, p_state, v_expires_at;
END
$$;

CREATE FUNCTION hwpx_agent.heartbeat_job_lease(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_job_id uuid,
    p_agent_instance_id uuid,
    p_execution_id uuid,
    p_attempt_no integer,
    p_fencing_token bigint,
    p_lease_seconds integer,
    p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_job_id uuid,
    returned_lease_expires_at timestamptz,
    returned_fencing_token bigint
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_job hwpx_agent.jobs%ROWTYPE;
    v_worker hwpx_agent.worker_registrations%ROWTYPE;
    v_now timestamptz := clock_timestamp();
    v_expires_at timestamptz;
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'JOB_CONTEXT_MISMATCH';
    END IF;
    IF p_tenant_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_project_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_job_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_agent_instance_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_execution_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$'
       OR p_attempt_no <> 1 OR p_fencing_token <> 1
       OR p_lease_seconds NOT BETWEEN 1 AND 3600
       OR p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'JOB_HEARTBEAT_REQUEST_INVALID';
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
    IF v_job.lease_expires_at <= v_now THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'JOB_LEASE_EXPIRED';
    END IF;
    SELECT * INTO v_worker
    FROM hwpx_agent.worker_registrations AS worker
    WHERE worker.tenant_id = p_tenant_id
      AND worker.agent_instance_id = p_agent_instance_id
    FOR UPDATE;
    IF NOT FOUND
       OR v_worker.subject_sha256 <> p_subject_sha256
       OR v_worker.target_profile_id <> v_job.required_target_profile_id
       OR v_worker.capability_set_sha256 <> v_job.required_capability_set_sha256
       OR v_worker.expires_at <= v_now THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'JOB_WORKER_NOT_QUALIFIED';
    END IF;
    v_expires_at := v_now + make_interval(secs => p_lease_seconds);
    IF v_expires_at <= v_job.lease_expires_at
       OR v_expires_at > v_job.lease_issued_at + interval '1 hour'
       OR v_expires_at > v_worker.expires_at THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'JOB_HEARTBEAT_BOUNDS_INVALID';
    END IF;
    PERFORM set_config('hwpx_agent.allow_job_lease_heartbeat', 'on', true);
    UPDATE hwpx_agent.jobs
    SET lease_expires_at = v_expires_at,
        updated_at = GREATEST(updated_at, transaction_timestamp())
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    UPDATE hwpx_agent.job_attempts
    SET lease_expires_at = v_expires_at,
        updated_at = GREATEST(updated_at, transaction_timestamp())
    WHERE tenant_id = p_tenant_id
      AND project_id = p_project_id
      AND job_id = p_job_id
      AND attempt_no = p_attempt_no
      AND execution_id = p_execution_id
      AND agent_instance_id = p_agent_instance_id
      AND fencing_token = p_fencing_token
      AND state_machine_version = 1
      AND state IN ('leased', 'running');
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'JOB_ATTEMPT_LEASE_MISMATCH';
    END IF;
    PERFORM set_config('hwpx_agent.allow_job_lease_heartbeat', 'off', true);
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'job.heartbeat', p_subject_sha256,
        p_job_id, p_event_sha256
    );
    RETURN QUERY SELECT p_job_id, v_expires_at, p_fencing_token;
END
$$;

CREATE FUNCTION hwpx_agent.expire_job_lease(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_job_id uuid,
    p_agent_instance_id uuid,
    p_execution_id uuid,
    p_attempt_no integer,
    p_fencing_token bigint,
    p_receipt_artifact_id uuid,
    p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_job_id uuid,
    returned_state text,
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
    v_now timestamptz := clock_timestamp();
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'JOB_CONTEXT_MISMATCH';
    END IF;
    IF p_tenant_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_project_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_job_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_agent_instance_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_execution_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_receipt_artifact_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$'
       OR p_attempt_no <> 1 OR p_fencing_token <> 1
       OR p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'JOB_EXPIRY_REQUEST_INVALID';
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
    IF v_job.lease_expires_at > v_now THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'JOB_LEASE_STILL_ACTIVE';
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
    PERFORM set_config('hwpx_agent.allow_job_lease_expiry_finalize', 'on', true);
    UPDATE hwpx_agent.jobs
    SET state = 'failed',
        lease_owner_agent_id = NULL,
        active_execution_id = NULL,
        lease_issued_at = NULL,
        lease_expires_at = NULL,
        terminal_error_code = 'LEASE_EXPIRED',
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
    PERFORM set_config('hwpx_agent.allow_job_lease_expiry_finalize', 'off', true);
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'job.lease_expired', p_subject_sha256,
        p_job_id, p_event_sha256
    );
    RETURN QUERY SELECT
        p_job_id, 'failed'::text, 'LEASE_EXPIRED'::text, p_receipt_artifact_id;
END
$$;

REVOKE ALL ON TABLE hwpx_agent.worker_registrations FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.guard_worker_registration_update() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.guard_job_state_machine_update() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.guard_job_attempt_state_machine_update() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.register_scheduler_worker(
    uuid, character, uuid, text, character, text, integer, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.heartbeat_scheduler_worker(
    uuid, character, uuid, text, character, text, integer, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.heartbeat_job_lease(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, integer, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.expire_job_lease(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, uuid, character
) FROM PUBLIC;

INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (6, 'p14.worker_lease_fencing_v1', current_setting('hwpx_agent.migration_sha256'));

COMMIT;
