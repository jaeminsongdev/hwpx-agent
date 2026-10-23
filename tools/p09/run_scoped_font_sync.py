"""314: docs-only closure for retained9 + recovered8 + affected3, no test/build replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_scoped_font_fixture_recovery as latest
shared,c,a,tools,compact,audit=latest.shared,latest.c,latest.a,latest.tools,latest.compact,latest.audit
OUTPUT='implementation/p09/evidence/p09-361-scoped-font-sync314.v1.json';DRIVER='tools/p09/run_scoped_font_sync.py'
BASE='implementation/p09/evidence/p09-361-font-embedding-sync309.v1.json'
REPORT='implementation/p09/P09_FONT_REFERENCE_REPLACEMENT_PROGRESS.md';PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
GLOBAL='protocol/migrations/p09-source-font-reference-replacement-v1.md';PROFILE='protocol/migrations/p09-scoped-font-name-replacement-v1.md'
OLD_ROW='| SEARCH-024 | 폰트 일괄 대체 | 원본 언어별 공유 참조 치환과 바이너리 결속 신규10+영향14=24pass, 이름 검색/선택 범위·실제 유효 폰트·fallback·현재 저장/제품/target 미완료 |'
NEW_ROW='| SEARCH-024 | 폰트 일괄 대체 | 공유 참조/바이너리24와 별도 이름/selector의 run·text 축 고유20pass, review/field/protection 조합·전체 옵션·실제 유효 폰트/fallback·현재 저장/제품/target 미완료 |'
APPEND='''
별도 [이름·선택 범위 후보](p09-scoped-font-name-replacement-v1.md)는 기존 공유 정의를 수정하지 않고
복사본과 선택된 run/text 참조를 연결한다. 이 전역 매핑 API를 selector 지원으로 자동 승격하지 않으며
해당 경로의 현재 저장/전체 제품/Native 자격도 별도로 남는다.
'''

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SCOPED_FONT_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SCOPED_FONT_SYNC',own_cpu_selection=selection,tests_build_DB_or_Hangul_replayed=False,
        document_audit_not_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT));partial=compact.unpack(q.json(latest.previous.OUTPUT));docs=q.json(BASE)
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='3b6fbc89aaacbd2321539d98b1adbe1ad7fb0ed715f0d9ca95dbdcfcc1857fea'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==731 and passed['executed_cases']==11 and passed['retained_passes']==9
            and passed['steps'][0]['diagnostics']==[]and all(s=='ok'for _,s in passed['steps'][0]['tests']),'EXACT313_ELEVEN_SUCCESS_AND_CURRENT_SOURCE_CLOSURE')
        c.require(q.snapshots[latest.previous.OUTPUT]['sha256']=='db4c26c1ea711de5337ce422ffbbbc07e34bc7179ffdef51f3fe81b14a56772d'and partial['cleanup']
            and sum(s=='ok'for _,s in partial['steps'][0]['tests'])==12,'EXACT312_PARTIAL12_PASS8_FAIL_RETAINED')
        old={p['path']:p for p in passed['source_pins']};original={p['path']:p for p in partial['source_pins']}
        source=latest.base.NEW|latest.base.CHANGED|{latest.DRIVER,latest.previous.DRIVER,latest.previous.previous.DRIVER}
        for n in source:
            q.pin(n);c.require(q.snapshots[n]==old[n],'SCOPED_NEW_CODE_AND_TESTS_AND_RUNNERS_UNCHANGED')
            if n!=latest.base.TEST and n in original:c.require(q.snapshots[n]==original[n],'PRODUCTION_CODE_UNCHANGED_FROM312')
        latest.inverse(q,original[latest.base.TEST])
        retained={n for n,s in partial['steps'][0]['tests']if s=='ok'}-{n for n,_ in passed['steps'][0]['tests']}
        all_cases={'scoped::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(latest.base.TEST))}
        c.require(len(retained)==9 and retained|{n for n,_ in passed['steps'][0]['tests']}==all_cases and len(all_cases)==20,'EXACT20_DISTINCT_CURRENT_IDENTITIES_NOT_SINGLE_FULL_RERUN')
        for r in (partial,passed):
            j=r['steps'][0]['owned_job'];c.require(j['owned_tree_empty']and j['cleanup_confirmed']and j['job_handle_closed']and j['last_job_accounting']['active_processes']==0,'ALL_MIXED_AND_RECOVERY_JOBS_TERMINAL_EMPTY_CLOSED')
        c.require(q.snapshots[BASE]['sha256']=='d3a21a1c149da4c45cac22adda8ababf95f2f1b948d31f67f2cd45c5e8716844'and docs['cleanup'],'EXACT309_PREVIOUS_DOCUMENT_BASELINE')
        old_docs={p['path']:p for p in docs['source_pins']}
        text=q.text('CURRENT_STATE.md');marker='> 2026-10-21 P09 ACTIVE 최신 폰트 바이너리 참조 결속'
        c.require(text.startswith('> 2026-10-21 P09 ACTIVE 최신 폰트 이름과 선택 범위 치환')and text.count(marker)==1,'ONE_CURRENT_SCOPED_FONT_PREFIX')
        audit.inverse(text[text.index(marker):],old_docs['CURRENT_STATE.md'],'ALL_PRIOR_CURRENT_STATE_HISTORY_PRESERVED')
        text=q.text(REPORT);start=text.index('## 폰트 이름과 선택 범위 치환\n');end=text.index('## 바이너리 참조 결속과 보존\n',start)
        audit.inverse(text[:start]+text[end:],old_docs[REPORT],'ALL_PRIOR_FONT_FAILURES_AND_COMPONENT_RESULTS_PRESERVED')
        for marker in ('고유20개','731fresh/final731','98.984초','5.203초','583.82MiB','21.80%','43.9516%','제품 코드는312와 동일','P09/A12/A13 OPEN'):
            c.require(marker in text,'REPORT_CURRENT_PARTIAL_AND_RESOURCE_SCOPE_EXACT')
        text=q.text(PROGRESS);start=text.index('이름 query/replacement와 네 selector의 명시적 run/text 축은');end=text.index('별도 font-binary/v10과 현재 패키지 리소스 결속은',start)
        c.require(text.count(NEW_ROW)==1,'ONE_SEARCH024_ROW_ADVANCED')
        audit.inverse((text[:start]+text[end:]).replace(NEW_ROW,OLD_ROW),old_docs[PROGRESS],'OTHER18_SEARCH_ROWS_AND_ALL_PRIOR_PROGRESS_UNCHANGED')
        text=q.text(GLOBAL);c.require(text.endswith(APPEND),'ONE_SEPARATE_SCOPED_CONTRACT_LINK')
        audit.inverse(text[:-len(APPEND)],old_docs[GLOBAL],'ORIGINAL_GLOBAL_MAPPING_CONTRACT_UNCHANGED')
        q.pin(PROFILE);q.pin(DRIVER);text=q.text(PROFILE)
        for marker in ('source-selector-font-replacement/v1','최대128개','1~4096bytes','RunProperty','TextStyle','scoped-font-static/v11','고유20개','실제 폰트와 Native','현재 저장 서비스'):
            c.require(marker in text,'SCOPED_CONTRACT_EXPLICIT_AXIS_LIMITS_AND_UNQUALIFIED_PRODUCT_BOUNDARY')
        q.finish();guard.check(force=True);row.update(state='PASS_SCOPED_FONT_DISTINCT20_CURRENT_DOC_SYNC_NOT_PRODUCT_OR_NATIVE_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            retained_cases=9,current_executed_cases=11,distinct_component_cases=20,official_queue_accepted=158,official_queue_total=249,
            next_work='current_stored_access_and_strict_product_binding_with_remaining_review_field_protection_cases')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'SCOPED_FONT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','distinct_component_cases')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
