"""330: preserve actual unsafe witnesses, bind fixed20 + retained source4, docs-only closure."""
import json,re,time
from types import SimpleNamespace as NS
import run_font_tracking_recovery as latest
shared,c,a,tools,compact,audit=latest.shared,latest.c,latest.a,latest.tools,latest.compact,latest.audit
OUTPUT='implementation/p09/evidence/p09-361-font-tracking-sync330.v1.json';DRIVER='tools/p09/run_font_tracking_sync.py'
BASE='implementation/p09/evidence/p09-361-compiled-font-sync325.v1.json'
REPORT='implementation/p09/P09_FONT_REFERENCE_REPLACEMENT_PROGRESS.md';PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
CONTRACT='protocol/migrations/p09-scoped-font-name-replacement-v1.md';PROFILE='protocol/migrations/p09-font-review-tracking-guard-v1.md'
OLD_ROW='| SEARCH-024 | 폰트 일괄 대체 | 원본/저장/제품·실제 헤더/본문 inventory와 공통 준비/계획 신규 폰트16+영향 기존4pass, review/field/protection 조합·전체 옵션·실제 유효 폰트/fallback·실행/저장/target 미완료 |'
NEW_ROW='| SEARCH-024 | 폰트 일괄 대체 | 원본/저장/제품·공통 준비/계획과 review/field/관측 보호 대표 고유24개, 상위 추적 표시 누락 수정, style_filter/preview_only·전체 유효 서식/폰트/fallback·실행/저장/target 미완료 |'
BEFORE='같은 원본 객체의 whole-source reconstruction, 원 필드/리뷰/색인과 보호·field cache·tracking 거부를 유지한다.\n'
AFTER='''같은 원본 객체의 whole-source reconstruction, 원 필드/리뷰/색인과 관측 보호·field cache 거부를 유지한다.
후속 [관측 추적 표시 guard](p09-font-review-tracking-guard-v1.md)는 상위 run/문단 표시가 선택된 text에
전파되지 않던 누락을 수정한다. 관측한 charTcId/paraTcId의 ID0도 표시이며 전체 보호 의미를 대신하지 않는다.
'''

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FONT_TRACKING_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_TRACKING_SYNC',own_cpu_selection=selection,tests_build_DB_or_Hangul_replayed=False,
        document_and_changed_source_audit_not_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT));failed=compact.unpack(q.json(latest.previous.OUTPUT));docs=q.json(BASE)
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='dacb11c37cd9280830b6b78c89092ec9ddf65f0290e3afea0d462019461fadf5'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==765 and passed['executed_cases']==20 and passed['retained_source_cases']==4,'EXACT329_FIXED20_CURRENT_SOURCE_CLOSURE')
        c.require(q.snapshots[latest.previous.OUTPUT]['sha256']=='13cf6b199291c354c8a5d5bf4638af7bc953e661c8dd37353f1999561d033a7c'and failed['cleanup']
            and failed['state']=='FAILED_FONT_ANCESTOR_TRACKING_THREE_UNEXPECTED_ACCEPTANCES_CONFIRMED'and failed['fresh_inputs']==failed['final_fresh_hashes']==763
            and failed['unexpected_tracking_acceptances']==3 and failed['source_admission_passes']==4,'EXACT328_REAL_UNSAFE_CANDIDATES_REMAIN_FAILED')
        original={p['path']:p for p in failed['source_pins']};old={p['path']:p for p in passed['source_pins']};source={latest.CORE,latest.TEST,latest.DRIVER,latest.previous.DRIVER,
            latest.previous.previous.DRIVER,latest.previous.previous.previous.DRIVER,latest.previous.previous.previous.PARENT,latest.previous.previous.previous.FIXTURE}|latest.previous.previous.FIXTURES
        for n in sorted(source):q.pin(n);c.require(q.snapshots[n]==old[n],'CURRENT_SCOPED_GUARD_ALL_TESTS_FIXTURES_AND_RUNNERS_MATCH329')
        latest.inverse(q,original)
        all_cases={'font_review_v1::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(latest.TEST))};retained={'font_review_v1::'+n for n in latest.previous.SOURCE};recovered={'font_review_v1::'+n for n in latest.previous.TRACKING}
        s=passed['steps'][0];before=failed['steps'][0]
        c.require(len(all_cases)==24 and len(s['tests'])==20 and {n for n,status in s['tests']if status=='ok'}==all_cases-retained and s['diagnostics']==[]
            and {n for n,status in before['tests']if status=='ok'}==retained and {n for n,status in before['tests']if status!='ok'}==recovered
            and before['bounded_output_observation']['unexpected_tracking_candidate_acceptance_witnesses']==3
            and s['bounded_output_observation']['unexpected_tracking_candidate_acceptance_witnesses']==0,'EXACT24_CURRENT_IDENTITIES_THREE_ACCEPTANCES_FIXED_AND_FOUR_PRE_IMPORT_DENIALS_RETAINED')
        for r in (failed,passed):
            j=r['steps'][0]['owned_job'];c.require(j['owned_tree_empty']and j['cleanup_confirmed']and j['job_handle_closed']and j['last_job_accounting']['active_processes']==0,'ALL_DIAGNOSTIC_AND_RECOVERY_JOBS_TERMINAL_EMPTY_CLOSED')
        j=s['owned_job']['last_job_accounting'];c.require(passed['elapsed_seconds']==143.11 and s['elapsed_seconds']==44.406 and j['job_cpu_seconds']==42.547 and j['peak_job_private_mib']==1860.77
            and passed['system_CPU_max']==70.9 and 37.5716<passed['available_RAM_min_percent']<37.5718,'EXACT_UNHIDDEN_WHOLE_SYSTEM_PEAK_AND_OWNED_JOB_RESOURCES')
        c.require(q.snapshots[BASE]['sha256']=='db2a1d9433cbfb7d815322d8203099fb618ccccd03522de1eb6f99ec7dc6b34c'and docs['cleanup'],'EXACT325_PREVIOUS_DOC_BASELINE')
        old_docs={p['path']:p for p in docs['source_pins']};text=q.text('CURRENT_STATE.md');marker='> 2026-10-21 P09 ACTIVE 최신 폰트 공통 준비와 계획'
        c.require(text.startswith('> 2026-10-21 P09 ACTIVE 최신 폰트 review와 상위 추적 표시 보호')and text.count(marker)==1,'ONE_CURRENT_FONT_TRACKING_PREFIX')
        prefix=text[:text.index(marker)];audit.inverse(text[text.index(marker):],old_docs['CURRENT_STATE.md'],'ALL_PRIOR_CURRENT_STATE_HISTORY_PRESERVED')
        for marker in ('765fresh/final765','대표 고유24개','763fresh/final763','FAILED 원본','70.90%','공식158/249','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in prefix,'CURRENT_PREFIX_CORRECT_FAILURES_SCOPE_RESOURCES_AND_PHASE_BOUNDARIES')
        sections=[]
        for path in (REPORT,PROGRESS):
            text=q.text(path);start=text.index('## 메모와 필드 및 추적 변경 보호\n');end=text.index('## 폰트 공통 준비와 계획 컴파일러\n',start);section=text[start:end];sections.append((path,section));restored=text[:start]+text[end:]
            if path==PROGRESS:c.require(text.count(NEW_ROW)==1,'ONLY_SEARCH024_ADVANCED');restored=restored.replace(NEW_ROW,OLD_ROW)
            audit.inverse(restored,old_docs[path],'ALL_OTHER_SEARCH_ROWS_PROGRESS_AND_FAILURE_HISTORY_PRESERVED')
            for marker in ('20pass','765fresh/final765','고유24개','143.11초','44.406초','7.22초','1860.77MiB','70.90%','37.5717%','P09/A12/A13 OPEN'):
                c.require(marker in section,'CURRENT_REVIEW_TRACKING_SCOPE_AND_RESOURCE_VALUES_EXACT')
        text=q.text(CONTRACT);c.require(text.count(AFTER)==1,'ONE_PRECISE_OBSERVED_ANCESTOR_GUARD_BOUNDARY_UPDATE')
        audit.inverse(text.replace(AFTER,BEFORE),dict(path=CONTRACT,bytes=4812,sha256='da2427ffc2a8d1d36b0718935ee1d70bc0f64cd4d7d3d8b10d52f3afd60aee00'),'ALL_PRIOR_SOURCE_FONT_CONTRACTS_MATCH_PRE_EDIT_BYTES');sections.append((CONTRACT,text))
        text=q.text(PROFILE);sections.append((PROFILE,text));q.pin(DRIVER)
        for marker in ('charTcId','paraTcId','ID0/1','763fresh/final763','765fresh/final765','대표 고유24개','style_filter/preview_only','전체 보호 의미'):
            c.require(marker in text,'EXPLICIT_TRACKING_OBSERVATION_SOURCE_REJECTION_AND_UNQUALIFIED_FULL_PRODUCT_BOUNDARY')
        for path,section in sections:
            for target in re.findall(r'\]\(([^)]+)\)',section):
                p=(c.ROOT/path).parent/target;c.require(p.resolve().is_relative_to(c.ROOT.resolve())and p.is_file(),'CURRENT_LOCAL_EVIDENCE_AND_CONTRACT_LINK_EXISTS')
        q.finish();guard.check(force=True);row.update(state='PASS_FONT_OBSERVED_ANCESTOR_TRACKING_FIXED20_RETAINED_SOURCE4_CURRENT_DOC_SYNC_NOT_FULL_OPTIONS_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            executed_review_cases=20,retained_source_cases=4,distinct_review_cases=24,official_queue_accepted=158,official_queue_total=249,next_work='font_style_filter_preview_and_remaining_qualified_execution_storage')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_TRACKING_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','distinct_review_cases')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
