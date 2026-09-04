BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 8 AND migration_name = 'p14.cancel_cleanup_v1'
    ) OR EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version >= 9) THEN
        RAISE EXCEPTION USING ERRCODE = '55000',
            MESSAGE = 'P14 retention mirror migration requires exact schema version 8';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256', true) !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023',
            MESSAGE = 'P14 retention mirror migration requires its exact SHA-256';
    END IF;
END
$$;

ALTER TABLE hwpx_agent.artifacts
    DROP CONSTRAINT artifacts_storage_state_value,
    DROP CONSTRAINT artifacts_quarantine_consistency,
    DROP CONSTRAINT artifacts_service_metadata_complete_v8,
    DROP CONSTRAINT artifacts_object_key_binding_v8;

ALTER TABLE hwpx_agent.artifacts
    ADD CONSTRAINT artifacts_storage_state_value CHECK (
        storage_state IN (
            'staged', 'available', 'quarantined', 'orphaned', 'purging',
            'tombstoned', 'purged'
        )
    ),
    ADD CONSTRAINT artifacts_quarantine_consistency CHECK (
        (storage_state = 'quarantined' AND quarantine_reason_code IS NOT NULL)
        OR (storage_state <> 'quarantined' AND quarantine_reason_code IS NULL)
    ),
    ADD CONSTRAINT artifacts_service_metadata_complete_v9 CHECK (
        (
            service_metadata_version IS NULL
            AND filename IS NULL AND object_key IS NULL
            AND encryption_algorithm IS NULL AND encryption_nonce IS NULL
            AND aad_sha256 IS NULL AND ciphertext_sha256 IS NULL
            AND validation_state IS NULL AND scanner_engine_ref IS NULL
            AND scanner_signature_version IS NULL AND authorization_generation IS NULL
            AND storage_state IN ('staged', 'orphaned', 'purging')
        )
        OR (
            service_metadata_version = 1
            AND filename IS NOT NULL
            AND encryption_algorithm = 'AES-256-GCM'
            AND encryption_nonce IS NOT NULL
            AND aad_sha256 IS NOT NULL AND ciphertext_sha256 IS NOT NULL
            AND validation_state IS NOT NULL
            AND scanner_engine_ref IS NOT NULL
            AND scanner_signature_version IS NOT NULL
            AND authorization_generation IS NOT NULL
            AND (
                (
                    storage_state IN ('available', 'purging', 'tombstoned')
                    AND object_key IS NOT NULL AND validation_state = 'verified'
                )
                OR (
                    storage_state = 'quarantined' AND object_key IS NOT NULL
                    AND validation_state IN ('unverified', 'failed', 'quarantined')
                )
                OR (
                    storage_state = 'purged' AND object_key IS NULL
                    AND validation_state = 'verified'
                )
            )
        )
    ),
    ADD CONSTRAINT artifacts_object_key_binding_v9 CHECK (
        object_key IS NULL
        OR object_key = concat(
            'artifacts/v1/', replace(tenant_id::text, '-', ''), '/', artifact_kind, '/',
            CASE WHEN storage_state IN ('purging', 'tombstoned')
                THEN 'available' ELSE storage_state END,
            '/', content_sha256, '.aes256gcm'
        )
    );

CREATE TABLE hwpx_agent.retention_policies (
    tenant_id uuid NOT NULL,
    retention_policy_id text NOT NULL,
    tombstone_grace_seconds integer NOT NULL,
    created_by_subject_sha256 character(64) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, retention_policy_id),
    CONSTRAINT retention_policy_tenant_fk FOREIGN KEY (tenant_id)
        REFERENCES hwpx_agent.tenants (tenant_id) ON DELETE RESTRICT,
    CONSTRAINT retention_policy_id_format CHECK (
        char_length(retention_policy_id) BETWEEN 3 AND 128
        AND retention_policy_id ~ '^[a-z][a-z0-9]*(\.[a-z0-9_-]+)+$'
    ),
    CONSTRAINT retention_policy_grace_range CHECK (
        tombstone_grace_seconds BETWEEN 0 AND 604800
    ),
    CONSTRAINT retention_policy_subject_format CHECK (
        created_by_subject_sha256 ~ '^[0-9a-f]{64}$'
    )
);

CREATE TABLE hwpx_agent.retention_policy_rules (
    tenant_id uuid NOT NULL,
    retention_policy_id text NOT NULL,
    artifact_kind text NOT NULL,
    retention_seconds bigint NOT NULL,
    PRIMARY KEY (tenant_id, retention_policy_id, artifact_kind),
    CONSTRAINT retention_rule_policy_fk FOREIGN KEY (tenant_id, retention_policy_id)
        REFERENCES hwpx_agent.retention_policies (tenant_id, retention_policy_id)
        ON DELETE RESTRICT,
    CONSTRAINT retention_rule_kind CHECK (
        artifact_kind IN ('source', 'result', 'preview', 'evidence', 'trace', 'diff', 'receipt')
    ),
    CONSTRAINT retention_rule_seconds CHECK (
        retention_seconds BETWEEN 1 AND 315360000
    )
);

CREATE TABLE hwpx_agent.legal_holds (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    legal_hold_id uuid NOT NULL,
    artifact_id uuid,
    reason_code text NOT NULL,
    state text NOT NULL DEFAULT 'active',
    created_by_subject_sha256 character(64) NOT NULL,
    released_by_subject_sha256 character(64),
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    released_at timestamptz,
    PRIMARY KEY (tenant_id, legal_hold_id),
    CONSTRAINT legal_hold_project_fk FOREIGN KEY (tenant_id, project_id)
        REFERENCES hwpx_agent.projects (tenant_id, project_id) ON DELETE RESTRICT,
    CONSTRAINT legal_hold_artifact_fk FOREIGN KEY (tenant_id, artifact_id)
        REFERENCES hwpx_agent.artifacts (tenant_id, artifact_id) ON DELETE RESTRICT,
    CONSTRAINT legal_hold_identity CHECK (
        legal_hold_id <> '00000000-0000-0000-0000-000000000000'::uuid
        AND reason_code ~ '^[A-Z][A-Z0-9_]{2,63}$'
        AND created_by_subject_sha256 ~ '^[0-9a-f]{64}$'
        AND (released_by_subject_sha256 IS NULL
            OR released_by_subject_sha256 ~ '^[0-9a-f]{64}$')
    ),
    CONSTRAINT legal_hold_state CHECK (state IN ('active', 'released')),
    CONSTRAINT legal_hold_release_shape CHECK (
        (state = 'active' AND released_at IS NULL AND released_by_subject_sha256 IS NULL)
        OR (state = 'released' AND released_at IS NOT NULL
            AND released_by_subject_sha256 IS NOT NULL
            AND released_at >= created_at)
    )
);

CREATE UNIQUE INDEX legal_holds_active_project_idx
    ON hwpx_agent.legal_holds (tenant_id, project_id)
    WHERE state = 'active' AND artifact_id IS NULL;

CREATE UNIQUE INDEX legal_holds_active_artifact_idx
    ON hwpx_agent.legal_holds (tenant_id, project_id, artifact_id)
    WHERE state = 'active' AND artifact_id IS NOT NULL;

