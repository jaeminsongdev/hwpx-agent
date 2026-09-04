BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hwpx_agent_idempotency_test_app') THEN
        CREATE ROLE hwpx_agent_idempotency_test_app
            NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
    END IF;
END
$$;

GRANT USAGE ON SCHEMA hwpx_agent TO hwpx_agent_idempotency_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.register_scheduler_worker(
    uuid, character, uuid, text, character, text, integer, character
) TO hwpx_agent_idempotency_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.commit_idempotent_revision_cas_v2(
    uuid, uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    uuid, uuid, uuid, bigint, uuid, uuid[], uuid, uuid, uuid,
    character, text, character, character, character, character
) TO hwpx_agent_idempotency_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.claim_idempotent_job_v2(
    uuid, uuid, uuid, character, uuid, uuid, uuid, uuid, uuid, bigint,
    character, character, character, character, character, character,
    text, character, integer, integer, integer, integer, character
) TO hwpx_agent_idempotency_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.lease_idempotent_job_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, character
) TO hwpx_agent_idempotency_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.advance_idempotent_job_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    text, text, character
) TO hwpx_agent_idempotency_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.heartbeat_idempotent_job_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    integer, character
) TO hwpx_agent_idempotency_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.schedule_idempotent_retry_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    text, uuid, character
) TO hwpx_agent_idempotency_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.mark_idempotent_outcome_unknown_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    uuid, character
) TO hwpx_agent_idempotency_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.complete_idempotent_job_success_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    uuid, uuid, character
) TO hwpx_agent_idempotency_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.fail_idempotent_job_terminal_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    text, text, uuid, character
) TO hwpx_agent_idempotency_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.reconcile_idempotent_job_v2(
    uuid, uuid, character, uuid, uuid, text, uuid, uuid, character
) TO hwpx_agent_idempotency_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.get_idempotent_job_v2(
    uuid, uuid, character, uuid
) TO hwpx_agent_idempotency_test_app;

INSERT INTO hwpx_agent.tenants (tenant_id, slug) VALUES
    ('d1000000-0000-0000-0000-000000000001', 'idempotency-tenant-primary'),
    ('d1000000-0000-0000-0000-000000000002', 'idempotency-tenant-other');
INSERT INTO hwpx_agent.projects (
    tenant_id, project_id, slug, display_name, target_profile_id, retention_policy_id
) VALUES (
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001',
    'idempotency-project', 'Idempotency Project',
    'hancom-hangul-2020-current-pc', 'retention.local-test'
);
INSERT INTO hwpx_agent.project_acl (tenant_id, project_id, subject_sha256, role) VALUES
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64), 'owner'
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('b', 64), 'reader'
    );
INSERT INTO hwpx_agent.branches (
    tenant_id, project_id, branch_id, name, is_default, created_by_subject_sha256
) VALUES (
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001',
    'd3000000-0000-0000-0000-000000000001',
    'main', true, repeat('a', 64)
);

WITH artifact_seed AS (
    SELECT
        ordinal,
        concat('d4000000-0000-0000-0000-', lpad(ordinal::text, 12, '0'))::uuid AS artifact_id,
        lpad(to_hex(ordinal + 1000), 64, '0') AS content_sha256,
        CASE
            WHEN ordinal IN (1, 6) THEN 'source'
            WHEN ordinal IN (4, 7) THEN 'result'
            ELSE 'receipt'
        END AS artifact_kind
    FROM generate_series(1, 10) AS ordinal
)
INSERT INTO hwpx_agent.artifacts (
    tenant_id, artifact_id, content_sha256, size_bytes, media_type, artifact_kind,
    storage_state, encryption_key_ref, verified_at, service_metadata_version, filename,
    object_key, encryption_algorithm, encryption_nonce, aad_sha256, ciphertext_sha256,
    validation_state, scanner_engine_ref, scanner_signature_version,
    authorization_generation
)
SELECT
    'd1000000-0000-0000-0000-000000000001', artifact_id, content_sha256,
    ordinal, 'application/octet-stream', artifact_kind, 'available',
    'kms.idempotency-test', transaction_timestamp(), 1,
    concat('artifact-', ordinal, '.bin'),
    concat(
        'artifacts/v1/d1000000000000000000000000000001/', artifact_kind,
        '/available/', content_sha256, '.aes256gcm'
    ),
    'AES-256-GCM', decode(lpad(to_hex(ordinal), 24, '0'), 'hex'),
    lpad(to_hex(ordinal + 1100), 64, '0'),
    lpad(to_hex(ordinal + 1200), 64, '0'),
    'verified', 'scanner.idempotency-test', 'v1', 1
FROM artifact_seed;

INSERT INTO hwpx_agent.artifact_acl (
    tenant_id, artifact_id, subject_sha256, can_read, can_manage
)
SELECT
    'd1000000-0000-0000-0000-000000000001', artifact_id,
    repeat('a', 64), true, true
FROM hwpx_agent.artifacts
WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001';

