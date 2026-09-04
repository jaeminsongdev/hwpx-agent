SET client_min_messages = warning;

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hwpx_agent_test_app') THEN
        CREATE ROLE hwpx_agent_test_app NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
    END IF;
END
$$;

GRANT USAGE ON SCHEMA hwpx_agent TO hwpx_agent_test_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA hwpx_agent TO hwpx_agent_test_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA hwpx_agent TO hwpx_agent_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id() TO hwpx_agent_test_app;
REVOKE ALL ON TABLE hwpx_agent.schema_versions FROM hwpx_agent_test_app;

INSERT INTO hwpx_agent.tenants (tenant_id, slug)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'tenant-one'),
    ('00000000-0000-0000-0000-000000000002', 'tenant-two');

INSERT INTO hwpx_agent.projects (
    tenant_id, project_id, slug, display_name, target_profile_id, retention_policy_id
)
VALUES
    (
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000101',
        'project-one', 'Project One', 'hancom-hangul-2020', 'retention.standard'
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000102',
        'project-two', 'Project Two', 'hancom-hangul-2020', 'retention.standard'
    ),
    (
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000103',
        'project-three', 'Project Three', 'hancom-hangul-2020', 'retention.standard'
    );

INSERT INTO hwpx_agent.artifacts (
    tenant_id, artifact_id, content_sha256, size_bytes, media_type,
    artifact_kind, encryption_key_ref
)
VALUES
    (
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000201', repeat('1', 64), 128,
        'application/hwpx+zip', 'source', 'kms.tenant_one'
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000202', repeat('2', 64), 256,
        'application/hwpx+zip', 'result', 'kms.tenant_one'
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000203', repeat('3', 64), 64,
        'application/json', 'receipt', 'kms.tenant_one'
    ),
    (
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000204', repeat('4', 64), 128,
        'application/hwpx+zip', 'source', 'kms.tenant_two'
    ),
    (
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000205', repeat('5', 64), 256,
        'application/hwpx+zip', 'result', 'kms.tenant_two'
    );

INSERT INTO hwpx_agent.revisions (
    tenant_id, project_id, revision_id, source_artifact_id, result_artifact_id,
    operation_plan_sha256, validation_state, validation_summary_sha256,
    created_by_subject_sha256
)
VALUES
    (
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000101',
        '00000000-0000-0000-0000-000000000301',
        '00000000-0000-0000-0000-000000000201',
        '00000000-0000-0000-0000-000000000202',
        repeat('6', 64), 'verified', repeat('7', 64), repeat('8', 64)
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000102',
        '00000000-0000-0000-0000-000000000302',
        '00000000-0000-0000-0000-000000000201',
        '00000000-0000-0000-0000-000000000202',
        repeat('9', 64), 'verified', repeat('a', 64), repeat('b', 64)
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000101',
        '00000000-0000-0000-0000-000000000304',
        '00000000-0000-0000-0000-000000000201',
        '00000000-0000-0000-0000-000000000202',
        repeat('3', 64), 'verified', repeat('4', 64), repeat('8', 64)
    ),
    (
        '00000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000103',
        '00000000-0000-0000-0000-000000000303',
        '00000000-0000-0000-0000-000000000204',
        '00000000-0000-0000-0000-000000000205',
        repeat('c', 64), 'verified', repeat('d', 64), repeat('e', 64)
    );

INSERT INTO hwpx_agent.revision_parents (
    tenant_id, project_id, revision_id, parent_revision_id, parent_ordinal
)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000101',
    '00000000-0000-0000-0000-000000000304',
    '00000000-0000-0000-0000-000000000301', 0
);

INSERT INTO hwpx_agent.checkpoints (
    tenant_id, project_id, checkpoint_id, revision_id, label,
    created_by_subject_sha256
)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000101',
    '00000000-0000-0000-0000-000000001001',
    '00000000-0000-0000-0000-000000000304', 'before-layout-change', repeat('8', 64)
);

INSERT INTO hwpx_agent.branches (
    tenant_id, project_id, branch_id, name, head_revision_id, is_default,
    created_by_subject_sha256
)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000101',
    '00000000-0000-0000-0000-000000000401',
    'main', '00000000-0000-0000-0000-000000000301', true, repeat('8', 64)
);

INSERT INTO hwpx_agent.project_acl (
    tenant_id, project_id, subject_sha256, role
)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000101', repeat('8', 64), 'owner'
);

