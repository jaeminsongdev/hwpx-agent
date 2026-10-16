import unittest
from types import FunctionType,SimpleNamespace as NS

M=BOUNDED=ACTUAL=COUNTS=None


class Tests(unittest.TestCase):
    def test_diagnostic_count_matches_original_encoder_on_small_packet(self):
        compact=dict(small='fixture',numbers=list(range(12)))
        encoded=BOUNDED.encode_compact(compact,lambda:None)
        self.assertEqual(M.diagnostic_wire_count(compact,lambda:None)['wire_bytes'],len(encoded.encode('ascii')))
    def test_all162_descriptors_and_context_survive_observation(self):
        self.assertEqual(len(ACTUAL.semantic['descriptors']),162)
        self.assertEqual(len(ACTUAL.compact['bindings']),162)
        self.assertEqual(ACTUAL.semantic['next_case'],165)
        self.assertEqual(ACTUAL.semantic['accepted_count_before'],158)
    def test_real_original_size_denial_is_not_promoted(self):
        if COUNTS['fits_wire']:
            self.assertIsNone(ACTUAL.error); self.assertIsInstance(ACTUAL.data,bytes)
        else:
            self.assertEqual(ACTUAL.error,'SUCCESSOR_WIRE_V2_ORIGINAL_16K_TRANSPORT')
            self.assertIsNone(ACTUAL.data); self.assertIsNone(ACTUAL.proof)
    def test_limits_remain_exact_and_dependency_was_restored(self):
        self.assertEqual(COUNTS['wire_limit_bytes'],16384); self.assertEqual(COUNTS['expanded_limit_bytes'],131072)
        self.assertTrue(ACTUAL.original_json_restored)
    def test_non_private_encoder_cannot_be_instrumented(self):
        def encode(*args): raise AssertionError('MUST_NOT_RUN')
        with self.assertRaises(ValueError): M.observe_encode(NS(encode=encode),None,{},lambda:None)
    def test_unrelated_original_failure_preserved_and_json_restored(self):
        marker=object()
        def encode(*args): raise ValueError('SYNTHETIC_UNRELATED_ORIGINAL_FAILURE')
        env=dict(encode.__globals__,__name__='p09_exact_packet_fixture',json=marker)
        fn=FunctionType(encode.__code__,env)
        with self.assertRaisesRegex(ValueError,'ONLY_REAL_WIRE_SIZE_DENIAL_EXPECTED'):
            M.observe_encode(NS(encode=fn),None,dict(prior_queue_pin={},prior_candidate_pin={}),lambda:None)
        self.assertIs(env['json'],marker)


if __name__=='__main__': unittest.main()
