"""Modeled preassigned controller callbacks only; never launches an actual Hwp/COM/worker."""
import ast
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock,patch

import crossref_preassigned_session_scope as subject


class FakeStartup:
    def __init__(self,index,events):
        self.events=events;self.pid=1000+index;self.birth=133000000000000000+index;self.session=1
        self.closed=False;self.alive=False;self.fail=None
        self.profile=dict(pre_run_verified=False,assigned_before_initial_thread=False,resumed=False,
            owner_bound=False,cleanup_confirmed=False,native_startup_qualified=False)
    def create_suspended(self):
        self.events.append(('create',self.pid));self.alive=True
        if self.fail=='create':raise ValueError('MODEL_CREATE_UNCERTAIN')
        self.profile.update(pre_run_verified=True,assigned_before_initial_thread=True)
    def resume(self):
        self.events.append(('resume',self.pid))
        if self.fail=='resume':raise ValueError('MODEL_RESUME_UNCERTAIN')
        self.profile['resumed']=True
    def observe(self):
        if not self.alive:raise ValueError('MODEL_EXITED_PROCESS_MUST_NOT_BE_OBSERVED')
        self.events.append(('observe',self.pid))
    def bind_owner(self,identity,window):
        self.events.append(('bind',self.pid))
        if self.fail=='bind':raise ValueError('MODEL_WINDOW_MISMATCH')
        if identity['process_id']!=self.pid:raise ValueError('MODEL_PID_MISMATCH')
        self.profile['owner_bound']=True;return dict(verified=True)
    def close(self):
        self.events.append(('close',self.pid))
        if self.alive:raise ValueError('MODEL_LIVE_NATIVE_RETAIN_HANDLES_AND_JOB')
        self.closed=True;self.profile['cleanup_confirmed']=True


