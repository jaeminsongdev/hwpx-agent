"""345: current named mutation owner/compiler and separate preview; focused new/affected cases only."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_named_style_product_metadata as previous
import run_sql23_storage as closure
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-compiled-named-styles345.v1.json';DRIVER='tools/p09/run_compiled_named_styles.py'
STORED=previous.previous.STORED;PRODUCT=previous.PRODUCT;PARENT=previous.TEST
COMMON='crates/product-cli/src/form_product_request/stored_operations.rs';REQUEST=COMMON[:-3]+'/request.rs';TABLE=COMMON[:-3]+'/search_mutations.rs'
PROJECTION=COMMON[:-3]+'/compiled_search/projection.rs';MUTATION=PRODUCT[:-3]+'/mutation.rs';TEST='crates/product-cli/tests/support/named_style_compiled.rs'
OLD_FONT='crates/product-cli/tests/support/scoped_font_compiled.rs';OLD_OPTIONS='crates/product-cli/tests/support/scoped_font_options_compiled.rs'
OLD_GIANT='crates/product-cli/tests/form_stored_provider/actual_import/search_mutation_dispatch.rs'
NEW={DRIVER,MUTATION,TEST};CHANGED={STORED,PRODUCT,PARENT,COMMON,REQUEST,TABLE,PROJECTION,OLD_FONT,OLD_OPTIONS,OLD_GIANT}
LINK='#[path="support/named_style_compiled.rs"]mod compiled_named;\n'
AFFECTED_NAMED={'preview_predicts_same_result_but_discards_output_and_never_calls_byte_consumer','exact_server_metadata_envelope_limit_and_one_byte_less_are_enforced',
    'required_root_fields_preview_flag_and_string_enum_shapes_reject_before_reads'}
AFFECTED_FONT={'compiled_font_v1::common_dispatch_font_receipt_and_output_match_standalone_and_keep_route_denied',
    'compiled_font_v1::compiled_font_plan_has_one_actual_body_owner_and_two_locked_header_resources',
    'compiled_font_v1::legacy_width_keeps_original_twelve_argument_compiler_path','compiled_font_v1::legacy_style_splices_keep_original_twelve_argument_compiler_path',
    'compiled_font_v1::legacy_regex_keeps_original_twelve_argument_compiler_path','compiled_font_v1::legacy_permutation_keeps_original_twelve_argument_compiler_path',
    'compiled_font_v2::appended_v2_family_preserves_all_nineteen_original_schema_positions',
    'compiled_font_v2::common_preview_is_separate_variant_json_only_and_matches_standalone_metadata',
    'compiled_font_v2::compiler_and_mutation_only_request_reject_preview_before_artifact_reads'}

def remove(text,marker):
    c.require(text.count(marker)==1,'ONE_DECLARED_NAMED_COMMON_ADDITION');return text.replace(marker,'')

def inverse(q,old):
    audit.inverse(remove(q.text(STORED),'compiler_source!(PreparedStoredNamedStyleCandidate);\n'),old[STORED],'ALL_CURRENT_SOURCE_HEAD_ACL_AEAD_WRITER_AND_PREVIEW_DISCARD_GUARDS_UNCHANGED')
    text=remove(q.text(PRODUCT),'mod mutation;\npub use mutation::{PreparedStoredNamedStyleMutation,StoredNamedStyleMutationRequest,PreparedStoredNamedStylePreviewProduct};\npub(crate) use mutation::preview_mode;\n')
    text=remove(text,'''        Self::prepare_parsed(provider,raw,request,limits,writer,now)
    }
    fn prepare_parsed<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],request:Request,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredNamedStyleProduct,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
''')
    start=text.index('fn check_binding<Rp,B,S,V>');helper=text[start:];c.require(helper.endswith('}\n'),'SHARED_BINDING_HELPER_FINAL_ITEM');text=text[:start]
    body=helper[helper.index('        if maximum_metadata_bytes'):].rsplit('\n}',1)[0]+'\n'
    body=body.replace('if maximum_metadata_bytes==0||maximum_metadata_bytes>','if self.maximum_metadata_bytes==0||self.maximum_metadata_bytes>')
    text=text.replace('        let r=&self.request;\n','        let r=&self.request;let p=&self.receipt;let s=&p.stored;let output=&s.output;let scope=provider.source_search_product_scope(&r.project_id,&r.document_id)?;\n')
    text=text.replace('        check_binding(r,&self.receipt,expected,self.maximum_metadata_bytes,provider)\n',body)
    text=text.replace('Preparation is not issuer, durable claim, CAS, Native execution or publication authority.','No common dispatcher, issuer, durable claim, CAS, Native execution or publication authority.')
    audit.inverse(text,old[PRODUCT],'ALL_STRICT_PARSE_PREPARATION_BINDING_CLAUSES_SERVER_METADATA_AND_DELIVERY_PRESERVED')
    text=remove(q.text(TABLE),'use literal::named_styles;\n')
    text=remove(text,'''    (NamedStyle, named_styles, StoredNamedStyleMutationRequest, PreparedStoredNamedStyleMutation, NamedStyleProductReceipt,
        named_styles::NamedStyleProductError, NAMED_STYLE_PRODUCT_REQUEST_SCHEMA, text),
''');audit.inverse(text,old[TABLE],'ALL_ORIGINAL20_FAMILY_POSITIONS_AND_PREPARERS_UNCHANGED')
    text=remove(q.text(PROJECTION),'        Receipt::NamedStyle(r)=>{let p=&r.stored.output;collect(p,p.source_package_sha256,p.output_package_sha256,"changes",p.changes.iter().map(|e|&e.paragraph_anchor))},\n')
    audit.inverse(text,old[PROJECTION],'ALL_ORIGINAL20_PROJECTIONS_FONT_RESOURCES_AND_SPLICES_UNCHANGED')
    text=remove(q.text(REQUEST),'    NamedStylePreview,\n')
    text=remove(text,'''        super::super::stored_literal_replacement::named_styles::NAMED_STYLE_PRODUCT_REQUEST_SCHEMA=>{
            let preview=super::super::stored_literal_replacement::named_styles::preview_mode(raw)?;
            if preview{Ok(Kind::NamedStylePreview)}else{Ok(Kind::SearchMutation(super::search_mutations::Family::NamedStyle))}
        }
''');audit.inverse(text,old[REQUEST],'ALL_OLD_SCHEMA_AND_FONT_MODE_CLASSIFICATION_UNCHANGED')
    text=remove(q.text(COMMON),'    NamedStylePreview(Box<super::stored_literal_replacement::named_styles::PreparedStoredNamedStylePreviewProduct>),\n')
    text=text.replace('Self::SearchPreview(_) | Self::NamedStylePreview(_)','Self::SearchPreview(_)')
    text=remove(text,'''            Self::NamedStylePreview(preview) => {
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(preview.require_current_product_route(provider,now)?)
            }
''')
    text=remove(text,'Self::NamedStylePreview(p)=>Ok(p.with_verified_json(provider,now,consume)?),')
    text=remove(text,'''            request::Kind::NamedStylePreview => {
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(PreparedStoredProductOperation::NamedStylePreview(Box::new(super::stored_literal_replacement::named_styles::StoredNamedStyleProductRequest::prepare_preview_json(provider,raw,limits.search,limits.writer,now)?)))
            }
''')
    text=remove(text,'''    #[error("product_operation_named_style_rejected")]
    NamedStyle(#[from]super::stored_literal_replacement::named_styles::NamedStyleProductError),
''');audit.inverse(text,old[COMMON],'LEGACY_FORM_FORMULA_FONT_PREVIEW_BYTES_BINDINGS_AND_ROUTE_DENIALS_UNCHANGED')
    audit.inverse(remove(q.text(PARENT),LINK),old[PARENT],'ALL_PREVIOUS31_NAMED_PRODUCT_TEST_BODIES_UNCHANGED')
    for path in (OLD_FONT,OLD_OPTIONS,OLD_GIANT):
        text=q.text(path);c.require(text.count('len(),21')==2,'TWO_SCHEMA_COUNT_EXPECTATIONS_ONLY');text=text.replace('len(),21','len(),20')
        marker=('    assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS[20],literal::named_styles::NAMED_STYLE_PRODUCT_REQUEST_SCHEMA);\n'if path==OLD_GIANT else'assert_eq!(SCHEMAS[20],hwpx_agent_cli::form_product_request::stored_literal_replacement::named_styles::NAMED_STYLE_PRODUCT_REQUEST_SCHEMA);')
        audit.inverse(remove(text,marker),old[path],'ORIGINAL_FONT_AND_GIANT_TEST_BODIES_EXCEPT_APPENDED_SCHEMA_ASSERTION_UNCHANGED')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'COMPILED_NAMED_STYLE_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_COMPILED_NAMED_STYLES',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,old_giant_suite_executed=False,
        output_ingest_commit_or_publication=False,full_SEARCH025_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='9602e98eecd230c3ff3c351bd8a9e8a86734bbb66a373ceb8a8a6cc718131130'and passed['cleanup']
            and passed['distinct_product_cases']==31 and passed['new_cases']==2 and passed['affected_cases']==3,'EXACT344_NAMED_METADATA31_BASELINE')
        old={p['path']:p for p in passed['source_pins']};names=closure.inventory(guard.check)|set(old)|NEW
        for n in sorted(names):
            q.pin(n)
            if n in old and n not in CHANGED:c.require(q.snapshots[n]==old[n],'ALL_OTHER_CORE_TEST_AUTHORITY_AND_VERIFIER_INPUTS_UNCHANGED')
            elif n not in old:c.require(n in NEW,'ONLY_DECLARED_NAMED_MODE_OWNER_TEST_AND_DRIVER_ADDED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases={'compiled_named::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST))}
        c.require(len(cases)==19 and len(AFFECTED_NAMED)==3 and len(AFFECTED_FONT)==9,'EXACT_NEW19_AFFECTED_NAMED3_COMMON9')
        scratch=c.ROOT/'target/p09-compiled-named-styles-scratch-345';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'COMPILED_NAMED_STYLE_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='COMPILED_NAMED_STYLE_PREFLIGHT',inputs=len(q.snapshots),new_cases=19,affected_cases=12)),flush=True)
        for binary,label,selected in [('named_style_product','compiled_named_new19_affected3',cases|AFFECTED_NAMED),('scoped_font_product','affected_common_font_and_legacy9',AFFECTED_FONT)]:
            harness.run_one(label,[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test',binary,'--message-format=short','--',*sorted(selected),'--test-threads=1'],selected,guard,env,row,
                observe_capture=previous.previous.previous.base.snapshot)
            tools.good_step(row['steps'][-1],selected)
        c.require(not any(scratch.iterdir()),'COMPILED_NAMED_STYLE_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_COMMON_NAMED_STYLE_MUTATION_COMPILER_SEPARATE_PREVIEW19_AFFECTED12_NOT_EXECUTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=19,affected_cases=12,mutation_families=21,preview_never_enters_mutation_compiler=True,full_named_output_receipt_bound_to_plan=True,
            next_work='named_character_styles_filters_full_options_and_qualified_execution_storage')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'COMPILED_NAMED_STYLE_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'COMPILED_NAMED_STYLE_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
