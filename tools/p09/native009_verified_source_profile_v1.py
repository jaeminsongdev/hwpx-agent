"""Fresh parent VerifiedPolicy before full72 binding and original callback.

The old complete closed-source verifier runs twice on real current bytes. Its
one private run upper bound8->9 has a whole-code inverse; before_run4 and all
original source/closure/codec predicates stay. Never dispatch or provide GO.
"""
import copy
import json
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/native009_verified_source_profile_v1.py'
TEST='tools/p09/tests/test_native009_verified_source_profile_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
PRODUCER=dict(path=PREFIX+'closed-prebody-sources002.v1.json',bytes=13326,
    sha256='abf4723f84c1dc08cbd627edf6983d2af73179955e720f0f7cbb403563b01c7b')
PARENT=dict(path=PREFIX+'native009-full72-parent002.v1.json',bytes=104500,
    sha256='78ee2509445862e737d2395d5e2a0c903fcb0c5214969858a3f9161253f21684')
WORKER=dict(path=PREFIX+'native009-full72-actual-worker-probe005.v1.json',bytes=71635,
    sha256='556b0330a940730b238bdf54f88cd24ddd957db754a66692a8d61d432f149b67')
PINS=[
 dict(path='tools/p09/runtime_record_envelope_v1.py',bytes=3596,sha256='59f4a0bc32f7c03dd1651b5e31f45ad7311fb4b8a36d6490b9b39242895337e5'),
 dict(path='tools/p09/closed_prebody_runtime_connection_v1.py',bytes=9638,sha256='9c57bda67b8b93c4cd1c228d97069ba5bc9ca8f7bec1fe904d08d8565b73faf5'),
 dict(path='tools/p09/current_queue_successor_wire_runtime_v2.py',bytes=11932,sha256='74c509ee713b571a8ed8d52f904513a567ff19391fb418942d1336a5ce6d6efd'),
 dict(path='tools/p09/runtime_record_envelope_v2.py',bytes=2891,sha256='9a97c8c9c9a6281992430bfc224bbfea036da6d780389ac2777fbb403d62960f')]


def require(ok,label):
    if not ok:raise ValueError('NATIVE009_VERIFIED_SOURCE_'+label)


