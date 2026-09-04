BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hwpx_agent_cleanup_test_app') THEN
        CREATE ROLE hwpx_agent_cleanup_test_app
            NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
    END IF;
END
$$;

GRANT USAGE ON SCHEMA hwpx_agent TO hwpx_agent_cleanup_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.register_scheduler_worker(
    uuid, character, uuid, text, character, text, integer, character
) TO hwpx_agent_cleanup_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.claim_idempotent_job_v2(
    uuid, uuid, uuid, character, uuid, uuid, uuid, uuid, uuid, bigint,
    character, character, character, character, character, character,
    text, character, integer, integer, integer, integer, character
) TO hwpx_agent_cleanup_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.lease_idempotent_job_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, character
) TO hwpx_agent_cleanup_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.advance_idempotent_job_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    text, text, character
) TO hwpx_agent_cleanup_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.request_job_cancellation_v1(
    uuid, uuid, character, uuid, uuid, uuid, uuid, character
) TO hwpx_agent_cleanup_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.mark_job_effect_phase_v1(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, text, character
) TO hwpx_agent_cleanup_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.finalize_job_cancellation_v1(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    uuid, uuid, character
) TO hwpx_agent_cleanup_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.queue_orphan_cleanup_v1(
    uuid, uuid, character, uuid, uuid, uuid, character
) TO hwpx_agent_cleanup_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.claim_cleanup_task_v1(
    uuid, character, uuid, uuid, integer, character
) TO hwpx_agent_cleanup_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.complete_cleanup_task_v1(
    uuid, character, uuid, uuid, uuid, integer, bigint, text, character, character
) TO hwpx_agent_cleanup_test_app;

INSERT INTO hwpx_agent.tenants (tenant_id, slug) VALUES
    ('e1000000-0000-0000-0000-000000000001', 'cleanup-tenant-primary'),
    ('e1000000-0000-0000-0000-000000000002', 'cleanup-tenant-other');
INSERT INTO hwpx_agent.projects (
    tenant_id, project_id, slug, display_name, target_profile_id, retention_policy_id
) VALUES (
    'e1000000-0000-0000-0000-000000000001',
    'e2000000-0000-0000-0000-000000000001',
    'cleanup-project', 'Cleanup Project',
    'hancom-hangul-2020-current-pc', 'retention.local-test'
);
INSERT INTO hwpx_agent.project_acl (tenant_id, project_id, subject_sha256, role) VALUES
    ('e1000000-0000-0000-0000-000000000001',
     'e2000000-0000-0000-0000-000000000001', repeat('a', 64), 'owner'),
    ('e1000000-0000-0000-0000-000000000001',
     'e2000000-0000-0000-0000-000000000001', repeat('b', 64), 'reader');
INSERT INTO hwpx_agent.branches (
    tenant_id, project_id, branch_id, name, is_default, created_by_subject_sha256
) VALUES (
    'e1000000-0000-0000-0000-000000000001',
    'e2000000-0000-0000-0000-000000000001',
    'e3000000-0000-0000-0000-000000000001', 'main', true, repeat('a', 64)
);

WITH artifact_seed AS (
    SELECT ordinal,
        format('e4000000-0000-0000-0000-%s', lpad(ordinal::text, 12, '0'))::uuid AS artifact_id,
        lpad(to_hex(ordinal + 5000), 64, '0') AS content_sha256,
        CASE WHEN ordinal = 1 THEN 'source'
             WHEN ordinal BETWEEN 2 AND 6 THEN 'receipt'
             ELSE 'result' END AS artifact_kind
    FROM generate_series(1, 8) AS ordinal
)
INSERT INTO hwpx_agent.artifacts (
    tenant_id, artifact_id, content_sha256, size_bytes, media_type, artifact_kind,
    storage_state, encryption_key_ref, verified_at, service_metadata_version, filename,
    object_key, encryption_algorithm, encryption_nonce, aad_sha256, ciphertext_sha256,
    validation_state, scanner_engine_ref, scanner_signature_version,
    authorization_generation
)
SELECT
    'e1000000-0000-0000-0000-000000000001', artifact_id, content_sha256,
    ordinal, 'application/octet-stream', artifact_kind, 'available',
    'kms.cleanup-test', transaction_timestamp(), 1, concat('artifact-', ordinal, '.bin'),
    concat('artifacts/v1/e1000000000000000000000000000001/', artifact_kind,
           '/available/', content_sha256, '.aes256gcm'),
    'AES-256-GCM', decode(lpad(to_hex(ordinal), 24, '0'), 'hex'),
    lpad(to_hex(ordinal + 5100), 64, '0'), lpad(to_hex(ordinal + 5200), 64, '0'),
    'verified', 'scanner.cleanup-test', 'v1', 1
