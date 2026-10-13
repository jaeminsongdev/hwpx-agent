import copy
import sys
import unittest
from pathlib import Path
from types import FunctionType, SimpleNamespace as NS
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import native_diagnostic_oracle_connection_v1 as oracle


class Tests(unittest.TestCase):
    def test_old_epoch_uses_original_not_new_validator(self):
        calls=[];row=dict(selected_test_index=145,serial_CPU_attribution={})
        with patch.object(oracle.diagnostic,"validate",side_effect=AssertionError("MUST_NOT_REBASE")):
            self.assertEqual(oracle.dispatch(lambda r:calls.append(r) or "legacy",row),"legacy")
        self.assertEqual(calls,[row])

    def test_new_epoch_cannot_use_old_PDH(self):
        with self.assertRaisesRegex(ValueError,"NEW_RUNTIME_MUST_HAVE_NATIVE_BACKEND"):
            oracle.dispatch(lambda r:True,dict(selected_test_index=146,serial_CPU_attribution={}))

    def test_new_epoch_full_native_validation_invoked(self):
        row=dict(selected_test_index=146,serial_CPU_attribution=dict(backend=oracle.diagnostic.BACKEND))
        with patch.object(oracle.diagnostic,"validate",return_value="native") as validator:
            self.assertEqual(oracle.dispatch(lambda r:None,row),"native")
        validator.assert_called_once_with(row)

    def test_historical_native_provenance_not_relabelled(self):
        with self.assertRaisesRegex(ValueError,"HISTORICAL_PROVENANCE_NOT_REBASED"):
            oracle.dispatch(lambda r:True,dict(selected_test_index=145,serial_CPU_attribution=dict(backend=oracle.diagnostic.BACKEND)))

    def test_runtime_cursor_strict(self):
        for index in (True,None,114,250):
            with self.assertRaises(ValueError):oracle.dispatch(lambda r:True,dict(selected_test_index=index))

    def test_full_validator_runs_before_diagnostic_dispatch(self):
        def actual_budget_binding(row): return "old"
        def validate_candidate(row):
            full(row)
            return actual_budget_binding(row)
        calls=[]
        env=dict(full=lambda row:calls.append("full"),actual_budget_binding=actual_budget_binding)
        exec(compile("def validate_candidate(row):\n full(row)\n return actual_budget_binding(row)\n",oracle.LEAF,"exec"),env)
        fn=env["validate_candidate"]
        updated,state=oracle.connect_candidate(fn)
        row=dict(selected_test_index=146,serial_CPU_attribution=dict(backend=oracle.diagnostic.BACKEND))
        with patch.object(oracle.diagnostic,"validate",side_effect=lambda row:calls.append("native") or True):
            self.assertTrue(updated(row))
        self.assertEqual(calls,["full","native"]);self.assertIs(updated.__code__,fn.__code__)
        self.assertIs(fn.__globals__["actual_budget_binding"],actual_budget_binding)

    def test_original_product_oracle_error_never_skipped(self):
        def actual_budget_binding(row): return True
        def validate_candidate(row):
            full(row)
            return actual_budget_binding(row)
        def fail(row):raise ValueError("ORIGINAL_FULL_SOURCE_REJECTED")
        env=dict(full=fail,actual_budget_binding=actual_budget_binding)
        exec(compile("def validate_candidate(row):\n full(row)\n return actual_budget_binding(row)\n",oracle.LEAF,"exec"),env)
        fn=env["validate_candidate"]
        updated,_=oracle.connect_candidate(fn)
        with patch.object(oracle.diagnostic,"validate") as validator:
            with self.assertRaisesRegex(ValueError,"ORIGINAL_FULL_SOURCE_REJECTED"):updated({})
            validator.assert_not_called()

    def test_wrong_leaf_missing_dependency_rejected(self):
        def leaf(row):return True
        fn=FunctionType(leaf.__code__.replace(co_filename=oracle.LEAF),{})
        with self.assertRaises(ValueError):oracle.connect_candidate(fn)


if __name__=="__main__":unittest.main()
