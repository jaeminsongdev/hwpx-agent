"""Exact selector tests; actual full prepare is executed by guarded qualifier."""
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
import accept_flat_lean130_compound_parent_v1 as m
RAW = PROJECTOR_RAW = API = LISTING = BODY = INHERITED = ROW = None

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

    def test_complete_expected_scope_independently_derived(self):
        expected=m.base.scope.extend(m.base.scope.compose(BODY["source_freeze"],
            list(m.base.scope.listing_inputs(LISTING).values())),INHERITED)
        expected=m.base.scope.extend(expected,m.base.scope.pins(ROW["bootstrap_metadata"]["input_pins"]))
        m.a.exact(expected,m.base.scope.pins(ROW["source_freeze"]),"ACTUAL_COMPLETE_SCOPE")
        self.assertEqual(len(expected),1936)

    def test_scope_conflict_rejected_not_overlaid(self):
        name=next(iter(INHERITED));wrong=dict(INHERITED[name],sha256="0"*64)
        with self.assertRaises(ValueError):m.base.scope.extend(INHERITED,{name:wrong})

    def test_missing_inherited_input_not_accepted_as_full_scope(self):
        baseline=m.base.scope.extend(m.base.scope.compose(BODY["source_freeze"],
            list(m.base.scope.listing_inputs(LISTING).values())),m.base.scope.pins(ROW["bootstrap_metadata"]["input_pins"]))
        self.assertEqual(len(baseline),1935)
        with self.assertRaises(ValueError):m.a.exact(baseline,m.base.scope.pins(ROW["source_freeze"]),"NO_OMISSION")

    def test_scoped_projector_uses_same_stronger_composition_twice(self):
        project,_=m.scoped_validator(API.validator,INHERITED)(PROJECTOR_RAW,m.lean.context(m.base.CONFIG))
        self.assertIs(project.__globals__["original"].scope,project.__globals__["ORACLE_SCOPE"])
        self.assertIs(project.__globals__["ORACLE_SCOPE"].pins,m.base.scope.pins)

    def test_original_global_scope_not_mutated(self):
        old,_=API.validator(PROJECTOR_RAW,m.lean.context(m.base.CONFIG))
        before=old.__globals__["original"].scope
        m.scoped_validator(API.validator,INHERITED)(PROJECTOR_RAW,m.lean.context(m.base.CONFIG))
        after,_=API.validator(PROJECTOR_RAW,m.lean.context(m.base.CONFIG))
        self.assertIs(before,after.__globals__["original"].scope)

if __name__=="__main__":unittest.main()
