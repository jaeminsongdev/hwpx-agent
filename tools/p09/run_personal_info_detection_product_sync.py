"""379: current read-only detection product32 + original mask3 evidence/docs; no passed-test replay."""
import json,re,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_personal_info_detection_product as base
shared,c,a,tools,compact,harness,audit=r.shared,r.c,r.a,r.tools,r.compact,r.harness,r.audit
OUTPUT='implementation/p09/evidence/p09-361-personal-info-detection-product-sync379.v1.json';DRIVER='tools/p09/run_personal_info_detection_product_sync.py'
STATE='CURRENT_STATE.md';SEARCH='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md';REPORT='implementation/p09/P09_PERSONAL_INFO_DETECTION_PROGRESS.md'
PROFILE='protocol/migrations/p09-personal-info-detection-product-v1.md'
OLD_ROW='| SEARCH-020 | 개인정보 찾아 바꾸기 | 명시적 형식 탐지/읽기 전용 원본 선택 core 신규23+영향3 검증, 현재 저장/제품·기본 형식 정책·전체 계약·실제 변경/저장/target 미완료 |'
NEW_ROW='| SEARCH-020 | 개인정보 찾아 바꾸기 | 명시적 형식 탐지 source23·현재 저장/엄격한 읽기 전용 제품/결과 이동·선택 신규32+영향3 검증, 기본 형식 정책·전체 계약·실제 변경/저장/target 미완료 |'
OLD_INTRO='원문을 노출하지 않는 위치·종류와 원본 선택 좌표를 반환한다. 현재 저장 서비스·엄격한 제품 요청은\n다음 연결이며 한글 기본 개인정보 패턴이나 실제 개인정보 유효성을 판정한 결과가 아니다.'
NEW_INTRO='원문을 노출하지 않는 위치·종류와 원본 선택 좌표를 반환한다. 현재 저장 서비스·엄격한 읽기 전용 제품\n요청에도 연결했으며 한글 기본 개인정보 패턴이나 실제 개인정보 유효성을 판정한 결과는 아니다.'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'DETECTION_PRODUCT_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_DETECTION_PRODUCT_SYNC',own_cpu_selection=selection,Cargo_tests_DB_or_Native_replayed=False,
        document_and_changed_source_audit_not_fresh_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False,
        whole_package_personal_data_removed=False,native_format_policy_or_execution_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);run=compact.unpack(q.json(base.OUTPUT));docs=q.json(base.DOCS);previous=compact.unpack(q.json(base.BASE))
        c.require(q.snapshots[base.OUTPUT]['sha256']=='878ffdb85abcc6fc57635c45a3a142b2bad2a8b4d5f4037f6b7f87359fd0e732'and run['cleanup']
            and run['fresh_inputs']==run['final_fresh_hashes']==881 and len(run['steps'])==1 and run['new_cases']==32 and run['affected_cases']==3,'EXACT378_FULL_CURRENT_SOURCE_READ_ONLY_PRODUCT32_AFFECTED3')
        c.require(q.snapshots[base.DOCS]['sha256']=='dc9a5efb9c3a645878ae064104d72861d66832fa16c6475699356c3e3df38ab4'and docs['cleanup']
            and docs['fresh_inputs']==docs['final_fresh_hashes']==31,'EXACT377_SOURCE_ONLY_DOC_BASELINE_RETAINS_FAILURES_NOT_RUNTIME_REPLAY')
        pins={p['path']:p for p in run['source_pins']};sources=base.NEW|base.CHANGED|{'tools/p09/named_style_verification_runtime.py',
            'crates/hwpx-package/src/document_import/search/personal_info.rs','crates/hwpx-package/src/document_import/search/reviews/selector.rs',
            'crates/product-cli/src/form_stored_provider/actual_import.rs','crates/product-cli/src/form_stored_provider.rs',
            'crates/product-cli/src/form_product_request/stored_source_search/selector.rs','crates/product-cli/src/form_product_request/stored_source_search/navigation.rs',
            'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/personal_info.rs',
            'crates/product-cli/tests/support/stored_source_fixture.rs','crates/product-cli/tests/support/personal_info_mask_compiled.rs'}
        for path in sorted(sources):q.pin(path);c.require(q.snapshots[path]==pins[path],'CURRENT_READ_ONLY_SOURCE_OWNER_PRODUCT_TESTS_AND_SHARED_ACCESS_GUARDS_MATCH378')
        base.inverse(q,{p['path']:p for p in previous['source_pins']})
        cases={'detection::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(base.TEST))}
        c.require(len(cases)==32 and '#[ignore]'not in q.text(base.TEST),'CURRENT32_WITHOUT_IGNORES');tools.good_step(run['steps'][0],cases|base.AFFECTED)
        c.require(run['steps'][0]['diagnostics']==[]and run['elapsed_seconds']==162.407 and run['system_CPU_max']==41.07
            and 35.8554<run['available_RAM_min_percent']<35.8555 and run['steps'][0]['owned_job']['last_job_accounting']['peak_job_private_mib']==1906.07,'EXACT378_WARNINGS_NONE_RESOURCE_SCOPE_NOT_FREEZE_FIX')
        old={p['path']:p for p in docs['source_pins']};state=q.text(STATE);marker='> 2026-10-21 P09 ACTIVE 최신 개인정보 형식 탐지와 원본 선택'
        c.require(state.startswith('> 2026-10-21 P09 ACTIVE 최신 개인정보 탐지의 현재 저장과 읽기 전용 제품')and state.count(marker)==1,'ONE_CURRENT_READ_ONLY_PRODUCT_PREFIX')
        prefix=state[:state.index(marker)];audit.inverse(state[state.index(marker):],old[STATE],'ALL_PREVIOUS_SOURCE_DETECTION_FAILURES_MASK_AND_PHASE_HISTORY_RETAINED')
        search=q.text(SEARCH);start=search.index('## 개인정보 탐지의 현재 저장과 읽기 전용 제품\n');end=search.index('## 개인정보 형식 탐지와 원본 선택\n',start);section=search[start:end]
        c.require(search.count(NEW_ROW)==1,'ONLY_SEARCH020_ROW_ADVANCED');audit.inverse((search[:start]+search[end:]).replace(NEW_ROW,OLD_ROW),old[SEARCH],'ALL_OTHER18_SEARCH_ROWS_AND_PREVIOUS_PROGRESS_RETAINED')
        report=q.text(REPORT);start=report.index('## 현재 저장과 읽기 전용 제품 요청\n');end=report.index('## 탐지와 선택 경계\n',start);report_section=report[start:end]
        c.require(report.count(NEW_INTRO)==1 and report.count('## 원본 코어 당시의 다음 제품 연결\n')==1,'ONE_CURRENT_INTRO_AND_HISTORICAL_NEXT_LABEL')
        restored=(report[:start]+report[end:]).replace(NEW_INTRO,OLD_INTRO).replace('## 원본 코어 당시의 다음 제품 연결\n','## 다음 제품 연결\n')
        audit.inverse(restored,old[REPORT],'ALL_SOURCE23_FIXTURE_FAILURES_RECOVERY26_AND_PRIOR_RESOURCE_EVIDENCE_PRESERVED')
        profile=q.text(PROFILE);q.pin(DRIVER)
        for text in(prefix,section,report_section,profile):
            for marker in('378','881fresh/final881','35pass','공식158/249','P09/A12/A13 OPEN','Native011 미승인/미실행','문자 스타일6종','실제 변경/저장'):
                c.require(marker in text,'CURRENT32_AFFECTED3_READ_ONLY_AND_UNCHANGED_PHASE_BOUNDARIES_EXPLICIT')
        for marker in('read_only','find_personal_info_formats','16KiB','4096byte','1~16','1~10000','detection_receipt_sha256','occurrence_index',
            'preview_only','RouteUnqualified','whole_package_personal_data_removed','consumer-final head','target match_set/semantic_diff/reopen'):
            c.require(marker in profile,'STRICT_BOUND_NEXT_SELECTION_WITHOUT_MUTATION_PREVIEW_EXECUTION_OR_SANITIZATION_PROMOTION')
        for path,text in((SEARCH,section),(REPORT,report_section),(PROFILE,profile)):
            for link in re.findall(r'\]\(([^)]+)\)',text):
                c.require(not link.startswith('http'),'ONLY_LOCAL_CURRENT_CONTRACTS_AND_EVIDENCE');target=((c.ROOT/path).parent/link).resolve()
                c.require(target.is_relative_to(c.ROOT.resolve())and target.is_file(),'ALL_REFERENCED_READ_ONLY_PRODUCT_CONTRACTS_AND_EVIDENCE_EXIST')
        q.finish();guard.check(force=True);row.update(state='PASS_CURRENT_STORED_DETECTION_PRODUCT32_AFFECTED3_DOC_SYNC_NOT_NATIVE_DEFAULTS_MUTATION_SANITIZATION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_product_cases=32,affected_mask_cases=3,retained_original_source_cases=23,mutation_families=23,
            official_queue_accepted=158,official_queue_total=249,next_work='qualified_native_format_policy_full_options_and_actual_execution_storage_target')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'DETECTION_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
