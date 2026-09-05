BEGIN;
DO $$
BEGIN
    IF current_setting('hwpx_agent.allow_p16_durable_plan_rollback', true) IS DISTINCT FROM 'yes'
        OR NOT EXISTS (SELECT 1 FROM hwpx_agent.schema_versions
            WHERE version = 12 AND migration_name = 'p16.durable_plan_store_v1')
        OR EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version > 12) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'durable plan rollback requires explicit gate and exact version 12';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.compiled_plan_records) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'durable plan rollback refuses compiled plans';
    END IF;
END
$$;
DROP TABLE hwpx_agent.compiled_plan_records;
DROP FUNCTION hwpx_agent.purge_expired_compiled_plan_records();
DROP FUNCTION hwpx_agent.reject_compiled_plan_change();
DROP FUNCTION hwpx_agent.validate_compiled_plan_record();
ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions WHERE version = 12 AND migration_name = 'p16.durable_plan_store_v1';
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;
COMMIT;
