"""P263 synthetic frame 계약은 실제 source/본체 수용 증거가 아님."""
import copy
import unittest
import close_observation_failure_source_frame as v
FIXTURES=None


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(FIXTURES,'explicit fixture required; no skip')
        root,self.required=copy.deepcopy(FIXTURES);self.frame=copy.deepcopy(root['terminal_source_frame'])
        f=self.frame;n=v.N;total=sum(x['bytes'] for x in self.required.values())
        f.update(frame_state='COMMITTED',registered_live_frame=False,input_count=n,input_bytes=total,
            original_owned_cleanup_confirmed_before_release=True,held_identity_after_owned_cleanup=dict(
                held_identity_checks_complete=True,separate_pathname_reopens=0,regular_file_count=n,directory_count=306))
        for row in f['actual_byte_boundaries']:
            row['actual_byte_pins']=list(self.required.values());row['reader_diagnostics'].update(read_passes=n,bytes_read=total)
        h=f['handles'];h.update(input_lock_handles_opened=n+306,input_lock_handles_closed=n+306,
            byte_stream_identity_checks=2*n,handle_metadata_checks=3*n+306)
        h['native_open_pacing']['open_reservations']=3*n+306
        h['borrowed_byte_streams'].update(duplicate_handles_opened=2*n,duplicate_handles_closed=2*n,shared_offset_resets=2*n)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):v.frame_contract(self.frame,self.required)
    def test_complete_synthetic_frame(self):v.frame_contract(self.frame,self.required)
    def test_full_scope(self):self.required.popitem();self.reject()
    def test_uncommitted(self):self.frame['frame_state']='CLOSED';self.reject()
    def test_registered(self):self.frame['registered_live_frame']=True;self.reject()
    def test_metadata_only_not_bytes(self):self.frame['actual_byte_boundaries'][1]['actual_byte_pins'].pop();self.reject()
    def test_partial_read(self):self.frame['actual_byte_boundaries'][1]['reader_diagnostics']['read_passes']-=1;self.reject()
    def test_fast_byte_rate(self):self.frame['actual_byte_boundaries'][0]['reader_diagnostics']['read_rates_by_kind']['other']*=2;self.reject()
    def test_native_rate(self):self.frame['handles']['native_open_pacing']['maximum_opens_per_second']=32;self.reject()
    def test_deadline(self):self.frame['handles']['maximum_lock_seconds']=601;self.reject()
    def test_native_residue(self):self.frame['handles']['input_lock_handles_remaining']=1;self.reject()
    def test_duplicate_residue(self):self.frame['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject()
    def test_duplicate_offset(self):self.frame['handles']['borrowed_byte_streams']['shared_offset_resets']-=1;self.reject()
    def test_identity_missing(self):self.frame['held_identity_after_owned_cleanup']=None;self.reject()
    def test_new_sampler(self):self.frame['actual_byte_boundaries'][0]['reader_diagnostics']['extra_sampler_or_native_query_started']=True;self.reject()
    def test_native_reservations_missing(self):self.frame['handles']['native_open_pacing']['open_reservations']-=1;self.reject()
    def test_budget_retains600_full_scope(self):
        row=v.budget(self.required);self.assertEqual(row['original_deadline_seconds'],600)
        self.assertLess(row['nominal_combined_seconds'],600);self.assertTrue(row['estimate_not_completion_guarantee'])


if __name__=='__main__':unittest.main()
