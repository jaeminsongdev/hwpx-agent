"""P340: 보존106 compound100에서 시작하는 고정 실행 큐.
원93 코드/제품 증거 보존. 새2 코드 포함 full1658. 통과 제품 재실행/자동 retry 없음.
원 감시기, 두 byte, Native identity, Job, pacing, cleanup은 기존 구현을 그대로 사용한다.
"""
import complete_preserved106_source as x
import audit_evidence_io as audit
import argparse,copy,hashlib,io,json,re,sys,types,unittest
from pathlib import PurePosixPath
from unittest.mock import patch
m=x.m;p=m.p;g=m.g;r=m.r
SELF='tools/p09/resume_preserved106_queue_runtime.py'
TEST='tools/p09/tests/test_preserved106_queue_runtime.py'
CLOSING_CODE=[
 dict(path=x.SELF,bytes=33090,sha256='d2c97f3723be25194c43a2142a95c58ae299b2f66919bba33b8442664b49518a'),
 dict(path=x.TEST,bytes=11920,sha256='943a4496515e6f13f2a25c87f52bc80d54dfe600ef6a783db184a09a8eb1027a')]
FROZEN93=x.CODE91+CLOSING_CODE
COMPOUND_REVIEW=dict(path=p.DIR+'/p338-review-run003.v1.json',bytes=293891,sha256='612b841e87840352adae2e1fab8819fc02556060da26912af028b372128e43f2')
COMPOUND_SOURCE=dict(path=p.DIR+'/p338-source-run004.v1.json',bytes=628772,sha256='2d19eaa5057ceac9b3dbc93e5c8f889facd5734ca720c451d0b547ec7d8688db')
COMPOUND=dict(path=p.DIR+'/p338-accept-run005.v1.json',bytes=293887,sha256='c46d5d978246006da2a1164adeafcd4d14662acf2f2cd6bd9e7f86a47853513b')
SCHEMA='hwpx-agent.p09-preserved106-fixed-runtime-queue/v13'
PASS='PASS_EXACT_PRESERVED106_NEXT_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT='PASS_PRESERVED106_NEXT_QUEUE_NOT_ACTUAL_OR_GATE'
FRESH='PASS_PRESERVED106_DISTINCT_FRESH_NOT_NATIVE_OR_PRODUCT'
STOP_REVIEW='PASS_PRESERVED106_PRE_PRODUCT_STOP_REVIEW_NOT_GO'
N=1658;DIRECTORIES=308
COUNT=252
EXECUTED=2*COUNT
FILE=re.compile(r'p340-case-([0-9]{3})-run([0-9]{3})\.v1\.json')
STARTUP_LIMITS=m.STARTUP_LIMITS
LAST_TERMINAL=None

def require(ok,code):m.require(ok,'PRESERVED106_QUEUE_'+code)

PREQUAL_FAILURE=dict(path=p.DIR+'/p340-light-run001.v1.json',bytes=132457,sha256='98514e8cf9b405089da66f76a36fc887a69906d20b2bf89c59047bba2aa85b94')
PREQUAL_CODE=[
 dict(path=SELF,bytes=30583,sha256='1ab74777e0a65aee2d175ece582794a3be2a329153df64c08eb8255b2f5c7249'),
 dict(path=TEST,bytes=15621,sha256='b3f25091c526915e3a18b013ca05b93d7c5e111cd3cdefe9b6939178c11f0658')]
PREQUAL2_FAILURE=dict(path=p.DIR+'/p340-light-run002.v1.json',bytes=132469,sha256='45f69f90dd7b3a38a2297b486376a3a85c335415d69bd13a6e713d3a9db75dbe')
PREQUAL2_CODE=[
 dict(path=SELF,bytes=34341,sha256='85b500833ff4cad7efa5b21fca21320cea9c14a2c36e65c912030797f6c7330d'),
 dict(path=TEST,bytes=16988,sha256='2a2e98db27d71c3b1b6743eb78d2a9c19e070283483bff0a4acc14c1f5ca6a33')]
PREQUAL_SPECS=[
 dict(pin=PREQUAL_FAILURE,codes=PREQUAL_CODE,archive='p340-preformal140-code',version=1,tests=70,failures=4,bound=147,
      cause='MISSING_OPTIONAL_ERROR_FIELD'),
 dict(pin=PREQUAL2_FAILURE,codes=PREQUAL2_CODE,archive='p340-preformal156-code',version=2,tests=78,failures=2,bound=150,
      cause='SYNTHETIC_PASS_STATE_NOT_REBOUND')]

def prequal_summary(spec=None):
    spec=PREQUAL_SPECS[0] if spec is None else spec
    return dict(original_failure_pin=spec['pin'],original_FAILED_preserved=True,
        actual_contracts_started_and_stopped=spec['tests'],partial_runner_calls=1,
        contract_qualification_pass=False,actual_Native_or_product_executed=False,
        cleanup_confirmed=True,found_cause=spec['cause'],guard_or_product_acceptance_changed=False)

def prequal_review(doc,spec=None):
    spec=PREQUAL_SPECS[0] if spec is None else spec
    require(spec in PREQUAL_SPECS and doc['schema_version']==f'hwpx-agent.p09-preserved106-fixed-runtime-queue/v{spec["version"]}'
        and doc['state']=='FAILED_NOT_ACCEPTED'
        and doc['error_code']=='P208_POST_STOP_RUNTIME_DIAGNOSTIC_RUNTIME_REVIEWED_STOP_QUEUE_RUNTIME_PRESERVED106_QUEUE_ALL_CURRENT_AND_FOLLOWING_CONTRACTS'
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['failure_diagnostic']['stage']=='contract_tests'
        and doc['current95_code_pins']==FROZEN93+spec['codes'] and doc['original93_pins']==FROZEN93
        and doc['startup_limits']==STARTUP_LIMITS and doc['compound100_pin']==COMPOUND
        and doc['prior_runtime_plan']['runtime_source_qualified_individual_cases']==100
        and doc['selected_test_index']==107 and doc['runtime_contract_executions']==0
        and doc['accepted_exact_product_body_count']==0 and doc['source_attempted'] is False
        and doc['actual_product_child_executed'] is False and doc['source_qualified'] is False
        and doc['original_parent_capture_adapter_selected'] is False and doc['diagnostic_parent_connection_selected'] is False
        and doc.get('terminal_source_frame') is None and doc.get('case_receipt_pin') is None
        and doc.get('terminal_parent_failure_sidecar_pin') is None and 'runtime_plan' not in doc,
        'IMMUTABLE_PREFORMAL_FAILURE_NEVER_ACCEPTED_OR_PRODUCT')
    row=doc['contract_checkpoint_statistics'];io_=doc['preparation_IO'];count=spec['tests']
    require(row['started_tests']==row['stopped_tests']==row['successful_before_test_checks']==row['successful_after_test_checks']==count
        and row['runner_calls']==row['returned_runner_calls']==row['successful_before_runner_checks']==row['successful_after_runner_checks']==1
        and row['original_unittest_results_preserved'] is True and row['original_guard_or_test_coverage_relaxed'] is False
        and row['new_sampler_or_thread_or_sleep_started'] is False
        and len(doc['contract_failures'])==spec['failures'] and io_['bound_inputs']==io_['read_passes']==spec['bound']
        and io_['final_fresh_hashes']==0 and io_['finished'] is False,'PARTIAL_CURRENT_RUNNER_NOT_FULL_PASS')
    return prequal_summary(spec)

PRIOR_LIGHT=dict(path=p.DIR+'/p340-light-run003.v1.json',bytes=49266,sha256='645e7cafa3c4c3ea495aa26a03b5514b402308963ef3526163defdcdbf99131d')
PRIOR_LIGHT_CODE=[
 dict(path=SELF,bytes=35532,sha256='7e9228c891a08689f4debc82cc74781fdd268f26e2aec58a979e6e5a7100eaef'),
 dict(path=TEST,bytes=18326,sha256='1a9afc7da79c04c637588dc6b9cda5d9b511305920943fc89028e39059f074b0')]

def prior_light_review(doc,plan,names,required,binding,extras,baseline,added):
    prior_required={**required,**{z['path']:z for z in PRIOR_LIGHT_CODE}}
    prior_added={**added,**{z['path']:z for z in PRIOR_LIGHT_CODE}}
    prior_extras={**extras,**{z['path']:z for z in PRIOR_LIGHT_CODE}}
    index,name=g.old.select(plan,names)
    require(doc['schema_version']=='hwpx-agent.p09-preserved106-fixed-runtime-queue/v3' and doc['state']==LIGHT
        and doc.get('error_code') is None and doc['resource_stop_reason'] is None
        and doc['resource_watcher_cleanup_confirmed'] is True and doc['prior_runtime_plan']==plan
        and doc['selected_test_index']==index==107 and doc['selected_test_name']==name
        and doc['current95_code_pins']==FROZEN93+PRIOR_LIGHT_CODE and doc['original93_pins']==FROZEN93
        and doc['scope_budget']==budget(prior_required,baseline,prior_added) and doc['scope_added_ten_pins']==list(prior_added.values())
        and doc['extra_frame_controller_pins']==list(prior_extras.values()) and doc['binding']==binding
        and doc['compound100_pin']==COMPOUND and doc['compound100_review_pin']==COMPOUND_REVIEW
        and doc['compound100_source_pin']==COMPOUND_SOURCE and doc['startup_limits']==STARTUP_LIMITS
        and doc['stop_resume_policy']==m.STOP_POLICY and doc['original_successful_bodies_not_reexecuted'] is True
        and doc['prequalification_failure_reviews']==[prequal_summary(z) for z in PREQUAL_SPECS],
        'ARCHIVE_BOUND172_PREVIOUS_CODE_NOT_CURRENT_GO')
    require(doc['runtime_contract_executions']==172 and doc['own_queue_contract_tests_passed']==doc['synthetic_following_queue_contract_tests_passed']==86
        and doc['source_attempted'] is False and doc['source_qualified'] is False and doc['actual_product_child_executed'] is False
        and doc['original_parent_capture_adapter_selected'] is False and doc['diagnostic_parent_connection_selected'] is False
        and doc['accepted_exact_product_body_count']==0 and doc.get('case_receipt_pin') is None
        and doc.get('closing_component') is None and doc['preparation_IO']['finished'] is True
        and doc['preparation_IO']['bound_inputs']==doc['preparation_IO']['final_fresh_hashes']==153
        and doc['preparation_IO']['read_passes']==306,'PREVIOUS172_METADATA_ONLY')
    m.guarded_contract(doc['contract_checkpoint_statistics'],172);m.leading_contract(doc['preparation_IO'])
    require(doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN' and all(doc[k] is False for k in (
        'whole1470_current_fresh_qualified','full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved')),
        'PREVIOUS172_NOT_GATE')
    return dict(pin=PRIOR_LIGHT,archive_bound_contract_executions=172,previous_code_only=True,current_actual_GO=False,
        actual_Native_or_product_executed=False,cleanup_confirmed=True)

def existing_body_contract(paths,known):
    require(type(paths) is list and len(paths)<=999 and len(set(paths))==len(paths),'BOUNDED_DISTINCT_BODY_INVENTORY')
    for name in paths:
        require(name in known and known[name]['path']==name and known[name]['bytes']==0
            and known[name]['sha256']==hashlib.sha256(b'').hexdigest(),'UNKNOWN_OR_NONEMPTY_BODY_BLOCKS_PRODUCT_REPLAY')

def existing_body_guard(q,index):
    paths=[z.relative_to(p.c.ROOT).as_posix() for z in (p.c.ROOT/p.DIR/'cases').glob(f'p340-case-{index:03}-run*.json')]
    existing_body_contract(paths,q.reviewed_zero_pins)
    for name in paths:require(q.pin(name)==q.reviewed_zero_pins[name],'REVIEWED_ZERO_STILL_EXACT')

def placeholder(q,rp,doc):
    name=doc.get('case_receipt_path')
    if name is None:return None
    match=FILE.fullmatch(PurePosixPath(rp['path']).name);require(match is not None,'BODY_ONLY_EXACT_CASE_FAILURE')
    index,number=map(int,match.groups())
    require(name==f'{p.DIR}/cases/p340-case-{index:03}-run{number:03}.json','FAILURE_BODY_PATH_MATCHES_ROOT')
    if not (p.c.ROOT/name).exists():return None
    pin=q.pin(name)
    require(pin['bytes']==0 and pin['sha256']==hashlib.sha256(b'').hexdigest(),'PRE_PRODUCT_BODY_ZERO_NOT_PASSED_PRODUCT')
    return pin

EPOCH_LIGHT=dict(path=p.DIR+'/p340-light-run004.v1.json',bytes=49322,sha256='8feb8f2758040f0028eb9f13a8466e13d8a95b012a210f102d3a133f78fc0ac6')
EPOCH_FRESH=dict(path=p.DIR+'/p340-light-review-run005.v1.json',bytes=47106,sha256='67994e90aa3ce8f9063dce096ac6647058e331c745278f9dca6041f03c10661f')
EPOCH_FAILURE=dict(path=p.DIR+'/p340-case-107-run006.v1.json',bytes=148100,sha256='d1bfffe5861c46f7eb7fdbbc92c4910aaa95c9d2e776dc1d22abbab749f1d2aa')
EPOCH_CODE=[
 dict(path=SELF,bytes=41166,sha256='1515339e63000f73ba6c304d5ce186246a59b41f231cb0d00b4161687a6f1f58'),
 dict(path=TEST,bytes=21036,sha256='1e493272502108659021df1a153c5929730c6bebafd605b944995d4951af904c')]

def reserved_post_reads(q):
    limit=m.m.m.META_READ_LIMIT
    count=q.shared_budget['read_calls']
    require(limit==720 and type(count) is int and 0<=count<=limit-2,'ORIGINAL720_POST_TWO_READS_RESERVED')
    return True

