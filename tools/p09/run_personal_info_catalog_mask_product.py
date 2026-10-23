"""431: strict catalog-mask products/shared compiler40 + affected legacy3; no Native or commit."""
import json,re,subprocess,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_personal_info_catalog_mask as prior
r,layout=prior.r,prior.layout
OUTPUT='implementation/p09/evidence/p09-361-personal-info-catalog-mask-product431.v1.json'
DRIVER='tools/p09/run_personal_info_catalog_mask_product.py'
BASE='implementation/p09/evidence/p09-361-personal-info-catalog-mask-recovery428.v1.json'
PRODUCT='crates/product-cli/src/form_product_request/stored_literal_replacement/personal_info/catalog.rs'
COMPILER='crates/product-cli/src/form_product_request/stored_operations/compiled_search/catalog_mask.rs'
PARENT='crates/product-cli/src/form_product_request/stored_literal_replacement/personal_info.rs'
COMMON='crates/product-cli/src/form_product_request/stored_operations/compiled_search.rs'
SERVICE='crates/product-cli/src/form_stored_provider/actual_import/source_search/personal_info_catalog/mask.rs'
LINK='crates/product-cli/tests/support/personal_info_catalog_mask_stored.rs'
TEST='crates/product-cli/tests/support/personal_info_catalog_mask_product.rs'
PREFIX='stored_catalog::mask::product::'
CONFIG=Path(r'C:\Program Files (x86)\HNC\Office 2020\HOffice110\Bin\PrivateInfo.ini')
CHANGED={PARENT,COMMON,SERVICE,LINK}
AFFECTED={'compiled::appended_twenty_third_family_preserves_original_twenty_two_schema_positions',
    'compiled::compiled_mask_targets_actual_text_anchors_and_locks_twelve_arguments','compiled::final_compilation_head_race_rejects'}


def original_service(text):
    candidate="""    pub(crate) fn compiler_source(&self)->&StoredImportedDocumentForms{&self.source}
    pub(crate) fn compiler_mask_inventory(&self)->&hwpx_package::document_import::search::replacement::atoms::personal_info::SourcePersonalInfoMaskEditInventory{self.output.edit_inventory()}
"""
    final="""    pub(crate) fn check_final_inputs<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource)->Result<(),M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        verify_catalog(catalog,&self.receipt.output.catalog)?;provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(())
    }
"""
    r.c.require(text.count(candidate)==1 and text.count(final)==2,'EXACT_ADDITIVE_SOURCE_INVENTORY_AND_FINAL_INPUT_HELPERS')
    return text.replace(candidate,'').replace(final,'')


