BEGIN;

INSERT INTO hwpx_agent.tenants (tenant_id, slug)
VALUES
    ('d1000000-0000-0000-0000-000000000001', 'history-primary'),
    ('e1000000-0000-0000-0000-000000000001', 'history-other');

INSERT INTO hwpx_agent.projects (
    tenant_id, project_id, slug, display_name, target_profile_id,
    retention_policy_id
) VALUES (
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001',
    'history-project', 'History Project', 'hancom-hangul-2020-secondary',
    'retention.local-test'
);

INSERT INTO hwpx_agent.project_acl (
    tenant_id, project_id, subject_sha256, role
) VALUES
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64), 'owner'
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('b', 64), 'reader'
    );

INSERT INTO hwpx_agent.artifacts (
    tenant_id, artifact_id, content_sha256, size_bytes, media_type,
    artifact_kind, storage_state, encryption_key_ref
)
SELECT
    'd1000000-0000-0000-0000-000000000001'::uuid,
    ('d4000000-0000-0000-0000-' || lpad(value::text, 12, '0'))::uuid,
    lpad(to_hex(value), 64, '0'), value,
    'application/octet-stream',
    CASE WHEN value IN (7, 8) THEN 'diff' ELSE 'result' END,
    'staged', 'kms.history-test'
FROM generate_series(1, 8) AS value;

INSERT INTO hwpx_agent.revisions (
    tenant_id, project_id, revision_id, source_artifact_id,
    result_artifact_id, semantic_diff_artifact_id, operation_plan_sha256,
    validation_state, validation_summary_sha256, created_by_subject_sha256
) VALUES
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000001',
        'd4000000-0000-0000-0000-000000000001',
        'd4000000-0000-0000-0000-000000000002', NULL,
        repeat('1', 64), 'verified', repeat('2', 64), repeat('a', 64)
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000002',
        'd4000000-0000-0000-0000-000000000001',
        'd4000000-0000-0000-0000-000000000003',
        'd4000000-0000-0000-0000-000000000007',
        repeat('3', 64), 'verified', repeat('4', 64), repeat('a', 64)
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000003',
        'd4000000-0000-0000-0000-000000000001',
        'd4000000-0000-0000-0000-000000000004', NULL,
        repeat('5', 64), 'verified', repeat('6', 64), repeat('a', 64)
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000004',
        'd4000000-0000-0000-0000-000000000001',
        'd4000000-0000-0000-0000-000000000005',
        'd4000000-0000-0000-0000-000000000008',
        repeat('7', 64), 'verified', repeat('8', 64), repeat('a', 64)
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000005',
        'd4000000-0000-0000-0000-000000000001',
        'd4000000-0000-0000-0000-000000000006', NULL,
        repeat('9', 64), 'verified', repeat('0', 64), repeat('a', 64)
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000006',
        'd4000000-0000-0000-0000-000000000001',
        'd4000000-0000-0000-0000-000000000002', NULL,
        repeat('a', 64), 'verified', repeat('b', 64), repeat('a', 64)
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000007',
        'd4000000-0000-0000-0000-000000000001',
        'd4000000-0000-0000-0000-000000000003', NULL,
        repeat('c', 64), 'verified', repeat('d', 64), repeat('a', 64)
    );

INSERT INTO hwpx_agent.revision_parents (
    tenant_id, project_id, revision_id, parent_revision_id, parent_ordinal
) VALUES
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000002',
        'd5000000-0000-0000-0000-000000000001', 0
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000003',
        'd5000000-0000-0000-0000-000000000001', 0
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000004',
        'd5000000-0000-0000-0000-000000000002', 0
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000004',
        'd5000000-0000-0000-0000-000000000003', 1
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000006',
        'd5000000-0000-0000-0000-000000000005', 0
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000007',
        'd5000000-0000-0000-0000-000000000004', 0
    );

