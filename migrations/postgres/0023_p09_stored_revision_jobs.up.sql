-- Pending runtime qualification. This file does not enable P09 target/product routing.
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version=22 AND migration_name='p09.formula_issuer_registry_v1')
        OR EXISTS(SELECT 1 FROM hwpx_agent.schema_versions WHERE version>=23) THEN
        RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='STORED_REVISION_JOBS_REQUIRE_SCHEMA_22';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256',true) IS NULL
        OR current_setting('hwpx_agent.migration_sha256',true) !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='STORED_REVISION_MIGRATION_DIGEST_REQUIRED';
    END IF;
END
$$;

-- P14's Source-only predicate is deliberately NOT replaced. Only new P09 entry points
-- accept a Result, and only as the sealed expected revision's exact package identity.
CREATE FUNCTION hwpx_agent.stored_revision_source_qualified_v1(
    p_tenant_id uuid, p_project_id uuid, p_branch_id uuid, p_subject_sha256 character(64),
    p_source_artifact_id uuid, p_source_artifact_sha256 character(64),
    p_expected_revision_id uuid, p_expected_generation bigint, p_require_current_head boolean
) RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,hwpx_agent AS $$
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(p_tenant_id,p_project_id,p_subject_sha256);
    IF p_expected_revision_id IS NULL OR p_expected_generation IS NULL OR p_expected_generation<=0
        OR p_require_current_head IS NULL THEN RETURN false; END IF;
    IF p_require_current_head AND NOT hwpx_agent.idempotency_v2_head_matches(
        p_tenant_id,p_project_id,p_branch_id,p_expected_revision_id,p_expected_generation
    ) THEN RETURN false; END IF;
    RETURN EXISTS(
        SELECT 1 FROM hwpx_agent.revisions r
        JOIN hwpx_agent.revision_graph_seals s USING(tenant_id,project_id,revision_id)
        JOIN hwpx_agent.revision_commit_receipts c ON c.tenant_id=r.tenant_id
            AND c.project_id=r.project_id AND c.committed_revision_id=r.revision_id
        JOIN hwpx_agent.artifacts a ON a.tenant_id=r.tenant_id AND a.artifact_id=r.result_artifact_id
        JOIN hwpx_agent.artifact_acl acl ON acl.tenant_id=a.tenant_id AND acl.artifact_id=a.artifact_id
        WHERE r.tenant_id=p_tenant_id AND r.project_id=p_project_id AND r.revision_id=p_expected_revision_id
            AND r.result_artifact_id=p_source_artifact_id AND r.validation_state='verified'
            AND s.seal_kind='service_v1' AND s.committed_generation=p_expected_generation
            AND s.commit_id=c.commit_id AND s.commit_request_sha256=c.commit_request_sha256
            AND s.transaction_receipt_sha256=c.transaction_receipt_sha256
            AND c.committed_generation=s.committed_generation
            AND c.subject_sha256=r.created_by_subject_sha256
            AND s.parent_count=(SELECT count(*) FROM hwpx_agent.revision_parents p
                WHERE p.tenant_id=r.tenant_id AND p.project_id=r.project_id AND p.revision_id=r.revision_id)
            AND a.service_metadata_version=1 AND a.artifact_kind='result'
            AND a.media_type='application/vnd.hancom.hwpx+zip' AND a.size_bytes BETWEEN 1 AND 33554432
            AND a.content_sha256=p_source_artifact_sha256 AND a.storage_state='available'
            AND a.validation_state='verified' AND a.quarantine_reason_code IS NULL
            AND acl.subject_sha256=p_subject_sha256 AND (acl.can_read OR acl.can_manage)
    );
END
$$;

-- Typed authority and immutable handles only. Encrypted Receipt bodies remain in ArtifactService.
CREATE TABLE hwpx_agent.stored_revision_commit_intents (
    tenant_id uuid NOT NULL, project_id uuid NOT NULL, idempotency_key uuid NOT NULL,
    job_id uuid NOT NULL, attempt_no integer NOT NULL, fencing_token bigint NOT NULL,
    subject_sha256 character(64) NOT NULL, agent_instance_id uuid NOT NULL, execution_id uuid NOT NULL,
    authorization_id uuid NOT NULL, commit_id uuid NOT NULL, new_revision_id uuid NOT NULL,
    result_artifact_id uuid NOT NULL, validation_summary_sha256 character(64) NOT NULL,
    commit_request_sha256 character(64) NOT NULL, intent_artifact_id uuid NOT NULL,
    intent_sha256 character(64) NOT NULL, precommit_artifact_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY(tenant_id,project_id,job_id,attempt_no),
    UNIQUE(tenant_id,project_id,idempotency_key,attempt_no),
    FOREIGN KEY(tenant_id,project_id,idempotency_key) REFERENCES hwpx_agent.idempotency_records ON DELETE RESTRICT,
    FOREIGN KEY(tenant_id,project_id,job_id,attempt_no) REFERENCES hwpx_agent.job_attempts ON DELETE RESTRICT,
    FOREIGN KEY(tenant_id,result_artifact_id) REFERENCES hwpx_agent.artifacts ON DELETE RESTRICT,
    FOREIGN KEY(tenant_id,intent_artifact_id) REFERENCES hwpx_agent.artifacts ON DELETE RESTRICT,
    FOREIGN KEY(tenant_id,precommit_artifact_id) REFERENCES hwpx_agent.artifacts ON DELETE RESTRICT,
    CHECK(attempt_no BETWEEN 1 AND 10 AND fencing_token=attempt_no),
    CHECK(subject_sha256 ~ '^[0-9a-f]{64}$' AND validation_summary_sha256 ~ '^[0-9a-f]{64}$'
        AND commit_request_sha256 ~ '^[0-9a-f]{64}$' AND intent_sha256 ~ '^[0-9a-f]{64}$'),
    CHECK(result_artifact_id<>intent_artifact_id AND result_artifact_id<>precommit_artifact_id
        AND intent_artifact_id<>precommit_artifact_id),
    CHECK(array_position(ARRAY[tenant_id,project_id,idempotency_key,job_id,agent_instance_id,execution_id,
        authorization_id,commit_id,new_revision_id,result_artifact_id,intent_artifact_id,precommit_artifact_id],
        '00000000-0000-0000-0000-000000000000'::uuid) IS NULL)
);
ALTER TABLE hwpx_agent.stored_revision_commit_intents ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.stored_revision_commit_intents FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.stored_revision_commit_intents
    USING(tenant_id=hwpx_agent.current_tenant_id()) WITH CHECK(tenant_id=hwpx_agent.current_tenant_id());
REVOKE ALL ON TABLE hwpx_agent.stored_revision_commit_intents FROM PUBLIC;
CREATE TRIGGER stored_revision_commit_intents_immutable BEFORE UPDATE OR DELETE
    ON hwpx_agent.stored_revision_commit_intents FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();

