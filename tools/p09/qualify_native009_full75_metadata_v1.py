"""Actual whole75 parent metadata callback and final hashes, not Native.

Use the real BuildReader, existing one-stat/readinto implementation and shared
metadata/Frame budget. Preserve all old declarations and original guards. No
Frame instance, GO, Job, worker or product may execute in this qualification.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

SELF = 'tools/p09/qualify_native009_full75_metadata_v1.py'
PREFIX = 'implementation/p09/evidence/p09-361-case165-'
PARENT_PROOF = dict(path=PREFIX+'native009-full75-parent-connection001.v1.json', bytes=105930,
    sha256='a5dd7597582a1e4d3ccbb233f51b1376f98a8d3489a53ca00c0fdbc458b5bfcd')
QUALIFIER = 'tools/p09/qualify_native009_full75_parent_v1.py'
REFERENCE = dict(path='tools/p09/qualify_native009_full73_metadata_v1.py', bytes=37288,
    sha256='ce9261db8fb4913279c88c60033593f5c5d96a82339bcdc1a3b3f6a73657b6e0')
CONSTRUCTION = dict(path='tools/p09/native009_full72_construction_v1.py', bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')


def require(ok, label):
    if not ok: raise ValueError('FULL75_METADATA_'+label)


def main():
    import argparse, os, re, threading, time, traceback
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    denied = []
    def audit(event, args):
        if event == 'subprocess.Popen': denied.append(1); raise ValueError('FULL75_METADATA_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(audit)
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import audit_evidence_io as original_io
    initial, _ = envelope.namespace_bundle.load(c.ROOT, [CONSTRUCTION], {})
    construction = initial.native009_full72_construction_v1
    libs, _ = envelope.namespace_bundle.load(c.ROOT, construction.PINS, {})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader, _ = libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle, libs.ast_clone_namespace_v1)
    loader, _ = construction.private_runtime_imports(loader)
    parser = argparse.ArgumentParser(); parser.add_argument('--attempt', type=int, required=True)
    attempt = parser.parse_args().attempt
    require(type(attempt) is int and 1 <= attempt <= 8, 'FINITE_ATTEMPT')
    output = PREFIX+f'native009-full75-metadata{attempt:03}.v1.json'
    native = c.ROOT/(PREFIX+'current-runtime-run009.v1.json')
    require(not (c.ROOT/output).exists() and not native.exists(), 'EXCLUSIVE_METADATA_NOT_NATIVE')
    guard = libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(
        libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started, phase = time.monotonic(), 'CURRENT_ADMISSION'
    q = metadata = binding_state = shared = chunk = None
    original_check = guard.check
    progress = dict(sample=0, stamp=started)
    def checkpoint(force=False):
        original_check(force=force)
        count = len(guard.samples)
        if count == progress['sample']: return
        progress['sample'] = count; now = time.monotonic()
        if now-progress['stamp'] < 30: return
        progress['stamp'] = now; sample = guard.samples[-1]
        print(json.dumps(dict(progress=True, phase=phase, elapsed_seconds=round(now-started, 2),
            metadata_read_passes=0 if metadata is None else metadata.read_passes,
            metadata_inputs=0 if metadata is None else len(metadata.snapshots),
            system_CPU=sample['system_cpu_percent'], owned_CPU=sample.get('parent_cpu_machine_percent'),
            available_RAM_percent=sample['available_ram_percent'])), flush=True)
    guard.check = checkpoint
    row = dict(state='FAILED_FULL75_ACTUAL_PARENT_METADATA_NOT_NATIVE', accepted_count_delta=0, GO_authorized=False,
        actual_product_or_Native_executed=False, actual_Native_Frame_created=False, preparation_CPU_policy_changed=False,
        whole_Native_source_or_product_acceptance_qualified=False, current_result_and_future_sources_must_be_recosted=True)
    try:
        guard.acquire(); seed = a.AcceptanceReader(c.ROOT, guard.check)
        proof = a.read_exact(seed, PARENT_PROOF); pins = scope.pins(proof['source_pins'])
        a.exact(seed.pin(QUALIFIER), pins[QUALIFIER], 'CURRENT_PARENT_CONSTRUCTION_SOURCE')
        modules, _ = loader.load(c.ROOT, [pins[QUALIFIER], REFERENCE], {})
        parent_code, reference = modules.qualify_native009_full75_parent_v1, modules.qualify_native009_full73_metadata_v1
        for pin in (parent_code.SNAPSHOT, parent_code.CHUNK, REFERENCE): a.exact(seed.pin(pin['path']), pin, 'CURRENT_QUALIFIED_READER_CODE')
        readers, _ = loader.load(c.ROOT, [parent_code.SNAPSHOT, parent_code.CHUNK], {'audit_evidence_io': original_io})
        snapshot, chunk = readers.single_snapshot_source_guard_v1, readers.reusable_audit_chunk_v1
        pin, raw = seed._read(snapshot.ORIGINAL_PIN['path'], parse=True); seed._bind(pin['path'], pin)
        a.exact(pin, snapshot.ORIGINAL_PIN, 'UNCHANGED_ORIGINAL_SOURCE_PREDICATE')
        original_source_raw = bytes(raw)
        SourceReader, _ = snapshot.reader_type(a.AcceptanceReader, original_source_raw)
        Reader, _ = chunk.reader_type(SourceReader, original_source_raw); del raw
        q = Reader(c.ROOT, guard.check)
        for pin in seed.snapshots.values(): a.exact(q.pin(pin['path']), pin, 'FRESH_READER_BOOTSTRAP')
        row['producer_source_pin'] = q.pin(SELF)
        a.fields(proof, dict(state='PASS_FULL75_PARENT_LAUNCH_JOB_FRAME_ORACLE_AND_SHARED_OWNER27_WITH_REPLAYABLE_DECLARED_COST_NOT_NATIVE',
            contracts=dict(run=27, errors=0, failures=0, skipped=0), semantic_inputs=3257, fresh_inputs=399, final_fresh_hashes=399,
            actual_parent_attempts=0, actual_worker_calls=0, actual_Frame_instances=0, subprocess_creation_attempts=0,
            previous_scope_and_budget_exactly_reconstructed=True, persisted_scope_uses_original_noninjecting_union=True,
            shared_owner_connected_but_unused=True, cleanup_confirmed=True), 'ACTUAL_CURRENT_PARENT27_NOT_METADATA_PASS')
        for pin in pins.values():
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):
                a.exact(q.pin(pin['path']), pin, 'ALL_CURRENT_PARENT_QUALIFIED_CODE')
        for pin in [CONSTRUCTION]+construction.PINS+parent_code.READINESS:
            a.exact(q.pin(pin['path']), pin, 'CURRENT_CORE_GRAPH_SOURCE')
        extra, _ = loader.load(c.ROOT, parent_code.READINESS, {})
        parts, _ = loader.load(c.ROOT, [pins[parent_code.ENTRY], pins[parent_code.PARENT], construction.DECLARATION], {})
        entry, parent = parts.native009_full75_worker_entry_v1, parts.native009_parent_launch_v1
        base = a.read_exact(q, proof['declared_scope_base_pin'])
        inherited = scope.extend(scope.pins(base['input_pins']), {proof['declared_scope_base_pin']['path']: proof['declared_scope_base_pin']})
        inherited = scope.extend(inherited, scope.pins(proof['declared_scope_delta_pins']))
        graph_pin = proof['graph_report_pin']; prepared = a.read_exact(q, graph_pin); hint = a.read_exact(q, entry.HINT)
        a.exact(entry.HINT, prepared['bootstrap_pin'], 'CURRENT_V5_HINT'); a.exact(entry.WIRE, prepared['capsule_pin'], 'CURRENT_V5_WIRE')
        transports, _ = loader.load(c.ROOT, [entry.TRANSPORT], {})
        facade = NS(connect=transports.native009_full75_transport_v1.connect, constant=libs.native009_full72_transport_v1.constant)
        source = libs.native009_verified_source_profile_v1.connect(c.ROOT, loader, scope, bytes_policy,
            libs.receipt_xz_envelope_v1, libs.bounded_successor_capsule_wire_v2, guard.check, a, q, hint, facade)
        pin, raw = q._read(entry.WIRE['path'], parse=True); q._bind(pin['path'], pin); a.exact(pin, entry.WIRE, 'ACTUAL_CURRENT_PACKET')
        api = source.api; graph, _ = api.reconstruct(hint, bytes(raw), guard.check); del raw
        inherited, _ = graph.binding.semantic_union(inherited, guard.check)
        a.exact(len(inherited), proof['semantic_inputs'], 'COMPLETE_PREVIOUS3257_NOT_SOURCE_SUBSET')
        original_union = type(graph.binding).semantic_union
        parts.native009_parent_scope_v1.inherit_declaration(graph, inherited, scope)
        launch = entry.launch_api(c.ROOT, loader)
        proxy, context = parent.recovery_api(libs.post_product_recovery_connection_v1, c.ROOT, q.snapshots[parent_code.ENTRY], launch,
            extra.worker_readiness_v1, extra.worker_readiness_connection_v1, c)
        built = api.build(c.ROOT, loader, api, graph, envelope.prior, proxy, libs.post_product_recovery_window_v1, guard.check)
        old_budget = graph.binding.runtime_budget(inherited, proof['inventory_requests'], built.window.DIRECT.runtime_budget, guard.check)
        a.exact(old_budget, proof['original_complete_runtime_budget'], 'ENTIRE_PREVIOUS_SCOPE_COST')
        a.exact(q.pin(parent_code.CONFIGURATION['path']), parent_code.CONFIGURATION, 'CURRENT_EXISTING_SHARED_CONFIGURATION')
        config, _ = loader.load(c.ROOT, [parent_code.CONFIGURATION], {})
        configuration = config.current_queue_successor_lossless_runtime_v4
        for pin in configuration.PINS[1:]: a.exact(q.pin(pin['path']), pin, 'EXACT_CURRENT_SHARED_COMPONENT')
        components, _ = loader.load(c.ROOT, configuration.PINS[1:], {})
        configuration.configure(api.runtime, components)
        connected = construction.construct(c.ROOT, loader, api, graph, built, envelope, libs.post_product_recovery_connection_v1,
            libs.post_product_recovery_window_v1, a, q, scope, inherited, prepared, graph_pin, guard.check)
        context.bind_parent(connected.parent_state)
        helpers = construction.helper_inventory(c.ROOT, connected.parent)
        require(helpers['Native_count'] <= 64, 'ACTUAL_HELPER64_BEFORE_METADATA')
        row['helper_inventory_before_metadata'] = helpers
        shared = parent_code.shared_owner(connected.frame)
        require(shared.metadata is None and shared.frame is None, 'FRESH_UNREGISTERED_SHARED_OWNER')
        build = connected.original_run.__globals__['build']
        metadata = build.BuildReader(c.ROOT, guard.check)
        pin, raw = q._read(parent_code.SNAPSHOT['path'], parse=True); q._bind(pin['path'], pin)
        a.exact(pin, parent_code.SNAPSHOT, 'FRESH_FIXED_SNAPSHOT_REFERENCE_SOURCE')
        references = reference.compiled_snapshot_references(bytes(raw)); del raw
        row['existing_source_code_comparison'] = {}
        row['metadata_builder_source_snapshot_connection'] = reference.adopt_source_snapshot(metadata, snapshot,
            original_source_raw, row['existing_source_code_comparison'], references)
        del original_source_raw
        metadata.pacer = bytes_policy.OwnedPacer()
        owner = NS(lock=threading.Lock(), samples=guard.samples, checkpoint_io=guard.check)
        binding_state = build.pressure.PreSaturationReadCheckpoint(metadata, owner)
        require(shared.metadata is metadata._lossless_metadata_router.budget and shared.frame is None, 'REAL_METADATA_REGISTERED_WITH_FRAME_SHARED_OWNER')
        phase = 'EARLY_CURRENT_SCOPE_AND_COST'
        early, _ = graph.binding.semantic_union(scope.extend(connected.oracle_inherited, q.snapshots), guard.check)
        inventory = a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'), ('rust_inputs',), dict(os=os, Path=Path, require=require))
        early_requests = []
        def early_paced(): early_requests.append(1); q.open_pacer.reserve()
        early_rust = inventory.rust_inputs(c.ROOT, early_paced)
        require(len(early_rust) == 787 and set(early_rust) <= set(early), 'EARLY_CURRENT_RUST787')
        early_budget = graph.binding.runtime_budget(early, len(early_requests), built.window.DIRECT.runtime_budget, guard.check)
        row.update(early_declared_inputs=len(early), early_predicted_complete_seconds_with_readiness=early_budget['predicted_runtime_combined_seconds']+15,
            early_current_declared_budget=early_budget, early_cost_is_not_full_metadata_or_Native_acceptance=True)
        require(row['early_predicted_complete_seconds_with_readiness'] < 600, 'EARLY_KNOWN_SCOPE_ALREADY_OUTSIDE600')
        phase = 'ACTUAL_ORIGINAL_PARENT_METADATA_CALLBACK'
        require(connected.original_run is built.engine.run_owned, 'SAME_WHOLE_ORIGINAL_PARENT_FUNCTION')
        required, rust = connected.original_run.__globals__['binding'](metadata)
        a.exact(sorted(early_rust), sorted(rust), 'SAME_REAL_CURRENT_RUST_SET')
        require(len(connected.callback_calls) == 1 and len(rust) == 787 and len(graph.binding.descriptors()) == 75, 'ONE_REAL_CALLBACK_AND_ALL75')
        for descriptor in graph.binding.descriptors():
            pin = descriptor['semantic_original_pin']; a.exact(metadata.pin(pin['path']), pin, 'ALL75_REAL_SEMANTIC_PINS')
        phase = 'ACTUAL_METADATA_CLOSING_HASHES'; metadata.finish()
        require(metadata.final_fresh_hashes == len(metadata.snapshots) > 0, 'EVERY_REAL_METADATA_INPUT_FINAL_HASHED')
        routed = metadata._lossless_metadata_router
        require(set(routed.counts) == set(graph.binding.originals) and all(n >= 2 for n in routed.counts.values()), 'ALL75_FRESH_INITIAL_AND_FINAL_DECODE')
        a.exact(construction.helper_inventory(c.ROOT, connected.parent), helpers, 'NO_LATE_PROJECT_HELPER_DRIFT')
        required = scope.extend(scope.extend(required, connected.oracle_inherited), q.snapshots)
        required, _ = graph.binding.semantic_union(scope.extend(required, metadata.snapshots), guard.check)
        require(all(required.get(n) == pin for n, pin in inherited.items()), 'NO_PREVIOUS_SEMANTIC_INPUT_REMOVED')
        requests = []
        def paced(): requests.append(1); q.open_pacer.reserve()
        a.exact(sorted(inventory.rust_inputs(c.ROOT, paced)), sorted(rust), 'FRESH_CURRENT_RUST_INVENTORY')
        budget = graph.binding.runtime_budget(required, len(requests), built.window.DIRECT.runtime_budget, guard.check)
        total = budget['predicted_runtime_combined_seconds']+15
        _, delta = parent_code.compact_scope(graph.binding, original_union, scope, base, proof['declared_scope_base_pin'], required, guard.check, a.exact)
        row.update(semantic_inputs=len(required), metadata_fresh_inputs=len(metadata.snapshots), metadata_final_fresh_hashes=metadata.final_fresh_hashes,
            actual_metadata_read_passes=metadata.read_passes, actual_metadata_physical_bytes=metadata.bytes_read,
            actual_metadata_source_pins_compact=reference.compact_pin_map(required, metadata.snapshots, scope, a.exact),
            actual_metadata_pin_map_losslessly_reconstructed=True, metadata_pressure=build.pressure_summary(binding_state),
            metadata_source_predicate_optimization=metadata.source_snapshot_diagnostics(), original_whole_parent_callback_executions=len(connected.callback_calls),
            descriptor_count=75, all75_fresh_initial_and_final_decodes=True, shared_decoder=shared.evidence(),
            previous_scope_and_budget_exactly_reconstructed=True, original_complete_runtime_budget=budget,
            predicted_complete_seconds_with_readiness=total, declared_cost_nominal_fits600=total < 600, current_Rust_path_count=len(rust),
            inventory_requests=len(requests), additional_readiness_seconds_without_old_credit=15,
            declared_scope_base_pin=proof['declared_scope_base_pin'], declared_scope_delta_pins=delta, persisted_scope_uses_original_noninjecting_union=True)
        require(total < 600, 'CURRENT_COMPLETE_SCOPE_PLUS_READINESS_OUTSIDE600')
        phase = 'FINAL_QUALIFIER_HASHES'; q.finish(); guard.check(force=True)
        require(context.jobs == context.attempts == len(connected.parent_state.frames) == built.state.calls == 0 and not denied and not native.exists(),
            'NO_NATIVE_FRAME_JOB_WORKER_OR_PRODUCT')
        row.update(state='PASS_FULL75_ACTUAL_PARENT_METADATA_AND_SHARED_DECODER_NOT_NATIVE_FRAME_OR_PRODUCT',
            source_pins=list(q.snapshots.values()), fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, NameError) as error:
        row['error_type'] = type(error).__name__
        row['error_frames'] = [dict(file=Path(f.filename).name, function=f.name, line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}', error.args[0]): row['error_code'] = error.args[0]
    finally:
        if metadata is not None:
            row['partial_metadata_diagnostics'] = dict(read_passes=metadata.read_passes, physical_bytes=metadata.bytes_read,
                input_count=len(metadata.snapshots), final_fresh_hashes=metadata.final_fresh_hashes, not_a_complete_hash_or_Native_or_product_claim=True)
            if callable(getattr(metadata, 'source_snapshot_diagnostics', None)):
                row['partial_metadata_diagnostics']['source_predicate_snapshot'] = metadata.source_snapshot_diagnostics()
        if binding_state is not None: binding_state.restore()
        if shared is not None: shared.restore()
        if q is not None:
            row['qualifier_observed_inputs'] = len(q.snapshots); row['qualifier_closing_hashes_completed'] = q.final_fresh_hashes
        guard.close()
        row.update(cleanup_confirmed=guard.cleanup, operation_phase=phase, elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples), default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None), default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None), default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples), default=None), subprocess_creation_attempts=len(denied))
        row['last_original_resource_samples'] = [{k: s.get(k) for k in ('time_utc', 'system_cpu_percent', 'parent_cpu_machine_percent',
            'available_ram_percent', 'commit_used_percent', 'parent_private_mib')} for s in guard.samples[-8:]]
    require(guard.cleanup, 'OWNER_CLEANUP')
    try: libs.successor_preparation_workspace_v1.publish(c.ROOT, output, row, a)
    except ValueError as error:
        if error.args != ('CURRENT_EPOCH_ACCEPT_WORKSPACE_BOUNDED_RECEIPT',): raise
        failure = dict(state='FAILED_BOUNDED_METADATA_RESULT_PUBLICATION_NOT_ACCEPTED', accepted_count_delta=0, GO_authorized=False,
            actual_product_or_Native_executed=False, actual_Native_Frame_created=False, producer_source_pin=row.get('producer_source_pin'),
            cleanup_confirmed=guard.cleanup, full_detailed_result_not_published=True, original_publisher_limit_bytes=262144,
            elapsed_seconds=row.get('elapsed_seconds'), operation_phase=row.get('operation_phase'))
        libs.successor_preparation_workspace_v1.publish(c.ROOT, output, failure, a)
        print(json.dumps(failure)); return 1
    print(json.dumps({k: row.get(k) for k in ('state', 'semantic_inputs', 'metadata_fresh_inputs', 'metadata_final_fresh_hashes',
        'fresh_inputs', 'final_fresh_hashes', 'early_declared_inputs', 'early_predicted_complete_seconds_with_readiness',
        'predicted_complete_seconds_with_readiness', 'shared_decoder', 'elapsed_seconds', 'CPU_max', 'owned_CPU_machine_max',
        'owned_private_MiB_max', 'RAM_min', 'cleanup_confirmed', 'operation_phase', 'error_code', 'error_frames')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__ == '__main__': raise SystemExit(main())
