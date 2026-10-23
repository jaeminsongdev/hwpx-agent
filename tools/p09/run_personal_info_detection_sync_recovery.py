"""376: separate document baseline from runtime pins; retain375 metadata failure, no Rust replay."""
import json,re,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_personal_info_detection as base
shared,c,a,tools,compact,harness,audit=r.shared,r.c,r.a,r.tools,r.compact,r.harness,r.audit
OUTPUT='implementation/p09/evidence/p09-361-personal-info-detection-sync-recovery376.v1.json';DRIVER='tools/p09/run_personal_info_detection_sync_recovery.py'
RUN='implementation/p09/evidence/p09-361-personal-info-detection-recovery374.v1.json';RECOVERY='tools/p09/run_personal_info_detection_recovery.py'
STATE='CURRENT_STATE.md';SEARCH='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
REPORT='implementation/p09/P09_PERSONAL_INFO_DETECTION_PROGRESS.md';PROFILE='protocol/migrations/p09-source-personal-info-detection-v1.md'
OLD_ROW='| SEARCH-020 | 개인정보 찾아 바꾸기 | 탐지/선택·치환·개인정보 정책 검증 필요 |'
NEW_ROW='| SEARCH-020 | 개인정보 찾아 바꾸기 | 명시적 형식 탐지/읽기 전용 원본 선택 core 신규23+영향3 검증, 현재 저장/제품·기본 형식 정책·전체 계약·실제 변경/저장/target 미완료 |'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'PERSONAL_INFO_DETECTION_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PERSONAL_INFO_DETECTION_SYNC',own_cpu_selection=selection,Cargo_tests_DB_or_Native_replayed=False,
        document_and_changed_source_audit_not_fresh_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False,
        whole_package_personal_data_removed=False,native_format_policy_or_execution_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        metadata_failure=q.json('implementation/p09/evidence/p09-361-personal-info-detection-sync375.v1.json')
        c.require(q.snapshots['implementation/p09/evidence/p09-361-personal-info-detection-sync375.v1.json']['sha256']=='7bfbbba57db7721b6212552d0e581ece9b9d055c6187bd4b32ef6f8ef14e1211'
            and metadata_failure['cleanup']and metadata_failure['error_type']=='KeyError'and metadata_failure['final_fresh_hashes']is None,'EXACT375_DOCUMENT_RUNTIME_PIN_MISMATCH_NOT_RUNTIME_OR_PRODUCT_FAILURE_RETAINED')
        q.pin('tools/p09/run_personal_info_detection_sync.py')
        prior_doc=q.json('implementation/p09/evidence/p09-361-personal-info-mask-sync364.v1.json')
        c.require(q.snapshots['implementation/p09/evidence/p09-361-personal-info-mask-sync364.v1.json']['sha256']=='23b83be5e323a5ffd72dd77ee785336d0ab5aa5f7b59ddf73f206d302c98dae2'and prior_doc['cleanup'],'EXACT364_DOCUMENT_CONTRACT_BASELINE_NOT_COMPILE_INPUT')
        document_pins={p['path']:p for p in prior_doc['source_pins']}
        run=compact.unpack(q.json(RUN));failed=compact.unpack(q.json(base.OUTPUT));docs=q.json(base.DOCS)
        for path,digest in((RUN,'5175b077d5a205afab069064fc561fb06954476acc08ef2d401da3e042e1c9ba'),
            (base.OUTPUT,'7fb46d31b2255f7b90d46bdcefc0235e6b470c58a20ed35d43c5870a521298e2'),
            (base.DOCS,'bf4afac8be084aecb7837434a017d8d4bedcc28f891dc64c218d92d5818656a4')):
            c.require(q.snapshots[path]['sha256']==digest,'EXACT_IMMUTABLE_DETECTION_RUNTIME_FAILURE_AND_PRIOR_DOC_RECORDS')
        c.require(run['cleanup']and run['fresh_inputs']==run['final_fresh_hashes']==875 and run['retained_cases']==25 and run['current_distinct_cases']==26
            and len(run['steps'])==1 and run['steps'][0]['diagnostics']==[],'EXACT374_ONLY_REPAIRED1_PASS_RETAINED25_WITHOUT_WARNINGS')
        case='detection::control_and_paragraph_barriers_are_not_joined_into_private_candidates';tools.good_step(run['steps'][0],{case})
        c.require(failed['cleanup']and failed['fresh_inputs']==failed['final_fresh_hashes']==873 and len(failed['steps'])==1
            and len(failed['steps'][0]['tests'])==26 and [(n,v)for n,v in failed['steps'][0]['tests']if v!='ok']==[(case,'FAILED')]
            and failed['steps'][0]['safe_error_variants']==['Body'],'EXACT373_ORIGINAL25_PASS_AND_INVALID_TAB_BODY_FAILURE_PRESERVED')
        pins={p['path']:p for p in run['source_pins']};sources=base.NEW|base.CHANGED|{RECOVERY,'tools/p09/named_style_verification_runtime.py',
            'crates/hwpx-package/src/document_import/search/reviews/selector.rs','crates/hwpx-package/src/document_import/search/captures.rs',
            'crates/hwpx-package/src/document_import/search/selector.rs','crates/hwpx-package/src/document_import/search/navigation.rs',
            'crates/hwpx-package/src/document_import/search/replacement/atoms/personal_info.rs','crates/hwpx-package/src/document_import/protection.rs',
            'crates/hwpx-package/src/text_flow.rs','crates/hwpx-package/tests/support/review_scope_fixture.rs',
            'crates/hwpx-package/tests/support/search_definition_fixture.rs','docs/04_feature_catalog/contracts/03_search_contracts.md'}
        for path in sorted(sources):
            q.pin(path)
            if path in pins:c.require(q.snapshots[path]==pins[path],'CURRENT_DETECTION_TESTS_ORIGINAL_INDEX_MAPPING_PROTECTION_MASK_AND_GUARDS_MATCH374')
            else:
                c.require(path=='docs/04_feature_catalog/contracts/03_search_contracts.md','ONLY_EXPLICIT_DOCUMENT_CONTRACT_OUTSIDE_RUNTIME_BASELINE')
                c.require(q.snapshots[path]==document_pins[path],'GENERIC_CONTRACT_MATCHES_SEPARATE364_DOCUMENT_BASELINE_NOT_RUNTIME_REQUALIFICATION')
        original=compact.unpack(q.json(base.BASE));base.inverse(q,{p['path']:p for p in original['source_pins']})
        c.require(len(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(base.TEST)))==23 and '#[ignore]'not in q.text(base.TEST),'EXACT_CURRENT23_DETECTION_CASES_WITHOUT_IGNORES')
        c.require(run['elapsed_seconds']==145.343 and run['system_CPU_max']==74.76 and 36.5546<run['available_RAM_min_percent']<36.5547
            and run['steps'][0]['owned_job']['last_job_accounting']['peak_job_private_mib']==1893.8,'EXACT374_RESOURCE_SCOPE_NOT_FREEZE_FIX')
        old={p['path']:p for p in docs['source_pins']};state=q.text(STATE);marker='> 2026-10-21 P09 ACTIVE 최신 개인정보 마스킹의 공통 계획 연결'
        c.require(state.startswith('> 2026-10-21 P09 ACTIVE 최신 개인정보 형식 탐지와 원본 선택')and state.count(marker)==1,'ONE_CURRENT_DETECTION_PREFIX')
        prefix=state[:state.index(marker)];audit.inverse(state[state.index(marker):],old[STATE],'ALL_PREVIOUS_COMMON_MASK_FAILURES_AND_PHASE_HISTORY_RETAINED')
        search=q.text(SEARCH);start=search.index('## 개인정보 형식 탐지와 원본 선택\n');end=search.index('## 개인정보 마스킹의 공통 변경 계획\n',start);section=search[start:end]
        c.require(search.count(NEW_ROW)==1,'ONLY_SEARCH020_ROW_ADVANCED');audit.inverse((search[:start]+search[end:]).replace(NEW_ROW,OLD_ROW),old[SEARCH],'ALL_OTHER18_SEARCH_ROWS_AND_PREVIOUS_PROGRESS_UNCHANGED')
        report=q.text(REPORT);profile=q.text(PROFILE);q.pin(DRIVER)
        for text in(prefix,section,report,profile):
            for marker in('373','374','875fresh/final875','이전25보존','공식158/249','P09/A12/A13 OPEN','Native011 미승인/미실행','문자 스타일6종'):
                c.require(marker in text,'NEW23_AFFECTED3_RETAINED25_FAILURES_AND_PHASE_BOUNDARIES_EXPLICIT')
        for marker in('read_only','PrivateInfo.ini','1~16','leftmost','개인정보 값별 해시','whole_package_personal_data_removed',
            '현재 저장 권한','기본 형식 정책','SourcePersonalInfoDetectionSelection','regex/DFA','target match_set/semantic_diff/reopen'):
            c.require(marker in profile,'EXPLICIT_FORMATS_AND_EXACT_SOURCE_SELECTION_NOT_NATIVE_BUILTINS_SERVICE_EXECUTION_OR_SANITIZATION')
        for path,text in((SEARCH,section),(REPORT,report),(PROFILE,profile)):
            for link in re.findall(r'\]\(([^)]+)\)',text):
                if link.startswith('https://'):
                    c.require(link in {'https://help.hancom.com/hoffice/multi/ko_kr/hwp/security/user_info_protection/protection%28search_hide%29.htm',
                        'https://help.hancom.com/hoffice/multi/ko_kr/hwp/security/user_info_protection/protection%28user_info_option%29.htm'},'ONLY_READ_OFFICIAL_HANCOM_HELP_LINKS');continue
                target=((c.ROOT/path).parent/link).resolve();c.require(target.is_relative_to(c.ROOT.resolve())and target.is_file(),'LOCAL_DETECTION_EVIDENCE_AND_CONTRACT_LINKS_EXIST')
        q.finish();guard.check(force=True);row.update(state='PASS_SOURCE_DETECTION23_AFFECTED3_DOC_SYNC_NOT_STORED_PRODUCT_NATIVE_SANITIZATION_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_detection_cases=23,affected_original_cases=3,current_distinct_cases=26,last_repaired_cases=1,retained_cases=25,mutation_families=23,
            official_queue_accepted=158,official_queue_total=249,next_work='current_stored_access_strict_read_only_product_then_native_format_policy_and_actual_execution')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'DETECTION_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