CREATE FUNCTION hwpx_agent.require_stored_commit_receipt_v1(
    p_tenant uuid,p_subject character(64),p_artifact uuid,p_sha character(64)
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,hwpx_agent AS $$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM hwpx_agent.artifacts a JOIN hwpx_agent.artifact_acl acl USING(tenant_id,artifact_id)
        WHERE a.tenant_id=p_tenant AND a.artifact_id=p_artifact AND a.content_sha256=p_sha
            AND a.service_metadata_version=1 AND a.artifact_kind='receipt' AND a.media_type='application/json'
            AND a.size_bytes BETWEEN 1 AND 65536 AND a.storage_state='available' AND a.validation_state='verified'
            AND a.quarantine_reason_code IS NULL AND acl.subject_sha256=p_subject AND (acl.can_read OR acl.can_manage)) THEN
        RAISE EXCEPTION USING ERRCODE='23503',MESSAGE='STORED_COMMIT_RECEIPT_NOT_QUALIFIED';
    END IF;
END
$$;

CREATE FUNCTION hwpx_agent.register_stored_revision_commit_intent_v1(
    p_tenant uuid,p_project uuid,p_subject character(64),p_key uuid,p_job uuid,p_agent uuid,p_execution uuid,
    p_attempt integer,p_fence bigint,p_authorization uuid,p_commit uuid,p_revision uuid,p_result uuid,
    p_summary character(64),p_request character(64),p_intent uuid,p_intent_sha character(64),p_precommit uuid
) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,hwpx_agent AS $$
DECLARE
    r hwpx_agent.idempotency_records%ROWTYPE;
    j hwpx_agent.jobs%ROWTYPE;
    old hwpx_agent.stored_revision_commit_intents%ROWTYPE;
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(p_tenant,p_project,p_subject);
    IF array_position(ARRAY[p_key,p_job,p_agent,p_execution,p_authorization,p_commit,p_revision,p_result,p_intent,p_precommit],NULL) IS NOT NULL
        OR p_attempt IS NULL OR p_fence IS NULL OR p_attempt NOT BETWEEN 1 AND 10 OR p_fence<>p_attempt
        OR p_summary IS NULL OR p_request IS NULL OR p_intent_sha IS NULL
        OR p_summary !~ '^[0-9a-f]{64}$' OR p_request !~ '^[0-9a-f]{64}$' OR p_intent_sha !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='STORED_COMMIT_INTENT_REQUEST_INVALID';
    END IF;
    SELECT * INTO r FROM hwpx_agent.idempotency_records
        WHERE tenant_id=p_tenant AND project_id=p_project AND idempotency_key=p_key FOR UPDATE;
    SELECT * INTO j FROM hwpx_agent.jobs WHERE tenant_id=p_tenant AND project_id=p_project AND job_id=p_job FOR UPDATE;
    IF r.record_version IS DISTINCT FROM 2 OR r.state IS DISTINCT FROM 'in_progress'
        OR r.job_id IS DISTINCT FROM p_job OR r.subject_sha256 IS DISTINCT FROM p_subject
        OR j.state_machine_version IS DISTINCT FROM 2 OR j.state IS DISTINCT FROM 'validating'
        OR ROW(j.lease_owner_agent_id,j.active_execution_id,j.attempt_count,j.fencing_token)
            IS DISTINCT FROM ROW(p_agent,p_execution,p_attempt,p_fence)
        OR j.lease_expires_at IS NULL OR j.lease_expires_at<=clock_timestamp()
        OR r.expires_at<=clock_timestamp() THEN
        RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='STORED_COMMIT_INTENT_LEASE_MISMATCH';
    END IF;
    PERFORM 1 FROM hwpx_agent.idempotency_commit_authorizations a
        WHERE a.tenant_id=p_tenant AND a.project_id=p_project AND a.idempotency_key=p_key AND a.job_id=p_job
            AND a.agent_instance_id=p_agent AND a.execution_id=p_execution AND a.attempt_no=p_attempt
            AND a.fencing_token=p_fence AND a.commit_authorization_id=p_authorization
            AND a.transaction_receipt_sha256=r.transaction_receipt_sha256 FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='STORED_COMMIT_INTENT_AUTHORIZATION_REQUIRED'; END IF;
    IF NOT hwpx_agent.stored_revision_source_qualified_v1(p_tenant,p_project,r.branch_id,p_subject,
        r.source_artifact_id,r.source_artifact_sha256,r.expected_revision_id,r.expected_revision_generation,true) THEN
        RAISE EXCEPTION USING ERRCODE='23503',MESSAGE='STORED_COMMIT_SOURCE_NOT_QUALIFIED';
    END IF;
    IF NOT EXISTS(SELECT 1 FROM hwpx_agent.artifacts a JOIN hwpx_agent.artifact_acl acl USING(tenant_id,artifact_id)
        WHERE a.tenant_id=p_tenant AND a.artifact_id=p_result AND a.content_sha256=r.expected_effect_sha256
            AND a.artifact_id<>r.source_artifact_id AND a.artifact_kind='result' AND a.service_metadata_version=1
            AND a.media_type='application/vnd.hancom.hwpx+zip' AND a.size_bytes BETWEEN 1 AND 33554432
            AND a.storage_state='available' AND a.validation_state='verified' AND a.quarantine_reason_code IS NULL
            AND acl.subject_sha256=p_subject AND (acl.can_read OR acl.can_manage)) THEN
        RAISE EXCEPTION USING ERRCODE='23503',MESSAGE='STORED_COMMIT_RESULT_NOT_QUALIFIED';
    END IF;
    PERFORM hwpx_agent.require_stored_commit_receipt_v1(p_tenant,p_subject,p_intent,p_intent_sha);
    -- The precommit receipt hash is NOT the larger intent-envelope hash.
    PERFORM hwpx_agent.require_stored_commit_receipt_v1(p_tenant,p_subject,p_precommit,r.transaction_receipt_sha256);
    SELECT * INTO old FROM hwpx_agent.stored_revision_commit_intents
        WHERE tenant_id=p_tenant AND project_id=p_project AND job_id=p_job AND attempt_no=p_attempt;
    IF FOUND THEN
        IF ROW(old.idempotency_key,old.subject_sha256,old.agent_instance_id,old.execution_id,old.fencing_token,
            old.authorization_id,old.commit_id,old.new_revision_id,old.result_artifact_id,old.validation_summary_sha256,
            old.commit_request_sha256,old.intent_artifact_id,old.intent_sha256,old.precommit_artifact_id)
            IS DISTINCT FROM ROW(p_key,p_subject,p_agent,p_execution,p_fence,p_authorization,p_commit,p_revision,p_result,
                p_summary,p_request,p_intent,p_intent_sha,p_precommit) THEN
            RAISE EXCEPTION USING ERRCODE='23505',MESSAGE='STORED_COMMIT_INTENT_CONFLICT';
        END IF;
        RETURN old.intent_artifact_id;
    END IF;
    INSERT INTO hwpx_agent.stored_revision_commit_intents(tenant_id,project_id,idempotency_key,job_id,attempt_no,
        fencing_token,subject_sha256,agent_instance_id,execution_id,authorization_id,commit_id,new_revision_id,
        result_artifact_id,validation_summary_sha256,commit_request_sha256,intent_artifact_id,intent_sha256,precommit_artifact_id)
        VALUES(p_tenant,p_project,p_key,p_job,p_attempt,p_fence,p_subject,p_agent,p_execution,p_authorization,p_commit,p_revision,
            p_result,p_summary,p_request,p_intent,p_intent_sha,p_precommit);
    RETURN p_intent;