INSERT INTO hwpx_agent.jobs (
    tenant_id, project_id, job_id, request_id, input_artifact_id,
    operation_plan_sha256, required_target_profile_id,
    required_capability_set_sha256, state, attempt_count,
    lease_owner_agent_id, fencing_token, lease_expires_at
)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000101',
    '00000000-0000-0000-0000-000000000501',
    '00000000-0000-0000-0000-000000000601',
    '00000000-0000-0000-0000-000000000201', repeat('6', 64),
    'hancom-hangul-2020', repeat('f', 64), 'leased', 1,
    '00000000-0000-0000-0000-000000000701', 1,
    transaction_timestamp() + interval '5 minutes'
);

INSERT INTO hwpx_agent.job_attempts (
    tenant_id, project_id, job_id, attempt_no, execution_id,
    agent_instance_id, fencing_token, state
)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000101',
    '00000000-0000-0000-0000-000000000501', 1,
    '00000000-0000-0000-0000-000000000801',
    '00000000-0000-0000-0000-000000000701', 1, 'running'
);

INSERT INTO hwpx_agent.idempotency_records (
    tenant_id, project_id, idempotency_key, request_sha256, state, job_id, expires_at
)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000101',
    '00000000-0000-0000-0000-000000000901', repeat('0', 64), 'claimed',
    '00000000-0000-0000-0000-000000000501',
    transaction_timestamp() + interval '1 day'
);

INSERT INTO hwpx_agent.audit_events (
    tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000101', 'job.created', repeat('8', 64),
    '00000000-0000-0000-0000-000000000501', repeat('1', 64)
);

SET ROLE hwpx_agent_test_app;
SELECT set_config('hwpx_agent.tenant_id', '00000000-0000-0000-0000-000000000001', false);
SET CONSTRAINTS ALL IMMEDIATE;

DO $$
BEGIN
    IF (SELECT count(*) FROM hwpx_agent.projects) <> 2 THEN
        RAISE EXCEPTION 'tenant A project visibility mismatch';
    END IF;
END
$$;

DO $$
BEGIN
    PERFORM 1 FROM hwpx_agent.projects
    WHERE tenant_id = '00000000-0000-0000-0000-000000000002';
    IF FOUND THEN RAISE EXCEPTION 'cross-tenant project became visible'; END IF;
END
$$;

DO $$
BEGIN
    BEGIN
        INSERT INTO hwpx_agent.projects (
            tenant_id, project_id, slug, display_name, target_profile_id, retention_policy_id
        ) VALUES (
            '00000000-0000-0000-0000-000000000002',
            '00000000-0000-0000-0000-000000000104',
            'denied-project', 'Denied', 'hancom-hangul-2020', 'retention.standard'
        );
        RAISE EXCEPTION 'cross-tenant insert unexpectedly succeeded';
    EXCEPTION WHEN insufficient_privilege THEN NULL;
    END;
END
$$;

DO $$
BEGIN
    BEGIN
        UPDATE hwpx_agent.revisions SET validation_state = 'failed'
        WHERE revision_id = '00000000-0000-0000-0000-000000000301';
        RAISE EXCEPTION 'immutable revision update unexpectedly succeeded';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL;
    END;
END
$$;

DO $$
BEGIN
    BEGIN
        UPDATE hwpx_agent.revisions SET created_at = created_at
        WHERE revision_id = '00000000-0000-0000-0000-000000000301';
        RAISE EXCEPTION 'immutable revision no-op update unexpectedly succeeded';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL;
    END;
END
$$;

DO $$
BEGIN
    BEGIN
        UPDATE hwpx_agent.artifacts SET content_sha256 = repeat('a', 64)
        WHERE artifact_id = '00000000-0000-0000-0000-000000000201';
        RAISE EXCEPTION 'artifact identity update unexpectedly succeeded';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL;
    END;
END
$$;

UPDATE hwpx_agent.artifacts SET storage_state = 'available', verified_at = transaction_timestamp()
WHERE artifact_id = '00000000-0000-0000-0000-000000000201';

DO $$
BEGIN
    IF (SELECT storage_state FROM hwpx_agent.artifacts
        WHERE artifact_id = '00000000-0000-0000-0000-000000000201') <> 'available' THEN
        RAISE EXCEPTION 'artifact mutable lifecycle fields did not update';
    END IF;
END
$$;

DO $$
BEGIN
    BEGIN
        UPDATE hwpx_agent.idempotency_records SET request_sha256 = repeat('f', 64)
        WHERE idempotency_key = '00000000-0000-0000-0000-000000000901';
        RAISE EXCEPTION 'idempotency identity update unexpectedly succeeded';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL;
    END;
END
$$;

DO $$
BEGIN
    BEGIN
        UPDATE hwpx_agent.projects
        SET head_revision_id = '00000000-0000-0000-0000-000000000302'
        WHERE project_id = '00000000-0000-0000-0000-000000000101';
        RAISE EXCEPTION 'cross-project head update unexpectedly succeeded';
    EXCEPTION WHEN foreign_key_violation THEN NULL;
    END;
