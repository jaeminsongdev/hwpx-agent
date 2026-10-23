"""Selected current code and document closure for explicit source v2; no tests or full592-input replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_regex_insertion_linear as linear
base=linear.base
shared,c,a=linear.shared,linear.c,linear.a
OUTPUT='implementation/p09/evidence/p09-361-regex-insertion-sync121.v1.json'
PROFILE='protocol/migrations/p09-source-selector-regex-insertion-v2.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-source-selector-regex-replacement-v1.md','protocol/migrations/p09-regex-replacement-product-request-v1.md'}
RETAINED={'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/search.rs',
    'crates/hwpx-package/src/document_import/search/replacement.rs','crates/hwpx-package/src/document_import/search/replacement/atoms/review.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/regex/template.rs','crates/hwpx-package/src/document_import/search/replacement/output.rs',
    'crates/hwpx-package/src/document_import/search/reviews/selector.rs','crates/hwpx-package/src/patch/leaf_scalar_ranges.rs',
    'crates/hwpx-package/src/patch/leaf_text.rs','crates/product-cli/src/reference_validation_product/source.rs',
    base.prior.STORED,base.prior.PRODUCT,base.prior.SELECTOR,base.prior.TEST,base.prior.OLD,
    'tools/p09/run_regex_insertion_components.py','tools/p09/run_regex_insertion_recovery.py','tools/p09/run_regex_insertion_linear.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','tools/p09/run_source_note_api_components.py'}


def good_step(step,names):
    c.require(step['exit_code']==0 and {n for n,s in step['tests']}==names and len(step['tests'])==len(names)
        and all(s=='ok'for n,s in step['tests'])and step['diagnostics']==[]and step['panic_locations']==[]and step['safe_error_variants']==[],
        'EXACT_COMPLETED_TEST_IDENTITIES_WITHOUT_IGNORES_OR_DIAGNOSTICS')
    job=step['owned_job'];limits=job['limits_readback']
    c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0
        and limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384 and limits['kill_on_close'],
        'ORIGINAL_ONE_CPU2_HARD_CAP_PRIORITY_AND_OWNED_JOB_TERMINAL_CLEANUP')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGEX_INSERTION_SYNC_IMMUTABLE_RUN_EXISTS');selection=base.prior.prior.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REGEX_INSERTION_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        failed=q.json(base.OUTPUT);recovered=q.json(linear.prior.OUTPUT);passed=q.json(linear.OUTPUT)
        for name,digest in[(base.OUTPUT,'209ef610f9b8f4024b12eec7edc398658637c00274f0415289e7c67493b929c0'),
            (linear.prior.OUTPUT,'b6ef94d5d05be689f4f73ebd4490df9cecfc24e14a55ac5971215e9042ec144d'),
            (linear.OUTPUT,'9488aacb48a5217973ab47b17411e5b6fbac23d92c49f17df21172880d4322ea')]:
            c.require(q.snapshots[name]['sha256']==digest,'EXACT_ORIGINAL_FAILURE_RECOVERY_AND_LINEAR_RUN_IDENTITIES')
        c.require(failed['state']=='FAILED_REGEX_INSERTION_COMPONENTS'and failed['cleanup']and recovered['state'].startswith('PASS_')and recovered['cleanup']
            and recovered['fresh_inputs']==recovered['final_fresh_hashes']==591 and passed['state'].startswith('PASS_')and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==592,'PRESERVED_FAILURE_AND_AUTHORITATIVE_COMPLETE_RECOVERY_INPUT_CLOSURES')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in recovered['source_pins']};original={p['path']:p for p in failed['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_SELECTED_CODE_AUTHORIZATION_WRITER_GUARDS_AND_TESTS_MATCH_LINEAR_PASS')
        linear.inverse(q,old);linear.prior.test_inverse(q,original);base.boundaries(q)
        current={'regex_insertions::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.TEST))}
        first=failed['steps'][0];retained={n for n,s in first['tests']if s=='ok'};retry={n for n,s in first['tests']if s=='FAILED'}
        c.require(len(retained)==78 and len(retry)==8 and not(retained&retry)and len(current)==19,'EXACT_ORIGINAL_SEVENTY_EIGHT_PASSES_EIGHT_FAILURES_NINETEEN_CURRENT_NEW_CASES')
        good_step(recovered['steps'][0],retry|{'regex_insertions::'+linear.prior.NEW_TEST});good_step(recovered['steps'][1],base.prior.expected(q))
        good_step(passed['steps'][0],current)
        c.require(len(retained|retry|{'regex_insertions::'+linear.prior.NEW_TEST})==87 and len(base.prior.expected(q))==29
            and passed['total_distinct_cases']==116 and passed['retained_original_cases']==97 and not passed['previous_original_cases_reexecuted'],
            'ONE_HUNDRED_SIXTEEN_DISTINCT_COMPONENTS_NOT_A_CURRENT_SINGLE_RUN_OR_QUEUE_ACCEPTANCE')
        for name in sorted(DOCS):q.pin(name)
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md');profile=q.text(PROFILE)
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_ROWS_RETAINED')
        for marker in('별도 빈 일치 source v2 통과','v2 저장/제품 연결·전체 계약 미완료','19pass·592fresh/final592','고유116개',
            '기존97개·공식249 대기열은 반복하지 않았다','다음은 빈 일치 source v2의 현재 저장/엄격한 제품 연결'):
            c.require(marker in progress,'PRECISE_CURRENT_SOURCE_ONLY_SEARCH_PROGRESS_AND_NEXT_BOUNDARY')
        for marker in('RightOriginalPointElseLeftFirstEmptyText','One suffix minimum','One protected output transaction',
            'empty query remains invalid','One direct-child edge inventory','does not repeatedly insert','116 distinct cases',
            'original97 results are retained','592 fresh/final592','102.328 seconds','26.500 seconds','1.77 seconds','24.891 seconds',
            '29.31%','35.9864%','1647.82 MiB','current storage and strict product JSON is next','unapproved/unexecuted'):
            c.require(marker.lower()in profile.lower(),'SOURCE_PROFILE_COORDINATES_POLICY_LIMITS_RESOURCES_AND_PENDING_PRODUCT_NATIVE_QUALIFICATION')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-source-selector-regex-insertion-v2.md'in q.text(name),'EXISTING_V1_PROFILES_LINK_V2_WITHOUT_WIDENING_OLD_REQUESTS')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 정규식 치환 저장과 제품 요청',1)[0]
        for marker in('19pass·592fresh/final592','고유116개','다음은 이 명시적 v2 빈 일치 후보의 현재 저장 서비스와 엄격한 제품 요청 연결',
            '공식158/249','잔여91','next165','P09/A12/A13 OPEN','P10미시작','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_IMPLEMENTATION_STATUS_AND_OFFICIAL_QUEUE_GATE_BOUNDARY')
        source=q.text('crates/product-cli/src/reference_validation_product/source.rs')
        c.require('hwpx-agent.product.reference-source-assessment/v12'in source and 'validation_report: None'in source
            and all('UnresolvedReferenceStage::'+n in source for n in('OtherTargetFamilies','ReferenceEdgeSemantics','CompleteAuxiliaryState','DocumentFlow')),
            'REFERENCE_SOURCE_API_STILL_INCOMPLETE_NOT_GATE_PASS')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_REGEX_INSERTION_CODE_DOCUMENT_SYNC_NOT_STORED_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_v2_cases=19,retained_original_cases=97,total_distinct_cases=116,entire_592_input_set_reaudited=False,tests_reexecuted=False,
            next_work='Explicit_v2_zero_width_current_stored_and_strict_product_binding_then_remaining_full_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REGEX_INSERTION_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_INSERTION_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
