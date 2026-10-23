"""18 new selected-axis resolution/search cases; no previous product or queue replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_paragraph_style_product_components as prior
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-resolved-style-components148.v1.json'
BASELINE='implementation/p09/evidence/p09-361-paragraph-style-product-compile-recovery146.v1.json'
DEFS='crates/hwpx-package/src/document_import/search/inspection/definitions.rs'
SELECTOR='crates/hwpx-package/src/document_import/search/reviews/selector.rs'
CORE=DEFS[:-3]+'/resolved.rs';MATCHER=SELECTOR[:-3]+'/resolved_styles.rs'
TEST='crates/hwpx-package/tests/document_import_resolved_style_search.rs'
NEW={CORE,MATCHER,TEST};CHANGED={DEFS,SELECTOR}


def inventory(check):return prior.inventory(check)|NEW


def expected(q):
    names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST))
    c.require(len(names)==len(set(names))==18,'EXACT_EIGHTEEN_NEW_REQUIRED_AXIS_RESOLUTION_TESTS');return set(names)


def inverse(q,old):
    for name,marker in[(DEFS,'pub mod resolved;\n'),(SELECTOR,'pub mod resolved_styles;\n')]:
        text=q.text(name);c.require(text.count(marker)==1,'ONE_ADDITIVE_RESOLUTION_MODULE_DECLARATION')
        audit.inverse(text.replace(marker,''),old[name],'WHOLE_ORIGINAL_DEFINITION_MATCHER_RECEIPT_SELECTOR_SCOPE_AND_PROTECTION_BODY_UNCHANGED')
    text=q.text(MATCHER)
    c.require(text.count('self.resolve_windows(selector,policy)?')==1 and text.count('inspection.resolve_style_definitions()?')==1
        and text.index('if !coverage.requested_axes_complete()')<text.index('self.base.index.find_windowed(')
        and 'self.base.index.find_windowed(query,None,Some(&accept),Some(&selected.windows))?'in text,
        'ONE_SELECTED_WINDOW_AND_TYPED_CATALOG_PASS_UNRESOLVED_REJECTED_BEFORE_QUERY_NO_SILENT_FALSE')
    core=q.text(CORE)
    c.require('refs.run.is_some()&&refs.text.is_none()'in core and 'refs.paragraph.is_some()'in core
        and 'coverage.observed_segment_visits+=1'in core and 'inferred_default_or_named_fallback:false'in core
        and 'native_effective_visibility_or_execution_authority:false'in core,
        'EXPLICIT_DIRECT_REFERENCE_COVERAGE_WITHOUT_TEXT_PRECEDENCE_OR_MISSING_AXIS_FALLBACK')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'RESOLVED_STYLE_IMMUTABLE_RUN_EXISTS')
    selection=prior.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_RESOLVED_STYLE_COMPONENTS',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_effective_cascade_or_visibility_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(BASELINE)
        c.require(q.snapshots[BASELINE]['sha256']=='989da55b913541ad97bf16fe68a8d1d5b98bdeacb6b13134349aa065a92b3e6f'
            and baseline['state']=='PASS_PARAGRAPH_PRODUCT_TWENTY_ONE_NEW_NOT_FULL_STYLE_NATIVE_OR_GATE'and baseline['cleanup']
            and baseline['fresh_inputs']==baseline['final_fresh_hashes']==635 and baseline['new_product_cases']==21,
            'EXACT_QUALIFIED_PARAGRAPH_PRODUCT_BASELINE_NOT_FULL_STYLE_AUTHORITY')
        old={p['path']:p for p in baseline['source_pins']}
        old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_TWO_NEW_RESOLUTION_MODULES_AND_ONE_NEW_TEST_FILE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_OTHER_SOURCE_PRODUCT_GUARD_WRITER_OR_PRIOR_TEST_CHANGE')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='RESOLVED_STYLE_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=18,previous_cases_reexecuted=0,one_cpu_mask=4)),flush=True)
        harness.run_one('eighteen_new_resolution_and_selected_style_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','document_import_resolved_style_search','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        limits=row['steps'][0]['owned_job']['limits_readback'];c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,
            'ORIGINAL_ONE_CPU2_HARD_CAP_AND_PRIORITY')
        c.require(inventory(guard.check)==names,'FINAL_RESOLVED_STYLE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_RESOLVED_DIRECT_STYLE_EIGHTEEN_NEW_NOT_FULL_CASCADE_STORED_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_resolution_cases=18,total_executed_cases=18,previous_product_source_and_unrelated_cases_reexecuted=False,
            original_definition_and_selector_whole_file_inverse_verified=True,one_catalog_and_window_resolution=True,
            unresolved_selected_required_axes_reject_before_query=True,no_named_or_zero_fallback_or_text_precedence_inferred=True,
            next_work='Current_stored_strict_product_binding_and_qualified_text_precedence_visibility_then_full_scope_transaction_native_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'RESOLVED_STYLE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_RESOLVED_STYLE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