END
$$;

DO $$
BEGIN
    BEGIN
        INSERT INTO hwpx_agent.branches (
            tenant_id, project_id, branch_id, name, is_default, created_by_subject_sha256
        ) VALUES (
            '00000000-0000-0000-0000-000000000001',
            '00000000-0000-0000-0000-000000000101',
            '00000000-0000-0000-0000-000000000402', 'duplicate-default', true,
            repeat('8', 64)
        );
        RAISE EXCEPTION 'second default branch unexpectedly succeeded';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;
END
$$;

DO $$
BEGIN
    BEGIN
        INSERT INTO hwpx_agent.jobs (
            tenant_id, project_id, job_id, request_id, input_artifact_id,
            operation_plan_sha256, required_target_profile_id,
            required_capability_set_sha256, state, attempt_count
        ) VALUES (
            '00000000-0000-0000-0000-000000000001',
            '00000000-0000-0000-0000-000000000101',
            '00000000-0000-0000-0000-000000000502',
            '00000000-0000-0000-0000-000000000602',
            '00000000-0000-0000-0000-000000000201', repeat('1', 64),
            'hancom-hangul-2020', repeat('2', 64), 'executing', 1
        );
        RAISE EXCEPTION 'invalid active lease unexpectedly succeeded';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
END
$$;

DO $$
BEGIN
    BEGIN
        UPDATE hwpx_agent.jobs SET operation_plan_sha256 = repeat('3', 64)
        WHERE job_id = '00000000-0000-0000-0000-000000000501';
        RAISE EXCEPTION 'job identity update unexpectedly succeeded';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL;
    END;
END
$$;

UPDATE hwpx_agent.job_attempts
SET state = 'succeeded', completed_at = transaction_timestamp(),
    receipt_artifact_id = '00000000-0000-0000-0000-000000000203'
WHERE job_id = '00000000-0000-0000-0000-000000000501' AND attempt_no = 1;

DO $$
BEGIN
    IF (SELECT state FROM hwpx_agent.job_attempts
        WHERE job_id = '00000000-0000-0000-0000-000000000501' AND attempt_no = 1)
        <> 'succeeded' THEN
        RAISE EXCEPTION 'job attempt terminal transition did not persist';
    END IF;
END
$$;

DO $$
BEGIN
    BEGIN
        UPDATE hwpx_agent.job_attempts SET fencing_token = 2
        WHERE job_id = '00000000-0000-0000-0000-000000000501' AND attempt_no = 1;
        RAISE EXCEPTION 'job attempt identity update unexpectedly succeeded';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL;
    END;
END
$$;

UPDATE hwpx_agent.jobs
SET state = 'succeeded', result_revision_id = '00000000-0000-0000-0000-000000000301',
    completed_at = transaction_timestamp(), lease_owner_agent_id = NULL, lease_expires_at = NULL
WHERE job_id = '00000000-0000-0000-0000-000000000501';

DO $$
BEGIN
    IF (SELECT state FROM hwpx_agent.jobs
        WHERE job_id = '00000000-0000-0000-0000-000000000501') <> 'succeeded' THEN
        RAISE EXCEPTION 'job terminal transition did not persist';
    END IF;
END
$$;

UPDATE hwpx_agent.idempotency_records
SET state = 'terminal_success',
    result_revision_id = '00000000-0000-0000-0000-000000000301',
    receipt_artifact_id = '00000000-0000-0000-0000-000000000203'
WHERE idempotency_key = '00000000-0000-0000-0000-000000000901';

DO $$
BEGIN
    IF (SELECT state FROM hwpx_agent.idempotency_records
        WHERE idempotency_key = '00000000-0000-0000-0000-000000000901')
        <> 'terminal_success' THEN
        RAISE EXCEPTION 'idempotency terminal transition did not persist';
    END IF;
END
$$;

DO $$
BEGIN
    BEGIN
        UPDATE hwpx_agent.audit_events SET event_type = 'job.changed';
        RAISE EXCEPTION 'audit event update unexpectedly succeeded';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL;
    END;
END
$$;

DO $$
BEGIN
    BEGIN
        DELETE FROM hwpx_agent.checkpoints
        WHERE checkpoint_id = '00000000-0000-0000-0000-000000001001';
        RAISE EXCEPTION 'checkpoint delete unexpectedly succeeded';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL;
    END;
END
$$;

DO $$
BEGIN
    IF hwpx_agent.current_tenant_id() <> '00000000-0000-0000-0000-000000000001'::uuid THEN
        RAISE EXCEPTION 'tenant context function mismatch';
    END IF;
END
$$;

RESET ROLE;

COMMIT;

SELECT 'P14_METADATA_SMOKE_PASS assertions=19';
