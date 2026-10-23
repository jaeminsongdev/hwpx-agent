-- Owned disposable test DB only. No password literals, production identities or role memberships.
BEGIN;
CREATE ROLE p09_artifact_284 LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS NOREPLICATION CONNECTION LIMIT 4;
CREATE ROLE p09_revision_284 LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS NOREPLICATION CONNECTION LIMIT 4;
GRANT USAGE ON SCHEMA hwpx_agent TO p09_artifact_284,p09_revision_284;
GRANT SELECT ON hwpx_agent.schema_versions TO p09_artifact_284,p09_revision_284;
GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id() TO p09_artifact_284;
GRANT SELECT,INSERT,UPDATE ON hwpx_agent.artifacts TO p09_artifact_284;
GRANT SELECT,INSERT,UPDATE,DELETE ON hwpx_agent.artifact_acl TO p09_artifact_284;
GRANT SELECT,INSERT ON hwpx_agent.artifact_service_audit TO p09_artifact_284;
GRANT USAGE ON SEQUENCE hwpx_agent.artifact_service_audit_event_id_seq TO p09_artifact_284;
GRANT SELECT ON hwpx_agent.branches,hwpx_agent.project_acl,hwpx_agent.revisions,hwpx_agent.revision_parents,
  hwpx_agent.revision_graph_seals,hwpx_agent.revision_commit_receipts,hwpx_agent.full_document_ir_intents TO p09_revision_284;
DO $$
DECLARE names text[]:=ARRAY[
 'current_tenant_id','current_subject_sha256',
 'commit_idempotent_revision_cas_v2','commit_idempotent_revision_cas_with_full_ir_v1',
 'read_source_form_policy_v1','register_source_form_policy_v1','revoke_source_form_policy_v1',
 'read_source_formula_policy_v1','register_source_formula_policy_v1','revoke_source_formula_policy_v1',
 'read_formula_issuer_trust_v1','read_formula_approval_v1',
 'register_stored_revision_commit_intent_v1','read_stored_revision_commit_intent_v1',
 'claim_stored_revision_job_v1','lease_stored_revision_job_v1','schedule_stored_revision_retry_v1',
 'complete_stored_revision_job_success_v1','reconcile_stored_revision_job_v1',
 'advance_idempotent_job_v2','mark_idempotent_outcome_unknown_v2','register_scheduler_worker'];
 n bigint; signature text;
BEGIN
 SELECT count(*) INTO n FROM pg_proc p JOIN pg_namespace s ON s.oid=p.pronamespace
 WHERE s.nspname='hwpx_agent' AND p.proname=ANY(names);
 IF n<>cardinality(names) THEN RAISE EXCEPTION USING ERRCODE='22023',MESSAGE='OWNED_ROLE_FUNCTION_NAME_NOT_UNIQUE'; END IF;
 FOR signature IN SELECT p.oid::regprocedure::text FROM pg_proc p JOIN pg_namespace s ON s.oid=p.pronamespace
   WHERE s.nspname='hwpx_agent' AND p.proname=ANY(names)
 LOOP EXECUTE format('GRANT EXECUTE ON FUNCTION %s TO p09_revision_284',signature); END LOOP;
END $$;
COMMIT;
