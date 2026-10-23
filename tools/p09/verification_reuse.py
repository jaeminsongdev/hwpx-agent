"""Read-only reuse dispatch for the last qualified fixed162 preparation.

Keep the existing result when its exact receipt and ALL declared dependencies
are unchanged. Do not rerun its constructors/contracts or recursively expand
the dependency receipts. This retains historical preparation evidence, NOT a
fresh runtime/environment, budget, Native, product or Gate qualification.

The command writes no receipts/cache and never imports the prepared engine.
Its original paced reader still reads every selected file again at closing.
"""
import copy
import json
import re

SELF = 'tools/p09/verification_reuse.py'
TEST = 'tools/p09/tests/test_verification_reuse.py'
PROOF = dict(
    path='implementation/p09/evidence/p09-361-case165-fixed162-worker-transport-g001-code002.v1.json',
    bytes=55056,
    sha256='9c96a89833b30dc53c464e19b298846f50085ead9595e768ab0ad3531a962713')
STATE = 'PASS_FIXED162_BOUNDED_BOOTSTRAP_AND_ORIGINAL_RECONSTRUCTION16_NOT_WORKER_PROCESS_OR_NATIVE'
DEPENDENCIES = 185
REQUIRED = (
    'tools/p09/qualify_fixed162_worker_transport_v1.py',
    'tools/p09/tests/test_fixed162_worker_transport_v1.py',
    'tools/p09/fixed162_worker_transport_v1.py',
    'tools/p09/fixed165_history_declaration_v1.py',
    'tools/p09/bounded_binary_capsule_wire_v3.py',
)


def require(value, code):
    if not value:
        raise ValueError('VERIFICATION_REUSE_' + code)


def exact(left, right):
    if type(left) is not type(right):
        return False
    if type(right) is dict:
        return set(left) == set(right) and all(exact(left[k], v) for k, v in right.items())
    if type(right) is list:
        return len(left) == len(right) and all(exact(a, b) for a, b in zip(left, right))
    return left == right


