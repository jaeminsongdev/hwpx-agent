-- SQL metadata tests only. No real policy plaintext, HWPX scanner, cipher or issuer evidence.
BEGIN;
INSERT INTO hwpx_agent.artifacts(tenant_id,artifact_id,content_sha256,size_bytes,media_type,artifact_kind,
    storage_state,encryption_key_ref,verified_at,service_metadata_version,filename,object_key,
    encryption_algorithm,encryption_nonce,aad_sha256,ciphertext_sha256,validation_state,
    scanner_engine_ref,scanner_signature_version,authorization_generation)
VALUES('60000000-0000-0000-0000-000000000001','64000000-0000-0000-0000-000000000006',repeat('d',64),1,
    'application/vnd.hwpx-agent.source-form-policy+json','evidence','available','kms.p09-ir',transaction_timestamp(),1,
    'test-policy.json','artifacts/v1/60000000000000000000000000000001/evidence/available/'||repeat('d',64)||'.aes256gcm',
    'AES-256-GCM',decode(repeat('02',12),'hex'),repeat('8',64),repeat('9',64),'verified','scanner.test-policy','v1',1);
INSERT INTO hwpx_agent.artifact_acl(tenant_id,artifact_id,subject_sha256,can_read,can_manage)
VALUES('60000000-0000-0000-0000-000000000001','64000000-0000-0000-0000-000000000006',repeat('a',64),true,true);
INSERT INTO hwpx_agent.project_acl(tenant_id,project_id,subject_sha256,role)
VALUES('60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001',repeat('b',64),'reader');
INSERT INTO hwpx_agent.artifact_acl(tenant_id,artifact_id,subject_sha256,can_read,can_manage)
SELECT tenant_id,artifact_id,repeat('b',64),true,false FROM hwpx_agent.artifacts
WHERE artifact_id IN ('64000000-0000-0000-0000-000000000002','64000000-0000-0000-0000-000000000006');
SELECT set_config('hwpx_agent.tenant_id','60000000-0000-0000-0000-000000000001',false);
SELECT set_config('hwpx_agent.subject_sha256',repeat('a',64),false);
CREATE ROLE p09_policy_test_app NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
GRANT USAGE ON SCHEMA hwpx_agent TO p09_policy_test_app;
GRANT EXECUTE ON FUNCTION
    hwpx_agent.register_source_form_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint,character,character,character,uuid,character),
    hwpx_agent.read_source_form_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint),
    hwpx_agent.revoke_source_form_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint)
    TO p09_policy_test_app;
CREATE FUNCTION pg_temp.register_policy(
    generation bigint DEFAULT 0,version uuid DEFAULT '66000000-0000-0000-0000-000000000001',
    head_generation bigint DEFAULT 1,artifact uuid DEFAULT '64000000-0000-0000-0000-000000000006',
    digest character(64) DEFAULT repeat('d',64),provenance character(64) DEFAULT repeat('5',64)
) RETURNS bigint LANGUAGE sql SECURITY INVOKER AS $$
SELECT hwpx_agent.register_source_form_policy_v1('60000000-0000-0000-0000-000000000001',
    '62000000-0000-0000-0000-000000000001','63000000-0000-0000-0000-000000000001',
    current_setting('hwpx_agent.subject_sha256')::character(64),'policy-document',version,generation,
    '65000000-0000-0000-0000-000000000001',head_generation,repeat('2',64),provenance,repeat('7',64),artifact,digest)
$$;
CREATE FUNCTION pg_temp.read_policy(document text DEFAULT 'policy-document',head_generation bigint DEFAULT 1)
RETURNS SETOF hwpx_agent.source_form_policy_versions LANGUAGE sql SECURITY INVOKER AS $$
SELECT * FROM hwpx_agent.read_source_form_policy_v1('60000000-0000-0000-0000-000000000001',
    '62000000-0000-0000-0000-000000000001','63000000-0000-0000-0000-000000000001',
    current_setting('hwpx_agent.subject_sha256')::character(64),document,
    '65000000-0000-0000-0000-000000000001',head_generation)
