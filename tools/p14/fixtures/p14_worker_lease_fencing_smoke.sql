BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hwpx_agent_scheduler_test_app') THEN
        CREATE ROLE hwpx_agent_scheduler_test_app
            NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
    END IF;
END
$$;

GRANT USAGE ON SCHEMA hwpx_agent TO hwpx_agent_scheduler_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.register_scheduler_worker(
    uuid, character, uuid, text, character, text, integer, character
) TO hwpx_agent_scheduler_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.heartbeat_scheduler_worker(
    uuid, character, uuid, text, character, text, integer, character
) TO hwpx_agent_scheduler_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.enqueue_job_state_machine(
    uuid, uuid, character, uuid, uuid, uuid, uuid, character, text, character
) TO hwpx_agent_scheduler_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.lease_job_state_machine(
    uuid, uuid, character, uuid, uuid, uuid, integer, character
) TO hwpx_agent_scheduler_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.heartbeat_job_lease(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, integer, character
) TO hwpx_agent_scheduler_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.advance_job_state_machine(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, text, text, character
) TO hwpx_agent_scheduler_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.commit_job_success(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, uuid, uuid, character
) TO hwpx_agent_scheduler_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.expire_job_lease(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, uuid, character
) TO hwpx_agent_scheduler_test_app;

INSERT INTO hwpx_agent.tenants (tenant_id, slug) VALUES
    ('c1000000-0000-0000-0000-000000000001', 'scheduler-tenant-primary'),
    ('c1000000-0000-0000-0000-000000000002', 'scheduler-tenant-other');
INSERT INTO hwpx_agent.projects (
    tenant_id, project_id, slug, display_name, target_profile_id, retention_policy_id
) VALUES (
    'c1000000-0000-0000-0000-000000000001',
    'c2000000-0000-0000-0000-000000000001',
    'scheduler-project', 'Scheduler Project', 'hancom-hangul-2020-current-pc',
    'retention.local-test'
);
INSERT INTO hwpx_agent.project_acl (tenant_id, project_id, subject_sha256, role) VALUES
    (
        'c1000000-0000-0000-0000-000000000001',
        'c2000000-0000-0000-0000-000000000001', repeat('a', 64), 'owner'
    ),
    (
        'c1000000-0000-0000-0000-000000000001',
        'c2000000-0000-0000-0000-000000000001', repeat('b', 64), 'editor'
    );

WITH artifact_seed AS (
    SELECT
        ordinal,
        concat('c4000000-0000-0000-0000-', lpad(ordinal::text, 12, '0'))::uuid AS artifact_id,
        lpad(to_hex(ordinal + 700), 64, '0') AS content_sha256,
        CASE WHEN ordinal = 1 THEN 'source'
             WHEN ordinal IN (2, 3) THEN 'receipt'
             ELSE 'result' END AS artifact_kind
    FROM generate_series(1, 4) AS ordinal
)
INSERT INTO hwpx_agent.artifacts (
    tenant_id, artifact_id, content_sha256, size_bytes, media_type, artifact_kind,
    storage_state, encryption_key_ref, verified_at, service_metadata_version, filename,
    object_key, encryption_algorithm, encryption_nonce, aad_sha256, ciphertext_sha256,
    validation_state, scanner_engine_ref, scanner_signature_version,
    authorization_generation
)
SELECT
    'c1000000-0000-0000-0000-000000000001', artifact_id, content_sha256,
    ordinal, 'application/octet-stream', artifact_kind, 'available',
    'kms.scheduler-test', transaction_timestamp(), 1,
    concat('artifact-', ordinal, '.bin'),
    concat(
        'artifacts/v1/c1000000000000000000000000000001/', artifact_kind,
        '/available/', content_sha256, '.aes256gcm'
    ),
    'AES-256-GCM', decode(lpad(to_hex(ordinal), 24, '0'), 'hex'),
    lpad(to_hex(ordinal + 800), 64, '0'), lpad(to_hex(ordinal + 900), 64, '0'),
    'verified', 'scanner.scheduler-test', 'v1', 1
