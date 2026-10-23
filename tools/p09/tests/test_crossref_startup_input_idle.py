"""Pure models only. No actual process wait/Native/COM or document actions."""
import ast,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
import crossref_startup_input_idle as subject
import crossref_native_startup as startup
def model():
    ticks=[0.0];events=[]
    state=NS(closed=False,process=91,profile=dict(resumed=True,native_startup_qualified=False,native_execution_authorized=False),
        observe=lambda:events.append('guard_kernel_job'),_fresh_image=lambda:events.append('fresh_image'))
    def sleep(seconds):events.append('sleep');ticks[0]+=seconds
    return state,events,ticks,sleep
class Tests(unittest.TestCase):
    def test_immediate_idle_rechecks_same_handle_and_image_not_authority(self):
        s,e,t,nap=model();wait=Mock(return_value=0);subject._wait(s,wait,lambda:t[0],nap)
        wait.assert_called_once_with(91,0);self.assertEqual(e,['guard_kernel_job','guard_kernel_job','fresh_image'])
        self.assertTrue(s.profile['input_idle_observed']);self.assertFalse(s.profile['input_idle_is_COM_readiness_or_authority']);self.assertFalse(s.profile['native_startup_qualified'])
    def test_timeouts_poll_only_same_handle_without_activation_or_relaunch(self):
        s,e,t,nap=model();wait=Mock(side_effect=[258,258,0]);subject._wait(s,wait,lambda:t[0],nap)
        self.assertEqual(wait.call_count,3);self.assertTrue(all(call.args==(91,0)for call in wait.call_args_list));self.assertEqual(e.count('sleep'),2)
    def test_never_idle_stops_at_original_fixed_bound_without_retry(self):
        s,e,t,nap=model();wait=Mock(return_value=258)
        with self.assertRaisesRegex(ValueError,'BOUNDED_STARTUP_WAIT_EXPIRED_NO_RETRY'):subject._wait(s,wait,lambda:t[0],nap)
        self.assertFalse(s.profile['input_idle_observed']);n=wait.call_count
        with self.assertRaisesRegex(ValueError,'ONE_RESUMED_HELD_PROCESS_WAIT_ONLY'):subject._wait(s,wait,lambda:t[0],nap)
        self.assertEqual(wait.call_count,n);self.assertLessEqual(t[0],subject.BOUND_SECONDS+.1)
    def test_wait_failed_and_unknown_status_never_sleep_or_bind(self):
        for code in(0xffffffff,1,259):
            s,e,t,nap=model()
            with self.assertRaisesRegex(ValueError,'WAIT_FAILED_NO_OWNER_OR_RETRY'):subject._wait(s,lambda h,m:code,lambda:t[0],nap)
            self.assertNotIn('sleep',e);self.assertFalse(s.profile['input_idle_observed'])
    def test_resource_or_kernel_rejection_precedes_wait_call(self):
        s,e,t,nap=model();s.observe=Mock(side_effect=ValueError('STOP_NATIVE_RESOURCE'));wait=Mock()
        with self.assertRaisesRegex(ValueError,'STOP_NATIVE_RESOURCE'):subject._wait(s,wait,lambda:t[0],nap)
        wait.assert_not_called();self.assertFalse(s.profile['input_idle_observed'])
    def test_rejection_after_idle_does_not_report_observed(self):
        s,e,t,nap=model();s.observe=Mock(side_effect=[None,ValueError('STOP_KERNEL_DRIFT')])
        with self.assertRaisesRegex(ValueError,'STOP_KERNEL_DRIFT'):subject._wait(s,lambda h,m:0,lambda:t[0],nap)
        self.assertFalse(s.profile['input_idle_observed'])
    def test_expired_final_image_check_does_not_report_observed(self):
        s,e,t,nap=model();s._fresh_image=lambda:t.__setitem__(0,subject.BOUND_SECONDS+1.0)
        with self.assertRaisesRegex(ValueError,'BOUNDED_STARTUP_WAIT_EXPIRED_NO_RETRY'):subject._wait(s,lambda h,m:0,lambda:t[0],nap)
        self.assertFalse(s.profile['input_idle_observed'])
    def test_closed_unresumed_or_missing_handle_are_not_waited(self):
        for field in('closed','resumed','process'):
            s,e,t,nap=model();wait=Mock()
            if field=='resumed':s.profile['resumed']=False
            else:setattr(s,field,True if field=='closed'else None)
            with self.assertRaisesRegex(ValueError,'ONE_RESUMED_HELD_PROCESS_WAIT_ONLY'):subject._wait(s,wait,lambda:t[0],nap)
            wait.assert_not_called()
    def test_single_resume_calls_wait_before_return_and_failure_latches(self):
        for fail in(False,True):
            s=startup.PreassignedNativeStartup.__new__(startup.PreassignedNativeStartup);events=[]
            s.closed=False;s.resume_attempted=False;s.thread=45;s.profile=dict(pre_run_verified=True)
            s._fresh_image=lambda:events.append('image');s.verify_suspended=lambda:events.append('suspended')
            s.windows=NS(k=NS(ResumeThread=lambda h:events.append('resume')or 1))
            def wait(value):
                self.assertIs(value,s);self.assertTrue(s.profile['resumed']);events.append('idle')
                if fail:raise ValueError('STOP_IDLE_MODEL')
            with patch.object(startup.input_idle,'wait',side_effect=wait):
                if fail:
                    with self.assertRaisesRegex(ValueError,'STOP_IDLE_MODEL')as caught:s.resume()
                    self.assertIs(caught.exception.preassigned_native_startup,s)
                else:s.resume()
            self.assertEqual(events,['image','suspended','resume','idle']);self.assertTrue(s.resume_attempted)
            with self.assertRaisesRegex(ValueError,'NO_RESUME_RETRY'):s.resume()
    def test_all_existing_controllers_use_same_resume_gate_without_fallback(self):
        root=Path(startup.__file__).parent
        for file in('crossref_session_qualification.py','crossref_preassigned_session_scope.py'):
            source=(root/file).read_text(encoding='utf-8');self.assertIn('self.current.resume()',source)
        source=Path(subject.__file__).read_text(encoding='utf-8');calls={n.func.attr for n in ast.walk(ast.parse(source))if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)}
        self.assertTrue({'CreateProcessW','ResumeThread','Attach','bind_owner','Quit','kill'}.isdisjoint(calls))
