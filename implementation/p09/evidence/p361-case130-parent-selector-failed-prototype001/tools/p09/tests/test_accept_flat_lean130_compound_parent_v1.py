"""Exact selector tests; actual full prepare is executed by guarded qualifier."""
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
import accept_flat_lean130_compound_parent_v1 as m
RAW = API = None

class ParentSelectorTests(unittest.TestCase):
    def test_one_selector_and_undo_entire_code(self):
        old=API.prepare_projection(RAW);new=m.projection(RAW,API.prepare_projection)
        self.assertEqual(new.__code__.replace(co_consts=old.__code__.co_consts),old.__code__)
        self.assertNotIn("runtime_candidate_pin",new.__code__.co_consts)
        self.assertIn("preserved_failed_product_root_pin",new.__code__.co_consts)

    def test_original_namespace_not_mutated(self):
        old=API.prepare_projection(RAW);before=old.__code__.co_consts
        m.projection(RAW,lambda raw:old)
        self.assertEqual(old.__code__.co_consts,before)

    def test_other_case_rejected(self):
        with patch.object(m.base,"CONFIG",NS(index=131)):
            with self.assertRaises(ValueError):m.projection(RAW,API.prepare_projection)

    def test_missing_selector_rejected(self):
        def f():return None
        with self.assertRaises(ValueError):m.projection(b"",lambda raw:f)

    def test_duplicate_selector_rejected(self):
        old=API.prepare_projection(RAW)
        # Same text constants normally deduplicate: append an explicit second
        # code constant to test strict closed selector accounting.
        f=type(old)(old.__code__.replace(co_consts=old.__code__.co_consts+("runtime_candidate_pin",)),old.__globals__)
        with self.assertRaises(ValueError):m.projection(RAW,lambda raw:f)

    def test_full_validator_dependency_retained(self):
        old=API.prepare_projection(RAW);new=m.projection(RAW,API.prepare_projection)
        self.assertIs(new.__globals__["validate_candidate"],old.__globals__["validate_candidate"])
        self.assertEqual(new.__globals__["PASS"],API.PASS)

    def test_wrong_completed_root_rejected_before_io(self):
        with self.assertRaises(ValueError):m.prepare(None,dict(m.ROOT_PIN,sha256="0"*64))

    def test_no_generic_prior_runtime_PASS_alias(self):
        self.assertEqual(m.ROOT_PIN["path"],"implementation/p09/evidence/p09-361-case130-current-runtime-run001.v1.json")
        self.assertEqual(m.lean.source.root_path(m.base.CONFIG),m.ROOT_PIN["path"])

if __name__=="__main__":unittest.main()
