"""Correct one outer-envelope fixture; keep561 failure, retain unchanged seven, execute only failed one."""
import json,re,subprocess,sys,time
from types import SimpleNamespace as NS
import verify_https_dispatch561 as previous
r=previous.r
SELF='tools/p09/verify_https_dispatch562.py'
OUTPUT='implementation/p09/evidence/p09-361-https-common-dispatch562.v1.json'
PRIOR=previous.OUTPUT
ARCHIVE='implementation/p09/source-archive/p361-https-dispatch562/'
FAILED={'dispatch::common_legacy_form_dispatch_retains_binding_error_without_https_policy_lookup'}
OLD='''    let request=serde_json::to_vec(&serde_json::json!({"schema_version":hwpx_agent_cli::form_product_request::FORM_PRODUCT_REQUEST_SCHEMA}))?;'''
NEW='''    let mut request=raw(&f,&bytes)?;let fields=request.as_object_mut().ok_or("request object")?;
    fields.remove("operation");fields.insert("schema_version".into(),serde_json::json!(hwpx_agent_cli::form_product_request::FORM_PRODUCT_REQUEST_SCHEMA));
    fields.insert("form_input".into(),serde_json::json!({}));let request=serde_json::to_vec(&request)?;'''

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--corrected-one-only'],'HTTPS562_NO_NATIVE_SQL_OR_REPLAY_MODE')
    c.require(not(c.ROOT/OUTPUT).exists(),'HTTPS562_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_HTTPS_COMMON_DISPATCH_FIXTURE_CLOSURE',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_SQL_Native_or_network_started=False,new_native_execution_authorized=False,
        previous_seven_body_cases_replayed=False,prior561_failure_or_missing_final_fresh_rewritten=False,
        operating_registry_worker_route_publication_or_long_term_custody_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);prior=previous.layout.unpack(q.json(PRIOR))
        c.require(q.snapshots[PRIOR]['sha256']=='b020f5c955281698b22145a6bc8c3cd4ad2ce118307fd4fcb7173fe858498c2d'
            and prior['state']=='FAILED_HTTPS_COMMON_POLICY_DISPATCH'and prior['cleanup']is True
            and prior['fresh_inputs']==848 and prior['final_fresh_hashes']==0,'HTTPS562_KEEP561_FAILURE_AND_MISSING_FINAL_CLOSURE')
        names=previous.inventory.inventory(guard)|{SELF,PRIOR,previous.SELF,previous.TEST,previous.HOST,ARCHIVE+'test561.rs',ARCHIVE+'verifier561.py',ARCHIVE+'observed561.d'}
        names|=previous.includes.test_inputs((previous.HOST,),guard)
        for path in sorted(names):q.pin(path)
        for pin in prior['source_pins']:
            if pin['path']not in q.snapshots:q.pin(pin['path'])
            actual=q.pin(ARCHIVE+'test561.rs')if pin['path']==previous.TEST else q.snapshots[pin['path']]
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'HTTPS562_ALL_PRIOR_INPUTS_UNCHANGED_OR_EXACT_FIXTURE_PREIMAGE')
        old=q.text(ARCHIVE+'test561.rs');c.require(old.count(OLD)==1 and old.replace(OLD,NEW,1)==q.text(previous.TEST),'HTTPS562_ONLY_ONE_OUTER_ENVELOPE_FIXTURE_CHANGED_NO_ASSERTION_OR_PRODUCT_CHANGE')
        previous.inverse(q)
        c.require(q.pin(previous.SELF)['sha256']==q.pin(ARCHIVE+'verifier561.py')['sha256'],'HTTPS562_ORIGINAL_QUALIFIER_PRESERVED')
        c.require(previous.deps.dependencies(c.ROOT/(ARCHIVE+'observed561.d'))<=set(q.snapshots),'HTTPS562_OBSERVED561_ACTUAL_COMPILER_INPUTS_PREPINNED')
        step,=prior['steps'];retained={name for name,status in step['tests']if status=='ok'}
        c.require(step['exit_code']==101 and {name for name,status in step['tests']if status=='FAILED'}==FAILED
            and len(retained)==7 and len(step['tests'])==8 and step['cleanup']is True,'HTTPS562_EXACT_SEVEN_UNCHANGED_BODY_RESULTS_AND_ONE_FAILURE')
        all_cases=previous.helpers.tests(q,previous.TEST,'dispatch::')|{'requests::not_observed_prepares_owned_product_once_and_legacy_dispatchers_cannot_bypass_policy_repository'}
        c.require(all_cases==retained|FAILED,'HTTPS562_ALL_CURRENT_EIGHT_IDENTITIES')
        row.update(retained_body_cases=7,retained_body_case_names=sorted(retained),retained_result_source=PRIOR,
            original_product_logic_and_other_seven_bodies_identical=True)
        scratch=c.ROOT/'target/p09-https-common-dispatch-scratch562';c.require(not scratch.exists(),'HTTPS562_UNIQUE_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='HTTPS_COMMON_DISPATCH_CORRECTED_ONE_PREFLIGHT',inputs=len(q.snapshots),current_cases=1,retained_body_cases=7,CPU_cap_percent=6.25)),flush=True)
        args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','stored_https_target_product','--message-format=short','--',*sorted(FAILED),'--exact','--test-threads=1']
        r.harness.run_one('https_common_dispatch_corrected_one',args,FAILED,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],FAILED);c.require(not row['steps'][-1]['diagnostics'],'HTTPS562_NO_COMPILER_WARNINGS')
        found=[]
        for path in(c.ROOT/'target/debug/deps').glob('stored_https_target_product-*.d'):
            declared=previous.deps.dependencies(path);c.require(declared<=set(q.snapshots),'HTTPS562_ALL_ACTUAL_COMPILER_INPUTS_PREPINNED')
            found.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_count=len(declared),all_predeclared=True))
        c.require(len(found)==1,'HTTPS562_ONE_HOST_DEP_INFO');row['actual_compile_inputs']=found
        c.require(not any(scratch.iterdir()),'HTTPS562_COMPILER_TEMP_EMPTY');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_COMMON_HTTPS_DISPATCH_CURRENT_ONE_RETAINED_SEVEN_NOT_EXECUTION_ROUTE_OR_GATE',current_qualified_cases=1,distinct_qualified_cases=8,
            old_policyless_api_still_denied=True,route_unqualified_preserved=True,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'HTTPS562_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),resource_samples=samples,
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,previous.layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),cleanup=s['cleanup'],diagnostics=s.get('diagnostics',[]),failed_cases=[n for n,status in s.get('tests',[])if status!='ok'])for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
