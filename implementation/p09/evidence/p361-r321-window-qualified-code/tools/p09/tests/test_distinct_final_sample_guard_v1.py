import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import distinct_final_sample_guard_v1 as m

class Clock:
    def __init__(self):self.value=1.;self.sleeps=[]
    def __call__(self):return self.value
    def sleep(self,n):self.sleeps.append(n);self.value+=n
def create(initial=True,error=None):
    clock=Clock()
    class Original:
        def __init__(self):self.last=1.;self.samples=[1.] if initial else [];self.calls=[]
        def check(self,force=False):
            self.calls.append(force)
            if error is not None:raise error
            if force or not self.samples or clock.value-self.last>=.5:
                self.last=clock.value;self.samples.append(clock.value)
    New=m.guard_type(Original,clock,clock.sleep)
    return New(),clock,Original

class Tests(unittest.TestCase):
    def test_force_waits_original_distinct_slot_and_one_new_sample(self):
        g,c,_=create();g.check(force=True)
        self.assertEqual(len(g.samples),2);self.assertGreaterEqual(g.samples[-1]-g.samples[0],.5)
        self.assertLessEqual(max(c.sleeps),.05)
    def test_nonforce_path_no_extra_wait_and_original_call(self):
        g,c,_=create();g.check();self.assertEqual(g.calls,[False]);self.assertEqual(c.sleeps,[])
    def test_first_force_retains_original_admission_behavior(self):
        g,c,_=create(False);g.check(force=True);self.assertEqual(g.calls,[True]);self.assertEqual(c.sleeps,[])
    def test_original_hard_error_identity_precedes_wait(self):
        error=ValueError("ORIGINAL_HARD_STOP");g,c,_=create(error=error)
        with self.assertRaises(ValueError) as ctx:g.check(force=True)
        self.assertIs(ctx.exception,error);self.assertEqual(c.sleeps,[])
    def test_already_distinct_force_no_double_sample(self):
        g,c,_=create();c.value=2.;g.check(force=True)
        self.assertEqual(g.samples,[1.,2.]);self.assertEqual(c.sleeps,[])
    def test_subsequent_force_requires_another_fresh_slot(self):
        g,c,_=create();g.check(force=True);g.check(force=True)
        self.assertEqual(len(g.samples),3);self.assertGreaterEqual(g.samples[-1]-g.samples[-2],.5)
    def test_deadline_error_during_wait_not_bypassed(self):
        g,c,old=create();base=old.check;error=ValueError("ORIGINAL600_TIMEOUT")
        def check(self,force=False):
            if c.value>1.1:raise error
            return base(self,force)
        old.check=check
        with self.assertRaises(ValueError) as ctx:g.check(force=True)
        self.assertIs(ctx.exception,error);self.assertEqual(len(g.samples),1)
    def test_clock_error_propagates_and_force_flag_bool_required(self):
        g,c,_=create()
        with self.assertRaises(ValueError):g.check(force=1)
        self.assertEqual(g.samples,[1.])
    def test_nonadvancing_wait_bounded_no_busy_loop(self):
        g,c,old=create();New=m.guard_type(old,c,lambda _:None);stopped=New()
        with self.assertRaisesRegex(ValueError,"WAIT_CLOCK_NOT_ADVANCING"):stopped.check(force=True)
        self.assertEqual(len(stopped.calls),64)

if __name__=="__main__":unittest.main()
