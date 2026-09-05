BEGIN;
DO $$
BEGIN
    IF current_setting('hwpx_agent.allow_p16_plan_source_rollback', true) IS DISTINCT FROM 'yes'
        OR NOT EXISTS (SELECT 1 FROM hwpx_agent.schema_versions
            WHERE version = 11 AND migration_name = 'p16.plan_source_v1')
        OR EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version > 11) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'plan source rollback requires explicit gate and exact version 11';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.revision_graph_bindings) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'plan source rollback refuses graph bindings';
    END IF;
END
$$;
DROP TABLE hwpx_agent.revision_graph_bindings;
DROP FUNCTION hwpx_agent.validate_revision_graph_binding();
ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions WHERE version = 11 AND migration_name = 'p16.plan_source_v1';
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;
COMMIT;
