"""P199: bounded-memory planning; same full case/closing validators and fresh IO.

과거 모든 case의 samples/source payload를 메모리에 동시에 보관하지 않는다.
현재 pin이 같은 기존 성공을 재사용하고 closing마다 원 case를 다시 읽어 검증한다.
P198는 수정하지 않는다. 새 dispatcher 두 입력도 실제 body의 전후 읽기에 포함한다.
"""
import io
import sys
import unittest
from unittest.mock import patch

import run_runtime_resumable_r07_case as p

r=p.r;b=p.b;c=p.c;v=p.v
SELF='tools/p09/stream_runtime_resume_progress.py'
TEST='tools/p09/tests/test_stream_runtime_resume_progress.py'
ORIGINAL_CONTROLLERS=p.CONTROLLERS
CONTROLLERS=(*ORIGINAL_CONTROLLERS,SELF,TEST)
RAW_CONTRACTS=p.contracts


def require(ok,code):c.require(ok,'P199_'+code)


def case_controller(case,current):
    declared=v.pins(case['runtime_resume_controller_input_pins'])
    require(set(declared) in (set(ORIGINAL_CONTROLLERS),set(CONTROLLERS)), 'CLOSED_CONTROLLER_GENERATIONS')
    require(all(current.get(name)==pin for name,pin in declared.items()),'UNCHANGED_EXECUTION_CONTROLLER_PINS')
    return declared


def compact_case(case,pin,expected,names,exe,engine,current):
    control=case_controller(case,current)
    r.case_scope(case,expected,names,exe,engine,control)
    # 이름/pin/키집합만 남긴다. samples/source list/doc 자체는 보관하지 않는다.
    return case['selected_test_names'][0],pin,frozenset(control)


def combine(legacy,base,names,closed,passed):
    original=set(base['runtime_qualified_test_names'])
    require(not original&set(closed),'NO_DUPLICATE_ORIGINAL_SUCCESS')
    synthetic=dict(legacy,accepted_test_names=base['runtime_qualified_test_names'],accepted_individual_cases=len(original))
    all_passed=list(original|set(passed));plan=r.runtime_plan(synthetic,names,closed,all_passed)
    plan['legacy_whole_accepted_individual_cases']=legacy['accepted_individual_cases']
    plan['legacy_whole_pending_successful_candidates']=legacy['successful_candidates_requiring_separate_closing']
    plan['prior_runtime_qualified_cases']=len(original)
    plan['all_successful_bodies_pending_whole_reconciliation']=len(all_passed)-legacy['accepted_individual_cases']
    return plan


def progress(q,expected,names,exe,engine,controller):
    legacy,base,pins=r.progress(q,expected,names,exe,engine,{n:controller[n] for n in (r.SELF,r.TEST)})
    files=sorted((c.ROOT/p.DIR).glob('p190-case-*-attempt-*.json'))
    require(len(files)<=4096,'BOUNDED_CASES');passed={};attempts={};seen=set()
    for file in files:
        match=p.CASE_FILE.fullmatch(file.name);require(match is not None,'CASE_FILENAME')
        index,attempt=map(int,match.groups());r.case_path(index,attempt)
        require((index,attempt) not in seen,'DUPLICATE_ATTEMPT');seen.add((index,attempt))
        attempts[index]=max(attempts.get(index,0),attempt)
        name=file.relative_to(c.ROOT).as_posix();doc=q.json(name)
        require(doc['binding']==v.identity(names,expected,exe) and doc['schema_version']==v.SCHEMA
            and doc['selected_test_names']==[names[index-1]],'CASE_IDENTITY')
        if doc['state']==v.CASE_PASS:
            passed[name]=compact_case(doc,q.reader.snapshots[name],expected,names,exe,engine,controller)
        else:require(doc['state'] in ('STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED','FAILED_NOT_ACCEPTED'),'CASE_STATE')
        del doc
    closed=[];closings=sorted((c.ROOT/p.META).glob('p198-case-*-attempt-*-close-*.v1.json'))
    require(len(closings)<=4096,'BOUNDED_CLOSINGS')
    for file in closings:
        match=p.CLOSE_FILE.fullmatch(file.name);require(match is not None,'CLOSING_FILENAME')
        name=file.relative_to(c.ROOT).as_posix();doc=q.json(name)
        if doc['state']!=r.PASS:
            require(doc['state']=='FAILED_NOT_ACCEPTED','CLOSING_STATE');del doc;continue
        source=f'{p.DIR}/p190-case-{int(match[1]):03}-attempt-{int(match[2]):03}.json'
        require(source in passed,'CLOSING_HAS_PASSED_CASE')
        public_name,pin,keys=passed[source]
        # 같은 receipt의 모든 byte를 다시 읽고 reader의 bind 비교로 변경을 거부한다.
        case=q.json(source);require(q.reader.snapshots[source]==pin,'RELOADED_CASE_PIN')
        control={n:controller[n] for n in keys}
        r.validate(doc,case,pin,expected,names,exe,engine,control)
        closed.append(public_name);pins.append(q.reader.snapshots[name])
        del case,doc
    plan=combine(legacy,base,names,closed,[record[0] for record in passed.values()])
    return legacy,plan,pins,attempts


def contracts():
    # 기존202 계약은 원8-controller 역할로 검증한다. 실제 새 입력은10개다.
    with patch.object(p,'CONTROLLERS',ORIGINAL_CONTROLLERS):result=RAW_CONTRACTS()
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_stream_runtime_resume_progress')
    with patch('subprocess.Popen',side_effect=AssertionError('P199_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P199_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P199_NO_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(checked.wasSuccessful() and checked.testsRun==10 and not checked.skipped,'CONTRACT10')
    result['streaming_progress_contract_tests_passed']=10;return result


def main():
    with patch.object(p,'progress',progress),patch.object(p,'CONTROLLERS',CONTROLLERS),patch.object(p,'contracts',contracts):
        return p.main()


if __name__=='__main__':
    sys.modules.setdefault('stream_runtime_resume_progress',sys.modules[__name__])
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,c.subprocess.SubprocessError) as error:
        print(p.json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=b.run.original.closed_error(error))))
        raise SystemExit(2) from None
