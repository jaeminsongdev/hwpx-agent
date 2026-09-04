BEGIN;

CREATE SCHEMA hwpx_agent;
REVOKE ALL ON SCHEMA hwpx_agent FROM PUBLIC;

CREATE FUNCTION hwpx_agent.current_tenant_id()
RETURNS uuid
LANGUAGE sql
STABLE
SET search_path = pg_catalog
AS $$
    SELECT NULLIF(current_setting('hwpx_agent.tenant_id', true), '')::uuid
$$;

CREATE FUNCTION hwpx_agent.touch_updated_at()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    NEW.updated_at := transaction_timestamp();
    RETURN NEW;
END
$$;

CREATE FUNCTION hwpx_agent.reject_immutable_change()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    RAISE EXCEPTION USING
        ERRCODE = '55000',
        MESSAGE = 'immutable metadata row cannot be updated or deleted';
END
$$;

CREATE FUNCTION hwpx_agent.protect_artifact_identity()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    IF ROW(
        NEW.tenant_id,
        NEW.artifact_id,
        NEW.content_sha256,
        NEW.size_bytes,
        NEW.media_type,
        NEW.artifact_kind,
        NEW.encryption_key_ref,
        NEW.created_at
    ) IS DISTINCT FROM ROW(
        OLD.tenant_id,
        OLD.artifact_id,
        OLD.content_sha256,
        OLD.size_bytes,
        OLD.media_type,
        OLD.artifact_kind,
        OLD.encryption_key_ref,
        OLD.created_at
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'artifact identity is immutable';
    END IF;
    RETURN NEW;
END
$$;

CREATE FUNCTION hwpx_agent.protect_idempotency_identity()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    IF ROW(
        NEW.tenant_id,
        NEW.project_id,
        NEW.idempotency_key,
        NEW.request_sha256,
        NEW.created_at
    ) IS DISTINCT FROM ROW(
        OLD.tenant_id,
        OLD.project_id,
        OLD.idempotency_key,
        OLD.request_sha256,
        OLD.created_at
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'idempotency identity is immutable';
    END IF;
    RETURN NEW;
END
$$;

CREATE FUNCTION hwpx_agent.protect_job_attempt_identity()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    IF ROW(
        NEW.tenant_id,
        NEW.project_id,
        NEW.job_id,
        NEW.attempt_no,
        NEW.execution_id,
        NEW.agent_instance_id,
        NEW.fencing_token,
        NEW.started_at
    ) IS DISTINCT FROM ROW(
        OLD.tenant_id,
        OLD.project_id,
        OLD.job_id,
        OLD.attempt_no,
        OLD.execution_id,
        OLD.agent_instance_id,
        OLD.fencing_token,
        OLD.started_at
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'job attempt identity is immutable';
    END IF;
    RETURN NEW;
END
$$;

CREATE FUNCTION hwpx_agent.protect_job_identity()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    IF ROW(
        NEW.tenant_id,
        NEW.project_id,
        NEW.job_id,
        NEW.request_id,
        NEW.input_artifact_id,
        NEW.expected_revision_id,
        NEW.operation_plan_sha256,
        NEW.required_target_profile_id,
        NEW.required_capability_set_sha256,
        NEW.created_at
    ) IS DISTINCT FROM ROW(
        OLD.tenant_id,
        OLD.project_id,
        OLD.job_id,
        OLD.request_id,
        OLD.input_artifact_id,
        OLD.expected_revision_id,
        OLD.operation_plan_sha256,
        OLD.required_target_profile_id,
        OLD.required_capability_set_sha256,
        OLD.created_at
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'job identity is immutable';
    END IF;
    RETURN NEW;
END
$$;

CREATE TABLE hwpx_agent.schema_versions (
    version bigint PRIMARY KEY,
    migration_name text NOT NULL UNIQUE,
    migration_sha256 character(64) NOT NULL,
    applied_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT schema_versions_name_format CHECK (
        migration_name ~ '^[a-z0-9][a-z0-9._-]{2,127}$'
    ),
    CONSTRAINT schema_versions_digest_format CHECK (
        migration_sha256 ~ '^[0-9a-f]{64}$'
    )
);

CREATE TABLE hwpx_agent.tenants (
    tenant_id uuid PRIMARY KEY,
    slug text NOT NULL UNIQUE,
    state text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT tenants_slug_format CHECK (slug ~ '^[a-z0-9][a-z0-9-]{2,62}$'),
    CONSTRAINT tenants_state_value CHECK (state IN ('active', 'suspended', 'deleting')),
    CONSTRAINT tenants_time_order CHECK (updated_at >= created_at)
);

CREATE TABLE hwpx_agent.projects (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    slug text NOT NULL,
    display_name text NOT NULL,
    target_profile_id text NOT NULL,
    retention_policy_id text NOT NULL,
    head_revision_id uuid,
    state text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, project_id),
    UNIQUE (tenant_id, slug),
    CONSTRAINT projects_tenant_fk FOREIGN KEY (tenant_id)
        REFERENCES hwpx_agent.tenants (tenant_id) ON DELETE RESTRICT,
    CONSTRAINT projects_slug_format CHECK (slug ~ '^[a-z0-9][a-z0-9-]{2,62}$'),
    CONSTRAINT projects_display_name_length CHECK (char_length(display_name) BETWEEN 1 AND 200),
    CONSTRAINT projects_target_profile_format CHECK (
        target_profile_id ~ '^[A-Za-z0-9][A-Za-z0-9._-]{1,126}$'
    ),
    CONSTRAINT projects_retention_policy_format CHECK (
        retention_policy_id ~ '^[a-z][a-z0-9]*(\.[a-z0-9_-]+)+$'
    ),
    CONSTRAINT projects_state_value CHECK (state IN ('active', 'archived', 'deleting')),
    CONSTRAINT projects_time_order CHECK (updated_at >= created_at)
);

CREATE TABLE hwpx_agent.project_acl (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    subject_sha256 character(64) NOT NULL,
    role text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, project_id, subject_sha256),
    CONSTRAINT project_acl_project_fk FOREIGN KEY (tenant_id, project_id)
        REFERENCES hwpx_agent.projects (tenant_id, project_id) ON DELETE CASCADE,
    CONSTRAINT project_acl_subject_format CHECK (subject_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT project_acl_role_value CHECK (role IN ('reader', 'editor', 'owner'))
);

CREATE TABLE hwpx_agent.artifacts (
    tenant_id uuid NOT NULL,
    artifact_id uuid NOT NULL,
    content_sha256 character(64) NOT NULL,
    size_bytes bigint NOT NULL,
    media_type text NOT NULL,
    artifact_kind text NOT NULL,
    storage_state text NOT NULL DEFAULT 'staged',
    quarantine_reason_code text,
    encryption_key_ref text NOT NULL,
    retention_until timestamptz,
    verified_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, artifact_id),
    UNIQUE (tenant_id, content_sha256),
    CONSTRAINT artifacts_tenant_fk FOREIGN KEY (tenant_id)
        REFERENCES hwpx_agent.tenants (tenant_id) ON DELETE RESTRICT,
    CONSTRAINT artifacts_digest_format CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT artifacts_size_range CHECK (size_bytes BETWEEN 0 AND 1099511627776),
    CONSTRAINT artifacts_media_type_format CHECK (
        media_type ~ '^[a-z0-9][a-z0-9!#$&^_.+-]+/[a-z0-9][a-z0-9!#$&^_.+-]+$'
    ),
    CONSTRAINT artifacts_kind_value CHECK (
        artifact_kind IN ('source', 'result', 'preview', 'evidence', 'trace', 'diff', 'receipt')
    ),
    CONSTRAINT artifacts_storage_state_value CHECK (
        storage_state IN ('staged', 'available', 'quarantined', 'orphaned', 'purging')
    ),
    CONSTRAINT artifacts_quarantine_consistency CHECK (
        (storage_state = 'quarantined' AND quarantine_reason_code IS NOT NULL)
        OR (storage_state <> 'quarantined' AND quarantine_reason_code IS NULL)
    ),
    CONSTRAINT artifacts_quarantine_code_format CHECK (
        quarantine_reason_code IS NULL
        OR quarantine_reason_code ~ '^[A-Z][A-Z0-9_]{2,63}$'
    ),
    CONSTRAINT artifacts_encryption_ref_format CHECK (
        encryption_key_ref ~ '^[a-z][a-z0-9]*(\.[a-z0-9_-]+)+$'
    ),
    CONSTRAINT artifacts_time_order CHECK (
        updated_at >= created_at
        AND (verified_at IS NULL OR verified_at >= created_at)
        AND (retention_until IS NULL OR retention_until >= created_at)
    )
);

CREATE TABLE hwpx_agent.revisions (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    revision_id uuid NOT NULL,
    source_artifact_id uuid NOT NULL,
    result_artifact_id uuid NOT NULL,
    semantic_diff_artifact_id uuid,
    operation_plan_sha256 character(64) NOT NULL,
    validation_state text NOT NULL,
    validation_summary_sha256 character(64) NOT NULL,
    created_by_subject_sha256 character(64) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, project_id, revision_id),
    UNIQUE (tenant_id, revision_id),
    CONSTRAINT revisions_project_fk FOREIGN KEY (tenant_id, project_id)
        REFERENCES hwpx_agent.projects (tenant_id, project_id) ON DELETE RESTRICT,
    CONSTRAINT revisions_source_artifact_fk FOREIGN KEY (tenant_id, source_artifact_id)
        REFERENCES hwpx_agent.artifacts (tenant_id, artifact_id) ON DELETE RESTRICT,
    CONSTRAINT revisions_result_artifact_fk FOREIGN KEY (tenant_id, result_artifact_id)
        REFERENCES hwpx_agent.artifacts (tenant_id, artifact_id) ON DELETE RESTRICT,
    CONSTRAINT revisions_diff_artifact_fk FOREIGN KEY (tenant_id, semantic_diff_artifact_id)
        REFERENCES hwpx_agent.artifacts (tenant_id, artifact_id) ON DELETE RESTRICT,
    CONSTRAINT revisions_plan_digest_format CHECK (operation_plan_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT revisions_validation_state_value CHECK (
        validation_state IN ('verified', 'partial', 'failed', 'unverified')
    ),
    CONSTRAINT revisions_validation_digest_format CHECK (
        validation_summary_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT revisions_subject_format CHECK (created_by_subject_sha256 ~ '^[0-9a-f]{64}$')
);

ALTER TABLE hwpx_agent.projects
    ADD CONSTRAINT projects_head_revision_fk
    FOREIGN KEY (tenant_id, project_id, head_revision_id)
    REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id)
    DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE hwpx_agent.branches (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    branch_id uuid NOT NULL,
    name text NOT NULL,
    head_revision_id uuid,
    is_default boolean NOT NULL DEFAULT false,
    created_by_subject_sha256 character(64) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, project_id, branch_id),
    UNIQUE (tenant_id, project_id, name),
    CONSTRAINT branches_project_fk FOREIGN KEY (tenant_id, project_id)
        REFERENCES hwpx_agent.projects (tenant_id, project_id) ON DELETE RESTRICT,
    CONSTRAINT branches_head_revision_fk FOREIGN KEY (
        tenant_id, project_id, head_revision_id
    ) REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id)
        ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT branches_name_format CHECK (
        name ~ '^[A-Za-z0-9][A-Za-z0-9._/-]{0,126}$'
        AND name !~ '(^|/)\.\.?($|/)'
        AND name !~ '//'
    ),
    CONSTRAINT branches_subject_format CHECK (
        created_by_subject_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT branches_time_order CHECK (updated_at >= created_at)
);

CREATE TABLE hwpx_agent.revision_parents (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    revision_id uuid NOT NULL,
    parent_revision_id uuid NOT NULL,
    parent_ordinal smallint NOT NULL,
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, project_id, revision_id, parent_revision_id),
    UNIQUE (tenant_id, project_id, revision_id, parent_ordinal),
    CONSTRAINT revision_parents_child_fk FOREIGN KEY (tenant_id, project_id, revision_id)
        REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id) ON DELETE RESTRICT,
    CONSTRAINT revision_parents_parent_fk FOREIGN KEY (tenant_id, project_id, parent_revision_id)
        REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id) ON DELETE RESTRICT,
    CONSTRAINT revision_parents_not_self CHECK (revision_id <> parent_revision_id),
    CONSTRAINT revision_parents_ordinal_range CHECK (parent_ordinal BETWEEN 0 AND 31)
);

