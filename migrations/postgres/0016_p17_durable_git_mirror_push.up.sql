BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 15 AND migration_name = 'p17.atomic_mirror_checkpoint_v3'
    ) OR EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version >= 16) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P17 durable Git mirror push requires exact schema version 15';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256', true) IS NULL
       OR current_setting('hwpx_agent.migration_sha256', true) !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            MESSAGE = 'P17 durable Git mirror push requires its migration digest';
    END IF;
END
$$;

CREATE TABLE hwpx_agent.git_mirror_push_effects (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    branch_id uuid NOT NULL,
    mirror_id uuid NOT NULL,
    push_id uuid NOT NULL,
    subject_sha256 character(64) NOT NULL,
    request_sha256 character(64) NOT NULL,
    idempotency_sha256 character(64) NOT NULL,
    expected_revision_id uuid,
    expected_generation bigint NOT NULL,
    expected_snapshot_sha256 character(64) NOT NULL,
    source_artifact_id uuid NOT NULL,
    result_revision_id uuid NOT NULL,
    result_generation bigint NOT NULL,
    result_snapshot_sha256 character(64) NOT NULL,
    result_artifact_id uuid NOT NULL,
    operation_plan_sha256 character(64) NOT NULL,
    git_plan_sha256 character(64) NOT NULL,
    git_plan_bytes bytea NOT NULL,
    expected_git_oid text,
    result_git_oid text NOT NULL,
    git_state_sha256 character(64) NOT NULL,
    validation_summary_sha256 character(64) NOT NULL,
    transaction_receipt_sha256 character(64) NOT NULL,
    commit_receipt_sha256 character(64) NOT NULL,
    state text NOT NULL,
    lease_execution_id uuid,
    lease_fencing_token bigint NOT NULL,
    lease_expires_at timestamptz,
    effect_receipt_sha256 character(64),
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    finalized_at timestamptz,
    diverged_at timestamptz,
    PRIMARY KEY (tenant_id, project_id, push_id),
    UNIQUE (tenant_id, project_id, request_sha256),
    UNIQUE (tenant_id, project_id, mirror_id, idempotency_sha256),
    UNIQUE (tenant_id, project_id, result_revision_id),
    CONSTRAINT git_mirror_push_mirror_fk FOREIGN KEY (tenant_id, mirror_id)
        REFERENCES hwpx_agent.project_local_mirrors (tenant_id, mirror_id) ON DELETE RESTRICT,
    CONSTRAINT git_mirror_push_branch_fk FOREIGN KEY (tenant_id, project_id, branch_id)
        REFERENCES hwpx_agent.branches (tenant_id, project_id, branch_id) ON DELETE RESTRICT,
    CONSTRAINT git_mirror_push_source_artifact_fk FOREIGN KEY (tenant_id, source_artifact_id)
        REFERENCES hwpx_agent.artifacts (tenant_id, artifact_id) ON DELETE RESTRICT,
    CONSTRAINT git_mirror_push_result_artifact_fk FOREIGN KEY (tenant_id, result_artifact_id)
        REFERENCES hwpx_agent.artifacts (tenant_id, artifact_id) ON DELETE RESTRICT,
    CONSTRAINT git_mirror_push_identity CHECK (
        push_id <> '00000000-0000-0000-0000-000000000000'::uuid
        AND result_revision_id <> '00000000-0000-0000-0000-000000000000'::uuid
        AND source_artifact_id <> result_artifact_id
        AND subject_sha256 ~ '^[0-9a-f]{64}$'
        AND request_sha256 ~ '^[0-9a-f]{64}$'
        AND idempotency_sha256 ~ '^[0-9a-f]{64}$'
        AND expected_snapshot_sha256 ~ '^[0-9a-f]{64}$'
        AND result_snapshot_sha256 ~ '^[0-9a-f]{64}$'
        AND operation_plan_sha256 ~ '^[0-9a-f]{64}$'
        AND git_plan_sha256 ~ '^[0-9a-f]{64}$'
        AND git_state_sha256 ~ '^[0-9a-f]{64}$'
        AND validation_summary_sha256 ~ '^[0-9a-f]{64}$'
        AND transaction_receipt_sha256 ~ '^[0-9a-f]{64}$'
        AND commit_receipt_sha256 ~ '^[0-9a-f]{64}$'
        AND (effect_receipt_sha256 IS NULL
            OR effect_receipt_sha256 ~ '^[0-9a-f]{64}$')
    ),
    CONSTRAINT git_mirror_push_generation CHECK (
        ((expected_revision_id IS NULL AND expected_generation = 0)
            OR (expected_revision_id IS NOT NULL AND expected_generation > 0))
        AND result_generation = expected_generation + 1
        AND result_generation > 0
    ),
    CONSTRAINT git_mirror_push_plan CHECK (
        octet_length(git_plan_bytes) BETWEEN 1 AND 4096
        AND git_plan_sha256 = encode(sha256(git_plan_bytes), 'hex')
        AND result_git_oid ~ '^[0-9a-f]{40}([0-9a-f]{24})?$'
        AND (expected_git_oid IS NULL OR (
            expected_git_oid ~ '^[0-9a-f]{40}([0-9a-f]{24})?$'
            AND length(expected_git_oid) = length(result_git_oid)
            AND expected_git_oid <> result_git_oid
        ))
    ),
    CONSTRAINT git_mirror_push_state CHECK (
        state IN ('executing', 'finalized', 'diverged')
    ),
    CONSTRAINT git_mirror_push_state_shape CHECK (
        (state = 'executing'
            AND lease_execution_id IS NOT NULL
            AND lease_expires_at IS NOT NULL
            AND effect_receipt_sha256 IS NULL
            AND finalized_at IS NULL AND diverged_at IS NULL)
        OR (state = 'finalized'
            AND lease_execution_id IS NULL AND lease_expires_at IS NULL
            AND effect_receipt_sha256 IS NOT NULL
            AND finalized_at IS NOT NULL AND diverged_at IS NULL)
        OR (state = 'diverged'
            AND lease_execution_id IS NULL AND lease_expires_at IS NULL
            AND effect_receipt_sha256 IS NULL
            AND finalized_at IS NULL AND diverged_at IS NOT NULL)
    ),
    CONSTRAINT git_mirror_push_lease CHECK (
        lease_fencing_token > 0
        AND updated_at >= created_at
        AND (lease_expires_at IS NULL OR lease_expires_at > created_at)
        AND (finalized_at IS NULL OR finalized_at >= created_at)
        AND (diverged_at IS NULL OR diverged_at >= created_at)
    )
);

