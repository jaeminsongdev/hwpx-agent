"""P152 current stored249 libtest build only, original owned limits unchanged.

원래 Cargo stream의 모든 record 검사/해시/상한/reader 정리를 재사용한다.
test target만 별도 선택하고 fresh suffix에 결과를 결합한다. build는 listing,
전체249 runtime 또는 SQL/native/Gate 성공이 아니다.
"""
import argparse
import contextlib
import copy
import io
import json
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

import prepare_current_stored_generation as prepared
import build_signed_durable_probe as legacy

c = prepared.c
SELF = 'tools/p09/build_current_stored_generation.py'
TEST = 'tools/p09/tests/test_build_current_stored_generation.py'
TARGET = c.TARGET
ARGS = ['rustc', '-p', 'hwpx-agent-cli', '--test', 'form_stored_provider', '--profile', 'test']
CONFIG = prepared.profile.CONFIG
AUDIT_PIN = dict(path='implementation/p09/evidence/p09-152-current-stored-generation.terminal-audit-run01.v1.json',
    bytes=299334, sha256='45b6fef6145b797a6d9bcc17f561a3e70e1066e9f54774d15ee6d3e05d16eec9')
PASS = 'PASS_CURRENT_STORED_LIBTEST_BUILD_ONLY_NOT_LISTING_RUNTIME_SQL_NATIVE_OR_GATE'
EXPECTED_PROFILE = dict(opt_level='1', debuginfo='line-tables-only', debug_assertions=True,
    overflow_checks=True, test=True)
RAW_PARSE = legacy.parse_build
RAW_STREAM = legacy.stream.CargoStream
TEST_COUNT = 16


def require(ok, code): c.require(ok, 'P152_BUILD_'+code)


def task_for(run):
    prepared.generation(run); return f'p152-current-stored-build-r{run:02}'


def run_for(task):
    require(isinstance(task, str) and re.fullmatch(r'p152-current-stored-build-r[0-9]{2}', task), 'TASK_SCOPE')
    run = int(task[-2:]); require(task_for(run) == task, 'TASK_SCOPE'); return run


def executable_name(run): return prepared.executable_name(run)


def profile_scope(profile):
    require(profile == EXPECTED_PROFILE and all(type(profile[k]) is bool
        for k in ('debug_assertions', 'overflow_checks', 'test')), 'LIBTEST_ASSERTION_PROFILE')


class CargoStream(RAW_STREAM):
    def accept(self, raw):
        # Original implementation validates EVERY raw record and total raw SHA.
        super().accept(raw)
        if not raw.strip(): return
        item = json.loads(raw.decode('utf-8'), object_pairs_hook=legacy.stream.unique_object)
        if item.get('reason') != 'compiler-artifact': return
        name = item.get('target', {}).get('name')
        require(name != 'formula_issuer_product_postgres_probe', 'UNRELATED_PROBE_ARTIFACT')
        if name != 'form_stored_provider': return
        require(self.artifact is None and item['target'].get('kind') == ['test'], 'EXACT_TEST_TARGET')
        original_profile = item.get('profile'); require(isinstance(original_profile, dict), 'PROFILE_SHAPE')
        profile = {k: original_profile.get(k) for k in EXPECTED_PROFILE}; profile_scope(profile)
        self.artifact = dict(reason='compiler-artifact', target=dict(name='form_stored_provider'),
            profile=profile, executable=item.get('executable'))


def parse_build(output, run, *, require_stream=False):
    prepared.generation(run)
    require(isinstance(output, str) and len(output.encode()) <= 32768, 'OUTPUT_BUDGET')
    translated = []; actual_profile = None; announcement = None
    for line in output.splitlines():
        if not line.strip(): continue
        try: item = json.loads(line, object_pairs_hook=legacy.stream.unique_object)
        except json.JSONDecodeError: raise ValueError('P152_BUILD_INVALID_JSON') from None
        require(isinstance(item, dict), 'RECORD_SHAPE')
        if item.get('reason') == 'compiler-artifact':
            require(item.get('target', {}).get('name') == 'form_stored_provider'
                and actual_profile is None, 'EXACT_ONE_CLOSED_TARGET')
            actual_profile = item.get('profile'); profile_scope(actual_profile)
            name = item.get('executable'); require(isinstance(name, str), 'EXECUTABLE_MISSING')
            path = c.Path(name); exact = c.ROOT/executable_name(run)
            canonical = path.parent == TARGET/'debug/deps' and bool(re.fullmatch(r'form_stored_provider-[0-9a-f]{16}\.exe', path.name))
            require(path.is_absolute() and (path == exact or canonical), 'EXECUTABLE_SCOPE')
            require(not canonical or require_stream, 'CANONICAL_NOT_EXECUTABLE_BINDING')
            if require_stream: require(prepared.scoped_path(executable_name(run)).is_file(), 'FRESH_SUFFIX_FILE_REQUIRED')
            announcement = 'canonical_hashed_name_with_frozen_driver_suffix' if canonical else 'exact_suffix_name'
            # Reuse the unchanged closed stream proof parser. Actual test=true
            # was required ABOVE; the translated false value is only an adapter
            # for its old non-test validator, never the observed catalog result.
            item = copy.deepcopy(item); item['target']['name'] = 'formula_issuer_product_postgres_probe'
            item['profile']['test'] = False; item['executable'] = str(exact)
        translated.append(json.dumps(item, separators=(',', ':')))
    require(actual_profile is not None, 'TEST_ARTIFACT_REQUIRED')
    with patch.object(legacy, 'executable_name', executable_name):
        result = RAW_PARSE('\n'.join(translated)+'\n', run, require_stream=require_stream)
    result.update(catalog_profile=actual_profile, Cargo_announcement_kind=announcement,
        actual_catalog_test_true_validated_before_legacy_protocol_adapter=True)
    return result


