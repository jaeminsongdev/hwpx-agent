BEGIN;
DO $$
BEGIN
    IF current_setting('hwpx_agent.allow_destructive_rollback', true) IS DISTINCT FROM 'on' THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'FULL_DOCUMENT_IR_ROLLBACK_REQUIRES_EXPLICIT_GATE';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version > 18)
        OR NOT EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version = 18 AND migration_name = 'p09.full_document_ir_v1') THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'FULL_DOCUMENT_IR_ROLLBACK_REQUIRES_SCHEMA_18';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.revisions WHERE full_document_ir_artifact_id IS NOT NULL)
        OR EXISTS (SELECT 1 FROM hwpx_agent.artifacts WHERE artifact_kind = 'document_ir') THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'FULL_DOCUMENT_IR_ROLLBACK_REFUSES_IR_DATA_LOSS';
    END IF;
END
$$;
DROP FUNCTION hwpx_agent.commit_revision_cas_with_full_ir_v1(
    uuid, uuid, uuid, character, uuid, uuid, bigint, uuid, uuid[], uuid, uuid, uuid,
    character, text, character, character, character, character,
    uuid, character, character, character
);
DROP TRIGGER revisions_full_document_ir_guard ON hwpx_agent.revisions;
DROP FUNCTION hwpx_agent.guard_revision_full_document_ir_v1();
ALTER TABLE hwpx_agent.revisions
    DROP CONSTRAINT revisions_full_document_ir_fk,
    DROP CONSTRAINT revisions_full_document_ir_shape,
    DROP COLUMN full_document_ir_artifact_id,
    DROP COLUMN full_document_ir_artifact_sha256,
    DROP COLUMN full_document_ir_result_package_sha256,
    DROP COLUMN full_document_ir_graph_sha256;
ALTER TABLE hwpx_agent.artifacts DROP CONSTRAINT artifacts_kind_value;
ALTER TABLE hwpx_agent.artifacts ADD CONSTRAINT artifacts_kind_value CHECK (
    artifact_kind IN ('source','result','preview','evidence','trace','diff','receipt')
);
-- The existing explicit destructive migration protocol, only in an empty-IR schema.
ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions WHERE version = 18 AND migration_name = 'p09.full_document_ir_v1';
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;
COMMIT;