def connect(root,loader,scope,bytes_policy,xz,bounded,checkpoint,a,q,hint,full72):
    require(type(hint) is dict and type(hint.get('index')) is int and hint['index']==165
        and type(hint.get('run')) is int and hint['run']==9,'ONLY_CURRENT165_RUN9')
    field='closed_prebody_source_declaration'
    require(field in hint,'EXPLICIT_CURRENT_DECLARATION')
    a.exact(hint[field]['producer_pin'],PRODUCER,'ONE_FIXED_CLOSED_SOURCE_PRODUCER')
    deps,proofs=loader.load(root,PINS,{})
    connection=deps.closed_prebody_runtime_connection_v1;bridge=deps.current_queue_successor_wire_runtime_v2
    codec=deps.runtime_record_envelope_v2;state=NS(ready=False,policy=None,alias=None,bindings=None,transport=None,verify_proof=None)
    expected_pin='tools/p09/closed_prebody_source_alias_v1.py'
    def load(actual_root,pins,reuse):
        names,proof=loader.load(actual_root,pins,reuse)
        selected={p['path'] for p in pins}
        if expected_pin in selected:
            # Only the original full8 dependency batch contains all these APIs.
            require(selected=={'tools/p09/current_queue_successor_runtime.py','tools/p09/current_queue_successor_connections.py',
                'tools/p09/current_queue_successor_binding.py','tools/p09/closed_prebody_worker_connection_v1.py',expected_pin,
                'tools/p09/prior_preparation_alias_v1.py','tools/p09/xz_ordinary_binding_v1.py','tools/p09/native008_failure_binding_v1.py'},'EXACT_BASE8_DEPENDENCY_SET')
            require(not state.ready,'ONE_CURRENT_PARENT_ADMISSION')
            alias=names.closed_prebody_source_alias_v1
            original=alias.verify
            revised,inverse=full72.constant(original,8,9,'verify','closed_prebody_source_alias_v1.py')
            alias.verify=revised
            policy=alias.verify(q,PRODUCER,165,9,a,scope,bridge,codec,'hwpx-agent.p09-lossless-runtime-source-projection/v1')
            a.exact(policy.evidence(),hint[field],'FRESH_VERIFIED_POLICY_EQUALS_FIXED_DECLARATION')
            state.policy=policy;state.alias=alias;state.bindings=names.current_queue_successor_binding
            state.transport=names.closed_prebody_worker_connection_v1;state.verify_proof=inverse
            state.original_verify=original;state.ready=True
            q.closed_source_policy=policy
            facade=connection.binding_api(state.bindings,alias,policy)
            names=NS(**{**vars(names),'current_queue_successor_binding':facade})
        return names,proof
    profile=NS(**{**vars(loader),'load':load})
    api=full72.connect(root,profile,scope,bytes_policy,xz,bounded,checkpoint,a.exact)
    require(state.ready and type(state.policy) is state.alias.VerifiedPolicy,'ACTUAL_COMPLETE_PARENT_POLICY_BEFORE_FACTORY')
    # Isolate the original four-function runtime family. The old connector's
    # publish_function changes only this private copy, not worker validators.
    names=('worker_hint','validate_worker_hint','reconstruct_worker_graph','current_input_scope')
    env=dict(api.runtime.current_input_scope.__globals__);functions={}
    for name in names:
        old=getattr(api.runtime,name)
        clone=FunctionType(old.__code__,env,name=old.__name__,argdefs=old.__defaults__,closure=old.__closure__)
        clone.__kwdefaults__=old.__kwdefaults__;functions[name]=clone;env[name]=clone
    isolated=NS(**{**vars(api.runtime),**functions})
    original_scope=functions['current_input_scope']
    proof=connection.connect(isolated,state.bindings,state.alias,state.transport,scope,a,bridge,codec,
        'hwpx-agent.p09-lossless-runtime-source-projection/v1',parent_policy=state.policy)
    api.runtime.current_input_scope=isolated.current_input_scope
    return NS(api=api,state=state,connection=connection,bridge=bridge,codec=codec,source_proofs=proofs,
        callback_proof=proof,original_scope=original_scope,isolated_runtime=isolated,
        default_modules_or_original_worker_validation_changed=False,Native_or_GO_authorized=False)


