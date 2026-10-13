"""P152 current Rust785/source249 admission ONLY; never launches a compiler.

현재 세대 입력 전체를 새로 해시하며 과거 compiled249를 현재 실행 허가로
승격하지 않는다. 캐시는 재사용할 계획이지만 fresh suffix의 실제 build,
compiled listing, 전체249 실행은 각각 별도 증거가 필요하다.
"""
import argparse
import copy
import io
import json
import re
import sys
import time
import unittest
from unittest.mock import patch

import run_aead_dependency_signed_tests as profile
import current_issuer_build_inputs as inputs
from live_sql_evidence_reader import LiveSQLReader
from sql_owned_execution import scoped_path
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher

c = profile.c
SELF = 'tools/p09/prepare_current_stored_generation.py'
TEST = 'tools/p09/tests/test_current_stored_generation.py'
PARENT = dict(path='implementation/p09/evidence/p09-151-current-SQL-execution.terminal-audit-run01.v1.json',
    bytes=289924, sha256='d28e1223c3cfabebb673e64a6bfec51932671bd72d691cdc87dc4e4fd1165f59')
BUILD = 'implementation/p09/evidence/p09-151-runtime-build.actual-run01.v1.json'
HISTORICAL_INVENTORY = 'implementation/p09/evidence/p09-149-aead-dependency.inventory-run02.v1.json'
PASS = 'PASS_CURRENT_RUST785_SOURCE249_PREPARATION_ONLY_NOT_COMPILED_RUNTIME_SQL_OR_GATE'
TEST_COUNT = 14


def require(ok, code):
    c.require(ok, 'P152_PREP_'+code)


def generation(run):
    require(type(run) is int and 1 <= run <= 99, 'RUN_SCOPE')
    return f'p152-r{run:02}'


def executable_name(run):
    return (c.TARGET/'debug/deps'/f'form_stored_provider-{generation(run)}.exe').relative_to(c.ROOT).as_posix()


def recipe(run):
    """A closed plan, NOT a callable executor or a build/runtime qualification."""
    profile.config_contract(profile.CONFIG)
    require(len(profile.CONFIG) == 81, 'PROFILE81')
    return dict(generation=generation(run), executable_path=executable_name(run),
        argv_without_cargo=[*[v for e in profile.CONFIG for v in ('--config', e)],
            'rustc', '-p', 'hwpx-agent-cli', '--test', 'form_stored_provider', '--profile', 'test',
            '--locked', '--offline', '--jobs', '1', '--color=never', '--target-dir', str(c.TARGET),
            '--message-format=json', '--', '-C', f'extra-filename=-{generation(run)}'],
        compile_maximum_seconds=600, full249_maximum_seconds=1200,
        test_package_profile_config=list(profile.CONFIG), compile_admission_RAM_percent=15,
        runtime_admission_RAM_percent=10, test_threads=1, cache_reuse_planned=True,
        actual_cache_hit_or_speedup_proven=False, executor_connected=False,
        build_catalog_requires_test_true=True, compiled249_listing_required_before_runtime=True,
        runtime_argv=['--test-threads=1', '--format=terse'], runtime_RUST_TEST_NOCAPTURE='0',
        full249_unfiltered_required=True, policy=copy.deepcopy(c.POLICY))


def parent_scope(row):
    require(isinstance(row, dict) and row.get('state') ==
        'PASS_CURRENT39_PRE_BACKEND_CANCEL_HOST_CLOSING_ONLY_NOT_SQL_NATIVE_OR_GATE'
        and row.get('source_closing_exact') is True and row.get('current_Rust_input_count') == 785
        and row.get('compiled_source_count') == 846 and row.get('protected_executables_exact') == 53
        and row.get('contract_tests_passed') == 36 and row.get('required_check_count') == 39
        and row.get('resource_stop_reason') is None and row.get('resource_watcher_cleanup_confirmed') is True
        and row.get('actual_SQL_native_or_runtime_EXE_executed') is False
        and row.get('product_complete') is False and row.get('P09_gate') == 'OPEN', 'PARENT_SCOPE')
    return inputs.inventory(row['bound_input_pins'], 1185)


def protected_scope(build, row, expected):
    require(build.get('state') == 'PASS_CURRENT_DS06_NON_TEST_RUNTIME_BUILD_ONLY_NOT_SQL_NATIVE_OR_GATE'
        and build.get('current_build_binding_accepted') is True
        and build.get('protected_executables_exact_after') is True
        and build.get('source_freeze_exact_after') is True, 'CURRENT_BUILD_SCOPE')
    protected = inputs.inventory([*build['protected_executables'], build['executable_pin']], 54)
    require(build['executable_pin'] == row['current_runtime_executable_pin'], 'CURRENT_RUNTIME_IDENTITY')
    require(all(expected.get(n) == p for n, p in protected.items()), 'PROTECTED_WHOLE_CLOSURE')
    return protected


def require_fresh_output(run, protected):
    name = executable_name(run)
    require(name not in protected, 'OUTPUT_OVERLAPS_HISTORY')
    scoped_path(name, fresh=True)
    return name


