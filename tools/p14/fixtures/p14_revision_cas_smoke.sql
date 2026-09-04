BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hwpx_agent_revision_test_app') THEN
        CREATE ROLE hwpx_agent_revision_test_app
            NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
    END IF;
END
$$;

GRANT USAGE ON SCHEMA hwpx_agent TO hwpx_agent_revision_test_app;
GRANT SELECT ON TABLE
    hwpx_agent.projects,
    hwpx_agent.project_acl,
    hwpx_agent.artifacts,
    hwpx_agent.revisions,
    hwpx_agent.revision_parents,
    hwpx_agent.branches,
    hwpx_agent.revision_graph_seals,
    hwpx_agent.revision_commit_receipts,
    hwpx_agent.audit_events
TO hwpx_agent_revision_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.commit_revision_cas(
    uuid, uuid, uuid, character, uuid, uuid, bigint, uuid, uuid[], uuid, uuid, uuid,
    character, text, character, character, character, character
) TO hwpx_agent_revision_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id()
TO hwpx_agent_revision_test_app;

INSERT INTO hwpx_agent.tenants (tenant_id, slug) VALUES
    ('a1000000-0000-0000-0000-000000000001', 'revision-tenant-a'),
    ('a1000000-0000-0000-0000-000000000002', 'revision-tenant-b');
INSERT INTO hwpx_agent.projects (
    tenant_id, project_id, slug, display_name, target_profile_id, retention_policy_id
) VALUES (
    'a1000000-0000-0000-0000-000000000001',
    'a2000000-0000-0000-0000-000000000001',
    'revision-project', 'Revision Project', 'hancom-hangul-2020-secondary',
    'retention.local-test'
);
INSERT INTO hwpx_agent.project_acl (tenant_id, project_id, subject_sha256, role) VALUES
    (
        'a1000000-0000-0000-0000-000000000001',
        'a2000000-0000-0000-0000-000000000001', repeat('a', 64), 'owner'
    ),
    (
        'a1000000-0000-0000-0000-000000000001',
        'a2000000-0000-0000-0000-000000000001', repeat('b', 64), 'reader'
    );
INSERT INTO hwpx_agent.branches (
    tenant_id, project_id, branch_id, name, is_default, created_by_subject_sha256
) VALUES
    (
        'a1000000-0000-0000-0000-000000000001',
        'a2000000-0000-0000-0000-000000000001',
        'a3000000-0000-0000-0000-000000000001', 'main', true, repeat('a', 64)
    ),
    (
        'a1000000-0000-0000-0000-000000000001',
        'a2000000-0000-0000-0000-000000000001',
        'a3000000-0000-0000-0000-000000000002', 'alternate', false, repeat('a', 64)
    );

WITH artifact_seed AS (
    SELECT
        ordinal,
        concat('a4000000-0000-0000-0000-', lpad(ordinal::text, 12, '0'))::uuid AS artifact_id,
        lpad(to_hex(ordinal), 64, '0') AS content_sha256,
        CASE ordinal % 3 WHEN 1 THEN 'source' WHEN 2 THEN 'result' ELSE 'diff' END AS artifact_kind
    FROM generate_series(1, 18) AS ordinal
)
INSERT INTO hwpx_agent.artifacts (
    tenant_id, artifact_id, content_sha256, size_bytes, media_type, artifact_kind,
    storage_state, encryption_key_ref, verified_at, service_metadata_version, filename,
    object_key, encryption_algorithm, encryption_nonce, aad_sha256, ciphertext_sha256,
    validation_state, scanner_engine_ref, scanner_signature_version,
    authorization_generation
)
SELECT
    'a1000000-0000-0000-0000-000000000001',
    artifact_id,
    content_sha256,
    ordinal,
    'application/octet-stream',
    artifact_kind,
    'available',
    'kms.revision-test',
    transaction_timestamp(),
    1,
    concat('artifact-', ordinal, '.bin'),
    concat(
        'artifacts/v1/a1000000000000000000000000000001/', artifact_kind,
        '/available/', content_sha256, '.aes256gcm'
    ),
    'AES-256-GCM',
    decode(lpad(to_hex(ordinal), 24, '0'), 'hex'),
    lpad(to_hex(ordinal + 100), 64, '0'),
    lpad(to_hex(ordinal + 200), 64, '0'),
    'verified',
    'scanner.revision-test',
    'v1',
    1
FROM artifact_seed;

INSERT INTO hwpx_agent.artifact_acl (
    tenant_id, artifact_id, subject_sha256, can_read, can_manage
)
SELECT
    'a1000000-0000-0000-0000-000000000001',
    artifact_id,
    repeat('a', 64),
    true,
    true
