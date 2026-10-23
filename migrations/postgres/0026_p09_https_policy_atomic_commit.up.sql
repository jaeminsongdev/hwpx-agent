-- Policy validation and original revision CAS share one caller-owned transaction. No execution capability is issued.
BEGIN;
DO $$ BEGIN
    IF NOT EXISTS(SELECT 1 FROM hwpx_agent.schema_versions WHERE version=25 AND migration_name='p09.source_https_target_policy_v1')
        OR EXISTS(SELECT 1 FROM hwpx_agent.schema_versions WHERE version>=26) THEN
        RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='HTTPS_ATOMIC_REQUIRES_SCHEMA25';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256',true) IS NULL OR current_setting('hwpx_agent.migration_sha256',true) !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='HTTPS_ATOMIC_MIGRATION_DIGEST_REQUIRED';
    END IF;
END $$;
CREATE FUNCTION hwpx_agent.require_https_policy_commit_v1(
    p_tenant uuid,p_project uuid,p_branch uuid,p_subject character(64),p_document text,p_revision uuid,p_head bigint,
    p_result uuid,p_package character(64),p_provenance character(64),p_graph character(64),p_version uuid,p_generation bigint,
    p_policy uuid,p_digest character(64)
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,hwpx_agent AS $$
DECLARE v_policy hwpx_agent.source_https_target_policy_versions%ROWTYPE; v_count integer;
BEGIN
    PERFORM hwpx_agent.require_source_https_target_policy_role_v1(p_tenant,p_project,p_subject,true);
    -- Same branch lock/order as policy registration, revocation and the original CAS.
    PERFORM 1 FROM hwpx_agent.branches WHERE tenant_id=p_tenant AND project_id=p_project AND branch_id=p_branch FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='HTTPS_ATOMIC_SCOPE_DENIED'; END IF;
    PERFORM 1 FROM hwpx_agent.tenants WHERE tenant_id=p_tenant FOR SHARE;
    PERFORM 1 FROM hwpx_agent.projects WHERE tenant_id=p_tenant AND project_id=p_project FOR SHARE;
    PERFORM 1 FROM hwpx_agent.project_acl WHERE tenant_id=p_tenant AND project_id=p_project AND subject_sha256=p_subject FOR SHARE;
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='HTTPS_ATOMIC_MEMBER_DENIED'; END IF;
    PERFORM artifact_id FROM hwpx_agent.artifacts WHERE tenant_id=p_tenant AND artifact_id IN(p_result,p_policy) ORDER BY artifact_id FOR SHARE;
    GET DIAGNOSTICS v_count=ROW_COUNT;
    IF v_count<>2 THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='HTTPS_ATOMIC_ARTIFACTS_DENIED'; END IF;
    PERFORM artifact_id FROM hwpx_agent.artifact_acl WHERE tenant_id=p_tenant AND artifact_id IN(p_result,p_policy)
        AND subject_sha256=p_subject ORDER BY artifact_id FOR SHARE;
    GET DIAGNOSTICS v_count=ROW_COUNT;
    IF v_count<>2 THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='HTTPS_ATOMIC_ACLS_DENIED'; END IF;
    -- This statement observes completed writers before the locks; later writers wait until the SAME CAS transaction ends.
    SELECT * INTO v_policy FROM hwpx_agent.read_source_https_target_policy_v1(p_tenant,p_project,p_branch,p_subject,p_document,p_revision,p_head);
    IF NOT FOUND OR ROW(v_policy.policy_version_id,v_policy.generation,v_policy.policy_artifact_id,v_policy.policy_artifact_sha256,
        v_policy.source_result_artifact_id,v_policy.source_package_sha256,v_policy.source_provenance_sha256,v_policy.observed_graph_sha256)
        IS DISTINCT FROM ROW(p_version,p_generation,p_policy,p_digest,p_result,p_package,p_provenance,p_graph) THEN
        RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='HTTPS_ATOMIC_POLICY_CHANGED';
    END IF;
END
$$;
REVOKE ALL ON FUNCTION hwpx_agent.require_https_policy_commit_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,character,character,character,uuid,bigint,uuid,character) FROM PUBLIC;
INSERT INTO hwpx_agent.schema_versions(version,migration_name,migration_sha256)
VALUES(26,'p09.https_policy_atomic_commit_v1',current_setting('hwpx_agent.migration_sha256'));
COMMIT;
