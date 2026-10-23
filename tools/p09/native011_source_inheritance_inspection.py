"""Real two-file parent flag transaction; no child/Native/READY/GO launch."""
import copy
import json
from pathlib import Path
import re
import sys
import time
import traceback
from types import SimpleNamespace as NS

SELF='tools/p09/native011_source_inheritance_inspection.py'
ORIGINALS=(
    dict(path='tools/p09/runtime_input_frame.py',bytes=5802,sha256='44a21215a76f4160ca7bfeb55b02f3bb464a2017671b0c2dae9883d7c9cd8929'),
    dict(path='tools/p09/locked_runtime_inputs.py',bytes=15465,sha256='e7c40a2ec0367e01c359e3b89c179d45367e9db233348e76ba82364cc0599e14'))


def require(ok,label):
    if not ok:raise ValueError('SOURCE_INHERITANCE_INSPECTION_'+label)


def main():
    require(not sys.argv[1:],'CLOSED_READONLY_ARGUMENTS')
    denied=[]
    def deny(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('SOURCE_INHERITANCE_NO_PROCESS')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import current_stored_runtime_scope as scope,runtime_input_frame as frames,locked_runtime_inputs as locks
    import native011_source_coverage as coverage,native011_worker_source_inheritance as inheritance
    import successor_preparation_workspace_v1 as publisher
    host.configure_host_policy(c)
    g=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=frame=loan=None;started=time.monotonic()
    output='implementation/p09/evidence/p09-361-native011-current805-source-inheritance001.v1.json'
    row=dict(state='FAILED_PARENT_SOURCE_INHERITANCE_PRIMITIVE_NOT_CHILD_OR_NATIVE',
        GO_authorized=False,accepted_count_delta=0,worker_or_product_executed=False,
        actual_child_inheritance_or_READY15_qualified=False)
    classes={cls:dict(vars(cls)) for cls in (frames.Frame,frames.Registry,locks.InputLocks)}
    try:
        g.acquire();q=a.AcceptanceReader(c.ROOT,g.check)
        require(not(c.ROOT/output).exists(),'EXCLUSIVE_PRIMITIVE_RESULT')
        for name in (SELF,inheritance.SELF,inheritance.TEST,coverage.SELF):q.pin(name)
        for pin in ORIGINALS:a.exact(q.pin(pin['path']),pin,'EXACT_ORIGINAL_FRAME_AND_LOCKS')
        protocol=dict(path='tools/p09/worker_readiness_v1.py',bytes=6890,
            sha256='047c3f78f8a4472feeec4d56b65716f57e0429091321cb49afe5b685047d3a45')
        a.exact(q.pin(protocol['path']),protocol,'EXACT_ORIGINAL_READY_PROTOCOL_SOURCE')
        required=scope.pins([q.snapshots[inheritance.SELF],protocol])
        held=locks.InputLocks(c.ROOT,g.check);held.api.pacer.rate=14
        frame=frames.Frame(frames.Registry(),required,g.check,held=held);frame.acquire()
        held.api.pacer.rate=20
        class Reader(a.AcceptanceReader):
            def diagnostics(self):
                return dict(read_passes=self.read_passes,bytes_read=self.bytes_read,
                    observed_input_count=len(self.snapshots),open_rate=self.open_pacer.rate,
                    actual_open_reservations=self.open_pacer.opens)
        factory=lambda checkpoint:Reader(c.ROOT,checkpoint)
        frame.read_boundary(factory,g.check)
        before=copy.deepcopy(held.files);counts=dict(held.stream_read_counts)
        loan=inheritance.SourceInheritance(frame,required,coverage,frame_type=frames.Frame)
        handles=loan.arm()
        require(len(handles)==2 and all(held.api.inspect(handle)['inheritable'] for handle in handles),
            'ACTUAL_WIN32_PARENT_INHERITANCE_FLAGS')
        for access in (locks.WRITE,locks.DELETE):
            result=held.api.access_probe(c.ROOT/inheritance.SELF,access)
            require(result['opened'] is False and result['win32_error']==32,'ORIGINAL_SHARE_LOCK_STILL_DENIES_WRITE_DELETE')
        require(loan.restore(),'ACTUAL_ORIGINAL_FLAGS_RESTORED')
        require(held.files==before and held.stream_read_counts==counts,'NO_IDENTITY_REBASE_OR_BYTE_CREDIT')
        row['before_coverage']=coverage.verify(frame,required,frame_type=frames.Frame,boundary='before')
        row['loan']=loan.summary()
        frame.read_boundary(factory,g.check)
        row['after_coverage']=coverage.verify(frame,required,frame_type=frames.Frame,boundary='after')
        require(frame.close(),'ALL_ORIGINAL_HANDLES_RELEASED')
        require(all(set(vars(cls))==set(saved) and all(vars(cls)[name] is value for name,value in saved.items())
            for cls,saved in classes.items()),'ORIGINAL_CLASSES_AND_METHODS_RETAINED')
        q.finish();g.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots) and not denied,'CLOSING_SOURCE_BYTES_NO_PROCESS')
        row.update(state='PASS_PARENT_TWO_FILE_SOURCE_INHERITANCE_FLAGS_RESTORED_NOT_CHILD_OR_NATIVE',
            actual_source_files=2,source_bytes=sum(pin['bytes'] for pin in required.values()),
            original_two_fresh_byte_boundaries=[dict(role=record['role'],**record['reader_diagnostics']) for record in frame.boundaries],
            original_OS_identities_and_read_counts_unmodified=True,write_delete_share_denial_preserved=True,
            original_classes_and_methods_retained=True,original_Frame_committed=False,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,MemoryError) as error:
        value=error.args[0] if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value) is str
            and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_SOURCE_INHERITANCE_FAILURE',
            error_frames=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno)
                for f in traceback.extract_tb(error.__traceback__)[-5:]])
    finally:
        clean=True
        try:
            if loan is not None:
                clean=loan.state=='RESTORED' or loan.restore();row['loan_terminal']=loan.summary()
            if frame is not None:
                clean=frame.close() and clean;row['handles']=frame.held.summary();row['frame_terminal_state']=frame.state
        finally:g.close()
        row.update(cleanup_confirmed=clean and g.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),process_creation_attempts=len(denied),
            resource_summary=dict(count=len(g.samples),system_CPU_max=max((s['system_cpu_percent'] for s in g.samples),default=None),
                available_RAM_min=min((s['available_ram_percent'] for s in g.samples),default=None)))
        receipt=publisher.publish(c.ROOT,output,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),error_frames=row.get('error_frames'),
            fresh=row.get('fresh_inputs'),final=row.get('final_fresh_hashes'),cleanup=row['cleanup_confirmed'],receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup_confirmed'] else 2


if __name__=='__main__':raise SystemExit(main())
