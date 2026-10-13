"""P357 작은 합성 진단. 기존runtime862/제품/GO 검사가 아니다."""
import copy
import unittest
from unittest.mock import patch
import qualify_ram_admission_rejection as m

def fixture():
    codes=[{'public':'frozen93'}]+copy.deepcopy(m.CODE2)
    common=dict(schema_version=m.SCHEMA,selected_test_index=110,
        prior_runtime_plan={'runtime_source_qualified_individual_cases':103},current95_code_pins=codes,
        resource_watcher_cleanup_confirmed=True,actual_product_child_executed=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',product_complete=False)
    stats={'public':'exact-862'}
    light=dict(common,state='PASS_PRESERVED106_NEXT_QUEUE_NOT_ACTUAL_OR_GATE',runtime_contract_executions=862,
        contract_checkpoint_statistics=stats)
    fresh=dict(common,state='PASS_PRESERVED106_DISTINCT_FRESH_NOT_NATIVE_OR_PRODUCT',runtime_contract_executions=0,
        reused_light_contract_executions=862,reviewed_light_pin=m.PINS[0])
    h=dict(input_lock_handles_opened=1966,input_lock_handles_closed=1966,input_lock_cleanup_confirmed=True,
        input_lock_handles_remaining=0,active_reader_bindings=0,active_byte_streams=0,
        handle_close_failed_attempts=0,borrowed_byte_streams=None)
    frame=dict(frame_state='CLOSED',registered_live_frame=False,input_count=1658,input_bytes=121216238,
        actual_byte_boundaries=[],handles=h)
    root=dict(common,state='FAILED_NOT_ACCEPTED',error_code='TERMINAL_FAILURE_EXACT_STOP_NOT_PASS',
        resource_stop_reason=None,failure_diagnostic={'stage':'owned_parent'},runtime_contract_executions=0,
        accepted_exact_product_body_count=0,source_attempted=True,source_qualified=False,
        qualified_light_pin=m.PINS[0],independent_fresh_pin=m.PINS[1],qualified_contract_checkpoint_statistics=stats,
        terminal_parent_failure_sidecar_pin=m.PINS[3],terminal_source_frame=frame,
        actual_input_path_guard_selected=True,actual_boundary_adapter_restored=True,actual_source_path_guard_diagnostics=[],
        binding={'public':'binding'},selected_test_name='public-test')
    parent=dict(state='DEFERRED_NOT_STARTED',stop_reason='DEFERRED_STABLE_RESOURCE_WINDOW',
        resource_stop_reason='DEFERRED_STABLE_RESOURCE_WINDOW',operation_phase='admission',
        task='p204-r07-case-110-tests',binding=root['binding'],selected_test_names=['public-test'],
        job_final=None,owned_source_reader_passes=[],owned_tree_empty=True,cleanup_confirmed=True,
        exit_code=None,tests_passed=None,samples=[dict(system_cpu_percent=1,available_ram_percent=9.5,commit_used_percent=43) for _ in range(6)])
    parent.update({k:False for k in ('worker_created','job_assigned','writer_authorized',
        'actual_job_membership_checked','owned_limits_verified','heavy_work_started','actual_product_child_executed')})
    side=dict(state='REJECTED_ORIGINAL_PARENT_DIAGNOSTIC_NOT_ACCEPTED',original_validation_error=root['error_code'],
        diagnostic_only=True,runtime_accepted=False,owner_done=True,owner_cleanup_confirmed=True,owner_stop_reason=None,
        product_body_executed_by_diagnostic=False,live_guard_sampler_or_frame_restarted=False,
        original_parent_state_reason_preserved=True,original_frame_snapshot=frame,original_parent_document=parent)
    return copy.deepcopy((light,fresh,root,side))

class RamAdmissionTests(unittest.TestCase):
    def setUp(self):self.docs=fixture()
    def reject(self):
        with self.assertRaises((ValueError,KeyError)):m.validate(*self.docs)
    def test_exact_negative_only(self):
        before=copy.deepcopy(self.docs);r=m.validate(*self.docs)
        self.assertFalse(r['current_GO']);self.assertFalse(r['runtime_recovery_connected'])
        self.assertEqual(self.docs,before)
        # 실제 pre-job defer 문서는 job_final 키 자체를 생성하지 않는다.
        for key in ('job_final','exit_code','tests_passed'):
            del self.docs[3]['original_parent_document'][key]
        self.assertFalse(m.validate(*self.docs)['current_GO'])
    def test_CPU_or_hard_RAM_or_commit_stop_not_reclassified(self):
        for key,value in [('system_cpu_percent',100),('available_ram_percent',7),('available_ram_percent',10),('commit_used_percent',95)]:
            with self.subTest(key=key,value=value):
                docs=fixture();docs[3]['original_parent_document']['samples'][0][key]=value
                with self.assertRaises(ValueError):m.validate(*docs)
    def test_product_or_job_or_worker_never_admission_only(self):
        for key in ('actual_product_child_executed','job_assigned','worker_created','heavy_work_started'):
            with self.subTest(key=key):
                docs=fixture();docs[3]['original_parent_document'][key]=True
                with self.assertRaises(ValueError):m.validate(*docs)
    def test_unclean_or_false_zero_handle_rejected(self):
        self.docs[2]['terminal_source_frame']['handles']['input_lock_handles_remaining']=False;self.reject()
    def test_foreign_light_or_current_code_pair_rejected(self):
        self.docs[1]['reviewed_light_pin']=dict(m.PINS[0],sha256='0'*64);self.reject()
        docs=fixture();docs[0]['current95_code_pins'][-1]['sha256']='0'*64
        with self.assertRaises(ValueError):m.validate(*docs)
        with patch.object(m.Path,'open',side_effect=AssertionError('NO_FOREIGN_OR_OVERSIZE_READ')):
            with self.assertRaises(ValueError):m.load(dict(m.PINS[0],bytes=2**31))
    def test_before_byte_boundary_never_admission_only(self):
        self.docs[2]['terminal_source_frame']['actual_byte_boundaries'].append({'role':'before'});self.reject()
    def test_body_or_queue_promotion_rejected(self):
        self.docs[2]['runtime_plan']={'accepted':104};self.reject()
    def test_non_numeric_or_bool_RAM_rejected(self):
        self.docs[3]['original_parent_document']['samples'][0]['available_ram_percent']=True;self.reject()
