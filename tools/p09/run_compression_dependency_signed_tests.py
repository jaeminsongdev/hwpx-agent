"""Exact ZIP/flate2/zlib-rs test-profile candidate; unchanged owned resource caps.

Same complete36 importer diagnostic, then fresh compiled249 and original signed16.
No product source, assertions, authorization, freshness, or global config changes.
"""
import argparse
import io
import json
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

import run_reconstruction_stage_profile as reconstruction
import run_xml_dependency_signed_tests as xml_profile
import run_optimized_signed_tests as signed
from current_issuer_build_inputs import rust_inputs
from live_sql_evidence_reader import LiveSQLReader
from sql_owned_execution import scoped_path
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher

c = reconstruction.c
SELF = 'tools/p09/run_compression_dependency_signed_tests.py'
TEST = 'tools/p09/tests/test_compression_dependency_signed_tests.py'
DIAGNOSTIC = 'compression-dependency-reconstruction-profile'
INVENTORY = 'compression-dependency-signed-inventory'
PROFILE = 'compression-dependency-signed-tests'
VARIANT = 'unchanged-r19-sources-zip-flate2-zlib-rs-test-opt1-r20'
BASE_CONFIG = xml_profile.CONFIG
COMPRESSION_PACKAGES = ('zip', 'flate2', 'zlib-rs')
COMPRESSION_CONFIG = tuple(f'profile.test.package.{name}.{key}={value}' for name in COMPRESSION_PACKAGES for key, value in (
    ('opt-level', '1'), ('debug-assertions', 'true'), ('overflow-checks', 'true'),
    ('codegen-units', '16'), ('debug', '"line-tables-only"')))
CONFIG = (*BASE_CONFIG, *COMPRESSION_CONFIG)
PARENT = {"path":"implementation/p09/evidence/p09-149-xml-dependency.summary-run01.v1.json","bytes":21637,"sha256":"43a261e638723da2f5be754bf02e24ff50b34980daa0b76f8b7f26fa792b6116"}
CURRENT = {"path":"implementation/p09/evidence/p09-149-xml-dependency.diagnostic-run01.v1.json","bytes":549588,"sha256":"78b09e7e098fcd3bb875832da54474c600e3316483222290429153a26c069bfb"}


def config_contract(entries):
    c.require(type(entries) is tuple and entries == (*BASE_CONFIG, *COMPRESSION_CONFIG)
        and len(entries) == 41 and len({e.split('=', 1)[0] for e in entries}) == 41,
        'COMPRESSION_DEPENDENCY_CLOSED_CONFIG_REQUIRED')


def require_duration(task, seconds):
    c.require(task in (DIAGNOSTIC, INVENTORY, PROFILE) and type(seconds) is int
        and 30 <= seconds <= (600 if task == INVENTORY else 180), 'COMPRESSION_DEPENDENCY_FINITE_SCOPE')


def inventory_path(run):
    signed.previous.original.inventory_path(run)
    return f'implementation/p09/evidence/p09-149-compression-dependency.inventory-run{run:02}.v1.json'


def accept_inventory(row, expected, names, modules):
    config_contract(CONFIG)
    c.require(row.get('source_variant') == VARIANT and row.get('task') == INVENTORY
        and row.get('test_package_profile_config') == list(CONFIG)
        and row.get('compression_dependencies_opt_level') == 1
        and row.get('original_owned_resource_policy_changed') is False,
        'COMPRESSION_DEPENDENCY_CURRENT_INVENTORY_REQUIRED')
    with patch.object(signed, 'CONFIG', CONFIG):
        signed.accept_inventory(dict(row, source_variant=signed.SOURCE_VARIANT,
            task=signed.INVENTORY), expected, names, modules)


