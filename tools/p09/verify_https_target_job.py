"""536: mandatory guard job preparation, original coordinator registration/CAS model and real pinned-policy denial; eight cases."""
import json,re,subprocess,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_character_detail_search as helpers
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import search_sql_receipt as layout
SELF='tools/p09/verify_https_target_job.py'
OUTPUT='implementation/p09/evidence/p09-361-https-target-job536.v1.json'
BASE='implementation/p09/evidence/p09-361-https-target-storage535.v1.json'
PRODUCT='crates/product-cli/src/form_product_request/stored_operations/https_targets.rs'
ROUTING=PRODUCT[:-3]+'/routing.rs'
JOB=ROUTING[:-3]+'/job.rs'
ADMISSION=PRODUCT[:-3]+'/admission.rs'
HOST='crates/product-cli/tests/stored_https_target_product.rs'
STORAGE_TEST='crates/product-cli/tests/support/stored_https_storage.rs'
TEST='crates/product-cli/tests/support/stored_https_coordinator.rs'
ARCHIVE='implementation/p09/source-archive/p361-https-job536/'
CHANGED={PRODUCT:'product.rs',ROUTING:'routing.rs',HOST:'test.rs',STORAGE_TEST:'storage-tests.rs'}
PINNED={'implementation/p02/evidence/signing-runs/7b63d0ede07ea116e64d084fa00015a0fefb4ec3/signed-registry.json',
    'implementation/p02/trust/p02-current-pc-local-trust-policy.json','implementation/p02/trust/p02-current-pc-local-ed25519-public.pem'}

def inverse(q):
    r.audit.inverse(q.text(PRODUCT).replace('pub mod admission;\n',''),q.snapshots[ARCHIVE+'product.rs'],'HTTPS536_ALL_ORIGINAL_REQUEST_LOOKUP_PRODUCT_GUARDS_UNCHANGED')
    r.audit.inverse(q.text(ROUTING).replace('pub mod job;\n',''),q.snapshots[ARCHIVE+'routing.rs'],'HTTPS536_ALL_ORIGINAL_SOURCE_POLICY_ROUTING_STORAGE_AND_LATCHING_GUARDS_UNCHANGED')
    r.audit.inverse(q.text(HOST).replace('#[path="support/stored_https_coordinator.rs"]mod coordinator;\n',''),q.snapshots[ARCHIVE+'test.rs'],'HTTPS536_ALL_ORIGINAL_HOST_TEST_BODIES_UNCHANGED')
    r.audit.inverse(q.text(STORAGE_TEST).replace('pub(super) fn routing','fn routing'),q.snapshots[ARCHIVE+'storage-tests.rs'],'HTTPS536_ENTIRE_ORIGINAL_STORAGE_EIGHT_CASES_AND_FIXTURES_UNCHANGED')

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'HTTPS536_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    start=time.monotonic();q=artifact=None
    row=dict(state='FAILED_HTTPS_TARGET_GUARDED_JOB',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_SQL_Native_or_network_started=False,official249_SQL520_or_previous_Native_replayed=False,external003_cleanup_or_claim_changed=False,
        operating_registry_release_policy_or_keys_changed=False,operating_sql_claim_worker_registration_policy_issuer_native_or_product_route_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='bae505240893446b051c1dbe7189254e6b0ecd38a4502a0bc52f3c4b2613621f'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==833 and base['current_qualified_cases']==8,'HTTPS536_EXACT535_ACCEPTANCE')
        names=inventory.inventory(guard)|{SELF,BASE,PRODUCT,ROUTING,JOB,ADMISSION,HOST,STORAGE_TEST,TEST,deps.CAPTURE}|{ARCHIVE+v for v in CHANGED.values()}|PINNED
        names|=includes.test_inputs((HOST,),guard)
        for path in sorted(names):q.pin(path)
        for pin in base['source_pins']:
            if not pin['path'].startswith('crates/'):continue
            if '/src/'not in pin['path']and pin['path']not in(HOST,STORAGE_TEST):continue
            actual=q.snapshots[ARCHIVE+CHANGED[pin['path']]]if pin['path']in CHANGED else q.snapshots[pin['path']]
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'HTTPS536_ALL_ORIGINAL_COMMON_COORDINATOR_AND_OTHER_LIBRARY_INPUTS_UNCHANGED')
        inverse(q);cases=helpers.tests(q,TEST,'coordinator::');c.require(len(cases)==8,'HTTPS536_EXACT_EIGHT_NEW_CASES')
        row.update(new_job_and_pinned_admission_cases=8,unchanged_storage_eight_replayed=False,unchanged_request_twenty_two_replayed=False)
        guard.check(force=True);scratch=c.ROOT/'target/p09-https-job-scratch536';c.require(not scratch.exists(),'HTTPS536_FRESH_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='HTTPS_JOB_PREFLIGHT',inputs=len(q.snapshots),current_cases=len(cases),prior_storage_and_requests_replayed=False,CPU_cap_percent=6.25)),flush=True)
        args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','stored_https_target_product','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
        r.harness.run_one('https_target_guarded_job',args,cases,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'HTTPS536_NO_COMPILER_WARNINGS')
        found=[]
        for path in(c.ROOT/'target/debug/deps').glob('stored_https_target_product-*.d'):
            declared=deps.dependencies(path);c.require(declared<=set(q.snapshots),'HTTPS536_ALL_ACTUAL_COMPILER_DEPENDENCIES_PREPINNED')
            found.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_count=len(declared),all_predeclared=True))
        c.require(len(found)==1,'HTTPS536_ONE_HOST_DEP_INFO');row['actual_compile_inputs']=found
        c.require(not any(scratch.iterdir()),'HTTPS536_COMPILER_TEMP_EMPTY');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_HTTPS_TARGET_GUARDED_COORDINATOR_AND_REAL_PINNED_DENIAL_EIGHT_NOT_SQL_WORKER_ROUTE_NATIVE_OR_GATE',current_qualified_cases=len(cases),
            actual_original_coordinator_registered_receipts_aead_and_in_memory_cas=True,actual_pinned_signature_verified_and_routing_denied_before_source=True,
            compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'HTTPS536_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),resource_samples=samples,
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),diagnostics=s.get('diagnostics',[]),cleanup=s['cleanup'],failed_cases=[n for n,status in s.get('tests',[])if status!='ok'])for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
