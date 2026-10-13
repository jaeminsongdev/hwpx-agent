BEGIN;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 18 AND migration_name = 'p09.full_document_ir_v1')
        OR EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version >= 19) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'FULL_IR_INTENT_REQUIRES_SCHEMA_18';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256', true) IS NULL
        OR current_setting('hwpx_agent.migration_sha256', true) !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'FULL_IR_INTENT_MIGRATION_DIGEST_REQUIRED';
    END IF;
END
$$;

-- Immutable admission-time IR intent. This is SQL metadata, NOT a native/import attestation.
CREATE TABLE hwpx_agent.full_document_ir_intents (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    idempotency_key uuid NOT NULL,
    artifact_id uuid NOT NULL,
    artifact_sha256 character(64) NOT NULL,
    result_package_sha256 character(64) NOT NULL,
    graph_sha256 character(64) NOT NULL,
    PRIMARY KEY (tenant_id, project_id, idempotency_key),
    FOREIGN KEY (tenant_id, project_id, idempotency_key)
        REFERENCES hwpx_agent.idempotency_records(tenant_id, project_id, idempotency_key)
        ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, artifact_id)
        REFERENCES hwpx_agent.artifacts(tenant_id, artifact_id) ON DELETE RESTRICT,
    CHECK (artifact_id <> '00000000-0000-0000-0000-000000000000'::uuid
        AND artifact_sha256 ~ '^[0-9a-f]{64}$'
        AND result_package_sha256 ~ '^[0-9a-f]{64}$'
        AND graph_sha256 ~ '^[0-9a-f]{64}$' AND artifact_sha256 = graph_sha256)
);
ALTER TABLE hwpx_agent.full_document_ir_intents ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.full_document_ir_intents FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.full_document_ir_intents
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());
REVOKE ALL ON TABLE hwpx_agent.full_document_ir_intents FROM PUBLIC;
CREATE TRIGGER full_document_ir_intents_immutable BEFORE UPDATE OR DELETE
    ON hwpx_agent.full_document_ir_intents
    FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();