class SessionScopeContracts(unittest.TestCase):
    def setUp(self):
        self.events=[];self.created=[];self.next_failure=None;self.reuse=False
        self.guard=NS(check=Mock(),windows=subject.startup.limits.c.Windows.__new__(subject.startup.limits.c.Windows))
        self.factory_patch=patch.object(subject.startup,'PreassignedNativeStartup',side_effect=self.factory)
        self.factory_mock=self.factory_patch.start();self.addCleanup(self.factory_patch.stop)
        self.scope=subject.PreassignedSessionScope(self.guard,lambda:None)
    def factory(self,*args):
        item=FakeStartup(1 if self.reuse else len(self.created)+1,self.events)
        item.fail=self.next_failure;self.created.append(item);return item
    def begin(self,index=1):
        self.scope.checkpoint(index,'prepare_slot');self.scope.checkpoint(index,'create_save_session')
    def admit(self,index=1):
        descriptor=self.scope.pending_owner_descriptor(index)
        return self.scope.admit_owner(index,{'process_id':descriptor['process_id']},123)
    def remaining(self,index=1):
        while self.scope.cursor<len(subject.original.STEPS):
            step=subject.original.STEPS[self.scope.cursor]
            self.scope.checkpoint(index,step)
            if step=='create_reopen_session':self.admit(index)
            if step in('save_session_close','reopen_session_close'):self.scope.current.alive=False

    def test_01_whole_fixed_eight_keeps_sixteen_nonoverlapping_preassigned_lifetimes(self):
        for index in range(1,9):
            self.begin(index);self.admit(index);self.remaining(index);self.scope.finish(index,'returned')
        self.scope.close();out=self.scope.summary()
        self.assertEqual(len(self.created),16);self.assertEqual(len(out['retired_sessions']),16)
        self.assertEqual(len(out['finished_cases']),8);self.assertTrue(out['all_eight_callback_cases_returned'])
        self.assertEqual([r['session_label']for r in out['retired_sessions']],['save','reopen']*8)
        for item in self.created:
            self.assertLess(self.events.index(('create',item.pid)),self.events.index(('resume',item.pid)))
            self.assertLess(self.events.index(('resume',item.pid)),self.events.index(('bind',item.pid)))
            self.assertTrue(item.closed)
        for field in('native_execution_authorized','native_startup_qualified','native_execution_attested','native_cleanup_qualified','P09_complete'):
            self.assertIs(out[field],False)

    def test_02_out_of_order_first_step_latches_before_factory(self):
        with self.assertRaisesRegex(ValueError,'EXACT_STEP_OR_PENDING_OWNER'):self.scope.checkpoint(1,'create_save_session')
        self.factory_mock.assert_not_called();self.assertTrue(self.scope.stopped)
        with self.assertRaisesRegex(ValueError,'STOPPED_NO_RETRY'):self.scope.checkpoint(1,'prepare_slot')

    def test_03_preparation_only_or_wrong_windows_guard_is_not_a_native_dependency(self):
        for guard in(NS(check=lambda:None,windows=self.guard.windows,preparation_CPU=True),NS(check=lambda:None,windows=object()),NS(windows=self.guard.windows)):
            with self.assertRaisesRegex(ValueError,'ORIGINAL_NATIVE_GUARD_REQUIRED'):subject.PreassignedSessionScope(guard,lambda:None)
        self.factory_mock.assert_not_called()

    def test_04_closed_scope_cannot_start_again(self):
        self.scope.close();self.scope.close()
        with self.assertRaisesRegex(ValueError,'STOPPED_NO_RETRY'):self.scope.checkpoint(1,'prepare_slot')
        self.factory_mock.assert_not_called()

    def test_05_work_cannot_pass_creation_without_exact_owner_admission(self):
        self.begin()
        with self.assertRaisesRegex(ValueError,'EXACT_STEP_OR_PENDING_OWNER'):self.scope.checkpoint(1,'source_open')
        self.assertEqual(len(self.created),1);self.assertIs(self.scope.current,self.created[0]);self.assertTrue(self.scope.stopped)

    def test_06_descriptor_is_current_identity_data_without_bound_com_or_authority(self):
        self.begin();descriptor=self.scope.pending_owner_descriptor(1)
        self.assertEqual(descriptor,self.scope.pending_owner_descriptor(1));self.assertEqual(descriptor['process_id'],self.created[0].pid)
        self.assertEqual(descriptor['created_at_utc'],subject.startup.utc_identity(self.created[0].birth))
        for key in('COM_owner_bound','native_execution_authorized','native_startup_qualified','P09_complete'):self.assertFalse(descriptor[key])
        self.assertEqual(sum(e[0]=='resume'for e in self.events),1)

    def test_07_admission_before_creation_and_after_binding_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'SINGLE_PENDING_OWNER_ADMISSION'):self.scope.admit_owner(1,{},123)
        self.factory_mock.assert_not_called()
        self.scope=subject.PreassignedSessionScope(self.guard,lambda:None);self.begin();self.admit()
        with self.assertRaisesRegex(ValueError,'SINGLE_PENDING_OWNER_ADMISSION'):self.scope.admit_owner(1,{},123)

    def test_08_bind_failure_keeps_same_backend_and_latches_no_retry(self):
        self.next_failure='bind';self.begin()
        with self.assertRaisesRegex(ValueError,'MODEL_WINDOW_MISMATCH'):self.admit()
        self.assertIs(self.scope.current,self.created[0]);self.assertTrue(self.scope.pending_admission)
        with self.assertRaisesRegex(ValueError,'STOPPED_NO_RETRY'):self.admit()

    def test_09_uncertain_creation_retains_backend_without_resume_or_restart(self):
        self.next_failure='create';self.scope.checkpoint(1,'prepare_slot')
        with self.assertRaisesRegex(ValueError,'MODEL_CREATE_UNCERTAIN'):self.scope.checkpoint(1,'create_save_session')
        self.assertIs(self.scope.current,self.created[0]);self.assertFalse(any(e[0]=='resume'for e in self.events))
        with self.assertRaisesRegex(ValueError,'STOPPED_NO_RETRY'):self.scope.checkpoint(1,'create_save_session')

    def test_10_uncertain_resume_retains_backend_and_does_not_retry(self):
        self.next_failure='resume';self.scope.checkpoint(1,'prepare_slot')
        with self.assertRaisesRegex(ValueError,'MODEL_RESUME_UNCERTAIN'):self.scope.checkpoint(1,'create_save_session')
        self.assertIs(self.scope.current,self.created[0]);self.assertEqual(sum(e[0]=='resume'for e in self.events),1)
        with self.assertRaisesRegex(ValueError,'STOPPED_NO_RETRY'):self.scope.checkpoint(1,'create_save_session')

    def test_11_cleanup_remains_available_after_guard_stop_without_more_sampling(self):
        self.begin();self.admit();self.guard.check.side_effect=ValueError('STOP_SYSTEM_CPU')
        self.created[0].alive=False;calls=self.guard.check.call_count;self.scope.close()
        self.assertEqual(calls,self.guard.check.call_count);self.assertTrue(self.scope.closed)

    def test_12_live_prior_owner_blocks_next_creation_and_retains_exact_backend(self):
        self.begin();self.admit()
        while subject.original.STEPS[self.scope.cursor]!='create_reopen_session':
            self.scope.checkpoint(1,subject.original.STEPS[self.scope.cursor])
        with self.assertRaisesRegex(ValueError,'MODEL_LIVE_NATIVE_RETAIN_HANDLES_AND_JOB'):self.scope.checkpoint(1,'create_reopen_session')
        self.assertEqual(len(self.created),1);self.assertIs(self.scope.current,self.created[0])

    def test_13_exited_previous_owner_is_retired_before_any_live_observation(self):
        self.begin();self.admit();self.remaining();self.scope.finish(1,'returned')
        self.assertEqual(len(self.scope.sessions),2);self.assertFalse(self.scope.stopped)

    def test_14_kernel_lifetime_reuse_is_rejected_before_second_resume(self):
        self.begin();self.admit();self.reuse=True
        while subject.original.STEPS[self.scope.cursor]!='create_reopen_session':
            step=subject.original.STEPS[self.scope.cursor];self.scope.checkpoint(1,step)
            if step=='save_session_close':self.scope.current.alive=False
        with self.assertRaisesRegex(ValueError,'UNIQUE_KERNEL_LIFETIME'):self.scope.checkpoint(1,'create_reopen_session')
        self.assertEqual(len(self.created),2);self.assertEqual(sum(e[0]=='resume'for e in self.events),1)
        self.assertIs(self.scope.current,self.created[1])

    def test_15_failed_finish_does_not_advance_and_cannot_be_replayed(self):
        self.scope.finish(1,'failed');self.assertTrue(self.scope.stopped);self.assertEqual(self.scope.case_index,1)
        with self.assertRaisesRegex(ValueError,'SINGLE_CASE_FINISH'):self.scope.finish(1,'failed')

    def test_16_case_boolean_subset_or_future_case_has_no_factory_effect(self):
        for index in(True,0,2,9):
            self.scope.stopped=False
            with self.assertRaisesRegex(ValueError,'EXACT_CASE_ORDER'):self.scope.checkpoint(index,'prepare_slot')
        self.factory_mock.assert_not_called()

    def test_17_completed_summary_is_detached_and_has_no_live_execution_token(self):
        self.begin();self.admit();self.remaining();self.scope.finish(1,'returned')
        out=self.scope.summary();out['retired_sessions'][0]['startup_profile']['cleanup_confirmed']=False
        out['finished_cases'].clear();self.assertTrue(self.scope.sessions[0]['startup_profile']['cleanup_confirmed']);self.assertEqual(len(self.scope.finished),1)

    def test_18_early_success_and_uncertain_finish_keep_live_owner_for_observation_only(self):
        self.begin();self.admit()
        with self.assertRaisesRegex(ValueError,'ALL_STEPS_AND_EXIT_BEFORE_RETURNED'):self.scope.finish(1,'returned')
        with self.assertRaisesRegex(ValueError,'MODEL_LIVE_NATIVE_RETAIN_HANDLES_AND_JOB'):self.scope.close()
        self.assertIs(self.scope.current,self.created[0]);self.created[0].alive=False;self.scope.close();self.assertTrue(self.scope.closed)

    def test_19_bound_pid_mismatch_never_becomes_late_job_admission(self):
        self.begin()
        with self.assertRaisesRegex(ValueError,'MODEL_PID_MISMATCH'):self.scope.admit_owner(1,{'process_id':999},123)
        self.assertEqual(sum(e[0]=='bind'for e in self.events),1);self.assertTrue(self.scope.stopped)

    def test_20_source_has_no_cli_com_creation_generic_process_or_late_assignment(self):
        text=(Path(__file__).resolve().parents[3]/'tools/p09/crossref_preassigned_session_scope.py').read_text(encoding='utf-8')
        tree=ast.parse(text);calls={n.func.attr if isinstance(n.func,ast.Attribute)else n.func.id for n in ast.walk(tree)
            if isinstance(n,ast.Call)and isinstance(n.func,(ast.Name,ast.Attribute))}
        self.assertFalse(calls&{'Popen','run','system','CreateProcessW','AssignProcessToJobObject','CoCreateInstance','GetActiveObject','kill','TerminateProcess','TerminateJobObject','sleep'})
        self.assertFalse(any(isinstance(n,ast.If)and'__name__'in ast.unparse(n.test)for n in tree.body))
        self.assertIn('self.current.create_suspended()',text);self.assertIn('self.current.bind_owner(identity,window_handle)',text)
