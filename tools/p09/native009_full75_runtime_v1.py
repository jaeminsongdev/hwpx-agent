"""One current75 entry for preparation qualification and actual Native009.

The same build function is used in both modes. Preparation never invokes the
whole metadata callback or parent. Native closes preparation before invoking
the unchanged owned entry exactly once; the original entry must freshly check
metadata, both full Native byte boundaries, worker Job/GO and complete capture.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

SELF = 'tools/p09/native009_full75_runtime_v1.py'
TEST = 'tools/p09/tests/test_native009_full75_runtime_v1.py'
PREFIX = 'implementation/p09/evidence/p09-361-case165-'
PROOF = dict(path=PREFIX+'native009-full75-dispatch-connection001.v1.json', bytes=104523,
    sha256='f433a721785d9501df673daf6fa99db2f0b14f2a20cf2cedb97cd882f40587d1')
CONSTRUCTION = dict(path='tools/p09/native009_full72_construction_v1.py', bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
PARENT = 'tools/p09/qualify_native009_full75_parent_v1.py'
ENTRY = 'tools/p09/native009_full75_worker_entry_v1.py'
LAUNCH = 'tools/p09/native009_parent_launch_v1.py'
CONNECTOR = 'tools/p09/native009_full75_dispatch_connection_v1.py'
NATIVE = PREFIX+'current-runtime-run009.v1.json'
CLAIM = PREFIX+'native009-full75-runtime-once-intent.v1.json'


def require(ok, label):
    if not ok: raise ValueError('FULL75_RUNTIME_'+label)


def unexecuted(built):
    require(built.context.attempts == built.context.jobs == built.connected.parent_state.attempts
        == built.engine.state.calls == len(built.connected.parent_state.frames) == len(built.connected.callback_calls) == 0,
        'UNEXECUTED_PARENT_FRAME_JOB_WORKER_METADATA')
    require(built.shared.metadata is None and built.shared.frame is None and not built.shared.restored,
        'FRESH_UNUSED_SHARED_OWNER')


class Once:
    def __init__(self): self.attempts = 0
    def execute(self, built, q, guard):
        require(self.attempts == 0, 'ONE_ENTRY_ATTEMPT_NO_RETRY')
        self.attempts += 1
        unexecuted(built)
        try: q.finish()
        finally: guard.close()
        require(guard.cleanup is True, 'PREPARATION_CLOSED_BEFORE_NATIVE_SAMPLER')
        return built.connected.outer(1)


def validate_qualification(row, a):
    a.fields(row, dict(state='PASS_FULL75_SAME_RUNTIME_ENTRY9_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE',
        contracts=dict(run=9, errors=0, failures=0, skipped=0), cleanup_confirmed=True,
        actual_product_or_Native_executed=False, GO_authorized=False, accepted_count_delta=0,
        actual_parent_attempts=0, actual_worker_calls=0, actual_Frame_instances=0, original_metadata_callback_calls=0,
        shared_owner_connected_but_unused=True, previous_scope_and_budget_exactly_reconstructed=True,
        persisted_scope_uses_original_noninjecting_union=True, additional_readiness_seconds_without_old_credit=15),
        'CURRENT_SAME_ENTRY_QUALIFICATION')
    require(type(row['fresh_inputs']) is int and row['fresh_inputs'] == row['final_fresh_hashes'] > 0,
        'ALL_QUALIFICATION_HASHES_CLOSED')
    require(type(row['predicted_complete_seconds_with_readiness']) is float
        and 0 < row['predicted_complete_seconds_with_readiness'] < 600, 'QUALIFIED_ORIGINAL600_NOT_COMPLETION_GUARANTEE')
    require(row['helper_inventory']['Native_count'] <= 64, 'QUALIFIED_ORIGINAL_HELPER64')


def build(c, a, q, loader, libs, construction, scope, bytes_policy, envelope):
    """Actual production construction, shared by --mode qualify and native."""
    proof = a.read_exact(q, PROOF); pins = scope.pins(proof['source_pins'])
    a.fields(proof, dict(state='PASS_FULL75_CURRENT_DISPATCH_PARENT_AND_ADDITIONAL_ORACLE7_NOT_NATIVE_OR_PRODUCT',
        contracts=dict(run=7, errors=0, failures=0, skipped=0), fresh_inputs=403, final_fresh_hashes=403,
        semantic_inputs=3263, actual_parent_attempts=0, actual_worker_calls=0, actual_Frame_instances=0,
        original_metadata_callback_calls=0, subprocess_creation_attempts=0, cleanup_confirmed=True), 'QUALIFIED_CURRENT_CONNECTION')
    for pin in pins.values():
        if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):
            a.exact(q.pin(pin['path']), pin, 'ALL_UNCHANGED_CONNECTION_PROGRAMS')
    for name in (SELF, TEST): q.pin(name)
    names, _ = loader.load(c.ROOT, [pins[PARENT], pins[ENTRY], pins[LAUNCH], pins[CONNECTOR]], {})
    parent_code = names.qualify_native009_full75_parent_v1
    entry, parent, connector = names.native009_full75_worker_entry_v1, names.native009_parent_launch_v1, names.native009_full75_dispatch_connection_v1
    metadata = a.read_exact(q, proof['metadata_qualification_pin']); connector.validate_metadata(metadata, a)
    for pin in [CONSTRUCTION]+construction.PINS+parent_code.READINESS+[parent_code.CONFIGURATION]:
        a.exact(q.pin(pin['path']), pin, 'CURRENT_CORE_COMPONENT')
    extra, _ = loader.load(c.ROOT, parent_code.READINESS+[parent_code.CONFIGURATION, construction.DECLARATION], {})
    configuration = extra.current_queue_successor_lossless_runtime_v4
    for pin in configuration.PINS[1:]: a.exact(q.pin(pin['path']), pin, 'EXISTING_LOSSLESS_SHARED_COMPONENTS')
    components, _ = loader.load(c.ROOT, configuration.PINS[1:], {})
    base = a.read_exact(q, proof['declared_scope_base_pin'])
    inherited = scope.extend(scope.pins(base['input_pins']), {proof['declared_scope_base_pin']['path']: proof['declared_scope_base_pin']})
    inherited = scope.extend(inherited, scope.pins(proof['declared_scope_delta_pins']))
    graph_pin = proof['graph_report_pin']; prepared = a.read_exact(q, graph_pin); hint = a.read_exact(q, entry.HINT)
    a.exact(entry.HINT, prepared['bootstrap_pin'], 'CURRENT_V5_HINT'); a.exact(entry.WIRE, prepared['capsule_pin'], 'CURRENT_V5_WIRE')
    transport, _ = loader.load(c.ROOT, [entry.TRANSPORT], {})
    facade = NS(connect=transport.native009_full75_transport_v1.connect, constant=libs.native009_full72_transport_v1.constant)
    source = libs.native009_verified_source_profile_v1.connect(c.ROOT, loader, scope, bytes_policy,
        libs.receipt_xz_envelope_v1, libs.bounded_successor_capsule_wire_v2, q.checkpoint, a, q, hint, facade)
    pin, raw = q._read(entry.WIRE['path'], parse=True); q._bind(pin['path'], pin); a.exact(pin, entry.WIRE, 'ACTUAL_CURRENT_PACKET')
    api = source.api; graph, _ = api.reconstruct(hint, bytes(raw), q.checkpoint); del raw
    inherited, _ = graph.binding.semantic_union(inherited, q.checkpoint)
    a.exact(len(inherited), proof['semantic_inputs'], 'WHOLE_SAVED3263_NOT_SOURCE_PIN_SUBSET')
    original_union = type(graph.binding).semantic_union
    extra.native009_parent_scope_v1.inherit_declaration(graph, inherited, scope)
    launch = entry.launch_api(c.ROOT, loader)
    proxy, context = parent.recovery_api(libs.post_product_recovery_connection_v1, c.ROOT, q.snapshots[ENTRY], launch,
        extra.worker_readiness_v1, extra.worker_readiness_connection_v1, c)
    engine = api.build(c.ROOT, loader, api, graph, envelope.prior, proxy, libs.post_product_recovery_window_v1, q.checkpoint)
    old_budget = graph.binding.runtime_budget(inherited, proof['inventory_requests'], engine.window.DIRECT.runtime_budget, q.checkpoint)
    a.exact(old_budget, proof['original_complete_runtime_budget'], 'WHOLE_PREVIOUS_SCOPE_COST')
    configuration.configure(api.runtime, components)
    current_loader, oracle_state = connector.oracle_loader(c.ROOT, loader, configuration, api.metadata, a, construction.ORACLE)
    connected = construction.construct(c.ROOT, current_loader, api, graph, engine, envelope, libs.post_product_recovery_connection_v1,
        libs.post_product_recovery_window_v1, a, q, scope, inherited, prepared, graph_pin, q.checkpoint)
    context.bind_parent(connected.parent_state)
    accounting = connector.verify_checker(connected.checker, graph, configuration)
    helpers = construction.helper_inventory(c.ROOT, connected.parent)
    require(helpers['Native_count'] <= 64 and oracle_state.loads == 1, 'ACTUAL_CURRENT_HELPER64_AND_ACCOUNTING')
    for name in helpers['original_Native_helper_union']: q.pin(name)
    value = NS(connected=connected, context=context, engine=engine, graph=graph, api=api, source=source,
        shared=parent_code.shared_owner(connected.frame), inherited=inherited, base=base, proof=proof,
        parent_code=parent_code, original_union=original_union, helpers=helpers, accounting=accounting)
    unexecuted(value)
    return value


def current_cost(value, q, a, scope):
    import os
    required, _ = value.graph.binding.semantic_union(scope.extend(value.connected.oracle_inherited, q.snapshots), q.checkpoint)
    require(all(required.get(n) == pin for n, pin in value.inherited.items()), 'NO_PREVIOUS_INPUT_REMOVED')
    inventory = a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'), ('rust_inputs',), dict(os=os, Path=Path, require=require))
    requests = []
    def paced(): requests.append(1); q.open_pacer.reserve()
    rust = inventory.rust_inputs(q.root, paced)
    require(len(rust) == 787 and set(rust) <= set(required), 'CURRENT_RUST787')
    budget = value.graph.binding.runtime_budget(required, len(requests), value.engine.window.DIRECT.runtime_budget, q.checkpoint)
    total = budget['predicted_runtime_combined_seconds']+15
    require(total < 600, 'COMPLETE_CURRENT_SCOPE_PLUS_READY15_OUTSIDE600')
    _, delta = value.parent_code.compact_scope(value.graph.binding, value.original_union, scope, value.base,
        value.proof['declared_scope_base_pin'], required, q.checkpoint, a.exact)
    return dict(semantic_inputs=len(required), original_complete_runtime_budget=budget, predicted_complete_seconds_with_readiness=total,
        declared_scope_base_pin=value.proof['declared_scope_base_pin'], declared_scope_delta_pins=delta,
        persisted_scope_uses_original_noninjecting_union=True, previous_scope_and_budget_exactly_reconstructed=True,
        additional_readiness_seconds_without_old_credit=15, inventory_requests=len(requests))


def main():
    import argparse, io, re, time, traceback, unittest
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    parser = argparse.ArgumentParser(); parser.add_argument('--mode', choices=('qualify', 'native'), required=True)
    parser.add_argument('--attempt', type=int, required=True); parser.add_argument('--qualification-attempt', type=int)
    args = parser.parse_args()
    require(1 <= args.attempt <= 8 and (args.mode != 'native' or args.qualification_attempt in range(1, 9)), 'FINITE_EXPLICIT_MODE')
    denied = []
    if args.mode == 'qualify':
        def audit(event, values):
            if event == 'subprocess.Popen': denied.append(1); raise ValueError('FULL75_RUNTIME_QUALIFICATION_ALL_SUBPROCESS_DENIED')
        sys.addaudithook(audit)
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import audit_evidence_io as original_io
    original, _ = envelope.namespace_bundle.load(c.ROOT, [CONSTRUCTION], {})
    construction = original.native009_full72_construction_v1
    libs, _ = envelope.namespace_bundle.load(c.ROOT, construction.PINS, {})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader, _ = libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle, libs.ast_clone_namespace_v1)
    loader, _ = construction.private_runtime_imports(loader)
    qualification_path = PREFIX+f'native009-full75-runtime-entry-qualification{(args.attempt if args.mode == "qualify" else args.qualification_attempt):03}.v1.json'
    output = qualification_path if args.mode == 'qualify' else PREFIX+f'native009-full75-runtime-entry-stop{args.attempt:03}.v1.json'
    require(not (c.ROOT/output).exists() and not (c.ROOT/NATIVE).exists() and not (c.ROOT/CLAIM).exists(), 'EXCLUSIVE_NATIVE009_NO_REPLAY')
    guard = libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(
        libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started, phase = time.monotonic(), 'CURRENT_ADMISSION'
    q = value = None
    row = dict(state='FAILED_FULL75_RUNTIME_ENTRY_NOT_NATIVE', accepted_count_delta=0, GO_authorized=False,
        actual_product_or_Native_executed=False, current_result_and_future_sources_must_be_recosted=True,
        preparation_CPU_policy_changed=False, whole_current_Native_source_or_product_acceptance_qualified=False)
    try:
        guard.acquire(); seed = a.AcceptanceReader(c.ROOT, guard.check)
        proof = a.read_exact(seed, PROOF); pins = scope.pins(proof['source_pins'])
        parent, _ = loader.load(c.ROOT, [pins[PARENT]], {})
        source = parent.qualify_native009_full75_parent_v1
        readers, _ = loader.load(c.ROOT, [source.SNAPSHOT, source.CHUNK], {'audit_evidence_io': original_io})
        snapshot, chunk = readers.single_snapshot_source_guard_v1, readers.reusable_audit_chunk_v1
        pin, raw = seed._read(snapshot.ORIGINAL_PIN['path'], parse=True); seed._bind(pin['path'], pin)
        a.exact(pin, snapshot.ORIGINAL_PIN, 'UNCHANGED_ORIGINAL_READER')
        SourceReader, _ = snapshot.reader_type(a.AcceptanceReader, bytes(raw)); Reader, _ = chunk.reader_type(SourceReader, bytes(raw)); del raw
        q = Reader(c.ROOT, guard.check)
        for pin in seed.snapshots.values(): a.exact(q.pin(pin['path']), pin, 'FRESH_SEED_INPUTS')
        for name in (SELF, TEST): q.pin(name)
        if args.mode == 'native':
            qualified = q.json(qualification_path); validate_qualification(qualified, a)
            sealed = scope.pins(qualified['source_pins'])
            for name in (SELF, TEST): a.exact(q.snapshots[name], sealed[name], 'EXACT_SAME_QUALIFIED_ENTRY_AND_TEST')
            for pin in qualified['source_pins']:
                if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'): a.exact(q.pin(pin['path']), pin, 'ALL_UNCHANGED_QUALIFIED_ENTRY_SOURCES')
            # Durable exclusive intent prevents a new process from replaying a
            # lost observation. This is not a Native result or GO/PASS claim.
            intent = dict(state='EXCLUSIVE_NATIVE009_ENTRY_INTENT_NOT_GO_OR_COMPLETION', index=165, physical_run=9,
                task='case165-current-r009-tests', runtime_path=NATIVE, entry_pin=q.snapshots[SELF],
                qualification_pin=q.snapshots[qualification_path], product_execution_state='NOT_YET_OBSERVED')
            libs.successor_preparation_workspace_v1.publish(c.ROOT, CLAIM, intent, a); q.pin(CLAIM)
        phase = 'SAME_CURRENT_RUNTIME_CONSTRUCTION'
        value = build(c, a, q, loader, libs, construction, scope, bytes_policy, envelope)
        row.update(current_cost(value, q, a, scope))
        row.update(helper_inventory=value.helpers, independent_accounting_connection=value.accounting,
            actual_parent_attempts=0, actual_worker_calls=0, actual_Frame_instances=0, original_metadata_callback_calls=0,
            shared_owner_connected_but_unused=True, construction_qualification_pin=PROOF)
        if args.mode == 'qualify':
            phase = 'SAME_ENTRY_CONTRACTS'
            tests, _ = loader.load(c.ROOT, [q.snapshots[TEST]], {'native009_full75_runtime_v1': sys.modules[__name__]})
            result = unittest.TextTestRunner(stream=io.StringIO(), failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests.test_native009_full75_runtime_v1))
            row['contracts'] = dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped))
            row['contract_failures'] = [dict(test=t.id().rsplit('.', 1)[-1], exception_type=trace.splitlines()[-1].split(':', 1)[0]) for t, trace in result.errors+result.failures]
            a.exact(row['contracts'], dict(run=9, errors=0, failures=0, skipped=0), 'SAME_ENTRY9')
            unexecuted(value); require(not denied and not (c.ROOT/CLAIM).exists(), 'NO_SUBPROCESS_OR_EXECUTION_INTENT')
            phase = 'FINAL_QUALIFIER_HASHES'; q.finish(); guard.check(force=True)
            row.update(state='PASS_FULL75_SAME_RUNTIME_ENTRY9_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE',
                source_pins=list(q.snapshots.values()), fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes)
        else:
            # Do not pre-run the metadata callback. The entire original entry
            # owns its fresh metadata, sole sampler/Job and both Frame reads.
            phase = 'ORIGINAL_NATIVE009_ENTRY_ONCE'
            code = Once().execute(value, q, guard)
            print(json.dumps(dict(state='NATIVE009_ENTRY_RETURNED_REQUIRES_INDEPENDENT_REVIEW', exit_code=code,
                runtime_path=NATIVE, native_result_exists=(c.ROOT/NATIVE).exists(), accepted_count_delta=0)))
            return code
    except (ValueError, OSError, KeyError, TypeError, AttributeError, NameError) as error:
        row['error_type'] = type(error).__name__
        row['error_frames'] = [dict(file=Path(f.filename).name, function=f.name, line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-8:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}', error.args[0]): row['error_code'] = error.args[0]
        if phase == 'ORIGINAL_NATIVE009_ENTRY_ONCE':
            row['actual_product_or_Native_executed'] = None
            row['state'] = 'NATIVE009_ENTRY_EXCEPTION_EXECUTION_UNKNOWN_NO_RETRY'
    finally:
        if value is not None: value.shared.restore()
        guard.close()
        row.update(cleanup_confirmed=guard.cleanup, operation_phase=phase, elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples), default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None), default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None), default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples), default=None), subprocess_creation_attempts=len(denied))
        if q is not None: row.update(observed_inputs=len(q.snapshots), closing_hashes_completed=q.final_fresh_hashes)
        row['last_original_resource_samples'] = [{k: s.get(k) for k in ('time_utc', 'system_cpu_percent', 'parent_cpu_machine_percent',
            'available_ram_percent', 'commit_used_percent', 'parent_private_mib')} for s in guard.samples[-8:]]
    require(guard.cleanup, 'PREPARATION_OWNER_CLEANUP')
    libs.successor_preparation_workspace_v1.publish(c.ROOT, output, row, a)
    print(json.dumps({k: row.get(k) for k in ('state', 'contracts', 'contract_failures', 'semantic_inputs', 'fresh_inputs', 'final_fresh_hashes',
        'predicted_complete_seconds_with_readiness', 'elapsed_seconds', 'CPU_max', 'owned_CPU_machine_max', 'owned_private_MiB_max',
        'RAM_min', 'cleanup_confirmed', 'operation_phase', 'error_code', 'error_frames')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__ == '__main__': raise SystemExit(main())