$$;
SET LOCAL ROLE p09_policy_test_app;
DO $$
BEGIN
    -- 1/2: only named entry points, no direct table/helper writes.
    BEGIN
        DELETE FROM hwpx_agent.source_form_policy_versions;
        RAISE EXCEPTION 'TEST_POLICY_DIRECT_WRITE_ACCEPTED';
    EXCEPTION WHEN insufficient_privilege THEN NULL; END;
    BEGIN
        PERFORM hwpx_agent.require_source_form_policy_role_v1('60000000-0000-0000-0000-000000000001',
            '62000000-0000-0000-0000-000000000001',repeat('a',64),true);
        RAISE EXCEPTION 'TEST_POLICY_HELPER_EXECUTE_ACCEPTED';
    EXCEPTION WHEN insufficient_privilege THEN NULL; END;
    -- 3/4: real public registration and exact immutable source metadata read.
    IF pg_temp.register_policy() <> 1 THEN RAISE EXCEPTION 'TEST_POLICY_FIRST_GENERATION'; END IF;
    IF NOT EXISTS(SELECT 1 FROM pg_temp.read_policy() WHERE generation=1
        AND policy_artifact_sha256=repeat('d',64) AND source_package_sha256=repeat('2',64)
        AND source_revision_id='65000000-0000-0000-0000-000000000001') THEN
        RAISE EXCEPTION 'TEST_POLICY_EXACT_READ';
    END IF;
    -- 5/6/7/8: no stale source/generation, wrong artifact role or wrong digest.
    BEGIN PERFORM pg_temp.register_policy(); RAISE EXCEPTION 'TEST_POLICY_STALE_GENERATION';
    EXCEPTION WHEN serialization_failure THEN IF SQLERRM<>'FORM_POLICY_GENERATION_CHANGED' THEN RAISE; END IF; END;
    BEGIN PERFORM pg_temp.register_policy(1,'66000000-0000-0000-0000-000000000002',2); RAISE EXCEPTION 'TEST_POLICY_STALE_HEAD';
    EXCEPTION WHEN serialization_failure THEN IF SQLERRM<>'FORM_POLICY_SOURCE_HEAD_CHANGED' THEN RAISE; END IF; END;
    BEGIN PERFORM pg_temp.register_policy(1,'66000000-0000-0000-0000-000000000002',1,'64000000-0000-0000-0000-000000000002',repeat('2',64)); RAISE EXCEPTION 'TEST_POLICY_RESULT_AS_POLICY';
    EXCEPTION WHEN insufficient_privilege THEN IF SQLERRM<>'FORM_POLICY_ARTIFACT_UNAVAILABLE' THEN RAISE; END IF; END;
    BEGIN PERFORM pg_temp.register_policy(1,'66000000-0000-0000-0000-000000000002',1,'64000000-0000-0000-0000-000000000006',repeat('e',64)); RAISE EXCEPTION 'TEST_POLICY_WRONG_DIGEST';
    EXCEPTION WHEN insufficient_privilege THEN IF SQLERRM<>'FORM_POLICY_ARTIFACT_UNAVAILABLE' THEN RAISE; END IF; END;
    -- 9/10: malformed binding and unknown document cannot default or reuse policy.
    BEGIN PERFORM pg_temp.register_policy(1,'66000000-0000-0000-0000-000000000002',1,'64000000-0000-0000-0000-000000000006',repeat('d',64),'invalid'); RAISE EXCEPTION 'TEST_POLICY_BAD_PROVENANCE';
    EXCEPTION WHEN check_violation THEN NULL; END;
    BEGIN PERFORM * FROM pg_temp.read_policy('other-document'); RAISE EXCEPTION 'TEST_POLICY_OTHER_DOCUMENT';
    EXCEPTION WHEN insufficient_privilege THEN IF SQLERRM<>'FORM_POLICY_NOT_CURRENT' THEN RAISE; END IF; END;
END
$$;
SELECT set_config('hwpx_agent.subject_sha256',repeat('b',64),false);
DO $$
BEGIN
    -- 11/12: reader may read but cannot register, even with readable policy/source artifacts.
    IF (SELECT count(*) FROM pg_temp.read_policy())<>1 THEN RAISE EXCEPTION 'TEST_POLICY_VIEWER_READ'; END IF;
    BEGIN PERFORM pg_temp.register_policy(1,'66000000-0000-0000-0000-000000000002'); RAISE EXCEPTION 'TEST_POLICY_VIEWER_WRITE';
    EXCEPTION WHEN insufficient_privilege THEN IF SQLERRM<>'FORM_POLICY_SCOPE_DENIED' THEN RAISE; END IF; END;
END
$$;
SELECT set_config('hwpx_agent.subject_sha256',repeat('c',64),false);
DO $$ BEGIN
    -- 13: no project ACL means no read, regardless of the public API grant.
    BEGIN PERFORM * FROM pg_temp.read_policy(); RAISE EXCEPTION 'TEST_POLICY_NONMEMBER_READ';
    EXCEPTION WHEN insufficient_privilege THEN IF SQLERRM<>'FORM_POLICY_SCOPE_DENIED' THEN RAISE; END IF; END;
