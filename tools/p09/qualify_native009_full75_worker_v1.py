"""Actual75 production CLI diagnostics in two serial owned Jobs.

Retain the original12 launch tests and external permanent product-Popen denial.
Add five75-entry contracts, retain all prior declarations and recost from the
original complete model. No Native/product acceptance or execution authority.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

SELF = 'tools/p09/qualify_native009_full75_worker_v1.py'
ENTRY = 'tools/p09/native009_full75_worker_entry_v1.py'
PREFIX = 'implementation/p09/evidence/p09-361-case165-'
CONSTRUCTION = dict(path='tools/p09/native009_full72_construction_v1.py', bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
CODE = dict(path=PREFIX+'native009-full75-transport-code001.v1.json', bytes=99524,
    sha256='decc6dda5e48bf794d89f334523452a4250e81d13ebfc6c49acf3fe05e5d403b')
OLD_DRIVER = dict(path='tools/p09/qualify_native009_worker_launch_v1.py', bytes=14485,
    sha256='aeb7d606695ab5a7e11b2f050f5e510b311d21badbc7fad4668a8de78f427bcb')
OLD_TEST = dict(path='tools/p09/tests/test_native009_worker_launch_v1.py', bytes=7030,
    sha256='0b3ef0ca56c257857bcc4c0a86a0d4e3b5f1c9bf7e587780178f8f17e219a6c0')
READINESS = [dict(path='tools/p09/worker_readiness_v1.py', bytes=6890,
    sha256='047c3f78f8a4472feeec4d56b65716f57e0429091321cb49afe5b685047d3a45'),
    dict(path='tools/p09/worker_readiness_connection_v1.py', bytes=5775,
    sha256='d306d62a08e16f717bb526b2a7fa6c60ac44890f6fed965fdf4a70daca3c0a9b')]


def require(ok, label):
    if not ok: raise ValueError('NATIVE009_FULL75_WORKER_QUAL_'+label)


def closed_error(stderr):
    import re
    tail = stderr[-16384:]; lines = tail.splitlines(); last = lines[-1] if lines else ''
    kind = re.match(r'([A-Za-z_][A-Za-z0-9_]{0,80})(?::|$)', last)
    allowed = {'ValueError', 'RuntimeError', 'KeyError', 'TypeError', 'AttributeError', 'OSError', 'ImportError',
        'ModuleNotFoundError', 'AssertionError', 'SystemExit', 'JSONDecodeError'}
    code = re.fullmatch(r'(?:ValueError|RuntimeError): ((?:NATIVE009_|ENVELOPE_|AST_|SUCCESSOR_|CLOSED_|CURRENT_|WORKER_|DIAG_|STOP_|SOURCE_|RUNTIME_)[A-Z0-9_]{1,140})', last)
    frames = [dict(file=Path(name).name, line=int(line), function=fn) for name, line, fn in
        re.findall(r'File "([^"\r\n]+)", line ([0-9]+), in ([A-Za-z_][A-Za-z0-9_]*)', tail)[-5:]]
    return dict(exception_type=kind[1] if kind is not None and kind[1] in allowed else None,
        error_code=None if code is None else code[1], frames=frames, raw_log_preserved_or_printed=False)


def main():
    import argparse, importlib.util, io, os, re, subprocess, time, traceback, unittest
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    permit = dict(command=None, calls=0, denied=0)
    def parent_audit(event, args):
        if event == 'subprocess.Popen':
            expected, actual = permit['command'], args[1]
            if expected is None or actual not in (expected, subprocess.list2cmdline(expected)):
                permit['denied'] += 1; raise ValueError('UNEXPECTED_PARENT_SUBPROCESS_DENIED')
            permit['command'] = None; permit['calls'] += 1
    sys.addaudithook(parent_audit)
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import audit_evidence_io as original_io
    from bounded_process_progress import BoundedProcessCapture
    initial, _ = envelope.namespace_bundle.load(c.ROOT, [CONSTRUCTION], {})
    construction = initial.native009_full72_construction_v1
    libs, _ = envelope.namespace_bundle.load(c.ROOT, construction.PINS+READINESS, {})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader, _ = libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle, libs.ast_clone_namespace_v1)
    protocol, connection = libs.worker_readiness_v1, libs.worker_readiness_connection_v1
    parser = argparse.ArgumentParser(); parser.add_argument('--attempt', type=int, required=True)
    attempt = parser.parse_args().attempt
    require(type(attempt) is int and 1 <= attempt <= 8, 'BOUNDED_ATTEMPT')
    output = PREFIX+f'native009-full75-production-worker{attempt:03}.v1.json'
    native = c.ROOT/(PREFIX+'current-runtime-run009.v1.json')
    require(not (c.ROOT/output).exists() and not native.exists(), 'EXCLUSIVE_REPORT_NO_NATIVE009')
    guard = libs.owned_cpu_baseline_v1.guard_type(libs.terminal_metadata_pressure_v1.guard_type(
        libs.distinct_final_sample_guard_v1.guard_type(a.Guard)))()
    started, phase = time.monotonic(), 'CURRENT_ADMISSION'
    row = dict(state='FAILED_FULL75_PRODUCTION_WORKER_NOT_NATIVE', accepted_count_delta=0, GO_authorized=False,
        actual_product_or_Native_executed=False, whole_current_Native_parent_or_Frame_or_dispatch_qualified=False,
        current_result_and_future_parent_dispatch_sources_must_be_recosted=True, preparation_CPU_policy_changed=False, cases=[])
    q = chunk = None
    try:
        guard.acquire(); seed = a.AcceptanceReader(c.ROOT, guard.check)
        current = a.read_exact(seed, CODE); pins = scope.pins(current['source_pins'])
        binding_name = 'tools/p09/legacy149_binding_v1.py'
        a.exact(seed.pin(binding_name), pins[binding_name], 'QUALIFIED_PREPARATION_READER_DEPENDENCIES')
        prepared_readers, _ = loader.load(c.ROOT, [pins[binding_name]], {})
        binding = prepared_readers.legacy149_binding_v1
        for pin in (binding.SNAPSHOT, binding.CHUNK): a.exact(seed.pin(pin['path']), pin, 'CURRENT_SOURCE_AND_BUFFER_HELPERS')
        names, _ = loader.load(c.ROOT, [binding.SNAPSHOT, binding.CHUNK], {'audit_evidence_io': original_io})
        snapshot, chunk = names.single_snapshot_source_guard_v1, names.reusable_audit_chunk_v1
        pin, raw = seed._read(snapshot.ORIGINAL_PIN['path'], parse=True); seed._bind(pin['path'], pin)
        a.exact(pin, snapshot.ORIGINAL_PIN, 'UNCHANGED_AUDIT_LEAF')
        SourceReader, _ = snapshot.reader_type(a.AcceptanceReader, bytes(raw))
        Reader, reader_proof = chunk.reader_type(SourceReader, bytes(raw)); del raw
        q = Reader(c.ROOT, guard.check)
        for pin in seed.snapshots.values(): a.exact(q.pin(pin['path']), pin, 'FRESH_READER_BOOTSTRAP')
        for name in (SELF, ENTRY): q.pin(name)
        for pin in [CONSTRUCTION, OLD_DRIVER, OLD_TEST]+construction.PINS+READINESS:
            a.exact(q.pin(pin['path']), pin, 'CURRENT_PROGRAMS')
        a.fields(current, dict(state='PASS_NATIVE009_FULL75_ORIGINAL_RECONSTRUCTION20_AND_REPLAYABLE_DECLARED_COST_NOT_WORKER_OR_NATIVE',
            contracts=dict(run=20, errors=0, failures=0, skipped=0), fresh_inputs=398, final_fresh_hashes=398,
            inherited_previous_scope_exactly_reconstructed=True, inherited_previous_budget_exactly_reconstructed=True,
            persisted_scope_uses_original_noninjecting_union=True, descriptor_count=75, semantic_inputs=3248,
            cleanup_confirmed=True, actual_engine_worker_calls=0), 'CURRENT_FULL75_PACKET_AND_COMPLETE_DECLARATION')
        for pin in pins.values():
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):
                a.exact(q.pin(pin['path']), pin, 'ALL_CURRENT_PACKET_QUALIFIED_CODE')
        graph_record = a.read_exact(q, current['graph_report_pin'])
        a.exact(graph_record['declared_scope_base_pin'], current['declared_scope_base_pin'], 'SAME_DECLARATION_BASE')
        a.exact(graph_record['declared_scope_delta_pins'], current['declared_scope_delta_pins'], 'SAME_ALL57_DELTA')
        base = a.read_exact(q, current['declared_scope_base_pin'])
        previous = scope.extend(scope.pins(base['input_pins']), {current['declared_scope_base_pin']['path']: current['declared_scope_base_pin']})
        previous = scope.extend(previous, scope.pins(current['declared_scope_delta_pins']))
        parts, _ = loader.load(c.ROOT, [q.snapshots[ENTRY], OLD_DRIVER], {})
        entry, driver = parts.native009_full75_worker_entry_v1, parts.qualify_native009_worker_launch_v1
        a.exact(q.pin(entry.PREVIOUS['path']), entry.PREVIOUS, 'EXACT_WHOLE_PREVIOUS_ENTRY')
        for pin in (entry.OLD_ENTRY, entry.OLD_LAUNCH, entry.TRANSPORT, entry.HINT, entry.WIRE, entry.STEP, *entry.EARLY_AST):
            a.exact(q.pin(pin['path']), pin, 'EXACT_CURRENT_WORKER_DEPENDENCIES')
        worker_api, launch = entry.worker_api(c.ROOT, envelope, loader), entry.launch_api(c.ROOT, loader)
        diagnostic = driver.DIAGNOSTIC
        require(diagnostic.count('.v3.json') == 2 and '.v5.json' not in diagnostic, 'TWO_EXACT_EXTERNAL_AUDIT_METADATA_NAMES')
        revised_diagnostic = diagnostic.replace('.v3.json', '.v5.json')
        require(revised_diagnostic.replace('.v5.json', '.v3.json') == diagnostic, 'WHOLE_EXTERNAL_DENIAL_AUDIT_INVERSE')
        raw = q.text(libs.post_product_recovery_window_v1.WINDOW_PIN['path']).encode('utf-8')
        component = libs.post_product_recovery_window_v1.tighten_window(envelope.prior.WINDOW, raw)
        phase = 'ORIGINAL_LAUNCH_AND_ENTRY_CONTRACTS'
        spec = importlib.util.spec_from_file_location('full75_original_launch_contracts', c.ROOT/OLD_TEST['path'])
        tests = importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
        tests.MODULE = launch; tests.PROTOCOL = protocol; tests.CONNECTION = connection; tests.WINDOW = component
        tests.ENTRY = worker_api; tests.ROOT = c.ROOT; tests.PIN = q.snapshots[ENTRY]
        method = 'test_entry_run9_graph_source_and_no_diagnostic_denial_in_production'
        revised, version_proof = libs.native009_full72_transport_v1.constant(getattr(tests.Tests, method),
            'p09-361-case165-successor-worker-bootstrap009.v3.json', 'p09-361-case165-successor-worker-bootstrap009.v5.json', method,
            'test_native009_worker_launch_v1.py')
        setattr(tests.Tests, method, revised)
        def original_main_execute_argument_and_read_bodies_retained():
            for name in ('main', 'execute', 'arguments', 'read'):
                old, fn = getattr(worker_api.original_api, name), getattr(worker_api, name)
                require(fn.__code__ is old.__code__ and fn.__defaults__ is old.__defaults__ and fn.__closure__ is old.__closure__, 'WHOLE_ORIGINAL_WORKER_ENTRY_FUNCTION')
            require(worker_api.original_api.HINT['path'].endswith('.v3.json') and worker_api.HINT == entry.HINT, 'ORIGINAL_DEFAULT_ENTRY_UNCHANGED')
        def entire_original_launch_family_retained():
            for item in launch.family_proofs:
                old, fn = getattr(launch.original_api, item['function']), getattr(launch, item['function'])
                require(fn.__code__ is old.__code__ and fn.__defaults__ is old.__defaults__ and fn.__closure__ is old.__closure__, 'WHOLE_ORIGINAL_LAUNCH_FUNCTION')
            require(launch.ENTRY == ENTRY and launch.original_api.ENTRY != ENTRY, 'ONE_EXPLICIT_PRIVATE_ENTRY_PATH')
        def exact_v5_metadata_and_original_limits():
            a.exact(worker_api.HINT, current['bootstrap_pin'], 'ACTUAL_CURRENT_V5_HINT')
            a.exact(worker_api.WIRE, current['capsule_pin'], 'ACTUAL_CURRENT_V5_WIRE')
            require(protocol.SECONDS == 15 and component.SECONDS == 10 and len(worker_api.family_proofs) >= 5, 'ORIGINAL_READY15_CAPTURE10')
        def preparation_body_has_exact_count_and_namespace_inverse():
            proof = worker_api.preparation_slots_proof
            require(proof['old_count'] == 73 and proof['new_count'] == 75 and proof['entire_code_inverse'], 'FULL_PREPARATION_INVERSE')
            before, after = worker_api.preparation_before, worker_api.prepare
            require(before.__globals__ is after.__globals__ and before.__defaults__ is after.__defaults__
                and before.__closure__ is after.__closure__ and before.__code__.co_code == after.__code__.co_code, 'WHOLE_ORIGINAL_PREPARATION_BODY')
            require(after is worker_api.main.__globals__['prepare'], 'ORIGINAL_MAIN_CALLS_REVISED_PREPARATION')
        def unrelated_preparation_body_and_missing_slots_rejected():
            for fn in (worker_api.main, worker_api.prepare):
                try: entry.prepare_slots(fn)
                except ValueError: pass
                else: raise ValueError('NATIVE009_FULL75_BAD_PREPARATION_ACCEPTED')
        def early_AST_copy_changes_only_explicit_dependency():
            a.fields(worker_api.early_ast_loader_proof, dict(root_and_private_helper_copy_dependency_connected=True,
                complete_original_loader_code_retained=True, default_copy_or_importlib_changed=False,
                byte_hash_AST_or_JSON_cache=False, Native_or_GO_authorized=False), 'QUALIFIED_EARLY_LOADER_ONLY')
        suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(tests)]+[
            unittest.FunctionTestCase(fn) for fn in (original_main_execute_argument_and_read_bodies_retained,
                entire_original_launch_family_retained, exact_v5_metadata_and_original_limits,
                preparation_body_has_exact_count_and_namespace_inverse, unrelated_preparation_body_and_missing_slots_rejected,
                early_AST_copy_changes_only_explicit_dependency)])
        result = unittest.TextTestRunner(stream=io.StringIO(), failfast=True).run(suite)
        row['contracts'] = dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped))
        row['contract_failures'] = [dict(test=t.id().rsplit('.', 1)[-1], exception_type=trace.splitlines()[-1].split(':', 1)[0])
            for t, trace in result.errors+result.failures]
        a.exact(row['contracts'], dict(run=18, errors=0, failures=0, skipped=0), 'ORIGINAL12_AND_ENTRY6')
        row.update(original_launch_test_metadata_inverse=version_proof, preparation_slots_proof=worker_api.preparation_slots_proof)
        for mode in ('EOF', 'GO_DENIED'):
            phase = 'ACTUAL_PRODUCTION75_MAIN_'+mode; guard.check(force=True)
            windows = c.Windows(); job = windows.job(); process = capture = api = None
            assigned = False; terminal = details = audit = None; begin = time.monotonic()
            try:
                limits = windows.verify_job_limits(job)
                expected = [str(c.ROOT/scope.EXE_PIN['path']), q.json(entry.HINT['path'])['step']['case'],
                    '--exact', '--test-threads=1', '--format=pretty', '--color=never']
                def diagnostic_factory(command, **kwargs):
                    require(command[:3] == [sys.executable, '-B', str(c.ROOT/ENTRY)], 'EXACT_PRODUCTION_ENTRY_COMMAND')
                    actual = [sys.executable, '-B', '-c', revised_diagnostic, command[2], json.dumps(expected), *command[3:]]
                    require(permit['command'] is None, 'ONE_PARENT_LAUNCH_PERMIT'); permit['command'] = actual
                    try: return subprocess.Popen(actual, **kwargs)
                    finally: permit['command'] = None
                def owned(actual): return launch.same_owned_job(windows, job, process, actual)
                api = launch.connect(c.ROOT, q.snapshots[ENTRY], component, protocol, connection, diagnostic_factory,
                    BoundedProcessCapture, subprocess, owned, guard.check)
                command = [sys.executable, str(c.ROOT/'tools/p09/current_queue_successor_runtime.py'), '--owned-worker', '--task', entry.TASK]
                process = api.Popen(command, cwd=c.ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW)
                handle = windows.k.OpenProcess(0x101, False, process.pid)
                try: require(handle and windows.k.AssignProcessToJobObject(job, handle), 'ORIGINAL_JOB_ASSIGN'); assigned = True
                finally:
                    if handle: require(windows.k.CloseHandle(handle), 'PROCESS_HANDLE_CLOSE')
                if mode == 'EOF': process.stdin.close(); capture = BoundedProcessCapture(process)
                else: process.stdin.write(protocol.GO); process.stdin.flush(); capture = api.Capture(process)
                deadline = time.monotonic()+15
                while True:
                    guard.check(); require(time.monotonic() < deadline, 'CHILD_CAPTURE_BOUND')
                    try: stdout, stderr = capture.communicate(.1); break
                    except subprocess.TimeoutExpired: capture.progress()
                lines = stderr.splitlines()
                if len(lines) != 2 or any(len(line) > 4096 for line in lines):
                    row['closed_child_setup_failure'] = closed_error(stderr)
                    raise ValueError('NATIVE009_FULL75_CHILD_SETUP_NOT_CLOSED_METADATA')
                details, audit = json.loads(lines[0]), json.loads(lines[1])
                a.fields(details, dict(terminal='WORKER_NOT_AUTHORIZED' if mode == 'EOF' else 'NATIVE009_WORKER_EXECUTION_FAILED',
                    task=entry.TASK, descriptor_count=75, actual_worker_attempts=1, actual_worker_calls=1, raw_policy_restored=True,
                    original_worker_code='run_case112_current_stored.py', source_step_pin_checked_before_after=True,
                    Native_source_Frame_or_acceptance_qualified=False), 'ACTUAL75_ORIGINAL_WORKER')
                a.exact(audit, dict(diagnostic_audit=dict(product_popen_calls=0 if mode == 'EOF' else 1,
                    exact_product_command=None if mode == 'EOF' else True, other_JSON_opens=0, step_JSON_reads=3),
                    all_subprocess_denied_before_OS_create=True), 'PERMANENT_EXTERNAL_PRODUCT_DENIAL')
                require(type(details['child_default_project_helper_count']) is int and details['child_default_project_helper_count'] <= 64,
                    'ACTUAL_CHILD_HELPER64')
                require(process.returncode == 1 and stdout == '', 'ORIGINAL_CLOSED_DIAGNOSTIC_EXIT')
            finally:
                require(windows.k.TerminateJobObject(job, 1), 'OWNED_JOB_TERMINATE')
                if process is not None:
                    if not assigned and process.poll() is None: process.terminate()
                    process.wait(timeout=2)
                if capture is not None: capture.close()
                elif process is not None:
                    for stream in (process.stdin, process.stdout, process.stderr): stream.close()
                until = time.monotonic()+2
                while True:
                    terminal = windows.accounting(job)
                    if terminal['active_processes'] == 0: break
                    require(time.monotonic() < until, 'OWNED_JOB_EMPTY_BOUND'); time.sleep(.02)
                require(windows.k.CloseHandle(job), 'OWNED_JOB_CLOSE')
                if api is not None:
                    for event in api.events: event.close()
                row['last_owned_cleanup'] = dict(active_after_cleanup=terminal['active_processes'],
                    Job_CPU_seconds=terminal['job_cpu_seconds'], Job_peak_private_MiB=terminal['peak_job_private_mib'], job_handle_closed=True)
            row['cases'].append(dict(mode=mode, child_terminal=details, diagnostic_audit=audit, window=api.state.diagnostics(),
                owned_limits_readback=limits, active_after_cleanup=terminal['active_processes'], cleanup_confirmed=True,
                elapsed_seconds=time.monotonic()-begin, Job_CPU_seconds=terminal['job_cpu_seconds'], Job_peak_private_MiB=terminal['peak_job_private_mib']))
        phase = 'EXACT_PREVIOUS_SCOPE_AND_CURRENT_COST'
        for name in (PREFIX+'native009-full75-production-worker001.v1.json',
            'implementation/p09/evidence/source-archive/p361-full75-worker-attempt001/native009_full75_worker_entry_v1.py',
            'implementation/p09/evidence/source-archive/p361-full75-worker-attempt001/qualify_native009_full75_worker_v1.py'):
            q.pin(name)
        loader, _ = construction.private_runtime_imports(loader)
        transport_names, _ = loader.load(c.ROOT, [entry.TRANSPORT], {})
        transport = transport_names.native009_full75_transport_v1
        facade = NS(connect=transport.connect, constant=libs.native009_full72_transport_v1.constant)
        hint = a.read_exact(q, entry.HINT)
        fresh = libs.native009_verified_source_profile_v1.connect(c.ROOT, loader, scope, bytes_policy,
            libs.receipt_xz_envelope_v1, libs.bounded_successor_capsule_wire_v2, guard.check, a, q, hint, facade)
        actual, wire = q._read(entry.WIRE['path'], parse=True); q._bind(actual['path'], actual)
        a.exact(actual, entry.WIRE, 'CURRENT_WIRE_FOR_COST_GRAPH')
        graph, _ = fresh.api.reconstruct(hint, bytes(wire), guard.check); del wire
        engine = fresh.api.build(c.ROOT, loader, fresh.api, graph, envelope.prior, libs.post_product_recovery_connection_v1,
            libs.post_product_recovery_window_v1, guard.check)
        previous, _ = graph.binding.semantic_union(previous, guard.check)
        a.exact(len(previous), current['semantic_inputs'], 'ALL_PREVIOUS3248_NOT_FRESH_SUBSET')
        prior_budget = graph.binding.runtime_budget(previous, current['inventory_requests'], engine.window.DIRECT.runtime_budget, guard.check)
        a.exact(prior_budget, current['original_complete_runtime_budget'], 'EXACT_PREVIOUS_COMPLETE_MODEL')
        for module in tuple(sys.modules.values()):
            filename = getattr(module, '__file__', None)
            if filename:
                path = Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix == '.py': q.pin(path.relative_to(c.ROOT).as_posix())
        required, _ = graph.binding.semantic_union(scope.extend(previous, q.snapshots), guard.check)
        require(all(required.get(n) == pin for n, pin in previous.items()), 'NO_PREVIOUS_INPUT_REMOVED')
        inventory = a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'), ('rust_inputs',), dict(os=os, Path=Path, require=require))
        requests = []
        def paced(): requests.append(1); q.open_pacer.reserve()
        rust = inventory.rust_inputs(c.ROOT, paced)
        require(len(rust) == 787 and set(rust) <= set(required), 'CURRENT_RUST787')
        budget = graph.binding.runtime_budget(required, len(requests), engine.window.DIRECT.runtime_budget, guard.check)
        total = budget['predicted_runtime_combined_seconds']+15
        parent_name = 'tools/p09/qualify_native009_full73_parent_v1.py'
        upstream, _ = loader.load(c.ROOT, [pins[parent_name]], {})
        _, delta = upstream.qualify_native009_full73_parent_v1.compact_scope(graph.binding, type(graph.binding).semantic_union,
            scope, base, current['declared_scope_base_pin'], required, guard.check, a.exact)
        row.update(original_complete_runtime_budget=budget, predicted_complete_seconds_with_readiness=total,
            declared_cost_nominal_fits600=total < 600, additional_readiness_seconds_without_old_credit=15,
            semantic_inputs=len(required), current_Rust_path_count=len(rust), inventory_requests=len(requests),
            declared_scope_base_pin=current['declared_scope_base_pin'], declared_scope_delta_pins=delta,
            persisted_scope_uses_original_noninjecting_union=True, previous_scope_and_budget_exactly_reconstructed=True,
            parent_cost_graph_worker_calls=engine.state.calls, transport_code_pin=CODE, graph_report_pin=current['graph_report_pin'],
            preparation_reader_connection=reader_proof)
        require(total < 600, 'CURRENT_COMPLETE_SCOPE_PLUS_READINESS_OUTSIDE600')
        phase = 'FINAL_METADATA_HASHES'; q.finish(); guard.check(force=True)
        require(permit['calls'] == 2 and permit['denied'] == 0 and permit['command'] is None and not native.exists(),
            'ONLY_TWO_DIAGNOSTIC_CHILDREN_NO_NATIVE')
        row.update(state='PASS_FULL75_PRODUCTION_MAIN_EOF_AND_PRODUCT_DENIED18_WITH_REPLAYABLE_DECLARED_COST_NOT_NATIVE',
            source_pins=list(q.snapshots.values()), fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
            whole_external_denial_audit_inverse=True)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, NameError) as error:
        row['error_type'] = type(error).__name__
        row['error_frames'] = [dict(file=Path(f.filename).name, function=f.name, line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}', error.args[0]): row['error_code'] = error.args[0]
    finally:
        if q is not None:
            row.update(fresh_inputs_observed=len(q.snapshots), closing_hashes_completed=q.final_fresh_hashes,
                metadata_read_passes=q.read_passes, metadata_physical_bytes=q.bytes_read,
                metadata_source_predicate_optimization=q.source_snapshot_diagnostics())
            if chunk is not None and hasattr(q, chunk.ATTRIBUTE): row['preparation_chunk_workspace'] = chunk.summary(q)
        row.update(diagnostic_child_launches=permit['calls'], denied_unexpected_parent_launches=permit['denied'],
            last_original_guard_samples=guard.samples[-8:])
        guard.close()
        row.update(cleanup_confirmed=guard.cleanup, operation_phase=phase, elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples), default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None), default=None),
            owned_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples if s.get('parent_private_mib') is not None), default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples), default=None))
    require(guard.cleanup, 'OWNER_CLEANUP')
    libs.successor_preparation_workspace_v1.publish(c.ROOT, output, row, a)
    print(json.dumps({k: row.get(k) for k in ('state', 'contracts', 'contract_failures', 'cases', 'closed_child_setup_failure',
        'last_owned_cleanup', 'diagnostic_child_launches', 'semantic_inputs', 'predicted_complete_seconds_with_readiness',
        'fresh_inputs', 'final_fresh_hashes', 'elapsed_seconds', 'CPU_max', 'owned_CPU_machine_max', 'owned_private_MiB_max',
        'RAM_min', 'cleanup_confirmed', 'operation_phase', 'error_code', 'error_frames')}, allow_nan=False))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__ == '__main__': raise SystemExit(main())
