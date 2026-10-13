-- Synthetic SQL METADATA only, no real blob/scanner/import/issuer/native acceptance.
BEGIN;
INSERT INTO hwpx_agent.tenants(tenant_id,slug) VALUES ('00000000-0000-0000-0000-000000000001','p09-revision-probe');
INSERT INTO hwpx_agent.retention_policies(tenant_id,retention_policy_id,tombstone_grace_seconds,created_by_subject_sha256)
VALUES ('00000000-0000-0000-0000-000000000001','retention.p09-revision-probe',0,repeat('a',64));
INSERT INTO hwpx_agent.projects(tenant_id,project_id,slug,display_name,target_profile_id,retention_policy_id)
VALUES ('00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000002',
'p09-revision-probe','Synthetic probe','hancom-hangul-2020-secondary','retention.p09-revision-probe');
INSERT INTO hwpx_agent.project_acl(tenant_id,project_id,subject_sha256,role)
VALUES ('00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000002',repeat('a',64),'owner');
INSERT INTO hwpx_agent.branches(tenant_id,project_id,branch_id,name,is_default,created_by_subject_sha256)
VALUES ('00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000002',
'00000000-0000-0000-0000-000000000003','main',true,repeat('a',64));
WITH seed AS (
 SELECT ('00000000-0000-0000-0000-'||lpad(to_hex(10+n),12,'0'))::uuid AS artifact_id,
 repeat(CASE WHEN n=5 THEN '6' ELSE n::text END,64) AS sha,
 CASE n WHEN 1 THEN 'source' WHEN 2 THEN 'result' WHEN 5 THEN 'receipt' ELSE 'document_ir' END AS kind
 FROM generate_series(1,5) n
)
INSERT INTO hwpx_agent.artifacts(tenant_id,artifact_id,content_sha256,size_bytes,media_type,artifact_kind,
storage_state,encryption_key_ref,verified_at,service_metadata_version,filename,object_key,encryption_algorithm,
encryption_nonce,aad_sha256,ciphertext_sha256,validation_state,scanner_engine_ref,scanner_signature_version,authorization_generation)
SELECT '00000000-0000-0000-0000-000000000001',artifact_id,sha,1,
CASE WHEN kind='document_ir' THEN 'application/vnd.hwpx-agent.document-graph+json' ELSE 'application/octet-stream' END,
kind,'available','kms.synthetic-probe',transaction_timestamp(),1,'synthetic.bin',
'artifacts/v1/00000000000000000000000000000001/'||kind||'/available/'||sha||'.aes256gcm',
'AES-256-GCM',decode(repeat('01',12),'hex'),repeat('8',64),repeat('9',64),'verified','scanner.synthetic-probe','v1',1
FROM seed;
INSERT INTO hwpx_agent.artifact_acl(tenant_id,artifact_id,subject_sha256,can_read,can_manage)
SELECT tenant_id,artifact_id,repeat('a',64),true,true FROM hwpx_agent.artifacts;
COMMIT;

