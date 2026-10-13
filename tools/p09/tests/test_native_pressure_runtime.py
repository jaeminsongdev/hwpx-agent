import copy
import unittest
import resume_native_pressure_runtime as d
FIXTURES=None


def pressure_row():
    return dict(warning_system_CPU_percent=95,cool_distinct_sample_windows=2,maximum_pause_windows_per_entry=8,
        warning_entries=0,completed_pause_windows=0,maximum_observed_pause_windows_in_one_entry=0,
        requested_pause_seconds=0.0,original_hard_resource_decisions_unmodified=True,original_IO_deadline_unmodified=True,
        original_sampler_windows_reused=True,new_native_query_or_sampler_thread_started=False,original_read_checks_skipped=False,
        original_frame_deadline_checked_before_open=True,original_32_open_rate_limit_and_no_burst_credits_preserved=True,
        pressure_applies_to_native_reservations_including_borrowed_streams=True,original_owner_sample_source_reused=True,
        cleanup_not_guarded_by_pressure=True,measured_CPU_or_PC_freeze_improvement_claimed=False)


class BridgeTests(unittest.TestCase):
    def setUp(self):
        if FIXTURES is None:raise RuntimeError('FRESH_QUEUE_FIXTURES_REQUIRED')
        self.legacy,self.base,self.names=copy.deepcopy(FIXTURES)
    def test_next_is_unaccepted_regular(self):
        index,name=d.g.old.select(self.base,self.names);self.assertNotIn(name,self.base['runtime_qualified_test_names'])
    def test_advance_does_not_mutate_prior_and_works_for_following(self):
        before=copy.deepcopy(self.base);index,_=d.g.old.select(self.base,self.names)
        plan=d.g.advance(self.legacy,self.base,self.names,index);following,_=d.g.old.select(plan,self.names)
        self.assertEqual(d.g.advance(self.legacy,plan,self.names,following)['runtime_source_qualified_individual_cases'],
            self.base['runtime_source_qualified_individual_cases']+2);self.assertEqual(before,self.base)
    def test_original_old_input_scope_not_excluded(self):
        self.assertEqual(len(d.NEW),5);self.assertEqual(len(d.EXTRAS),26)
        self.assertTrue(set(d.g.EXTRAS)<set(d.EXTRAS))
    def test_pressure_zero_warnings_is_valid_not_improvement_claim(self):d.pressure_contract(pressure_row())
    def test_two_cool_windows_are_required(self):
        row=pressure_row();row.update(warning_entries=1,completed_pause_windows=1,
            maximum_observed_pause_windows_in_one_entry=1,requested_pause_seconds=0.5)
        with self.assertRaises(ValueError):d.pressure_contract(row)
    def test_completed_cooling_is_accepted(self):
        row=pressure_row();row.update(warning_entries=1,completed_pause_windows=2,
            maximum_observed_pause_windows_in_one_entry=2,requested_pause_seconds=1)
        d.pressure_contract(row)
    def test_original_lock_deadline_cannot_be_relaxed(self):
        row=pressure_row();row['original_frame_deadline_checked_before_open']=False
        with self.assertRaises(ValueError):d.pressure_contract(row)
    def test_CPU_threshold_cannot_be_changed(self):
        row=pressure_row();row['warning_system_CPU_percent']=35
        with self.assertRaises(ValueError):d.pressure_contract(row)
    def test_freeze_improvement_claim_rejected(self):
        row=pressure_row();row['measured_CPU_or_PC_freeze_improvement_claimed']=True
        with self.assertRaises(ValueError):d.pressure_contract(row)
    def test_CPU_stop_before_frame_or_GO_blocks_retry(self):
        with self.assertRaisesRegex(ValueError,'INSPECT_ANY_FAILED'):
            d.closed_attempt(dict(state='FAILED_NOT_ACCEPTED',resource_stop_reason='STOP_SUSTAINED_SYSTEM_CPU',
                frame_acquisition_requested=False,product_worker_invocation_requested=False))
    def test_failed_frame_without_resource_reason_still_blocks_retry(self):
        with self.assertRaisesRegex(ValueError,'INSPECT_ANY_FAILED'):
            d.closed_attempt(dict(state='FAILED_NOT_ACCEPTED',resource_stop_reason=None,
                frame_acquisition_requested=True,product_worker_invocation_requested=False))
    def test_failed_cleanup_blocks_prior_success(self):
        with self.assertRaisesRegex(ValueError,'INSPECT_ANY_FAILED'):
            d.closed_attempt(dict(state=d.PASS,error_code=None,resource_stop_reason=None,
                resource_watcher_cleanup_confirmed=False))
