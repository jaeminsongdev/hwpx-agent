"""Exact AEAD dependency test-profile candidate; unchanged owned resource caps.

Same complete36 diagnostic, fresh compiled249 and unchanged signed test; no result
is qualified from the prior RAM-stopped run. The full r21 source freeze is bound.
No product source, assertions, authorization, freshness, or global config changes.
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
from unittest.mock import patch

import run_reconstruction_stage_profile as reconstruction
import run_compression_dependency_signed_tests as compression_profile
import run_optimized_signed_tests as signed
from current_issuer_build_inputs import rust_inputs
from live_sql_evidence_reader import LiveSQLReader
from sql_owned_execution import scoped_path
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher

c = reconstruction.c
SELF = 'tools/p09/run_aead_dependency_signed_tests.py'
TEST = 'tools/p09/tests/test_aead_dependency_signed_tests.py'
DIAGNOSTIC = 'aead-dependency-reconstruction-profile'
INVENTORY = 'aead-dependency-signed-inventory'
PROFILE = 'aead-dependency-signed-tests'
VARIANT = 'unchanged-r21-sources-aead-stack-test-opt1-r23'
BASE_CONFIG = compression_profile.CONFIG
AEAD_PACKAGES = ('aead', 'aes', 'aes-gcm', 'cipher', 'ctr', 'ghash', 'polyval', 'universal-hash')
AEAD_CONFIG = tuple(f'profile.test.package.{name}.{key}={value}' for name in AEAD_PACKAGES for key, value in (
    ('opt-level', '1'), ('debug-assertions', 'true'), ('overflow-checks', 'true'),
    ('codegen-units', '16'), ('debug', '"line-tables-only"')))
CONFIG = (*BASE_CONFIG, *AEAD_CONFIG)
HEADROOM_ARCHIVE = 'implementation/p09/source-archive/p09-149-pre-aead-compiler-headroom-r23/helper-preimages.v1.json'
HEADROOM_LIGHT = {'path':'implementation/p09/evidence/p09-149-aead-dependency.light-run01.v1.json',
    'bytes':1478,'sha256':'de90fc241e3663b6acf7a3eec35e3e358f51b0ed50b01e5707a3bd8aca8163af'}
BASE_ADMITTED_COUNT = c.admitted_count


def admission_ram_percent(task):
    c.require(task in (DIAGNOSTIC, INVENTORY, PROFILE), 'AEAD_DEPENDENCY_ADMISSION_TASK_SCOPE')
    return (c.POLICY['stop_ram_min_percent'] + c.POLICY['job_memory_stop_percent']
        if task in (DIAGNOSTIC, INVENTORY) else c.POLICY['start_ram_min_percent'])


def admission_count(task, row, count):
    # Compiler peak must fit above the original emergency reserve. No cap increase.
    return BASE_ADMITTED_COUNT(row, count) if row['available_ram_percent'] >= admission_ram_percent(task) else 0
PARENT = {"path":"implementation/p09/evidence/p09-149-compression-captured-suite.terminal-audit-run01.v1.json","bytes":9174,"sha256":"333380ecf6f02892fec76fcd4581e5b6e61ff03026a7268a4af97b086f571af7"}
CURRENT = {"path":"implementation/p09/evidence/p09-149-compression-full-stored.actual-run02.v1.json","bytes":3322888,"sha256":"103c85ed2b7bad5885c37e7cc22f8f55ba46c4a2c6435b4f8110e34687940557"}


def config_contract(entries):
    c.require(type(entries) is tuple and entries == (*BASE_CONFIG, *AEAD_CONFIG)
        and len(entries) == 81 and len({e.split('=', 1)[0] for e in entries}) == 81,
        'AEAD_DEPENDENCY_CLOSED_CONFIG_REQUIRED')


def require_duration(task, seconds):
    c.require(task in (DIAGNOSTIC, INVENTORY, PROFILE) and type(seconds) is int
        and 30 <= seconds <= (600 if task == INVENTORY else 180), 'AEAD_DEPENDENCY_FINITE_SCOPE')


def inventory_path(run):
    signed.previous.original.inventory_path(run)
    return f'implementation/p09/evidence/p09-149-aead-dependency.inventory-run{run:02}.v1.json'


def accept_inventory(row, expected, names, modules):
    config_contract(CONFIG)
    c.require(row.get('source_variant') == VARIANT and row.get('task') == INVENTORY
        and row.get('test_package_profile_config') == list(CONFIG)
        and row.get('aead_dependencies_opt_level') == 1
        and row.get('original_owned_resource_policy_changed') is False,
        'AEAD_DEPENDENCY_CURRENT_INVENTORY_REQUIRED')
    with patch.object(signed, 'CONFIG', CONFIG):
        signed.accept_inventory(dict(row, source_variant=signed.SOURCE_VARIANT,
            task=signed.INVENTORY), expected, names, modules)



def accept_parent(summary, current):
    # A stopped run binds exact current bytes, never runtime/Gate qualification.
    c.require(summary.get('state') == 'PASS_R21_TERMINAL_AUDIT_FULL249_UNFINISHED_NOT_SQL_NATIVE_OR_GATE'
        and summary.get('source_closing_exact') is True and summary.get('current_Rust_inputs') == 783
        and summary.get('compiled_inventory_current_exact') is True
        and summary.get('original_stored_test_names') == 249 and summary.get('original_stored_module_instances') == 59
        and summary.get('execution_source_freezes_current_exact') is True
        and summary.get('product_complete') is False and summary.get('full249_current_qualified') is False
        and summary.get('resource_stop') is None and summary.get('resource_watcher_cleanup_confirmed') is True
        and CURRENT in summary.get('support_pins', []), 'AEAD_DEPENDENCY_EXACT_TERMINAL_AUDIT_REQUIRED')
    c.require(current.get('state') == 'STOPPED_NOT_ACCEPTED' and current.get('stop_reason') == 'STOP_LOW_AVAILABLE_RAM'
        and current.get('tests_passed') is None and current.get('full249_current_qualified') is False
        and current.get('signed16_current_qualified') is False and current.get('product_complete') is False
        and current.get('cleanup_confirmed') is True and current.get('owned_tree_empty') is True
        and current.get('job_final', {}).get('active_processes') == 0
        and current.get('policy') == c.POLICY and current.get('maximum_seconds') == 1200
        and current.get('test_package_profile_config') == list(compression_profile.CONFIG)
        and current.get('capture_diagnostics', {}).get('error_code') is None
        and current.get('capture_diagnostics', {}).get('per_stream_limit_bytes') == 32768,
        'AEAD_DEPENDENCY_STOPPED_PARENT_NOT_RUNTIME_PASS')


def load_binding(task, inventory_run):
    require_duration(task, 180); config_contract(CONFIG)
    # Reuse the full current r18 freeze, not a historical compiled qualification.
    expected = reconstruction.load_binding()
    resources = SQLRuntimeResources(); resources.admit(); q = LiveSQLReader(resources)
    try:
        c.require(q.pin(PARENT['path']) == PARENT and q.pin(CURRENT['path']) == CURRENT,
            'AEAD_DEPENDENCY_PARENT_PIN_DRIFT')
        summary = q.json(PARENT['path']); current = q.json(CURRENT['path'])
        accept_parent(summary, current)
        frozen = {p['path']: p for p in current['source_freeze']}
        c.require(len(frozen) == len(current['source_freeze'])
            and all(frozen.get(n) == p for n, p in expected.items()), 'AEAD_DEPENDENCY_PARENT_FREEZE_DRIFT')
        for name, pin in frozen.items():
            c.require(q.pin(name) == pin, 'AEAD_DEPENDENCY_UNDECLARED_INPUT_DRIFT')
        expected.update(frozen)
        c.require(q.pin(HEADROOM_LIGHT['path']) == HEADROOM_LIGHT, 'AEAD_DEPENDENCY_PRE_HEADROOM_LIGHT_DRIFT')
        light = q.json(HEADROOM_LIGHT['path']); archive = q.json(HEADROOM_ARCHIVE)
        c.require(light['tests_run'] == light['tests_passed'] == 14 and not light['failed_tests']
            and light['source_closing_exact'] and archive['qualified_light_pin'] == HEADROOM_LIGHT,
            'AEAD_DEPENDENCY_PRE_HEADROOM_SCOPE')
        original = {p['path']:p for p in light['source_freeze']}; seen = set()
        for item in archive['files']:
            name = item['path']; raw = base64.b64decode(item['base64'], validate=True)
            pin = {k:item[k] for k in ('path','bytes','sha256')}
            c.require(name in (SELF,TEST) and name not in seen and original[name] == pin
                and len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'],
                'AEAD_DEPENDENCY_PRE_HEADROOM_PREIMAGE_DRIFT')
            seen.add(name)
        c.require(seen == {SELF,TEST}, 'AEAD_DEPENDENCY_PRE_HEADROOM_FULL_HELPERS_REQUIRED')
        for name in (SELF, TEST, PARENT['path'], CURRENT['path'], HEADROOM_ARCHIVE, HEADROOM_LIGHT['path']): expected[name] = q.pin(name)
        selected = {n for n in expected if n.startswith(('crates/', 'protocol/generated/rust/', 'tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        c.require(rust_inputs(c.ROOT, resources.checkpoint_io) == selected and len(selected) == 783,
            'AEAD_DEPENDENCY_COMPLETE_RUST_SCOPE_REQUIRED')
        def read(name):
            c.require(name in expected and q.pin(name) == expected[name], 'AEAD_DEPENDENCY_MODULE_SOURCE_DRIFT')
            return q.text(name)
        names, modules = signed.previous.parent.recursive_names(read, 'stored-form-tests')
        signed.previous.original.select_names(names)
        c.require(len(modules) == 59, 'AEAD_DEPENDENCY_COMPLETE_MODULES_REQUIRED')
        if task == PROFILE:
            name = inventory_path(inventory_run)
            accept_inventory(q.json(name), expected, names, modules)
            expected[name] = q.pin(name)
        q.finish()
        return expected, names, modules
    finally:
        c.require(finish_watcher(resources, {}), 'STOP_BINDING_WATCHER_CLEANUP_FAILED')


def run_worker(task):
    require_duration(task, 180); config_contract(CONFIG)
    if task == DIAGNOSTIC:
        with patch.object(reconstruction, 'TASK', DIAGNOSTIC), patch.object(reconstruction.profile, 'CONFIG', CONFIG):
            return reconstruction.worker()
    with patch.object(signed, 'INVENTORY', INVENTORY), patch.object(signed, 'PROFILE', PROFILE), \
            patch.object(signed, 'CONFIG', CONFIG):
        return signed.run_worker(task)


def run_owned(destination, expected, names, modules, task, seconds):
    require_duration(task, seconds); config_contract(CONFIG); dump = json.dump
    def write(row, stream, **kwargs):
        row.update(source_variant=VARIANT, test_package_profile_config=list(CONFIG),
            additional_admission_available_RAM_min_percent=admission_ram_percent(task),
            optimized_aead_dependencies=list(AEAD_PACKAGES),
            aead_dependencies_opt_level=1, aead_dependencies_parent_pin=PARENT,
            product_sources_or_original_test_assertions_changed=False,
            original_owned_resource_policy_changed=False, whole_Cargo_or_OS_settings_changed=False,
            full249_current_qualified=False, statistical_speedup_proven=False,
            PC_freeze_resolved=False, product_complete=False, P09_gate='OPEN')
        return dump(row, stream, **kwargs)
    if task == DIAGNOSTIC:
        with patch.object(reconstruction, 'SELF', SELF), patch.object(reconstruction, 'TEST', TEST), \
                patch.object(reconstruction, 'TASK', DIAGNOSTIC), \
                patch.object(reconstruction.profile, 'CONFIG', CONFIG), patch.object(json, 'dump', write), \
                patch.object(c, 'admitted_count', lambda row,count: admission_count(task,row,count)):
            return reconstruction.run_owned(destination, expected, seconds)
    with patch.object(signed, 'SELF', SELF), patch.object(signed, 'TEST', TEST), \
            patch.object(signed, 'INVENTORY', INVENTORY), patch.object(signed, 'PROFILE', PROFILE), \
            patch.object(signed, 'CONFIG', CONFIG), patch.object(json, 'dump', write), \
            patch.object(c, 'admitted_count', lambda row,count: admission_count(task,row,count)):
        return signed.run_owned(destination, expected, names, modules, task, seconds)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=int, choices=range(1, 100), required=True)
    parser.add_argument('--task', choices=(DIAGNOSTIC, INVENTORY, PROFILE), default=DIAGNOSTIC)
    parser.add_argument('--inventory-run', type=int, choices=range(1, 100), default=1)
    parser.add_argument('--maximum-seconds', type=int, default=180)
    parser.add_argument('--light', action='store_true')
    args = parser.parse_args(); require_duration(args.task, args.maximum_seconds)
    c.require(c.Path.cwd().resolve() == c.ROOT, 'AEAD_DEPENDENCY_ROOT_SCOPE')
    kind = 'light' if args.light else ('inventory' if args.task == INVENTORY else ('diagnostic' if args.task == DIAGNOSTIC else 'actual'))
    destination = scoped_path(f'implementation/p09/evidence/p09-149-aead-dependency.{kind}-run{args.run:02}.v1.json', fresh=True)
    if not args.light:
        expected, names, modules = load_binding(args.task, args.inventory_run)
        return run_owned(destination, expected, names, modules, args.task, args.maximum_seconds)
    from tests.test_aead_dependency_signed_tests import AeadDependencySignedTests
    resources = SQLRuntimeResources(); resources.admit(); q = LiveSQLReader(resources); row = {}
    try:
        freeze = [q.pin(n) for n in (SELF, TEST, PARENT['path'], CURRENT['path'])]
        with patch('subprocess.Popen', side_effect=AssertionError('AEAD_DEPENDENCY_LIGHT_CHILD_FORBIDDEN')), \
                patch('subprocess.run', side_effect=AssertionError('AEAD_DEPENDENCY_LIGHT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start', side_effect=AssertionError('AEAD_DEPENDENCY_LIGHT_THREAD_FORBIDDEN')):
            result = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(AeadDependencySignedTests))
        failed = sorted({t.id().split('.')[-1] for t, _ in result.failures + result.errors + result.skipped})
        passed = result.testsRun == 17 and result.wasSuccessful() and not result.skipped
        q.finish(); row.update(state='PASS_AEAD_DEPENDENCY_CONTRACT_ONLY_NOT_RUNTIME_OR_GATE' if passed else 'FAILED_NOT_ACCEPTED',
            tests_run=result.testsRun, tests_passed=result.testsRun-len(failed), failed_tests=failed,
            source_freeze=freeze, source_closing_exact=True, Cargo_SQL_native_executed=False,
            product_complete=False, P09_gate='OPEN', IO=q.summary())
    finally:
        row['resource_stop'] = resources.reason; finish_watcher(resources, row)
    c.require(row['resource_stop'] is None and row['resource_watcher_cleanup_confirmed'], 'AEAD_DEPENDENCY_LIGHT_RESOURCE_STOP')
    with destination.open('x', encoding='utf-8') as stream: json.dump(row, stream, indent=2)
    print(json.dumps({k: row[k] for k in ('state', 'tests_run', 'tests_passed', 'failed_tests')}))
    return 0 if passed else 2


if __name__ == '__main__':
    if len(sys.argv[1:]) == 3 and sys.argv[1:3] == ['--owned-worker', '--task']:
        raise SystemExit(run_worker(sys.argv[3]))
    try: raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        code = ('DEFERRED_RESOURCE_ADMISSION_NOT_SATISFIED' if isinstance(error, ValueError)
            and str(error) == 'bootstrap_idle_window_not_admitted' else
            (str(error) if isinstance(error, ValueError) and re.fullmatch(r'[A-Z_]+', str(error)) else 'AEAD_DEPENDENCY_OPERATION_FAILED'))
        print(json.dumps({'state': 'FAILED_NOT_ACCEPTED', 'error_code': code})); raise SystemExit(2) from None