END
$$;

CREATE FUNCTION hwpx_agent.read_stored_revision_commit_intent_v1(
    p_tenant uuid,p_project uuid,p_subject character(64),p_key uuid,p_job uuid,p_attempt integer
) RETURNS SETOF hwpx_agent.stored_revision_commit_intents LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,hwpx_agent AS $$
DECLARE i hwpx_agent.stored_revision_commit_intents%ROWTYPE;
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(p_tenant,p_project,p_subject);
    SELECT * INTO i FROM hwpx_agent.stored_revision_commit_intents
        WHERE tenant_id=p_tenant AND project_id=p_project AND subject_sha256=p_subject
            AND idempotency_key=p_key AND job_id=p_job AND attempt_no=p_attempt;
    IF NOT FOUND THEN RETURN; END IF;
    -- Historical observation: no current lease/head requirement, no retry authorization.
    PERFORM hwpx_agent.require_stored_commit_receipt_v1(p_tenant,p_subject,i.intent_artifact_id,i.intent_sha256);
    RETURN NEXT i;
END
$$;

CREATE FUNCTION hwpx_agent.guard_stored_revision_commit_intent_v1()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,hwpx_agent AS $$
DECLARE r hwpx_agent.idempotency_records%ROWTYPE;
BEGIN
    SELECT record.* INTO r FROM hwpx_agent.idempotency_records record
        JOIN hwpx_agent.artifacts a ON a.tenant_id=record.tenant_id AND a.artifact_id=record.source_artifact_id
        WHERE record.tenant_id=NEW.tenant_id AND record.project_id=NEW.project_id
            AND record.record_version=2 AND record.transaction_receipt_sha256=NEW.transaction_receipt_sha256
            AND a.artifact_kind='result';
    IF NOT FOUND THEN RETURN NEW; END IF; -- Legacy P14 Source jobs retain their original rules.
    IF NOT EXISTS(SELECT 1 FROM hwpx_agent.stored_revision_commit_intents i
        JOIN hwpx_agent.jobs j USING(tenant_id,project_id,job_id)
        JOIN hwpx_agent.revisions v ON v.tenant_id=i.tenant_id AND v.project_id=i.project_id
            AND v.revision_id=i.new_revision_id
        WHERE i.tenant_id=NEW.tenant_id AND i.project_id=NEW.project_id AND i.job_id=r.job_id
            AND i.idempotency_key=r.idempotency_key AND i.subject_sha256=NEW.subject_sha256
            AND i.attempt_no=j.attempt_count AND i.fencing_token=j.fencing_token
            AND i.agent_instance_id=j.lease_owner_agent_id AND i.execution_id=j.active_execution_id
            AND i.authorization_id::text=current_setting('hwpx_agent.commit_authorization_id',true)
            AND i.commit_id=NEW.commit_id AND i.new_revision_id=NEW.committed_revision_id
            AND i.result_artifact_id=v.result_artifact_id AND i.validation_summary_sha256=v.validation_summary_sha256
            AND i.commit_request_sha256=NEW.commit_request_sha256) THEN
        RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='STORED_COMMIT_INTENT_REQUIRED';
    END IF;
    RETURN NEW;
END
$$;
CREATE TRIGGER revision_commit_receipts_stored_intent_guard BEFORE INSERT
    ON hwpx_agent.revision_commit_receipts FOR EACH ROW EXECUTE FUNCTION hwpx_agent.guard_stored_revision_commit_intent_v1();

-- BEGIN_FROZEN_V2_DERIVATIONS
CREATE FUNCTION hwpx_agent.stored_revision_committed_effect_qualified_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_branch_id uuid,
    p_subject_sha256 character(64),
    p_source_artifact_id uuid,
    p_source_artifact_sha256 character(64),
    p_expected_revision_id uuid,
    p_expected_generation bigint,
    p_operation_plan_sha256 character(64),
    p_result_revision_id uuid,
    p_expected_effect_sha256 character(64),
    p_transaction_receipt_sha256 character(64),
    p_receipt_artifact_id uuid
)
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
    SELECT
        hwpx_agent.idempotency_v2_head_matches(
            p_tenant_id, p_project_id, p_branch_id,
            p_result_revision_id, p_expected_generation + 1
        )
        AND hwpx_agent.stored_revision_source_qualified_v1(
        p_tenant_id, p_project_id, p_branch_id, p_subject_sha256, p_source_artifact_id, p_source_artifact_sha256,
        p_expected_revision_id, p_expected_generation, false
    )
        AND hwpx_agent.idempotency_v2_artifact_qualified(
            p_tenant_id, p_subject_sha256, p_receipt_artifact_id,
            'receipt', p_transaction_receipt_sha256
        )
        AND EXISTS (
            SELECT 1
            FROM hwpx_agent.revisions AS revision
            JOIN hwpx_agent.artifacts AS result_artifact
              ON result_artifact.tenant_id = revision.tenant_id
             AND result_artifact.artifact_id = revision.result_artifact_id
            JOIN hwpx_agent.artifact_acl AS result_acl
              ON result_acl.tenant_id = result_artifact.tenant_id
             AND result_acl.artifact_id = result_artifact.artifact_id
            JOIN hwpx_agent.revision_graph_seals AS seal
              ON seal.tenant_id = revision.tenant_id
             AND seal.project_id = revision.project_id
             AND seal.revision_id = revision.revision_id
            JOIN hwpx_agent.revision_commit_receipts AS commit_receipt
              ON commit_receipt.tenant_id = revision.tenant_id
             AND commit_receipt.project_id = revision.project_id
             AND commit_receipt.committed_revision_id = revision.revision_id
            WHERE revision.tenant_id = p_tenant_id
              AND revision.project_id = p_project_id
              AND revision.revision_id = p_result_revision_id
              AND revision.source_artifact_id = p_source_artifact_id
              AND revision.operation_plan_sha256 = p_operation_plan_sha256
              AND revision.validation_state = 'verified'
              AND revision.created_by_subject_sha256 = p_subject_sha256
              AND result_artifact.service_metadata_version = 1
              AND result_artifact.storage_state = 'available'
              AND result_artifact.validation_state = 'verified'
              AND result_artifact.artifact_kind = 'result'
              AND result_artifact.content_sha256 = p_expected_effect_sha256
              AND result_acl.subject_sha256 = p_subject_sha256
              AND (result_acl.can_read OR result_acl.can_manage)
              AND seal.seal_kind = 'service_v1'
              AND seal.committed_generation = p_expected_generation + 1
              AND seal.transaction_receipt_sha256 = p_transaction_receipt_sha256
              AND seal.commit_id = commit_receipt.commit_id
              AND seal.commit_request_sha256 = commit_receipt.commit_request_sha256
              AND commit_receipt.branch_id = p_branch_id
              AND commit_receipt.previous_revision_id IS NOT DISTINCT FROM p_expected_revision_id
              AND commit_receipt.expected_generation = p_expected_generation
              AND commit_receipt.committed_generation = p_expected_generation + 1
              AND commit_receipt.transaction_receipt_sha256 = p_transaction_receipt_sha256
              AND commit_receipt.subject_sha256 = p_subject_sha256
        )
