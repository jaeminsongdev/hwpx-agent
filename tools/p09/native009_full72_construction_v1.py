"""Construct the original full72 parent, Frame class and independent oracle.

No engine/outer/checker execution and no Frame instance. Fresh Source admission
is real; inherited pins remain declarations, not current whole-byte evidence.
Private libraries retain source bodies instead of importing and hiding modules.
"""
import json
import sys
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/native009_full72_construction_v1.py'
TEST='tools/p09/tests/test_native009_full72_construction_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
QUALIFIED=dict(path=PREFIX+'native009-verified-source-profile002.v1.json',bytes=110395,
    sha256='1ca00eeb366959d7e957b96e986f21651c17c2837a77d2a6707a43cd0d2934c4')
PINS=[
 dict(path='tools/p09/prepared_run_closure_v1.py',bytes=23900,sha256='c159da53076f5bb88dce252db163f82a1f1d71522c9dd248349ca615dc84e672'),
 dict(path='tools/p09/terminal_metadata_pressure_v1.py',bytes=2956,sha256='7b5bb9b890cde566f566857c06f010736519ac6e2551480dcf92bdab6dfdd9dd'),
 dict(path='tools/p09/distinct_final_sample_guard_v1.py',bytes=1683,sha256='8c590aa82c2677d391d6d5781b356641f77c7cdc6e55370ca251d6a809ad67c3'),
 dict(path='tools/p09/owned_cpu_baseline_v1.py',bytes=1389,sha256='0fce7a5f5700270291b02167e96c3739943d5a44c0a912eef43555a1a729b4b5'),
 dict(path='tools/p09/ast_clone_namespace_v1.py',bytes=2361,sha256='d9f0094355c628cb76743221598032a4007890fe1d08867ea4f54118c3f17b4c'),
 dict(path='tools/p09/ast_copy_namespace_connection_v1.py',bytes=3055,sha256='08c1e02736849832490a8dbabf792d0ec96e9ffb136852dd89cebe835bc744ec'),
 dict(path='tools/p09/receipt_xz_envelope_v1.py',bytes=4012,sha256='21daa1b06dd82af0a374923ecdefcdde245aafd88f2c218bcdae11f8211b5f09'),
 dict(path='tools/p09/bounded_successor_capsule_wire_v2.py',bytes=5102,sha256='3f604ad4f98c6592e37e6174b11ddac7c73f1f37373738ecc8baa2b6cfb1dd30'),
 dict(path='tools/p09/native009_full72_transport_v1.py',bytes=15741,sha256='441a0c98198d0442552004d918d4f6516e1c67e38a9de3585cd8e5a84612080e'),
 dict(path='tools/p09/native009_verified_source_profile_v1.py',bytes=16808,sha256='c9422ff0fd16a2583b40689b3533dfd666a196c8c1c4797440df6e365d1aa483'),
 dict(path='tools/p09/post_product_recovery_window_v1.py',bytes=12876,sha256='ce0dd3fdddc238dd7181d5c12c0a161a2dea74c791dc8053dd99a2b0ca7e8890'),
 dict(path='tools/p09/post_product_recovery_connection_v1.py',bytes=8676,sha256='105e55a7534defdd5ea804a03a007c72a96079de042d21fa53d5675064968f77'),
 dict(path='tools/p09/successor_preparation_workspace_v1.py',bytes=9656,sha256='003a0978b515c148d1a7f17ba53cdcab9eb77698535714216c90b53c868bbb98')]
ORACLE=dict(path='tools/p09/current_queue_successor_oracle.py',bytes=10143,
    sha256='5656ef67c1c8521fdce9a95d96c74de84df70e45ff369aef4524059fc7e5cf9a')
LEGACY=dict(path='tools/p09/case160_run007_controller.py',bytes=10968,
    sha256='98eca8fcce39c906a1459fac0bbf3d344f8bed3c47816d5d8a0aeddc8b8f4826')
