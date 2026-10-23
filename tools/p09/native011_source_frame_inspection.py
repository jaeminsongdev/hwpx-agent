"""Actual all198 source locks/two reads; no child, product or Native retry.

This exercises original basic Frame/Locks, not the projected Native runtime.
It cannot authorize moving any worker boundary or a product GO.
"""
import argparse
import copy
import json
from pathlib import Path
import re
import sys
import time
import traceback
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/native011_source_frame_inspection.py'
WORKER=dict(path='implementation/p09/evidence/p09-361-native011-inherited-event-worker001.v1.json',
    bytes=45663,sha256='b0a4817ba79f7a8acb7764a2f9ceac89f86fe2312baa0f991ecb763dfdd0337f')
ORIGINALS=(
    dict(path='tools/p09/runtime_input_frame.py',bytes=5802,sha256='44a21215a76f4160ca7bfeb55b02f3bb464a2017671b0c2dae9883d7c9cd8929'),
    dict(path='tools/p09/locked_runtime_inputs.py',bytes=15465,sha256='e7c40a2ec0367e01c359e3b89c179d45367e9db233348e76ba82364cc0599e14'))


def main():
    sys.dont_write_bytecode=True
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    args=parser.parse_args()
    if not 1<=args.attempt<=8:raise ValueError('SOURCE_FRAME_BOUNDED_ATTEMPT')
    denied=[]
    def deny(event,arguments):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('SOURCE_FRAME_PROCESS_DENIED')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import current_stored_runtime_scope as scope,runtime_input_frame as frames,locked_runtime_inputs as locks
    import native011_source_coverage as coverage,successor_preparation_workspace_v1 as publisher
    host.configure_host_policy(c)
    guard=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    output=f'implementation/p09/evidence/p09-361-native011-source-frame-attempt{args.attempt:03}.v1.json'
    row=dict(state='FAILED_FULL198_READONLY_SOURCE_FRAME_NOT_NATIVE',contracts=[],process_creation_attempts=0,
        actual_worker_or_product_executed=False,worker_IO_exemptions_applied=False,
        actual_projected_Native_Frame_qualified=False,GO_authorized=False,accepted_count_delta=0)
    q=frame=None;started=time.monotonic()
    shapes={cls:dict(vars(cls)) for cls in (frames.Frame,frames.Registry,locks.InputLocks)}
    def same_classes():
        return all(set(vars(cls))==set(saved) and all(vars(cls)[name] is value for name,value in saved.items())
            for cls,saved in shapes.items())
    def rejected(label,fn):
        try:fn()
        except ValueError as error:
            row['contracts'].append(dict(name=label,state='REJECTED_AS_REQUIRED',error_type=type(error).__name__))
        else:raise ValueError('SOURCE_FRAME_REQUIRED_REJECTION_MISSING')
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        c.require(not (c.ROOT/output).exists(),'SOURCE_FRAME_EXCLUSIVE_RESULT')
        for name in (SELF,coverage.SELF):q.pin(name)
        for pin in ORIGINALS:a.exact(q.pin(pin['path']),pin,'SOURCE_FRAME_ORIGINAL_UNMODIFIED_CODE')
        worker=a.read_exact(q,WORKER)
        a.fields(worker,dict(state='PASS_ORIGINAL_INHERITED_EVENT_EOF_WORKER_NOT_PRODUCT',
            fresh_inputs=198,final_fresh_hashes=198,actual_product_GO_received=False,
            process_creation_attempts=0),'SOURCE_FRAME_REAL_REQUIRED198_NOT_MODEL')
        required=scope.pins(worker['source_pins'],198)
        held=locks.InputLocks(c.ROOT,guard.check)
        c.require(held.api.pacer.rate==32 and held.api.pacer.opens==0,'SOURCE_FRAME_UNUSED_ORIGINAL_PACER')
        held.api.pacer.rate=14  # Lower than original32; no burst state reset.
        frame=frames.Frame(frames.Registry(),required,guard.check,held=held)
        check=lambda role,req=required:coverage.verify(frame,req,frame_type=frames.Frame,boundary=role)
        rejected('new_frame_without_locks_or_first_bytes',lambda:check('before'))
        row['stage']='ACTUAL198_LOCK_ACQUISITION14';frame.acquire()
        c.require(held.api.pacer.rate==14,'SOURCE_FRAME_ACQUISITION14_RETAINED')
        held.api.pacer.rate=20  # Original phase ceilings14/20, both below32.
        class Reader(a.AcceptanceReader):
            def diagnostics(self):
                return dict(read_passes=self.read_passes,bytes_read=self.bytes_read,
                    observed_input_count=len(self.snapshots),open_rate=self.open_pacer.rate,
                    actual_open_reservations=self.open_pacer.opens)
        reader_factory=lambda checkpoint:Reader(c.ROOT,checkpoint)
        row['stage']='ORIGINAL_FIRST_FULL198_BYTE_BOUNDARY';frame.read_boundary(reader_factory,guard.check)
        row['before_coverage']=check('before')
        row['contracts'].append(dict(name='actual_live_all198_before_coverage',state='PASS'))
        tampered=copy.deepcopy(required);first=next(iter(tampered));tampered[first]['sha256']='0'*64
        rejected('same_paths_wrong_hash',lambda:check('before',tampered))
        missing=dict(required);missing['tools/p09/nonexistent-source-coverage-required.py']=dict(
            path='tools/p09/nonexistent-source-coverage-required.py',bytes=1,sha256='0'*64)
        rejected('required_worker_input_missing_from_frame',lambda:check('before',missing))
        rejected('serialized_frame_summary_not_live_reference',lambda:coverage.verify(
            frame.summary(),required,frame_type=frames.Frame,boundary='before'))
        for label,access in (('write_access_denied_by_live_share_lock',locks.WRITE),
                             ('delete_access_denied_by_live_share_lock',locks.DELETE)):
            result=held.api.access_probe(c.ROOT/'tools/p09/native011_ready_worker.py',access)
            c.require(result['opened'] is False and result['win32_error']==32,'SOURCE_FRAME_ACTUAL_SHARE_VIOLATION')
            row['contracts'].append(dict(name=label,state='PASS_NO_CONTENT_OR_ATTRIBUTE_OPERATION'))
        row['stage']='ORIGINAL_SECOND_FULL198_BYTE_BOUNDARY';frame.read_boundary(reader_factory,guard.check)
        rejected('after_boundary_cannot_serve_as_before',lambda:check('before'))
        row['after_coverage']=check('after')
        row['contracts'].append(dict(name='actual_live_all198_after_coverage',state='PASS'))
        row['two_stream_passes']=held.verify_two_byte_passes(required)
        c.require(frame.close(),'SOURCE_FRAME_ORIGINAL_CLOSE_ALL_HANDLES')
        rejected('closed_frame_not_live_coverage',lambda:check('after'))
        c.require(len(row['contracts'])==10 and same_classes() and not denied,
            'SOURCE_FRAME_TEN_NEW_CONTRACTS_ORIGINAL_METHODS_AND_NO_PROCESS')
        q.finish();guard.check(force=True)
        row.update(state='PASS_FULL198_LIVE_READONLY_SOURCE_FRAME_COVERAGE_TWO_BOUNDARIES_NOT_NATIVE',
            required_worker_input_count=198,held_input_bytes=sum(p['bytes'] for p in required.values()),
            original_classes_and_methods_unchanged=True,original_frame_committed=False,
            all198_worker_inputs_physically_read_twice=True,live_handle_exemptions_applied=False,
            prior_suites_reexecuted=False)
    except (ValueError,OSError,KeyError,IndexError,TypeError,AttributeError,MemoryError,NameError,ImportError) as error:
        row['error_type']=type(error).__name__
        row['error_code']=error.args[0] if error.args and type(error.args[0]) is str and re.fullmatch(
            '[A-Za-z0-9_]{1,160}',error.args[0]) else 'CLOSED_SOURCE_FRAME_INSPECTION_FAILURE'
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-5:]]
    finally:
        cleanup=True
        try:
            if frame is not None and frame.registered:cleanup=frame.close()
            if frame is not None:
                row['frame_terminal_state']=frame.state;row['handles']=frame.held.summary()
                row['boundary_counts']=[dict(role=b['role'],**b['reader_diagnostics']) for b in frame.boundaries]
        finally:guard.close()
        row.update(cleanup_confirmed=cleanup and guard.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=guard.samples,
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            process_creation_attempts=len(denied))
        if not row['cleanup_confirmed']:row['state']='FAILED_FULL198_READONLY_SOURCE_FRAME_CLEANUP'
        pin=publisher.publish(c.ROOT,output,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],stage=row.get('stage'),error_code=row.get('error_code'),
            error_frames=row.get('error_frames'),contracts=len(row['contracts']),cleanup=row['cleanup_confirmed'],
            elapsed=row['elapsed_seconds'],handles=row.get('handles'),boundaries=row.get('boundary_counts'),
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            RAM_available_min=min((s['available_ram_percent'] for s in guard.samples),default=None),receipt=pin)),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup_confirmed'] else 2


if __name__=='__main__':raise SystemExit(main())
