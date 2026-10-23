"""Document-only reconciliation of prior1+new3 ack cases, never runtime or old test replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_sql23_ack_loss as latest
shared,c,a,tools,compact,audit=latest.shared,latest.c,latest.a,latest.tools,latest.compact,latest.audit
OUTPUT='implementation/p09/evidence/p09-361-sql23-ack-sync296.v1.json'
DRIVER='tools/p09/run_sql23_ack_sync.py'
REPORT='implementation/p09/P09_SQL23_ACK_RECOVERY_PROGRESS.md'
DOC_BASE='implementation/p09/evidence/p09-361-sql23-real-storage-sync291.v1.json'
PROFILE='protocol/migrations/p09-stored-revision-jobs-v1.md';PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,PROGRESS,'CURRENT_STATE.md'}
TITLE='## SQL23 응답 유실과 복구\n';OLDTITLE='## 디스크 AEAD와 SQL23 등록 CAS 완료\n'
BEFORE='입력/route/scanner/validator는 합성이며 확인 유실/unknown 복구·전체 거부 경계·scanner/issuer와 실제 P09 제품 실행 자격은 미완료다.\n'
AFTER='''호출자 경계의 합성 응답 유실4개도 실제 SQL/AEAD에 연결해 재시작 후 unknown 보존/committed 복구를 확인했다.
입력/route/scanner/validator는 합성이며 실제 네트워크/crash/키 유실 복구·전체 거부 경계·attempt 이력 정합성과 실제 P09 제품 실행 자격은 미완료다.
'''
def tight(t):return ''.join(t.split())
def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'ACK_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_ACK_SYNC',own_cpu_selection=selection,current_run_Rust_DB_or_execution_replayed=False,
        document_audit_not_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,actual_network_fault=False,
        actual_P09_product_or_Native_execution=False,Native011_executed=False,prior_Native_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT));prior=compact.unpack(q.json(latest.PRIOR_CASE))
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='c84559aaaa5b3e0185525e18febeec4c3c385f717e725983d3276676870a9485'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==685 and passed['current_executed_ack_cases']==3
            and passed['prior_completed_ack_cases_reused']==1 and passed['ack_case_union']==4,'EXACT295_NEW_THREE_NOT_FOUR_REPLAYED')
        c.require(q.snapshots[latest.PRIOR_CASE]['sha256']=='ff84f93fb99f57b8b5cd308ec6e9d6724a75451ba6cf45996cf7a3f8d533c8fb'
            and prior['cleanup']and prior['accepted_ack_cases']==['register_after'],'EXACT294_PREVIOUS_ONE_WITH_LATE_SOURCE_CLOSURE')
        old={p['path']:p for p in passed['source_pins']}
        for n in latest.NEW:q.pin(n);c.require(q.snapshots[n]==old[n],'SCOPED_NEW_ACK_SOURCES_AND_PRIOR_FAILURES_UNCHANGED')
        observed=q.json('target/p09-sql23-ack-observations-295.json');first=q.json('target/p09-sql23-ack-case-293-register_after.json')
        c.require(q.snapshots['target/p09-sql23-ack-observations-295.json']['sha256']=='2953d3ae82c5ee00373c14d24a5b22c623d05c127e5945dda516e07d2dbccda5'
            and q.snapshots['target/p09-sql23-ack-case-293-register_after.json']['sha256']=='da6dcd0eba3ebc63806da99e0f532d9bc1d0e6975b8e0d9ec2d69e677663d2a1','EXACT_CURRENT_THREE_AND_PRIOR_ONE_OBSERVATIONS')
        cases=[first['case']]+observed['cases'];c.require([r['case']for r in cases]==['register_after','cas_before','cas_after','complete_after'],'FOUR_DISTINCT_ACK_CASES')
        for r in cases:c.require(r['complete']and r['blob_snapshots'][0]==r['blob_snapshots'][1]and len(r['blob_snapshots'][0])==6
            and r['snapshots'][0]['attempt']==r['snapshots'][1]['attempt']==1 and r['probes'][-1]['execution_retried']is False,'ALL_FOUR_REAL_AEAD_AND_SINGLE_ATTEMPT_RESTART')
        c.require([r['probes'][-1]['committed_observed']for r in cases]==[False,False,True,True]
            and [r['probes'][-1]['job_reconciled_committed']for r in cases]==[False,False,True,False]
            and sum(r['probes'][-1]['oracle_negative_SQLSTATE55000']for r in cases)==3
            and cases[2]['snapshots'][1]['attempt_state']=='unknown_outcome','EXACT_UNKNOWN_VS_COMMITTED_AND_RETAINED_ATTEMPT_HISTORY')
        c.require(observed['actual_initdb_count']==observed['actual_schema23_application_count']==1 and observed['prior_register_after_executed']is False
            and len(observed['postmasters'])==7 and all(p['normal_stop']for p in observed['postmasters']),'ONE_INITIALIZATION_SEVEN_NORMAL_STOPS_NO_PRIOR_EXECUTION')
        for pin in observed['case_checkpoint_pins']:q.pin(pin['path']);c.require(q.snapshots[pin['path']]==pin,'THREE_EXACT_DURABLE_CASE_CHECKPOINTS')
        for s in passed['steps']:
            j=s['owned_job'];c.require(j['owned_tree_empty']and j['cleanup_confirmed']and j['job_handle_closed']and j['last_job_accounting']['active_processes']==0
                and j['limits_readback']['cpu_hard_cap_machine_percent']==6.25,'BOTH_OWNED_JOBS_TERMINAL_PROTECTION_UNCHANGED')
        docs=q.json(DOC_BASE);c.require(q.snapshots[DOC_BASE]['sha256']=='8abf3b06ad77cb8ca1b0b405e162ffc165622635aaadf21f99234a2e94566fe9'and docs['cleanup'],'EXACT291_DOCUMENT_BASE')
        old_docs={p['path']:p for p in docs['source_pins']}
        for n in DOCS|{DRIVER,REPORT}:q.pin(n)
        text=q.text('CURRENT_STATE.md');at=text.index('> 2026-10-21 P09 ACTIVE 최신 디스크 AEAD와 SQL23 등록 CAS 완료')
        audit.inverse(text[at:],old_docs['CURRENT_STATE.md'],'ALL_PREVIOUS_CURRENT_HISTORY_UNCHANGED');blocks=[text[:at]]
        for n in(PROGRESS,PROFILE):
            text=q.text(n);start=text.index(TITLE);end=text.index(OLDTITLE,start);blocks.append(text[start:end]);restored=text[:start]+text[end:]
            if n==PROFILE:c.require(restored.count(AFTER)==1,'ONE_ACK_SCOPE_INTRO');restored=restored.replace(AFTER,BEFORE)
            audit.inverse(restored,old_docs[n],'ALL_PREVIOUS_SEARCH_AND_CONTRACT_HISTORY_UNCHANGED')
        c.require(len(set(re.findall(r'^\| SEARCH-(\d{3}) \|',q.text(PROGRESS),re.M)))==19,'SEARCH19_UNCHANGED')
        for block in blocks:
            for m in('register_after/cas_before','SQLSTATE55000','cas_after','complete_after','이전1개 재사용+이번3개','attempt1/fence1','685fresh/final685',
                '123.438','21.63%','41.8705%','initdb1회/schema23 적용1회','postmaster7회 정상 종료','active0/empty/handle closed',
                'CPU cap6.25%','RAM/commit95%','공식158/249','잔여91','next165','P09/A12/A13 OPEN','Native011 미승인/미실행','routing_allowed=false'):
                c.require(tight(m)in tight(block),'ACCURATE_REUSE_RESOURCE_AND_OPEN_GATE_SUMMARY')
        report=q.text(REPORT)
        for m in('98.52%','73.83MiB','SQLSTATE23514','runtime1583','684fresh/final684','706.57MiB','74.03MiB','키','NOT_RUN','unknown_outcome','고유4개'):
            c.require(m in report,'FULL_REPORT_PRESERVES_FAILURES_AND_UNVERIFIED_BOUNDARIES')
        q.finish();guard.check(force=True);row.update(state='PASS_SQL23_ACK_CASE_UNION4_AND_DOC_SYNC_NOT_NETWORK_RUNTIME_OR_P09_GATE',fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes,prior_case_reused=1,current_cases_executed=3,ack_case_union=4,
            next_work='attempt_history_consistency_remaining_negative_boundaries_and_qualified_product_dispatcher')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        code=str(error);row.update(error_type=type(error).__name__,error_code=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code)else'ACK_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
