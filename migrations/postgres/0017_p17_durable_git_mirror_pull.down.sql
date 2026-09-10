BEGIN;

DO $$
BEGIN
    IF current_setting(
        'hwpx_agent.allow_p17_durable_git_mirror_pull_rollback', true
    ) IS DISTINCT FROM 'yes'
       OR NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 17 AND migration_name = 'p17.durable_git_mirror_pull_v1'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P17 durable Git mirror pull rollback requires an explicit gate and exact version 17';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version > 17) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P17 durable Git mirror pull rollback requires later migrations removed first';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.git_mirror_pull_observations) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P17 durable Git mirror pull rollback refuses retained observations';
    END IF;
END
$$;

DROP FUNCTION hwpx_agent.reconcile_git_mirror_pull_v1(
    uuid, uuid, character, uuid, uuid, uuid, character, uuid, bigint, character,
    uuid, bigint, character, text, character
);
DROP TRIGGER git_mirror_pull_observation_guard
    ON hwpx_agent.git_mirror_pull_observations;
DROP FUNCTION hwpx_agent.guard_git_mirror_pull_observation_v1();
DROP TABLE hwpx_agent.git_mirror_pull_observations;

ALTER TABLE hwpx_agent.project_local_mirrors
    DROP CONSTRAINT local_mirror_clean_snapshot_binding,
    DROP CONSTRAINT local_mirror_observed_snapshot_format;
DROP TRIGGER local_mirror_observed_snapshot_binding
    ON hwpx_agent.project_local_mirrors;
DROP FUNCTION hwpx_agent.bind_local_mirror_observed_snapshot_v1();
ALTER TABLE hwpx_agent.project_local_mirrors
    DROP COLUMN observed_snapshot_sha256;

ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions
WHERE version = 17 AND migration_name = 'p17.durable_git_mirror_pull_v1';
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;

COMMIT;