FROM hwpx_agent.artifacts
WHERE tenant_id = 'a1000000-0000-0000-0000-000000000001';

COMMIT;

-- assertion 01: version, tables and head-generation columns exist.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 3 AND migration_name = 'p14.revision_cas_v1'
    ) OR NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'hwpx_agent' AND table_name = 'revision_graph_seals'
    ) OR NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'hwpx_agent' AND table_name = 'branches'
          AND column_name = 'head_generation'
    ) THEN
        RAISE EXCEPTION 'revision CAS schema shape differs';
    END IF;
END
$$;

-- assertion 02: the application role has only read plus CAS execute on graph state.
DO $$
BEGIN
    IF has_table_privilege('hwpx_agent_revision_test_app', 'hwpx_agent.revisions', 'INSERT')
       OR has_table_privilege('hwpx_agent_revision_test_app', 'hwpx_agent.branches', 'UPDATE')
       OR NOT has_function_privilege(
            'hwpx_agent_revision_test_app',
            'hwpx_agent.commit_revision_cas(uuid,uuid,uuid,character,uuid,uuid,bigint,uuid,uuid[],uuid,uuid,uuid,character,text,character,character,character,character)',
            'EXECUTE'
       ) THEN
        RAISE EXCEPTION 'revision application privilege boundary differs';
    END IF;
END
$$;

-- assertion 03: a reader subject cannot commit.
DO $$
BEGIN
    PERFORM set_config('hwpx_agent.tenant_id', 'a1000000-0000-0000-0000-000000000001', true);
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('b', 64), true);
    BEGIN
        PERFORM * FROM hwpx_agent.commit_revision_cas(
            'a1000000-0000-0000-0000-000000000001',
            'a2000000-0000-0000-0000-000000000001',
            'a3000000-0000-0000-0000-000000000001', repeat('b', 64),
            'a6000000-0000-0000-0000-000000000099', NULL, 0,
            'a5000000-0000-0000-0000-000000000099', ARRAY[]::uuid[],
            'a4000000-0000-0000-0000-000000000001',
            'a4000000-0000-0000-0000-000000000002',
            'a4000000-0000-0000-0000-000000000003',
            repeat('1', 64), 'verified', repeat('2', 64), repeat('3', 64),
            repeat('0', 63) || 'c', repeat('0', 63) || 'd'
        );
        RAISE EXCEPTION 'reader subject unexpectedly committed';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'REVISION_COMMIT_DENIED' THEN RAISE; END IF;
    END;
END
$$;

-- assertion 04: tenant or subject context mismatch fails before graph lookup.
DO $$
BEGIN
    PERFORM set_config('hwpx_agent.tenant_id', 'a1000000-0000-0000-0000-000000000002', true);
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);
    BEGIN
        PERFORM * FROM hwpx_agent.commit_revision_cas(
            'a1000000-0000-0000-0000-000000000001',
            'a2000000-0000-0000-0000-000000000001',
            'a3000000-0000-0000-0000-000000000001', repeat('a', 64),
            'a6000000-0000-0000-0000-000000000098', NULL, 0,
            'a5000000-0000-0000-0000-000000000098', ARRAY[]::uuid[],
            'a4000000-0000-0000-0000-000000000001',
            'a4000000-0000-0000-0000-000000000002', NULL,
            repeat('1', 64), 'verified', repeat('2', 64), repeat('3', 64),
            repeat('0', 63) || 'e', repeat('0', 63) || 'f'
        );
        RAISE EXCEPTION 'cross-tenant context unexpectedly committed';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'REVISION_CONTEXT_MISMATCH' THEN RAISE; END IF;
    END;
END
$$;

-- assertion 05: only verified output can advance a head.
DO $$
BEGIN
    PERFORM set_config('hwpx_agent.tenant_id', 'a1000000-0000-0000-0000-000000000001', true);
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);
    BEGIN
        PERFORM * FROM hwpx_agent.commit_revision_cas(
            'a1000000-0000-0000-0000-000000000001',
            'a2000000-0000-0000-0000-000000000001',
            'a3000000-0000-0000-0000-000000000001', repeat('a', 64),
            'a6000000-0000-0000-0000-000000000097', NULL, 0,
            'a5000000-0000-0000-0000-000000000097', ARRAY[]::uuid[],
            'a4000000-0000-0000-0000-000000000001',
            'a4000000-0000-0000-0000-000000000002', NULL,
            repeat('1', 64), 'unverified', repeat('2', 64), repeat('3', 64),
            repeat('4', 64), repeat('5', 64)
        );
        RAISE EXCEPTION 'unverified revision unexpectedly committed';
    EXCEPTION WHEN invalid_parameter_value THEN
        IF SQLERRM <> 'REVISION_REQUEST_INVALID' THEN RAISE; END IF;
    END;
