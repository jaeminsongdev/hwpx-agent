"""P340: current/following 합성 자료만 사용. 실제 제품/Native/수용 증거가 아니다."""
import copy,types,unittest
from unittest.mock import patch
import resume_preserved106_queue_runtime as m
import test_admission_classified_queue_runtime as oldtests
FIXTURES=None
FOLLOWING=False
TEMPLATE=None
PREQUALIFICATION=None
PREQUALIFICATION2=None

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
            prequalification_failure_reviews=[m.prequal_summary(z) for z in m.PREQUAL_SPECS],
            current95_code_pins=m.FROZEN93+[required[m.SELF],required[m.TEST]],
            runtime_contract_executions=0,contract_checkpoint_statistics=None,
            qualified_contract_checkpoint_statistics=row,reused_light_contract_executions=m.EXECUTED,
            qualified_light_pin=dict(path=m.p.DIR+'/p340-light-run001.v1.json',bytes=1,sha256='a'*64),
            independent_fresh_pin=dict(path=m.p.DIR+'/p340-light-review-run002.v1.json',bytes=1,sha256='b'*64),
            source_attempted=True,source_qualified=True)
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
    d,b,p,required,binding,extras,names,legacy,base,baseline,added=fixture()
    row=d['qualified_contract_checkpoint_statistics']
    for key in ('closing_component','case_receipt_pin','runtime_plan'):d.pop(key,None)
    d.update(state=m.LIGHT,runtime_contract_executions=m.EXECUTED,contract_checkpoint_statistics=row,
        own_queue_contract_tests_passed=m.COUNT,synthetic_following_queue_contract_tests_passed=m.COUNT,
        accepted_exact_product_body_count=0,actual_product_child_executed=False,source_attempted=False,source_qualified=False,
        original_parent_capture_adapter_selected=False,diagnostic_parent_connection_selected=False)
    return d,required,binding,extras,names,base,baseline,added

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