FROM artifact_seed;

INSERT INTO hwpx_agent.artifact_acl (
    tenant_id, artifact_id, subject_sha256, can_read, can_manage
)
SELECT
    'c1000000-0000-0000-0000-000000000001', artifact_id,
    repeat('a', 64), true, true
FROM hwpx_agent.artifacts
WHERE tenant_id = 'c1000000-0000-0000-0000-000000000001';

INSERT INTO hwpx_agent.revisions (
    tenant_id, project_id, revision_id, source_artifact_id, result_artifact_id,
    semantic_diff_artifact_id, operation_plan_sha256, validation_state,
    validation_summary_sha256, created_by_subject_sha256
) VALUES (
    'c1000000-0000-0000-0000-000000000001',
    'c2000000-0000-0000-0000-000000000001',
    'c5000000-0000-0000-0000-000000000001',
    'c4000000-0000-0000-0000-000000000001',
    'c4000000-0000-0000-0000-000000000004', NULL,
    repeat('1', 64), 'verified', repeat('2', 64), repeat('a', 64)
);
INSERT INTO hwpx_agent.revision_graph_seals (
    tenant_id, project_id, revision_id, seal_kind, parent_count,
    committed_generation, commit_id, commit_request_sha256,
    transaction_receipt_sha256
) VALUES (
    'c1000000-0000-0000-0000-000000000001',
    'c2000000-0000-0000-0000-000000000001',
    'c5000000-0000-0000-0000-000000000001', 'service_v1', 0, 1,
    'c6000000-0000-0000-0000-000000000001', repeat('3', 64), repeat('4', 64)
);

SELECT set_config(
    'hwpx_agent.tenant_id', 'c1000000-0000-0000-0000-000000000001', true
);
SELECT set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);

DO $$
DECLARE
    v_assertions integer := 0;
    v_count bigint;
    v_state text;
    v_error text;
    v_fence bigint;
    v_old_expiry timestamptz;
    v_new_expiry timestamptz;
