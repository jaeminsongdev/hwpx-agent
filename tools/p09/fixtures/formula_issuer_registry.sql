-- P140 disposable SQL metadata fixture. NOT real AEAD/signature/custody/product evidence.
BEGIN;
SET LOCAL statement_timeout='10s';
SET LOCAL lock_timeout='5s';
SELECT set_config('hwpx_agent.tenant_id','60000000-0000-0000-0000-000000000001',true);
SELECT set_config('hwpx_agent.subject_sha256',repeat('a',64),true);
INSERT INTO hwpx_agent.project_acl(tenant_id,project_id,subject_sha256,role)
SELECT tenant_id,project_id,repeat(subject,64),role FROM hwpx_agent.projects
CROSS JOIN (VALUES('e','editor'),('b','reader')) AS members(subject,role)
WHERE tenant_id='60000000-0000-0000-0000-000000000001';
INSERT INTO hwpx_agent.artifacts(tenant_id,artifact_id,content_sha256,size_bytes,media_type,artifact_kind,
 storage_state,encryption_key_ref,verified_at,service_metadata_version,filename,object_key,
 encryption_algorithm,encryption_nonce,aad_sha256,ciphertext_sha256,validation_state,
 scanner_engine_ref,scanner_signature_version,authorization_generation)
SELECT tenant_id,('71000000-0000-0000-0000-'||lpad(n::text,12,'0'))::uuid,repeat(chr(96+n),64),1,
 CASE WHEN n=1 THEN 'application/vnd.hwpx-agent.source-table-formula-policy+json'
 WHEN n IN (2,4,6) THEN 'application/vnd.hwpx-agent.source-formula-issuer-trust+json'
 ELSE 'application/vnd.hwpx-agent.source-formula-approval+json' END,
 'evidence',storage_state,encryption_key_ref,transaction_timestamp(),service_metadata_version,'metadata-only.json',
 'artifacts/v1/60000000000000000000000000000001/evidence/available/'||repeat(chr(96+n),64)||'.aes256gcm',
 encryption_algorithm,encryption_nonce,aad_sha256,ciphertext_sha256,validation_state,
 scanner_engine_ref,scanner_signature_version,authorization_generation
FROM hwpx_agent.artifacts CROSS JOIN generate_series(1,6) n
WHERE artifact_id='64000000-0000-0000-0000-000000000002';
INSERT INTO hwpx_agent.artifact_acl(tenant_id,artifact_id,subject_sha256,can_read,can_manage)
SELECT tenant_id,artifact_id,repeat(subject,64),true,subject IN ('a','e') FROM hwpx_agent.artifacts
CROSS JOIN (VALUES('a'),('b'),('e')) AS members(subject)
WHERE artifact_id::text LIKE '71000000-%' OR (artifact_id='64000000-0000-0000-0000-000000000002' AND subject<>'a');
CREATE ROLE p140_root NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE p140_approval NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE p140_read NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE p140_policy NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE p140_rls_probe NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
GRANT USAGE ON SCHEMA hwpx_agent TO p140_root,p140_approval,p140_read,p140_policy,p140_rls_probe;
GRANT EXECUTE ON FUNCTION hwpx_agent.register_formula_issuer_trust_v1(uuid,uuid,character,uuid,bigint,text,bigint,bigint,bigint,uuid,character),
 hwpx_agent.revoke_formula_issuer_trust_v1(uuid,uuid,character,uuid,bigint) TO p140_root;
GRANT EXECUTE ON FUNCTION hwpx_agent.register_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint,uuid,bigint,uuid,bigint,uuid,character),
 hwpx_agent.revoke_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,uuid,bigint) TO p140_approval;
GRANT EXECUTE ON FUNCTION hwpx_agent.read_formula_issuer_trust_v1(uuid,uuid,character),
 hwpx_agent.read_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint) TO p140_read;
GRANT EXECUTE ON FUNCTION hwpx_agent.register_source_formula_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint,character,character,character,uuid,character) TO p140_policy;
GRANT SELECT ON hwpx_agent.formula_issuer_trust_versions TO p140_rls_probe;
-- Dedicated fixture-only direct RLS probe needs the policy expression helper, not any writer/helper authority.
GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id() TO p140_rls_probe;
CREATE FUNCTION pg_temp.ok(name text,condition boolean) RETURNS text LANGUAGE plpgsql SECURITY INVOKER AS $$
BEGIN IF condition IS DISTINCT FROM true THEN RAISE EXCEPTION 'P140_ASSERTION_FAILED'; END IF;
 RETURN 'P140_SQL_CHECK:'||name; END $$;
