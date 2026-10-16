"""Qualify fixed161 over the real75 factory, never build/execute an engine.

The old Native009 output is immutable input, not replay authority. All161
physical carriers are freshly decoded twice with one original five-second
budget. This remains separate from actual metadata+Frame shared qualification.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

SELF='tools/p09/qualify_legacy_history_binding_v1.py'
LIBRARY='tools/p09/legacy_history_binding_v1.py'
TEST='tools/p09/tests/test_legacy_history_binding_v1.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
CONSTRUCTION=dict(path='tools/p09/native009_full72_construction_v1.py',bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')


def require(ok,label):
    if not ok: raise ValueError('QUALIFY_LEGACY_HISTORY_'+label)


def main():
    import argparse,importlib.util,io,os,re,time,traceback,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    denied=[]
    def audit(event,args):
        if event=='subprocess.Popen': denied.append(1); raise ValueError('LEGACY_HISTORY_QUALIFICATION_ALL_SUBPROCESS_DENIED')
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
    output=PREFIX+f'legacy-history-binding-code{attempt:03}.v1.json'
    manifest_name=PREFIX+f'legacy-history-binding-manifest{attempt:03}.v1.json'
    require(not(c.ROOT/output).exists() and not(c.ROOT/manifest_name).exists(),'EXCLUSIVE_DIAGNOSTIC_ARTIFACTS')
    guard=libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started=time.monotonic(); q=budget=None; phase='ADMISSION'
    row=dict(state='FAILED_FIXED_HISTORY161_BINDING_NOT_ADOPTED',accepted_count_delta=0,GO_authorized=False,
        actual_worker_engine_Job_Frame_or_Native_executed=False,full_current_runtime_scope_or_helper_bound_qualified=False,
        actual_metadata_Frame_shared_decoder5_qualified=False,worker_transport_or_dispatch_qualified=False,
        Native009_replayed=False,current_result_and_future_sources_must_be_recosted=True,preparation_CPU_policy_changed=False)
    try:
        guard.acquire(); seed=a.AcceptanceReader(c.ROOT,guard.check)
        # Reader optimization is exactly the one recorded by current75 proofs.
        for name in (SELF,LIBRARY,TEST): seed.pin(name)
        library,_=loader.load(c.ROOT,[seed.snapshots[LIBRARY]],{}); m=library.legacy_history_binding_v1
        physical_proof=a.read_exact(seed,m.REPACK)
        reader_helper='tools/p09/legacy149_binding_v1.py'
        # Fixed source pin is inherited from Native009, not an arbitrary local
        # dependency. The report is read normally before native is ever reused.
        native_seed=a.read_exact(seed,m.NATIVE)
        native_pins=scope.pins(native_seed['source_freeze'])
        a.exact(seed.pin(reader_helper),native_pins[reader_helper],'QUALIFIED_READER_HELPER_FROM_NATIVE009')
        names,_=loader.load(c.ROOT,[native_pins[reader_helper]],{})
        reader=names.legacy149_binding_v1
        for p in (reader.SNAPSHOT,reader.CHUNK): a.exact(seed.pin(p['path']),p,'FIXED_SOURCE_SNAPSHOT_AND_REUSABLE_CHUNK')
        readers,_=loader.load(c.ROOT,[reader.SNAPSHOT,reader.CHUNK],{'audit_evidence_io':original_io})
        snapshot,chunk=readers.single_snapshot_source_guard_v1,readers.reusable_audit_chunk_v1
        p,raw=seed._read(snapshot.ORIGINAL_PIN['path'],parse=True); seed._bind(p['path'],p)
        a.exact(p,snapshot.ORIGINAL_PIN,'ORIGINAL_SOURCE_PREDICATE')
        Source,_=snapshot.reader_type(a.AcceptanceReader,bytes(raw)); Reader,_=chunk.reader_type(Source,bytes(raw)); del raw
        q=Reader(c.ROOT,guard.check)
        for p in seed.snapshots.values(): a.exact(q.pin(p['path']),p,'FRESH_SEED_SCOPE')
        phase='FIXED_REPORTED_STATE_AND_CURRENT_CARRIER_ADMISSION'
        catalog,history,repack,native=m.admit(q,a)
        for p in [CONSTRUCTION]+construction.PINS: a.exact(q.pin(p['path']),p,'UNCHANGED_ORIGINAL_FACTORY_PROGRAMS')
        entry_name='tools/p09/native009_full75_worker_entry_v1.py'
        a.exact(q.pin(entry_name),native_pins[entry_name],'EXACT_FROZEN_WORKER_METADATA_CONSTANTS_ONLY')
        entry_ns,_=loader.load(c.ROOT,[native_pins[entry_name]],{}); entry=entry_ns.native009_full75_worker_entry_v1
        for p in (entry.TRANSPORT,entry.HINT,entry.WIRE,entry.STEP): a.exact(q.pin(p['path']),p,'EXACT_FROZEN75_TRANSPORT_INPUTS')
        transport,_=loader.load(c.ROOT,[entry.TRANSPORT],{})
        api=transport.native009_full75_transport_v1.connect(c.ROOT,loader,scope,bytes_policy,libs.receipt_xz_envelope_v1,
            libs.bounded_successor_capsule_wire_v2,guard.check,a.exact)
        for proof in api.source_proofs: a.exact(q.pin(proof['source_pin']['path']),proof['source_pin'],'ALL_FACTORY_PRIVATE_SOURCE_BYTES')
        hint=a.read_exact(q,entry.HINT); prior=catalog.prior()
        def factory(): return api.factory(hint,copy_prior68())
        def copy_prior68():
            import copy
            return copy.deepcopy(prior[:68])
        module=factory(); old_bound=module.Binding(prior,m.MANIFEST,next_case=165)
        a.exact(old_bound.descriptors(),prior,'ACTUAL_WHOLE_CURRENT75_FACTORY_WITHOUT_ENGINE_BUILD')
        semantic=scope.pins(native['source_input_representation']['semantic_source_freeze'])
        # Original cost family only; constructing a runtime engine would try
        # to reuse Native009, so never call api.build or a worker entry here.
        window,_=libs.post_product_recovery_connection_v1.current_window(envelope.prior,libs.post_product_recovery_window_v1,
            q.text(libs.post_product_recovery_window_v1.WINDOW_PIN['path']).encode('utf-8'))
        requests=native['complete_runtime_budget']['final_inventory_checkpoint_count']
        before=old_bound.runtime_budget(semantic,requests,window.DIRECT.runtime_budget,guard.check)
        a.exact(before,native['complete_runtime_budget'],'ENTIRE_REAL_NATIVE009_MODEL_REPRODUCED')
        phase='PRIVATE161_CONSTRUCTOR_AND_ORACLES'
        proof=m.install(module,catalog,libs.receipt_xz_envelope_v1,mode='parent')
        fixture=dict(schema_version='hwpx-agent.p09-fixed-history161-binding-diagnostic/v1',descriptors=catalog.rows(),
            legacy_history_physical_evidence_provenance=catalog.declaration(),worker_packet_or_Native_qualified=False)
        manifest_pin=libs.successor_preparation_workspace_v1.publish(c.ROOT,manifest_name,fixture,a); q.pin(manifest_name)
        rows=catalog.rows(); by_name={r['semantic_original_pin']['path']:r for r in rows}
        names=(rows[75]['semantic_original_pin']['path'],catalog.declaration()['old_seven_descriptors'][0]['semantic_original_pin']['path'])
        carriers=[]
        for name in names:
            r=by_name[name]; p,buffer=q._read(r['physical_envelope_pin']['path'],parse=True); q._bind(p['path'],p)
            a.exact(p,r['physical_envelope_pin'],'FRESH_CODEC_CONTRACT_DATA'); carriers.append((r,bytes(buffer))); del buffer
        try: module.source.codec.decode(carriers[0][1],guard.check)
        except ValueError as error: require(error.args==('LEGACY_HISTORY_BINDING_COMPLETE161_BEFORE_NEW_CODEC',),'PRECONSTRUCTOR_NEW_CODEC_DENIAL')
        else: require(False,'NEW_CODEC_MUST_REQUIRE_WHOLE161')
        bound=module.Binding(rows,manifest_pin,next_case=165)
        required,_=bound.semantic_union(scope.extend(semantic,q.snapshots),guard.check)
        spec=importlib.util.spec_from_file_location('legacy_history_binding_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
        tests.M=m; tests.CATALOG=catalog; tests.MODULE=module; tests.BOUND=bound; tests.PIN=manifest_pin
        tests.REQUIRED=required; tests.CHECK=guard.check; tests.PROOF=proof; tests.FACTORY=factory
        tests.XZ=libs.receipt_xz_envelope_v1; tests.CARRIERS=carriers; tests.NATIVE=native
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['contract_failures']=[dict(test=t.id().rsplit('.',1)[-1],exception_type=trace.splitlines()[-1].split(':',1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row['contracts'],dict(run=18,errors=0,failures=0,skipped=0),'ALL_FIXED161_CONTRACTS18')
        bound=module.Binding(rows,manifest_pin,next_case=165)
        projection,_=bound.project(required,guard.check)
        physical=envelope._namespaces.runtime_envelope_physical_io_v1
        a.exact(q.pin(physical.SELF),native_pins[physical.SELF],'ORIGINAL_FIVE_SECOND_BUDGET_SOURCE')
        budget=physical.DecoderBudget(guard.check); counts={r['semantic_original_pin']['path']:0 for r in rows}
        phase='ALL161_TWO_FRESH_PHYSICAL_DECODE_PASSES'
        for boundary in ('before','after'):
            for r in rows:
                old,new=r['semantic_original_pin'],r['physical_envelope_pin']
                p,buffer=q._read(new['path'],parse=True); q._bind(p['path'],p); a.exact(p,new,'ALL161_FRESH_PHYSICAL_BYTES')
                decoded=budget.run(lambda check:projection.decode_fresh(old['path'],p,bytes(buffer),check)); del buffer
                require(len(decoded)==old['bytes'],'FULL_ORIGINAL_DECODED_SIZE'); del decoded
                counts[old['path']]+=1
        require(budget.attempts==budget.completed==322 and all(n==2 for n in counts.values()),'ALL161_FRESH_OPAQUE_RESTORATIONS')
        phase='FULL_DECLARED_SCOPE_AND_BOTH_DEADLINE_MODELS'
        inventory=a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'),('rust_inputs',),dict(os=os,Path=Path,require=require))
        observed=[]
        def paced(): observed.append(1); q.open_pacer.reserve()
        rust=inventory.rust_inputs(c.ROOT,paced); require(len(rust)==787,'CURRENT_RUST787')
        model_source='tools/p09/whole_runtime_metadata_budget_v1.py'; q.pin(model_source)
        model_ns,_=loader.load(c.ROOT,[q.snapshots[model_source]],{})
        required,_=bound.semantic_union(scope.extend(semantic,q.snapshots),guard.check)
        require(all(required.get(n)==p for n,p in semantic.items()) and set(rust)<=set(required),'EVERY_NATIVE009_SEMANTIC_PIN_AND_RUST_PRESERVED')
        cost=bound.runtime_budget(required,len(observed),window.DIRECT.runtime_budget,guard.check)
        whole=model_ns.whole_runtime_metadata_budget_v1.assess(cost)
        row.update(descriptor_count=161,prior75_constructor_preserved=True,new_history_aliases=86,repacked_existing_aliases=7,
            exact_reported_role_catalog_sha256=m.CATALOG_SHA,role_declaration_sha256=m.DECLARATION_SHA,
            original_missing_execution_flags_not_defaulted=True,worker_declaration_not_parent_admission=True,
            declared_semantic_inputs=len(required),complete_prototype_runtime_budget=cost,whole720_necessary_model=whole,
            prototype_model_is_not_current_runtime_admission=True,inventory_requests=len(observed),current_Rust_path_count=len(rust),
            decoder_budget=budget.evidence(),decode_counts=counts,all_prior_semantic_pins_retained=True,
            current_manifest_pin=manifest_pin,physical_trial_pins=[m.HISTORY,m.REPACK],prior_failed_native_pin=m.NATIVE)
        phase='FINAL_FRESH_HASHES'; q.finish(); guard.check(force=True)
        require(not denied,'NO_SUBPROCESS_OR_PRODUCT')
        row.update(state='PASS_FIXED161_BINDING18_AND_TWO_PHYSICAL_DECODE_PASSES_NOT_WORKER_OR_NATIVE',
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
