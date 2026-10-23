"""Selected source/docs closure for3 current +78 retained; no Cargo/test/full654 replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_unicode_normalization_failed_cases as target
base=target.base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-unicode-normalization-sync160.v1.json'
PROFILE='protocol/migrations/p09-source-unicode-normalization-v1.md'
DOCS={PROFILE,'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md','protocol/migrations/p09-source-search-index-v1.md'}
RETAINED={base.ROOT+'normalization.rs',base.ROOT+'extract.rs',base.ROOT+'replacement.rs',base.ROOT+'replacement/output.rs',
    base.ROOT+'replacement/atoms/review.rs','crates/hwpx-package/src/document_import/search.rs',
    'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/fields.rs',
    'crates/product-cli/src/reference_validation_product/source.rs','Cargo.lock','Cargo.toml',
    'crates/hwpx-package/tests/support/search_definition_fixture.rs','crates/hwpx-package/tests/support/review_scope_fixture.rs',
    'crates/hwpx-package/tests/support/review_cell_output_fixture.rs','crates/hwpx-package/tests/support/document_import_review_assembly_fixture.rs',
    'crates/hwpx-package/tests/document_import_search_atom_replacement.rs','crates/hwpx-package/tests/document_import_search_review_replacement.rs',
    'crates/hwpx-package/tests/document_import_review_selector_replacement.rs','crates/hwpx-package/tests/document_import_regex_replacement.rs',
    'crates/hwpx-package/tests/document_import_review_selector.rs','tools/p09/run_unicode_normalization_components.py',
    'tools/p09/run_unicode_normalization_recovery.py','tools/p09/run_unicode_normalization_failed_cases.py'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'UNICODE_SYNC_IMMUTABLE_RUN_EXISTS');selection=base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_UNICODE_NORMALIZATION_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT);failed=q.json(target.previous.OUTPUT);original=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='d8b44843bb5ecc8959625c7614d3ac126d5b75f927dd2347173ccda29fe7899a'
            and passed['state']=='PASS_UNICODE_3_REPAIRED_78_RETAINED_NOT_STORED_PRODUCT_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==654 and passed['total_distinct_cases']==81
            and not passed['previous_78_passes_reexecuted']and passed['production_unchanged_after157'],'EXACT_NEW3_RETAINED78_SOURCE_CLOSURE')
        c.require(q.snapshots[target.previous.OUTPUT]['sha256']=='ea53e63363b1b407028dc5f76af1421aa3873e1d960cddb00e27415984488628'
            and failed['cleanup']and failed['steps'][0]['exit_code']==101,'EXACT_ORIGINAL78_PASS_THREE_FAILURES_PRESERVED')
        tested={p['path']:p for p in passed['source_pins']};failed_pins={p['path']:p for p in failed['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'SELECTED_CURRENT_IMPLEMENTATION_POLICY_FIXTURE_AND_TEST_INPUTS_MATCH_159')
        target.repairs(q,failed_pins);base.inverse(q,{p['path']:p for p in original['source_pins']});cases=base.expected(q)
        retained={n for n,s in failed['steps'][0]['tests']if s=='ok'}
        c.require(len(retained)==78 and retained|target.CASES==cases and len(cases)==81,'EXACT_DISTINCT_24_NEW_57_AFFECTED_CASE_IDENTITIES')
        base.good_step(passed['steps'][0],target.CASES)
        job=failed['steps'][0]['owned_job'];limits=job['limits_readback']
        c.require(failed['steps'][0]['cleanup']and job['owned_tree_empty']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0
            and limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,
            'RETAINED78_PASS_RESULTS_HAVE_ORIGINAL_LIMITS_AND_TERMINAL_JOB')
        for name in sorted(DOCS):q.pin(name)
        profile=q.text(PROFILE);progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md');latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 제어 내부 서식 해석 누락 수정',1)[0]
        for marker in('source-selector-unicode-normalization/v1','FirstOriginalRunRetainAllRuns','Unicode 17.0.0','최소 연속 편집 성분',
            '654fresh/final654','신규24+영향기존57=고유81개','87.469','3.437','0.42','580.07MiB','33.2%',
            '현재 저장 서비스·엄격한 제품 JSON','공식158/249','Native011'):
            c.require(marker in profile,'PRECISE_SOURCE_NORMALIZATION_CONTRACT_EVIDENCE_AND_REMAINING_BOUNDARY')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19 and
            '| SEARCH-022 | Unicode 정규화 | 실제 원본 4형태/4범위·최소 성분/서식 보존 core 고유81개 검증, 현재 저장/제품·전체 계약 미완료 |'in progress,
            'ALL19_ROWS_AND_PRECISE_PARTIAL_SEARCH022_STATUS')
        for marker in('654fresh/final654','고유81개','다음은 이 Unicode 후보의 현재 저장 서비스·엄격한 제품 JSON 연결',
            '공식158/249','P09/A12/A13 OPEN','목표ACTIVE','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in latest,'CURRENT_STATE_COUNTS_NEXT_TASK_AND_ORIGINAL_PHASE_BOUNDARIES')
        c.require('p09-source-unicode-normalization-v1.md'in q.text('protocol/migrations/p09-source-search-index-v1.md'),'EXISTING_NFC_PROFILE_LINKS_DISTINCT_ACTUAL_SOURCE_TRANSFORM')
        q.pin(Path(__file__).absolute().relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_UNICODE_NORMALIZATION_SELECTED_SOURCE_DOCS_SYNC_NOT_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_cases=3,retained_cases=78,total_distinct_cases=81,new_source_cases=24,affected_source_cases=57,
            source654_or_Cargo_or_passed_tests_reexecuted=False,old_common_bodies_and_failed_oracle_inverses_rechecked=True,
            next_work='Current_stored_service_strict_product_request_and_full_SEARCH022_contract_binding')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'UNICODE_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_UNICODE_SYNC_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
