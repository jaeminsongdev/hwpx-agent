import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import run_source_xml_product_full as d

class SourceXmlProductFullTests(unittest.TestCase):
    def test_wrong_task_cannot_execute_historical_r03(self):
        with self.assertRaises(ValueError):d.worker(d.s.task_for(3))

    def test_current_r04_all249_no_filter_or_new_compile(self):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=True;return True
        calls=[];before=d.p.b.executable_name(1);current=d.p.b.executable_name(4)
        with patch.object(d.p.c,'Windows',return_value=SimpleNamespace(k=Kernel())), \
                patch.object(d.p.c.sys,'stdin',io.StringIO('P149_GO\n')), \
                patch.object(d.p.c.shutil,'which',return_value='cargo'), \
                patch.object(d.s,'observed_call',side_effect=lambda a,**kw:calls.append((a,kw)) or 0):
            d.worker(d.s.task_for(4))
        self.assertEqual(calls[0][0],[str(d.p.c.ROOT/current),'--test-threads=1','--format=terse'])
        self.assertEqual(calls[0][1]['env']['RUST_TEST_NOCAPTURE'],'0')
        self.assertEqual(d.p.b.executable_name(1),before);self.assertEqual(d.prior.RUN,3)

    def test_original1200_and_zero_filtered_acceptance_remain_required(self):
        for seconds in (180,600,1201):
            with self.assertRaises(ValueError):d.s.original.require_scope(seconds)
        with self.assertRaises(ValueError):
            d.s.original.full.validate_output('test result: ok. 248 passed; 0 failed; 0 ignored; 0 measured; 1 filtered out; finished in 1s\n')

    def test_old_or_build_only_closing_is_not_runtime_authority(self):
        for state in ('PASS_CURRENT_GRAPH_COMPILED249_INVENTORY_CLOSING_ONLY_NOT_FULL_RUNTIME_OR_GATE',
                'PASS_SOURCE_XML_PRODUCT_BUILD_CLOSING_ONLY_NOT_LISTING_FULL249_OR_GATE'):
            with self.assertRaises(ValueError):d.parent_scope(dict(state=state))

if __name__=='__main__':unittest.main()