def epoch_review(light,fresh,failed,plan,names,required,binding,extras,baseline,added):
    older={z['path']:z for z in EPOCH_CODE}
    old_required={**required,**older};old_extras={**extras,**older};old_added={**added,**older};codes=FROZEN93+EPOCH_CODE
    old_common=rebound(common,SCHEMA='hwpx-agent.p09-preserved106-fixed-runtime-queue/v4')
    old_light=rebound(light_contract,common=old_common,COUNT=99,EXECUTED=198)
    old_fresh=rebound(fresh_contract,common=old_common,light_contract=old_light,EXECUTED=198)
    old_light(light,plan,names,old_required,binding,old_extras,baseline,old_added,codes)
    old_fresh(fresh,light,EPOCH_LIGHT,plan,names,old_required,binding,old_extras,baseline,old_added,codes)
    require(failed['schema_version']=='hwpx-agent.p09-preserved106-fixed-runtime-queue/v4' and failed['state']=='FAILED_NOT_ACCEPTED'
        and failed['error_code']=='P152_FULL_REDACTED_FAILURE' and failed['resource_stop_reason'] is None
        and failed['resource_watcher_cleanup_confirmed'] is True and failed['current95_code_pins']==codes
        and failed['prior_runtime_plan']==plan and failed['selected_test_index']==107
        and failed['qualified_light_pin']==EPOCH_LIGHT and failed['independent_fresh_pin']==EPOCH_FRESH
        and failed['runtime_contract_executions']==0 and failed['reused_light_contract_executions']==198
        and failed['accepted_exact_product_body_count']==0 and failed['actual_product_child_executed'] is False
        and failed['source_attempted'] is False and failed['source_qualified'] is False
        and failed['original_parent_capture_adapter_selected'] is False and failed['diagnostic_parent_connection_selected'] is False
        and failed.get('terminal_source_frame') is None and failed.get('terminal_parent_failure_sidecar_pin') is None
        and failed.get('case_receipt_path') is None and failed.get('case_receipt_pin') is None and 'runtime_plan' not in failed,
        'EXACT_PRE_NATIVE_ATTRIBUTE_FAILURE_NOT_PRODUCT_REPLAY')
    d=failed['failure_diagnostic'];io_=failed['preparation_IO']
    require(d['stage']=='final_fresh_preparation' and d['exception_class']=='AttributeError'
        and d['locations']==[dict(file='resume_preserved106_queue_runtime.py',line=459)]
        and d['exception_message_included'] is False and d['diagnostic_not_acceptance'] is True
        and io_['finished'] is True and io_['bound_inputs']==io_['final_fresh_hashes']==158
        and io_['read_passes']==317 and failed['existing_body_replay_guard_verified'] is True
        and failed['qualified_contract_checkpoint_statistics']==light['contract_checkpoint_statistics'],
        'ORIGINAL_PHASE_LINE_COMPLETE_FRESH_AND_NO_NATIVE')
    return dict(failure_pin=EPOCH_FAILURE,light_pin=EPOCH_LIGHT,fresh_pin=EPOCH_FRESH,
        original_FAILED_preserved=True,original198_contracts_previous_code_only=True,
        current_actual_GO=False,Native_or_product_started=False,cleanup_confirmed=True,
        fixed_cause='META_READ_LIMIT_MODULE_REFERENCE',source_scope_reduced=False)

NATIVE107_ROOT=dict(path=p.DIR+'/p340-case-107-run009.v1.json',bytes=677180,sha256='7e88493af85906c48e69cc620daa432adad87a785109c35d458b77bd8f65b7fb')
NATIVE107_BODY=dict(path=p.DIR+'/cases/p340-case-107-run009.json',bytes=191699,sha256='c74a592e305a882f5aadda54a10ced7f98a8369cd3b83ec412084bd6b0782e6d')
NATIVE107_LIGHT=dict(path=p.DIR+'/p340-light-run007.v1.json',bytes=50410,sha256='327a54c5655da57ae3a751157f2ea9cbe4d5fcefdffb374c3a9a8d0adb29aace')
NATIVE107_FRESH=dict(path=p.DIR+'/p340-light-review-run008.v1.json',bytes=47746,sha256='a695fb73b386837c8138d2c8c1dcb90662ccf00d808ef27548ab5b954c79be71')
NATIVE107_CODE=[
 dict(path=SELF,bytes=46937,sha256='3422b3b404e8efa5ae54813a2b22a633097b01a6c554fdf87c32d93365706b5a'),
 dict(path=TEST,bytes=24869,sha256='21154ffd3e7d98637af869be395e2fb117aa8fe69d166d57064b31e407b66408')]

def native107_epoch(root,body,light,fresh,legacy,base,names,required,binding,extras,baseline,added):
    old={z['path']:z for z in NATIVE107_CODE}
    old_required={**required,**old};old_extras={**extras,**old};old_added={**added,**old};codes=FROZEN93+NATIVE107_CODE
    old_common=rebound(common,SCHEMA='hwpx-agent.p09-preserved106-fixed-runtime-queue/v5')
    old_light=rebound(light_contract,common=old_common,COUNT=116,EXECUTED=232)
    old_fresh=rebound(fresh_contract,common=old_common,light_contract=old_light,EXECUTED=232)
    old_record=rebound(record,common=old_common,EXECUTED=232)
    old_light(light,base,names,old_required,binding,old_extras,baseline,old_added,codes)
    old_fresh(fresh,light,NATIVE107_LIGHT,base,names,old_required,binding,old_extras,baseline,old_added,codes)
    require(root['qualified_light_pin']==NATIVE107_LIGHT and root['independent_fresh_pin']==NATIVE107_FRESH
        and root['case_receipt_pin']==NATIVE107_BODY
        and root['qualified_contract_checkpoint_statistics']==light['contract_checkpoint_statistics'],
        'NATIVE107_LITERAL_CHAIN_NOT_NEW_EXECUTION')
    result=old_record(root,body,NATIVE107_BODY,legacy,base,names,old_required,binding,old_extras,baseline,old_added,codes)
    require(result['runtime_source_qualified_individual_cases']==101 and result['next_runtime_index']==108
        and result['runtime_remaining_individual_cases']==148,'EXACT_NATIVE101_NEXT108')
    return result

def current_contract_scope(scope,plan):
    require(type(scope) is tuple and len(scope)==10 and type(plan) is dict,'EXACT_CONTRACT_SCOPE_SHAPE')
    base=scope[1];names=scope[2];g.old.select(plan,names)
    require(plan['runtime_source_qualified_individual_cases']>=base['runtime_source_qualified_individual_cases']
        and set(base['runtime_qualified_test_names'])<=set(plan['runtime_qualified_test_names']),
        'SCANNED_CURRENT_PLAN_NOT_STALE_OR_ROLLBACK')
    return (scope[0],plan,*scope[2:])

def ancestor_directories(required):
    # 각 파일은 검사하되 이미 등록한 부모의 조상은 재생성/재순회하지 않는다.
    directories={PurePosixPath('.')}
    for name in required:
        current=PurePosixPath(name).parent
        while current not in directories:
            directories.add(current);current=current.parent
    return directories

def budget(required,baseline,added):
    require(len(required)==N and len(baseline)==1644 and len(added)==14
        and not set(baseline)&set(added) and required=={**baseline,**added}
        and baseline[p.m.EXE['path']]==p.m.EXE and sum(z['bytes'] for z in baseline.values())==120516712
        and sum(z['bytes'] for z in added.values())<=1048576,'ALL1644_PLUS14_NOT_SUBSET')
    directories=ancestor_directories(required)
    require(len(directories)==DIRECTORIES,'ALL308_ANCESTORS')
    binary=p.m.EXE['bytes'];other=sum(z['bytes'] for z in required.values())-binary
    seconds=(N+DIRECTORIES)/14+2*N/20+2*binary/1048576+2*other/2097152+60+20+15+60
    require(seconds<600,'ORIGINAL600_FITS_NOT_PROOF')
    return dict(full_runtime_inputs=N,baseline_full_source_inputs=1644,new_inputs=14,
        actual_ancestor_directory_count=DIRECTORIES,native_rate=20,acquisition_native_rate=14,metadata_rate=32,
        original_IO_scope_seconds=600,shared_metadata_read_limit=720,extra_new_bytes_upper_bound=1048576,
        metadata_allowance_seconds=60,product_allowance_seconds=20,early_yield_allowance_seconds=15,
        margin_seconds=60,nominal_combined_seconds=seconds,prediction_not_completion_guarantee=True)

def rebound(function,**expected):
    # 보호 함수/자원 owner를 바꾸지 않고 pure validator의 scope/namespace 기대값만 별도 globals로 준다.
    globals_=dict(function.__globals__,**expected)
    result=types.FunctionType(function.__code__,globals_,function.__name__,function.__defaults__,function.__closure__)
    result.__kwdefaults__=copy.copy(function.__kwdefaults__)
    return result

def native_pair(component,body,pin,required,binding,extras):
    return rebound(m.native_pair,N=N,DIRECTORIES=DIRECTORIES)(component,body,pin,required,binding,extras)

def stopped(doc,plan,required,binding,extras,baseline,added,names,sidecar=None):
    require(doc.get('source_attempted') is False or doc.get('terminal_source_frame') is not None,'ATTEMPT_NEEDS_FRAME')
    return rebound(m.stopped_before_product,N=N,DIRECTORIES=DIRECTORIES,budget=budget)(
        doc,plan,required,binding,extras,baseline,added,names,sidecar,expected_schema=SCHEMA)

def compound(doc,reviewed,source,legacy,base,names,required,checked,codes):
    x.review_receipt(reviewed,required,checked,codes);x.source_receipt(source,required,checked,codes);x.prepared(doc,required)
    require(doc['state']==x.ACCEPT_PASS and doc['review']==checked and doc['current93_code_pins']==codes
        and doc['review_pin']==source['review_pin']==COMPOUND_REVIEW and doc['separate_source_frame_pin']==COMPOUND_SOURCE
        and doc['prior_runtime_plan']==base and doc['runtime_plan']==x.advance(legacy,base,names)
        and doc['accepted_exact_compound_case_count']==doc['semantic_body_capture_pass_count']==1
        and doc['original_failed_root_accepted'] is False and doc['original_partial_after_hash_completed'] is False
        and doc['additional_source_frame_executed'] is False and doc['actual_source_frame_executed'] is False
        and doc['actual_product_child_executed'] is False,'EXACT_CLOSED100_NO_PRODUCT_REPLAY')
    return doc['runtime_plan']

SCOPE_FAILURE=dict(path=p.DIR+'/p340-light-run010.v1.json',bytes=155508,sha256='4feb599ee48ff2fa75df20c9e76c687aec5ad67d6e49b64c20ecc74ed4e59365')
SCOPE_FAILURE_CODE=[
 dict(path=SELF,bytes=50953,sha256='7025b4e9aa9c987b6ecf922053d16991279257932ac7dd98631502c44f00245e'),
 dict(path=TEST,bytes=27688,sha256='723d9710736cd57d623fd21049c670508004e0b8751a65b69c5d29bcc3bdbcee')]

def scope_failure_summary():
    return dict(pin=SCOPE_FAILURE,original_failed_preserved=True,current_contracts128_partial_one_runner=True,
        qualification256_not_passed=True,Native_or_product_started=False,cleanup_confirmed=True,
        body_actual_child_false_must_be_rejected=True)

def scope_failure_review(doc):
    require(doc['schema_version']=='hwpx-agent.p09-preserved106-fixed-runtime-queue/v6'
        and doc['state']=='FAILED_NOT_ACCEPTED'
        and doc['error_code']=='P208_POST_STOP_RUNTIME_DIAGNOSTIC_RUNTIME_REVIEWED_STOP_QUEUE_RUNTIME_PRESERVED106_QUEUE_ALL_CURRENT_AND_FOLLOWING_CONTRACTS'
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['failure_diagnostic']['stage']=='contract_tests'
        and doc['current95_code_pins']==FROZEN93+SCOPE_FAILURE_CODE and doc['original93_pins']==FROZEN93
        and doc['native107_epoch_root_pin']==NATIVE107_ROOT and doc['startup_limits']==STARTUP_LIMITS
        and doc['compound100_pin']==COMPOUND and doc['prior_runtime_plan']['runtime_source_qualified_individual_cases']==101
        and doc['selected_test_index']==108 and doc['runtime_contract_executions']==0
        and doc['accepted_exact_product_body_count']==0 and doc['source_attempted'] is False
        and doc['source_qualified'] is False and doc['actual_product_child_executed'] is False
        and doc['original_parent_capture_adapter_selected'] is False and doc['diagnostic_parent_connection_selected'] is False
        and doc.get('terminal_source_frame') is None and doc.get('case_receipt_pin') is None
        and doc.get('terminal_parent_failure_sidecar_pin') is None and 'runtime_plan' not in doc,
        'EXACT_SCOPE_FAILURE_NOT_PRODUCT_OR_ACCEPTANCE')
    row=doc['contract_checkpoint_statistics'];io_=doc['preparation_IO']
    require(row['started_tests']==row['stopped_tests']==row['successful_before_test_checks']==row['successful_after_test_checks']==128
        and row['runner_calls']==row['returned_runner_calls']==row['successful_before_runner_checks']==row['successful_after_runner_checks']==1
        and row['original_unittest_results_preserved'] is True and row['original_guard_or_test_coverage_relaxed'] is False
        and row['new_sampler_or_thread_or_sleep_started'] is False
        and doc['contract_failures']==['test_native107_child_required (test_preserved106_queue_runtime.Native107EpochTests.test_native107_child_required)']
        and io_['bound_inputs']==io_['read_passes']==167 and io_['final_fresh_hashes']==0 and io_['finished'] is False,
        'ORIGINAL128_FAILURE_NOT256_PASS')
    return scope_failure_summary()

EPOCH272_CODE=[
 dict(path=SELF,bytes=54919,sha256='78fb64845c7f4b00afa81ed0f5c4dbb0a1a321a37d5f857da7b001d8f651f08f'),
 dict(path=TEST,bytes=29158,sha256='f51d1933e043c81bb1526992663d688a98bb74181f1fd41a232231680bc9571e')]
