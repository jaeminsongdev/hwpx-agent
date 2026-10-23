"""Actual scoped source paragraph ordering, original protection/writer/readback; not full SEARCH021/Native."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_sibling_permutation_recovery as prior
harness,shared,c,a,audit,tools=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.tools
OUTPUT='implementation/p09/evidence/p09-361-source-paragraph-sort-components230.v1.json'
DRIVER='tools/p09/run_source_paragraph_sort_components.py'
DOC_BASE='implementation/p09/evidence/p09-361-sibling-permutation-sync229.v1.json'
ROOT='crates/hwpx-package/src/document_import/search/replacement/atoms.rs'
MODEL=ROOT[:-3]+'/sort.rs';ORDER=MODEL[:-3]+'/order.rs';VERIFY=MODEL[:-3]+'/verify.rs'
TEST='crates/hwpx-package/tests/source_paragraph_sort.rs'
NEW={MODEL,ORDER,VERIFY,TEST,DRIVER};CHANGED={ROOT}


def inventory(check):return prior.inventory(check)|NEW|{'tools/p09/run_sibling_permutation_sync.py','protocol/migrations/p09-sibling-permutation-v1.md'}


def expected(q):
    cases=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST));c.require(len(cases)==len(set(cases))==19,'EXACT19_ACTUAL_SOURCE_PARAGRAPH_SORT_CASES')
    return set(cases)


def inverse(q,old):
    text=q.text(ROOT);marker='pub mod sort;\n';c.require(text.count(marker)==1,'ONE_SOURCE_SORT_CHILD')
    audit.inverse(text.replace(marker,''),old[ROOT],'ALL_ORIGINAL_SEARCH_REPLACEMENTS_PROTECTIONS_AND_READBACK_BODIES_UNCHANGED')
    text=q.text(MODEL)
    for marker in ('self.for_original(original)','index.transformation_windows(selector,policy)','blocks.iter().any','R::IncompleteParagraphScope',
        'node.parent()!=Some(parent)','R::ParentScope','context.field_intervals(source,&fields)','guard[stop]!=guard[i]',
        'order::sort(&keys,spec)','PatchIntent::PermuteSiblingElements','styles::text::output::build','verify::output(',
        'locale_native_full_protection_or_execution_authority:false'):
        c.require(marker in text,'FRESH_ORIGINAL_SCOPE_NO_WIDENING_PARENT_AND_FIELD_GUARDS_ACTUAL_PATCH_AND_READBACK')
    order=q.text(ORDER)
    for marker in ('checked_mul(2)','spec.max_comparison_bytes','work.checked_add(1)','std::mem::swap','cmp!=Ordering::Greater','cmp!=Ordering::Less'):
        c.require(marker in order,'STABLE_FALLIBLE_MERGE_ORDER_WITH_METERED_PREFIX_WORK')
    for marker in ('ImportedSourcePackage::import','ImportedDocumentForms::import','context.readback','raw.get(before..start)!=out.get(after..next)',
        'raw.get(a..b)!=out.get(next..stop)','raw.get(before..)!=out.get(after..)'):
        c.require(marker in q.text(VERIFY),'INDEPENDENT_EXACT_BYTE_GAP_AND_SUBTREE_READBACK_AFTER_ORIGINAL_OUTPUT_ADMISSION')
    for name in (MODEL,ORDER,VERIFY):
        c.require(all(marker not in q.text(name)for marker in('std::fs::','std::process::','SignatureVerified','commit_success(','unsafe','RouteContext::new')),
            'NO_EXTERNAL_IO_NATIVE_ROUTE_TRUST_COMMIT_OR_SOURCE_WRITE')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SOURCE_SORT_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SOURCE_PARAGRAPH_SORT_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SEARCH021_complete=False,multi_parent_or_nested_composition_qualified=False,locale_native_order_verified=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(prior.OUTPUT);docs=q.json(DOC_BASE)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='70cc6ee303f59feff83bc97d2f4b9c9c28b393ad72222196dd2595c1b28d80ed'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==786,'EXACT228_SIBLING_PERMUTATION18_AND_TERMINAL_CLOSURE')
        c.require(q.snapshots[DOC_BASE]['sha256']=='dada1b71b13ef7bde88b2b81a7656eed2df333d249c4cf51a0a3a64f79c92b36'
            and docs['cleanup']and docs['fresh_inputs']==docs['final_fresh_hashes']==22,'EXACT229_PREVIOUS_SORT_BASE_DOCS')
        old={p['path']:p for p in passed['source_pins']};documented={p['path']:p for p in docs['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in NEW|CHANGED:
                pin=documented.get(name,old.get(name));c.require(pin is not None and q.snapshots[name]==pin,'ALL_OTHER_SOURCE_SELECTOR_REVIEW_PROTECTION_PATCH_WRITER_PRODUCTS_AND_TESTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='SOURCE_PARAGRAPH_SORT_PREFLIGHT',inputs=len(q.snapshots),new_cases=len(cases),old18_and_official249_reexecuted=False)),flush=True)
        harness.run_one('nineteen_actual_source_selector_sort_protection_policy_and_exact_readback_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','source_paragraph_sort','--message-format=short','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=prior.base.prior.base.base.snapshot)
        tools.good_step(row['steps'][-1],cases);q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_SIBLING_PARAGRAPH_SORT19_NOT_FULL_SEARCH021_PRODUCT_TRANSACTION_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=19,
            explicit_NFC_stable_scope_parent_protection_field_writer_and_independent_readback_verified=True,
            prior_patch18_crypto18_protection44_compiler36_and_official249_reexecuted=False,
            next_work='multi_parent_nested_group_and_structured_keys_then_current_store_strict_product_request_compiler_and_execution')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SOURCE_SORT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SOURCE_SORT_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes','closed_nested_error_variants','closed_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