DISPATCH=dict(path='tools/p09/current_queue_successor_dispatch.py',bytes=22558,
    sha256='afa51947097da26304dbbd03fb504fad75a0b0256e9c34282b384c0c411feaef')
DECLARATION=dict(path='tools/p09/native009_parent_scope_v1.py',bytes=17887,
    sha256='5f2bd00076fcca14c81fa8f3bb2dcc6bc5adeb347bad775cd1500dc0557b02c9')


def require(ok,label):
    if not ok:raise ValueError('NATIVE009_CONSTRUCTION_'+label)


def helper_inventory(root,engine):
    defaults=set()
    for module in tuple(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).absolute()
            if path.suffix=='.py' and path.is_relative_to(root/'tools/p09'):
                defaults.add(path.relative_to(root).as_posix())
    env=engine.run_owned.__globals__
    explicit={env['SELF'],env['TEST'],env['native'].SELF,env['native'].TEST,env['scope'].SELF,env['scope'].TEST}
    names=defaults|explicit
    return dict(default_imported_helpers=sorted(defaults),explicit_original_Native_helpers=sorted(explicit),
        original_Native_helper_union=sorted(names),default_count=len(defaults),Native_count=len(names),
        observed_before_project_test_module_load=True,modules_removed_hidden_or_bound_increased=False)


def private_runtime_imports(loader):
    """Preserve runtime function bodies; late imports use its declared Binding.

    Functions capture builtins at creation, so recreate the complete private
    family after installing its local import dependency. Never edit sys.modules.
    """
    proofs=[]
    def load(root,pins,reuse):
        names,proof=loader.load(root,pins,reuse)
        selected={p['path'] for p in pins}
        if 'tools/p09/current_queue_successor_runtime.py' in selected:
            require('tools/p09/current_queue_successor_binding.py' in selected,'RUNTIME_AND_BINDING_ONE_DECLARED_BATCH')
            runtime=names.current_queue_successor_runtime;binding=names.current_queue_successor_binding
            env=runtime.validate_worker_hint.__globals__;ordinary=env['__builtins__']['__import__']
            def declared(name,globals=None,locals=None,fromlist=(),level=0):
                if name=='current_queue_successor_binding' and level==0:return binding
                return ordinary(name,globals,locals,fromlist,level)
            env['__builtins__']={**env['__builtins__'],'__import__':declared}
            functions=[]
            for name,old in tuple(vars(runtime).items()):
                if type(old) is FunctionType and old.__globals__ is env:
                    current=FunctionType(old.__code__,env,name=old.__name__,argdefs=old.__defaults__,closure=old.__closure__)
                    current.__kwdefaults__=old.__kwdefaults__
                    require(current.__code__ is old.__code__ and current.__defaults__ is old.__defaults__
                        and current.__closure__ is old.__closure__,'WHOLE_RUNTIME_CODE_DEFAULTS_CLOSURE')
                    env[name]=current;setattr(runtime,name,current);functions.append(name)
            proofs.append(dict(functions=sorted(functions),whole_original_function_bodies_retained=True,
                exact_declared_private_Binding_for_late_import=True,default_modules_mutated_or_hidden=False))
        return names,proof
    return NS(**{**vars(loader),'load':load}),proofs


