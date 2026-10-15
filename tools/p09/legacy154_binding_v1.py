"""Exact legacy154 alias after the complete existing72 constructor.

Keep all semantic pins, original raw73 constructor, nonconstructor/Projection
oracles and old codecs. Only the fixed P154 duration failure is added; generic
metadata, source, EXE, fixtures and current product descriptors remain denied.
"""
import copy
import hashlib
import json
import sys
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/legacy154_binding_v1.py'
TEST='tools/p09/tests/test_legacy154_binding_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
PHYSICAL_PROOF=dict(path=PREFIX+'legacy154-full73-physical-g001-attempt001.v1.json',bytes=94286,
    sha256='c24cea0dd8baf0e71158550df29e237cc3a4be0706858c0318bff4865191e805')
PARENT_PROOF=dict(path=PREFIX+'native009-parent-launch-connection001.v1.json',bytes=82523,
    sha256='8154f72ea6e94fcd217a5b46cde20be702cbf3818ca05048d381d09d7dc7843d')
CONSTRUCTION=dict(path='tools/p09/native009_full72_construction_v1.py',bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
ORIGINAL=dict(path='implementation/p09/evidence/p09-154-observed-full.actual-run01.v1.json',bytes=3917483,
    sha256='c81b34d53215da2bee70709358963db5f1de5db6fbd17caa629673011c67754a')
PHYSICAL=dict(path='implementation/p09/evidence/p361-lossless-runtime-inputs/legacy-p154-observed-full.actual-run01.failed.duration.xz8m-g001.envelope.v1.json',
    bytes=277562,sha256='0a5b83d09e650a80d604f3d832eb42a503d2aa3cba843ba4c28389e8298272c0')
TABLE72='511bd45f12ad0e600c1ea7eea335364ea382994f256898318a59a312f2f8e966'
ROLE=dict(schema_version='hwpx-agent.p09-exact-legacy154-validation-alias/v1',current_case=165,successor_physical_run=9,
    original=ORIGINAL,physical=PHYSICAL,source_role='historical_validation_worker_writer_started_duration_stop_product_execution_unknown',
    original_failure_promoted=False,actual_failed_product_child_executed=None,physical_verification_pin=PHYSICAL_PROOF,
    current_product_or_GO_qualified=False)


def require(ok,label):
    if not ok:raise ValueError('LEGACY154_BINDING_'+label)


def fingerprint(rows):
    return hashlib.sha256(json.dumps(rows,ensure_ascii=True,sort_keys=True,allow_nan=False,separators=(',',':')).encode('ascii')).hexdigest()


def admission(q,a):
    proof=a.read_exact(q,PHYSICAL_PROOF)
    a.fields(proof,dict(state='PASS_LEGACY154_COMPLETE73_PHYSICAL10_NOT_BINDING_WORKER_OR_NATIVE',
        contracts=dict(run=10,errors=0,failures=0,skipped=0),pair_count=73,decode_count=146,fresh_inputs=175,final_fresh_hashes=175,
        cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False,
        original_overwritten_or_deleted=False,prior72_mapping_or_descriptor_policy_changed=False),'ACTUAL_CURRENT_PHYSICAL73')
    a.fields(proof['record'],{k:ROLE[k] for k in ('original','physical','source_role','original_failure_promoted','actual_failed_product_child_executed')},'EXACT_UNKNOWN_FAILED_ROLE')
    require(fingerprint(proof['full72_descriptors'])==TABLE72,'FIXED_PRIOR72')
    a.fields(proof['decoder_budget'],dict(aggregate_limit_seconds=5.0,attempted_decodes=146,completed_decodes=146,
        active_decode=False,terminal_error_seen=False,two_boundaries_share_one_budget=True),'ONE_ACTUAL_146_DECODE_BUDGET')
    for pin in proof['source_pins']:
        if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):a.exact(q.pin(pin['path']),pin,'CURRENT_PHYSICAL73_VERIFIER_CODE')
    a.exact(q.pin(PHYSICAL['path']),PHYSICAL,'CURRENT_CARRIER_BYTES')
    return copy.deepcopy(ROLE),proof


