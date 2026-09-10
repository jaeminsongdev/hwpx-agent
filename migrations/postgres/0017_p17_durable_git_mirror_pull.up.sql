BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 16 AND migration_name = 'p17.durable_git_mirror_push_v1'
    ) OR EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version >= 17) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P17 durable Git mirror pull requires exact schema version 16';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256', true) IS NULL
       OR current_setting('hwpx_agent.migration_sha256', true) !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            MESSAGE = 'P17 durable Git mirror pull requires its migration digest';
    END IF;
END
$$;

ALTER TABLE hwpx_agent.project_local_mirrors
    ADD COLUMN observed_snapshot_sha256 character(64);

UPDATE hwpx_agent.project_local_mirrors AS mirror
SET observed_snapshot_sha256 = CASE
    WHEN mirror.observed_revision_id IS NULL THEN mirror.snapshot_sha256
    ELSE (
        SELECT artifact.content_sha256
        FROM hwpx_agent.revisions AS revision
        JOIN hwpx_agent.artifacts AS artifact
          ON artifact.tenant_id = revision.tenant_id
         AND artifact.artifact_id = revision.result_artifact_id
        WHERE revision.tenant_id = mirror.tenant_id
          AND revision.project_id = mirror.project_id
          AND revision.revision_id = mirror.observed_revision_id
          AND revision.validation_state = 'verified'
          AND artifact.storage_state = 'available'
          AND artifact.validation_state = 'verified'
    )
END;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM hwpx_agent.project_local_mirrors
        WHERE observed_snapshot_sha256 IS NULL
           OR observed_snapshot_sha256 !~ '^[0-9a-f]{64}$'
           OR observed_snapshot_sha256 = repeat('0', 64)
           OR (state = 'clean' AND snapshot_sha256 <> observed_snapshot_sha256)
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P17 durable Git mirror pull cannot prove existing observed snapshots';
    END IF;
END
$$;

CREATE FUNCTION hwpx_agent.bind_local_mirror_observed_snapshot_v1()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_snapshot_sha256 character(64);
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.observed_snapshot_sha256 IS NULL THEN
            IF NEW.state = 'clean' OR NEW.observed_revision_id IS NULL THEN
                NEW.observed_snapshot_sha256 := NEW.snapshot_sha256;
            ELSE
                SELECT artifact.content_sha256 INTO v_snapshot_sha256
                FROM hwpx_agent.revisions AS revision
                JOIN hwpx_agent.artifacts AS artifact
                  ON artifact.tenant_id = revision.tenant_id
                 AND artifact.artifact_id = revision.result_artifact_id
                WHERE revision.tenant_id = NEW.tenant_id
                  AND revision.project_id = NEW.project_id
                  AND revision.revision_id = NEW.observed_revision_id
                  AND revision.validation_state = 'verified'
                  AND artifact.storage_state = 'available'
                  AND artifact.validation_state = 'verified';
                NEW.observed_snapshot_sha256 := v_snapshot_sha256;
            END IF;
        END IF;
    ELSIF ROW(NEW.branch_id, NEW.observed_revision_id, NEW.observed_generation)
          IS DISTINCT FROM ROW(OLD.branch_id, OLD.observed_revision_id, OLD.observed_generation) THEN
        IF NEW.state = 'clean' THEN
            NEW.observed_snapshot_sha256 := NEW.snapshot_sha256;
        ELSIF NEW.observed_revision_id IS NOT NULL THEN
            SELECT artifact.content_sha256 INTO v_snapshot_sha256
            FROM hwpx_agent.revisions AS revision
            JOIN hwpx_agent.artifacts AS artifact
              ON artifact.tenant_id = revision.tenant_id
             AND artifact.artifact_id = revision.result_artifact_id
            WHERE revision.tenant_id = NEW.tenant_id
              AND revision.project_id = NEW.project_id
              AND revision.revision_id = NEW.observed_revision_id
              AND revision.validation_state = 'verified'
              AND artifact.storage_state = 'available'
              AND artifact.validation_state = 'verified';
            NEW.observed_snapshot_sha256 := v_snapshot_sha256;
        ELSIF OLD.observed_generation = 0 AND NEW.observed_generation = 0 THEN
            NEW.observed_snapshot_sha256 := OLD.observed_snapshot_sha256;
        ELSE
            RAISE EXCEPTION USING
                ERRCODE = '55000', MESSAGE = 'MIRROR_OBSERVED_SNAPSHOT_UNAVAILABLE';
        END IF;
    ELSIF NEW.state = 'clean' THEN
        NEW.observed_snapshot_sha256 := NEW.snapshot_sha256;
    END IF;
    IF NEW.observed_snapshot_sha256 IS NULL
       OR NEW.observed_snapshot_sha256 !~ '^[0-9a-f]{64}$'
       OR NEW.observed_snapshot_sha256 = repeat('0', 64) THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023', MESSAGE = 'MIRROR_OBSERVED_SNAPSHOT_INVALID';
    END IF;
    RETURN NEW;
