"""Selected MIXED number-control source/docs closure, never a promotion of the required review failure."""
import json,re,time
from types import SimpleNamespace as NS
import run_number_control_source_selection_recovery as target
import run_control_product_sync_recovery as retained
shared,c,a,tools,source=target.shared,target.c,target.a,target.tools,target.prior
OUTPUT='implementation/p09/evidence/p09-361-number-control-source-sync199.v1.json'
PROFILE='protocol/migrations/p09-source-number-control-replacement-v1.md'
DOCS={PROFILE,'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md','protocol/migrations/p09-text-control-product-request-v1.md'}
RETAINED=retained.RETAINED|{source.CORE,source.TEST,source.PARENT,source.DISCOVERY,source.GEOMETRY,source.BUNDLE,
    'crates/hwpx-package/src/document_import/reference_targets.rs','crates/hwpx-package/src/document_import/reference_targets/caption_source_state.rs',
    'crates/hwpx-package/src/document_import/reference_targets/caption_source_state/output/sequence.rs',
    'crates/hwpx-package/src/document_import/structure/caption_numbering_sequence.rs','crates/hwpx-package/src/document_import/structure/caption_text_batch.rs',
    'tools/p09/run_number_control_source_components.py','tools/p09/run_number_control_source_selection_recovery.py'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NUMBER_CONTROL_DOC_SYNC_IMMUTABLE_RUN_EXISTS');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NUMBER_CONTROL_SOURCE_DOC_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        original_required_review_case_still_failed=True,full_number_control_source_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);mixed=q.json(target.OUTPUT);failed=q.json(source.OUTPUT)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='9d03de8ada7504b1909c2fa89451f84c6b6f7d5d9fa9e004403a26d0d0b77f2a'
            and mixed['state']=='MIXED_NUMBER_CONTROL_SOURCE19_DIAGNOSTIC1_REQUIRED_REVIEW_CASE_UNRESOLVED'and mixed['cleanup']
            and mixed['fresh_inputs']==mixed['final_fresh_hashes']==721 and mixed['new_functional_source_cases_passed']==19
            and mixed['new_functional_source_cases_required']==20 and mixed['original_required_review_case_still_failed']
            and not mixed['full_number_control_source_qualified']and mixed['original_positive_review_test_unchanged'],'EXACT198_MIXED19_OF20_NOT_FULL_SOURCE_OR_PRODUCT_PASS')
        c.require(q.snapshots[source.OUTPUT]['sha256']=='fb2db6f720cc563578f668dd071946806c947e14b06b34687050fdb2454129b3'
            and failed['state']=='FAILED_NUMBER_CONTROL_SOURCE_COMPONENTS'and failed['cleanup']
            and sum(status=='ok'for _,status in failed['steps'][0]['tests'])==54,'ORIGINAL197_54PASS_TWO_FAILURES_PRESERVED')
        tools.good_step(mixed['steps'][0],{target.FIXED,target.DIAGNOSTIC})
        tested={p['path']:p for p in mixed['source_pins']};c.require(RETAINED<=tested.keys(),'SELECTED_MIXED_SOURCE_INPUTS_DECLARED_BY198')
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'SELECTED_SOURCE_STREAM_COMPILER_GUARDS_TESTS_AND_HELPERS_MATCH198')
        for name in sorted(DOCS):q.pin(name)
        q.pin('tools/p09/run_number_control_source_sync.py');progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        rows=re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M);c.require(len(rows)==len(set(rows))==19 and not set(rows)&{'011','012','015','016','017','018'},'EXACT19_P09_SEARCH_ROWS_EXCLUDE_P11')
        for text in(q.text(PROFILE),progress,q.text('CURRENT_STATE.md')[:12500]):
            c.require('source-selector-number-control-replacement/v1'in text and 'MIXED'in text and '721fresh/final721'in text and 'Coverage'in text
                and '158/249'in text and '91'in text and 'Native011'in text and 'P10'in text,'DOCS_MIXED_SOURCE_PROFILE_INPUTS_UNRESOLVED_COVERAGE_AND_UNCHANGED_GATES')
        for marker in('고유19개','성공 사례1개는 실패','54pass/2fail','삭제·완화·ignore하지 않았다','현재 저장/제품 요청',
            'guard3N','4N','기존 제품266개·공식249는 재실행하지 않았고','review 문단을 검증해 연결해야 한다'):
            c.require(marker in q.text(PROFILE),'REQUIRED_FAILURE_NOT_ERASED_QUALIFICATION_NOT_NARROWED_AND_NEXT_ACTUAL_REVIEW_JOIN')
        c.require('필수 review1개 실패/MIXED'in progress and 'complete number-stream 입력/출력 admission'in progress,'SEARCH009_ROW_AND_NEXT_REVIEW_ADMISSION_STAY_UNQUALIFIED')
        q.finish();guard.check(force=True);row.update(state='PASS_SELECTED_DOCS_SYNC_FOR_MIXED_NUMBER_CONTROL_SOURCE_NOT_FULL_SOURCE_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,source_functional_cases_retained=19,source_functional_cases_required=20,
            affected_control_cases_retained=36,diagnostic_cases_retained=1,old_cases_and_full721_inputs_replayed=False,
            next_work='implement_actual_review_bound_complete_number_stream_input_output_admission_and_shared_output_import')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'NUMBER_CONTROL_SOURCE_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
