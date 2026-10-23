"""Original entry/launcher bodies with synthetic process/event/worker only."""
import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
from types import FunctionType, SimpleNamespace as NS
import unittest
from unittest.mock import patch

import batch_product_worker as worker
import batch_product_launch as launch
import runtime_envelope_namespace_bundle_v1 as loader
import worker_readiness_v1 as protocol
import worker_readiness_connection_v1 as connection
import strict_product_window_v1 as window
from tools.p09.tests.test_native009_worker_launch_v1 import Clock, Event, Capture

ROOT = WORKER_PIN = None


def worker_fixture(*, prepare_error=None):
    f = NS(prepares=[], executed=[], events=[], errors=io.StringIO())
    def prepare(root, *, package):
        f.prepares.append((root, package))
        if prepare_error is not None:
            raise prepare_error
        def execute(task):
            f.executed.append((task, sys.stdin.readline()))
            if f.executed[-1][1] != 'P149_GO\n':
                raise ValueError('WORKER_NOT_AUTHORIZED')
            return 0
        f.linked = NS(execute=execute, state=NS(attempts=0, calls=0), policy=NS(restored=True),
            original_worker=execute, graph=NS(binding=NS(descriptors=lambda: [None] * 162)))
        class ChildEvent:
            def __init__(self, handle):
                self.handle, self.signals, self.closed = handle, 0, False
                f.events.append(self)
            def signal_and_close(self):
                self.signals += 1
                self.close()
            def close(self):
                self.closed = True
        return f.linked, NS(WindowsEvent=ChildEvent, ReadyReader=protocol.ReadyReader)
    def load(root, pins, reuse):
        libraries, proof = loader.load(root, pins, reuse)
        if hasattr(libraries, 'batch_worker_launch'):
            common = NS(**{**vars(libraries.batch_worker_launch), 'prepare':prepare})
            package = NS(**{**vars(libraries.batch_zlib_runtime),
                'terminal_evidence':lambda linked, row: dict(row, fixture_preparation_only=True)})
            libraries = NS(batch_worker_launch=common, batch_zlib_runtime=package)
        return libraries, proof
    f.api = worker.worker_api(ROOT, NS(load=load))
    return f


def run_worker(f, text, *, probe):
    argv = ['--ready-handle', '123', '--task', worker.TASK]
    with patch.object(sys, 'stdin', io.StringIO(text)), contextlib.redirect_stderr(f.errors):
        return worker.run(f.api, argv, probe=probe)


def launch_fixture(*, probe=False, owned=lambda process: True, fail_reset=False):
    common_lib, _ = loader.load(ROOT, [worker.COMMON], {})
    api = launch.launch_api(ROOT, loader, common_lib.batch_worker_launch, probe=probe)
    clock = Clock()
    event = Event(clock, fail_reset)
    pipe = io.BytesIO()
    process = NS(stdin=pipe, pid=123, poll=lambda: None)
    calls = []
    def factory(*args, **kwargs):
        calls.append((args, kwargs))
        return process
    binding = api.connect(ROOT, dict(WORKER_PIN), window, protocol, connection, factory, Capture,
        subprocess, owned, lambda: None, event_factory=lambda: event, clock=clock)
    argv = [sys.executable, str(ROOT / 'tools/p09/current_queue_successor_runtime.py'),
        '--owned-worker', '--task', worker.TASK]
    options = dict(cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW)
    return NS(api=api, binding=binding, argv=argv, options=options, process=process,
        calls=calls, clock=clock, event=event, pipe=pipe)


class EntryTests(unittest.TestCase):
    def test_original_main_execute_and_argument_code_preserved(self):
        f = worker_fixture()
        original_lib, _ = loader.load(ROOT, [f.api.common.ENTRY], {})
        original = original_lib.native009_worker_entry_v1
        for name in ('main', 'execute', 'arguments', 'read'):
            self.assertEqual(getattr(f.api, name).__code__, getattr(original, name).__code__)
        self.assertFalse(f.api.execution_authorization_granted)

    def test_actual_eof_runs_original_closed_terminal_not_product(self):
        f = worker_fixture()
        self.assertEqual(run_worker(f, '', probe=True), 1)
        row = json.loads(f.errors.getvalue())
        self.assertEqual(row['terminal'], 'WORKER_NOT_AUTHORIZED')
        self.assertEqual(row['task'], worker.TASK)
        self.assertEqual(row['separate_product_entry'], worker.SELF)
        self.assertFalse(row['actual_product_or_Native_or_acceptance_qualified'])
        self.assertEqual(f.executed, [(worker.TASK, '')])
        self.assertTrue(f.events[0].closed)
        self.assertEqual(f.events[0].signals, 1)

    def test_probe_rejects_real_go_instead_of_faking_eof(self):
        f = worker_fixture()
        self.assertEqual(run_worker(f, 'P149_GO\n', probe=True), 1)
        self.assertEqual(f.executed, [])
        self.assertEqual(json.loads(f.errors.getvalue())['terminal'], 'NATIVE009_WORKER_EXECUTION_FAILED')
        self.assertTrue(f.events[0].closed)

    def test_product_mode_retains_real_original_read_and_restores_stdin(self):
        f = worker_fixture()
        before_argv, before_stdin = sys.argv, sys.stdin
        self.assertEqual(run_worker(f, 'P149_GO\n', probe=False), 0)
        self.assertEqual(f.executed, [(worker.TASK, 'P149_GO\n')])
        self.assertIs(sys.argv, before_argv)
        self.assertIs(sys.stdin, before_stdin)
        self.assertTrue(f.events[0].closed)

    def test_closed_args_fail_before_preparation(self):
        for args in ([], ['--zlib'], ['--ready-handle', '0', '--task', worker.TASK],
                     ['--ready-handle', '123', '--task', 'case165-current-r009-tests']):
            f = worker_fixture()
            with self.assertRaises(ValueError):
                worker.run(f.api, args, probe=False)
            self.assertEqual(f.prepares, [])

    def test_failed_preparation_cannot_retry(self):
        error = ValueError('ORIGINAL_CHILD_PREPARATION_FAILURE')
        f = worker_fixture(prepare_error=error)
        with self.assertRaises(ValueError) as caught:
            f.api.prepare(ROOT)
        self.assertIs(caught.exception, error)
        with self.assertRaisesRegex(ValueError, 'NO_RETRY'):
            f.api.prepare(ROOT)
        self.assertEqual(len(f.prepares), 1)

    def test_old_diagnostic_zlib_gate_not_relaxed(self):
        f = worker_fixture()
        with self.assertRaisesRegex(ValueError, 'REQUIRES_NO_GO_PROBE'):
            f.api.common.preparation_profile(False, ['--zlib'])

    def test_probe_process_denial_covers_shell_and_exec(self):
        for event in ('subprocess.Popen', 'os.system', 'os.startfile', 'os.exec', 'os.posix_spawn', 'os.fork'):
            with self.assertRaisesRegex(ValueError, 'PROBE_PROCESS_DENIED'):
                worker.deny_probe_process(event, ())
        worker.deny_probe_process('open', ())


