BEGIN;
DO $$
BEGIN
    IF current_setting('hwpx_agent.allow_p16_plan_review_evidence_rollback', true) IS DISTINCT FROM 'yes'
        OR NOT EXISTS (SELECT 1 FROM hwpx_agent.schema_versions
            WHERE version = 13 AND migration_name = 'p16.plan_review_evidence_v1')
        OR EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version > 13) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'plan review evidence rollback requires explicit gate and exact version 13';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.plan_review_evidence_records) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'plan review evidence rollback refuses evidence records';
    END IF;
END
$$;
DROP TABLE hwpx_agent.plan_review_evidence_records;
DROP FUNCTION hwpx_agent.purge_expired_plan_review_evidence_records();
DROP FUNCTION hwpx_agent.reject_plan_review_evidence_change();
DROP FUNCTION hwpx_agent.validate_plan_review_evidence_record();
ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions WHERE version = 13 AND migration_name = 'p16.plan_review_evidence_v1';
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;
COMMIT;
