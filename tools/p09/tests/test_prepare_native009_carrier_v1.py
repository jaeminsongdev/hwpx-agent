import copy
import unittest

MODULE=FAILURE=RAW=None


class Tests(unittest.TestCase):
    def test_exact_real_failure_and_original_are_valid(self):
        MODULE.validate_projection(FAILURE); MODULE.exact_original(MODULE.ORIGINAL,RAW)
    def test_failure_cannot_be_promoted_or_reclassified_as_prebody(self):
        for delta in (dict(state='PASS'),dict(phase='admission'),dict(stop='STOP_STRICT_PRODUCT_WINDOW'),dict(product_complete=True)):
            with self.assertRaises(ValueError): MODULE.validate_projection(dict(FAILURE,**delta))
    def test_actual_body_execution_is_true_not_unknown_or_false(self):
        for field in ('body','actual_child','worker','assigned','writer'):
            for value in (False,None):
                with self.assertRaises(ValueError): MODULE.validate_projection(dict(FAILURE,**{field:value}))
    def test_original_cleanup_and_closed_partial_frame_are_mandatory(self):
        for delta in (dict(cleanup=False),dict(tree_empty=False),dict(registered=True),dict(handles_remaining=1),dict(readers=1),dict(streams=1)):
            with self.assertRaises(ValueError): MODULE.validate_projection(dict(FAILURE,**delta))
    def test_one_boundary_is_not_claimed_as_two_or_committed(self):
        for delta in (dict(completed_boundaries=2),dict(frame_state='COMMITTED'),dict(Native_qualified=True),dict(candidate_qualified=True)):
            with self.assertRaises(ValueError): MODULE.validate_projection(dict(FAILURE,**delta))
    def test_case_args_go_and_capture_are_exact(self):
        for delta in (dict(index=164),dict(arguments=[]),dict(GO=0),dict(captures=2),dict(capture_complete=False),dict(ready=False)):
            with self.assertRaises(ValueError): MODULE.validate_projection(dict(FAILURE,**delta))
    def test_original_windows_and_partial_decoder_limits_are_not_widened(self):
        for delta in (dict(product_window=20),dict(ready_limit=30),dict(decoder_limit=10.0),dict(GO_seconds=10.01),dict(ready_seconds=15.01),dict(decoder_work=5.01)):
            with self.assertRaises(ValueError): MODULE.validate_projection(dict(FAILURE,**delta))
    def test_boolean_numbers_nan_and_missing_values_are_rejected(self):
        for delta in (dict(accepted_delta=False),dict(completed_boundaries=True),dict(GO_seconds=float('nan')),dict(decoder_work=None)):
            with self.assertRaises(ValueError): MODULE.validate_projection(dict(FAILURE,**delta))
    def test_original_pin_size_hash_and_finite_new_destination(self):
        for pin in (dict(MODULE.ORIGINAL,bytes=1),dict(MODULE.ORIGINAL,sha256='0'*64)):
            with self.assertRaises(ValueError): MODULE.exact_original(pin,RAW)
        self.assertNotEqual(MODULE.destination(1),MODULE.ORIGINAL['path'])
        for generation in (True,0,9):
            with self.assertRaises(ValueError): MODULE.destination(generation)
    def test_projection_tests_do_not_copy_whole_receipt_or_mutate_actual_facts(self):
        original=copy.deepcopy(FAILURE); changed=dict(FAILURE,accepted_delta=1)
        with self.assertRaises(ValueError): MODULE.validate_projection(changed)
        self.assertEqual(FAILURE,original); self.assertLess(len(str(FAILURE)),10000)


if __name__=='__main__': unittest.main()
