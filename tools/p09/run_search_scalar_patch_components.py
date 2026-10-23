"""SEARCH-006 original scalar patch prerequisite, not a search replacement/product Gate."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_search_review_text_components as base
harness,shared,c,a=base.harness,base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-search-scalar-patch-recovery062.v1.json'
FAILED='implementation/p09/evidence/p09-361-search-scalar-patch-components061.v1.json'
PRIOR='implementation/p09/evidence/p09-361-search-navigation-recovery059.v1.json'
TEST='crates/hwpx-package/tests/patch_leaf_scalar_ranges.rs'
PATCH='crates/hwpx-package/src/patch.rs'
LIB='crates/hwpx-package/src/lib.rs'
LEGACY=('crates/hwpx-package/tests/patch_leaf_text.rs','crates/hwpx-package/tests/patch_engine.rs')
CAPTURE='implementation/p09/evidence/private/p09-14-hyperlink-discovery-20260912-attempt02/after.hwpx'
NEW={TEST,'crates/hwpx-package/src/patch/leaf_scalar_ranges.rs'}
CHANGED={PATCH,LIB}
TARGETED={'five_xml_intents_are_surgical_and_keep_every_other_part_exact','overlap_stale_root_and_malicious_fragments_fail_before_publication'}


def inventory(check):
    return base.inventory(check)|{TEST,*LEGACY,CAPTURE,'crates/hwpx-package/tests/document_import_search_navigation.rs'}


def inverse(q,old):
    text=q.text(PATCH)
    for addition in ('mod leaf_scalar_ranges;\npub use leaf_scalar_ranges::LeafTextRangeReplacement;\n',
        '    /// Original decoded Unicode scalar ranges, not caller byte offsets or XML.\n    ReplaceLeafScalarRanges {\n        target: XmlElementSelector,\n        ranges: Vec<LeafTextRangeReplacement>,\n    },\n',
        '            Self::ReplaceLeafScalarRanges { .. } => formatter.write_str("ReplaceLeafScalarRanges(<redacted>)"),\n',
        '        leaf_scalar_ranges::preflight(self.intents, self.patch_limits)?;\n',
        '                PatchIntent::ReplaceLeafScalarRanges { target, ranges } => {\n                    self.plan_leaf_scalar_ranges(target, ranges, origin, &mut edits)?;\n                }\n'):
        c.require(text.count(addition)==1,'ONE_ADDITIVE_SCALAR_PATCH_BRANCH');text=text.replace(addition,'')
    base.inverse(text,old[PATCH],'ORIGINAL_PATCH_VALIDATORS_AND_ALL_EXISTING_INTENT_BODIES_EXACT_INVERSE')
    text=q.text(LIB);addition=', LeafTextRangeReplacement';c.require(text.count(addition)==1,'ONE_NEW_TYPED_SCALAR_RANGE_EXPORT')
    base.inverse(text.replace(addition,''),old[LIB],'ORIGINAL_PUBLIC_LIBRARY_EXPORTS_UNCHANGED')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SCALAR_PATCH_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SEARCH_SCALAR_PATCH_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,search_replacement_product_route_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        prior=q.json(PRIOR);c.require(q.snapshots[PRIOR]['sha256']=='bc4535b330d9a3a82b948d2080d56988aaf51ad643765e437ec062a2aeeb729a'
            and prior['state'].startswith('PASS_')and prior['cleanup'],'EXACT_PRIOR_NAVIGATION_PASS')
        old={p['path']:p for p in prior['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml'}}
        c.require(names-{*LEGACY,CAPTURE}==old_names|NEW,'EXACT_SCALAR_PREREQUISITE_SOURCE_INVENTORY')
        for name in names-NEW-CHANGED-set(LEGACY)-{CAPTURE}:c.require(q.snapshots[name]==old[name],'NO_SEARCH_PRODUCT_OR_OTHER_SOURCE_INPUT_CHANGE')
        inverse(q,old)
        failed=q.json(FAILED);c.require(q.snapshots[FAILED]['sha256']=='807b6b6919b176e66dcfdcca457cdc4ff6750cfe1cdf68ca982389dda8125826'
            and failed['state']=='FAILED_SEARCH_SCALAR_PATCH_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1
            and failed['steps'][0]['tests']==[],'ORIGINAL_SCALAR_TYPE_DERIVE_COMPILATION_FAILURE_NO_TESTS_PRESERVED')
        initial={p['path']:p for p in failed['source_pins']};helper='crates/hwpx-package/src/patch/leaf_scalar_ranges.rs'
        for name in names-{helper}:c.require(q.snapshots[name]==initial[name],'NO_OTHER_INPUT_CHANGE_DURING_SCALAR_DERIVE_REPAIR')
        text=q.text(helper);addition='#[derive(Clone,Eq,PartialEq)]\n';c.require(text.count(addition)==1,'ONLY_NEW_RANGE_EQUALITY_DERIVE_ADDED')
        base.inverse(text.replace(addition,'#[derive(Clone)]\n'),initial[helper],'SCALAR_HELPER_BODY_UNCHANGED_AFTER_COMPILE_FAILURE')
        core=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST)))
        legacy=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(LEGACY[0])))
        engine=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(LEGACY[1])))
        c.require(len(core)==8 and len(legacy)==3 and TARGETED<=engine,'EXACT_EIGHT_NEW_THREE_LEAF_TWO_PATCH_CASES')
        env=base.environment();common=[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package']
        print(json.dumps(dict(state='SCALAR_PATCH_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=8,affected_cases=5)),flush=True)
        harness.run_one('eight_original_scalar_range_patch_cases',common+['--test','patch_leaf_scalar_ranges','--','--test-threads=1'],core,guard,env,row)
        harness.run_one('three_original_whole_leaf_patch_cases',common+['--test','patch_leaf_text','--','--test-threads=1'],legacy,guard,env,row)
        harness.run_one('two_targeted_original_atomic_patch_cases',common+['--test','patch_engine','--',*sorted(TARGETED),'--exact','--test-threads=1'],TARGETED,guard,env,row)
        c.require(inventory(guard.check)==names,'FINAL_SCALAR_PATCH_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_SCALAR_RANGE_PATCH_EIGHT_NEW_FIVE_AFFECTED_NOT_SEARCH_REPLACEMENT_PRODUCT_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_cases=8,affected_cases=5,total_executed_cases=13,
            original_patch_validator_and_intent_bodies_inverse_verified=True,source_and_other_part_preservation_verified=True,
            per_leaf_single_scan_and_aggregate_range_value_bounds=True,search_matching_and_service_implementation_changed=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SCALAR_PATCH_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SCALAR_PATCH_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
