"""Selected source/test/doc closure for real storage primitive, no Cargo/full852 replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_stored_revision_commit_recovery as base
shared,c,a,audit,tools,compact=base.shared,base.c,base.a,base.audit,base.tools,base.compact
OUTPUT='implementation/p09/evidence/p09-361-stored-revision-commit-sync257.v1.json'
DRIVER='tools/p09/run_stored_revision_commit_sync.py'
PROFILE='protocol/migrations/p09-stored-revision-cas-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
RETAINED={base.DRIVER,base.base.DRIVER,base.base.MODEL,base.base.PARENT,base.base.LIB,base.base.ADAPTER,base.base.ENGINE_TEST,
    base.base.SERVICE_TEST,base.base.FIXTURE,'crates/product-cli/tests/support/stored_source_fixture.rs',
    'crates/operation-engine/src/transaction/source.rs','crates/operation-engine/src/transaction/integrity.rs',
    'crates/operation-engine/tests/support/bytes_transaction.rs','crates/operation-engine/src/lib.rs',
    'crates/operation-engine/src/state.rs','crates/operation-engine/src/manifest.rs','crates/foundation/src/workdir.rs',
    'crates/artifact-service/src/service.rs','crates/artifact-service/src/types.rs','crates/artifact-service/src/store.rs',
    'crates/artifact-service/src/crypto.rs','crates/revision-service/src/service.rs','crates/revision-service/src/types.rs',
    'crates/revision-service/src/store.rs','crates/product-cli/src/form_stored_provider.rs',
    'crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/product-cli/src/form_product_request/stored_operations/compiled_search/p02_registry.rs',
    'crates/product-cli/src/form_product_request/stored_operations/compiled_search/routing.rs',
    'Cargo.toml','Cargo.lock','crates/product-cli/Cargo.toml','crates/operation-engine/Cargo.toml','tools/p09/compact_receipt_json.py'}


def tight(text):return ''.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STORED_CAS_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_REVISION_COMMIT_SYNC',own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        P09_product_execution_or_commit=False,actual_registry_target_or_native_qualified=False,durable_database_or_idempotency_qualified=False,
        actual_cases_reexecuted=0,full852_inputs_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(base.OUTPUT))
        c.require(q.snapshots[base.OUTPUT]['sha256']=='288d3306b6ec71d3040528d7a619a901a4e33c276671b4a0d09c3264d16bcd56'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==852
            and passed['total_executed_cases']==13 and passed['prior_engine_cases_reused']==26
            and passed['evidence_union_cases']==39 and passed['test_scratch_empty'],'EXACT256_SERVICE13_AND_REUSED26_WITH852_SOURCE_CLOSURE')
        tested={p['path']:p for p in passed['source_pins']}
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_SERVICE_ENGINE_SOURCE_AND_P09_DENIALS_MATCH_TESTED_GENERATION')
        service=set(base.base.names(q,base.base.SERVICE_TEST));tools.good_step(passed['steps'][0],service)
        failed=compact.unpack(q.json(base.base.OUTPUT))
        c.require(q.snapshots[base.base.OUTPUT]['sha256']=='22119ff209e6e8a151a81a67b524a82fbaa99aebc9ef0289c418b68392844ecf'
            and failed['cleanup']and len(failed['steps'])==2,'EXACT255_ENGINE26_AND_NEW_TEST_COMPILE_FAILURE_RETAINED')
        engine=set(base.base.names(q,base.base.PARENT))|{'bytes_v1::'+n for n in base.base.names(q,'crates/operation-engine/tests/support/bytes_transaction.rs')}|{'unknown_cas::'+n for n in base.base.names(q,base.base.ENGINE_TEST)}
        c.require(len(engine)==26 and len(service)==13,'EXACT_UNION39');tools.good_step(failed['steps'][0],engine)
        for step in [failed['steps'][0],failed['steps'][1],passed['steps'][0]]:
            job=step['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']and
                job['last_job_accounting']['active_processes']==0,'ALL255_256_JOBS_TERMINAL_EMPTY_CLOSED')
        base.inverse(q,{p['path']:p for p in failed['source_pins']})
        docs=q.json(base.base.DOC_BASE);c.require(q.snapshots[base.base.DOC_BASE]['sha256']=='fe7099ccd1a7b5844a0f69b6e0699a965fceae56f698581a43433e0faa45a26e'
            and docs['cleanup'],'EXACT254_PRIOR_DOC_BASE')
        old={p['path']:p for p in docs['source_pins']}
        for name in(PROFILE,PROGRESS,'CURRENT_STATE.md',DRIVER):q.pin(name)
        current=q.text('CURRENT_STATE.md');at=current.index('> 2026-10-20 P09 ACTIVE 최신 bytes 원본 트랜잭션과 게시 무결성')
        audit.inverse(current[at:],old['CURRENT_STATE.md'],'PREVIOUS_CURRENT_STATE_AND_FAILURE_HISTORY_UNCHANGED')
        progress=q.text(PROGRESS);start=progress.index('## 저장 서비스와 revision CAS 연결\n');end=progress.index('## bytes 원본 트랜잭션과 게시 무결성\n',start)
        audit.inverse(progress[:start]+progress[end:],old[PROGRESS],'ALL19_SEARCH_ROWS_AND_PRIOR_FEATURE_RECORDS_UNCHANGED')
        c.require(len(set(re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M)))==19,'EXACT19_SEARCH_ROWS_NO_PROMOTION')
        for text in(current[:at],progress[start:end],q.text(PROFILE)):
            for marker in('StoredResultRevisionCas','ArtifactService','RevisionService','RevisionCasOutcome::Unknown',
                'CommitOutcomeUnknown','Incomplete/CommittedOutcomeUncertain','dedup','SHA','메모리','영속','E0308',
                '신규3+기존23=26pass','서비스13pass','852fresh/final852','합집합39개','신규16개',
                '112.828','3.422','0.08','3.0','727.44MiB/2.28318%','15.79%','46.9934%',
                'active0/empty/handle closed','CPU cap6.25%','private8%/stop7%','RAM/commit95%',
                'in-memory','합성','routing_allowed=false','158/249','잔여91','next165','P09/A12/A13 OPEN',
                'CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
                c.require(tight(marker)in tight(text),'ACCURATE_SERVICE39_SCOPE_FAILURE_RECOVERY_METRICS_AND_OPEN_GATES')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_STORAGE_SERVICE13_REUSED_ENGINE26_AND_DOC_SYNC_NOT_P09_EXECUTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,service_cases_retained=13,engine_cases_retained=26,
            prior255_failure_and_previous_docs_preserved=True,next_work='durable_reconciliation_and_idempotency_then_qualified_P09_execution_integration')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'STORED_REVISION_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
