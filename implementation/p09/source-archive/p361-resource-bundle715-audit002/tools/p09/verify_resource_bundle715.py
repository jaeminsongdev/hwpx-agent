"""Phase/raw resource qualification and bounded backend source inspection; no product/Native."""
import hashlib,json,re,subprocess,sys,time,tomllib
from pathlib import Path
import named_style_verification_runtime as r
import resource_bundle714 as journal
import run_prepared_bookmark_native631 as p
SELF='tools/p09/verify_resource_bundle715.py'
TEST='tools/p09/tests/test_resource_bundle714.py'
PRIOR='implementation/p09/evidence/p09-361-insertion-request713-product002.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-resource-bundle715-audit002.v1.json'
BACKEND=('crates/local-workflow/Cargo.toml','crates/local-workflow/src/lib.rs',
    'crates/local-companion-daemon/Cargo.toml','crates/local-companion-daemon/src/lib.rs',
    'web/local-companion-mcp/src/server.ts','protocol/private/p17-local-daemon-v2.json')
def require(ok,code):
    if not ok:raise ValueError('XREF_RESOURCE715_'+code)
def models(guard,expected,row):
    owned=capture=None;start=time.monotonic();step=dict(stage='discover_exact_previously_successful_models_without_running',cleanup=False);row['steps'].append(step)
    env=r.audit.environment();env['PYTHONPATH']=str(r.c.ROOT/'tools/p09')
    code="import unittest,json; pending=[unittest.defaultTestLoader.discover('tools/p09/tests',pattern='test_resource_bundle714.py')]; ids=[]\\nwhile pending:\\n item=pending.pop()\\n if isinstance(item,unittest.TestSuite):pending.extend(item)\\n else:ids.append(item.id())\\nprint(json.dumps({'loaded_model_ids':sorted(ids),'tests_executed':False}))"
    args=[sys.executable,'-B','-c',code]
    try:
        owned=r.shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[sys.executable],cwd=r.c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();require(time.monotonic()-start<20,'MODEL_DEADLINE')
            try:out,err=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        value=json.loads(out)if owned.returncode==0 and not err else None
        require(value is not None and value['tests_executed']is False,'DISCOVERY_ONLY_NO_RERUN')
        ids=value['loaded_model_ids'];require(all(name.startswith('test_resource_bundle714.Tests.')for name in ids),'EXACT_MODEL_MODULE')
        observed={name.rsplit('.',1)[1]for name in ids}
        step.update(exit_code=owned.returncode,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),
            stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest(),
            current_discovered_closed_models=sorted(observed),expected_models=len(expected),tests_executed=False)
        require(observed==expected and len(ids)==len(expected),'EXACT_CURRENT9_MODELS_RETAINED_ORIGINAL_EXIT0')
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
def main():
    require(sys.argv[1:]==['--models-and-resource-readonly-no-product']and not(r.c.ROOT/OUTPUT).exists(),'MODE_IMMUTABLE')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=binary=observer=None;begin=time.monotonic()
    row=dict(state='FAILED715_PHASE_RESOURCE',steps=[],new_product_Cargo_SQL_or_Native_started=False,
        successful713_or_previous_model20_replayed=False,original_guard_limits_changed=False,
        historical713_spike_cause_or_PC_freeze_resolution_established=False,P09_complete=False)
    try:
        observer=journal.Attached(guard);guard.acquire();observer.phase('input_binding')
        q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        prior=p.codec.unpack(q.json(PRIOR),guard.check)
        require(q.snapshots[PRIOR]['sha256']=='862bba9d45b143b6de6f8bd52a2d85aa045606fce6262f8b0266d287f1cb0892'
            and prior['cleanup']is True and prior['fresh_inputs']==prior['final_fresh_hashes']==1119,'EXACT_SUCCESSFUL713_PRESERVED_NOT_REPLAYED')
        first_path='implementation/p09/evidence/p09-361-resource-bundle715-audit001.v1.json'
        first=p.codec.unpack(q.json(first_path),guard.check)
        require(q.snapshots[first_path]['sha256']=='aded0a37b30025b03e71088211e77ea8851c5870ecdc2841c52efe4df983593b'
            and first['cleanup']is True and first['steps'][0]['exit_code']==0
            and first['steps'][0]['expected_models']==9 and first['steps'][0]['stdout_bytes']==0
            and first['steps'][0]['stderr_bytes']==1643 and first['steps'][0]['passed_closed_models']==[],
            'ORIGINAL_MODEL_DISCOVERY_AND_EXECUTION_EXIT0_ID_COLLECTOR_FAILURE_PRESERVED')
        for pin in first['source_pins']:
            name='implementation/p09/source-archive/p361-resource-bundle715-audit001/'+pin['path']if pin['path']==SELF else pin['path']
            bound=q.pin(name);require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'SAME_ORIGINAL_MODELS_AND_GUARD_CODE_ARCHIVED_COLLECTOR')
        row['retained_original_model_run']=dict(execution_exit_code=0,discovery_start='tools/p09/tests',pattern='test_resource_bundle714.py',
            module_identifiers_were_not_collected=True,stderr_sha256=first['steps'][0]['stderr_sha256'],models_reexecuted=False)
        names={SELF,TEST,'tools/p09/resource_bundle714.py',*BACKEND}
        for module in tuple(sys.modules.values()):
            name=getattr(module,'__file__',None)
            if name:
                path=Path(name)
                if path.is_relative_to(r.c.ROOT/'tools/p09')and path.suffix=='.py':names.add(path.relative_to(r.c.ROOT).as_posix())
        require(len(names)<=512,'COMPONENT_MODULE_SCOPE_BOUND')
        for name in sorted(names):q.pin(name)
        prior_by={pin['path']:pin for pin in prior['source_pins']}
        retained=[name for name in names if name in prior_by]
        for name in retained:require(q.snapshots[name]==prior_by[name],'UNCHANGED_PRIOR_RUNTIME_AND_GUARD_CODE')
        row['unchanged_prior_runtime_inputs']=len(retained)
        expected=set(re.findall(r'def (test_[A-Za-z0-9_]+)\(',q.text(TEST)));require(len(expected)==9,'EXACT_NEW9')
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)
        binary=r.a.AcceptanceReader(Path(sys.executable).parent,guard.check)
        binary.pin(Path(sys.executable).name)
        observer.phase('model_checks');models(guard,expected,row)
        observer.phase('backend_inspection')
        workflow=q.text('crates/local-workflow/src/lib.rs');daemon=q.text('crates/local-companion-daemon/src/lib.rs')
        bridge=q.text('web/local-companion-mcp/src/server.ts')
        dependency_sets={name:sorted(tomllib.loads(q.text(name)).get('dependencies',{}))for name in BACKEND if name.endswith('Cargo.toml')}
        require(all('hwpx-agent-cli'not in values and'product-cli'not in values for values in dependency_sets.values()),'OBSERVED_BACKEND_NOT_LINKED_TO_PRODUCT_LIBRARY')
        require(all('pub fn '+name+'('in workflow for name in('open','materialize','diff','publish')),'EXISTING_LOCAL_WORKFLOW_ENTRY_POINTS')
        require('local_companion_publish'in bridge and'local_companion_health'in bridge,'OBSERVED_BRIDGE_CATALOG')
        row['backend_static_observation']=dict(dependencies=dependency_sets,
            current_local_workflow_handles_materialize_diff_publish=True,
            product_library_dependency_present=False,new_insertion_backend_runtime_qualified=False,
            inspected_code_only=True,live_config_or_trust_DB_changed=False)
        require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_PROCESS_CHANGE')
        observer.phase('final_binary');binary.finish()
        observer.phase('final_source');q.finish()
        observer.phase('final_resource');guard.check(force=True)
        row.update(state='QUALIFIED715_LOSSLESS_PHASE_RESOURCES_NEW9_LIVE_ORIGINAL_GUARD_BACKEND_SOURCE_ONLY',
            new_models=9,resource_capture_integrated_with_live_original_guard=True,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**p.runtime.io.safe_failure(error))
    finally:
        guard.close()
        observer_cleanup=True if observer is None else observer.close()
        if observer is not None:row['phase_resources']=observer.packet()
        row.update(cleanup=guard.cleanup and observer_cleanup and all(step['cleanup']for step in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,interpreter_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-resource-bundle715-audit002-forensic',row);pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','interpreter_final_fresh_hashes','new_models','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'recorded_original_samples':len(guard.samples),'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED715_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
