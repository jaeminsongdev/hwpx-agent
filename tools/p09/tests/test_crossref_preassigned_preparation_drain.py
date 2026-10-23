"""New post-terminal envelope models only. No process or Native invocation."""
import io,unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
import crossref_preassigned_preparation_drain as subject


def fake(counts,live=False):
    state=subject.DrainedPreparationWorker.__new__(subject.DrainedPreparationWorker)
    state.closed=False;state.job=123;state.profile={'cleanup_confirmed':False}
    state.process=NS(poll=lambda:None if live else 0,wait=Mock(),stdin=io.StringIO(),stdout=io.StringIO(),stderr=io.StringIO())
    values=iter(counts);last=0
    def accounting(job):
        nonlocal last
        last=next(values,last);return {'active_processes':last}
    state.windows=NS(accounting=Mock(side_effect=accounting),k=NS(CloseHandle=Mock(return_value=True)))
    return state


class DrainContracts(unittest.TestCase):
    def test_01_same_tree_waits_until_empty_before_original_close(self):
        state=fake([2,1,0])
        with patch.object(subject.time,'sleep')as sleep:state.close()
        self.assertEqual(sleep.call_count,2);self.assertTrue(state.profile['cleanup_confirmed']);self.assertIsNone(state.job)
        self.assertEqual(state.profile['post_terminal_tree_drain']['initial_active_prefix'],[2,1,0])
        state.windows.k.CloseHandle.assert_called_once_with(123)
    def test_02_live_bootstrap_still_refused_without_polling_or_losing_job(self):
        state=fake([1],live=True)
        with self.assertRaisesRegex(ValueError,'LIVE_WORKER_NO_FORCE_CLOSE'):state.close()
        state.windows.accounting.assert_not_called();state.windows.k.CloseHandle.assert_not_called()
        self.assertEqual(state.job,123);self.assertFalse(state.closed);self.assertFalse(hasattr(state,'kill'))
    def test_03_successful_close_is_idempotent_not_a_second_tree_release(self):
        state=fake([0])
        with patch.object(subject.time,'sleep'):state.close();calls=state.windows.accounting.call_count;state.close()
        self.assertEqual(state.windows.accounting.call_count,calls);state.windows.k.CloseHandle.assert_called_once_with(123)
    def test_04_wait_diagnostics_are_bounded_while_same_job_is_retained(self):
        state=fake([1]*20+[0])
        with patch.object(subject.time,'sleep'):state.close()
        observed=state.profile['post_terminal_tree_drain']
        self.assertEqual(observed['observations'],21);self.assertEqual(observed['initial_active_prefix'],[1]*8)
        self.assertTrue(observed['same_job_observed']);self.assertFalse(observed['forced_termination_invoked'])
