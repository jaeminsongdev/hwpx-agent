"""P179 r2 fresh half-second counter windows; first zero-interval failures preserved."""
import io
import math
import sys
import time
import unittest
from unittest.mock import patch
import pre_go_parent_cpu_observer as prior
SELF='tools/p09/pre_go_parent_cpu_observer_r2.py'
TEST='tools/p09/tests/test_parent_cpu_observer_interval.py'
RAW_WINDOWS=prior.c.Windows
RAW_PARENT=prior.ParentCPUWindows
RAW_CONTRACTS=prior.contracts

class FreshInterval:
    def __init__(self,clock=time.monotonic,sleep=time.sleep):
        self.clock=clock;self.sleep=sleep;self.last=clock()
    def wait(self):
        now=self.clock()
        prior.c.require(type(now) in (int,float) and math.isfinite(now) and now>=self.last,'PARENT_INTERVAL_CLOCK_INVALID')
        target=self.last+prior.c.POLICY['sample_seconds']
        if now<target:self.sleep(target-now)
        now=self.clock()
        prior.c.require(type(now) in (int,float) and math.isfinite(now) and now>=target,'PARENT_INTERVAL_NOT_ADVANCED')
    def completed(self):self.last=self.clock()

class IntervalWindows(RAW_WINDOWS):
    def __init__(self):super().__init__();self.interval=FreshInterval()
    def sample(self):
        self.interval.wait();row=super().sample();self.interval.completed();return row

class IntervalParent(RAW_PARENT):
    def __init__(self):super().__init__();self.interval=FreshInterval()
    def sample(self):
        self.interval.wait();row=super().sample();self.interval.completed();return row

def contracts():
    # Original fixtures patch the original base sampler. Keep that context exact
    # while the actual observer later selects the interval wrapper.
    with patch.object(prior.c,'Windows',RAW_WINDOWS),patch.object(prior,'ParentCPUWindows',RAW_PARENT):RAW_CONTRACTS()
    sys.path.insert(0,str(prior.c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_parent_cpu_observer_interval')
    with patch('subprocess.Popen',side_effect=AssertionError('P179_R2_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P179_R2_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P179_R2_NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    prior.c.require(result.wasSuccessful() and result.testsRun==2 and not result.skipped,'PARENT_INTERVAL_CONTRACT5_PLUS2')
    return dict(contract_tests_passed=7)

def main():
    raw_path=prior.scoped_path
    def destination(name,**kw):return raw_path(name.replace('-run01.v1.json','-r2-run01.v1.json'),**kw)
    with patch.object(prior,'SELF',SELF),patch.object(prior,'TEST',TEST),patch.object(prior,'scoped_path',destination), \
            patch.object(prior,'contracts',contracts),patch.object(prior.c,'Windows',IntervalWindows), \
            patch.object(prior,'ParentCPUWindows',IntervalParent):return prior.main()

if __name__=='__main__':raise SystemExit(main())
