"""Selected review-bound source/docs closure, no67-case/Cargo/723-input replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_number_control_review_components as target
import run_number_control_source_sync as retained
shared,c,a,tools=target.shared,target.c,target.a,target.tools
OUTPUT='implementation/p09/evidence/p09-361-number-control-review-sync201.v1.json'
PROFILE='protocol/migrations/p09-source-number-control-replacement-v1.md'
DOCS=retained.DOCS
RETAINED=retained.RETAINED|target.NEW|target.CHANGED|{'tools/p09/run_number_control_review_components.py'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NUMBER_CONTROL_REVIEW_SYNC_IMMUTABLE_RUN_EXISTS');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NUMBER_CONTROL_REVIEW_DOC_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        number_control_store_product_native_or_gate_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT);baseline=q.json(target.prior.OUTPUT)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='a8a32399ec72474a03f8672dc6530e661b0108f1c09e941232460c2808250450'
            and passed['state']=='PASS_REVIEW_BOUND_NUMBER_SOURCE30_DIAGNOSTIC1_AFFECTED36_NOT_STORE_PRODUCT_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==723 and passed['total_executed_cases']==67
            and passed['original_required_review_case_now_passed']and passed['actual_form_review_identity_not_caller_allowlist']
            and passed['one_shared_output_form_fields_review_numbering_import'],'EXACT200_67PASS_FRESH_REVIEW_IDENTITY_AND_SHARED_OUTPUT_NOT_NATIVE_OR_PRODUCT')
        c.require(q.snapshots[target.prior.OUTPUT]['sha256']=='9d03de8ada7504b1909c2fa89451f84c6b6f7d5d9fa9e004403a26d0d0b77f2a'
            and baseline['state']=='MIXED_NUMBER_CONTROL_SOURCE19_DIAGNOSTIC1_REQUIRED_REVIEW_CASE_UNRESOLVED'
            and baseline['original_required_review_case_still_failed'],'ORIGINAL198_MIXED_HISTORY_PRESERVED_NOT_OVERWRITTEN')
        tested={p['path']:p for p in passed['source_pins']};c.require(RETAINED<=tested.keys(),'SELECTED_REVIEW_SOURCE_INPUTS_DECLARED_BY200')
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'SELECTED_SOURCE_GUARDS_LEGACY_BODY_BRANCH_SHARED_OUTPUT_REQUESTS_AND_TESTS_MATCH200')
        target.inverse(q,{p['path']:p for p in baseline['source_pins']});tools.good_step(passed['steps'][0],target.expected(q))
        for name in sorted(DOCS):q.pin(name)
        q.pin('tools/p09/run_number_control_review_sync.py');progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        rows=re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M);c.require(len(rows)==len(set(rows))==19 and not set(rows)&{'011','012','015','016','017','018'},'EXACT19_P09_SEARCH_ROWS_EXCLUDE_P11')
        for text in(q.text(PROFILE),progress,q.text('CURRENT_STATE.md')[:12500]):
            c.require('source-selector-number-control-replacement/v1'in text and '67pass'in text and '723fresh/final723'in text
                and 'import_review_bound'in text and 'output_review_import'in text and '158/249'in text and '91'in text and 'Native011'in text and 'P10'in text,
                'DOCS_REVIEW_SOURCE_PROFILE_PASSES_SHARED_OUTPUT_AND_UNCHANGED_GATES')
        for marker in('초기 실패와 원인 분리','198 당시 전체 source 자격은 false','원197 실패·198 MIXED',
            'source-review-observations-v2','review_body_inventory_sha256','pointer identity','caller paragraph allowlist',
            'None일 때 JSON에서 생략','기존 strict Coverage 거부','추가 재수입을 없앴다',
            'AutoNumber/NewNumber의 현재 저장 서비스·엄격한 제품 JSON 연결'):
            c.require(marker in q.text(PROFILE),'REAL_REVIEW_RECOVERY_LEGACY_REJECTIONS_HISTORICAL_FAILURES_AND_REMAINING_STORE_PRODUCT_BOUNDARY')
        c.require('번호 저장/제품·다른 제어·전체 실행 미완료'in progress and '번호 제어의 현재 저장 서비스·엄격한 제품 JSON 연결'in progress,
            'SEARCH009_ROW_AND_NEXT_NUMBER_CONTROL_STORE_PRODUCT_WORK')
        q.finish();guard.check(force=True);row.update(state='PASS_SELECTED_NUMBER_CONTROL_REVIEW_DOC_SYNC_NOT_STORE_PRODUCT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,original_number_functional_cases_retained=20,new_review_admission_cases_retained=10,
            legacy_diagnostic_cases_retained=1,affected_control_cases_retained=36,old_cases_and_full723_inputs_replayed=False,
            next_work='SEARCH009_number_control_current_store_strict_product_other_families_full_contract_native_and_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'NUMBER_CONTROL_REVIEW_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
