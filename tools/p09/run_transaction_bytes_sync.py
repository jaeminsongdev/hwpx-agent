"""Selected23 byte/file transaction cases and source/defect/doc closure; no Cargo/full844 replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_transaction_bytes_components as base
shared,c,a,audit,tools=base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-transaction-bytes-sync254.v1.json'
DRIVER='tools/p09/run_transaction_bytes_sync.py'
PROFILE='protocol/migrations/p09-transaction-byte-source-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,PROGRESS,'CURRENT_STATE.md',DRIVER}
RETAINED={base.DRIVER,base.base.DRIVER,base.base.base.DRIVER,base.INTEGRITY,base.base.base.MODEL,
    base.base.base.SOURCE,base.base.base.PARENT,base.base.base.TEST,'tools/p09/compact_receipt_json.py',
    'Cargo.toml','Cargo.lock','crates/operation-engine/Cargo.toml','crates/operation-engine/src/lib.rs',
    'crates/operation-engine/src/state.rs','crates/operation-engine/src/manifest.rs','crates/foundation/src/workdir.rs',
    'crates/product-cli/src/form_stored_provider.rs','crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/product-cli/src/form_product_request/stored_operations/compiled_search/p02_registry.rs',
    'crates/product-cli/src/form_product_request/stored_operations/compiled_search/routing.rs'}


def tight(text):return ''.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'BYTE_TRANSACTION_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_BYTE_TRANSACTION_DOC_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        P09_product_execution_or_commit=False,actual_registry_target_or_native_qualified=False,ArtifactService_ingest_or_RevisionService_CAS=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=base.base.base.prior.compact.unpack(q.json(base.OUTPUT))
        c.require(q.snapshots[base.OUTPUT]['sha256']=='77d9c82ec55f7537e85abe637cab3b54ead17d846ee0762500e0e487e77eb79c'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==844 and passed['total_executed_cases']==23
            and passed['test_scratch_empty'],'EXACT253_NEW14_AFFECTED9_AND844_CLOSURE')
        tested={p['path']:p for p in passed['source_pins']}
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_BYTE_FILE_ADAPTER_STREAMING_INTEGRITY_PIPELINE_AND_P09_GUARDS_MATCH253')
        cases=base.expected(q);tools.good_step(passed['steps'][0],cases)
        job=passed['steps'][0]['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']
            and job['last_job_accounting']['active_processes']==0,'SUCCESS253_JOB_TERMINAL_EMPTY_CLOSED')
        probe=base.base.base.prior.compact.unpack(q.json(base.base.OUTPUT))
        c.require(q.snapshots[base.base.OUTPUT]['sha256']=='45315df255c1338aa631d3ecb7a1f2afa741dce71800b1e9e3121cdb9ad640d9'
            and probe['cleanup']and probe['state']=='REPRODUCED_STAGED_OUTPUT_TAMPER_TEST_FAILURE_NOT_ACCEPTANCE_OR_GATE'
            and probe['total_accepted_cases']==0 and probe['steps'][0]['tests']==[[base.base.base.CASE,'FAILED']],'EXACT252_NEGATIVE_FAILURE_PRESERVED_NOT_ACCEPTANCE')
        base.inverse(q,{p['path']:p for p in probe['source_pins']})
        failed=base.base.base.prior.compact.unpack(q.json(base.base.base.OUTPUT))
        c.require(q.snapshots[base.base.base.OUTPUT]['sha256']=='9af1a2d0e63848a56746a2cc022e93bf8e5fb2cb715e1a0309b96d3e5711edf8'
            and failed['cleanup']and failed['error_type']=='KeyError'and not failed['steps'],'EXACT251_INPUT_SCOPE_FAILURE_NO_TESTS_RETAINED')
        baseline=probe['original_test_baseline'];c.require(baseline==base.base.TEST_BASELINE,'EXACT_READONLY_OLD_TEST_BLOB_BASELINE')
        parent=q.text(base.base.base.PARENT);child=base.base.base.CHILD;c.require(parent.endswith(child)and parent.count(child)==1,'ONE_ORIGINAL9_TEST_CHILD_ONLY')
        audit.inverse(parent[:-len(child)],baseline,'ORIGINAL9_FILE_TRANSACTION_TEST_BODIES_REMAIN_IDENTICAL_TO_READONLY_BASELINE')
        scratch=c.ROOT/base.SCRATCH;c.require(scratch.is_dir()and not scratch.is_symlink()and not scratch.is_junction()and not any(scratch.iterdir()),'OWNED_TEST_TEMP_PARENT_STILL_EMPTY')
        docs=q.json(base.base.base.DOC_BASE);c.require(q.snapshots[base.base.base.DOC_BASE]['sha256']=='9383b9a082ba6eb65e7400e56f9d1228e8ea2611f890348e6c2326c4574ee5cb'and docs['cleanup'],'EXACT250_PREVIOUS_DOC_CLOSURE')
        old={p['path']:p for p in docs['source_pins']}
        for name in sorted(DOCS):q.pin(name)
        current=q.text('CURRENT_STATE.md');at=current.index('> 2026-10-20 P09 ACTIVE 최신 다중 그룹 정렬의 공통 계획 연결')
        audit.inverse(current[at:],old['CURRENT_STATE.md'],'ENTIRE_PREVIOUS_CURRENT_STATE_AND_FAILURE_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## bytes 원본 트랜잭션과 게시 무결성\n');end=progress.index('## 다중 그룹 정렬의 공통 계획 연결\n',start)
        audit.inverse(progress[:start]+progress[end:],old[PROGRESS],'ALL19_SEARCH_ROWS_AND_PREVIOUS_FEATURE_PROOFS_UNCHANGED')
        c.require(len(set(re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M)))==19,'EXACT19_SEARCH_ROWS_NO_FEATURE_PROMOTION')
        for text in(current[:at],progress[start:end],q.text(PROFILE)):
            for marker in('WorkspaceTransaction::execute_bytes','Cow::Borrowed','KeyError','Cargo/시험0','실패1개','수용0',
                'Incomplete/CommittedOutcomeUncertain','추가 재검사만64KiB','신규14+영향 파일9=23pass','844fresh/final844',
                '111.766','3.344','0.23','2.062','440.98MiB/1.38409%','19.07%','56.9722%',
                'active0/empty/handle closed','CPU cap6.25%','private8%/stop7%','RAM/commit95%',
                'target/p09-transaction-byte-scratch-253','ArtifactService','RevisionService','합성',
                '158/249','잔여91','next165','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
                c.require(tight(marker)in tight(text),'ACCURATE_BYTE_PRIMITIVE_SECURITY_DEFECT23_CASES_AND_REMAINING_PRODUCT_BOUNDARIES')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_BYTE_TRANSACTION14_AFFECTED_FILE9_AND_DEFECT_DOC_SYNC_NOT_P09_EXECUTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_cases_retained=14,affected_file_cases_retained=9,
            actual_cases_reexecuted=0,full844_inputs_replayed=False,original251_252_failures_and_previous_docs_preserved=True,
            next_work='provider_owned_verified_source_and_result_ingest_then_RevisionService_CAS_and_durable_idempotency_behind_real_execution_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'BYTE_TRANSACTION_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
