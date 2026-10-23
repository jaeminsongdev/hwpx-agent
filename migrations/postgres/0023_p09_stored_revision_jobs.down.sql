-- Explicit administrative rollback only; never discard recorded jobs, intents or artifacts.
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version=23 AND migration_name='p09.stored_revision_jobs_v1')
        OR EXISTS(SELECT 1 FROM hwpx_agent.schema_versions WHERE version>23) THEN
        RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='STORED_REVISION_DOWN_REQUIRES_EXACT_SCHEMA_23';
    END IF;
    IF EXISTS(SELECT 1 FROM hwpx_agent.stored_revision_commit_intents)
        OR EXISTS(SELECT 1 FROM hwpx_agent.idempotency_records r JOIN hwpx_agent.artifacts a
            ON a.tenant_id=r.tenant_id AND a.artifact_id=r.source_artifact_id
            WHERE r.record_version=2 AND a.artifact_kind='result') THEN
        RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='STORED_REVISION_DOWN_PRESERVES_EXISTING_RECORDS';
    END IF;
END
$$;
DROP TRIGGER revision_commit_receipts_stored_intent_guard ON hwpx_agent.revision_commit_receipts;
DROP FUNCTION hwpx_agent.reconcile_stored_revision_job_v1(uuid,uuid,character,uuid,uuid,text,uuid,uuid,character);
DROP FUNCTION hwpx_agent.complete_stored_revision_job_success_v1(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,uuid,uuid,character);
DROP FUNCTION hwpx_agent.schedule_stored_revision_retry_v1(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,text,uuid,character);
DROP FUNCTION hwpx_agent.lease_stored_revision_job_v1(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,character);
DROP FUNCTION hwpx_agent.claim_stored_revision_job_v1(uuid,uuid,uuid,character,uuid,uuid,uuid,uuid,uuid,bigint,character,character,character,character,character,character,text,character,integer,integer,integer,integer,character);
DROP FUNCTION hwpx_agent.stored_revision_committed_effect_qualified_v1(uuid,uuid,uuid,character,uuid,character,uuid,bigint,character,uuid,character,character,uuid);
DROP FUNCTION hwpx_agent.guard_stored_revision_commit_intent_v1();
DROP FUNCTION hwpx_agent.read_stored_revision_commit_intent_v1(uuid,uuid,character,uuid,uuid,integer);
DROP FUNCTION hwpx_agent.register_stored_revision_commit_intent_v1(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,uuid,uuid,uuid,uuid,character,character,uuid,character,uuid);
DROP FUNCTION hwpx_agent.require_stored_commit_receipt_v1(uuid,character,uuid,character);
DROP FUNCTION hwpx_agent.stored_revision_source_qualified_v1(uuid,uuid,uuid,character,uuid,character,uuid,bigint,boolean);
DROP TABLE hwpx_agent.stored_revision_commit_intents;
DELETE FROM hwpx_agent.schema_versions WHERE version=23 AND migration_name='p09.stored_revision_jobs_v1';
COMMIT;
