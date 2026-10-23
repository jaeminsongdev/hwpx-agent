"""319: exact header/body font effects12 + affected source9/product24, no Native/queue replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_stored_font_recovery as previous
import run_sql23_storage as closure
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-font-edit-inventory319.v1.json';DRIVER='tools/p09/run_font_inventory_components.py'
base=previous.previous;CORE=base.CORE;CATALOG=base.previous.base.CATALOG;INVENTORY=CORE[:-3]+'/inventory.rs'
TEST='crates/product-cli/tests/support/scoped_font_edit_inventory.rs';NEW={DRIVER,INVENTORY,TEST};CHANGED={CORE,CATALOG,base.STORED,base.REQUEST,base.TEST}
LINK='#[path="support/scoped_font_edit_inventory.rs"]mod edit_inventory_v1;\n'
STORED_METHOD='''    /// # Errors
    /// Metadata delivery shares the original fresh source/integrity/consumer-final head checks.
    pub fn with_verified_edit_inventory<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,
        consume:impl FnOnce(&hwpx_package::document_import::search::replacement::atoms::styles::fonts::inventory::SourceFontEditInventory)->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.with_verified_bytes(provider,now,|_|consume(self.output.edit_inventory()))
    }
'''
PRODUCT_METHOD='''    /// # Errors
    /// Exact header resource effects and body splices, never an unchecked byte/authority path.
    pub fn with_verified_edit_inventory<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,
        consume:impl FnOnce(&hwpx_package::document_import::search::replacement::atoms::styles::fonts::inventory::SourceFontEditInventory)->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;Ok(self.candidate.with_verified_edit_inventory(provider,now,consume)?)
    }
'''
CORE_CASES={'partial_run_clones_shared_property_and_preserves_nonselected_scalars_and_entities','two_paragraphs_share_original_style_but_only_selected_node_changes',
    'explicit_text_style_splits_text_without_changing_run_or_unselected_text_axis','document_and_section_scope_apply_once_and_reuse_one_clone_per_original_style',
    'selected_nfc_scalar_keeps_all_original_hangul_contributors_and_outside_spelling','controls_retain_original_bytes_and_are_not_counted_as_changed_text',
    'finite_scalar_and_writer_limits_never_return_partial_candidates','request_binding_changes_with_language_set_and_names_are_not_disclosed',
    'different_original_properties_get_separate_clones_with_nonfont_effects_preserved'}

def inverse(q,old):
    text=q.text(CORE)
    for marker in ('pub mod inventory;\n','    #[must_use]pub const fn edit_inventory(&self)->&inventory::SourceFontEditInventory{&self.edit_inventory}\n',
        '        let mut edit_inventory=inventory::Builder::new(axis);\n','                edit_inventory.body(part,i,edit)?;\n','        let edit_inventory=edit_inventory.finish(&receipt,intents.len())?;\n'):
        c.require(text.count(marker)==1,'ONE_DECLARED_ADDITIVE_FONT_INVENTORY_OBSERVATION');text=text.replace(marker,'')
    text=text.replace(',edit_inventory:inventory::SourceFontEditInventory','').replace(',edit_inventory})','})').replace('index.limits.0.result_bytes,&mut edit_inventory)?','index.limits.0.result_bytes)?')
    audit.inverse(text,old[CORE],'ALL_ORIGINAL_FONT_MATCH_CLONE_RENDER_PROTECTION_PATCH_WRITER_READBACK_RECEIPT_BODIES_UNCHANGED')
    text=q.text(CATALOG);marker=',inventory:&mut inventory::Builder';c.require(text.count(marker)==1,'ONE_PRIVATE_OBSERVER_ARGUMENT');text=text.replace(marker,'')
    for marker in ('    inventory.count(header,container,count,total-needed.len(),total,&edits[&span.start()])?;\n','    inventory.append(header,last,needed.len(),&edits[&insertion])?;\n'):
        c.require(text.count(marker)==1,'ONE_OBSERVATION_OF_EACH_ACTUAL_HEADER_PATCH');text=text.replace(marker,'')
    audit.inverse(text,old[CATALOG],'ALL_ACTUAL_HEADER_COPY_COUNT_APPEND_AND_PRESERVATION_ALGORITHMS_UNCHANGED')
    for path,marker in ((base.STORED,STORED_METHOD),(base.REQUEST,PRODUCT_METHOD),(base.TEST,LINK)):
        text=q.text(path);c.require(text.count(marker)==1,'ONE_ADDITIVE_FRESH_INVENTORY_CALLBACK_OR_TEST_MODULE')
        audit.inverse(text.replace(marker,''),old[path],'ALL_CURRENT_AUTHORITY_VERIFICATION_DELIVERY_ROUTE_AND_PREVIOUS24_TEST_BODIES_UNCHANGED')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FONT_INVENTORY_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_EDIT_INVENTORY',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,
        common_operation_compiler_or_dispatcher_qualified=False,output_ingest_commit_or_publication=False,full_SEARCH024_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='69244dce380116a69c7429d2a6bdc40e983a33545a151b3c6ce9ccf2e52a7182'and passed['cleanup']and passed['new_cases']==24,'EXACT316_PRODUCT24_SOURCE_BASELINE')
        old={p['path']:p for p in passed['source_pins']};names=closure.inventory(guard.check)|set(old)|NEW|CHANGED
        for n in sorted(names):
            q.pin(n)
            if n in old and n not in CHANGED:c.require(q.snapshots[n]==old[n],'ALL_OTHER_COMPILED_INPUTS_ORIGINAL_POLICIES_MATCHERS_AND_TESTS_UNCHANGED')
            elif n not in old:c.require(n in NEW,'ONLY_DECLARED_INVENTORY_FILES_NEW_TO_CLOSURE')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        source_test=base.previous.base.TEST;all_source=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(source_test)))
        c.require(len(all_source)==20 and len(CORE_CASES)==9 and CORE_CASES<=all_source,'ONLY_AFFECTED_SOURCE_CANDIDATE_OUTPUT_AND_WRITER_CASES')
        legacy=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(base.TEST)));new={'edit_inventory_v1::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST))}
        c.require(len(legacy)==24 and len(new)==12,'EXACT_PREVIOUS24_AND_NEW12_IDENTITIES')
        scratch=c.ROOT/'target/p09-font-inventory-scratch-319';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'FONT_INVENTORY_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));source_cases={'scoped::'+n for n in CORE_CASES}
        print(json.dumps(dict(state='FONT_INVENTORY_PREFLIGHT',inputs=len(q.snapshots),new_inventory_cases=12,affected_source_cases=9,affected_product_cases=24,unrelated_source_cases_retained=11)),flush=True)
        harness.run_one('font_inventory_affected_source9',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','document_import_scoped_fonts',
            '--message-format=short','--',*sorted(source_cases),'--test-threads=1'],source_cases,guard,env,row,observe_capture=base.snapshot)
        tools.good_step(row['steps'][-1],source_cases)
        harness.run_one('font_inventory_new12_and_affected_product24',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','scoped_font_product',
            '--message-format=short','--','--test-threads=1'],legacy|new,guard,env,row,observe_capture=base.snapshot)
        tools.good_step(row['steps'][-1],legacy|new);c.require(not any(scratch.iterdir()),'FONT_INVENTORY_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_FONT_EXACT_HEADER_BODY_INVENTORY_NEW12_AFFECTED_SOURCE9_PRODUCT24_NOT_COMMON_COMPILER_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=12,affected_source_cases=9,affected_product_cases=24,unchanged_source_cases_not_replayed=11,next_work='bind_header_resource_dependencies_and_actual_body_owners_in_common_operation_compiler')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_INVENTORY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'FONT_INVENTORY_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