CREATE FUNCTION hwpx_agent.require_full_ir_intent_artifact_v1(
    p_tenant_id uuid, p_subject_sha256 character(64), p_artifact_id uuid,
    p_artifact_sha256 character(64), p_graph_sha256 character(64)
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
BEGIN
    IF p_artifact_id IS NULL OR p_artifact_sha256 IS NULL OR p_graph_sha256 IS NULL
        OR p_artifact_sha256 IS DISTINCT FROM p_graph_sha256
        OR NOT EXISTS (
            SELECT 1 FROM hwpx_agent.artifacts AS artifact
            JOIN hwpx_agent.artifact_acl AS acl
                ON acl.tenant_id = artifact.tenant_id AND acl.artifact_id = artifact.artifact_id
            WHERE artifact.tenant_id = p_tenant_id AND artifact.artifact_id = p_artifact_id
                AND artifact.artifact_kind = 'document_ir'
                AND artifact.content_sha256 = p_artifact_sha256
                AND artifact.media_type = 'application/vnd.hwpx-agent.document-graph+json'
                AND artifact.service_metadata_version = 1
                AND artifact.storage_state = 'available'
                AND artifact.validation_state = 'verified'
                AND artifact.quarantine_reason_code IS NULL
                AND artifact.size_bytes BETWEEN 1 AND 33554432
                AND acl.subject_sha256 = p_subject_sha256 AND acl.can_read
        ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'FULL_IR_INTENT_ARTIFACT_NOT_QUALIFIED';
    END IF;
END
$$;

-- Also protects the unchanged legacy API and schema18 leaf from bypass.
-- The original idempotency receipt guard still validates and consumes genuine lease authority.
CREATE FUNCTION hwpx_agent.guard_full_ir_commit_intent_v1()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_intent hwpx_agent.full_document_ir_intents%ROWTYPE;
    v_revision hwpx_agent.revisions%ROWTYPE;
    v_has_intent boolean;
BEGIN
    SELECT intent.* INTO v_intent FROM hwpx_agent.full_document_ir_intents AS intent
    JOIN hwpx_agent.idempotency_records AS record
        USING (tenant_id, project_id, idempotency_key)
    WHERE record.tenant_id = NEW.tenant_id AND record.project_id = NEW.project_id
        AND record.transaction_receipt_sha256 = NEW.transaction_receipt_sha256;
    v_has_intent := FOUND;
    SELECT * INTO v_revision FROM hwpx_agent.revisions AS revision
    WHERE revision.tenant_id = NEW.tenant_id AND revision.project_id = NEW.project_id
        AND revision.revision_id = NEW.committed_revision_id;
    IF v_has_intent OR v_revision.full_document_ir_artifact_id IS NOT NULL THEN
        IF NOT v_has_intent OR ROW(v_revision.full_document_ir_artifact_id,
            v_revision.full_document_ir_artifact_sha256,
            v_revision.full_document_ir_result_package_sha256,
            v_revision.full_document_ir_graph_sha256)
            IS DISTINCT FROM ROW(v_intent.artifact_id, v_intent.artifact_sha256,
                v_intent.result_package_sha256, v_intent.graph_sha256) THEN
            RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'FULL_IR_COMMIT_INTENT_MISMATCH';
        END IF;
        PERFORM hwpx_agent.require_full_ir_intent_artifact_v1(
            NEW.tenant_id, NEW.subject_sha256, v_intent.artifact_id,
            v_intent.artifact_sha256, v_intent.graph_sha256
        );
    END IF;
    RETURN NEW;
END
$$;
CREATE TRIGGER revision_commit_receipts_full_ir_intent_guard
    BEFORE INSERT ON hwpx_agent.revision_commit_receipts
    FOR EACH ROW EXECUTE FUNCTION hwpx_agent.guard_full_ir_commit_intent_v1();

-- Original v2 claim/commit control flow retained under five additive transformations each.
CREATE FUNCTION hwpx_agent.claim_idempotent_job_with_full_ir_v1(
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
    p_event_sha256 character(64),
    p_full_document_ir_artifact_id uuid,
    p_full_document_ir_artifact_sha256 character(64),
    p_full_document_ir_result_package_sha256 character(64),
    p_full_document_ir_graph_sha256 character(64)
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
    PERFORM hwpx_agent.require_full_ir_intent_artifact_v1(
        p_tenant_id, p_subject_sha256, p_full_document_ir_artifact_id,
        p_full_document_ir_artifact_sha256, p_full_document_ir_graph_sha256
    );
    IF p_full_document_ir_artifact_id IS NOT DISTINCT FROM p_source_artifact_id
       OR p_full_document_ir_result_package_sha256 IS DISTINCT FROM p_expected_effect_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'FULL_IR_INTENT_REQUEST_INVALID';
    END IF;
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
        IF NOT EXISTS (
            SELECT 1 FROM hwpx_agent.full_document_ir_intents AS intent
            WHERE intent.tenant_id = p_tenant_id AND intent.project_id = p_project_id
              AND intent.idempotency_key = p_idempotency_key
              AND ROW(intent.artifact_id, intent.artifact_sha256,
                  intent.result_package_sha256, intent.graph_sha256)
              IS NOT DISTINCT FROM ROW(p_full_document_ir_artifact_id,
                  p_full_document_ir_artifact_sha256,
                  p_full_document_ir_result_package_sha256, p_full_document_ir_graph_sha256)
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23505', MESSAGE = 'FULL_IR_INTENT_KEY_CONFLICT';
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
    IF NOT hwpx_agent.idempotency_v2_artifact_qualified(
        p_tenant_id, p_subject_sha256, p_source_artifact_id,
        'source', p_source_artifact_sha256
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
    INSERT INTO hwpx_agent.full_document_ir_intents (
        tenant_id, project_id, idempotency_key, artifact_id,
        artifact_sha256, result_package_sha256, graph_sha256
    ) VALUES (
        p_tenant_id, p_project_id, p_idempotency_key, p_full_document_ir_artifact_id,
        p_full_document_ir_artifact_sha256, p_full_document_ir_result_package_sha256,
        p_full_document_ir_graph_sha256
    );
    RETURN QUERY SELECT 'new'::text, p_job_id, 'claimed'::text,
        0, 0::bigint, NULL::timestamptz, NULL::uuid, NULL::text, NULL::uuid;
END
$$;

CREATE FUNCTION hwpx_agent.commit_idempotent_revision_cas_with_full_ir_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_branch_id uuid,
    p_subject_sha256 character(64),
    p_idempotency_key uuid,
    p_job_id uuid,
    p_agent_instance_id uuid,
    p_execution_id uuid,
    p_attempt_no integer,
    p_fencing_token bigint,
    p_commit_authorization_id uuid,
    p_commit_id uuid,
    p_expected_revision_id uuid,
    p_expected_generation bigint,
    p_new_revision_id uuid,
    p_parent_revision_ids uuid[],
    p_source_artifact_id uuid,
    p_result_artifact_id uuid,
    p_semantic_diff_artifact_id uuid,
    p_operation_plan_sha256 character(64),
    p_validation_state text,
    p_validation_summary_sha256 character(64),
    p_transaction_receipt_sha256 character(64),
    p_commit_request_sha256 character(64),
    p_commit_receipt_sha256 character(64),
    p_full_document_ir_artifact_id uuid,
    p_full_document_ir_artifact_sha256 character(64),
    p_full_document_ir_result_package_sha256 character(64),
    p_full_document_ir_graph_sha256 character(64)
)
RETURNS TABLE (
    outcome text,
    observed_revision_id uuid,
    observed_generation bigint,
    committed_revision_id uuid,
    committed_generation bigint,
    receipt_sha256 character(64)
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
BEGIN
    PERFORM hwpx_agent.require_idempotency_v2_editor(
        p_tenant_id, p_project_id, p_subject_sha256
    );
    PERFORM hwpx_agent.require_full_ir_intent_artifact_v1(
        p_tenant_id, p_subject_sha256, p_full_document_ir_artifact_id,
        p_full_document_ir_artifact_sha256, p_full_document_ir_graph_sha256
    );
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.full_document_ir_intents AS intent
        WHERE intent.tenant_id = p_tenant_id AND intent.project_id = p_project_id
          AND intent.idempotency_key = p_idempotency_key
          AND ROW(intent.artifact_id, intent.artifact_sha256,
              intent.result_package_sha256, intent.graph_sha256)
          IS NOT DISTINCT FROM ROW(p_full_document_ir_artifact_id,
              p_full_document_ir_artifact_sha256,
              p_full_document_ir_result_package_sha256, p_full_document_ir_graph_sha256)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'FULL_IR_COMMIT_INTENT_MISMATCH';
    END IF;
    IF p_commit_authorization_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_attempt_no NOT BETWEEN 1 AND 10
       OR p_fencing_token <> p_attempt_no THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023', MESSAGE = 'IDEMPOTENCY_COMMIT_REQUEST_INVALID';
    END IF;
    PERFORM 1
    FROM hwpx_agent.idempotency_commit_authorizations AS commit_auth
    WHERE commit_auth.tenant_id = p_tenant_id
      AND commit_auth.project_id = p_project_id
      AND commit_auth.idempotency_key = p_idempotency_key
      AND commit_auth.job_id = p_job_id
      AND commit_auth.agent_instance_id = p_agent_instance_id
      AND commit_auth.execution_id = p_execution_id
      AND commit_auth.attempt_no = p_attempt_no
      AND commit_auth.fencing_token = p_fencing_token
      AND commit_auth.commit_authorization_id = p_commit_authorization_id
      AND commit_auth.transaction_receipt_sha256 = p_transaction_receipt_sha256
    FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = '42501', MESSAGE = 'IDEMPOTENCY_COMMIT_AUTHORIZATION_REQUIRED';
    END IF;

    PERFORM set_config(
        'hwpx_agent.commit_authorization_id', p_commit_authorization_id::text, true
    );
    RETURN QUERY SELECT * FROM hwpx_agent.commit_revision_cas_with_full_ir_v1(
        p_tenant_id, p_project_id, p_branch_id, p_subject_sha256,
        p_commit_id, p_expected_revision_id, p_expected_generation,
        p_new_revision_id, p_parent_revision_ids, p_source_artifact_id,
        p_result_artifact_id, p_semantic_diff_artifact_id,
        p_operation_plan_sha256, p_validation_state,
        p_validation_summary_sha256, p_transaction_receipt_sha256,
        p_commit_request_sha256, p_commit_receipt_sha256,
        p_full_document_ir_artifact_id, p_full_document_ir_artifact_sha256,
        p_full_document_ir_result_package_sha256, p_full_document_ir_graph_sha256
    );
    PERFORM set_config('hwpx_agent.commit_authorization_id', '', true);
END
$$;
REVOKE ALL ON FUNCTION hwpx_agent.require_full_ir_intent_artifact_v1(
    uuid, character, uuid, character, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.guard_full_ir_commit_intent_v1() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.claim_idempotent_job_with_full_ir_v1(
    uuid, uuid, uuid, character, uuid, uuid, uuid, uuid, uuid, bigint,
    character, character, character, character, character, character,
    text, character, integer, integer, integer, integer, character,
    uuid, character, character, character
) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.commit_idempotent_revision_cas_with_full_ir_v1(
    uuid, uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    uuid, uuid, uuid, bigint, uuid, uuid[], uuid, uuid, uuid,
    character, text, character, character, character, character,
    uuid, character, character, character
) FROM PUBLIC;
INSERT INTO hwpx_agent.schema_versions(version, migration_name, migration_sha256)
VALUES (19, 'p09.authorized_full_ir_intent_v1', current_setting('hwpx_agent.migration_sha256'));
COMMIT;

