"""Exact two historical failed-validation aliases after complete70.

Execute original70, then the entire unchanged raw72 constructor. Preserve all
nonconstructor and Projection oracles. CODE/cost planning only, never dispatch.
"""
import copy
import hashlib
import json
import sys
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/legacy_validation_binding_v1.py'
TEST='tools/p09/tests/test_legacy_validation_binding_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
FULL72=dict(path=PREFIX+'legacy2-full72-physical-g001-attempt002.v1.json',bytes=92822,
    sha256='476b5a8efdc79d0e629e2c2d35d7ccc79a10eddeeb20a6ab8afbf1d649c69787')
CODE70=dict(path=PREFIX+'native007-binding-code001.v1.json',bytes=19953,
    sha256='c449af1f26697141b67acb8a7becec3ea2754d3d32048bd664e164a52a06fc4b')
TABLE70='a87ef61d635219f7cddc4cdcab0eb923f7e7e4fe598120b40bd8156cab5b9bcf'
RECORDS=[
 dict(key='p159-full249',original=dict(path='implementation/p09/evidence/p09-159-current-graph-full.actual-run01.v1.json',bytes=3959557,
    sha256='70d755fb99fa2ae5f2776d613d52123cdc9fed4e63860e5ed71d593ba6b9784e'),physical=dict(
    path='implementation/p09/evidence/p361-lossless-runtime-inputs/legacy-p159-full249.actual-run01.failed.duration.xz8m-g001.envelope.v1.json',
    bytes=281526,sha256='6c03182776dcf66dc22adca274a2c35a16c84b2af5ede75bbc71d336d6ac204b')),
 dict(key='p165-adaptive-full249',original=dict(path='implementation/p09/evidence/p09-165-adaptive-source-xml-full.actual-run01.v1.json',bytes=3939320,
    sha256='cdeb4115b293a61d17948700471c4cc4c137d887e260353c8c4ee73a19c3e9a9'),physical=dict(
    path='implementation/p09/evidence/p361-lossless-runtime-inputs/legacy-p165-adaptive-full249.actual-run01.failed.duration.xz8m-g001.envelope.v1.json',
    bytes=274394,sha256='fe40ec53d44c1ff05d927d9a6ddf20465788228877f502422b8008d0a5cc99ac'))]
for _r in RECORDS:_r.update(source_role='historical_validation_worker_and_writer_started_duration_stop_not_accepted',
    original_failure_promoted=False,product_child_execution_asserted=False)
ROLE=dict(schema_version='hwpx-agent.p09-exact-legacy-validation-aliases/v1',current_case=165,successor_physical_run=9,
    records=RECORDS,physical_verification_pin=FULL72,current_product_or_GO_qualified=False)


def require(ok,label):
    if not ok:raise ValueError('LEGACY_VALIDATION_BINDING_'+label)


def fingerprint(rows):
    return hashlib.sha256(json.dumps(rows,ensure_ascii=True,sort_keys=True,allow_nan=False,separators=(',',':')).encode('ascii')).hexdigest()


def admission(q,a):
    proof=a.read_exact(q,FULL72)
    a.fields(proof,dict(state='PASS_LEGACY2_FULL72_PHYSICAL_NOT_BINDING_WORKER_OR_NATIVE',contracts=dict(run=10,errors=0,failures=0,skipped=0),
        pair_count=72,decode_count=144,fresh_inputs=173,final_fresh_hashes=173,cleanup_confirmed=True,
        accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False,
        original_overwritten_or_deleted=False,prior70_mapping_or_descriptor_policy_changed=False),'EXACT_FULL72_PROOF')
    a.exact(proof['records'],RECORDS,'EXACT_TWO_OPAQUE_FAILURES')
    require(fingerprint(proof['full70_descriptors'])==TABLE70,'FULL_PRIOR70_TABLE')
    a.fields(proof['decoder_budget'],dict(aggregate_limit_seconds=5.0,attempted_decodes=144,completed_decodes=144,
        active_decode=False,terminal_error_seen=False,two_boundaries_share_one_budget=True),'ALL144_SHARED5')
    require(type(proof['decoder_budget']['elapsed_decoder_work_seconds']) is float
        and 0<=proof['decoder_budget']['elapsed_decoder_work_seconds']<5,'ACTUAL_DECODER_WITHIN5')
    for pin in proof['source_pins']:
        if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):a.exact(q.pin(pin['path']),pin,'CURRENT_PHYSICAL_PROOF_PROGRAMS')
    for r in RECORDS:a.exact(q.pin(r['physical']['path']),r['physical'],'CURRENT_PHYSICAL_CARRIER_PIN')
    return copy.deepcopy(ROLE),proof


