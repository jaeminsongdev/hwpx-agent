"""P253 현재 큐 synthetic 계약. 이전+1이며 특정 수용 수에 고정하지 않는다."""
import copy
import unittest
import resume_generic_metadata_runtime_r2 as m
import test_post_stop_compound_runtime as f


class GenericQueueTests(unittest.TestCase):
    def setUp(self):
        self.doc,self.body,self.required,self.binding,self.extras,self.names,self.legacy,self.plan=f.fixture()
        self.pin=self.doc['case_receipt_pin'];self.own=self.doc['preparation_IO']['metadata_read_entry_pacing']
    def record(self):
        return m.record(self.doc,self.body,self.pin,self.required,self.binding,self.extras,self.names,self.legacy,self.plan)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.record()
    def test_current_queue_prior_plus_one(self):
        self.assertEqual(self.record()['runtime_source_qualified_individual_cases'],self.plan['runtime_source_qualified_individual_cases']+1)
    def test_current_queue_next_name_not_repeated(self):
        next_plan=self.record();index,_=m.g.old.select(next_plan,self.names)
        self.assertNotEqual(index,self.doc['selected_test_index'])
    def test_historical_scope_explicit(self):
        self.doc['historical_support_fixture_scope']='CURRENT';self.reject()
    def test_current_core_required(self):self.doc['current_queue_runtime_contract_tests_passed']=0;self.reject()
    def test_generic_queue_contracts_required(self):self.doc['generic_queue_runtime_contract_tests_passed']=0;self.reject()
    def test_fixed_count_failure_pin_exact(self):self.doc['reviewed_fixed_count_admission_pin']=dict(m.ADMISSION_FAILURE,bytes=1);self.reject()
    def test_original_body_not_retry(self):self.plan['runtime_qualified_test_names'].append(self.doc['selected_test_name']);self.reject()
    def test_full_scope_not_reduced(self):self.required.popitem();self.reject()
    def test_native_rate_stays20(self):
        self.doc['closing_component']['source_frame']['handles']['native_open_pacing']['maximum_opens_per_second']=32;self.reject()
    def test_metadata_reads_not_skipped(self):self.own['original_reads_skipped']=True;self.reject()
    def test_metadata_detached(self):self.own['binding_active']=True;self.reject()
    def test_original_job_limits(self):self.body['owned_limits_verified']=False;self.reject()
    def test_original_source_cleanup(self):
        self.doc['closing_component']['source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
    def test_gate_not_promoted(self):self.doc['P09_gate']='PASS';self.reject()
    def test_new_failure_blocks_auto_retry(self):
        with self.assertRaises(ValueError):m.closed_attempt(dict(state='FAILED_NOT_ACCEPTED'))
    def test_new_controller_budget_exact(self):
        added={n:self.required[n] for n in m.NEW};old={n:p for n,p in self.required.items() if n not in added}
        m.enforce_scope_budget(self.required,old,added,m.connected_budget())
        with self.assertRaises(ValueError):m.enforce_scope_budget(self.required,old,added,dict(m.connected_budget(),unchanged_IO_scope_seconds=601))


    def test_own_light_closed_state_accepted(self):
        m.closed_attempt(dict(schema_version=m.SCHEMA,state=m.LIGHT,error_code=None,
            resource_stop_reason=None,resource_watcher_cleanup_confirmed=True))
    def test_foreign_generation_light_rejected(self):
        with self.assertRaises(ValueError):
            m.closed_attempt(dict(schema_version='hwpx-agent.p09-generic-metadata-runtime-pair/v1',
                state='PASS_GENERIC_METADATA_SELECTION_NOT_ACTUAL_OR_GATE',error_code=None,
                resource_stop_reason=None,resource_watcher_cleanup_confirmed=True))

