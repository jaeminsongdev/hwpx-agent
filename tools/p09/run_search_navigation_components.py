"""Additive retained-result navigation: ten core and seven authenticated product cases."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_search_review_text_components as base
harness,shared,c,a=base.harness,base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-search-navigation-recovery059.v1.json'
FAILED='implementation/p09/evidence/p09-361-search-navigation-components058.v1.json'
RECOVERED='navigation_request_types_are_strict_and_selected_response_is_bounded_without_truncation'
PRIOR=base.OUTPUT
TEST='crates/hwpx-package/tests/document_import_search_navigation.rs'
PRODUCT='crates/product-cli/tests/form_stored_provider/actual_import/source_search_navigation.rs'
ROOT='crates/hwpx-package/src/document_import/search'
WRAPPERS={ROOT+'.rs',ROOT+'/scope.rs',ROOT+'/inspection.rs',ROOT+'/inspection/definitions.rs',ROOT+'/reviews.rs'}
STORED='crates/product-cli/src/form_stored_provider/actual_import/source_search.rs'
REQUEST='crates/product-cli/src/form_product_request/stored_source_search.rs'
MODULE='crates/product-cli/tests/form_stored_provider/actual_import.rs'
NEW={TEST,PRODUCT,ROOT+'/navigation.rs',STORED[:-3]+'/navigation.rs',REQUEST[:-3]+'/navigation.rs'}
CHANGED=WRAPPERS|{STORED,REQUEST,MODULE}


def inverse(q,old):
    for path in WRAPPERS:
        text=q.text(path);needle='    pub fn navigate('
        c.require(text.count(needle)==1,'ONE_ADDITIVE_NAVIGATION_METHOD_PER_RESULT')
        start=text.rfind('    /// # Errors\n',0,text.index(needle));end=text.index('\n    }\n',text.index(needle))+len('\n    }\n')
        c.require(start>=0,'NAVIGATION_METHOD_DOCUMENTATION_BOUNDARY');text=text[:start]+text[end:]
        if path==ROOT+'.rs':
            for addition in ('pub mod navigation;\n','    #[error("SOURCE_SEARCH_CURSOR_STALE_OR_INVALID")] Cursor,\n'):
                c.require(text.count(addition)==1,'ONE_ADDITIVE_NAVIGATION_DECLARATION');text=text.replace(addition,'')
        base.inverse(text,old[path],'ORIGINAL_SEARCH_MATCHER_WRAPPER_AND_SERIALIZATION_EXACT_INVERSE')
    for path in (STORED,REQUEST):
        text=q.text(path);c.require(text.count('pub mod navigation;\n')==1,'ONLY_ADDITIVE_NAVIGATION_CHILD_MODULE')
        base.inverse(text.replace('pub mod navigation;\n',''),old[path],'ORIGINAL_PRODUCT_AND_STORED_ACCESS_CODE_UNCHANGED')
    text=q.text(MODULE);addition='#[path = "actual_import/source_search_navigation.rs"]\nmod source_search_navigation;\n'
    c.require(text.count(addition)==1,'ONLY_ADDITIVE_NAVIGATION_TEST_MODULE');base.inverse(text.replace(addition,''),old[MODULE],'ORIGINAL_ALL_STORED_TEST_MODULES_UNCHANGED')


def inventory(check):return base.inventory(check)|{TEST}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NAVIGATION_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SEARCH_NAVIGATION_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,previous_search_tests_reexecuted=False,
        full_search_target_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        prior=q.json(PRIOR);c.require(q.snapshots[PRIOR]['sha256']=='2e1ca12d71eaead27bf18e42db72072505696813467583e2a0f9349914b3a692'
            and prior['state'].startswith('PASS_')and prior['cleanup'],'EXACT_PRIOR_REVIEW_SEARCH_PASS')
        old={p['path']:p for p in prior['source_pins']};original_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml'}}
        c.require(names==original_names|NEW,'EXACT_FIVE_NEW_NAVIGATION_FILES_IN_CURRENT_SOURCE_INVENTORY')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_OTHER_SEARCH_SOURCE_TEST_HEADER_AND_MODEL_INPUTS_UNCHANGED')
        inverse(q,old)
        failed=q.json(FAILED);c.require(q.snapshots[FAILED]['sha256']=='cc4396db8157b9d0514d73d90db8f963d9fd14321dc8fe55a4b347545b820767'
            and failed['state']=='FAILED_SEARCH_NAVIGATION_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1,'ORIGINAL_NINE_PASSES_ONE_FAILED_ASSERTION_PRESERVED')
        failed_pins={p['path']:p for p in failed['source_pins']}
        for name in names-{TEST}:c.require(q.snapshots[name]==failed_pins[name],'NO_PRODUCTION_OR_OTHER_INPUT_CHANGE_FOR_EXPECTATION_REPAIR')
        repaired=q.text(TEST)
        for current,original in (
            ('    let nav=found.navigate(&step(Direction::Forward,false,None),[0;32])?;let expected=nav.canonical_json()?;\n    assert!(expected.len()<=original_len);\n',
             '    let nav=found.navigate(&step(Direction::Forward,false,None),[0;32])?;assert!(nav.canonical_json()?.len()>original_len);\n'),
            ('    let found=bounded.find(query("K"))?;assert_eq!(found.navigate(&step(Direction::Forward,false,None),[0;32])?.canonical_json()?,expected);\n'
             '    let too_small=s.source_text_index(&b,SourceSearchLimits::new(SourceSearchLimitConfig {result_bytes:original_len-1,..Default::default()})?)?;\n'
             '    assert!(matches!(too_small.find(query("K")),Err(E::Output)));Ok(())\n',
             '    let found=bounded.find(query("K"))?;assert!(matches!(found.navigate(&step(Direction::Forward,false,None),[0;32]),Err(E::Output)));Ok(())\n')):
            c.require(repaired.count(current)==1,'ONLY_INVALID_SIZE_EXPECTATION_REPLACED');repaired=repaired.replace(current,original)
        base.inverse(repaired,failed_pins[TEST],'NINE_PASSED_CORE_BODIES_AND_OTHER_ASSERTIONS_UNCHANGED')
        core=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST)))
        product={'actual_import::source_search_navigation::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(PRODUCT))}
        c.require(len(core)==10 and len(product)==7,'EXACT_TEN_CORE_AND_SEVEN_PRODUCT_NAVIGATION_CASES')
        c.require({n for n,s in failed['steps'][0]['tests']}==core and dict(failed['steps'][0]['tests'])[RECOVERED]=='FAILED'
            and sum(s=='ok'for n,s in failed['steps'][0]['tests'])==9,'EXACT_NINE_UNCHANGED_CORE_PASSES_RETAINED')
        env=base.environment();common=[harness.CARGO,'test','--offline','--locked','-j','1']
        print(json.dumps(dict(state='NAVIGATION_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_core_cases=10,new_product_cases=7,original_search_bodies_exactly_preserved=True)),flush=True)
        harness.run_one('one_corrected_exact_size_boundary_core_case',common+['-p','hwpx-package','--test','document_import_search_navigation','--',RECOVERED,'--exact','--test-threads=1'],{RECOVERED},guard,env,row)
        harness.run_one('seven_authenticated_retained_search_navigation_cases',common+['-p','hwpx-agent-cli','--test','form_stored_provider','--',*sorted(product),'--exact','--test-threads=1'],product,guard,env,row)
        c.require(inventory(guard.check)==names,'FINAL_NAVIGATION_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_RETAINED_SEARCH_NAVIGATION_ONE_RECOVERED_NINE_RETAINED_SEVEN_PRODUCT_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_core_cases=1,new_product_cases=7,total_executed_cases=8,prior_core_passes_preserved=9,
            only_invalid_response_size_test_expectation_repaired=True,production_changed_after_initial_failure=False,
            original_search_code_and_test_bodies_inverse_verified=True,cursor_binds_original_result_and_product_context=True,
            direction_and_wrap_explicit=True,retained_query_reexecuted=False,source_authorization_and_final_head_rechecked=True,
            unrelated_stored_suites_reexecuted=False,idempotency_key_claimed=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'NAVIGATION_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_NAVIGATION_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
