import copy
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import run_current_stored_inventory as s


class CurrentStoredInventoryTests(unittest.TestCase):
    def names(self):return [f'case_{i}' for i in range(249)]
    def listing(self):return '\n'.join(n+': test' for n in self.names())+'\n'
    def worker(self,go='P149_GO\n',member=True):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=member;return True
        calls=[]
        with patch.object(s.c,'Windows',return_value=SimpleNamespace(k=Kernel())),patch.object(s.c.sys,'stdin',io.StringIO(go)), \
                patch.object(s.c.shutil,'which',return_value='cargo'),patch.object(s.subprocess,'call',side_effect=lambda a,**kw:calls.append((a,kw)) or 0):
            result=s.worker(s.task_for(1))
        return result,calls
    def test_complete249_listing(self):s.validate_listing(self.listing(),self.names())
    def test_missing_duplicate_or_unknown_listing_denied(self):
        for text in (self.listing().replace('case_0: test\n',''),self.listing()+'case_0: test\n',self.listing()+'unknown\n'):
            with self.assertRaises(ValueError):s.validate_listing(text,self.names())
    def test_output_limit_and_benchmark_denied(self):
        for text in ('x'*32769,self.listing()+'1 benchmarks\n'):
            with self.assertRaises(ValueError):s.validate_listing(text,self.names())
    def test_job_membership_and_GO_required(self):
        for go,member in (('wrong\n',True),('P149_GO\n',False)):
            with self.assertRaises(ValueError):self.worker(go,member)
    def test_only_fresh_suffix_list_no_Cargo_or_filter(self):
        _,calls=self.worker();self.assertEqual(calls[0][0],[str(s.c.ROOT/s.build.executable_name(1)),'--list','--format=terse'])
        self.assertEqual(calls[0][1]['env']['RUST_TEST_NOCAPTURE'],'0')
    def test_closed_inventory_generation(self):
        self.assertEqual(s.run_for(s.task_for(1)),1)
        for value in (0,100,True,'1'):
            with self.assertRaises(ValueError):s.task_for(value)
    def test_original_policy_unchanged(self):
        before=copy.deepcopy(s.c.POLICY);self.worker();self.assertEqual(before,s.c.POLICY)
    def test_build_closing_immutable_not_stale_inventory(self):
        self.assertEqual(s.CLOSING['sha256'],'edde914ab29feae0286ff03ea0005c12604e42f3b53ab60b49d972502d514d5a')
        self.assertEqual(s.EXE_RUN,1)


if __name__=='__main__':unittest.main()