CREATE UNIQUE INDEX git_mirror_push_active_reservation_idx
    ON hwpx_agent.git_mirror_push_effects (
        tenant_id, project_id, branch_id, expected_generation
    ) WHERE state = 'executing';

ALTER TABLE hwpx_agent.git_mirror_push_effects ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.git_mirror_push_effects FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.git_mirror_push_effects
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());

CREATE FUNCTION hwpx_agent.guard_git_mirror_push_effect_v1()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    IF TG_OP = 'DELETE' OR OLD.state IN ('finalized', 'diverged') THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'GIT_MIRROR_PUSH_IMMUTABLE';
    END IF;
    IF ROW(
        NEW.tenant_id, NEW.project_id, NEW.branch_id, NEW.mirror_id,
        NEW.push_id, NEW.subject_sha256, NEW.request_sha256, NEW.idempotency_sha256,
        NEW.expected_revision_id, NEW.expected_generation,
        NEW.expected_snapshot_sha256, NEW.source_artifact_id, NEW.result_revision_id,
        NEW.result_generation, NEW.result_snapshot_sha256, NEW.result_artifact_id,
        NEW.operation_plan_sha256, NEW.git_plan_sha256, NEW.git_plan_bytes,
        NEW.expected_git_oid, NEW.result_git_oid, NEW.git_state_sha256,
        NEW.validation_summary_sha256, NEW.transaction_receipt_sha256,
        NEW.commit_receipt_sha256, NEW.created_at
    ) IS DISTINCT FROM ROW(
        OLD.tenant_id, OLD.project_id, OLD.branch_id, OLD.mirror_id,
        OLD.push_id, OLD.subject_sha256, OLD.request_sha256, OLD.idempotency_sha256,
        OLD.expected_revision_id, OLD.expected_generation,
        OLD.expected_snapshot_sha256, OLD.source_artifact_id, OLD.result_revision_id,
        OLD.result_generation, OLD.result_snapshot_sha256, OLD.result_artifact_id,
        OLD.operation_plan_sha256, OLD.git_plan_sha256, OLD.git_plan_bytes,
        OLD.expected_git_oid, OLD.result_git_oid, OLD.git_state_sha256,
        OLD.validation_summary_sha256, OLD.transaction_receipt_sha256,
        OLD.commit_receipt_sha256, OLD.created_at
    ) OR NEW.lease_fencing_token < OLD.lease_fencing_token
       OR NEW.lease_fencing_token > OLD.lease_fencing_token + 1 THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'GIT_MIRROR_PUSH_PLAN_IMMUTABLE';
    END IF;
    RETURN NEW;
END
$$;

CREATE TRIGGER git_mirror_push_effect_guard
BEFORE UPDATE OR DELETE ON hwpx_agent.git_mirror_push_effects
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.guard_git_mirror_push_effect_v1();

