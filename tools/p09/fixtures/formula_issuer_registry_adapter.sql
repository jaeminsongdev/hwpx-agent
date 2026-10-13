-- P141 disposable only. Credential-bound adapter profiles; no real blob/signature/key evidence.
BEGIN;
SET LOCAL statement_timeout='10s';
SELECT set_config('hwpx_agent.tenant_id','60000000-0000-0000-0000-000000000001',true);
SELECT set_config('hwpx_agent.subject_sha256',repeat('a',64),true);
INSERT INTO hwpx_agent.artifacts(tenant_id,artifact_id,content_sha256,size_bytes,media_type,artifact_kind,
 storage_state,encryption_key_ref,verified_at,service_metadata_version,filename,object_key,
 encryption_algorithm,encryption_nonce,aad_sha256,ciphertext_sha256,validation_state,
 scanner_engine_ref,scanner_signature_version,authorization_generation)
SELECT tenant_id,'71000000-0000-0000-0000-000000000007',repeat('7',64),size_bytes,media_type,artifact_kind,
 storage_state,encryption_key_ref,transaction_timestamp(),service_metadata_version,filename,
 'artifacts/v1/60000000000000000000000000000001/evidence/available/'||repeat('7',64)||'.aes256gcm',
 encryption_algorithm,encryption_nonce,aad_sha256,ciphertext_sha256,validation_state,
 scanner_engine_ref,scanner_signature_version,authorization_generation
FROM hwpx_agent.artifacts WHERE artifact_id='71000000-0000-0000-0000-000000000005';
INSERT INTO hwpx_agent.artifact_acl(tenant_id,artifact_id,subject_sha256,can_read,can_manage)
SELECT tenant_id,'71000000-0000-0000-0000-000000000007',subject_sha256,can_read,can_manage
FROM hwpx_agent.artifact_acl WHERE artifact_id='71000000-0000-0000-0000-000000000005';
CREATE ROLE p141_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE p141_root LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE p141_approval LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE p141_bad_direct LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE p141_bad_helper LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
GRANT USAGE ON SCHEMA hwpx_agent TO p141_reader,p141_root,p141_approval,p141_bad_direct,p141_bad_helper;
GRANT SELECT ON hwpx_agent.schema_versions,hwpx_agent.branches,hwpx_agent.project_acl,
 hwpx_agent.revisions,hwpx_agent.revision_parents,hwpx_agent.revision_graph_seals,
 hwpx_agent.revision_commit_receipts,hwpx_agent.full_document_ir_intents
 TO p141_reader,p141_root,p141_approval,p141_bad_direct,p141_bad_helper;
-- Exact admission-required legacy capabilities only; no jobs/lease/owner/direct table writers.
DO $$DECLARE fname text; sig text; n bigint; target text;
BEGIN
 FOREACH fname IN ARRAY ARRAY['current_tenant_id','current_subject_sha256',
  'commit_idempotent_revision_cas_with_full_ir_v1','commit_idempotent_revision_cas_v2',
  'read_source_form_policy_v1','register_source_form_policy_v1','revoke_source_form_policy_v1',
  'read_source_formula_policy_v1','register_source_formula_policy_v1','revoke_source_formula_policy_v1'] LOOP
  SELECT count(*),min(p.oid::regprocedure::text) INTO n,sig FROM pg_proc p
   WHERE pronamespace='hwpx_agent'::regnamespace AND proname=fname;
  IF n<>1 THEN RAISE EXCEPTION 'P141_FUNCTION_IDENTITY_AMBIGUOUS'; END IF;
  FOREACH target IN ARRAY ARRAY['p141_reader','p141_root','p141_approval','p141_bad_direct','p141_bad_helper'] LOOP
   EXECUTE format('GRANT EXECUTE ON FUNCTION %s TO %I',sig,target);
  END LOOP;
 END LOOP;
END$$;
GRANT EXECUTE ON FUNCTION hwpx_agent.read_formula_issuer_trust_v1(uuid,uuid,character),
 hwpx_agent.read_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint)
 TO p141_reader,p141_bad_direct,p141_bad_helper;
GRANT EXECUTE ON FUNCTION hwpx_agent.register_formula_issuer_trust_v1(uuid,uuid,character,uuid,bigint,text,bigint,bigint,bigint,uuid,character),
 hwpx_agent.revoke_formula_issuer_trust_v1(uuid,uuid,character,uuid,bigint) TO p141_root;
GRANT EXECUTE ON FUNCTION hwpx_agent.register_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint,uuid,bigint,uuid,bigint,uuid,character),
 hwpx_agent.revoke_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,uuid,bigint) TO p141_approval;
-- Deliberately unsafe fixture profiles must fail fresh adapter admission.
GRANT SELECT ON hwpx_agent.formula_issuer_trust_versions TO p141_bad_direct;
GRANT EXECUTE ON FUNCTION hwpx_agent.require_formula_issuer_owner_v1(uuid,uuid,character) TO p141_bad_helper;
SET CONSTRAINTS ALL IMMEDIATE;
COMMIT;
