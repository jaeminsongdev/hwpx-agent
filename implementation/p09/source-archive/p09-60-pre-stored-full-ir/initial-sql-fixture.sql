-- Disposable SQL METADATA fixtures only: no real HWPX/import/issuer/native evidence.
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
    CASE WHEN n=3 THEN 'application/vnd.hwpx-agent.document-graph+json' ELSE 'application/octet-stream' END,
    CASE n WHEN 1 THEN 'source' WHEN 2 THEN 'result' ELSE 'document_ir' END,
    'available','kms.p09-ir',transaction_timestamp(),1,'test-only.bin',
    'artifacts/v1/60000000000000000000000000000001/'||
        CASE n WHEN 1 THEN 'source' WHEN 2 THEN 'result' ELSE 'document_ir' END||'/available/'||repeat(n::text,64)||'.aes256gcm',
    'AES-256-GCM',decode(repeat('01',12),'hex'),repeat('8',64),repeat('9',64),'verified','scanner.p09-ir','v1',1
FROM generate_series(1,3) n;
INSERT INTO hwpx_agent.artifact_acl(tenant_id,artifact_id,subject_sha256,can_read,can_manage)
SELECT tenant_id,artifact_id,repeat('a',64),true,true FROM hwpx_agent.artifacts;
SELECT set_config('hwpx_agent.tenant_id','60000000-0000-0000-0000-000000000001',false);
SELECT set_config('hwpx_agent.subject_sha256',repeat('a',64),false);

