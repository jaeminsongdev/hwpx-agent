"""Synthetic adversarial contracts only; no queue/Gate/product evidence."""
import ast
import copy
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

import held_native_view_oracle_v1 as m

CHECKPOINT = lambda: None
ORIGINAL_NODE = FOCUSED_FRAME = FOCUSED_REQUIRED = EXACT = FIELDS = None


class DirectOracleContracts(unittest.TestCase):
    def setUp(self):
        CHECKPOINT()

    def test_original_whole_AST_input_unchanged(self):
        before = ast.dump(ORIGINAL_NODE, include_attributes=False)
        projected = m.mechanics_projection(ORIGINAL_NODE)
        self.assertEqual(ast.dump(ORIGINAL_NODE, include_attributes=False), before)
        self.assertEqual(len(projected.body), len(ORIGINAL_NODE.body))
        self.assertEqual(sum(isinstance(n, ast.If) for n in ast.walk(projected)),
                         sum(isinstance(n, ast.If) for n in ast.walk(ORIGINAL_NODE)))

    def test_only_expected_physical_counters_zero(self):
        node = m.mechanics_projection(ORIGINAL_NODE)
        calls = {n.args[2].value:n for n in ast.walk(node) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name) and n.func.id == 'fields' and len(n.args) == 3
                 and isinstance(n.args[2], ast.Constant)}
        s = {k.arg:ast.unparse(k.value) for k in calls['BORROWED_STREAMS'].args[1].keywords}
        self.assertEqual(s['duplicate_handles_opened'], '0')
        self.assertEqual(s['duplicate_handles_closed'], '0')
        self.assertEqual(s['shared_offset_resets'], '2 * n')
        self.assertEqual(s['original_resource_and_byte_rate_guards_retained'], 'True')
        s = {k.arg:ast.unparse(k.value) for k in calls['NATIVE_PACING'].args[1].keywords}
        self.assertEqual(s['open_reservations'], 'held')
        self.assertEqual(s['maximum_opens_per_second'], '20')

    def test_duplicate_projection_cannot_run_twice(self):
        with self.assertRaises(ValueError):
            m.mechanics_projection(m.mechanics_projection(ORIGINAL_NODE))

    def test_absent_physical_term_rejected(self):
        node = copy.deepcopy(ORIGINAL_NODE)
        for n in ast.walk(node):
            if isinstance(n, ast.keyword) and n.arg == 'duplicate_handles_opened':
                n.value = ast.Constant(0)
        with self.assertRaises(ValueError):m.mechanics_projection(node)

    def test_missing_cost_equality_rejected(self):
        node = copy.deepcopy(ORIGINAL_NODE)
        for n in ast.walk(node):
            if isinstance(n, ast.Constant) and n.value == 'NO_HIDDEN_COST':n.value = 'DRIFT'
        with self.assertRaises(ValueError):m.mechanics_projection(node)

    def test_isolated_projector_globals_and_same_code(self):
        def function():return mechanics_projection, ORACLE_SCOPE
        old = NS(cost='old', preserved='same')
        from types import FunctionType
        original = FunctionType(function.__code__, dict(function.__globals__,
                   mechanics_projection='old_projection', ORACLE_SCOPE=old))
        before = dict(original.__globals__)
        connected = m.project_checker(original, old)
        self.assertIs(connected.__code__, original.__code__)
        self.assertEqual(original.__globals__, before)
        self.assertEqual(original(), ('old_projection', old))
        self.assertIs(connected()[0], m.mechanics_projection)
        self.assertIs(connected()[1].cost, m.cost)
        self.assertEqual(connected()[1].preserved, 'same')

    def test_unqualified_projector_rejected(self):
        with self.assertRaises(ValueError):m.project_checker(lambda:None, NS())

    def test_actual_focused_native_mechanics_without_product_promotion(self):
        row = m.native_mechanics(FOCUSED_FRAME, FOCUSED_REQUIRED, EXACT, FIELDS)
        self.assertEqual(row['physical_duplicates'], 0)
        self.assertTrue(row['native_mechanics_only_not_product_or_Gate'])
        self.assertEqual(FOCUSED_FRAME['frame_state'], 'CLOSED')

    def reject(self, frame):
        with self.assertRaises((ValueError, KeyError)):
            m.native_mechanics(frame, FOCUSED_REQUIRED, EXACT, FIELDS)

    def test_all_view_fact_drift_rejected(self):
        original = FOCUSED_FRAME['handles']['held_native_read_views']
        for key, value in original.items():
            CHECKPOINT()
            row = copy.deepcopy(FOCUSED_FRAME)
            drift = not value if type(value) is bool else value + 1
            row['handles']['held_native_read_views'][key] = drift
            row['handles']['borrowed_byte_streams'][key] = drift
            with self.subTest(key=key):self.reject(row)

    def test_view_summary_alias_drift_rejected(self):
        row = copy.deepcopy(FOCUSED_FRAME)
        row['handles']['borrowed_byte_streams']['duplicate_handles_opened'] = 1
        self.reject(row)

    def test_handle_close_history_rejected_after_eventual_close(self):
        row = copy.deepcopy(FOCUSED_FRAME)
        row['handles']['handle_close_failed_attempts'] = 1
        self.reject(row)

    def test_physical_handle_ceiling_rejected(self):
        row = copy.deepcopy(FOCUSED_FRAME)
        row['handles']['input_lock_handles_opened'] = 8193
        row['handles']['input_lock_handles_closed'] = 8193
        self.reject(row)

    def test_missing_original_identity_pass_rejected(self):
        row = copy.deepcopy(FOCUSED_FRAME)
        row['handles']['byte_stream_identity_checks'] -= 1
        self.reject(row)

    def test_pending_binding_or_incomplete_read_rejected(self):
        for key, value in [('active_reader_bindings', 1), ('active_byte_streams', 1),
                           ('input_lock_handles_remaining', 1)]:
            row = copy.deepcopy(FOCUSED_FRAME);row['handles'][key] = value;self.reject(row)

    def test_unchanged_open20_and_no_credit_burst(self):
        for key, value in [('maximum_opens_per_second', 21), ('open_reservations', 11),
                           ('idle_time_cannot_accumulate_multiple_open_credits', False)]:
            row = copy.deepcopy(FOCUSED_FRAME)
            row['handles']['native_open_pacing'][key] = value;self.reject(row)

    def test_actual_direct_cost_plus_distinct_half_second(self):
        before = m.views.model(FOCUSED_REQUIRED, 167)
        after = m.runtime_budget(FOCUSED_REQUIRED, 167)
        self.assertEqual(after['predicted_runtime_combined_seconds'],
                         before['predicted_runtime_combined_seconds'] + .5)
        self.assertEqual(after['final_postcleanup_distinct_sample_wait_allowance_seconds'], .5)
        self.assertFalse(after['GO_authorized'])
        self.assertFalse(after['direct_view_connection_qualified'])

    def test_original_inventory_and_acquisition_cannot_be_relaxed(self):
        for rate in [20, 14.0, True]:
            with self.assertRaises(ValueError):m.cost(FOCUSED_REQUIRED, rate)
        for count in [166, 168, 167.0, True]:
            with self.assertRaises(ValueError):m.runtime_budget(FOCUSED_REQUIRED, count)

    def test_original600_cannot_be_relaxed_for_final_sample(self):
        with patch.object(m.views, 'model', return_value=dict(predicted_runtime_combined_seconds=599.5)):
            with self.assertRaises(ValueError):m.runtime_budget(FOCUSED_REQUIRED, 167)

    def test_focused_closed_frame_cannot_pass_full_product_handler(self):
        original = NS(original=NS(additional_observer_evidence=lambda row:None,
            original=NS(scope=NS(pins=lambda p:FOCUSED_REQUIRED), exact=EXACT, fields=FIELDS)))
        row = dict(source_freeze=[], source_frame=FOCUSED_FRAME)
        with self.assertRaises(ValueError):m.retained_evidence(row, original)


if __name__ == '__main__':unittest.main()