def load_current(q, resources, run):
    require(q.pin(PARENT['path']) == PARENT, 'IMMUTABLE_PARENT')
    row = q.json(PARENT['path']); expected = parent_scope(row)
    # Each original parent member is read in full, then again at closing.
    for name, pin in expected.items():
        require(q.pin(name) == pin, 'CURRENT_INPUT_DRIFT')
    rust = {n for n in expected if n.startswith(('crates/', 'protocol/generated/rust/', 'tools/xtask/'))
        and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
    require(len(rust) == 785 and inputs.rust_inputs(c.ROOT, resources.checkpoint_io) == rust, 'WHOLE_RUST785')
    protected = protected_scope(q.json(BUILD), row, expected)
    require_fresh_output(run, protected)
    def read(name):
        require(name in expected, 'MODULE_OUTSIDE_CURRENT_PARENT')
        value = q.text(name)
        require(q.reader.snapshots[name] == expected[name], 'CURRENT_MODULE_DRIFT')
        return value
    names, modules = profile.signed.previous.parent.recursive_names(read, 'stored-form-tests')
    profile.signed.previous.original.select_names(names)
    require(len(modules) == 59, 'COMPLETE59_MODULES')
    prior = q.json(HISTORICAL_INVENTORY)
    require(prior.get('source_test_names') == list(names) and prior.get('source_module_instances') == list(modules)
        and prior.get('test_package_profile_config') == list(profile.CONFIG), 'SOURCE_INVENTORY_CONTINUITY')
    # Historical compiled PASS is intentionally NOT accepted as current compiled PASS.
    helpers = {SELF, TEST}
    for module in tuple(sys.modules.values()):
        file = getattr(module, '__file__', None)
        if file:
            path = c.Path(file).absolute()
            if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix == '.py':
                helpers.add(path.relative_to(c.ROOT).as_posix())
    for name in sorted(helpers):
        q.pin(name)
    return dict(current_Rust_input_count=785, source_test_names=list(names), source_module_instances=list(modules),
        source_test_count=249, source_module_instance_count=59, protected_executables=list(protected.values()),
        protected_executables_exact=54, historical_inventory_used_for_names_only=True,
        original_parent_inputs_exact=1185, imported_helper_inventory=sorted(helpers),
        compile_recipe=recipe(run), current_compiled249_qualified=False, full249_current_qualified=False)


def contracts():
    sys.path.insert(0, str(c.ROOT/'tools/p09/tests'))
    suite = unittest.defaultTestLoader.loadTestsFromName('test_current_stored_generation')
    with patch('subprocess.Popen', side_effect=AssertionError('P152_PREP_CHILD_FORBIDDEN')), \
            patch('subprocess.run', side_effect=AssertionError('P152_PREP_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start', side_effect=AssertionError('P152_PREP_THREAD_FORBIDDEN')):
        result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    failed = sorted({getattr(t, 'test_case', t).id().split('.')[-1]
        for t, _ in result.failures+result.errors+result.skipped})
    require(result.wasSuccessful() and result.testsRun == TEST_COUNT and not result.skipped, 'CONTRACT14')
    return dict(contract_tests_run=result.testsRun, contract_tests_passed=result.testsRun, failed_tests=failed)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--run', type=int, choices=range(1, 100), required=True)
    parser.add_argument('--mode', choices=('light', 'prepare'), required=True); args = parser.parse_args()
    require(c.Path.cwd().resolve() == c.ROOT, 'REPOSITORY_CWD')
    generation(args.run)
    destination = scoped_path(f'implementation/p09/evidence/p09-152-current-stored-generation.{args.mode}-run{args.run:02}.v1.json', fresh=True)
    resources = SQLRuntimeResources(); q = None; started = time.monotonic()
    out = dict(schema_version='hwpx-agent.p09-current-stored-source-generation/v1', state='FAILED_NOT_ACCEPTED',
        mode=args.mode, generation=generation(args.run), parent_closing_pin=PARENT, source_closing_exact=False,
        actual_Cargo_Rustc_SQL_Docker_native_or_child_executed=False, new_git_started=False,
        system_Defender_WSL_Codex_settings_changed=False, raw_logs_included=False,
        current_compiled249_qualified=False, full249_current_qualified=False, signed16_current_qualified=False,
        product_complete=False, P09_gate='OPEN', A12_gate='OPEN', A13_gate='OPEN',
        remaining_non_permission_work_units=76, PC_freeze_resolved=False, resource_samples=resources.samples)
    try:
        resources.admit(); q = LiveSQLReader(resources)
        for name in (SELF, TEST): q.pin(name)
        out.update(contracts())
        if args.mode == 'prepare':
            out.update(load_current(q, resources, args.run))
        q.finish(); out.update(source_closing_exact=True,
            state=PASS if args.mode == 'prepare' else 'PASS_CURRENT_STORED_PREPARATION_CONTRACT_ONLY_NOT_COMPILED_RUNTIME_OR_GATE')
    except (ValueError, OSError, KeyError, TypeError, AttributeError, KeyboardInterrupt) as error:
        code = str(error) if isinstance(error, ValueError) else 'P152_PREP_REDACTED_FAILURE'
        out['error_code'] = code if re.fullmatch('[A-Za-z0-9_]{1,160}', code) else 'P152_PREP_REDACTED_FAILURE'
    finally:
        if q is not None and not q.finished:
            try: q.finish(); out['source_closing_exact'] = True
            except (ValueError, OSError): out['final_freshness_error'] = 'P152_PREP_FINAL_FRESHNESS'
        finish_watcher(resources, out); out['resource_stop_reason'] = resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):
            out['state'] = 'FAILED_NOT_ACCEPTED'
        if q is not None:
            out['IO'] = q.summary(); out['bound_input_pins'] = list(q.reader.snapshots.values())
        out['wall_seconds'] = round(time.monotonic()-started, 4)
        with destination.open('x', encoding='utf-8') as stream: json.dump(out, stream, indent=2)
        print(json.dumps({k: out.get(k) for k in ('state', 'contract_tests_passed', 'source_test_count',
            'protected_executables_exact', 'error_code', 'wall_seconds', 'resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') and out['source_closing_exact'] else 2


if __name__ == '__main__': raise SystemExit(main())
