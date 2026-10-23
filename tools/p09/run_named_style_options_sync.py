"""353: current named v2/common docs; original failures preserved, no Cargo/Native replay."""
import json,re,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_compiled_named_style_options as base
shared,c,a,tools,compact,harness,audit=r.shared,r.c,r.a,r.tools,r.compact,r.harness,r.audit
OUTPUT='implementation/p09/evidence/p09-361-named-style-options-sync353.v1.json';DRIVER='tools/p09/run_named_style_options_sync.py'
RECONCILED='implementation/p09/evidence/p09-361-compiled-named-style-options-reconciled352.v1.json'
DOC_BASE='implementation/p09/evidence/p09-361-filtered-named-styles-sync349.v1.json';COMMON_BASE='implementation/p09/evidence/p09-361-compiled-named-styles-sync347.v1.json'
STATE='CURRENT_STATE.md';PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md';REPORT='implementation/p09/P09_NAMED_STYLE_REPLACEMENT_PROGRESS.md'
SOURCE='protocol/migrations/p09-named-paragraph-style-source-v1.md';V1='protocol/migrations/p09-named-paragraph-style-product-v1.md';PROFILE='protocol/migrations/p09-named-paragraph-style-product-v2.md'
COMMON='protocol/migrations/p09-common-search-mutation-dispatch.md';COMPILER='protocol/migrations/p09-source-search-operation-compiler-v1.md';FONT='protocol/migrations/p09-font-options-product-v2.md'
OLD_ROW='| SEARCH-025 | 스타일 일괄 대체 | 문단 이름 core26·제품/preview31·공통 신규19+영향12·필터 원본 신규18+영향9 검증, 필터 저장/제품/공통·문자 스타일/전체 옵션·실제 적용/실행/저장/target 미완료 |'
NEW_ROW='| SEARCH-025 | 스타일 일괄 대체 | 문단 이름/필터 core·현재 저장/엄격한 v2/preview 신규28+영향4·공통22계열 신규18+영향9 원 결과 대조, 문자 스타일/전체 옵션·실제 적용/실행/저장/target 미완료 |'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NAMED_OPTIONS_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NAMED_OPTIONS_SYNC',own_cpu_selection=selection,Cargo_tests_DB_or_Native_replayed=False,
        document_and_changed_source_audit_not_fresh_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);recovered=q.json(RECONCILED);failed=compact.unpack(q.json(base.OUTPUT));product=compact.unpack(q.json(base.previous.OUTPUT));docs=q.json(DOC_BASE);prior=q.json(COMMON_BASE)
        c.require(q.snapshots[RECONCILED]['sha256']=='c15c8ffc2918b884f0c08a27884255d6cd871ad6dd07cd1757c166cbbd2d026f'and recovered['cleanup']and recovered['fresh_inputs']==recovered['final_fresh_hashes']==26
            and recovered['original_case_count']==27 and recovered['original_failure_receipt_unchanged'],'EXACT352_ORIGINAL27_RECONCILED_WITHOUT_REPLAY')
        c.require(q.snapshots[base.OUTPUT]['sha256']=='11bbf8033db14c59af5f439e6d1aef70705865ca1c0d6d9fb99641879481051f'and failed['state']=='FAILED_COMPILED_NAMED_OPTIONS'
            and failed['error_type']=='AttributeError'and failed['cleanup']and failed['fresh_inputs']==failed['final_fresh_hashes']==821,'EXACT351_FAILED_POSTCHECK_AND_ORIGINAL_RUNTIME_CLOSURE_RETAINED')
        c.require(q.snapshots[base.previous.OUTPUT]['sha256']=='04f732999478a7068a2b5c2063e967f34f0c1cde750401e63f7b38e1b0f75788'and product['cleanup']and product['fresh_inputs']==product['final_fresh_hashes']==815,'EXACT350_STORED_STRICT_V2_PREVIEW')
        c.require(q.snapshots[DOC_BASE]['sha256']=='1f8e39382b0aa9729d62cc2a39567d14a989dcdaa57df0d13004b4d9e7ec8846'and docs['cleanup'],'EXACT349_DOC_BASELINE')
        c.require(q.snapshots[COMMON_BASE]['sha256']=='b98f65fddb04d344443566c4e99a593fd1aa488114b1f60c94afba1da710cdf8'and prior['cleanup'],'EXACT347_PRIOR_COMMON_CONTRACTS')
        old={p['path']:p for p in recovered['source_pins']}
        for path in sorted(base.CHANGED|base.NEW):q.pin(path);c.require(q.snapshots[path]==old[path],'ALL_CURRENT_OPTIONS_CODE_TESTS_AND_FIXED_RUNTIME_MATCH352')
        base.inverse(q,{p['path']:p for p in product['source_pins']});base.preserve_import_failure(q)
        cases={'named_options::compiled::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(base.TEST))}|base.AFFECTED_OPTIONS|base.AFFECTED_COMMON
        tools.good_step(failed['steps'][0],cases);c.require(len(cases)==27 and len(product['steps'][0]['tests'])==32,'EXACT_NEW18_AFFECTED9_AND_PRIOR_NEW28_AFFECTED4')
        for result in(product,failed):
            job=result['steps'][0]['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0,'BOTH_ORIGINAL_JOBS_EMPTY_CLOSED')
        c.require(product['system_CPU_max']==36.26 and failed['system_CPU_max']==26.56 and failed['steps'][0]['owned_job']['last_job_accounting']['peak_job_private_mib']==924.94,'EXACT_ORIGINAL_RESOURCE_SCOPE')
        old_docs={p['path']:p for p in docs['source_pins']};old_prior={p['path']:p for p in prior['source_pins']}
        state=q.text(STATE);marker='> 2026-10-21 P09 ACTIVE 최신 문단 스타일 이름 대체의 원본 서식 필터';c.require(state.count(marker)==1,'ONE_PRIOR_SOURCE_FILTER_PREFIX');prefix=state[:state.index(marker)]
        audit.inverse(state[state.index(marker):],old_docs[STATE],'ALL_PRIOR_STATE_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 문단 스타일 필터의 제품과 공통 계획\n');end=progress.index('## 원본 서식으로 선택한 문단 스타일 이름 대체\n',start);section=progress[start:end]
        c.require(progress.count(NEW_ROW)==1,'ONLY_SEARCH025_ROW_ADVANCED');audit.inverse((progress[:start]+progress[end:]).replace(NEW_ROW,OLD_ROW),old_docs[PROGRESS],'ALL_OTHER18_SEARCH_ROWS_AND_HISTORY_UNCHANGED')
        report=q.text(REPORT);start=report.index('## 선택적 서식 필터의 저장과 제품 및 공통 계획\n');end=report.index('## 원본 서식 필터를 사용하는 문단 이름 대체\n',start);report_section=report[start:end]
        audit.inverse(report[:start]+report[end:],old_docs[REPORT],'ALL_PRIOR_CORE_PRODUCT_FAILURE_AND_NATIVE_HISTORY_UNCHANGED')
        source=q.text(SOURCE);addition='''필터의 현재 저장·엄격한 v2/preview·공통22번째 변경 계획은 [별도 v2 계약](p09-named-paragraph-style-product-v2.md)을
따른다.350 제품32pass와 원351 공통27pass의 후처리 실패/352 대조는 core348의 증거와 구분한다.
원본 filtered 후보 자체는 현재 접근·실제 실행/저장/게시·Native/Gate 자격을 부여하지 않는다.

''';audit.inverse(base.remove(source,addition),old_docs[SOURCE],'ALL_ORIGINAL_FILTER_EXTENT_EMPTY_SCOPE_AND_READER_CONTRACT_UNCHANGED')
        common=q.text(COMMON);start=common.index('현재 변경 준비 표는22개 family');end=common.index('문단 이름 v1 연결 당시 변경 준비 표는21개',start)
        audit.inverse(common[:start]+common[end:].replace('문단 이름 v1 연결 당시 변경 준비 표는21개','현재 변경 준비 표는21개',1),old_prior[COMMON],'ALL_PRIOR_COMMON_CONTRACT_HISTORY_PRESERVED')
        compiler=q.text(COMPILER);start=compiler.index('현재 공통 표는 기존21개 순서');end=compiler.index('문단 이름 v1 연결 당시 공통 표는 기존20개',start)
        audit.inverse(compiler[:start]+compiler[end:].replace('문단 이름 v1 연결 당시 공통 표는 기존20개','현재 공통 표는 기존20개',1),old_prior[COMPILER],'ALL_PRIOR_COMPILER_LIMITS_OWNERS_AND_HISTORY_PRESERVED')
        font=q.text(FONT);font_before='''현재는 그20개 순서 뒤에 문단 스타일 이름 대체를 추가한21개다. 폰트 v1/v2의 위치와 동작·인자·
기존 SearchPreview API는 그대로이며 [추가 계열 계약](p09-named-paragraph-style-product-v1.md)을 따른다.
''';font_after='''현재는 그20개 순서 뒤에 문단 스타일 이름 v1/v2를 추가한22개다. 폰트 v1/v2의 위치와 동작·인자·
기존 SearchPreview API는 그대로이며 [추가 계열 계약](p09-named-paragraph-style-product-v2.md)을 따른다.
''';c.require(font.count(font_after)==1,'ONLY_CURRENT_FAMILY_COUNT_AND_LINK_UPDATED');audit.inverse(font.replace(font_after,font_before),old_prior[FONT],'ALL_FONT_API_STYLE_RESOURCE_AND_PREVIEW_CONTRACT_UNCHANGED')
        v1=q.text(V1);addition='''선택적 원본 style_filter는 [별도 v2 계약](p09-named-paragraph-style-product-v2.md)에서 처리한다.
v1은 계속 거부하며 v1의21번째 위치와 preview API는 그대로다. 아래는 v1 검증 이력이다.

''';audit.inverse(base.remove(v1,addition),old_prior[V1],'V1_SCHEMA_AND_PREVIEW_CONTRACT_REMAIN_CLOSED')
        profile=q.text(PROFILE);q.pin(DRIVER)
        for document in(prefix,section,report_section,profile):
            for marker in('350','351','352','AttributeError','27pass','공식158/249','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행','문자 스타일'):
                c.require(marker in document,'CURRENT_V2_SCOPE_FAILURES_AND_GATE_BOUNDARIES_EXACT')
        for marker in('815fresh/final815','821fresh/final821','26fresh/final26','재귀 한도1000','36.26%','924.94MiB','전체FAILED'):
            c.require(marker in prefix+section+report_section,'ORIGINAL_RUNTIME_AND_RECONCILIATION_NOT_CONFLATED')
        for path,document in((PROGRESS,section),(REPORT,report_section),(SOURCE,source),(PROFILE,profile),(V1,v1),(COMMON,common),(COMPILER,compiler),(FONT,font)):
            for target in re.findall(r'\]\(([^)]+)\)',document):
                p=((c.ROOT/path).parent/target).resolve();c.require(p.is_relative_to(c.ROOT.resolve())and p.is_file(),'CURRENT_LOCAL_CONTRACT_AND_EVIDENCE_LINK_EXISTS')
        q.finish();guard.check(force=True);row.update(state='PASS_NAMED_V2_STORED_PREVIEW28_COMMON18_CURRENT_DOC_SYNC_ORIGINAL_FAILURES_PRESERVED_NOT_NATIVE_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases=28,new_common_cases=18,original_common_cases=27,original_common_failure_preserved=True,mutation_families=22,official_queue_accepted=158,official_queue_total=249,
            next_work='named_character_style_semantics_full_options_and_qualified_execution_storage')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'NAMED_OPTIONS_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