def install(module,prior_rows,admitted,xz,*,physical_run):
    require(type(physical_run) is int and physical_run==9,'EXACT_RUN9')
    require(type(module) is NS and type(getattr(module,'source',None)) is NS,'PRIVATE_MODULE')
    module.exact(admitted,ROLE,'EXACT_TYPED_HISTORICAL_FAILURE_ROLES')
    require(type(prior_rows) is list and len(prior_rows)==70 and fingerprint(prior_rows)==TABLE70,'ALL_FIXED_PRIOR70')
    require(hasattr(module,'native007_failure_alias') and hasattr(module,'native008_failure_alias')
        and not hasattr(module,'legacy_validation_aliases'),'ONE_INSTALL_AFTER007_AND008')
    source=module.source;env=source.Projection.__init__.__globals__
    require(env.get('__name__','').startswith('p09_exact_') and env.get('descriptor') is source.descriptor
        and not any(getattr(m,'__dict__',None) is env for m in tuple(sys.modules.values()) if m),'PRIVATE_GRAPH_NOT_DEFAULT')
    old_init=module.Binding.__init__;raw_init=module.xz_original_initialize
    require(type(raw_init) is FunctionType and raw_init.__code__.co_filename.replace('\\','/').endswith('runtime_envelope_scope_binding_v1.py'),'WHOLE_RAW_CONSTRUCTOR')
    old_descriptor=source.descriptor;old_codec=source.codec;old_representation=module.Binding.representation
    methods={k:v for k,v in vars(module.Binding).items() if k not in ('__init__','representation')};projection=dict(vars(source.Projection))
    prior=copy.deepcopy(prior_rows);provenance=copy.deepcopy(admitted)
    pairs=[dict(schema_version=source.SCHEMA,next_case=165,semantic_original_pin=copy.deepcopy(r['original']),
        physical_envelope_pin=copy.deepcopy(r['physical'])) for r in RECORDS]
    by_name={p['semantic_original_pin']['path']:p for p in pairs};physical_hashes={r['physical']['sha256'] for r in RECORDS}
    complete=prior+pairs;state=dict(ready=False)
    def descriptor(old,new,*,next_case):
        if type(old) is not dict or old.get('path') not in by_name:return old_descriptor(old,new,next_case=next_case)
        require(type(next_case) is int and next_case==165,'EXACT_CASE165')
        expected=by_name[old['path']]
        module.exact(source.copy_pin(old),expected['semantic_original_pin'],'EXACT_LEGACY_ORIGINAL')
        module.exact(source.copy_pin(new),expected['physical_envelope_pin'],'EXACT_LEGACY_CARRIER');return copy.deepcopy(expected)
    def initialize(self,rows,manifest_pin,*,next_case):
        state['ready']=False;module.exact(rows,complete,'EXACT70_PLUS_TWO_LEGACY')
        require(type(next_case) is int and next_case==165,'FULL72_CURRENT_CASE')
        old_init(self,rows[:70],manifest_pin,next_case=next_case)
        module.exact(self.descriptors(),prior,'ENTIRE_ORIGINAL70_CONSTRUCTOR_COMPLETED')
        raw_init(self,rows,manifest_pin,next_case=next_case)
        module.exact(self.descriptors(),complete,'WHOLE_RAW72_CONSTRUCTOR_COMPLETED');state['ready']=True
    def decode(encoded,checkpoint):
        checkpoint();require(type(encoded) is bytes and 0<len(encoded)<=xz.MAX_BYTES,'FRESH_BOUNDED_CODEC_INPUT')
        if hashlib.sha256(encoded).hexdigest() in physical_hashes:
            require(state['ready'],'FULL72_CONSTRUCTOR_BEFORE_LEGACY_DECODE');return xz.decode(encoded,checkpoint)
        return old_codec.decode(encoded,checkpoint)
    def representation(self,projection):
        require(all(r['original']['path'] in self.originals for r in RECORDS),'BOTH_EXPLICIT_ORIGINALS')
        row=old_representation(self,projection);row['historical_validation_failures_provenance']=copy.deepcopy(provenance);return row
    source.descriptor=descriptor;env['descriptor']=descriptor
    source.codec=NS(**{**vars(old_codec),'decode':decode});env['codec']=source.codec
    module.Binding.__init__=initialize;module.Binding.representation=representation
    module.legacy_validation_aliases=copy.deepcopy(provenance)
    require(all(vars(module.Binding).get(k) is v for k,v in methods.items()),'ALL_NONCONSTRUCTOR_ORACLES_RETAINED')
    require(all(vars(source.Projection).get(k) is v for k,v in projection.items()),'ALL_PROJECTION_METHODS_RETAINED')
    return dict(entire_original70_before_whole_raw72=True,original_nonconstructor_and_Projection_methods_retained=True,
        historical_failures_not_promoted_or_relabelled_prebody=True,Native_or_GO_authorized=False)


