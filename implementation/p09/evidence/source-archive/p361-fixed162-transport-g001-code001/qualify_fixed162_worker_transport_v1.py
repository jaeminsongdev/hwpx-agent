"""Fresh fixed162 bootstrap/constructor/current-wire checks, no worker process.

Whole prior3297 declaration/cost is reconstructed before adding current sources.
The original Native009 file is a failed input, never a reusable execution grant.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

SELF='tools/p09/qualify_fixed162_worker_transport_v1.py'
TEST='tools/p09/tests/test_fixed162_worker_transport_v1.py'
LIBRARY='tools/p09/fixed162_worker_transport_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
BUILDER=dict(path='tools/p09/qualify_native009_failure_binding_v1.py',bytes=15143,
    sha256='2643f3b0966ed170c74435fa6f69ecaf26547805bbe42fbdce45ee9e35ccf038')
PRIOR=dict(path=PREFIX+'fixed162-binary-packet-probe002.v1.json',bytes=50167,
    sha256='db92516020d18b7caebbac0781b3915041654e6ddc24543deb2f1d16a0c27551')
CONSTRUCTION=dict(path='tools/p09/native009_full72_construction_v1.py',bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')


def require(ok,label):
    if not ok: raise ValueError('QUALIFY_FIXED162_WORKER_'+label)


def main():
    import argparse,importlib.util,io,os,re,time,traceback,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows(); denied=[]
    def audit(event,args):
        if event=='subprocess.Popen': denied.append(1); raise ValueError('FIXED162_TRANSPORT_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(audit)
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    originals,_=envelope.namespace_bundle.load(c.ROOT,[CONSTRUCTION],{}); construction=originals.native009_full72_construction_v1
    libs,_=envelope.namespace_bundle.load(c.ROOT,construction.PINS,{})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader,_=libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle,libs.ast_clone_namespace_v1)
    loader,_=construction.private_runtime_imports(loader)
    parser=argparse.ArgumentParser(); parser.add_argument('--generation',type=int,default=1); parser.add_argument('--attempt',type=int,required=True)
    args=parser.parse_args(); require(all(type(v) is int and 1<=v<=8 for v in (args.generation,args.attempt)),'FINITE_GENERATION_AND_ATTEMPT')
    output=PREFIX+f'fixed162-worker-transport-g{args.generation:03}-code{args.attempt:03}.v1.json'
    manifest_name=PREFIX+f'successor-fixed162-manifest-g{args.generation:03}.v1.json'
    version=args.generation+5
    wire_name=PREFIX+f'successor-worker-capsule009.compact.v{version}.json'
    hint_name=PREFIX+f'successor-worker-bootstrap009.v{version}.json'
    require(not(c.ROOT/output).exists(),'EXCLUSIVE_QUALIFIER_RESULT')
    guard=libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started=time.monotonic(); q=None; phase='ADMISSION'; observed=dict(active=False,JSON_file_opens=0)
    row=dict(state='FAILED_FIXED162_WORKER_TRANSPORT_NOT_ADOPTED',accepted_count_delta=0,GO_authorized=False,
        Native009_replayed=False,worker_process_engine_Job_Frame_or_Native_executed=False,
        current_full_runtime_scope_or_helper64_qualified=False,actual_metadata_Frame_shared_decoder5_qualified=False,
        original_limits_or_preparation_CPU_policy_changed=False,current_result_and_future_sources_must_be_recosted=True)
    try:
        guard.acquire(); q=a.AcceptanceReader(c.ROOT,guard.check)
        for path in (SELF,LIBRARY,TEST): q.pin(path)
        prior=a.read_exact(q,PRIOR)
        a.fields(prior,dict(state='PASS_FIXED162_BINARY_WIRE18_AND_FULL_COST_NOT_RECONSTRUCTION_OR_NATIVE',
            contracts=dict(run=18,errors=0,failures=0,skipped=0),fresh_inputs=178,final_fresh_hashes=178,
            actual_original_worker_capsule_decoder_exercised=True,wire_counts=dict(fits_wire=True),cleanup_confirmed=True),'REAL_ALL162_DECODER_NOT_BINARY001_SIZE_REJECTION')
        for pin in prior['source_pins']:
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'): a.exact(q.pin(pin['path']),pin,'ALL_CURRENT_QUALIFIED_PREDECESSOR_PROGRAMS')
        a.exact(q.pin(BUILDER['path']),BUILDER,'UNMODIFIED_ROLE_BUILDER_NOT_FAILED_CODE_PROMOTION')
        builders,_=loader.load(c.ROOT,[BUILDER],{}); builder=builders.qualify_native009_failure_binding_v1
        value=builder.build(c,a,q,loader,libs,construction,scope,bytes_policy,envelope)
        module=value.module; rows=value.proof.rows
        baseline=module.Binding(rows,prior['manifest_pin'],next_case=165)
        inherited,_=baseline.semantic_union(scope.extend(value.prior_scope,scope.pins(prior['source_pins'])),guard.check)
        a.exact(len(inherited),prior['declared_semantic_inputs'],'WHOLE_PREVIOUS3297_NOT_FRESH178_SUBSET')
        old_cost=baseline.runtime_budget(inherited,prior['inventory_requests'],value.window.DIRECT.runtime_budget,guard.check)
        a.exact(old_cost,prior['complete_prototype_runtime_budget'],'WHOLE_PREVIOUS_COST_EXACT')
        names,_=loader.load(c.ROOT,[q.snapshots[LIBRARY]],{}); transport=names.fixed162_worker_transport_v1
        for pin in transport.PINS: a.exact(q.pin(pin['path']),pin,'ALL_CURRENT_TRANSPORT_AND_FIXED_DECLARATION_SOURCES')
        api=transport.connect(c.ROOT,loader,scope,bytes_policy,libs.receipt_xz_envelope_v1,
            libs.bounded_successor_capsule_wire_v2,guard.check,a.exact,version=version)
        a.exact(api.data,value.catalog.declaration(),'SOURCE_MODULE_EQUALS_FRESH_PARENT_ADMITTED_HISTORY')
        publisher_name='tools/p09/native009_parent_scope_v1.py'; publisher_pin=q.pin(publisher_name)
        publishers,_=loader.load(c.ROOT,[publisher_pin],{}); publisher=publishers.native009_parent_scope_v1
        old_hint=q.json(PREFIX+'successor-worker-bootstrap009.v5.json'); step=old_hint['step']
        authority=a.read_exact(q,step['prior_queue_pin'])
        a.fields(authority,dict(accepted_count_after=158,next_runtime_index=165,runtime_candidate_pin=step['prior_candidate_pin']),'CURRENT_UNADVANCED_AUTHORITY')
        phase='PUBLISH_COMPLETE_MANIFEST_AND_UNCHANGED_BOUND16K_FILES'
        manifest=dict(schema_version='hwpx-agent.p09-fixed162-successor-manifest/v1',descriptors=rows,
            legacy_history_declaration_module_pin=transport.DATA,native009_post_body_shared720_failure_provenance=value.role,
            source_step=step,Native_or_worker_process_or_GO_qualified=False)
        encoded=lambda row:(json.dumps(row,ensure_ascii=True,sort_keys=True,allow_nan=False,separators=(',',':'))+'\n').encode('ascii')
        manifest_pin=publisher.publish_bytes(c.ROOT,manifest_name,encoded(manifest),q,guard,bytes_policy,a,262144)
        bound=module.Binding(rows,manifest_pin,next_case=165)
        graph,_=api.metadata.connect(c.ROOT,loader,bytes_policy,module,bound,step,9,guard.check)
        graph.worker,wire_proof=api.binary.connect(graph.worker,guard.check)
        wire,_=graph.worker.encode(bound,step['prior_queue_pin'],step['prior_candidate_pin'],guard.check)
        wire_pin=publisher.publish_bytes(c.ROOT,wire_name,wire,q,guard,bytes_policy,a,16384)
        hint=dict(copy.deepcopy(old_hint),manifest_pin=manifest_pin,capsule_pin=wire_pin,
            **{transport.MODULE_FIELD:transport.DATA,transport.FAILURE_FIELD:value.role})
        hint_pin=publisher.publish_bytes(c.ROOT,hint_name,transport.bootstrap_bytes(hint),q,guard,bytes_policy,a,16384)
        # Read the actual new files through the bounded original reader, not
        # merely the encoder's in-memory values or an expected payload.
        pin,buffer=q._read(wire_name,parse=True); q._bind(pin['path'],pin); a.exact(pin,wire_pin,'ACTUAL_PUBLISHED_WIRE_BYTES')
        wire=bytes(buffer); del buffer; hint=a.read_exact(q,hint_pin)
        phase='ORIGINAL75_CONSTRUCTION_AND_ACTUAL162_RECONSTRUCTION'
        def track(event,args):
            if observed['active'] and event=='open' and args and isinstance(args[0],str) and args[0].lower().endswith('.json'):
                observed['JSON_file_opens']+=1
        sys.addaudithook(track); observed['active']=True
        try: rebuilt,proof=api.reconstruct(hint,wire,guard.check)
        finally: observed['active']=False
        a.exact(rebuilt.binding.descriptors(),rows,'WHOLE_ACTUAL162_GRAPH')
        a.exact(observed['JSON_file_opens'],0,'NO_MANIFEST_OR_RECEIPT_OR_ORIGINAL_JSON_OPEN_IN_RECONSTRUCTION')
        phase='CURRENT_TRANSPORT_CONTRACTS'
        spec=importlib.util.spec_from_file_location('fixed162_transport_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
        tests.M=transport; tests.API=api; tests.HINT=hint; tests.WIRE=wire; tests.ROWS=rows; tests.CHECK=guard.check
        tests.GRAPH=rebuilt; tests.PROOF=proof; tests.OBSERVED=observed
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=16,errors=0,failures=0,skipped=0),'ALL16_CURRENT_BOOTSTRAP_AND_RECONSTRUCTION_CONTRACTS')
        phase='COMPLETE_CURRENT_DECLARATION_AND_ORIGINAL600_720_MODELS'
        model_name='tools/p09/whole_runtime_metadata_budget_v1.py'; model_pin=q.pin(model_name)
        models,_=loader.load(c.ROOT,[model_pin],{})
        inventory=a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'),('rust_inputs',),dict(os=os,Path=Path,require=require))
        requests=[]
        def paced(): requests.append(1); q.open_pacer.reserve()
        rust=inventory.rust_inputs(c.ROOT,paced); require(len(rust)==787,'CURRENT_RUST787')
        required,_=rebuilt.binding.semantic_union(scope.extend(inherited,q.snapshots),guard.check)
        require(all(required.get(n)==p for n,p in inherited.items()) and set(rust)<=set(required),'ALL3297_AND_CURRENT_RUST_RETAINED')
        cost=rebuilt.binding.runtime_budget(required,len(requests),value.window.DIRECT.runtime_budget,guard.check)
        row.update(descriptor_count=162,manifest_pin=manifest_pin,wire_pin=wire_pin,bootstrap_pin=hint_pin,
            data_source_module_pin=transport.DATA,wire_connection_proof=wire_proof,reconstruction_proof=proof,
            inherited_semantic_inputs=len(inherited),declared_semantic_inputs=len(required),inventory_requests=len(requests),
            complete_prototype_runtime_budget=cost,whole720_necessary_model=models.whole_runtime_metadata_budget_v1.assess(cost),
            all_prior_semantic_pins_retained=True,current_Rust_path_count=len(rust),prior_probe_pin=PRIOR,
            reconstruction_JSON_file_opens=observed['JSON_file_opens'],original_suffix_slot_proof=api.suffix_proof,
            internal75_constructor_packet_not_actual_external_transport=True,original75_reconstruction_body_unchanged=True,
            actual_current162_original_decoder_completed=True,parent_source_admission_not_granted_to_worker=True)
        phase='FINAL_FRESH_HASHES'; q.finish(); guard.check(force=True)
        row.update(state='PASS_FIXED162_BOUNDED_BOOTSTRAP_AND_ORIGINAL_RECONSTRUCTION16_NOT_WORKER_PROCESS_OR_NATIVE',
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError) as error:
        row['error_type']=type(error).__name__
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-7:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]): row['error_code']=error.args[0]
    finally:
        observed['active']=False
        if q is not None: row.update(observed_inputs=len(q.snapshots),closing_hashes_completed=q.final_fresh_hashes)
        guard.close(); row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None),subprocess_creation_attempts=len(denied))
    require(guard.cleanup,'QUALIFIER_OWNER_CLEANUP'); libs.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','wire_pin','bootstrap_pin','declared_semantic_inputs',
        'whole720_necessary_model','fresh_inputs','final_fresh_hashes','reconstruction_JSON_file_opens','elapsed_seconds',
        'CPU_max','owned_CPU_machine_max','owned_private_MiB_max','RAM_min','cleanup_confirmed','operation_phase','error_code','error_frames')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__': raise SystemExit(main())
