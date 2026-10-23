"""351: original v2 optional-filter candidate to common22/compiler and separate preview; new18/affected9."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
from named_style_verification_runtime import shared,c,a,tools,compact,harness,audit,closure,snapshot
previous=NS(OUTPUT='implementation/p09/evidence/p09-361-named-style-options-product350.v1.json',
    STORED='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/named_styles/options.rs',
    PRODUCT='crates/product-cli/src/form_product_request/stored_literal_replacement/named_styles/options.rs',TEST='crates/product-cli/tests/support/named_style_options_product.rs')
OUTPUT='implementation/p09/evidence/p09-361-compiled-named-style-options351.v1.json';DRIVER='tools/p09/run_compiled_named_style_options.py'
STORED=previous.STORED;PRODUCT=previous.PRODUCT;OLD_OPTIONS=previous.TEST;MUTATION=PRODUCT[:-3]+'/mutation.rs';TEST='crates/product-cli/tests/support/named_style_options_compiled.rs'
COMMON='crates/product-cli/src/form_product_request/stored_operations.rs';REQUEST=COMMON[:-3]+'/request.rs';TABLE=COMMON[:-3]+'/search_mutations.rs';PROJECTION=COMMON[:-3]+'/compiled_search/projection.rs'
OLD_NAMED='crates/product-cli/tests/support/named_style_compiled.rs';OLD_FONT='crates/product-cli/tests/support/scoped_font_compiled.rs';OLD_FONT_OPTIONS='crates/product-cli/tests/support/scoped_font_options_compiled.rs';OLD_GIANT='crates/product-cli/tests/form_stored_provider/actual_import/search_mutation_dispatch.rs'
IMPORT_FAILURE='implementation/p09/evidence/p09-361-compiled-named-options-import351.v1.json';RUNTIME='tools/p09/named_style_verification_runtime.py'
NEW={DRIVER,MUTATION,TEST,RUNTIME,IMPORT_FAILURE};CHANGED={STORED,PRODUCT,OLD_OPTIONS,COMMON,REQUEST,TABLE,PROJECTION,OLD_NAMED,OLD_FONT,OLD_FONT_OPTIONS,OLD_GIANT};LINK='#[path="named_style_options_compiled.rs"]mod compiled;\n'
AFFECTED_OPTIONS={'named_options::'+n for n in('v1_stays_closed_and_foreign_v2_schema_rejects_before_source_reads','required_mode_and_closed_filter_shapes_are_rejected_before_source_reads',
    'preview_predicts_same_candidate_but_drops_output_and_never_calls_file_consumer','borrowed_owned_and_product_share_same_original_filtered_receipt_and_output',
    'exact_outer_server_metadata_limit_and_one_byte_less_are_enforced','entire_filter_request_hashes_are_bound_and_private_names_body_and_keys_are_redacted')}
AFFECTED_COMMON={'compiled_named::'+n for n in('appended_named_family_preserves_first_twenty_positions','two_named_paragraphs_compile_to_two_actual_owners_not_first_node','separate_preview_metadata_matches_standalone_and_has_no_output')}

# Import failure preimage reconstruction begin.
def preserve_import_failure(q):
    failure=q.json(IMPORT_FAILURE);text=q.text(DRIVER)
    start=text.index('# Import failure preimage reconstruction begin.\n');end=text.index('# Import failure preimage reconstruction end.\n',start)+len('# Import failure preimage reconstruction end.\n')
    text=text[:start]+text[end:];text=remove(text,'        preserve_import_failure(q)\n')
    text=text.replace("from named_style_verification_runtime import shared,c,a,tools,compact,harness,audit,closure,snapshot\nprevious=NS(OUTPUT='implementation/p09/evidence/p09-361-named-style-options-product350.v1.json',\n    STORED='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/named_styles/options.rs',\n    PRODUCT='crates/product-cli/src/form_product_request/stored_literal_replacement/named_styles/options.rs',TEST='crates/product-cli/tests/support/named_style_options_product.rs')\n",failure['original_import_block'])
    text=remove(text,"IMPORT_FAILURE='implementation/p09/evidence/p09-361-compiled-named-options-import351.v1.json';RUNTIME='tools/p09/named_style_verification_runtime.py'\n")
    text=text.replace('NEW={DRIVER,MUTATION,TEST,RUNTIME,IMPORT_FAILURE}','NEW={DRIVER,MUTATION,TEST}').replace('observe_capture=snapshot','observe_capture='+failure['original_observer_expression'])
    audit.inverse(text,dict(sha256=failure['driver_sha256'],bytes=len(text.encode('utf-8'))),'EXACT_ORIGINAL351_IMPORT_FAILURE_DRIVER_RECONSTRUCTED')
    c.require(not failure['owned_job_started']and not failure['Cargo_started']and failure['tests_started']==0 and sys.getrecursionlimit()==1000,'IMPORT_FAILURE_BEFORE_RUNTIME_AND_DEFAULT_RECURSION_LIMIT_RETAINED')
# Import failure preimage reconstruction end.
def remove(text,marker):c.require(text.count(marker)==1,'ONE_DECLARED_NAMED_OPTIONS_COMMON_ADDITION');return text.replace(marker,'')
def inverse(q,old):
    audit.inverse(remove(q.text(STORED),'compiler_source!(PreparedStoredNamedStyleOptionsCandidate);\n'),old[STORED],'STORED_FILTER_BINDINGS_SOURCE_WRITER_AND_OUTPUT_DISCARD_UNCHANGED')
    text=remove(q.text(PRODUCT),'mod mutation;\npub use mutation::{PreparedStoredNamedStyleOptionsMutation,StoredNamedStyleOptionsMutationRequest,PreparedStoredNamedStyleOptionsPreviewProduct};\npub(crate) use mutation::preview_mode;\n')
    text=remove(text,'''        Self::prepare_parsed(provider,raw,request,limits,writer,now)
    }
    fn prepare_parsed<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],request:Request,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredNamedStyleOptionsProduct,X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
''').replace('        let request=Request::parse(raw)?;\n        let maximum_metadata_bytes=','        let request=Request::parse(raw)?;let maximum_metadata_bytes=')
    start=text.index('fn check_binding<Rp,B,S,V>');helper=text[start:];c.require(helper.endswith('}\n'),'SHARED_OPTIONS_BINDING_HELPER_FINAL_ITEM');text=text[:start]
    body=helper[helper.index('        if maximum_metadata_bytes'):].rsplit('\n}',1)[0]+'\n';body=body.replace('if maximum_metadata_bytes==0||maximum_metadata_bytes>','if self.maximum_metadata_bytes==0||self.maximum_metadata_bytes>')
    text=text.replace('        let r=&self.request;\n','        let r=&self.request;let p=&self.receipt;let s=&p.stored;let output=s.output.source();let scope=provider.source_search_product_scope(&r.project_id,&r.document_id)?;\n').replace('        check_binding(r,&self.receipt,expected,self.maximum_metadata_bytes,provider)\n',body)
    audit.inverse(text,old[PRODUCT],'ALL_V2_STRICT_PARSE_PREPARATION_BINDING_CLAUSES_SERVER_BUDGETS_AND_DELIVERY_UNCHANGED')
    text=remove(q.text(TABLE),'use named_styles::options as named_options;\n');text=remove(text,'''    (NamedStyleOptions, named_options, StoredNamedStyleOptionsMutationRequest, PreparedStoredNamedStyleOptionsMutation, NamedStyleOptionsProductReceipt,
        named_styles::NamedStyleProductError, NAMED_STYLE_OPTIONS_REQUEST_SCHEMA, text),
''');audit.inverse(text,old[TABLE],'ALL_ORIGINAL21_FAMILY_POSITIONS_AND_PREPARERS_UNCHANGED')
    text=remove(q.text(PROJECTION),'        Receipt::NamedStyleOptions(r)=>{let p=&r.stored.output;let s=p.source();collect(p,s.source_package_sha256,s.output_package_sha256,"changes",s.changes.iter().map(|e|&e.paragraph_anchor))},\n');audit.inverse(text,old[PROJECTION],'ALL_ORIGINAL21_PROJECTIONS_AND_OWNER_DOMAINS_UNCHANGED')
    text=remove(q.text(REQUEST),'    NamedStyleOptionsPreview,\n');text=remove(text,'''        super::super::stored_literal_replacement::named_styles::options::NAMED_STYLE_OPTIONS_REQUEST_SCHEMA=>{
            let preview=super::super::stored_literal_replacement::named_styles::options::preview_mode(raw)?;
            if preview{Ok(Kind::NamedStyleOptionsPreview)}else{Ok(Kind::SearchMutation(super::search_mutations::Family::NamedStyleOptions))}
        }
''');audit.inverse(text,old[REQUEST],'ALL_LEGACY_FORM_FORMULA_FONT_AND_NAMED_V1_CLASSIFICATION_UNCHANGED')
    text=remove(q.text(COMMON),'    NamedStyleOptionsPreview(Box<super::stored_literal_replacement::named_styles::options::PreparedStoredNamedStyleOptionsPreviewProduct>),\n')
    text=text.replace('Self::SearchPreview(_) | Self::NamedStylePreview(_) | Self::NamedStyleOptionsPreview(_)','Self::SearchPreview(_) | Self::NamedStylePreview(_)')
    text=remove(text,'''            Self::NamedStyleOptionsPreview(preview) => {
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(preview.require_current_product_route(provider,now)?)
            }
''');text=remove(text,'Self::NamedStyleOptionsPreview(p)=>Ok(p.with_verified_json(provider,now,consume)?),')
    text=remove(text,'''            request::Kind::NamedStyleOptionsPreview => {
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(PreparedStoredProductOperation::NamedStyleOptionsPreview(Box::new(super::stored_literal_replacement::named_styles::options::StoredNamedStyleOptionsProductRequest::prepare_preview_json(provider,raw,limits.search,limits.writer,now)?)))
            }
''');audit.inverse(text,old[COMMON],'ORIGINAL_BYTES_PREVIEW_BINDINGS_AND_ROUTE_DENIALS_UNCHANGED')
    text=remove(q.text(OLD_OPTIONS),LINK).replace('v1_stays_closed_and_foreign_v2_schema_rejects_before_source_reads','v1_stays_closed_and_v2_does_not_claim_common_dispatch_or_compiler_support')
    text=remove(text,'    let mut foreign=good;foreign["schema_version"]=json!("hwpx-agent.product-named-paragraph-style-replacement-request/v999");\n').replace('&wire(&foreign)?','&wire(&good)?')
    audit.inverse(text,old[OLD_OPTIONS],'ALL_PREVIOUS28_V2_TEST_BODIES_EXCEPT_NEW_COMMON_SCHEMA_SUPPORT_EXPECTATION_UNCHANGED')
    for path in(OLD_NAMED,OLD_FONT,OLD_FONT_OPTIONS,OLD_GIANT):
        text=q.text(path);c.require(text.count('len(),22')==2,'ONLY_TWO_FAMILY_COUNT_ASSERTIONS_CHANGED');audit.inverse(text.replace('len(),22','len(),21'),old[path],'ALL_PRIOR_COMMON_TEST_BODIES_EXCEPT_FAMILY_COUNT_UNCHANGED')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'COMPILED_NAMED_OPTIONS_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_COMPILED_NAMED_OPTIONS',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,old_suites_replayed=False,
        output_ingest_commit_or_publication=False,full_SEARCH025_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='04f732999478a7068a2b5c2063e967f34f0c1cde750401e63f7b38e1b0f75788'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==815 and passed['new_cases']==28 and passed['affected_cases']==4,'EXACT350_STORED_STRICT_V2_PREVIEW28_BASELINE')
        old={p['path']:p for p in passed['source_pins']};names=closure.inventory(guard.check)|set(old)|NEW
        for n in sorted(names):
            q.pin(n)
            if n in old and n not in CHANGED:c.require(q.snapshots[n]==old[n],'ALL_OTHER_CORE_STORED_PRODUCT_WRITER_AND_RESOURCE_GUARDS_UNCHANGED')
            elif n not in old:c.require(n in NEW,'ONLY_DECLARED_OPTIONS_MODE_OWNER_TEST_AND_DRIVER_ADDED')
        inverse(q,old)
        preserve_import_failure(q)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases={'named_options::compiled::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST))}|AFFECTED_OPTIONS|AFFECTED_COMMON
        c.require(len(cases)==27 and len(AFFECTED_OPTIONS)==6 and len(AFFECTED_COMMON)==3,'EXACT_NEW18_AFFECTED_V2_SIX_COMMON_THREE')
        scratch=c.ROOT/'target/p09-compiled-named-style-options-scratch-351';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'COMPILED_NAMED_OPTIONS_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='COMPILED_NAMED_OPTIONS_PREFLIGHT',inputs=len(q.snapshots),new_cases=18,affected_cases=9)),flush=True)
        harness.run_one('compiled_named_options18_affected_v2_six_common_three',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','named_style_product','--message-format=short','--',*sorted(cases),'--test-threads=1'],cases,guard,env,row,
            observe_capture=snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'COMPILED_NAMED_OPTIONS_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_COMMON_NAMED_OPTIONS_MUTATION_COMPILER_SEPARATE_PREVIEW18_AFFECTED9_NOT_EXECUTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=18,affected_cases=9,mutation_families=22,preview_never_enters_mutation_compiler=True,full_optional_filter_output_receipt_bound_to_plan=True,
            next_work='named_character_style_semantics_full_options_and_qualified_execution_storage')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'COMPILED_NAMED_OPTIONS_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'COMPILED_NAMED_OPTIONS_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
