"""Audit new registered recovery evidence and policy interpretation; never replay runtime/tests."""
import json,re,time
from types import SimpleNamespace as NS
import run_registered_recovery_postgres as latest
shared,c,a,tools,compact,audit=latest.shared,latest.c,latest.a,latest.tools,latest.compact,latest.audit
OUTPUT='implementation/p09/evidence/p09-361-registered-recovery-sync299.v1.json'
DRIVER='tools/p09/run_registered_recovery_sync.py'
REPORT='implementation/p09/P09_REGISTERED_RECOVERY_PROGRESS.md'
ACK_REPORT='implementation/p09/P09_SQL23_ACK_RECOVERY_PROGRESS.md'
DOC_BASE='implementation/p09/evidence/p09-361-sql23-ack-sync296.v1.json'
PROFILE='protocol/migrations/p09-stored-revision-jobs-v1.md';PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,PROGRESS,'CURRENT_STATE.md',ACK_REPORT}
TITLE='## 등록 영수증 기반 읽기 전용 복구\n';OLDTITLE='## SQL23 응답 유실과 복구\n'
BEFORE='입력/route/scanner/validator는 합성이며 실제 네트워크/crash/키 유실 복구·전체 거부 경계·attempt 이력 정합성과 실제 P09 제품 실행 자격은 미완료다.\n'
AFTER='''등록 행과 암호화 영수증만 사용하는 읽기 전용 복구도 구현하고 실제 DB 재시작 후 별도 요청 파일 없이 확인했다.
관측된 attempt 이력 보존은 기존 P14의 terminal/immutable 계약과 일치한다. 입력/route/scanner/validator는 합성이며
실제 네트워크/crash/키 유실 복구·전체 거부 경계와 실제 P09 제품 실행 자격은 미완료다.
'''
POLICY='implementation/p14/P14-07_DURABLE_POLICY.md'
def tight(t):return ''.join(t.split())
def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGISTERED_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REGISTERED_RECOVERY_SYNC',own_cpu_selection=selection,current_run_Rust_DB_or_tests_replayed=False,
        document_audit_not_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,actual_P09_product_or_Native_execution=False,
        Native011_executed=False,prior_Native_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT));units=compact.unpack(q.json(latest.components.OUTPUT))
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='5cb52bcd3daa26f9f3de0789ceb7ac28e298f56a29dae6d639eabc775ca10386'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==681 and passed['actual_registered_DB_checks']==3,'EXACT298_ACTUAL_REGISTERED_DB3_CLOSURE')
        c.require(q.snapshots[latest.components.OUTPUT]['sha256']=='ee60ee3fcb2fe75189fdd1139bc24f91f1fc63d1fab662a8811c41b37b413c71'and units['cleanup']
            and units['fresh_inputs']==units['final_fresh_hashes']==674 and[len(s['tests'])for s in units['steps']]==[10,12]
            and all(status=='ok'for s in units['steps']for _,status in s['tests']),'EXACT297_NEW10_AND_AFFECTED12_WITHOUT_SKIPS')
        old={p['path']:p for p in passed['source_pins']}
        for n in latest.components.CHANGED|latest.components.NEW|latest.CHANGED|latest.NEW|{latest.components.OLD_TEST}:
            q.pin(n);c.require(q.snapshots[n]==old[n],'SCOPED_NEW_API_TESTS_AND_NATIVE_PROBE_UNCHANGED')
        observations=q.json('target/p09-sql23-storage-observations-298.json');probe=observations['probes'][-1]
        c.require(q.snapshots['target/p09-sql23-storage-observations-298.json']['sha256']=='94f8bcf6e48a576f75ad4a5633d775022b0f7ef336672bcea27a5adbbff8a4a8'
            and probe['registered_recovery_checks']==3 and probe['retained_request_file_used']is False and probe['request_fixture_preserved']
            and probe['execution_retried']is False and observations['snapshots'][0]==observations['snapshots'][1]
            and observations['blob_snapshots'][0]==observations['blob_snapshots'][1]and len(observations['blob_snapshots'][0])==6
            and len(observations['postmasters'])==2 and all(p['normal_stop']for p in observations['postmasters']),'REAL_NEW_READER_NO_RETAINED_REQUEST_OR_DOMAIN_MUTATION')
        for result in(units,passed):
            for s in result['steps']:
                j=s['owned_job'];c.require(j['owned_tree_empty']and j['cleanup_confirmed']and j['job_handle_closed']and j['last_job_accounting']['active_processes']==0
                    and j['limits_readback']['cpu_hard_cap_machine_percent']==6.25,'ALL_FOUR_JOBS_TERMINAL_WITH_UNCHANGED_PROTECTION')
        policy=q.text(POLICY);meta=q.json('implementation/p14/postgres/p14-idempotency-reconciliation-v2.json')
        original=next(p for p in meta['source_files']if p['path']==POLICY)
        c.require(q.snapshots[POLICY]['sha256']==original['sha256']and tight('each prior attempt remains terminal and immutable')in tight(policy),'ORIGINAL_P14_TERMINAL_ATTEMPT_IMMUTABILITY_CONTRACT_NOT_INVENTED')
        sql=q.text('migrations/postgres/0023_p09_stored_revision_jobs.up.sql');at=sql.index('CREATE FUNCTION hwpx_agent.reconcile_stored_revision_job_v1(');body=sql[at:]
        committed=body[body.index("IF p_mode = 'committed' THEN"):body.index('IF NOT hwpx_agent.idempotency_v2_artifact_qualified')]
        c.require('UPDATE hwpx_agent.jobs SET'in committed and'UPDATE hwpx_agent.idempotency_records SET'in committed and'UPDATE hwpx_agent.job_attempts'not in committed,'CURRENT_SQL_RECONCILES_JOB_RECORD_WITHOUT_REWRITING_TERMINAL_ATTEMPT')
        old_obs=q.json('target/p09-sql23-ack-observations-295.json');case=next(x for x in old_obs['cases']if x['case']=='cas_after')
        c.require(case['snapshots'][1]['job_state']=='succeeded'and case['snapshots'][1]['record_state']=='terminal_success'
            and case['snapshots'][1]['attempt_state']=='unknown_outcome','OBSERVED_DIFFERENCE_MATCHES_EXISTING_CONTRACT')
        docs=q.json(DOC_BASE);c.require(q.snapshots[DOC_BASE]['sha256']=='1105f2a24961115ba066eb63dd4a460d81f7727618aedd81295b132919aa5050'and docs['cleanup'],'EXACT296_DOCUMENT_BASE')
        old_docs={p['path']:p for p in docs['source_pins']}
        for n in DOCS|{DRIVER,REPORT}:q.pin(n)
        text=q.text('CURRENT_STATE.md');at=text.index('> 2026-10-21 P09 ACTIVE 최신 SQL23 응답 유실과 복구')
        audit.inverse(text[at:],old_docs['CURRENT_STATE.md'],'ALL_PRIOR_CURRENT_STATE_HISTORY_PRESERVED');blocks=[text[:at]]
        for n in(PROGRESS,PROFILE):
            text=q.text(n);start=text.index(TITLE);end=text.index(OLDTITLE,start);blocks.append(text[start:end]);restored=text[:start]+text[end:]
            if n==PROFILE:c.require(restored.count(AFTER)==1,'ONE_CURRENT_REGISTERED_API_INTRO');restored=restored.replace(AFTER,BEFORE)
            audit.inverse(restored,old_docs[n],'ALL_PRIOR_SEARCH_ROWS_AND_CONTRACT_HISTORY_PRESERVED')
        text=q.text(ACK_REPORT);at=text.index('# SQL23 응답 유실과 실제 DB 복구');audit.inverse(text[at:],old_docs[ACK_REPORT],'ORIGINAL_ACK_EVIDENCE_REPORT_RETAINED_AFTER_FOLLOWUP_NOTE')
        c.require(len(set(re.findall(r'^\| SEARCH-(\d{3}) \|',q.text(PROGRESS),re.M)))==19,'ALL19_SEARCH_ROWS_UNCHANGED')
        for block in blocks:
            for marker in('reconcile_registered_stored_commit','RegistrationNotObserved','Registered(NotObserved)','Registered(Committed)','별도 ServiceRequest 파일 없이',
                '신규10+영향 기존12=22pass','674fresh/final674','681fresh/final681','116.672','20.90%','43.0679%',
                'active0/empty/handle closed','CPU cap6.25%','RAM/commit95%','공식158/249','잔여91','next165','P09/A12/A13 OPEN','Native011 미승인/미실행','routing_allowed=false'):
                c.require(tight(marker)in tight(block),'ACCURATE_NEW_API_SCOPE_RESOURCES_AND_OPEN_GATES')
        report=q.text(REPORT)
        for marker in('876.64MiB','72.95MiB','completed-handles.preserved.json','SQL7','SQL23','terminal/immutable','실제 HWPX','네트워크/crash/키 유실','각 영수증을 한 번씩'):
            c.require(marker in report,'FULL_REGISTERED_API_LIMITS_POLICY_AND_REUSE_REPORTED')
        q.finish();guard.check(force=True);row.update(state='PASS_REGISTERED_RECOVERY_UNIT22_ACTUAL_DB3_AND_POLICY_DOC_SYNC_NOT_PRODUCT_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            prior_unit_cases=22,prior_actual_DB_checks=3,attempt_history_interpretation='matches_existing_terminal_immutable_policy',SQL_migrations_changed=False,
            next_work='remaining_actual_negative_boundaries_and_qualified_P09_product_dispatcher')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,StopIteration)as error:
        code=str(error);row.update(error_type=type(error).__name__,error_code=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code)else'REGISTERED_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
