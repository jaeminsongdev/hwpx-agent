"""P178 lower owned hashing rate; P177 pre-GO CPU stop preserved, fresh r07 only."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import build_xml_capacity_product as prior
import owned_source_read_pressure as pressure
SELF='tools/p09/build_xml_capacity_product_r2.py'
TEST='tools/p09/tests/test_owned_source_read_pressure.py'
PREPARATION='implementation/p09/evidence/p09-178-owned-hash-pressure.preparation-run01.v1.json'
ACTUAL='implementation/p09/evidence/p09-178-owned-hash-pressure.actual-run01.v1.json'
LIGHT='implementation/p09/evidence/p09-178-owned-hash-pressure.light-run01.v1.json'
COUNT=260
RAW_CONTRACTS=prior.contracts
RAW_HELPERS=prior.helpers

def contracts():
    RAW_CONTRACTS();sys.path.insert(0,str(prior.c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_owned_source_read_pressure')
    with patch('subprocess.Popen',side_effect=AssertionError('P178_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P178_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P178_NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    prior.require(result.wasSuccessful() and result.testsRun==6 and not result.skipped,'CONTRACT254_PLUS6')
    return dict(contract_tests_passed=COUNT,contract_tests_run=COUNT)

def helpers():return sorted(set(RAW_HELPERS())|{SELF,TEST,pressure.SELF,prior.ACTUAL,prior.PREPARATION,
    'implementation/p09/evidence/p09-177-xml-capacity-product-build.actual-run01.v1.json',
    'implementation/p09/evidence/p09-177-xml-capacity-product-build.preparation-run01.v1.json'})

def worker(task):return prior.worker(task)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),required=True);mode=ap.parse_args().mode
    prior.require(prior.c.Path.cwd().resolve()==prior.c.ROOT,'P178_CWD')
    if mode=='actual':
        # Fresh original r07 is allowed only because the first run never created
        # worker/Job/output. The existing fresh_scope rejects any actual output.
        destination=prior.s.scoped_path(ACTUAL,fresh=True);prior.fresh_scope({})
        with patch.object(prior,'SELF',SELF),patch.object(prior,'PREPARATION',PREPARATION), \
                patch.object(prior,'ACTUAL',ACTUAL),patch.object(prior,'helpers',helpers), \
                patch.object(prior,'contracts',contracts),patch.object(prior,'weighted',pressure):
            return prior.run_owned(destination,prior.load_binding())
    destination=prior.s.scoped_path(LIGHT,fresh=True);resources=prior.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',
        actual_Cargo_SQL_native_or_child_executed=False,actual_lower_rate_build_executed=False,PC_freeze_resolved=False,
        original_compile600_full2491200_and_guards_unchanged=True)
    try:
        resources.admit();q=pressure.WeightedLiveReader(resources);out.update(contracts())
        for n in helpers():q.pin(n)
        old=q.json('implementation/p09/evidence/p09-177-xml-capacity-product-build.actual-run01.v1.json')
        prior.require(old['state']=='DEFERRED_NOT_STARTED' and old['stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
            and not old['heavy_work_started'] and not old['worker_created'] and not old['job_assigned']
            and not old['writer_authorized'] and old['executable_pin'] is None
            and old['cleanup_confirmed'] and old['owned_tree_empty'],'FIRST_PRE_GO_STOP_PRESERVED')
        q.finish();out.update(state='PASS_LOWER_OWNED_HASH_PRESSURE_CONTRACTS_ONLY_NOT_ACTUAL_OR_GATE',
            source_closing_exact=True,owned_hash_read_rates={'binary':pressure.BINARY_RATE,'other':pressure.OTHER_RATE},
            independent_live_reader_rates={'binary':pressure.prior.BINARY_RATE,'other':pressure.prior.OTHER_RATE},
            first_stop_receipt_pin=q.reader.snapshots['implementation/p09/evidence/p09-177-xml-capacity-product-build.actual-run01.v1.json'])
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=prior.parser.d.original.closed_error(error)
    finally:
        prior.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['resource_tail']=pressure.resource_tail(resources)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,prior.b.subprocess.SubprocessError) as error:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=prior.parser.d.original.closed_error(error))))
        raise SystemExit(2) from None
