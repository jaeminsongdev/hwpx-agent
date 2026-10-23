"""535: shared router/manifest/job/CAS primitives for HTTPS; new6 + directly affected existing-search2, retain requests22."""
import json,re,subprocess,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_character_detail_search as helpers
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import search_sql_receipt as layout
SELF='tools/p09/verify_https_target_storage.py'
OUTPUT='implementation/p09/evidence/p09-361-https-target-storage535.v1.json'
BASE='implementation/p09/evidence/p09-361-https-target-request534.v1.json'
SHARED_ROUTE='crates/product-cli/src/form_product_request/stored_operations/compiled_search/routing.rs'
SHARED_STORAGE=SHARED_ROUTE[:-3]+'/storage.rs'
COMPILER='crates/product-cli/src/form_stored_provider/actual_import/https_target_output/compiled.rs'
PRODUCT='crates/product-cli/src/form_product_request/stored_operations/https_targets.rs'
ROUTE=PRODUCT[:-3]+'/routing.rs'
HOST='crates/product-cli/tests/stored_https_target_product.rs'
REQUEST_TEST='crates/product-cli/tests/support/stored_https_request.rs'
TEST='crates/product-cli/tests/support/stored_https_storage.rs'
ARCHIVE='implementation/p09/source-archive/p361-https-storage535/'
CHANGED={SHARED_ROUTE:'shared-routing.rs',SHARED_STORAGE:'shared-storage.rs',COMPILER:'compiled.rs',PRODUCT:'product.rs',HOST:'test.rs',REQUEST_TEST:'request-tests.rs'}
EXTRACT='''    make_for_source(v.source,plan,receipt.source_package_sha256,protection,context,catalog,transaction,now)
}
pub(crate) fn make_for_source(original:&StoredImportedDocumentForms,plan:&CompiledOperationPlan,source_sha256:[u8;32],
    protection:&SourceProtectionObservation,context:&RouteContext,catalog:&CapabilityRouteCatalog,transaction:TransactionId,now:u64)
    ->Result<(Vec<RouteDecision>,ExecutionManifest,[u8;32]),SearchManifestError>{
'''
FACTORY='''                let prepared=PreparedSearchStorage::bind_verified(source,output,&self.manifest,v.document,(project,branch,head),receipt,identity,
                    (&r.canonical_request_sha256,&r.scoped_request_sha256))?;
                Ok(consume(prepared))'''
ORIGINAL='''                Ok(consume(PreparedSearchStorage {source,output,manifest:&self.manifest,document:v.document,project,branch,head,receipt,identity,
                    canonical:&r.canonical_request_sha256,scoped:&r.scoped_request_sha256}))'''
