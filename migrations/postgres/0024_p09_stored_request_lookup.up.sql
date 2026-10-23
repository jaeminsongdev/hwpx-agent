-- Additive cold-request observation only. No claim/lease/retry/commit or product routing permit.
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM hwpx_agent.schema_versions WHERE version=23 AND migration_name='p09.stored_revision_jobs_v1')
        OR EXISTS(SELECT 1 FROM hwpx_agent.schema_versions WHERE version>=24) THEN
        RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='STORED_REQUEST_LOOKUP_REQUIRES_SCHEMA_23';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256',true) IS NULL
        OR current_setting('hwpx_agent.migration_sha256',true) !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='STORED_REQUEST_LOOKUP_MIGRATION_DIGEST_REQUIRED';
    END IF;
END
$$;

-- Both point lookups use existing tenant/project/key or tenant/project/job primary keys.
-- STABLE snapshot; no row/advisory locks, domain writes or authority issuance.
CREATE FUNCTION hwpx_agent.read_stored_revision_request_v1(
    p_tenant_id uuid,p_project_id uuid,p_branch_id uuid,p_subject_sha256 character(64),
    p_key uuid,p_job uuid,p_request uuid,p_request_sha256 character(64),
    p_source_sha256 character(64),p_expected_revision uuid,p_expected_generation bigint
)
RETURNS TABLE(
    returned_outcome text,returned_job_id uuid,returned_state text,returned_attempt_count integer,
    returned_fencing_token bigint,returned_retry_not_before timestamptz,returned_result_revision_id uuid,
    returned_terminal_error_code text,returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    r hwpx_agent.idempotency_records%ROWTYPE;
    j hwpx_agent.jobs%ROWTYPE;
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(p_tenant_id,p_project_id,p_subject_sha256);
    IF p_branch_id IS NULL OR p_key IS NULL OR p_job IS NULL OR p_request IS NULL
        OR p_expected_revision IS NULL OR p_expected_generation IS NULL OR p_expected_generation<=0
        OR p_request_sha256 IS NULL OR p_request_sha256 !~ '^[0-9a-f]{64}$'
        OR p_source_sha256 IS NULL OR p_source_sha256 !~ '^[0-9a-f]{64}$'
        OR array_position(ARRAY[p_branch_id,p_key,p_job,p_request,p_expected_revision],'00000000-0000-0000-0000-000000000000'::uuid) IS NOT NULL THEN
        RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='STORED_REQUEST_LOOKUP_INVALID';
    END IF;
    SELECT * INTO r FROM hwpx_agent.idempotency_records x
        WHERE x.tenant_id=p_tenant_id AND x.project_id=p_project_id AND x.idempotency_key=p_key;
    IF NOT FOUND THEN RETURN; END IF;
    -- Another subject cannot inspect the occupied key or learn its job state.
    IF r.subject_sha256 IS DISTINCT FROM p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='STORED_REQUEST_LOOKUP_UNAVAILABLE';
    END IF;
    IF r.record_version<>2 OR ROW(r.branch_id,r.job_id,r.request_id,r.request_sha256,r.source_artifact_sha256,r.expected_revision_id,r.expected_revision_generation)
        IS DISTINCT FROM ROW(p_branch_id,p_job,p_request,p_request_sha256,p_source_sha256,p_expected_revision,p_expected_generation) THEN
        RAISE EXCEPTION USING ERRCODE='23505',MESSAGE='STORED_REQUEST_KEY_CONFLICT';
    END IF;
    SELECT * INTO j FROM hwpx_agent.jobs x
        WHERE x.tenant_id=p_tenant_id AND x.project_id=p_project_id AND x.job_id=r.job_id;
    IF NOT FOUND OR j.state_machine_version<>2
        OR ROW(j.request_id,j.input_artifact_id,j.expected_revision_id) IS DISTINCT FROM ROW(r.request_id,r.source_artifact_id,r.expected_revision_id) THEN
        RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='STORED_REQUEST_LOOKUP_INCONSISTENT';
    END IF;
    IF NOT hwpx_agent.stored_revision_source_qualified_v1(p_tenant_id,p_project_id,r.branch_id,p_subject_sha256,
        r.source_artifact_id,r.source_artifact_sha256,r.expected_revision_id,r.expected_revision_generation,false) THEN
        RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='STORED_REQUEST_LOOKUP_UNAVAILABLE';
    END IF;
    RETURN QUERY SELECT 'replay'::text,r.job_id,r.state,r.attempt_count,r.last_fencing_token,
        r.retry_not_before,r.result_revision_id,r.terminal_error_code,r.receipt_artifact_id;
END
$$;
REVOKE ALL ON FUNCTION hwpx_agent.read_stored_revision_request_v1(uuid,uuid,uuid,character,uuid,uuid,uuid,character,character,uuid,bigint) FROM PUBLIC;
-- No grants installed. The explicit schema24 connector must admit exact schema/function/security first.
INSERT INTO hwpx_agent.schema_versions(version,migration_name,migration_sha256)
VALUES(24,'p09.stored_request_lookup_v1',current_setting('hwpx_agent.migration_sha256'));
COMMIT;
