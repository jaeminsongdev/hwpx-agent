BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 17 AND migration_name = 'p17.durable_git_mirror_pull_v1')
        OR EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version >= 18) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'FULL_DOCUMENT_IR_REQUIRES_SCHEMA_17';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256', true) IS NULL
        OR current_setting('hwpx_agent.migration_sha256', true) !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'FULL_DOCUMENT_IR_MIGRATION_DIGEST_REQUIRED';
    END IF;
END
$$;

-- No historical migration/function/checksum is rewritten.
ALTER TABLE hwpx_agent.artifacts DROP CONSTRAINT artifacts_kind_value;
ALTER TABLE hwpx_agent.artifacts ADD CONSTRAINT artifacts_kind_value CHECK (
    artifact_kind IN ('source','result','document_ir','preview','evidence','trace','diff','receipt')
);
ALTER TABLE hwpx_agent.revisions
    ADD COLUMN full_document_ir_artifact_id uuid,
    ADD COLUMN full_document_ir_artifact_sha256 character(64),
    ADD COLUMN full_document_ir_result_package_sha256 character(64),
    ADD COLUMN full_document_ir_graph_sha256 character(64),
    ADD CONSTRAINT revisions_full_document_ir_fk FOREIGN KEY (tenant_id, full_document_ir_artifact_id)
        REFERENCES hwpx_agent.artifacts(tenant_id, artifact_id) ON DELETE RESTRICT,
    ADD CONSTRAINT revisions_full_document_ir_shape CHECK (
        (full_document_ir_artifact_id IS NULL AND full_document_ir_artifact_sha256 IS NULL
            AND full_document_ir_result_package_sha256 IS NULL AND full_document_ir_graph_sha256 IS NULL)
        OR (
            full_document_ir_artifact_id IS NOT NULL AND full_document_ir_artifact_sha256 IS NOT NULL
            AND full_document_ir_result_package_sha256 IS NOT NULL AND full_document_ir_graph_sha256 IS NOT NULL
            AND full_document_ir_artifact_id <> source_artifact_id
            AND full_document_ir_artifact_id <> result_artifact_id
            AND full_document_ir_artifact_id IS DISTINCT FROM semantic_diff_artifact_id
            AND full_document_ir_artifact_sha256 ~ '^[0-9a-f]{64}$'
            AND full_document_ir_result_package_sha256 ~ '^[0-9a-f]{64}$'
            AND full_document_ir_graph_sha256 ~ '^[0-9a-f]{64}$'
            AND full_document_ir_artifact_sha256 = full_document_ir_graph_sha256
        )
    );

CREATE FUNCTION hwpx_agent.guard_revision_full_document_ir_v1()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, hwpx_agent AS $$
BEGIN
    IF NEW.full_document_ir_artifact_id IS NULL THEN RETURN NEW; END IF;
    IF NEW.tenant_id IS DISTINCT FROM hwpx_agent.current_tenant_id()
        OR NEW.created_by_subject_sha256 IS DISTINCT FROM hwpx_agent.current_subject_sha256() THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'FULL_DOCUMENT_IR_SCOPE_DENIED';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.artifacts AS ir
        JOIN hwpx_agent.artifacts AS result ON result.tenant_id = ir.tenant_id
        WHERE ir.tenant_id = NEW.tenant_id AND ir.artifact_id = NEW.full_document_ir_artifact_id
            AND ir.artifact_kind = 'document_ir'
            AND ir.media_type = 'application/vnd.hwpx-agent.document-graph+json'
            AND ir.storage_state = 'available' AND ir.validation_state = 'verified'
            AND ir.quarantine_reason_code IS NULL AND ir.size_bytes BETWEEN 1 AND 33554432
            AND ir.content_sha256 = NEW.full_document_ir_artifact_sha256
            AND ir.content_sha256 = NEW.full_document_ir_graph_sha256
            AND result.artifact_id = NEW.result_artifact_id AND result.artifact_kind = 'result'
            AND result.storage_state = 'available' AND result.validation_state = 'verified'
            AND result.quarantine_reason_code IS NULL AND result.size_bytes BETWEEN 1 AND 33554432
            AND result.content_sha256 = NEW.full_document_ir_result_package_sha256
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'FULL_DOCUMENT_IR_ARTIFACT_BINDING_REJECTED';
    END IF;
    RETURN NEW;
END
$$;
CREATE TRIGGER revisions_full_document_ir_guard BEFORE INSERT ON hwpx_agent.revisions
    FOR EACH ROW EXECUTE FUNCTION hwpx_agent.guard_revision_full_document_ir_v1();

-- Exact original v1 CAS control flow with additive parameters and INSERT columns only.
-- Stored metadata/scanner status is not a signed form route or native import attestation.
CREATE FUNCTION hwpx_agent.commit_revision_cas_with_full_ir_v1(
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
    p_commit_receipt_sha256 character(64),
    p_full_document_ir_artifact_id uuid,
    p_full_document_ir_artifact_sha256 character(64),
    p_full_document_ir_result_package_sha256 character(64),
    p_full_document_ir_graph_sha256 character(64)
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
    IF p_full_document_ir_artifact_id IS NULL THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'FULL_DOCUMENT_IR_REQUIRED';
    END IF;
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
        validation_summary_sha256, created_by_subject_sha256,
        full_document_ir_artifact_id, full_document_ir_artifact_sha256,
        full_document_ir_result_package_sha256, full_document_ir_graph_sha256
    ) VALUES (
        p_tenant_id, p_project_id, p_new_revision_id, p_source_artifact_id,
        p_result_artifact_id, p_semantic_diff_artifact_id, p_operation_plan_sha256,
        p_validation_state, p_validation_summary_sha256, p_subject_sha256,
        p_full_document_ir_artifact_id, p_full_document_ir_artifact_sha256,
        p_full_document_ir_result_package_sha256, p_full_document_ir_graph_sha256
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

REVOKE ALL ON FUNCTION hwpx_agent.guard_revision_full_document_ir_v1() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.commit_revision_cas_with_full_ir_v1(
    uuid, uuid, uuid, character, uuid, uuid, bigint, uuid, uuid[], uuid, uuid, uuid,
    character, text, character, character, character, character,
    uuid, character, character, character
) FROM PUBLIC;
INSERT INTO hwpx_agent.schema_versions(version, migration_name, migration_sha256)
VALUES (18, 'p09.full_document_ir_v1', current_setting('hwpx_agent.migration_sha256'));
COMMIT;
