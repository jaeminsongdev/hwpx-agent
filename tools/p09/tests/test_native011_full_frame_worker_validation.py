import base64
import copy
import hashlib
import json
from pathlib import Path
import unittest

import native011_full_frame_worker_validation as m
import native011_readonly_frame_owned as original
import native011_product_worker_ready_probe as child_checker
import native011_product_worker_entry as worker_entry
import test_native011_readonly_frame_owned as old_fixture
import native011_ready_scope_connection as control
import native011_product_worker_scope as qualification
import current_stored_runtime_scope as scope


def fixture():
    proof,part,frame=old_fixture.fixture()
    required={f'tools/p09/model_worker_{i:03}.py':dict(path=f'tools/p09/model_worker_{i:03}.py',bytes=3,sha256='a'*64)
        for i in range(201)}
    entry=worker_entry.SELF;required[entry]=dict(path=entry,bytes=3,sha256='a'*64)
    pins=list(required.values());size=3*202
    frame.update(input_count=202,input_bytes=size)
    for boundary in frame['actual_byte_boundaries']:
        boundary.update(actual_byte_pins=copy.deepcopy(pins),reader_diagnostics=dict(read_passes=202,bytes_read=size))
    shared=frame['shared_metadata_frame_decoder'];shared.update(metadata_completed=325,Frame_completed=324)
    proof.update(state=m.CHILD_PASS,current_inputs=202,whole_inputs=621,metadata_tail_mode=True,
        exact_read_mode=True,decoder_timing_mode=True,chunk_join_mode=True)
    value=proof['readonly_frame_result'];value.update(current_inputs=202,worker_source_count=202,
        product_or_worker_processes_created=1,shared_decoder=copy.deepcopy(shared))
    value['whole_opening']['fresh_inputs']=621;value['loan'].update(armed_handles=202,restored_handles=202)
    for name in ('before_coverage','restored_coverage','after_coverage'):
        value[name].update(worker_required_count=202,parent_input_count=202)
    ledger=dict(read_passes=202,actual_declared_scope_count=202,bytes_read=size,bytes_paced=size,
        reserved_bytes=size+202,refunded_bytes=202,reservations=404,pending_request=False,failed=False)
    value['exact_read_factory']=dict(attempts=2,completed=2,failed=False,original_factory_and_workspace_retained=True,
        readers=[dict(ledger),dict(ledger)])
    codec=dict(actual_Frame_and_metadata_projection_class_same=True,candidate_codec_namespace_used_by_both=True)
    value['chunk_join_actual_Frame']=dict(codec);proof['terminal_chunk_join_binding']=dict(codec)
    proof['chunk_join_codec_connection']=dict(codec_connection_proof=dict(exact_original_decoder_AST_inverse=True),
        exact_same_metadata_and_Frame_projection_class=True,original_projection_method_and_property_code_retained=True,
        default_module_or_class_changed=False)
    observation=dict(attempts=2,completed=2,failed=False,original_shared=copy.deepcopy(shared),
        original_shared_and_budget_method_bodies_retained=True,roles={})
    for role,count in (('metadata',325),('frame',324)):
        observation['roles'][role]=dict(attempts=count,completed=count,failed=False,rows=[{} for _ in range(count)],
            original_budget=dict(attempted_decodes=count,completed_decodes=count,terminal_error_seen=False,
                active_decode=False,aggregate_limit_seconds=5.),original_clock_check_run_body_and_limit_unchanged=True,
            observation_not_used_for_admission_or_budget=True)
    proof['shared_decoder_timing_observation']=observation
    assignment=dict(original_engine_assignment_required_before_IO=True,original_owned_binary1_other2_MiB_rates_retained=True,
        all_original_read_wrappers_still_called=True,used_or_failed_pacer_reset_permitted=False,
        original_Native_guard_deadline_or_shared_budget_changed=False)
    factory=dict(unused_allocator_stage=dict(original_metadata_two_point_five_four_MiB_rates_retained=True,
        metadata_rate_membership_only_code_inverse=True),engine_assignment_stage=assignment,
        entire_original_metadata_factory_and_Router_code_retained=True,
        original_decoder_shared_budget_and_reader_tracking_retained=True,default_modules_classes_or_ctors_changed=False)
    proof['metadata_tail_connection']=dict(original_engine_owned_assignment_required=True,original_engine_metadata_IO_rates=dict(m.RATES),
        default_candidate_or_original_classes_mutated=False,reader_allocations_during_connection=0,metadata_factory_connection=factory)
    adopted=dict(assignment_attempts=1,assignment_completed=1,failed=False,original_engine_owned_assignment_adopted=True,
        source_table_and_read_proxy_retained=True,original_owned_rates=dict(m.RATES),physical_read_passes=2,
        physical_bytes_read=size,semantic_fresh_inputs=1,semantic_final_fresh_hashes=1)
    value['metadata_tail_reader']=dict(actual_factory_selected_reader=True,fresh_inputs=1,final_fresh_hashes=1,
        physical_read_passes=2,query_requests=2,physical_bytes_read=size,bytes_paced=size,reserved_bytes=size+2,
        refunded_bytes=2,reservations=4,actual_declared_whole_inputs=621,pending_request=False,failed=False,
        hash_JSON_source_or_closing_cache=False,original_metadata_binary2p5_other4_MiB_policy_retained=False,
        original_owned_binary1_other2_MiB_policy_retained=True,actual_owned_engine_adoption=adopted,
        actual_metadata_rates=dict(m.RATES),actual_paced_bytes_by_kind=dict(binary=0,other=size))
    value['metadata']=dict(state='PASS_ACTUAL_NATIVE011_METADATA_CALLBACK_NOT_NATIVE',metadata_body_executed=True,
        Frame_created=False,worker_created=False,GO_authorized=False,selected_current_inputs=202,fresh_inputs=1,final_fresh_hashes=1,
        physical_read_passes=2,physical_bytes_read=size,preparation_only_owned_allocation=True,complete_product_input_pins_qualified=False,
        original_owned_allocation_assignment_prefix=dict(whole_original_engine_source_pin=dict(m.ENGINE),
            original_statements_executed=2,actual_factory_and_byte_policy_dependencies_used=True,GO_authorized=False))
    parent=dict(verified=True,cpu_hard_cap_machine_percent=6.25,affinity_mask=1,priority_class=16384,active_process_limit=16,
        kill_on_close=True,breakaway_disabled=True,job_private_limit_mib=100.)
    limits=dict(verified=True,parent_original_limit_readback=parent,relative_parent_cpu_hard_cap_percent=100,
        maximum_system_CPU_percent=6.25,default_Windows_or_Native_policy_changed=False,product_or_GO_authorized=False,
        affinity_mask=1,priority_class=16384,kill_on_close=True,breakaway_disabled=True,job_private_limit_mib=100.)
    child=dict(state='COMPLETED_ORIGINAL_INHERITED_WORKER_NOT_PRODUCT_ACCEPTANCE',original_worker_exit_code=1,error_code=None,
        cleanup_confirmed=True,cleanup=dict(import_finder_restored=True,inherited_source_cleanup_confirmed=True),
        source_count=202,final_fresh_hashes=202,inherited_sources_closed=202,source_pin_sha256=worker_entry.pin_digest(required),
        source_closing_before_original_READY=True,every_declared_source_read_at_least_twice=True,original_GO_observed=False,
        original_input_reads=1,product_creation_attempts=0,GO_written_by_child=False,Native_or_product_acceptance_qualified=False)
    handoff=dict(failed=False,spawn_attempts=1,process_returned_for_original_cleanup=True,source_flags_and_descriptor_cleanup_errors=[],
        preparation_START_sent=True,original_Gate15_bound=True,raw_START_outside_original_product_Input10=True,
        source_bytes_hashes_JSON_or_AST_cached=False,original_parent_byte_read_credit_changed=False,
        original_Job_or_deadline_or_resource_policy_changed=False,product_GO_written_by_handoff=False)
    worker=dict(state='PASS_WHOLE_FRAME_WORKER202_SOURCE_READY_REAL_EOF_NOT_NATIVE_ACCEPTANCE',cleanup_confirmed=True,
        child_launch_attempts=1,child_exit_code=1,product_GO_writes=0,original_product_Job_or_commit_qualified=False,
        original_Native_Frame_and_guard_closed_by_child_probe=False,preparation_only_nested_Job_not_product_Job=True,elapsed_seconds=5.,
        readiness=dict(readiness_limit_seconds=15,readiness_elapsed_seconds=2.,readiness_confirmed=True,stopped=True,actual_original_GO_written=False),
        child=child,before_coverage=copy.deepcopy(value['before_coverage']),restored_coverage=copy.deepcopy(value['restored_coverage']),
        source_handoff=handoff,preparation_job_limits=limits,preparation_job_limits_after_ready=copy.deepcopy(limits),inner_job_final=dict(active_processes=0))
    value['whole_Frame_worker_ready']=dict(callback_attempts=1,callback_completed=True,original_product_Job_or_commit_qualified=False,
        product_or_GO_authorized=False,worker=worker)
    proof['full_frame_worker_connection']=dict(worker=worker,full_Native_phase_created=True,actual_whole_Frame_or_child_executed=True,
        metadata_allocation_or_body_executed=True,original_product_parent_still_denied=True,
        process_audit=dict(original_process_denial_registrations=1,exact_child_factory_attempts=1,exact_worker_Popen_events_allowed=1,
            other_Popen_events_denied=0,launch_scope_active=False,product_GO_or_intent_authorized=False))
    def encode():
        raw=json.dumps(frame).encode();part.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),base64=base64.b64encode(raw).decode())
        proof['full_frame_artifact'].update(bytes=len(raw),sha256=part['sha256'])
    encode();reads=[]
    def read(pin):reads.append(pin['path']);return part
    return proof,frame,required,encode,read,reads


