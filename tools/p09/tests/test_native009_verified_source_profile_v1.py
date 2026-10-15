import copy
import unittest

MODULE=LINKED=GRAPH=REQUIRED=HINT=CHECK=READER=SCOPE=COUNTS=ENGINE=None


class Tests(unittest.TestCase):
    def test_actual_typed_immutable_policy_not_declaration(self):
        p=LINKED.state.policy
        self.assertIs(type(p),LINKED.state.alias.VerifiedPolicy)
        self.assertEqual(p.evidence(),HINT['closed_prebody_source_declaration']);self.assertEqual(p.before_run,4)
        with self.assertRaises(AttributeError):p.index=164

    def test_serialized_declaration_or_fake_token_cannot_authorize_binding(self):
        with self.assertRaises(ValueError):LINKED.connection.binding_api(LINKED.state.bindings,LINKED.state.alias,HINT['closed_prebody_source_declaration'])
        with self.assertRaises(ValueError):LINKED.state.alias.VerifiedPolicy(object(),165,4,MODULE.PRODUCER,[])

    def test_full_original_verifier_private_run9_inverse_only(self):
        proof=LINKED.state.verify_proof
        self.assertEqual((proof['old'],proof['new']),(8,9));self.assertTrue(proof['whole_code_inverse'])
        self.assertTrue(LINKED.state.original_verify.__globals__['__name__'].startswith('p09_exact_'))
        self.assertIn(8,LINKED.state.original_verify.__code__.co_consts)

    def test_raw_originals_fresh_initial_and_callback_reads(self):
        self.assertEqual(len(COUNTS),2);self.assertTrue(all(n>=2 for n in COUNTS.values()))
        self.assertEqual(READER.closed_source_policy.evidence(),LINKED.state.policy.evidence())

    def test_original_callback_and_worker_validators_not_substituted(self):
        self.assertIs(LINKED.callback_proof['original_parent_input_callback'],LINKED.original_scope)
        self.assertTrue(LINKED.original_scope.__code__.co_filename.replace('\\','/').endswith('current_queue_successor_runtime.py'))
        self.assertTrue(LINKED.callback_proof['fresh_closed_original_admission_before_original_parent_callback'])
        LINKED.api.validate(HINT)
        changed=copy.deepcopy(HINT);changed['run']=8
        with self.assertRaises(ValueError):LINKED.api.validate(changed)

    def test_all72_and_separate_executed_unknown_legacy_failure_roles(self):
        self.assertEqual(len(GRAPH.binding.descriptors()),72)
        p,_=GRAPH.binding.project(REQUIRED,CHECK);r=GRAPH.binding.representation(p)
        self.assertEqual(r['closed_prebody_source_policy'],LINKED.state.policy.evidence())
        self.assertIs(r['same_case_failed165_run007_provenance']['actual_failed_product_child_executed'],True)
        self.assertIsNone(r['same_case_failed165_run008_provenance']['actual_failed_product_child_executed'])
        for row in r['historical_validation_failures_provenance']['records']:self.assertFalse(row['original_failure_promoted'])

    def test_closed_pairs_are_only_exact_original2_and3(self):
        rows=LINKED.state.policy.descriptors();self.assertEqual(len(rows),2)
        self.assertEqual([r['semantic_original_pin']['path'].split('run')[-1] for r in rows],['002.v1.json','003.v1.json'])
        row=rows[0]
        with self.assertRaises(ValueError):GRAPH.binding_module.source.descriptor(dict(row['semantic_original_pin'],sha256='0'*64),row['physical_envelope_pin'],next_case=165)

    def test_isolated_runtime_and_no_default_module_mutation(self):
        self.assertIsNot(LINKED.isolated_runtime,LINKED.api.runtime)
        self.assertFalse(LINKED.default_modules_or_original_worker_validation_changed)
        self.assertIs(LINKED.api.runtime.current_input_scope,LINKED.isolated_runtime.current_input_scope)

    def test_no_worker_native_frame_or_go_authority(self):
        self.assertEqual(ENGINE.state.attempts,0);self.assertEqual(ENGINE.state.calls,0);self.assertFalse(ENGINE.state.completed)
        self.assertFalse(LINKED.Native_or_GO_authorized);self.assertEqual(ENGINE.window.WINDOW.SECONDS,10)
