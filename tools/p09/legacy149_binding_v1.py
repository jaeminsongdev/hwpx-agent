"""Two exact P149 roles after the complete73 Binding; no runtime authority.

Preserve every prior constructor, nonconstructor oracle and Projection method.
Only two source-pinned stopped validation records gain lossless physical aliases.
Unknown product execution is never converted into prebody, False, True or PASS.
"""
import copy
import hashlib
import json
import sys
from types import FunctionType, SimpleNamespace as NS

SELF = 'tools/p09/legacy149_binding_v1.py'
TEST = 'tools/p09/tests/test_legacy149_binding_v1.py'
PREFIX = 'implementation/p09/evidence/p09-361-case165-'
PHYSICAL_PROOF = dict(path=PREFIX+'legacy149-full75-physical-g001-attempt002.v1.json', bytes=98768,
    sha256='fc9d78d0cbc9a966ffb2dbca8844e578d467d7ed32040ec5f4adfd519c9e46de')
PARENT_PROOF = dict(path=PREFIX+'native009-full73-parent-connection003.v1.json', bytes=92954,
    sha256='f186ec913c3ce6b7c9703634a0c34859b0f5eac581f447457610d47034268a34')
CONSTRUCTION = dict(path='tools/p09/native009_full72_construction_v1.py', bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
SNAPSHOT = dict(path='tools/p09/single_snapshot_source_guard_v1.py', bytes=4560,
    sha256='f3555f4395154be7c929e76eeb451226402b49cc54b0ab6da335ba94555eae43')
CHUNK = dict(path='tools/p09/reusable_audit_chunk_v1.py', bytes=8088,
    sha256='1aa1db74585cbdf50df32ac0c9dc07dfd31557fc37647ca6e6ea3969fbb60e75')
CHUNK_TEST = dict(path='tools/p09/tests/test_reusable_audit_chunk_v1.py', bytes=10148,
    sha256='60af53923c129d9f67774b8347a5e7df6aef85ea1c30cd9e65378e4a37a5a399')
TABLE73 = 'bb494ffde464655456d068ccae6516c257956e558fcdf4d6ca1a97530c8473ca'
SOURCE_ROLE = 'historical_validation_worker_writer_started_stopped_not_accepted_product_execution_unknown'
RECORDS = [
    dict(key='run01', original=dict(path='implementation/p09/evidence/p09-149-compression-full-stored.actual-run01.v1.json',
        bytes=3607741, sha256='677ef24e932a3f48690a6b4818e41f2753b977206b904f649fa22df3b89fd774'),
        physical=dict(path='implementation/p09/evidence/p361-lossless-runtime-inputs/legacy-p149-compression-full-stored.actual-run01.failed.runner.xz8m-g001.envelope.v1.json',
        bytes=199178, sha256='539b0282ac53f9c65256fda49cfabe9e60137fe6dd3019758dcb1b459327a08c'),
        source_role=SOURCE_ROLE, original_stop_reason='OWNED_RUNNER_FAILURE', original_failure_promoted=False,
        actual_failed_product_child_executed=None),
    dict(key='run02', original=dict(path='implementation/p09/evidence/p09-149-compression-full-stored.actual-run02.v1.json',
        bytes=3322888, sha256='103c85ed2b7bad5885c37e7cc22f8f55ba46c4a2c6435b4f8110e34687940557'),
        physical=dict(path='implementation/p09/evidence/p361-lossless-runtime-inputs/legacy-p149-compression-full-stored.actual-run02.failed.ram.xz8m-g001.envelope.v1.json',
        bytes=190922, sha256='6e62315c33cf1618b55ffbca238b0e1aaa9245078e3fc563c08d137793bc97f9'),
        source_role=SOURCE_ROLE, original_stop_reason='STOP_LOW_AVAILABLE_RAM', original_failure_promoted=False,
        actual_failed_product_child_executed=None)]
ROLE = dict(schema_version='hwpx-agent.p09-exact-legacy149-validation-aliases/v1', current_case=165,
    successor_physical_run=9, records=RECORDS, physical_verification_pin=PHYSICAL_PROOF,
    original_failure_promoted=False, current_product_or_GO_qualified=False)


def require(ok, label):
    if not ok: raise ValueError('LEGACY149_BINDING_'+label)


def fingerprint(rows):
    return hashlib.sha256(json.dumps(rows, ensure_ascii=True, sort_keys=True,
        allow_nan=False, separators=(',', ':')).encode('ascii')).hexdigest()


def admission(q, a):
    proof = a.read_exact(q, PHYSICAL_PROOF)
    a.fields(proof, dict(state='PASS_LEGACY149_COMPLETE75_PHYSICAL13_NOT_BINDING_WORKER_OR_NATIVE',
        contracts=dict(run=13, errors=0, failures=0, skipped=0), pair_count=75, decode_count=150,
        fresh_inputs=181, final_fresh_hashes=181, cleanup_confirmed=True, accepted_count_delta=0,
        GO_authorized=False, product_or_Native_executed=False, original_overwritten_or_deleted=False,
        prior73_mapping_or_descriptor_policy_changed=False, full75_binding_worker_or_Native_qualified=False), 'EXACT_PHYSICAL75')
    a.exact(proof['records'], RECORDS, 'BOTH_DISTINCT_UNKNOWN_UNPROMOTED_FAILURES')
    require(fingerprint(proof['full73_descriptors']) == TABLE73, 'ALL_FIXED_PRIOR73')
    a.fields(proof['decoder_budget'], dict(aggregate_limit_seconds=5.0, attempted_decodes=150,
        completed_decodes=150, active_decode=False, terminal_error_seen=False,
        two_boundaries_share_one_budget=True), 'PHYSICAL_PROOF_NOT_CURRENT_SHARED_RUNTIME_BUDGET')
    for pin in proof['source_pins']:
        if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):
            a.exact(q.pin(pin['path']), pin, 'ALL_CURRENT_PHYSICAL_VERIFIER_CODE')
    for record in RECORDS:
        a.exact(q.pin(record['original']['path']), record['original'], 'CURRENT_FIXED_ORIGINAL_BYTES')
    # Physical bytes are freshly read, hashed AND bound by the caller before
    # codec tests; avoid an extra preliminary hash-only open of the same file.
    return copy.deepcopy(ROLE), proof