DO $$
DECLARE result record; base_node_count bigint;
BEGIN
    SELECT count(*) INTO base_node_count FROM hwpx_agent.revisions;
    BEGIN
        PERFORM * FROM hwpx_agent.commit_revision_cas_with_full_ir_v1(
            '60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001',
            '63000000-0000-0000-0000-000000000001',repeat('a',64),
            '66000000-0000-0000-0000-000000000001',NULL,0,'65000000-0000-0000-0000-000000000001',ARRAY[]::uuid[],
            '64000000-0000-0000-0000-000000000001','64000000-0000-0000-0000-000000000002',NULL,
            repeat('4',64),'verified',repeat('5',64),repeat('6',64),repeat('7',64),repeat('8',64),
            NULL,NULL,NULL,NULL);
        RAISE EXCEPTION 'TEST_NULL_IR_ACCEPTED';
    EXCEPTION WHEN invalid_parameter_value THEN NULL; END;
    BEGIN
        PERFORM * FROM hwpx_agent.commit_revision_cas_with_full_ir_v1(
            '60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001',
            '63000000-0000-0000-0000-000000000001',repeat('a',64),
            '66000000-0000-0000-0000-000000000001',NULL,0,'65000000-0000-0000-0000-000000000001',ARRAY[]::uuid[],
            '64000000-0000-0000-0000-000000000001','64000000-0000-0000-0000-000000000002',NULL,
            repeat('4',64),'verified',repeat('5',64),repeat('6',64),repeat('7',64),repeat('8',64),
            '64000000-0000-0000-0000-000000000003',repeat('3',64),repeat('1',64),repeat('3',64));
        RAISE EXCEPTION 'TEST_PACKAGE_DIGEST_ACCEPTED';
    EXCEPTION WHEN foreign_key_violation THEN NULL; END;
    BEGIN
        PERFORM * FROM hwpx_agent.commit_revision_cas_with_full_ir_v1(
            '60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001',
            '63000000-0000-0000-0000-000000000001',repeat('a',64),
            '66000000-0000-0000-0000-000000000001',NULL,0,'65000000-0000-0000-0000-000000000001',ARRAY[]::uuid[],
            '64000000-0000-0000-0000-000000000001','64000000-0000-0000-0000-000000000002',NULL,
            repeat('4',64),'verified',repeat('5',64),repeat('6',64),repeat('7',64),repeat('8',64),
            '64000000-0000-0000-0000-000000000003',repeat('1',64),repeat('2',64),repeat('3',64));
        RAISE EXCEPTION 'TEST_ARTIFACT_DIGEST_ACCEPTED';
    EXCEPTION WHEN foreign_key_violation THEN NULL; END;
    BEGIN
        PERFORM * FROM hwpx_agent.commit_revision_cas_with_full_ir_v1(
            '60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001',
            '63000000-0000-0000-0000-000000000001',repeat('a',64),
            '66000000-0000-0000-0000-000000000001',NULL,0,'65000000-0000-0000-0000-000000000001',ARRAY[]::uuid[],
            '64000000-0000-0000-0000-000000000001','64000000-0000-0000-0000-000000000002',NULL,
            repeat('4',64),'verified',repeat('5',64),repeat('6',64),repeat('7',64),repeat('8',64),
            '64000000-0000-0000-0000-000000000002',repeat('2',64),repeat('2',64),repeat('2',64));
        RAISE EXCEPTION 'TEST_RESULT_USED_AS_IR';
    EXCEPTION WHEN foreign_key_violation THEN NULL; END;
    IF (SELECT count(*) FROM hwpx_agent.revisions) <> base_node_count
        OR EXISTS (SELECT 1 FROM hwpx_agent.branches WHERE head_generation <> 0) THEN
        RAISE EXCEPTION 'TEST_FAILED_IR_COMMIT_MUTATED_HEAD';
    END IF;
    SELECT * INTO result FROM hwpx_agent.commit_revision_cas_with_full_ir_v1(
        '60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001',
        '63000000-0000-0000-0000-000000000001',repeat('a',64),
        '66000000-0000-0000-0000-000000000001',NULL,0,'65000000-0000-0000-0000-000000000001',ARRAY[]::uuid[],
        '64000000-0000-0000-0000-000000000001','64000000-0000-0000-0000-000000000002',NULL,
        repeat('4',64),'verified',repeat('5',64),repeat('6',64),repeat('7',64),repeat('8',64),
        '64000000-0000-0000-0000-000000000003',repeat('3',64),repeat('2',64),repeat('3',64));
    IF result.outcome <> 'committed' OR result.committed_generation <> 1 THEN
        RAISE EXCEPTION 'TEST_FULL_IR_COMMIT_FAILED';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM hwpx_agent.revisions
        WHERE revision_id='65000000-0000-0000-0000-000000000001'
            AND full_document_ir_artifact_id='64000000-0000-0000-0000-000000000003'
            AND full_document_ir_artifact_sha256=repeat('3',64)
            AND full_document_ir_result_package_sha256=repeat('2',64)
            AND full_document_ir_graph_sha256=repeat('3',64)) THEN
        RAISE EXCEPTION 'TEST_FULL_IR_BINDING_NOT_STORED';
    END IF;
    SELECT * INTO result FROM hwpx_agent.commit_revision_cas_with_full_ir_v1(
        '60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001',
        '63000000-0000-0000-0000-000000000001',repeat('a',64),
        '66000000-0000-0000-0000-000000000002',NULL,0,'65000000-0000-0000-0000-000000000002',ARRAY[]::uuid[],
        '64000000-0000-0000-0000-000000000001','64000000-0000-0000-0000-000000000002',NULL,
        repeat('4',64),'verified',repeat('5',64),repeat('6',64),repeat('7',64),repeat('8',64),
        '64000000-0000-0000-0000-000000000003',repeat('3',64),repeat('2',64),repeat('3',64));
    IF result.outcome <> 'conflict' OR result.observed_generation <> 1 THEN
        RAISE EXCEPTION 'TEST_STALE_FULL_IR_CAS_ACCEPTED';
    END IF;
    BEGIN
        UPDATE hwpx_agent.revisions SET full_document_ir_graph_sha256=repeat('1',64)
        WHERE revision_id='65000000-0000-0000-0000-000000000001';
        RAISE EXCEPTION 'TEST_SEALED_IR_MUTATED';
    EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL; END;
    SELECT * INTO result FROM hwpx_agent.commit_revision_cas(
        '60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000002',
        '63000000-0000-0000-0000-000000000002',repeat('a',64),
        '66000000-0000-0000-0000-000000000003',NULL,0,'65000000-0000-0000-0000-000000000003',ARRAY[]::uuid[],
        '64000000-0000-0000-0000-000000000001','64000000-0000-0000-0000-000000000002',NULL,
        repeat('4',64),'verified',repeat('5',64),repeat('6',64),repeat('7',64),repeat('8',64));
    IF result.outcome <> 'committed' OR EXISTS (SELECT 1 FROM hwpx_agent.revisions
        WHERE revision_id='65000000-0000-0000-0000-000000000003' AND full_document_ir_artifact_id IS NOT NULL) THEN
        RAISE EXCEPTION 'TEST_LEGACY_CAS_CHANGED';
    END IF;
END
$$;
SELECT 'P09_STORED_FULL_IR_METADATA_PASS assertions=9';
