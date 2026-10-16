"""Current75 dispatch construction and independent accounting, never execute.

Reuse the completed whole-metadata evidence without rereading all its data in
another preparation callback. Freshly verify every qualified program, rebuild
the original parent, and independently replay the full declared scope/cost.
Fresh Native metadata, both byte boundaries and product remain mandatory.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

SELF = 'tools/p09/qualify_native009_full75_dispatch_v1.py'
PREFIX = 'implementation/p09/evidence/p09-361-case165-'
METADATA = dict(path=PREFIX+'native009-full75-metadata002.v1.json', bytes=123352,
    sha256='740e5aced9e82de5b409735bbdf2f44afdf469864a2017bb112d1541db9aaff1')
CONSTRUCTION = dict(path='tools/p09/native009_full72_construction_v1.py', bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
CONNECTOR = 'tools/p09/native009_full75_dispatch_connection_v1.py'
TEST = 'tools/p09/tests/test_native009_full75_dispatch_connection_v1.py'
PARENT = 'tools/p09/qualify_native009_full75_parent_v1.py'
ENTRY = 'tools/p09/native009_full75_worker_entry_v1.py'
LAUNCH = 'tools/p09/native009_parent_launch_v1.py'


def require(ok, label):
    if not ok: raise ValueError('FULL75_DISPATCH_'+label)


def main():
    import argparse, io, os, re, time, traceback, unittest
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    denied = []
    def audit(event, args):
        if event == 'subprocess.Popen': denied.append(1); raise ValueError('FULL75_DISPATCH_ALL_SUBPROCESS_DENIED')
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
    output = PREFIX+f'native009-full75-dispatch-connection{attempt:03}.v1.json'
    native = c.ROOT/(PREFIX+'current-runtime-run009.v1.json')
    require(not (c.ROOT/output).exists() and not native.exists(), 'EXCLUSIVE_REPORT_AND_NO_NATIVE009')
    guard = libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(
        libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started, phase = time.monotonic(), 'CURRENT_ADMISSION'
    q = shared = None
    row = dict(state='FAILED_FULL75_DISPATCH_CONNECTION_NOT_NATIVE', accepted_count_delta=0, GO_authorized=False,
        actual_product_or_Native_executed=False, actual_metadata_callback_executed=False,
        whole_current_Native_source_or_dispatch_qualified=False, current_result_and_future_sources_must_be_recosted=True,
        preparation_CPU_policy_changed=False)
    try:
        guard.acquire(); seed = a.AcceptanceReader(c.ROOT, guard.check)
        proof = a.read_exact(seed, METADATA); pins = scope.pins(proof['source_pins'])
        a.exact(seed.pin(PARENT), pins[PARENT], 'CURRENT_PARENT_QUALIFIER')
        names, _ = loader.load(c.ROOT, [pins[PARENT]], {})
        parent_code = names.qualify_native009_full75_parent_v1
        readers, _ = loader.load(c.ROOT, [parent_code.SNAPSHOT, parent_code.CHUNK], {'audit_evidence_io': original_io})
        snapshot, chunk = readers.single_snapshot_source_guard_v1, readers.reusable_audit_chunk_v1
        pin, raw = seed._read(snapshot.ORIGINAL_PIN['path'], parse=True); seed._bind(pin['path'], pin)
        a.exact(pin, snapshot.ORIGINAL_PIN, 'ORIGINAL_SOURCE_PREDICATE')
        SourceReader, _ = snapshot.reader_type(a.AcceptanceReader, bytes(raw))
        Reader, _ = chunk.reader_type(SourceReader, bytes(raw)); del raw
        q = Reader(c.ROOT, guard.check)
        for pin in seed.snapshots.values(): a.exact(q.pin(pin['path']), pin, 'FRESH_SEED_SOURCES')
        for name in (SELF, CONNECTOR, TEST): q.pin(name)
        code, _ = loader.load(c.ROOT, [q.snapshots[CONNECTOR]], {})
        connector = code.native009_full75_dispatch_connection_v1
        connector.validate_metadata(proof, a)
        for pin in pins.values():
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):
                a.exact(q.pin(pin['path']), pin, 'ALL_UNCHANGED_QUALIFIED_PROGRAMS')
        for pin in [CONSTRUCTION]+construction.PINS+parent_code.READINESS+[parent_code.CONFIGURATION]:
            a.exact(q.pin(pin['path']), pin, 'CURRENT_CORE_COMPONENT')
        extra, _ = loader.load(c.ROOT, parent_code.READINESS, {})
        parts, _ = loader.load(c.ROOT, [pins[ENTRY], pins[LAUNCH], construction.DECLARATION, parent_code.CONFIGURATION], {})
        entry, parent = parts.native009_full75_worker_entry_v1, parts.native009_parent_launch_v1
        configuration = parts.current_queue_successor_lossless_runtime_v4
        for pin in configuration.PINS[1:]: a.exact(q.pin(pin['path']), pin, 'EXISTING_LOSSLESS_AND_SHARED_CODE')
        components, _ = loader.load(c.ROOT, configuration.PINS[1:], {})
        base = a.read_exact(q, proof['declared_scope_base_pin'])
        inherited = scope.extend(scope.pins(base['input_pins']), {proof['declared_scope_base_pin']['path']: proof['declared_scope_base_pin']})
        inherited = scope.extend(inherited, scope.pins(proof['declared_scope_delta_pins']))
        # The fixed parent proof, not the candidate or a best-effort glob, owns
        # the current graph pin. Metadata retains that proof as a fresh input.
        parent_proof = a.read_exact(q, pins['implementation/p09/evidence/p09-361-case165-native009-full75-parent-connection001.v1.json'])
        graph_pin = parent_proof['graph_report_pin']; prepared = a.read_exact(q, graph_pin); hint = a.read_exact(q, entry.HINT)
        a.exact(entry.HINT, prepared['bootstrap_pin'], 'CURRENT_V5_HINT'); a.exact(entry.WIRE, prepared['capsule_pin'], 'CURRENT_V5_WIRE')
        transports, _ = loader.load(c.ROOT, [entry.TRANSPORT], {})
        facade = NS(connect=transports.native009_full75_transport_v1.connect, constant=libs.native009_full72_transport_v1.constant)
        source = libs.native009_verified_source_profile_v1.connect(c.ROOT, loader, scope, bytes_policy,
            libs.receipt_xz_envelope_v1, libs.bounded_successor_capsule_wire_v2, guard.check, a, q, hint, facade)
        pin, raw = q._read(entry.WIRE['path'], parse=True); q._bind(pin['path'], pin); a.exact(pin, entry.WIRE, 'ACTUAL_CURRENT_PACKET')
        api = source.api; graph, _ = api.reconstruct(hint, bytes(raw), guard.check); del raw
        inherited, _ = graph.binding.semantic_union(inherited, guard.check)
        a.exact(len(inherited), proof['semantic_inputs'], 'WHOLE_SAVED3259_NOT_399_SOURCE_SUBSET')
        original_union = type(graph.binding).semantic_union
        parts.native009_parent_scope_v1.inherit_declaration(graph, inherited, scope)
        launch = entry.launch_api(c.ROOT, loader)
        proxy, context = parent.recovery_api(libs.post_product_recovery_connection_v1, c.ROOT, q.snapshots[ENTRY], launch,
            extra.worker_readiness_v1, extra.worker_readiness_connection_v1, c)
        built = api.build(c.ROOT, loader, api, graph, envelope.prior, proxy, libs.post_product_recovery_window_v1, guard.check)
        old_budget = graph.binding.runtime_budget(inherited, proof['inventory_requests'], built.window.DIRECT.runtime_budget, guard.check)
        a.exact(old_budget, proof['original_complete_runtime_budget'], 'COMPLETE_PREVIOUS_SCOPE_AND_COST')
        configuration.configure(api.runtime, components)
        current_loader, oracle_state = connector.oracle_loader(c.ROOT, loader, configuration, api.metadata, a, construction.ORACLE)
        phase = 'ACTUAL_CURRENT_PARENT_AND_ADDITIONAL_ORACLE_CONNECTION'
        connected = construction.construct(c.ROOT, current_loader, api, graph, built, envelope, libs.post_product_recovery_connection_v1,
            libs.post_product_recovery_window_v1, a, q, scope, inherited, prepared, graph_pin, guard.check)
        context.bind_parent(connected.parent_state)
        row['independent_accounting_connection'] = connector.verify_checker(connected.checker, graph, configuration)
        helpers = construction.helper_inventory(c.ROOT, connected.parent)
        require(helpers['Native_count'] <= 64 and oracle_state.loads == 1, 'ACTUAL_HELPER64_AND_ONE_EXISTING_ORACLE')
        for name in helpers['original_Native_helper_union']: q.pin(name)
        row['helper_inventory'] = helpers
        shared = parent_code.shared_owner(connected.frame)
        require(shared.metadata is None and shared.frame is None and not shared.restored, 'FRESH_SHARED_OWNER_NOT_REUSED_METADATA_WORK')
        # Existing accounting's entire checker is tested using its real source,
        # but these small connector contracts never manufacture a Native row.
        phase = 'NEW_CONNECTION_CONTRACTS'
        tests, _ = loader.load(c.ROOT, [q.snapshots[TEST]], {'native009_full75_dispatch_connection_v1': connector})
        result = unittest.TextTestRunner(stream=io.StringIO(), failfast=True).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests.test_native009_full75_dispatch_connection_v1))
        row['contracts'] = dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped))
        row['contract_failures'] = [dict(test=t.id().rsplit('.', 1)[-1], exception_type=trace.splitlines()[-1].split(':', 1)[0])
            for t, trace in result.errors+result.failures]
        a.exact(row['contracts'], dict(run=7, errors=0, failures=0, skipped=0), 'NEW_CONNECTION7')
        phase = 'CURRENT_FULL_DECLARATION_AND_COST'
        required, _ = graph.binding.semantic_union(scope.extend(connected.oracle_inherited, q.snapshots), guard.check)
        require(all(required.get(n) == pin for n, pin in inherited.items()), 'NO_PRIOR_INPUT_REMOVED')
        inventory = a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'), ('rust_inputs',), dict(os=os, Path=Path, require=require))
        requests = []
        def paced(): requests.append(1); q.open_pacer.reserve()
        rust = inventory.rust_inputs(c.ROOT, paced)
        require(len(rust) == 787 and set(rust) <= set(required), 'CURRENT_RUST787')
        budget = graph.binding.runtime_budget(required, len(requests), built.window.DIRECT.runtime_budget, guard.check)
        total = budget['predicted_runtime_combined_seconds']+15
        _, delta = parent_code.compact_scope(graph.binding, original_union, scope, base, proof['declared_scope_base_pin'], required, guard.check, a.exact)
        row.update(semantic_inputs=len(required), previous_scope_and_budget_exactly_reconstructed=True,
            declared_scope_base_pin=proof['declared_scope_base_pin'], declared_scope_delta_pins=delta,
            persisted_scope_uses_original_noninjecting_union=True, original_complete_runtime_budget=budget,
            predicted_complete_seconds_with_readiness=total, additional_readiness_seconds_without_old_credit=15,
            inventory_requests=len(requests), metadata_qualification_pin=METADATA, graph_report_pin=graph_pin,
            actual_parent_attempts=connected.parent_state.attempts, actual_worker_calls=built.state.calls,
            actual_Frame_instances=len(connected.parent_state.frames), original_metadata_callback_calls=len(connected.callback_calls),
            shared_owner_connected_but_unused=True, parent_context=context.evidence())
        require(total < 600, 'CURRENT_COMPLETE_SCOPE_PLUS_READY15_OUTSIDE600')
        require(context.attempts == context.jobs == connected.parent_state.attempts == built.state.calls == len(connected.parent_state.frames)
            == len(connected.callback_calls) == 0 and not denied and not native.exists(), 'NO_METADATA_FRAME_JOB_WORKER_OR_PRODUCT')
        phase = 'FINAL_QUALIFIER_HASHES'; q.finish(); guard.check(force=True)
        row.update(state='PASS_FULL75_CURRENT_DISPATCH_PARENT_AND_ADDITIONAL_ORACLE7_NOT_NATIVE_OR_PRODUCT',
            source_pins=list(q.snapshots.values()), fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, NameError) as error:
        row['error_type'] = type(error).__name__
        row['error_frames'] = [dict(file=Path(f.filename).name, function=f.name, line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-8:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}', error.args[0]): row['error_code'] = error.args[0]
    finally:
        if shared is not None: shared.restore()
        guard.close()
        row.update(cleanup_confirmed=guard.cleanup, operation_phase=phase, elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples), default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None), default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None), default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples), default=None), subprocess_creation_attempts=len(denied))
        if q is not None: row.update(observed_inputs=len(q.snapshots), closing_hashes_completed=q.final_fresh_hashes)
        row['last_original_resource_samples'] = [{k: s.get(k) for k in ('time_utc', 'system_cpu_percent', 'parent_cpu_machine_percent',
            'available_ram_percent', 'commit_used_percent', 'parent_private_mib')} for s in guard.samples[-8:]]
    require(guard.cleanup, 'OWNER_CLEANUP')
    libs.successor_preparation_workspace_v1.publish(c.ROOT, output, row, a)
    print(json.dumps({k: row.get(k) for k in ('state', 'contracts', 'contract_failures', 'semantic_inputs', 'fresh_inputs', 'final_fresh_hashes',
        'predicted_complete_seconds_with_readiness', 'elapsed_seconds', 'CPU_max', 'owned_CPU_machine_max', 'owned_private_MiB_max',
        'RAM_min', 'cleanup_confirmed', 'operation_phase', 'error_code', 'error_frames')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__ == '__main__': raise SystemExit(main())