END
$$;

CREATE TRIGGER local_mirror_observed_snapshot_binding
BEFORE INSERT OR UPDATE ON hwpx_agent.project_local_mirrors
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.bind_local_mirror_observed_snapshot_v1();

ALTER TABLE hwpx_agent.project_local_mirrors
    ALTER COLUMN observed_snapshot_sha256 SET NOT NULL,
    ADD CONSTRAINT local_mirror_observed_snapshot_format CHECK (
        observed_snapshot_sha256 ~ '^[0-9a-f]{64}$'
        AND observed_snapshot_sha256 <> repeat('0', 64)
    ),
    ADD CONSTRAINT local_mirror_clean_snapshot_binding CHECK (
        state <> 'clean' OR snapshot_sha256 = observed_snapshot_sha256
    );

CREATE TABLE hwpx_agent.git_mirror_pull_observations (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    branch_id uuid NOT NULL,
    mirror_id uuid NOT NULL,
    observation_id uuid NOT NULL,
    subject_sha256 character(64) NOT NULL,
    request_sha256 character(64) NOT NULL,
    observed_revision_id uuid,
    observed_generation bigint NOT NULL,
    observed_snapshot_sha256 character(64) NOT NULL,
    remote_revision_id uuid,
    remote_generation bigint NOT NULL,
    remote_snapshot_sha256 character(64) NOT NULL,
    remote_git_oid text,
    remote_git_state_sha256 character(64),
    outcome text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, project_id, observation_id),
    UNIQUE (tenant_id, project_id, subject_sha256, request_sha256),
    CONSTRAINT git_mirror_pull_mirror_fk FOREIGN KEY (tenant_id, mirror_id)
        REFERENCES hwpx_agent.project_local_mirrors (tenant_id, mirror_id) ON DELETE RESTRICT,
    CONSTRAINT git_mirror_pull_branch_fk FOREIGN KEY (tenant_id, project_id, branch_id)
        REFERENCES hwpx_agent.branches (tenant_id, project_id, branch_id) ON DELETE RESTRICT,
    CONSTRAINT git_mirror_pull_observed_revision_fk FOREIGN KEY (
        tenant_id, project_id, observed_revision_id
    ) REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id) ON DELETE RESTRICT,
    CONSTRAINT git_mirror_pull_remote_revision_fk FOREIGN KEY (
        tenant_id, project_id, remote_revision_id
    ) REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id) ON DELETE RESTRICT,
    CONSTRAINT git_mirror_pull_identity CHECK (
        observation_id <> '00000000-0000-0000-0000-000000000000'::uuid
        AND subject_sha256 ~ '^[0-9a-f]{64}$'
        AND request_sha256 ~ '^[0-9a-f]{64}$'
        AND observed_snapshot_sha256 ~ '^[0-9a-f]{64}$'
        AND observed_snapshot_sha256 <> repeat('0', 64)
        AND remote_snapshot_sha256 ~ '^[0-9a-f]{64}$'
        AND remote_snapshot_sha256 <> repeat('0', 64)
        AND (remote_git_state_sha256 IS NULL
            OR remote_git_state_sha256 ~ '^[0-9a-f]{64}$')
    ),
    CONSTRAINT git_mirror_pull_observed_head CHECK (
        (observed_revision_id IS NULL AND observed_generation = 0)
        OR (observed_revision_id IS NOT NULL AND observed_generation > 0)
    ),
    CONSTRAINT git_mirror_pull_remote_head CHECK (
        (remote_revision_id IS NULL AND remote_generation = 0
            AND remote_git_oid IS NULL AND remote_git_state_sha256 IS NULL)
        OR (remote_revision_id IS NOT NULL AND remote_generation > 0
            AND remote_git_oid ~ '^[0-9a-f]{40}([0-9a-f]{24})?$'
            AND remote_git_state_sha256 ~ '^[0-9a-f]{64}$')
    ),
    CONSTRAINT git_mirror_pull_outcome CHECK (
        (outcome = 'unchanged'
            AND ROW(remote_revision_id, remote_generation, remote_snapshot_sha256)
                IS NOT DISTINCT FROM
                ROW(observed_revision_id, observed_generation, observed_snapshot_sha256))
        OR (outcome IN ('updated', 'conflict')
            AND remote_revision_id IS NOT NULL
            AND remote_generation > observed_generation)
    )
);

