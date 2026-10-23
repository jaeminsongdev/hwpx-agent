"""Bounded common HTTPS dispatch qualification: new7 + affected legacy1, no Native/SQL/replay."""
import json,re,subprocess,sys,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_character_detail_search as helpers
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import search_sql_receipt as layout
SELF='tools/p09/verify_https_dispatch561.py'
OUTPUT='implementation/p09/evidence/p09-361-https-common-dispatch561.v1.json'
BASE='implementation/p09/evidence/p09-361-https-atomic-sql543.v1.json'
OPERATIONS='crates/product-cli/src/form_product_request/stored_operations.rs'
PRODUCT=OPERATIONS[:-3]+'/https_targets.rs'
DISPATCH=PRODUCT[:-3]+'/dispatch.rs'
HOST='crates/product-cli/tests/stored_https_target_product.rs'
TEST='crates/product-cli/tests/support/stored_https_dispatch.rs'
REQUEST_TEST='crates/product-cli/tests/support/stored_https_request.rs'
ARCHIVE='implementation/p09/source-archive/p361-https-dispatch561/'
CHANGED={OPERATIONS:'operations-before.rs',PRODUCT:'https-before.rs',HOST:'host-before.rs'}
HELPER='''        Self::prepare_classified(provider,raw,bindings,limits,now,request::classify(raw)?)
    }
    fn prepare_classified<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],bindings:Option<&StoredProductFormBindings<'_>>,
        limits:search_mutations::SearchMutationLimits,now:u64,kind:request::Kind)->Result<PreparedStoredProductOperation,StoredProductOperationError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        match kind {'''

def inverse(q):
    text=q.text(OPERATIONS)
    text=text.replace('    HttpsTargets(Box<https_targets::PreparedHttpsTargetProduct>),\n','')
    text=text.replace('            Self::HttpsTargets(_) => Err(StoredProductOperationError::PolicyRepositoryRequired),\n','')
    text=text.replace('    #[error("product_operation_https_targets_rejected")]\n    HttpsTargets(#[from]https_targets::HttpsTargetProductError),\n','')
    r.c.require(text.count(HELPER)==1,'HTTPS561_ONE_CLASSIFIED_DISPATCH_EXTRACTION')
    r.audit.inverse(text.replace(HELPER,'        match request::classify(raw)? {'),q.snapshots[ARCHIVE+CHANGED[OPERATIONS]],'HTTPS561_ENTIRE_OLD_CLASSIFIER_DISPATCH_BYTES_PREVIEW_AND_ROUTE_DENIALS_PRESERVED')
    r.audit.inverse(q.text(PRODUCT).replace('pub mod dispatch;\n',''),q.snapshots[ARCHIVE+CHANGED[PRODUCT]],'HTTPS561_ENTIRE_ORIGINAL_STRICT_HTTPS_SCOPE_OWNERSHIP_PLAN_POLICY_AND_REPOSITORY_CHECKS_PRESERVED')
    r.audit.inverse(q.text(HOST).replace('#[path="support/stored_https_dispatch.rs"]mod dispatch;\n',''),q.snapshots[ARCHIVE+CHANGED[HOST]],'HTTPS561_ALL_PREVIOUS_TEST_AND_FIXTURE_BODIES_PRESERVED')

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--new-and-affected-only'],'HTTPS561_NO_NATIVE_OR_SQL_MODE')
    c.require(not(c.ROOT/OUTPUT).exists(),'HTTPS561_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_HTTPS_COMMON_POLICY_DISPATCH',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_SQL_Native_or_network_started=False,official249_or_previous_SQL_or_Native_replayed=False,
        new_native_execution_authorized=False,operating_registry_worker_route_publication_or_long_term_custody_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='66854516e9f612e46f2ee55e97e289dd47673195c9f7bdb7af46308640bef8f7'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==881,'HTTPS561_EXACT543_ATOMIC_CAS_BASELINE_NOT_REPLAY')
        names=inventory.inventory(guard)|{SELF,BASE,OPERATIONS,PRODUCT,DISPATCH,HOST,TEST,REQUEST_TEST,deps.CAPTURE}|{ARCHIVE+v for v in CHANGED.values()}
        names|=includes.test_inputs((HOST,),guard)
        for path in sorted(names):q.pin(path)
        for pin in base['source_pins']:
            path=pin['path']
            if not path.startswith('crates/')or('/src/'not in path and path not in(HOST,REQUEST_TEST)):continue
            actual=q.snapshots[ARCHIVE+CHANGED[path]]if path in CHANGED else q.snapshots[path]
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'HTTPS561_UNRELATED_PRIOR_PRODUCT_AND_STORAGE_SOURCE_IDENTICAL')
        inverse(q);cases=helpers.tests(q,TEST,'dispatch::')
        c.require(len(cases)==7,'HTTPS561_NEW_SEVEN_COMMON_DISPATCH_CASES')
        affected={'requests::not_observed_prepares_owned_product_once_and_legacy_dispatchers_cannot_bypass_policy_repository'}
        c.require(affected<=helpers.tests(q,REQUEST_TEST,'requests::'),'HTTPS561_EXACT_ONE_LEGACY_DISPATCH_REGRESSION')
        cases|=affected;guard.check(force=True)
        scratch=c.ROOT/'target/p09-https-common-dispatch-scratch561';c.require(not scratch.exists(),'HTTPS561_UNIQUE_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='HTTPS_COMMON_DISPATCH_PREFLIGHT',inputs=len(q.snapshots),new_cases=7,affected_cases=1,CPU_cap_percent=6.25)),flush=True)
        args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','stored_https_target_product','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
        r.harness.run_one('https_common_policy_dispatch',args,cases,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'HTTPS561_NO_COMPILER_WARNINGS')
        found=[]
        for path in(c.ROOT/'target/debug/deps').glob('stored_https_target_product-*.d'):
            declared=deps.dependencies(path);c.require(declared<=set(q.snapshots),'HTTPS561_ALL_ACTUAL_COMPILER_DEPENDENCIES_PREPINNED')
            found.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_count=len(declared),all_predeclared=True))
        c.require(len(found)==1,'HTTPS561_ONE_HOST_DEP_INFO');row['actual_compile_inputs']=found
        c.require(not any(scratch.iterdir()),'HTTPS561_COMPILER_TEMP_EMPTY');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_COMMON_HTTPS_POLICY_DISPATCH_SEVEN_AND_LEGACY_ONE_NOT_EXECUTION_ROUTE_OR_GATE',current_qualified_cases=8,new_cases=7,affected_legacy_cases=1,
            original_dispatch_source_and_route_checks_preserved=True,actual_stored_source_policy_writer_and_consumer_checks=True,
            old_policyless_api_still_denied=True,route_unqualified_preserved=True,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'HTTPS561_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),resource_samples=samples,
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),cleanup=s['cleanup'],diagnostics=s.get('diagnostics',[]),failed_cases=[n for n,status in s.get('tests',[])if status!='ok'])for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
