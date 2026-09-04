BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 6 AND migration_name = 'p14.worker_lease_fencing_v1'
    ) OR EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions WHERE version >= 7
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 idempotency reconciliation migration requires exact schema version 6';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256', true)
        !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            MESSAGE = 'P14 idempotency reconciliation migration requires its exact SHA-256';
    END IF;
END
$$;

-- Legacy rows remain record_version=1. They cannot be upgraded because the new immutable
-- subject, branch, manifest, source, effect and transaction identities cannot be reconstructed.
ALTER TABLE hwpx_agent.idempotency_records
    DROP CONSTRAINT idempotency_state_value,
    DROP CONSTRAINT idempotency_terminal_consistency,
    DROP CONSTRAINT idempotency_time_order,
    ADD COLUMN record_version smallint NOT NULL DEFAULT 1,
    ADD COLUMN subject_sha256 character(64),
    ADD COLUMN branch_id uuid,
    ADD COLUMN request_id uuid,
    ADD COLUMN source_artifact_id uuid,
    ADD COLUMN expected_revision_id uuid,
    ADD COLUMN expected_revision_generation bigint,
    ADD COLUMN execution_manifest_sha256 character(64),
    ADD COLUMN source_artifact_sha256 character(64),
    ADD COLUMN expected_effect_sha256 character(64),
    ADD COLUMN transaction_receipt_sha256 character(64),
    ADD COLUMN max_attempts smallint,
    ADD COLUMN base_delay_seconds integer,
    ADD COLUMN max_delay_seconds integer,
    ADD COLUMN attempt_count integer,
    ADD COLUMN last_fencing_token bigint,
    ADD COLUMN retry_not_before timestamptz,
    ADD COLUMN last_retry_class text,
    ADD CONSTRAINT idempotency_v2_branch_fk FOREIGN KEY (
        tenant_id, project_id, branch_id
    ) REFERENCES hwpx_agent.branches (tenant_id, project_id, branch_id) ON DELETE RESTRICT,
    ADD CONSTRAINT idempotency_v2_source_artifact_fk FOREIGN KEY (
        tenant_id, source_artifact_id
    ) REFERENCES hwpx_agent.artifacts (tenant_id, artifact_id) ON DELETE RESTRICT,
    ADD CONSTRAINT idempotency_v2_expected_revision_fk FOREIGN KEY (
        tenant_id, project_id, expected_revision_id
    ) REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id) ON DELETE RESTRICT,
    ADD CONSTRAINT idempotency_record_version_value CHECK (record_version IN (1, 2)),
    ADD CONSTRAINT idempotency_state_value CHECK (
        state IN (
            'claimed', 'in_progress', 'retry_pending', 'outcome_unknown',
            'terminal_success', 'terminal_failure'
        )
    ),
    ADD CONSTRAINT idempotency_v2_digest_format CHECK (
        record_version = 1
        OR (
            subject_sha256 ~ '^[0-9a-f]{64}$'
            AND execution_manifest_sha256 ~ '^[0-9a-f]{64}$'
            AND source_artifact_sha256 ~ '^[0-9a-f]{64}$'
            AND expected_effect_sha256 ~ '^[0-9a-f]{64}$'
            AND transaction_receipt_sha256 ~ '^[0-9a-f]{64}$'
        )
    ),
    ADD CONSTRAINT idempotency_v2_retry_class CHECK (
        last_retry_class IS NULL
        OR last_retry_class IN (
            'transient_storage', 'transient_network',
            'automation_unknown', 'automation_no_effect'
        )
    ),
    ADD CONSTRAINT idempotency_v2_metadata_complete CHECK (
        (
            record_version = 1
            AND subject_sha256 IS NULL
            AND branch_id IS NULL
            AND request_id IS NULL
            AND source_artifact_id IS NULL
            AND expected_revision_id IS NULL
            AND expected_revision_generation IS NULL
            AND execution_manifest_sha256 IS NULL
            AND source_artifact_sha256 IS NULL
            AND expected_effect_sha256 IS NULL
            AND transaction_receipt_sha256 IS NULL
            AND max_attempts IS NULL
            AND base_delay_seconds IS NULL
            AND max_delay_seconds IS NULL
            AND attempt_count IS NULL
            AND last_fencing_token IS NULL
            AND retry_not_before IS NULL
            AND last_retry_class IS NULL
            AND state IN ('claimed', 'outcome_unknown', 'terminal_success', 'terminal_failure')
        )
        OR (
            record_version = 2
            AND subject_sha256 IS NOT NULL
            AND branch_id IS NOT NULL
            AND request_id IS NOT NULL
            AND source_artifact_id IS NOT NULL
            AND expected_revision_generation IS NOT NULL
            AND execution_manifest_sha256 IS NOT NULL
            AND source_artifact_sha256 IS NOT NULL
            AND expected_effect_sha256 IS NOT NULL
            AND transaction_receipt_sha256 IS NOT NULL
            AND job_id IS NOT NULL
            AND max_attempts BETWEEN 1 AND 10
            AND base_delay_seconds BETWEEN 1 AND 86400
            AND max_delay_seconds BETWEEN base_delay_seconds AND 86400
            AND attempt_count BETWEEN 0 AND max_attempts
            AND last_fencing_token = attempt_count
            AND expires_at <= created_at + interval '7 days'
            AND (
                (expected_revision_id IS NULL AND expected_revision_generation = 0)
                OR (expected_revision_id IS NOT NULL AND expected_revision_generation > 0)
            )
        )
    ),
    ADD CONSTRAINT idempotency_terminal_consistency CHECK (
        (
            record_version = 1
            AND (
                (state = 'claimed' AND result_revision_id IS NULL AND receipt_artifact_id IS NULL)
                OR (
                    state = 'terminal_success'
                    AND result_revision_id IS NOT NULL
                    AND receipt_artifact_id IS NOT NULL
                    AND terminal_error_code IS NULL
                )
                OR (
                    state IN ('terminal_failure', 'outcome_unknown')
                    AND result_revision_id IS NULL
                    AND receipt_artifact_id IS NOT NULL
                    AND terminal_error_code IS NOT NULL
                )
            )
        )
        OR (
            record_version = 2
            AND (
                (
                    state = 'claimed'
                    AND attempt_count = 0
                    AND result_revision_id IS NULL
                    AND receipt_artifact_id IS NULL
                    AND terminal_error_code IS NULL
                    AND retry_not_before IS NULL
                    AND last_retry_class IS NULL
                )
                OR (
                    state = 'in_progress'
                    AND attempt_count > 0
                    AND result_revision_id IS NULL
                    AND receipt_artifact_id IS NULL
                    AND terminal_error_code IS NULL
                    AND retry_not_before IS NULL
                )
                OR (
                    state = 'retry_pending'
                    AND attempt_count > 0
                    AND result_revision_id IS NULL
                    AND receipt_artifact_id IS NOT NULL
                    AND terminal_error_code IS NULL
                    AND retry_not_before IS NOT NULL
                    AND last_retry_class IN (
                        'transient_storage', 'transient_network', 'automation_no_effect'
                    )
                )
                OR (
                    state = 'outcome_unknown'
                    AND attempt_count > 0
                    AND result_revision_id IS NULL
                    AND receipt_artifact_id IS NOT NULL
                    AND terminal_error_code = 'OUTCOME_UNKNOWN'
                    AND retry_not_before IS NULL
                    AND last_retry_class = 'automation_unknown'
                )
                OR (
                    state = 'terminal_success'
                    AND attempt_count > 0
                    AND result_revision_id IS NOT NULL
                    AND receipt_artifact_id IS NOT NULL
                    AND terminal_error_code IS NULL
                    AND retry_not_before IS NULL
                )
                OR (
                    state = 'terminal_failure'
                    AND attempt_count > 0
                    AND result_revision_id IS NULL
                    AND receipt_artifact_id IS NOT NULL
                    AND terminal_error_code IS NOT NULL
                    AND retry_not_before IS NULL
                )
            )
        )
    ),
    ADD CONSTRAINT idempotency_time_order CHECK (
        updated_at >= created_at
        AND expires_at > created_at
        AND (retry_not_before IS NULL OR retry_not_before >= created_at)
    );

CREATE INDEX idempotency_v2_retry_ready_idx
    ON hwpx_agent.idempotency_records (
        tenant_id, retry_not_before, project_id, idempotency_key
    )
    WHERE record_version = 2 AND state = 'retry_pending';
CREATE UNIQUE INDEX idempotency_v2_job_unique_idx
    ON hwpx_agent.idempotency_records (tenant_id, project_id, job_id)
    WHERE record_version = 2;
CREATE UNIQUE INDEX idempotency_v2_transaction_unique_idx
    ON hwpx_agent.idempotency_records (
        tenant_id, project_id, transaction_receipt_sha256
    )
    WHERE record_version = 2;

-- One unpredictable authorization capability exists only for the currently leased attempt.
-- The application has no table privilege, the lease function returns the capability only to that
-- worker attempt, and the commit-receipt trigger consumes it in the same transaction as the guarded
-- commit wrapper. Retry/unknown/terminal transitions revoke it first.
CREATE TABLE hwpx_agent.idempotency_commit_authorizations (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    idempotency_key uuid NOT NULL,
    job_id uuid NOT NULL,
    agent_instance_id uuid NOT NULL,
    execution_id uuid NOT NULL,
    attempt_no integer NOT NULL,
    fencing_token bigint NOT NULL,
    commit_authorization_id uuid NOT NULL,
    transaction_receipt_sha256 character(64) NOT NULL,
    created_backend_pid integer NOT NULL,
    created_transaction_id xid8 NOT NULL,
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, project_id, idempotency_key),
    UNIQUE (commit_authorization_id),
    UNIQUE (tenant_id, project_id, transaction_receipt_sha256),
    CONSTRAINT idempotency_commit_authorizations_record_fk FOREIGN KEY (
        tenant_id, project_id, idempotency_key
    ) REFERENCES hwpx_agent.idempotency_records (
        tenant_id, project_id, idempotency_key
    ) ON DELETE CASCADE,
    CONSTRAINT idempotency_commit_authorizations_job_fk FOREIGN KEY (
        tenant_id, project_id, job_id
    ) REFERENCES hwpx_agent.jobs (tenant_id, project_id, job_id) ON DELETE RESTRICT,
    CONSTRAINT idempotency_commit_authorizations_identity CHECK (
        job_id <> '00000000-0000-0000-0000-000000000000'::uuid
        AND agent_instance_id <> '00000000-0000-0000-0000-000000000000'::uuid
        AND execution_id <> '00000000-0000-0000-0000-000000000000'::uuid
        AND attempt_no BETWEEN 1 AND 10
        AND fencing_token = attempt_no
        AND commit_authorization_id <> '00000000-0000-0000-0000-000000000000'::uuid
        AND transaction_receipt_sha256 ~ '^[0-9a-f]{64}$'
        AND created_backend_pid > 0
    )
);

