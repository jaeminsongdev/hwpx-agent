"""335: common v2 mutation owner/compiler and separate preview; new23 + affected common6/v2 six."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_font_options_product as previous
import run_sql23_storage as closure
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-compiled-font-options335.v1.json';DRIVER='tools/p09/run_compiled_font_options.py'
STORED=previous.STORED[:-3]+'/options.rs';PRODUCT=previous.PRODUCT[:-3]+'/options.rs';PARENT=previous.PARENT
COMMON='crates/product-cli/src/form_product_request/stored_operations.rs';REQUEST=COMMON[:-3]+'/request.rs';TABLE=COMMON[:-3]+'/search_mutations.rs'
PROJECTION=COMMON[:-3]+'/compiled_search/projection.rs';PREVIEW=COMMON[:-3]+'/search_preview.rs';MUTATION=PRODUCT[:-3]+'/mutation.rs'
TEST='crates/product-cli/tests/support/scoped_font_options_compiled.rs';OLD_COMPILED='crates/product-cli/tests/support/scoped_font_compiled.rs'
OLD_GIANT='crates/product-cli/tests/form_stored_provider/actual_import/search_mutation_dispatch.rs'
NEW={DRIVER,MUTATION,PREVIEW,TEST};CHANGED={STORED,PRODUCT,COMMON,REQUEST,TABLE,PROJECTION,PARENT,OLD_COMPILED,OLD_GIANT}
LINK='#[path="support/scoped_font_options_compiled.rs"]mod compiled_font_v2;\n'
AFFECTED_COMMON={'common_dispatch_font_receipt_and_output_match_standalone_and_keep_route_denied','compiled_font_plan_has_one_actual_body_owner_and_two_locked_header_resources',
    'legacy_width_keeps_original_twelve_argument_compiler_path','legacy_style_splices_keep_original_twelve_argument_compiler_path','legacy_regex_keeps_original_twelve_argument_compiler_path','legacy_permutation_keeps_original_twelve_argument_compiler_path'}
AFFECTED_V2={'preview_discards_output_and_matches_mutation_predicted_result_without_claiming_a_key','direct_borrowed_owned_and_preview_reuse_same_current_source_candidate',
    'original_definition_filter_reaches_product_without_default_axis_guess','final_head_race_in_preview_json_delivery_blocks_consumer',
    'final_head_race_in_mutation_metadata_delivery_blocks_consumer','required_preview_flag_and_closed_filter_shapes_reject_before_source_reads'}

def remove(text,marker):
    c.require(text.count(marker)==1,'ONE_DECLARED_COMPILER_OR_PREVIEW_ADDITION');return text.replace(marker,'')

def inverse(q,old):
    text=remove(q.text(STORED),'compiler_source!(PreparedStoredFontOptionsCandidate);\n')
    text=remove(text,'''    pub(crate) fn compiler_font_inventory(&self)->&hwpx_package::document_import::search::replacement::atoms::styles::fonts::inventory::SourceFontEditInventory{
        match &self.output{Output::Unfiltered(c)=>c.edit_inventory(),Output::Filtered(c)=>c.edit_inventory()}
    }
''');audit.inverse(text,old[STORED],'STORED_SOURCE_ACL_HEAD_AEAD_OUTPUT_DISCARD_AND_WRITER_GUARDS_UNCHANGED')
    text=remove(q.text(PRODUCT),'mod mutation;\npub use mutation::{PreparedStoredFontOptionsMutation,StoredFontOptionsMutationRequest};\npub(crate) use mutation::preview_mode;\n')
    text=remove(text,'''        Self::prepare_parsed(provider,raw,request,limits,writer,now)
    }
    fn prepare_parsed<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],request:Request,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredFontOptionsProduct,X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
''')
    start=text.index('fn check_binding<Rp,B,S,V>');helper=text[start:];c.require(helper.endswith('}\n'),'SHARED_BINDING_HELPER_IS_FINAL_ITEM');text=text[:start]
    clauses=helper[helper.index('    if r.schema_version'):].rsplit('\n}',1)[0]+'\n';clauses=''.join('    '+line for line in clauses.splitlines(keepends=True))
    text=text.replace('        let r=&self.request;\n','        let r=&self.request;let p=&self.receipt;let s=&p.stored;let output=s.output.source();let scope=provider.source_search_product_scope(&r.project_id,&r.document_id)?;\n')
    text=text.replace('        check_binding(&self.request,&self.receipt,expected,provider)\n',clauses)
    audit.inverse(text,old[PRODUCT],'V2_STRICT_PARSER_PREPARATION_ALL_BINDING_CLAUSES_CURRENT_ACCESS_AND_PREVIEW_DELIVERY_UNCHANGED')
    text=remove(q.text(TABLE),'use fonts::options as font_options;\n')
    text=remove(text,'''    (FontOptions, font_options, StoredFontOptionsMutationRequest, PreparedStoredFontOptionsMutation, FontOptionsProductReceipt,
        font_options::FontOptionsProductError, FONT_OPTIONS_REQUEST_SCHEMA, text),
''');text=remove(text,'Self::FontOptions(candidate)=>Some(candidate.compiler_font_inventory()),')
    audit.inverse(text,old[TABLE],'ALL_ORIGINAL19_FAMILY_ORDER_PREPARERS_RECEIPTS_ERRORS_AND_DELIVERY_PATHS_UNCHANGED')
    text=remove(q.text(PROJECTION),'''        Receipt::FontOptions(r)=>{
            let mut p=super::font_resources::project(candidate,r.stored.output.source())?;
            p.receipt_sha=bounded_hash(&r.stored.output,MAX_METADATA_BYTES)?;Ok(p)
        },
''');audit.inverse(text,old[PROJECTION],'ORIGINAL19_PROJECTIONS_AND_FONT_HEADER_RESOURCE_VALIDATION_UNCHANGED')
    text=remove(q.text(REQUEST),'    FontPreview,\n')
    text=remove(text,'''        super::super::stored_literal_replacement::fonts::options::FONT_OPTIONS_REQUEST_SCHEMA=>{
            let preview=super::super::stored_literal_replacement::fonts::options::preview_mode(raw)?;
            if preview{Ok(Kind::FontPreview)}else{Ok(Kind::SearchMutation(super::search_mutations::Family::FontOptions))}
        }
''');audit.inverse(text,old[REQUEST],'ALL_LEGACY_FORM_FORMULA_AND_SEARCH_CLASSIFICATION_UNCHANGED')
    text=remove(q.text(COMMON),'pub mod search_preview;\n');text=remove(text,'    SearchPreview(Box<search_preview::PreparedStoredSearchPreview>),\n')
    text=remove(text,'''            Self::SearchPreview(_) => {
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Err(StoredProductOperationError::PreviewOnly)
            }
''');text=remove(text,'''            Self::SearchPreview(preview) => {
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(preview.require_current_product_route(provider,now)?)
            }
''')
    start=text.index('impl PreparedStoredProductOperation {\n    /// # Errors\n');end=text.index('#[derive(Debug)]\npub struct StoredProductRequest;',start);text=text[:start]+text[end:]
    text=remove(text,'''            request::Kind::FontPreview => {
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(PreparedStoredProductOperation::SearchPreview(Box::new(search_preview::prepare(provider,raw,limits,now)?)))
            }
''');text=remove(text,'''    #[error("product_operation_font_options_rejected")]
    FontOptions(#[from]super::stored_literal_replacement::fonts::options::FontOptionsProductError),
    #[error("product_operation_preview_has_no_output")]
    PreviewOnly,
    #[error("product_operation_preview_kind_rejected")]
    PreviewKind,
''');audit.inverse(text,old[COMMON],'ALL_LEGACY_BINDINGS_DISPATCH_SOURCE_AND_ROUTE_DENIALS_UNCHANGED')
    text=remove(q.text(PARENT),LINK);audit.inverse(text,old[PARENT],'ALL_PREVIOUS108_PRODUCT_TEST_BODIES_UNCHANGED')
    text=q.text(OLD_COMPILED);c.require(text.count('len(),20')==2,'ONLY_TWO_EXISTING_FAMILY_COUNTS_CHANGED')
    text=remove(text,'assert_eq!(SCHEMAS[19],hwpx_agent_cli::form_product_request::stored_literal_replacement::fonts::options::FONT_OPTIONS_REQUEST_SCHEMA);')
    audit.inverse(text.replace('len(),20','len(),19'),old[OLD_COMPILED],'ALL_OLD20_COMPILED_FONT_AND_LEGACY_TEST_BODIES_EXCEPT_SCHEMA_COUNT_UNCHANGED')
    text=q.text(OLD_GIANT);c.require(text.count('len(),20')==2,'ONLY_TWO_GIANT_FAMILY_COUNTS_CHANGED')
    text=remove(text,'    assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS[19],literal::fonts::options::FONT_OPTIONS_REQUEST_SCHEMA);\n')
    audit.inverse(text.replace('len(),20','len(),19'),old[OLD_GIANT],'OLD_GIANT_DISPATCH_TEST_EXCEPT_APPENDED_FAMILY_ASSERTIONS_UNCHANGED_NOT_EXECUTED')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'COMPILED_FONT_OPTIONS_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_COMPILED_FONT_OPTIONS',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,
        output_ingest_commit_or_publication=False,full_SEARCH024_product_or_native_qualified=False,old_giant_suite_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='545d365f0a65a678624607f5d1411385291a1b12b5592d42ccd4f5c2e1e4cf0f'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==774 and passed['new_cases']==28,'EXACT333_STORED_V2_PREVIEW32_BASELINE')
        old={p['path']:p for p in passed['source_pins']};names=closure.inventory(guard.check)|set(old)|NEW
        for n in sorted(names):
            q.pin(n)
            if n in old and n not in CHANGED:c.require(q.snapshots[n]==old[n],'ALL_OTHER_PRODUCTION_TEST_AND_VERIFIER_INPUTS_UNCHANGED')
            elif n not in old:c.require(n in NEW,'ONLY_DECLARED_MUTATION_OWNER_PREVIEW_ADAPTER_TEST_AND_DRIVER_ADDED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases={'compiled_font_v2::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST))}|{'compiled_font_v1::'+n for n in AFFECTED_COMMON}|{'font_options_v2::'+n for n in AFFECTED_V2}
        c.require(len(cases)==35 and len(AFFECTED_COMMON)==len(AFFECTED_V2)==6,'EXACT_NEW23_AFFECTED_COMMON6_V2_SIX')
        scratch=c.ROOT/'target/p09-compiled-font-options-scratch-335';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'COMPILED_FONT_OPTIONS_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='COMPILED_FONT_OPTIONS_PREFLIGHT',inputs=len(q.snapshots),new_cases=23,affected_cases=12,official249_replayed=False)),flush=True)
        harness.run_one('compiled_font_options23_affected_common6_product6',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','scoped_font_product',
            '--message-format=short','--',*sorted(cases),'--test-threads=1'],cases,guard,env,row,observe_capture=previous.previous.previous.previous.snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'COMPILED_FONT_OPTIONS_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_COMMON_FONT_V2_MUTATION_COMPILER_SEPARATE_PREVIEW23_AFFECTED12_NOT_EXECUTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=23,affected_cases=12,preview_never_enters_mutation_compiler=True,full_filtered_receipt_bound_to_plan=True,
            next_work='remaining_full_font_options_effective_formatting_protection_and_qualified_execution_storage')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'COMPILED_FONT_OPTIONS_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'COMPILED_FONT_OPTIONS_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
