"""Fake PDH contracts; no performance provider/Native input/product work."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import serial_cpu_attribution as p
import accept_case112_current_epoch as a


class Fake:
    def __init__(self):
        self.names={};self.calls=0;self.closed=[];self.bad=set();self.return_code=0;self.close_code=0
        self.data=dict(MsMpEng_pid=5408,System_pid=4,MsMpEng_cpu=800.,System_cpu=160.,total_cpu=95.,DPC_cpu=2.,interrupt_cpu=1.)
    def open(self):return 0,1
    def add(self,query,path):
        name=next(n for n,v in p.PATHS.items() if v==path);self.names[name]=name
        return 0,name
    def collect(self,query):self.calls+=1;return self.return_code
    def value(self,name,is_pid):return (0,0xc0000bc6,None) if name in self.bad else (0,1,self.data[name])
    def close(self,query):self.closed.append(query);return self.close_code


class SerialAttributionContracts(unittest.TestCase):
    def make(self,**kw):
        api=Fake();probe=p.Probe(16,api=api,**kw);self.addCleanup(probe.close);return probe,api
    def test_fixed_seven_no_wildcards_two_collections_and_multicore_not_capped100(self):
        probe,api=self.make();row=probe.sample()
        self.assertEqual(api.calls,2);self.assertEqual(len(api.names),7)
        self.assertFalse(any('*' in v for v in p.PATHS.values()))
        self.assertEqual(row['values']['MsMpEng']['machine_cpu_percent'],50)
        self.assertEqual(row['values']['System']['machine_cpu_percent'],10)
        self.assertEqual(row['values']['total_cpu'],95)
    def test_invalid_or_missing_counter_is_unknown_not_zero(self):
        probe,api=self.make();api.bad.add('MsMpEng_cpu');row=probe.sample()
        self.assertIsNone(row['values']['MsMpEng']['machine_cpu_percent'])
    def test_pid_change_or_system_not4_is_not_misattributed(self):
        probe,api=self.make();api.data['MsMpEng_pid']=999;api.data['System_pid']=8
        row=probe.sample();self.assertIsNone(row['values']['MsMpEng']['machine_cpu_percent'])
        self.assertIsNone(row['values']['System']['machine_cpu_percent'])
        row=probe.sample();self.assertEqual(row['values']['MsMpEng']['machine_cpu_percent'],50)
        self.assertIsNone(row['values']['System']['machine_cpu_percent'])
    def test_error_from_collect_does_not_invent_measurement(self):
        probe,api=self.make();api.return_code=123;row=probe.sample()
        self.assertFalse(row['available']);self.assertEqual(row['values'],{})
    def test_negative_nan_above_machine100_are_unknown(self):
        probe,api=self.make()
        for value in (-1,float('nan'),1601.):
            api.data['MsMpEng_cpu']=value
            with self.subTest():self.assertIsNone(probe.sample()['values']['MsMpEng']['machine_cpu_percent'])
    def test_same_observer_owner_required_no_new_thread(self):
        owner=[1];probe,api=self.make(identity=lambda:owner[0]);owner[0]=2
        with self.assertRaisesRegex(ValueError,'OWNER'):probe.sample()
        self.assertEqual(api.calls,1)
    def test_cost_limit_closes_query_and_drops_untrustworthy_slow_sample(self):
        ticks=iter([0.,0.,0.,1.,1.06,1.06]);probe,api=self.make(clock=lambda:next(ticks))
        row=probe.sample();self.assertFalse(row['available']);self.assertIsNone(row['values'])
        self.assertEqual(probe.disabled_reason,'MEASUREMENT_COST_BUDGET_EXCEEDED')
        self.assertTrue(probe.cleanup);self.assertIsNone(probe.query)
    def test_close_is_idempotent_and_failed_close_not_reported_clean(self):
        probe,api=self.make();api.close_code=123
        self.assertFalse(probe.close());self.assertFalse(probe.cleanup)
        api.close_code=0;self.assertTrue(probe.close());calls=len(api.closed)
        self.assertTrue(probe.close());self.assertEqual(len(api.closed),calls)
    def test_unavailable_baseline_does_not_claim_valid_zero(self):
        api=Fake();api.return_code=123;probe=p.Probe(16,api=api)
        try:self.assertEqual(probe.sample()['reason'],'BASELINE_UNAVAILABLE')
        finally:self.assertTrue(probe.close())


if __name__=='__main__':
    guard=a.Guard();result=None
    try:
        guard.acquire();result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(SerialAttributionContracts))
    finally:guard.close()
    print(json.dumps(dict(contract_count=result.testsRun if result else 0,passed=bool(result and result.wasSuccessful()),
        cleanup_confirmed=guard.cleanup,actual_PDH_queries=False,product_child_executed=False)))
    raise SystemExit(0 if result and result.wasSuccessful() and guard.cleanup else 2)
