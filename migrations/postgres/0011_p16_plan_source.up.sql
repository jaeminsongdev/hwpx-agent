BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 10 AND migration_name = 'p16.artifact_repository_v1')
        OR EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version >= 11) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'plan source requires exact schema version 10';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256', true) IS NULL
        OR current_setting('hwpx_agent.migration_sha256', true) !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'plan source requires its migration digest';
    END IF;
END
$$;

CREATE TABLE hwpx_agent.revision_graph_bindings (
    tenant_id uuid NOT NULL,
    project_id uuid NOT NULL,
    revision_id uuid NOT NULL,
    source_artifact_id uuid NOT NULL,
    graph_sha256 character(64) NOT NULL,
    created_by_subject_sha256 character(64) NOT NULL,
    sealed_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
    PRIMARY KEY (tenant_id, project_id, revision_id),
    UNIQUE (tenant_id, project_id, revision_id, source_artifact_id),
    CONSTRAINT revision_graph_bindings_revision_fk FOREIGN KEY (tenant_id, project_id, revision_id)
        REFERENCES hwpx_agent.revisions (tenant_id, project_id, revision_id) ON DELETE RESTRICT,
    CONSTRAINT revision_graph_bindings_source_fk FOREIGN KEY (tenant_id, source_artifact_id)
        REFERENCES hwpx_agent.artifacts (tenant_id, artifact_id) ON DELETE RESTRICT,
    CONSTRAINT revision_graph_bindings_graph_digest_format CHECK (graph_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT revision_graph_bindings_subject_format CHECK (
        created_by_subject_sha256 ~ '^[0-9a-f]{64}$'
    )
);

CREATE FUNCTION hwpx_agent.validate_revision_graph_binding()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM hwpx_agent.revisions AS revision
        JOIN hwpx_agent.revision_graph_seals AS seal
          ON seal.tenant_id = revision.tenant_id
         AND seal.project_id = revision.project_id
         AND seal.revision_id = revision.revision_id
        JOIN hwpx_agent.revision_commit_receipts AS receipt
          ON receipt.tenant_id = revision.tenant_id
         AND receipt.project_id = revision.project_id
         AND receipt.committed_revision_id = revision.revision_id
         AND receipt.commit_id = seal.commit_id
         AND receipt.committed_generation = seal.committed_generation
         AND receipt.commit_request_sha256 = seal.commit_request_sha256
         AND receipt.transaction_receipt_sha256 = seal.transaction_receipt_sha256
         AND receipt.subject_sha256 = NEW.created_by_subject_sha256
        JOIN hwpx_agent.artifacts AS artifact
          ON artifact.tenant_id = revision.tenant_id
         AND artifact.artifact_id = revision.source_artifact_id
        WHERE revision.tenant_id = NEW.tenant_id
          AND revision.project_id = NEW.project_id
          AND revision.revision_id = NEW.revision_id
          AND revision.source_artifact_id = NEW.source_artifact_id
          AND revision.created_by_subject_sha256 = NEW.created_by_subject_sha256
          AND seal.seal_kind = 'service_v1'
          AND artifact.artifact_kind = 'source'
          AND artifact.storage_state = 'available'
          AND artifact.validation_state = 'verified'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'revision graph binding requires the exact verified source artifact';
    END IF;
    RETURN NEW;
END
$$;

CREATE TRIGGER revision_graph_bindings_validate
BEFORE INSERT ON hwpx_agent.revision_graph_bindings
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.validate_revision_graph_binding();
CREATE TRIGGER revision_graph_bindings_immutable
BEFORE UPDATE OR DELETE ON hwpx_agent.revision_graph_bindings
FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();

ALTER TABLE hwpx_agent.revision_graph_bindings ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.revision_graph_bindings FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.revision_graph_bindings
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());
REVOKE ALL ON TABLE hwpx_agent.revision_graph_bindings FROM PUBLIC;
REVOKE ALL ON FUNCTION hwpx_agent.validate_revision_graph_binding() FROM PUBLIC;

INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (11, 'p16.plan_source_v1', current_setting('hwpx_agent.migration_sha256'));
COMMIT;
