"""Construct fixed162 and close both physical passes without any engine.

Reuse complete161 declarations, not its small qualifier source-pin subset.
The shared720 model includes the new producer/proofs/diagnostic manifest.
"""
import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

SELF='tools/p09/qualify_native009_failure_binding_v1.py'
LIBRARY='tools/p09/native009_failure_binding_v1.py'
TEST='tools/p09/tests/test_native009_failure_binding_v1.py'
HISTORY='tools/p09/legacy_history_binding_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
CONSTRUCTION=dict(path='tools/p09/native009_full72_construction_v1.py',bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
PHYSICAL=dict(path='tools/p09/runtime_envelope_physical_io_v1.py',bytes=7214,
    sha256='b3bf5637c1f5d13bf9090236274826440e4c6c543b6db219a95b0869919c324c')


def require(ok,label):
    if not ok: raise ValueError('QUALIFY_NATIVE009_FAILURE_'+label)


def build(c,a,q,loader,libs,construction,scope,bytes_policy,envelope):
    """Reusable source/role/Binding construction; no runtime api.build call."""
    q.pin(LIBRARY); modules,_=loader.load(c.ROOT,[q.snapshots[LIBRARY]],{})
    m=modules.native009_failure_binding_v1
    role,prior_code,temporary_native=m.admission(q,a,loader); del temporary_native
    pins=scope.pins(prior_code['source_pins'])
    for path in (HISTORY,'tools/p09/legacy149_binding_v1.py','tools/p09/native009_full75_worker_entry_v1.py'):
        a.exact(q.pin(path),pins[path],'CURRENT_FIXED161_PROGRAMS')
    modules,_=loader.load(c.ROOT,[pins[HISTORY]],{}); history=modules.legacy_history_binding_v1
    catalog,_,_,native=history.admit(q,a)
    for pin in [CONSTRUCTION]+construction.PINS: a.exact(q.pin(pin['path']),pin,'EXACT_ORIGINAL_FACTORY_PROGRAMS')
    entry_name='tools/p09/native009_full75_worker_entry_v1.py'
    entries,_=loader.load(c.ROOT,[pins[entry_name]],{}); entry=entries.native009_full75_worker_entry_v1
    for pin in (entry.TRANSPORT,entry.HINT,entry.WIRE,entry.STEP): a.exact(q.pin(pin['path']),pin,'FROZEN75_METADATA_NOT_REPLAY')
    transports,_=loader.load(c.ROOT,[entry.TRANSPORT],{})
    api=transports.native009_full75_transport_v1.connect(c.ROOT,loader,scope,bytes_policy,libs.receipt_xz_envelope_v1,
        libs.bounded_successor_capsule_wire_v2,q.checkpoint,a.exact)
    for proof in api.source_proofs: a.exact(q.pin(proof['source_pin']['path']),proof['source_pin'],'ALL_ORIGINAL_PRIVATE_FACTORY_BYTES')
    hint=a.read_exact(q,entry.HINT)
    module=api.factory(hint,copy.deepcopy(catalog.prior()[:68]))
    history_proof=history.install(module,catalog,libs.receipt_xz_envelope_v1,mode='parent')
    a.exact(history.fingerprint(catalog.rows()),m.TABLE161,'COMPLETE_CURRENT161_NOT_SOURCE_SUBSET')
    before=module.Binding(catalog.rows(),prior_code['current_manifest_pin'],next_case=165)
    semantic=scope.pins(native['source_input_representation']['semantic_source_freeze'])
    prior_scope,_=before.semantic_union(scope.extend(semantic,scope.pins(prior_code['source_pins'])),q.checkpoint)
    a.exact(len(prior_scope),prior_code['declared_semantic_inputs'],'REPLAY_ALL3280_DECLARED_INPUTS')
    window,_=libs.post_product_recovery_connection_v1.current_window(envelope.prior,libs.post_product_recovery_window_v1,
        q.text(libs.post_product_recovery_window_v1.WINDOW_PIN['path']).encode('utf-8'))
    old_model=before.runtime_budget(prior_scope,prior_code['inventory_requests'],window.DIRECT.runtime_budget,q.checkpoint)
    a.exact(old_model,prior_code['complete_prototype_runtime_budget'],'ENTIRE_PRIOR161_COST_EXACT')
    proof=m.install(module,catalog.rows(),role,libs.receipt_xz_envelope_v1)
    return NS(m=m,history=history,catalog=catalog,module=module,proof=proof,history_proof=history_proof,
        native=native,prior_code=prior_code,prior_scope=prior_scope,semantic=semantic,window=window,role=role)


def main():
    import argparse,importlib.util,io,os,re,time,traceback,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    denied=[]
    def audit(event,args):
        if event=='subprocess.Popen': denied.append(1); raise ValueError('NATIVE009_BINDING_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(audit)
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import audit_evidence_io as original_io
    bootstrap,_=envelope.namespace_bundle.load(c.ROOT,[CONSTRUCTION],{})
    construction=bootstrap.native009_full72_construction_v1
    libs,_=envelope.namespace_bundle.load(c.ROOT,construction.PINS,{})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader,_=libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle,libs.ast_clone_namespace_v1)
    loader,_=construction.private_runtime_imports(loader)
    parser=argparse.ArgumentParser(); parser.add_argument('--attempt',type=int,required=True)
    attempt=parser.parse_args().attempt; require(type(attempt) is int and 1<=attempt<=8,'FINITE_ATTEMPT')
    output=PREFIX+f'native009-failure-binding-code{attempt:03}.v1.json'
    manifest_name=PREFIX+f'native009-failure-binding-manifest{attempt:03}.v1.json'
    require(not(c.ROOT/output).exists() and not(c.ROOT/manifest_name).exists(),'EXCLUSIVE_DIAGNOSTIC_ONLY')
    guard=libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started=time.monotonic(); q=budget=None; phase='ADMISSION'
    row=dict(state='FAILED_NATIVE009_FAILURE162_BINDING_NOT_ADOPTED',accepted_count_delta=0,GO_authorized=False,
        Native009_replayed=False,actual_worker_engine_Job_Frame_or_Native_executed=False,
        full_current_runtime_scope_or_helper_bound_qualified=False,actual_metadata_Frame_shared_decoder5_qualified=False,
        worker_transport_or_dispatch_qualified=False,current_result_and_future_sources_must_be_recosted=True,
        preparation_CPU_policy_changed=False,product_execution_or_replay_authorized=False)
    try:
        guard.acquire(); seed=a.AcceptanceReader(c.ROOT,guard.check)
        for path in (SELF,LIBRARY,TEST): seed.pin(path)
        names,_=loader.load(c.ROOT,[seed.snapshots[LIBRARY]],{}); m=names.native009_failure_binding_v1
        previous=a.read_exact(seed,m.PRIOR_CODE); saved=scope.pins(previous['source_pins'])
        name='tools/p09/legacy149_binding_v1.py'; a.exact(seed.pin(name),saved[name],'EXACT_EXISTING_READER_HELPER')
        helpers,_=loader.load(c.ROOT,[saved[name]],{}); reader=helpers.legacy149_binding_v1
        for p in (reader.SNAPSHOT,reader.CHUNK): a.exact(seed.pin(p['path']),p,'FIXED_SINGLE_SNAPSHOT_AND_REUSABLE_CHUNK')
        readers,_=loader.load(c.ROOT,[reader.SNAPSHOT,reader.CHUNK],{'audit_evidence_io':original_io})
        snapshot,chunk=readers.single_snapshot_source_guard_v1,readers.reusable_audit_chunk_v1
        p,raw=seed._read(snapshot.ORIGINAL_PIN['path'],parse=True); seed._bind(p['path'],p); a.exact(p,snapshot.ORIGINAL_PIN,'ORIGINAL_SOURCE_PREDICATES')
        Source,_=snapshot.reader_type(a.AcceptanceReader,bytes(raw)); Reader,_=chunk.reader_type(Source,bytes(raw)); del raw
        q=Reader(c.ROOT,guard.check)
        for p in seed.snapshots.values(): a.exact(q.pin(p['path']),p,'FRESH_SEED_PROGRAMS_AND_PROOF')
        phase='WHOLE161_ROLE_AND_NEW_FAILURE162_CONSTRUCTION'
        value=build(c,a,q,loader,libs,construction,scope,bytes_policy,envelope)
        m,module,proof=value.m,value.module,value.proof
        fixture=dict(schema_version='hwpx-agent.p09-failed009-fixed162-binding-diagnostic/v1',descriptors=proof.rows,
            native009_post_body_shared720_failure_provenance=value.role,legacy_history_physical_evidence_provenance=value.catalog.declaration(),
            worker_packet_or_Native_qualified=False,product_execution_or_replay_authorized=False)
        manifest_pin=libs.successor_preparation_workspace_v1.publish(c.ROOT,manifest_name,fixture,a); q.pin(manifest_name)
        p,buffer=q._read(m.PHYSICAL['path'],parse=True); q._bind(p['path'],p); a.exact(p,m.PHYSICAL,'FRESH_NEW009_CODEC_DATA')
        carrier=bytes(buffer); del buffer
        try: module.source.codec.decode(carrier,guard.check)
        except ValueError as error: require(error.args==('NATIVE009_FAILURE_BINDING_ENTIRE162_BEFORE_NEW009_DECODE',),'PRECONSTRUCTOR_NEW009_DENIAL')
        else: require(False,'NEW009_REQUIRES_WHOLE162')
        bound=module.Binding(proof.rows,manifest_pin,next_case=165)
        required,_=bound.semantic_union(scope.extend(value.prior_scope,q.snapshots),guard.check)
        phase='NEW_FAILURE_BINDING_CONTRACTS'
        spec=importlib.util.spec_from_file_location('native009_failure_binding_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
        tests.M=m; tests.MODULE=module; tests.ROWS=proof.rows; tests.PRIOR=value.catalog.rows(); tests.PIN=manifest_pin
        tests.CHECK=guard.check; tests.PROOF=proof; tests.REQUIRED=required; tests.CARRIER=carrier; tests.NATIVE=value.native
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=12,errors=0,failures=0,skipped=0),'FAILURE162_CONTRACTS12')
        bound=module.Binding(proof.rows,manifest_pin,next_case=165); projection,_=bound.project(required,guard.check)
        a.exact(q.pin(PHYSICAL['path']),PHYSICAL,'ORIGINAL_DECODER_BUDGET')
        physical=envelope._namespaces.runtime_envelope_physical_io_v1
        budget=physical.DecoderBudget(guard.check); counts={r['semantic_original_pin']['path']:0 for r in proof.rows}
        phase='ALL162_TWO_FRESH_PHYSICAL_DECODE_PASSES'
        for boundary in ('before','after'):
            for r in proof.rows:
                old,new=r['semantic_original_pin'],r['physical_envelope_pin']
                p,buffer=q._read(new['path'],parse=True); q._bind(p['path'],p); a.exact(p,new,'ALL162_NEW_FRESH_BYTES')
                decoded=budget.run(lambda check:projection.decode_fresh(old['path'],p,bytes(buffer),check)); del buffer,decoded
                counts[old['path']]+=1
        require(budget.attempts==budget.completed==324 and all(n==2 for n in counts.values()),'ENTIRE162_RESTORED_TWICE')
        phase='CURRENT_FULL_DECLARATION_AND600_720_MODELS'
        inventory=a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'),('rust_inputs',),dict(os=os,Path=Path,require=require))
        requests=[]
        def paced(): requests.append(1); q.open_pacer.reserve()
        rust=inventory.rust_inputs(c.ROOT,paced); require(len(rust)==787,'CURRENT_RUST787')
        model_source='tools/p09/whole_runtime_metadata_budget_v1.py'; q.pin(model_source)
        model_ns,_=loader.load(c.ROOT,[q.snapshots[model_source]],{})
        required,_=bound.semantic_union(scope.extend(value.prior_scope,q.snapshots),guard.check)
        require(all(required.get(n)==p for n,p in value.prior_scope.items()) and set(rust)<=set(required),'ALL_PRIOR3280_AND_CURRENT_RUST_PRESERVED')
        cost=bound.runtime_budget(required,len(requests),value.window.DIRECT.runtime_budget,guard.check)
        whole=model_ns.whole_runtime_metadata_budget_v1.assess(cost)
        row.update(descriptor_count=162,entire_prior161_constructor_and_model_preserved=True,
            declared_semantic_inputs=len(required),complete_prototype_runtime_budget=cost,whole720_necessary_model=whole,
            prototype_model_is_not_current_runtime_admission=True,all_prior_semantic_pins_retained=True,
            current_manifest_pin=manifest_pin,prior161_code_pin=m.PRIOR_CODE,native009_carrier_publication_pin=m.PUBLICATION,
            failed_Native009_pin=m.ORIGINAL,failed_Native009_physical_pin=m.PHYSICAL,failed_body_PASS_not_accepted=True,
            inventory_requests=len(requests),current_Rust_path_count=len(rust),decode_counts=counts,decoder_budget=budget.evidence(),
            source_role=value.role,parent_source_admission_completed_without_any_GO=True)
        phase='FINAL_FRESH_HASHES'; q.finish(); guard.check(force=True); require(not denied,'NO_SUBPROCESS_NATIVE_OR_PRODUCT')
        row.update(state='PASS_FIXED162_POST_BODY_FAILURE_BINDING12_AND_TWO_PHYSICAL_PASSES_NOT_WORKER_OR_NATIVE',
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError) as error:
        row['error_type']=type(error).__name__
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-7:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]): row['error_code']=error.args[0]
    finally:
        if budget is not None: row['decoder_budget']=budget.evidence()
        if q is not None: row.update(observed_inputs=len(q.snapshots),closing_hashes_completed=q.final_fresh_hashes,
            actual_read_passes=q.read_passes,actual_physical_read_bytes=q.bytes_read)
        guard.close(); row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None),subprocess_creation_attempts=len(denied))
        row['last_original_resource_samples']=[{k:s.get(k) for k in ('time_utc','system_cpu_percent','parent_cpu_machine_percent','available_ram_percent','commit_used_percent','parent_private_mib')} for s in guard.samples[-8:]]
    require(guard.cleanup,'QUALIFIER_OWNER_CLEANUP'); libs.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','contract_failures','descriptor_count','declared_semantic_inputs','whole720_necessary_model',
        'decoder_budget','fresh_inputs','final_fresh_hashes','elapsed_seconds','CPU_max','owned_CPU_machine_max','owned_private_MiB_max','RAM_min',
        'cleanup_confirmed','operation_phase','error_code','error_frames')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__': raise SystemExit(main())
