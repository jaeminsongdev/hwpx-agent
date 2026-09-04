BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 2 AND migration_name = 'p14.artifact_service_v1'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 revision CAS migration requires p14.artifact_service_v1';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version = 3) THEN
        RAISE EXCEPTION USING
            ERRCODE = '42710',
            MESSAGE = 'P14 revision CAS migration version 3 already exists';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256', true)
        !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            MESSAGE = 'P14 revision CAS migration requires its exact SHA-256';
    END IF;
END
$$;

ALTER TABLE hwpx_agent.projects
    ADD COLUMN head_generation bigint NOT NULL DEFAULT 0;
UPDATE hwpx_agent.projects
SET head_generation = -1
WHERE head_revision_id IS NOT NULL;
ALTER TABLE hwpx_agent.projects
    ADD CONSTRAINT projects_head_generation_consistency CHECK (
        (head_revision_id IS NULL AND head_generation = 0)
        OR (head_revision_id IS NOT NULL AND head_generation = -1)
        OR (head_revision_id IS NOT NULL AND head_generation > 0)
    );

ALTER TABLE hwpx_agent.branches
    ADD COLUMN head_generation bigint NOT NULL DEFAULT 0;
UPDATE hwpx_agent.branches
SET head_generation = -1
WHERE head_revision_id IS NOT NULL;
ALTER TABLE hwpx_agent.branches
    ADD CONSTRAINT branches_head_generation_consistency CHECK (
        (head_revision_id IS NULL AND head_generation = 0)
        OR (head_revision_id IS NOT NULL AND head_generation = -1)
        OR (head_revision_id IS NOT NULL AND head_generation > 0)
    );

CREATE TABLE hwpx_agent.revision_graph_seals (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    revision_id uuid NOT NULL,
    seal_kind text NOT NULL,
    parent_count smallint NOT NULL,
    committed_generation bigint,
    commit_id uuid,
    commit_request_sha256 character(64),
    transaction_receipt_sha256 character(64),
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, project_id, revision_id),
    CONSTRAINT revision_graph_seals_revision_fk FOREIGN KEY (
        tenant_id, project_id, revision_id
    ) REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id)
        ON DELETE RESTRICT,
    CONSTRAINT revision_graph_seals_parent_count_range CHECK (
        parent_count BETWEEN 0 AND 32
    ),
    CONSTRAINT revision_graph_seals_kind_value CHECK (
        seal_kind IN ('legacy_unqualified', 'service_v1')
    ),
    CONSTRAINT revision_graph_seals_service_complete CHECK (
        (
            seal_kind = 'legacy_unqualified'
            AND committed_generation IS NULL
            AND commit_id IS NULL
            AND commit_request_sha256 IS NULL
            AND transaction_receipt_sha256 IS NULL
        )
        OR (
            seal_kind = 'service_v1'
            AND committed_generation > 0
            AND commit_id IS NOT NULL
            AND commit_request_sha256 ~ '^[0-9a-f]{64}$'
            AND transaction_receipt_sha256 ~ '^[0-9a-f]{64}$'
        )
    )
);

INSERT INTO hwpx_agent.revision_graph_seals (
    tenant_id, project_id, revision_id, seal_kind, parent_count
)
SELECT
    revision.tenant_id,
    revision.project_id,
    revision.revision_id,
    'legacy_unqualified',
    count(parent.parent_revision_id)::smallint
FROM hwpx_agent.revisions AS revision
LEFT JOIN hwpx_agent.revision_parents AS parent
    ON parent.tenant_id = revision.tenant_id
    AND parent.project_id = revision.project_id
    AND parent.revision_id = revision.revision_id
GROUP BY revision.tenant_id, revision.project_id, revision.revision_id;

