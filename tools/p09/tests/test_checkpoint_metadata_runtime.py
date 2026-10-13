"""P255: 명시적인 synthetic 현재 큐·sealed checkpoint 음성 계약. 실제 PASS가 아니다."""
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import resume_checkpoint_metadata_runtime as m
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
    def test_packed_prior_namespace_uses_same_original_decoder(self):
        reader=m.Reader.__new__(m.Reader)
        name=m.PROTOTYPE_LIGHT['path'];reader.reader=SimpleNamespace(snapshots={name:m.PROTOTYPE_LIGHT})
        reader.checkpoint=lambda:None
        carrier={'schema_version':m.r.packed.SCHEMA};decoded={'schema_version':'explicit_synthetic_prior_receipt'}
        with (patch.object(m.prior.prior.Reader,'json',return_value=carrier),
                patch.object(m.r.h,'canonical') as canonical,
                patch.object(m.r.packed,'unpack',return_value=decoded) as unpack):
            self.assertIs(reader.json(name),decoded)
            canonical.assert_called_once_with(carrier,m.PROTOTYPE_LIGHT,reader.checkpoint)
            unpack.assert_called_once_with(carrier,reader.checkpoint)


class CheckpointAdmissionTests(unittest.TestCase):
    def setUp(self):
        pins=[dict(path=f'explicit-synthetic/checkpoint-input-{i:03}',bytes=1,sha256='a'*64) for i in range(95)]
        self.doc=dict(schema_version=m.CHECKPOINT_SCHEMA,state=m.CHECKPOINT_PASS,
            resource_stop_reason=None,resource_watcher_cleanup_confirmed=True,document_revision=102,
            document_contract_tests_passed=14,root_actual_pair_pin=m.HEAD,
            product_body_or_full_source_reexecuted=False,exact_r101_document_bytes_preserved=True,
            IO=dict(finished=True,read_passes=192,bound_inputs=95,final_fresh_hashes=95),
            bound_input_pins=pins,required_bound_input_names=sorted(p['path'] for p in pins),report_pin=pins[0],
            runtime_plan=dict(runtime_source_qualified_individual_cases=75,next_runtime_index=82,
                runtime_remaining_individual_cases=174,runtime_remaining_regular_cases=168,
                runtime_remaining_corpus_cases=6,runtime_successful_candidates_requiring_closing=0,
                all_successful_bodies_pending_whole_reconciliation=72),
            P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',
            full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,
            PC_freeze_resolved=False,whole1470_current_fresh_qualified=False,historical67_current_fresh_qualified=False)
    def reject(self):
        with self.assertRaises((ValueError,KeyError)):m.checkpoint_contract(self.doc)
    def test_exact_sealed_checkpoint_shape(self):self.assertEqual(len(m.checkpoint_contract(self.doc)),95)
    def test_unfinished_checkpoint_fresh_rejected(self):self.doc['IO']['finished']=False;self.reject()
    def test_missing_checkpoint_binding_rejected(self):self.doc['bound_input_pins'].pop();self.reject()
    def test_checkpoint_queue_mismatch_rejected(self):self.doc['runtime_plan']['next_runtime_index']=83;self.reject()
    def test_checkpoint_gate_promotion_rejected(self):self.doc['P09_gate']='PASS';self.reject()
    def test_checkpoint_head_pin_mismatch_rejected(self):self.doc['root_actual_pair_pin']=dict(m.HEAD,bytes=1);self.reject()
    def test_unknown_prior_namespace_blocks_auto_resume(self):
        class Folder:
            def glob(self,pattern):
                key=pattern.split('-')[0]
                names=list(m.PRIOR_NAMESPACE_FILES[key])
                if key=='p253':names.append('p253-admission-run999.v1.json')
                return [SimpleNamespace(name=n) for n in names]
        with self.assertRaises(ValueError):m.prior_namespace_inventory(Folder())
