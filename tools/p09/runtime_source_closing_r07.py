"""P196 exact-case runtime source closing, NOT legacy whole1470 acceptance.

현재 실행 입력을 모두 두 번 fresh 읽는다. 과거67 EXE는 sealed reference이고
현재 whole/Gate 미검증으로 유지한다. 기존 성공/실패 파일과 v.plan은 변경하지 않는다.
"""
import argparse
import io
import json
import re
import sys
import time
import unittest
from unittest.mock import patch

import run_shared_resumable_r07_batch as b
import observe_shared_metadata_recheck as observation

c=b.c;v=b.v;core=b.core
SELF='tools/p09/runtime_source_closing_r07.py'
TEST='tools/p09/tests/test_runtime_source_closing_r07.py'
DIR='implementation/p09/evidence/runtime-r07'
SCHEMA='hwpx-agent.p09-r07-runtime-source-closing/v1'
PASS='PASS_EXACT_R07_RUNTIME_SOURCE_CLOSING_NOT_WHOLE_OR_GATE'
RAW_READER=b.run.pressure.PressureReader
RAW_PROGRESS=core.progress
CLOSE_NAME=re.compile(r'p196-case-([0-9]{3})-attempt-([0-9]{3})-close-([0-9]{2})\.v1\.json')


def require(ok,code):c.require(ok,'P196_'+code)


def flags():
    return dict(**core.flags(),whole1470_current_fresh_qualified=False,
        historical67_current_fresh_qualified=False,legacy_whole_acceptance_not_changed=True,
        historical_whole_gate_reconciliation_required=True,actual_product_child_executed=False)


def case_path(index,attempt):
    require(type(index) is int and 1<=index<=249 and type(attempt) is int and 1<=attempt<=999,'CASE_RANGE')
    return f'{core.DIR}/p190-case-{index:03}-attempt-{attempt:03}.json'


def destination(mode,index,attempt,number):
    require(type(number) is int and 1<=number<=99,'RUN_RANGE');case_path(index,attempt)
    require(mode in ('light','close','plan'),'MODE')
    return f'{DIR}/p196-case-{index:03}-attempt-{attempt:03}-{mode}-{number:02}.v1.json'


class Reader(RAW_READER):
    def __init__(self,owner,context):
        self.context=context;super().__init__(owner);context.reader=self.reader
    def pin(self,name):
        with self.context.scope('metadata_hash'):return super().pin(name)
    def json(self,name):
        with self.context.scope('metadata_read_parse'):return super().json(name)
    def text(self,name):
        with self.context.scope('document_read'):return super().text(name)
    def finish(self):
        with self.context.scope('final_fresh_hash'):return super().finish()


def controllers(q):
    return {name:q.pin(name) for name in (SELF,TEST)}


def case_scope(case,expected,names,exe,engine,controller):
    require(case.get('selected_test_names') and case['selected_test_names'][0] in names,'KNOWN_CASE')
    name=case['selected_test_names'][0];v.validate_case(case,name,v.identity(names,expected,exe))
    runtime,historical=b.OLD_RUNTIME_SCOPE(expected,exe)
    if 'supplemental_scheduler_input_pins' in case:
        required,_=b.source_extension(runtime,historical,engine)
        require(case['supplemental_scheduler_input_pins']==list(engine.values())
            and case['baseline_input_manifest_not_rewritten'] is True
            and case['serial_single_case_job'] is True,'SHARED_ORIGINAL_SCOPE')
    else:required=runtime
    extra=case.get('runtime_resume_controller_input_pins')
    if extra is not None:
        require(v.pins(extra)==controller and set(required).isdisjoint(controller),'BODY_CONTROLLER_SCOPE')
        required={**required,**controller}
    require(v.pins(case['source_freeze'])==required,'EXACT_RUNTIME_SOURCE_SET')
    require(len(case['owned_source_reader_passes'])==2 and all(row['read_passes']==len(required)
        and row['bytes_read']==sum(pin['bytes'] for pin in required.values())
        for row in case['owned_source_reader_passes']),'ORIGINAL_TWO_CASE_FRESH_PASSES')
    require(len(historical)==67 and not (set(required)&historical)
        and expected[exe['path']]==required[exe['path']], 'HISTORY_NOT_RUNTIME_CURRENT_EXE_RETAINED')
    return required,historical


