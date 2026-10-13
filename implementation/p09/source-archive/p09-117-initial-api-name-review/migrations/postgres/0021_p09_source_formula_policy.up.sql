-- P09-117: separate FORMULA policy DATA domain; not signed issuer/execution qualification.
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 20 AND migration_name = 'p09.source_form_policy_v1')
        OR EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version >= 21) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'FORMULA_POLICY_REQUIRES_SCHEMA_20';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256', true) IS NULL
        OR current_setting('hwpx_agent.migration_sha256', true) !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'FORMULA_POLICY_MIGRATION_DIGEST_REQUIRED';
    END IF;
END
$$;

-- Metadata only. Policy values belong to an existing AES-GCM Evidence artifact,
-- with a dedicated explicit-policy media type. Never plaintext JSON in this table.
CREATE TABLE hwpx_agent.source_formula_policy_versions (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    branch_id uuid NOT NULL,
    document_id text NOT NULL CHECK (document_id ~ '^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$'),
    policy_version_id uuid NOT NULL CHECK (policy_version_id <> '00000000-0000-0000-0000-000000000000'::uuid),
    generation bigint NOT NULL CHECK (generation > 0),
    source_revision_id uuid NOT NULL,
    source_head_generation bigint NOT NULL CHECK (source_head_generation > 0),
    source_result_artifact_id uuid NOT NULL,
    source_package_sha256 character(64) NOT NULL CHECK (source_package_sha256 ~ '^[0-9a-f]{64}$'),
    source_provenance_sha256 character(64) NOT NULL CHECK (source_provenance_sha256 ~ '^[0-9a-f]{64}$'),
    observed_graph_sha256 character(64) NOT NULL CHECK (observed_graph_sha256 ~ '^[0-9a-f]{64}$'),
    policy_artifact_id uuid NOT NULL,
    policy_artifact_sha256 character(64) NOT NULL CHECK (policy_artifact_sha256 ~ '^[0-9a-f]{64}$'),
    created_by_subject_sha256 character(64) NOT NULL CHECK (created_by_subject_sha256 ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, project_id, policy_version_id),
    UNIQUE (tenant_id, project_id, branch_id, document_id, generation),
    FOREIGN KEY (tenant_id, project_id, branch_id) REFERENCES hwpx_agent.branches ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, project_id, source_revision_id) REFERENCES hwpx_agent.revisions ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, source_result_artifact_id) REFERENCES hwpx_agent.artifacts ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, policy_artifact_id) REFERENCES hwpx_agent.artifacts ON DELETE RESTRICT,
    CHECK (source_result_artifact_id <> policy_artifact_id)
);
CREATE TABLE hwpx_agent.source_formula_policy_revocations (
    tenant_id uuid NOT NULL, project_id uuid NOT NULL, policy_version_id uuid NOT NULL,
    revoked_by_subject_sha256 character(64) NOT NULL CHECK (revoked_by_subject_sha256 ~ '^[0-9a-f]{64}$'),
    revoked_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, project_id, policy_version_id),
    FOREIGN KEY (tenant_id, project_id, policy_version_id)
        REFERENCES hwpx_agent.source_formula_policy_versions ON DELETE RESTRICT
);
ALTER TABLE hwpx_agent.source_formula_policy_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.source_formula_policy_versions FORCE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.source_formula_policy_revocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.source_formula_policy_revocations FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.source_formula_policy_versions
    USING (tenant_id = hwpx_agent.current_tenant_id()) WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());
CREATE POLICY tenant_isolation ON hwpx_agent.source_formula_policy_revocations
    USING (tenant_id = hwpx_agent.current_tenant_id()) WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());
REVOKE ALL ON hwpx_agent.source_formula_policy_versions, hwpx_agent.source_formula_policy_revocations FROM PUBLIC;
CREATE TRIGGER source_formula_policy_versions_immutable BEFORE UPDATE OR DELETE
    ON hwpx_agent.source_formula_policy_versions FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();
CREATE TRIGGER source_formula_policy_revocations_immutable BEFORE UPDATE OR DELETE
    ON hwpx_agent.source_formula_policy_revocations FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();

