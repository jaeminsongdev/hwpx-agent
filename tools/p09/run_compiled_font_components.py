"""323: real common font compiler/dispatch16 + four affected legacy paths; retain prior36."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_font_inventory_recovery as previous
import run_sql23_storage as closure
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
base=previous.previous.base
OUTPUT='implementation/p09/evidence/p09-361-compiled-font-components323.v1.json';DRIVER='tools/p09/run_compiled_font_components.py'
ROOT='crates/product-cli/src/form_product_request/stored_operations/compiled_search.rs';PROJECTION=ROOT[:-3]+'/projection.rs';BUILD=ROOT[:-3]+'/build.rs';RESOURCES=ROOT[:-3]+'/font_resources.rs'
MODEL='crates/product-cli/src/form_product_request/stored_operations/search_mutations.rs'
OLD_TEST='crates/product-cli/tests/form_stored_provider/actual_import/search_mutation_dispatch.rs';TEST='crates/product-cli/tests/support/scoped_font_compiled.rs'
NEW={DRIVER,RESOURCES,TEST};CHANGED={ROOT,PROJECTION,BUILD,MODEL,OLD_TEST,base.STORED,base.REQUEST,base.TEST}
FONT_ROW='''    (Font, fonts, StoredFontProductRequest, PreparedStoredFontProduct, FontProductReceipt,
        fonts::FontProductError, FONT_PRODUCT_REQUEST_SCHEMA, text),
'''
FONT_METHOD='''    pub(crate) fn font_inventory(&self)->Option<&hwpx_package::document_import::search::replacement::atoms::styles::fonts::inventory::SourceFontEditInventory>{
        match self{Self::Font(candidate)=>Some(candidate.compiler_font_inventory()),_=>None}
    }
'''
BUILD_LINES=[
    '    let font_arguments=p.font_resources.as_ref().map(super::font_resources::HeaderResources::arguments).transpose()?;\n',
    '    if let Some(resources)=&font_arguments{let bytes:usize=resources.iter().map(|(name,value)|name.len()+value.len()).sum();bytes.checked_mul(p.edits.len()).filter(|n|*n<=MAX_METADATA_BYTES).ok_or(CompiledSearchError::Limit)?;}\n',
    '    if let Some(resources)=&font_arguments{for(name,_)in resources{definition.arguments.insert((*name).into(),ArgumentSpec{kind:ArgumentKind::Text{max_bytes:2048},required:true,default:None,default_policy:DefaultPolicy::Locked});}}\n',
    '        if let Some(resources)=&font_arguments{for(name,value)in resources{arguments.insert((*name).into(),ArgumentDraft::Text(value.clone()));}}\n']

def inverse(q,old):
    for path,macro,call in ((base.STORED,'compiler_source!(PreparedStoredFontCandidate);\n','self.output.edit_inventory()'),
        (base.REQUEST,'compiler_product!(PreparedStoredFontProduct, request, plain);\n','self.candidate.compiler_font_inventory()')):
        getter='    pub(crate) fn compiler_font_inventory(&self)->&hwpx_package::document_import::search::replacement::atoms::styles::fonts::inventory::SourceFontEditInventory{'+call+'}\n'
        text=q.text(path);c.require(text.count(macro)==text.count(getter)==1,'ONE_CRATE_PRIVATE_SOURCE_AND_INVENTORY_COMPILER_BORROW')
        audit.inverse(text.replace(macro,'').replace(getter,''),old[path],'ALL_ORIGINAL_FONT_PARSE_AUTHORITY_DELIVERY_ROUTE_AND_RECEIPT_CODE_UNCHANGED')
    text=q.text(MODEL);c.require(text.count(FONT_ROW)==text.count(FONT_METHOD)==1,'ONE_CLOSED_FONT_FAMILY_AND_IMMUTABLE_INVENTORY_BRANCH')
    audit.inverse(text.replace(FONT_ROW,'').replace(FONT_METHOD,'').replace('sort_groups, fonts};','sort_groups};'),old[MODEL],'ALL_ORIGINAL18_FAMILIES_ORDER_BUDGETS_AND_MACRO_DISPATCH_UNCHANGED')
    text=q.text(ROOT);c.require(text.count('mod font_resources;\n')==1,'ONE_COMPILER_RESOURCE_MODULE_LINK');audit.inverse(text.replace('mod font_resources;\n',''),old[ROOT],'ALL_COMPILE_VERIFY_DELIVERY_HEAD_BINDING_AND_RECEIPTS_UNCHANGED')
    text=q.text(PROJECTION);text=text.replace(',pub font_resources:Option<super::font_resources::HeaderResources<\'a>>','').replace('pub(super) fn collect<','fn collect<').replace(',font_resources:None','')
    marker='        Receipt::Font(r)=>super::font_resources::project(candidate,&r.stored.output),\n';c.require(text.count(marker)==1,'ONE_FONT_RESOURCE_AND_BODY_PROJECTION')
    audit.inverse(text.replace(marker,''),old[PROJECTION],'ALL_PREVIOUS18_RECEIPT_DOMAINS_AND_SPLICE_INVENTORY_ALGORITHMS_UNCHANGED')
    text=q.text(BUILD)
    for marker in BUILD_LINES:c.require(text.count(marker)==1,'ONE_FONT_ONLY_RESOURCE_DEFINITION_BUDGET_AND_ARGUMENT_ADDITION');text=text.replace(marker,'')
    audit.inverse(text.replace('max_arguments_per_operation:if font_arguments.is_some(){15}else{12}','max_arguments_per_operation:12'),old[BUILD],'ALL_ORIGINAL_TWELVE_ARGUMENT_COMPILER_SNAPSHOT_TARGET_AND_TOTAL_BOUNDS_UNCHANGED')
    text=q.text(base.TEST);marker='#[path="support/scoped_font_compiled.rs"]mod compiled_font_v1;\n';c.require(text.count(marker)==1,'ONE_STANDALONE_COMPILER_TEST_MODULE_LINK')
    audit.inverse(text.replace(marker,''),old[base.TEST],'ALL_PREVIOUS36_FONT_TESTS_AND_FIXTURES_UNCHANGED')
    text=q.text(OLD_TEST);marker='    assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS[18],literal::fonts::FONT_PRODUCT_REQUEST_SCHEMA);\n';c.require(text.count(marker)==1,'ONE_NEW_CLOSED_SCHEMA_ASSERTION')
    text=text.replace(marker,'').replace('SEARCH_MUTATION_REQUEST_SCHEMAS.len(),19','SEARCH_MUTATION_REQUEST_SCHEMAS.len(),18').replace('collect::<BTreeSet<_>>().len(),19','collect::<BTreeSet<_>>().len(),18')
    audit.inverse(text,old[OLD_TEST],'LEGACY_TEST_BODY_ONLY_EXPECTED_SCHEMA_COUNT_AND_NEW_MEMBER_EXTENDED_NOT_EXECUTED')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'COMPILED_FONT_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_COMPILED_FONT_COMPONENTS',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,previous36_replayed=False,
        output_ingest_commit_or_publication=False,full_SEARCH024_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='cec5c861e4cd4a8386023d843835fc5cb0962479315cb282309e389e041d69ce'and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==745,'EXACT320_FONT_INVENTORY_AND_PRODUCT_BASELINE')
        old={p['path']:p for p in passed['source_pins']};names=closure.inventory(guard.check)|set(old)|NEW|CHANGED
        for n in sorted(names):
            q.pin(n)
            if n in old and n not in CHANGED:c.require(q.snapshots[n]==old[n],'ALL_OTHER_COMPILED_KERNEL_SCANNER_CRYPTO_POLICIES_AND_SOURCE_INPUTS_UNCHANGED')
            elif n not in old:c.require(n in NEW,'ONLY_DECLARED_FONT_COMPILER_SOURCE_AND_TEST_FILES_ADDED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases={'compiled_font_v1::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST))};c.require(len(cases)==20,'EXACT16_FONT_COMMON_AND4_AFFECTED_LEGACY_CASES')
        scratch=c.ROOT/'target/p09-compiled-font-scratch-323';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'COMPILED_FONT_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='COMPILED_FONT_PREFLIGHT',inputs=len(q.snapshots),font_common_cases=16,affected_legacy_cases=4,prior36_and_official249_replayed=False)),flush=True)
        harness.run_one('font_common_compiler16_and_legacy4',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','scoped_font_product',
            '--message-format=short','--','compiled_font_v1::','--test-threads=1'],cases,guard,env,row,observe_capture=base.snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'COMPILED_FONT_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_FONT_COMMON_COMPILER_DISPATCH16_LEGACY4_NOT_EXECUTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_font_common_cases=16,affected_legacy_cases=4,next_work='qualified_registry_manifest_and_actual_font_execution_storage_with_remaining_full_options_and_native')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'COMPILED_FONT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'COMPILED_FONT_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