CREATE TABLE hwpx_agent.revision_commit_receipts (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    commit_id uuid NOT NULL,
    branch_id uuid NOT NULL,
    previous_revision_id uuid,
    expected_generation bigint NOT NULL,
    committed_revision_id uuid NOT NULL,
    committed_generation bigint NOT NULL,
    commit_request_sha256 character(64) NOT NULL,
    transaction_receipt_sha256 character(64) NOT NULL,
    commit_receipt_sha256 character(64) NOT NULL,
    subject_sha256 character(64) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, project_id, commit_id),
    UNIQUE (tenant_id, project_id, committed_revision_id),
    UNIQUE (tenant_id, project_id, commit_request_sha256),
    CONSTRAINT revision_commit_receipts_branch_fk FOREIGN KEY (
        tenant_id, project_id, branch_id
    ) REFERENCES hwpx_agent.branches (tenant_id, project_id, branch_id)
        ON DELETE RESTRICT,
    CONSTRAINT revision_commit_receipts_previous_fk FOREIGN KEY (
        tenant_id, project_id, previous_revision_id
    ) REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id)
        ON DELETE RESTRICT,
    CONSTRAINT revision_commit_receipts_committed_fk FOREIGN KEY (
        tenant_id, project_id, committed_revision_id
    ) REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id)
        ON DELETE RESTRICT,
    CONSTRAINT revision_commit_receipts_generation_step CHECK (
        expected_generation >= 0
        AND committed_generation = expected_generation + 1
    ),
    CONSTRAINT revision_commit_receipts_digest_format CHECK (
        commit_request_sha256 ~ '^[0-9a-f]{64}$'
        AND transaction_receipt_sha256 ~ '^[0-9a-f]{64}$'
        AND commit_receipt_sha256 ~ '^[0-9a-f]{64}$'
        AND subject_sha256 ~ '^[0-9a-f]{64}$'
    )
);

CREATE FUNCTION hwpx_agent.current_subject_sha256()
RETURNS character(64)
LANGUAGE sql
STABLE
SET search_path = pg_catalog
AS $$
    SELECT CASE
        WHEN current_setting('hwpx_agent.subject_sha256', true) ~ '^[0-9a-f]{64}$'
        THEN current_setting('hwpx_agent.subject_sha256', true)::character(64)
        ELSE NULL
    END
$$;