ALTER TABLE hwpx_agent.idempotency_commit_authorizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.idempotency_commit_authorizations FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.idempotency_commit_authorizations
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());
REVOKE ALL ON TABLE hwpx_agent.idempotency_commit_authorizations FROM PUBLIC;

CREATE OR REPLACE FUNCTION hwpx_agent.protect_idempotency_identity()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    IF ROW(
        NEW.tenant_id, NEW.project_id, NEW.idempotency_key,
        NEW.request_sha256, NEW.created_at, NEW.record_version
    ) IS DISTINCT FROM ROW(
        OLD.tenant_id, OLD.project_id, OLD.idempotency_key,
        OLD.request_sha256, OLD.created_at, OLD.record_version
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_IDENTITY_IMMUTABLE';
    END IF;
    IF OLD.record_version = 2 AND ROW(
        NEW.subject_sha256, NEW.branch_id, NEW.request_id, NEW.job_id,
        NEW.source_artifact_id, NEW.expected_revision_id,
        NEW.expected_revision_generation, NEW.execution_manifest_sha256,
        NEW.source_artifact_sha256, NEW.expected_effect_sha256,
        NEW.transaction_receipt_sha256, NEW.max_attempts,
        NEW.base_delay_seconds, NEW.max_delay_seconds, NEW.expires_at
    ) IS DISTINCT FROM ROW(
        OLD.subject_sha256, OLD.branch_id, OLD.request_id, OLD.job_id,
        OLD.source_artifact_id, OLD.expected_revision_id,
        OLD.expected_revision_generation, OLD.execution_manifest_sha256,
        OLD.source_artifact_sha256, OLD.expected_effect_sha256,
        OLD.transaction_receipt_sha256, OLD.max_attempts,
        OLD.base_delay_seconds, OLD.max_delay_seconds, OLD.expires_at
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_V2_BINDING_IMMUTABLE';
    END IF;
    RETURN NEW;
END
$$;

ALTER TABLE hwpx_agent.jobs
    DROP CONSTRAINT jobs_state_value,
    DROP CONSTRAINT jobs_terminal_time_consistency,
    DROP CONSTRAINT jobs_state_machine_version,
    DROP CONSTRAINT jobs_state_machine_v1_complete,
    ADD CONSTRAINT jobs_state_value CHECK (
        state IN (
            'queued', 'leased', 'staged', 'executing', 'validating', 'retry_pending',
            'succeeded', 'failed', 'cancelled', 'unknown_outcome'
        )
    ),
    ADD CONSTRAINT jobs_terminal_time_consistency CHECK (
        (
            state IN ('succeeded', 'failed', 'cancelled')
            OR (state = 'unknown_outcome' AND state_machine_version IS DISTINCT FROM 2)
        ) = (completed_at IS NOT NULL)
    ),
    ADD CONSTRAINT jobs_state_machine_version CHECK (
        state_machine_version IS NULL OR state_machine_version IN (1, 2)
    ),
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
    DROP CONSTRAINT job_attempts_state_machine_version,
    DROP CONSTRAINT job_attempts_state_machine_v1_complete,
    ADD CONSTRAINT job_attempts_state_machine_version CHECK (
        state_machine_version IS NULL OR state_machine_version IN (1, 2)
    ),
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

CREATE INDEX jobs_idempotency_v2_ready_idx
    ON hwpx_agent.jobs (tenant_id, state, created_at, job_id)
    WHERE state_machine_version = 2 AND state IN ('queued', 'retry_pending');

-- Version 1 keeps the exact v6 worker/lease guard. Version 2 updates are accepted only through
-- the SECURITY DEFINER functions below; PUBLIC has no direct table privilege.
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

    IF OLD.state_machine_version = 2 THEN
        IF NOT v_v2_allowed THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_V2_TRANSITION_REQUIRED';
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
       AND NEW.state IS DISTINCT FROM OLD.state
       AND OLD.lease_expires_at <= v_now
       AND NOT (
            v_expiry_allowed AND NEW.state = 'failed'
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
            SELECT 1 FROM hwpx_agent.worker_registrations AS worker
            WHERE worker.tenant_id = NEW.tenant_id
              AND worker.agent_instance_id = NEW.lease_owner_agent_id
              AND worker.subject_sha256 = hwpx_agent.current_subject_sha256()
              AND worker.target_profile_id = NEW.required_target_profile_id
              AND worker.capability_set_sha256 = NEW.required_capability_set_sha256
              AND worker.state = 'ready'
              AND worker.last_heartbeat_at <= v_now AND worker.expires_at > v_now
              AND NEW.lease_expires_at > v_now
              AND NEW.lease_expires_at <= worker.expires_at
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
    IF v_job.state = 'queued' THEN
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
       OR (
            v_job.state_machine_version = 1
            AND v_job.state IN ('succeeded', 'failed')
            AND v_attempt.completed_at IS DISTINCT FROM v_job.completed_at
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'JOB_ATTEMPT_CONSISTENCY_INVALID';
    END IF;
    RETURN NULL;
END
$$;

CREATE FUNCTION hwpx_agent.verify_idempotency_job_consistency()
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
    IF NOT v_record_found AND (NOT v_job_found OR v_job.state_machine_version IS DISTINCT FROM 2) THEN
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
       OR (v_record.state = 'terminal_failure' AND v_job.state <> 'failed') THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'IDEMPOTENCY_JOB_CONSISTENCY_INVALID';
    END IF;
    RETURN NULL;
END
$$;

CREATE CONSTRAINT TRIGGER idempotency_job_consistency_from_record
AFTER INSERT OR UPDATE ON hwpx_agent.idempotency_records
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.verify_idempotency_job_consistency();
CREATE CONSTRAINT TRIGGER idempotency_job_consistency_from_job
AFTER INSERT OR UPDATE ON hwpx_agent.jobs
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.verify_idempotency_job_consistency();

CREATE FUNCTION hwpx_agent.require_idempotency_v2_editor(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64)
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
STABLE
SET search_path = pg_catalog, hwpx_agent
AS $$
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'IDEMPOTENCY_CONTEXT_MISMATCH';
    END IF;
    IF p_tenant_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_project_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'IDEMPOTENCY_REQUEST_INVALID';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.project_acl AS acl
        JOIN hwpx_agent.projects AS project
          ON project.tenant_id = acl.tenant_id AND project.project_id = acl.project_id
        WHERE acl.tenant_id = p_tenant_id AND acl.project_id = p_project_id
          AND acl.subject_sha256 = p_subject_sha256
          AND acl.role IN ('editor', 'owner') AND project.state = 'active'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'IDEMPOTENCY_MUTATION_DENIED';
    END IF;
END
$$;

CREATE FUNCTION hwpx_agent.idempotency_v2_artifact_qualified(
    p_tenant_id uuid,
    p_subject_sha256 character(64),
    p_artifact_id uuid,
    p_artifact_kind text,
    p_expected_sha256 character(64)
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
          AND artifact.storage_state = 'available' AND artifact.validation_state = 'verified'
          AND artifact.artifact_kind = p_artifact_kind
          AND artifact.content_sha256 = p_expected_sha256
          AND acl.subject_sha256 = p_subject_sha256 AND (acl.can_read OR acl.can_manage)
    )
$$;

CREATE FUNCTION hwpx_agent.idempotency_v2_head_matches(
    p_tenant_id uuid,
    p_project_id uuid,
    p_branch_id uuid,
    p_expected_revision_id uuid,
    p_expected_generation bigint
)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
BEGIN
    -- The lock closes the no-effect TOCTOU window against commit_revision_cas, whose branch
    -- update requires an exclusive row lock. It is held until the caller transaction ends.
    PERFORM 1 FROM hwpx_agent.branches AS branch
    WHERE branch.tenant_id = p_tenant_id AND branch.project_id = p_project_id
      AND branch.branch_id = p_branch_id
      AND branch.head_revision_id IS NOT DISTINCT FROM p_expected_revision_id
      AND branch.head_generation = p_expected_generation
      AND branch.head_generation >= 0
    FOR SHARE;
    RETURN FOUND;
END
$$;

CREATE FUNCTION hwpx_agent.idempotency_v2_committed_effect_qualified(
    p_tenant_id uuid,
    p_project_id uuid,
    p_branch_id uuid,
    p_subject_sha256 character(64),
    p_source_artifact_id uuid,
    p_source_artifact_sha256 character(64),
    p_expected_revision_id uuid,
    p_expected_generation bigint,
    p_operation_plan_sha256 character(64),
    p_result_revision_id uuid,
    p_expected_effect_sha256 character(64),
    p_transaction_receipt_sha256 character(64),
    p_receipt_artifact_id uuid
)
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
    SELECT
        hwpx_agent.idempotency_v2_head_matches(
            p_tenant_id, p_project_id, p_branch_id,
            p_result_revision_id, p_expected_generation + 1
        )
        AND hwpx_agent.idempotency_v2_artifact_qualified(
            p_tenant_id, p_subject_sha256, p_source_artifact_id,
            'source', p_source_artifact_sha256
        )
        AND hwpx_agent.idempotency_v2_artifact_qualified(
            p_tenant_id, p_subject_sha256, p_receipt_artifact_id,
            'receipt', p_transaction_receipt_sha256
        )
        AND EXISTS (
            SELECT 1
            FROM hwpx_agent.revisions AS revision
            JOIN hwpx_agent.artifacts AS result_artifact
              ON result_artifact.tenant_id = revision.tenant_id
             AND result_artifact.artifact_id = revision.result_artifact_id
            JOIN hwpx_agent.artifact_acl AS result_acl
              ON result_acl.tenant_id = result_artifact.tenant_id
             AND result_acl.artifact_id = result_artifact.artifact_id
            JOIN hwpx_agent.revision_graph_seals AS seal
              ON seal.tenant_id = revision.tenant_id
             AND seal.project_id = revision.project_id
             AND seal.revision_id = revision.revision_id
            JOIN hwpx_agent.revision_commit_receipts AS commit_receipt
              ON commit_receipt.tenant_id = revision.tenant_id
             AND commit_receipt.project_id = revision.project_id
             AND commit_receipt.committed_revision_id = revision.revision_id
            WHERE revision.tenant_id = p_tenant_id
              AND revision.project_id = p_project_id
              AND revision.revision_id = p_result_revision_id
              AND revision.source_artifact_id = p_source_artifact_id
              AND revision.operation_plan_sha256 = p_operation_plan_sha256
              AND revision.validation_state = 'verified'
              AND revision.created_by_subject_sha256 = p_subject_sha256
              AND result_artifact.service_metadata_version = 1
              AND result_artifact.storage_state = 'available'
              AND result_artifact.validation_state = 'verified'
              AND result_artifact.artifact_kind = 'result'
              AND result_artifact.content_sha256 = p_expected_effect_sha256
              AND result_acl.subject_sha256 = p_subject_sha256
              AND (result_acl.can_read OR result_acl.can_manage)
              AND seal.seal_kind = 'service_v1'
              AND seal.committed_generation = p_expected_generation + 1
              AND seal.transaction_receipt_sha256 = p_transaction_receipt_sha256
              AND seal.commit_id = commit_receipt.commit_id
              AND seal.commit_request_sha256 = commit_receipt.commit_request_sha256
              AND commit_receipt.branch_id = p_branch_id
              AND commit_receipt.previous_revision_id IS NOT DISTINCT FROM p_expected_revision_id
              AND commit_receipt.expected_generation = p_expected_generation
              AND commit_receipt.committed_generation = p_expected_generation + 1
              AND commit_receipt.transaction_receipt_sha256 = p_transaction_receipt_sha256
              AND commit_receipt.subject_sha256 = p_subject_sha256
        )
$$;

CREATE FUNCTION hwpx_agent.guard_idempotent_revision_commit_v2()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_record hwpx_agent.idempotency_records%ROWTYPE;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_authorization hwpx_agent.idempotency_commit_authorizations%ROWTYPE;
    v_revision hwpx_agent.revisions%ROWTYPE;
    v_result_sha256 character(64);
    v_result_qualified boolean;
    v_presented_authorization_text text;
    v_presented_authorization_id uuid;
    v_now timestamptz := clock_timestamp();
BEGIN
    SELECT * INTO v_record
    FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = NEW.tenant_id
      AND record.project_id = NEW.project_id
      AND record.transaction_receipt_sha256 = NEW.transaction_receipt_sha256
      AND record.record_version = 2;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = '42501', MESSAGE = 'IDEMPOTENCY_COMMIT_AUTHORIZATION_REQUIRED';
    END IF;

    BEGIN
        SELECT * INTO v_authorization
        FROM hwpx_agent.idempotency_commit_authorizations AS commit_auth
        WHERE commit_auth.tenant_id = NEW.tenant_id
          AND commit_auth.project_id = NEW.project_id
          AND commit_auth.idempotency_key = v_record.idempotency_key
          AND commit_auth.transaction_receipt_sha256 = NEW.transaction_receipt_sha256
        FOR UPDATE NOWAIT;
    EXCEPTION
        WHEN lock_not_available THEN
            RAISE EXCEPTION USING
                ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_COMMIT_AUTHORIZATION_BUSY';
    END;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = '42501', MESSAGE = 'IDEMPOTENCY_COMMIT_AUTHORIZATION_REQUIRED';
    END IF;

    v_presented_authorization_text := current_setting(
        'hwpx_agent.commit_authorization_id', true
    );
    IF v_presented_authorization_text IS NULL
       OR v_presented_authorization_text !~
          '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN
        RAISE EXCEPTION USING
            ERRCODE = '42501', MESSAGE = 'IDEMPOTENCY_COMMIT_CAPABILITY_MISMATCH';
    END IF;
    v_presented_authorization_id := v_presented_authorization_text::uuid;
    IF v_presented_authorization_id <> v_authorization.commit_authorization_id THEN
        RAISE EXCEPTION USING
            ERRCODE = '42501', MESSAGE = 'IDEMPOTENCY_COMMIT_CAPABILITY_MISMATCH';
    END IF;

    SELECT * INTO v_job FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = v_record.tenant_id
      AND job.project_id = v_record.project_id
      AND job.job_id = v_record.job_id;
    SELECT * INTO v_revision FROM hwpx_agent.revisions AS revision
    WHERE revision.tenant_id = NEW.tenant_id
      AND revision.project_id = NEW.project_id
      AND revision.revision_id = NEW.committed_revision_id;
    SELECT
        result_artifact.content_sha256,
        EXISTS (
            SELECT 1 FROM hwpx_agent.artifact_acl AS acl
            WHERE acl.tenant_id = result_artifact.tenant_id
              AND acl.artifact_id = result_artifact.artifact_id
              AND acl.subject_sha256 = v_record.subject_sha256
              AND (acl.can_read OR acl.can_manage)
        )
    INTO v_result_sha256, v_result_qualified
    FROM hwpx_agent.artifacts AS result_artifact
    WHERE result_artifact.tenant_id = NEW.tenant_id
      AND result_artifact.artifact_id = v_revision.result_artifact_id
      AND result_artifact.service_metadata_version = 1
      AND result_artifact.storage_state = 'available'
      AND result_artifact.validation_state = 'verified'
      AND result_artifact.artifact_kind = 'result';

    IF v_record.state <> 'in_progress'
       OR v_record.expires_at <= v_now
       OR v_record.attempt_count <> v_authorization.attempt_no
       OR v_record.last_fencing_token <> v_authorization.fencing_token
       OR v_job.state_machine_version IS DISTINCT FROM 2
       OR v_job.state <> 'validating'
       OR v_job.lease_expires_at <= v_now
       OR ROW(
            v_authorization.job_id, v_authorization.agent_instance_id,
            v_authorization.execution_id, v_authorization.attempt_no,
            v_authorization.fencing_token
       ) IS DISTINCT FROM ROW(
            v_job.job_id, v_job.lease_owner_agent_id, v_job.active_execution_id,
            v_job.attempt_count, v_job.fencing_token
       )
       OR NEW.branch_id <> v_record.branch_id
       OR NEW.previous_revision_id IS DISTINCT FROM v_record.expected_revision_id
       OR NEW.expected_generation <> v_record.expected_revision_generation
       OR NEW.subject_sha256 <> v_record.subject_sha256
       OR v_revision.source_artifact_id <> v_record.source_artifact_id
       OR v_revision.operation_plan_sha256 <> v_job.operation_plan_sha256
       OR v_revision.validation_state <> 'verified'
       OR v_result_sha256 IS DISTINCT FROM v_record.expected_effect_sha256
       OR NOT COALESCE(v_result_qualified, false) THEN
        RAISE EXCEPTION USING
            ERRCODE = '42501', MESSAGE = 'IDEMPOTENCY_COMMIT_FENCE_MISMATCH';
    END IF;

    DELETE FROM hwpx_agent.idempotency_commit_authorizations AS commit_auth
    WHERE commit_auth.tenant_id = v_authorization.tenant_id
      AND commit_auth.project_id = v_authorization.project_id
      AND commit_auth.idempotency_key = v_authorization.idempotency_key
      AND commit_auth.created_backend_pid = v_authorization.created_backend_pid
      AND commit_auth.created_transaction_id = v_authorization.created_transaction_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_COMMIT_AUTHORIZATION_LOST';
    END IF;
    RETURN NEW;
END
$$;

CREATE TRIGGER revision_commit_receipts_idempotency_v2_guard
BEFORE INSERT ON hwpx_agent.revision_commit_receipts
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.guard_idempotent_revision_commit_v2();

CREATE FUNCTION hwpx_agent.commit_idempotent_revision_cas_v2(
    p_tenant_id uuid,
    p_project_id uuid,
    p_branch_id uuid,
    p_subject_sha256 character(64),
    p_idempotency_key uuid,
    p_job_id uuid,
    p_agent_instance_id uuid,
    p_execution_id uuid,
    p_attempt_no integer,
    p_fencing_token bigint,
    p_commit_authorization_id uuid,
    p_commit_id uuid,
    p_expected_revision_id uuid,
    p_expected_generation bigint,
    p_new_revision_id uuid,
    p_parent_revision_ids uuid[],
    p_source_artifact_id uuid,
    p_result_artifact_id uuid,
    p_semantic_diff_artifact_id uuid,
    p_operation_plan_sha256 character(64),
    p_validation_state text,
    p_validation_summary_sha256 character(64),
    p_transaction_receipt_sha256 character(64),
    p_commit_request_sha256 character(64),
    p_commit_receipt_sha256 character(64)
)
RETURNS TABLE (
    outcome text,
    observed_revision_id uuid,
    observed_generation bigint,
    committed_revision_id uuid,
    committed_generation bigint,
    receipt_sha256 character(64)
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(
        p_tenant_id, p_project_id, p_subject_sha256
    );
    IF p_commit_authorization_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_attempt_no NOT BETWEEN 1 AND 10
       OR p_fencing_token <> p_attempt_no THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023', MESSAGE = 'IDEMPOTENCY_COMMIT_REQUEST_INVALID';
    END IF;
    PERFORM 1
    FROM hwpx_agent.idempotency_commit_authorizations AS commit_auth
    WHERE commit_auth.tenant_id = p_tenant_id
      AND commit_auth.project_id = p_project_id
      AND commit_auth.idempotency_key = p_idempotency_key
      AND commit_auth.job_id = p_job_id
      AND commit_auth.agent_instance_id = p_agent_instance_id
      AND commit_auth.execution_id = p_execution_id
      AND commit_auth.attempt_no = p_attempt_no
      AND commit_auth.fencing_token = p_fencing_token
      AND commit_auth.commit_authorization_id = p_commit_authorization_id
      AND commit_auth.transaction_receipt_sha256 = p_transaction_receipt_sha256
    FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = '42501', MESSAGE = 'IDEMPOTENCY_COMMIT_AUTHORIZATION_REQUIRED';
    END IF;

    PERFORM set_config(
        'hwpx_agent.commit_authorization_id', p_commit_authorization_id::text, true
    );
    RETURN QUERY SELECT * FROM hwpx_agent.commit_revision_cas(
        p_tenant_id, p_project_id, p_branch_id, p_subject_sha256,
        p_commit_id, p_expected_revision_id, p_expected_generation,
        p_new_revision_id, p_parent_revision_ids, p_source_artifact_id,
        p_result_artifact_id, p_semantic_diff_artifact_id,
        p_operation_plan_sha256, p_validation_state,
        p_validation_summary_sha256, p_transaction_receipt_sha256,
        p_commit_request_sha256, p_commit_receipt_sha256
    );
    PERFORM set_config('hwpx_agent.commit_authorization_id', '', true);
END
$$;

CREATE FUNCTION hwpx_agent.idempotency_v2_retry_at(
    p_now timestamptz,
    p_attempt_count integer,
    p_base_delay_seconds integer,
    p_max_delay_seconds integer
)
RETURNS timestamptz
LANGUAGE sql
IMMUTABLE
SET search_path = pg_catalog
AS $$
    SELECT p_now + make_interval(secs => LEAST(
        p_max_delay_seconds,
        (p_base_delay_seconds::numeric * power(2::numeric, GREATEST(p_attempt_count - 1, 0)))::integer
    ))
$$;

-- A shared return shape keeps claim/replay, mutation and reconciliation observations exact.
CREATE FUNCTION hwpx_agent.claim_idempotent_job_v2(
    p_tenant_id uuid,
    p_project_id uuid,
    p_branch_id uuid,
    p_subject_sha256 character(64),
    p_idempotency_key uuid,
    p_job_id uuid,
    p_request_id uuid,
    p_source_artifact_id uuid,
    p_expected_revision_id uuid,
    p_expected_revision_generation bigint,
    p_request_sha256 character(64),
    p_execution_manifest_sha256 character(64),
    p_source_artifact_sha256 character(64),
    p_expected_effect_sha256 character(64),
    p_transaction_receipt_sha256 character(64),
    p_operation_plan_sha256 character(64),
    p_required_target_profile_id text,
    p_required_capability_set_sha256 character(64),
    p_max_attempts integer,
    p_base_delay_seconds integer,
    p_max_delay_seconds integer,
    p_ttl_seconds integer,
    p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_outcome text, returned_job_id uuid, returned_state text,
    returned_attempt_count integer, returned_fencing_token bigint,
    returned_retry_not_before timestamptz, returned_result_revision_id uuid,
    returned_terminal_error_code text, returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_record hwpx_agent.idempotency_records%ROWTYPE;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_head_revision_id uuid;
    v_head_generation bigint;
    v_now timestamptz := transaction_timestamp();
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(
        p_tenant_id, p_project_id, p_subject_sha256
    );
    IF p_branch_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_idempotency_key = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_job_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_request_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_source_artifact_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_request_sha256 !~ '^[0-9a-f]{64}$'
       OR p_execution_manifest_sha256 !~ '^[0-9a-f]{64}$'
       OR p_source_artifact_sha256 !~ '^[0-9a-f]{64}$'
       OR p_expected_effect_sha256 !~ '^[0-9a-f]{64}$'
       OR p_transaction_receipt_sha256 !~ '^[0-9a-f]{64}$'
       OR p_operation_plan_sha256 !~ '^[0-9a-f]{64}$'
       OR p_required_capability_set_sha256 !~ '^[0-9a-f]{64}$'
       OR p_required_target_profile_id !~ '^[A-Za-z0-9][A-Za-z0-9._-]{1,126}$'
       OR p_max_attempts NOT BETWEEN 1 AND 10
       OR p_base_delay_seconds NOT BETWEEN 1 AND 86400
       OR p_max_delay_seconds NOT BETWEEN p_base_delay_seconds AND 86400
       OR p_ttl_seconds NOT BETWEEN 60 AND 604800
       OR p_event_sha256 !~ '^[0-9a-f]{64}$'
       OR (p_expected_revision_id IS NULL AND p_expected_revision_generation <> 0)
       OR (p_expected_revision_id IS NOT NULL AND p_expected_revision_generation <= 0) THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'IDEMPOTENCY_CLAIM_REQUEST_INVALID';
    END IF;

    PERFORM pg_advisory_xact_lock(hashtextextended(
        concat(p_tenant_id::text, '/', p_project_id::text, '/', p_idempotency_key::text), 0
    ));
    SELECT * INTO v_record FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = p_tenant_id AND record.project_id = p_project_id
      AND record.idempotency_key = p_idempotency_key
    FOR UPDATE;
    IF FOUND THEN
        SELECT * INTO v_job FROM hwpx_agent.jobs AS job
        WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
          AND job.job_id = v_record.job_id;
        IF v_record.record_version <> 2 OR v_job.state_machine_version IS DISTINCT FROM 2
           OR ROW(
                v_record.subject_sha256, v_record.branch_id, v_record.job_id,
                v_record.request_id, v_record.source_artifact_id,
                v_record.expected_revision_id, v_record.expected_revision_generation,
                v_record.request_sha256, v_record.execution_manifest_sha256,
                v_record.source_artifact_sha256, v_record.expected_effect_sha256,
                v_record.transaction_receipt_sha256, v_record.max_attempts,
                v_record.base_delay_seconds, v_record.max_delay_seconds,
                extract(epoch FROM (v_record.expires_at - v_record.created_at))::integer
           ) IS DISTINCT FROM ROW(
                p_subject_sha256, p_branch_id, p_job_id, p_request_id,
                p_source_artifact_id, p_expected_revision_id,
                p_expected_revision_generation, p_request_sha256,
                p_execution_manifest_sha256, p_source_artifact_sha256,
                p_expected_effect_sha256, p_transaction_receipt_sha256,
                p_max_attempts, p_base_delay_seconds, p_max_delay_seconds, p_ttl_seconds
           )
           OR ROW(
                v_job.request_id, v_job.input_artifact_id, v_job.expected_revision_id,
                v_job.operation_plan_sha256, v_job.required_target_profile_id,
                v_job.required_capability_set_sha256
           ) IS DISTINCT FROM ROW(
                p_request_id, p_source_artifact_id, p_expected_revision_id,
                p_operation_plan_sha256, p_required_target_profile_id,
                p_required_capability_set_sha256
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23505', MESSAGE = 'IDEMPOTENCY_KEY_CONFLICT';
        END IF;
        RETURN QUERY SELECT 'replay'::text, v_record.job_id, v_record.state,
            v_record.attempt_count, v_record.last_fencing_token,
            v_record.retry_not_before, v_record.result_revision_id,
            v_record.terminal_error_code, v_record.receipt_artifact_id;
        RETURN;
    END IF;

    SELECT branch.head_revision_id, branch.head_generation
    INTO v_head_revision_id, v_head_generation
    FROM hwpx_agent.branches AS branch
    WHERE branch.tenant_id = p_tenant_id AND branch.project_id = p_project_id
      AND branch.branch_id = p_branch_id
    FOR UPDATE;
    IF NOT FOUND OR ROW(v_head_revision_id, v_head_generation)
       IS DISTINCT FROM ROW(p_expected_revision_id, p_expected_revision_generation)
       OR v_head_generation < 0 THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_HEAD_CONFLICT';
    END IF;
    IF NOT hwpx_agent.idempotency_v2_artifact_qualified(
        p_tenant_id, p_subject_sha256, p_source_artifact_id,
        'source', p_source_artifact_sha256
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'IDEMPOTENCY_SOURCE_NOT_QUALIFIED';
    END IF;

    BEGIN
        INSERT INTO hwpx_agent.jobs (
            tenant_id, project_id, job_id, request_id, input_artifact_id,
            expected_revision_id, operation_plan_sha256, required_target_profile_id,
            required_capability_set_sha256, state, attempt_count, fencing_token,
            state_machine_version
        ) VALUES (
            p_tenant_id, p_project_id, p_job_id, p_request_id, p_source_artifact_id,
            p_expected_revision_id, p_operation_plan_sha256, p_required_target_profile_id,
            p_required_capability_set_sha256, 'queued', 0, 0, 2
        );
    EXCEPTION
        WHEN unique_violation THEN
            RAISE EXCEPTION USING
                ERRCODE = '23505', MESSAGE = 'IDEMPOTENCY_IDENTITY_ALREADY_EXISTS';
    END;
    INSERT INTO hwpx_agent.idempotency_records (
        tenant_id, project_id, idempotency_key, request_sha256, state, job_id,
        created_at, updated_at, expires_at, record_version, subject_sha256,
        branch_id, request_id, source_artifact_id, expected_revision_id,
        expected_revision_generation, execution_manifest_sha256,
        source_artifact_sha256, expected_effect_sha256,
        transaction_receipt_sha256, max_attempts, base_delay_seconds,
        max_delay_seconds, attempt_count, last_fencing_token
    ) VALUES (
        p_tenant_id, p_project_id, p_idempotency_key, p_request_sha256,
        'claimed', p_job_id, v_now, v_now,
        v_now + make_interval(secs => p_ttl_seconds), 2, p_subject_sha256,
        p_branch_id, p_request_id, p_source_artifact_id, p_expected_revision_id,
        p_expected_revision_generation, p_execution_manifest_sha256,
        p_source_artifact_sha256, p_expected_effect_sha256,
        p_transaction_receipt_sha256, p_max_attempts, p_base_delay_seconds,
        p_max_delay_seconds, 0, 0
    );
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'idempotency.v2_claimed',
        p_subject_sha256, p_job_id, p_event_sha256
    );
    RETURN QUERY SELECT 'new'::text, p_job_id, 'claimed'::text,
        0, 0::bigint, NULL::timestamptz, NULL::uuid, NULL::text, NULL::uuid;
END
$$;

CREATE FUNCTION hwpx_agent.lease_idempotent_job_v2(
    p_tenant_id uuid, p_project_id uuid, p_subject_sha256 character(64),
    p_idempotency_key uuid, p_job_id uuid, p_agent_instance_id uuid,
    p_execution_id uuid, p_lease_seconds integer, p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_outcome text, returned_job_id uuid, returned_state text,
    returned_attempt_count integer, returned_fencing_token bigint,
    returned_retry_not_before timestamptz, returned_result_revision_id uuid,
    returned_terminal_error_code text, returned_receipt_artifact_id uuid,
    returned_commit_authorization_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_record hwpx_agent.idempotency_records%ROWTYPE;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_worker hwpx_agent.worker_registrations%ROWTYPE;
    v_attempt integer;
    v_commit_authorization_id uuid := gen_random_uuid();
    v_now timestamptz := clock_timestamp();
    v_expires timestamptz;
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(p_tenant_id, p_project_id, p_subject_sha256);
    IF p_job_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_agent_instance_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_execution_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_lease_seconds NOT BETWEEN 1 AND 3600
       OR p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'IDEMPOTENCY_LEASE_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_record FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = p_tenant_id AND record.project_id = p_project_id
      AND record.idempotency_key = p_idempotency_key FOR UPDATE;
    IF NOT FOUND OR v_record.record_version <> 2 OR v_record.job_id <> p_job_id
       OR v_record.subject_sha256 <> p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'IDEMPOTENCY_RECORD_NOT_FOUND';
    END IF;
    SELECT * INTO v_job FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
      AND job.job_id = p_job_id FOR UPDATE;
    IF NOT FOUND OR v_job.state_machine_version IS DISTINCT FROM 2
       OR (v_record.state = 'claimed' AND v_job.state <> 'queued')
       OR (v_record.state = 'retry_pending' AND v_job.state <> 'retry_pending')
       OR v_record.state NOT IN ('claimed', 'retry_pending') THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_LEASE_STATE_INVALID';
    END IF;
    IF v_record.expires_at <= v_now THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_EXPIRED';
    END IF;
    IF v_record.retry_not_before IS NOT NULL AND v_record.retry_not_before > v_now THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_RETRY_NOT_READY';
    END IF;
    IF v_record.attempt_count >= v_record.max_attempts THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_RETRY_EXHAUSTED';
    END IF;
    IF NOT hwpx_agent.idempotency_v2_artifact_qualified(
        p_tenant_id, p_subject_sha256, v_record.source_artifact_id,
        'source', v_record.source_artifact_sha256
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'IDEMPOTENCY_SOURCE_NOT_QUALIFIED';
    END IF;
    SELECT * INTO v_worker FROM hwpx_agent.worker_registrations AS worker
    WHERE worker.tenant_id = p_tenant_id
      AND worker.agent_instance_id = p_agent_instance_id FOR UPDATE;
    v_expires := v_now + make_interval(secs => p_lease_seconds);
    IF NOT FOUND OR v_worker.subject_sha256 <> p_subject_sha256
       OR v_worker.target_profile_id <> v_job.required_target_profile_id
       OR v_worker.capability_set_sha256 <> v_job.required_capability_set_sha256
       OR v_worker.state <> 'ready' OR v_worker.last_heartbeat_at > v_now
       OR v_worker.expires_at <= v_now OR v_expires > v_worker.expires_at
       OR v_expires > v_record.expires_at THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'JOB_WORKER_NOT_QUALIFIED';
    END IF;
    v_attempt := v_record.attempt_count + 1;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'on', true);
    UPDATE hwpx_agent.jobs SET
        state = 'leased', attempt_count = v_attempt,
        lease_owner_agent_id = p_agent_instance_id, active_execution_id = p_execution_id,
        fencing_token = v_attempt, lease_issued_at = v_now,
        lease_expires_at = v_expires, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    INSERT INTO hwpx_agent.job_attempts (
        tenant_id, project_id, job_id, attempt_no, execution_id,
        agent_instance_id, fencing_token, state, started_at,
        state_machine_version, lease_expires_at, updated_at
    ) VALUES (
        p_tenant_id, p_project_id, p_job_id, v_attempt, p_execution_id,
        p_agent_instance_id, v_attempt, 'leased', v_now, 2, v_expires, v_now
    );
    INSERT INTO hwpx_agent.idempotency_commit_authorizations (
        tenant_id, project_id, idempotency_key, job_id,
        agent_instance_id, execution_id, attempt_no, fencing_token,
        commit_authorization_id, transaction_receipt_sha256, created_backend_pid,
        created_transaction_id, created_at
    ) VALUES (
        p_tenant_id, p_project_id, p_idempotency_key, p_job_id,
        p_agent_instance_id, p_execution_id, v_attempt, v_attempt,
        v_commit_authorization_id, v_record.transaction_receipt_sha256, pg_backend_pid(),
        pg_current_xact_id(), v_now
    );
    UPDATE hwpx_agent.idempotency_records SET
        state = 'in_progress', attempt_count = v_attempt,
        last_fencing_token = v_attempt, retry_not_before = NULL,
        receipt_artifact_id = NULL, terminal_error_code = NULL,
        updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND idempotency_key = p_idempotency_key;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'off', true);
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'idempotency.v2_leased',
        p_subject_sha256, p_job_id, p_event_sha256
    );
    RETURN QUERY SELECT 'leased'::text, p_job_id, 'in_progress'::text,
        v_attempt, v_attempt::bigint, NULL::timestamptz,
        NULL::uuid, NULL::text, NULL::uuid, v_commit_authorization_id;
END
$$;

CREATE FUNCTION hwpx_agent.advance_idempotent_job_v2(
    p_tenant_id uuid, p_project_id uuid, p_subject_sha256 character(64),
    p_idempotency_key uuid, p_job_id uuid, p_agent_instance_id uuid,
    p_execution_id uuid, p_attempt_no integer, p_fencing_token bigint,
    p_expected_state text, p_next_state text, p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_outcome text, returned_job_id uuid, returned_state text,
    returned_attempt_count integer, returned_fencing_token bigint,
    returned_retry_not_before timestamptz, returned_result_revision_id uuid,
    returned_terminal_error_code text, returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_record hwpx_agent.idempotency_records%ROWTYPE;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_now timestamptz := clock_timestamp();
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(p_tenant_id, p_project_id, p_subject_sha256);
    IF ROW(p_expected_state, p_next_state) NOT IN (
        ROW('leased', 'staged'), ROW('staged', 'executing'), ROW('executing', 'validating')
    ) OR p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'IDEMPOTENCY_STAGE_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_record FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = p_tenant_id AND record.project_id = p_project_id
      AND record.idempotency_key = p_idempotency_key FOR UPDATE;
    SELECT * INTO v_job FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
      AND job.job_id = p_job_id FOR UPDATE;
    IF v_record.record_version IS DISTINCT FROM 2 OR v_record.state <> 'in_progress'
       OR v_record.job_id <> p_job_id OR v_record.subject_sha256 <> p_subject_sha256
       OR v_job.state_machine_version IS DISTINCT FROM 2 OR v_job.state <> p_expected_state
       OR ROW(v_job.lease_owner_agent_id, v_job.active_execution_id,
              v_job.attempt_count, v_job.fencing_token)
          IS DISTINCT FROM ROW(p_agent_instance_id, p_execution_id,
                               p_attempt_no, p_fencing_token) THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_LEASE_MISMATCH';
    END IF;
    IF v_job.lease_expires_at <= v_now OR v_record.expires_at <= v_now THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'JOB_LEASE_EXPIRED';
    END IF;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'on', true);
    UPDATE hwpx_agent.jobs SET state = p_next_state, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    IF p_next_state = 'executing' THEN
        UPDATE hwpx_agent.job_attempts SET state = 'running', updated_at = v_now
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id
          AND attempt_no = p_attempt_no AND execution_id = p_execution_id
          AND agent_instance_id = p_agent_instance_id AND fencing_token = p_fencing_token
          AND state_machine_version = 2 AND state = 'leased';
        IF NOT FOUND THEN
            RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_ATTEMPT_MISMATCH';
        END IF;
    END IF;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'off', true);
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, concat('idempotency.v2_', p_next_state),
        p_subject_sha256, p_job_id, p_event_sha256
    );
    RETURN QUERY SELECT p_next_state, p_job_id, 'in_progress'::text,
        p_attempt_no, p_fencing_token, NULL::timestamptz,
        NULL::uuid, NULL::text, NULL::uuid;
END
$$;

CREATE FUNCTION hwpx_agent.heartbeat_idempotent_job_v2(
    p_tenant_id uuid, p_project_id uuid, p_subject_sha256 character(64),
    p_idempotency_key uuid, p_job_id uuid, p_agent_instance_id uuid,
    p_execution_id uuid, p_attempt_no integer, p_fencing_token bigint,
    p_lease_seconds integer, p_event_sha256 character(64)
)
RETURNS TABLE (returned_job_id uuid, returned_lease_expires_at timestamptz,
               returned_fencing_token bigint)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_record hwpx_agent.idempotency_records%ROWTYPE;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_worker hwpx_agent.worker_registrations%ROWTYPE;
    v_now timestamptz := clock_timestamp();
    v_expires timestamptz;
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(p_tenant_id, p_project_id, p_subject_sha256);
    IF p_lease_seconds NOT BETWEEN 1 AND 3600 OR p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'IDEMPOTENCY_HEARTBEAT_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_record FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = p_tenant_id AND record.project_id = p_project_id
      AND record.idempotency_key = p_idempotency_key FOR UPDATE;
    SELECT * INTO v_job FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
      AND job.job_id = p_job_id FOR UPDATE;
    IF v_record.record_version IS DISTINCT FROM 2 OR v_record.state <> 'in_progress'
       OR v_record.job_id <> p_job_id OR v_record.subject_sha256 <> p_subject_sha256
       OR v_job.state_machine_version IS DISTINCT FROM 2
       OR v_job.state NOT IN ('leased', 'staged', 'executing', 'validating')
       OR ROW(v_job.lease_owner_agent_id, v_job.active_execution_id,
              v_job.attempt_count, v_job.fencing_token)
          IS DISTINCT FROM ROW(p_agent_instance_id, p_execution_id,
                               p_attempt_no, p_fencing_token)
       OR v_job.lease_expires_at <= v_now THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_LEASE_MISMATCH';
    END IF;
    SELECT * INTO v_worker FROM hwpx_agent.worker_registrations AS worker
    WHERE worker.tenant_id = p_tenant_id AND worker.agent_instance_id = p_agent_instance_id
    FOR UPDATE;
    v_expires := v_now + make_interval(secs => p_lease_seconds);
    IF NOT FOUND OR v_worker.subject_sha256 <> p_subject_sha256
       OR v_worker.target_profile_id <> v_job.required_target_profile_id
       OR v_worker.capability_set_sha256 <> v_job.required_capability_set_sha256
       OR v_worker.expires_at <= v_now OR v_expires <= v_job.lease_expires_at
       OR v_expires > v_worker.expires_at
       OR v_expires > v_job.lease_issued_at + interval '1 hour'
       OR v_expires > v_record.expires_at THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'IDEMPOTENCY_HEARTBEAT_BOUNDS_INVALID';
    END IF;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'on', true);
    PERFORM set_config('hwpx_agent.allow_job_lease_heartbeat', 'on', true);
    UPDATE hwpx_agent.jobs SET lease_expires_at = v_expires, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    UPDATE hwpx_agent.job_attempts SET lease_expires_at = v_expires, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id
      AND attempt_no = p_attempt_no AND execution_id = p_execution_id
      AND agent_instance_id = p_agent_instance_id AND fencing_token = p_fencing_token
      AND state_machine_version = 2 AND state IN ('leased', 'running');
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_ATTEMPT_MISMATCH';
    END IF;
    PERFORM set_config('hwpx_agent.allow_job_lease_heartbeat', 'off', true);
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'off', true);
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'idempotency.v2_heartbeat',
        p_subject_sha256, p_job_id, p_event_sha256
    );
    RETURN QUERY SELECT p_job_id, v_expires, p_fencing_token;
END
$$;

CREATE FUNCTION hwpx_agent.schedule_idempotent_retry_v2(
    p_tenant_id uuid, p_project_id uuid, p_subject_sha256 character(64),
    p_idempotency_key uuid, p_job_id uuid, p_agent_instance_id uuid,
    p_execution_id uuid, p_attempt_no integer, p_fencing_token bigint,
    p_retry_class text, p_receipt_artifact_id uuid, p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_outcome text, returned_job_id uuid, returned_state text,
    returned_attempt_count integer, returned_fencing_token bigint,
    returned_retry_not_before timestamptz, returned_result_revision_id uuid,
    returned_terminal_error_code text, returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_record hwpx_agent.idempotency_records%ROWTYPE;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_attempt_state text;
    v_now timestamptz := clock_timestamp();
    v_retry_at timestamptz;
    v_terminal boolean;
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(p_tenant_id, p_project_id, p_subject_sha256);
    IF p_retry_class NOT IN ('transient_storage', 'transient_network')
       OR p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'IDEMPOTENCY_RETRY_CLASS_INVALID';
    END IF;
    SELECT * INTO v_record FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = p_tenant_id AND record.project_id = p_project_id
      AND record.idempotency_key = p_idempotency_key FOR UPDATE;
    SELECT * INTO v_job FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
      AND job.job_id = p_job_id FOR UPDATE;
    IF v_record.record_version IS DISTINCT FROM 2 OR v_record.state <> 'in_progress'
       OR v_record.job_id <> p_job_id OR v_record.subject_sha256 <> p_subject_sha256
       OR v_job.state_machine_version IS DISTINCT FROM 2
       OR v_job.state NOT IN ('leased', 'staged', 'executing', 'validating')
       OR ROW(v_job.lease_owner_agent_id, v_job.active_execution_id,
              v_job.attempt_count, v_job.fencing_token)
          IS DISTINCT FROM ROW(p_agent_instance_id, p_execution_id,
                               p_attempt_no, p_fencing_token)
       OR v_job.lease_expires_at <= v_now THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_LEASE_MISMATCH';
    END IF;
    IF NOT hwpx_agent.idempotency_v2_artifact_qualified(
        p_tenant_id, p_subject_sha256, p_receipt_artifact_id, 'receipt',
        (SELECT content_sha256 FROM hwpx_agent.artifacts
         WHERE tenant_id = p_tenant_id AND artifact_id = p_receipt_artifact_id)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'IDEMPOTENCY_RECEIPT_NOT_QUALIFIED';
    END IF;
    IF NOT hwpx_agent.idempotency_v2_artifact_qualified(
        p_tenant_id, p_subject_sha256, v_record.source_artifact_id,
        'source', v_record.source_artifact_sha256
    ) OR NOT hwpx_agent.idempotency_v2_head_matches(
        p_tenant_id, p_project_id, v_record.branch_id,
        v_record.expected_revision_id, v_record.expected_revision_generation
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_NO_EFFECT_ORACLE_FAILED';
    END IF;
    v_retry_at := hwpx_agent.idempotency_v2_retry_at(
        v_now, v_record.attempt_count,
        v_record.base_delay_seconds, v_record.max_delay_seconds
    );
    v_terminal := v_record.attempt_count >= v_record.max_attempts
        OR v_retry_at >= v_record.expires_at;
    v_attempt_state := CASE WHEN v_job.state IN ('leased', 'staged') THEN 'leased' ELSE 'running' END;
    DELETE FROM hwpx_agent.idempotency_commit_authorizations
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND idempotency_key = p_idempotency_key
      AND job_id = p_job_id AND attempt_no = p_attempt_no
      AND fencing_token = p_fencing_token;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'on', true);
    UPDATE hwpx_agent.job_attempts SET state = 'failed',
        receipt_artifact_id = p_receipt_artifact_id, completed_at = v_now, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id
      AND attempt_no = p_attempt_no AND execution_id = p_execution_id
      AND agent_instance_id = p_agent_instance_id AND fencing_token = p_fencing_token
      AND state_machine_version = 2 AND state = v_attempt_state;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_ATTEMPT_MISMATCH';
    END IF;
    UPDATE hwpx_agent.jobs SET
        state = CASE WHEN v_terminal THEN 'failed' ELSE 'retry_pending' END,
        lease_owner_agent_id = NULL, active_execution_id = NULL,
        lease_issued_at = NULL, lease_expires_at = NULL,
        terminal_error_code = CASE WHEN v_terminal THEN 'RETRY_EXHAUSTED' ELSE NULL END,
        completed_at = CASE WHEN v_terminal THEN v_now ELSE NULL END,
        updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    UPDATE hwpx_agent.idempotency_records SET
        state = CASE WHEN v_terminal THEN 'terminal_failure' ELSE 'retry_pending' END,
        receipt_artifact_id = p_receipt_artifact_id,
        terminal_error_code = CASE WHEN v_terminal THEN 'RETRY_EXHAUSTED' ELSE NULL END,
        retry_not_before = CASE WHEN v_terminal THEN NULL ELSE v_retry_at END,
        last_retry_class = p_retry_class, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND idempotency_key = p_idempotency_key;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'off', true);
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id,
        CASE WHEN v_terminal THEN 'idempotency.v2_retry_exhausted'
             ELSE 'idempotency.v2_retry_scheduled' END,
        p_subject_sha256, p_job_id, p_event_sha256
    );
    RETURN QUERY SELECT
        CASE WHEN v_terminal THEN 'terminal_failure' ELSE 'retry_scheduled' END,
        p_job_id,
        CASE WHEN v_terminal THEN 'terminal_failure' ELSE 'retry_pending' END,
        p_attempt_no, p_fencing_token,
        CASE WHEN v_terminal THEN NULL ELSE v_retry_at END,
        NULL::uuid, CASE WHEN v_terminal THEN 'RETRY_EXHAUSTED' ELSE NULL END,
        p_receipt_artifact_id;
END
$$;

CREATE FUNCTION hwpx_agent.mark_idempotent_outcome_unknown_v2(
    p_tenant_id uuid, p_project_id uuid, p_subject_sha256 character(64),
    p_idempotency_key uuid, p_job_id uuid, p_agent_instance_id uuid,
    p_execution_id uuid, p_attempt_no integer, p_fencing_token bigint,
    p_receipt_artifact_id uuid, p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_outcome text, returned_job_id uuid, returned_state text,
    returned_attempt_count integer, returned_fencing_token bigint,
    returned_retry_not_before timestamptz, returned_result_revision_id uuid,
    returned_terminal_error_code text, returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_record hwpx_agent.idempotency_records%ROWTYPE;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_attempt_state text;
    v_now timestamptz := clock_timestamp();
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(p_tenant_id, p_project_id, p_subject_sha256);
    IF p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'IDEMPOTENCY_UNKNOWN_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_record FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = p_tenant_id AND record.project_id = p_project_id
      AND record.idempotency_key = p_idempotency_key FOR UPDATE;
    SELECT * INTO v_job FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
      AND job.job_id = p_job_id FOR UPDATE;
    IF v_record.record_version IS DISTINCT FROM 2 OR v_record.state <> 'in_progress'
       OR v_record.job_id <> p_job_id OR v_record.subject_sha256 <> p_subject_sha256
       OR v_job.state_machine_version IS DISTINCT FROM 2
       OR v_job.state NOT IN ('leased', 'staged', 'executing', 'validating')
       OR ROW(v_job.lease_owner_agent_id, v_job.active_execution_id,
              v_job.attempt_count, v_job.fencing_token)
          IS DISTINCT FROM ROW(p_agent_instance_id, p_execution_id,
                               p_attempt_no, p_fencing_token) THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_LEASE_MISMATCH';
    END IF;
    IF NOT hwpx_agent.idempotency_v2_artifact_qualified(
        p_tenant_id, p_subject_sha256, p_receipt_artifact_id, 'receipt',
        (SELECT content_sha256 FROM hwpx_agent.artifacts
         WHERE tenant_id = p_tenant_id AND artifact_id = p_receipt_artifact_id)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'IDEMPOTENCY_RECEIPT_NOT_QUALIFIED';
    END IF;
    v_attempt_state := CASE WHEN v_job.state IN ('leased', 'staged') THEN 'leased' ELSE 'running' END;
    DELETE FROM hwpx_agent.idempotency_commit_authorizations
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND idempotency_key = p_idempotency_key
      AND job_id = p_job_id AND attempt_no = p_attempt_no
      AND fencing_token = p_fencing_token;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'on', true);
    UPDATE hwpx_agent.job_attempts SET state = 'unknown_outcome',
        receipt_artifact_id = p_receipt_artifact_id, completed_at = v_now, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id
      AND attempt_no = p_attempt_no AND execution_id = p_execution_id
      AND agent_instance_id = p_agent_instance_id AND fencing_token = p_fencing_token
      AND state_machine_version = 2 AND state = v_attempt_state;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_ATTEMPT_MISMATCH';
    END IF;
    UPDATE hwpx_agent.jobs SET state = 'unknown_outcome',
        lease_owner_agent_id = NULL, active_execution_id = NULL,
        lease_issued_at = NULL, lease_expires_at = NULL,
        terminal_error_code = 'OUTCOME_UNKNOWN', completed_at = NULL, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    UPDATE hwpx_agent.idempotency_records SET state = 'outcome_unknown',
        receipt_artifact_id = p_receipt_artifact_id,
        terminal_error_code = 'OUTCOME_UNKNOWN', retry_not_before = NULL,
        last_retry_class = 'automation_unknown', updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND idempotency_key = p_idempotency_key;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'off', true);
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'idempotency.v2_outcome_unknown',
        p_subject_sha256, p_job_id, p_event_sha256
    );
    RETURN QUERY SELECT 'outcome_unknown'::text, p_job_id, 'outcome_unknown'::text,
        p_attempt_no, p_fencing_token, NULL::timestamptz,
        NULL::uuid, 'OUTCOME_UNKNOWN'::text, p_receipt_artifact_id;
