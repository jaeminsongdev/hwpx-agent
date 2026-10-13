-- Disposable SQL METADATA fixtures only: no real HWPX/import/issuer/native evidence.
BEGIN;
INSERT INTO hwpx_agent.tenants(tenant_id,slug)
VALUES ('60000000-0000-0000-0000-000000000001','p09-full-ir-test');
INSERT INTO hwpx_agent.retention_policies(tenant_id,retention_policy_id,tombstone_grace_seconds,created_by_subject_sha256)
VALUES ('60000000-0000-0000-0000-000000000001','retention.p09-ir',0,repeat('a',64));
INSERT INTO hwpx_agent.projects(tenant_id,project_id,slug,display_name,target_profile_id,retention_policy_id)
SELECT '60000000-0000-0000-0000-000000000001',
    ('62000000-0000-0000-0000-'||lpad(n::text,12,'0'))::uuid,
    'p09-ir-project-'||n,'Test only','hancom-hangul-2020-secondary','retention.p09-ir'
FROM generate_series(1,2) n;
INSERT INTO hwpx_agent.project_acl(tenant_id,project_id,subject_sha256,role)
SELECT tenant_id,project_id,repeat('a',64),'owner' FROM hwpx_agent.projects;
INSERT INTO hwpx_agent.branches(tenant_id,project_id,branch_id,name,is_default,created_by_subject_sha256)
SELECT tenant_id,project_id,('63000000-0000-0000-0000-'||lpad(n::text,12,'0'))::uuid,'main',true,repeat('a',64)
FROM hwpx_agent.projects JOIN generate_series(1,2) n ON project_id = ('62000000-0000-0000-0000-'||lpad(n::text,12,'0'))::uuid;
INSERT INTO hwpx_agent.artifacts(tenant_id,artifact_id,content_sha256,size_bytes,media_type,artifact_kind,
    storage_state,encryption_key_ref,verified_at,service_metadata_version,filename,object_key,
    encryption_algorithm,encryption_nonce,aad_sha256,ciphertext_sha256,validation_state,
    scanner_engine_ref,scanner_signature_version,authorization_generation)
SELECT '60000000-0000-0000-0000-000000000001',
    ('64000000-0000-0000-0000-'||lpad(n::text,12,'0'))::uuid,repeat(n::text,64),1,
    CASE WHEN n IN (3,4) THEN 'application/vnd.hwpx-agent.document-graph+json' ELSE 'application/octet-stream' END,
    CASE n WHEN 1 THEN 'source' WHEN 2 THEN 'result' WHEN 5 THEN 'receipt' ELSE 'document_ir' END,
    'available','kms.p09-ir',transaction_timestamp(),1,'test-only.bin',
    'artifacts/v1/60000000000000000000000000000001/'||
        CASE n WHEN 1 THEN 'source' WHEN 2 THEN 'result' WHEN 5 THEN 'receipt' ELSE 'document_ir' END||'/available/'||repeat(n::text,64)||'.aes256gcm',
    'AES-256-GCM',decode(repeat('01',12),'hex'),repeat('8',64),repeat('9',64),'verified','scanner.p09-ir','v1',1
FROM generate_series(1,5) n;
INSERT INTO hwpx_agent.artifact_acl(tenant_id,artifact_id,subject_sha256,can_read,can_manage)
SELECT tenant_id,artifact_id,repeat('a',64),true,true FROM hwpx_agent.artifacts;
SELECT set_config('hwpx_agent.tenant_id','60000000-0000-0000-0000-000000000001',false);
SELECT set_config('hwpx_agent.subject_sha256',repeat('a',64),false);

-- No table rights and no EXECUTE on internal helpers/leaf. Only named production APIs.
CREATE ROLE p09_full_ir_test_app NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
GRANT USAGE ON SCHEMA hwpx_agent TO p09_full_ir_test_app;
GRANT EXECUTE ON FUNCTION hwpx_agent.register_scheduler_worker(
    uuid, character, uuid, text, character, text, integer, character
), hwpx_agent.claim_idempotent_job_with_full_ir_v1(
    uuid, uuid, uuid, character, uuid, uuid, uuid, uuid, uuid, bigint,
    character, character, character, character, character, character,
    text, character, integer, integer, integer, integer, character,
    uuid, character, character, character
), hwpx_agent.commit_idempotent_revision_cas_with_full_ir_v1(
    uuid, uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    uuid, uuid, uuid, bigint, uuid, uuid[], uuid, uuid, uuid,
    character, text, character, character, character, character,
    uuid, character, character, character
), hwpx_agent.commit_idempotent_revision_cas_v2(
    uuid, uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint,
    uuid, uuid, uuid, bigint, uuid, uuid[], uuid, uuid, uuid,
    character, text, character, character, character, character
), hwpx_agent.lease_idempotent_job_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, character
), hwpx_agent.advance_idempotent_job_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint, text, text, character
), hwpx_agent.complete_idempotent_job_success_v2(
    uuid, uuid, character, uuid, uuid, uuid, uuid, integer, bigint, uuid, uuid, character
) TO p09_full_ir_test_app;

