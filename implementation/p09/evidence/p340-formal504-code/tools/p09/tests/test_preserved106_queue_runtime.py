"""P340: current/following 합성 자료만 사용. 실제 제품/Native/수용 증거가 아니다."""
import copy,types,unittest
from unittest.mock import patch
import resume_preserved106_queue_runtime as m
import test_admission_classified_queue_runtime as oldtests
FIXTURES=None
FOLLOWING=False
TEMPLATE=None
LIGHT_TEMPLATE=None
CLOSING_TEMPLATE=None
CLOSING_TEMPLATE_BUILDS=0
PREQUALIFICATION=None
PREQUALIFICATION2=None
LITERAL_PRIOR_LIGHT=None
EPOCH_DOCUMENTS=None
NATIVE107_DOCUMENTS=None
NATIVE107_BASE=None
SCOPE_FAILURE_DOCUMENT=None
EPOCH272_DOCUMENTS=None
PARTIAL308_DOCUMENT=None
PENDING108_DOCUMENTS=None
PENDING108_BASE=None
SOURCE021_DOCUMENT=None
REVIEW404_DOCUMENT=None
REVIEW022_DOCUMENT=None

def fixture():
    global TEMPLATE
    if TEMPLATE is None:
        if FIXTURES is None:raise RuntimeError('FRESH_LITERAL100_SCOPE_REQUIRED')
        legacy,plan,names,binding,required,extras,baseline,added,healthy,prior=FIXTURES
        proxy=types.SimpleNamespace(**dict(m.m.__dict__,SCHEMA=m.SCHEMA,PASS=m.PASS,N=m.N,COUNT=m.COUNT,EXECUTED=m.EXECUTED,budget=m.budget))
        data=(legacy,plan,names,required,extras,baseline,added,healthy[0],healthy[1])
        with patch.object(oldtests,'m',proxy),patch.object(oldtests,'FIXTURES',data),patch.object(oldtests,'FOLLOWING',FOLLOWING):
            fields=oldtests.build_template()
        doc,body,pin,required,binding,extras,names,legacy,base,baseline,added=fields
        row=doc['contract_checkpoint_statistics']
        pin=dict(pin,path=f'{m.p.DIR}/cases/p340-case-{doc["selected_test_index"]:03}-run003.json')
        doc['closing_component']['case_receipt_pin']=pin
        doc.update(case_receipt_pin=pin,compound100_pin=m.COMPOUND,compound100_review_pin=m.COMPOUND_REVIEW,
            compound100_source_pin=m.COMPOUND_SOURCE,original93_pins=m.FROZEN93,
            prequalification_failure_reviews=[m.prequal_summary(z) for z in m.PREQUAL_SPECS],native107_epoch_root_pin=m.NATIVE107_ROOT,
            scope_fix_failure_review=m.scope_failure_summary(),epoch272_stop_review=m.epoch272_summary(),partial308_stop_review=m.partial308_summary(),pending108_product_review=m.pending108_summary(),preformal400_failure_review=m.preformal400_summary(),source021_CPU_stop_review=m.source021_summary(),review022_CPU_stop_review=m.review022_summary(),
            current95_code_pins=m.FROZEN93+[required[m.SELF],required[m.TEST]],
            runtime_contract_executions=0,contract_checkpoint_statistics=None,
            qualified_contract_checkpoint_statistics=row,reused_light_contract_executions=m.EXECUTED,
            qualified_light_pin=dict(path=m.p.DIR+'/p340-light-run001.v1.json',bytes=1,sha256='a'*64),
            independent_fresh_pin=dict(path=m.p.DIR+'/p340-light-review-run002.v1.json',bytes=1,sha256='b'*64),
            source_attempted=True,source_qualified=True,existing_body_replay_guard_verified=True)
        TEMPLATE=(doc,body,pin,required,binding,extras,names,legacy,base,baseline,added)
    return copy.deepcopy(TEMPLATE)

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.doc,self.body,self.pin,self.required,self.binding,self.extras,self.names,self.legacy,self.base,self.baseline,self.added=fixture()
        self.codes=self.doc['current95_code_pins']
    def record(self):
        return m.record(self.doc,self.body,self.pin,self.legacy,self.base,self.names,self.required,self.binding,
            self.extras,self.baseline,self.added,self.codes)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError,AttributeError)):self.record()
    def test_exact_synthetic_next_one(self):
        before=copy.deepcopy((self.doc,self.body));result=self.record()
        self.assertEqual(result['runtime_source_qualified_individual_cases'],self.base['runtime_source_qualified_individual_cases']+1)
        self.assertEqual((self.doc,self.body),before)
    def test_body_actual_child_false_denied(self):self.body['actual_product_child_executed']=False;self.reject()
    def test_full_scope_required(self):self.required.pop(m.SELF);self.reject()
    def test_partial_after_denied(self):self.body['owned_source_reader_passes'][1]['read_passes']-=1;self.reject()
    def test_incomplete_capture_denied(self):self.body['capture']['complete_streams']=False;self.reject()
    def test_job_cpu_not_relaxed(self):self.body['owned_limits_readback']['cpu_hard_cap_machine_percent']=100;self.reject()
    def test_job_affinity_not_relaxed(self):self.body['owned_limits_readback']['affinity_mask']=3;self.reject()
    def test_wrong_task_denied(self):self.body['task']='p204-r07-case-105-tests';self.reject()
    def test_exit_failure_denied(self):self.body['exit_code']=1;self.reject()
    def test_Native20_preserved(self):self.doc['closing_component']['source_frame']['handles']['native_open_pacing']['maximum_opens_per_second']=100;self.reject()
    def test_acquisition14_preserved(self):self.doc['closing_component']['source_frame']['handles']['acquisition_phase_pressure']['acquisition_maximum_reservations_per_second']=20;self.reject()
    def test_Native600_preserved(self):self.doc['closing_component']['source_frame']['handles']['maximum_lock_seconds']=601;self.reject()
    def test_duplicate_remaining_denied(self):self.doc['closing_component']['source_frame']['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject()
    def test_identity_count_denied(self):self.doc['closing_component']['source_frame']['held_identity_after_owned_cleanup']['regular_file_count']-=1;self.reject()
    def test_reader_remaining_denied(self):self.doc['closing_component']['source_frame']['handles']['active_reader_bindings']=1;self.reject()
    def test_cleanup_missing_denied(self):self.doc['resource_watcher_cleanup_confirmed']=False;self.reject()
    def test_wrong_schema_denied(self):self.doc['schema_version']='wrong';self.reject()
    def test_more_than_one_denied(self):self.doc['accepted_exact_product_body_count']=2;self.reject()
    def test_wrong_cursor_denied(self):self.doc['prior_runtime_plan']['next_runtime_index']+=1;self.reject()
    def test_wrong_binding_denied(self):self.body['binding']['expected_test_count']=248;self.reject()
    def test_gate_NOT_PASS(self):self.doc['P09_gate']='PASS';self.reject()
    def test_reuse_exact_count(self):self.doc['reused_light_contract_executions']-=1;self.reject()
    def test_actual_claims_no_new_contract_execution(self):self.doc['runtime_contract_executions']=m.EXECUTED;self.reject()
    def test_no_fabricated_current_checkpoints(self):self.doc['contract_checkpoint_statistics']=self.doc['qualified_contract_checkpoint_statistics'];self.reject()
    def test_startup_limits_immutable(self):self.doc['startup_limits']['own_priority']='Normal';self.reject()
    def test_source_attempt_required(self):self.doc['source_attempted']=False;self.reject()
    def test_source_qualified_required(self):self.doc['source_qualified']=False;self.reject()
    def test_independent_fresh_required(self):self.doc['independent_fresh_pin']=None;self.reject()
    def test_original_return_record_required(self):self.doc['parent_return_status_recorded_before_after_parent_guard']=False;self.reject()
    def test_bool_not_exit_zero(self):self.doc['original_parent_return_code']=False;self.reject()
    def test_original_aggregate_required(self):self.doc['aggregate_post_reader_connection_verified']=False;self.reject()
    def test_original_byte_pin_not_subset(self):self.doc['closing_component']['source_frame']['actual_byte_boundaries'][1]['actual_byte_pins'].pop();self.reject()
    def test_original93_no_drift(self):self.doc['original93_pins'][0]['sha256']='0'*64;self.reject()
    def test_rebound_validator_never_changes_original_globals(self):
        self.record();self.assertEqual(m.m.N,1654);self.assertEqual(m.x.N,1656);self.assertEqual(m.m.SCHEMA,'hwpx-agent.p09-admission-classified-queue-runtime-pair/v4')

def light_fixture():
    global LIGHT_TEMPLATE
    if LIGHT_TEMPLATE is None:
        # 원 full fixture를 한 번만 생성한 뒤 필요한 LIGHT projection을 별도로 보관.
        # 매 테스트 full Native frame/body를 복사하고 곧바로 폐기하는 비용만 제거한다.
        fixture()
        d,_,_,required,binding,extras,names,_,base,baseline,added=TEMPLATE
        doc=dict(d)
        for key in ('closing_component','case_receipt_pin','runtime_plan','terminal_source_frame'):doc.pop(key,None)
        row=doc['qualified_contract_checkpoint_statistics']
        doc.update(state=m.LIGHT,runtime_contract_executions=m.EXECUTED,contract_checkpoint_statistics=row,
            own_queue_contract_tests_passed=m.COUNT,synthetic_following_queue_contract_tests_passed=m.COUNT,
            accepted_exact_product_body_count=0,actual_product_child_executed=False,source_attempted=False,source_qualified=False,
            original_parent_capture_adapter_selected=False,diagnostic_parent_connection_selected=False)
        LIGHT_TEMPLATE=copy.deepcopy((doc,required,binding,extras,names,base,baseline,added))
    # 변경용 중첩 자료는 매번 새 deep-copy. 동일 객체 또는 이전 테스트 변이를 공유하지 않는다.
    return copy.deepcopy(LIGHT_TEMPLATE)

class QualificationTests(unittest.TestCase):
    def setUp(self):
        self.light,self.required,self.binding,self.extras,self.names,self.base,self.baseline,self.added=light_fixture()
        self.codes=self.light['current95_code_pins'];self.pin=dict(path=m.p.DIR+'/p340-light-run001.v1.json',bytes=1,sha256='a'*64)
        self.fresh=copy.deepcopy(self.light)
        self.fresh.update(state=m.FRESH,runtime_contract_executions=0,contract_checkpoint_statistics=None,
            reviewed_light_pin=self.pin,reused_light_contract_executions=m.EXECUTED)
    def light_check(self):
        m.light_contract(self.light,self.base,self.names,self.required,self.binding,self.extras,self.baseline,self.added,self.codes)
    def fresh_check(self):
        m.fresh_contract(self.fresh,self.light,self.pin,self.base,self.names,self.required,self.binding,self.extras,self.baseline,self.added,self.codes)
    def reject_light(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.light_check()
    def reject_fresh(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.fresh_check()
    def test_light_actual_contracts_and_no_product(self):self.light_check()
    def test_distinct_fresh_reuses_no_new_executions(self):self.fresh_check()
    def test_light_no_incomplete_metadata(self):self.light['preparation_IO']['finished']=False;self.reject_light()
    def test_light_no_Native(self):self.light['source_attempted']=True;self.reject_light()
    def test_light_no_product(self):self.light['actual_product_child_executed']=True;self.reject_light()
    def test_light_all_contracts(self):self.light['runtime_contract_executions']-=1;self.reject_light()
    def test_light_every_checkpoint(self):self.light['contract_checkpoint_statistics']['successful_after_test_checks']-=1;self.reject_light()
    def test_fresh_same_light(self):self.fresh['reviewed_light_pin']=dict(self.pin,sha256='c'*64);self.reject_fresh()
    def test_fresh_no_claimed_tests(self):self.fresh['runtime_contract_executions']=m.EXECUTED;self.reject_fresh()
    def test_fresh_no_fabricated_checkpoints(self):self.fresh['contract_checkpoint_statistics']=self.light['contract_checkpoint_statistics'];self.reject_fresh()
    def test_fresh_reuse_exact_count(self):self.fresh['reused_light_contract_executions']-=1;self.reject_fresh()
    def test_no_fresh_before_product(self):
        q=types.SimpleNamespace(freshes=[])
        with self.assertRaises(ValueError):m.select_go(q,self.base)
    def test_stale_fresh_before_product_denied(self):
        q=types.SimpleNamespace(freshes=[(self.pin,dict(self.fresh,prior_runtime_plan={}),self.pin,self.light)])
        with self.assertRaises(ValueError):m.select_go(q,self.base)
    def test_current_fresh_selects_without_child(self):
        q=types.SimpleNamespace(freshes=[(self.pin,self.fresh,self.pin,self.light)])
        self.assertEqual(m.select_go(q,self.base)[1],self.fresh)
    def test_empty_light_before_fresh_denied(self):
        with self.assertRaises(ValueError):m.select_light(types.SimpleNamespace(lights=[]),self.base)

class CompoundTests(unittest.TestCase):
    def setUp(self):
        self.doc,self.review,self.source,self.base,self.required,self.checked,self.codes=copy.deepcopy(FIXTURES[-1])
        self.legacy,self.names=FIXTURES[0],FIXTURES[2]
    def check(self):
        return m.compound(self.doc,self.review,self.source,self.legacy,self.base,self.names,self.required,self.checked,self.codes)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.check()
    def test_literal100_reused_not_rerun(self):
        before=copy.deepcopy((self.doc,self.review,self.source));self.assertEqual(self.check()['runtime_source_qualified_individual_cases'],100)
        self.assertEqual((self.doc,self.review,self.source),before)
    def test_failed106_not_promoted(self):self.doc['original_failed_root_accepted']=True;self.reject()
    def test_partial_after_not_promoted(self):self.doc['original_partial_after_hash_completed']=True;self.reject()
    def test_compound_one_exact(self):self.doc['accepted_exact_compound_case_count']=2;self.reject()
    def test_compound_current93_same(self):self.doc['current93_code_pins'].pop();self.reject()
    def test_compound_source_complete(self):self.source['source_frame']['actual_byte_boundaries'].pop();self.reject()
    def test_compound_original_no_product_rerun(self):self.doc['actual_product_child_executed']=True;self.reject()
    def test_compound_source_pin_immutable(self):self.doc['separate_source_frame_pin']=dict(m.COMPOUND_SOURCE,bytes=1);self.reject()
    def test_compound_review_pin_immutable(self):self.doc['review_pin']=dict(m.COMPOUND_REVIEW,bytes=1);self.reject()

class StopTests(unittest.TestCase):
    def setUp(self):
        d,b,p,required,binding,extras,names,legacy,base,baseline,added=fixture()
        self.required,self.binding,self.extras,self.names,self.base,self.baseline,self.added=required,binding,extras,names,base,baseline,added
        d.update(state='FAILED_NOT_ACCEPTED',error_code='STOP_SUSTAINED_SYSTEM_CPU',resource_stop_reason='STOP_SUSTAINED_SYSTEM_CPU',
            accepted_exact_product_body_count=0,actual_product_child_executed=False,source_qualified=False,
            original_parent_capture_adapter_selected=False,diagnostic_parent_connection_selected=False,
            failure_diagnostic=dict(stage='source_frame_acquire'))
        d.pop('runtime_plan',None);d.pop('case_receipt_pin',None);d.pop('closing_component',None)
        frame=copy.deepcopy(fixture()[0]['closing_component']['source_frame'])
        frame.update(frame_state='CLOSED',registered_live_frame=False,held_identity_after_owned_cleanup=None,actual_byte_boundaries=[])
        frame['handles']['borrowed_byte_streams']=None
        self.doc=d;self.doc['terminal_source_frame']=frame
    def check(self):
        return m.stopped(self.doc,self.base,self.required,self.binding,self.extras,self.baseline,self.added,self.names)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.check()
    def test_clean_pre_product_STOP_not_advance(self):
        self.assertEqual(self.check()['accepted_count_delta'],0);self.assertNotIn('runtime_plan',self.doc)
    def test_post_product_STOP_denied(self):self.doc['failure_diagnostic']['stage']='source_frame_closing';self.reject()
    def test_actual_child_denied(self):self.doc['actual_product_child_executed']=True;self.reject()
    def test_handle_remaining_denied(self):self.doc['terminal_source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
    def test_unregistered_required(self):self.doc['terminal_source_frame']['registered_live_frame']=True;self.reject()
    def test_unknown_cleanup_denied(self):self.doc['resource_watcher_cleanup_confirmed']=False;self.reject()
    def test_native_attempt_without_frame_denied(self):self.doc.pop('terminal_source_frame');self.reject()
    def test_unknown_stop_denied(self):self.doc['error_code']='UNKNOWN';self.reject()

class PinTests(unittest.TestCase):
    def test_exact_pin(self):
        pin=dict(path=m.p.DIR+'/p340-light-run001.v1.json',bytes=1,sha256='a'*64);self.assertEqual(m.pin_argument(pin,'light'),pin)
    def test_parent_traversal_denied(self):
        with self.assertRaises(ValueError):m.pin_argument(dict(path=m.p.DIR+'/../p340-light-run001.v1.json',bytes=1,sha256='a'*64),'light')
    def test_other_namespace_denied(self):
        with self.assertRaises(ValueError):m.pin_argument(dict(path=m.p.DIR+'/p335-light-run001.v1.json',bytes=1,sha256='a'*64),'light')
    def test_bool_bytes_denied(self):
        with self.assertRaises(ValueError):m.pin_argument(dict(path=m.p.DIR+'/p340-light-run001.v1.json',bytes=True,sha256='a'*64),'light')
    def test_unknown_field_denied(self):
        with self.assertRaises(ValueError):m.pin_argument(dict(path=m.p.DIR+'/p340-light-run001.v1.json',bytes=1,sha256='a'*64,secret='not-a-secret'),'light')

class PrequalificationTests(unittest.TestCase):
    def setUp(self):
        if PREQUALIFICATION is None:raise RuntimeError('LITERAL_PREFORMAL_FAILURE_REQUIRED')
        self.doc=copy.deepcopy(PREQUALIFICATION)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):m.prequal_review(self.doc)
    def test_prequal_failure_not_acceptance(self):
        before=copy.deepcopy(self.doc);self.assertFalse(m.prequal_review(self.doc)['contract_qualification_pass']);self.assertEqual(self.doc,before)
    def test_prequal_unknown_cleanup_denied(self):self.doc['resource_watcher_cleanup_confirmed']=False;self.reject()
    def test_prequal_Native_attempt_denied(self):self.doc['source_attempted']=True;self.reject()
    def test_prequal_actual_product_denied(self):self.doc['actual_product_child_executed']=True;self.reject()
    def test_prequal_checkpoint_count_denied(self):self.doc['contract_checkpoint_statistics']['stopped_tests']=69;self.reject()
    def test_prequal_missing_failures_denied(self):self.doc['contract_failures']=[];self.reject()
    def test_prequal_PASS_denied(self):self.doc['state']=m.LIGHT;self.reject()
    def test_prequal_old_code_pin_drift_denied(self):self.doc['current95_code_pins'][-1]['bytes']+=1;self.reject()

class Prequalification2Tests(unittest.TestCase):
    def setUp(self):
        if PREQUALIFICATION2 is None:raise RuntimeError('LITERAL_SECOND_PREFORMAL_FAILURE_REQUIRED')
        self.doc=copy.deepcopy(PREQUALIFICATION2)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):m.prequal_review(self.doc,m.PREQUAL_SPECS[1])
    def test_second_prequal_not_acceptance(self):
        self.assertFalse(m.prequal_review(self.doc,m.PREQUAL_SPECS[1])['contract_qualification_pass'])
    def test_second_prequal_cleanup_denied(self):self.doc['resource_watcher_cleanup_confirmed']=False;self.reject()
    def test_second_prequal_Native_denied(self):self.doc['source_attempted']=True;self.reject()
    def test_second_prequal_product_denied(self):self.doc['actual_product_child_executed']=True;self.reject()
    def test_second_prequal_checkpoint_denied(self):self.doc['contract_checkpoint_statistics']['stopped_tests']=77;self.reject()
    def test_second_prequal_missing_failures_denied(self):self.doc['contract_failures']=[];self.reject()
    def test_second_prequal_PASS_denied(self):self.doc['state']=m.LIGHT;self.reject()
    def test_second_prequal_code_drift_denied(self):self.doc['current95_code_pins'][-1]['bytes']+=1;self.reject()

class ReplayGuardTests(unittest.TestCase):
    def test_no_existing_body_allowed(self):m.existing_body_contract([], {})
    def test_only_exact_reviewed_zero_allowed(self):
        name=m.p.DIR+'/cases/p340-case-107-run003.json';m.existing_body_contract([name],{name:dict(path=name,bytes=0,sha256=m.hashlib.sha256(b'').hexdigest())})
    def test_unknown_body_denied(self):
        with self.assertRaises(ValueError):m.existing_body_contract(['unknown'],{})
    def test_nonempty_body_denied(self):
        with self.assertRaises(ValueError):m.existing_body_contract(['x'],{'x':dict(path='x',bytes=1,sha256=m.hashlib.sha256(b'').hexdigest())})
    def test_mismatched_zero_hash_denied(self):
        with self.assertRaises(ValueError):m.existing_body_contract(['x'],{'x':dict(path='x',bytes=0,sha256='a'*64)})
    def test_duplicate_inventory_denied(self):
        with self.assertRaises(ValueError):m.existing_body_contract(['x','x'],{})
    def test_runtime_replay_guard_required(self):
        d,b,p,required,binding,extras,names,legacy,base,baseline,added=fixture();d['existing_body_replay_guard_verified']=False
        with self.assertRaises(ValueError):m.record(d,b,p,legacy,base,names,required,binding,extras,baseline,added,d['current95_code_pins'])

class PriorLightTests(unittest.TestCase):
    def setUp(self):
        if LITERAL_PRIOR_LIGHT is None:raise RuntimeError('LITERAL_PRIOR172_REQUIRED')
        self.doc=copy.deepcopy(LITERAL_PRIOR_LIGHT)
        self.legacy,self.plan,self.names,self.binding,self.required,self.extras,self.baseline,self.added,_,_=FIXTURES
        # archive-bound qualificationは100/107。following fixtureの101/108を偽装しない。
        self.plan=copy.deepcopy(self.doc['prior_runtime_plan'])
    def check(self):
        return m.prior_light_review(self.doc,self.plan,self.names,self.required,self.binding,self.extras,self.baseline,self.added)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.check()
    def test_prior172_not_current_GO(self):self.assertFalse(self.check()['current_actual_GO'])
    def test_prior172_checkpoint_count_denied(self):self.doc['contract_checkpoint_statistics']['stopped_tests']=171;self.reject()
    def test_prior172_NOT_Native(self):self.doc['source_attempted']=True;self.reject()
    def test_prior172_NO_product(self):self.doc['actual_product_child_executed']=True;self.reject()
    def test_prior172_old_code_immutable(self):self.doc['current95_code_pins'][-1]['bytes']+=1;self.reject()
    def test_prior172_unknown_cleanup_denied(self):self.doc['resource_watcher_cleanup_confirmed']=False;self.reject()

class ImportedAPIAndBudgetTests(unittest.TestCase):
    def test_original720_reference_available(self):self.assertEqual(m.m.m.m.META_READ_LIMIT,720)
    def test_original_capture_classes_available(self):self.assertTrue(issubclass(m.m.m.a.Capture,m.m.m.m.support.candidate.Capture))
    def test_original_native_and_parent_connections_available(self):
        self.assertTrue(callable(m.m.profile.InputLocks));self.assertTrue(callable(m.m.connection.ParentConnection))
        self.assertTrue(callable(m.m.connection.TimedInputLocks));self.assertTrue(callable(m.m.m.job_contract));self.assertTrue(callable(m.m.m.early_contract))
    def test_reserve718_allowed(self):self.assertTrue(m.reserved_post_reads(types.SimpleNamespace(shared_budget=dict(read_calls=718))))
    def test_reserve719_denied(self):
        with self.assertRaises(ValueError):m.reserved_post_reads(types.SimpleNamespace(shared_budget=dict(read_calls=719)))
    def test_reserve_bool_denied(self):
        with self.assertRaises(ValueError):m.reserved_post_reads(types.SimpleNamespace(shared_budget=dict(read_calls=True)))

class EpochReviewTests(unittest.TestCase):
    def setUp(self):
        if EPOCH_DOCUMENTS is None:raise RuntimeError('IMMUTABLE_EPOCH198_REQUIRED')
        self.light,self.fresh,self.failed=copy.deepcopy(EPOCH_DOCUMENTS)
        _,_,self.names,self.binding,self.required,self.extras,self.baseline,self.added,_,_=FIXTURES
        self.plan=copy.deepcopy(self.failed['prior_runtime_plan'])
    def check(self):
        return m.epoch_review(self.light,self.fresh,self.failed,self.plan,self.names,self.required,self.binding,self.extras,self.baseline,self.added)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.check()
    def test_epoch_failure_not_GO_or_product(self):self.assertFalse(self.check()['current_actual_GO'])
    def test_epoch_native_attempt_denied(self):self.failed['source_attempted']=True;self.reject()
    def test_epoch_product_denied(self):self.failed['actual_product_child_executed']=True;self.reject()
    def test_epoch_missing_cleanup_denied(self):self.failed['resource_watcher_cleanup_confirmed']=False;self.reject()
    def test_epoch_wrong_failure_phase_denied(self):self.failed['failure_diagnostic']['stage']='owned_parent';self.reject()
    def test_epoch_wrong_line_denied(self):self.failed['failure_diagnostic']['locations'][0]['line']=460;self.reject()
    def test_epoch_failed_cursor_not_advance(self):self.failed['runtime_plan']={};self.reject()
    def test_epoch_parent_capture_unknown_denied(self):self.failed['original_parent_capture_adapter_selected']=True;self.reject()

class SameReaderCacheTests(unittest.TestCase):
    def fake(self):
        calls=[];checks=[]
        q=types.SimpleNamespace(reader=types.SimpleNamespace(checkpoint=lambda:checks.append(True),snapshots={}))
        def read(name):
            calls.append(name);q.reader.snapshots[name]=dict(bytes=1)
            return dict(state=m.LIGHT,source_attempted=False,actual_product_child_executed=False,closing_component=None)
        q.json=read
        return q,calls,checks
    def test_same_reader_light_read_once(self):
        q,calls,checks=self.fake();read=m.cached_light_json(q);name=m.p.DIR+'/p340-light-run007.v1.json'
        read(name);read(name);self.assertEqual(calls,[name]);self.assertEqual(len(checks),1)
    def test_separate_reader_wrapper_not_cross_command_cache(self):
        q,calls,_=self.fake();name=m.p.DIR+'/p340-light-run007.v1.json'
        m.cached_light_json(q)(name);m.cached_light_json(q)(name);self.assertEqual(len(calls),2)
    def test_at_most_one_light_json_retained(self):
        q,calls,_=self.fake();read=m.cached_light_json(q);a=m.p.DIR+'/p340-light-run007.v1.json';b=m.p.DIR+'/p340-light-run009.v1.json'
        read(a);read(b);read(a);self.assertEqual(calls,[a,b,a])

class Native107EpochTests(unittest.TestCase):
    def setUp(self):
        if NATIVE107_DOCUMENTS is None or NATIVE107_BASE is None:raise RuntimeError('LITERAL_NATIVE107_REQUIRED')
        self.root,self.body,self.light,self.fresh=copy.deepcopy(NATIVE107_DOCUMENTS)
        self.base=copy.deepcopy(NATIVE107_BASE)
        self.legacy,_,self.names,self.binding,self.required,self.extras,self.baseline,self.added,_,_=FIXTURES
    def check(self):
        return m.native107_epoch(self.root,self.body,self.light,self.fresh,self.legacy,self.base,self.names,self.required,self.binding,self.extras,self.baseline,self.added)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.check()
    def test_archived_native107_keeps101_no_rerun(self):
        before=copy.deepcopy((self.root,self.body));self.assertEqual(self.check()['runtime_source_qualified_individual_cases'],101)
        self.assertEqual((self.root,self.body),before)
    def test_native107_wrong_body_pin(self):self.root['case_receipt_pin']=dict(m.NATIVE107_BODY,bytes=0);self.reject()
    def test_native107_no_fake_current_native(self):self.root['current95_code_pins'][-1]['bytes']+=1;self.reject()
    def test_native107_source_scope_not_reduced(self):self.body['source_freeze'].pop();self.reject()
    def test_native107_cleanup_required(self):self.root['resource_watcher_cleanup_confirmed']=False;self.reject()
    def test_native107_child_required(self):self.body['actual_product_child_executed']=False;self.reject()
    def test_native107_next_cursor_not_skipped(self):self.root['runtime_plan']['next_runtime_index']=109;self.reject()
    def test_native107_exact_fresh_pin(self):self.root['independent_fresh_pin']=dict(m.NATIVE107_FRESH,bytes=0);self.reject()

class ScopeFailureReviewTests(unittest.TestCase):
    def setUp(self):
        if SCOPE_FAILURE_DOCUMENT is None:raise RuntimeError('LITERAL_SCOPE_FAILURE_REQUIRED')
        self.doc=copy.deepcopy(SCOPE_FAILURE_DOCUMENT)
    def check(self):return m.scope_failure_review(self.doc)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.check()
    def test_scope_failure_not256_PASS(self):
        before=copy.deepcopy(self.doc);self.assertTrue(self.check()['qualification256_not_passed'])
        self.assertEqual(self.doc,before)
    def test_scope_failure_not_product(self):self.doc['actual_product_child_executed']=True;self.reject()
    def test_scope_failure_cleanup_required(self):self.doc['resource_watcher_cleanup_confirmed']=False;self.reject()
    def test_scope_failure_exact_ID(self):self.doc['contract_failures']=[];self.reject()
    def test_scope_failure_cursor_not_advance(self):self.doc['prior_runtime_plan']['runtime_source_qualified_individual_cases']=102;self.reject()
    def test_scope_failure_exact128_not256(self):self.doc['contract_checkpoint_statistics']['started_tests']=256;self.reject()
    def test_scope_failure_original_no_Native(self):self.doc['source_attempted']=True;self.reject()

class AncestorPlanningTests(unittest.TestCase):
    def test_all_original308_directories_retained(self):
        required=FIXTURES[4];old={m.PurePosixPath('.')}
        for name in required:old.update(m.PurePosixPath(name).parents)
        self.assertEqual(m.ancestor_directories(required),old);self.assertEqual(len(old),308)
    def test_shared_parents_are_not_excluded(self):
        required={'a/b/one':{},'a/b/two':{},'a/c/three':{}}
        self.assertEqual(m.ancestor_directories(required),set(map(m.PurePosixPath,['.','a','a/b','a/c'])))
    def test_root_file_has_root_parent(self):self.assertEqual(m.ancestor_directories({'one':{}}),{m.PurePosixPath('.')})
    def test_ancestor_input_mapping_not_mutated(self):
        required={'a/b/one':{'bytes':1}};before=copy.deepcopy(required);m.ancestor_directories(required);self.assertEqual(required,before)

class QualificationCacheTests(unittest.TestCase):
    def fake(self,oversized=False,product=False):
        calls=[];checks=[];q=types.SimpleNamespace(reader=types.SimpleNamespace(checkpoint=lambda:checks.append(True),snapshots={}))
        def read(name):
            calls.append(name);q.reader.snapshots[name]=dict(bytes=131073 if oversized else 100)
            return dict(state=m.FRESH if 'light-review' in name else m.LIGHT,source_attempted=product,
                actual_product_child_executed=product,closing_component=None)
        q.json=read;return q,calls,checks
    def test_light_and_fresh_each_one_retained(self):
        q,calls,checks=self.fake();read=m.cached_light_json(q);a=m.p.DIR+'/p340-light-run011.v1.json';b=m.p.DIR+'/p340-light-review-run012.v1.json'
        read(a);read(b);read(a);read(b);self.assertEqual(calls,[a,b]);self.assertEqual(len(checks),2)
    def test_oversized_not_cached(self):
        q,calls,_=self.fake(oversized=True);read=m.cached_light_json(q);a=m.p.DIR+'/p340-light-review-run012.v1.json';read(a);read(a);self.assertEqual(len(calls),2)
    def test_product_not_cached(self):
        q,calls,_=self.fake(product=True);read=m.cached_light_json(q);a=m.p.DIR+'/p340-light-review-run012.v1.json';read(a);read(a);self.assertEqual(len(calls),2)
    def test_cache_checkpoint_failure_not_swallowed(self):
        q,_,_=self.fake();read=m.cached_light_json(q);a=m.p.DIR+'/p340-light-review-run012.v1.json';read(a)
        q.reader.checkpoint=lambda:(_ for _ in ()).throw(ValueError('STOP'))
        with self.assertRaises(ValueError):read(a)

class Prior272StopReviewTests(unittest.TestCase):
    def setUp(self):
        if EPOCH272_DOCUMENTS is None:raise RuntimeError('LITERAL_PRIOR272_STOPS_REQUIRED')
        self.light,self.fresh,self.native,self.metadata=copy.deepcopy(EPOCH272_DOCUMENTS)
        _,_,self.names,self.binding,self.required,self.extras,self.baseline,self.added,_,_=FIXTURES
        self.plan=copy.deepcopy(self.native['prior_runtime_plan'])
    def check(self):
        return m.epoch272_review(self.light,self.fresh,self.native,self.metadata,self.plan,self.names,self.required,self.binding,self.extras,self.baseline,self.added)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.check()
    def test_prior272_current_GO_false(self):self.assertFalse(self.check()['current_actual_GO'])
    def test_failed_originals_not_mutated(self):
        before=copy.deepcopy((self.native,self.metadata));self.check();self.assertEqual((self.native,self.metadata),before)
    def test_native_stop_product_denied(self):self.native['actual_product_child_executed']=True;self.reject()
    def test_native_stop_cleanup_required(self):self.native['resource_watcher_cleanup_confirmed']=False;self.reject()
    def test_native163_exact(self):self.native['terminal_source_frame']['handles']['input_lock_handles_opened']=164;self.reject()
    def test_native_open_handle_remaining_denied(self):self.native['terminal_source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
    def test_metadata_review_not_finished(self):self.metadata['preparation_IO']['finished']=True;self.reject()
    def test_anchor_no_Native_required(self):self.metadata['source_attempted']=True;self.reject()
    def test_cpu_stop_not_silent_GO(self):self.native['resource_stop_reason']=None;self.reject()
    def test_previous272_not_new308(self):self.light['runtime_contract_executions']=m.EXECUTED;self.reject()

class LightProjectionTests(unittest.TestCase):
    def test_light_projection_does_not_mutate_full_template(self):
        fixture();before=copy.deepcopy(TEMPLATE);light_fixture();self.assertEqual(TEMPLATE,before)
    def test_each_light_test_has_independent_nested_copy(self):
        first=light_fixture();first[0]['startup_limits']['own_priority']='Normal';second=light_fixture()
        self.assertEqual(second[0]['startup_limits']['own_priority'],'BelowNormal')
    def test_light_has_no_unused_Native_frame(self):
        d=light_fixture()[0];self.assertNotIn('closing_component',d);self.assertNotIn('case_receipt_pin',d);self.assertNotIn('terminal_source_frame',d)
    def test_required_pins_remain_all1658(self):
        light=light_fixture();self.assertEqual(light[1],FIXTURES[4]);self.assertEqual(len(light[1]),1658)

class Partial308StopReviewTests(unittest.TestCase):
    def check(self,doc):
        _,_,names,binding,required,extras,baseline,added,_,_=FIXTURES
        return m.partial308_review(doc,doc['prior_runtime_plan'],names,required,binding,extras,baseline,added)
    def test_partial12_not308_PASS(self):
        doc=copy.deepcopy(PARTIAL308_DOCUMENT);before=copy.deepcopy(doc)
        self.assertTrue(self.check(doc)['qualification308_not_passed']);self.assertEqual(doc,before)
    def test_partial_after12_fabrication_denied(self):
        doc=copy.deepcopy(PARTIAL308_DOCUMENT);doc['contract_checkpoint_statistics']['successful_after_test_checks']=12
        with self.assertRaises(ValueError):self.check(doc)


def build_closing_template():
    doc,required,binding,extras,names,_,baseline,added=light_fixture()
    base=copy.deepcopy(PENDING108_BASE)
    scope=(FIXTURES[0],base,names,binding,required,extras,baseline,added,FIXTURES[8],FIXTURES[9])
    doc.update(state=m.C_REVIEW,prior_runtime_plan=base,selected_test_index=108,selected_test_name=m.P108_NAME,
        reused_light_contract_executions=0,successful_product_reexecution_allowed=False,
        original_failed_root_accepted=False,original_partial_after_hash_completed=False,
        independent_source_frame_attempted=False,independent_source_frame_qualified=False,
        source_kind='INDEPENDENT_CURRENT95_AFTER_COMPLETED108_NOT_ORIGINAL_PARTIAL_AFTER',
        original_executed_source_pins=list(m.pending108_scope(required).values()),current_source_transition_paths=[m.SELF,m.TEST])
    review=copy.deepcopy(doc);rp=dict(path=m.p.DIR+'/p340-closing-review-run019.v1.json',bytes=1,sha256='a'*64)
    source=copy.deepcopy(doc)
    frame=fixture()[0]['closing_component']['source_frame']
    events=frame['handles']['lock_timing_diagnostic']['explicit_phase_events']
    frame['handles']['lock_timing_diagnostic']['explicit_phase_events']=[events[0],events[1],events[-1]]
    source.update(state=m.C_SOURCE,runtime_contract_executions=0,contract_checkpoint_statistics=None,
        reused_light_contract_executions=m.EXECUTED,qualified_contract_checkpoint_statistics=review['contract_checkpoint_statistics'],
        closing_review_pin=copy.deepcopy(rp),independent_source_frame_attempted=True,independent_source_frame_qualified=True,
        source_frame=frame,source_path_guard_diagnostics=[dict(native_metadata_queries_attempted=m.N,fresh_held_metadata_queries=m.N,original_path_guard_predicates=3*m.N,original_reader_root_restored=True,active_path_guard_adapter=False,pathname_metadata_probes=0,original_stream_identity_check_retained=True,metadata_reused_between_source_requests=False,added_native_queries_recorded_separately_from_original_lock_checks=True,kernel_call_reduction_or_CPU_freeze_improvement_claimed=False) for _ in range(2)],early_source_runtime_connection_verified=True,early_source_native_and_byte_guard_connected=True)
    sp=dict(path=m.p.DIR+'/p340-closing-source-run020.v1.json',bytes=1,sha256='b'*64)
    accepted=copy.deepcopy(source);accepted.pop('source_frame');accepted['source_path_guard_diagnostics']=[]
    accepted.update(state=m.C_ACCEPT,independent_source_frame_attempted=False,independent_source_frame_qualified=False,
        closing_source_pin=copy.deepcopy(sp),accepted_exact_compound_case_count=1,semantic_body_capture_pass_count=1,
        runtime_plan=m.g.advance(scope[0],base,names,108))
    return review,source,accepted,rp,sp,scope,doc['current95_code_pins']


def closing_fixture():
    global CLOSING_TEMPLATE,CLOSING_TEMPLATE_BUILDS
    # 불변 runner-local 합성 원형만 한 번 만든다. 모든 검사 자료는 새 독립 deep-copy.
    # 실제 receipt/Native 결과/검사 PASS를 cache하지 않으며 runner 경계에서 reset한다.
    if CLOSING_TEMPLATE is None:
        CLOSING_TEMPLATE=build_closing_template();CLOSING_TEMPLATE_BUILDS+=1
    review,source,accepted,rp,sp,scope,codes=CLOSING_TEMPLATE
    review,source,accepted,rp,sp,plan,fields,codes=copy.deepcopy(
        (review,source,accepted,rp,sp,scope[1],scope[3:8],codes))
    fresh_scope=(scope[0],plan,scope[2],*fields,scope[8],scope[9])
    return review,source,accepted,rp,sp,fresh_scope,codes


class Pending108ProductTests(unittest.TestCase):
    def setUp(self):
        if PENDING108_DOCUMENTS is None:raise RuntimeError('EXACT_COMPLETED108_REQUIRED')
        self.root,self.body,self.light,self.fresh=copy.deepcopy(PENDING108_DOCUMENTS)
        _,_,self.names,self.binding,self.required,self.extras,self.baseline,self.added,_,_=FIXTURES
        self.base=copy.deepcopy(PENDING108_BASE)
    def check(self):
        return m.pending108_review(self.root,self.body,self.light,self.fresh,self.base,self.names,self.required,self.binding,self.extras,self.baseline,self.added)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.check()
    def test_original_success_not_reexecute(self):
        before=copy.deepcopy((self.root,self.body));self.assertFalse(self.check()['successful_product_reexecution_allowed']);self.assertEqual((self.root,self.body),before)
    def test_body_actual_child_required(self):self.body['actual_product_child_executed']=False;self.reject()
    def test_body_exit_must_zero(self):self.body['exit_code']=1;self.reject()
    def test_root_failed_must_preserved(self):self.root['state']=m.PASS;self.reject()
    def test_partial_after_not_full(self):self.body['owned_source_reader_passes'][1]['read_passes']=1658;self.reject()
    def test_capture_complete_required(self):self.body['capture']['complete_streams']=False;self.reject()
    def test_exact_test_name(self):self.body['passed_test_names']=[];self.reject()
    def test_correct_original_code95(self):self.root['current95_code_pins'][-1]['bytes']+=1;self.reject()
    def test_before_scope_not_subset(self):self.body['source_freeze'].pop();self.reject()
    def test_job_cpu_not_relaxed(self):self.body['owned_limits_readback']['cpu_hard_cap_machine_percent']=100;self.reject()
    def test_cleanup_required(self):self.body['cleanup_confirmed']=False;self.reject()
    def test_no_active_job(self):self.body['job_final']['active_processes']=1;self.reject()
    def test_root_sidecar_pin_exact(self):self.root['terminal_parent_failure_sidecar_pin']['bytes']+=1;self.reject()
    def test_all1966_native_closed(self):self.root['terminal_source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
    def test_no_committed_original_partial(self):self.root['terminal_source_frame']['frame_state']='COMMITTED';self.reject()
    def test_source_before_pins_exact(self):self.root['terminal_source_frame']['actual_byte_boundaries'][0]['actual_byte_pins'].pop();self.reject()
    def test_cursor_still101(self):self.base['runtime_source_qualified_individual_cases']=102;self.reject()
    def test_no_gate_promote(self):self.body['P09_gate']='PASS';self.reject()

class Completed108ClosingTests(unittest.TestCase):
    def setUp(self):
        self.review,self.source,self.accepted,self.rp,self.sp,self.scope,self.codes=closing_fixture()
    def review_check(self):return m.closing_contract(self.review,self.scope,self.codes)
    def source_check(self):return m.closing_contract(self.source,self.scope,self.codes,self.review,self.rp)
    def accept_check(self):return m.closing_contract(self.accepted,self.scope,self.codes,self.review,self.rp,self.source,self.sp)
    def reject(self,which):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError,AttributeError)):getattr(self,which+'_check')()
    def test_review_pin_argument_independent(self):self.assertIsNot(self.source['closing_review_pin'],self.rp)
    def test_source_pin_argument_independent(self):self.assertIsNot(self.accepted['closing_source_pin'],self.sp)
    def test_review_only_current400(self):self.review_check()
    def test_source_only_full1658(self):self.source_check()
    def test_compound102_no_rerun(self):self.accept_check();self.assertEqual(self.accepted['runtime_plan']['runtime_source_qualified_individual_cases'],102)
    def test_review_missing_checkpoint(self):self.review['contract_checkpoint_statistics']['successful_after_test_checks']-=1;self.reject('review')
    def test_review_no_source_attempt(self):self.review['independent_source_frame_attempted']=True;self.reject('review')
    def test_source_no_new_test_claim(self):self.source['runtime_contract_executions']=m.EXECUTED;self.reject('source')
    def test_source_wrong_review_pin(self):self.source['closing_review_pin']['sha256']='c'*64;self.reject('source')
    def test_source_partial1657_denied(self):self.source['source_frame']['actual_byte_boundaries'][1]['reader_diagnostics']['read_passes']-=1;self.reject('source')
    def test_source_wrong_byte_pin(self):self.source['source_frame']['actual_byte_boundaries'][1]['actual_byte_pins'].pop();self.reject('source')
    def test_source_identity_required(self):self.source['source_frame']['held_identity_after_owned_cleanup']['regular_file_count']-=1;self.reject('source')
    def test_source_borrowed_remaining(self):self.source['source_frame']['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject('source')
    def test_source_CPU_guard_not_relaxed(self):self.source['early_source_checkpoint']['original_hard_CPU_RAM600_guards_preserved']=False;self.reject('source')
    def test_accept_no_product_flag(self):self.accepted['actual_product_child_executed']=True;self.reject('accept')
    def test_accept_exact102_cursor(self):self.accepted['runtime_plan']['next_runtime_index']=110;self.reject('accept')
    def test_accept_original_failed_NOT_PASS(self):self.accepted['original_failed_root_accepted']=True;self.reject('accept')
    def test_accept_no_source_pin_substitution(self):self.accepted['closing_source_pin']['bytes']+=1;self.reject('accept')
    def test_accept_source_review_same_chain(self):self.source['closing_review_pin']['sha256']='d'*64;self.reject('accept')
    def test_source_not_original_partial_promoted(self):self.source['original_partial_after_hash_completed']=True;self.reject('source')

class Completed108ModeAndPinTests(unittest.TestCase):
    def test_actual108_rerun_denied(self):
        with self.assertRaises(ValueError):m.require_no_pending_product_reexecution(108)
    def test_actual109_not_blocked_by_pending108_guard(self):m.require_no_pending_product_reexecution(109)
    def test_closing_pin_path_exact(self):
        pin=dict(path=m.p.DIR+'/p340-closing-review-run019.v1.json',bytes=1,sha256='a'*64);self.assertEqual(m.closing_pin(pin,'review'),pin)
    def test_closing_pin_wrong_kind_denied(self):
        pin=dict(path=m.p.DIR+'/p340-closing-review-run019.v1.json',bytes=1,sha256='a'*64)
        with self.assertRaises(ValueError):m.closing_pin(pin,'source')

class CurrentContractScopeTests(unittest.TestCase):
    def test_scope_uses_scanned_current_not_bootstrap(self):
        scope=FIXTURES;index,_=m.g.old.select(scope[1],scope[2]);plan=m.g.advance(scope[0],scope[1],scope[2],index)
        result=m.current_contract_scope(scope,plan);self.assertIs(result[1],plan)
        self.assertIs(result[4],scope[4]);self.assertIs(result[8],scope[8])
    def test_scope_not_rollback(self):
        scope=FIXTURES;bad=copy.deepcopy(scope[1]);bad['runtime_source_qualified_individual_cases']-=1
        with self.assertRaises(ValueError):m.current_contract_scope(scope,bad)
    def test_scope_not_omit_names(self):
        scope=FIXTURES;bad=copy.deepcopy(scope[1]);bad['runtime_qualified_test_names']=[]
        with self.assertRaises(ValueError):m.current_contract_scope(scope,bad)
    def test_scope_shape_not_changed(self):
        with self.assertRaises(ValueError):m.current_contract_scope(FIXTURES[:-1],FIXTURES[1])


class HeldPathGuardTests(unittest.TestCase):
    """작은 fake 계약만. 실제 Native/full-source PASS로 쓰지 않는다."""
    def setUp(self):
        import test_borrowed_locked_streams as b
        self.b=b;self.pin=dict(path='tools/p09/mock.py',bytes=3,sha256=m.hashlib.sha256(b'abc').hexdigest())
        self.native=b.old.FakeNative();original=self.native.open
        def opened(path,directory):
            handle=original(path,directory)
            if not directory:self.native.handles[handle]['size']=3
            return handle
        self.native.open=opened;self.api=b.API(self.native)
        self.held=b.b.BorrowedInputLocks(b.b.locks.ROOT,lambda:None,api=self.native,borrow_api=self.api)
        self.frame=m.p.frames.Frame(m.p.frames.Registry(),{self.pin['path']:self.pin},lambda:None,held=self.held)
        self.frame.acquire();self.reader=m.audit.AuditEvidenceReader(self.held.root,lambda:None);self.guard=None
    def tearDown(self):
        self.held.checkpoint=lambda:None;self.api.fail=None
        if self.held.borrower:self.held.borrower.identity=lambda:self.held.borrower.owner
        if self.guard and not self.guard.closed:self.guard.restore()
        self.frame.close()
    def attach(self):self.guard=m.HeldPathGuard(self.frame,self.reader);return self.guard
    def read(self):
        self.attach()
        try:
            with self.held.reader_sources(self.reader):return self.reader.fresh_pin(self.pin['path'])
        finally:self.guard.restore()
    def test_all_original_boolean_guards_one_fresh_query(self):
        self.assertEqual(self.read(),self.pin)
        self.assertEqual((self.guard.queries,self.guard.guards),(1,3))
    def test_original_source_function_is_unchanged(self):
        original=self.reader._source.__func__;self.read();self.assertIs(self.reader._source.__func__,original)
    def test_no_pathname_metadata_or_open(self):
        with patch.object(m.audit.Path,'is_file',side_effect=AssertionError('PATH_STAT_FORBIDDEN')),patch.object(m.audit.Path,'is_symlink',side_effect=AssertionError('PATH_STAT_FORBIDDEN')),patch.object(m.audit.Path,'is_junction',side_effect=AssertionError('PATH_STAT_FORBIDDEN')),patch.object(m.audit.Path,'open',side_effect=AssertionError('PATH_OPEN_FORBIDDEN')):
            self.assertEqual(self.read(),self.pin)
    def test_no_fresh_query_cached_across_source_requests(self):
        self.attach()
        with self.held.reader_sources(self.reader):
            self.reader.fresh_pin(self.pin['path']);self.reader.fresh_pin(self.pin['path'])
        self.assertEqual((self.guard.queries,self.guard.guards),(2,6))
        self.assertEqual(self.held.stream_identity_checks,2)
    def test_stream_identity_original_and_extra_checks_separate(self):
        before=self.held.metadata_checks;self.read()
        self.assertEqual(self.held.metadata_checks,before+1);self.assertEqual(self.guard.queries,1)
    def test_original_root_restored_on_success(self):
        original=self.reader.root;self.read();self.assertIs(self.reader.root,original);self.assertTrue(self.guard.restored)
    def test_original_root_restored_on_read_STOP(self):
        original=self.reader.root
        self.held.checkpoint=lambda:(_ for _ in ()).throw(ValueError('CPU_STOP'))
        with self.assertRaises(ValueError):self.read()
        self.assertIs(self.reader.root,original)
    def test_wrong_original_source_rejected(self):
        self.reader._source=lambda name:self.held.root/name
        with self.assertRaises(ValueError):self.attach()
    def test_wrong_reader_root_rejected(self):
        self.reader.root=self.held.root/'tools'
        with self.assertRaises(ValueError):self.attach()
    def test_unheld_scope_rejected(self):
        self.frame.inputs={**self.frame.inputs,'tools/p09/not-held.py':self.pin}
        with self.assertRaises(ValueError):self.attach()
    def test_outside_reader_binding_rejected(self):
        self.attach()
        with self.assertRaises(ValueError):self.guard.source(self.pin['path'])
        self.assertEqual(self.guard.attempted,0)
    def test_unknown_absolute_traversal_and_alias_rejected(self):
        self.attach()
        with self.held.reader_sources(self.reader):
            for name in ('../mock.py','/mock.py','C:/mock.py','tools\\p09\\mock.py','tools/p09/missing.py'):
                with self.assertRaises(ValueError):self.reader._source(name)
        self.assertEqual(self.guard.attempted,0)
    def test_wrong_thread_rejected(self):
        self.attach();original=self.frame.registry.identity;self.frame.registry.identity=lambda:(-1,-1)
        try:
            with self.assertRaises(ValueError):self.guard.source(self.pin['path'])
        finally:self.frame.registry.identity=original
    def bad_metadata(self,key,value):
        self.attach();handle=self.guard.regular[str(self.held.root/self.pin['path'])][1]
        self.native.handles[handle][key]=value
        with self.held.reader_sources(self.reader):
            with self.assertRaises(ValueError):self.reader._source(self.pin['path'])
        self.assertEqual(self.api.calls,[])
    def test_fresh_held_identity_drift_rejected(self):self.bad_metadata('identity',[99,99])
    def test_fresh_size_drift_rejected(self):self.bad_metadata('size',4)
    def test_fresh_directory_rejected(self):self.bad_metadata('directory',True)
    def test_fresh_symlink_or_junction_reparse_rejected(self):self.bad_metadata('reparse',True)
    def test_fresh_inheritable_rejected(self):self.bad_metadata('inheritable',True)
    def test_source_facade_direct_open_rejected(self):
        self.attach()
        with self.held.reader_sources(self.reader):
            source=self.guard.source(self.pin['path'])
            with self.assertRaises(ValueError):source.open('rb')
    def test_stale_predicate_outside_binding_rejected(self):
        self.attach()
        with self.held.reader_sources(self.reader):source=self.guard.source(self.pin['path'])
        with self.assertRaises(ValueError):source.is_file()
    def test_stale_predicate_after_root_restore_rejected(self):
        self.attach()
        with self.held.reader_sources(self.reader):source=self.guard.source(self.pin['path'])
        self.guard.restore()
        with self.assertRaises(ValueError):source.is_file()
    def test_stale_predicate_during_new_reader_binding_rejected(self):
        self.attach()
        with self.held.reader_sources(self.reader):source=self.guard.source(self.pin['path'])
        with self.held.reader_sources(self.reader):
            with self.assertRaises(ValueError):source.is_file()
    def test_borrowed_stream_identity_drift_still_rejected(self):
        original=self.api.duplicate
        def duplicate(source):
            handle=original(source);self.native.handles[handle]['identity']=[99,99];return handle
        self.api.duplicate=duplicate
        with self.assertRaises(ValueError):self.read()
        self.assertIsNone(self.held.borrower.loan);self.assertEqual(self.guard.queries,1)
    def test_summary_disclaims_measured_freeze_fix(self):
        self.read();row=self.guard.summary();self.assertFalse(row['kernel_call_reduction_or_CPU_freeze_improvement_claimed'])
        self.assertFalse(row['active_path_guard_adapter']);self.assertEqual(row['pathname_metadata_probes'],0)
    def test_frame_boundary_restores_root_even_after_STOP(self):
        readers=[];rows=[]
        class Reader(m.audit.AuditEvidenceReader):
            def diagnostics(self):return dict(read_passes=self.read_passes,bytes_read=self.bytes_read)
        def factory(checkpoint):
            reader=Reader(self.held.root,checkpoint);readers.append(reader);return reader
        with patch.object(self.api,'descriptor',side_effect=OSError('MOCK_READ_STOP')):
            with self.assertRaises(OSError):m.read_with_held_path_guards(self.frame,factory,lambda:None,rows)
        self.assertEqual(len(rows),1);self.assertTrue(rows[0]['original_reader_root_restored'])
        self.assertEqual(readers[0].root,self.held.root);self.assertFalse(rows[0]['active_path_guard_adapter'])
    def test_exact_two_full_fake_boundaries_and_cleanup(self):
        rows=[]
        class Reader(m.audit.AuditEvidenceReader):
            def diagnostics(self):return dict(read_passes=self.read_passes,bytes_read=self.bytes_read)
        for _ in range(2):
            m.read_with_held_path_guards(self.frame,lambda cp:Reader(self.held.root,cp),lambda:None,rows)
        self.assertEqual(len(self.frame.boundaries),2);self.assertEqual([r['fresh_held_metadata_queries'] for r in rows],[1,1])
        self.held.verify_two_byte_passes({self.pin['path']:self.pin})
        self.assertTrue(self.frame.close());self.assertEqual(self.native.handles,{})

class Source021StopReviewTests(unittest.TestCase):
    def setUp(self):
        if SOURCE021_DOCUMENT is None or REVIEW404_DOCUMENT is None:raise RuntimeError('EXACT_SOURCE021_AND404_REQUIRED')
        self.doc=copy.deepcopy(SOURCE021_DOCUMENT);self.review=copy.deepcopy(REVIEW404_DOCUMENT)
        self.scope=FIXTURES
        if FOLLOWING:self.scope=(FIXTURES[0],PENDING108_BASE,*FIXTURES[2:])
    def check(self):return m.source021_review(self.doc,self.review,self.scope)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):self.check()
    def test_literal_source_failure_preserved_not_accept(self):self.assertTrue(self.check()['independent_source_not_qualified'])
    def test_partial426_no_completed_boundary(self):self.doc['source_frame']['actual_byte_boundaries']=[{}];self.reject()
    def test_CPU_reason_cannot_be_removed(self):self.doc['resource_stop_reason']=None;self.reject()
    def test_code95_exact_v11_required(self):self.doc['current95_code_pins'][-1]['bytes']+=1;self.reject()
    def test_all_handles_must_close(self):self.doc['source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
    def test_all_duplicates_must_close(self):self.doc['source_frame']['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject()
    def test_no_product_reexecution(self):self.doc['actual_product_child_executed']=True;self.reject()
    def test_same404_literal_review(self):self.doc['closing_review_pin']['sha256']='0'*64;self.reject()
    def test_old404_guard_review_required(self):self.review['contract_checkpoint_statistics']['successful_after_test_checks']-=1;self.reject()

class HeldPathOracleTests(unittest.TestCase):
    def setUp(self):self.review,self.source,self.accepted,self.rp,self.sp,self.scope,self.codes=closing_fixture()
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):m.closing_contract(self.source,self.scope,self.codes,self.review,self.rp)
    def test_full1658_path_queries_required(self):self.source['source_path_guard_diagnostics'][1]['fresh_held_metadata_queries']-=1;self.reject()
    def test_all_three_original_logical_guards_required(self):self.source['source_path_guard_diagnostics'][0]['original_path_guard_predicates']-=1;self.reject()
    def test_adapter_root_restore_required(self):self.source['source_path_guard_diagnostics'][0]['original_reader_root_restored']=False;self.reject()
    def test_no_cache_between_queries(self):self.source['source_path_guard_diagnostics'][0]['metadata_reused_between_source_requests']=True;self.reject()
    def test_no_measured_freeze_fix_claim(self):self.source['source_path_guard_diagnostics'][0]['kernel_call_reduction_or_CPU_freeze_improvement_claimed']=True;self.reject()


class ClosingTemplateCacheTests(unittest.TestCase):
    def test_runner_builds_template_once(self):
        closing_fixture();before=CLOSING_TEMPLATE_BUILDS;closing_fixture()
        self.assertEqual(CLOSING_TEMPLATE_BUILDS,before);self.assertEqual(before,1)
    def test_all_returned_documents_independent_between_tests(self):
        first=closing_fixture();second=closing_fixture()
        first[1]['source_frame']['actual_byte_boundaries'][0]['actual_byte_pins'].pop()
        self.assertEqual(len(second[1]['source_frame']['actual_byte_boundaries'][0]['actual_byte_pins']),m.N)
    def test_expected_pins_independent_from_doc(self):
        _,source,accepted,rp,sp,_,_=closing_fixture()
        self.assertIsNot(source['closing_review_pin'],rp);self.assertIsNot(accepted['closing_source_pin'],sp)
    def test_cache_not_mutated_by_returned_metadata(self):
        first=closing_fixture();old=CLOSING_TEMPLATE[0]['scope_budget']['full_runtime_inputs']
        first[0]['scope_budget']['full_runtime_inputs']=1
        self.assertEqual(CLOSING_TEMPLATE[0]['scope_budget']['full_runtime_inputs'],old)
    def test_required_maps_remain_independent(self):
        first=closing_fixture();second=closing_fixture();first[5][4].pop(m.SELF)
        self.assertIn(m.SELF,second[5][4]);self.assertIn(m.SELF,CLOSING_TEMPLATE[5][4])

class Review022StopTests(unittest.TestCase):
    def setUp(self):
        if REVIEW022_DOCUMENT is None:raise RuntimeError('EXACT_REVIEW022_REQUIRED')
        self.doc=copy.deepcopy(REVIEW022_DOCUMENT)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):m.review022_stop(self.doc)
    def test_original_CPU_stop_not484_pass(self):self.assertTrue(m.review022_stop(self.doc)['partial14_not484_qualified'])
    def test_no_native_was_executed(self):self.doc['independent_source_frame_attempted']=True;self.reject()
    def test_only13_successful_after_test_checks(self):self.doc['contract_checkpoint_statistics']['successful_after_test_checks']=14;self.reject()
    def test_unfinished_metadata_not_fresh(self):self.doc['preparation_IO']['finished']=True;self.reject()
    def test_owner_cleanup_required(self):self.doc['resource_watcher_cleanup_confirmed']=False;self.reject()
