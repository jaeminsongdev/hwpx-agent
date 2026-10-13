import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import run_source_xml_product_inventory as s

class SourceXmlProductInventoryTests(unittest.TestCase):
    def test_wrong_task_cannot_select_old_r03(self):
        with self.assertRaises(ValueError):s.worker(s.i.task_for(3))

    def test_worker_selects_only_current_r04_list(self):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=True;return True
        calls=[]
        with patch.object(s.p.c,'Windows',return_value=SimpleNamespace(k=Kernel())), \
                patch.object(s.p.c.sys,'stdin',io.StringIO('P149_GO\n')), \
                patch.object(s.p.c.shutil,'which',return_value='cargo'), \
                patch.object(s.i.subprocess,'call',side_effect=lambda a,**kw:calls.append(a) or 0):
            s.worker(s.i.task_for(4))
        self.assertEqual(calls,[[str(s.p.c.ROOT/s.p.b.executable_name(4)),'--list','--format=terse']])

    def test_old_or_stopped_compile_closing_cannot_pass(self):
        for state in ('PASS_CURRENT_OBSERVED_GRAPH_BUILD_CLOSING_ONLY_NOT_LISTING_FULL249_OR_GATE',
                'PASS_SOURCE_XML_PRODUCT_BUILD_STOP_ACCOUNTED_ONLY_NOT_BUILD_OR_GATE'):
            with self.assertRaises(ValueError):s.closing_scope(dict(state=state))

    def test_current_compile_and_library_closures_are_distinct(self):
        self.assertNotEqual(s.CLOSING,s.prior.CLOSING)
        self.assertNotEqual(s.CLOSING,s.d.PARENT)
        self.assertEqual(s.d.RUN,4)
        self.assertTrue(s.CLOSING['path'].endswith('p09-162-source-xml-product-build.terminal-audit-run01.v1.json'))

if __name__=='__main__':unittest.main()