def inverse(q):
    text=q.text(SHARED_ROUTE);r.c.require(text.count(EXTRACT)==1,'HTTPS535_ONE_SHARED_ROUTER_EXTRACTION')
    text=text.replace(EXTRACT,'').replace('protection.verify_binding(original.imported().source())','protection.verify_binding(v.source.imported().source())')
    text=text.replace('let source=original.receipt();','let source=v.source.receipt();').replace('transaction,artifact,source_sha256,source_size','transaction,artifact,receipt.source_package_sha256,source_size')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'shared-routing.rs'],'HTTPS535_ENTIRE_ORIGINAL_TIME_PROTECTION_ROUTER_MANIFEST_BODY_UNCHANGED')
    text=q.text(SHARED_STORAGE);start=text.index("impl<'a> PreparedSearchStorage<'a>{");end=text.index('/// One actual staged-byte import.',start)
    text=(text[:start]+text[end:]).replace(FACTORY,ORIGINAL)
    r.audit.inverse(text,q.snapshots[ARCHIVE+'shared-storage.rs'],'HTTPS535_ALL_ORIGINAL_SOURCE_HASH_VALIDATOR_IDENTITY_JOB_CAS_AND_GUARD_LOGIC_UNCHANGED')
    r.audit.inverse(q.text(COMPILER).replace('    pub(crate) fn source(&self)->&StoredImportedDocumentForms{&self.candidate.source}\n',''),q.snapshots[ARCHIVE+'compiled.rs'],
        'HTTPS535_ORIGINAL_HTTPS_COMPILER_AND_ALL_FRESH_POLICY_CHECKS_UNCHANGED')
    r.audit.inverse(q.text(PRODUCT).replace('pub mod routing;\n',''),q.snapshots[ARCHIVE+'product.rs'],'HTTPS535_ALL_ORIGINAL_PUBLIC_REQUEST_LOOKUP_AND_DELIVERY_BODIES_UNCHANGED')
    r.audit.inverse(q.text(HOST).replace('#[path="support/stored_https_storage.rs"]mod storage;\n',''),q.snapshots[ARCHIVE+'test.rs'],'HTTPS535_ALL_ORIGINAL_HOST_TEST_BODIES_UNCHANGED')
    text=q.text(REQUEST_TEST)
    for name in('budget','raw','allowed'):text=text.replace('pub(super) fn '+name,'fn '+name)
    r.audit.inverse(text,q.snapshots[ARCHIVE+'request-tests.rs'],'HTTPS535_ENTIRE_ORIGINAL_REQUEST_FIXTURE_AND_EIGHT_TEST_BODIES_UNCHANGED')

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'HTTPS535_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    start=time.monotonic();q=artifact=None
    row=dict(state='FAILED_HTTPS_TARGET_SHARED_STORAGE',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_SQL_Native_or_network_started=False,official249_SQL520_or_previous_Native_replayed=False,external003_cleanup_or_claim_changed=False,
        operating_policy_issuer_attested_registry_registration_durable_claim_or_product_route_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='dda75e446e0d1f5ba8f902c8da6d94edcfc9f02cda5b86877b2f3a514d24550b'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==834 and base['distinct_qualified_cases']==22,'HTTPS535_EXACT534_ACCEPTANCE')
        names=inventory.inventory(guard)|{SELF,BASE,SHARED_ROUTE,SHARED_STORAGE,COMPILER,PRODUCT,ROUTE,HOST,REQUEST_TEST,TEST,deps.CAPTURE}|{ARCHIVE+v for v in CHANGED.values()}
        names|=includes.test_inputs((HOST,),guard)
        for path in sorted(names):q.pin(path)
        for pin in base['source_pins']:
            if not pin['path'].startswith('crates/'):continue
            if '/src/'not in pin['path']and pin['path']not in(HOST,REQUEST_TEST):continue
            actual=q.snapshots[ARCHIVE+CHANGED[pin['path']]]if pin['path']in CHANGED else q.snapshots[pin['path']]
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'HTTPS535_ALL_PRIOR_SOURCE_INPUTS_UNCHANGED_OR_ARCHIVED')
        inverse(q);cases=helpers.tests(q,TEST,'storage::');c.require(len(cases)==8,'HTTPS535_EXACT_NEW_HTTPS_SIX_AFFECTED_SHARED_SEARCH_TWO')
        row.update(new_https_storage_cases=6,affected_existing_search_cases=2,unchanged_prior_request_cases_retained=22,prior_request_twenty_two_replayed=False)
        guard.check(force=True);scratch=c.ROOT/'target/p09-https-storage-scratch535';c.require(not scratch.exists(),'HTTPS535_FRESH_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='HTTPS_STORAGE_PREFLIGHT',inputs=len(q.snapshots),current_cases=len(cases),retained_requests=22,CPU_cap_percent=6.25)),flush=True)
        args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','stored_https_target_product','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
        r.harness.run_one('https_target_shared_storage',args,cases,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'HTTPS535_NO_COMPILER_WARNINGS')
        found=[]
        for path in(c.ROOT/'target/debug/deps').glob('stored_https_target_product-*.d'):
            declared=deps.dependencies(path);c.require(declared<=set(q.snapshots),'HTTPS535_ALL_ACTUAL_COMPILER_DEPENDENCIES_PREPINNED')
            found.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_count=len(declared),all_predeclared=True))
        c.require(len(found)==1,'HTTPS535_ONE_HOST_DEP_INFO');row['actual_compile_inputs']=found
        c.require(not any(scratch.iterdir()),'HTTPS535_COMPILER_TEMP_EMPTY');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_HTTPS_TARGET_SHARED_MANIFEST_STORAGE_EIGHT_NOT_REGISTRATION_CLAIM_ROUTE_NATIVE_OR_GATE',current_qualified_cases=len(cases),
            actual_common_manifest_validator_aead_and_in_memory_cas=True,original_current_policy_guard_failure_latches=True,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'HTTPS535_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),resource_samples=samples,
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),diagnostics=s.get('diagnostics',[]),cleanup=s['cleanup'],failed_cases=[n for n,status in s.get('tests',[])if status!='ok'])for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
