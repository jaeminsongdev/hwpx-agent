"""Actual sort splice inventory -> shared17-family compiler/router data path; never execution qualification."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_paragraph_sort_product_components as prior
harness,shared,c,a,audit,tools=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.tools
OUTPUT='implementation/p09/evidence/p09-361-sort-compiler-components237.v1.json'
DRIVER='tools/p09/run_sort_compiler_components.py'
DOC_BASE='implementation/p09/evidence/p09-361-paragraph-sort-product-sync236.v1.json'
CORE=prior.prior.base.MODEL;INVENTORY=CORE[:-3]+'/intents.rs'
CORE_PARENT=prior.prior.base.TEST
CORE_TEST='crates/hwpx-package/tests/support/paragraph_sort_splice_inventory.rs'
DISPATCH='crates/product-cli/src/form_product_request/stored_operations/search_mutations.rs'
PROJECTION='crates/product-cli/src/form_product_request/stored_operations/compiled_search/projection.rs'
DISPATCH_TEST='crates/product-cli/tests/form_stored_provider/actual_import/search_mutation_dispatch.rs'
COMPILED_PARENT='crates/product-cli/tests/form_stored_provider/actual_import/compiled_search_product.rs'
MANIFEST_PARENT='crates/product-cli/tests/form_stored_provider/actual_import/compiled_search_routing.rs'
COMPILED_TEST='crates/product-cli/tests/form_stored_provider/actual_import/sort_compiled_product.rs'
MANIFEST_TEST='crates/product-cli/tests/form_stored_provider/actual_import/sort_manifest_product.rs'
NEW={INVENTORY,CORE_TEST,COMPILED_TEST,MANIFEST_TEST,DRIVER}
CHANGED={CORE,CORE_PARENT,prior.STORED,prior.PRODUCT,DISPATCH,PROJECTION,DISPATCH_TEST,COMPILED_PARENT,MANIFEST_PARENT}
PREFIX='actual_import::regex_replacement_product::unicode_v1::dispatch_v1::'
OLD_SCHEMA='    assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS,SCHEMAS);assert_eq!(SCHEMAS.into_iter().collect::<BTreeSet<_>>().len(),16);\n'
NEW_SCHEMA='''    assert_eq!(&SEARCH_MUTATION_REQUEST_SCHEMAS[..16],SCHEMAS);assert_eq!(SCHEMAS.into_iter().collect::<BTreeSet<_>>().len(),16);
    assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS.len(),17);assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS[16],literal::sort::PARAGRAPH_SORT_PRODUCT_REQUEST_SCHEMA);
    assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS.iter().copied().collect::<BTreeSet<_>>().len(),17);
'''
CORE_CHILD='\n#[path="support/paragraph_sort_splice_inventory.rs"]mod splice_inventory_v1;\n'
COMPILED_CHILD='#[path="sort_compiled_product.rs"]mod sort_v1;\n'
MANIFEST_CHILD='#[path="sort_manifest_product.rs"]mod sort_v1;\n'


def inventory(check):return prior.inventory(check)|NEW|{'tools/p09/run_paragraph_sort_product_sync.py','protocol/migrations/p09-paragraph-sort-product-request-v1.md'}


def expected(q):
    def names(path,prefix,n):
        found=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path));c.require(len(found)==len(set(found))==n,'EXACT6_SOURCE8_COMPILER4_MANIFEST_NEW_CASES');return{prefix+x for x in found}
    core=names(CORE_TEST,'splice_inventory_v1::',6)
    products=names(COMPILED_TEST,PREFIX+'compiled_v1::sort_v1::',8)|names(MANIFEST_TEST,PREFIX+'routing_v1::sort_v1::',4)
    affected={PREFIX+'dispatch_closed_schemas_strict_each_family_and_no_cross_kind_fallback_before_reads',PREFIX+'compiled_v1::compiled_literal_v1',PREFIX+'routing_v1::manifest_literal_v1'}
    return core,products,affected


def inverse(q,old):
    text=q.text(CORE)
    changes=[('pub mod intents;\n',''),
        ('pub struct SourceParagraphSortCandidate {artifact:PackageArtifact,receipt:SourceParagraphSortReceipt,splices:intents::SourceParagraphSortSpliceInventory}',
         'pub struct SourceParagraphSortCandidate {artifact:PackageArtifact,receipt:SourceParagraphSortReceipt}'),
        ('    #[must_use] pub const fn splice_inventory(&self)->&intents::SourceParagraphSortSpliceInventory {&self.splices}\n',''),
        ('        let splices=intents::build(&receipt,&spans,limits.0.result_bytes)?;\n        Ok(SourceParagraphSortCandidate {artifact,receipt,splices})',
         '        Ok(SourceParagraphSortCandidate {artifact,receipt})')]
    for new,previous in changes:c.require(text.count(new)==1,'ONE_ADDITIVE_SORT_INVENTORY_AT_ORIGINAL_RETURN');text=text.replace(new,previous)
    audit.inverse(text,old[CORE],'ALL_ORIGINAL_SORT_SCOPE_COMPARISON_GUARDS_PATCH_READBACK_AND_LEGACY_RECEIPT_FIELDS_UNCHANGED')
    for path,child in((CORE_PARENT,CORE_CHILD),(COMPILED_PARENT,COMPILED_CHILD),(MANIFEST_PARENT,MANIFEST_CHILD)):
        text=q.text(path);c.require(text.endswith(child)and text.count(child)==1,'ONE_APPENDED_FOCUSED_TEST_CHILD')
        audit.inverse(text[:-len(child)],old[path],'ALL_ORIGINAL_SOURCE_COMPILER_AND_MANIFEST_TEST_BODIES_UNCHANGED')
    for path,macro in((prior.STORED,'compiler_source!(PreparedStoredParagraphSortCandidate);\n'),(prior.PRODUCT,'compiler_product!(PreparedStoredParagraphSortProduct, request, plain);\n')):
        text=q.text(path);c.require(text.count(macro)==1,'ONE_ORIGINAL_READONLY_COMPILER_VIEW')
        text=text.replace(macro,'');text,count=re.subn(r'    pub\(crate\) fn compiler_sort_splices\([^\n]+\n','',text);c.require(count==1,'ONE_IMMUTABLE_SORT_INVENTORY_BORROW')
        audit.inverse(text,old[path],'ALL_CURRENT_SORT_WRITE_ACL_SOURCE_HEAD_JSON_DELIVERY_AND_ROUTE_DENIAL_BODIES_UNCHANGED')
    text=q.text(DISPATCH).replace('styles, text_styles, unicode, whitespace, width, sort};','styles, text_styles, unicode, whitespace, width};')
    marker='''    (ParagraphSort, sort, StoredParagraphSortProductRequest, PreparedStoredParagraphSortProduct, ParagraphSortProductReceipt,
        sort::ParagraphSortProductError, PARAGRAPH_SORT_PRODUCT_REQUEST_SCHEMA, text),
'''
    c.require(text.count(marker)==1,'EXACT_SEVENTEENTH_CLOSED_FAMILY');text=text.replace(marker,'')
    text,count=re.subn(r'(?m)^impl PreparedStoredSearchMutation \{\n    pub\(crate\) fn sort_splices\(.*?\n}\n','',text,flags=re.S);c.require(count==1,'ONE_IMMUTABLE_SORT_ONLY_PROJECTION_NO_LEGACY_CHANGES')
    audit.inverse(text,old[DISPATCH],'ALL_ORIGINAL16_FAMILY_DISPATCH_TABLE_AND_GENERIC_BRANCHES_UNCHANGED')
    text=q.text(PROJECTION);marker='        Receipt::ParagraphSort(r)=>permutation(candidate,&r.stored.output),\n';c.require(text.count(marker)==1,'ONE_ACTUAL_SORT_PROJECTION_ARM')
    text=text.replace(marker,'');start=text.index('fn permutation');end=text.index('fn style',start)
    audit.inverse(text[:start]+text[end:],old[PROJECTION],'ALL_ORIGINAL16_TEXT_AND_FINAL_STYLE_SPLICE_PROJECTIONS_UNCHANGED')
    text=q.text(DISPATCH_TEST);c.require(text.count(NEW_SCHEMA)==1,'EXACT_ORIGINAL16_PLUS_ONE_NEW_SCHEMA_ASSERTION')
    audit.inverse(text.replace(NEW_SCHEMA,OLD_SCHEMA),old[DISPATCH_TEST],'ALL_ORIGINAL_DISPATCH_TESTS_EXCEPT_EXACT_SUPPORTED_SCHEMA_EXTENSION_UNCHANGED')
    text=q.text(INVENTORY)
    for marker in('if destination==source{continue;}','replacement_sha256:moved.subtree_sha256','source_anchor:receipt.entries[destination].paragraph_anchor.clone()',
        'splices.len()!=receipt.moved_paragraphs','legacy_receipt_sha256:hash(receipt,maximum)?','canonical_sha256=hash(&inventory,8*1024*1024)?'):
        c.require(marker in text,'SEALED_EXACT_MOVED_DESTINATIONS_REPLACEMENT_HASHES_AND_LEGACY_RECEIPT_BINDING')
    c.require('Deserialize'not in text and 'pub struct'in text,'NO_CALLER_CONSTRUCTOR_OR_DESERIALIZATION_OF_SEALED_INVENTORY')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SORT_COMPILER_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SORT_COMPILER_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SEARCH021_complete=False,actual_registry_target_or_native_qualified=False,output_ingest_commit_or_publication=False,synthetic_route_test_evidence_only=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(prior.OUTPUT);docs=q.json(DOC_BASE)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='af2133b3d4387533375c28d2dcf40b850f7f34b0c039288f9f10286a557affbe'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==802,'EXACT235_CURRENT_SORT_PRODUCT20_AND_TERMINAL_CLOSURE')
        c.require(q.snapshots[DOC_BASE]['sha256']=='a6580d59025c64f0370878aab906a23ae39531641e45d752a71645252d6fb8f2'
            and docs['cleanup']and docs['fresh_inputs']==docs['final_fresh_hashes']==30,'EXACT236_CURRENT_SORT_PRODUCT_DOCS')
        old={p['path']:p for p in passed['source_pins']};documented={p['path']:p for p in docs['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in NEW|CHANGED:
                pin=documented.get(name,old.get(name));c.require(pin is not None and q.snapshots[name]==pin,'ALL_OTHER_SOURCE_COMPILERS_OWNERS_ROUTER_MANIFEST_SECURITY_AND_TESTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        inverse(q,old);core,products,affected=expected(q)
        print(json.dumps(dict(state='SORT_COMPILER_PREFLIGHT',inputs=len(q.snapshots),new_source_cases=6,new_compiler_manifest_cases=12,affected_legacy_cases=3,official249_reexecuted=False)),flush=True)
        snapshot=prior.prior.base.prior.base.prior.base.base.snapshot
        harness.run_one('six_actual_source_sort_splice_inventory_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','source_paragraph_sort','--message-format=short','--','splice_inventory_v1::','--test-threads=1'],core,guard,audit.environment(),row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],core)
        harness.run_one('twelve_sort_compiler_manifest_and_three_affected_legacy_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',*sorted(products|affected),'--exact','--test-threads=1'],products|affected,guard,audit.environment(),row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],products|affected);q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_SORT_SPLICES6_SHARED_COMPILER_MANIFEST12_AFFECTED3_NOT_EXECUTION_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=21,source_cases=6,new_product_cases=12,affected_legacy_cases=3,
            all17_families_closed_and_original16_bodies_retained=True,actual_sort_moved_slot_inventory_bound_to_original_compiler_and_manifest=True,
            old_sort_source19_product20_and_official249_reexecuted=False,
            next_work='actual_trusted_execution_ingest_commit_CAS_idempotency_and_remaining_multi_group_search_reference_native_gate_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SORT_COMPILER_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SORT_COMPILER_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes','closed_nested_error_variants','closed_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