CREATE FUNCTION hwpx_agent.require_source_formula_policy_role_v1(
    p_tenant uuid, p_project uuid, p_subject character(64), p_edit boolean
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, hwpx_agent AS $$
BEGIN
    IF p_tenant IS DISTINCT FROM hwpx_agent.current_tenant_id()
        OR p_subject IS DISTINCT FROM hwpx_agent.current_subject_sha256()
        OR p_edit IS NULL OR NOT EXISTS (
            SELECT 1 FROM hwpx_agent.project_acl acl
            JOIN hwpx_agent.projects project USING (tenant_id, project_id)
            JOIN hwpx_agent.tenants tenant USING (tenant_id)
            WHERE acl.tenant_id = p_tenant AND acl.project_id = p_project AND acl.subject_sha256 = p_subject
                AND project.state = 'active' AND tenant.state = 'active'
                AND (NOT p_edit OR acl.role IN ('owner','editor'))
        ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'FORMULA_POLICY_SCOPE_DENIED';
    END IF;
END
$$;
CREATE FUNCTION hwpx_agent.require_source_formula_policy_artifacts_v1(
    p_tenant uuid, p_subject character(64), p_result uuid, p_package character(64),
    p_policy uuid, p_policy_digest character(64), p_manage boolean
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, hwpx_agent AS $$
BEGIN
    IF p_manage IS NULL OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.artifacts result
        JOIN hwpx_agent.artifact_acl result_acl ON result_acl.tenant_id=result.tenant_id AND result_acl.artifact_id=result.artifact_id
        JOIN hwpx_agent.artifacts policy ON policy.tenant_id=result.tenant_id
        JOIN hwpx_agent.artifact_acl policy_acl ON policy_acl.tenant_id=policy.tenant_id AND policy_acl.artifact_id=policy.artifact_id
        WHERE result.tenant_id=p_tenant AND result.artifact_id=p_result
            AND result.artifact_kind='result' AND result.content_sha256=p_package
            AND result.service_metadata_version=1 AND result.storage_state='available'
            AND result.validation_state='verified' AND result.quarantine_reason_code IS NULL
            AND result.size_bytes BETWEEN 1 AND 33554432
            AND result_acl.subject_sha256=p_subject AND result_acl.can_read
            AND policy.artifact_id=p_policy AND policy.artifact_id<>result.artifact_id
            AND policy.artifact_kind='evidence' AND policy.content_sha256=p_policy_digest
            AND policy.media_type='application/vnd.hwpx-agent.source-form-policy+json'
            AND policy.service_metadata_version=1 AND policy.storage_state='available'
            AND policy.validation_state='verified' AND policy.quarantine_reason_code IS NULL
            AND policy.size_bytes BETWEEN 1 AND 1048576
            AND policy_acl.subject_sha256=p_subject AND policy_acl.can_read
            AND (NOT p_manage OR policy_acl.can_manage)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'FORMULA_POLICY_ARTIFACT_UNAVAILABLE';
    END IF;
END
$$;

CREATE FUNCTION hwpx_agent.register_source_formula_policy_v1(
    p_tenant uuid, p_project uuid, p_branch uuid, p_subject character(64), p_document text,
    p_version uuid, p_expected_generation bigint, p_revision uuid, p_head_generation bigint,
    p_package character(64), p_provenance character(64), p_graph character(64),
    p_policy_artifact uuid, p_policy_digest character(64)
) RETURNS bigint LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, hwpx_agent AS $$
DECLARE v_head uuid; v_head_generation bigint; v_generation bigint; v_result uuid;
BEGIN
    PERFORM hwpx_agent.require_source_formula_policy_role_v1(p_tenant,p_project,p_subject,true);
    SELECT head_revision_id,head_generation INTO v_head,v_head_generation FROM hwpx_agent.branches
        WHERE tenant_id=p_tenant AND project_id=p_project AND branch_id=p_branch FOR UPDATE;
    IF NOT FOUND OR v_head IS NULL OR ROW(v_head,v_head_generation) IS DISTINCT FROM ROW(p_revision,p_head_generation) THEN
        RAISE EXCEPTION USING ERRCODE='40001', MESSAGE='FORMULA_POLICY_SOURCE_HEAD_CHANGED';
    END IF;
    SELECT result_artifact_id INTO v_result FROM hwpx_agent.revisions
        WHERE tenant_id=p_tenant AND project_id=p_project AND revision_id=v_head;
    PERFORM hwpx_agent.require_source_formula_policy_artifacts_v1(p_tenant,p_subject,v_result,p_package,p_policy_artifact,p_policy_digest,true);
    SELECT coalesce(max(generation),0) INTO v_generation FROM hwpx_agent.source_formula_policy_versions
        WHERE tenant_id=p_tenant AND project_id=p_project AND branch_id=p_branch AND document_id=p_document;
    IF v_generation IS DISTINCT FROM p_expected_generation OR v_generation=9223372036854775807 THEN
        RAISE EXCEPTION USING ERRCODE='40001', MESSAGE='FORMULA_POLICY_GENERATION_CHANGED';
    END IF;
    INSERT INTO hwpx_agent.source_formula_policy_versions(tenant_id,project_id,branch_id,document_id,policy_version_id,
        generation,source_revision_id,source_head_generation,source_result_artifact_id,source_package_sha256,
        source_provenance_sha256,observed_graph_sha256,policy_artifact_id,policy_artifact_sha256,created_by_subject_sha256)
    VALUES(p_tenant,p_project,p_branch,p_document,p_version,v_generation+1,p_revision,p_head_generation,v_result,
        p_package,p_provenance,p_graph,p_policy_artifact,p_policy_digest,p_subject);
    RETURN v_generation+1;
END
$$;

CREATE FUNCTION hwpx_agent.read_source_formula_policy_v1(
    p_tenant uuid, p_project uuid, p_branch uuid, p_subject character(64), p_document text,
    p_revision uuid, p_head_generation bigint
) RETURNS SETOF hwpx_agent.source_formula_policy_versions LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent AS $$
DECLARE v_policy hwpx_agent.source_formula_policy_versions%ROWTYPE; v_head uuid; v_generation bigint;
BEGIN
    PERFORM hwpx_agent.require_source_formula_policy_role_v1(p_tenant,p_project,p_subject,false);
    SELECT head_revision_id,head_generation INTO v_head,v_generation FROM hwpx_agent.branches
        WHERE tenant_id=p_tenant AND project_id=p_project AND branch_id=p_branch;
    IF NOT FOUND OR ROW(v_head,v_generation) IS DISTINCT FROM ROW(p_revision,p_head_generation) THEN
        RAISE EXCEPTION USING ERRCODE='40001', MESSAGE='FORMULA_POLICY_SOURCE_HEAD_CHANGED';
    END IF;
    SELECT * INTO v_policy FROM hwpx_agent.source_formula_policy_versions
        WHERE tenant_id=p_tenant AND project_id=p_project AND branch_id=p_branch AND document_id=p_document
        ORDER BY generation DESC LIMIT 1;
    IF NOT FOUND OR ROW(v_policy.source_revision_id,v_policy.source_head_generation) IS DISTINCT FROM ROW(p_revision,p_head_generation)
        OR EXISTS(SELECT 1 FROM hwpx_agent.source_formula_policy_revocations
            WHERE tenant_id=p_tenant AND project_id=p_project AND policy_version_id=v_policy.policy_version_id) THEN
        RAISE EXCEPTION USING ERRCODE='42501', MESSAGE='FORMULA_POLICY_NOT_CURRENT';
    END IF;
    PERFORM hwpx_agent.require_source_formula_policy_artifacts_v1(p_tenant,p_subject,v_policy.source_result_artifact_id,
        v_policy.source_package_sha256,v_policy.policy_artifact_id,v_policy.policy_artifact_sha256,false);
    RETURN NEXT v_policy;
END
$$;
CREATE FUNCTION hwpx_agent.revoke_source_formula_policy_v1(
    p_tenant uuid,p_project uuid,p_branch uuid,p_subject character(64),p_document text,p_version uuid,p_expected_generation bigint
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,hwpx_agent AS $$
DECLARE v_policy hwpx_agent.source_formula_policy_versions%ROWTYPE;
BEGIN
    PERFORM hwpx_agent.require_source_formula_policy_role_v1(p_tenant,p_project,p_subject,true);
    PERFORM 1 FROM hwpx_agent.branches WHERE tenant_id=p_tenant AND project_id=p_project AND branch_id=p_branch FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORMULA_POLICY_SCOPE_DENIED'; END IF;
    SELECT * INTO v_policy FROM hwpx_agent.source_formula_policy_versions
        WHERE tenant_id=p_tenant AND project_id=p_project AND branch_id=p_branch AND document_id=p_document ORDER BY generation DESC LIMIT 1;
    IF NOT FOUND OR ROW(v_policy.policy_version_id,v_policy.generation) IS DISTINCT FROM ROW(p_version,p_expected_generation) THEN
        RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='FORMULA_POLICY_GENERATION_CHANGED';
    END IF;
    INSERT INTO hwpx_agent.source_formula_policy_revocations(tenant_id,project_id,policy_version_id,revoked_by_subject_sha256)
        VALUES(p_tenant,p_project,p_version,p_subject);
END
$$;
REVOKE ALL ON FUNCTION hwpx_agent.require_source_formula_policy_role_v1(uuid,uuid,character,boolean),
    hwpx_agent.require_source_formula_policy_artifacts_v1(uuid,character,uuid,character,uuid,character,boolean),
    hwpx_agent.register_source_formula_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint,character,character,character,uuid,character),
    hwpx_agent.read_source_formula_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint),
    hwpx_agent.revoke_source_formula_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint) FROM PUBLIC;
INSERT INTO hwpx_agent.schema_versions(version,migration_name,migration_sha256)
VALUES(21,'p09.source_formula_policy_v1',current_setting('hwpx_agent.migration_sha256'));
COMMIT;
