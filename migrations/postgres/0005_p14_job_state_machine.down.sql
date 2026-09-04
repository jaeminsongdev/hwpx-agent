BEGIN;

DO $$
BEGIN
    IF current_setting('hwpx_agent.allow_destructive_rollback', true) IS DISTINCT FROM 'on' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 job state-machine rollback requires explicit hwpx_agent.allow_destructive_rollback=on';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM hwpx_agent.schema_versions
        WHERE version = 5 AND migration_name = 'p14.job_state_machine_v1'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 job state-machine migration version 5 is not installed';
    END IF;
    IF EXISTS (SELECT 1 FROM hwpx_agent.schema_versions WHERE version > 5) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 job state-machine rollback requires later migrations removed first';
    END IF;
END
$$;

DROP FUNCTION hwpx_agent.get_job_state_machine(uuid, uuid, character, uuid);
DROP FUNCTION hwpx_agent.fail_job_state_machine(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, text, uuid, character
);
DROP FUNCTION hwpx_agent.commit_job_success(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, uuid, uuid, character
);
DROP FUNCTION hwpx_agent.advance_job_state_machine(
    uuid, uuid, character, uuid, uuid, uuid, integer, bigint, text, text, character
);
DROP FUNCTION hwpx_agent.lease_job_state_machine(
    uuid, uuid, character, uuid, uuid, uuid, integer, character
);
DROP FUNCTION hwpx_agent.enqueue_job_state_machine(
    uuid, uuid, character, uuid, uuid, uuid, uuid, character, text, character
);

DROP TRIGGER job_attempts_state_machine_consistency ON hwpx_agent.job_attempts;
DROP TRIGGER jobs_state_machine_consistency ON hwpx_agent.jobs;
DROP TRIGGER job_attempts_state_machine_guard ON hwpx_agent.job_attempts;
DROP TRIGGER jobs_state_machine_guard ON hwpx_agent.jobs;
DROP FUNCTION hwpx_agent.verify_job_state_machine_consistency();
DROP FUNCTION hwpx_agent.guard_job_attempt_state_machine_update();
DROP FUNCTION hwpx_agent.guard_job_state_machine_update();

DROP INDEX hwpx_agent.job_attempts_state_machine_active_idx;
DROP INDEX hwpx_agent.jobs_state_machine_queue_idx;

ALTER TABLE hwpx_agent.job_attempts
    DROP CONSTRAINT job_attempts_state_machine_v1_complete,
    DROP CONSTRAINT job_attempts_state_machine_version,
    DROP COLUMN updated_at,
    DROP COLUMN lease_expires_at,
    DROP COLUMN state_machine_version;
ALTER TABLE hwpx_agent.jobs
    DROP CONSTRAINT jobs_state_machine_v1_complete,
    DROP CONSTRAINT jobs_state_machine_version,
    DROP COLUMN lease_issued_at,
    DROP COLUMN active_execution_id,
    DROP COLUMN state_machine_version;

ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions WHERE version = 5;
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;

COMMIT;