CREATE TEMP TABLE p09_fixture_placeholder(n integer);
-- These small fixture-only helpers are SECURITY INVOKER, never fabricate auth/job/lease rows.
CREATE FUNCTION pg_temp.claim_ir(
    ir uuid DEFAULT '64000000-0000-0000-0000-000000000003', raw_sha character(64) DEFAULT repeat('3',64),
    package_sha character(64) DEFAULT repeat('2',64), graph_sha character(64) DEFAULT repeat('3',64)
) RETURNS TABLE(outcome text, state text, revision uuid)
LANGUAGE sql SECURITY INVOKER AS $$
    SELECT returned_outcome, returned_state, returned_result_revision_id
    FROM hwpx_agent.claim_idempotent_job_with_full_ir_v1(
        '60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001','63000000-0000-0000-0000-000000000001',repeat('a',64),
        '67000000-0000-0000-0000-000000000001','68000000-0000-0000-0000-000000000001','6b000000-0000-0000-0000-000000000001','64000000-0000-0000-0000-000000000001',NULL,0,
        repeat('1',64),repeat('2',64),repeat('1',64),repeat('2',64),repeat('6',64),repeat('4',64),
        'hancom-hangul-2020-secondary',repeat('c',64),3,1,4,600,repeat('4',64),
        ir,raw_sha,package_sha,graph_sha
    )
$$;
CREATE FUNCTION pg_temp.commit_ir(
    auth uuid, ir uuid DEFAULT '64000000-0000-0000-0000-000000000003', raw_sha character(64) DEFAULT repeat('3',64),
    package_sha character(64) DEFAULT repeat('2',64), graph_sha character(64) DEFAULT repeat('3',64),
    fence bigint DEFAULT 1
) RETURNS TABLE(outcome text, generation bigint)
LANGUAGE sql SECURITY INVOKER AS $$
    SELECT outcome, committed_generation
    FROM hwpx_agent.commit_idempotent_revision_cas_with_full_ir_v1(
        '60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001','63000000-0000-0000-0000-000000000001',repeat('a',64),
        '67000000-0000-0000-0000-000000000001','68000000-0000-0000-0000-000000000001','69000000-0000-0000-0000-000000000001','6a000000-0000-0000-0000-000000000001',1,fence,auth,
        '66000000-0000-0000-0000-000000000001',NULL,0,
        '65000000-0000-0000-0000-000000000001',ARRAY[]::uuid[],
        '64000000-0000-0000-0000-000000000001','64000000-0000-0000-0000-000000000002',NULL,repeat('4',64),'verified',repeat('5',64),
        repeat('6',64),repeat('7',64),repeat('8',64),ir,raw_sha,package_sha,graph_sha
    )
$$;
DO $$
BEGIN
    IF has_table_privilege('p09_full_ir_test_app','hwpx_agent.full_document_ir_intents','INSERT')
        OR has_function_privilege('p09_full_ir_test_app',
            'hwpx_agent.require_full_ir_intent_artifact_v1(uuid,character,uuid,character,character)','EXECUTE') THEN
        RAISE EXCEPTION 'TEST_ROLE_EXCESS_AUTHORITY';
    END IF;