def install(module, prior_rows, admitted, xz, *, physical_run):
    require(type(physical_run) is int and physical_run == 9, 'ONLY_CURRENT_RUN9')
    require(type(module) is NS and type(getattr(module, 'source', None)) is NS, 'PRIVATE_MODULE')
    module.exact(admitted, ROLE, 'EXACT_TWO_FAILURE_ROLES')
    require(type(prior_rows) is list and len(prior_rows) == 73 and fingerprint(prior_rows) == TABLE73, 'ALL_FIXED_PRIOR73')
    require(hasattr(module, 'legacy154_validation_alias') and not hasattr(module, 'legacy149_validation_aliases'), 'ONE_INSTALL_AFTER73')
    source = module.source
    env = source.Projection.__init__.__globals__
    require(env.get('__name__', '').startswith('p09_exact_') and env.get('descriptor') is source.descriptor
        and not any(getattr(m, '__dict__', None) is env for m in tuple(sys.modules.values()) if m), 'PRIVATE_SOURCE_NOT_DEFAULT')
    old_init, raw_init = module.Binding.__init__, module.xz_original_initialize
    require(type(raw_init) is FunctionType and raw_init.__code__.co_filename.replace('\\', '/').endswith(
        'runtime_envelope_scope_binding_v1.py'), 'WHOLE_ORIGINAL_RAW_CONSTRUCTOR')
    old_descriptor, old_codec = source.descriptor, source.codec
    old_representation = module.Binding.representation
    methods = {n: f for n, f in vars(module.Binding).items() if n not in ('__init__', 'representation')}
    projections = dict(vars(source.Projection))
    prior, provenance = copy.deepcopy(prior_rows), copy.deepcopy(admitted)
    pairs = [dict(schema_version=source.SCHEMA, next_case=165, semantic_original_pin=dict(r['original']),
        physical_envelope_pin=dict(r['physical'])) for r in RECORDS]
    by_original = {r['original']['path']: (r, p) for r, p in zip(RECORDS, pairs)}
    physical_hashes = {r['physical']['sha256'] for r in RECORDS}
    complete, state = prior+pairs, dict(ready=False)

    def descriptor(old, new, *, next_case):
        if type(old) is not dict or old.get('path') not in by_original:
            return old_descriptor(old, new, next_case=next_case)
        require(type(next_case) is int and next_case == 165, 'ONLY_CASE165')
        record, pair = by_original[old['path']]
        module.exact(source.copy_pin(old), record['original'], 'EXACT_ORIGINAL')
        module.exact(source.copy_pin(new), record['physical'], 'EXACT_PHYSICAL')
        return copy.deepcopy(pair)

    def initialize(self, rows, manifest_pin, *, next_case):
        state['ready'] = False
        module.exact(rows, complete, 'EXACT73_PLUS_TWO149')
        require(type(next_case) is int and next_case == 165, 'FULL75_CASE165')
        old_init(self, rows[:73], manifest_pin, next_case=next_case)
        module.exact(self.descriptors(), prior, 'ENTIRE_ORIGINAL73_COMPLETED')
        raw_init(self, rows, manifest_pin, next_case=next_case)
        module.exact(self.descriptors(), complete, 'WHOLE_ORIGINAL_RAW75_COMPLETED')
        state['ready'] = True

    def decode(encoded, checkpoint):
        checkpoint()
        require(type(encoded) is bytes and 0 < len(encoded) <= xz.MAX_BYTES, 'FRESH_BOUNDED_CODEC_INPUT')
        if hashlib.sha256(encoded).hexdigest() in physical_hashes:
            require(state['ready'], 'FULL75_CONSTRUCTOR_BEFORE149_DECODE')
            return xz.decode(encoded, checkpoint)
        return old_codec.decode(encoded, checkpoint)

    def representation(self, projection):
        require(all(n in self.originals for n in by_original), 'BOTH_EXPLICIT_ORIGINALS')
        row = old_representation(self, projection)
        row['legacy149_validation_failures_provenance'] = copy.deepcopy(provenance)
        return row

    source.descriptor = env['descriptor'] = descriptor
    source.codec = env['codec'] = NS(**{**vars(old_codec), 'decode': decode})
    module.Binding.__init__, module.Binding.representation = initialize, representation
    module.legacy149_validation_aliases = copy.deepcopy(provenance)
    require(all(vars(module.Binding).get(n) is f for n, f in methods.items()), 'ALL_NONCONSTRUCTOR_ORACLES_RETAINED')
    require(all(vars(source.Projection).get(n) is f for n, f in projections.items()), 'ALL_PROJECTION_METHODS_RETAINED')
    return dict(entire_original73_before_whole_raw75=True, all_nonconstructor_and_Projection_oracles_retained=True,
        distinct_stop_reasons_and_unknown_product_execution_preserved=True, Native_or_GO_authorized=False)


