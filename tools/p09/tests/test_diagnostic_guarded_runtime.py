"""P271 현재/다음1575 synthetic40. 원P26530 거부조건 유지/새연결10 추가."""
import resume_diagnostic_guarded_runtime as m
import test_monotonic_compound_runtime as old


class QueueTests(old.QueueTests):
    def setUp(self):
        super().setUp()
        policy=m.metadata.Binding.summary(type('Policy',(),dict(early=m.early_review.EarlySourceCheckpoint(lambda:None,None)))())
        self.doc['preparation_IO']['early_metadata_pressure']=policy
        self.doc['closing_component']['metadata_IO']['early_metadata_pressure']=policy
        h=self.doc['closing_component']['source_frame']['handles']
        h['handle_metadata_checks']=4*len(self.required)+612
        h['lock_timing_diagnostic']=dict(original_guard_checks=100,first_original_error=None,original_lock_limit_seconds=600,
            original_check_invoked_without_replacement=True,extra_clock_only_at_boundary_or_first_error=True,
            unknown_measurements_not_zeroed=True,extra_CPU_RAM_or_native_query_started=False,
            original_resource_guard_or_deadline_extended=False,cleanup_callback_wrapped=False,
            CPU_or_PC_freeze_improvement_established=False,
            explicit_phase_events=[dict(label=label,phase='admission',original_lock_elapsed_seconds=float(i),
                guard_check_number=i+1) for i,label in enumerate(m.connection.LABELS)])
    def test_diagnostic_connection_not_selected_denied(self):self.doc['diagnostic_parent_connection_selected']=False;self.reject()
    def test_native_timing_not_connected_denied(self):self.doc['native_timing_connected']=False;self.reject()
    def test_metadata90_not_connected_denied(self):self.doc['early_metadata_connection_selected']=False;self.reject()
    def test_qualified_metadata_pin_drift_denied(self):self.doc['qualified_metadata_pin']=dict(m.METADATA_PIN,bytes=0);self.reject()
    def test_metadata_warning_not_delayed_back_to95(self):
        self.doc['preparation_IO']['early_metadata_pressure']['selected_metadata_warning_CPU_percent']=95;self.reject()
    def test_original95_not_removed(self):
        self.doc['preparation_IO']['early_metadata_pressure']['original95_pressure_retained_as_base']=False;self.reject()
    def test_timing_original_error_not_PASS(self):
        self.doc['closing_component']['source_frame']['handles']['lock_timing_diagnostic']['first_original_error']={};self.reject()
    def test_timing600_not_extended(self):
        self.doc['closing_component']['source_frame']['handles']['lock_timing_diagnostic']['original_lock_limit_seconds']=601;self.reject()
    def test_unknown_timing_not_invented_zero(self):
        self.doc['closing_component']['source_frame']['handles']['lock_timing_diagnostic']['explicit_phase_events'][0]['original_lock_elapsed_seconds']=None;self.reject()
    def test_timing_claim_or_query_not_added(self):
        self.doc['closing_component']['source_frame']['handles']['lock_timing_diagnostic']['extra_CPU_RAM_or_native_query_started']=True;self.reject()


if __name__=='__main__':
    import unittest
    unittest.main()
