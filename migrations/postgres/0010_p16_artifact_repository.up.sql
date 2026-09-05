BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 9 AND migration_name = 'p14.retention_local_mirror_v1')
        OR EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version >= 10) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'artifact repository requires exact schema version 9';
    END IF;
    IF current_setting('hwpx_agent.migration_sha256', true) IS NULL
        OR current_setting('hwpx_agent.migration_sha256', true) !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'artifact repository requires its migration digest';
    END IF;
END
$$;

-- Closed, content-free service audit projection. The general P14 digest-only audit log is unchanged.
CREATE TABLE hwpx_agent.artifact_service_audit (
    event_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id uuid NOT NULL,
    artifact_id uuid NOT NULL,
    event_type text NOT NULL CHECK (event_type IN (
        'artifact.ingested', 'artifact.metadata.read', 'artifact.download',
        'artifact.signed_url.issued', 'artifact.signed_url.redeemed',
        'artifact.acl.changed', 'artifact.quarantined', 'artifact.ingest.deduplicated'
    )),
    subject_sha256 character(64) NOT NULL CHECK (subject_sha256 ~ '^[0-9a-f]{64}$'),
    content_sha256 character(64) NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    outcome text NOT NULL CHECK (outcome IN ('allowed', 'denied', 'quarantined')),
    recorded_at_unix_seconds bigint NOT NULL CHECK (recorded_at_unix_seconds BETWEEN 0 AND 253402300799),
    CONSTRAINT artifact_service_audit_identity_fk FOREIGN KEY (tenant_id, artifact_id)
        REFERENCES hwpx_agent.artifacts(tenant_id, artifact_id) ON DELETE RESTRICT
);
CREATE INDEX artifact_service_audit_tenant_order_idx
    ON hwpx_agent.artifact_service_audit (tenant_id, event_id);
CREATE TRIGGER artifact_service_audit_immutable
    BEFORE UPDATE OR DELETE ON hwpx_agent.artifact_service_audit
    FOR EACH ROW EXECUTE FUNCTION hwpx_agent.reject_immutable_change();
ALTER TABLE hwpx_agent.artifact_service_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE hwpx_agent.artifact_service_audit FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON hwpx_agent.artifact_service_audit
    USING (tenant_id = hwpx_agent.current_tenant_id())
    WITH CHECK (tenant_id = hwpx_agent.current_tenant_id());
REVOKE ALL ON TABLE hwpx_agent.artifact_service_audit FROM PUBLIC;
REVOKE ALL ON SEQUENCE hwpx_agent.artifact_service_audit_event_id_seq FROM PUBLIC;

INSERT INTO hwpx_agent.schema_versions (version, migration_name, migration_sha256)
VALUES (10, 'p16.artifact_repository_v1', current_setting('hwpx_agent.migration_sha256'));
COMMIT;