ALTER TABLE hwpx_agent.git_mirror_pull_observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.git_mirror_pull_observations FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.git_mirror_pull_observations
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());

CREATE FUNCTION hwpx_agent.guard_git_mirror_pull_observation_v1()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    RAISE EXCEPTION USING
        ERRCODE = '55000', MESSAGE = 'GIT_MIRROR_PULL_OBSERVATION_IMMUTABLE';
END
$$;

CREATE TRIGGER git_mirror_pull_observation_guard
BEFORE UPDATE OR DELETE ON hwpx_agent.git_mirror_pull_observations
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.guard_git_mirror_pull_observation_v1();

CREATE FUNCTION hwpx_agent.reconcile_git_mirror_pull_v1(
    p_tenant_id uuid,
    p_project_id uuid,
    p_subject_sha256 character(64),
    p_branch_id uuid,
    p_mirror_id uuid,
    p_observation_id uuid,
    p_request_sha256 character(64),
    p_observed_revision_id uuid,
    p_observed_generation bigint,
    p_observed_snapshot_sha256 character(64),
    p_remote_revision_id uuid,
    p_remote_generation bigint,
    p_remote_snapshot_sha256 character(64),
    p_remote_git_oid text,
    p_remote_git_state_sha256 character(64)
)
RETURNS TABLE (
    outcome text,
    revision_id uuid,
    generation bigint,
    snapshot_sha256 character(64),
    replayed boolean
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, hwpx_agent
AS $$
DECLARE
    v_existing hwpx_agent.git_mirror_pull_observations%ROWTYPE;
    v_mirror hwpx_agent.project_local_mirrors%ROWTYPE;
    v_branch hwpx_agent.branches%ROWTYPE;
    v_remote_snapshot character(64);
    v_observed_snapshot character(64);
    v_is_ancestor boolean;
    v_outcome text;
BEGIN
    PERFORM hwpx_agent.require_retention_role_v1(
        p_tenant_id, p_project_id, p_subject_sha256, false
    );
    IF p_observation_id = '00000000-0000-0000-0000-000000000000'::uuid
       OR p_request_sha256 !~ '^[0-9a-f]{64}$'
       OR p_observed_snapshot_sha256 !~ '^[0-9a-f]{64}$'
       OR p_observed_snapshot_sha256 = repeat('0', 64)
       OR (p_observed_revision_id IS NULL) <> (p_observed_generation = 0)
       OR (p_remote_revision_id IS NULL) <> (p_remote_generation = 0)
       OR p_remote_snapshot_sha256 !~ '^[0-9a-f]{64}$'
       OR p_remote_snapshot_sha256 = repeat('0', 64)
       OR ((p_remote_generation = 0) <> (
            p_remote_git_oid IS NULL AND p_remote_git_state_sha256 IS NULL
       ))
       OR (p_remote_generation > 0 AND (
            p_remote_git_oid !~ '^[0-9a-f]{40}([0-9a-f]{24})?$'
            OR p_remote_git_state_sha256 !~ '^[0-9a-f]{64}$'
       )) THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'GIT_MIRROR_PULL_REQUEST_INVALID';
    END IF;

    SELECT * INTO v_existing
    FROM hwpx_agent.git_mirror_pull_observations
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND subject_sha256 = p_subject_sha256
      AND request_sha256 = p_request_sha256;
    IF FOUND THEN
        IF ROW(
            v_existing.branch_id, v_existing.mirror_id, v_existing.observation_id,
            v_existing.observed_revision_id, v_existing.observed_generation,
            v_existing.observed_snapshot_sha256,
            v_existing.remote_revision_id, v_existing.remote_generation,
            v_existing.remote_snapshot_sha256,
            v_existing.remote_git_oid, v_existing.remote_git_state_sha256
        ) IS DISTINCT FROM ROW(
            p_branch_id, p_mirror_id, p_observation_id,
            p_observed_revision_id, p_observed_generation,
            p_observed_snapshot_sha256,
            p_remote_revision_id, p_remote_generation,
            p_remote_snapshot_sha256,
            p_remote_git_oid, p_remote_git_state_sha256
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'GIT_MIRROR_PULL_REPLAY_DRIFT';
        END IF;
        RETURN QUERY SELECT v_existing.outcome, v_existing.remote_revision_id,
            v_existing.remote_generation, v_existing.remote_snapshot_sha256, true;
        RETURN;
    END IF;

    SELECT * INTO v_mirror
    FROM hwpx_agent.project_local_mirrors
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND mirror_id = p_mirror_id
    FOR UPDATE;
    IF NOT FOUND OR v_mirror.branch_id <> p_branch_id
       OR v_mirror.state IN ('push_prepared', 'conflict', 'manual_merge_required')
       OR v_mirror.active_push_id IS NOT NULL
       OR ROW(v_mirror.observed_revision_id, v_mirror.observed_generation,
              v_mirror.observed_snapshot_sha256)
          IS DISTINCT FROM ROW(p_observed_revision_id, p_observed_generation,
                               p_observed_snapshot_sha256) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'GIT_MIRROR_PULL_MIRROR_DRIFT';
    END IF;

    SELECT * INTO v_branch
    FROM hwpx_agent.branches
    WHERE tenant_id = p_tenant_id AND project_id = p_project_id
      AND branch_id = p_branch_id
    FOR SHARE;
    IF NOT FOUND OR v_branch.head_generation < 0
       OR ROW(v_branch.head_revision_id, v_branch.head_generation)
          IS DISTINCT FROM ROW(p_remote_revision_id, p_remote_generation) THEN
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'GIT_MIRROR_PULL_REMOTE_DRIFT';
    END IF;

    IF p_remote_generation = 0 THEN
        v_remote_snapshot := p_observed_snapshot_sha256;
    ELSE
        SELECT artifact.content_sha256 INTO v_remote_snapshot
        FROM hwpx_agent.revisions AS revision
        JOIN hwpx_agent.artifacts AS artifact
          ON artifact.tenant_id = revision.tenant_id
         AND artifact.artifact_id = revision.result_artifact_id
        JOIN hwpx_agent.artifact_acl AS acl
          ON acl.tenant_id = artifact.tenant_id
         AND acl.artifact_id = artifact.artifact_id
         AND acl.subject_sha256 = p_subject_sha256
         AND (acl.can_read OR acl.can_manage)
        WHERE revision.tenant_id = p_tenant_id
          AND revision.project_id = p_project_id
          AND revision.revision_id = p_remote_revision_id
          AND revision.validation_state = 'verified'
          AND artifact.storage_state = 'available'
          AND artifact.validation_state = 'verified';
    END IF;
    IF v_remote_snapshot IS NULL
       OR v_remote_snapshot IS DISTINCT FROM p_remote_snapshot_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'GIT_MIRROR_PULL_REMOTE_STATE_DRIFT';
    END IF;

    IF p_observed_generation > 0 THEN
        SELECT artifact.content_sha256 INTO v_observed_snapshot
        FROM hwpx_agent.revisions AS revision
        JOIN hwpx_agent.artifacts AS artifact
          ON artifact.tenant_id = revision.tenant_id
         AND artifact.artifact_id = revision.result_artifact_id
        WHERE revision.tenant_id = p_tenant_id
          AND revision.project_id = p_project_id
          AND revision.revision_id = p_observed_revision_id
          AND revision.validation_state = 'verified'
          AND artifact.storage_state = 'available'
          AND artifact.validation_state = 'verified';
        IF v_observed_snapshot IS DISTINCT FROM p_observed_snapshot_sha256 THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'GIT_MIRROR_PULL_OBSERVED_STATE_DRIFT';
        END IF;
    END IF;

    IF p_remote_generation < p_observed_generation
       OR (p_remote_generation = p_observed_generation
           AND p_remote_revision_id IS DISTINCT FROM p_observed_revision_id) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'GIT_MIRROR_PULL_NONFORWARD_HEAD';
    END IF;

    IF p_remote_generation > p_observed_generation THEN
        WITH RECURSIVE chain(revision_id, generation) AS (
            SELECT p_remote_revision_id, p_remote_generation
            UNION ALL
            SELECT receipt.previous_revision_id, receipt.expected_generation
            FROM chain
            JOIN hwpx_agent.revision_commit_receipts AS receipt
              ON receipt.tenant_id = p_tenant_id
             AND receipt.project_id = p_project_id
             AND receipt.branch_id = p_branch_id
             AND receipt.committed_revision_id = chain.revision_id
             AND receipt.committed_generation = chain.generation
            WHERE chain.generation > p_observed_generation
        )
        SELECT EXISTS (
            SELECT 1 FROM chain
            WHERE chain.generation = p_observed_generation
              AND chain.revision_id IS NOT DISTINCT FROM p_observed_revision_id
        ) INTO v_is_ancestor;
        IF NOT COALESCE(v_is_ancestor, false) THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'GIT_MIRROR_PULL_ANCESTRY_DRIFT';
        END IF;
    END IF;

    IF p_remote_generation = p_observed_generation THEN
        IF p_remote_snapshot_sha256 <> p_observed_snapshot_sha256 THEN
            RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'GIT_MIRROR_PULL_SAME_HEAD_DRIFT';
        END IF;
        v_outcome := 'unchanged';
    ELSIF v_mirror.state = 'clean' THEN
        UPDATE hwpx_agent.project_local_mirrors
        SET observed_revision_id = p_remote_revision_id,
            observed_generation = p_remote_generation,
            observed_snapshot_sha256 = p_remote_snapshot_sha256,
            snapshot_sha256 = p_remote_snapshot_sha256,
            updated_at = transaction_timestamp()
        WHERE tenant_id = p_tenant_id AND mirror_id = p_mirror_id;
        v_outcome := 'updated';
    ELSIF v_mirror.state = 'ahead' THEN
        INSERT INTO hwpx_agent.local_mirror_conflicts (
            tenant_id, project_id, mirror_id, conflict_id,
            observed_revision_id, observed_generation,
            current_revision_id, current_generation
        ) VALUES (
            p_tenant_id, p_project_id, p_mirror_id, p_observation_id,
            p_observed_revision_id, p_observed_generation,
            p_remote_revision_id, p_remote_generation
        );
        UPDATE hwpx_agent.project_local_mirrors
        SET state = 'conflict', updated_at = transaction_timestamp()
        WHERE tenant_id = p_tenant_id AND mirror_id = p_mirror_id;
        v_outcome := 'conflict';
    ELSE
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'GIT_MIRROR_PULL_STATE_INVALID';
    END IF;

    INSERT INTO hwpx_agent.git_mirror_pull_observations (
        tenant_id, project_id, branch_id, mirror_id, observation_id,
        subject_sha256, request_sha256,
        observed_revision_id, observed_generation, observed_snapshot_sha256,
        remote_revision_id, remote_generation, remote_snapshot_sha256,
        remote_git_oid, remote_git_state_sha256, outcome
    ) VALUES (
        p_tenant_id, p_project_id, p_branch_id, p_mirror_id, p_observation_id,
        p_subject_sha256, p_request_sha256,
        p_observed_revision_id, p_observed_generation, p_observed_snapshot_sha256,
        p_remote_revision_id, p_remote_generation, p_remote_snapshot_sha256,
        p_remote_git_oid, p_remote_git_state_sha256, v_outcome
    );
    RETURN QUERY SELECT v_outcome, p_remote_revision_id, p_remote_generation,
        p_remote_snapshot_sha256, false;
END
$$;

REVOKE ALL ON TABLE hwpx_agent.git_mirror_pull_observations FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.bind_local_mirror_observed_snapshot_v1() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.guard_git_mirror_pull_observation_v1() FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.reconcile_git_mirror_pull_v1(
    uuid, uuid, character, uuid, uuid, uuid, character, uuid, bigint, character,
    uuid, bigint, character, text, character
) FROM PUBLIC;

INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (17, 'p17.durable_git_mirror_pull_v1',
        current_setting('hwpx_agent.migration_sha256'));

COMMIT;
