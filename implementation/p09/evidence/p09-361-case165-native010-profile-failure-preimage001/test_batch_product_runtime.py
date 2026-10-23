"""Dispatcher contracts with synthetic IO/Native/Job; no product execution."""
import copy
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

import accept_case112_current_epoch as a
import batch_product_runtime as module


def policy_fixture(*, product=True):
    root = Path('D:/development path/hwpx-agent')
    checks = []
    context = NS(active=False, attempts=0, jobs=0, checkpoint=lambda: checks.append(True))
    policy = module.ProcessPolicy(root, product=product)
    command = [sys.executable, '-B', str(root / module.WORKER['path']),
        '--ready-handle', '123', '--task', module.TASK]
    return NS(root=root, context=context, policy=policy, checks=checks, command=command)


def emit(f, command=None, **changes):
    args = [None, subprocess.list2cmdline(f.command if command is None else command), str(f.root), None]
    for key, value in changes.items():
        args[int(key)] = value
    return f.policy('subprocess.Popen', tuple(args))


def chain_fixture(*, native_code=0):
    f = NS(events=[])
    f.context = NS()
    f.route = NS(checkpoint=lambda: None, context=NS())
    f.epochs = NS(advance=lambda role: f.events.append(('epoch', role)),
        check=lambda **kw: f.events.append('preparation_final'), close=lambda: f.events.append('preparation_closed'))
    f.relay = NS(arm=lambda: f.events.append('handoff_armed'),
        finish_native=lambda actual: f.events.append('native_terminal'))
    f.process = NS(attempts=1, denied=[], arm=lambda actual: f.events.append('process_armed'))
    def Reader(root, checkpoint):
        return NS(snapshots={'source': {}}, bytes_read=3, final_fresh_hashes=1)
    f.Reader = Reader
    batch = NS(begin=lambda r: f.events.append('whole_opening'))
    def native(run):
        f.events.append(('native', run))
        return native_code
    f.context.result = NS(assembled=NS(batch=batch, parent=NS(run_owned=native)))
    f.route.start_closing = lambda: f.events.append('closing_started')
    f.route.finish_whole = lambda r: f.events.append('whole_closing') or {'not_accepted': True}
    def verify(reader, *, load_inputs):
        f.events.append('oracle')
        load_inputs(reader)
        reader.snapshots[module.CANONICAL] = {'path': module.CANONICAL}
        return {}, {'original': True}
    f.route.verify = verify
    f.api = NS(c=NS(ROOT=Path('D:/synthetic')))
    f.inputs = lambda reader, context, api: ({'samples': []}, {}, {}, {}, NS())
    return f


def execute(f):
    with patch.object(module, 'oracle_inputs', f.inputs):
        return module.execute_chain(f.context, f.route, f.relay, f.epochs, f.Reader, f.process,
            f.api, lambda stage: f.events.append(stage))


def pin(name):
    return dict(path=name, bytes=1, sha256='0' * 64)


def qualification_fixture():
    pins = [pin(n) for n in (module.SELF, module.TEST, module.PRIOR['path'], module.POST['path'],
        module.WORKER['path'], module.LAUNCH['path'])]
    tests = dict(tests=1, errors=0, failures=0, skips=0, process_creation_attempts=0,
        cleanup_confirmed=True, source_pins=copy.deepcopy(pins))
    closed = dict(tests=22, errors=0, failures=0, skips=0, process_creation_attempts=0,
        cleanup_confirmed=True, source_pins=[])
    connected = dict(state='PASS_NATIVE010_PRODUCT_DRIVER_CONNECTION_NOT_EXECUTION', mode='connect-only',
        original_parent_execution_attempted=False, process_creation_attempts=0, cleanup_confirmed=True,
        helper_inventory={'Native_count': 64}, construction_fresh_inputs=len(pins),
        construction_final_hashes=len(pins), construction_source_pins=copy.deepcopy(pins))
    row = dict(state='QUALIFIED_NATIVE010_DISPATCH_CODE_AND_CONSTRUCTION_NOT_EXECUTION',
        GO_authorized=False, accepted_count_delta=0, official_accepted_count=158, next_case=165,
        dispatcher_contracts=tests, closing_contracts=closed, actual_connection=connected)
    reader = NS(json=lambda path: copy.deepcopy(row), pin=pin,
        snapshots={module.QUALIFICATION: pin(module.QUALIFICATION)})
    return NS(row=row, reader=reader)