END
$$;

CREATE FUNCTION hwpx_agent.complete_idempotent_job_success_v2(
    p_tenant_id uuid, p_project_id uuid, p_subject_sha256 character(64),
    p_idempotency_key uuid, p_job_id uuid, p_agent_instance_id uuid,
    p_execution_id uuid, p_attempt_no integer, p_fencing_token bigint,
    p_result_revision_id uuid, p_receipt_artifact_id uuid,
    p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_outcome text, returned_job_id uuid, returned_state text,
    returned_attempt_count integer, returned_fencing_token bigint,
    returned_retry_not_before timestamptz, returned_result_revision_id uuid,
    returned_terminal_error_code text, returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_record hwpx_agent.idempotency_records%ROWTYPE;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_now timestamptz := clock_timestamp();
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(p_tenant_id, p_project_id, p_subject_sha256);
    IF p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'IDEMPOTENCY_SUCCESS_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_record FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = p_tenant_id AND record.project_id = p_project_id
      AND record.idempotency_key = p_idempotency_key FOR UPDATE;
    SELECT * INTO v_job FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
      AND job.job_id = p_job_id FOR UPDATE;
    IF v_record.record_version IS DISTINCT FROM 2 OR v_record.state <> 'in_progress'
       OR v_record.job_id <> p_job_id OR v_record.subject_sha256 <> p_subject_sha256
       OR v_job.state_machine_version IS DISTINCT FROM 2 OR v_job.state <> 'validating'
       OR ROW(v_job.lease_owner_agent_id, v_job.active_execution_id,
              v_job.attempt_count, v_job.fencing_token)
          IS DISTINCT FROM ROW(p_agent_instance_id, p_execution_id,
                               p_attempt_no, p_fencing_token)
       OR v_job.lease_expires_at <= v_now THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_LEASE_MISMATCH';
    END IF;
    IF NOT hwpx_agent.idempotency_v2_committed_effect_qualified(
        p_tenant_id, p_project_id, v_record.branch_id, p_subject_sha256,
        v_record.source_artifact_id, v_record.source_artifact_sha256,
        v_record.expected_revision_id, v_record.expected_revision_generation,
        v_job.operation_plan_sha256, p_result_revision_id, v_record.expected_effect_sha256,
        v_record.transaction_receipt_sha256, p_receipt_artifact_id
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_COMMITTED_ORACLE_FAILED';
    END IF;
    DELETE FROM hwpx_agent.idempotency_commit_authorizations
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND idempotency_key = p_idempotency_key
      AND job_id = p_job_id AND attempt_no = p_attempt_no
      AND fencing_token = p_fencing_token;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'on', true);
    UPDATE hwpx_agent.job_attempts SET state = 'succeeded',
        receipt_artifact_id = p_receipt_artifact_id, completed_at = v_now, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id
      AND attempt_no = p_attempt_no AND execution_id = p_execution_id
      AND agent_instance_id = p_agent_instance_id AND fencing_token = p_fencing_token
      AND state_machine_version = 2 AND state = 'running';
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_ATTEMPT_MISMATCH';
    END IF;
    UPDATE hwpx_agent.jobs SET state = 'succeeded',
        lease_owner_agent_id = NULL, active_execution_id = NULL,
        lease_issued_at = NULL, lease_expires_at = NULL,
        result_revision_id = p_result_revision_id,
        terminal_error_code = NULL, completed_at = v_now, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    UPDATE hwpx_agent.idempotency_records SET state = 'terminal_success',
        result_revision_id = p_result_revision_id,
        receipt_artifact_id = p_receipt_artifact_id,
        terminal_error_code = NULL, retry_not_before = NULL, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND idempotency_key = p_idempotency_key;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'off', true);
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id,
        revision_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'idempotency.v2_succeeded',
        p_subject_sha256, p_job_id, p_result_revision_id, p_event_sha256
    );
    RETURN QUERY SELECT 'committed'::text, p_job_id, 'terminal_success'::text,
        p_attempt_no, p_fencing_token, NULL::timestamptz,
        p_result_revision_id, NULL::text, p_receipt_artifact_id;
