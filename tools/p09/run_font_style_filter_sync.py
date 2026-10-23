"""332: docs-only audit of filtered-font core evidence, original histories and phase boundaries."""
import json,re,time
from types import SimpleNamespace as NS
import run_font_style_filter as latest
shared,c,a,tools,compact,audit=latest.shared,latest.c,latest.a,latest.tools,latest.compact,latest.audit
OUTPUT='implementation/p09/evidence/p09-361-font-style-filter-sync332.v1.json';DRIVER='tools/p09/run_font_style_filter_sync.py'
BASE='implementation/p09/evidence/p09-361-font-tracking-sync330.v1.json'
REPORT='implementation/p09/P09_FONT_REFERENCE_REPLACEMENT_PROGRESS.md';PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
PROFILE='protocol/migrations/p09-filtered-font-source-v1.md'
OLD_ROW='| SEARCH-024 | 폰트 일괄 대체 | 원본/저장/제품·공통 준비/계획과 review/field/관측 보호 대표 고유24개, 상위 추적 표시 누락 수정, style_filter/preview_only·전체 유효 서식/폰트/fallback·실행/저장/target 미완료 |'
NEW_ROW='| SEARCH-024 | 폰트 일괄 대체 | 원본/저장/제품·공통 준비/계획·관측 보호와 별도 원본 서식 필터 신규18+영향6개 검증, 필터 저장/제품·preview_only·전체 유효 서식/폰트/fallback·실행/저장/target 미완료 |'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FONT_FILTER_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_FILTER_SYNC',own_cpu_selection=selection,tests_build_DB_or_Hangul_replayed=False,
        document_and_changed_source_audit_not_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT));docs=q.json(BASE)
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='1f9a46abf434fd5bcccae9d246f1861afb652e98ff6c6419bbde996357b08cfd'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==769 and passed['new_cases']==18 and passed['affected_cases']==6,'EXACT331_SOURCE_FILTER24_CURRENT_INPUT_CLOSURE')
        c.require(q.snapshots[BASE]['sha256']=='187880ec07701a466f917adaab43b8e08de17fd364c590e8d20a7e0588f8aadb'and docs['cleanup'],'EXACT330_PRIOR_DOC_BASELINE')
        old={p['path']:p for p in passed['source_pins']};source={latest.CORE,latest.FILTER,latest.PARENT,latest.TEST,latest.DRIVER,
            'crates/hwpx-package/src/document_import/search/inspection.rs','crates/hwpx-package/src/document_import/search/inspection/definitions.rs',
            'crates/hwpx-package/src/document_import/search/reviews/selector/styles.rs'}
        for n in sorted(source):q.pin(n);c.require(q.snapshots[n]==old[n],'CURRENT_FILTER_CORE_V1_SHARED_PATH_TESTS_AND_FILTER_PREDICATES_MATCH331')
        cases={'filtered::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(latest.TEST))}|{'scoped::'+n for n in latest.AFFECTED}
        c.require(len(passed['steps'])==1,'ONE_CARGO_RUN_ONLY');step=passed['steps'][0]
        c.require(len(cases)==24 and len(step['tests'])==24 and {n for n,status in step['tests']if status=='ok'}==cases
            and step['diagnostics']==[]and step['bounded_output_observation']['safe_warning_locations']==[],'EXACT_NEW18_AND_AFFECTED6_PASS_NO_WARNINGS')
        job=step['owned_job'];account=job['last_job_accounting']
        c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']and account['active_processes']==0,'OWNED_JOB_TERMINAL_EMPTY_CLOSED')
        c.require(passed['elapsed_seconds']==133.719 and step['elapsed_seconds']==33.875 and account['job_cpu_seconds']==32.25
            and account['peak_job_private_mib']==1855.82 and passed['system_CPU_max']==35.55 and 35.8527<passed['available_RAM_min_percent']<35.8528,'EXACT_UNHIDDEN_RUNTIME_RESOURCES')
        old_docs={p['path']:p for p in docs['source_pins']};text=q.text('CURRENT_STATE.md');marker='> 2026-10-21 P09 ACTIVE 최신 폰트 review와 상위 추적 표시 보호'
        c.require(text.startswith('> 2026-10-21 P09 ACTIVE 최신 폰트 원본 서식 필터')and text.count(marker)==1,'ONE_CURRENT_FILTER_PREFIX')
        prefix=text[:text.index(marker)];audit.inverse(text[text.index(marker):],old_docs['CURRENT_STATE.md'],'ALL_PRIOR_CURRENT_STATE_HISTORY_PRESERVED')
        for marker in ('24pass','769fresh/final769','원본 core','preview_only','35.55%','공식158/249','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in prefix,'CURRENT_PREFIX_CORRECT_CORE_ONLY_SCOPE_AND_PHASE_BOUNDARIES')
        sections=[]
        for path in (REPORT,PROGRESS):
            text=q.text(path);start=text.index('## 원본 서식 조건으로 선택한 폰트 대체\n');end=text.index('## 메모와 필드 및 추적 변경 보호\n',start);section=text[start:end]
            sections.append((path,section));restored=text[:start]+text[end:]
            if path==PROGRESS:c.require(text.count(NEW_ROW)==1,'ONLY_SEARCH024_ADVANCED');restored=restored.replace(NEW_ROW,OLD_ROW)
            audit.inverse(restored,old_docs[path],'ALL_OTHER_SEARCH_ROWS_PROGRESS_AND_FAILURE_HISTORY_PRESERVED')
            for marker in ('24pass','769fresh/final769','133.719초','33.875초','32.25초','1855.82MiB','35.55%','35.8527%','preview_only','P09/A12/A13 OPEN'):
                c.require(marker in section,'CURRENT_FILTER_SCOPE_AND_RESOURCES_EXACT')
        text=q.text(PROFILE);sections.append((PROFILE,text));q.pin(DRIVER)
        for marker in ('SourceFontFilteredReplacementCandidate','SourceReviewStyleFilter','U+0344','Selection','원본 segment','현재 저장','preview_only','769fresh/final769','Native011 미승인/미실행'):
            c.require(marker in text,'FILTER_CONTRACT_EXPLICIT_NFC_PROVENANCE_AND_UNQUALIFIED_PRODUCT_BOUNDARY')
        for path,section in sections:
            for target in re.findall(r'\]\(([^)]+)\)',section):
                p=(c.ROOT/path).parent/target;c.require(p.resolve().is_relative_to(c.ROOT.resolve())and p.is_file(),'CURRENT_LOCAL_EVIDENCE_AND_CONTRACT_LINK_EXISTS')
        q.finish();guard.check(force=True);row.update(state='PASS_FONT_STYLE_FILTER_CORE18_AFFECTED6_DOC_SYNC_NOT_STORED_PRODUCT_PREVIEW_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_source_cases=18,affected_source_cases=6,official_queue_accepted=158,official_queue_total=249,next_work='stored_filtered_font_and_strict_product_preview_request')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_FILTER_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