END $$;
SELECT set_config('hwpx_agent.subject_sha256',repeat('a',64),false);
RESET ROLE;
UPDATE hwpx_agent.artifact_acl SET can_read=false WHERE artifact_id='64000000-0000-0000-0000-000000000006' AND subject_sha256=repeat('a',64);
SET LOCAL ROLE p09_policy_test_app;
DO $$ BEGIN
    -- 14/15: fresh revoked policy ACL blocks both read and registration.
    BEGIN PERFORM * FROM pg_temp.read_policy(); RAISE EXCEPTION 'TEST_POLICY_REVOKED_READ';
    EXCEPTION WHEN insufficient_privilege THEN IF SQLERRM<>'FORM_POLICY_ARTIFACT_UNAVAILABLE' THEN RAISE; END IF; END;
    BEGIN PERFORM pg_temp.register_policy(1,'66000000-0000-0000-0000-000000000002'); RAISE EXCEPTION 'TEST_POLICY_REVOKED_WRITE';
    EXCEPTION WHEN insufficient_privilege THEN IF SQLERRM<>'FORM_POLICY_ARTIFACT_UNAVAILABLE' THEN RAISE; END IF; END;
END $$;
RESET ROLE;
UPDATE hwpx_agent.artifact_acl SET can_read=true WHERE artifact_id='64000000-0000-0000-0000-000000000006' AND subject_sha256=repeat('a',64);
-- Additional negative cases keep all original22 tests, not a replacement subset.
UPDATE hwpx_agent.artifact_acl SET can_manage=false WHERE artifact_id='64000000-0000-0000-0000-000000000006' AND subject_sha256=repeat('a',64);
SET LOCAL ROLE p09_policy_test_app;
DO $$ BEGIN
    -- 23/24: readable policy does not grant management/authoring rights.
    IF (SELECT count(*) FROM pg_temp.read_policy())<>1 THEN RAISE EXCEPTION 'TEST_POLICY_READ_WITHOUT_MANAGE'; END IF;
    BEGIN PERFORM pg_temp.register_policy(1,'66000000-0000-0000-0000-000000000002'); RAISE EXCEPTION 'TEST_POLICY_MISSING_MANAGE';
    EXCEPTION WHEN insufficient_privilege THEN IF SQLERRM<>'FORM_POLICY_ARTIFACT_UNAVAILABLE' THEN RAISE; END IF; END;
END $$;
RESET ROLE;
UPDATE hwpx_agent.artifact_acl SET can_manage=true WHERE artifact_id='64000000-0000-0000-0000-000000000006' AND subject_sha256=repeat('a',64);
UPDATE hwpx_agent.artifact_acl SET can_read=false WHERE artifact_id='64000000-0000-0000-0000-000000000002' AND subject_sha256=repeat('a',64);
SET LOCAL ROLE p09_policy_test_app;
DO $$ BEGIN
    -- 25/26: source Result ACL is fresh too, not merely the policy artifact ACL.
    BEGIN PERFORM * FROM pg_temp.read_policy(); RAISE EXCEPTION 'TEST_POLICY_REVOKED_SOURCE_READ';
    EXCEPTION WHEN insufficient_privilege THEN IF SQLERRM<>'FORM_POLICY_ARTIFACT_UNAVAILABLE' THEN RAISE; END IF; END;
    BEGIN PERFORM pg_temp.register_policy(1,'66000000-0000-0000-0000-000000000002'); RAISE EXCEPTION 'TEST_POLICY_REVOKED_SOURCE_WRITE';
    EXCEPTION WHEN insufficient_privilege THEN IF SQLERRM<>'FORM_POLICY_ARTIFACT_UNAVAILABLE' THEN RAISE; END IF; END;
