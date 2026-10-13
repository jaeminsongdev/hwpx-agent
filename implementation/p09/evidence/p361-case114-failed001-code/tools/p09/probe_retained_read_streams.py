"""Small real Windows sharing/identity/two-byte/retained-handle probe only.

One original sampler/mutex/CPU/RAM/deadline; no Job/product/queue acceptance,
full1731 qualification, cache across frames, or changes to originals/OS settings.
"""
import json
from pathlib import Path
import re
import sys
import threading
import time
from types import SimpleNamespace as NS

import accept_case112_current_epoch as a
import retained_read_streams as retained
import run_case112_current_stored as prior

SELF='tools/p09/probe_retained_read_streams.py'
OUTPUT='implementation/p09/evidence/p09-361-retained-read-streams-probe001.v1.json'
PASS='PASS_SMALL_REAL_RETAINED_STREAMS_NOT_WHOLE_CURRENT_RUNTIME_OR_PRODUCT'


def require(ok,code):
    if not ok:raise ValueError('RETAINED_PROBE_'+code)


def run():
    destination=a.c.ROOT/OUTPUT
    require(not destination.exists() and not destination.is_symlink(),'IMMUTABLE_OUTPUT')
    started=time.monotonic();guard=a.Guard();q=None;frame=None;held=None;api=None
    state='NOT_RUN';stop=None;verified=False;frame_clean=True;phase='admission'
    try:
        guard.acquire();phase='source_setup';q=a.AcceptanceReader(a.c.ROOT,guard.check)
        for name in ('fixtures/synthetic/p01-foundation.txt','fixtures/synthetic/p02-source-records/xsd.json',
                retained.SELF,retained.TEST,SELF):q.pin(name)
        api=retained.load(q,14,a.c)
        for module in tuple(sys.modules.values()):
            path=getattr(module,'__file__',None)
            if path:
                path=Path(path).absolute()
                if path.is_relative_to(a.c.ROOT/'tools/p09') and path.suffix=='.py':
                    q.pin(path.relative_to(a.c.ROOT).as_posix())
        require(len(q.snapshots)<=64,'SMALL_CLOSURE_BOUND')
        owner=NS(lock=threading.Lock(),samples=guard.samples,checkpoint_io=guard.check)
        context=NS(phase='metadata_hash')
        early=api.EarlySourceCheckpoint(guard.check,owner)
        held=api.InputLocks(a.c.ROOT,early,owner,context)
        frame=retained.frames.Frame(retained.frames.Registry(),q.snapshots,early,held=held)
        phase='native_acquisition';held.mark('before_acquire');frame.acquire();held.mark('after_acquire')
        def factory(checkpoint):return prior.BoundaryReader(a.c.ROOT,checkpoint,owner=owner,api=api)
        phase='before_bytes';first=api.read_with_held_path_guards(frame,factory,guard.check,[])
        after_first=held.borrower.summary()
        require(after_first['duplicate_handles_opened']==len(q.snapshots)
            and after_first['duplicate_handles_closed']==0,'REAL_STREAMS_RETAINED_AFTER_BEFORE')
        phase='after_bytes';second=api.read_with_held_path_guards(frame,factory,guard.check,[])
        require(first==second==list(frame.inputs.values()),'BOTH_COMPLETE_BYTE_PASSES')
        held.verify_two_byte_passes(frame.inputs);held.verify_held_identities()
        s=held.borrower.summary();n=len(frame.inputs)
        require(s['duplicate_handles_opened']==n and s['shared_offset_resets']==2*n
            and s['new_duplicate_open_reservations']==n and s['reused_stream_pressure_checkpoints']==n
            and s['logical_read_leases']==s['logical_read_lease_returns']==2*n,'ACTUAL_RETENTION_COUNTS')
        require(held.api.pacer.opens==len(held.owned)+n,'ACTUAL_NEW_PHYSICAL_OPEN_RESERVATIONS')
        phase='release';require(frame.close(),'ALL_NATIVE_AND_RETAINED_HANDLES_CLOSED')
        s=held.borrower.summary()
        require(s['duplicate_handles_closed']==n and s['duplicate_handles_remaining']==0
            and s['duplicate_close_failed_attempts']==0,'PHYSICAL_DUPLICATE_CLEANUP')
        phase='fresh_closing';q.finish();guard.check(force=True);verified=True;state=PASS;phase='completed'
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        state='STOPPED_SMALL_PROBE_NOT_QUALIFIED'
        stop=str(error) if isinstance(error,ValueError) and re.fullmatch('[A-Z0-9_]{1,256}',str(error)) else 'REDACTED_GUARD_OR_CONTRACT_FAILED'
        # Do not print exception values or arbitrary filesystem/native errors.
    finally:
        if frame is not None:frame_clean=frame.close()
        guard.close()
    ready=verified and frame_clean and guard.cleanup
    row=dict(schema_version='hwpx-agent.p09-retained-read-streams-probe/v1',state=state,
        ready_for_separate_current_queue_integration=ready,stop_reason=stop,phase=phase,
        sole_serial_original_sampler=True,second_observer_or_thread_or_process=False,
        actual_product_or_Job_executed=False,whole_current_scope_qualified=False,queue_delta=0,
        source_probe_frame=frame.summary() if frame else None,
        fresh_input_pins=list(q.snapshots.values()) if q else [],
        final_fresh_hashes=q.final_fresh_hashes if q else 0,
        original_reader_binding_projection=api.retained_binding_projection if api else None,
        resource_samples=guard.samples,resource_cleanup_confirmed=guard.cleanup,
        cleanup_confirmed=frame_clean and guard.cleanup,elapsed_seconds=time.monotonic()-started,
        P09_gate='OPEN',PC_freeze_resolved=False,Hangul_access_or_OS_settings_changed=False)
    with destination.open('x',encoding='utf-8') as stream:json.dump(row,stream,ensure_ascii=True,indent=2)
    print(json.dumps(dict(state=state,ready=ready,input_count=len(q.snapshots) if q else 0,
        cleanup_confirmed=row['cleanup_confirmed'],product_executed=False,queue_delta=0)))
    return 0 if ready else 2


if __name__=='__main__':raise SystemExit(run())
