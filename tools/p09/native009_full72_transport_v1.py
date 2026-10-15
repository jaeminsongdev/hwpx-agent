"""Full72 worker packet around original reconstruction and fixed prior69.

Only private dependency injection, exact69->72 count slots and the new capsule
suffix change. Original full68/69/70/72 constructors, hash/schema/wire checks,
worker body and product10 remain. This module never dispatches a product.
"""
import copy
import hashlib
import json
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/native009_full72_transport_v1.py'
TEST='tools/p09/tests/test_native009_full72_transport_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
FIELD7='native007_executed_failure_declaration'
FIELD2='legacy_validation_failure_declarations'
MANIFEST=PREFIX+'successor-native009-full72-manifest001.v1.json'
HINT=PREFIX+'successor-worker-bootstrap009.v3.json'
CAPSULE=PREFIX+'successor-worker-capsule009.compact.v3.json'
GRAPH=PREFIX+'successor-native009-full72-graph001.v1.json'
CODE72=dict(path=PREFIX+'legacy2-binding-code001.v1.json',bytes=27274,
    sha256='7c32f19ce6cb725600cebc4a04e9701833a5183267fd2d3372cfbb22cf039767')
PINS=[
 dict(path='tools/p09/native009_worker_transport_v1.py',bytes=18239,sha256='18f41dfa319f50ac4c5e3aa8623cc8f5c6562a9347f222305b7c9967990e8d2c'),
 dict(path='tools/p09/native007_failure_binding_v1.py',bytes=14269,sha256='f3bd8f01ad108f9c28f2bb0d985ebdffbabe08547f5aca7c2dc572e810ed8ded'),
 dict(path='tools/p09/legacy_validation_binding_v1.py',bytes=20142,sha256='228627cc1aa2b746e6d904ea5849e043dd0adb518206f5aea67e260ea6f9ad41'),
 dict(path='tools/p09/native009_engine_connection_v1.py',bytes=9522,sha256='fee9a1af80ec92b7422db8d4b707422c8b7efe1699fa17336b2a38b258baff18')]


def require(ok,label):
    if not ok:raise ValueError('NATIVE009_FULL72_'+label)


def constant(original,old,new,name,source):
    require(type(original) is FunctionType and original.__name__==name
        and original.__code__.co_filename.replace('\\','/').endswith(source),'EXACT_PRIVATE_FUNCTION')
    before=original.__code__;slots=[i for i,v in enumerate(before.co_consts) if type(v) is type(old) and v==old]
    require(len(slots)==1,'ONE_TYPED_CONSTANT_SLOT')
    values=list(before.co_consts);values[slots[0]]=new;code=before.replace(co_consts=tuple(values))
    undo=list(code.co_consts);undo[slots[0]]=old
    require(code.replace(co_consts=tuple(undo))==before,'WHOLE_CODE_INVERSE')
    fn=FunctionType(code,original.__globals__,name=original.__name__,argdefs=original.__defaults__,closure=original.__closure__)
    fn.__kwdefaults__=original.__kwdefaults__
    return fn,dict(function=name,old=old,new=new,constant_slot=slots[0],whole_code_inverse=True,
        original_defaults_closure_and_globals_retained=True)


