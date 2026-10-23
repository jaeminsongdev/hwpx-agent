"""Source-only SQL contracts, NOT SQL parsing, execution, authorization or restart proof."""
import re

OLD='migrations/postgres/0007_p14_idempotency_reconciliation.up.sql'
UP='migrations/postgres/0023_p09_stored_revision_jobs.up.sql'
DOWN='migrations/postgres/0023_p09_stored_revision_jobs.down.sql'
MAP={
    'idempotency_v2_committed_effect_qualified':'stored_revision_committed_effect_qualified_v1',
    'claim_idempotent_job_v2':'claim_stored_revision_job_v1',
    'lease_idempotent_job_v2':'lease_stored_revision_job_v1',
    'schedule_idempotent_retry_v2':'schedule_stored_revision_retry_v1',
    'complete_idempotent_job_success_v2':'complete_stored_revision_job_success_v1',
    'reconcile_idempotent_job_v2':'reconcile_stored_revision_job_v1',
}
REPLAY='''        IF NOT hwpx_agent.stored_revision_source_qualified_v1(
            p_tenant_id,p_project_id,p_branch_id,p_subject_sha256,p_source_artifact_id,
            p_source_artifact_sha256,p_expected_revision_id,p_expected_revision_generation,false
        ) THEN
            RAISE EXCEPTION USING ERRCODE='23503',MESSAGE='STORED_REVISION_REPLAY_SOURCE_NOT_QUALIFIED';
        END IF;
'''


def functions(text):return {
    m.group(1):m.group(0)for m in re.finditer(r'CREATE FUNCTION hwpx_agent\.(\w+)\([\s\S]*?\$\$;',text)}


def check(q,c):
    old=q.text(OLD);up=q.text(UP);down=q.text(DOWN);original=functions(old);current=functions(up);checks=[]
    c.require(len(current)==11,'EXACT11_NEW_STORED_SQL_FUNCTIONS')
    for before,after in MAP.items():
        text=current[after]
        if before=='claim_idempotent_job_v2':
            c.require(text.count(REPLAY)==1,'ONE_P09_REPLAY_SOURCE_ADMISSION');text=text.replace(REPLAY,'')
        for x,y in MAP.items():text=text.replace('hwpx_agent.'+y+'(','hwpx_agent.'+x+'(')
        pattern=r'hwpx_agent\.stored_revision_source_qualified_v1\(\s*p_tenant_id,\s*p_project_id,\s*(p_branch_id|v_record\.branch_id),\s*p_subject_sha256,\s*(p_source_artifact_id|v_record\.source_artifact_id),\s*(p_source_artifact_sha256|v_record\.source_artifact_sha256),\s*(?:p_expected_revision_id|v_record\.expected_revision_id),\s*(?:p_expected_generation|p_expected_revision_generation|v_record\.expected_revision_generation),\s*(?:true|false)\s*\)'
        text,n=re.subn(pattern,lambda m:"hwpx_agent.idempotency_v2_artifact_qualified(p_tenant_id,p_subject_sha256,"+m[2]+",'source',"+m[3]+")",text)
        c.require(n==(0 if before=='complete_idempotent_job_success_v2'else 1),'EXACT_DECLARED_SOURCE_PREDICATE_SUBSTITUTION')
        c.require(''.join(text.split())==''.join(original[before].split()),'FROZEN_V2_STATE_FENCE_WORKER_ATTEMPT_BACKOFF_EXPIRY_AND_TRANSACTION_IDENTICAL')
        checks.append('inverse_'+after)
    c.require('artifact.artifact_kind = p_artifact_kind'in original['idempotency_v2_artifact_qualified']and
        "'source', p_source_artifact_sha256"in original['claim_idempotent_job_v2'],'LEGACY_SOURCE_ONLY_DENIAL_REMAINS_EXACT')
    checks.append('original_source_only_boundary')
    for marker in("a.artifact_kind='result'","r.result_artifact_id=p_source_artifact_id","s.seal_kind='service_v1'",
        's.commit_request_sha256=c.commit_request_sha256','s.committed_generation=p_expected_generation',
        "a.quarantine_reason_code IS NULL",'p_require_current_head AND NOT hwpx_agent.idempotency_v2_head_matches'):
        c.require(marker in current['stored_revision_source_qualified_v1'],'SEALED_RESULT_SOURCE_BOUND_TO_HEAD_SCOPE_ACL_DIGEST_AND_STATE')
    checks.append('sealed_result_source_predicate')
    register=current['register_stored_revision_commit_intent_v1']
    for marker in("j.state IS DISTINCT FROM 'validating'",'j.lease_expires_at<=clock_timestamp()',
        'a.commit_authorization_id=p_authorization','old.commit_request_sha256',
        'p_precommit,r.transaction_receipt_sha256','p_intent,p_intent_sha','r.expected_effect_sha256'):
        c.require(marker in register,'EXACT_JOB_FENCE_AUTHORITY_AND_TWO_DISTINCT_RECEIPT_IDENTITIES')
    checks.append('registered_v2_lease_and_distinct_precommit_intent')
    for marker in('i.commit_request_sha256=NEW.commit_request_sha256','i.commit_id=NEW.commit_id',
        'i.new_revision_id=NEW.committed_revision_id','i.fencing_token=j.fencing_token',
        'i.authorization_id::text=current_setting',"a.artifact_kind='result'"):
        c.require(marker in current['guard_stored_revision_commit_intent_v1'],'MANDATORY_EXACT_REQUEST_INTENT_FOR_RESULT_SOURCE_COMMIT_ONLY')
    checks.append('mandatory_exact_intent_commit_trigger')
    c.require('FORCE ROW LEVEL SECURITY'in up and 'stored_revision_commit_intents_immutable BEFORE UPDATE OR DELETE'in up
        and len(re.findall(r'^REVOKE ALL ON FUNCTION ',up,re.M))==11 and not re.search(r'^GRANT ',up,re.M)
        and 'CREATE OR REPLACE FUNCTION'not in up,'NO_LEGACY_FUNCTION_REPLACEMENT_NO_PUBLIC_OR_AUTOMATIC_ROLE_GRANTS')
    checks.append('forced_RLS_immutability_and_revoked_functions')
    read=current['read_stored_revision_commit_intent_v1']
    c.require(not re.search(r'\b(?:INSERT|UPDATE|DELETE|TRUNCATE|lease_expires_at)\b',read)and'RETURN NEXT i'in read,
        'HISTORICAL_INTENT_READ_NEVER_RETRIES_OR_REQUIRES_LIVE_LEASE')
    checks.append('historical_read_no_effect_or_retry_claim')
    c.require(down.index('STORED_REVISION_DOWN_PRESERVES_EXISTING_RECORDS')<down.index('DROP TABLE')
        and "a.artifact_kind='result'"in down and 'DROP TABLE hwpx_agent.artifacts'not in down,
        'ROLLBACK_REFUSES_PERSISTED_RESULT_SOURCE_JOBS_OR_INTENTS_AND_NEVER_DELETES_ARTIFACTS')
    checks.append('empty_only_rollback_preserves_jobs_and_artifacts')
    return dict(kind='static_source_contract_only_NOT_SQL_parse_or_runtime',checks=checks,
        derived_functions=6,original_migrations_replaced=0,SQL_executed=False)