def construct(root,loader,api,graph,built,envelope,recovery,window_tool,a,q,scope,inherited,prepared,graph_pin,checkpoint):
    # One real template was already constructed by api.build; do not construct it twice.
    original=built.engine;original_run=original.run_owned;original_worker=original.worker
    declared=scope.extend(inherited,q.snapshots)
    declared,_=graph.binding.semantic_union(declared,checkpoint)
    calls=[]
    def callback(reader):
        calls.append(1)
        return api.runtime.current_input_scope(reader,graph,prepared['step'],graph_pin,prepared['manifest_pin'],declared)
    def same_engine():return original,dict(single_preconstructed_engine_reused=True)
    parent,parent_state,parent_proof=api.runtime.compose_parent(same_engine,graph,callback,checkpoint)
    def same_parent():return parent,parent_proof
    dispatch=a.native.definitions(q.text(DISPATCH['path']),('compose_outer',),{})
    outer,outer_state=dispatch.compose_outer(built.window,same_parent,callback,api.metadata)
    # Historical case160/run7 supplies the actual independent checker family.
    # A private sys alias selects its original historical context without
    # rewriting real argv or relabelling it as current Native9 acceptance.
    proxy=NS(**{**vars(envelope),'namespace_bundle':loader})
    historical,_=loader.load(root,[LEGACY],{'flat_current_queue_envelope_runtime_v25':proxy,
        'sys':NS(**{**vars(sys),'argv':[]})})
    legacy=historical.case160_run007_controller
    require(legacy.NATIVE==7 and legacy.CURRENT is not None,'ORIGINAL_HISTORICAL_CHECKER_CONTEXT7')
    for pin in legacy.LEGACY_PINS+[legacy.SOURCE_PIN,legacy.TEST_PIN,legacy.BOOTSTRAP_PIN]:
        a.exact(q.pin(pin['path']),pin,'CURRENT_LEGACY_CHECKER_DECLARATIONS')
    # api.build already selected the one immutable current step. Historical
    # initialization must not reconfigure or reset that process-wide context.
    step=built.window.M.base.CONFIG
    a.fields(vars(step),dict(index=165,before=158),'CURRENT_STEP_RESTORED')
    oracles,oracle_sources=loader.load(root,[ORACLE],{'current_queue_successor_connections':api.metadata})
    raw=q.text(window_tool.WINDOW_PIN['path']).encode('utf-8')
    oracle_inherited=scope.extend(declared,q.snapshots)
    oracle_inherited,_=graph.binding.semantic_union(oracle_inherited,checkpoint)
    connect=recovery.connect_oracle(oracles.current_queue_successor_oracle.connect,window_tool,raw)
    checker,oracle_proof=connect(legacy.CURRENT,graph,step,built.names,oracle_inherited,checkpoint)
    checker.environment['only159']()
    closures=dict(zip(parent.run_owned.__code__.co_freevars,(c.cell_contents for c in parent.run_owned.__closure__)))
    frame=closures['native'].frames.Frame
    require(parent_state.frames==[] and built.state.calls==built.state.attempts==parent_state.attempts==0,'CONSTRUCTION_NOT_EXECUTION')
    require(original_worker is parent.worker and original_run is parent_state.original,'SAME_ORIGINAL_ENGINE_AND_WORKER')
    require(checker.environment['prior'].WINDOW.SECONDS==built.window.WINDOW.SECONDS==10,'PARENT_AND_INDEPENDENT_CHECKER10')
    return NS(parent=parent,parent_state=parent_state,parent_proof=parent_proof,original_run=original_run,
        original_worker=original_worker,outer=outer,outer_state=outer_state,frame=frame,callback=callback,
        callback_calls=calls,checker=checker,oracle_proof=oracle_proof,oracle_sources=oracle_sources,
        legacy=legacy,oracle_inherited=oracle_inherited,declared=declared,built=built)


