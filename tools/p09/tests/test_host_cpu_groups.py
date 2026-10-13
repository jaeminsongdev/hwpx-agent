import ctypes
import copy
import unittest
import host_cpu_group_observer as s
import probe_host_cpu_groups as probe
from test_host_cpu_observer import array,Fake
from test_probe_host_cpu_observer import payload


def select(cpu,pids,baseline=None):
    return s.select(cpu,pids,baseline if baseline is not None else s.pid_sets(pids),16)


class GroupCPUObserverTests(unittest.TestCase):
    def test_duplicate_values_preserved(self):self.assertEqual(s.decode(*array([('a',1,0),('a',2,0)])),{'a':[1.,2.]})
    def test_group_no_false_pid(self):
        row,_=select({'chatgpt':[16.,32.]},{'chatgpt':[50.,60.]});item=row['top'][0]
        self.assertEqual(item['machine_cpu_percent'],3);self.assertIsNone(item['pid']);self.assertEqual(item['identity_granularity'],'group')
        self.assertEqual(row['ambiguous_instances'],2)
    def test_pid_set_order_not_identity(self):
        row,_=select({'a':[16.,32.]},{'a':[60.,50.]},{'a':frozenset((50,60))})
        self.assertEqual(row['stable_instance_count'],2)
    def test_changed_pid_set_not_accepted(self):
        row,_=select({'a':[16.,32.]},{'a':[60.,51.]},{'a':frozenset((50,60))})
        self.assertEqual(row['top'],[]);self.assertEqual(row['unstable_instances'],2)
    def test_partial_unknown_group_not_zero_or_partial_sum(self):
        row,_=select({'a':[16.,None]},{'a':[50.,60.]})
        self.assertEqual(row['top'],[]);self.assertEqual(row['unavailable_instances'],2)
    def test_group_count_mismatch(self):
        row,_=select({'a':[16.]},{'a':[50.,60.]})
        self.assertEqual(row['top'],[]);self.assertEqual(row['unavailable_instances'],1)
    def test_singleton_exact_pid_and_owned(self):
        row,_=s.select({'msmpeng':[1600.]},{'msmpeng':[50.]},{'msmpeng':frozenset((50,))},16,(50,))
        self.assertEqual(row['top'][0]['pid'],50);self.assertEqual(row['top'][0]['machine_cpu_percent'],100)
        self.assertEqual(row['top'][0]['owned_member_count'],1);self.assertFalse(row['causal_attribution'])
    def test_duplicate_pid_rejected(self):
        for pids in ({'a':[50.,50.]},{'a':[50.],'b':[50.]}):
            with self.assertRaises(ValueError):s.pid_sets(pids)
    def test_buffer_pointer_checks_preserved(self):
        b,n,c=array([('a',1,0)]);ctypes.cast(b,ctypes.POINTER(s.old.Item))[0].name=1
        with self.assertRaises(ValueError):s.decode(b,n,c)
    def test_native_flow_and_cleanup(self):
        class API(Fake):
            def PdhAddEnglishCounterW(self,q,path,user,out):out._obj.value=s.PATHS.index(path)+1;return 0
        api=API();o=s.Observer(16,api);self.assertIsNone(o.collect());self.assertEqual(o.collect()['top'][0]['pid'],50)
        o.close();self.assertEqual(api.closed,1)
    def test_validator_accepts_group_only_scope(self):
        row=payload()
        for sample in row['samples']:
            sample['observation']=select({'chatgpt':[16.,32.]},{'chatgpt':[50.,60.]})[0]
        self.assertIs(probe.validate_payload(row),row)
        row['samples'][0]['observation']['top'][0]['pid']=50
        with self.assertRaises(ValueError):probe.validate_payload(row)
    def test_contract_does_not_change_original_v2(self):
        self.assertIn('Process V2',s.old.PATHS[0]);self.assertNotIn('Process V2',s.PATHS[0])


if __name__=='__main__':unittest.main()
