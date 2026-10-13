"""P238 fresh 증거로 만든 명시적인 synthetic 계약 fixture; 실제 PASS 증거 아님."""
import copy
import unittest
import resume_post_stop_compound_runtime as m
FIXTURES=None


def fixture():
    if FIXTURES is None:raise RuntimeError('FRESH_RUNTIME_CONTRACT_FIXTURES_REQUIRED')
    (base,doc,body,required,extras)=copy.deepcopy(FIXTURES)
    legacy,plan,names,stop=base;index,name=m.g.old.select(plan,names);binding=doc['binding']
    pins=list(required.values());n=len(pins);size=sum(pin['bytes'] for pin in pins)
    old_size=body['owned_source_reader_passes'][0]['bytes_read'];added=size-old_size
    body.update(selected_test_names=[name],passed_test_names=[name],test_arguments=m.p.v.arguments(name),
        task=f'p204-r07-case-{index:03}-tests',minimal_worker_task=f'p204-r07-case-{index:03}-tests',source_freeze=pins)
    for row in body['owned_source_reader_passes']:
        row.update(read_passes=n,bytes_read=size);row['bytes_read_by_kind']['other']+=added
    component=doc['closing_component'];frame=component['source_frame'];own=frame['handles'];dup=own['borrowed_byte_streams']
    component.update(selected_test_name=name,extra_frame_controller_pins=list(extras.values()))
    frame.update(input_count=n,input_bytes=size)
    for i,row in enumerate(frame['actual_byte_boundaries']):
        row.update(actual_byte_pins=pins,reader_diagnostics=body['owned_source_reader_passes'][i])
    own.update(input_lock_handles_opened=n+306,input_lock_handles_closed=n+306,byte_stream_identity_checks=2*n)
    own['native_open_pacing']['open_reservations']=3*n+306
    dup.update(duplicate_handles_opened=2*n,duplicate_handles_closed=2*n,shared_offset_resets=2*n)
    frame['held_identity_after_owned_cleanup']['regular_file_count']=n
    doc.update(schema_version=m.SCHEMA,state=m.PASS,selected_test_index=index,selected_test_name=name,
        prior_runtime_plan=plan,runtime_plan=m.g.advance(legacy,plan,names,index),
        compound_anchor_pin=m.COMPOUND,preserved_case078_stop_pin=m.review.ROOT_PIN,
        compound_anchor_verified_without_body_reexecution=True,post_stop_runtime_contract_tests_passed=18)
    return doc,body,required,binding,extras,names,legacy,plan


class PostStopRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.doc,self.body,self.required,self.binding,self.extras,self.names,self.legacy,self.plan=fixture()
        self.pin=self.doc['case_receipt_pin']
    def record(self):
        return m.record(self.doc,self.body,self.pin,self.required,self.binding,self.extras,self.names,self.legacy,self.plan)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.record()
    def test_explicit_synthetic_complete_record(self):
        result=self.record();self.assertEqual(result['runtime_source_qualified_individual_cases'],self.plan['runtime_source_qualified_individual_cases']+1)
    def test_original_stop_is_not_runtime_pass(self):self.doc['state']='FAILED_NOT_ACCEPTED';self.reject()
    def test_compound_pin_drift(self):self.doc['compound_anchor_pin']=dict(m.COMPOUND,bytes=1);self.reject()
    def test_preserved_original78_pin_drift(self):self.doc['preserved_case078_stop_pin']=dict(m.review.ROOT_PIN,bytes=1);self.reject()
    def test_scope_subset(self):self.required.popitem();self.reject()
    def test_body_capture_incomplete(self):self.body['capture']['complete_streams']=False;self.reject()
    def test_original_job_limit_readback_absent(self):self.body['owned_limits_verified']=False;self.reject()
    def test_wrong_selected_name(self):self.doc['selected_test_name']='different';self.reject()
    def test_wrong_task(self):self.body['task']='p204-r07-case-078-tests';self.reject()
    def test_gate_promotion(self):self.doc['P09_gate']='PASS';self.reject()
    def test_lossy_serializer_stats(self):self.doc['packed_parent_write_statistics']['semantic_fields_removed']=1;self.reject()
    def test_unclosed_input_handle(self):self.doc['closing_component']['source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
    def test_unclosed_duplicate(self):self.doc['closing_component']['source_frame']['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject()
    def test_pressure_guard_relaxed(self):
        self.doc['closing_component']['source_frame']['handles']['native_open_backpressure']['original_hard_resource_decisions_unmodified']=False;self.reject()
    def test_advance_does_not_mutate_prior(self):
        before=copy.deepcopy(self.plan);self.record();self.assertEqual(self.plan,before)
    def test_following_selection_skips_accepted(self):
        new=self.record();index,name=m.g.old.select(new,self.names)
        self.assertNotEqual(index,self.doc['selected_test_index']);self.assertNotIn(name,new['runtime_qualified_test_names'])
    def test_already_accepted_name_blocks_wrong_record(self):
        self.plan['runtime_qualified_test_names'].append(self.doc['selected_test_name']);self.reject()
    def test_new_failed_attempt_blocks_automatic_retry(self):
        with self.assertRaises(ValueError):m.closed_attempt(dict(state='FAILED_NOT_ACCEPTED'))