END $$;
RESET ROLE;
UPDATE hwpx_agent.artifact_acl SET can_read=true WHERE artifact_id='64000000-0000-0000-0000-000000000002' AND subject_sha256=repeat('a',64);
SET LOCAL ROLE p09_policy_test_app;
DO $$ BEGIN
    -- 27/28/29: null identity, foreign tenant and null CAS generation are not accepted.
    BEGIN PERFORM * FROM hwpx_agent.read_source_form_policy_v1('60000000-0000-0000-0000-000000000001',
        '62000000-0000-0000-0000-000000000001','63000000-0000-0000-0000-000000000001',NULL,'policy-document',
        '65000000-0000-0000-0000-000000000001',1); RAISE EXCEPTION 'TEST_POLICY_NULL_SUBJECT';
    EXCEPTION WHEN insufficient_privilege THEN IF SQLERRM<>'FORM_POLICY_SCOPE_DENIED' THEN RAISE; END IF; END;
    BEGIN PERFORM * FROM hwpx_agent.read_source_form_policy_v1('60000000-0000-0000-0000-000000000002',
        '62000000-0000-0000-0000-000000000001','63000000-0000-0000-0000-000000000001',repeat('a',64),'policy-document',
        '65000000-0000-0000-0000-000000000001',1); RAISE EXCEPTION 'TEST_POLICY_FOREIGN_TENANT';
    EXCEPTION WHEN insufficient_privilege THEN IF SQLERRM<>'FORM_POLICY_SCOPE_DENIED' THEN RAISE; END IF; END;
    BEGIN PERFORM pg_temp.register_policy(NULL,'66000000-0000-0000-0000-000000000002'); RAISE EXCEPTION 'TEST_POLICY_NULL_GENERATION';
    EXCEPTION WHEN serialization_failure THEN IF SQLERRM<>'FORM_POLICY_GENERATION_CHANGED' THEN RAISE; END IF; END;
    -- 30/31: nil version identifier and stale revocation do not change history.
    BEGIN PERFORM pg_temp.register_policy(1,'00000000-0000-0000-0000-000000000000'); RAISE EXCEPTION 'TEST_POLICY_NIL_VERSION';
    EXCEPTION WHEN check_violation THEN NULL; END;
    BEGIN PERFORM hwpx_agent.revoke_source_form_policy_v1('60000000-0000-0000-0000-000000000001',
        '62000000-0000-0000-0000-000000000001','63000000-0000-0000-0000-000000000001',repeat('a',64),
        'policy-document','66000000-0000-0000-0000-000000000002',1); RAISE EXCEPTION 'TEST_POLICY_STALE_REVOCATION';
    EXCEPTION WHEN serialization_failure THEN IF SQLERRM<>'FORM_POLICY_GENERATION_CHANGED' THEN RAISE; END IF; END;
END $$;
SELECT set_config('hwpx_agent.subject_sha256',repeat('b',64),false);
DO $$ BEGIN
    -- 32: read membership alone cannot revoke policy either.
    BEGIN PERFORM hwpx_agent.revoke_source_form_policy_v1('60000000-0000-0000-0000-000000000001',
        '62000000-0000-0000-0000-000000000001','63000000-0000-0000-0000-000000000001',repeat('b',64),
        'policy-document','66000000-0000-0000-0000-000000000001',1); RAISE EXCEPTION 'TEST_POLICY_READER_REVOCATION';
    EXCEPTION WHEN insufficient_privilege THEN IF SQLERRM<>'FORM_POLICY_SCOPE_DENIED' THEN RAISE; END IF; END;
END $$;
SELECT set_config('hwpx_agent.subject_sha256',repeat('a',64),false);
RESET ROLE;
DO $$ BEGIN
    -- 16/17: owner maintenance cannot mutate either immutable history table.
    BEGIN UPDATE hwpx_agent.source_form_policy_versions SET observed_graph_sha256=repeat('8',64); RAISE EXCEPTION 'TEST_POLICY_IMMUTABILITY';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL; END;
    BEGIN DELETE FROM hwpx_agent.source_form_policy_versions; RAISE EXCEPTION 'TEST_POLICY_DELETE';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL; END;
END $$;
SET LOCAL ROLE p09_policy_test_app;
DO $$ BEGIN
    -- 18/19/20: new version increments CAS; explicit latest revocation does not fall back to v1.
    IF pg_temp.register_policy(1,'66000000-0000-0000-0000-000000000002')<>2 THEN RAISE EXCEPTION 'TEST_POLICY_SECOND_GENERATION'; END IF;
    PERFORM hwpx_agent.revoke_source_form_policy_v1('60000000-0000-0000-0000-000000000001',
        '62000000-0000-0000-0000-000000000001','63000000-0000-0000-0000-000000000001',repeat('a',64),
        'policy-document','66000000-0000-0000-0000-000000000002',2);
    BEGIN PERFORM * FROM pg_temp.read_policy(); RAISE EXCEPTION 'TEST_POLICY_REVOKED_VERSION_FALLBACK';
    EXCEPTION WHEN insufficient_privilege THEN IF SQLERRM<>'FORM_POLICY_NOT_CURRENT' THEN RAISE; END IF; END;
END $$;
RESET ROLE;
DO $$ BEGIN
    -- 21/22: all failed registrations were rolled back; revocation cannot be erased.
    IF (SELECT count(*) FROM hwpx_agent.source_form_policy_versions)<>2
        OR (SELECT count(*) FROM hwpx_agent.source_form_policy_revocations)<>1 THEN RAISE EXCEPTION 'TEST_POLICY_HISTORY_COUNT'; END IF;
    BEGIN DELETE FROM hwpx_agent.source_form_policy_revocations; RAISE EXCEPTION 'TEST_POLICY_REVOCATION_DELETE';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL; END;
END $$;
SET CONSTRAINTS ALL IMMEDIATE;
COMMIT;
SELECT 'P09_SOURCE_FORM_POLICY_METADATA_PASS assertions=32';
