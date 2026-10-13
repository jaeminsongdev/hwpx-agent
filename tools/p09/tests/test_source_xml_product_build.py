import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import build_source_xml_product as s

class SourceXmlProductBuildTests(unittest.TestCase):
    def test_parent_cannot_be_old_graph_or_failed_unit(self):
        for state in ('PASS_CURRENT_OBSERVED_GRAPH_BUILD_CLOSING_ONLY_NOT_LISTING_FULL249_OR_GATE',
                'PASS_SOURCE_XML_REUSE_DELTA_AND_UNIT_STOP_ACCOUNTED_ONLY_NOT_RUNTIME_OR_GATE'):
            with self.assertRaises(ValueError):s.parent_scope(dict(state=state))

    def test_fresh_r04_not_historical_executable(self):
        with self.assertRaises(ValueError):s.fresh_scope({s.p.b.executable_name(4):{}})
        with patch.object(s.p.s,'scoped_path',return_value=SimpleNamespace()):
            self.assertTrue(s.fresh_scope({}).endswith('p152-r04.exe'))

    def test_worker_only_current_task_and_adapter_restores(self):
        with self.assertRaises(ValueError):s.worker(s.p.b.task_for(3))
        with patch.object(s.d,'worker',side_effect=lambda task:(s.d.RUN,task)):
            self.assertEqual(s.worker(s.p.b.task_for(4)),(4,s.p.b.task_for(4)))
        self.assertEqual(s.d.RUN,3)

    def test_original_recipe_caps_and_profiles_unchanged(self):
        before=copy.deepcopy(s.p.c.POLICY);r=s.p.s.recipe(4)
        self.assertEqual(len(r['test_package_profile_config']),81)
        self.assertEqual(r['compile_maximum_seconds'],600)
        self.assertEqual(r['full249_maximum_seconds'],1200)
        self.assertEqual(r['compile_admission_RAM_percent'],15)
        self.assertIn('--offline',r['argv_without_cargo'])
        self.assertIn('--locked',r['argv_without_cargo'])
        self.assertEqual(s.p.c.POLICY,before)

if __name__=='__main__':unittest.main()
