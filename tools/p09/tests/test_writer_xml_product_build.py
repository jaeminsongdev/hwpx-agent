import copy
import unittest
from unittest.mock import patch
import build_writer_xml_product as d

class WriterProductBuildTests(unittest.TestCase):
    def test_parent_rejects_failed_or_previous_source_generations(self):
        for state in ('FAILED_NOT_ACCEPTED','PASS_SOURCE_XML_REUSE_DELTA_AND_ALL68_LIB_UNITS_ONLY_NOT_FULL249_OR_GATE'):
            with self.assertRaises(ValueError):d.parent_scope(dict(state=state))

    def test_exact_new_target_and_suffix_recipe_only(self):
        r=d.recipe();self.assertEqual(r['executable_path'],d.executable_name())
        self.assertIn('p09-168-writer-xml-reuse',r['executable_path'])
        self.assertTrue(r['executable_path'].endswith('p152-r05.exe'))
        self.assertEqual(r['argv_without_cargo'][-2:],['-C','extra-filename=-p152-r05'])
        self.assertEqual(r['argv_without_cargo'][r['argv_without_cargo'].index('--target-dir')+1],str(d.TARGET))

    def test_original_profile_caps_and_unfiltered_runtime_plan(self):
        old=copy.deepcopy(d.c.POLICY);r=d.recipe()
        self.assertEqual(r['test_package_profile_config'],list(d.b.CONFIG));self.assertEqual(len(d.b.CONFIG),81)
        self.assertEqual((r['compile_maximum_seconds'],r['full249_maximum_seconds']),(600,1200))
        self.assertEqual(r['compile_admission_RAM_percent'],15);self.assertTrue(r['full249_unfiltered_required'])
        self.assertEqual(d.c.POLICY,old)

    def test_foreign_worker_is_rejected_without_launch(self):
        with patch.object(d.b,'worker',side_effect=AssertionError('NO_LAUNCH')):
            with self.assertRaises(ValueError):d.worker(d.b.task_for(4))

    def test_worker_adapter_restores_original_target(self):
        old=d.b.TARGET;calls=[]
        with patch.object(d.b,'worker',side_effect=lambda task:calls.append((task,d.b.TARGET,d.c.TARGET)) or 0):
            self.assertEqual(d.worker(d.b.task_for(5)),0)
        self.assertEqual(calls,[(d.b.task_for(5),d.TARGET,d.TARGET)]);self.assertEqual(d.b.TARGET,old)

    def test_no_old_executable_can_be_fresh_output(self):
        with self.assertRaises(ValueError):d.fresh_scope({d.executable_name():{}})

if __name__=='__main__':unittest.main()
