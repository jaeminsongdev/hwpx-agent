"""Current full72 packet through the whole original parent callback.

Whole declared scope/cost and current Rust path sets only. No full source-byte
freshness/Frame/Native/helper64 qualification, worker execution or GO.
"""
import copy
import json
import sys
from pathlib import Path

SELF='tools/p09/native009_full72_parent_v1.py'
TEST='tools/p09/tests/test_native009_full72_parent_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
TRANSPORT=dict(path=PREFIX+'native009-full72-transport-code001.v1.json',bytes=24311,
    sha256='a7f40dbdc805f659afad4742308da090084c22151f497f89e7eb9f4c9e0a1770')


def require(ok,label):
    if not ok:raise ValueError('NATIVE009_FULL72_PARENT_'+label)


def graph_name(attempt):
    require(type(attempt) is int and 1<=attempt<=8,'BOUNDED_GRAPH_ATTEMPT')
    return PREFIX+f'successor-native009-full72-parent-graph{attempt:03}.v1.json'


def prepare_graph(c,a,envelope,scope,bytes_policy,xz,bounded,optimization,cloner,transport,parent,publisher,Guard,attempt):
    import time,re,traceback
    output=PREFIX+f'native009-full72-parent-graph-preparation{attempt:03}.v1.json'
    require(not(c.ROOT/output).exists() and not(c.ROOT/graph_name(attempt)).exists(),'EXCLUSIVE_PARENT_GRAPH')
    guard=Guard();started=time.monotonic();prepared=None
    row=dict(state='FAILED_FULL72_PARENT_GRAPH_METADATA_NOT_NATIVE',accepted_count_delta=0,GO_authorized=False,
        actual_worker_product_or_Native_executed=False,current_full_source_Frame_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,TEST,'tools/p09/prepare_current_queue_step.py',PREFIX+'step-config001.v1.json'):q.pin(name)
        code=a.read_exact(q,TRANSPORT)
        a.fields(code,dict(state='PASS_NATIVE009_FULL72_ORIGINAL_RECONSTRUCTION12_NOT_WORKER_OR_NATIVE',
            contracts=dict(run=12,errors=0,failures=0,skipped=0),cleanup_confirmed=True,descriptor_count=72),'ACTUAL_UNCHANGED_TRANSPORT')
        for pin in code['source_pins']:a.exact(q.pin(pin['path']),pin,'CURRENT_TRANSPORT_DEPENDENCIES')
        old=a.read_exact(q,code['graph_report_pin']);hint=a.read_exact(q,old['bootstrap_pin'])
        pin,buffer=q._read(old['capsule_pin']['path'],parse=True);q._bind(pin['path'],pin);a.exact(pin,old['capsule_pin'],'SAME_ACTUAL72_WIRE')
        loader,_=optimization.connect(envelope.namespace_bundle,cloner)
        api=transport.connect(c.ROOT,loader,scope,bytes_policy,xz,bounded,guard.check,a.exact)
        graph,_=api.reconstruct(hint,bytes(buffer),guard.check);del buffer
        require(len(graph.binding.descriptors())==72,'ALL72_UNCHANGED')
        for loaded in tuple(sys.modules.values()):
            filename=getattr(loaded,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        q.finish();guard.check(force=True)
        prepared=dict(old,source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_step_config_and_original_derivation_sources_explicit=True,cleanup_confirmed=True)
        row.update(state='PASS_FULL72_PARENT_GRAPH_STEP_SOURCES_NOT_CALLBACK_OR_NATIVE',fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes,source_pins=list(q.snapshots.values()))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row['error_type']=type(error).__name__;row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-5:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None))
    require(guard.cleanup,'PARENT_GRAPH_OWNER_CLEANUP')
    if prepared is not None:row['graph_report_pin']=publisher.publish(c.ROOT,graph_name(attempt),prepared,a)
    publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','fresh_inputs','final_fresh_hashes','elapsed_seconds','CPU_max','owned_CPU_machine_max','RAM_min','cleanup_confirmed','error_code','error_frames')}))
    return 0 if row['state'].startswith('PASS_') else 1


