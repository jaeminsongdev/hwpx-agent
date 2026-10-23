"""Review-body search code/result/docs closure; no Cargo, Native or queue replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_search_review_text_components as base
shared,c,a=base.shared,base.c,base.a
PASSED=base.OUTPUT
OUTPUT='implementation/p09/evidence/p09-361-search-review-text-sync057.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',
    'protocol/migrations/p09-source-definition-style-search-v3.md','protocol/migrations/p09-source-review-text-search-v4.md')
RETAINED={'crates/hwpx-package/src/document_import/search/scope.rs','crates/hwpx-package/src/document_import/search/normalization.rs',
    'crates/hwpx-package/src/document_import/structure/review.rs','crates/hwpx-package/src/document_import/forms.rs',
    'crates/product-cli/src/form_stored_provider.rs',base.HEADER}
RETAINED|={'crates/hwpx-package/tests/'+n+'.rs'for n in base.RETAINED}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REVIEW_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SEARCH_REVIEW_TEXT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(PASSED);prior=q.json(base.PRIOR)
        c.require(q.snapshots[PASSED]['sha256']=='2e1ca12d71eaead27bf18e42db72072505696813467583e2a0f9349914b3a692'
            and q.snapshots[base.PRIOR]['sha256']==base.PRIOR_SHA,'EXACT_REVIEW_PASS_AND_ORIGINAL_DEFINITION_RESULT')
        c.require(passed['state']=='PASS_ORIGINAL_REVIEW_TEXT_EIGHT_CORE_FOUR_TARGETED_TWENTY_SIX_PRODUCT_NOT_APP_VISIBILITY_NATIVE_OR_GATE'
            and passed['fresh_inputs']==passed['final_fresh_hashes']==454 and passed['cleanup']and passed['total_executed_cases']==38,
            'EXACT_FRESH_THIRTY_EIGHT_REVIEW_CASE_BOUNDARIES')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in prior['source_pins']}
        sources={n for n in tested if n.startswith('crates/')or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml'}}
        original={n for n in old if n.startswith('crates/')or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml'}}
        c.require(sources-original==base.NEW,'ONLY_THREE_NEW_REVIEW_SOURCE_TEST_AND_FIXTURE_FILES')
        for name in sources-base.NEW-base.CHANGED:c.require(tested[name]==old[name],'ORIGINAL_OTHER_SOURCE_PINS_RETAINED_IN_REVIEW_PASS')
        for name in sorted(base.NEW|base.CHANGED|RETAINED|set(base.MODELS)):
            q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_REVIEW_AND_RETAINED_SHARED_INPUTS_MATCH_PASS')
        base.original_core_inverse(q,old)
        prefix=q.text(base.PRODUCT).split('// Additive v4 review-text cases;',1)[0]
        c.require(prefix.endswith('\n\n'),'ONE_ADDITIVE_V4_SEPARATOR');base.inverse(prefix[:-1],old[base.PRODUCT],'ORIGINAL_TWENTY_PRODUCT_BODIES_EXACT_INVERSE')
        core=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.TEST)))
        product={'actual_import::source_search::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.PRODUCT))}
        c.require(len(core)==8 and len(product)==26 and len(passed['steps'])==3,'EXACT_NEW_AND_AFFECTED_TEST_INVENTORIES')
        for step,expected in zip(passed['steps'],(core,base.TARGETED,product),strict=True):
            c.require(len(step['tests'])==len(expected)and{n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])
                and not step['diagnostics']and not step['panic_locations'],'ALL_THIRTY_EIGHT_REVIEW_CASES_PASS_WITHOUT_DIAGNOSTICS')
            job=step['owned_job'];c.require(step['exit_code']==0 and step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']
                and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0,'THREE_REVIEW_JOBS_TERMINAL_EMPTY_CLOSED')
        c.require(all(not passed[k]for k in('actual_Hangul_or_COM','Native011_executed','prior_Native_replayed',
            'compiled_queue_reexecuted','full_cascade_visibility_or_search_qualified','output_ingest_commit_or_publication')),
            'NO_NATIVE_QUEUE_OR_AUTHORITY_PROMOTION')
        for name in DOCS:q.pin(name)
        progress=q.text(DOCS[1]);c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'RETAINED_NINETEEN_SEARCH_COMPLETION_ROWS')
        for marker in ('총38','454 fresh/final454','기존20개','include_hidden_explanations','include_memo_bodies','다시 찾기 cursor'):
            c.require(marker in progress,'REVIEW_PROGRESS_CURRENT_CASES_POLICY_AND_NEXT_WORK')
        profile=q.text(DOCS[3])
        for marker in ('V1/v2/v3 reject','Scope resolution first','Policy exclusions then precede','XML order is not native',
            'coverage=selected_admitted_file_regions','app_visibility_cascade_or_full_document_search_qualified=false',
            'all38 pass,454 fresh/final454','P09/A12/A13 OPEN','Native011 unapproved/unexecuted'):
            c.require(marker in profile,'V4_ORIGINAL_BODY_POLICY_ACCESS_AND_GATE_BOUNDARIES')
        c.require('p09-source-review-text-search-v4.md'in q.text(DOCS[2]),'V3_AND_V4_PROFILES_LINKED')
        state=q.text(DOCS[0]).split('> 2026-10-20 P09 이전 원본 서식 정의 검색',1)[0]
        for marker in ('2026-10-20','38개 PASS','454fresh/final454','53.83%','20.0813%','4.9954%',
            '잔여91','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행','P10미시작','다시 찾기 cursor'):
            c.require(marker in state,'CURRENT_REVIEW_PASS_RESOURCES_AND_UNCHANGED_GATE')
        runner='tools/p09/run_search_review_text_components.py';q.pin(runner)
        c.require(q.snapshots[runner]==tested[runner],'SUCCESSFUL_REVIEW_COMPONENT_RUNNER_UNCHANGED')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_ORIGINAL_REVIEW_BODY_SEARCH_CODE_DOCUMENT_SYNC_THIRTY_EIGHT_CASES_NOT_APP_VISIBILITY_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,current_executed_cases=38,new_cases=14,affected_cases=24,
            original_matcher_and_none_extraction_inverse_verified=True,original_twenty_product_bodies_unchanged=True,
            embedded_header_and_official_source_inputs_pinned=True,entire_454_inputs_reaudited=False,
            full_cascade_visibility_or_search_qualified=False,next_work='SEARCH_005_source_bound_find_next_cursor_and_movement_policy')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REVIEW_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_REVIEW_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
