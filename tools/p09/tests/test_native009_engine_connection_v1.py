import copy
import unittest
from types import SimpleNamespace as NS

MODULE=None
LINKED=None
API=None
CHECKPOINT=None


class Tests(unittest.TestCase):
    def test_all_actual_root_task_physical_and_logical_identities_agree(self):
        self.assertEqual(LINKED.names.physical_run(165),9)
        self.assertEqual(LINKED.names.task(165),MODULE.TASK)
        self.assertEqual(LINKED.names.root_path(NS(index=165)),MODULE.ROOT_RECEIPT)
        self.assertEqual(LINKED.names.public_run(165,9),1)

    def test_original_full_worker_same_function_not_a_replacement(self):
        self.assertIs(LINKED.state.original,LINKED.original_worker)
        self.assertIs(LINKED.engine.worker,LINKED.original_worker)
        self.assertTrue(LINKED.original_worker.__code__.co_filename.replace('\\','/').endswith('run_case112_current_stored.py'))

    def test_single_argument_physical_adapter_not_stacked(self):
        self.assertTrue(LINKED.identity_proof['original_single_argument_adapter_not_stacked'])
        self.assertTrue(LINKED.identity_proof['original_identity_entire_code_inverse'])

    def test_private_factory_limit_inverse_and_original_not_modified(self):
        original=API.runtime.connect_factory;before=original.__code__
        fn,proof=MODULE.factory9(original)
        self.assertIs(original.__code__,before);self.assertTrue(proof['entire_code_inverse'])
        self.assertIs(fn.__defaults__,original.__defaults__);self.assertIs(fn.__closure__,original.__closure__)

    def test_unrelated_factory_cannot_be_projected(self):
        with self.assertRaises(ValueError):MODULE.factory9(lambda:None)

    def test_original10_window_and_complete69_binding(self):
        self.assertEqual(LINKED.window.WINDOW.SECONDS,10)
        self.assertEqual(len(LINKED.graph.binding.descriptors()),69)
        self.assertEqual(LINKED.graph.worker.TASK,MODULE.TASK)

    def test_worker_once_only_connector_exists_but_not_executed(self):
        self.assertEqual(LINKED.state.attempts,0);self.assertEqual(LINKED.state.calls,0)
        self.assertFalse(LINKED.state.completed);self.assertTrue(callable(LINKED.execute))

    def test_real_original_policy_and_binding_same_graph(self):
        self.assertEqual(LINKED.policy.binding.descriptors(),LINKED.graph.binding.descriptors())
        self.assertTrue(LINKED.worker_proof['whole_original_worker_body_retained'])
        self.assertTrue(LINKED.worker_proof['current_exact_task_and_once_only_policy_connected'])

    def test_no_native_or_GO_authority_from_composition(self):
        self.assertFalse(LINKED.product_Native_or_GO_authorized)
        self.assertFalse(LINKED.whole_Native009_source_Frame_qualified)

    def test_old_names_still_original_not_run008_renamed(self):
        self.assertTrue(LINKED.identity_proof['original_template_chain_code_defaults_and_closures_retained'])
        self.assertEqual(LINKED.names.public_run(164,1),1)
