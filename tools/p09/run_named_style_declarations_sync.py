"""356: declaration-only current docs, original354 failure and15 retained passes; no test replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_named_style_declarations_recovery as latest
base=latest.base
shared,c,a,tools,compact,harness,audit=latest.shared,latest.c,latest.a,latest.tools,latest.compact,latest.harness,latest.audit
OUTPUT='implementation/p09/evidence/p09-361-named-style-declarations-sync356.v1.json';DRIVER='tools/p09/run_named_style_declarations_sync.py'
BASE_DOC='implementation/p09/evidence/p09-361-named-style-options-sync353.v1.json'
STATE='CURRENT_STATE.md';PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md';REPORT='implementation/p09/P09_NAMED_STYLE_REPLACEMENT_PROGRESS.md'
PROFILE='protocol/migrations/p09-named-style-declaration-resolution-v1.md'
OLD_ROW='| SEARCH-025 | 스타일 일괄 대체 | 문단 이름/필터 core·현재 저장/엄격한 v2/preview 신규28+영향4·공통22계열 신규18+영향9 원 결과 대조, 문자 스타일/전체 옵션·실제 적용/실행/저장/target 미완료 |'
NEW_ROW='| SEARCH-025 | 스타일 일괄 대체 | 문단 이름/필터 v2 제품·공통22계열 및 PARA/CHAR 원본 선언 고유19+기존 catalog3 검증, 문자 스타일 본문 결속/전체 옵션·실제 적용/실행/저장/target 미완료 |'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NAMED_DECLARATIONS_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NAMED_DECLARATIONS_SYNC',own_cpu_selection=selection,Cargo_tests_DB_or_Native_replayed=False,
        document_and_changed_source_audit_not_fresh_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False,
        body_occurrences_or_target_semantics_qualified=False,character_style_capture_authorized=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT));failed=compact.unpack(q.json(base.OUTPUT));docs=q.json(BASE_DOC)
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='805f9edd4cbd317522faa1cd7ce57458ac851dc8931a988ef66f4345cb8f8b92'and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==832
            and passed['distinct_current_declaration_cases']==19 and passed['retained_declaration_cases']==15,'EXACT355_RECOVERED_CURRENT19_AND_CATALOG3')
        c.require(q.snapshots[base.OUTPUT]['sha256']=='a36c0016568d8f350e1d465fbbf679a0b89d529c45ac35e36fe11a70c144bb37'and failed['cleanup']and failed['fresh_inputs']==failed['final_fresh_hashes']==830,'EXACT354_RESPONSE_LIMIT_FAILURE_RETAINED')
        c.require(q.snapshots[BASE_DOC]['sha256']=='55777c569a6e88cdbbb57d5f978b867f0bd24915d991a9742f071a6ae7d6b266'and docs['cleanup'],'EXACT353_PRIOR_DOC_BASELINE')
        old={p['path']:p for p in passed['source_pins']};sources=base.NEW|{base.PARENT,base.OLD_TEST,latest.DRIVER,base.RUNTIME}|base.REFERENCES|{
            'crates/hwpx-package/src/character_style.rs','crates/hwpx-package/src/id_index.rs','crates/hwpx-package/src/document_import/search/replacement/atoms/styles/paragraphs/named.rs'}
        for path in sorted(sources):q.pin(path);c.require(q.snapshots[path]==old[path],'CURRENT_DECLARATIONS_RESOURCE_READERS_ID_RULES_TESTS_AND_RUNTIME_MATCH355')
        latest.inverse(q,{p['path']:p for p in failed['source_pins']})
        original=compact.unpack(q.json(base.BASE));base.inverse(q,{p['path']:p for p in original['source_pins']})
        tests=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(base.TEST)));old_pass={n for n,s in failed['steps'][0]['tests']if s=='ok'};current_cases={latest.FAILED,latest.NEW_CASE}|latest.AFFECTED
        tools.good_step(passed['steps'][0],current_cases);tools.good_step(passed['steps'][1],base.AFFECTED)
        c.require(len(tests)==19 and len(old_pass)==17 and len(old_pass-current_cases)==15 and tests==(old_pass-current_cases)|current_cases,'EXACT_CURRENT19_FROM_RETAINED15_AND_CURRENT4_NOT_ONE19_REPLAY')
        for result in(failed,passed):
            for step in result['steps']:
                job=step['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0,'ALL_ORIGINAL_JOBS_EMPTY_CLOSED')
        c.require(passed['elapsed_seconds']==140.265 and passed['system_CPU_max']==24.43 and 37.4163<passed['available_RAM_min_percent']<37.4164
            and max(s['owned_job']['last_job_accounting']['peak_job_private_mib']for s in passed['steps'])==1884.47,'EXACT355_RESOURCE_SCOPE')
        old_docs={p['path']:p for p in docs['source_pins']};state=q.text(STATE);marker='> 2026-10-21 P09 ACTIVE 최신 문단 스타일 필터의 제품과 공통 계획'
        c.require(state.count(marker)==1 and state.startswith('> 2026-10-21 P09 ACTIVE 최신 문단과 문자 스타일 선언 해석'),'ONE_CURRENT_DECLARATION_ONLY_PREFIX')
        prefix=state[:state.index(marker)];audit.inverse(state[state.index(marker):],old_docs[STATE],'ALL_PRIOR_STATE_FAILURE_AND_PRODUCT_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 원본 문단과 문자 스타일 선언의 이름 해석\n');end=progress.index('## 문단 스타일 필터의 제품과 공통 계획\n',start);section=progress[start:end]
        c.require(progress.count(NEW_ROW)==1,'ONLY_SEARCH025_ROW_ADVANCED');audit.inverse((progress[:start]+progress[end:]).replace(NEW_ROW,OLD_ROW),old_docs[PROGRESS],'ALL_OTHER18_SEARCH_ROWS_AND_PRIOR_PROGRESS_PRESERVED')
        report=q.text(REPORT);start=report.index('## 문단과 문자 스타일의 원본 선언과 자원 해석\n');end=report.index('## 선택적 서식 필터의 저장과 제품 및 공통 계획\n',start);report_section=report[start:end]
        audit.inverse(report[:start]+report[end:],old_docs[REPORT],'ALL_PRIOR_CORE_PRODUCT_IMPORT_AND_POSTCHECK_FAILURE_HISTORY_PRESERVED')
        profile=q.text(PROFILE);q.pin(DRIVER)
        for document in(prefix,section,report_section,profile):
            for marker in('354','355','832fresh/final832','공식158/249','P09/A12/A13 OPEN','Native011 미승인/미실행','문자 스타일'):
                c.require(marker in document,'DECLARATION_ONLY_SCOPE_RESOURCES_AND_PHASE_BOUNDARIES_EXACT')
        for marker in('고유19개','단일19개','1884.47MiB','24.43%','4MiB','본문','승인'):
            c.require(marker in prefix+section+report_section,'RETAINED_RESULTS_FINITE_BUDGET_AND_UNQUALIFIED_CAPTURE_BOUNDARIES')
        for marker in('SourceNamedStyleNameQuery','nextStyle','body_occurrences_or_target_semantics_qualified','current_access_execution_or_publication_authority','한글 2020 글자 스타일 도움말','StyleType.cpp'):
            c.require(marker in profile,'DECLARATION_RESOURCE_SEPARATION_AND_PRIMARY_SOURCE_SCOPE')
        allowed_hosts=('https://raw.githubusercontent.com/hancom-io/','https://help.hancom.com/','https://tech.hancom.com/')
        for path,document in((PROGRESS,section),(REPORT,report_section),(PROFILE,profile)):
            for target in re.findall(r'\]\(([^)]+)\)',document):
                if target.startswith('https://'):c.require(target.startswith(allowed_hosts),'ONLY_PRIMARY_OFFICIAL_WEB_REFERENCES');continue
                p=((c.ROOT/path).parent/target).resolve();c.require(p.is_relative_to(c.ROOT.resolve())and p.is_file(),'LOCAL_DECLARATION_EVIDENCE_AND_CONTRACT_LINK_EXISTS')
        q.finish();guard.check(force=True);row.update(state='PASS_NAMED_DECLARATION19_CATALOG3_CURRENT_DOC_SYNC_NOT_CHARACTER_BODY_BINDING_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            distinct_declaration_cases=19,original_catalog_cases=3,latest_executed_declaration_cases=4,retained_declaration_cases=15,mutation_families=22,official_queue_accepted=158,official_queue_total=249,
            next_work='qualified_character_style_before_after_sources_or_approved_capture_then_exact_body_binding')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'NAMED_DECLARATIONS_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
