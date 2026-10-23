"""Selected genuine P02 signature consumer/docs closure, not new P09 registry authority; no test replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_pinned_p02_registry_components as base
shared,c,a,audit,tools=base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-pinned-p02-registry-sync226.v1.json'
DRIVER='tools/p09/run_pinned_p02_registry_sync.py'
PROFILE='protocol/migrations/p09-pinned-p02-registry-evidence-v1.md'
MANIFEST='protocol/migrations/p09-source-search-execution-manifest-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,MANIFEST,PROGRESS,'CURRENT_STATE.md'}
RETAINED=base.NEW|base.CHANGED|set(base.MATERIALS)|base.EXPLANATION|{'crates/product-cli/src/form_product_request.rs',
    'crates/product-cli/src/form_product_request/stored_operations/request.rs','crates/product-cli/Cargo.toml','Cargo.toml','Cargo.lock'}


def norm(text):return ' '.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'PINNED_REGISTRY_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PINNED_P02_REGISTRY_DOC_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        private_key_read=False,registry_or_runtime_support_promoted=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(base.OUTPUT);docs=q.json(base.DOC_BASE)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='a4bff4e76e3beba1bc050d3a5d71c8f9e8297bc38f226fa083d6062faf3460bb'
            and passed['state']=='PASS_ACTUAL_PINNED_P02_CRYPTO12_SEARCH_POLICY6_NOT_CURRENT_NATIVE_ROUTE_TRANSACTION_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==780 and passed['total_executed_cases']==18,
            'EXACT225_ACTUAL_CRYPTO12_POLICY6_AND780_CLOSURE')
        c.require(q.snapshots[base.DOC_BASE]['sha256']=='59bccb0cfdc08137ed9e73f030af798adea04a7a9f87b74c0033c439401e929b'
            and docs['cleanup'],'EXACT224_PREVIOUS_SOURCE_PROTECTION_DOC_HISTORY')
        tested={p['path']:p for p in passed['source_pins']};c.require(RETAINED<=tested.keys(),'ALL_SELECTED_CRYPTO_MATERIALS_CODE_AND_TESTS_DECLARED_BY225')
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'LIVE_SELECTED_TRUST_EVIDENCE_CONSUMER_PARSED_SOURCE_AND_TEST_INPUTS_MATCH225')
        units,products=base.expected(q);tools.good_step(passed['steps'][0],units);tools.good_step(passed['steps'][1],products)
        for step in passed['steps']:
            job=step['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0,
                'BOTH225_OWNED_JOBS_TERMINAL_EMPTY_CLOSED')
        base.inverse(q,{p['path']:p for p in q.json(base.prior.OUTPUT)['source_pins']})
        for name in sorted(DOCS|{DRIVER}):q.pin(name)
        old={p['path']:p for p in docs['source_pins']}
        current=q.text('CURRENT_STATE.md');at=current.index('> 2026-10-20 P09 ACTIVE 최신 원본 전체 보호 신호와 manifest 결속')
        audit.inverse(current[at:],old['CURRENT_STATE.md'],'ENTIRE_PREVIOUS_PROTECTION_MANIFEST_COMPILER_AND_CURRENT_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 보존된 P02 registry의 실제 서명 검증\n');end=progress.index('## 원본 전체 보호 신호와 manifest 결속\n',start)
        audit.inverse(progress[:start]+progress[end:],old[PROGRESS],'ALL19_SEARCH_ROWS_PRIOR_COMPONENTS_AND_FAILURE_HISTORY_PRESERVED')
        text=q.text(MANIFEST);heading='\n## 보존된 P02 registry의 실제 서명 검증\n';c.require(text.count(heading)==1,'ONE_ORIGINAL_MANIFEST_CONTRACT_EXTENSION')
        audit.inverse(text[:text.index(heading)],old[MANIFEST],'ENTIRE_PREVIOUS_MANIFEST_PROTECTION_AND_NONAUTHORITATIVE_ROUTE_CONTRACT_PRESERVED')
        ids=re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M);c.require(len(ids)==len(set(ids))==19,'EXACT19_P09_SEARCH_ROWS_NO_P11_SCOPE_ADDED')
        for text in(current[:at],progress[start:end],q.text(PROFILE)):
            for marker in('p09-pinned-p02-registry-evidence/v1','PinnedP02RegistryEvidence','Ed25519','536','routing_allowed=false',
                'prepare_compiled_search_json_with_pinned_registry','원본 읽기/후보 준비 전에','225','18pass','780fresh/final780','개인 서명키','RouteUnqualified'):
                c.require(norm(marker)in norm(text),'DOCUMENTED_ACTUAL_PINNED_EVIDENCE18_NOT_CURRENT_NATIVE_OR_NEW_REGISTRY_AUTHORITY')
        profile=norm(q.text(PROFILE))
        for marker in('SignedSupportClaim','signature_verified','runtime_probe_reexecuted','current_installed_target_observed','64MiB','32MiB','64KiB',
            '963624','verified2/failed1/blocked17/not_run12','routing_enabled/execution_authority','158/249','잔여91','next165','P09/A12/A13 OPEN',
            'CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(norm(marker)in profile,'EXACT_HISTORICAL_SCOPE_LIMITS_AND_REMAINING_PRODUCT_NATIVE_GATE_BOUNDARIES')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_PINNED_P02_CRYPTO18_DOC_SYNC_NOT_CURRENT_NATIVE_ROUTE_TRANSACTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_crypto_cases_retained=12,new_product_cases_retained=6,
            actual_cases_reexecuted=0,full780_inputs_replayed=False,p02_materials_and_all_previous_doc_history_preserved=True,
            next_work='actual_qualified_P09_target_registry_and_native_protection_not_P02_promotion_then_durable_ingest_commit_CAS_idempotency_and_remaining_P09_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'PINNED_REGISTRY_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
