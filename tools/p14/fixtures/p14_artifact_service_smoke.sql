SET client_min_messages = warning;

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hwpx_agent_artifact_test_app') THEN
        CREATE ROLE hwpx_agent_artifact_test_app
            NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
    END IF;
END
$$;

GRANT USAGE ON SCHEMA hwpx_agent TO hwpx_agent_artifact_test_app;
GRANT SELECT, INSERT, UPDATE, DELETE
    ON hwpx_agent.artifacts, hwpx_agent.artifact_acl
    TO hwpx_agent_artifact_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id()
    TO hwpx_agent_artifact_test_app;
REVOKE ALL ON TABLE hwpx_agent.schema_versions FROM hwpx_agent_artifact_test_app;

INSERT INTO hwpx_agent.tenants (tenant_id, slug)
VALUES
    ('10000000-0000-0000-0000-000000000001', 'artifact-tenant-one'),
    ('20000000-0000-0000-0000-000000000002', 'artifact-tenant-two');

INSERT INTO hwpx_agent.artifacts (
    tenant_id, artifact_id, content_sha256, size_bytes, media_type, artifact_kind,
    storage_state, encryption_key_ref, service_metadata_version, filename, object_key,
    encryption_algorithm, encryption_nonce, aad_sha256, ciphertext_sha256,
    validation_state, scanner_engine_ref, scanner_signature_version,
    authorization_generation
)
VALUES
    (
        '10000000-0000-0000-0000-000000000001',
        '10000000-0000-0000-0000-000000000101', repeat('1', 64), 128,
        'application/hwpx+zip', 'source', 'available', 'kms.artifact-v1', 1,
        'fixture.hwpx',
        'artifacts/v1/10000000000000000000000000000001/source/available/'
            || repeat('1', 64) || '.aes256gcm',
        'AES-256-GCM', decode(repeat('ab', 12), 'hex'), repeat('2', 64), repeat('3', 64),
        'verified', 'scanner.fixture', 'fixture-v1', 1
    ),
    (
        '20000000-0000-0000-0000-000000000002',
        '20000000-0000-0000-0000-000000000102', repeat('4', 64), 256,
        'application/hwpx+zip', 'result', 'available', 'kms.artifact-v1', 1,
        'result.hwpx',
        'artifacts/v1/20000000000000000000000000000002/result/available/'
            || repeat('4', 64) || '.aes256gcm',
        'AES-256-GCM', decode(repeat('cd', 12), 'hex'), repeat('5', 64), repeat('6', 64),
        'verified', 'scanner.fixture', 'fixture-v1', 1
    );

INSERT INTO hwpx_agent.artifact_acl (
    tenant_id, artifact_id, subject_sha256, can_read, can_manage, can_read_quarantine
)
VALUES
    (
        '10000000-0000-0000-0000-000000000001',
        '10000000-0000-0000-0000-000000000101', repeat('a', 64), true, true, true
    ),
    (
        '20000000-0000-0000-0000-000000000002',
        '20000000-0000-0000-0000-000000000102', repeat('b', 64), true, true, true
    );

SET CONSTRAINTS ALL IMMEDIATE;

-- ASSERT: schema_version_digest_bound
DO $$
BEGIN
    IF (SELECT count(*) FROM hwpx_agent.schema_versions
        WHERE version = 2
          AND migration_name = 'p14.artifact_service_v1'
          AND migration_sha256 ~ '^[0-9a-f]{64}$') <> 1 THEN
        RAISE EXCEPTION 'artifact service schema version binding mismatch';
    END IF;
END
$$;

-- ASSERT: artifact_acl_forced_rls
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_class class
        JOIN pg_namespace namespace ON namespace.oid = class.relnamespace
        WHERE namespace.nspname = 'hwpx_agent' AND class.relname = 'artifact_acl'
          AND class.relrowsecurity AND class.relforcerowsecurity
    ) THEN
        RAISE EXCEPTION 'artifact ACL forced RLS is missing';
    END IF;
