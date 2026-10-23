"""Exact original constructor inverse for the diagnostic driver only."""
from types import SimpleNamespace as NS
import unittest
import conservative_maintenance as c
import native011_ready_scope_connection as control


class ReadonlyProjectionContracts(unittest.TestCase):
    def test_original_constructor_inverse_retains_guards_and_only_adds_driver_sites(self):
        raw=(c.ROOT/control.ORIGINAL['path']).read_bytes()
        driver=NS(output='implementation/p09/evidence/model-readonly.json')
        call,proof=control.project(raw,{},None,None,driver=driver)
        self.assertTrue(proof['entire_original_constructor_AST_inverse'])
        self.assertEqual(proof['readonly_driver_sites'],3)
        self.assertEqual(proof['exclusive_new_output'],driver.output)
        self.assertIs(call.__globals__['_readonly_driver'],driver)
        self.assertIn('finish',call.__code__.co_names);self.assertIn('close',call.__code__.co_names)
    def test_default_construction_still_has_no_runtime_driver_sites(self):
        raw=(c.ROOT/control.ORIGINAL['path']).read_bytes();_,proof=control.project(raw,{},None,None)
        self.assertEqual(proof['readonly_driver_sites'],0)
    def test_changed_original_source_is_not_accepted_with_driver(self):
        raw=(c.ROOT/control.ORIGINAL['path']).read_bytes()
        with self.assertRaisesRegex(ValueError,'EXACT_FULL_ORIGINAL_SHARED_CONSTRUCTOR'):
            control.project(raw+b'\n',{},None,None,driver=NS(output='model'))
