"""Virtual clock only: no native calls, process creation, COM or document operations."""
import unittest
from types import SimpleNamespace as NS
import crossref_startup_input_idle_candidate546 as subject
def model():
    t=[0.0];events=[];naps=[]
    state=NS(closed=False,process=91,profile=dict(resumed=True,native_startup_qualified=False,native_execution_authorized=False),
        observe=lambda:events.append('guard'),_fresh_image=lambda:events.append('image'))
    def nap(seconds):naps.append(seconds);t[0]+=seconds
    return state,t,events,naps,nap
class Tests(unittest.TestCase):
    def test_delayed_four_second_idle_is_not_three_second_failure(self):
        s,t,e,n,nap=model();calls=[]
        def wait(h,ms):calls.append((h,ms));return 0 if t[0]>=4 else 258
        subject._wait(s,wait,lambda:t[0],nap)
        self.assertGreaterEqual(t[0],4);self.assertLess(t[0],4.1);self.assertEqual(set(calls),{(91,0)})
        self.assertEqual(e.count('guard'),len(calls)+1);self.assertEqual(e.count('image'),1)
        self.assertFalse(s.profile['native_startup_qualified']);self.assertFalse(s.profile['native_execution_authorized'])
    def test_never_idle_has_clipped_sleep_strict_fifteen_and_no_retry(self):
        s,t,e,n,nap=model();calls=[]
        def wait(h,ms):calls.append((h,ms));return 258
        with self.assertRaisesRegex(ValueError,'BOUNDED_STARTUP_WAIT_EXPIRED_NO_RETRY'):subject._wait(s,wait,lambda:t[0],nap)
        self.assertEqual(t[0],15);self.assertTrue(all(0<v<=.05 for v in n));self.assertLessEqual(len(calls),301)
        before=len(calls)
        with self.assertRaisesRegex(ValueError,'ONE_RESUMED_HELD_PROCESS_WAIT_ONLY'):subject._wait(s,wait,lambda:t[0],nap)
        self.assertEqual(len(calls),before);self.assertFalse(s.profile['input_idle_observed'])
    def test_idle_just_before_limit_is_accepted_only_after_same_guard_and_image(self):
        s,t,e,n,nap=model();t[0]=0
        def wait(h,ms):return 0 if t[0]>=14.9 else 258
        subject._wait(s,wait,lambda:t[0],nap)
        self.assertLess(t[0],15);self.assertEqual(e[-2:],['guard','image'])
    def test_expired_observer_never_calls_wait(self):
        s,t,e,n,nap=model();s.observe=lambda:t.__setitem__(0,15.0);calls=[]
        with self.assertRaisesRegex(ValueError,'BOUNDED_STARTUP_WAIT_EXPIRED_NO_RETRY'):subject._wait(s,lambda h,ms:calls.append(h),lambda:t[0],nap)
        self.assertEqual(calls,[]);self.assertEqual(n,[]);self.assertFalse(s.profile['input_idle_observed'])
    def test_wait_timeout_consuming_remaining_budget_never_sleeps(self):
        s,t,e,n,nap=model()
        def wait(h,ms):t[0]=15;return 258
        with self.assertRaisesRegex(ValueError,'BOUNDED_STARTUP_WAIT_EXPIRED_NO_RETRY'):subject._wait(s,wait,lambda:t[0],nap)
        self.assertEqual(n,[]);self.assertEqual(s.profile['input_idle_poll_count'],1)
    def test_native_guard_cost_counts_against_same_absolute_bound(self):
        s,t,e,n,nap=model()
        def guard():t[0]+=.4;e.append('guard')
        s.observe=guard
        subject._wait(s,lambda h,ms:0 if t[0]>=4 else 258,lambda:t[0],nap)
        self.assertGreater(t[0],4);self.assertLess(t[0],15);self.assertLess(s.profile['input_idle_poll_count'],12)
    def test_resource_rejection_after_old_bound_still_precedes_wait(self):
        s,t,e,n,nap=model();calls=[]
        def guard():
            if t[0]>=4:raise ValueError('STOP_NATIVE_RESOURCE')
        s.observe=guard
        with self.assertRaisesRegex(ValueError,'STOP_NATIVE_RESOURCE'):subject._wait(s,lambda h,ms:calls.append(t[0])or 258,lambda:t[0],nap)
        self.assertTrue(calls);self.assertLess(max(calls),4);self.assertFalse(s.profile['input_idle_observed'])
    def test_post_idle_image_and_owner_guard_deadline_still_denies(self):
        s,t,e,n,nap=model();s._fresh_image=lambda:t.__setitem__(0,15.0)
        with self.assertRaisesRegex(ValueError,'BOUNDED_STARTUP_WAIT_EXPIRED_NO_RETRY'):subject._wait(s,lambda h,ms:0,lambda:t[0],nap)
        self.assertFalse(s.profile['input_idle_observed']);self.assertFalse(s.profile['input_idle_is_COM_readiness_or_authority'])
