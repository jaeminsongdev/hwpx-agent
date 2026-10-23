"""533: strict public HTTPS requests, original scoped lookup/owned transfer, new8+affected10; no old queue/Native."""
import json,re,subprocess,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_character_detail_search as helpers
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import search_sql_receipt as layout
SELF='tools/p09/verify_https_target_request.py'
OUTPUT='implementation/p09/evidence/p09-361-https-target-request533.v1.json'
BASE='implementation/p09/evidence/p09-361-https-target-compiler532.v1.json'
STORED='crates/product-cli/src/form_stored_provider/actual_import/https_target_output.rs'
OWNED=STORED[:-3]+'/owned.rs'
OPERATIONS='crates/product-cli/src/form_product_request/stored_operations.rs'
CLASSIFY=OPERATIONS[:-3]+'/request.rs'
PRODUCT=OPERATIONS[:-3]+'/https_targets.rs'
HOST='crates/product-cli/tests/stored_https_target_product.rs'
COMPILER_TEST='crates/product-cli/tests/support/stored_https_compiler.rs'
TEST='crates/product-cli/tests/support/stored_https_request.rs'
ARCHIVE='implementation/p09/source-archive/p361-https-request533/'
CHANGED={STORED:'stored.rs',OPERATIONS:'operations.rs',CLASSIFY:'request.rs',HOST:'test.rs'}
AFFECTED={'captured_source_actual_encrypted_policy_and_output_readback_do_not_publish',
    'stored_batch_preserves_unselected_field_and_rejects_one_unapproved_member_atomically',
    'candidate_delivery_rechecks_both_acls_repository_revocation_scope_and_latest_version',
    'policy_revocation_during_preparation_or_final_delivery_never_exposes_bytes',
    'changed_stored_head_denies_delivery_and_does_not_replace_newer_revision'}

def inverse(q):
    text=q.text(STORED).replace('mod owned;\nuse owned::HttpsSource;\n','')
    text=text.replace("source:HttpsSource<'a>","source:&'a StoredImportedDocumentForms").replace('source:HttpsSource::Borrowed(self)','source:self')
    text=text.replace('scope(&self.source)','scope(self.source)').replace('policy(&self.source,','policy(self.source,')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'stored.rs'],'HTTPS533_ORIGINAL_STORED_POLICY_LOWERER_GUARDS_AND_CONSUMER_CHECKS_UNCHANGED')
    text=q.text(OPERATIONS).replace('pub mod https_targets;\n','').replace('            request::Kind::HttpsTargets => Err(StoredProductOperationError::PolicyRepositoryRequired),\n','')
    text=text.replace('    #[error("product_operation_https_current_policy_repository_required")]\n    PolicyRepositoryRequired,\n','')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'operations.rs'],'HTTPS533_ORIGINAL_ALL_LEGACY_PRODUCT_DISPATCH_AND_ROUTE_DENIALS_UNCHANGED')
    text=q.text(CLASSIFY).replace('    HttpsTargets,\n','').replace('''        super::https_targets::HTTPS_TARGET_PRODUCT_REQUEST_SCHEMA=>{
            super::https_targets::validate_request(raw).map_err(|_|RequestError::Request)?;
            Ok(Kind::HttpsTargets)
        }
''','')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'request.rs'],'HTTPS533_ORIGINAL_ALL_LEGACY_CLASSIFICATION_AND_DUPLICATE_GUARDS_UNCHANGED')
    r.audit.inverse(q.text(HOST).replace('#[path="support/stored_https_request.rs"]mod requests;\n',''),q.snapshots[ARCHIVE+'test.rs'],
        'HTTPS533_ORIGINAL_NINE_TEST_BODIES_AND_FIXTURES_UNCHANGED')

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'HTTPS533_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    start=time.monotonic();q=artifact=None
    row=dict(state='FAILED_HTTPS_TARGET_PUBLIC_REQUEST',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_SQL_Native_or_network_started=False,official249_SQL520_or_previous_Native_replayed=False,external003_cleanup_or_claim_changed=False,
        operating_policy_issuer_registry_manifest_durable_claim_job_CAS_route_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='97fbb3599951c000118ad58f434393b11bfc20ccd95a59af6026a370809aef37'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==831 and base['distinct_qualified_cases']==14,'HTTPS533_EXACT532_ACCEPTANCE')
        names=inventory.inventory(guard)|{SELF,BASE,STORED,OWNED,OPERATIONS,CLASSIFY,PRODUCT,HOST,TEST,COMPILER_TEST,deps.CAPTURE}|{ARCHIVE+v for v in CHANGED.values()}
        names|=includes.test_inputs((HOST,),guard)
        for path in sorted(names):q.pin(path)
        for pin in base['source_pins']:
            if not pin['path'].startswith('crates/'):continue
            if '/src/'not in pin['path']and pin['path']not in(HOST,COMPILER_TEST):continue
            actual=q.snapshots[ARCHIVE+CHANGED[pin['path']]]if pin['path']in CHANGED else q.snapshots[pin['path']]
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'HTTPS533_ALL_UNRELATED_PRODUCT_SOURCE_AND_COMPILER_TESTS_UNCHANGED')
        inverse(q)
        old=helpers.tests(q,HOST);compiled=helpers.tests(q,COMPILER_TEST,'compiled::');new=helpers.tests(q,TEST,'requests::');retained=old-AFFECTED
        c.require((len(old),len(compiled),len(new),len(retained))==(9,5,8,4),'HTTPS533_NEW_EIGHT_AFFECTED_TEN_RETAINED_FOUR')
        row.update(retained_early_denial_cases=4,retained_case_names=sorted(retained),unchanged_early_denial_four_replayed=False,new_request_cases=8,
            affected_source_ownership_cases=10,prior_positive_cases_replayed_because_source_ownership_representation_changed=True)
        cases=AFFECTED|compiled|new;guard.check(force=True);scratch=c.ROOT/'target/p09-https-request-scratch533'
        c.require(not scratch.exists(),'HTTPS533_FRESH_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='HTTPS_REQUEST_PREFLIGHT',inputs=len(q.snapshots),current_cases=len(cases),retained_early_denial=4,CPU_cap_percent=6.25)),flush=True)
        args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','stored_https_target_product','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
        r.harness.run_one('https_target_public_request',args,cases,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'HTTPS533_NO_COMPILER_WARNINGS')
        found=[]
        for path in(c.ROOT/'target/debug/deps').glob('stored_https_target_product-*.d'):
            declared=deps.dependencies(path);c.require(declared<=set(q.snapshots),'HTTPS533_ALL_ACTUAL_COMPILER_DEPENDENCIES_PREPINNED')
            found.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_count=len(declared),all_predeclared=True))
        c.require(len(found)==1,'HTTPS533_ONE_HOST_DEP_INFO');row['actual_compile_inputs']=found
        c.require(not any(scratch.iterdir()),'HTTPS533_COMPILER_TEMP_EMPTY');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_HTTPS_TARGET_PUBLIC_REQUEST_CURRENT_EIGHTEEN_RETAINED_FOUR_NOT_CLAIM_ROUTE_NATIVE_OR_GATE',current_qualified_cases=len(cases),distinct_qualified_cases=len(old|compiled|new),
            actual_strict_request_common_scoped_lookup_owned_source_and_compiler=True,source_or_head_published_by_candidate=False,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'HTTPS533_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),resource_samples=samples,
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),diagnostics=s.get('diagnostics',[]),cleanup=s['cleanup'],failed_cases=[n for n,status in s.get('tests',[])if status!='ok'])for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
