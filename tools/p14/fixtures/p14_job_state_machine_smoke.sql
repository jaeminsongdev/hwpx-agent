BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hwpx_agent_job_test_app') THEN
        CREATE ROLE hwpx_agent_job_test_app
            NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
    END IF;
END
$$;

GRANT USAGE ON SCHEMA hwpx_agent TO hwpx_agent_job_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.enqueue_job_state_machine(
    uuid, uuid, character, uuid, uuid, uuid, uuid, character, text, character
) TO hwpx_agent_job_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.lease_job_state_machine(
    uuid, uuid, character, uuid, uuid, uuid, integer, character
) TO hwpx_agent_job_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.advance_job_state_machine(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, text, text, character
) TO hwpx_agent_job_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.commit_job_success(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, uuid, uuid, character
) TO hwpx_agent_job_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.fail_job_state_machine(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, text, uuid, character
) TO hwpx_agent_job_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.get_job_state_machine(
    uuid, uuid, character, uuid
) TO hwpx_agent_job_test_app;

INSERT INTO hwpx_agent.tenants (tenant_id, slug) VALUES
    ('b1000000-0000-0000-0000-000000000001', 'job-tenant-primary'),
    ('b1000000-0000-0000-0000-000000000002', 'job-tenant-other');
INSERT INTO hwpx_agent.projects (
    tenant_id, project_id, slug, display_name, target_profile_id, retention_policy_id
) VALUES (
    'b1000000-0000-0000-0000-000000000001',
    'b2000000-0000-0000-0000-000000000001',
    'job-project', 'Job Project', 'hancom-hangul-2020-secondary',
    'retention.local-test'
);
INSERT INTO hwpx_agent.project_acl (tenant_id, project_id, subject_sha256, role) VALUES
    (
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001', repeat('a', 64), 'owner'
    ),
    (
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001', repeat('b', 64), 'reader'
    ),
    (
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001', repeat('c', 64), 'editor'
    );

WITH artifact_seed AS (
    SELECT
        ordinal,
        concat('b4000000-0000-0000-0000-', lpad(ordinal::text, 12, '0'))::uuid AS artifact_id,
        lpad(to_hex(ordinal + 300), 64, '0') AS content_sha256,
        CASE
            WHEN ordinal = 1 THEN 'source'
            WHEN ordinal IN (2, 3) THEN 'receipt'
            ELSE 'result'
        END AS artifact_kind
    FROM generate_series(1, 7) AS ordinal
)
INSERT INTO hwpx_agent.artifacts (
    tenant_id, artifact_id, content_sha256, size_bytes, media_type, artifact_kind,
    storage_state, encryption_key_ref, verified_at, service_metadata_version, filename,
    object_key, encryption_algorithm, encryption_nonce, aad_sha256, ciphertext_sha256,
    validation_state, scanner_engine_ref, scanner_signature_version,
    authorization_generation
)
SELECT
    'b1000000-0000-0000-0000-000000000001',
    artifact_id,
    content_sha256,
    ordinal,
    'application/octet-stream',
    artifact_kind,
    'available',
    'kms.job-test',
    transaction_timestamp(),
    1,
    concat('artifact-', ordinal, '.bin'),
    concat(
        'artifacts/v1/b1000000000000000000000000000001/', artifact_kind,
        '/available/', content_sha256, '.aes256gcm'
    ),
    'AES-256-GCM',
    decode(lpad(to_hex(ordinal), 24, '0'), 'hex'),
    lpad(to_hex(ordinal + 400), 64, '0'),
    lpad(to_hex(ordinal + 500), 64, '0'),
    'verified',
    'scanner.job-test',
    'v1',
    1
FROM artifact_seed;

-- This legacy artifact remains deliberately unqualified for negative tests.
INSERT INTO hwpx_agent.artifacts (
    tenant_id, artifact_id, content_sha256, size_bytes, media_type,
    artifact_kind, storage_state, encryption_key_ref
) VALUES (
    'b1000000-0000-0000-0000-000000000001',
    'b4000000-0000-0000-0000-000000000099', repeat('f', 64), 99,
    'application/octet-stream', 'source', 'staged', 'kms.job-test'
);

