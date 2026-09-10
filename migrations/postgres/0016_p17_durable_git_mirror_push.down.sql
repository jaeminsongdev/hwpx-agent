BEGIN;

DO $$
BEGIN
    IF current_setting(
        'hwpx_agent.allow_p17_durable_git_mirror_push_rollback', true
    ) IS DISTINCT FROM 'yes'
       OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 16 AND migration_name = 'p17.durable_git_mirror_push_v1'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P17 durable Git mirror push rollback requires an explicit gate and exact version 16';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version > 16) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P17 durable Git mirror push rollback requires later migrations removed first';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.git_mirror_push_effects) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P17 durable Git mirror push rollback refuses retained effects';
    END IF;
END
$$;

DROP FUNCTION hwpx_agent.finalize_git_mirror_push_v1(
    uuid, uuid, character, uuid, character, uuid, bigint, character, character
);
DROP FUNCTION hwpx_agent.mark_git_mirror_push_diverged_v1(
    uuid, uuid, character, uuid, character, uuid, bigint
);
DROP FUNCTION hwpx_agent.acquire_git_mirror_push_lease_v1(
    uuid, uuid, character, uuid, character, uuid, integer
);
DROP FUNCTION hwpx_agent.store_git_mirror_push_plan_v1(
    uuid, uuid, character, uuid, uuid, uuid, character, character, uuid, bigint,
    character, uuid, character, character, character, bytea, text, text,
    character, character, character, character, uuid, integer
);
DROP FUNCTION hwpx_agent.inspect_git_mirror_push_v1(
    uuid, uuid, character, uuid, uuid, uuid, character, character, uuid, bigint,
    uuid, character, character
);
DROP TRIGGER branches_git_mirror_push_guard ON hwpx_agent.branches;
DROP FUNCTION hwpx_agent.guard_branch_git_mirror_push_v1();
DROP TRIGGER git_mirror_push_effect_guard ON hwpx_agent.git_mirror_push_effects;
DROP FUNCTION hwpx_agent.guard_git_mirror_push_effect_v1();

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

DROP TABLE hwpx_agent.git_mirror_push_effects;

ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions
WHERE version = 16 AND migration_name = 'p17.durable_git_mirror_push_v1';
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;

COMMIT;
