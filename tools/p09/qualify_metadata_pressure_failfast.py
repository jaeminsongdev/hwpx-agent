"""Bounded actual failure review and synthetic opt-in contracts, not runtime.

One original sole Guard owns all fresh reads. A single explicitly reported
GetPerformanceInfo comparison is diagnostic only; no sampler thread or worker.
Frozen flat runtime/run001 and authority119 remain unchanged. The new binding
has NOT been connected/qualified in a whole Native/product runtime.
"""
import io
import json
from pathlib import Path
import re
import sys
import time
import unittest
from unittest.mock import patch

import accept_case112_current_epoch as a
import system_commit_diagnostic as diagnostic

SELF = 'tools/p09/qualify_metadata_pressure_failfast.py'
FILES = (SELF, 'tools/p09/metadata_pressure_failfast.py',
         'tools/p09/system_commit_diagnostic.py',
         'tools/p09/tests/test_metadata_pressure_failfast.py')
OUTPUT = 'implementation/p09/evidence/p09-361-case120-stop-and-metadata-failfast-qualification-r266.v1.json'
FAILURE = dict(path='implementation/p09/evidence/p09-361-case120-current-runtime-run001.v1.json',
               bytes=46951, sha256='ce95eeb3db66595d59467e72c3ac43aba162e7b6931cf03886961918df9629b4')
CORE = (
    dict(path='tools/p09/flat_current_queue_runtime.py', bytes=11527,
         sha256='f67172dc0eedb965b67bde07d494ec8f1f1edd95573b58660bf2826d21baac1d'),
    dict(path='tools/p09/flat_current_queue_acceptance.py', bytes=8269,
         sha256='4ea09d59208e447767409b04588417dc7d2a19c63b3ba10f81511fd7d92d17ce'),
    dict(path='tools/p09/tests/test_flat_current_queue.py', bytes=14870,
         sha256='69e2e87b6ec091d8d989b278788f97bda34ef22c1f4997eaac2aa9e3d9ba33f9'),
)


