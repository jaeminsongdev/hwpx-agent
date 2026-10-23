-- Explicit administrative rollback only. All jobs/intents/artifacts are preserved.
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM hwpx_agent.schema_versions WHERE version=24 AND migration_name='p09.stored_request_lookup_v1')
        OR EXISTS(SELECT 1 FROM hwpx_agent.schema_versions WHERE version>24) THEN
        RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='STORED_REQUEST_LOOKUP_DOWN_REQUIRES_EXACT24';
    END IF;
END
$$;
DROP FUNCTION hwpx_agent.read_stored_revision_request_v1(uuid,uuid,uuid,character,uuid,uuid,uuid,character,character,uuid,bigint);
DELETE FROM hwpx_agent.schema_versions WHERE version=24 AND migration_name='p09.stored_request_lookup_v1';
COMMIT;