FROM artifact_seed;
INSERT INTO hwpx_agent.artifact_acl (
    tenant_id, artifact_id, subject_sha256, can_read, can_manage
)
SELECT tenant_id, artifact_id, repeat('a', 64), true, true
FROM hwpx_agent.artifacts
WHERE tenant_id = 'e1000000-0000-0000-0000-000000000001';

SELECT set_config('hwpx_agent.tenant_id', 'e1000000-0000-0000-0000-000000000001', true);
SELECT set_config('hwpx_agent.subject_sha256', repeat('a', 64), true);

DO $$
DECLARE
    v_assertions integer := 0;
    v_i integer;
    v_source_sha character(64);
    v_state text;
    v_job_state text;
    v_task_id uuid;
    v_claimed_task uuid;
    v_target_kind text;
    v_artifact_id uuid;
    v_attempt integer;
    v_fence bigint;
    v_expiry timestamptz;
    v_error text;
BEGIN
    SELECT content_sha256 INTO v_source_sha FROM hwpx_agent.artifacts
    WHERE tenant_id = 'e1000000-0000-0000-0000-000000000001'
      AND artifact_id = 'e4000000-0000-0000-0000-000000000001';

    -- 01: schema, forced RLS, and no PUBLIC mutation surface are exact.
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 8 AND migration_name = 'p14.cancel_cleanup_v1'
    ) OR (SELECT count(*) FROM pg_class AS relation
          JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
          WHERE namespace.nspname = 'hwpx_agent'
            AND relation.relname IN ('job_cancellation_requests', 'job_effect_markers', 'cleanup_tasks')
            AND relation.relrowsecurity AND relation.relforcerowsecurity) <> 3
       OR has_function_privilege(
            'public',
            'hwpx_agent.complete_cleanup_task_v1(uuid,character,uuid,uuid,uuid,integer,bigint,text,character,character)',
            'EXECUTE'
       ) THEN RAISE EXCEPTION 'assertion 01 failed'; END IF;
    v_assertions := v_assertions + 1;

    PERFORM * FROM hwpx_agent.register_scheduler_worker(
        'e1000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e9000000-0000-0000-0000-000000000001',
        'hancom-hangul-2020-current-pc', repeat('c', 64),
        'ready', 300, repeat('1', 64)
    );
    FOR v_i IN 1..4 LOOP
        PERFORM * FROM hwpx_agent.claim_idempotent_job_v2(
            'e1000000-0000-0000-0000-000000000001',
            'e2000000-0000-0000-0000-000000000001',
            'e3000000-0000-0000-0000-000000000001', repeat('a', 64),
            format('e7000000-0000-0000-0000-%s', lpad(v_i::text, 12, '0'))::uuid,
            format('e8000000-0000-0000-0000-%s', lpad(v_i::text, 12, '0'))::uuid,
            format('e8100000-0000-0000-0000-%s', lpad(v_i::text, 12, '0'))::uuid,
            'e4000000-0000-0000-0000-000000000001', NULL, 0,
            lpad(to_hex(6000 + v_i), 64, '0'), lpad(to_hex(6100 + v_i), 64, '0'),
            v_source_sha, lpad(to_hex(6200 + v_i), 64, '0'),
            lpad(to_hex(6300 + v_i), 64, '0'), lpad(to_hex(6400 + v_i), 64, '0'),
            'hancom-hangul-2020-current-pc', repeat('c', 64),
            3, 1, 4, 600, lpad(to_hex(6500 + v_i), 64, '0')
        );
    END LOOP;
    FOR v_i IN 2..4 LOOP
        PERFORM * FROM hwpx_agent.lease_idempotent_job_v2(
            'e1000000-0000-0000-0000-000000000001',
            'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
            format('e7000000-0000-0000-0000-%s', lpad(v_i::text, 12, '0'))::uuid,
            format('e8000000-0000-0000-0000-%s', lpad(v_i::text, 12, '0'))::uuid,
            'e9000000-0000-0000-0000-000000000001',
            format('ea000000-0000-0000-0000-%s', lpad(v_i::text, 12, '0'))::uuid,
            120, lpad(to_hex(6600 + v_i), 64, '0')
        );
    END LOOP;
    v_assertions := v_assertions + 1;

    -- 03: queued cancellation is immediate, receipt-backed, and exact replay only.
    SELECT returned_state, returned_job_state INTO v_state, v_job_state
    FROM hwpx_agent.request_job_cancellation_v1(
        'e1000000-0000-0000-0000-000000000001',
        'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e7000000-0000-0000-0000-000000000001',
        'e8000000-0000-0000-0000-000000000001',
        'eb000000-0000-0000-0000-000000000001',
        'e4000000-0000-0000-0000-000000000002', repeat('2', 64)
    );
    IF v_state <> 'cancelled' OR v_job_state <> 'cancelled' OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.idempotency_records
        WHERE tenant_id = 'e1000000-0000-0000-0000-000000000001'
          AND idempotency_key = 'e7000000-0000-0000-0000-000000000001'
          AND state = 'terminal_failure' AND attempt_count = 0
          AND terminal_error_code = 'JOB_CANCELLED'
    ) THEN RAISE EXCEPTION 'assertion 03 failed'; END IF;
    v_assertions := v_assertions + 1;
    PERFORM * FROM hwpx_agent.request_job_cancellation_v1(
        'e1000000-0000-0000-0000-000000000001',
        'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e7000000-0000-0000-0000-000000000001',
        'e8000000-0000-0000-0000-000000000001',
        'eb000000-0000-0000-0000-000000000001',
        'e4000000-0000-0000-0000-000000000002', repeat('3', 64)
    );
    BEGIN
        PERFORM * FROM hwpx_agent.request_job_cancellation_v1(
            'e1000000-0000-0000-0000-000000000001',
            'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'e7000000-0000-0000-0000-000000000001',
            'e8000000-0000-0000-0000-000000000001',
            'eb000000-0000-0000-0000-000000000099',
            'e4000000-0000-0000-0000-000000000002', repeat('3', 64)
        );
        RAISE EXCEPTION 'assertion 04 unexpectedly succeeded';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'CANCELLATION_IDENTITY_CONFLICT' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 05: a prepared active attempt cancels at a safe point and queues only its workspace.
    PERFORM * FROM hwpx_agent.request_job_cancellation_v1(
        'e1000000-0000-0000-0000-000000000001',
        'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e7000000-0000-0000-0000-000000000002',
        'e8000000-0000-0000-0000-000000000002',
        'eb000000-0000-0000-0000-000000000002',
        'e4000000-0000-0000-0000-000000000003', repeat('4', 64)
    );
    SELECT returned_state, returned_cleanup_task_id INTO v_state, v_task_id
    FROM hwpx_agent.finalize_job_cancellation_v1(
        'e1000000-0000-0000-0000-000000000001',
        'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e7000000-0000-0000-0000-000000000002',
        'e8000000-0000-0000-0000-000000000002',
        'e9000000-0000-0000-0000-000000000001',
        'ea000000-0000-0000-0000-000000000002', 1, 1,
        'ec000000-0000-0000-0000-000000000001',
        'ed000000-0000-0000-0000-000000000001', repeat('5', 64)
    );
    IF v_state <> 'cancelled'
       OR v_task_id <> 'ec000000-0000-0000-0000-000000000001'::uuid
       OR NOT EXISTS (
            SELECT 1 FROM hwpx_agent.job_attempts
            WHERE tenant_id = 'e1000000-0000-0000-0000-000000000001'
              AND job_id = 'e8000000-0000-0000-0000-000000000002'
              AND state = 'cancelled'
       ) THEN RAISE EXCEPTION 'assertion 05 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 06: started effect becomes unknown-outcome, never a false cancellation success.
    PERFORM hwpx_agent.mark_job_effect_phase_v1(
        'e1000000-0000-0000-0000-000000000001',
        'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e8000000-0000-0000-0000-000000000003',
        'e9000000-0000-0000-0000-000000000001',
        'ea000000-0000-0000-0000-000000000003', 1, 1, 'started', repeat('6', 64)
    );
    PERFORM * FROM hwpx_agent.request_job_cancellation_v1(
        'e1000000-0000-0000-0000-000000000001',
        'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e7000000-0000-0000-0000-000000000003',
        'e8000000-0000-0000-0000-000000000003',
        'eb000000-0000-0000-0000-000000000003',
        'e4000000-0000-0000-0000-000000000004', repeat('7', 64)
    );
    SELECT returned_state INTO v_state
    FROM hwpx_agent.finalize_job_cancellation_v1(
        'e1000000-0000-0000-0000-000000000001',
        'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e7000000-0000-0000-0000-000000000003',
        'e8000000-0000-0000-0000-000000000003',
        'e9000000-0000-0000-0000-000000000001',
        'ea000000-0000-0000-0000-000000000003', 1, 1,
        'ec000000-0000-0000-0000-000000000002',
        'ed000000-0000-0000-0000-000000000002', repeat('8', 64)
    );
    IF v_state <> 'outcome_unknown' OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.jobs
        WHERE tenant_id = 'e1000000-0000-0000-0000-000000000001'
          AND job_id = 'e8000000-0000-0000-0000-000000000003'
          AND state = 'unknown_outcome' AND terminal_error_code = 'OUTCOME_UNKNOWN'
          AND completed_at IS NULL
    ) THEN RAISE EXCEPTION 'assertion 06 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 07: a committed effect is too late; no cleanup task is created and normal flow unblocks.
    PERFORM hwpx_agent.mark_job_effect_phase_v1(
        'e1000000-0000-0000-0000-000000000001',
        'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e8000000-0000-0000-0000-000000000004',
        'e9000000-0000-0000-0000-000000000001',
        'ea000000-0000-0000-0000-000000000004', 1, 1, 'started', repeat('9', 64)
    );
    PERFORM hwpx_agent.mark_job_effect_phase_v1(
        'e1000000-0000-0000-0000-000000000001',
        'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e8000000-0000-0000-0000-000000000004',
        'e9000000-0000-0000-0000-000000000001',
        'ea000000-0000-0000-0000-000000000004', 1, 1, 'committed', repeat('a', 64)
    );
    PERFORM * FROM hwpx_agent.request_job_cancellation_v1(
        'e1000000-0000-0000-0000-000000000001',
        'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e7000000-0000-0000-0000-000000000004',
        'e8000000-0000-0000-0000-000000000004',
        'eb000000-0000-0000-0000-000000000004',
        'e4000000-0000-0000-0000-000000000005', repeat('b', 64)
    );
    SELECT returned_state, returned_cleanup_task_id INTO v_state, v_task_id
    FROM hwpx_agent.finalize_job_cancellation_v1(
        'e1000000-0000-0000-0000-000000000001',
        'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e7000000-0000-0000-0000-000000000004',
        'e8000000-0000-0000-0000-000000000004',
        'e9000000-0000-0000-0000-000000000001',
        'ea000000-0000-0000-0000-000000000004', 1, 1,
        'ec000000-0000-0000-0000-000000000003',
        'ed000000-0000-0000-0000-000000000003', repeat('c', 64)
    );
    IF v_state <> 'too_late' OR v_task_id IS NOT NULL OR EXISTS (
        SELECT 1 FROM hwpx_agent.cleanup_tasks
        WHERE tenant_id = 'e1000000-0000-0000-0000-000000000001'
          AND cleanup_task_id = 'ec000000-0000-0000-0000-000000000003'
    ) THEN RAISE EXCEPTION 'assertion 07 failed'; END IF;
    PERFORM * FROM hwpx_agent.advance_idempotent_job_v2(
        'e1000000-0000-0000-0000-000000000001',
        'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e7000000-0000-0000-0000-000000000004',
        'e8000000-0000-0000-0000-000000000004',
        'e9000000-0000-0000-0000-000000000001',
        'ea000000-0000-0000-0000-000000000004', 1, 1,
        'leased', 'staged', repeat('d', 64)
    );
    v_assertions := v_assertions + 1;

    -- 08: source and any artifact referenced by durable metadata are not cleanup candidates.
    BEGIN
        PERFORM hwpx_agent.queue_orphan_cleanup_v1(
            'e1000000-0000-0000-0000-000000000001',
            'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'e8000000-0000-0000-0000-000000000001',
            'ec000000-0000-0000-0000-000000000010',
            'e4000000-0000-0000-0000-000000000001', repeat('e', 64)
        );
        RAISE EXCEPTION 'assertion 08 source unexpectedly queued';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'CLEANUP_SOURCE_PROTECTED' THEN RAISE; END IF;
    END;
    BEGIN
        PERFORM hwpx_agent.queue_orphan_cleanup_v1(
            'e1000000-0000-0000-0000-000000000001',
            'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
            'e8000000-0000-0000-0000-000000000001',
            'ec000000-0000-0000-0000-000000000011',
            'e4000000-0000-0000-0000-000000000002', repeat('f', 64)
        );
        RAISE EXCEPTION 'assertion 08 referenced unexpectedly queued';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'CLEANUP_TARGET_REFERENCED' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 09: an unreferenced result queues with its database-derived digest and kind.
    PERFORM hwpx_agent.queue_orphan_cleanup_v1(
        'e1000000-0000-0000-0000-000000000001',
        'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e8000000-0000-0000-0000-000000000001',
        'ec000000-0000-0000-0000-000000000004',
        'e4000000-0000-0000-0000-000000000007', repeat('0', 64)
    );
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.cleanup_tasks AS task
        JOIN hwpx_agent.artifacts AS artifact
          ON artifact.tenant_id = task.tenant_id AND artifact.artifact_id = task.artifact_id
        WHERE task.tenant_id = 'e1000000-0000-0000-0000-000000000001'
          AND task.cleanup_task_id = 'ec000000-0000-0000-0000-000000000004'
          AND task.artifact_content_sha256 = artifact.content_sha256
          AND task.artifact_kind = artifact.artifact_kind AND task.state = 'pending'
    ) THEN RAISE EXCEPTION 'assertion 09 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 10-12: before-effect crash expires, reclaims with a new fence, and rejects the stale lease.
    SELECT returned_cleanup_task_id, returned_target_kind, returned_attempt_count,
           returned_fencing_token, returned_lease_expires_at
    INTO v_claimed_task, v_target_kind, v_attempt, v_fence, v_expiry
    FROM hwpx_agent.claim_cleanup_task_v1(
        'e1000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e9000000-0000-0000-0000-000000000001',
        'ee000000-0000-0000-0000-000000000001', 1, repeat('1', 64)
    );
    IF v_claimed_task <> 'ec000000-0000-0000-0000-000000000001'::uuid
       OR v_target_kind <> 'workspace' OR v_attempt <> 1 OR v_fence <> 1 THEN
        RAISE EXCEPTION 'assertion 10 failed';
    END IF;
    v_assertions := v_assertions + 1;
    PERFORM pg_sleep(1.1);
    SELECT returned_cleanup_task_id, returned_attempt_count, returned_fencing_token
    INTO v_claimed_task, v_attempt, v_fence
    FROM hwpx_agent.claim_cleanup_task_v1(
        'e1000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e9000000-0000-0000-0000-000000000001',
        'ee000000-0000-0000-0000-000000000002', 30, repeat('2', 64)
    );
    IF v_claimed_task <> 'ec000000-0000-0000-0000-000000000001'::uuid
       OR v_attempt <> 2 OR v_fence <> 2 THEN RAISE EXCEPTION 'assertion 11 failed'; END IF;
    v_assertions := v_assertions + 1;
    BEGIN
        PERFORM * FROM hwpx_agent.complete_cleanup_task_v1(
            'e1000000-0000-0000-0000-000000000001', repeat('a', 64),
            'ec000000-0000-0000-0000-000000000001',
            'e9000000-0000-0000-0000-000000000001',
            'ee000000-0000-0000-0000-000000000001', 1, 1,
            'workspace_removed', repeat('3', 64), repeat('4', 64)
        );
        RAISE EXCEPTION 'assertion 12 stale lease unexpectedly succeeded';
    EXCEPTION WHEN serialization_failure THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'CLEANUP_LEASE_MISMATCH' THEN RAISE; END IF;
    END;
    PERFORM * FROM hwpx_agent.complete_cleanup_task_v1(
        'e1000000-0000-0000-0000-000000000001', repeat('a', 64),
        'ec000000-0000-0000-0000-000000000001',
        'e9000000-0000-0000-0000-000000000001',
        'ee000000-0000-0000-0000-000000000002', 2, 2,
        'workspace_already_absent', repeat('5', 64), repeat('6', 64)
    );
    v_assertions := v_assertions + 1;

    -- 13: the started-effect workspace is cleaned independently.
    SELECT returned_cleanup_task_id, returned_attempt_count, returned_fencing_token
    INTO v_claimed_task, v_attempt, v_fence
    FROM hwpx_agent.claim_cleanup_task_v1(
        'e1000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e9000000-0000-0000-0000-000000000001',
        'ee000000-0000-0000-0000-000000000003', 30, repeat('7', 64)
    );
    PERFORM * FROM hwpx_agent.complete_cleanup_task_v1(
        'e1000000-0000-0000-0000-000000000001', repeat('a', 64),
        v_claimed_task, 'e9000000-0000-0000-0000-000000000001',
        'ee000000-0000-0000-0000-000000000003', v_attempt, v_fence,
        'workspace_removed', repeat('8', 64), repeat('9', 64)
    );
    IF v_claimed_task <> 'ec000000-0000-0000-0000-000000000002'::uuid THEN
        RAISE EXCEPTION 'assertion 13 failed';
    END IF;
    v_assertions := v_assertions + 1;

    -- 14-15: after-effect crash leaves a purging reservation; retry records already-quarantined.
    SELECT returned_cleanup_task_id, returned_artifact_id,
           returned_attempt_count, returned_fencing_token
    INTO v_claimed_task, v_artifact_id, v_attempt, v_fence
    FROM hwpx_agent.claim_cleanup_task_v1(
        'e1000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e9000000-0000-0000-0000-000000000001',
        'ee000000-0000-0000-0000-000000000004', 1, repeat('a', 64)
    );
    IF v_claimed_task <> 'ec000000-0000-0000-0000-000000000004'::uuid
       OR v_artifact_id <> 'e4000000-0000-0000-0000-000000000007'::uuid
       OR NOT EXISTS (
            SELECT 1 FROM hwpx_agent.artifacts
            WHERE tenant_id = 'e1000000-0000-0000-0000-000000000001'
              AND artifact_id = v_artifact_id AND storage_state = 'purging'
       ) THEN RAISE EXCEPTION 'assertion 14 failed'; END IF;
    v_assertions := v_assertions + 1;
    PERFORM pg_sleep(1.1);
    SELECT returned_cleanup_task_id, returned_attempt_count, returned_fencing_token
    INTO v_claimed_task, v_attempt, v_fence
    FROM hwpx_agent.claim_cleanup_task_v1(
        'e1000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e9000000-0000-0000-0000-000000000001',
        'ee000000-0000-0000-0000-000000000005', 30, repeat('b', 64)
    );
    PERFORM * FROM hwpx_agent.complete_cleanup_task_v1(
        'e1000000-0000-0000-0000-000000000001', repeat('a', 64),
        v_claimed_task, 'e9000000-0000-0000-0000-000000000001',
        'ee000000-0000-0000-0000-000000000005', v_attempt, v_fence,
        'artifact_already_quarantined', repeat('c', 64), repeat('d', 64)
    );
    IF v_attempt <> 2 OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.artifacts
        WHERE tenant_id = 'e1000000-0000-0000-0000-000000000001'
          AND artifact_id = 'e4000000-0000-0000-0000-000000000007'
          AND storage_state = 'quarantined' AND validation_state = 'quarantined'
          AND quarantine_reason_code = 'ORPHAN_CLEANUP'
    ) THEN RAISE EXCEPTION 'assertion 15 failed'; END IF;
    v_assertions := v_assertions + 1;

    -- 16: receipt replay is exact and a conflicting proof is rejected.
    PERFORM * FROM hwpx_agent.complete_cleanup_task_v1(
        'e1000000-0000-0000-0000-000000000001', repeat('a', 64),
        'ec000000-0000-0000-0000-000000000004',
        'e9000000-0000-0000-0000-000000000001',
        'ee000000-0000-0000-0000-000000000005', 2, 2,
        'artifact_already_quarantined', repeat('c', 64), repeat('e', 64)
    );
    BEGIN
        PERFORM * FROM hwpx_agent.complete_cleanup_task_v1(
            'e1000000-0000-0000-0000-000000000001', repeat('a', 64),
            'ec000000-0000-0000-0000-000000000004',
            'e9000000-0000-0000-0000-000000000001',
            'ee000000-0000-0000-0000-000000000005', 2, 2,
            'artifact_already_quarantined', repeat('f', 64), repeat('e', 64)
        );
        RAISE EXCEPTION 'assertion 16 conflicting proof unexpectedly succeeded';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'CLEANUP_RECEIPT_CONFLICT' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 17: a reference created after queueing is caught before any cleanup lease is issued.
    PERFORM hwpx_agent.queue_orphan_cleanup_v1(
        'e1000000-0000-0000-0000-000000000001',
        'e2000000-0000-0000-0000-000000000001', repeat('a', 64),
        'e8000000-0000-0000-0000-000000000001',
        'ec000000-0000-0000-0000-000000000005',
        'e4000000-0000-0000-0000-000000000008', repeat('1', 64)
    );
    INSERT INTO hwpx_agent.revisions (
        tenant_id, project_id, revision_id, source_artifact_id, result_artifact_id,
        operation_plan_sha256, validation_state, validation_summary_sha256,
        created_by_subject_sha256
    ) VALUES (
        'e1000000-0000-0000-0000-000000000001',
        'e2000000-0000-0000-0000-000000000001',
        'ef000000-0000-0000-0000-000000000001',
        'e4000000-0000-0000-0000-000000000001',
        'e4000000-0000-0000-0000-000000000008',
        repeat('1', 64), 'verified', repeat('2', 64), repeat('a', 64)
    );
    BEGIN
        PERFORM * FROM hwpx_agent.claim_cleanup_task_v1(
            'e1000000-0000-0000-0000-000000000001', repeat('a', 64),
            'e9000000-0000-0000-0000-000000000001',
            'ee000000-0000-0000-0000-000000000006', 30, repeat('3', 64)
        );
        RAISE EXCEPTION 'assertion 17 reference race unexpectedly leased';
    EXCEPTION WHEN no_data_found THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
        IF v_error <> 'CLEANUP_TASK_NOT_FOUND' THEN RAISE; END IF;
    END;
    v_assertions := v_assertions + 1;

    -- 18: records hold opaque identifiers only; no file-system path column exists.
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'hwpx_agent' AND table_name IN (
            'job_cancellation_requests', 'job_effect_markers', 'cleanup_tasks'
        ) AND column_name ~ '(path|filename|object_key)'
    ) THEN RAISE EXCEPTION 'assertion 18 failed'; END IF;
    v_assertions := v_assertions + 1;

    IF v_assertions <> 18 THEN RAISE EXCEPTION 'assertion count mismatch'; END IF;
    RAISE NOTICE 'P14_CANCEL_CLEANUP_SMOKE_PASS assertions=%', v_assertions;
END
$$;

SET CONSTRAINTS ALL IMMEDIATE;
SELECT 'P14_CANCEL_CLEANUP_SMOKE_PASS assertions=18';
ROLLBACK;