END
$$;

CREATE FUNCTION hwpx_agent.fail_idempotent_job_terminal_v2(
    p_tenant_id uuid, p_project_id uuid, p_subject_sha256 character(64),
    p_idempotency_key uuid, p_job_id uuid, p_agent_instance_id uuid,
    p_execution_id uuid, p_attempt_no integer, p_fencing_token bigint,
    p_failure_class text, p_error_code text, p_receipt_artifact_id uuid,
    p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_outcome text, returned_job_id uuid, returned_state text,
    returned_attempt_count integer, returned_fencing_token bigint,
    returned_retry_not_before timestamptz, returned_result_revision_id uuid,
    returned_terminal_error_code text, returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_record hwpx_agent.idempotency_records%ROWTYPE;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_attempt_state text;
    v_now timestamptz := clock_timestamp();
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(p_tenant_id, p_project_id, p_subject_sha256);
    IF p_failure_class NOT IN ('planning', 'schema', 'validation')
       OR p_error_code !~ '^[A-Z][A-Z0-9_]{2,63}$'
       OR p_error_code IN ('OUTCOME_UNKNOWN', 'RETRY_EXHAUSTED')
       OR p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'IDEMPOTENCY_TERMINAL_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_record FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = p_tenant_id AND record.project_id = p_project_id
      AND record.idempotency_key = p_idempotency_key FOR UPDATE;
    SELECT * INTO v_job FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
      AND job.job_id = p_job_id FOR UPDATE;
    IF v_record.record_version IS DISTINCT FROM 2 OR v_record.state <> 'in_progress'
       OR v_record.job_id <> p_job_id OR v_record.subject_sha256 <> p_subject_sha256
       OR v_job.state_machine_version IS DISTINCT FROM 2
       OR v_job.state NOT IN ('leased', 'staged', 'executing', 'validating')
       OR ROW(v_job.lease_owner_agent_id, v_job.active_execution_id,
              v_job.attempt_count, v_job.fencing_token)
          IS DISTINCT FROM ROW(p_agent_instance_id, p_execution_id,
                               p_attempt_no, p_fencing_token) THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_LEASE_MISMATCH';
    END IF;
    IF NOT hwpx_agent.idempotency_v2_artifact_qualified(
        p_tenant_id, p_subject_sha256, p_receipt_artifact_id, 'receipt',
        (SELECT content_sha256 FROM hwpx_agent.artifacts
         WHERE tenant_id = p_tenant_id AND artifact_id = p_receipt_artifact_id)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'IDEMPOTENCY_RECEIPT_NOT_QUALIFIED';
    END IF;
    v_attempt_state := CASE WHEN v_job.state IN ('leased', 'staged') THEN 'leased' ELSE 'running' END;
    DELETE FROM hwpx_agent.idempotency_commit_authorizations
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND idempotency_key = p_idempotency_key
      AND job_id = p_job_id AND attempt_no = p_attempt_no
      AND fencing_token = p_fencing_token;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'on', true);
    UPDATE hwpx_agent.job_attempts SET state = 'failed',
        receipt_artifact_id = p_receipt_artifact_id, completed_at = v_now, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id
      AND attempt_no = p_attempt_no AND execution_id = p_execution_id
      AND agent_instance_id = p_agent_instance_id AND fencing_token = p_fencing_token
      AND state_machine_version = 2 AND state = v_attempt_state;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_ATTEMPT_MISMATCH';
    END IF;
    UPDATE hwpx_agent.jobs SET state = 'failed',
        lease_owner_agent_id = NULL, active_execution_id = NULL,
        lease_issued_at = NULL, lease_expires_at = NULL,
        terminal_error_code = p_error_code, completed_at = v_now, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    UPDATE hwpx_agent.idempotency_records SET state = 'terminal_failure',
        receipt_artifact_id = p_receipt_artifact_id,
        terminal_error_code = p_error_code, retry_not_before = NULL, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND idempotency_key = p_idempotency_key;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'off', true);
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, concat('idempotency.v2_terminal_', p_failure_class),
        p_subject_sha256, p_job_id, p_event_sha256
    );
    RETURN QUERY SELECT 'terminal_failure'::text, p_job_id, 'terminal_failure'::text,
        p_attempt_no, p_fencing_token, NULL::timestamptz,
        NULL::uuid, p_error_code, p_receipt_artifact_id;
