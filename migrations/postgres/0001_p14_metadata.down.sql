BEGIN;

DO $$
BEGIN
    IF current_setting('hwpx_agent.allow_destructive_rollback', true) IS DISTINCT FROM 'on' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'P14 metadata rollback requires explicit hwpx_agent.allow_destructive_rollback=on';
    END IF;
END
$$;

DROP SCHEMA hwpx_agent CASCADE;

COMMIT;
