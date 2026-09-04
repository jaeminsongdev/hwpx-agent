BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hwpx_agent_retention_test_app') THEN
        CREATE ROLE hwpx_agent_retention_test_app
            NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
    END IF;
END
$$;

GRANT USAGE ON SCHEMA hwpx_agent TO hwpx_agent_retention_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id()
TO hwpx_agent_retention_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.current_subject_sha256()
TO hwpx_agent_retention_test_app;
GRANT SELECT ON TABLE
    hwpx_agent.schema_versions,
    hwpx_agent.projects,
    hwpx_agent.project_acl,
    hwpx_agent.artifacts,
    hwpx_agent.revisions,
    hwpx_agent.branches,
    hwpx_agent.revision_commit_receipts,
    hwpx_agent.retention_policies,
    hwpx_agent.retention_policy_rules,
    hwpx_agent.legal_holds,
    hwpx_agent.artifact_deletion_requests,
    hwpx_agent.artifact_purge_receipts,
    hwpx_agent.project_local_mirrors,
    hwpx_agent.local_mirror_conflicts
TO hwpx_agent_retention_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.create_retention_policy_v1(
    uuid, text, character, integer, bigint, bigint, bigint, bigint, bigint, bigint, bigint
) TO hwpx_agent_retention_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.create_legal_hold_v1(
    uuid, uuid, character, uuid, uuid, text
) TO hwpx_agent_retention_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.release_legal_hold_v1(
    uuid, uuid, character, uuid
) TO hwpx_agent_retention_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.request_artifact_deletion_v1(
    uuid, uuid, character, uuid, uuid, text
) TO hwpx_agent_retention_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.claim_artifact_purge_v1(
    uuid, uuid, character, uuid, uuid, uuid, integer
) TO hwpx_agent_retention_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.record_artifact_purge_failure_v1(
    uuid, uuid, character, uuid, uuid, bigint, character
) TO hwpx_agent_retention_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.complete_artifact_purge_v1(
    uuid, uuid, character, uuid, uuid, bigint, uuid, text, character
) TO hwpx_agent_retention_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.register_local_mirror_v1(
    uuid, uuid, character, uuid, character, uuid, uuid, bigint, character
) TO hwpx_agent_retention_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.queue_local_mirror_plan_v1(
    uuid, uuid, character, uuid, character, character
) TO hwpx_agent_retention_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.begin_local_mirror_push_v1(
    uuid, uuid, character, uuid, uuid, uuid, integer
) TO hwpx_agent_retention_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.complete_local_mirror_push_v1(
    uuid, uuid, character, uuid, uuid, uuid
) TO hwpx_agent_retention_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.resolve_local_mirror_conflict_v1(
    uuid, uuid, character, uuid, text, uuid
) TO hwpx_agent_retention_test_app;

INSERT INTO hwpx_agent.tenants (tenant_id, slug) VALUES
    ('f1000000-0000-0000-0000-000000000001', 'retention-tenant-primary'),
    ('f1000000-0000-0000-0000-000000000002', 'retention-tenant-other');

INSERT INTO hwpx_agent.projects (
    tenant_id, project_id, slug, display_name, target_profile_id, retention_policy_id
) VALUES
    (
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001',
        'retention-project-primary', 'Retention Project Primary',
        'hancom-hangul-2020-current-pc', 'retention.p14-09-fixture'
    ),
    (
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000002',
        'retention-project-shared', 'Retention Project Shared',
        'hancom-hangul-2020-current-pc', 'retention.p14-09-fixture'
    );

INSERT INTO hwpx_agent.project_acl (tenant_id, project_id, subject_sha256, role) VALUES
    ('f1000000-0000-0000-0000-000000000001',
     'f2000000-0000-0000-0000-000000000001', repeat('a', 64), 'owner'),
    ('f1000000-0000-0000-0000-000000000001',
     'f2000000-0000-0000-0000-000000000001', repeat('b', 64), 'reader'),
    ('f1000000-0000-0000-0000-000000000001',
     'f2000000-0000-0000-0000-000000000001', repeat('c', 64), 'editor'),
    ('f1000000-0000-0000-0000-000000000001',
     'f2000000-0000-0000-0000-000000000002', repeat('a', 64), 'owner');

INSERT INTO hwpx_agent.branches (
    tenant_id, project_id, branch_id, name, is_default, created_by_subject_sha256
) VALUES
    ('f1000000-0000-0000-0000-000000000001',
     'f2000000-0000-0000-0000-000000000001',
     'f3000000-0000-0000-0000-000000000001', 'main', true, repeat('a', 64)),
    ('f1000000-0000-0000-0000-000000000001',
     'f2000000-0000-0000-0000-000000000001',
     'f3000000-0000-0000-0000-000000000002', 'alternate', false, repeat('a', 64)),
    ('f1000000-0000-0000-0000-000000000001',
     'f2000000-0000-0000-0000-000000000002',
     'f3000000-0000-0000-0000-000000000003', 'main', true, repeat('a', 64));

