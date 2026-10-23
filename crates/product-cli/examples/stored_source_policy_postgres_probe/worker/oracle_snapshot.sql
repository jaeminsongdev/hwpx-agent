-- Failure-only, non-locking observation of the SAME owned record/result/receipt arguments.
-- BOOL/NULL columns only. Not the original atomic oracle or proof of failure cause.
SELECT
    (b.head_revision_id = $6) AS head_revision,
    (b.head_generation = r.expected_revision_generation + 1) AS head_generation,
    (b.head_generation >= 0) AS head_generation_nonnegative,
    (sa.service_metadata_version = 1) AS source_metadata,
    (sa.storage_state = 'available') AS source_available,
    (sa.validation_state = 'verified') AS source_verified,
    (sa.artifact_kind = 'source') AS source_kind,
    (sa.content_sha256 = r.source_artifact_sha256) AS source_digest,
    (sacl.can_read OR sacl.can_manage) AS source_acl,
    (ra.service_metadata_version = 1) AS receipt_metadata,
    (ra.storage_state = 'available') AS receipt_available,
    (ra.validation_state = 'verified') AS receipt_verified,
    (ra.artifact_kind = 'receipt') AS receipt_kind,
    (ra.content_sha256 = r.transaction_receipt_sha256) AS receipt_digest,
    (racl.can_read OR racl.can_manage) AS receipt_acl,
    (v.source_artifact_id = r.source_artifact_id) AS revision_source,
    (v.operation_plan_sha256 = j.operation_plan_sha256) AS revision_plan,
    (v.validation_state = 'verified') AS revision_verified,
    (v.created_by_subject_sha256 = $3::character(64)) AS revision_subject,
    (a.service_metadata_version = 1) AS result_metadata,
    (a.storage_state = 'available') AS result_available,
    (a.validation_state = 'verified') AS result_verified,
    (a.artifact_kind = 'result') AS result_kind,
    (a.content_sha256 = r.expected_effect_sha256) AS result_digest,
    (acl.can_read OR acl.can_manage) AS result_acl,
    (s.seal_kind = 'service_v1') AS seal_kind,
    (s.committed_generation = r.expected_revision_generation + 1) AS seal_generation,
    (s.transaction_receipt_sha256 = r.transaction_receipt_sha256) AS seal_receipt,
    (s.commit_id = c.commit_id) AS seal_commit_id,
    (s.commit_request_sha256 = c.commit_request_sha256) AS seal_request,
    (c.branch_id = r.branch_id) AS commit_branch,
    (c.previous_revision_id IS NOT DISTINCT FROM r.expected_revision_id) AS commit_previous,
    (c.expected_generation = r.expected_revision_generation) AS commit_expected_generation,
    (c.committed_generation = r.expected_revision_generation + 1) AS commit_generation,
    (c.transaction_receipt_sha256 = r.transaction_receipt_sha256) AS commit_receipt,
    (c.subject_sha256 = $3::character(64)) AS commit_subject,
    (r.job_id = $5) AS record_job_binding,
    (r.record_version = 2 AND r.state = 'in_progress') AS record_in_progress,
    (j.state_machine_version = 2 AND j.state = 'validating') AS job_validating,
    (j.lease_expires_at > clock_timestamp()) AS lease_current_at_observation
FROM hwpx_agent.idempotency_records r
LEFT JOIN hwpx_agent.jobs j ON j.tenant_id=r.tenant_id AND j.project_id=r.project_id AND j.job_id=r.job_id
LEFT JOIN hwpx_agent.branches b ON b.tenant_id=r.tenant_id AND b.project_id=r.project_id AND b.branch_id=r.branch_id
LEFT JOIN hwpx_agent.artifacts sa ON sa.tenant_id=r.tenant_id AND sa.artifact_id=r.source_artifact_id
LEFT JOIN hwpx_agent.artifact_acl sacl ON sacl.tenant_id=sa.tenant_id AND sacl.artifact_id=sa.artifact_id AND sacl.subject_sha256=$3::character(64)
LEFT JOIN hwpx_agent.artifacts ra ON ra.tenant_id=r.tenant_id AND ra.artifact_id=$7
LEFT JOIN hwpx_agent.artifact_acl racl ON racl.tenant_id=ra.tenant_id AND racl.artifact_id=ra.artifact_id AND racl.subject_sha256=$3::character(64)
LEFT JOIN hwpx_agent.revisions v ON v.tenant_id=r.tenant_id AND v.project_id=r.project_id AND v.revision_id=$6
LEFT JOIN hwpx_agent.artifacts a ON a.tenant_id=v.tenant_id AND a.artifact_id=v.result_artifact_id
LEFT JOIN hwpx_agent.artifact_acl acl ON acl.tenant_id=a.tenant_id AND acl.artifact_id=a.artifact_id AND acl.subject_sha256=$3::character(64)
LEFT JOIN hwpx_agent.revision_graph_seals s ON s.tenant_id=v.tenant_id AND s.project_id=v.project_id AND s.revision_id=v.revision_id
LEFT JOIN hwpx_agent.revision_commit_receipts c ON c.tenant_id=v.tenant_id AND c.project_id=v.project_id AND c.committed_revision_id=v.revision_id
WHERE r.tenant_id=$1 AND r.project_id=$2 AND r.subject_sha256=$3::character(64)
  AND r.idempotency_key=$4;
