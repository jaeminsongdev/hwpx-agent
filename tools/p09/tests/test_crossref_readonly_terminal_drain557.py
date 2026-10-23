"""New terminal-only close tests. No child/process creation or Native activation."""
import unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
import crossref_readonly_terminal_drain557 as subject
def fake(counts,live=False):
    state=subject.DrainedReadonlyProcess.__new__(subject.DrainedReadonlyProcess);state.closed=False;state.process=91;state.thread=92
    state.profile={'cleanup_confirmed':False};state.envelope=NS(job=123,profile={})
    state.envelope.close=Mock(side_effect=lambda:state.envelope.profile.update(cleanup_confirmed=True))
    values=iter(counts)
    state.windows=NS(accounting=Mock(side_effect=lambda job:dict(active_processes=next(values,0))),
        k=NS(WaitForSingleObject=Mock(return_value=258 if live else 0),CloseHandle=Mock(return_value=True)))
    return state
class Tests(unittest.TestCase):
    def test_same_terminal_process_and_job_drain_before_original_handle_close(self):
        state=fake([2,1,0])
        with patch.object(subject.time,'sleep')as nap:state.close()
        self.assertEqual(nap.call_count,2);self.assertTrue(state.closed);self.assertTrue(state.profile['cleanup_confirmed'])
        self.assertEqual(state.profile['post_terminal_tree_drain']['initial_active_prefix'],[2,1,0]);self.assertIsNone(state.process);self.assertIsNone(state.thread)
        self.assertEqual([c.args for c in state.windows.k.CloseHandle.call_args_list],[(92,),(91,)])
    def test_still_live_child_keeps_original_refusal_without_tree_poll_or_close(self):
        state=fake([1],True)
        with self.assertRaisesRegex(ValueError,'LIVE_CHILD_RETAIN_HANDLES'):state.close()
        state.windows.accounting.assert_not_called();state.windows.k.CloseHandle.assert_not_called();self.assertEqual(state.process,91);self.assertFalse(state.closed)
    def test_completed_close_is_idempotent_and_cannot_resume_or_restart(self):
        state=fake([0]);state.close();calls=state.windows.accounting.call_count;state.close()
        self.assertEqual(state.windows.accounting.call_count,calls);self.assertEqual(state.windows.k.CloseHandle.call_count,2)
        self.assertEqual(set(subject.DrainedReadonlyProcess.__dict__)-{'__module__','__doc__'},{'close'})
    def test_bounded_diagnostic_prefix_does_not_truncate_or_skip_remaining_tree(self):
        state=fake([1]*20+[0])
        with patch.object(subject.time,'sleep')as nap:state.close()
        value=state.profile['post_terminal_tree_drain'];self.assertEqual(value['observations'],21);self.assertEqual(value['initial_active_prefix'],[1]*8)
        self.assertEqual(nap.call_count,20);self.assertTrue(value['same_job_observed']);self.assertFalse(value['forced_termination_invoked'])