WITH artifact_seed AS (
    SELECT
        ordinal,
        concat('f4000000-0000-0000-0000-', lpad(ordinal::text, 12, '0'))::uuid AS artifact_id,
        lpad(to_hex(ordinal), 64, '0') AS content_sha256,
        CASE ordinal % 3 WHEN 1 THEN 'source' WHEN 2 THEN 'result' ELSE 'diff' END
            AS artifact_kind
    FROM generate_series(1, 30) AS ordinal
)
INSERT INTO hwpx_agent.artifacts (
    tenant_id, artifact_id, content_sha256, size_bytes, media_type, artifact_kind,
    storage_state, encryption_key_ref, verified_at, created_at, updated_at,
    service_metadata_version, filename, object_key, encryption_algorithm,
    encryption_nonce, aad_sha256, ciphertext_sha256, validation_state,
    scanner_engine_ref, scanner_signature_version, authorization_generation
)
SELECT
    'f1000000-0000-0000-0000-000000000001', artifact_id, content_sha256, ordinal,
    'application/octet-stream', artifact_kind, 'available', 'kms.retention-fixture',
    transaction_timestamp() - interval '30 days',
    transaction_timestamp() - interval '30 days',
    transaction_timestamp() - interval '30 days',
    1, concat('artifact-', ordinal, '.bin'),
    concat(
        'artifacts/v1/f1000000000000000000000000000001/', artifact_kind,
        '/available/', content_sha256, '.aes256gcm'
    ),
    'AES-256-GCM', decode(lpad(to_hex(ordinal), 24, '0'), 'hex'),
    lpad(to_hex(ordinal + 100), 64, '0'),
    lpad(to_hex(ordinal + 200), 64, '0'),
    'verified', 'scanner.retention-fixture', 'v1', 1
FROM artifact_seed;

INSERT INTO hwpx_agent.artifact_acl (
    tenant_id, artifact_id, subject_sha256, can_read, can_manage
)
SELECT tenant_id, artifact_id, repeat('a', 64), true, true
FROM hwpx_agent.artifacts
WHERE tenant_id = 'f1000000-0000-0000-0000-000000000001';

-- Fixture-only remote seeding. The P14-07 regression fixture separately proves that production
-- receipts can only be created by the idempotent commit capability. This temporary helper creates
-- the already-validated receipt/head shape so P14-09 can exercise its consumer-side bindings.
CREATE FUNCTION pg_temp.seed_remote_commit(
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
) RETURNS TABLE (outcome text)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
DECLARE
    v_replication_role text := current_setting('session_replication_role');
    v_parent_id uuid;
    v_ordinal integer := 0;
BEGIN
    IF p_validation_state <> 'verified' OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.branches
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id
          AND branch_id = p_branch_id
          AND head_revision_id IS NOT DISTINCT FROM p_expected_revision_id
          AND head_generation = p_expected_generation
    ) THEN
        RAISE EXCEPTION 'fixture remote head mismatch';
    END IF;
    PERFORM set_config('session_replication_role', 'replica', true);
    BEGIN
        INSERT INTO hwpx_agent.revisions (
            tenant_id, project_id, revision_id, source_artifact_id, result_artifact_id,
            semantic_diff_artifact_id, operation_plan_sha256, validation_state,
            validation_summary_sha256, created_by_subject_sha256
        ) VALUES (
            p_tenant_id, p_project_id, p_new_revision_id, p_source_artifact_id,
            p_result_artifact_id, p_semantic_diff_artifact_id, p_operation_plan_sha256,
            p_validation_state, p_validation_summary_sha256, p_subject_sha256
        );
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
            p_tenant_id, p_project_id, p_new_revision_id, 'service_v1',
            COALESCE(cardinality(p_parent_revision_ids), 0), p_expected_generation + 1,
            p_commit_id, p_commit_request_sha256, p_transaction_receipt_sha256
        );
        UPDATE hwpx_agent.branches
        SET head_revision_id = p_new_revision_id,
            head_generation = p_expected_generation + 1
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id
          AND branch_id = p_branch_id;
        UPDATE hwpx_agent.projects AS project
        SET head_revision_id = p_new_revision_id,
            head_generation = p_expected_generation + 1
        WHERE project.tenant_id = p_tenant_id AND project.project_id = p_project_id
          AND EXISTS (
              SELECT 1 FROM hwpx_agent.branches AS branch
              WHERE branch.tenant_id = project.tenant_id
                AND branch.project_id = project.project_id
                AND branch.branch_id = p_branch_id AND branch.is_default
          );
        INSERT INTO hwpx_agent.revision_commit_receipts (
            tenant_id, project_id, commit_id, branch_id, previous_revision_id,
            expected_generation, committed_revision_id, committed_generation,
            commit_request_sha256, transaction_receipt_sha256, commit_receipt_sha256,
            subject_sha256
        ) VALUES (
            p_tenant_id, p_project_id, p_commit_id, p_branch_id, p_expected_revision_id,
            p_expected_generation, p_new_revision_id, p_expected_generation + 1,
            p_commit_request_sha256, p_transaction_receipt_sha256,
            p_commit_receipt_sha256, p_subject_sha256
        );
        INSERT INTO hwpx_agent.audit_events (
            tenant_id, project_id, event_type, subject_sha256, revision_id, payload_sha256
        ) VALUES (
            p_tenant_id, p_project_id, 'revision.cas_committed', p_subject_sha256,
            p_new_revision_id, p_commit_request_sha256
        );
    EXCEPTION WHEN OTHERS THEN
        PERFORM set_config('session_replication_role', v_replication_role, true);
        RAISE;
    END;
    PERFORM set_config('session_replication_role', v_replication_role, true);
    RETURN QUERY SELECT 'committed'::text;
END
$$;

REVOKE ALL ON FUNCTION pg_temp.seed_remote_commit(
    uuid, uuid, uuid, character, uuid, uuid, bigint, uuid, uuid[], uuid, uuid, uuid,
    character, text, character, character, character, character
) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION pg_temp.seed_remote_commit(
    uuid, uuid, uuid, character, uuid, uuid, bigint, uuid, uuid[], uuid, uuid, uuid,
    character, text, character, character, character, character
) TO hwpx_agent_retention_test_app;

