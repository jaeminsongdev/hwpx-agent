"""Exact monitor adaptation and lossless evidence validation; no OS processes."""
import ast
import base64
import copy
import hashlib
import json
from pathlib import Path
import unittest
import native011_readonly_frame_owned as owned


def fixture():
    pins=[dict(path='model',bytes=3,sha256='a'*64)]
    frame=dict(frame_state='CLOSED',registered_live_frame=False,input_count=1,input_bytes=3,
        original_owned_cleanup_confirmed_before_release=False,
        parent_live_raw_policy_installed=True,parent_python_live_raw_access_policy=dict(active_scope=False,
            all_original_open_function_identities_restored=True),
        handles=dict(input_lock_cleanup_confirmed=True,input_lock_handles_opened=2,input_lock_handles_closed=2,
            input_lock_handles_remaining=0,active_reader_bindings=0,active_byte_streams=0),
        actual_byte_boundaries=[dict(role=r,actual_byte_pins=copy.deepcopy(pins),
            reader_diagnostics=dict(read_passes=1,bytes_read=3)) for r in ('before','after')],
        shared_metadata_frame_decoder=dict(shared_limit_seconds=5,total_decoder_work_seconds=1.5,
            metadata_registered=True,Frame_registered=True,terminal_error_seen=False))
    raw=json.dumps(frame).encode();part=dict(schema_version='hwpx-agent.p09-terminal-frame-part/v1',
        Native_execution_finished=True,Native_or_product_acceptance_qualified=False,index=0,bytes=len(raw),
        sha256=hashlib.sha256(raw).hexdigest(),base64=base64.b64encode(raw).decode())
    index=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),parts=[dict(path='model.frame-part000.v1.json')],
        Native_handles_closed_before_output=True,Native_execution_resumed=False)
    value=dict(whole_opening=dict(actual_complete=True,fresh_inputs=420),current_inputs=1,worker_source_count=201,
        readonly600_elapsed_seconds=30,product_or_worker_processes_created=0,GO_writes=0,
        original_Job_commit_supplied=False,case_finished_called=False,
        original_parent_wrapper_called=True,original_parent_wrapper_attempts=1,
        original_engine_body_called=False,explicit_no_product_delegate_only=True,
        loan=dict(restore_confirmed=True,failed=False,armed_handles=201,restored_handles=201),
        shared_decoder=copy.deepcopy(frame['shared_metadata_frame_decoder']))
    for name,role,count in (('before_coverage','before',1),('restored_coverage','before',1),('after_coverage','after',2)):
        value[name]=dict(worker_required_count=201,parent_input_count=1,boundary=role,actual_parent_byte_boundaries=count,
            exact_whole_worker_pin_coverage=True,live_original_registry_and_OS_handles_verified=True)
    proof=dict(state=owned.CHILD_PASS,cleanup_confirmed=True,fresh_inputs=12,final_fresh_hashes=12,
        readonly_driver_bound=True,Frame_instances=1,actual_Native_Frame_created=True,actual_product_executed=False,
        process_creation_attempts=0,shared_budget_restored=True,
        actual_owned_Native_acceptance_qualified=False,Native_clock_reset_or_extended=False,
        batch_phase_after_readonly_abort='BROKEN',parent_attempts=1,worker_attempts=0,worker_calls=0,
        readonly_stage_records=[dict(stage=s,cleanup_confirmed=True,elapsed_seconds=10,
            guard_kind='original_Native_no_preparation_relaxation' if s=='native' else 'approved_preparation')
            for s in ('construction','opening','native')],readonly_frame_result=value,full_frame_artifact=index,
        whole_inputs=420,current_inputs=1)
    return proof,part,frame


