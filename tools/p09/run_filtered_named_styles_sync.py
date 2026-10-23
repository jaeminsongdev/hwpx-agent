"""349: filtered named source documentation only; preserve all product and failure history."""
import json,re,time
from types import SimpleNamespace as NS
import run_filtered_named_styles as latest
shared,c,a,tools,compact,harness,audit=latest.shared,latest.c,latest.a,latest.tools,latest.compact,latest.harness,latest.audit
OUTPUT='implementation/p09/evidence/p09-361-filtered-named-styles-sync349.v1.json';DRIVER='tools/p09/run_filtered_named_styles_sync.py'
BASE='implementation/p09/evidence/p09-361-compiled-named-styles-sync347.v1.json'
STATE='CURRENT_STATE.md';PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md';REPORT='implementation/p09/P09_NAMED_STYLE_REPLACEMENT_PROGRESS.md'
PROFILE='protocol/migrations/p09-named-paragraph-style-source-v1.md'
OLD_ROW='| SEARCH-025 | 스타일 일괄 대체 | 문단 이름 core26·현재 저장/제품/preview 고유31·공통 준비/계획 신규19+영향12 검증, 문자 스타일/필터/전체 옵션·실제 적용/실행/저장/target 미완료 |'
NEW_ROW='| SEARCH-025 | 스타일 일괄 대체 | 문단 이름 core26·제품/preview31·공통 신규19+영향12·필터 원본 신규18+영향9 검증, 필터 저장/제품/공통·문자 스타일/전체 옵션·실제 적용/실행/저장/target 미완료 |'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FILTERED_NAMED_DOC_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FILTERED_NAMED_DOC_SYNC',own_cpu_selection=selection,tests_build_DB_or_Hangul_replayed=False,
        document_and_changed_source_audit_not_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT));docs=q.json(BASE)
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='75f0ead9d37f20d8e3cffb74353f13f2a02286e4f1374b301a91a121256f5b6d'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==810 and passed['new_cases']==18 and passed['affected_source_cases']==6 and passed['affected_product_cases']==3,'EXACT348_FILTERED_SOURCE18_AFFECTED9')
        c.require(q.snapshots[BASE]['sha256']=='b98f65fddb04d344443566c4e99a593fd1aa488114b1f60c94afba1da710cdf8'and docs['cleanup'],'EXACT347_PRE_FILTER_DOC_BASELINE')
        old={p['path']:p for p in passed['source_pins']};original=compact.unpack(q.json(latest.previous.OUTPUT));old_original={p['path']:p for p in original['source_pins']}
        sources=latest.CHANGED|latest.NEW|{'crates/hwpx-package/src/document_import/search/replacement/atoms/styles/paragraphs.rs',
            'crates/hwpx-package/src/document_import/search/replacement/atoms/styles/paragraphs/verify.rs','crates/hwpx-package/src/document_import/search/inspection.rs',
            'crates/hwpx-package/src/document_import/search/inspection/definitions.rs','crates/hwpx-package/src/document_import/search/reviews/selector.rs',
            'crates/hwpx-package/src/document_import/search.rs',latest.previous.base.PRODUCT,latest.previous.base.STORED,latest.previous.base.TEST}
        for n in sorted(sources):q.pin(n);c.require(q.snapshots[n]==old[n],'CURRENT_FILTER_CACHE_SOURCE_GUARDS_AND_EXISTING_PRODUCT_MATCH348')
        latest.inverse(q,old_original)
        cases={'named::filtered::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(latest.TEST))}
        c.require(len(cases)==18,'EXACT_NEW18_FILTER_SOURCE_CASES');tools.good_step(passed['steps'][0],cases|latest.AFFECTED_SOURCE);tools.good_step(passed['steps'][1],latest.AFFECTED_PRODUCT)
        for step in passed['steps']:
            job=step['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0,'BOTH_OWNED_JOBS_TERMINAL_EMPTY_CLOSED')
        c.require(passed['elapsed_seconds']==179.766 and passed['system_CPU_max']==32.94 and 35.5548<passed['available_RAM_min_percent']<35.5550,'EXACT348_RESOURCE_METADATA')
        c.require([s['elapsed_seconds']for s in passed['steps']]==[34.187,39.016]and max(s['owned_job']['last_job_accounting']['peak_job_private_mib']for s in passed['steps'])==1883.01,'EXACT348_COMMAND_AND_PRIVATE_PEAK')
        old_docs={p['path']:p for p in docs['source_pins']};state=q.text(STATE);marker='> 2026-10-21 P09 ACTIVE 최신 문단 스타일 이름 대체의 제품과 공통 계획'
        c.require(state.count(marker)==1 and state.startswith('> 2026-10-21 P09 ACTIVE 최신 문단 스타일 이름 대체의 원본 서식 필터'),'ONE_CURRENT_FILTER_PREFIX')
        prefix=state[:state.index(marker)];audit.inverse(state[state.index(marker):],old_docs[STATE],'ALL_PRIOR_STATE_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 원본 서식으로 선택한 문단 스타일 이름 대체\n');end=progress.index('## 문단 스타일 이름 대체의 제품과 공통 계획\n',start);section=progress[start:end]
        c.require(progress.count(NEW_ROW)==1,'ONLY_SEARCH025_ROW_ADVANCED');audit.inverse((progress[:start]+progress[end:]).replace(NEW_ROW,OLD_ROW),old_docs[PROGRESS],'ALL_OTHER18_SEARCH_ROWS_AND_PRIOR_PROGRESS_UNCHANGED')
        report=q.text(REPORT);start=report.index('## 원본 서식 필터를 사용하는 문단 이름 대체\n');end=report.index('## 현재 저장과 제품 요청 및 공통 계획\n',start);report_section=report[start:end]
        audit.inverse(report[:start]+report[end:],old_docs[REPORT],'ALL_PRODUCT_COMMON_SOURCE_FAILURE_AND_NATIVE_BOUNDARIES_HISTORY_PRESERVED')
        profile=q.text(PROFILE);start=profile.index('## 원본 서식 필터를 사용하는 별도 후보\n');end=profile.index('## 후보와 검증\n',start);profile_section=profile[start:end]
        audit.inverse(profile[:start]+profile[end:],old_docs[PROFILE],'ORIGINAL_V1_NAME_RESOLUTION_SCOPE_PRESERVATION_AND_PRODUCT_LINK_UNCHANGED')
        q.pin(DRIVER)
        for document in(prefix,section,report_section):
            for marker in('810fresh/final810','32.94%','1883.01MiB','공식158/249','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행','필터','문자 스타일'):
                c.require(marker in document,'CURRENT_FILTER_ONLY_SCOPE_RESOURCES_AND_PHASE_BOUNDARIES_EXACT')
        for marker in('all_indexed_source_units_of_whole_paragraph','SourceReviewStyleFilter','빈 문단','810fresh/final810','저장/제품/preview/공통 연결 자격은 아니다'):
            c.require(marker in profile_section,'FILTER_EXTENT_EMPTY_SOURCE_AND_UNCONNECTED_PRODUCT_BOUNDARY_EXACT')
        for path,document in((PROGRESS,section),(REPORT,report_section),(PROFILE,profile_section)):
            for target in re.findall(r'\]\(([^)]+)\)',document):
                p=((c.ROOT/path).parent/target).resolve();c.require(p.is_relative_to(c.ROOT.resolve())and p.is_file(),'LOCAL_FILTER_EVIDENCE_AND_CONTRACT_LINK_EXISTS')
        q.finish();guard.check(force=True);row.update(state='PASS_FILTERED_NAMED_SOURCE18_AFFECTED9_CURRENT_DOC_SYNC_NOT_FILTERED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=18,affected_source_cases=6,affected_product_cases=3,official_queue_accepted=158,official_queue_total=249,
            next_work='filtered_named_current_stored_product_preview_common_connection_and_character_style_semantics')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FILTERED_NAMED_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
