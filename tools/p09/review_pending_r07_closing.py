"""P194: review a passed exact case whose independent source closing stopped.

완료 후보를 다시 실행하지 않는다. 원 실패 receipt와 후보를 바이트 바인딩하며
원 v.plan으로 기존 수용3/미수용 후보1을 재구성한다. closing을 대신하지 않는다.
"""
import io
import json
import sys
import unittest
from unittest.mock import patch
import run_shared_resumable_r07_batch as batch

c=batch.c;v=batch.v;core=batch.core
SELF='tools/p09/review_pending_r07_closing.py'
TEST='tools/p09/tests/test_pending_r07_closing_review.py'
DEST='implementation/p09/evidence/p09-194-pending-case004-closing-review-run01.v1.json'
CASE=dict(path=core.DIR+'/p190-case-004-attempt-001.json',bytes=617816,
    sha256='53159ac973e75e5562439c8a173afa948c9b7c23719826cb51a205d305b9634a')
STOP=dict(path=core.paths(5)['closing'],bytes=304809,
    sha256='715d9f22098622741f5f844ed832a5917078b417cfb4122dee081b1bb90cb3bd')


def require(ok,code):c.require(ok,'P194_'+code)


def validate_pending(case,stop,status):
    require(case['state']==v.CASE_PASS and case['closing_id']==STOP['path'],'ORIGINAL_PASSED_CASE')
    require(stop['state']=='FAILED_NOT_ACCEPTED'
        and stop['error_code']==stop['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and stop['resource_watcher_cleanup_confirmed'] is True and stop['IO']['finished'] is False
        and stop['actual_test_runtime_executed'] is False,'STOP_NOT_PROMOTED')
    require(status['accepted_individual_cases']==3 and status['remaining_individual_cases']==246
        and status['successful_candidates_requiring_separate_closing']==1
        and status['remaining_regular_cases']==240 and status['remaining_corpus_cases']==6
        and status['next_index']==5,'EXACT_PENDING_STATE')
    return dict(successful_case004_requires_independent_closing=True,
        automatically_reexecute_successful_case004=False,start_case005_before_candidate_closing=False,
        original_failed_closing_not_overwritten=True,whole_source_recovery_or_fresh_closing_completed=False)


def contracts():
    result=batch.contracts();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_pending_r07_closing_review')
    with patch('subprocess.Popen',side_effect=AssertionError('P194_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P194_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P194_NO_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(checked.wasSuccessful() and checked.testsRun==4 and not checked.skipped,'CONTRACT4')
    result['pending_review_contract_tests_passed']=4;return result


def main():
    require(c.Path.cwd().resolve()==c.ROOT,'CWD');destination=batch.s.scoped_path(DEST,fresh=True)
    resources=batch.run.pressure.observation.ObservedResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',**core.flags(),actual_product_test_child_executed=False,
        new_whole_source_or_EXE_reaudit_executed=False,pending_review_not_source_closing=True)
    try:
        resources.admit();q=batch.run.pressure.PressureReader(resources)
        for name in (SELF,TEST):q.pin(name)
        out.update(contracts());expected,names,exe=batch.baseline(q)
        for pin in (CASE,STOP):require(q.pin(pin['path'])==pin,'IMMUTABLE_CANDIDATE_AND_STOP')
        case=q.json(CASE['path']);stop=q.json(STOP['path']);status=core.progress(q,names,expected,exe)
        v.validate_case(case,names[3],v.identity(names,expected,exe))
        engine={name:q.pin(name) for name in (batch.SELF,batch.TEST)}
        batch.validate_supplement(case,expected,engine)
        actions=validate_pending(case,stop,status);q.finish()
        out.update(state='PASS_PENDING_CASE004_AND_PRESERVED_STOP_PLAN_ONLY_NOT_CLOSING_OR_GATE',
            plan=status,successful_case_receipt_pin=CASE,original_failed_closing_pin=STOP,**actions)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=batch.run.original.closed_error(error)
    finally:
        batch.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['resource_tail']=batch.run.pressure.observation.parent_tail(resources)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','pending_review_contract_tests_passed',
            'error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