INSERT INTO hwpx_agent.revision_graph_seals (
    tenant_id, project_id, revision_id, seal_kind, parent_count,
    committed_generation, commit_id, commit_request_sha256,
    transaction_receipt_sha256
) VALUES
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000001', 'service_v1', 0, 1,
        'd6000000-0000-0000-0000-000000000001', repeat('1', 64), repeat('2', 64)
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000002', 'service_v1', 1, 2,
        'd6000000-0000-0000-0000-000000000002', repeat('3', 64), repeat('4', 64)
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000003', 'service_v1', 1, 2,
        'd6000000-0000-0000-0000-000000000003', repeat('5', 64), repeat('6', 64)
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000004', 'service_v1', 2, 3,
        'd6000000-0000-0000-0000-000000000004', repeat('7', 64), repeat('8', 64)
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000005', 'legacy_unqualified', 0,
        NULL, NULL, NULL, NULL
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000006', 'service_v1', 1, 1,
        'd6000000-0000-0000-0000-000000000006', repeat('a', 64), repeat('b', 64)
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000007', 'service_v1', 1, 2,
        'd6000000-0000-0000-0000-000000000007', repeat('c', 64), repeat('d', 64)
    );

UPDATE hwpx_agent.projects
SET head_revision_id = 'd5000000-0000-0000-0000-000000000004',
    head_generation = 3
WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
  AND project_id = 'd2000000-0000-0000-0000-000000000001';

INSERT INTO hwpx_agent.branches (
    tenant_id, project_id, branch_id, name, head_revision_id,
    head_generation, is_default, created_by_subject_sha256
) VALUES (
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001',
    'd3000000-0000-0000-0000-000000000001', 'main',
    'd5000000-0000-0000-0000-000000000004', 3, true, repeat('a', 64)
);

SELECT set_config(
    'hwpx_agent.tenant_id', 'd1000000-0000-0000-0000-000000000001', true
);
SELECT set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);

DO $$
DECLARE
    v_assertions integer := 0;
    v_count integer;
    v_value text;
    v_uuid uuid;