END
$$;

BEGIN;
SET LOCAL ROLE hwpx_agent_revision_test_app;
SELECT set_config('hwpx_agent.tenant_id', 'a1000000-0000-0000-0000-000000000001', true);
SELECT set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);
SELECT * FROM hwpx_agent.commit_revision_cas(
    'a1000000-0000-0000-0000-000000000001',
    'a2000000-0000-0000-0000-000000000001',
    'a3000000-0000-0000-0000-000000000001', repeat('a', 64),
    'a6000000-0000-0000-0000-000000000001', NULL, 0,
    'a5000000-0000-0000-0000-000000000001', ARRAY[]::uuid[],
    'a4000000-0000-0000-0000-000000000001',
    'a4000000-0000-0000-0000-000000000002',
    'a4000000-0000-0000-0000-000000000003',
    repeat('1', 64), 'verified', repeat('2', 64), repeat('3', 64),
    repeat('4', 64), repeat('5', 64)
);
COMMIT;

-- assertion 06: root CAS committed exactly generation one.
DO $$
BEGIN
    IF (SELECT head_generation FROM hwpx_agent.branches
        WHERE branch_id = 'a3000000-0000-0000-0000-000000000001') <> 1 THEN
        RAISE EXCEPTION 'root generation differs';
    END IF;
END
$$;

-- assertion 07: default project and branch head are byte-identical mirrors.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.projects AS project
        JOIN hwpx_agent.branches AS branch
          ON branch.tenant_id = project.tenant_id
         AND branch.project_id = project.project_id
        WHERE branch.branch_id = 'a3000000-0000-0000-0000-000000000001'
          AND ROW(project.head_revision_id, project.head_generation)
              = ROW(branch.head_revision_id, branch.head_generation)
          AND project.head_revision_id = 'a5000000-0000-0000-0000-000000000001'
    ) THEN
        RAISE EXCEPTION 'default head mirror differs';
    END IF;
END
$$;

-- assertion 08: root is sealed with no parents and complete service identity.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.revision_graph_seals
        WHERE revision_id = 'a5000000-0000-0000-0000-000000000001'
          AND seal_kind = 'service_v1' AND parent_count = 0
          AND committed_generation = 1
          AND commit_id = 'a6000000-0000-0000-0000-000000000001'
    ) THEN
        RAISE EXCEPTION 'root seal differs';
    END IF;
END
$$;

-- assertion 09: successful commit has one immutable receipt and one audit event.
DO $$
BEGIN
    IF (SELECT count(*) FROM hwpx_agent.revision_commit_receipts
        WHERE committed_revision_id = 'a5000000-0000-0000-0000-000000000001') <> 1
       OR (SELECT count(*) FROM hwpx_agent.audit_events
        WHERE revision_id = 'a5000000-0000-0000-0000-000000000001'
          AND event_type = 'revision.cas_committed') <> 1 THEN
        RAISE EXCEPTION 'root receipt or audit differs';
    END IF;
END
$$;

BEGIN;
SET LOCAL ROLE hwpx_agent_revision_test_app;
SELECT set_config('hwpx_agent.tenant_id', 'a1000000-0000-0000-0000-000000000001', true);
SELECT set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);
SELECT * FROM hwpx_agent.commit_revision_cas(
    'a1000000-0000-0000-0000-000000000001',
    'a2000000-0000-0000-0000-000000000001',
    'a3000000-0000-0000-0000-000000000001', repeat('a', 64),
    'a6000000-0000-0000-0000-000000000002',
    'a5000000-0000-0000-0000-000000000001', 1,
    'a5000000-0000-0000-0000-000000000002',
    ARRAY['a5000000-0000-0000-0000-000000000001']::uuid[],
    'a4000000-0000-0000-0000-000000000004',
    'a4000000-0000-0000-0000-000000000005',
    'a4000000-0000-0000-0000-000000000006',
    repeat('6', 64), 'verified', repeat('7', 64), repeat('8', 64),
    repeat('9', 64), repeat('a', 64)
);
COMMIT;

-- assertion 10: child commit advances once and binds ordinal-zero parent.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.revision_parents
        WHERE revision_id = 'a5000000-0000-0000-0000-000000000002'
          AND parent_revision_id = 'a5000000-0000-0000-0000-000000000001'
          AND parent_ordinal = 0
    ) OR (SELECT head_generation FROM hwpx_agent.branches
        WHERE branch_id = 'a3000000-0000-0000-0000-000000000001') <> 2 THEN
        RAISE EXCEPTION 'child parent or generation differs';
    END IF;
