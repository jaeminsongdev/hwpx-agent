"""Current AEAD profile, original unfiltered249, unchanged captured1200s runner.

Reuse the already-tested bounded capture/owned Job implementation. A current
compiled inventory is mandatory; neither stopped diagnostics nor stage markers
qualify the suite. No Rust/product/assertion/global/resource-policy changes.
"""
import argparse
import base64
import hashlib
import io
import json
import re
import subprocess
import sys
import unittest
from contextlib import contextmanager
from unittest.mock import patch

import run_aead_dependency_signed_tests as candidate
import run_compression_full_stored as captured
from live_sql_evidence_reader import LiveSQLReader
from sql_owned_execution import scoped_path
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher

c = candidate.c
SELF = 'tools/p09/run_aead_full_stored.py'
TEST = 'tools/p09/tests/test_aead_full_stored.py'
TASK = 'aead-full-stored-tests'
VARIANT = 'r23-aead-profile-exact-full249-captured-terse-no-filter'
MAXIMUM_SECONDS = 1200
LIGHT_TESTS = 22


def require_scope(seconds):
    c.require(type(seconds) is int and seconds == MAXIMUM_SECONDS,
        'AEAD_FULL_ORIGINAL1200_SCOPE')
    candidate.config_contract(candidate.CONFIG)
    c.require(captured.MAXIMUM_SECONDS == MAXIMUM_SECONDS
        and captured.bounded.LIMIT == 32768, 'AEAD_FULL_EXISTING_LIMIT_DRIFT')


@contextmanager
def adapter():
    require_scope(MAXIMUM_SECONDS)
    with patch.object(captured, 'candidate', candidate), patch.object(captured, 'SELF', SELF), \
            patch.object(captured, 'TASK', TASK), patch.object(captured, 'VARIANT', VARIANT):
        yield


def capture_provenance(q, expected):
    # Read the original helper names outside the adapter; preserve both failures.
    for name in (captured.SELF, captured.TEST):
        c.require(expected.get(name) == q.pin(name), 'AEAD_FULL_CAPTURE_SOURCE_DRIFT')
    c.require(q.pin(captured.FAILED['path']) == captured.FAILED,
        'AEAD_FULL_ORIGINAL_FAILED_PIN_DRIFT')
    failed = q.json(captured.FAILED['path']); archive = q.json(captured.ARCHIVE)
    c.require(failed['state'] == 'STOPPED_NOT_ACCEPTED'
        and failed['stop_reason'] == 'OWNED_RUNNER_FAILURE'
        and failed['full249_current_qualified'] is False
        and failed['signed16_current_qualified'] is False
        and failed['cleanup_confirmed'] and failed['owned_tree_empty']
        and failed['job_final']['active_processes'] == 0
        and archive['failed_execution_pin'] == captured.FAILED,
        'AEAD_FULL_FAILED_PARENT_NOT_PASS')
    frozen = {p['path']:p for p in failed['source_freeze']}; seen = set()
    for item in archive['files']:
        name = item['path']; raw = base64.b64decode(item['base64'], validate=True)
        pin = {k:item[k] for k in ('path','bytes','sha256')}
        c.require(name in (captured.SELF,captured.TEST) and name not in seen
            and frozen.get(name) == pin and len(raw) == pin['bytes']
            and hashlib.sha256(raw).hexdigest() == pin['sha256'],
            'AEAD_FULL_CAPTURE_WHOLE_PREIMAGE_DRIFT')
        seen.add(name)
    c.require(seen == {captured.SELF,captured.TEST}, 'AEAD_FULL_CAPTURE_PREIMAGE_SCOPE')
    for name in (captured.ARCHIVE,captured.FAILED['path']): expected[name] = q.pin(name)


def load_binding(inventory_run):
    require_scope(MAXIMUM_SECONDS)
    expected,names,modules = candidate.load_binding(candidate.PROFILE,inventory_run)
    resources = SQLRuntimeResources(); row = {}
    try:
        resources.admit(); q = LiveSQLReader(resources)
        capture_provenance(q,expected)
        for name in (SELF,TEST): expected[name] = q.pin(name)
        q.finish()
        return expected,names,modules
    finally:
        c.require(finish_watcher(resources,row), 'STOP_BINDING_WATCHER_CLEANUP_FAILED')