END
$$;

SET ROLE hwpx_agent_artifact_test_app;
SELECT set_config(
    'hwpx_agent.tenant_id', '10000000-0000-0000-0000-000000000001', true
);

-- ASSERT: own_artifact_visible
DO $$
BEGIN
    IF (SELECT count(*) FROM hwpx_agent.artifacts) <> 1 THEN
        RAISE EXCEPTION 'own artifact visibility mismatch';
    END IF;
END
$$;

-- ASSERT: cross_tenant_artifact_hidden
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM hwpx_agent.artifacts
        WHERE tenant_id = '20000000-0000-0000-0000-000000000002'
    ) THEN
        RAISE EXCEPTION 'cross-tenant artifact became visible';
    END IF;
END
$$;

-- ASSERT: own_acl_visible
DO $$
BEGIN
    IF (SELECT count(*) FROM hwpx_agent.artifact_acl) <> 1 THEN
        RAISE EXCEPTION 'own artifact ACL visibility mismatch';
    END IF;
END
$$;

-- ASSERT: cross_tenant_acl_hidden
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM hwpx_agent.artifact_acl
        WHERE tenant_id = '20000000-0000-0000-0000-000000000002'
    ) THEN
        RAISE EXCEPTION 'cross-tenant artifact ACL became visible';
    END IF;
END
$$;

-- ASSERT: cross_tenant_artifact_insert_denied
DO $$
BEGIN
    BEGIN
        INSERT INTO hwpx_agent.artifacts (
            tenant_id, artifact_id, content_sha256, size_bytes, media_type,
            artifact_kind, encryption_key_ref
        ) VALUES (
            '20000000-0000-0000-0000-000000000002',
            '20000000-0000-0000-0000-000000000199', repeat('7', 64), 1,
            'application/octet-stream', 'source', 'kms.artifact-v1'
        );
        RAISE EXCEPTION 'cross-tenant artifact insert unexpectedly succeeded';
    EXCEPTION WHEN insufficient_privilege THEN NULL;
    END;
END
$$;

-- ASSERT: cross_tenant_acl_insert_denied
DO $$
BEGIN
    BEGIN
        INSERT INTO hwpx_agent.artifact_acl (
            tenant_id, artifact_id, subject_sha256, can_read
        ) VALUES (
            '20000000-0000-0000-0000-000000000002',
            '20000000-0000-0000-0000-000000000102', repeat('c', 64), true
        );
        RAISE EXCEPTION 'cross-tenant artifact ACL insert unexpectedly succeeded';
    EXCEPTION WHEN insufficient_privilege THEN NULL;
    END;
END
$$;

-- ASSERT: encryption_identity_immutable
DO $$
BEGIN
    BEGIN
        UPDATE hwpx_agent.artifacts
        SET encryption_nonce = decode(repeat('ef', 12), 'hex')
        WHERE artifact_id = '10000000-0000-0000-0000-000000000101';
        RAISE EXCEPTION 'encryption identity update unexpectedly succeeded';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL;
    END;
END
$$;

-- ASSERT: empty_acl_rejected
DO $$
BEGIN
    BEGIN
        INSERT INTO hwpx_agent.artifact_acl (
            tenant_id, artifact_id, subject_sha256
        ) VALUES (
            '10000000-0000-0000-0000-000000000001',
            '10000000-0000-0000-0000-000000000101', repeat('d', 64)
        );
        RAISE EXCEPTION 'empty ACL unexpectedly succeeded';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
END
$$;

-- ASSERT: acl_grant_increments_generation
INSERT INTO hwpx_agent.artifact_acl (
    tenant_id, artifact_id, subject_sha256, can_read
) VALUES (
    '10000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000101', repeat('e', 64), true
);
DO $$
BEGIN
    IF (SELECT authorization_generation FROM hwpx_agent.artifacts
        WHERE artifact_id = '10000000-0000-0000-0000-000000000101') <> 2 THEN
        RAISE EXCEPTION 'ACL grant did not increment authorization generation';
    END IF;
