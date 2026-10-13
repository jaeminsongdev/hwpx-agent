"""P217 지원 계약만 검증한다. 실제 잠금/제품 실행·연결/프리즈 해결 증거가 아니다."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import resume_generic_locked_runtime as g
import native_open_backpressure as native

p=g.p
SELF='tools/p09/qualify_native_open_backpressure.py'
PASS='PASS_NATIVE_OPEN_BACKPRESSURE_CONTRACT10_NOT_ACTUAL_OR_GATE'


def contracts():
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_native_open_backpressure as tests
    with patch('subprocess.Popen',side_effect=AssertionError('NO_NATIVE_CONTRACT_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_NATIVE_CONTRACT_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_NATIVE_CONTRACT_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    p.require(result.wasSuccessful() and result.testsRun==10 and not result.skipped,'NATIVE_OPEN_CONTRACT10')
    return 10


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    p.require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=99,'NATIVE_OPEN_CWD_RUN')
    destination=p.c.ROOT/f'{p.DIR}/p217-native-open-light-run{args.run:02}.v1.json'
    p.require(not destination.exists(),'NATIVE_OPEN_FRESH_ONLY')
    context=g.observation.Context();owner=g.observation.Resources(context);q=None;candidate=None
    out=dict(state='FAILED_NOT_ACCEPTED',schema_version='hwpx-agent.p09-native-open-pressure-contract/v1',
        **p.r.flags(),actual_native_pressure_frame_executed=False,actual_product_bridge_connected=False)
    try:
        owner.admit();q=p.qualification.Reader(owner,context)
        out['native_open_contract_tests_passed']=contracts()
        for name in (SELF,native.SELF,native.TEST,native.borrowed.SELF,native.borrowed.TEST,
                native.borrowed.locks.SELF,native.borrowed.locks.TEST,native.pressure.SELF,native.pressure.TEST):q.pin(name)
        q.finish();candidate=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out.update(state='FAILED_NOT_ACCEPTED',error_code=p.b.run.original.closed_error(error));candidate=None
    finally:
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['metadata_observation']=g.observation.summary(owner)
        def validate(doc):p.require(doc['IO']['finished'] is True
            and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes'],'NATIVE_OPEN_FINAL_FRESH')
        g.complete(out,owner,candidate,validate)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','native_open_contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