EPOCH272_PINS=[
 dict(path=p.DIR+'/p340-light-run011.v1.json',bytes=53534,sha256='fbb1c05ba0b1147afb82e11cbff39b8828de37d51f7af1d61a3b43fe46d8dbe0'),
 dict(path=p.DIR+'/p340-light-review-run012.v1.json',bytes=50674,sha256='596e12216ca8bb93c5746e6592b9cce0a1d6b5f513691c36ff2ad40dd0bc5537'),
 dict(path=p.DIR+'/p340-case-108-run013.v1.json',bytes=185528,sha256='0c0040175691708de217afa660bc3a779e0bee86f6f826aaee22514857d6df6c'),
 dict(path=p.DIR+'/p340-stop-review-run014.v1.json',bytes=58697,sha256='c6085b6033fc781929e766562ba7f59b97eec871176e264c6dd4284652971365')]

def epoch272_summary():
    return dict(pins=EPOCH272_PINS,original272_previous_code_only=True,current_actual_GO=False,
        original_failed_roots_preserved=True,partial_Native163_all_closed=True,
        product_started=False,accepted_delta=0,actual_product_reexecution_authorized=False)

def epoch272_review(light,fresh,native_stop,metadata_stop,plan,names,required,binding,extras,baseline,added):
    old={z['path']:z for z in EPOCH272_CODE};req={**required,**old};ext={**extras,**old};add={**added,**old}
    codes=FROZEN93+EPOCH272_CODE;schema='hwpx-agent.p09-preserved106-fixed-runtime-queue/v7'
    old_common=rebound(common,SCHEMA=schema)
    old_light=rebound(light_contract,common=old_common,COUNT=136,EXECUTED=272)
    old_fresh=rebound(fresh_contract,common=old_common,light_contract=old_light,EXECUTED=272)
    old_light(light,plan,names,req,binding,ext,baseline,add,codes)
    old_fresh(fresh,light,EPOCH272_PINS[0],plan,names,req,binding,ext,baseline,add,codes)
    old_stop=rebound(m.stopped_before_product,N=N,DIRECTORIES=DIRECTORIES,budget=budget)
    for doc,stage,bound,finished in ((native_stop,'source_frame_acquire',172,True),(metadata_stop,'anchor',116,False)):
        classified=old_stop(doc,plan,req,binding,ext,baseline,add,names,expected_schema=schema)
        io_=doc['preparation_IO'];observation=doc['metadata_observation']
        require(classified['actual_product_reexecution_authorized'] is False
            and doc['failure_diagnostic']['stage']==stage and doc['startup_limits']==STARTUP_LIMITS
            and io_['bound_inputs']==bound and io_['final_fresh_hashes']==(bound if finished else 0)
            and io_['read_passes']==(2*bound if finished else bound) and io_['finished'] is finished
            and observation['foreign_PID_query_executed'] is False and observation['new_sampler_thread_started'] is False,
            'EXACT_PRE_PRODUCT_EPOCH272_CPU_STOP_NO_GO')
    require(native_stop['current95_code_pins']==codes and native_stop['source_attempted'] is True
        and native_stop['qualified_light_pin']==EPOCH272_PINS[0] and native_stop['independent_fresh_pin']==EPOCH272_PINS[1]
        and native_stop['terminal_source_frame']['handles']['input_lock_handles_opened']==163
        and metadata_stop['source_attempted'] is False and metadata_stop.get('terminal_source_frame') is None
        and metadata_stop.get('selected_test_index') is None and 'runtime_plan' not in metadata_stop,
        'EXACT_NATIVE163_AND_ANCHOR_NO_FRAME_NO_ADVANCE')
    return epoch272_summary()

PARTIAL308_PIN=dict(path=p.DIR+'/p340-light-run015.v1.json',bytes=139871,sha256='c016966616aa1e3ba0f5da5aa954ae833c7589c9a6f9426022d62bfa7f3c4c45')
PARTIAL308_CODE=[
 dict(path=SELF,bytes=60077,sha256='8f34c5b858101840b6f292dce3a0e9fe6664935bd1b5a8b9b0f0dde7891affe3'),
 dict(path=TEST,bytes=33635,sha256='8cd044b3ab1c27291ecad1c9c956941b53e6070c66b0cf3a8e38552bfbecac8b')]

def partial308_summary():
    return dict(pin=PARTIAL308_PIN,original_failed_preserved=True,qualification308_not_passed=True,
        only12_started12_stopped11_after_checks=True,Native_or_product_started=False,current_actual_GO=False)

def partial308_review(doc,plan,names,required,binding,extras,baseline,added):
    old={z['path']:z for z in PARTIAL308_CODE};req={**required,**old};ext={**extras,**old};add={**added,**old}
    stopped_check=rebound(m.stopped_before_product,N=N,DIRECTORIES=DIRECTORIES,budget=budget)
    stopped_check(doc,plan,req,binding,ext,baseline,add,names,expected_schema='hwpx-agent.p09-preserved106-fixed-runtime-queue/v8')
    row=doc['contract_checkpoint_statistics'];io_=doc['preparation_IO']
    require(doc['failure_diagnostic']['stage']=='contract_tests' and doc['current95_code_pins']==FROZEN93+PARTIAL308_CODE
        and doc['source_attempted'] is False and doc['source_qualified'] is False
        and doc.get('terminal_source_frame') is None and doc.get('case_receipt_pin') is None
        and doc['runtime_contract_executions']==0 and doc['epoch272_stop_review']==epoch272_summary()
        and row['started_tests']==row['stopped_tests']==row['successful_before_test_checks']==12
        and row['successful_after_test_checks']==11 and row['runner_calls']==row['successful_before_runner_checks']==1
        and row['returned_runner_calls']==row['successful_after_runner_checks']==0
        and row['original_unittest_results_preserved'] is True and row['original_guard_or_test_coverage_relaxed'] is False
        and row['new_sampler_or_thread_or_sleep_started'] is False
        and io_['bound_inputs']==io_['read_passes']==176 and io_['final_fresh_hashes']==0 and io_['finished'] is False,
        'EXACT_PARTIAL12_CPU_STOP_NOT308_PASS')
    return partial308_summary()

C_REVIEW='PASS_PRESERVED108_SOURCE_REVIEW_NOT_NATIVE_OR_PRODUCT'
C_SOURCE='PASS_PRESERVED108_INDEPENDENT_WHOLE_SOURCE_NOT_PRODUCT_RERUN'
C_ACCEPT='PASS_PRESERVED108_COMPOUND102_NOT_WHOLE_OR_GATE'
C_STATES=(C_REVIEW,C_SOURCE,C_ACCEPT)
P108_NAME='actual_import::no_form_stored_source_preserves_real_body_without_policy_attestation'
P108_ROOT=dict(path=p.DIR+'/p340-case-108-run018.v1.json',bytes=988355,sha256='1a9896bd97da63066101075aa65f2d0a0fdf42bdf5405755faaa2a57849f186d')
P108_BODY=dict(path=p.DIR+'/cases/p340-failure-108-run018.json',bytes=557079,sha256='eaa7265c260f5e2ab39813016f317ab4a5d6507c94b2bba473e484a8cb4397f8')
P108_ZERO=dict(path=p.DIR+'/cases/p340-case-108-run018.json',bytes=0,sha256=hashlib.sha256(b'').hexdigest())
P108_LIGHT=dict(path=p.DIR+'/p340-light-run016.v1.json',bytes=53610,sha256='405f431597d4137acb0a9e5f0cabce7b44fd760a709efce20155c0724353b0da')
P108_FRESH=dict(path=p.DIR+'/p340-light-review-run017.v1.json',bytes=51774,sha256='be2680ef2bb5256ef671dc187386b2f6df377662388260fd2e07ddc32bb63c25')
P108_CODE=[
 dict(path=SELF,bytes=63174,sha256='df27dcd564610c1488afa63877e72280e5558e73b978449fecbba996f8f2af3d'),
 dict(path=TEST,bytes=35821,sha256='caa6165d523f9b3b465a7a6d7fa8cec1d9e235f6cea0baca8ec6ec78ff9cc34b')]

def pending108_summary():
    return dict(original_root_pin=P108_ROOT,original_parent_pin=P108_BODY,original_zero_pin=P108_ZERO,
        original_executed_code95_pins=FROZEN93+P108_CODE,semantic_body_capture_complete=True,
        original_failed_root_preserved=True,original_stopped_parent_preserved=True,original_partial_after_completed=False,
        original_zero_placeholder_preserved=True,source_closing_candidate_count=1,accepted_delta=0,
        successful_product_reexecution_allowed=False,original_Job_cleanup_confirmed=True,
        independent_current_source_closing_required=True)

