"""Selected whole-source protection/manifest and docs closure; retain42, no Rust/Cargo or764-input replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_source_protection_manifest_components as base
shared,c,a,audit,tools=base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-source-protection-manifest-sync224.v1.json'
DRIVER='tools/p09/run_source_protection_manifest_sync.py'
PASSED='implementation/p09/evidence/p09-361-source-protection-manifest-recovery223.v1.json'
PROFILE='protocol/migrations/p09-source-protection-signals-v1.md'
MANIFEST='protocol/migrations/p09-source-search-execution-manifest-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,MANIFEST,PROGRESS,'CURRENT_STATE.md'}
RETAINED=base.NEW|base.CHANGED|{'tools/p09/run_source_protection_manifest_recovery.py',
    'crates/hwpx-package/src/document_import/structure/caption_text_batch.rs','crates/hwpx-package/src/text_flow.rs',
    'crates/hwpx-package/tests/support/search_definition_fixture.rs','crates/hwpx-package/tests/support/document_import_field_fixture.rs',
    'crates/hwpx-package/tests/support/document_import_catalog_fixture.rs','crates/domain-ir/src/capability_router.rs','crates/operation-engine/src/manifest.rs'}


def norm(text):return ' '.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SOURCE_PROTECTION_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SOURCE_PROTECTION_DOC_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        native_protection_or_crypto_signature_attested=False,trusted_registry_or_native_evidence=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(PASSED);failed=q.json(base.OUTPUT);docbase=q.json(base.DOC_BASE)
        c.require(q.snapshots[PASSED]['sha256']=='a8ab120602e26510ce6e106761a89f79b4d1a12dd855b741886339c32eb42264'
            and passed['state']=='PASS_WHOLE_SOURCE_PROTECTION10_PRODUCT8_AFFECTED_MANIFEST26_RETAINED42_NOT_NATIVE_PROTECTION_CRYPTO_TRUST_TRANSACTION_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==764 and passed['total_executed_cases']==2
            and not passed['passed42_cases_reexecuted'],'EXACT223_RECOVERED_TWO_CURRENT764_CLOSURE_AND42_NOT_REPLAYED')
        c.require(q.snapshots[base.OUTPUT]['sha256']=='01f0cc12f4412febddfbd15c74fb2071bbe467d8aedc073086716154b74be024'
            and failed['cleanup']and failed['state']=='FAILED_SOURCE_PROTECTION_MANIFEST_COMPONENTS'
            and failed['steps'][0]['exit_code']==0 and failed['steps'][1]['exit_code']==101,'ORIGINAL222_SOURCE10_PRODUCT33_PASS_ONE_BODY_IMPORT_FAILURE_PRESERVED')
        c.require(q.snapshots[base.DOC_BASE]['sha256']=='d5e30db6d32b0b9b7aedf53a324e54df73312c1d49bdfae2be691551d62e32c7'
            and docbase['cleanup'],'EXACT221_PREVIOUS_DOC_HISTORY')
        tested={p['path']:p for p in passed['source_pins']};c.require(RETAINED<=tested.keys(),'SELECTED_WHOLE_SOURCE_MANIFEST_PARSER_TESTS_DECLARED_BY223')
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'LIVE_SELECTED_PROTECTION_AND_PRODUCT_INPUTS_MATCH223')
        core,products,affected=base.expected(q);prior_core={n for n,s in failed['steps'][0]['tests']if s=='ok'}
        repaired_negative=base.prior.PREFIX+'protection_v1::protection_selected_local_lock_keeps_original_candidate_rejection'
        retained={n for n,s in failed['steps'][1]['tests']if s=='ok'and n!=repaired_negative};recovered={n for n,s in passed['steps'][0]['tests']if s=='ok'}
        c.require(prior_core==core and len(retained)==32 and len(recovered)==2 and retained.isdisjoint(recovered)
            and retained|recovered==products|affected,'EXACT10_PLUS8_PLUS26_DISTINCT44_NOT_CURRENT44_SINGLE_RUN')
        tools.good_step(failed['steps'][0],core);tools.good_step(passed['steps'][0],recovered)
        for step in failed['steps']+passed['steps']:
            job=step['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0,
                'ORIGINAL222_AND223_ALL_OWNED_JOBS_TERMINAL_EMPTY_CLOSED')
        base.inverse(q,{p['path']:p for p in q.json(base.BASELINE)['source_pins']})
        for name in sorted(DOCS|{DRIVER}):q.pin(name)
        previous={p['path']:p for p in docbase['source_pins']}
        current=q.text('CURRENT_STATE.md');at=current.index('> 2026-10-20 P09 ACTIVE 최신 실제 원본 실행 manifest 연결')
        audit.inverse(current[at:],previous['CURRENT_STATE.md'],'ENTIRE_PREVIOUS_MANIFEST_COMPILER_AND_CURRENT_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 원본 전체 보호 신호와 manifest 결속\n');end=progress.index('## 실제 원본 계획의 실행 manifest 연결\n',start)
        audit.inverse(progress[:start]+progress[end:],previous[PROGRESS],'ALL19_SEARCH_ROWS_COMPONENT_EVIDENCE_AND_FAILURE_HISTORY_PRESERVED')
        text=q.text(MANIFEST);heading='\n## 실제 원본 보호 신호 결속\n';c.require(text.count(heading)==1,'ONE_ORIGINAL_MANIFEST_CONTRACT_EXTENSION')
        audit.inverse(text[:text.index(heading)],previous[MANIFEST],'ENTIRE_PREVIOUS_MANIFEST_AND_REGISTRY_NATIVE_LIMITATIONS_PRESERVED')
        ids=re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M);c.require(len(ids)==len(set(ids))==19,'EXACT19_P09_SEARCH_ROWS_NO_P11_SCOPE_ADDED')
        for text in(current[:at],progress[start:end],q.text(PROFILE)):
            for marker in('source-protection-signals/partial-v1','SourceProtectionObservation','Unprotected','native_protection_verified',
                'cryptographic_signature_verified','execution_authority','222','223','764fresh/final764','고유44개','단일 실행이 아니다',
                '통과42개','최종 head','신호 부재는 보호 없음'):
                c.require(norm(marker)in norm(text),'DOCUMENTED_WHOLE_SOURCE_OBSERVATION44_NOT_NATIVE_UNPROTECTION_OR_EXECUTION')
        profile=norm(q.text(PROFILE))
        for marker in('document_signal_parts','local_blocked_elements','protection_element_visits','1000','2pass','추가1pass','Compile::Protection',
            'RouteUnqualified','routing_allowed=false','158/249','잔여91','next165','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(norm(marker)in profile,'EXACT_ORIGINAL_GUARDS_COUNTS_AND_REMAINING_PRODUCT_NATIVE_GATE_BOUNDARIES')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_WHOLE_SOURCE_PROTECTION44_DOC_SYNC_NOT_NATIVE_PROTECTION_CRYPTO_TRUST_TRANSACTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_source_cases_retained=10,new_product_cases_retained=8,
            affected_manifest_cases_retained=26,actual_cases_reexecuted=0,full764_inputs_replayed=False,
            original222_failure_and_previous_doc_history_preserved=True,
            next_work='qualified_native_protection_and_trusted_current_registry_target_then_durable_ingest_commit_CAS_idempotency_and_remaining_P09_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SOURCE_PROTECTION_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
