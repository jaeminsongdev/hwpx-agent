"""Serial read-only code qualification; no Cargo, Hancom, COM or Native worker."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace as NS

import named_style_verification_runtime as r
import bookmark_native_preparation629 as preparation
import inspect_bookmark_native_batch629 as entry
import crossref_lossless_receipt610 as receipt
import metadata_forensic_retention615 as retention

SELF = 'tools/p09/verify_bookmark_native_preparation629.py'
TEST = 'tools/p09/tests/test_bookmark_native_preparation629.py'
OUTPUT = entry.CODE
SPOOL = 'implementation/p09/evidence/private/p09-361-bookmark-native-preparation629-code002-forensic'
FAILED = 'implementation/p09/evidence/p09-361-bookmark-native-preparation629-code001.v1.json'
ARCHIVE = 'implementation/p09/source-archive/p361-bookmark-native-preparation629/'


def contracts(guard, env, row):
    owned = capture = None
    start = time.monotonic()
    step = dict(stage='readonly_preparation_contracts18', cleanup=False)
    row['steps'].append(step)
    try:
        args = [str(preparation.inspection.fixed.PYTHON), '-B', str(r.c.ROOT / TEST)]
        owned = r.shared.OwnedSQLJobProcess(args, windows=guard.windows, allowed_executables=[str(preparation.inspection.fixed.PYTHON)],
            cwd=r.c.ROOT, checkpoint=guard.check, env=env)
        capture = r.shared.BoundedProcessCapture(owned, output_limit=32768, parse_markers=False)
        while True:
            guard.check()
            preparation.require(time.monotonic() - start < 60, 'READONLY_CONTRACT_DEADLINE')
            try:
                out, err = capture.communicate(timeout=.5)
                owned.observe()
                break
            except subprocess.TimeoutExpired:
                capture.progress()
                owned.observe()
        step.update(exit_code=owned.returncode, stdout_bytes=len(out.encode()), stderr_bytes=len(err.encode()),
                    stdout_sha256=hashlib.sha256(out.encode()).hexdigest(), stderr_sha256=hashlib.sha256(err.encode()).hexdigest())
        result = json.loads(out)
        row['contracts'] = {k: result[k] for k in ('run', 'errors', 'failures', 'skipped')}
        step['failed_tests'] = result['failed_tests']
        preparation.require(owned.returncode == 0 and not err and not result['failed_tests']
                            and row['contracts'] == dict(run=18, errors=0, failures=0, skipped=0), 'CONTRACTS18_NO_ERRORS_FAILURES_SKIPS')
    finally:
        if owned is not None:
            owned.kill()
            owned.wait(timeout=2)
            if capture is not None:
                capture.close()
            owned.close()
            step.update(cleanup=owned.profile['cleanup_confirmed'], owned_job=owned.profile)
        step['elapsed_seconds'] = round(time.monotonic() - start, 3)


def main():
    preparation.require(sys.argv[1:] == ['--bounded-readonly-preparation'], 'CLOSED_READONLY_MODE')
    c, a, shared = r.c, r.a, r.shared
    preparation.require_absent(c.ROOT, OUTPUT)
    selection = r.tools.select_own_single_cpu()
    shared.host.configure_host_policy(c)
    guard = shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard), role='whole_metadata_preflight'))()
    q = native = python = None
    started = time.monotonic()
    row = dict(state='FAILED629_READONLY_CODE_PREPARATION', steps=[], own_cpu_selection=selection,
               actual_native_started=False, fixed_eight_executed=False, permission_dialog_requested=False,
               native_execution_authorized=False, native_entry_ready=False, accepted_count_delta=0, P09_gate='OPEN', P10_started=False,
               previous627_or628_product_tests_replayed=False, PC_freeze_resolved=False)
    try:
        guard.acquire()
        q = a.AcceptanceReader(c.ROOT, guard.check)
        row['prepared_files'] = preparation.validate_prepared(q, receipt.unpack)
        prior = receipt.unpack(q.json(preparation.PRIOR))
        previous = {p['path']: p for p in prior['source_pins']}
        failure = receipt.unpack(q.json(FAILED))
        preparation.require(q.snapshots[FAILED]['sha256'] == '435cbb3df70a385f5211827dc579747dc30c6c8da147d63976641ed2a22494c1'
                            and failure['state'] == 'FAILED629_READONLY_CODE_PREPARATION'
                            and failure['error_code'] == 'OWNED_SQL_EXECUTABLE_NOT_ALLOWLISTED'
                            and failure.get('contracts') is None, 'ORIGINAL_PRELAUNCH_FAILURE_PRESERVED')
        paths = preparation.loaded_dependencies(c.ROOT) | {SELF, TEST, FAILED, ARCHIVE+'verifier-code001.py', ARCHIVE+'entry-code001.py'}
        row['entry_dependency_paths'] = sorted(paths)
        for path in sorted(paths):
            pin = q.pin(path)
            if path in previous:
                preparation.require(pin == previous[path], 'UNCHANGED_PREVIOUS_RUNTIME_BODIES')
        failed_pins = {p['path']: p for p in failure['source_pins']}
        preparation.require(q.snapshots[ARCHIVE+'verifier-code001.py']['sha256'] == failed_pins[SELF]['sha256']
                            and q.snapshots[ARCHIVE+'entry-code001.py']['sha256'] == failed_pins[entry.SELF]['sha256'],
                            'EXACT_FAILED_VERIFIER_AND_ENTRY_ARCHIVE')
        row['original_prelaunch_failure_preserved'] = FAILED
        row['python_qualification'] = preparation.runtime.require_qualification(q)
        executable = Path(preparation.inspection.native.EXECUTABLE)
        native = a.AcceptanceReader(executable.parent, guard.check)
        python = a.AcceptanceReader(preparation.inspection.fixed.PYTHON.parent, guard.check)
        preparation.require(not preparation.inspection.prerequisites.startup.hwp_pids(guard.windows, guard.check), 'NO_PREEXISTING_HWP')
        print(json.dumps(dict(state='P629_READONLY_CODE_PREFLIGHT', new_contracts=18, prepared_files=8,
                              Cargo_or_native_started=False)), flush=True)
        contracts(guard, r.audit.environment(), row)
        row['actual_kernel_readonly_observation'] = preparation.inspect_current(guard.windows, guard.check,
            lambda: native.fresh_pin(executable.name), lambda: preparation.runtime.verify_current_reader(python))
        preparation.require(not preparation.inspection.prerequisites.startup.hwp_pids(guard.windows, guard.check), 'NO_HWP_AFTER_READONLY')
        native.finish()
        python.finish()
        q.finish()
        guard.check(force=True)
        row['state'] = entry.CODE_STATE
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        row.update(error_type=type(error).__name__, error_code=preparation.safe_code(error))
    finally:
        guard.close()
        row.update(cleanup=guard.cleanup and all(step['cleanup'] for step in row['steps']),
                   elapsed_seconds=round(time.monotonic() - started, 3), source_pins=[] if q is None else list(q.snapshots.values()),
                   fresh_inputs=0 if q is None else len(q.snapshots), final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
                   native_image_final_fresh_hashes=0 if native is None else native.final_fresh_hashes,
                   runtime_final_fresh_hashes=0 if python is None else python.final_fresh_hashes,
                   resource_samples=guard.samples,
                   system_CPU_max=max((v['system_cpu_percent'] for v in guard.samples), default=None),
                   available_RAM_min_percent=min((v['available_ram_percent'] for v in guard.samples), default=None))
        normalized, retained = retention.retain(c.ROOT, SPOOL, row)
        pin = shared.publisher.publish(c.ROOT, OUTPUT, receipt.pack(normalized, lambda: None), NS(require=c.require, exact=a.exact))
        print(json.dumps({**{k: row.get(k) for k in ('state', 'error_code', 'contracts', 'cleanup', 'elapsed_seconds',
              'fresh_inputs', 'final_fresh_hashes', 'system_CPU_max', 'available_RAM_min_percent')},
              'failed_tests': [name for step in row['steps'] for name in step.get('failed_tests', [])],
              'receipt': pin, 'retained_metadata': retained}), flush=True)
    return 0 if row['state'] == entry.CODE_STATE and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
