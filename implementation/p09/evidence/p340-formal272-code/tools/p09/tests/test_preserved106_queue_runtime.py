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
LITERAL_PRIOR_LIGHT=None
EPOCH_DOCUMENTS=None
NATIVE107_DOCUMENTS=None
NATIVE107_BASE=None
SCOPE_FAILURE_DOCUMENT=None

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
            scope_fix_failure_review=m.scope_failure_summary(),
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
        q=types.SimpleNamespace(reader=types.SimpleNamespace(checkpoint=lambda:checks.append(True)))
        def read(name):
            calls.append(name)
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
