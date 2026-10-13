"""P340: 보존106 compound100에서 시작하는 고정 실행 큐.
원93 코드/제품 증거 보존. 새2 코드 포함 full1658. 통과 제품 재실행/자동 retry 없음.
원 감시기, 두 byte, Native identity, Job, pacing, cleanup은 기존 구현을 그대로 사용한다.
"""
import complete_preserved106_source as x
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
SCHEMA='hwpx-agent.p09-preserved106-fixed-runtime-queue/v2'
PASS='PASS_EXACT_PRESERVED106_NEXT_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT='PASS_PRESERVED106_NEXT_QUEUE_NOT_ACTUAL_OR_GATE'
FRESH='PASS_PRESERVED106_DISTINCT_FRESH_NOT_NATIVE_OR_PRODUCT'
STOP_REVIEW='PASS_PRESERVED106_PRE_PRODUCT_STOP_REVIEW_NOT_GO'
N=1658;DIRECTORIES=308
COUNT=78
EXECUTED=2*COUNT
FILE=re.compile(r'p340-case-([0-9]{3})-run([0-9]{3})\.v1\.json')
STARTUP_LIMITS=m.STARTUP_LIMITS
LAST_TERMINAL=None

def require(ok,code):m.require(ok,'PRESERVED106_QUEUE_'+code)

PREQUAL_FAILURE=dict(path=p.DIR+'/p340-light-run001.v1.json',bytes=132457,sha256='98514e8cf9b405089da66f76a36fc887a69906d20b2bf89c59047bba2aa85b94')
PREQUAL_CODE=[
 dict(path=SELF,bytes=30583,sha256='1ab74777e0a65aee2d175ece582794a3be2a329153df64c08eb8255b2f5c7249'),
 dict(path=TEST,bytes=15621,sha256='b3f25091c526915e3a18b013ca05b93d7c5e111cd3cdefe9b6939178c11f0658')]
PREQUAL_ARCHIVES=[dict(z,path='implementation/p09/evidence/p340-preformal140-code/'+z['path']) for z in PREQUAL_CODE]

def prequal_summary():
    return dict(original_failure_pin=PREQUAL_FAILURE,original_FAILED_preserved=True,
        actual_contracts_started_and_stopped=70,partial_runner_calls=1,
        contract_qualification_pass=False,actual_Native_or_product_executed=False,
        cleanup_confirmed=True,missing_optional_error_field_found=True,
        fix_missing_optional_error_field_does_not_change_guard_or_product_acceptance=True)

def prequal_review(doc):
    require(doc['schema_version']=='hwpx-agent.p09-preserved106-fixed-runtime-queue/v1'
        and doc['state']=='FAILED_NOT_ACCEPTED'
        and doc['error_code']=='P208_POST_STOP_RUNTIME_DIAGNOSTIC_RUNTIME_REVIEWED_STOP_QUEUE_RUNTIME_PRESERVED106_QUEUE_ALL_CURRENT_AND_FOLLOWING_CONTRACTS'
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['failure_diagnostic']['stage']=='contract_tests'
        and doc['current95_code_pins']==FROZEN93+PREQUAL_CODE and doc['original93_pins']==FROZEN93
        and doc['startup_limits']==STARTUP_LIMITS and doc['compound100_pin']==COMPOUND
        and doc['prior_runtime_plan']['runtime_source_qualified_individual_cases']==100
        and doc['selected_test_index']==107 and doc['runtime_contract_executions']==0
        and doc['accepted_exact_product_body_count']==0 and doc['source_attempted'] is False
        and doc['actual_product_child_executed'] is False and doc['source_qualified'] is False
        and doc['original_parent_capture_adapter_selected'] is False and doc['diagnostic_parent_connection_selected'] is False
        and doc.get('terminal_source_frame') is None and doc.get('case_receipt_pin') is None
        and doc.get('terminal_parent_failure_sidecar_pin') is None and 'runtime_plan' not in doc,
        'IMMUTABLE_PREFORMAL_FAILURE_NEVER_ACCEPTED_OR_PRODUCT')
    row=doc['contract_checkpoint_statistics'];io_=doc['preparation_IO']
    require(row['started_tests']==row['stopped_tests']==row['successful_before_test_checks']==row['successful_after_test_checks']==70
        and row['runner_calls']==row['returned_runner_calls']==row['successful_before_runner_checks']==row['successful_after_runner_checks']==1
        and row['original_unittest_results_preserved'] is True and row['original_guard_or_test_coverage_relaxed'] is False
        and row['new_sampler_or_thread_or_sleep_started'] is False
        and len(doc['contract_failures'])==4 and io_['bound_inputs']==io_['read_passes']==147
        and io_['final_fresh_hashes']==0 and io_['finished'] is False,'PARTIAL_CURRENT_RUNNER_NOT140_PASS')
    return prequal_summary()

