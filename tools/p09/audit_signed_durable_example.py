"""P150 terminal/source audit, same process only; never starts SQL or native work."""
import base64
import hashlib
import io
import json
import re
import sys
import threading
import unittest

import run_signed_durable_example_tests as s
from live_sql_evidence_reader import LiveSQLReader
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher

SELF = 'tools/p09/audit_signed_durable_example.py'
TEST = 'tools/p09/tests/test_signed_durable_example_tests.py'
FIRST = 'implementation/p09/source-archive/p09-150-pre-cwd-diagnostic-r27/failure-preimages.v1.json'
RECOVERED = 'implementation/p09/source-archive/p09-150-diagnostic-helper-recovered-r27/helper-preimages.v1.json'
SPLIT = 'implementation/p09/source-archive/p09-150-pre-compile-run-separation-r27/helper-preimages.v1.json'
DOCS = ('CURRENT_STATE.md', 'implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')


def require(ok, code): s.c.require(ok, 'SIGNED_DURABLE_AUDIT_'+code)


def preimage(p):
    raw = base64.b64decode(p['base64'], validate=True)
    pin = {k: p[k] for k in ('path', 'bytes', 'sha256')}
    require(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'], 'PREIMAGE_BYTES')
    return raw, pin


def audit():
    threads = {t.ident for t in threading.enumerate()}
    resources = SQLRuntimeResources(); receipt = dict(
        schema_version='hwpx-agent.p09-signed-durable-example-terminal-audit/v1',
        state='NOT_ACCEPTED', product_complete=False, P09_gate='OPEN', remaining_non_permission_work_units=76)
    try:
        resources.admit(); q = LiveSQLReader(resources)
        runs = {}
        for number in range(1, 8):
            name = f'implementation/p09/evidence/p09-150-signed-durable-example.actual-run{number:02}.v1.json'
            row = q.json(name); runs[number] = row
            require(row['owned_tree_empty'] and row['cleanup_confirmed']
                    and row['job_final']['active_processes'] == 0 and row['job_final']['owned_processes'] == [], 'TERMINAL_CLEANUP')
            require(row['P09_gate'] == 'OPEN' and not row['product_complete']
                    and not row['actual_SQL_or_native_executed']
                    and not row['durable_signed_SQL_consumer_qualified'], 'NO_PROMOTION')
        require([runs[n]['state'] for n in (1, 2, 3, 4, 6)] ==
                ['STOPPED_NOT_ACCEPTED']*5, 'FAILED_RECEIPTS_PRESERVED')
        require([runs[n]['stop_reason'] for n in (1, 2, 3, 4, 6)] ==
                ['OWNED_COMMAND_FAILED', 'OWNED_RUNNER_FAILURE', 'OWNED_RUNNER_FAILURE', 'OWNED_RUNNER_FAILURE', 'OWNED_COMMAND_FAILED'], 'FAILED_REASONS')
        for number in (5, 7):
            require(runs[number]['state'] == 'PASS_SCOPED_NOT_GATE' and runs[number]['tests_passed'] == 19, 'EXACT19')
        require(runs[5]['diagnostic_working_directory'] == 'repository'
                and runs[6]['diagnostic_working_directory'] == 'package', 'CONTROLLED_CWD')
        for number in (5, 6):
            binary = next(p for p in runs[number]['source_freeze'] if p['path'] == s.BINARY)
            require(q.pin(s.BINARY) == binary, 'SAME_DIAGNOSTIC_BINARY')
        row = runs[7]; capture = row['capture_diagnostics']
        require(row['execution_kind'] == 'owned_compile_no_run_then_exact_test_binary_repository_CWD'
                and row['exit_code'] == 0 and row['worker_created'] and row['job_assigned'] and row['writer_authorized']
                and row['post_hash_stable_admission_revalidated'] and row['compile_admission_RAM_percent'] == 15, 'OWNED_EXECUTION')
        require(capture['error_code'] is None and capture['complete_result_accepted']
                and capture['per_stream_limit_bytes'] == 32768 and not capture['raw_log_content_included']
                and capture['running_test_counts'] == ['19']
                and capture['test_summary_numbers'] == [['19', '0', '0', '0', '0']]
                and capture['compile_only_completed'] and len(capture['compiled_test_artifact']) == 1, 'BOUNDED_CAPTURE')
        artifact, size, digest = capture['compiled_test_artifact'][0]
        compiled = q.pin('target/p09-150-signed-durable/build/debug/examples/'+artifact)
        require(compiled['bytes'] == int(size) and compiled['sha256'] == digest, 'COMPILED_ARTIFACT_WHOLE')
        limits = row['owned_limits_readback']
        require(limits['verified'] and limits['cpu_hard_cap_machine_percent'] == 6.25
                and limits['affinity_mask'] == 1 and limits['priority_class'] == 16384
                and limits['active_process_limit'] == 16 and limits['kill_on_close'] and limits['breakaway_disabled'], 'LIMIT_READBACK')
        require(row['policy'] == s.c.POLICY, 'GLOBAL_POLICY_UNCHANGED')
        current = {p['path']: p for p in row['source_freeze']}
        require(len(current) == len(row['source_freeze']), 'CURRENT_INPUT_UNIQUE')
        for name, pin in current.items(): require(q.pin(name) == pin, 'CURRENT_INPUT_DRIFT')
        rust = {n for n in current if n.startswith(('crates/', 'protocol/generated/rust/', 'tools/xtask/'))
                and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust) == 784 and s.rust_inputs(s.c.ROOT, resources.checkpoint_io) == rust, 'COMPLETE_RUST784')
        protected = row['protected_executables']
        require(len(protected) == 50 and len({p['path'] for p in protected}) == 50, 'PROTECTED_SCOPE')
        for pin in protected: require(q.pin(pin['path']) == pin, 'PROTECTED_EXE_DRIFT')
        for p in q.json(s.ARCHIVE)['files']:
            original, _ = preimage(p)
            restored = s.restore_original(p['path'], q.text(p['path']))
            restored = restored.replace('\n', '\r\n').encode() if b'\r\n' in original else restored.encode()
            require(restored == original, 'WHOLE_ORIGINAL_BODY')
        for p in q.json(s.DRIVERS)['files']:
            _, pin = preimage(p); require(q.pin(p['path']) == pin, 'ORIGINAL_RUNTIME_HELPER')
        archived_failures = {}
        for archive_name in (FIRST, RECOVERED, SPLIT):
            archive = q.json(archive_name)
            parent_pins = archive.get('parent_execution_pins', archive.get('failed_execution_pins', []))
            if 'failed_execution_pin' in archive: parent_pins = [archive['failed_execution_pin']]
            for pin in parent_pins: require(q.pin(pin['path']) == pin, 'FAILED_PARENT_PIN')
            for p in archive['files']:
                _, pin = preimage(p)
                numbers = [p['failed_run']] if 'failed_run' in p else ([1] if archive_name == FIRST else [5, 6])
                for number in numbers:
                    require(pin in runs[number]['source_freeze'], 'FAILED_WHOLE_SOURCE_LINK')
                    if p['path'] == s.SELF: archived_failures[number] = pin
        require(set(archived_failures) == {1, 2, 3, 4, 5, 6}, 'ALL_HELPER_VERSIONS_PRESERVED')
        backend = q.text(s.BACKEND_SOURCE)
        require(set(re.findall(r'#\[test\]\s+fn ([a-z_]+)\(', backend)) == set(s.TEST_NAMES)
                and len(re.findall(r'#\[test\]', backend)) == 8
                and len(re.findall(r'#\[test\]', q.text(s.PROVIDER_SOURCE))) == 11, 'TEST_SOURCE_SCOPE')
        for name in (SELF, TEST): q.pin(name)
        document_inputs = [q.pin(name) for name in DOCS]
        sys.path.insert(0, str(s.c.ROOT/'tools/p09/tests'))
        suite = unittest.defaultTestLoader.loadTestsFromName('test_signed_durable_example_tests')
        result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
        require(result.wasSuccessful() and result.testsRun == 12, 'DRIVER_CONTRACT12')
        require({t.ident for t in threading.enumerate()} == threads, 'NO_NEW_THREAD')
        q.finish()
        receipt.update(state='PASS_CURRENT_DURABLE_ADAPTER_EXAMPLE19_ONLY_NOT_SQL_NATIVE_OR_GATE',
            example_tests_passed=19, original_source_tests_retained=11, new_backend_tests=8,
            driver_contract_tests_passed=12, whole_workspace_Rust_inputs=784,
            protected_executables_exact=50, current_source_closing_exact=True,
            original_root_and_provider_whole_bodies_restored_exact=True,
            original_runtime_helpers_unchanged=True, archived_helper_versions_bound_to_runs=sorted(archived_failures),
            failed_results_not_promoted=True, compiled_test_artifact=compiled,
            runtime_job_CPU_seconds=row['job_final']['job_cpu_seconds'],
            runtime_job_private_peak_MiB=row['job_final']['peak_job_private_mib'],
            host_available_RAM_min_percent=min(p['available_ram_percent'] for p in row['samples']),
            host_CPU_max_percent=max(p['system_cpu_percent'] for p in row['samples']),
            actual_SQL_or_native_executed=False, process_restart_or_key_custody_qualified=False,
            durable_signed_SQL_consumer_qualified=False, full249_current_qualified=False,
            PC_freeze_resolved=False, IO=q.summary(), document_inputs=document_inputs,
            bound_input_pins=list(q.reader.snapshots.values()), audit_new_child_started=False,
            audit_new_thread_started=False, raw_logs_included=False)
    finally:
        receipt['resource_stop'] = resources.reason
        require(finish_watcher(resources, receipt), 'WATCHER_CLEANUP')
    return receipt


if __name__ == '__main__':
    try: print(json.dumps(audit(), ensure_ascii=True, separators=(',', ':')))
    except (ValueError, OSError, KeyError, TypeError, StopIteration) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch('[A-Z_]+', str(error)) else 'SIGNED_DURABLE_AUDIT_NOT_ACCEPTED'
        print(json.dumps(dict(state='NOT_ACCEPTED', error_code=code))); raise SystemExit(2) from None
