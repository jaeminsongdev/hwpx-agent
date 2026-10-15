import copy
import unittest

API=GRAPH=ROW=REQUIRED=INHERITED=RUST=ACTUAL_RUST=CHECK=LINKED=None


class Tests(unittest.TestCase):
    def test_whole_original_parent_callback_not_replaced(self):
        fn=API.runtime.current_input_scope
        self.assertEqual(fn.__name__,'current_input_scope')
        self.assertTrue(fn.__code__.co_filename.replace('\\','/').endswith('current_queue_successor_runtime.py'))
        self.assertTrue(fn.__globals__['__name__'].startswith('p09_exact_'))
        self.assertTrue(ROW['original_parent_callback_body_unchanged'])

    def test_all72_and_every_predecessor_declared_input_preserved(self):
        self.assertEqual(len(GRAPH.binding.descriptors()),72)
        self.assertTrue(all(REQUIRED.get(n)==pin for n,pin in INHERITED.items()))
        self.assertEqual(ROW['semantic_inputs'],ROW['physical_inputs'])

    def test_current_and_final_rust_and_original_cost_limits(self):
        self.assertEqual(RUST,ACTUAL_RUST);self.assertEqual(len(RUST),787)
        b=ROW['original_complete_runtime_budget']
        self.assertEqual(b['unchanged_lock_deadline_seconds'],600);self.assertEqual(b['unallocated_margin_seconds'],60)
        self.assertEqual(b['aggregate_envelope_decoder_allowance_seconds'],5.0)
        self.assertEqual(ROW['additional_readiness_seconds_without_old_allowance_credit'],15)
        self.assertLess(ROW['predicted_complete_seconds_with_readiness'],600)

    def test_failure_roles_are_not_promoted_by_parent_metadata(self):
        p,_=GRAPH.binding.project(REQUIRED,CHECK);r=GRAPH.binding.representation(p)
        self.assertIs(r['same_case_failed165_run007_provenance']['actual_failed_product_child_executed'],True)
        self.assertIsNone(r['same_case_failed165_run008_provenance']['actual_failed_product_child_executed'])
        for failure in r['historical_validation_failures_provenance']['records']:self.assertFalse(failure['original_failure_promoted'])

    def test_missing_original_and_changed_alias_still_reject(self):
        descriptor=GRAPH.binding.descriptors()[-1];rows=copy.deepcopy(REQUIRED)
        rows.pop(descriptor['semantic_original_pin']['path'])
        # Preparation inheritance intentionally restores its exact declaration;
        # conflicting bytes must still fail instead of being rebased.
        rows[descriptor['semantic_original_pin']['path']]=dict(descriptor['semantic_original_pin'],sha256='0'*64)
        with self.assertRaises(ValueError):GRAPH.binding.semantic_union(rows,CHECK)

    def test_no_worker_frame_native_or_product_authorization(self):
        self.assertEqual(LINKED.state.attempts,0);self.assertEqual(LINKED.state.calls,0);self.assertFalse(LINKED.state.completed)
        self.assertEqual(LINKED.window.WINDOW.SECONDS,10)
        for key in ('GO_authorized','actual_worker_product_or_Native_executed','current_full_source_hash_Frame_or_dispatch_qualified','whole_Native_helper64_qualified'):
            self.assertIs(ROW[key],False)
