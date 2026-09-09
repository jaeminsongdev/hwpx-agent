BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 14 AND migration_name = 'p17.history_checkpoint_note_v2'
    ) OR EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version >= 15) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P17 atomic mirror checkpoint requires exact schema version 14';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256', true) IS NULL
       OR current_setting('hwpx_agent.migration_sha256', true) !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            MESSAGE = 'P17 atomic mirror checkpoint requires its migration digest';
    END IF;
END
$$;

CREATE FUNCTION hwpx_agent.create_mirror_history_checkpoint_v3(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_branch_id uuid,
    p_mirror_id uuid,
    p_expected_revision_id uuid,
    p_expected_generation bigint,
    p_request_id uuid,
    p_request_sha256 character(64),
    p_checkpoint_id uuid,
    p_revision_id uuid,
    p_label text,
    p_note text
)
RETURNS TABLE (
    outcome text,
    checkpoint_id uuid,
    revision_id uuid,
    label text,
    note text,
    request_sha256 character(64)
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_mirror hwpx_agent.project_local_mirrors%ROWTYPE;
    v_head_revision_id uuid;
    v_head_generation bigint;
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'MIRROR_CONTEXT_MISMATCH';
    END IF;
    IF p_tenant_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_project_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_branch_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_mirror_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_expected_revision_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_revision_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_expected_generation <= 0
       OR p_expected_revision_id IS DISTINCT FROM p_revision_id
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'MIRROR_CHECKPOINT_INVALID';
    END IF;

    PERFORM 1
    FROM hwpx_agent.projects
    WHERE tenant_id = p_tenant_id
      AND project_id = p_project_id
      AND state = 'active'
    FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'MIRROR_PROJECT_NOT_FOUND';
    END IF;

    PERFORM 1
    FROM hwpx_agent.project_acl
    WHERE tenant_id = p_tenant_id
      AND project_id = p_project_id
      AND subject_sha256 = p_subject_sha256
      AND role IN ('editor', 'owner')
    FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'MIRROR_CHECKPOINT_DENIED';
    END IF;

    SELECT mirror.* INTO v_mirror
    FROM hwpx_agent.project_local_mirrors AS mirror
    WHERE mirror.tenant_id = p_tenant_id
      AND mirror.project_id = p_project_id
      AND mirror.mirror_id = p_mirror_id
    FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'MIRROR_NOT_FOUND';
    END IF;
    IF v_mirror.branch_id <> p_branch_id
       OR v_mirror.state <> 'clean'
       OR v_mirror.pending_plan_sha256 IS NOT NULL
       OR v_mirror.active_push_id IS NOT NULL
       OR v_mirror.active_push_subject_sha256 IS NOT NULL
       OR v_mirror.active_push_expires_at IS NOT NULL
       OR ROW(v_mirror.observed_revision_id, v_mirror.observed_generation)
          IS DISTINCT FROM ROW(p_expected_revision_id, p_expected_generation) THEN
        RAISE EXCEPTION USING ERRCODE = 'P1702', MESSAGE = 'MIRROR_CHECKPOINT_CONFLICT';
    END IF;

    SELECT branch.head_revision_id, branch.head_generation
    INTO v_head_revision_id, v_head_generation
    FROM hwpx_agent.branches AS branch
    WHERE branch.tenant_id = p_tenant_id
      AND branch.project_id = p_project_id
      AND branch.branch_id = p_branch_id
    FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'MIRROR_BRANCH_NOT_FOUND';
    END IF;
    IF ROW(v_head_revision_id, v_head_generation)
       IS DISTINCT FROM ROW(p_expected_revision_id, p_expected_generation) THEN
        RAISE EXCEPTION USING ERRCODE = 'P1702', MESSAGE = 'MIRROR_HEAD_CONFLICT';
    END IF;

    RETURN QUERY
    SELECT result.outcome, result.checkpoint_id, result.revision_id,
           result.label, result.note, result.request_sha256
    FROM hwpx_agent.create_history_checkpoint_v2(
        p_tenant_id, p_project_id, p_subject_sha256, p_request_id,
        p_request_sha256, p_checkpoint_id, p_revision_id, p_label, p_note
    ) AS result;
END
$$;

REVOKE ALL ON FUNCTION hwpx_agent.create_mirror_history_checkpoint_v3(
    uuid, uuid, character, uuid, uuid, uuid, bigint,
    uuid, character, uuid, uuid, text, text
) FROM PUBLIC;

INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (15, 'p17.atomic_mirror_checkpoint_v3',
        current_setting('hwpx_agent.migration_sha256'));

COMMIT;
