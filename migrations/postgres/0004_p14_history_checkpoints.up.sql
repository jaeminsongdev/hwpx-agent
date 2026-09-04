BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 3 AND migration_name = 'p14.revision_cas_v1'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 history migration requires p14.revision_cas_v1';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version = 4) THEN
        RAISE EXCEPTION USING
            ERRCODE = '42710',
            MESSAGE = 'P14 history migration version 4 already exists';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256', true)
        !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            MESSAGE = 'P14 history migration requires its exact SHA-256';
    END IF;
END
$$;

CREATE TABLE hwpx_agent.history_checkpoint_requests (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    request_id uuid NOT NULL,
    request_sha256 character(64) NOT NULL,
    checkpoint_id uuid NOT NULL,
    revision_id uuid NOT NULL,
    label text NOT NULL,
    subject_sha256 character(64) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, project_id, request_id),
    UNIQUE (tenant_id, project_id, checkpoint_id),
    UNIQUE (tenant_id, project_id, label),
    CONSTRAINT history_checkpoint_requests_project_fk FOREIGN KEY (tenant_id, project_id)
        REFERENCES hwpx_agent.projects (tenant_id, project_id) ON DELETE RESTRICT,
    CONSTRAINT history_checkpoint_requests_revision_fk FOREIGN KEY (
        tenant_id, project_id, revision_id
    ) REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id)
        ON DELETE RESTRICT,
    CONSTRAINT history_checkpoint_requests_digest_format CHECK (
        request_sha256 ~ '^[0-9a-f]{64}$'
        AND subject_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT history_checkpoint_requests_label_format CHECK (
        char_length(label) BETWEEN 1 AND 120
        AND label = btrim(label)
        AND label !~ '[[:cntrl:]]'
    )
);

CREATE TRIGGER history_checkpoint_requests_immutable
BEFORE UPDATE OR DELETE ON hwpx_agent.history_checkpoint_requests
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();

CREATE INDEX revision_graph_seals_history_order_idx
    ON hwpx_agent.revision_graph_seals (
        tenant_id, project_id, committed_generation DESC, revision_id
    ) WHERE seal_kind = 'service_v1';

CREATE FUNCTION hwpx_agent.create_history_checkpoint(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_request_id uuid,
    p_request_sha256 character(64),
    p_checkpoint_id uuid,
    p_revision_id uuid,
    p_label text
)
RETURNS TABLE (
    outcome text,
    checkpoint_id uuid,
    revision_id uuid,
    label text,
    request_sha256 character(64)
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_claim hwpx_agent.history_checkpoint_requests%ROWTYPE;
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
       OR p_label ~ '[[:cntrl:]]' THEN
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
        revision_id, label, subject_sha256
    ) VALUES (
        p_tenant_id, p_project_id, p_request_id, p_request_sha256, p_checkpoint_id,
        p_revision_id, p_label, p_subject_sha256
    )
    ON CONFLICT (tenant_id, project_id, request_id) DO NOTHING;

    SELECT * INTO STRICT v_claim
    FROM hwpx_agent.history_checkpoint_requests
    WHERE tenant_id = p_tenant_id
      AND project_id = p_project_id
      AND request_id = p_request_id;

    IF ROW(
        v_claim.request_sha256, v_claim.checkpoint_id, v_claim.revision_id,
        v_claim.label, v_claim.subject_sha256
    ) IS DISTINCT FROM ROW(
        p_request_sha256, p_checkpoint_id, p_revision_id, p_label, p_subject_sha256
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'HISTORY_IDEMPOTENCY_CONFLICT';
    END IF;

    IF EXISTS (
        SELECT 1 FROM hwpx_agent.checkpoints AS checkpoint
        WHERE checkpoint.tenant_id = p_tenant_id
          AND checkpoint.project_id = p_project_id
          AND checkpoint.checkpoint_id = p_checkpoint_id
    ) THEN
        RETURN QUERY SELECT
            'replayed'::text, p_checkpoint_id, p_revision_id, p_label,
            p_request_sha256;
        RETURN;
    END IF;

    INSERT INTO hwpx_agent.checkpoints (
        tenant_id, project_id, checkpoint_id, revision_id, label,
        created_by_subject_sha256
    ) VALUES (
        p_tenant_id, p_project_id, p_checkpoint_id, p_revision_id, p_label,
        p_subject_sha256
    );
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, revision_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'history.checkpoint_created', p_subject_sha256,
        p_revision_id, p_request_sha256
    );
    RETURN QUERY SELECT
        'created'::text, p_checkpoint_id, p_revision_id, p_label,
        p_request_sha256;
