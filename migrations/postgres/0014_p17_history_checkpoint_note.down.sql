BEGIN;

DO $$
BEGIN
    IF current_setting(
        'hwpx_agent.allow_p17_history_checkpoint_note_rollback', true
    ) IS DISTINCT FROM 'yes'
       OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 14 AND migration_name = 'p17.history_checkpoint_note_v2'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P17 history checkpoint note rollback requires an explicit gate and exact version 14';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version > 14) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P17 history checkpoint note rollback requires later migrations removed first';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.history_checkpoint_requests WHERE note IS NOT NULL)
       OR EXISTS (SELECT 1 FROM hwpx_agent.checkpoints WHERE note IS NOT NULL) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P17 history checkpoint note rollback would discard immutable data';
    END IF;
END
$$;

DROP FUNCTION hwpx_agent.create_history_checkpoint_v2(
    uuid, uuid, character, uuid, character, uuid, uuid, text, text
);

ALTER TABLE hwpx_agent.checkpoints
    DROP CONSTRAINT checkpoints_note_format,
    DROP COLUMN note;
ALTER TABLE hwpx_agent.history_checkpoint_requests
    DROP CONSTRAINT history_checkpoint_requests_note_format,
    DROP COLUMN note;

ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions
WHERE version = 14 AND migration_name = 'p17.history_checkpoint_note_v2';
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;

COMMIT;
