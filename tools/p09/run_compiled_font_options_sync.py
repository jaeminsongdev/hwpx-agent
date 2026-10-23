"""336: docs-only audit of common v2 compilation and separate preview, retaining all prior histories."""
import json,re,time
from types import SimpleNamespace as NS
import run_compiled_font_options as latest
shared,c,a,tools,compact,audit=latest.shared,latest.c,latest.a,latest.tools,latest.compact,latest.audit
OUTPUT='implementation/p09/evidence/p09-361-compiled-font-options-sync336.v1.json';DRIVER='tools/p09/run_compiled_font_options_sync.py'
BASE='implementation/p09/evidence/p09-361-font-options-product-sync334.v1.json';GENERIC_BASE='implementation/p09/evidence/p09-361-compiled-font-sync325.v1.json'
REPORT='implementation/p09/P09_FONT_REFERENCE_REPLACEMENT_PROGRESS.md';PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
PROFILE='protocol/migrations/p09-font-options-product-v2.md';SOURCE_PROFILE='protocol/migrations/p09-filtered-font-source-v1.md'
COMPILER='protocol/migrations/p09-source-search-operation-compiler-v1.md';DISPATCH='protocol/migrations/p09-common-search-mutation-dispatch.md'
OLD_ROW='| SEARCH-024 | 폰트 일괄 대체 | 원본/저장/엄격한 v2 필터·preview_only 신규28+영향 v1 제품4개 검증, v2 공통 준비/계획·전체 옵션/유효 서식/폰트/fallback·실행/저장/target 미완료 |'
NEW_ROW='| SEARCH-024 | 폰트 일괄 대체 | 원본/저장/엄격한 v2와 공통 준비/계획·분리 preview 신규23+영향12개 검증, 전체 옵션/유효 서식/폰트/fallback/보호·실행/저장/target 미완료 |'
INTRO_BEFORE='저장/제품 알고리즘은 그대로이며 v1은 두 옵션을 계속 거부한다. 공통 dispatcher·계획 compiler와\n실제 실행·저장 트랜잭션은 아직 연결하지 않았다.\n'
INTRO_AFTER='저장/제품 알고리즘은 그대로이며 v1은 두 옵션을 계속 거부한다. v2 변경 후보는 공통20번째 family이며\n미리보기는 별도 비변경 결과다. 실제 실행·저장 트랜잭션은 아직 연결하지 않았다.\n'
GENERIC_BEFORE={COMPILER:'''현재 공통 표는 기존18개 family와 폰트를 합한19개다. 기존18개는 아래12개 인자 계약을 유지하고
폰트만 실제 본문 owner와 두 헤더 자원·적용 profile의15개 인자를 사용한다.
[폰트 공통 계획 계약](p09-compiled-font-resources-v1.md)은 body_splices index와 전체 inventory 지문을
구분하며 헤더를 본문 node로 만들거나 operation마다 반복 적용하지 않는다. 신규 폰트16+영향 기존4개
검증은 준비·계획의 범위이며 실제 실행/저장·신뢰된 registry·Native/Gate는 남는다.
이하 초기16종과 후속 연결의 원본 검증 이력을 보존한다.

''',DISPATCH:'''현재 준비 표는19개 family이며 폰트 schema는 기존18개 뒤에 추가했다. 원 typed parser/receipt·
서버 한도·현재 접근/전달/route 거부를 그대로 사용한다. [폰트 공통 계획](p09-compiled-font-resources-v1.md)은
실제 본문 owner와 두 헤더 자원 효과를 결속하며 실행 권한을 열지 않는다. 신규 폰트16+영향 기존4개
검증에서 기존 네 경로의12개 인자를 유지했고 폰트만15개다. 이하 초기16종과 후속 연결 기록은 이전 이력이다.

'''}

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'COMPILED_FONT_OPTIONS_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_COMPILED_FONT_OPTIONS_SYNC',own_cpu_selection=selection,tests_build_DB_or_Hangul_replayed=False,
        document_and_changed_source_audit_not_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT));docs=q.json(BASE);generic=q.json(GENERIC_BASE)
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='47073d385a8453f7d306dc36d15fda6d63765d4390c417e367db1280629e2d78'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==779 and passed['new_cases']==23 and passed['affected_cases']==12,'EXACT335_COMMON_V2_COMPILER_PREVIEW35_CURRENT_CLOSURE')
        c.require(q.snapshots[BASE]['sha256']=='58f44e3e80258ef1961acbee1696bfcdf13e2d877ea83d440ca28ebe28f979c5'and docs['cleanup'],'EXACT334_PRIOR_DOC_BASELINE')
        c.require(q.snapshots[GENERIC_BASE]['sha256']=='db2a1d9433cbfb7d815322d8203099fb618ccccd03522de1eb6f99ec7dc6b34c'and generic['cleanup'],'EXACT325_PRIOR_GENERIC_CONTRACTS')
        old={p['path']:p for p in passed['source_pins']};source=latest.CHANGED|latest.NEW|{latest.COMMON[:-3]+'/compiled_search/font_resources.rs',latest.COMMON[:-3]+'/compiled_search/build.rs',latest.COMMON[:-3]+'/compiled_search.rs'}
        for n in sorted(source):q.pin(n);c.require(q.snapshots[n]==old[n],'CURRENT_COMMON_MODE_TYPE_PARSER_OWNER_HEADER_BUDGET_GUARDS_AND_TESTS_MATCH335')
        previous=compact.unpack(q.json(latest.previous.OUTPUT));latest.inverse(q,{p['path']:p for p in previous['source_pins']})
        cases={'compiled_font_v2::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(latest.TEST))}|{'compiled_font_v1::'+n for n in latest.AFFECTED_COMMON}|{'font_options_v2::'+n for n in latest.AFFECTED_V2}
        c.require(len(passed['steps'])==1,'ONE_OWNED_CARGO_ONLY');step=passed['steps'][0]
        c.require(len(cases)==35 and len(step['tests'])==35 and {n for n,status in step['tests']if status=='ok'}==cases
            and step['diagnostics']==[]and step['bounded_output_observation']['safe_warning_locations']==[],'EXACT_NEW23_AFFECTED_COMMON6_PRODUCT6_PASS')
        job=step['owned_job'];account=job['last_job_accounting'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']and account['active_processes']==0,'OWNED_JOB_TERMINAL_EMPTY_CLOSED')
        c.require(passed['elapsed_seconds']==133.906 and step['elapsed_seconds']==32.094 and account['job_cpu_seconds']==30.016
            and account['peak_job_private_mib']==900.62 and passed['system_CPU_max']==30.18 and 42.1102<passed['available_RAM_min_percent']<42.1104,'EXACT_UNHIDDEN_RUNTIME_RESOURCES')
        old_docs={p['path']:p for p in docs['source_pins']};text=q.text('CURRENT_STATE.md');marker='> 2026-10-21 P09 ACTIVE 최신 폰트 필터와 미리보기 제품 준비'
        c.require(text.startswith('> 2026-10-21 P09 ACTIVE 최신 폰트 v2 공통 계획과 비변경 미리보기')and text.count(marker)==1,'ONE_CURRENT_COMMON_V2_PREFIX')
        prefix=text[:text.index(marker)];audit.inverse(text[text.index(marker):],old_docs['CURRENT_STATE.md'],'ALL_PRIOR_CURRENT_STATE_HISTORY_PRESERVED')
        for marker in ('35pass','779fresh/final779','SearchPreview','30.18%','공식158/249','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in prefix,'CURRENT_PREFIX_CORRECT_COMMON_PREPARATION_ONLY_SCOPE_AND_PHASE_BOUNDARIES')
        sections=[]
        for path in (REPORT,PROGRESS):
            text=q.text(path);start=text.index('## 폰트 v2 공통 계획과 비변경 미리보기\n');end=text.index('## 폰트 필터와 미리보기의 저장 및 제품 준비\n',start);section=text[start:end];sections.append((path,section));restored=text[:start]+text[end:]
            if path==PROGRESS:c.require(text.count(NEW_ROW)==1,'ONLY_SEARCH024_ADVANCED');restored=restored.replace(NEW_ROW,OLD_ROW)
            audit.inverse(restored,old_docs[path],'ALL_OTHER_SEARCH_ROWS_PROGRESS_AND_FAILURE_HISTORY_PRESERVED')
            for marker in ('35pass','779fresh/final779','133.906초','32.094초','30.016초','900.62MiB','30.18%','42.1103%','SearchPreview','P09/A12/A13 OPEN'):
                c.require(marker in section,'CURRENT_COMMON_SCOPE_AND_RESOURCE_VALUES_EXACT')
        text=q.text(PROFILE);start=text.index('## 공통 준비와 계획 및 비변경 미리보기\n');end=text.index('## 이전 저장과 제품 검증\n',start);section=text[start:end];sections.append((PROFILE,text))
        restored=text[:start]+text[end:];c.require(text.count(INTRO_AFTER)==1,'ONE_PRODUCT_INTRO_UPDATED')
        restored=restored.replace(INTRO_AFTER,INTRO_BEFORE).replace('## 이전 저장과 제품 검증\n','## 검증과 남은 경계\n').replace(
            '전체 옵션·유효 cascade/폰트/fallback/보호 의미,\n','v2 공통 준비/계획과 별도 비변경 preview dispatch, 전체 옵션·유효 cascade/폰트/fallback/보호 의미,\n')
        audit.inverse(restored,old_docs[PROFILE],'ALL_PRIOR_V2_JSON_STORED_PREVIEW_AND_FAILED_BOUNDARIES_PRESERVED')
        for marker in ('PreparedStoredFontOptionsMutation','SearchPreview','with_verified_preview_json','mutation_receipt_sha256','35pass','779fresh/final779','최종 head 경합5개'):
            c.require(marker in section,'COMMON_CONTRACT_EXPLICIT_MODE_SEPARATION_FILTER_BINDING_AND_RUNTIME_SCOPE')
        text=q.text(SOURCE_PROFILE);new='전체 제품 옵션·전체 서식/폰트/보호 의미·신뢰 registry·실제 실행/저장/게시와 Native/Gate는\n';oldline='전체 제품 옵션·v2 공통 준비/계획·전체 서식/폰트/보호 의미·신뢰 registry·실제 실행/저장/게시와 Native/Gate는\n'
        c.require(text.count(new)==1,'ONE_SOURCE_CONTRACT_REMAINING_BOUNDARY_UPDATE');audit.inverse(text.replace(new,oldline),old_docs[SOURCE_PROFILE],'ALL_OTHER_SOURCE_FILTER_CONTRACT_BYTES_PRESERVED')
        old_generic={p['path']:p for p in generic['source_pins']}
        for path,before in GENERIC_BEFORE.items():
            text=q.text(path);start=text.index('## 현재 공통 경로\n\n')+len('## 현재 공통 경로\n\n');end=text.index('## 이전 연결 기록\n',start);section=text[start:end];sections.append((path,section))
            audit.inverse(text[:start]+before+text[end:],old_generic[path],'ALL_GENERIC_CONTRACT_HISTORY_EXCEPT_CURRENT20_AND_PREVIEW_SCOPE_PRESERVED')
            for marker in ('20개','SearchPreview','신규23+영향12개','15개','12개'):c.require(marker in section,'GENERIC_CONTRACT_CURRENT20_SEPARATE_PREVIEW_AND_ARGUMENT_COUNTS')
        q.pin(DRIVER)
        for path,section in sections:
            for target in re.findall(r'\]\(([^)]+)\)',section):
                p=(c.ROOT/path).parent/target;c.require(p.resolve().is_relative_to(c.ROOT.resolve())and p.is_file(),'CURRENT_LOCAL_EVIDENCE_AND_CONTRACT_LINK_EXISTS')
        q.finish();guard.check(force=True);row.update(state='PASS_COMMON_FONT_V2_COMPILER_PREVIEW23_AFFECTED12_DOC_SYNC_NOT_EXECUTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_common_cases=23,affected_cases=12,official_queue_accepted=158,official_queue_total=249,next_work='remaining_full_font_options_effective_formatting_protection_and_qualified_execution_storage')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'COMPILED_FONT_OPTIONS_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
