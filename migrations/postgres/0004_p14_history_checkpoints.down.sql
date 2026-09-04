BEGIN;

DO $$
BEGIN
    IF current_setting('hwpx_agent.allow_destructive_rollback', true) IS DISTINCT FROM 'on' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 history rollback requires explicit hwpx_agent.allow_destructive_rollback=on';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 4 AND migration_name = 'p14.history_checkpoints_v1'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 history migration version 4 is not installed';
    END IF;
END
$$;

DROP FUNCTION hwpx_agent.query_revision_history(
    uuid, uuid, character, uuid, bigint, bigint, uuid, integer
);
DROP FUNCTION hwpx_agent.create_history_branch(
    uuid, uuid, character, uuid, text, uuid, character
);
DROP FUNCTION hwpx_agent.create_history_checkpoint(
    uuid, uuid, character, uuid, character, uuid, uuid, text
);
DROP INDEX hwpx_agent.revision_graph_seals_history_order_idx;
DROP TRIGGER history_checkpoint_requests_immutable
    ON hwpx_agent.history_checkpoint_requests;
DROP TABLE hwpx_agent.history_checkpoint_requests;

ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions WHERE version = 4;
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;

COMMIT;
