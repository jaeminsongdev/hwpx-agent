"""Full73 worker in original parent/Job/Frame construction, without execution.

Keep complete inherited declarations, real fresh Source policy and independent
oracle. Reuse original contracts with only two reversible count expectations.
All subprocess creation is permanently denied before graph construction.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

SELF='tools/p09/qualify_native009_full73_parent_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
WORKER=dict(path=PREFIX+'native009-full73-production-worker001.v1.json',bytes=87923,
    sha256='da79b977a97640a0b81c7f3f6532ec3403b3ff55aca6ae5d4019692cd32048bc')
CONSTRUCTION=dict(path='tools/p09/native009_full72_construction_v1.py',bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
ENTRY='tools/p09/native009_full73_worker_entry_v1.py'
PARENT='tools/p09/native009_parent_launch_v1.py'
TEST='tools/p09/tests/test_native009_parent_launch_v1.py'
SNAPSHOT=dict(path='tools/p09/single_snapshot_source_guard_v1.py',bytes=4560,
    sha256='f3555f4395154be7c929e76eeb451226402b49cc54b0ab6da335ba94555eae43')
READINESS=[dict(path='tools/p09/worker_readiness_v1.py',bytes=6890,
    sha256='047c3f78f8a4472feeec4d56b65716f57e0429091321cb49afe5b685047d3a45'),
 dict(path='tools/p09/worker_readiness_connection_v1.py',bytes=5775,
    sha256='d306d62a08e16f717bb526b2a7fa6c60ac44890f6fed965fdf4a70daca3c0a9b')]


def require(ok,label):
    if not ok:raise ValueError('FULL73_PARENT_'+label)


def main():
    import argparse,importlib.util,io,os,re,time,traceback,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    denied=[]
    def audit(event,args):
        if event=='subprocess.Popen':denied.append(1);raise ValueError('FULL73_PARENT_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(audit)
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import audit_evidence_io as original_io
    bootstrap,_=envelope.namespace_bundle.load(c.ROOT,[CONSTRUCTION],{})
    construction=bootstrap.native009_full72_construction_v1
    libs,_=envelope.namespace_bundle.load(c.ROOT,construction.PINS+READINESS,{})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader,_=libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle,libs.ast_clone_namespace_v1)
    loader,imports=construction.private_runtime_imports(loader)
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    attempt=parser.parse_args().attempt
    require(type(attempt) is int and 1<=attempt<=8,'BOUNDED_ATTEMPT')
    output=PREFIX+f'native009-full73-parent-connection{attempt:03}.v1.json'
    native=c.ROOT/(PREFIX+'current-runtime-run009.v1.json')
    require(not(c.ROOT/output).exists() and not native.exists(),'EXCLUSIVE_REPORT_AND_NO_NATIVE009')
    guard=libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started=time.monotonic();phase='CURRENT_ADMISSION'
    row=dict(state='FAILED_FULL73_PARENT_CONNECTION_NOT_NATIVE',accepted_count_delta=0,GO_authorized=False,
        actual_product_or_Native_executed=False,whole_current_byte_Frame_and_dispatch_qualified=False,
        preparation_CPU_policy_changed=False,current_result_and_future_dispatch_sources_must_be_recosted=True)
    try:
        guard.acquire();seed=a.AcceptanceReader(c.ROOT,guard.check)
        a.exact(seed.pin(SNAPSHOT['path']),SNAPSHOT,'CURRENT_QUALIFIED_SOURCE_PREDICATE_HELPER')
        names,_=loader.load(c.ROOT,[SNAPSHOT],{'audit_evidence_io':original_io})
        snapshot=names.single_snapshot_source_guard_v1
        pin,raw=seed._read(snapshot.ORIGINAL_PIN['path'],parse=True);seed._bind(pin['path'],pin)
        a.exact(pin,snapshot.ORIGINAL_PIN,'ORIGINAL_IO_LEAF')
        Reader,_=snapshot.reader_type(a.AcceptanceReader,bytes(raw));del raw
        q=Reader(c.ROOT,guard.check)
        for pin in seed.snapshots.values():a.exact(q.pin(pin['path']),pin,'FRESH_BOOTSTRAP')
        q.pin(SELF)
        for pin in [CONSTRUCTION]+construction.PINS+READINESS:a.exact(q.pin(pin['path']),pin,'CURRENT_CORE_SOURCES')
        worker=a.read_exact(q,WORKER)
        a.fields(worker,dict(state='PASS_FULL73_PRODUCTION_MAIN_EOF_AND_PRODUCT_DENIED15_WITH_COMPLETE_DECLARED_COST_NOT_NATIVE',
            contracts=dict(run=15,errors=0,failures=0,skipped=0),fresh_inputs=387,final_fresh_hashes=387,
            semantic_inputs=3218,cleanup_confirmed=True,actual_product_or_Native_executed=False,
            previous_scope_and_budget_exactly_reconstructed=True,parent_cost_graph_worker_calls=0),'CLOSED_REAL73_WORKER_DIAGNOSTICS')
        oldpins=scope.pins(worker['source_pins'])
        for pin in oldpins.values():
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):
                a.exact(q.pin(pin['path']),pin,'ALL_CURRENT_WORKER_QUALIFIED_CODE')
        base=a.read_exact(q,worker['declared_scope_base_pin'])
        inherited=scope.extend(scope.pins(base['input_pins']),{worker['declared_scope_base_pin']['path']:worker['declared_scope_base_pin']})
        inherited=scope.extend(inherited,scope.pins(worker['declared_scope_delta_pins']))
        graph_pin=oldpins[PREFIX+'successor-native009-full73-graph005.v1.json']
        prepared=a.read_exact(q,graph_pin)
        hint=a.read_exact(q,prepared['bootstrap_pin'])
        parts,_=loader.load(c.ROOT,[oldpins[ENTRY],oldpins[PARENT],construction.DECLARATION],{})
        entry=parts.native009_full73_worker_entry_v1;parent=parts.native009_parent_launch_v1
        for pin in (entry.OLD_ENTRY,entry.OLD_LAUNCH,entry.TRANSPORT,entry.HINT,entry.WIRE,entry.STEP):
            a.exact(q.pin(pin['path']),pin,'EXACT_CURRENT_WORKER_DEPENDENCY')
        a.exact(entry.HINT,prepared['bootstrap_pin'],'EXACT_V4_HINT');a.exact(entry.WIRE,prepared['capsule_pin'],'EXACT_V4_CAPSULE')
        transport_names,_=loader.load(c.ROOT,[entry.TRANSPORT],{})
        transport=NS(connect=transport_names.native009_full73_transport_v1.connect,constant=libs.native009_full72_transport_v1.constant)
        source=libs.native009_verified_source_profile_v1.connect(c.ROOT,loader,scope,bytes_policy,libs.receipt_xz_envelope_v1,
            libs.bounded_successor_capsule_wire_v2,guard.check,a,q,hint,transport)
        pin,wire=q._read(entry.WIRE['path'],parse=True);q._bind(pin['path'],pin);a.exact(pin,entry.WIRE,'CURRENT_FULL73_PACKET')
        api=source.api;graph,_=api.reconstruct(hint,bytes(wire),guard.check);del wire
        inherited,_=graph.binding.semantic_union(inherited,guard.check)
        a.exact(len(inherited),worker['semantic_inputs'],'EXACT_COMPLETE_PREVIOUS_SCOPE')
        parts.native009_parent_scope_v1.inherit_declaration(graph,inherited,scope)
        launch=entry.launch_api(c.ROOT,loader)
        proxy,context=parent.recovery_api(libs.post_product_recovery_connection_v1,c.ROOT,q.snapshots[ENTRY],launch,
            libs.worker_readiness_v1,libs.worker_readiness_connection_v1,c)
        phase='CURRENT_FULL73_PARENT_AND_ORACLE_CONSTRUCTION'
        built=api.build(c.ROOT,loader,api,graph,envelope.prior,proxy,libs.post_product_recovery_window_v1,guard.check)
        prior_budget=graph.binding.runtime_budget(inherited,worker['inventory_requests'],built.window.DIRECT.runtime_budget,guard.check)
        a.exact(prior_budget,worker['original_complete_runtime_budget'],'EXACT_PREVIOUS_WHOLE_COST')
        for pin in [construction.ORACLE,construction.LEGACY,construction.DISPATCH,construction.DECLARATION]:
            a.exact(q.pin(pin['path']),pin,'UNCHANGED_ORIGINAL_PARENT_AND_ORACLE_CODE')
        connected=construction.construct(c.ROOT,loader,api,graph,built,envelope,libs.post_product_recovery_connection_v1,
            libs.post_product_recovery_window_v1,a,q,scope,inherited,prepared,graph_pin,guard.check)
        context.bind_parent(connected.parent_state)
        helpers=construction.helper_inventory(c.ROOT,connected.parent);row['helper_inventory']=helpers
        require(helpers['Native_count']<=64,'ACTUAL_ORIGINAL_HELPER64_BEFORE_TESTS')
        for name in helpers['original_Native_helper_union']:q.pin(name)
        phase='CURRENT_FULL73_PARENT_CONNECTION_CONTRACTS'
        suites=[];inverses=[]
        for name,path,method in (
            ('full73_original_construction_contracts',construction.TEST,'test_fresh_verified_Source_and_all72_failure_roles_preserved'),
            ('full73_parent_launch_contracts',TEST,'test_actual_current_full72_and_independent_oracle_still_connected')):
            a.exact(q.pin(path),oldpins[path],'ORIGINAL_CONTRACT_SOURCE')
            spec=importlib.util.spec_from_file_location(name,c.ROOT/path)
            tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
            tests.MODULE=parent;tests.CONNECTED=connected;tests.CONTEXT=context;tests.SOURCE=source;tests.GRAPH=graph
            tests.HELPERS=helpers;tests.INHERITED=inherited;tests.SCOPE=scope;tests.API=api;tests.GUARD=guard
            tests.IMPORT_PROOFS=imports;tests.C=c;tests.LAUNCH=launch
            revised,inverse=libs.native009_full72_transport_v1.constant(getattr(tests.Tests,method),72,73,method,Path(path).name)
            setattr(tests.Tests,method,revised);inverses.append(inverse)
            suites.append(unittest.defaultTestLoader.loadTestsFromModule(tests))
        def current_worker_and_launch_metadata_connected():
            require(launch.ENTRY==ENTRY and launch.original_api.ENTRY!=ENTRY,'CURRENT_ENTRY_ONLY_PRIVATE')
            require(len(context.windows)==1 and context.parent is connected.parent_state,'ONE_CURRENT_PARENT_WINDOW')
            require(connected.built is built and len(graph.binding.descriptors())==73,'SAME_FULL73_PARENT_ENGINE')
        def original_limits_and_unexecuted_parent_preserved():
            require(built.window.WINDOW.SECONDS==10 and libs.worker_readiness_v1.SECONDS==15,'PRODUCT10_READY15')
            require(context.jobs==context.attempts==context.frame_checks==len(context.bindings)==0,'NO_REAL_JOB_FRAME_OR_PARENT_EXECUTION')
            require(not connected.parent_state.frames and not connected.callback_calls and not connected.checker.projectors,'NO_RUNTIME_OR_ACCEPTANCE_CALLS')
        def complete_previous_scope_and_cost_preserved():
            a.exact(prior_budget,worker['original_complete_runtime_budget'],'NO_MISSING_PREVIOUS_COST_INPUTS')
            require(len(inherited)==3218 and all(connected.oracle_inherited.get(n)==p for n,p in inherited.items()),'ALL_PREVIOUS_DECLARED_INPUTS')
        suites.append(unittest.TestSuite(unittest.FunctionTestCase(fn) for fn in (current_worker_and_launch_metadata_connected,
            original_limits_and_unexecuted_parent_preserved,complete_previous_scope_and_cost_preserved)))
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.TestSuite(suites))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=23,errors=0,failures=0,skipped=0),'ORIGINAL20_PLUS_CURRENT3')
        row['whole_original_contract_count_slot_inverses']=inverses
        phase='CURRENT_COMPLETE_SCOPE_AND_COST'
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        required=scope.extend(connected.oracle_inherited,q.snapshots);required,_=graph.binding.semantic_union(required,guard.check)
        require(all(required.get(n)==p for n,p in inherited.items()),'NO_PREVIOUS_INPUT_REMOVED')
        inventory=a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'),('rust_inputs',),dict(os=os,Path=Path,require=require))
        requests=[]
        def paced():requests.append(1);q.open_pacer.reserve()
        rust=inventory.rust_inputs(c.ROOT,paced);require(len(rust)==787 and set(rust)<=set(required),'CURRENT_RUST787')
        budget=graph.binding.runtime_budget(required,len(requests),built.window.DIRECT.runtime_budget,guard.check)
        total=budget['predicted_runtime_combined_seconds']+15
        base_scope=scope.extend(scope.pins(base['input_pins']),{worker['declared_scope_base_pin']['path']:worker['declared_scope_base_pin']})
        base_scope,_=graph.binding.semantic_union(base_scope,guard.check)
        delta=sorted((p for n,p in required.items() if n not in base_scope),key=lambda p:p['path'])
        a.exact(scope.extend(base_scope,scope.pins(delta)),required,'EXACT_COMPACT_DECLARATION_ROUNDTRIP')
        row.update(previous_scope_and_budget_exactly_reconstructed=True,semantic_inputs=len(required),
            current_Rust_path_count=len(rust),inventory_requests=len(requests),original_complete_runtime_budget=budget,
            predicted_complete_seconds_with_readiness=total,declared_cost_nominal_fits600=total<600,
            additional_readiness_seconds_without_old_credit=15,declared_scope_base_pin=worker['declared_scope_base_pin'],
            declared_scope_delta_pins=delta,parent_context=context.evidence(),actual_parent_attempts=connected.parent_state.attempts,
            actual_worker_calls=built.state.calls,actual_Frame_instances=len(connected.parent_state.frames))
        phase='FINAL_METADATA_HASHES';q.finish();guard.check(force=True)
        row.update(source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            metadata_source_predicate_optimization=q.source_snapshot_diagnostics())
        require(not denied and not native.exists(),'NO_SUBPROCESS_OR_NATIVE009')
        require(total<600,'COMPLETE_DECLARED_SCOPE_PLUS_READINESS_OUTSIDE600')
        row['state']='PASS_FULL73_PARENT_LAUNCH_JOB_FRAME_AND_ORACLE23_WITH_DECLARED_COST_NOT_NATIVE'
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError) as error:
        row['error_type']=type(error).__name__
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None),subprocess_creation_attempts=len(denied))
    require(guard.cleanup,'OWNER_CLEANUP');libs.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','semantic_inputs','predicted_complete_seconds_with_readiness',
        'fresh_inputs','final_fresh_hashes','actual_parent_attempts','actual_worker_calls','actual_Frame_instances','elapsed_seconds','CPU_max',
        'owned_CPU_machine_max','owned_private_MiB_max','RAM_min','cleanup_confirmed','operation_phase','error_code','error_frames')},allow_nan=False))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