CREATE FUNCTION hwpx_agent.guard_branch_git_mirror_push_v1()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
DECLARE
    v_push hwpx_agent.git_mirror_push_effects%ROWTYPE;
BEGIN
    IF ROW(NEW.head_revision_id, NEW.head_generation)
       IS NOT DISTINCT FROM ROW(OLD.head_revision_id, OLD.head_generation) THEN
        RETURN NEW;
    END IF;
    SELECT effect.* INTO v_push
    FROM hwpx_agent.git_mirror_push_effects AS effect
    WHERE effect.tenant_id = OLD.tenant_id
      AND effect.project_id = OLD.project_id
      AND effect.branch_id = OLD.branch_id
      AND effect.expected_revision_id IS NOT DISTINCT FROM OLD.head_revision_id
      AND effect.expected_generation = OLD.head_generation
      AND effect.state = 'executing';
    IF FOUND AND (
        current_setting('hwpx_agent.git_push_id', true) IS DISTINCT FROM v_push.push_id::text
        OR current_setting('hwpx_agent.git_push_fencing_token', true)
           IS DISTINCT FROM v_push.lease_fencing_token::text
        OR ROW(NEW.head_revision_id, NEW.head_generation)
           IS DISTINCT FROM ROW(v_push.result_revision_id, v_push.result_generation)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'GIT_MIRROR_PUSH_RESERVED';
    END IF;
    RETURN NEW;
END
$$;

CREATE TRIGGER branches_git_mirror_push_guard
BEFORE UPDATE OF head_revision_id, head_generation ON hwpx_agent.branches
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.guard_branch_git_mirror_push_v1();

CREATE OR REPLACE FUNCTION hwpx_agent.guard_idempotent_revision_commit_v2()
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
    v_git_effect hwpx_agent.git_mirror_push_effects%ROWTYPE;
    v_result_sha256 character(64);
    v_result_qualified boolean;
    v_presented_authorization_text text;
    v_presented_authorization_id uuid;
    v_presented_git_push_id text;
    v_presented_git_fencing text;
    v_now timestamptz := clock_timestamp();
BEGIN
    v_presented_git_push_id := current_setting('hwpx_agent.git_push_id', true);
    v_presented_git_fencing := current_setting(
        'hwpx_agent.git_push_fencing_token', true
    );
    IF v_presented_git_push_id ~
          '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
       AND v_presented_git_fencing ~ '^[1-9][0-9]{0,18}$' THEN
        SELECT effect.* INTO v_git_effect
        FROM hwpx_agent.git_mirror_push_effects AS effect
        WHERE effect.tenant_id = NEW.tenant_id
          AND effect.project_id = NEW.project_id
          AND effect.push_id = v_presented_git_push_id::uuid
          AND effect.push_id = NEW.commit_id
          AND effect.branch_id = NEW.branch_id
          AND effect.expected_revision_id IS NOT DISTINCT FROM NEW.previous_revision_id
          AND effect.expected_generation = NEW.expected_generation
          AND effect.result_revision_id = NEW.committed_revision_id
          AND effect.result_generation = NEW.committed_generation
          AND effect.request_sha256 = NEW.commit_request_sha256
          AND effect.transaction_receipt_sha256 = NEW.transaction_receipt_sha256
          AND effect.commit_receipt_sha256 = NEW.commit_receipt_sha256
          AND effect.subject_sha256 = NEW.subject_sha256
          AND effect.subject_sha256 = hwpx_agent.current_subject_sha256()
          AND effect.tenant_id = hwpx_agent.current_tenant_id()
          AND effect.state = 'executing'
          AND effect.lease_fencing_token = v_presented_git_fencing::bigint
          AND effect.lease_expires_at > v_now
        FOR SHARE;
        IF FOUND THEN
            RETURN NEW;
        END IF;
        RAISE EXCEPTION USING
            ERRCODE = '42501', MESSAGE = 'GIT_MIRROR_PUSH_COMMIT_FENCE_MISMATCH';
    END IF;

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

CREATE FUNCTION hwpx_agent.inspect_git_mirror_push_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_branch_id uuid,
    p_mirror_id uuid,
    p_push_id uuid,
    p_request_sha256 character(64),
    p_idempotency_sha256 character(64),
    p_expected_revision_id uuid,
    p_expected_generation bigint,
    p_result_revision_id uuid,
    p_result_snapshot_sha256 character(64),
    p_operation_plan_sha256 character(64)
)
RETURNS TABLE (
    outcome text,
    observed_revision_id uuid,
    observed_generation bigint,
    expected_snapshot_sha256 character(64),
    effect_state text,
    git_plan_bytes bytea,
    lease_execution_id uuid,
    lease_fencing_token bigint,
    lease_expires_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_effect hwpx_agent.git_mirror_push_effects%ROWTYPE;
    v_mirror hwpx_agent.project_local_mirrors%ROWTYPE;
    v_head_revision_id uuid;
    v_head_generation bigint;
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'GIT_MIRROR_PUSH_CONTEXT_MISMATCH';
    END IF;
    IF p_push_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_result_revision_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$'
       OR p_request_sha256 !~ '^[0-9a-f]{64}$'
       OR p_idempotency_sha256 !~ '^[0-9a-f]{64}$'
       OR p_result_snapshot_sha256 !~ '^[0-9a-f]{64}$'
       OR p_operation_plan_sha256 !~ '^[0-9a-f]{64}$'
       OR ((p_expected_revision_id IS NULL) <> (p_expected_generation = 0))
       OR p_expected_generation < 0 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'GIT_MIRROR_PUSH_REQUEST_INVALID';
    END IF;
    PERFORM 1 FROM hwpx_agent.projects
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND state = 'active'
    FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'GIT_MIRROR_PUSH_PROJECT_NOT_FOUND';
    END IF;
    PERFORM 1 FROM hwpx_agent.project_acl
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND subject_sha256 = p_subject_sha256 AND role IN ('editor', 'owner')
    FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'GIT_MIRROR_PUSH_DENIED';
    END IF;
    SELECT effect.* INTO v_effect
    FROM hwpx_agent.git_mirror_push_effects AS effect
    WHERE effect.tenant_id = p_tenant_id AND effect.project_id = p_project_id
      AND (effect.push_id = p_push_id OR effect.request_sha256 = p_request_sha256
        OR (effect.mirror_id = p_mirror_id
            AND effect.idempotency_sha256 = p_idempotency_sha256))
    FOR SHARE;
    IF FOUND THEN
        IF v_effect.push_id <> p_push_id OR v_effect.request_sha256 <> p_request_sha256
           OR v_effect.idempotency_sha256 <> p_idempotency_sha256
           OR v_effect.branch_id <> p_branch_id OR v_effect.mirror_id <> p_mirror_id
           OR v_effect.subject_sha256 <> p_subject_sha256
           OR v_effect.expected_revision_id IS DISTINCT FROM p_expected_revision_id
           OR v_effect.expected_generation <> p_expected_generation
           OR v_effect.result_revision_id <> p_result_revision_id
           OR v_effect.result_snapshot_sha256 <> p_result_snapshot_sha256
           OR v_effect.operation_plan_sha256 <> p_operation_plan_sha256 THEN
            RAISE EXCEPTION USING ERRCODE = '23505', MESSAGE = 'GIT_MIRROR_PUSH_IDEMPOTENCY_CONFLICT';
        END IF;
        RETURN QUERY SELECT
            'existing'::text, v_effect.result_revision_id, v_effect.result_generation,
            v_effect.expected_snapshot_sha256, v_effect.state, v_effect.git_plan_bytes,
            v_effect.lease_execution_id, v_effect.lease_fencing_token,
            v_effect.lease_expires_at;
        RETURN;
    END IF;
    SELECT mirror.* INTO v_mirror
    FROM hwpx_agent.project_local_mirrors AS mirror
    WHERE mirror.tenant_id = p_tenant_id AND mirror.project_id = p_project_id
      AND mirror.mirror_id = p_mirror_id
    FOR SHARE;
    IF NOT FOUND OR v_mirror.branch_id <> p_branch_id THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'GIT_MIRROR_PUSH_MIRROR_NOT_FOUND';
    END IF;
    SELECT branch.head_revision_id, branch.head_generation
    INTO v_head_revision_id, v_head_generation
    FROM hwpx_agent.branches AS branch
    WHERE branch.tenant_id = p_tenant_id AND branch.project_id = p_project_id
      AND branch.branch_id = p_branch_id
    FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'GIT_MIRROR_PUSH_BRANCH_NOT_FOUND';
    END IF;
    IF ROW(v_head_revision_id, v_head_generation)
       IS DISTINCT FROM ROW(p_expected_revision_id, p_expected_generation)
       OR ROW(v_mirror.observed_revision_id, v_mirror.observed_generation)
          IS DISTINCT FROM ROW(p_expected_revision_id, p_expected_generation)
       OR v_mirror.state <> 'clean' OR v_mirror.pending_plan_sha256 IS NOT NULL
       OR v_mirror.active_push_id IS NOT NULL THEN
        RETURN QUERY SELECT
            'conflict'::text, v_head_revision_id, v_head_generation,
            NULL::character(64), NULL::text, NULL::bytea,
            NULL::uuid, NULL::bigint, NULL::timestamptz;
        RETURN;
    END IF;
    RETURN QUERY SELECT
        'new'::text, v_head_revision_id, v_head_generation,
        v_mirror.snapshot_sha256, NULL::text, NULL::bytea,
        NULL::uuid, NULL::bigint, NULL::timestamptz;
END
$$;

CREATE FUNCTION hwpx_agent.store_git_mirror_push_plan_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_branch_id uuid,
    p_mirror_id uuid,
    p_push_id uuid,
    p_request_sha256 character(64),
    p_idempotency_sha256 character(64),
    p_expected_revision_id uuid,
    p_expected_generation bigint,
    p_expected_snapshot_sha256 character(64),
    p_result_revision_id uuid,
    p_result_snapshot_sha256 character(64),
    p_operation_plan_sha256 character(64),
    p_git_plan_sha256 character(64),
    p_git_plan_bytes bytea,
    p_expected_git_oid text,
    p_result_git_oid text,
    p_git_state_sha256 character(64),
    p_validation_summary_sha256 character(64),
    p_transaction_receipt_sha256 character(64),
    p_commit_receipt_sha256 character(64),
    p_execution_id uuid,
    p_lease_seconds integer
)
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_mirror hwpx_agent.project_local_mirrors%ROWTYPE;
    v_head_revision_id uuid;
    v_head_generation bigint;
    v_source_artifact_id uuid;
    v_result_artifact_id uuid;
    v_now timestamptz := clock_timestamp();
    v_expires timestamptz;
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'GIT_MIRROR_PUSH_CONTEXT_MISMATCH';
    END IF;
    IF p_execution_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_lease_seconds NOT BETWEEN 1 AND 300
       OR p_git_plan_sha256 <> encode(sha256(p_git_plan_bytes), 'hex') THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'GIT_MIRROR_PUSH_PLAN_INVALID';
    END IF;
    PERFORM 1 FROM hwpx_agent.project_acl
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND subject_sha256 = p_subject_sha256 AND role IN ('editor', 'owner')
    FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'GIT_MIRROR_PUSH_DENIED';
    END IF;
    SELECT mirror.* INTO v_mirror
    FROM hwpx_agent.project_local_mirrors AS mirror
    WHERE mirror.tenant_id = p_tenant_id AND mirror.project_id = p_project_id
      AND mirror.mirror_id = p_mirror_id
    FOR UPDATE;
    IF NOT FOUND OR v_mirror.branch_id <> p_branch_id
       OR v_mirror.state <> 'clean' OR v_mirror.pending_plan_sha256 IS NOT NULL
       OR v_mirror.active_push_id IS NOT NULL
       OR ROW(v_mirror.observed_revision_id, v_mirror.observed_generation)
          IS DISTINCT FROM ROW(p_expected_revision_id, p_expected_generation)
       OR v_mirror.snapshot_sha256 <> p_expected_snapshot_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = 'P1702', MESSAGE = 'GIT_MIRROR_PUSH_MIRROR_CONFLICT';
    END IF;
    SELECT branch.head_revision_id, branch.head_generation
    INTO v_head_revision_id, v_head_generation
    FROM hwpx_agent.branches AS branch
    WHERE branch.tenant_id = p_tenant_id AND branch.project_id = p_project_id
      AND branch.branch_id = p_branch_id
    FOR UPDATE;
    IF NOT FOUND OR ROW(v_head_revision_id, v_head_generation)
       IS DISTINCT FROM ROW(p_expected_revision_id, p_expected_generation) THEN
        RAISE EXCEPTION USING ERRCODE = 'P1702', MESSAGE = 'GIT_MIRROR_PUSH_HEAD_CONFLICT';
    END IF;
    SELECT artifact.artifact_id INTO v_source_artifact_id
    FROM hwpx_agent.artifacts AS artifact
    WHERE artifact.tenant_id = p_tenant_id
      AND artifact.content_sha256 = p_expected_snapshot_sha256
      AND artifact.artifact_kind IN ('source', 'result')
      AND artifact.storage_state = 'available' AND artifact.validation_state = 'verified'
      AND EXISTS (
        SELECT 1 FROM hwpx_agent.artifact_acl AS acl
        WHERE acl.tenant_id = artifact.tenant_id
          AND acl.artifact_id = artifact.artifact_id
          AND acl.subject_sha256 = p_subject_sha256
          AND (acl.can_read OR acl.can_manage)
      )
    FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'GIT_MIRROR_PUSH_SOURCE_UNAVAILABLE';
    END IF;
    SELECT artifact.artifact_id INTO v_result_artifact_id
    FROM hwpx_agent.artifacts AS artifact
    WHERE artifact.tenant_id = p_tenant_id
      AND artifact.content_sha256 = p_result_snapshot_sha256
      AND artifact.artifact_kind = 'result'
      AND artifact.storage_state = 'available' AND artifact.validation_state = 'verified'
      AND EXISTS (
        SELECT 1 FROM hwpx_agent.artifact_acl AS acl
        WHERE acl.tenant_id = artifact.tenant_id
          AND acl.artifact_id = artifact.artifact_id
          AND acl.subject_sha256 = p_subject_sha256
          AND (acl.can_read OR acl.can_manage)
      )
    FOR SHARE;
    IF NOT FOUND OR v_result_artifact_id = v_source_artifact_id THEN
        RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'GIT_MIRROR_PUSH_RESULT_UNAVAILABLE';
    END IF;
    v_expires := v_now + make_interval(secs => p_lease_seconds);
    INSERT INTO hwpx_agent.git_mirror_push_effects (
        tenant_id, project_id, branch_id, mirror_id, push_id, subject_sha256,
        request_sha256, idempotency_sha256, expected_revision_id, expected_generation,
        expected_snapshot_sha256, source_artifact_id, result_revision_id, result_generation,
        result_snapshot_sha256, result_artifact_id, operation_plan_sha256, git_plan_sha256,
        git_plan_bytes, expected_git_oid, result_git_oid, git_state_sha256,
        validation_summary_sha256, transaction_receipt_sha256,
        commit_receipt_sha256, state, lease_execution_id,
        lease_fencing_token, lease_expires_at, created_at, updated_at
    ) VALUES (
        p_tenant_id, p_project_id, p_branch_id, p_mirror_id, p_push_id,
        p_subject_sha256, p_request_sha256, p_idempotency_sha256, p_expected_revision_id,
        p_expected_generation, p_expected_snapshot_sha256, v_source_artifact_id,
        p_result_revision_id, p_expected_generation + 1, p_result_snapshot_sha256,
        v_result_artifact_id,
        p_operation_plan_sha256, p_git_plan_sha256, p_git_plan_bytes,
        p_expected_git_oid, p_result_git_oid, p_git_state_sha256,
        p_validation_summary_sha256, p_transaction_receipt_sha256,
        p_commit_receipt_sha256, 'executing', p_execution_id, 1,
        v_expires, v_now, v_now
    );
    UPDATE hwpx_agent.project_local_mirrors
    SET snapshot_sha256 = p_result_snapshot_sha256,
        pending_plan_sha256 = p_operation_plan_sha256,
        state = 'push_prepared', active_push_id = p_push_id,
        active_push_subject_sha256 = p_subject_sha256,
        active_push_expires_at = v_expires, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND mirror_id = p_mirror_id;
    RETURN 1;
