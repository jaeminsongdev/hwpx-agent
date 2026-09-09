BEGIN;

DO $$
BEGIN
    IF current_setting(
        'hwpx_agent.allow_p17_atomic_mirror_checkpoint_rollback', true
    ) IS DISTINCT FROM 'yes'
       OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 15 AND migration_name = 'p17.atomic_mirror_checkpoint_v3'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P17 atomic mirror checkpoint rollback requires an explicit gate and exact version 15';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version > 15) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P17 atomic mirror checkpoint rollback requires later migrations removed first';
    END IF;
END
$$;

DROP FUNCTION hwpx_agent.create_mirror_history_checkpoint_v3(
    uuid, uuid, character, uuid, uuid, uuid, bigint,
    uuid, character, uuid, uuid, text, text
);

ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions
WHERE version = 15 AND migration_name = 'p17.atomic_mirror_checkpoint_v3';
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;

COMMIT;