-- This is a genuine v1 row created after v7. Its absent v2 evidence remains absent.
INSERT INTO hwpx_agent.idempotency_records (
    tenant_id, project_id, idempotency_key, request_sha256, state, expires_at
) VALUES (
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001',
    'd7000000-0000-0000-0000-000000000099', repeat('0', 64),
    'claimed', transaction_timestamp() + interval '1 hour'
);

SELECT set_config(
    'hwpx_agent.tenant_id', 'd1000000-0000-0000-0000-000000000001', true
);
SELECT set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);

DO $$
DECLARE
    v_assertions integer := 0;
    v_outcome text;
    v_state text;
    v_error text;
    v_job_id uuid;
    v_result_revision_id uuid;
    v_attempt integer;
    v_fence bigint;
    v_retry_at timestamptz;
    v_count bigint;
    v_source1_sha character(64);
    v_source2_sha character(64);
    v_result1_sha character(64);
    v_result2_sha character(64);
    v_tx1_sha character(64);
    v_tx2_sha character(64);
    v_commit_authorization_id uuid;
BEGIN
    SELECT content_sha256 INTO v_source1_sha FROM hwpx_agent.artifacts
    WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
      AND artifact_id = 'd4000000-0000-0000-0000-000000000001';
    SELECT content_sha256 INTO v_result1_sha FROM hwpx_agent.artifacts
    WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
      AND artifact_id = 'd4000000-0000-0000-0000-000000000004';
    SELECT content_sha256 INTO v_tx1_sha FROM hwpx_agent.artifacts
    WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
      AND artifact_id = 'd4000000-0000-0000-0000-000000000005';
    SELECT content_sha256 INTO v_source2_sha FROM hwpx_agent.artifacts
    WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
      AND artifact_id = 'd4000000-0000-0000-0000-000000000006';
    SELECT content_sha256 INTO v_result2_sha FROM hwpx_agent.artifacts
    WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
      AND artifact_id = 'd4000000-0000-0000-0000-000000000007';
    SELECT content_sha256 INTO v_tx2_sha FROM hwpx_agent.artifacts
    WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
      AND artifact_id = 'd4000000-0000-0000-0000-000000000008';

    -- 01: v7 is exact, tenant tables remain forced-RLS and PUBLIC cannot execute mutations.
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 7 AND migration_name = 'p14.idempotency_reconciliation_v2'
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_class AS relation
        JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
        WHERE namespace.nspname = 'hwpx_agent'
          AND relation.relname = 'idempotency_records'
          AND relation.relrowsecurity AND relation.relforcerowsecurity
    ) OR has_function_privilege(
        'public',
        'hwpx_agent.reconcile_idempotent_job_v2(uuid,uuid,character,uuid,uuid,text,uuid,uuid,character)',
        'EXECUTE'
    ) OR has_function_privilege(
        'public', 'hwpx_agent.guard_idempotent_revision_commit_v2()', 'EXECUTE'
    ) THEN RAISE EXCEPTION 'assertion 01 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 02: the bounded app surface is executable but tables remain non-mutable.
    IF has_table_privilege(
        'hwpx_agent_idempotency_test_app', 'hwpx_agent.idempotency_records', 'UPDATE'
    ) OR has_table_privilege(
        'hwpx_agent_idempotency_test_app', 'hwpx_agent.jobs', 'INSERT'
    ) OR has_table_privilege(
        'hwpx_agent_idempotency_test_app',
        'hwpx_agent.idempotency_commit_authorizations', 'DELETE'
    ) OR NOT has_function_privilege(
        'hwpx_agent_idempotency_test_app',
        'hwpx_agent.claim_idempotent_job_v2(uuid,uuid,uuid,character,uuid,uuid,uuid,uuid,uuid,bigint,character,character,character,character,character,character,text,character,integer,integer,integer,integer,character)',
        'EXECUTE'
    ) OR NOT has_function_privilege(
        'hwpx_agent_idempotency_test_app',
        'hwpx_agent.commit_idempotent_revision_cas_v2(uuid,uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,uuid,uuid,uuid,bigint,uuid,uuid[],uuid,uuid,uuid,character,text,character,character,character,character)',
        'EXECUTE'
    ) OR has_function_privilege(
        'hwpx_agent_idempotency_test_app',
        'hwpx_agent.commit_revision_cas(uuid,uuid,uuid,character,uuid,uuid,bigint,uuid,uuid[],uuid,uuid,uuid,character,text,character,character,character,character)',
        'EXECUTE'
    ) THEN RAISE EXCEPTION 'assertion 02 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 03: legacy evidence stays version 1 with no synthesized v2 identity.
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.idempotency_records
        WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
          AND project_id = 'd2000000-0000-0000-0000-000000000001'
          AND idempotency_key = 'd7000000-0000-0000-0000-000000000099'
          AND record_version = 1 AND subject_sha256 IS NULL
          AND execution_manifest_sha256 IS NULL AND attempt_count IS NULL
    ) THEN RAISE EXCEPTION 'assertion 03 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 04: legacy rows cannot be silently promoted.
    BEGIN
        UPDATE hwpx_agent.idempotency_records SET record_version = 2
        WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
          AND project_id = 'd2000000-0000-0000-0000-000000000001'
          AND idempotency_key = 'd7000000-0000-0000-0000-000000000099';
        RAISE EXCEPTION 'assertion 04 unexpectedly succeeded';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN
        IF SQLERRM <> 'IDEMPOTENCY_IDENTITY_IMMUTABLE' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- Register exact and mismatched workers.
    PERFORM * FROM hwpx_agent.register_scheduler_worker(
        'd1000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd9000000-0000-0000-0000-000000000001',
        'hancom-hangul-2020-current-pc', repeat('c', 64),
        'ready', 300, repeat('1', 64)
    );
    PERFORM * FROM hwpx_agent.register_scheduler_worker(
        'd1000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd9000000-0000-0000-0000-000000000002',
        'hancom-hangul-2024-other', repeat('c', 64),
        'ready', 300, repeat('1', 64)
    );

    -- 05: claim creates exactly one version-2 record and one coupled queued job.
    SELECT returned_outcome, returned_job_id, returned_state,
           returned_attempt_count, returned_fencing_token
    INTO v_outcome, v_job_id, v_state, v_attempt, v_fence
    FROM hwpx_agent.claim_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd3000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000001',
        'd8000000-0000-0000-0000-000000000001',
        'd8100000-0000-0000-0000-000000000001',
        'd4000000-0000-0000-0000-000000000001', NULL, 0,
        repeat('1', 64), repeat('2', 64), v_source1_sha,
        repeat('e', 64), repeat('f', 64), repeat('3', 64),
        'hancom-hangul-2020-current-pc', repeat('c', 64),
        3, 1, 4, 600, repeat('4', 64)
    );
    IF ROW(v_outcome, v_job_id, v_state, v_attempt, v_fence)
       IS DISTINCT FROM ROW(
            'new'::text, 'd8000000-0000-0000-0000-000000000001'::uuid,
            'claimed'::text, 0, 0::bigint
       ) OR NOT EXISTS (
            SELECT 1 FROM hwpx_agent.jobs
            WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
              AND project_id = 'd2000000-0000-0000-0000-000000000001'
              AND job_id = v_job_id AND state_machine_version = 2 AND state = 'queued'
       ) THEN RAISE EXCEPTION 'assertion 05 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 06: an exact replay observes the same record and creates no second job.
    SELECT returned_outcome, returned_state INTO v_outcome, v_state
    FROM hwpx_agent.claim_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd3000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000001',
        'd8000000-0000-0000-0000-000000000001',
        'd8100000-0000-0000-0000-000000000001',
        'd4000000-0000-0000-0000-000000000001', NULL, 0,
        repeat('1', 64), repeat('2', 64), v_source1_sha,
        repeat('e', 64), repeat('f', 64), repeat('3', 64),
        'hancom-hangul-2020-current-pc', repeat('c', 64),
        3, 1, 4, 600, repeat('4', 64)
    );
    SELECT count(*) INTO v_count FROM hwpx_agent.jobs
    WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
      AND project_id = 'd2000000-0000-0000-0000-000000000001'
      AND state_machine_version = 2;
    IF v_outcome <> 'replay' OR v_state <> 'claimed' OR v_count <> 1 THEN
        RAISE EXCEPTION 'assertion 06 failed';
    END IF;
    v_assertions := v_assertions + 1;

    -- 07: reuse with any immutable binding drift fails without mutation.
    BEGIN
        PERFORM * FROM hwpx_agent.claim_idempotent_job_v2(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001',
            'd3000000-0000-0000-0000-000000000001', repeat('a', 64),
            'd7000000-0000-0000-0000-000000000001',
            'd8000000-0000-0000-0000-000000000001',
            'd8100000-0000-0000-0000-000000000001',
            'd4000000-0000-0000-0000-000000000001', NULL, 0,
            repeat('9', 64), repeat('2', 64), v_source1_sha,
            repeat('e', 64), repeat('f', 64), repeat('3', 64),
            'hancom-hangul-2020-current-pc', repeat('c', 64),
            3, 1, 4, 600, repeat('4', 64)
        );
        RAISE EXCEPTION 'assertion 07 unexpectedly succeeded';
    EXCEPTION WHEN unique_violation THEN
        IF SQLERRM <> 'IDEMPOTENCY_KEY_CONFLICT' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 08: direct v2 job mutation is rejected even by the fixture owner unless a service opens it.
    BEGIN
        UPDATE hwpx_agent.jobs SET state = 'failed', terminal_error_code = 'FORGED',
            completed_at = clock_timestamp()
        WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
          AND project_id = 'd2000000-0000-0000-0000-000000000001'
          AND job_id = 'd8000000-0000-0000-0000-000000000001';
        RAISE EXCEPTION 'assertion 08 unexpectedly succeeded';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN
        IF SQLERRM <> 'IDEMPOTENCY_V2_TRANSITION_REQUIRED' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 09: a profile mismatch cannot lease.
    BEGIN
        PERFORM * FROM hwpx_agent.lease_idempotent_job_v2(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'd7000000-0000-0000-0000-000000000001',
            'd8000000-0000-0000-0000-000000000001',
            'd9000000-0000-0000-0000-000000000002',
            'da000000-0000-0000-0000-000000000001', 60, repeat('5', 64)
        );
        RAISE EXCEPTION 'assertion 09 unexpectedly succeeded';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'JOB_WORKER_NOT_QUALIFIED' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 10: exact worker lease atomically creates attempt/fence 1.
    SELECT returned_state, returned_attempt_count, returned_fencing_token,
           returned_commit_authorization_id
    INTO v_state, v_attempt, v_fence, v_commit_authorization_id
    FROM hwpx_agent.lease_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000001',
        'd8000000-0000-0000-0000-000000000001',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000001', 60, repeat('5', 64)
    );
    IF ROW(v_state, v_attempt, v_fence) IS DISTINCT FROM ROW('in_progress'::text, 1, 1::bigint)
       OR NOT EXISTS (
            SELECT 1 FROM hwpx_agent.job_attempts
            WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
              AND project_id = 'd2000000-0000-0000-0000-000000000001'
              AND job_id = 'd8000000-0000-0000-0000-000000000001'
              AND attempt_no = 1 AND fencing_token = 1 AND state = 'leased'
       ) OR NOT EXISTS (
            SELECT 1 FROM hwpx_agent.idempotency_commit_authorizations
            WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
              AND project_id = 'd2000000-0000-0000-0000-000000000001'
              AND idempotency_key = 'd7000000-0000-0000-0000-000000000001'
              AND job_id = 'd8000000-0000-0000-0000-000000000001'
              AND agent_instance_id = 'd9000000-0000-0000-0000-000000000001'
              AND execution_id = 'da000000-0000-0000-0000-000000000001'
              AND attempt_no = 1 AND fencing_token = 1
              AND commit_authorization_id = v_commit_authorization_id
              AND transaction_receipt_sha256 = repeat('f', 64)
       ) THEN RAISE EXCEPTION 'assertion 10 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 11: a wrong commit capability and a stale fence cannot use the live attempt.
    BEGIN
        PERFORM set_config(
            'hwpx_agent.commit_authorization_id',
            '00000000-0000-0000-0000-000000000001', true
        );
        PERFORM * FROM hwpx_agent.commit_revision_cas(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001',
            'd3000000-0000-0000-0000-000000000001', repeat('a', 64),
            'dc000000-0000-0000-0000-000000000007', NULL, 0,
            'db000000-0000-0000-0000-000000000007', ARRAY[]::uuid[],
            'd4000000-0000-0000-0000-000000000001',
            'd4000000-0000-0000-0000-000000000004', NULL,
            repeat('3', 64), 'verified', repeat('4', 64), repeat('f', 64),
            repeat('7', 64), repeat('8', 64)
        );
        RAISE EXCEPTION 'assertion 11 wrong capability unexpectedly succeeded';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'IDEMPOTENCY_COMMIT_CAPABILITY_MISMATCH' THEN RAISE; END IF;
    END;
    PERFORM set_config('hwpx_agent.commit_authorization_id', '', true);
    BEGIN
        PERFORM * FROM hwpx_agent.advance_idempotent_job_v2(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'd7000000-0000-0000-0000-000000000001',
            'd8000000-0000-0000-0000-000000000001',
            'd9000000-0000-0000-0000-000000000001',
            'da000000-0000-0000-0000-000000000001', 1, 2,
            'leased', 'staged', repeat('6', 64)
        );
        RAISE EXCEPTION 'assertion 11 unexpectedly succeeded';
    EXCEPTION WHEN serialization_failure THEN
        IF SQLERRM <> 'IDEMPOTENCY_LEASE_MISMATCH' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 12: the exact attempt advances through the bounded stage chain.
    PERFORM * FROM hwpx_agent.advance_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000001',
        'd8000000-0000-0000-0000-000000000001',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000001', 1, 1,
        'leased', 'staged', repeat('6', 64)
    );
    PERFORM * FROM hwpx_agent.advance_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000001',
        'd8000000-0000-0000-0000-000000000001',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000001', 1, 1,
        'staged', 'executing', repeat('6', 64)
    );
    PERFORM * FROM hwpx_agent.advance_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000001',
        'd8000000-0000-0000-0000-000000000001',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000001', 1, 1,
        'executing', 'validating', repeat('6', 64)
    );
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.jobs
        WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
          AND project_id = 'd2000000-0000-0000-0000-000000000001'
          AND job_id = 'd8000000-0000-0000-0000-000000000001'
          AND state = 'validating' AND attempt_count = 1 AND fencing_token = 1
    ) THEN RAISE EXCEPTION 'assertion 12 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 13: automation-no-effect cannot bypass the outcome-unknown reconciliation path.
    BEGIN
        PERFORM * FROM hwpx_agent.schedule_idempotent_retry_v2(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'd7000000-0000-0000-0000-000000000001',
            'd8000000-0000-0000-0000-000000000001',
            'd9000000-0000-0000-0000-000000000001',
            'da000000-0000-0000-0000-000000000001', 1, 1,
            'automation_no_effect',
            'd4000000-0000-0000-0000-000000000002', repeat('7', 64)
        );
        RAISE EXCEPTION 'assertion 13 unexpectedly succeeded';
    EXCEPTION WHEN invalid_parameter_value THEN
        IF SQLERRM <> 'IDEMPOTENCY_RETRY_CLASS_INVALID' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 14: retry revokes the old fence's commit authorization before any later effect.
    SELECT returned_state, returned_retry_not_before
    INTO v_state, v_retry_at
    FROM hwpx_agent.schedule_idempotent_retry_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000001',
        'd8000000-0000-0000-0000-000000000001',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000001', 1, 1,
        'transient_storage',
        'd4000000-0000-0000-0000-000000000002', repeat('7', 64)
    );
    IF v_state <> 'retry_pending' OR v_retry_at <= clock_timestamp()
       OR EXISTS (
            SELECT 1 FROM hwpx_agent.idempotency_commit_authorizations
            WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
              AND project_id = 'd2000000-0000-0000-0000-000000000001'
              AND idempotency_key = 'd7000000-0000-0000-0000-000000000001'
       ) OR NOT EXISTS (
            SELECT 1 FROM hwpx_agent.job_attempts
            WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
              AND project_id = 'd2000000-0000-0000-0000-000000000001'
              AND job_id = 'd8000000-0000-0000-0000-000000000001'
              AND attempt_no = 1 AND state = 'failed'
       ) THEN RAISE EXCEPTION 'assertion 14 failed'; END IF;
    BEGIN
        PERFORM * FROM hwpx_agent.commit_idempotent_revision_cas_v2(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001',
            'd3000000-0000-0000-0000-000000000001', repeat('a', 64),
            'd7000000-0000-0000-0000-000000000001',
            'd8000000-0000-0000-0000-000000000001',
            'd9000000-0000-0000-0000-000000000001',
            'da000000-0000-0000-0000-000000000001', 1, 1,
            v_commit_authorization_id,
            'dc000000-0000-0000-0000-000000000009', NULL, 0,
            'db000000-0000-0000-0000-000000000009', ARRAY[]::uuid[],
            'd4000000-0000-0000-0000-000000000001',
            'd4000000-0000-0000-0000-000000000004', NULL,
            repeat('3', 64), 'verified', repeat('4', 64), repeat('f', 64),
            repeat('8', 64), repeat('9', 64)
        );
        RAISE EXCEPTION 'assertion 14 late commit unexpectedly succeeded';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'IDEMPOTENCY_COMMIT_AUTHORIZATION_REQUIRED' THEN RAISE; END IF;
    END;
    BEGIN
        PERFORM * FROM hwpx_agent.commit_revision_cas(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001',
            'd3000000-0000-0000-0000-000000000001', repeat('a', 64),
            'dc000000-0000-0000-0000-000000000008', NULL, 0,
            'db000000-0000-0000-0000-000000000008', ARRAY[]::uuid[],
            'd4000000-0000-0000-0000-000000000001',
            'd4000000-0000-0000-0000-000000000004', NULL,
            repeat('3', 64), 'verified', repeat('4', 64), repeat('0', 64),
            repeat('7', 64), repeat('8', 64)
        );
        RAISE EXCEPTION 'assertion 14 unbound commit unexpectedly succeeded';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'IDEMPOTENCY_COMMIT_AUTHORIZATION_REQUIRED' THEN RAISE; END IF;
    END;
    IF EXISTS (
        SELECT 1 FROM hwpx_agent.revisions
        WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
          AND project_id = 'd2000000-0000-0000-0000-000000000001'
          AND revision_id = 'db000000-0000-0000-0000-000000000009'
    ) OR EXISTS (
        SELECT 1 FROM hwpx_agent.revisions
        WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
          AND project_id = 'd2000000-0000-0000-0000-000000000001'
          AND revision_id = 'db000000-0000-0000-0000-000000000008'
    ) OR EXISTS (
        SELECT 1 FROM hwpx_agent.branches
        WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
          AND project_id = 'd2000000-0000-0000-0000-000000000001'
          AND branch_id = 'd3000000-0000-0000-0000-000000000001'
          AND (head_revision_id IS NOT NULL OR head_generation <> 0)
    ) THEN RAISE EXCEPTION 'assertion 14 late commit mutated durable state'; END IF;
    v_assertions := v_assertions + 1;

    -- 15: deterministic backoff is enforced before the next lease.
    BEGIN
        PERFORM * FROM hwpx_agent.lease_idempotent_job_v2(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'd7000000-0000-0000-0000-000000000001',
            'd8000000-0000-0000-0000-000000000001',
            'd9000000-0000-0000-0000-000000000001',
            'da000000-0000-0000-0000-000000000002', 60, repeat('8', 64)
        );
        RAISE EXCEPTION 'assertion 15 unexpectedly succeeded';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN
        IF SQLERRM <> 'IDEMPOTENCY_RETRY_NOT_READY' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    PERFORM pg_sleep(1.1);
    -- 16: retry lease advances both attempt and fencing token exactly once.
    SELECT returned_attempt_count, returned_fencing_token
    INTO v_attempt, v_fence
    FROM hwpx_agent.lease_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000001',
        'd8000000-0000-0000-0000-000000000001',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000002', 60, repeat('8', 64)
    );
    IF ROW(v_attempt, v_fence) IS DISTINCT FROM ROW(2, 2::bigint) THEN
        RAISE EXCEPTION 'assertion 16 failed';
    END IF;
    v_assertions := v_assertions + 1;

    -- 17: an automation timeout freezes the second effect.
    SELECT returned_state, returned_terminal_error_code
    INTO v_state, v_error
    FROM hwpx_agent.mark_idempotent_outcome_unknown_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000001',
        'd8000000-0000-0000-0000-000000000001',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000002', 2, 2,
        'd4000000-0000-0000-0000-000000000003', repeat('9', 64)
    );
    IF v_state <> 'outcome_unknown' OR v_error <> 'OUTCOME_UNKNOWN' THEN
        RAISE EXCEPTION 'assertion 17 failed';
    END IF;
    v_assertions := v_assertions + 1;

    -- 18: no lease can start while outcome remains unknown.
    BEGIN
        PERFORM * FROM hwpx_agent.lease_idempotent_job_v2(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'd7000000-0000-0000-0000-000000000001',
            'd8000000-0000-0000-0000-000000000001',
            'd9000000-0000-0000-0000-000000000001',
            'da000000-0000-0000-0000-000000000003', 60, repeat('a', 64)
        );
        RAISE EXCEPTION 'assertion 18 unexpectedly succeeded';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN
        IF SQLERRM <> 'IDEMPOTENCY_LEASE_STATE_INVALID' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 19: a caller-supplied nonexistent committed revision cannot thaw the record.
    BEGIN
        PERFORM * FROM hwpx_agent.reconcile_idempotent_job_v2(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'd7000000-0000-0000-0000-000000000001',
            'd8000000-0000-0000-0000-000000000001', 'committed',
            'db000000-0000-0000-0000-000000000099',
            'd4000000-0000-0000-0000-000000000005', repeat('b', 64)
        );
        RAISE EXCEPTION 'assertion 19 unexpectedly succeeded';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN
        IF SQLERRM <> 'IDEMPOTENCY_COMMITTED_ORACLE_FAILED' THEN RAISE; END IF;
    END;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.idempotency_records
        WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
          AND project_id = 'd2000000-0000-0000-0000-000000000001'
          AND idempotency_key = 'd7000000-0000-0000-0000-000000000001'
          AND state = 'outcome_unknown'
    ) THEN RAISE EXCEPTION 'assertion 19 mutated frozen record'; END IF;
    v_assertions := v_assertions + 1;

    -- 20: independently observed unchanged source/head proves no effect and schedules retry.
    SELECT returned_state, returned_retry_not_before
    INTO v_state, v_retry_at
    FROM hwpx_agent.reconcile_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000001',
        'd8000000-0000-0000-0000-000000000001', 'no_effect', NULL,
        'd4000000-0000-0000-0000-000000000002', repeat('c', 64)
    );
    IF v_state <> 'retry_pending' OR v_retry_at <= clock_timestamp() THEN
        RAISE EXCEPTION 'assertion 20 failed';
    END IF;
    v_assertions := v_assertions + 1;

    PERFORM pg_sleep(2.1);
    -- 21: the third and final attempt gets fence 3, never fence reuse.
    SELECT returned_attempt_count, returned_fencing_token
    INTO v_attempt, v_fence
    FROM hwpx_agent.lease_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000001',
        'd8000000-0000-0000-0000-000000000001',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000003', 60, repeat('d', 64)
    );
    IF ROW(v_attempt, v_fence) IS DISTINCT FROM ROW(3, 3::bigint) THEN
        RAISE EXCEPTION 'assertion 21 failed';
    END IF;
    v_assertions := v_assertions + 1;

    -- 22: schema/validation/planning failures are terminal and all attempts stay immutable/dense.
    SELECT returned_state, returned_terminal_error_code
    INTO v_state, v_error
    FROM hwpx_agent.fail_idempotent_job_terminal_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000001',
        'd8000000-0000-0000-0000-000000000001',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000003', 3, 3,
        'schema', 'SCHEMA_REJECTED',
        'd4000000-0000-0000-0000-000000000010', repeat('e', 64)
    );
    SELECT count(*) INTO v_count FROM hwpx_agent.job_attempts
    WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
      AND project_id = 'd2000000-0000-0000-0000-000000000001'
      AND job_id = 'd8000000-0000-0000-0000-000000000001'
      AND attempt_no = fencing_token AND state_machine_version = 2
      AND state IN ('failed', 'unknown_outcome');
    IF v_state <> 'terminal_failure' OR v_error <> 'SCHEMA_REJECTED' OR v_count <> 3 THEN
        RAISE EXCEPTION 'assertion 22 failed';
    END IF;
    v_assertions := v_assertions + 1;

    -- 23: direct success is accepted only after the exact sealed commit oracle exists.
    PERFORM * FROM hwpx_agent.claim_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd3000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000002',
        'd8000000-0000-0000-0000-000000000002',
        'd8100000-0000-0000-0000-000000000002',
        'd4000000-0000-0000-0000-000000000001', NULL, 0,
        repeat('1', 64), repeat('2', 64), v_source1_sha,
        v_result1_sha, v_tx1_sha, repeat('3', 64),
        'hancom-hangul-2020-current-pc', repeat('c', 64),
        3, 1, 4, 600, repeat('4', 64)
    );
    SELECT returned_commit_authorization_id INTO v_commit_authorization_id
    FROM hwpx_agent.lease_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000002',
        'd8000000-0000-0000-0000-000000000002',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000011', 60, repeat('5', 64)
    );
    PERFORM * FROM hwpx_agent.advance_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000002',
        'd8000000-0000-0000-0000-000000000002',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000011', 1, 1,
        'leased', 'staged', repeat('6', 64)
    );
    PERFORM * FROM hwpx_agent.advance_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000002',
        'd8000000-0000-0000-0000-000000000002',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000011', 1, 1,
        'staged', 'executing', repeat('6', 64)
    );
    PERFORM * FROM hwpx_agent.advance_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000002',
        'd8000000-0000-0000-0000-000000000002',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000011', 1, 1,
        'executing', 'validating', repeat('6', 64)
    );
    PERFORM * FROM hwpx_agent.commit_idempotent_revision_cas_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd3000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000002',
        'd8000000-0000-0000-0000-000000000002',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000011', 1, 1,
        v_commit_authorization_id,
        'dc000000-0000-0000-0000-000000000001', NULL, 0,
        'db000000-0000-0000-0000-000000000001', ARRAY[]::uuid[],
        'd4000000-0000-0000-0000-000000000001',
        'd4000000-0000-0000-0000-000000000004', NULL,
        repeat('3', 64), 'verified', repeat('4', 64), v_tx1_sha,
        repeat('5', 64), repeat('6', 64)
    );
    SELECT returned_state, returned_result_revision_id
    INTO v_state, v_result_revision_id
    FROM hwpx_agent.complete_idempotent_job_success_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000002',
        'd8000000-0000-0000-0000-000000000002',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000011', 1, 1,
        'db000000-0000-0000-0000-000000000001',
        'd4000000-0000-0000-0000-000000000005', repeat('7', 64)
    );
    IF v_state <> 'terminal_success'
       OR v_result_revision_id <> 'db000000-0000-0000-0000-000000000001'::uuid THEN
        RAISE EXCEPTION 'assertion 23 failed';
    END IF;
    v_assertions := v_assertions + 1;

    -- 24: a terminal exact replay returns the bound result without another effect.
    SELECT returned_outcome, returned_state, returned_result_revision_id
    INTO v_outcome, v_state, v_result_revision_id
    FROM hwpx_agent.claim_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd3000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000002',
        'd8000000-0000-0000-0000-000000000002',
        'd8100000-0000-0000-0000-000000000002',
        'd4000000-0000-0000-0000-000000000001', NULL, 0,
        repeat('1', 64), repeat('2', 64), v_source1_sha,
        v_result1_sha, v_tx1_sha, repeat('3', 64),
        'hancom-hangul-2020-current-pc', repeat('c', 64),
        3, 1, 4, 600, repeat('4', 64)
    );
    IF v_outcome <> 'replay' OR v_state <> 'terminal_success'
       OR v_result_revision_id <> 'db000000-0000-0000-0000-000000000001'::uuid THEN
        RAISE EXCEPTION 'assertion 24 failed';
    END IF;
    v_assertions := v_assertions + 1;

    -- 25: a committed-but-timed-out effect is recovered only from the exact DB oracle join.
    PERFORM * FROM hwpx_agent.claim_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd3000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000003',
        'd8000000-0000-0000-0000-000000000003',
        'd8100000-0000-0000-0000-000000000003',
        'd4000000-0000-0000-0000-000000000006',
        'db000000-0000-0000-0000-000000000001', 1,
        repeat('7', 64), repeat('8', 64), v_source2_sha,
        v_result2_sha, v_tx2_sha, repeat('9', 64),
        'hancom-hangul-2020-current-pc', repeat('c', 64),
        3, 1, 4, 600, repeat('a', 64)
    );
    SELECT returned_commit_authorization_id INTO v_commit_authorization_id
    FROM hwpx_agent.lease_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000003',
        'd8000000-0000-0000-0000-000000000003',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000021', 60, repeat('b', 64)
    );
    PERFORM * FROM hwpx_agent.advance_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000003',
        'd8000000-0000-0000-0000-000000000003',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000021', 1, 1,
        'leased', 'staged', repeat('c', 64)
    );
    PERFORM * FROM hwpx_agent.advance_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000003',
        'd8000000-0000-0000-0000-000000000003',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000021', 1, 1,
        'staged', 'executing', repeat('c', 64)
    );
    PERFORM * FROM hwpx_agent.advance_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000003',
        'd8000000-0000-0000-0000-000000000003',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000021', 1, 1,
        'executing', 'validating', repeat('c', 64)
    );
    PERFORM * FROM hwpx_agent.commit_idempotent_revision_cas_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd3000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000003',
        'd8000000-0000-0000-0000-000000000003',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000021', 1, 1,
        v_commit_authorization_id,
        'dc000000-0000-0000-0000-000000000002',
        'db000000-0000-0000-0000-000000000001', 1,
        'db000000-0000-0000-0000-000000000002',
        ARRAY['db000000-0000-0000-0000-000000000001'::uuid],
        'd4000000-0000-0000-0000-000000000006',
        'd4000000-0000-0000-0000-000000000007', NULL,
        repeat('9', 64), 'verified', repeat('a', 64), v_tx2_sha,
        repeat('b', 64), repeat('c', 64)
    );
    PERFORM * FROM hwpx_agent.mark_idempotent_outcome_unknown_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000003',
        'd8000000-0000-0000-0000-000000000003',
        'd9000000-0000-0000-0000-000000000001',
        'da000000-0000-0000-0000-000000000021', 1, 1,
        'd4000000-0000-0000-0000-000000000009', repeat('d', 64)
    );
    SELECT returned_outcome, returned_state, returned_result_revision_id
    INTO v_outcome, v_state, v_result_revision_id
    FROM hwpx_agent.reconcile_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000003',
        'd8000000-0000-0000-0000-000000000003', 'committed',
        'db000000-0000-0000-0000-000000000002',
        'd4000000-0000-0000-0000-000000000008', repeat('e', 64)
    );
    IF v_outcome <> 'committed' OR v_state <> 'terminal_success'
       OR v_result_revision_id <> 'db000000-0000-0000-0000-000000000002'::uuid
       OR NOT EXISTS (
            SELECT 1 FROM hwpx_agent.job_attempts
            WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
              AND project_id = 'd2000000-0000-0000-0000-000000000001'
              AND job_id = 'd8000000-0000-0000-0000-000000000003'
              AND attempt_no = 1 AND state = 'unknown_outcome'
       ) THEN RAISE EXCEPTION 'assertion 25 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 26: readers from another subject cannot discover a v2 idempotency record.
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('b', 64), true);
    BEGIN
        PERFORM * FROM hwpx_agent.get_idempotent_job_v2(
            'd1000000-0000-0000-0000-000000000001',
            'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'd7000000-0000-0000-0000-000000000003'
        );
        RAISE EXCEPTION 'assertion 26 unexpectedly succeeded';
    EXCEPTION WHEN no_data_found THEN
        IF SQLERRM <> 'IDEMPOTENCY_RECORD_NOT_FOUND' THEN RAISE; END IF;
    END;
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);
    v_assertions := v_assertions + 1;

    -- 27: the owning subject reads the exact terminal state and fence.
    SELECT returned_state, returned_attempt_count, returned_fencing_token,
           returned_result_revision_id
    INTO v_state, v_attempt, v_fence, v_result_revision_id
    FROM hwpx_agent.get_idempotent_job_v2(
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'd7000000-0000-0000-0000-000000000003'
    );
    IF ROW(v_state, v_attempt, v_fence, v_result_revision_id)
       IS DISTINCT FROM ROW(
            'terminal_success'::text, 1, 1::bigint,
            'db000000-0000-0000-0000-000000000002'::uuid
       ) THEN RAISE EXCEPTION 'assertion 27 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 28: audit events and final state mapping exist without cross-tenant leakage.
    SELECT count(*) INTO v_count FROM hwpx_agent.audit_events
    WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
      AND event_type LIKE 'idempotency.v2_%';
    IF v_count < 15 OR EXISTS (
        SELECT 1 FROM hwpx_agent.idempotency_records
        WHERE tenant_id = 'd1000000-0000-0000-0000-000000000002'
          AND record_version = 2
    ) OR EXISTS (
        SELECT 1 FROM hwpx_agent.idempotency_commit_authorizations
    ) THEN RAISE EXCEPTION 'assertion 28 failed'; END IF;
    v_assertions := v_assertions + 1;

    IF v_assertions <> 28 THEN RAISE EXCEPTION 'assertion count mismatch'; END IF;
    RAISE NOTICE 'P14_IDEMPOTENCY_RECONCILIATION_SMOKE_PASS assertions=%', v_assertions;
END
$$;

SET CONSTRAINTS ALL IMMEDIATE;
SELECT 'P14_IDEMPOTENCY_RECONCILIATION_SMOKE_PASS assertions=28';
ROLLBACK;
