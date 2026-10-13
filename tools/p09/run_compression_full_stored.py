"""All original249 tests, bounded terse output, same existing full-suite1200s policy.

No filtering/ignoring/check removal. Current compiled249 with exact dependency
profile/source must qualify first. Captured libtest output prevents successful
receipt/panic diagnostics from overflowing the unchanged bounded transport.
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

import run_compression_dependency_signed_tests as candidate
from sql_owned_execution import scoped_path
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher
from live_sql_evidence_reader import LiveSQLReader

c = candidate.c
bounded = candidate.signed.bounded
cost = candidate.signed.previous
SELF = 'tools/p09/run_compression_full_stored.py'
TEST = 'tools/p09/tests/test_compression_full_stored.py'
TASK = 'compression-full-stored-tests'
ARGS = cost.original.ARGS
MAXIMUM_SECONDS = 1200
VARIANT = 'r20-compression-profile-exact-full249-captured-terse-no-filter'
ARCHIVE = 'implementation/p09/source-archive/p09-149-pre-compression-full-capture-r20/helper-preimages.v1.json'
FAILED = {'path':'implementation/p09/evidence/p09-149-compression-full-stored.actual-run01.v1.json',
    'bytes':3607741,'sha256':'677ef24e932a3f48690a6b4818e41f2753b977206b904f649fa22df3b89fd774'}
CAPTURE_CODES = {
    'live_progress_output_limit':'FULL_CAPTURE_OUTPUT_LIMIT',
    'live_progress_marker_scope':'FULL_CAPTURE_MARKER_SCOPE',
    'live_progress_marker_incomplete':'FULL_CAPTURE_MARKER_INCOMPLETE',
    'owned_pipe_read_failed':'FULL_CAPTURE_PIPE_READ_FAILED',
    'owned_pipe_cleanup_timeout':'FULL_CAPTURE_CLEANUP_TIMEOUT',
}


def capture_code(error):
    return CAPTURE_CODES.get(error, 'FULL_CAPTURE_UNCLASSIFIED') if error else None


class FullCapture(bounded.BoundedProcessCapture):
    def __init__(self, *args, **kwargs):
        self.accepted = False
        self.received_bytes = {'stdout':0, 'stderr':0}
        super().__init__(*args, **kwargs)
        c.require(self.output_limit == bounded.LIMIT == 32768, 'FULL_CAPTURE_ORIGINAL_STREAM_LIMIT')

    def _accept(self, name, chunk):
        with self.lock:
            self.received_bytes[name] += len(chunk)
        super()._accept(name, chunk)

    def diagnostics(self):
        with self.lock:
            return {'buffered_bytes':{n:len(b) for n,b in self.buffers.items()},
                'received_bytes':dict(self.received_bytes), 'error_code':capture_code(self.error),
                'per_stream_limit_bytes':self.output_limit, 'raw_log_content_included':False}

    def progress(self):
        try:
            return super().progress()
        except ValueError:
            # Persist only a closed allowlist code; never exception/log text.
            with self.lock:
                code = capture_code(self.error)
            raise ValueError(code or 'FULL_CAPTURE_UNCLASSIFIED') from None

    def communicate(self, timeout):
        output, errors = super().communicate(timeout)
        if self.process.returncode == 0:
            validate_output(output)
            c.require('P149_SIGNED_COST:' not in errors and 'P120_ORIGINAL_CORPUS_RECEIPT:' not in errors
                and 'P121_CHANGED_CORPUS_RECEIPT:' not in errors, 'FULL_CAPTURE_SUCCESS_OUTPUT_NOT_CAPTURED')
            self.accepted = True
        return output, errors


def require_scope(seconds):
    c.require(type(seconds) is int and seconds == MAXIMUM_SECONDS, 'COMPRESSION_FULL_ORIGINAL1200_SCOPE')
    candidate.config_contract(candidate.CONFIG)


def validate_output(output):
    c.require(isinstance(output, str) and len(output.encode()) <= bounded.LIMIT, 'COMPRESSION_FULL_OUTPUT_LIMIT')
    running = re.findall(r'(?m)^running ([0-9]+) tests\r?$', output)
    summaries = re.findall(r'(?m)^test result: ok\. ([0-9]+) passed; ([0-9]+) failed; ([0-9]+) ignored; ([0-9]+) measured; ([0-9]+) filtered out;', output)
    c.require(running == ['249'] and summaries == [('249', '0', '0', '0', '0')], 'COMPRESSION_FULL_EXACT_COMPLETE_RESULT_REQUIRED')


def load_binding(inventory_run):
    require_scope(MAXIMUM_SECONDS)
    expected, names, modules = candidate.load_binding(candidate.PROFILE, inventory_run)
    resources = SQLRuntimeResources(); resources.admit(); q = LiveSQLReader(resources)
    try:
        c.require(q.pin(FAILED['path']) == FAILED, 'FULL_CAPTURE_FAILED_EXECUTION_DRIFT')
        failed = q.json(FAILED['path']); archive = q.json(ARCHIVE)
        c.require(failed['state'] == 'STOPPED_NOT_ACCEPTED' and failed['stop_reason'] == 'OWNED_RUNNER_FAILURE'
            and failed['full249_current_qualified'] is False and failed['signed16_current_qualified'] is False
            and failed['cleanup_confirmed'] and failed['owned_tree_empty']
            and failed['job_final']['active_processes'] == 0 and archive['failed_execution_pin'] == FAILED,
            'FULL_CAPTURE_PREVIOUS_FAILURE_SCOPE')
        frozen = {p['path']:p for p in failed['source_freeze']}; seen = set()
        for item in archive['files']:
            name = item['path']; raw = base64.b64decode(item['base64'], validate=True)
            pin = {k:item[k] for k in ('path','bytes','sha256')}
            c.require(name in (SELF,TEST) and name not in seen and pin == frozen[name]
                and len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'],
                'FULL_CAPTURE_PREVIOUS_HELPER_PREIMAGE_DRIFT')
            seen.add(name)
        c.require(seen == {SELF,TEST}, 'FULL_CAPTURE_PREVIOUS_HELPER_SCOPE')
        for name in (ARCHIVE,FAILED['path']): expected[name] = q.pin(name)
        for name in (SELF, TEST): expected[name] = q.pin(name)
        q.finish()
        return expected, names, modules
    finally:
        c.require(finish_watcher(resources, {}), 'STOP_BINDING_WATCHER_CLEANUP_FAILED')


def worker():
    require_scope(MAXIMUM_SECONDS); call = subprocess.call
    def selected(args, **kwargs):
        expected = [*ARGS, '--locked', '--offline', '--jobs', '1', '--color=never',
            '--target-dir', str(c.TARGET), '--', '--test-threads=1']
        c.require(args[1:] == expected and kwargs.get('cwd') == c.ROOT and kwargs.get('stdin') == subprocess.DEVNULL,
            'COMPRESSION_FULL_WORKER_NO_FILTER_REQUIRED')
        env = kwargs['env']
        c.require(all(env.get(k) == v for k, v in {'CARGO_BUILD_JOBS':'1','CARGO_PROFILE_TEST_OPT_LEVEL':'0',
            'CARGO_PROFILE_TEST_DEBUG_ASSERTIONS':'true','CARGO_PROFILE_TEST_OVERFLOW_CHECKS':'true',
            'CARGO_PROFILE_TEST_CODEGEN_UNITS':'16','RUST_TEST_THREADS':'1','RUSTUP_AUTO_INSTALL':'0'}.items()),
            'COMPRESSION_FULL_WORKER_CHECKS_REQUIRED')
        config = [v for e in candidate.CONFIG for v in ('--config', e)]
        # An inherited environment must not silently turn capture off.
        kwargs['env'] = dict(env, RUST_TEST_NOCAPTURE='0')
        return call([args[0], *config, *args[1:], '--format=terse'], **kwargs)
    with patch.object(c, 'TASKS', {TASK:ARGS}), patch.object(subprocess, 'call', selected): return c.worker(TASK)


def run_owned(destination, expected, names, modules):
    require_scope(MAXIMUM_SECONDS); original_pins = c.pins; dump = json.dump; captures = []
    cost.original.select_names(names)
    c.require(len(modules) == 59, 'COMPRESSION_FULL_COMPLETE_MODULES_REQUIRED')
    class Capture(FullCapture):
        def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs); self.accepted=False; captures.append(self)
    def pins(checkpoint=None):
        actual=original_pins(checkpoint); current={p['path']:p for p in actual}
        c.require(all(current.get(n)==p for n,p in expected.items()), 'COMPRESSION_FULL_FRESH_INPUT_DRIFT'); return actual
    def write(row, stream, **kwargs):
        capture=captures[-1] if captures else None; accepted=bool(capture and capture.accepted)
        if row['state']=='PASS_SCOPED_NOT_GATE' and not accepted:
            row.update(state='STOPPED_NOT_ACCEPTED', stop_reason='COMPRESSION_FULL_COMPLETE_RESULT_MISSING')
        passed=row['state']=='PASS_SCOPED_NOT_GATE' and accepted
        row.update(source_variant=VARIANT, source_test_names=list(names), source_module_instances=list(modules),
            test_package_profile_config=list(candidate.CONFIG), selected_test_names=list(names),
            expected_test_count=249, tests_passed=249 if passed else None, full249_current_qualified=passed,
            signed16_current_qualified=passed, signed_original_test_name=cost.original.NAME,
            signed16_qualification_basis='exact_current_compiled249_unfiltered_all249_passed_original_assertions_retained',
            signed_stage_cost=None, signed_stage_diagnostics_collected=False,
            capture_diagnostics=capture.diagnostics() if capture else None, previous_failed_execution_pin=FAILED,
            execution_mode='all_original249_no_filter_no_ignore_libtest_captured_terse_output',
            original_test_bodies_or_product_sources_changed=False, original_owned_resource_policy_changed=False,
            output_verbosity_only_changed=True, raw_logs_printed_or_saved=False,
            PC_freeze_resolved=False, product_complete=False, P09_gate='OPEN')
        return dump(row, stream, **kwargs)
    with patch.object(c, '__file__', str(c.ROOT/SELF)), patch.object(c, 'TASKS', {TASK:ARGS}), \
            patch.object(c, 'SOURCES', list(dict.fromkeys([*c.SOURCES,*expected]))), patch.object(c, 'pins', pins), \
            patch.object(bounded, 'BoundedProcessCapture', Capture), patch.object(json, 'dump', write):
        return c.run(TASK, destination, MAXIMUM_SECONDS)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--run', type=int, choices=range(1,100), required=True)
    parser.add_argument('--inventory-run', type=int, choices=range(1,100), default=1); parser.add_argument('--light', action='store_true')
    args=parser.parse_args(); require_scope(MAXIMUM_SECONDS)
    c.require(c.Path.cwd().resolve()==c.ROOT, 'COMPRESSION_FULL_ROOT_SCOPE')
    kind='light' if args.light else 'actual'
    destination=scoped_path(f'implementation/p09/evidence/p09-149-compression-full-stored.{kind}-run{args.run:02}.v1.json', fresh=True)
    if not args.light: return run_owned(destination, *load_binding(args.inventory_run))
    from tests.test_compression_full_stored import CompressionFullStoredTests
    resources=SQLRuntimeResources(); resources.admit(); q=LiveSQLReader(resources); row={}
    try:
        freeze=[q.pin(n) for n in (SELF,TEST,candidate.SELF,candidate.TEST)]
        with patch('subprocess.Popen', side_effect=AssertionError('FULL_LIGHT_CHILD_FORBIDDEN')), \
                patch('subprocess.run', side_effect=AssertionError('FULL_LIGHT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start', side_effect=AssertionError('FULL_LIGHT_THREAD_FORBIDDEN')):
            result=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(CompressionFullStoredTests))
        failed=sorted({t.id().split('.')[-1] for t,_ in result.failures+result.errors+result.skipped})
        passed=result.testsRun==13 and result.wasSuccessful() and not result.skipped
        q.finish(); row.update(state='PASS_FULL249_CAPTURED_TERSE_CONTRACT_ONLY_NOT_RUNTIME_OR_GATE' if passed else 'FAILED_NOT_ACCEPTED',
            tests_run=result.testsRun, tests_passed=result.testsRun-len(failed), failed_tests=failed,
            source_freeze=freeze, source_closing_exact=True, Cargo_SQL_native_executed=False,
            product_complete=False,P09_gate='OPEN', IO=q.summary())
    finally: row['resource_stop']=resources.reason; finish_watcher(resources,row)
    c.require(row['resource_stop'] is None and row['resource_watcher_cleanup_confirmed'], 'COMPRESSION_FULL_LIGHT_RESOURCE_STOP')
    with destination.open('x',encoding='utf-8') as stream: json.dump(row,stream,indent=2)
    print(json.dumps({k:row[k] for k in ('state','tests_run','tests_passed','failed_tests')})); return 0 if passed else 2


if __name__=='__main__':
    if sys.argv[1:]==['--owned-worker','--task',TASK]: raise SystemExit(worker())
    try: raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch(r'[A-Z_]+',str(error)) else 'COMPRESSION_FULL_OPERATION_FAILED'
        print(json.dumps({'state':'FAILED_NOT_ACCEPTED','error_code':code})); raise SystemExit(2) from None
