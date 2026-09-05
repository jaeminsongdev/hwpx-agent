BEGIN;
DO $$
BEGIN
    IF current_setting('hwpx_agent.allow_p16_artifact_repository_rollback', true) IS DISTINCT FROM 'yes'
        OR NOT EXISTS (SELECT 1 FROM hwpx_agent.schema_versions
            WHERE version = 10 AND migration_name = 'p16.artifact_repository_v1')
        OR EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version > 10) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'artifact repository rollback requires explicit gate and exact version 10';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.artifact_service_audit) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'artifact repository rollback refuses audit data';
    END IF;
END
$$;
DROP TABLE hwpx_agent.artifact_service_audit;
-- The explicit empty-data/version gate above permits only this maintenance deletion.
-- Transaction rollback also restores the trigger if any subsequent statement fails.
ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions WHERE version = 10 AND migration_name = 'p16.artifact_repository_v1';
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;
COMMIT;