class ReadonlyOwnedContracts(unittest.TestCase):
    def test_codec_mode_never_uses_constructor_or_partial_proof_as_runtime_acceptance(self):
        proof,part,frame=fixture();proof['chunk_join_mode']=True
        with self.assertRaisesRegex(ValueError,'CHUNK_JOIN_REQUIRES_ORIGINAL_EXACT'):
            owned.validate(proof,lambda pin:part)

    def test_optional_timing_keeps_original_frame_and_per_role_budget_counts(self):
        for broken in (None,'failed','count','credit','sidecar','sidecar_drift'):
            proof,part,frame=fixture();proof.update(exact_read_mode=True,decoder_timing_mode=True)
            ledger=dict(read_passes=1,actual_declared_scope_count=1,bytes_read=3,bytes_paced=3,
                reserved_bytes=5,refunded_bytes=2,reservations=4,pending_request=False,failed=False)
            proof['readonly_frame_result']['exact_read_factory']=dict(attempts=2,completed=2,failed=False,
                original_factory_and_workspace_retained=True,readers=[dict(ledger),dict(ledger)])
            shared=frame['shared_metadata_frame_decoder'];shared.update(metadata_completed=1,Frame_completed=1)
            proof['readonly_frame_result']['shared_decoder']=dict(shared)
            budget=dict(attempted_decodes=1,completed_decodes=1,terminal_error_seen=False,active_decode=False,
                aggregate_limit_seconds=5.)
            timing=dict(attempts=1,completed=1,failed=False,rows=[{}],original_budget=budget,
                original_clock_check_run_body_and_limit_unchanged=True,observation_not_used_for_admission_or_budget=True)
            observation=dict(attempts=2,completed=2,failed=False,original_shared=dict(shared),
                original_shared_and_budget_method_bodies_retained=True,
                roles={role:copy.deepcopy(timing) for role in ('metadata','frame')})
            proof['shared_decoder_timing_observation']=observation
            if broken=='failed':observation['failed']=True
            if broken=='count':observation['roles']['frame']['completed']=0
            if broken=='credit':observation['roles']['frame']['observation_not_used_for_admission_or_budget']=False
            if broken in ('sidecar','sidecar_drift'):
                proof['shared_decoder_timing_observation_artifact']=dict(path='model.timing.v1.json')
                proof['shared_decoder_timing_observation']=owned.timing_summary(observation)
                if broken=='sidecar_drift':proof['shared_decoder_timing_observation']['roles']['metadata']['recorded_row_count']=2
            raw=json.dumps(frame).encode();part.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
                base64=base64.b64encode(raw).decode());proof['full_frame_artifact'].update(bytes=len(raw),sha256=part['sha256'])
            def read(pin):return observation if pin['path']=='model.timing.v1.json' else part
            if broken in (None,'sidecar'):owned.validate(proof,read)
            else:
                with self.assertRaises(ValueError):owned.validate(proof,read)

    def test_optional_exact_mode_requires_two_full_matched_byte_ledgers(self):
        def ledger():return dict(read_passes=1,actual_declared_scope_count=1,bytes_read=3,bytes_paced=3,
            reserved_bytes=4,refunded_bytes=1,reservations=2,pending_request=False,failed=False)
        for broken in (None,'bytes','refund','pending','scope','factory'):
            proof,part,_=fixture();proof['exact_read_mode']=True
            exact=dict(attempts=2,completed=2,failed=False,original_factory_and_workspace_retained=True,
                readers=[ledger(),ledger()])
            proof['readonly_frame_result']['exact_read_factory']=exact
            if broken=='bytes':exact['readers'][1].update(bytes_read=4,bytes_paced=4,reserved_bytes=5)
            if broken=='refund':exact['readers'][1]['refunded_bytes']=0
            if broken=='pending':exact['readers'][1]['pending_request']=True
            if broken=='scope':exact['readers'][1]['actual_declared_scope_count']=2
            if broken=='factory':exact['completed']=1
            if broken is None:self.assertEqual(owned.validate(proof,lambda pin:part)['accepted_count_delta'],0)
            else:
                with self.assertRaises(ValueError):owned.validate(proof,lambda pin:part)
    def test_full_original_monitor_ast_inverse_and_no_product_command(self):
        raw=(Path(__file__).resolve().parents[3]/owned.SOURCE['path']).read_bytes()
        node,proof=owned.project(raw);text=ast.unparse(ast.fix_missing_locations(node))
        self.assertTrue(proof['readonly_main_AST_inverse'])
        self.assertTrue(proof['original_Monitor_Job_capture_cleanup_deadlines_retained'])
        self.assertIn("command = [sys.executable, '-B', str(c.ROOT / TARGET), '--attempt', str(args.attempt)]",text)
        self.assertIn('2400',text);self.assertIn('_validate_readonly',text)
        self.assertNotIn("proof['metadata']",text)

    def test_changed_original_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'EXACT_ENTIRE_ORIGINAL_OWNED_MONITOR_SOURCE'):owned.project(b'changed')

    def test_terminal_protocol_projection_preserves_inverse_and_distinguishes_actual_audit_guard(self):
        raw=(Path(__file__).resolve().parents[3]/owned.SOURCE['path']).read_bytes()
        node,proof=owned.project(raw,terminal_protocol=True);text=ast.unparse(ast.fix_missing_locations(node))
        self.assertTrue(proof['readonly_main_AST_inverse']);self.assertTrue(proof['terminal_marker_has_no_live_epoch_credit'])
        self.assertTrue(proof['post_cleanup_audit_has_distinct_actual_guard']);self.assertIn('2400',text)
        self.assertIn('_cleanup_terminal',text);self.assertIn('_terminal_complete',text)
        self.assertNotIn('monitor.seen == 4',text)
        self.assertIn('tools/p09/native011_readonly_terminal_monitor.py',text)
        self.assertIn('tools/p09/tests/test_native011_readonly_terminal_monitor.py',text)
        with self.assertRaises(ValueError):owned.project(raw,terminal_protocol=1)

    def test_original_full_frame_and_metadata_validators_unchanged_from_archived_008_source(self):
        import base64
        root=Path(__file__).resolve().parents[3]
        saved=json.loads((root/'implementation/p09/evidence/p09-361-native011-current805-readonly-monitor-original008-source314.v1.json').read_text(encoding='utf-8'))
        pin=saved['archive']['original_source_pin'];before=base64.b64decode(saved['archive']['base64'],validate=True)
        self.assertEqual(len(before),pin['bytes']);self.assertEqual(hashlib.sha256(before).hexdigest(),pin['sha256'])
        after=(root/pin['path']).read_bytes()
        def functions(raw):
            return {node.name:ast.dump(node,include_attributes=False) for node in ast.parse(raw).body
                if isinstance(node,ast.FunctionDef)}
        old,new=functions(before),functions(after)
        for name in ('restore_parts','validate_metadata_tail','validate'):
            self.assertEqual(old[name],new[name])

    def test_metadata_tail_requires_original_full_callback_and_cross_matched_actual_ledger(self):
        import copy
        proof=dict(chunk_join_mode=True,exact_read_mode=True,decoder_timing_mode=True,current_inputs=3,whole_inputs=4,
            metadata_tail_connection=dict(original_metadata_two_point_five_four_MiB_rates_retained=True,
                metadata_rate_membership_only_code_inverse=True,entire_original_metadata_factory_and_Router_code_retained=True,
                original_decoder_shared_budget_and_reader_tracking_retained=True,default_modules_classes_or_ctors_changed=False))
        value=dict(metadata=dict(state='PASS_ACTUAL_NATIVE011_METADATA_CALLBACK_NOT_NATIVE',metadata_body_executed=True,
            Frame_created=False,worker_created=False,GO_authorized=False,selected_current_inputs=3,
            fresh_inputs=1,final_fresh_hashes=1,physical_read_passes=2,physical_bytes_read=6),
            metadata_tail_reader=dict(actual_factory_selected_reader=True,fresh_inputs=1,final_fresh_hashes=1,
                physical_read_passes=2,query_requests=2,physical_bytes_read=6,bytes_paced=6,reserved_bytes=8,
                refunded_bytes=2,reservations=4,actual_declared_whole_inputs=4,pending_request=False,
                failed=False,hash_JSON_source_or_closing_cache=False))
        owned.validate_metadata_tail(proof,value)
        for kind in ('small','closing','bytes','queries','scope','cache','rate','mode'):
            p,v=copy.deepcopy(proof),copy.deepcopy(value)
            if kind=='small':v['metadata']['state']='PASS_SMALL_COMPONENT_ONLY'
            if kind=='closing':v['metadata_tail_reader']['final_fresh_hashes']=0
            if kind=='bytes':v['metadata_tail_reader']['bytes_paced']=5
            if kind=='queries':v['metadata_tail_reader']['query_requests']=1
            if kind=='scope':v['metadata_tail_reader']['actual_declared_whole_inputs']=3
            if kind=='cache':v['metadata_tail_reader']['hash_JSON_source_or_closing_cache']=True
            if kind=='rate':p['metadata_tail_connection']['metadata_rate_membership_only_code_inverse']=False
            if kind=='mode':p['decoder_timing_mode']=False
            with self.assertRaises(ValueError):owned.validate_metadata_tail(p,v)

    def test_complete_original_frame_restored_and_readonly_result_accepted_only_as_diagnostic(self):
        proof,part,frame=fixture()
        self.assertEqual(owned.restore_parts(proof['full_frame_artifact'],lambda pin:part),frame)
        result=owned.validate(proof,lambda pin:part)
        self.assertEqual(result['two_boundary_bytes'],6);self.assertEqual(result['accepted_count_delta'],0)
        self.assertEqual(result['batch_phase'],'BROKEN');self.assertFalse(result['product_executed'])

    def test_missing_or_corrupt_part_and_wrong_part_order_rejected(self):
        for mode in ('missing','hash','base64','order'):
            proof,part,_=fixture();index=proof['full_frame_artifact']
            if mode=='missing':index['parts']=[]
            if mode=='hash':part['sha256']='b'*64
            if mode=='base64':part['base64']='*invalid*'
            if mode=='order':index['parts'][0]['path']='model.frame-part001.v1.json'
            with self.assertRaises(ValueError):owned.restore_parts(index,lambda pin:part)

    def test_product_commit_successful_batch_or_clock_reset_never_promoted(self):
        for key,value in (('actual_product_executed',True),('actual_owned_Native_acceptance_qualified',True),
            ('Native_clock_reset_or_extended',True),('batch_phase_after_readonly_abort','CLOSED'),('worker_calls',1)):
            proof,part,_=fixture();proof[key]=value
            with self.assertRaises(ValueError):owned.validate(proof,lambda pin:part)
        for key in ('original_Job_commit_supplied','case_finished_called'):
            proof,part,_=fixture();proof['readonly_frame_result'][key]=True
            with self.assertRaises(ValueError):owned.validate(proof,lambda pin:part)

    def test_failed_cleanup_expired_native_or_unrestored_flags_rejected(self):
        for mode in ('cleanup','deadline','flags','guard'):
            proof,part,_=fixture()
            if mode=='cleanup':proof['cleanup_confirmed']=False
            if mode=='deadline':proof['readonly_frame_result']['readonly600_elapsed_seconds']=600
            if mode=='flags':proof['readonly_frame_result']['loan']['restored_handles']=200
            if mode=='guard':proof['readonly_stage_records'][-1]['guard_kind']='approved_preparation'
            with self.assertRaises(ValueError):owned.validate(proof,lambda pin:part)

    def test_truncated_boundary_or_decoder_overrun_rejected_after_lossless_reconstruction(self):
        for mode in ('boundary','decoder','handles'):
            proof,part,frame=fixture()
            if mode=='boundary':frame['actual_byte_boundaries'].pop()
            if mode=='decoder':frame['shared_metadata_frame_decoder']['total_decoder_work_seconds']=6
            if mode=='handles':frame['handles']['input_lock_handles_remaining']=1
            raw=json.dumps(frame).encode();part.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
                base64=base64.b64encode(raw).decode());proof['full_frame_artifact'].update(bytes=len(raw),sha256=part['sha256'])
            with self.assertRaises(ValueError):owned.validate(proof,lambda pin:part)

    def test_terminal_failure_preservation_does_not_grant_late_phase_credit(self):
        from types import SimpleNamespace as NS
        monitor=NS(seen=2,MARKERS=('a','b','c','d'));row=dict(owned={})
        capture=NS(progress=lambda:(['a','b','c'],[]));process=NS(returncode=2,observe=lambda:None)
        with self.assertRaisesRegex(ValueError,'MODEL_ORIGINAL_FAILURE'):
            owned.original.preserve_terminal_failure(process,capture,row,json.dumps(dict(error_code='MODEL_ORIGINAL_FAILURE')),'',monitor)
        self.assertEqual(monitor.seen,2);self.assertEqual(row['owned']['uncredited_terminal_markers'],['c'])