$$;

CREATE FUNCTION hwpx_agent.claim_stored_revision_job_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_branch_id uuid,
    p_subject_sha256 character(64),
    p_idempotency_key uuid,
    p_job_id uuid,
    p_request_id uuid,
    p_source_artifact_id uuid,
    p_expected_revision_id uuid,
    p_expected_revision_generation bigint,
    p_request_sha256 character(64),
    p_execution_manifest_sha256 character(64),
    p_source_artifact_sha256 character(64),
    p_expected_effect_sha256 character(64),
    p_transaction_receipt_sha256 character(64),
    p_operation_plan_sha256 character(64),
    p_required_target_profile_id text,
    p_required_capability_set_sha256 character(64),
    p_max_attempts integer,
    p_base_delay_seconds integer,
    p_max_delay_seconds integer,
    p_ttl_seconds integer,
    p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_outcome text, returned_job_id uuid, returned_state text,
    returned_attempt_count integer, returned_fencing_token bigint,
    returned_retry_not_before timestamptz, returned_result_revision_id uuid,
    returned_terminal_error_code text, returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_record hwpx_agent.idempotency_records%ROWTYPE;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_head_revision_id uuid;
    v_head_generation bigint;
    v_now timestamptz := transaction_timestamp();
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(
        p_tenant_id, p_project_id, p_subject_sha256
    );
    IF p_branch_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_idempotency_key = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_job_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_request_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_source_artifact_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_request_sha256 !~ '^[0-9a-f]{64}$'
       OR p_execution_manifest_sha256 !~ '^[0-9a-f]{64}$'
       OR p_source_artifact_sha256 !~ '^[0-9a-f]{64}$'
       OR p_expected_effect_sha256 !~ '^[0-9a-f]{64}$'
       OR p_transaction_receipt_sha256 !~ '^[0-9a-f]{64}$'
       OR p_operation_plan_sha256 !~ '^[0-9a-f]{64}$'
       OR p_required_capability_set_sha256 !~ '^[0-9a-f]{64}$'
       OR p_required_target_profile_id !~ '^[A-Za-z0-9][A-Za-z0-9._-]{1,126}$'
       OR p_max_attempts NOT BETWEEN 1 AND 10
       OR p_base_delay_seconds NOT BETWEEN 1 AND 86400
       OR p_max_delay_seconds NOT BETWEEN p_base_delay_seconds AND 86400
       OR p_ttl_seconds NOT BETWEEN 60 AND 604800
       OR p_event_sha256 !~ '^[0-9a-f]{64}$'
       OR (p_expected_revision_id IS NULL AND p_expected_revision_generation <> 0)
       OR (p_expected_revision_id IS NOT NULL AND p_expected_revision_generation <= 0) THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'IDEMPOTENCY_CLAIM_REQUEST_INVALID';
    END IF;

    PERFORM pg_advisory_xact_lock(hashtextextended(
        concat(p_tenant_id::text, '/', p_project_id::text, '/', p_idempotency_key::text), 0
    ));
    SELECT * INTO v_record FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = p_tenant_id AND record.project_id = p_project_id
      AND record.idempotency_key = p_idempotency_key
    FOR UPDATE;
    IF FOUND THEN
        SELECT * INTO v_job FROM hwpx_agent.jobs AS job
        WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
          AND job.job_id = v_record.job_id;
        IF v_record.record_version <> 2 OR v_job.state_machine_version IS DISTINCT FROM 2
           OR ROW(
                v_record.subject_sha256, v_record.branch_id, v_record.job_id,
                v_record.request_id, v_record.source_artifact_id,
                v_record.expected_revision_id, v_record.expected_revision_generation,
                v_record.request_sha256, v_record.execution_manifest_sha256,
                v_record.source_artifact_sha256, v_record.expected_effect_sha256,
                v_record.transaction_receipt_sha256, v_record.max_attempts,
                v_record.base_delay_seconds, v_record.max_delay_seconds,
                extract(epoch FROM (v_record.expires_at - v_record.created_at))::integer
           ) IS DISTINCT FROM ROW(
                p_subject_sha256, p_branch_id, p_job_id, p_request_id,
                p_source_artifact_id, p_expected_revision_id,
                p_expected_revision_generation, p_request_sha256,
                p_execution_manifest_sha256, p_source_artifact_sha256,
                p_expected_effect_sha256, p_transaction_receipt_sha256,
                p_max_attempts, p_base_delay_seconds, p_max_delay_seconds, p_ttl_seconds
           )
           OR ROW(
                v_job.request_id, v_job.input_artifact_id, v_job.expected_revision_id,
                v_job.operation_plan_sha256, v_job.required_target_profile_id,
                v_job.required_capability_set_sha256
           ) IS DISTINCT FROM ROW(
                p_request_id, p_source_artifact_id, p_expected_revision_id,
                p_operation_plan_sha256, p_required_target_profile_id,
                p_required_capability_set_sha256
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23505', MESSAGE = 'IDEMPOTENCY_KEY_CONFLICT';
        END IF;
        IF NOT hwpx_agent.stored_revision_source_qualified_v1(
            p_tenant_id,p_project_id,p_branch_id,p_subject_sha256,p_source_artifact_id,
            p_source_artifact_sha256,p_expected_revision_id,p_expected_revision_generation,false
        ) THEN
            RAISE EXCEPTION USING ERRCODE='23503',MESSAGE='STORED_REVISION_REPLAY_SOURCE_NOT_QUALIFIED';
        END IF;
        RETURN QUERY SELECT 'replay'::text, v_record.job_id, v_record.state,
            v_record.attempt_count, v_record.last_fencing_token,
            v_record.retry_not_before, v_record.result_revision_id,
            v_record.terminal_error_code, v_record.receipt_artifact_id;
        RETURN;
    END IF;

    SELECT branch.head_revision_id, branch.head_generation
    INTO v_head_revision_id, v_head_generation
    FROM hwpx_agent.branches AS branch
    WHERE branch.tenant_id = p_tenant_id AND branch.project_id = p_project_id
      AND branch.branch_id = p_branch_id
    FOR UPDATE;
    IF NOT FOUND OR ROW(v_head_revision_id, v_head_generation)
       IS DISTINCT FROM ROW(p_expected_revision_id, p_expected_revision_generation)
       OR v_head_generation < 0 THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_HEAD_CONFLICT';
    END IF;
    IF NOT hwpx_agent.stored_revision_source_qualified_v1(
        p_tenant_id, p_project_id, p_branch_id, p_subject_sha256, p_source_artifact_id, p_source_artifact_sha256,
        p_expected_revision_id, p_expected_revision_generation, true
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'IDEMPOTENCY_SOURCE_NOT_QUALIFIED';
    END IF;

    BEGIN
        INSERT INTO hwpx_agent.jobs (
            tenant_id, project_id, job_id, request_id, input_artifact_id,
            expected_revision_id, operation_plan_sha256, required_target_profile_id,
            required_capability_set_sha256, state, attempt_count, fencing_token,
            state_machine_version
        ) VALUES (
            p_tenant_id, p_project_id, p_job_id, p_request_id, p_source_artifact_id,
            p_expected_revision_id, p_operation_plan_sha256, p_required_target_profile_id,
            p_required_capability_set_sha256, 'queued', 0, 0, 2
        );
    EXCEPTION
        WHEN unique_violation THEN
            RAISE EXCEPTION USING
                ERRCODE = '23505', MESSAGE = 'IDEMPOTENCY_IDENTITY_ALREADY_EXISTS';
    END;
    INSERT INTO hwpx_agent.idempotency_records (
        tenant_id, project_id, idempotency_key, request_sha256, state, job_id,
        created_at, updated_at, expires_at, record_version, subject_sha256,
        branch_id, request_id, source_artifact_id, expected_revision_id,
        expected_revision_generation, execution_manifest_sha256,
        source_artifact_sha256, expected_effect_sha256,
        transaction_receipt_sha256, max_attempts, base_delay_seconds,
        max_delay_seconds, attempt_count, last_fencing_token
    ) VALUES (
        p_tenant_id, p_project_id, p_idempotency_key, p_request_sha256,
        'claimed', p_job_id, v_now, v_now,
        v_now + make_interval(secs => p_ttl_seconds), 2, p_subject_sha256,
        p_branch_id, p_request_id, p_source_artifact_id, p_expected_revision_id,
        p_expected_revision_generation, p_execution_manifest_sha256,
        p_source_artifact_sha256, p_expected_effect_sha256,
        p_transaction_receipt_sha256, p_max_attempts, p_base_delay_seconds,
        p_max_delay_seconds, 0, 0
    );
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'idempotency.v2_claimed',
        p_subject_sha256, p_job_id, p_event_sha256
    );
    RETURN QUERY SELECT 'new'::text, p_job_id, 'claimed'::text,
        0, 0::bigint, NULL::timestamptz, NULL::uuid, NULL::text, NULL::uuid;
END
$$;

CREATE FUNCTION hwpx_agent.lease_stored_revision_job_v1(
    p_tenant_id uuid, p_project_id uuid, p_subject_sha256 character(64),
    p_idempotency_key uuid, p_job_id uuid, p_agent_instance_id uuid,
    p_execution_id uuid, p_lease_seconds integer, p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_outcome text, returned_job_id uuid, returned_state text,
    returned_attempt_count integer, returned_fencing_token bigint,
    returned_retry_not_before timestamptz, returned_result_revision_id uuid,
    returned_terminal_error_code text, returned_receipt_artifact_id uuid,
    returned_commit_authorization_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_record hwpx_agent.idempotency_records%ROWTYPE;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_worker hwpx_agent.worker_registrations%ROWTYPE;
    v_attempt integer;
    v_commit_authorization_id uuid := gen_random_uuid();
    v_now timestamptz := clock_timestamp();
    v_expires timestamptz;
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(p_tenant_id, p_project_id, p_subject_sha256);
    IF p_job_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_agent_instance_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_execution_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_lease_seconds NOT BETWEEN 1 AND 3600
       OR p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'IDEMPOTENCY_LEASE_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_record FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = p_tenant_id AND record.project_id = p_project_id
      AND record.idempotency_key = p_idempotency_key FOR UPDATE;
    IF NOT FOUND OR v_record.record_version <> 2 OR v_record.job_id <> p_job_id
       OR v_record.subject_sha256 <> p_subject_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'IDEMPOTENCY_RECORD_NOT_FOUND';
    END IF;
    SELECT * INTO v_job FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
      AND job.job_id = p_job_id FOR UPDATE;
    IF NOT FOUND OR v_job.state_machine_version IS DISTINCT FROM 2
       OR (v_record.state = 'claimed' AND v_job.state <> 'queued')
       OR (v_record.state = 'retry_pending' AND v_job.state <> 'retry_pending')
       OR v_record.state NOT IN ('claimed', 'retry_pending') THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_LEASE_STATE_INVALID';
    END IF;
    IF v_record.expires_at <= v_now THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_EXPIRED';
    END IF;
    IF v_record.retry_not_before IS NOT NULL AND v_record.retry_not_before > v_now THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_RETRY_NOT_READY';
    END IF;
    IF v_record.attempt_count >= v_record.max_attempts THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_RETRY_EXHAUSTED';
    END IF;
    IF NOT hwpx_agent.stored_revision_source_qualified_v1(
        p_tenant_id, p_project_id, v_record.branch_id, p_subject_sha256, v_record.source_artifact_id, v_record.source_artifact_sha256,
        v_record.expected_revision_id, v_record.expected_revision_generation, true
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'IDEMPOTENCY_SOURCE_NOT_QUALIFIED';
    END IF;
    SELECT * INTO v_worker FROM hwpx_agent.worker_registrations AS worker
    WHERE worker.tenant_id = p_tenant_id
      AND worker.agent_instance_id = p_agent_instance_id FOR UPDATE;
    v_expires := v_now + make_interval(secs => p_lease_seconds);
    IF NOT FOUND OR v_worker.subject_sha256 <> p_subject_sha256
       OR v_worker.target_profile_id <> v_job.required_target_profile_id
       OR v_worker.capability_set_sha256 <> v_job.required_capability_set_sha256
       OR v_worker.state <> 'ready' OR v_worker.last_heartbeat_at > v_now
       OR v_worker.expires_at <= v_now OR v_expires > v_worker.expires_at
       OR v_expires > v_record.expires_at THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'JOB_WORKER_NOT_QUALIFIED';
    END IF;
    v_attempt := v_record.attempt_count + 1;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'on', true);
    UPDATE hwpx_agent.jobs SET
        state = 'leased', attempt_count = v_attempt,
        lease_owner_agent_id = p_agent_instance_id, active_execution_id = p_execution_id,
        fencing_token = v_attempt, lease_issued_at = v_now,
        lease_expires_at = v_expires, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    INSERT INTO hwpx_agent.job_attempts (
        tenant_id, project_id, job_id, attempt_no, execution_id,
        agent_instance_id, fencing_token, state, started_at,
        state_machine_version, lease_expires_at, updated_at
    ) VALUES (
        p_tenant_id, p_project_id, p_job_id, v_attempt, p_execution_id,
        p_agent_instance_id, v_attempt, 'leased', v_now, 2, v_expires, v_now
    );
    INSERT INTO hwpx_agent.idempotency_commit_authorizations (
        tenant_id, project_id, idempotency_key, job_id,
        agent_instance_id, execution_id, attempt_no, fencing_token,
        commit_authorization_id, transaction_receipt_sha256, created_backend_pid,
        created_transaction_id, created_at
    ) VALUES (
        p_tenant_id, p_project_id, p_idempotency_key, p_job_id,
        p_agent_instance_id, p_execution_id, v_attempt, v_attempt,
        v_commit_authorization_id, v_record.transaction_receipt_sha256, pg_backend_pid(),
        pg_current_xact_id(), v_now
    );
    UPDATE hwpx_agent.idempotency_records SET
        state = 'in_progress', attempt_count = v_attempt,
        last_fencing_token = v_attempt, retry_not_before = NULL,
        receipt_artifact_id = NULL, terminal_error_code = NULL,
        updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND idempotency_key = p_idempotency_key;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'off', true);
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'idempotency.v2_leased',
        p_subject_sha256, p_job_id, p_event_sha256
    );
    RETURN QUERY SELECT 'leased'::text, p_job_id, 'in_progress'::text,
        v_attempt, v_attempt::bigint, NULL::timestamptz,
        NULL::uuid, NULL::text, NULL::uuid, v_commit_authorization_id;
