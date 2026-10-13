"""Fresh P150 executable binding. Build only; no old SQL admission is restamped.

Same current Rust784/original-body restoration/protected history as P150 example
qualification. The original Windows GO/Job/limits/capture/final pins stay intact.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from unittest.mock import patch

import run_signed_durable_example_tests as original
import signed_durable_build_stream as stream
from audit_evidence_io import AuditEvidenceReader
from live_sql_evidence_reader import LiveSQLReader
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher
from sql_owned_execution import scoped_path

c = original.c
SELF = 'tools/p09/build_signed_durable_probe.py'
TEST = 'tools/p09/tests/test_build_signed_durable_probe.py'
STREAM_TEST = 'tools/p09/tests/test_signed_durable_build_stream.py'
ARCHIVES = ('implementation/p09/source-archive/p09-150-pre-build-light-tail-fix-r28/source-preimages.v1.json',
            'implementation/p09/source-archive/p09-150-pre-build-stream-r28/source-preimages.v1.json',
            'implementation/p09/source-archive/p09-150-pre-build-catalog-diagnostic-r28/source-preimages.v1.json',
            'implementation/p09/source-archive/p09-150-pre-runtime-build-profile-r28/source-preimages.v1.json',
            'implementation/p09/source-archive/p09-150-pre-canonical-compiler-suffix-r28/source-preimages.v1.json')
TARGET = original.TARGET
ARGS = ['rustc', '-p', 'hwpx-agent-cli', '--example', 'formula_issuer_product_postgres_probe', '--profile', 'dev']
DEV_CONFIG = tuple(entry.replace('profile.test.', 'profile.dev.', 1) for entry in original.base.CONFIG)
AUDIT_PIN = dict(path='implementation/p09/evidence/p09-150-signed-durable-example.terminal-audit-run01.v1.json',
                 bytes=205503, sha256='7f07ca7443a04fbe2462ed6438fad776df71ba44ad31aaae6c489c539c88db8b')
PASS = 'PASS_CURRENT_DURABLE_PROBE_BUILD_ONLY_NOT_SQL_NATIVE_OR_GATE'
RAW_CAPTURE = original.capture.bounded.BoundedProcessCapture


def require(ok, code): c.require(ok, 'DURABLE_BUILD_'+code)


def task_for(run):
    require(type(run) is int and 1 <= run <= 99, 'RUN_SCOPE')
    return f'p150-durable-probe-build-r{run:02}'


def run_for(task):
    require(isinstance(task, str) and re.fullmatch(r'p150-durable-probe-build-r[0-9]{2}', task), 'TASK_SCOPE')
    run = int(task[-2:]); require(task_for(run) == task, 'TASK_SCOPE'); return run


def executable_name(run):
    task_for(run)
    return f'target/p09-150-signed-durable/build/debug/examples/formula_issuer_product_postgres_probe-p150-r{run:02}.exe'


def parse_build(output, run, *, require_stream=False):
    require(isinstance(output, str) and len(output.encode('utf-8')) <= 32768, 'OUTPUT_BUDGET')
    finished, artifacts, diagnostics, streams = [], [], [], []
    for line in output.splitlines():
        if not line.strip(): continue
        try: item = json.loads(line)
        except json.JSONDecodeError: raise ValueError('DURABLE_BUILD_JSON_INVALID') from None
        require(isinstance(item, dict) and item.get('reason') in
                {'build-finished', 'compiler-artifact', 'compiler-message', 'build-script-executed', 'p150-validated-stream'}, 'MESSAGE_SCOPE')
        if item['reason'] == 'build-finished':
            require(type(item.get('success')) is bool, 'FINISH_SCOPE'); finished.append(item['success'])
        elif item['reason'] == 'compiler-artifact' and item.get('target', {}).get('name') == 'formula_issuer_product_postgres_probe':
            raw = item.get('profile', {})
            profile = {key: raw.get(key) for key in ('opt_level', 'debuginfo', 'debug_assertions', 'overflow_checks', 'test')}
            require(profile == dict(opt_level='1', debuginfo='line-tables-only', debug_assertions=True,
                                    overflow_checks=True, test=False)
                    and profile['debug_assertions'] is True and profile['overflow_checks'] is True
                    and profile['test'] is False, 'ASSERTION_PROFILE_SCOPE')
            name = item.get('executable')
            # Cargo announces its canonical name even when rustc extra-filename
            # emits our run-specific suffix (observed run04, retained as failure).
            # Only these two exact names can bind; execute/hash the fresh suffix,
            # NEVER a canonical/stale or caller-selected file.
            require(isinstance(name,str),'EXECUTABLE_MISSING');path=c.Path(name)
            exact=c.ROOT/executable_name(run)
            canonical=TARGET/'debug/examples/formula_issuer_product_postgres_probe.exe'
            require(path.is_absolute() and path in (exact,canonical),'EXECUTABLE_SCOPE')
            if path==canonical:
                require(require_stream and scoped_path(executable_name(run)).is_file(),'EXACT_FRESH_COMPILER_OUTPUT_REQUIRED')
            artifacts.append(dict(path=executable_name(run),profile=profile,
                Cargo_announcement_kind='canonical_name_with_frozen_driver_suffix' if path==canonical else 'exact_suffix_name'))
        elif item['reason'] == 'compiler-message':
            message = item.get('message', {})
            if message.get('level') in {'error', 'warning'}:
                require(len(diagnostics) < 32, 'DIAGNOSTIC_BUDGET')
                code = (message.get('code') or {}).get('code')
                diagnostics.append(dict(level=message['level'], code=code if isinstance(code, str)
                    and re.fullmatch(r'[A-Za-z_0-9]{1,64}', code) else None))
        elif item['reason'] == 'p150-validated-stream':
            require(set(item) == {'reason','all_records_validated','raw_stdout_bytes','raw_stdout_sha256','messages',
                'maximum_record_bytes','raw_stderr_bytes','stdout_record_buffer_limit','stdout_total_JSON_IO_budget',
                'stderr_total_limit','raw_output_truncated','raw_logs_included'}, 'STREAM_PROTOCOL')
            require(item['all_records_validated'] is True and item['raw_output_truncated'] is False
                and item['raw_logs_included'] is False and item['stdout_record_buffer_limit'] == 32768
                and item['stderr_total_limit'] == 32768 and item['stdout_total_JSON_IO_budget'] == 16*1024*1024
                and re.fullmatch('[0-9a-f]{64}', item['raw_stdout_sha256']), 'STREAM_LIMITS')
            for key, limit in (('raw_stdout_bytes',16*1024*1024),('raw_stderr_bytes',32768),
                               ('messages',2048),('maximum_record_bytes',32768)):
                require(type(item[key]) is int and 0 <= item[key] <= limit, 'STREAM_COUNTS')
            require(item['messages'] >= 2, 'STREAM_COUNTS'); streams.append(item)
    require(finished == [True] and len(artifacts) == 1 and not diagnostics, 'EXACT_CLEAN_BUILD_REQUIRED')
    require(len(streams) == (1 if require_stream else 0), 'STREAM_PROOF_REQUIRED')
    return dict(build_finished_success=True, executable_path=artifacts[0]['path'],
                catalog_profile=artifacts[0]['profile'], diagnostics=diagnostics,
                executable_binding='exact_fresh_frozen_rustc_extra_filename_output',
                Cargo_announcement_kind=artifacts[0]['Cargo_announcement_kind'],
                validated_stream=streams[0] if streams else None)


def worker(task):
    run = run_for(task)
    def selected(args, **kw):
        require(args[1:] == [*ARGS, '--locked', '--offline', '--jobs', '1', '--color=never', '--target-dir', str(TARGET)], 'WORKER_ARGUMENT_SCOPE')
        env = dict(kw['env'])
        require(all(not env.get(k) for k in ('RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'RUSTC_WRAPPER',
                    'RUSTC_WORKSPACE_WRAPPER', 'RUSTC', 'CARGO_BUILD_TARGET')), 'AMBIENT_COMPILER_OVERRIDE')
        for name in ('P150_BLOB_ROOT', 'P150_BLOB_RUN_ID', 'P150_BLOB_MODE'): env.pop(name, None)
        # Cargo rustc --profile test selects a test binary. SQL requires dev/test=false.
        env.update(CARGO_PROFILE_DEV_OPT_LEVEL='0', CARGO_PROFILE_DEV_CODEGEN_UNITS='16', CARGO_INCREMENTAL='0')
        actual = [args[0], *[v for entry in DEV_CONFIG for v in ('--config', entry)],
                  *args[1:], '--message-format=json', '--', '-C', f'extra-filename=-p150-r{run:02}']
        kw['env'] = env
        return stream.run_command(actual, kw, lambda output: parse_build(output, run, require_stream=True))
    with patch.object(c, 'TARGET', TARGET), patch.object(c, 'TASKS', {task: ARGS}), patch.object(subprocess, 'call', selected):
        return c.worker(task)


def load_binding():
    expected, protected = original.load_binding()
    resources = SQLRuntimeResources(); row = {}
    try:
        resources.admit(); q = LiveSQLReader(resources)
        require(q.pin(AUDIT_PIN['path']) == AUDIT_PIN, 'PARENT_AUDIT_DRIFT')
        parent = q.json(AUDIT_PIN['path'])
        require(parent['state'] == 'PASS_CURRENT_DURABLE_ADAPTER_EXAMPLE19_ONLY_NOT_SQL_NATIVE_OR_GATE'
                and parent['current_source_closing_exact'] and parent['example_tests_passed'] == 19
                and parent['driver_contract_tests_passed'] == 12 and parent['protected_executables_exact'] == 50, 'PARENT_NOT_ACCEPTED')
        prior = {p['path']: p for p in parent['bound_input_pins']}
        for name in (original.ROOT_SOURCE, original.PROVIDER_SOURCE, original.BACKEND_SOURCE, original.SELF,
                     'tools/p09/tests/test_signed_durable_example_tests.py'):
            require(q.pin(name) == prior[name], 'CURRENT_PARENT_SOURCE_DRIFT')
        test_exe = parent['compiled_test_artifact']; require(q.pin(test_exe['path']) == test_exe, 'PARENT_EXE_DRIFT')
        protected = [*protected, test_exe]
        require(len(protected) == len({p['path'] for p in protected}) == 51, 'PROTECTED_SCOPE')
        expected[test_exe['path']] = test_exe
        expected[AUDIT_PIN['path']] = AUDIT_PIN
        # Bind every actually imported local helper as well as the preserved parent closure.
        helpers = {SELF, TEST, STREAM_TEST, *ARCHIVES}
        for module in tuple(sys.modules.values()):
            file = getattr(module, '__file__', None)
            if file:
                path = c.Path(file).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix == '.py':
                    helpers.add(path.relative_to(c.ROOT).as_posix())
        for name in sorted(helpers): expected[name] = q.pin(name)
        q.finish(); return expected, protected, sorted(helpers)
    finally: require(finish_watcher(resources, row), 'WATCHER_CLEANUP')


def run_owned(run, destination, expected, protected, helpers):
    task = task_for(run); raw_pins = c.pins; dump = json.dump
    revalidated = False; captures = []; accepted_final = False
    class Capture(original.capture.FullCapture):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw); self.build = None; captures.append(self)
        def communicate(self, timeout):
            output, errors = RAW_CAPTURE.communicate(self, timeout)
            if self.process.returncode == 0:
                self.build = parse_build(output, run, require_stream=True); self.accepted = True
            return output, errors
        def diagnostics(self):
            row=super().diagnostics()
            with self.lock: errors=bytes(self.buffers['stderr']).decode('utf-8',errors='replace')
            row['closed_validation_error_codes']=re.findall(r'(?m)^P150_BUILD_CLOSED_ERROR:(DURABLE_BUILD_[A-Z_]+)\r?$',errors)
            row['closed_Cargo_executable_basenames']=re.findall(r'(?m)^P150_BUILD_CLOSED_BASENAME:(formula_issuer_product_postgres_probe(?:-p150-r[0-9]{2})?\.exe)\r?$',errors)
            row['closed_Cargo_profiles']=[json.loads(x) for x in re.findall(r'(?m)^P150_BUILD_CLOSED_PROFILE:(\{[^\r\n]{1,512}\})\r?$',errors)]
            return row
    def pins(checkpoint=None):
        nonlocal revalidated
        rows = raw_pins(checkpoint); actual = {p['path']: p for p in rows}
        require(all(actual.get(name) == pin for name, pin in expected.items()), 'CURRENT_INPUT_DRIFT')
        if not revalidated:
            resources = SQLRuntimeResources(); state = {}
            try:
                resources.admit(); count = 0; deadline = time.monotonic()+c.POLICY['admission_max_seconds']
                while time.monotonic() < deadline:
                    time.sleep(c.POLICY['sample_seconds']); sample = resources.sample()
                    require(not resources.stop.is_set(), 'POST_HASH_RESOURCE_STOP')
                    count = original.base.BASE_ADMITTED_COUNT(sample, count) if sample['available_ram_percent'] >= 15 else 0
                    if count >= 2: break
                require(count >= 2, 'POST_HASH_STABLE_RESOURCE_WINDOW_REQUIRED'); revalidated = True
            finally: require(finish_watcher(resources, state), 'POST_HASH_WATCHER_CLEANUP')
        return rows
    def write(row, stream, **kw):
        nonlocal accepted_final
        observed = captures[-1] if captures else None
        accepted = row['state'] == 'PASS_SCOPED_NOT_GATE' and observed is not None and observed.accepted
        pin = None
        if accepted:
            reader = AuditEvidenceReader(c.ROOT, lambda: None)
            pin = reader.fresh_pin(executable_name(run)); reader.finish()
        accepted_final = accepted
        if row['state'] == 'PASS_SCOPED_NOT_GATE': row['state'] = PASS if accepted else 'STOPPED_NOT_ACCEPTED'
        row.update(schema_version='hwpx-agent.p09-current-durable-probe-build/v1', run=run,
            current_build_binding_accepted=accepted, executable_pin=pin,
            build_result=observed.build if observed else None, imported_helper_inventory=helpers,
            protected_executables=protected, protected_executables_exact_after=accepted,
            original_root_and_provider_whole_bodies_restored_exact=True, whole_workspace_Rust_input_count=784,
            source_freeze_exact_after=accepted, compile_admission_RAM_percent=15,
            post_hash_stable_admission_revalidated=revalidated, parent_example_audit_pin=AUDIT_PIN,
            original_test_package_profile_config=list(original.base.CONFIG),
            current_dev_package_profile_config=list(DEV_CONFIG), assertions_unchanged=True,
            capture_diagnostics=observed.diagnostics() if observed else None,
            old_SQL_admission_modified=False, current_SQL_admission_qualified=False,
            actual_SQL_or_native_executed=False, product_complete=False, P09_gate='OPEN', PC_freeze_resolved=False)
        return dump(row, stream, **kw)
    with patch.object(c, '__file__', str(c.ROOT/SELF)), patch.object(c, 'TARGET', TARGET), \
            patch.object(c, 'TASKS', {task: ARGS}), patch.object(c, 'SOURCES', list(dict.fromkeys([*c.SOURCES, *expected]))), \
            patch.object(c, 'pins', pins), patch.object(c, 'admitted_count', lambda row, count: original.base.admission_count(original.base.INVENTORY, row, count)), \
            patch.object(original.capture.bounded, 'BoundedProcessCapture', Capture), patch.object(json, 'dump', write):
        result = c.run(task, destination, 600)
    return 0 if accepted_final else result


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--run', type=int, choices=range(1, 100), required=True)
    args = parser.parse_args(); require(c.Path.cwd().resolve() == c.ROOT, 'ROOT_SCOPE')
    destination = scoped_path(f'implementation/p09/evidence/p09-150-durable-probe-build.actual-run{args.run:02}.v1.json', fresh=True)
    scoped_path(executable_name(args.run), fresh=True)
    expected, protected, helpers = load_binding()
    return run_owned(args.run, destination, expected, protected, helpers)


if __name__ == '__main__':
    if len(sys.argv[1:]) == 3 and sys.argv[1:3] == ['--owned-worker', '--task']: raise SystemExit(worker(sys.argv[3]))
    try: raise SystemExit(main())
    except (ValueError, OSError, TypeError, KeyError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch('[A-Z_]+', str(error)) else 'DURABLE_BUILD_OPERATION_NOT_ACCEPTED'
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED', error_code=code))); raise SystemExit(2) from None