END
$$;

-- ASSERT: acl_revoke_increments_generation
DELETE FROM hwpx_agent.artifact_acl
WHERE artifact_id = '10000000-0000-0000-0000-000000000101'
  AND subject_sha256 = repeat('e', 64);
DO $$
BEGIN
    IF (SELECT authorization_generation FROM hwpx_agent.artifacts
        WHERE artifact_id = '10000000-0000-0000-0000-000000000101') <> 3 THEN
        RAISE EXCEPTION 'ACL revoke did not increment authorization generation';
    END IF;
END
$$;

-- ASSERT: final_manager_required
DO $$
BEGIN
    BEGIN
        DELETE FROM hwpx_agent.artifact_acl
        WHERE artifact_id = '10000000-0000-0000-0000-000000000101'
          AND subject_sha256 = repeat('a', 64);
        SET CONSTRAINTS artifact_acl_manager_required IMMEDIATE;
        RAISE EXCEPTION 'final artifact manager deletion unexpectedly succeeded';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
END
$$;

-- ASSERT: malformed_object_key_rejected
DO $$
BEGIN
    BEGIN
        INSERT INTO hwpx_agent.artifacts (
            tenant_id, artifact_id, content_sha256, size_bytes, media_type, artifact_kind,
            storage_state, encryption_key_ref, service_metadata_version, filename, object_key,
            encryption_algorithm, encryption_nonce, aad_sha256, ciphertext_sha256,
            validation_state, scanner_engine_ref, scanner_signature_version,
            authorization_generation
        ) VALUES (
            '10000000-0000-0000-0000-000000000001',
            '10000000-0000-0000-0000-000000000111', repeat('8', 64), 1,
            'application/octet-stream', 'source', 'available', 'kms.artifact-v1', 1,
            'bad.bin', '../escape', 'AES-256-GCM', decode(repeat('ab', 12), 'hex'),
            repeat('8', 64), repeat('9', 64), 'verified', 'scanner.fixture', 'fixture-v1', 1
        );
        RAISE EXCEPTION 'malformed object key unexpectedly succeeded';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
END
$$;

-- ASSERT: state_validation_binding
DO $$
BEGIN
    BEGIN
        UPDATE hwpx_agent.artifacts
        SET validation_state = 'unverified', authorization_generation = 4
        WHERE artifact_id = '10000000-0000-0000-0000-000000000101';
        RAISE EXCEPTION 'available unverified artifact unexpectedly succeeded';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
END
$$;

-- ASSERT: legacy_available_rejected
DO $$
BEGIN
    BEGIN
        INSERT INTO hwpx_agent.artifacts (
            tenant_id, artifact_id, content_sha256, size_bytes, media_type,
            artifact_kind, storage_state, encryption_key_ref
        ) VALUES (
            '10000000-0000-0000-0000-000000000001',
            '10000000-0000-0000-0000-000000000114', repeat('7', 64), 1,
            'application/octet-stream', 'source', 'available', 'kms.artifact-v1'
        );
        RAISE EXCEPTION 'legacy available artifact unexpectedly succeeded';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
END
$$;

-- ASSERT: nonce_size_binding
DO $$
BEGIN
    BEGIN
        INSERT INTO hwpx_agent.artifacts (
            tenant_id, artifact_id, content_sha256, size_bytes, media_type, artifact_kind,
            storage_state, encryption_key_ref, service_metadata_version, filename, object_key,
            encryption_algorithm, encryption_nonce, aad_sha256, ciphertext_sha256,
            validation_state, scanner_engine_ref, scanner_signature_version,
            authorization_generation
        ) VALUES (
            '10000000-0000-0000-0000-000000000001',
            '10000000-0000-0000-0000-000000000112', repeat('9', 64), 1,
            'application/octet-stream', 'source', 'available', 'kms.artifact-v1', 1,
            'bad.bin',
            'artifacts/v1/10000000000000000000000000000001/source/available/'
                || repeat('9', 64) || '.aes256gcm',
            'AES-256-GCM', decode(repeat('ab', 11), 'hex'), repeat('8', 64), repeat('9', 64),
            'verified', 'scanner.fixture', 'fixture-v1', 1
        );
        RAISE EXCEPTION 'short AES-GCM nonce unexpectedly succeeded';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
