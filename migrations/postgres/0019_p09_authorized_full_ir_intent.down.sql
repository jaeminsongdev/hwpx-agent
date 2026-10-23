BEGIN;
DO $$
BEGIN
    IF current_setting('hwpx_agent.allow_destructive_rollback', true) IS DISTINCT FROM 'on' THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'FULL_IR_INTENT_ROLLBACK_REQUIRES_EXPLICIT_GATE';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version > 19)
        OR NOT EXISTS (SELECT 1 FROM hwpx_agent.schema_versions
            WHERE version = 19 AND migration_name = 'p09.authorized_full_ir_intent_v1') THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'FULL_IR_INTENT_ROLLBACK_REQUIRES_SCHEMA_19';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.full_document_ir_intents)
        OR EXISTS (SELECT 1 FROM hwpx_agent.revisions WHERE full_document_ir_artifact_id IS NOT NULL) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'FULL_IR_INTENT_ROLLBACK_REFUSES_DATA_LOSS';
    END IF;
END
$$;
DROP FUNCTION hwpx_agent.commit_idempotent_revision_cas_with_full_ir_v1(
    uuid, uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    uuid, uuid, uuid, bigint, uuid, uuid[], uuid, uuid, uuid,
    character, text, character, character, character, character,
    uuid, character, character, character
);
DROP FUNCTION hwpx_agent.claim_idempotent_job_with_full_ir_v1(
    uuid, uuid, uuid, character, uuid, uuid, uuid, uuid, uuid, bigint,
    character, character, character, character, character, character,
    text, character, integer, integer, integer, integer, character,
    uuid, character, character, character
);
DROP TRIGGER revision_commit_receipts_full_ir_intent_guard ON hwpx_agent.revision_commit_receipts;
DROP FUNCTION hwpx_agent.guard_full_ir_commit_intent_v1();
DROP FUNCTION hwpx_agent.require_full_ir_intent_artifact_v1(uuid, character, uuid, character, character);
DROP TABLE hwpx_agent.full_document_ir_intents;
-- Existing explicit empty-data rollback protocol; no application path may invoke this.
ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions WHERE version = 19 AND migration_name = 'p09.authorized_full_ir_intent_v1';
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;
COMMIT;