def pending108_review(root,body,light,fresh,plan,names,required,binding,extras,baseline,added):
    old={z['path']:z for z in P108_CODE};req={**required,**old};ext={**extras,**old};add={**added,**old}
    codes=FROZEN93+P108_CODE;schema='hwpx-agent.p09-preserved106-fixed-runtime-queue/v9'
    old_common=rebound(common,SCHEMA=schema)
    old_light=rebound(light_contract,common=old_common,COUNT=160,EXECUTED=320)
    old_fresh=rebound(fresh_contract,common=old_common,light_contract=old_light,EXECUTED=320)
    old_light(light,plan,names,req,binding,ext,baseline,add,codes)
    old_fresh(fresh,light,P108_LIGHT,plan,names,req,binding,ext,baseline,add,codes)
    require(root['schema_version']==schema and root['state']=='FAILED_NOT_ACCEPTED'
        and root['error_code']==root['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and root['resource_watcher_cleanup_confirmed'] is True and root['failure_diagnostic']['stage']=='owned_parent'
        and root['selected_test_index']==108 and root['selected_test_name']==P108_NAME==names[107]
        and root['prior_runtime_plan']==plan and plan['runtime_source_qualified_individual_cases']==101
        and plan['next_runtime_index']==108 and P108_NAME not in plan['runtime_qualified_test_names']
        and root['current95_code_pins']==codes and root['binding']==binding
        and root['qualified_light_pin']==P108_LIGHT and root['independent_fresh_pin']==P108_FRESH
        and root['runtime_contract_executions']==0 and root['reused_light_contract_executions']==320
        and root['qualified_contract_checkpoint_statistics']==light['contract_checkpoint_statistics']
        and root['accepted_exact_product_body_count']==0 and root.get('case_receipt_pin') is None
        and root.get('closing_component') is None and 'runtime_plan' not in root
        and root['terminal_parent_failure_sidecar_pin']==P108_BODY and root['case_receipt_path']==P108_ZERO['path']
        and root['original_failure_body_placeholder_preserved'] is True and root.get('terminal_failure_write_error') is None,
        'ORIGINAL108_FAILED_NOT_RETRY_OR_ACCEPTANCE')
    require(body['state']=='STOPPED_NOT_ACCEPTED' and body['operation_phase']=='final_source_freeze'
        and body['stop_reason']==body['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and body['policy']==p.c.POLICY and body['maximum_seconds']==1200
        and body['actual_product_child_executed'] is True and type(body['exit_code']) is int and body['exit_code']==0
        and body['selected_test_names']==body['passed_test_names']==[P108_NAME]
        and body['terminal_summary']==dict(passed=1,failed=0,ignored=0,measured=0,filtered_out=248)
        and body['test_arguments']==p.v.arguments(P108_NAME) and body['binding']==binding
        and body['task']==body['minimal_worker_task']=='p204-r07-case-108-tests'
        and body['minimal_owned_worker_path']==p.m.SELF
        and body['capture']==dict(error_code=None,per_stream_limit_bytes=32768,complete_streams=True,raw_logs_saved=False)
        and all(body[k] is True for k in ('worker_created','job_assigned','writer_authorized','owned_limits_verified',
            'actual_job_membership_checked','cleanup_confirmed','owned_tree_empty'))
        and body['job_final']['active_processes']==0 and body['job_final']['owned_processes']==[],
        'ONE_REAL_SUCCESSFUL_CHILD_PRESERVED_NO_RERUN')
    m.m.job_contract(body)
    require(p.v.pins(body['source_freeze'])==req and len(req)==1658 and sum(z['bytes'] for z in req.values())==121039342,
        'EXACT_ORIGINAL_EXECUTED1658_OLD95_NOT_CURRENT_CODE_ALIAS')
    passes=body['owned_source_reader_passes'];frame=root['terminal_source_frame'];h=frame['handles'];dup=h['borrowed_byte_streams']
    require(len(passes)==2 and passes[0]['read_passes']==1658 and passes[0]['bytes_read']==121039342
        and passes[1]['read_passes']==728 and passes[1]['bytes_read']==63288057
        and all(z['read_rates_by_kind']==dict(binary=1048576,other=2097152)
            and z['original_owned_read_operations_preserved'] is True and z['extra_sampler_or_native_query_started'] is False for z in passes)
        and frame['frame_state']=='CLOSED' and frame['registered_live_frame'] is False
        and frame['input_count']==1658 and frame['input_bytes']==121039342
        and len(frame['actual_byte_boundaries'])==1 and frame['actual_byte_boundaries'][0]['role']=='before'
        and p.v.pins(frame['actual_byte_boundaries'][0]['actual_byte_pins'])==req
        and frame['held_identity_after_owned_cleanup'] is None
        and h['input_lock_handles_opened']==h['input_lock_handles_closed']==1966
        and h['input_lock_handles_remaining']==h['active_reader_bindings']==h['active_byte_streams']==h['handle_close_failed_attempts']==0
        and h['input_lock_cleanup_confirmed'] is True and h['maximum_lock_seconds']==600
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2386
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==0
        and dup['active_borrow_binding'] is False and dup['byte_stream_pathname_reopens']==0,
        'ORIGINAL_FULL_BEFORE_PARTIAL728_ALL_HANDLES_CLOSED')
    m.profile.phase_contract(h['acquisition_phase_pressure'],1966,True);m.m.early_contract(root['early_source_checkpoint'])
    io_=root['preparation_IO'];stats=root['terminal_parent_failure_statistics']
    require(io_['finished'] is True and io_['bound_inputs']==io_['final_fresh_hashes']==181
        and io_['read_passes']==362 and io_['bytes_read']==29354226
        and stats['characters_written']==P108_BODY['bytes'] and stats['semantic_fields_intentionally_removed']==0
        and stats['terminal_failed_evidence_only'] is True and stats['runtime_accepted'] is False
        and stats['original_files_rewritten'] is False and stats['original_live_frame_guard_restarted'] is False,
        'ORIGINAL_ALL_METADATA_AND_BOUNDED_FAILURE_WRITE')
    for doc in (root,body):
        require(doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
            and all(doc[k] is False for k in ('full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved')),
            'PENDING108_NO_GATE_PROMOTION')
    return pending108_summary()

def closing_pin(value,kind):
    pin=json.loads(value) if isinstance(value,str) else value
    require(kind in ('review','source','accept') and type(pin) is dict and set(pin)=={'path','bytes','sha256'}
        and type(pin['bytes']) is int and 0<pin['bytes']<=16777216 and isinstance(pin['sha256'],str)
        and re.fullmatch('[0-9a-f]{64}',pin['sha256']) is not None and isinstance(pin['path'],str)
        and re.fullmatch(re.escape(p.DIR)+r'/p340-closing-'+kind+r'-run[0-9]{3}\.v1\.json',pin['path']) is not None,
        'EXACT_CLOSING_LITERAL_PIN')
    return pin

def closing_contract(doc,scope,codes,reviewed=None,review_pin=None,source=None,source_pin=None):
    legacy,plan,names,binding,required,extras,baseline,added,_,_=scope
    common(doc,plan,names,required,binding,extras,baseline,added,codes)
    require(plan['runtime_source_qualified_individual_cases']==101 and plan['next_runtime_index']==108
        and doc['pending108_product_review']==pending108_summary()
        and doc['actual_product_child_executed'] is False and doc['accepted_exact_product_body_count']==0
        and doc['source_attempted'] is False and doc['source_qualified'] is False
        and doc['original_parent_capture_adapter_selected'] is False and doc['diagnostic_parent_connection_selected'] is False
        and doc['successful_product_reexecution_allowed'] is False
        and doc['original_failed_root_accepted'] is False and doc['original_partial_after_hash_completed'] is False
        and doc['source_kind']=='INDEPENDENT_CURRENT95_AFTER_COMPLETED108_NOT_ORIGINAL_PARTIAL_AFTER'
        and doc['original_executed_source_pins']==list(pending108_scope(required).values())
        and doc['current_source_transition_paths']==[SELF,TEST],
        'INDEPENDENT_SOURCE_EPOCH_NOT_NEW_PRODUCT_OR_ORIGINAL_REWRITE')
    if doc['state']==C_REVIEW:
        require(doc['runtime_contract_executions']==EXECUTED and doc['reused_light_contract_executions']==0
            and doc['own_queue_contract_tests_passed']==doc['synthetic_following_queue_contract_tests_passed']==COUNT
            and doc['independent_source_frame_attempted'] is False and doc['independent_source_frame_qualified'] is False
            and doc.get('source_frame') is None and 'runtime_plan' not in doc,'CLOSING_REVIEW_ONLY_ALL_CURRENT_CONTRACTS')
        m.guarded_contract(doc['contract_checkpoint_statistics'],EXECUTED)
        return
    require(doc['state'] in (C_SOURCE,C_ACCEPT) and reviewed is not None,'ONLY_SOURCE_OR_ACCEPT')
    closing_contract(reviewed,scope,codes);closing_pin(review_pin,'review')
    require(doc['closing_review_pin']==review_pin and doc['runtime_contract_executions']==0
        and doc['contract_checkpoint_statistics'] is None and doc['reused_light_contract_executions']==EXECUTED
        and doc['qualified_contract_checkpoint_statistics']==reviewed['contract_checkpoint_statistics'],
        'EXACT_SAME_CODE_REVIEW_REUSE_NO_FABRICATED_TESTS')
    if doc['state']==C_SOURCE:
        require(doc['independent_source_frame_attempted'] is True and doc['independent_source_frame_qualified'] is True
            and 'runtime_plan' not in doc,'SOURCE_NATIVE_ONLY_NO_ADVANCE')
        path_guard_contract(doc['source_path_guard_diagnostics'])
        rebound(x.validate_source,N=N,DIRECTORIES=DIRECTORIES,SOURCE_PASS=C_SOURCE,prepared=closing_source_header)(doc,required)
        return
    closing_pin(source_pin,'source')
    require(source is not None and source['closing_review_pin']==review_pin and doc['closing_source_pin']==source_pin,
        'EXACT_REVIEW_SOURCE_ACCEPT_CHAIN')
    closing_contract(source,scope,codes,reviewed,review_pin)
    require(doc['independent_source_frame_attempted'] is False and doc['independent_source_frame_qualified'] is False
        and doc.get('source_frame') is None and doc['accepted_exact_compound_case_count']==1
        and doc['semantic_body_capture_pass_count']==1
        and doc['runtime_plan']==g.advance(legacy,plan,names,108),'EXACT_ONCE_COMPOUND102_NOT_ORIGINAL_FAILED_PASS')

def closing_source_header(doc,required):
    # 106 전용 metadata 기대값만 현재108로 바인딩. 원 Native/두 byte/identity/cleanup oracle 유지.
    require(doc['schema_version']==SCHEMA and doc['state']==C_SOURCE and len(required)==N
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['preparation_IO']['finished'] is True
        and doc['preparation_IO']['bound_inputs']==doc['preparation_IO']['final_fresh_hashes']
        and doc['pending108_product_review']==pending108_summary() and doc['actual_product_child_executed'] is False
        and doc['successful_product_reexecution_allowed'] is False
        and doc['original_failed_root_accepted'] is False and doc['original_partial_after_hash_completed'] is False
        and doc['independent_source_frame_attempted'] is True and doc['independent_source_frame_qualified'] is True
        and p.v.pins(doc['original_executed_source_pins'])==pending108_scope(required)
        and doc['current_source_transition_paths']==[SELF,TEST],
        'CURRENT1658_SOURCE_HEADER_REPLACES_ONLY_106_SPECIFIC_METADATA')

def pending108_scope(required):
    return {**required,**{z['path']:z for z in P108_CODE}}

def require_no_pending_product_reexecution(index):
    require(index!=108,'SUCCESSFUL108_SOURCE_CLOSING_REQUIRED_NO_PRODUCT_REEXECUTION')

def closing_accept_from_folder(q,scope):
    folder=p.c.ROOT/p.DIR;paths=list(folder.glob('p340-closing-accept-run*.v1.json'))
    require(len(paths)<=64,'BOUNDED_COMPOUND_ACCEPT_NAMESPACE');accepted=None
    bound=m.m.m.review.bound_json
    for path in sorted(paths):
        name=path.relative_to(p.c.ROOT).as_posix();doc=q.json(name)
        if doc['state']=='FAILED_NOT_ACCEPTED':
            require(doc['actual_product_child_executed'] is False and doc['resource_watcher_cleanup_confirmed'] is True,
                'FAILED_ACCEPT_NO_PRODUCT_OR_LIVE_RESOURCES');continue
        pin=closing_pin(q.reader.snapshots[name],'accept')
        rp=closing_pin(doc['closing_review_pin'],'review');reviewed=bound(q,rp)
        sp=closing_pin(doc['closing_source_pin'],'source');source=bound(q,sp)
        closing_contract(doc,scope,q.codes,reviewed,rp,source,sp)
        require(accepted is None,'ONLY_ONE_COMPOUND108_ACCEPTANCE')
        accepted=(pin,doc)
    return accepted

PREFORMAL400_PIN=dict(path=p.DIR+'/p340-closing-review-run019.v1.json',bytes=429686,sha256='d47ba93eb8c8d40be27658663574203929332932639dd2be20385900e86f39b2')
PREFORMAL400_CODE=[
 dict(path=SELF,bytes=87356,sha256='c7217c6eed7a6ef992ff405d308b30d6b1c360ec6e641bf25aa6c577535044a9'),
 dict(path=TEST,bytes=44479,sha256='b99464b89a36eef2fc73bceb2c1c85f50926f5d872cd4fc77e62c6d6c8788dd3')]

def preformal400_summary():
    return dict(pin=PREFORMAL400_PIN,original_failed_preserved=True,qualification400_not_passed=True,
        partial_current200_one_runner=True,Native_or_product_started=False,cleanup_confirmed=True,
        found_cause='SYNTHETIC_EXPECTED_PIN_ALIAS_NOT_INDEPENDENT')

def preformal400_review(doc):
    require(doc['schema_version']=='hwpx-agent.p09-preserved106-fixed-runtime-queue/v10'
        and doc['state']=='FAILED_NOT_ACCEPTED' and doc['failure_diagnostic']['stage']=='contract_tests'
        and doc['error_code']=='P208_POST_STOP_RUNTIME_DIAGNOSTIC_RUNTIME_REVIEWED_STOP_QUEUE_RUNTIME_PRESERVED106_QUEUE_ALL_CURRENT_AND_FOLLOWING_CONTRACTS'
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['current95_code_pins']==FROZEN93+PREFORMAL400_CODE
        and doc['pending108_product_review']==pending108_summary() and doc['runtime_contract_executions']==0
        and doc['actual_product_child_executed'] is False and doc['independent_source_frame_attempted'] is False
        and doc['independent_source_frame_qualified'] is False and doc.get('source_frame') is None
        and doc['contract_failures']==[
            'test_accept_no_source_pin_substitution (test_preserved106_queue_runtime.Completed108ClosingTests.test_accept_no_source_pin_substitution)',
            'test_source_wrong_review_pin (test_preserved106_queue_runtime.Completed108ClosingTests.test_source_wrong_review_pin)'],
        'IMMUTABLE_PREFORMAL400_TWO_SYNTHETIC_ALIAS_FAILURES_NOT_NATIVE')
    row=doc['contract_checkpoint_statistics'];io_=doc['preparation_IO']
    require(row['started_tests']==row['stopped_tests']==row['successful_before_test_checks']==row['successful_after_test_checks']==200
        and row['runner_calls']==row['returned_runner_calls']==row['successful_before_runner_checks']==row['successful_after_runner_checks']==1
        and row['original_unittest_results_preserved'] is True and row['new_sampler_or_thread_or_sleep_started'] is False
        and row['original_guard_or_test_coverage_relaxed'] is False
        and io_['bound_inputs']==io_['read_passes']==186 and io_['final_fresh_hashes']==0 and io_['finished'] is False,
        'PARTIAL200_NOT400_QUALIFICATION')
    return preformal400_summary()


class HeldPathGuard:
    """한 source 요청의 세 pathname 판정을 신선한 exact-held metadata로 묶는다.

    원 AuditEvidenceReader._source boolean guard와 P206 stream identity 검사는
    그대로 실행한다. reader/frame/binding 수명 밖으로 facade를 내보내지 않는다.
    Native.inspect의 내부 kernel 호출 수 감소나 프리즈 해결은 주장하지 않는다.
    """
    def __init__(self,frame,reader):
        frame.check()
        require(reader.root==frame.held.root and '_source' not in vars(reader)
            and getattr(reader._source,'__func__',None) is audit.AuditEvidenceReader._source,
            'EXACT_ORIGINAL_AUDIT_SOURCE_AND_ROOT')
        self.frame=frame;self.reader=reader;self.original_root=reader.root;self.closed=False
        self.regular={str(path):(name,handle) for name,path,handle,directory in frame.held.owned if not directory}
        require(set(self.regular)=={str(self.original_root/name) for name in frame.inputs},
            'ALL_EXACT_HELD_REGULAR_INPUTS')
        self.attempted=self.queries=self.guards=0;self.restored=False
        owner=self
        class Root:
            def __truediv__(self,name):return owner.source(name)
        self.root=Root();reader.root=self.root
    def check(self):
        require(not self.closed and self.reader.root is self.root,'LIVE_PATH_GUARD_ROOT')
        self.frame.check();held=self.frame.held
        require(id(self.reader) in held.active_readers
            and getattr(self.reader,'_p206_input_lock_owner',None) is held
            and held.borrower is not None and held.borrower.active_binding
            and held.borrower.bound_reader is self.reader
            and held.borrower.loan is None and held.borrower.close_failures==0,
            'LIVE_ORIGINAL_READER_AND_BORROW_BINDING')
    def source(self,name):
        self.check()
        require(type(name) is str and name in self.frame.inputs,'EXACT_FRAME_INPUT_NAME')
        path=self.original_root/name;key=str(path)
        require(key in self.regular and self.regular[key][0]==name,'EXACT_HELD_PATH_NAME')
        self.attempted+=1
        current=self.frame.held.api.inspect(self.regular[key][1]);self.queries+=1
        require(current==self.frame.held.files[key] and current['directory'] is False
            and current['reparse'] is False and current['inheritable'] is False,
            'FRESH_HELD_PATH_IDENTITY_TYPE_LINK_INHERITANCE')
        owner=self;root=self.root;token=self.frame.held.borrower.binding_token
        class Source:
            def __str__(self):return str(path)
            def relative_to(self,base):return path.relative_to(base)
            def predicate(self,result):
                owner.check();require(owner.root is root and owner.frame.held.borrower.binding_token is token,
                    'EXACT_PATH_FACADE_TOKEN')
                owner.guards+=1;return result
            def is_file(self):return self.predicate(not current['directory'])
            def is_symlink(self):return self.predicate(current['reparse'])
            def is_junction(self):return self.predicate(current['reparse'])
            def open(self,mode):raise ValueError('HELD_PATH_FACADE_REQUIRES_ORIGINAL_BORROW_WRAPPER')
        return Source()
    def restore(self):
        # STOP 후 원 resource callback을 재호출하지 않아도 adapter를 반드시 복구한다.
        self.frame.registry.check()
        correct=self.reader.root is self.root
        self.reader.root=self.original_root;self.closed=True;self.restored=self.reader.root is self.original_root
        require(correct and self.restored,'ORIGINAL_READER_ROOT_RESTORED')
    def summary(self):
        return dict(native_metadata_queries_attempted=self.attempted,fresh_held_metadata_queries=self.queries,
            original_path_guard_predicates=self.guards,original_reader_root_restored=self.restored,
            active_path_guard_adapter=not self.closed,pathname_metadata_probes=0,
            original_stream_identity_check_retained=True,metadata_reused_between_source_requests=False,
            added_native_queries_recorded_separately_from_original_lock_checks=True,
            kernel_call_reduction_or_CPU_freeze_improvement_claimed=False)

def read_with_held_path_guards(frame,factory,checkpoint,diagnostics):
    adapters=[]
    def wrapped(guarded):
        reader=factory(guarded);adapters.append(HeldPathGuard(frame,reader));return reader
    try:return frame.read_boundary(wrapped,checkpoint)
    finally:
        for adapter in adapters:
            try:adapter.restore()
            finally:diagnostics.append(adapter.summary())

def path_guard_contract(rows):
    require(type(rows) is list and len(rows)==2,'TWO_PATH_GUARD_BOUNDARIES')
    for row in rows:
        require(row['native_metadata_queries_attempted']==row['fresh_held_metadata_queries']==N
            and row['original_path_guard_predicates']==3*N
            and row['original_reader_root_restored'] is True and row['active_path_guard_adapter'] is False
            and row['pathname_metadata_probes']==0 and row['original_stream_identity_check_retained'] is True
            and row['metadata_reused_between_source_requests'] is False
            and row['added_native_queries_recorded_separately_from_original_lock_checks'] is True
            and row['kernel_call_reduction_or_CPU_freeze_improvement_claimed'] is False,
            'ALL_CURRENT_INPUT_GUARDS_FRESH_RESTORED_NOT_SKIPPED')

SOURCE021_PIN=dict(path=p.DIR+'/p340-closing-source-run021.v1.json',bytes=819478,sha256='8c94da41f340ef9d877a488b1a56ab23d10fa6f6dfda566777dc5d2530b30f95')
REVIEW404_PIN=dict(path=p.DIR+'/p340-closing-review-run020.v1.json',bytes=186067,sha256='d6ad33748c2092ea1065938fa9d2834975b6380c12d77fce836d12d0eecb769a')
SOURCE021_CODE=[
 dict(path=SELF,bytes=90666,sha256='cbc7051ab7542ab71efe239758dcd9651954e20edfd739ce434dae1c193c3dc4'),
 dict(path=TEST,bytes=44786,sha256='fa3a811c945d3ca6b2087a99d4704f8784599d9142a148c8d62a9cb22b51ee1e')]

def source021_summary():
    return dict(pin=SOURCE021_PIN,qualified_review_pin=REVIEW404_PIN,
        original_failed_preserved=True,independent_source_not_qualified=True,
        actual_product_reexecution=False,partial_read_count426_not_full_boundary=True,
        owned_handle_and_adapter_cleanup_confirmed=True,CPU_stop_not_bypassed=True)

def source021_review(doc,reviewed,scope):
    legacy,plan,names,binding,required,extras,baseline,added,_,_=scope
    old_required={**required,**{z['path']:z for z in SOURCE021_CODE}}
    old_added={**added,**{z['path']:z for z in SOURCE021_CODE}}
    old_extras={**extras,**{z['path']:z for z in SOURCE021_CODE}}
    old_scope=(legacy,plan,names,binding,old_required,old_extras,baseline,old_added,scope[8],scope[9])
    old_common=rebound(common,SCHEMA='hwpx-agent.p09-preserved106-fixed-runtime-queue/v11')
    rebound(closing_contract,common=old_common,COUNT=202,EXECUTED=404)(reviewed,old_scope,FROZEN93+SOURCE021_CODE)
    require(doc['schema_version']=='hwpx-agent.p09-preserved106-fixed-runtime-queue/v11'
        and doc['state']=='FAILED_NOT_ACCEPTED' and doc['error_code']==doc['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and doc['failure_diagnostic']['stage']=='metadata_hash'
        and doc['resource_watcher_cleanup_confirmed'] is True and doc['current95_code_pins']==FROZEN93+SOURCE021_CODE
        and doc['closing_review_pin']==REVIEW404_PIN and doc['actual_product_child_executed'] is False
        and doc['accepted_exact_product_body_count']==doc['runtime_contract_executions']==0
        and doc['reused_light_contract_executions']==404 and doc['independent_source_frame_attempted'] is True
        and doc['independent_source_frame_qualified'] is False
        and doc['successful_product_reexecution_allowed'] is False and doc['original_failed_root_accepted'] is False
        and doc['original_partial_after_hash_completed'] is False
        and doc['pending108_product_review']==pending108_summary(),
        'EXACT_SOURCE021_CPU_STOP_AFTER404_NOT_NEW_PRODUCT')
    f=doc['source_frame'];h=f['handles'];b=h['borrowed_byte_streams'];io_=doc['preparation_IO']
    require(f['frame_state']=='CLOSED' and f['registered_live_frame'] is False
        and f['input_count']==N and f['input_bytes']==121075799 and f['actual_byte_boundaries']==[]
        and h['input_lock_handles_opened']==h['input_lock_handles_closed']==N+DIRECTORIES
        and h['input_lock_cleanup_confirmed'] is True
        and all(h[k]==0 for k in ('input_lock_handles_remaining','active_reader_bindings','active_byte_streams','handle_close_failed_attempts'))
        and h['handle_metadata_checks']==N+DIRECTORIES+426
        and b['duplicate_handles_opened']==b['duplicate_handles_closed']==b['shared_offset_resets']==426
        and b['duplicate_handles_remaining']==b['duplicate_close_failed_attempts']==b['byte_stream_pathname_reopens']==0
        and b['active_borrow_binding'] is False
        and io_['bound_inputs']==io_['final_fresh_hashes']==190 and io_['read_passes']==380
        and io_['bytes_read']==34211174 and io_['finished'] is True
        and doc['early_source_checkpoint']['original_hard_CPU_RAM600_guards_preserved'] is True,
        'ALL_SOURCE021_RESOURCES_CLOSED_PARTIAL426_NEVER_FULL')
    return source021_summary()



REVIEW022_PIN=dict(path=p.DIR+'/p340-closing-review-run022.v1.json',bytes=438848,sha256='626321cae7d63f9b45d896d986186aa812c1094a59405d06f94c9c43a5af6288')
REVIEW022_CODE=[
 dict(path=SELF,bytes=100997,sha256='bf52033555c8b067645044d4ea4f09cf0901322b7fcaeaccd40f6fc91af5a1f8'),
 dict(path=TEST,bytes=56849,sha256='14be30332205ad2acb9ef30bced4d286d1b813e18142d701128e54e232f171f8')]

def review022_summary():
    return dict(pin=REVIEW022_PIN,original_CPU_stop_preserved=True,partial14_not484_qualified=True,
        Native_or_product_started=False,resource_owner_cleanup_confirmed=True,
        original_contract_scope_and_guards_retained=True)

def review022_stop(doc):
    require(doc['schema_version']=='hwpx-agent.p09-preserved106-fixed-runtime-queue/v12'
        and doc['state']=='FAILED_NOT_ACCEPTED' and doc['error_code']==doc['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and doc['failure_diagnostic']['stage']=='contract_tests' and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['current95_code_pins']==FROZEN93+REVIEW022_CODE
        and doc['source021_CPU_stop_review']==source021_summary()
        and doc['runtime_contract_executions']==0 and doc['actual_product_child_executed'] is False
        and doc['independent_source_frame_attempted'] is False and doc['independent_source_frame_qualified'] is False
        and doc.get('source_frame') is None and doc['source_path_guard_diagnostics']==[],
        'EXACT_REVIEW022_CONTRACT_CPU_STOP_NO_NATIVE')
    row=doc['contract_checkpoint_statistics'];io_=doc['preparation_IO']
    require(row['started_tests']==row['stopped_tests']==row['successful_before_test_checks']==14
        and row['successful_after_test_checks']==13
        and row['runner_calls']==row['successful_before_runner_checks']==1
        and row['returned_runner_calls']==row['successful_after_runner_checks']==0
        and row['original_unittest_results_preserved'] is True and row['original_guard_or_test_coverage_relaxed'] is False
        and row['new_sampler_or_thread_or_sleep_started'] is False
        and io_['bound_inputs']==io_['read_passes']==193 and io_['final_fresh_hashes']==0
        and io_['bytes_read']==18082911 and io_['finished'] is False,
        'REVIEW022_PARTIAL14_PREPARATION_UNFINISHED_NO_PROMOTION')
    return review022_summary()


def bootstrap(q):
    healthy={};original_json=q.json
    def capture_healthy(name):
        value=original_json(name)
        if name==p.DIR+'/cases/p335-case-105-run009.json':healthy['body']=value
        return value
    with patch.object(q,'json',capture_healthy):
        legacy,base,names,binding,original,closed,root,body,checked,codes,latest=x.load(q)
    require('body' in healthy,'ONE_SAME_READER_HEALTHY_BODY_FOR_SYNTHETIC_CONTRACTS')
    require(codes==FROZEN93,'PHYSICAL_ORIGINAL93_IMMUTABLE')
    bound=m.m.m.review.bound_json
    reviewed=bound(q,COMPOUND_REVIEW);source=bound(q,COMPOUND_SOURCE);doc=bound(q,COMPOUND)
    plan=compound(doc,reviewed,source,legacy,base,names,closed,checked,codes)
    oldadded=p.v.pins(root['scope_added_ten_pins']);oldextras=p.v.pins(root['extra_frame_controller_pins'])
    baseline={k:v for k,v in original.items() if k not in oldadded}
    new={z['path']:z for z in CLOSING_CODE}
    new.update({name:q.pin(name) for name in (SELF,TEST)})
    added={**oldadded,**new};required={**baseline,**added};extras={**oldextras,**new}
    require(len(oldadded)==10 and len(oldextras)==187 and len(extras)==191 and required=={**closed,SELF:new[SELF],TEST:new[TEST]},
        'ORIGINAL_FULL_SCOPE_PLUS_CLOSING2_AND_CURRENT2')
    budget(required,baseline,added)
    q.codes=FROZEN93+[new[SELF],new[TEST]]
    q.prequal_documents=[];q.prequal_reviews=[]
    for spec in PREQUAL_SPECS:
        for logical in spec['codes']:
            archive=dict(logical,path='implementation/p09/evidence/'+spec['archive']+'/'+logical['path'])
            require(q.pin(archive['path'])==archive,'EXACT_PREFORMAL_CODE_ARCHIVE')
        failure=bound(q,spec['pin']);q.prequal_documents.append(failure);q.prequal_reviews.append(prequal_review(failure,spec))
    q.prequal_document=q.prequal_documents[0]
    for logical in PRIOR_LIGHT_CODE:
        archive=dict(logical,path='implementation/p09/evidence/p340-formal172-code/'+logical['path'])
        require(q.pin(archive['path'])==archive,'EXACT_PRIOR172_CODE_ARCHIVE')
    q.prior_light_document=bound(q,PRIOR_LIGHT)
    q.prior_light_review=prior_light_review(q.prior_light_document,plan,names,required,binding,extras,baseline,added)
    for logical in EPOCH_CODE:
        archive=dict(logical,path='implementation/p09/evidence/p340-formal198-code/'+logical['path'])
        require(q.pin(archive['path'])==archive,'EXACT_PRIOR198_CODE_ARCHIVE')
    q.epoch_documents=[bound(q,z) for z in (EPOCH_LIGHT,EPOCH_FRESH,EPOCH_FAILURE)]
    q.epoch_review=epoch_review(*q.epoch_documents,plan,names,required,binding,extras,baseline,added)
    q.native107_base=plan
    for logical in NATIVE107_CODE:
        archive=dict(logical,path='implementation/p09/evidence/p340-formal232-code/'+logical['path'])
        require(q.pin(archive['path'])==archive,'EXACT_NATIVE107_CODE_ARCHIVE')
    q.native107_documents=[bound(q,z) for z in (NATIVE107_ROOT,NATIVE107_BODY,NATIVE107_LIGHT,NATIVE107_FRESH)]
    plan=native107_epoch(*q.native107_documents,legacy,plan,names,required,binding,extras,baseline,added)
    for logical in SCOPE_FAILURE_CODE:
        archive=dict(logical,path='implementation/p09/evidence/p340-preformal256-code/'+logical['path'])
        require(q.pin(archive['path'])==archive,'EXACT_SCOPE_FAILURE_CODE_ARCHIVE')
    q.scope_failure_document=bound(q,SCOPE_FAILURE)
    q.scope_failure_review=scope_failure_review(q.scope_failure_document)
    for logical in EPOCH272_CODE:
        archive=dict(logical,path='implementation/p09/evidence/p340-formal272-code/'+logical['path'])
        require(q.pin(archive['path'])==archive,'EXACT_PRIOR272_CODE_ARCHIVE')
    q.epoch272_documents=[bound(q,z) for z in EPOCH272_PINS]
    q.epoch272_review=epoch272_review(*q.epoch272_documents,plan,names,required,binding,extras,baseline,added)
    for logical in PARTIAL308_CODE:
        archive=dict(logical,path='implementation/p09/evidence/p340-v8-partial308-code/'+logical['path'])
        require(q.pin(archive['path'])==archive,'EXACT_PARTIAL308_CODE_ARCHIVE')
    q.partial308_document=bound(q,PARTIAL308_PIN)
    q.partial308_review=partial308_review(q.partial308_document,plan,names,required,binding,extras,baseline,added)
    for logical in P108_CODE:
        archive=dict(logical,path='implementation/p09/evidence/p340-formal320-code/'+logical['path'])
        require(q.pin(archive['path'])==archive,'EXACT_PRODUCT108_V9_CODE_ARCHIVE')
    q.pending108_base=plan
    q.pending108_documents=[bound(q,z) for z in (P108_ROOT,P108_BODY,P108_LIGHT,P108_FRESH)]
    require(q.pin(P108_ZERO['path'])==P108_ZERO,'ORIGINAL108_ZERO_PLACEHOLDER_UNCHANGED')
    q.pending108_review=pending108_review(*q.pending108_documents,plan,names,required,binding,extras,baseline,added)
    for logical in PREFORMAL400_CODE:
        archive=dict(logical,path='implementation/p09/evidence/p340-v10-partial400-code/'+logical['path'])
        require(q.pin(archive['path'])==archive,'EXACT_PREFORMAL400_CODE_ARCHIVE')
    q.preformal400_document=bound(q,PREFORMAL400_PIN)
    q.preformal400_review=preformal400_review(q.preformal400_document)
    for logical in SOURCE021_CODE:
        archive=dict(logical,path='implementation/p09/evidence/p340-formal404-code/'+logical['path'])
        require(q.pin(archive['path'])==archive,'EXACT_SOURCE021_V11_CODE_ARCHIVE')
    q.source021_document=bound(q,SOURCE021_PIN);q.review404_document=bound(q,REVIEW404_PIN)
    q.source021_review=source021_review(q.source021_document,q.review404_document,
        (legacy,plan,names,binding,required,extras,baseline,added,(latest,healthy['body']),(doc,reviewed,source,base,closed,checked,codes)))
    for logical in REVIEW022_CODE:
        archive=dict(logical,path='implementation/p09/evidence/p340-v12-partial484-code/'+logical['path'])
        require(q.pin(archive['path'])==archive,'EXACT_REVIEW022_CODE_ARCHIVE')
    q.review022_document=bound(q,REVIEW022_PIN);q.review022_stop=review022_stop(q.review022_document)
    return legacy,plan,names,binding,required,extras,baseline,added,(latest,healthy['body']),(doc,reviewed,source,base,closed,checked,codes)

def pin_argument(value,kind):
    pin=json.loads(value) if isinstance(value,str) else value
    require(type(pin) is dict and set(pin)=={'path','bytes','sha256'} and type(pin['bytes']) is int
        and 0<pin['bytes']<=16777216 and isinstance(pin['sha256'],str) and re.fullmatch('[0-9a-f]{64}',pin['sha256']) is not None,
        'EXACT_LITERAL_PIN')
    pattern={'stop':r'p340-(?:case-[0-9]{3}|admission|light|light-review)-run[0-9]{3}\.v1\.json',
        'review':r'p340-stop-review-run[0-9]{3}\.v1\.json','light':r'p340-light-run[0-9]{3}\.v1\.json','fresh':r'p340-light-review-run[0-9]{3}\.v1\.json'}[kind]
    require(isinstance(pin['path'],str) and pin['path'].startswith(p.DIR+'/')
        and re.fullmatch(pattern,pin['path'][len(p.DIR)+1:]) is not None,'SCOPED_FILENAME_NOT_SUBSTRING')
    return pin

def common(doc,plan,names,required,binding,extras,baseline,added,codes):
    index,name=g.old.select(plan,names)
    if int(SCHEMA.rsplit('/v',1)[1])>=13:require(doc['review022_CPU_stop_review']==review022_summary(),'CURRENT_CONTRACT_CPU_STOP_REVIEW_REQUIRED')
    if int(SCHEMA.rsplit('/v',1)[1])>=12:require(doc['source021_CPU_stop_review']==source021_summary(),'CURRENT_SOURCE021_CLEANUP_REVIEW_REQUIRED')
    if int(SCHEMA.rsplit('/v',1)[1])>=11:require(doc['preformal400_failure_review']==preformal400_summary(),'CURRENT_PREFORMAL400_REVIEW_REQUIRED')
    if int(SCHEMA.rsplit('/v',1)[1])>=10:require(doc['pending108_product_review']==pending108_summary(),'CURRENT_COMPLETED108_CAPTURE_REVIEW_REQUIRED')
    if int(SCHEMA.rsplit('/v',1)[1])>=9:require(doc['partial308_stop_review']==partial308_summary(),'CURRENT_PARTIAL308_STOP_REVIEW_REQUIRED')
    if int(SCHEMA.rsplit('/v',1)[1])>=8:require(doc['epoch272_stop_review']==epoch272_summary(),'CURRENT_PRIOR272_STOP_REVIEW_REQUIRED')
    if int(SCHEMA.rsplit('/v',1)[1])>=7:require(doc['scope_fix_failure_review']==scope_failure_summary(),'CURRENT_SCOPE_FAILURE_REVIEW_REQUIRED')
    if int(SCHEMA.rsplit('/v',1)[1])>=6:require(doc['native107_epoch_root_pin']==NATIVE107_ROOT,'CURRENT_NATIVE101_EPOCH_REQUIRED')
    require(doc['schema_version']==SCHEMA and doc.get('error_code') is None and doc['resource_stop_reason'] is None
        and doc['resource_watcher_cleanup_confirmed'] is True and doc['compound100_pin']==COMPOUND
        and doc['compound100_review_pin']==COMPOUND_REVIEW and doc['compound100_source_pin']==COMPOUND_SOURCE
        and doc['original93_pins']==FROZEN93 and doc['current95_code_pins']==codes
        and doc['startup_limits']==STARTUP_LIMITS and doc['stop_resume_policy']==m.STOP_POLICY
        and doc['original_successful_bodies_not_reexecuted'] is True and doc['prior_runtime_plan']==plan
        and doc['selected_test_index']==index and doc['selected_test_name']==name and doc['binding']==binding
        and doc['prequalification_failure_reviews']==[prequal_summary(z) for z in PREQUAL_SPECS]
        and doc['scope_budget']==budget(required,baseline,added) and doc['scope_added_ten_pins']==list(added.values())
        and doc['extra_frame_controller_pins']==list(extras.values()),'EXACT_CURRENT_SCOPE_CODE_CURSOR')
    require(doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc[k] is False for k in ('whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
            'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved')),'NO_GATE_PROMOTION')
    io_=doc['preparation_IO'];require(io_['finished'] is True and io_['bound_inputs']==io_['final_fresh_hashes'],'ORIGINAL_ALL_FRESH')
    m.leading_contract(io_)

def light_contract(doc,plan,names,required,binding,extras,baseline,added,codes):
    common(doc,plan,names,required,binding,extras,baseline,added,codes)
    require(doc['state']==LIGHT and doc['runtime_contract_executions']==EXECUTED
        and doc['own_queue_contract_tests_passed']==doc['synthetic_following_queue_contract_tests_passed']==COUNT
        and doc['accepted_exact_product_body_count']==0 and doc['source_attempted'] is False
        and doc['actual_product_child_executed'] is False and doc['source_qualified'] is False
        and doc['original_parent_capture_adapter_selected'] is False and doc['diagnostic_parent_connection_selected'] is False
        and doc.get('closing_component') is None
        and doc.get('case_receipt_pin') is None,'ACTUAL_CONTRACTS_NOT_NATIVE_OR_PRODUCT')
    m.guarded_contract(doc['contract_checkpoint_statistics'],EXECUTED)

def fresh_contract(doc,light,light_pin,plan,names,required,binding,extras,baseline,added,codes):
    light_contract(light,plan,names,required,binding,extras,baseline,added,codes)
    common(doc,plan,names,required,binding,extras,baseline,added,codes)
    require(doc['state']==FRESH and doc['reviewed_light_pin']==light_pin and doc['runtime_contract_executions']==0
        and doc['reused_light_contract_executions']==EXECUTED and doc['contract_checkpoint_statistics'] is None
        and doc['qualified_contract_checkpoint_statistics']==light['contract_checkpoint_statistics']
        and doc['source_attempted'] is False and doc['source_qualified'] is False and doc['actual_product_child_executed'] is False
        and doc.get('closing_component') is None and doc.get('case_receipt_pin') is None
        and doc['original_parent_capture_adapter_selected'] is False and doc['diagnostic_parent_connection_selected'] is False
        and doc['accepted_exact_product_body_count']==0,'DISTINCT_FRESH_NO_FABRICATED_EXECUTIONS')

def record(doc,body,pin,legacy,plan,names,required,binding,extras,baseline,added,codes):
    common(doc,plan,names,required,binding,extras,baseline,added,codes);index,name=g.old.select(plan,names)
    require(doc['state']==PASS and doc['runtime_contract_executions']==0 and doc['reused_light_contract_executions']==EXECUTED
        and doc['contract_checkpoint_statistics'] is None and doc['accepted_exact_product_body_count']==1
        and doc['runtime_plan']==g.advance(legacy,plan,names,index) and name not in plan['runtime_qualified_test_names']
        and doc['case_receipt_pin']==pin and doc['actual_product_child_executed'] is True
        and body['actual_product_child_executed'] is True
        and doc['source_attempted'] is True and doc['source_qualified'] is True
        and doc['existing_body_replay_guard_verified'] is True
        and body['task']==body['minimal_worker_task']==f'p204-r07-case-{index:03}-tests'
        and doc['parent_return_status_recorded_before_after_parent_guard'] is True
        and type(doc['original_parent_return_code']) is int and doc['original_parent_return_code']==0
        and doc['original_parent_pending_failure_before_after_parent_guard'] is False
        and doc['original_parent_rejected_failure_before_after_parent_guard'] is False
        and doc['aggregate_post_reader_connection_verified'] is True
        and doc['original_parent_capture_adapter_selected'] is True and doc['diagnostic_parent_connection_selected'] is True
        and doc['early_source_guard_connected'] is True and doc['acquisition_phase_connection_selected'] is True
        and doc['native_timing_connected'] is True,'EXACT_NEXT_ONE_ACTUAL_NATIVE_RETURN')
    m.guarded_contract(doc['qualified_contract_checkpoint_statistics'],EXECUTED)
    pin_argument(doc['qualified_light_pin'],'light');pin_argument(doc['independent_fresh_pin'],'fresh')
    require(doc['receipt_serialization_policy']==r.policy() and doc['monotonic_binding_policy']==m.review.policy()
        and doc['preparation_IO']['read_passes']+doc['closing_component']['metadata_IO']['read_passes']<=720,
        'ORIGINAL_AGGREGATE_READ_BUDGET')
    m.leading_contract(doc['closing_component']['metadata_IO']);m.m.job_contract(body)
    m.m.early_contract(doc['early_source_checkpoint'])
    native_pair(doc['closing_component'],body,pin,required,binding,extras)
    r.stats_contract(doc['packed_parent_write_statistics'],pin)
    return doc['runtime_plan']

def review_contract(doc,rp,root,plan,names,required,binding,extras,baseline,added,codes,sidecar=None,zero=None):
    common(doc,plan,names,required,binding,extras,baseline,added,codes)
    classification=stopped(root,plan,required,binding,extras,baseline,added,names,sidecar)
    require(doc['state']==STOP_REVIEW and doc['reviewed_root_pin']==rp
        and doc['reviewed_failure_classification']==classification and doc['reviewed_body_placeholder_pin']==zero
        and doc['runtime_contract_executions']==0
        and doc['source_attempted'] is False and doc['actual_product_child_executed'] is False
        and doc['accepted_exact_product_body_count']==0,'REVIEW_NOT_GO_OR_ADVANCE')

def cached_light_json(q):
    # 같은 Reader의 LIGHT/FRESH 각 마지막1개, 총2개만 유지. 원 final-fresh는 그대로 수행.
    original=q.json;last={}
    def read(name):
        match=re.fullmatch(re.escape(p.DIR)+r'/p340-(light|light-review)-run[0-9]{3}\.v1\.json',name)
        kind=match.group(1) if match else None
        if kind in last and last[kind][0]==name:
            q.reader.checkpoint()
            return last[kind][1]
        value=original(name)
        pin=q.reader.snapshots.get(name,{})
        if kind is not None and value.get('state')==({'light':LIGHT,'light-review':FRESH}[kind]) \
                and value.get('source_attempted') is False and value.get('actual_product_child_executed') is False \
                and value.get('closing_component') is None and type(pin.get('bytes')) is int and 0<pin['bytes']<=131072:
            # 128KiB 초과/제품/Native/실패 JSON은 cache 대상 아님. 별도 명령 간 재사용 없음.
            last[kind]=(name,value)
        return value
    return read

def scan(q,scope,approved_pins=(),target=None):
    with patch.object(q,'json',cached_light_json(q)):
        q.closed108=closing_accept_from_folder(q,scope)
        if q.closed108 is not None:scope=current_contract_scope(scope,q.closed108[1]['runtime_plan'])
        return _scan(q,scope,approved_pins,target)

def _scan(q,scope,approved_pins=(),target=None):
    legacy,base,names,binding,required,extras,baseline,added,latest,prior=scope
    codes=q.codes;bound=m.m.m.review.bound_json;folder=p.c.ROOT/p.DIR
    files=list(folder.glob('p340-*-run*.v1.json'));require(len(files)<=2048,'BOUNDED_FIXED_NAMESPACE')
    rows=[];support=[];reviews={};plan=base;plans=[base];target_result=None;failures={}
    for ap in approved_pins:
        ap=pin_argument(ap,'review');d=bound(q,ap)
        rp=pin_argument(d['reviewed_root_pin'],'stop');require(rp['path'] not in reviews,'NO_DUPLICATE_APPROVAL')
        reviews[rp['path']]=(ap,d)
    for path in sorted(files):
        match=FILE.fullmatch(path.name)
        (rows if match else support).append(path)
    for path in rows:
        if path.relative_to(p.c.ROOT).as_posix()==P108_ROOT['path']:
            require(q.reader.snapshots[P108_ROOT['path']]==P108_ROOT and q.pending108_review==pending108_summary(),
                'ONLY_EXACT_SUCCESSFUL108_CAPTURE_PRESERVED_NOT_PRODUCT_RETRY')
            continue
        if path.relative_to(p.c.ROOT).as_posix()==EPOCH272_PINS[2]['path']:
            require(q.reader.snapshots[EPOCH272_PINS[2]['path']]==EPOCH272_PINS[2]
                and q.epoch272_review==epoch272_summary(),'ONLY_EXACT_REVIEWED_PRE_PRODUCT_NATIVE_STOP272')
            continue
        if path.relative_to(p.c.ROOT).as_posix()==NATIVE107_ROOT['path']:
            require(q.reader.snapshots[NATIVE107_ROOT['path']]==NATIVE107_ROOT,'ONLY_EXACT_NATIVE107_ALREADY_IN_BASE101')
            continue
        if path.relative_to(p.c.ROOT).as_posix()==EPOCH_FAILURE['path']:
            require(q.reader.snapshots[EPOCH_FAILURE['path']]==EPOCH_FAILURE and q.epoch_review['Native_or_product_started'] is False,
                'ONLY_EXACT_PRE_NATIVE_MODULE_FAILURE_ARCHIVE_REVIEW')
            continue
        d=q.json(path.relative_to(p.c.ROOT).as_posix());rp=q.reader.snapshots[path.relative_to(p.c.ROOT).as_posix()]
        index,number=map(int,FILE.fullmatch(path.name).groups())
        require(1<=index<=249 and 1<=number<=999 and d.get('selected_test_index')==index,'EXACT_CASE_FILE_ID')
        if d['state']=='FAILED_NOT_ACCEPTED':failures[rp['path']]=(rp,d,copy.deepcopy(plan));continue
        bp=d['case_receipt_pin'];require(bp['path']==f'{p.DIR}/cases/p340-case-{index:03}-run{number:03}.json','EXACT_BODY_PATH')
        body=bound(q,bp)
        lp=pin_argument(d['qualified_light_pin'],'light');light=bound(q,lp)
        fp=pin_argument(d['independent_fresh_pin'],'fresh');fresh=bound(q,fp)
        light_contract(light,plan,names,required,binding,extras,baseline,added,codes)
        fresh_contract(fresh,light,lp,plan,names,required,binding,extras,baseline,added,codes)
        require(fresh['reviewed_light_pin']==lp and d['qualified_contract_checkpoint_statistics']==light['contract_checkpoint_statistics'],
            'ACCEPTED_ORIGINAL_CURRENT_LIGHT_FRESH_CHAIN')
        plan=record(d,body,bp,legacy,plan,names,required,binding,extras,baseline,added,codes);plans.append(plan)
    lights=[];freshes=[];q.reviewed_zero_pins={}
    for path in support:
        name=path.relative_to(p.c.ROOT).as_posix()
        previous108={z['path']:z for z in (P108_LIGHT,P108_FRESH)}
        if name in previous108:
            require(q.reader.snapshots[name]==previous108[name] and q.pending108_review==pending108_summary(),
                'ORIGINAL320_PRODUCT108_EPOCH_NOT_CURRENT_GO')
            continue
        if path.name.startswith('p340-closing-'):
            require(re.fullmatch(r'p340-closing-(?:review|source|accept)-run[0-9]{3}\.v1\.json',path.name) is not None,
                'NO_UNKNOWN_CLOSING_NAMESPACE')
            continue
        if name==PARTIAL308_PIN['path']:
            require(q.reader.snapshots[name]==PARTIAL308_PIN and q.partial308_review==partial308_summary(),
                'ONLY_EXACT_INDEPENDENT_REVIEWED_PARTIAL308_STOP')
            continue
        prior272={z['path']:z for z in EPOCH272_PINS}
        if name in prior272:
            require(q.reader.snapshots[name]==prior272[name] and q.epoch272_review==epoch272_summary(),
                'ONLY_EXACT_ARCHIVE_REVIEW272_NOT_CURRENT_GO')
            continue
        prequal={z['pin']['path']:z['pin'] for z in PREQUAL_SPECS}
        epochs={z['path']:z for z in (EPOCH_LIGHT,EPOCH_FRESH)}
        natives={z['path']:z for z in (NATIVE107_LIGHT,NATIVE107_FRESH)}
        if name in natives:
            require(q.reader.snapshots[name]==natives[name],'NATIVE107_PREVIOUS_CODE_QUALIFICATION_NOT_CURRENT_GO')
            continue
        if name in epochs:
            require(q.reader.snapshots[name]==epochs[name] and q.epoch_review['current_actual_GO'] is False,'ONLY_ARCHIVE_BOUND198_NOT_CURRENT_GO')
            continue
        if name==PRIOR_LIGHT['path']:
            require(q.reader.snapshots[name]==PRIOR_LIGHT and q.prior_light_review['current_actual_GO'] is False,
                'PRIOR172_ARCHIVE_REVIEW_NOT_CURRENT_GO')
            continue
        if name==SCOPE_FAILURE['path']:
            require(q.reader.snapshots[name]==SCOPE_FAILURE and q.scope_failure_review==scope_failure_summary(),
                'ONLY_EXACT_INDEPENDENT_REVIEWED_SCOPE_FAILURE')
            continue
        if name in prequal:
            require(q.reader.snapshots[name]==prequal[name]
                and q.prequal_reviews==[prequal_summary(z) for z in PREQUAL_SPECS],'ONLY_EXACT_INDEPENDENT_REVIEWED_PREFORMAL_FAILURE')
            continue
        if path.name.startswith('p340-stop-review-'):continue
        require(re.fullmatch(r'p340-(?:admission|light|light-review)-run[0-9]{3}\.v1\.json',path.name) is not None,'NO_UNKNOWN_ROWS')
        d=q.json(name);rp=q.reader.snapshots[name]
        if d['state']=='FAILED_NOT_ACCEPTED':
            at=d.get('prior_runtime_plan',base);require(at in plans,'FAILED_CURSOR_KNOWN_NO_ADVANCE')
            failures[name]=(rp,d,at);continue
        at=d['prior_runtime_plan'];require(at in plans,'QUALIFICATION_KNOWN_CURSOR')
        if d['state']==LIGHT:
            light_contract(d,at,names,required,binding,extras,baseline,added,codes);lights.append((rp,d))
        else:
            lp=pin_argument(d['reviewed_light_pin'],'light');ld=bound(q,lp)
            fresh_contract(d,ld,lp,at,names,required,binding,extras,baseline,added,codes);freshes.append((rp,d,lp,ld))
    used=set()
    for name,(rp,d,at) in failures.items():
        side=bound(q,d['terminal_parent_failure_sidecar_pin']) if d.get('terminal_parent_failure_sidecar_pin') else None
        zero=placeholder(q,rp,d)
        if target is not None and rp==target:
            require(target_result is None,'EXACT_SINGLE_STOP_TARGET')
            target_result=(rp,d,at,stopped(d,at,required,binding,extras,baseline,added,names,side),side,zero);continue
        require(name in reviews,'UNREVIEWED_STOP_BLOCKS_GO')
        ap,reviewed=reviews[name];review_contract(reviewed,rp,d,at,names,required,binding,extras,baseline,added,codes,side,zero);used.add(name)
        if zero is not None:q.reviewed_zero_pins[zero['path']]=zero
    require(used==set(reviews) and (target is None or target_result is not None),'NO_UNUSED_APPROVAL_OR_MISSING_TARGET')
    q.lights=lights;q.freshes=freshes
    return plan,target_result

def select_light(q,plan):
    rows=[row for row in q.lights if row[1]['prior_runtime_plan']==plan]
    require(bool(rows),'CURRENT_QUALIFIED_LIGHT_REQUIRED');return rows[-1]

def select_go(q,plan):
    rows=[row for row in q.freshes if row[1]['prior_runtime_plan']==plan]
    require(bool(rows),'DISTINCT_CURRENT_FRESH_BEFORE_PRODUCT');return rows[-1]

def contracts(scope,q):
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_preserved106_queue_runtime as t
    statistics=None
    try:
        with m.WarmTestIsolation(),m.guarded.bind(q.reader.checkpoint) as statistics, \
                patch('subprocess.Popen',side_effect=AssertionError('NO_CONTRACT_CHILD')), \
                patch('subprocess.run',side_effect=AssertionError('NO_CONTRACT_CHILD')), \
                patch('threading.Thread.start',side_effect=AssertionError('NO_CONTRACT_THREAD')):
            for following in (False,True):
                with patch.multiple(t,FIXTURES=scope,FOLLOWING=following,TEMPLATE=None,LIGHT_TEMPLATE=None,CLOSING_TEMPLATE=None,CLOSING_TEMPLATE_BUILDS=0,PREQUALIFICATION=q.prequal_document,PREQUALIFICATION2=q.prequal_documents[1],LITERAL_PRIOR_LIGHT=q.prior_light_document,EPOCH_DOCUMENTS=q.epoch_documents,NATIVE107_DOCUMENTS=q.native107_documents,NATIVE107_BASE=q.native107_base,SCOPE_FAILURE_DOCUMENT=q.scope_failure_document,EPOCH272_DOCUMENTS=q.epoch272_documents,PARTIAL308_DOCUMENT=q.partial308_document,PENDING108_DOCUMENTS=q.pending108_documents,PENDING108_BASE=q.pending108_base,SOURCE021_DOCUMENT=q.source021_document,REVIEW404_DOCUMENT=q.review404_document,REVIEW022_DOCUMENT=q.review022_document):
                    result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(t))
                if not result.wasSuccessful():q.contract_failures=[str(t) for t,_ in result.failures+result.errors][:8]
                require(result.wasSuccessful() and result.testsRun==COUNT and not result.skipped,'ALL_CURRENT_AND_FOLLOWING_CONTRACTS')
        row=statistics.summary();m.guarded_contract(row,EXECUTED)
        require(unittest.TextTestRunner is m.guarded._ORIGINAL_RUNNER and m.guarded._ACTIVE is False,'ORIGINAL_RUNNER_RESTORED')
        return EXECUTED,row
    finally:q.contract_statistics=statistics.summary() if statistics is not None else None

def preserve(capture,owner,out,index,number):
    path=p.c.ROOT/f'{p.DIR}/cases/p340-failure-{index:03}-run{number:03}.json'
    with path.open('x',encoding='utf-8') as stream:
        output=m.PinningOutput(stream)
        stats=capture.write_rejected(output,owner,out) if capture.rejected else capture.write_terminal(output,owner,out)
    out.update(terminal_parent_failure_sidecar_pin=dict(path=path.relative_to(p.c.ROOT).as_posix(),
        bytes=output.written,sha256=output.digest.hexdigest()),terminal_parent_failure_statistics=stats,
        original_failure_body_placeholder_preserved=True)

def closing_main(args):
    require((args.mode!='closing-review')==(args.closing_review_pin is not None)
        and (args.mode=='closing-accept')==(args.closing_source_pin is not None)
        and not args.review_pin and args.stop_root_pin is None,'EXPLICIT_SOURCE_ONLY_MODE_PINS')
    destination=p.c.ROOT/f'{p.DIR}/p340-{args.mode}-run{args.run:03}.v1.json'
    require(not destination.exists(),'FRESH_SOURCE_ONLY_OUTPUT')
    context=g.observation.Context();owner=g.observation.Resources(context)
    q=frame=early=proposed=scope=reviewed=source=rp=sp=None;stage='admission'
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),
        compound100_pin=COMPOUND,compound100_review_pin=COMPOUND_REVIEW,compound100_source_pin=COMPOUND_SOURCE,
        original93_pins=FROZEN93,startup_limits=STARTUP_LIMITS,stop_resume_policy=m.STOP_POLICY,
        original_successful_bodies_not_reexecuted=True,accepted_exact_product_body_count=0,
        runtime_contract_executions=0,contract_checkpoint_statistics=None,reused_light_contract_executions=0,
        source_attempted=False,source_qualified=False,original_parent_capture_adapter_selected=False,
        diagnostic_parent_connection_selected=False,receipt_serialization_policy=r.policy(),
        monotonic_binding_policy=m.review.policy(),successful_product_reexecution_allowed=False,
        original_failed_root_accepted=False,original_partial_after_hash_completed=False,
        independent_source_frame_attempted=False,independent_source_frame_qualified=False,
        source_kind='INDEPENDENT_CURRENT95_AFTER_COMPLETED108_NOT_ORIGINAL_PARTIAL_AFTER',source_path_guard_diagnostics=[])
    try:
        owner.admit();q=m.Reader(owner,context);stage='anchor';scope=bootstrap(q)
        legacy,base,names,binding,required,extras,baseline,added,_,_=scope
        stage='selection';plan,_=scan(q,scope)
        require(plan==base and q.closed108 is None,'PENDING108_NOT_ALREADY_ACCEPTED')
        index,name=g.old.select(plan,names);require(index==108 and name==P108_NAME,'ONE_PENDING108_SOURCE_ONLY')
        out.update(prior_runtime_plan=plan,selected_test_index=index,selected_test_name=name,binding=binding,
            scope_budget=budget(required,baseline,added),scope_added_ten_pins=list(added.values()),
            extra_frame_controller_pins=list(extras.values()),current95_code_pins=q.codes,
            prequalification_failure_reviews=q.prequal_reviews,native107_epoch_root_pin=NATIVE107_ROOT,
            scope_fix_failure_review=q.scope_failure_review,epoch272_stop_review=q.epoch272_review,
            partial308_stop_review=q.partial308_review,pending108_product_review=q.pending108_review,
            preformal400_failure_review=q.preformal400_review,source021_CPU_stop_review=q.source021_review,review022_CPU_stop_review=q.review022_stop,
            original_executed_source_pins=list(pending108_scope(required).values()),current_source_transition_paths=[SELF,TEST])
        bound=m.m.m.review.bound_json
        if args.mode!='closing-review':
            rp=closing_pin(args.closing_review_pin,'review');reviewed=bound(q,rp)
            closing_contract(reviewed,scope,q.codes);out['closing_review_pin']=rp
        if args.mode=='closing-accept':
            sp=closing_pin(args.closing_source_pin,'source');source=bound(q,sp)
            closing_contract(source,scope,q.codes,reviewed,rp);require(source['closing_review_pin']==rp,'SAME_REVIEW_SOURCE_CHAIN')
            out['closing_source_pin']=sp
        stage='contract_tests'
        if args.mode=='closing-review':
            with context.scope('contract_tests'):
                out['runtime_contract_executions'],out['contract_checkpoint_statistics']=contracts(scope,q)
            out.update(own_queue_contract_tests_passed=COUNT,synthetic_following_queue_contract_tests_passed=COUNT)
        else:
            out.update(reused_light_contract_executions=EXECUTED,
                qualified_contract_checkpoint_statistics=reviewed['contract_checkpoint_statistics'])
        stage='final_fresh_preparation';q.finish()
        if args.mode=='closing-review':proposed=dict(state=C_REVIEW)
        elif args.mode=='closing-accept':
            proposed=dict(state=C_ACCEPT,runtime_plan=g.advance(legacy,base,names,108),
                accepted_exact_compound_case_count=1,semantic_body_capture_pass_count=1)
        else:
            early=m.early_review.EarlySourceCheckpoint(owner.checkpoint_io,owner)
            held=m.profile.InputLocks(p.c.ROOT,early,owner,context)
            require(held.checkpoint is early and held.api.pacer.rate==20 and held.open_pressure.resources is owner,
                'SOURCE_ONLY_ORIGINAL_NATIVE_OWNER')
            frame=p.frames.Frame(p.frames.Registry(),required,early,held=held)
            context.reader=p.frames.Counters(q.reader,frame.readers)
            out.update(independent_source_frame_attempted=True,early_source_native_and_byte_guard_connected=True)
            stage='source_frame_acquire';held.mark('before_acquire')
            with context.scope('metadata_hash'):frame.acquire()
            held.mark('after_acquire')
            def factory(checkpoint):
                return p.core.run.owned.OwnedReader(p.c.ROOT,checkpoint,samples=owner,protected={p.m.EXE['path']})
            for phase in ('metadata_hash','final_fresh_hash'):
                stage=phase
                with context.scope(phase):read_with_held_path_guards(frame,factory,owner.checkpoint_io,out['source_path_guard_diagnostics'])
            stage='source_commit';held.mark('before_release')
            out.update(source_frame=frame.commit(q.pending108_documents[1]),early_source_runtime_connection_verified=True,
                independent_source_frame_qualified=True);proposed=dict(state=C_SOURCE)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,KeyboardInterrupt) as error:
        out.update(error_code=p.b.run.original.closed_error(error),failure_diagnostic=m.m.diagnostic(error,stage));proposed=None
    finally:
        if frame is not None:
            try:
                if not frame.close():out['error_code']='SOURCE_FRAME_CLEANUP_FAILED';proposed=None
            except (ValueError,OSError):out['error_code']='SOURCE_FRAME_CLEANUP_FAILED';proposed=None
            out['source_frame']=frame.summary()
        if early is not None:out['early_source_checkpoint']=early.summary()
        if q is not None:
            q.close_entry();out.update(preparation_IO=q.summary(),bound_preparation_input_pins=list(q.reader.snapshots.values()))
            if hasattr(q,'contract_statistics'):out['contract_checkpoint_statistics']=q.contract_statistics
            if hasattr(q,'contract_failures'):out['contract_failures']=q.contract_failures
        out['metadata_observation']=g.observation.summary(owner)
        def validate(doc):closing_contract(doc,scope,q.codes,reviewed,rp,source,sp)
        m.complete_runtime(out,owner,proposed,validate)
        try:
            with destination.open('x',encoding='utf-8') as stream:
                output=m.PinningOutput(stream)
                writer=r.packed.dump if out['state'] in C_STATES else r.compact.dump
                def terminal():require(owner.done.is_set(),'NO_RESOURCE_RESTART')
                writer(out,output,checkpoint=terminal,indent=2)
                pin=dict(path=destination.relative_to(p.c.ROOT).as_posix(),bytes=output.written,sha256=output.digest.hexdigest())
        except (ValueError,OSError,TypeError):
            print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code='ROOT_SERIALIZATION_FAILED')));return 2
        print(json.dumps(dict(state=out['state'],receipt_pin=pin,resource_watcher_cleanup_confirmed=out.get('resource_watcher_cleanup_confirmed'),
            runtime_contract_executions=out['runtime_contract_executions'],error_code=out.get('error_code'),
            resource_stop_reason=out.get('resource_stop_reason'),actual_product_child_executed=False)),flush=True)
    return 0 if out['state'] in C_STATES else 2