def main():
    import argparse,importlib.util,io,os,re,time,traceback,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    # Permanent denial before any project graph/engine construction.
    denied=[]
    def audit(event,args):
        if event=='subprocess.Popen':
            denied.append(1);raise ValueError('CONSTRUCTION_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(audit)
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    # The envelope already constructed this exact source-pinned original. A
    # second default import would also construct a duplicate lean namespace.
    original_window=envelope.prior
    libs,bootstrap_sources=envelope.namespace_bundle.load(c.ROOT,PINS,{})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader,loader_proof=libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle,libs.ast_clone_namespace_v1)
    loader,runtime_import_proofs=private_runtime_imports(loader)
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    attempt=parser.parse_args().attempt
    require(type(attempt) is int and 1<=attempt<=8,'BOUNDED_ATTEMPT')
    output=PREFIX+f'native009-full72-construction{attempt:03}.v1.json'
    require(not(c.ROOT/output).exists(),'EXCLUSIVE_REPORT')
    Guard=libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))
    guard=Guard();started=time.monotonic();phase='ADMISSION'
    row=dict(state='FAILED_NATIVE009_FULL72_CONSTRUCTION_NOT_NATIVE',accepted_count_delta=0,GO_authorized=False,
        product_worker_or_Native_executed=False,whole_current_source_hash_Frame_and_checker_qualified=False,
        production_worker9_launch_and_readiness_connected=False,additional_product_execution_authority_pending=True,
        preparation_CPU_policy_changed=False,full_preflight_and_dispatch_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,TEST):q.pin(name)
        for pin in PINS+[ORACLE,LEGACY,DISPATCH,DECLARATION]:a.exact(q.pin(pin['path']),pin,'ALL_CONSTRUCTION_SOURCES')
        prior=a.read_exact(q,QUALIFIED)
        a.fields(prior,dict(state='PASS_NATIVE009_FRESH_VERIFIED_SOURCE9_AND_PARENT_COST_NOT_FRAME_OR_NATIVE',
            contracts=dict(run=9,errors=0,failures=0,skipped=0),fresh_inputs=527,final_fresh_hashes=527,
            actual_engine_worker_calls=0,cleanup_confirmed=True),'ACTUAL_VERIFIED_SOURCE_PROFILE9')
        for pin in prior['source_pins']:
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):
                a.exact(q.pin(pin['path']),pin,'CURRENT_QUALIFIED_CODE')
        parent=a.read_exact(q,libs.native009_verified_source_profile_v1.PARENT)
        prepared=a.read_exact(q,parent['graph_report_pin']);graph_pin=parent['graph_report_pin']
        hint=a.read_exact(q,prepared['bootstrap_pin'])
        declaration=a.read_exact(q,prior['scope_declaration_pin'])
        inherited=scope.extend(scope.pins(declaration['input_pins']),{prior['scope_declaration_pin']['path']:prior['scope_declaration_pin']})
        inherited=scope.extend(inherited,scope.pins(prior['source_pins']))
        pin,wire=q._read(prepared['capsule_pin']['path'],parse=True);q._bind(pin['path'],pin);a.exact(pin,prepared['capsule_pin'],'CURRENT72_WIRE')
        phase='FRESH_SOURCE_POLICY_AND_ORIGINAL_ENGINE'
        source=libs.native009_verified_source_profile_v1.connect(c.ROOT,loader,scope,bytes_policy,libs.receipt_xz_envelope_v1,
            libs.bounded_successor_capsule_wire_v2,guard.check,a,q,hint,libs.native009_full72_transport_v1)
        api=source.api;graph,_=api.reconstruct(hint,bytes(wire),guard.check);del wire
        adapters,_=loader.load(c.ROOT,[DECLARATION],{})
        adapters.native009_parent_scope_v1.inherit_declaration(graph,inherited,scope)
        built=api.build(c.ROOT,loader,api,graph,original_window,libs.post_product_recovery_connection_v1,libs.post_product_recovery_window_v1,guard.check)
        phase='ORIGINAL_PARENT_FRAME_CLASS_OUTER_AND_ORACLE'
        connected=construct(c.ROOT,loader,api,graph,built,envelope,libs.post_product_recovery_connection_v1,
            libs.post_product_recovery_window_v1,a,q,scope,inherited,prepared,graph_pin,guard.check)
        helpers=helper_inventory(c.ROOT,connected.parent)
        row['helper_inventory']=helpers
        row['private_runtime_import_proofs']=runtime_import_proofs
        require(helpers['Native_count']<=64,'ORIGINAL_NATIVE_HELPER64_BEFORE_TESTS')
        for name in helpers['original_Native_helper_union']:q.pin(name)
        phase='CONSTRUCTION_CONTRACTS'
        spec=importlib.util.spec_from_file_location('native009_full72_construction_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        tests.MODULE=sys.modules[__name__];tests.CONNECTED=connected;tests.SOURCE=source;tests.GRAPH=graph
        tests.HELPERS=helpers;tests.INHERITED=inherited;tests.SCOPE=scope;tests.API=api;tests.GUARD=guard
        tests.IMPORT_PROOFS=runtime_import_proofs
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=8,errors=0,failures=0,skipped=0),'ALL_CONSTRUCTION8')
        phase='DECLARED_COST_NOT_CURRENT_FULL_HASH'
        required=scope.extend(connected.oracle_inherited,q.snapshots)
        required,_=graph.binding.semantic_union(required,guard.check)
        inventory=a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'),('rust_inputs',),dict(os=os,Path=Path,require=require))
        requests=[]
        def paced():requests.append(1);q.open_pacer.reserve()
        rust=inventory.rust_inputs(c.ROOT,paced)
        require(len(rust)==787 and set(rust)<=set(required),'CURRENT_RUST787_DECLARED')
        name=PREFIX+f'native009-full72-construction-declared-scope{attempt:03}.v1.json'
        manifest=dict(schema_version='hwpx-agent.p09-full72-construction-declared-inputs/v1',input_pins=sorted(required.values(),key=lambda p:p['path']),
            current_full_byte_Frame_and_dispatch_qualified=False,self_pin_added_separately_after_publication=True)
        raw=(json.dumps(manifest,ensure_ascii=True,indent=2)+'\n').encode('ascii')
        scope_pin=adapters.native009_parent_scope_v1.publish_bytes(c.ROOT,name,raw,q,guard,bytes_policy,a,2*1024*1024)
        required=scope.extend(required,{name:scope_pin})
        budget=graph.binding.runtime_budget(required,len(requests),built.window.DIRECT.runtime_budget,guard.check)
        total=budget['predicted_runtime_combined_seconds']+15
        row.update(scope_declaration_pin=scope_pin,semantic_inputs=len(required),current_Rust_path_count=len(rust),inventory_requests=len(requests),
            original_complete_runtime_budget=budget,additional_readiness_seconds_without_old_credit=15,
            predicted_complete_seconds_with_readiness=total,declared_cost_nominal_fits600=total<600,
            cost_for_this_declared_construction_only_not_future_launch_or_result=True)
        phase='FINAL_METADATA_HASHES';q.finish();guard.check(force=True)
        require(not denied and not connected.callback_calls and not connected.checker.projectors,'NO_DISPATCH_OR_CHECKER_EXECUTION')
        require(not(c.ROOT/(PREFIX+'current-runtime-run009.v1.json')).exists(),'NATIVE009_REMAINS_ABSENT')
        row.update(state='PASS_FULL72_PARENT_FRAME_CLASS_OUTER_AND_INDEPENDENT_ORACLE8_NOT_NATIVE',
            actual_worker_calls=built.state.calls,actual_parent_attempts=connected.parent_state.attempts,actual_Frame_instances=len(connected.parent_state.frames),
            actual_parent_callback_calls=len(connected.callback_calls),actual_oracle_projectors=len(connected.checker.projectors),
            exact_original_engine_worker_and_outer_retained=True,parent_and_independent_oracle_window_seconds=10,
            oracle_connection_proof=connected.oracle_proof,source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
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
        'predicted_complete_seconds_with_readiness','declared_cost_nominal_fits600','fresh_inputs','final_fresh_hashes',
        'actual_worker_calls','actual_parent_attempts','actual_Frame_instances','elapsed_seconds','CPU_max','owned_CPU_machine_max',
        'owned_private_MiB_max','RAM_min','cleanup_confirmed','operation_phase','error_code','error_frames')},allow_nan=False))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