CREATE TABLE hwpx_agent.artifact_deletion_requests (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    artifact_id uuid NOT NULL,
    deletion_request_id uuid NOT NULL,
    retention_policy_id text NOT NULL,
    request_kind text NOT NULL,
    subject_sha256 character(64) NOT NULL,
    state text NOT NULL DEFAULT 'tombstoned',
    tombstoned_at timestamptz NOT NULL,
    purge_not_before timestamptz NOT NULL,
    attempt_count integer NOT NULL DEFAULT 0,
    lease_worker_id uuid,
    lease_execution_id uuid,
    lease_fencing_token bigint NOT NULL DEFAULT 0,
    lease_expires_at timestamptz,
    last_failure_sha256 character(64),
    completed_at timestamptz,
    PRIMARY KEY (tenant_id, deletion_request_id),
    UNIQUE (tenant_id, artifact_id),
    CONSTRAINT deletion_project_fk FOREIGN KEY (tenant_id, project_id)
        REFERENCES hwpx_agent.projects (tenant_id, project_id) ON DELETE RESTRICT,
    CONSTRAINT deletion_artifact_fk FOREIGN KEY (tenant_id, artifact_id)
        REFERENCES hwpx_agent.artifacts (tenant_id, artifact_id) ON DELETE RESTRICT,
    CONSTRAINT deletion_policy_fk FOREIGN KEY (tenant_id, retention_policy_id)
        REFERENCES hwpx_agent.retention_policies (tenant_id, retention_policy_id)
        ON DELETE RESTRICT,
    CONSTRAINT deletion_identity CHECK (
        deletion_request_id <> '00000000-0000-0000-0000-000000000000'::uuid
        AND subject_sha256 ~ '^[0-9a-f]{64}$'
        AND request_kind IN ('user_delete', 'policy_expiry')
    ),
    CONSTRAINT deletion_state CHECK (
        state IN ('tombstoned', 'leased', 'purged', 'failed_terminal')
    ),
    CONSTRAINT deletion_attempt_range CHECK (attempt_count BETWEEN 0 AND 3),
    CONSTRAINT deletion_failure_digest_format CHECK (
        last_failure_sha256 IS NULL OR last_failure_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT deletion_lease_shape CHECK (
        (state = 'tombstoned' AND attempt_count BETWEEN 0 AND 2
            AND lease_worker_id IS NULL AND lease_execution_id IS NULL
            AND lease_fencing_token = attempt_count AND lease_expires_at IS NULL
            AND completed_at IS NULL)
        OR (state = 'leased' AND attempt_count BETWEEN 1 AND 3
            AND lease_worker_id IS NOT NULL AND lease_execution_id IS NOT NULL
            AND lease_fencing_token = attempt_count AND lease_expires_at IS NOT NULL
            AND completed_at IS NULL)
        OR (state = 'purged' AND attempt_count BETWEEN 1 AND 3
            AND lease_worker_id IS NULL AND lease_execution_id IS NULL
            AND lease_fencing_token = attempt_count AND lease_expires_at IS NULL
            AND completed_at IS NOT NULL)
        OR (state = 'failed_terminal' AND attempt_count = 3
            AND lease_worker_id IS NULL AND lease_execution_id IS NULL
            AND lease_fencing_token = 3 AND lease_expires_at IS NULL
            AND completed_at IS NOT NULL)
    ),
    CONSTRAINT deletion_time_order CHECK (
        purge_not_before >= tombstoned_at
        AND (lease_expires_at IS NULL OR lease_expires_at > tombstoned_at)
        AND (completed_at IS NULL OR completed_at >= tombstoned_at)
    )
);

CREATE TABLE hwpx_agent.artifact_purge_receipts (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    artifact_id uuid NOT NULL,
    deletion_request_id uuid NOT NULL,
    purge_receipt_id uuid NOT NULL,
    outcome text NOT NULL,
    proof_sha256 character(64) NOT NULL,
    completed_at timestamptz NOT NULL,
    PRIMARY KEY (tenant_id, purge_receipt_id),
    UNIQUE (tenant_id, deletion_request_id),
    CONSTRAINT purge_receipt_request_fk FOREIGN KEY (tenant_id, deletion_request_id)
        REFERENCES hwpx_agent.artifact_deletion_requests (tenant_id, deletion_request_id)
        ON DELETE RESTRICT,
    CONSTRAINT purge_receipt_project_fk FOREIGN KEY (tenant_id, project_id)
        REFERENCES hwpx_agent.projects (tenant_id, project_id) ON DELETE RESTRICT,
    CONSTRAINT purge_receipt_artifact_fk FOREIGN KEY (tenant_id, artifact_id)
        REFERENCES hwpx_agent.artifacts (tenant_id, artifact_id) ON DELETE RESTRICT,
    CONSTRAINT purge_receipt_identity CHECK (
        purge_receipt_id <> '00000000-0000-0000-0000-000000000000'::uuid
        AND outcome IN ('object_deleted', 'object_already_absent')
        AND proof_sha256 ~ '^[0-9a-f]{64}$'
    )
);

CREATE TABLE hwpx_agent.project_local_mirrors (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    mirror_id uuid NOT NULL,
    device_sha256 character(64) NOT NULL,
    branch_id uuid NOT NULL,
    observed_revision_id uuid,
    observed_generation bigint NOT NULL,
    snapshot_sha256 character(64) NOT NULL,
    pending_plan_sha256 character(64),
    state text NOT NULL DEFAULT 'clean',
    active_push_id uuid,
    active_push_subject_sha256 character(64),
    active_push_expires_at timestamptz,
    created_by_subject_sha256 character(64) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, mirror_id),
    UNIQUE (tenant_id, project_id, device_sha256, branch_id),
    CONSTRAINT local_mirror_branch_fk FOREIGN KEY (tenant_id, project_id, branch_id)
        REFERENCES hwpx_agent.branches (tenant_id, project_id, branch_id) ON DELETE RESTRICT,
    CONSTRAINT local_mirror_revision_fk FOREIGN KEY (
        tenant_id, project_id, observed_revision_id
    ) REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id) ON DELETE RESTRICT,
    CONSTRAINT local_mirror_identity CHECK (
        mirror_id <> '00000000-0000-0000-0000-000000000000'::uuid
        AND device_sha256 ~ '^[0-9a-f]{64}$'
        AND snapshot_sha256 ~ '^[0-9a-f]{64}$'
        AND (pending_plan_sha256 IS NULL OR pending_plan_sha256 ~ '^[0-9a-f]{64}$')
        AND (active_push_subject_sha256 IS NULL
            OR active_push_subject_sha256 ~ '^[0-9a-f]{64}$')
        AND created_by_subject_sha256 ~ '^[0-9a-f]{64}$'
        AND ((observed_revision_id IS NULL AND observed_generation = 0)
            OR (observed_revision_id IS NOT NULL AND observed_generation > 0))
    ),
    CONSTRAINT local_mirror_state CHECK (
        state IN ('clean', 'ahead', 'push_prepared', 'conflict', 'manual_merge_required')
    ),
    CONSTRAINT local_mirror_state_shape CHECK (
        (state = 'clean' AND pending_plan_sha256 IS NULL
            AND active_push_id IS NULL AND active_push_subject_sha256 IS NULL
            AND active_push_expires_at IS NULL)
        OR (state = 'ahead' AND pending_plan_sha256 IS NOT NULL
            AND active_push_id IS NULL AND active_push_subject_sha256 IS NULL
            AND active_push_expires_at IS NULL)
        OR (state = 'push_prepared' AND pending_plan_sha256 IS NOT NULL
            AND active_push_id IS NOT NULL AND active_push_subject_sha256 IS NOT NULL
            AND active_push_expires_at IS NOT NULL)
        OR (state IN ('conflict', 'manual_merge_required')
            AND pending_plan_sha256 IS NOT NULL
            AND active_push_id IS NULL AND active_push_subject_sha256 IS NULL
            AND active_push_expires_at IS NULL)
    ),
    CONSTRAINT local_mirror_time_order CHECK (updated_at >= created_at)
);

CREATE UNIQUE INDEX local_mirror_push_reservation_idx
    ON hwpx_agent.project_local_mirrors (
        tenant_id, project_id, branch_id, observed_generation
    ) WHERE state = 'push_prepared';

CREATE UNIQUE INDEX local_mirror_active_push_identity_idx
    ON hwpx_agent.project_local_mirrors (tenant_id, project_id, active_push_id)
    WHERE active_push_id IS NOT NULL;