END
$$;

CREATE FUNCTION hwpx_agent.schedule_stored_revision_retry_v1(
    p_tenant_id uuid, p_project_id uuid, p_subject_sha256 character(64),
    p_idempotency_key uuid, p_job_id uuid, p_agent_instance_id uuid,
    p_execution_id uuid, p_attempt_no integer, p_fencing_token bigint,
    p_retry_class text, p_receipt_artifact_id uuid, p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_outcome text, returned_job_id uuid, returned_state text,
    returned_attempt_count integer, returned_fencing_token bigint,
    returned_retry_not_before timestamptz, returned_result_revision_id uuid,
    returned_terminal_error_code text, returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_record hwpx_agent.idempotency_records%ROWTYPE;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_attempt_state text;
    v_now timestamptz := clock_timestamp();
    v_retry_at timestamptz;
    v_terminal boolean;
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(p_tenant_id, p_project_id, p_subject_sha256);
    IF p_retry_class NOT IN ('transient_storage', 'transient_network')
       OR p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'IDEMPOTENCY_RETRY_CLASS_INVALID';
    END IF;
    SELECT * INTO v_record FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = p_tenant_id AND record.project_id = p_project_id
      AND record.idempotency_key = p_idempotency_key FOR UPDATE;
    SELECT * INTO v_job FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
      AND job.job_id = p_job_id FOR UPDATE;
    IF v_record.record_version IS DISTINCT FROM 2 OR v_record.state <> 'in_progress'
       OR v_record.job_id <> p_job_id OR v_record.subject_sha256 <> p_subject_sha256
       OR v_job.state_machine_version IS DISTINCT FROM 2
       OR v_job.state NOT IN ('leased', 'staged', 'executing', 'validating')
       OR ROW(v_job.lease_owner_agent_id, v_job.active_execution_id,
              v_job.attempt_count, v_job.fencing_token)
          IS DISTINCT FROM ROW(p_agent_instance_id, p_execution_id,
                               p_attempt_no, p_fencing_token)
       OR v_job.lease_expires_at <= v_now THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_LEASE_MISMATCH';
    END IF;
    IF NOT hwpx_agent.idempotency_v2_artifact_qualified(
        p_tenant_id, p_subject_sha256, p_receipt_artifact_id, 'receipt',
        (SELECT content_sha256 FROM hwpx_agent.artifacts
         WHERE tenant_id = p_tenant_id AND artifact_id = p_receipt_artifact_id)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'IDEMPOTENCY_RECEIPT_NOT_QUALIFIED';
    END IF;
    IF NOT hwpx_agent.stored_revision_source_qualified_v1(
        p_tenant_id, p_project_id, v_record.branch_id, p_subject_sha256, v_record.source_artifact_id, v_record.source_artifact_sha256,
        v_record.expected_revision_id, v_record.expected_revision_generation, true
    ) OR NOT hwpx_agent.idempotency_v2_head_matches(
        p_tenant_id, p_project_id, v_record.branch_id,
        v_record.expected_revision_id, v_record.expected_revision_generation
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_NO_EFFECT_ORACLE_FAILED';
    END IF;
    v_retry_at := hwpx_agent.idempotency_v2_retry_at(
        v_now, v_record.attempt_count,
        v_record.base_delay_seconds, v_record.max_delay_seconds
    );
    v_terminal := v_record.attempt_count >= v_record.max_attempts
        OR v_retry_at >= v_record.expires_at;
    v_attempt_state := CASE WHEN v_job.state IN ('leased', 'staged') THEN 'leased' ELSE 'running' END;
    DELETE FROM hwpx_agent.idempotency_commit_authorizations
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND idempotency_key = p_idempotency_key
      AND job_id = p_job_id AND attempt_no = p_attempt_no
      AND fencing_token = p_fencing_token;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'on', true);
    UPDATE hwpx_agent.job_attempts SET state = 'failed',
        receipt_artifact_id = p_receipt_artifact_id, completed_at = v_now, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id
      AND attempt_no = p_attempt_no AND execution_id = p_execution_id
      AND agent_instance_id = p_agent_instance_id AND fencing_token = p_fencing_token
      AND state_machine_version = 2 AND state = v_attempt_state;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_ATTEMPT_MISMATCH';
    END IF;
    UPDATE hwpx_agent.jobs SET
        state = CASE WHEN v_terminal THEN 'failed' ELSE 'retry_pending' END,
        lease_owner_agent_id = NULL, active_execution_id = NULL,
        lease_issued_at = NULL, lease_expires_at = NULL,
        terminal_error_code = CASE WHEN v_terminal THEN 'RETRY_EXHAUSTED' ELSE NULL END,
        completed_at = CASE WHEN v_terminal THEN v_now ELSE NULL END,
        updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    UPDATE hwpx_agent.idempotency_records SET
        state = CASE WHEN v_terminal THEN 'terminal_failure' ELSE 'retry_pending' END,
        receipt_artifact_id = p_receipt_artifact_id,
        terminal_error_code = CASE WHEN v_terminal THEN 'RETRY_EXHAUSTED' ELSE NULL END,
        retry_not_before = CASE WHEN v_terminal THEN NULL ELSE v_retry_at END,
        last_retry_class = p_retry_class, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND idempotency_key = p_idempotency_key;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'off', true);
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id,
        CASE WHEN v_terminal THEN 'idempotency.v2_retry_exhausted'
             ELSE 'idempotency.v2_retry_scheduled' END,
        p_subject_sha256, p_job_id, p_event_sha256
    );
    RETURN QUERY SELECT
        CASE WHEN v_terminal THEN 'terminal_failure' ELSE 'retry_scheduled' END,
        p_job_id,
        CASE WHEN v_terminal THEN 'terminal_failure' ELSE 'retry_pending' END,
        p_attempt_no, p_fencing_token,
        CASE WHEN v_terminal THEN NULL ELSE v_retry_at END,
        NULL::uuid, CASE WHEN v_terminal THEN 'RETRY_EXHAUSTED' ELSE NULL END,
        p_receipt_artifact_id;
