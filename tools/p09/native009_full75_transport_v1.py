"""Exact75 worker packet; retain the whole original73 reconstruction chain.

Only fixed P149 aliases, typed descriptor-count/suffix slots and two named
closure dependencies change. Fresh Source, parser/hash/schema, all constructors,
worker/Frame/oracle bodies and product10 remain. Never dispatch a product here.
"""
import copy
import json
import sys
from types import FunctionType, SimpleNamespace as NS

SELF = 'tools/p09/native009_full75_transport_v1.py'
TEST = 'tools/p09/tests/test_native009_full75_transport_v1.py'
PREFIX = 'implementation/p09/evidence/p09-361-case165-'
FIELD = 'legacy149_validation_failure_declarations'
MANIFEST = PREFIX+'successor-native009-full75-manifest001.v1.json'
CAPSULE = PREFIX+'successor-worker-capsule009.compact.v5.json'
HINT = PREFIX+'successor-worker-bootstrap009.v5.json'
CODE = dict(path=PREFIX+'legacy149-binding-code003.v1.json', bytes=97562,
    sha256='40bd6b82fd1db97993b2916cff72909e51d113496e9a25971871e5ea2383bffd')
CONSTRUCTION = dict(path='tools/p09/native009_full72_construction_v1.py', bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
PINS = [dict(path='tools/p09/native009_full73_transport_v1.py', bytes=23590,
    sha256='ad415de73edfefbf6263266511807a707330480eac996697e36c9101bbf2bc26'),
    dict(path='tools/p09/legacy149_binding_v1.py', bytes=31313,
    sha256='d25516fbcd852df624ca98dad49eef0ca714bf0c799617b8a5e5e97a2f33ea7b'),
    dict(path='tools/p09/native009_full72_transport_v1.py', bytes=15741,
    sha256='441a0c98198d0442552004d918d4f6516e1c67e38a9de3585cd8e5a84612080e')]


def require(ok, label):
    if not ok: raise ValueError('NATIVE009_FULL75_'+label)


def graph_path(attempt):
    require(type(attempt) is int and 1 <= attempt <= 8, 'BOUNDED_GRAPH_ATTEMPT')
    return PREFIX+f'successor-native009-full75-graph{attempt:03}.v1.json'


def top_dependency(original, expected, replacement):
    require(type(original) is FunctionType and original.__name__ == 'reconstruct'
        and original.__code__.co_filename.replace('\\', '/').endswith('native009_full73_transport_v1.py'), 'EXACT_TOP73_BODY')
    before = original.__closure__; slots = list(original.__code__.co_freevars)
    require(before is not None and slots.count('reconstruction') == 1, 'ONE_NAMED_TOP_DEPENDENCY')
    index = slots.index('reconstruction')
    require(before[index].cell_contents is expected, 'EXACT_PRIOR_MIDDLE_RECONSTRUCTION')
    def cell(value): return (lambda: value).__closure__[0]
    cells = tuple(cell(replacement) if n == index else value for n, value in enumerate(before))
    fn = FunctionType(original.__code__, original.__globals__, name=original.__name__,
        argdefs=original.__defaults__, closure=cells)
    fn.__kwdefaults__ = original.__kwdefaults__
    undo = tuple(before[index] if n == index else value for n, value in enumerate(cells))
    require(fn.__code__ is original.__code__ and fn.__globals__ is original.__globals__
        and fn.__defaults__ is original.__defaults__ and all(a is b for a, b in zip(undo, before)), 'WHOLE_TOP_CODE_AND_CLOSURE_INVERSE')
    return fn, dict(dependency='reconstruction', closure_slot=index, entire_original_code_defaults_globals_retained=True,
        only_one_named_dependency_changed=True, entire_closure_inverse=True)


def connect(root, loader, scope, bytes_policy, xz, bounded, checkpoint, exact):
    libs, proofs = loader.load(root, PINS, {})
    previous, added, slots = libs.native009_full73_transport_v1, libs.legacy149_binding_v1, libs.native009_full72_transport_v1
    injected = []
    def load(actual_root, pins, reuse):
        names, proof = loader.load(actual_root, pins, reuse)
        if pins == previous.PINS:
            require(not injected, 'ONE_PRIVATE73_DEPENDENCY_INJECTION'); injected.append(True)
            old = names.legacy154_binding_v1
            def installed(module, prior72, admitted, codec, *, physical_run):
                before = old.install(module, prior72, admitted, codec, physical_run=physical_run)
                prior73 = copy.deepcopy(prior72)+[dict(schema_version=module.source.SCHEMA, next_case=165,
                    semantic_original_pin=copy.deepcopy(old.ORIGINAL), physical_envelope_pin=copy.deepcopy(old.PHYSICAL))]
                after = added.install(module, prior73, copy.deepcopy(added.ROLE), codec, physical_run=physical_run)
                return dict(before, legacy149_entire73_before_whole75_installed=after)
            names = NS(**{**vars(names), 'legacy154_binding_v1': NS(**{**vars(old), 'install': installed})})
        return names, proof
    api73 = previous.connect(root, NS(**{**vars(loader), 'load': load}), scope, bytes_policy, xz, bounded, checkpoint, exact)
    old_validator = api73.runtime.validate_worker_hint
    suffix, suffix_proof = slots.constant(old_validator, '.compact.v4.json', '.compact.v5.json',
        'validate_worker_hint', 'current_queue_successor_runtime.py')
    old_validator.__globals__['validate_worker_hint'] = suffix
    api73.runtime.validate_worker_hint = suffix
    inner, inner_proof = slots.constant(api73.revised_inner, 73, 75, 'reconstruct', 'native009_worker_transport_v1.py')
    middle_count, middle_proof = slots.constant(api73.revised_outer, 73, 75, 'reconstruct', 'native009_full72_transport_v1.py')
    middle, middle_closure = previous.closure_dependency(middle_count, 'reconstruction', api73.revised_inner, inner)
    top_count, top_proof = slots.constant(api73.reconstruct, 73, 75, 'reconstruct', 'native009_full73_transport_v1.py')
    reconstruction, top_closure = top_dependency(top_count, api73.revised_outer, middle)
    build, engine_proof = slots.constant(api73.build, 73, 75, 'build', 'native009_engine_connection_v1.py')
    def core_hint(hint):
        require(type(hint) is dict and FIELD in hint, 'EXPLICIT_TWO_P149_FAILURE_ROLES')
        exact(hint[FIELD], added.ROLE, 'EXACT_DISTINCT_UNKNOWN_UNPROMOTED149')
        return {k: v for k, v in hint.items() if k != FIELD}
    def validate(hint): return api73.validate(core_hint(hint))
    def factory(hint, prior68): return api73.factory(core_hint(hint), prior68)
    def reconstruct(hint, wire, check):
        checkpoint(); core = core_hint(hint); api73.validate(core)
        graph, proof = reconstruction(core, wire, check)
        require(len(graph.binding.descriptors()) == 75, 'ALL75_AFTER_WHOLE_ORIGINAL_CHAIN')
        return graph, dict(proof, descriptor_count=75, whole_original73_reconstruction_chain_retained=True,
            count_slots_and_two_named_dependencies_have_exact_inverses=True, actual_Native_or_product_qualified=False)
    require(injected == [True], 'ACTUAL_PRIVATE73_INJECTION')
    return NS(runtime=api73.runtime, metadata=api73.metadata, factory=factory, validate=validate, reconstruct=reconstruct, build=build,
        roles=NS(**{**vars(api73.roles), 'legacy149': copy.deepcopy(added.ROLE)}), source_proofs=proofs+api73.source_proofs,
        inner_count_proof=inner_proof, middle_count_proof=middle_proof, top_count_proof=top_proof, engine_proof=engine_proof,
        middle_closure_proof=middle_closure, top_closure_proof=top_closure, suffix_proof=suffix_proof,
        original_inner=api73.revised_inner, revised_inner=inner, original_middle=api73.revised_outer, revised_middle=middle,
        original_top=api73.reconstruct, revised_top=reconstruction, old_api=api73, original_default_modules_mutated=False)


def main():
    import argparse, importlib.util, io, os, re, time, traceback, unittest
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    denied = []
    def deny(event, args):
        if event == 'subprocess.Popen': denied.append(1); raise ValueError('FULL75_TRANSPORT_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(deny)
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
    output = PREFIX+f'native009-full75-transport-code{attempt:03}.v1.json'
    graph_name = graph_path(attempt)
    native = c.ROOT/(PREFIX+'current-runtime-run009.v1.json')
    require(not (c.ROOT/output).exists() and not (c.ROOT/graph_name).exists() and not native.exists(), 'EXCLUSIVE_REPORT_NOT_NATIVE')
    guard = libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(
        libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    row = dict(state='FAILED_NATIVE009_FULL75_TRANSPORT_NOT_ADOPTED', accepted_count_delta=0, GO_authorized=False,
        actual_worker_product_or_Native_executed=False, current_full_source_Frame_or_dispatch_qualified=False,
        current_report_graph_and_later_worker_dispatch_results_must_be_recosted=True, preparation_CPU_policy_changed=False)
    started, phase = time.monotonic(), 'CURRENT_ADMISSION'
    q = prepared = chunk = None
    encoded = lambda value: (json.dumps(value, ensure_ascii=True, indent=2, allow_nan=False)+'\n').encode('ascii')
    try:
        guard.acquire(); seed = a.AcceptanceReader(c.ROOT, guard.check)
        for pin in PINS+[CONSTRUCTION]: a.exact(seed.pin(pin['path']), pin, 'CURRENT_FIXED_COMPONENTS')
        components, _ = loader.load(c.ROOT, [PINS[1]], {})
        binding = components.legacy149_binding_v1
        for pin in (binding.SNAPSHOT, binding.CHUNK): a.exact(seed.pin(pin['path']), pin, 'CURRENT_OPTIMIZED_READER_COMPONENTS')
        readers, _ = loader.load(c.ROOT, [binding.SNAPSHOT, binding.CHUNK], {'audit_evidence_io': original_io})
        snapshot, chunk = readers.single_snapshot_source_guard_v1, readers.reusable_audit_chunk_v1
        pin, raw = seed._read(snapshot.ORIGINAL_PIN['path'], parse=True); seed._bind(pin['path'], pin)
        a.exact(pin, snapshot.ORIGINAL_PIN, 'UNCHANGED_ORIGINAL_READER_LEAF')
        SourceReader, _ = snapshot.reader_type(a.AcceptanceReader, bytes(raw))
        Reader, reader_proof = chunk.reader_type(SourceReader, bytes(raw)); del raw
        q = Reader(c.ROOT, guard.check)
        for pin in seed.snapshots.values(): a.exact(q.pin(pin['path']), pin, 'FRESH_READER_BOOTSTRAP')
        q.pin(SELF); q.pin(TEST)
        for pin in construction.PINS: a.exact(q.pin(pin['path']), pin, 'CURRENT_CORE_GRAPH_SOURCE')
        code = a.read_exact(q, CODE)
        a.fields(code, dict(state='PASS_LEGACY149_FULL75_BINDING_AND_CHUNK29_WITH_REPLAYABLE_DECLARED_COST_NOT_WORKER_OR_NATIVE',
            contracts=dict(run=29, errors=0, failures=0, skipped=0), semantic_inputs=3242, fresh_inputs=408, final_fresh_hashes=408,
            cleanup_confirmed=True, actual_engine_worker_calls=0, subprocess_creation_attempts=0,
            previous_scope_and_budget_exactly_reconstructed=True, persisted_scope_uses_original_noninjecting_union=True), 'CURRENT_BINDING75_CODE29')
        for pin in code['source_pins']:
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):
                a.exact(q.pin(pin['path']), pin, 'ALL_CURRENT_BINDING_QUALIFIED_PROGRAMS')
        fixture = a.read_exact(q, code['code_manifest_pin']); rows = fixture['descriptors']
        require(len(rows) == 75 and binding.fingerprint(rows[:73]) == binding.TABLE73, 'EXACT_ALL75_FIXTURE')
        base = a.read_exact(q, code['declared_scope_base_pin'])
        inherited = scope.extend(scope.pins(base['input_pins']), {code['declared_scope_base_pin']['path']: code['declared_scope_base_pin']})
        inherited = scope.extend(inherited, scope.pins(code['declared_scope_delta_pins']))
        pins = scope.pins(code['source_pins'])
        upstream_name = 'tools/p09/qualify_native009_full73_parent_v1.py'
        upstream, _ = loader.load(c.ROOT, [pins[upstream_name], construction.DECLARATION], {})
        old_hint_name = PREFIX+'successor-worker-bootstrap009.v4.json'
        previous_hint = q.json(old_hint_name)
        a.exact(q.snapshots[old_hint_name], pins[old_hint_name], 'EXACT_QUALIFIED_PRIOR_V4_HINT')
        old_manifest = a.read_exact(q, previous_hint['manifest_pin'])
        hint = copy.deepcopy(previous_hint); step = hint['step']
        authority = a.read_exact(q, step['prior_queue_pin'])
        a.fields(authority, dict(accepted_count_after=158, next_runtime_index=165,
            runtime_candidate_pin=step['prior_candidate_pin']), 'CURRENT_UNADVANCED_AUTHORITY')
        phase = 'REAL_FRESH_SOURCE_BEFORE75_FACTORY'
        facade = NS(connect=connect, constant=libs.native009_full72_transport_v1.constant)
        fresh = libs.native009_verified_source_profile_v1.connect(c.ROOT, loader, scope, bytes_policy,
            libs.receipt_xz_envelope_v1, libs.bounded_successor_capsule_wire_v2, guard.check, a, q, hint, facade)
        api = fresh.api
        manifest = dict(old_manifest, schema_version='hwpx-agent.p09-native009-full75-manifest/v1', descriptors=rows,
            legacy149_validation_failure_roles=api.roles.legacy149, current_whole_Native_source_scope_qualified=False)
        publisher = upstream.native009_parent_scope_v1
        manifest_pin = publisher.publish_bytes(c.ROOT, MANIFEST, encoded(manifest), q, guard, bytes_policy, a, 262144)
        hint.update(manifest_pin=manifest_pin, **{FIELD: api.roles.legacy149})
        module = api.factory(dict(hint, capsule_pin=dict(path=CAPSULE, bytes=1, sha256='0'*64)), rows[:68])
        bound = module.Binding(rows, manifest_pin, next_case=165)
        graph, _ = api.metadata.connect(c.ROOT, loader, bytes_policy, module, bound, step, 9, guard.check)
        wire, _ = graph.worker.encode(bound, step['prior_queue_pin'], step['prior_candidate_pin'], guard.check)
        hint['capsule_pin'] = publisher.publish_bytes(c.ROOT, CAPSULE, wire, q, guard, bytes_policy, a, 16384)
        hint_pin = publisher.publish_bytes(c.ROOT, HINT, encoded(hint), q, guard, bytes_policy, a, 16384)
        phase = 'WHOLE_ORIGINAL75_RECONSTRUCTION'
        observed = dict(active=True, data_file_opens=0)
        def audit(event, args):
            if observed['active'] and event == 'open' and args and isinstance(args[0], str) and args[0].lower().endswith('.json'):
                observed['data_file_opens'] += 1
        sys.addaudithook(audit)
        try: rebuilt, proof = api.reconstruct(hint, wire, guard.check)
        finally: observed['active'] = False
        a.exact(observed['data_file_opens'], 0, 'ORIGINAL_RECONSTRUCTION_NO_DATA_JSON_OPENS')
        a.exact(rebuilt.binding.descriptors(), rows, 'ENTIRE75_ORIGINAL_DECODE')
        linked = api.build(c.ROOT, loader, api, rebuilt, envelope.prior, libs.post_product_recovery_connection_v1,
            libs.post_product_recovery_window_v1, guard.check)
        phase = 'EXACT_PREVIOUS_WHOLE_DECLARATION_AND_COST'
        baseline = module.Binding(rows, code['code_manifest_pin'], next_case=165)
        inherited, _ = baseline.semantic_union(inherited, guard.check)
        projection, _ = baseline.project(inherited, guard.check)
        baseline_bytes = sum(p['bytes'] for p in projection.physical_pins.values())
        a.exact(len(inherited), code['semantic_inputs'], 'ALL_PREVIOUS3242_NOT_FRESH_SUBSET')
        a.exact(baseline_bytes, code['physical_bytes'], 'EXACT_PREVIOUS_PHYSICAL_DECLARATION')
        old_budget = baseline.runtime_budget(inherited, code['inventory_requests'], linked.window.DIRECT.runtime_budget, guard.check)
        a.exact(old_budget, code['original_complete_runtime_budget'], 'ENTIRE_PREVIOUS_COST_EXACT')
        phase = 'TRANSPORT_CONTRACTS'
        spec = importlib.util.spec_from_file_location('native009_full75_transport_contracts', c.ROOT/TEST)
        tests = importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
        tests.MODULE = sys.modules[__name__]; tests.API = api; tests.HINT = hint; tests.WIRE = wire; tests.GRAPH = rebuilt
        tests.ROWS = rows; tests.CHECK = guard.check; tests.BOUNDED = libs.bounded_successor_capsule_wire_v2
        tests.LINKED = linked; tests.OBSERVED = observed; tests.BASIS = inherited; tests.CODE = code
        tests.BASIS_BYTES = baseline_bytes; tests.READER = q; tests.CHUNK = chunk; tests.SOURCE = fresh
        result = unittest.TextTestRunner(stream=io.StringIO(), failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts'] = dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped))
        row['contract_failures'] = [dict(test=t.id().rsplit('.', 1)[-1], exception_type=trace.splitlines()[-1].split(':', 1)[0])
            for t, trace in result.errors+result.failures]
        a.exact(row['contracts'], dict(run=20, errors=0, failures=0, skipped=0), 'ALL_TRANSPORT20')
        phase = 'CURRENT_COMPLETE_DECLARED_SCOPE_AND_COST'
        for loaded in tuple(sys.modules.values()):
            filename = getattr(loaded, '__file__', None)
            if filename:
                path = Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix == '.py': q.pin(path.relative_to(c.ROOT).as_posix())
        required, _ = rebuilt.binding.semantic_union(scope.extend(inherited, q.snapshots), guard.check)
        require(all(required.get(n) == pin for n, pin in inherited.items()), 'NO_PREVIOUS_SEMANTIC_INPUT_REMOVED')
        _, delta = upstream.qualify_native009_full73_parent_v1.compact_scope(rebuilt.binding, type(rebuilt.binding).semantic_union,
            scope, base, code['declared_scope_base_pin'], required, guard.check, a.exact)
        inventory = a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'), ('rust_inputs',), dict(os=os, Path=Path, require=require))
        requests = []
        def paced(): requests.append(1); q.open_pacer.reserve()
        rust = inventory.rust_inputs(c.ROOT, paced)
        require(len(rust) == 787 and set(rust) <= set(required), 'CURRENT_RUST787')
        budget = rebuilt.binding.runtime_budget(required, len(requests), linked.window.DIRECT.runtime_budget, guard.check)
        total = budget['predicted_runtime_combined_seconds']+15
        row.update(original_complete_runtime_budget=budget, predicted_complete_seconds_with_readiness=total,
            declared_cost_nominal_fits600=total < 600, semantic_inputs=len(required), current_Rust_path_count=len(rust),
            inventory_requests=len(requests), additional_readiness_seconds_without_old_credit=15,
            declared_scope_base_pin=code['declared_scope_base_pin'], declared_scope_delta_pins=delta,
            persisted_scope_uses_original_noninjecting_union=True, inherited_previous_scope_exactly_reconstructed=True,
            inherited_previous_semantic_inputs=len(inherited), inherited_previous_physical_bytes=baseline_bytes,
            inherited_previous_budget_exactly_reconstructed=True, prior_binding_code_pin=CODE,
            actual_engine_worker_calls=linked.state.calls, manifest_pin=manifest_pin, capsule_pin=hint['capsule_pin'], bootstrap_pin=hint_pin)
        require(total < 600, 'CURRENT_COMPLETE_SCOPE_PLUS_READINESS_OUTSIDE600')
        phase = 'FINAL_METADATA_HASHES'
        q.finish(); guard.check(force=True)
        require(not denied and not native.exists() and linked.state.calls == 0, 'NO_SUBPROCESS_WORKER_OR_NATIVE')
        row.update(state='PASS_NATIVE009_FULL75_ORIGINAL_RECONSTRUCTION20_AND_REPLAYABLE_DECLARED_COST_NOT_WORKER_OR_NATIVE',
            descriptor_count=75, source_pins=list(q.snapshots.values()), fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
            reconstruction_proof=proof, inner_count_proof=api.inner_count_proof, middle_count_proof=api.middle_count_proof,
            top_count_proof=api.top_count_proof, engine_count_proof=api.engine_proof, middle_closure_proof=api.middle_closure_proof,
            top_closure_proof=api.top_closure_proof, suffix_proof=api.suffix_proof, reconstruction_JSON_file_opens=0,
            preparation_reader_connection=reader_proof)
        prepared = dict(state='PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO', index=165, physical_run=9,
            step=step, manifest_pin=manifest_pin, capsule_pin=hint['capsule_pin'], bootstrap_pin=hint_pin, descriptors=75,
            accepted_count_delta=0, product_or_Native_executed=False, GO_authorized=False, actual_current_source_Frame_qualified=False,
            source_pins=list(q.snapshots.values()), fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
            cleanup_confirmed=True, declared_scope_base_pin=code['declared_scope_base_pin'], declared_scope_delta_pins=delta,
            inherited_previous_scope_exactly_reconstructed=True, persisted_scope_uses_original_noninjecting_union=True)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, NameError) as error:
        row['error_type'] = type(error).__name__
        row['error_frames'] = [dict(file=Path(f.filename).name, function=f.name, line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}', error.args[0]):
            row['error_code'] = error.args[0]
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
    if prepared is not None:
        row['graph_report_pin'] = libs.successor_preparation_workspace_v1.publish(c.ROOT, graph_name, prepared, a)
    libs.successor_preparation_workspace_v1.publish(c.ROOT, output, row, a)
    print(json.dumps({k: row.get(k) for k in ('state', 'contracts', 'contract_failures', 'descriptor_count', 'semantic_inputs',
        'predicted_complete_seconds_with_readiness', 'fresh_inputs', 'final_fresh_hashes', 'elapsed_seconds', 'CPU_max',
        'owned_CPU_machine_max', 'owned_private_MiB_max', 'RAM_min', 'cleanup_confirmed', 'subprocess_creation_attempts',
        'operation_phase', 'error_code', 'error_frames')}, allow_nan=False))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__ == '__main__': raise SystemExit(main())
