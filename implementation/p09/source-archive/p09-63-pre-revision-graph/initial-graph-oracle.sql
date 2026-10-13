-- Read-only postconditions on the complete owned tenant graph; original guards stay active.
DO $$
DECLARE t uuid := '00000000-0000-0000-0000-000000000001';
BEGIN
 IF (SELECT count(*) FROM hwpx_agent.revisions WHERE tenant_id=t) <> 6 THEN RAISE EXCEPTION 'P63_REVISION_COUNT'; END IF;
 IF (SELECT count(*) FROM hwpx_agent.revision_graph_seals WHERE tenant_id=t AND seal_kind='service_v1') <> 6 THEN RAISE EXCEPTION 'P63_SEAL_COUNT'; END IF;
 IF (SELECT count(*) FROM hwpx_agent.revision_commit_receipts WHERE tenant_id=t) <> 6 THEN RAISE EXCEPTION 'P63_RECEIPT_COUNT'; END IF;
 IF (SELECT count(*) FROM hwpx_agent.revision_parents WHERE tenant_id=t) <> 5 THEN RAISE EXCEPTION 'P63_PARENT_EDGE_COUNT'; END IF;
 IF (SELECT count(*) FROM hwpx_agent.jobs WHERE tenant_id=t) <> 7
 OR (SELECT count(*) FROM hwpx_agent.jobs WHERE tenant_id=t AND state='succeeded') <> 6
 OR (SELECT count(*) FROM hwpx_agent.jobs WHERE tenant_id=t AND state='validating') <> 1 THEN RAISE EXCEPTION 'P63_JOB_COUNT'; END IF;
 IF (SELECT count(*) FROM hwpx_agent.job_attempts WHERE tenant_id=t) <> 7
 OR (SELECT count(*) FROM hwpx_agent.job_attempts WHERE tenant_id=t AND state='succeeded') <> 6
 OR (SELECT count(*) FROM hwpx_agent.job_attempts WHERE tenant_id=t AND state='running') <> 1 THEN RAISE EXCEPTION 'P63_ATTEMPT_COUNT'; END IF;
 IF (SELECT count(*) FROM hwpx_agent.idempotency_commit_authorizations WHERE tenant_id=t) <> 1 THEN RAISE EXCEPTION 'P63_AUTH_COUNT'; END IF;
 IF (SELECT count(*) FROM hwpx_agent.full_document_ir_intents WHERE tenant_id=t) <> 5 THEN RAISE EXCEPTION 'P63_IR_INTENT_COUNT'; END IF;
 IF (SELECT head_generation FROM hwpx_agent.branches WHERE tenant_id=t AND branch_id='00000000-0000-0000-0000-000000000003') <> 5
 OR (SELECT head_generation FROM hwpx_agent.branches WHERE tenant_id=t AND branch_id='00000000-0000-0000-0000-000000000004') <> 1 THEN RAISE EXCEPTION 'P63_BRANCH_HEAD_COUNT'; END IF;
END $$;
SELECT 'P09_REVISION_GRAPH_METADATA_PASS assertions=9';