CREATE FUNCTION pg_temp.denied(name text,sql text,expected_state text,expected_message text DEFAULT NULL)
RETURNS text LANGUAGE plpgsql SECURITY INVOKER AS $$
BEGIN
 BEGIN EXECUTE sql; EXCEPTION WHEN OTHERS THEN
  IF SQLSTATE<>expected_state OR (expected_message IS NOT NULL AND SQLERRM<>expected_message) THEN RAISE; END IF;
  RETURN 'P140_SQL_CHECK:'||name;
 END;
 RAISE EXCEPTION 'P140_UNEXPECTED_ACCEPTANCE';
END $$;
CREATE FUNCTION pg_temp.root_register(gen bigint DEFAULT 0,version uuid DEFAULT '73000000-0000-0000-0000-000000000001',
 artifact uuid DEFAULT '71000000-0000-0000-0000-000000000002',digest character(64) DEFAULT repeat('b',64))
RETURNS bigint LANGUAGE sql SECURITY INVOKER AS $$
 SELECT hwpx_agent.register_formula_issuer_trust_v1('60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001',
 current_setting('hwpx_agent.subject_sha256')::character(64),version,gen,'p140-test',0,
 floor(extract(epoch FROM clock_timestamp()))::bigint+3600,600,artifact,digest) $$;
CREATE FUNCTION pg_temp.root_read() RETURNS SETOF hwpx_agent.formula_issuer_trust_versions LANGUAGE sql SECURITY INVOKER AS $$
 SELECT * FROM hwpx_agent.read_formula_issuer_trust_v1('60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001',current_setting('hwpx_agent.subject_sha256')::character(64)) $$;
CREATE FUNCTION pg_temp.approval_register(gen bigint DEFAULT 0,version uuid DEFAULT '74000000-0000-0000-0000-000000000001',
 artifact uuid DEFAULT '71000000-0000-0000-0000-000000000003',digest character(64) DEFAULT repeat('c',64),
 policy uuid DEFAULT '72000000-0000-0000-0000-000000000001',trust uuid DEFAULT '73000000-0000-0000-0000-000000000001',trust_gen bigint DEFAULT 1)
RETURNS bigint LANGUAGE sql SECURITY INVOKER AS $$
 SELECT hwpx_agent.register_formula_approval_v1('60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001',
 '63000000-0000-0000-0000-000000000001',current_setting('hwpx_agent.subject_sha256')::character(64),'p140-formula',version,gen,
 policy,1,'65000000-0000-0000-0000-000000000001',1,trust,trust_gen,artifact,digest) $$;
CREATE FUNCTION pg_temp.approval_read() RETURNS SETOF hwpx_agent.formula_approval_versions LANGUAGE sql SECURITY INVOKER AS $$
 SELECT * FROM hwpx_agent.read_formula_approval_v1('60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001',
 '63000000-0000-0000-0000-000000000001',current_setting('hwpx_agent.subject_sha256')::character(64),'p140-formula',
 '65000000-0000-0000-0000-000000000001',1,'72000000-0000-0000-0000-000000000001',1) $$;
SELECT pg_temp.ok('forced_rls_four_tables',(SELECT count(*)=4 AND bool_and(relrowsecurity AND relforcerowsecurity)
 FROM pg_class WHERE oid IN ('hwpx_agent.formula_issuer_trust_versions'::regclass,'hwpx_agent.formula_issuer_trust_revocations'::regclass,
 'hwpx_agent.formula_approval_versions'::regclass,'hwpx_agent.formula_approval_revocations'::regclass)));
SELECT pg_temp.ok('nine_bounded_security_definers',(SELECT count(*)=9 AND bool_and(prosecdef AND proconfig @> ARRAY['search_path=pg_catalog, hwpx_agent'])
 FROM pg_proc WHERE pronamespace='hwpx_agent'::regnamespace AND proname IN ('lock_formula_issuer_scope_v1','require_formula_issuer_owner_v1',
 'require_formula_issuer_artifact_v1','register_formula_issuer_trust_v1','read_formula_issuer_trust_v1','revoke_formula_issuer_trust_v1',
 'register_formula_approval_v1','read_formula_approval_v1','revoke_formula_approval_v1')));
