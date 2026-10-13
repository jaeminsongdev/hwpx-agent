import copy
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import run_adaptive_source_xml_full as d

class AdaptiveSourceXmlFullTests(unittest.TestCase):
    def test_wrong_generation_denied_before_native_or_child(self):
        with self.assertRaises(ValueError):d.worker(d.s.task_for(3))

    def test_worker_current_r04_unfiltered_adaptive_callback_only(self):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=True;return True
        calls=[];before=d.s.observed_call;current=d.p.b.executable_name(4)
        with patch.object(d.p.c,'Windows',return_value=SimpleNamespace(k=Kernel())), \
                patch.object(d.p.c.sys,'stdin',io.StringIO('P149_GO\n')), \
                patch.object(d.p.c.shutil,'which',return_value='cargo'), \
                patch.object(d.adaptive,'observed_call',side_effect=lambda a,**kw:calls.append((a,kw)) or 0):
            self.assertEqual(d.worker(d.s.task_for(4)),0)
        self.assertEqual(calls[0][0],[str(d.p.c.ROOT/current),'--test-threads=1','--format=terse'])
        self.assertEqual(calls[0][1]['env']['RUST_TEST_NOCAPTURE'],'0');self.assertIs(d.s.observed_call,before)

    def test_component_does_not_accept_old_full_stop_or_product_build_as_parent(self):
        for state in ('PASS_SOURCE_XML_CURRENT_FULL_STOP_ACCOUNTED_ONLY_NOT_RUNTIME_OR_GATE',
                'PASS_SOURCE_XML_PRODUCT_BUILD_CLOSING_ONLY_NOT_LISTING_FULL249_OR_GATE'):
            with self.assertRaises(ValueError):d.parent_scope(dict(state=state))

    def test_original1200_and_all249_guard_predicates_unchanged(self):
        before=copy.deepcopy(d.p.c.POLICY);d.s.original.require_scope(1200)
        self.assertEqual(d.p.c.POLICY,before);self.assertEqual(len(d.p.b.CONFIG),81)
        self.assertEqual(d.s.original.MAXIMUM_SECONDS,1200)
        with self.assertRaises(ValueError):d.s.original.full.validate_output('test result: ok. 248 passed; 0 failed; 0 ignored; 0 measured; 1 filtered out;')

if __name__=='__main__':unittest.main()
