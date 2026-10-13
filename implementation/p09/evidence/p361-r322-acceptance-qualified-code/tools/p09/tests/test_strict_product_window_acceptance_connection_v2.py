import ast
import copy
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import strict_product_window_acceptance_connection_v2 as m
import native_pressure_full_connection_v1 as pressure

def raw():
    return ast.parse('def f():\n fields(p,dict(cool_distinct_sample_windows=2,maximum_pause_windows_per_entry=8),"BYTE_PRESSURE")\n fields(p,dict(clock_and_sleeper_and_checkpoint_retained=True),"PHASE")\n fields(p,dict(byte_boundary_cooling_policy_changed=False),"FAIL_FAST")\n fields(b,dict(product_allowance_seconds=20,unallocated_margin_seconds=60),"RUNTIME_COST")\n').body[0]
def prior(node):
    return pressure.changed_expectations(node,{
        "BYTE_PRESSURE":{"cool_distinct_sample_windows":(2,0),"maximum_pause_windows_per_entry":(8,0)},
        "PHASE":{"clock_and_sleeper_and_checkpoint_retained":(True,False)},
        "FAIL_FAST":{"byte_boundary_cooling_policy_changed":(False,True)}})

class Tests(unittest.TestCase):
    def test_actual_four_prior_pressure_markers_preserved_and_product15(self):
        old=prior(raw());new=m.product_expectation(old)
        for left,right in zip(old.body[:-1],new.body[:-1]):
            self.assertEqual(ast.dump(left,include_attributes=False),ast.dump(right,include_attributes=False))
        self.assertEqual(new.body[-1].value.args[1].keywords[0].value.value,15)
        self.assertEqual(new.body[-1].value.args[1].keywords[1].value.value,60)
    def test_v1_generic_undo_fails_but_isolated_undo_passes(self):
        old=prior(raw())
        with self.assertRaises(ValueError):pressure.changed_expectations(old,{"RUNTIME_COST":{"product_allowance_seconds":(20,15)}})
        self.assertIsInstance(m.product_expectation(old),ast.FunctionDef)
    def test_original_input_ast_not_mutated(self):
        old=prior(raw());before=copy.deepcopy(old);m.product_expectation(old)
        self.assertEqual(ast.dump(old,include_attributes=False),ast.dump(before,include_attributes=False))
    def test_missing_duplicate_wrong_product_expectation_rejected(self):
        for variant in (0,1,2):
            node=raw()
            if variant==0:node.body.pop()
            if variant==1:node.body.append(copy.deepcopy(node.body[-1]))
            if variant==2:node.body[-1].value.args[1].keywords[0].value.value=19
            with self.assertRaises(ValueError):m.product_expectation(node)
    def test_original_budget_cost_and_retained_bytecodes_unchanged(self):
        def budget(*a):return views.model(*a)
        def cost(*a):return runtime_budget(*a)
        def retained(*a):return runtime_budget(*a)
        original=NS(runtime_budget=budget,cost=cost,retained_evidence=retained,mechanics_projection=prior)
        new=m.direct_oracle(original,NS(model=lambda *a:None))
        self.assertIs(new.runtime_budget.__code__,budget.__code__)
        self.assertIs(new.cost.__code__,cost.__code__)
        self.assertIs(new.retained_evidence.__code__,retained.__code__)
        self.assertEqual(new.mechanics_projection(raw()).body[-1].value.args[1].keywords[0].value.value,15)

if __name__=="__main__":unittest.main()