def original_common(text):
    added="""    receipt_for_view(&candidate.compiler_view(),candidate.schema_version(),plan,p)
}
fn receipt_for_view(v:&CompilationView<'_>,schema:&'static str,plan:&CompiledOperationPlan,p:&projection::Projection<'_>)->Result<CompiledSearchReceipt,CompiledSearchError>{
    let source=v.source.receipt();let graph=v.source.imported().graph();let head=v.source.compiler_head();"""
    original="    let v=candidate.compiler_view();let source=v.source.receipt();let graph=v.source.imported().graph();let head=v.source.compiler_head();"
    r.c.require(text.count('pub mod catalog_mask;\n')==1 and text.count(added)==1 and text.count('request_schema:schema,')==1,'ONE_SHARED_RECEIPT_VIEW_EXTRACTION_NO_ALGORITHM_CHANGE')
    return text.replace('pub mod catalog_mask;\n','').replace(added,original).replace('request_schema:schema,','request_schema:candidate.schema_version(),')


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'CATALOG_MASK_PRODUCT431_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;final_attempted=False;started=time.monotonic();row=dict(state='FAILED_PERSONAL_INFO_CATALOG_MASK_PRODUCT431',steps=[],own_cpu_selection=selection,
        actual_DB_Hangul_or_COM_started=False,Native011_executed=False,prior_Native_replayed=False,official249_replayed=False,
        prior_source30_or_stored20_replayed=False,private_user_catalog_accessed=False,installed_catalog_mutated=False,
        same_common_operation_compiler_and_actual_owner_resolver=True,context_free_dispatcher_has_no_catalog_fallback=True,
        source_document_mutation=False,ingest_commit_or_publication=False,native_catalog_mask_semantics_or_service_execution_qualified=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='7874d8df4e887e5a52d96cd405c40cc017331cefbba0cd9f3377b155500b1fc0'
            and base['cleanup']is True and base['current_distinct_cases']==50 and base['fresh_inputs']==base['final_fresh_hashes']==844,'EXACT428_SOURCE30_STORED20_ACCEPTANCE_RETAINED')
        old={p['path']:p for p in base['source_pins']};expected=set(base['actual_stored_test_inputs'][0]['dependency_paths'])|{TEST}
        names=set(old)|r.shared.source_inventory(guard.check)|{DRIVER,PRODUCT,COMPILER,TEST}|expected
        for path in sorted(names):
            pin=q.pin(path)
            if path in old and path not in CHANGED:c.require(pin==old[path],'ALL_OTHER_PASSED_LIBRARY_TEST_AND_EXECUTION_GUARD_INPUTS_UNCHANGED')
        text=q.text(PARENT);c.require(text.count('pub mod catalog;\n')==1,'ONE_CATALOG_MASK_PRODUCT_EXPORT')
        r.audit.inverse(text.replace('pub mod catalog;\n',''),old[PARENT],'ALL_ORIGINAL_SELECTED_MASK_PRODUCT_AND_MUTATION_CODE_PRESERVED')
        text=q.text(LINK);added='mod product{include!("personal_info_catalog_mask_product.rs");}\n';c.require(text.count(added)==1,'ONE_ADDITIVE_PRODUCT_TEST_LINK')
        r.audit.inverse(text.replace(added,''),old[LINK],'ALL_PREVIOUS_STORED20_TEST_BODIES_PRESERVED')
        r.audit.inverse(original_service(q.text(SERVICE)),old[SERVICE],'ALL_ORIGINAL_SOURCE_CONFIG_ACCESS_OUTPUT_AND_PREVIEW_GUARDS_UNCHANGED')
        r.audit.inverse(original_common(q.text(COMMON)),old[COMMON],'ORIGINAL_COMMON_RECEIPT_ALGORITHM_DELEGATES_IDENTICAL_BODY')
        text=q.text(TEST);new={PREFIX+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}
        c.require(len(new)==40 and '#[ignore]'not in text and text.count('#[cfg(all(windows,feature="p09-installed-format-fixture"))]')==1,'EXACT39_SYNTHETIC_AND_ONE_EXPLICIT_INSTALLED_TEST')
        expected_cases=new|AFFECTED;c.require(len(expected_cases)==43,'EXACT_NEW40_AND_AFFECTED3_NO_UNAFFECTED_REPLAY')
        image=a.AcceptanceReader(CONFIG.parent,guard.check);pin=image.pin(CONFIG.name)
        c.require((pin['bytes'],pin['sha256'])==(17020,'fe3721e68a749c3d1ec843207d475249fa75e68f1de569fe45468c05b1022434'),'EXACT_ORIGINAL_FIXED_INSTALLED_CATALOG_NOT_PRIVATE_CONFIG')
        scratch=c.ROOT/'target/p09-catalog-mask-product-scratch-431';c.require(not scratch.exists()and scratch.parent.is_dir()
            and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'CATALOG_MASK_PRODUCT431_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='CATALOG_MASK_PRODUCT431_PREFLIGHT',inputs=len(q.snapshots),new=40,affected=3,declared_test_inputs=len(expected))),flush=True)
        args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','personal_info_mask_product','--features','p09-installed-format-fixture','--message-format=short','--',*sorted(expected_cases),'--test-threads=1']
        r.harness.run_one('strict_catalog_mask_products_and_real_common_compiler43',args,expected_cases,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],expected_cases);c.require(not row['steps'][-1]['diagnostics'],'CATALOG_MASK_PRODUCT43_NO_WARNINGS')
        row['actual_compiled_test_inputs']=prior.compiled_inputs(prior.CONFIGS[1],expected,guard)
        c.require(not any(scratch.iterdir()),'CATALOG_MASK_PRODUCT431_COMPILER_TEMP_EMPTY')
        final_attempted=True;image.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_PERSONAL_INFO_CATALOG_MASK_PRODUCT40_AFFECTED3_NOT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            installed_config_final_fresh_hashes=image.final_fresh_hashes,new_product_cases=40,affected_product_cases=3)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'CATALOG_MASK_PRODUCT_FAILURE_NO_RAW_VALUES')
        if q is not None and not final_attempted:
            final_attempted=True
            try:
                if image is not None:image.finish();row['installed_config_final_fresh_hashes']=image.final_fresh_hashes
                q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),installed_config_pins=[]if image is None else list(image.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','cleanup')},'cases':len(s.get('tests',[])),
                'compiler_codes':s.get('bounded_output_observation',{}).get('rust_error_codes',[]),'compiler_locations':s.get('bounded_output_observation',{}).get('short_error_locations',[]),
                'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
