"""Bounded code tests and actual ready DENIAL; no Native/session execution."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace as NS
from unittest.mock import patch

import prepared_bookmark_native630 as runtime
import run_prepared_bookmark_native630 as entry
import crossref_lossless_receipt610 as codec
import crossref_inline_receipt567 as historical
import compact_receipt_json as compact
import metadata_forensic_retention615 as retention
import crossref_session_ready_denial_io as current_session

r = runtime.r
SELF = 'tools/p09/verify_prepared_bookmark_native630.py'
TEST = 'tools/p09/tests/test_prepared_bookmark_native630.py'
OUTPUT = entry.CODE
SPOOL = 'implementation/p09/evidence/private/p09-361-prepared-bookmark630-code004-forensic'
PRIOR003 = 'implementation/p09/evidence/p09-361-prepared-bookmark630-code003.v1.json'
PSTEST = 'implementation/p09/tools/test-prepared-bookmark630-ports.ps1'
FAILED = 'implementation/p09/evidence/p09-361-prepared-bookmark630-code001.v1.json'
FAILED002 = 'implementation/p09/evidence/p09-361-prepared-bookmark630-code002.v1.json'
ARCHIVE = 'implementation/p09/source-archive/p361-prepared-bookmark630/'
OLD = 'implementation/p09/evidence/p09-361-capture010-entry-code606-revised.v1.json'
SESSION = 'implementation/p09/evidence/p09-361-crossref-session-qualification-code407.v1.json'
EXTERNAL = 'implementation/p09/evidence/p09-361-bookmark-native-preparation629-external001.v1.json'


class ReadyDenial:
    def __init__(self, worker, shell_pin):
        self.worker, self.shell_pin = worker, shell_pin
        self.lease = None
        self.calls = 0

    def handle(self, raw):
        runtime.require(self.calls == 0 and self.lease is None, 'PREPARED630_DENIAL_ONE_READY_ONLY')
        value = json.loads(raw, object_pairs_hook=runtime.base.batch.original.original.unique_pairs)
        runtime.require(type(value) is dict and set(value) == {'schema_version', 'worker_identity'}
                        and value['schema_version'] == runtime.base.batch.READY, 'PREPARED630_EXACT_READY_NOT_CASE_IO')
        self.lease = runtime.base.session.WorkerKernelLease(self.worker, value['worker_identity'], self.shell_pin,
                                                         expected_role='private_fixed_eight_worker')
        self.calls += 1
        return json.dumps(dict(schema_version=runtime.base.batch.READY_REPLY, acknowledged=False,
            error_code='XREF_HOST_PREPARED630_CODE_ONLY_NO_NATIVE_RELEASE', native_execution_authorized=False, p09_complete=False), separators=(',', ':'))

    def current_native(self):
        return None

    def close(self):
        if self.lease is not None:
            self.lease.close()

    def summary(self):
        return dict(ready_frames=self.calls, case_frames=0, native_constructor_calls=0,
                    lease_closed=self.lease is not None and self.lease.closed)


def contracts(guard, env, row):
    owned = capture = None
    step = dict(stage='prepared_capture_new_contracts14', cleanup=False)
    row['steps'].append(step)
    start = time.monotonic()
    try:
        args = [str(runtime.prepared.inspection.fixed.PYTHON), '-B', str(r.c.ROOT/TEST)]
        owned = r.shared.OwnedSQLJobProcess(args, windows=guard.windows, allowed_executables=[args[0]],
                                          cwd=r.c.ROOT, checkpoint=guard.check, env=env)
        capture = r.shared.BoundedProcessCapture(owned, output_limit=32768, parse_markers=False)
        while True:
            guard.check()
            runtime.require(time.monotonic()-start < 90, 'PREPARED630_CONTRACT_DEADLINE')
            try:
                out, err = capture.communicate(timeout=.5)
                owned.observe()
                break
            except subprocess.TimeoutExpired:
                capture.progress()
                owned.observe()
        result = json.loads(out)
        row['contracts'] = {k: result[k] for k in ('run', 'errors', 'failures', 'skipped')}
        step.update(exit_code=owned.returncode, stderr_bytes=len(err.encode()), stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),
                    failed_tests=result['failed_tests'])
        runtime.require(owned.returncode == 0 and not err and row['contracts'] == dict(run=14, errors=0, failures=0, skipped=0),
                        'PREPARED630_ALL_CONTRACTS14_NO_SKIPS')
    finally:
        if owned is not None:
            owned.kill()
            owned.wait(timeout=2)
            if capture is not None:
                capture.close()
            owned.close()
            step.update(cleanup=owned.profile['cleanup_confirmed'], owned_job=owned.profile)
        step['elapsed_seconds'] = round(time.monotonic()-start, 3)


def port_models(guard, env, row):
    owned = capture = None
    step = dict(stage='prepared_port_models7_not_native', cleanup=False)
    row['steps'].append(step)
    start = time.monotonic()
    try:
        shell = runtime.base.candidate.original.SHELL
        args = [shell, '-NoLogo', '-NoProfile', '-NonInteractive', '-STA', '-File', str(r.c.ROOT/PSTEST), '-ModelsOnly']
        owned = r.shared.OwnedSQLJobProcess(args, windows=guard.windows, allowed_executables=[shell], cwd=r.c.ROOT, checkpoint=guard.check, env=env)
        capture = r.shared.BoundedProcessCapture(owned, output_limit=32768, parse_markers=False)
        while True:
            guard.check()
            runtime.require(time.monotonic()-start < 60, 'PREPARED630_MODEL_DEADLINE')
            try:
                out, err = capture.communicate(timeout=.5)
                owned.observe()
                break
            except subprocess.TimeoutExpired:
                capture.progress()
                owned.observe()
        result = json.loads(out)
        row['port_models'] = {k: result[k] for k in ('run', 'errors', 'failures', 'skipped')}
        step.update(exit_code=owned.returncode, stdout_sha256=hashlib.sha256(out.encode()).hexdigest(), stderr_bytes=len(err.encode()))
        runtime.require(owned.returncode == 0 and not err and result['actual_native_started'] is False
                        and row['port_models'] == dict(run=7, errors=0, failures=0, skipped=0), 'PREPARED630_ALL_MODELS7')
    finally:
        if owned is not None:
            owned.kill()
            owned.wait(timeout=2)
            if capture is not None:
                capture.close()
            owned.close()
            step.update(cleanup=owned.profile['cleanup_confirmed'], owned_job=owned.profile)
        step['elapsed_seconds'] = round(time.monotonic()-start, 3)


def main():
    runtime.require(sys.argv[1:] == ['--bounded-code-and-ready-denial'], 'PREPARED630_CLOSED_CODE_ONLY_MODE')
    runtime.prepared.require_absent(r.c.ROOT, OUTPUT)
    runtime.absent()
    selection = r.tools.select_own_single_cpu()
    r.shared.host.configure_host_policy(r.c)
    guard = r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q = shell = python = None
    started = time.monotonic()
    row = dict(state='FAILED630_PREPARED_CAPTURE_CODE', steps=[], own_cpu_selection=selection,
               actual_native_started=False, permission_dialog_requested=False, fixed_eight_executed=False,
               prior627_628_629_tests_replayed=False, consumed010_or_Native011_executed=False,
               semantic_acceptance_qualified=False, P09_gate='OPEN', P10_started=False)
    try:
        guard.acquire()
        q = r.a.AcceptanceReader(r.c.ROOT, guard.check)
        old = historical.unpack(q.json(OLD))
        runtime.require(q.snapshots[OLD]['sha256'] == 'e609b643938fdc778151c73e822dfee0abed10009b0104ad28ffed43a963abda', 'PREPARED630_EXACT_HISTORIC_CODE_PROOF')
        old_pins = {v['path']: v for v in old['source_pins']}
        session = compact.unpack(q.json(SESSION))
        runtime.require(q.snapshots[SESSION]['sha256'] == 'fc474e94efd9126f4c237e52e78adf092f8a41a293d1754b4e593ba7aa533729', 'PREPARED630_EXACT_SESSION_CODE_PROOF')
        session_pins = {v['path']: v for v in session['source_pins']}
        external = codec.unpack(q.json(EXTERNAL))
        runtime.require(q.snapshots[EXTERNAL]['sha256'] == '6bcc77cf3a61dd5bf82e5673a2400f450de9631c157926df5dd73dd9602d2cb6'
                        and external['cleanup'] is True and external['native_entry_ready'] is False,
                        'PREPARED630_EXTERNAL_OBSERVATION_PRESERVED_NOT_A_PERMIT')
        row['prepared_files'] = runtime.prepared.validate_prepared(q, codec.unpack)
        failed = codec.unpack(q.json(FAILED))
        runtime.require(q.snapshots[FAILED]['sha256'] == 'f1475b72294d82bcf9a5388dfa8b34069319dffd4512a62fc400d852cf325afb'
                        and failed['state'] == 'FAILED630_PREPARED_CAPTURE_CODE' and failed['steps'] == [],
                        'PREPARED630_ORIGINAL_PRETEST_FAILURE_PRESERVED')
        row['original_pretest_failure_preserved'] = FAILED
        failed002 = codec.unpack(q.json(FAILED002))
        runtime.require(q.snapshots[FAILED002]['sha256'] == '9b31842bd58bc3a80854f6267e9ecf1b1641ad4f2757857d0b9ba6a2206dae2a'
                        and failed002['steps'] == [], 'PREPARED630_ORIGINAL_SESSION_SOURCE_DRIFT_PRESERVED')
        row['original_session_source_drift_preserved'] = FAILED002
        row['python_host'] = runtime.prepared.runtime.require_qualification(q)
        prior = codec.unpack(q.json(PRIOR003))
        runtime.require(q.snapshots[PRIOR003]['sha256'] == '1090a0f155c21aa2d6725cb2afe012fcf51397af8f61cc14ca53cbcef3c91a5a'
                        and prior['state'] == entry.STATE and prior['cleanup'] is True
                        and prior['contracts'] == dict(run=14, errors=0, failures=0, skipped=0), 'PREPARED630_PASSED14_RETAINED')
        prior_pins = {v['path']: v for v in prior['source_pins']}
        for path in (TEST, runtime.SELF):
            runtime.require(q.pin(path) == prior_pins[path], 'PREPARED630_RETAINED14_IDENTICAL_TEST_AND_CORE')
        row.update(contracts=prior['contracts'], retained14_receipt=PRIOR003, prior14_tests_replayed=False)
        execution_paths = runtime.prepared.loaded_dependencies(r.c.ROOT) | runtime.SOURCES | {
            runtime.prepared.PREPARED, runtime.prepared.SOURCE} | {v['output']['path'] for v in row['prepared_files']['cases']}
        execution_paths -= {SELF, 'tools/p09/crossref_session_ready_denial_io.py'}
        history_paths = {SELF, TEST, PSTEST, OLD, SESSION, EXTERNAL, runtime.prepared.PRIOR, FAILED, FAILED002, PRIOR003,
            ARCHIVE+'verifier-code001.py', ARCHIVE+'entry-code001.py',
            ARCHIVE+'verifier-code002.py', ARCHIVE+'entry-code002.py',
            ARCHIVE+'verifier-code003.py', ARCHIVE+'entry-code003.py', ARCHIVE+'worker-code003.ps1'}
        paths = execution_paths | history_paths | {'tools/p09/crossref_session_ready_denial_io.py'}
        row['execution_dependency_paths'] = sorted(execution_paths)
        row['history_proofs_checked_only_at_bundle_boundaries_not_per_case'] = True
        new_sources = {runtime.TARGET, runtime.PORTS, runtime.CHANNEL, SELF, TEST, runtime.SELF, entry.SELF}
        for path in sorted(paths):
            pin = q.pin(path)
            if path in runtime.SOURCES-new_sources:
                if path == runtime.base.candidate.TARGET:
                    runtime.require(pin == dict(path=path, bytes=5730, sha256='d86b565f01fec16e543ce1f2c65d6518e007732e0f53f0d00541d115e3192aab'),
                                    'PREPARED630_EXPLICIT_CURRENT_SESSION_WORKER_SOURCE')
                    continue  # Requalified by actual root-denial below, NOT treated as old407.
                expected = old_pins.get(path) or session_pins.get(path)
                runtime.require(expected is not None and pin == expected, 'PREPARED630_ORIGINAL_SESSION_AND_IO_BODIES_UNCHANGED')
        shell = r.a.AcceptanceReader(Path(runtime.base.candidate.original.SHELL).parent, guard.check)
        row['shell_pin'] = shell.pin(Path(runtime.base.candidate.original.SHELL).name)
        python = r.a.AcceptanceReader(runtime.prepared.inspection.fixed.PYTHON.parent, guard.check)
        runtime.prepared.runtime.verify_current_reader(python)
        runtime.require(not runtime.base.session.startup.hwp_pids(guard.windows, guard.check), 'PREPARED630_NO_HWP_BEFORE')
        scratch = r.c.ROOT/'target/p09-prepared-bookmark630-code004-scratch'
        runtime.prepared.require_absent(r.c.ROOT, scratch.relative_to(r.c.ROOT).as_posix())
        scratch.mkdir()
        env = r.audit.environment()
        env.update(TEMP=str(scratch), TMP=str(scratch), PYTHONDONTWRITEBYTECODE='1')
        print(json.dumps(dict(state='P630_CODE_PREFLIGHT', retained_contracts=14, new_port_models=7, actual_native_or_Cargo=False)), flush=True)
        port_models(guard, env, row)
        full = runtime.Worker(guard)
        denial = ReadyDenial(full, lambda: shell.fresh_pin(Path(runtime.base.candidate.original.SHELL).name))
        attempt = {}
        row['ready_denial'] = attempt
        with patch.object(runtime.base.session.startup, 'PreassignedNativeStartup', side_effect=ValueError('PREPARED630_NATIVE_FACTORY_FORBIDDEN')) as trap:
            result = runtime.io.run(guard, full, q, full.start_fixed_worker, denial,
                'hwpx-agent.private.crossref-fixed-worker-result/v1', env,
                lambda value: print(json.dumps(dict(state=value['state'], native_factory_forbidden=True)), flush=True), attempt)
            runtime.require(trap.call_count == 0 and denial.calls == 1 and attempt['exit_code'] == 2
                            and attempt['cleanup'] is True and result['completed_callback_cases'] == 0
                            and result['error_code'] == 'P09_XREF_BIND_PREPARED_CURRENT_LIVE_RELEASE_REQUIRED'
                            and result['retained_live_or_uncertain_owners'] == 0, 'PREPARED630_ACTUAL_READY_DENIED_BEFORE_ANY_CASE')
        # Current session worker differs from407. Exercise its actual current
        # x86 transport/cleanup against genuine parent denial with a constructor
        # trap. No Native, no saved qualification and no historical35 replay.
        current_session.run(guard, q, lambda: shell.fresh_pin(Path(runtime.base.candidate.original.SHELL).name), env, row)
        session_step = row['steps'][-1]
        runtime.require(session_step['native_constructor_trap_calls'] == 0 and session_step['cleanup'] is True
                        and session_step['session_summary']['native_backend_profile'] is None,
                        'PREPARED630_CURRENT_SESSION_WORKER_REQUALIFIED_NO_NATIVE')
        row['current_session_worker_source_requalified_not_called_unchanged'] = True
        runtime.absent()
        runtime.require(not runtime.base.session.startup.hwp_pids(guard.windows, guard.check), 'PREPARED630_NO_HWP_AFTER')
        q.finish()
        shell.finish()
        python.finish()
        guard.check(force=True)
        row['state'] = entry.STATE
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        row.update(error_type=type(error).__name__, error_code=runtime.prepared.safe_code(error))
    finally:
        guard.close()
        row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps']) and row.get('ready_denial', {'cleanup': True})['cleanup'],
            elapsed_seconds=round(time.monotonic()-started, 3), source_pins=[] if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots), final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            resource_samples=guard.samples, system_CPU_max=max((s['system_cpu_percent'] for s in guard.samples), default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in guard.samples), default=None))
        normalized, retained = retention.retain(r.c.ROOT, SPOOL, row)
        pin = entry.publish(OUTPUT, normalized)
        print(json.dumps({**{k: row.get(k) for k in ('state', 'error_code', 'contracts', 'cleanup', 'fresh_inputs', 'final_fresh_hashes',
            'elapsed_seconds', 'system_CPU_max', 'available_RAM_min_percent')}, 'failed_tests': [n for s in row['steps'] for n in s.get('failed_tests', [])],
            'receipt': pin, 'retained_metadata': retained}), flush=True)
    return 0 if row['state'] == entry.STATE and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