END
$$;

CREATE FUNCTION hwpx_agent.acquire_git_mirror_push_lease_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_push_id uuid,
    p_request_sha256 character(64),
    p_execution_id uuid,
    p_lease_seconds integer
)
RETURNS TABLE (
    outcome text,
    git_plan_bytes bytea,
    lease_fencing_token bigint,
    result_revision_id uuid,
    result_generation bigint,
    result_snapshot_sha256 character(64)
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_effect hwpx_agent.git_mirror_push_effects%ROWTYPE;
    v_now timestamptz := clock_timestamp();
    v_expires timestamptz;
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'GIT_MIRROR_PUSH_CONTEXT_MISMATCH';
    END IF;
    IF p_execution_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_lease_seconds NOT BETWEEN 1 AND 300 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'GIT_MIRROR_PUSH_LEASE_INVALID';
    END IF;
    PERFORM 1 FROM hwpx_agent.project_acl
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND subject_sha256 = p_subject_sha256 AND role IN ('editor', 'owner')
    FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'GIT_MIRROR_PUSH_DENIED';
    END IF;
    SELECT effect.* INTO v_effect
    FROM hwpx_agent.git_mirror_push_effects AS effect
    WHERE effect.tenant_id = p_tenant_id AND effect.project_id = p_project_id
      AND effect.push_id = p_push_id AND effect.request_sha256 = p_request_sha256
      AND effect.subject_sha256 = p_subject_sha256
    FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'GIT_MIRROR_PUSH_NOT_FOUND';
    END IF;
    IF v_effect.state = 'finalized' THEN
        RETURN QUERY SELECT 'finalized'::text, v_effect.git_plan_bytes,
            v_effect.lease_fencing_token, v_effect.result_revision_id,
            v_effect.result_generation, v_effect.result_snapshot_sha256;
        RETURN;
    END IF;
    IF v_effect.state = 'diverged' THEN
        RETURN QUERY SELECT 'diverged'::text, v_effect.git_plan_bytes,
            v_effect.lease_fencing_token, v_effect.result_revision_id,
            v_effect.result_generation, v_effect.result_snapshot_sha256;
        RETURN;
    END IF;
    IF v_effect.lease_execution_id = p_execution_id
       AND v_effect.lease_expires_at > v_now THEN
        RETURN QUERY SELECT 'acquired'::text, v_effect.git_plan_bytes,
            v_effect.lease_fencing_token, v_effect.result_revision_id,
            v_effect.result_generation, v_effect.result_snapshot_sha256;
        RETURN;
    END IF;
    IF v_effect.lease_expires_at > v_now THEN
        RETURN QUERY SELECT 'busy'::text, NULL::bytea,
            v_effect.lease_fencing_token, v_effect.result_revision_id,
            v_effect.result_generation, v_effect.result_snapshot_sha256;
        RETURN;
    END IF;
    v_expires := v_now + make_interval(secs => p_lease_seconds);
    UPDATE hwpx_agent.git_mirror_push_effects AS effect
    SET lease_execution_id = p_execution_id,
        lease_fencing_token = effect.lease_fencing_token + 1,
        lease_expires_at = v_expires, updated_at = v_now
    WHERE effect.tenant_id = p_tenant_id AND effect.project_id = p_project_id
      AND effect.push_id = p_push_id
    RETURNING effect.* INTO v_effect;
    UPDATE hwpx_agent.project_local_mirrors
    SET active_push_expires_at = v_expires, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND mirror_id = v_effect.mirror_id AND state = 'push_prepared'
      AND active_push_id = p_push_id
      AND active_push_subject_sha256 = p_subject_sha256;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'GIT_MIRROR_PUSH_MIRROR_DRIFT';
    END IF;
    RETURN QUERY SELECT 'acquired'::text, v_effect.git_plan_bytes,
        v_effect.lease_fencing_token, v_effect.result_revision_id,
        v_effect.result_generation, v_effect.result_snapshot_sha256;
END
$$;

CREATE FUNCTION hwpx_agent.mark_git_mirror_push_diverged_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_push_id uuid,
    p_request_sha256 character(64),
    p_execution_id uuid,
    p_fencing_token bigint
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_effect hwpx_agent.git_mirror_push_effects%ROWTYPE;
    v_now timestamptz := clock_timestamp();
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'GIT_MIRROR_PUSH_CONTEXT_MISMATCH';
    END IF;
    SELECT effect.* INTO v_effect
    FROM hwpx_agent.git_mirror_push_effects AS effect
    WHERE effect.tenant_id = p_tenant_id AND effect.project_id = p_project_id
      AND effect.push_id = p_push_id AND effect.request_sha256 = p_request_sha256
    FOR UPDATE;
    IF NOT FOUND OR v_effect.subject_sha256 <> p_subject_sha256
       OR v_effect.state <> 'executing'
       OR v_effect.lease_execution_id <> p_execution_id
       OR v_effect.lease_fencing_token <> p_fencing_token
       OR v_effect.lease_expires_at <= v_now THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'GIT_MIRROR_PUSH_LEASE_STALE';
    END IF;
    UPDATE hwpx_agent.git_mirror_push_effects
    SET state = 'diverged', lease_execution_id = NULL,
        lease_expires_at = NULL, diverged_at = v_now, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND push_id = p_push_id;
    UPDATE hwpx_agent.project_local_mirrors
    SET state = 'manual_merge_required', active_push_id = NULL,
        active_push_subject_sha256 = NULL, active_push_expires_at = NULL,
        updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND mirror_id = v_effect.mirror_id AND state = 'push_prepared'
      AND active_push_id = p_push_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'GIT_MIRROR_PUSH_MIRROR_DRIFT';
    END IF;
END
$$;

CREATE FUNCTION hwpx_agent.finalize_git_mirror_push_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_push_id uuid,
    p_request_sha256 character(64),
    p_execution_id uuid,
    p_fencing_token bigint,
    p_git_plan_sha256 character(64),
    p_effect_receipt_sha256 character(64)
)
RETURNS TABLE (
    outcome text,
    revision_id uuid,
    generation bigint,
    snapshot_sha256 character(64)
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_effect hwpx_agent.git_mirror_push_effects%ROWTYPE;
    v_commit record;
    v_now timestamptz := clock_timestamp();
    v_parents uuid[];
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'GIT_MIRROR_PUSH_CONTEXT_MISMATCH';
    END IF;
    IF p_effect_receipt_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'GIT_MIRROR_PUSH_RECEIPT_INVALID';
    END IF;
    SELECT effect.* INTO v_effect
    FROM hwpx_agent.git_mirror_push_effects AS effect
    WHERE effect.tenant_id = p_tenant_id AND effect.project_id = p_project_id
      AND effect.push_id = p_push_id AND effect.request_sha256 = p_request_sha256
    FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'GIT_MIRROR_PUSH_NOT_FOUND';
    END IF;
    IF v_effect.state = 'finalized' THEN
        IF v_effect.git_plan_sha256 <> p_git_plan_sha256
           OR v_effect.effect_receipt_sha256 <> p_effect_receipt_sha256 THEN
            RAISE EXCEPTION USING ERRCODE = '23505', MESSAGE = 'GIT_MIRROR_PUSH_RECEIPT_CONFLICT';
        END IF;
        RETURN QUERY SELECT 'replayed'::text, v_effect.result_revision_id,
            v_effect.result_generation, v_effect.result_snapshot_sha256;
        RETURN;
    END IF;
    IF v_effect.subject_sha256 <> p_subject_sha256
       OR v_effect.state <> 'executing'
       OR v_effect.lease_execution_id <> p_execution_id
       OR v_effect.lease_fencing_token <> p_fencing_token
       OR v_effect.lease_expires_at <= v_now
       OR v_effect.git_plan_sha256 <> p_git_plan_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'GIT_MIRROR_PUSH_LEASE_STALE';
    END IF;
    PERFORM set_config('hwpx_agent.git_push_id', p_push_id::text, true);
    PERFORM set_config('hwpx_agent.git_push_fencing_token', p_fencing_token::text, true);
    v_parents := CASE WHEN v_effect.expected_revision_id IS NULL
        THEN ARRAY[]::uuid[] ELSE ARRAY[v_effect.expected_revision_id] END;
    SELECT * INTO v_commit
    FROM hwpx_agent.commit_revision_cas(
        p_tenant_id, p_project_id, v_effect.branch_id, p_subject_sha256,
        p_push_id, v_effect.expected_revision_id, v_effect.expected_generation,
        v_effect.result_revision_id, v_parents, v_effect.source_artifact_id,
        v_effect.result_artifact_id, NULL,
        v_effect.operation_plan_sha256, 'verified',
        v_effect.validation_summary_sha256,
        v_effect.transaction_receipt_sha256, v_effect.request_sha256,
        v_effect.commit_receipt_sha256
    );
    IF v_commit.outcome <> 'committed'
       OR v_commit.committed_revision_id <> v_effect.result_revision_id
       OR v_commit.committed_generation <> v_effect.result_generation THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'GIT_MIRROR_PUSH_DATABASE_CONFLICT';
    END IF;
    UPDATE hwpx_agent.project_local_mirrors
    SET observed_revision_id = v_effect.result_revision_id,
        observed_generation = v_effect.result_generation,
        snapshot_sha256 = v_effect.result_snapshot_sha256,
        pending_plan_sha256 = NULL, state = 'clean', active_push_id = NULL,
        active_push_subject_sha256 = NULL, active_push_expires_at = NULL,
        updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND mirror_id = v_effect.mirror_id AND branch_id = v_effect.branch_id
      AND state = 'push_prepared' AND active_push_id = p_push_id
      AND active_push_subject_sha256 = p_subject_sha256
      AND pending_plan_sha256 = v_effect.operation_plan_sha256;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'GIT_MIRROR_PUSH_MIRROR_DRIFT';
    END IF;
    UPDATE hwpx_agent.git_mirror_push_effects
    SET state = 'finalized', lease_execution_id = NULL,
        lease_expires_at = NULL, effect_receipt_sha256 = p_effect_receipt_sha256,
        finalized_at = v_now, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND push_id = p_push_id;
    RETURN QUERY SELECT 'committed'::text, v_effect.result_revision_id,
        v_effect.result_generation, v_effect.result_snapshot_sha256;
END
$$;

REVOKE ALL ON TABLE hwpx_agent.git_mirror_push_effects FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.guard_git_mirror_push_effect_v1() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.guard_branch_git_mirror_push_v1() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.inspect_git_mirror_push_v1(
    uuid, uuid, character, uuid, uuid, uuid, character, character, uuid, bigint,
    uuid, character, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.store_git_mirror_push_plan_v1(
    uuid, uuid, character, uuid, uuid, uuid, character, character, uuid, bigint,
    character, uuid, character, character, character, bytea, text, text,
    character, character, character, character, uuid, integer
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.acquire_git_mirror_push_lease_v1(
    uuid, uuid, character, uuid, character, uuid, integer
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.mark_git_mirror_push_diverged_v1(
    uuid, uuid, character, uuid, character, uuid, bigint
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.finalize_git_mirror_push_v1(
    uuid, uuid, character, uuid, character, uuid, bigint, character, character
) FROM PUBLIC;

INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (16, 'p17.durable_git_mirror_push_v1',
        current_setting('hwpx_agent.migration_sha256'));

COMMIT;
