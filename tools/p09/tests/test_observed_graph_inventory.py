import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import run_observed_graph_inventory as s


class ObservedGraphInventoryTests(unittest.TestCase):
    def test_wrong_task_cannot_select_old_exe(self):
        with self.assertRaises(ValueError):s.worker(s.i.task_for(1))

    def test_worker_selects_only_current_r03_list(self):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=True;return True
        calls=[]
        with patch.object(s.p.c,'Windows',return_value=SimpleNamespace(k=Kernel())), \
                patch.object(s.p.c.sys,'stdin',io.StringIO('P149_GO\n')),patch.object(s.p.c.shutil,'which',return_value='cargo'), \
                patch.object(s.i.subprocess,'call',side_effect=lambda a,**kw:calls.append(a) or 0):s.worker(s.i.task_for(3))
        self.assertEqual(calls,[[str(s.p.c.ROOT/s.p.b.executable_name(3)),'--list','--format=terse']])

    def test_stopped_or_old_closing_is_not_accepted(self):
        with self.assertRaises((ValueError,KeyError)):s.closing_scope(dict(state='PASS_CPU_STOP_ACCOUNTED_CURRENT_INPUTS_ONLY_NOT_PRODUCT_BUILD_OR_GATE'))
        with self.assertRaises((ValueError,KeyError)):s.closing_scope(dict(state='PASS_CURRENT_LIBTEST_BUILD_CLOSING_ONLY_NOT_COMPILED249_LISTING_RUNTIME_SQL_OR_GATE'))

    def test_receipt_is_pinned_to_current_build_not_old_inventory(self):
        self.assertNotEqual(s.CLOSING,s.i.CLOSING);self.assertEqual(s.d.RUN,3);self.assertEqual(s.CLOSING['bytes'],354808)


if __name__=='__main__':unittest.main()