def connect(root,loader,scope,bytes_policy,xz,bounded,checkpoint,exact):
    libs,source_proofs=loader.load(root,PINS,{})
    base=libs.native009_worker_transport_v1;failed7=libs.native007_failure_binding_v1;legacy=libs.legacy_validation_binding_v1
    injected=[]
    def load(actual_root,pins,reuse):
        names,proof=loader.load(actual_root,pins,reuse)
        if pins==base.PINS:
            require(not injected,'ONE_PRIVATE_BASE_DEPENDENCY_INJECTION');injected.append(True)
            failed8=names.native008_failure_binding_v1
            def installed(module,prior68,admitted8,codec,*,physical_run):
                original_proof=failed8.install(module,prior68,admitted8,codec,physical_run=physical_run)
                pair8=dict(schema_version=module.source.SCHEMA,next_case=165,
                    semantic_original_pin=copy.deepcopy(failed8.ORIGINAL),physical_envelope_pin=copy.deepcopy(failed8.PHYSICAL))
                prior69=copy.deepcopy(prior68)+[pair8]
                failed7.install(module,prior69,copy.deepcopy(failed7.ROLE),codec,physical_run=physical_run)
                prior70=prior69+[dict(schema_version=module.source.SCHEMA,next_case=165,
                    semantic_original_pin=copy.deepcopy(failed7.ORIGINAL),physical_envelope_pin=copy.deepcopy(failed7.PHYSICAL))]
                legacy.install(module,prior70,copy.deepcopy(legacy.ROLE),codec,physical_run=physical_run)
                return dict(original_proof,all69_70_72_constructor_layers_installed=True,parent_fresh_admission_still_required=True)
            names=NS(**{**vars(names),'native008_failure_binding_v1':NS(**{**vars(failed8),'install':installed})})
        return names,proof
    proxy=NS(**{**vars(loader),'load':load})
    api=base.connect(root,proxy,scope,bytes_policy,xz,bounded,checkpoint,exact)
    revised,suffix_proof=constant(api.runtime.validate_worker_hint,'.compact.v1.json','.compact.v3.json',
        'validate_worker_hint','current_queue_successor_runtime.py')
    base.publish_function(api.runtime,'validate_worker_hint',revised)
    reconstruction,count_proof=constant(api.reconstruct,69,72,'reconstruct','native009_worker_transport_v1.py')
    build,engine_proof=constant(libs.native009_engine_connection_v1.build,69,72,'build','native009_engine_connection_v1.py')
    def core_hint(hint):
        require(type(hint) is dict and FIELD7 in hint and FIELD2 in hint,'BOTH_EXTRA_FAILURE_DECLARATIONS')
        exact(hint[FIELD7],failed7.ROLE,'EXACT_EXECUTED_BUT_FAILED007_ROLE')
        exact(hint[FIELD2],legacy.ROLE,'EXACT_TWO_HISTORICAL_DURATION_FAILURE_ROLES')
        return {k:v for k,v in hint.items() if k not in (FIELD7,FIELD2)}
    def validate(hint):return api.validate(core_hint(hint))
    def factory(hint,prior68):
        raw=core_hint(hint);api.validate(raw);return api.factory(raw,prior68)
    def reconstruct(hint,wire,check):
        checkpoint();raw=core_hint(hint);api.validate(raw)
        graph,proof=reconstruction(raw,wire,check)
        require(len(graph.binding.descriptors())==72,'WHOLE72_AFTER_ORIGINAL_RECONSTRUCTION')
        return graph,dict(proof,descriptor_count=72,whole_original_raw_reconstruction_body_retained=True,
            two_private_count_bounds_changed_with_inverse=True,extra_failure_roles_validated_before_reconstruction=True,
            actual_Native_or_product_qualified=False)
    require(injected==[True],'ACTUAL_BASE_LOADER_INJECTION')
    return NS(runtime=api.runtime,metadata=api.metadata,factory=factory,validate=validate,reconstruct=reconstruct,build=build,
        roles=NS(failed7=copy.deepcopy(failed7.ROLE),legacy=copy.deepcopy(legacy.ROLE)),
        source_proofs=source_proofs+api.source_proofs,count_proof=count_proof,engine_proof=engine_proof,suffix_proof=suffix_proof,
        original_default_modules_mutated=False,old_api=api)


