"""Pure necessary-model tests, no Native fixture or product process."""
import unittest

MODULE=None


def fixture():
    return dict(inputs=3268,binary_bytes=28433408,other_bytes=171457273,
        predicted_runtime_combined_seconds=582.7896766390119,unchanged_lock_deadline_seconds=600,
        unallocated_margin_seconds=60,aggregate_envelope_decoder_allowance_seconds=5.0)


class Tests(unittest.TestCase):
    def test_native600_pass_does_not_imply_shared720_pass(self):
        row=MODULE.assess(fixture())
        self.assertTrue(row['Native600_nominal_fits']); self.assertFalse(row['shared720_nominal_fits'])
        self.assertAlmostEqual(row['minimum_combined_declared_model_seconds'],761.1396766390119)
        self.assertFalse(row['product_execution_or_replay_authorized'])

    def test_metadata_optimistic_overlap_is_max_not_sum(self):
        row=MODULE.assess(fixture())
        self.assertEqual(row['optimistic_metadata_seconds'],max(row['optimistic_metadata_open_seconds'],row['optimistic_metadata_byte_seconds']))
        self.assertFalse(row['metadata_work_overlapped_with_later_Native'])

    def test_fastest_legal_rate_and_initial_credit_are_optimistic_only(self):
        row=MODULE.assess(fixture())
        self.assertEqual(row['optimistic_metadata_open_seconds'],3267/20)
        self.assertEqual(row['optimistic_metadata_byte_seconds'],(199890681-65536)/2097152)
        self.assertTrue(row['slower_binary_IO_optimistically_charged_at_fastest_legal_metadata_rate'])
        self.assertFalse(row['protection_or_IO_policy_changed'])

    def test_small_model_is_only_necessary_check_not_qualification(self):
        row=MODULE.assess(dict(fixture(),inputs=1,binary_bytes=1,other_bytes=1,predicted_runtime_combined_seconds=100.0))
        self.assertEqual(row['state'],'NECESSARY_SHARED720_MODEL_CHECK_ONLY_NOT_QUALIFICATION')
        self.assertTrue(row['estimate_not_completion_guarantee'])

    def test_original_limits_and_reservations_cannot_be_changed(self):
        for delta in (dict(metadata_open_limit=40),dict(fastest_metadata_rate=4194304),dict(burst_bytes=131072),
                dict(readiness_seconds=3),dict(shared_seconds=1200)):
            with self.assertRaises(ValueError): MODULE.assess(fixture(),**delta)
        for delta in (dict(unchanged_lock_deadline_seconds=720),dict(unallocated_margin_seconds=0),
                dict(aggregate_envelope_decoder_allowance_seconds=10.0)):
            with self.assertRaises(ValueError): MODULE.assess(dict(fixture(),**delta))

    def test_boolean_negative_nonfinite_and_untyped_models_are_rejected(self):
        for delta in (dict(inputs=True),dict(inputs=0),dict(other_bytes=-1),dict(binary_bytes=False),
                dict(predicted_runtime_combined_seconds=float('nan')),dict(predicted_runtime_combined_seconds=float('inf'))):
            with self.assertRaises(ValueError): MODULE.assess(dict(fixture(),**delta))

    def test_shared_deadline_boundary_is_strict(self):
        row=MODULE.assess(dict(fixture(),inputs=1,binary_bytes=0,other_bytes=0,predicted_runtime_combined_seconds=705.0))
        self.assertEqual(row['minimum_combined_declared_model_seconds'],720.0)
        self.assertFalse(row['shared720_nominal_fits'])


if __name__=='__main__': unittest.main()
