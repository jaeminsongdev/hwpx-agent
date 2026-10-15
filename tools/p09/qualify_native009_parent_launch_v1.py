"""Original full72 parent with run9 launch/Job/Frame dependencies, no execution.

Contract and declared cost qualification only. Permanent Popen denial, no real
Frame or parent/worker dispatch and no new scope-manifest duplication.
"""
import json
import sys
from pathlib import Path

SELF='tools/p09/qualify_native009_parent_launch_v1.py'
PARENT='tools/p09/native009_parent_launch_v1.py'
TEST='tools/p09/tests/test_native009_parent_launch_v1.py'
LAUNCH='tools/p09/native009_worker_launch_v1.py'
ENTRY='tools/p09/native009_worker_entry_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
CONSTRUCTION=dict(path='tools/p09/native009_full72_construction_v1.py',bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
BASE=dict(path=PREFIX+'native009-full72-construction003.v1.json',bytes=82460,
    sha256='f4593cd202f7e7ef146f1615d4cd6a34d26261d8743322536301180a1e3bf27a')
WORKER=dict(path=PREFIX+'native009-production-worker-launch001.v1.json',bytes=73756,
    sha256='37bc875206a632d96709f93570275185b55230fbfcd637de8bca7eb7ebbdcd22')
READINESS=[dict(path='tools/p09/worker_readiness_v1.py',bytes=6890,
    sha256='047c3f78f8a4472feeec4d56b65716f57e0429091321cb49afe5b685047d3a45'),
 dict(path='tools/p09/worker_readiness_connection_v1.py',bytes=5775,
    sha256='d306d62a08e16f717bb526b2a7fa6c60ac44890f6fed965fdf4a70daca3c0a9b')]


def require(ok,label):
    if not ok:raise ValueError('NATIVE009_PARENT_LAUNCH_QUAL_'+label)


def main():
    import argparse,importlib.util,io,os,re,time,traceback,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    denied=[]
    def audit(event,args):
        if event=='subprocess.Popen':denied.append(1);raise ValueError('CONSTRUCTION_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(audit)
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    bootstrap,_=envelope.namespace_bundle.load(c.ROOT,[CONSTRUCTION],{})
    construction=bootstrap.native009_full72_construction_v1
    libs,_=envelope.namespace_bundle.load(c.ROOT,construction.PINS+READINESS,{})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader,_=libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle,libs.ast_clone_namespace_v1)
    loader,imports=construction.private_runtime_imports(loader)
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);attempt=parser.parse_args().attempt
    require(type(attempt) is int and 1<=attempt<=8,'BOUNDED_ATTEMPT')
    output=PREFIX+f'native009-parent-launch-connection{attempt:03}.v1.json'
    require(not(c.ROOT/output).exists(),'EXCLUSIVE_REPORT')
    guard=libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started=time.monotonic();phase='CURRENT_ADMISSION'
    row=dict(state='FAILED_NATIVE009_PARENT_LAUNCH_CONNECTION_NOT_NATIVE',accepted_count_delta=0,GO_authorized=False,
        product_worker_or_Native_executed=False,whole_current_byte_Frame_and_dispatch_qualified=False,
        current_qualification_result_and_future_sources_must_be_recosted=True,
        additional_actual_product_execution_authority_pending=True,preparation_CPU_policy_changed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,PARENT,TEST,LAUNCH,ENTRY,construction.TEST):q.pin(name)
        for pin in [CONSTRUCTION]+construction.PINS+READINESS:a.exact(q.pin(pin['path']),pin,'CURRENT_CORE_SOURCES')
        base=a.read_exact(q,BASE);worker=a.read_exact(q,WORKER)
        a.fields(base,dict(state='PASS_FULL72_PARENT_FRAME_CLASS_OUTER_AND_INDEPENDENT_ORACLE8_NOT_NATIVE',
            contracts=dict(run=8,errors=0,failures=0,skipped=0),fresh_inputs=374,final_fresh_hashes=374,cleanup_confirmed=True),'ACTUAL_PREVIOUS_CONSTRUCTION8')
        a.fields(worker,dict(state='PASS_PRODUCTION_WORKER9_MAIN_AND_LAUNCH12_EOF_AND_PRODUCT_DENIED_NOT_NATIVE',
            contracts=dict(run=12,errors=0,failures=0,skipped=0),fresh_inputs=367,final_fresh_hashes=367,cleanup_confirmed=True),'ACTUAL_PRODUCTION_LAUNCH12')
        for proof in (base,worker):
            for pin in proof['source_pins']:
                if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):
                    a.exact(q.pin(pin['path']),pin,'ALL_CURRENT_PREVIOUS_PROGRAM_PINS')
        declaration=a.read_exact(q,base['scope_declaration_pin'])
        inherited=scope.extend(scope.pins(declaration['input_pins']),{base['scope_declaration_pin']['path']:base['scope_declaration_pin']})
        for proof in (base,worker):inherited=scope.extend(inherited,scope.pins(proof['source_pins']))
        parent=a.read_exact(q,libs.native009_verified_source_profile_v1.PARENT)
        prepared=a.read_exact(q,parent['graph_report_pin']);graph_pin=parent['graph_report_pin']
        hint=a.read_exact(q,prepared['bootstrap_pin'])
        pin,wire=q._read(prepared['capsule_pin']['path'],parse=True);q._bind(pin['path'],pin);a.exact(pin,prepared['capsule_pin'],'CURRENT_FULL72_PACKET')
        phase='REAL_FRESH_SOURCE_POLICY_AND_PARENT_CONSTRUCTION'
        source=libs.native009_verified_source_profile_v1.connect(c.ROOT,loader,scope,bytes_policy,libs.receipt_xz_envelope_v1,
            libs.bounded_successor_capsule_wire_v2,guard.check,a,q,hint,libs.native009_full72_transport_v1)
        api=source.api;graph,_=api.reconstruct(hint,bytes(wire),guard.check);del wire
        adapters,_=loader.load(c.ROOT,[construction.DECLARATION],{})
        adapters.native009_parent_scope_v1.inherit_declaration(graph,inherited,scope)
        modules,_=loader.load(c.ROOT,[q.snapshots[PARENT],q.snapshots[LAUNCH]],{})
        parent_api=modules.native009_parent_launch_v1;launch=modules.native009_worker_launch_v1
        recovery=libs.post_product_recovery_connection_v1;window_tool=libs.post_product_recovery_window_v1
        proxy,context=parent_api.recovery_api(recovery,c.ROOT,q.snapshots[ENTRY],launch,libs.worker_readiness_v1,
            libs.worker_readiness_connection_v1,c)
        built=api.build(c.ROOT,loader,api,graph,envelope.prior,proxy,window_tool,guard.check)
        connected=construction.construct(c.ROOT,loader,api,graph,built,envelope,recovery,window_tool,a,q,scope,inherited,prepared,graph_pin,guard.check)
        context.bind_parent(connected.parent_state)
        helpers=construction.helper_inventory(c.ROOT,connected.parent);row['helper_inventory']=helpers
        require(helpers['Native_count']<=64,'ACTUAL_ORIGINAL_NATIVE_HELPER64_BEFORE_TESTS')
        for name in helpers['original_Native_helper_union']:q.pin(name)
        phase='CHANGED_COMPOSITION_AND_JOB_FRAME_CONTRACTS'
        suites=[]
        for name,path in (('original_construction_current_launch_contracts',construction.TEST),('current_parent_launch_contracts',TEST)):
            spec=importlib.util.spec_from_file_location(name,c.ROOT/path);tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
            tests.MODULE=parent_api;tests.CONNECTED=connected;tests.CONTEXT=context;tests.SOURCE=source;tests.GRAPH=graph
            tests.HELPERS=helpers;tests.INHERITED=inherited;tests.SCOPE=scope;tests.API=api;tests.GUARD=guard
            tests.IMPORT_PROOFS=imports;tests.C=c;tests.LAUNCH=launch
            suites.append(unittest.defaultTestLoader.loadTestsFromModule(tests))
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.TestSuite(suites))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=20,errors=0,failures=0,skipped=0),'CHANGED_COMPOSITION8_AND_PARENT_LAUNCH12')
        require(context.jobs==context.attempts==context.frame_checks==len(context.bindings)==0,'REAL_PARENT_NOT_EXECUTED_BY_SYNTHETIC_MECHANICS_TESTS')
        phase='CURRENT_RUST_PATHS_AND_WHOLE_DECLARED_COST'
        required=scope.extend(connected.oracle_inherited,q.snapshots)
        required,_=graph.binding.semantic_union(required,guard.check)
        inventory=a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'),('rust_inputs',),dict(os=os,Path=Path,require=require))
        requests=[]
        def paced():requests.append(1);q.open_pacer.reserve()
        rust=inventory.rust_inputs(c.ROOT,paced)
        require(len(rust)==787 and set(rust)<=set(required),'CURRENT_DECLARED_RUST787')
        budget=graph.binding.runtime_budget(required,len(requests),built.window.DIRECT.runtime_budget,guard.check)
        total=budget['predicted_runtime_combined_seconds']+15
        row.update(semantic_inputs=len(required),current_Rust_path_count=len(rust),inventory_requests=len(requests),
            original_complete_runtime_budget=budget,additional_readiness_seconds_without_old_credit=15,
            predicted_complete_seconds_with_readiness=total,declared_cost_nominal_fits600=total<600,
            declared_scope_base_pin=base['scope_declaration_pin'],full_scope_manifest_duplicated=False,
            all_previous_declarations_preserved=True,actual_parent_launch_context=context.evidence())
        phase='FINAL_METADATA_HASHES';q.finish();guard.check(force=True)
        require(not denied and not connected.callback_calls and not connected.checker.projectors,'NO_NATIVE_OR_CALLBACK_OR_CHECKER_EXECUTION')
        require(not(c.ROOT/(PREFIX+'current-runtime-run009.v1.json')).exists(),'NATIVE009_STILL_ABSENT')
        row.update(state='PASS_PARENT_RUN9_LAUNCH_JOB_FRAME_DEPENDENCIES20_NOT_NATIVE_OR_COMPLETE_COST',
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_parent_attempts=connected.parent_state.attempts,actual_worker_calls=built.state.calls,actual_Frame_instances=len(connected.parent_state.frames))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError) as error:
        row['error_type']=type(error).__name__;row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None),subprocess_creation_attempts=len(denied))
    require(guard.cleanup,'OWNER_CLEANUP');libs.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','semantic_inputs','current_Rust_path_count','inventory_requests',
        'predicted_complete_seconds_with_readiness','declared_cost_nominal_fits600','fresh_inputs','final_fresh_hashes','actual_parent_launch_context',
        'actual_parent_attempts','actual_worker_calls','actual_Frame_instances','elapsed_seconds','CPU_max','owned_CPU_machine_max',
        'owned_private_MiB_max','RAM_min','cleanup_confirmed','operation_phase','error_code','error_frames')},allow_nan=False))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