END
$$;

BEGIN;
SET LOCAL ROLE hwpx_agent_revision_test_app;
SELECT set_config('hwpx_agent.tenant_id', 'a1000000-0000-0000-0000-000000000001', true);
SELECT set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);
SELECT * FROM hwpx_agent.commit_revision_cas(
    'a1000000-0000-0000-0000-000000000001',
    'a2000000-0000-0000-0000-000000000001',
    'a3000000-0000-0000-0000-000000000001', repeat('a', 64),
    'a6000000-0000-0000-0000-000000000003',
    'a5000000-0000-0000-0000-000000000001', 1,
    'a5000000-0000-0000-0000-000000000003',
    ARRAY['a5000000-0000-0000-0000-000000000001']::uuid[],
    'a4000000-0000-0000-0000-000000000007',
    'a4000000-0000-0000-0000-000000000008',
    'a4000000-0000-0000-0000-000000000009',
    repeat('b', 64), 'verified', repeat('c', 64), repeat('d', 64),
    repeat('e', 64), repeat('f', 64)
);
COMMIT;

-- assertion 11: stale CAS creates no revision, seal, receipt or audit side effect.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM hwpx_agent.revisions
        WHERE revision_id = 'a5000000-0000-0000-0000-000000000003')
       OR EXISTS (SELECT 1 FROM hwpx_agent.revision_commit_receipts
        WHERE commit_id = 'a6000000-0000-0000-0000-000000000003')
       OR (SELECT head_generation FROM hwpx_agent.branches
        WHERE branch_id = 'a3000000-0000-0000-0000-000000000001') <> 2 THEN
        RAISE EXCEPTION 'stale CAS had a side effect';
    END IF;
END
$$;

-- assertion 12: absent or non-available artifacts reject before mutation.
DO $$
BEGIN
    PERFORM set_config('hwpx_agent.tenant_id', 'a1000000-0000-0000-0000-000000000001', true);
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);
    BEGIN
        PERFORM * FROM hwpx_agent.commit_revision_cas(
            'a1000000-0000-0000-0000-000000000001',
            'a2000000-0000-0000-0000-000000000001',
            'a3000000-0000-0000-0000-000000000001', repeat('a', 64),
            'a6000000-0000-0000-0000-000000000012',
            'a5000000-0000-0000-0000-000000000002', 2,
            'a5000000-0000-0000-0000-000000000012',
            ARRAY['a5000000-0000-0000-0000-000000000002']::uuid[],
            'a4000000-0000-0000-0000-999999999999',
            'a4000000-0000-0000-0000-000000000011', NULL,
            repeat('1', 64), 'verified', repeat('2', 64), repeat('3', 64),
            repeat('0', 63) || '1', repeat('0', 63) || '2'
        );
        RAISE EXCEPTION 'absent artifact unexpectedly committed';
    EXCEPTION WHEN foreign_key_violation THEN
        IF SQLERRM <> 'REVISION_ARTIFACT_UNAVAILABLE' THEN RAISE; END IF;
    END;
END
$$;

-- assertion 13: duplicate parent identity is rejected.
DO $$
BEGIN
    PERFORM set_config('hwpx_agent.tenant_id', 'a1000000-0000-0000-0000-000000000001', true);
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);
    BEGIN
        PERFORM * FROM hwpx_agent.commit_revision_cas(
            'a1000000-0000-0000-0000-000000000001',
            'a2000000-0000-0000-0000-000000000001',
            'a3000000-0000-0000-0000-000000000001', repeat('a', 64),
            'a6000000-0000-0000-0000-000000000013',
            'a5000000-0000-0000-0000-000000000002', 2,
            'a5000000-0000-0000-0000-000000000013',
            ARRAY[
                'a5000000-0000-0000-0000-000000000002',
                'a5000000-0000-0000-0000-000000000002'
            ]::uuid[],
            'a4000000-0000-0000-0000-000000000010',
            'a4000000-0000-0000-0000-000000000011', NULL,
            repeat('1', 64), 'verified', repeat('2', 64), repeat('3', 64),
            repeat('0', 63) || '3', repeat('0', 63) || '4'
        );
        RAISE EXCEPTION 'duplicate parents unexpectedly committed';
    EXCEPTION WHEN invalid_parameter_value THEN
        IF SQLERRM <> 'REVISION_PARENT_SET_INVALID' THEN RAISE; END IF;
    END;