class ModeAndPolicyTests(unittest.TestCase):
    def test_modes_explicit_and_no_retry_or_old_native_flags(self):
        self.assertFalse(module.mode(['--connect-only']))
        self.assertTrue(module.mode(['--run-product']))
        for args in ([], ['--run-product', '--retry'], ['--native009'], ['--connect-only', '--run-product']):
            with self.assertRaises(ValueError):
                module.mode(args)

    def test_connect_only_permanently_denies_process_creation(self):
        f = policy_fixture(product=False)
        with self.assertRaises(ValueError):
            emit(f)
        with self.assertRaises(ValueError):
            f.policy.arm(f.context)
        self.assertEqual(f.checks, [])

    def test_before_arm_and_second_creation_never_allowed(self):
        f = policy_fixture()
        with self.assertRaises(ValueError):
            emit(f)
        with self.assertRaises(ValueError):
            f.policy.arm(f.context)
        f = policy_fixture()
        f.policy.arm(f.context)
        emit(f)
        with self.assertRaises(ValueError):
            emit(f)
        self.assertEqual(f.policy.attempts, 1)
        self.assertEqual(f.checks, [True])

    def test_exact_windows_command_and_actual_frame_checkpoint(self):
        f = policy_fixture()
        f.policy.arm(f.context)
        emit(f)
        self.assertEqual(f.policy.attempts, 1)
        self.assertEqual(f.checks, [True])
        self.assertEqual(f.policy.denied, [])

    def test_probe_old_entry_or_other_task_denied_before_checkpoint(self):
        for change in ('probe', 'old', 'task'):
            f = policy_fixture()
            f.policy.arm(f.context)
            command = list(f.command)
            if change == 'probe':
                command.insert(3, '--probe-no-go')
            elif change == 'old':
                command[2] = str(f.root / 'tools/p09/batch_worker_launch.py')
            else:
                command[-1] = 'case165-current-r009-tests'
            with self.assertRaises(ValueError):
                emit(f, command)
            self.assertEqual(f.checks, [])

    def test_noncanonical_handles_root_or_environment_rejected(self):
        for handle in ('0', '001', str(2**64), '123 x'):
            f = policy_fixture()
            f.policy.arm(f.context)
            command = list(f.command)
            command[4] = handle
            with self.assertRaises(ValueError):
                emit(f, command)
        for changes in ({'0': 'other.exe'}, {'2': 'D:/other'}, {'3': {'ENV': 'value'}}):
            f = policy_fixture()
            f.policy.arm(f.context)
            with self.assertRaises(ValueError):
                emit(f, **changes)
            self.assertEqual(f.checks, [])

    def test_original_frame_guard_error_preserved_and_sticky(self):
        f = policy_fixture()
        error = ValueError('STOP_ORIGINAL_FRAME_CPU')
        def fail():
            raise error
        f.context.checkpoint = fail
        f.policy.arm(f.context)
        with self.assertRaises(ValueError) as caught:
            emit(f)
        self.assertIs(caught.exception, error)
        self.assertEqual(f.policy.attempts, 0)
        f.context.checkpoint = lambda: None
        with self.assertRaises(ValueError):
            emit(f)

    def test_shell_and_exec_always_denied_nonprocess_untouched(self):
        for event in ('os.system', 'os.startfile', 'os.exec', 'os.posix_spawn', 'os.fork'):
            f = policy_fixture()
            f.policy.arm(f.context)
            with self.assertRaises(ValueError):
                f.policy(event, ())
        f.policy('open', ())


