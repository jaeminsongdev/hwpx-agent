"""Actual multi-part moved-slot inventory through18-family compiler/manifest; never execution qualification."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_sort_groups_product_components as base
harness,shared,c,a,audit,tools=base.harness,base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-sort-groups-compiler-components248.v1.json'
DRIVER='tools/p09/run_sort_groups_compiler_components.py'
DOC_BASE='implementation/p09/evidence/p09-361-sort-groups-product-sync247.v1.json'
CORE=base.prior.base.MODEL
INTENTS=base.prior.base.HASH
GROUP_INVENTORY=INTENTS[:-3]+'/groups.rs'
CORE_PARENT=base.prior.base.TEST
CORE_TEST='crates/hwpx-package/tests/support/paragraph_sort_groups_splices.rs'
DISPATCH='crates/product-cli/src/form_product_request/stored_operations/search_mutations.rs'
PROJECTION='crates/product-cli/src/form_product_request/stored_operations/compiled_search/projection.rs'
DISPATCH_TEST='crates/product-cli/tests/form_stored_provider/actual_import/search_mutation_dispatch.rs'
COMPILED_PARENT='crates/product-cli/tests/form_stored_provider/actual_import/sort_compiled_product.rs'
MANIFEST_PARENT='crates/product-cli/tests/form_stored_provider/actual_import/sort_manifest_product.rs'
COMPILED_TEST='crates/product-cli/tests/form_stored_provider/actual_import/sort_groups_compiled_product.rs'
MANIFEST_TEST='crates/product-cli/tests/form_stored_provider/actual_import/sort_groups_manifest_product.rs'
FIXTURE='crates/product-cli/tests/form_stored_provider/actual_import/sort_groups_plan_fixture.rs'
NEW={DRIVER,GROUP_INVENTORY,CORE_TEST,COMPILED_TEST,MANIFEST_TEST,FIXTURE}
CHANGED={CORE,INTENTS,CORE_PARENT,base.STORED,base.PRODUCT,DISPATCH,PROJECTION,DISPATCH_TEST,COMPILED_PARENT,MANIFEST_PARENT}
PREFIX='actual_import::regex_replacement_product::unicode_v1::dispatch_v1::'
OLD_SCHEMA='''    assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS.len(),17);assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS[16],literal::sort::PARAGRAPH_SORT_PRODUCT_REQUEST_SCHEMA);
    assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS.iter().copied().collect::<BTreeSet<_>>().len(),17);
'''
NEW_SCHEMA='''    assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS.len(),18);assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS[16],literal::sort::PARAGRAPH_SORT_PRODUCT_REQUEST_SCHEMA);
    assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS[17],literal::sort_groups::PARAGRAPH_SORT_GROUPS_PRODUCT_REQUEST_SCHEMA);
    assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS.iter().copied().collect::<BTreeSet<_>>().len(),18);
'''
CORE_CHILD='#[path="support/paragraph_sort_groups_splices.rs"]mod splices_v1;\n'
COMPILED_CHILD='#[path="sort_groups_compiled_product.rs"]mod groups_v1;\n'
MANIFEST_CHILD='#[path="sort_groups_manifest_product.rs"]mod groups_v1;\n'
PREPARE='''        let splices=intents::groups::prepare(slots.iter().flat_map(|(path,rows)|rows.iter().map(move |(destination,moved)|
            (*path,&destination.entry,&moved.entry,destination.start,destination.end))),selected_paragraphs,moved)?;
'''


def inventory(check):return base.inventory(check)|NEW|{'tools/p09/run_sort_groups_product_sync.py','protocol/migrations/p09-paragraph-sort-groups-product-request-v1.md'}


def expected(q):
    def names(path,prefix,n):
        cases=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path));c.require(len(cases)==len(set(cases))==n,'EXACT6_SOURCE10_COMPILER4_MANIFEST_NEW_CASES');return{prefix+x for x in cases}
    core=names(CORE_TEST,'splices_v1::',6)
    products=names(COMPILED_TEST,PREFIX+'compiled_v1::sort_v1::groups_v1::',10)|names(MANIFEST_TEST,PREFIX+'routing_v1::sort_v1::groups_v1::',4)
    affected={PREFIX+'dispatch_closed_schemas_strict_each_family_and_no_cross_kind_fallback_before_reads',
        PREFIX+'compiled_v1::compiled_literal_v1',PREFIX+'routing_v1::manifest_literal_v1',
        PREFIX+'compiled_v1::sort_v1::compiled_sort_dispatch_matches_original_product_output_and_exact_locked_plan',
        PREFIX+'routing_v1::sort_v1::manifest_sort_uses_actual_compiled_plan_source_routes_and_original_denial'}
    return core,products,affected


def inverse(q,old):
    text=q.text(INTENTS);marker='pub(super) mod groups;\n';c.require(text.count(marker)==1,'ONE_CHILD_WITHOUT_LEGACY_SPLICE_CHANGES')
    audit.inverse(text.replace(marker,''),old[INTENTS],'ALL_ORIGINAL_SINGLE_GROUP_SPLICES_AND_STREAMING_HASH_BODIES_UNCHANGED')
    text=q.text(CORE)
    for new,previous in(
        ('pub struct SourceParagraphSortGroupsCandidate {artifact:PackageArtifact,receipt:SourceParagraphSortGroupsReceipt,splices:intents::SourceParagraphSortSpliceInventory}',
         'pub struct SourceParagraphSortGroupsCandidate {artifact:PackageArtifact,receipt:SourceParagraphSortGroupsReceipt}'),
        ('    #[must_use] pub const fn splice_inventory(&self)->&intents::SourceParagraphSortSpliceInventory {&self.splices}\n',''),
        (PREPARE,''),
        ('        let splices=intents::groups::bind(&receipt,splices,limits.0.result_bytes)?;\n        Ok(SourceParagraphSortGroupsCandidate{artifact,receipt,splices})',
         '        Ok(SourceParagraphSortGroupsCandidate{artifact,receipt})')):
        c.require(text.count(new)==1,'EXACT_ADDITIVE_IMMUTABLE_MULTIGROUP_INVENTORY');text=text.replace(new,previous)
    audit.inverse(text,old[CORE],'ALL_ORIGINAL_MULTIGROUP_SELECTION_COMPARISON_PROTECTION_WRITER_READBACK_AND_RECEIPT_FIELDS_UNCHANGED')
    for path,child in((CORE_PARENT,CORE_CHILD),(COMPILED_PARENT,COMPILED_CHILD),(MANIFEST_PARENT,MANIFEST_CHILD)):
        text=q.text(path);c.require(text.endswith(child)and text.count(child)==1,'ONE_FOCUSED_TEST_CHILD')
        audit.inverse(text[:-len(child)],old[path],'ALL_PREVIOUS_SOURCE16_COMPILER8_MANIFEST4_TEST_BODIES_UNCHANGED')
    for path,macro in((base.STORED,'compiler_source!(PreparedStoredParagraphSortGroupsCandidate);\n'),
                        (base.PRODUCT,'compiler_product!(PreparedStoredParagraphSortGroupsProduct, request, plain);\n')):
        text=q.text(path);c.require(text.count(macro)==1,'ONE_ORIGINAL_READONLY_COMPILER_MACRO');text=text.replace(macro,'')
        text,n=re.subn(r'    pub\(crate\) fn compiler_sort_splices\([^\n]+\n','',text);c.require(n==1,'ONE_IMMUTABLE_SORT_SPLICE_BORROW')
        audit.inverse(text,old[path],'ALL_CURRENT_MULTIGROUP_WRITE_SCOPE_HEAD_ACL_JSON_AND_BYTE_DELIVERY_BODIES_UNCHANGED')
    text=q.text(DISPATCH).replace('styles, text_styles, unicode, whitespace, width, sort, sort_groups};','styles, text_styles, unicode, whitespace, width, sort};')
    marker='''    (ParagraphSortGroups, sort_groups, StoredParagraphSortGroupsProductRequest, PreparedStoredParagraphSortGroupsProduct, ParagraphSortGroupsProductReceipt,
        sort_groups::ParagraphSortGroupsProductError, PARAGRAPH_SORT_GROUPS_PRODUCT_REQUEST_SCHEMA, text),
'''
    c.require(text.count(marker)==1,'EXACT_EIGHTEENTH_CLOSED_SCHEMA');text=text.replace(marker,'')
    marker='Self::ParagraphSortGroups(candidate)=>Some(candidate.compiler_sort_splices()),';c.require(text.count(marker)==1,'ONE_NEW_SEALED_INVENTORY_ACCESSOR_ARM')
    audit.inverse(text.replace(marker,''),old[DISPATCH],'ALL_ORIGINAL17_DISPATCH_TABLE_AND_FRESH_GENERIC_BRANCHES_UNCHANGED')
    text=q.text(PROJECTION);marker='        Receipt::ParagraphSortGroups(r)=>permutation(candidate,&r.stored.output),\n';c.require(text.count(marker)==1,'ONE_GROUPS_ARM_REUSING_ORIGINAL_PERMUTATION_PROJECTION')
    audit.inverse(text.replace(marker,''),old[PROJECTION],'ALL_ORIGINAL_ANCHOR_PROJECTION_AND12_LOCKED_ARGUMENT_BINDING_UNCHANGED')
    text=q.text(DISPATCH_TEST);c.require(text.count(NEW_SCHEMA)==1,'EXACT18_SCHEMA_ASSERTION_ONLY')
    audit.inverse(text.replace(NEW_SCHEMA,OLD_SCHEMA),old[DISPATCH_TEST],'ALL_ORIGINAL_DISPATCH_TESTS_EXCEPT_SCHEMA_COUNT_EXTENSION_UNCHANGED')
    text=q.text(GROUP_INVENTORY)
    for marker in('selected>PatchLimits::default().config().max_intents','destination.paragraph_anchor==source.paragraph_anchor',
        'path==p&&start<stop','count!=selected||splices.len()!=moved','replacement_sha256:source.subtree_sha256',
        'max_fragment_bytes','legacy_receipt_sha256:hash(receipt,maximum)?','canonical_sha256=hash(&inventory,8*1024*1024)?'):
        c.require(marker in text,'EXACT_MULTIPART_MOVED_DESTINATIONS_AGGREGATE_BUDGET_AND_ORIGINAL_RECEIPT_BINDING')
    c.require(all(x not in text for x in('Deserialize','std::fs::','std::process::','unsafe','SignatureVerified')),'NO_CALLER_METADATA_TRUST_OR_EXECUTION')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SORT_GROUPS_COMPILER_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SORT_GROUPS_COMPILER_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SEARCH021_complete=False,actual_registry_target_or_native_qualified=False,output_ingest_commit_or_publication=False,synthetic_route_test_evidence_only=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);previous=q.json(base.OUTPUT);docs=q.json(DOC_BASE)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='96a937a14719cf4d88e6540d8c3fedc08ed0e93ce1cfe57ae8044515fd879630'
            and previous['cleanup']and previous['fresh_inputs']==previous['final_fresh_hashes']==824,'EXACT246_MULTIGROUP_PRODUCT20_AND824_CLOSURE')
        c.require(q.snapshots[DOC_BASE]['sha256']=='191f667a921804505d3db4d181283081c94e959992cbe25954dd1e92053b2a04'
            and docs['cleanup']and docs['fresh_inputs']==docs['final_fresh_hashes']==35,'EXACT247_PREVIOUS_PRODUCT_DOCS')
        old={p['path']:p for p in previous['source_pins']};documented={p['path']:p for p in docs['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in NEW|CHANGED:
                pin=documented.get(name,old.get(name));c.require(pin is not None and q.snapshots[name]==pin,'ALL_OTHER_CURRENT_SOURCE_PRODUCTS_COMPILER_OWNERS_ROUTER_MANIFEST_SECURITY_AND_TESTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        inverse(q,old);core,products,affected=expected(q)
        print(json.dumps(dict(state='SORT_GROUPS_COMPILER_PREFLIGHT',inputs=len(q.snapshots),new_source=6,new_compiler_manifest=14,affected_legacy=5,official249_reexecuted=False)),flush=True)
        snapshot=base.prior.base.base.base.prior.prior.base.prior.base.prior.base.base.snapshot
        harness.run_one('six_actual_source_multigroup_moved_slot_inventory_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','source_paragraph_sort_groups','--message-format=short','--','splices_v1::','--test-threads=1'],core,guard,audit.environment(),row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],core)
        harness.run_one('fourteen_multigroup_compiler_manifest_and_five_affected_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',*sorted(products|affected),'--exact','--test-threads=1'],products|affected,guard,audit.environment(),row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],products|affected);q.finish();guard.check(force=True)
        row.update(state='PASS_MULTIGROUP_SOURCE_SPLICES6_COMPILER_MANIFEST14_AFFECTED5_NOT_EXECUTION_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=25,new_source_cases=6,new_product_cases=14,affected_legacy_cases=5,
            all18_closed_families_and_original17_bodies_retained=True,actual_moved_slots_bound_to_original_compiler_and_manifest=True,
            old_multigroup_source16_product20_and_official249_reexecuted=False,
            next_work='actual_trusted_execution_ingest_commit_CAS_idempotency_and_remaining_nested_structured_search_reference_native_gate_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SORT_GROUPS_COMPILER_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_MULTIGROUP_COMPILER_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes','closed_nested_error_variants','closed_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
