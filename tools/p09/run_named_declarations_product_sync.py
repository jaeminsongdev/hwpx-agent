"""360: preserve357/358 failures and359 current29, source/document-only audit without test replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_named_declarations_product_isolated as latest
base=latest.base
shared,c,a,tools,compact,harness,audit=base.shared,base.c,base.a,base.tools,base.compact,base.harness,base.audit
OUTPUT='implementation/p09/evidence/p09-361-named-declarations-product-sync360.v1.json';DRIVER='tools/p09/run_named_declarations_product_sync.py'
STATE='CURRENT_STATE.md';PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md';REPORT='implementation/p09/P09_NAMED_STYLE_REPLACEMENT_PROGRESS.md'
PROFILE='protocol/migrations/p09-named-style-declarations-product-v1.md'
OLD_ROW='| SEARCH-025 | 스타일 일괄 대체 | 문단 이름/필터 v2 제품·공통22계열 및 PARA/CHAR 원본 선언 고유19+기존 catalog3 검증, 문자 스타일 본문 결속/전체 옵션·실제 적용/실행/저장/target 미완료 |'
NEW_ROW='| SEARCH-025 | 스타일 일괄 대체 | 문단 이름/필터 v2 제품·공통22계열과 PARA/CHAR 선언19·catalog3 및 현재 저장/엄격한 선언 제품 신규26+영향3 검증, 문자 스타일 본문/전체 옵션·실제 적용/실행/저장/target 미완료 |'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NAMED_DECLARATIONS_PRODUCT_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NAMED_DECLARATIONS_PRODUCT_SYNC',own_cpu_selection=selection,Cargo_tests_DB_or_Native_replayed=False,
        document_and_changed_source_audit_not_fresh_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False,
        body_occurrences_or_target_semantics_qualified=False,character_style_capture_authorized=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);run=compact.unpack(q.json(base.OUTPUT));docs=q.json(base.DOCS);resolver=compact.unpack(q.json(base.BASE))
        c.require(q.snapshots[base.OUTPUT]['sha256']=='278695e20b8d3406dc28b9a6f483cfad44ffc73ebadde06a1e53c34119f09cfe'and run['cleanup']
            and run['fresh_inputs']==run['final_fresh_hashes']==842 and run['state']=='PASS_CURRENT_NAMED_DECLARATIONS_SERVICE_PRODUCT26_AFFECTED_NAMED3_NOT_BODY_BINDING_NATIVE_OR_GATE','EXACT359_CURRENT26_AFFECTED3_TERMINAL_FULL_FRESH_SOURCE')
        c.require(docs['cleanup']and docs['distinct_declaration_cases']==19 and docs['original_catalog_cases']==3,'EXACT356_PRIOR_DECLARATION19_CATALOG3_DOC_BASELINE')
        old={p['path']:p for p in run['source_pins']};sources=base.NEW|{base.STORE_PARENT,base.PRODUCT_PARENT,base.CORE,
            'crates/product-cli/tests/named_style_product.rs','crates/product-cli/tests/support/stored_source_fixture.rs',
            'crates/product-cli/src/form_stored_provider/actual_import/source_search.rs','crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/named_styles.rs',
            'crates/hwpx-package/src/character_style.rs','crates/hwpx-package/src/id_index.rs','tools/p09/named_style_verification_runtime.py'}
        for path in sorted(sources):q.pin(path);c.require(q.snapshots[path]==old[path],'ALL_CURRENT_DECLARATION_SERVICE_PRODUCT_TEST_GUARDS_AND_ORIGINAL_READERS_MATCH359')
        base.inverse(q,{p['path']:p for p in resolver['source_pins']})
        failed=compact.unpack(q.json(latest.recovery.FAILED));c.require(failed['failed_final_fresh_check']and failed['system_CPU_max']==94.47 and failed.get('fresh_inputs')is None,'357_CPU_PEAK_AND_FAILED_FINAL_FRESH_NOT_PROMOTED')
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(base.TEST)));c.require(len(cases)==26 and '#[ignore]'not in q.text(base.TEST),'EXACT26_NO_IGNORES')
        tools.good_step(run['steps'][0],cases);tools.good_step(run['steps'][1],base.AFFECTED)
        c.require(run['elapsed_seconds']==135.172 and run['system_CPU_max']==32.16 and 25.9121<run['available_RAM_min_percent']<25.9122
            and max(s['owned_job']['last_job_accounting']['peak_job_private_mib']for s in run['steps'])==933.64,'EXACT359_RESOURCES_NOT_FREEZE_SOLUTION')
        old_docs={p['path']:p for p in docs['source_pins']};state=q.text(STATE);marker='> 2026-10-21 P09 ACTIVE 최신 문단과 문자 스타일 선언 해석'
        c.require(state.startswith('> 2026-10-21 P09 ACTIVE 최신 스타일 선언의 현재 저장과 제품 요청')and state.count(marker)==1,'ONE_CURRENT_SERVICE_PRODUCT_DECLARATION_PREFIX')
        prefix=state[:state.index(marker)];audit.inverse(state[state.index(marker):],old_docs[STATE],'ALL_PRIOR_DECLARATION_RUNTIME_FAILURE_AND_PHASE_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 스타일 선언의 현재 저장과 제품 요청\n');end=progress.index('## 원본 문단과 문자 스타일 선언의 이름 해석\n',start);section=progress[start:end]
        c.require(progress.count(NEW_ROW)==1,'ONLY_SEARCH025_ROW_ADVANCED');audit.inverse((progress[:start]+progress[end:]).replace(NEW_ROW,OLD_ROW),old_docs[PROGRESS],'ALL_OTHER18_SEARCH_ROWS_AND_PRIOR_PROGRESS_PRESERVED')
        report=q.text(REPORT);start=report.index('## 스타일 선언의 현재 저장과 제품 요청\n');end=report.index('## 문단과 문자 스타일의 원본 선언과 자원 해석\n',start);report_section=report[start:end]
        audit.inverse(report[:start]+report[end:],old_docs[REPORT],'ALL_PRIOR_NAMED_SOURCE_PRODUCT_IMPORT_AND_BOUND_FAILURES_PRESERVED')
        profile=q.text(PROFILE);q.pin(DRIVER)
        for document in(prefix,section,report_section,profile):
            for marker in('357','358','359','842fresh/final842','29pass','공식158/249','P09/A12/A13 OPEN','Native011 미승인/미실행','문자 스타일','고정6종'):
                c.require(marker in document,'CURRENT_SERVICE_METADATA_ONLY_COUNTS_CAPTURE_AND_PHASE_BOUNDARIES_EXACT')
        for marker in('idempotency_key_claimed','resolve_named_style_declarations','16KiB','4MiB','consumer','RouteUnqualified','본문','승인','840fresh/final840','94.47%'):
            c.require(marker in profile,'STRICT_REQUEST_FINITE_RESPONSE_CURRENT_ACCESS_AND_ORIGINAL_FAILURE_SCOPE')
        for path,document in((PROGRESS,section),(REPORT,report_section),(PROFILE,profile)):
            for target in re.findall(r'\]\(([^)]+)\)',document):
                c.require(not target.startswith('http'),'ONLY_LOCAL_EXISTING_DECLARATION_CONTRACT_AND_EVIDENCE_LINKS');p=((c.ROOT/path).parent/target).resolve()
                c.require(p.is_relative_to(c.ROOT.resolve())and p.is_file(),'LOCAL_DECLARATION_EVIDENCE_AND_CONTRACT_LINK_EXISTS')
        q.finish();guard.check(force=True);row.update(state='PASS_CURRENT_DECLARATION_SERVICE_PRODUCT29_DOC_SYNC_NOT_CHARACTER_BODY_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_service_product_cases=26,affected_named_product_cases=3,retained_original_declaration_cases=19,mutation_families=22,official_queue_accepted=158,official_queue_total=249,
            next_work='qualified_character_style_before_after_sources_then_body_mapping_full_options_and_actual_execution')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'NAMED_DECLARATIONS_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
