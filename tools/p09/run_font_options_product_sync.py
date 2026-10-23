"""334: docs-only current stored/v2 preview proof; preserve source contracts and all earlier history."""
import json,re,time
from types import SimpleNamespace as NS
import run_font_options_product as latest
shared,c,a,tools,compact,audit=latest.shared,latest.c,latest.a,latest.tools,latest.compact,latest.audit
OUTPUT='implementation/p09/evidence/p09-361-font-options-product-sync334.v1.json';DRIVER='tools/p09/run_font_options_product_sync.py'
BASE='implementation/p09/evidence/p09-361-font-style-filter-sync332.v1.json'
REPORT='implementation/p09/P09_FONT_REFERENCE_REPLACEMENT_PROGRESS.md';PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
SOURCE_CONTRACT='protocol/migrations/p09-filtered-font-source-v1.md';PROFILE='protocol/migrations/p09-font-options-product-v2.md'
OLD_ROW='| SEARCH-024 | 폰트 일괄 대체 | 원본/저장/제품·공통 준비/계획·관측 보호와 별도 원본 서식 필터 신규18+영향6개 검증, 필터 저장/제품·preview_only·전체 유효 서식/폰트/fallback·실행/저장/target 미완료 |'
NEW_ROW='| SEARCH-024 | 폰트 일괄 대체 | 원본/저장/엄격한 v2 필터·preview_only 신규28+영향 v1 제품4개 검증, v2 공통 준비/계획·전체 옵션/유효 서식/폰트/fallback·실행/저장/target 미완료 |'
BEFORE='현재 저장 ACL/head/AEAD 및 엄격한 제품 JSON 연결과 preview_only는 아직 미완료다.\n'
AFTER='별도 현재 저장 ACL/head/AEAD와 엄격한 v2 JSON·preview_only 연결은\n[폰트 제품 옵션 계약](p09-font-options-product-v2.md)을 따른다. 이 원본 후보 자체는 현재 서비스 권한이 아니다.\n'
OLD_REMAINS='저장/제품 옵션·preview_only·전체 서식/폰트/보호 의미·신뢰 registry·실제 실행/저장/게시와 Native/Gate는\n'
NEW_REMAINS='전체 제품 옵션·v2 공통 준비/계획·전체 서식/폰트/보호 의미·신뢰 registry·실제 실행/저장/게시와 Native/Gate는\n'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FONT_OPTIONS_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_OPTIONS_SYNC',own_cpu_selection=selection,tests_build_DB_or_Hangul_replayed=False,
        document_and_changed_source_audit_not_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT));docs=q.json(BASE)
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='545d365f0a65a678624607f5d1411385291a1b12b5592d42ccd4f5c2e1e4cf0f'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==774 and passed['new_cases']==28 and passed['affected_cases']==4,'EXACT333_STORED_OPTIONS_PRODUCT32_CURRENT_INPUT_CLOSURE')
        c.require(q.snapshots[BASE]['sha256']=='a4a870da9e284cd8377c0664e49e48acb9d2def666f3a241b0c0199521d45689'and docs['cleanup'],'EXACT332_PRIOR_DOC_BASELINE')
        old={p['path']:p for p in passed['source_pins']};source={latest.STORED,latest.PRODUCT,latest.PARENT,latest.TEST,latest.DRIVER,
            latest.STORED[:-3]+'/options.rs',latest.PRODUCT[:-3]+'/options.rs',latest.previous.CORE,latest.previous.FILTER}
        for n in sorted(source):q.pin(n);c.require(q.snapshots[n]==old[n],'CURRENT_STORED_PRODUCT_FILTER_GUARDS_TESTS_AND_RUNNER_MATCH333')
        previous=compact.unpack(q.json(latest.previous.OUTPUT));latest.inverse(q,{p['path']:p for p in previous['source_pins']})
        stored=q.text(latest.STORED[:-3]+'/options.rs');c.require('pub struct PreparedStoredFontPreview<\'a>{source:LiteralSource<\'a>,receipt:StoredFontOptionsReceipt}'in stored
            and 'drop(output);receipt.profile=STORED_FONT_PREVIEW_PROFILE;receipt.preview_only=true;receipt.candidate_output_retained=false;'in stored,'PREVIEW_OWNS_NO_OUTPUT_ARTIFACT')
        preview_impl=stored[stored.index('impl PreparedStoredFontPreview<\'_>{'):]
        c.require(not any(marker in preview_impl for marker in('with_verified_bytes','inventory','compiler_source!','compiler_font_inventory','into_candidate')),'PREVIEW_IMPL_HAS_NO_OUTPUT_OR_MUTATION_ADAPTER')
        cases={'font_options_v2::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(latest.TEST))}|latest.AFFECTED
        c.require(len(passed['steps'])==1,'ONE_CARGO_RUN_ONLY');step=passed['steps'][0]
        c.require(len(cases)==32 and len(step['tests'])==32 and {n for n,status in step['tests']if status=='ok'}==cases
            and step['diagnostics']==[]and step['bounded_output_observation']['safe_warning_locations']==[],'EXACT_NEW28_AFFECTED4_PASS_NO_WARNINGS')
        job=step['owned_job'];account=job['last_job_accounting']
        c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']and account['active_processes']==0,'OWNED_JOB_TERMINAL_EMPTY_CLOSED')
        c.require(passed['elapsed_seconds']==150.563 and step['elapsed_seconds']==49.891 and account['job_cpu_seconds']==47.766
            and account['peak_job_private_mib']==1874.33 and passed['system_CPU_max']==31.76 and 46.7796<passed['available_RAM_min_percent']<46.7798,'EXACT_UNHIDDEN_RUNTIME_RESOURCES')
        old_docs={p['path']:p for p in docs['source_pins']};text=q.text('CURRENT_STATE.md');marker='> 2026-10-21 P09 ACTIVE 최신 폰트 원본 서식 필터'
        c.require(text.startswith('> 2026-10-21 P09 ACTIVE 최신 폰트 필터와 미리보기 제품 준비')and text.count(marker)==1,'ONE_CURRENT_OPTIONS_PREFIX')
        prefix=text[:text.index(marker)];audit.inverse(text[text.index(marker):],old_docs['CURRENT_STATE.md'],'ALL_PRIOR_CURRENT_STATE_HISTORY_PRESERVED')
        for marker in ('32pass','774fresh/final774','미리보기','PreviewOnly','31.76%','공식158/249','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in prefix,'CURRENT_PREFIX_CORRECT_STORED_PRODUCT_ONLY_SCOPE_AND_PHASE_BOUNDARIES')
        sections=[]
        for path in (REPORT,PROGRESS):
            text=q.text(path);start=text.index('## 폰트 필터와 미리보기의 저장 및 제품 준비\n');end=text.index('## 원본 서식 조건으로 선택한 폰트 대체\n',start);section=text[start:end]
            sections.append((path,section));restored=text[:start]+text[end:]
            if path==PROGRESS:c.require(text.count(NEW_ROW)==1,'ONLY_SEARCH024_ADVANCED');restored=restored.replace(NEW_ROW,OLD_ROW)
            audit.inverse(restored,old_docs[path],'ALL_OTHER_SEARCH_ROWS_PROGRESS_AND_FAILURE_HISTORY_PRESERVED')
            for marker in ('32pass','774fresh/final774','150.563초','49.891초','47.766초','1874.33MiB','31.76%','46.7797%','preview','P09/A12/A13 OPEN'):
                c.require(marker in section,'CURRENT_OPTIONS_SCOPE_AND_RESOURCES_EXACT')
        text=q.text(SOURCE_CONTRACT);c.require(text.count(AFTER)==1 and text.count(NEW_REMAINS)==1,'TWO_PRECISE_SOURCE_CONTRACT_PROGRESS_UPDATES')
        audit.inverse(text.replace(AFTER,BEFORE).replace(NEW_REMAINS,OLD_REMAINS),old_docs[SOURCE_CONTRACT],'ALL_OTHER_SOURCE_FILTER_CONTRACT_BYTES_PRESERVED');sections.append((SOURCE_CONTRACT,text))
        text=q.text(PROFILE);sections.append((PROFILE,text));q.pin(DRIVER)
        for marker in ('SourceReviewStyleFilter','PreparedStoredFontPreview','PreviewOnly','candidate_output_retained','16KiB','64KiB','774fresh/final774','마지막 head 경합6개','Native011 미승인/미실행'):
            c.require(marker in text,'OPTIONS_CONTRACT_EXPLICIT_PREVIEW_AUTHORITY_AND_UNQUALIFIED_COMMON_EXECUTION_BOUNDARY')
        for path,section in sections:
            for target in re.findall(r'\]\(([^)]+)\)',section):
                p=(c.ROOT/path).parent/target;c.require(p.resolve().is_relative_to(c.ROOT.resolve())and p.is_file(),'CURRENT_LOCAL_EVIDENCE_AND_CONTRACT_LINK_EXISTS')
        q.finish();guard.check(force=True);row.update(state='PASS_FONT_OPTIONS_STORED_PRODUCT_PREVIEW28_AFFECTED4_DOC_SYNC_NOT_COMMON_EXECUTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases=28,affected_v1_cases=4,official_queue_accepted=158,official_queue_total=249,next_work='common_v2_font_candidate_and_explicit_nonmutating_preview_dispatch')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_OPTIONS_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