def worker(task):
    run = run_for(task); recipe = prepared.recipe(run)
    def selected(args, **kw):
        require(args[1:] == [*ARGS, '--locked', '--offline', '--jobs', '1', '--color=never', '--target-dir', str(TARGET)], 'WORKER_ARGUMENT_SCOPE')
        require(kw.get('cwd') == c.ROOT and kw.get('stdin') == subprocess.DEVNULL, 'WORKER_CALL_SCOPE')
        env = dict(kw['env'])
        require(all(not env.get(k) for k in ('RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'RUSTC_WRAPPER',
            'RUSTC_WORKSPACE_WRAPPER', 'RUSTC', 'CARGO_BUILD_TARGET')), 'AMBIENT_COMPILER_OVERRIDE')
        require(all(env.get(k) == v for k, v in dict(CARGO_BUILD_JOBS='1', CARGO_PROFILE_TEST_OPT_LEVEL='0',
            CARGO_PROFILE_TEST_CODEGEN_UNITS='16', CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',
            CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true', RUST_TEST_THREADS='1', RUSTUP_AUTO_INSTALL='0').items()), 'ORIGINAL_POLICY_ENVIRONMENT')
        for name in ('P150_BLOB_ROOT', 'P150_BLOB_RUN_ID', 'P150_BLOB_MODE'): env.pop(name, None)
        env['CARGO_INCREMENTAL'] = '0'; kw['env'] = env
        with patch.object(legacy.stream, 'CargoStream', CargoStream):
            return legacy.stream.run_command([args[0], *recipe['argv_without_cargo']], kw,
                lambda output: parse_build(output, run, require_stream=True))
    with patch.object(c, 'TARGET', TARGET), patch.object(c, 'TASKS', {task: ARGS}), patch.object(subprocess, 'call', selected):
        return c.worker(task)


def load_binding(run):
    resources = prepared.SQLRuntimeResources(); state = {}
    try:
        resources.admit(); q = prepared.LiveSQLReader(resources)
        require(q.pin(AUDIT_PIN['path']) == AUDIT_PIN, 'IMMUTABLE_PREPARATION_CLOSING')
        row = q.json(AUDIT_PIN['path'])
        require(row['state'] == 'PASS_CURRENT_RUST785_SOURCE249_CLOSING_ONLY_NOT_COMPILED_RUNTIME_SQL_OR_GATE'
            and row['source_closing_exact'] and row['current_Rust_input_count'] == 785
            and row['source_test_count'] == 249 and row['source_module_instance_count'] == 59
            and row['protected_executables_exact'] == 54 and row['preserved_parent_EXE_input_count'] == 59
            and row['compile_executor_connected'] is False and row['full249_current_qualified'] is False
            and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'], 'PARENT_SCOPE')
        expected = prepared.inputs.inventory(row['bound_input_pins'], 1190)
        for name, pin in expected.items(): require(q.pin(name) == pin, 'CURRENT_INPUT_DRIFT')
        original = q.json(prepared.PARENT['path']); prior = prepared.parent_scope(original)
        protected = prepared.protected_scope(q.json(prepared.BUILD), original, prior)
        prepared.require_fresh_output(run, protected)
        rust = {n for n in expected if n.startswith(('crates/', 'protocol/generated/rust/', 'tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust) == 785 and prepared.inputs.rust_inputs(c.ROOT, resources.checkpoint_io) == rust, 'WHOLE_RUST785')
        helpers = {SELF, TEST, AUDIT_PIN['path']}
        for module in tuple(sys.modules.values()):
            file = getattr(module, '__file__', None)
            if file:
                path = c.Path(file).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix == '.py': helpers.add(path.relative_to(c.ROOT).as_posix())
        for name in sorted(helpers): expected[name] = q.pin(name)
        q.finish(); return expected, list(protected.values()), sorted(helpers)
    finally: require(prepared.finish_watcher(resources, state), 'WATCHER_CLEANUP')


def run_owned(run, destination, expected, protected, helpers):
    dump = json.dump
    def write(row, stream, **kw):
        accepted = row.get('current_build_binding_accepted') is True
        if row.get('state') == legacy.PASS: row['state'] = PASS
        row.pop('current_dev_package_profile_config', None)
        row.update(schema_version='hwpx-agent.p09-current-stored-libtest-build/v1',
            whole_workspace_Rust_input_count=785, current_test_package_profile_config=list(CONFIG),
            current_source249_preparation_closing_pin=AUDIT_PIN, protected_executables_expected=54,
            previous_parent_EXE_inputs_preserved=59, source249_generation_connected_to_actual_build=True,
            build_only_accepted=accepted, compile_recipe=prepared.recipe(run),
            current_compiled249_qualified=False, full249_current_qualified=False, signed16_current_qualified=False,
            compiled249_listing_required_before_runtime=True, runtime_tests_executed=False,
            remaining_non_permission_work_units=76)
        return dump(row, stream, **kw)
    with contextlib.ExitStack() as stack:
        for name, value in (('SELF', SELF), ('TARGET', TARGET), ('ARGS', ARGS), ('DEV_CONFIG', CONFIG),
                ('task_for', task_for), ('run_for', run_for), ('executable_name', executable_name),
                ('parse_build', parse_build), ('AUDIT_PIN', AUDIT_PIN)):
            stack.enter_context(patch.object(legacy, name, value))
        stack.enter_context(patch.object(json, 'dump', write))
        return legacy.run_owned(run, destination, expected, protected, helpers)


def light(run):
    resources = prepared.SQLRuntimeResources(); q = None; out = dict(state='FAILED_NOT_ACCEPTED')
    try:
        resources.admit(); q = prepared.LiveSQLReader(resources)
        for name in (SELF, TEST, 'tools/p09/signed_durable_build_stream.py'): q.pin(name)
        sys.path.insert(0, str(c.ROOT/'tools/p09/tests'))
        suite = unittest.defaultTestLoader.loadTestsFromName('test_build_current_stored_generation')
        with patch('subprocess.Popen', side_effect=AssertionError('P152_BUILD_LIGHT_CHILD_FORBIDDEN')), \
                patch('subprocess.run', side_effect=AssertionError('P152_BUILD_LIGHT_CHILD_FORBIDDEN')):
            checked = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
        failed = sorted({getattr(t, 'test_case', t).id().split('.')[-1] for t, _ in checked.failures+checked.errors+checked.skipped})
        passed = checked.wasSuccessful() and checked.testsRun == TEST_COUNT and not checked.skipped
        q.finish(); out.update(state='PASS_CURRENT_STORED_BUILD_CONTRACT_ONLY_NOT_COMPILED_RUNTIME_OR_GATE' if passed else 'FAILED_NOT_ACCEPTED',
            contract_tests_run=checked.testsRun, contract_tests_passed=checked.testsRun-len(failed), failed_tests=failed,
            source_closing_exact=True, actual_Cargo_SQL_native_executed=False, product_complete=False, P09_gate='OPEN')
    finally:
        prepared.finish_watcher(resources, out); out['resource_stop_reason'] = resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'): out['state'] = 'FAILED_NOT_ACCEPTED'
        if q is not None: out['IO'] = q.summary(); out['bound_input_pins'] = list(q.reader.snapshots.values())
    destination = prepared.scoped_path(f'implementation/p09/evidence/p09-152-current-stored-build.light-run{run:02}.v1.json', fresh=True)
    with destination.open('x', encoding='utf-8') as stream: json.dump(out, stream, indent=2)
    print(json.dumps({k: out.get(k) for k in ('state', 'contract_tests_run', 'contract_tests_passed', 'failed_tests', 'resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--run', type=int, choices=range(1, 100), required=True)
    parser.add_argument('--mode', choices=('light', 'actual'), required=True); args = parser.parse_args()
    require(c.Path.cwd().resolve() == c.ROOT, 'REPOSITORY_CWD')
    if args.mode == 'light': return light(args.run)
    destination = prepared.scoped_path(f'implementation/p09/evidence/p09-152-current-stored-build.actual-run{args.run:02}.v1.json', fresh=True)
    prepared.require_fresh_output(args.run, {})
    return run_owned(args.run, destination, *load_binding(args.run))


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1:3] == ['--owned-worker', '--task']: raise SystemExit(worker(sys.argv[3]))
    try: raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) else 'P152_BUILD_REDACTED_FAILURE'
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED', error_code=code if re.fullmatch('[A-Za-z0-9_]{1,160}', code) else 'P152_BUILD_REDACTED_FAILURE')))
        raise SystemExit(2) from None
