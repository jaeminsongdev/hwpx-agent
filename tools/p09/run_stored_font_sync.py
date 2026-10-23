"""317: bounded docs/current modified-source audit of font product24, no runtime replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_stored_font_recovery as latest
shared,c,a,tools,compact,audit=latest.shared,latest.c,latest.a,latest.tools,latest.compact,latest.audit
OUTPUT='implementation/p09/evidence/p09-361-stored-font-sync317.v1.json';DRIVER='tools/p09/run_stored_font_sync.py'
BASE='implementation/p09/evidence/p09-361-scoped-font-sync314.v1.json'
REPORT='implementation/p09/P09_FONT_REFERENCE_REPLACEMENT_PROGRESS.md';PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
PROFILE='protocol/migrations/p09-scoped-font-name-replacement-v1.md';PRODUCT='protocol/migrations/p09-stored-scoped-font-product-v1.md'
OLD_ROW='| SEARCH-024 | 폰트 일괄 대체 | 공유 참조/바이너리24와 별도 이름/selector의 run·text 축 고유20pass, review/field/protection 조합·전체 옵션·실제 유효 폰트/fallback·현재 저장/제품/target 미완료 |'
NEW_ROW='| SEARCH-024 | 폰트 일괄 대체 | 공유 참조/바이너리24·이름/selector run·text 고유20·현재 저장/별도 엄격한 제품24pass, 공통 compiler/dispatcher·review/field/protection 조합·전체 옵션·실제 유효 폰트/fallback·실행/저장/target 미완료 |'
OLD_BOUNDARY='''현재 저장 서비스의 ACL/head/격리/AEAD·제품 입력·operation compiler/실행·저장 트랜잭션·게시,
style_filter/preview_only의 전체 제품 계약, 풍부한 review/field/protection 조합, 실제 폰트와 Native
match_set·semantic_diff·reopen은 남는다. SEARCH-024 전체 제품과 P09 Gate는 OPEN이다.
'''
NEW_BOUNDARY='''현재 저장 서비스의 ACL/head/격리/AEAD와 엄격한 별도 제품 입력은 후속
[저장 폰트 제품 계약](p09-stored-scoped-font-product-v1.md)의24개 시험으로 연결했다.
이 경로는 서버 query/compiled/DFA 상한이 더 낮으면 이를 유지한다. 기본 이름 해석 API의 한도와
기존 매핑·요청 지문 의미는 그대로다. 공통 operation compiler/실행·저장 트랜잭션·게시,
style_filter/preview_only의 전체 제품 계약, 풍부한 review/field/protection 조합, 실제 폰트와 Native
match_set·semantic_diff·reopen은 남는다. SEARCH-024 전체 제품과 P09 Gate는 OPEN이다.
'''

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STORED_FONT_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_FONT_SYNC',own_cpu_selection=selection,tests_build_DB_or_Hangul_replayed=False,
        document_and_changed_source_audit_not_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT));failed=compact.unpack(q.json(latest.previous.OUTPUT));docs=q.json(BASE)
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='69244dce380116a69c7429d2a6bdc40e983a33545a151b3c6ce9ccf2e52a7182'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==739 and passed['new_cases']==24,'EXACT316_STORED_PRODUCT24_CURRENT_SOURCE_EVIDENCE')
        c.require(q.snapshots[latest.previous.OUTPUT]['sha256']=='64d2e528c343302c9b08ab9b2ad83cb8cd623a2550e64446c9b603b098918055'and failed['cleanup']and failed['steps'][0]['tests']==[],'EXACT315_ORIGINAL_COMPILE_FAILURE_RETAINED')
        old={p['path']:p for p in passed['source_pins']};code=latest.previous
        source=code.NEW|code.CHANGED|{code.FIXTURE,latest.DRIVER,code.previous.base.CATALOG,code.previous.base.READBACK,code.previous.base.TEST}
        for n in sorted(source):q.pin(n);c.require(q.snapshots[n]==old[n],'CURRENT_CHANGED_SOURCES_FIXTURES_AND_RUNNERS_MATCH316')
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(code.TEST)));step=passed['steps'][0];j=step['owned_job'];account=j['last_job_accounting']
        c.require(len(cases)==24 and {n for n,s in step['tests']if s=='ok'}==cases and len(step['tests'])==24 and step['diagnostics']==[]and step['exit_code']==0,'EXACT24_SUCCESSFUL_IDENTITIES_AND_NO_DIAGNOSTICS')
        c.require(j['owned_tree_empty']and j['cleanup_confirmed']and j['job_handle_closed']and account['active_processes']==0,'EXACT316_TERMINAL_EMPTY_CLOSED_JOB')
        c.require(step['elapsed_seconds']==12.969 and account['job_cpu_seconds']==12.266 and account['peak_job_private_mib']==736.46
            and passed['elapsed_seconds']==107.782 and passed['system_CPU_max']==16.93 and 41.2961<passed['available_RAM_min_percent']<41.2962,'EXACT_REPORTED_RESOURCE_VALUES')
        c.require(q.snapshots[BASE]['sha256']=='8768e6cce5b61967097090cc261341d8299abe482ef6a47718666cecf7240f29'and docs['cleanup'],'EXACT314_PREVIOUS_DOC_BASELINE')
        old_docs={p['path']:p for p in docs['source_pins']}
        text=q.text('CURRENT_STATE.md');marker='> 2026-10-21 P09 ACTIVE 최신 폰트 이름과 선택 범위 치환'
        c.require(text.startswith('> 2026-10-21 P09 ACTIVE 최신 폰트 현재 저장과 제품 요청')and text.count(marker)==1,'ONE_NEW_CURRENT_STORED_FONT_PREFIX')
        prefix=text[:text.index(marker)];audit.inverse(text[text.index(marker):],old_docs['CURRENT_STATE.md'],'ALL_PRIOR_CURRENT_STATE_HISTORY_PRESERVED')
        for marker in ('739fresh/final739','신규24pass','제품 코드는315와 동일','공통 operation compiler/dispatcher','공식158/249','P09/A12/A13 OPEN','Native011 미승인/미실행','CROSSREF8종 NOT_RUN'):
            c.require(marker in prefix,'CURRENT_PREFIX_EXPLICIT_EVIDENCE_AND_UNCHANGED_GATE_BOUNDARY')
        sections=[]
        for path,end in ((REPORT,'## 폰트 이름과 선택 범위 치환\n'),(PROGRESS,'## 원본 폰트 참조 치환\n')):
            text=q.text(path);start=text.index('## 현재 저장 서비스와 폰트 제품 요청\n');finish=text.index(end,start);section=text[start:finish];sections.append((path,section))
            restored=text[:start]+text[finish:]
            if path==PROGRESS:c.require(text.count(NEW_ROW)==1,'ONLY_SEARCH024_ADVANCED');restored=restored.replace(NEW_ROW,OLD_ROW)
            audit.inverse(restored,old_docs[path],'ALL_OTHER_PROGRESS_AND_FAILURE_HISTORY_PRESERVED')
            for marker in ('24pass','739fresh/final739','107.782초','12.969초','8.39초','736.46MiB','16.93%','41.2961%','P09/A12/A13 OPEN'):
                c.require(marker in section,'REPORT_EXACT_PRODUCT_COMPONENT_AND_RESOURCE_SCOPE')
        text=q.text(PROFILE);c.require(text.count(NEW_BOUNDARY)==1,'ONE_SOURCE_CONTRACT_CURRENT_STORED_BOUNDARY')
        audit.inverse(text.replace(NEW_BOUNDARY,OLD_BOUNDARY),old_docs[PROFILE],'ALL_ORIGINAL_SOURCE_NAME_SCOPE_READBACK_AND_FAILURE_CONTRACTS_PRESERVED')
        text=q.text(PRODUCT);sections.extend(((PROFILE,NEW_BOUNDARY),(PRODUCT,text)));q.pin(DRIVER)
        for marker in ('product-scoped-font-replacement-request/v1','1~10000','16KiB','RouteUnqualified','공통 operation compiler/dispatcher','739fresh/final739'):
            c.require(marker in text,'STRICT_FONT_PRODUCT_CONTRACT_SCHEMA_BUDGET_AND_DENIED_AUTHORITY')
        for path,section in sections:
            for target in re.findall(r'\]\(([^)]+)\)',section):
                p=(c.ROOT/path).parent/target;c.require(p.resolve().is_relative_to(c.ROOT.resolve())and p.is_file(),'NEW_LOCAL_EVIDENCE_AND_PROTOCOL_LINK_EXISTS')
        q.finish();guard.check(force=True);row.update(state='PASS_STORED_FONT_PRODUCT24_CURRENT_DOC_SYNC_NOT_COMMON_EXECUTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            distinct_new_product_cases=24,official_queue_accepted=158,official_queue_total=249,next_work='source_edit_inventory_and_common_operation_compiler_and_dispatcher')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'STORED_FONT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','distinct_new_product_cases')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