END
$$;

CREATE FUNCTION hwpx_agent.create_history_branch(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_branch_id uuid,
    p_name text,
    p_revision_id uuid,
    p_request_sha256 character(64)
)
RETURNS TABLE (
    branch_id uuid,
    name text,
    head_revision_id uuid,
    head_generation bigint
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_generation bigint;
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'HISTORY_CONTEXT_MISMATCH';
    END IF;
    IF p_tenant_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_project_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_branch_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_revision_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$'
       OR p_request_sha256 !~ '^[0-9a-f]{64}$'
       OR p_name !~ '^[A-Za-z0-9][A-Za-z0-9._/-]{0,126}$'
       OR p_name ~ '(^|/)\.\.?($|/)'
       OR p_name ~ '//' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'HISTORY_BRANCH_REQUEST_INVALID';
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
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'HISTORY_BRANCH_DENIED';
    END IF;

    SELECT seal.committed_generation INTO v_generation
    FROM hwpx_agent.revisions AS revision
    JOIN hwpx_agent.revision_graph_seals AS seal
      ON seal.tenant_id = revision.tenant_id
     AND seal.project_id = revision.project_id
     AND seal.revision_id = revision.revision_id
    WHERE revision.tenant_id = p_tenant_id
      AND revision.project_id = p_project_id
      AND revision.revision_id = p_revision_id
      AND seal.seal_kind = 'service_v1'
      AND seal.committed_generation > 0;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'HISTORY_REVISION_NOT_QUALIFIED';
    END IF;

    INSERT INTO hwpx_agent.branches (
        tenant_id, project_id, branch_id, name, head_revision_id, head_generation,
        is_default, created_by_subject_sha256
    ) VALUES (
        p_tenant_id, p_project_id, p_branch_id, p_name, p_revision_id, v_generation,
        false, p_subject_sha256
    );
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, revision_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'history.branch_created', p_subject_sha256,
        p_revision_id, p_request_sha256
    );
    RETURN QUERY SELECT p_branch_id, p_name, p_revision_id, v_generation;
END
$$;