END
$$;

CREATE FUNCTION hwpx_agent.reconcile_idempotent_job_v2(
    p_tenant_id uuid, p_project_id uuid, p_subject_sha256 character(64),
    p_idempotency_key uuid, p_job_id uuid, p_mode text,
    p_result_revision_id uuid, p_receipt_artifact_id uuid,
    p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_outcome text, returned_job_id uuid, returned_state text,
    returned_attempt_count integer, returned_fencing_token bigint,
    returned_retry_not_before timestamptz, returned_result_revision_id uuid,
    returned_terminal_error_code text, returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_record hwpx_agent.idempotency_records%ROWTYPE;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_now timestamptz := clock_timestamp();
    v_retry_at timestamptz;
    v_terminal boolean;
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(p_tenant_id, p_project_id, p_subject_sha256);
    IF p_mode NOT IN ('committed', 'no_effect')
       OR p_event_sha256 !~ '^[0-9a-f]{64}$'
       OR (p_mode = 'committed' AND p_result_revision_id IS NULL)
       OR (p_mode = 'no_effect' AND p_result_revision_id IS NOT NULL) THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'IDEMPOTENCY_RECONCILE_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_record FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = p_tenant_id AND record.project_id = p_project_id
      AND record.idempotency_key = p_idempotency_key FOR UPDATE;
    SELECT * INTO v_job FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
      AND job.job_id = p_job_id FOR UPDATE;
    IF v_record.record_version IS DISTINCT FROM 2 OR v_record.state <> 'outcome_unknown'
       OR v_record.job_id <> p_job_id OR v_record.subject_sha256 <> p_subject_sha256
       OR v_job.state_machine_version IS DISTINCT FROM 2
       OR v_job.state <> 'unknown_outcome' THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_RECONCILE_STATE_INVALID';
    END IF;

    IF p_mode = 'committed' THEN
        IF NOT hwpx_agent.idempotency_v2_committed_effect_qualified(
            p_tenant_id, p_project_id, v_record.branch_id, p_subject_sha256,
            v_record.source_artifact_id, v_record.source_artifact_sha256,
            v_record.expected_revision_id, v_record.expected_revision_generation,
            v_job.operation_plan_sha256, p_result_revision_id, v_record.expected_effect_sha256,
            v_record.transaction_receipt_sha256, p_receipt_artifact_id
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_COMMITTED_ORACLE_FAILED';
        END IF;
        PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'on', true);
        UPDATE hwpx_agent.jobs SET state = 'succeeded',
            result_revision_id = p_result_revision_id,
            terminal_error_code = NULL, completed_at = v_now, updated_at = v_now
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
        UPDATE hwpx_agent.idempotency_records SET state = 'terminal_success',
            result_revision_id = p_result_revision_id,
            receipt_artifact_id = p_receipt_artifact_id,
            terminal_error_code = NULL, retry_not_before = NULL, updated_at = v_now
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id
          AND idempotency_key = p_idempotency_key;
        PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'off', true);
        INSERT INTO hwpx_agent.audit_events (
            tenant_id, project_id, event_type, subject_sha256, job_id,
            revision_id, payload_sha256
        ) VALUES (
            p_tenant_id, p_project_id, 'idempotency.v2_reconciled_committed',
            p_subject_sha256, p_job_id, p_result_revision_id, p_event_sha256
        );
        RETURN QUERY SELECT 'committed'::text, p_job_id, 'terminal_success'::text,
            v_record.attempt_count, v_record.last_fencing_token,
            NULL::timestamptz, p_result_revision_id, NULL::text,
            p_receipt_artifact_id;
        RETURN;
    END IF;

    IF NOT hwpx_agent.idempotency_v2_artifact_qualified(
        p_tenant_id, p_subject_sha256, p_receipt_artifact_id, 'receipt',
        (SELECT content_sha256 FROM hwpx_agent.artifacts
         WHERE tenant_id = p_tenant_id AND artifact_id = p_receipt_artifact_id)
    ) OR NOT hwpx_agent.idempotency_v2_artifact_qualified(
        p_tenant_id, p_subject_sha256, v_record.source_artifact_id,
        'source', v_record.source_artifact_sha256
    ) OR NOT hwpx_agent.idempotency_v2_head_matches(
        p_tenant_id, p_project_id, v_record.branch_id,
        v_record.expected_revision_id, v_record.expected_revision_generation
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_NO_EFFECT_ORACLE_FAILED';
    END IF;
    v_retry_at := hwpx_agent.idempotency_v2_retry_at(
        v_now, v_record.attempt_count,
        v_record.base_delay_seconds, v_record.max_delay_seconds
    );
    v_terminal := v_record.attempt_count >= v_record.max_attempts
        OR v_retry_at >= v_record.expires_at;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'on', true);
    UPDATE hwpx_agent.jobs SET
        state = CASE WHEN v_terminal THEN 'failed' ELSE 'retry_pending' END,
        terminal_error_code = CASE WHEN v_terminal THEN 'RETRY_EXHAUSTED' ELSE NULL END,
        completed_at = CASE WHEN v_terminal THEN v_now ELSE NULL END,
        updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    UPDATE hwpx_agent.idempotency_records SET
        state = CASE WHEN v_terminal THEN 'terminal_failure' ELSE 'retry_pending' END,
        receipt_artifact_id = p_receipt_artifact_id,
        terminal_error_code = CASE WHEN v_terminal THEN 'RETRY_EXHAUSTED' ELSE NULL END,
        retry_not_before = CASE WHEN v_terminal THEN NULL ELSE v_retry_at END,
        last_retry_class = 'automation_no_effect', updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND idempotency_key = p_idempotency_key;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'off', true);
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id,
        CASE WHEN v_terminal THEN 'idempotency.v2_no_effect_exhausted'
             ELSE 'idempotency.v2_reconciled_no_effect' END,
        p_subject_sha256, p_job_id, p_event_sha256
    );
    RETURN QUERY SELECT
        CASE WHEN v_terminal THEN 'terminal_failure' ELSE 'no_effect' END,
        p_job_id,
        CASE WHEN v_terminal THEN 'terminal_failure' ELSE 'retry_pending' END,
        v_record.attempt_count, v_record.last_fencing_token,
        CASE WHEN v_terminal THEN NULL ELSE v_retry_at END,
        NULL::uuid, CASE WHEN v_terminal THEN 'RETRY_EXHAUSTED' ELSE NULL END,
        p_receipt_artifact_id;