class Tests(unittest.TestCase):
    def build(self):
        raw=(Path(__file__).resolve().parents[3]/m.SOURCE['path']).read_bytes()
        return m.build(raw,original,child_checker.validate_child,worker_entry.pin_digest)
    def test_full_original_inverse_and_one_restoration_keep_diagnostic_not_product_acceptance(self):
        selected=self.build();proof,frame,required,encode,read,reads=fixture();result=selected.validate(proof,read,required)
        self.assertTrue(selected.projection['entire_original_three_function_AST_inverse'])
        self.assertEqual(result['two_boundary_bytes'],1212);self.assertEqual(result['worker_source_count'],202)
        self.assertEqual(result['accepted_count_delta'],0);self.assertFalse(result['product_executed'])
        self.assertTrue(result['actual_source_worker_READY_and_EOF_qualified']);self.assertFalse(result['original_product_Job_or_commit_qualified'])
        self.assertEqual(len(reads),1)
    def test_declared_sources_come_from_fixed_original201_and_qualified_child202_not_the_candidate(self):
        root=Path(__file__).resolve().parents[3];reads=[]
        def read(pin):
            raw=(root/pin['path']).read_bytes();self.assertEqual(len(raw),pin['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(),pin['sha256']);reads.append(pin['path']);return json.loads(raw)
        declared=m.declared_worker(read,control,qualification,scope)
        self.assertEqual(len(declared),202);self.assertIn(worker_entry.SELF,declared)
        self.assertEqual(reads,[control.READY['path'],qualification.READY['path']])
    def test_original201_default_and_old_receipts_are_not_mutated(self):
        before=original.validate.__code__;selected=self.build();proof,*_=old_fixture.fixture()
        self.assertIs(original.validate.__code__,before);self.assertIn(201,before.co_consts)
        with self.assertRaisesRegex(ValueError,'COMPLETE_ORIGINAL_TIMED_EXACT'):selected.validate(proof,lambda pin:None,{})
    def test_source_or_original_function_drift_rejected_before_validation(self):
        with self.assertRaisesRegex(ValueError,'EXACT_ORIGINAL_WHOLE_VALIDATOR_SOURCE'):
            m.build(b'changed',original,child_checker.validate_child,worker_entry.pin_digest)
    def test_missing_or_conflicting_worker_pin_in_actual_frame_never_accepted(self):
        selected=self.build()
        for kind in ('missing','hash'):
            proof,frame,required,encode,read,_=fixture()
            if kind=='missing':required.pop(next(iter(required)))
            else:required[next(iter(required))]['sha256']='b'*64
            with self.assertRaises(ValueError):selected.validate(proof,read,required)
    def test_child_go_product_attempt_wrong_digest_or_incomplete_source_closing_rejected(self):
        selected=self.build()
        for key,value in (('original_GO_observed',True),('product_creation_attempts',1),('source_pin_sha256','0'*64),
            ('final_fresh_hashes',201),('inherited_sources_closed',201),('original_input_reads',0)):
            proof,frame,required,encode,read,_=fixture();proof['full_frame_worker_connection']['worker']['child'][key]=value
            with self.assertRaises(ValueError):selected.validate(proof,read,required)
    def test_ready_timeout_wrong_job_quota_or_live_job_cannot_qualify(self):
        selected=self.build()
        for kind in ('ready','quota','machine','live','guard_closed'):
            proof,frame,required,encode,read,_=fixture();worker=proof['full_frame_worker_connection']['worker']
            if kind=='ready':worker['readiness']['readiness_elapsed_seconds']=15
            elif kind=='quota':worker['preparation_job_limits']['relative_parent_cpu_hard_cap_percent']=1
            elif kind=='machine':worker['preparation_job_limits']['parent_original_limit_readback']['cpu_hard_cap_machine_percent']=100
            elif kind=='live':worker['inner_job_final']['active_processes']=1
            else:worker['original_Native_Frame_and_guard_closed_by_child_probe']=True
            with self.assertRaises(ValueError):selected.validate(proof,read,required)
    def test_old_rate_label_bad_adoption_or_incomplete_paced_metadata_is_rejected(self):
        selected=self.build()
        for kind in ('label','adoption','rates','bytes','prefix','closing'):
            proof,frame,required,encode,read,_=fixture();ledger=proof['readonly_frame_result']['metadata_tail_reader']
            if kind=='label':ledger['original_metadata_binary2p5_other4_MiB_policy_retained']=True
            elif kind=='adoption':ledger['actual_owned_engine_adoption']['assignment_completed']=0
            elif kind=='rates':ledger['actual_metadata_rates']['other']=4194304
            elif kind=='bytes':ledger['actual_paced_bytes_by_kind']['other']-=1
            elif kind=='prefix':proof['readonly_frame_result']['metadata']['original_owned_allocation_assignment_prefix']['original_statements_executed']=1
            else:ledger['final_fresh_hashes']=0
            with self.assertRaises(ValueError):selected.validate(proof,read,required)
    def test_original_frame_cleanup_byte_accounting_raw_policy_and_decoder_checks_still_reject(self):
        selected=self.build()
        for kind in ('handle','bytes','raw','decoder'):
            proof,frame,required,encode,read,_=fixture()
            if kind=='handle':frame['handles']['input_lock_handles_remaining']=1
            elif kind=='bytes':frame['actual_byte_boundaries'][1]['reader_diagnostics']['bytes_read']-=1
            elif kind=='raw':frame['parent_python_live_raw_access_policy']['active_scope']=True
            else:frame['shared_metadata_frame_decoder']['Frame_completed']=323
            encode()
            with self.assertRaises(ValueError):selected.validate(proof,read,required)
    def test_original_native_clock_guard_commit_and_failed_batch_boundaries_remain(self):
        selected=self.build()
        for kind in ('clock','guard','commit','batch'):
            proof,frame,required,encode,read,_=fixture()
            if kind=='clock':proof['readonly_frame_result']['readonly600_elapsed_seconds']=600
            elif kind=='guard':proof['readonly_stage_records'][-1]['guard_kind']='approved_preparation'
            elif kind=='commit':proof['readonly_frame_result']['original_Job_commit_supplied']=True
            else:proof['batch_phase_after_readonly_abort']='CLOSED'
            with self.assertRaises(ValueError):selected.validate(proof,read,required)
    def test_audit_retries_boolean_counter_or_lingering_scope_are_not_accepted(self):
        selected=self.build()
        for key,value in (('exact_child_factory_attempts',2),('exact_worker_Popen_events_allowed',True),('launch_scope_active',True)):
            proof,frame,required,encode,read,_=fixture();proof['full_frame_worker_connection']['process_audit'][key]=value
            with self.assertRaises(ValueError):selected.validate(proof,read,required)
    def test_handoff_or_child_cleanup_failure_is_never_hidden_by_successful_body(self):
        selected=self.build()
        for kind in ('flags','cleanup','credit'):
            proof,frame,required,encode,read,_=fixture();worker=proof['full_frame_worker_connection']['worker']
            if kind=='flags':worker['source_handoff']['source_flags_and_descriptor_cleanup_errors']=['UNCONFIRMED_SOURCE_FLAGS']
            elif kind=='cleanup':worker['cleanup_confirmed']=False
            else:worker['source_handoff']['original_parent_byte_read_credit_changed']=True
            with self.assertRaises(ValueError):selected.validate(proof,read,required)
    def test_each_validation_restores_actual_frame_again_no_parsed_evidence_cache(self):
        selected=self.build();proof,frame,required,encode,read,reads=fixture()
        selected.validate(proof,read,required);selected.validate(proof,read,required)
        self.assertEqual(len(reads),2)


if __name__=='__main__':unittest.main()
