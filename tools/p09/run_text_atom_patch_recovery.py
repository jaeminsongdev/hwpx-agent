"""Recover the two new fixture failures, retain eight passes, then run nine affected cases."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_text_atom_patch_components as base
harness,shared,c,a=base.harness,base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-text-atom-patch-recovery073.v1.json'
FAILED=base.OUTPUT
RECOVERED={'atom_ranges_preserve_controls_entities_run_style_and_all_other_parts',
    'atom_ranges_use_the_actual_search_pieces_original_atom_and_unicode_scalar_coordinates'}
NEGATIVE=('    // Keep the existing writer ID profile\'s rejection; no new charStyleIDRef rule is inferred.\n'
    '    let unqualified=package("<hp:t charStyleIDRef=\'0\'>ABC<hp:lineBreak/>DEF</hp:t>")?;\n'
    '    assert!(apply(&unqualified,&[(0,vec![(0,0,1,"X")])],Default::default(),false).is_err());\n')


def repairs(q,failed,check):
    old={p['path']:p for p in failed['source_pins']}
    for name in base.inventory(check)-{base.TEST,'crates/hwpx-package/src/patch/text_atom_ranges.rs'}:
        c.require(q.snapshots[name]==old[name],'NO_OTHER_INPUT_CHANGE_AFTER_NEW_ATOM_FIXTURE_FAILURES')
    path='crates/hwpx-package/src/patch/text_atom_ranges.rs';text=q.text(path)
    current='XmlElementSelector,escape_text';previous='XmlElementSelector,XmlTokenKind,escape_text'
    c.require(text.count(current)==1,'ONLY_UNUSED_ATOM_IMPORT_REMOVAL')
    base.prior.prior.base.inverse(text.replace(current,previous),old[path],'ATOM_SOURCE_PARSER_AND_EDIT_BODIES_UNCHANGED_AFTER_FIXTURE_FAILURES')
    text=q.text(base.TEST);c.require(text.count(NEGATIVE)==1,'PRESERVED_UNQUALIFIED_ID_ATTRIBUTE_REJECTION')
    text=text.replace(NEGATIVE,'')
    for current,previous,count in (("xmlns:k='urn:keep'","charStyleIDRef='0'",2),('hp:lineBreak/>Ω</hp:t>','hp:lineBreak/>D</hp:t>',1),
        ('("Ω",4,0,1)','("D",4,0,1)',1)):
        c.require(text.count(current)==count,'ONLY_FAILED_ATOM_FIXTURE_AND_EXPECTATION_REPAIRS');text=text.replace(current,previous)
    base.prior.prior.base.inverse(text,old[base.TEST],'OTHER_EIGHT_TEST_BODIES_AND_SHARED_HELPERS_EXACTLY_UNCHANGED')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'TEXT_ATOM_RECOVERY_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_TEXT_ATOM_PATCH_RECOVERY',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_literal_search_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(base.PRIOR);c.require(q.snapshots[base.PRIOR]['sha256']=='cacd9b8ef647792299c661d3a5f107fa9b5e516b081e8485c653f4e6900449df'
            and previous['state'].startswith('PASS_')and previous['cleanup'],'EXACT_PREVIOUS_STRICT_PRODUCT_PASS_RETAINED')
        failed=q.json(FAILED);c.require(q.snapshots[FAILED]['sha256']=='da4d29646be723868f2a93feef7ed068875cccd22f1dce8d01e9c1b8828e66ac'
            and failed['state']=='FAILED_TEXT_ATOM_PATCH_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1,'ORIGINAL_EIGHT_PASS_TWO_FAIL_ATOM_RESULT_PRESERVED')
        tests=dict(failed['steps'][0]['tests']);c.require({n for n,s in tests.items()if s=='FAILED'}==RECOVERED
            and sum(s=='ok'for s in tests.values())==8 and len(tests)==10,'ONLY_TWO_FAILED_NEW_CASES_REQUIRE_RECOVERY')
        old={p['path']:p for p in previous['source_pins']};base.inverse(q,old)
        # Pass the already acquired guard explicitly; do not create another watcher or reader.
        repairs(q,failed,guard.check)
        old_tests=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.prior.prior.scalar.TEST)))
        c.require(len(old_tests)==9,'EXACT_NINE_UNRUN_AFFECTED_SCALAR_CASES')
        env=base.prior.prior.base.environment();common=[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package']
        print(json.dumps(dict(state='TEXT_ATOM_RECOVERY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),recovered_cases=2,retained_passes=8,unrun_affected_cases=9)),flush=True)
        harness.run_one('two_repaired_source_atom_fixture_cases',common+['--test','patch_text_atom_ranges','--',*sorted(RECOVERED),'--exact','--test-threads=1'],RECOVERED,guard,env,row)
        harness.run_one('nine_affected_original_scalar_boundary_cases',common+['--test','patch_leaf_scalar_ranges','--','--test-threads=1'],old_tests,guard,env,row)
        c.require(base.inventory(guard.check)==names,'FINAL_ATOM_RECOVERY_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_TEXT_ATOM_PATCH_TWO_RECOVERED_NINE_AFFECTED_EIGHT_RETAINED_NOT_SEARCH_COMPILER_PRODUCT_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,recovered_cases=2,affected_cases=9,total_executed_cases=11,
            prior_new_passes_preserved=8,distinct_validated_cases=19,original_reader_value_policy_and_patch_bodies_inverse_verified=True,
            original_controls_and_unselected_package_bytes_preserved=True,combined_scalar_intent_budgets_enforced=True,
            other_eight_case_and_shared_fixture_bodies_unchanged=True,failed_source_result_preserved=True,
            old_literal_core_stored_and_product_tests_reexecuted=False,
            next_work='Explicit_v2_literal_candidate_compiler_preserving_controls_and_output_atom_readback')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'TEXT_ATOM_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_ATOM_RECOVERY_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