CREATE FUNCTION pg_temp.try_tombstoned_revision_reference()
RETURNS void
LANGUAGE sql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
    INSERT INTO hwpx_agent.revisions (
        tenant_id, project_id, revision_id, source_artifact_id, result_artifact_id,
        semantic_diff_artifact_id, operation_plan_sha256, validation_state,
        validation_summary_sha256, created_by_subject_sha256
    ) VALUES (
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001',
        'f5000000-0000-0000-0000-000000000099',
        'f4000000-0000-0000-0000-000000000002',
        'f4000000-0000-0000-0000-000000000010',
        NULL, repeat('7', 64), 'verified', repeat('8', 64), repeat('a', 64)
    )
$$;

REVOKE ALL ON FUNCTION pg_temp.try_tombstoned_revision_reference() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION pg_temp.try_tombstoned_revision_reference()
TO hwpx_agent_retention_test_app;

SET LOCAL ROLE hwpx_agent_retention_test_app;

DO $$
DECLARE
    v_assertions integer := 0;
    v_error text;
    v_text text;
    v_outcome text;
    v_attempt integer;
    v_fence bigint;
    v_count bigint;
BEGIN
    PERFORM set_config('hwpx_agent.tenant_id',
        'f1000000-0000-0000-0000-000000000001', true);
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);

    -- 01: exact v9 shape exists, is tenant isolated, and has the bounded worker functions.
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 9 AND migration_name = 'p14.retention_local_mirror_v1'
    ) OR (
        SELECT count(*) FROM information_schema.tables
        WHERE table_schema = 'hwpx_agent' AND table_name IN (
            'retention_policies', 'retention_policy_rules', 'legal_holds',
            'artifact_deletion_requests', 'artifact_purge_receipts',
            'project_local_mirrors', 'local_mirror_conflicts'
        )
    ) <> 7 OR NOT EXISTS (
        SELECT 1 FROM pg_proc
        WHERE oid = 'hwpx_agent.record_artifact_purge_failure_v1(uuid,uuid,character,uuid,uuid,bigint,character)'::regprocedure
          AND prosecdef
    ) THEN
        RAISE EXCEPTION 'assertion 01 failed';
    END IF;
    v_assertions := v_assertions + 1;

    -- 02: the application role has function access but no direct mutation privilege.
    IF has_table_privilege(
        'hwpx_agent_retention_test_app', 'hwpx_agent.project_local_mirrors', 'UPDATE'
    ) OR has_table_privilege(
        'hwpx_agent_retention_test_app', 'hwpx_agent.artifact_deletion_requests', 'DELETE'
    ) OR NOT has_function_privilege(
        'hwpx_agent_retention_test_app',
        'hwpx_agent.begin_local_mirror_push_v1(uuid,uuid,character,uuid,uuid,uuid,integer)',
        'EXECUTE'
    ) OR has_function_privilege(
        'hwpx_agent_retention_test_app',
        'hwpx_agent.protect_p14_09_identity()',
        'EXECUTE'
    ) THEN
        RAISE EXCEPTION 'assertion 02 failed';
    END IF;
    v_assertions := v_assertions + 1;

    -- Establish three revisions on project A and one shared-artifact revision on project B.
    SELECT outcome INTO v_outcome FROM pg_temp.seed_remote_commit(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001',
        'f3000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f6000000-0000-0000-0000-000000000001', NULL, 0,
        'f5000000-0000-0000-0000-000000000001', ARRAY[]::uuid[],
        'f4000000-0000-0000-0000-000000000001',
        'f4000000-0000-0000-0000-000000000002',
        'f4000000-0000-0000-0000-000000000003',
        repeat('1', 64), 'verified', repeat('2', 64), repeat('3', 64),
        repeat('4', 64), repeat('5', 64)
    );
    SELECT outcome INTO v_outcome FROM pg_temp.seed_remote_commit(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001',
        'f3000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f6000000-0000-0000-0000-000000000002',
        'f5000000-0000-0000-0000-000000000001', 1,
        'f5000000-0000-0000-0000-000000000002',
        ARRAY['f5000000-0000-0000-0000-000000000001']::uuid[],
        'f4000000-0000-0000-0000-000000000004',
        'f4000000-0000-0000-0000-000000000005',
        'f4000000-0000-0000-0000-000000000006',
        repeat('6', 64), 'verified', repeat('7', 64), repeat('8', 64),
        repeat('9', 64), repeat('a', 64)
    );
    SELECT outcome INTO v_outcome FROM pg_temp.seed_remote_commit(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001',
        'f3000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f6000000-0000-0000-0000-000000000003',
        'f5000000-0000-0000-0000-000000000002', 2,
        'f5000000-0000-0000-0000-000000000003',
        ARRAY['f5000000-0000-0000-0000-000000000002']::uuid[],
        'f4000000-0000-0000-0000-000000000007',
        'f4000000-0000-0000-0000-000000000010',
        'f4000000-0000-0000-0000-000000000011',
        repeat('b', 64), 'verified', repeat('c', 64), repeat('d', 64),
        repeat('e', 64), repeat('f', 64)
    );
    SELECT outcome INTO v_outcome FROM pg_temp.seed_remote_commit(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000002',
        'f3000000-0000-0000-0000-000000000003', repeat('a', 64),
        'f6000000-0000-0000-0000-000000000010', NULL, 0,
        'f5000000-0000-0000-0000-000000000010', ARRAY[]::uuid[],
        'f4000000-0000-0000-0000-000000000007',
        'f4000000-0000-0000-0000-000000000012',
        'f4000000-0000-0000-0000-000000000013',
        repeat('0', 64), 'verified', repeat('1', 64), repeat('2', 64),
        repeat('3', 64), repeat('4', 64)
    );
    IF v_outcome <> 'committed' OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.branches
        WHERE branch_id = 'f3000000-0000-0000-0000-000000000001'
          AND head_revision_id = 'f5000000-0000-0000-0000-000000000003'
          AND head_generation = 3
    ) THEN RAISE EXCEPTION 'assertion 03 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 04: a reader cannot spoof an owner's digest through a function argument.
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('b', 64), true);
    BEGIN
        PERFORM hwpx_agent.create_retention_policy_v1(
            'f1000000-0000-0000-0000-000000000001', 'retention.spoofed',
            repeat('a', 64), 0, 1, 1, 1, 1, 1, 1, 1
        );
        RAISE EXCEPTION 'assertion 04 unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'RETENTION_RESOURCE_NOT_FOUND' THEN RAISE; END IF;
    END;
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);
    v_assertions := v_assertions + 1;

    -- 05: policy identity is bounded and a complete immutable seven-class policy is created.
    BEGIN
        PERFORM hwpx_agent.create_retention_policy_v1(
            'f1000000-0000-0000-0000-000000000001', repeat('a', 129) || '.policy',
            repeat('a', 64), 0, 1, 1, 1, 1, 1, 1, 1
        );
        RAISE EXCEPTION 'assertion 05 oversized policy unexpectedly succeeded';
    EXCEPTION WHEN check_violation THEN
        NULL;
    END;
    PERFORM hwpx_agent.create_retention_policy_v1(
        'f1000000-0000-0000-0000-000000000001', 'retention.p14-09-fixture',
        repeat('a', 64), 0,
        315360000, 315360000, 315360000, 315360000,
        315360000, 315360000, 315360000
    );
    IF (SELECT count(*) FROM hwpx_agent.retention_policy_rules
        WHERE retention_policy_id = 'retention.p14-09-fixture') <> 7 THEN
        RAISE EXCEPTION 'assertion 05 failed';
    END IF;
    v_assertions := v_assertions + 1;

    -- 06: an artifact legal hold blocks tombstoning.
    PERFORM hwpx_agent.create_legal_hold_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f9000000-0000-0000-0000-000000000001',
        'f4000000-0000-0000-0000-000000000002', 'LITIGATION_HOLD'
    );
    BEGIN
        PERFORM hwpx_agent.request_artifact_deletion_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'f4000000-0000-0000-0000-000000000002',
            'fb000000-0000-0000-0000-000000000001', 'user_delete'
        );
        RAISE EXCEPTION 'assertion 06 unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'RETENTION_LEGAL_HOLD_ACTIVE' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 07: release permits one tombstone and exact request replay.
    PERFORM hwpx_agent.release_legal_hold_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f9000000-0000-0000-0000-000000000001'
    );
    SELECT hwpx_agent.request_artifact_deletion_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f4000000-0000-0000-0000-000000000002',
        'fb000000-0000-0000-0000-000000000001', 'user_delete'
    ) INTO v_text;
    IF v_text <> 'tombstoned' THEN RAISE EXCEPTION 'assertion 07 failed'; END IF;
    SELECT hwpx_agent.request_artifact_deletion_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f4000000-0000-0000-0000-000000000002',
        'fb000000-0000-0000-0000-000000000001', 'user_delete'
    ) INTO v_text;
    IF v_text <> 'replay' OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.artifacts
        WHERE artifact_id = 'f4000000-0000-0000-0000-000000000002'
          AND storage_state = 'tombstoned' AND authorization_generation = 2
    ) THEN RAISE EXCEPTION 'assertion 07 replay failed'; END IF;
    BEGIN
        PERFORM hwpx_agent.request_artifact_deletion_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'f4000000-0000-0000-0000-000000000002',
            'fb000000-0000-0000-0000-000000000001', 'policy_expiry'
        );
        RAISE EXCEPTION 'assertion 07 drift unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'RETENTION_DELETE_CONFLICT' THEN RAISE; END IF;
    END;
    BEGIN
        PERFORM pg_temp.try_tombstoned_revision_reference();
        RAISE EXCEPTION 'assertion 07 reference race unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'RETENTION_ARTIFACT_UNAVAILABLE' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 08: a different deletion identity cannot alias the same artifact.
    BEGIN
        PERFORM hwpx_agent.request_artifact_deletion_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'f4000000-0000-0000-0000-000000000002',
            'fb000000-0000-0000-0000-000000000099', 'user_delete'
        );
        RAISE EXCEPTION 'assertion 08 unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'RETENTION_DELETE_CONFLICT' THEN RAISE; END IF;
    END;
    BEGIN
        PERFORM hwpx_agent.request_artifact_deletion_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'f4000000-0000-0000-0000-000000000010',
            'fb000000-0000-0000-0000-000000000001', 'user_delete'
        );
        RAISE EXCEPTION 'assertion 08 request alias unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'RETENTION_DELETE_CONFLICT' THEN RAISE; END IF;
    END;
    BEGIN
        PERFORM hwpx_agent.request_artifact_deletion_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'f4000000-0000-0000-0000-000000000099',
            'fb000000-0000-0000-0000-000000000001', 'user_delete'
        );
        RAISE EXCEPTION 'assertion 08 missing artifact alias unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'RETENTION_DELETE_CONFLICT' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 09: first purge claim is fenced at attempt one.
    SELECT returned_attempt, returned_fencing_token INTO v_attempt, v_fence
    FROM hwpx_agent.claim_artifact_purge_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'fb000000-0000-0000-0000-000000000001',
        'fc000000-0000-0000-0000-000000000001',
        'fd000000-0000-0000-0000-000000000001', 30
    );
    IF v_attempt <> 1 OR v_fence <> 1 THEN RAISE EXCEPTION 'assertion 09 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 10: a new legal hold cannot silently overtake an already-authorized purge lease.
    BEGIN
        PERFORM hwpx_agent.create_legal_hold_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'f9000000-0000-0000-0000-000000000002',
            'f4000000-0000-0000-0000-000000000002', 'REGULATORY_HOLD'
        );
        RAISE EXCEPTION 'assertion 10 unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'RETENTION_PURGE_IN_PROGRESS' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 11: a failed effect releases a retry slot; a hold added between attempts blocks reclaim.
    SELECT hwpx_agent.record_artifact_purge_failure_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'fb000000-0000-0000-0000-000000000001',
        'fd000000-0000-0000-0000-000000000001', 1, repeat('1', 64)
    ) INTO v_text;
    PERFORM hwpx_agent.create_legal_hold_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f9000000-0000-0000-0000-000000000002',
        'f4000000-0000-0000-0000-000000000002', 'REGULATORY_HOLD'
    );
    BEGIN
        PERFORM * FROM hwpx_agent.claim_artifact_purge_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'fb000000-0000-0000-0000-000000000001',
            'fc000000-0000-0000-0000-000000000001',
            'fd000000-0000-0000-0000-000000000002', 30
        );
        RAISE EXCEPTION 'assertion 11 unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'RETENTION_LEGAL_HOLD_ACTIVE' THEN RAISE; END IF;
    END;
    PERFORM hwpx_agent.release_legal_hold_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f9000000-0000-0000-0000-000000000002'
    );
    IF v_text <> 'tombstoned' THEN RAISE EXCEPTION 'assertion 11 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 12: a stale execution cannot complete the second fenced attempt.
    SELECT returned_attempt, returned_fencing_token INTO v_attempt, v_fence
    FROM hwpx_agent.claim_artifact_purge_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'fb000000-0000-0000-0000-000000000001',
        'fc000000-0000-0000-0000-000000000001',
        'fd000000-0000-0000-0000-000000000002', 30
    );
    BEGIN
        PERFORM hwpx_agent.complete_artifact_purge_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'fb000000-0000-0000-0000-000000000001',
            'fd000000-0000-0000-0000-000000000001', 1,
            'fe000000-0000-0000-0000-000000000099',
            'object_deleted', repeat('2', 64)
        );
        RAISE EXCEPTION 'assertion 12 unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'RETENTION_LEASE_STALE' THEN RAISE; END IF;
    END;
    IF v_attempt <> 2 OR v_fence <> 2 THEN RAISE EXCEPTION 'assertion 12 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 13: three recorded failures reach an explicit terminal state with no fourth effect.
    PERFORM hwpx_agent.record_artifact_purge_failure_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'fb000000-0000-0000-0000-000000000001',
        'fd000000-0000-0000-0000-000000000002', 2, repeat('3', 64)
    );
    SELECT returned_attempt, returned_fencing_token INTO v_attempt, v_fence
    FROM hwpx_agent.claim_artifact_purge_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'fb000000-0000-0000-0000-000000000001',
        'fc000000-0000-0000-0000-000000000001',
        'fd000000-0000-0000-0000-000000000003', 30
    );
    SELECT hwpx_agent.record_artifact_purge_failure_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'fb000000-0000-0000-0000-000000000001',
        'fd000000-0000-0000-0000-000000000003', 3, repeat('4', 64)
    ) INTO v_text;
    IF v_attempt <> 3 OR v_fence <> 3 OR v_text <> 'failed_terminal'
       OR NOT EXISTS (
            SELECT 1 FROM hwpx_agent.artifact_deletion_requests
            WHERE deletion_request_id = 'fb000000-0000-0000-0000-000000000001'
              AND state = 'failed_terminal' AND attempt_count = 3
              AND last_failure_sha256 = repeat('4', 64) AND completed_at IS NOT NULL
       ) THEN RAISE EXCEPTION 'assertion 13 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 14: a second artifact completes to a durable purged state and immutable receipt.
    PERFORM hwpx_agent.request_artifact_deletion_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f4000000-0000-0000-0000-000000000005',
        'fb000000-0000-0000-0000-000000000002', 'user_delete'
    );
    SELECT returned_attempt, returned_fencing_token INTO v_attempt, v_fence
    FROM hwpx_agent.claim_artifact_purge_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'fb000000-0000-0000-0000-000000000002',
        'fc000000-0000-0000-0000-000000000001',
        'fd000000-0000-0000-0000-000000000004', 30
    );
    PERFORM hwpx_agent.complete_artifact_purge_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'fb000000-0000-0000-0000-000000000002',
        'fd000000-0000-0000-0000-000000000004', 1,
        'fe000000-0000-0000-0000-000000000001',
        'object_deleted', repeat('5', 64)
    );
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.artifacts
        WHERE artifact_id = 'f4000000-0000-0000-0000-000000000005'
          AND storage_state = 'purged' AND object_key IS NULL
          AND authorization_generation = 3
    ) OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.artifact_purge_receipts
        WHERE purge_receipt_id = 'fe000000-0000-0000-0000-000000000001'
          AND outcome = 'object_deleted' AND proof_sha256 = repeat('5', 64)
    ) THEN RAISE EXCEPTION 'assertion 14 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 15: a purged artifact cannot receive a misleading new legal hold.
    BEGIN
        PERFORM hwpx_agent.create_legal_hold_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'f9000000-0000-0000-0000-000000000003',
            'f4000000-0000-0000-0000-000000000005', 'LATE_HOLD'
        );
        RAISE EXCEPTION 'assertion 15 unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'RETENTION_RESOURCE_NOT_FOUND' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 16: policy expiry respects the per-class duration and cannot be promoted early.
    BEGIN
        PERFORM hwpx_agent.request_artifact_deletion_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'f4000000-0000-0000-0000-000000000010',
            'fb000000-0000-0000-0000-000000000003', 'policy_expiry'
        );
        RAISE EXCEPTION 'assertion 16 unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'RETENTION_NOT_DUE' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 17: an artifact referenced by another project cannot be tombstoned.
    BEGIN
        PERFORM hwpx_agent.request_artifact_deletion_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'f4000000-0000-0000-0000-000000000007',
            'fb000000-0000-0000-0000-000000000004', 'user_delete'
        );
        RAISE EXCEPTION 'assertion 17 unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'RETENTION_ARTIFACT_SHARED' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 18: a project-wide hold blocks all project artifact deletion requests.
    PERFORM hwpx_agent.create_legal_hold_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f9000000-0000-0000-0000-000000000004', NULL, 'PROJECT_WIDE_HOLD'
    );
    BEGIN
        PERFORM hwpx_agent.request_artifact_deletion_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'f4000000-0000-0000-0000-000000000010',
            'fb000000-0000-0000-0000-000000000005', 'user_delete'
        );
        RAISE EXCEPTION 'assertion 18 unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'RETENTION_LEGAL_HOLD_ACTIVE' THEN RAISE; END IF;
    END;
    PERFORM hwpx_agent.release_legal_hold_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f9000000-0000-0000-0000-000000000004'
    );
    v_assertions := v_assertions + 1;

    -- 19: a hold cannot be attached through a project that does not reference the artifact.
    BEGIN
        PERFORM hwpx_agent.create_legal_hold_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'f9000000-0000-0000-0000-000000000005',
            'f4000000-0000-0000-0000-000000000012', 'WRONG_PROJECT_HOLD'
        );
        RAISE EXCEPTION 'assertion 19 unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'RETENTION_RESOURCE_NOT_FOUND' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 20: forced RLS hides tenant A state under tenant B context.
    PERFORM set_config('hwpx_agent.tenant_id',
        'f1000000-0000-0000-0000-000000000002', true);
    SELECT count(*) INTO v_count FROM hwpx_agent.artifact_deletion_requests;
    IF v_count <> 0 THEN RAISE EXCEPTION 'assertion 20 failed'; END IF;
    PERFORM set_config('hwpx_agent.tenant_id',
        'f1000000-0000-0000-0000-000000000001', true);
    v_assertions := v_assertions + 1;

    -- 21: invalid observed head registration is rejected without a mirror row.
    BEGIN
        PERFORM hwpx_agent.register_local_mirror_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'f8000000-0000-0000-0000-000000000099', repeat('9', 64),
            'f3000000-0000-0000-0000-000000000001',
            'f5000000-0000-0000-0000-000000000002', 2, repeat('9', 64)
        );
        RAISE EXCEPTION 'assertion 21 unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'MIRROR_REMOTE_HEAD_CONFLICT' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 22: exact mirror registration, local plan queue, and push reservation succeed.
    PERFORM hwpx_agent.register_local_mirror_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000001', repeat('1', 64),
        'f3000000-0000-0000-0000-000000000001',
        'f5000000-0000-0000-0000-000000000003', 3, repeat('2', 64)
    );
    PERFORM hwpx_agent.queue_local_mirror_plan_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000001', repeat('3', 64), repeat('a', 64)
    );
    SELECT hwpx_agent.begin_local_mirror_push_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000001',
        'f6000000-0000-0000-0000-000000000004',
        'fa000000-0000-0000-0000-000000000004', 300
    ) INTO v_text;
    IF v_text <> 'prepared' THEN RAISE EXCEPTION 'assertion 22 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 23: only the matching revision-CAS receipt and plan can complete the mirror push.
    SELECT outcome INTO v_outcome FROM pg_temp.seed_remote_commit(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001',
        'f3000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f6000000-0000-0000-0000-000000000004',
        'f5000000-0000-0000-0000-000000000003', 3,
        'f5000000-0000-0000-0000-000000000004',
        ARRAY['f5000000-0000-0000-0000-000000000003']::uuid[],
        'f4000000-0000-0000-0000-000000000014',
        'f4000000-0000-0000-0000-000000000015',
        'f4000000-0000-0000-0000-000000000016',
        repeat('a', 64), 'verified', repeat('b', 64), repeat('c', 64),
        repeat('d', 64), repeat('e', 64)
    );
    PERFORM hwpx_agent.complete_local_mirror_push_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000001',
        'f6000000-0000-0000-0000-000000000004',
        'f5000000-0000-0000-0000-000000000004'
    );
    IF v_outcome <> 'committed' OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.project_local_mirrors
        WHERE mirror_id = 'f8000000-0000-0000-0000-000000000001'
          AND state = 'clean' AND observed_generation = 4
          AND pending_plan_sha256 IS NULL AND active_push_id IS NULL
    ) THEN RAISE EXCEPTION 'assertion 23 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- Register two mirrors at generation four before the next remote advance.
    PERFORM hwpx_agent.register_local_mirror_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000002', repeat('2', 64),
        'f3000000-0000-0000-0000-000000000001',
        'f5000000-0000-0000-0000-000000000004', 4, repeat('4', 64)
    );
    PERFORM hwpx_agent.register_local_mirror_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000003', repeat('3', 64),
        'f3000000-0000-0000-0000-000000000001',
        'f5000000-0000-0000-0000-000000000004', 4, repeat('5', 64)
    );

    -- 24: a CAS with a different operation plan cannot be acknowledged by the mirror.
    PERFORM hwpx_agent.queue_local_mirror_plan_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000002', repeat('6', 64), repeat('b', 64)
    );
    PERFORM hwpx_agent.begin_local_mirror_push_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000002',
        'f6000000-0000-0000-0000-000000000005',
        'fa000000-0000-0000-0000-000000000005', 300
    );
    SELECT outcome INTO v_outcome FROM pg_temp.seed_remote_commit(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001',
        'f3000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f6000000-0000-0000-0000-000000000005',
        'f5000000-0000-0000-0000-000000000004', 4,
        'f5000000-0000-0000-0000-000000000005',
        ARRAY['f5000000-0000-0000-0000-000000000004']::uuid[],
        'f4000000-0000-0000-0000-000000000017',
        'f4000000-0000-0000-0000-000000000018',
        'f4000000-0000-0000-0000-000000000019',
        repeat('c', 64), 'verified', repeat('d', 64), repeat('e', 64),
        repeat('f', 64), repeat('0', 64)
    );
    BEGIN
        PERFORM hwpx_agent.complete_local_mirror_push_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'f8000000-0000-0000-0000-000000000002',
            'f6000000-0000-0000-0000-000000000005',
            'f5000000-0000-0000-0000-000000000005'
        );
        RAISE EXCEPTION 'assertion 24 unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'MIRROR_PLAN_MISMATCH' THEN RAISE; END IF;
    END;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.project_local_mirrors
        WHERE mirror_id = 'f8000000-0000-0000-0000-000000000002'
          AND state = 'push_prepared' AND observed_generation = 4
    ) THEN RAISE EXCEPTION 'assertion 24 state failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 25: a stale mirror becomes an explicit conflict without overwriting the remote head.
    PERFORM hwpx_agent.queue_local_mirror_plan_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000003', repeat('7', 64), repeat('d', 64)
    );
    SELECT hwpx_agent.begin_local_mirror_push_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000003',
        'f6000000-0000-0000-0000-000000000013',
        'fa000000-0000-0000-0000-000000000013', 300
    ) INTO v_text;
    IF v_text <> 'conflict' OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.local_mirror_conflicts
        WHERE conflict_id = 'fa000000-0000-0000-0000-000000000013'
          AND observed_generation = 4 AND current_generation = 5
    ) OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.branches
        WHERE branch_id = 'f3000000-0000-0000-0000-000000000001'
          AND head_revision_id = 'f5000000-0000-0000-0000-000000000005'
          AND head_generation = 5
    ) THEN RAISE EXCEPTION 'assertion 25 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 26: rebase resolution updates the observed head once and cannot be replayed.
    SELECT hwpx_agent.resolve_local_mirror_conflict_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'fa000000-0000-0000-0000-000000000013', 'rebase_operation_plan', NULL
    ) INTO v_text;
    BEGIN
        PERFORM hwpx_agent.resolve_local_mirror_conflict_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'fa000000-0000-0000-0000-000000000013', 'manual_merge', NULL
        );
        RAISE EXCEPTION 'assertion 26 replay unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'MIRROR_CONFLICT_ALREADY_RESOLVED' THEN RAISE; END IF;
    END;
    IF v_text <> 'ahead' OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.project_local_mirrors
        WHERE mirror_id = 'f8000000-0000-0000-0000-000000000003'
          AND state = 'ahead' AND observed_generation = 5
    ) THEN RAISE EXCEPTION 'assertion 26 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 27: branch resolution moves the pending plan to an exact alternate branch head.
    PERFORM hwpx_agent.register_local_mirror_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000004', repeat('4', 64),
        'f3000000-0000-0000-0000-000000000001',
        'f5000000-0000-0000-0000-000000000005', 5, repeat('8', 64)
    );
    PERFORM hwpx_agent.queue_local_mirror_plan_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000004', repeat('9', 64), repeat('e', 64)
    );
    SELECT outcome INTO v_outcome FROM pg_temp.seed_remote_commit(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001',
        'f3000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f6000000-0000-0000-0000-000000000006',
        'f5000000-0000-0000-0000-000000000005', 5,
        'f5000000-0000-0000-0000-000000000006',
        ARRAY['f5000000-0000-0000-0000-000000000005']::uuid[],
        'f4000000-0000-0000-0000-000000000020',
        'f4000000-0000-0000-0000-000000000021',
        'f4000000-0000-0000-0000-000000000022',
        repeat('5', 64), 'verified', repeat('6', 64), repeat('7', 64),
        repeat('8', 64), repeat('9', 64)
    );
    PERFORM hwpx_agent.begin_local_mirror_push_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000004',
        'f6000000-0000-0000-0000-000000000014',
        'fa000000-0000-0000-0000-000000000014', 300
    );
    SELECT hwpx_agent.resolve_local_mirror_conflict_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'fa000000-0000-0000-0000-000000000014', 'branch',
        'f3000000-0000-0000-0000-000000000002'
    ) INTO v_text;
    IF v_text <> 'ahead' OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.project_local_mirrors
        WHERE mirror_id = 'f8000000-0000-0000-0000-000000000004'
          AND branch_id = 'f3000000-0000-0000-0000-000000000002'
          AND observed_revision_id IS NULL AND observed_generation = 0
    ) THEN RAISE EXCEPTION 'assertion 27 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 28: manual resolution preserves the local base and requires explicit merge work.
    PERFORM hwpx_agent.register_local_mirror_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000005', repeat('5', 64),
        'f3000000-0000-0000-0000-000000000001',
        'f5000000-0000-0000-0000-000000000006', 6, repeat('a', 64)
    );
    PERFORM hwpx_agent.queue_local_mirror_plan_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000005', repeat('b', 64), repeat('f', 64)
    );
    SELECT outcome INTO v_outcome FROM pg_temp.seed_remote_commit(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001',
        'f3000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f6000000-0000-0000-0000-000000000007',
        'f5000000-0000-0000-0000-000000000006', 6,
        'f5000000-0000-0000-0000-000000000007',
        ARRAY['f5000000-0000-0000-0000-000000000006']::uuid[],
        'f4000000-0000-0000-0000-000000000023',
        'f4000000-0000-0000-0000-000000000024',
        'f4000000-0000-0000-0000-000000000025',
        repeat('6', 64), 'verified', repeat('5', 64), repeat('4', 64),
        repeat('3', 64), repeat('2', 64)
    );
    PERFORM hwpx_agent.begin_local_mirror_push_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000005',
        'f6000000-0000-0000-0000-000000000015',
        'fa000000-0000-0000-0000-000000000015', 300
    );
    SELECT hwpx_agent.resolve_local_mirror_conflict_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'fa000000-0000-0000-0000-000000000015', 'manual_merge', NULL
    ) INTO v_text;
    IF v_text <> 'manual_merge_required' OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.project_local_mirrors
        WHERE mirror_id = 'f8000000-0000-0000-0000-000000000005'
          AND state = 'manual_merge_required' AND observed_generation = 6
    ) THEN RAISE EXCEPTION 'assertion 28 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 29: an expired push reservation can be reclaimed with a new fenced push id.
    PERFORM hwpx_agent.register_local_mirror_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000006', repeat('6', 64),
        'f3000000-0000-0000-0000-000000000001',
        'f5000000-0000-0000-0000-000000000007', 7, repeat('c', 64)
    );
    PERFORM hwpx_agent.queue_local_mirror_plan_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000006', repeat('d', 64), repeat('0', 64)
    );
    PERFORM hwpx_agent.begin_local_mirror_push_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000006',
        'f6000000-0000-0000-0000-000000000020',
        'fa000000-0000-0000-0000-000000000020', 1
    );
    PERFORM pg_sleep(1.1);
    BEGIN
        PERFORM hwpx_agent.begin_local_mirror_push_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'f8000000-0000-0000-0000-000000000006',
            'f6000000-0000-0000-0000-000000000020',
            'fa000000-0000-0000-0000-000000000021', 300
        );
        RAISE EXCEPTION 'assertion 29 reused expired push id unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'MIRROR_PUSH_ID_CONFLICT' THEN RAISE; END IF;
    END;
    SELECT hwpx_agent.begin_local_mirror_push_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000006',
        'f6000000-0000-0000-0000-000000000021',
        'fa000000-0000-0000-0000-000000000021', 300
    ) INTO v_text;
    IF v_text <> 'prepared' OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.project_local_mirrors
        WHERE mirror_id = 'f8000000-0000-0000-0000-000000000006'
          AND active_push_id = 'f6000000-0000-0000-0000-000000000021'
          AND active_push_subject_sha256 = repeat('a', 64)
    ) THEN RAISE EXCEPTION 'assertion 29 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 30: branch generations and active push identities are reserved exactly once.
    PERFORM hwpx_agent.register_local_mirror_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000007', repeat('7', 64),
        'f3000000-0000-0000-0000-000000000001',
        'f5000000-0000-0000-0000-000000000007', 7, repeat('e', 64)
    );
    PERFORM hwpx_agent.queue_local_mirror_plan_v1(
        'f1000000-0000-0000-0000-000000000001',
        'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'f8000000-0000-0000-0000-000000000007', repeat('f', 64), repeat('1', 64)
    );
    BEGIN
        PERFORM hwpx_agent.begin_local_mirror_push_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'f8000000-0000-0000-0000-000000000007',
            'f6000000-0000-0000-0000-000000000022',
            'fa000000-0000-0000-0000-000000000022', 300
        );
        RAISE EXCEPTION 'assertion 30 unexpectedly succeeded';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;
    BEGIN
        PERFORM hwpx_agent.begin_local_mirror_push_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'f8000000-0000-0000-0000-000000000004',
            'f6000000-0000-0000-0000-000000000021',
            'fa000000-0000-0000-0000-000000000023', 300
        );
        RAISE EXCEPTION 'assertion 30 duplicate push id unexpectedly succeeded';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;
    v_assertions := v_assertions + 1;

    -- 31: another editor cannot complete a reservation created by the owner.
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('c', 64), true);
    BEGIN
        PERFORM hwpx_agent.complete_local_mirror_push_v1(
            'f1000000-0000-0000-0000-000000000001',
            'f2000000-0000-0000-0000-000000000001', repeat('c', 64),
            'f8000000-0000-0000-0000-000000000006',
            'f6000000-0000-0000-0000-000000000021',
            'f5000000-0000-0000-0000-000000000007'
        );
        RAISE EXCEPTION 'assertion 31 unexpectedly succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'MIRROR_PUSH_STALE' THEN RAISE; END IF;
    END;
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);
    v_assertions := v_assertions + 1;

    -- 32: mirror metadata contains only opaque ids and digests, never a local path.
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'hwpx_agent'
          AND table_name IN ('project_local_mirrors', 'local_mirror_conflicts')
          AND column_name ~ '(path|filename|object_key|machine_name|user_name)'
    ) THEN RAISE EXCEPTION 'assertion 32 failed'; END IF;
    v_assertions := v_assertions + 1;

    IF v_assertions <> 32 THEN RAISE EXCEPTION 'assertion count mismatch'; END IF;
    RAISE NOTICE 'P14_RETENTION_LOCAL_MIRROR_SMOKE_PASS assertions=%', v_assertions;
END
$$;

SET CONSTRAINTS ALL IMMEDIATE;
SELECT 'P14_RETENTION_LOCAL_MIRROR_SMOKE_PASS assertions=32';
ROLLBACK;
