"""P239 지원 계약52: 실제 CPU stress/Native frame/제품 실행 없이 새 helper 검증."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import deferred_uncreated_borrower_failure as candidate
import resume_post_stop_compound_runtime as r
SELF='tools/p09/qualify_uncreated_borrower_failure.py'
PASS='PASS_UNCREATED_BORROWER_FAILURE_CONTRACT52_ONLY_NOT_RUNTIME_CONNECTION_OR_GATE'


def contracts():
    r.require(r.r.qualified.contracts()==44,'ORIGINAL_TERMINAL44')
    sys.path.insert(0,str(r.p.c.ROOT/'tools/p09/tests'))
    with patch('subprocess.Popen',side_effect=AssertionError('NO_UNCREATED_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_UNCREATED_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_UNCREATED_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromName('test_uncreated_borrower_failure'))
    r.require(result.wasSuccessful() and result.testsRun==8 and not result.skipped,'UNCREATED_NEW8')
    return 52


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True,type=int);args=ap.parse_args()
    r.require(r.p.c.Path.cwd().resolve()==r.p.c.ROOT and 1<=args.run<=99,'UNCREATED_CWD_RUN')
    path=r.p.c.ROOT/f'{r.p.DIR}/p239-uncreated-borrower-support-run{args.run:02}.v1.json'
    r.require(not path.exists(),'UNCREATED_FRESH_ONLY')
    context=r.g.observation.Context();owner=r.g.observation.Resources(context);q=proposed=None
    out=dict(schema_version='hwpx-agent.p09-uncreated-borrower-failure-support/v1',state='FAILED_NOT_ACCEPTED',
        **r.p.r.flags(),actual_product_body_executed=False,actual_Native_frame_or_CPU_STOP_executed=False,
        runtime_connection_qualified=False,original_sources_rewritten=False)
    try:
        owner.admit();q=r.Reader(owner,context)
        sources=(SELF,candidate.SELF,candidate.TEST,candidate.original.SELF,candidate.original.TEST,
            candidate.original.failure.SELF,candidate.original.failure.TEST,r.r.qualified.SELF,
            'tools/p09/terminal_failure_receipt.py','tools/p09/tests/test_terminal_failure_receipt.py',
            r.r.compact.SELF,r.r.compact.TEST)
        for name in sources:q.pin(name)
        out['support_contract_tests_passed']=contracts();q.finish();proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=r.p.b.run.original.closed_error(error)
    finally:
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        r.g.complete(out,owner,proposed,lambda doc:r.require(doc['IO']['finished'] is True
            and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']==12
            and doc['support_contract_tests_passed']==52,'UNCREATED_ALL_FRESH52'))
        with path.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','support_contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