CREATE FUNCTION hwpx_agent.guard_revision_parent_insert()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog, hwpx_agent
AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM hwpx_agent.revision_graph_seals
        WHERE tenant_id = NEW.tenant_id
          AND project_id = NEW.project_id
          AND revision_id = NEW.revision_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'REVISION_GRAPH_SEALED';
    END IF;
    IF EXISTS (
        WITH RECURSIVE ancestors(revision_id) AS (
            SELECT NEW.parent_revision_id
            UNION
            SELECT parent.parent_revision_id
            FROM hwpx_agent.revision_parents AS parent
            JOIN ancestors
              ON parent.tenant_id = NEW.tenant_id
             AND parent.project_id = NEW.project_id
             AND parent.revision_id = ancestors.revision_id
        )
        SELECT 1 FROM ancestors WHERE revision_id = NEW.revision_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23000',
            MESSAGE = 'REVISION_GRAPH_CYCLE';
    END IF;
    RETURN NEW;
END
$$;

CREATE TRIGGER revision_parents_guard_insert
BEFORE INSERT ON hwpx_agent.revision_parents
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.guard_revision_parent_insert();

CREATE TRIGGER revision_graph_seals_immutable
BEFORE UPDATE OR DELETE ON hwpx_agent.revision_graph_seals
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();

CREATE TRIGGER revision_commit_receipts_immutable
BEFORE UPDATE OR DELETE ON hwpx_agent.revision_commit_receipts
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();

CREATE FUNCTION hwpx_agent.commit_revision_cas(
    p_tenant_id uuid,
    p_project_id uuid,
    p_branch_id uuid,
    p_subject_sha256 character(64),
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
DECLARE
    v_head_revision_id uuid;
    v_head_generation bigint;
    v_project_head_revision_id uuid;
    v_project_head_generation bigint;
    v_is_default boolean;
    v_parent_id uuid;
    v_parent_count integer;
    v_ordinal integer;
    v_artifact_id uuid;
BEGIN
    IF hwpx_agent.current_tenant_id() IS DISTINCT FROM p_tenant_id
       OR hwpx_agent.current_subject_sha256() IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'REVISION_CONTEXT_MISMATCH';
    END IF;
    IF p_tenant_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_project_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_branch_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_commit_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_new_revision_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$'
       OR p_operation_plan_sha256 !~ '^[0-9a-f]{64}$'
       OR p_validation_summary_sha256 !~ '^[0-9a-f]{64}$'
       OR p_transaction_receipt_sha256 !~ '^[0-9a-f]{64}$'
       OR p_commit_request_sha256 !~ '^[0-9a-f]{64}$'
       OR p_commit_receipt_sha256 !~ '^[0-9a-f]{64}$'
       OR p_validation_state <> 'verified' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'REVISION_REQUEST_INVALID';
    END IF;
    IF p_source_artifact_id = p_result_artifact_id
       OR p_source_artifact_id = p_semantic_diff_artifact_id
       OR p_result_artifact_id = p_semantic_diff_artifact_id THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'REVISION_ARTIFACT_ID_REUSED';
    END IF;

    SELECT
        branch.head_revision_id,
        branch.head_generation,
        branch.is_default,
        project.head_revision_id,
        project.head_generation
    INTO
        v_head_revision_id,
        v_head_generation,
        v_is_default,
        v_project_head_revision_id,
        v_project_head_generation
    FROM hwpx_agent.branches AS branch
    JOIN hwpx_agent.projects AS project
      ON project.tenant_id = branch.tenant_id
     AND project.project_id = branch.project_id
    WHERE branch.tenant_id = p_tenant_id
      AND branch.project_id = p_project_id
      AND branch.branch_id = p_branch_id
      AND project.state = 'active'
    FOR UPDATE OF branch, project;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'REVISION_STREAM_NOT_FOUND';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.project_acl
        WHERE tenant_id = p_tenant_id
          AND project_id = p_project_id
          AND subject_sha256 = p_subject_sha256
          AND role IN ('editor', 'owner')
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'REVISION_COMMIT_DENIED';
    END IF;
    IF v_head_generation < 0 OR (v_is_default AND v_project_head_generation < 0) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'REVISION_LEGACY_HEAD_UNQUALIFIED';
    END IF;
    IF v_is_default AND ROW(v_project_head_revision_id, v_project_head_generation)
        IS DISTINCT FROM ROW(v_head_revision_id, v_head_generation) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'REVISION_DEFAULT_HEAD_INCONSISTENT';
    END IF;

    IF v_head_revision_id IS DISTINCT FROM p_expected_revision_id
       OR v_head_generation <> p_expected_generation THEN
        RETURN QUERY SELECT
            'conflict'::text,
            v_head_revision_id,
            v_head_generation,
            NULL::uuid,
            NULL::bigint,
            NULL::character(64);
        RETURN;
    END IF;

    v_parent_count := COALESCE(cardinality(p_parent_revision_ids), 0);
    IF v_parent_count > 32
       OR (v_head_revision_id IS NULL AND (p_expected_generation <> 0 OR v_parent_count <> 0))
       OR (v_head_revision_id IS NOT NULL AND (
            p_expected_generation <= 0
            OR v_parent_count = 0
            OR p_parent_revision_ids[1] IS DISTINCT FROM v_head_revision_id
       ))
       OR p_new_revision_id = ANY(COALESCE(p_parent_revision_ids, ARRAY[]::uuid[]))
       OR (
            SELECT count(*) <> count(DISTINCT parent_id)
            FROM unnest(COALESCE(p_parent_revision_ids, ARRAY[]::uuid[])) AS parent_id
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'REVISION_PARENT_SET_INVALID';
    END IF;
    IF EXISTS (
        SELECT 1 FROM hwpx_agent.revisions
        WHERE tenant_id = p_tenant_id
          AND project_id = p_project_id
          AND revision_id = p_new_revision_id
    ) OR EXISTS (
        SELECT 1 FROM hwpx_agent.revision_commit_receipts
        WHERE tenant_id = p_tenant_id
          AND project_id = p_project_id
          AND (commit_id = p_commit_id OR commit_request_sha256 = p_commit_request_sha256)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23505', MESSAGE = 'REVISION_IDENTITY_ALREADY_EXISTS';
    END IF;
    FOREACH v_parent_id IN ARRAY COALESCE(p_parent_revision_ids, ARRAY[]::uuid[]) LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM hwpx_agent.revisions AS revision
            JOIN hwpx_agent.revision_graph_seals AS seal
              ON seal.tenant_id = revision.tenant_id
             AND seal.project_id = revision.project_id
             AND seal.revision_id = revision.revision_id
            WHERE revision.tenant_id = p_tenant_id
              AND revision.project_id = p_project_id
              AND revision.revision_id = v_parent_id
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'REVISION_PARENT_UNAVAILABLE';
        END IF;
    END LOOP;
    FOREACH v_artifact_id IN ARRAY array_remove(ARRAY[
        p_source_artifact_id, p_result_artifact_id, p_semantic_diff_artifact_id
    ], NULL) LOOP
        IF NOT EXISTS (
            SELECT 1 FROM hwpx_agent.artifacts
            WHERE tenant_id = p_tenant_id
              AND artifact_id = v_artifact_id
              AND storage_state = 'available'
              AND validation_state = 'verified'
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'REVISION_ARTIFACT_UNAVAILABLE';
        END IF;
    END LOOP;

    INSERT INTO hwpx_agent.revisions (
        tenant_id, project_id, revision_id, source_artifact_id, result_artifact_id,
        semantic_diff_artifact_id, operation_plan_sha256, validation_state,
        validation_summary_sha256, created_by_subject_sha256
    ) VALUES (
        p_tenant_id, p_project_id, p_new_revision_id, p_source_artifact_id,
        p_result_artifact_id, p_semantic_diff_artifact_id, p_operation_plan_sha256,
        p_validation_state, p_validation_summary_sha256, p_subject_sha256
    );

    v_ordinal := 0;
    FOREACH v_parent_id IN ARRAY COALESCE(p_parent_revision_ids, ARRAY[]::uuid[]) LOOP
        INSERT INTO hwpx_agent.revision_parents (
            tenant_id, project_id, revision_id, parent_revision_id, parent_ordinal
        ) VALUES (
            p_tenant_id, p_project_id, p_new_revision_id, v_parent_id, v_ordinal
        );
        v_ordinal := v_ordinal + 1;
    END LOOP;

    INSERT INTO hwpx_agent.revision_graph_seals (
        tenant_id, project_id, revision_id, seal_kind, parent_count,
        committed_generation, commit_id, commit_request_sha256,
        transaction_receipt_sha256
    ) VALUES (
        p_tenant_id, p_project_id, p_new_revision_id, 'service_v1', v_parent_count,
        p_expected_generation + 1, p_commit_id, p_commit_request_sha256,
        p_transaction_receipt_sha256
    );

    UPDATE hwpx_agent.branches
    SET head_revision_id = p_new_revision_id,
        head_generation = p_expected_generation + 1
    WHERE tenant_id = p_tenant_id
      AND project_id = p_project_id
      AND branch_id = p_branch_id;
    IF v_is_default THEN
        UPDATE hwpx_agent.projects
        SET head_revision_id = p_new_revision_id,
            head_generation = p_expected_generation + 1
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id;
    END IF;

    INSERT INTO hwpx_agent.revision_commit_receipts (
        tenant_id, project_id, commit_id, branch_id, previous_revision_id,
        expected_generation, committed_revision_id, committed_generation,
        commit_request_sha256, transaction_receipt_sha256, commit_receipt_sha256,
        subject_sha256
    ) VALUES (
        p_tenant_id, p_project_id, p_commit_id, p_branch_id, p_expected_revision_id,
        p_expected_generation, p_new_revision_id, p_expected_generation + 1,
        p_commit_request_sha256, p_transaction_receipt_sha256, p_commit_receipt_sha256,
        p_subject_sha256
    );

    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, revision_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'revision.cas_committed', p_subject_sha256,
        p_new_revision_id, p_commit_request_sha256
    );

    RETURN QUERY SELECT
        'committed'::text,
        p_new_revision_id,
        p_expected_generation + 1,
        p_new_revision_id,
        p_expected_generation + 1,
        p_commit_receipt_sha256;
END
$$;

ALTER TABLE hwpx_agent.revision_graph_seals ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.revision_graph_seals FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.revision_graph_seals
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());

ALTER TABLE hwpx_agent.revision_commit_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.revision_commit_receipts FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.revision_commit_receipts
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());

REVOKE ALL ON TABLE hwpx_agent.revision_graph_seals FROM PUBLIC;
REVOKE ALL ON TABLE hwpx_agent.revision_commit_receipts FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.current_subject_sha256() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.guard_revision_parent_insert() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.commit_revision_cas(
    uuid, uuid, uuid, character, uuid, uuid, bigint, uuid, uuid[], uuid, uuid, uuid,
    character, text, character, character, character, character
) FROM PUBLIC;

INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (3, 'p14.revision_cas_v1', current_setting('hwpx_agent.migration_sha256'));

COMMIT;