END
$$;

CREATE FUNCTION hwpx_agent.complete_stored_revision_job_success_v1(
    p_tenant_id uuid, p_project_id uuid, p_subject_sha256 character(64),
    p_idempotency_key uuid, p_job_id uuid, p_agent_instance_id uuid,
    p_execution_id uuid, p_attempt_no integer, p_fencing_token bigint,
    p_result_revision_id uuid, p_receipt_artifact_id uuid,
    p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_outcome text, returned_job_id uuid, returned_state text,
    returned_attempt_count integer, returned_fencing_token bigint,
    returned_retry_not_before timestamptz, returned_result_revision_id uuid,
    returned_terminal_error_code text, returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_record hwpx_agent.idempotency_records%ROWTYPE;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_now timestamptz := clock_timestamp();
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(p_tenant_id, p_project_id, p_subject_sha256);
    IF p_event_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'IDEMPOTENCY_SUCCESS_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_record FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = p_tenant_id AND record.project_id = p_project_id
      AND record.idempotency_key = p_idempotency_key FOR UPDATE;
    SELECT * INTO v_job FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
      AND job.job_id = p_job_id FOR UPDATE;
    IF v_record.record_version IS DISTINCT FROM 2 OR v_record.state <> 'in_progress'
       OR v_record.job_id <> p_job_id OR v_record.subject_sha256 <> p_subject_sha256
       OR v_job.state_machine_version IS DISTINCT FROM 2 OR v_job.state <> 'validating'
       OR ROW(v_job.lease_owner_agent_id, v_job.active_execution_id,
              v_job.attempt_count, v_job.fencing_token)
          IS DISTINCT FROM ROW(p_agent_instance_id, p_execution_id,
                               p_attempt_no, p_fencing_token)
       OR v_job.lease_expires_at <= v_now THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_LEASE_MISMATCH';
    END IF;
    IF NOT hwpx_agent.stored_revision_committed_effect_qualified_v1(
        p_tenant_id, p_project_id, v_record.branch_id, p_subject_sha256,
        v_record.source_artifact_id, v_record.source_artifact_sha256,
        v_record.expected_revision_id, v_record.expected_revision_generation,
        v_job.operation_plan_sha256, p_result_revision_id, v_record.expected_effect_sha256,
        v_record.transaction_receipt_sha256, p_receipt_artifact_id
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_COMMITTED_ORACLE_FAILED';
    END IF;
    DELETE FROM hwpx_agent.idempotency_commit_authorizations
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND idempotency_key = p_idempotency_key
      AND job_id = p_job_id AND attempt_no = p_attempt_no
      AND fencing_token = p_fencing_token;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'on', true);
    UPDATE hwpx_agent.job_attempts SET state = 'succeeded',
        receipt_artifact_id = p_receipt_artifact_id, completed_at = v_now, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id
      AND attempt_no = p_attempt_no AND execution_id = p_execution_id
      AND agent_instance_id = p_agent_instance_id AND fencing_token = p_fencing_token
      AND state_machine_version = 2 AND state = 'running';
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'IDEMPOTENCY_ATTEMPT_MISMATCH';
    END IF;
    UPDATE hwpx_agent.jobs SET state = 'succeeded',
        lease_owner_agent_id = NULL, active_execution_id = NULL,
        lease_issued_at = NULL, lease_expires_at = NULL,
        result_revision_id = p_result_revision_id,
        terminal_error_code = NULL, completed_at = v_now, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    UPDATE hwpx_agent.idempotency_records SET state = 'terminal_success',
        result_revision_id = p_result_revision_id,
        receipt_artifact_id = p_receipt_artifact_id,
        terminal_error_code = NULL, retry_not_before = NULL, updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND idempotency_key = p_idempotency_key;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'off', true);
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id,
        revision_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id, 'idempotency.v2_succeeded',
        p_subject_sha256, p_job_id, p_result_revision_id, p_event_sha256
    );
    RETURN QUERY SELECT 'committed'::text, p_job_id, 'terminal_success'::text,
        p_attempt_no, p_fencing_token, NULL::timestamptz,
        p_result_revision_id, NULL::text, p_receipt_artifact_id;