def main():
    import argparse,importlib.util,io,re,sys,time,unittest
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
    import native009_parent_scope_v1 as parent
    import flat_current_queue_product_window_runtime_v18 as original_window
    import post_product_recovery_window_v1 as window_tool
    import post_product_recovery_connection_v1 as recovery
    import prepare_native007_carrier_v1 as producer
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    attempt=producer.identifier(parser.parse_args().attempt);output=PREFIX+f'native009-full72-transport-code{attempt:03}.v1.json'
    require(not(c.ROOT/output).exists(),'EXCLUSIVE_CODE_REPORT')
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))();started=time.monotonic();phase='ADMISSION';prepared=None
    row=dict(state='FAILED_NATIVE009_FULL72_TRANSPORT_NOT_ADOPTED',accepted_count_delta=0,GO_authorized=False,
        actual_worker_product_or_Native_executed=False,current_full_source_Frame_or_dispatch_qualified=False)
    encoded=lambda value:(json.dumps(value,ensure_ascii=True,indent=2,allow_nan=False)+'\n').encode('ascii')
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF);q.pin(TEST)
        code=a.read_exact(q,CODE72)
        a.fields(code,dict(state='PASS_LEGACY2_FULL72_BINDING11_AND_DECLARED_COST_NOT_WORKER_OR_NATIVE',contracts=dict(run=11,errors=0,failures=0,skipped=0),
            fresh_inputs=120,final_fresh_hashes=120,cleanup_confirmed=True,actual_engine_worker_calls=0,
            accepted_count_delta=0,GO_authorized=False),'ACTUAL_WHOLE72_BINDING_CODE')
        for pin in code['source_pins']:
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):a.exact(q.pin(pin['path']),pin,'CURRENT_QUALIFIED_PROGRAMS')
        for pin in PINS:a.exact(q.pin(pin['path']),pin,'FIXED_PRIVATE_DEPENDENCY_SOURCE')
        fixture=a.read_exact(q,code['manifest_pin']);rows=fixture['descriptors'];require(len(rows)==72,'REAL_CODE72_DESCRIPTOR_TABLE')
        old_hint=q.json(parent.BOOTSTRAP);old_manifest=a.read_exact(q,old_hint['manifest_pin']);step=old_hint['step']
        authority=a.read_exact(q,step['prior_queue_pin'])
        a.fields(authority,dict(accepted_count_after=158,next_runtime_index=165,runtime_candidate_pin=step['prior_candidate_pin']),'ACTUAL_UNADVANCED_AUTHORITY')
        loader,_=optimization.connect(envelope.namespace_bundle,cloner)
        api=connect(c.ROOT,loader,scope,bytes_policy,xz,bounded,guard.check,a.exact)
        manifest=dict(old_manifest,schema_version='hwpx-agent.p09-native009-full72-manifest/v1',descriptors=rows,
            same_case_executed_failure_role=api.roles.failed7,historical_validation_failure_roles=api.roles.legacy,
            current_whole_Native_source_scope_qualified=False)
        manifest_pin=parent.publish_bytes(c.ROOT,MANIFEST,encoded(manifest),q,guard,bytes_policy,a,262144)
        hint=copy.deepcopy(old_hint);hint.update(manifest_pin=manifest_pin,**{FIELD7:api.roles.failed7,FIELD2:api.roles.legacy})
        module=api.factory(dict(hint,capsule_pin=dict(path=CAPSULE,bytes=1,sha256='0'*64)),rows[:68])
        bound=module.Binding(rows,manifest_pin,next_case=165)
        graph,_=api.metadata.connect(c.ROOT,loader,bytes_policy,module,bound,step,9,guard.check)
        wire,_=graph.worker.encode(bound,step['prior_queue_pin'],step['prior_candidate_pin'],guard.check)
        hint['capsule_pin']=parent.publish_bytes(c.ROOT,CAPSULE,wire,q,guard,bytes_policy,a,16384)
        hint_pin=parent.publish_bytes(c.ROOT,HINT,encoded(hint),q,guard,bytes_policy,a,16384)
        phase='ORIGINAL_FULL72_RECONSTRUCTION'
        observed=dict(active=True,data_file_opens=0)
        def audit(event,args):
            if observed['active'] and event=='open' and args and isinstance(args[0],str) and args[0].lower().endswith('.json'):observed['data_file_opens']+=1
        sys.addaudithook(audit)
        try:rebuilt,proof=api.reconstruct(hint,wire,guard.check)
        finally:observed['active']=False
        a.exact(observed['data_file_opens'],0,'ORIGINAL_RECONSTRUCTION_NO_HISTORICAL_JSON_IO')
        a.exact(rebuilt.binding.descriptors(),rows,'ALL72_RECONSTRUCTED_NOT_SUBSET')
        linked=api.build(c.ROOT,loader,api,rebuilt,original_window,recovery,window_tool,guard.check)
        phase='CONTRACTS'
        spec=importlib.util.spec_from_file_location('native009_full72_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        tests.MODULE=sys.modules[__name__];tests.API=api;tests.HINT=hint;tests.WIRE=wire;tests.GRAPH=rebuilt;tests.ROWS=rows
        tests.CHECK=guard.check;tests.BOUNDED=bounded;tests.LINKED=linked
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=12,errors=0,failures=0,skipped=0),'ALL_FULL72_TRANSPORT12')
        for loaded in tuple(sys.modules.values()):
            filename=getattr(loaded,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        phase='FINAL_METADATA_HASHES';q.finish();guard.check(force=True)
        row.update(state='PASS_NATIVE009_FULL72_ORIGINAL_RECONSTRUCTION12_NOT_WORKER_OR_NATIVE',manifest_pin=manifest_pin,capsule_pin=hint['capsule_pin'],
            bootstrap_pin=hint_pin,descriptor_count=72,source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            reconstruction_proof=proof,count_proof=api.count_proof,engine_count_proof=api.engine_proof,suffix_proof=api.suffix_proof,
            reconstruction_JSON_file_opens=0,actual_engine_worker_calls=linked.state.calls)
        prepared=dict(state='PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO',index=165,physical_run=9,step=step,
            manifest_pin=manifest_pin,capsule_pin=hint['capsule_pin'],bootstrap_pin=hint_pin,descriptors=72,accepted_count_delta=0,
            product_or_Native_executed=False,GO_authorized=False,actual_current_source_Frame_qualified=False,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,cleanup_confirmed=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        import traceback
        row['error_type']=type(error).__name__;row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None))
    require(guard.cleanup,'OWNER_CLEANUP')
    if prepared is not None:row['graph_report_pin']=publisher.publish(c.ROOT,GRAPH,prepared,a)
    publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','descriptor_count','manifest_pin','capsule_pin','bootstrap_pin',
        'fresh_inputs','final_fresh_hashes','actual_engine_worker_calls','elapsed_seconds','CPU_max','owned_CPU_machine_max','owned_private_MiB_max','RAM_min','cleanup_confirmed','error_code','error_frames')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
