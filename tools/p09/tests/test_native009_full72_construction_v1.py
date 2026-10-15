import unittest

MODULE=CONNECTED=SOURCE=GRAPH=HELPERS=INHERITED=SCOPE=API=GUARD=IMPORT_PROOFS=None


class Tests(unittest.TestCase):
    def test_same_original_parent_and_worker_no_execution(self):
        c=CONNECTED
        self.assertIs(c.parent_state.original,c.original_run)
        self.assertIs(c.parent.worker,c.original_worker)
        self.assertEqual((c.parent_state.attempts,c.built.state.attempts,c.built.state.calls),(0,0,0))
        self.assertIs(c.parent.run_owned.__globals__,c.original_run.__globals__)

    def test_actual_projected_Frame_class_contains_original_no_instance(self):
        c=CONNECTED
        original=c.original_run.__globals__['native'].frames.Frame
        self.assertIn(original,c.frame.__mro__)
        self.assertIsNot(c.frame,original)
        self.assertEqual(c.parent_state.frames,[])
        self.assertTrue(callable(c.frame.acquire));self.assertTrue(callable(c.frame.close))

    def test_original_outer_and_one_static_connection_unexecuted(self):
        self.assertTrue(callable(CONNECTED.outer))
        self.assertEqual(CONNECTED.outer_state['actual_local_bindings'],0)
        self.assertEqual(CONNECTED.outer_state['static_leaf_connections'],1)
        self.assertEqual(CONNECTED.callback_calls,[])

    def test_whole_independent_oracle_inverse_not_candidate_observations(self):
        c=CONNECTED;original=c.legacy.CURRENT.M.validate_candidate
        inverse=API.metadata.project(c.checker.validate_candidate,c.checker.environment,{165:160})
        self.assertEqual(inverse.__code__,original.__code__)
        self.assertIs(inverse.__defaults__,original.__defaults__)
        self.assertIs(inverse.__closure__,original.__closure__)
        self.assertTrue(c.oracle_proof['independent_declared_scope_not_current_observations'])
        self.assertEqual(c.checker.projectors,[])

    def test_current165_and_strict10_in_both_parent_and_oracle(self):
        c=CONNECTED
        self.assertEqual((c.checker.environment['base'].CONFIG.index,c.checker.environment['base'].CONFIG.before),(165,158))
        self.assertEqual(c.checker.environment['prior'].WINDOW.SECONDS,10)
        self.assertEqual(c.built.window.WINDOW.SECONDS,10)
        self.assertEqual(c.built.names.physical_run(165),9)
        self.assertEqual(c.built.names.public_run(165,9),1)

    def test_fresh_verified_Source_and_all72_failure_roles_preserved(self):
        self.assertIs(type(SOURCE.state.policy),SOURCE.state.alias.VerifiedPolicy)
        self.assertEqual(len(GRAPH.binding.descriptors()),72)
        projection,_=GRAPH.binding.project(CONNECTED.oracle_inherited,GUARD.check)
        representation=GRAPH.binding.representation(projection)
        self.assertIs(representation['same_case_failed165_run007_provenance']['actual_failed_product_child_executed'],True)
        self.assertIsNone(representation['same_case_failed165_run008_provenance']['actual_failed_product_child_executed'])
        self.assertEqual(representation['closed_prebody_source_policy'],SOURCE.state.policy.evidence())

    def test_all_inherited_declarations_retained_not_whole_byte_PASS(self):
        required,_=GRAPH.binding.semantic_union(SCOPE.extend(INHERITED,CONNECTED.oracle_inherited),GUARD.check)
        for name,pin in INHERITED.items():
            if name not in GRAPH.binding.reverse:self.assertEqual(required[name],pin)
        self.assertFalse(CONNECTED.oracle_proof['actual_current_candidate_or_Native_or_product_qualified'])

    def test_real_helper_inventory_before_tests_without_hiding_or_cap_raise(self):
        self.assertTrue(HELPERS['observed_before_project_test_module_load'])
        self.assertLessEqual(HELPERS['Native_count'],64)
        self.assertFalse(HELPERS['modules_removed_hidden_or_bound_increased'])
        self.assertEqual(HELPERS['Native_count'],len(set(HELPERS['default_imported_helpers'])|set(HELPERS['explicit_original_Native_helpers'])))
        for name in ('current_queue_successor_binding','flat_current_queue_product_window_runtime_v18','flat_preserved129_lean_connection_v2'):
            self.assertNotIn('tools/p09/'+name+'.py',HELPERS['default_imported_helpers'])
        self.assertEqual(len(IMPORT_PROOFS),1)
        self.assertIn('validate_worker_hint',IMPORT_PROOFS[0]['functions'])
        self.assertTrue(IMPORT_PROOFS[0]['whole_original_function_bodies_retained'])
        self.assertFalse(IMPORT_PROOFS[0]['default_modules_mutated_or_hidden'])
