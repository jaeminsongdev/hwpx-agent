"""Owned read-only engine/EOF inspection; inherently no GO or product mode.

The actual original worker runs once with real stdin EOF and must reject it.
Permanent process denial is additional containment, not a replacement verdict.
This does not exercise an inherited readiness event or a live Native Frame.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import time
import traceback
from types import SimpleNamespace as NS

SELF='tools/p09/native011_eof_inspection.py'
PUBLISHER=dict(path='tools/p09/successor_preparation_workspace_v1.py',bytes=9656,
    sha256='003a0978b515c148d1a7f17ba53cdcab9eb77698535714216c90b53c868bbb98')


class EOFOnly:
    def __init__(self,original):self.original=original;self.reads=0
    def __getattr__(self,name):return getattr(self.original,name)
    def readline(self,*args,**kwargs):
        if self.reads!=0:raise ValueError('NATIVE011_EOF_ONE_ACTUAL_READ')
        self.reads+=1
        actual=self.original.readline(*args,**kwargs)
        if type(actual) is not str or actual!='':raise ValueError('NATIVE011_EOF_REAL_EOF_ONLY')
        return actual


def main():
    sys.dont_write_bytecode=True
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    args=parser.parse_args()
    if not 1<=args.attempt<=8:raise ValueError('NATIVE011_EOF_BOUNDED_ATTEMPT')
    denied=[]
    def deny(event,arguments):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('NATIVE011_EOF_PROCESS_CREATION_DENIED')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import current_stored_runtime_scope as scope,owned_source_read_pressure as bytes_policy
    import runtime_envelope_namespace_bundle_v1 as source_loader
    publishers,_=source_loader.load(c.ROOT,[PUBLISHER],{})
    publisher=publishers.successor_preparation_workspace_v1
    host.configure_host_policy(c)
    guard=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    output=f'implementation/p09/evidence/p09-361-native011-eof-inspection-attempt{args.attempt:03}.v1.json'
    row=dict(state='FAILED_NATIVE011_ORIGINAL_ENGINE_EOF_INSPECTION_NOT_NATIVE',stage='PREPARATION',
        product_executed=False,GO_authorized=False,accepted_count_delta=0,official_accepted_count=158,
        readiness_event_qualified=False,live_Native_Frame_or_dispatch_qualified=False)
    q=None;started=time.monotonic();before_stdin=sys.stdin
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        c.require(not (c.ROOT/output).exists(),'NATIVE011_EOF_EXCLUSIVE_RESULT')
        q.pin(SELF)
        a.exact(q.pin(PUBLISHER['path']),PUBLISHER,'NATIVE011_EOF_ORIGINAL_PRIVATE_PUBLISHER_SOURCE')
        helper_paths=('tools/p09/native011_preparation.py','tools/p09/native011_worker_transport.py',
            'tools/p09/native011_zlib_binding.py','tools/p09/native011_worker_preparation.py')
        helper_pins=[q.pin(name) for name in helper_paths]
        allowed={p['path']:p for p in helper_pins}
        # The existing whole namespace loader receives fresh paced source
        # bytes. No normal module is removed, masked or replaced.
        class Source:
            def __init__(self,name):self.name=name
            def __fspath__(self):return os.fspath(c.ROOT/self.name)
            def open(self,mode):
                c.require(mode=='rb' and self.name in allowed,'NATIVE011_EOF_DECLARED_BOOTSTRAP_SOURCE')
                pin=allowed[self.name];before=q.maximum_parse_bytes
                try:
                    q.maximum_parse_bytes=min(before,pin['bytes']+1)
                    actual,raw=q._read(self.name,parse=True);q._bind(self.name,actual)
                finally:q.maximum_parse_bytes=before
                a.exact(actual,pin,'NATIVE011_EOF_FRESH_BOOTSTRAP_SOURCE')
                import io
                return io.BytesIO(raw)
        class Root:
            def __fspath__(self):return os.fspath(c.ROOT)
            def __truediv__(self,name):return Source(name)
        libraries,_=source_loader.load(Root(),helper_pins,{})
        worker=libraries.native011_worker_preparation
        row['stage']='SAME_PUBLISHED_PACKAGE_ENGINE_CONSTRUCTION'
        prepared=worker.prepare(c.ROOT,q,a,scope,bytes_policy,source_loader)
        row['preparation_proof']=prepared.proof
        linked=prepared.linked
        c.require(linked.state.attempts==linked.state.calls==0,'NATIVE011_EOF_BEFORE_ORIGINAL_WORKER')
        q.finish();guard.check(force=True)
        c.require(q.final_fresh_hashes==len(q.snapshots),'NATIVE011_EOF_PREPARATION_CLOSING_BYTES')
        row['stage']='ORIGINAL_WORKER_ACTUAL_STDIN_EOF'
        actual=EOFOnly(before_stdin);sys.stdin=actual
        try:linked.execute(worker.transport.TASK)
        except ValueError as error:
            c.require(error.args==('WORKER_NOT_AUTHORIZED',),'NATIVE011_EOF_EXACT_ORIGINAL_REJECTION')
            row['original_worker_error']='WORKER_NOT_AUTHORIZED'
        else:c.require(False,'NATIVE011_EOF_ORIGINAL_WORKER_MUST_REJECT')
        finally:sys.stdin=before_stdin
        c.require(actual.reads==1 and linked.state.attempts==linked.state.calls==1
            and linked.state.completed is False and linked.policy.restored and not denied,
            'NATIVE011_EOF_ONCE_NO_PROCESS_OR_GO_AND_POLICY_RESTORED')
        a.exact(q.fresh_pin(worker.STEP['path']),worker.STEP,'NATIVE011_EOF_STEP_AFTER_ORIGINAL_WORKER')
        guard.check(force=True)
        row.update(state='PASS_NATIVE011_REAL_ENGINE_AND_ORIGINAL_WORKER_EOF_REJECTION_NOT_PRODUCT',
            actual_stdin_EOF_reads=actual.reads,original_worker_attempts=linked.state.attempts,
            original_worker_calls=linked.state.calls,product_calls=0,raw_policy_restored=linked.policy.restored,
            product_window_seconds=linked.window.WINDOW.SECONDS,
            worker_source_path=Path(linked.original_worker.__code__.co_filename).name,
            closing_hash_boundary='Preparation before EOF; STEP additionally fresh after original rejection',
            existing_package_reencoded_or_republished=False,prior_suites_reexecuted=False)
    except (ValueError,OSError,KeyError,IndexError,TypeError,AttributeError,MemoryError,NameError,ImportError) as error:
        row['error_type']=type(error).__name__
        row['error_code']=error.args[0] if error.args and type(error.args[0]) is str and re.fullmatch(
            '[A-Za-z0-9_]{1,160}',error.args[0]) else 'CLOSED_EOF_INSPECTION_FAILURE'
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-6:]]
        missing=getattr(q,'missing_worker_construction_input',None)
        if isinstance(missing,str) and missing.startswith('tools/p09/') and missing.endswith('.py'):
            row['missing_declared_source']=missing
        row['default_helper_count_at_stop']=getattr(q,'worker_default_helper_count',None)
    finally:
        sys.stdin=before_stdin;guard.close()
        row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            resource_samples=guard.samples,process_creation_attempts=len(denied))
        if not guard.cleanup:row['state']='FAILED_NATIVE011_EOF_INSPECTION_CLEANUP'
        receipt=publisher.publish(c.ROOT,output,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],stage=row['stage'],error_code=row.get('error_code'),
            error_frames=row.get('error_frames'),missing_declared_source=row.get('missing_declared_source'),
            cleanup=row['cleanup_confirmed'],fresh=row['fresh_inputs'],
            final=row['final_fresh_hashes'],elapsed=row['elapsed_seconds'],preparation=row.get('preparation_proof'),
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            available_RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None),receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup_confirmed'] else 2


if __name__=='__main__':
    raise SystemExit(main())
