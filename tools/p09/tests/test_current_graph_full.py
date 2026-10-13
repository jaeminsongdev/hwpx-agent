import copy
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import run_current_graph_full as d


class CurrentGraphFullTests(unittest.TestCase):
    def test_wrong_task_cannot_execute_historical_full(self):
        with self.assertRaises(ValueError):d.worker(d.s.task_for(1))

    def test_worker_current_r03_all249_no_filter(self):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=True;return True
        calls=[];before=d.p.b.executable_name(1);current=d.p.b.executable_name(3)
        with patch.object(d.p.c,'Windows',return_value=SimpleNamespace(k=Kernel())), \
                patch.object(d.p.c.sys,'stdin',io.StringIO('P149_GO\n')),patch.object(d.p.c.shutil,'which',return_value='cargo'), \
                patch.object(d.s,'observed_call',side_effect=lambda a,**kw:calls.append((a,kw)) or 0):d.worker(d.s.task_for(3))
        self.assertEqual(calls[0][0],[str(d.p.c.ROOT/current),'--test-threads=1','--format=terse'])
        self.assertEqual(calls[0][1]['env']['RUST_TEST_NOCAPTURE'],'0');self.assertEqual(d.p.b.executable_name(1),before)

    def test_shorter_scope_or_filtered_capture_is_rejected(self):
        for seconds in (180,600,1201):
            with self.assertRaises(ValueError):d.s.original.require_scope(seconds)
        with self.assertRaises(ValueError):d.s.original.full.validate_output('test result: ok. 248 passed; 0 failed; 0 ignored; 0 measured; 1 filtered out; finished in 1s\n')

    def test_original_caps_and_full_profile_are_unchanged(self):
        before=copy.deepcopy(d.p.c.POLICY);d.s.original.require_scope(1200)
        self.assertEqual(d.p.c.POLICY,before);self.assertEqual(d.s.original.MAXIMUM_SECONDS,1200)
        self.assertEqual(len(d.p.b.CONFIG),81);self.assertEqual(d.s.MAX_SAVED,10)

    def test_stale_build_or_stop_is_not_compiled249_authority(self):
        for state in ('PASS_CURRENT_OBSERVED_GRAPH_BUILD_CLOSING_ONLY_NOT_LISTING_FULL249_OR_GATE','PASS_CPU_STOP_ACCOUNTED_CURRENT_INPUTS_ONLY_NOT_PRODUCT_BUILD_OR_GATE'):
            with self.assertRaises((ValueError,KeyError)):d.parent_scope(dict(state=state))


if __name__=='__main__':unittest.main()
