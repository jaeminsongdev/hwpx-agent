"""P205: 기존 exact-one 감독에 source-only 경량 worker를 연결한다.

원 입력 전후 전체 fresh 확인, GO/Job/guard/capture/cleanup은 그대로 유지한다.
과거 성공 body를 재실행하지 않고 새 controller 세대만 명시적으로 추가한다.
"""
import io
import re
import sys
import unittest
from unittest.mock import patch
import joined_runtime_resume_progress as j
import minimal_r07_worker as m

p=j.p;r=j.r;b=j.b;c=j.c;v=j.v
SELF='tools/p09/run_minimal_runtime_r07_case.py'
TEST='tools/p09/tests/test_minimal_runtime_r07_case.py'
CONTROLLERS=(*j.CONTROLLERS,m.SELF,m.TEST,SELF,TEST)
ORIGINAL_RUN=c.run
ORIGINAL_CASE_CONTROLLER=j.case_controller
WORKER_PIN=dict(path=m.SELF,bytes=5738,sha256='ef38375738d19d6075bbe0b303895e92416354926d272840bd5c98b5f30cab0b')
WORKER_TEST_PIN=dict(path=m.TEST,bytes=5059,sha256='bb12056fcf3d3d61d3175f38cfbcad405cd668bd4d084536e631ff63d594e0e7')


def require(ok,code):c.require(ok,'P205_'+code)


def worker_task(original):
    match=re.fullmatch(r'p191-r07-case-([0-9]{3})-tests',original)
    require(match is not None,'ORIGINAL_EXACT_TASK')
    index=int(match[1]);require(1<=index<=249,'TASK_RANGE')
    return f'p204-r07-case-{index:03}-tests'


def owned_run(task,receipt,maximum_seconds):
    require(type(maximum_seconds) is int and maximum_seconds==1200,'UNCHANGED_DEADLINE')
    require(c.TASKS=={task:m.TASK_ARGS} and c.TARGET==m.TARGET,'ORIGINAL_PARENT_TASK_TARGET')
    selected=worker_task(task)
    # 실제 c.run이 생성·Job 할당·GO 전송을 수행한다. 자식 소속은 m.worker의 원 c.worker가 확인한다.
    with patch.object(c,'__file__',str(c.ROOT/m.SELF)),patch.object(c,'TASKS',{selected:m.TASK_ARGS}):
        return ORIGINAL_RUN(selected,receipt,maximum_seconds)


def validate_bridge(case,controller):
    require(set(controller)==set(CONTROLLERS),'BRIDGE_CONTROLLER_SET')
    require(controller[m.SELF]==WORKER_PIN and controller[m.TEST]==WORKER_TEST_PIN,'P204_TESTED_WORKER_UNCHANGED')
    task=case['original_parent_task_before_minimal_worker'];selected=worker_task(task)
    require(case['task']==selected and case['minimal_owned_worker_path']==m.SELF
        and case['minimal_worker_source_only_import_connected'] is True
        and case['original_parent_guard_and_full_runtime_fresh_scope_retained'] is True,
        'ACTUAL_MINIMAL_WORKER_CONNECTION')
    if case['state']==v.CASE_PASS:
        require(case['actual_job_membership_checked'] and case['owned_limits_verified']
            and case['job_assigned'] and case['writer_authorized'] and case['cleanup_confirmed']
            and case['owned_tree_empty'],'ACTUAL_ORIGINAL_JOB_GO_AND_CLEANUP')


def case_controller(case,current):
    declared=v.pins(case['runtime_resume_controller_input_pins'])
    if set(declared)!=set(CONTROLLERS):return ORIGINAL_CASE_CONTROLLER(case,current)
    require(all(current.get(name)==pin for name,pin in declared.items()),'UNCHANGED_BRIDGE_CONTROLLER_PINS')
    validate_bridge(case,declared);return declared


def progress(q,expected,names,exe,engine,controller):
    require(controller[m.SELF]==WORKER_PIN and controller[m.TEST]==WORKER_TEST_PIN,'TESTED_WORKER_CURRENT_PIN')
    require(m.EXE==exe and m.PARENT==b.run.PARENT and m.TARGET==b.core.run.b.TARGET
        and m.TASK_ARGS==b.core.run.original.TASK_ARGS,'ORIGINAL_ARGUMENT_EXE_PARITY')
    require(all(expected[name]==dict(path=name,**pin) for name,pin in m.CORE_PINS.items()),'ORIGINAL_CORE_BYTE_PINS')
    return j.progress(q,expected,names,exe,engine,controller)


def contracts():
    result=j.contracts();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in
        ('test_minimal_r07_worker','test_minimal_runtime_r07_case'))
    with patch('subprocess.Popen',side_effect=AssertionError('P205_NO_CONTRACT_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P205_NO_CONTRACT_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P205_NO_CONTRACT_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(checked.wasSuccessful() and checked.testsRun==22 and not checked.skipped,'CONTRACT12_PLUS10')
    result.update(minimal_worker_contract_tests_passed=12,minimal_runtime_bridge_contract_tests_passed=10)
    return result


def publish(doc,stream,**kw):
    doc['joined_progress_parse_accounting']=dict(j.ACCOUNTING)
    doc['minimal_runtime_bridge_generation']='P205_CONTROLLER16'
    if doc.get('schema_version')==v.SCHEMA:
        match=re.fullmatch(r'p204-r07-case-([0-9]{3})-tests',doc['task'])
        require(match is not None,'PUBLISHED_MINIMAL_TASK')
        original=f'p191-r07-case-{int(match[1]):03}-tests'
        doc.update(original_parent_task_before_minimal_worker=original,minimal_owned_worker_path=m.SELF,
            minimal_worker_source_only_import_connected=True,original_parent_guard_and_full_runtime_fresh_scope_retained=True)
        if doc['state']==v.CASE_PASS:validate_bridge(doc,v.pins(doc['runtime_resume_controller_input_pins']))
    return ORIGINAL_DUMP(doc,stream,**kw)


ORIGINAL_DUMP=p.RAW_DUMP


def main():
    with patch.object(p,'progress',progress),patch.object(p,'CONTROLLERS',CONTROLLERS), \
            patch.object(p,'contracts',contracts),patch.object(p,'RAW_DUMP',publish), \
            patch.object(j,'case_controller',case_controller),patch.object(c,'run',owned_run):
        return p.main()


if __name__=='__main__':
    sys.modules.setdefault('run_minimal_runtime_r07_case',sys.modules[__name__])
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,c.subprocess.SubprocessError) as error:
        print(p.json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=b.run.original.closed_error(error))))
        raise SystemExit(2) from None