CREATE TABLE hwpx_agent.checkpoints (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    checkpoint_id uuid NOT NULL,
    revision_id uuid NOT NULL,
    label text NOT NULL,
    created_by_subject_sha256 character(64) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, project_id, checkpoint_id),
    UNIQUE (tenant_id, project_id, label),
    CONSTRAINT checkpoints_revision_fk FOREIGN KEY (tenant_id, project_id, revision_id)
        REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id) ON DELETE RESTRICT,
    CONSTRAINT checkpoints_label_length CHECK (char_length(label) BETWEEN 1 AND 120),
    CONSTRAINT checkpoints_subject_format CHECK (created_by_subject_sha256 ~ '^[0-9a-f]{64}$')
);

CREATE TABLE hwpx_agent.jobs (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    job_id uuid NOT NULL,
    request_id uuid NOT NULL,
    input_artifact_id uuid NOT NULL,
    expected_revision_id uuid,
    result_revision_id uuid,
    operation_plan_sha256 character(64) NOT NULL,
    required_target_profile_id text NOT NULL,
    required_capability_set_sha256 character(64) NOT NULL,
    state text NOT NULL DEFAULT 'queued',
    attempt_count integer NOT NULL DEFAULT 0,
    lease_owner_agent_id uuid,
    fencing_token bigint NOT NULL DEFAULT 0,
    lease_expires_at timestamptz,
    cancellation_requested_at timestamptz,
    terminal_error_code text,
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    completed_at timestamptz,
    PRIMARY KEY (tenant_id, project_id, job_id),
    UNIQUE (tenant_id, project_id, request_id),
    CONSTRAINT jobs_project_fk FOREIGN KEY (tenant_id, project_id)
        REFERENCES hwpx_agent.projects (tenant_id, project_id) ON DELETE RESTRICT,
    CONSTRAINT jobs_input_artifact_fk FOREIGN KEY (tenant_id, input_artifact_id)
        REFERENCES hwpx_agent.artifacts (tenant_id, artifact_id) ON DELETE RESTRICT,
    CONSTRAINT jobs_expected_revision_fk FOREIGN KEY (tenant_id, project_id, expected_revision_id)
        REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id) ON DELETE RESTRICT,
    CONSTRAINT jobs_result_revision_fk FOREIGN KEY (tenant_id, project_id, result_revision_id)
        REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id) ON DELETE RESTRICT,
    CONSTRAINT jobs_plan_digest_format CHECK (operation_plan_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT jobs_target_profile_format CHECK (
        required_target_profile_id ~ '^[A-Za-z0-9][A-Za-z0-9._-]{1,126}$'
    ),
    CONSTRAINT jobs_capability_digest_format CHECK (
        required_capability_set_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT jobs_state_value CHECK (
        state IN (
            'queued', 'leased', 'staged', 'executing', 'validating',
            'succeeded', 'failed', 'cancelled', 'unknown_outcome'
        )
    ),
    CONSTRAINT jobs_attempt_count_range CHECK (attempt_count BETWEEN 0 AND 100),
    CONSTRAINT jobs_fencing_token_range CHECK (fencing_token >= 0),
    CONSTRAINT jobs_active_lease_consistency CHECK (
        state NOT IN ('leased', 'staged', 'executing', 'validating')
        OR (
            lease_owner_agent_id IS NOT NULL
            AND fencing_token > 0
            AND lease_expires_at IS NOT NULL
            AND attempt_count > 0
        )
    ),
    CONSTRAINT jobs_queued_lease_consistency CHECK (
        state <> 'queued'
        OR (
            lease_owner_agent_id IS NULL
            AND fencing_token = 0
            AND lease_expires_at IS NULL
            AND attempt_count = 0
        )
    ),
    CONSTRAINT jobs_inactive_lease_consistency CHECK (
        state IN ('leased', 'staged', 'executing', 'validating', 'queued')
        OR (lease_owner_agent_id IS NULL AND lease_expires_at IS NULL)
    ),
    CONSTRAINT jobs_terminal_time_consistency CHECK (
        (state IN ('succeeded', 'failed', 'cancelled', 'unknown_outcome')) =
        (completed_at IS NOT NULL)
    ),
    CONSTRAINT jobs_terminal_result_consistency CHECK (
        (
            state = 'succeeded'
            AND result_revision_id IS NOT NULL
            AND terminal_error_code IS NULL
        )
        OR (
            state IN ('failed', 'cancelled', 'unknown_outcome')
            AND result_revision_id IS NULL
            AND terminal_error_code IS NOT NULL
        )
        OR (
            state NOT IN ('succeeded', 'failed', 'cancelled', 'unknown_outcome')
            AND result_revision_id IS NULL
            AND terminal_error_code IS NULL
        )
    ),
    CONSTRAINT jobs_error_code_format CHECK (
        terminal_error_code IS NULL OR terminal_error_code ~ '^[A-Z][A-Z0-9_]{2,63}$'
    ),
    CONSTRAINT jobs_time_order CHECK (
        updated_at >= created_at
        AND (lease_expires_at IS NULL OR lease_expires_at >= created_at)
        AND (cancellation_requested_at IS NULL OR cancellation_requested_at >= created_at)
        AND (completed_at IS NULL OR completed_at >= created_at)
    )
);

CREATE TABLE hwpx_agent.job_attempts (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    job_id uuid NOT NULL,
    attempt_no integer NOT NULL,
    execution_id uuid NOT NULL,
    agent_instance_id uuid NOT NULL,
    fencing_token bigint NOT NULL,
    state text NOT NULL,
    receipt_artifact_id uuid,
    started_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    completed_at timestamptz,
    PRIMARY KEY (tenant_id, project_id, job_id, attempt_no),
    UNIQUE (tenant_id, execution_id),
    CONSTRAINT job_attempts_job_fk FOREIGN KEY (tenant_id, project_id, job_id)
        REFERENCES hwpx_agent.jobs (tenant_id, project_id, job_id) ON DELETE RESTRICT,
    CONSTRAINT job_attempts_receipt_artifact_fk FOREIGN KEY (tenant_id, receipt_artifact_id)
        REFERENCES hwpx_agent.artifacts (tenant_id, artifact_id) ON DELETE RESTRICT,
    CONSTRAINT job_attempts_number_range CHECK (attempt_no BETWEEN 1 AND 100),
    CONSTRAINT job_attempts_fencing_range CHECK (fencing_token > 0),
    CONSTRAINT job_attempts_state_value CHECK (
        state IN ('leased', 'running', 'succeeded', 'failed', 'cancelled', 'unknown_outcome')
    ),
    CONSTRAINT job_attempts_terminal_time_consistency CHECK (
        (state IN ('succeeded', 'failed', 'cancelled', 'unknown_outcome')) =
        (completed_at IS NOT NULL)
    ),
    CONSTRAINT job_attempts_receipt_consistency CHECK (
        (state IN ('succeeded', 'failed', 'cancelled', 'unknown_outcome')) =
        (receipt_artifact_id IS NOT NULL)
    ),
    CONSTRAINT job_attempts_time_order CHECK (
        completed_at IS NULL OR completed_at >= started_at
    )
);

CREATE TABLE hwpx_agent.idempotency_records (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    idempotency_key uuid NOT NULL,
    request_sha256 character(64) NOT NULL,
    state text NOT NULL DEFAULT 'claimed',
    job_id uuid,
    result_revision_id uuid,
    receipt_artifact_id uuid,
    terminal_error_code text,
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    expires_at timestamptz NOT NULL,
    PRIMARY KEY (tenant_id, project_id, idempotency_key),
    CONSTRAINT idempotency_project_fk FOREIGN KEY (tenant_id, project_id)
        REFERENCES hwpx_agent.projects (tenant_id, project_id) ON DELETE RESTRICT,
    CONSTRAINT idempotency_job_fk FOREIGN KEY (tenant_id, project_id, job_id)
        REFERENCES hwpx_agent.jobs (tenant_id, project_id, job_id) ON DELETE RESTRICT,
    CONSTRAINT idempotency_result_revision_fk FOREIGN KEY (
        tenant_id, project_id, result_revision_id
    ) REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id) ON DELETE RESTRICT,
    CONSTRAINT idempotency_receipt_artifact_fk FOREIGN KEY (tenant_id, receipt_artifact_id)
        REFERENCES hwpx_agent.artifacts (tenant_id, artifact_id) ON DELETE RESTRICT,
    CONSTRAINT idempotency_request_digest_format CHECK (request_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT idempotency_state_value CHECK (
        state IN ('claimed', 'terminal_success', 'terminal_failure', 'unknown_outcome')
    ),
    CONSTRAINT idempotency_terminal_consistency CHECK (
        (state = 'claimed' AND result_revision_id IS NULL AND receipt_artifact_id IS NULL)
        OR (
            state = 'terminal_success'
            AND result_revision_id IS NOT NULL
            AND receipt_artifact_id IS NOT NULL
            AND terminal_error_code IS NULL
        )
        OR (
            state IN ('terminal_failure', 'unknown_outcome')
            AND result_revision_id IS NULL
            AND receipt_artifact_id IS NOT NULL
            AND terminal_error_code IS NOT NULL
        )
    ),
    CONSTRAINT idempotency_error_code_format CHECK (
        terminal_error_code IS NULL OR terminal_error_code ~ '^[A-Z][A-Z0-9_]{2,63}$'
    ),
    CONSTRAINT idempotency_time_order CHECK (
        updated_at >= created_at AND expires_at > created_at
    )
);

CREATE TABLE hwpx_agent.audit_events (
    audit_event_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id uuid NOT NULL,
    project_id uuid,
    event_type text NOT NULL,
    subject_sha256 character(64) NOT NULL,
    job_id uuid,
    revision_id uuid,
    payload_sha256 character(64) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT audit_events_tenant_fk FOREIGN KEY (tenant_id)
        REFERENCES hwpx_agent.tenants (tenant_id) ON DELETE RESTRICT,
    CONSTRAINT audit_events_project_fk FOREIGN KEY (tenant_id, project_id)
        REFERENCES hwpx_agent.projects (tenant_id, project_id) ON DELETE RESTRICT,
    CONSTRAINT audit_events_job_fk FOREIGN KEY (tenant_id, project_id, job_id)
        REFERENCES hwpx_agent.jobs (tenant_id, project_id, job_id) ON DELETE RESTRICT,
    CONSTRAINT audit_events_revision_fk FOREIGN KEY (tenant_id, project_id, revision_id)
        REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id) ON DELETE RESTRICT,
    CONSTRAINT audit_events_type_format CHECK (
        event_type ~ '^[a-z][a-z0-9]*(\.[a-z0-9_-]+)+$'
    ),
    CONSTRAINT audit_events_subject_format CHECK (subject_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT audit_events_payload_format CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT audit_events_optional_project_consistency CHECK (
        project_id IS NOT NULL OR (job_id IS NULL AND revision_id IS NULL)
    )
);

CREATE INDEX revisions_project_created_idx
    ON hwpx_agent.revisions (tenant_id, project_id, created_at DESC, revision_id);
CREATE UNIQUE INDEX branches_one_default_idx
    ON hwpx_agent.branches (tenant_id, project_id)
    WHERE is_default;
CREATE INDEX branches_head_revision_idx
    ON hwpx_agent.branches (tenant_id, project_id, head_revision_id)
    WHERE head_revision_id IS NOT NULL;
CREATE INDEX revision_parents_parent_idx
    ON hwpx_agent.revision_parents (tenant_id, project_id, parent_revision_id);
CREATE INDEX checkpoints_revision_idx
    ON hwpx_agent.checkpoints (tenant_id, project_id, revision_id);
CREATE INDEX jobs_queue_idx
    ON hwpx_agent.jobs (required_target_profile_id, required_capability_set_sha256, created_at, job_id)
    WHERE state = 'queued';
CREATE INDEX jobs_lease_expiry_idx
    ON hwpx_agent.jobs (lease_expires_at, tenant_id, project_id, job_id)
    WHERE state IN ('leased', 'staged', 'executing', 'validating');
CREATE INDEX artifacts_retention_idx
    ON hwpx_agent.artifacts (retention_until, tenant_id, artifact_id)
    WHERE retention_until IS NOT NULL;
CREATE INDEX idempotency_expiry_idx
    ON hwpx_agent.idempotency_records (expires_at, tenant_id, project_id, idempotency_key);
CREATE INDEX audit_events_project_time_idx
    ON hwpx_agent.audit_events (tenant_id, project_id, created_at DESC, audit_event_id);

CREATE TRIGGER tenants_touch_updated_at
BEFORE UPDATE ON hwpx_agent.tenants
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.touch_updated_at();
CREATE TRIGGER projects_touch_updated_at
BEFORE UPDATE ON hwpx_agent.projects
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.touch_updated_at();
CREATE TRIGGER branches_touch_updated_at
BEFORE UPDATE ON hwpx_agent.branches
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.touch_updated_at();
CREATE TRIGGER artifacts_protect_identity
BEFORE UPDATE ON hwpx_agent.artifacts
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.protect_artifact_identity();
CREATE TRIGGER artifacts_touch_updated_at
BEFORE UPDATE ON hwpx_agent.artifacts
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.touch_updated_at();
CREATE TRIGGER jobs_touch_updated_at
BEFORE UPDATE ON hwpx_agent.jobs
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.touch_updated_at();
CREATE TRIGGER jobs_protect_identity
BEFORE UPDATE ON hwpx_agent.jobs
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.protect_job_identity();
CREATE TRIGGER idempotency_protect_identity
BEFORE UPDATE ON hwpx_agent.idempotency_records
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.protect_idempotency_identity();
CREATE TRIGGER idempotency_touch_updated_at
BEFORE UPDATE ON hwpx_agent.idempotency_records
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.touch_updated_at();

CREATE TRIGGER revisions_immutable
BEFORE UPDATE OR DELETE ON hwpx_agent.revisions
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();
CREATE TRIGGER schema_versions_immutable
BEFORE UPDATE OR DELETE ON hwpx_agent.schema_versions
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();
CREATE TRIGGER revision_parents_immutable
BEFORE UPDATE OR DELETE ON hwpx_agent.revision_parents
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();
CREATE TRIGGER checkpoints_immutable
BEFORE UPDATE OR DELETE ON hwpx_agent.checkpoints
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();
CREATE TRIGGER job_attempts_protect_identity
BEFORE UPDATE ON hwpx_agent.job_attempts
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.protect_job_attempt_identity();
CREATE TRIGGER job_attempts_reject_delete
BEFORE DELETE ON hwpx_agent.job_attempts
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();
CREATE TRIGGER audit_events_immutable
BEFORE UPDATE OR DELETE ON hwpx_agent.audit_events
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();

DO $$
DECLARE
    table_name text;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'tenants', 'projects', 'branches', 'project_acl', 'artifacts', 'revisions',
        'revision_parents', 'checkpoints', 'jobs', 'job_attempts',
        'idempotency_records', 'audit_events'
    ] LOOP
        EXECUTE format('ALTER TABLE hwpx_agent.%I ENABLE ROW LEVEL SECURITY', table_name);
        EXECUTE format('ALTER TABLE hwpx_agent.%I FORCE ROW LEVEL SECURITY', table_name);
        EXECUTE format(
            'CREATE POLICY tenant_isolation ON hwpx_agent.%I '
            'USING (tenant_id = hwpx_agent.current_tenant_id()) '
            'WITH CHECK (tenant_id = hwpx_agent.current_tenant_id())',
            table_name
        );
    END LOOP;
END
$$;

REVOKE ALL ON ALL TABLES IN SCHEMA hwpx_agent FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA hwpx_agent FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA hwpx_agent FROM PUBLIC;

INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (
    1,
    'p14.metadata_v1',
    current_setting('hwpx_agent.migration_sha256')
);

COMMIT;
