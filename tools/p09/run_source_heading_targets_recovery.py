"""419: preserve418 pre-test verifier KeyError; current source closure and actual24 cases, no prior test promotion."""
import hashlib,json,re,subprocess,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_source_heading_targets as prior

OUTPUT='implementation/p09/evidence/p09-361-source-heading-targets-recovery419.v1.json'
DRIVER='tools/p09/run_source_heading_targets_recovery.py'


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'HEADING_RECOVERY419_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;final_attempted=False;started=time.monotonic();row=dict(state='FAILED_HEADING_RECOVERY419',steps=[],own_cpu_selection=selection,
        actual_DB_Hangul_or_COM_started=False,Native011_executed=False,prior_Native_replayed=False,official249_replayed=False,
        prior_successful_tests_replayed=False,prior_unpinned_root_test_results_reused=False,source_API_schema_changed=False,
        native_number_or_navigation_qualified=False,complete_reference_state_qualified=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=r.compact.unpack(q.json(prior.OUTPUT))
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='8034254f9fcc6d2d4133eeeb96811035720fb3101ef2dec5a08cf5a850295df3'
            and failed['state']=='FAILED_SOURCE_HEADING_TARGETS418'and failed['error_type']=='KeyError'and failed['cleanup']is True
            and failed['fresh_inputs']==failed['final_fresh_hashes']==785 and failed['steps']==[],'EXACT418_VERIFIER_ROOT_TEST_BASELINE_LOOKUP_FAILURE_NO_CARGO_OR_TESTS')
        for pin in failed['source_pins']:c.require(q.pin(pin['path'])==pin,'ALL785_CURRENT_SOURCE_AND_DECLARED_MODEL_INPUTS_UNCHANGED_SINCE418')
        q.pin(DRIVER);base=r.compact.unpack(q.json(prior.BASE));old={p['path']:p for p in base['source_pins']}
        c.require(prior.ROOT_TEST not in old,'PREVIOUS_CATALOG_GRAPH_DID_NOT_QUALIFY_THIS_OTHER_INTEGRATION_TEST_ROOT')
        text=q.text(prior.PARENT);c.require(text.count('pub mod headings;\n')==1,'ONE_NEW_HEADING_MODULE_EXPORT')
        r.audit.inverse(text.replace('pub mod headings;\n',''),old[prior.PARENT],'ALL_PREVIOUS_TARGET_PRODUCTION_ALGORITHMS_UNCHANGED')
        text=q.text(prior.ROOT_TEST);c.require(text.count(prior.LINK)==1,'ONE_NEW_HEADING_TEST_CHILD')
        inverse=text.replace(prior.LINK,'').encode();c.require(len(inverse)==157125 and hashlib.sha256(inverse).hexdigest()==
            '6d5093e28d8089b077c7dcb47df7851089a2063cc58a89a8bc2e3dce0838586f','DECLARED_SINGLE_INCLUDE_PREIMAGE_RECORDED_NOT_INDEPENDENT_PRIOR_TEST_PASS')
        row['root_test_baseline_origin']='current418_file_with_declared_one_include_removed_not_independent_historical_test_acceptance'
        c.require(q.pin(prior.SOURCE_API)==old[prior.SOURCE_API],'V12_SOURCE_API_AND_FOUR_UNRESOLVED_STAGES_UNCHANGED')
        for path,(size,sha)in prior.PINS.items():
            pin=q.pin(prior.MODELS+path);c.require((pin['bytes'],pin['sha256'])==(size,sha),'EXACT_OBSERVED_PINNED_PRIMARY_DECLARATION_SOURCE')
        model=q.text(prior.MODELS+'Head/heading.cpp');enum=q.text(prior.MODELS+'enumdef.h')
        for key in('type','idRef','level'):c.require('GetAttribute(att, L"'+key+'"'in model,'EXACT_THREE_EXPLICIT_ATTRIBUTES_NOT_CONSTRUCTOR_DEFAULTS')
        for value in('NONE','OUTLINE','NUMBER','BULLET'):c.require('L"'+value+'"'in enum,'ONLY_OFFICIAL_TYPE_LABELS')
        text=q.text(prior.TEST);cases={'source_headings::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}
        c.require(len(cases)==22 and '#[ignore]'not in text,'EXACT_NEW22_NO_SKIPS');selected=cases|prior.AFFECTED
        scratch=c.ROOT/'target/p09-source-heading-targets-scratch-419';c.require(not scratch.exists()and scratch.parent.is_dir()
            and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'HEADING419_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='HEADING419_PREFLIGHT',inputs=len(q.snapshots),new_cases=22,affected_original_cases_to_execute=2,prior_test_results_reused=0)),flush=True)
        r.harness.run_one('source_heading_new22_original_targets2',[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test',
            'document_import_reference_targets','--message-format=short','--',*sorted(selected),'--test-threads=1'],selected,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],selected);c.require(row['steps'][-1]['diagnostics']==[],'ALL_CURRENT24_EXECUTED_WITHOUT_WARNINGS')
        c.require(not any(scratch.iterdir()),'HEADING419_COMPILER_TEMP_EMPTY');final_attempted=True;q.finish();guard.check(force=True)
        row.update(state='PASS_DIRECT_SOURCE_HEADING22_ORIGINAL_TARGETS2_NOT_API_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=22,affected_cases=2,next_work='versioned_reference_source_API_heading_target_integration_keep_four_unresolved_stages')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'HEADING419_FAILURE_NO_RAW_VALUES')
        if q is not None and not final_attempted:
            try:final_attempted=True;q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=r.a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('exit_code','diagnostics','safe_error_variants','panic_locations','cleanup')},'cases':len(s.get('tests',[])),
                'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
