"""P227: 원 P208 호출 경로의 합성 STOP 연결과 종료 후 실제 새 sidecar 기록.

원 ORIGINAL_RUN만 합성 terminal로 대체한다. EXE/Job/GO/source frame 획득 없음.
실제 제품 STOP를 일으키거나 case060을 재시도하지 않는다.
"""
import argparse
import hashlib
import io
import json
import sys
import unittest
from unittest.mock import patch
import deferred_parent_failure as adapter
import resume_packed_pressure_runtime as r

SELF='tools/p09/qualify_deferred_parent_failure.py'
PASS='PASS_ORIGINAL_PARENT_STOP_CONNECTION_SYNTHETIC_NOT_PRODUCT_OR_RESUME'
NOTICE=dict(path=r.p.DIR+'/p226-stop-notice-run01.v1.json',bytes=14737,
    sha256='df2713cd6b0461108bfa486ca13d3196f990034702252d74004efebe133ce1a7')


def contracts():
    sys.path.insert(0,str(r.p.c.ROOT/'tools/p09/tests'))
    import test_terminal_failure_receipt as old
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in
        ('test_terminal_failure_receipt','test_terminal_failure_receipt_r2','test_deferred_parent_failure'))
    with patch.object(old,'m',adapter.failure), \
         patch('subprocess.Popen',side_effect=AssertionError('NO_PARENT_CONNECTION_CHILD')), \
         patch('subprocess.run',side_effect=AssertionError('NO_PARENT_CONNECTION_CHILD')), \
         patch('threading.Thread.start',side_effect=AssertionError('NO_PARENT_CONNECTION_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    r.require(result.wasSuccessful() and result.testsRun==44 and not result.skipped,'CONNECTION_CONTRACT44')
    return 44


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,required=True);args=parser.parse_args()
    r.require(r.p.c.Path.cwd().resolve()==r.p.c.ROOT and 1<=args.run<=99,'CONNECTION_CWD_RUN')
    destination=r.p.c.ROOT/f'{r.p.DIR}/p227-parent-stop-connection-run{args.run:02}.v1.json'
    sidecar=r.p.c.ROOT/f'{r.p.DIR}/cases/p227-synthetic-stop-run{args.run:02}.json'
    r.require(not destination.exists() and not sidecar.exists(),'CONNECTION_FRESH_ONLY')
    context=r.g.observation.Context();owner=r.g.observation.Resources(context);q=candidate=capture=None
    out=dict(schema_version='hwpx-agent.p09-deferred-parent-connection/v1',state='FAILED_NOT_ACCEPTED',
        **r.p.r.flags(),synthetic_parent_terminal_only=True,actual_product_worker_executed=False,
        actual_Job_GO_or_input_frame_acquired=False,product_body_reexecuted=False,
        runtime_resume_authorized=False,CPU_cause_or_PC_freeze_resolution_established=False)
    try:
        owner.admit();q=r.Reader(owner,context)
        source_names=(SELF,adapter.SELF,adapter.TEST,adapter.failure.SELF,adapter.failure.TEST,
            'tools/p09/terminal_failure_receipt.py','tools/p09/tests/test_terminal_failure_receipt.py',
            r.SELF,r.TEST,r.p.SELF,r.p.TEST,r.p.frames.SELF,r.p.frames.TEST,
            r.compact.SELF,r.compact.TEST,'tools/p09/conservative_maintenance.py')
        for name in source_names:q.pin(name)
        r.require(q.pin(NOTICE['path'])==NOTICE,'CONNECTION_STOP_NOTICE_PIN')
        notice=q.json(NOTICE['path'])
        r.require(notice['state']=='PASS_PACKED_STOP_DOCUMENT_NOTICE_NOT_RUNTIME_RESUME_OR_GATE'
            and notice['runtime_resume_authorized'] is False and notice['failure_writer_actual_connection'] is False
            and notice['IO']['finished'] is True and notice['resource_stop_reason'] is None
            and notice['resource_watcher_cleanup_confirmed'] is True,'CONNECTION_PRIOR_NOT_RESUME')
        out['connection_contract_tests_passed']=contracts()
        import test_deferred_parent_failure as tests
        frame=tests.Frame();completed=[];capture=adapter.Capture(frame,completed,60,tests.NAME,tests.BINDING)
        placeholder=io.StringIO();calls=[]
        def stopped(task,path,seconds):
            r.require(task=='p204-r07-case-060-tests' and seconds==1200 and not calls,'ONE_SYNTHETIC_PARENT')
            calls.append(task);frame.state='BROKEN';row=tests.document()
            json.dump(row,placeholder,ensure_ascii=False,indent=2)
            return 2
        with patch.object(r.p,'ORIGINAL_RUN',stopped),patch.object(r.p,'RAW_DUMP',capture.writer), \
             patch('subprocess.Popen',side_effect=AssertionError('NO_CONNECTION_PRODUCT_CHILD')), \
             patch('subprocess.run',side_effect=AssertionError('NO_CONNECTION_PRODUCT_CHILD')), \
             patch('threading.Thread.start',side_effect=AssertionError('NO_CONNECTION_NEW_THREAD')):
            code=r.p.run_parent(frame,60,tests.NAME,None,context,tests.BINDING)
        r.require(code==2 and calls==['p204-r07-case-060-tests'] and capture.pending
            and placeholder.getvalue()=='' and not completed,'EXACT_SYNTHETIC_STOP_DEFERRED')
        r.require(frame.close(),'SYNTHETIC_FRAME_CLOSED')
        out.update(original_parent_call_path_exercised=True,original_parent_STOP_not_swallowed=True,
            no_live_frame_check_or_write_during_STOP=True,synthetic_frame_only=True,
            successful_packed_writer_unmodified=True)
        q.finish();candidate=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=r.p.b.run.original.closed_error(e)
    finally:
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        r.g.complete(out,owner,candidate,lambda row:r.require(row['IO']['finished'] is True
            and row['IO']['bound_inputs']==row['IO']['final_fresh_hashes']
            and row['connection_contract_tests_passed']==44,'CONNECTION_ALL_FRESH'))
        if out['state']==PASS:
            try:
                digest=hashlib.sha256();written=0
                class HashingStream:
                    def __init__(self,stream):self.stream=stream
                    def write(self,block):
                        nonlocal written
                        count=self.stream.write(block)
                        r.require(type(count) is int and count==len(block),'CONNECTION_OUTPUT_SHORT_WRITE')
                        digest.update(block.encode('ascii'));written+=count
                        return count
                with sidecar.open('x',encoding='utf-8') as stream:
                    stats=capture.write_terminal(HashingStream(stream),owner,out)
                out.update(synthetic_sidecar_pin=dict(path=sidecar.relative_to(r.p.c.ROOT).as_posix(),
                    bytes=written,sha256=digest.hexdigest()),synthetic_sidecar_write_statistics=stats,
                    real_filesystem_sidecar_written_after_original_owner_cleanup=True)
            except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:
                out.update(state='FAILED_NOT_ACCEPTED',error_code=r.p.b.run.original.closed_error(e))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({key:out.get(key) for key in ('state','error_code','resource_stop_reason',
            'resource_watcher_cleanup_confirmed','connection_contract_tests_passed',
            'synthetic_sidecar_pin','real_filesystem_sidecar_written_after_original_owner_cleanup')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
