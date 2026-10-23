"""Exact original budget function with synthetic model data; no Native or IO."""
import ast
from types import SimpleNamespace as NS
import unittest
import conservative_maintenance as c
import native011_current_epoch_inventory_budget as inventory


def fixture():
    raw=(c.ROOT/inventory.SOURCE['path']).read_bytes()
    node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='runtime_budget')
    def require(ok,code):
        if not ok:raise ValueError(code)
    def model(required,requests):
        return dict(predicted_runtime_combined_seconds=100+requests/20,unchanged_lock_deadline_seconds=600,
                    unallocated_margin_seconds=60)
    env=dict(require=require,views=NS(model=model),INVENTORY_REQUESTS=167,FINAL_SAMPLE_SECONDS=.5)
    exec(compile(ast.Module(body=[node],type_ignores=[]),inventory.SOURCE['path'],'exec'),env)
    return env['runtime_budget']


class InventoryBudgetContracts(unittest.TestCase):
    def test_whole_original_code_only_count_identity_data_change_and_actual_cost_increases(self):
        original=fixture();current,proof=inventory.bind(original,173)
        self.assertIs(current.__code__,original.__code__)
        self.assertEqual(original.__globals__['INVENTORY_REQUESTS'],167)
        self.assertEqual(current.__globals__['INVENTORY_REQUESTS'],173)
        self.assertAlmostEqual(current({},173)['predicted_runtime_combined_seconds']
            -original({},167)['predicted_runtime_combined_seconds'],6/20)
        self.assertFalse(proof['deadline600_or_margin60_or_decoder5_or_readiness15_changed'])

    def test_wrong_runtime_count_still_fails_original_equality_guard(self):
        current,_=inventory.bind(fixture(),173)
        for value in (167,172,True):
            with self.assertRaisesRegex(ValueError,'UNCHANGED_WHOLE_RUST_INVENTORY'):current({},value)

    def test_unbounded_noninteger_or_already_projected_identity_rejected(self):
        for value in (0,8193,True,None,'173'):
            with self.assertRaisesRegex(ValueError,'ACTUAL_BOUNDED_INVENTORY_COUNT'):
                inventory.bind(fixture(),value)
        projected,_=inventory.bind(fixture(),173)
        with self.assertRaisesRegex(ValueError,'ORIGINAL167_IDENTITY_NOT_ALREADY_PROJECTED'):
            inventory.bind(projected,173)
