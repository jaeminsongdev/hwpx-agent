BEGIN;

INSERT INTO hwpx_agent.project_acl (
    tenant_id, project_id, subject_sha256, role
) VALUES (
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001',
    '__P17_PULL_SUBJECT_SHA256__', 'owner'
);

INSERT INTO hwpx_agent.artifact_acl (
    tenant_id, artifact_id, subject_sha256, can_read, can_manage
)
SELECT
    tenant_id, artifact_id, '__P17_PULL_SUBJECT_SHA256__', true, true
FROM hwpx_agent.artifacts
WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001';

INSERT INTO hwpx_agent.project_local_mirrors (
    tenant_id, project_id, mirror_id, device_sha256, branch_id,
    observed_revision_id, observed_generation, snapshot_sha256,
    created_by_subject_sha256
) VALUES
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd7000000-0000-0000-0000-000000000002',
        '4d96f5b9e2cd98acb9c07dd3e6dff689e982fa8a96e38235a78a8c02af26fc20',
        'd3000000-0000-0000-0000-000000000001',
        '__P17_REVISION_ONE_UUID__', 1,
        '50d49b1b57c9efac0446b21ad91529443906865a859fe5abbca967a85d803e6f',
        '__P17_PULL_SUBJECT_SHA256__'
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd7000000-0000-0000-0000-000000000003',
        'fa8ea73bf42b96db10aa27407cd2ea7901c726e0d048357bd085780938de8495',
        'd3000000-0000-0000-0000-000000000001',
        '__P17_REVISION_ONE_UUID__', 1,
        '50d49b1b57c9efac0446b21ad91529443906865a859fe5abbca967a85d803e6f',
        '__P17_PULL_SUBJECT_SHA256__'
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd2000000-0000-0000-0000-000000000001',
        'd7000000-0000-0000-0000-000000000004',
        'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',
        'd3000000-0000-0000-0000-000000000001',
        '__P17_REVISION_ONE_UUID__', 1,
        '50d49b1b57c9efac0446b21ad91529443906865a859fe5abbca967a85d803e6f',
        '__P17_PULL_SUBJECT_SHA256__'
    );

UPDATE hwpx_agent.project_local_mirrors
SET snapshot_sha256 = repeat('8', 64),
    pending_plan_sha256 = repeat('9', 64),
    state = 'ahead', updated_at = transaction_timestamp()
WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
  AND mirror_id = 'd7000000-0000-0000-0000-000000000003';

COMMIT;
