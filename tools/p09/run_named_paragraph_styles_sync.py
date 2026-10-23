"""342: docs-only source named-style19 + affected7 coverage, exact failures and empty-shape semantics."""
import json,re,time
from types import SimpleNamespace as NS
import run_named_paragraph_styles_empty_recovery as latest
base=latest.base
shared,c,a,tools,compact,audit=latest.shared,latest.c,latest.a,latest.tools,latest.compact,latest.audit
OUTPUT='implementation/p09/evidence/p09-361-named-paragraph-styles-sync342.v1.json';DRIVER='tools/p09/run_named_paragraph_styles_sync.py'
BASE='implementation/p09/evidence/p09-361-compiled-font-options-sync336.v1.json'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md';REPORT='implementation/p09/P09_NAMED_STYLE_REPLACEMENT_PROGRESS.md';PROFILE='protocol/migrations/p09-named-paragraph-style-source-v1.md'
OLD_ROW='| SEARCH-025 | 스타일 일괄 대체 | 실제 스타일 관계·범위·보존 검증 필요 |'
NEW_ROW='| SEARCH-025 | 스타일 일괄 대체 | 문단 스타일 이름→원본 styleIDRef 신규19+영향7 고유26개 검증, 문자 스타일/필터·저장/제품/preview·실제 적용/실행/target 미완료 |'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NAMED_PARAGRAPH_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NAMED_PARAGRAPH_SYNC',own_cpu_selection=selection,tests_build_DB_or_Hangul_replayed=False,
        document_and_changed_source_audit_not_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT));repair=compact.unpack(q.json(latest.previous.OUTPUT));mixed=compact.unpack(q.json(latest.previous.previous.OUTPUT));docs=q.json(BASE)
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='93794d7832e36c503c2ff59dccfa1a18286ae1d3a8e824b88a1a308822bde63d'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==793 and passed['executed_cases']==1 and passed['retained_cases']==25,'EXACT341_ONE_RECOVERED25_RETAINED_CURRENT_CLOSURE')
        c.require(q.snapshots[latest.previous.OUTPUT]['sha256']=='ed2f436f2e1a95cf9d945fca9b7984a0ce2c06cd1997d5b3ae210b035dc0a49b'and repair['cleanup']and repair['fresh_inputs']==repair['final_fresh_hashes']==791,'EXACT340_TWO_PASS_ONE_FAILED_EXPECTATION_RETAINED')
        c.require(q.snapshots[latest.previous.previous.OUTPUT]['sha256']=='a395c5cf0cba82bca54e801c640f18b809a75cab0c2f9a65c4e385d4fd3667e8'and mixed['cleanup']and mixed['fresh_inputs']==mixed['final_fresh_hashes']==789,'EXACT339_23_PASS_THREE_FAILURES_RETAINED')
        compile_failed=compact.unpack(q.json(latest.previous.previous.previous.OUTPUT));scope_failed=compact.unpack(q.json(base.OUTPUT))
        c.require(q.snapshots[latest.previous.previous.previous.OUTPUT]['sha256']=='782c42f5c6b4347e45882a32fe0b9a0c1154f106004ed56218ffcee5191d08b5'and compile_failed['cleanup']
            and compile_failed['steps'][0]['tests']==[]and compile_failed['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0425','E0433'],'EXACT338_COMPILE_ONLY_REGEX_NAMESPACE_FAILURE_RETAINED')
        c.require(q.snapshots[base.OUTPUT]['sha256']=='ac2f7e9921e914169c4ea535df0a438166567b72b9fa552dbc54384893b41fb9'and scope_failed['cleanup']and scope_failed['steps']==[],'EXACT337_BEFORE_CARGO_SCOPE_FAILURE_RETAINED')
        c.require(q.snapshots[BASE]['sha256']=='758b9201a9a8b3ca36c2dbbd6be671f7a62046c0cb41146c691fb90862d2f9d6'and docs['cleanup'],'EXACT336_PRIOR_DOC_BASELINE')
        old={p['path']:p for p in passed['source_pins']};source={base.CORE,base.NAMED,base.PARENT,base.TEST,base.DRIVER,latest.DRIVER,latest.previous.DRIVER,latest.previous.previous.DRIVER,latest.previous.previous.previous.DRIVER,
            base.CORE[:-3]+'/verify.rs','crates/hwpx-package/src/text_flow.rs','crates/hwpx-package/src/document_import/search/extract.rs','crates/hwpx-package/src/document_import/fields/semantics/catalog.rs'}
        for n in sorted(source):q.pin(n);c.require(q.snapshots[n]==old[n],'CURRENT_SOURCE_COMPILER_READER_GUARDS_NAMED_QUERY_TESTS_AND_RUNNERS_MATCH341')
        original=compact.unpack(q.json(base.previous.OUTPUT));supplement=q.json(latest.previous.previous.previous.SUPPLEMENT)
        original_pins={p['path']:p for p in original['source_pins']};historical={p['path']:p for p in supplement['source_pins']};original_pins[base.PARENT]=historical[base.PARENT];base.inverse(q,original_pins)
        text=q.text(base.TEST);c.require(text.count(latest.AFTER)==1,'ONE_EXPANDED_EMPTY_RUN_OPEN_TEXT_SELF_CLOSING_TEXT_POSITIVE_AND_RUNLESS_NEGATIVE')
        restored=text.replace(latest.AFTER,latest.BEFORE);repair_pins={p['path']:p for p in repair['source_pins']};audit.inverse(restored,repair_pins[base.TEST],'ALL25_PASSED_TEST_BODIES_UNCHANGED')
        for before,after in((latest.previous.OLD_EMPTY,latest.previous.NEW_EMPTY),(latest.previous.OLD_SELECTION,latest.previous.NEW_SELECTION),(latest.previous.OLD_CONTROL,latest.previous.NEW_CONTROL)):
            c.require(restored.count(after)==1,'ONLY_THREE_INITIAL_FAILED_FIXTURE_REPAIRS');restored=restored.replace(after,before)
        mixed_pins={p['path']:p for p in mixed['source_pins']};audit.inverse(restored,mixed_pins[base.TEST],'ALL_ORIGINAL23_PASSES_AND_ALL_OTHER_INITIAL_ASSERTIONS_UNCHANGED')
        current={'named::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}|base.AFFECTED
        first={n for n,status in mixed['steps'][0]['tests']if status=='ok'};second={n for n,status in repair['steps'][0]['tests']if status=='ok'};last={n for n,status in passed['steps'][0]['tests']if status=='ok'}
        c.require(len(current)==26 and len(first)==23 and len(second)==2 and last=={latest.CASE}and current==first|second|last
            and not first&second and not first&last and not second&last,'EXACT_CURRENT26_UNIQUE19_NEW7_AFFECTED_NOT_ONE26_TEST_REPLAY')
        for result in(compile_failed,mixed,repair,passed):
            s=result['steps'][0];job=s['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0,'ALL_OWNED_JOBS_TERMINAL_EMPTY_CLOSED')
        s=passed['steps'][0];account=s['owned_job']['last_job_accounting']
        c.require(passed['elapsed_seconds']==106.766 and s['elapsed_seconds']==3.516 and account['job_cpu_seconds']==2.25 and account['peak_job_private_mib']==586.83
            and passed['system_CPU_max']==12.43 and 45.1305<passed['available_RAM_min_percent']<45.1307 and mixed['system_CPU_max']==55.25,'EXACT_LAST_RECOVERY_AND_UNHIDDEN_EARLIER_SYSTEM_PEAK')
        old_docs={p['path']:p for p in docs['source_pins']};state=q.text('CURRENT_STATE.md');marker='> 2026-10-21 P09 ACTIVE 최신 폰트 v2 공통 계획과 비변경 미리보기'
        c.require(state.startswith('> 2026-10-21 P09 ACTIVE 최신 문단 스타일 이름 일괄 참조 대체')and state.count(marker)==1,'ONE_CURRENT_NAMED_STYLE_PREFIX')
        prefix=state[:state.index(marker)];audit.inverse(state[state.index(marker):],old_docs['CURRENT_STATE.md'],'ALL_PRIOR_CURRENT_STATE_HISTORY_PRESERVED')
        for marker in('고유26개','793fresh/final793','단일26개','55.25%','12.43%','공식158/249','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in prefix,'CURRENT_PREFIX_SCOPE_FAILURES_RESOURCES_AND_PHASE_BOUNDARIES_EXACT')
        progress=q.text(PROGRESS);start=progress.index('## 문단 스타일 이름을 사용하는 원본 참조 대체\n');end=progress.index('## 폰트 v2 공통 계획과 비변경 미리보기\n',start);section=progress[start:end]
        c.require(progress.count(NEW_ROW)==1,'ONLY_SEARCH025_ADVANCED');audit.inverse((progress[:start]+progress[end:]).replace(NEW_ROW,OLD_ROW),old_docs[PROGRESS],'ALL_OTHER18_SEARCH_ROWS_AND_PROGRESS_HISTORY_PRESERVED')
        report=q.text(REPORT);profile=q.text(PROFILE);q.pin(DRIVER)
        for document in(section,report,profile):
            for marker in('고유26개','793fresh/final793','styleIDRef','문자 스타일','preview','P09/A12/A13 OPEN'):c.require(marker in document,'NAMED_STYLE_CORE_ONLY_SCOPE_AND_GATE_BOUNDARIES')
        for marker in('337','338','339','340','341','23pass/3fail','2pass/1fail','::regex','55.25%','586.83MiB'):
            c.require(marker in prefix+report,'ALL_ORIGINAL_FAILURE_AND_RESOURCE_HISTORY_RETAINED')
        for path,document in((PROGRESS,section),(REPORT,report),(PROFILE,profile)):
            for target in re.findall(r'\]\(([^)]+)\)',document):
                p=(c.ROOT/path).parent/target;c.require(p.resolve().is_relative_to(c.ROOT.resolve())and p.is_file(),'CURRENT_LOCAL_EVIDENCE_AND_CONTRACT_LINK_EXISTS')
        q.finish();guard.check(force=True);row.update(state='PASS_NAMED_PARAGRAPH_SOURCE19_AFFECTED7_CURRENT_DOC_SYNC_NOT_FULL_SEARCH025_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_named_cases=19,affected_original_cases=7,distinct_current_cases=26,latest_executed_cases=1,retained_cases=25,official_queue_accepted=158,official_queue_total=249,
            next_work='named_style_current_stored_product_preview_and_character_style_support')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'NAMED_PARAGRAPH_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