class ChainTests(unittest.TestCase):
    def test_exact_original_execution_order_and_one_native_call(self):
        f = chain_fixture()
        result = execute(f)
        events = f.events
        self.assertLess(events.index('whole_opening'), events.index('preparation_closed'))
        self.assertLess(events.index('preparation_closed'), events.index('handoff_armed'))
        self.assertLess(events.index('handoff_armed'), events.index(('native', 1)))
        self.assertLess(events.index('native_terminal'), events.index('closing_started'))
        self.assertLess(events.index('whole_closing'), events.index('oracle'))
        self.assertEqual(events.count(('native', 1)), 1)
        self.assertEqual(result['original_oracle_result'], ({}, {'original': True}))

    def test_native_failure_never_starts_closing_or_oracle(self):
        f = chain_fixture(native_code=2)
        with self.assertRaisesRegex(ValueError, 'NO_AUTOMATIC_RETRY'):
            execute(f)
        self.assertIn('native_terminal', f.events)
        self.assertNotIn('closing_started', f.events)
        self.assertNotIn('oracle', f.events)

    def test_original_native_exception_keeps_terminal_handoff_and_no_retry(self):
        f = chain_fixture()
        error = ValueError('ORIGINAL_NATIVE_SETUP_FAILURE')
        def fail(run):
            raise error
        f.context.result.assembled.parent.run_owned = fail
        with self.assertRaises(ValueError) as caught:
            execute(f)
        self.assertIs(caught.exception, error)
        self.assertIn('native_terminal', f.events)
        self.assertNotIn('closing_started', f.events)

    def test_whole_opening_failure_never_arms_product(self):
        f = chain_fixture()
        def fail(reader):
            raise ValueError('ORIGINAL_WHOLE_INPUT_CHANGED')
        f.context.result.assembled.batch.begin = fail
        with self.assertRaises(ValueError):
            execute(f)
        self.assertNotIn('process_armed', f.events)
        self.assertNotIn(('native', 1), f.events)

    def test_whole_closing_or_oracle_failure_never_return_success(self):
        for name in ('finish_whole', 'verify'):
            f = chain_fixture()
            def fail(*args, **kwargs):
                raise ValueError('ORIGINAL_POST_NATIVE_FAILURE')
            setattr(f.route, name, fail)
            with self.assertRaises(ValueError):
                execute(f)
            self.assertEqual(f.events.count(('native', 1)), 1)

    def test_cleanup_continues_after_individual_restore_failure(self):
        calls = []
        def fail():
            calls.append('failed')
            raise ValueError('ORIGINAL_RESTORE_ERROR')
        self.assertFalse(module.close_all((fail, lambda: calls.append('second'), lambda: calls.append('third'))))
        self.assertEqual(calls, ['failed', 'second', 'third'])


class QualificationTests(unittest.TestCase):
    def test_current_code_and_actual_nonexecuting_construction_required(self):
        f = qualification_fixture()
        self.assertEqual(module.admit_qualification(f.reader, a), pin(module.QUALIFICATION))

    def test_old_closing_contracts_or_skips_or_boolean_counts_rejected(self):
        for modify in (lambda r: r['closing_contracts'].update(tests=19),
                       lambda r: r['dispatcher_contracts'].update(skips=1),
                       lambda r: r['dispatcher_contracts'].update(errors=False),
                       lambda r: r['actual_connection'].update(construction_fresh_inputs=True)):
            f = qualification_fixture()
            modify(f.row)
            with self.assertRaises(ValueError):
                module.admit_qualification(f.reader, a)

    def test_missing_or_changed_current_source_rejected(self):
        f = qualification_fixture()
        f.reader.pin = lambda path: dict(pin(path), bytes=2)
        with self.assertRaises(ValueError):
            module.admit_qualification(f.reader, a)
        f = qualification_fixture()
        f.row['actual_connection']['construction_source_pins'].pop()
        with self.assertRaises(ValueError):
            module.admit_qualification(f.reader, a)

    def test_qualification_cannot_grant_go_or_contain_actual_execution(self):
        for modify in (lambda r: r.update(GO_authorized=True),
                       lambda r: r['actual_connection'].update(original_parent_execution_attempted=True)):
            f = qualification_fixture()
            modify(f.row)
            with self.assertRaises(ValueError):
                module.admit_qualification(f.reader, a)