BEGIN
    -- 01: v6 schema, forced RLS, trigger and public revokes exist.
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 6 AND migration_name = 'p14.worker_lease_fencing_v1'
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_class AS relation
        JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
        WHERE namespace.nspname = 'hwpx_agent'
          AND relation.relname = 'worker_registrations'
          AND relation.relrowsecurity AND relation.relforcerowsecurity
    ) OR has_function_privilege(
        'public',
        'hwpx_agent.expire_job_lease(uuid,uuid,character,uuid,uuid,uuid,integer,bigint,uuid,character)',
        'EXECUTE'
    ) THEN RAISE EXCEPTION 'assertion 01 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 02: app role has bounded functions but no direct table mutation.
    IF has_table_privilege(
        'hwpx_agent_scheduler_test_app', 'hwpx_agent.worker_registrations', 'UPDATE'
    ) OR NOT has_function_privilege(
        'hwpx_agent_scheduler_test_app',
        'hwpx_agent.register_scheduler_worker(uuid,character,uuid,text,character,text,integer,character)',
        'EXECUTE'
    ) THEN RAISE EXCEPTION 'assertion 02 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 03: exact worker registration succeeds once.
    SELECT returned_state, returned_expires_at INTO v_state, v_old_expiry
    FROM hwpx_agent.register_scheduler_worker(
        'c1000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c9000000-0000-0000-0000-000000000001',
        'hancom-hangul-2020-current-pc', repeat('2', 64),
        'ready', 300, repeat('5', 64)
    );
    IF v_state <> 'ready' OR v_old_expiry <= clock_timestamp() THEN
        RAISE EXCEPTION 'assertion 03 failed';
    END IF;
    v_assertions := v_assertions + 1;

    -- 04: duplicate registration is refused without changing identity.
    BEGIN
        PERFORM * FROM hwpx_agent.register_scheduler_worker(
            'c1000000-0000-0000-0000-000000000001', repeat('a', 64),
            'c9000000-0000-0000-0000-000000000001',
            'hancom-hangul-2020-current-pc', repeat('2', 64),
            'ready', 300, repeat('5', 64)
        );
        RAISE EXCEPTION 'assertion 04 unexpectedly succeeded';
    EXCEPTION WHEN unique_violation THEN
        IF SQLERRM <> 'WORKER_ALREADY_REGISTERED' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 05: heartbeat rejects profile/capability drift without mutation.
    BEGIN
        PERFORM * FROM hwpx_agent.heartbeat_scheduler_worker(
            'c1000000-0000-0000-0000-000000000001', repeat('a', 64),
            'c9000000-0000-0000-0000-000000000001',
            'hancom-hangul-2024-other', repeat('2', 64),
            'ready', 300, repeat('6', 64)
        );
        RAISE EXCEPTION 'assertion 05 unexpectedly succeeded';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'WORKER_IDENTITY_MISMATCH' THEN RAISE; END IF;
    END;
    SELECT expires_at INTO v_new_expiry FROM hwpx_agent.worker_registrations
    WHERE tenant_id = 'c1000000-0000-0000-0000-000000000001'
      AND agent_instance_id = 'c9000000-0000-0000-0000-000000000001';
    IF v_new_expiry IS DISTINCT FROM v_old_expiry THEN
        RAISE EXCEPTION 'assertion 05 mutated worker';
    END IF;
    v_assertions := v_assertions + 1;

    -- 06: cross-subject worker access is denied.
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('b', 64), true);
    BEGIN
        PERFORM * FROM hwpx_agent.heartbeat_scheduler_worker(
            'c1000000-0000-0000-0000-000000000001', repeat('b', 64),
            'c9000000-0000-0000-0000-000000000001',
            'hancom-hangul-2020-current-pc', repeat('2', 64),
            'ready', 300, repeat('6', 64)
        );
        RAISE EXCEPTION 'assertion 06 unexpectedly succeeded';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'WORKER_IDENTITY_MISMATCH' THEN RAISE; END IF;
    END;
    PERFORM set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);
    SELECT returned_expires_at INTO v_new_expiry
    FROM hwpx_agent.heartbeat_scheduler_worker(
        'c1000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c9000000-0000-0000-0000-000000000001',
        'hancom-hangul-2020-current-pc', repeat('2', 64),
        'ready', 300, repeat('6', 64)
    );
    IF v_new_expiry <= v_old_expiry THEN
        RAISE EXCEPTION 'assertion 06 heartbeat did not extend worker';
    END IF;
    v_old_expiry := v_new_expiry;
    v_assertions := v_assertions + 1;

    -- Seed mismatch, draining and soon-stale workers.
    PERFORM * FROM hwpx_agent.register_scheduler_worker(
        'c1000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c9000000-0000-0000-0000-000000000002',
        'hancom-hangul-2024-other', repeat('2', 64),
        'ready', 300, repeat('7', 64)
    );
    PERFORM * FROM hwpx_agent.register_scheduler_worker(
        'c1000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c9000000-0000-0000-0000-000000000003',
        'hancom-hangul-2020-current-pc', repeat('3', 64),
        'ready', 300, repeat('7', 64)
    );
    PERFORM * FROM hwpx_agent.register_scheduler_worker(
        'c1000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c9000000-0000-0000-0000-000000000004',
        'hancom-hangul-2020-current-pc', repeat('2', 64),
        'draining', 300, repeat('7', 64)
    );
    PERFORM * FROM hwpx_agent.register_scheduler_worker(
        'c1000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c9000000-0000-0000-0000-000000000005',
        'hancom-hangul-2020-current-pc', repeat('2', 64),
        'ready', 1, repeat('7', 64)
    );

    PERFORM * FROM hwpx_agent.enqueue_job_state_machine(
        'c1000000-0000-0000-0000-000000000001',
        'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c7000000-0000-0000-0000-000000000001',
        'c8000000-0000-0000-0000-000000000001',
        'c4000000-0000-0000-0000-000000000001', NULL, repeat('1', 64),
        'hancom-hangul-2020-current-pc', repeat('2', 64)
    );

    -- 07: mismatched target profile cannot lease through the legacy v5 function.
    BEGIN
        PERFORM * FROM hwpx_agent.lease_job_state_machine(
            'c1000000-0000-0000-0000-000000000001',
            'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'c7000000-0000-0000-0000-000000000001',
            'c9000000-0000-0000-0000-000000000002',
            'ca000000-0000-0000-0000-000000000002', 120, repeat('8', 64)
        );
        RAISE EXCEPTION 'assertion 07 unexpectedly succeeded';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'JOB_WORKER_NOT_QUALIFIED' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 08: mismatched capabilities cannot lease.
    BEGIN
        PERFORM * FROM hwpx_agent.lease_job_state_machine(
            'c1000000-0000-0000-0000-000000000001',
            'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'c7000000-0000-0000-0000-000000000001',
            'c9000000-0000-0000-0000-000000000003',
            'ca000000-0000-0000-0000-000000000003', 120, repeat('8', 64)
        );
        RAISE EXCEPTION 'assertion 08 unexpectedly succeeded';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'JOB_WORKER_NOT_QUALIFIED' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 09: draining workers cannot lease.
    BEGIN
        PERFORM * FROM hwpx_agent.lease_job_state_machine(
            'c1000000-0000-0000-0000-000000000001',
            'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'c7000000-0000-0000-0000-000000000001',
            'c9000000-0000-0000-0000-000000000004',
            'ca000000-0000-0000-0000-000000000004', 120, repeat('8', 64)
        );
        RAISE EXCEPTION 'assertion 09 unexpectedly succeeded';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'JOB_WORKER_NOT_QUALIFIED' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 10: a job lease may not outlive the worker heartbeat.
    BEGIN
        PERFORM * FROM hwpx_agent.lease_job_state_machine(
            'c1000000-0000-0000-0000-000000000001',
            'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'c7000000-0000-0000-0000-000000000001',
            'c9000000-0000-0000-0000-000000000005',
            'ca000000-0000-0000-0000-000000000005', 120, repeat('8', 64)
        );
        RAISE EXCEPTION 'assertion 10 unexpectedly succeeded';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'JOB_WORKER_NOT_QUALIFIED' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 11: exact worker receives attempt 1 and fencing token 1.
    SELECT returned_state, returned_fencing_token INTO v_state, v_fence
    FROM hwpx_agent.lease_job_state_machine(
        'c1000000-0000-0000-0000-000000000001',
        'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c7000000-0000-0000-0000-000000000001',
        'c9000000-0000-0000-0000-000000000001',
        'ca000000-0000-0000-0000-000000000001', 120, repeat('8', 64)
    );
    IF v_state <> 'leased' OR v_fence <> 1 THEN
        RAISE EXCEPTION 'assertion 11 failed';
    END IF;
    SELECT lease_expires_at INTO v_old_expiry FROM hwpx_agent.jobs
    WHERE tenant_id = 'c1000000-0000-0000-0000-000000000001'
      AND project_id = 'c2000000-0000-0000-0000-000000000001'
      AND job_id = 'c7000000-0000-0000-0000-000000000001';
    v_assertions := v_assertions + 1;

    -- 12: bounded heartbeat extends both job and attempt under the same fence.
    SELECT returned_lease_expires_at, returned_fencing_token
    INTO v_new_expiry, v_fence
    FROM hwpx_agent.heartbeat_job_lease(
        'c1000000-0000-0000-0000-000000000001',
        'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c7000000-0000-0000-0000-000000000001',
        'c9000000-0000-0000-0000-000000000001',
        'ca000000-0000-0000-0000-000000000001', 1, 1, 180, repeat('9', 64)
    );
    IF v_new_expiry <= v_old_expiry OR v_fence <> 1 OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.job_attempts
        WHERE tenant_id = 'c1000000-0000-0000-0000-000000000001'
          AND project_id = 'c2000000-0000-0000-0000-000000000001'
          AND job_id = 'c7000000-0000-0000-0000-000000000001'
          AND lease_expires_at = v_new_expiry
    ) THEN RAISE EXCEPTION 'assertion 12 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 13: direct same-state lease extension cannot open the guarded path.
    BEGIN
        UPDATE hwpx_agent.jobs
        SET lease_expires_at = lease_expires_at + interval '1 second'
        WHERE tenant_id = 'c1000000-0000-0000-0000-000000000001'
          AND project_id = 'c2000000-0000-0000-0000-000000000001'
          AND job_id = 'c7000000-0000-0000-0000-000000000001';
        RAISE EXCEPTION 'assertion 13 unexpectedly succeeded';
    EXCEPTION WHEN SQLSTATE '55000' THEN
        IF SQLERRM <> 'JOB_HEARTBEAT_INVALID' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 14: stale fencing token cannot advance.
    BEGIN
        PERFORM * FROM hwpx_agent.advance_job_state_machine(
            'c1000000-0000-0000-0000-000000000001',
            'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'c7000000-0000-0000-0000-000000000001',
            'c9000000-0000-0000-0000-000000000001',
            'ca000000-0000-0000-0000-000000000001', 1, 2,
            'leased', 'staged', repeat('a', 64)
        );
        RAISE EXCEPTION 'assertion 14 unexpectedly succeeded';
    EXCEPTION WHEN invalid_parameter_value THEN
        IF SQLERRM <> 'JOB_STAGE_REQUEST_INVALID' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 15: live lease retains the exact stage chain and success path.
    PERFORM * FROM hwpx_agent.advance_job_state_machine(
        'c1000000-0000-0000-0000-000000000001',
        'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c7000000-0000-0000-0000-000000000001',
        'c9000000-0000-0000-0000-000000000001',
        'ca000000-0000-0000-0000-000000000001', 1, 1,
        'leased', 'staged', repeat('a', 64)
    );
    PERFORM * FROM hwpx_agent.advance_job_state_machine(
        'c1000000-0000-0000-0000-000000000001',
        'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c7000000-0000-0000-0000-000000000001',
        'c9000000-0000-0000-0000-000000000001',
        'ca000000-0000-0000-0000-000000000001', 1, 1,
        'staged', 'executing', repeat('a', 64)
    );
    PERFORM * FROM hwpx_agent.advance_job_state_machine(
        'c1000000-0000-0000-0000-000000000001',
        'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c7000000-0000-0000-0000-000000000001',
        'c9000000-0000-0000-0000-000000000001',
        'ca000000-0000-0000-0000-000000000001', 1, 1,
        'executing', 'validating', repeat('a', 64)
    );
    SELECT returned_state INTO v_state FROM hwpx_agent.commit_job_success(
        'c1000000-0000-0000-0000-000000000001',
        'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c7000000-0000-0000-0000-000000000001',
        'c9000000-0000-0000-0000-000000000001',
        'ca000000-0000-0000-0000-000000000001', 1, 1,
        'c5000000-0000-0000-0000-000000000001',
        'c4000000-0000-0000-0000-000000000002', repeat('b', 64)
    );
    IF v_state <> 'succeeded' THEN RAISE EXCEPTION 'assertion 15 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 16: soon-expiring job reaches validating while its fence is live.
    PERFORM * FROM hwpx_agent.enqueue_job_state_machine(
        'c1000000-0000-0000-0000-000000000001',
        'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c7000000-0000-0000-0000-000000000002',
        'c8000000-0000-0000-0000-000000000002',
        'c4000000-0000-0000-0000-000000000001', NULL, repeat('1', 64),
        'hancom-hangul-2020-current-pc', repeat('2', 64)
    );
    PERFORM * FROM hwpx_agent.lease_job_state_machine(
        'c1000000-0000-0000-0000-000000000001',
        'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c7000000-0000-0000-0000-000000000002',
        'c9000000-0000-0000-0000-000000000001',
        'ca000000-0000-0000-0000-000000000002', 5, repeat('c', 64)
    );
    PERFORM * FROM hwpx_agent.advance_job_state_machine(
        'c1000000-0000-0000-0000-000000000001',
        'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c7000000-0000-0000-0000-000000000002',
        'c9000000-0000-0000-0000-000000000001',
        'ca000000-0000-0000-0000-000000000002', 1, 1,
        'leased', 'staged', repeat('c', 64)
    );
    PERFORM * FROM hwpx_agent.advance_job_state_machine(
        'c1000000-0000-0000-0000-000000000001',
        'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c7000000-0000-0000-0000-000000000002',
        'c9000000-0000-0000-0000-000000000001',
        'ca000000-0000-0000-0000-000000000002', 1, 1,
        'staged', 'executing', repeat('c', 64)
    );
    PERFORM * FROM hwpx_agent.advance_job_state_machine(
        'c1000000-0000-0000-0000-000000000001',
        'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c7000000-0000-0000-0000-000000000002',
        'c9000000-0000-0000-0000-000000000001',
        'ca000000-0000-0000-0000-000000000002', 1, 1,
        'executing', 'validating', repeat('c', 64)
    );
    SELECT state INTO v_state FROM hwpx_agent.jobs
    WHERE tenant_id = 'c1000000-0000-0000-0000-000000000001'
      AND project_id = 'c2000000-0000-0000-0000-000000000001'
      AND job_id = 'c7000000-0000-0000-0000-000000000002';
    IF v_state <> 'validating' THEN RAISE EXCEPTION 'assertion 16 failed'; END IF;
    BEGIN
        PERFORM * FROM hwpx_agent.expire_job_lease(
            'c1000000-0000-0000-0000-000000000001',
            'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'c7000000-0000-0000-0000-000000000002',
            'c9000000-0000-0000-0000-000000000001',
            'ca000000-0000-0000-0000-000000000002', 1, 1,
            'c4000000-0000-0000-0000-000000000003', repeat('c', 64)
        );
        RAISE EXCEPTION 'assertion 16 expiry unexpectedly succeeded';
    EXCEPTION WHEN SQLSTATE '55000' THEN
        IF SQLERRM <> 'JOB_LEASE_STILL_ACTIVE' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    PERFORM pg_sleep(5.2);

    -- 17: late worker success is rejected at the table guard with no revision commit.
    BEGIN
        PERFORM * FROM hwpx_agent.commit_job_success(
            'c1000000-0000-0000-0000-000000000001',
            'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'c7000000-0000-0000-0000-000000000002',
            'c9000000-0000-0000-0000-000000000001',
            'ca000000-0000-0000-0000-000000000002', 1, 1,
            'c5000000-0000-0000-0000-000000000001',
            'c4000000-0000-0000-0000-000000000002', repeat('d', 64)
        );
        RAISE EXCEPTION 'assertion 17 unexpectedly succeeded';
    EXCEPTION WHEN serialization_failure THEN
        IF SQLERRM <> 'JOB_LEASE_EXPIRED' THEN RAISE; END IF;
    END;
    SELECT state INTO v_state FROM hwpx_agent.jobs
    WHERE tenant_id = 'c1000000-0000-0000-0000-000000000001'
      AND project_id = 'c2000000-0000-0000-0000-000000000001'
      AND job_id = 'c7000000-0000-0000-0000-000000000002';
    IF v_state <> 'validating' THEN RAISE EXCEPTION 'assertion 17 mutated job'; END IF;
    v_assertions := v_assertions + 1;

    -- 18: unqualified expiry receipt is side-effect free.
    BEGIN
        PERFORM * FROM hwpx_agent.expire_job_lease(
            'c1000000-0000-0000-0000-000000000001',
            'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'c7000000-0000-0000-0000-000000000002',
            'c9000000-0000-0000-0000-000000000001',
            'ca000000-0000-0000-0000-000000000002', 1, 1,
            'c4000000-0000-0000-0000-000000000004', repeat('e', 64)
        );
        RAISE EXCEPTION 'assertion 18 unexpectedly succeeded';
    EXCEPTION WHEN foreign_key_violation THEN
        IF SQLERRM <> 'JOB_RECEIPT_ARTIFACT_NOT_QUALIFIED' THEN RAISE; END IF;
    END;
    SELECT state INTO v_state FROM hwpx_agent.jobs
    WHERE tenant_id = 'c1000000-0000-0000-0000-000000000001'
      AND project_id = 'c2000000-0000-0000-0000-000000000001'
      AND job_id = 'c7000000-0000-0000-0000-000000000002';
    IF v_state <> 'validating' THEN RAISE EXCEPTION 'assertion 18 mutated job'; END IF;
    v_assertions := v_assertions + 1;

    -- 19: qualified expiry receipt closes both job and attempt deterministically.
    SELECT returned_state, returned_terminal_error_code
    INTO v_state, v_error
    FROM hwpx_agent.expire_job_lease(
        'c1000000-0000-0000-0000-000000000001',
        'c2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'c7000000-0000-0000-0000-000000000002',
        'c9000000-0000-0000-0000-000000000001',
        'ca000000-0000-0000-0000-000000000002', 1, 1,
        'c4000000-0000-0000-0000-000000000003', repeat('f', 64)
    );
    IF v_state <> 'failed' OR v_error <> 'LEASE_EXPIRED' OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.job_attempts
        WHERE tenant_id = 'c1000000-0000-0000-0000-000000000001'
          AND project_id = 'c2000000-0000-0000-0000-000000000001'
          AND job_id = 'c7000000-0000-0000-0000-000000000002'
          AND state = 'failed'
          AND receipt_artifact_id = 'c4000000-0000-0000-0000-000000000003'
    ) THEN RAISE EXCEPTION 'assertion 19 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 20: expiry, heartbeat and worker audit events are complete and scoped.
    BEGIN
        PERFORM * FROM hwpx_agent.heartbeat_scheduler_worker(
            'c1000000-0000-0000-0000-000000000001', repeat('a', 64),
            'c9000000-0000-0000-0000-000000000005',
            'hancom-hangul-2020-current-pc', repeat('2', 64),
            'ready', 300, repeat('f', 64)
        );
        RAISE EXCEPTION 'assertion 20 stale worker unexpectedly revived';
    EXCEPTION WHEN SQLSTATE '55000' THEN
        IF SQLERRM <> 'WORKER_UNAVAILABLE' THEN RAISE; END IF;
    END;
    SELECT count(*) INTO v_count FROM hwpx_agent.audit_events
    WHERE tenant_id = 'c1000000-0000-0000-0000-000000000001'
      AND event_type IN (
          'worker.registered', 'worker.heartbeat', 'job.heartbeat', 'job.lease_expired'
      );
    IF v_count <> 8 THEN RAISE EXCEPTION 'assertion 20 failed count=%', v_count; END IF;
    v_assertions := v_assertions + 1;

    IF v_assertions <> 20 THEN RAISE EXCEPTION 'assertion count mismatch'; END IF;
    RAISE NOTICE 'P14_WORKER_LEASE_FENCING_SMOKE_PASS assertions=%', v_assertions;
END
$$;

SET CONSTRAINTS ALL IMMEDIATE;
SELECT 'P14_WORKER_LEASE_FENCING_SMOKE_PASS assertions=20';
ROLLBACK;
