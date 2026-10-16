"""Actual75 worker in the original parent/Job/Frame/oracle construction.

Keep all inherited pins, original20 contracts and original live guards. Connect
the existing shared metadata/Frame budget before construction, never execute
metadata, a Frame, a parent, a worker or a product in this qualification.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

SELF = 'tools/p09/qualify_native009_full75_parent_v1.py'
PREFIX = 'implementation/p09/evidence/p09-361-case165-'
WORKER = dict(path=PREFIX+'native009-full75-production-worker002.v1.json', bytes=103989,
    sha256='c30e3ace79dd3884614195770893b2be146fe1975ec9cc9e59c09342f8100969')
CONSTRUCTION = dict(path='tools/p09/native009_full72_construction_v1.py', bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
ENTRY = 'tools/p09/native009_full75_worker_entry_v1.py'
PARENT = 'tools/p09/native009_parent_launch_v1.py'
TEST = 'tools/p09/tests/test_native009_parent_launch_v1.py'
SNAPSHOT = dict(path='tools/p09/single_snapshot_source_guard_v1.py', bytes=4560,
    sha256='f3555f4395154be7c929e76eeb451226402b49cc54b0ab6da335ba94555eae43')
CHUNK = dict(path='tools/p09/reusable_audit_chunk_v1.py', bytes=8088,
    sha256='1aa1db74585cbdf50df32ac0c9dc07dfd31557fc37647ca6e6ea3969fbb60e75')
CONFIGURATION = dict(path='tools/p09/current_queue_successor_lossless_runtime_v4.py', bytes=18227,
    sha256='8ff8d105e753e2727b7fe4294f1e2b6fe6d670bd9d12e69afac5946888602db8')
READINESS = [dict(path='tools/p09/worker_readiness_v1.py', bytes=6890,
    sha256='047c3f78f8a4472feeec4d56b65716f57e0429091321cb49afe5b685047d3a45'),
    dict(path='tools/p09/worker_readiness_connection_v1.py', bytes=5775,
    sha256='d306d62a08e16f717bb526b2a7fa6c60ac44890f6fed965fdf4a70daca3c0a9b')]


def require(ok, label):
    if not ok: raise ValueError('FULL75_PARENT_'+label)


def compact_scope(binding, original_union, scope, base, base_pin, required, checkpoint, exact):
    # Never let the later live declaration injector normalize a saved basis.
    require(original_union.__name__ == 'semantic_union' and original_union.__code__.co_filename.replace('\\', '/').endswith(
        'prior_preparation_alias_v1.py') and set(original_union.__code__.co_freevars) == {'index', 'module', 'original', 'pairs'},
        'ORIGINAL_NONINJECTING_UNION_FOR_PERSISTED_BASE')
    explicit = scope.extend(scope.pins(base['input_pins']), {base_pin['path']: base_pin})
    baseline, _ = original_union(binding, explicit, checkpoint)
    delta = sorted((p for n, p in required.items() if n not in baseline), key=lambda p: p['path'])
    exact(scope.extend(baseline, scope.pins(delta)), required, 'INDEPENDENT_SAVED_BASE_AND_DELTA_FULL_ROUNDTRIP')
    replay, _ = original_union(binding, scope.extend(explicit, scope.pins(delta)), checkpoint)
    exact(replay, required, 'RAW_SAVED_BASE_AND_DELTA_REPLAY_WITHOUT_HIDDEN_INHERITANCE')
    return baseline, delta


def shared_owner(frame):
    owners = []
    for cls in frame.__mro__:
        fn = vars(cls).get('__init__')
        if callable(fn) and getattr(fn, '__closure__', None) and fn.__code__.co_filename.replace('\\', '/').endswith(
            'shared_metadata_frame_decoder_budget_v1.py'):
            cells = dict(zip(fn.__code__.co_freevars, (cell.cell_contents for cell in fn.__closure__)))
            if 'shared' in cells: owners.append(cells['shared'])
    require(len(owners) == 1, 'ONE_CURRENT_SHARED_METADATA_FRAME_OWNER')
    return owners[0]


def main():
    import argparse, importlib.util, io, os, re, time, traceback, unittest
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    denied = []
    def audit(event, args):
        if event == 'subprocess.Popen': denied.append(1); raise ValueError('FULL75_PARENT_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(audit)
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import audit_evidence_io as original_io
    initial, _ = envelope.namespace_bundle.load(c.ROOT, [CONSTRUCTION], {})
    construction = initial.native009_full72_construction_v1
    libs, _ = envelope.namespace_bundle.load(c.ROOT, construction.PINS+READINESS, {})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader, _ = libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle, libs.ast_clone_namespace_v1)
    loader, imports = construction.private_runtime_imports(loader)
    parser = argparse.ArgumentParser(); parser.add_argument('--attempt', type=int, required=True)
    attempt = parser.parse_args().attempt
    require(type(attempt) is int and 1 <= attempt <= 8, 'BOUNDED_ATTEMPT')
    output = PREFIX+f'native009-full75-parent-connection{attempt:03}.v1.json'
    native = c.ROOT/(PREFIX+'current-runtime-run009.v1.json')
    require(not (c.ROOT/output).exists() and not native.exists(), 'EXCLUSIVE_REPORT_AND_NO_NATIVE009')
    guard = libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(
        libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started, phase = time.monotonic(), 'CURRENT_ADMISSION'
    q = chunk = None
    row = dict(state='FAILED_FULL75_PARENT_CONNECTION_NOT_NATIVE', accepted_count_delta=0, GO_authorized=False,
        actual_product_or_Native_executed=False, whole_current_byte_Frame_and_dispatch_qualified=False,
        preparation_CPU_policy_changed=False, current_result_and_future_dispatch_sources_must_be_recosted=True)
    try:
        guard.acquire(); seed = a.AcceptanceReader(c.ROOT, guard.check)
        for pin in (SNAPSHOT, CHUNK): a.exact(seed.pin(pin['path']), pin, 'CURRENT_QUALIFIED_READER_HELPER')
        names, _ = loader.load(c.ROOT, [SNAPSHOT, CHUNK], {'audit_evidence_io': original_io})
        snapshot, chunk = names.single_snapshot_source_guard_v1, names.reusable_audit_chunk_v1
        pin, raw = seed._read(snapshot.ORIGINAL_PIN['path'], parse=True); seed._bind(pin['path'], pin)
        a.exact(pin, snapshot.ORIGINAL_PIN, 'ORIGINAL_IO_LEAF')
        SourceReader, _ = snapshot.reader_type(a.AcceptanceReader, bytes(raw))
        Reader, reader_proof = chunk.reader_type(SourceReader, bytes(raw)); del raw
        q = Reader(c.ROOT, guard.check)
        for pin in seed.snapshots.values(): a.exact(q.pin(pin['path']), pin, 'FRESH_BOOTSTRAP')
        q.pin(SELF)
        for pin in [CONSTRUCTION]+construction.PINS+READINESS: a.exact(q.pin(pin['path']), pin, 'CURRENT_CORE_SOURCES')
        worker = a.read_exact(q, WORKER)
        a.fields(worker, dict(state='PASS_FULL75_PRODUCTION_MAIN_EOF_AND_PRODUCT_DENIED18_WITH_REPLAYABLE_DECLARED_COST_NOT_NATIVE',
            contracts=dict(run=18, errors=0, failures=0, skipped=0), fresh_inputs=400, final_fresh_hashes=400,
            semantic_inputs=3255, cleanup_confirmed=True, actual_product_or_Native_executed=False,
            previous_scope_and_budget_exactly_reconstructed=True, persisted_scope_uses_original_noninjecting_union=True,
            parent_cost_graph_worker_calls=0, diagnostic_child_launches=2, denied_unexpected_parent_launches=0), 'REAL75_WORKER_DIAGNOSTICS18')
        oldpins = scope.pins(worker['source_pins'])
        for pin in oldpins.values():
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):
                a.exact(q.pin(pin['path']), pin, 'ALL_CURRENT_WORKER_QUALIFIED_CODE')
        base = a.read_exact(q, worker['declared_scope_base_pin'])
        inherited = scope.extend(scope.pins(base['input_pins']), {worker['declared_scope_base_pin']['path']: worker['declared_scope_base_pin']})
        inherited = scope.extend(inherited, scope.pins(worker['declared_scope_delta_pins']))
        graph_pin = worker['graph_report_pin']
        a.exact(graph_pin, oldpins[PREFIX+'successor-native009-full75-graph001.v1.json'], 'CURRENT_PREPARED75_GRAPH_PIN')
        prepared = a.read_exact(q, graph_pin); hint = a.read_exact(q, prepared['bootstrap_pin'])
        parts, _ = loader.load(c.ROOT, [oldpins[ENTRY], oldpins[PARENT], construction.DECLARATION], {})
        entry, parent = parts.native009_full75_worker_entry_v1, parts.native009_parent_launch_v1
        for pin in (entry.PREVIOUS, entry.OLD_ENTRY, entry.OLD_LAUNCH, entry.TRANSPORT, entry.HINT, entry.WIRE, entry.STEP, *entry.EARLY_AST):
            a.exact(q.pin(pin['path']), pin, 'EXACT_CURRENT_WORKER_DEPENDENCY')
        a.exact(entry.HINT, prepared['bootstrap_pin'], 'EXACT_V5_HINT'); a.exact(entry.WIRE, prepared['capsule_pin'], 'EXACT_V5_CAPSULE')
        transports, _ = loader.load(c.ROOT, [entry.TRANSPORT], {})
        transport = NS(connect=transports.native009_full75_transport_v1.connect, constant=libs.native009_full72_transport_v1.constant)
        source = libs.native009_verified_source_profile_v1.connect(c.ROOT, loader, scope, bytes_policy, libs.receipt_xz_envelope_v1,
            libs.bounded_successor_capsule_wire_v2, guard.check, a, q, hint, transport)
        pin, wire = q._read(entry.WIRE['path'], parse=True); q._bind(pin['path'], pin); a.exact(pin, entry.WIRE, 'CURRENT_FULL75_PACKET')
        api = source.api; graph, _ = api.reconstruct(hint, bytes(wire), guard.check); del wire
        inherited, _ = graph.binding.semantic_union(inherited, guard.check)
        a.exact(len(inherited), worker['semantic_inputs'], 'COMPLETE_PREVIOUS3255_NOT_FRESH_SUBSET')
        original_union = type(graph.binding).semantic_union
        parts.native009_parent_scope_v1.inherit_declaration(graph, inherited, scope)
        launch = entry.launch_api(c.ROOT, loader)
        proxy, context = parent.recovery_api(libs.post_product_recovery_connection_v1, c.ROOT, q.snapshots[ENTRY], launch,
            libs.worker_readiness_v1, libs.worker_readiness_connection_v1, c)
        phase = 'CURRENT75_PARENT_AND_SHARED_BUDGET_CONSTRUCTION'
        built = api.build(c.ROOT, loader, api, graph, envelope.prior, proxy, libs.post_product_recovery_window_v1, guard.check)
        prior_budget = graph.binding.runtime_budget(inherited, worker['inventory_requests'], built.window.DIRECT.runtime_budget, guard.check)
        a.exact(prior_budget, worker['original_complete_runtime_budget'], 'EXACT_PREVIOUS_WHOLE_COST')
        for pin in [construction.ORACLE, construction.LEGACY, construction.DISPATCH, construction.DECLARATION]:
            a.exact(q.pin(pin['path']), pin, 'UNCHANGED_PARENT_AND_INDEPENDENT_ORACLE_CODE')
        a.exact(q.pin(CONFIGURATION['path']), CONFIGURATION, 'CURRENT_EXISTING_SHARED_CONFIGURATION')
        configurations, _ = loader.load(c.ROOT, [CONFIGURATION], {})
        configuration = configurations.current_queue_successor_lossless_runtime_v4
        for pin in configuration.PINS[1:]: a.exact(q.pin(pin['path']), pin, 'EXACT_EXISTING_SHARED_READER_COMPONENTS')
        components, _ = loader.load(c.ROOT, configuration.PINS[1:], {})
        configuration.configure(api.runtime, components)
        connected = construction.construct(c.ROOT, loader, api, graph, built, envelope, libs.post_product_recovery_connection_v1,
            libs.post_product_recovery_window_v1, a, q, scope, inherited, prepared, graph_pin, guard.check)
        context.bind_parent(connected.parent_state)
        shared = shared_owner(connected.frame)
        helpers = construction.helper_inventory(c.ROOT, connected.parent); row['helper_inventory'] = helpers
        require(helpers['Native_count'] <= 64, 'ACTUAL_ORIGINAL_HELPER64_BEFORE_TESTS')
        for name in helpers['original_Native_helper_union']: q.pin(name)
        phase = 'CURRENT_FULL75_PARENT_CONNECTION_CONTRACTS'
        suites, inverses = [], []
        for name, path, method in (
            ('full75_original_construction_contracts', construction.TEST, 'test_fresh_verified_Source_and_all72_failure_roles_preserved'),
            ('full75_parent_launch_contracts', TEST, 'test_actual_current_full72_and_independent_oracle_still_connected')):
            a.exact(q.pin(path), oldpins[path], 'ORIGINAL_CONTRACT_SOURCE')
            spec = importlib.util.spec_from_file_location(name, c.ROOT/path)
            tests = importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
            tests.MODULE = parent; tests.CONNECTED = connected; tests.CONTEXT = context; tests.SOURCE = source; tests.GRAPH = graph
            tests.HELPERS = helpers; tests.INHERITED = inherited; tests.SCOPE = scope; tests.API = api; tests.GUARD = guard
            tests.IMPORT_PROOFS = imports; tests.C = c; tests.LAUNCH = launch
            revised, inverse = libs.native009_full72_transport_v1.constant(getattr(tests.Tests, method), 72, 75, method, Path(path).name)
            setattr(tests.Tests, method, revised); inverses.append(inverse)
            suites.append(unittest.defaultTestLoader.loadTestsFromModule(tests))
        def current_worker_and_launch_metadata_connected():
            require(launch.ENTRY == ENTRY and launch.original_api.ENTRY != ENTRY, 'CURRENT_ENTRY_ONLY_PRIVATE')
            require(len(context.windows) == 1 and context.parent is connected.parent_state, 'ONE_CURRENT_PARENT_WINDOW')
            require(connected.built is built and len(graph.binding.descriptors()) == 75, 'SAME_FULL75_PARENT_ENGINE')
        def original_limits_and_unexecuted_parent_preserved():
            require(built.window.WINDOW.SECONDS == 10 and libs.worker_readiness_v1.SECONDS == 15, 'PRODUCT10_READY15')
            require(context.jobs == context.attempts == context.frame_checks == len(context.bindings) == 0, 'NO_REAL_JOB_FRAME_OR_PARENT_EXECUTION')
            require(not connected.parent_state.frames and not connected.callback_calls and not connected.checker.projectors, 'NO_RUNTIME_OR_ACCEPTANCE_CALLS')
        def complete_previous_scope_and_cost_preserved():
            a.exact(prior_budget, worker['original_complete_runtime_budget'], 'NO_MISSING_PREVIOUS_COST_INPUTS')
            require(len(inherited) == 3255 and all(connected.oracle_inherited.get(n) == p for n, p in inherited.items()), 'ALL_PREVIOUS_DECLARED_INPUTS')
        def compact_scope_replays_without_live_inheritance_injection():
            baseline, delta = compact_scope(graph.binding, original_union, scope, base, worker['declared_scope_base_pin'], inherited, guard.check, a.exact)
            require(len(baseline) == 3191 and len(delta) == 64, 'ORIGINAL_BASE3191_AND_ALL64_SAVED_DELTA')
        def injecting_normalizer_is_rejected_for_persisted_scope():
            try: compact_scope(graph.binding, type(graph.binding).semantic_union, scope, base, worker['declared_scope_base_pin'], inherited, guard.check, a.exact)
            except ValueError as error:
                require(error.args == ('FULL75_PARENT_ORIGINAL_NONINJECTING_UNION_FOR_PERSISTED_BASE',), 'EXACT_INJECTING_NORMALIZER_REJECTION')
            else: raise ValueError('FULL75_PARENT_INJECTING_BASE_ACCEPTED')
        def both_new149_failure_roles_are_in_actual_parent():
            projection, _ = graph.binding.project(inherited, guard.check)
            role = graph.binding.representation(projection)['legacy149_validation_failures_provenance']
            a.exact(role, hint['legacy149_validation_failure_declarations'], 'PARENT_EXACT_TWO149_ROLES')
            require([r['original_stop_reason'] for r in role['records']] == ['OWNED_RUNNER_FAILURE', 'STOP_LOW_AVAILABLE_RAM']
                and all(r['actual_failed_product_child_executed'] is None and r['original_failure_promoted'] is False for r in role['records']),
                'BOTH_DISTINCT_UNKNOWN_FAILURES_NEVER_PREBODY_OR_PASS')
        def existing_shared_budget_owner_is_fresh_and_unused():
            require(shared is shared_owner(connected.frame) and shared.metadata is None and shared.frame is None, 'ONE_FRESH_UNREGISTERED_SHARED_OWNER')
            require(not connected.callback_calls and not connected.parent_state.frames, 'NO_METADATA_OR_FRAME_EXECUTION_IN_CONSTRUCTION')
        suites.append(unittest.TestSuite(unittest.FunctionTestCase(fn) for fn in (
            current_worker_and_launch_metadata_connected, original_limits_and_unexecuted_parent_preserved,
            complete_previous_scope_and_cost_preserved, compact_scope_replays_without_live_inheritance_injection,
            injecting_normalizer_is_rejected_for_persisted_scope, both_new149_failure_roles_are_in_actual_parent,
            existing_shared_budget_owner_is_fresh_and_unused)))
        result = unittest.TextTestRunner(stream=io.StringIO(), failfast=True).run(unittest.TestSuite(suites))
        row['contracts'] = dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped))
        row['contract_failures'] = [dict(test=t.id().rsplit('.', 1)[-1], exception_type=trace.splitlines()[-1].split(':', 1)[0],
            error_code=(m[1] if (m := re.fullmatch(r'(?:ValueError|RuntimeError): ([A-Z0-9_]{1,160})', trace.splitlines()[-1])) else None))
            for t, trace in result.errors+result.failures]
        a.exact(row['contracts'], dict(run=27, errors=0, failures=0, skipped=0), 'ORIGINAL20_AND_CURRENT7')
        row['whole_original_contract_count_slot_inverses'] = inverses
        phase = 'CURRENT_COMPLETE_SCOPE_AND_COST'
        for module in tuple(sys.modules.values()):
            filename = getattr(module, '__file__', None)
            if filename:
                path = Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix == '.py': q.pin(path.relative_to(c.ROOT).as_posix())
        required, _ = graph.binding.semantic_union(scope.extend(connected.oracle_inherited, q.snapshots), guard.check)
        require(all(required.get(n) == p for n, p in inherited.items()), 'NO_PREVIOUS_INPUT_REMOVED')
        inventory = a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'), ('rust_inputs',), dict(os=os, Path=Path, require=require))
        requests = []
        def paced(): requests.append(1); q.open_pacer.reserve()
        rust = inventory.rust_inputs(c.ROOT, paced); require(len(rust) == 787 and set(rust) <= set(required), 'CURRENT_RUST787')
        budget = graph.binding.runtime_budget(required, len(requests), built.window.DIRECT.runtime_budget, guard.check)
        total = budget['predicted_runtime_combined_seconds']+15
        _, delta = compact_scope(graph.binding, original_union, scope, base, worker['declared_scope_base_pin'], required, guard.check, a.exact)
        row.update(previous_scope_and_budget_exactly_reconstructed=True, semantic_inputs=len(required),
            current_Rust_path_count=len(rust), inventory_requests=len(requests), original_complete_runtime_budget=budget,
            predicted_complete_seconds_with_readiness=total, declared_cost_nominal_fits600=total < 600,
            additional_readiness_seconds_without_old_credit=15, declared_scope_base_pin=worker['declared_scope_base_pin'],
            declared_scope_delta_pins=delta, persisted_scope_uses_original_noninjecting_union=True,
            parent_context=context.evidence(), actual_parent_attempts=connected.parent_state.attempts,
            actual_worker_calls=built.state.calls, actual_Frame_instances=len(connected.parent_state.frames),
            shared_decoder_configuration_pin=CONFIGURATION, shared_owner_connected_but_unused=True,
            preparation_reader_connection=reader_proof, worker_qualification_pin=WORKER, graph_report_pin=graph_pin)
        require(total < 600, 'COMPLETE_DECLARED_SCOPE_PLUS_READINESS_OUTSIDE600')
        phase = 'FINAL_METADATA_HASHES'; q.finish(); guard.check(force=True)
        require(not denied and not native.exists(), 'NO_SUBPROCESS_OR_NATIVE009')
        row.update(state='PASS_FULL75_PARENT_LAUNCH_JOB_FRAME_ORACLE_AND_SHARED_OWNER27_WITH_REPLAYABLE_DECLARED_COST_NOT_NATIVE',
            source_pins=list(q.snapshots.values()), fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, NameError) as error:
        row['error_type'] = type(error).__name__
        row['error_frames'] = [dict(file=Path(f.filename).name, function=f.name, line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}', error.args[0]): row['error_code'] = error.args[0]
    finally:
        if q is not None:
            row.update(fresh_inputs_observed=len(q.snapshots), closing_hashes_completed=q.final_fresh_hashes,
                metadata_read_passes=q.read_passes, metadata_physical_bytes=q.bytes_read,
                metadata_source_predicate_optimization=q.source_snapshot_diagnostics())
            if chunk is not None and hasattr(q, chunk.ATTRIBUTE): row['preparation_chunk_workspace'] = chunk.summary(q)
        row['last_original_guard_samples'] = guard.samples[-8:]
        guard.close()
        row.update(cleanup_confirmed=guard.cleanup, operation_phase=phase, elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples), default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None), default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None), default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples), default=None), subprocess_creation_attempts=len(denied))
    require(guard.cleanup, 'OWNER_CLEANUP')
    libs.successor_preparation_workspace_v1.publish(c.ROOT, output, row, a)
    print(json.dumps({k: row.get(k) for k in ('state', 'contracts', 'contract_failures', 'semantic_inputs',
        'predicted_complete_seconds_with_readiness', 'fresh_inputs', 'final_fresh_hashes', 'actual_parent_attempts',
        'actual_worker_calls', 'actual_Frame_instances', 'elapsed_seconds', 'CPU_max', 'owned_CPU_machine_max',
        'owned_private_MiB_max', 'RAM_min', 'cleanup_confirmed', 'operation_phase', 'error_code', 'error_frames')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__ == '__main__': raise SystemExit(main())
