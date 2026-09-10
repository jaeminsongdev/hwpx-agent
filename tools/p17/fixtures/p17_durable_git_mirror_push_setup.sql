BEGIN;

INSERT INTO hwpx_agent.tenants (tenant_id, slug)
VALUES ('d1000000-0000-0000-0000-000000000001', 'p17-durable-git-push-probe');

INSERT INTO hwpx_agent.projects (
    tenant_id, project_id, slug, display_name, target_profile_id,
    retention_policy_id
) VALUES (
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001',
    'p17-durable-git-project', 'P17 Durable Git Project',
    'hancom-hangul-2020-secondary', 'retention.local-test'
);

INSERT INTO hwpx_agent.project_acl (
    tenant_id, project_id, subject_sha256, role
) VALUES (
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001',
    '__P17_SERVICE_SUBJECT_SHA256__', 'owner'
);

INSERT INTO hwpx_agent.artifacts (
    tenant_id, artifact_id, content_sha256, size_bytes, media_type, artifact_kind,
    storage_state, encryption_key_ref, verified_at, service_metadata_version, filename,
    object_key, encryption_algorithm, encryption_nonce, aad_sha256, ciphertext_sha256,
    validation_state, scanner_engine_ref, scanner_signature_version,
    authorization_generation
) VALUES
    (
        'd1000000-0000-0000-0000-000000000001',
        'd4000000-0000-0000-0000-000000000001',
        'ed685a0de881a84828b3a46573afd4458419ea758367e7e5351c47746471cbbc',
        128, 'application/vnd.hancom.hwpx', 'source', 'available',
        'kms.p17-durable-probe', transaction_timestamp(), 1, 'source.hwpx',
        'artifacts/v1/d1000000000000000000000000000001/source/available/ed685a0de881a84828b3a46573afd4458419ea758367e7e5351c47746471cbbc.aes256gcm',
        'AES-256-GCM', decode(repeat('01', 12), 'hex'), repeat('1', 64),
        repeat('2', 64), 'verified', 'scanner.p17-durable-probe', 'v1', 1
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd4000000-0000-0000-0000-000000000002',
        '50d49b1b57c9efac0446b21ad91529443906865a859fe5abbca967a85d803e6f',
        256, 'application/vnd.hancom.hwpx', 'result', 'available',
        'kms.p17-durable-probe', transaction_timestamp(), 1, 'result.hwpx',
        'artifacts/v1/d1000000000000000000000000000001/result/available/50d49b1b57c9efac0446b21ad91529443906865a859fe5abbca967a85d803e6f.aes256gcm',
        'AES-256-GCM', decode(repeat('02', 12), 'hex'), repeat('3', 64),
        repeat('4', 64), 'verified', 'scanner.p17-durable-probe', 'v1', 1
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd4000000-0000-0000-0000-000000000003',
        repeat('6', 64),
        384, 'application/vnd.hancom.hwpx', 'result', 'available',
        'kms.p17-durable-probe', transaction_timestamp(), 1, 'result-2.hwpx',
        'artifacts/v1/d1000000000000000000000000000001/result/available/6666666666666666666666666666666666666666666666666666666666666666.aes256gcm',
        'AES-256-GCM', decode(repeat('03', 12), 'hex'), repeat('5', 64),
        repeat('6', 64), 'verified', 'scanner.p17-durable-probe', 'v1', 1
    );

INSERT INTO hwpx_agent.artifact_acl (
    tenant_id, artifact_id, subject_sha256, can_read, can_manage
)
SELECT
    tenant_id, artifact_id, '__P17_SERVICE_SUBJECT_SHA256__', true, true
FROM hwpx_agent.artifacts
WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001';

INSERT INTO hwpx_agent.branches (
    tenant_id, project_id, branch_id, name, head_revision_id,
    head_generation, is_default, created_by_subject_sha256
) VALUES (
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001',
    'd3000000-0000-0000-0000-000000000001', 'main',
    NULL, 0, true, '__P17_SERVICE_SUBJECT_SHA256__'
);

INSERT INTO hwpx_agent.project_local_mirrors (
    tenant_id, project_id, mirror_id, device_sha256, branch_id,
    observed_revision_id, observed_generation, snapshot_sha256,
    created_by_subject_sha256
) VALUES (
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001',
    'd7000000-0000-0000-0000-000000000001',
    'fb453a77dac233cb10d2701bab550ce4f0e19071f02c2a8250560236b4293147',
    'd3000000-0000-0000-0000-000000000001',
    NULL, 0,
    'ed685a0de881a84828b3a46573afd4458419ea758367e7e5351c47746471cbbc',
    '__P17_SERVICE_SUBJECT_SHA256__'
);

COMMIT;
