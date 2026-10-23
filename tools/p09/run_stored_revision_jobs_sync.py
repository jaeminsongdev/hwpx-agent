"""Selected Rust29 + pending SQL23 source/doc closure, no Cargo/DB/full872 replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_stored_revision_jobs_checker_recovery as tested_driver
import run_stored_commit_intent_sync as previous_sync
base=tested_driver.base
shared,c,a,audit,tools,compact=base.shared,base.c,base.a,base.audit,base.tools,base.compact
OUTPUT='implementation/p09/evidence/p09-361-stored-revision-jobs-sync264.v1.json'
DRIVER='tools/p09/run_stored_revision_jobs_sync.py'
PROFILE='protocol/migrations/p09-stored-revision-jobs-v1.md'
OLD_PROFILE='protocol/migrations/p09-stored-commit-intent-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
RETAINED=previous_sync.RETAINED|{base.MODEL,base.TEST,base.RECOVERY_TEST,base.DRIVER,
    tested_driver.DRIVER,tested_driver.origin.DRIVER,'tools/p09/stored_revision_jobs_source_contract.py',
    base.sql_contract.UP,base.sql_contract.DOWN,base.sql_contract.OLD}


def tight(text):return ''.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STORED_JOBS_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_REVISION_JOBS_SYNC',own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_PostgreSQL_or_process_restart=False,durable_idempotency_complete=False,P09_product_execution_or_commit=False,
        SQL23_applied=False,SQL23_parse_or_runtime_qualified=False,SQL23_Rust_connector_or_job_registration_connected=False,
        actual_cases_reexecuted=0,full872_inputs_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(tested_driver.OUTPUT))
        c.require(q.snapshots[tested_driver.OUTPUT]['sha256']=='e6144affdc1e37d38e23bc64046981ec4984c0bdb5ead262e42a5a245bb6bb1c'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==872 and passed['total_executed_cases']==29
            and passed['new_cases']==4 and passed['affected_cases']==25 and passed['test_scratch_empty'],'EXACT263_RUST29_WITH872_SOURCE_CLOSURE_SQL_UNQUALIFIED')
        tested={p['path']:p for p in passed['source_pins']}
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_PRECOMMIT_JOB_SQL_SOURCE_AND_GATE_DENIALS_MATCH263')
        names=lambda path:re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path))
        cases=set(names(base.base.PARENT))|{'recovery_v1::'+n for n in names(base.RECOVERY_TEST)}|{'precommit_v1::'+n for n in names(base.TEST)}
        c.require(len(cases)==29,'EXACT29_CURRENT_RUST_CASE_NAMES');tools.good_step(passed['steps'][0],cases)
        job=passed['steps'][0]['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']
            and job['last_job_accounting']['active_processes']==0,'263_JOB_TERMINAL_EMPTY_CLOSED')
        contract=base.sql_contract.check(q,c);c.require(contract==passed['SQL23_static_source_contract']and len(contract['checks'])==13
            and contract['derived_functions']==6 and not contract['SQL_executed'],'EXACT13_STATIC_SQL_CONTRACTS_NOT_SQL_PARSE_OR_RUNTIME')
        prior=compact.unpack(q.json(base.base.OUTPUT));tested_driver.inverse(q,{p['path']:p for p in prior['source_pins']})
        for path,sha,code in[(tested_driver.origin.FAILED,'f20c7a0edb81157d0d2adfc2aa6160d0157d34d7b89d9c8999c74943df1d53bf','ALL_OTHER_PRODUCT_POSTGRES_SQL1_TO22_ROUTING_NATIVE_AND_TEST_INPUTS_UNCHANGED'),
            (tested_driver.FAILED,'6c811b8289635d3726659aeb951ccb48c7fadf7347540b3a15c2830d5a62c390','ONE_READONLY_PRECOMMIT_JSON_GETTER')]:
            failed=compact.unpack(q.json(path));c.require(q.snapshots[path]['sha256']==sha and failed['cleanup']and not failed['steps']
                and failed['error_code']==code,'261_262_PREFLIGHT_FAILURES_RETAINED_NO_PRODUCT_OR_TEST_FAILURE_PROMOTION')
        c.require(q.snapshots[base.sql_contract.OLD]==tested_driver.origin.SQL_BASELINE,'UNCHANGED_READONLY_GIT_HEAD_P14_SQL_BASELINE')
        docs=q.json(base.DOC_BASE);c.require(q.snapshots[base.DOC_BASE]['sha256']=='0b756f8f61961f75ac7640c57db3971e67bd627bd5f759ab640d5dfe9910f54e'
            and docs['cleanup'],'EXACT260_PRIOR_DOC_CLOSURE')
        old={p['path']:p for p in docs['source_pins']}
        for name in(PROFILE,OLD_PROFILE,PROGRESS,'CURRENT_STATE.md',DRIVER):q.pin(name)
        current=q.text('CURRENT_STATE.md');at=current.index('> 2026-10-20 P09 ACTIVE 최신 커밋 의도와 읽기 전용 복구')
        audit.inverse(current[at:],old['CURRENT_STATE.md'],'ALL_PREVIOUS_CURRENT_STATE_AND_FAILURE_HISTORY_UNCHANGED')
        progress=q.text(PROGRESS);start=progress.index('## Precommit receipt와 저장 job 경계\n');end=progress.index('## 커밋 의도와 읽기 전용 복구\n',start)
        audit.inverse(progress[:start]+progress[end:],old[PROGRESS],'ALL19_SEARCH_ROWS_AND_PRIOR_FEATURE_RECORDS_UNCHANGED')
        c.require(len(set(re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M)))==19,'EXACT19_SEARCH_ROWS_NO_PROMOTION')
        profile=q.text(OLD_PROFILE);added='''별도 workspace-precommit.json은 엔진 canonical JSON과 같은 transaction SHA를 갖는다.
이 receipt는 더 큰 intent envelope와 다른 UUID/SHA로 저장하고 복호화 readback한다.
미확인/손상된 precommit은 intent/CAS 전에 거부한다. 새 저장 job SQL과 미완료 연결은
[Precommit와 저장 job 계약](p09-stored-revision-jobs-v1.md)을 따른다. 아래259는 이 별도 저장 전 검증이다.
'''
        c.require(profile.count(added)==1,'ONE_ADDITIVE_PRECOMMIT_ROLE_AND_SCOPE_NOTE');audit.inverse(profile.replace(added,''),old[OLD_PROFILE],'ALL_PRIOR_INTENT_AND_READONLY_RECOVERY_CONTRACT_UNCHANGED')
        for text in(current[:at],progress[start:end],q.text(PROFILE)):
            for marker in('workspace-precommit.json','RevisionCommitRequest::canonical_json','SQL23은 구문/실행 미검증·미적용',
                'Rust schema23 connector/등록 callback도 미연결','Cargo/시험0','Rust 신규4+영향25=29pass','872fresh/final872',
                'SQL 정적 소스 계약13개(6개 역변환 포함)','SQL parsing/runtime 증거가 아니다','125.531','12.469','0.19','10.656',
                '875.66MiB/2.74838%','22.99%','45.7716%','active0/empty/handle closed','CPU cap6.25%','private8%/stop7%',
                'RAM/commit95%','in-memory','합성','routing_allowed=false','158/249','잔여91','next165',
                'P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
                c.require(tight(marker)in tight(text),'ACCURATE_RUST29_SQL_STATIC_ONLY_METRICS_FAILURES_AND_OPEN_GATES')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_PRECOMMIT4_AFFECTED25_PENDING_SQL23_SOURCE_AND_DOC_SYNC_NOT_SQL_RUNTIME_P09_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_cases_retained=4,affected_cases_retained=25,
            static_SQL_contracts_retained=13,derived_v2_functions=6,prior261_262_and_documents_preserved=True,
            next_work='strict_schema23_connector_registration_callback_and_owned_DB_runtime_restart_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'STORED_JOBS_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
