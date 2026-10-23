"""Retain50 passes, remove one unused test import, compile-check only and close scoped docs."""
import json,re,subprocess,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_search_selector_components as base
harness,shared,c,a=base.harness,base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-search-selector-closure091.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',
    'protocol/migrations/p09-source-index-scope-selector-v1.md','protocol/migrations/p09-source-search-index-v1.md',
    'protocol/migrations/p09-review-literal-product-request-v3.md')
RETAINED={base.CORE,base.MODULE,'crates/hwpx-package/src/document_import/search/scope.rs',
    'crates/hwpx-package/src/document_import/search/normalization.rs','crates/hwpx-package/src/document_import/search/extract.rs',
    'crates/hwpx-package/src/document_import/search/reviews.rs','crates/hwpx-package/src/document_import/structure.rs',
    'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import.rs',
    'crates/hwpx-package/tests/support/document_import_field_fixture.rs',
    'crates/hwpx-package/tests/support/document_import_review_assembly_fixture.rs',
    'crates/hwpx-package/tests/support/review_cell_output_fixture.rs',
    'tools/p09/run_search_selector_components.py','tools/p09/run_source_note_api_components.py',
    'Cargo.toml','Cargo.lock','rust-toolchain.toml','crates/hwpx-package/Cargo.toml'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SEARCH_SELECTOR_CLOSURE_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SEARCH_SELECTOR_CLOSURE',steps=[],actual_Cargo=True,actual_tests=False,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed,previous=q.json(base.OUTPUT),q.json(base.PRIOR)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='f20ba266c903118cbaac7e74f6dfd4747a0b007621be2ca617601f4bd5c08f95'
            and q.snapshots[base.PRIOR]['sha256']=='3905c914aea2a4f55b241675b7fa120615a0530b619c9763979b0dc80cd392c4','EXACT_SELECTOR_FIFTY_AND_PRIOR_PRODUCT_PASS_RESULTS')
        c.require(passed['state']=='PASS_SOURCE_SELECTOR_TWELVE_NEW_THIRTY_EIGHT_AFFECTED_NOT_STORED_PRODUCT_NATIVE_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==511
            and passed['new_source_cases']==12 and passed['affected_cases']==38 and passed['total_executed_cases']==50,'EXACT_FIFTY_PASS_INPUT_CLOSURE')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in previous['source_pins']}
        names=RETAINED|{'crates/hwpx-package/tests/'+target+'.rs'for target in base.TARGETS[1:]}
        for name in sorted(names):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_SOURCE_MATCHER_PROOF_AND_EXISTING_TESTS_MATCH_PASS')
        q.pin(base.TEST);text=q.text(base.TEST)
        c.require(text.count('BoundedZipReader,document_import')==1,'EXACT_ONLY_UNUSED_PACKAGE_LIMITS_IMPORT_REMOVAL')
        base.prior.prior.base.prior.audit.inverse(text.replace('BoundedZipReader,document_import','BoundedZipReader,PackageLimits,document_import'),tested[base.TEST],
            'ENTIRE_NEW_TEST_FILE_RECONSTRUCTS_PASS_SOURCE_ALL_TWELVE_BODIES_UNCHANGED')
        base.inverse(q,old);groups=[base.test_names(q,t)for t in base.TARGETS];expected=set().union(*groups)
        c.require(tuple(map(len,groups))==(12,24,6,8)and len(expected)==50,'EXACT_RETAINED_FIFTY_TEST_IDENTITIES')
        c.require(len(passed['steps'])==1,'ONE_ORIGINAL_SERIAL_SELECTOR_COMMAND');step=passed['steps'][0]
        c.require(step['exit_code']==0 and len(step['tests'])==50 and {n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])
            and step['panic_locations']==[] and len(step['diagnostics'])==2 and step['diagnostics'][0]=='warning: unused import: `PackageLimits`',
            'RETAIN_ORIGINAL_FIFTY_PASSES_AND_UNUSED_IMPORT_WARNING_NOT_RELABELED')
        job=step['owned_job'];c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']
            and job['last_job_accounting']['active_processes']==0,'ORIGINAL_SELECTOR_JOB_TERMINAL_EMPTY_CLOSED')
        for name in DOCS:q.pin(name)
        progress=q.text(DOCS[1]);c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_ROWS_RETAINED')
        for marker in ('50pass·511fresh/final511','검색 뒤','실제 문자열 창을 먼저 잘라','전체 제품 SearchScopeSelector 완료가 아니다',
            '현재 stored revision/head/source 결속','cargo check만','새 범위의 제품 연결/전체 검색 계약 미완료'):
            c.require(marker in progress,'PROGRESS_SOURCE_SCOPE_PASS_NOT_FULL_SELECTOR_PRODUCT_COMPLETION')
        profile=q.text(DOCS[2])
        for marker in ('not the completed product','actual graph section IDs','actual graph NodeCommon.node_id',
            'before regex anchors','not UTF-8/XML byte offsets','NodeSet','Section','Selection','Document',
            '50 total,511 fresh/final511','does not replay the50 tests','Native011 unapproved/unexecuted','P09/A12/A13 OPEN'):
            c.require(marker in profile,'PRECISE_SCOPE_IDENTITIES_COORDINATES_WARNING_AND_OPEN_PRODUCT_BOUNDARY')
        for name in DOCS[3:]:c.require('p09-source-index-scope-selector-v1.md'in q.text(name),'EXISTING_PROFILES_LINK_SEPARATE_SOURCE_SELECTOR')
        state=q.text(DOCS[0]).split('> 2026-10-20 P09 ACTIVE 최신 v3 제품 요청',1)[0]
        for marker in ('50pass·511fresh/final511','91.625초','25.875초','27.93%','27.0931%','5.0637%',
            '전체 SearchScopeSelector 완료로 취급하지 않는다','공식158/249','잔여91','Native011 미승인/미실행','P10미시작'):
            c.require(marker in state,'CURRENT_SOURCE_SELECTOR_COUNTS_RESOURCE_AND_NATIVE_BOUNDARY')
        env=base.prior.prior.base.prior.audit.environment()
        print(json.dumps(dict(state='SELECTOR_CLOSURE_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),retained_passes=50,
            only_unused_test_import_removed=True,tests_to_reexecute=0)),flush=True)
        harness.run_one('selector_target_compile_check_only_no_test_replay',[harness.CARGO,'check','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','document_import_search_selector'],set(),guard,env,row,observe_capture=base.prior.prior.snapshot)
        c.require(row['steps'][0]['diagnostics']==[],'CLEAN_SELECTOR_TARGET_COMPILE_CHECK_NO_DIAGNOSTICS')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_SELECTOR_FIFTY_RETAINED_WARNING_FREE_CHECK_AND_DOCUMENT_CLOSURE_NOT_PRODUCT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,retained_source_cases=50,new_source_cases=12,affected_cases=38,
            test_bodies_and_source_semantics_unchanged=True,only_unused_import_removed=True,entire_511_input_set_reaudited=False,
            full_selector_product_revision_or_native_qualified=False,resource_policy_unchanged=True,
            next_work='Authenticated_selector_discovery_stored_revision_binding_and_explicit_source_scope_JSON')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SEARCH_SELECTOR_CLOSURE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SELECTOR_CLOSURE_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','tests')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
