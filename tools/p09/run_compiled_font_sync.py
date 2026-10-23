"""325: scoped current compiler source/docs closure, no test/Native/old queue replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_compiled_font_recovery as latest
shared,c,a,tools,compact,audit=latest.shared,latest.c,latest.a,latest.tools,latest.compact,latest.audit
OUTPUT='implementation/p09/evidence/p09-361-compiled-font-sync325.v1.json';DRIVER='tools/p09/run_compiled_font_sync.py'
BASE='implementation/p09/evidence/p09-361-font-edit-inventory-sync-recovery322.v1.json'
REPORT='implementation/p09/P09_FONT_REFERENCE_REPLACEMENT_PROGRESS.md';PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
INVENTORY='protocol/migrations/p09-font-edit-inventory-v1.md';PRODUCT='protocol/migrations/p09-stored-scoped-font-product-v1.md';PROFILE='protocol/migrations/p09-compiled-font-resources-v1.md'
OLD_ROW='| SEARCH-024 | 폰트 일괄 대체 | 원본/별도 제품 기반과 실제 헤더·본문 편집 inventory 신규12+영향 원본9/제품24pass, 공통 compiler/dispatcher·review/field/protection 조합·전체 옵션·실제 유효 폰트/fallback·실행/저장/target 미완료 |'
NEW_ROW='| SEARCH-024 | 폰트 일괄 대체 | 원본/저장/제품·실제 헤더/본문 inventory와 공통 준비/계획 신규 폰트16+영향 기존4pass, review/field/protection 조합·전체 옵션·실제 유효 폰트/fallback·실행/저장/target 미완료 |'
CHANGES={INVENTORY:[('''이 목록은 헤더를 첫 문단이나 가상 노드로 바꾸지 않는다. 후속 [폰트 공통 계획](p09-compiled-font-resources-v1.md)은
두 헤더 효과를 필수 잠금 자원 인자로 보존하고 실제 본문 소유자에 결속한다. 공통 준비와 compiler는
연결했지만 실제 실행 route는 여전히 미완료다.
''','''이 목록은 헤더를 첫 문단이나 가상 노드로 바꾸지 않는다. 후속 compiler는 두 헤더 효과를 필수 자원
의존성으로 보존하고 실제 본문 소유자와 결속해야 한다. 아직 공통 dispatcher/실행 route에 연결하지 않았다.
''')],PRODUCT:[('''폰트는 후속 [공통 준비와 계획](p09-compiled-font-resources-v1.md)의19번째 family에도 연결했다.
본문 편집의 [실제 inventory](p09-font-edit-inventory-v1.md)와 두 헤더 자원 효과를 함께 결속한다.
독립 API의 현재 접근/receipt/route 거부는 그대로이며 공통 계획도 실행 권한을 부여하지 않는다.
''','''폰트는 현재 독립 제품 API이며 기존 공통 검색 mutation 표에 넣지 않았다. 실제 header 정의 추가와
본문 편집의 [실제 inventory](p09-font-edit-inventory-v1.md)는 후속 신규12개 시험으로 연결했다.
헤더 자원 의존성과 실제 본문 소유자를 원 IR/compiler에 결속한 뒤 공통 표를 확장해야 한다.
'''),('공통 compiler/준비 연결은 후속 폰트16+영향 기존4개 시험으로 확인했다. 풍부한 review/field/protection 조합,\n',
    '다음은 헤더 자원/본문 소유자의 공통 compiler/dispatcher 결속이다. 풍부한 review/field/protection 조합,\n')]}
GENERIC=[('protocol/migrations/p09-source-search-operation-compiler-v1.md',7415,'144baad94aac5e4b16c25e4211fec249d72ae356eab18383264828fd700dd23e'),
    ('protocol/migrations/p09-common-search-mutation-dispatch.md',8476,'1672754eff8cab077eb59bb78fb1296bf8349e4d60d6286866af690254f1e11b')]

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'COMPILED_FONT_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_COMPILED_FONT_SYNC',own_cpu_selection=selection,tests_build_DB_or_Hangul_replayed=False,
        document_and_changed_source_audit_not_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT));failed=compact.unpack(q.json(latest.previous.OUTPUT));docs=q.json(BASE)
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='03833b97cf9144c6095528edbb425611a7800dacb5b5a5835a97a3dca051a545'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==753 and passed['new_font_common_cases']==16 and passed['affected_legacy_cases']==4,'EXACT324_COMMON_FONT16_LEGACY4_EVIDENCE')
        c.require(q.snapshots[latest.previous.OUTPUT]['sha256']=='4c3b7a5956bbeaec6b5681cfbfe1e45d08a7f7a8e3df22925f339af471c9d26d'and failed['cleanup']and failed['steps']==[],'EXACT323_BEFORE_BUILD_INPUT_FAILURE_RETAINED')
        code=latest.previous;old={p['path']:p for p in passed['source_pins']}
        for n in sorted(code.NEW|code.CHANGED|{latest.DRIVER}):q.pin(n);c.require(q.snapshots[n]==old[n],'CURRENT_COMMON_COMPILER_DISPATCH_HELPERS_AND_TESTS_MATCH324')
        cases={'compiled_font_v1::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(code.TEST))};step=passed['steps'][0];j=step['owned_job'];account=j['last_job_accounting']
        c.require(len(cases)==20 and len([n for n in cases if n.startswith('compiled_font_v1::legacy_')])==4 and len(step['tests'])==20
            and {n for n,s in step['tests']if s=='ok'}==cases and step['diagnostics']==[]and step['exit_code']==0,'EXACT20_SUCCESSFUL_IDENTITIES_NO_DIAGNOSTICS')
        c.require(j['owned_tree_empty']and j['cleanup_confirmed']and j['job_handle_closed']and account['active_processes']==0,'COMPILED_JOB_TERMINAL_EMPTY_CLOSED')
        c.require(passed['elapsed_seconds']==120.562 and step['elapsed_seconds']==22.797 and account['job_cpu_seconds']==21.234 and account['peak_job_private_mib']==894.05
            and passed['system_CPU_max']==25.57 and 40.2435<passed['available_RAM_min_percent']<40.2437,'EXACT_REPORTED_RESOURCES')
        c.require(q.snapshots[BASE]['sha256']=='a5a0bf951e1b246cabe2ee6ec0e5defec80604f10157433a6f776784397de7af'and docs['cleanup'],'EXACT322_PRIOR_DOC_BASELINE')
        old_docs={p['path']:p for p in docs['source_pins']};text=q.text('CURRENT_STATE.md');marker='> 2026-10-21 P09 ACTIVE 최신 폰트 헤더와 본문 편집 목록'
        c.require(text.startswith('> 2026-10-21 P09 ACTIVE 최신 폰트 공통 준비와 계획')and text.count(marker)==1,'ONE_CURRENT_COMMON_FONT_PREFIX')
        prefix=text[:text.index(marker)];audit.inverse(text[text.index(marker):],old_docs['CURRENT_STATE.md'],'ALL_PRIOR_CURRENT_STATE_HISTORY_PRESERVED')
        for marker in ('753fresh/final753','16+영향 기존4=20pass','공식158/249','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행','실제 실행기는 아직 연결하지 않았다'):
            c.require(marker in prefix,'CURRENT_PREFIX_EXACT_SCOPE_AND_DENIED_EXECUTION_BOUNDARIES')
        sections=[]
        for path in (REPORT,PROGRESS):
            text=q.text(path);start=text.index('## 폰트 공통 준비와 계획 컴파일러\n');end=text.index('## 폰트 헤더 자원과 본문 편집 목록\n',start);section=text[start:end];sections.append((path,section));restored=text[:start]+text[end:]
            if path==PROGRESS:c.require(text.count(NEW_ROW)==1,'ONLY_SEARCH024_ADVANCED');restored=restored.replace(NEW_ROW,OLD_ROW)
            audit.inverse(restored,old_docs[path],'ALL_OTHER_SEARCH_ROWS_PROGRESS_AND_FAILURE_HISTORY_PRESERVED')
            for marker in ('신규 폰트16+영향 기존4=20pass','753fresh/final753','120.562초','22.797초','10.00초','894.05MiB','25.57%','40.2436%','P09/A12/A13 OPEN'):
                c.require(marker in section,'EXACT_REPORTED_COMMON_PRODUCT_COUNT_RESOURCES_AND_GATE_SCOPE')
        for path,changes in CHANGES.items():
            text=q.text(path);restored=text
            for after,before in changes:c.require(restored.count(after)==1,'ONE_EXPLICIT_CONTRACT_CURRENT_BOUNDARY_CHANGE');restored=restored.replace(after,before)
            audit.inverse(restored,old_docs[path],'ALL_ORIGINAL_FONT_INPUT_INVENTORY_AND_FAILURE_CONTRACTS_PRESERVED');sections.append((path,text))
        for path,size,sha in GENERIC:
            text=q.text(path);start=text.index('## 현재 공통 경로\n');end=text.index('## 이전 연결 기록\n\n',start)+len('## 이전 연결 기록\n\n');section=text[start:end];sections.append((path,section))
            audit.inverse(text[:start]+text[end:],dict(path=path,bytes=size,sha256=sha),'ALL_GENERIC_COMPILER_AND_DISPATCH_HISTORY_MATCHES_PRE_EDIT_BYTES')
        text=q.text(PROFILE);sections.append((PROFILE,text));q.pin(DRIVER)
        for marker in ('19번째','source_font_header_count_effect_json','source_font_header_append_effect_json','source_font_resource_binding_profile','source_edit_operations','본문 operation 수','15개','기존18개','16+영향 기존4=20pass','RouteUnqualified'):
            c.require(marker in text,'EXPLICIT_CURRENT_FONT_PLAN_BODY_RESOURCE_GROUP_AND_UNQUALIFIED_EXECUTION_CONTRACT')
        for path,section in sections:
            for target in re.findall(r'\]\(([^)]+)\)',section):
                p=(c.ROOT/path).parent/target;c.require(p.resolve().is_relative_to(c.ROOT.resolve())and p.is_file(),'CURRENT_LOCAL_EVIDENCE_AND_CONTRACT_LINK_EXISTS')
        q.finish();guard.check(force=True);row.update(state='PASS_FONT_COMMON_COMPILER16_LEGACY4_CURRENT_DOC_SYNC_NOT_EXECUTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_font_common_cases=16,affected_legacy_cases=4,official_queue_accepted=158,official_queue_total=249,next_work='remaining_font_full_options_and_review_field_protection_then_qualified_execution_storage')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'COMPILED_FONT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','new_font_common_cases','affected_legacy_cases')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