END
$$;
SET LOCAL ROLE p09_full_ir_test_app;
DO $$
DECLARE r record; auth uuid; transitions text[] := ARRAY['leased','staged','executing','validating'];
BEGIN
    -- 1/2: actual unprivileged direct writes and internal leaf execution denied.
    BEGIN
        INSERT INTO hwpx_agent.full_document_ir_intents
        VALUES ('60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001','67000000-0000-0000-0000-000000000001','64000000-0000-0000-0000-000000000003',repeat('3',64),repeat('2',64),repeat('3',64));
        RAISE EXCEPTION 'TEST_DIRECT_INTENT_INSERT_ACCEPTED';
    EXCEPTION WHEN insufficient_privilege THEN NULL; END;
    BEGIN
        PERFORM * FROM hwpx_agent.commit_revision_cas_with_full_ir_v1(
            '60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001','63000000-0000-0000-0000-000000000001',repeat('a',64),
            '66000000-0000-0000-0000-000000000001',NULL,0,
            '65000000-0000-0000-0000-000000000001',ARRAY[]::uuid[],
            '64000000-0000-0000-0000-000000000001','64000000-0000-0000-0000-000000000002',NULL,repeat('4',64),'verified',repeat('5',64),
            repeat('6',64),repeat('7',64),repeat('8',64),'64000000-0000-0000-0000-000000000003',repeat('3',64),repeat('2',64),repeat('3',64));
        RAISE EXCEPTION 'TEST_DIRECT_LEAF_EXECUTE_ACCEPTED';
    EXCEPTION WHEN insufficient_privilege THEN NULL; END;
    -- 3..6: null/wrong-kind/digest/package rejected, no weakened validation.
    BEGIN
        PERFORM * FROM pg_temp.claim_ir(NULL);
        RAISE EXCEPTION 'TEST_NULL_IR_ACCEPTED';
    EXCEPTION WHEN foreign_key_violation THEN
        IF SQLERRM <> 'FULL_IR_INTENT_ARTIFACT_NOT_QUALIFIED' THEN RAISE; END IF;
    END;
    BEGIN
        PERFORM * FROM pg_temp.claim_ir('64000000-0000-0000-0000-000000000002',repeat('2',64),repeat('2',64),repeat('2',64));
        RAISE EXCEPTION 'TEST_RESULT_AS_IR_ACCEPTED';
    EXCEPTION WHEN foreign_key_violation THEN
        IF SQLERRM <> 'FULL_IR_INTENT_ARTIFACT_NOT_QUALIFIED' THEN RAISE; END IF;
    END;
    BEGIN
        PERFORM * FROM pg_temp.claim_ir('64000000-0000-0000-0000-000000000003',repeat('1',64));
        RAISE EXCEPTION 'TEST_BAD_IR_DIGEST_ACCEPTED';
    EXCEPTION WHEN foreign_key_violation THEN
        IF SQLERRM <> 'FULL_IR_INTENT_ARTIFACT_NOT_QUALIFIED' THEN RAISE; END IF;
    END;
    BEGIN
        PERFORM * FROM pg_temp.claim_ir('64000000-0000-0000-0000-000000000003',repeat('3',64),repeat('1',64));
        RAISE EXCEPTION 'TEST_BAD_PACKAGE_DIGEST_ACCEPTED';
    EXCEPTION WHEN invalid_parameter_value THEN
        IF SQLERRM <> 'FULL_IR_INTENT_REQUEST_INVALID' THEN RAISE; END IF;
    END;
    -- 7/8: real claim and exact replay.
    SELECT * INTO r FROM pg_temp.claim_ir();
    IF r.outcome <> 'new' OR r.state <> 'claimed' THEN RAISE EXCEPTION 'TEST_CLAIM_FAILED'; END IF;
    SELECT * INTO r FROM pg_temp.claim_ir();
    IF r.outcome <> 'replay' OR r.state <> 'claimed' THEN RAISE EXCEPTION 'TEST_CLAIM_REPLAY_FAILED'; END IF;
    -- 9: a valid but different IR cannot replace an existing admission.
    BEGIN
        PERFORM * FROM pg_temp.claim_ir('64000000-0000-0000-0000-000000000004',repeat('4',64),repeat('2',64),repeat('4',64));
        RAISE EXCEPTION 'TEST_IR_SWAP_CLAIM_ACCEPTED';
    EXCEPTION WHEN unique_violation THEN
        IF SQLERRM <> 'FULL_IR_INTENT_KEY_CONFLICT' THEN RAISE; END IF;
    END;
    -- 10: no real lease authority => rejected.
    BEGIN
        PERFORM * FROM pg_temp.commit_ir('6d000000-0000-0000-0000-000000000001');
        RAISE EXCEPTION 'TEST_UNAUTHORIZED_COMMIT_ACCEPTED';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'IDEMPOTENCY_COMMIT_AUTHORIZATION_REQUIRED' THEN RAISE; END IF;
    END;
    PERFORM * FROM hwpx_agent.register_scheduler_worker(
        '60000000-0000-0000-0000-000000000001',repeat('a',64),'69000000-0000-0000-0000-000000000001',
        'hancom-hangul-2020-secondary',repeat('c',64),'ready',300,repeat('1',64));
    SELECT * INTO r FROM hwpx_agent.lease_idempotent_job_v2('60000000-0000-0000-0000-000000000001', '62000000-0000-0000-0000-000000000001', repeat('a',64), '67000000-0000-0000-0000-000000000001', '68000000-0000-0000-0000-000000000001', '69000000-0000-0000-0000-000000000001', '6a000000-0000-0000-0000-000000000001',60,repeat('5',64));
    auth := r.returned_commit_authorization_id;
    -- 11: actual worker/lease/attempt/fence and returned authority.
    IF auth IS NULL OR r.returned_attempt_count <> 1 OR r.returned_fencing_token <> 1 THEN
        RAISE EXCEPTION 'TEST_REAL_LEASE_FAILED';
    END IF;
    -- 12/13: bad fence / wrong job stage refused.
    BEGIN
        PERFORM * FROM pg_temp.commit_ir(auth,fence => 2);
        RAISE EXCEPTION 'TEST_WRONG_FENCE_ACCEPTED';
    EXCEPTION WHEN invalid_parameter_value THEN
        IF SQLERRM <> 'IDEMPOTENCY_COMMIT_REQUEST_INVALID' THEN RAISE; END IF;
    END;
    BEGIN
        PERFORM * FROM pg_temp.commit_ir(auth);
        RAISE EXCEPTION 'TEST_PREVALIDATION_COMMIT_ACCEPTED';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'IDEMPOTENCY_COMMIT_FENCE_MISMATCH' THEN RAISE; END IF;
    END;
    FOR i IN 1..3 LOOP
        PERFORM * FROM hwpx_agent.advance_idempotent_job_v2(
            '60000000-0000-0000-0000-000000000001', '62000000-0000-0000-0000-000000000001', repeat('a',64), '67000000-0000-0000-0000-000000000001', '68000000-0000-0000-0000-000000000001', '69000000-0000-0000-0000-000000000001', '6a000000-0000-0000-0000-000000000001',1,1,transitions[i],transitions[i+1],repeat('6',64));
    END LOOP;
    -- 14: valid alternate IR must still match original immutable intent.
    BEGIN
        PERFORM * FROM pg_temp.commit_ir(auth,'64000000-0000-0000-0000-000000000004',repeat('4',64),repeat('2',64),repeat('4',64));
        RAISE EXCEPTION 'TEST_IR_SWAP_COMMIT_ACCEPTED';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'FULL_IR_COMMIT_INTENT_MISMATCH' THEN RAISE; END IF;
    END;
    -- 15/16: subject/tenant scoped checks remain enforced.
    PERFORM set_config('hwpx_agent.subject_sha256',repeat('b',64),true);
    BEGIN
        PERFORM * FROM pg_temp.commit_ir(auth);
        RAISE EXCEPTION 'TEST_WRONG_SUBJECT_ACCEPTED';
    EXCEPTION WHEN insufficient_privilege THEN NULL; END;
    PERFORM set_config('hwpx_agent.subject_sha256',repeat('a',64),true);
    PERFORM set_config('hwpx_agent.tenant_id','60000000-0000-0000-0000-000000000002',true);
    BEGIN
        PERFORM * FROM pg_temp.commit_ir(auth);
        RAISE EXCEPTION 'TEST_WRONG_TENANT_ACCEPTED';
    EXCEPTION WHEN insufficient_privilege THEN NULL; END;
    PERFORM set_config('hwpx_agent.tenant_id','60000000-0000-0000-0000-000000000001',true);
    -- 17: unchanged legacy wrapper cannot drop admitted IR, even with genuine auth.
    BEGIN
        PERFORM * FROM hwpx_agent.commit_idempotent_revision_cas_v2(
            '60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001','63000000-0000-0000-0000-000000000001',repeat('a',64),
            '67000000-0000-0000-0000-000000000001','68000000-0000-0000-0000-000000000001','69000000-0000-0000-0000-000000000001','6a000000-0000-0000-0000-000000000001',1,1,auth,
            '66000000-0000-0000-0000-000000000001',NULL,0,
            '65000000-0000-0000-0000-000000000001',ARRAY[]::uuid[],
            '64000000-0000-0000-0000-000000000001','64000000-0000-0000-0000-000000000002',NULL,repeat('4',64),'verified',repeat('5',64),
            repeat('6',64),repeat('7',64),repeat('8',64));
        RAISE EXCEPTION 'TEST_LEGACY_IR_BYPASS_ACCEPTED';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'FULL_IR_COMMIT_INTENT_MISMATCH' THEN RAISE; END IF;
    END;
    -- 18: genuine authorized commit; failed earlier transactions did not consume auth/head.
    SELECT * INTO r FROM pg_temp.commit_ir(auth);
    IF r.outcome <> 'committed' OR r.generation <> 1
        OR current_setting('hwpx_agent.commit_authorization_id',true) <> '' THEN
        RAISE EXCEPTION 'TEST_AUTHORIZED_IR_COMMIT_FAILED';
    END IF;
    -- 19: same token is single-use.
    BEGIN
        PERFORM * FROM pg_temp.commit_ir(auth);
        RAISE EXCEPTION 'TEST_CONSUMED_AUTH_REUSED';
    EXCEPTION WHEN insufficient_privilege THEN
        IF SQLERRM <> 'IDEMPOTENCY_COMMIT_AUTHORIZATION_REQUIRED' THEN RAISE; END IF;
    END;
    -- 20/21: authentic terminal completion and exact replay, no second effect.
    SELECT * INTO r FROM hwpx_agent.complete_idempotent_job_success_v2(
        '60000000-0000-0000-0000-000000000001', '62000000-0000-0000-0000-000000000001', repeat('a',64), '67000000-0000-0000-0000-000000000001', '68000000-0000-0000-0000-000000000001', '69000000-0000-0000-0000-000000000001', '6a000000-0000-0000-0000-000000000001',1,1,'65000000-0000-0000-0000-000000000001','64000000-0000-0000-0000-000000000005',repeat('7',64));
    IF r.returned_state <> 'terminal_success' THEN RAISE EXCEPTION 'TEST_COMPLETION_FAILED'; END IF;
    SELECT * INTO r FROM pg_temp.claim_ir();
    IF r.outcome <> 'replay' OR r.state <> 'terminal_success'
        OR r.revision <> '65000000-0000-0000-0000-000000000001'::uuid THEN
        RAISE EXCEPTION 'TEST_TERMINAL_REPLAY_FAILED';
    END IF;