END
$$;

-- ASSERT: state_change_requires_generation
DO $$
BEGIN
    BEGIN
        UPDATE hwpx_agent.artifacts
        SET storage_state = 'quarantined', validation_state = 'quarantined',
            quarantine_reason_code = 'MANUAL_REVIEW',
            object_key = 'artifacts/v1/10000000000000000000000000000001/source/quarantined/'
                || repeat('1', 64) || '.aes256gcm'
        WHERE artifact_id = '10000000-0000-0000-0000-000000000101';
        RAISE EXCEPTION 'security state changed without generation increment';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL;
    END;
END
$$;

-- ASSERT: quarantine_transition_bound
UPDATE hwpx_agent.artifacts
SET storage_state = 'quarantined', validation_state = 'quarantined',
    quarantine_reason_code = 'MANUAL_REVIEW', authorization_generation = 4,
    object_key = 'artifacts/v1/10000000000000000000000000000001/source/quarantined/'
        || repeat('1', 64) || '.aes256gcm'
WHERE artifact_id = '10000000-0000-0000-0000-000000000101';
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.artifacts
        WHERE artifact_id = '10000000-0000-0000-0000-000000000101'
          AND storage_state = 'quarantined'
          AND validation_state = 'quarantined'
          AND authorization_generation = 4
          AND quarantine_reason_code = 'MANUAL_REVIEW'
    ) THEN
        RAISE EXCEPTION 'bounded quarantine transition did not persist';
    END IF;
END
$$;

-- ASSERT: service_artifact_requires_manager
DO $$
BEGIN
    BEGIN
        INSERT INTO hwpx_agent.artifacts (
            tenant_id, artifact_id, content_sha256, size_bytes, media_type, artifact_kind,
            storage_state, encryption_key_ref, service_metadata_version, filename, object_key,
            encryption_algorithm, encryption_nonce, aad_sha256, ciphertext_sha256,
            validation_state, scanner_engine_ref, scanner_signature_version,
            authorization_generation
        ) VALUES (
            '10000000-0000-0000-0000-000000000001',
            '10000000-0000-0000-0000-000000000113', repeat('f', 64), 1,
            'application/octet-stream', 'source', 'available', 'kms.artifact-v1', 1,
            'unowned.bin',
            'artifacts/v1/10000000000000000000000000000001/source/available/'
                || repeat('f', 64) || '.aes256gcm',
            'AES-256-GCM', decode(repeat('ab', 12), 'hex'), repeat('e', 64), repeat('f', 64),
            'verified', 'scanner.fixture', 'fixture-v1', 1
        );
        SET CONSTRAINTS artifact_service_manager_required IMMEDIATE;
        RAISE EXCEPTION 'service artifact without manager unexpectedly succeeded';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
END
$$;

RESET ROLE;

-- ASSERT: public_privileges_revoked
DO $$
BEGIN
    IF has_table_privilege('public', 'hwpx_agent.artifact_acl', 'SELECT') THEN
        RAISE EXCEPTION 'PUBLIC unexpectedly has artifact ACL access';
    END IF;
END
$$;

COMMIT;

-- ASSERT: transaction_local_tenant_context_cleared
DO $$
BEGIN
    IF nullif(current_setting('hwpx_agent.tenant_id', true), '') IS NOT NULL THEN
        RAISE EXCEPTION 'transaction-local tenant context leaked after commit';
    END IF;
END
$$;

SELECT 'P14_ARTIFACT_SERVICE_SMOKE_PASS assertions=22';
