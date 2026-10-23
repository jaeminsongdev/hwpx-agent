"""Serial bounded changed-code tests, partial-capture binding and actual READY denial.
Never releases a worker to start Native. Retains unchanged630 evidence, not replay.
"""
import json
from pathlib import Path
import subprocess
import sys
import time

import prepared_bookmark_native631 as runtime
import run_prepared_bookmark_native631 as entry

r = runtime.r
SELF = 'tools/p09/verify_prepared_bookmark631.py'
TEST = 'tools/p09/tests/test_prepared_bookmark631.py'
PS_TEST = 'implementation/p09/tools/test-prepared-bookmark631-ports.ps1'
TYPELIB = 'tools/p09/inspect_prepared_render631.ps1'
SPOOL = 'implementation/p09/evidence/private/p09-361-prepared-bookmark631-code001-forensic'
PWSH = Path(sys.executable).parent.parent/'native/powershell/pwsh.exe'


class ReadyDenial:
    def __init__(self, worker, shell_pin):
        self.worker, self.shell_pin = worker, shell_pin
        self.lease = None
        self.calls = 0

    def handle(self, raw):
        runtime.require(self.calls == 0 and self.lease is None, 'PREPARED631_DENIAL_SINGLE_READY')
        value = json.loads(raw, object_pairs_hook=runtime.base.batch.original.original.unique_pairs)
        runtime.require(type(value) is dict and set(value) == {'schema_version', 'worker_identity'}
                        and value['schema_version'] == runtime.base.batch.READY, 'PREPARED631_READY_NOT_CASE_IO')
        self.lease = runtime.base.session.WorkerKernelLease(self.worker, value['worker_identity'], self.shell_pin,
                                                          expected_role='private_fixed_eight_worker')
        self.calls += 1
        return json.dumps(dict(schema_version=runtime.base.batch.READY_REPLY, acknowledged=False,
            error_code='XREF_HOST_PREPARED631_CODE_ONLY_NO_NATIVE_RELEASE', native_execution_authorized=False,
            p09_complete=False), separators=(',', ':'))

    def current_native(self): return None

    def close(self):
        if self.lease is not None: self.lease.close()

    def summary(self):
        return dict(ready_frames=self.calls, case_frames=0, native_constructor_calls=0,
                    lease_closed=self.lease is not None and self.lease.closed)


def command(guard, args, env, row, label):
    step = dict(stage=label, cleanup=False)
    row['steps'].append(step)
    owned = capture = None
    start = time.monotonic()
    try:
        owned = r.shared.OwnedSQLJobProcess(args, windows=guard.windows, allowed_executables=[args[0]],
                                          cwd=r.c.ROOT, checkpoint=guard.check, env=env)
        capture = r.shared.BoundedProcessCapture(owned, output_limit=32768, parse_markers=False)
        while True:
            guard.check()
            runtime.require(time.monotonic()-start < 90, 'PREPARED631_CODE_COMMAND_TIMEOUT')
            try:
                out, err = capture.communicate(timeout=.5)
                owned.observe()
                break
            except subprocess.TimeoutExpired:
                capture.progress()
                owned.observe()
        value = json.loads(out)
        step.update(exit_code=owned.returncode, stderr_bytes=len(err.encode()), result=value)
        runtime.require(owned.returncode == 0 and not err, 'PREPARED631_CODE_COMMAND_FAILED')
        return value
    finally:
        if owned is not None:
            # Only the code-test Job owns these processes; NEVER a Native Job.
            owned.kill()
            owned.wait(timeout=2)
            if capture is not None: capture.close()
            owned.close()
            step.update(cleanup=owned.profile['cleanup_confirmed'], owned_job=owned.profile)