CREATE TABLE hwpx_agent.local_mirror_conflicts (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    mirror_id uuid NOT NULL,
    conflict_id uuid NOT NULL,
    observed_revision_id uuid,
    observed_generation bigint NOT NULL,
    current_revision_id uuid,
    current_generation bigint NOT NULL,
    resolution text,
    resolution_branch_id uuid,
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    resolved_at timestamptz,
    PRIMARY KEY (tenant_id, conflict_id),
    CONSTRAINT mirror_conflict_mirror_fk FOREIGN KEY (tenant_id, mirror_id)
        REFERENCES hwpx_agent.project_local_mirrors (tenant_id, mirror_id) ON DELETE RESTRICT,
    CONSTRAINT mirror_conflict_observed_revision_fk FOREIGN KEY (
        tenant_id, project_id, observed_revision_id
    ) REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id) ON DELETE RESTRICT,
    CONSTRAINT mirror_conflict_current_revision_fk FOREIGN KEY (
        tenant_id, project_id, current_revision_id
    ) REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id) ON DELETE RESTRICT,
    CONSTRAINT mirror_conflict_resolution_branch_fk FOREIGN KEY (
        tenant_id, project_id, resolution_branch_id
    ) REFERENCES hwpx_agent.branches (tenant_id, project_id, branch_id) ON DELETE RESTRICT,
    CONSTRAINT mirror_conflict_identity CHECK (
        conflict_id <> '00000000-0000-0000-0000-000000000000'::uuid
        AND ((observed_revision_id IS NULL AND observed_generation = 0)
            OR (observed_revision_id IS NOT NULL AND observed_generation > 0))
        AND ((current_revision_id IS NULL AND current_generation = 0)
            OR (current_revision_id IS NOT NULL AND current_generation > 0))
        AND ROW(observed_revision_id, observed_generation)
            IS DISTINCT FROM ROW(current_revision_id, current_generation)
    ),
    CONSTRAINT mirror_conflict_resolution CHECK (
        (resolution IS NULL AND resolution_branch_id IS NULL AND resolved_at IS NULL)
        OR (resolution = 'rebase_operation_plan'
            AND resolution_branch_id IS NULL AND resolved_at IS NOT NULL)
        OR (resolution = 'branch'
            AND resolution_branch_id IS NOT NULL AND resolved_at IS NOT NULL)
        OR (resolution = 'manual_merge'
            AND resolution_branch_id IS NULL AND resolved_at IS NOT NULL)
    )
);

CREATE UNIQUE INDEX local_mirror_open_conflict_idx
    ON hwpx_agent.local_mirror_conflicts (tenant_id, mirror_id)
    WHERE resolution IS NULL;

ALTER TABLE hwpx_agent.retention_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.retention_policies FORCE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.retention_policy_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.retention_policy_rules FORCE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.legal_holds ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.legal_holds FORCE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.artifact_deletion_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.artifact_deletion_requests FORCE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.artifact_purge_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.artifact_purge_receipts FORCE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.project_local_mirrors ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.project_local_mirrors FORCE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.local_mirror_conflicts ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.local_mirror_conflicts FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON hwpx_agent.retention_policies
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());
CREATE POLICY tenant_isolation ON hwpx_agent.retention_policy_rules
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());
CREATE POLICY tenant_isolation ON hwpx_agent.legal_holds
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());
CREATE POLICY tenant_isolation ON hwpx_agent.artifact_deletion_requests
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());
CREATE POLICY tenant_isolation ON hwpx_agent.artifact_purge_receipts
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());
CREATE POLICY tenant_isolation ON hwpx_agent.project_local_mirrors
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());
CREATE POLICY tenant_isolation ON hwpx_agent.local_mirror_conflicts
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());

CREATE FUNCTION hwpx_agent.protect_p14_09_identity()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'P14_09_RECORD_DELETE_FORBIDDEN';
    END IF;
    CASE TG_TABLE_NAME
        WHEN 'retention_policies' THEN
            IF ROW(
                NEW.tenant_id, NEW.retention_policy_id, NEW.tombstone_grace_seconds,
                NEW.created_by_subject_sha256, NEW.created_at
            ) IS DISTINCT FROM ROW(
                OLD.tenant_id, OLD.retention_policy_id, OLD.tombstone_grace_seconds,
                OLD.created_by_subject_sha256, OLD.created_at
            ) THEN
                RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'P14_09_IDENTITY_IMMUTABLE';
            END IF;
        WHEN 'retention_policy_rules' THEN
            IF ROW(
                NEW.tenant_id, NEW.retention_policy_id, NEW.artifact_kind,
                NEW.retention_seconds
            ) IS DISTINCT FROM ROW(
                OLD.tenant_id, OLD.retention_policy_id, OLD.artifact_kind,
                OLD.retention_seconds
            ) THEN
                RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'P14_09_IDENTITY_IMMUTABLE';
            END IF;
        WHEN 'legal_holds' THEN
            IF ROW(
                NEW.tenant_id, NEW.project_id, NEW.legal_hold_id, NEW.artifact_id,
                NEW.reason_code, NEW.created_by_subject_sha256, NEW.created_at
            ) IS DISTINCT FROM ROW(
                OLD.tenant_id, OLD.project_id, OLD.legal_hold_id, OLD.artifact_id,
                OLD.reason_code, OLD.created_by_subject_sha256, OLD.created_at
            ) THEN
                RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'P14_09_IDENTITY_IMMUTABLE';
            END IF;
        WHEN 'artifact_deletion_requests' THEN
            IF ROW(
                NEW.tenant_id, NEW.project_id, NEW.artifact_id, NEW.deletion_request_id,
                NEW.retention_policy_id, NEW.request_kind, NEW.subject_sha256,
                NEW.tombstoned_at, NEW.purge_not_before
            ) IS DISTINCT FROM ROW(
                OLD.tenant_id, OLD.project_id, OLD.artifact_id, OLD.deletion_request_id,
                OLD.retention_policy_id, OLD.request_kind, OLD.subject_sha256,
                OLD.tombstoned_at, OLD.purge_not_before
            ) THEN
                RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'P14_09_IDENTITY_IMMUTABLE';
            END IF;
        WHEN 'artifact_purge_receipts' THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'P14_09_IDENTITY_IMMUTABLE';
        WHEN 'project_local_mirrors' THEN
            IF ROW(
                NEW.tenant_id, NEW.project_id, NEW.mirror_id, NEW.device_sha256,
                NEW.created_by_subject_sha256, NEW.created_at
            ) IS DISTINCT FROM ROW(
                OLD.tenant_id, OLD.project_id, OLD.mirror_id, OLD.device_sha256,
                OLD.created_by_subject_sha256, OLD.created_at
            ) THEN
                RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'P14_09_IDENTITY_IMMUTABLE';
            END IF;
        WHEN 'local_mirror_conflicts' THEN
            IF ROW(
                NEW.tenant_id, NEW.project_id, NEW.mirror_id, NEW.conflict_id,
                NEW.observed_revision_id, NEW.observed_generation,
                NEW.current_revision_id, NEW.current_generation, NEW.created_at
            ) IS DISTINCT FROM ROW(
                OLD.tenant_id, OLD.project_id, OLD.mirror_id, OLD.conflict_id,
                OLD.observed_revision_id, OLD.observed_generation,
                OLD.current_revision_id, OLD.current_generation, OLD.created_at
            ) THEN
                RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'P14_09_IDENTITY_IMMUTABLE';
            END IF;
        ELSE
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'P14_09_TRIGGER_SCOPE_INVALID';
    END CASE;
    RETURN NEW;
END
$$;

CREATE TRIGGER retention_policies_protect
BEFORE UPDATE OR DELETE ON hwpx_agent.retention_policies
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.protect_p14_09_identity();
CREATE TRIGGER retention_policy_rules_protect
BEFORE UPDATE OR DELETE ON hwpx_agent.retention_policy_rules
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.protect_p14_09_identity();
CREATE TRIGGER legal_holds_protect
BEFORE UPDATE OR DELETE ON hwpx_agent.legal_holds
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.protect_p14_09_identity();
CREATE TRIGGER deletion_requests_protect
BEFORE UPDATE OR DELETE ON hwpx_agent.artifact_deletion_requests
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.protect_p14_09_identity();
CREATE TRIGGER purge_receipts_protect
BEFORE UPDATE OR DELETE ON hwpx_agent.artifact_purge_receipts
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.protect_p14_09_identity();
CREATE TRIGGER local_mirrors_protect
BEFORE UPDATE OR DELETE ON hwpx_agent.project_local_mirrors
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.protect_p14_09_identity();
CREATE TRIGGER mirror_conflicts_protect
BEFORE UPDATE OR DELETE ON hwpx_agent.local_mirror_conflicts
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.protect_p14_09_identity();

