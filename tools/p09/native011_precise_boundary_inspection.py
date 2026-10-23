"""Actual original Native BoundaryReader, clock-only change, no Frame/worker.

Both variants perform first and closing fresh byte/hash passes on the same
explicit14 sources. Wall comparison is diagnostic, not controlled cache/CPU.
"""
import json
import re
import sys
import threading
import time
from types import SimpleNamespace as NS

SELF='tools/p09/native011_precise_boundary_inspection.py'
OUTPUT='implementation/p09/evidence/p09-361-native011-current805-precise-boundary001.v1.json'
NATIVE=dict(path='tools/p09/run_case112_current_stored.py',bytes=23159,
    sha256='6f2a79556ebcfae40765ebd127a8fcc1022e5ee8611d666fd3daa723a4236713')


def main():
    if sys.argv[1:]:raise ValueError('PRECISE_BOUNDARY_CLOSED_INVOCATION')
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import owned_source_read_pressure as pressure,native011_precise_boundary_pacer as precise
    import native011_ready_scope_connection as controls,successor_preparation_workspace_v1 as publisher
    host.configure_host_policy(c)
    g=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;denied=[];started=time.monotonic()
    row=dict(state='FAILED_PRECISE_ORIGINAL_NATIVE_BOUNDARY_READER_NOT_FRAME',GO_authorized=False,
        actual_Frame_or_worker_or_product_executed=False,accepted_count_delta=0,variants={})
    def audit(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('PRECISE_BOUNDARY_PROCESS_DENIED')
    sys.addaudithook(audit)
    try:
        g.acquire();q=a.AcceptanceReader(c.ROOT,g.check);c.require(not(c.ROOT/OUTPUT).exists(),'EXCLUSIVE_PRECISE_READER_PROBE')
        for name in (SELF,precise.SELF,precise.TEST,controls.SELF,
            'tools/p09/owned_source_read_pressure.py','tools/p09/weighted_audit_io.py','tools/p09/audit_evidence_io.py'):q.pin(name)
        source=q.text(NATIVE['path']);a.exact(q.snapshots[NATIVE['path']],NATIVE,'ORIGINAL_NATIVE_BOUNDARY_DEFINITION')
        loaded=a.native.definitions(source,('BoundaryReader',),dict(byte_policy=pressure))
        api=a.native.load(q,14,c)
        names=controls.CONTROLS[:14];pins={name:q.pin(name) for name in names}
        owner=NS(lock=threading.Lock(),samples=g.samples)
        for mode in ('original','precise'):
            reader=loaded.BoundaryReader(c.ROOT,g.check,owner=owner,api=api)
            original_type=type(reader);checkpoint=reader.checkpoint;original_methods={name:getattr(type(reader),name)
                for name in ('_read','_bind','pin','fresh_pin','finish','diagnostics')}
            proof=precise.connect(reader,pressure) if mode=='precise' else None
            begin=time.perf_counter()
            for name,pin in pins.items():a.exact(reader.pin(name),pin,'REAL_NATIVE_READER_FIRST_BYTES')
            reader.finish();g.check(force=True)
            c.require(reader.read_passes==2*len(pins) and reader.final_fresh_hashes==len(pins)
                and reader.bytes_read==2*sum(pin['bytes'] for pin in pins.values())
                and reader.pacer.bytes_paced==reader.bytes_read and reader.snapshots==pins,
                'ORIGINAL_TWO_REAL_HASH_PASSES_AND_PACER_COUNTERS')
            c.require(type(reader) is original_type and reader.checkpoint is checkpoint
                and all(getattr(type(reader),name) is method for name,method in original_methods.items()),
                'ORIGINAL_READER_CLASS_METHODS_AND_PRESSURE_CHECKPOINT_RETAINED')
            row['variants'][mode]=dict(elapsed_seconds=time.perf_counter()-begin,
                read_passes=reader.read_passes,final_fresh_hashes=reader.final_fresh_hashes,bytes_read=reader.bytes_read,
                actual_byte_pins=list(reader.snapshots.values()),pacer_bytes=reader.pacer.bytes_paced,
                requested_sleep_seconds=reader.pacer.requested_sleep_seconds,clock=mode,
                diagnostics=reader.diagnostics(),connection_proof=proof)
        q.finish();g.check(force=True);c.require(not denied and q.final_fresh_hashes==len(q.snapshots),'PROBE_CLOSING')
        row.update(state='PASS_PRECISE_ORIGINAL_NATIVE_BOUNDARY_READER_TWO_HASH_PASSES_NOT_FRAME',
            explicit_source_count=len(pins),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            wall_comparison_not_controlled_OS_cache_or_background_load=True,
            actual_full_current3015_or_Native_deadline_or_shared5_qualified=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,MemoryError) as error:
        value=error.args[0] if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value) is str
            and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_PRECISE_READER_PROBE_FAILURE')
    finally:
        g.close();row.update(cleanup_confirmed=g.cleanup,source_pins=[] if q is None else list(q.snapshots.values()),
            elapsed_seconds=time.monotonic()-started,process_creation_attempts=len(denied),
            resource_summary=dict(system_CPU_max=max((s['system_cpu_percent'] for s in g.samples),default=None),
                available_RAM_min=min((s['available_ram_percent'] for s in g.samples),default=None)))
        receipt=publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),cleanup=g.cleanup,
            fresh=row.get('fresh_inputs'),final=row.get('final_fresh_hashes'),receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and g.cleanup else 2


if __name__=='__main__':raise SystemExit(main())