END
$$;

-- assertion 14: a sealed node cannot receive a late parent edge.
DO $$
BEGIN
    BEGIN
        INSERT INTO hwpx_agent.revision_parents (
            tenant_id, project_id, revision_id, parent_revision_id, parent_ordinal
        ) VALUES (
            'a1000000-0000-0000-0000-000000000001',
            'a2000000-0000-0000-0000-000000000001',
            'a5000000-0000-0000-0000-000000000001',
            'a5000000-0000-0000-0000-000000000002', 0
        );
        RAISE EXCEPTION 'sealed root unexpectedly accepted a parent';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN
        IF SQLERRM <> 'REVISION_GRAPH_SEALED' THEN RAISE; END IF;
    END;
END
$$;

-- assertion 15: cross-tenant RLS exposes no revision rows to the application role.
BEGIN;
SET LOCAL ROLE hwpx_agent_revision_test_app;
SELECT set_config('hwpx_agent.tenant_id', 'a1000000-0000-0000-0000-000000000002', true);
DO $$
BEGIN
    IF (SELECT count(*) FROM hwpx_agent.revisions) <> 0 THEN
        RAISE EXCEPTION 'cross-tenant revision rows were visible';
    END IF;
END
$$;
COMMIT;

-- assertion 16: tenant and subject settings are transaction-local and cleared on commit.
DO $$
BEGIN
    IF nullif(current_setting('hwpx_agent.tenant_id', true), '') IS NOT NULL
       OR nullif(current_setting('hwpx_agent.subject_sha256', true), '') IS NOT NULL THEN
        RAISE EXCEPTION 'revision request context leaked beyond transaction';
    END IF;
END
$$;

-- assertion 17: committed revision rows remain immutable.
DO $$
BEGIN
    BEGIN
        UPDATE hwpx_agent.revisions SET validation_state = 'partial'
        WHERE revision_id = 'a5000000-0000-0000-0000-000000000001';
        RAISE EXCEPTION 'immutable revision unexpectedly changed';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN
        IF SQLERRM <> 'immutable metadata row cannot be updated or deleted' THEN RAISE; END IF;
    END;
END
$$;

BEGIN;
SET LOCAL ROLE hwpx_agent_revision_test_app;
SELECT set_config('hwpx_agent.tenant_id', 'a1000000-0000-0000-0000-000000000001', true);
SELECT set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);
SELECT * FROM hwpx_agent.commit_revision_cas(
    'a1000000-0000-0000-0000-000000000001',
    'a2000000-0000-0000-0000-000000000001',
    'a3000000-0000-0000-0000-000000000002', repeat('a', 64),
    'a6000000-0000-0000-0000-000000000004', NULL, 0,
    'a5000000-0000-0000-0000-000000000004', ARRAY[]::uuid[],
    'a4000000-0000-0000-0000-000000000010',
    'a4000000-0000-0000-0000-000000000011',
    'a4000000-0000-0000-0000-000000000012',
    repeat('1', 64), 'verified', repeat('2', 64), repeat('3', 64),
    repeat('0', 63) || '5', repeat('0', 63) || '6'
);
COMMIT;

-- assertion 18: a non-default branch has its own generation-one root.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.branches
        WHERE branch_id = 'a3000000-0000-0000-0000-000000000002'
          AND head_revision_id = 'a5000000-0000-0000-0000-000000000004'
          AND head_generation = 1
    ) THEN
        RAISE EXCEPTION 'alternate branch head differs';
    END IF;
END
$$;

-- assertion 19: non-default commit does not rewrite the project/default head.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.projects
        WHERE project_id = 'a2000000-0000-0000-0000-000000000001'
          AND head_revision_id = 'a5000000-0000-0000-0000-000000000002'
          AND head_generation = 2
    ) THEN
        RAISE EXCEPTION 'alternate branch changed project head';
    END IF;
END
$$;

-- assertion 20: exactly three successful commits are sealed and receipted.
DO $$
BEGIN
    IF (SELECT count(*) FROM hwpx_agent.revision_graph_seals
        WHERE tenant_id = 'a1000000-0000-0000-0000-000000000001'
          AND seal_kind = 'service_v1') <> 3
       OR (SELECT count(*) FROM hwpx_agent.revision_commit_receipts
        WHERE tenant_id = 'a1000000-0000-0000-0000-000000000001') <> 3 THEN
        RAISE EXCEPTION 'successful revision cardinality differs';
    END IF;
END
$$;

SELECT 'P14_REVISION_CAS_SMOKE_PASS assertions=20';