END
$$;

CREATE FUNCTION hwpx_agent.reconcile_stored_revision_job_v1(
    p_tenant_id uuid, p_project_id uuid, p_subject_sha256 character(64),
    p_idempotency_key uuid, p_job_id uuid, p_mode text,
    p_result_revision_id uuid, p_receipt_artifact_id uuid,
    p_event_sha256 character(64)
)
RETURNS TABLE (
    returned_outcome text, returned_job_id uuid, returned_state text,
    returned_attempt_count integer, returned_fencing_token bigint,
    returned_retry_not_before timestamptz, returned_result_revision_id uuid,
    returned_terminal_error_code text, returned_receipt_artifact_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_record hwpx_agent.idempotency_records%ROWTYPE;
    v_job hwpx_agent.jobs%ROWTYPE;
    v_now timestamptz := clock_timestamp();
    v_retry_at timestamptz;
    v_terminal boolean;
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(p_tenant_id, p_project_id, p_subject_sha256);
    IF p_mode NOT IN ('committed', 'no_effect')
       OR p_event_sha256 !~ '^[0-9a-f]{64}$'
       OR (p_mode = 'committed' AND p_result_revision_id IS NULL)
       OR (p_mode = 'no_effect' AND p_result_revision_id IS NOT NULL) THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'IDEMPOTENCY_RECONCILE_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_record FROM hwpx_agent.idempotency_records AS record
    WHERE record.tenant_id = p_tenant_id AND record.project_id = p_project_id
      AND record.idempotency_key = p_idempotency_key FOR UPDATE;
    SELECT * INTO v_job FROM hwpx_agent.jobs AS job
    WHERE job.tenant_id = p_tenant_id AND job.project_id = p_project_id
      AND job.job_id = p_job_id FOR UPDATE;
    IF v_record.record_version IS DISTINCT FROM 2 OR v_record.state <> 'outcome_unknown'
       OR v_record.job_id <> p_job_id OR v_record.subject_sha256 <> p_subject_sha256
       OR v_job.state_machine_version IS DISTINCT FROM 2
       OR v_job.state <> 'unknown_outcome' THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_RECONCILE_STATE_INVALID';
    END IF;

    IF p_mode = 'committed' THEN
        IF NOT hwpx_agent.stored_revision_committed_effect_qualified_v1(
            p_tenant_id, p_project_id, v_record.branch_id, p_subject_sha256,
            v_record.source_artifact_id, v_record.source_artifact_sha256,
            v_record.expected_revision_id, v_record.expected_revision_generation,
            v_job.operation_plan_sha256, p_result_revision_id, v_record.expected_effect_sha256,
            v_record.transaction_receipt_sha256, p_receipt_artifact_id
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_COMMITTED_ORACLE_FAILED';
        END IF;
        PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'on', true);
        UPDATE hwpx_agent.jobs SET state = 'succeeded',
            result_revision_id = p_result_revision_id,
            terminal_error_code = NULL, completed_at = v_now, updated_at = v_now
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
        UPDATE hwpx_agent.idempotency_records SET state = 'terminal_success',
            result_revision_id = p_result_revision_id,
            receipt_artifact_id = p_receipt_artifact_id,
            terminal_error_code = NULL, retry_not_before = NULL, updated_at = v_now
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id
          AND idempotency_key = p_idempotency_key;
        PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'off', true);
        INSERT INTO hwpx_agent.audit_events (
            tenant_id, project_id, event_type, subject_sha256, job_id,
            revision_id, payload_sha256
        ) VALUES (
            p_tenant_id, p_project_id, 'idempotency.v2_reconciled_committed',
            p_subject_sha256, p_job_id, p_result_revision_id, p_event_sha256
        );
        RETURN QUERY SELECT 'committed'::text, p_job_id, 'terminal_success'::text,
            v_record.attempt_count, v_record.last_fencing_token,
            NULL::timestamptz, p_result_revision_id, NULL::text,
            p_receipt_artifact_id;
        RETURN;
    END IF;

    IF NOT hwpx_agent.idempotency_v2_artifact_qualified(
        p_tenant_id, p_subject_sha256, p_receipt_artifact_id, 'receipt',
        (SELECT content_sha256 FROM hwpx_agent.artifacts
         WHERE tenant_id = p_tenant_id AND artifact_id = p_receipt_artifact_id)
    ) OR NOT hwpx_agent.stored_revision_source_qualified_v1(
        p_tenant_id, p_project_id, v_record.branch_id, p_subject_sha256, v_record.source_artifact_id, v_record.source_artifact_sha256,
        v_record.expected_revision_id, v_record.expected_revision_generation, true
    ) OR NOT hwpx_agent.idempotency_v2_head_matches(
        p_tenant_id, p_project_id, v_record.branch_id,
        v_record.expected_revision_id, v_record.expected_revision_generation
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'IDEMPOTENCY_NO_EFFECT_ORACLE_FAILED';
    END IF;
    v_retry_at := hwpx_agent.idempotency_v2_retry_at(
        v_now, v_record.attempt_count,
        v_record.base_delay_seconds, v_record.max_delay_seconds
    );
    v_terminal := v_record.attempt_count >= v_record.max_attempts
        OR v_retry_at >= v_record.expires_at;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'on', true);
    UPDATE hwpx_agent.jobs SET
        state = CASE WHEN v_terminal THEN 'failed' ELSE 'retry_pending' END,
        terminal_error_code = CASE WHEN v_terminal THEN 'RETRY_EXHAUSTED' ELSE NULL END,
        completed_at = CASE WHEN v_terminal THEN v_now ELSE NULL END,
        updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id AND job_id = p_job_id;
    UPDATE hwpx_agent.idempotency_records SET
        state = CASE WHEN v_terminal THEN 'terminal_failure' ELSE 'retry_pending' END,
        receipt_artifact_id = p_receipt_artifact_id,
        terminal_error_code = CASE WHEN v_terminal THEN 'RETRY_EXHAUSTED' ELSE NULL END,
        retry_not_before = CASE WHEN v_terminal THEN NULL ELSE v_retry_at END,
        last_retry_class = 'automation_no_effect', updated_at = v_now
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND idempotency_key = p_idempotency_key;
    PERFORM set_config('hwpx_agent.allow_idempotency_v2_transition', 'off', true);
    INSERT INTO hwpx_agent.audit_events (
        tenant_id, project_id, event_type, subject_sha256, job_id, payload_sha256
    ) VALUES (
        p_tenant_id, p_project_id,
        CASE WHEN v_terminal THEN 'idempotency.v2_no_effect_exhausted'
             ELSE 'idempotency.v2_reconciled_no_effect' END,
        p_subject_sha256, p_job_id, p_event_sha256
    );
    RETURN QUERY SELECT
        CASE WHEN v_terminal THEN 'terminal_failure' ELSE 'no_effect' END,
        p_job_id,
        CASE WHEN v_terminal THEN 'terminal_failure' ELSE 'retry_pending' END,
        v_record.attempt_count, v_record.last_fencing_token,
        CASE WHEN v_terminal THEN NULL ELSE v_retry_at END,
        NULL::uuid, CASE WHEN v_terminal THEN 'RETRY_EXHAUSTED' ELSE NULL END,
        p_receipt_artifact_id;
