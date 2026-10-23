"""367: actual original mask edit inventory -> common23/compiler; strict mutation/preview ownership."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
shared,c,a,tools,compact,harness,audit=r.shared,r.c,r.a,r.tools,r.compact,r.harness,r.audit
OUTPUT='implementation/p09/evidence/p09-361-compiled-personal-info-mask367.v1.json';DRIVER='tools/p09/run_compiled_personal_info_mask.py'
BASE='implementation/p09/evidence/p09-361-personal-info-mask-product365.v1.json';DOCS='implementation/p09/evidence/p09-361-personal-info-mask-product-sync366.v1.json'
CORE='crates/hwpx-package/src/document_import/search/replacement/atoms/personal_info.rs';STORE='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/personal_info.rs'
PRODUCT='crates/product-cli/src/form_product_request/stored_literal_replacement/personal_info.rs';MUTATION=PRODUCT[:-3]+'/mutation.rs';ROOT_TEST='crates/product-cli/tests/personal_info_mask_product.rs';TEST='crates/product-cli/tests/support/personal_info_mask_compiled.rs'
COMMON='crates/product-cli/src/form_product_request/stored_operations.rs';REQUEST=COMMON[:-3]+'/request.rs';TABLE=COMMON[:-3]+'/search_mutations.rs';PROJECTION=COMMON[:-3]+'/compiled_search/projection.rs'
COUNTS={'crates/product-cli/tests/support/named_style_options_compiled.rs','crates/product-cli/tests/support/named_style_compiled.rs','crates/product-cli/tests/support/scoped_font_options_compiled.rs',
    'crates/product-cli/tests/support/scoped_font_compiled.rs','crates/product-cli/tests/form_stored_provider/actual_import/search_mutation_dispatch.rs'}
NEW={DRIVER,MUTATION,TEST};CHANGED={CORE,STORE,PRODUCT,ROOT_TEST,COMMON,REQUEST,TABLE,PROJECTION}|COUNTS
AFFECTED={'borrowed_owned_and_product_share_one_original_mask_receipt_and_verified_output','preview_discards_output_never_calls_byte_consumer_and_keeps_same_prediction',
    'exact_entire_metadata_envelope_and_one_byte_less_are_enforced_in_both_modes','request_key_plan_policy_and_mode_bind_hashes_without_disclosing_private_body'}
NAMED={'compiled_named::appended_named_family_preserves_first_twenty_positions','compiled_named::two_named_paragraphs_compile_to_two_actual_owners_not_first_node',
    'compiled_named::separate_preview_metadata_matches_standalone_and_has_no_output','named_options::compiled::twenty_second_family_owns_original_v2_receipt_and_matches_standalone_output',
    'named_options::compiled::physically_separate_preview_matches_original_metadata_and_has_no_file_output'}
FONTS={'compiled_font_v1::common_dispatch_font_receipt_and_output_match_standalone_and_keep_route_denied','compiled_font_v2::twentieth_family_preserves_original_nineteen_schema_positions'}
SOURCE={'exact_receipt_result_limit_is_enforced_independently_of_private_binding_hash','public_metadata_has_no_original_text_pieces_or_per_value_source_hashes'}
LINK='\n#[path="support/personal_info_mask_compiled.rs"]mod compiled;\n'

def remove(text,block):c.require(text.count(block)==1,'ONE_EXPLICIT_COMPILED_MASK_ADDITION');return text.replace(block,'')
def inverse(q,old):
    text=q.text(CORE);start=text.index('/// Immutable source/output/receipt-bound edit anchors.');end=text.index('pub struct SourcePersonalInfoMaskCandidate',start);text=text[:start]+text[end:]
    text=text.replace(',inventory:SourcePersonalInfoMaskEditInventory}','}')
    text=remove(text,'    #[must_use]pub const fn edit_inventory(&self)->&SourcePersonalInfoMaskEditInventory{&self.inventory}\n')
    start=text.index('        let anchors:Vec<_>=plan.changes.iter()');end=text.index('\n    }\n}',start)
    text=text[:start]+'        Ok(SourcePersonalInfoMaskCandidate{artifact,receipt,maximum_bytes:limits.maximum_result_bytes()})'+text[end:]
    audit.inverse(text,old[CORE],'ALL_ORIGINAL_MASKING_POLICIES_SELECTION_PROTECTION_WRITER_READBACK_RECEIPT_AND_OUTPUT_BYTES_UNCHANGED')
    text=remove(q.text(STORE),'compiler_source!(PreparedStoredPersonalInfoMaskCandidate);\n');text=remove(text,'    pub(crate) fn compiler_mask_inventory(&self)->&hwpx_package::document_import::search::replacement::atoms::personal_info::SourcePersonalInfoMaskEditInventory{self.output.edit_inventory()}\n')
    audit.inverse(text,old[STORE],'ALL_CURRENT_SOURCE_ACCESS_METADATA_LIMITS_OWNER_MOVE_AND_PREVIEW_ARTIFACT_DISCARD_UNCHANGED')
    text=remove(q.text(PRODUCT),'mod mutation;\npub use mutation::{StoredPersonalInfoMaskMutationRequest,PreparedStoredPersonalInfoMaskMutation,PreparedStoredPersonalInfoMaskPreviewProduct};\npub(crate) use mutation::preview_mode;\n')
    split='''        let request=Request::parse(raw)?;Self::prepare_parsed(provider,raw,request,limits,writer,now)
    }
    fn prepare_parsed<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],request:Request,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredPersonalInfoMaskProduct,M>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let maximum_metadata_bytes=limits.maximum_result_bytes();'''
    c.require(text.count(split)==1,'ONE_SHARED_MASK_PREPARATION_EXTRACTION');text=text.replace(split,'        let request=Request::parse(raw)?;let maximum_metadata_bytes=limits.maximum_result_bytes();')
    start=text.index('fn check_binding<Rp,B,S,V>');helper=text[start:];text=text[:start]
    body=helper[helper.index('        if p.profile'):].rsplit('\n}',1)[0]+'\n'
    text=text.replace('        let r=&self.request;\n','        let r=&self.request;let p=&self.receipt;let s=&p.stored;let o=&s.output;let scope=provider.source_search_product_scope(&r.project_id,&r.document_id)?;\n')
    text=text.replace('        check_binding(r,&self.receipt,expected,provider)\n',body)
    audit.inverse(text,old[PRODUCT],'ALL_ORIGINAL_STRICT_REQUEST_BINDINGS_SERVER_LIMITS_PRIVATE_METADATA_AND_PREVIEW_ERROR_BOUNDARIES_UNCHANGED')
    audit.inverse(remove(q.text(ROOT_TEST),LINK),old[ROOT_TEST],'ALL33_ORIGINAL_MASK_PRODUCT_TEST_BODIES_UNCHANGED')
    for path in COUNTS:
        text=q.text(path);text=re.sub(r'((?:SCHEMAS|SEARCH_MUTATION_REQUEST_SCHEMAS)(?:\.iter\(\)\.copied\(\)\.collect::<BTreeSet<_>>\(\))?\.len\(\),)23',r'\g<1>22',text)
        audit.inverse(text,old[path],'ONLY_SCHEMA_TABLE_LENGTH22_TO23_EXPECTATIONS_CHANGED_NOT_OTHER_TEST_BODIES')
    text=remove(q.text(TABLE),'use literal::personal_info;\n')
    text=remove(text,'''    (PersonalInfoMask, personal_info, StoredPersonalInfoMaskMutationRequest, PreparedStoredPersonalInfoMaskMutation, PersonalInfoMaskProductReceipt,
        personal_info::PersonalInfoMaskProductError, PERSONAL_INFO_MASK_PRODUCT_SCHEMA, text),
''')
    text=remove(text,'''    pub(crate) fn personal_info_mask_inventory(&self)->Option<&hwpx_package::document_import::search::replacement::atoms::personal_info::SourcePersonalInfoMaskEditInventory>{
        match self{Self::PersonalInfoMask(candidate)=>Some(candidate.compiler_mask_inventory()),_=>None}
    }
''');audit.inverse(text,old[TABLE],'ALL_FIRST22_FAMILY_POSITIONS_ERRORS_AND_DISPATCH_BODIES_UNCHANGED')
    text=q.text(PROJECTION);start=text.index('        Receipt::PersonalInfoMask(r)=>{');end=text.index('        Receipt::TextControl',start);audit.inverse(text[:start]+text[end:],old[PROJECTION],'ALL_OTHER_COMPILER_OWNER_AND_INVENTORY_PROJECTIONS_UNCHANGED')
    text=remove(q.text(REQUEST),'    PersonalInfoMaskPreview,\n');start=text.index('        super::super::stored_literal_replacement::personal_info::PERSONAL_INFO_MASK_PRODUCT_SCHEMA=>{');end=text.index('        schema =>',start)
    audit.inverse(text[:start]+text[end:],old[REQUEST],'ALL_ORIGINAL_COMMON_STRICT_CLASSIFICATION_PRE_READ_LIMITS_AND_PREVIEWS_UNCHANGED')
    text=remove(q.text(COMMON),'    PersonalInfoMaskPreview(Box<super::stored_literal_replacement::personal_info::PreparedStoredPersonalInfoMaskPreviewProduct>),\n')
    text=text.replace(' | Self::PersonalInfoMaskPreview(_)','').replace('Self::PersonalInfoMaskPreview(p)=>Ok(p.with_verified_json(provider,now,consume)?),','')
    text=remove(text,'''            Self::PersonalInfoMaskPreview(preview) => {
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(preview.require_current_product_route(provider,now)?)
            }
''');text=remove(text,'''            request::Kind::PersonalInfoMaskPreview => {
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(PreparedStoredProductOperation::PersonalInfoMaskPreview(Box::new(super::stored_literal_replacement::personal_info::StoredPersonalInfoMaskProductRequest::prepare_preview_json(provider,raw,limits.search,limits.writer,now)?)))
            }
''');text=remove(text,'''    #[error("product_operation_personal_info_mask_rejected")]
    PersonalInfoMask(#[from]super::stored_literal_replacement::personal_info::PersonalInfoMaskProductError),
''');audit.inverse(text,old[COMMON],'ALL_ORIGINAL_FORM_FORMULA_SEARCH_PREVIEW_AND_MUTATION_ACCESS_ERROR_PATHS_UNCHANGED')

def main(scratch_relative='target/p09-compiled-personal-info-mask-scratch-367'):
    c.require(not(c.ROOT/OUTPUT).exists(),'COMPILED_PERSONAL_INFO_MASK_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_COMPILED_PERSONAL_INFO_MASK',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,old_suites_replayed=False,
        source_document_mutation=False,output_ingest_commit_or_publication=False,whole_package_personal_data_removed=False,native_mask_semantics_qualified=False)
    try:
        guard.acquire();scratch=c.ROOT/scratch_relative;c.require(scratch.parent==c.ROOT/'target'and not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'COMPILED_MASK_EARLY_UNIQUE_TEMP')
        q=a.AcceptanceReader(c.ROOT,guard.check);before=compact.unpack(q.json(BASE));docs=q.json(DOCS)
        c.require(q.snapshots[BASE]['sha256']=='e20bcb78ea203d8ecfc0b4e8d7d09adb28d56e5838352de665c6603239ede3e0'and before['cleanup']and before['fresh_inputs']==before['final_fresh_hashes']==856,'EXACT365_FULL_SOURCE33_AND_AFFECTED3_TERMINAL')
        c.require(q.snapshots[DOCS]['sha256']=='661948d8b159eb195caebb099a6e2872e186cfdc678fab57cf678ef95b0ad661'and docs['cleanup'],'EXACT366_CURRENT_SERVICE_PRODUCT_DOC_BASELINE')
        old={p['path']:p for p in before['source_pins']}
        for path in sorted(r.closure.inventory(guard.check)|set(old)|NEW|CHANGED):
            q.pin(path)
            if path in old and path not in CHANGED:c.require(q.snapshots[path]==old[path],'ALL_OTHER_SOURCE_WRITER_PROTECTION_COMPILER_ROUTING_TESTS_AND_GUARDS_UNCHANGED')
            elif path not in old:c.require(path in NEW,'ONLY_MASK_MODE_OWNER_COMPILER_TEST_DRIVER_ADDED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases={'compiled::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST))};c.require(len(cases)==19,'EXACT19_COMPILED_MASK_MODE_AND_INVENTORY_CASES')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='COMPILED_PERSONAL_INFO_MASK_PREFLIGHT',inputs=len(q.snapshots),new_cases=19,affected_cases=13)),flush=True)
        for package,binary,label,selected in [('hwpx-agent-cli','personal_info_mask_product','compiled_mask19_affected_product4',cases|AFFECTED),
            ('hwpx-agent-cli','named_style_product','affected_named_common_v1_v2_five',NAMED),('hwpx-agent-cli','scoped_font_product','affected_font_common_schema_two',FONTS),
            ('hwpx-package','personal_info_mask','affected_source_mask_receipt_privacy_two',SOURCE)]:
            harness.run_one(label,[harness.CARGO,'test','--offline','--locked','-j','1','-p',package,'--test',binary,'--message-format=short','--',*sorted(selected),'--test-threads=1'],selected,guard,env,row,observe_capture=r.snapshot)
            tools.good_step(row['steps'][-1],selected)
        c.require(not any(scratch.iterdir()),'COMPILED_MASK_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_COMMON23_MASK_MUTATION_COMPILER19_AFFECTED13_SEPARATE_PREVIEW_NOT_EXECUTION_NATIVE_SANITIZATION_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=19,affected_cases=13,mutation_families=23,preview_never_enters_mutation_compiler=True,
            next_work='qualified_execution_storage_full_privacy_policy_search020_and_target_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'COMPILED_PERSONAL_INFO_MASK_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'COMPILED_MASK_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
