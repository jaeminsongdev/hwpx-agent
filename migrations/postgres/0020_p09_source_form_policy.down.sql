BEGIN;
DO $$
BEGIN
    IF current_setting('hwpx_agent.allow_destructive_rollback',true) IS DISTINCT FROM 'on' THEN
        RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORM_POLICY_ROLLBACK_REQUIRES_EXPLICIT_GATE';
    END IF;
    IF EXISTS(SELECT 1 FROM hwpx_agent.schema_versions WHERE version>20)
        OR NOT EXISTS(SELECT 1 FROM hwpx_agent.schema_versions WHERE version=20 AND migration_name='p09.source_form_policy_v1') THEN
        RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='FORM_POLICY_ROLLBACK_REQUIRES_SCHEMA_20';
    END IF;
    IF EXISTS(SELECT 1 FROM hwpx_agent.source_form_policy_versions)
        OR EXISTS(SELECT 1 FROM hwpx_agent.source_form_policy_revocations) THEN
        RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='FORM_POLICY_ROLLBACK_REFUSES_DATA_LOSS';
    END IF;
END
$$;
DROP FUNCTION hwpx_agent.revoke_source_form_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint);
DROP FUNCTION hwpx_agent.read_source_form_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint);
DROP FUNCTION hwpx_agent.register_source_form_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint,character,character,character,uuid,character);
DROP FUNCTION hwpx_agent.require_source_form_policy_artifacts_v1(uuid,character,uuid,character,uuid,character,boolean);
DROP FUNCTION hwpx_agent.require_source_form_policy_role_v1(uuid,uuid,character,boolean);
DROP TABLE hwpx_agent.source_form_policy_revocations;
DROP TABLE hwpx_agent.source_form_policy_versions;
ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions WHERE version=20 AND migration_name='p09.source_form_policy_v1';
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;
COMMIT;
