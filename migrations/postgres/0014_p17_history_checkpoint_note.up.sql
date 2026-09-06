BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 13 AND migration_name = 'p16.plan_review_evidence_v1'
    ) OR EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version >= 14) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P17 history checkpoint note requires exact schema version 13';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256', true) IS NULL
       OR current_setting('hwpx_agent.migration_sha256', true) !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            MESSAGE = 'P17 history checkpoint note requires its migration digest';
    END IF;
END
$$;

ALTER TABLE hwpx_agent.history_checkpoint_requests
    ADD COLUMN note text;
ALTER TABLE hwpx_agent.history_checkpoint_requests
    ADD CONSTRAINT history_checkpoint_requests_note_format CHECK (
        note IS NULL OR char_length(note) BETWEEN 1 AND 1000
    );

ALTER TABLE hwpx_agent.checkpoints
    ADD COLUMN note text;
ALTER TABLE hwpx_agent.checkpoints
    ADD CONSTRAINT checkpoints_note_format CHECK (
        note IS NULL OR char_length(note) BETWEEN 1 AND 1000
    );

CREATE FUNCTION hwpx_agent.create_history_checkpoint_v2(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
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
    v_claim hwpx_agent.history_checkpoint_requests%ROWTYPE;
    v_checkpoint hwpx_agent.checkpoints%ROWTYPE;
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'HISTORY_CONTEXT_MISMATCH';
    END IF;
    IF p_tenant_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_project_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_request_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_checkpoint_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_revision_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$'
       OR p_request_sha256 !~ '^[0-9a-f]{64}$'
       OR char_length(p_label) NOT BETWEEN 1 AND 120
       OR p_label <> btrim(p_label)
       OR p_label ~ '[[:cntrl:]]'
       OR (p_note IS NOT NULL AND char_length(p_note) NOT BETWEEN 1 AND 1000) THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'HISTORY_CHECKPOINT_REQUEST_INVALID';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.projects
        WHERE tenant_id = p_tenant_id
          AND project_id = p_project_id
          AND state = 'active'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'HISTORY_PROJECT_NOT_FOUND';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.project_acl
        WHERE tenant_id = p_tenant_id
          AND project_id = p_project_id
          AND subject_sha256 = p_subject_sha256
          AND role IN ('editor', 'owner')
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'HISTORY_CHECKPOINT_DENIED';
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
          AND revision.revision_id = p_revision_id
          AND seal.seal_kind = 'service_v1'
          AND seal.committed_generation > 0
    ) THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'HISTORY_REVISION_NOT_QUALIFIED';
    END IF;

    INSERT INTO hwpx_agent.history_checkpoint_requests (
        tenant_id, project_id, request_id, request_sha256, checkpoint_id,
        revision_id, label, note, subject_sha256
    ) VALUES (
        p_tenant_id, p_project_id, p_request_id, p_request_sha256, p_checkpoint_id,
        p_revision_id, p_label, p_note, p_subject_sha256
    )
    ON CONFLICT (tenant_id, project_id, request_id) DO NOTHING;

    SELECT * INTO STRICT v_claim
    FROM hwpx_agent.history_checkpoint_requests
    WHERE tenant_id = p_tenant_id
      AND project_id = p_project_id
      AND request_id = p_request_id;

    IF ROW(
        v_claim.request_sha256, v_claim.checkpoint_id, v_claim.revision_id,
        v_claim.label, v_claim.note, v_claim.subject_sha256
    ) IS DISTINCT FROM ROW(
        p_request_sha256, p_checkpoint_id, p_revision_id,
        p_label, p_note, p_subject_sha256
    ) THEN
        RAISE EXCEPTION USING ERRCODE = 'P1701', MESSAGE = 'HISTORY_IDEMPOTENCY_CONFLICT';
    END IF;

    SELECT checkpoint.* INTO v_checkpoint
    FROM hwpx_agent.checkpoints AS checkpoint
    WHERE checkpoint.tenant_id = p_tenant_id
      AND checkpoint.project_id = p_project_id
      AND checkpoint.checkpoint_id = p_checkpoint_id;
    IF FOUND THEN
        IF ROW(
            v_checkpoint.revision_id, v_checkpoint.label, v_checkpoint.note,
            v_checkpoint.created_by_subject_sha256
        ) IS DISTINCT FROM ROW(
            p_revision_id, p_label, p_note, p_subject_sha256
        ) THEN
            RAISE EXCEPTION USING
                ERRCODE = '55000', MESSAGE = 'HISTORY_CHECKPOINT_STATE_MISMATCH';
        END IF;
        IF (
            SELECT count(*) FROM hwpx_agent.audit_events AS audit
            WHERE audit.tenant_id = p_tenant_id
              AND audit.project_id = p_project_id
              AND audit.event_type = 'history.checkpoint_created'
              AND audit.subject_sha256 = p_subject_sha256
              AND audit.revision_id = p_revision_id
              AND audit.payload_sha256 = p_request_sha256
        ) <> 1 THEN
            RAISE EXCEPTION USING
                ERRCODE = '55000', MESSAGE = 'HISTORY_CHECKPOINT_AUDIT_MISMATCH';
        END IF;
        RETURN QUERY SELECT
            'replayed'::text, v_checkpoint.checkpoint_id, v_checkpoint.revision_id,
            v_checkpoint.label, v_checkpoint.note, v_claim.request_sha256;
        RETURN;
    END IF;

    INSERT INTO hwpx_agent.checkpoints (
        tenant_id, project_id, checkpoint_id, revision_id, label, note,
        created_by_subject_sha256
    ) VALUES (
        p_tenant_id, p_project_id, p_checkpoint_id, p_revision_id, p_label, p_note,
        p_subject_sha256
    );
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, revision_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'history.checkpoint_created', p_subject_sha256,
        p_revision_id, p_request_sha256
    );
    RETURN QUERY SELECT
        'created'::text, p_checkpoint_id, p_revision_id, p_label, p_note,
        p_request_sha256;
END
$$;

REVOKE ALL ON FUNCTION hwpx_agent.create_history_checkpoint_v2(
    uuid, uuid, character, uuid, character, uuid, uuid, text, text
) FROM PUBLIC;

INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (14, 'p17.history_checkpoint_note_v2', current_setting('hwpx_agent.migration_sha256'));

COMMIT;