class LaunchTests(unittest.TestCase):
    def test_new_product_command_and_original_event_inheritance(self):
        f = launch_fixture()
        self.assertIs(f.binding.Popen(f.argv, **f.options), f.process)
        argv = f.calls[0][0][0]
        self.assertEqual(argv, [sys.executable, '-B', str(ROOT / worker.SELF),
            '--ready-handle', '123', '--task', worker.TASK])
        self.assertEqual(f.calls[0][1]['startupinfo'].lpAttributeList, {'handle_list': [123]})
        self.assertTrue(f.calls[0][1]['close_fds'])
        self.assertEqual(f.event.flags, [True, False])
        f.process.stdin.close()

    def test_probe_command_is_separate_and_not_zlib_diagnostic_flag_removal(self):
        f = launch_fixture(probe=True)
        f.binding.Popen(f.argv, **f.options)
        self.assertEqual(f.calls[0][0][0][3], '--probe-no-go')
        self.assertNotIn('--zlib', f.calls[0][0][0])
        f.process.stdin.close()

    def test_same_owned_job_readiness_and_original_strict10_retained(self):
        f = launch_fixture()
        f.binding.Popen(f.argv, **f.options)
        self.assertIsNone(f.binding.state.started)
        f.process.stdin.write(protocol.GO)
        f.process.stdin.flush()
        self.assertEqual(f.pipe.getvalue(), protocol.GO)
        self.assertTrue(f.binding.state.diagnostics()['worker_readiness']['readiness_confirmed'])
        cap = f.binding.Capture(f.process)
        f.clock.value += 10
        with self.assertRaisesRegex(ValueError, 'STOP_STRICT_PRODUCT_WINDOW'):
            cap.communicate(1)

    def test_wrong_job_or_inheritance_restore_denies_go(self):
        for options in (dict(owned=lambda process: False), dict(fail_reset=True)):
            f = launch_fixture(**options)
            f.binding.Popen(f.argv, **f.options)
            with self.assertRaises(ValueError):
                f.process.stdin.write(protocol.GO)
            self.assertEqual(f.pipe.getvalue(), b'')
            self.assertEqual(f.binding.state.go_writes, 0)
            f.process.stdin.close()

    def test_old_entry_pin_and_changed_hash_fail_before_factory(self):
        f = launch_fixture()
        for pin in (dict(WORKER_PIN, path=worker.COMMON['path']), dict(WORKER_PIN, sha256='0' * 64)):
            with self.assertRaises(ValueError):
                f.api.source(ROOT, pin)
        self.assertEqual(f.calls, [])

    def test_other_parent_commands_and_options_cannot_spawn(self):
        for index, value in ((1, 'other.py'), (4, 'case165-current-r008-tests')):
            f = launch_fixture()
            f.argv[index] = value
            with self.assertRaises(ValueError):
                f.binding.Popen(f.argv, **f.options)
            self.assertEqual(f.calls, [])
        f = launch_fixture()
        with self.assertRaises(ValueError):
            f.binding.Popen(f.argv, **dict(f.options, shell=True))
        self.assertEqual(f.calls, [])

    def test_parent_api_keeps_body_and_changes_only_explicit_private_dependencies(self):
        def connect():
            return WORKER
        original = FunctionType(connect.__code__, dict(connect.__globals__, WORKER=worker.COMMON['path']))
        entry = NS(WORKER=worker.COMMON['path'], connect=original)
        original_loader = NS(load=lambda *args: (NS(), []))
        parent = NS(connect_package=lambda: NS(loader=original_loader))
        selected_entry, selected_parent = launch.parent_apis(entry, parent, probe=False)
        self.assertIs(selected_entry.connect.__code__, original.__code__)
        self.assertIs(selected_entry.connect.__closure__, original.__closure__)
        self.assertEqual(selected_entry.connect(), worker.SELF)
        self.assertEqual(original(), worker.COMMON['path'])
        self.assertIsNot(selected_parent.connect_package().loader, original_loader)


if __name__ == '__main__':
    unittest.main()
