"""Fixed connection code contracts; real130 oracle executes in guarded qualifier."""
import ast
import copy
import hashlib
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
import flat_current_queue_inherited_scope_runtime_v1 as m

RAW=DATA=ACTUAL=ROOT=LISTING=BODY=INHERITED=None


class InheritedScopeTests(unittest.TestCase):
    def test_original_binding_AST_exactly_restored(self):
        fn,proof=m.binding_projection(RAW)
        self.assertTrue(proof["original_binding_AST_restored_exactly"])
        self.assertEqual(proof["changed_validator_dependencies"],1)
        self.assertIs(fn.__globals__["_validate_previous"],m.previous_validation)

    def test_wrong_binding_hash_rejected(self):
        with self.assertRaises(ValueError):m.binding_projection(RAW[:-1]+b" ")

    def test_trailing_raw_bytes_rejected(self):
        with self.assertRaises(ValueError):m.binding_projection(RAW+b"\n")

    def test_missing_closed_dependency_rejected(self):
        raw=RAW.replace(b"acceptance.validate_candidate(q,row,listing",b"acceptance.other(q,row,listing")
        pin=dict(m.BASE_PIN,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        with patch.object(m,"BASE_PIN",pin):
            with self.assertRaises(ValueError):m.binding_projection(raw)

    def test_wrong_dependency_arguments_rejected(self):
        raw=RAW.replace(b"flat=CONFIG.index>116",b"flat=CONFIG.index>117")
        pin=dict(m.BASE_PIN,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        with patch.object(m,"BASE_PIN",pin):
            with self.assertRaises(ValueError):m.binding_projection(raw)

    def test_current_CONFIG_and_original_binding_not_mutated(self):
        code=m.base.binding.__code__;step=m.base.CONFIG
        m.binding_projection(RAW)
        self.assertIs(m.base.binding.__code__,code)
        self.assertIs(m.base.CONFIG,step)

    def test_data_shape_valid(self):
        self.assertEqual(m.validate_data(copy.deepcopy(DATA),m.base.CONFIG),DATA)

    def test_extra_DATA_payload_rejected(self):
        row=dict(DATA,ignored_input="forbidden")
        with self.assertRaises(ValueError):m.validate_data(row,m.base.CONFIG)

    def test_wrong_DATA_count_rejected(self):
        row=dict(DATA,before=123)
        with self.assertRaises(ValueError):m.validate_data(row,m.base.CONFIG)

    def test_wrong_BASE_pin_rejected(self):
        row=copy.deepcopy(DATA);row["original_base_runtime_pin"]["sha256"]="0"*64
        with self.assertRaises(ValueError):m.validate_data(row,m.base.CONFIG)

    def test_missing_controller_rejected(self):
        row=dict(DATA,connection_code_pins=DATA["connection_code_pins"][:1])
        with self.assertRaises(ValueError):m.validate_data(row,m.base.CONFIG)

    def test_wrong_qualification_path_rejected(self):
        row=copy.deepcopy(DATA);row["connection_qualification_pin"]["path"]="fixtures/not-authority.json"
        with self.assertRaises(ValueError):m.validate_data(row,m.base.CONFIG)

    def test_future_data_paths_fixed_without_recursive_modules(self):
        for index in (131,132,249):
            self.assertEqual(m.data_path(index),f"implementation/p09/evidence/p09-361-case{index}-inherited-scope-data001.v1.json")
        for index in (130,250,True):
            with self.assertRaises(ValueError):m.data_path(index)

    def test_context_targets_executed_controller(self):
        ctx=m.context(m.base.CONFIG)
        self.assertEqual((ctx.SELF,ctx.TEST,ctx.INDEX,ctx.BEFORE),(m.SELF,m.TEST,131,124))
        self.assertEqual(ctx.arguments(),[m.base.CONFIG.case,"--exact","--test-threads=1","--format=pretty","--color=never"])

    def test_template_preserves_entire_engine_code(self):
        old,_=m.source.template();new,proof=m.template()
        self.assertEqual(old.run_owned.__code__,new.run_owned.__code__)
        self.assertEqual(old.worker.__code__,new.worker.__code__)
        self.assertEqual(new.run_owned.__globals__["SELF"],m.SELF)
        self.assertTrue(proof["original_CPU_RAM_deadlines_and_costs_retained"])

    def test_actual_previous_full_oracle_passed_not_fixture(self):
        self.assertTrue(ACTUAL[1]["previous_actual_full_oracle_retained"])
        self.assertTrue(ACTUAL[1]["previous_runtime_context_bound_to_executed_code"])
        self.assertFalse(ACTUAL[1]["current_CONFIG_mutated"])
        self.assertEqual(ACTUAL[1]["original_validator_projection"]["input_count"],1936)

    def test_scope_derived_independently_not_actual_observations(self):
        expected=m.base.scope.extend(m.base.scope.compose(BODY["source_freeze"],
            list(m.base.scope.listing_inputs(LISTING).values())),INHERITED)
        expected=m.base.scope.extend(expected,m.base.scope.pins(ROOT["bootstrap_metadata"]["input_pins"]))
        m.a.exact(expected,m.base.scope.pins(ROOT["source_freeze"]),"REAL_FULL1936")

    def test_missing_inherited_scope_rejected(self):
        baseline=m.base.scope.extend(m.base.scope.compose(BODY["source_freeze"],
            list(m.base.scope.listing_inputs(LISTING).values())),m.base.scope.pins(ROOT["bootstrap_metadata"]["input_pins"]))
        with self.assertRaises(ValueError):m.a.exact(baseline,m.base.scope.pins(ROOT["source_freeze"]),"NO_SOURCE_OMISSION")

    def test_conflicting_inherited_pin_rejected(self):
        name=next(iter(INHERITED));pin=dict(INHERITED[name],sha256="0"*64)
        with self.assertRaises(ValueError):m.base.scope.extend(INHERITED,{name:pin})

    def test_invalid_previous_context_rejected_before_IO(self):
        wrong=NS(INDEX=129,BEFORE=122,CASE="wrong")
        with self.assertRaises(ValueError):m.previous_validation(None,None,LISTING,None,None,wrong)


if __name__=="__main__":unittest.main()
