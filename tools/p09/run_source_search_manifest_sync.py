"""Selected original-router/source-manifest and docs closure, no Cargo or756-input replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_source_search_manifest_components as base
shared,c,a,audit,tools=base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-source-search-manifest-sync220.v1.json'
DRIVER='tools/p09/run_source_search_manifest_sync.py'
PASSED='implementation/p09/evidence/p09-361-source-search-manifest-preflight-recovery219.v1.json'
FAILED=base.OUTPUT
PROFILE='protocol/migrations/p09-source-search-execution-manifest-v1.md'
COMPILER='protocol/migrations/p09-source-search-operation-compiler-v1.md'
COMMON='protocol/migrations/p09-common-search-mutation-dispatch.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,COMPILER,COMMON,PROGRESS,'CURRENT_STATE.md'}
RETAINED=base.NEW|base.CHANGED|base.base.NEW|base.base.CHANGED|{
    'tools/p09/run_source_search_manifest_preflight_recovery.py','crates/operation-engine/src/manifest.rs'}


def norm(text):return ' '.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SOURCE_MANIFEST_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SOURCE_MANIFEST_DOC_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        trusted_registry_or_native_evidence=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(PASSED);failed=q.json(FAILED);previous_docs=q.json(base.SYNC)
        c.require(q.snapshots[PASSED]['sha256']=='ba76f88e3bfc69d4775eca4aed7283bb818ff11e47686054cf8b5eaf9f2fa34a'
            and passed['state']=='PASS_SIXTEEN_FAMILY_SOURCE_ROUTER_EXECUTION_MANIFEST26_NOT_TRUSTED_REGISTRY_NATIVE_TRANSACTION_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==756 and passed['total_executed_cases']==26,
            'EXACT219_CURRENT26_AND756_CLOSURE')
        c.require(q.snapshots[FAILED]['sha256']=='65ee27be1f73fb73c4605bdd46baf9271c6e764875c7214ca4f23e56321054e1'
            and failed['cleanup']and failed['steps']==[]and failed['error_code']=='NO_FABRICATED_SUPPORT_TRUST_REIMPORT_NATIVE_OR_COMMIT',
            'ORIGINAL218_STATIC_COMMENT_FAILURE_BEFORE_CARGO_TEST0_PRESERVED')
        c.require(q.snapshots[base.SYNC]['sha256']=='926184ba203ca22646e267973766784b33e113aac048ec1cd44f618e44a949ed'
            and previous_docs['cleanup'],'EXACT217_PREVIOUS_COMPILER_DOC_HISTORY')
        tested={p['path']:p for p in passed['source_pins']};c.require(RETAINED<=tested.keys(),'ALL_SELECTED_CURRENT_MANIFEST_COMPILER_SOURCE_INPUTS_DECLARED_BY219')
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'LIVE_SELECTED_SOURCE_ROUTER_MANIFEST_COMPILER_PRODUCTS_AND_TESTS_MATCH219')
        cases=base.expected(q);tools.good_step(passed['steps'][0],cases)
        job=passed['steps'][0]['owned_job']
        c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0,
            'EXACT219_TERMINAL_EMPTY_OWNED_JOB_CLOSED')
        original=q.json(base.prior.OUTPUT);base.inverse(q,{p['path']:p for p in original['source_pins']})
        for name in sorted(DOCS|{DRIVER}):q.pin(name)
        old={p['path']:p for p in previous_docs['source_pins']}
        current=q.text('CURRENT_STATE.md');at=current.index('> 2026-10-20 P09 ACTIVE 최신 원본 결속 검색 operation compiler')
        audit.inverse(current[at:],old['CURRENT_STATE.md'],'ENTIRE_PREVIOUS_COMPILER_SPLICE_AND_OLD_CURRENT_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 실제 원본 계획의 실행 manifest 연결\n');end=progress.index('## 실제 원본에 결속한 공통 operation compiler\n',start)
        audit.inverse(progress[:start]+progress[end:],old[PROGRESS],'ALL19_SEARCH_ROWS_PRIOR_COMPONENTS_AND_FAILURE_HISTORY_PRESERVED')
        for name,heading in((COMMON,'\n## 원본 계획의 실행 manifest 연결\n'),(COMPILER,'\n## 실제 원본 manifest 소비자\n')):
            text=q.text(name);c.require(text.count(heading)==1,'ONE_ADDITIVE_ACTUAL_MANIFEST_CONSUMER_SECTION')
            audit.inverse(text[:text.index(heading)],old[name],'ENTIRE_PREVIOUS_CONTRACT_AND_SOURCE_QUALIFICATION_HISTORY_PRESERVED')
        ids=re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M);c.require(len(ids)==len(set(ids))==19,'EXACT19_P09_SEARCH_ROWS_P11_EXCLUDED')
        for text in(current[:at],progress[start:end],q.text(PROFILE)):
            for marker in('prepare_execution_manifest','CapabilityRouter','ExecutionManifest::from_receipts','route_plan','128','20','218','219',
                '26pass','756fresh/final756','checked_mul(1000)','RouteUnqualified','최종 head','합성 fixture'):
                c.require(norm(marker)in norm(text),'DOCUMENTED_ACTUAL26_AND_PER_CALL_ROUTING_NOT_TRUSTED_EXECUTION')
        profile=norm(q.text(PROFILE))
        for marker in('SignatureVerified','SupportState::Verified','routing_allowed=false','source protection','ingest/commit/CAS',
            '158/249','잔여91','next165','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(norm(marker)in profile,'EXACT_TRUST_AND_PRODUCT_NATIVE_GATE_BOUNDARIES')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_SOURCE_ROUTER_MANIFEST26_DOC_SYNC_NOT_TRUSTED_REGISTRY_NATIVE_TRANSACTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_manifest_cases_retained=26,actual_cases_reexecuted=0,
            full756_inputs_replayed=False,original218_failure_and_previous_doc_history_preserved=True,
            next_work='trusted_current_registry_target_and_source_protection_binding_then_durable_ingest_commit_CAS_idempotency_and_remaining_P09_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SOURCE_MANIFEST_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