def pins(rows):
    require(type(rows) is list and len(rows) == DEPENDENCIES, 'EXACT_DEPENDENCY_COUNT')
    result = {}
    folded = set()
    for row in rows:
        require(type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}, 'PIN_SHAPE')
        name = row['path']
        require(type(name) is str and 0 < len(name) <= 1024
            and not name.startswith('/') and not any(c in name for c in '\\:*?<>|"')
            and not any(ord(c) < 32 for c in name)
            and all(part not in ('', '.', '..') and not part.endswith((' ', '.'))
                    for part in name.split('/')), 'DIRECT_RELATIVE_PATH')
        require(type(row['bytes']) is int and 0 < row['bytes'] <= 512 * 1024 * 1024
            and type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256']), 'PIN_VALUES')
        require(name.casefold() not in folded, 'NO_DUPLICATE_OR_WINDOWS_ALIAS')
        folded.add(name.casefold())
        result[name] = dict(row)
    require(set(REQUIRED) <= set(result) and PROOF['path'] not in result, 'CLOSED_EXISTING_DEPENDENCIES')
    return result


def dependencies(row):
    require(type(row) is dict, 'PROOF_OBJECT')
    expected = dict(state=STATE, contracts=dict(run=16, errors=0, failures=0, skipped=0),
        descriptor_count=162, fresh_inputs=DEPENDENCIES, final_fresh_hashes=DEPENDENCIES,
        cleanup_confirmed=True, accepted_count_delta=0, GO_authorized=False,
        Native009_replayed=False, worker_process_engine_Job_Frame_or_Native_executed=False,
        current_full_runtime_scope_or_helper64_qualified=False,
        actual_metadata_Frame_shared_decoder5_qualified=False,
        original_limits_or_preparation_CPU_policy_changed=False, subprocess_creation_attempts=0,
        actual_current162_original_decoder_completed=True, reconstruction_JSON_file_opens=0)
    require(all(exact(row.get(k), value) for k, value in expected.items()), 'EXACT_CLOSED_PREPARATION16_ONLY')
    result = pins(row.get('source_pins'))
    for key in ('manifest_pin', 'wire_pin', 'bootstrap_pin', 'data_source_module_pin'):
        value = row.get(key)
        require(type(value) is dict and exact(result.get(value.get('path')), value), 'ALL_ACTUAL_ARTIFACT_PINS')
    return result


def check(reader):
    """Only select an existing result; caller MUST finish reader and guards."""
    row = reader.json(PROOF['path'])
    require(exact(reader.snapshots.get(PROOF['path']), PROOF), 'IMMUTABLE_PROOF_HASH')
    expected = dependencies(row)
    for name, pin in expected.items():
        require(exact(reader.pin(name), pin), 'DEPENDENCY_CHANGED_REVERIFY_REQUIRED')
    return dict(state='UNCHANGED_PREPARATION_RESULT_RETAINED_NOT_CURRENT_RUNTIME_QUALIFICATION',
        retained_proof_pin=copy.deepcopy(PROOF), unchanged_dependencies=len(expected),
        preparation_contracts_retained=16, preparation_contracts_reexecuted=0,
        historical_receipts_recursively_revalidated=False,
        current_runtime_budget_reused=False, prior_resource_measurements_reused=False,
        current_environment_qualified=False, Native_source_frame_qualified=False,
        accepted_count_delta=0, GO_authorized=False, product_executed=False,
        whole_current_source_scope_changed=False, evidence_files_created=0)


def complete(reader, guard):
    candidate = check(reader)
    reader.finish()
    guard.check(force=True)
    require(reader.final_fresh_hashes == len(reader.snapshots), 'ALL_CLOSING_HASHES')
    return candidate


def main():
    import argparse
    import importlib.util
    import io
    import sys
    import time
    import unittest

    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser(description=__doc__)
    tests = parser.add_mutually_exclusive_group()
    tests.add_argument('--self-test', action='store_true', help='Run reuse-dispatch contracts once before checking')
    tests.add_argument('--self-test-only', action='store_true', help='Check only changed dispatch code, not the historical dependency set')
    tests.add_argument('--batch-policy-tests', action='store_true', help='Check the new batch policy and the real scope source body; no history scan or Native')
    tests.add_argument('--batch-policy-io-check', action='store_true', help='Exercise actual batch start/current/end reads on four fixed small files only; not a current runtime scope qualification')
    tests.add_argument('--batch-policy-plan', action='store_true', help='Reconstruct the saved3305 declaration and explicit phase partition from pinned records; no corpus rehash, decoder, constructor or Native')
    tests.add_argument('--batch-policy-connect', action='store_true', help='Connect the real qualified fixed162 preparation graph to the batch scope; no engine, process, GO or Native')
    tests.add_argument('--batch-engine-connect', action='store_true', help='Construct the actual run010 engine and historical checker; no worker body, process or GO')
    tests.add_argument('--batch-package', action='store_true', help='Publish exclusive NO-GO manifest/wire/bootstrap/report and verify real file entry; no engine or process')
    parser.add_argument('--package-generation', type=int, choices=range(1,9), default=1,
        help='Explicit immutable preparation report generation, not a product run or automatic retry')
    args = parser.parse_args()
    if args.batch_package:args.batch_policy_connect = True
    denied = []

    def audit(event, values):
        if event in ('subprocess.Popen', 'os.system', 'os.startfile'):
            denied.append(1)
            raise ValueError('VERIFICATION_REUSE_SUBPROCESS_DENIED')
    sys.addaudithook(audit)
    import accept_case112_current_epoch as a
    import conservative_maintenance as c
    import distinct_final_sample_guard_v1 as final
    import owned_cpu_baseline_v1 as baseline
    import prepared_run_closure_v1 as policy
    import terminal_metadata_pressure_v1 as pressure
    policy.configure_host_policy(c)
    guard = baseline.guard_type(pressure.guard_type(final.guard_type(a.Guard)))()
    reader = None
    pending_package = package_module = None
    started = time.monotonic()
    summary = dict(state='REVERIFY_REQUIRED_NOT_REUSED', accepted_count_delta=0,
        GO_authorized=False, product_executed=False, evidence_files_created=0)
    try:
        guard.acquire()
        reader = a.AcceptanceReader(c.ROOT, guard.check)
        reader.pin(SELF)
        reader.pin(TEST)
        if args.batch_policy_tests or args.batch_policy_io_check or args.batch_policy_plan or args.batch_policy_connect or args.batch_engine_connect:
            policy_path = 'tools/p09/batch_verification.py'
            contract_path = 'tools/p09/tests/test_batch_verification.py'
            worker_entry_path = 'tools/p09/batch_worker_entry.py'
            package_path = 'tools/p09/batch_preparation_package.py'
            reader.pin(policy_path)
            reader.pin(contract_path)
            reader.pin(worker_entry_path)
            reader.pin(package_path)
            spec = importlib.util.spec_from_file_location('batch_verification', c.ROOT / policy_path)
            batch_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(batch_module)
        if args.batch_policy_plan or args.batch_policy_connect or args.batch_engine_connect:
            current_doc = a.read_exact(reader, PROOF)
            dependencies(current_doc)
            packet_doc = a.read_exact(reader, current_doc['prior_probe_pin'])
            history_path = 'implementation/p09/evidence/p09-361-case165-legacy-history-binding-code001.v1.json'
            history_pin = next(p for p in current_doc['source_pins'] if p['path'] == history_path)
            history_doc = a.read_exact(reader, history_pin)
            native_doc = a.read_exact(reader, dict(
                path='implementation/p09/evidence/p09-361-case165-current-runtime-run009.v1.json', bytes=5046802,
                sha256='3588e9d53ff9b442c711d165e8ad09fb93627bc0dc756a467a059f11a71ce753'))
            manifest_doc = a.read_exact(reader, current_doc['manifest_pin'])
            hint_doc = a.read_exact(reader, current_doc['bootstrap_pin'])
            declared = batch_module.reconstruct_declared_scope(native_doc, history_doc, packet_doc,
                current_doc, manifest_doc, guard.check)
            # Challenge the reconstructed declaration in memory, not by
            # modifying originals or rehashing the whole corpus again.
            rejected = 0
            if args.batch_policy_plan:
                wrong_count = copy.deepcopy(current_doc)
                wrong_count['declared_semantic_inputs'] -= 1
                wrong_dimensions = copy.deepcopy(current_doc)
                wrong_dimensions['complete_prototype_runtime_budget']['other_bytes'] += 1
                duplicate = copy.deepcopy(manifest_doc)
                duplicate['descriptors'][-1] = copy.deepcopy(duplicate['descriptors'][0])
                conflicting = copy.deepcopy(current_doc)
                old_names = {p['path'] for p in native_doc['source_input_representation']['semantic_source_freeze']}
                common = next(p for p in conflicting['source_pins'] if p['path'].startswith('tools/') and p['path'] in old_names)
                common['sha256'] = ('f' if common['sha256'] != 'f'*64 else 'e') * 64
                challenges = (
                    (wrong_count, manifest_doc, 'BATCH_VERIFY_EXACT_SAVED_DECLARATION_STAGE'),
                    (wrong_dimensions, manifest_doc, 'BATCH_VERIFY_EXACT_SAVED_SCOPE_COUNTS_BYTES_AND_DIRECTORIES'),
                    (current_doc, duplicate, 'BATCH_VERIFY_UNIQUE_COMPLETE162_PAIRS'),
                    (conflicting, manifest_doc, 'CURRENT_STORED_RUNTIME_SCOPE_CONFLICT_NOT_SILENT_REBASE'))
                for challenged, descriptors, expected_error in challenges:
                    try:
                        batch_module.reconstruct_declared_scope(native_doc, history_doc, packet_doc,
                            challenged, descriptors, guard.check)
                    except ValueError as error:
                        # A CPU/RAM/reader stop is never a passing negative test.
                        if error.args != (expected_error,):
                            raise
                        rejected += 1
                require(rejected == len(challenges), 'ALL_DECLARATION_CHALLENGES_REJECTED')
            explicit = declared.to_physical(current_doc['source_pins'])
            prior = declared.to_physical([hint_doc['step']['prior_queue_pin'], hint_doc['step']['prior_candidate_pin']])
            mandatory = set(explicit) | set(prior) | set(native_doc['imported_worker_source_paths'])
            require(mandatory <= set(declared.physical), 'ALL_EXPLICIT_REFERENCE_DEPENDENCIES_RETAINED')
            plan = batch_module.partition.candidate(declared.physical, 165, tuple(sorted(mandatory)), guard.check)
            hot = batch_module.scope.pins(plan['per_case_candidate'])
            cold = batch_module.scope.pins(plan['batch_preservation_candidate'])
            proposed = batch_module.Batch(declared.physical, hot, cold, first_index=165, checkpoint=guard.check)
            policy_sources = {n: dict(reader.snapshots[n]) for n in (SELF, TEST, policy_path, contract_path, worker_entry_path, package_path)}
            legacy_config = batch_module.LEGACY_CONFIG
            a.exact(reader.fresh_pin(legacy_config['path']), legacy_config, 'EXACT_COMMITTED_LEGACY_CONFIGURATION')
            policy_inputs = batch_module.scope.extend(policy_sources, {legacy_config['path']:legacy_config})
            policy_whole = batch_module.scope.extend(declared.physical, policy_inputs)
            policy_current = batch_module.scope.extend(hot, policy_inputs)
            current_policy = batch_module.Batch(policy_whole, policy_current, cold,
                first_index=165, checkpoint=guard.check)
            summary.update(reference_declaration=declared.proof,
                declaration_negative_checks=rejected,
                reference_phase_partition=proposed.summary(),
                current_policy_declaration=current_policy.summary(),
                current_policy_program_pins=list(policy_sources.values()),
                explicit_committed_legacy_configuration_pin=legacy_config,
                reference_current_bytes=sum(p['bytes'] for p in hot.values()),
                reference_preservation_bytes=sum(p['bytes'] for p in cold.values()),
                explicit_reference_dependencies_protected=len(mandatory),
                policy_programs_added_explicitly_not_by_transitive_receipt_union=sum(n not in declared.physical
                    for n in (SELF, TEST, policy_path, contract_path, worker_entry_path, package_path)),
                full_reference_source_bytes_rehashed=False, actual_engine_or_Native_connected=False,
                real_current_runtime_manifest_qualified=False)
            if args.batch_policy_connect or args.batch_engine_connect:
                import owned_source_read_pressure as bytes_policy
                connected = batch_module.connect_preparation(c.ROOT, reader, current_doc, manifest_doc,
                    hint_doc, declared, current_policy, a, bytes_policy)
                prior_doc = a.read_exact(reader, hint_doc['step']['prior_candidate_pin'])
                membership = current_policy.bootstrap_declaration(prior_doc['bootstrap_metadata']['input_pins'],
                    connected.graph.binding)
                authority_doc = a.read_exact(reader, hint_doc['step']['prior_queue_pin'])
                actual_scope = connected.api.runtime.current_input_scope
                imported = actual_scope.__builtins__['__import__']
                private_binding = imported('current_queue_successor_binding', actual_scope.__globals__, None, (), 0)
                derived = private_binding.inherited_scope(batch_module.scope, prior_doc['source_input_representation'],
                    authority_doc['fresh_input_pins'], connected.source_pins, guard.check)
                seeded = current_policy.scope_declaration(derived, connected.graph.binding)
                expected = batch_module.scope.extend(declared.logical, policy_inputs)
                a.exact(seeded, expected, 'REAL_DERIVED_SCOPE_AND_EXPLICIT_BATCH_DECLARATION')
                summary['real_preparation_connection'] = {key: value for key, value in connected.proof.items()
                    if key not in ('decoder_reconstruction', 'scope_adapter')}
                summary['real_preparation_connection'].update(
                    original_scope_AST_inverse=connected.proof['scope_adapter']['exact_original_AST_inverse'],
                    prior164_bootstrap_declared_inputs=len(prior_doc['bootstrap_metadata']['input_pins']),
                    prior164_bootstrap_physical_memberships=len(membership),
                    real_prior_and_authority_scope_composition_verified=True,
                    real_seeded_logical_inputs=len(seeded),
                    prior_unit_and_declaration_negative_tests_reexecuted=False)
                if args.batch_engine_connect:
                    assembled = batch_module.construct_runtime(c.ROOT, reader, connected, current_policy,
                        expected, batch_module.scope.extend(declared.logical, policy_inputs), a)
                    summary['actual_engine_connection'] = assembled.proof
                    summary['actual_engine_or_Native_connected'] = True
                if args.batch_package:
                    spec = importlib.util.spec_from_file_location('batch_preparation_package', c.ROOT/package_path)
                    package_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(package_module)
                    summary['package_artifact_paths'] = list(package_module.PATHS[:3])+[package_module.report_path(args.package_generation)]
                    summary['evidence_files_created'] = None  # On failure, preserve and inspect partial writes.
                    publisher_path = 'tools/p09/native009_parent_scope_v1.py'
                    known = batch_module.scope.extend(expected, batch_module.scope.pins(current_doc['source_pins']))
                    libraries, _ = connected.loader.load(c.ROOT, [known[publisher_path]], {})
                    import batch_worker_entry as worker
                    pending_package = package_module.prepare(c.ROOT, reader, guard, connected, manifest_doc,
                        hint_doc, current_doc, prior_doc, private_binding.PROVENANCE_KEYS, known, bytes_policy,
                        a, libraries.native009_parent_scope_v1, worker)
                    summary['package_data_preparation'] = pending_package.proof
        if args.batch_policy_io_check:
            historical = dict(path='implementation/p09/evidence/p09-361-case130-compound-predecessor-data001.v1.json',
                bytes=1295, sha256='7f6723ff3669940c4c1da364bd2b0c49551c0271e4f7d9a45fc941a97dc7bd62')
            current = {n: dict(reader.snapshots[n]) for n in (SELF, policy_path, contract_path)}
            whole = {**current, historical['path']: historical}
            batch = batch_module.Batch(whole, current, {historical['path']: historical},
                first_index=165, checkpoint=guard.check)
            def phase_reader():
                value = a.AcceptanceReader(c.ROOT, guard.check)
                value.pacer = reader.pacer
                value.open_pacer = reader.open_pacer
                return value
            opening = phase_reader()
            batch.begin(opening)
            metadata_reader = phase_reader()
            with batch.metadata_reader(metadata_reader):
                a.exact(metadata_reader.fresh_pin(SELF), current[SELF], 'ACTUAL_CURRENT_POLICY_METADATA')
                selected = batch.select_current(whole, metadata_reader)
                a.exact(selected, current, 'ACTUAL_DECLARED_CURRENT_SET_NOT_WHOLE')
            metadata_reader.finish()
            closing = phase_reader()
            details = batch.finish(closing)
            summary.update(batch_policy_IO=details,
                actual_batch_boundary_file_reads=opening.read_passes+closing.read_passes,
                actual_batch_boundary_bytes=opening.bytes_read+closing.bytes_read,
                actual_current_metadata_final_hashes=metadata_reader.final_fresh_hashes,
                actual_preservation_policy_IO_verified=True, real_current_runtime_manifest_qualified=False)
        if args.batch_policy_tests:
            reader.pin('tools/p09/runtime_envelope_full_oracle_connection_v1.py')
            engine_pin, engine_raw = reader._read(batch_module.ENGINE, parse=True)
            reader._bind(engine_pin['path'], engine_pin)
            actual, raw = reader._read(batch_module.RUNTIME, parse=True)
            reader._bind(actual['path'], actual)
            require(actual['sha256'] == batch_module.RUNTIME_SHA, 'EXACT_ORIGINAL_SCOPE_FOR_BATCH_TESTS')
            spec = importlib.util.spec_from_file_location('batch_verification_tests', c.ROOT / contract_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.MODULE = batch_module
            module.RAW_RUNTIME = bytes(raw)
            module.RAW_ENGINE = bytes(engine_raw)
            result = unittest.TextTestRunner(stream=io.StringIO(), failfast=True).run(
                unittest.defaultTestLoader.loadTestsFromModule(module))
            summary['self_tests'] = result.testsRun
            summary['contract_failures'] = [dict(test=t.id().rsplit('.', 1)[-1],
                exception_type=trace.splitlines()[-1].split(':', 1)[0],
                policy_codes=re.findall(r'BATCH_VERIFY_[A-Z_]+', trace.splitlines()[-1])[:2],
                missing_attributes=re.findall(r"has no attribute '([A-Za-z_][A-Za-z0-9_]{0,80})'",
                    trace.splitlines()[-1])[:1])
                for t, trace in result.errors + result.failures]
            require(result.wasSuccessful() and not result.skipped and result.testsRun >= 25, 'BATCH_POLICY_SELF_TESTS')
        if args.self_test or args.self_test_only:
            spec = importlib.util.spec_from_file_location('verification_reuse_tests', c.ROOT / TEST)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.MODULE = sys.modules[__name__]
            result = unittest.TextTestRunner(stream=io.StringIO(), failfast=True).run(
                unittest.defaultTestLoader.loadTestsFromModule(module))
            require(result.wasSuccessful() and not result.skipped and result.testsRun >= 12, 'SELF_TESTS')
            summary['self_tests'] = result.testsRun
        if args.self_test_only or args.batch_policy_tests or args.batch_policy_io_check or args.batch_policy_plan or args.batch_policy_connect or args.batch_engine_connect:
            state = ('PASS_BATCH_POLICY_REAL_ENGINE_AND_CHECKER_CONSTRUCTED_NOT_NATIVE' if args.batch_engine_connect
                else 'PASS_BATCH_POLICY_REAL_PREPARATION_GRAPH_CONNECTED_NOT_NATIVE' if args.batch_policy_connect
                else 'PASS_BATCH_POLICY_REFERENCE_DECLARATION_NOT_CURRENT_SCOPE_OR_NATIVE' if args.batch_policy_plan
                else 'PASS_BATCH_POLICY_REAL_SMALL_IO_NOT_FULL_SCOPE_OR_NATIVE' if args.batch_policy_io_check
                else 'PASS_BATCH_POLICY_CONTRACTS_NOT_CURRENT_SCOPE_OR_NATIVE' if args.batch_policy_tests
                else 'PASS_REUSE_DISPATCH_CONTRACTS_ONLY_NOT_REAL_DEPENDENCY_CHECK')
            candidate = dict(state=state,
                retained_preparation_result_checked=False)
            reader.finish()
            guard.check(force=True)
        else:
            candidate = complete(reader, guard)
        require(reader.final_fresh_hashes == len(reader.snapshots) and not denied, 'FRESH_CLOSING_AND_NO_PROCESS')
        summary.update(candidate)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, NameError, ImportError) as error:
        # Never emit arbitrary exception strings, values or receipt contents.
        summary['error_type'] = type(error).__name__
        if args.batch_engine_connect and 'connected' in locals() and hasattr(connected, 'missing_construction_input'):
            summary['missing_declared_project_input'] = connected.missing_construction_input
        if error.args and type(error.args[0]) is str and re.fullmatch('[A-Z0-9_]{1,160}', error.args[0]):
            summary['error_code'] = error.args[0]
        import traceback
        summary['error_frames'] = [dict(file=c.Path(f.filename).name, function=f.name, line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-6:]]
    finally:
        try:
            guard.close()
        except (ValueError, OSError):
            summary['state'] = 'CLEANUP_FAILED_NOT_REUSED'
        if guard.cleanup is not True:
            summary['state'] = 'CLEANUP_FAILED_NOT_REUSED'
        samples = guard.samples
        summary.update(cleanup_confirmed=guard.cleanup,
            fresh_inputs=0 if reader is None else len(reader.snapshots),
            final_fresh_hashes=0 if reader is None else reader.final_fresh_hashes,
            bytes_read=0 if reader is None else reader.bytes_read,
            elapsed_seconds=time.monotonic() - started,
            CPU_max=max((s['system_cpu_percent'] for s in samples), default=None),
            owned_CPU_machine_max=max((s.get('parent_cpu_machine_percent') or 0 for s in samples), default=None),
            private_MiB_max=max((s['parent_private_mib'] for s in samples), default=None),
            RAM_available_min=min((s['available_ram_percent'] for s in samples), default=None),
            subprocess_creation_attempts=len(denied))
        if args.batch_package and pending_package is not None and summary['state'].startswith('PASS_'):
            try:
                package_result = package_module.finish(c.ROOT, pending_package, reader, guard, a, bytes_policy, args.package_generation)
                summary.update(state=package_result['state'], preparation_package=package_result,
                    evidence_files_created=package_result['files_created'])
            except (ValueError, OSError, KeyError, TypeError) as error:
                summary.update(state='FAILED_PACKAGE_FINAL_PUBLICATION_NOT_NATIVE', error_type=type(error).__name__)
                if error.args and type(error.args[0]) is str and re.fullmatch('[A-Z0-9_]{1,160}', error.args[0]):
                    summary['error_code'] = error.args[0]
        print(json.dumps(summary, ensure_ascii=True))
    return 0 if summary['state'].startswith(('UNCHANGED_PREPARATION_RESULT_RETAINED_',
        'PASS_REUSE_DISPATCH_CONTRACTS_ONLY_', 'PASS_BATCH_POLICY_CONTRACTS_', 'PASS_BATCH_POLICY_REAL_SMALL_IO_',
        'PASS_BATCH_POLICY_REFERENCE_DECLARATION_', 'PASS_BATCH_POLICY_REAL_PREPARATION_GRAPH_',
        'PASS_BATCH_POLICY_REAL_ENGINE_AND_CHECKER_', 'PUBLISHED_RUN010_PREPARATION_PACKAGE_')) else 2


if __name__ == '__main__':
    raise SystemExit(main())