def load_binding(task, inventory_run):
    require_duration(task, 180); config_contract(CONFIG)
    # Reuse the full current r18 freeze, not a historical compiled qualification.
    expected = reconstruction.load_binding()
    resources = SQLRuntimeResources(); resources.admit(); q = LiveSQLReader(resources)
    try:
        c.require(q.pin(PARENT['path']) == PARENT and q.pin(CURRENT['path']) == CURRENT,
            'COMPRESSION_DEPENDENCY_PARENT_PIN_DRIFT')
        summary = q.json(PARENT['path']); current = q.json(CURRENT['path'])
        c.require(summary['source_closing_exact'] is True and summary['current_Rust_inputs'] == 783
            and summary['product_complete'] is False and current['state'] == 'PASS_SCOPED_NOT_GATE'
            and current['cleanup_confirmed'] is True and current['owned_tree_empty'] is True
            and current['job_final']['active_processes'] == 0, 'COMPRESSION_DEPENDENCY_PARENT_SCOPE')
        reconstruction.validate(json.dumps(current['stage_profile']))
        frozen = {p['path']: p for p in current['source_freeze']}
        c.require(len(frozen) == len(current['source_freeze'])
            and all(frozen.get(n) == p for n, p in expected.items()), 'COMPRESSION_DEPENDENCY_PARENT_FREEZE_DRIFT')
        for name, pin in frozen.items():
            c.require(q.pin(name) == pin, 'COMPRESSION_DEPENDENCY_UNDECLARED_INPUT_DRIFT')
        expected.update(frozen)
        for name in (SELF, TEST, PARENT['path'], CURRENT['path']): expected[name] = q.pin(name)
        selected = {n for n in expected if n.startswith(('crates/', 'protocol/generated/rust/', 'tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        c.require(rust_inputs(c.ROOT, resources.checkpoint_io) == selected and len(selected) == 783,
            'COMPRESSION_DEPENDENCY_COMPLETE_RUST_SCOPE_REQUIRED')
        def read(name):
            c.require(name in expected and q.pin(name) == expected[name], 'COMPRESSION_DEPENDENCY_MODULE_SOURCE_DRIFT')
            return q.text(name)
        names, modules = signed.previous.parent.recursive_names(read, 'stored-form-tests')
        signed.previous.original.select_names(names)
        c.require(len(modules) == 59, 'COMPRESSION_DEPENDENCY_COMPLETE_MODULES_REQUIRED')
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
            optimized_compression_dependencies=list(COMPRESSION_PACKAGES),
            compression_dependencies_opt_level=1, compression_dependencies_parent_pin=PARENT,
            product_sources_or_original_test_assertions_changed=False,
            original_owned_resource_policy_changed=False, whole_Cargo_or_OS_settings_changed=False,
            full249_current_qualified=False, statistical_speedup_proven=False,
            PC_freeze_resolved=False, product_complete=False, P09_gate='OPEN')
        return dump(row, stream, **kwargs)
    if task == DIAGNOSTIC:
        with patch.object(reconstruction, 'SELF', SELF), patch.object(reconstruction, 'TEST', TEST), \
                patch.object(reconstruction, 'TASK', DIAGNOSTIC), \
                patch.object(reconstruction.profile, 'CONFIG', CONFIG), patch.object(json, 'dump', write):
            return reconstruction.run_owned(destination, expected, seconds)
    with patch.object(signed, 'SELF', SELF), patch.object(signed, 'TEST', TEST), \
            patch.object(signed, 'INVENTORY', INVENTORY), patch.object(signed, 'PROFILE', PROFILE), \
            patch.object(signed, 'CONFIG', CONFIG), patch.object(json, 'dump', write):
        return signed.run_owned(destination, expected, names, modules, task, seconds)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=int, choices=range(1, 100), required=True)
    parser.add_argument('--task', choices=(DIAGNOSTIC, INVENTORY, PROFILE), default=DIAGNOSTIC)
    parser.add_argument('--inventory-run', type=int, choices=range(1, 100), default=1)
    parser.add_argument('--maximum-seconds', type=int, default=180)
    parser.add_argument('--light', action='store_true')
    args = parser.parse_args(); require_duration(args.task, args.maximum_seconds)
    c.require(c.Path.cwd().resolve() == c.ROOT, 'COMPRESSION_DEPENDENCY_ROOT_SCOPE')
    kind = 'light' if args.light else ('inventory' if args.task == INVENTORY else ('diagnostic' if args.task == DIAGNOSTIC else 'actual'))
    destination = scoped_path(f'implementation/p09/evidence/p09-149-compression-dependency.{kind}-run{args.run:02}.v1.json', fresh=True)
    if not args.light:
        expected, names, modules = load_binding(args.task, args.inventory_run)
        return run_owned(destination, expected, names, modules, args.task, args.maximum_seconds)
    from tests.test_compression_dependency_signed_tests import CompressionDependencySignedTests
    resources = SQLRuntimeResources(); resources.admit(); q = LiveSQLReader(resources); row = {}
    try:
        freeze = [q.pin(n) for n in (SELF, TEST, PARENT['path'], CURRENT['path'])]
        with patch('subprocess.Popen', side_effect=AssertionError('COMPRESSION_DEPENDENCY_LIGHT_CHILD_FORBIDDEN')), \
                patch('subprocess.run', side_effect=AssertionError('COMPRESSION_DEPENDENCY_LIGHT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start', side_effect=AssertionError('COMPRESSION_DEPENDENCY_LIGHT_THREAD_FORBIDDEN')):
            result = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(CompressionDependencySignedTests))
        failed = sorted({t.id().split('.')[-1] for t, _ in result.failures + result.errors + result.skipped})
        passed = result.testsRun == 12 and result.wasSuccessful() and not result.skipped
        q.finish(); row.update(state='PASS_COMPRESSION_DEPENDENCY_CONTRACT_ONLY_NOT_RUNTIME_OR_GATE' if passed else 'FAILED_NOT_ACCEPTED',
            tests_run=result.testsRun, tests_passed=result.testsRun-len(failed), failed_tests=failed,
            source_freeze=freeze, source_closing_exact=True, Cargo_SQL_native_executed=False,
            product_complete=False, P09_gate='OPEN', IO=q.summary())
    finally:
        row['resource_stop'] = resources.reason; finish_watcher(resources, row)
    c.require(row['resource_stop'] is None and row['resource_watcher_cleanup_confirmed'], 'COMPRESSION_DEPENDENCY_LIGHT_RESOURCE_STOP')
    with destination.open('x', encoding='utf-8') as stream: json.dump(row, stream, indent=2)
    print(json.dumps({k: row[k] for k in ('state', 'tests_run', 'tests_passed', 'failed_tests')}))
    return 0 if passed else 2


if __name__ == '__main__':
    if len(sys.argv[1:]) == 3 and sys.argv[1:3] == ['--owned-worker', '--task']:
        raise SystemExit(run_worker(sys.argv[3]))
    try: raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r'[A-Z_]+', str(error)) else 'COMPRESSION_DEPENDENCY_OPERATION_FAILED'
        print(json.dumps({'state': 'FAILED_NOT_ACCEPTED', 'error_code': code})); raise SystemExit(2) from None
