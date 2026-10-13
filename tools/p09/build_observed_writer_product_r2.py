"""P171 r2 worker-side r06 recipe binding; preserves first terminal failure."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import build_observed_writer_product as prior
d=prior.d; c=prior.c; s=prior.s; b=prior.b
SELF='tools/p09/build_observed_writer_product_r2.py'
TEST='tools/p09/tests/test_observed_writer_product_r2.py'
CONTRACT_COUNT=205
RAW_HELPERS=prior.helpers

def helpers():return sorted(set(RAW_HELPERS())|{SELF,TEST,
    'implementation/p09/evidence/p09-171-observed-writer-product-build.actual-run01.v1.json',
    'implementation/p09/evidence/p09-171-observed-writer-product-build.terminal-audit-run01.v1.json'})

def worker(task):
    with patch.object(d,'RUN',6):return prior.worker(task)

def contracts():
    prior.contracts();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_observed_writer_product_r2')
    with patch('subprocess.Popen',side_effect=AssertionError('P171_R2_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P171_R2_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P171_R2_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    prior.require(result.wasSuccessful() and result.testsRun==3 and not result.skipped,'R2_CONTRACT3_PLUS202')
    return dict(contract_tests_run=CONTRACT_COUNT,contract_tests_passed=CONTRACT_COUNT)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True)
    mode=parser.parse_args().mode;prior.require(c.Path.cwd().resolve()==c.ROOT,'R2_CWD')
    destination=s.scoped_path(f'implementation/p09/evidence/p09-171-observed-writer-product-build.{mode}-run05.v1.json'
        if mode=='light' else 'implementation/p09/evidence/p09-171-observed-writer-product-build.actual-run02.v1.json',fresh=True)
    if mode=='actual':
        contracts()
        with patch.object(prior,'SELF',SELF),patch.object(prior,'helpers',helpers):
            return prior.run_owned(destination,prior.load_binding())
    resources=s.SQLRuntimeResources();q=None;out=dict(state='FAILED_NOT_ACCEPTED')
    try:
        resources.admit();q=s.LiveSQLReader(resources)
        out.update(contracts())
        for n in (*prior.helpers(),SELF,TEST):q.pin(n)
        q.finish();out.update(state='PASS_WORKER_R06_PROGRESS_BINDING_CONTRACTS_ONLY_NOT_ACTUAL_OR_GATE',
            actual_Cargo_SQL_native_executed=False,product_complete=False,P09_gate='OPEN')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=d.writer.b.prior.d.original.closed_error(e)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,b.subprocess.SubprocessError) as e:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=d.writer.b.prior.d.original.closed_error(e))))
        raise SystemExit(2) from None