CREATE FUNCTION hwpx_agent.require_retention_role_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_owner_required boolean
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
BEGIN
    IF p_tenant_id <> hwpx_agent.current_tenant_id()
       OR p_subject_sha256 <> hwpx_agent.current_subject_sha256()
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$'
       OR NOT EXISTS (
            SELECT 1 FROM hwpx_agent.project_acl
            WHERE tenant_id = p_tenant_id AND project_id = p_project_id
              AND subject_sha256 = p_subject_sha256
              AND ((p_owner_required AND role = 'owner')
                OR (NOT p_owner_required AND role IN ('editor', 'owner')))
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'RETENTION_RESOURCE_NOT_FOUND';
    END IF;
END
$$;

CREATE FUNCTION hwpx_agent.has_active_legal_hold_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_artifact_id uuid
) RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
    SELECT EXISTS (
        SELECT 1 FROM hwpx_agent.legal_holds
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id
          AND state = 'active' AND (artifact_id IS NULL OR artifact_id = p_artifact_id)
    )
$$;

CREATE FUNCTION hwpx_agent.artifact_referenced_by_project_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_artifact_id uuid
) RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
    SELECT EXISTS (
        SELECT 1 FROM hwpx_agent.revisions
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id
          AND (source_artifact_id = p_artifact_id OR result_artifact_id = p_artifact_id
            OR semantic_diff_artifact_id = p_artifact_id)
        UNION ALL SELECT 1 FROM hwpx_agent.jobs
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id
          AND input_artifact_id = p_artifact_id
        UNION ALL SELECT 1 FROM hwpx_agent.job_attempts
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id
          AND receipt_artifact_id = p_artifact_id
        UNION ALL SELECT 1 FROM hwpx_agent.idempotency_records
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id
          AND receipt_artifact_id = p_artifact_id
        UNION ALL SELECT 1 FROM hwpx_agent.job_cancellation_requests
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id
          AND request_receipt_artifact_id = p_artifact_id
        UNION ALL SELECT 1 FROM hwpx_agent.cleanup_tasks
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id
          AND artifact_id = p_artifact_id
    )
$$;

CREATE FUNCTION hwpx_agent.artifact_referenced_outside_project_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_artifact_id uuid
) RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
    SELECT EXISTS (
        SELECT 1 FROM hwpx_agent.revisions
        WHERE tenant_id = p_tenant_id AND project_id <> p_project_id
          AND (source_artifact_id = p_artifact_id OR result_artifact_id = p_artifact_id
            OR semantic_diff_artifact_id = p_artifact_id)
        UNION ALL SELECT 1 FROM hwpx_agent.jobs
        WHERE tenant_id = p_tenant_id AND project_id <> p_project_id
          AND input_artifact_id = p_artifact_id
        UNION ALL SELECT 1 FROM hwpx_agent.job_attempts
        WHERE tenant_id = p_tenant_id AND project_id <> p_project_id
          AND receipt_artifact_id = p_artifact_id
        UNION ALL SELECT 1 FROM hwpx_agent.idempotency_records
        WHERE tenant_id = p_tenant_id AND project_id <> p_project_id
          AND receipt_artifact_id = p_artifact_id
        UNION ALL SELECT 1 FROM hwpx_agent.job_cancellation_requests
        WHERE tenant_id = p_tenant_id AND project_id <> p_project_id
          AND request_receipt_artifact_id = p_artifact_id
        UNION ALL SELECT 1 FROM hwpx_agent.cleanup_tasks
        WHERE tenant_id = p_tenant_id AND project_id <> p_project_id
          AND artifact_id = p_artifact_id
    )
$$;

CREATE FUNCTION hwpx_agent.guard_new_artifact_reference_v1()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
DECLARE
    v_artifact_ids uuid[];
    v_expected_count integer;
    v_available_count integer;
BEGIN
    IF TG_OP = 'UPDATE' THEN
        CASE TG_TABLE_NAME
            WHEN 'revisions' THEN
                IF ROW(NEW.source_artifact_id, NEW.result_artifact_id,
                       NEW.semantic_diff_artifact_id)
                   IS NOT DISTINCT FROM ROW(OLD.source_artifact_id, OLD.result_artifact_id,
                                             OLD.semantic_diff_artifact_id) THEN
                    RETURN NEW;
                END IF;
            WHEN 'jobs' THEN
                IF NEW.input_artifact_id IS NOT DISTINCT FROM OLD.input_artifact_id THEN
                    RETURN NEW;
                END IF;
            WHEN 'job_attempts' THEN
                IF NEW.receipt_artifact_id IS NOT DISTINCT FROM OLD.receipt_artifact_id THEN
                    RETURN NEW;
                END IF;
            WHEN 'idempotency_records' THEN
                IF NEW.receipt_artifact_id IS NOT DISTINCT FROM OLD.receipt_artifact_id THEN
                    RETURN NEW;
                END IF;
            WHEN 'job_cancellation_requests' THEN
                IF NEW.request_receipt_artifact_id
                   IS NOT DISTINCT FROM OLD.request_receipt_artifact_id THEN
                    RETURN NEW;
                END IF;
            WHEN 'cleanup_tasks' THEN
                IF NEW.artifact_id IS NOT DISTINCT FROM OLD.artifact_id THEN
                    RETURN NEW;
                END IF;
            ELSE
                RAISE EXCEPTION USING ERRCODE = '55000',
                    MESSAGE = 'RETENTION_REFERENCE_TRIGGER_SCOPE_INVALID';
        END CASE;
    END IF;
    CASE TG_TABLE_NAME
        WHEN 'revisions' THEN
            v_artifact_ids := array_remove(ARRAY[
                NEW.source_artifact_id, NEW.result_artifact_id,
                NEW.semantic_diff_artifact_id
            ], NULL);
        WHEN 'jobs' THEN v_artifact_ids := array_remove(ARRAY[NEW.input_artifact_id], NULL);
        WHEN 'job_attempts' THEN
            v_artifact_ids := array_remove(ARRAY[NEW.receipt_artifact_id], NULL);
        WHEN 'idempotency_records' THEN
            v_artifact_ids := array_remove(ARRAY[NEW.receipt_artifact_id], NULL);
        WHEN 'job_cancellation_requests' THEN
            v_artifact_ids := array_remove(ARRAY[NEW.request_receipt_artifact_id], NULL);
        WHEN 'cleanup_tasks' THEN
            v_artifact_ids := array_remove(ARRAY[NEW.artifact_id], NULL);
        ELSE
            RAISE EXCEPTION USING ERRCODE = '55000',
                MESSAGE = 'RETENTION_REFERENCE_TRIGGER_SCOPE_INVALID';
    END CASE;
    SELECT count(DISTINCT requested.artifact_id) INTO v_expected_count
    FROM unnest(v_artifact_ids) AS requested(artifact_id);
    IF v_expected_count = 0 THEN
        RETURN NEW;
    END IF;
    PERFORM 1 FROM hwpx_agent.artifacts
    WHERE tenant_id = NEW.tenant_id AND artifact_id = ANY(v_artifact_ids)
    ORDER BY artifact_id
    FOR SHARE;
    SELECT count(DISTINCT artifact_id) INTO v_available_count
    FROM hwpx_agent.artifacts
    WHERE tenant_id = NEW.tenant_id AND artifact_id = ANY(v_artifact_ids)
      AND storage_state NOT IN ('tombstoned', 'purged');
    IF v_available_count <> v_expected_count THEN
        RAISE EXCEPTION USING ERRCODE = '55000',
            MESSAGE = 'RETENTION_ARTIFACT_UNAVAILABLE';
    END IF;
    RETURN NEW;
