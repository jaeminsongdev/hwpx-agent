"""P195 metadata-only cost/scope inventory; no EXE bytes or acceptance change."""
import io
import json
import sys
import unittest
from unittest.mock import patch
import recover_r07_case004_closing as recovery

b=recovery.b;c=b.c;v=b.v
SELF='tools/p09/audit_r07_closing_workload.py'
TEST='tools/p09/tests/test_r07_closing_workload.py'
DEST='implementation/p09/evidence/p09-195-closing-workload-inventory-run01.v1.json'
LIGHT=dict(path=recovery.paths('light',4),bytes=28959,
    sha256='a4a8803485e247713079adadd6e66d908708a945cee07b914429beddf09ca338')
STOP=dict(path=recovery.paths('recover',3),bytes=758505,
    sha256='070c8087d9cc548a33faeaefd407fd0858a5691e7f33d3fd2d8b7214a9f527bf')


def require(ok,code):c.require(ok,'P195_COST_'+code)


def classify(expected,exe,engine):
    runtime,history=b.OLD_RUNTIME_SCOPE(expected,exe)
    augmented,_=b.source_extension(runtime,history,engine)
    require(len(expected)==1470 and len(runtime)==1403 and len(augmented)==1405 and len(history)==67,'EXACT_SCOPE')
    return dict(original_whole_input_count=len(expected),actual_case_runtime_input_count=len(augmented),
        historical_EXE_count=len(history),runtime_current_EXE_bytes=exe['bytes'],
        runtime_total_bytes_one_full_pass=sum(p['bytes'] for p in augmented.values()),
        whole_total_bytes_one_full_pass=sum(p['bytes'] for p in expected.values()),
        historical_only_EXE_bytes_one_pass=sum(expected[n]['bytes'] for n in history),
        historical_only_EXE_bytes_two_passes=2*sum(expected[n]['bytes'] for n in history),
        every_non_EXE_runtime_input_retained=True,current_EXE_retained=True,
        historical_pins_are_sealed_references_not_current_byte_verification=True,
        workload_inventory_not_permission_to_skip_whole_gate=True)


def contracts():
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_r07_closing_workload')
    with patch('subprocess.Popen',side_effect=AssertionError('NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==4 and not result.skipped,'CONTRACT4')
    return dict(scope_inventory_contract_tests_passed=4)


def main():
    require(c.Path.cwd().resolve()==c.ROOT,'CWD');destination=b.s.scoped_path(DEST,fresh=True)
    owner=b.run.pressure.observation.ObservedResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',**b.core.flags(),actual_product_child_executed=False,
        historical_or_current_EXE_bytes_rehashed=False,new_whole_closing_executed=False,
        legacy_whole_acceptance_not_changed=True)
    try:
        owner.admit();q=b.run.pressure.PressureReader(owner)
        for name in (SELF,TEST):q.pin(name)
        for pin in (LIGHT,STOP,recovery.CASE):require(q.pin(pin['path'])==pin,'RECOVERY_HISTORY')
        light=q.json(LIGHT['path']);old=v.pins(light['bound_input_pins'])
        require(light['state']=='PASS_P195_CONTRACTS_AND_PENDING_PLAN_ONLY_NOT_RECOVERY'
            and light['contract_tests_passed']==154 and light['observation_contract_tests_passed']==10
            and light['independent_closing_contract_tests_passed']==12 and light['resource_stop_reason'] is None
            and light['resource_watcher_cleanup_confirmed'] and light['IO']['finished'],'PRIOR176')
        for name in recovery.SOURCES:require(q.pin(name)==old[name],'TESTED_SOURCE_UNCHANGED')
        stop=q.json(STOP['path']);require(stop['state']=='FAILED_NOT_ACCEPTED'
            and stop['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU' and stop['IO']['finished'] is False
            and stop['candidate_body_reexecuted'] is False and stop['additional_product_child_executed'] is False,'STOP_NOT_PASS')
        expected,names,exe=b.baseline(q);engine={n:q.pin(n) for n in (b.SELF,b.TEST)}
        case=q.json(recovery.CASE['path']);v.validate_case(case,names[3],v.identity(names,expected,exe))
        b.validate_supplement(case,expected,engine)
        cost=classify(expected,exe,engine);status=recovery.RAW_PROGRESS(q,names,expected,exe)
        recovery.pending.validate_pending(case,q.json(recovery.STOP['path']),status)
        out.update(contracts());q.finish()
        out.update(state='PASS_RUNTIME_AND_HISTORICAL_SCOPE_COST_INVENTORY_ONLY_NOT_CLOSING_OR_GATE',
            cost=cost,plan=status,reused_prior_contract_tests_passed=176,
            successful_case_receipt_pin=recovery.CASE,failed_recovery_pin=STOP)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.run.original.closed_error(error)
    finally:
        b.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
        if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['resource_tail']=b.run.pressure.observation.parent_tail(owner)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','reused_prior_contract_tests_passed',
            'scope_inventory_contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