SET LOCAL ROLE p140_policy;
SELECT pg_temp.ok('named_source_formula_registration',hwpx_agent.register_source_formula_policy_v1(
 '60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001','63000000-0000-0000-0000-000000000001',repeat('a',64),
 'p140-formula','72000000-0000-0000-0000-000000000001',0,'65000000-0000-0000-0000-000000000001',1,repeat('2',64),repeat('5',64),repeat('7',64),
 '71000000-0000-0000-0000-000000000001',repeat('a',64))=1);
SET LOCAL ROLE p140_root;
SELECT pg_temp.ok('owner_root_registration',pg_temp.root_register()=1);
SELECT pg_temp.denied('root_cas_stale','SELECT pg_temp.root_register()','40001','FORMULA_ISSUER_GENERATION_CHANGED');
SELECT pg_temp.denied('root_wrong_digest',$q$SELECT pg_temp.root_register(1,'73000000-0000-0000-0000-000000000002','71000000-0000-0000-0000-000000000004',repeat('f',64))$q$,'42501','FORMULA_ISSUER_ARTIFACT_UNAVAILABLE');
SELECT pg_temp.denied('root_profile_no_read','SELECT * FROM pg_temp.root_read()','42501');
SELECT pg_temp.denied('root_profile_no_approval','SELECT pg_temp.approval_register()','42501');
SELECT pg_temp.denied('direct_table_read_denied','SELECT * FROM hwpx_agent.formula_issuer_trust_versions','42501');
SELECT pg_temp.denied('direct_table_write_denied','DELETE FROM hwpx_agent.formula_issuer_trust_versions','42501');
SELECT pg_temp.denied('internal_helper_execute_denied',$q$SELECT hwpx_agent.require_formula_issuer_owner_v1('60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001',repeat('a',64))$q$,'42501');
SELECT set_config('hwpx_agent.subject_sha256',repeat('e',64),true);
SELECT pg_temp.denied('editor_cannot_install_root','SELECT pg_temp.root_register()','42501','FORMULA_ISSUER_OWNER_REQUIRED');
SET LOCAL ROLE p140_approval;
SELECT pg_temp.ok('editor_approval_registration',pg_temp.approval_register()=1);
SELECT pg_temp.denied('approval_cas_stale','SELECT pg_temp.approval_register()','40001','FORMULA_APPROVAL_GENERATION_CHANGED');
SELECT pg_temp.denied('approval_profile_no_root','SELECT pg_temp.root_register()','42501');
SELECT pg_temp.denied('approval_profile_no_read','SELECT * FROM pg_temp.approval_read()','42501');
SELECT pg_temp.denied('approval_artifact_alias',$q$SELECT pg_temp.approval_register(1,'74000000-0000-0000-0000-000000000002','71000000-0000-0000-0000-000000000001',repeat('a',64))$q$,'42501','FORMULA_APPROVAL_ARTIFACT_ALIAS');
SELECT pg_temp.denied('approval_stale_policy',$q$SELECT pg_temp.approval_register(1,'74000000-0000-0000-0000-000000000002','71000000-0000-0000-0000-000000000005',repeat('e',64),'72000000-0000-0000-0000-000000000002')$q$,'40001','FORMULA_APPROVAL_POLICY_CHANGED');
SELECT pg_temp.denied('approval_stale_trust',$q$SELECT pg_temp.approval_register(1,'74000000-0000-0000-0000-000000000002','71000000-0000-0000-0000-000000000005',repeat('e',64),'72000000-0000-0000-0000-000000000001','73000000-0000-0000-0000-000000000002')$q$,'40001','FORMULA_APPROVAL_TRUST_CHANGED');
SELECT set_config('hwpx_agent.subject_sha256',repeat('b',64),true);
SELECT pg_temp.denied('reader_cannot_write_approval','SELECT pg_temp.approval_register()','42501','FORMULA_POLICY_SCOPE_DENIED');
SET LOCAL ROLE p140_read;
SELECT pg_temp.ok('reader_live_root_exact',(SELECT count(*)=1 AND bool_and(generation=1 AND trust_artifact_sha256=repeat('b',64)) FROM pg_temp.root_read()));
SELECT pg_temp.ok('reader_live_approval_exact',(SELECT count(*)=1 AND bool_and(generation=1 AND trust_generation=1 AND policy_generation=1 AND created_by_subject_sha256=repeat('e',64)) FROM pg_temp.approval_read()));
SELECT set_config('hwpx_agent.subject_sha256',repeat('c',64),true);
SELECT pg_temp.denied('nonmember_root_read','SELECT * FROM pg_temp.root_read()','42501','FORMULA_POLICY_SCOPE_DENIED');
SELECT set_config('hwpx_agent.subject_sha256',repeat('a',64),true);
SELECT set_config('hwpx_agent.tenant_id','60000000-0000-0000-0000-000000000002',true);
SELECT pg_temp.denied('foreign_tenant_named_read','SELECT * FROM pg_temp.root_read()','42501','FORMULA_POLICY_SCOPE_DENIED');
SET LOCAL ROLE p140_rls_probe;
SELECT pg_temp.ok('rls_foreign_tenant_zero',(SELECT count(*)=0 FROM hwpx_agent.formula_issuer_trust_versions));
SELECT set_config('hwpx_agent.tenant_id','60000000-0000-0000-0000-000000000001',true);
SELECT pg_temp.ok('rls_own_tenant_visible',(SELECT count(*)=1 FROM hwpx_agent.formula_issuer_trust_versions));
RESET ROLE;
SELECT pg_temp.denied('immutable_root_update','UPDATE hwpx_agent.formula_issuer_trust_versions SET issuer=issuer','55000');
SELECT pg_temp.denied('immutable_approval_delete','DELETE FROM hwpx_agent.formula_approval_versions','55000');
UPDATE hwpx_agent.artifact_acl SET can_read=false WHERE artifact_id='71000000-0000-0000-0000-000000000003' AND subject_sha256=repeat('a',64);
SET LOCAL ROLE p140_read;
SELECT pg_temp.denied('fresh_approval_acl_revocation','SELECT * FROM pg_temp.approval_read()','42501','FORMULA_ISSUER_ARTIFACT_UNAVAILABLE');
RESET ROLE;
UPDATE hwpx_agent.artifact_acl SET can_read=true WHERE artifact_id='71000000-0000-0000-0000-000000000003' AND subject_sha256=repeat('a',64);
SET LOCAL ROLE p140_root;
SELECT hwpx_agent.revoke_formula_issuer_trust_v1('60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001',repeat('a',64),'73000000-0000-0000-0000-000000000001',1);
SET LOCAL ROLE p140_read;
SELECT pg_temp.denied('revoked_root_no_fallback','SELECT * FROM pg_temp.root_read()','42501','FORMULA_ISSUER_TRUST_NOT_CURRENT');
SELECT pg_temp.denied('revoked_root_blocks_approval','SELECT * FROM pg_temp.approval_read()','42501','FORMULA_ISSUER_TRUST_NOT_CURRENT');
SET LOCAL ROLE p140_approval;
SELECT hwpx_agent.revoke_formula_approval_v1('60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001','63000000-0000-0000-0000-000000000001',repeat('a',64),'p140-formula','72000000-0000-0000-0000-000000000001','74000000-0000-0000-0000-000000000001',1);
RESET ROLE;
SELECT pg_temp.ok('admin_revoke_after_root_revocation',(SELECT count(*)=1 FROM hwpx_agent.formula_approval_revocations));
SET LOCAL ROLE p140_root;
SELECT pg_temp.ok('root_replacement_cas',pg_temp.root_register(1,'73000000-0000-0000-0000-000000000002','71000000-0000-0000-0000-000000000004',repeat('d',64))=2);
SET LOCAL ROLE p140_read;
SELECT pg_temp.denied('old_approval_after_root_replacement','SELECT * FROM pg_temp.approval_read()','42501','FORMULA_APPROVAL_NOT_CURRENT');
SET LOCAL ROLE p140_approval;
SELECT pg_temp.ok('approval_replacement_cas',pg_temp.approval_register(1,'74000000-0000-0000-0000-000000000002','71000000-0000-0000-0000-000000000005',repeat('e',64),'72000000-0000-0000-0000-000000000001','73000000-0000-0000-0000-000000000002',2)=2);
SET LOCAL ROLE p140_read;
SELECT pg_temp.ok('replacement_approval_read_exact',(SELECT count(*)=1 AND bool_and(generation=2 AND trust_generation=2 AND approval_artifact_sha256=repeat('e',64)) FROM pg_temp.approval_read()));
RESET ROLE;
SELECT pg_temp.ok('failed_subtransactions_left_no_extra_rows',(SELECT count(*)=2 FROM hwpx_agent.formula_issuer_trust_versions) AND (SELECT count(*)=2 FROM hwpx_agent.formula_approval_versions));
SET CONSTRAINTS ALL IMMEDIATE;
COMMIT;