def install(module,prior_rows,admitted,xz,*,physical_run):
    require(type(physical_run) is int and physical_run==9,'ONLY_CURRENT_RUN9')
    require(type(module) is NS and type(getattr(module,'source',None)) is NS,'PRIVATE_MODULE')
    module.exact(admitted,ROLE,'ONE_EXACT_UNPROMOTED_UNKNOWN_ROLE')
    require(type(prior_rows) is list and len(prior_rows)==72 and fingerprint(prior_rows)==TABLE72,'ALL_FIXED_PRIOR72')
    require(hasattr(module,'legacy_validation_aliases') and not hasattr(module,'legacy154_validation_alias'),'ONE_INSTALL_AFTER_COMPLETE72')
    source=module.source;env=source.Projection.__init__.__globals__
    require(env.get('__name__','').startswith('p09_exact_') and env.get('descriptor') is source.descriptor
        and not any(getattr(m,'__dict__',None) is env for m in tuple(sys.modules.values()) if m),'PRIVATE_SOURCE_GRAPH_NOT_DEFAULT')
    old_init=module.Binding.__init__;raw_init=module.xz_original_initialize
    require(type(raw_init) is FunctionType and raw_init.__code__.co_filename.replace('\\','/').endswith('runtime_envelope_scope_binding_v1.py'),'WHOLE_ORIGINAL_RAW_CONSTRUCTOR')
    old_descriptor=source.descriptor;old_codec=source.codec;old_representation=module.Binding.representation
    methods={n:f for n,f in vars(module.Binding).items() if n not in ('__init__','representation')};projections=dict(vars(source.Projection))
    prior=copy.deepcopy(prior_rows);provenance=copy.deepcopy(admitted)
    pair=dict(schema_version=source.SCHEMA,next_case=165,semantic_original_pin=dict(ORIGINAL),physical_envelope_pin=dict(PHYSICAL))
    complete=prior+[pair];state=dict(ready=False)
    def descriptor(old,new,*,next_case):
        if type(old) is not dict or old.get('path')!=ORIGINAL['path']:return old_descriptor(old,new,next_case=next_case)
        require(type(next_case) is int and next_case==165,'EXACT_CURRENT_CASE165')
        module.exact(source.copy_pin(old),ORIGINAL,'EXACT_LEGACY154_ORIGINAL')
        module.exact(source.copy_pin(new),PHYSICAL,'EXACT_LEGACY154_CARRIER');return copy.deepcopy(pair)
    def initialize(self,rows,manifest_pin,*,next_case):
        state['ready']=False;module.exact(rows,complete,'EXACT72_PLUS_ONE154')
        require(type(next_case) is int and next_case==165,'FULL73_CASE165')
        old_init(self,rows[:72],manifest_pin,next_case=next_case)
        module.exact(self.descriptors(),prior,'ENTIRE_ORIGINAL72_CONSTRUCTOR_COMPLETED')
        raw_init(self,rows,manifest_pin,next_case=next_case)
        module.exact(self.descriptors(),complete,'WHOLE_ORIGINAL_RAW73_CONSTRUCTOR_COMPLETED');state['ready']=True
    def decode(encoded,checkpoint):
        checkpoint();require(type(encoded) is bytes and 0<len(encoded)<=xz.MAX_BYTES,'FRESH_BOUNDED_CODEC_INPUT')
        if hashlib.sha256(encoded).hexdigest()==PHYSICAL['sha256']:
            require(state['ready'],'FULL73_CONSTRUCTOR_BEFORE154_DECODE');return xz.decode(encoded,checkpoint)
        return old_codec.decode(encoded,checkpoint)
    def representation(self,projection):
        require(ORIGINAL['path'] in self.originals,'EXPLICIT_LEGACY154_ORIGINAL')
        row=old_representation(self,projection);row['legacy154_validation_failure_provenance']=copy.deepcopy(provenance);return row
    source.descriptor=descriptor;env['descriptor']=descriptor
    source.codec=NS(**{**vars(old_codec),'decode':decode});env['codec']=source.codec
    module.Binding.__init__=initialize;module.Binding.representation=representation;module.legacy154_validation_alias=copy.deepcopy(provenance)
    require(all(vars(module.Binding).get(n) is f for n,f in methods.items()),'ALL_NONCONSTRUCTOR_ORACLES_RETAINED')
    require(all(vars(source.Projection).get(n) is f for n,f in projections.items()),'ALL_PROJECTION_METHODS_RETAINED')
    return dict(entire_original72_before_whole_raw73=True,original_nonconstructor_and_Projection_oracles_retained=True,
        original_failure_not_prebody_or_pass_and_product_execution_unknown=True,Native_or_GO_authorized=False)


