"""Selected intent/source/doc closure; no Cargo/old engine/official tests or full860 replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_stored_commit_intent_components as base
shared,c,a,audit,tools,compact=base.shared,base.c,base.a,base.audit,base.tools,base.compact
OUTPUT='implementation/p09/evidence/p09-361-stored-commit-intent-sync260.v1.json'
DRIVER='tools/p09/run_stored_commit_intent_sync.py'
PROFILE='protocol/migrations/p09-stored-commit-intent-v1.md'
OLD_PROFILE='protocol/migrations/p09-stored-revision-cas-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
RETAINED={base.DRIVER,base.ADAPTER,base.PARENT,base.REV_LIB,base.RECON,base.INTENT,base.TEST,
    'crates/product-cli/tests/support/stored_commit_manifest.rs','crates/product-cli/tests/support/stored_source_fixture.rs',
    'crates/revision-service/src/service.rs','crates/revision-service/src/store.rs','crates/revision-service/src/types.rs',
    'crates/revision-service/src/postgres.rs','crates/artifact-service/src/service.rs','crates/artifact-service/src/types.rs',
    'crates/artifact-service/src/store.rs','crates/artifact-service/src/crypto.rs','crates/artifact-service/src/store/postgres_repository.rs',
    'crates/operation-engine/src/transaction.rs','crates/operation-engine/src/transaction/source.rs',
    'crates/operation-engine/src/transaction/integrity.rs','crates/operation-engine/tests/workspace_transaction.rs',
    'crates/operation-engine/tests/support/bytes_transaction.rs','crates/operation-engine/tests/support/unknown_cas_transaction.rs',
    'crates/product-cli/src/lib.rs','crates/product-cli/src/form_stored_provider.rs','crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/product-cli/src/form_product_request/stored_operations/compiled_search/p02_registry.rs',
    'crates/product-cli/src/form_product_request/stored_operations/compiled_search/routing.rs',
    'Cargo.toml','Cargo.lock','crates/product-cli/Cargo.toml','crates/revision-service/Cargo.toml','tools/p09/compact_receipt_json.py'}


def tight(text):return ''.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'INTENT_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_COMMIT_INTENT_SYNC',own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_PostgreSQL_or_process_restart=False,durable_idempotency_complete=False,P09_product_execution_or_commit=False,
        actual_cases_reexecuted=0,full860_inputs_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(base.OUTPUT))
        c.require(q.snapshots[base.OUTPUT]['sha256']=='b36cc802d704a9c8b58fd035a2d97646970b856c57a5b1e1edb21de6516b13fc'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==860
            and passed['total_executed_cases']==25 and passed['new_cases']==12 and passed['affected_cases']==13
            and passed['test_scratch_empty'],'EXACT259_INTENT12_AFFECTED13_WITH860_SOURCE_CLOSURE')
        tested={p['path']:p for p in passed['source_pins']}
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_INTENT_RECONCILIATION_SERVICES_POSTGRES_AND_GATE_DENIALS_MATCH259')
        names=lambda path:re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path))
        cases=set(names(base.PARENT))|{'recovery_v1::'+name for name in names(base.TEST)}
        c.require(len(cases)==25,'EXACT25_CURRENT_TEST_NAMES');tools.good_step(passed['steps'][0],cases)
        job=passed['steps'][0]['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']
            and job['last_job_accounting']['active_processes']==0,'259_JOB_TERMINAL_EMPTY_CLOSED')
        prior=compact.unpack(q.json(base.base.OUTPUT));base.inverse(q,{p['path']:p for p in prior['source_pins']})
        docs=q.json(base.DOC_BASE);c.require(q.snapshots[base.DOC_BASE]['sha256']=='f782542be153960bb40253165c0ebce577bce5cabe9a323a76dfa3d9129a8130'
            and docs['cleanup'],'EXACT258_PRIOR_DOC_CLOSURE')
        old={p['path']:p for p in docs['source_pins']}
        for name in(PROFILE,OLD_PROFILE,PROGRESS,'CURRENT_STATE.md',DRIVER):q.pin(name)
        current=q.text('CURRENT_STATE.md');at=current.index('> 2026-10-20 P09 ACTIVE 최신 저장 서비스와 revision CAS 연결')
        audit.inverse(current[at:],old['CURRENT_STATE.md'],'ALL_PRIOR_CURRENT_STATE_AND_FAILURE_HISTORY_UNCHANGED')
        progress=q.text(PROGRESS);start=progress.index('## 커밋 의도와 읽기 전용 복구\n');end=progress.index('## 저장 서비스와 revision CAS 연결\n',start)
        audit.inverse(progress[:start]+progress[end:],old[PROGRESS],'ALL19_SEARCH_ROWS_AND_PREVIOUS_FEATURE_RECORDS_UNCHANGED')
        c.require(len(set(re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M)))==19,'EXACT19_SEARCH_ROWS_NO_PROMOTION')
        profile=q.text(OLD_PROFILE)
        after='''후속 의도 저장 경로는 CAS 전에 불변 Receipt를 수입하고 원 요청의 읽기 전용 커밋 판별을 제공한다.
영속 job의 intent ID/SHA 등록과 기존 v2 멱등 권한 연결은 미완료이며 파일/저장소/DB 분산 원자성은 없다.
[커밋 의도와 복구 계약](p09-stored-commit-intent-v1.md)을 따른다. 아래255/256은 의도 저장 전 검증 이력이다.
'''
        before='현재 복구 정보는 메모리뿐이고 영속 멱등이나 파일/저장소/DB 분산 원자성이 아니다.\n'
        c.require(profile.count(after)==1,'ONE_SUPERSEDED_MEMORY_ONLY_SCOPE_UPDATED')
        audit.inverse(profile.replace(after,before),old[OLD_PROFILE],'ALL_ORIGINAL_STORAGE_CONTRACT_AND_FAILURE_EVIDENCE_PRESERVED')
        for text in(current[:at],progress[start:end],q.text(PROFILE)):
            for marker in('StoredResultRevisionCas','ArtifactService','hwpx-agent.stored-revision-commit-intent/v1',
                'RevisionService::observe_commit','reconcile_stored_commit','NotObserved','Committed/Unavailable','64KiB',
                '영속 job의 intent ID/SHA 등록','기존 v2 멱등 권한 연결은 미완료','실제 DB/프로세스 재시작 검증도 NOT_RUN',
                '신규12+영향 기존13=25pass','860fresh/final860','123.375','12.641','0.16','10.812',
                '875.72MiB/2.74857%','64.31%','46.8754%','active0/empty/handle closed',
                'CPU cap6.25%','private8%/stop7%','RAM/commit95%','in-memory','합성','routing_allowed=false',
                '158/249','잔여91','next165','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
                c.require(tight(marker)in tight(text),'ACCURATE_INTENT25_READONLY_SCOPE_REMAINING_DURABLE_JOIN_AND_METRICS')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_IMMUTABLE_INTENT12_AFFECTED13_AND_DOC_SYNC_NOT_DB_RESTART_P09_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_cases_retained=12,affected_cases_retained=13,
            previous_docs_and_failure_records_preserved=True,next_work='durable_job_intent_handle_join_existing_v2_authority_and_owned_DB_restart_evidence')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'INTENT_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