INSERT INTO hwpx_agent.artifact_acl (
    tenant_id, artifact_id, subject_sha256, can_read, can_manage
)
SELECT
    'b1000000-0000-0000-0000-000000000001',
    artifact_id,
    repeat('a', 64),
    true,
    true
FROM hwpx_agent.artifacts
WHERE tenant_id = 'b1000000-0000-0000-0000-000000000001'
  AND service_metadata_version = 1;

INSERT INTO hwpx_agent.revisions (
    tenant_id, project_id, revision_id, source_artifact_id, result_artifact_id,
    semantic_diff_artifact_id, operation_plan_sha256, validation_state,
    validation_summary_sha256, created_by_subject_sha256
) VALUES
    (
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001',
        'b5000000-0000-0000-0000-000000000001',
        'b4000000-0000-0000-0000-000000000001',
        'b4000000-0000-0000-0000-000000000004', NULL,
        repeat('1', 64), 'verified', repeat('2', 64), repeat('a', 64)
    ),
    (
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001',
        'b5000000-0000-0000-0000-000000000002',
        'b4000000-0000-0000-0000-000000000001',
        'b4000000-0000-0000-0000-000000000005', NULL,
        repeat('3', 64), 'verified', repeat('4', 64), repeat('a', 64)
    );
INSERT INTO hwpx_agent.revision_parents (
    tenant_id, project_id, revision_id, parent_revision_id, parent_ordinal
) VALUES (
    'b1000000-0000-0000-0000-000000000001',
    'b2000000-0000-0000-0000-000000000001',
    'b5000000-0000-0000-0000-000000000002',
    'b5000000-0000-0000-0000-000000000001', 0
);
INSERT INTO hwpx_agent.revision_graph_seals (
    tenant_id, project_id, revision_id, seal_kind, parent_count,
    committed_generation, commit_id, commit_request_sha256,
    transaction_receipt_sha256
) VALUES
    (
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001',
        'b5000000-0000-0000-0000-000000000001', 'service_v1', 0, 1,
        'b6000000-0000-0000-0000-000000000001', repeat('5', 64), repeat('6', 64)
    ),
    (
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001',
        'b5000000-0000-0000-0000-000000000002', 'service_v1', 1, 2,
        'b6000000-0000-0000-0000-000000000002', repeat('7', 64), repeat('8', 64)
    );

SELECT set_config(
    'hwpx_agent.tenant_id', 'b1000000-0000-0000-0000-000000000001', true
);
SELECT set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);

DO $$
DECLARE
    v_assertions integer := 0;
    v_count bigint;
    v_state text;
    v_attempt integer;
    v_fence bigint;
    v_error text;
    v_revision uuid;
    v_receipt uuid;
