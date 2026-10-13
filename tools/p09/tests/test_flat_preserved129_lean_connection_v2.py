"""Actual raw/receipt injection; no historical runner import or Native replay."""
import ast
import copy
import sys
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

import flat_preserved129_lean_connection_v2 as m

API = PROOF = DOCUMENTS = RAW = RAW_PREFLIGHT = RAW_LEAF = CHECKPOINT = None


class LeanConnectionTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(API, "guarded exact namespace injection required")
        self.assertTrue(callable(CHECKPOINT)); CHECKPOINT()

    def candidate(self, row=None):
        c = API.contract; d = DOCUMENTS
        return c.validate(d["original"],c.source.STOP_PIN,d["row"] if row is None else row,
            c.SOURCE_PIN,d["authority"],c.source.AUTHORITY_PIN,d["listing"],d["sourcequal"],
            c.prior.QUAL_PIN,d["previous"],d["connected"],d["observed"],d["real"],CHECKPOINT)

    def test_actual_full_native_and_body_oracle(self):
        result=self.candidate()
        self.assertEqual(result["state"],API.contract.PASS)
        self.assertEqual(result["whole_source_inputs"],1913)
        self.assertEqual(result["accepted_count_delta"],0)

    def test_all_five_original_ast_proofs(self):
        self.assertEqual(len(PROOF["original_AST_proofs"]),5)
        self.assertTrue(all(p["original_selected_function_and_constant_AST_unchanged"] for p in PROOF["original_AST_proofs"]))

    def test_source_only_three_validation_functions_no_run(self):
        source=API.contract.source
        self.assertTrue(all(callable(getattr(source,n)) for n in m.SOURCE_FUNCTIONS))
        self.assertFalse(hasattr(source,"run"));self.assertFalse(hasattr(source,"prepare"))

    def test_no_original_full_modules_imported(self):
        self.assertTrue(all(n not in sys.modules for n in ("close_flat_case129_preserved_source_v1",
            "review_flat_completed_body_stop_v1","validate_flat_case129_compound_v1",
            "validate_flat_case129_compound_observer_v2","flat_preserved129_compound_connection_v1")))

    def test_actual_compound_parent_consumed(self):
        self.assertGreater(len(API.parent_header(DOCUMENTS["accepted129"],m.base.CONFIG)),0)

    def test_old_qualification_expected_kind_isolated(self):
        self.assertEqual(API.qualification.__globals__["SELF"],m.SOURCES[4]["path"])
        self.assertEqual(API.binding.__globals__["SELF"],m.SELF)
        self.assertEqual(API.qualification.__globals__["QUAL_PATH"],m.LEGACY_QUAL["path"])

    def test_ordinary_runtime_PASS_alias_rejected(self):
        bad=dict(DOCUMENTS["accepted129"],runtime_candidate_pin=API.contract.source.STOP_PIN)
        with self.assertRaises(ValueError):API.parent_header(bad,m.base.CONFIG)

    def test_native_boundary_missing_rejected(self):
        row=dict(DOCUMENTS["row"]);row["source_frame"]=dict(row["source_frame"],actual_byte_boundaries=[])
        with self.assertRaises(ValueError):self.candidate(row)

    def test_native_handle_cleanup_failure_rejected(self):
        row=dict(DOCUMENTS["row"]);row["source_frame"]=copy.deepcopy(row["source_frame"])
        row["source_frame"]["handles"]["input_lock_handles_remaining"]=1
        with self.assertRaises(ValueError):self.candidate(row)

    def test_previous_scope_input_omission_rejected(self):
        row=dict(DOCUMENTS["row"],required_source_pins=DOCUMENTS["row"]["required_source_pins"][1:])
        with self.assertRaises(ValueError):self.candidate(row)

    def test_observer_query_cleanup_failure_rejected(self):
        row=dict(DOCUMENTS["row"]);row["source_observer_epoch"]=copy.deepcopy(row["source_observer_epoch"])
        row["source_observer_epoch"]["PDH_cleanup_confirmed"]=False
        with self.assertRaises(ValueError):self.candidate(row)

    def test_failed_body_root_stays_failed(self):
        self.assertEqual(DOCUMENTS["original"]["state"],"STOPPED_NOT_ACCEPTED")
        result=self.candidate()
        self.assertFalse(result["original_failed_frame_promoted_to_PASS"])
        self.assertFalse(result["successful_product_body_replayed"])

    def test_raw_code_hash_tamper_rejected(self):
        with self.assertRaises(ValueError):m.project(RAW[0]+b"\n",m.SOURCES[0],{})

    def test_unknown_function_not_silently_removed(self):
        with self.assertRaises(ValueError):m.project(RAW[0],m.SOURCES[0],{},("missing",))

    def test_original_predicate_function_ast_and_code(self):
        c=API.contract
        for index,fn in ((0,c.source.completed.review),(1,c.source.validate_frame),
            (2,c.prior.validate),(3,c.validate),(4,API.binding)):
            node=next(n for n in ast.parse(RAW[index].decode("utf-8")).body if isinstance(n,ast.FunctionDef) and n.name==fn.__name__)
            original=compile(ast.Module(body=[node],type_ignores=[]),m.SOURCES[index]["path"],"exec")
            expected=next(x for x in original.co_consts if hasattr(x,"co_name") and x.co_name==fn.__name__)
            self.assertEqual(fn.__code__,expected)

    def test_original_runtime_template_and_worker(self):
        engine,proof=m.template()
        self.assertEqual(engine.run_owned.__globals__["SELF"],m.SELF)
        self.assertEqual(engine.worker.__globals__["SELF"],m.SELF)
        self.assertTrue(proof["original_engine_bytecode_unchanged"])

    def test_parent_runner_original_code_and_new_binding(self):
        captured=[]
        def factory(code,env,argdefs=None):captured.append((code,env));return lambda run:run
        with patch.object(m,"FunctionType",side_effect=factory):self.assertEqual(m.run_owned(1),1)
        self.assertIs(captured[0][0],m.source.run_owned.__code__)
        self.assertIs(captured[0][1]["binding_attempt"],m.binding_attempt)

    def test_original_metadata10_tests_not_removed_from_preflight(self):
        old=m.source.preflight_projection(RAW_PREFLIGHT,RAW_LEAF)
        new=m.preflight_projection(RAW_PREFLIGHT,RAW_LEAF)
        self.assertEqual(new.__code__.replace(co_consts=old.__code__.co_consts),old.__code__)
        self.assertEqual(new.__globals__["SELF"],m.SELF)
        self.assertIs(new.__globals__["binding_attempt"],m.binding_attempt)

    def test_fresh_distinct_preflight002_destination(self):
        code=m.preflight_projection(RAW_PREFLIGHT,RAW_LEAF).__code__
        self.assertIn("-lean-compound-preflight002.v1.json",code.co_consts)
        self.assertNotIn("-source-stat-ancestor-preflight001.v1.json",code.co_consts)

    def test_new_validator_controllers_added_not_removed(self):
        self.assertTrue(set(m.source.CONTROLLERS)<=set(API.CONTROLLERS))
        self.assertTrue({m.SELF,m.TEST}<=set(API.CONTROLLERS))

    def test_prepare_original_code_expects_actual_compound_parent(self):
        fn=API.prepare_projection(DOCUMENTS["raw_prepare"])
        self.assertEqual(fn.__globals__["PASS"],API.PASS)
        self.assertIs(fn.__globals__["validate_candidate"],API.validate_candidate)

    def test_original_source_budget_and_limits_retained(self):
        c=API.contract
        required=m.base.scope.pins(DOCUMENTS["row"]["required_source_pins"])
        self.assertEqual(c.source.source_budget(required),DOCUMENTS["row"]["source_budget"])
        self.assertEqual(m.source.attempt(130),1)

    def test_no_automatic_product_retry(self):
        with self.assertRaises(ValueError):m.binding_attempt(None,2)

    def test_module_defaults_not_changed(self):
        self.assertFalse(PROOF["default_runtime_modules_mutated"])
        self.assertFalse(PROOF["imported_modules_hidden_or_removed"])
        self.assertFalse(PROOF["helper64_ceiling_raised"])


if __name__=="__main__":unittest.main()
