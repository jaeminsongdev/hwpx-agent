-- P143 NEW disposable DB only. Original job API and exact SQL22 reader profile.
-- No registry table writes, helper, owner, replication or bypass-RLS privileges.
BEGIN;
SET LOCAL statement_timeout='10s';
SELECT set_config('hwpx_agent.tenant_id','60000000-0000-0000-0000-000000000001',true);
SELECT set_config('hwpx_agent.subject_sha256',repeat('a',64),true);
INSERT INTO hwpx_agent.branches(tenant_id,project_id,branch_id,name,is_default,created_by_subject_sha256)
VALUES ('60000000-0000-0000-0000-000000000001','62000000-0000-0000-0000-000000000001',
 '63000000-0000-0000-0000-000000000003','p143-source',false,repeat('a',64));
CREATE ROLE p143_worker LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS NOREPLICATION CONNECTION LIMIT 4;
GRANT USAGE ON SCHEMA hwpx_agent TO p143_worker;
GRANT SELECT ON hwpx_agent.schema_versions TO p143_worker;
GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id(),hwpx_agent.current_subject_sha256(),
hwpx_agent.register_scheduler_worker(uuid,character,uuid,text,character,text,integer,character),
hwpx_agent.claim_idempotent_job_with_full_ir_v1(uuid,uuid,uuid,character,uuid,uuid,uuid,uuid,uuid,bigint,character,character,character,character,character,character,text,character,integer,integer,integer,integer,character,uuid,character,character,character),
hwpx_agent.lease_idempotent_job_v2(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,character),
hwpx_agent.advance_idempotent_job_v2(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,text,text,character),
hwpx_agent.complete_idempotent_job_success_v2(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,uuid,uuid,character),
hwpx_agent.commit_idempotent_revision_cas_v2(uuid,uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,uuid,uuid,uuid,bigint,uuid,uuid[],uuid,uuid,uuid,character,text,character,character,character,character),
hwpx_agent.commit_idempotent_revision_cas_with_full_ir_v1(uuid,uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,uuid,uuid,uuid,bigint,uuid,uuid[],uuid,uuid,uuid,character,text,character,character,character,character,uuid,character,character,character)
TO p143_worker;
GRANT SELECT ON hwpx_agent.branches,hwpx_agent.project_acl,hwpx_agent.revisions,
 hwpx_agent.revision_parents,hwpx_agent.revision_graph_seals,hwpx_agent.revision_commit_receipts,
 hwpx_agent.full_document_ir_intents TO p143_worker;
-- Original adapter admission requires these named legacy policy capabilities.
DO $$DECLARE fname text; sig text; n bigint;
BEGIN
 FOREACH fname IN ARRAY ARRAY['read_source_form_policy_v1','register_source_form_policy_v1',
  'revoke_source_form_policy_v1','read_source_formula_policy_v1',
  'register_source_formula_policy_v1','revoke_source_formula_policy_v1'] LOOP
  SELECT count(*),min(p.oid::regprocedure::text) INTO n,sig FROM pg_proc p
   WHERE pronamespace='hwpx_agent'::regnamespace AND proname=fname;
  IF n<>1 THEN RAISE EXCEPTION 'P143_FUNCTION_IDENTITY_AMBIGUOUS'; END IF;
  EXECUTE format('GRANT EXECUTE ON FUNCTION %s TO p143_worker',sig);
 END LOOP;
END$$;
GRANT EXECUTE ON FUNCTION hwpx_agent.read_formula_issuer_trust_v1(uuid,uuid,character),
 hwpx_agent.read_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint)
 TO p143_worker;
DO $$DECLARE entry record;
BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='p143_worker'
   AND (rolsuper OR rolreplication OR rolbypassrls OR rolcreatedb OR rolcreaterole OR rolinherit))
   THEN RAISE EXCEPTION 'P143_UNSAFE_WORKER_ROLE'; END IF;
 FOR entry IN SELECT c.oid,c.relrowsecurity,c.relforcerowsecurity FROM pg_class c
   WHERE c.relnamespace='hwpx_agent'::regnamespace AND c.relname IN
   ('formula_issuer_trust_versions','formula_issuer_trust_revocations',
    'formula_approval_versions','formula_approval_revocations') LOOP
  IF NOT entry.relrowsecurity OR NOT entry.relforcerowsecurity
    OR has_table_privilege('p143_worker',entry.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
    THEN RAISE EXCEPTION 'P143_DIRECT_REGISTRY_PRIVILEGE_OR_RLS_DRIFT'; END IF;
 END LOOP;
 FOR entry IN SELECT p.oid FROM pg_proc p WHERE p.pronamespace='hwpx_agent'::regnamespace
   AND p.proname IN ('require_formula_issuer_owner_v1','require_formula_approval_editor_v1',
    'register_formula_issuer_trust_v1','revoke_formula_issuer_trust_v1',
    'register_formula_approval_v1','revoke_formula_approval_v1') LOOP
  IF has_function_privilege('p143_worker',entry.oid,'EXECUTE')
   THEN RAISE EXCEPTION 'P143_WORKER_WRITER_OR_HELPER_PRIVILEGE'; END IF;
 END LOOP;
END$$;
SET CONSTRAINTS ALL IMMEDIATE;
COMMIT;
