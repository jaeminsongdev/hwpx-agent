BEGIN;

DO $$
BEGIN
    IF current_setting('hwpx_agent.allow_destructive_rollback', true) IS DISTINCT FROM 'on' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 revision CAS rollback requires explicit hwpx_agent.allow_destructive_rollback=on';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 3 AND migration_name = 'p14.revision_cas_v1'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 revision CAS migration version 3 is not installed';
    END IF;
END
$$;

DROP FUNCTION hwpx_agent.commit_revision_cas(
    uuid, uuid, uuid, character, uuid, uuid, bigint, uuid, uuid[], uuid, uuid, uuid,
    character, text, character, character, character, character
);
DROP TRIGGER revision_commit_receipts_immutable ON hwpx_agent.revision_commit_receipts;
DROP TRIGGER revision_graph_seals_immutable ON hwpx_agent.revision_graph_seals;
DROP TRIGGER revision_parents_guard_insert ON hwpx_agent.revision_parents;
DROP FUNCTION hwpx_agent.guard_revision_parent_insert();
DROP FUNCTION hwpx_agent.current_subject_sha256();
DROP TABLE hwpx_agent.revision_commit_receipts;
DROP TABLE hwpx_agent.revision_graph_seals;

ALTER TABLE hwpx_agent.branches
    DROP CONSTRAINT branches_head_generation_consistency,
    DROP COLUMN head_generation;
ALTER TABLE hwpx_agent.projects
    DROP CONSTRAINT projects_head_generation_consistency,
    DROP COLUMN head_generation;

ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions WHERE version = 3;
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;

COMMIT;
