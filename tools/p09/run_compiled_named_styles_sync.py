"""347: synchronize current named stored/product/common docs; no Rust/DB/Native replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_compiled_named_styles_recovery as latest
base=latest.base
shared,c,a,tools,compact,harness,audit=latest.shared,latest.c,latest.a,latest.tools,latest.compact,latest.harness,latest.audit
OUTPUT='implementation/p09/evidence/p09-361-compiled-named-styles-sync347.v1.json';DRIVER='tools/p09/run_compiled_named_styles_sync.py'
DOC_BASE='implementation/p09/evidence/p09-361-named-paragraph-styles-sync342.v1.json';FONT_BASE='implementation/p09/evidence/p09-361-compiled-font-options-sync336.v1.json'
STATE='CURRENT_STATE.md';PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md';REPORT='implementation/p09/P09_NAMED_STYLE_REPLACEMENT_PROGRESS.md'
SOURCE='protocol/migrations/p09-named-paragraph-style-source-v1.md';PROFILE='protocol/migrations/p09-named-paragraph-style-product-v1.md'
COMMON='protocol/migrations/p09-common-search-mutation-dispatch.md';COMPILER='protocol/migrations/p09-source-search-operation-compiler-v1.md';FONT='protocol/migrations/p09-font-options-product-v2.md'
OLD_ROW='| SEARCH-025 | 스타일 일괄 대체 | 문단 스타일 이름→원본 styleIDRef 신규19+영향7 고유26개 검증, 문자 스타일/필터·저장/제품/preview·실제 적용/실행/target 미완료 |'
NEW_ROW='| SEARCH-025 | 스타일 일괄 대체 | 문단 이름 core26·현재 저장/제품/preview 고유31·공통 준비/계획 신규19+영향12 검증, 문자 스타일/필터/전체 옵션·실제 적용/실행/저장/target 미완료 |'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'COMPILED_NAMED_DOC_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_COMPILED_NAMED_DOC_SYNC',own_cpu_selection=selection,tests_build_DB_or_Hangul_replayed=False,
        document_and_changed_source_audit_not_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT));failed=compact.unpack(q.json(base.OUTPUT))
        metadata=compact.unpack(q.json(base.previous.OUTPUT));product=compact.unpack(q.json(base.previous.previous.OUTPUT));docs=q.json(DOC_BASE);fonts=q.json(FONT_BASE)
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='e3e66e16e0eb259a3d9eddba7c8973d99b2d13e4d019f1b848d1dfa5f3cefa58'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==806 and passed['new_cases']==19 and passed['affected_cases']==12,'EXACT346_NAMED_COMMON_NEW19_AFFECTED12')
        c.require(q.snapshots[base.OUTPUT]['sha256']=='a28972345759ca8830bc6549208134af9000be1e379779baf472609ca48eae89'and failed['cleanup']and failed['steps'][0]['tests']==[],'EXACT345_COMPILE_FAILURE_RETAINED')
        c.require(q.snapshots[base.previous.OUTPUT]['sha256']=='9602e98eecd230c3ff3c351bd8a9e8a86734bbb66a373ceb8a8a6cc718131130'and metadata['cleanup']and metadata['distinct_product_cases']==31,'EXACT344_CURRENT_SERVER_METADATA31')
        c.require(q.snapshots[base.previous.previous.OUTPUT]['sha256']=='97b2c77bf78accbaf2a75c9095a7ac9443b2154838ffcd0e20dd6e487f521b95'and product['cleanup']and len(product['steps'][0]['tests'])==29,'EXACT343_ORIGINAL29_PRODUCT_CASES')
        c.require(q.snapshots[DOC_BASE]['sha256']=='a60b6c6c7b17c014bb67cb591423d5b86f7c81791aea71787930ed37d9354842'and docs['cleanup'],'EXACT342_DOC_BASELINE')
        c.require(q.snapshots[FONT_BASE]['sha256']=='758b9201a9a8b3ca36c2dbbd6be671f7a62046c0cb41146c691fb90862d2f9d6'and fonts['cleanup'],'EXACT336_COMMON_FONT_CONTRACT_BASELINE')
        old={p['path']:p for p in passed['source_pins']};original={p['path']:p for p in metadata['source_pins']}
        sources=base.CHANGED|base.NEW|{latest.DRIVER,base.previous.SEARCH,'crates/product-cli/src/form_product_request/stored_operations/compiled_search.rs',
            'crates/product-cli/src/form_product_request/stored_operations/compiled_search/build.rs','crates/product-cli/src/form_product_request/stored_operations/compiled_search/owners.rs',
            'crates/product-cli/src/form_product_request/stored_operations/search_preview.rs'}
        for n in sorted(sources):q.pin(n);c.require(q.snapshots[n]==old[n],'CURRENT_CHANGED_CODE_TESTS_LIMITS_AND_ORIGINAL_COMPILER_MATCH346')
        base.inverse(q,original)
        cases={'compiled_named::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(base.TEST))}
        tools.good_step(passed['steps'][0],cases|base.AFFECTED_NAMED);tools.good_step(passed['steps'][1],base.AFFECTED_FONT)
        for result in(product,metadata,failed,passed):
            for step in result['steps']:
                job=step['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0,'ALL_OWNED_JOBS_TERMINAL_EMPTY_CLOSED')
        c.require(passed['elapsed_seconds']==134.766 and passed['system_CPU_max']==32.39 and 40.1648<passed['available_RAM_min_percent']<40.1650,'EXACT346_RESOURCE_METADATA')
        c.require(max(s['owned_job']['last_job_accounting']['peak_job_private_mib']for s in passed['steps'])==782.48,'EXACT346_OWNED_PRIVATE_PEAK')
        old_docs={p['path']:p for p in docs['source_pins']};old_fonts={p['path']:p for p in fonts['source_pins']}
        state=q.text(STATE);marker='> 2026-10-21 P09 ACTIVE 최신 문단 스타일 이름 일괄 참조 대체';c.require(state.count(marker)==1,'ONE_PRIOR_SOURCE_ONLY_PREFIX')
        prefix=state[:state.index(marker)];audit.inverse(state[state.index(marker):],old_docs[STATE],'ALL_PRIOR_CURRENT_STATE_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 문단 스타일 이름 대체의 제품과 공통 계획\n');end=progress.index('## 문단 스타일 이름을 사용하는 원본 참조 대체\n',start);section=progress[start:end]
        c.require(progress.count(NEW_ROW)==1,'ONE_SEARCH025_ROW_ADVANCED');audit.inverse((progress[:start]+progress[end:]).replace(NEW_ROW,OLD_ROW),old_docs[PROGRESS],'ALL_OTHER18_SEARCH_ROWS_AND_HISTORY_UNCHANGED')
        report=q.text(REPORT);start=report.index('## 현재 저장과 제품 요청 및 공통 계획\n');end=report.index('## 원본 선택과 변경\n',start);audit.inverse(report[:start]+report[end:],old_docs[REPORT],'ALL_NAMED_SOURCE_FAILURES_AND_SOURCE26_HISTORY_UNCHANGED')
        source=q.text(SOURCE);source_before='''full_style_filter_character_style_native_or_execution_qualified는 false다. 현재 ACL/head/AEAD,
저장/제품/preview·문자 스타일·전체 옵션과 실행/저장/게시·Native/Gate는 아직 연결/검증하지 않았다.
''';source_after='''full_style_filter_character_style_native_or_execution_qualified는 false다. 현재 ACL/head/AEAD·저장/제품/preview와
공통 계획 연결은 [별도 제품 계약](p09-named-paragraph-style-product-v1.md)을 따른다. 문자 스타일·
서식 필터/전체 옵션과 실제 실행/저장/게시·Native/Gate는 미완료다. pure core 자체는 현재 실행 권한이 아니다.
''';c.require(source.count(source_after)==1,'ONE_SOURCE_TO_PRODUCT_CONTRACT_LINK');audit.inverse(source.replace(source_after,source_before),old_docs[SOURCE],'SOURCE_QUERY_READER_PRESERVATION_AND_FAILURE_CONTRACT_UNCHANGED')
        common=q.text(COMMON);start=common.index('현재 변경 준비 표는21개 family');end=common.index('폰트 연결 당시 변경 준비 표는20개 family',start)
        audit.inverse(common[:start]+common[end:].replace('폰트 연결 당시 변경 준비 표는20개 family','현재 변경 준비 표는20개 family',1),old_fonts[COMMON],'ALL_PRIOR_COMMON_CONTRACT_AND_FAILURE_HISTORY_PRESERVED')
        compiler=q.text(COMPILER);start=compiler.index('현재 공통 표는 기존20개 순서');end=compiler.index('폰트 연결 당시 공통 표는 기존19개',start)
        audit.inverse(compiler[:start]+compiler[end:].replace('폰트 연결 당시 공통 표는 기존19개','현재 공통 표는 기존19개',1),old_fonts[COMPILER],'ALL_PRIOR_COMPILER_RESOURCE_AND_GUARD_CONTRACT_PRESERVED')
        font=q.text(FONT);start=font.index('폰트 연결 당시 공통 mutation 표는');end=font.index('\n\npreview_only=true는',start)
        audit.inverse(font[:start]+'공통 mutation 표는 기존19개 순서를 유지한20개이며 `FontOptions`가 마지막이다.'+font[end:],old_fonts[FONT],'FONT_SCHEMA_STRICT_INPUT_PREVIEW_SOURCE_AND_RESOURCE_CONTRACT_UNCHANGED')
        profile=q.text(PROFILE);q.pin(DRIVER)
        for document in(prefix,section,report,profile):
            for marker in('공식158/249','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행','문자 스타일','preview'):
                c.require(marker in document,'CURRENT_DOCUMENT_SCOPE_AND_GATE_BOUNDARIES_EXACT')
        for marker in('343','344','345','346','806fresh/final806','32.39%','782.48MiB','384문단','공통21번째'):
            c.require(marker in prefix+section+report,'CURRENT_RECEIPTS_FAILURE_RESOURCE_AND_SERVER_LIMIT_SCOPE')
        for path,document in((PROGRESS,section),(REPORT,report),(SOURCE,source),(PROFILE,profile),(COMMON,common),(COMPILER,compiler),(FONT,font)):
            for target in re.findall(r'\]\(([^)]+)\)',document):
                resolved=((c.ROOT/path).parent/target).resolve();c.require(resolved.is_relative_to(c.ROOT.resolve())and resolved.is_file(),'LOCAL_EVIDENCE_AND_CONTRACT_LINK_EXISTS')
        q.finish();guard.check(force=True);row.update(state='PASS_NAMED_STYLE_PRODUCT31_COMMON_NEW19_AFFECTED12_CURRENT_DOC_SYNC_NOT_FULL_SEARCH025_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            product_distinct_cases=31,common_new_cases=19,latest_affected_cases=12,mutation_families=21,official_queue_accepted=158,official_queue_total=249,
            next_work='named_character_styles_filters_full_options_and_qualified_execution_storage')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'COMPILED_NAMED_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
