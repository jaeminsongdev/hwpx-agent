"""Whole original protection signals once, actual sixteen-family manifest denial, original local guards."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_source_search_manifest_components as prior
base=prior.base
harness,shared,c,a,audit,tools=base.harness,base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-source-protection-manifest-components222.v1.json'
DRIVER='tools/p09/run_source_protection_manifest_components.py'
BASELINE='implementation/p09/evidence/p09-361-source-search-manifest-preflight-recovery219.v1.json'
DOC_BASE='implementation/p09/evidence/p09-361-source-search-manifest-sync-recovery221.v1.json'
SOURCE_ROOT='crates/hwpx-package/src/document_import.rs'
SOURCE=SOURCE_ROOT[:-3]+'/protection.rs'
NATIVE='crates/hwpx-package/src/native_form_package.rs'
CORE='crates/hwpx-package/tests/source_protection_signals.rs'
FIXTURE='crates/hwpx-package/tests/support/source_protection_fixture.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/source_protection_manifest.rs'
NEW={SOURCE,CORE,FIXTURE,TEST,DRIVER}
CHANGED={SOURCE_ROOT,NATIVE,prior.ROUTING,prior.TEST}
DOCS={'protocol/migrations/p09-source-search-execution-manifest-v1.md','tools/p09/run_source_search_manifest_sync.py',
    'tools/p09/run_source_search_manifest_sync_recovery.py','tools/p09/run_source_search_manifest_preflight_recovery.py'}
CHILD='#[path="source_protection_manifest.rs"]mod protection_v1;\n'
REVERSE=[
('use hwpx_package::document_import::protection::{SourceProtectionObservation,SourceProtectionObservationError};\n',''),
('    source_protection:SourceProtectionObservation,\n',''),
('''        let((routes,manifest,target_profile_sha256),source_protection)=self.with_verified_bytes(provider,now,|_|{
            let source_protection=self.candidate.compiler_view().source.imported().source().observe_protection_signals()?;
            let value=make(&self,&source_protection,context,catalog,transaction,now)?;''',
'''        let(routes,manifest,target_profile_sha256)=self.with_verified_bytes(provider,now,|_|{
            let value=make(&self,context,catalog,transaction,now)?;'''),
('Ok::<_,SearchManifestError>((value,source_protection))','Ok::<_,SearchManifestError>(value)'),
('target_profile_sha256,routes,source_protection})','target_profile_sha256,routes})'),
('    #[must_use] pub const fn source_protection_observation(&self)->&SourceProtectionObservation{&self.source_protection}\n',''),
('make(&self.compiled,&self.source_protection,context,catalog,self.manifest.transaction_id().clone(),now)?',
 'make(&self.compiled,context,catalog,self.manifest.transaction_id().clone(),now)?'),
('fn make(compiled:&PreparedCompiledSearchMutation,protection:&SourceProtectionObservation,context:',
 'fn make(compiled:&PreparedCompiledSearchMutation,context:'),
('''    protection.verify_binding(compiled.candidate.compiler_view().source.imported().source())?;
    protection.require_no_observed_document_signals()?;
''',''),
('    #[error("search_manifest_original_source_protection_rejected")] SourceProtection(#[from]SourceProtectionObservationError),\n','')]


def inventory(check):return prior.inventory(check)|NEW|DOCS


def expected(q):
    core=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(CORE))
    product=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST))
    c.require(len(core)==len(set(core))==10 and len(product)==len(set(product))==8,'EXACT10_SOURCE_AND8_PRODUCT_PROTECTION_CASES')
    return set(core),{prior.PREFIX+'protection_v1::'+n for n in product},prior.expected(q)


def inverse(q,old):
    text=q.text(SOURCE_ROOT);c.require(text.count('pub mod protection;\n')==1,'ONE_NEW_SEALED_SOURCE_OBSERVATION_CHILD')
    audit.inverse(text.replace('pub mod protection;\n',''),old[SOURCE_ROOT],'ENTIRE_ORIGINAL_WHOLE_PACKAGE_IMPORT_PRESERVATION_BOUNDS_AND_SOURCE_BODY_UNCHANGED')
    text=q.text(NATIVE);c.require(text.count('pub(crate) fn sensitive(name: &str) -> bool {')==1,'ONE_CRATE_READONLY_VISIBILITY_CHANGE')
    audit.inverse(text.replace('pub(crate) fn sensitive(name: &str) -> bool {','fn sensitive(name: &str) -> bool {'),old[NATIVE],
        'ENTIRE_ORIGINAL_NATIVE_FORM_SECURITY_PREDICATE_SCOPES_AND_ALGORITHMS_UNCHANGED')
    text=q.text(prior.ROUTING)
    for new,previous in REVERSE:
        c.require(text.count(new)==1,'ONE_DECLARED_SOURCE_PROTECTION_ADDITION_TO_EXISTING_MANIFEST_PATH');text=text.replace(new,previous)
    audit.inverse(text,old[prior.ROUTING],'ALL_ORIGINAL_CURRENT_ROUTER_CLOCK_BACKEND_TARGET_MANIFEST_FINAL_HEAD_AND_ROUTE_DENIAL_BODIES_PRESERVED')
    text=q.text(prior.TEST);c.require(text.count(CHILD)==1 and text.endswith(CHILD),'ONE_APPENDED_PROTECTION_PRODUCT_CHILD')
    audit.inverse(text.replace(CHILD,''),old[prior.TEST],'ALL26_AFFECTED_MANIFEST_REQUIREMENTS_AND_FIXTURES_UNCHANGED')
    source=q.text(SOURCE);routing=q.text(prior.ROUTING)
    for marker in('super::structure::caption_text_batch::observed_protection(xml)','crate::native_form_package::sensitive(node.name().local_name())',
        'counts.xml_elements!=self.receipt().xml_elements','native_protection_verified:false,cryptographic_signature_verified:false,execution_authority:false',
        'self.counts.document_signal_parts!=0','&self.document_id!=source.document_id()'):
        c.require(source.count(marker)==1,'ORIGINAL_GUARDS_WHOLE_ADMITTED_INVENTORY_BINDING_AND_UNKNOWN_SECURITY_NOT_NATIVE_ATTESTATION')
    c.require(routing.count('observe_protection_signals()?')==1 and routing.count('protection.verify_binding(')==1
        and routing.count('protection.require_no_observed_document_signals()?')==1,'ONE_PREPARE_SCAN_ONLY_CURRENT_MANIFEST_BINDING_NOT_PER_VERIFY_RESCAN')
    uncommented=re.sub(r'//[^\n]*','',source+routing)
    c.require(all(marker not in uncommented for marker in('ProtectionState::Unprotected','RegistryTrustState::SignatureVerified',
        'SupportState::Verified','ImportedSourcePackage::import','BoundedZipReader::open','commit_success(','WorkspaceTransaction::create')),
        'NO_FABRICATED_UNPROTECTED_OR_TRUST_NO_ZIP_REIMPORT_NATIVE_OR_COMMIT')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SOURCE_PROTECTION_MANIFEST_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SOURCE_PROTECTION_MANIFEST_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        native_protection_or_crypto_signature_attested=False,trusted_registry_or_native_evidence=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(BASELINE);docs=q.json(DOC_BASE)
        c.require(q.snapshots[BASELINE]['sha256']=='ba76f88e3bfc69d4775eca4aed7283bb818ff11e47686054cf8b5eaf9f2fa34a'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==756 and passed['total_executed_cases']==26,
            'EXACT219_ORIGINAL26_MANIFEST_AND_CURRENT_SOURCE_CLOSURE')
        c.require(q.snapshots[DOC_BASE]['sha256']=='d5e30db6d32b0b9b7aedf53a324e54df73312c1d49bdfae2be691551d62e32c7'
            and docs['cleanup']and docs['fresh_inputs']==docs['final_fresh_hashes']==63,'EXACT221_CURRENT_MANIFEST_DOCS_AND_HISTORY')
        old={p['path']:p for p in passed['source_pins']};documented={p['path']:p for p in docs['source_pins']};names=inventory(guard.check)
        for name in sorted(names):
            q.pin(name)
            if name not in NEW|CHANGED:
                pin=documented.get(name,old.get(name));c.require(pin is not None and q.snapshots[name]==pin,'ALL_OTHER_SOURCE_COMPILERS_PROTECTIONS_PRODUCTS_TESTS_FIXTURES_AND_DOCS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        inverse(q,old);core,product,affected=expected(q)
        print(json.dumps(dict(state='SOURCE_PROTECTION_MANIFEST_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),source_cases=len(core),new_product_cases=len(product),
            affected_manifest_cases=len(affected),earlier_compiler36_and_official249_reexecuted=False)),flush=True)
        harness.run_one('ten_whole_admitted_source_protection_observations',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','source_protection_signals','--message-format=short','--','--test-threads=1'],core,guard,audit.environment(),row,observe_capture=base.snapshot)
        tools.good_step(row['steps'][-1],core)
        harness.run_one('eight_new_protection_products_and_twentysix_affected_manifests',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',prior.PREFIX,'--test-threads=1'],product|affected,guard,audit.environment(),row,observe_capture=base.snapshot)
        tools.good_step(row['steps'][-1],product|affected);q.finish();guard.check(force=True)
        row.update(state='PASS_WHOLE_SOURCE_PROTECTION10_PRODUCT8_AFFECTED_MANIFEST26_NOT_NATIVE_PROTECTION_CRYPTO_TRUST_TRANSACTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_source_cases=10,new_product_cases=8,affected_manifest_cases=26,total_executed_cases=44,
            source_observation_once_no_verify_rescan_reimport_or_unprotected_inference=True,
            original_native_signal_predicate_and_local_lock_algorithms_unchanged=True,
            next_work='qualified_native_protection_and_trusted_current_registry_target_then_durable_ingest_commit_CAS_idempotency_and_remaining_P09_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SOURCE_PROTECTION_MANIFEST_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SOURCE_PROTECTION_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes','closed_nested_error_variants','closed_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