def main():
    runtime.require(sys.argv[1:] == ['--code-only-no-native'], 'PREPARED631_CODE_ONLY_MODE')
    runtime.prepared.require_absent(r.c.ROOT, entry.CODE)
    r.tools.select_own_single_cpu()
    r.shared.host.configure_host_policy(r.c)
    guard = r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q = None
    start = time.monotonic()
    row = dict(state='FAILED631_TAIL_SIX_CODE_QUALIFICATION', actual_native_started=False,
               all_new_tests_passed=False, old26_contracts_replayed=False, steps=[], P09_gate='OPEN', P10_started=False)
    try:
        guard.acquire()
        q = r.a.AcceptanceReader(r.c.ROOT, guard.check)
        row['retained_cases'] = runtime.evidence.retained(q, entry.codec.unpack)
        old = entry.codec.unpack(q.json(runtime.evidence.CODE))
        row['retained_630_denials_and26_contracts_source_identical'] = True
        row['prepared_files'] = runtime.prepared.validate_prepared(q, entry.codec.unpack)
        paths = set(old['execution_dependency_paths']) | runtime.SOURCES | runtime.prepared.loaded_dependencies(r.c.ROOT)
        paths -= {SELF}
        row['execution_dependency_paths'] = sorted(paths)
        for path in sorted(paths | {SELF, TEST, PS_TEST, TYPELIB, 'tools/p09/inspect_click_here_lifecycle_typelib.ps1'}):
            q.pin(path)
        row['shell_pin'] = old['shell_pin']
        native = runtime.base.session.startup
        runtime.require(not native.hwp_pids(guard.windows, guard.check), 'PREPARED631_NO_HWP_BEFORE')
        env = r.audit.environment()
        tests = command(guard, [sys.executable, '-B', str(r.c.ROOT/TEST)], env, row, 'changed_contracts14')
        runtime.require({k: tests[k] for k in ('run', 'errors', 'failures', 'skipped')} == dict(run=14, errors=0, failures=0, skipped=0),
                        'PREPARED631_ALL_CHANGED_CONTRACTS')
        tests = command(guard, [runtime.base.candidate.original.SHELL, '-NoLogo', '-NoProfile', '-NonInteractive', '-File',
                               str(r.c.ROOT/PS_TEST), '-ModelsOnly'], env, row, 'ports_and_BMP_models14')
        runtime.require({k: tests[k] for k in ('run', 'errors', 'failures', 'skipped')} == dict(run=14, errors=0, failures=0, skipped=0),
                        'PREPARED631_ALL_PORT_AND_BMP_MODELS')
        declaration = command(guard, [str(PWSH), '-NoLogo', '-NoProfile', '-File', str(r.c.ROOT/TYPELIB)], env, row, 'installed_typelib_readonly')
        runtime.require(declaration['state'] == 'OBSERVED631_INSTALLED_RENDER_DECLARATIONS_NOT_NATIVE'
                        and declaration['no_com_server_activation'] is True and declaration['hwp_process_set_unchanged'] is True
                        and declaration['typelib_sha256'] == 'abd7ca72b9873dbd90f2d28df872f2353f875662354d226fcc294557c44ca4f9',
                        'PREPARED631_EXACT_INSTALLED_DECLARATIONS')
        row['render_declarations'] = declaration
        worker = runtime.Worker(guard)
        handler = ReadyDenial(worker, row['shell_pin'])
        attempt = {}
        row['ready_denial'] = attempt
        result = runtime.io.run(guard, worker, q, worker.start_fixed_worker, handler,
            'hwpx-agent.private.crossref-fixed-worker-result/v1', env, lambda value: None, attempt)
        runtime.require(attempt['exit_code'] == 2 and attempt['cleanup'] is True and attempt['requests'] == 1
                        and handler.calls == 1 and result['completed_callback_cases'] == 0
                        and result['retained_live_or_uncertain_owners'] == 0, 'PREPARED631_ACTUAL_READY_DENIAL_NO_CASES')
        runtime.require(not native.hwp_pids(guard.windows, guard.check), 'PREPARED631_NO_HWP_AFTER')
        q.finish()
        guard.check(force=True)
        row.update(state=entry.STATE, all_new_tests_passed=True)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        row.update(**runtime.io.safe_failure(error))
    finally:
        guard.close()
        row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps'])
                   and ('ready_denial' not in row or row['ready_denial']['cleanup']),
                   source_pins=[] if q is None else list(q.snapshots.values()),
                   fresh_inputs=0 if q is None else len(q.snapshots), final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
                   elapsed_seconds=round(time.monotonic()-start, 3), resource_samples=guard.samples,
                   system_CPU_max=max((s['system_cpu_percent'] for s in guard.samples), default=None),
                   available_RAM_min_percent=min((s['available_ram_percent'] for s in guard.samples), default=None))
        normalized, retained = entry.retention.retain(r.c.ROOT, SPOOL, row)
        pin = entry.publish(entry.CODE, normalized)
        print(json.dumps({**{k: row.get(k) for k in ('state', 'error_code', 'all_new_tests_passed', 'fresh_inputs', 'final_fresh_hashes',
            'cleanup', 'elapsed_seconds', 'system_CPU_max', 'available_RAM_min_percent')},
            'failed_tests': [n for s in row['steps'] for n in s.get('result', {}).get('failed_tests', [])], 'receipt': pin}), flush=True)
    return 0 if row['state'] == entry.STATE and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