def main():
    a.require(Path.cwd().resolve() == a.c.ROOT, 'QUALIFICATION_CWD')
    destination = a.c.ROOT / OUTPUT
    a.require(not destination.exists(), 'FRESH_QUALIFICATION_RECEIPT')
    guard = None
    reader = None
    proposed = None
    started = time.monotonic()
    out = dict(schema_version='hwpx-agent.p09-metadata-pressure-failfast-qualification/v1',
               state='FAILED_NOT_ACCEPTED', failed_runtime_pin=FAILURE,
               accepted_count_before=113, accepted_count_after=113,
               accepted_count_delta=0, remaining=136, next_runtime_index=120,
               product_worker_or_Native_frame_executed=False,
               retry_run002_executed=False, runtime_connection_qualified=False,
               global_commit_guard_replacement_qualified=False,
               second_sampler_or_thread=False, full249_current_qualified=False,
               signed16_current_qualified=False, P09_gate='OPEN', A12_gate='OPEN',
               A13_gate='OPEN', PC_freeze_resolved=False)
    try:
        guard = a.Guard()
        guard.acquire()
        reader = a.AcceptanceReader(a.c.ROOT, guard.check)
        failed = a.read_exact(reader, FAILURE)
        a.fields(failed, dict(state='DEFERRED_NOT_STARTED', selected_test_index=120,
                             stop_reason='STOP_SYSTEM_COMMIT_PRESSURE', worker_created=False,
                             product_body_observed=False, source_frame=None,
                             Native_source_frame_qualified=False, cleanup_confirmed=True,
                             owned_tree_empty=True, accepted_count_delta=0,
                             full249_current_qualified=False, signed16_current_qualified=False,
                             P09_gate='OPEN', A12_gate='OPEN', A13_gate='OPEN'), 'ACTUAL_FAILED120')
        a.exact(failed['passed_test_names'], [], 'NO_PRODUCT_CASE_PASS')
        boot = failed['bootstrap_metadata']
        a.exact(boot['read_passes'], 52, 'ACTUAL_BOOTSTRAP_READS')
        a.exact(boot['bytes_read'], 18773746, 'ACTUAL_BOOTSTRAP_BYTES')
        early = boot['early_pressure']
        a.fields(early, dict(warning_system_CPU_percent=75, warning_entries=1,
                            completed_pause_windows=7, original_checkpoint_restored=True),
                 'ALREADY_PAUSED_NOT_CONTINUED_IO')
        samples = failed['samples']
        a.require(len(samples) == 30, 'ACTUAL_SAMPLE_COUNT')
        out['failed_runtime_review'] = dict(
            preserved_failed_not_accepted=True, original_warning_CPU_percent=75,
            original_cooling_pause_windows=7, original_read_passes=52,
            original_read_bytes=18773746, Native_handle_counts_unmeasured_not_zero=True,
            host_CPU_max_percent=max(x['system_cpu_percent'] for x in samples),
            available_RAM_min_percent=min(x['available_ram_percent'] for x in samples),
            original_process_or_system_commit_max_percent=max(x['commit_used_percent'] for x in samples),
            parent_private_max_MiB=max(x['parent_private_mib'] for x in samples),
            sampled_parent_CPU_last_two=[x['parent_cpu_machine_percent'] for x in samples[-2:]],
            last_six_original_samples=[{k: x[k] for k in (
                'time_utc', 'system_cpu_percent', 'available_ram_percent',
                'commit_used_percent', 'parent_cpu_machine_percent', 'parent_private_mib')}
                for x in samples[-6:]],
            indirect_verifier_triggered_external_load_not_excluded=True,
            Defender_or_other_causal_process_identified=False)
        out['new_code_pins'] = [reader.pin(name) for name in FILES]
        for pin in CORE:
            a.exact(reader.pin(pin['path']), pin, 'FROZEN_CORE_UNCHANGED')
        out['frozen_core_pins'] = list(CORE)
        sys.path.insert(0, str(a.c.ROOT / 'tools/p09/tests'))
        import test_metadata_pressure_failfast as tests
        with patch('subprocess.Popen', side_effect=AssertionError('NO_CHILD')), \
             patch('subprocess.run', side_effect=AssertionError('NO_CHILD')), \
             patch('threading.Thread.start', side_effect=AssertionError('NO_SECOND_SAMPLER')):
            result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
                unittest.defaultTestLoader.loadTestsFromModule(tests))
        a.require(result.wasSuccessful() and result.testsRun == 12 and not result.skipped,
                  'SYNTHETIC_CONTRACT12')
        out['synthetic_contracts_passed'] = result.testsRun
        time.sleep(.5)
        guard.check(force=True)
        out['current_original_resource_sample'] = guard.samples[-1]
        out['single_global_commit_diagnostic'] = diagnostic.once(guard.windows.k)
        # These sequential calls are not identical sampling instants, and do
        # not explain the historic failed120 interval or replace its decisions.
        reader.finish()
        time.sleep(.5)
        guard.check(force=True)
        proposed = 'PASS_FAILED120_REVIEW_AND_SYNTHETIC12_NOT_RUNTIME_CONNECTION_OR_GATE'
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        code = str(exc) if isinstance(exc, ValueError) else 'REDACTED_QUALIFICATION_FAILURE'
        out['error_code'] = code if re.fullmatch('[A-Z0-9_]{1,256}', code) else 'REDACTED_QUALIFICATION_FAILURE'
    finally:
        if guard is not None:
            try:
                guard.close()
            except (ValueError, OSError):
                proposed = None
                out['error_code'] = 'ORIGINAL_GUARD_CLEANUP_FAILED'
        out['cleanup_confirmed'] = bool(guard is not None and guard.cleanup)
        if proposed and out['cleanup_confirmed']:
            out['state'] = proposed
        samples = guard.samples if guard is not None else []
        out.update(original_resource_samples=len(samples),
                   original_resource_history=samples,
                   host_CPU_max_percent=max((x['system_cpu_percent'] for x in samples), default=None),
                   available_RAM_min_percent=min((x['available_ram_percent'] for x in samples), default=None),
                   elapsed_seconds=time.monotonic() - started,
                   fresh_read_passes=reader.read_passes if reader else 0,
                   fresh_bytes_read=reader.bytes_read if reader else 0,
                   final_fresh_hashes=reader.final_fresh_hashes if reader else 0)
        with destination.open('x', encoding='utf-8') as stream:
            json.dump(out, stream, indent=2)
        print(json.dumps({k: out.get(k) for k in (
            'state', 'error_code', 'synthetic_contracts_passed', 'original_resource_samples',
            'host_CPU_max_percent', 'available_RAM_min_percent', 'cleanup_confirmed',
            'single_global_commit_diagnostic', 'elapsed_seconds')}))
    return 0 if proposed and out['cleanup_confirmed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