def main(argv=None):
    global LAST_TERMINAL
    LAST_TERMINAL=None
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','light-review','actual','stop-review','closing-review','closing-source','closing-accept'),required=True)
    ap.add_argument('--run',type=int,required=True);ap.add_argument('--review-pin',action='append',default=[]);ap.add_argument('--stop-root-pin');ap.add_argument('--closing-review-pin');ap.add_argument('--closing-source-pin')
    args=ap.parse_args(argv);require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=999,'CWD_RUN')
    require((args.mode=='stop-review')==(args.stop_root_pin is not None),'STOP_TARGET_ONLY')
    if args.mode.startswith('closing-'):return closing_main(args)
    require(args.closing_review_pin is None and args.closing_source_pin is None,'CLOSING_PINS_ONLY_IN_CLOSING_MODES')
    destination=p.c.ROOT/f'{p.DIR}/p340-{args.mode if args.mode!="actual" else "admission"}-run{args.run:03}.v1.json'
    require(not destination.exists(),'FRESH_ONLY')
    context=g.observation.Context();owner=g.observation.Resources(context)
    q=meta=frame=early=capture=parent=proposed=None;scope=plan=body=target_result=None;writes=[];index=None
    stage='admission'
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),compound100_pin=COMPOUND,
        compound100_review_pin=COMPOUND_REVIEW,compound100_source_pin=COMPOUND_SOURCE,original93_pins=FROZEN93,
        startup_limits=STARTUP_LIMITS,stop_resume_policy=m.STOP_POLICY,original_successful_bodies_not_reexecuted=True,
        accepted_exact_product_body_count=0,runtime_contract_executions=0,contract_checkpoint_statistics=None,
        source_attempted=False,source_qualified=False,original_parent_capture_adapter_selected=False,
        diagnostic_parent_connection_selected=False,parent_return_status_recorded_before_after_parent_guard=False,
        receipt_serialization_policy=r.policy(),monotonic_binding_policy=m.review.policy())
    try:
        owner.admit();stage='reader_constructor';q=m.Reader(owner,context)
        stage='anchor';scope=bootstrap(q)
        legacy,base,names,binding,required,extras,baseline,added,latest,prior=scope
        stage='selection';target=pin_argument(args.stop_root_pin,'stop') if args.stop_root_pin else None
        plan,target_result=scan(q,scope,args.review_pin,target);index,name=g.old.select(plan,names)
        out.update(prior_runtime_plan=plan,selected_test_index=index,selected_test_name=name,binding=binding,
            scope_budget=budget(required,baseline,added),scope_added_ten_pins=list(added.values()),
            extra_frame_controller_pins=list(extras.values()),current95_code_pins=q.codes,
            prequalification_failure_reviews=q.prequal_reviews,native107_epoch_root_pin=NATIVE107_ROOT,
            scope_fix_failure_review=q.scope_failure_review,epoch272_stop_review=q.epoch272_review,partial308_stop_review=q.partial308_review,pending108_product_review=q.pending108_review,preformal400_failure_review=q.preformal400_review,source021_CPU_stop_review=q.source021_review,review022_CPU_stop_review=q.review022_stop)
        if args.mode=='light':
            stage='contract_tests'
            with context.scope('contract_tests'):out['runtime_contract_executions'],out['contract_checkpoint_statistics']=contracts(current_contract_scope(scope,plan),q)
            out.update(own_queue_contract_tests_passed=COUNT,synthetic_following_queue_contract_tests_passed=COUNT)
        elif args.mode in ('light-review','actual'):
            if args.mode=='light-review':
                lp,light=select_light(q,plan);out['reviewed_light_pin']=lp
            else:
                fp,fresh,lp,light=select_go(q,plan)
                out.update(independent_fresh_pin=fp,qualified_light_pin=lp)
            out.update(reused_light_contract_executions=EXECUTED,
                qualified_contract_checkpoint_statistics=light['contract_checkpoint_statistics'])
        stage='final_fresh_preparation'
        if args.mode=='actual':require_no_pending_product_reexecution(index);existing_body_guard(q,index);out['existing_body_replay_guard_verified']=True
        q.finish()
        if args.mode=='light':proposed=dict(state=LIGHT)
        elif args.mode=='light-review':proposed=dict(state=FRESH)
        elif args.mode=='stop-review':
            rp,root,at,classification,side,zero=target_result
            # review의 cursor는 실패가 발생한 바로 그 cursor. 나중 성공으로 cursor를 바꾸지 않는다.
            require(plan==at,'REVIEW_CURRENT_STOP_CURSOR')
            out.update(reviewed_root_pin=rp,reviewed_failure_classification=classification,reviewed_body_placeholder_pin=zero);proposed=dict(state=STOP_REVIEW)
        else:
            destination=p.c.ROOT/f'{p.DIR}/p340-case-{index:03}-run{args.run:03}.v1.json';require(not destination.exists(),'FRESH_CASE')
            body_path=p.c.ROOT/f'{p.DIR}/cases/p340-case-{index:03}-run{args.run:03}.json'
            require(not body_path.exists() and reserved_post_reads(q),'NEW_BODY_AND_RESERVED_POST_READS')
            early=m.early_review.EarlySourceCheckpoint(owner.checkpoint_io,owner)
            held=m.profile.InputLocks(p.c.ROOT,early,owner,context)
            require(held.checkpoint is early and held.api.pacer.rate==20 and held.open_pressure.resources is owner,'ORIGINAL_NATIVE20_OWNER')
            frame=p.frames.Frame(p.frames.Registry(),required,early,held=held)
            counter=p.frames.Counters(q.reader,frame.readers);context.reader=counter
            out.update(source_attempted=True,early_source_guard_connected=True,acquisition_phase_connection_selected=True,
                case_receipt_path=body_path.relative_to(p.c.ROOT).as_posix())
            stage='source_frame_acquire';held.mark('before_acquire')
            with context.scope('metadata_hash'):frame.acquire()
            held.mark('after_acquire')
            parent=m.connection.ParentConnection(frame,writes,index,name,binding);capture=parent.capture
            out.update(original_parent_capture_adapter_selected=isinstance(capture,m.m.m.support.candidate.Capture),
                diagnostic_parent_connection_selected=type(parent) is m.connection.ParentConnection and type(capture) is m.m.a.Capture,
                native_timing_connected=isinstance(held,m.connection.TimedInputLocks))
            stage='owned_parent';held.mark('before_parent');code=parent.run(body_path,context)
            m.record_return_before_original_guard(out,capture,code,held)
            if capture.pending:out['original_parent_STOP_captured_not_accepted']=True;raise ValueError('ORIGINAL_PARENT_STOP_DEFERRED_NOT_ACCEPTED')
            stage='post_reader_constructor';meta=m.review.construct(m.Reader,owner,context,counter)
            require(context.reader is counter and counter.metadata==[meta.reader],'ORIGINAL_MONOTONIC_COUNTER')
            out['aggregate_post_reader_connection_verified']=True
            body=meta.json(body_path.relative_to(p.c.ROOT).as_posix());pin=meta.reader.snapshots[body_path.relative_to(p.c.ROOT).as_posix()]
            require(code==0 and len(writes)==1,'ORIGINAL_PARENT_EXACT_ONCE')
            p.validate_parent(body,name,binding,required);m.m.job_contract(body);r.stats_contract(writes[0],pin);meta.finish()
            stage='source_frame_closing';held.mark('before_release')
            component=dict(schema_version=p.CLOSING_SCHEMA,state=p.PASS,**p.r.flags(),selected_test_name=name,binding=binding,
                case_receipt_pin=pin,metadata_IO=meta.summary(),source_frame=frame.commit(body),
                extra_frame_controller_pins=list(extras.values()),sealed_whole_before_anchor=p.b.BASE_CLOSE)
            out.update(case_receipt_pin=pin,closing_component=component,packed_parent_write_statistics=writes[0],
                source_qualified=True,actual_product_child_executed=body.get('actual_product_child_executed') is True)
            proposed=dict(state=PASS,runtime_plan=g.advance(legacy,plan,names,index),accepted_exact_product_body_count=1)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,KeyboardInterrupt,p.c.subprocess.SubprocessError) as error:
        out.update(error_code=p.b.run.original.closed_error(error),failure_diagnostic=m.m.diagnostic(error,stage));proposed=None
    finally:
        if frame is not None:
            try:
                if not frame.close():out['error_code']='SOURCE_FRAME_CLEANUP_FAILED';proposed=None
            except (ValueError,OSError):out['error_code']='SOURCE_FRAME_CLEANUP_FAILED';proposed=None
            out['terminal_source_frame']=frame.summary()
        if early is not None:out['early_source_checkpoint']=early.summary()
        for reader in (q,meta):
            if reader is not None:reader.close_entry()
        if q is not None:
            out.update(preparation_IO=q.summary(),bound_preparation_input_pins=list(q.reader.snapshots.values()))
            if hasattr(q,'contract_statistics'):out['contract_checkpoint_statistics']=q.contract_statistics
            if hasattr(q,'contract_failures'):out['contract_failures']=q.contract_failures
        if meta is not None:out['terminal_metadata_IO']=meta.summary()
        out['metadata_observation']=g.observation.summary(owner)
        def validate(doc):
            if doc['state']==LIGHT:light_contract(doc,plan,names,required,binding,extras,baseline,added,q.codes)
            elif doc['state']==FRESH:fresh_contract(doc,light,lp,plan,names,required,binding,extras,baseline,added,q.codes)
            elif doc['state']==STOP_REVIEW:review_contract(doc,rp,root,at,names,required,binding,extras,baseline,added,q.codes,side,zero)
            else:
                doc['closing_component'].update(resource_stop_reason=doc['resource_stop_reason'],
                    resource_watcher_cleanup_confirmed=doc['resource_watcher_cleanup_confirmed'])
                record(doc,body,pin,legacy,plan,names,required,binding,extras,baseline,added,q.codes)
        m.complete_runtime(out,owner,proposed,validate)
        if capture is not None and (capture.pending or capture.rejected):
            try:preserve(capture,owner,out,index,args.run)
            except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:out.update(state='FAILED_NOT_ACCEPTED',terminal_failure_write_error=p.b.run.original.closed_error(error))
        try:
            with destination.open('x',encoding='utf-8') as stream:
                output=m.PinningOutput(stream)
                writer=r.packed.dump if out['state'] in (PASS,LIGHT,FRESH,STOP_REVIEW) else r.compact.dump
                def terminal():require(owner.done.is_set(),'NO_WATCHER_RESTART')
                writer(out,output,checkpoint=terminal,indent=2)
                receipt_pin=dict(path=destination.relative_to(p.c.ROOT).as_posix(),bytes=output.written,sha256=output.digest.hexdigest())
        except (ValueError,OSError,TypeError):
            print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code='ROOT_SERIALIZATION_FAILED')));return 2
        LAST_TERMINAL=dict(state=out['state'],receipt_pin=receipt_pin,
            resource_watcher_cleanup_confirmed=out.get('resource_watcher_cleanup_confirmed'),
            runtime_contract_executions=out['runtime_contract_executions'],selected_test_index=out.get('selected_test_index'),
            error_code=out.get('error_code'),resource_stop_reason=out.get('resource_stop_reason'))
        print(json.dumps(LAST_TERMINAL),flush=True)
    return 0 if out['state'] in (PASS,LIGHT,FRESH,STOP_REVIEW) else 2

if __name__=='__main__':
    sys.modules.setdefault('resume_preserved106_queue_runtime',sys.modules[__name__])
    raise SystemExit(main())