END
$$;
RESET ROLE;
DO $$
BEGIN
    -- 22: exact stored link, atomic head, single job/attempt, consumed authority.
    IF (SELECT count(*) FROM hwpx_agent.revisions) <> 1
        OR (SELECT count(*) FROM hwpx_agent.jobs) <> 1
        OR (SELECT count(*) FROM hwpx_agent.job_attempts) <> 1
        OR (SELECT count(*) FROM hwpx_agent.full_document_ir_intents) <> 1
        OR EXISTS (SELECT 1 FROM hwpx_agent.idempotency_commit_authorizations)
        OR NOT EXISTS (SELECT 1 FROM hwpx_agent.revisions
            WHERE revision_id='65000000-0000-0000-0000-000000000001'
                AND full_document_ir_artifact_id='64000000-0000-0000-0000-000000000003'
                AND full_document_ir_artifact_sha256=repeat('3',64)
                AND full_document_ir_result_package_sha256=repeat('2',64)
                AND full_document_ir_graph_sha256=repeat('3',64))
        OR NOT EXISTS (SELECT 1 FROM hwpx_agent.branches WHERE branch_id='63000000-0000-0000-0000-000000000001' AND head_generation=1) THEN
        RAISE EXCEPTION 'TEST_ATOMIC_IR_RESULT_MISMATCH';
    END IF;
    -- 23/24: both intent and sealed link remain immutable.
    BEGIN
        UPDATE hwpx_agent.full_document_ir_intents SET graph_sha256=repeat('1',64);
        RAISE EXCEPTION 'TEST_IMMUTABLE_INTENT_CHANGED';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL; END;
    BEGIN
        UPDATE hwpx_agent.revisions SET full_document_ir_graph_sha256=repeat('1',64);
        RAISE EXCEPTION 'TEST_SEALED_LINK_CHANGED';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL; END;
    -- 25: fresh IR ACL is rechecked, even for a terminal replay.
    UPDATE hwpx_agent.artifact_acl SET can_read=false WHERE artifact_id='64000000-0000-0000-0000-000000000003';
    BEGIN
        PERFORM * FROM pg_temp.claim_ir();
        RAISE EXCEPTION 'TEST_REVOKED_IR_READ_ACCEPTED';
    EXCEPTION WHEN foreign_key_violation THEN
        IF SQLERRM <> 'FULL_IR_INTENT_ARTIFACT_NOT_QUALIFIED' THEN RAISE; END IF;
    END;
    UPDATE hwpx_agent.artifact_acl SET can_read=true WHERE artifact_id='64000000-0000-0000-0000-000000000003';
END
$$;
SET CONSTRAINTS ALL IMMEDIATE;
COMMIT;
SELECT 'P09_AUTHORIZED_FULL_IR_METADATA_PASS assertions=25';

