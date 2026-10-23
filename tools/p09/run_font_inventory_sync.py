"""321: current font effect metadata/source/docs audit; no successful test or Native replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_font_inventory_recovery as latest
shared,c,a,tools,compact,audit=latest.shared,latest.c,latest.a,latest.tools,latest.compact,latest.audit
OUTPUT='implementation/p09/evidence/p09-361-font-edit-inventory-sync321.v1.json';DRIVER='tools/p09/run_font_inventory_sync.py'
BASE='implementation/p09/evidence/p09-361-stored-font-sync-recovery318.v1.json'
REPORT='implementation/p09/P09_FONT_REFERENCE_REPLACEMENT_PROGRESS.md';PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
PRODUCT='protocol/migrations/p09-stored-scoped-font-product-v1.md';PROFILE='protocol/migrations/p09-font-edit-inventory-v1.md'
OLD_ROW='| SEARCH-024 | 폰트 일괄 대체 | 공유 참조/바이너리24·이름/selector run·text 고유20·현재 저장/별도 엄격한 제품24pass, 공통 compiler/dispatcher·review/field/protection 조합·전체 옵션·실제 유효 폰트/fallback·실행/저장/target 미완료 |'
NEW_ROW='| SEARCH-024 | 폰트 일괄 대체 | 원본/별도 제품 기반과 실제 헤더·본문 편집 inventory 신규12+영향 원본9/제품24pass, 공통 compiler/dispatcher·review/field/protection 조합·전체 옵션·실제 유효 폰트/fallback·실행/저장/target 미완료 |'
PRODUCT_CHANGES=[('''본문 편집의 [실제 inventory](p09-font-edit-inventory-v1.md)는 후속 신규12개 시험으로 연결했다.
헤더 자원 의존성과 실제 본문 소유자를 원 IR/compiler에 결속한 뒤 공통 표를 확장해야 한다.
''','본문 편집을 원 IR에 결속하는 inventory/compiler 연결을 구현한 뒤 공통 표를 확장해야 한다.\n'),
('''후속 inventory의 현재 전달은 신규12+영향 제품24pass이며 기존 원본9개 결과를 별도로 보존했다.
다음은 헤더 자원/본문 소유자의 공통 compiler/dispatcher 결속이다. 풍부한 review/field/protection 조합,
''','다음은 편집 inventory와 공통 compiler/dispatcher다. 풍부한 review/field/protection 조합,\n')]

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FONT_INVENTORY_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_INVENTORY_SYNC',own_cpu_selection=selection,tests_build_DB_or_Hangul_replayed=False,
        document_and_changed_source_audit_not_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT));partial=compact.unpack(q.json(latest.previous.OUTPUT));docs=q.json(BASE)
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='cec5c861e4cd4a8386023d843835fc5cb0962479315cb282309e389e041d69ce'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==745 and passed['new_cases']==12 and passed['retained_source_cases']==9,'EXACT320_NEW12_PRODUCT24_CURRENT_SOURCE_CLOSURE')
        c.require(q.snapshots[latest.previous.OUTPUT]['sha256']=='b99c99bf713335849158e0f0d0484e47e4a1bf69a92f3b1da326e7ca6b5aa238'and partial['cleanup']
            and partial['steps'][1]['tests']==[]and partial['steps'][1]['bounded_output_observation']['rust_error_codes']==['E0624'],'EXACT319_SOURCE9_AND_ORIGINAL_COMPILE_FAILURE_RETAINED')
        old={p['path']:p for p in passed['source_pins']};original={p['path']:p for p in partial['source_pins']};code=latest.previous
        source=code.NEW|code.CHANGED|{latest.DRIVER,code.base.previous.base.TEST,code.base.FIXTURE}
        for n in sorted(source):
            q.pin(n);c.require(q.snapshots[n]==old[n],'CURRENT_INVENTORY_SERVICE_KERNEL_TESTS_AND_RUNNERS_MATCH320')
            if n!=code.TEST and n in original:c.require(q.snapshots[n]==original[n],'PRODUCTION_UNCHANGED_FROM319_SOURCE9')
        text=q.text(code.TEST);c.require(text.count(latest.CURRENT)==1,'ONE_PUBLIC_ATTRIBUTE_BYTE_READ_CORRECTION')
        audit.inverse(text.replace(latest.CURRENT,latest.ORIGINAL),original[code.TEST],'ALL_OTHER_NEW_TEST_BODIES_UNCHANGED_FROM319')
        legacy=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(code.base.TEST)));new={'edit_inventory_v1::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}
        c.require(len(legacy)==24 and len(new)==12 and len(passed['steps'][0]['tests'])==36 and {n for n,s in passed['steps'][0]['tests']if s=='ok'}==legacy|new
            and passed['steps'][0]['diagnostics']==[],'EXACT36_CURRENT_SUCCESSFUL_PRODUCT_IDENTITIES')
        core={'scoped::'+n for n in code.CORE_CASES};c.require(len(partial['steps'][0]['tests'])==9 and {n for n,s in partial['steps'][0]['tests']if s=='ok'}==core
            and partial['steps'][0]['diagnostics']==[],'EXACT9_RETAINED_SOURCE_IDENTITIES_NOT_REPLAYED')
        for r in (partial,passed):
            for s in r['steps']:
                j=s['owned_job'];c.require(j['owned_tree_empty']and j['cleanup_confirmed']and j['job_handle_closed']and j['last_job_accounting']['active_processes']==0,'ALL_COMPILE_TEST_JOBS_TERMINAL_EMPTY_CLOSED')
        j=passed['steps'][0]['owned_job']['last_job_accounting']
        c.require(passed['elapsed_seconds']==115.36 and passed['steps'][0]['elapsed_seconds']==19.437 and j['job_cpu_seconds']==17.438 and j['peak_job_private_mib']==735.09
            and passed['system_CPU_max']==27.44 and 41.0090<passed['available_RAM_min_percent']<41.0092,'EXACT320_REPORTED_RESOURCES')
        c.require(q.snapshots[BASE]['sha256']=='fc1763f24a0630d67c3f6cfed6666681983ce1cae1544ea6b0020daaff826a98'and docs['cleanup'],'EXACT318_PRIOR_DOC_BASELINE')
        old_docs={p['path']:p for p in docs['source_pins']};text=q.text('CURRENT_STATE.md');marker='> 2026-10-21 P09 ACTIVE 최신 폰트 현재 저장과 제품 요청'
        c.require(text.startswith('> 2026-10-21 P09 ACTIVE 최신 폰트 헤더와 본문 편집 목록')and text.count(marker)==1,'ONE_NEW_FONT_INVENTORY_PREFIX')
        prefix=text[:text.index(marker)];audit.inverse(text[text.index(marker):],old_docs['CURRENT_STATE.md'],'ALL_PRIOR_CURRENT_STATE_HISTORY_PRESERVED')
        for marker in ('745fresh/final745','고유45개','단일45개 전체 실행은 아니다','공식158/249','P09/A12/A13 OPEN','Native011 미승인/미실행','CROSSREF8종 NOT_RUN'):
            c.require(marker in prefix,'CURRENT_PREFIX_PRESERVES_EXACT_EVIDENCE_AND_GATE_BOUNDARIES')
        sections=[]
        for path in (REPORT,PROGRESS):
            text=q.text(path);start=text.index('## 폰트 헤더 자원과 본문 편집 목록\n');end=text.index('## 현재 저장 서비스와 폰트 제품 요청\n',start);section=text[start:end];sections.append((path,section));restored=text[:start]+text[end:]
            if path==PROGRESS:c.require(text.count(NEW_ROW)==1,'ONLY_SEARCH024_ADVANCED');restored=restored.replace(NEW_ROW,OLD_ROW)
            audit.inverse(restored,old_docs[path],'ALL_OTHER_SEARCH_ROWS_PROGRESS_AND_FAILURE_HISTORY_PRESERVED')
            for marker in ('신규12+영향 제품24=36pass','745fresh/final745','고유45개','115.36초','19.437초','13.94초','735.09MiB','1861.88MiB','27.44%','P09/A12/A13 OPEN'):
                c.require(marker in section,'EXACT_INVENTORY_COMPONENT_COUNT_RESOURCE_AND_GATE_SCOPE')
        text=q.text(PRODUCT);restored=text
        for after,before in PRODUCT_CHANGES:c.require(restored.count(after)==1,'ONE_CURRENT_PRODUCT_CONTRACT_BOUNDARY_UPDATE');restored=restored.replace(after,before)
        audit.inverse(restored,old_docs[PRODUCT],'ALL_ORIGINAL_STRICT_PRODUCT_AND_FAILURE_CONTRACTS_PRESERVED');sections.append((PRODUCT,text))
        text=q.text(PROFILE);sections.append((PROFILE,text));q.pin(DRIVER)
        for marker in ('source-font-edit-inventory/v1','4096개','8MiB','CharacterPropertyCount','AppendCharacterProperties','RunSubtree','TextSubtree','공통 dispatcher/실행 route에 연결하지 않았다','고유45개'):
            c.require(marker in text,'EXPLICIT_TYPED_HEADER_BODY_BUDGET_AND_UNQUALIFIED_COMPILER_CONTRACT')
        for path,section in sections:
            for target in re.findall(r'\]\(([^)]+)\)',section):
                p=(c.ROOT/path).parent/target;c.require(p.resolve().is_relative_to(c.ROOT.resolve())and p.is_file(),'NEW_LOCAL_EVIDENCE_AND_PROTOCOL_LINK_EXISTS')
        q.finish();guard.check(force=True);row.update(state='PASS_FONT_HEADER_BODY_INVENTORY_NEW12_AFFECTED33_CURRENT_DOC_SYNC_NOT_COMMON_COMPILER_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_inventory_cases=12,retained_source_cases=9,current_product_cases=36,distinct_cases=45,official_queue_accepted=158,official_queue_total=249,
            next_work='bind_header_resource_dependencies_and_actual_body_owners_in_common_operation_compiler')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_INVENTORY_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','distinct_cases')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
