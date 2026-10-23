"""307: sync partial13 and embedding failure after correcting current-status placement."""
import json,re,time
from types import SimpleNamespace as NS
import run_font_reference_followup as latest
shared,c,a,tools,compact,audit=latest.shared,latest.c,latest.a,latest.tools,latest.compact,latest.audit
OUTPUT='implementation/p09/evidence/p09-361-font-reference-sync307.v1.json'
FAILED='implementation/p09/evidence/p09-361-font-reference-sync306.v1.json'
DRIVER='tools/p09/run_font_reference_sync.py'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
REPORT='implementation/p09/P09_FONT_REFERENCE_REPLACEMENT_PROGRESS.md'
CONTRACT='protocol/migrations/p09-source-font-reference-replacement-v1.md'
BASE='implementation/p09/evidence/p09-361-registered-recovery-sync299.v1.json'
GOOD='implementation/p09/evidence/p09-361-font-reference-followup304.v1.json'
DIAGNOSTIC='implementation/p09/evidence/p09-361-font-reference-followup305.v1.json'
OLD_ROW='| SEARCH-024 | 폰트 일괄 대체 | 실제 폰트 참조·fallback·보존 검증 필요 |'
NEW_ROW='| SEARCH-024 | 폰트 일괄 대체 | 원본 언어별 공유 참조 치환 고유13pass·내장 폰트1fail, 이름 검색/선택 범위·유효 내장 리소스·fallback·현재 저장/제품/target 미완료 |'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FONT_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_REFERENCE_SYNC',own_cpu_selection=selection,tests_build_DB_or_Hangul_replayed=False,
        document_audit_not_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        failed=q.json(FAILED);c.require(q.snapshots[FAILED]['sha256']=='11cda5ad15ec81be5e33f12d06b2b41d98ddc25cbe6f8a2fb63f0570035fc75d'
            and failed['cleanup']and failed['error_code']=='ONE_CURRENT_FONT_PREFIX','EXACT306_DOCUMENT_PREFIX_PLACEMENT_FAILURE_PRESERVED')
        good=compact.unpack(q.json(GOOD));bad=compact.unpack(q.json(DIAGNOSTIC));original=compact.unpack(q.json(latest.previous.OUTPUT));docs=q.json(BASE)
        c.require(q.snapshots[GOOD]['sha256']=='ba6b467d617feb6aecc704bcc84beaa99bdb8fe128e24e753bb6d377d234b1ed'and good['cleanup']
            and good['fresh_inputs']==good['final_fresh_hashes']==710 and good['steps'][0]['tests']==[['all_seven_language_axes_read_back_and_other_package_members_exact','ok']],'EXACT304_ONE_POSITIVE_SUCCESS_AND_FULL_CURRENT_SOURCE_CLOSURE')
        c.require(q.snapshots[DIAGNOSTIC]['sha256']=='914753acacc03c798218dddb7f7e202171d410ef770ea66773257a2c84b832ce'and bad['cleanup']and bad['state']=='FAILED_FONT_FOLLOWUP'
            and bad['diagnostic_only']and bad['steps'][0]['tests']==[['embedded_declarations_and_binary_reference_remain_exact_without_activation','FAILED']]
            and bad['steps'][0]['bounded_output_observation']['closed_static_patch_codes']==['id_index_validation_failed'],'EXACT305_ID_VALIDATION_FAILURE_REMAINS_FAILURE')
        c.require(q.snapshots[latest.previous.OUTPUT]['sha256']=='6b46012c9acee2016331789eddb68e1f76fef7c2fe450228f5e37a9041298c11'
            and original['cleanup']and sum(s=='ok'for _,s in original['steps'][0]['tests'])==12,'EXACT303_RETAINED12_NOT_FULL_PASS')
        old={p['path']:p for p in good['source_pins']};original_pins={p['path']:p for p in original['source_pins']};bad_pins={p['path']:p for p in bad['source_pins']}
        for n in {latest.prior.CORE,latest.prior.PARENT,latest.prior.TEST,latest.prior.DRIVER,latest.DRIVER,latest.previous.DRIVER}:
            q.pin(n);c.require(q.snapshots[n]==old[n]==bad_pins[n],'SCOPED_CURRENT_CODE_TESTS_AND_EXACT_FOLLOWUP_DRIVER_UNCHANGED')
        source=q.text(latest.prior.CORE);restored=source.replace('.map_err(|error| E::Patch(error.code()))','.map_err(|_| E::Patch)').replace(
            '#[error("FONT_REFERENCE_REPLACEMENT_PATCH_REJECTED:{0}")] Patch(&\'static str),','#[error("FONT_REFERENCE_REPLACEMENT_PATCH_REJECTED")] Patch,')
        audit.inverse(restored,original_pins[latest.prior.CORE],'RETAINED12_PRODUCT_ALGORITHM_IDENTICAL_ONLY_FIXED_ERROR_CODE')
        text=q.text(latest.prior.TEST);c.require(text.count(latest.NEW)==1,'ONE_SOURCE_BASED_EXPECTED_MAP_TEST')
        audit.inverse(text.replace(latest.NEW,latest.OLD),original_pins[latest.prior.TEST],'OTHER13_TEST_BODIES_PRESERVED')
        for r in (original,good,bad):
            j=r['steps'][0]['owned_job'];c.require(j['owned_tree_empty']and j['cleanup_confirmed']and j['job_handle_closed']and j['last_job_accounting']['active_processes']==0,'ALL_PARTIAL_AND_DIAGNOSTIC_JOBS_TERMINAL_EMPTY_CLOSED')
        c.require(q.snapshots[BASE]['sha256']=='6eae9262b720d521b25791f641a9280e3fcd73e7c2d52eaf15a60c4e4f55a288'and docs['cleanup'],'EXACT299_DOCUMENT_BASELINE')
        old_docs={p['path']:p for p in docs['source_pins']}
        text=q.text('CURRENT_STATE.md');marker='> 2026-10-21 P09 ACTIVE 최신 등록 영수증 기반 읽기 전용 복구'
        c.require(text.startswith('> 2026-10-21 P09 ACTIVE 최신 원본 폰트 참조 치환')and text.count(marker)==1,'ONE_CURRENT_FONT_PREFIX')
        audit.inverse(text[text.index(marker):],old_docs['CURRENT_STATE.md'],'ALL_PRIOR_CURRENT_STATE_HISTORY_PRESERVED')
        text=q.text(PROGRESS);start=text.index('## 원본 폰트 참조 치환\n');end=text.index('## P09 검색 기능의 완료 경계\n',start)
        c.require(text.count(NEW_ROW)==1,'ONE_CHANGED_SEARCH024_ROW')
        audit.inverse((text[:start]+text[end:]).replace(NEW_ROW,OLD_ROW),old_docs[PROGRESS],'OTHER18_SEARCH_ROWS_AND_ALL_PRIOR_PROGRESS_PRESERVED')
        for n in (REPORT,CONTRACT,DRIVER):q.pin(n)
        report=q.text(REPORT);contract=q.text(CONTRACT)
        for marker in ('고유13개','id_index_validation_failed','최대128개','최대4096개','SearchScopeSelector','공식158/249','P10 미시작','Native011 미승인/미실행'):
            c.require(marker in report,'REPORT_EXACT_PARTIAL_SCOPE_AND_UNRESOLVED_GATE')
        c.require('언어/from_native_id/to_native_id'in contract and '지원으로 표시하지 않는다'in contract and 'scope/name/fallback/Native/full-protection/execution'in contract,'CONTRACT_BOUNDARIES_NO_FALSE_SUPPORT')
        q.finish();guard.check(force=True);row.update(state='PASS_FONT_REFERENCE_PARTIAL13_AND_UNRESOLVED_EMBEDDING_DOC_SYNC_NOT_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            distinct_passed_component_cases=13,unresolved_original_cases=1,official_queue_accepted=158,official_queue_total=249,
            next_work='inspect_font_binary_ID_profile_and_real_manifest_resource_binding_without_bypassing_original_failures')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','distinct_passed_component_cases','unresolved_original_cases')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