def worker():
    with adapter(): return captured.worker()


def run_owned(destination,expected,names,modules):
    require_scope(MAXIMUM_SECONDS); dump = json.dump
    def write(row,stream,**kwargs):
        c.require(row.get('test_package_profile_config') == list(candidate.CONFIG),
            'AEAD_FULL_CONFIG_RECEIPT_DRIFT')
        row.update(aead_dependencies_parent_pin=candidate.PARENT,
            optimized_aead_dependencies=list(candidate.AEAD_PACKAGES),
            aead_dependencies_opt_level=1,
            precompiled_runtime_admission_RAM_percent=c.POLICY['start_ram_min_percent'],
            new_profile_compiled_inventory_required=True,
            statistical_speedup_proven=False)
        return dump(row,stream,**kwargs)
    with adapter(), patch.object(json,'dump',write):
        return captured.run_owned(destination,expected,names,modules)


def run_light(destination):
    from tests.test_compression_full_stored import CompressionFullStoredTests
    from tests.test_aead_full_stored import AeadFullStoredTests
    resources = SQLRuntimeResources(); row = {}
    try:
        resources.admit(); q = LiveSQLReader(resources)
        freeze = [q.pin(n) for n in (SELF,TEST,candidate.SELF,candidate.TEST,captured.SELF,captured.TEST)]
        suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(t)
            for t in (CompressionFullStoredTests,AeadFullStoredTests))
        with patch('subprocess.Popen',side_effect=AssertionError('AEAD_FULL_LIGHT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('AEAD_FULL_LIGHT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('AEAD_FULL_LIGHT_THREAD_FORBIDDEN')):
            result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
        failed = sorted({t.id().split('.')[-1] for t,_ in result.failures+result.errors+result.skipped})
        passed = result.testsRun == LIGHT_TESTS and result.wasSuccessful() and not result.skipped
        q.finish()
        row.update(state='PASS_AEAD_FULL_CONTRACT_ONLY_NOT_RUNTIME_OR_GATE' if passed else 'FAILED_NOT_ACCEPTED',
            tests_run=result.testsRun,tests_passed=result.testsRun-len(failed),failed_tests=failed,
            source_freeze=freeze,source_closing_exact=True,Cargo_SQL_native_executed=False,
            product_complete=False,P09_gate='OPEN',IO=q.summary())
    finally:
        row['resource_stop'] = resources.reason; finish_watcher(resources,row)
    c.require(row['resource_stop'] is None and row['resource_watcher_cleanup_confirmed'],
        'AEAD_FULL_LIGHT_RESOURCE_STOP')
    with destination.open('x',encoding='utf-8') as stream: json.dump(row,stream,indent=2)
    print(json.dumps({k:row[k] for k in ('state','tests_run','tests_passed','failed_tests')}))
    return 0 if passed else 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--inventory-run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--light',action='store_true')
    args = parser.parse_args(); require_scope(MAXIMUM_SECONDS)
    c.require(c.Path.cwd().resolve() == c.ROOT,'AEAD_FULL_ROOT_SCOPE')
    kind = 'light' if args.light else 'actual'
    destination = scoped_path(f'implementation/p09/evidence/p09-149-aead-full-stored.{kind}-run{args.run:02}.v1.json',fresh=True)
    if args.light: return run_light(destination)
    return run_owned(destination,*load_binding(args.inventory_run))


if __name__ == '__main__':
    if sys.argv[1:] == ['--owned-worker','--task',TASK]: raise SystemExit(worker())
    try: raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as error:
        code = ('DEFERRED_RESOURCE_ADMISSION_NOT_SATISFIED' if isinstance(error,ValueError)
            and str(error) == 'bootstrap_idle_window_not_admitted' else
            (str(error) if isinstance(error,ValueError) and re.fullmatch('[A-Z_]+',str(error)) else 'AEAD_FULL_OPERATION_FAILED'))
        print(json.dumps({'state':'FAILED_NOT_ACCEPTED','error_code':code})); raise SystemExit(2) from None
