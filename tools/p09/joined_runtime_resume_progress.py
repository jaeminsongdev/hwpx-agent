"""P201: join a single case and its closings; retain all fresh byte checks.

성공 receipt를 JSON으로 두 번 해석하지 않는다. 첫 원본과 closing을 함께
검증하되 기존 두 번째 읽기는 fresh pin으로 수행한다. 원 byte 변경은 거부한다.
기존 8/10-controller와 새 12-controller를 구분하며 원 validator는 그대로다.
"""
import io
import sys
import unittest
from unittest.mock import patch

import stream_runtime_resume_progress as s

p=s.p;r=s.r;b=s.b;c=s.c;v=s.v
SELF='tools/p09/joined_runtime_resume_progress.py'
TEST='tools/p09/tests/test_joined_runtime_resume_progress.py'
CONTROLLERS=(*s.CONTROLLERS,SELF,TEST)
ACCOUNTING={}


def require(ok,code):c.require(ok,'P201_'+code)


def case_controller(case,current):
    declared=v.pins(case['runtime_resume_controller_input_pins'])
    require(set(declared) in (set(s.ORIGINAL_CONTROLLERS),set(s.CONTROLLERS),set(CONTROLLERS)),
        'CLOSED_CONTROLLER_GENERATIONS')
    require(all(current.get(name)==pin for name,pin in declared.items()),'UNCHANGED_EXECUTION_CONTROLLER_PINS')
    return declared


def verify_new_cases(q,expected,names,exe,engine,controller,files,closings):
    require(len(files)<=4096 and len(closings)<=4096,'BOUNDED_INVENTORIES')
    by_case={};visited=set();attempts={};seen=set();passed=[];closed=[];pins=[]
    metrics=dict(case_JSON_parses=0,closing_JSON_parses=0,retained_fresh_case_rechecks=0,
        redundant_case_JSON_parses_avoided=0,case_payloads_retained_at_once_limit=1,
        original_full_case_and_closing_validators_retained=True,
        original_second_case_full_byte_read_retained=True,final_fresh_hash_pass_retained=True,
        cross_run_parsed_or_raw_payload_cache_used=False)
    for file in closings:
        match=p.CLOSE_FILE.fullmatch(file.name);require(match is not None,'CLOSING_FILENAME')
        index,attempt=map(int,(match[1],match[2]));r.case_path(index,attempt)
        source=f'{p.DIR}/p190-case-{index:03}-attempt-{attempt:03}.json'
        by_case.setdefault(source,[]).append(file)
    for file in files:
        match=p.CASE_FILE.fullmatch(file.name);require(match is not None,'CASE_FILENAME')
        index,attempt=map(int,match.groups());r.case_path(index,attempt)
        require((index,attempt) not in seen,'DUPLICATE_ATTEMPT');seen.add((index,attempt))
        attempts[index]=max(attempts.get(index,0),attempt)
        source=file.relative_to(c.ROOT).as_posix();case=q.json(source);metrics['case_JSON_parses']+=1
        require(case['binding']==v.identity(names,expected,exe) and case['schema_version']==v.SCHEMA
            and case['selected_test_names']==[names[index-1]],'CASE_IDENTITY')
        accepted=case['state']==v.CASE_PASS
        if accepted:
            control=case_controller(case,controller)
            r.case_scope(case,expected,names,exe,engine,control)
            pin=q.reader.snapshots[source];passed.append(case['selected_test_names'][0])
        else:
            require(case['state'] in ('STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED','FAILED_NOT_ACCEPTED'),'CASE_STATE')
        for closing_file in by_case.get(source,()):
            name=closing_file.relative_to(c.ROOT).as_posix();doc=q.json(name)
            metrics['closing_JSON_parses']+=1;visited.add(name)
            if doc['state']==r.PASS:
                require(accepted,'CLOSING_HAS_PASSED_CASE')
                # 기존 재읽기와 동일한 전체 byte hash/변경 거부; JSON 해석만 중복하지 않는다.
                require(q.pin(source)==pin,'RECHECKED_CASE_PIN')
                metrics['retained_fresh_case_rechecks']+=1
                metrics['redundant_case_JSON_parses_avoided']+=1
                r.validate(doc,case,pin,expected,names,exe,engine,control)
                closed.append(case['selected_test_names'][0]);pins.append(q.reader.snapshots[name])
            else:require(doc['state']=='FAILED_NOT_ACCEPTED','CLOSING_STATE')
            del doc
        del case
    for file in closings:
        name=file.relative_to(c.ROOT).as_posix()
        if name not in visited:
            doc=q.json(name);metrics['closing_JSON_parses']+=1
            require(doc['state']=='FAILED_NOT_ACCEPTED','ORPHAN_CLOSING_NOT_ACCEPTED');del doc
    return closed,passed,pins,attempts,metrics


def progress(q,expected,names,exe,engine,controller):
    ACCOUNTING.clear()
    legacy,base,pins=r.progress(q,expected,names,exe,engine,{n:controller[n] for n in (r.SELF,r.TEST)})
    files=sorted((c.ROOT/p.DIR).glob('p190-case-*-attempt-*.json'))
    closings=sorted((c.ROOT/p.META).glob('p198-case-*-attempt-*-close-*.v1.json'))
    closed,passed,new_pins,attempts,metrics=verify_new_cases(q,expected,names,exe,engine,controller,files,closings)
    plan=s.combine(legacy,base,names,closed,passed);pins.extend(new_pins);ACCOUNTING.update(metrics)
    return legacy,plan,pins,attempts


def contracts():
    result=s.contracts();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_joined_runtime_resume_progress')
    with patch('subprocess.Popen',side_effect=AssertionError('P201_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P201_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P201_NO_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(checked.wasSuccessful() and checked.testsRun==12 and not checked.skipped,'CONTRACT12')
    result['joined_progress_contract_tests_passed']=12;return result


def main():
    original_dump=p.RAW_DUMP
    def write(doc,stream,**kw):
        doc['joined_progress_parse_accounting']=dict(ACCOUNTING)
        doc['joined_progress_dispatcher_input_paths']=[SELF,TEST]
        return original_dump(doc,stream,**kw)
    with patch.object(p,'progress',progress),patch.object(p,'CONTROLLERS',CONTROLLERS), \
            patch.object(p,'contracts',contracts),patch.object(p,'RAW_DUMP',write):
        return p.main()


if __name__=='__main__':
    sys.modules.setdefault('joined_runtime_resume_progress',sys.modules[__name__])
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,c.subprocess.SubprocessError) as error:
        print(p.json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=b.run.original.closed_error(error))))
        raise SystemExit(2) from None