def main():
    import argparse,importlib.util,io,os,re,sys,time,traceback,unittest
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    import prepared_run_closure_v1 as host
    host.configure_host_policy(c);c.Windows()
    import accept_case112_current_epoch as a
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import owned_cpu_baseline_v1 as baseline
    import flat_current_queue_envelope_runtime_v25 as envelope
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import receipt_xz_envelope_v1 as xz
    import bounded_successor_capsule_wire_v2 as bounded
    import ast_clone_namespace_v1 as cloner
    import ast_copy_namespace_connection_v1 as optimization
    import native009_parent_scope_v1 as declaration_adapter
    import native009_full72_transport_v1 as full72
    import flat_current_queue_product_window_runtime_v18 as original_window
    import post_product_recovery_window_v1 as window_tool
    import post_product_recovery_connection_v1 as recovery
    import prepare_native007_carrier_v1 as producer
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    attempt=producer.identifier(parser.parse_args().attempt);output=PREFIX+f'native009-verified-source-profile{attempt:03}.v1.json'
    require(not(c.ROOT/output).exists(),'EXCLUSIVE_PROFILE_REPORT')
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))();started=time.monotonic();phase='ADMISSION'
    row=dict(state='FAILED_NATIVE009_VERIFIED_SOURCE_PROFILE_NOT_NATIVE',accepted_count_delta=0,GO_authorized=False,
        actual_worker_product_or_Native_executed=False,current_full_source_hash_Frame_or_dispatch_qualified=False,
        whole_Native_helper64_qualified=False,additional_Native_qualification_and_result_sources_must_be_recosted=True)
    counts={}
    class Reader(a.AcceptanceReader):
        def _read(self,name,parse=False):
            pin,raw=super()._read(name,parse=parse)
            if name in tracked:counts[name]=counts.get(name,0)+1
            return pin,raw
    tracked=set()
    try:
        guard.acquire();q=Reader(c.ROOT,guard.check);q.pin(SELF);q.pin(TEST)
        parent=a.read_exact(q,PARENT);worker=a.read_exact(q,WORKER)
        a.fields(parent,dict(state='PASS_CURRENT_FULL72_PARENT_CALLBACK_COST6_NOT_FULL_HASH_FRAME_OR_NATIVE',
            contracts=dict(run=6,errors=0,failures=0,skipped=0),fresh_inputs=506,final_fresh_hashes=506,cleanup_confirmed=True),'CURRENT_PARENT6')
        a.fields(worker,dict(state='PASS_ACTUAL_WORKER009_FULL72_EOF_AND_EXACT_COMMAND_DENIED_NOT_NATIVE',
            sanitizer_contracts=dict(run=5,errors=0,failures=0,skipped=0),fresh_inputs=356,final_fresh_hashes=356,cleanup_confirmed=True),'CURRENT_WORKER_DIAGNOSTICS')
        for proof in (parent,worker):
            for pin in proof['source_pins']:
                if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):a.exact(q.pin(pin['path']),pin,'CURRENT_QUALIFIED_PROGRAMS')
        for pin in PINS:a.exact(q.pin(pin['path']),pin,'UNMODIFIED_ADMISSION_CONNECTION_SOURCES')
        prepared=a.read_exact(q,parent['graph_report_pin']);hint=a.read_exact(q,prepared['bootstrap_pin'])
        tracked.update(r['semantic_original_pin']['path'] for r in hint['closed_prebody_source_declaration']['closed_descriptors'])
        old=a.read_exact(q,parent['scope_declaration_pin'])
        inherited=scope.extend(scope.pins(old['input_pins']),{parent['scope_declaration_pin']['path']:parent['scope_declaration_pin']})
        for extra in (parent['source_pins'],worker['source_pins']):inherited=scope.extend(inherited,scope.pins(extra))
        pin,buffer=q._read(prepared['capsule_pin']['path'],parse=True);q._bind(pin['path'],pin);a.exact(pin,prepared['capsule_pin'],'CURRENT_FULL72_CAPSULE')
        loader,_=optimization.connect(envelope.namespace_bundle,cloner)
        phase='FRESH_PARENT_SOURCE_ADMISSION'
        linked=connect(c.ROOT,loader,scope,bytes_policy,xz,bounded,guard.check,a,q,hint,full72)
        api=linked.api;graph,_=api.reconstruct(hint,bytes(buffer),guard.check);del buffer
        row['preparation_declaration_union']=declaration_adapter.inherit_declaration(graph,inherited,scope)
        explicit=scope.extend(scope.pins(prepared['source_pins']),{parent['graph_report_pin']['path']:parent['graph_report_pin']})
        explicit=scope.extend(explicit,{SELF:q.snapshots[SELF],TEST:q.snapshots[TEST]})
        phase='FRESH_READMISSION_AND_ORIGINAL_PARENT_CALLBACK'
        required,rust=api.runtime.current_input_scope(q,graph,hint['step'],parent['graph_report_pin'],prepared['manifest_pin'],explicit)
        row['original_closed_raw_reads_before_closing_hashes']=dict(counts)
        require(len(counts)==2 and all(n>=2 for n in counts.values()),'BOTH_ACTUAL_ORIGINALS_READ_BY_INITIAL_AND_CALLBACK_ADMISSION')
        required=scope.extend(required,inherited);required=scope.extend(required,q.snapshots)
        required,_=graph.binding.semantic_union(required,guard.check)
        require(all(required.get(n)==pin for n,pin in inherited.items() if n not in graph.binding.reverse),'NO_DECLARED_INPUT_REMOVAL')
        engine=api.build(c.ROOT,loader,api,graph,original_window,recovery,window_tool,guard.check)
        phase='CURRENT_RUST_PATHS'
        inventory=a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'),('rust_inputs',),dict(os=os,Path=Path,require=require))
        requests=[]
        def paced():requests.append(1);q.open_pacer.reserve()
        a.exact(inventory.rust_inputs(c.ROOT,paced),rust,'CURRENT_RUST787_PATH_SET')
        phase='CODE_CONTRACTS'
        spec=importlib.util.spec_from_file_location('native009_verified_source_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        tests.MODULE=sys.modules[__name__];tests.LINKED=linked;tests.GRAPH=graph;tests.REQUIRED=required
        tests.HINT=hint;tests.CHECK=guard.check;tests.READER=q;tests.SCOPE=scope;tests.COUNTS=counts;tests.ENGINE=engine
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=9,errors=0,failures=0,skipped=0),'ALL_FRESH_SOURCE9')
        for loaded in tuple(sys.modules.values()):
            filename=getattr(loaded,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        required=scope.extend(required,q.snapshots);required,_=graph.binding.semantic_union(required,guard.check)
        name=PREFIX+f'native009-verified-source-declared-scope{attempt:03}.v1.json'
        declaration=dict(schema_version='hwpx-agent.p09-current-verified-source-declared-inputs/v1',input_pins=sorted(required.values(),key=lambda p:p['path']),
            full_current_source_hashes_or_Frame_qualified=False,self_pin_added_separately_after_publication=True)
        declaration_pin=declaration_adapter.publish_bytes(c.ROOT,name,(json.dumps(declaration,ensure_ascii=True,indent=2)+'\n').encode('ascii'),q,guard,bytes_policy,a,2*1024*1024)
        required=scope.extend(required,{name:declaration_pin});projected,_=graph.binding.project(required,guard.check)
        phase='ORIGINAL_COMPLETE_COST'
        budget=graph.binding.runtime_budget(required,len(requests),engine.window.DIRECT.runtime_budget,guard.check);total=budget['predicted_runtime_combined_seconds']+15
        row.update(policy_evidence=linked.state.policy.evidence(),verify_run_limit_inverse=linked.state.verify_proof,
            fresh_source_admission_before_factory_and_parent_callback=True,original_parent_callback_body_retained=True,
            worker_validator_and_default_modules_not_changed=True,actual_engine_worker_calls=engine.state.calls,
            semantic_inputs=len(required),physical_inputs=len(projected.physical_pins),physical_bytes=sum(p['bytes'] for p in projected.physical_pins.values()),
            scope_declaration_pin=declaration_pin,current_Rust_path_count=len(rust),inventory_requests=len(requests),
            original_complete_runtime_budget=budget,additional_readiness_seconds_without_old_allowance_credit=15,
            predicted_complete_seconds_with_readiness=total,declared_cost_nominal_fits600=total<600)
        require(total<600,'COMPLETE_SCOPE_AND_READINESS_OUTSIDE600')
        phase='FINAL_METADATA_HASHES';q.finish();guard.check(force=True)
        row.update(state='PASS_NATIVE009_FRESH_VERIFIED_SOURCE9_AND_PARENT_COST_NOT_FRAME_OR_NATIVE',source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,original_closed_raw_reads_including_closing_hashes=dict(counts))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row['error_type']=type(error).__name__;row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None))
    require(guard.cleanup,'OWNER_CLEANUP');publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','semantic_inputs','physical_inputs','physical_bytes','current_Rust_path_count','inventory_requests',
        'predicted_complete_seconds_with_readiness','fresh_inputs','final_fresh_hashes','actual_engine_worker_calls','original_closed_raw_reads_before_closing_hashes',
        'elapsed_seconds','CPU_max','owned_CPU_machine_max','owned_private_MiB_max','RAM_min','cleanup_confirmed','operation_phase','error_code','error_frames')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