BEGIN
    -- assertion 01: bounded first page contains exactly two rows.
    SELECT count(*) INTO v_count
    FROM hwpx_agent.query_revision_history(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd5000000-0000-0000-0000-000000000004', 3, NULL, NULL, 2
    );
    IF v_count <> 2 THEN RAISE EXCEPTION 'assertion 01 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- assertion 02: snapshot head is first in the deterministic page.
    SELECT revision_id INTO v_uuid
    FROM hwpx_agent.query_revision_history(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd5000000-0000-0000-0000-000000000004', 3, NULL, NULL, 2
    ) LIMIT 1;
    IF v_uuid <> 'd5000000-0000-0000-0000-000000000004'::uuid THEN
        RAISE EXCEPTION 'assertion 02 failed';
    END IF;
    v_assertions := v_assertions + 1;

    -- assertion 03: keyset continuation returns the remaining two unique rows.
    SELECT count(*) INTO v_count
    FROM hwpx_agent.query_revision_history(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd5000000-0000-0000-0000-000000000004', 3,
        2, 'd5000000-0000-0000-0000-000000000002', 100
    );
    IF v_count <> 2 THEN RAISE EXCEPTION 'assertion 03 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- assertion 04: full reachable set is exactly the four-node merge DAG.
    SELECT count(DISTINCT revision_id) INTO v_count
    FROM hwpx_agent.query_revision_history(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd5000000-0000-0000-0000-000000000004', 3, NULL, NULL, 100
    );
    IF v_count <> 4 THEN RAISE EXCEPTION 'assertion 04 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- assertion 05: parent ordinal is preserved for the merge node.
    SELECT array_to_string(parent_revision_ids, ',') INTO v_value
    FROM hwpx_agent.query_revision_history(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd5000000-0000-0000-0000-000000000004', 3, NULL, NULL, 1
    );
    IF v_value <> 'd5000000-0000-0000-0000-000000000002,d5000000-0000-0000-0000-000000000003' THEN
        RAISE EXCEPTION 'assertion 05 failed';
    END IF;
    v_assertions := v_assertions + 1;

    -- assertion 06: reader is authorized for the read-only history query.
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('b', 64), true);
    SELECT count(*) INTO v_count
    FROM hwpx_agent.query_revision_history(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('b', 64),
        'd5000000-0000-0000-0000-000000000004', 3, NULL, NULL, 1
    );
    IF v_count <> 1 THEN RAISE EXCEPTION 'assertion 06 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- assertion 07: an unlisted subject is hidden as project absence.
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('c', 64), true);
    BEGIN
        PERFORM * FROM hwpx_agent.query_revision_history(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('c', 64),
            'd5000000-0000-0000-0000-000000000004', 3, NULL, NULL, 1
        );
        RAISE EXCEPTION 'assertion 07 expected failure';
    EXCEPTION WHEN no_data_found THEN NULL;
    END;
    v_assertions := v_assertions + 1;

    -- assertion 08: a mismatched tenant context is denied.
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);
    PERFORM set_config('hwpx_agent.tenant_id', 'e1000000-0000-0000-0000-000000000001', true);
    BEGIN
        PERFORM * FROM hwpx_agent.query_revision_history(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'd5000000-0000-0000-0000-000000000004', 3, NULL, NULL, 1
        );
        RAISE EXCEPTION 'assertion 08 expected failure';
    EXCEPTION WHEN insufficient_privilege THEN NULL;
    END;
    v_assertions := v_assertions + 1;
    PERFORM set_config('hwpx_agent.tenant_id', 'd1000000-0000-0000-0000-000000000001', true);

    -- assertion 09: page sizes above the contract limit are rejected.
    BEGIN
        PERFORM * FROM hwpx_agent.query_revision_history(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'd5000000-0000-0000-0000-000000000004', 3, NULL, NULL, 101
        );
        RAISE EXCEPTION 'assertion 09 expected failure';
    EXCEPTION WHEN invalid_parameter_value THEN NULL;
    END;
    v_assertions := v_assertions + 1;

    -- assertion 10: legacy nodes cannot anchor or hide inside a qualified history.
    BEGIN
        PERFORM * FROM hwpx_agent.query_revision_history(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'd5000000-0000-0000-0000-000000000005', 1, NULL, NULL, 1
        );
        RAISE EXCEPTION 'assertion 10 expected failure';
    EXCEPTION WHEN no_data_found THEN NULL;
    END;
    BEGIN
        PERFORM * FROM hwpx_agent.query_revision_history(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'd5000000-0000-0000-0000-000000000006', 1, NULL, NULL, 10
        );
        RAISE EXCEPTION 'assertion 10 expected hidden-parent failure';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN
        IF SQLERRM <> 'HISTORY_LEGACY_REVISION_UNQUALIFIED' THEN RAISE; END IF;
    END;
    BEGIN
        PERFORM * FROM hwpx_agent.query_revision_history(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'd5000000-0000-0000-0000-000000000007', 2, NULL, NULL, 10
        );
        RAISE EXCEPTION 'assertion 10 expected generation failure';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN
        IF SQLERRM <> 'HISTORY_GRAPH_GENERATION_INVALID' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- assertion 11: owner creates one immutable checkpoint.
    SELECT outcome INTO v_value
    FROM hwpx_agent.create_history_checkpoint(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000001', repeat('d', 64),
        'd8000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000002', 'Reviewed baseline'
    );
    IF v_value <> 'created' THEN RAISE EXCEPTION 'assertion 11 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- assertion 12: the exact idempotency retry replays the same result.
    SELECT outcome INTO v_value
    FROM hwpx_agent.create_history_checkpoint(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000001', repeat('d', 64),
        'd8000000-0000-0000-0000-000000000001',
        'd5000000-0000-0000-0000-000000000002', 'Reviewed baseline'
    );
    IF v_value <> 'replayed' THEN RAISE EXCEPTION 'assertion 12 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- assertion 13: replay produced one claim and one checkpoint only.
    SELECT count(*) INTO v_count
    FROM hwpx_agent.history_checkpoint_requests AS request
    JOIN hwpx_agent.checkpoints AS checkpoint
      ON checkpoint.tenant_id = request.tenant_id
     AND checkpoint.project_id = request.project_id
     AND checkpoint.checkpoint_id = request.checkpoint_id
    WHERE request.tenant_id = 'd1000000-0000-0000-0000-000000000001'
      AND request.project_id = 'd2000000-0000-0000-0000-000000000001';
    IF v_count <> 1 THEN RAISE EXCEPTION 'assertion 13 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- assertion 14: idempotency request drift is rejected.
    BEGIN
        PERFORM * FROM hwpx_agent.create_history_checkpoint(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'd7000000-0000-0000-0000-000000000001', repeat('e', 64),
            'd8000000-0000-0000-0000-000000000002',
            'd5000000-0000-0000-0000-000000000001', 'Drifted request'
        );
        RAISE EXCEPTION 'assertion 14 expected failure';
    EXCEPTION WHEN serialization_failure THEN NULL;
    END;
    v_assertions := v_assertions + 1;

    -- assertion 15: reader cannot create checkpoints.
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('b', 64), true);
    BEGIN
        PERFORM * FROM hwpx_agent.create_history_checkpoint(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('b', 64),
            'd7000000-0000-0000-0000-000000000002', repeat('f', 64),
            'd8000000-0000-0000-0000-000000000002',
            'd5000000-0000-0000-0000-000000000001', 'Reader denied'
        );
        RAISE EXCEPTION 'assertion 15 expected failure';
    EXCEPTION WHEN insufficient_privilege THEN NULL;
    END;
    v_assertions := v_assertions + 1;
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);

    -- assertion 16: a second request cannot reuse an immutable label.
    BEGIN
        PERFORM * FROM hwpx_agent.create_history_checkpoint(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'd7000000-0000-0000-0000-000000000002', repeat('f', 64),
            'd8000000-0000-0000-0000-000000000002',
            'd5000000-0000-0000-0000-000000000001', 'Reviewed baseline'
        );
        RAISE EXCEPTION 'assertion 16 expected failure';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;
    v_assertions := v_assertions + 1;

    -- assertion 17: checkpoint rows remain immutable.
    BEGIN
        UPDATE hwpx_agent.checkpoints SET label = 'Changed'
        WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
          AND project_id = 'd2000000-0000-0000-0000-000000000001'
          AND checkpoint_id = 'd8000000-0000-0000-0000-000000000001';
        RAISE EXCEPTION 'assertion 17 expected failure';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL;
    END;
    v_assertions := v_assertions + 1;

    -- assertion 18: owner creates a branch at the qualified revision generation.
    SELECT head_generation INTO v_count
    FROM hwpx_agent.create_history_branch(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd3000000-0000-0000-0000-000000000002', 'review/baseline',
        'd5000000-0000-0000-0000-000000000002', repeat('1', 64)
    );
    IF v_count <> 2 THEN RAISE EXCEPTION 'assertion 18 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- assertion 19: branch name uniqueness is enforced.
    BEGIN
        PERFORM * FROM hwpx_agent.create_history_branch(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'd3000000-0000-0000-0000-000000000003', 'review/baseline',
            'd5000000-0000-0000-0000-000000000001', repeat('2', 64)
        );
        RAISE EXCEPTION 'assertion 19 expected failure';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;
    v_assertions := v_assertions + 1;

    -- assertion 20: reader cannot create branches.
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('b', 64), true);
    BEGIN
        PERFORM * FROM hwpx_agent.create_history_branch(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('b', 64),
            'd3000000-0000-0000-0000-000000000004', 'reader/denied',
            'd5000000-0000-0000-0000-000000000001', repeat('3', 64)
        );
        RAISE EXCEPTION 'assertion 20 expected failure';
    EXCEPTION WHEN insufficient_privilege THEN NULL;
    END;
    v_assertions := v_assertions + 1;
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);

    -- assertion 21: an unqualified revision cannot be used as a branch head.
    BEGIN
        PERFORM * FROM hwpx_agent.create_history_branch(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'd3000000-0000-0000-0000-000000000005', 'legacy/denied',
            'd5000000-0000-0000-0000-000000000005', repeat('4', 64)
        );
        RAISE EXCEPTION 'assertion 21 expected failure';
    EXCEPTION WHEN no_data_found THEN NULL;
    END;
    v_assertions := v_assertions + 1;

    -- assertion 22: checkpoint label and semantic diff identity are returned together.
    SELECT count(*) INTO v_count
    FROM hwpx_agent.query_revision_history(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd5000000-0000-0000-0000-000000000004', 3, NULL, NULL, 100
    ) AS history
    WHERE history.revision_id = 'd5000000-0000-0000-0000-000000000002'
      AND history.semantic_diff_artifact_id = 'd4000000-0000-0000-0000-000000000007'
      AND history.checkpoint_labels = ARRAY['Reviewed baseline']::text[];
    IF v_count <> 1 THEN RAISE EXCEPTION 'assertion 22 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- assertion 23: the idempotency claim itself is immutable.
    BEGIN
        DELETE FROM hwpx_agent.history_checkpoint_requests
        WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
          AND project_id = 'd2000000-0000-0000-0000-000000000001'
          AND request_id = 'd7000000-0000-0000-0000-000000000001';
        RAISE EXCEPTION 'assertion 23 expected failure';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL;
    END;
    v_assertions := v_assertions + 1;

    -- assertion 24: history checkpoint request storage forces tenant RLS.
    SELECT count(*) INTO v_count
    FROM pg_class AS relation
    JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
    WHERE namespace.nspname = 'hwpx_agent'
      AND relation.relname = 'history_checkpoint_requests'
      AND relation.relrowsecurity
      AND relation.relforcerowsecurity;
    IF v_count <> 1 THEN RAISE EXCEPTION 'assertion 24 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- assertion 25: PUBLIC cannot execute mutation or query functions.
    IF has_function_privilege(
        'public',
        'hwpx_agent.create_history_checkpoint(uuid,uuid,character,uuid,character,uuid,uuid,text)',
        'EXECUTE'
    ) OR has_function_privilege(
        'public',
        'hwpx_agent.create_history_branch(uuid,uuid,character,uuid,text,uuid,character)',
        'EXECUTE'
    ) OR has_function_privilege(
        'public',
        'hwpx_agent.query_revision_history(uuid,uuid,character,uuid,bigint,bigint,uuid,integer)',
        'EXECUTE'
    ) THEN
        RAISE EXCEPTION 'assertion 25 failed';
    END IF;
    v_assertions := v_assertions + 1;

    -- assertion 26: migration version and audit events are durable.
    SELECT count(*) INTO v_count
    FROM hwpx_agent.schema_versions AS version
    WHERE version.version = 4
      AND version.migration_name = 'p14.history_checkpoints_v1'
      AND version.migration_sha256 ~ '^[0-9a-f]{64}$';
    IF v_count <> 1 OR (
        SELECT count(*) FROM hwpx_agent.audit_events
        WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
          AND project_id = 'd2000000-0000-0000-0000-000000000001'
          AND event_type IN ('history.checkpoint_created', 'history.branch_created')
    ) <> 2 THEN
        RAISE EXCEPTION 'assertion 26 failed';
    END IF;
    v_assertions := v_assertions + 1;

    IF v_assertions <> 26 THEN
        RAISE EXCEPTION 'history assertion count drifted: %', v_assertions;
    END IF;
END
$$;

SELECT 'P14_HISTORY_SMOKE_PASS assertions=26';

ROLLBACK;