def main():
    import argparse,importlib.util,io,os,re,time,unittest
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
    import native009_worker_transport_v1 as transport
    import native009_parent_scope_v1 as parent
    import native009_engine_connection_v1 as engine
    import native007_failure_binding_v1 as failed7
    import prepare_native007_carrier_v1 as producer
    import flat_current_queue_product_window_runtime_v18 as original_window
    import post_product_recovery_window_v1 as window_tool
    import post_product_recovery_connection_v1 as recovery
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    attempt=producer.identifier(parser.parse_args().attempt);output=PREFIX+f'legacy2-binding-code{attempt:03}.v1.json'
    require(not(c.ROOT/output).exists(),'EXCLUSIVE_CODE_REPORT')
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))();started=time.monotonic();phase='ADMISSION'
    row=dict(state='FAILED_LEGACY2_BINDING_NOT_ADOPTED',accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False,
        full72_worker_transport_or_current_Native_scope_qualified=False,current_complete_Native_budget_qualified=False,
        additional_qualification_dispatch_and_result_sources_must_be_recosted=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF);q.pin(TEST)
        admitted,physical_proof=admission(q,a);previous=a.read_exact(q,CODE70)
        a.fields(previous,dict(state='PASS_NATIVE007_FULL70_BINDING_CODE9_NOT_WORKER_OR_NATIVE',contracts=dict(run=9,errors=0,failures=0,skipped=0),
            fresh_inputs=104,final_fresh_hashes=104,cleanup_confirmed=True),'EXACT_PREVIOUS70_CODE')
        for pin in previous['source_pins']:
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):a.exact(q.pin(pin['path']),pin,'CURRENT_PRIOR_CODE_PROGRAMS')
        old_admitted=failed7.admission(q,a)
        loader,_=optimization.connect(envelope.namespace_bundle,cloner)
        api=transport.connect(c.ROOT,loader,scope,bytes_policy,xz,bounded,guard.check,a.exact);parent.version2(api,transport)
        sources=scope.pins(previous['source_pins']);hint=a.read_exact(q,sources[parent.BOOTSTRAP])
        pin,data=q._read(hint['capsule_pin']['path'],parse=True);q._bind(pin['path'],pin);a.exact(pin,hint['capsule_pin'],'CURRENT69_WIRE')
        graph,_=api.reconstruct(hint,bytes(data),guard.check);del data
        # Compose only the qualified69 engine to obtain its original complete
        # cost function. No execute/worker call and no fake72 transport claim.
        a.exact(q.pin(window_tool.WINDOW_PIN['path']),window_tool.WINDOW_PIN,'CURRENT_WINDOW_TOOL')
        linked=engine.build(c.ROOT,loader,api,graph,original_window,recovery,window_tool,guard.check)
        module=graph.binding_module;prior69=graph.binding.descriptors()
        failed7.install(module,prior69,old_admitted,xz,physical_run=9)
        prior70=copy.deepcopy(prior69)+[dict(schema_version=module.source.SCHEMA,next_case=165,
            semantic_original_pin=copy.deepcopy(failed7.ORIGINAL),physical_envelope_pin=copy.deepcopy(failed7.PHYSICAL))]
        a.exact(prior70,physical_proof['full70_descriptors'],'SAME_CURRENT70_AND_PHYSICAL_PROOF')
        methods={k:v for k,v in vars(module.Binding).items() if k not in ('__init__','representation')};projections=dict(vars(module.source.Projection))
        row['installation_proof']=install(module,prior70,admitted,xz,physical_run=9)
        rows=prior70+[dict(schema_version=module.source.SCHEMA,next_case=165,semantic_original_pin=copy.deepcopy(r['original']),
            physical_envelope_pin=copy.deepcopy(r['physical'])) for r in RECORDS]
        fixture=dict(schema_version='hwpx-agent.p09-full72-binding-code-fixture/v1',descriptors=rows,Native_graph_or_worker_packet_qualified=False)
        name=PREFIX+f'legacy2-binding-code-manifest{attempt:03}.v1.json'
        fixture_pin=parent.publish_bytes(c.ROOT,name,(json.dumps(fixture,ensure_ascii=True,indent=2)+'\n').encode('ascii'),q,guard,bytes_policy,a,262144)
        encoded=[]
        for r in RECORDS:
            pin,buffer=q._read(r['physical']['path'],parse=True);a.exact(pin,r['physical'],'ACTUAL_LEGACY_CARRIER_FOR_CODE')
            encoded.append(bytes(buffer))
            try:module.source.codec.decode(encoded[-1],guard.check)
            except ValueError as error:require(error.args==('LEGACY_VALIDATION_BINDING_FULL72_CONSTRUCTOR_BEFORE_LEGACY_DECODE',),'EXACT_UNCONSTRUCTED_DENIAL')
            else:require(False,'UNCONSTRUCTED_DECODE_DENIED')
        phase='CODE_CONTRACTS'
        spec=importlib.util.spec_from_file_location('legacy_binding_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        tests.MODULE=sys.modules[__name__];tests.BINDING=module;tests.ROWS=rows;tests.PIN=fixture_pin;tests.SCOPE=scope;tests.CHECK=guard.check
        tests.CARRIERS=encoded;tests.METHODS=methods;tests.PROJECTION=projections;tests.PRIOR=prior70;tests.XZ=xz
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=11,errors=0,failures=0,skipped=0),'ALL_BINDING11')
        for loaded in tuple(sys.modules.values()):
            filename=getattr(loaded,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        phase='DECLARED_COMPLETE_COST'
        plan=q.json(PREFIX+'native009-parent-plan003.v1.json')
        a.fields(plan,dict(state='FAILED_NATIVE009_PARENT_PLAN_NOT_NATIVE',cleanup_confirmed=True,
            error_code='NATIVE009_PARENT_SCOPE_COMPLETE_SCOPE_PLUS_READINESS_OUTSIDE600',current_Rust_path_count=787,inventory_requests=167),'UNCHANGED_PREVIOUS_SCOPE_DECLARATION_ONLY')
        declaration=a.read_exact(q,plan['scope_declaration_pin'])
        required=scope.pins(declaration['input_pins']);base=copy.deepcopy(required)
        for extra in (previous['source_pins'],physical_proof['source_pins']):required=scope.extend(required,scope.pins(extra))
        required=scope.extend(required,q.snapshots)
        bound=module.Binding(rows,fixture_pin,next_case=165);required,_=bound.semantic_union(required,guard.check)
        require(all(required.get(n)==p for n,p in base.items()),'NO_PREVIOUS_DECLARED_INPUT_REMOVED')
        listing=a.read_exact(q,scope.LIST_PIN);current=scope.listing_inputs(listing)
        rust={n for n in current if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/')) and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==787,'EXACT_DECLARED_RUST787')
        inventory=a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'),('rust_inputs',),dict(os=os,Path=Path,require=require))
        requests=[]
        def paced():requests.append(1);q.open_pacer.reserve()
        a.exact(inventory.rust_inputs(c.ROOT,paced),rust,'CURRENT_RUST787_PATH_SET')
        required=scope.extend(required,q.snapshots);required,_=bound.semantic_union(required,guard.check)
        source_name=PREFIX+f'legacy2-declared-scope{attempt:03}.v1.json'
        source_row=dict(schema_version='hwpx-agent.p09-legacy2-complete-declared-inputs/v1',input_pins=sorted(required.values(),key=lambda p:p['path']),
            current_live_input_hashes_or_Frame_qualified=False,self_pin_added_separately_after_publication=True)
        scope_pin=parent.publish_bytes(c.ROOT,source_name,(json.dumps(source_row,ensure_ascii=True,indent=2)+'\n').encode('ascii'),q,guard,bytes_policy,a,2*1024*1024)
        required=scope.extend(required,{scope_pin['path']:scope_pin});projected,_=bound.project(required,guard.check)
        budget=bound.runtime_budget(required,len(requests),linked.window.DIRECT.runtime_budget,guard.check)
        total=budget['predicted_runtime_combined_seconds']+15
        row.update(manifest_pin=fixture_pin,scope_declaration_pin=scope_pin,original_complete_runtime_budget=budget,
            additional_readiness_seconds_without_old_allowance_credit=15,predicted_complete_seconds_with_readiness=total,
            declared_cost_nominal_fits600=total<600,semantic_inputs=len(required),physical_inputs=len(projected.physical_pins),
            physical_bytes=sum(p['bytes'] for p in projected.physical_pins.values()),current_Rust_path_count=len(rust),inventory_requests=len(requests),
            all_previous_declared_inputs_preserved=True,full_declared_input_hashes_not_freshly_read=True,
            actual_engine_worker_calls=linked.state.calls,whole_scope_native_helper64_NOT_RUN=True)
        phase='FINAL_METADATA_HASHES';q.finish();guard.check(force=True)
        row.update(state='PASS_LEGACY2_FULL72_BINDING11_AND_DECLARED_COST_NOT_WORKER_OR_NATIVE',source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,one_private_module_reused_for_contracts=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        import traceback
        row['error_type']=type(error).__name__;row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-5:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None))
    require(guard.cleanup,'OWNER_CLEANUP');publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','semantic_inputs','physical_inputs','physical_bytes','current_Rust_path_count',
        'inventory_requests','predicted_complete_seconds_with_readiness','declared_cost_nominal_fits600','fresh_inputs','final_fresh_hashes',
        'elapsed_seconds','CPU_max','owned_CPU_machine_max','owned_private_MiB_max','RAM_min','cleanup_confirmed','error_code','error_frames')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
