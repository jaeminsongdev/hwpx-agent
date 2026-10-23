"""Reconcile actual SQL23 job15/restart evidence and local docs; never repeat Rust/DB execution."""
import json,re,time
from types import SimpleNamespace as NS
import run_sql23_job_lifecycle as latest
shared,c,a,tools,compact=latest.shared,latest.c,latest.a,latest.tools,latest.compact
audit=latest.audit
OUTPUT='implementation/p09/evidence/p09-361-sql23-job-lifecycle-sync287.v1.json'
DRIVER='tools/p09/run_sql23_job_lifecycle_sync.py'
DOC_BASE='implementation/p09/evidence/p09-361-sql23-service-admission-sync285.v1.json'
PROFILE='protocol/migrations/p09-stored-revision-jobs-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,PROGRESS,'CURRENT_STATE.md'}
TITLE='## SQL23 작업의 실제 claim과 lease\n'
OLDTITLE='## SQL23 서비스 계정의 실제 접속과 거부\n'
OLD_CURRENT='> 2026-10-21 P09 ACTIVE 최신 SQL23 서비스 계정의 실제 접속과 거부'
BEFORE='''실제 blob/AEAD/scanner/issuer·worker 등록/lease·job 함수/trigger의 실제 실행·등록/CAS·
완료/확인 유실/재시작 복구와 제품 실행 자격은 미완료다.
'''
AFTER='''실제 서비스 계정으로 SQL23 claim/lease/단계 전환과 거부를 포함한15개 검사와 DB 재시작 후 한 시도 보존도 확인했다.
실제 blob/AEAD/scanner/issuer·SQL23 intent 등록/결과 CAS/성공 완료/확인 유실 복구와 제품 실행 자격은 미완료다.
'''
EXPECTED=['actual_new_claim','exact_replay_without_attempt','same_key_changed_request_denied','unsealed_source_kind_denied',
    'unregistered_worker_denied','wrong_worker_profile_denied','wrong_worker_capability_denied','draining_worker_denied',
    'actual_worker_lease_authorization','duplicate_lease_denied','foreign_execution_denied','skipped_stage_denied',
    'three_actual_ordered_transitions','uncommitted_effect_completion_denied','final_replay_one_attempt']
def tight(text):return ''.join(text.split())
def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SQL23_JOB_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SQL23_JOB_SYNC',own_cpu_selection=selection,current_run_Rust_or_DB_replayed=False,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_blob_AEAD_or_product_execution=False,SQL23_result_CAS_or_completion=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT))
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='17fc9b845c7d8106e56331f7910c9a703cd65e5dcfd2d561c2184a8213ac1454'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==228
            and passed['actual_job_checks']==EXPECTED and passed['actual_job_restart_observed'],'EXACT286_JOB15_AND_RESTART_SOURCE_CLOSURE')
        for pin in passed['source_pins']:
            q.pin(pin['path']);c.require(q.snapshots[pin['path']]==pin,'ALL286_PROBE_SERVICE_SQL_CRYPTO_OWNERSHIP_SOURCES_UNCHANGED')
        observations=q.json('target/p09-sql23-job-observations-286.json')
        c.require(q.snapshots['target/p09-sql23-job-observations-286.json']['sha256']=='44c3dfa6475f2b57859f0c739eab31e244d9ada462657c87f5fc82182883a278'
            and observations['all_owned_postmasters_normal_stop']and len(observations['postmasters'])==2
            and all(p['normal_stop']for p in observations['postmasters']),'EXACT286_TWO_NORMAL_POSTMASTER_STOPS')
        c.require(observations['checks']==EXPECTED and observations['probes'][1]['checks']==EXPECTED
            and sum(n.endswith('_denied')for n in EXPECTED)==10,'FIFTEEN_ACTUAL_GUARDS_TEN_INDEPENDENT_SQLSTATE_NEGATIVES')
        state=dict(job_state='validating',attempt=1,fence=1,record_state='in_progress',attempt_rows=1,authorization_rows=1,intent_rows=0,revisions=1,all_jobs=2)
        c.require(observations['snapshots']==[state,state]and observations['probes'][2]['new_worker_or_execution']is False
            and observations['actual_blob_AEAD_or_product_execution']is False and observations['SQL23_result_CAS_or_completion']is False,'EXACT286_RESTART_NO_EXTRA_ATTEMPT_OR_FALSE_COMPLETION')
        for step in passed['steps']:
            job=step['owned_job'];limits=job['limits_readback'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['affinity_mask']==4
                and limits['breakaway_disabled']and limits['kill_on_close'],'BOTH_OWNED_JOBS_TERMINAL_WITH_UNCHANGED_RESOURCE_LIMITS')
        docs=q.json(DOC_BASE);c.require(q.snapshots[DOC_BASE]['sha256']=='47f3fc305a4e7bdb49e0015df0b0d2da7985a38a91f721e6744120b9316b64c1'
            and docs['cleanup'],'EXACT285_PRIOR_DOCUMENT_CLOSURE')
        old={p['path']:p for p in docs['source_pins']}
        for name in DOCS|{DRIVER}:q.pin(name)
        current=q.text('CURRENT_STATE.md');at=current.index(OLD_CURRENT)
        audit.inverse(current[at:],old['CURRENT_STATE.md'],'ALL_PREVIOUS_CURRENT_STATE_AND_FAILURES_UNCHANGED');blocks=[current[:at]]
        for name in(PROGRESS,PROFILE):
            text=q.text(name);start=text.index(TITLE);end=text.index(OLDTITLE,start);blocks.append(text[start:end]);restored=text[:start]+text[end:]
            if name==PROFILE:
                c.require(restored.count(AFTER)==1,'ONE_JOB_SCOPE_INTRO_UPDATE');restored=restored.replace(AFTER,BEFORE)
            audit.inverse(restored,old[name],'ALL_PREVIOUS_SEARCH_ROWS_AND_CONTRACT_HISTORY_UNCHANGED')
        c.require(len(set(re.findall(r'^\| SEARCH-(\d{3}) \|',q.text(PROGRESS),re.M)))==19,'ALL19_SEARCH_ROWS_RETAINED')
        for block in blocks:
            for marker in('p09_sql23_jobs','StoredJobLifecycleRepository','합성 SQL 메타데이터','revision/seal 직접 삽입',
                '15개 검사','거부10개','실제 SQLSTATE','시도1/fence1','attempt행1','authorization행1','intent0','revision1','job2',
                '228fresh/final228','48.547','20.08%','44.8425%','postmaster2회 정상 종료','active0/empty/handle closed',
                'CPU cap6.25%','private8%/stop7%','RAM/commit95%','실제 blob/AEAD/scanner/issuer','SQL23 intent 등록/결과 CAS/성공 완료/확인 유실 복구',
                '공식158/249','잔여91','next165','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행','routing_allowed=false'):
                c.require(tight(marker)in tight(block),'ACCURATE_SQL23_JOB_SCOPE_RESOURCES_AND_OPEN_GATES')
        q.finish();guard.check(force=True)
        row.update(state='PASS_ACTUAL_SQL23_JOB15_RESTART_AND_DOC_SYNC_NOT_AEAD_CAS_OR_P09_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            prior_actual_job_checks=EXPECTED,prior_negative_SQLSTATE_cases=10,prior_normal_postmaster_stops=2,
            next_work='actual_blob_AEAD_stored_intent_registered_CAS_completion_unknown_recovery_and_qualified_product_dispatcher')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        code=str(error);row.update(error_type=type(error).__name__,error_code=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code)else'SQL23_JOB_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
