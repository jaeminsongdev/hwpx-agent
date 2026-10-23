"""372: audit current common23 mask sources and document deltas; no passing test replay."""
import json,re,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_compiled_personal_info_mask as base
shared,c,a,tools,compact,harness,audit=r.shared,r.c,r.a,r.tools,r.compact,r.harness,r.audit
OUTPUT='implementation/p09/evidence/p09-361-compiled-personal-info-mask-sync372.v1.json';DRIVER='tools/p09/run_compiled_personal_info_mask_sync.py'
RUN='implementation/p09/evidence/p09-361-compiled-personal-info-mask-metadata-recovery370.v1.json'
FINAL='implementation/p09/evidence/p09-361-compiled-personal-info-mask-receipt-hash371.v1.json'
DOCS=base.DOCS;CONTRACT_BASE='implementation/p09/evidence/p09-361-named-style-options-sync353.v1.json'
STATE='CURRENT_STATE.md';SEARCH='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md';REPORT='implementation/p09/P09_PERSONAL_INFO_MASK_PROGRESS.md'
DISPATCH='protocol/migrations/p09-common-search-mutation-dispatch.md';COMPILER='protocol/migrations/p09-source-search-operation-compiler-v1.md'
PROFILE='protocol/migrations/p09-compiled-personal-info-mask-v1.md'
OLD_ROW='| SEARCH-019 | 개인정보 바로 바꾸기 | 선택 마스킹 source25+공유3 및 현재 저장/엄격한 제품·출력 폐기 preview 신규33+영향3 검증, 공통 실행/저장·전체 개인정보 정책/문서 전체 익명화/target 미완료 |'
NEW_ROW='| SEARCH-019 | 개인정보 바로 바꾸기 | source25·제품33·공통23번째 변경/분리 preview 신규19+영향13 및 독립 receipt SHA 영향1 검증, 실제 실행/저장·전체 개인정보 정책/문서 전체 익명화/SEARCH-020/target 미완료 |'