END
$$;

CREATE TRIGGER revisions_retention_reference_guard
BEFORE INSERT OR UPDATE OF source_artifact_id, result_artifact_id, semantic_diff_artifact_id
ON hwpx_agent.revisions
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.guard_new_artifact_reference_v1();

CREATE TRIGGER jobs_retention_reference_guard
BEFORE INSERT OR UPDATE OF input_artifact_id ON hwpx_agent.jobs
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.guard_new_artifact_reference_v1();

CREATE TRIGGER job_attempts_retention_reference_guard
BEFORE INSERT OR UPDATE OF receipt_artifact_id ON hwpx_agent.job_attempts
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.guard_new_artifact_reference_v1();

CREATE TRIGGER idempotency_retention_reference_guard
BEFORE INSERT OR UPDATE OF receipt_artifact_id ON hwpx_agent.idempotency_records
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.guard_new_artifact_reference_v1();

CREATE TRIGGER cancellations_retention_reference_guard
BEFORE INSERT OR UPDATE OF request_receipt_artifact_id
ON hwpx_agent.job_cancellation_requests
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.guard_new_artifact_reference_v1();

CREATE TRIGGER cleanup_tasks_retention_reference_guard
BEFORE INSERT OR UPDATE OF artifact_id ON hwpx_agent.cleanup_tasks
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.guard_new_artifact_reference_v1();