def validate(doc,case,pin,expected,names,exe,engine,controller):
    required,historical=case_scope(case,expected,names,exe,engine,controller)
    require(doc['schema_version']==SCHEMA and doc['state']==PASS
        and doc['binding']==v.identity(names,expected,exe) and doc['case_receipt_pin']==pin
        and doc['selected_test_name']==case['selected_test_names'][0]
        and doc['pending_legacy_whole_closing_reference']==case['closing_id'],'RUNTIME_CLOSING_IDENTITY')
    require(doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['IO']['finished'] and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']
        and doc['IO']['maximum_scope_seconds']==600,'COMPLETE_GUARDED_CLOSING')
    require(v.pins(doc['runtime_source_before'])==v.pins(doc['runtime_source_after'])==required
        and v.pins(doc['closing_controller_before'])==v.pins(doc['closing_controller_after'])==controller,
        'EXACT_RUNTIME_AND_CONTROLLER_BOUNDARIES')
    bound=v.pins(doc['bound_input_pins'])
    require(all(bound.get(n)==p for n,p in {**required,**controller}.items())
        and not set(bound)&historical,'EVERY_RUNTIME_BYTE_FRESH_NO_HISTORY_CLAIM')
    require(doc['sealed_whole_before_anchor']==b.BASE_CLOSE and doc['historical_EXE_boundary_count']==67
        and all(doc[k] is False for k in ('whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
            'actual_product_child_executed','full249_current_qualified','signed16_current_qualified','product_complete',
            'PC_freeze_resolved')) and doc['legacy_whole_acceptance_not_changed'] is True
        and doc['historical_whole_gate_reconciliation_required'] is True
        and doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN','NO_WHOLE_OR_GATE_PROMOTION')


def runtime_plan(legacy,names,closed_names,passed_names):
    accepted=set(legacy['accepted_test_names'])
    require(len(accepted)==legacy['accepted_individual_cases'] and len(closed_names)==len(set(closed_names))
        and not accepted&set(closed_names) and set(closed_names)<=set(passed_names)<=set(names),'DISTINCT_RUNTIME_NAMES')
    qualified=accepted|set(closed_names);unclosed=set(passed_names)-qualified
    pending=[i for i,name in enumerate(names,1) if name not in qualified]
    heavy=[i for i in pending if names[i-1].startswith(v.CORPUS_PREFIX)]
    runnable=[i for i in pending if i not in heavy and names[i-1] not in unclosed]
    return dict(scope='INDIVIDUAL_RUNTIME_PROGRESS_NOT_WHOLE_OR_GATE',
        legacy_whole_accepted_individual_cases=legacy['accepted_individual_cases'],
        legacy_whole_pending_successful_candidates=legacy['successful_candidates_requiring_separate_closing'],
        runtime_source_qualified_individual_cases=len(qualified),runtime_remaining_individual_cases=len(pending),
        runtime_remaining_regular_cases=len(pending)-len(heavy),runtime_remaining_corpus_cases=len(heavy),
        runtime_successful_candidates_requiring_closing=len(unclosed),
        next_runtime_index=runnable[0] if runnable else None,runtime_qualified_test_names=sorted(qualified),
        historical_whole_gate_reconciliation_required=True,whole1470_current_fresh_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,P09_gate='OPEN')


def progress(q,expected,names,exe,engine,controller):
    legacy=RAW_PROGRESS(q,names,expected,exe)
    cases=sorted((c.ROOT/core.DIR).glob('p190-case-*-attempt-*.json'))
    require(len(cases)<=4096,'BOUNDED_CASE_INVENTORY');passed={}
    for file in cases:
        name=file.relative_to(c.ROOT).as_posix();case=q.json(name)
        if case['state']==v.CASE_PASS:
            case_scope(case,expected,names,exe,engine,controller)
            passed[name]=(case,q.reader.snapshots[name])
    files=sorted((c.ROOT/DIR).glob('p196-case-*-attempt-*-close-*.v1.json'))
    require(len(files)<=4096,'BOUNDED_RUNTIME_CLOSING_INVENTORY');closed=[];pins=[]
    for file in files:
        match=CLOSE_NAME.fullmatch(file.name);require(match is not None,'CLOSING_FILENAME')
        name=file.relative_to(c.ROOT).as_posix();doc=q.json(name)
        if doc['state']!=PASS:
            require(doc['state']=='FAILED_NOT_ACCEPTED','UNKNOWN_CLOSING_STATE');continue
        source=case_path(int(match[1]),int(match[2]));require(source in passed,'MATCH_PASSED_CASE')
        case,pin=passed[source];validate(doc,case,pin,expected,names,exe,engine,controller)
        closed.append(case['selected_test_names'][0]);pins.append(q.reader.snapshots[name])
    return legacy,runtime_plan(legacy,names,closed,[doc['selected_test_names'][0] for doc,_ in passed.values()]),pins


def contracts():
    out=b.contracts();out.update(observation.new_contracts())
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_runtime_source_closing_r07')
    with patch('subprocess.Popen',side_effect=AssertionError('P196_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P196_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P196_NO_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(checked.wasSuccessful() and checked.testsRun==14 and not checked.skipped,'CONTRACT14')
    out['runtime_source_closing_contract_tests_passed']=14;return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','close','plan'),required=True)
    ap.add_argument('--run',type=int,required=True);ap.add_argument('--index',type=int,default=4)
    ap.add_argument('--attempt',type=int,default=1);args=ap.parse_args()
    require(c.Path.cwd().resolve()==c.ROOT,'CWD')
    target=b.s.scoped_path(destination(args.mode,args.index,args.attempt,args.run),fresh=True)
    context=observation.Context();owner=observation.Resources(context);q=None;started=time.monotonic()
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**flags())
    try:
        owner.admit();q=Reader(owner,context);controller=controllers(q)
        for name in (observation.SELF,observation.TEST):q.pin(name)
        out.update(contracts());expected,names,exe=b.baseline(q);engine={n:q.pin(n) for n in (b.SELF,b.TEST)}
        if args.mode=='close':
            source=case_path(args.index,args.attempt);case=q.json(source);pin=q.reader.snapshots[source]
            required,historical=case_scope(case,expected,names,exe,engine,controller)
            legacy=RAW_PROGRESS(q,names,expected,exe)
            require(names[args.index-1] not in legacy['accepted_test_names'],'NO_REPEAT_LEGACY_ACCEPTED_CASE')
            require(case['selected_test_names']==[names[args.index-1]],'EXACT_REQUESTED_CASE')
            q.reader.protected=frozenset({exe['path']})
            for name,expected_pin in required.items():require(q.pin(name)==expected_pin,'FRESH_EVERY_RUNTIME_INPUT')
            q.finish();out.update(state=PASS,binding=v.identity(names,expected,exe),case_receipt_pin=pin,
                selected_test_name=names[args.index-1],pending_legacy_whole_closing_reference=case['closing_id'],
                runtime_source_before=list(required.values()),runtime_source_after=[q.reader.snapshots[n] for n in required],
                closing_controller_before=list(controller.values()),closing_controller_after=[q.reader.snapshots[n] for n in controller],
                historical_EXE_boundary_count=len(historical),sealed_whole_before_anchor=b.BASE_CLOSE)
            # 検証にはfinallyと同じcleanup/IO/pin表現を用いる（実際の完了状態のみ）。
        else:
            legacy,plan,pins=progress(q,expected,names,exe,engine,controller);q.finish()
            out.update(state='PASS_RUNTIME_SOURCE_CLOSING_CONTRACTS_AND_PLAN_ONLY_NOT_WHOLE_OR_GATE',
                legacy_plan=legacy,runtime_plan=plan,runtime_closing_receipt_pins=pins)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.run.original.closed_error(error)
    finally:
        b.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
        if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        if out['state']==PASS:
            try:validate(out,case,pin,expected,names,exe,engine,controller)
            except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
                out.update(state='FAILED_NOT_ACCEPTED',error_code=b.run.original.closed_error(error))
        out.update(wall_seconds=round(time.monotonic()-started,4),metadata_observation=observation.summary(owner))
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','runtime_source_closing_contract_tests_passed',
            'error_code','resource_stop_reason','wall_seconds')}),flush=True)
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':
    sys.modules.setdefault('runtime_source_closing_r07',sys.modules[__name__])
    raise SystemExit(main())