def reader_probe(c, a, libs, loader, attempt):
    """Close the allocation optimization independently, never the Binding gate."""
    import importlib.util, io, re, time, unittest
    from pathlib import Path
    output = PREFIX+f'legacy149-preparation-reader-code{attempt:03}.v1.json'
    require(not (c.ROOT/output).exists(), 'EXCLUSIVE_READER_REPORT')
    guard = libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(
        libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started = time.monotonic(); q = chunk = None
    row = dict(state='FAILED_LEGACY149_PREPARATION_READER_NOT_BINDING', accepted_count_delta=0,
        GO_authorized=False, product_or_Native_executed=False, actual_full73_graph_construction=False,
        full75_Binding_or_worker_or_Native_qualified=False, preparation_CPU_policy_changed=False)
    try:
        import audit_evidence_io as original_io
        guard.acquire(); seed = a.AcceptanceReader(c.ROOT, guard.check)
        for name in (SELF, TEST): seed.pin(name)
        for pin in (SNAPSHOT, CHUNK, CHUNK_TEST): a.exact(seed.pin(pin['path']), pin, 'EXACT_READER_SOURCES')
        modules, _ = loader.load(c.ROOT, [SNAPSHOT, CHUNK], {'audit_evidence_io': original_io})
        snapshot, chunk = modules.single_snapshot_source_guard_v1, modules.reusable_audit_chunk_v1
        pin, raw = seed._read(snapshot.ORIGINAL_PIN['path'], parse=True); seed._bind(pin['path'], pin)
        a.exact(pin, snapshot.ORIGINAL_PIN, 'EXACT_ORIGINAL_LEAF')
        SourceReader, _ = snapshot.reader_type(a.AcceptanceReader, bytes(raw))
        Reader, proof = chunk.reader_type(SourceReader, bytes(raw))
        leaf_raw = bytes(raw); del raw
        q = Reader(c.ROOT, guard.check)
        for pin in seed.snapshots.values(): a.exact(q.pin(pin['path']), pin, 'FRESH_READER_PROBE_INPUT')
        suites = []
        for name, path in (('binding_reader_probe', TEST), ('original_chunk_probe', CHUNK_TEST['path'])):
            spec = importlib.util.spec_from_file_location(name, c.ROOT/path)
            tests = importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
            if path == TEST:
                tests.READER = q; tests.SOURCE_READER = SourceReader; tests.CHUNK = chunk
                suites.append(unittest.TestSuite(tests.Tests(method) for method in (
                    'test_actual_preparation_reader_preserves_source_and_every_prior_MRO_layer',
                    'test_actual_preparation_workspace_fresh_reads_no_cache_or_active_lease')))
            else:
                tests.r = chunk; tests.CHECKPOINT = guard.check; tests.SOURCE_BYTES = leaf_raw
                suites.append(unittest.defaultTestLoader.loadTestsFromModule(tests))
        result = unittest.TextTestRunner(stream=io.StringIO(), failfast=True).run(unittest.TestSuite(suites))
        row['contracts'] = dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped))
        row['contract_failures'] = [dict(test=t.id().rsplit('.', 1)[-1], exception_type=trace.splitlines()[-1].split(':', 1)[0])
            for t, trace in result.errors+result.failures]
        a.exact(row['contracts'], dict(run=17, errors=0, failures=0, skipped=0), 'READER_CONNECTION2_AND_UNCHANGED_CHUNK15')
        for loaded in tuple(sys.modules.values()):
            filename = getattr(loaded, '__file__', None)
            if filename:
                path = Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix == '.py':
                    q.pin(path.relative_to(c.ROOT).as_posix())
        q.finish(); guard.check(force=True)
        row.update(state='PASS_LEGACY149_PREPARATION_READER17_NOT_FULL75_BINDING_OR_RUNTIME',
            connection=proof, source_pins=list(q.snapshots.values()), fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
            workspace=chunk.summary(q), source_predicates=q.source_snapshot_diagnostics())
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        row['error_type'] = type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}', error.args[0]):
            row['error_code'] = error.args[0]
    finally:
        guard.close()
        row.update(cleanup_confirmed=guard.cleanup, elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples), default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None), default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None), default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples), default=None))
    require(guard.cleanup, 'READER_CLEANUP')
    libs.successor_preparation_workspace_v1.publish(c.ROOT, output, row, a)
    print(json.dumps({k: row.get(k) for k in ('state', 'contracts', 'contract_failures', 'fresh_inputs', 'final_fresh_hashes',
        'elapsed_seconds', 'CPU_max', 'owned_CPU_machine_max', 'owned_private_MiB_max', 'RAM_min', 'cleanup_confirmed', 'error_code')}))
    return 0 if row['state'].startswith('PASS_') else 1


