"""391: external inspection/empty limits and prior catalog source evidence -> surgical docs, no runtime replay."""
import json
from pathlib import Path
import re
import time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import inspect_external_crossref_host as external

OUTPUT='implementation/p09/evidence/p09-361-external-crossref-host-sync391.v1.json'
DRIVER='tools/p09/sync_external_crossref_host.py'
STATE='CURRENT_STATE.md'
REPORT='implementation/p09/P09_CROSSREF_EXECUTION_READINESS.md'
GUIDE='implementation/p09/P09_EXTERNAL_CROSSREF_HOST_RUNBOOK.md'
SEARCH='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DETECT='implementation/p09/P09_PERSONAL_INFO_DETECTION_PROGRESS.md'
OLD_DOCS='implementation/p09/evidence/p09-361-current-crossref-prerequisites-sync381.v1.json'
OLD_PRODUCT_DOCS='implementation/p09/evidence/p09-361-personal-info-detection-product-sync379.v1.json'
CATALOG='implementation/p09/evidence/p09-361-personal-info-catalog-fixture-profile385.v1.json'
EMPTY='implementation/p09/evidence/p09-361-external-crossref-empty-limits390.v1.json'
ENTRY='implementation/p09/evidence/p09-361-external-crossref-host-inspection-run007.v1.json'
NATIVE='implementation/p09/evidence/p09-361-current-crossref-prerequisites380.v1.json'
CURRENT_MARKER='> 2026-10-21 P09 ACTIVE 실제 CROSSREF 실행 경계 재확인'
CATALOG_SOURCES={'crates/hwpx-package/Cargo.toml','crates/hwpx-package/src/document_import/search.rs',
    'crates/hwpx-package/src/document_import/search/personal_info.rs','crates/hwpx-package/src/document_import/search/personal_info/catalog.rs',
    'crates/hwpx-package/src/document_import/search/reviews/selector.rs','crates/hwpx-package/tests/personal_info_mask.rs',
    'crates/hwpx-package/tests/support/personal_info_catalog.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/source_search/personal_info.rs',
    'crates/product-cli/src/form_product_request/stored_source_search/personal_info.rs'}


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'EXTERNAL_HOST_SYNC_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_EXTERNAL_HOST_DOC_SYNC',own_cpu_selection=selection,
        user_external_inspection001_NOT_RUN_at_sync=True,actual_Cargo_Hangul_COM_or_child_replayed=False,
        fixed_eight_executed=False,native_startup_qualified=False,Native011_executed=False,accepted_count_delta=0,
        P09_gate='OPEN',P10_started=False,OS_parent_Job_or_security_settings_changed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        code=external.load_code_proof(q);empty=r.compact.unpack(q.json(EMPTY));entry=r.compact.unpack(q.json(ENTRY));catalog=r.compact.unpack(q.json(CATALOG))
        docs=q.json(OLD_DOCS);product_docs=q.json(OLD_PRODUCT_DOCS);native=q.json(NATIVE)
        expected={external.CODE:'f8dce9618217b420958ed48047c8782f6ce178f072c4f2e96cd06ce42c033fef',
            EMPTY:'4e9e57ba076092be29735dc08692e549c6fdbcabc8d6e36fd4676f4605b20e81',ENTRY:'ac9a5b961e595bc571942447e712533a40c63a7f3f7a0958a104bee3414e0d91',
            OLD_DOCS:'7b674a483387b7a39a26a177e04c184f1109d83705bba74d146096556ac71b51',
            OLD_PRODUCT_DOCS:'2ddadac05cde72decbe2845cc1e984061b4820f170c93e857e3e672d43598047',
            NATIVE:'2cc887cfbc1991084ca944c28815dfeb9bfec09fcd8b7be49829d0ea4e4107ca'}
        for path,sha in expected.items():c.require(q.snapshots[path]['sha256']==sha,'EXACT_IMMUTABLE_EXTERNAL_HOST_AND_PRIOR_DOCUMENT_BASELINES')
        c.require(code['cleanup']and code['fresh_inputs']==code['final_fresh_hashes']==200 and code['current_distinct_contracts']==24
            and code['retained_contracts']==23,'CURRENT24_CONTRACTS_LAST1_RETAIN23_NOT_CURRENT24_REPLAY')
        c.require(empty['state']=='PASS_ACTUAL_EMPTY_NATIVE7_WORKER1_LIMITS_AND_CLEANUP_NOT_JOBLESS_NATIVE_OR_GATE'
            and empty['fresh_inputs']==empty['final_fresh_hashes']==12 and empty['cleanup']
            and empty['actual_empty_resource_layout']['empty_jobs_closed']and not empty['native_or_worker_process_assigned'],
            'ACTUAL_EMPTY_JOB_RESOURCE_CONFIGURATION_NOT_PREASSIGNMENT_OR_NATIVE')
        c.require(entry['state']=='DENIED_EXTERNAL_HOST_PREREQUISITES_NO_NATIVE_STARTED'and entry['cleanup']
            and entry['fresh_inputs']==entry['final_fresh_hashes']==200
            and entry['observation']['prerequisites']['failed_prerequisites']==['caller_lifecycle_native_safe'],
            'ACTUAL_ENTRY_DENIAL_NOT_EXTERNAL_JOBLESS_SUCCESS')
        c.require(catalog['state']=='PASS_CATALOG_DEFAULT_NO_ENV1_EXPLICIT_INSTALLATION4_RETAINED28_CURRENT33_NOT_NATIVE_OR_GATE'
            and catalog['fresh_inputs']==catalog['final_fresh_hashes']==893 and catalog['external_final_fresh_hashes']==1
            and catalog['cleanup']and catalog['current_distinct_cases']==33 and catalog['last_executed_cases']==5
            and catalog['retained_cases']==28,'PRIOR385_SOURCE33_LAST5_RETAIN28_NOT_PRODUCT_CATALOG_OR_NATIVE')
        old_native={p['path']:p for p in native['source_pins']}
        for path,pin in sorted(old_native.items()):c.require(q.pin(path)==pin,'ORIGINAL_NATIVE_FACTORY_FIXED_EIGHT_AND_LIFECYCLE_GUARDS_UNCHANGED')
        latest={p['path']:p for p in code['source_pins']}
        for path in(external.SELF,external.MODULE,external.TEST):c.require(q.pin(path)==latest[path],'CURRENT_QUALIFIED_INSPECTION_ENTRY_BODY_UNCHANGED')
        catpins={p['path']:p for p in catalog['source_pins']}
        for path in sorted(CATALOG_SOURCES):c.require(q.pin(path)==catpins[path],'CATALOG_CORE_AND_EXISTING_EXPLICIT_RULE_V1_PRODUCT_BODIES_UNCHANGED')
        old={p['path']:p for p in docs['source_pins']};oldprod={p['path']:p for p in product_docs['source_pins']}
        state=q.text(STATE);start=state.index(CURRENT_MARKER)
        c.require(state.startswith('> 2026-10-21 P09 ACTIVE 외부 CROSSREF 호스트 사전검사 준비'),'ONE_NEW_EXTERNAL_INSPECTION_CURRENT_PREFIX')
        r.audit.inverse(state[start:],old[STATE],'ALL_PRIOR_NATIVE_FAILURES_PRODUCT_STATE_AND_USER_HISTORY_PRESERVED')
        report=q.text(REPORT);start=report.index('## 외부 호스트 사전검사 준비');end=report.index('## 현재 확인 결과',start)
        restored=(report[:start]+report[end:]).replace(
            '직접 실행 가능 답변은 외부 사전검사 준비 범위로 적용했다. 사용자에게 검사 명령을 전달했으며\n외부 실행001 결과를 기다린다. 이 답변으로 작업 스케줄러·상위 Job/보안 설정을 변경하거나\nNative011·문자 스타일6종을 실행하지 않는다. 원 고정8종도 전체 세션 자격 후의 조건부 범위다.',
            '외부 전용 호스트 준비 후 직접 실행 가능한지 사용자에게 질문했다. 답변은 아직 없으며 외부 프로세스·\n작업 스케줄러·Job/보안 설정을 변경하거나 Native를 실행하는 새 승인으로 해석하지 않는다.')
        r.audit.inverse(restored,old[REPORT],'ONLY_EXTERNAL_ANSWER_AND_NEW_INSPECTION_STATUS_ADDED_ORIGINAL_NATIVE_CONDITIONS_RETAINED')
        detection=q.text(DETECT);start=detection.index('## 설치 개인정보 형식 카탈로그');end=detection.index('## 현재 저장과 읽기 전용 제품 요청',start)
        r.audit.inverse(detection[:start]+detection[end:],oldprod[DETECT],'ALL_PRIOR_EXPLICIT_RULE_PRODUCT_V1_HISTORY_AND_CLAIM_BOUNDARIES_RETAINED')
        search=q.text(SEARCH);new='| SEARCH-020 | 개인정보 찾아 바꾸기 | 명시적 형식 source23·저장/읽기 전용 제품32+영향3와 원 설치64패턴 카탈로그 source27+영향6 검증, 전체 카탈로그 저장/제품 선택·Native 일치 의미·전체 계약·실제 변경/저장/target 미완료 |'
        previous='| SEARCH-020 | 개인정보 찾아 바꾸기 | 명시적 형식 탐지 source23·현재 저장/엄격한 읽기 전용 제품/결과 이동·선택 신규32+영향3 검증, 기본 형식 정책·전체 계약·실제 변경/저장/target 미완료 |'
        c.require(search.count(new)==1,'ONE_PERSONAL_CATALOG_SOURCE_STATUS_ROW');r.audit.inverse(search.replace(new,previous),oldprod[SEARCH],'ALL_OTHER18_SEARCH_FEATURE_STATUS_AND_HISTORY_UNCHANGED')
        guide=q.text(GUIDE);q.pin(DRIVER)
        for marker in('--inspect-only --inspection-run 1','관리자 권한은 필요 없으며','실제 프로세스 배정은 하지 않는다',
            '현재 고유24개','200fresh/final200','12fresh/final12','Native011 미승인/미실행','공식158/249','잔여91','P09/A12/A13 OPEN','목표ACTIVE'):
            c.require(marker in guide,'USER_COMMAND_AND_SOURCE_NATIVE_AUTHORITY_BOUNDARIES_EXPLICIT')
        future='implementation/p09/evidence/p09-361-external-crossref-host-inspection-run001.v1.json'
        for path,text in((GUIDE,guide),(REPORT,report),(DETECT,detection)):
            for link in re.findall(r'\]\(([^)]+)\)',text):
                if link.startswith('https://'):continue
                target=((c.ROOT/path).parent/link).resolve();c.require(target.is_relative_to(c.ROOT.resolve()),'DOC_LINK_WITHIN_PROJECT')
                relative=target.relative_to(c.ROOT.resolve()).as_posix()
                c.require(relative==future or target.is_file(),'ALL_EVIDENCE_LINKS_EXIST_EXCEPT_EXPLICIT_FUTURE_USER_INSPECTION001')
        row['user_external_inspection001_NOT_RUN_at_sync']=not(c.ROOT/future).exists()
        q.finish();guard.check(force=True);row.update(state='PASS_EXTERNAL_HOST_PREPARATION_AND_CATALOG_DOC_SYNC_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            next_work='observe_user_external001_and_connect_live_native_factory_without_replaying_old_runs_then_catalog_product_binding')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        row.update(error_type=type(error).__name__,error_code=external.safe_code(error))
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
