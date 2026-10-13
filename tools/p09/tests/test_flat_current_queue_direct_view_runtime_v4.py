"""Five new factory contracts; original v3 twelve and metadata ten run separately."""
import copy
import sys
import unittest
import flat_current_queue_direct_view_runtime_v4 as m

CHECKPOINT=lambda:None
V3_RAW=METADATA_RAW=METADATA_TEST_RAW=CHUNK_RAW=DATA=None
PREFLIGHT_NAMES=None


class TestNamespaceContracts(unittest.TestCase):
    def setUp(self):CHECKPOINT()

    def test_exact_v3_initialization_AST_and_no_module_import(self):
        source,proof=m.project_v3(V3_RAW)
        self.assertTrue(proof['all_original_v3_functions_constants_and_initialization_loop_AST_unchanged'])
        self.assertFalse(proof['full_v3_module_or_CLI_import_executed'])
        self.assertEqual(source.API.prepare.__code__,m.V3.API.prepare.__code__)
        self.assertIs(source.API.template,source.template)
        self.assertEqual(source.API.template.__globals__['SELF'],m.V3_PIN['path'])
        for name in ('flat_current_queue_direct_view_runtime_v3','test_flat_current_queue_metadata_connection'):
            self.assertNotIn(name,sys.modules)
        with self.assertRaises(ValueError):m.project_v3(V3_RAW+b'\n')

    def test_all_metadata10_class_methods_unchanged_and_drift_rejected(self):
        module=m.metadata_test_namespace(METADATA_TEST_RAW)
        suite=unittest.defaultTestLoader.loadTestsFromModule(module)
        self.assertEqual(suite.countTestCases(),10)
        with self.assertRaises(ValueError):m.metadata_test_namespace(METADATA_TEST_RAW+b'\n')

    def test_engine_and_native_budget_code_unchanged(self):
        old,_=m.V3.template();new,_=m.template()
        # Two exact raw compilations create distinct objects; compare complete
        # code values, not Python object addresses. Every original AST is bound.
        self.assertEqual(old.run_owned.__code__,new.run_owned.__code__)
        self.assertEqual(old.worker.__code__,new.worker.__code__)
        self.assertIs(new.run_owned.__globals__['native'],m.V3.NATIVE)
        self.assertIs(new.run_owned.__globals__['runtime_budget'],m.V3.ORACLE.runtime_budget)
        self.assertEqual(new.worker.__globals__['SELF'],m.SELF)
        self.assertEqual(m.API.prepare.__code__,m.V3.API.prepare.__code__)

    def test_preflight004_keeps_original10_and_whole_cost_without_test_import(self):
        fn=m.preflight_projection(METADATA_RAW,CHUNK_RAW)
        self.assertIn('-direct-view-preflight004.v1.json',fn.__code__.co_consts)
        self.assertIn('metadata_tests',fn.__code__.co_names)
        self.assertNotIn('test_flat_current_queue_metadata_connection',fn.__code__.co_names)
        self.assertIs(fn.__globals__['base'].stable.runtime_budget,m.V3.ORACLE.runtime_budget)
        self.assertIs(fn.__globals__['binding_attempt'],m.API.binding_attempt)

    def test_closed_DATA_and_real64_helper_inventory_without_hiding(self):
        self.assertEqual(len(PREFLIGHT_NAMES),64)
        self.assertIn(m.SELF,PREFLIGHT_NAMES)
        self.assertNotIn(m.METADATA_TEST_PIN['path'],PREFLIGHT_NAMES)
        self.assertFalse(m.PROOF['imported_modules_hidden_or_removed'])
        self.assertFalse(m.PROOF['helper_ceiling_raised'])
        self.assertEqual(m.validate_data(copy.deepcopy(DATA),m.base.CONFIG),DATA)
        with self.assertRaises(ValueError):m.validate_data(dict(DATA,skip_original10=True),m.base.CONFIG)
        wrong=copy.deepcopy(DATA);wrong['failed003_pin']=None
        with self.assertRaises(ValueError):m.validate_data(wrong,m.base.CONFIG)


if __name__=='__main__':unittest.main()