def main():
    import argparse, importlib.util, io, os, re, time, traceback, unittest
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    denied = []
    def audit(event, args):
        if event == 'subprocess.Popen':
            denied.append(1)
            raise ValueError('LEGACY149_BINDING_ALL_SUBPROCESS_DENIED')
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--attempt', type=int, required=True)
    parser.add_argument('--reader-only', action='store_true')
    args = parser.parse_args(); attempt = args.attempt
    require(type(attempt) is int and 1 <= attempt <= 8, 'BOUNDED_ATTEMPT')
    if args.reader_only: return reader_probe(c, a, libs, loader, attempt)
    output = PREFIX+f'legacy149-binding-code{attempt:03}.v1.json'
    manifest_name = PREFIX+f'legacy149-binding-code-manifest{attempt:03}.v1.json'
    native = c.ROOT/(PREFIX+'current-runtime-run009.v1.json')
    require(not (c.ROOT/output).exists() and not (c.ROOT/manifest_name).exists() and not native.exists(), 'EXCLUSIVE_NEW_REPORT_NOT_NATIVE')
    guard = libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(
        libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started, phase = time.monotonic(), 'CURRENT_ADMISSION'
    q = chunk = None
    row = dict(state='FAILED_LEGACY149_BINDING_NOT_ADOPTED', accepted_count_delta=0, GO_authorized=False,
        product_or_Native_executed=False, full75_worker_transport_or_Native_qualified=False,
        current_complete_Native_cost_qualified=False, preparation_CPU_policy_changed=False,
        current_result_and_future_transport_dispatch_sources_must_be_recosted=True)
    try:
        guard.acquire()
        seed = a.AcceptanceReader(c.ROOT, guard.check)
        a.exact(seed.pin(SNAPSHOT['path']), SNAPSHOT, 'CURRENT_OPTIMIZED_SOURCE_HELPER')
        for pin in (CHUNK, CHUNK_TEST): a.exact(seed.pin(pin['path']), pin, 'UNCHANGED_REUSABLE_CHUNK_SOURCE')
        names, _ = loader.load(c.ROOT, [SNAPSHOT, CHUNK], {'audit_evidence_io': original_io})
        snapshot = names.single_snapshot_source_guard_v1
        chunk = names.reusable_audit_chunk_v1
        pin, raw = seed._read(snapshot.ORIGINAL_PIN['path'], parse=True)
        seed._bind(pin['path'], pin)
        a.exact(pin, snapshot.ORIGINAL_PIN, 'UNCHANGED_ORIGINAL_SOURCE')
        SourceReader, _ = snapshot.reader_type(a.AcceptanceReader, bytes(raw))
        Reader, chunk_proof = chunk.reader_type(SourceReader, bytes(raw))
        del raw
        q = Reader(c.ROOT, guard.check)
        row['preparation_chunk_connection'] = chunk_proof
        for pin in seed.snapshots.values(): a.exact(q.pin(pin['path']), pin, 'FRESH_BOOTSTRAP')
        q.pin(SELF); q.pin(TEST)
        for pin in [CONSTRUCTION]+construction.PINS: a.exact(q.pin(pin['path']), pin, 'CURRENT_CORE_SOURCES')
        admitted, physical = admission(q, a)
        previous = a.read_exact(q, PARENT_PROOF)
        a.fields(previous, dict(state='PASS_FULL73_PARENT_LAUNCH_JOB_FRAME_AND_ORACLE25_WITH_REPLAYABLE_DECLARED_COST_NOT_NATIVE',
            contracts=dict(run=25, errors=0, failures=0, skipped=0), semantic_inputs=3223,
            fresh_inputs=392, final_fresh_hashes=392, cleanup_confirmed=True, actual_parent_attempts=0,
            actual_worker_calls=0, actual_Frame_instances=0, subprocess_creation_attempts=0,
            persisted_scope_uses_original_noninjecting_union=True), 'REPLAYABLE_CURRENT_PARENT73')
        oldpins = scope.pins(previous['source_pins'])
        for pin in oldpins.values():
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):
                a.exact(q.pin(pin['path']), pin, 'ALL_CURRENT_PARENT_QUALIFIED_CODE')
        base = a.read_exact(q, previous['declared_scope_base_pin'])
        inherited = scope.extend(scope.pins(base['input_pins']), {previous['declared_scope_base_pin']['path']: previous['declared_scope_base_pin']})
        inherited = scope.extend(inherited, scope.pins(previous['declared_scope_delta_pins']))
        qualified = 'tools/p09/qualify_native009_full73_parent_v1.py'
        entry_name = 'tools/p09/native009_full73_worker_entry_v1.py'
        parts, _ = loader.load(c.ROOT, [oldpins[qualified], oldpins[entry_name], construction.DECLARATION], {})
        entry = parts.native009_full73_worker_entry_v1
        prepared = a.read_exact(q, oldpins[PREFIX+'successor-native009-full73-graph005.v1.json'])
        hint = a.read_exact(q, entry.HINT)
        a.exact(entry.HINT, prepared['bootstrap_pin'], 'CURRENT73_HINT')
        a.exact(entry.WIRE, prepared['capsule_pin'], 'CURRENT73_PACKET')
        transports, _ = loader.load(c.ROOT, [entry.TRANSPORT], {})
        facade = NS(connect=transports.native009_full73_transport_v1.connect, constant=libs.native009_full72_transport_v1.constant)
        phase = 'REAL_ORIGINAL73_GRAPH_AND_COST'
        source = libs.native009_verified_source_profile_v1.connect(c.ROOT, loader, scope, bytes_policy,
            libs.receipt_xz_envelope_v1, libs.bounded_successor_capsule_wire_v2, guard.check, a, q, hint, facade)
        pin, raw = q._read(entry.WIRE['path'], parse=True); q._bind(pin['path'], pin)
        a.exact(pin, entry.WIRE, 'CURRENT_FULL73_WIRE')
        api = source.api
        graph, _ = api.reconstruct(hint, bytes(raw), guard.check)
        del raw
        inherited, _ = graph.binding.semantic_union(inherited, guard.check)
        a.exact(len(inherited), previous['semantic_inputs'], 'COMPLETE_PREVIOUS3223')
        engine = api.build(c.ROOT, loader, api, graph, envelope.prior, libs.post_product_recovery_connection_v1,
            libs.post_product_recovery_window_v1, guard.check)
        old_budget = graph.binding.runtime_budget(inherited, previous['inventory_requests'], engine.window.DIRECT.runtime_budget, guard.check)
        a.exact(old_budget, previous['original_complete_runtime_budget'], 'ENTIRE_PREVIOUS_DECLARATION_AND_COST')
        module, prior = graph.binding_module, graph.binding.descriptors()
        require(fingerprint(prior) == TABLE73, 'ACTUAL_COMPLETE73')
        methods = {n: f for n, f in vars(module.Binding).items() if n not in ('__init__', 'representation')}
        projections = dict(vars(module.source.Projection))
        row['installation_proof'] = install(module, prior, admitted, libs.receipt_xz_envelope_v1, physical_run=9)
        rows = copy.deepcopy(prior)+[dict(schema_version=module.source.SCHEMA, next_case=165,
            semantic_original_pin=dict(r['original']), physical_envelope_pin=dict(r['physical'])) for r in RECORDS]
        fixture = dict(schema_version='hwpx-agent.p09-full75-binding-code-fixture/v1', descriptors=rows,
            worker_packet_or_Native_graph_qualified=False)
        encoded = (json.dumps(fixture, ensure_ascii=True, indent=2)+'\n').encode('ascii')
        fixture_pin = parts.native009_parent_scope_v1.publish_bytes(c.ROOT, manifest_name, encoded, q, guard, bytes_policy, a, 262144)
        carriers = []
        for record in RECORDS:
            pin, buffer = q._read(record['physical']['path'], parse=True)
            q._bind(pin['path'], pin)
            a.exact(pin, record['physical'], 'FRESH_TEST_CODEC_BYTES')
            carriers.append(bytes(buffer)); del buffer
        try: module.source.codec.decode(carriers[0], guard.check)
        except ValueError as error: require(error.args == ('LEGACY149_BINDING_FULL75_CONSTRUCTOR_BEFORE149_DECODE',), 'PRECONSTRUCTOR_CODEC_DENIAL')
        else: require(False, 'NO_NEW_DECODE_BEFORE_COMPLETE75')
        phase = 'FULL75_BINDING_CONTRACTS'
        spec = importlib.util.spec_from_file_location('legacy149_binding_contracts', c.ROOT/TEST)
        tests = importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
        tests.MODULE = sys.modules[__name__]; tests.BINDING = module; tests.ROWS = rows; tests.PIN = fixture_pin
        tests.SCOPE = scope; tests.CHECK = guard.check; tests.CARRIERS = carriers
        tests.METHODS = methods; tests.PROJECTION = projections; tests.PRIOR = prior; tests.XZ = libs.receipt_xz_envelope_v1
        tests.READER = q; tests.SOURCE_READER = SourceReader; tests.CHUNK = chunk
        chunk_spec = importlib.util.spec_from_file_location('legacy149_original_chunk_contracts', c.ROOT/CHUNK_TEST['path'])
        chunk_tests = importlib.util.module_from_spec(chunk_spec); chunk_spec.loader.exec_module(chunk_tests)
        chunk_tests.r = chunk; chunk_tests.CHECKPOINT = guard.check
        pin, buffer = q._read(snapshot.ORIGINAL_PIN['path'], parse=True)
        q._bind(pin['path'], pin); a.exact(pin, snapshot.ORIGINAL_PIN, 'FRESH_UNCHANGED_LEAF_TEST_SOURCE')
        chunk_tests.SOURCE_BYTES = bytes(buffer); del buffer
        suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m) for m in (tests, chunk_tests))
        result = unittest.TextTestRunner(stream=io.StringIO(), failfast=True).run(suite)
        row['contracts'] = dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped))
        row['contract_failures'] = [dict(test=t.id().rsplit('.', 1)[-1], exception_type=trace.splitlines()[-1].split(':', 1)[0])
            for t, trace in result.errors+result.failures]
        a.exact(row['contracts'], dict(run=29, errors=0, failures=0, skipped=0), 'BINDING14_AND_ORIGINAL_CHUNK15')
        tests.CARRIERS = None
        del carriers
        phase = 'FULL_INHERITED_SCOPE_AND_DECLARED_COST'
        inherited = scope.extend(inherited, scope.pins(physical['source_pins']))
        # Include the current metadata producer and its preserved failed results;
        # their declarations never replace the missing full metadata acceptance.
        for name in ('tools/p09/qualify_native009_full73_metadata_v1.py',
            PREFIX+'legacy149-binding-code001.v1.json',
            PREFIX+'legacy149-binding-code-manifest001.v1.json',
            PREFIX+'native009-full73-metadata-g002-attempt001.v1.json',
            PREFIX+'native009-full73-metadata-publication-review003.v1.json'):
            q.pin(name)
        for number in (2, 4, 5, 6, 7, 8): q.pin(PREFIX+f'native009-full73-metadata{number:03}.v1.json')
        for loaded in tuple(sys.modules.values()):
            filename = getattr(loaded, '__file__', None)
            if filename:
                path = Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix == '.py':
                    q.pin(path.relative_to(c.ROOT).as_posix())
        bound = module.Binding(rows, fixture_pin, next_case=165)
        required, _ = bound.semantic_union(scope.extend(inherited, q.snapshots), guard.check)
        normalized_prior, _ = bound.semantic_union(inherited, guard.check)
        require(all(required.get(n) == pin for n, pin in normalized_prior.items()), 'NO_PREVIOUS_SEMANTIC_INPUT_REMOVED')
        inventory = a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'), ('rust_inputs',), dict(os=os, Path=Path, require=require))
        requests = []
        def paced(): requests.append(1); q.open_pacer.reserve()
        rust = inventory.rust_inputs(c.ROOT, paced)
        require(len(rust) == 787 and set(rust) <= set(required), 'CURRENT_RUST787')
        budget = bound.runtime_budget(required, len(requests), engine.window.DIRECT.runtime_budget, guard.check)
        total = budget['predicted_runtime_combined_seconds']+15
        projection, _ = bound.project(required, guard.check)
        _, delta = parts.qualify_native009_full73_parent_v1.compact_scope(bound, type(bound).semantic_union,
            scope, base, previous['declared_scope_base_pin'], required, guard.check, a.exact)
        row.update(semantic_inputs=len(required), physical_inputs=len(projection.physical_pins),
            physical_bytes=sum(p['bytes'] for p in projection.physical_pins.values()),
            current_Rust_path_count=len(rust), inventory_requests=len(requests), original_complete_runtime_budget=budget,
            additional_readiness_seconds_without_old_credit=15, predicted_complete_seconds_with_readiness=total,
            declared_cost_nominal_fits600=total < 600, declared_scope_base_pin=previous['declared_scope_base_pin'],
            declared_scope_delta_pins=delta, persisted_scope_uses_original_noninjecting_union=True,
            previous_scope_and_budget_exactly_reconstructed=True, prior_parent_connection_pin=PARENT_PROOF,
            new_physical75_proof_pin=PHYSICAL_PROOF, code_manifest_pin=fixture_pin,
            actual_engine_worker_calls=engine.state.calls, whole_Native_metadata_or_byte_boundaries_qualified=False)
        require(total < 600, 'DECLARED_SCOPE_PLUS_READINESS_OUTSIDE600')
        phase = 'FINAL_METADATA_HASHES'
        q.finish(); guard.check(force=True)
        require(not denied and not native.exists() and engine.state.calls == 0, 'NO_SUBPROCESS_WORKER_OR_NATIVE')
        row.update(state='PASS_LEGACY149_FULL75_BINDING_AND_CHUNK29_WITH_REPLAYABLE_DECLARED_COST_NOT_WORKER_OR_NATIVE',
            source_pins=list(q.snapshots.values()), fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
            metadata_source_predicate_optimization=q.source_snapshot_diagnostics())
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
    libs.successor_preparation_workspace_v1.publish(c.ROOT, output, row, a)
    print(json.dumps({k: row.get(k) for k in ('state', 'contracts', 'contract_failures', 'semantic_inputs', 'physical_inputs',
        'physical_bytes', 'predicted_complete_seconds_with_readiness', 'fresh_inputs', 'final_fresh_hashes',
        'elapsed_seconds', 'CPU_max', 'owned_CPU_machine_max', 'owned_private_MiB_max', 'RAM_min',
        'cleanup_confirmed', 'subprocess_creation_attempts', 'operation_phase', 'error_code', 'error_frames')}, allow_nan=False))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__ == '__main__': raise SystemExit(main())