BEGIN
    -- 01: migration shape is exact enough for runtime use.
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 5 AND migration_name = 'p14.job_state_machine_v1'
    ) OR NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'hwpx_agent' AND table_name = 'jobs'
          AND column_name = 'state_machine_version'
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'jobs_state_machine_consistency' AND tgisinternal = false
    ) THEN RAISE EXCEPTION 'assertion 01 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 02: application role has function execution but no direct mutation path.
    IF has_table_privilege('hwpx_agent_job_test_app', 'hwpx_agent.jobs', 'UPDATE')
       OR has_table_privilege('hwpx_agent_job_test_app', 'hwpx_agent.job_attempts', 'INSERT')
       OR NOT has_function_privilege(
            'hwpx_agent_job_test_app',
            'hwpx_agent.enqueue_job_state_machine(uuid,uuid,character,uuid,uuid,uuid,uuid,character,text,character)',
            'EXECUTE'
       ) THEN RAISE EXCEPTION 'assertion 02 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 03: transaction-local context mismatch fails before resource lookup.
    PERFORM set_config('hwpx_agent.tenant_id', 'b1000000-0000-0000-0000-000000000002', true);
    BEGIN
        PERFORM * FROM hwpx_agent.enqueue_job_state_machine(
            'b1000000-0000-0000-0000-000000000001',
            'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'b7000000-0000-0000-0000-000000000003',
            'b8000000-0000-0000-0000-000000000003',
            'b4000000-0000-0000-0000-000000000001',
            'b5000000-0000-0000-0000-000000000001', repeat('1', 64),
            'hancom-hangul-2020-secondary', repeat('2', 64)
        );
        RAISE EXCEPTION 'assertion 03 unexpectedly succeeded';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'JOB_CONTEXT_MISMATCH' THEN RAISE; END IF;
    END;
    PERFORM set_config('hwpx_agent.tenant_id', 'b1000000-0000-0000-0000-000000000001', true);
    v_assertions := v_assertions + 1;

    -- 04: project reader cannot enqueue.
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('b', 64), true);
    BEGIN
        PERFORM * FROM hwpx_agent.enqueue_job_state_machine(
            'b1000000-0000-0000-0000-000000000001',
            'b2000000-0000-0000-0000-000000000001', repeat('b', 64),
            'b7000000-0000-0000-0000-000000000004',
            'b8000000-0000-0000-0000-000000000004',
            'b4000000-0000-0000-0000-000000000001', NULL, repeat('1', 64),
            'hancom-hangul-2020-secondary', repeat('2', 64)
        );
        RAISE EXCEPTION 'assertion 04 unexpectedly succeeded';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'JOB_MUTATION_DENIED' THEN RAISE; END IF;
    END;
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);
    v_assertions := v_assertions + 1;

    -- 05: legacy or unverified input artifacts never enqueue.
    BEGIN
        PERFORM * FROM hwpx_agent.enqueue_job_state_machine(
            'b1000000-0000-0000-0000-000000000001',
            'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'b7000000-0000-0000-0000-000000000005',
            'b8000000-0000-0000-0000-000000000005',
            'b4000000-0000-0000-0000-000000000099', NULL, repeat('1', 64),
            'hancom-hangul-2020-secondary', repeat('2', 64)
        );
        RAISE EXCEPTION 'assertion 05 unexpectedly succeeded';
    EXCEPTION WHEN foreign_key_violation THEN
        IF SQLERRM <> 'JOB_INPUT_ARTIFACT_NOT_QUALIFIED' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 06: an absent/unsealed expected revision is rejected.
    BEGIN
        PERFORM * FROM hwpx_agent.enqueue_job_state_machine(
            'b1000000-0000-0000-0000-000000000001',
            'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'b7000000-0000-0000-0000-000000000006',
            'b8000000-0000-0000-0000-000000000006',
            'b4000000-0000-0000-0000-000000000001',
            'b5000000-0000-0000-0000-000000000099', repeat('1', 64),
            'hancom-hangul-2020-secondary', repeat('2', 64)
        );
        RAISE EXCEPTION 'assertion 06 unexpectedly succeeded';
    EXCEPTION WHEN foreign_key_violation THEN
        IF SQLERRM <> 'JOB_EXPECTED_REVISION_NOT_QUALIFIED' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 07: happy enqueue creates exactly one qualified queued row.
    SELECT returned_state, returned_attempt_count, returned_fencing_token
    INTO v_state, v_attempt, v_fence
    FROM hwpx_agent.enqueue_job_state_machine(
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'b7000000-0000-0000-0000-000000000001',
        'b8000000-0000-0000-0000-000000000001',
        'b4000000-0000-0000-0000-000000000001',
        'b5000000-0000-0000-0000-000000000001', repeat('1', 64),
        'hancom-hangul-2020-secondary', repeat('2', 64)
    );
    IF ROW(v_state, v_attempt, v_fence) IS DISTINCT FROM ROW('queued', 0, 0::bigint) THEN
        RAISE EXCEPTION 'assertion 07 failed';
    END IF;
    v_assertions := v_assertions + 1;

    -- 08: duplicate job or request identities are side-effect free.
    BEGIN
        PERFORM * FROM hwpx_agent.enqueue_job_state_machine(
            'b1000000-0000-0000-0000-000000000001',
            'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'b7000000-0000-0000-0000-000000000008',
            'b8000000-0000-0000-0000-000000000001',
            'b4000000-0000-0000-0000-000000000001', NULL, repeat('1', 64),
            'hancom-hangul-2020-secondary', repeat('2', 64)
        );
        RAISE EXCEPTION 'assertion 08 unexpectedly succeeded';
    EXCEPTION WHEN unique_violation THEN
        IF SQLERRM <> 'JOB_IDENTITY_ALREADY_EXISTS' THEN RAISE; END IF;
    END;
    SELECT count(*) INTO v_count FROM hwpx_agent.jobs
    WHERE tenant_id = 'b1000000-0000-0000-0000-000000000001'
      AND state_machine_version = 1;
    IF v_count <> 1 THEN RAISE EXCEPTION 'assertion 08 mutated rows'; END IF;
    v_assertions := v_assertions + 1;

    -- 09: lease TTL is structurally bounded.
    BEGIN
        PERFORM * FROM hwpx_agent.lease_job_state_machine(
            'b1000000-0000-0000-0000-000000000001',
            'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'b7000000-0000-0000-0000-000000000001',
            'b9000000-0000-0000-0000-000000000001',
            'ba000000-0000-0000-0000-000000000001', 3601, repeat('3', 64)
        );
        RAISE EXCEPTION 'assertion 09 unexpectedly succeeded';
    EXCEPTION WHEN invalid_parameter_value THEN
        IF SQLERRM <> 'JOB_LEASE_REQUEST_INVALID' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 10: lease binds one exact attempt, execution, agent and fence.
    SELECT returned_state, returned_attempt_count, returned_fencing_token
    INTO v_state, v_attempt, v_fence
    FROM hwpx_agent.lease_job_state_machine(
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'b7000000-0000-0000-0000-000000000001',
        'b9000000-0000-0000-0000-000000000001',
        'ba000000-0000-0000-0000-000000000001', 300, repeat('3', 64)
    );
    IF ROW(v_state, v_attempt, v_fence) IS DISTINCT FROM ROW('leased', 1, 1::bigint) THEN
        RAISE EXCEPTION 'assertion 10 failed';
    END IF;
    v_assertions := v_assertions + 1;

    -- 11: a second lease cannot create another attempt.
    BEGIN
        PERFORM * FROM hwpx_agent.lease_job_state_machine(
            'b1000000-0000-0000-0000-000000000001',
            'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'b7000000-0000-0000-0000-000000000001',
            'b9000000-0000-0000-0000-000000000002',
            'ba000000-0000-0000-0000-000000000002', 300, repeat('3', 64)
        );
        RAISE EXCEPTION 'assertion 11 unexpectedly succeeded';
    EXCEPTION WHEN SQLSTATE '55000' THEN
        IF SQLERRM <> 'JOB_TRANSITION_INVALID' THEN RAISE; END IF;
    END;
    SELECT count(*) INTO v_count FROM hwpx_agent.job_attempts
    WHERE tenant_id = 'b1000000-0000-0000-0000-000000000001'
      AND project_id = 'b2000000-0000-0000-0000-000000000001'
      AND job_id = 'b7000000-0000-0000-0000-000000000001';
    IF v_count <> 1 THEN RAISE EXCEPTION 'assertion 11 mutated attempts'; END IF;
    v_assertions := v_assertions + 1;

    -- 12: a skipped stage is invalid at the request boundary.
    BEGIN
        PERFORM * FROM hwpx_agent.advance_job_state_machine(
            'b1000000-0000-0000-0000-000000000001',
            'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'b7000000-0000-0000-0000-000000000001',
            'b9000000-0000-0000-0000-000000000001',
            'ba000000-0000-0000-0000-000000000001', 1, 1,
            'leased', 'executing', repeat('4', 64)
        );
        RAISE EXCEPTION 'assertion 12 unexpectedly succeeded';
    EXCEPTION WHEN invalid_parameter_value THEN
        IF SQLERRM <> 'JOB_STAGE_REQUEST_INVALID' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 13: a stale execution binding cannot advance.
    BEGIN
        PERFORM * FROM hwpx_agent.advance_job_state_machine(
            'b1000000-0000-0000-0000-000000000001',
            'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'b7000000-0000-0000-0000-000000000001',
            'b9000000-0000-0000-0000-000000000001',
            'ba000000-0000-0000-0000-000000000099', 1, 1,
            'leased', 'staged', repeat('4', 64)
        );
        RAISE EXCEPTION 'assertion 13 unexpectedly succeeded';
    EXCEPTION WHEN serialization_failure THEN
        IF SQLERRM <> 'JOB_LEASE_MISMATCH' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 14: leased -> staged is the only first stage edge.
    SELECT returned_state INTO v_state
    FROM hwpx_agent.advance_job_state_machine(
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'b7000000-0000-0000-0000-000000000001',
        'b9000000-0000-0000-0000-000000000001',
        'ba000000-0000-0000-0000-000000000001', 1, 1,
        'leased', 'staged', repeat('4', 64)
    );
    IF v_state <> 'staged' THEN RAISE EXCEPTION 'assertion 14 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 15: repeated/backward edge leaves state unchanged.
    BEGIN
        PERFORM * FROM hwpx_agent.advance_job_state_machine(
            'b1000000-0000-0000-0000-000000000001',
            'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'b7000000-0000-0000-0000-000000000001',
            'b9000000-0000-0000-0000-000000000001',
            'ba000000-0000-0000-0000-000000000001', 1, 1,
            'leased', 'staged', repeat('4', 64)
        );
        RAISE EXCEPTION 'assertion 15 unexpectedly succeeded';
    EXCEPTION WHEN SQLSTATE '55000' THEN
        IF SQLERRM <> 'JOB_TRANSITION_INVALID' THEN RAISE; END IF;
    END;
    SELECT state INTO v_state FROM hwpx_agent.jobs
    WHERE tenant_id = 'b1000000-0000-0000-0000-000000000001'
      AND project_id = 'b2000000-0000-0000-0000-000000000001'
      AND job_id = 'b7000000-0000-0000-0000-000000000001';
    IF v_state <> 'staged' THEN RAISE EXCEPTION 'assertion 15 mutated state'; END IF;
    v_assertions := v_assertions + 1;

    -- 16: staged -> executing also promotes the attempt to running.
    PERFORM * FROM hwpx_agent.advance_job_state_machine(
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'b7000000-0000-0000-0000-000000000001',
        'b9000000-0000-0000-0000-000000000001',
        'ba000000-0000-0000-0000-000000000001', 1, 1,
        'staged', 'executing', repeat('5', 64)
    );
    SELECT state INTO v_state FROM hwpx_agent.job_attempts
    WHERE tenant_id = 'b1000000-0000-0000-0000-000000000001'
      AND execution_id = 'ba000000-0000-0000-0000-000000000001';
    IF v_state <> 'running' THEN RAISE EXCEPTION 'assertion 16 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 17: executing -> validating completes the nonterminal chain.
    SELECT returned_state INTO v_state
    FROM hwpx_agent.advance_job_state_machine(
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'b7000000-0000-0000-0000-000000000001',
        'b9000000-0000-0000-0000-000000000001',
        'ba000000-0000-0000-0000-000000000001', 1, 1,
        'executing', 'validating', repeat('6', 64)
    );
    IF v_state <> 'validating' THEN RAISE EXCEPTION 'assertion 17 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 18: success refuses an unqualified result revision without mutation.
    BEGIN
        PERFORM * FROM hwpx_agent.commit_job_success(
            'b1000000-0000-0000-0000-000000000001',
            'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'b7000000-0000-0000-0000-000000000001',
            'b9000000-0000-0000-0000-000000000001',
            'ba000000-0000-0000-0000-000000000001', 1, 1,
            'b5000000-0000-0000-0000-000000000099',
            'b4000000-0000-0000-0000-000000000002', repeat('7', 64)
        );
        RAISE EXCEPTION 'assertion 18 unexpectedly succeeded';
    EXCEPTION WHEN foreign_key_violation THEN
        IF SQLERRM <> 'JOB_RESULT_REVISION_NOT_QUALIFIED' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 19: success refuses a non-receipt artifact without mutation.
    BEGIN
        PERFORM * FROM hwpx_agent.commit_job_success(
            'b1000000-0000-0000-0000-000000000001',
            'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'b7000000-0000-0000-0000-000000000001',
            'b9000000-0000-0000-0000-000000000001',
            'ba000000-0000-0000-0000-000000000001', 1, 1,
            'b5000000-0000-0000-0000-000000000002',
            'b4000000-0000-0000-0000-000000000004', repeat('7', 64)
        );
        RAISE EXCEPTION 'assertion 19 unexpectedly succeeded';
    EXCEPTION WHEN foreign_key_violation THEN
        IF SQLERRM <> 'JOB_RECEIPT_ARTIFACT_NOT_QUALIFIED' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 20: validating -> succeeded atomically binds revision and receipt.
    SELECT returned_state, returned_result_revision_id, returned_receipt_artifact_id
    INTO v_state, v_revision, v_receipt
    FROM hwpx_agent.commit_job_success(
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'b7000000-0000-0000-0000-000000000001',
        'b9000000-0000-0000-0000-000000000001',
        'ba000000-0000-0000-0000-000000000001', 1, 1,
        'b5000000-0000-0000-0000-000000000002',
        'b4000000-0000-0000-0000-000000000002', repeat('7', 64)
    );
    IF ROW(v_state, v_revision, v_receipt) IS DISTINCT FROM ROW(
        'succeeded', 'b5000000-0000-0000-0000-000000000002'::uuid,
        'b4000000-0000-0000-0000-000000000002'::uuid
    ) THEN RAISE EXCEPTION 'assertion 20 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 21: terminal success is immutable.
    BEGIN
        PERFORM * FROM hwpx_agent.fail_job_state_machine(
            'b1000000-0000-0000-0000-000000000001',
            'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'b7000000-0000-0000-0000-000000000001',
            'b9000000-0000-0000-0000-000000000001',
            'ba000000-0000-0000-0000-000000000001', 1, 1,
            'LATE_FAILURE', 'b4000000-0000-0000-0000-000000000003', repeat('8', 64)
        );
        RAISE EXCEPTION 'assertion 21 unexpectedly succeeded';
    EXCEPTION WHEN SQLSTATE '55000' THEN
        IF SQLERRM <> 'JOB_TRANSITION_INVALID' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 22: an authorized reader gets the same terminal projection.
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('b', 64), true);
    SELECT returned_state, returned_result_revision_id, returned_receipt_artifact_id
    INTO v_state, v_revision, v_receipt
    FROM hwpx_agent.get_job_state_machine(
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001', repeat('b', 64),
        'b7000000-0000-0000-0000-000000000001'
    );
    IF v_state <> 'succeeded' OR v_revision IS NULL OR v_receipt IS NULL THEN
        RAISE EXCEPTION 'assertion 22 failed';
    END IF;
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);
    v_assertions := v_assertions + 1;

    -- 23: second job can terminate directly from leased with a receipt.
    PERFORM * FROM hwpx_agent.enqueue_job_state_machine(
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'b7000000-0000-0000-0000-000000000002',
        'b8000000-0000-0000-0000-000000000002',
        'b4000000-0000-0000-0000-000000000001', NULL, repeat('9', 64),
        'hancom-hangul-2020-secondary', repeat('a', 64)
    );
    PERFORM * FROM hwpx_agent.lease_job_state_machine(
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'b7000000-0000-0000-0000-000000000002',
        'b9000000-0000-0000-0000-000000000002',
        'ba000000-0000-0000-0000-000000000002', 300, repeat('b', 64)
    );
    SELECT returned_state, returned_terminal_error_code, returned_receipt_artifact_id
    INTO v_state, v_error, v_receipt
    FROM hwpx_agent.fail_job_state_machine(
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'b7000000-0000-0000-0000-000000000002',
        'b9000000-0000-0000-0000-000000000002',
        'ba000000-0000-0000-0000-000000000002', 1, 1,
        'STAGING_FAILED', 'b4000000-0000-0000-0000-000000000003', repeat('c', 64)
    );
    SELECT state INTO v_state FROM hwpx_agent.jobs
    WHERE tenant_id = 'b1000000-0000-0000-0000-000000000001'
      AND project_id = 'b2000000-0000-0000-0000-000000000001'
      AND job_id = 'b7000000-0000-0000-0000-000000000002';
    IF v_state <> 'failed' OR v_error <> 'STAGING_FAILED' OR v_receipt IS NULL THEN
        RAISE EXCEPTION 'assertion 23 failed';
    END IF;
    v_assertions := v_assertions + 1;

    -- 24: direct skip update is rejected by the table guard.
    PERFORM * FROM hwpx_agent.enqueue_job_state_machine(
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'b7000000-0000-0000-0000-000000000024',
        'b8000000-0000-0000-0000-000000000024',
        'b4000000-0000-0000-0000-000000000001', NULL, repeat('d', 64),
        'hancom-hangul-2020-secondary', repeat('e', 64)
    );
    BEGIN
        UPDATE hwpx_agent.jobs SET state = 'executing'
        WHERE tenant_id = 'b1000000-0000-0000-0000-000000000001'
          AND project_id = 'b2000000-0000-0000-0000-000000000001'
          AND job_id = 'b7000000-0000-0000-0000-000000000024';
        RAISE EXCEPTION 'assertion 24 unexpectedly succeeded';
    EXCEPTION WHEN SQLSTATE '55000' THEN
        IF SQLERRM <> 'JOB_TRANSITION_INVALID' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 25: terminal attempt rows cannot be edited after success.
    BEGIN
        UPDATE hwpx_agent.job_attempts SET state = 'failed'
        WHERE tenant_id = 'b1000000-0000-0000-0000-000000000001'
          AND project_id = 'b2000000-0000-0000-0000-000000000001'
          AND job_id = 'b7000000-0000-0000-0000-000000000001';
        RAISE EXCEPTION 'assertion 25 unexpectedly succeeded';
    EXCEPTION WHEN SQLSTATE '55000' THEN
        IF SQLERRM <> 'JOB_ATTEMPT_TERMINAL_IMMUTABLE' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 26: pre-v5 legacy jobs are not promoted by inference.
    INSERT INTO hwpx_agent.jobs (
        tenant_id, project_id, job_id, request_id, input_artifact_id,
        operation_plan_sha256, required_target_profile_id,
        required_capability_set_sha256
    ) VALUES (
        'b1000000-0000-0000-0000-000000000001',
        'b2000000-0000-0000-0000-000000000001',
        'b7000000-0000-0000-0000-000000000026',
        'b8000000-0000-0000-0000-000000000026',
        'b4000000-0000-0000-0000-000000000001', repeat('f', 64),
        'hancom-hangul-2020-secondary', repeat('0', 64)
    );
    BEGIN
        PERFORM * FROM hwpx_agent.lease_job_state_machine(
            'b1000000-0000-0000-0000-000000000001',
            'b2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'b7000000-0000-0000-0000-000000000026',
            'b9000000-0000-0000-0000-000000000026',
            'ba000000-0000-0000-0000-000000000026', 300, repeat('1', 64)
        );
        RAISE EXCEPTION 'assertion 26 unexpectedly succeeded';
    EXCEPTION WHEN no_data_found THEN
        IF SQLERRM <> 'JOB_NOT_FOUND' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 27: state transitions emitted the expected audit events.
    SELECT count(*) INTO v_count FROM hwpx_agent.audit_events
    WHERE tenant_id = 'b1000000-0000-0000-0000-000000000001'
      AND project_id = 'b2000000-0000-0000-0000-000000000001'
      AND event_type IN (
          'job.enqueued', 'job.leased', 'job.staged', 'job.executing',
          'job.validating', 'job.succeeded', 'job.failed'
      );
    IF v_count <> 10 THEN RAISE EXCEPTION 'assertion 27 failed count=%', v_count; END IF;
    v_assertions := v_assertions + 1;

    -- 28: reserved later-phase terminal states cannot be reached in v1.
    BEGIN
        UPDATE hwpx_agent.jobs SET state = 'cancelled', terminal_error_code = 'CANCELLED',
            completed_at = transaction_timestamp()
        WHERE tenant_id = 'b1000000-0000-0000-0000-000000000001'
          AND project_id = 'b2000000-0000-0000-0000-000000000001'
          AND job_id = 'b7000000-0000-0000-0000-000000000024';
        RAISE EXCEPTION 'assertion 28 unexpectedly succeeded';
    EXCEPTION WHEN SQLSTATE '55000' THEN
        IF SQLERRM <> 'JOB_TRANSITION_INVALID' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 29: a valid-looking edge cannot mutate the immutable job specification.
    BEGIN
        UPDATE hwpx_agent.jobs
        SET state = 'leased', attempt_count = 1,
            lease_owner_agent_id = 'b9000000-0000-0000-0000-000000000029',
            active_execution_id = 'ba000000-0000-0000-0000-000000000029',
            fencing_token = 1, lease_issued_at = transaction_timestamp(),
            lease_expires_at = transaction_timestamp() + interval '5 minutes',
            operation_plan_sha256 = repeat('0', 64),
            updated_at = transaction_timestamp()
        WHERE tenant_id = 'b1000000-0000-0000-0000-000000000001'
          AND project_id = 'b2000000-0000-0000-0000-000000000001'
          AND job_id = 'b7000000-0000-0000-0000-000000000024';
        RAISE EXCEPTION 'assertion 29 unexpectedly succeeded';
    EXCEPTION WHEN SQLSTATE '55000' THEN
        IF SQLERRM <> 'job identity is immutable' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 30: a project editor without artifact ACL cannot enqueue that artifact.
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('c', 64), true);
    BEGIN
        PERFORM * FROM hwpx_agent.enqueue_job_state_machine(
            'b1000000-0000-0000-0000-000000000001',
            'b2000000-0000-0000-0000-000000000001', repeat('c', 64),
            'b7000000-0000-0000-0000-000000000030',
            'b8000000-0000-0000-0000-000000000030',
            'b4000000-0000-0000-0000-000000000001', NULL, repeat('1', 64),
            'hancom-hangul-2020-secondary', repeat('2', 64)
        );
        RAISE EXCEPTION 'assertion 30 unexpectedly succeeded';
    EXCEPTION WHEN foreign_key_violation THEN
        IF SQLERRM <> 'JOB_INPUT_ARTIFACT_NOT_QUALIFIED' THEN RAISE; END IF;
    END;
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);
    v_assertions := v_assertions + 1;

    IF v_assertions <> 30 THEN RAISE EXCEPTION 'assertion count mismatch'; END IF;
    RAISE NOTICE 'P14_JOB_STATE_MACHINE_SMOKE_PASS assertions=%', v_assertions;
END
$$;

SET CONSTRAINTS ALL IMMEDIATE;
SELECT 'P14_JOB_STATE_MACHINE_SMOKE_PASS assertions=30';
ROLLBACK;
