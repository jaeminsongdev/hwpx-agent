BEGIN;

INSERT INTO hwpx_agent.tenants (tenant_id, slug)
VALUES ('d1000000-0000-0000-0000-000000000001', 'p17-checkpoint-probe');

INSERT INTO hwpx_agent.projects (
    tenant_id, project_id, slug, display_name, target_profile_id,
    retention_policy_id
) VALUES (
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001',
    'p17-checkpoint-project', 'P17 Checkpoint Project',
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
    tenant_id, artifact_id, content_sha256, size_bytes, media_type,
    artifact_kind, storage_state, encryption_key_ref
) VALUES
    (
        'd1000000-0000-0000-0000-000000000001',
        'd4000000-0000-0000-0000-000000000001', repeat('1', 64), 128,
        'application/vnd.hancom.hwpx', 'source', 'staged', 'kms.p17-probe'
    ),
    (
        'd1000000-0000-0000-0000-000000000001',
        'd4000000-0000-0000-0000-000000000002', repeat('2', 64), 256,
        'application/vnd.hancom.hwpx', 'result', 'staged', 'kms.p17-probe'
    );

INSERT INTO hwpx_agent.revisions (
    tenant_id, project_id, revision_id, source_artifact_id,
    result_artifact_id, semantic_diff_artifact_id, operation_plan_sha256,
    validation_state, validation_summary_sha256, created_by_subject_sha256
) VALUES (
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001',
    'd5000000-0000-0000-0000-000000000001',
    'd4000000-0000-0000-0000-000000000001',
    'd4000000-0000-0000-0000-000000000002', NULL,
    repeat('3', 64), 'verified', repeat('4', 64),
    '__P17_SERVICE_SUBJECT_SHA256__'
);

INSERT INTO hwpx_agent.revision_graph_seals (
    tenant_id, project_id, revision_id, seal_kind, parent_count,
    committed_generation, commit_id, commit_request_sha256,
    transaction_receipt_sha256
) VALUES (
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001',
    'd5000000-0000-0000-0000-000000000001',
    'service_v1', 0, 1,
    'd6000000-0000-0000-0000-000000000001', repeat('5', 64), repeat('6', 64)
);

UPDATE hwpx_agent.projects
SET head_revision_id = 'd5000000-0000-0000-0000-000000000001',
    head_generation = 1
WHERE tenant_id = 'd1000000-0000-0000-0000-000000000001'
  AND project_id = 'd2000000-0000-0000-0000-000000000001';

INSERT INTO hwpx_agent.branches (
    tenant_id, project_id, branch_id, name, head_revision_id,
    head_generation, is_default, created_by_subject_sha256
) VALUES (
    'd1000000-0000-0000-0000-000000000001',
    'd2000000-0000-0000-0000-000000000001',
    'd3000000-0000-0000-0000-000000000001', 'main',
    'd5000000-0000-0000-0000-000000000001', 1, true,
    '__P17_SERVICE_SUBJECT_SHA256__'
);

COMMIT;
