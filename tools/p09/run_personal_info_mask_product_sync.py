"""366: service/product33 + original boundary3, source/docs-only audit with no passed-test replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_personal_info_mask_product as base
shared,c,a,tools,compact,harness,audit=base.shared,base.c,base.a,base.tools,base.compact,base.harness,base.audit
OUTPUT='implementation/p09/evidence/p09-361-personal-info-mask-product-sync366.v1.json';DRIVER='tools/p09/run_personal_info_mask_product_sync.py'
STATE='CURRENT_STATE.md';PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md';REPORT='implementation/p09/P09_PERSONAL_INFO_MASK_PROGRESS.md'
PROFILE='protocol/migrations/p09-personal-info-mask-product-v1.md'
OLD_ROW='| SEARCH-019 | 개인정보 바로 바꾸기 | 명시적 선택/두 별표 정책 source25+공유 경계3 검증, 현재 저장/제품·전체 개인정보 정책·문서 전체 익명화/실제 실행/저장/target 미완료 |'
NEW_ROW='| SEARCH-019 | 개인정보 바로 바꾸기 | 선택 마스킹 source25+공유3 및 현재 저장/엄격한 제품·출력 폐기 preview 신규33+영향3 검증, 공통 실행/저장·전체 개인정보 정책/문서 전체 익명화/target 미완료 |'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'PERSONAL_INFO_MASK_PRODUCT_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PERSONAL_INFO_MASK_PRODUCT_SYNC',own_cpu_selection=selection,Cargo_tests_DB_or_Native_replayed=False,
        document_and_changed_source_audit_not_fresh_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False,
        whole_package_personal_data_removed=False,native_mask_semantics_or_execution_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);run=compact.unpack(q.json(base.OUTPUT));docs=q.json(base.DOCS);before=compact.unpack(q.json(base.BASE))
        c.require(q.snapshots[base.OUTPUT]['sha256']=='e20bcb78ea203d8ecfc0b4e8d7d09adb28d56e5838352de665c6603239ede3e0'and run['cleanup']and run['fresh_inputs']==run['final_fresh_hashes']==856
            and run['state']=='PASS_CURRENT_PERSONAL_INFO_MASK_SERVICE_PRODUCT33_AFFECTED_NAMED3_NOT_NATIVE_SANITIZATION_OR_GATE','EXACT365_CURRENT33_AND_AFFECTED3_FULL_FRESH_SOURCE_AND_TERMINAL_JOBS')
        c.require(q.snapshots[base.DOCS]['sha256']=='23b83be5e323a5ffd72dd77ee785336d0ab5aa5f7b59ddf73f206d302c98dae2'and docs['cleanup'],'EXACT364_PRIOR_SOURCE_ONLY_DOC_BASELINE')
        old={p['path']:p for p in run['source_pins']};sources=base.NEW|{base.STORE_PARENT,base.PRODUCT_PARENT,
            'crates/hwpx-package/src/document_import/search/replacement/atoms/personal_info.rs','crates/hwpx-package/tests/personal_info_mask.rs',
            'crates/product-cli/src/form_stored_provider/actual_import.rs','crates/product-cli/src/form_stored_provider/actual_import/source_search.rs',
            'crates/product-cli/src/form_product_request/stored_source_search/selector.rs','crates/product-cli/src/form_product_request/stored_literal_replacement/selector.rs',
            'crates/product-cli/tests/named_style_product.rs','crates/product-cli/tests/support/stored_source_fixture.rs','tools/p09/named_style_verification_runtime.py'}
        for path in sorted(sources):q.pin(path);c.require(q.snapshots[path]==old[path],'ALL_CURRENT_MASK_SERVICE_PRODUCT_TESTS_CORE_SHARED_GUARDS_AND_STRICT_SELECTOR_MATCH365')
        base.inverse(q,{p['path']:p for p in before['source_pins']})
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(base.TEST)));c.require(len(cases)==33 and '#[ignore]'not in q.text(base.TEST),'EXACT_CURRENT33_NO_IGNORES')
        tools.good_step(run['steps'][0],cases);tools.good_step(run['steps'][1],base.AFFECTED)
        c.require(run['elapsed_seconds']==172.843 and run['system_CPU_max']==33.97 and 37.0530<run['available_RAM_min_percent']<37.0531
            and max(s['owned_job']['last_job_accounting']['peak_job_private_mib']for s in run['steps'])==1896.59,'EXACT365_RESOURCE_SCOPE_NOT_FREEZE_FIX')
        old_docs={p['path']:p for p in docs['source_pins']};state=q.text(STATE);marker='> 2026-10-21 P09 ACTIVE 최신 개인정보 선택 본문 마스킹'
        c.require(state.startswith('> 2026-10-21 P09 ACTIVE 최신 개인정보 마스킹의 현재 저장과 제품 요청')and state.count(marker)==1,'ONE_CURRENT_STORED_PRODUCT_MASK_PREFIX')
        prefix=state[:state.index(marker)];audit.inverse(state[state.index(marker):],old_docs[STATE],'ALL_PRIOR_SOURCE_MASK_FAILURE_STYLE_AND_PHASE_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 개인정보 마스킹의 현재 저장과 제품 요청\n');end=progress.index('## 선택한 원본 본문의 개인정보 마스킹\n',start);section=progress[start:end]
        c.require(progress.count(NEW_ROW)==1,'ONLY_SEARCH019_ROW_ADVANCED');audit.inverse((progress[:start]+progress[end:]).replace(NEW_ROW,OLD_ROW),old_docs[PROGRESS],'ALL_OTHER18_SEARCH_ROWS_AND_PRIOR_PROGRESS_PRESERVED')
        report=q.text(REPORT);start=report.index('## 현재 저장과 엄격한 제품 요청\n');end=report.index('## 선택과 두 마스킹 정책\n',start);report_section=report[start:end]
        audit.inverse(report[:start]+report[end:],old_docs[REPORT],'ALL_PRIOR_SOURCE_MASK_POLICIES_FIXTURE_FAILURES_AND_PRIVACY_BOUNDARIES_PRESERVED')
        profile=q.text(PROFILE);q.pin(DRIVER)
        for document in(prefix,section,report_section,profile):
            for marker in('365','856fresh/final856','36pass','공식158/249','P09/A12/A13 OPEN','Native011 미승인/미실행','SEARCH-020','preview'):
                c.require(marker in document,'CURRENT_SERVICE_PREVIEW_COUNTS_NO_SEARCH020_SANITIZATION_NATIVE_OR_GATE_PROMOTION')
        for marker in('preview_only','mask_selected_personal_info','16KiB','4MiB','PreviewOnly','RouteUnqualified','whole_package_personal_data_removed=false',
            'idempotency_key_claimed','consumer','query/replacement','개인정보 값별 해시','미리보기'):
            c.require(marker in profile,'STRICT_SCHEMA_SOURCE_BOUND_NO_OUTPUT_PREVIEW_AND_FINITE_PRIVACY_BOUNDARIES')
        for path,document in((PROGRESS,section),(REPORT,report_section),(PROFILE,profile)):
            for target in re.findall(r'\]\(([^)]+)\)',document):
                c.require(not target.startswith('http'),'LOCAL_EXISTING_SOURCE_PROFILE_AND_PRODUCT_EVIDENCE_ONLY');p=((c.ROOT/path).parent/target).resolve()
                c.require(p.is_relative_to(c.ROOT.resolve())and p.is_file(),'LOCAL_MASK_PRODUCT_CONTRACT_AND_EVIDENCE_LINK_EXISTS')
        q.finish();guard.check(force=True);row.update(state='PASS_CURRENT_MASK_SERVICE_PRODUCT33_AFFECTED3_DOC_SYNC_NOT_COMMON_EXECUTION_NATIVE_SANITIZATION_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_service_product_cases=33,affected_named_product_cases=3,retained_original_source_mask_cases=25,mutation_families=22,official_queue_accepted=158,official_queue_total=249,
            next_work='mutation_only_compiler_owner_common_dispatch_then_actual_execution_and_full_privacy_target_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'PERSONAL_INFO_MASK_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
