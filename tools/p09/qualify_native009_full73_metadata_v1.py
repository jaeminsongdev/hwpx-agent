"""Actual full73 parent metadata admission and closing hashes; no Native entry.

Use the engine's original BuildReader and unchanged live pressure binding.
Register the real shared metadata decoder before any future Frame. Never
substitute a standalone decoder budget, fake Job cleanup or a product receipt.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

SELF='tools/p09/qualify_native009_full73_metadata_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
PARENT_PROOF=dict(path=PREFIX+'native009-full73-parent-connection003.v1.json',bytes=92954,
    sha256='f186ec913c3ce6b7c9703634a0c34859b0f5eac581f447457610d47034268a34')
CONSTRUCTION=dict(path='tools/p09/native009_full72_construction_v1.py',bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
QUALIFIER='tools/p09/qualify_native009_full73_parent_v1.py'
FAILED_METADATA=dict(path=PREFIX+'native009-full73-metadata002.v1.json',bytes=8139,
    sha256='2e75b98d9003635fbe5483a694049aea3641df7ce6cea66564270f200f4e866b')
PUBLICATION_REVIEW=PREFIX+'native009-full73-metadata-publication-review003.v1.json'


def require(ok,label):
    if not ok:raise ValueError('FULL73_METADATA_'+label)


def restore_pin_map(required,record,scope,exact):
    import hashlib
    require(type(record) is dict and set(record)=={'schema_version','omitted_declared_paths','extra_physical_pins','raw_pin_count','raw_pin_map_sha256'},'COMPACT_PIN_MAP_FIELDS')
    require(record['schema_version']=='hwpx-agent.p09-metadata-pin-map-over-declared-scope/v1','COMPACT_PIN_MAP_SCHEMA')
    omitted=record['omitted_declared_paths'];extra=record['extra_physical_pins']
    require(type(omitted) is list and omitted==sorted(set(omitted)) and set(omitted)<=set(required),'EXACT_OMISSION_SET')
    require(type(extra) is list,'COMPACT_EXTRA_PIN_LIST')
    extra={} if not extra else scope.pins(extra)
    require(not(set(extra)&set(required)),'NO_COMPACT_PIN_CONFLICT_OVERRIDE')
    restored={n:dict(p) for n,p in required.items() if n not in omitted}
    restored.update(extra)
    exact(scope.pins(list(restored.values())),restored,'RESTORED_PIN_MAP_SHAPE')
    require(type(record['raw_pin_count']) is int and len(restored)==record['raw_pin_count'],'COMPACT_PIN_COUNT')
    digest=hashlib.sha256(json.dumps(restored,ensure_ascii=True,sort_keys=True,separators=(',',':')).encode('ascii')).hexdigest()
    exact(digest,record['raw_pin_map_sha256'],'COMPACT_PIN_MAP_DIGEST')
    return restored


def compact_pin_map(required,actual,scope,exact):
    import hashlib
    require(type(required) is dict and bool(required) and type(actual) is dict and bool(actual),'NONEMPTY_PIN_MAPS')
    exact(scope.pins(list(required.values())),required,'DECLARED_PIN_MAP_SHAPE')
    exact(scope.pins(list(actual.values())),actual,'ACTUAL_PIN_MAP_SHAPE')
    record=dict(schema_version='hwpx-agent.p09-metadata-pin-map-over-declared-scope/v1',
        omitted_declared_paths=sorted(set(required)-set(actual)),
        extra_physical_pins=sorted((p for n,p in actual.items() if n not in required),key=lambda p:p['path']),
        raw_pin_count=len(actual),raw_pin_map_sha256=hashlib.sha256(json.dumps(actual,ensure_ascii=True,
            sort_keys=True,separators=(',',':')).encode('ascii')).hexdigest())
    exact(restore_pin_map(required,record,scope,exact),actual,'WHOLE_ACTUAL_PIN_MAP_LOSSLESS_ROUNDTRIP')
    return record


def encoding_contracts(scope,exact):
    def pin(name):return dict(path=name,bytes=1,sha256='a'*64)
    required=scope.pins([pin(f'input/{n:04}.json') for n in range(3230)])
    full=compact_pin_map(required,required,scope,exact)
    exact(restore_pin_map(required,full,scope,exact),required,'ENCODER_FULL_MAP')
    subset={n:p for i,(n,p) in enumerate(required.items()) if i>1}
    omitted=compact_pin_map(required,subset,scope,exact)
    require(len(omitted['omitted_declared_paths'])==2,'ENCODER_EXACT_OMISSIONS')
    actual=scope.extend(subset,scope.pins([pin(f'physical/{n}.json') for n in range(4)]))
    expanded=compact_pin_map(required,actual,scope,exact)
    require(len(expanded['extra_physical_pins'])==4,'ENCODER_EXACT_EXTRAS')
    conflict=dict(required);name=next(iter(conflict));conflict[name]=dict(conflict[name],sha256='b'*64)
    try:compact_pin_map(required,conflict,scope,exact)
    except ValueError:pass
    else:raise ValueError('FULL73_METADATA_ENCODER_CONFLICT_ACCEPTED')
    try:restore_pin_map(required,dict(full,raw_pin_map_sha256='0'*64),scope,exact)
    except ValueError:pass
    else:raise ValueError('FULL73_METADATA_ENCODER_DIGEST_MUTATION_ACCEPTED')
    raw_bytes=len(json.dumps(actual,ensure_ascii=True,indent=2).encode('ascii'))
    compact_bytes=len(json.dumps(expanded,ensure_ascii=True,indent=2).encode('ascii'))
    require(raw_bytes>262144 and compact_bytes<2048,'ENCODER_3230_INPUTS_WITHOUT_PUBLISHER_LIMIT_INCREASE')
    return dict(state='PASS_BOUNDED_METADATA_REPORT_PIN_MAP6_NOT_RUNTIME_OR_PRODUCT',contracts=6,
        raw_fixture_bytes=raw_bytes,compact_fixture_bytes=compact_bytes,publisher_limit_bytes=262144,
        raw_pin_count=len(actual),full_map_losslessly_restored=True,actual_product_or_Native_executed=False)


def main():
    import argparse,os,re,threading,time,traceback
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    if '--check-report-encoding' in sys.argv[1:]:
        require(sys.argv[1:]==['--check-report-encoding'],'ONLY_ENCODING_CONTRACT_MODE')
        import accept_case112_current_epoch as a
        import current_stored_runtime_scope as scope
        print(json.dumps(encoding_contracts(scope,a.exact),allow_nan=False));return 0
    denied=[]
    def audit(event,args):
        if event=='subprocess.Popen':denied.append(1);raise ValueError('FULL73_METADATA_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(audit)
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import audit_evidence_io as original_io
    boot,_=envelope.namespace_bundle.load(c.ROOT,[CONSTRUCTION],{})
    construction=boot.native009_full72_construction_v1
    # Construction's13 fixed libraries suffice for the fresh reader/graph.
    libs,_=envelope.namespace_bundle.load(c.ROOT,construction.PINS,{})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader,_=libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle,libs.ast_clone_namespace_v1)
    loader,imports=construction.private_runtime_imports(loader)
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    attempt=parser.parse_args().attempt
    require(type(attempt) is int and 1<=attempt<=8,'BOUNDED_ATTEMPT')
    output=PREFIX+f'native009-full73-metadata{attempt:03}.v1.json'
    native=c.ROOT/(PREFIX+'current-runtime-run009.v1.json')
    require(not(c.ROOT/output).exists() and not native.exists(),'EXCLUSIVE_REPORT_AND_NO_NATIVE009')
    guard=libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started=time.monotonic();phase='CURRENT_ADMISSION';binding_state=metadata=shared=None
    original_check=guard.check;progress_state=dict(sample=0,last=started)
    def checkpoint(force=False):
        original_check(force=force)
        count=len(guard.samples)
        if count==progress_state['sample']:return
        progress_state['sample']=count;now=time.monotonic()
        if now-progress_state['last']<30:return
        progress_state['last']=now;sample=guard.samples[-1]
        print(json.dumps(dict(progress=True,phase=phase,elapsed_seconds=round(now-started,2),
            metadata_read_passes=0 if metadata is None else metadata.read_passes,
            metadata_inputs=0 if metadata is None else len(metadata.snapshots),
            system_CPU=sample['system_cpu_percent'],owned_CPU=sample.get('parent_cpu_machine_percent'),
            available_RAM_percent=sample['available_ram_percent'])),flush=True)
    # Passive progress over the same already-sampled Guard; no extra observer.
    guard.check=checkpoint
    row=dict(state='FAILED_FULL73_ACTUAL_PARENT_METADATA_NOT_NATIVE',accepted_count_delta=0,GO_authorized=False,
        actual_product_or_Native_executed=False,actual_Native_Frame_created=False,preparation_CPU_policy_changed=False,
        whole_Native_source_or_product_acceptance_qualified=False,current_result_and_future_sources_must_be_recosted=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        row['producer_source_pin']=q.pin(SELF)
        parent_proof=a.read_exact(q,PARENT_PROOF)
        a.exact(q.pin(FAILED_METADATA['path']),FAILED_METADATA,'ORIGINAL_MISSING_SHARED_CONNECTION_FAILURE')
        review=q.json(PUBLICATION_REVIEW)
        a.fields(review,dict(state='FAILED_RESULT_PUBLICATION_REVIEW_NOT_RUNTIME_OR_NATIVE_ACCEPTANCE',
            expected_original_output_absent_after_terminal_exit=True,process_exit_code=1,
            unchanged_publisher_limit_bytes=262144,inner_final_qualification_outcome_not_recoverable=True,
            accepted_count_delta=0,GO_authorized=False),'FAILED_PUBLICATION_REVIEW_NOT_RUNTIME_AUTHORITY')
        a.fields(parent_proof,dict(state='PASS_FULL73_PARENT_LAUNCH_JOB_FRAME_AND_ORACLE25_WITH_REPLAYABLE_DECLARED_COST_NOT_NATIVE',
            contracts=dict(run=25,errors=0,failures=0,skipped=0),semantic_inputs=3223,fresh_inputs=392,final_fresh_hashes=392,
            actual_parent_attempts=0,actual_worker_calls=0,actual_Frame_instances=0,subprocess_creation_attempts=0,
            previous_scope_and_budget_exactly_reconstructed=True,persisted_scope_uses_original_noninjecting_union=True,
            cleanup_confirmed=True),'CURRENT_REPLAYABLE_PARENT_COMPOSITION25')
        pins=scope.pins(parent_proof['source_pins'])
        for pin in pins.values():
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):
                a.exact(q.pin(pin['path']),pin,'ALL_QUALIFIED_CURRENT_CODE')
        for pin in [CONSTRUCTION]+construction.PINS:a.exact(q.pin(pin['path']),pin,'CORE_GRAPH_SOURCES')
        names,_=loader.load(c.ROOT,[pins[QUALIFIER]],{})
        upstream=names.qualify_native009_full73_parent_v1
        extra,_=loader.load(c.ROOT,upstream.READINESS,{})
        modules,_=loader.load(c.ROOT,[pins[upstream.ENTRY],pins[upstream.PARENT],construction.DECLARATION],{})
        entry=modules.native009_full73_worker_entry_v1;parent=modules.native009_parent_launch_v1
        base=a.read_exact(q,parent_proof['declared_scope_base_pin'])
        inherited=scope.extend(scope.pins(base['input_pins']),{parent_proof['declared_scope_base_pin']['path']:parent_proof['declared_scope_base_pin']})
        inherited=scope.extend(inherited,scope.pins(parent_proof['declared_scope_delta_pins']))
        graph_pin=pins[PREFIX+'successor-native009-full73-graph005.v1.json']
        prepared=a.read_exact(q,graph_pin);hint=a.read_exact(q,entry.HINT)
        a.exact(entry.HINT,prepared['bootstrap_pin'],'CURRENT_V4_HINT');a.exact(entry.WIRE,prepared['capsule_pin'],'CURRENT_V4_WIRE')
        transport,_=loader.load(c.ROOT,[entry.TRANSPORT],{})
        facade=NS(connect=transport.native009_full73_transport_v1.connect,constant=libs.native009_full72_transport_v1.constant)
        source=libs.native009_verified_source_profile_v1.connect(c.ROOT,loader,scope,bytes_policy,libs.receipt_xz_envelope_v1,
            libs.bounded_successor_capsule_wire_v2,guard.check,a,q,hint,facade)
        pin,raw=q._read(entry.WIRE['path'],parse=True);q._bind(pin['path'],pin);a.exact(pin,entry.WIRE,'EXACT_PACKET')
        api=source.api;graph,_=api.reconstruct(hint,bytes(raw),guard.check);del raw
        inherited,_=graph.binding.semantic_union(inherited,guard.check)
        a.exact(len(inherited),parent_proof['semantic_inputs'],'COMPLETE_PREVIOUS_SCOPE')
        original_union=type(graph.binding).semantic_union
        modules.native009_parent_scope_v1.inherit_declaration(graph,inherited,scope)
        launch=entry.launch_api(c.ROOT,loader)
        proxy,context=parent.recovery_api(libs.post_product_recovery_connection_v1,c.ROOT,q.snapshots[upstream.ENTRY],launch,
            extra.worker_readiness_v1,extra.worker_readiness_connection_v1,c)
        built=api.build(c.ROOT,loader,api,graph,envelope.prior,proxy,libs.post_product_recovery_window_v1,guard.check)
        old_budget=graph.binding.runtime_budget(inherited,parent_proof['inventory_requests'],built.window.DIRECT.runtime_budget,guard.check)
        a.exact(old_budget,parent_proof['original_complete_runtime_budget'],'ENTIRE_PREVIOUS_COST')
        configuration_pin=inherited['tools/p09/current_queue_successor_lossless_runtime_v4.py']
        a.exact(q.pin(configuration_pin['path']),configuration_pin,'EXACT_EXISTING_LOSSLESS_CONFIGURATION')
        configurations,_=loader.load(c.ROOT,[configuration_pin],{})
        configuration=configurations.current_queue_successor_lossless_runtime_v4
        for pin in configuration.PINS[1:]:a.exact(q.pin(pin['path']),pin,'EXACT_EXISTING_SHARED_READER_COMPONENT')
        components,_=loader.load(c.ROOT,configuration.PINS[1:],{})
        configuration.configure(api.runtime,components)
        row['lossless_configuration_source_pin']=configuration_pin
        connected=construction.construct(c.ROOT,loader,api,graph,built,envelope,libs.post_product_recovery_connection_v1,
            libs.post_product_recovery_window_v1,a,q,scope,inherited,prepared,graph_pin,guard.check)
        context.bind_parent(connected.parent_state)
        helpers=construction.helper_inventory(c.ROOT,connected.parent)
        require(helpers['Native_count']<=64,'ACTUAL_HELPER64_BEFORE_METADATA')
        row['helper_inventory_before_metadata']=helpers
        build=connected.original_run.__globals__['build']
        # The real configured Frame MRO carries the very same shared owner.
        owners=[]
        for cls in connected.frame.__mro__:
            fn=vars(cls).get('__init__')
            if callable(fn) and getattr(fn,'__closure__',None) and fn.__code__.co_filename.replace('\\','/').endswith('shared_metadata_frame_decoder_budget_v1.py'):
                cells=dict(zip(fn.__code__.co_freevars,(cell.cell_contents for cell in fn.__closure__)))
                if 'shared' in cells:owners.append(cells['shared'])
        require(len(owners)==1,'ONE_ORIGINAL_FRAME_SHARED_OWNER');shared=owners[0]
        require(shared.metadata is None and shared.frame is None,'FRESH_UNEXECUTED_SHARED_BUDGET')
        phase='ACTUAL_ORIGINAL_PARENT_METADATA_CALLBACK'
        metadata=build.BuildReader(c.ROOT,guard.check);metadata.pacer=bytes_policy.OwnedPacer()
        owner=NS(lock=threading.Lock(),samples=guard.samples,checkpoint_io=guard.check)
        binding_state=build.pressure.PreSaturationReadCheckpoint(metadata,owner)
        require(shared.metadata is metadata._lossless_metadata_router.budget and shared.frame is None,'REAL_READER_REGISTERED_IN_FRAME_SHARED_OWNER')
        require(connected.original_run is built.engine.run_owned,'SAME_WHOLE_ORIGINAL_ENGINE_FUNCTION')
        actual_callback=connected.original_run.__globals__['binding']
        required,rust=actual_callback(metadata)
        require(len(connected.callback_calls)==1 and len(rust)==787,'ONE_REAL_WHOLE_CALLBACK_AND_RUST787')
        for descriptor in graph.binding.descriptors():
            pin=descriptor['semantic_original_pin'];a.exact(metadata.pin(pin['path']),pin,'ALL73_REAL_SEMANTIC_PINS')
        require(len(graph.binding.descriptors())==73,'ALL73_CURRENT_BINDINGS')
        phase='ACTUAL_METADATA_CLOSING_HASHES';metadata.finish()
        require(metadata.final_fresh_hashes==len(metadata.snapshots)>0,'EVERY_REAL_METADATA_INPUT_FINAL_HASHED')
        routed=metadata._lossless_metadata_router
        require(set(routed.counts)==set(graph.binding.originals) and all(n>=2 for n in routed.counts.values()),'ALL73_FRESH_FIRST_AND_FINAL_DECODE')
        after=construction.helper_inventory(c.ROOT,connected.parent)
        a.exact(after,helpers,'NO_LATE_PROJECT_HELPER_DRIFT')
        required=scope.extend(required,connected.oracle_inherited);required=scope.extend(required,q.snapshots)
        required=scope.extend(required,metadata.snapshots);required,_=graph.binding.semantic_union(required,guard.check)
        require(all(required.get(n)==pin for n,pin in inherited.items()),'NO_PREVIOUS_SCOPE_REMOVED')
        inventory=a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'),('rust_inputs',),dict(os=os,Path=Path,require=require))
        requests=[]
        def paced():requests.append(1);q.open_pacer.reserve()
        a.exact(sorted(inventory.rust_inputs(c.ROOT,paced)),sorted(rust),'FRESH_CURRENT_RUST_INVENTORY')
        budget=graph.binding.runtime_budget(required,len(requests),built.window.DIRECT.runtime_budget,guard.check)
        total=budget['predicted_runtime_combined_seconds']+15
        _,delta=upstream.compact_scope(graph.binding,original_union,scope,base,parent_proof['declared_scope_base_pin'],required,guard.check,a.exact)
        row.update(semantic_inputs=len(required),metadata_fresh_inputs=len(metadata.snapshots),metadata_final_fresh_hashes=metadata.final_fresh_hashes,
            actual_metadata_read_passes=metadata.read_passes,actual_metadata_physical_bytes=metadata.bytes_read,
            actual_metadata_source_pins_compact=compact_pin_map(required,metadata.snapshots,scope,a.exact),
            actual_metadata_pin_map_losslessly_reconstructed=True,metadata_pressure=build.pressure_summary(binding_state),
            original_whole_parent_callback_executions=len(connected.callback_calls),descriptor_count=73,
            all73_fresh_first_and_final_decodes=True,shared_decoder=shared.evidence(),helper_inventory_after_metadata=after,
            previous_scope_and_budget_exactly_reconstructed=True,original_complete_runtime_budget=budget,
            predicted_complete_seconds_with_readiness=total,declared_cost_nominal_fits600=total<600,
            current_Rust_path_count=len(rust),inventory_requests=len(requests),additional_readiness_seconds_without_old_credit=15,
            declared_scope_base_pin=parent_proof['declared_scope_base_pin'],declared_scope_delta_pins=delta)
        phase='FINAL_QUALIFIER_HASHES';q.finish();guard.check(force=True)
        require(context.jobs==context.attempts==len(connected.parent_state.frames)==built.state.calls==0 and not denied and not native.exists(),'NO_NATIVE_FRAME_JOB_WORKER_OR_PRODUCT')
        require(total<600,'COMPLETE_DECLARED_SCOPE_PLUS_READINESS_OUTSIDE600')
        row.update(state='PASS_FULL73_ACTUAL_PARENT_METADATA_AND_SHARED_DECODER_NOT_NATIVE_FRAME_OR_PRODUCT',
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError) as error:
        row['error_type']=type(error).__name__
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        if metadata is not None:
            row['partial_metadata_diagnostics']=dict(read_passes=metadata.read_passes,physical_bytes=metadata.bytes_read,
                input_count=len(metadata.snapshots),final_fresh_hashes=metadata.final_fresh_hashes,
                not_a_complete_hash_or_Native_or_product_claim=True)
        if binding_state is not None:binding_state.restore()
        if shared is not None:shared.restore()
        guard.close();row.update(cleanup_confirmed=guard.cleanup,operation_phase=phase,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None),subprocess_creation_attempts=len(denied))
    require(guard.cleanup,'OWNER_CLEANUP')
    try:libs.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    except ValueError as error:
        if error.args!=('CURRENT_EPOCH_ACCEPT_WORKSPACE_BOUNDED_RECEIPT',):raise
        # Preserve a terminal failure rather than lose the result again. This
        # intentionally cannot stand in for the detailed whole-input proof.
        failure=dict(state='FAILED_BOUNDED_METADATA_RESULT_PUBLICATION_NOT_ACCEPTED',accepted_count_delta=0,
            GO_authorized=False,actual_product_or_Native_executed=False,actual_Native_Frame_created=False,
            producer_source_pin=row.get('producer_source_pin'),cleanup_confirmed=guard.cleanup,
            full_detailed_result_not_published=True,original_publisher_limit_bytes=262144,
            elapsed_seconds=row.get('elapsed_seconds'),operation_phase=row.get('operation_phase'))
        libs.successor_preparation_workspace_v1.publish(c.ROOT,output,failure,a)
        print(json.dumps(failure,allow_nan=False));return 1
    print(json.dumps({k:row.get(k) for k in ('state','semantic_inputs','metadata_fresh_inputs','metadata_final_fresh_hashes','fresh_inputs','final_fresh_hashes',
        'predicted_complete_seconds_with_readiness','shared_decoder','elapsed_seconds','CPU_max','owned_CPU_machine_max','owned_private_MiB_max',
        'RAM_min','cleanup_confirmed','operation_phase','error_code','error_frames')},allow_nan=False))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
