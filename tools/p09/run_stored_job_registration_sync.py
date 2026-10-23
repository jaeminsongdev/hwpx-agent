"""Selected connector/model/registration/doc closure; no Cargo, DB or full901 replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_stored_job_registration_confirmed as latest
import run_stored_revision_jobs_sync as previous_sync
base=latest.base
shared,c,a,audit,tools,compact=base.shared,base.c,base.a,base.audit,base.tools,base.compact
OUTPUT='implementation/p09/evidence/p09-361-stored-job-registration-sync269.v1.json'
DRIVER='tools/p09/run_stored_job_registration_sync.py'
PROFILE='protocol/migrations/p09-stored-revision-jobs-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
RETAINED=previous_sync.RETAINED|{base.DRIVER,latest.DRIVER,latest.predecessor.DRIVER,latest.predecessor.origin.DRIVER,
    base.ISSUER,base.CONNECTOR,base.ADMISSION,base.TYPES,base.ADAPTER,base.CHILD,base.PARENT,base.TEST}


def tight(text):return ''.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGISTERED_JOB_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_JOB_REGISTRATION_SYNC',own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_PostgreSQL_or_process_restart=False,SQL23_applied=False,SQL23_catalog_privilege_or_runtime_qualified=False,
        durable_idempotency_complete=False,P09_product_execution_or_commit=False,actual_cases_reexecuted=0,full901_inputs_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT))
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='3d106c605c830a79488bf2584704231790ec38a2ec670c109b59c8b738a9400d'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==901 and passed['total_executed_cases']==9
            and passed['unchanged_cases_reused']==34 and passed['test_scratch_empty'],'EXACT268_CONFIRMED9_AND_REUSED34_WITH901_SOURCE_CLOSURE')
        tested={p['path']:p for p in passed['source_pins']}
        for name in sorted(RETAINED|base.migration_inputs(guard.check)):
            q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_CONNECTOR_ALL23_MIGRATIONS_CALLBACK_CONFIRMATION_AND_GATE_DENIALS_MATCH268')
        cases={'registered_v1::'+n for n in base.names(q,base.TEST)};c.require(len(cases)==9,'EXACT9_CONFIRMED_REGISTRATION_CASE_NAMES');tools.good_step(passed['steps'][0],cases)
        original=compact.unpack(q.json(latest.predecessor.OUTPUT))
        c.require(q.snapshots[latest.predecessor.OUTPUT]['sha256']=='a5c69bdcde17d83fcdff94dd77ee2a8f7b203393a91e5eb2177d427e09059312'
            and original['cleanup']and original['total_executed_cases']==43 and original['fresh_inputs']==original['final_fresh_hashes']==903,
            'EXACT267_MODELS5_REGISTERED9_AFFECTED29_WITH903_CLOSURE')
        models={base.PREFIX+n for n in base.names(q,base.ADMISSION)}
        allproduct=set(base.names(q,base.PARENT))|{'recovery_v1::'+n for n in base.names(q,base.prior.RECOVERY_TEST)}|{'precommit_v1::'+n for n in base.names(q,base.prior.TEST)}|cases
        tools.good_step(original['steps'][0],models);tools.good_step(original['steps'][1],allproduct)
        c.require(len(models)==5 and len(allproduct)==38 and len(original['newly_scoped_existing_compilation_migrations'])==21,'EXACT_REUSED34_AND_ALL23_MIGRATION_INPUTS')
        for step in original['steps']+passed['steps']:
            job=step['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0,'ALL267_268_JOBS_TERMINAL_EMPTY_CLOSED')
        latest.inverse(q,{p['path']:p for p in original['source_pins']})
        docs=q.json(base.DOC_BASE);c.require(q.snapshots[base.DOC_BASE]['sha256']=='78a75141ba6c7ce3d4a09407626843451edc01b985bf6c00d4902c4617edae10'
            and docs['cleanup'],'EXACT264_PRIOR_DOCUMENT_CLOSURE')
        old={p['path']:p for p in docs['source_pins']}
        for name in(PROFILE,PROGRESS,'CURRENT_STATE.md',DRIVER):q.pin(name)
        current=q.text('CURRENT_STATE.md');at=current.index('> 2026-10-20 P09 ACTIVE 최신 precommit receipt와 저장 job 경계')
        audit.inverse(current[at:],old['CURRENT_STATE.md'],'ALL_PREVIOUS_CURRENT_STATE_AND_FAILURE_HISTORY_UNCHANGED')
        progress=q.text(PROGRESS);start=progress.index('## SQL23 접속 검사와 CAS 전 등록\n');end=progress.index('## Precommit receipt와 저장 job 경계\n',start)
        audit.inverse(progress[:start]+progress[end:],old[PROGRESS],'ALL19_SEARCH_ROWS_AND_PREVIOUS_FEATURE_RECORDS_UNCHANGED')
        c.require(len(set(re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M)))==19,'EXACT19_SEARCH_ROWS_NO_PROMOTION')
        profile=q.text(PROFILE);pstart=profile.index('## SQL23 접속 검사와 CAS 전 등록\n');pend=profile.index('## 두 receipt의 역할\n',pstart)
        restored=profile[:pstart]+profile[pend:]
        before='SQL23은 구문/실행 미검증·미적용이며 Rust schema23 connector/등록 callback도 미연결이다.\n'
        after='''SQL23은 여전히 구문/실행 미검증·미적용이다. 전용 Rust connector와 CAS 전 등록 callback은 구현·
컴파일·모델 검증했지만 실제 DB 연결 증거는 없다. ArtifactService SQL23 profile과 typed job coordinator,
실제 claim/lease/완료·중단/재시작 검증은 미완료다.
'''
        c.require(restored.count(after)==1,'ONE_PREVIOUS_UNIMPLEMENTED_STATUS_REPLACED_WITH_COMPILED_MODEL_ONLY_STATUS')
        audit.inverse(restored.replace(after,before),old[PROFILE],'ALL_PRECOMMIT_SQL_SOURCE_CONTRACTS_AND_FAILURE_HISTORY_UNCHANGED')
        for text in(current[:at],progress[start:end],profile[pstart:pend]):
            for marker in('LocalPostgresStoredRevisionJobsRepository','schema1..23','bind_registered','registration_response','registered_job_intent',
                'SQL23은 여전히 미적용·실제 catalog/권한/함수 실행 미검증','E0425','Cargo/시험0',
                '모델5+등록9+영향29=43pass','903fresh/final903','등록9pass','901fresh/final901','모델5/기존29=34개는 재실행하지 않았다',
                '128.313','12.000','0.06','10.312','877.45MiB/2.75400%','26.95%','46.5261%',
                'active0/empty/handle closed','CPU cap6.25%','private8%/stop7%','RAM/commit95%','in-memory',
                '실제 SQL23 catalog/권한/등록/CAS/DB 재시작 증거가 아니다','ArtifactService SQL23 profile·typed claim/lease/complete coordinator·실제 DB 검증은 미완료',
                '158/249','잔여91','next165','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행','routing_allowed=false'):
                c.require(tight(marker)in tight(text),'ACCURATE_COMPILED_CONNECTOR_MODEL43_CONFIRMED9_REUSE34_METRICS_AND_OPEN_GATES')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_SCHEMA23_MODEL5_REGISTERED9_PRIOR29_AND_DOC_SYNC_NOT_SQL_RUNTIME_P09_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,retained_evidence_union_cases=43,
            confirmed_registration_cases=9,unchanged_cases_reused=34,all23_migration_inputs_retained=True,
            previous265_266_failures_preserved_in_history=True,next_work='ArtifactService_SQL23_profile_typed_job_coordinator_then_real_DB_runtime_restart_evidence')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REGISTERED_JOB_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