END
$$;

CREATE FUNCTION hwpx_agent.get_idempotent_job_v2(
    p_tenant_id uuid, p_project_id uuid, p_subject_sha256 character(64),
    p_idempotency_key uuid
)
RETURNS TABLE (
    returned_outcome text, returned_job_id uuid, returned_state text,
    returned_attempt_count integer, returned_fencing_token bigint,
    returned_retry_not_before timestamptz, returned_result_revision_id uuid,
    returned_terminal_error_code text, returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
STABLE
SET search_path = pg_catalog, hwpx_agent
AS $$
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256
       OR NOT EXISTS (
            SELECT 1 FROM hwpx_agent.project_acl AS acl
            WHERE acl.tenant_id = p_tenant_id AND acl.project_id = p_project_id
              AND acl.subject_sha256 = p_subject_sha256
       ) THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'IDEMPOTENCY_RECORD_NOT_FOUND';
    END IF;
    RETURN QUERY SELECT 'read'::text, record.job_id, record.state,
        record.attempt_count, record.last_fencing_token, record.retry_not_before,
        record.result_revision_id, record.terminal_error_code, record.receipt_artifact_id
    FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = p_tenant_id AND record.project_id = p_project_id
      AND record.idempotency_key = p_idempotency_key AND record.record_version = 2;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'IDEMPOTENCY_RECORD_NOT_FOUND';
    END IF;
END
$$;

REVOKE ALL ON FUNCTION hwpx_agent.verify_idempotency_job_consistency() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.require_idempotency_v2_editor(uuid, uuid, character) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.idempotency_v2_artifact_qualified(
    uuid, character, uuid, text, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.idempotency_v2_head_matches(
    uuid, uuid, uuid, uuid, bigint
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.idempotency_v2_committed_effect_qualified(
    uuid, uuid, uuid, character, uuid, character, uuid, bigint,
    character, uuid, character, character, uuid
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.guard_idempotent_revision_commit_v2() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.commit_idempotent_revision_cas_v2(
    uuid, uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    uuid, uuid, uuid, bigint, uuid, uuid[], uuid, uuid, uuid,
    character, text, character, character, character, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.idempotency_v2_retry_at(
    timestamptz, integer, integer, integer
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.claim_idempotent_job_v2(
    uuid, uuid, uuid, character, uuid, uuid, uuid, uuid, uuid, bigint,
    character, character, character, character, character, character,
    text, character, integer, integer, integer, integer, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.lease_idempotent_job_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.advance_idempotent_job_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    text, text, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.heartbeat_idempotent_job_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    integer, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.schedule_idempotent_retry_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    text, uuid, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.mark_idempotent_outcome_unknown_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    uuid, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.complete_idempotent_job_success_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    uuid, uuid, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.fail_idempotent_job_terminal_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    text, text, uuid, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.reconcile_idempotent_job_v2(
    uuid, uuid, character, uuid, uuid, text, uuid, uuid, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.get_idempotent_job_v2(
    uuid, uuid, character, uuid
) FROM PUBLIC;

INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (7, 'p14.idempotency_reconciliation_v2', current_setting('hwpx_agent.migration_sha256'));

COMMIT;
