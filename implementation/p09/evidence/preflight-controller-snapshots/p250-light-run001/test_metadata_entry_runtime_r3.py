"""P250 explicit synthetic 계약. 실제 Native/제품/CPU stress 없음."""
import copy
import unittest
import resume_metadata_entry_runtime_r3 as m
import test_post_stop_compound_runtime as old


class MetadataRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.doc,self.body,self.required,self.binding,self.extras,self.names,self.legacy,self.plan=old.fixture()
        self.pin=self.doc['case_receipt_pin'];self.own=self.doc['preparation_IO']['metadata_read_entry_pacing']
    def record(self):
        return m.record(self.doc,self.body,self.pin,self.required,self.binding,self.extras,self.names,self.legacy,self.plan)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):self.record()
    def test_explicit_synthetic_complete_pair(self):
        self.assertEqual(self.record()['runtime_source_qualified_individual_cases'],74)
    def test_missing_paced_metadata(self):
        del self.doc['preparation_IO']['metadata_read_entry_pacing'];self.reject()
    def test_metadata_rate_cannot_increase(self):self.own['maximum_metadata_read_entries_per_second']=33;self.reject()
    def test_original_reads_cannot_skip(self):self.own['original_reads_skipped']=True;self.reject()
    def test_binding_must_be_detached(self):self.own['binding_active']=True;self.reject()
    def test_no_false_CPU_improvement(self):self.own['measured_CPU_or_PC_freeze_improvement_claimed']=True;self.reject()
    def test_review_receipt_pin_exact(self):self.doc['metadata_stop_review_pin']=dict(m.METADATA_REVIEW,bytes=1);self.reject()
    def test_original_failure_pin_exact(self):self.doc['reviewed_metadata_stop_pin']=dict(m.metadata_review.ROOT_PIN,bytes=1);self.reject()
    def test_shared_read_budget_not_relaxed(self):
        row=self.doc['preparation_IO'];row['read_passes']=721
        self.own.update(entry_calls=721,reservations=721,completed_original_read_calls=721);self.reject()
    def test_new_contracts_required(self):self.doc['metadata_entry_runtime_contract_tests_passed']=0;self.reject()
    def test_actual_scope_bounds_required(self):self.doc['metadata_entry_scope_bounds_enforced']=False;self.reject()
    def test_future_scope_budget_exact(self):
        added={name:self.required[name] for name in m.NEW};original={name:pin for name,pin in self.required.items() if name not in added}
        budget=m.connected_budget()
        m.enforce_scope_budget(self.required,original,added,budget)
        with self.assertRaises(ValueError):m.enforce_scope_budget(self.required,original,added,dict(budget,unchanged_IO_scope_seconds=601))




