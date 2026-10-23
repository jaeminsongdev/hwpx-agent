"""Actual multi-parent/multipart source ordering in one transaction; no old cases or Native replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_sort_compiler_recovery as base
harness,shared,c,a,audit,tools=base.harness,base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-sort-groups-components242.v1.json'
DRIVER='tools/p09/run_sort_groups_components.py'
DOC_BASE='implementation/p09/evidence/p09-361-sort-compiler-sync239.v1.json'
ROOT=base.base.CORE
HASH=base.base.INVENTORY
MODEL=ROOT[:-3]+'/groups.rs'
READBACK=ROOT[:-3]+'/groups/readback.rs'
TEST='crates/hwpx-package/tests/source_paragraph_sort_groups.rs'
NEW={DRIVER,MODEL,READBACK,TEST}
CHANGED={ROOT,HASH}


def inventory(check):return base.inventory(check)|NEW|{'tools/p09/run_sort_compiler_sync.py','protocol/migrations/p09-sort-operation-compiler-v1.md'}


def expected(q):
    cases=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST))
    c.require(len(cases)==len(set(cases))==16,'EXACT16_NEW_ACTUAL_SOURCE_MULTIGROUP_CASES')
    return set(cases)


def inverse(q,old):
    text=q.text(ROOT);marker='pub mod groups;\n';c.require(text.count(marker)==1,'ONE_ADDITIVE_MULTIGROUP_MODULE')
    audit.inverse(text.replace(marker,''),old[ROOT],'ORIGINAL_SINGLE_GROUP_COMPARISON_GUARDS_WRITER_READBACK_RECEIPT_AND_API_UNCHANGED')
    text=q.text(HASH);new='pub(super) fn hash(value:&impl Serialize,maximum:usize)';previous='fn hash(value:&impl Serialize,maximum:usize)'
    c.require(text.count(new)==1,'ONE_CRATE_INTERNAL_SHARED_BOUNDED_HASH_ACCESS')
    audit.inverse(text.replace(new,previous),old[HASH],'ORIGINAL_SORT_SPLICE_INVENTORY_AND_STREAMING_HASH_BODIES_UNCHANGED')
    for name in(MODEL,READBACK):
        text=q.text(name)
        c.require(all(marker not in text for marker in('std::fs::','std::process::','SignatureVerified','unsafe','commit_success(','RouteContext::new')),
            'NO_NATIVE_IO_TRUST_FORGING_OR_COMMIT_ADDED')
    text=q.text(MODEL)
    for marker in('self.for_original(original)','index.transformation_windows(selector,policy)','R::IncompleteParagraphScope','R::StructuredKey',
        'guards.insert(path,guard(xml)?)','protection[stop]!=protection[i]','context.field_intervals(source,&fields)',
        'spec.max_comparison_bytes.checked_sub(work)','PatchIntent::PermuteSiblingElements','readback::slots(&grouped)?',
        'locale_native_full_protection_or_execution_authority:false'):
        c.require(marker in text,'ALL_SELECTED_GROUPS_FULL_SCOPE_PROTECTION_AND_GLOBAL_WORK_BUDGET')
    c.require(text.count('styles::text::output::build(')==1 and 'lower_selector_paragraph_sort_candidate('not in text,
        'ONE_TRANSACTION_NO_PER_GROUP_PACKAGE_GENERATION_OR_LEGACY_SORT_REPLAY')
    text=q.text(READBACK)
    c.require(text.count('ImportedSourcePackage::import(')==1 and text.count('ImportedDocumentForms::import(')==1,
        'ONE_OUTPUT_SOURCE_AND_FORM_ADMISSION_FOR_ALL_GROUPS')
    for marker in('row.start<previous','context.readback','raw.get(before..destination.start).ok_or','raw.get(moved.start..moved.end).ok_or','raw.get(before..).ok_or'):
        c.require(marker in text,'ORIGINAL_NONOVERLAPPING_SLOTS_SUBTREE_GAPS_TAIL_AND_REVIEW_READBACK')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SORT_GROUPS_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SORT_GROUPS_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SEARCH021_complete=False,actual_registry_target_or_native_qualified=False,output_ingest_commit_or_publication=False,
        structured_or_nested_selected_subtree_composition_qualified=False,multigroup_current_stored_or_product_request_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);previous=q.json(base.OUTPUT);docs=q.json(DOC_BASE)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='c06a8d1482b21cc0d753d943faf948affbfb41984a4502fa5204c692af174619'
            and previous['cleanup']and previous['fresh_inputs']==previous['final_fresh_hashes']==810,'EXACT238_PREVIOUS_SORT_COMPILER_LINEAGE_AND_CLOSURE')
        c.require(q.snapshots[DOC_BASE]['sha256']=='021d3a52307cea1992b3a53476f38b1307a05c0fc97cf58f48dc6fca7379e113'
            and docs['cleanup']and docs['fresh_inputs']==docs['final_fresh_hashes']==39,'EXACT239_DOCUMENTED_SOURCE_BASELINE')
        old={p['path']:p for p in previous['source_pins']};documented={p['path']:p for p in docs['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in NEW|CHANGED:
                pin=documented.get(name,old.get(name));c.require(pin is not None and q.snapshots[name]==pin,
                    'ALL_OTHER_CURRENT_SOURCE_PRODUCTS_COMPILER_ROUTER_NATIVE_GUARDS_AND_TESTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='SORT_GROUPS_PREFLIGHT',inputs=len(q.snapshots),new_source_cases=len(cases),old_sort19_product20_compiler21_official249_reexecuted=False)),flush=True)
        harness.run_one('sixteen_actual_source_groups_scope_global_budget_protection_and_single_output_readback_cases',
            [harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','source_paragraph_sort_groups','--message-format=short','--','--test-threads=1'],
            cases,guard,audit.environment(),row,observe_capture=base.base.prior.prior.base.prior.base.prior.base.base.snapshot)
        tools.good_step(row['steps'][-1],cases);q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_MULTIPARENT_MULTIPART_PARAGRAPH_SORT16_NOT_CURRENT_PRODUCT_EXECUTION_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=16,
            one_original_transaction_and_output_admission=True,global_comparison_budget_and_all_selected_protection=True,
            old_sort19_product20_compiler21_and_official249_reexecuted=False,
            next_work='current_store_strict_multigroup_request_actual_splices_common_compiler_then_nested_structured_keys_and_actual_execution')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SORT_GROUPS_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SORT_GROUPS_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes','closed_nested_error_variants','closed_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