class OracleInputTests(unittest.TestCase):
    def fixture(self):
        records = {'listing': {}, 'body': {}, 'fresh': {}}
        row, fresh, config, calls = {}, {}, object(), []
        ctx = NS(INDEX=165, BEFORE=158, CASE='case165')
        def context(actual):
            calls.append(actual)
            return ctx
        connected = NS(result=NS(assembled=NS(checker=NS(environment={'context': context}),
            built=NS(window=NS(M=NS(base=NS(CONFIG=config)))))),
            connected=NS(core={'step': {'case': 'case165'}}))
        checkpoint = lambda: None
        reader = NS(json=lambda path: row, checkpoint=checkpoint)
        api = NS(scope=NS(LIST_PIN=pin('listing')), BODY_PIN=pin('body'), FRESH_PIN=pin('fresh'),
            read_exact=lambda q, p: records[p['path']],
            packed=NS(unpack=lambda value, check: fresh if value is records['fresh'] and check is checkpoint else None))
        return NS(reader=reader, context=connected, api=api, row=row, fresh=fresh, records=records,
            config=config, calls=calls, ctx=ctx)

    def test_exact_original_inputs_and_actual_context_factory_without_rewriting(self):
        f = self.fixture()
        result = module.oracle_inputs(f.reader, f.context, f.api)
        for actual, expected in zip(result, (f.row, f.records['listing'], f.records['body'], f.fresh, f.ctx)):
            self.assertIs(actual, expected)
        self.assertEqual(f.calls, [f.config])

    def test_context_case_or_cursor_mismatch_denied(self):
        for field, value in (('INDEX', 164), ('BEFORE', 157), ('CASE', 'other')):
            f = self.fixture()
            setattr(f.ctx, field, value)
            with self.assertRaisesRegex(ValueError, 'CURRENT_ORACLE_CONTEXT'):
                module.oracle_inputs(f.reader, f.context, f.api)


class FailureObservationTests(unittest.TestCase):
    def fixture(self, row=None):
        original = dict(state='DEFERRED_NOT_STARTED', stop_reason='STOP_ORIGINAL_CPU',
            cleanup_confirmed=True, owned_tree_empty=True, worker_created=False, job_assigned=False,
            source_frame=None, product_body_observed=False) if row is None else row
        guard = NS(acquire=lambda: None, check=lambda **kw: None, cleanup=None, closes=0)
        def close():
            guard.closes += 1
            guard.cleanup = True
        guard.close = close
        reader = NS(json=lambda path: original, finish=lambda: None,
            snapshots={module.CANONICAL: pin(module.CANONICAL)})
        return NS(row=original, guard=guard, reader=reader,
            read=lambda root, check: reader, factory=lambda role: guard)

    def test_original_pre_frame_failure_and_cleanup_evidence_observed(self):
        f = self.fixture()
        result = module.observe_failure(Path('D:/synthetic'), f.factory, f.read)
        self.assertTrue(result['original_cleanup_confirmed'])
        self.assertEqual(result['original_stop_reason'], 'STOP_ORIGINAL_CPU')
        self.assertEqual(result['original_Frame_boundaries'], 0)
        self.assertEqual(f.guard.closes, 1)

    def test_unknown_or_unreleased_cleanup_never_promoted(self):
        f = self.fixture()
        f.row['cleanup_confirmed'] = False
        self.assertFalse(module.observe_failure(Path('D:/synthetic'), f.factory, f.read)['original_cleanup_confirmed'])
        f = self.fixture()
        f.row['worker_created'] = True
        self.assertFalse(module.observe_failure(Path('D:/synthetic'), f.factory, f.read)['original_cleanup_confirmed'])

    def test_missing_receipt_still_closes_observer_and_preserves_error(self):
        f = self.fixture()
        error = FileNotFoundError('fixture')
        def fail(path):
            raise error
        f.reader.json = fail
        with self.assertRaises(FileNotFoundError) as caught:
            module.observe_failure(Path('D:/synthetic'), f.factory, f.read)
        self.assertIs(caught.exception, error)
        self.assertEqual(f.guard.closes, 1)

    def test_arbitrary_failure_text_not_echoed(self):
        f = self.fixture()
        f.row['stop_reason'] = 'not public failure detail'
        result = module.observe_failure(Path('D:/synthetic'), f.factory, f.read)
        self.assertNotIn('original_stop_reason', result)


if __name__ == '__main__':
    unittest.main()
