-- Source only. Never executed by a connection; explicit migration-owner rollback gate required.
BEGIN;
DO $$ BEGIN
    IF current_setting('hwpx_agent.allow_destructive_rollback',true) IS DISTINCT FROM 'on' THEN
        RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='HTTPS_ATOMIC_ROLLBACK_REQUIRES_EXPLICIT_GATE';
    END IF;
    IF EXISTS(SELECT 1 FROM hwpx_agent.schema_versions WHERE version>26)
        OR NOT EXISTS(SELECT 1 FROM hwpx_agent.schema_versions WHERE version=26 AND migration_name='p09.https_policy_atomic_commit_v1')
        OR EXISTS(SELECT 1 FROM hwpx_agent.source_https_target_policy_versions) THEN
        RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='HTTPS_ATOMIC_ROLLBACK_REFUSES_QUALIFIED_POLICY_HISTORY';
    END IF;
END $$;
DROP FUNCTION hwpx_agent.require_https_policy_commit_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,character,character,character,uuid,bigint,uuid,character);
ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions WHERE version=26 AND migration_name='p09.https_policy_atomic_commit_v1';
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;
COMMIT;