def main():
    import argparse,importlib.util,io,os,re,time,traceback,unittest
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    denied=[]
    def audit(event,args):
        if event=='subprocess.Popen':denied.append(1);raise ValueError('BINDING_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(audit)
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    bootstrap,_=envelope.namespace_bundle.load(c.ROOT,[CONSTRUCTION],{})
    construction=bootstrap.native009_full72_construction_v1
    libs,_=envelope.namespace_bundle.load(c.ROOT,construction.PINS,{})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader,_=libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle,libs.ast_clone_namespace_v1)
    loader,_=construction.private_runtime_imports(loader)
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);attempt=parser.parse_args().attempt
    require(type(attempt) is int and 1<=attempt<=8,'BOUNDED_ATTEMPT')
    output=PREFIX+f'legacy154-binding-code{attempt:03}.v1.json';require(not(c.ROOT/output).exists(),'EXCLUSIVE_CODE_REPORT')
    guard=libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started=time.monotonic();phase='ADMISSION'
    row=dict(state='FAILED_LEGACY154_BINDING_NOT_ADOPTED',accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False,
        full73_worker_transport_or_Native_qualified=False,current_complete_Native_cost_qualified=False,
        current_result_and_later_transport_dispatch_sources_must_be_recosted=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF);q.pin(TEST)
        for pin in [CONSTRUCTION]+construction.PINS:a.exact(q.pin(pin['path']),pin,'CURRENT_BOOTSTRAP_SOURCES')
        admitted,physical=admission(q,a);previous=a.read_exact(q,PARENT_PROOF)
        a.fields(previous,dict(state='PASS_PARENT_RUN9_LAUNCH_JOB_FRAME_DEPENDENCIES20_NOT_NATIVE_OR_COMPLETE_COST',
            contracts=dict(run=20,errors=0,failures=0,skipped=0),fresh_inputs=381,final_fresh_hashes=381,cleanup_confirmed=True,
            actual_parent_attempts=0,actual_worker_calls=0,actual_Frame_instances=0),'REAL_PREVIOUS_CONNECTION20_NOT_COST_PASS')
        for pin in previous['source_pins']:
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):a.exact(q.pin(pin['path']),pin,'CURRENT_PARENT_CONNECTION_PROGRAMS')
        old_decl=a.read_exact(q,previous['declared_scope_base_pin'])
        inherited=scope.extend(scope.pins(old_decl['input_pins']),{previous['declared_scope_base_pin']['path']:previous['declared_scope_base_pin']})
        for proof in (previous,physical):inherited=scope.extend(inherited,scope.pins(proof['source_pins']))
        parent=a.read_exact(q,libs.native009_verified_source_profile_v1.PARENT)
        prepared=a.read_exact(q,parent['graph_report_pin']);hint=a.read_exact(q,prepared['bootstrap_pin'])
        pin,wire=q._read(prepared['capsule_pin']['path'],parse=True);q._bind(pin['path'],pin);a.exact(pin,prepared['capsule_pin'],'CURRENT_FULL72_PACKET_NOT73')
        phase='REAL_SOURCE_POLICY_AND_ORIGINAL72_ENGINE'
        fresh=libs.native009_verified_source_profile_v1.connect(c.ROOT,loader,scope,bytes_policy,libs.receipt_xz_envelope_v1,
            libs.bounded_successor_capsule_wire_v2,guard.check,a,q,hint,libs.native009_full72_transport_v1)
        api=fresh.api;graph,_=api.reconstruct(hint,bytes(wire),guard.check);del wire
        # The original72 engine is constructed only to obtain its unchanged
        # complete cost model; do not pretend it consumes a73 worker packet.
        engine=api.build(c.ROOT,loader,api,graph,envelope.prior,libs.post_product_recovery_connection_v1,
            libs.post_product_recovery_window_v1,guard.check)
        module=graph.binding_module;prior=graph.binding.descriptors();require(fingerprint(prior)==TABLE72,'ACTUAL_COMPLETE72_RECONSTRUCTION')
        methods={n:f for n,f in vars(module.Binding).items() if n not in ('__init__','representation')};projections=dict(vars(module.source.Projection))
        row['installation_proof']=install(module,prior,admitted,libs.receipt_xz_envelope_v1,physical_run=9)
        rows=copy.deepcopy(prior)+[dict(schema_version=module.source.SCHEMA,next_case=165,semantic_original_pin=dict(ORIGINAL),physical_envelope_pin=dict(PHYSICAL))]
        fixture=dict(schema_version='hwpx-agent.p09-full73-binding-code-fixture/v1',descriptors=rows,worker_packet_or_Native_graph_qualified=False)
        name=PREFIX+f'legacy154-binding-code-manifest{attempt:03}.v1.json'
        adapters,_=loader.load(c.ROOT,[construction.DECLARATION],{})
        fixture_pin=adapters.native009_parent_scope_v1.publish_bytes(c.ROOT,name,(json.dumps(fixture,ensure_ascii=True,indent=2)+'\n').encode('ascii'),q,guard,bytes_policy,a,262144)
        pin,buffer=q._read(PHYSICAL['path'],parse=True);a.exact(pin,PHYSICAL,'ACTUAL_NEW_CARRIER_FOR_CODE');encoded=bytes(buffer);del buffer
        try:module.source.codec.decode(encoded,guard.check)
        except ValueError as error:require(error.args==('LEGACY154_BINDING_FULL73_CONSTRUCTOR_BEFORE154_DECODE',),'UNCONSTRUCTED_DECODE_DENIAL')
        else:require(False,'NO_DECODE_BEFORE_COMPLETE73_CONSTRUCTION')
        phase='EXACT_BINDING_CONTRACTS'
        spec=importlib.util.spec_from_file_location('legacy154_binding_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        tests.MODULE=sys.modules[__name__];tests.BINDING=module;tests.ROWS=rows;tests.PIN=fixture_pin;tests.SCOPE=scope
        tests.CHECK=guard.check;tests.CARRIER=encoded;tests.METHODS=methods;tests.PROJECTION=projections;tests.PRIOR=prior;tests.XZ=libs.receipt_xz_envelope_v1
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=10,errors=0,failures=0,skipped=0),'ALL_BINDING10')
        del encoded;tests.CARRIER=None
        phase='CURRENT_RUST_AND_COMPLETE_DECLARED_COST'
        for loaded in tuple(sys.modules.values()):
            filename=getattr(loaded,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        required=scope.extend(inherited,q.snapshots)
        bound=module.Binding(rows,fixture_pin,next_case=165);required,_=bound.semantic_union(required,guard.check)
        require(all(required.get(n)==pin for n,pin in inherited.items() if n not in bound.reverse),'NO_PREVIOUS_SEMANTIC_INPUT_REMOVED')
        inventory=a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'),('rust_inputs',),dict(os=os,Path=Path,require=require))
        requests=[]
        def paced():requests.append(1);q.open_pacer.reserve()
        rust=inventory.rust_inputs(c.ROOT,paced);require(len(rust)==787 and set(rust)<=set(required),'CURRENT_RUST787_PATHS')
        budget=bound.runtime_budget(required,len(requests),engine.window.DIRECT.runtime_budget,guard.check);total=budget['predicted_runtime_combined_seconds']+15
        projection,_=bound.project(required,guard.check)
        row.update(semantic_inputs=len(required),physical_inputs=len(projection.physical_pins),physical_bytes=sum(p['bytes'] for p in projection.physical_pins.values()),
            current_Rust_path_count=len(rust),inventory_requests=len(requests),original_complete_runtime_budget=budget,
            additional_readiness_seconds_without_old_credit=15,predicted_complete_seconds_with_readiness=total,declared_cost_nominal_fits600=total<600,
            declared_scope_base_pin=previous['declared_scope_base_pin'],prior_parent_connection_pin=PARENT_PROOF,
            new_physical73_proof_pin=PHYSICAL_PROOF,code_manifest_pin=fixture_pin,full_scope_manifest_duplicated=False,
            actual_engine_worker_calls=engine.state.calls)
        require(total<600,'DECLARED_SCOPE_PLUS_READINESS_OUTSIDE600')
        phase='FINAL_METADATA_HASHES';q.finish();guard.check(force=True);require(not denied,'NO_SUBPROCESS_ATTEMPTS')
        row.update(state='PASS_LEGACY154_FULL73_BINDING10_AND_DECLARED_COST_NOT_WORKER_OR_NATIVE',
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError) as error:
        row['error_type']=type(error).__name__;row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None))
    require(guard.cleanup,'OWNER_CLEANUP');libs.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','semantic_inputs','physical_inputs','physical_bytes',
        'current_Rust_path_count','inventory_requests','predicted_complete_seconds_with_readiness','fresh_inputs','final_fresh_hashes','actual_engine_worker_calls',
        'elapsed_seconds','CPU_max','owned_CPU_machine_max','owned_private_MiB_max','RAM_min','cleanup_confirmed','operation_phase','error_code','error_frames')},allow_nan=False))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