CREATE FUNCTION hwpx_agent.query_revision_history(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_snapshot_revision_id uuid,
    p_snapshot_generation bigint,
    p_after_generation bigint,
    p_after_revision_id uuid,
    p_limit integer
)
RETURNS TABLE (
    revision_id uuid,
    parent_revision_ids uuid[],
    result_artifact_id uuid,
    semantic_diff_artifact_id uuid,
    committed_generation bigint,
    checkpoint_labels text[]
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_reachable_count bigint;
    v_qualified_count bigint;
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'HISTORY_CONTEXT_MISMATCH';
    END IF;
    IF p_tenant_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_project_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_snapshot_revision_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$'
       OR p_snapshot_generation <= 0
       OR p_limit NOT BETWEEN 1 AND 100
       OR ((p_after_generation IS NULL) <> (p_after_revision_id IS NULL))
       OR (p_after_generation IS NOT NULL AND p_after_generation <= 0) THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'HISTORY_QUERY_INVALID';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.projects
        WHERE tenant_id = p_tenant_id
          AND project_id = p_project_id
          AND state = 'active'
    ) OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.project_acl
        WHERE tenant_id = p_tenant_id
          AND project_id = p_project_id
          AND subject_sha256 = p_subject_sha256
          AND role IN ('reader', 'editor', 'owner')
    ) THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'HISTORY_PROJECT_NOT_FOUND';
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
          AND revision.revision_id = p_snapshot_revision_id
          AND seal.seal_kind = 'service_v1'
          AND seal.committed_generation = p_snapshot_generation
    ) THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'HISTORY_SNAPSHOT_NOT_QUALIFIED';
    END IF;

    WITH RECURSIVE reachable(revision_id) AS (
        SELECT p_snapshot_revision_id
        UNION
        SELECT parent.parent_revision_id
        FROM hwpx_agent.revision_parents AS parent
        JOIN reachable
          ON parent.tenant_id = p_tenant_id
         AND parent.project_id = p_project_id
         AND parent.revision_id = reachable.revision_id
    ), bounded AS (
        SELECT reachable.revision_id
        FROM reachable
        LIMIT 10001
    )
    SELECT
        count(*),
        count(seal.revision_id)
    INTO v_reachable_count, v_qualified_count
    FROM bounded
    LEFT JOIN hwpx_agent.revision_graph_seals AS seal
      ON seal.tenant_id = p_tenant_id
     AND seal.project_id = p_project_id
     AND seal.revision_id = bounded.revision_id
     AND seal.seal_kind = 'service_v1'
     AND seal.committed_generation > 0;
    IF v_reachable_count > 10000 THEN
        RAISE EXCEPTION USING ERRCODE = '54000', MESSAGE = 'HISTORY_GRAPH_LIMIT_EXCEEDED';
    END IF;
    IF v_qualified_count <> v_reachable_count THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'HISTORY_LEGACY_REVISION_UNQUALIFIED';
    END IF;
    IF EXISTS (
        WITH RECURSIVE reachable(revision_id) AS (
            SELECT p_snapshot_revision_id
            UNION
            SELECT parent.parent_revision_id
            FROM hwpx_agent.revision_parents AS parent
            JOIN reachable
              ON parent.tenant_id = p_tenant_id
             AND parent.project_id = p_project_id
             AND parent.revision_id = reachable.revision_id
        )
        SELECT 1
        FROM reachable
        JOIN hwpx_agent.revision_parents AS edge
          ON edge.tenant_id = p_tenant_id
         AND edge.project_id = p_project_id
         AND edge.revision_id = reachable.revision_id
        JOIN hwpx_agent.revision_graph_seals AS child_seal
          ON child_seal.tenant_id = edge.tenant_id
         AND child_seal.project_id = edge.project_id
         AND child_seal.revision_id = edge.revision_id
         AND child_seal.seal_kind = 'service_v1'
        JOIN hwpx_agent.revision_graph_seals AS parent_seal
          ON parent_seal.tenant_id = edge.tenant_id
         AND parent_seal.project_id = edge.project_id
         AND parent_seal.revision_id = edge.parent_revision_id
         AND parent_seal.seal_kind = 'service_v1'
        WHERE parent_seal.committed_generation >= child_seal.committed_generation
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'HISTORY_GRAPH_GENERATION_INVALID';
    END IF;

    RETURN QUERY
    WITH RECURSIVE reachable(revision_id) AS (
        SELECT p_snapshot_revision_id
        UNION
        SELECT parent.parent_revision_id
        FROM hwpx_agent.revision_parents AS parent
        JOIN reachable
          ON parent.tenant_id = p_tenant_id
         AND parent.project_id = p_project_id
         AND parent.revision_id = reachable.revision_id
    )
    SELECT
        revision.revision_id,
        COALESCE((
            SELECT array_agg(parent.parent_revision_id ORDER BY parent.parent_ordinal)
            FROM hwpx_agent.revision_parents AS parent
            WHERE parent.tenant_id = p_tenant_id
              AND parent.project_id = p_project_id
              AND parent.revision_id = revision.revision_id
        ), ARRAY[]::uuid[]) AS parent_revision_ids,
        revision.result_artifact_id,
        revision.semantic_diff_artifact_id,
        seal.committed_generation,
        COALESCE((
            SELECT array_agg(checkpoint.label ORDER BY checkpoint.label COLLATE "C")
            FROM hwpx_agent.checkpoints AS checkpoint
            WHERE checkpoint.tenant_id = p_tenant_id
              AND checkpoint.project_id = p_project_id
              AND checkpoint.revision_id = revision.revision_id
        ), ARRAY[]::text[]) AS checkpoint_labels
    FROM reachable
    JOIN hwpx_agent.revisions AS revision
      ON revision.tenant_id = p_tenant_id
     AND revision.project_id = p_project_id
     AND revision.revision_id = reachable.revision_id
    JOIN hwpx_agent.revision_graph_seals AS seal
      ON seal.tenant_id = revision.tenant_id
     AND seal.project_id = revision.project_id
     AND seal.revision_id = revision.revision_id
     AND seal.seal_kind = 'service_v1'
     AND seal.committed_generation > 0
    WHERE p_after_generation IS NULL
       OR seal.committed_generation < p_after_generation
       OR (
            seal.committed_generation = p_after_generation
            AND revision.revision_id > p_after_revision_id
       )
    ORDER BY seal.committed_generation DESC, revision.revision_id
    LIMIT p_limit;
END
$$;

ALTER TABLE hwpx_agent.history_checkpoint_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.history_checkpoint_requests FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.history_checkpoint_requests
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());

REVOKE ALL ON TABLE hwpx_agent.history_checkpoint_requests FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.create_history_checkpoint(
    uuid, uuid, character, uuid, character, uuid, uuid, text
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.create_history_branch(
    uuid, uuid, character, uuid, text, uuid, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.query_revision_history(
    uuid, uuid, character, uuid, bigint, bigint, uuid, integer
) FROM PUBLIC;

INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (4, 'p14.history_checkpoints_v1', current_setting('hwpx_agent.migration_sha256'));

COMMIT;
