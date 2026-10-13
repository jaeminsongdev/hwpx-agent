"""P244 원 검증 fixture의 명시적 합성 계약. 실제 제품/Native/CPU stress 아님."""
import unittest
import resume_lower_native_runtime as m
import test_post_stop_compound_runtime as old


class LowerRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.doc,self.body,self.required,self.binding,self.extras,self.names,self.legacy,self.plan=old.fixture()
        self.pin=self.doc['case_receipt_pin']
    def record(self):
        return m.record(self.doc,self.body,self.pin,self.required,self.binding,self.extras,self.names,self.legacy,self.plan)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):self.record()
    def test_synthetic_new_full_scope_record(self):
        self.assertEqual(self.record()['runtime_source_qualified_individual_cases'],74)
    def test_original32_pacer_not_selected(self):
        self.doc['closing_component']['source_frame']['handles']['native_open_pacing']['maximum_opens_per_second']=32
        self.reject()
    def test_cleanup_guard_cannot_change(self):
        self.doc['closing_component']['source_frame']['handles']['lower_native_fan_out']['cleanup_not_rate_or_pressure_guarded']=False
        self.reject()
    def test_native_support_pin_must_be_sealed(self):
        self.doc['lower_native_support_pin']=dict(m.LOWER_SUPPORT,bytes=1);self.reject()
    def test_original_native_failure_pin_cannot_change(self):
        self.doc['reviewed_native_acquisition_stop_pin']=dict(m.acquisition.ROOT_PIN,bytes=1);self.reject()
    def test_additional_connection_contracts_required(self):
        self.doc['lower_native_runtime_contract_tests_passed']=0;self.reject()
    def test_future_scope_bounds_enforced(self):
        self.doc['lower_native_scope_bounds_enforced']=False;self.reject()
    def test_no_false_CPU_improvement_claim(self):
        self.doc['closing_component']['source_frame']['handles']['lower_native_fan_out']['measured_CPU_or_PC_freeze_improvement_claimed']=True
        self.reject()