END
$$;
-- END_FROZEN_V2_DERIVATIONS

-- Grants are deliberately not installed. An explicit schema23 connector must verify all old
-- guards plus this table/trigger/function boundary before any server job can use this path.
REVOKE ALL ON FUNCTION hwpx_agent.stored_revision_source_qualified_v1(uuid,uuid,uuid,character,uuid,character,uuid,bigint,boolean) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.require_stored_commit_receipt_v1(uuid,character,uuid,character) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.register_stored_revision_commit_intent_v1(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,uuid,uuid,uuid,uuid,character,character,uuid,character,uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.read_stored_revision_commit_intent_v1(uuid,uuid,character,uuid,uuid,integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.guard_stored_revision_commit_intent_v1() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.stored_revision_committed_effect_qualified_v1(uuid,uuid,uuid,character,uuid,character,uuid,bigint,character,uuid,character,character,uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.claim_stored_revision_job_v1(uuid,uuid,uuid,character,uuid,uuid,uuid,uuid,uuid,bigint,character,character,character,character,character,character,text,character,integer,integer,integer,integer,character) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.lease_stored_revision_job_v1(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,character) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.schedule_stored_revision_retry_v1(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,text,uuid,character) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.complete_stored_revision_job_success_v1(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,uuid,uuid,character) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.reconcile_stored_revision_job_v1(uuid,uuid,character,uuid,uuid,text,uuid,uuid,character) FROM PUBLIC;
INSERT INTO hwpx_agent.schema_versions(version,migration_name,migration_sha256)
VALUES(23,'p09.stored_revision_jobs_v1',current_setting('hwpx_agent.migration_sha256'));
COMMIT;