def main():
    import argparse,importlib.util,io,os,re,time,traceback,unittest
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
    import native009_parent_scope_v1 as parent
    import native009_full72_transport_v1 as transport
    import flat_current_queue_product_window_runtime_v18 as original_window
    import post_product_recovery_window_v1 as window_tool
    import post_product_recovery_connection_v1 as recovery
    import prepare_native007_carrier_v1 as producer
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    parser.add_argument('--prepare-graph',action='store_true');parser.add_argument('--graph-attempt',type=int,default=1)
    args=parser.parse_args();attempt=producer.identifier(args.attempt)
    Guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))
    if args.prepare_graph:return prepare_graph(c,a,envelope,scope,bytes_policy,xz,bounded,optimization,cloner,transport,parent,publisher,Guard,attempt)
    output=PREFIX+f'native009-full72-parent{attempt:03}.v1.json'
    require(not(c.ROOT/output).exists(),'EXCLUSIVE_PARENT_REPORT')
    guard=Guard();started=time.monotonic();phase='ADMISSION'
    row=dict(state='FAILED_NATIVE009_FULL72_PARENT_NOT_NATIVE',accepted_count_delta=0,GO_authorized=False,
        actual_worker_product_or_Native_executed=False,current_full_source_hash_Frame_or_dispatch_qualified=False,
        whole_Native_helper64_qualified=False,additional_dispatch_and_result_sources_must_be_recosted=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF);q.pin(TEST)
        qualified=a.read_exact(q,TRANSPORT)
        a.fields(qualified,dict(state='PASS_NATIVE009_FULL72_ORIGINAL_RECONSTRUCTION12_NOT_WORKER_OR_NATIVE',
            contracts=dict(run=12,errors=0,failures=0,skipped=0),descriptor_count=72,fresh_inputs=116,final_fresh_hashes=116,
            actual_engine_worker_calls=0,cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False),'EXACT_FULL72_TRANSPORT12')
        for pin in qualified['source_pins']:a.exact(q.pin(pin['path']),pin,'ALL_CURRENT_QUALIFIED_GRAPH_INPUTS')
        old_prepared=a.read_exact(q,qualified['graph_report_pin'])
        prepared=q.json(graph_name(args.graph_attempt));graph_pin=q.snapshots[graph_name(args.graph_attempt)]
        for key in ('step','manifest_pin','capsule_pin','bootstrap_pin'):
            a.exact(prepared[key],old_prepared[key],'SAME_QUALIFIED72_PACKET_AND_STEP')
        a.fields(prepared,dict(state='PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO',index=165,
            physical_run=9,descriptors=72,cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False,
            product_or_Native_executed=False),'ACTUAL_FULL72_STANDARD_GRAPH')
        basis=a.read_exact(q,transport.CODE72)
        a.fields(basis,dict(state='PASS_LEGACY2_FULL72_BINDING11_AND_DECLARED_COST_NOT_WORKER_OR_NATIVE',
            cleanup_confirmed=True,actual_engine_worker_calls=0,semantic_inputs=3167),'WHOLE_PREVIOUS_SCOPE_DECLARATION_NOT_FRESH_HASH_REUSE')
        prior_scope=a.read_exact(q,basis['scope_declaration_pin'])
        inherited=scope.extend(scope.pins(prior_scope['input_pins']),{basis['scope_declaration_pin']['path']:basis['scope_declaration_pin']})
        hint=a.read_exact(q,prepared['bootstrap_pin'])
        pin,buffer=q._read(prepared['capsule_pin']['path'],parse=True);q._bind(pin['path'],pin)
        a.exact(pin,prepared['capsule_pin'],'ACTUAL_CURRENT72_WIRE')
        loader,_=optimization.connect(envelope.namespace_bundle,cloner)
        api=transport.connect(c.ROOT,loader,scope,bytes_policy,xz,bounded,guard.check,a.exact)
        graph,_=api.reconstruct(hint,bytes(buffer),guard.check);del buffer
        row['preparation_declaration_union']=parent.inherit_declaration(graph,inherited,scope)
        explicit=scope.extend(scope.pins(prepared['source_pins']),{graph_pin['path']:graph_pin})
        explicit=scope.extend(explicit,{SELF:q.snapshots[SELF],TEST:q.snapshots[TEST],TRANSPORT['path']:TRANSPORT})
        phase='ORIGINAL_WHOLE_PARENT_CALLBACK'
        required,rust=api.runtime.current_input_scope(q,graph,hint['step'],graph_pin,prepared['manifest_pin'],explicit)
        required=scope.extend(required,inherited);required=scope.extend(required,q.snapshots)
        required,_=graph.binding.semantic_union(required,guard.check)
        require(all(required.get(n)==p for n,p in inherited.items()),'NO_PREVIOUS_DECLARED_INPUT_REMOVED')
        phase='CURRENT_RUST_INVENTORY'
        inventory=a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'),('rust_inputs',),dict(os=os,Path=Path,require=require))
        requests=[]
        def paced():requests.append(1);q.open_pacer.reserve()
        actual=inventory.rust_inputs(c.ROOT,paced);a.exact(actual,rust,'CURRENT_RUST787_PATH_SET')
        linked=api.build(c.ROOT,loader,api,graph,original_window,recovery,window_tool,guard.check)
        for loaded in tuple(sys.modules.values()):
            filename=getattr(loaded,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        required=scope.extend(required,q.snapshots);required,_=graph.binding.semantic_union(required,guard.check)
        name=PREFIX+f'native009-full72-parent-declared-scope{attempt:03}.v1.json'
        declaration=dict(schema_version='hwpx-agent.p09-current-full72-parent-declared-inputs/v1',input_pins=sorted(required.values(),key=lambda p:p['path']),
            current_full_source_hashes_or_Frame_qualified=False,self_pin_added_separately_after_publication=True)
        declaration_pin=parent.publish_bytes(c.ROOT,name,(json.dumps(declaration,ensure_ascii=True,indent=2)+'\n').encode('ascii'),q,guard,bytes_policy,a,2*1024*1024)
        required=scope.extend(required,{name:declaration_pin});projected,_=graph.binding.project(required,guard.check)
        phase='ORIGINAL_COMPLETE_COST'
        budget=graph.binding.runtime_budget(required,len(requests),linked.window.DIRECT.runtime_budget,guard.check)
        total=budget['predicted_runtime_combined_seconds']+15
        row.update(scope_declaration_pin=declaration_pin,semantic_inputs=len(required),physical_inputs=len(projected.physical_pins),
            physical_bytes=sum(p['bytes'] for p in projected.physical_pins.values()),current_Rust_path_count=len(rust),inventory_requests=len(requests),
            original_complete_runtime_budget=budget,additional_readiness_seconds_without_old_allowance_credit=15,
            predicted_complete_seconds_with_readiness=total,declared_cost_nominal_fits600=total<600,
            inherited_declared_inputs=len(inherited),all_previous_declared_inputs_preserved=True,
            original_parent_callback_body_unchanged=True,full_declared_input_hashes_not_freshly_read=True,actual_engine_worker_calls=linked.state.calls)
        require(total<600,'COMPLETE_SCOPE_AND_READINESS_OUTSIDE600')
        phase='FINAL_RUST_INVENTORY'
        final=[]
        def final_paced():final.append(1);q.open_pacer.reserve()
        a.exact(inventory.rust_inputs(c.ROOT,final_paced),rust,'FINAL_RUST787_PATH_SET')
        a.exact(len(final),len(requests),'SAME_FINAL_INVENTORY_PACING')
        spec=importlib.util.spec_from_file_location('native009_full72_parent_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        tests.API=api;tests.GRAPH=graph;tests.ROW=row;tests.REQUIRED=required;tests.INHERITED=inherited;tests.RUST=rust
        tests.ACTUAL_RUST=actual;tests.CHECK=guard.check;tests.LINKED=linked
        phase='PARENT_CONTRACTS'
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=6,errors=0,failures=0,skipped=0),'ALL_PARENT6')
        phase='FINAL_METADATA_HASHES';q.finish();guard.check(force=True)
        row.update(state='PASS_CURRENT_FULL72_PARENT_CALLBACK_COST6_NOT_FULL_HASH_FRAME_OR_NATIVE',
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            graph_report_pin=graph_pin,current_transport_code_pin=TRANSPORT)
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
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','semantic_inputs','physical_inputs','physical_bytes','current_Rust_path_count',
        'inventory_requests','predicted_complete_seconds_with_readiness','fresh_inputs','final_fresh_hashes','actual_engine_worker_calls',
        'elapsed_seconds','CPU_max','owned_CPU_machine_max','owned_private_MiB_max','RAM_min','cleanup_confirmed','operation_phase','error_code','error_frames')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
