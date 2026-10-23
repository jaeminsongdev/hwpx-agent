-- P09-136: immutable approval/trust metadata. NOT signature verification or production key provisioning.
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version=21 AND migration_name='p09.source_formula_policy_v1')
        OR EXISTS(SELECT 1 FROM hwpx_agent.schema_versions WHERE version>=22) THEN
        RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='FORMULA_ISSUER_REQUIRES_SCHEMA_21';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256',true) IS NULL
        OR current_setting('hwpx_agent.migration_sha256',true) !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='FORMULA_ISSUER_MIGRATION_DIGEST_REQUIRED';
    END IF;
END
$$;

-- Keys and signatures remain inside bounded AEAD Evidence artifacts, not plaintext SQL payloads.
CREATE TABLE hwpx_agent.formula_issuer_trust_versions (
    tenant_id uuid NOT NULL, project_id uuid NOT NULL,
    trust_version_id uuid NOT NULL CHECK(trust_version_id<>'00000000-0000-0000-0000-000000000000'::uuid),
    generation bigint NOT NULL CHECK(generation>0),
    issuer text NOT NULL CHECK(issuer ~ '^[A-Za-z0-9._-]{1,64}$'),
    valid_from bigint NOT NULL CHECK(valid_from>=0),
    valid_until bigint NOT NULL CHECK(valid_until>valid_from),
    max_approval_lifetime bigint NOT NULL CHECK(max_approval_lifetime BETWEEN 1 AND 86400),
    trust_artifact_id uuid NOT NULL,
    trust_artifact_sha256 character(64) NOT NULL CHECK(trust_artifact_sha256 ~ '^[0-9a-f]{64}$'),
    created_by_subject_sha256 character(64) NOT NULL CHECK(created_by_subject_sha256 ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY(tenant_id,project_id,trust_version_id),
    UNIQUE(tenant_id,project_id,generation),
    UNIQUE(tenant_id,project_id,trust_artifact_id),
    FOREIGN KEY(tenant_id,project_id) REFERENCES hwpx_agent.projects ON DELETE RESTRICT,
    FOREIGN KEY(tenant_id,trust_artifact_id) REFERENCES hwpx_agent.artifacts ON DELETE RESTRICT
);
CREATE TABLE hwpx_agent.formula_issuer_trust_revocations (
    tenant_id uuid NOT NULL, project_id uuid NOT NULL, trust_version_id uuid NOT NULL,
    revoked_by_subject_sha256 character(64) NOT NULL CHECK(revoked_by_subject_sha256 ~ '^[0-9a-f]{64}$'),
    revoked_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY(tenant_id,project_id,trust_version_id),
    FOREIGN KEY(tenant_id,project_id,trust_version_id)
        REFERENCES hwpx_agent.formula_issuer_trust_versions ON DELETE RESTRICT
);
CREATE TABLE hwpx_agent.formula_approval_versions (
    tenant_id uuid NOT NULL, project_id uuid NOT NULL, branch_id uuid NOT NULL,
    document_id text NOT NULL CHECK(document_id ~ '^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$'),
    approval_version_id uuid NOT NULL CHECK(approval_version_id<>'00000000-0000-0000-0000-000000000000'::uuid),
    generation bigint NOT NULL CHECK(generation>0),
    policy_version_id uuid NOT NULL, policy_generation bigint NOT NULL CHECK(policy_generation>0),
    trust_version_id uuid NOT NULL, trust_generation bigint NOT NULL CHECK(trust_generation>0),
    approval_artifact_id uuid NOT NULL,
    approval_artifact_sha256 character(64) NOT NULL CHECK(approval_artifact_sha256 ~ '^[0-9a-f]{64}$'),
    created_by_subject_sha256 character(64) NOT NULL CHECK(created_by_subject_sha256 ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY(tenant_id,project_id,approval_version_id),
    UNIQUE(tenant_id,project_id,policy_version_id,generation),
    UNIQUE(tenant_id,project_id,approval_artifact_id),
    FOREIGN KEY(tenant_id,project_id,branch_id) REFERENCES hwpx_agent.branches ON DELETE RESTRICT,
    FOREIGN KEY(tenant_id,project_id,policy_version_id)
        REFERENCES hwpx_agent.source_formula_policy_versions ON DELETE RESTRICT,
    FOREIGN KEY(tenant_id,project_id,trust_version_id)
        REFERENCES hwpx_agent.formula_issuer_trust_versions ON DELETE RESTRICT,
    FOREIGN KEY(tenant_id,approval_artifact_id) REFERENCES hwpx_agent.artifacts ON DELETE RESTRICT
);
CREATE TABLE hwpx_agent.formula_approval_revocations (
    tenant_id uuid NOT NULL, project_id uuid NOT NULL, approval_version_id uuid NOT NULL,
    revoked_by_subject_sha256 character(64) NOT NULL CHECK(revoked_by_subject_sha256 ~ '^[0-9a-f]{64}$'),
    revoked_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY(tenant_id,project_id,approval_version_id),
    FOREIGN KEY(tenant_id,project_id,approval_version_id)
        REFERENCES hwpx_agent.formula_approval_versions ON DELETE RESTRICT
);

ALTER TABLE hwpx_agent.formula_issuer_trust_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.formula_issuer_trust_versions FORCE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.formula_issuer_trust_revocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.formula_issuer_trust_revocations FORCE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.formula_approval_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.formula_approval_versions FORCE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.formula_approval_revocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.formula_approval_revocations FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.formula_issuer_trust_versions
    USING(tenant_id=hwpx_agent.current_tenant_id()) WITH CHECK(tenant_id=hwpx_agent.current_tenant_id());
CREATE POLICY tenant_isolation ON hwpx_agent.formula_issuer_trust_revocations
    USING(tenant_id=hwpx_agent.current_tenant_id()) WITH CHECK(tenant_id=hwpx_agent.current_tenant_id());
CREATE POLICY tenant_isolation ON hwpx_agent.formula_approval_versions
    USING(tenant_id=hwpx_agent.current_tenant_id()) WITH CHECK(tenant_id=hwpx_agent.current_tenant_id());
CREATE POLICY tenant_isolation ON hwpx_agent.formula_approval_revocations
    USING(tenant_id=hwpx_agent.current_tenant_id()) WITH CHECK(tenant_id=hwpx_agent.current_tenant_id());
REVOKE ALL ON hwpx_agent.formula_issuer_trust_versions,hwpx_agent.formula_issuer_trust_revocations,
    hwpx_agent.formula_approval_versions,hwpx_agent.formula_approval_revocations FROM PUBLIC;
CREATE TRIGGER formula_issuer_trust_versions_immutable BEFORE UPDATE OR DELETE
    ON hwpx_agent.formula_issuer_trust_versions FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();
CREATE TRIGGER formula_issuer_trust_revocations_immutable BEFORE UPDATE OR DELETE
    ON hwpx_agent.formula_issuer_trust_revocations FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();
CREATE TRIGGER formula_approval_versions_immutable BEFORE UPDATE OR DELETE
    ON hwpx_agent.formula_approval_versions FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();
CREATE TRIGGER formula_approval_revocations_immutable BEFORE UPDATE OR DELETE
    ON hwpx_agent.formula_approval_revocations FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();

CREATE FUNCTION hwpx_agent.lock_formula_issuer_scope_v1(p_tenant uuid,p_project uuid,p_subject character(64),p_owner boolean)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,hwpx_agent AS $$
BEGIN
    PERFORM hwpx_agent.require_source_formula_policy_role_v1(p_tenant,p_project,p_subject,true);
    IF p_owner IS NULL THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORMULA_ISSUER_SCOPE_DENIED'; END IF;
    PERFORM 1 FROM hwpx_agent.projects WHERE tenant_id=p_tenant AND project_id=p_project FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORMULA_ISSUER_SCOPE_DENIED'; END IF;
    -- After project locking, lock and recheck the active owner/editor membership and tenant.
    PERFORM 1 FROM hwpx_agent.project_acl acl JOIN hwpx_agent.projects project USING(tenant_id,project_id)
        JOIN hwpx_agent.tenants tenant USING(tenant_id)
        WHERE acl.tenant_id=p_tenant AND acl.project_id=p_project AND acl.subject_sha256=p_subject
            AND project.state='active' AND tenant.state='active'
            AND (acl.role='owner' OR (NOT p_owner AND acl.role='editor')) FOR SHARE OF acl,tenant;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORMULA_ISSUER_OWNER_REQUIRED';
    END IF;
END
$$;
CREATE FUNCTION hwpx_agent.require_formula_issuer_owner_v1(p_tenant uuid,p_project uuid,p_subject character(64))
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,hwpx_agent AS $$
BEGIN
    PERFORM hwpx_agent.lock_formula_issuer_scope_v1(p_tenant,p_project,p_subject,true);
END
$$;
CREATE FUNCTION hwpx_agent.require_formula_issuer_artifact_v1(
    p_tenant uuid,p_subject character(64),p_artifact uuid,p_digest character(64),p_trust boolean,p_manage boolean
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,hwpx_agent AS $$
BEGIN
    IF p_trust IS NULL OR p_manage IS NULL OR NOT EXISTS(
        SELECT 1 FROM hwpx_agent.artifacts a JOIN hwpx_agent.artifact_acl acl USING(tenant_id,artifact_id)
        WHERE a.tenant_id=p_tenant AND a.artifact_id=p_artifact AND a.content_sha256=p_digest
            AND a.artifact_kind='evidence' AND a.service_metadata_version=1 AND a.storage_state='available'
            AND a.validation_state='verified' AND a.quarantine_reason_code IS NULL
            AND a.media_type=CASE WHEN p_trust THEN 'application/vnd.hwpx-agent.source-formula-issuer-trust+json'
                ELSE 'application/vnd.hwpx-agent.source-formula-approval+json' END
            AND a.size_bytes BETWEEN 1 AND CASE WHEN p_trust THEN 32768 ELSE 16384 END
            AND acl.subject_sha256=p_subject AND acl.can_read AND (NOT p_manage OR acl.can_manage)
    ) THEN
        RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORMULA_ISSUER_ARTIFACT_UNAVAILABLE';
    END IF;
END
$$;

CREATE FUNCTION hwpx_agent.register_formula_issuer_trust_v1(
    p_tenant uuid,p_project uuid,p_subject character(64),p_version uuid,p_expected_generation bigint,
    p_issuer text,p_valid_from bigint,p_valid_until bigint,p_max_lifetime bigint,p_artifact uuid,p_digest character(64)
) RETURNS bigint LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,hwpx_agent AS $$
DECLARE v_generation bigint;
BEGIN
    PERFORM hwpx_agent.require_formula_issuer_owner_v1(p_tenant,p_project,p_subject);
    -- All SQL22 writers acquire project before branch; root replacement cannot race approval publication.
    PERFORM 1 FROM hwpx_agent.projects WHERE tenant_id=p_tenant AND project_id=p_project FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORMULA_ISSUER_SCOPE_DENIED'; END IF;
    PERFORM hwpx_agent.require_formula_issuer_artifact_v1(p_tenant,p_subject,p_artifact,p_digest,true,true);
    SELECT coalesce(max(generation),0) INTO v_generation FROM hwpx_agent.formula_issuer_trust_versions
        WHERE tenant_id=p_tenant AND project_id=p_project;
    IF v_generation IS DISTINCT FROM p_expected_generation OR v_generation=9223372036854775807 THEN
        RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='FORMULA_ISSUER_GENERATION_CHANGED';
    END IF;
    INSERT INTO hwpx_agent.formula_issuer_trust_versions(tenant_id,project_id,trust_version_id,generation,
        issuer,valid_from,valid_until,max_approval_lifetime,trust_artifact_id,trust_artifact_sha256,created_by_subject_sha256)
    VALUES(p_tenant,p_project,p_version,v_generation+1,p_issuer,p_valid_from,p_valid_until,p_max_lifetime,p_artifact,p_digest,p_subject);
    RETURN v_generation+1;
END
$$;
CREATE FUNCTION hwpx_agent.read_formula_issuer_trust_v1(p_tenant uuid,p_project uuid,p_subject character(64))
RETURNS SETOF hwpx_agent.formula_issuer_trust_versions LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,hwpx_agent AS $$
DECLARE v_trust hwpx_agent.formula_issuer_trust_versions%ROWTYPE; v_now bigint;
BEGIN
    PERFORM hwpx_agent.require_source_formula_policy_role_v1(p_tenant,p_project,p_subject,false);
    SELECT * INTO v_trust FROM hwpx_agent.formula_issuer_trust_versions
        WHERE tenant_id=p_tenant AND project_id=p_project ORDER BY generation DESC LIMIT 1;
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORMULA_ISSUER_TRUST_NOT_CURRENT'; END IF;
    v_now:=floor(extract(epoch FROM clock_timestamp()))::bigint;
    IF v_now<v_trust.valid_from OR v_now>=v_trust.valid_until
        OR EXISTS(SELECT 1 FROM hwpx_agent.formula_issuer_trust_revocations
            WHERE tenant_id=p_tenant AND project_id=p_project AND trust_version_id=v_trust.trust_version_id) THEN
        RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORMULA_ISSUER_TRUST_NOT_CURRENT';
    END IF;
    PERFORM hwpx_agent.require_formula_issuer_artifact_v1(p_tenant,p_subject,v_trust.trust_artifact_id,
        v_trust.trust_artifact_sha256,true,false);
    RETURN NEXT v_trust;
END
$$;
CREATE FUNCTION hwpx_agent.revoke_formula_issuer_trust_v1(
    p_tenant uuid,p_project uuid,p_subject character(64),p_version uuid,p_expected_generation bigint
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,hwpx_agent AS $$
DECLARE v_trust hwpx_agent.formula_issuer_trust_versions%ROWTYPE;
BEGIN
    PERFORM hwpx_agent.require_formula_issuer_owner_v1(p_tenant,p_project,p_subject);
    PERFORM 1 FROM hwpx_agent.projects WHERE tenant_id=p_tenant AND project_id=p_project FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORMULA_ISSUER_SCOPE_DENIED'; END IF;
    SELECT * INTO v_trust FROM hwpx_agent.formula_issuer_trust_versions
        WHERE tenant_id=p_tenant AND project_id=p_project ORDER BY generation DESC LIMIT 1;
    IF NOT FOUND OR ROW(v_trust.trust_version_id,v_trust.generation) IS DISTINCT FROM ROW(p_version,p_expected_generation) THEN
        RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='FORMULA_ISSUER_GENERATION_CHANGED';
    END IF;
    INSERT INTO hwpx_agent.formula_issuer_trust_revocations(tenant_id,project_id,trust_version_id,revoked_by_subject_sha256)
        VALUES(p_tenant,p_project,p_version,p_subject);
END
$$;

CREATE FUNCTION hwpx_agent.register_formula_approval_v1(
    p_tenant uuid,p_project uuid,p_branch uuid,p_subject character(64),p_document text,p_version uuid,
    p_expected_generation bigint,p_policy_version uuid,p_policy_generation bigint,p_revision uuid,p_head_generation bigint,
    p_trust_version uuid,p_trust_generation bigint,p_artifact uuid,p_digest character(64)
) RETURNS bigint LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,hwpx_agent AS $$
DECLARE v_policy hwpx_agent.source_formula_policy_versions%ROWTYPE;
    v_trust hwpx_agent.formula_issuer_trust_versions%ROWTYPE; v_generation bigint;
BEGIN
    PERFORM hwpx_agent.lock_formula_issuer_scope_v1(p_tenant,p_project,p_subject,false);
    PERFORM 1 FROM hwpx_agent.projects WHERE tenant_id=p_tenant AND project_id=p_project FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORMULA_ISSUER_SCOPE_DENIED'; END IF;
    PERFORM 1 FROM hwpx_agent.branches WHERE tenant_id=p_tenant AND project_id=p_project AND branch_id=p_branch FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORMULA_ISSUER_SCOPE_DENIED'; END IF;
    SELECT * INTO v_policy FROM hwpx_agent.read_source_formula_policy_v1(p_tenant,p_project,p_branch,p_subject,p_document,p_revision,p_head_generation);
    IF NOT FOUND OR ROW(v_policy.policy_version_id,v_policy.generation) IS DISTINCT FROM ROW(p_policy_version,p_policy_generation) THEN
        RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='FORMULA_APPROVAL_POLICY_CHANGED';
    END IF;
    SELECT * INTO v_trust FROM hwpx_agent.read_formula_issuer_trust_v1(p_tenant,p_project,p_subject);
    IF NOT FOUND OR ROW(v_trust.trust_version_id,v_trust.generation) IS DISTINCT FROM ROW(p_trust_version,p_trust_generation) THEN
        RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='FORMULA_APPROVAL_TRUST_CHANGED';
    END IF;
    IF p_artifact=v_policy.policy_artifact_id OR p_artifact=v_policy.source_result_artifact_id OR p_artifact=v_trust.trust_artifact_id THEN
        RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORMULA_APPROVAL_ARTIFACT_ALIAS';
    END IF;
    PERFORM hwpx_agent.require_formula_issuer_artifact_v1(p_tenant,p_subject,p_artifact,p_digest,false,true);
    SELECT coalesce(max(generation),0) INTO v_generation FROM hwpx_agent.formula_approval_versions
        WHERE tenant_id=p_tenant AND project_id=p_project AND policy_version_id=p_policy_version;
    IF v_generation IS DISTINCT FROM p_expected_generation OR v_generation=9223372036854775807 THEN
        RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='FORMULA_APPROVAL_GENERATION_CHANGED';
    END IF;
    INSERT INTO hwpx_agent.formula_approval_versions(tenant_id,project_id,branch_id,document_id,approval_version_id,generation,
        policy_version_id,policy_generation,trust_version_id,trust_generation,approval_artifact_id,approval_artifact_sha256,created_by_subject_sha256)
    VALUES(p_tenant,p_project,p_branch,p_document,p_version,v_generation+1,p_policy_version,p_policy_generation,
        p_trust_version,p_trust_generation,p_artifact,p_digest,p_subject);
    RETURN v_generation+1;
END
$$;
CREATE FUNCTION hwpx_agent.read_formula_approval_v1(
    p_tenant uuid,p_project uuid,p_branch uuid,p_subject character(64),p_document text,
    p_revision uuid,p_head_generation bigint,p_policy_version uuid,p_policy_generation bigint
) RETURNS SETOF hwpx_agent.formula_approval_versions LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,hwpx_agent AS $$
DECLARE v_policy hwpx_agent.source_formula_policy_versions%ROWTYPE;
    v_trust hwpx_agent.formula_issuer_trust_versions%ROWTYPE; v_approval hwpx_agent.formula_approval_versions%ROWTYPE;
BEGIN
    SELECT * INTO v_policy FROM hwpx_agent.read_source_formula_policy_v1(p_tenant,p_project,p_branch,p_subject,p_document,p_revision,p_head_generation);
    IF NOT FOUND OR ROW(v_policy.policy_version_id,v_policy.generation) IS DISTINCT FROM ROW(p_policy_version,p_policy_generation) THEN
        RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='FORMULA_APPROVAL_POLICY_CHANGED';
    END IF;
    SELECT * INTO v_trust FROM hwpx_agent.read_formula_issuer_trust_v1(p_tenant,p_project,p_subject);
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORMULA_ISSUER_TRUST_NOT_CURRENT'; END IF;
    SELECT * INTO v_approval FROM hwpx_agent.formula_approval_versions
        WHERE tenant_id=p_tenant AND project_id=p_project AND policy_version_id=p_policy_version
        ORDER BY generation DESC LIMIT 1;
    IF NOT FOUND OR ROW(v_approval.branch_id,v_approval.document_id,v_approval.policy_generation,v_approval.trust_version_id,v_approval.trust_generation)
        IS DISTINCT FROM ROW(p_branch,p_document,p_policy_generation,v_trust.trust_version_id,v_trust.generation)
        OR EXISTS(SELECT 1 FROM hwpx_agent.formula_approval_revocations
            WHERE tenant_id=p_tenant AND project_id=p_project AND approval_version_id=v_approval.approval_version_id)
        OR v_approval.approval_artifact_id IN(v_policy.policy_artifact_id,v_policy.source_result_artifact_id,v_trust.trust_artifact_id) THEN
        RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORMULA_APPROVAL_NOT_CURRENT';
    END IF;
    PERFORM hwpx_agent.require_formula_issuer_artifact_v1(p_tenant,p_subject,v_approval.approval_artifact_id,
        v_approval.approval_artifact_sha256,false,false);
    RETURN NEXT v_approval;
END
$$;
CREATE FUNCTION hwpx_agent.revoke_formula_approval_v1(
    p_tenant uuid,p_project uuid,p_branch uuid,p_subject character(64),p_document text,
    p_policy_version uuid,p_version uuid,p_expected_generation bigint
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,hwpx_agent AS $$
DECLARE v_approval hwpx_agent.formula_approval_versions%ROWTYPE;
BEGIN
    PERFORM hwpx_agent.lock_formula_issuer_scope_v1(p_tenant,p_project,p_subject,false);
    PERFORM 1 FROM hwpx_agent.projects WHERE tenant_id=p_tenant AND project_id=p_project FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORMULA_ISSUER_SCOPE_DENIED'; END IF;
    PERFORM 1 FROM hwpx_agent.branches WHERE tenant_id=p_tenant AND project_id=p_project AND branch_id=p_branch FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORMULA_ISSUER_SCOPE_DENIED'; END IF;
    SELECT * INTO v_approval FROM hwpx_agent.formula_approval_versions
        WHERE tenant_id=p_tenant AND project_id=p_project AND policy_version_id=p_policy_version
        ORDER BY generation DESC LIMIT 1;
    -- Administrative revocation remains possible after source-head movement or root revocation.
    IF NOT FOUND OR ROW(v_approval.branch_id,v_approval.document_id,v_approval.approval_version_id,v_approval.generation)
        IS DISTINCT FROM ROW(p_branch,p_document,p_version,p_expected_generation) THEN
        RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='FORMULA_APPROVAL_GENERATION_CHANGED';
    END IF;
    INSERT INTO hwpx_agent.formula_approval_revocations(tenant_id,project_id,approval_version_id,revoked_by_subject_sha256)
        VALUES(p_tenant,p_project,p_version,p_subject);
END
$$;
REVOKE ALL ON FUNCTION hwpx_agent.lock_formula_issuer_scope_v1(uuid,uuid,character,boolean),
    hwpx_agent.require_formula_issuer_owner_v1(uuid,uuid,character),
    hwpx_agent.require_formula_issuer_artifact_v1(uuid,character,uuid,character,boolean,boolean),
    hwpx_agent.register_formula_issuer_trust_v1(uuid,uuid,character,uuid,bigint,text,bigint,bigint,bigint,uuid,character),
    hwpx_agent.read_formula_issuer_trust_v1(uuid,uuid,character),
    hwpx_agent.revoke_formula_issuer_trust_v1(uuid,uuid,character,uuid,bigint),
    hwpx_agent.register_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint,uuid,bigint,uuid,bigint,uuid,character),
    hwpx_agent.read_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint),
    hwpx_agent.revoke_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,uuid,bigint) FROM PUBLIC;
INSERT INTO hwpx_agent.schema_versions(version,migration_name,migration_sha256)
VALUES(22,'p09.formula_issuer_registry_v1',current_setting('hwpx_agent.migration_sha256'));
COMMIT;