def budget(required,baseline,added):
    require(len(required)==N and len(baseline)==1644 and len(added)==14
        and not set(baseline)&set(added) and required=={**baseline,**added}
        and baseline[p.m.EXE['path']]==p.m.EXE and sum(z['bytes'] for z in baseline.values())==120516712
        and sum(z['bytes'] for z in added.values())<=1048576,'ALL1644_PLUS14_NOT_SUBSET')
    directories={PurePosixPath('.')}
    for name in required:directories.update(PurePosixPath(name).parents)
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
    for logical,archive in zip(PREQUAL_CODE,PREQUAL_ARCHIVES):
        require(q.pin(archive['path'])==archive,'EXACT_PREFORMAL_CODE_ARCHIVE')
    q.prequal_document=bound(q,PREQUAL_FAILURE);q.prequal_review=prequal_review(q.prequal_document)
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
    require(doc['schema_version']==SCHEMA and doc.get('error_code') is None and doc['resource_stop_reason'] is None
        and doc['resource_watcher_cleanup_confirmed'] is True and doc['compound100_pin']==COMPOUND
        and doc['compound100_review_pin']==COMPOUND_REVIEW and doc['compound100_source_pin']==COMPOUND_SOURCE
        and doc['original93_pins']==FROZEN93 and doc['current95_code_pins']==codes
        and doc['startup_limits']==STARTUP_LIMITS and doc['stop_resume_policy']==m.STOP_POLICY
        and doc['original_successful_bodies_not_reexecuted'] is True and doc['prior_runtime_plan']==plan
        and doc['selected_test_index']==index and doc['selected_test_name']==name and doc['binding']==binding
        and doc['prequalification_failure_review']==prequal_summary()
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
        and doc['source_attempted'] is True and doc['source_qualified'] is True
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

def review_contract(doc,rp,root,plan,names,required,binding,extras,baseline,added,codes,sidecar=None):
    common(doc,plan,names,required,binding,extras,baseline,added,codes)
    classification=stopped(root,plan,required,binding,extras,baseline,added,names,sidecar)
    require(doc['state']==STOP_REVIEW and doc['reviewed_root_pin']==rp
        and doc['reviewed_failure_classification']==classification and doc['runtime_contract_executions']==0
        and doc['source_attempted'] is False and doc['actual_product_child_executed'] is False
        and doc['accepted_exact_product_body_count']==0,'REVIEW_NOT_GO_OR_ADVANCE')

def scan(q,scope,approved_pins=(),target=None):
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
    lights=[];freshes=[]
    for path in support:
        name=path.relative_to(p.c.ROOT).as_posix()
        if name==PREQUAL_FAILURE['path']:
            require(q.reader.snapshots[name]==PREQUAL_FAILURE and q.prequal_review==prequal_summary(),'ONLY_EXACT_INDEPENDENT_REVIEWED_PREFORMAL_FAILURE')
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
        if target is not None and rp==target:
            require(target_result is None,'EXACT_SINGLE_STOP_TARGET')
            target_result=(rp,d,at,stopped(d,at,required,binding,extras,baseline,added,names,side),side);continue
        require(name in reviews,'UNREVIEWED_STOP_BLOCKS_GO')
        ap,reviewed=reviews[name];review_contract(reviewed,rp,d,at,names,required,binding,extras,baseline,added,codes,side);used.add(name)
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
                with patch.object(t,'FIXTURES',scope),patch.object(t,'FOLLOWING',following),patch.object(t,'TEMPLATE',None),patch.object(t,'PREQUALIFICATION',q.prequal_document):
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

def main(argv=None):
    global LAST_TERMINAL
    LAST_TERMINAL=None
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','light-review','actual','stop-review'),required=True)
    ap.add_argument('--run',type=int,required=True);ap.add_argument('--review-pin',action='append',default=[]);ap.add_argument('--stop-root-pin')
    args=ap.parse_args(argv);require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=999,'CWD_RUN')
    require((args.mode=='stop-review')==(args.stop_root_pin is not None),'STOP_TARGET_ONLY')
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
            prequalification_failure_review=q.prequal_review)
        if args.mode=='light':
            stage='contract_tests'
            with context.scope('contract_tests'):out['runtime_contract_executions'],out['contract_checkpoint_statistics']=contracts(scope,q)
            out.update(own_queue_contract_tests_passed=COUNT,synthetic_following_queue_contract_tests_passed=COUNT)
        elif args.mode in ('light-review','actual'):
            if args.mode=='light-review':
                lp,light=select_light(q,plan);out['reviewed_light_pin']=lp
            else:
                fp,fresh,lp,light=select_go(q,plan)
                out.update(independent_fresh_pin=fp,qualified_light_pin=lp)
            out.update(reused_light_contract_executions=EXECUTED,
                qualified_contract_checkpoint_statistics=light['contract_checkpoint_statistics'])
        stage='final_fresh_preparation';q.finish()
        if args.mode=='light':proposed=dict(state=LIGHT)
        elif args.mode=='light-review':proposed=dict(state=FRESH)
        elif args.mode=='stop-review':
            rp,root,at,classification,side=target_result
            # review의 cursor는 실패가 발생한 바로 그 cursor. 나중 성공으로 cursor를 바꾸지 않는다.
            require(plan==at,'REVIEW_CURRENT_STOP_CURSOR')
            out.update(reviewed_root_pin=rp,reviewed_failure_classification=classification);proposed=dict(state=STOP_REVIEW)
        else:
            destination=p.c.ROOT/f'{p.DIR}/p340-case-{index:03}-run{args.run:03}.v1.json';require(not destination.exists(),'FRESH_CASE')
            body_path=p.c.ROOT/f'{p.DIR}/cases/p340-case-{index:03}-run{args.run:03}.json'
            require(not body_path.exists() and q.shared_budget['read_calls']<=m.m.META_READ_LIMIT-2,'NEW_BODY_AND_RESERVED_POST_READS')
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
            elif doc['state']==STOP_REVIEW:review_contract(doc,rp,root,at,names,required,binding,extras,baseline,added,q.codes,side)
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