CREATE FUNCTION hwpx_agent.create_retention_policy_v1(
    p_tenant_id uuid,
    p_retention_policy_id text,
    p_subject_sha256 character(64),
    p_tombstone_grace_seconds integer,
    p_source_seconds bigint,
    p_result_seconds bigint,
    p_preview_seconds bigint,
    p_evidence_seconds bigint,
    p_trace_seconds bigint,
    p_diff_seconds bigint,
    p_receipt_seconds bigint
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
BEGIN
    IF p_tenant_id <> hwpx_agent.current_tenant_id()
       OR p_subject_sha256 <> hwpx_agent.current_subject_sha256()
       OR p_subject_sha256 !~ '^[0-9a-f]{64}$'
       OR NOT EXISTS (
            SELECT 1 FROM hwpx_agent.project_acl
            WHERE tenant_id = p_tenant_id AND subject_sha256 = p_subject_sha256
              AND role = 'owner'
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'RETENTION_RESOURCE_NOT_FOUND';
    END IF;
    INSERT INTO hwpx_agent.retention_policies (
        tenant_id, retention_policy_id, tombstone_grace_seconds,
        created_by_subject_sha256
    ) VALUES (
        p_tenant_id, p_retention_policy_id, p_tombstone_grace_seconds,
        p_subject_sha256
    );
    INSERT INTO hwpx_agent.retention_policy_rules (
        tenant_id, retention_policy_id, artifact_kind, retention_seconds
    ) VALUES
        (p_tenant_id, p_retention_policy_id, 'source', p_source_seconds),
        (p_tenant_id, p_retention_policy_id, 'result', p_result_seconds),
        (p_tenant_id, p_retention_policy_id, 'preview', p_preview_seconds),
        (p_tenant_id, p_retention_policy_id, 'evidence', p_evidence_seconds),
        (p_tenant_id, p_retention_policy_id, 'trace', p_trace_seconds),
        (p_tenant_id, p_retention_policy_id, 'diff', p_diff_seconds),
        (p_tenant_id, p_retention_policy_id, 'receipt', p_receipt_seconds);
END
$$;

CREATE FUNCTION hwpx_agent.create_legal_hold_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_legal_hold_id uuid,
    p_artifact_id uuid,
    p_reason_code text
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
BEGIN
    PERFORM hwpx_agent.require_retention_role_v1(
        p_tenant_id, p_project_id, p_subject_sha256, true
    );
    PERFORM 1 FROM hwpx_agent.projects
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
    FOR UPDATE;
    IF p_artifact_id IS NOT NULL AND (
        NOT EXISTS (
            SELECT 1 FROM hwpx_agent.artifacts
            WHERE tenant_id = p_tenant_id AND artifact_id = p_artifact_id
              AND storage_state <> 'purged'
        ) OR NOT hwpx_agent.artifact_referenced_by_project_v1(
            p_tenant_id, p_project_id, p_artifact_id
        )
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '02000', MESSAGE = 'RETENTION_RESOURCE_NOT_FOUND';
    END IF;
    IF EXISTS (
        SELECT 1 FROM hwpx_agent.artifact_deletion_requests
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id
          AND (p_artifact_id IS NULL OR artifact_id = p_artifact_id)
          AND state = 'leased' AND lease_expires_at > clock_timestamp()
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RETENTION_PURGE_IN_PROGRESS';
    END IF;
    INSERT INTO hwpx_agent.legal_holds (
        tenant_id, project_id, legal_hold_id, artifact_id, reason_code,
        created_by_subject_sha256
    ) VALUES (
        p_tenant_id, p_project_id, p_legal_hold_id, p_artifact_id, p_reason_code,
        p_subject_sha256
    );
END
$$;

CREATE FUNCTION hwpx_agent.release_legal_hold_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_legal_hold_id uuid
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
BEGIN
    PERFORM hwpx_agent.require_retention_role_v1(
        p_tenant_id, p_project_id, p_subject_sha256, true
    );
    PERFORM 1 FROM hwpx_agent.projects
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
    FOR UPDATE;
    UPDATE hwpx_agent.legal_holds
    SET state = 'released', released_by_subject_sha256 = p_subject_sha256,
        released_at = transaction_timestamp()
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND legal_hold_id = p_legal_hold_id AND state = 'active';
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RETENTION_HOLD_CONFLICT';
    END IF;
END
$$;

CREATE FUNCTION hwpx_agent.request_artifact_deletion_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_artifact_id uuid,
    p_deletion_request_id uuid,
    p_request_kind text
) RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
DECLARE
    v_artifact hwpx_agent.artifacts%ROWTYPE;
    v_policy_id text;
    v_retention_seconds bigint;
    v_grace integer;
    v_due_at timestamptz;
    v_existing hwpx_agent.artifact_deletion_requests%ROWTYPE;
BEGIN
    PERFORM hwpx_agent.require_retention_role_v1(
        p_tenant_id, p_project_id, p_subject_sha256, true
    );
    PERFORM 1 FROM hwpx_agent.projects
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
    FOR UPDATE;
    IF p_request_kind NOT IN ('user_delete', 'policy_expiry') THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'RETENTION_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_existing
    FROM hwpx_agent.artifact_deletion_requests
    WHERE tenant_id = p_tenant_id AND deletion_request_id = p_deletion_request_id;
    IF FOUND THEN
        IF v_existing.project_id = p_project_id
           AND v_existing.artifact_id = p_artifact_id
           AND v_existing.subject_sha256 = p_subject_sha256
           AND v_existing.request_kind = p_request_kind THEN
            RETURN 'replay';
        END IF;
        RAISE EXCEPTION USING ERRCODE = '23505', MESSAGE = 'RETENTION_DELETE_CONFLICT';
    END IF;
    PERFORM 1 FROM hwpx_agent.artifact_deletion_requests
    WHERE tenant_id = p_tenant_id AND artifact_id = p_artifact_id;
    IF FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '23505', MESSAGE = 'RETENTION_DELETE_CONFLICT';
    END IF;
    SELECT * INTO v_artifact FROM hwpx_agent.artifacts
    WHERE tenant_id = p_tenant_id AND artifact_id = p_artifact_id
    FOR UPDATE;
    IF NOT FOUND OR v_artifact.service_metadata_version <> 1 THEN
        RAISE EXCEPTION USING ERRCODE = '02000', MESSAGE = 'RETENTION_RESOURCE_NOT_FOUND';
    END IF;
    IF v_artifact.storage_state <> 'available' OR v_artifact.validation_state <> 'verified' THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RETENTION_ARTIFACT_UNAVAILABLE';
    END IF;
    IF hwpx_agent.has_active_legal_hold_v1(p_tenant_id, p_project_id, p_artifact_id) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RETENTION_LEGAL_HOLD_ACTIVE';
    END IF;
    IF hwpx_agent.artifact_referenced_outside_project_v1(
        p_tenant_id, p_project_id, p_artifact_id
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RETENTION_ARTIFACT_SHARED';
    END IF;
    IF NOT hwpx_agent.artifact_referenced_by_project_v1(
        p_tenant_id, p_project_id, p_artifact_id
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '02000', MESSAGE = 'RETENTION_PROJECT_ARTIFACT_NOT_FOUND';
    END IF;
    SELECT project.retention_policy_id, policy.tombstone_grace_seconds,
           rule.retention_seconds
    INTO v_policy_id, v_grace, v_retention_seconds
    FROM hwpx_agent.projects AS project
    JOIN hwpx_agent.retention_policies AS policy
      ON policy.tenant_id = project.tenant_id
     AND policy.retention_policy_id = project.retention_policy_id
    JOIN hwpx_agent.retention_policy_rules AS rule
      ON rule.tenant_id = policy.tenant_id
     AND rule.retention_policy_id = policy.retention_policy_id
     AND rule.artifact_kind = v_artifact.artifact_kind
    WHERE project.tenant_id = p_tenant_id AND project.project_id = p_project_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RETENTION_POLICY_INCOMPLETE';
    END IF;
    v_due_at := GREATEST(
        v_artifact.created_at + make_interval(secs => v_retention_seconds),
        COALESCE(v_artifact.retention_until, v_artifact.created_at)
    );
    IF p_request_kind = 'policy_expiry' AND transaction_timestamp() < v_due_at THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RETENTION_NOT_DUE';
    END IF;
    INSERT INTO hwpx_agent.artifact_deletion_requests (
        tenant_id, project_id, artifact_id, deletion_request_id,
        retention_policy_id, request_kind, subject_sha256,
        tombstoned_at, purge_not_before
    ) VALUES (
        p_tenant_id, p_project_id, p_artifact_id, p_deletion_request_id,
        v_policy_id, p_request_kind, p_subject_sha256,
        transaction_timestamp(),
        transaction_timestamp() + make_interval(secs => v_grace)
    );
    UPDATE hwpx_agent.artifacts
    SET storage_state = 'tombstoned', authorization_generation = authorization_generation + 1,
        updated_at = transaction_timestamp()
    WHERE tenant_id = p_tenant_id AND artifact_id = p_artifact_id;
    RETURN 'tombstoned';
END
$$;

CREATE FUNCTION hwpx_agent.claim_artifact_purge_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_deletion_request_id uuid,
    p_worker_id uuid,
    p_execution_id uuid,
    p_lease_seconds integer
) RETURNS TABLE (
    returned_artifact_id uuid,
    returned_object_key text,
    returned_content_sha256 character(64),
    returned_attempt integer,
    returned_fencing_token bigint,
    returned_lease_expires_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
DECLARE
    v_request hwpx_agent.artifact_deletion_requests%ROWTYPE;
    v_now timestamptz := clock_timestamp();
BEGIN
    PERFORM hwpx_agent.require_retention_role_v1(
        p_tenant_id, p_project_id, p_subject_sha256, true
    );
    PERFORM 1 FROM hwpx_agent.projects
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
    FOR UPDATE;
    IF p_lease_seconds NOT BETWEEN 1 AND 300
       OR p_worker_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_execution_id = '00000000-0000-0000-0000-000000000000'::uuid THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'RETENTION_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_request FROM hwpx_agent.artifact_deletion_requests
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND deletion_request_id = p_deletion_request_id
    FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '02000', MESSAGE = 'RETENTION_RESOURCE_NOT_FOUND';
    END IF;
    IF hwpx_agent.has_active_legal_hold_v1(
        p_tenant_id, p_project_id, v_request.artifact_id
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RETENTION_LEGAL_HOLD_ACTIVE';
    END IF;
    IF hwpx_agent.artifact_referenced_outside_project_v1(
        p_tenant_id, p_project_id, v_request.artifact_id
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RETENTION_ARTIFACT_SHARED';
    END IF;
    IF v_now < v_request.purge_not_before THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RETENTION_NOT_DUE';
    END IF;
    IF v_request.state = 'leased' AND v_request.lease_expires_at > v_now THEN
        RAISE EXCEPTION USING ERRCODE = '55P03', MESSAGE = 'RETENTION_PURGE_BUSY';
    END IF;
    IF v_request.state NOT IN ('tombstoned', 'leased') OR v_request.attempt_count >= 3 THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RETENTION_PURGE_TERMINAL';
    END IF;
    UPDATE hwpx_agent.artifact_deletion_requests
    SET state = 'leased', attempt_count = v_request.attempt_count + 1,
        lease_worker_id = p_worker_id, lease_execution_id = p_execution_id,
        lease_fencing_token = v_request.attempt_count + 1,
        lease_expires_at = v_now + make_interval(secs => p_lease_seconds)
    WHERE tenant_id = p_tenant_id AND deletion_request_id = p_deletion_request_id;
    RETURN QUERY
    SELECT artifact.artifact_id, artifact.object_key, artifact.content_sha256,
           v_request.attempt_count + 1, (v_request.attempt_count + 1)::bigint,
           v_now + make_interval(secs => p_lease_seconds)
    FROM hwpx_agent.artifacts AS artifact
    WHERE artifact.tenant_id = p_tenant_id
      AND artifact.artifact_id = v_request.artifact_id
      AND artifact.storage_state = 'tombstoned';
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RETENTION_ARTIFACT_STATE_DRIFT';
    END IF;
END
$$;

CREATE FUNCTION hwpx_agent.record_artifact_purge_failure_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_deletion_request_id uuid,
    p_execution_id uuid,
    p_fencing_token bigint,
    p_failure_sha256 character(64)
) RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
DECLARE
    v_request hwpx_agent.artifact_deletion_requests%ROWTYPE;
    v_next_state text;
    v_now timestamptz := clock_timestamp();
BEGIN
    PERFORM hwpx_agent.require_retention_role_v1(
        p_tenant_id, p_project_id, p_subject_sha256, true
    );
    PERFORM 1 FROM hwpx_agent.projects
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
    FOR UPDATE;
    IF p_failure_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'RETENTION_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_request FROM hwpx_agent.artifact_deletion_requests
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND deletion_request_id = p_deletion_request_id
    FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '02000', MESSAGE = 'RETENTION_RESOURCE_NOT_FOUND';
    END IF;
    IF v_request.state <> 'leased' OR v_request.lease_execution_id <> p_execution_id
       OR v_request.lease_fencing_token <> p_fencing_token
       OR v_request.lease_expires_at <= v_now THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RETENTION_LEASE_STALE';
    END IF;
    v_next_state := CASE WHEN v_request.attempt_count = 3
        THEN 'failed_terminal' ELSE 'tombstoned' END;
    UPDATE hwpx_agent.artifact_deletion_requests
    SET state = v_next_state, lease_worker_id = NULL, lease_execution_id = NULL,
        lease_expires_at = NULL, last_failure_sha256 = p_failure_sha256,
        completed_at = CASE WHEN v_next_state = 'failed_terminal' THEN v_now ELSE NULL END
    WHERE tenant_id = p_tenant_id AND deletion_request_id = p_deletion_request_id;
    RETURN v_next_state;
END
$$;

CREATE FUNCTION hwpx_agent.complete_artifact_purge_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_deletion_request_id uuid,
    p_execution_id uuid,
    p_fencing_token bigint,
    p_purge_receipt_id uuid,
    p_outcome text,
    p_proof_sha256 character(64)
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
DECLARE
    v_request hwpx_agent.artifact_deletion_requests%ROWTYPE;
    v_now timestamptz := clock_timestamp();
BEGIN
    PERFORM hwpx_agent.require_retention_role_v1(
        p_tenant_id, p_project_id, p_subject_sha256, true
    );
    PERFORM 1 FROM hwpx_agent.projects
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
    FOR UPDATE;
    IF p_outcome NOT IN ('object_deleted', 'object_already_absent')
       OR p_proof_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'RETENTION_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_request FROM hwpx_agent.artifact_deletion_requests
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND deletion_request_id = p_deletion_request_id
    FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '02000', MESSAGE = 'RETENTION_RESOURCE_NOT_FOUND';
    END IF;
    IF hwpx_agent.has_active_legal_hold_v1(
        p_tenant_id, p_project_id, v_request.artifact_id
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RETENTION_LEGAL_HOLD_ACTIVE';
    END IF;
    IF hwpx_agent.artifact_referenced_outside_project_v1(
        p_tenant_id, p_project_id, v_request.artifact_id
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RETENTION_ARTIFACT_SHARED';
    END IF;
    IF v_request.state <> 'leased' OR v_request.lease_execution_id <> p_execution_id
       OR v_request.lease_fencing_token <> p_fencing_token
       OR v_request.lease_expires_at <= v_now THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RETENTION_LEASE_STALE';
    END IF;
    UPDATE hwpx_agent.artifacts
    SET storage_state = 'purged', object_key = NULL,
        authorization_generation = authorization_generation + 1,
        updated_at = v_now
    WHERE tenant_id = p_tenant_id AND artifact_id = v_request.artifact_id
      AND storage_state = 'tombstoned';
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RETENTION_ARTIFACT_STATE_DRIFT';
    END IF;
    UPDATE hwpx_agent.artifact_deletion_requests
    SET state = 'purged', lease_worker_id = NULL, lease_execution_id = NULL,
        lease_expires_at = NULL, completed_at = v_now
    WHERE tenant_id = p_tenant_id AND deletion_request_id = p_deletion_request_id;
    INSERT INTO hwpx_agent.artifact_purge_receipts (
        tenant_id, project_id, artifact_id, deletion_request_id,
        purge_receipt_id, outcome, proof_sha256, completed_at
    ) VALUES (
        p_tenant_id, p_project_id, v_request.artifact_id, p_deletion_request_id,
        p_purge_receipt_id, p_outcome, p_proof_sha256, v_now
    );
END
$$;

CREATE FUNCTION hwpx_agent.register_local_mirror_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_mirror_id uuid,
    p_device_sha256 character(64),
    p_branch_id uuid,
    p_observed_revision_id uuid,
    p_observed_generation bigint,
    p_snapshot_sha256 character(64)
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
DECLARE
    v_revision_id uuid;
    v_generation bigint;
BEGIN
    PERFORM hwpx_agent.require_retention_role_v1(
        p_tenant_id, p_project_id, p_subject_sha256, false
    );
    SELECT head_revision_id, head_generation INTO v_revision_id, v_generation
    FROM hwpx_agent.branches
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND branch_id = p_branch_id FOR SHARE;
    IF NOT FOUND OR ROW(v_revision_id, v_generation)
       IS DISTINCT FROM ROW(p_observed_revision_id, p_observed_generation)
       OR v_generation < 0 THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'MIRROR_REMOTE_HEAD_CONFLICT';
    END IF;
    INSERT INTO hwpx_agent.project_local_mirrors (
        tenant_id, project_id, mirror_id, device_sha256, branch_id,
        observed_revision_id, observed_generation, snapshot_sha256,
        created_by_subject_sha256
    ) VALUES (
        p_tenant_id, p_project_id, p_mirror_id, p_device_sha256, p_branch_id,
        p_observed_revision_id, p_observed_generation, p_snapshot_sha256,
        p_subject_sha256
    );
END
$$;

CREATE FUNCTION hwpx_agent.queue_local_mirror_plan_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_mirror_id uuid,
    p_snapshot_sha256 character(64),
    p_operation_plan_sha256 character(64)
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
BEGIN
    PERFORM hwpx_agent.require_retention_role_v1(
        p_tenant_id, p_project_id, p_subject_sha256, false
    );
    IF p_snapshot_sha256 !~ '^[0-9a-f]{64}$'
       OR p_operation_plan_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'MIRROR_REQUEST_INVALID';
    END IF;
    UPDATE hwpx_agent.project_local_mirrors
    SET snapshot_sha256 = p_snapshot_sha256,
        pending_plan_sha256 = p_operation_plan_sha256,
        state = 'ahead', updated_at = transaction_timestamp()
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND mirror_id = p_mirror_id AND state = 'clean';
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'MIRROR_STATE_CONFLICT';
    END IF;
END
$$;

CREATE FUNCTION hwpx_agent.begin_local_mirror_push_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_mirror_id uuid,
    p_push_id uuid,
    p_conflict_id uuid,
    p_lease_seconds integer
) RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
DECLARE
    v_mirror hwpx_agent.project_local_mirrors%ROWTYPE;
    v_revision_id uuid;
    v_generation bigint;
    v_now timestamptz := clock_timestamp();
BEGIN
    PERFORM hwpx_agent.require_retention_role_v1(
        p_tenant_id, p_project_id, p_subject_sha256, false
    );
    IF p_lease_seconds NOT BETWEEN 1 AND 300
       OR p_push_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_conflict_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_push_id = p_conflict_id THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'MIRROR_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_mirror FROM hwpx_agent.project_local_mirrors
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND mirror_id = p_mirror_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'MIRROR_STATE_CONFLICT';
    END IF;
    IF v_mirror.state = 'push_prepared'
       AND v_mirror.active_push_expires_at <= v_now THEN
        IF v_mirror.active_push_id = p_push_id THEN
            RAISE EXCEPTION USING ERRCODE = '55000',
                MESSAGE = 'MIRROR_PUSH_ID_CONFLICT';
        END IF;
        UPDATE hwpx_agent.project_local_mirrors
        SET state = 'ahead', active_push_id = NULL,
            active_push_subject_sha256 = NULL, active_push_expires_at = NULL,
            updated_at = v_now
        WHERE tenant_id = p_tenant_id AND mirror_id = p_mirror_id;
        v_mirror.state := 'ahead';
        v_mirror.active_push_id := NULL;
        v_mirror.active_push_subject_sha256 := NULL;
        v_mirror.active_push_expires_at := NULL;
    END IF;
    IF v_mirror.state <> 'ahead' THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'MIRROR_STATE_CONFLICT';
    END IF;
    SELECT head_revision_id, head_generation INTO v_revision_id, v_generation
    FROM hwpx_agent.branches
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND branch_id = v_mirror.branch_id FOR UPDATE;
    IF NOT FOUND OR v_generation < 0 THEN
        RAISE EXCEPTION USING ERRCODE = '02000', MESSAGE = 'MIRROR_BRANCH_NOT_FOUND';
    END IF;
    IF ROW(v_revision_id, v_generation)
       IS DISTINCT FROM ROW(v_mirror.observed_revision_id, v_mirror.observed_generation) THEN
        INSERT INTO hwpx_agent.local_mirror_conflicts (
            tenant_id, project_id, mirror_id, conflict_id,
            observed_revision_id, observed_generation,
            current_revision_id, current_generation
        ) VALUES (
            p_tenant_id, p_project_id, p_mirror_id, p_conflict_id,
            v_mirror.observed_revision_id, v_mirror.observed_generation,
            v_revision_id, v_generation
        );
        UPDATE hwpx_agent.project_local_mirrors
        SET state = 'conflict', updated_at = transaction_timestamp()
        WHERE tenant_id = p_tenant_id AND mirror_id = p_mirror_id;
        RETURN 'conflict';
    END IF;
    UPDATE hwpx_agent.project_local_mirrors
    SET state = 'push_prepared', active_push_id = p_push_id,
        active_push_subject_sha256 = p_subject_sha256,
        active_push_expires_at = v_now
            + make_interval(secs => p_lease_seconds),
        updated_at = v_now
    WHERE tenant_id = p_tenant_id AND mirror_id = p_mirror_id;
    RETURN 'prepared';
END
$$;

CREATE FUNCTION hwpx_agent.complete_local_mirror_push_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_mirror_id uuid,
    p_push_id uuid,
    p_committed_revision_id uuid
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
DECLARE
    v_mirror hwpx_agent.project_local_mirrors%ROWTYPE;
    v_revision_id uuid;
    v_generation bigint;
    v_plan_sha256 character(64);
BEGIN
    PERFORM hwpx_agent.require_retention_role_v1(
        p_tenant_id, p_project_id, p_subject_sha256, false
    );
    SELECT * INTO v_mirror FROM hwpx_agent.project_local_mirrors
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND mirror_id = p_mirror_id FOR UPDATE;
    IF NOT FOUND OR v_mirror.state <> 'push_prepared'
       OR v_mirror.active_push_id <> p_push_id
       OR v_mirror.active_push_subject_sha256 <> p_subject_sha256
       OR v_mirror.active_push_expires_at <= clock_timestamp() THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'MIRROR_PUSH_STALE';
    END IF;
    SELECT branch.head_revision_id, branch.head_generation,
           revision.operation_plan_sha256
    INTO v_revision_id, v_generation, v_plan_sha256
    FROM hwpx_agent.branches AS branch
    JOIN hwpx_agent.revisions AS revision
      ON revision.tenant_id = branch.tenant_id
     AND revision.project_id = branch.project_id
     AND revision.revision_id = branch.head_revision_id
    JOIN hwpx_agent.revision_commit_receipts AS receipt
      ON receipt.tenant_id = branch.tenant_id
     AND receipt.project_id = branch.project_id
     AND receipt.branch_id = branch.branch_id
     AND receipt.committed_revision_id = revision.revision_id
    WHERE branch.tenant_id = p_tenant_id AND branch.project_id = p_project_id
      AND branch.branch_id = v_mirror.branch_id
      AND receipt.commit_id = p_push_id
      AND receipt.previous_revision_id IS NOT DISTINCT FROM v_mirror.observed_revision_id
      AND receipt.expected_generation = v_mirror.observed_generation
      AND receipt.subject_sha256 = p_subject_sha256
    FOR SHARE OF branch, revision, receipt;
    IF NOT FOUND OR v_revision_id <> p_committed_revision_id
       OR v_generation <> v_mirror.observed_generation + 1 THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'MIRROR_REMOTE_HEAD_CONFLICT';
    END IF;
    IF v_plan_sha256 <> v_mirror.pending_plan_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'MIRROR_PLAN_MISMATCH';
    END IF;
    UPDATE hwpx_agent.project_local_mirrors
    SET observed_revision_id = v_revision_id, observed_generation = v_generation,
        pending_plan_sha256 = NULL, state = 'clean', active_push_id = NULL,
        active_push_subject_sha256 = NULL,
        active_push_expires_at = NULL, updated_at = transaction_timestamp()
    WHERE tenant_id = p_tenant_id AND mirror_id = p_mirror_id;
END
$$;

CREATE FUNCTION hwpx_agent.resolve_local_mirror_conflict_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_conflict_id uuid,
    p_resolution text,
    p_resolution_branch_id uuid
) RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $$
DECLARE
    v_conflict hwpx_agent.local_mirror_conflicts%ROWTYPE;
    v_mirror hwpx_agent.project_local_mirrors%ROWTYPE;
    v_revision_id uuid;
    v_generation bigint;
    v_state text;
BEGIN
    PERFORM hwpx_agent.require_retention_role_v1(
        p_tenant_id, p_project_id, p_subject_sha256, false
    );
    IF p_resolution NOT IN ('rebase_operation_plan', 'branch', 'manual_merge')
       OR (p_resolution = 'branch') <> (p_resolution_branch_id IS NOT NULL) THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'MIRROR_REQUEST_INVALID';
    END IF;
    SELECT * INTO v_conflict FROM hwpx_agent.local_mirror_conflicts
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND conflict_id = p_conflict_id FOR UPDATE;
    IF NOT FOUND OR v_conflict.resolution IS NOT NULL THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'MIRROR_CONFLICT_ALREADY_RESOLVED';
    END IF;
    SELECT * INTO v_mirror FROM hwpx_agent.project_local_mirrors
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND mirror_id = v_conflict.mirror_id
    FOR UPDATE;
    IF NOT FOUND OR v_mirror.state <> 'conflict' THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'MIRROR_STATE_CONFLICT';
    END IF;
    IF p_resolution = 'rebase_operation_plan' THEN
        v_revision_id := v_conflict.current_revision_id;
        v_generation := v_conflict.current_generation;
        v_state := 'ahead';
    ELSIF p_resolution = 'branch' THEN
        SELECT head_revision_id, head_generation INTO v_revision_id, v_generation
        FROM hwpx_agent.branches
        WHERE tenant_id = p_tenant_id AND project_id = p_project_id
          AND branch_id = p_resolution_branch_id FOR SHARE;
        IF NOT FOUND OR v_generation < 0 THEN
            RAISE EXCEPTION USING ERRCODE = '02000', MESSAGE = 'MIRROR_BRANCH_NOT_FOUND';
        END IF;
        v_state := 'ahead';
    ELSE
        v_revision_id := v_conflict.observed_revision_id;
        v_generation := v_conflict.observed_generation;
        v_state := 'manual_merge_required';
    END IF;
    UPDATE hwpx_agent.local_mirror_conflicts
    SET resolution = p_resolution, resolution_branch_id = p_resolution_branch_id,
        resolved_at = transaction_timestamp()
    WHERE tenant_id = p_tenant_id AND conflict_id = p_conflict_id;
    UPDATE hwpx_agent.project_local_mirrors
    SET branch_id = COALESCE(p_resolution_branch_id, branch_id),
        observed_revision_id = v_revision_id, observed_generation = v_generation,
        state = v_state, active_push_id = NULL,
        active_push_subject_sha256 = NULL, active_push_expires_at = NULL,
        updated_at = transaction_timestamp()
    WHERE tenant_id = p_tenant_id AND mirror_id = v_conflict.mirror_id;
    RETURN v_state;
END
$$;

REVOKE ALL ON TABLE
    hwpx_agent.retention_policies,
    hwpx_agent.retention_policy_rules,
    hwpx_agent.legal_holds,
    hwpx_agent.artifact_deletion_requests,
    hwpx_agent.artifact_purge_receipts,
    hwpx_agent.project_local_mirrors,
    hwpx_agent.local_mirror_conflicts
FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.protect_p14_09_identity() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.require_retention_role_v1(uuid, uuid, character, boolean) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.has_active_legal_hold_v1(uuid, uuid, uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.artifact_referenced_by_project_v1(uuid, uuid, uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.artifact_referenced_outside_project_v1(uuid, uuid, uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.guard_new_artifact_reference_v1() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.create_retention_policy_v1(uuid, text, character, integer, bigint, bigint, bigint, bigint, bigint, bigint, bigint) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.create_legal_hold_v1(uuid, uuid, character, uuid, uuid, text) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.release_legal_hold_v1(uuid, uuid, character, uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.request_artifact_deletion_v1(uuid, uuid, character, uuid, uuid, text) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.claim_artifact_purge_v1(uuid, uuid, character, uuid, uuid, uuid, integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.record_artifact_purge_failure_v1(uuid, uuid, character, uuid, uuid, bigint, character) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.complete_artifact_purge_v1(uuid, uuid, character, uuid, uuid, bigint, uuid, text, character) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.register_local_mirror_v1(uuid, uuid, character, uuid, character, uuid, uuid, bigint, character) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.queue_local_mirror_plan_v1(uuid, uuid, character, uuid, character, character) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.begin_local_mirror_push_v1(uuid, uuid, character, uuid, uuid, uuid, integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.complete_local_mirror_push_v1(uuid, uuid, character, uuid, uuid, uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.resolve_local_mirror_conflict_v1(uuid, uuid, character, uuid, text, uuid) FROM PUBLIC;

INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (
    9,
    'p14.retention_local_mirror_v1',
    current_setting('hwpx_agent.migration_sha256')::character(64)
);

COMMIT;
