"""Affected contracts only; no real Native/model result promoted to acceptance."""
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import prepared_bookmark_native631 as subject
import prepared_bookmark631_drain as drain
import prepared_bookmark631_evidence as evidence
import prepared_bookmark631_sections as sections
import run_prepared_bookmark_native631 as entry


def frame(step='prepare_slot', **changes):
    value = dict(schema_version=subject.REQUEST, sequence=1, case_index=1, operation='checkpoint', step=step)
    value.update(changes)
    return json.dumps(value)


class Contracts(unittest.TestCase):
    def test_01_exact_six_source_mapping(self):
        self.assertEqual([subject.directory(i)[-2:] for i in range(1, 7)], ['03', '04', '05', '06', '07', '08'])
        for index in (True, 0, 7, 8):
            with self.assertRaises(ValueError):
                subject.directory(index)

    def test_02_public_steps_and_new_wire(self):
        self.assertEqual(tuple(subject.LEGACY.values()), subject.base.batch.original.original.STEPS)
        for step in subject.STEPS:
            public, internal = subject.translate_request(frame(step))
            self.assertEqual(internal['step'], subject.LEGACY[public['step']])
        for raw in (frame('initial_pdf'), frame('sdk_insert'), frame(case_index=7), frame(case_index=True),
                    frame(schema_version=subject.base.batch.original.REQUEST), frame(path='private'), frame()+'\n',
                    frame()[:-1]+',"case_index":1}'):
            with self.assertRaises(ValueError):
                subject.translate_request(raw)

    def test_03_six_section_policy_same_resource_and_wall_limits(self):
        self.assertEqual(sections.SECTIONS, ('preparation', 'qualification', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'batch_close', 'final_audit'))
        self.assertEqual((sections.SECTION_SECONDS, sections.WHOLE_SECONDS), (600, 1800))
        original = (subject.r.c.ROOT/'tools/p09/crossref_section010_policy.py').read_text(encoding='utf-8')
        current = (subject.r.c.ROOT/'tools/p09/prepared_bookmark631_sections.py').read_text(encoding='utf-8')
        inverse = current.replace('prepared_bookmark631_sections', 'crossref_section010_policy').replace('range(1,7)', 'range(1,9)').replace('SECTION631', 'SECTION010').replace('prepared631-six-closed-sections', 'fixed010-closed-sections')
        self.assertEqual(inverse, original)

    def drain_fixture(self, states):
        clock = NS(value=0.)
        def sleep(seconds): clock.value += seconds
        account = Mock(side_effect=[dict(active_processes=n) for n in states])
        windows = NS(k=NS(WaitForSingleObject=Mock(return_value=0)), accounting=account)
        guard = NS(check=Mock(), windows=windows, samples=[dict(system_cpu_percent=1., available_ram_percent=50.)])
        current = NS(closed=False, pid=123, process=1, owner_job=NS(job=2, observe=Mock()), observe=Mock())
        worker, notify, records = NS(observe=Mock()), Mock(), []
        args = dict(clock=lambda: clock.value, sleep=sleep, observe_identities=Mock(return_value=[dict(pid=42)]))
        return current, guard, worker, notify, records, args

    def test_04_exited_root_child_is_guarded_until_empty(self):
        c, g, w, notify, rows, args = self.drain_fixture([1, 1, 0])
        drain.wait(c, g, w, notify, rows, **args)
        self.assertEqual(g.check.call_count, 3)
        self.assertEqual(c.owner_job.observe.call_count, 3)
        self.assertEqual(w.observe.call_count, 3)
        c.observe.assert_not_called()
        self.assertTrue(rows[0]['closed'])
        self.assertTrue(notify.called)

    def test_05_finite_work_timeout_never_kills_or_claims_cleanup(self):
        c, g, w, notify, rows, args = self.drain_fixture([1]*250)
        with self.assertRaisesRegex(ValueError, 'WORK45_TIMEOUT_NO_RETRY'):
            drain.wait(c, g, w, notify, rows, **args)
        self.assertTrue(rows[0]['work_stopped'])
        self.assertFalse(rows[0]['cleanup_confirmed'])
        self.assertLessEqual(len(rows[0]['observations']), 11)

    def test_06_CPU_or_RAM_guard_failure_stops_before_work(self):
        c, g, w, notify, rows, args = self.drain_fixture([1])
        g.check.side_effect = ValueError('STOP_RAM')
        with self.assertRaisesRegex(ValueError, 'STOP_RAM'):
            drain.wait(c, g, w, notify, rows, **args)
        c.owner_job.observe.assert_not_called()
        w.observe.assert_not_called()
        self.assertFalse(rows[0]['closed'])

    def test_07_worker_budget_failure_is_not_ignored(self):
        c, g, w, notify, rows, args = self.drain_fixture([0])
        w.observe.side_effect = ValueError('STOP_WORKER_PRIVATE')
        with self.assertRaisesRegex(ValueError, 'STOP_WORKER_PRIVATE'):
            drain.wait(c, g, w, notify, rows, **args)
        self.assertFalse(rows[0]['closed'])

    def test_08_bad_wait_is_not_exit(self):
        c, g, w, notify, rows, args = self.drain_fixture([0])
        g.windows.k.WaitForSingleObject.return_value = 0xffffffff
        with self.assertRaisesRegex(ValueError, 'EXACT_ROOT_WAIT_FAILED'):
            drain.wait(c, g, w, notify, rows, **args)

    def test_09_closed_and_absent_no_work(self):
        c, g, w, notify, rows, args = self.drain_fixture([])
        drain.wait(None, g, w, notify, rows, **args)
        c.closed = True
        drain.wait(c, g, w, notify, rows, **args)
        g.check.assert_not_called()

    def test_10_host_failure_latches_no_delegate(self):
        host = object.__new__(subject.Host)
        host.scope = NS(stopped=False, case_index=1, cursor=10, current=NS())
        host.protocol = NS(protocol=NS(stopped=False, sequence=0))
        host.ready = True
        host.worker_lease = Mock()
        host.guard, host.worker, host.drain_notify, host.drain_records = Mock(), Mock(), Mock(), []
        with patch.object(drain, 'wait', side_effect=ValueError('STOP_CPU')), patch.object(subject.base.batch.FixedEightHost, 'respond') as delegate:
            with self.assertRaisesRegex(ValueError, 'STOP_CPU'):
                host.respond(frame('create_reopen_session'))
            delegate.assert_not_called()
        self.assertTrue(host.scope.stopped and host.protocol.protocol.stopped)

    def test_11_wrong_next_checkpoint_cannot_enter_old_wait(self):
        host = object.__new__(subject.Host)
        host.scope = NS(stopped=False, case_index=1, cursor=0)
        host.protocol = NS(protocol=NS(stopped=False, sequence=0))
        with patch.object(subject.base.batch.FixedEightHost, 'respond') as delegate:
            with self.assertRaisesRegex(ValueError, 'EXACT_NEXT_CHECKPOINT'):
                host.respond(frame('create_reopen_session'))
            delegate.assert_not_called()

    def test_12_entry_no_old_flag_or_unknown_arguments(self):
        from contextlib import redirect_stderr
        for args in ([], ['--execute-prepared-eight-once'], ['--execute-remaining-six-once', '--retry']):
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                entry.parser().parse_args(args)
        self.assertTrue(entry.parser().parse_args(['--execute-remaining-six-once']).execute_remaining_six_once)

    def test_13_old_failure_and_incomplete_capture_not_reclassified(self):
        reader = Mock()
        reader.json.return_value = dict(schema_version='hwpx-agent.private.prepared-bookmark630-trace/v1', case_index=1,
            state='capture_started_semantics_unqualified')
        with self.assertRaises(ValueError):
            evidence.captured(reader, 'MODELED', 1, [], retained=True)
        reader.pin.assert_not_called()

    def test_14_empty_or_unclosed_producer_rejected(self):
        with self.assertRaises(ValueError):
            evidence.producer(dict(sessions=[], dual_identity_evidence=[]), [])


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Contracts)
    result = unittest.TestResult()
    suite.run(result)
    print(json.dumps(dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped),
        failed_tests=[str(t) for t, _ in result.errors+result.failures], actual_native_started=False)))
    sys.exit(0 if result.wasSuccessful() else 2)