def section(text,start,end):
    c.require(text.count(start)==text.count(end)==1,'ONE_EXPLICIT_MASK_DOC_SECTION')
    left=text.index(start);right=text.index(end,left)
    return text[left:right],text[:left]+text[right:]

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'COMPILED_MASK_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_COMPILED_MASK_SYNC',own_cpu_selection=selection,Cargo_tests_DB_or_Native_replayed=False,
        document_and_changed_source_audit_not_fresh_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,whole_package_personal_data_removed=False,native_mask_semantics_or_execution_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        run=compact.unpack(q.json(RUN));final=compact.unpack(q.json(FINAL));docs=q.json(DOCS);contracts=q.json(CONTRACT_BASE)
        for path,digest in((RUN,'e70b1f39ea06773091b58d624f9273af2d65a8b19c1d3a46131ae8a94d250330'),
            (FINAL,'2e95bcaa81070948634a550e4b6260178768e8eff8a2aef3a823ebaeafbbc873'),
            (DOCS,'661948d8b159eb195caebb099a6e2872e186cfdc678fab57cf678ef95b0ad661'),
            (CONTRACT_BASE,'55777c569a6e88cdbbb57d5f978b867f0bd24915d991a9742f071a6ae7d6b266')):
            c.require(q.snapshots[path]['sha256']==digest,'EXACT_IMMUTABLE_RUNTIME_AND_DOC_BASELINES')
        c.require(run['cleanup']and run['fresh_inputs']==run['final_fresh_hashes']==866 and len(run['steps'])==4
            and sum(len(s['tests'])for s in run['steps'])==32,'EXACT370_NEW19_AFFECTED13_NOT33')
        for s in run['steps']:tools.good_step(s,{n for n,_ in s['tests']})
        c.require(final['cleanup']and final['fresh_inputs']==final['final_fresh_hashes']==868 and final['distinct_cases']==32
            and final['retained_cases']==31 and len(final['steps'])==1 and final['steps'][0]['diagnostics']==[],'EXACT371_AFFECTED1_RETAINED31_NO_WARNINGS')
        tools.good_step(final['steps'][0],{'compiled::compiled_mask_targets_actual_text_anchors_and_locks_twelve_arguments'})
        pins={p['path']:p for p in final['source_pins']}
        for path in sorted(base.CHANGED|base.NEW|{'tools/p09/run_compiled_personal_info_mask_recovery.py',
            'tools/p09/run_compiled_personal_info_mask_metadata_recovery.py','tools/p09/run_compiled_personal_info_mask_receipt_hash.py','tools/p09/named_style_verification_runtime.py'}):
            q.pin(path);c.require(q.snapshots[path]==pins[path],'CURRENT_SOURCE_TEST_OWNER_PREVIEW_AND_RUNTIME_MATCH371')
        previous=compact.unpack(q.json(base.BASE));base.inverse(q,{p['path']:p for p in previous['source_pins']})
        old={p['path']:p for p in docs['source_pins']};state=q.text(STATE);marker='> 2026-10-21 P09 ACTIVE 최신 개인정보 마스킹의 현재 저장과 제품 요청'
        c.require(state.startswith('> 2026-10-21 P09 ACTIVE 최신 개인정보 마스킹의 공통 계획 연결')and state.count(marker)==1,'ONE_CURRENT_COMMON_MASK_PREFIX')
        prefix=state[:state.index(marker)];audit.inverse(state[state.index(marker):],old[STATE],'ALL_PRIOR_STATE_AND_FAILURE_HISTORY_RETAINED')
        search=q.text(SEARCH);s,rest=section(search,'## 개인정보 마스킹의 공통 변경 계획\n','## 개인정보 마스킹의 현재 저장과 제품 요청\n')
        c.require(rest.count(NEW_ROW)==1,'ONE_SEARCH019_ROW_DELTA');audit.inverse(rest.replace(NEW_ROW,OLD_ROW),old[SEARCH],'ALL_OTHER18_SEARCH_ROWS_AND_PREVIOUS_PROGRESS_RETAINED')
        report=q.text(REPORT);p,rest=section(report,'## 변경 전용 owner와 공통 계획 연결\n','## 현재 저장과 엄격한 제품 요청\n')
        audit.inverse(rest,old[REPORT],'ALL_ORIGINAL_MASK_SOURCE_PRODUCT_POLICY_AND_FAILURE_HISTORY_RETAINED')
        contract_pins={p['path']:p for p in contracts['source_pins']}
        for path,start,old_line,new_line in((DISPATCH,'현재 변경 준비 표는23개 family',
            '현재 변경 준비 표는22개 family','문단 스타일 v2 연결 당시 변경 준비 표는22개 family'),
            (COMPILER,'현재 공통 표는 기존22개 순서',
            '현재 공통 표는 기존21개 순서','문단 스타일 v2 연결 당시 공통 표는 기존21개 순서')):
            text=q.text(path);_,rest=section(text,start,new_line)
            audit.inverse(rest.replace(new_line,old_line,1),contract_pins[path],'ONLY_CURRENT23_PREFIX_WITH_PREVIOUS22_HISTORY_RETAINED')
        profile=q.text(PROFILE);q.pin(DRIVER)
        for text in(prefix,s,p,profile):
            for marker in('367','369','370','371','868fresh/final868','공식158/249','P09/A12/A13 OPEN','Native011 미승인/미실행','SEARCH-020'):
                c.require(marker in text,'CURRENT_COUNTS_FAILURES_PHASE_AND_SEARCH020_BOUNDARIES_EXPLICIT')
        for marker in('selected_mask_text_splices','실행 레시피가 아니다','12개','23번째','whole_package_personal_data_removed=false','32pass','이전31개'):
            c.require(marker in profile,'ACTUAL_ANCHORS_NOT_SCALAR_RECIPES_AND_NO_SANITIZATION_OR_GATE_PROMOTION')
        for path,text in((SEARCH,s),(REPORT,p),(PROFILE,profile),(DISPATCH,q.text(DISPATCH)),(COMPILER,q.text(COMPILER))):
            for link in re.findall(r'\]\(([^)]+)\)',text):
                c.require(not link.startswith('http'),'ONLY_LOCAL_VERIFIED_EVIDENCE_LINKS');target=((c.ROOT/path).parent/link).resolve()
                c.require(target.is_relative_to(c.ROOT.resolve())and target.is_file(),'ALL_REFERENCED_CONTRACTS_AND_EVIDENCE_EXIST')
        q.finish();guard.check(force=True);row.update(state='PASS_COMMON23_MASK_CURRENT32_DOC_SYNC_NOT_RUNTIME_REPLAY_EXECUTION_NATIVE_SANITIZATION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,mutation_families=23,current_distinct_cases=32,
            new_cases=19,affected_cases=13,last_affected_rerun=1,last_retained=31,official_queue_accepted=158,official_queue_total=249,
            next_work='search020_detection_selection_and_qualified_actual_execution_storage_target')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'COMPILED_MASK_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
